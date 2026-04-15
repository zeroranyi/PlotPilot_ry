"""Unified logging configuration module."""

import logging
import os
from typing import Optional

# Valid logging levels for validation
VALID_LOGGING_LEVELS = [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL
]


def _validate_logging_level(level: int) -> None:
    """Validate that the logging level is a valid Python logging level.

    Args:
        level: The logging level to validate

    Raises:
        ValueError: If the logging level is not valid
    """
    if level not in VALID_LOGGING_LEVELS:
        raise ValueError(
            f"Invalid logging level: {level}. "
            f"Valid levels are: {VALID_LOGGING_LEVELS}"
        )


def _validate_log_file(log_file: str) -> None:
    """Validate that the log file path is writable.

    Args:
        log_file: Path to the log file to validate

    Raises:
        ValueError: If the log file path is invalid or not writable
        TypeError: If the log_file parameter is not a string
    """
    if not isinstance(log_file, str):
        raise TypeError(f"log_file must be a string, got {type(log_file).__name__}")

    if not log_file or not log_file.strip():
        raise ValueError("log_file cannot be empty or whitespace")

    # Try to create parent directories if they don't exist
    try:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    except (OSError, IOError) as e:
        raise ValueError(f"Cannot create log directory: {e}")

    # Check if we can write to the location
    try:
        # Try to open the file in append mode to check writability
        # This will fail if the path is invalid or not writable
        test_handle = open(log_file, 'a')
        test_handle.close()
    except (OSError, IOError, PermissionError) as e:
        raise ValueError(f"Cannot write to log file '{log_file}': {e}")


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
) -> None:
    """Configure logging with console and optional file output.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path for file logging output
        format_string: Log message format string

    Raises:
        ValueError: If logging level or log file path is invalid
        TypeError: If log_file parameter is not a string when provided
    """
    # Validate logging level
    _validate_logging_level(level)

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set the root logging level
    root_logger.setLevel(level)

    # Create formatters with different date formats for console and file
    console_formatter = logging.Formatter(
        format_string,
        datefmt="%H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional) with error handling
    if log_file is not None:
        # Validate log file path BEFORE trying to create handler
        # Validation errors should be raised immediately
        _validate_log_file(log_file)

        # Only catch file creation errors, not validation errors
        try:
            file_formatter = logging.Formatter(
                format_string,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        except (OSError, IOError, PermissionError) as e:
            # Log a warning if file handler creation fails, but continue with console only
            print(f"WARNING: Failed to setup file logging: {e}")
            print("Logging will continue with console output only.")

    # Uvicorn：保留默认访问日志格式（INFO: 127.0.0.1:port - "GET ..." 200 OK）
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Logger instance configured with the global settings
    """
    return logging.getLogger(name)