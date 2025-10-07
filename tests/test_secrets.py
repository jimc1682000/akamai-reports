"""
Tests for Secrets Management Module

Comprehensive test coverage for SecretManager and credential retrieval.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.lib.secrets import SecretManager
from tools.lib.secrets.manager import AkamaiCredentials


class TestAkamaiCredentials(unittest.TestCase):
    """Test AkamaiCredentials dataclass"""

    def test_credentials_initialization(self):
        """Test credentials object initialization"""
        creds = AkamaiCredentials(
            client_token="test_token",
            client_secret="test_secret",
            access_token="test_access",
            host="test.akamaiapis.net",
        )

        self.assertEqual(creds.client_token, "test_token")
        self.assertEqual(creds.client_secret, "test_secret")
        self.assertEqual(creds.access_token, "test_access")
        self.assertEqual(creds.host, "test.akamaiapis.net")


class TestSecretManagerEnvironmentVariables(unittest.TestCase):
    """Test SecretManager with environment variables"""

    def setUp(self):
        """Set up test environment variables"""
        self.env_vars = {
            "AKAMAI_CLIENT_TOKEN": "env_client_token",
            "AKAMAI_CLIENT_SECRET": "env_client_secret",
            "AKAMAI_ACCESS_TOKEN": "env_access_token",
            "AKAMAI_HOST": "env.akamaiapis.net",
        }

    def test_env_auth_source(self):
        """Test initialization with env auth source"""
        manager = SecretManager(auth_source="env")
        self.assertEqual(manager.auth_source, "env")

    @patch.dict(
        os.environ,
        {
            "AKAMAI_CLIENT_TOKEN": "env_client_token",
            "AKAMAI_CLIENT_SECRET": "env_client_secret",
            "AKAMAI_ACCESS_TOKEN": "env_access_token",
            "AKAMAI_HOST": "env.akamaiapis.net",
        },
    )
    def test_get_credentials_from_env(self):
        """Test retrieving credentials from environment variables"""
        manager = SecretManager(auth_source="env")
        creds = manager.get_akamai_credentials()

        self.assertEqual(creds.client_token, "env_client_token")
        self.assertEqual(creds.client_secret, "env_client_secret")
        self.assertEqual(creds.access_token, "env_access_token")
        self.assertEqual(creds.host, "env.akamaiapis.net")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_vars_raises_error(self):
        """Test that missing environment variables raise ValueError"""
        manager = SecretManager(auth_source="env")

        with self.assertRaises(ValueError) as context:
            manager.get_akamai_credentials()

        error_msg = str(context.exception)
        self.assertIn("Missing required environment variables", error_msg)
        self.assertIn("AKAMAI_CLIENT_TOKEN", error_msg)
        self.assertIn("AKAMAI_CLIENT_SECRET", error_msg)
        self.assertIn("AKAMAI_ACCESS_TOKEN", error_msg)
        self.assertIn("AKAMAI_HOST", error_msg)

    @patch.dict(os.environ, {"AKAMAI_CLIENT_TOKEN": "token_only"}, clear=True)
    def test_partial_env_vars_raises_error(self):
        """Test that partial environment variables raise ValueError"""
        manager = SecretManager(auth_source="env")

        with self.assertRaises(ValueError) as context:
            manager.get_akamai_credentials()

        error_msg = str(context.exception)
        self.assertIn("Missing required environment variables", error_msg)
        # Should list missing vars, not the present one
        self.assertIn("AKAMAI_CLIENT_SECRET", error_msg)
        self.assertIn("AKAMAI_ACCESS_TOKEN", error_msg)
        self.assertIn("AKAMAI_HOST", error_msg)


class TestSecretManagerEdgeRC(unittest.TestCase):
    """Test SecretManager with .edgerc files"""

    @pytest.fixture(autouse=True)
    def setup_temp_edgerc(self, tmp_path):
        """Create temporary .edgerc file for testing"""
        self.edgerc_path = tmp_path / ".edgerc"
        edgerc_content = """[default]
client_token = default_token
client_secret = default_secret
access_token = default_access
host = default.akamaiapis.net

