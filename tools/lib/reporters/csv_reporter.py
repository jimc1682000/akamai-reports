#!/usr/bin/env python3
"""
CSV Reporter Module - 可重用的 CSV 報告生成工具

提供標準化的 CSV 報告生成功能，可用於各種流量數據導出需求。
"""

import csv
from datetime import datetime


class CSVReporter:
    """CSV 報告生成器"""

    @staticmethod
    def generate_timestamp():
        """生成時間戳記用於檔案命名"""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def write_summary_csv(filename, data, regions):
        """
        生成摘要比較 CSV

        Args:
            filename (str): 輸出檔案名
            data (dict): 包含各地區數據的字典
            regions (dict): 地區代碼到名稱的映射
        """
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Country Code",
                    "Country Name",
                    "API Version",
                    "Total Bytes",
                    "Total TB",
                    "Total Hits",
                    "Data Points",
                    "Avg Bytes per Hit",
                ]
            )

            for country_code, country_data in data.items():
                country_name = regions.get(country_code, country_code)

                # V1 row
                if country_data.get("v1", {}).get("success"):
                    v1 = country_data["v1"]
                    v1_tb = round(v1["total_bytes"] / (1024**4), 4)
                    v1_avg = (
                        v1["total_bytes"] / v1["total_hits"]
                        if v1["total_hits"] > 0
                        else 0
                    )

                    writer.writerow(
                        [
                            country_code,
                            country_name,
                            "V1",
                            v1["total_bytes"],
                            v1_tb,
                            v1["total_hits"],
                            v1["data_points"],
                            f"{v1_avg:.0f}",
                        ]
                    )

                # V2 row
                if country_data.get("v2", {}).get("success"):
                    v2 = country_data["v2"]
                    v2_tb = round(v2["total_bytes"] / (1024**4), 4)
                    v2_avg = (
                        v2["total_bytes"] / v2["total_hits"]
                        if v2["total_hits"] > 0
                        else 0
                    )

                    writer.writerow(
                        [
                            country_code,
                            country_name,
                            "V2",
                            v2["total_bytes"],
                            v2_tb,
                            v2["total_hits"],
                            v2["data_points"],
                            f"{v2_avg:.0f}",
                        ]
                    )

                # Comparison row
                if country_data.get("v1", {}).get("success") and country_data.get(
                    "v2", {}
                ).get("success"):
                    v1 = country_data["v1"]
                    v2 = country_data["v2"]

                    bytes_ratio = (
                        v2["total_bytes"] / v1["total_bytes"]
                        if v1["total_bytes"] > 0
                        else 0
                    )
                    hits_ratio = (
                        v2["total_hits"] / v1["total_hits"]
                        if v1["total_hits"] > 0
                        else 0
                    )

                    writer.writerow(
                        [
                            country_code,
                            country_name,
                            "V2/V1 Ratio",
                            f"{bytes_ratio:.2f}x",
                            "",
                            f"{hits_ratio:.2f}x",
                            "",
                            "",
                        ]
                    )

                # Empty row for separation
                writer.writerow([])

    @staticmethod
    def write_daily_breakdown_csv(filename, data, all_dates, regions, api_version):
        """
        生成每日數據明細 CSV

        Args:
            filename (str): 輸出檔案名
            data (dict): 包含各地區數據的字典
            all_dates (list): 所有日期列表
            regions (dict): 地區代碼到名稱的映射
            api_version (str): "v1" 或 "v2"
        """
        region_codes = list(regions.keys())

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            header = ["Date"]
            for code in region_codes:
                header.extend([f"{code}_Bytes", f"{code}_TB", f"{code}_Hits"])
            writer.writerow(header)

            # Data rows
            for date in all_dates:
                row = [date]

                for country_code in region_codes:
                    country_data = data.get(country_code, {})
                    version_data = country_data.get(api_version, {})

                    if version_data.get("success") and "daily_data" in version_data:
                        daily = version_data["daily_data"].get(
                            date, {"bytes": 0, "hits": 0}
                        )
                        bytes_val = daily["bytes"]
                        hits_val = daily["hits"]
                        tb_val = round(bytes_val / (1024**4), 4)

                        row.extend([bytes_val, tb_val, hits_val])
                    else:
                        row.extend([0, 0, 0])

                writer.writerow(row)

    @staticmethod
    def write_daily_comparison_csv(filename, data, all_dates, regions):
        """
        生成每日 V1 vs V2 對比 CSV

        Args:
            filename (str): 輸出檔案名
            data (dict): 包含各地區數據的字典
            all_dates (list): 所有日期列表
            regions (dict): 地區代碼到名稱的映射
        """
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Date",
                    "Country",
                    "V1_Bytes",
                    "V1_TB",
                    "V1_Hits",
                    "V2_Bytes",
                    "V2_TB",
                    "V2_Hits",
                    "Diff_Bytes",
                    "Diff_TB",
                    "Ratio",
                ]
            )

            # Data rows
            for date in all_dates:
                for country_code in regions.keys():
                    country_data = data.get(country_code, {})

                    v1 = country_data.get("v1", {})
                    v2 = country_data.get("v2", {})

                    v1_daily = {}
                    v2_daily = {}

                    if v1.get("success") and "daily_data" in v1:
                        v1_daily = v1["daily_data"].get(date, {"bytes": 0, "hits": 0})

                    if v2.get("success") and "daily_data" in v2:
                        v2_daily = v2["daily_data"].get(date, {"bytes": 0, "hits": 0})

                    v1_bytes = v1_daily.get("bytes", 0)
                    v1_hits = v1_daily.get("hits", 0)
                    v1_tb = round(v1_bytes / (1024**4), 4)

                    v2_bytes = v2_daily.get("bytes", 0)
                    v2_hits = v2_daily.get("hits", 0)
                    v2_tb = round(v2_bytes / (1024**4), 4)

                    diff_bytes = v2_bytes - v1_bytes
                    diff_tb = round((v2_bytes - v1_bytes) / (1024**4), 4)
                    ratio = v2_bytes / v1_bytes if v1_bytes > 0 else 0

                    writer.writerow(
                        [
                            date,
                            country_code,
                            v1_bytes,
                            v1_tb,
                            v1_hits,
                            v2_bytes,
                            v2_tb,
                            v2_hits,
                            diff_bytes,
                            f"{diff_tb:+.4f}",
                            f"{ratio:.2f}x",
                        ]
                    )

    @staticmethod
    def write_detailed_comparison_csv(filename, data, regions, period_info):
        """
        生成詳細比較分析 CSV

        Args:
            filename (str): 輸出檔案名
            data (dict): 包含各地區數據的字典
            regions (dict): 地區代碼到名稱的映射
            period_info (dict): 期間資訊 (start, end, description, cp_codes_count, etc.)
        """
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Metadata header
            writer.writerow(["Akamai V1 vs V2 API Comparison Report"])
            writer.writerow(["Report Period:", period_info.get("description", "")])
            writer.writerow(
                ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")]
            )
            writer.writerow(
                ["CP Codes:", f"{period_info.get('cp_codes_count', 0)} codes"]
            )
            writer.writerow([])

            # API information
            writer.writerow(
                [
                    "V1 API:",
                    "enhancedtraffic-by-country (will be decommissioned 2026-02-05)",
                ]
            )
            writer.writerow(["V2 API:", "delivery/traffic/emissions"])
            writer.writerow([])

            # Main data table
            writer.writerow(
                [
                    "Country",
                    "Metric",
                    "V1 Value",
                    "V2 Value",
                    "Difference",
                    "Ratio (V2/V1)",
                    "Notes",
                ]
            )

            for country_code, country_data in data.items():
                country_name = regions.get(country_code, country_code)
                v1 = country_data.get("v1", {})
                v2 = country_data.get("v2", {})

                if v1.get("success") and v2.get("success"):
                    # Bytes comparison
                    v1_bytes = v1["total_bytes"]
                    v2_bytes = v2["total_bytes"]
                    diff_bytes = v2_bytes - v1_bytes
                    ratio_bytes = v2_bytes / v1_bytes if v1_bytes > 0 else float("inf")

                    writer.writerow(
                        [
                            country_name,
                            "Total Bytes",
                            v1_bytes,
                            v2_bytes,
                            diff_bytes,
                            f"{ratio_bytes:.2f}x",
                            "Anomaly"
                            if ratio_bytes > 100 or ratio_bytes < 0.5
                            else "Normal",
                        ]
                    )

                    # TB comparison
                    v1_tb = round(v1_bytes / (1024**4), 4)
                    v2_tb = round(v2_bytes / (1024**4), 4)
                    diff_tb = round((v2_bytes - v1_bytes) / (1024**4), 4)

                    writer.writerow(
                        [
                            country_name,
                            "Total TB",
                            v1_tb,
                            v2_tb,
                            f"{diff_tb:+.4f}",
                            f"{ratio_bytes:.2f}x",
                            "",
                        ]
                    )

                    # Hits comparison
                    v1_hits = v1["total_hits"]
                    v2_hits = v2["total_hits"]
                    diff_hits = v2_hits - v1_hits
                    ratio_hits = v2_hits / v1_hits if v1_hits > 0 else float("inf")

                    writer.writerow(
                        [
                            country_name,
                            "Total Hits",
                            v1_hits,
                            v2_hits,
                            diff_hits,
                            f"{ratio_hits:.2f}x",
                            "",
                        ]
                    )

                    # Avg bytes per hit
                    v1_avg = v1_bytes / v1_hits if v1_hits > 0 else 0
                    v2_avg = v2_bytes / v2_hits if v2_hits > 0 else 0
                    diff_avg = v2_avg - v1_avg

                    writer.writerow(
                        [
                            country_name,
                            "Avg Bytes/Hit",
                            f"{v1_avg:.0f}",
                            f"{v2_avg:.0f}",
                            f"{diff_avg:+.0f}",
                            f"{(v2_avg / v1_avg):.2f}x" if v1_avg > 0 else "N/A",
                            "Similar" if abs(diff_avg) < 50000 else "Different",
                        ]
                    )

                    writer.writerow([])  # Separator
