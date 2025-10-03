"""
HTTP client utilities for Akamai Traffic Report System

This package provides HTTP client abstractions and concurrent request handling.
"""

from tools.lib.http.concurrent_client import ConcurrentAPIClient


__all__ = ["ConcurrentAPIClient"]
