#!/usr/bin/env python3
"""
Time Handling Module

Provides functions for time range calculation and date parsing.
"""

from datetime import datetime, timedelta
from typing import Tuple

from tools.lib.config_loader import ConfigLoader


def get_last_week_range(
    week_start_offset: int = 0, week_duration_days: int = 7
) -> Tuple[str, str]:
    """
    Calculate last week's date range based on configurable week definition
    All times are in UTC+0.

    Args:
        week_start_offset (int): Day offset for week start (0=Sunday, 1=Monday, etc.)
        week_duration_days (int): Duration of week in days (default: 7, can be 5 for work week)

    Examples:
        - week_start_offset=0, week_duration_days=7: Sunday to Saturday (default)
        - week_start_offset=1, week_duration_days=7: Monday to Sunday
        - week_start_offset=1, week_duration_days=5: Monday to Friday (work week)

    Returns:
        tuple: (start_date, end_date) in ISO-8601 format UTC+0
    """
    # Use UTC+0 for all calculations
    today = datetime.utcnow()

    # Calculate days since the desired week start day
    # today.weekday(): Monday=0, Tuesday=1, ..., Sunday=6
    # Convert to our offset system: week_start_offset=0 means Sunday is day 0
    current_day_offset = (today.weekday() + 1) % 7  # Convert to Sunday=0 system

    # Calculate days since the configured week start
    days_since_week_start = (current_day_offset - week_start_offset) % 7

    # Go back to this week's start day
    this_week_start = today - timedelta(days=days_since_week_start)

    # Go back one full week to get last week's start
    last_week_start = this_week_start - timedelta(days=7)
    last_week_start = last_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate last week end (duration_days - 1 days after start)
    last_week_end = last_week_start + timedelta(days=week_duration_days - 1)
    last_week_end = last_week_end.replace(hour=23, minute=59, second=59, microsecond=0)

    start_date = last_week_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = last_week_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    return start_date, end_date


def get_last_week_range_with_config(config_loader: ConfigLoader) -> Tuple[str, str]:
    """
    Calculate last week's date range using configuration settings

    Args:
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        tuple: (start_date, end_date) in ISO-8601 format UTC+0
    """
    week_start_offset = config_loader.get_week_start_offset()
    week_duration_days = config_loader.get_week_duration_days()

    return get_last_week_range(week_start_offset, week_duration_days)


def parse_date_string(date_string: str, end_of_day: bool = False) -> str:
    """
    Parse date string in YYYY-MM-DD format to ISO-8601 UTC+0 format

    Args:
        date_string (str): Date in YYYY-MM-DD format
        end_of_day (bool): If True, return end of day (23:59:59), else start of day (00:00:00)

    Returns:
        str: ISO-8601 formatted datetime string in UTC+0
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        if end_of_day:
            date_obj = date_obj.replace(hour=23, minute=59, second=59)
        else:
            date_obj = date_obj.replace(hour=0, minute=0, second=0)
        return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")


def validate_time_range(start_date: str, end_date: str) -> bool:
    """
    Validate that the time range is logical

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format

    Returns:
        bool: True if valid

    Raises:
        ValueError: If time range is invalid
    """
    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    if start >= end:
        raise ValueError("Start date must be before end date")

    # Check if range is too large (more than 90 days)
    if (end - start).days > 90:
        raise ValueError("Time range cannot exceed 90 days")

    return True


def get_time_range(args, config_loader: ConfigLoader) -> Tuple[str, str]:
    """
    Get time range based on arguments (automatic or manual)
    All times are in UTC+0

    Args:
        args: Parsed command line arguments
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        tuple: (start_date, end_date) in ISO-8601 format UTC+0
    """
    if args.start and args.end:
        # Manual mode - use UTC+0
        start_date = parse_date_string(args.start, end_of_day=False)  # 00:00:00 UTC+0
        end_date = parse_date_string(args.end, end_of_day=True)  # 23:59:59 UTC+0

        validate_time_range(start_date, end_date)
        print(f"📅 使用手動指定時間範圍: {args.start} 00:00 ~ {args.end} 23:59 (UTC+0)")

    else:
        # Automatic mode - calculate last week based on configuration
        start_date, end_date = get_last_week_range_with_config(config_loader)
        start_display = start_date[:10]  # Extract YYYY-MM-DD part
        end_display = end_date[:10]

        # Display week definition info
        week_def = config_loader.get_week_definition()
        week_desc_map = {
            "sunday_to_saturday": "週日到週六",
            "monday_to_sunday": "週一到週日",
            "monday_to_friday": "週一到週五",
            "custom": f"自定義 (起始日: {config_loader.get_custom_start_day()})",
        }
        week_desc = week_desc_map.get(week_def, week_def)
        print(
            f"📅 自動計算上週時間範圍: {start_display} 00:00 ~ {end_display} 23:59 (UTC+0)"
        )
        print(f"   週期定義: {week_desc}")

    return start_date, end_date
