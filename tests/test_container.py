"""
Tests for Service Container Module

Comprehensive test coverage for container lifecycle management.
"""

import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.lib.container import ServiceContainer


class TestServiceContainerBasics(unittest.TestCase):
    """Test basic container functionality"""

    @pytest.fixture(autouse=True)
    def setup_config(self, tmp_path):
        """Create temporary config file for testing"""
        self.config_path = tmp_path / "test_config.json"
        config_content = """{
            "api": {
                "endpoints": {
                    "traffic": "https://test.akamaiapis.net/traffic",
                    "emissions": "https://test.akamaiapis.net/emissions"
                },
                "timeout": 60,
                "max_retries": 3,
                "edgerc_section": "default"
            },
            "business": {
                "cp_codes": ["123456"],
                "billing_coefficient": 1.0
            },
            "reporting": {
                "week_definition": "sunday_to_saturday"
            },
            "system": {
                "data_point_limit": 50000
            }
        }"""
        self.config_path.write_text(config_content)

    def test_container_initialization(self):
        """Test container initializes correctly"""
        container = ServiceContainer(config_path=str(self.config_path))
        self.assertEqual(container.config_path, str(self.config_path))
        self.assertIsNone(container._config_loader)
        self.assertIsNone(container._auth)
        self.assertFalse(container._initialized)

    @patch("tools.lib.container.load_configuration")
    def test_lazy_config_loader(self, mock_load_config):
        """Test config_loader lazy initialization"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))

        # Should not be loaded initially
        self.assertIsNone(container._config_loader)

        # Access should trigger loading
        config = container.config_loader
        self.assertEqual(config, mock_config)
        mock_load_config.assert_called_once_with(str(self.config_path))

        # Second access should not reload
        config2 = container.config_loader
        self.assertEqual(config2, mock_config)
        mock_load_config.assert_called_once()  # Still only one call

    def test_lazy_auth_property_exists(self):
        """Test auth property exists and is lazy"""
        container = ServiceContainer(config_path=str(self.config_path))

        # Should not be loaded initially
        self.assertIsNone(container._auth)

        # Auth property should exist
        self.assertTrue(hasattr(container, "auth"))


class TestServiceContainerLifecycle(unittest.TestCase):
    """Test container lifecycle management"""

    @pytest.fixture(autouse=True)
    def setup_config(self, tmp_path):
        """Create temporary config file"""
        self.config_path = tmp_path / "test_config.json"
        config_content = """{
            "api": {
                "endpoints": {
                    "traffic": "https://test.akamaiapis.net/traffic",
                    "emissions": "https://test.akamaiapis.net/emissions"
                },
                "timeout": 60,
                "max_retries": 3
            },
            "business": {
                "cp_codes": ["123456"],
                "billing_coefficient": 1.0
            },
            "reporting": {
                "week_definition": "sunday_to_saturday"
            },
            "system": {
                "data_point_limit": 50000
            }
        }"""
        self.config_path.write_text(config_content)

    @patch("tools.lib.container.load_configuration")
    def test_initialize_method(self, mock_load_config):
        """Test initialize() method for eager initialization"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))

        # Initially not initialized
        self.assertFalse(container._initialized)

        # Manually set auth to avoid real authentication
        container._auth = MagicMock()

        # Call initialize
        container.initialize()

        # Should be initialized now
        self.assertTrue(container._initialized)
        self.assertIsNotNone(container._config_loader)

    @patch("tools.lib.container.load_configuration")
    def test_reset_method(self, mock_load_config):
        """Test reset() clears all cached instances"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))

        # Manually initialize
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True
        self.assertTrue(container._initialized)

        # Reset
        container.reset()

        # Should be cleared
        self.assertIsNone(container._config_loader)
        self.assertIsNone(container._auth)
        self.assertFalse(container._initialized)

    @patch("tools.lib.container.load_configuration")
    def test_reset_multiple_times(self, mock_load_config):
        """Test reset can be called multiple times"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))

        # Cycle 1: initialize and reset
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True
        self.assertTrue(container._initialized)
        container.reset()
        self.assertFalse(container._initialized)

        # Cycle 2: initialize and reset again
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True
        self.assertTrue(container._initialized)
        container.reset()
        self.assertFalse(container._initialized)


