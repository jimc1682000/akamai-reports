"""
Error and Request Context Management

Provides rich context tracking for errors and API requests,
enabling better debugging and error analysis.
"""

import contextvars
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from tools.lib.tracing.correlation import get_correlation_id


# Thread-local storage for request context
_request_context: contextvars.ContextVar[Optional["RequestContext"]] = (
    contextvars.ContextVar("request_context", default=None)
)


@dataclass
class RequestContext:
    """
    Context information for API requests.

    Tracks request metadata for correlation and debugging.

    Attributes:
        correlation_id: Unique request identifier
        api_endpoint: API endpoint being called
        start_time: Request start timestamp
        params: Request parameters
        metadata: Additional context metadata
    """

    correlation_id: str
    api_endpoint: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.

        Returns:
            dict: Context as dictionary
        """
        return {
            "correlation_id": self.correlation_id,
            "api_endpoint": self.api_endpoint,
            "start_time": self.start_time.isoformat() + "Z",
            "params": self.params,
            "metadata": self.metadata,
        }

    def get_duration_ms(self) -> float:
        """
        Calculate request duration in milliseconds.

        Returns:
            float: Duration in milliseconds
        """
        delta = datetime.utcnow() - self.start_time
        return delta.total_seconds() * 1000


@dataclass
class ErrorContext:
    """
    Enhanced error context with tracing information.

    Provides comprehensive error information for debugging and logging.

    Attributes:
        error_type: Type of exception
        error_message: Error message
        stack_trace: Full stack trace
        correlation_id: Request correlation ID
        request_context: Request context if available
        timestamp: When error occurred
        additional_context: Extra debugging information
    """

    error_type: str
    error_message: str
    stack_trace: str
    correlation_id: Optional[str] = None
    request_context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_exception(
        cls, exception: Exception, additional_context: Optional[Dict[str, Any]] = None
    ) -> "ErrorContext":
        """
        Create ErrorContext from an exception.

        Args:
            exception: Exception to capture
            additional_context: Extra context information

        Returns:
            ErrorContext: Error context with full details
        """
        # Get current correlation ID and request context
        correlation_id = get_correlation_id()
        req_ctx = get_current_context()

        return cls(
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            correlation_id=correlation_id,
            request_context=req_ctx.to_dict() if req_ctx else None,
            additional_context=additional_context or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error context to dictionary.

        Returns:
            dict: Error context as dictionary
        """
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "correlation_id": self.correlation_id,
            "request_context": self.request_context,
            "timestamp": self.timestamp.isoformat() + "Z",
            "additional_context": self.additional_context,
        }


def get_current_context() -> Optional[RequestContext]:
    """
    Get the current request context.

    Returns:
        Optional[RequestContext]: Current context or None
    """
    return _request_context.get()


def set_current_context(context: RequestContext) -> None:
    """
    Set the current request context.

    Args:
        context: Request context to set
    """
    _request_context.set(context)


def clear_current_context() -> None:
    """Clear the current request context."""
    _request_context.set(None)
