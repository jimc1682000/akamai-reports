#!/usr/bin/env python3
"""
Unit Tests for API calling functions in traffic.py

Comprehensive test coverage for API interaction functionality with mocking.
"""

import json
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

import requests

# Import functions to test
from tools.lib.api_client import (
    call_emissions_api,
    call_traffic_api,
    get_all_regional_traffic,
    get_all_service_traffic,
    get_regional_traffic,
    get_service_traffic,
    get_total_edge_traffic,
    reset_circuit_breakers,
)
from tools.lib.config_loader import ConfigLoader


class TestCallTrafficAPI(unittest.TestCase):
    """Test call_traffic_api function"""

    def setUp(self):
        """Set up mock config and auth"""
        # Reset circuit breakers before each test to ensure clean state
        reset_circuit_breakers()
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get_api_endpoints.return_value = {
            "traffic": "https://example.com/traffic"
        }
        self.mock_config.get_max_retries.return_value = 3
        self.mock_config.get_request_timeout.return_value = 60
        self.mock_config.get_data_point_limit.return_value = 50000
        self.mock_config.get_data_point_warning_threshold.return_value = 0.9
        self.mock_config.get_exponential_backoff_base.return_value = 2
        self.mock_config.get_network_error_delay.return_value = 1.0
        self.mock_config.get_rate_limit_delay.return_value = 0.5

        self.mock_auth = MagicMock()

        self.test_payload = {
            "dimensions": ["time5minutes"],
            "metrics": ["edgeBytesSum"],
            "filters": [
                {
                    "dimensionName": "cpcode",
                    "operator": "IN_LIST",
                    "expressions": ["123"],
                }
            ],
        }

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_success(self, mock_logger, mock_post):
        """Test successful API call"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"time5minutes": "2025-09-24T00:00:00Z", "edgeBytesSum": 1000000}]
        }
        mock_post.return_value = mock_response

        result = call_traffic_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify API call
        mock_post.assert_called_once_with(
            "https://example.com/traffic",
            params={"start": "2025-09-24T00:00:00Z", "end": "2025-09-24T23:59:59Z"},
            json=self.test_payload,
            auth=self.mock_auth,
            timeout=60,
        )

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result["data"]), 1)

        # Verify print calls
        mock_logger.info.assert_any_call("📡 發送 V2 Traffic API 請求 (嘗試 1/3)")
        mock_logger.info.assert_any_call("📊 API 回應狀態: 200")
        mock_logger.info.assert_any_call("✅ 成功! 返回 1 個數據點")

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_data_point_warning(self, mock_logger, mock_post):
        """Test API call with data point limit warning"""
        # Mock response with high data point count
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"edgeBytesSum": 1000}] * 46000  # 92% of 50000 limit
        }
        mock_post.return_value = mock_response

        result = call_traffic_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify warning message
        mock_logger.warning.assert_any_call("⚠️  警告: 接近數據點限制 (46,000/50,000)")
        self.assertIsNotNone(result)

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_400_error(self, mock_logger, mock_post):
        """Test API call with 400 Bad Request error"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid request parameters"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("HTTP 400", str(context.exception))
        mock_logger.error.assert_any_call("❌ 請求參數錯誤: Invalid request parameters")

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_401_error(self, mock_logger, mock_post):
        """Test API call with 401 Authentication error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Authentication failed (401)", str(context.exception))
        mock_logger.error.assert_any_call("❌ 認證失敗")

    @patch("tools.lib.api_client.logger")
    @patch("tools.lib.api_client.requests.post")
    def test_call_traffic_api_403_error(self, mock_post, mock_logger):
        """Test API call with 403 Authorization error"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Authorization failed (403)", str(context.exception))
        mock_logger.error.assert_any_call("❌ 授權不足")

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_429_retry(self, mock_logger, mock_sleep, mock_post):
        """Test API call with 429 rate limit and retry"""
        # First call returns 429, second call succeeds
        mock_responses = [
            MagicMock(status_code=429),
            MagicMock(status_code=200, json=lambda: {"data": [{"edgeBytesSum": 1000}]}),
        ]
        mock_post.side_effect = mock_responses

        result = call_traffic_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify retry behavior
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second wait
        mock_logger.info.assert_any_call("⏳ 速率限制，等待重試...")
        self.assertIsNotNone(result)

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_429_max_retries(self, mock_logger, mock_sleep, mock_post):
        """Test API call with 429 rate limit exceeding max retries"""
        # All calls return 429
        mock_post.return_value = MagicMock(status_code=429)

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Rate limit exceeded", str(context.exception))
        self.assertEqual(mock_post.call_count, 3)  # Max retries = 3

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_500_retry(self, mock_logger, mock_sleep, mock_post):
        """Test API call with 500 server error and retry"""
        # First call returns 500, second call succeeds
        mock_responses = [
            MagicMock(status_code=500),
            MagicMock(status_code=200, json=lambda: {"data": [{"edgeBytesSum": 1000}]}),
        ]
        mock_post.side_effect = mock_responses

        result = call_traffic_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify retry behavior
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        mock_logger.info.assert_any_call("🔧 伺服器錯誤 (500)，等待重試...")
        self.assertIsNotNone(result)

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_timeout(self, mock_logger, mock_post):
        """Test API call with timeout exception"""
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Request timeout", str(context.exception))
        mock_logger.info.assert_any_call("⏱️  請求超時，嘗試重試...")

    @patch("tools.lib.api_client.logger")
    @patch("tools.lib.api_client.requests.post")
    def test_call_traffic_api_unexpected_status_code(self, mock_post, mock_logger):
        """Test API call with unexpected status code"""
        mock_response = MagicMock()
        mock_response.status_code = 418  # I'm a teapot
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            call_traffic_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Unexpected status code: 418", str(context.exception))
        mock_logger.error.assert_any_call("❌ 未預期的狀態碼: 418")

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_call_traffic_api_network_error_retry(
        self, mock_logger, mock_sleep, mock_post
    ):
        """Test API call with network error and retry"""
        # First call raises network error, second succeeds
        mock_responses = [
            requests.exceptions.RequestException("Network error"),
            MagicMock(status_code=200, json=lambda: {"data": [{"edgeBytesSum": 1000}]}),
        ]
        mock_post.side_effect = mock_responses

        result = call_traffic_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify retry behavior
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        mock_logger.info.assert_any_call("🌐 網路錯誤: Network error")
        self.assertIsNotNone(result)


