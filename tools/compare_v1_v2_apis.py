#!/usr/bin/env python3
"""
Compare V1 and V2 API daily traffic for a specified date range
Generate CSV reports for Akamai support analysis
"""

import argparse
from datetime import datetime, timedelta

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from tools.lib.csv_reporter import CSVReporter

# Import from tools/lib/
from tools.lib.config_loader import load_configuration


def setup_authentication():
    """Initialize Akamai EdgeGrid authentication"""
    edgerc = EdgeRc("~/.edgerc")
    auth = EdgeGridAuth.from_edgerc(edgerc, "default")
    return auth


def get_v1_single_day(country_code, date_str, cp_codes, auth, config_loader):
    """
    Get V1 API data for a single day

    Args:
        country_code (str): Country code (ID, TW, SG)
        date_str (str): Date in YYYY-MM-DD format
        cp_codes (list): List of CP codes
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance

    Returns:
        dict: Result with bytes and hits for that day
    """
    v2_endpoint = config_loader.get_api_endpoints()["traffic"]
    base_url = "/".join(v2_endpoint.split("/")[:3])
    url = (
        base_url
        + "/reporting-api/v1/reports/enhancedtraffic-by-country/versions/1/report-data"
    )

    # V1 API requires start = day 00:00, end = next day 00:00
    start_dt = datetime.strptime(date_str, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)

    start_date = start_dt.strftime("%Y-%m-%dT00:00Z")
    end_date = end_dt.strftime("%Y-%m-%dT00:00Z")

    params = {
        "start": start_date,
        "end": end_date,
        "objectIds": ",".join(cp_codes),
        "metrics": "edgeBytes,edgeHits",
        "filters": f"country={country_code}",
    }

    try:
        response = requests.get(url, params=params, auth=auth, timeout=60)

        if response.status_code == 200:
            data = response.json()

            total_bytes = 0
            total_hits = 0

            for entry in data.get("data", []):
                bytes_val = entry.get("edgeBytes", 0)
                hits_val = entry.get("edgeHits", 0)

                if isinstance(bytes_val, str):
                    bytes_val = int(bytes_val)
                if isinstance(hits_val, str):
                    hits_val = int(hits_val)

                total_bytes += bytes_val
                total_hits += hits_val

            return {
                "success": True,
                "bytes": total_bytes,
                "hits": total_hits,
                "date": date_str,
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "date": date_str,
                "bytes": 0,
                "hits": 0,
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "date": date_str,
            "bytes": 0,
            "hits": 0,
        }


def get_v1_daily_data(country_code, all_dates, cp_codes, auth, config_loader):
    """
    Get V1 API data for each day in the date range

    Args:
        country_code (str): Country code
        all_dates (list): List of date strings in YYYY-MM-DD format
        cp_codes (list): List of CP codes
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance

    Returns:
        dict: Result with daily data
    """
    print(f"      Querying {len(all_dates)} days individually...")

    daily_data = {}
    total_bytes = 0
    total_hits = 0

    for i, date_str in enumerate(all_dates, 1):
        if i % 5 == 0:
            print(f"      Progress: {i}/{len(all_dates)} days...")

        result = get_v1_single_day(
            country_code, date_str, cp_codes, auth, config_loader
        )

        if result.get("success"):
            daily_data[date_str] = {"bytes": result["bytes"], "hits": result["hits"]}
            total_bytes += result["bytes"]
            total_hits += result["hits"]
        else:
            # Store 0 for failed queries
            daily_data[date_str] = {
                "bytes": 0,
                "hits": 0,
                "error": result.get("error", "Unknown error"),
            }

        # Small delay to avoid rate limiting
        import time

        time.sleep(0.2)

    return {
        "success": True,
        "total_bytes": total_bytes,
        "total_hits": total_hits,
        "daily_data": daily_data,
        "data_points": len(daily_data),
    }


