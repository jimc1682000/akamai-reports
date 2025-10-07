#!/usr/bin/env python3
"""
Unit Tests for Circuit Breaker

Comprehensive test coverage for circuit breaker edge cases and state transitions.
"""

import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from tools.lib.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreakerBasics(unittest.TestCase):
    """Test basic circuit breaker functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            name="Test API",
        )

    def test_initial_state_is_closed(self):
        """Test circuit breaker starts in CLOSED state"""
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit_breaker.failure_count, 0)
        self.assertEqual(self.circuit_breaker.success_count, 0)

    def test_successful_call_in_closed_state(self):
        """Test successful call in CLOSED state"""

        def successful_func():
            return "success"

        result = self.circuit_breaker.call(successful_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit_breaker.failure_count, 0)

    def test_failed_call_increments_failure_count(self):
        """Test failed call increments failure count"""

        def failing_func():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            self.circuit_breaker.call(failing_func)

        self.assertEqual(self.circuit_breaker.failure_count, 1)
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)

    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after reaching failure threshold"""

        def failing_func():
            raise ValueError("Test error")

        # Fail 3 times to reach threshold
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(failing_func)

        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
        self.assertEqual(self.circuit_breaker.failure_count, 3)

    def test_open_circuit_rejects_calls(self):
        """Test OPEN circuit rejects all calls immediately"""

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(3):
            try:
                self.circuit_breaker.call(failing_func)
            except ValueError:
                pass  # Expected

        # Verify circuit is now OPEN
        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)

        # Now circuit is OPEN, should reject immediately
        exception_raised = False
        try:
            self.circuit_breaker.call(lambda: "should not execute")
        except CircuitBreakerOpenError:
            exception_raised = True

        self.assertTrue(
            exception_raised,
            "CircuitBreakerOpenError should be raised when circuit is OPEN",
        )

    def test_reset_clears_state(self):
        """Test reset clears all state"""

        def failing_func():
            raise ValueError("Test error")

        # Fail to accumulate state
        with self.assertRaises(ValueError):
            self.circuit_breaker.call(failing_func)

        self.assertEqual(self.circuit_breaker.failure_count, 1)

        # Reset
        self.circuit_breaker.reset()

        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit_breaker.failure_count, 0)
        self.assertEqual(self.circuit_breaker.success_count, 0)
        self.assertIsNone(self.circuit_breaker.last_failure_time)


class TestCircuitBreakerHalfOpenState(unittest.TestCase):
    """Test HALF_OPEN state transitions"""

    def setUp(self):
        """Set up test fixtures"""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,
            success_threshold=2,
            name="Test API",
        )

    def test_half_open_after_recovery_timeout(self):
        """Test circuit transitions to HALF_OPEN after recovery timeout"""

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(failing_func)

        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        # We use a successful function to test the transition
        def successful_func():
            return "success"

        result = self.circuit_breaker.call(successful_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, CircuitState.HALF_OPEN)
        self.assertEqual(self.circuit_breaker.success_count, 1)

    def test_half_open_reopens_on_failure(self):
        """Test HALF_OPEN → OPEN transition on failure"""

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(failing_func)

        # Wait for recovery
        time.sleep(1.1)

        # Transition to HALF_OPEN with one success
        self.circuit_breaker.call(lambda: "success")
        self.assertEqual(self.circuit_breaker.state, CircuitState.HALF_OPEN)

        # Now fail - should reopen circuit
        with self.assertRaises(ValueError):
            self.circuit_breaker.call(failing_func)

        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
        self.assertEqual(self.circuit_breaker.success_count, 0)

    def test_half_open_closes_after_success_threshold(self):
        """Test HALF_OPEN → CLOSED after success threshold"""

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                self.circuit_breaker.call(failing_func)

        # Wait for recovery
        time.sleep(1.1)

        # Succeed twice to reach success threshold
        self.circuit_breaker.call(lambda: "success 1")
        self.assertEqual(self.circuit_breaker.state, CircuitState.HALF_OPEN)

        self.circuit_breaker.call(lambda: "success 2")
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit_breaker.failure_count, 0)
        self.assertEqual(self.circuit_breaker.success_count, 0)


