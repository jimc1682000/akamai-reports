#!/usr/bin/env python3
"""
Custom exceptions for Akamai API operations.

This module provides a hierarchy of exception classes for precise error handling
in Akamai V2 Traffic and Emissions API interactions. All exceptions inherit from
the base AkamaiAPIError class, enabling unified error handling while allowing
specific error type discrimination.

Exception Hierarchy:
    AkamaiAPIError (base)
    ├── APIRequestError (400 Bad Request)
    ├── APIAuthenticationError (401 Unauthorized)
    ├── APIAuthorizationError (403 Forbidden)
    ├── APIRateLimitError (429 Too Many Requests)
    ├── APIServerError (500+ Server Errors)
    ├── APITimeoutError (Request Timeout)
    └── APINetworkError (Network Connection Errors)

Usage Example:
    try:
        response = call_traffic_api(...)
    except APIAuthenticationError:
        print("Please check your .edgerc credentials")
    except APIRateLimitError as e:
        print(f"Rate limited, retry after {e.retry_after} seconds")
    except AkamaiAPIError as e:
        print(f"API error: {e}")
"""


class AkamaiAPIError(Exception):
    """
    Base exception for all Akamai API errors.

    This is the parent class for all custom exceptions in this module.
    Catch this exception to handle any Akamai API-related error.
    """

    pass


class APIRequestError(AkamaiAPIError):
    """
    Raised when API request fails due to invalid parameters (400 Bad Request).

    Attributes:
        status_code (int): HTTP status code from the API response
        message (str): Detailed error message from the API
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class APIAuthenticationError(AkamaiAPIError):
    """
    Raised when authentication fails (401 Unauthorized).

    This typically indicates invalid or missing EdgeGrid credentials in ~/.edgerc
    or incorrect section name being used for authentication.
    """

    pass


class APIAuthorizationError(AkamaiAPIError):
    """
    Raised when authorization fails (403 Forbidden).

    This indicates the authenticated user lacks sufficient permissions to access
    the requested API endpoint or resource.
    """

    pass


class APIRateLimitError(AkamaiAPIError):
    """
    Raised when rate limit is exceeded (429 Too Many Requests).

    Attributes:
        retry_after (int, optional): Suggested number of seconds to wait before retry
    """

    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after} seconds"
        super().__init__(msg)


class APIServerError(AkamaiAPIError):
    """
    Raised when server error occurs (500, 502, 503, 504, etc.).

    Attributes:
        status_code (int): HTTP status code (500+)
    """

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"Server error: HTTP {status_code}")


class APITimeoutError(AkamaiAPIError):
    """
    Raised when request times out.

    This occurs when the API does not respond within the configured timeout period.
    Consider checking network connectivity or increasing the timeout threshold.
    """

    pass


class APINetworkError(AkamaiAPIError):
    """
    Raised when network error occurs during API communication.

    This includes DNS resolution failures, connection refused, network unreachable,
    and other low-level network issues.
    """

    pass


__all__ = [
    "AkamaiAPIError",
    "APIRequestError",
    "APIAuthenticationError",
    "APIAuthorizationError",
    "APIRateLimitError",
    "APIServerError",
    "APITimeoutError",
    "APINetworkError",
]
