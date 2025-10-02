#!/usr/bin/env python3
"""
Unit Tests for report generation functions in traffic.py

Comprehensive test coverage for report and data processing functionality.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

# Import functions to test
from tools.lib.reporters import (
    generate_weekly_report,
    print_summary_stats,
    save_report_data,
)


class TestGenerateWeeklyReport(unittest.TestCase):
    """Test generate_weekly_report function"""

    def setUp(self):
        """Set up test data"""
        self.start_date = "2025-09-14T00:00:00Z"
        self.end_date = "2025-09-20T23:59:59Z"

        self.total_traffic = {
            "total_tb": 100.5,
            "billing_estimate": 110.4,
            "data_points": 2016,  # 7 days * 24 hours * 12 (5-min intervals)
        }

        self.service_traffic = {
            "123": {
                "success": True,
                "name": "Service A",
                "traffic_value": 50.25,
                "unit": "TB",
                "cp_code": "123",
            },
            "456": {
                "success": True,
                "name": "Service B",
                "traffic_value": 25000.5,
                "unit": "GB",
                "cp_code": "456",
            },
            "789": {"success": False, "error": "API timeout", "cp_code": "789"},
        }

        self.regional_traffic = {
            "TW": {
                "success": True,
                "region_name": "Region 2",
                "country_code": "TW",
                "total_tb": 45.5,
            },
            "SG": {
                "success": True,
                "region_name": "Region 3",
                "country_code": "SG",
                "total_tb": 30.2,
            },
            "ID": {
                "success": True,
                "region_name": "Region 1",
                "country_code": "ID",
                "total_tb": 20.1,
            },
            "_summary": {
                "total_regions": 3,
                "successful_queries": 3,
                "total_regional_traffic_tb": 95.8,
                "success_rate": 100.0,
            },
        }

    @patch("tools.lib.reporters.console_reporter.datetime")
    def test_generate_weekly_report_complete(self, mock_datetime):
        """Test complete report generation with all data"""
        # Mock current time for report generation
        mock_datetime.utcnow.return_value = datetime(2025, 9, 25, 10, 30, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.0

        report = generate_weekly_report(
            self.start_date,
            self.end_date,
            self.total_traffic,
            self.service_traffic,
            self.regional_traffic,
            mock_config,
        )

        # Verify report contains key sections
        self.assertIn("📊 週報流量數據報告", report)
        self.assertIn("2025-09-14 ~ 2025-09-20", report)
        self.assertIn("報告期間: 7 天", report)
        self.assertIn("UTC+0", report)

        # Verify traffic data
        self.assertIn("總 Edge 流量:", report)
        self.assertIn("100.50 TB", report)
        self.assertIn("預估計費用量:", report)
        self.assertIn("110.40 TB", report)

        # Verify service data
        self.assertIn("Service A (123)", report)
        self.assertIn("50.25 TB", report)
        self.assertIn("Service B (456)", report)
        self.assertIn("25,000.50 GB", report)
        self.assertIn("查詢失敗服務: 1 個", report)

        # Verify regional data
        self.assertIn("Region 2 (TW)", report)
        self.assertIn("45.50 TB", report)
        self.assertIn("Region 3 (SG)", report)
        self.assertIn("30.20 TB", report)
        self.assertIn("Region 1 (ID)", report)
        self.assertIn("20.10 TB", report)
        self.assertIn("地區小計:", report)
        self.assertIn("95.80 TB", report)

        # Verify statistics
        self.assertIn("Traffic API 數據點:", report)
        self.assertIn("2,016", report)
        self.assertIn("成功查詢服務:                   2/3", report)
        self.assertIn("成功查詢地區:                   3/3", report)

        # Verify coverage calculation
        coverage = (95.8 / 100.5) * 100
        self.assertIn(f"地區流量覆蓋率:              {coverage:.1f}%", report)

        # Verify billing analysis
        self.assertIn("計費分析:", report)
        self.assertIn("API 總流量:                  100.50 TB", report)
        self.assertIn("預估實際計費:                110.40 TB", report)
        self.assertIn("計費修正係數:               1.0", report)

        # Verify system performance
        self.assertIn("系統效能指標:", report)
        api_calls = 1 + 2 + 3  # 1 total + 2 successful services + 3 regions
        self.assertIn(f"總 API 呼叫次數:               {api_calls}", report)

        # Verify footer
        self.assertIn("報告完成", report)
        self.assertIn("Akamai V2 APIs", report)

    @patch("tools.lib.reporters.console_reporter.datetime")
    def test_generate_weekly_report_no_services(self, mock_datetime):
        """Test report generation with no successful services"""
        mock_datetime.utcnow.return_value = datetime(2025, 9, 25, 10, 30, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.2

        # All services failed
        failed_services = {
            "123": {"success": False, "error": "Timeout"},
            "456": {"success": False, "error": "Auth failed"},
        }

        report = generate_weekly_report(
            self.start_date,
            self.end_date,
            self.total_traffic,
            failed_services,
            self.regional_traffic,
            mock_config,
        )

        # Should still generate report but show no successful services
        self.assertIn("成功查詢服務:                   0/2", report)
        self.assertIn("⚠️  查詢失敗服務: 2 個", report)
        self.assertNotIn("Service A", report)

    @patch("tools.lib.reporters.console_reporter.datetime")
    def test_generate_weekly_report_no_regions(self, mock_datetime):
        """Test report generation with no regional data"""
        mock_datetime.utcnow.return_value = datetime(2025, 9, 25, 10, 30, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.0

        # No regional data
        empty_regional = {
            "_summary": {
                "total_regions": 3,
                "successful_queries": 0,
                "total_regional_traffic_tb": 0,
                "success_rate": 0.0,
            }
        }

        report = generate_weekly_report(
            self.start_date,
            self.end_date,
            self.total_traffic,
            self.service_traffic,
            empty_regional,
            mock_config,
        )

        # Should show zero coverage
        self.assertIn("地區流量覆蓋率:              0.0%", report)
        self.assertIn("成功查詢地區:                   0/3", report)
        self.assertIn("地區小計:                      0.00 TB", report)

    def test_generate_weekly_report_service_sorting(self):
        """Test that services are sorted by traffic value"""
        # Create services with different traffic values
        services_unsorted = {
            "123": {
                "success": True,
                "name": "Small",
                "traffic_value": 10.0,
                "unit": "TB",
                "cp_code": "123",
            },
            "456": {
                "success": True,
                "name": "Large",
                "traffic_value": 100.0,
                "unit": "TB",
                "cp_code": "456",
            },
            "789": {
                "success": True,
                "name": "Medium",
                "traffic_value": 50.0,
                "unit": "TB",
                "cp_code": "789",
            },
        }

        with patch("tools.lib.reporters.console_reporter.datetime") as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 9, 25, 10, 30, 0)
            mock_dt.fromisoformat.side_effect = lambda x: datetime.fromisoformat(
                x.replace("Z", "+00:00")
            )

            mock_config = MagicMock()
            mock_config.get_billing_coefficient.return_value = 1.0

            report = generate_weekly_report(
                self.start_date,
                self.end_date,
                self.total_traffic,
                services_unsorted,
                self.regional_traffic,
                mock_config,
            )

        # Find the positions of service names in the report
        large_pos = report.find("Large (456)")
        medium_pos = report.find("Medium (789)")
        small_pos = report.find("Small (123)")

        # Large should appear before Medium, Medium before Small (descending order)
        self.assertLess(large_pos, medium_pos)
        self.assertLess(medium_pos, small_pos)

    def test_generate_weekly_report_region_sorting(self):
        """Test that regions are sorted by traffic value"""
        # Modify regional data to test sorting
        regional_mixed = {
            "TW": {
                "success": True,
                "region_name": "Region 2",
                "country_code": "TW",
                "total_tb": 20.0,
            },
            "SG": {
                "success": True,
                "region_name": "Region 3",
                "country_code": "SG",
                "total_tb": 50.0,
            },
            "ID": {
                "success": True,
                "region_name": "Region 1",
                "country_code": "ID",
                "total_tb": 35.0,
            },
            "_summary": {"total_regional_traffic_tb": 105.0, "successful_queries": 3},
        }

        with patch("tools.lib.reporters.console_reporter.datetime") as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 9, 25, 10, 30, 0)
            mock_dt.fromisoformat.side_effect = lambda x: datetime.fromisoformat(
                x.replace("Z", "+00:00")
            )

            mock_config = MagicMock()
            mock_config.get_billing_coefficient.return_value = 1.0

            report = generate_weekly_report(
                self.start_date,
                self.end_date,
                self.total_traffic,
                self.service_traffic,
                regional_mixed,
                mock_config,
            )

        # Find positions - Region 3 (50.0) should come first, then Region 1 (35.0), then Region 2 (20.0)
        sg_pos = report.find("Region 3")
        id_pos = report.find("Region 1")
        tw_pos = report.find("Region 2")

        self.assertLess(sg_pos, id_pos)
        self.assertLess(id_pos, tw_pos)


class TestPrintSummaryStats(unittest.TestCase):
    """Test print_summary_stats function"""

    def setUp(self):
        """Set up test data"""
        self.total_traffic = {"total_tb": 100.5, "billing_estimate": 110.4}

        self.service_traffic = {
            "123": {
                "success": True,
                "name": "Top Service",
                "traffic_value": 75.0,
                "unit": "TB",
            },
            "456": {
                "success": True,
                "name": "Small Service",
                "traffic_value": 10.0,
                "unit": "GB",
            },
            "789": {"success": False, "error": "Failed"},
        }

        self.regional_traffic = {
            "TW": {"success": True, "region_name": "Region 2", "total_tb": 60.0},
            "SG": {"success": True, "region_name": "Region 3", "total_tb": 30.0},
            "ID": {"success": False, "error": "Failed"},
            "_summary": {"total_regional_traffic_tb": 90.0},
        }

    @patch("tools.lib.reporters.console_reporter.logger")
    def test_print_summary_stats_complete(self, mock_logger):
        """Test printing complete summary stats"""
        print_summary_stats(
            self.total_traffic, self.service_traffic, self.regional_traffic
        )

        # Verify key summary information is printed
        call_args = [str(call) for call in mock_logger.info.call_args_list]

        # Check for total traffic
        self.assertTrue(any("總 Edge 流量: 100.50 TB" in arg for arg in call_args))

        # Check for billing estimate
        self.assertTrue(any("預估計費: 110.40 TB" in arg for arg in call_args))

        # Check for top service (highest traffic)
        self.assertTrue(
            any("最大服務: Top Service (75.00 TB)" in arg for arg in call_args)
        )

        # Check for top region (highest traffic)
        self.assertTrue(
            any("最大地區: Region 2 (60.00 TB)" in arg for arg in call_args)
        )

        # Check for coverage calculation
        coverage = (90.0 / 100.5) * 100
        self.assertTrue(any(f"地區覆蓋率: {coverage:.1f}%" in arg for arg in call_args))

    @patch("tools.lib.logger.logger")
    def test_print_summary_stats_no_services(self, mock_logger):
        """Test printing summary with no successful services"""
        no_services = {"123": {"success": False, "error": "Failed"}}

        print_summary_stats(self.total_traffic, no_services, self.regional_traffic)

        call_args = [str(call) for call in mock_logger.info.call_args_list]

        # Should not print top service line
        self.assertFalse(any("最大服務:" in arg for arg in call_args))

    @patch("tools.lib.reporters.console_reporter.logger")
    def test_print_summary_stats_no_regions(self, mock_logger):
        """Test printing summary with no successful regions"""
        no_regions = {
            "TW": {"success": False, "error": "Failed"},
            "_summary": {"total_regional_traffic_tb": 0},
        }

        print_summary_stats(self.total_traffic, self.service_traffic, no_regions)

        call_args = [str(call) for call in mock_logger.info.call_args_list]

        # Should not print top region line
        self.assertFalse(any("最大地區:" in arg for arg in call_args))

        # Should show 0% coverage
        self.assertTrue(any("地區覆蓋率: 0.0%" in arg for arg in call_args))

    @patch("tools.lib.logger.logger")
    def test_print_summary_stats_zero_total_traffic(self, mock_logger):
        """Test printing summary with zero total traffic"""
        zero_traffic = {"total_tb": 0, "billing_estimate": 0}

        print_summary_stats(zero_traffic, self.service_traffic, self.regional_traffic)

        call_args = [str(call) for call in mock_logger.info.call_args_list]

        # Should not print coverage (division by zero avoided)
        self.assertFalse(any("地區覆蓋率:" in arg for arg in call_args))


class TestSaveReportData(unittest.TestCase):
    """Test save_report_data function"""

    def setUp(self):
        """Set up test data and temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.start_date = "YYYY-MM-DDT00:00:00Z"
        self.end_date = "YYYY-MM-DDT23:59:59Z"

        self.total_traffic = {
            "total_tb": 100.5,
            "billing_estimate": 110.4,
            "data_points": 2016,
        }

        self.service_traffic = {
            "123": {
                "success": True,
                "name": "Service A",
                "traffic_value": 50.25,
                "unit": "TB",
            },
            "456": {"success": False, "error": "API timeout"},
        }

        self.regional_traffic = {
            "TW": {"success": True, "region_name": "Region 2", "total_tb": 45.5},
            "SG": {"success": False, "error": "Network error"},
            "_summary": {"total_regional_traffic_tb": 45.5, "successful_queries": 1},
        }

    def tearDown(self):
        """Clean up temporary directory"""
        os.chdir(self.original_cwd)
        # Clean up any files created in temp directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    @patch("tools.lib.reporters.json_reporter.datetime")
    @patch("tools.lib.reporters.json_reporter.logger")
    def test_save_report_data_success(self, mock_logger, mock_datetime):
        """Test successful report data saving"""
        # Mock datetime for consistent filename
        mock_now = datetime(2025, 9, 25, 14, 30, 45)
        mock_datetime.utcnow.return_value = mock_now

        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.0

        filename = save_report_data(
            self.start_date,
            self.end_date,
            self.total_traffic,
            self.service_traffic,
            self.regional_traffic,
            mock_config,
        )

        # Verify filename format
        expected_filename = "traffic_report_20250925_143045.json"
        self.assertEqual(filename, expected_filename)

        # Verify file was created
        self.assertTrue(os.path.exists(filename))

        # Verify file contents
        with open(filename, encoding="utf-8") as f:
            saved_data = json.load(f)

        # Check metadata
        self.assertEqual(saved_data["report_metadata"]["period_start"], self.start_date)
        self.assertEqual(saved_data["report_metadata"]["period_end"], self.end_date)
        self.assertEqual(saved_data["report_metadata"]["billing_coefficient"], 1.0)
        self.assertIn("generated_at", saved_data["report_metadata"])

        # Check traffic summary
        self.assertEqual(saved_data["traffic_summary"]["total_edge_tb"], 100.5)
        self.assertEqual(saved_data["traffic_summary"]["billing_estimate_tb"], 110.4)
        self.assertEqual(saved_data["traffic_summary"]["data_points"], 2016)

        # Check service traffic
        self.assertIn("123", saved_data["service_traffic"])
        self.assertEqual(saved_data["service_traffic"]["123"]["name"], "Service A")
        self.assertEqual(saved_data["service_traffic"]["123"]["traffic_value"], 50.25)
        self.assertEqual(saved_data["service_traffic"]["123"]["unit"], "TB")
        self.assertTrue(saved_data["service_traffic"]["123"]["success"])

        self.assertIn("456", saved_data["service_traffic"])
        self.assertFalse(saved_data["service_traffic"]["456"]["success"])

        # Check regional traffic
        self.assertIn("TW", saved_data["regional_traffic"])
        self.assertEqual(
            saved_data["regional_traffic"]["TW"]["region_name"], "Region 2"
        )
        self.assertEqual(saved_data["regional_traffic"]["TW"]["total_tb"], 45.5)
        self.assertTrue(saved_data["regional_traffic"]["TW"]["success"])

        self.assertIn("SG", saved_data["regional_traffic"])
        self.assertFalse(saved_data["regional_traffic"]["SG"]["success"])

        # Check regional summary
        self.assertEqual(
            saved_data["regional_summary"]["total_regional_traffic_tb"], 45.5
        )
        self.assertEqual(saved_data["regional_summary"]["successful_queries"], 1)

        # Verify print message
        mock_logger.info.assert_called_with(f"📄 報告數據已保存至: {expected_filename}")

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    @patch("tools.lib.reporters.json_reporter.logger")
    def test_save_report_data_file_error(self, mock_logger, mock_open_error):
        """Test report data saving with file error"""
        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.0

        filename = save_report_data(
            self.start_date,
            self.end_date,
            self.total_traffic,
            self.service_traffic,
            self.regional_traffic,
            mock_config,
        )

        # Should return None on error
        self.assertIsNone(filename)

        # Should print error message
        mock_logger.warning.assert_called_with("⚠️  保存報告數據失敗: Permission denied")

    @patch(
        "tools.lib.reporters.json_reporter.json.dump",
        side_effect=ValueError("JSON encoding error"),
    )
    @patch("tools.lib.reporters.json_reporter.logger")
    def test_save_report_data_json_error(self, mock_logger, mock_json_dump):
        """Test report data saving with JSON encoding error"""
        # Mock config loader
        mock_config = MagicMock()
        mock_config.get_billing_coefficient.return_value = 1.0

        filename = save_report_data(
            self.start_date,
            self.end_date,
            self.total_traffic,
            self.service_traffic,
            self.regional_traffic,
            mock_config,
        )

        # Should return None on error
        self.assertIsNone(filename)

        # Should print error message
        call_args = [str(call) for call in mock_logger.warning.call_args_list]
        self.assertTrue(any("保存報告數據失敗:" in arg for arg in call_args))

    def test_save_report_data_excludes_raw_data(self):
        """Test that raw API data is excluded from saved report"""
        # Add raw_data to test data (should be excluded)
        service_with_raw = self.service_traffic.copy()
        service_with_raw["123"]["raw_data"] = {"large": "api_response"}

        regional_with_raw = self.regional_traffic.copy()
        regional_with_raw["TW"]["raw_data"] = {"large": "emissions_data"}

        with patch("tools.lib.reporters.json_reporter.datetime") as mock_dt:
            mock_dt.utcnow.return_value = datetime(2025, 9, 25, 12, 0, 0)

            # Mock config loader
            mock_config = MagicMock()
            mock_config.get_billing_coefficient.return_value = 1.0

            filename = save_report_data(
                self.start_date,
                self.end_date,
                self.total_traffic,
                service_with_raw,
                regional_with_raw,
                mock_config,
            )

        # Verify raw_data is not in saved file
        with open(filename, encoding="utf-8") as f:
            saved_data = json.load(f)

        # Should not contain raw_data fields
        saved_json_str = json.dumps(saved_data)
        self.assertNotIn("raw_data", saved_json_str)
        self.assertNotIn("large", saved_json_str)  # Content of raw_data


if __name__ == "__main__":
    unittest.main()
