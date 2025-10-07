#!/usr/bin/env python3
"""
Configuration Loader for Akamai Traffic Report

This module handles loading and validation of external configuration files,
replacing hardcoded constants in the main script.

Author: Development Team
Version: 1.0
Date: 2024-09-24
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigurationError(Exception):
    """Configuration loading or validation error"""

    pass


class ConfigLoader:
    """Configuration loader and validator for Akamai Traffic Report"""

    REQUIRED_SECTIONS = ["api", "business", "reporting", "system"]
    REQUIRED_API_FIELDS = ["endpoints", "timeout", "max_retries"]
    REQUIRED_BUSINESS_FIELDS = ["cp_codes", "service_mappings", "billing_coefficient"]
    REQUIRED_REPORTING_FIELDS = ["week_definition", "region_mappings"]
    REQUIRED_SYSTEM_FIELDS = ["data_point_limit"]

    VALID_WEEK_DEFINITIONS = [
        "sunday_to_saturday",
        "monday_to_sunday",
        "monday_to_friday",
        "custom",
    ]

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration loader

        Args:
            config_file (str): Path to configuration file (default: 'config.json')
        """
        self.config_file = config_file
        self.config = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from file

        Returns:
            Dict[str, Any]: Loaded configuration

        Raises:
            ConfigurationError: If loading or validation fails
        """
        try:
            # Check if config file exists
            if not Path(self.config_file).exists():
                raise ConfigurationError(
                    f"配置檔案不存在: {self.config_file}\n"
                    f"請複製 config.template.json 為 {self.config_file} 並填入實際值"
                )

            # Load JSON configuration
            with open(self.config_file, encoding="utf-8") as f:
                self.config = json.load(f)

            # Validate configuration structure
            self._validate_config()

            print(f"✅ 配置載入成功: {self.config_file}")
            return self.config

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置檔案 JSON 格式錯誤: {e}")
        except Exception as e:
            raise ConfigurationError(f"配置載入失敗: {e}")

    def _validate_config(self):
        """Validate loaded configuration structure"""
        if not self.config:
            raise ConfigurationError("配置為空")

        # Check required sections
        missing_sections = []
        for section in self.REQUIRED_SECTIONS:
            if section not in self.config:
                missing_sections.append(section)

        if missing_sections:
            raise ConfigurationError(f"缺少必要配置區段: {', '.join(missing_sections)}")

        # Validate API section
        self._validate_section(self.config["api"], self.REQUIRED_API_FIELDS, "api")

        # Validate business section
        self._validate_section(
            self.config["business"], self.REQUIRED_BUSINESS_FIELDS, "business"
        )

        # Validate reporting section
        self._validate_section(
            self.config["reporting"], self.REQUIRED_REPORTING_FIELDS, "reporting"
        )

        # Validate system section
        self._validate_section(
            self.config["system"], self.REQUIRED_SYSTEM_FIELDS, "system"
        )

        # Validate specific fields
        self._validate_week_definition()
        self._validate_cp_codes()
        self._validate_service_mappings()

    def _validate_section(
        self, section: Dict[str, Any], required_fields: List[str], section_name: str
    ):
        """Validate a configuration section has required fields"""
        missing_fields = []
        for field in required_fields:
            if field not in section:
                missing_fields.append(field)

        if missing_fields:
            raise ConfigurationError(
                f"配置區段 '{section_name}' 缺少必要欄位: {', '.join(missing_fields)}"
            )

    def _validate_week_definition(self):
        """Validate week definition setting"""
        week_def = self.config["reporting"]["week_definition"]
        if week_def not in self.VALID_WEEK_DEFINITIONS:
            raise ConfigurationError(
                f"無效的週期定義: {week_def}. "
                f"可用選項: {', '.join(self.VALID_WEEK_DEFINITIONS)}"
            )

        # If custom, check custom_start_day is provided
        if week_def == "custom":
            if "custom_start_day" not in self.config["reporting"]:
                raise ConfigurationError(
                    "使用 'custom' 週期定義時必須提供 'custom_start_day' 參數"
                )

            start_day = self.config["reporting"]["custom_start_day"]
            if not isinstance(start_day, int) or start_day < 0 or start_day > 6:
                raise ConfigurationError(
                    f"custom_start_day 必須是 0-6 之間的整數 (0=週日, 6=週六)，當前值: {start_day}"
                )

    def _validate_cp_codes(self):
        """Validate CP codes list"""
        cp_codes = self.config["business"]["cp_codes"]
        if not isinstance(cp_codes, list):
            raise ConfigurationError("cp_codes 必須是陣列格式")

        if len(cp_codes) == 0:
            raise ConfigurationError("cp_codes 陣列不能為空")

        # Check all CP codes are strings
        for i, cp_code in enumerate(cp_codes):
            if not isinstance(cp_code, str):
                raise ConfigurationError(
                    f"CP code at index {i} 必須是字串格式: {cp_code}"
                )

    def _validate_service_mappings(self):
        """Validate service mappings structure"""
        mappings = self.config["business"]["service_mappings"]
        if not isinstance(mappings, dict):
            raise ConfigurationError("service_mappings 必須是物件格式")

        for cp_code, mapping in mappings.items():
            if not isinstance(mapping, dict):
                raise ConfigurationError(
                    f"service_mappings['{cp_code}'] 必須是物件格式"
                )

            required_mapping_fields = ["name", "unit", "description"]
            for field in required_mapping_fields:
                if field not in mapping:
                    raise ConfigurationError(
                        f"service_mappings['{cp_code}'] 缺少必要欄位: {field}"
                    )

    # Accessor methods for easy configuration access
    def get_cp_codes(self) -> List[str]:
        """Get all CP codes list"""
        return self.config["business"]["cp_codes"]

    def get_service_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get service mappings dictionary"""
        return self.config["business"]["service_mappings"]

    def get_region_mappings(self) -> Dict[str, str]:
        """Get region mappings dictionary"""
        return self.config["reporting"]["region_mappings"]

    def get_target_regions(self) -> List[str]:
        """Get list of target regions to analyze"""
        # Default to standard regions if not specified in config
        return self.config["reporting"].get(
            "target_regions", ["REGION_CODE_1", "REGION_CODE_2", "REGION_CODE_3"]
        )

    def get_billing_coefficient(self) -> float:
        """Get billing coefficient"""
        return self.config["business"]["billing_coefficient"]

    def get_api_endpoints(self) -> Dict[str, str]:
        """Get API endpoints"""
        return self.config["api"]["endpoints"]

    def get_max_retries(self) -> int:
        """Get maximum retry attempts"""
        return self.config["api"]["max_retries"]

    def get_request_timeout(self, api_type: str = None) -> int:
        """
        Get request timeout in seconds for specific API type.

        Args:
            api_type: API type ("traffic" or "emissions"). If None, returns default timeout.

        Returns:
            int: Timeout in seconds
        """
        if api_type:
            # Try to get API-specific timeout first
            api_timeouts = self.config.get("api", {}).get("timeouts", {})
            if api_type.lower() in api_timeouts:
                return api_timeouts[api_type.lower()]

        # Fall back to default timeout
        return self.config["api"]["timeout"]

    def get_data_point_limit(self) -> int:
        """Get data point limit"""
        return self.config["system"]["data_point_limit"]

    def get_week_definition(self) -> str:
        """Get week definition setting"""
        return self.config["reporting"]["week_definition"]

    def get_custom_start_day(self) -> Optional[int]:
        """Get custom start day (if week_definition is 'custom')"""
        return self.config["reporting"].get("custom_start_day")

    def get_week_start_offset(self) -> int:
        """
        Get the day offset for week start calculation

        Returns:
            int: Days to offset from Sunday (0) to get the desired week start
                 0 = Sunday, 1 = Monday, etc.
        """
        week_def = self.get_week_definition()

        if week_def == "sunday_to_saturday":
            return 0  # Week starts on Sunday
        elif week_def == "monday_to_sunday":
            return 1  # Week starts on Monday
        elif week_def == "monday_to_friday":
            return 1  # Week starts on Monday (5-day week)
        elif week_def == "custom":
            return self.get_custom_start_day()
        else:
            raise ConfigurationError(f"未支援的週期定義: {week_def}")

    def get_week_duration_days(self) -> int:
        """
        Get the duration of the week in days

        Returns:
            int: Number of days in the reporting week
        """
        week_def = self.get_week_definition()

        if week_def == "monday_to_friday":
            return 5  # 5-day work week
        else:
            return 7  # Standard 7-day week

    def get_exponential_backoff_base(self) -> int:
        """
        Get exponential backoff base for retry delays.

        Returns:
            int: Base for exponential backoff calculation (delay = base^attempt).
                 Defaults to 2 if not configured.
        """
        return (
            self.config.get("api", {})
            .get("retry_delays", {})
            .get("exponential_backoff_base", 2)
        )

    def get_network_error_delay(self) -> float:
        """
        Get delay for network errors.

        Returns:
            float: Fixed delay after network errors in seconds.
                   Defaults to 1.0 if not configured.
        """
        return (
            self.config.get("api", {})
            .get("retry_delays", {})
            .get("network_error_delay", 1.0)
        )

    def get_rate_limit_delay(self) -> float:
        """
        Get delay between API calls to avoid rate limiting.

        Returns:
            float: Delay between API calls in seconds.
                   Defaults to 0.5 if not configured.
        """
        return (
            self.config.get("api", {})
            .get("retry_delays", {})
            .get("rate_limit_delay", 0.5)
        )

    def get_max_workers(self) -> int:
        """
        Get maximum number of concurrent workers for parallel API requests.

        Returns:
            int: Maximum concurrent workers. Defaults to 3 if not configured.
        """
        return (
            self.config.get("system", {}).get("concurrency", {}).get("max_workers", 3)
        )

    def get_circuit_breaker_failure_threshold(self) -> int:
        """
        Get circuit breaker failure threshold.

        Returns:
            int: Number of failures before opening circuit. Defaults to 3.
        """
        return (
            self.config.get("system", {})
            .get("circuit_breaker", {})
            .get("failure_threshold", 3)
        )

    def get_circuit_breaker_recovery_timeout(self) -> int:
        """
        Get circuit breaker recovery timeout.

        Returns:
            int: Seconds before attempting recovery. Defaults to 30.
        """
        return (
            self.config.get("system", {})
            .get("circuit_breaker", {})
            .get("recovery_timeout", 30)
        )

    def get_circuit_breaker_success_threshold(self) -> int:
        """
        Get circuit breaker success threshold.

        Returns:
            int: Successes needed to close circuit from half-open. Defaults to 2.
        """
        return (
            self.config.get("system", {})
            .get("circuit_breaker", {})
            .get("success_threshold", 2)
        )

    def get_data_point_warning_threshold(self) -> float:
        """
        Get threshold ratio for data point warning.

        Returns:
            float: Ratio at which to warn about approaching data point limit (0-1).
                   For example, 0.9 means warn at 90% of limit.
                   Defaults to 0.9 if not configured.
        """
        return (
            self.config.get("api", {})
            .get("thresholds", {})
            .get("data_point_warning_ratio", 0.9)
        )

    def get_edgerc_section(self) -> str:
        """
        Get EdgeRC section name to use for authentication.

        Returns:
            str: Section name in ~/.edgerc file.
                 Defaults to 'default' if not configured.
        """
        return self.config.get("api", {}).get("edgerc_section", "default")

    def get_auth_source(self) -> str:
        """
        Get authentication source.

        Returns:
            str: Authentication source ('edgerc', 'env', or 'aws').
                 Defaults to 'edgerc' if not configured.
        """
        return self.config.get("authentication", {}).get("source", "edgerc")

    def get_edgerc_path(self) -> Optional[str]:
        """
        Get custom .edgerc file path.

        Returns:
            Optional[str]: Custom path to .edgerc file, or None to use default (~/.edgerc)
        """
        return self.config.get("authentication", {}).get("edgerc_path")

    def print_config_summary(self):
        """Print a summary of loaded configuration (without sensitive data)"""
        if not self.config:
            print("❌ 配置未載入")
            return

        print("\n📋 配置摘要:")
        print(f"   CP Codes 數量: {len(self.get_cp_codes())}")
        print(f"   服務映射數量: {len(self.get_service_mappings())}")
        print(f"   週期定義: {self.get_week_definition()}")
        if self.get_week_definition() == "custom":
            print(f"   自定義起始日: {self.get_custom_start_day()} (0=週日)")
        print(f"   計費係數: {self.get_billing_coefficient()}")
        print(f"   API 超時: {self.get_request_timeout()} 秒")
        print(f"   最大重試: {self.get_max_retries()} 次")
        print(f"   數據點限制: {self.get_data_point_limit():,}")


def load_configuration(config_file: str = "config.json") -> ConfigLoader:
    """
    Convenience function to load and return configuration loader

    Args:
        config_file (str): Configuration file path

    Returns:
        ConfigLoader: Loaded configuration object

    Raises:
        ConfigurationError: If loading fails
    """
    loader = ConfigLoader(config_file)
    loader.load_config()
    return loader


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_configuration()
        config.print_config_summary()
        print("✅ 配置檔案測試成功")
    except ConfigurationError as e:
        print(f"❌ 配置檔案測試失敗: {e}")