class TestServiceContainerHealthCheck(unittest.TestCase):
    """Test container health check functionality"""

    @pytest.fixture(autouse=True)
    def setup_config(self, tmp_path):
        """Create temporary config file"""
        self.config_path = tmp_path / "test_config.json"
        config_content = """{
            "api": {"timeout": 60, "max_retries": 3},
            "business": {"cp_codes": ["123456"], "billing_coefficient": 1.0},
            "reporting": {"week_definition": "sunday_to_saturday"},
            "system": {"data_point_limit": 50000}
        }"""
        self.config_path.write_text(config_content)

    def test_health_check_not_initialized(self):
        """Test health check when services not initialized"""
        container = ServiceContainer(config_path=str(self.config_path))

        health = container.health_check()

        self.assertEqual(health["config_loader"], "not_initialized")
        self.assertEqual(health["auth"], "not_initialized")
        self.assertEqual(health["overall"], "healthy")
        self.assertEqual(health["initialized"], "False")

    @patch("tools.lib.container.load_configuration")
    def test_health_check_initialized(self, mock_load_config):
        """Test health check when services initialized"""
        mock_config = MagicMock()
        mock_config.get_cp_codes.return_value = ["123456"]
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True

        health = container.health_check()

        self.assertEqual(health["config_loader"], "healthy")
        self.assertEqual(health["auth"], "healthy")
        self.assertEqual(health["overall"], "healthy")
        self.assertEqual(health["initialized"], "True")

    @patch("tools.lib.container.load_configuration")
    def test_health_check_unhealthy_config(self, mock_load_config):
        """Test health check with unhealthy config"""
        mock_config = MagicMock()
        mock_config.get_cp_codes.side_effect = Exception("Config error")
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True

        health = container.health_check()

        self.assertIn("unhealthy", health["config_loader"])
        self.assertIn("Config error", health["config_loader"])
        self.assertEqual(health["overall"], "unhealthy")


class TestServiceContainerThreadSafety(unittest.TestCase):
    """Test container thread safety"""

    @pytest.fixture(autouse=True)
    def setup_config(self, tmp_path):
        """Create temporary config file"""
        self.config_path = tmp_path / "test_config.json"
        config_content = """{
            "api": {"timeout": 60, "max_retries": 3},
            "business": {"cp_codes": ["123456"], "billing_coefficient": 1.0},
            "reporting": {"week_definition": "sunday_to_saturday"},
            "system": {"data_point_limit": 50000}
        }"""
        self.config_path.write_text(config_content)

    @patch("tools.lib.container.load_configuration")
    def test_concurrent_initialization(self, mock_load_config):
        """Test thread-safe concurrent initialization"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))
        results = []

        def access_config():
            config = container.config_loader
            results.append(id(config))

        # Create multiple threads accessing config simultaneously
        threads = [threading.Thread(target=access_config) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should get the same instance
        self.assertEqual(len(set(results)), 1)
        # Config should only be loaded once
        mock_load_config.assert_called_once()

    @patch("tools.lib.container.load_configuration")
    def test_concurrent_reset(self, mock_load_config):
        """Test thread-safe concurrent reset"""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        container = ServiceContainer(config_path=str(self.config_path))
        _ = container.config_loader
        container._auth = MagicMock()
        container._initialized = True

        def reset_container():
            container.reset()
            time.sleep(0.01)  # Small delay to increase chance of race condition

        # Create multiple threads resetting simultaneously
        threads = [threading.Thread(target=reset_container) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Container should be in clean state
        self.assertIsNone(container._config_loader)
        self.assertIsNone(container._auth)
        self.assertFalse(container._initialized)


if __name__ == "__main__":
    unittest.main()
