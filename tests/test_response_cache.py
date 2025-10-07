"""
Tests for Response Cache Module

Comprehensive test coverage for cache TTL, cached_call, and statistics functionality.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.lib.cache.response_cache import ResponseCache


class TestResponseCache:
    """Test suite for ResponseCache class"""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory"""
        return str(tmp_path / "test_cache")

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with 1 second TTL for testing"""
        return ResponseCache(cache_dir=temp_cache_dir, ttl_seconds=1)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache directory creation"""
        cache = ResponseCache(cache_dir=temp_cache_dir, ttl_seconds=3600)
        assert Path(temp_cache_dir).exists()
        assert cache.ttl == timedelta(seconds=3600)

    def test_cache_key_generation(self, cache):
        """Test consistent cache key generation"""
        key1 = cache._get_cache_key("test_func", arg1="value1", arg2="value2")
        key2 = cache._get_cache_key("test_func", arg2="value2", arg1="value1")
        # Keys should be identical regardless of arg order
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    def test_cache_key_different_for_different_args(self, cache):
        """Test cache keys differ for different arguments"""
        key1 = cache._get_cache_key("test_func", arg1="value1")
        key2 = cache._get_cache_key("test_func", arg1="value2")
        assert key1 != key2

    def test_cache_set_and_get(self, cache):
        """Test basic cache set and get operations"""
        test_data = {"status": "success", "data": [1, 2, 3]}
        key = "test_key"

        cache.set(key, test_data)
        retrieved = cache.get(key)

        assert retrieved == test_data

    def test_cache_json_serialization(self, cache, temp_cache_dir):
        """Test that cache uses JSON serialization"""
        test_data = {"status": "success", "count": 42}
        key = "json_test"

        cache.set(key, test_data)

        # Verify file is JSON
        cache_file = Path(temp_cache_dir) / f"{key}.json"
        assert cache_file.exists()

        with open(cache_file) as f:
            file_data = json.load(f)

        assert "value" in file_data
        assert "expires_at" in file_data
        assert file_data["value"] == test_data

    def test_cache_ttl_expiration(self, cache):
        """Test cache TTL expiration"""
        test_data = {"message": "This should expire"}
        key = "expiring_key"

        cache.set(key, test_data)

        # Should retrieve immediately
        assert cache.get(key) == test_data

        # Wait for TTL to expire (cache has 1 second TTL)
        time.sleep(1.1)

        # Should return None after expiration
        assert cache.get(key) is None

    def test_cache_ttl_timestamp_stored(self, cache, temp_cache_dir):
        """Test that TTL timestamp is stored in cache file"""
        test_data = {"data": "test"}
        key = "ttl_test"

        before = datetime.now()
        cache.set(key, test_data)
        after = datetime.now()

        cache_file = Path(temp_cache_dir) / f"{key}.json"
        with open(cache_file) as f:
            file_data = json.load(f)

        expires_at = datetime.fromisoformat(file_data["expires_at"])

        # Verify expires_at is approximately now + TTL (1 second)
        assert before <= expires_at <= after + timedelta(seconds=1)

    def test_cache_get_nonexistent_key(self, cache):
        """Test get with non-existent key"""
        assert cache.get("nonexistent") is None

    def test_cache_corrupted_file_handling(self, cache, temp_cache_dir):
        """Test handling of corrupted cache files"""
        key = "corrupted"
        cache_file = Path(temp_cache_dir) / f"{key}.json"

        # Write invalid JSON
        with open(cache_file, "w") as f:
            f.write("INVALID JSON{{{")

        # Should return None and delete corrupted file
        assert cache.get(key) is None
        assert not cache_file.exists()

    def test_cache_missing_fields_handling(self, cache, temp_cache_dir):
        """Test handling of cache files with missing fields"""
        key = "incomplete"
        cache_file = Path(temp_cache_dir) / f"{key}.json"

        # Write JSON without required fields
        with open(cache_file, "w") as f:
            json.dump({"value": "data"}, f)  # Missing expires_at

        # Should return None and delete incomplete file
        assert cache.get(key) is None
        assert not cache_file.exists()

    def test_cached_call_cache_hit(self, cache):
        """Test cached_call with cache hit"""
        mock_func = MagicMock(return_value={"result": "success"})

        # First call - cache miss
        result1 = cache.cached_call(mock_func, "test_func", arg="value")
        assert result1 == {"result": "success"}
        assert mock_func.call_count == 1

        # Second call - cache hit
        result2 = cache.cached_call(mock_func, "test_func", arg="value")
        assert result2 == {"result": "success"}
        assert mock_func.call_count == 1  # Should not call again

    def test_cached_call_cache_miss(self, cache):
        """Test cached_call with different arguments causes cache miss"""
        mock_func = MagicMock(return_value={"result": "success"})

        cache.cached_call(mock_func, "test_func", arg="value1")
        cache.cached_call(mock_func, "test_func", arg="value2")

        assert mock_func.call_count == 2  # Different args = different cache keys

    def test_cached_call_expiration(self, cache):
        """Test cached_call after TTL expiration"""
        mock_func = MagicMock(return_value={"result": "success"})

        # First call
        cache.cached_call(mock_func, "test_func", arg="value")
        assert mock_func.call_count == 1

        # Wait for expiration
        time.sleep(1.1)

        # Second call after expiration - should call function again
        cache.cached_call(mock_func, "test_func", arg="value")
        assert mock_func.call_count == 2

    def test_cache_clear(self, cache):
        """Test cache clearing"""
        # Add multiple cache entries
        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        cache.set("key3", {"data": 3})

        # Clear cache
        count = cache.clear()

        assert count == 3
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_cache_stats(self, cache):
        """Test cache statistics"""
        # Add some data
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})

        stats = cache.get_stats()

        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] > 0
        assert stats["ttl_seconds"] == 1
        assert "cache_dir" in stats

    def test_cache_stats_empty_cache(self, cache):
        """Test statistics for empty cache"""
        stats = cache.get_stats()

        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["total_size_mb"] == 0

    def test_cache_complex_data_types(self, cache):
        """Test caching complex nested data structures"""
        complex_data = {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ],
                "metadata": {"count": 2, "page": 1},
            },
            "numbers": [1, 2, 3, 4, 5],
        }

        cache.set("complex", complex_data)
        retrieved = cache.get("complex")

        assert retrieved == complex_data

    def test_cache_file_extension(self, cache, temp_cache_dir):
        """Test that cache files use .json extension"""
        cache.set("test", {"data": "value"})

        json_files = list(Path(temp_cache_dir).glob("*.json"))
        pkl_files = list(Path(temp_cache_dir).glob("*.pkl"))

        assert len(json_files) > 0
        assert len(pkl_files) == 0
