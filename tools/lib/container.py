"""
Dependency Injection Container for Akamai Traffic Report System

This module provides a dependency injection container to manage application
dependencies and promote loose coupling between components.
"""

from typing import Optional

from akamai.edgegrid import EdgeGridAuth

from tools.lib.api_client import setup_authentication
from tools.lib.config_loader import ConfigLoader, load_configuration


class ServiceContainer:
    """
    Dependency injection container for the application.

    Provides centralized management of application dependencies with lazy initialization.
    Supports dependency injection for better testability and maintainability.
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

    @property
    def config_loader(self) -> ConfigLoader:
        """
        Get configuration loader instance (lazy initialization).

        Returns:
            ConfigLoader instance
        """
        if self._config_loader is None:
            self._config_loader = load_configuration(self.config_path)
        return self._config_loader

    @property
    def auth(self) -> EdgeGridAuth:
        """
        Get EdgeGrid authentication instance (lazy initialization).

        Returns:
            EdgeGridAuth instance
        """
        if self._auth is None:
            self._auth = setup_authentication(self.config_loader)
        return self._auth

    def reset(self):
        """
        Reset all cached instances.

        Useful for testing or when configuration needs to be reloaded.
        """
        self._config_loader = None
        self._auth = None
