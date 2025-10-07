"""
Sanitizing Logger Wrapper

Automatically sanitizes sensitive data from log messages to prevent
credential leakage in logs.
"""

import logging
import re
from typing import Any, Dict, List, Optional


class SanitizingLogger:
    """
    Logger wrapper that automatically sanitizes sensitive data.

    Redacts sensitive patterns like tokens, secrets, passwords, and API keys
    from log messages before they are written.

    Args:
        logger: Base logger instance to wrap
        patterns: Optional list of additional regex patterns to sanitize
        replacement: String to replace sensitive data with (default: "***REDACTED***")
    """

    # Default sensitive patterns
    DEFAULT_PATTERNS = [
        # API tokens and keys
        (r"(client_token[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(client_secret[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(access_token[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(api_key[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(api_token[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        # Passwords
        (r"(password[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(passwd[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(pwd[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        # Authorization headers
        (r"(Authorization:\s*)(Bearer\s+[^\s]+)", r"\1Bearer ***REDACTED***"),
        (r"(Authorization:\s*)(Basic\s+[^\s]+)", r"\1Basic ***REDACTED***"),
        # AWS keys (example pattern)
        (r"(AKIA[0-9A-Z]{16})", r"***REDACTED_AWS_KEY***"),
        # Generic secret patterns
        (r"(secret[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
        (r"(token[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***REDACTED***"),
    ]

    def __init__(
        self,
        logger: logging.Logger,
        patterns: Optional[List[tuple]] = None,
        replacement: str = "***REDACTED***",
    ):
        self.logger = logger
        self.replacement = replacement

        # Combine default and custom patterns
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if patterns:
            self.patterns.extend(patterns)

        # Compile regex patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), repl)
            for pattern, repl in self.patterns
        ]

    def _sanitize(self, message: str) -> str:
        """
        Sanitize sensitive data from message.

        Args:
            message: Original log message

        Returns:
            Sanitized message with sensitive data redacted
        """
        sanitized = str(message)

        for pattern, replacement in self.compiled_patterns:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def _format_extra(self, extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sanitize extra context dictionary.

        Args:
            extra: Extra context dictionary

        Returns:
            Sanitized extra dictionary
        """
        if not extra:
            return {}

        sanitized_extra = {}
        for key, value in extra.items():
            if isinstance(value, str):
                sanitized_extra[key] = self._sanitize(value)
            elif isinstance(value, dict):
                sanitized_extra[key] = self._format_extra(value)
            else:
                sanitized_extra[key] = value

        return sanitized_extra

    def debug(self, message: str, *args, **kwargs):
        """Log debug message with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.debug(sanitized_message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.info(sanitized_message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.warning(sanitized_message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.error(sanitized_message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.critical(sanitized_message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with sanitization"""
        sanitized_message = self._sanitize(message)
        if "extra" in kwargs:
            kwargs["extra"] = self._format_extra(kwargs["extra"])
        self.logger.exception(sanitized_message, *args, **kwargs)

    def add_pattern(self, pattern: str, replacement: Optional[str] = None):
        """
        Add custom sanitization pattern.

        Args:
            pattern: Regex pattern to match
            replacement: Replacement string (uses default if None)
        """
        repl = replacement or self.replacement
        self.patterns.append((pattern, repl))
        self.compiled_patterns.append((re.compile(pattern, re.IGNORECASE), repl))


def create_sanitizing_logger(
    base_logger: logging.Logger,
    patterns: Optional[List[tuple]] = None,
) -> SanitizingLogger:
    """
    Factory function to create sanitizing logger.

    Args:
        base_logger: Base logger to wrap
        patterns: Optional additional patterns

    Returns:
        SanitizingLogger instance
    """
    return SanitizingLogger(base_logger, patterns=patterns)
