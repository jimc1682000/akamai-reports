"""
Secrets Management Module

Provides secure credential management with support for multiple secret sources:
- .edgerc files (default)
- Environment variables
- AWS Secrets Manager (optional)
"""

from tools.lib.secrets.manager import SecretManager


__all__ = ["SecretManager"]
