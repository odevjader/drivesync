"""Módulo para interações com a API do Google Drive (operações de ficheiros e pastas)."""

import logging
import mimetypes # For guessing MIME types
import time # For sleep in retry logic
import random # For jitter in retry logic
from functools import wraps # For decorator
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload # For file uploads

# Configure logger for this module
logger = logging.getLogger(__name__)

# Module-level configuration, to be set by init_drive_config
_config = None

def init_drive_config(config_obj):
    """Initializes the drive module with application configuration."""
    global _config
    _config = config_obj
    logger.info("Drive manager configured with API retry settings.")

def retry_with_backoff(api_call_func):
    """
    Decorator to retry a Google Drive API call with exponential backoff and jitter.
    Reads retry parameters from the globally available _config object.
    """
    @wraps(api_call_func)
    def wrapper(*args, **kwargs):
        if _config is None or not _config.has_section('API_Retries'):
            logger.warning("API_Retries configuration not found or _config not initialized. Executing API call without custom retry logic.")
            # Fallback to executing the call directly if config is not available.
            # The underlying Google API client might have its own limited retries.
            return api_call_func(*args, **kwargs)

        try:
            max_retries = _config.getint('API_Retries', 'max_retries', fallback=3)
            initial_backoff_seconds = _config.getfloat('API_Retries', 'initial_backoff_seconds', fallback=1.0)
            max_backoff_seconds = _config.getfloat('API_Retries', 'max_backoff_seconds', fallback=30.0)
            backoff_factor = _config.getfloat('API_Retries', 'backoff_factor', fallback=2.0)
            retryable_statuses = {500, 502, 503, 504}
            retryable_403_reasons = {'rateLimitExceeded', 'userRateLimitExceeded'}
        except Exception as e:
            logger.error(f"Error reading API_Retries configuration: {e}. Using default retry values.")
            max_retries = 3
            initial_backoff_seconds = 1.0
            max_backoff_seconds = 30.0
            backoff_factor = 2.0
            retryable_statuses = {500, 502, 503, 504}
            retryable_403_reasons = {'rateLimitExceeded', 'userRateLimitExceeded'}

        attempt_number = 0
        last_exception = None
        while attempt_number < max_retries:
            attempt_number += 1
            try:
                return api_call_func(*args, **kwargs)
            except HttpError as e:
                last_exception = e
                logger.warning(f"API call '{api_call_func.__name__}' failed (attempt {attempt_number}/{max_retries}): {e.resp.status} {e.resp.reason}")

                is_retryable = False
                if e.resp.status in retryable_statuses:
                    is_retryable = True
                elif e.resp.status == 403:
                    try:
                        error_content = e.content.decode('utf-8')
                        import json
                        error_details = json.loads(error_content)
                        if 'error' in error_details and 'errors' in error_details['error']:
                            for err_detail in error_details['error']['errors']:
                                if err_detail.get('reason') in retryable_403_reasons:
                                    is_retryable = True
                                    break
                        elif isinstance(error_details.get("error"), str) and "rate limit" in error_details["error"].lower():
                            is_retryable = True
                    except Exception as json_err: # Broad catch for parsing issues
                        logger.warning(f"Could not parse error content for 403 reason: {json_err}")

                if is_retryable and attempt_number < max_retries:
                    wait_time = min(initial_backoff_seconds * (backoff_factor ** (attempt_number - 1)), max_backoff_seconds)
                    jitter = random.uniform(0, 0.2 * wait_time)
                    actual_wait_time = wait_time + jitter

                    logger.info(f"Retrying API call to '{api_call_func.__name__}' in {actual_wait_time:.2f} seconds...")
                    time.sleep(actual_wait_time)
                elif attempt_number >= max_retries or not is_retryable: # Max retries reached or not retryable
                    if not is_retryable:
                        logger.error(f"API call to '{api_call_func.__name__}' failed with non-retryable error: {e.resp.status} {e.resp.reason}")
                    else:
                        logger.error(f"API call to '{api_call_func.__name__}' failed permanently after {attempt_number} attempts: {e.resp.status} {e.resp.reason}")
                    raise e
            except Exception as e_general:
                last_exception = e_general
                logger.error(f"A non-HttpError exception occurred during API call '{api_call_func.__name__}' (attempt {attempt_number}/{max_retries}): {e_general}", exc_info=True)
                raise e_general

        # If loop finishes, it means all retries failed. Re-raise the last known exception.
        logger.error(f"API call '{api_call_func.__name__}' failed to complete successfully after all {max_retries} attempts.")
        if last_exception: # Should always be set if we are here
            raise last_exception
        else:
            # Fallback, though theoretically unreachable if max_retries > 0
            raise Exception(f"API call '{api_call_func.__name__}' failed after {max_retries} configured retries without a specific exception on the last attempt.")
    return wrapper

