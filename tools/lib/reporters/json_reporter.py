#!/usr/bin/env python3
"""
JSON Reporter Module

This module provides functions to save traffic report data to JSON files
for future analysis and record keeping.

Functions:
    - save_report_data(): Save report data to timestamped JSON file
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from tools.lib.config_loader import ConfigLoader
from tools.lib.logger import logger


def save_report_data(
    start_date: str,
    end_date: str,
    total_traffic: Dict[str, Any],
    service_traffic: Dict[str, Dict[str, Any]],
    regional_traffic: Dict[str, Any],
    config_loader: ConfigLoader,
) -> Optional[str]:
    """
    Save raw report data to JSON file for future analysis (optional)

    Args:
        start_date (str): Start date
        end_date (str): End date
        total_traffic (dict): Total traffic data
        service_traffic (dict): Service traffic data
        regional_traffic (dict): Regional traffic data
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        str: Filename if saved successfully, None otherwise
    """
    try:
        # Create summary data without raw API responses (too large)
        summary_data = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "period_start": start_date,
                "period_end": end_date,
                "billing_coefficient": config_loader.get_billing_coefficient(),
            },
            "traffic_summary": {
                "total_edge_tb": total_traffic.get("total_tb", 0),
                "billing_estimate_tb": total_traffic.get("billing_estimate", 0),
                "data_points": total_traffic.get("data_points", 0),
            },
            "service_traffic": {
                cp_code: {
                    "name": result.get("name", f"CP {cp_code}"),
                    "traffic_value": result.get("traffic_value", 0),
                    "unit": result.get("unit", "TB"),
                    "success": result.get("success", False),
                }
                for cp_code, result in service_traffic.items()
            },
            "regional_traffic": {
                code: {
                    "region_name": regional_traffic[code].get("region_name", code),
                    "total_tb": regional_traffic[code].get("total_tb", 0),
                    "success": regional_traffic[code].get("success", False),
                }
                for code in regional_traffic
                if code != "_summary"  # Skip summary entry
            },
            "regional_summary": regional_traffic.get("_summary", {}),
        }

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"traffic_report_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 報告數據已保存至: {filename}")
        return filename

    except Exception as e:
        logger.warning(f"⚠️  保存報告數據失敗: {e}")
        return None
