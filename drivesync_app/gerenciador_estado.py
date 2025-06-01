"""Módulo para carregar e salvar o estado da aplicação (ex: mapeamentos de pastas, itens processados) usando SQLite."""

import sqlite3
import logging
import os

# Configure logger for this module
logger = logging.getLogger(__name__)

DB_SCHEMA = {
    "processed_items": """
        CREATE TABLE IF NOT EXISTS processed_items (
            local_relative_path TEXT PRIMARY KEY,
            drive_id TEXT,
            local_size INTEGER,
            local_modified_time REAL,
            drive_md5_checksum TEXT
        );
    """,
    "folder_mappings": """
        CREATE TABLE IF NOT EXISTS folder_mappings (
            local_relative_path TEXT PRIMARY KEY,
            drive_folder_id TEXT NOT NULL
        );
    """,
    "idx_processed_items_path": "CREATE INDEX IF NOT EXISTS idx_processed_items_path ON processed_items (local_relative_path);",
    "idx_folder_mappings_path": "CREATE INDEX IF NOT EXISTS idx_folder_mappings_path ON folder_mappings (local_relative_path);"
}

def initialize_state_db(config):
    """
    Initializes the SQLite database connection and creates tables if they don't exist.

    The path to the database file is retrieved from the `state_file` key
    within the `[Sync]` section of the `config.ini` file.

    Args:
        config: The application's loaded configuration object.

    Returns:
        A sqlite3.Connection object or None if initialization fails.
    """
    db_path = None
    try:
        db_path = config['Sync']['state_file']
    except KeyError:
        logger.error("Key 'state_file' not found in section '[Sync]' of the configuration.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving 'state_file' from configuration: {e}")
        return None

    if not db_path:
        logger.error("'state_file' is not defined or is empty in the [Sync] section of the configuration.")
        return None

    try:
        # Ensure the directory for the db file exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created directory for database: {db_dir}")

        conn = sqlite3.connect(db_path)
        logger.info(f"Successfully connected to SQLite database at {db_path}")

        with conn: # Use connection as a context manager for automatic commit/rollback
            conn.execute(DB_SCHEMA["processed_items"])
            conn.execute(DB_SCHEMA["folder_mappings"])
            conn.execute(DB_SCHEMA["idx_processed_items_path"])
            conn.execute(DB_SCHEMA["idx_folder_mappings_path"])
        logger.info("Database tables and indexes ensured.")
        return conn
    except sqlite3.Error as e:
        logger.error(f"SQLite error during database initialization at {db_path}: {e}")
        return None
    except OSError as e:
        logger.error(f"OS error during database directory creation for {db_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during database initialization at {db_path}: {e}")
        return None