@retry_with_backoff
def _execute_drive_request(request_obj):
    """Executes a standard Google Drive API request object (e.g., list, create, get)."""
    return request_obj.execute()

@retry_with_backoff
def _execute_next_chunk(upload_request_obj):
    """Executes the next_chunk() method of a resumable upload request."""
    # This specifically handles resumable upload chunk execution.
    # It might return (None, None) if not done, or (status, None) or (None, response)
    return upload_request_obj.next_chunk()


def find_or_create_folder(drive_service, parent_folder_id, folder_name):
    """
    Finds a folder by name within a parent folder, or creates it if not found.
    Uses retry logic for API calls.
    """
    try:
        escaped_folder_name = folder_name.replace("'", "\\'")
        query = (f"name='{escaped_folder_name}' and "
                 f"mimeType='application/vnd.google-apps.folder' and "
                 f"'{parent_folder_id}' in parents and "
                 f"trashed=false")

        list_request = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageToken=None
        )
        response = _execute_drive_request(list_request)

        folders = response.get('files', [])

        if folders:
            if len(folders) > 1:
                logger.warning(f"Multiple folders named '{folder_name}' found under parent ID '{parent_folder_id}'. Using the first one found (ID: {folders[0]['id']}).")
            folder_id = folders[0]['id']
            logger.info(f"Folder '{folder_name}' found with ID: {folder_id} under parent ID '{parent_folder_id}'.")
            return folder_id
        else:
            logger.info(f"Folder '{folder_name}' not found under parent ID '{parent_folder_id}'. Creating it...")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            create_request = drive_service.files().create(
                body=file_metadata,
                fields='id'
            )
            folder = _execute_drive_request(create_request)
            folder_id = folder.get('id')
            logger.info(f"Folder '{folder_name}' created successfully with ID: {folder_id} under parent ID '{parent_folder_id}'.")
            return folder_id

    except HttpError as error: # Errors re-raised by decorator will be caught here
        error_content = error.content.decode('utf-8', 'ignore') if error.content else 'No additional content.'
        logger.error(
            f"API operation failed for folder '{folder_name}' under parent '{parent_folder_id}' after retries. "
            f"Status: {error.resp.status if hasattr(error.resp, 'status') else 'N/A'}. "
            f"Reason: {error.resp.reason if hasattr(error.resp, 'reason') else 'N/A'}. "
            f"Details: {error_content}"
        )
        return None
    except Exception as e: # Catch other unexpected errors
        logger.error(f"An unexpected error occurred in find_or_create_folder for '{folder_name}' under parent '{parent_folder_id}': {e}", exc_info=True)
        return None

def list_folder_contents(drive_service, folder_id):
    """
    Lists all files and folders directly within a given folder ID.
    Uses retry logic for API calls.
    """
    contents = {}
    page_token = None
    try:
        while True:
            query = f"'{folder_id}' in parents and trashed=false"
            list_request = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, md5Checksum, modifiedTime)',
                pageToken=page_token
            )
            response = _execute_drive_request(list_request)

            for item in response.get('files', []):
                contents[item['name']] = {
                    'id': item['id'],
                    'mimeType': item['mimeType'],
                    'md5Checksum': item.get('md5Checksum'),
                    'modifiedTime': item['modifiedTime']
                }
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        logger.info(f"Successfully listed {len(contents)} items in folder ID '{folder_id}'.")
        return contents
    except HttpError as error: # Errors re-raised by decorator
        error_content = error.content.decode('utf-8', 'ignore') if error.content else 'No additional content.'
        logger.error(
            f"API operation failed while listing contents for folder ID '{folder_id}' after retries. "
            f"Status: {error.resp.status if hasattr(error.resp, 'status') else 'N/A'}. "
            f"Reason: {error.resp.reason if hasattr(error.resp, 'reason') else 'N/A'}. "
            f"Details: {error_content}"
        )
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in list_folder_contents for folder ID '{folder_id}': {e}", exc_info=True)
        return None

