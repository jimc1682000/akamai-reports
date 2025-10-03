"""
Circuit Breaker Pattern Implementation

This module implements the circuit breaker pattern to prevent cascading failures
and provide fault tolerance for API calls.
"""

import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from tools.lib.logger import logger


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""

    pass


class CircuitBreaker:
    """
    Circuit breaker for API resilience.

    Implements the circuit breaker pattern with three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Seconds before attempting recovery (default: 60)
        success_threshold: Successes needed to close circuit from half-open (default: 2)
        name: Optional name for logging purposes
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        name: str = "unnamed",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function if circuit is closed
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(
                        f"Circuit breaker [{self.name}] entering HALF_OPEN state"
                    )
                    self.state = CircuitState.HALF_OPEN
                else:
                    time_remaining = self._time_until_retry()
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker [{self.name}] is OPEN, "
                        f"retry in {time_remaining:.0f}s"
                    )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful function execution"""
        with self._lock:
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info(
                        f"Circuit breaker [{self.name}] CLOSED (recovered after "
                        f"{self.success_count} successful calls)"
                    )
                    self.state = CircuitState.CLOSED
                    self.success_count = 0

    def _on_failure(self):
        """Handle failed function execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                # Single failure in half-open state reopens circuit
                logger.warning(
                    f"Circuit breaker [{self.name}] reopened during recovery attempt"
                )
                self.state = CircuitState.OPEN
                self.success_count = 0
            elif self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker [{self.name}] OPEN after "
                    f"{self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
                self.success_count = 0

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        elapsed = datetime.now() - self.last_failure_time
        return elapsed > timedelta(seconds=self.recovery_timeout)

    def _time_until_retry(self) -> float:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0

        elapsed = datetime.now() - self.last_failure_time
        remaining = timedelta(seconds=self.recovery_timeout) - elapsed
        return max(0, remaining.total_seconds())

    def reset(self):
        """
        Manually reset circuit breaker to CLOSED state.

        Useful for administrative recovery or testing.
        """
        with self._lock:
            logger.info(f"Circuit breaker [{self.name}] manually reset to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    def get_state(self) -> dict:
        """
        Get current circuit breaker state information.

        Returns:
            Dictionary with state, counters, and timing information
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "recovery_timeout": self.recovery_timeout,
                "time_until_retry": (
                    self._time_until_retry() if self.state == CircuitState.OPEN else 0
                ),
                "last_failure_time": (
                    self.last_failure_time.isoformat()
                    if self.last_failure_time
                    else None
                ),
            }
