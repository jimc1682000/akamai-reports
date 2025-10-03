# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Akamai V2 Traffic Reports** automation system that replaces deprecated V1 APIs. The main script `traffic.py` generates automated traffic reports (supports any time range, defaults to weekly) using Akamai's V2 Traffic and Emissions APIs.

**Critical Context**: This tool was developed to ensure business continuity as Akamai V1 Traffic Reports will be discontinued on 2025-11-05 (GUI) / 2026-02-05 (API).

## Core Commands

### Quick Start
```bash
# Setup complete development environment
task setup

# Run weekly report (recommended)
task run

# Run with manual date range
task run-manual START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD

# Compare V1 vs V2 API data for any date range
python tools/compare_v1_v2_apis.py --start YYYY-MM-01 --end YYYY-MM-30
```

### Configuration Setup
```bash
# 1. Copy configuration template
cp config.template.json config.json

# 2. Edit config.json with actual values (API endpoints, CP codes, etc.)
# Note: config.json is in .gitignore to prevent committing sensitive data

# 3. Verify configuration
task config-check
```

### Development Workflow
```bash
# Complete CI pipeline (quality + tests)
task ci

# Code quality checks
task quality          # Run linter + formatter
task lint-fix         # Auto-fix linting issues
task format           # Format code

# Testing
task test-coverage    # Full test suite with coverage
task test-quick       # Fast tests without coverage
task coverage-report  # Open HTML coverage report

# Pre-commit hooks
task pre-commit       # Run all hooks manually
pre-commit install    # Install hooks (done automatically by task setup)
```

### Dependencies Installation
```bash
# Development dependencies (includes testing tools)
pip install -r requirements-test.txt

# Production dependencies only
pip install requests akamai-edgegrid-auth
```

### Prerequisites
- Valid `.edgerc` file in user home directory for Akamai EdgeGrid authentication
- Properly configured `config.json` file (see config.template.json for structure)
- Python 3.8+
- Network access to Akamai APIs

## Architecture Overview

### Core Data Flow
1. **Configuration Loading**: Loads external config.json with all business parameters and API settings
2. **Time Calculation**: Automatically calculates last week based on configurable week definition or uses manual range
3. **V2 Traffic API**: Queries `time5minutes` dimension for edge traffic across configured CP codes
4. **V2 Emissions API**: Queries `time1day` dimension with country filtering (ID, TW, SG)
5. **Data Processing**: Aggregates data, converts units (Bytes → TB/GB), applies billing coefficient from config
6. **Report Generation**: Outputs formatted console report and JSON file

### Key Components

**Configuration System** (`config_loader.py`):
- External JSON configuration with validation
- Supports multiple week definitions (Sunday-Saturday, Monday-Sunday, Monday-Friday, custom)
- Template-based setup prevents sensitive data commits
- Business parameters (CP codes, billing coefficient) externalized from code

**Authentication Module** (`setup_authentication()`):
- Uses Akamai EdgeGrid authentication
- Reads from `~/.edgerc` default section

**Time Processing Module**:
- `get_last_week_range()`: Calculates configurable week cycles in UTC+0
- `get_time_range()`: Unified interface for auto/manual time handling with config support

**API Query Modules**:
- `call_traffic_api()`: V2 Traffic API with retry mechanism
- `call_emissions_api()`: V2 Emissions API with country filtering
- Both implement exponential backoff and error handling

**Response Caching (NEW)**:
- **File-Based Cache**: Development/testing optimization to reduce API calls
  - SHA256-based cache keys from function name and parameters
  - Configurable TTL (default: 2 hours for API responses)
  - Enable via `ENABLE_API_CACHE=1` environment variable
- **Cache Management**: Clear cache with `clear_cache()`, get stats with `get_cache_stats()`
- **Production Safe**: Disabled by default, only for development acceleration

**Response Schema Validation (NEW)**:
- **Pydantic Models**: Type-safe API response validation
  - TrafficAPIResponse/TrafficDataPoint for Traffic API
  - EmissionsAPIResponse/EmissionsDataPoint for Emissions API
  - Field validators: non-negative bytes, valid country codes, timestamp validation
- **Runtime Validation**: Enable via `ENABLE_SCHEMA_VALIDATION=1` environment variable
- **Error Reporting**: Returns 422 status code with detailed validation errors
- **Backward Compatible**: Disabled by default for zero performance impact

**Error Context and Tracing (NEW)**:
- **Correlation IDs**: Unique request identifiers for distributed tracing
  - UUID4-based correlation IDs automatically generated
  - Thread-safe context storage using contextvars
  - Included in all API request logs for log correlation
- **Request Context**: Comprehensive request tracking
  - API endpoint, parameters, metadata
  - Automatic duration tracking (milliseconds)
  - Request lifecycle management
