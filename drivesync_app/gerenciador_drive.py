import logging
import mimetypes # For guessing MIME types
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload # For file uploads

# Configure logger for this module
logger = logging.getLogger(__name__)

def find_or_create_folder(drive_service, parent_folder_id, folder_name):
    """
    Finds a folder by name within a parent folder, or creates it if not found.

    Args:
        drive_service: Authorized Google Drive service instance.
        parent_folder_id: ID of the parent folder (can be 'root').
        folder_name: Name of the folder to find or create.

    Returns:
        The ID of the found or created folder, or None if an error occurs.
    """
    try:
        # Search for the folder
        # Escape single quotes in folder_name for the query
        escaped_folder_name = folder_name.replace("'", "\\'")
        query = (f"name='{escaped_folder_name}' and "
                 f"mimeType='application/vnd.google-apps.folder' and "
                 f"'{parent_folder_id}' in parents and "
                 f"trashed=false")

        response = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)', # Only need id and name for existing folders
            pageToken=None  # Ensure a fresh search, not continuation of unrelated listing
        ).execute()

        folders = response.get('files', [])

        if folders:
            if len(folders) > 1:
                logger.warning(f"Multiple folders named '{folder_name}' found under parent ID '{parent_folder_id}'. Using the first one found (ID: {folders[0]['id']}).")
            folder_id = folders[0]['id']
            logger.info(f"Folder '{folder_name}' found with ID: {folder_id} under parent ID '{parent_folder_id}'.")
            return folder_id
        else:
            # Create the folder
            logger.info(f"Folder '{folder_name}' not found under parent ID '{parent_folder_id}'. Creating it...")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = drive_service.files().create(
                body=file_metadata,
                fields='id' # Only need id for the new folder
            ).execute()
            folder_id = folder.get('id')
            logger.info(f"Folder '{folder_name}' created successfully with ID: {folder_id} under parent ID '{parent_folder_id}'.")
            return folder_id

    except HttpError as error:
        logger.error(f"An API error occurred while finding/creating folder '{folder_name}': {error}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in find_or_create_folder for '{folder_name}': {e}")
        return None

def list_folder_contents(drive_service, folder_id):
    """
    Lists all files and folders directly within a given folder ID.

    Args:
        drive_service: Authorized Google Drive service instance.
        folder_id: ID of the folder whose contents are to be listed.

    Returns:
        A dictionary where keys are item names and values are dictionaries
        containing their 'id', 'mimeType', 'md5Checksum' (if applicable),
        and 'modifiedTime'. Returns None if an error occurs.
    """
    contents = {}
    page_token = None
    try:
        while True:
            query = f"'{folder_id}' in parents and trashed=false" # Ensure single quotes around folder_id
            response = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, md5Checksum, modifiedTime)', # Correct fields for pagination and details
                pageToken=page_token
            ).execute()

            for item in response.get('files', []):
                contents[item['name']] = {
                    'id': item['id'],
                    'mimeType': item['mimeType'],
                    'md5Checksum': item.get('md5Checksum'), # Safely get md5Checksum
                    'modifiedTime': item['modifiedTime']
                }

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        logger.info(f"Successfully listed {len(contents)} items in folder ID '{folder_id}'.")
        return contents

    except HttpError as error:
        logger.error(f"An API error occurred while listing contents for folder ID '{folder_id}': {error}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in list_folder_contents for folder ID '{folder_id}': {e}")
        return None


def upload_basic_file(drive_service, local_file_path, file_name, parent_drive_folder_id, mime_type=None):
    """
    Uploads a file to Google Drive with basic, non-resumable upload.

    Args:
        drive_service: Authorized Google Drive service instance.
        local_file_path (str): Absolute path to the local file to upload.
        file_name (str): Name of the file as it should appear on Drive.
        parent_drive_folder_id (str): ID of the Drive folder to upload into.
        mime_type (str, optional): Mime type of the file. If None, it's guessed.

    Returns:
        str: The Google Drive file ID if successful, None otherwise.
    """
    try:
        if mime_type is None:
            mime_type = mimetypes.guess_type(local_file_path)[0]
            if mime_type is None: # Fallback if guess fails
                mime_type = 'application/octet-stream'
            logger.debug(f"Guessed MIME type for '{local_file_path}' as '{mime_type}'.")

        file_metadata = {
            'name': file_name,
            'parents': [parent_drive_folder_id]
        }

        media = MediaFileUpload(local_file_path,
                                mimetype=mime_type,
                                resumable=False) # Basic upload for this task

        logger.info(f"Uploading '{file_name}' (local: {local_file_path}) to Drive folder '{parent_drive_folder_id}'...")
        file = drive_service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()

        drive_file_id = file.get('id')
        if drive_file_id:
            logger.info(f"File '{file_name}' (local: {local_file_path}) uploaded successfully to Drive folder '{parent_drive_folder_id}' with ID: {drive_file_id}")
            return drive_file_id
        else:
            logger.error(f"File '{file_name}' upload failed, no ID returned. Local path: {local_file_path}")
            return None

    except HttpError as error:
        logger.error(f"An API error occurred while uploading file '{file_name}': {error}. Local path: {local_file_path}")
        return None
    except FileNotFoundError:
        logger.error(f"Local file not found for upload: {local_file_path}. File name: '{file_name}'")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred uploading file '{file_name}': {e}. Local path: {local_file_path}")
        return None
