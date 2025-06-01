"""Módulo contendo a lógica principal de sincronização de arquivos e pastas."""

import logging
import time # For sync duration
from pathlib import Path
from tqdm import tqdm # Import tqdm
from . import processador_arquivos
from . import gerenciador_drive
from . import gerenciador_estado # Import for DB functions

logger = logging.getLogger(__name__)

def sizeof_fmt(num, suffix="B"):
    """Converts a number of bytes to a human-readable format."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def run_sync(config, drive_service, db_connection, dry_run=False):
    """
    Orchestrates the main synchronization logic between a local folder and Google Drive.
    Handles persistent API failures gracefully for individual items and shows progress.
    """
    start_time = time.time() # Record start time

    if dry_run:
        logger.info("Dry run mode enabled. No actual changes will be made to Google Drive or application state.")
    logger.info("Starting synchronization process...")

    failed_items_log = []
    files_uploaded_count = 0
    files_skipped_count = 0
    total_data_transferred_bytes = 0

    source_folder_str = None
    try:
        source_folder_str = config.get('Sync', 'source_folder', fallback=None)
        if not source_folder_str:
            logger.error("Source folder is not configured. Halting sync.")
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
            logger.info("'target_drive_folder_id' not configured, using 'root'.")
    except Exception as e:
        logger.error(f"Error reading 'target_drive_folder_id' from config: {e}. Using 'root'.")

    local_to_drive_parent_map = {'.': target_drive_folder_id}

    logger.info(f"Scanning local directory: {source_folder_str}...")
    all_local_items = list(processador_arquivos.walk_local_directory(source_folder_str))

    total_files_to_process = sum(1 for item in all_local_items if item['type'] == 'file')
    logger.info(f"Found {len(all_local_items)} total items ({total_files_to_process} files) to process.")

    with tqdm(total=total_files_to_process, unit="file", desc="Syncing files",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]") as progress_bar:

        for item in all_local_items:
            relative_item_path = item['path']
            item_name = item['name']
            item_name_short = (item_name[:27] + '...') if len(item_name) > 30 else item_name

            parent_relative_path = str(Path(relative_item_path).parent)
            drive_parent_id = local_to_drive_parent_map.get(parent_relative_path)

            if item['type'] == 'file':
                progress_bar.set_postfix_str(f"Processing: {item_name_short}", refresh=True)

            if drive_parent_id is None:
                logger.error(f"Parent Drive ID for '{relative_item_path}' not found. Skipping.")
                if item['type'] == 'file':
                    failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': 'Parent folder resolution failed persistently'})
                    progress_bar.update(1)
                continue

            if item['type'] == 'folder':
                drive_folder_id = None
                existing_mapping = gerenciador_estado.get_folder_mapping(db_connection, relative_item_path)
                if existing_mapping:
                    drive_folder_id = existing_mapping['drive_folder_id']
                else:
                    if not dry_run:
                        try:
                            drive_folder_id = gerenciador_drive.find_or_create_folder(drive_service, drive_parent_id, item_name)
                            if drive_folder_id is None:
                                logger.error(f"Failed to find/create Drive folder '{relative_item_path}' after retries. It and its contents will be skipped.")
                                failed_items_log.append({'path': relative_item_path, 'type': 'folder', 'reason': 'find_or_create_folder failed'})
                        except Exception as e_folder:
                            logger.critical(f"Critical error: find_or_create_folder for '{relative_item_path}': {e_folder}", exc_info=True)
                            failed_items_log.append({'path': relative_item_path, 'type': 'folder', 'reason': f'find_or_create_folder critical error: {e_folder}'})
                            drive_folder_id = None
                    else:
                        drive_folder_id = f"dry_run_folder_id_{relative_item_path.replace('/', '_')}"

                if drive_folder_id:
                    if not existing_mapping and not dry_run:
                        mapping_details = {'local_relative_path': relative_item_path, 'drive_folder_id': drive_folder_id}
                        if not gerenciador_estado.update_folder_mapping(db_connection, mapping_details):
                            logger.error(f"DB Error: Failed to update folder mapping for '{relative_item_path}'.")
                    local_to_drive_parent_map[relative_item_path] = drive_folder_id

            elif item['type'] == 'file':
                current_local_size = item['size']
                current_local_modified_time = item['modified_time']
                needs_upload = True

                stored_item_info = gerenciador_estado.get_processed_item(db_connection, relative_item_path)

                if stored_item_info:
                    if (stored_item_info.get('local_size') == current_local_size and
                            stored_item_info.get('local_modified_time') == current_local_modified_time):
                        progress_bar.set_postfix_str(f"Skipped: {item_name_short}", refresh=True)
                        needs_upload = False
                        files_skipped_count +=1

                if needs_upload:
                    if drive_parent_id is None:
                        logger.error(f"Cannot upload file '{relative_item_path}', parent Drive ID undetermined. Skipping.")
                        failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': 'Parent folder ID undetermined at upload stage'})
                    else:
                        local_full_path = item['full_path']
                        new_drive_file_id = None

                        if not dry_run:
                            try:
                                new_drive_file_id = gerenciador_drive.upload_file(drive_service, local_full_path, item_name, drive_parent_id)
                                if new_drive_file_id:
                                    progress_bar.set_postfix_str(f"Uploaded: {item_name_short}", refresh=True)
                                    files_uploaded_count += 1
                                    total_data_transferred_bytes += current_local_size
                                    item_db_details = {
                                        'local_relative_path': relative_item_path, 'drive_id': new_drive_file_id,
                                        'local_size': current_local_size, 'local_modified_time': current_local_modified_time,
                                        'drive_md5_checksum': None
                                    }
                                    if not gerenciador_estado.update_processed_item(db_connection, item_db_details):
                                        logger.error(f"DB Error: Failed to update state for '{relative_item_path}'.")
                                else: # upload_file returned None
                                    logger.error(f"Upload failed persistently for '{relative_item_path}'.")
                                    failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': 'upload_file returned None after retries'})
                            except Exception as e_upload:
                                logger.critical(f"Critical error during upload for '{relative_item_path}': {e_upload}", exc_info=True)
                                failed_items_log.append({'path': relative_item_path, 'type': 'file', 'reason': f'upload_file critical error: {e_upload}'})
                        else: # dry_run
                            progress_bar.set_postfix_str(f"DryRun-Upload: {item_name_short}", refresh=True)
                            # In dry_run, we can simulate successful upload for counting if needed,
                            # or assume skipped if state matches. For this report, only actual uploads count for "uploaded".
                            # If it needed upload and was dry_run, it wasn't "skipped" in the sense of being up-to-date.
                            # For simplicity, files_skipped_count is only for up-to-date files.
                            # files_uploaded_count is only for actual successful uploads.

                progress_bar.update(1)

    progress_bar.set_postfix_str("Finalizing...", refresh=True)

    end_time = time.time()
    duration_seconds = end_time - start_time

    logger.info("--------------------------------------------------")
    logger.info("SYNC SUMMARY")
    logger.info("--------------------------------------------------")
    logger.info(f"Total synchronization time: {duration_seconds:.2f} seconds")
    logger.info(f"Total local files considered: {total_files_to_process}")
    logger.info(f"Files successfully uploaded/updated: {files_uploaded_count}")
    logger.info(f"Files skipped (already up-to-date): {files_skipped_count}")
    logger.info(f"Files/folders failed to process: {len(failed_items_log)}") # Renamed for clarity
    logger.info(f"Total data transferred this session: {sizeof_fmt(total_data_transferred_bytes)}")

    if failed_items_log:
        logger.warning("--- Items that failed to process: ---") # Changed title slightly
        for failed_item in failed_items_log: # Assumes failed_items_log stores dicts
            logger.warning(f"  - Type: {failed_item['type']}, Path: {failed_item['path']}, Reason: {failed_item['reason']}")
        logger.info("Please check app.log for more details on errors for these items.")
    logger.info("--------------------------------------------------")

    logger.info("Synchronization process run_sync function call completed.")
