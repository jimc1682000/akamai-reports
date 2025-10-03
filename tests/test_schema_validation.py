#!/usr/bin/env python3
"""
Unit Tests for API Schema Validation

Tests for Pydantic schema validation of Akamai V2 API responses.
"""

import unittest

from pydantic import ValidationError

from tools.lib.models import (
    EmissionsAPIResponse,
    EmissionsDataPoint,
    TrafficAPIResponse,
    TrafficDataPoint,
)


class TestTrafficDataPoint(unittest.TestCase):
    """Test cases for TrafficDataPoint schema validation"""

    def test_valid_traffic_data_point(self):
        """Test validation of valid traffic data point"""
        data = {
            "time": "2025-09-24T00:00:00Z",
            "edgeHitsTotal": 1000,
            "edgeBytesTotal": 5000000,
            "originHitsTotal": 100,
            "originBytesTotal": 500000,
        }
        point = TrafficDataPoint(**data)
        self.assertEqual(point.time, "2025-09-24T00:00:00Z")
        self.assertEqual(point.edgeBytesTotal, 5000000)
        self.assertEqual(point.edgeHitsTotal, 1000)

    def test_minimal_valid_data_point(self):
        """Test data point with only required fields"""
        data = {"time": "2025-09-24T00:00:00Z", "edgeBytesTotal": 5000000}
        point = TrafficDataPoint(**data)
        self.assertEqual(point.edgeBytesTotal, 5000000)
        self.assertIsNone(point.edgeHitsTotal)
        self.assertIsNone(point.originBytesTotal)

    def test_negative_edge_bytes_rejected(self):
        """Test that negative edgeBytesTotal is rejected"""
        data = {"time": "2025-09-24T00:00:00Z", "edgeBytesTotal": -1000}
        with self.assertRaises(ValidationError) as context:
            TrafficDataPoint(**data)
        self.assertIn("edgeBytesTotal", str(context.exception))

    def test_missing_required_field(self):
        """Test that missing edgeBytesTotal is rejected"""
        data = {"time": "2025-09-24T00:00:00Z"}
        with self.assertRaises(ValidationError) as context:
            TrafficDataPoint(**data)
        self.assertIn("edgeBytesTotal", str(context.exception))

    def test_invalid_time_format(self):
        """Test that invalid time format is rejected"""
        data = {"time": "", "edgeBytesTotal": 1000}
        with self.assertRaises(ValidationError) as context:
            TrafficDataPoint(**data)
        self.assertIn("time", str(context.exception))


class TestTrafficAPIResponse(unittest.TestCase):
    """Test cases for TrafficAPIResponse schema validation"""

    def test_valid_traffic_response(self):
        """Test validation of valid traffic API response"""
        data = {
            "data": [
                {
                    "time": "2025-09-24T00:00:00Z",
                    "edgeBytesTotal": 1000000,
                    "edgeHitsTotal": 500,
                },
                {
                    "time": "2025-09-24T00:05:00Z",
                    "edgeBytesTotal": 2000000,
                    "edgeHitsTotal": 800,
                },
            ],
            "summaryStatistics": {"totalBytes": 3000000},
        }
        response = TrafficAPIResponse(**data)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0].edgeBytesTotal, 1000000)
        self.assertIsNotNone(response.summaryStatistics)

    def test_empty_data_allowed(self):
        """Test that empty data list is allowed"""
        data = {"data": []}
        response = TrafficAPIResponse(**data)
        self.assertEqual(len(response.data), 0)

    def test_missing_data_field_uses_default(self):
        """Test that missing data field uses default empty list"""
        data = {}
        response = TrafficAPIResponse(**data)
        self.assertEqual(len(response.data), 0)

    def test_invalid_data_point_rejected(self):
        """Test that invalid data points are rejected"""
        data = {
            "data": [
                {"time": "2025-09-24T00:00:00Z"}  # Missing required edgeBytesTotal
            ]
        }
        with self.assertRaises(ValidationError) as context:
            TrafficAPIResponse(**data)
        self.assertIn("edgeBytesTotal", str(context.exception))


