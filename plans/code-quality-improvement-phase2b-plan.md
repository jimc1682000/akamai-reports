# Code Quality Improvement Plan - Phase 2B

**Project**: Akamai V2 Traffic Reports
**Branch**: `feature/refactor-weekly-report` (continue)
**Created**: 2025-10-02
**Status**: Planning
**Estimated Effort**: 15-22 hours (3-4 work days)

---

## Executive Summary

After completing Phase 2 refactoring (1080 lines → 138 lines, 87% reduction), Python-expert analysis identified high-ROI improvements that will further enhance code quality from A- to A+.

**Key Improvements**:
1. Eliminate 256 lines of duplicate HTTP retry logic (60% reduction in api_client.py)
2. Configure magic numbers for production flexibility
3. Complete type hint coverage (30% → 100%)
4. Implement custom exception hierarchy for precise error handling
5. Replace print() with Python logging framework

**Expected Outcomes**:
- Complexity: C(15) → A(3-4) for API functions
- Code duplication: 256 lines → 0 lines
- Type coverage: 30% → 100%
- Better error handling and debugging capabilities

---

## Background: Python-Expert Analysis Results

### Current State (Post-Phase 2):
- **Lines of Code**: 138 (main script), 500 (api_client), 223 (console_reporter)
- **Test Coverage**: 90.88% (153 tests passing)
- **Average Complexity**: A (3.98)
- **Overall Grade**: A- (Excellent)

### Identified Issues:

#### HIGH Priority:
1. **Code Duplication** (256 lines): `call_traffic_api()` and `call_emissions_api()` are 95% identical
2. **Magic Numbers**: Hardcoded delays (2**attempt, 0.5, 0.9) reduce configurability

#### MEDIUM Priority:
3. **Type Hints**: Only 30% coverage, need 100% for IDE support
4. **Generic Exceptions**: Using `Exception` instead of custom types
5. **Print Statements**: Should use Python logging framework

---

## Detailed Implementation Plan

### Step 1: Create Custom Exception Hierarchy (2-3 hours)

**Objective**: Replace generic `Exception` with domain-specific exception types for precise error handling.

#### New File: `tools/lib/exceptions.py`

```python
"""Custom exceptions for Akamai API operations"""

class AkamaiAPIError(Exception):
    """Base exception for all Akamai API errors"""
    pass

class APIRequestError(AkamaiAPIError):
    """Raised when API request fails (400 Bad Request)"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")

class APIAuthenticationError(AkamaiAPIError):
    """Raised when authentication fails (401)"""
    pass

class APIAuthorizationError(AkamaiAPIError):
    """Raised when authorization fails (403)"""
    pass

class APIRateLimitError(AkamaiAPIError):
    """Raised when rate limit exceeded (429)"""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after} seconds"
        super().__init__(msg)

class APIServerError(AkamaiAPIError):
    """Raised when server error occurs (500+)"""
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"Server error: HTTP {status_code}")

class APITimeoutError(AkamaiAPIError):
    """Raised when request times out"""
    pass

class APINetworkError(AkamaiAPIError):
    """Raised when network error occurs"""
    pass
```

#### Files to Update:
- `api_client.py`: Replace all `raise Exception(...)` with custom exceptions
- `weekly_traffic_report.py`: Add specific exception handling
- Test files: Update exception assertions

**Benefits**:
- Precise error catching and handling
- Better error messages and debugging
- Follows Python exception best practices

---

### Step 2: Configure Magic Numbers (1-2 hours)

**Objective**: Move hardcoded values to configuration for production tuning.

#### Update `config.template.json`:

Add new section under `"api"`:

```json
{
  "api": {
    "endpoints": { ... },
    "timeout": 60,
    "max_retries": 3,

    "retry_delays": {
      "_description": "Retry delay configurations",
      "exponential_backoff_base": 2,
      "_backoff_note": "Base for exponential backoff (delay = base^attempt)",
      "network_error_delay": 1.0,
      "_network_note": "Fixed delay after network errors (seconds)",
      "rate_limit_delay": 0.5,
      "_rate_limit_note": "Delay between API calls to avoid rate limiting (seconds)"
    },

    "thresholds": {
      "_description": "Warning and limit thresholds",
      "data_point_warning_ratio": 0.9,
      "_warning_note": "Warn when data points reach this ratio of limit (0.9 = 90%)"
    },

    "edgerc_section": "default",
    "_edgerc_note": "Section name in ~/.edgerc file to use for authentication"
  }
}
```