def get_v2_daily_data(
    country_code, start_date, end_date, cp_codes, auth, config_loader
):
    """
    Get V2 Emissions API data with daily breakdown

    Args:
        country_code (str): Country code
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        cp_codes (list): List of CP codes
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance

    Returns:
        dict: Result with daily data
    """
    url = config_loader.get_api_endpoints()["emissions"]

    payload = {
        "dimensions": ["time1day", "country"],
        "metrics": ["edgeBytesSum", "edgeHitsSum"],
        "filters": [
            {
                "dimensionName": "cpcode",
                "operator": "IN_LIST",
                "expressions": cp_codes,
            },
            {
                "dimensionName": "country",
                "operator": "IN_LIST",
                "expressions": [country_code],
            },
        ],
        "sortBys": [{"name": "time1day", "sortOrder": "ASCENDING"}],
        "limit": 50000,
    }

    params = {"start": start_date, "end": end_date}

    try:
        response = requests.post(
            url, params=params, json=payload, auth=auth, timeout=60
        )

        if response.status_code == 200:
            data = response.json()

            # Parse daily data
            daily_data = {}
            for entry in data.get("data", []):
                timestamp = entry.get("time1day")
                bytes_val = entry.get("edgeBytesSum", 0)
                hits_val = entry.get("edgeHitsSum", 0)

                # Convert timestamp to date
                dt = datetime.fromtimestamp(timestamp)
                date_str = dt.strftime("%Y-%m-%d")

                daily_data[date_str] = {
                    "bytes": bytes_val,
                    "hits": hits_val,
                    "timestamp": timestamp,
                }

            total_bytes = sum(d["bytes"] for d in daily_data.values())
            total_hits = sum(d["hits"] for d in daily_data.values())

            return {
                "success": True,
                "total_bytes": total_bytes,
                "total_hits": total_hits,
                "daily_data": daily_data,
                "data_points": len(data.get("data", [])),
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_date_range(start_date_str, end_date_str):
    """
    Generate all dates in the specified range

    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format

    Returns:
        list: List of date strings in YYYY-MM-DD format
    """
    dates = []
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")

    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Compare Akamai V1 and V2 API traffic data for a specified date range"
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYY-MM-DD format (e.g., YYYY-MM-01)",
    )
    parser.add_argument(
        "--end", required=True, help="End date in YYYY-MM-DD format (e.g., YYYY-MM-30)"
    )
    return parser.parse_args()


