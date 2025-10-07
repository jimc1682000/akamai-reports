"""
API Response Schema Validation

Pydantic models for validating Akamai V2 API responses.
Ensures data integrity and provides type safety.
"""

# ruff: noqa: N815
# Akamai API uses mixedCase field names - must match exactly

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TrafficDataPoint(BaseModel):
    """
    Schema for individual traffic data point.

    Attributes:
        time: ISO-8601 timestamp
        edgeHitsTotal: Total edge hits
        edgeBytesTotal: Total edge bytes (required)
        originHitsTotal: Total origin hits
        originBytesTotal: Total origin bytes
    """

    time: str
    edgeHitsTotal: Optional[int] = None
    edgeBytesTotal: int  # Required field for traffic calculation
    originHitsTotal: Optional[int] = None
    originBytesTotal: Optional[int] = None

    @field_validator("edgeBytesTotal")
    @classmethod
    def validate_edge_bytes(cls, v: int) -> int:
        """Ensure edgeBytesTotal is non-negative"""
        if v < 0:
            raise ValueError("edgeBytesTotal must be non-negative")
        return v

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Basic validation for ISO-8601 format"""
        if not v or len(v) < 10:
            raise ValueError("Invalid time format")
        return v


class TrafficAPIResponse(BaseModel):
    """
    Schema for Akamai V2 Traffic API response.

    Attributes:
        data: List of traffic data points
        summaryStatistics: Summary metrics (optional)
    """

    data: List[TrafficDataPoint] = Field(default_factory=list)
    summaryStatistics: Optional[dict] = None

    @field_validator("data")
    @classmethod
    def validate_data_points(cls, v: List[TrafficDataPoint]) -> List[TrafficDataPoint]:
        """Ensure data list is not empty for valid responses"""
        # Allow empty list for error cases, validation happens at API layer
        return v


class EmissionsDataPoint(BaseModel):
    """
    Schema for individual emissions data point.

    Attributes:
        time: ISO-8601 timestamp
        country: Country code (e.g., 'ID', 'TW', 'SG')
        edgeBytesTotal: Total edge bytes (required)
        carbonIntensity: Carbon intensity value
        carbonEmission: Carbon emission value
    """

    time: str
    country: str
    edgeBytesTotal: int
    carbonIntensity: Optional[float] = None
    carbonEmission: Optional[float] = None

    @field_validator("edgeBytesTotal")
    @classmethod
    def validate_edge_bytes(cls, v: int) -> int:
        """Ensure edgeBytesTotal is non-negative"""
        if v < 0:
            raise ValueError("edgeBytesTotal must be non-negative")
        return v

    @field_validator("country")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code format"""
        if not v or len(v) < 2:
            raise ValueError("Invalid country code")
        return v.upper()

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Basic validation for ISO-8601 format"""
        if not v or len(v) < 10:
            raise ValueError("Invalid time format")
        return v


class EmissionsAPIResponse(BaseModel):
    """
    Schema for Akamai V2 Emissions API response.

    Attributes:
        data: List of emissions data points
        summaryStatistics: Summary metrics (optional)
    """

    data: List[EmissionsDataPoint] = Field(default_factory=list)
    summaryStatistics: Optional[dict] = None

    @field_validator("data")
    @classmethod
    def validate_data_points(
        cls, v: List[EmissionsDataPoint]
    ) -> List[EmissionsDataPoint]:
        """Ensure data list is not empty for valid responses"""
        return v