[staging]
client_token = staging_token
client_secret = staging_secret
access_token = staging_access
host = staging.akamaiapis.net
"""
        self.edgerc_path.write_text(edgerc_content)

    def test_edgerc_default_section(self):
        """Test reading from default section of .edgerc"""
        manager = SecretManager(auth_source="edgerc", edgerc_path=str(self.edgerc_path))
        creds = manager.get_akamai_credentials()

        self.assertEqual(creds.client_token, "default_token")
        self.assertEqual(creds.client_secret, "default_secret")
        self.assertEqual(creds.access_token, "default_access")
        self.assertEqual(creds.host, "default.akamaiapis.net")

    def test_edgerc_custom_section(self):
        """Test reading from custom section of .edgerc"""
        manager = SecretManager(
            auth_source="edgerc",
            edgerc_path=str(self.edgerc_path),
            edgerc_section="staging",
        )
        creds = manager.get_akamai_credentials()

        self.assertEqual(creds.client_token, "staging_token")
        self.assertEqual(creds.client_secret, "staging_secret")
        self.assertEqual(creds.access_token, "staging_access")
        self.assertEqual(creds.host, "staging.akamaiapis.net")

    def test_edgerc_nonexistent_file_raises_error(self):
        """Test that nonexistent .edgerc raises ValueError"""
        manager = SecretManager(
            auth_source="edgerc", edgerc_path="/nonexistent/path/.edgerc"
        )

        with self.assertRaises(ValueError) as context:
            manager.get_akamai_credentials()

        self.assertIn(".edgerc file not found", str(context.exception))

    def test_edgerc_nonexistent_section_raises_error(self):
        """Test that nonexistent section raises ValueError"""
        manager = SecretManager(
            auth_source="edgerc",
            edgerc_path=str(self.edgerc_path),
            edgerc_section="nonexistent",
        )

        with self.assertRaises(ValueError) as context:
            manager.get_akamai_credentials()

        error_msg = str(context.exception)
        self.assertIn("Section 'nonexistent' not found", error_msg)
        self.assertIn("Available sections", error_msg)

    def test_edgerc_default_path(self):
        """Test that default path points to home directory"""
        manager = SecretManager(auth_source="edgerc")
        expected_path = str(Path.home() / ".edgerc")
        self.assertEqual(manager.edgerc_path, expected_path)


class TestSecretManagerAWS(unittest.TestCase):
    """Test SecretManager with AWS Secrets Manager"""

    def test_aws_raises_not_implemented(self):
        """Test that AWS Secrets Manager raises NotImplementedError"""
        manager = SecretManager(auth_source="aws")

        with self.assertRaises(NotImplementedError) as context:
            manager.get_akamai_credentials()

        error_msg = str(context.exception)
        self.assertIn("AWS Secrets Manager support is not yet implemented", error_msg)
        self.assertIn("Use 'env' or 'edgerc'", error_msg)


class TestSecretManagerValidation(unittest.TestCase):
    """Test credential validation"""

    def test_validate_complete_credentials(self):
        """Test validation with complete credentials"""
        manager = SecretManager()
        creds = AkamaiCredentials(
            client_token="token",
            client_secret="secret",
            access_token="access",
            host="host.net",
        )

        self.assertTrue(manager.validate_credentials(creds))

    def test_validate_missing_client_token(self):
        """Test validation fails with missing client_token"""
        manager = SecretManager()
        creds = AkamaiCredentials(
            client_token="",  # Missing
            client_secret="secret",
            access_token="access",
            host="host.net",
        )

        self.assertFalse(manager.validate_credentials(creds))

    def test_validate_missing_host(self):
        """Test validation fails with missing host"""
        manager = SecretManager()
        creds = AkamaiCredentials(
            client_token="token",
            client_secret="secret",
            access_token="access",
            host="",  # Missing
        )

        self.assertFalse(manager.validate_credentials(creds))

    def test_validate_all_missing(self):
        """Test validation fails with all fields missing"""
        manager = SecretManager()
        creds = AkamaiCredentials(
            client_token="",
            client_secret="",
            access_token="",
            host="",
        )

        self.assertFalse(manager.validate_credentials(creds))


class TestSecretManagerConfiguration(unittest.TestCase):
    """Test SecretManager configuration"""

    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        manager = SecretManager()

        self.assertEqual(manager.auth_source, "edgerc")
        self.assertEqual(manager.edgerc_section, "default")
        expected_path = str(Path.home() / ".edgerc")
        self.assertEqual(manager.edgerc_path, expected_path)

    def test_initialization_with_custom_values(self):
        """Test initialization with custom values"""
        manager = SecretManager(
            auth_source="env",
            edgerc_path="/custom/path/.edgerc",
            edgerc_section="production",
        )

        self.assertEqual(manager.auth_source, "env")
        self.assertEqual(manager.edgerc_path, "/custom/path/.edgerc")
        self.assertEqual(manager.edgerc_section, "production")

    def test_unsupported_auth_source_raises_error(self):
        """Test that unsupported auth source raises ValueError"""
        manager = SecretManager(auth_source="unsupported")

        with self.assertRaises(ValueError) as context:
            manager.get_akamai_credentials()

        self.assertIn("Unsupported auth source", str(context.exception))


if __name__ == "__main__":
    unittest.main()
