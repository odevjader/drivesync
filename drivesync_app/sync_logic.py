"""Módulo contendo a lógica principal de sincronização de arquivos e pastas."""

import logging
from pathlib import Path
from . import processador_arquivos
from . import gerenciador_drive
from . import gerenciador_estado # Import for DB functions

logger = logging.getLogger(__name__)

def run_sync(config, drive_service, db_connection, dry_run=False):
    """
    Orchestrates the main synchronization logic between a local folder and Google Drive.
    Handles persistent API failures gracefully for individual items.
    """
    if dry_run:
        logger.info("Dry run mode enabled. No actual changes will be made to Google Drive or application state.")
    logger.info("Starting synchronization process...")

    failed_items_log = [] # To store info about items that failed persistently

    source_folder_str = None
    try:
        source_folder_str = config.get('Sync', 'source_folder', fallback=None)
        if not source_folder_str:
            logger.error("Source folder is not configured in config.ini ([Sync] -> source_folder) or is empty. Halting sync.")
            return
    except Exception as e:
        logger.error(f"Could not read 'source_folder' from config: {e}. Halting sync.")
        return

    target_drive_folder_id = 'root'
    try:
        configured_target_id = config.get('Sync', 'target_drive_folder_id', fallback=None)
        if configured_target_id:
            target_drive_folder_id = configured_target_id
            logger.info(f"Using configured 'target_drive_folder_id': {target_drive_folder_id}")
        else:
            logger.info("'target_drive_folder_id' is not configured or empty in config.ini, using 'root' as target.")
    except Exception as e:
        logger.error(f"Error reading 'target_drive_folder_id' from config: {e}. Using 'root'.")

    local_to_drive_parent_map = {'.': target_drive_folder_id}

    logger.info(f"Starting processing of local directory: {source_folder_str}")
    for item in processador_arquivos.walk_local_directory(source_folder_str):
        relative_item_path = item['path']
        item_name = item['name']
        parent_relative_path = str(Path(relative_item_path).parent)
        drive_parent_id = local_to_drive_parent_map.get(parent_relative_path)

        if drive_parent_id is None:
            logger.error(f"Parent Drive ID for '{relative_item_path}' (local parent: '{parent_relative_path}') not found. Skipping item. This may occur if parent folder processing failed persistently.")
            # No need to add to failed_items_log here, as the parent folder failure would have been logged.
            continue

        # --- Folder Processing ---
        if item['type'] == 'folder':
            logger.info(f"Processing folder: '{relative_item_path}' (Local Name: '{item_name}')")
            drive_folder_id = None
            existing_mapping = gerenciador_estado.get_folder_mapping(db_connection, relative_item_path)

            if existing_mapping:
                drive_folder_id = existing_mapping['drive_folder_id']
                logger.info(f"Folder mapping already exists for '{relative_item_path}'. Drive ID: '{drive_folder_id}'")
            else:
                if not dry_run:
                    logger.info(f"Attempting to find or create Drive folder for '{item_name}' in parent Drive ID '{drive_parent_id}'")
                    try:
                        drive_folder_id = gerenciador_drive.find_or_create_folder(drive_service, drive_parent_id, item_name)
                        if drive_folder_id is None: # Explicit check for None after retries
                            logger.error(f"Failed to find or create Drive folder for '{relative_item_path}' (Name: '{item_name}') after retries. This folder and its contents will be skipped.")
                            failed_items_log.append({'path': relative_item_path, 'type': 'folder', 'reason': 'find_or_create_folder failed after retries'})
                        # If an exception was raised by find_or_create_folder (e.g. non-HttpError or decorator re-raised), it would be caught by the outer try-except in main or here if we add one.
                        # For now, assuming find_or_create_folder returns None on persistent HttpError.
                    except Exception as e_folder: # Catch any unexpected error from find_or_create_folder
                        logger.critical(f"Critical error during find_or_create_folder for '{relative_item_path}': {e_folder}", exc_info=True)
                        failed_items_log.append({'path': relative_item_path, 'type': 'folder', 'reason': f'find_or_create_folder critical error: {e_folder}'})
                        drive_folder_id = None # Ensure it's None

                else: # dry_run
                    drive_folder_id = f"dry_run_folder_id_{relative_item_path.replace('/', '_')}"
                    logger.info(f"[Dry Run] Would attempt to find or create Drive folder for '{item_name}'. Simulated ID: '{drive_folder_id}'")

            if drive_folder_id: # Proceed only if folder ID was obtained (real or simulated)
                if not existing_mapping and not dry_run: # Only update if it's a new mapping and not dry_run
                    mapping_details = {'local_relative_path': relative_item_path, 'drive_folder_id': drive_folder_id}
                    if not gerenciador_estado.update_folder_mapping(db_connection, mapping_details):
                        logger.error(f"Failed to add folder mapping to DB for '{relative_item_path}'. This is an internal state update error.")
                        # This is a state update error, not an API error. Consider how to handle.

                local_to_drive_parent_map[relative_item_path] = drive_folder_id
                logger.debug(f"Updated local_to_drive_parent_map: '{relative_item_path}' -> '{drive_folder_id}' (Dry run: {dry_run})")
            # If drive_folder_id is None (due to real failure), children will be skipped as drive_parent_id will be None for them.

        # --- File Processing ---
        elif item['type'] == 'file':
            logger.info(f"Processing file: '{relative_item_path}' (Local Name: '{item_name}')")
            current_local_size = item['size']
            current_local_modified_time = item['modified_time']
            needs_upload = True

            stored_item_info = gerenciador_estado.get_processed_item(db_connection, relative_item_path)

            if stored_item_info:
                stored_size = stored_item_info.get('local_size')
                stored_modified_time = stored_item_info.get('local_modified_time')
                drive_id_for_logging = stored_item_info.get('drive_id')
                if stored_size == current_local_size and stored_modified_time == current_local_modified_time:
                    logger.info(f"File '{relative_item_path}' is already synced and unchanged. Skipping. Drive ID: {drive_id_for_logging}")
                    needs_upload = False
                else:
                    logger.info(f"File '{relative_item_path}' has changed. Marked for re-upload. Old Drive ID: {drive_id_for_logging}")
            else:
                logger.info(f"File '{relative_item_path}' is new. Preparing for upload.")

            if needs_upload:
                if drive_parent_id is None: # Check if parent folder creation/retrieval failed
                    logger.error(f"Cannot upload file '{relative_item_path}' because its parent Drive folder ID ('{parent_relative_path}') could not be determined. Skipping.")
                    failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': f'Parent folder {parent_relative_path} resolution failed'})
                    continue # Skip to next item in walk_local_directory

                local_full_path = item['full_path']
                new_drive_file_id = None # Initialize before try block

                if not dry_run:
                    try:
                        logger.info(f"Attempting to upload file '{local_full_path}' to Drive parent ID '{drive_parent_id}' as '{item_name}'")
                        new_drive_file_id = gerenciador_drive.upload_file(drive_service, local_full_path, item_name, drive_parent_id)

                        if new_drive_file_id:
                            logger.info(f"File '{relative_item_path}' uploaded/re-uploaded successfully. New Drive ID: {new_drive_file_id}")
                            item_db_details = {
                                'local_relative_path': relative_item_path,
                                'drive_id': new_drive_file_id,
                                'local_size': current_local_size,
                                'local_modified_time': current_local_modified_time,
                                'drive_md5_checksum': None
                            }
                            if not gerenciador_estado.update_processed_item(db_connection, item_db_details):
                                logger.error(f"Failed to update DB for '{relative_item_path}' after upload. This is an internal state update error.")
                                # Consider adding to a separate log for state errors if needed
                        else: # upload_file returned None, meaning persistent failure after retries
                            logger.error(f"Upload failed persistently for '{relative_item_path}' after retries, as reported by upload_file.")
                            failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': 'upload_file failed after retries'})

                    except Exception as e_upload: # Catch any other unexpected error from upload_file call itself
                        logger.critical(f"Critical error during upload_file call for '{relative_item_path}': {e_upload}", exc_info=True)
                        failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': f'upload_file critical error: {e_upload}'})
                        # new_drive_file_id remains None or its previous state
                else: # dry_run
                    simulated_drive_file_id = f"dry_run_file_id_{relative_item_path.replace('/', '_')}"
                    logger.info(f"[Dry Run] Would attempt to upload file '{local_full_path}' as '{item_name}' to Drive parent ID '{drive_parent_id}'.")
                    logger.info(f"[Dry Run] Simulated new Drive File ID would be '{simulated_drive_file_id}'.")
                    logger.info(f"[Dry Run] Would update DB for '{relative_item_path}' with simulated Drive ID and local metadata.")

    logger.info(f"Completed processing loop for source folder: {source_folder_str} (Dry run: {dry_run}).")

    if failed_items_log:
        logger.warning("--- Summary of Failed Items (due to persistent API errors or critical issues) ---")
        for failed_item in failed_items_log:
            logger.warning(f"  - Type: {failed_item['type']}, Path: {failed_item['path']}, Reason: {failed_item['reason']}")
        logger.warning(f"Total items that failed persistently: {len(failed_items_log)}")
    else:
        logger.info("All items processed without persistent API errors or critical issues during sync run.")

    logger.info("Synchronization process run_sync function call completed.")
