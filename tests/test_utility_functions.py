#!/usr/bin/env python3
"""
Unit Tests for utility functions in traffic.py

Comprehensive test coverage for utility and helper functionality.
"""

import argparse
import unittest
from unittest.mock import MagicMock, patch

# Import functions to test
from tools.lib.api_client import setup_authentication
from tools.lib.utils import bytes_to_gb, bytes_to_tb, format_number


class TestSetupAuthentication(unittest.TestCase):
    """Test setup_authentication function"""

    @patch("tools.lib.api_client.EdgeRc")
    @patch("tools.lib.api_client.EdgeGridAuth")
    @patch("tools.lib.api_client.logger")
    def test_setup_authentication_success(
        self, mock_logger, mock_edge_auth, mock_edge_rc
    ):
        """Test successful authentication setup"""
        # Mock EdgeRc
        mock_edgerc_instance = MagicMock()
        mock_edge_rc.return_value = mock_edgerc_instance

        # Mock EdgeGridAuth
        mock_auth_instance = MagicMock()
        mock_edge_auth.from_edgerc.return_value = mock_auth_instance

        result = setup_authentication()

        # Verify EdgeRc was called with correct path
        mock_edge_rc.assert_called_once_with("~/.edgerc")

        # Verify EdgeGridAuth was called with edgerc and default section
        mock_edge_auth.from_edgerc.assert_called_once_with(
            mock_edgerc_instance, "default"
        )

        # Verify success message was printed
        mock_logger.info.assert_called_with("✅ 認證設定成功")

        # Verify return value
        self.assertEqual(result, mock_auth_instance)

    @patch("tools.lib.api_client.EdgeRc")
    @patch("tools.lib.api_client.logger")
    def test_setup_authentication_edgerc_file_not_found(
        self, mock_logger, mock_edge_rc
    ):
        """Test authentication setup with missing .edgerc file"""
        mock_edge_rc.side_effect = FileNotFoundError("File not found: ~/.edgerc")

        with self.assertRaises(FileNotFoundError):
            setup_authentication()

        # Verify error message was printed
        mock_logger.error.assert_called_with(
            "❌ 認證設定失敗: File not found: ~/.edgerc"
        )

    @patch("tools.lib.api_client.EdgeRc")
    @patch("tools.lib.api_client.EdgeGridAuth")
    @patch("tools.lib.api_client.logger")
    def test_setup_authentication_invalid_credentials(
        self, mock_logger, mock_edge_auth, mock_edge_rc
    ):
        """Test authentication setup with invalid credentials format"""
        mock_edge_rc.return_value = MagicMock()
        mock_edge_auth.from_edgerc.side_effect = ValueError("Invalid credential format")

        with self.assertRaises(ValueError):
            setup_authentication()

        # Verify error message was printed
        mock_logger.error.assert_called_with(
            "❌ 認證設定失敗: Invalid credential format"
        )

    @patch("tools.lib.api_client.EdgeRc")
    @patch("tools.lib.api_client.EdgeGridAuth")
    @patch("tools.lib.api_client.logger")
    def test_setup_authentication_permission_error(
        self, mock_logger, mock_edge_auth, mock_edge_rc
    ):
        """Test authentication setup with permission error"""
        mock_edge_rc.side_effect = PermissionError("Permission denied: ~/.edgerc")

        with self.assertRaises(PermissionError):
            setup_authentication()

        # Verify error message was printed
        mock_logger.error.assert_called_with(
            "❌ 認證設定失敗: Permission denied: ~/.edgerc"
        )


