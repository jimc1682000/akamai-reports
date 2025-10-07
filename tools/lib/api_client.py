#!/usr/bin/env python3
"""
Akamai API Client Module

This module provides functions to interact with Akamai V2 Traffic and Emissions APIs.
All API calls include retry mechanisms and comprehensive error handling.

Functions:
    - setup_authentication(): Initialize EdgeGrid authentication
    - call_traffic_api(): Call V2 Traffic API with retry
    - call_emissions_api(): Call V2 Emissions API with retry
    - get_total_edge_traffic(): Query total traffic across all CP codes
    - get_service_traffic(): Query traffic for specific service
    - get_all_service_traffic(): Query all services
    - get_regional_traffic(): Query regional traffic
    - get_all_regional_traffic(): Query all regions
"""

import os
import time
from typing import Any, Dict, Optional

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from pydantic import ValidationError

from tools.lib.cache import ResponseCache
from tools.lib.config_loader import ConfigLoader
from tools.lib.exceptions import (
    APIAuthenticationError,
    APIAuthorizationError,
    APINetworkError,
    APIRateLimitError,
    APIRequestError,
    APIServerError,
    APITimeoutError,
)
from tools.lib.http import ConcurrentAPIClient
from tools.lib.logger import logger
from tools.lib.models import EmissionsAPIResponse, TrafficAPIResponse
from tools.lib.resilience import CircuitBreaker
from tools.lib.tracing import (
    ErrorContext,
    RequestContext,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    set_current_context,
)
from tools.lib.utils import bytes_to_gb, bytes_to_tb, format_number


# Global cache for API responses (disabled by default, enable via env var)
_response_cache = ResponseCache(cache_dir=".cache", ttl_seconds=7200)  # 2 hour TTL

# Global circuit breakers for each API endpoint
_traffic_circuit_breaker = CircuitBreaker(
    failure_threshold=3, recovery_timeout=30, success_threshold=2, name="Traffic API"
)

_emissions_circuit_breaker = CircuitBreaker(
    failure_threshold=3, recovery_timeout=30, success_threshold=2, name="Emissions API"
)


def reset_circuit_breakers():
    """Reset all circuit breakers to CLOSED state. Useful for testing."""
    _traffic_circuit_breaker.reset()
    _emissions_circuit_breaker.reset()


def get_circuit_breaker_states() -> dict:
    """Get current state of all circuit breakers."""
    return {
        "traffic": _traffic_circuit_breaker.get_state(),
        "emissions": _emissions_circuit_breaker.get_state(),
    }


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return _response_cache.get_stats()


def clear_cache() -> int:
    """
    Clear all cached API responses.

    Returns:
        Number of cache files deleted
    """
    return _response_cache.clear()


def setup_authentication(config_loader: Optional[ConfigLoader] = None) -> EdgeGridAuth:
    """
    Initialize Akamai EdgeGrid authentication.

    Args:
        config_loader: Optional ConfigLoader instance to get edgerc section name.
                      If not provided, defaults to "default" section.

    Returns:
        EdgeGridAuth: Configured authentication object

    Raises:
        Exception: If authentication setup fails
    """
    try:
        edgerc = EdgeRc("~/.edgerc")
        section = config_loader.get_edgerc_section() if config_loader else "default"
        auth = EdgeGridAuth.from_edgerc(edgerc, section)
        logger.info("✅ 認證設定成功")
        return auth
    except Exception as e:
        logger.error(f"❌ 認證設定失敗: {e}")
        raise