#### Update `config_loader.py`:

Add new getter methods:

```python
def get_exponential_backoff_base(self) -> int:
    """Get exponential backoff base for retry delays (default: 2)"""
    return self.config.get("api", {}).get("retry_delays", {}).get(
        "exponential_backoff_base", 2
    )

def get_network_error_delay(self) -> float:
    """Get delay for network errors (default: 1.0 seconds)"""
    return self.config.get("api", {}).get("retry_delays", {}).get(
        "network_error_delay", 1.0
    )

def get_rate_limit_delay(self) -> float:
    """Get delay between API calls (default: 0.5 seconds)"""
    return self.config.get("api", {}).get("retry_delays", {}).get(
        "rate_limit_delay", 0.5
    )

def get_data_point_warning_threshold(self) -> float:
    """Get threshold ratio for data point warning (default: 0.9)"""
    return self.config.get("api", {}).get("thresholds", {}).get(
        "data_point_warning_ratio", 0.9
    )

def get_edgerc_section(self) -> str:
    """Get EdgeRC section name (default: 'default')"""
    return self.config.get("api", {}).get("edgerc_section", "default")
```

#### Update `api_client.py`:

Replace hardcoded values:

```python
# Line 109, 117, 358, 366 - Replace:
time.sleep(2**attempt)
# With:
backoff_base = config_loader.get_exponential_backoff_base()
time.sleep(backoff_base ** attempt)

# Line 136, 385 - Replace:
time.sleep(1)
# With:
time.sleep(config_loader.get_network_error_delay())

# Line 293, 487 - Replace:
time.sleep(0.5)
# With:
time.sleep(config_loader.get_rate_limit_delay())

# Line 87 - Replace:
if data_points >= data_point_limit * 0.9:
# With:
threshold = config_loader.get_data_point_warning_threshold()
if data_points >= data_point_limit * threshold:

# Line 34 - Replace:
auth = EdgeGridAuth.from_edgerc(edgerc, "default")
# With:
section = config_loader.get_edgerc_section() if config_loader else "default"
auth = EdgeGridAuth.from_edgerc(edgerc, section)
```

**Benefits**:
- Production tuning without code changes
- Environment-specific configurations
- A/B testing of retry strategies

---

### Step 3: Extract API Retry Logic (4-6 hours)

**Objective**: Eliminate 256 lines of duplicate code by extracting common HTTP retry logic.

#### Refactor `api_client.py`:

**Current Structure**:
- `call_traffic_api()`: 97 lines (lines 45-141)
- `call_emissions_api()`: 90 lines (lines 301-390)
- 95% duplicate code

**New Structure**:

