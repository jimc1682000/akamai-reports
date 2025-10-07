"""
Secret Manager Implementation

Provides flexible secret retrieval from multiple sources with fallback support.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from akamai.edgegrid import EdgeRc


@dataclass
class AkamaiCredentials:
    """Akamai API credentials"""

    client_token: str
    client_secret: str
    access_token: str
    host: str


class SecretManager:
    """
    Manages secrets from multiple sources with priority fallback.

    Priority order:
    1. Environment variables (highest priority)
    2. .edgerc file (default)
    3. AWS Secrets Manager (if configured)

    Attributes:
        auth_source: Configured authentication source ('env', 'edgerc', 'aws')
        edgerc_path: Path to .edgerc file
        edgerc_section: Section name in .edgerc file
    """

    def __init__(
        self,
        auth_source: str = "edgerc",
        edgerc_path: Optional[str] = None,
        edgerc_section: str = "default",
    ):
        """
        Initialize SecretManager.

        Args:
            auth_source: Authentication source ('env', 'edgerc', 'aws')
            edgerc_path: Path to .edgerc file (defaults to ~/.edgerc)
            edgerc_section: Section name in .edgerc (defaults to 'default')
        """
        self.auth_source = auth_source
        self.edgerc_path = edgerc_path or str(Path.home() / ".edgerc")
        self.edgerc_section = edgerc_section

    def get_akamai_credentials(self) -> AkamaiCredentials:
        """
        Retrieve Akamai credentials from configured source.

        Returns:
            AkamaiCredentials object

        Raises:
            ValueError: If credentials cannot be retrieved or are incomplete
        """
        if self.auth_source == "env":
            return self._get_credentials_from_env()
        elif self.auth_source == "edgerc":
            return self._get_credentials_from_edgerc()
        elif self.auth_source == "aws":
            return self._get_credentials_from_aws()
        else:
            raise ValueError(f"Unsupported auth source: {self.auth_source}")

    def _get_credentials_from_env(self) -> AkamaiCredentials:
        """
        Retrieve credentials from environment variables.

        Required environment variables:
            - AKAMAI_CLIENT_TOKEN
            - AKAMAI_CLIENT_SECRET
            - AKAMAI_ACCESS_TOKEN
            - AKAMAI_HOST

        Returns:
            AkamaiCredentials object

        Raises:
            ValueError: If required environment variables are missing
        """
        client_token = os.getenv("AKAMAI_CLIENT_TOKEN")
        client_secret = os.getenv("AKAMAI_CLIENT_SECRET")
        access_token = os.getenv("AKAMAI_ACCESS_TOKEN")
        host = os.getenv("AKAMAI_HOST")

        missing_vars = []
        if not client_token:
            missing_vars.append("AKAMAI_CLIENT_TOKEN")
        if not client_secret:
            missing_vars.append("AKAMAI_CLIENT_SECRET")
        if not access_token:
            missing_vars.append("AKAMAI_ACCESS_TOKEN")
        if not host:
            missing_vars.append("AKAMAI_HOST")

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        return AkamaiCredentials(
            client_token=client_token,
            client_secret=client_secret,
            access_token=access_token,
            host=host,
        )

    def _get_credentials_from_edgerc(self) -> AkamaiCredentials:
        """
        Retrieve credentials from .edgerc file.

        Returns:
            AkamaiCredentials object

        Raises:
            ValueError: If .edgerc file not found or section missing
        """
        if not Path(self.edgerc_path).exists():
            raise ValueError(f".edgerc file not found at: {self.edgerc_path}")

        try:
            edgerc = EdgeRc(self.edgerc_path)

            # Verify section exists
            if not edgerc.has_section(self.edgerc_section):
                available_sections = edgerc.sections()
                raise ValueError(
                    f"Section '{self.edgerc_section}' not found in .edgerc. "
                    f"Available sections: {', '.join(available_sections)}"
                )

            return AkamaiCredentials(
                client_token=edgerc.get(self.edgerc_section, "client_token"),
                client_secret=edgerc.get(self.edgerc_section, "client_secret"),
                access_token=edgerc.get(self.edgerc_section, "access_token"),
                host=edgerc.get(self.edgerc_section, "host"),
            )

        except Exception as e:
            raise ValueError(
                f"Failed to read credentials from .edgerc: {str(e)}"
            ) from e

    def _get_credentials_from_aws(self) -> AkamaiCredentials:
        """
        Retrieve credentials from AWS Secrets Manager.

        Note: This is a placeholder for future AWS Secrets Manager integration.
        Requires boto3 and proper AWS configuration.

        Returns:
            AkamaiCredentials object

        Raises:
            NotImplementedError: AWS Secrets Manager support not yet implemented
        """
        raise NotImplementedError(
            "AWS Secrets Manager support is not yet implemented. "
            "Use 'env' or 'edgerc' auth source instead."
        )

    def validate_credentials(self, credentials: AkamaiCredentials) -> bool:
        """
        Validate that all required credential fields are present and non-empty.

        Args:
            credentials: AkamaiCredentials object to validate

        Returns:
            True if all fields are valid, False otherwise
        """
        return all(
            [
                credentials.client_token,
                credentials.client_secret,
                credentials.access_token,
                credentials.host,
            ]
        )