class TestCallEmissionsAPI(unittest.TestCase):
    """Test call_emissions_api function"""

    def setUp(self):
        """Set up mock config and auth"""
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get_api_endpoints.return_value = {
            "emissions": "https://example.com/emissions"
        }
        self.mock_config.get_max_retries.return_value = 3
        self.mock_config.get_request_timeout.return_value = 60
        self.mock_config.get_exponential_backoff_base.return_value = 2
        self.mock_config.get_network_error_delay.return_value = 1.0
        self.mock_config.get_rate_limit_delay.return_value = 0.5

        self.mock_auth = MagicMock()

        self.test_payload = {
            "dimensions": ["time1day", "country"],
            "metrics": ["edgeBytesSum"],
            "filters": [
                {
                    "dimensionName": "country",
                    "operator": "IN_LIST",
                    "expressions": ["TW"],
                }
            ],
        }

    @patch("tools.lib.api_client.requests.post")
    @patch("tools.lib.api_client.logger")
    def test_call_emissions_api_success(self, mock_logger, mock_post):
        """Test successful emissions API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"time1day": "2025-09-24", "country": "TW", "edgeBytesSum": 2000000}
            ]
        }
        mock_post.return_value = mock_response

        result = call_emissions_api(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.test_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify API call
        mock_post.assert_called_once_with(
            "https://example.com/emissions",
            params={"start": "2025-09-24T00:00:00Z", "end": "2025-09-24T23:59:59Z"},
            json=self.test_payload,
            auth=self.mock_auth,
            timeout=60,
        )

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result["data"]), 1)

        # Verify print calls
        mock_logger.info.assert_any_call("📡 發送 V2 Emissions API 請求 (嘗試 1/3)")
        mock_logger.info.assert_any_call("📊 API 回應狀態: 200")
        mock_logger.info.assert_any_call("✅ 成功! 返回 1 個數據點")


class TestGetTotalEdgeTraffic(unittest.TestCase):
    """Test get_total_edge_traffic function"""

    def setUp(self):
        """Set up mock config"""
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get_cp_codes.return_value = ["123", "456", "789"]
        self.mock_config.get_data_point_limit.return_value = 50000
        self.mock_config.get_billing_coefficient.return_value = 1.0

        self.mock_auth = MagicMock()

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.bytes_to_tb")
    @patch("tools.lib.api_client.format_number")
    @patch("tools.lib.api_client.logger")
    def test_get_total_edge_traffic_success(
        self, mock_logger, mock_format, mock_bytes_to_tb, mock_call_api
    ):
        """Test successful total edge traffic retrieval"""
        # Mock API response
        mock_call_api.return_value = {
            "data": [
                {"edgeBytesSum": 1000000000000},  # 1TB in bytes
                {"edgeBytesSum": 2000000000000},  # 2TB in bytes
            ]
        }

        # Mock conversion functions
        mock_bytes_to_tb.return_value = 3.0  # 3TB total
        mock_format.side_effect = lambda x: f"{x:.1f}"

        result = get_total_edge_traffic(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        # Verify API call
        expected_payload = {
            "dimensions": ["time5minutes"],
            "metrics": ["edgeBytesSum"],
            "filters": [
                {
                    "dimensionName": "cpcode",
                    "operator": "IN_LIST",
                    "expressions": ["123", "456", "789"],
                }
            ],
            "sortBys": [{"name": "time5minutes", "sortOrder": "ASCENDING"}],
            "limit": 50000,
        }
        mock_call_api.assert_called_once_with(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            expected_payload,
            self.mock_auth,
            self.mock_config,
        )

        # Verify calculations
        mock_bytes_to_tb.assert_called_once_with(3000000000000)  # Sum of bytes

        # Verify result structure
        self.assertTrue(result["success"])
        self.assertEqual(result["total_tb"], 3.0)
        self.assertEqual(result["total_bytes"], 3000000000000)
        self.assertEqual(result["billing_estimate"], 3.0 * 1.0)
        self.assertEqual(result["data_points"], 2)

        # Verify print calls
        mock_logger.info.assert_any_call("\n🔍 查詢總體 Edge 流量 (所有 3 個 CP codes)")
        mock_logger.info.assert_any_call("📊 總 Edge 流量: 3.0 TB")
        mock_logger.info.assert_any_call("💰 預估計費用量: 3.0 TB (×1.0)")

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.logger")
    def test_get_total_edge_traffic_no_data(self, mock_logger, mock_call_api):
        """Test total edge traffic with no data returned"""
        mock_call_api.return_value = None

        result = get_total_edge_traffic(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No data returned")

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.logger")
    def test_get_total_edge_traffic_api_error(self, mock_logger, mock_call_api):
        """Test total edge traffic with API error"""
        mock_call_api.side_effect = Exception("API connection failed")

        result = get_total_edge_traffic(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        self.assertFalse(result["success"])
        self.assertIn("API connection failed", result["error"])
        mock_logger.error.assert_any_call("❌ 總體流量查詢失敗: API connection failed")


class TestGetServiceTraffic(unittest.TestCase):
    """Test get_service_traffic function"""

    def setUp(self):
        """Set up mock config"""
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get_service_mappings.return_value = {
            "123": {"name": "Test Service", "unit": "TB", "description": "Test"},
            "456": {"name": "GB Service", "unit": "GB", "description": "Test GB"},
        }
        self.mock_config.get_data_point_limit.return_value = 50000

        self.mock_auth = MagicMock()

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.bytes_to_tb")
    @patch("tools.lib.api_client.format_number")
    @patch("tools.lib.api_client.logger")
    def test_get_service_traffic_tb_unit(
        self, mock_logger, mock_format, mock_bytes_to_tb, mock_call_api
    ):
        """Test service traffic with TB unit"""
        mock_call_api.return_value = {
            "data": [{"edgeBytesSum": 1000000000000}]  # 1TB
        }

        mock_bytes_to_tb.return_value = 1.0
        mock_format.return_value = "1.0"

        result = get_service_traffic(
            "123",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["cp_code"], "123")
        self.assertEqual(result["name"], "Test Service")
        self.assertEqual(result["traffic_value"], 1.0)
        self.assertEqual(result["unit"], "TB")

        mock_logger.info.assert_any_call("🔍 查詢 Test Service (123) 流量")
        mock_logger.info.assert_any_call("📊 Test Service: 1.0 TB")

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.bytes_to_gb")
    @patch("tools.lib.api_client.format_number")
    @patch("tools.lib.api_client.logger")
    def test_get_service_traffic_gb_unit(
        self, mock_logger, mock_format, mock_bytes_to_gb, mock_call_api
    ):
        """Test service traffic with GB unit"""
        mock_call_api.return_value = {
            "data": [{"edgeBytesSum": 1000000000}]  # 1GB
        }

        mock_bytes_to_gb.return_value = 1.0
        mock_format.return_value = "1.0"

        result = get_service_traffic(
            "456",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["unit"], "GB")
        mock_bytes_to_gb.assert_called_once()

    @patch("tools.lib.api_client.call_traffic_api")
    @patch("tools.lib.api_client.logger")
    def test_get_service_traffic_unknown_cp_code(self, mock_logger, mock_call_api):
        """Test service traffic with unknown CP code"""
        mock_call_api.return_value = {"data": [{"edgeBytesSum": 1000000000000}]}

        # Unknown CP code should get default mapping
        result = get_service_traffic(
            "999",  # Not in service mappings
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            self.mock_auth,
            self.mock_config,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "CP 999")  # Default name
        self.assertEqual(result["unit"], "TB")  # Default unit

        mock_logger.info.assert_any_call("🔍 查詢 CP 999 (999) 流量")


class TestGetAllServiceTraffic(unittest.TestCase):
    """Test get_all_service_traffic function"""

    @patch("tools.lib.api_client.get_service_traffic")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_get_all_service_traffic(self, mock_logger, mock_sleep, mock_get_service):
        """Test getting all service traffic"""
        # Mock config with service mappings
        mock_config = MagicMock()
        mock_config.get_service_mappings.return_value = {
            "123": {"name": "Service 1"},
            "456": {"name": "Service 2"},
        }

        # Mock individual service results
        mock_get_service.side_effect = [
            {"success": True, "name": "Service 1"},
            {"success": True, "name": "Service 2"},
        ]

        result = get_all_service_traffic(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            MagicMock(),  # auth
            mock_config,  # config_loader
        )

        # Should call get_service_traffic for each CP code
        self.assertEqual(mock_get_service.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)  # Sleep between requests

        # Verify results structure
        self.assertIn("123", result)
        self.assertIn("456", result)


class TestGetRegionalTraffic(unittest.TestCase):
    """Test get_regional_traffic function"""

    @patch("tools.lib.api_client.call_emissions_api")
    @patch("tools.lib.api_client.bytes_to_tb")
    @patch("tools.lib.api_client.format_number")
    @patch("tools.lib.api_client.logger")
    def test_get_regional_traffic_success(
        self, mock_logger, mock_format, mock_bytes_to_tb, mock_call_api
    ):
        """Test successful regional traffic retrieval"""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_region_mappings.return_value = {"TW": "Region 2"}
        mock_config.get_cp_codes.return_value = ["123", "456"]
        mock_config.get_data_point_limit.return_value = 50000

        mock_call_api.return_value = {
            "data": [
                {
                    "edgeBytesSum": 1000000000000,
                    "country": "TW",
                    "time1day": "2025-09-24",
                }
            ]
        }

        mock_bytes_to_tb.return_value = 1.0
        mock_format.return_value = "1.0"

        result = get_regional_traffic(
            "TW",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            MagicMock(),  # auth
            mock_config,  # config_loader
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["country_code"], "TW")
        self.assertEqual(result["region_name"], "Region 2")
        self.assertEqual(result["total_tb"], 1.0)

        mock_logger.info.assert_any_call("🔍 查詢 Region 2 (TW) Edge 流量")
        mock_logger.info.assert_any_call("📊 Region 2: 1.0 TB")


class TestGetAllRegionalTraffic(unittest.TestCase):
    """Test get_all_regional_traffic function"""

    @patch("tools.lib.api_client.get_regional_traffic")
    @patch("tools.lib.api_client.time.sleep")
    @patch("tools.lib.api_client.logger")
    def test_get_all_regional_traffic(self, mock_logger, mock_sleep, mock_get_regional):
        """Test getting all regional traffic"""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_target_regions.return_value = [
            "ID",
            "TW",
            "SG",
        ]

        # Mock individual regional results
        mock_get_regional.side_effect = [
            {"success": True, "total_tb": 10.0, "region_name": "Region 1"},
            {"success": True, "total_tb": 5.0, "region_name": "Region 2"},
            {"success": True, "total_tb": 3.0, "region_name": "Region 3"},
        ]

        result = get_all_regional_traffic(
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            MagicMock(),  # auth
            mock_config,  # config_loader
        )

        # Should call get_regional_traffic for each region
        self.assertEqual(mock_get_regional.call_count, 3)
        mock_get_regional.assert_any_call(
            "ID",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            unittest.mock.ANY,
            mock_config,
        )
        mock_get_regional.assert_any_call(
            "TW",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            unittest.mock.ANY,
            mock_config,
        )
        mock_get_regional.assert_any_call(
            "SG",
            "2025-09-24T00:00:00Z",
            "2025-09-24T23:59:59Z",
            unittest.mock.ANY,
            mock_config,
        )

        # Verify summary
        self.assertIn("_summary", result)
        summary = result["_summary"]
        self.assertEqual(summary["total_regions"], 3)
        self.assertEqual(summary["successful_queries"], 3)
        self.assertEqual(summary["total_regional_traffic_tb"], 18.0)  # 10+5+3
        self.assertEqual(summary["success_rate"], 100.0)

        # Verify print calls
        mock_logger.info.assert_any_call("\n🔍 查詢所有地區 Edge 流量")
        mock_logger.info.assert_any_call("\n📊 地區流量總計: 18.00 TB")
        mock_logger.info.assert_any_call("✅ 成功查詢: 3/3 個地區")


class TestEmissionsAPIErrorHandling(unittest.TestCase):
    """Test emissions API error handling"""

    def setUp(self):
        """Set up test data"""
        self.test_payload = {"dimensions": ["time1day"], "metrics": ["edgeBytesSum"]}
        self.mock_auth = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.get_api_endpoints.return_value = {
            "emissions": "https://example.com/emissions"
        }
        self.mock_config.get_request_timeout.return_value = 60
        self.mock_config.get_max_retries.return_value = 3
        self.mock_config.get_exponential_backoff_base.return_value = 2
        self.mock_config.get_network_error_delay.return_value = 1.0
        self.mock_config.get_rate_limit_delay.return_value = 0.5

    @patch("tools.lib.api_client.logger")
    @patch("tools.lib.api_client.requests.post")
    def test_call_emissions_api_403_error(self, mock_post, mock_logger):
        """Test emissions API call with 403 authorization error"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            call_emissions_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Authorization failed (403)", str(context.exception))
        mock_logger.error.assert_any_call("❌ 授權不足")

    @patch("tools.lib.api_client.logger")
    @patch("tools.lib.api_client.requests.post")
    def test_call_emissions_api_timeout(self, mock_post, mock_logger):
        """Test emissions API call with timeout"""
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(Exception) as context:
            call_emissions_api(
                "2025-09-24T00:00:00Z",
                "2025-09-24T23:59:59Z",
                self.test_payload,
                self.mock_auth,
                self.mock_config,
            )

        self.assertIn("Request timeout", str(context.exception))
        mock_logger.info.assert_any_call("⏱️  請求超時，嘗試重試...")


if __name__ == "__main__":
    unittest.main()