def get_processed_item(db_connection, relative_path):
    """
    Retrieves a specific processed item's state from the database.

    Args:
        db_connection: Active SQLite connection object.
        relative_path: The local relative path of the item.

    Returns:
        A dictionary representing the item's state or None if not found or error.
    """
    try:
        cursor = db_connection.execute(
            "SELECT drive_id, local_size, local_modified_time, drive_md5_checksum FROM processed_items WHERE local_relative_path = ?",
            (relative_path,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "local_relative_path": relative_path, # Add this as it's not stored in the row but is key
                "drive_id": row[0],
                "local_size": row[1],
                "local_modified_time": row[2],
                "drive_md5_checksum": row[3]
            }
        return None
    except sqlite3.Error as e:
        logger.error(f"SQLite error retrieving processed item '{relative_path}': {e}")
        return None

def update_processed_item(db_connection, item_details):
    """
    Inserts or updates an item in the processed_items table.

    Args:
        db_connection: Active SQLite connection object.
        item_details: A dictionary containing the item's details.
                      Expected keys: 'local_relative_path', 'drive_id',
                                     'local_size', 'local_modified_time', 'drive_md5_checksum'.

    Returns:
        True if successful, False otherwise.
    """
    sql = """
        INSERT OR REPLACE INTO processed_items
        (local_relative_path, drive_id, local_size, local_modified_time, drive_md5_checksum)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        with db_connection:
            db_connection.execute(sql, (
                item_details['local_relative_path'],
                item_details.get('drive_id'),
                item_details.get('local_size'),
                item_details.get('local_modified_time'),
                item_details.get('drive_md5_checksum')
            ))
        # logger.debug(f"Successfully updated/inserted processed item: {item_details['local_relative_path']}")
        return True
    except sqlite3.Error as e:
        logger.error(f"SQLite error updating/inserting processed item '{item_details.get('local_relative_path')}': {e}")
        return False
    except KeyError as e:
        logger.error(f"Missing key in item_details for processed item update: {e}")
        return False

def remove_processed_item(db_connection, relative_path):
    """
    Removes a processed item from the database.

    Args:
        db_connection: Active SQLite connection object.
        relative_path: The local relative path of the item to remove.

    Returns:
        True if successful or item not found, False on error.
    """
    sql = "DELETE FROM processed_items WHERE local_relative_path = ?"
    try:
        with db_connection:
            cursor = db_connection.execute(sql, (relative_path,))
            if cursor.rowcount > 0:
                logger.info(f"Successfully removed processed item: {relative_path}")
            # else:
                # logger.debug(f"No processed item found with path {relative_path} to remove, or already removed.")
        return True
    except sqlite3.Error as e:
        logger.error(f"SQLite error removing processed item '{relative_path}': {e}")
        return False

def get_folder_mapping(db_connection, relative_path):
    """
    Retrieves a folder mapping from the database.

    Args:
        db_connection: Active SQLite connection object.
        relative_path: The local relative path of the folder.

    Returns:
        A dictionary representing the folder mapping or None if not found or error.
    """
    try:
        cursor = db_connection.execute(
            "SELECT drive_folder_id FROM folder_mappings WHERE local_relative_path = ?",
            (relative_path,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "local_relative_path": relative_path, # Add this for consistency
                "drive_folder_id": row[0]
            }
        return None
    except sqlite3.Error as e:
        logger.error(f"SQLite error retrieving folder mapping for '{relative_path}': {e}")
        return None

def update_folder_mapping(db_connection, mapping_details):
    """
    Inserts or updates a folder mapping in the folder_mappings table.

    Args:
        db_connection: Active SQLite connection object.
        mapping_details: A dictionary containing the mapping details.
                         Expected keys: 'local_relative_path', 'drive_folder_id'.

    Returns:
        True if successful, False otherwise.
    """
    sql = """
        INSERT OR REPLACE INTO folder_mappings
        (local_relative_path, drive_folder_id)
        VALUES (?, ?)
    """
    try:
        with db_connection:
            db_connection.execute(sql, (
                mapping_details['local_relative_path'],
                mapping_details['drive_folder_id']
            ))
        # logger.debug(f"Successfully updated/inserted folder mapping: {mapping_details['local_relative_path']}")
        return True
    except sqlite3.Error as e:
        logger.error(f"SQLite error updating/inserting folder mapping for '{mapping_details.get('local_relative_path')}': {e}")
        return False
    except KeyError as e:
        logger.error(f"Missing key in mapping_details for folder mapping update: {e}")
        return False

def get_all_processed_items(db_connection):
    """
    Retrieves all processed items from the database.
    Used for verification purposes, like finding items in state but not on disk.

    Args:
        db_connection: Active SQLite connection object.

    Returns:
        A dictionary of all processed items {relative_path: item_details} or empty dict.
    """
    items = {}
    try:
        cursor = db_connection.execute(
            "SELECT local_relative_path, drive_id, local_size, local_modified_time, drive_md5_checksum FROM processed_items"
        )
        for row in cursor.fetchall():
            items[row[0]] = {
                "local_relative_path": row[0],
                "drive_id": row[1],
                "local_size": row[2],
                "local_modified_time": row[3],
                "drive_md5_checksum": row[4]
            }
        return items
    except sqlite3.Error as e:
        logger.error(f"SQLite error retrieving all processed items: {e}")
        return {}

def get_all_folder_mappings(db_connection):
    """
    Retrieves all folder mappings from the database.

    Args:
        db_connection: Active SQLite connection object.

    Returns:
        A dictionary of all folder mappings {relative_path: drive_folder_id} or empty dict.
    """
    mappings = {}
    try:
        cursor = db_connection.execute(
            "SELECT local_relative_path, drive_folder_id FROM folder_mappings"
        )
        for row in cursor.fetchall():
            mappings[row[0]] = row[1] # Storing drive_folder_id directly
        return mappings
    except sqlite3.Error as e:
        logger.error(f"SQLite error retrieving all folder mappings: {e}")
        return {}

# Note: The old load_state and save_state functions are no longer needed
# and have been replaced by the SQLite specific functions.
# Ensure that the main application logic is updated to use these new functions
# and correctly manages the db_connection lifecycle (e.g., open at start, close at end).

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    # Create a dummy config object for testing
    class DummyConfig:
        def __init__(self, state_file_path):
            self.config = {'Sync': {'state_file': state_file_path}}
        def __getitem__(self, key):
            return self.config[key]

    # Use an in-memory database for this example, or specify a file path
    # test_db_path = ":memory:"
    test_db_path = "test_drivesync_state.db"

    # Clean up old test db if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    dummy_config = DummyConfig(test_db_path)

    conn = initialize_state_db(dummy_config)

    if conn:
        logger.info("Database initialized successfully for testing.")

        # Test processed_items
        item1 = {
            'local_relative_path': 'folder1/fileA.txt',
            'drive_id': 'driveA123',
            'local_size': 1024,
            'local_modified_time': 1678886400.0,
            'drive_md5_checksum': 'md5hashA'
        }
        item2 = {
            'local_relative_path': 'fileB.jpg',
            'drive_id': 'driveB456',
            'local_size': 2048,
            'local_modified_time': 1678887400.0,
            'drive_md5_checksum': None # Test nullable md5
        }

        if update_processed_item(conn, item1):
            logger.info(f"Item1 updated: {item1['local_relative_path']}")
        retrieved_item1 = get_processed_item(conn, 'folder1/fileA.txt')
        logger.info(f"Retrieved item1: {retrieved_item1}")
        assert retrieved_item1 and retrieved_item1['drive_id'] == 'driveA123'

        if update_processed_item(conn, item2):
            logger.info(f"Item2 updated: {item2['local_relative_path']}")

        # Test updating an existing item
        item1_updated = {
            'local_relative_path': 'folder1/fileA.txt',
            'drive_id': 'driveA_new_id_789',
            'local_size': 1030,
            'local_modified_time': 1678886450.0,
            'drive_md5_checksum': 'md5hashA_updated'
        }
        if update_processed_item(conn, item1_updated):
            logger.info(f"Item1 re-updated: {item1_updated['local_relative_path']}")
        retrieved_item1_updated = get_processed_item(conn, 'folder1/fileA.txt')
        logger.info(f"Retrieved item1 after update: {retrieved_item1_updated}")
        assert retrieved_item1_updated and retrieved_item1_updated['drive_id'] == 'driveA_new_id_789'
        assert retrieved_item1_updated['local_size'] == 1030

        all_items = get_all_processed_items(conn)
        logger.info(f"All processed items: {all_items}")
        assert len(all_items) == 2
        assert 'folder1/fileA.txt' in all_items
        assert 'fileB.jpg' in all_items

        # Test folder_mappings
        mapping1 = {'local_relative_path': 'MyPictures', 'drive_folder_id': 'driveFolderX789'}
        mapping2 = {'local_relative_path': 'MyDocuments/Reports', 'drive_folder_id': 'driveFolderY101'}

        if update_folder_mapping(conn, mapping1):
            logger.info(f"Mapping1 updated: {mapping1['local_relative_path']}")
        retrieved_mapping1 = get_folder_mapping(conn, 'MyPictures')
        logger.info(f"Retrieved mapping1: {retrieved_mapping1}")
        assert retrieved_mapping1 and retrieved_mapping1['drive_folder_id'] == 'driveFolderX789'

        if update_folder_mapping(conn, mapping2):
            logger.info(f"Mapping2 updated: {mapping2['local_relative_path']}")

        all_mappings = get_all_folder_mappings(conn)
        logger.info(f"All folder mappings: {all_mappings}")
        assert len(all_mappings) == 2
        assert 'MyPictures' in all_mappings
        assert all_mappings['MyDocuments/Reports'] == 'driveFolderY101'

        # Test removing an item
        if remove_processed_item(conn, 'fileB.jpg'):
            logger.info("Item fileB.jpg removed.")
        retrieved_item_b = get_processed_item(conn, 'fileB.jpg')
        assert retrieved_item_b is None
        all_items_after_remove = get_all_processed_items(conn)
        logger.info(f"All processed items after remove: {all_items_after_remove}")
        assert len(all_items_after_remove) == 1

        # Test removing a non-existent item
        if remove_processed_item(conn, 'nonexistent/file.txt'):
            logger.info("Attempted to remove non-existent item (should not error).")

        conn.close()
        logger.info("Database connection closed.")

        # Clean up the test database file
        if test_db_path != ":memory:" and os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info(f"Test database {test_db_path} removed.")
    else:
        logger.error("Failed to initialize database for testing.")

"""
Old JSON-based functions (for reference, will be removed by overwrite):

import json
# logger and os already imported

def load_state(config):
    # ... (old implementation) ...
    pass

def save_state(config, state_data):
    # ... (old implementation) ...
    pass
"""
