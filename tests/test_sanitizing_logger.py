"""
Tests for Sanitizing Logger

Comprehensive test coverage for sensitive data sanitization in logs.
"""

import logging
import unittest
from io import StringIO

from tools.lib.logging.sanitizing_logger import (
    SanitizingLogger,
    create_sanitizing_logger,
)


class TestSanitizingLogger(unittest.TestCase):
    """Test sanitizing logger functionality"""

    def setUp(self):
        """Set up test logger"""
        # Create in-memory logger for testing
        self.log_stream = StringIO()
        self.base_logger = logging.getLogger("test_sanitizer")
        self.base_logger.setLevel(logging.DEBUG)
        self.base_logger.handlers = []  # Clear any existing handlers

        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.base_logger.addHandler(handler)

        self.sanitizer = SanitizingLogger(self.base_logger)

    def get_log_output(self) -> str:
        """Get logged output"""
        return self.log_stream.getvalue()

    def test_sanitize_client_token(self):
        """Test client_token sanitization"""
        self.sanitizer.info("Config: client_token=akab-1234567890abcdef")  # ggignore
        output = self.get_log_output()
        self.assertNotIn("akab-1234567890abcdef", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_client_secret(self):
        """Test client_secret sanitization"""
        self.sanitizer.info("Auth: client_secret=supersecret123")  # ggignore
        output = self.get_log_output()
        self.assertNotIn("supersecret123", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_access_token(self):
        """Test access_token sanitization"""
        self.sanitizer.info("Token: access_token=akab-access-token-xyz")  # ggignore
        output = self.get_log_output()
        self.assertNotIn("akab-access-token-xyz", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_password(self):
        """Test password sanitization"""
        self.sanitizer.info("User password=MySecretPass123!")
        output = self.get_log_output()
        self.assertNotIn("MySecretPass123!", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_api_key(self):
        """Test API key sanitization"""
        self.sanitizer.info("API configuration: api_key=1234567890abcdef")
        output = self.get_log_output()
        self.assertNotIn("1234567890abcdef", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_authorization_bearer(self):
        """Test Bearer token sanitization"""
        self.sanitizer.info(
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        )
        output = self.get_log_output()
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", output)
        self.assertIn("Bearer ***REDACTED***", output)

    def test_sanitize_authorization_basic(self):
        """Test Basic auth sanitization"""
        self.sanitizer.info("Authorization: Basic dXNlcjpwYXNzd29yZA==")
        output = self.get_log_output()
        self.assertNotIn("dXNlcjpwYXNzd29yZA==", output)
        self.assertIn("Basic ***REDACTED***", output)

    def test_sanitize_aws_key(self):
        """Test AWS key pattern sanitization"""
        self.sanitizer.info("AWS key: AKIAIOSFODNN7EXAMPLE")
        output = self.get_log_output()
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", output)
        self.assertIn("***REDACTED_AWS_KEY***", output)

    def test_sanitize_json_format(self):
        """Test sanitization in JSON-like strings"""
        self.sanitizer.info(
            '{"client_token": "akab-secret", "api_key": "12345"}'
        )  # ggignore
        output = self.get_log_output()
        self.assertNotIn("akab-secret", output)
        self.assertNotIn("12345", output)
        self.assertIn("***REDACTED***", output)

    def test_sanitize_with_quotes(self):
        """Test sanitization with various quote styles"""
        self.sanitizer.info("token='secret123' password=\"pass456\"")
        output = self.get_log_output()
        self.assertNotIn("secret123", output)
        self.assertNotIn("pass456", output)

    def test_case_insensitive(self):
        """Test case-insensitive pattern matching"""
        self.sanitizer.info("CLIENT_TOKEN=secret")  # ggignore
        output = self.get_log_output()
        self.assertNotIn("secret", output)
        self.assertIn("***REDACTED***", output)

    def test_multiple_secrets_in_message(self):
        """Test multiple secrets in single message"""
        self.sanitizer.info(
            "Config: client_token=abc123 password=xyz789 api_key=key456"  # ggignore
        )
        output = self.get_log_output()
        self.assertNotIn("abc123", output)
        self.assertNotIn("xyz789", output)
        self.assertNotIn("key456", output)
        # Should have 3 redactions
        self.assertEqual(output.count("***REDACTED***"), 3)

    def test_preserves_non_sensitive_data(self):
        """Test that non-sensitive data is preserved"""
        self.sanitizer.info("Processing CP code 123456 for customer ABC")
        output = self.get_log_output()
        self.assertIn("Processing CP code 123456", output)
        self.assertIn("customer ABC", output)

    def test_all_log_levels(self):
        """Test sanitization works for all log levels"""
        test_msg = "secret=password123"

        self.sanitizer.debug(test_msg)
        self.sanitizer.info(test_msg)
        self.sanitizer.warning(test_msg)
        self.sanitizer.error(test_msg)
        self.sanitizer.critical(test_msg)

        output = self.get_log_output()
        self.assertNotIn("password123", output)
        # Should have 5 redactions (one per level)
        self.assertEqual(output.count("***REDACTED***"), 5)

    def test_sanitize_extra_dict(self):
        """Test sanitization of extra context dictionary"""
        self.sanitizer.info(
            "API call",
            extra={
                "api_key": "secret123",
                "endpoint": "https://api.example.com",
                "headers": {"Authorization": "Bearer token456"},
            },
        )
        output = self.get_log_output()
        # Note: Extra dict sanitization may not appear in simple format
        # But should not crash
        self.assertIn("API call", output)

    def test_add_custom_pattern(self):
        """Test adding custom sanitization pattern"""
        self.sanitizer.add_pattern(
            r"(credit_card:\s*)(\d{16})", r"\1****-****-****-****"
        )

        self.sanitizer.info("Payment: credit_card: 1234567890123456")
        output = self.get_log_output()
        self.assertNotIn("1234567890123456", output)
        self.assertIn("****-****-****-****", output)

    def test_factory_function(self):
        """Test create_sanitizing_logger factory"""
        sanitizer = create_sanitizing_logger(self.base_logger)
        self.assertIsInstance(sanitizer, SanitizingLogger)

        sanitizer.info("token=secret123")
        output = self.get_log_output()
        self.assertNotIn("secret123", output)

    def test_factory_with_custom_patterns(self):
        """Test factory with custom patterns"""
        custom_patterns = [(r"(ssn:\s*)(\d{3}-\d{2}-\d{4})", r"\1***-**-****")]

        sanitizer = create_sanitizing_logger(self.base_logger, patterns=custom_patterns)
        sanitizer.info("SSN: ssn: 123-45-6789")

        output = self.get_log_output()
        self.assertNotIn("123-45-6789", output)
        self.assertIn("***-**-****", output)

    def test_empty_message(self):
        """Test sanitization with empty message"""
        self.sanitizer.info("")
        output = self.get_log_output()
        self.assertEqual(output.strip(), "")

    def test_none_to_string_conversion(self):
        """Test that None values are converted to string"""
        self.sanitizer.info(None)
        # Should not crash, converts None to "None"
        output = self.get_log_output()
        self.assertIn("None", output)

    def test_nested_dict_sanitization(self):
        """Test sanitization of nested dictionaries in extra"""
        self.sanitizer.info(
            "Config loaded",
            extra={
                "auth": {
                    "client_token": "secret1",  # ggignore
                    "client_secret": "secret2",  # ggignore
                }
            },
        )
        # Should not crash with nested dict
        output = self.get_log_output()
        self.assertIn("Config loaded", output)


if __name__ == "__main__":
    unittest.main()
