#!/usr/bin/env python3
"""
Weekly Traffic Report Script for Akamai CDN

This script automatically generates weekly traffic reports using Akamai V2 APIs.
It supports both automatic (last week) and manual time range specification.

Author: Development Team
Version: 2.0 (Refactored)
Date: 2025-10-02
"""

import argparse
from datetime import datetime

from tools.lib.api_client import (
    get_all_regional_traffic,
    get_all_service_traffic,
    get_total_edge_traffic,
)
from tools.lib.container import ServiceContainer
from tools.lib.exceptions import (
    AkamaiAPIError,
    APIAuthenticationError,
    APIRateLimitError,
    APITimeoutError,
    CircuitBreakerOpenError,
)
from tools.lib.logger import logger
from tools.lib.reporters import (
    generate_weekly_report,
    print_summary_stats,
    save_report_data,
)
from tools.lib.time_handler import get_time_range


def validate_date_format(date_str: str) -> str:
    """
    Validate and sanitize date input.

    Accepts YYYY-MM-DD or ISO-8601 format and returns ISO-8601 with time.

    Args:
        date_str: Date string to validate

    Returns:
        ISO-8601 formatted datetime string (YYYY-MM-DDTHH:MM:SSZ)

    Raises:
        argparse.ArgumentTypeError: If date format is invalid

    Examples:
        >>> validate_date_format("2025-01-01")
        '2025-01-01T00:00:00Z'
        >>> validate_date_format("2025-01-01T12:00:00Z")
        '2025-01-01T12:00:00Z'
    """
    try:
        # Try parsing as ISO-8601 first
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            # Parse YYYY-MM-DD format and set time to 00:00:00
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        # Return in consistent ISO-8601 format
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. "
            f"Expected YYYY-MM-DD or ISO-8601 format (e.g., 2025-01-01 or 2025-01-01T00:00:00Z)"
        ) from e


def main(container: ServiceContainer = None) -> int:
    """
    Main function to orchestrate the weekly traffic report generation.

    Args:
        container: Optional dependency injection container for testing

    Returns:
        Exit code (0 for success, 1 for failure)
    """

    logger.info("🚀 週報流量數據腳本啟動")
    logger.info("=" * 50)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate weekly Akamai traffic report",
        epilog="Example: python traffic.py --start 2025-01-01 --end 2025-01-07",
    )
    parser.add_argument(
        "--start",
        help="Start date (YYYY-MM-DD or ISO-8601 format)",
        type=validate_date_format,
        metavar="DATE",
    )
    parser.add_argument(
        "--end",
        help="End date (YYYY-MM-DD or ISO-8601 format)",
        type=validate_date_format,
        metavar="DATE",
    )

    args = parser.parse_args()

    try:
        # Initialize service container
        if container is None:
            container = ServiceContainer()

        # Get dependencies from container
        logger.info("📋 載入配置檔案...")
        config_loader = container.config_loader
        config_loader.print_config_summary()

        # Get authentication from container
        auth = container.auth

        # Get time range
        start_date, end_date = get_time_range(args, config_loader)

        logger.info("\n📊 開始生成週報...")
        logger.info(f"   時間範圍: {start_date} ~ {end_date}")

        # Query V2 Traffic API
        logger.info(f"\n{'=' * 60}")
        logger.info("🔍 V2 Traffic API 數據查詢")
        logger.info(f"{'=' * 60}")

        # Get total edge traffic
        total_traffic = get_total_edge_traffic(
            start_date, end_date, auth, config_loader
        )
        if not total_traffic["success"]:
            logger.error(
                f"❌ 無法取得總體流量數據: {total_traffic.get('error', '未知錯誤')}"
            )
            return 1

        # Get individual service traffic
        service_traffic = get_all_service_traffic(
            start_date, end_date, auth, config_loader
        )

        # Query V2 Emissions API for regional data
        logger.info(f"\n{'=' * 60}")
        logger.info("🌏 V2 Emissions API 數據查詢")
        logger.info(f"{'=' * 60}")

        regional_traffic = get_all_regional_traffic(
            start_date, end_date, auth, config_loader
        )

        # Generate and display formatted report
        logger.info(f"\n{'=' * 60}")
        logger.info("📋 生成週報")
        logger.info(f"{'=' * 60}")

        report_content = generate_weekly_report(
            start_date,
            end_date,
            total_traffic,
            service_traffic,
            regional_traffic,
            config_loader,
        )

        # Display the complete report
        logger.info("\n" + report_content)

        # Display quick summary for console reference
        print_summary_stats(total_traffic, service_traffic, regional_traffic)

        # Optionally save report data to JSON file
        saved_file = save_report_data(
            start_date,
            end_date,
            total_traffic,
            service_traffic,
            regional_traffic,
            config_loader,
        )

        logger.info("\n✅ 週報生成完成!")
        if saved_file:
            logger.info(f"   數據檔案: {saved_file}")

        # Final validation
        total_api_calls = (
            1
            + sum(1 for s in service_traffic.values() if s.get("success"))
            + regional_traffic.get("_summary", {}).get("successful_queries", 0)
        )
        logger.info(f"   API 調用: {total_api_calls} 次")
        logger.info("   執行狀態: 成功")

    except APIAuthenticationError as e:
        logger.error(f"\n❌ 認證失敗: {e}")
        logger.error("   請檢查您的 .edgerc 檔案和認證設定")
        return 1

    except APIRateLimitError as e:
        logger.error(f"\n❌ API 速率限制: {e}")
        logger.error("   請稍後再試，或聯繫管理員調整速率限制")
        return 1

    except APITimeoutError as e:
        logger.error(f"\n❌ 請求超時: {e}")
        logger.error("   請檢查網路連線或稍後再試")
        return 1

    except CircuitBreakerOpenError as e:
        logger.error(f"\n❌ 電路斷路器開啟: {e}")
        logger.error("   API 服務異常,系統已進入保護模式")
        logger.error(f"   請等待 {e.time_until_retry:.0f} 秒後重試")
        return 1

    except AkamaiAPIError as e:
        logger.error(f"\n❌ Akamai API 錯誤: {e}")
        logger.error("   請查看詳細錯誤訊息並聯繫技術支援")
        return 1

    except Exception as e:
        logger.error(f"\n❌ 執行失敗: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
