"""
Concurrent API Client Implementation

This module provides concurrent API request execution with rate limiting
and controlled parallelism to improve performance while respecting API limits.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

from tools.lib.logger import logger


class ConcurrentAPIClient:
    """
    Concurrent API client with rate limiting.

    Executes multiple API requests concurrently using thread pool
    while controlling the rate of requests to respect API limits.

    Args:
        max_workers: Maximum number of concurrent requests (default: 5)
        rate_limit_delay: Delay between request submissions in seconds (default: 0.1)
    """

    def __init__(self, max_workers: int = 5, rate_limit_delay: float = 0.1):
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

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
        Shutdown the thread pool executor.

        Args:
            wait: If True, wait for all threads to complete (default: True)
        """
        self.executor.shutdown(wait=wait)
