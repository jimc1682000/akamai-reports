#!/usr/bin/env python3
"""
Unit Tests for time handling functions in traffic.py

Comprehensive test coverage for time processing functionality.
"""

import argparse
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from tools.lib.config_loader import ConfigLoader

# Import functions to test
from tools.lib.time_handler import (
    get_last_week_range,
    get_last_week_range_with_config,
    get_time_range,
    parse_date_string,
    validate_time_range,
)


class TestGetLastWeekRange(unittest.TestCase):
    """Test get_last_week_range function"""

    @patch("tools.lib.time_handler.datetime")
    def test_get_last_week_range_default_sunday_to_saturday(self, mock_datetime):
        """Test default Sunday to Saturday week calculation"""
        # Set up mock date: Wednesday 2025-09-24 12:00:00 UTC
        mock_now = datetime(2025, 9, 24, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range()

        # Expected: Last Sunday (2025-09-14) to Last Saturday (2025-09-20)
        self.assertEqual(start_date, "2025-09-14T00:00:00Z")
        self.assertEqual(end_date, "2025-09-20T23:59:59Z")

    @patch("tools.lib.time_handler.datetime")
    def test_get_last_week_range_monday_to_sunday(self, mock_datetime):
        """Test Monday to Sunday week calculation"""
        # Set up mock date: Wednesday 2025-09-24 12:00:00 UTC
        mock_now = datetime(2025, 9, 24, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range(
            week_start_offset=1, week_duration_days=7
        )

        # Expected: Last Monday (2025-09-15) to Last Sunday (2025-09-21)
        self.assertEqual(start_date, "2025-09-15T00:00:00Z")
        self.assertEqual(end_date, "2025-09-21T23:59:59Z")

    @patch("tools.lib.time_handler.datetime")
    def test_get_last_week_range_monday_to_friday(self, mock_datetime):
        """Test Monday to Friday (work week) calculation"""
        # Set up mock date: Wednesday 2025-09-24 12:00:00 UTC
        mock_now = datetime(2025, 9, 24, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range(
            week_start_offset=1, week_duration_days=5
        )

        # Expected: Last Monday (2025-09-15) to Last Friday (2025-09-19)
        self.assertEqual(start_date, "2025-09-15T00:00:00Z")
        self.assertEqual(end_date, "2025-09-19T23:59:59Z")

    @patch("tools.lib.time_handler.datetime")
    def test_get_last_week_range_custom_start_day(self, mock_datetime):
        """Test custom start day (Wednesday) calculation"""
        # Set up mock date: Friday 2025-09-26 12:00:00 UTC
        mock_now = datetime(2025, 9, 26, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range(
            week_start_offset=3, week_duration_days=7
        )  # Wednesday = 3

        # Expected: Last Wednesday (2025-09-17) to Tuesday (2025-09-23)
        self.assertEqual(start_date, "2025-09-17T00:00:00Z")
        self.assertEqual(end_date, "2025-09-23T23:59:59Z")

    @patch("tools.lib.time_handler.datetime")
    def test_get_last_week_range_boundary_conditions(self, mock_datetime):
        """Test boundary conditions (Sunday, Monday)"""
        # Test on Sunday
        mock_now = datetime(2025, 9, 21, 12, 0, 0)  # Sunday
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range()

        # Expected: Previous Sunday (2025-09-14) to Previous Saturday (2025-09-20)
        self.assertEqual(start_date, "2025-09-14T00:00:00Z")
        self.assertEqual(end_date, "2025-09-20T23:59:59Z")

        # Test on Monday
        mock_now = datetime(2025, 9, 22, 12, 0, 0)  # Monday
        mock_datetime.utcnow.return_value = mock_now

        start_date, end_date = get_last_week_range()

        # Expected: Previous Sunday (2025-09-14) to Previous Saturday (2025-09-20)
        self.assertEqual(start_date, "2025-09-14T00:00:00Z")
        self.assertEqual(end_date, "2025-09-20T23:59:59Z")


class TestGetLastWeekRangeWithConfig(unittest.TestCase):
    """Test get_last_week_range_with_config function"""

    def setUp(self):
        """Set up mock config loader"""
        self.mock_config = MagicMock(spec=ConfigLoader)

    def test_get_last_week_range_with_config_sunday_to_saturday(self):
        """Test config-based week calculation for Sunday to Saturday"""
        self.mock_config.get_week_start_offset.return_value = 0
        self.mock_config.get_week_duration_days.return_value = 7

        with patch("tools.lib.time_handler.get_last_week_range") as mock_get_range:
            mock_get_range.return_value = (
                "YYYY-MM-DDT00:00:00Z",
                "YYYY-MM-DDT23:59:59Z",
            )

            start_date, end_date = get_last_week_range_with_config(self.mock_config)

            mock_get_range.assert_called_once_with(0, 7)
            self.assertEqual(start_date, "YYYY-MM-DDT00:00:00Z")
            self.assertEqual(end_date, "YYYY-MM-DDT23:59:59Z")

    def test_get_last_week_range_with_config_monday_to_friday(self):
        """Test config-based week calculation for Monday to Friday"""
        self.mock_config.get_week_start_offset.return_value = 1
        self.mock_config.get_week_duration_days.return_value = 5

        with patch("tools.lib.time_handler.get_last_week_range") as mock_get_range:
            mock_get_range.return_value = (
                "2025-09-15T00:00:00Z",
                "2025-09-19T23:59:59Z",
            )

            start_date, end_date = get_last_week_range_with_config(self.mock_config)

            mock_get_range.assert_called_once_with(1, 5)
            self.assertEqual(start_date, "2025-09-15T00:00:00Z")
            self.assertEqual(end_date, "2025-09-19T23:59:59Z")


class TestParseDateString(unittest.TestCase):
    """Test parse_date_string function"""

    def test_parse_date_string_start_of_day(self):
        """Test parsing date string for start of day"""
        result = parse_date_string("2025-09-24", end_of_day=False)
        self.assertEqual(result, "2025-09-24T00:00:00Z")

    def test_parse_date_string_end_of_day(self):
        """Test parsing date string for end of day"""
        result = parse_date_string("2025-09-24", end_of_day=True)
        self.assertEqual(result, "2025-09-24T23:59:59Z")

    def test_parse_date_string_invalid_format(self):
        """Test parsing invalid date string format"""
        with self.assertRaises(ValueError) as context:
            parse_date_string("2025/09/24")

        self.assertIn("Invalid date format", str(context.exception))
        self.assertIn("Expected YYYY-MM-DD", str(context.exception))

    def test_parse_date_string_invalid_date(self):
        """Test parsing invalid date"""
        with self.assertRaises(ValueError) as context:
            parse_date_string("2025-13-45")

        self.assertIn("Invalid date format", str(context.exception))


class TestValidateTimeRange(unittest.TestCase):
    """Test validate_time_range function"""

    def test_validate_time_range_valid(self):
        """Test validating valid time range"""
        start_date = "2025-09-01T00:00:00Z"
        end_date = "2025-09-30T23:59:59Z"

        result = validate_time_range(start_date, end_date)
        self.assertTrue(result)

    def test_validate_time_range_start_after_end(self):
        """Test validating time range where start is after end"""
        start_date = "2025-09-30T00:00:00Z"
        end_date = "2025-09-01T23:59:59Z"

        with self.assertRaises(ValueError) as context:
            validate_time_range(start_date, end_date)

        self.assertEqual(str(context.exception), "Start date must be before end date")

    def test_validate_time_range_start_equals_end(self):
        """Test validating time range where start equals end"""
        start_date = "2025-09-15T00:00:00Z"
        end_date = "2025-09-15T00:00:00Z"

        with self.assertRaises(ValueError) as context:
            validate_time_range(start_date, end_date)

        self.assertEqual(str(context.exception), "Start date must be before end date")

    def test_validate_time_range_too_long(self):
        """Test validating time range that exceeds 90 days"""
        start_date = "2025-01-01T00:00:00Z"
        end_date = "2025-06-01T23:59:59Z"  # More than 90 days

        with self.assertRaises(ValueError) as context:
            validate_time_range(start_date, end_date)

        self.assertEqual(str(context.exception), "Time range cannot exceed 90 days")

    def test_validate_time_range_exactly_90_days(self):
        """Test validating time range that is exactly 90 days"""
        start_date = "2025-01-01T00:00:00Z"
        end_date = "2025-03-31T23:59:59Z"  # Exactly 90 days (Jan+Feb+Mar)

        result = validate_time_range(start_date, end_date)
        self.assertTrue(result)


class TestGetTimeRange(unittest.TestCase):
    """Test get_time_range function"""

    def setUp(self):
        """Set up mock config loader"""
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get_week_definition.return_value = "sunday_to_saturday"
        self.mock_config.get_custom_start_day.return_value = 0

    @patch("builtins.print")
    @patch("tools.lib.time_handler.validate_time_range")
    @patch("tools.lib.time_handler.parse_date_string")
    def test_get_time_range_manual_mode(self, mock_parse, mock_validate, mock_print):
        """Test manual time range mode"""
        # Set up mocks
        mock_parse.side_effect = ["YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z"]
        mock_validate.return_value = True

        # Create mock args
        mock_args = MagicMock()
        mock_args.start = "YYYY-MM-DD"
        mock_args.end = "YYYY-MM-DD"

        start_date, end_date = get_time_range(mock_args, self.mock_config)

        # Verify calls
        mock_parse.assert_any_call("YYYY-MM-DD", end_of_day=False)
        mock_parse.assert_any_call("YYYY-MM-DD", end_of_day=True)
        mock_validate.assert_called_once_with(
            "YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z"
        )

        # Verify results
        self.assertEqual(start_date, "YYYY-MM-DDT00:00:00Z")
        self.assertEqual(end_date, "YYYY-MM-DDT23:59:59Z")

        # Verify print output
        mock_print.assert_called_with(
            "📅 使用手動指定時間範圍: YYYY-MM-DD 00:00 ~ YYYY-MM-DD 23:59 (UTC+0)"
        )

    @patch("builtins.print")
    @patch("tools.lib.time_handler.get_last_week_range_with_config")
    def test_get_time_range_automatic_mode_sunday_to_saturday(
        self, mock_get_range, mock_print
    ):
        """Test automatic time range mode with Sunday to Saturday"""
        # Set up mocks
        mock_get_range.return_value = ("YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z")
        self.mock_config.get_week_definition.return_value = "sunday_to_saturday"

        # Create mock args for automatic mode
        mock_args = MagicMock()
        mock_args.start = None
        mock_args.end = None

        start_date, end_date = get_time_range(mock_args, self.mock_config)

        # Verify calls
        mock_get_range.assert_called_once_with(self.mock_config)

        # Verify results
        self.assertEqual(start_date, "YYYY-MM-DDT00:00:00Z")
        self.assertEqual(end_date, "YYYY-MM-DDT23:59:59Z")

        # Verify print output includes week description
        expected_calls = [
            unittest.mock.call(
                "📅 自動計算上週時間範圍: YYYY-MM-DD 00:00 ~ YYYY-MM-DD 23:59 (UTC+0)"
            ),
            unittest.mock.call("   週期定義: 週日到週六"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch("builtins.print")
    @patch("tools.lib.time_handler.get_last_week_range_with_config")
    def test_get_time_range_automatic_mode_monday_to_friday(
        self, mock_get_range, mock_print
    ):
        """Test automatic time range mode with Monday to Friday"""
        # Set up mocks
        mock_get_range.return_value = ("2025-09-15T00:00:00Z", "2025-09-19T23:59:59Z")
        self.mock_config.get_week_definition.return_value = "monday_to_friday"

        # Create mock args for automatic mode
        mock_args = MagicMock()
        mock_args.start = None
        mock_args.end = None

        start_date, end_date = get_time_range(mock_args, self.mock_config)

        # Verify calls
        mock_get_range.assert_called_once_with(self.mock_config)

        # Verify results
        self.assertEqual(start_date, "2025-09-15T00:00:00Z")
        self.assertEqual(end_date, "2025-09-19T23:59:59Z")

        # Verify print output includes week description
        expected_calls = [
            unittest.mock.call(
                "📅 自動計算上週時間範圍: 2025-09-15 00:00 ~ 2025-09-19 23:59 (UTC+0)"
            ),
            unittest.mock.call("   週期定義: 週一到週五"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch("builtins.print")
    @patch("tools.lib.time_handler.get_last_week_range_with_config")
    def test_get_time_range_automatic_mode_custom(self, mock_get_range, mock_print):
        """Test automatic time range mode with custom definition"""
        # Set up mocks
        mock_get_range.return_value = ("2025-09-17T00:00:00Z", "2025-09-23T23:59:59Z")
        self.mock_config.get_week_definition.return_value = "custom"
        self.mock_config.get_custom_start_day.return_value = 3  # Wednesday

        # Create mock args for automatic mode
        mock_args = MagicMock()
        mock_args.start = None
        mock_args.end = None

        start_date, end_date = get_time_range(mock_args, self.mock_config)

        # Verify calls
        mock_get_range.assert_called_once_with(self.mock_config)

        # Verify results
        self.assertEqual(start_date, "2025-09-17T00:00:00Z")
        self.assertEqual(end_date, "2025-09-23T23:59:59Z")

        # Verify print output includes custom start day
        expected_calls = [
            unittest.mock.call(
                "📅 自動計算上週時間範圍: 2025-09-17 00:00 ~ 2025-09-23 23:59 (UTC+0)"
            ),
            unittest.mock.call("   週期定義: 自定義 (起始日: 3)"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch("builtins.print")
    @patch("tools.lib.time_handler.get_last_week_range_with_config")
    def test_get_time_range_automatic_mode_unknown_definition(
        self, mock_get_range, mock_print
    ):
        """Test automatic time range mode with unknown week definition"""
        # Set up mocks
        mock_get_range.return_value = ("YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z")
        self.mock_config.get_week_definition.return_value = "unknown_definition"

        # Create mock args for automatic mode
        mock_args = MagicMock()
        mock_args.start = None
        mock_args.end = None

        start_date, end_date = get_time_range(mock_args, self.mock_config)

        # Should still work but show the raw definition
        expected_calls = [
            unittest.mock.call(
                "📅 自動計算上週時間範圍: YYYY-MM-DD 00:00 ~ YYYY-MM-DD 23:59 (UTC+0)"
            ),
            unittest.mock.call("   週期定義: unknown_definition"),
        ]
        mock_print.assert_has_calls(expected_calls)


class TestTimezoneBehavior(unittest.TestCase):
    """Test timezone handling behavior"""

    @patch("tools.lib.time_handler.datetime")
    def test_utc_timezone_consistency(self, mock_datetime):
        """Test that all time calculations use UTC+0"""
        # Test with different times of day to ensure UTC+0 is used consistently
        test_times = [
            datetime(2025, 9, 24, 0, 0, 0),  # Midnight
            datetime(2025, 9, 24, 12, 0, 0),  # Noon
            datetime(2025, 9, 24, 23, 59, 59),  # End of day
        ]

        for test_time in test_times:
            mock_datetime.utcnow.return_value = test_time

            start_date, end_date = get_last_week_range()

            # All results should be in UTC (Z suffix)
            self.assertTrue(start_date.endswith("Z"))
            self.assertTrue(end_date.endswith("Z"))

            # Times should be consistently formatted
            self.assertRegex(start_date, r"\d{4}-\d{2}-\d{2}T00:00:00Z")
            self.assertRegex(end_date, r"\d{4}-\d{2}-\d{2}T23:59:59Z")


if __name__ == "__main__":
    unittest.main()
