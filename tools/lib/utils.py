#!/usr/bin/env python3
"""
Utility Functions Module

Provides common utility functions for data conversion and formatting.
"""

from typing import Union


def bytes_to_tb(bytes_value: Union[int, float, str]) -> float:
    """
    Convert bytes to TB with 2 decimal places

    Args:
        bytes_value: Value in bytes (can be int, float, or string)

    Returns:
        float: Value in TB rounded to 2 decimal places
    """
    if isinstance(bytes_value, str):
        bytes_value = float(bytes_value)
    return round(bytes_value / (1024**4), 2)


def bytes_to_gb(bytes_value: Union[int, float, str]) -> float:
    """
    Convert bytes to GB with 2 decimal places

    Args:
        bytes_value: Value in bytes (can be int, float, or string)

    Returns:
        float: Value in GB rounded to 2 decimal places
    """
    if isinstance(bytes_value, str):
        bytes_value = float(bytes_value)
    return round(bytes_value / (1024**3), 2)


def format_number(number: Union[int, float, str], decimal_places: int = 2) -> str:
    """
    Format number with thousand separators and specified decimal places

    Args:
        number: Number to format (can be int, float, or string)
        decimal_places (int): Number of decimal places (default: 2)

    Returns:
        str: Formatted number string with thousand separators
    """
    if isinstance(number, str):
        number = float(number)
    return f"{number:,.{decimal_places}f}"