def get_file_metadata(drive_service, file_id, fields='id,name,size,trashed,md5Checksum'):
    """
    Retrieves metadata for a specific file ID from Google Drive.
    Uses retry logic for the API call.

    Args:
        drive_service: Authorized Google Drive service instance.
        file_id (str): The ID of the file to retrieve metadata for.
        fields (str, optional): Comma-separated string of fields to retrieve.
                                Defaults to 'id,name,size,trashed,md5Checksum'.

    Returns:
        dict: The file metadata if successful, None otherwise.
    """
    try:
        get_request = drive_service.files().get(fileId=file_id, fields=fields)
        metadata = _execute_drive_request(get_request)
        logger.debug(f"Successfully retrieved metadata for file ID '{file_id}'.")
        return metadata
    except HttpError as error: # Errors re-raised by decorator
        # Log specific details if needed, but decorator already logs extensively
        logger.error(f"Failed to get metadata for file ID '{file_id}' after retries: {error.resp.status} {error.resp.reason}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_file_metadata for file ID '{file_id}': {e}", exc_info=True)
        return None


def upload_file(drive_service, local_file_path, file_name, parent_drive_folder_id, mime_type=None):
    """
    Uploads a file to Google Drive with resumable uploads, using retry logic for each chunk.
    """
    if mime_type is None:
        mime_type = mimetypes.guess_type(local_file_path)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        logger.debug(f"Guessed MIME type for '{local_file_path}' as '{mime_type}'.")

    try:
        media = MediaFileUpload(local_file_path,
                                mimetype=mime_type,
                                resumable=True,
                                chunksize=1024 * 1024)
    except FileNotFoundError:
        logger.error(f"Local file not found for upload: {local_file_path}. File name: '{file_name}'")
        return None
    except Exception as e:
        logger.error(f"Error initializing MediaFileUpload for '{local_file_path}': {e}")
        return None

    file_metadata = {
        'name': file_name,
        'parents': [parent_drive_folder_id]
    }

    # Initial API call to set up the resumable upload session.
    # This call itself might also benefit from retries if it can fail with server errors.
    try:
        request = drive_service.files().create(body=file_metadata,
                                               media_body=media,
                                               fields='id')
        # For the initial create request, we can wrap its execute if it's prone to errors
        # However, the main part that needs chunk-by-chunk retry is next_chunk()
        # If create() itself fails often, it could be wrapped by _execute_drive_request.
        # For now, assuming create() is less prone to retryable issues than chunk uploads.
        # If it fails, the upload won't start.
    except HttpError as e:
        logger.error(f"Failed to initiate resumable upload session for '{file_name}': {e.resp.status} {e.resp.reason}")
        return None
    except Exception as e_init:
        logger.error(f"Unexpected error initiating resumable upload for '{file_name}': {e_init}")
        return None


    logger.info(f"Starting resumable upload for '{file_name}' (local: {local_file_path}) to Drive folder '{parent_drive_folder_id}'.")

    response = None
    while response is None: # Loop until the upload is complete (response is not None)
        try:
            # _execute_next_chunk will handle retries for individual chunk uploads
            status, response = _execute_next_chunk(request)

            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}% for file {file_name}")
            # If response is not None, the upload is complete.
            # If status is None and response is None, it implies an error handled by _execute_next_chunk,
            # which would have re-raised the exception.

        except HttpError as error: # Catch errors re-raised by _execute_next_chunk after retries
            logger.error(f"Upload of '{file_name}' failed permanently after retries for a chunk: {error.resp.status} {error.resp.reason}")
            return None # Indicate upload failure
        except Exception as e: # Catch other unexpected errors during the upload loop
            logger.error(f"An unexpected error occurred during the resumable upload loop for '{file_name}': {e}", exc_info=True)
            return None

    # If loop exits and response is not None, it means success
    if response:
        drive_file_id = response.get('id')
        logger.info(f"File '{file_name}' uploaded successfully with ID: {drive_file_id}")
        return drive_file_id
    else:
        # This state should ideally not be reached if logic is correct,
        # means loop exited without response and without raising an exception.
        logger.error(f"Upload for '{file_name}' concluded without a definitive success or propagated error.")
        return None
