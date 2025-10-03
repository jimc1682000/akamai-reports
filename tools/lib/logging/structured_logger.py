"""
Structured Logging Implementation

This module provides JSON-formatted structured logging for machine-parsable logs
suitable for log aggregation systems (ELK, Splunk, Datadog).
"""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format with additional context fields for better
    observability and log aggregation.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom context fields if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "api_endpoint"):
            log_data["api_endpoint"] = record.api_endpoint

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        if hasattr(record, "data_points"):
            log_data["data_points"] = record.data_points

        # Add any extra fields passed to logger
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.

    Provides colored and well-formatted logs for terminal display.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in human-readable format"""
        return record.getMessage()


class StructuredLogger:
    """
    Structured logger wrapper providing both JSON and human-readable output.

    Attributes:
        logger: Underlying Python logger instance
        structured_mode: Whether to use JSON formatting
    """

    def __init__(self, name: str, structured_mode: bool = False):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            structured_mode: Enable JSON formatting (default: False for compatibility)
        """
        self.logger = logging.getLogger(name)
        self.structured_mode = structured_mode

    def _log_with_context(
        self, level: int, message: str, **context: Dict[str, Any]
    ) -> None:
        """
        Log message with additional context fields.

        Args:
            level: Log level
            message: Log message
            **context: Additional context fields
        """
        if context:
            # Create log record with extra fields
            extra = {"extra_fields": context}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def info(self, message: str, **context: Dict[str, Any]) -> None:
        """Log info message with optional context"""
        self._log_with_context(logging.INFO, message, **context)

    def warning(self, message: str, **context: Dict[str, Any]) -> None:
        """Log warning message with optional context"""
        self._log_with_context(logging.WARNING, message, **context)

    def error(self, message: str, **context: Dict[str, Any]) -> None:
        """Log error message with optional context"""
        self._log_with_context(logging.ERROR, message, **context)

    def debug(self, message: str, **context: Dict[str, Any]) -> None:
        """Log debug message with optional context"""
        self._log_with_context(logging.DEBUG, message, **context)


def setup_structured_logging(
    log_file: str = "logs/weekly_report.log",
    log_level: str = "INFO",
    enable_structured: bool = False,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> StructuredLogger:
    """
    Setup structured logging with both console and file handlers.

    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_structured: Enable JSON formatting for file logs
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        StructuredLogger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get or create logger
    logger_name = "akamai_traffic"
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(HumanReadableFormatter())
    logger.addHandler(console_handler)

    # File handler with optional JSON formatting
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))

    if enable_structured:
        # JSON format for machine parsing
        file_handler.setFormatter(StructuredFormatter())
    else:
        # Traditional format for backward compatibility
        traditional_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(traditional_format)

    logger.addHandler(file_handler)

    return StructuredLogger(logger_name, structured_mode=enable_structured)