def _make_api_request_with_retry(
    url: str,
    params: Dict[str, str],
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
    api_type: str = "Traffic",
) -> Optional[Dict[str, Any]]:
    """
    Generic API request handler with exponential backoff retry and tracing.

    This private function handles the common HTTP retry logic for both
    Traffic and Emissions APIs, eliminating code duplication.

    Args:
        url (str): API endpoint URL
        params (dict): Query parameters (start, end dates)
        payload (dict): Request body
        auth: EdgeGrid authentication object
        config_loader: Configuration instance
        api_type (str): API name for logging ("Traffic" or "Emissions")

    Returns:
        dict: API response data or None if failed

    Raises:
        APIAuthenticationError: If authentication fails (401)
        APIAuthorizationError: If authorization fails (403)
        APIRateLimitError: If rate limit exceeded (429)
        APIServerError: If server error occurs (500+)
        APITimeoutError: If request times out
        APINetworkError: If network error occurs
    """
    # Setup correlation ID and request context for tracing
    if not get_correlation_id():
        set_correlation_id(generate_correlation_id())

    # Create request context
    req_context = RequestContext(
        correlation_id=get_correlation_id() or "unknown",
        api_endpoint=f"{api_type} API: {url}",
        params={"start": params.get("start"), "end": params.get("end")},
        metadata={"api_type": api_type, "attempt": 0},
    )
    set_current_context(req_context)

    max_retries = config_loader.get_max_retries()

    for attempt in range(max_retries):
        try:
            # Update attempt metadata
            req_context.metadata["attempt"] = attempt + 1

            correlation_id = get_correlation_id()
            logger.info(
                f"📡 發送 V2 {api_type} API 請求 (嘗試 {attempt + 1}/{max_retries}) "
                f"[{correlation_id}]"
            )

            response = requests.post(
                url,
                params=params,
                json=payload,
                auth=auth,
                timeout=config_loader.get_request_timeout(),
            )

            duration_ms = req_context.get_duration_ms()
            logger.info(
                f"📊 API 回應狀態: {response.status_code} (耗時: {duration_ms:.0f}ms)"
            )

            # Delegate to status handler
            result = _handle_response_status(
                response, attempt, max_retries, config_loader, api_type
            )
            # If result is not None, we got a successful response
            if result is not None:
                return result
            # Otherwise, continue to next retry attempt

        except requests.exceptions.Timeout as e:
            # Capture error context for timeout
            error_ctx = ErrorContext.from_exception(
                e, additional_context={"attempt": attempt + 1, "url": url}
            )
            logger.debug(f"Timeout error context: {error_ctx.to_dict()}")
            _handle_timeout_retry(attempt, max_retries)
        except requests.exceptions.RequestException as e:
            # Capture error context for network errors
            error_ctx = ErrorContext.from_exception(
                e,
                additional_context={
                    "attempt": attempt + 1,
                    "url": url,
                    "duration_ms": req_context.get_duration_ms(),
                },
            )
            logger.debug(f"Network error context: {error_ctx.to_dict()}")
            _handle_network_retry(e, attempt, max_retries, config_loader)

    return None


def _handle_response_status(
    response: requests.Response,
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader,
    api_type: str,
) -> Optional[Dict[str, Any]]:
    """
    Handle HTTP response status codes with appropriate actions.

    Args:
        response: HTTP response object
        attempt (int): Current retry attempt number
        max_retries (int): Maximum retry attempts
        config_loader: Configuration instance
        api_type (str): API type for logging

    Returns:
        dict: Response data on success

    Raises:
        Various API exceptions based on status code
    """
    status = response.status_code

    if status == 200:
        return _handle_success_response(response, config_loader, api_type)
    elif status == 400:
        logger.error(f"❌ 請求參數錯誤: {response.text}")
        raise APIRequestError(400, response.text)
    elif status == 401:
        logger.error("❌ 認證失敗")
        raise APIAuthenticationError("Authentication failed (401)")
    elif status == 403:
        logger.error("❌ 授權不足")
        raise APIAuthorizationError("Authorization failed (403)")
    elif status == 429:
        _handle_rate_limit(attempt, max_retries, config_loader)
    elif status >= 500:
        _handle_server_error(status, attempt, max_retries, config_loader)
    else:
        logger.error(f"❌ 未預期的狀態碼: {status}")
        raise APIRequestError(status, f"Unexpected status code: {status}")


