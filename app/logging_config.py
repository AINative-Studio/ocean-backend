"""
Logging Configuration for Ocean Backend

Configures structured logging with file and console handlers.
Performance logs go to logs/queries.log for analysis.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(debug: bool = False):
    """
    Configure application logging.

    Sets up:
    - Console handler for general application logs
    - File handler for performance/query logs
    - Rotating file handler to prevent disk space issues

    Args:
        debug: Enable debug level logging
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler - for general application logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for performance logs (slow queries)
    performance_logger = logging.getLogger("ocean.performance")
    performance_logger.setLevel(logging.DEBUG)
    performance_logger.propagate = False  # Don't send to root logger

    # Rotating file handler (10MB max, keep 5 backup files)
    file_handler = RotatingFileHandler(
        logs_dir / "queries.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    performance_logger.addHandler(file_handler)

    # Also add console handler to performance logger in debug mode
    if debug:
        performance_logger.addHandler(console_handler)

    # Log startup message
    logging.info("Logging configured successfully")
    logging.info(f"Performance logs: {logs_dir / 'queries.log'}")
