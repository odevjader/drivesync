import json
import logging
import os

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_state(config):
    """
    Loads the application's synchronization state from a JSON file.

    The path to this state file is retrieved from the `state_file` key
    within the `[Sync]` section of the `config.ini` file.

    Args:
        config: The application's loaded configuration object (assumed to be a configparser.ConfigParser instance).

    Returns:
        A dictionary representing the loaded state. If the file doesn't exist
        or is invalid, returns a default empty state:
        `{"processed_items": {}, "folder_mappings": {}}`.
    """
    default_state = {"processed_items": {}, "folder_mappings": {}}
    state_file_path = None
    try:
        # Assuming config is a configparser.ConfigParser object
        state_file_path = config['Sync']['state_file']
    except KeyError:
        logger.error("Key 'state_file' not found in section '[Sync]' of the configuration.")
        return default_state
    except Exception as e:
        logger.error(f"Error retrieving 'state_file' from configuration: {e}")
        return default_state

    if not state_file_path:
        # This case might be redundant if configparser itself raises an error for empty values,
        # but kept for robustness.
        logger.error("'state_file' is not defined or is empty in the [Sync] section of the configuration.")
        return default_state

    try:
        with open(state_file_path, 'r') as f:
            state_data = json.load(f)
            if not isinstance(state_data, dict):
                logger.error(f"State file {state_file_path} does not contain a valid JSON dictionary. Returning default state.")
                return default_state
            # Ensure essential keys are present
            if "processed_items" not in state_data:
                logger.warning(f"'processed_items' key not found in state file {state_file_path}. Initializing with empty dict.")
                state_data["processed_items"] = {}
            if "folder_mappings" not in state_data:
                logger.warning(f"'folder_mappings' key not found in state file {state_file_path}. Initializing with empty dict.")
                state_data["folder_mappings"] = {}
            logger.info(f"Successfully loaded state from {state_file_path}")
            return state_data
    except FileNotFoundError:
        logger.info(f"State file {state_file_path} not found. Returning default empty state.")
        return default_state
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from state file {state_file_path}. The file might be empty or corrupted. Returning default state.")
        return default_state
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading state from {state_file_path}: {e}")
        return default_state

def save_state(config, state_data):
    """
    Saves the application's synchronization state to a JSON file.

    The path to this state file is retrieved from the `state_file` key
    within the `[Sync]` section of the `config.ini` file.
    The save operation is performed atomically.

    Args:
        config: The application's loaded configuration object (assumed to be a configparser.ConfigParser instance).
        state_data: The Python dictionary (state) to be saved.

    Returns:
        True if saving was successful, False otherwise.
    """
    state_file_path = None
    try:
        # Assuming config is a configparser.ConfigParser object
        state_file_path = config['Sync']['state_file']
    except KeyError:
        logger.error("Key 'state_file' not found in section '[Sync]' of the configuration.")
        return False
    except Exception as e:
        logger.error(f"Error retrieving 'state_file' from configuration: {e}")
        return False

    if not state_file_path:
        # This case might be redundant if configparser itself raises an error for empty values,
        # but kept for robustness.
        logger.error("'state_file' is not defined or is empty in the [Sync] section of the configuration.")
        return False

    temp_file_path = state_file_path + ".tmp"

    try:
        with open(temp_file_path, 'w') as f:
            json.dump(state_data, f, indent=4)
        # Atomically move the temporary file to the actual state file path
        os.replace(temp_file_path, state_file_path)
        logger.info(f"Successfully saved state to {state_file_path}")
        return True
    except Exception as e:
        logger.error(f"An error occurred while saving state to {state_file_path}: {e}")
        # Clean up the temporary file if it exists and an error occurred
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as remove_e:
                logger.error(f"Error cleaning up temporary state file {temp_file_path}: {remove_e}")
        return False