class TestBytesToTB(unittest.TestCase):
    """Test bytes_to_tb function"""

    def test_bytes_to_tb_integer(self):
        """Test bytes to TB conversion with integer input"""
        # 1 TB = 1,099,511,627,776 bytes (1024^4)
        result = bytes_to_tb(1099511627776)
        self.assertEqual(result, 1.0)

    def test_bytes_to_tb_float(self):
        """Test bytes to TB conversion with float input"""
        # 2.5 TB
        bytes_value = int(2.5 * (1024**4))
        result = bytes_to_tb(bytes_value)
        self.assertEqual(result, 2.5)

    def test_bytes_to_tb_string(self):
        """Test bytes to TB conversion with string input"""
        result = bytes_to_tb("1099511627776")
        self.assertEqual(result, 1.0)

    def test_bytes_to_tb_zero(self):
        """Test bytes to TB conversion with zero bytes"""
        result = bytes_to_tb(0)
        self.assertEqual(result, 0.0)

    def test_bytes_to_tb_precision(self):
        """Test bytes to TB conversion precision (2 decimal places)"""
        # Test value that would have more than 2 decimal places
        bytes_value = 1234567890123  # Should give 1.12 TB (rounded)
        result = bytes_to_tb(bytes_value)

        # Verify result is rounded to 2 decimal places
        self.assertEqual(len(str(result).split(".")[-1]), 2)
        self.assertAlmostEqual(result, 1.12, places=2)

    def test_bytes_to_tb_large_value(self):
        """Test bytes to TB conversion with very large value"""
        # 1000 TB
        bytes_value = 1000 * (1024**4)
        result = bytes_to_tb(bytes_value)
        self.assertEqual(result, 1000.0)

    def test_bytes_to_tb_small_value(self):
        """Test bytes to TB conversion with very small value"""
        # 1 byte should be very close to 0 TB
        result = bytes_to_tb(1)
        self.assertAlmostEqual(result, 0.0, places=2)


class TestBytesToGB(unittest.TestCase):
    """Test bytes_to_gb function"""

    def test_bytes_to_gb_integer(self):
        """Test bytes to GB conversion with integer input"""
        # 1 GB = 1,073,741,824 bytes (1024^3)
        result = bytes_to_gb(1073741824)
        self.assertEqual(result, 1.0)

    def test_bytes_to_gb_float(self):
        """Test bytes to GB conversion with float input"""
        # 2.5 GB
        bytes_value = int(2.5 * (1024**3))
        result = bytes_to_gb(bytes_value)
        self.assertEqual(result, 2.5)

    def test_bytes_to_gb_string(self):
        """Test bytes to GB conversion with string input"""
        result = bytes_to_gb("1073741824")
        self.assertEqual(result, 1.0)

    def test_bytes_to_gb_zero(self):
        """Test bytes to GB conversion with zero bytes"""
        result = bytes_to_gb(0)
        self.assertEqual(result, 0.0)

    def test_bytes_to_gb_precision(self):
        """Test bytes to GB conversion precision (2 decimal places)"""
        # Test value that would have more than 2 decimal places
        bytes_value = 1234567890  # Should give 1.15 GB (rounded)
        result = bytes_to_gb(bytes_value)

        # Verify result is rounded to 2 decimal places
        self.assertEqual(len(str(result).split(".")[-1]), 2)
        self.assertAlmostEqual(result, 1.15, places=2)

    def test_bytes_to_gb_large_value(self):
        """Test bytes to GB conversion with very large value"""
        # 1000 GB
        bytes_value = 1000 * (1024**3)
        result = bytes_to_gb(bytes_value)
        self.assertEqual(result, 1000.0)

    def test_bytes_to_gb_small_value(self):
        """Test bytes to GB conversion with very small value"""
        # 1 byte should be very close to 0 GB
        result = bytes_to_gb(1)
        self.assertAlmostEqual(result, 0.0, places=2)


