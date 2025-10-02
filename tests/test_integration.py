#!/usr/bin/env python3
"""
Integration Tests for Akamai Traffic Report System

Comprehensive end-to-end testing with mocked external dependencies.
"""

import argparse
import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from tools.lib.config_loader import ConfigLoader, load_configuration

# Import main function and modules to test
from traffic import main


class TestMainFunctionIntegration(unittest.TestCase):
    """Integration tests for the main function"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "config.json")

        self.valid_config = {
            "api": {
                "endpoints": {
                    "traffic": "https://example.com/traffic",
                    "emissions": "https://example.com/emissions",
                },
                "timeout": 60,
                "max_retries": 3,
            },
            "business": {
                "cp_codes": ["123", "456"],
                "service_mappings": {
                    "123": {"name": "Test Service", "unit": "TB", "description": "Test"}
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "custom_start_day": 0,
                "region_mappings": {
                    "TW": "Region 2",
                    "SG": "Region 3",
                    "ID": "Region 1",
                },
            },
            "system": {"data_point_limit": 50000},
        }

        with open(self.test_config_file, "w") as f:
            json.dump(self.valid_config, f)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)

    @patch("traffic.argparse.ArgumentParser.parse_args")
    @patch("traffic.load_configuration")
    @patch("traffic.setup_authentication")
    @patch("traffic.get_time_range")
    @patch("traffic.get_total_edge_traffic")
    @patch("traffic.get_all_service_traffic")
    @patch("traffic.get_all_regional_traffic")
    @patch("traffic.generate_weekly_report")
    @patch("traffic.print_summary_stats")
    @patch("traffic.save_report_data")
    @patch("traffic.logger")
    def test_main_function_success_automatic_mode(
        self,
        mock_logger,
        mock_save_data,
        mock_print_stats,
        mock_gen_report,
        mock_regional,
        mock_services,
        mock_total,
        mock_time_range,
        mock_auth,
        mock_config,
        mock_args,
    ):
        """Test successful main function execution in automatic mode"""

        # Mock command line arguments (automatic mode)
        mock_args.return_value = MagicMock(start=None, end=None)

        # Mock configuration loading
        mock_config_loader = MagicMock(spec=ConfigLoader)
        mock_config_loader.print_config_summary = MagicMock()
        mock_config.return_value = mock_config_loader

        # Mock authentication
        mock_auth_obj = MagicMock()
        mock_auth.return_value = mock_auth_obj

        # Mock time range calculation
        mock_time_range.return_value = ("2025-09-14T00:00:00Z", "2025-09-20T23:59:59Z")

        # Mock successful total traffic
        mock_total.return_value = {
            "success": True,
            "total_tb": 100.5,
            "billing_estimate": 110.4,
        }

        # Mock successful service traffic
        mock_services.return_value = {"123": {"success": True, "name": "Test Service"}}

        # Mock successful regional traffic
        mock_regional.return_value = {
            "TW": {"success": True, "region_name": "Region 2"},
            "_summary": {"total_regional_traffic_tb": 50.0},
        }

        # Mock report generation
        mock_gen_report.return_value = "Generated Report Content"
        mock_save_data.return_value = "report_20250925_120000.json"

        # Execute main function
        result = main()

        # Verify successful execution
        self.assertEqual(result, 0)

        # Verify configuration was loaded
        mock_config.assert_called_once()
        mock_config_loader.print_config_summary.assert_called_once()

        # Verify authentication setup
        mock_auth.assert_called_once()

        # Verify time range calculation
        mock_time_range.assert_called_once()

        # Verify all data collection steps
        mock_total.assert_called_once_with(
            "2025-09-14T00:00:00Z",
            "2025-09-20T23:59:59Z",
            mock_auth_obj,
            mock_config_loader,
        )
        mock_services.assert_called_once()
        mock_regional.assert_called_once()

        # Verify report generation and output
        mock_gen_report.assert_called_once()
        mock_print_stats.assert_called_once()
        mock_save_data.assert_called_once()

        # Verify success messages
        success_messages = [str(call) for call in mock_logger.info.call_args_list]
        self.assertTrue(any("週報生成完成!" in msg for msg in success_messages))

    @patch("traffic.argparse.ArgumentParser.parse_args")
    @patch("traffic.load_configuration")
    @patch("traffic.setup_authentication")
    @patch("traffic.get_time_range")
    @patch("traffic.get_total_edge_traffic")
    @patch("traffic.logger")
    def test_main_function_total_traffic_failure(
        self,
        mock_logger,
        mock_total,
        mock_time_range,
        mock_auth,
        mock_config,
        mock_args,
    ):
        """Test main function with total traffic API failure"""

        # Mock command line arguments
        mock_args.return_value = MagicMock(start=None, end=None)

        # Mock configuration and auth
        mock_config_loader = MagicMock(spec=ConfigLoader)
        mock_config_loader.print_config_summary = MagicMock()
        mock_config.return_value = mock_config_loader
        mock_auth.return_value = MagicMock()

        # Mock time range
        mock_time_range.return_value = ("YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z")

        # Mock failed total traffic
        mock_total.return_value = {"success": False, "error": "API connection failed"}

        # Execute main function
        result = main()

        # Verify failure return code
        self.assertEqual(result, 1)

        # Verify error message was printed
        error_messages = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(any("無法取得總體流量數據" in msg for msg in error_messages))
        self.assertTrue(any("API connection failed" in msg for msg in error_messages))

    @patch("traffic.argparse.ArgumentParser.parse_args")
    @patch("traffic.load_configuration")
    @patch("traffic.logger")
    def test_main_function_configuration_error(
        self, mock_logger, mock_config, mock_args
    ):
        """Test main function with configuration loading error"""

        # Mock command line arguments
        mock_args.return_value = MagicMock(start=None, end=None)

        # Mock configuration loading failure
        from tools.lib.config_loader import ConfigurationError

        mock_config.side_effect = ConfigurationError("Configuration file not found")

        # Execute main function
        result = main()

        # Verify failure return code
        self.assertEqual(result, 1)

        # Verify error message was printed
        error_messages = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(any("執行失敗:" in msg for msg in error_messages))
        self.assertTrue(
            any("Configuration file not found" in msg for msg in error_messages)
        )

    @patch("traffic.argparse.ArgumentParser.parse_args")
    @patch("traffic.load_configuration")
    @patch("traffic.setup_authentication")
    @patch("traffic.logger")
    def test_main_function_authentication_error(
        self, mock_logger, mock_auth, mock_config, mock_args
    ):
        """Test main function with authentication error"""

        # Mock command line arguments
        mock_args.return_value = MagicMock(start=None, end=None)

        # Mock configuration
        mock_config_loader = MagicMock(spec=ConfigLoader)
        mock_config_loader.print_config_summary = MagicMock()
        mock_config.return_value = mock_config_loader

        # Mock authentication failure
        from tools.lib.exceptions import APIAuthenticationError

        mock_auth.side_effect = APIAuthenticationError("EdgeGrid authentication failed")

        # Execute main function
        result = main()

        # Verify failure return code
        self.assertEqual(result, 1)

        # Verify error message was printed
        error_messages = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(any("認證失敗:" in msg for msg in error_messages))
        self.assertTrue(
            any("EdgeGrid authentication failed" in msg for msg in error_messages)
        )

    @patch("traffic.argparse.ArgumentParser.parse_args")
    @patch("traffic.load_configuration")
    @patch("traffic.setup_authentication")
    @patch("traffic.get_time_range")
    @patch("traffic.get_total_edge_traffic")
    @patch("traffic.get_all_service_traffic")
    @patch("traffic.get_all_regional_traffic")
    @patch("traffic.generate_weekly_report")
    @patch("traffic.print_summary_stats")
    @patch("traffic.save_report_data")
    @patch("traffic.logger")
    def test_main_function_manual_mode(
        self,
        mock_logger,
        mock_save_data,
        mock_print_stats,
        mock_gen_report,
        mock_regional,
        mock_services,
        mock_total,
        mock_time_range,
        mock_auth,
        mock_config,
        mock_args,
    ):
        """Test main function in manual date range mode"""

        # Mock command line arguments (manual mode)
        mock_args.return_value = MagicMock(start="YYYY-MM-DD", end="YYYY-MM-DD")

        # Mock all dependencies as successful
        mock_config_loader = MagicMock(spec=ConfigLoader)
        mock_config_loader.print_config_summary = MagicMock()
        mock_config.return_value = mock_config_loader

        mock_auth.return_value = MagicMock()
        mock_time_range.return_value = ("YYYY-MM-DDT00:00:00Z", "YYYY-MM-DDT23:59:59Z")

        mock_total.return_value = {"success": True, "total_tb": 100.0}
        mock_services.return_value = {"123": {"success": True}}
        mock_regional.return_value = {"_summary": {}}

        mock_gen_report.return_value = "Report content"
        mock_save_data.return_value = "report.json"

        # Execute main function
        result = main()

        # Verify successful execution
        self.assertEqual(result, 0)

        # Verify time range was called with manual arguments
        mock_time_range.assert_called_once()
        args, kwargs = mock_time_range.call_args
        self.assertEqual(args[0].start, "YYYY-MM-DD")
        self.assertEqual(args[0].end, "YYYY-MM-DD")


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests with realistic data flow"""

    def setUp(self):
        """Set up realistic test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")

        # Create realistic configuration
        config_data = {
            "api": {
                "endpoints": {
                    "traffic": "https://akab-test.luna.akamaiapis.net/reporting-api/v2/reports/delivery/traffic/current/data",
                    "emissions": "https://akab-test.luna.akamaiapis.net/reporting-api/v2/reports/delivery/traffic/emissions/data",
                },
                "timeout": 60,
                "max_retries": 3,
            },
            "business": {
                "cp_codes": ["123456", "789012"],
                "service_mappings": {
                    "123456": {
                        "name": "Video Service",
                        "unit": "TB",
                        "description": "Video streaming",
                    },
                    "789012": {
                        "name": "Live Stream",
                        "unit": "GB",
                        "description": "Live streaming",
                    },
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "region_mappings": {
                    "ID": "Region 1",
                    "TW": "Region 2",
                    "SG": "Region 3",
                },
            },
            "system": {"data_point_limit": 50000},
        }

        with open(self.config_file, "w") as f:
            json.dump(config_data, f)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.setup_authentication")
    @patch("tools.lib.time_handler.datetime")
    @patch("traffic.logger")
    def test_realistic_api_flow(
        self, mock_logger, mock_datetime, mock_auth, mock_requests
    ):
        """Test realistic API call flow with actual response structures"""

        # Mock current time for consistent week calculation
        mock_datetime.utcnow.return_value = datetime(2025, 9, 24, 12, 0, 0)

        # Mock authentication
        mock_auth.return_value = MagicMock()

        # Mock API responses with realistic data structures
        traffic_response = MagicMock()
        traffic_response.status_code = 200
        traffic_response.json.return_value = {
            "data": [
                {
                    "time5minutes": "YYYY-MM-DDT00:00:00Z",
                    "edgeBytesSum": 5497558138880,
                },  # ~5TB
                {
                    "time5minutes": "YYYY-MM-DDT00:05:00Z",
                    "edgeBytesSum": 4398046511104,
                },  # ~4TB
                {
                    "time5minutes": "YYYY-MM-DDT00:10:00Z",
                    "edgeBytesSum": 3298534883328,
                },  # ~3TB
            ]
        }

        emissions_response = MagicMock()
        emissions_response.status_code = 200
        emissions_response.json.return_value = {
            "data": [
                {
                    "time1day": "YYYY-MM-DD",
                    "country": "TW",
                    "edgeBytesSum": 6597069766656,
                },  # ~6TB
                {
                    "time1day": "YYYY-MM-DD",
                    "country": "SG",
                    "edgeBytesSum": 4398046511104,
                },  # ~4TB
                {
                    "time1day": "YYYY-MM-DD",
                    "country": "ID",
                    "edgeBytesSum": 2199023255552,
                },  # ~2TB
            ]
        }

        # Configure mock to return different responses for different URLs
        def side_effect(*args, **kwargs):
            url = args[0]
            if "traffic" in url:
                return traffic_response
            elif "emissions" in url:
                return emissions_response
            return MagicMock(status_code=404)

        mock_requests.side_effect = side_effect

        # Load configuration and test integration
        config_loader = load_configuration(self.config_file)

        # Test individual components with realistic flow
        from tools.lib.api_client import (
            get_regional_traffic,
            get_service_traffic,
            get_total_edge_traffic,
        )

        auth = MagicMock()
        start_date = "YYYY-MM-DDT00:00:00Z"
        end_date = "YYYY-MM-DDT23:59:59Z"

        # Test total edge traffic
        total_result = get_total_edge_traffic(start_date, end_date, auth, config_loader)
        self.assertTrue(total_result["success"])
        self.assertGreater(total_result["total_tb"], 0)

        # Test service traffic
        service_result = get_service_traffic(
            "123456", start_date, end_date, auth, config_loader
        )
        self.assertTrue(service_result["success"])
        self.assertEqual(service_result["name"], "Video Service")
        self.assertEqual(service_result["unit"], "TB")

        # Test regional traffic
        regional_result = get_regional_traffic(
            "TW", start_date, end_date, auth, config_loader
        )
        self.assertTrue(regional_result["success"])
        self.assertEqual(regional_result["region_name"], "Region 2")
        self.assertGreater(regional_result["total_tb"], 0)

    @patch("traffic.load_configuration")
    def test_configuration_integration(self, mock_load_config):
        """Test configuration integration with all modules"""

        # Load real configuration
        real_config = load_configuration(self.config_file)
        mock_load_config.return_value = real_config

        # Test configuration accessor methods
        self.assertEqual(len(real_config.get_cp_codes()), 2)
        self.assertIn("123456", real_config.get_cp_codes())

        service_mappings = real_config.get_service_mappings()
        self.assertIn("123456", service_mappings)
        self.assertEqual(service_mappings["123456"]["name"], "Video Service")

        # Test week configuration
        self.assertEqual(real_config.get_week_definition(), "sunday_to_saturday")
        self.assertEqual(real_config.get_week_start_offset(), 0)
        self.assertEqual(real_config.get_week_duration_days(), 7)

        # Test API configuration
        endpoints = real_config.get_api_endpoints()
        self.assertIn("traffic", endpoints)
        self.assertIn("emissions", endpoints)

        # Test system configuration
        self.assertEqual(real_config.get_max_retries(), 3)
        self.assertEqual(real_config.get_request_timeout(), 60)
        self.assertEqual(real_config.get_data_point_limit(), 50000)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across module boundaries"""

    @patch("traffic.load_configuration")
    @patch("traffic.logger")
    def test_configuration_error_propagation(self, mock_logger, mock_load_config):
        """Test that configuration errors are properly handled"""

        from tools.lib.config_loader import ConfigurationError

        mock_load_config.side_effect = ConfigurationError("Invalid config format")

        # Mock sys.argv to avoid argparse issues
        with patch("sys.argv", ["traffic.py"]):
            result = main()

        self.assertEqual(result, 1)

        # Verify error was printed
        error_messages = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(any("執行失敗" in msg for msg in error_messages))

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.setup_authentication")
    @patch("traffic.load_configuration")
    @patch("traffic.logger")
    def test_api_timeout_handling(
        self, mock_logger, mock_load_config, mock_auth, mock_requests
    ):
        """Test API timeout error handling"""

        import requests

        # Mock configuration
        mock_config = MagicMock()
        mock_config.get_max_retries.return_value = 2
        mock_config.get_request_timeout.return_value = 1
        mock_config.get_api_endpoints.return_value = {"traffic": "https://example.com"}
        mock_load_config.return_value = mock_config

        # Mock authentication
        mock_auth.return_value = MagicMock()

        # Mock timeout on all requests
        mock_requests.side_effect = requests.exceptions.Timeout("Request timeout")

        from tools.lib.api_client import call_traffic_api

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "YYYY-MM-DDT00:00:00Z",
                "YYYY-MM-DDT23:59:59Z",
                {"test": "payload"},
                MagicMock(),
                mock_config,
            )

        self.assertIn("Request timeout", str(context.exception))

    def test_data_processing_error_handling(self):
        """Test error handling in data processing functions"""

        from tools.lib.utils import bytes_to_gb, bytes_to_tb, format_number

        # Test invalid input handling
        with self.assertRaises(ValueError):
            bytes_to_tb("invalid_number")

        with self.assertRaises(ValueError):
            bytes_to_gb("not_a_number")

        with self.assertRaises(ValueError):
            format_number("invalid_input")


if __name__ == "__main__":
    # Set up test suite
    unittest.main(verbosity=2)
