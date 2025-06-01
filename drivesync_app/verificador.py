import logging
from drivesync_app import processador_arquivos # To iterate through local files
from googleapiclient.errors import HttpError # To handle Drive API errors

def verify_sync(config, drive_service, current_state, logger_instance):
    """
    Verifies the consistency of synchronized files between the local source,
    the application's recorded state, and Google Drive.

    It iterates through local files in the `source_folder` (defined in `config`):
    1.  Checks if each local file is recorded in `current_state['processed_items']`.
    2.  If recorded, retrieves the Google Drive file ID and fetches its metadata from Drive.
    3.  Compares the local file's size with the size reported by Google Drive.
    4.  Checks if the file on Google Drive is marked as 'trashed'.
    5.  Logs discrepancies, such as:
        - Local files not found in the application state.
        - Files in the state but missing their Drive ID.
        - Files in the state but not found on Google Drive (404 error).
        - Files on Drive that are in the trash.
        - Size mismatches between local and Drive versions.
        - API or other errors encountered during verification.
    6.  Provides a summary of verification results.

    Args:
        config (configparser.ConfigParser): The application's configuration object,
                                            used to get the `source_folder`.
        drive_service (googleapiclient.discovery.Resource): Authenticated Google Drive
                                                            API service instance.
        current_state (dict): The application's current synchronization state,
                              containing `processed_items` and `folder_mappings`.
        logger_instance (logging.Logger): The logger instance to use for output.
    """
    logger = logger_instance # Use the passed logger
    logger.info("Starting synchronization verification process...")

    source_folder = None
    try:
        source_folder = config.get('Sync', 'source_folder')
        if not source_folder:
            logger.error("Source folder is not configured in config.ini ([Sync] -> source_folder). Halting verification.")
            return
    except Exception as e:
        logger.error(f"Could not read 'source_folder' from config: {e}. Halting verification.")
        return

    logger.info(f"Verifying local folder: '{source_folder}' against Drive state.")

    verified_files_count = 0
    mismatch_files_count = 0
    local_only_files_count = 0
    drive_missing_or_trashed_files_count = 0 # Combined counter

    for item in processador_arquivos.walk_local_directory(source_folder):
        if item['type'] == 'file':
            verified_files_count += 1
            relative_path = item['path']
            local_size = item['size'] # This is an integer

            if relative_path in current_state.get('processed_items', {}):
                stored_info = current_state['processed_items'][relative_path]
                drive_id = stored_info.get('drive_id')
                # stored_local_size_in_state = stored_info.get('local_size') # Not directly used for Drive comparison here

                if not drive_id:
                    logger.warning(f"File '{relative_path}' is in state but has no Drive ID. Skipping Drive check for this item.")
                    # This might be an inconsistent state, or an item that failed post-upload update
                    mismatch_files_count +=1 # Count as a mismatch/inconsistency
                    continue

                try:
                    logger.debug(f"Verifying file '{relative_path}' (Drive ID: {drive_id}) on Google Drive.")
                    # Request 'size' (string) and 'trashed' (boolean) fields
                    drive_file_metadata = drive_service.files().get(
                        fileId=drive_id,
                        fields='id,name,size,trashed'
                    ).execute()

                    if drive_file_metadata.get('trashed', False):
                        logger.warning(f"File '{relative_path}' (Drive ID: {drive_id}) is in the TRASH on Google Drive.")
                        drive_missing_or_trashed_files_count +=1
                    else:
                        drive_size_str = drive_file_metadata.get('size')
                        if drive_size_str is not None:
                            try:
                                drive_size_int = int(drive_size_str) # Drive API returns size as string
                                if local_size == drive_size_int:
                                    logger.info(f"File '{relative_path}' (Drive ID: {drive_id}): Local size ({local_size}) matches Drive size ({drive_size_int}). OK.")
                                else:
                                    logger.warning(f"File '{relative_path}' (Drive ID: {drive_id}): SIZE MISMATCH. Local: {local_size}, Drive: {drive_size_int}.")
                                    mismatch_files_count += 1
                            except ValueError:
                                logger.error(f"File '{relative_path}' (Drive ID: {drive_id}): Could not convert Drive size '{drive_size_str}' to integer.")
                                mismatch_files_count += 1
                        else:
                            # This case is unusual for regular files on Drive, might indicate a Google Doc or folder
                            # Google Docs, Sheets, Slides etc., do not have a 'size' field in the same way.
                            # Their mimeType would be 'application/vnd.google-apps.document', etc.
                            # For this verification, we assume files being synced are expected to have a byte size.
                            logger.warning(f"File '{relative_path}' (Drive ID: {drive_id}): No size information returned from Drive. (Is it a Google Workspace document type?). Local size: {local_size}.")
                            # Consider if this should be a mismatch. For now, treating as a warning.
                            # If it's a Google Doc, it shouldn't have been processed as a regular file with size in `processed_items` anyway.

                except HttpError as e:
                    if e.resp.status == 404:
                        logger.error(f"File '{relative_path}' (Drive ID: {drive_id}) found in state but MISSING on Google Drive (404 Not Found).")
                        drive_missing_or_trashed_files_count += 1
                    else:
                        logger.error(f"API Error verifying file '{relative_path}' (Drive ID: {drive_id}): {e}")
                        mismatch_files_count += 1 # Count as a mismatch due to API error during check
                except Exception as e:
                    logger.error(f"Unexpected error verifying file '{relative_path}' (Drive ID: {drive_id}) on Drive: {e}")
                    mismatch_files_count += 1 # Count as a mismatch due to unexpected error

            else: # file not in processed_items
                logger.warning(f"Local file '{relative_path}' NOT FOUND in sync state (processed_items).")
                local_only_files_count += 1

    logger.info(f"Verification Summary --- Total local files processed: {verified_files_count}")
    logger.info(f"  - Size mismatches or Drive access issues: {mismatch_files_count}")
    logger.info(f"  - Local files not found in state: {local_only_files_count}")
    logger.info(f"  - Files in state but missing/trashed on Drive: {drive_missing_or_trashed_files_count}")
    logger.info("File verification process completed.")
