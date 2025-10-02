#!/usr/bin/env python3
"""
Centralized logging configuration for Akamai Traffic Reports.

Provides structured logging to both console and file with configurable levels.
The logger maintains emoji support for console output while providing detailed
information in log files for debugging and monitoring.

Usage:
    from tools.lib.logger import logger

    logger.info("Success message")
    logger.error("API request failed")
    logger.warning("Warning: approaching limit")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "akamai_traffic",
    log_file: Optional[str] = "logs/weekly_report.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup and configure logger with console and file handlers.

    Args:
        name: Logger name (default: "akamai_traffic")
        log_file: Path to log file, None to disable file logging
        console_level: Console logging level (default: INFO)
        file_level: File logging level (default: DEBUG)
        max_bytes: Max log file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured logger instance with console and file handlers
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Console handler - with emoji support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_format = logging.Formatter("%(message)s")  # Simple format for console
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler - with detailed information
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(file_level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance with optional custom name.

    Args:
        name: Optional custom logger name

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return logger
