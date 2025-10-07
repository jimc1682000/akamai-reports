#!/usr/bin/env python3
"""
Unit Tests for config_loader.py

Comprehensive test coverage for configuration loading and validation functionality.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from tools.lib.config_loader import ConfigLoader, ConfigurationError, load_configuration


class TestConfigurationError(unittest.TestCase):
    """Test ConfigurationError exception"""

    def test_configuration_error_creation(self):
        """Test ConfigurationError can be created and raised"""
        error = ConfigurationError("Test error")
        self.assertEqual(str(error), "Test error")

        with self.assertRaises(ConfigurationError) as context:
            raise ConfigurationError("Test message")
        self.assertEqual(str(context.exception), "Test message")


class TestConfigLoader(unittest.TestCase):
    """Test ConfigLoader class functionality"""

    def setUp(self):
        """Set up test environment"""
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
                "cp_codes": ["123", "456", "789"],
                "service_mappings": {
                    "123": {
                        "name": "Service 1",
                        "unit": "TB",
                        "description": "Test service",
                    },
                    "456": {
                        "name": "Service 2",
                        "unit": "GB",
                        "description": "Test service 2",
                    },
                    "789": {
                        "name": "Service 3",
                        "unit": "TB",
                        "description": "Test service 3",
                    },
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "custom_start_day": 0,
                "region_mappings": {
                    "REGION_CODE_2": "地區名稱 2",
                    "REGION_CODE_3": "地區名稱 3",
                },
            },
            "system": {
                "data_point_limit": 50000,
                "concurrency": {
                    "max_workers": 3,
                    "rate_limit_delay": 0.1,
                    "pool_connections": 10,
                    "pool_maxsize": 20,
                },
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "recovery_timeout": 30,
                    "success_threshold": 2,
                },
            },
        }

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary files
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)

    def _write_config_file(self, config_data):
        """Helper to write config data to test file"""
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def test_init_with_default_config_file(self):
        """Test ConfigLoader initialization with default config file"""
        loader = ConfigLoader()
        self.assertEqual(loader.config_file, "config.json")
        self.assertIsNone(loader.config)

    def test_init_with_custom_config_file(self):
        """Test ConfigLoader initialization with custom config file"""
        loader = ConfigLoader("custom_config.json")
        self.assertEqual(loader.config_file, "custom_config.json")
        self.assertIsNone(loader.config)

    def test_load_config_success(self):
        """Test successful configuration loading"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)

        config = loader.load_config()
        self.assertEqual(config, self.valid_config)
        self.assertEqual(loader.config, self.valid_config)

    def test_load_config_file_not_exists(self):
        """Test loading non-existent config file"""
        loader = ConfigLoader("non_existent.json")

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        self.assertIn("配置檔案不存在", str(context.exception))
        self.assertIn("請複製 config.template.json", str(context.exception))

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON config file"""
        # Write invalid JSON
        with open(self.test_config_file, "w") as f:
            f.write('{"invalid": json}')

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        self.assertIn("配置檔案 JSON 格式錯誤", str(context.exception))

    def test_validate_config_missing_sections(self):
        """Test validation with missing required sections"""
        incomplete_config = {"api": {"endpoints": {}}}
        self._write_config_file(incomplete_config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Field required
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("Field required", str(context.exception))

    def test_validate_config_missing_api_fields(self):
        """Test validation with missing API fields"""
        config = self.valid_config.copy()
        del config["api"]["endpoints"]  # endpoints is required (no default)
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Field required for endpoints
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("endpoints", str(context.exception))

    def test_validate_config_invalid_week_definition(self):
        """Test validation with invalid week definition"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "invalid_week"
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be one of the allowed literals
        self.assertIn("配置驗證失敗", str(context.exception))

    def test_validate_config_custom_week_missing_start_day(self):
        """Test validation with custom week definition but missing start day"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "custom"
        del config["reporting"]["custom_start_day"]
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic model_validator: custom_start_day must be provided when week_definition is 'custom'
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("custom_start_day", str(context.exception))

    def test_validate_config_invalid_custom_start_day(self):
        """Test validation with invalid custom start day"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "custom"
        config["reporting"]["custom_start_day"] = 7  # Invalid, should be 0-6
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be less than or equal to 6
        self.assertIn("配置驗證失敗", str(context.exception))

    def test_validate_cp_codes_not_list(self):
        """Test validation with CP codes not as list"""
        config = self.valid_config.copy()
        config["business"]["cp_codes"] = "not_a_list"
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be a valid list
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("cp_codes", str(context.exception))

    def test_validate_empty_cp_codes(self):
        """Test validation with empty CP codes list"""
        config = self.valid_config.copy()
        config["business"]["cp_codes"] = []
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: list should have at least 1 item
        self.assertIn("配置驗證失敗", str(context.exception))

    def test_validate_cp_codes_invalid_type(self):
        """Test validation with non-string CP codes"""
        config = self.valid_config.copy()
        config["business"]["cp_codes"] = ["123", 456]  # Mixed types
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be a valid string
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("cp_codes", str(context.exception))

    def test_validate_service_mappings_not_dict(self):
        """Test validation with service mappings not as dict"""
        config = self.valid_config.copy()
        config["business"]["service_mappings"] = []
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be a valid dictionary
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("service_mappings", str(context.exception))

    def test_validate_service_mappings_missing_fields(self):
        """Test validation with service mappings missing required fields"""
        config = self.valid_config.copy()
        config["business"]["service_mappings"] = {
            "123": {"name": "Service", "unit": "TB"}  # Missing description
        }
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Field required (description)
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("description", str(context.exception))

    # Test accessor methods
    def test_get_cp_codes(self):
        """Test get_cp_codes method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        cp_codes = loader.get_cp_codes()
        self.assertEqual(cp_codes, ["123", "456", "789"])

    def test_get_service_mappings(self):
        """Test get_service_mappings method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        mappings = loader.get_service_mappings()
        self.assertEqual(mappings, self.valid_config["business"]["service_mappings"])

    def test_get_region_mappings(self):
        """Test get_region_mappings method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        mappings = loader.get_region_mappings()
        self.assertEqual(
            mappings, {"REGION_CODE_2": "地區名稱 2", "REGION_CODE_3": "地區名稱 3"}
        )

    def test_get_billing_coefficient(self):
        """Test get_billing_coefficient method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        coefficient = loader.get_billing_coefficient()
        self.assertEqual(coefficient, 1.0)

    def test_get_api_endpoints(self):
        """Test get_api_endpoints method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        endpoints = loader.get_api_endpoints()
        expected = {
            "traffic": "https://example.com/traffic",
            "emissions": "https://example.com/emissions",
        }
        self.assertEqual(endpoints, expected)

    def test_get_max_retries(self):
        """Test get_max_retries method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        retries = loader.get_max_retries()
        self.assertEqual(retries, 3)

    def test_get_request_timeout(self):
        """Test get_request_timeout method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        timeout = loader.get_request_timeout()
        self.assertEqual(timeout, 60)

    def test_get_request_timeout_with_api_specific(self):
        """Test get_request_timeout with API-specific configuration"""
        config = self.valid_config.copy()
        config["api"]["timeouts"] = {"traffic": 60, "emissions": 90}
        self._write_config_file(config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        # Test API-specific timeouts
        traffic_timeout = loader.get_request_timeout("traffic")
        self.assertEqual(traffic_timeout, 60)

        emissions_timeout = loader.get_request_timeout("emissions")
        self.assertEqual(emissions_timeout, 90)

        # Test default timeout when no API type specified
        default_timeout = loader.get_request_timeout()
        self.assertEqual(default_timeout, 60)

    def test_get_request_timeout_fallback_to_default(self):
        """Test get_request_timeout falls back to default when API type not configured"""
        config = self.valid_config.copy()
        # Only configure timeout for traffic, not emissions
        config["api"]["timeouts"] = {"traffic": 45}
        self._write_config_file(config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        # Traffic should use specific timeout
        traffic_timeout = loader.get_request_timeout("traffic")
        self.assertEqual(traffic_timeout, 45)

        # Emissions should fall back to default
        emissions_timeout = loader.get_request_timeout("emissions")
        self.assertEqual(emissions_timeout, 60)

    def test_get_request_timeout_case_insensitive(self):
        """Test get_request_timeout is case-insensitive"""
        config = self.valid_config.copy()
        config["api"]["timeouts"] = {"traffic": 60, "emissions": 90}
        self._write_config_file(config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        # Test case variations
        self.assertEqual(loader.get_request_timeout("Traffic"), 60)
        self.assertEqual(loader.get_request_timeout("TRAFFIC"), 60)
        self.assertEqual(loader.get_request_timeout("Emissions"), 90)
        self.assertEqual(loader.get_request_timeout("EMISSIONS"), 90)

    def test_get_data_point_limit(self):
        """Test get_data_point_limit method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        limit = loader.get_data_point_limit()
        self.assertEqual(limit, 50000)

    def test_get_week_definition(self):
        """Test get_week_definition method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        week_def = loader.get_week_definition()
        self.assertEqual(week_def, "sunday_to_saturday")

    def test_get_custom_start_day(self):
        """Test get_custom_start_day method"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        start_day = loader.get_custom_start_day()
        self.assertEqual(start_day, 0)

    def test_get_week_start_offset_sunday_to_saturday(self):
        """Test get_week_start_offset for sunday_to_saturday"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        offset = loader.get_week_start_offset()
        self.assertEqual(offset, 0)

    def test_get_week_start_offset_monday_to_sunday(self):
        """Test get_week_start_offset for monday_to_sunday"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "monday_to_sunday"
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        offset = loader.get_week_start_offset()
        self.assertEqual(offset, 1)

    def test_get_week_start_offset_monday_to_friday(self):
        """Test get_week_start_offset for monday_to_friday"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "monday_to_friday"
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        offset = loader.get_week_start_offset()
        self.assertEqual(offset, 1)

    def test_get_week_start_offset_custom(self):
        """Test get_week_start_offset for custom"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "custom"
        config["reporting"]["custom_start_day"] = 3  # Wednesday
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        offset = loader.get_week_start_offset()
        self.assertEqual(offset, 3)

    def test_get_week_start_offset_invalid(self):
        """Test get_week_start_offset with invalid week definition"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "invalid"
        # Bypass validation by setting config directly
        loader = ConfigLoader(self.test_config_file)
        loader.config = config

        with self.assertRaises(ConfigurationError) as context:
            loader.get_week_start_offset()

        self.assertIn("未支援的週期定義", str(context.exception))

    def test_get_week_duration_days_standard(self):
        """Test get_week_duration_days for standard weeks"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        duration = loader.get_week_duration_days()
        self.assertEqual(duration, 7)

    def test_get_week_duration_days_workweek(self):
        """Test get_week_duration_days for work week"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "monday_to_friday"
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        duration = loader.get_week_duration_days()
        self.assertEqual(duration, 5)

    @patch("builtins.print")
    def test_print_config_summary_no_config(self, mock_print):
        """Test print_config_summary with no loaded config"""
        loader = ConfigLoader()
        loader.print_config_summary()

        mock_print.assert_called_with("❌ 配置未載入")

    @patch("builtins.print")
    def test_print_config_summary_with_config(self, mock_print):
        """Test print_config_summary with loaded config"""
        self._write_config_file(self.valid_config)
        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        loader.print_config_summary()

        # Verify some expected print calls
        call_args = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("配置摘要" in arg for arg in call_args))
        self.assertTrue(any("CP Codes 數量" in arg for arg in call_args))
        self.assertTrue(any("週期定義" in arg for arg in call_args))

    @patch("builtins.print")
    def test_print_config_summary_with_custom_week(self, mock_print):
        """Test print_config_summary with custom week definition"""
        config = self.valid_config.copy()
        config["reporting"]["week_definition"] = "custom"
        config["reporting"]["custom_start_day"] = 2
        self._write_config_file(config)

        loader = ConfigLoader(self.test_config_file)
        loader.load_config()

        loader.print_config_summary()

        # Verify custom start day is shown
        call_args = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("自定義起始日: 2" in arg for arg in call_args))


class TestLoadConfigurationFunction(unittest.TestCase):
    """Test load_configuration convenience function"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")

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
                "cp_codes": ["123"],
                "service_mappings": {
                    "123": {"name": "Test", "unit": "TB", "description": "Test"}
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "region_mappings": {"REGION_CODE_2": "地區名稱 2"},
            },
            "system": {
                "data_point_limit": 1000,
                "concurrency": {
                    "max_workers": 3,
                    "rate_limit_delay": 0.1,
                    "pool_connections": 10,
                    "pool_maxsize": 20,
                },
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "recovery_timeout": 30,
                    "success_threshold": 2,
                },
            },
        }

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)

    def test_load_configuration_success(self):
        """Test successful configuration loading via convenience function"""
        with open(self.test_config_file, "w") as f:
            json.dump(self.valid_config, f)

        loader = load_configuration(self.test_config_file)

        self.assertIsInstance(loader, ConfigLoader)
        self.assertEqual(loader.config, self.valid_config)

    def test_load_configuration_failure(self):
        """Test failed configuration loading via convenience function"""
        with self.assertRaises(ConfigurationError):
            load_configuration("non_existent.json")