```python
from typing import Dict, Any, Optional, Callable
from akamai.edgegrid import EdgeGridAuth
import requests

# ==================== PRIVATE HELPER FUNCTIONS ====================

def _make_api_request_with_retry(
    url: str,
    params: Dict[str, str],
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader,
    api_type: str = "Traffic"
) -> Optional[Dict[str, Any]]:
    """
    Generic API request handler with exponential backoff retry.

    Args:
        url: API endpoint URL
        params: Query parameters (start, end dates)
        payload: Request body
        auth: EdgeGrid authentication object
        config_loader: Configuration instance
        api_type: API name for logging ("Traffic" or "Emissions")

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
    max_retries = config_loader.get_max_retries()

    for attempt in range(max_retries):
        try:
            logger.info(f"📡 發送 V2 {api_type} API 請求 (嘗試 {attempt + 1}/{max_retries})")

            response = requests.post(
                url,
                params=params,
                json=payload,
                auth=auth,
                timeout=config_loader.get_request_timeout(),
            )

            logger.info(f"📊 API 回應狀態: {response.status_code}")

            # Delegate to status handler
            return _handle_response_status(
                response, attempt, max_retries, config_loader, api_type
            )

        except requests.exceptions.Timeout:
            _handle_timeout_retry(attempt, max_retries)
        except requests.exceptions.RequestException as e:
            _handle_network_retry(e, attempt, max_retries, config_loader)

    return None


def _handle_response_status(
    response: requests.Response,
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader,
    api_type: str
) -> Dict[str, Any]:
    """
    Handle HTTP response status codes with appropriate actions.

    Raises appropriate exceptions or returns data on success.
    """
    status = response.status_code

    if status == 200:
        return _handle_success_response(response, config_loader, api_type)
    elif status == 400:
        logger.error(f"❌ 請求參數錯誤: {response.text}")
        raise APIRequestError(400, response.text)
    elif status == 401:
        logger.error("❌ 認證失敗")
        raise APIAuthenticationError("Authentication failed")
    elif status == 403:
        logger.error("❌ 授權不足")
        raise APIAuthorizationError("Authorization failed")
    elif status == 429:
        return _handle_rate_limit(attempt, max_retries, config_loader)
    elif status >= 500:
        return _handle_server_error(status, attempt, max_retries, config_loader)
    else:
        logger.error(f"❌ 未預期的狀態碼: {status}")
        raise APIRequestError(status, f"Unexpected status code: {status}")


def _handle_success_response(
    response: requests.Response,
    config_loader: ConfigLoader,
    api_type: str
) -> Dict[str, Any]:
    """Handle successful API response (200 OK)"""
    data = response.json()
    data_points = len(data.get("data", []))
    logger.info(f"✅ 成功! 返回 {data_points:,} 個數據點")

    # Check data point limit only for Traffic API
    if api_type == "Traffic":
        _check_data_point_limit(data_points, config_loader)

    return data


def _check_data_point_limit(data_points: int, config_loader: ConfigLoader) -> None:
    """Check if data points are approaching the limit and warn"""
    limit = config_loader.get_data_point_limit()
    threshold = config_loader.get_data_point_warning_threshold()

    if data_points >= limit * threshold:
        logger.warning(
            f"⚠️  警告: 接近數據點限制 ({data_points:,}/{limit:,})"
        )


def _handle_rate_limit(
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader
) -> None:
    """Handle rate limit error (429) with retry"""
    logger.warning("⏳ 速率限制，等待重試...")

    if attempt < max_retries - 1:
        backoff_base = config_loader.get_exponential_backoff_base()
        delay = backoff_base ** attempt
        time.sleep(delay)
        # Will retry in next iteration
    else:
        raise APIRateLimitError()


def _handle_server_error(
    status_code: int,
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader
) -> None:
    """Handle server error (500+) with retry"""
    logger.warning(f"🔧 伺服器錯誤 ({status_code})，等待重試...")

    if attempt < max_retries - 1:
        backoff_base = config_loader.get_exponential_backoff_base()
        delay = backoff_base ** attempt
        time.sleep(delay)
        # Will retry in next iteration
    else:
        raise APIServerError(status_code)


def _handle_timeout_retry(attempt: int, max_retries: int) -> None:
    """Handle timeout error with retry"""
    logger.warning("⏱️  請求超時，嘗試重試...")

    if attempt >= max_retries - 1:
        raise APITimeoutError("Request timeout after all retries")


def _handle_network_retry(
    error: requests.exceptions.RequestException,
    attempt: int,
    max_retries: int,
    config_loader: ConfigLoader
) -> None:
    """Handle network error with retry"""
    logger.warning(f"🌐 網路錯誤: {error}")

    if attempt < max_retries - 1:
        delay = config_loader.get_network_error_delay()
        time.sleep(delay)
        # Will retry in next iteration
    else:
        raise APINetworkError(f"Network error: {error}") from error


# ==================== PUBLIC API FUNCTIONS ====================

def call_traffic_api(
    start_date: str,
    end_date: str,
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader
) -> Optional[Dict[str, Any]]:
    """
    Call V2 Traffic API with retry mechanism.

    Simplified wrapper around generic request handler.
    """
    url = config_loader.get_api_endpoints()["traffic"]
    params = {"start": start_date, "end": end_date}
    return _make_api_request_with_retry(
        url, params, payload, auth, config_loader, "Traffic"
    )


def call_emissions_api(
    start_date: str,
    end_date: str,
    payload: Dict[str, Any],
    auth: EdgeGridAuth,
    config_loader: ConfigLoader
) -> Optional[Dict[str, Any]]:
    """
    Call V2 Emissions API with retry mechanism.

    Simplified wrapper around generic request handler.
    """
    url = config_loader.get_api_endpoints()["emissions"]
    params = {"start": start_date, "end": end_date}
    return _make_api_request_with_retry(
        url, params, payload, auth, config_loader, "Emissions"
    )
```

**Impact**:
- Lines: 256 → ~100 (60% reduction)
- Complexity: C(15) → A(3-4)
- Single source of truth for retry logic
- Easier to add new APIs

---

### Step 4: Complete Type Hints (3-4 hours)

**Objective**: Add comprehensive type annotations to all modules for IDE support and static analysis.

