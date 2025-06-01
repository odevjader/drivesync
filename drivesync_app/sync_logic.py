import logging
from pathlib import Path
from . import processador_arquivos
from . import gerenciador_drive
# from . import gerenciador_estado # State is passed in, direct use might be minimal

logger = logging.getLogger(__name__)

def run_sync(config, drive_service, app_state):
    """
    Orchestrates the main synchronization logic.

    - Iterates through local files and folders.
    - Creates corresponding folder structures on Google Drive.
    - Uploads new files (basic upload for this phase).
    - Updates `app_state['folder_mappings']`.

    Args:
        config: The application's loaded configuration object.
        drive_service: Authenticated Google Drive service instance.
        app_state: The application's current state (loaded from state file).
                   This dictionary will be modified directly.
    """
    logger.info("Starting synchronization process...")

    source_folder_str = None
    try:
        # Using .get() from configparser to avoid direct KeyError, provides default=None
        source_folder_str = config.get('Sync', 'source_folder', fallback=None)
        if not source_folder_str: # Checks for empty string or None
            logger.error("Source folder is not configured in config.ini ([Sync] -> source_folder) or is empty. Halting sync.")
            return
    except Exception as e: # Catch any other unexpected errors during config access
        logger.error(f"Could not read 'source_folder' from config: {e}. Halting sync.")
        return

    target_drive_folder_id = 'root' # Default
    try:
        # Using .get() for consistency and safety, provides default=None
        configured_target_id = config.get('Sync', 'target_drive_folder_id', fallback=None)
        if configured_target_id: # If key exists and is not empty
            target_drive_folder_id = configured_target_id
            logger.info(f"Using configured 'target_drive_folder_id': {target_drive_folder_id}")
        else:
            logger.info("'target_drive_folder_id' is not configured or empty in config.ini, using 'root' as target.")
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Error reading 'target_drive_folder_id' from config: {e}. Using 'root'.")
        # target_drive_folder_id remains 'root'

    logger.info(f"Source folder: '{source_folder_str}', Target Drive folder ID: '{target_drive_folder_id}'")

    # Ensure essential state keys are present (should be handled by load_state, but as a safeguard)
    if 'folder_mappings' not in app_state:
        logger.warning("'folder_mappings' not found in app_state, initializing.")
        app_state['folder_mappings'] = {}
    if 'processed_items' not in app_state:
        logger.warning("'processed_items' not found in app_state, initializing.")
        app_state['processed_items'] = {}

    local_to_drive_parent_map = {'.': target_drive_folder_id}

    logger.info(f"Starting processing of local directory: {source_folder_str}")
    for item in processador_arquivos.walk_local_directory(source_folder_str):
        relative_item_path = item['path']
        item_name = item['name']
        parent_relative_path = str(Path(relative_item_path).parent)
        drive_parent_id = local_to_drive_parent_map.get(parent_relative_path)

        if drive_parent_id is None:
            logger.error(f"Parent Drive ID for '{relative_item_path}' (local parent: '{parent_relative_path}') not found. Skipping item. This may occur if parent folder processing failed.")
            continue

        if item['type'] == 'folder':
            logger.info(f"Processing folder: '{relative_item_path}' (Local Name: '{item_name}')")
            drive_folder_id = None
            if relative_item_path in app_state['folder_mappings']:
                drive_folder_id = app_state['folder_mappings'][relative_item_path]
                logger.info(f"Folder mapping already exists for '{relative_item_path}'. Drive ID: '{drive_folder_id}'")
            else:
                logger.info(f"Attempting to find or create Drive folder for '{item_name}' in parent Drive ID '{drive_parent_id}'")
                drive_folder_id = gerenciador_drive.find_or_create_folder(drive_service, drive_parent_id, item_name)

            if drive_folder_id:
                if relative_item_path not in app_state['folder_mappings']:
                    app_state['folder_mappings'][relative_item_path] = drive_folder_id
                    logger.info(f"New folder mapping added: Local '{relative_item_path}' -> Drive ID '{drive_folder_id}'")
                local_to_drive_parent_map[relative_item_path] = drive_folder_id
                logger.debug(f"Updated local_to_drive_parent_map: '{relative_item_path}' -> '{drive_folder_id}'")
            else:
                logger.error(f"Failed to find or create Drive folder for '{relative_item_path}' (Name: '{item_name}'). Items under this folder may be skipped or affected.")

        elif item['type'] == 'file':
            logger.info(f"Processing file: '{relative_item_path}' (Local Name: '{item_name}')")
            current_local_size = item['size']
            current_local_modified_time = item['modified_time']
            needs_upload = True

            if relative_item_path in app_state['processed_items']:
                stored_item_info = app_state['processed_items'][relative_item_path]
                stored_size = stored_item_info.get('local_size')
                stored_modified_time = stored_item_info.get('local_modified_time')
                drive_id = stored_item_info.get('drive_id')

                if stored_size == current_local_size and stored_modified_time == current_local_modified_time:
                    logger.info(f"File '{relative_item_path}' is already synced and unchanged. Skipping. Drive ID: {drive_id}")
                    needs_upload = False
                else:
                    logger.info(f"File '{relative_item_path}' has changed (Size: {stored_size} -> {current_local_size}, ModTime: {stored_modified_time} -> {current_local_modified_time}). Re-uploading. Old Drive ID: {drive_id}")
            else:
                logger.info(f"File '{relative_item_path}' is new. Preparing for upload.")

            if needs_upload:
                local_full_path = item['full_path']
                # item_name is already defined above
                # drive_parent_id is already defined above

                if drive_parent_id: # This check was already implicitly part of the outer loop structure, but good to be explicit
                    logger.info(f"Attempting to upload file '{local_full_path}' to Drive parent ID '{drive_parent_id}' as '{item_name}'")
                    new_drive_file_id = gerenciador_drive.upload_file(drive_service, local_full_path, item_name, drive_parent_id)

                    if new_drive_file_id:
                        logger.info(f"File '{relative_item_path}' uploaded/re-uploaded successfully. New Drive ID: {new_drive_file_id}")
                        app_state['processed_items'][relative_item_path] = {
                            'drive_id': new_drive_file_id,
                            'local_size': current_local_size,
                            'local_modified_time': current_local_modified_time
                        }
                        logger.info(f"Updated state for '{relative_item_path}' with new Drive ID and local metadata.")
                    else:
                        logger.error(f"Upload failed for '{relative_item_path}'. State not updated for this item.")
                else:
                    # This case should have been caught by the check at the beginning of the loop for drive_parent_id
                    logger.error(f"Cannot upload file '{relative_item_path}' because its parent Drive folder ID could not be determined. Skipping.")
            # If needs_upload is False, we've already logged skipping it.

    logger.info(f"Completed processing loop for source folder: {source_folder_str}.")
    logger.info("Synchronization process run_sync function call completed.")
