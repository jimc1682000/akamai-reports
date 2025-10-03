"""
Correlation ID Management

Provides correlation ID generation and tracking for distributed tracing
and error tracking across API calls.
"""

import contextvars
import uuid
from typing import Optional


# Thread-local storage for correlation ID
_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID using UUID4.

    Returns:
        str: New correlation ID in format 'xxxx-xxxx-xxxx-xxxx'
    """
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Optional[str]: Current correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in current context.

    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from current context."""
    _correlation_id.set(None)


class CorrelationIDMiddleware:
    """
    Middleware to automatically manage correlation IDs.

    Ensures every request has a correlation ID for tracking
    across multiple API calls and error contexts.
    """

    def __init__(self, auto_generate: bool = True):
        """
        Initialize correlation ID middleware.

        Args:
            auto_generate: Automatically generate correlation ID if not present
        """
        self.auto_generate = auto_generate

    def __enter__(self):
        """Enter context - generate correlation ID if needed"""
        if self.auto_generate and not get_correlation_id():
            set_correlation_id(generate_correlation_id())
        return get_correlation_id()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - optionally clear correlation ID"""
        # Keep correlation ID for the entire request lifecycle
        # Only clear explicitly if needed
        pass
