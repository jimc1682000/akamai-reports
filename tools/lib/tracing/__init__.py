"""
Error Context and Tracing Module

This package provides enhanced error tracking with correlation IDs,
request context, and detailed stack traces for debugging.
"""

from tools.lib.tracing.context import (
    ErrorContext,
    RequestContext,
    get_current_context,
    set_current_context,
)
from tools.lib.tracing.correlation import (
    CorrelationIDMiddleware,
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)


__all__ = [
    "ErrorContext",
    "RequestContext",
    "get_current_context",
    "set_current_context",
    "CorrelationIDMiddleware",
    "clear_correlation_id",
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
]
