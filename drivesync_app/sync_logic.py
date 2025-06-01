"""Módulo contendo a lógica principal de sincronização de arquivos e pastas."""

import logging
from pathlib import Path
from . import processador_arquivos
from . import gerenciador_drive
# from . import gerenciador_estado # State is passed in, direct use might be minimal

logger = logging.getLogger(__name__)

def run_sync(config, drive_service, app_state, dry_run=False):
    """
    Orchestrates the main synchronization logic between a local folder and Google Drive.

    This function iterates through local files and folders specified by `source_folder`
    in the configuration. It aims to replicate the local structure on Google Drive
    under the `target_drive_folder_id`.

    Key operations include:
    - Retrieving source and target folder information from `config`.
    - Walking the local directory structure.
    - For each local folder:
        - Checking if it's already mapped in `app_state['folder_mappings']`.
        - If not, finding or creating the folder on Google Drive (unless `dry_run` is True).
        - Storing new folder mappings in `app_state` (if not `dry_run`).
        - Maintaining a temporary map (`local_to_drive_parent_map`) to find Drive parent IDs for children.
    - For each local file:
        - Comparing its current size and modification time against stored state in `app_state['processed_items']`.
        - Uploading the file if it's new or changed (unless `dry_run` is True).
        - Updating `app_state['processed_items']` with the Drive file ID and local metadata after successful upload (if not `dry_run`).
    - If `dry_run` is True, all Drive operations (folder creation, file upload) and
      state modifications (`app_state`) are simulated and logged, but not actually performed.

    Args:
        config (configparser.ConfigParser): The application's loaded configuration object.
        drive_service (googleapiclient.discovery.Resource): Authenticated Google Drive API service instance.
        app_state (dict): The application's current state, loaded from a state file.
                          This dictionary is modified in-place with new folder mappings
                          and processed item details.
        dry_run (bool, optional): If True, the function simulates synchronization
                                  operations without making any actual changes to
                                  Google Drive or the application state. Defaults to False.
    """
    if dry_run:
        logger.info("Dry run mode enabled. No actual changes will be made to Google Drive or application state.")
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

        # --- Folder Processing ---
        if item['type'] == 'folder':
            logger.info(f"Processing folder: '{relative_item_path}' (Local Name: '{item_name}')")
            drive_folder_id = None
            if relative_item_path in app_state['folder_mappings']:
                drive_folder_id = app_state['folder_mappings'][relative_item_path]
                logger.info(f"Folder mapping already exists for '{relative_item_path}'. Drive ID: '{drive_folder_id}'")
            else:
                if not dry_run:
                    logger.info(f"Attempting to find or create Drive folder for '{item_name}' in parent Drive ID '{drive_parent_id}'")
                    drive_folder_id = gerenciador_drive.find_or_create_folder(drive_service, drive_parent_id, item_name)
                else:
                    drive_folder_id = f"dry_run_folder_id_{relative_item_path.replace('/', '_')}"
                    logger.info(f"[Dry Run] Would attempt to find or create Drive folder for '{item_name}'. Simulated ID: '{drive_folder_id}'")

            if drive_folder_id:
                if relative_item_path not in app_state['folder_mappings']:
                    if not dry_run:
                        app_state['folder_mappings'][relative_item_path] = drive_folder_id
                        logger.info(f"New folder mapping added: Local '{relative_item_path}' -> Drive ID '{drive_folder_id}'")
                    else:
                        logger.info(f"[Dry Run] Would add folder mapping: Local '{relative_item_path}' -> Drive ID '{drive_folder_id}'")
                # Always update local_to_drive_parent_map for the current session, even in dry_run, to allow child processing
                local_to_drive_parent_map[relative_item_path] = drive_folder_id
                logger.debug(f"Updated local_to_drive_parent_map: '{relative_item_path}' -> '{drive_folder_id}' (Dry run: {dry_run})")
            else:
                logger.error(f"Failed to find or create Drive folder for '{relative_item_path}' (Name: '{item_name}'). Items under this folder may be skipped or affected.")

        # --- File Processing ---
        elif item['type'] == 'file':
            logger.info(f"Processing file: '{relative_item_path}' (Local Name: '{item_name}')")
            current_local_size = item['size']
            current_local_modified_time = item['modified_time']
            needs_upload = True # Assume upload is needed unless state check proves otherwise

            # Check if the file is already in processed_items and if it has changed
            if relative_item_path in app_state['processed_items']:
                stored_item_info = app_state['processed_items'][relative_item_path]
                stored_size = stored_item_info.get('local_size')
                stored_modified_time = stored_item_info.get('local_modified_time')
                drive_id = stored_item_info.get('drive_id') # For logging purposes

                # Condition for skipping: if size and modified time match stored values
                if stored_size == current_local_size and stored_modified_time == current_local_modified_time:
                    logger.info(f"File '{relative_item_path}' is already synced and unchanged. Skipping. Drive ID: {drive_id}")
                    needs_upload = False
                else:
                    # Condition for re-upload: if size or modified time differs
                    logger.info(f"File '{relative_item_path}' has changed (Size: {stored_size} -> {current_local_size}, ModTime: {stored_modified_time} -> {current_local_modified_time}). Marked for re-upload. Old Drive ID: {drive_id}")
            else:
                # Condition for new file: if not in processed_items
                logger.info(f"File '{relative_item_path}' is new. Preparing for upload.")

            # Proceed with upload if needed
            if needs_upload:
                local_full_path = item['full_path']
                # item_name is already defined above
                # item_name is already defined above
                # drive_parent_id is already defined above

                if drive_parent_id:
                    if not dry_run:
                        # --- Actual Upload ---
                        logger.info(f"Attempting to upload file '{local_full_path}' to Drive parent ID '{drive_parent_id}' as '{item_name}'")
                        new_drive_file_id = gerenciador_drive.upload_file(drive_service, local_full_path, item_name, drive_parent_id)

                        if new_drive_file_id:
                            logger.info(f"File '{relative_item_path}' uploaded/re-uploaded successfully. New Drive ID: {new_drive_file_id}")
                            # Update state with new Drive ID and current local metadata
                            app_state['processed_items'][relative_item_path] = {
                                'drive_id': new_drive_file_id,
                                'local_size': current_local_size,
                                'local_modified_time': current_local_modified_time
                            }
                            logger.info(f"Updated state for '{relative_item_path}' with new Drive ID and local metadata.")
                        else:
                            logger.error(f"Upload failed for '{relative_item_path}'. State not updated for this item.")
                    else:
                        # --- Dry Run: Simulate Upload ---
                        new_drive_file_id = f"dry_run_file_id_{relative_item_path.replace('/', '_')}" # Simulated ID
                        logger.info(f"[Dry Run] Would attempt to upload file '{local_full_path}' as '{item_name}' to Drive parent ID '{drive_parent_id}'.")
                        logger.info(f"[Dry Run] Simulated new Drive File ID would be '{new_drive_file_id}'.")
                        # Do not update app_state['processed_items'] in dry run
                        logger.info(f"[Dry Run] Would update state for '{relative_item_path}' with simulated Drive ID and local metadata (Size: {current_local_size}, ModTime: {current_local_modified_time}).")
                else:
                    # This case should ideally be rare if parent folder processing is robust
                    logger.error(f"Cannot upload file '{relative_item_path}' because its parent Drive folder ID could not be determined. Skipping.")
            # If needs_upload is False, it means the file was found in state and deemed unchanged, already logged.

    logger.info(f"Completed processing loop for source folder: {source_folder_str} (Dry run: {dry_run}).")
    logger.info("Synchronization process run_sync function call completed.")
