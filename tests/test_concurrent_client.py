"""
Tests for Concurrent API Client with Connection Pooling

Comprehensive test coverage for concurrent execution and connection reuse.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from tools.lib.http.concurrent_client import ConcurrentAPIClient


class TestConcurrentClientBasics(unittest.TestCase):
    """Test basic concurrent client functionality"""

    def test_initialization(self):
        """Test client initializes correctly"""
        client = ConcurrentAPIClient(max_workers=3, rate_limit_delay=0.05)
        self.assertEqual(client.max_workers, 3)
        self.assertEqual(client.rate_limit_delay, 0.05)
        self.assertIsNotNone(client.session)
        self.assertIsNotNone(client.executor)
        client.shutdown()

    def test_initialization_with_pool_settings(self):
        """Test initialization with custom pool settings"""
        client = ConcurrentAPIClient(
            max_workers=5, pool_connections=15, pool_maxsize=30
        )
        self.assertIsNotNone(client.session)
        # Verify adapters are mounted
        self.assertIn("http://", client.session.adapters)
        self.assertIn("https://", client.session.adapters)
        client.shutdown()

    def test_session_creation(self):
        """Test that session is created with connection pooling"""
        client = ConcurrentAPIClient()
        session = client.get_session()
        self.assertIsNotNone(session)
        self.assertEqual(session, client.session)
        client.shutdown()


class TestConcurrentExecution(unittest.TestCase):
    """Test concurrent execution functionality"""

    def test_execute_batch_basic(self):
        """Test basic batch execution"""
        client = ConcurrentAPIClient(max_workers=2)

        def mock_func(item, multiplier=1):
            return {"result": item * multiplier}

        items = [1, 2, 3]
        results = client.execute_batch(mock_func, items, multiplier=10)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[1], {"result": 10})
        self.assertEqual(results[2], {"result": 20})
        self.assertEqual(results[3], {"result": 30})
        client.shutdown()

    def test_execute_batch_empty_items(self):
        """Test batch execution with empty items"""
        client = ConcurrentAPIClient()

        def mock_func(item):
            return {"result": item}

        results = client.execute_batch(mock_func, [])
        self.assertEqual(results, {})
        client.shutdown()

    def test_execute_batch_with_errors(self):
        """Test batch execution handles errors gracefully"""
        client = ConcurrentAPIClient(max_workers=2)

        def failing_func(item):
            if item == 2:
                raise ValueError("Test error")
            return {"result": item}

        items = [1, 2, 3]
        results = client.execute_batch(failing_func, items)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[1], {"result": 1})
        self.assertFalse(results[2]["success"])
        self.assertIn("Test error", results[2]["error"])
        self.assertEqual(results[3], {"result": 3})
        client.shutdown()

    def test_rate_limiting(self):
        """Test rate limiting between request submissions"""
        client = ConcurrentAPIClient(max_workers=5, rate_limit_delay=0.1)
        call_times = []

        def time_tracking_func(item):
            call_times.append(time.time())
            return {"result": item}

        items = [1, 2, 3]
        start_time = time.time()
        client.execute_batch(time_tracking_func, items)

        # Verify rate limiting delay exists
        # With 3 items and 0.1s delay, should take at least 0.2s to submit all
        total_time = time.time() - start_time
        self.assertGreater(total_time, 0.15)  # Allow some margin
        client.shutdown()


class TestConnectionPooling(unittest.TestCase):
    """Test connection pooling functionality"""

    def test_session_reuse(self):
        """Test that same session is reused across calls"""
        client = ConcurrentAPIClient()

        session1 = client.get_session()
        session2 = client.get_session()

        # Should be the same object
        self.assertIs(session1, session2)
        client.shutdown()

    def test_adapter_configuration(self):
        """Test HTTPAdapter is properly configured"""
        client = ConcurrentAPIClient(pool_connections=5, pool_maxsize=10)

        # Check that adapters are mounted
        http_adapter = client.session.get_adapter("http://example.com")
        https_adapter = client.session.get_adapter("https://example.com")

        self.assertIsNotNone(http_adapter)
        self.assertIsNotNone(https_adapter)
        client.shutdown()

    @patch("requests.Session.request")
    def test_connection_reuse_in_batch(self, mock_request):
        """Test that connections are reused in batch execution"""
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: {"ok": True}
        )

        client = ConcurrentAPIClient(max_workers=2)

        def api_call(item):
            # Use the session for a request
            return client.session.get(f"https://api.example.com/{item}").json()

        items = [1, 2, 3]
        client.execute_batch(api_call, items)

        # Verify session.request was called (connection pooling active)
        self.assertGreater(mock_request.call_count, 0)
        client.shutdown()


class TestShutdown(unittest.TestCase):
    """Test shutdown and cleanup functionality"""

    def test_shutdown_basic(self):
        """Test basic shutdown"""
        client = ConcurrentAPIClient()
        client.shutdown()

        # Session should be closed
        # Executor should be shut down (no assertion needed, just verify no error)

    def test_shutdown_with_wait(self):
        """Test shutdown with wait parameter"""
        client = ConcurrentAPIClient()

        def slow_func(item):
            time.sleep(0.05)
            return {"result": item}

        # Start a batch
        import threading

        def run_batch():
            client.execute_batch(slow_func, [1, 2])

        thread = threading.Thread(target=run_batch)
        thread.start()

        time.sleep(0.01)  # Let it start

        # Shutdown with wait=True should wait for completion
        client.shutdown(wait=True)
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())

    def test_context_manager(self):
        """Test context manager usage"""
        with ConcurrentAPIClient(max_workers=2) as client:

            def mock_func(item):
                return {"result": item}

            results = client.execute_batch(mock_func, [1, 2])
            self.assertEqual(len(results), 2)

        # After context exit, should be shut down (no exception)

    def test_context_manager_with_exception(self):
        """Test context manager cleanup on exception"""
        try:
            with ConcurrentAPIClient() as client:
                self.assertIsNotNone(client.session)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should have cleaned up despite exception


class TestConcurrentPerformance(unittest.TestCase):
    """Test concurrent execution performance"""

    def test_concurrent_faster_than_sequential(self):
        """Test that concurrent execution is faster"""

        def slow_func(item):
            time.sleep(0.1)
            return {"result": item}

        items = [1, 2, 3, 4, 5]

        # Sequential execution time
        start = time.time()
        for item in items:
            slow_func(item)
        sequential_time = time.time() - start

        # Concurrent execution time
        client = ConcurrentAPIClient(max_workers=5, rate_limit_delay=0)
        start = time.time()
        client.execute_batch(slow_func, items)
        concurrent_time = time.time() - start

        # Concurrent should be significantly faster
        # Sequential: ~0.5s (5 * 0.1s)
        # Concurrent: ~0.1s (all parallel)
        self.assertLess(concurrent_time, sequential_time * 0.5)
        client.shutdown()

    def test_max_workers_limit(self):
        """Test that max_workers limit is respected"""
        client = ConcurrentAPIClient(max_workers=2)

        execution_times = []

        def tracking_func(item):
            start = time.time()
            time.sleep(0.05)
            execution_times.append((item, time.time() - start))
            return {"result": item}

        items = [1, 2, 3, 4]
        client.execute_batch(tracking_func, items)

        # With max_workers=2, we should have overlap but not all 4 at once
        self.assertEqual(len(execution_times), 4)
        client.shutdown()


if __name__ == "__main__":
    unittest.main()