def _handle_success_response(
    response: requests.Response, config_loader: ConfigLoader, api_type: str
) -> Dict[str, Any]:
    """
    Handle successful API response (200 OK) with optional schema validation.

    Args:
        response: HTTP response object
        config_loader: Configuration instance
        api_type (str): API type ("Traffic" or "Emissions")

    Returns:
        dict: Parsed JSON response data

    Raises:
        APIRequestError: If schema validation fails
    """
    data = response.json()
    data_points = len(data.get("data", []))
    logger.info(f"✅ 成功! 返回 {data_points:,} 個數據點")

    # Check data point limit only for Traffic API
    if api_type == "Traffic":
        _check_data_point_limit(data_points, config_loader)

    # Optional schema validation (disabled by default for backward compatibility)
    env_validate = os.getenv("ENABLE_SCHEMA_VALIDATION", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if env_validate:
        _validate_response_schema(data, api_type)

    return data


def _validate_response_schema(data: Dict[str, Any], api_type: str) -> None:
    """
    Validate API response against Pydantic schema.

    Args:
        data: API response data
        api_type: API type ("Traffic" or "Emissions")

    Raises:
        APIRequestError: If validation fails
    """
    try:
        if api_type == "Traffic":
            TrafficAPIResponse(**data)
            logger.debug(f"✅ Schema validation passed for {api_type} API")
        elif api_type == "Emissions":
            EmissionsAPIResponse(**data)
            logger.debug(f"✅ Schema validation passed for {api_type} API")
    except ValidationError as e:
        error_msg = f"Schema validation failed for {api_type} API: {e}"
        logger.error(f"❌ {error_msg}")
        raise APIRequestError(422, error_msg) from e


def _check_data_point_limit(data_points: int, config_loader: ConfigLoader) -> None:
    """
    Check if data points are approaching the limit and warn.

    Args:
        data_points (int): Number of data points returned
        config_loader: Configuration instance
    """
    limit = config_loader.get_data_point_limit()
    threshold = config_loader.get_data_point_warning_threshold()

    if data_points >= limit * threshold:
        logger.warning(f"⚠️  警告: 接近數據點限制 ({data_points:,}/{limit:,})")


def _handle_rate_limit(
    attempt: int, max_retries: int, config_loader: ConfigLoader
) -> None:
    """
    Handle rate limit error (429) with retry.

    Args:
        attempt (int): Current retry attempt
        max_retries (int): Maximum retries
        config_loader: Configuration instance

    Raises:
        APIRateLimitError: If max retries exceeded
    """
    logger.info("⏳ 速率限制，等待重試...")

    if attempt < max_retries - 1:
        backoff_base = config_loader.get_exponential_backoff_base()
        time.sleep(backoff_base**attempt)
        # Will retry in next iteration
    else:
        raise APIRateLimitError()


def _handle_server_error(
    status_code: int, attempt: int, max_retries: int, config_loader: ConfigLoader
) -> None:
    """
    Handle server error (500+) with retry.

    Args:
        status_code (int): HTTP status code
        attempt (int): Current retry attempt
        max_retries (int): Maximum retries
        config_loader: Configuration instance

    Raises:
        APIServerError: If max retries exceeded
    """
    logger.info(f"🔧 伺服器錯誤 ({status_code})，等待重試...")

    if attempt < max_retries - 1:
        backoff_base = config_loader.get_exponential_backoff_base()
        time.sleep(backoff_base**attempt)
        # Will retry in next iteration
    else:
        raise APIServerError(status_code)


def _handle_timeout_retry(attempt: int, max_retries: int) -> None:
    """
    Handle timeout error with retry.

    Args:
        attempt (int): Current retry attempt
        max_retries (int): Maximum retries

    Raises:
        APITimeoutError: If max retries exceeded
    """
    logger.info("⏱️  請求超時，嘗試重試...")

    if attempt >= max_retries - 1:
        raise APITimeoutError("Request timeout after all retries")


def _handle_network_retry(
    error: requests.exceptions.RequestException,
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader,
) -> None:
    """
    Handle network error with retry.

    Args:
        error: Original RequestException
        attempt (int): Current retry attempt
        max_retries (int): Maximum retries
        config_loader: Configuration instance

    Raises:
        APINetworkError: If max retries exceeded
    """
    logger.info(f"🌐 網路錯誤: {error}")

    if attempt < max_retries - 1:
        time.sleep(config_loader.get_network_error_delay())
        # Will retry in next iteration
    else:
        raise APINetworkError(f"Network error: {error}") from error


def call_traffic_api(
    start_date: str,
    end_date: str,
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
    use_cache: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Call V2 Traffic API with retry mechanism and circuit breaker protection.

    Simplified wrapper around generic request handler with circuit breaker and optional caching.

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        payload (dict): Request payload
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration
        use_cache (bool): Enable response caching (default: False)

    Returns:
        dict: API response data or None if failed

    Raises:
        APIRequestError: If request fails with 400 or unexpected status code
        APIAuthenticationError: If authentication fails (401)
        APIAuthorizationError: If authorization fails (403)
        APIRateLimitError: If rate limit exceeded (429)
        APIServerError: If server error occurs (500+)
        APITimeoutError: If request times out
        APINetworkError: If network error occurs
        CircuitBreakerOpenError: If circuit breaker is open

    Environment Variables:
        ENABLE_API_CACHE: Set to "1" or "true" to enable caching
    """
    import os

    # Check environment variable for cache enablement
    env_cache = os.getenv("ENABLE_API_CACHE", "").lower() in ("1", "true", "yes")
    enable_cache = use_cache or env_cache

    url = config_loader.get_api_endpoints()["traffic"]
    params = {"start": start_date, "end": end_date}

    if enable_cache:
        # Use cache with circuit breaker
        return _response_cache.cached_call(
            lambda **kw: _traffic_circuit_breaker.call(
                _make_api_request_with_retry,
                kw["url"],
                kw["params"],
                kw["payload"],
                kw["auth"],
                kw["config_loader"],
                "Traffic",
            ),
            "call_traffic_api",
            url=url,
            params=params,
            payload=payload,
            auth=auth,
            config_loader=config_loader,
        )
    else:
        # Direct call with circuit breaker only
        return _traffic_circuit_breaker.call(
            _make_api_request_with_retry,
            url,
            params,
            payload,
            auth,
            config_loader,
            "Traffic",
        )


def get_total_edge_traffic(
    start_date: str, end_date: str, auth: EdgeGridAuth, config_loader: ConfigLoader
) -> Dict[str, Any]:
    """
    Get total edge traffic for all CP codes using time5minutes dimension

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        dict: Contains total_tb, data_points, success status
    """
    all_cp_codes = config_loader.get_cp_codes()
    logger.info(f"\n🔍 查詢總體 Edge 流量 (所有 {len(all_cp_codes)} 個 CP codes)")

    payload = {
        "dimensions": ["time5minutes"],
        "metrics": ["edgeBytesSum"],
        "filters": [
            {
                "dimensionName": "cpcode",
                "operator": "IN_LIST",
                "expressions": all_cp_codes,
            }
        ],
        "sortBys": [{"name": "time5minutes", "sortOrder": "ASCENDING"}],
        "limit": config_loader.get_data_point_limit(),
    }

    try:
        data = call_traffic_api(start_date, end_date, payload, auth, config_loader)
        if not data:
            return {"success": False, "error": "No data returned"}

        # Calculate total edge traffic
        total_edge_bytes = sum(entry.get("edgeBytesSum", 0) for entry in data["data"])
        total_edge_tb = bytes_to_tb(total_edge_bytes)

        logger.info(f"📊 總 Edge 流量: {format_number(total_edge_tb)} TB")

        # Calculate billing estimate
        billing_coefficient = config_loader.get_billing_coefficient()
        billing_estimate = total_edge_tb * billing_coefficient
        logger.info(
            f"💰 預估計費用量: {format_number(billing_estimate)} TB (×{billing_coefficient})"
        )

        return {
            "success": True,
            "total_tb": total_edge_tb,
            "total_bytes": total_edge_bytes,
            "billing_estimate": billing_estimate,
            "data_points": len(data["data"]),
            "raw_data": data,
        }

    except Exception as e:
        logger.error(f"❌ 總體流量查詢失敗: {e}")
        return {"success": False, "error": str(e)}


def get_service_traffic(
    cp_code: str,
    start_date: str,
    end_date: str,
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
) -> Dict[str, Any]:
    """
    Get traffic for a specific service (CP code) using time5minutes dimension

    Args:
        cp_code (str): CP code to query
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        dict: Contains traffic data for the specific service
    """
    service_mappings = config_loader.get_service_mappings()
    service_info = service_mappings.get(
        cp_code, {"name": f"CP {cp_code}", "unit": "TB"}
    )
    logger.info(f"🔍 查詢 {service_info['name']} ({cp_code}) 流量")

    payload = {
        "dimensions": ["time5minutes"],
        "metrics": ["edgeBytesSum"],
        "filters": [
            {"dimensionName": "cpcode", "operator": "IN_LIST", "expressions": [cp_code]}
        ],
        "sortBys": [{"name": "time5minutes", "sortOrder": "ASCENDING"}],
        "limit": config_loader.get_data_point_limit(),
    }

    try:
        data = call_traffic_api(start_date, end_date, payload, auth, config_loader)
        if not data:
            return {"success": False, "error": "No data returned"}

        # Calculate service traffic
        total_edge_bytes = sum(entry.get("edgeBytesSum", 0) for entry in data["data"])

        # Convert to appropriate unit
        if service_info["unit"] == "TB":
            traffic_value = bytes_to_tb(total_edge_bytes)
            unit = "TB"
        else:  # GB
            traffic_value = bytes_to_gb(total_edge_bytes)
            unit = "GB"

        logger.info(f"📊 {service_info['name']}: {format_number(traffic_value)} {unit}")

        return {
            "success": True,
            "cp_code": cp_code,
            "name": service_info["name"],
            "traffic_value": traffic_value,
            "unit": unit,
            "total_bytes": total_edge_bytes,
            "data_points": len(data["data"]),
            "raw_data": data,
        }

    except Exception as e:
        logger.error(f"❌ {service_info['name']} 流量查詢失敗: {e}")
        return {"success": False, "error": str(e), "cp_code": cp_code}


def get_all_service_traffic(
    start_date: str,
    end_date: str,
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
    use_concurrent: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Get traffic for all predefined services.

    Can execute requests sequentially or concurrently based on use_concurrent flag.

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration
        use_concurrent (bool): Use concurrent execution (default: True)

    Returns:
        dict: Contains traffic data for all services
    """
    service_mappings = config_loader.get_service_mappings()
    logger.info("\n🔍 查詢所有個別服務流量")

    cp_codes = list(service_mappings.keys())

    if not cp_codes:
        logger.warning("⚠️  No services configured")
        return {}

    if use_concurrent and len(cp_codes) > 1:
        # Concurrent execution for better performance
        client = ConcurrentAPIClient(
            max_workers=min(3, len(cp_codes)),  # Limit to 3 concurrent requests
            rate_limit_delay=config_loader.get_rate_limit_delay(),
        )

        results = client.execute_batch(
            get_service_traffic,
            cp_codes,
            start_date=start_date,
            end_date=end_date,
            auth=auth,
            config_loader=config_loader,
        )

        client.shutdown()
        return results
    else:
        # Sequential execution (legacy behavior)
        results = {}
        for cp_code in cp_codes:
            result = get_service_traffic(
                cp_code, start_date, end_date, auth, config_loader
            )
            results[cp_code] = result

            # Add small delay between requests to be nice to the API
            time.sleep(config_loader.get_rate_limit_delay())

        return results


def call_emissions_api(
    start_date: str,
    end_date: str,
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
) -> Optional[Dict[str, Any]]:
    """
    Call V2 Emissions API with retry mechanism and circuit breaker protection.

    Simplified wrapper around generic request handler with circuit breaker.

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        payload (dict): Request payload
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        dict: API response data or None if failed

    Raises:
        APIRequestError: If request fails with 400 or unexpected status code
        APIAuthenticationError: If authentication fails (401)
        APIAuthorizationError: If authorization fails (403)
        APIRateLimitError: If rate limit exceeded (429)
        APIServerError: If server error occurs (500+)
        APITimeoutError: If request times out
        APINetworkError: If network error occurs
        CircuitBreakerOpenError: If circuit breaker is open
    """
    url = config_loader.get_api_endpoints()["emissions"]
    params = {"start": start_date, "end": end_date}

    # Use circuit breaker to protect against cascading failures
    return _emissions_circuit_breaker.call(
        _make_api_request_with_retry,
        url,
        params,
        payload,
        auth,
        config_loader,
        "Emissions",
    )


def get_regional_traffic(
    country_code: str,
    start_date: str,
    end_date: str,
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
) -> Dict[str, Any]:
    """
    Get edge traffic for a specific region using time1day dimension

    Args:
        country_code (str): Country code (ID, TW, SG)
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration

    Returns:
        dict: Contains regional traffic data
    """
    region_mappings = config_loader.get_region_mappings()
    region_name = region_mappings.get(country_code, country_code)
    logger.info(f"🔍 查詢 {region_name} ({country_code}) Edge 流量")

    payload = {
        "dimensions": ["time1day", "country"],
        "metrics": ["edgeBytesSum"],
        "filters": [
            {
                "dimensionName": "cpcode",
                "operator": "IN_LIST",
                "expressions": config_loader.get_cp_codes(),
            },
            {
                "dimensionName": "country",
                "operator": "IN_LIST",
                "expressions": [country_code],
            },
        ],
        "sortBys": [{"name": "time1day", "sortOrder": "ASCENDING"}],
        "limit": config_loader.get_data_point_limit(),
    }

    try:
        data = call_emissions_api(start_date, end_date, payload, auth, config_loader)
        if not data:
            return {"success": False, "error": "No data returned"}

        # Calculate regional traffic
        total_edge_bytes = sum(entry.get("edgeBytesSum", 0) for entry in data["data"])
        total_edge_tb = bytes_to_tb(total_edge_bytes)

        logger.info(f"📊 {region_name}: {format_number(total_edge_tb)} TB")

        return {
            "success": True,
            "country_code": country_code,
            "region_name": region_name,
            "total_tb": total_edge_tb,
            "total_bytes": total_edge_bytes,
            "data_points": len(data["data"]),
            "raw_data": data,
        }

    except Exception as e:
        logger.error(f"❌ {region_name} 流量查詢失敗: {e}")
        return {"success": False, "error": str(e), "country_code": country_code}


def get_all_regional_traffic(
    start_date: str,
    end_date: str,
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
    use_concurrent: bool = True,
) -> Dict[str, Any]:
    """
    Get edge traffic for all target regions (ID, TW, SG).

    Can execute requests sequentially or concurrently based on use_concurrent flag.

    Args:
        start_date (str): Start date in ISO-8601 format
        end_date (str): End date in ISO-8601 format
        auth: EdgeGrid authentication object
        config_loader: ConfigLoader instance with loaded configuration
        use_concurrent (bool): Use concurrent execution (default: True)

    Returns:
        dict: Contains traffic data for all regions
    """
    logger.info("\n🔍 查詢所有地區 Edge 流量")

    target_regions = config_loader.get_target_regions()
    total_regional_traffic = 0
    successful_queries = 0

    if use_concurrent and len(target_regions) > 1:
        # Concurrent execution for better performance
        client = ConcurrentAPIClient(
            max_workers=min(3, len(target_regions)),  # Limit to 3 concurrent requests
            rate_limit_delay=config_loader.get_rate_limit_delay(),
        )

        results = client.execute_batch(
            get_regional_traffic,
            target_regions,
            start_date=start_date,
            end_date=end_date,
            auth=auth,
            config_loader=config_loader,
        )

        client.shutdown()
    else:
        # Sequential execution (legacy behavior)
        results = {}
        for country_code in target_regions:
            result = get_regional_traffic(
                country_code, start_date, end_date, auth, config_loader
            )
            results[country_code] = result

            # Add delay between requests
            time.sleep(config_loader.get_rate_limit_delay())

    # Calculate summary
    for _country_code, result in results.items():
        if result.get("success"):
            total_regional_traffic += result["total_tb"]
            successful_queries += 1

    # Add summary information
    results["_summary"] = {
        "total_regions": len(target_regions),
        "successful_queries": successful_queries,
        "total_regional_traffic_tb": total_regional_traffic,
        "success_rate": (
            (successful_queries / len(target_regions)) * 100 if target_regions else 0
        ),
    }

    logger.info(f"\n📊 地區流量總計: {format_number(total_regional_traffic)} TB")
    logger.info(f"✅ 成功查詢: {successful_queries}/{len(target_regions)} 個地區")

    return results
