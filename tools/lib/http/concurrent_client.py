"""
Concurrent API Client Implementation

This module provides concurrent API request execution with rate limiting
and controlled parallelism to improve performance while respecting API limits.
Includes connection pooling for efficient network resource usage.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

import requests
from requests.adapters import HTTPAdapter

from tools.lib.logger import logger


class ConcurrentAPIClient:
    """
    Concurrent API client with connection pooling and rate limiting.

    Executes multiple API requests concurrently using thread pool
    while controlling the rate of requests to respect API limits.
    Uses requests.Session with connection pooling for efficient network usage.

    Args:
        max_workers: Maximum number of concurrent requests (default: 3)
        rate_limit_delay: Delay between request submissions in seconds (default: 0.1)
        pool_connections: Number of connection pools to cache (default: 10)
        pool_maxsize: Maximum number of connections to save in pool (default: 20)
    """

    def __init__(
        self,
        max_workers: int = 3,
        rate_limit_delay: float = 0.1,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
    ):
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Create session with connection pooling
        self.session = requests.Session()

        # Configure HTTPAdapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=0,  # Retries handled by api_client layer
        )

        # Mount adapter for both HTTP and HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.debug(
            f"Connection pool initialized: {pool_connections} pools, "
            f"max {pool_maxsize} connections per pool"
        )

    def execute_batch(
        self, func: Callable, items: List[Any], **common_kwargs
    ) -> Dict[Any, Dict[str, Any]]:
        """
        Execute function concurrently for multiple items.

        Args:
            func: Function to execute for each item
            items: List of items to process
            **common_kwargs: Common keyword arguments passed to all function calls

        Returns:
            Dictionary mapping items to their results
        """
        if not items:
            return {}

        logger.info(
            f"🚀 Starting concurrent execution for {len(items)} items "
            f"(max {self.max_workers} workers)"
        )

        futures = []
        for item in items:
            future = self.executor.submit(func, item, **common_kwargs)
            futures.append((item, future))
            time.sleep(self.rate_limit_delay)  # Stagger requests

        results = {}
        completed_count = 0
        failed_count = 0

        for item, future in futures:
            try:
                result = future.result(timeout=120)
                results[item] = result
                completed_count += 1
                logger.debug(f"✅ Completed: {item} ({completed_count}/{len(items)})")
            except Exception as e:
                logger.error(f"❌ Failed for {item}: {e}")
                results[item] = {"success": False, "error": str(e)}
                failed_count += 1

        logger.info(
            f"✅ Concurrent execution completed: "
            f"{completed_count} success, {failed_count} failed"
        )

        return results

    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool executor and close session.

        Args:
            wait: If True, wait for all threads to complete (default: True)
        """
        self.executor.shutdown(wait=wait)
        self.session.close()
        logger.debug("Connection pool and thread executor shut down")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically cleanup"""
        self.shutdown()

    def get_session(self) -> requests.Session:
        """
        Get the underlying requests session for direct use.

        Returns:
            requests.Session with connection pooling configured
        """
        return self.session
