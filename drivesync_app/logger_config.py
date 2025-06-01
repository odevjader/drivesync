"""Módulo para configuração do logger."""

import logging
import configparser

def setup_logger(config: configparser.ConfigParser):
    """
    Configures the root logger for the application based on settings from the
    `[Logging]` section of the `config` object.

    It sets up:
    - A file handler to write logs to a specified file (`log_file`).
    - A console handler to output logs to the standard stream.
    - The logging level (`log_level`) for both handlers.
    - A common log message format.

    If logging settings are missing in the `config`, it uses default fallbacks
    (e.g., 'drivesync.log' for file path, 'INFO' for log level).

    Args:
        config (configparser.ConfigParser): ConfigParser instance, expected to
            contain a `[Logging]` section with `log_file` and `log_level` options.
    """
    log_file_path = config.get('Logging', 'log_file', fallback='drivesync.log')
    log_level_str = config.get('Logging', 'log_level', fallback='INFO').upper()

    # Get the numeric log level
    numeric_log_level = getattr(logging, log_level_str, logging.INFO)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_log_level)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(numeric_log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logging.info("Logger configured: File output to %s, Level: %s", log_file_path, log_level_str)

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # Create a dummy config.ini for testing
    dummy_config_content = """
[logging]
log_file = test_app.log
log_level = DEBUG
"""
    config_parser = configparser.ConfigParser()
    config_parser.read_string(dummy_config_content)

    setup_logger(config_parser)

    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")

    # Example of how another module would get the logger
    # test_logger = logging.getLogger(__name__)
    # test_logger.info("Message from test logger")
    print(f"Check '{config_parser.get('logging', 'log_file')}' for log output.")