#### Import additions:

```python
from typing import Dict, List, Optional, Any, Tuple, Union
from akamai.edgegrid import EdgeGridAuth
```

#### Files to update with complete type hints:

1. **api_client.py** (all 8 functions)
2. **console_reporter.py** (2 functions)
3. **json_reporter.py** (1 function)
4. **time_handler.py** (5 functions)
5. **utils.py** (3 functions)
6. **weekly_traffic_report.py** (main function)

**Example - Before**:
```python
def get_total_edge_traffic(start_date, end_date, auth, config_loader):
    """Get total edge traffic..."""
```

**Example - After**:
```python
def get_total_edge_traffic(
    start_date: str,
    end_date: str,
    auth: EdgeGridAuth,
    config_loader: ConfigLoader
) -> Dict[str, Any]:
    """Get total edge traffic..."""
```

**Benefits**:
- IDE autocomplete and IntelliSense
- Catch type errors before runtime
- Better code documentation
- Enable mypy/pyright static analysis

---

### Step 5: Implement Python Logging (2-3 hours)

**Objective**: Replace print() with structured logging for better debugging and monitoring.

#### New File: `tools/lib/logger.py`

```python
"""
Centralized logging configuration for Akamai Traffic Reports.

Provides structured logging to both console and file with configurable levels.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "akamai_traffic",
    log_file: Optional[str] = "logs/weekly_report.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup and configure logger with console and file handlers.

    Args:
        name: Logger name
        log_file: Path to log file (None to disable file logging)
        console_level: Console logging level (default: INFO)
        file_level: File logging level (default: DEBUG)
        max_bytes: Max log file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler - with emoji support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_format = logging.Formatter(
        '%(message)s'  # Simple format for console (keep emoji)
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler - with detailed information
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(file_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance with optional custom name"""
    if name:
        return logging.getLogger(name)
    return logger
```

#### Update all modules:

Replace:
```python
print("✅ 認證設定成功")
print(f"❌ 認證設定失敗: {e}")
```

With:
```python
from tools.lib.logger import logger

logger.info("✅ 認證設定成功")
logger.error(f"❌ 認證設定失敗: {e}")
```

**Benefits**:
- Structured logs with timestamps and context
- Separate console and file logging
- Log rotation to prevent disk space issues
- Configurable log levels for debugging
- Better production monitoring

---

### Step 6: Minor Optimizations (1 hour)

#### 6.1 Fix List Comprehension (weekly_traffic_report.py:124)

**Before**:
```python
total_api_calls = (
    1
    + len([s for s in service_traffic.values() if s.get("success")])
    + regional_traffic.get("_summary", {}).get("successful_queries", 0)
)
```

**After**:
```python
total_api_calls = (
    1
    + sum(1 for s in service_traffic.values() if s.get("success"))
    + regional_traffic.get("_summary", {}).get("successful_queries", 0)
)
```

#### 6.2 Extract Complex Expression (console_reporter.py:165)

**Before**:
```python
print(f"   查詢成功率:                 {((len(successful_services) + regional_summary.get('successful_queries', 0)) / (len(service_traffic) + 3) * 100):.1f}%")
```

**After**:
```python
successful_count = len(successful_services) + regional_summary.get('successful_queries', 0)
total_queries = len(service_traffic) + 3
success_rate = (successful_count / total_queries * 100) if total_queries > 0 else 0.0
logger.info(f"   查詢成功率:                 {success_rate:.1f}%")
```

#### 6.3 Clean Up Redundant Comments

Remove decorative comment headers:
```python
# ==================== AUTHENTICATION SETUP ====================
# ==================== V2 TRAFFIC API QUERY MODULE ====================
```

These are redundant as module docstrings already provide this info.

---

### Step 7: Test Updates & Verification (2-3 hours)

#### 7.1 Update Test Files

**Files to update**:
- `tests/test_api_functions.py`: Update exception assertions
- `tests/test_integration.py`: Update exception handling tests
- `tests/test_config_loader.py`: Add tests for new config methods

**New test file**:
- `tests/test_exceptions.py`: Test custom exception hierarchy

#### 7.2 Verification Checklist

```bash
# 1. Run complete test suite
task test-coverage

# Expected: All 153 tests pass, coverage ≥ 90%

# 2. Run linter
task lint-fix

# Expected: No warnings after auto-fix

# 3. Run formatter
task format

# Expected: All files formatted

# 4. Complete CI pipeline
task ci

# Expected: All checks pass

# 5. Optional: Type checking
mypy tools/lib/ --strict

# Expected: No type errors
```

