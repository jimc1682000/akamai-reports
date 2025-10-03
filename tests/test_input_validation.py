#!/usr/bin/env python3
"""
Unit Tests for Input Validation

Tests for date validation and sanitization in traffic.py
"""

import argparse
import unittest

from traffic import validate_date_format


class TestDateValidation(unittest.TestCase):
    """Test cases for date validation function"""

    def test_valid_yyyy_mm_dd_format(self):
        """Test validation of YYYY-MM-DD format"""
        result = validate_date_format("2025-01-01")
        self.assertEqual(result, "2025-01-01T00:00:00Z")

    def test_valid_iso8601_format(self):
        """Test validation of ISO-8601 format"""
        result = validate_date_format("2025-01-01T12:30:45Z")
        self.assertEqual(result, "2025-01-01T12:30:45Z")

    def test_valid_iso8601_without_z(self):
        """Test validation of ISO-8601 format without Z"""
        result = validate_date_format("2025-01-01T12:30:45")
        self.assertEqual(result, "2025-01-01T12:30:45Z")

    def test_yyyy_mm_dd_sets_time_to_midnight(self):
        """Test that YYYY-MM-DD format sets time to 00:00:00"""
        result = validate_date_format("2025-06-15")
        self.assertEqual(result, "2025-06-15T00:00:00Z")

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_date_format("2025/01/01")  # Wrong delimiter

        self.assertIn("Invalid date format", str(context.exception))
        self.assertIn("2025/01/01", str(context.exception))

    def test_invalid_date_raises_error(self):
        """Test that invalid date raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("2025-13-01")  # Invalid month

    def test_invalid_day_raises_error(self):
        """Test that invalid day raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("2025-02-30")  # Invalid day for February

    def test_malformed_string_raises_error(self):
        """Test that malformed string raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("not-a-date")

    def test_empty_string_raises_error(self):
        """Test that empty string raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("")

    def test_partial_date_raises_error(self):
        """Test that partial date raises ArgumentTypeError"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("2025-01")  # Missing day

    def test_leap_year_february_29(self):
        """Test that Feb 29 is valid in leap year"""
        result = validate_date_format("2024-02-29")  # 2024 is leap year
        self.assertEqual(result, "2024-02-29T00:00:00Z")

    def test_non_leap_year_february_29_raises_error(self):
        """Test that Feb 29 is invalid in non-leap year"""
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_date_format("2025-02-29")  # 2025 is not leap year

    def test_error_message_includes_expected_format(self):
        """Test that error message includes helpful format information"""
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_date_format("invalid")

        error_msg = str(context.exception)
        self.assertIn("YYYY-MM-DD", error_msg)
        self.assertIn("ISO-8601", error_msg)
        self.assertIn("2025-01-01", error_msg)

    def test_consistent_output_format(self):
        """Test that output is always in consistent format"""
        inputs = [
            "2025-01-01",
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:00",
        ]

        results = [validate_date_format(inp) for inp in inputs]

        # All should produce the same normalized output
        expected = "2025-01-01T00:00:00Z"
        for result in results:
            self.assertEqual(result, expected)

    def test_preserves_time_component(self):
        """Test that time component is preserved for ISO-8601"""
        result = validate_date_format("2025-06-15T14:30:00Z")
        self.assertEqual(result, "2025-06-15T14:30:00Z")

    def test_various_valid_dates(self):
        """Test various valid dates throughout the year"""
        test_cases = [
            ("2025-01-01", "2025-01-01T00:00:00Z"),
            ("2025-12-31", "2025-12-31T00:00:00Z"),
            ("2025-06-15", "2025-06-15T00:00:00Z"),
            ("2025-02-28", "2025-02-28T00:00:00Z"),
        ]

        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = validate_date_format(input_date)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
