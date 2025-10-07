"""
Dependency Injection Container for Akamai Traffic Report System

This module provides a dependency injection container to manage application
dependencies and promote loose coupling between components.
"""

import threading
from typing import Dict, Optional

from akamai.edgegrid import EdgeGridAuth

from tools.lib.api_client import setup_authentication
from tools.lib.config_loader import ConfigLoader, load_configuration


class ServiceContainer:
    """
    Dependency injection container for the application.

    Provides centralized management of application dependencies with lazy initialization.
    Supports dependency injection for better testability and maintainability.
    Thread-safe with initialization control and health checks.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the service container.

        Args:
            config_path: Path to configuration file (default: "config.json")
        """
        self.config_path = config_path
        self._config_loader: Optional[ConfigLoader] = None
        self._auth: Optional[EdgeGridAuth] = None
        self._initialized = False
        self._lock = threading.Lock()

    @property
    def config_loader(self) -> ConfigLoader:
        """
        Get configuration loader instance (lazy initialization with thread safety).

        Returns:
            ConfigLoader instance
        """
        if self._config_loader is None:
            with self._lock:
                if self._config_loader is None:
                    self._config_loader = load_configuration(self.config_path)
        return self._config_loader

    @property
    def auth(self) -> EdgeGridAuth:
        """
        Get EdgeGrid authentication instance (lazy initialization with thread safety).

        Returns:
            EdgeGridAuth instance
        """
        if self._auth is None:
            with self._lock:
                if self._auth is None:
                    self._auth = setup_authentication(self.config_loader)
        return self._auth

    def initialize(self) -> None:
        """
        Eagerly initialize all dependencies.

        Useful for fail-fast behavior at startup rather than lazy initialization.
        Thread-safe operation.
        """
        with self._lock:
            if not self._initialized:
                # Trigger lazy initialization
                _ = self.config_loader
                _ = self.auth
                self._initialized = True

    def health_check(self) -> Dict[str, str]:
        """
        Perform health check on all container services.

        Returns:
            Dict with health status of each service
        """
        health_status = {}

        # Check config loader
        try:
            if self._config_loader is not None:
                self.config_loader.get_cp_codes()  # Test access
                health_status["config_loader"] = "healthy"
            else:
                health_status["config_loader"] = "not_initialized"
        except Exception as e:
            health_status["config_loader"] = f"unhealthy: {str(e)}"

        # Check authentication
        try:
            if self._auth is not None:
                # Auth is healthy if it exists
                health_status["auth"] = "healthy"
            else:
                health_status["auth"] = "not_initialized"
        except Exception as e:
            health_status["auth"] = f"unhealthy: {str(e)}"

        # Overall status
        all_healthy = all(
            status in ["healthy", "not_initialized"]
            for status in health_status.values()
        )
        health_status["overall"] = "healthy" if all_healthy else "unhealthy"
        health_status["initialized"] = str(self._initialized)

        return health_status

    def reset(self) -> None:
        """
        Reset all cached instances.

        Useful for testing or when configuration needs to be reloaded.
        Thread-safe operation.
        """
        with self._lock:
            self._config_loader = None
            self._auth = None
            self._initialized = False