#### 7.3 Manual Testing

```bash
# Test with actual config
python weekly_traffic_report.py --help

# Test with manual date range
python weekly_traffic_report.py --start YYYY-MM-01 --end 2025-09-07
```

---

## File Impact Summary

### New Files (3):
- `tools/lib/exceptions.py` (~100 lines)
- `tools/lib/logger.py` (~80 lines)
- `tests/test_exceptions.py` (~50 lines)
- `logs/` directory (created automatically)

### Modified Files (12):
- `tools/lib/api_client.py` (500 → 350 lines, -30%)
- `tools/lib/config_loader.py` (+60 lines for new getters)
- `config.template.json` (+30 lines for new config)
- `weekly_traffic_report.py` (minor updates)
- `tools/lib/reporters/console_reporter.py` (add types + logging)
- `tools/lib/reporters/json_reporter.py` (add types + logging)
- `tools/lib/time_handler.py` (add types)
- `tools/lib/utils.py` (add types)
- `tests/test_api_functions.py` (update exception tests)
- `tests/test_integration.py` (update exception tests)
- `tests/test_config_loader.py` (add new tests)
- `.gitignore` (add logs/ directory)

---

## Success Metrics

### Quantitative:
- ✅ Code lines: api_client.py -150 lines (-30%)
- ✅ Complexity: All functions ≤ A(4)
- ✅ Duplication: 256 lines → 0 lines
- ✅ Type coverage: 100%
- ✅ Tests passing: 153/153
- ✅ Coverage: ≥ 90%

### Qualitative:
- ✅ Better error handling and debugging
- ✅ Production-tunable configuration
- ✅ Full IDE support with type hints
- ✅ Structured logging for monitoring
- ✅ Maintainable and extensible code

---

## Risk Mitigation

### Potential Issues:

1. **Breaking Tests**: Exception type changes may break existing tests
   - **Mitigation**: Update tests incrementally, run after each step

2. **Configuration Compatibility**: New config fields may break existing setups
   - **Mitigation**: All new fields have defaults, backward compatible

3. **Logging Overhead**: File logging may impact performance
   - **Mitigation**: Async handlers, log rotation, configurable levels

4. **Import Cycles**: New modules may create circular imports
   - **Mitigation**: Keep exceptions.py and logger.py as leaf modules

### Rollback Strategy:
- Each step creates a commit
- Can rollback any step independently
- Git branch protection ensures safety

---

## Timeline

### Recommended Schedule (4 work days):

**Day 1 (5-7 hours)**:
- Morning: Step 1 - Custom exceptions (2-3h)
- Afternoon: Step 2 - Configure magic numbers (1-2h)
- Evening: Step 6 - Minor optimizations (1h)
- Commit: "Add custom exceptions and configure magic numbers"

**Day 2 (4-6 hours)**:
- Full day: Step 3 - Extract API retry logic (4-6h)
- Commit: "Refactor API client to eliminate duplication"

**Day 3 (5-7 hours)**:
- Morning: Step 4 - Complete type hints (3-4h)
- Afternoon: Step 5 - Implement logging (2-3h)
- Commit: "Add type hints and implement logging framework"

**Day 4 (3-4 hours)**:
- Full morning: Step 7 - Test updates & verification (2-3h)
- Final commit: "Update tests and verify Phase 2B improvements"
- Create PR and review

---

## Next Steps After Phase 2B

### Optional Future Enhancements:
1. **Async API Calls**: Use asyncio for concurrent requests (8-10h)
2. **Dataclasses**: Replace dicts with structured dataclasses (4-6h)
3. **Configuration Validation**: Enhanced validation with pydantic (2-3h)
4. **Performance Profiling**: Identify and optimize bottlenecks (3-4h)
5. **Monitoring Dashboard**: Add metrics collection (10-15h)

---

## References

- Python Expert Analysis: Analysis completed 2025-10-02
- Phase 2 Refactoring: Commit `a02416b`
- Original Codebase: 1080 lines → 138 lines
- Test Suite: 153 tests, 90.88% coverage

---

## Approval & Sign-off

**Prepared by**: Claude Code (Python Expert Agent)
**Date**: 2025-10-02
**Status**: Ready for execution
**Approval**: [ ] Pending

---

*This plan follows software engineering best practices and Python community standards (PEP 8, PEP 257, PEP 484).*
