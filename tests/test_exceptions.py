#!/usr/bin/env python3
"""
Tests for custom exception hierarchy.

Tests each exception class instantiation, inheritance, and message formatting.
"""

import pytest

from tools.lib.exceptions import (
    AkamaiAPIError,
    APIAuthenticationError,
    APIAuthorizationError,
    APINetworkError,
    APIRateLimitError,
    APIRequestError,
    APIServerError,
    APITimeoutError,
)


class TestExceptionHierarchy:
    """Test custom exception inheritance"""

    def test_all_exceptions_inherit_from_akamai_api_error(self):
        """Verify all custom exceptions inherit from AkamaiAPIError"""
        exceptions = [
            APIRequestError(400, "test"),
            APIAuthenticationError(),
            APIAuthorizationError(),
            APIRateLimitError(),
            APIServerError(500),
            APITimeoutError(),
            APINetworkError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, AkamaiAPIError)
            assert isinstance(exc, Exception)

    def test_base_exception_is_exception_subclass(self):
        """Verify AkamaiAPIError inherits from Exception"""
        exc = AkamaiAPIError("test error")
        assert isinstance(exc, Exception)


class TestAPIRequestError:
    """Test APIRequestError exception"""

    def test_instantiation_with_status_and_message(self):
        """Test creating APIRequestError with status code and message"""
        exc = APIRequestError(400, "Bad Request")
        assert exc.status_code == 400
        assert exc.message == "Bad Request"
        assert str(exc) == "HTTP 400: Bad Request"

    def test_different_status_codes(self):
        """Test APIRequestError with different status codes"""
        exc_400 = APIRequestError(400, "Bad Request")
        exc_404 = APIRequestError(404, "Not Found")

        assert exc_400.status_code == 400
        assert exc_404.status_code == 404
        assert str(exc_400) == "HTTP 400: Bad Request"
        assert str(exc_404) == "HTTP 404: Not Found"


class TestAPIAuthenticationError:
    """Test APIAuthenticationError exception"""

    def test_instantiation_without_message(self):
        """Test creating APIAuthenticationError without message"""
        exc = APIAuthenticationError()
        assert isinstance(exc, AkamaiAPIError)

    def test_instantiation_with_message(self):
        """Test creating APIAuthenticationError with message"""
        exc = APIAuthenticationError("Authentication failed (401)")
        assert str(exc) == "Authentication failed (401)"


class TestAPIAuthorizationError:
    """Test APIAuthorizationError exception"""

    def test_instantiation_without_message(self):
        """Test creating APIAuthorizationError without message"""
        exc = APIAuthorizationError()
        assert isinstance(exc, AkamaiAPIError)

    def test_instantiation_with_message(self):
        """Test creating APIAuthorizationError with message"""
        exc = APIAuthorizationError("Authorization failed (403)")
        assert str(exc) == "Authorization failed (403)"


class TestAPIRateLimitError:
    """Test APIRateLimitError exception"""

    def test_instantiation_without_retry_after(self):
        """Test creating APIRateLimitError without retry_after"""
        exc = APIRateLimitError()
        assert exc.retry_after is None
        assert str(exc) == "Rate limit exceeded"

    def test_instantiation_with_retry_after(self):
        """Test creating APIRateLimitError with retry_after"""
        exc = APIRateLimitError(retry_after=60)
        assert exc.retry_after == 60
        assert str(exc) == "Rate limit exceeded, retry after 60 seconds"

    def test_different_retry_after_values(self):
        """Test APIRateLimitError with different retry_after values"""
        exc_30 = APIRateLimitError(retry_after=30)
        exc_120 = APIRateLimitError(retry_after=120)

        assert exc_30.retry_after == 30
        assert exc_120.retry_after == 120
        assert str(exc_30) == "Rate limit exceeded, retry after 30 seconds"
        assert str(exc_120) == "Rate limit exceeded, retry after 120 seconds"


class TestAPIServerError:
    """Test APIServerError exception"""

    def test_instantiation_with_status_code(self):
        """Test creating APIServerError with status code"""
        exc = APIServerError(500)
        assert exc.status_code == 500
        assert str(exc) == "Server error: HTTP 500"

    def test_different_server_error_codes(self):
        """Test APIServerError with different 5xx status codes"""
        exc_500 = APIServerError(500)
        exc_502 = APIServerError(502)
        exc_503 = APIServerError(503)

        assert exc_500.status_code == 500
        assert exc_502.status_code == 502
        assert exc_503.status_code == 503

        assert str(exc_500) == "Server error: HTTP 500"
        assert str(exc_502) == "Server error: HTTP 502"
        assert str(exc_503) == "Server error: HTTP 503"


class TestAPITimeoutError:
    """Test APITimeoutError exception"""

    def test_instantiation_without_message(self):
        """Test creating APITimeoutError without message"""
        exc = APITimeoutError()
        assert isinstance(exc, AkamaiAPIError)

    def test_instantiation_with_message(self):
        """Test creating APITimeoutError with message"""
        exc = APITimeoutError("Request timeout")
        assert str(exc) == "Request timeout"


class TestAPINetworkError:
    """Test APINetworkError exception"""

    def test_instantiation_without_message(self):
        """Test creating APINetworkError without message"""
        exc = APINetworkError()
        assert isinstance(exc, AkamaiAPIError)

    def test_instantiation_with_message(self):
        """Test creating APINetworkError with message"""
        exc = APINetworkError("Network error: Connection refused")
        assert str(exc) == "Network error: Connection refused"

    def test_network_error_with_chained_exception(self):
        """Test APINetworkError with exception chaining"""
        original_error = ConnectionError("Connection refused")
        try:
            raise APINetworkError("Network error") from original_error
        except APINetworkError as exc:
            assert isinstance(exc, AkamaiAPIError)
            assert exc.__cause__ is original_error


class TestExceptionRaising:
    """Test raising and catching custom exceptions"""

    def test_raise_and_catch_api_request_error(self):
        """Test raising and catching APIRequestError"""
        with pytest.raises(APIRequestError) as exc_info:
            raise APIRequestError(400, "Bad Request")

        assert exc_info.value.status_code == 400
        assert exc_info.value.message == "Bad Request"

    def test_raise_and_catch_authentication_error(self):
        """Test raising and catching APIAuthenticationError"""
        with pytest.raises(APIAuthenticationError):
            raise APIAuthenticationError("Auth failed")

    def test_raise_and_catch_base_exception(self):
        """Test catching specific exception as base AkamaiAPIError"""
        with pytest.raises(AkamaiAPIError):
            raise APIAuthenticationError("Auth failed")

    def test_exception_hierarchy_catch_order(self):
        """Test exception catching respects hierarchy"""
        # Specific exception should be caught first
        try:
            raise APIAuthenticationError("Auth failed")
        except APIAuthenticationError:
            caught_type = "specific"
        except AkamaiAPIError:
            caught_type = "base"

        assert caught_type == "specific"

        # Base exception should catch all custom exceptions
        try:
            raise APIServerError(500)
        except AkamaiAPIError as e:
            caught_type = "base"
            caught_exception = e

        assert caught_type == "base"
        assert isinstance(caught_exception, APIServerError)
