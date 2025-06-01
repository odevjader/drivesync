"""Módulo para processamento de arquivos e diretórios locais."""

import os
import logging
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)

def walk_local_directory(local_folder_path_str: str):
    """
    Recursively traverses a local directory and yields information about
    each directory and file found.

    Args:
        local_folder_path_str (str): The absolute path to the local folder to traverse.

    Yields:
        dict: A dictionary containing information about the found item.
              For folders: {'type': 'folder', 'path': 'relative_path_str', 'name': 'folder_name'}
              For files: {'type': 'file', 'path': 'relative_path_str', 'name': 'file_name',
                          'full_path': 'absolute_path_str', 'size': file_size_in_bytes,
                          'modified_time': last_modified_timestamp}
    """
    base_path = Path(local_folder_path_str)
    if not base_path.is_dir():
        logger.error(f"Provided path '{local_folder_path_str}' is not a valid directory or does not exist.")
        return

    logger.info(f"Starting to walk local directory: '{base_path}'")

    # onerror=None is the default, it means os.walk will ignore errors from os.scandir()
    # We will handle errors for individual items within the loop.
    for root, dirs, files in os.walk(local_folder_path_str, topdown=True):
        current_root_path = Path(root)

        # Process directories
        # Sort for consistent order, which helps in testing and debugging
        dirs.sort()
        for dir_name in dirs:
            full_dir_path = None  # Initialize for use in except block
            try:
                full_dir_path = current_root_path / dir_name
                # Calculate path relative to the initial local_folder_path_str
                relative_dir_path = full_dir_path.relative_to(base_path)

                yield {
                    'type': 'folder',
                    'path': str(relative_dir_path), # Convert Path object to string
                    'name': dir_name
                }
            except Exception as e:
                logger.error(f"Error processing directory '{full_dir_path}': {e}. Skipping.")
                # To prevent os.walk from descending into problematic directories after an error,
                # one could remove it from `dirs` list here if `topdown=True`.
                # However, os.walk's default behavior with onerror=None is to log and continue.

        # Process files
        # Sort for consistent order
        files.sort()
        for file_name in files:
            full_file_path = None  # Initialize for use in except block
            try:
                full_file_path = current_root_path / file_name
                relative_file_path = full_file_path.relative_to(base_path)

                # Perform stat operations to get size and modified time
                # Using full_file_path (Path object) directly with os.stat is fine in Python 3.6+
                stat_info = os.stat(full_file_path)
                file_size = stat_info.st_size
                modified_time = stat_info.st_mtime

                yield {
                    'type': 'file',
                    'path': str(relative_file_path), # Convert Path object to string
                    'name': file_name,
                    'full_path': str(full_file_path), # Convert Path object to string
                    'size': file_size,
                    'modified_time': modified_time
                }
            except FileNotFoundError:
                logger.error(f"File not found during processing: '{full_file_path}'. It might have been deleted post-scan. Skipping.")
            except PermissionError:
                logger.error(f"Permission error accessing file: '{full_file_path}'. Skipping.")
            except Exception as e:
                # Log other potential errors (e.g., from os.stat)
                logger.error(f"Error processing file '{full_file_path}': {e}. Skipping.")

    logger.info(f"Finished walking local directory: '{base_path}'")
