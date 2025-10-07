#!/usr/bin/env python3
"""
Configuration Loader for Akamai Traffic Report

This module handles loading and validation of external configuration files,
replacing hardcoded constants in the main script.

Author: Development Team
Version: 2.0
Date: 2024-09-24
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from tools.lib.models.config_models import Config


class ConfigurationError(Exception):
    """Configuration loading or validation error"""

    pass


class ConfigLoader:
    """
    Configuration loader and validator for Akamai Traffic Report.

    Uses Pydantic models for type-safe validation with comprehensive error messages.
    """

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration loader

        Args:
            config_file (str): Path to configuration file (default: 'config.json')
        """
        self.config_file = config_file
        self.config: Optional[Dict[str, Any]] = None
        self.validated_config: Optional[Config] = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from file using Pydantic models.

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
                config_data = json.load(f)

            # Validate using Pydantic model
            try:
                self.validated_config = Config.model_validate(config_data)
                # Store raw dict for backward compatibility
                self.config = config_data
            except ValidationError as e:
                # Format Pydantic validation errors for better readability
                error_messages = []
                for error in e.errors():
                    field_path = " -> ".join(str(loc) for loc in error["loc"])
                    error_messages.append(f"  • {field_path}: {error['msg']}")
                raise ConfigurationError("配置驗證失敗:\n" + "\n".join(error_messages))

            print(f"✅ 配置載入成功: {self.config_file}")
            return self.config

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置檔案 JSON 格式錯誤: {e}")
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"配置載入失敗: {e}")

    def _ensure_config_loaded(self) -> Dict[str, Any]:
        """Ensure config is loaded and return it"""
        if self.config is None:
            raise ConfigurationError("配置未載入，請先呼叫 load_config()")
        return self.config

    # Accessor methods for easy configuration access
    def get_cp_codes(self) -> List[str]:
        """Get all CP codes list"""
        config = self._ensure_config_loaded()
        return config["business"]["cp_codes"]  # type: ignore[no-any-return]

    def get_service_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get service mappings dictionary"""
        config = self._ensure_config_loaded()
        return config["business"]["service_mappings"]  # type: ignore[no-any-return]

    def get_region_mappings(self) -> Dict[str, str]:
        """Get region mappings dictionary"""
        config = self._ensure_config_loaded()
        return config["reporting"]["region_mappings"]  # type: ignore[no-any-return]

    def get_target_regions(self) -> List[str]:
        """Get list of target regions to analyze"""
        config = self._ensure_config_loaded()
        # If target_regions is not specified, use all keys from region_mappings
        if "target_regions" in config["reporting"]:
            return config["reporting"]["target_regions"]  # type: ignore[no-any-return]
        else:
            # Use all region codes from region_mappings
            return list(config["reporting"]["region_mappings"].keys())

    def get_billing_coefficient(self) -> float:
        """Get billing coefficient"""
        config = self._ensure_config_loaded()
        return config["business"]["billing_coefficient"]  # type: ignore[no-any-return]

    def get_api_endpoints(self) -> Dict[str, str]:
        """Get API endpoints"""
        config = self._ensure_config_loaded()
        return config["api"]["endpoints"]  # type: ignore[no-any-return]

    def get_max_retries(self) -> int:
        """Get maximum retry attempts"""
        config = self._ensure_config_loaded()
        return config["api"]["max_retries"]  # type: ignore[no-any-return]

    def get_request_timeout(self, api_type: Optional[str] = None) -> int:
        """
        Get request timeout in seconds for specific API type.

        Args:
            api_type: API type ("traffic" or "emissions"). If None, returns default timeout.

        Returns:
            int: Timeout in seconds
        """
        config = self._ensure_config_loaded()
        if api_type:
            # Try to get API-specific timeout first
            api_timeouts = config.get("api", {}).get("timeouts", {})
            if api_type.lower() in api_timeouts:
                return api_timeouts[api_type.lower()]  # type: ignore[no-any-return]

        # Fall back to default timeout
        return config["api"]["timeout"]  # type: ignore[no-any-return]

    def get_data_point_limit(self) -> int:
        """Get data point limit"""
        config = self._ensure_config_loaded()
        return config["system"]["data_point_limit"]  # type: ignore[no-any-return]

    def get_week_definition(self) -> str:
        """Get week definition setting"""
        config = self._ensure_config_loaded()
        return config["reporting"]["week_definition"]  # type: ignore[no-any-return]

    def get_custom_start_day(self) -> Optional[int]:
        """Get custom start day (if week_definition is 'custom')"""
        config = self._ensure_config_loaded()
        return config["reporting"].get("custom_start_day")  # type: ignore[no-any-return]

    def get_week_start_offset(self) -> int:
        """
        Get the day offset for week start calculation

        Returns:
            int: Days to offset from Sunday (0) to get the desired week start
                 0 = Sunday, 1 = Monday, etc.
        """
        _ = self._ensure_config_loaded()  # Ensure config is loaded
        week_def = self.get_week_definition()

        if week_def == "sunday_to_saturday":
            return 0  # Week starts on Sunday
        elif week_def == "monday_to_sunday":
            return 1  # Week starts on Monday
        elif week_def == "monday_to_friday":
            return 1  # Week starts on Monday (5-day week)
        elif week_def == "custom":
            custom_day = self.get_custom_start_day()
            if custom_day is None:
                raise ConfigurationError("custom week requires custom_start_day")
            return custom_day
        else:
            raise ConfigurationError(f"未支援的週期定義: {week_def}")

    def get_week_duration_days(self) -> int:
        """
        Get the duration of the week in days

        Returns:
            int: Number of days in the reporting week
        """
        _ = self._ensure_config_loaded()  # Ensure config is loaded
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
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("api", {})
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
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("api", {})
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
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("api", {}).get("retry_delays", {}).get("rate_limit_delay", 0.5)
        )

    def get_max_workers(self) -> int:
        """
        Get maximum number of concurrent workers for parallel API requests.

        Returns:
            int: Maximum concurrent workers. Defaults to 3 if not configured.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {}).get("concurrency", {}).get("max_workers", 3)
        )

    def get_pool_connections(self) -> int:
        """
        Get number of HTTP connection pools to cache.

        Returns:
            int: Pool connections. Defaults to 10 if not configured.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {}).get("concurrency", {}).get("pool_connections", 10)
        )

    def get_pool_maxsize(self) -> int:
        """
        Get maximum number of connections per pool.

        Returns:
            int: Pool maxsize. Defaults to 20 if not configured.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {}).get("concurrency", {}).get("pool_maxsize", 20)
        )

    def get_circuit_breaker_failure_threshold(self) -> int:
        """
        Get circuit breaker failure threshold.

        Returns:
            int: Number of failures before opening circuit. Defaults to 3.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {})
            .get("circuit_breaker", {})
            .get("failure_threshold", 3)
        )

    def get_circuit_breaker_recovery_timeout(self) -> int:
        """
        Get circuit breaker recovery timeout.

        Returns:
            int: Seconds before attempting recovery. Defaults to 30.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {})
            .get("circuit_breaker", {})
            .get("recovery_timeout", 30)
        )

    def get_circuit_breaker_success_threshold(self) -> int:
        """
        Get circuit breaker success threshold.

        Returns:
            int: Successes needed to close circuit from half-open. Defaults to 2.
        """
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("system", {})
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
        config = self._ensure_config_loaded()
        return (  # type: ignore[no-any-return]
            config.get("api", {})
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
        config = self._ensure_config_loaded()
        return config.get("api", {}).get("edgerc_section", "default")  # type: ignore[no-any-return]

    def get_auth_source(self) -> str:
        """
        Get authentication source.

        Returns:
            str: Authentication source ('edgerc', 'env', or 'aws').
                 Defaults to 'edgerc' if not configured.
        """
        config = self._ensure_config_loaded()
        return config.get("authentication", {}).get("source", "edgerc")  # type: ignore[no-any-return]

    def get_edgerc_path(self) -> Optional[str]:
        """
        Get custom .edgerc file path.

        Returns:
            Optional[str]: Custom path to .edgerc file, or None to use default (~/.edgerc)
        """
        config = self._ensure_config_loaded()
        return config.get("authentication", {}).get("edgerc_path")  # type: ignore[no-any-return]

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