def main():
    """Generate comparison report"""
    args = parse_arguments()

    # Validate date format
    try:
        start_dt = datetime.strptime(args.start, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError:
        print("❌ Error: Invalid date format. Use YYYY-MM-DD (e.g., YYYY-MM-01)")
        return 1

    if start_dt > end_dt:
        print("❌ Error: Start date must be before or equal to end date")
        return 1

    # Format dates for display
    period_desc = f"{args.start} to {args.end}"
    print(f"🔍 V1 vs V2 API Daily Comparison - {period_desc}")
    print("=" * 80)

    config_loader = load_configuration()
    auth = setup_authentication()
    cp_codes = config_loader.get_cp_codes()

    # Calculate date range for V2 API
    start_date_v2 = f"{args.start}T00:00:00Z"
    end_date_v2 = f"{args.end}T23:59:59Z"

    regions = config_loader.get_region_mappings()

    # Generate all dates in range
    all_dates = generate_date_range(args.start, args.end)

    # Collect all data
    all_data = {}

    for country_code, country_name in regions.items():
        print(f"\n📊 Querying {country_name} ({country_code})...")

        # Get V1 data (day by day)
        print("   → V1 API (querying each day individually)...")
        v1_result = get_v1_daily_data(
            country_code, all_dates, cp_codes, auth, config_loader
        )

        # Get V2 data (batch query with daily breakdown)
        print("   → V2 API (batch query)...")
        v2_result = get_v2_daily_data(
            country_code, start_date_v2, end_date_v2, cp_codes, auth, config_loader
        )

        all_data[country_code] = {
            "name": country_name,
            "v1": v1_result,
            "v2": v2_result,
        }

        if v1_result.get("success"):
            v1_tb = round(v1_result["total_bytes"] / (1024**4), 4)
            print(f"   ✅ V1: {v1_tb} TB ({v1_result['data_points']} data points)")
        else:
            print(f"   ❌ V1 Error: {v1_result.get('error')}")

        if v2_result.get("success"):
            v2_tb = round(v2_result["total_bytes"] / (1024**4), 4)
            print(f"   ✅ V2: {v2_tb} TB ({v2_result['data_points']} data points)")
        else:
            print(f"   ❌ V2 Error: {v2_result.get('error')}")

    # Generate CSV files using CSVReporter
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Prepare period info for detailed CSV
    period_info = {
        "description": period_desc,
        "start": args.start,
        "end": args.end,
        "cp_codes_count": len(cp_codes),
    }

    # CSV 1: Summary comparison
    summary_csv = f"v1_v2_comparison_summary_{timestamp}.csv"
    print(f"\n📄 Generating summary CSV: {summary_csv}")
    CSVReporter.write_summary_csv(summary_csv, all_data, regions)

    # CSV 2: V1 Daily breakdown
    v1_daily_csv = f"v1_daily_breakdown_{args.start}_{args.end}_{timestamp}.csv"
    print(f"📄 Generating V1 daily breakdown CSV: {v1_daily_csv}")
    CSVReporter.write_daily_breakdown_csv(
        v1_daily_csv, all_data, all_dates, regions, "v1"
    )

    # CSV 3: V2 Daily breakdown
    v2_daily_csv = f"v2_daily_breakdown_{args.start}_{args.end}_{timestamp}.csv"
    print(f"📄 Generating V2 daily breakdown CSV: {v2_daily_csv}")
    CSVReporter.write_daily_breakdown_csv(
        v2_daily_csv, all_data, all_dates, regions, "v2"
    )

    # CSV 4: Daily V1 vs V2 Comparison
    daily_comparison_csv = f"daily_v1_v2_comparison_{timestamp}.csv"
    print(f"📄 Generating daily V1 vs V2 comparison CSV: {daily_comparison_csv}")
    CSVReporter.write_daily_comparison_csv(
        daily_comparison_csv, all_data, all_dates, regions
    )

    # CSV 5: Detailed comparison with metadata
    detail_csv = f"v1_v2_detailed_comparison_{timestamp}.csv"
    print(f"📄 Generating detailed comparison CSV: {detail_csv}")
    CSVReporter.write_detailed_comparison_csv(
        detail_csv, all_data, regions, period_info
    )

    print(f"\n{'=' * 80}")
    print("✅ Report Generation Complete!")
    print(f"{'=' * 80}")
    print("\n生成的檔案:")
    print(f"  1. {summary_csv} - 簡要摘要比較")
    print(f"  2. {v1_daily_csv} - V1 API 每日數據明細")
    print(f"  3. {v2_daily_csv} - V2 API 每日數據明細")
    print(f"  4. {daily_comparison_csv} - 每日 V1 vs V2 逐日對比")
    print(f"  5. {detail_csv} - 詳細比較與分析")

    print("\n📧 聯繫 Akamai Support 時請提供:")
    print("  • 所有 5 個 CSV 檔案")
    print(f"  • 重點檔案: {daily_comparison_csv}")
    print("  • 說明問題: 特定地區 V2/V1 ratio 異常")
    print("  • 詢問: V1 和 V2 API 的數據計算邏輯差異")
    print("  • 詢問: 是否為 GeoIP 數據庫版本差異")
    print(
        f"\n⏱️  提示: V1 API 需要逐日查詢 ({len(all_dates)} days × {len(regions)} regions = {len(all_dates) * len(regions)} API calls)"
    )
    print("   腳本已加入延遲避免 rate limiting")

    return 0


if __name__ == "__main__":
    exit(main())