- **Error Context**: Enhanced error debugging
  - Stack traces with correlation IDs
  - Request context capture at error time
  - Additional context for root cause analysis
- **Benefits**:
  - Better error debugging with full context
  - Request correlation across distributed systems
  - Performance monitoring with duration tracking
  - Production-ready error analysis

**Data Processing**:
- `bytes_to_tb()` / `bytes_to_gb()`: Unit conversion functions
- Billing estimation using coefficient 1.0 (derived from historical analysis)

### Critical Business Logic

**CP Code Mappings**:
- Total: Multiple CP codes for comprehensive traffic analysis (實際 CP codes 請查詢 Akamai Console)
- Specific services: 服務 1 (PLACEHOLDER_CP_CODE_001), 服務 2 (PLACEHOLDER_CP_CODE_002), 服務 3 (PLACEHOLDER_CP_CODE_003), 服務 4 (PLACEHOLDER_CP_CODE_004)
- Geographic regions: Region 1, Region 2, Region 3
- Note: Service mappings are configured in config.json

**API Dimension Requirements**:
- V2 Traffic API: MUST use `time5minutes` dimension
- V2 Emissions API: MUST use `time1day` dimension (does NOT support time5minutes)

**Time Handling**:
- Week definition: Sunday 00:00 UTC+0 to Saturday 23:59 UTC+0
- All times converted to ISO-8601 format for API calls
- Automatic mode calculates "last complete week"

**Billing Estimation Formula**:
```
Estimated Billing = Total Edge Traffic (TB) × 1.0
```
This coefficient (1.0) was derived from comparative analysis with actual billing data.

### Output Formats

**Console Report**: Structured, aligned output with emoji indicators and performance metrics

**JSON Export**: Timestamped files (`weekly_traffic_report_YYYYMMDD_HHMMSS.json`) containing:
- Raw API responses
- Processed metrics
- Billing calculations
- Metadata and timestamps

## Important Configuration

**API Endpoints**: Hardcoded to specific Akamai Luna instance
**Rate Limits**: 50,000 data points per API call (monitored and warned)
**Retry Logic**: 3 attempts with exponential backoff
**Timeout**: 60 seconds per request

## Testing & Quality Assurance

### Test Suite Overview
This project maintains **production-ready quality** with comprehensive testing:

- **213 test cases** across 8 test modules
- **83%+ code coverage** (architecture improvements fully tested)
- **Automated testing** on every commit via pre-commit hooks
- **Complete error handling** and edge case coverage

### Test Structure
```bash
test_config_loader.py     # Configuration system tests (38 tests)
test_time_functions.py    # Date/time handling tests (19 tests)
test_utility_functions.py # Utility function tests (43 tests)
test_api_functions.py     # API interaction tests (31 tests) - includes schema validation
test_report_functions.py  # Report generation tests (17 tests)
test_integration.py       # End-to-end integration tests (10 tests)
test_schema_validation.py # Schema validation tests (19 tests) - NEW
test_tracing.py           # Error context and tracing tests (16 tests) - NEW
```

### Running Tests
```bash
# Recommended: Use task commands
task test-coverage        # Full test suite with HTML coverage report
task test-quick           # Fast test run without coverage
task ci                   # Complete CI pipeline

# Direct pytest usage
python -m pytest --cov=. --cov-report=html --cov-fail-under=90 -v
python run_tests.py       # Custom test runner with detailed reporting
```

### Code Quality Standards
- **Ruff linter & formatter** - Modern Python code quality
- **Pre-commit hooks** - Automatic quality checks before commits
- **Configuration validation** - Prevents runtime configuration errors
- **Type hints and docstrings** - Comprehensive code documentation
- **Error handling patterns** - Robust error recovery and retry mechanisms

## Development Notes

### Code Modification Guidelines
When modifying this code:
- **Run tests first**: `task ci` before making changes
- **Maintain test coverage**: Add tests for new functionality
- **Follow code quality**: Pre-commit hooks ensure standards
- The billing coefficient (1.0) should only be changed based on new comparative analysis
- CP code lists are business-critical - changes require verification
- Time zone handling is strictly UTC+0 - do not modify without business approval
- API dimension choices (time5minutes vs time1day) are API-constraint driven, not preferences

### Configuration System
- **External configuration**: All sensitive data in `config.json` (gitignored)
- **Template system**: `config.template.json` for safe sharing
- **Validation layer**: Comprehensive validation prevents runtime errors
- **Flexible week definitions**: Support for different business week cycles

The script is production-ready with:
- **Comprehensive error handling** for network failures, authentication issues, and API rate limits
- **Retry mechanisms** with exponential backoff
- **Configuration validation** preventing common deployment issues
- **Extensive test coverage** ensuring reliability
