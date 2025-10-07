#!/usr/bin/env python3
"""
Unit Tests for Error Context and Tracing

Tests for correlation ID management, request context, and error context tracking.
"""

import unittest
from datetime import datetime

from tools.lib.tracing import (
    CorrelationIDMiddleware,
    ErrorContext,
    RequestContext,
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    get_current_context,
    set_correlation_id,
    set_current_context,
)


class TestCorrelationID(unittest.TestCase):
    """Test cases for correlation ID management"""

    def tearDown(self):
        """Clean up correlation ID after each test"""
        clear_correlation_id()

    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        corr_id = generate_correlation_id()
        self.assertIsNotNone(corr_id)
        self.assertIsInstance(corr_id, str)
        self.assertGreater(len(corr_id), 0)

        # Generate another to ensure uniqueness
        corr_id2 = generate_correlation_id()
        self.assertNotEqual(corr_id, corr_id2)

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        test_id = "test-correlation-id-12345"
        set_correlation_id(test_id)

        retrieved_id = get_correlation_id()
        self.assertEqual(retrieved_id, test_id)

    def test_clear_correlation_id(self):
        """Test clearing correlation ID"""
        set_correlation_id("test-id")
        self.assertIsNotNone(get_correlation_id())

        clear_correlation_id()
        self.assertIsNone(get_correlation_id())

    def test_get_correlation_id_when_not_set(self):
        """Test getting correlation ID when not set returns None"""
        clear_correlation_id()
        self.assertIsNone(get_correlation_id())


class TestCorrelationIDMiddleware(unittest.TestCase):
    """Test cases for CorrelationIDMiddleware"""

    def tearDown(self):
        """Clean up correlation ID after each test"""
        clear_correlation_id()

    def test_middleware_auto_generates_id(self):
        """Test middleware auto-generates correlation ID"""
        with CorrelationIDMiddleware(auto_generate=True) as corr_id:
            self.assertIsNotNone(corr_id)
            self.assertEqual(corr_id, get_correlation_id())

    def test_middleware_preserves_existing_id(self):
        """Test middleware preserves existing correlation ID"""
        existing_id = "existing-correlation-id"
        set_correlation_id(existing_id)

        with CorrelationIDMiddleware(auto_generate=True) as corr_id:
            self.assertEqual(corr_id, existing_id)

    def test_middleware_without_auto_generate(self):
        """Test middleware without auto-generation"""
        with CorrelationIDMiddleware(auto_generate=False) as corr_id:
            self.assertIsNone(corr_id)


class TestRequestContext(unittest.TestCase):
    """Test cases for RequestContext"""

    def test_create_request_context(self):
        """Test creating request context"""
        ctx = RequestContext(
            correlation_id="test-id-123",
            api_endpoint="https://api.example.com/traffic",
            params={"start": "2025-01-01", "end": "2025-01-07"},
            metadata={"api_type": "Traffic"},
        )

        self.assertEqual(ctx.correlation_id, "test-id-123")
        self.assertEqual(ctx.api_endpoint, "https://api.example.com/traffic")
        self.assertEqual(ctx.params["start"], "2025-01-01")
        self.assertEqual(ctx.metadata["api_type"], "Traffic")

    def test_request_context_to_dict(self):
        """Test converting request context to dictionary"""
        ctx = RequestContext(
            correlation_id="test-id-456",
            api_endpoint="https://api.example.com/emissions",
        )

        ctx_dict = ctx.to_dict()
        self.assertEqual(ctx_dict["correlation_id"], "test-id-456")
        self.assertEqual(ctx_dict["api_endpoint"], "https://api.example.com/emissions")
        self.assertIn("start_time", ctx_dict)
        self.assertIn("params", ctx_dict)
        self.assertIn("metadata", ctx_dict)

    def test_request_context_get_duration(self):
        """Test request context duration calculation"""
        ctx = RequestContext(
            correlation_id="test-id", api_endpoint="https://api.example.com"
        )

        import time

        time.sleep(0.01)  # Sleep 10ms
        duration_ms = ctx.get_duration_ms()

        self.assertGreater(duration_ms, 5)  # Should be > 5ms


class TestErrorContext(unittest.TestCase):
    """Test cases for ErrorContext"""

    def test_create_error_context_from_exception(self):
        """Test creating error context from exception"""
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            error_ctx = ErrorContext.from_exception(
                e, additional_context={"test_key": "test_value"}
            )

            self.assertEqual(error_ctx.error_type, "ValueError")
            self.assertEqual(error_ctx.error_message, "Test error message")
            self.assertIn("ValueError", error_ctx.stack_trace)
            self.assertEqual(error_ctx.additional_context["test_key"], "test_value")

    def test_error_context_captures_correlation_id(self):
        """Test error context captures correlation ID"""
        test_corr_id = "error-test-correlation-id"
        set_correlation_id(test_corr_id)

        try:
            raise RuntimeError("Test error")
        except RuntimeError as e:
            error_ctx = ErrorContext.from_exception(e)
            self.assertEqual(error_ctx.correlation_id, test_corr_id)

        clear_correlation_id()

    def test_error_context_captures_request_context(self):
        """Test error context captures request context"""
        req_ctx = RequestContext(
            correlation_id="req-ctx-test-id",
            api_endpoint="https://api.example.com/test",
        )
        set_current_context(req_ctx)

        try:
            raise KeyError("Test key error")
        except KeyError as e:
            error_ctx = ErrorContext.from_exception(e)
            self.assertIsNotNone(error_ctx.request_context)
            self.assertEqual(
                error_ctx.request_context["correlation_id"], "req-ctx-test-id"
            )
            self.assertEqual(
                error_ctx.request_context["api_endpoint"],
                "https://api.example.com/test",
            )

    def test_error_context_to_dict(self):
        """Test converting error context to dictionary"""
        try:
            raise TypeError("Test type error")
        except TypeError as e:
            error_ctx = ErrorContext.from_exception(
                e, additional_context={"custom": "data"}
            )

            error_dict = error_ctx.to_dict()
            self.assertEqual(error_dict["error_type"], "TypeError")
            self.assertEqual(error_dict["error_message"], "Test type error")
            self.assertIn("stack_trace", error_dict)
            self.assertIn("timestamp", error_dict)
            self.assertEqual(error_dict["additional_context"]["custom"], "data")


class TestRequestContextManagement(unittest.TestCase):
    """Test cases for request context management functions"""

    def test_set_and_get_current_context(self):
        """Test setting and getting current context"""
        ctx = RequestContext(
            correlation_id="context-test-id", api_endpoint="https://api.example.com"
        )
        set_current_context(ctx)

        retrieved_ctx = get_current_context()
        self.assertIsNotNone(retrieved_ctx)
        self.assertEqual(retrieved_ctx.correlation_id, "context-test-id")

    def test_get_current_context_when_not_set(self):
        """Test getting current context when not set"""
        # Ensure clean state
        from tools.lib.tracing.context import clear_current_context

        clear_current_context()

        ctx = get_current_context()
        self.assertIsNone(ctx)


if __name__ == "__main__":
    unittest.main()