class TestFormatNumber(unittest.TestCase):
    """Test format_number function"""

    def test_format_number_default_precision(self):
        """Test number formatting with default 2 decimal places"""
        result = format_number(1234.5678)
        self.assertEqual(result, "1,234.57")

    def test_format_number_custom_precision(self):
        """Test number formatting with custom decimal places"""
        result = format_number(1234.5678, decimal_places=3)
        self.assertEqual(result, "1,234.568")

    def test_format_number_integer(self):
        """Test number formatting with integer input"""
        result = format_number(1234)
        self.assertEqual(result, "1,234.00")

    def test_format_number_zero_precision(self):
        """Test number formatting with zero decimal places"""
        result = format_number(1234.5678, decimal_places=0)
        self.assertEqual(result, "1,235")  # Rounded up

    def test_format_number_string_input(self):
        """Test number formatting with string input"""
        result = format_number("1234.5678")
        self.assertEqual(result, "1,234.57")

    def test_format_number_zero(self):
        """Test number formatting with zero"""
        result = format_number(0)
        self.assertEqual(result, "0.00")

    def test_format_number_negative(self):
        """Test number formatting with negative number"""
        result = format_number(-1234.56)
        self.assertEqual(result, "-1,234.56")

    def test_format_number_large_number(self):
        """Test number formatting with very large number"""
        result = format_number(1234567890.12)
        self.assertEqual(result, "1,234,567,890.12")

    def test_format_number_small_decimal(self):
        """Test number formatting with small decimal"""
        result = format_number(0.001)
        self.assertEqual(result, "0.00")

    def test_format_number_exact_decimal(self):
        """Test number formatting with exact decimal places"""
        result = format_number(123.45)
        self.assertEqual(result, "123.45")

    def test_format_number_single_decimal(self):
        """Test number formatting with single decimal precision"""
        result = format_number(1234.5678, decimal_places=1)
        self.assertEqual(result, "1,234.6")

    def test_format_number_four_decimal(self):
        """Test number formatting with four decimal precision"""
        result = format_number(1234.5678, decimal_places=4)
        self.assertEqual(result, "1,234.5678")

    def test_format_number_rounding_up(self):
        """Test number formatting with rounding up"""
        result = format_number(1234.996, decimal_places=2)
        self.assertEqual(result, "1,235.00")  # Rounded up

    def test_format_number_rounding_down(self):
        """Test number formatting with rounding down"""
        result = format_number(1234.994, decimal_places=2)
        self.assertEqual(result, "1,234.99")  # Rounded down

    def test_format_number_no_thousands_separator_small(self):
        """Test number formatting with number less than 1000"""
        result = format_number(123.45)
        self.assertEqual(result, "123.45")  # No comma needed

    def test_format_number_exactly_thousand(self):
        """Test number formatting with exactly 1000"""
        result = format_number(1000)
        self.assertEqual(result, "1,000.00")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_bytes_to_tb_invalid_string(self):
        """Test bytes_to_tb with invalid string input"""
        with self.assertRaises(ValueError):
            bytes_to_tb("not_a_number")

    def test_bytes_to_gb_invalid_string(self):
        """Test bytes_to_gb with invalid string input"""
        with self.assertRaises(ValueError):
            bytes_to_gb("invalid")

    def test_format_number_invalid_string(self):
        """Test format_number with invalid string input"""
        with self.assertRaises(ValueError):
            format_number("not_a_number")

    def test_format_number_negative_precision(self):
        """Test format_number with negative decimal places"""
        # Should raise ValueError for negative precision
        with self.assertRaises(ValueError):
            format_number(1234.5678, decimal_places=-1)

    def test_bytes_conversion_consistency(self):
        """Test consistency between byte conversion functions"""
        bytes_value = 1099511627776  # 1 TB

        tb_result = bytes_to_tb(bytes_value)
        gb_result = bytes_to_gb(bytes_value)

        # 1 TB should equal 1024 GB
        self.assertEqual(tb_result, 1.0)
        self.assertEqual(gb_result, 1024.0)

        # Verify relationship: TB * 1024 = GB
        self.assertAlmostEqual(tb_result * 1024, gb_result, places=2)

    def test_format_number_extreme_precision(self):
        """Test format_number with extreme precision values"""
        # Very high precision
        result = format_number(1234.123456789, decimal_places=10)
        self.assertIn("1,234.1234567890", result)

        # Zero precision should work
        result = format_number(1234.56, decimal_places=0)
        self.assertEqual(result, "1,235")


class TestFunctionTypes(unittest.TestCase):
    """Test function type handling and parameter validation"""

    def test_bytes_to_tb_type_handling(self):
        """Test bytes_to_tb handles different numeric types correctly"""
        test_values = [
            (1099511627776, 1.0),  # int
            (1099511627776.0, 1.0),  # float
            ("1099511627776", 1.0),  # string
        ]

        for input_val, expected in test_values:
            with self.subTest(input_val=input_val):
                result = bytes_to_tb(input_val)
                self.assertEqual(result, expected)

    def test_bytes_to_gb_type_handling(self):
        """Test bytes_to_gb handles different numeric types correctly"""
        test_values = [
            (1073741824, 1.0),  # int
            (1073741824.0, 1.0),  # float
            ("1073741824", 1.0),  # string
        ]

        for input_val, expected in test_values:
            with self.subTest(input_val=input_val):
                result = bytes_to_gb(input_val)
                self.assertEqual(result, expected)

    def test_format_number_type_handling(self):
        """Test format_number handles different numeric types correctly"""
        test_values = [
            (1234, "1,234.00"),  # int
            (1234.0, "1,234.00"),  # float
            ("1234", "1,234.00"),  # string
            (1234.56, "1,234.56"),  # float with decimals
        ]

        for input_val, expected in test_values:
            with self.subTest(input_val=input_val):
                result = format_number(input_val)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
