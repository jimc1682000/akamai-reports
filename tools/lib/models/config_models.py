"""
Pydantic Models for Configuration Validation

This module defines Pydantic models for validating config.json structure.
Provides type-safe configuration with automatic validation and helpful error messages.
"""

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class APIEndpointsConfig(BaseModel):
    """API endpoint URLs configuration"""

    traffic: str = Field(..., min_length=1, description="V2 Traffic API endpoint URL")
    emissions: str = Field(
        ..., min_length=1, description="V2 Emissions API endpoint URL"
    )

    @field_validator("traffic", "emissions")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that endpoint looks like a URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Endpoint must be a valid HTTP(S) URL, got: {v}")
        return v


class APITimeoutsConfig(BaseModel):
    """API-specific timeout configuration"""

    traffic: int = Field(
        60, gt=0, le=300, description="Timeout for Traffic API in seconds"
    )
    emissions: int = Field(
        60, gt=0, le=300, description="Timeout for Emissions API in seconds"
    )


class RetryDelaysConfig(BaseModel):
    """Retry delay configuration"""

    exponential_backoff_base: int = Field(
        2,
        ge=2,
        le=10,
        description="Base for exponential backoff (delay = base^attempt)",
    )
    network_error_delay: float = Field(
        1.0, gt=0, le=60, description="Fixed delay after network errors (seconds)"
    )
    rate_limit_delay: float = Field(
        0.5, gt=0, le=10, description="Delay between API calls (seconds)"
    )


class APIThresholdsConfig(BaseModel):
    """API threshold configuration"""

    data_point_warning_ratio: float = Field(
        0.9,
        gt=0,
        le=1.0,
        description="Ratio at which to warn about approaching data point limit",
    )


class APIConfig(BaseModel):
    """API configuration section"""

    endpoints: APIEndpointsConfig
    timeout: int = Field(60, gt=0, le=600, description="Default API timeout in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    timeouts: Optional[APITimeoutsConfig] = None
    retry_delays: Optional[RetryDelaysConfig] = None
    thresholds: Optional[APIThresholdsConfig] = None
    edgerc_section: str = Field(
        "default", min_length=1, description="Section name in ~/.edgerc file"
    )


class ServiceMappingConfig(BaseModel):
    """Service mapping configuration"""

    name: str = Field(..., min_length=1, description="Service display name")
    unit: str = Field(..., min_length=1, description="Reporting unit")
    description: str = Field(..., min_length=1, description="Service description")


class BusinessConfig(BaseModel):
    """Business configuration section"""

    cp_codes: list[str] = Field(
        ..., min_length=1, description="List of CP codes to query"
    )
    service_mappings: Dict[str, ServiceMappingConfig] = Field(
        ..., description="Mapping of CP codes to service information"
    )
    billing_coefficient: float = Field(
        1.0, gt=0, le=2.0, description="Billing calculation coefficient"
    )

    @field_validator("cp_codes")
    @classmethod
    def validate_cp_codes(cls, v: list[str]) -> list[str]:
        """Validate CP codes are non-empty strings"""
        for cp_code in v:
            if not cp_code or not cp_code.strip():
                raise ValueError("CP codes cannot be empty strings")
        return v


class ReportingConfig(BaseModel):
    """Reporting configuration section"""

    week_definition: Literal[
        "sunday_to_saturday", "monday_to_sunday", "monday_to_friday", "custom"
    ] = Field("sunday_to_saturday", description="Week cycle definition")
    region_mappings: Dict[str, str] = Field(
        ..., min_length=1, description="Region code to name mappings"
    )
    custom_start_day: Optional[int] = Field(
        None, ge=0, le=6, description="Custom week start day (0=Sunday, 6=Saturday)"
    )

    @model_validator(mode="after")
    def validate_custom_week(self) -> "ReportingConfig":
        """Validate custom_start_day is provided when week_definition is 'custom'"""
        if self.week_definition == "custom" and self.custom_start_day is None:
            raise ValueError(
                "custom_start_day must be provided when week_definition is 'custom'"
            )
        return self


class ConcurrencyConfig(BaseModel):
    """Concurrency configuration"""

    max_workers: int = Field(
        3, ge=1, le=20, description="Maximum concurrent API request workers"
    )
    rate_limit_delay: float = Field(
        0.1, gt=0, le=10, description="Delay between request submissions (seconds)"
    )
    pool_connections: int = Field(
        10, ge=1, le=100, description="Number of HTTP connection pools"
    )
    pool_maxsize: int = Field(
        20, ge=1, le=200, description="Maximum connections per pool"
    )


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration"""

    failure_threshold: int = Field(
        3, ge=1, le=20, description="Failures before opening circuit"
    )
    recovery_timeout: int = Field(
        30, ge=1, le=600, description="Seconds before attempting recovery"
    )
    success_threshold: int = Field(
        2, ge=1, le=10, description="Successes needed to close circuit from half-open"
    )


class SystemConfig(BaseModel):
    """System configuration section"""

    data_point_limit: int = Field(
        50000, gt=0, le=1000000, description="API single query data point limit"
    )
    concurrency: ConcurrencyConfig
    circuit_breaker: CircuitBreakerConfig


class AuthenticationConfig(BaseModel):
    """Authentication configuration"""

    source: Literal["edgerc", "env", "aws"] = Field(
        "edgerc", description="Credential source"
    )
    edgerc_path: Optional[str] = Field(None, description="Custom path to .edgerc file")


class Config(BaseModel):
    """
    Root configuration model for Akamai Traffic Report.

    This model validates the entire config.json structure with comprehensive
    type checking, range validation, and business logic validation.
    """

    api: APIConfig
    business: BusinessConfig
    reporting: ReportingConfig
    system: SystemConfig
    authentication: Optional[AuthenticationConfig] = None

    model_config = {
        "extra": "allow",  # Allow metadata fields like _version, _description
        "str_strip_whitespace": True,  # Auto-strip whitespace from strings
    }

    @model_validator(mode="after")
    def validate_service_mappings(self) -> "Config":
        """Validate that all CP codes have service mappings"""
        cp_codes = set(self.business.cp_codes)
        mapped_codes = set(self.business.service_mappings.keys())

        # It's OK to have extra mappings, but all CP codes should be mapped
        unmapped = cp_codes - mapped_codes
        if unmapped:
            raise ValueError(
                f"CP codes missing service mappings: {', '.join(sorted(unmapped))}"
            )

        return self
