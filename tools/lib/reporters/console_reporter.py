#!/usr/bin/env python3
"""
Console Reporter Module

This module provides functions to generate formatted console reports for
Akamai traffic data. It includes the main weekly report and quick summaries.

Functions:
    - generate_weekly_report(): Generate comprehensive weekly traffic report
    - print_summary_stats(): Print quick summary statistics
"""

from datetime import datetime
from typing import Any, Dict

from tools.lib.config_loader import ConfigLoader
from tools.lib.logger import logger
from tools.lib.utils import format_number


def generate_weekly_report(
    start_date: str,
    end_date: str,
    total_traffic: Dict[str, Any],
    service_traffic: Dict[str, Dict[str, Any]],
    regional_traffic: Dict[str, Any],
    config_loader: ConfigLoader,
) -> str:
    """
    Generate formatted weekly traffic report

    Args:
        start_date (str): Start date string
        end_date (str): End date string
        total_traffic (dict): Total traffic data from Traffic API
        service_traffic (dict): Service-specific traffic data
        regional_traffic (dict): Regional traffic data from Emissions API
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        str: Formatted report string
    """
    # Extract date parts for display
    start_display = start_date[:10]  # YYYY-MM-DD
    end_display = end_date[:10]

    # Calculate report period info
    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    period_days = (end_dt - start_dt).days + 1

    report_lines = []

    # Header
    report_lines.extend(
        [
            "=" * 80,
            f"📊 週報流量數據報告 ({start_display} ~ {end_display})",
            f"    報告期間: {period_days} 天 | 時區: UTC+0 | 生成時間: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "=" * 80,
        ]
    )

    # V2 Traffic API Section
    report_lines.extend(
        [
            "",
            "🔍 V2 Traffic API 數據 (time5minutes 維度):",
            f"   總 Edge 流量:              {format_number(total_traffic['total_tb'], 2):>8} TB",
            f"   └─ 預估計費用量:           {format_number(total_traffic['billing_estimate'], 2):>8} TB (×{config_loader.get_billing_coefficient()})",
            "",
        ]
    )

    # Individual Services Section
    report_lines.append("   個別服務流量:")
    successful_services = []
    failed_services = []

    for _cp_code, result in service_traffic.items():
        if result.get("success"):
            successful_services.append(result)
        else:
            failed_services.append(result)

    # Sort successful services by traffic value (descending)
    successful_services.sort(key=lambda x: x.get("traffic_value", 0), reverse=True)

    for service in successful_services:
        name = service["name"]
        value = format_number(service["traffic_value"], 2)
        unit = service["unit"]
        cp_code = service["cp_code"]
        report_lines.append(f"                   {name} ({cp_code}):{value:>10} {unit}")

    if failed_services:
        report_lines.append(f"   ⚠️  查詢失敗服務: {len(failed_services)} 個")

    # V2 Emissions API Section
    regional_summary = regional_traffic.get("_summary", {})
    report_lines.extend(["", "🌏 V2 Emissions API 數據 (time1day 維度):"])

    # Regional traffic breakdown
    regional_data = []
    for country_code, region_data_item in regional_traffic.items():
        if country_code != "_summary" and region_data_item.get("success"):
            regional_data.append(region_data_item)

    # Sort by traffic volume (descending)
    regional_data.sort(key=lambda x: x.get("total_tb", 0), reverse=True)

    for region in regional_data:
        region_name = region["region_name"]
        country_code = region["country_code"]
        total_tb = format_number(region["total_tb"], 2)
        report_lines.append(
            f"         {region_name} ({country_code}):{total_tb:>14} TB"
        )

    report_lines.extend(
        [
            f"   {'─' * 32}",
            f"   地區小計:                  {format_number(regional_summary.get('total_regional_traffic_tb', 0), 2):>8} TB",
        ]
    )

    # Data Summary Section
    total_coverage = 0
    if total_traffic["total_tb"] > 0:
        total_coverage = (
            regional_summary.get("total_regional_traffic_tb", 0)
            / total_traffic["total_tb"]
        ) * 100

    report_lines.extend(
        [
            "",
            "📈 數據摘要統計:",
            f"   Traffic API 數據點:         {total_traffic.get('data_points', 0):>4,}",
            f"   成功查詢服務:                   {len(successful_services)}/{len(service_traffic)}",
            f"   成功查詢地區:                   {regional_summary.get('successful_queries', 0)}/3",
            f"   地區流量覆蓋率:              {total_coverage:.1f}%",
            "",
        ]
    )

    # Billing and Business Intelligence
    report_lines.extend(
        [
            "💰 計費分析:",
            f"   API 總流量:                {format_number(total_traffic['total_tb'], 2):>8} TB",
            f"   預估實際計費:              {format_number(total_traffic['billing_estimate'], 2):>8} TB",
            f"   計費修正係數:               {config_loader.get_billing_coefficient()}",
            "",
        ]
    )

    # Performance Metrics
    api_calls = (
        1 + len(successful_services) + regional_summary.get("successful_queries", 0)
    )
    report_lines.extend(
        [
            "⚡ 系統效能指標:",
            f"   總 API 呼叫次數:               {api_calls}",
            f"   查詢成功率:                 {((len(successful_services) + regional_summary.get('successful_queries', 0)) / (len(service_traffic) + 3) * 100):.1f}%",
            "   數據時間粒度:        5分鐘 (Traffic) / 1天 (Emissions)",
            "",
        ]
    )

    # Footer
    report_lines.extend(
        [
            "=" * 80,
            f"📋 報告完成 | 數據來源: Akamai V2 APIs | 基於 {config_loader.get_billing_coefficient()} 計費係數分析",
            "=" * 80,
        ]
    )

    return "\n".join(report_lines)


def print_summary_stats(
    total_traffic: Dict[str, Any],
    service_traffic: Dict[str, Dict[str, Any]],
    regional_traffic: Dict[str, Any],
) -> None:
    """
    Print concise summary statistics for quick reference

    Args:
        total_traffic (dict): Total traffic data
        service_traffic (dict): Service traffic data
        regional_traffic (dict): Regional traffic data
    """
    logger.info("\n🎯 快速統計摘要:")
    logger.info(f"   📊 總 Edge 流量: {format_number(total_traffic['total_tb'])} TB")
    logger.info(
        f"   💰 預估計費: {format_number(total_traffic['billing_estimate'])} TB"
    )

    # Top service
    successful_services = [s for s in service_traffic.values() if s.get("success")]
    if successful_services:
        top_service = max(successful_services, key=lambda x: x.get("traffic_value", 0))
        logger.info(
            f"   🥇 最大服務: {top_service['name']} ({format_number(top_service['traffic_value'])} {top_service['unit']})"
        )

    # Top region
    regional_summary = regional_traffic.get("_summary", {})
    regional_data = [
        region_data
        for code, region_data in regional_traffic.items()
        if code != "_summary" and region_data.get("success")
    ]
    if regional_data:
        top_region = max(regional_data, key=lambda x: x.get("total_tb", 0))
        logger.info(
            f"   🌏 最大地區: {top_region['region_name']} ({format_number(top_region['total_tb'])} TB)"
        )

    # Coverage - Extract complex expression for better readability
    if total_traffic["total_tb"] > 0:
        regional_total = regional_summary.get("total_regional_traffic_tb", 0)
        total_tb = total_traffic["total_tb"]
        coverage = (regional_total / total_tb) * 100 if total_tb > 0 else 0.0
        logger.info(f"   📈 地區覆蓋率: {coverage:.1f}%")
