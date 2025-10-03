#!/usr/bin/env python3
"""
Unit Tests for Retry Strategy with Jitter

Tests for exponential backoff with jitter to prevent thundering herd.
"""

import unittest

from tools.lib.api_client import _calculate_backoff_with_jitter


class TestBackoffWithJitter(unittest.TestCase):
    """Test cases for backoff calculation with jitter"""

    def test_jitter_within_expected_range_first_attempt(self):
        """Test jitter is within range for first attempt"""
        # First attempt (attempt=0): should be between 0 and 2^0 = 1
        for _ in range(100):  # Run multiple times to check randomness
            delay = _calculate_backoff_with_jitter(attempt=0, base=2)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 1)

    def test_jitter_within_expected_range_second_attempt(self):
        """Test jitter is within range for second attempt"""
        # Second attempt (attempt=1): should be between 0 and 2^1 = 2
        for _ in range(100):
            delay = _calculate_backoff_with_jitter(attempt=1, base=2)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 2)

    def test_jitter_within_expected_range_third_attempt(self):
        """Test jitter is within range for third attempt"""
        # Third attempt (attempt=2): should be between 0 and 2^2 = 4
        for _ in range(100):
            delay = _calculate_backoff_with_jitter(attempt=2, base=2)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 4)

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        # Large attempt number should be capped at max_delay
        for _ in range(100):
            delay = _calculate_backoff_with_jitter(attempt=10, base=2, max_delay=5)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 5)  # Should not exceed max_delay

    def test_custom_base(self):
        """Test with custom exponential base"""
        # With base=3, attempt=2 should give range [0, 9]
        for _ in range(100):
            delay = _calculate_backoff_with_jitter(attempt=2, base=3)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 9)  # 3^2 = 9

    def test_jitter_randomness(self):
        """Test that jitter produces different values (is actually random)"""
        delays = [_calculate_backoff_with_jitter(attempt=3, base=2) for _ in range(50)]

        # Should have more than one unique value (statistical test)
        unique_delays = set(delays)
        self.assertGreater(
            len(unique_delays), 10, "Jitter should produce varied delays"
        )

    def test_jitter_distribution(self):
        """Test that jitter is uniformly distributed"""
        # For attempt=2, base=2: range is [0, 4]
        delays = [
            _calculate_backoff_with_jitter(attempt=2, base=2) for _ in range(1000)
        ]

        # Check that we get values across the range
        # Statistical test: should have delays in lower, middle, and upper quartiles
        lower_quartile = sum(1 for d in delays if 0 <= d < 1)
        middle_quartile = sum(1 for d in delays if 1 <= d < 3)
        upper_quartile = sum(1 for d in delays if 3 <= d <= 4)

        # Each quartile should have some representation (not perfect distribution)
        self.assertGreater(lower_quartile, 50, "Should have delays in lower range")
        self.assertGreater(middle_quartile, 100, "Should have delays in middle range")
        self.assertGreater(upper_quartile, 50, "Should have delays in upper range")

    def test_zero_attempt(self):
        """Test behavior with zero attempt (first retry)"""
        # Attempt 0 with base 2 should give [0, 1]
        delay = _calculate_backoff_with_jitter(attempt=0, base=2)
        self.assertGreaterEqual(delay, 0)
        self.assertLessEqual(delay, 1)

    def test_large_attempt_with_max_delay(self):
        """Test that very large attempts respect max_delay"""
        # Even with huge attempt number, should cap at max_delay
        delay = _calculate_backoff_with_jitter(attempt=100, base=2, max_delay=30)
        self.assertGreaterEqual(delay, 0)
        self.assertLessEqual(delay, 30)

    def test_small_max_delay(self):
        """Test with small max_delay value"""
        # Max delay of 1 second should cap everything
        for attempt in range(10):
            delay = _calculate_backoff_with_jitter(attempt=attempt, base=2, max_delay=1)
            self.assertGreaterEqual(delay, 0)
            self.assertLessEqual(delay, 1)

    def test_different_base_values(self):
        """Test behavior with different exponential bases"""
        test_cases = [
            (2, 3, 8),  # base=2, attempt=3: max 2^3 = 8
            (3, 2, 9),  # base=3, attempt=2: max 3^2 = 9
            (4, 2, 16),  # base=4, attempt=2: max 4^2 = 16
        ]

        for base, attempt, expected_max in test_cases:
            with self.subTest(base=base, attempt=attempt):
                delay = _calculate_backoff_with_jitter(attempt=attempt, base=base)
                self.assertGreaterEqual(delay, 0)
                self.assertLessEqual(delay, expected_max)

    def test_prevents_thundering_herd(self):
        """Test that jitter helps prevent thundering herd"""
        # Multiple "clients" retrying at the same time should get different delays
        num_clients = 20
        attempt = 2  # Same attempt number for all

        delays = [
            _calculate_backoff_with_jitter(attempt=attempt, base=2)
            for _ in range(num_clients)
        ]

        # Should have multiple unique values (prevents all clients retrying at once)
        unique_delays = len(set(delays))
        self.assertGreater(
            unique_delays,
            num_clients // 2,
            "Jitter should spread out retry attempts",
        )

    def test_float_return_type(self):
        """Test that function returns float type"""
        delay = _calculate_backoff_with_jitter(attempt=1, base=2)
        self.assertIsInstance(delay, float)

    def test_deterministic_range_bounds(self):
        """Test that bounds are deterministic even if value is random"""
        base = 2
        max_delay = 60

        for attempt in range(10):
            expected_upper_bound = min(base**attempt, max_delay)

            # Run multiple times to ensure all values respect bounds
            for _ in range(20):
                delay = _calculate_backoff_with_jitter(
                    attempt=attempt, base=base, max_delay=max_delay
                )
                self.assertGreaterEqual(
                    delay, 0, f"Delay should be >= 0 for attempt {attempt}"
                )
                self.assertLessEqual(
                    delay,
                    expected_upper_bound,
                    f"Delay should be <= {expected_upper_bound} for attempt {attempt}",
                )


if __name__ == "__main__":
    unittest.main()