class TestCircuitBreakerEdgeCases(unittest.TestCase):
    """Test edge cases and concurrent scenarios"""

    def test_time_until_retry_when_open(self):
        """Test time_until_retry calculation via get_state()"""
        circuit_breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=10, success_threshold=2
        )

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                circuit_breaker.call(failing_func)

        # Check time until retry via get_state()
        state = circuit_breaker.get_state()
        time_remaining = state["time_until_retry"]
        self.assertGreater(time_remaining, 0)
        self.assertLessEqual(time_remaining, 10)

    def test_time_until_retry_when_closed(self):
        """Test time_until_retry returns 0 when CLOSED via get_state()"""
        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

        state = circuit_breaker.get_state()
        time_remaining = state["time_until_retry"]
        self.assertEqual(time_remaining, 0)

    def test_get_state_returns_dict(self):
        """Test get_state returns complete state information"""
        circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            name="Test CB",
        )

        state = circuit_breaker.get_state()

        self.assertIn("name", state)
        self.assertIn("state", state)
        self.assertIn("failure_count", state)
        self.assertIn("success_count", state)
        self.assertIn("failure_threshold", state)
        self.assertIn("success_threshold", state)
        self.assertIn("recovery_timeout", state)
        self.assertIn("time_until_retry", state)
        self.assertEqual(state["state"], "closed")  # State values are lowercase
        self.assertEqual(state["name"], "Test CB")

    def test_state_persistence_across_resets(self):
        """Test state can be properly reset multiple times"""

        def failing_func():
            raise ValueError("Test error")

        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # First cycle
        for _ in range(2):
            with self.assertRaises(ValueError):
                circuit_breaker.call(failing_func)
        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)

        # Reset
        circuit_breaker.reset()
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)

        # Second cycle
        for _ in range(2):
            with self.assertRaises(ValueError):
                circuit_breaker.call(failing_func)
        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)

        # Reset again
        circuit_breaker.reset()
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)

    def test_concurrent_call_handling(self):
        """Test circuit breaker handles concurrent-like calls correctly"""
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        def failing_func():
            raise ValueError("Test error")

        # Simulate rapid successive failures - stop after circuit opens
        failures = 0
        for _ in range(5):
            try:
                circuit_breaker.call(failing_func)
            except ValueError:
                failures += 1
            except CircuitBreakerOpenError:
                # Circuit is now open, break
                break

        # Circuit should be OPEN after 3 failures
        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)
        self.assertEqual(failures, 3)

        # Additional calls should be rejected without executing
        call_executed = False

        def test_func():
            nonlocal call_executed
            call_executed = True
            return "executed"

        exception_raised = False
        try:
            circuit_breaker.call(test_func)
        except CircuitBreakerOpenError:
            exception_raised = True

        self.assertTrue(exception_raised, "CircuitBreakerOpenError should be raised")
        self.assertFalse(
            call_executed, "Function should not execute when circuit is OPEN"
        )


class TestCircuitBreakerConfiguration(unittest.TestCase):
    """Test circuit breaker with different configurations"""

    def test_low_failure_threshold(self):
        """Test circuit breaker with failure_threshold=1"""
        circuit_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        def failing_func():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            circuit_breaker.call(failing_func)

        # Should open immediately after 1 failure
        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)

    def test_high_success_threshold(self):
        """Test circuit breaker with high success threshold"""
        circuit_breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=1, success_threshold=5
        )

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                circuit_breaker.call(failing_func)

        # Wait for recovery
        time.sleep(1.1)

        # Need 5 successes to close
        for _ in range(4):
            circuit_breaker.call(lambda: "success")
            self.assertEqual(circuit_breaker.state, CircuitState.HALF_OPEN)

        # 5th success should close the circuit
        circuit_breaker.call(lambda: "success")
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)

    def test_zero_recovery_timeout(self):
        """Test circuit breaker with recovery_timeout=0"""
        circuit_breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=0, success_threshold=1
        )

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with self.assertRaises(ValueError):
                circuit_breaker.call(failing_func)

        self.assertEqual(circuit_breaker.state, CircuitState.OPEN)

        # Should immediately allow recovery attempts
        circuit_breaker.call(lambda: "success")
        self.assertEqual(circuit_breaker.state, CircuitState.CLOSED)


if __name__ == "__main__":
    unittest.main()