class TestEmissionsDataPoint(unittest.TestCase):
    """Test cases for EmissionsDataPoint schema validation"""

    def test_valid_emissions_data_point(self):
        """Test validation of valid emissions data point"""
        data = {
            "time": "2025-09-24T00:00:00Z",
            "country": "ID",
            "edgeBytesTotal": 5000000,
            "carbonIntensity": 0.45,
            "carbonEmission": 2250,
        }
        point = EmissionsDataPoint(**data)
        self.assertEqual(point.country, "ID")
        self.assertEqual(point.edgeBytesTotal, 5000000)
        self.assertEqual(point.carbonIntensity, 0.45)

    def test_country_code_uppercased(self):
        """Test that country code is converted to uppercase"""
        data = {
            "time": "2025-09-24T00:00:00Z",
            "country": "id",
            "edgeBytesTotal": 5000000,
        }
        point = EmissionsDataPoint(**data)
        self.assertEqual(point.country, "ID")

    def test_minimal_emissions_data(self):
        """Test emissions data with only required fields"""
        data = {
            "time": "2025-09-24T00:00:00Z",
            "country": "TW",
            "edgeBytesTotal": 1000000,
        }
        point = EmissionsDataPoint(**data)
        self.assertEqual(point.edgeBytesTotal, 1000000)
        self.assertIsNone(point.carbonIntensity)
        self.assertIsNone(point.carbonEmission)

    def test_negative_edge_bytes_rejected(self):
        """Test that negative edgeBytesTotal is rejected"""
        data = {
            "time": "2025-09-24T00:00:00Z",
            "country": "SG",
            "edgeBytesTotal": -1000,
        }
        with self.assertRaises(ValidationError) as context:
            EmissionsDataPoint(**data)
        self.assertIn("edgeBytesTotal", str(context.exception))

    def test_invalid_country_code_rejected(self):
        """Test that invalid country code is rejected"""
        data = {"time": "2025-09-24T00:00:00Z", "country": "X", "edgeBytesTotal": 1000}
        with self.assertRaises(ValidationError) as context:
            EmissionsDataPoint(**data)
        self.assertIn("country", str(context.exception))


class TestEmissionsAPIResponse(unittest.TestCase):
    """Test cases for EmissionsAPIResponse schema validation"""

    def test_valid_emissions_response(self):
        """Test validation of valid emissions API response"""
        data = {
            "data": [
                {
                    "time": "2025-09-24T00:00:00Z",
                    "country": "ID",
                    "edgeBytesTotal": 1000000,
                    "carbonIntensity": 0.5,
                },
                {
                    "time": "2025-09-24T00:00:00Z",
                    "country": "TW",
                    "edgeBytesTotal": 2000000,
                    "carbonIntensity": 0.6,
                },
            ],
            "summaryStatistics": {"totalEmissions": 1500},
        }
        response = EmissionsAPIResponse(**data)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0].country, "ID")
        self.assertEqual(response.data[1].country, "TW")

    def test_empty_emissions_data_allowed(self):
        """Test that empty data list is allowed"""
        data = {"data": []}
        response = EmissionsAPIResponse(**data)
        self.assertEqual(len(response.data), 0)

    def test_invalid_emissions_point_rejected(self):
        """Test that invalid emissions data points are rejected"""
        data = {
            "data": [
                {
                    "time": "2025-09-24T00:00:00Z",
                    "country": "ID",
                    # Missing required edgeBytesTotal
                }
            ]
        }
        with self.assertRaises(ValidationError) as context:
            EmissionsAPIResponse(**data)
        self.assertIn("edgeBytesTotal", str(context.exception))


class TestSchemaValidationIntegration(unittest.TestCase):
    """Integration tests for schema validation in API client"""

    def test_traffic_response_parsing(self):
        """Test parsing real-world traffic API response structure"""
        real_response = {
            "data": [
                {
                    "time": "2025-09-24T00:00:00Z",
                    "edgeHitsTotal": 12345,
                    "edgeBytesTotal": 567890123,
                    "originHitsTotal": 234,
                    "originBytesTotal": 12345678,
                }
            ],
            "summaryStatistics": {
                "edgeHitsTotal": 12345,
                "edgeBytesTotal": 567890123,
            },
        }
        response = TrafficAPIResponse(**real_response)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].edgeBytesTotal, 567890123)

    def test_emissions_response_parsing(self):
        """Test parsing real-world emissions API response structure"""
        real_response = {
            "data": [
                {
                    "time": "2025-09-24T00:00:00Z",
                    "country": "ID",
                    "edgeBytesTotal": 123456789,
                    "carbonIntensity": 0.456,
                    "carbonEmission": 56.3,
                },
                {
                    "time": "2025-09-24T00:00:00Z",
                    "country": "TW",
                    "edgeBytesTotal": 234567890,
                    "carbonIntensity": 0.567,
                    "carbonEmission": 133.0,
                },
            ]
        }
        response = EmissionsAPIResponse(**real_response)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0].country, "ID")
        self.assertEqual(response.data[1].country, "TW")


if __name__ == "__main__":
    unittest.main()
