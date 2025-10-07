"""
Response Cache Implementation

This module provides file-based response caching with TTL for API responses.
Useful for development and testing to avoid unnecessary API calls.
Uses JSON serialization for security and performance.
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional


class ResponseCache:
    """
    File-based response cache for API calls with TTL support.

    Caches API responses to disk with configurable time-to-live (TTL).
    Useful for development iterations and testing without hitting rate limits.

    Attributes:
        cache_dir: Directory for cache files
        ttl: Time-to-live for cached responses in seconds
    """

    def __init__(self, cache_dir: str = ".cache", ttl_seconds: int = 3600):
        """
        Initialize response cache.

        Args:
            cache_dir: Directory to store cache files (default: ".cache")
            ttl_seconds: Cache TTL in seconds (default: 3600 = 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(seconds=ttl_seconds)

    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        """
        Generate cache key from function name and arguments.

        Args:
            func_name: Name of the cached function
            **kwargs: Function arguments

        Returns:
            SHA256 hash of the cache key
        """
        key_data = {"func": func_name, "args": kwargs}
        # Sort keys for consistent hashing
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_json.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached response if not expired.

        Args:
            key: Cache key

        Returns:
            Cached response or None if expired/not found
        """
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # Load cached data with TTL
        try:
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check expiration using stored TTL timestamp
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.now() >= expires_at:
                # Cache expired, delete it
                cache_file.unlink()
                return None

            return cache_data["value"]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache file, delete it
            cache_file.unlink()
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store response in cache with TTL timestamp.

        Args:
            key: Cache key
            value: Response to cache
        """
        cache_file = self.cache_dir / f"{key}.json"
        expires_at = datetime.now() + self.ttl

        cache_data = {"value": value, "expires_at": expires_at.isoformat()}

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

    def cached_call(self, func: Callable, func_name: str, **kwargs) -> Any:
        """
        Execute function with caching.

        Args:
            func: Function to execute
            func_name: Function name for cache key
            **kwargs: Function arguments

        Returns:
            Function result (from cache or fresh call)
        """
        cache_key = self._get_cache_key(func_name, **kwargs)

        # Try to get from cache
        cached_result = self.get(cache_key)
        if cached_result is not None:
            from tools.lib.logger import logger

            logger.debug(f"Cache hit for {func_name}")
            return cached_result

        # Cache miss - execute function
        from tools.lib.logger import logger

        logger.debug(f"Cache miss for {func_name}")
        result = func(**kwargs)

        # Store in cache
        self.set(cache_key, result)
        return result

    def clear(self) -> int:
        """
        Clear all cached responses.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(self.cache_dir),
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "ttl_seconds": int(self.ttl.total_seconds()),
        }