class TestConfigValidationEdgeCases(unittest.TestCase):
    """Test edge cases in config validation"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)

    def test_validate_service_mappings_non_dict_mapping(self):
        """Test validation with non-dict mapping"""
        config_data = {
            "api": {"endpoints": {}, "timeout": 60, "max_retries": 3},
            "business": {
                "cp_codes": ["123"],
                "service_mappings": {"123": "invalid_non_dict"},  # Should be dict
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "region_mappings": {},
            },
            "system": {"data_point_limit": 5000},
        }

        with open(self.config_file, "w") as f:
            json.dump(config_data, f)

        loader = ConfigLoader(self.config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Input should be a valid dictionary
        self.assertIn("配置驗證失敗", str(context.exception))

    def test_validate_service_mappings_missing_field(self):
        """Test validation with missing required field in service mapping"""
        config_data = {
            "api": {"endpoints": {}, "timeout": 60, "max_retries": 3},
            "business": {
                "cp_codes": ["123"],
                "service_mappings": {
                    "123": {"name": "Test", "unit": "TB"}  # Missing 'description'
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "region_mappings": {},
            },
            "system": {"data_point_limit": 5000},
        }

        with open(self.config_file, "w") as f:
            json.dump(config_data, f)

        loader = ConfigLoader(self.config_file)

        with self.assertRaises(ConfigurationError) as context:
            loader.load_config()

        # Pydantic error: Field required (description)
        self.assertIn("配置驗證失敗", str(context.exception))
        self.assertIn("description", str(context.exception))

    def test_get_target_regions_default(self):
        """Test get_target_regions returns default when not configured"""
        # Use valid_config as base but ensure target_regions is not set
        config_data = {
            "api": {
                "endpoints": {
                    "traffic": "https://example.com/traffic",
                    "emissions": "https://example.com/emissions",
                },
                "timeout": 60,
                "max_retries": 3,
            },
            "business": {
                "cp_codes": ["123"],
                "service_mappings": {
                    "123": {
                        "name": "Service 1",
                        "unit": "TB",
                        "description": "Test service",
                    }
                },
                "billing_coefficient": 1.0,
            },
            "reporting": {
                "week_definition": "sunday_to_saturday",
                "region_mappings": {"REGION_CODE_1": "Region 1"},
            },
            "system": {
                "data_point_limit": 5000,
                "concurrency": {
                    "max_workers": 3,
                    "rate_limit_delay": 0.1,
                    "pool_connections": 10,
                    "pool_maxsize": 20,
                },
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "recovery_timeout": 30,
                    "success_threshold": 2,
                },
            },
        }

        with open(self.config_file, "w") as f:
            json.dump(config_data, f)

        loader = ConfigLoader(self.config_file)
        loader.load_config()

        # Should return default regions when not configured
        regions = loader.get_target_regions()
        self.assertEqual(regions, ["REGION_CODE_1", "REGION_CODE_2", "REGION_CODE_3"])

    def test_print_config_summary_no_config(self):
        """Test print_config_summary with no config loaded"""
        loader = ConfigLoader(self.config_file)

        with patch("builtins.print") as mock_print:
            loader.print_config_summary()

        mock_print.assert_called_with("❌ 配置未載入")


if __name__ == "__main__":
    unittest.main()
