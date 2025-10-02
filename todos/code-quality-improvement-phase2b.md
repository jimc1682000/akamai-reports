# Code Quality Improvement Phase 2B - TODO List

**Branch**: `feature/refactor-weekly-report`
**Created**: 2025-10-02
**Status**: Not Started
**Plan**: `plans/code-quality-improvement-phase2b-plan.md`

---

## Progress Overview

- **Total Tasks**: 47
- **Completed**: 0
- **In Progress**: 0
- **Remaining**: 47
- **Estimated Total Time**: 15-22 hours

---

## Step 1: Create Custom Exception Hierarchy (2-3 hours)

### 1.1 Create exceptions.py Module
- [ ] 1.1.1 Create new file `tools/lib/exceptions.py`
- [ ] 1.1.2 Add module docstring explaining exception hierarchy
- [ ] 1.1.3 Implement base exception `AkamaiAPIError`
- [ ] 1.1.4 Implement `APIRequestError` with status_code and message
- [ ] 1.1.5 Implement `APIAuthenticationError` (401 errors)
- [ ] 1.1.6 Implement `APIAuthorizationError` (403 errors)
- [ ] 1.1.7 Implement `APIRateLimitError` with optional retry_after
- [ ] 1.1.8 Implement `APIServerError` with status_code (500+ errors)
- [ ] 1.1.9 Implement `APITimeoutError` for timeout scenarios
- [ ] 1.1.10 Implement `APINetworkError` for network failures
- [ ] 1.1.11 Add `__all__` export list
- [ ] 1.1.12 Run `ruff check` on exceptions.py

### 1.2 Update api_client.py to Use Custom Exceptions
- [ ] 1.2.1 Add import: `from tools.lib.exceptions import *`
- [ ] 1.2.2 Replace `raise Exception(f"Bad Request (400): {response.text}")` with `APIRequestError`
- [ ] 1.2.3 Replace `raise Exception("Authentication failed (401)")` with `APIAuthenticationError`
- [ ] 1.2.4 Replace `raise Exception("Authorization failed (403)")` with `APIAuthorizationError`
- [ ] 1.2.5 Replace `raise Exception("Rate limit exceeded (429)")` with `APIRateLimitError`
- [ ] 1.2.6 Replace `raise Exception(f"Server error ({status_code})")` with `APIServerError`
- [ ] 1.2.7 Replace `raise Exception("Request timeout")` with `APITimeoutError`
- [ ] 1.2.8 Replace `raise Exception(f"Network error: {e}")` with `APINetworkError` (add `from e`)
- [ ] 1.2.9 Replace `raise Exception(f"Unexpected status code...")` with `APIRequestError`
- [ ] 1.2.10 Update docstrings to document raised exceptions
- [ ] 1.2.11 Apply same changes to `call_emissions_api()` function

### 1.3 Update weekly_traffic_report.py Error Handling
- [ ] 1.3.1 Add import: `from tools.lib.exceptions import *`
- [ ] 1.3.2 Add specific exception handling in main() function
- [ ] 1.3.3 Handle `APIAuthenticationError` with user-friendly message
- [ ] 1.3.4 Handle `APIRateLimitError` with retry suggestion
- [ ] 1.3.5 Handle `APITimeoutError` with network check suggestion
- [ ] 1.3.6 Keep generic `AkamaiAPIError` catch for other API errors

### 1.4 Update Tests for Custom Exceptions
- [ ] 1.4.1 Create `tests/test_exceptions.py`
- [ ] 1.4.2 Test each exception class instantiation
- [ ] 1.4.3 Test exception inheritance (all inherit from AkamaiAPIError)
- [ ] 1.4.4 Test exception message formatting
- [ ] 1.4.5 Update `tests/test_api_functions.py` exception assertions
- [ ] 1.4.6 Update `tests/test_integration.py` exception handling tests
- [ ] 1.4.7 Run test suite: `task test-coverage`
- [ ] 1.4.8 Verify all 153+ tests pass

### 1.5 Commit Step 1
- [ ] 1.5.1 Stage changes: `git add tools/lib/exceptions.py tools/lib/api_client.py weekly_traffic_report.py tests/`
- [ ] 1.5.2 Run pre-commit hooks: `git commit` (let hooks run)
- [ ] 1.5.3 Verify commit message clearly describes custom exception hierarchy
- [ ] 1.5.4 Push to remote branch

---

## Step 2: Configure Magic Numbers (1-2 hours)

### 2.1 Update Configuration Template
- [ ] 2.1.1 Open `config.template.json`
- [ ] 2.1.2 Add `retry_delays` section under `api`
- [ ] 2.1.3 Add `exponential_backoff_base: 2` with explanation comment
- [ ] 2.1.4 Add `network_error_delay: 1.0` with comment
- [ ] 2.1.5 Add `rate_limit_delay: 0.5` with comment
- [ ] 2.1.6 Add `thresholds` section under `api`
- [ ] 2.1.7 Add `data_point_warning_ratio: 0.9` with comment
- [ ] 2.1.8 Add `edgerc_section: "default"` under `api` with comment
- [ ] 2.1.9 Verify JSON syntax with `python -m json.tool config.template.json`

### 2.2 Update ConfigLoader Class
- [ ] 2.2.1 Open `tools/lib/config_loader.py`
- [ ] 2.2.2 Add method `get_exponential_backoff_base() -> int` (default: 2)
- [ ] 2.2.3 Add method `get_network_error_delay() -> float` (default: 1.0)
- [ ] 2.2.4 Add method `get_rate_limit_delay() -> float` (default: 0.5)
- [ ] 2.2.5 Add method `get_data_point_warning_threshold() -> float` (default: 0.9)
- [ ] 2.2.6 Add method `get_edgerc_section() -> str` (default: "default")
- [ ] 2.2.7 Add docstrings for all new methods
- [ ] 2.2.8 Add type hints for all new methods

### 2.3 Update api_client.py to Use Configuration
- [ ] 2.3.1 Find all `time.sleep(2**attempt)` (lines ~109, 117, 358, 366)
- [ ] 2.3.2 Replace with: `backoff_base = config_loader.get_exponential_backoff_base(); time.sleep(backoff_base ** attempt)`
- [ ] 2.3.3 Find all `time.sleep(1)` (lines ~136, 385)
- [ ] 2.3.4 Replace with: `time.sleep(config_loader.get_network_error_delay())`
- [ ] 2.3.5 Find all `time.sleep(0.5)` (lines ~293, 487)
- [ ] 2.3.6 Replace with: `time.sleep(config_loader.get_rate_limit_delay())`
- [ ] 2.3.7 Find `if data_points >= data_point_limit * 0.9` (line ~87)
- [ ] 2.3.8 Replace with: `threshold = config_loader.get_data_point_warning_threshold(); if data_points >= data_point_limit * threshold`
- [ ] 2.3.9 Update `setup_authentication()` to support configurable section
- [ ] 2.3.10 Update function signature: `setup_authentication(config_loader: ConfigLoader = None)`
- [ ] 2.3.11 Use `config_loader.get_edgerc_section()` if provided, else "default"

### 2.4 Update Tests for New Configuration
- [ ] 2.4.1 Open `tests/test_config_loader.py`
- [ ] 2.4.2 Add test for `get_exponential_backoff_base()`
- [ ] 2.4.3 Add test for `get_network_error_delay()`
- [ ] 2.4.4 Add test for `get_rate_limit_delay()`
- [ ] 2.4.5 Add test for `get_data_point_warning_threshold()`
- [ ] 2.4.6 Add test for `get_edgerc_section()`
- [ ] 2.4.7 Test default values when config missing
- [ ] 2.4.8 Update integration tests if needed
- [ ] 2.4.9 Run test suite: `task test-coverage`
- [ ] 2.4.10 Verify all tests pass

### 2.5 Commit Step 2
- [ ] 2.5.1 Stage changes: `git add config.template.json tools/lib/config_loader.py tools/lib/api_client.py tests/`
- [ ] 2.5.2 Commit with message: "Configure magic numbers for production flexibility"
- [ ] 2.5.3 Push to remote branch

---

## Step 3: Extract API Retry Logic (4-6 hours)

### 3.1 Design Private Helper Functions
- [ ] 3.1.1 Plan function signatures for all helper functions
- [ ] 3.1.2 Document data flow between helper functions
- [ ] 3.1.3 Identify shared vs API-specific logic

### 3.2 Implement Core Retry Logic
- [ ] 3.2.1 Create `_make_api_request_with_retry()` function
- [ ] 3.2.2 Add comprehensive docstring with Args, Returns, Raises
- [ ] 3.2.3 Add type hints for all parameters and return type
- [ ] 3.2.4 Implement retry loop structure
- [ ] 3.2.5 Add logging statements
- [ ] 3.2.6 Integrate exception handling for timeout and network errors

### 3.3 Implement Response Handlers
- [ ] 3.3.1 Create `_handle_response_status()` function
- [ ] 3.3.2 Implement status code routing logic (200, 400, 401, 403, 429, 500+)
- [ ] 3.3.3 Add logging for each status type
- [ ] 3.3.4 Create `_handle_success_response()` function
- [ ] 3.3.5 Implement data point limit checking
- [ ] 3.3.6 Create `_check_data_point_limit()` helper
- [ ] 3.3.7 Create `_handle_rate_limit()` function
- [ ] 3.3.8 Implement exponential backoff for rate limits
- [ ] 3.3.9 Create `_handle_server_error()` function
- [ ] 3.3.10 Implement exponential backoff for server errors

### 3.4 Implement Error Handlers
- [ ] 3.4.1 Create `_handle_timeout_retry()` function
- [ ] 3.4.2 Add retry logic or raise APITimeoutError
- [ ] 3.4.3 Create `_handle_network_retry()` function
- [ ] 3.4.4 Add delay and retry or raise APINetworkError with `from e`

### 3.5 Simplify Public API Functions
- [ ] 3.5.1 Refactor `call_traffic_api()` to 3-5 lines
- [ ] 3.5.2 Use `_make_api_request_with_retry()` wrapper
- [ ] 3.5.3 Update docstring to reference raised exceptions
- [ ] 3.5.4 Add complete type hints
- [ ] 3.5.5 Refactor `call_emissions_api()` to 3-5 lines
- [ ] 3.5.6 Use `_make_api_request_with_retry()` wrapper
- [ ] 3.5.7 Update docstring
- [ ] 3.5.8 Add complete type hints

### 3.6 Test Refactored Logic
- [ ] 3.6.1 Run existing API function tests: `pytest tests/test_api_functions.py -v`
- [ ] 3.6.2 Verify all 28 API tests still pass
- [ ] 3.6.3 Check test coverage for new helper functions
- [ ] 3.6.4 Add tests for edge cases if needed
- [ ] 3.6.5 Test timeout scenarios
- [ ] 3.6.6 Test rate limit scenarios
- [ ] 3.6.7 Test server error scenarios
- [ ] 3.6.8 Run full test suite: `task test-coverage`

### 3.7 Verify Code Quality
- [ ] 3.7.1 Run `ruff check tools/lib/api_client.py`
- [ ] 3.7.2 Check cyclomatic complexity: should be A(3-4) or better
- [ ] 3.7.3 Verify no code duplication between Traffic and Emissions
- [ ] 3.7.4 Check line count: should be ~350 lines (down from 500)
- [ ] 3.7.5 Run formatter: `task format`

### 3.8 Commit Step 3
- [ ] 3.8.1 Stage changes: `git add tools/lib/api_client.py tests/`
- [ ] 3.8.2 Commit with detailed message about eliminating 256 lines of duplication
- [ ] 3.8.3 Push to remote branch

---

## Step 4: Complete Type Hints (3-4 hours)

### 4.1 Add Type Imports
- [ ] 4.1.1 Add to all modules: `from typing import Dict, List, Optional, Any, Tuple`
- [ ] 4.1.2 Import domain types: `from akamai.edgegrid import EdgeGridAuth`
- [ ] 4.1.3 Import config type: `from tools.lib.config_loader import ConfigLoader`

### 4.2 Update api_client.py Type Hints
- [ ] 4.2.1 Add types to `setup_authentication()`
- [ ] 4.2.2 Add types to `call_traffic_api()` (already done in Step 3)
- [ ] 4.2.3 Add types to `call_emissions_api()` (already done in Step 3)
- [ ] 4.2.4 Add types to `get_total_edge_traffic()`
- [ ] 4.2.5 Add types to `get_service_traffic()`
- [ ] 4.2.6 Add types to `get_all_service_traffic()`
- [ ] 4.2.7 Add types to `get_regional_traffic()`
- [ ] 4.2.8 Add types to `get_all_regional_traffic()`
- [ ] 4.2.9 Add types to all private helper functions

### 4.3 Update console_reporter.py Type Hints
- [ ] 4.3.1 Add type hints to `generate_weekly_report()` parameters
- [ ] 4.3.2 Add return type `-> str` to `generate_weekly_report()`
- [ ] 4.3.3 Add type hints to `print_summary_stats()` parameters
- [ ] 4.3.4 Add return type `-> None` to `print_summary_stats()`

### 4.4 Update json_reporter.py Type Hints
- [ ] 4.4.1 Add type hints to `save_report_data()` parameters
- [ ] 4.4.2 Add return type `-> Optional[str]` to `save_report_data()`

### 4.5 Update time_handler.py Type Hints
- [ ] 4.5.1 Add type hints to `get_last_week_range()`
- [ ] 4.5.2 Add type hints to `get_last_week_range_with_config()`
- [ ] 4.5.3 Add type hints to `parse_date_string()`
- [ ] 4.5.4 Add type hints to `validate_time_range()`
- [ ] 4.5.5 Add type hints to `get_time_range()`
- [ ] 4.5.6 Add return type annotations (usually `-> str` or `-> Tuple[str, str]`)

### 4.6 Update utils.py Type Hints
- [ ] 4.6.1 Add type hints to `bytes_to_tb()` parameters and return
- [ ] 4.6.2 Add type hints to `bytes_to_gb()` parameters and return
- [ ] 4.6.3 Add type hints to `format_number()` parameters and return
- [ ] 4.6.4 Use `Union[int, float, str]` for flexible input types

### 4.7 Update weekly_traffic_report.py Type Hints
- [ ] 4.7.1 Add type hint to `main()` function: `-> int`
- [ ] 4.7.2 Add type hints to argparse setup if needed

### 4.8 Optional: Run mypy for Verification
- [ ] 4.8.1 Install mypy: `pip install mypy`
- [ ] 4.8.2 Run: `mypy tools/lib/ --ignore-missing-imports`
- [ ] 4.8.3 Fix any type errors found
- [ ] 4.8.4 Consider adding mypy to pre-commit hooks (optional)

### 4.9 Test Type Hints
- [ ] 4.9.1 Run full test suite: `task test-coverage`
- [ ] 4.9.2 Verify IDE autocomplete works (manually check in VSCode/PyCharm)
- [ ] 4.9.3 Check ruff linter: `task lint`
- [ ] 4.9.4 Verify no type-related warnings

### 4.10 Commit Step 4
- [ ] 4.10.1 Stage all modified files
- [ ] 4.10.2 Commit with message: "Add comprehensive type hints for IDE support"
- [ ] 4.10.3 Push to remote branch

---

## Step 5: Implement Python Logging (2-3 hours)

### 5.1 Create Logger Module
- [ ] 5.1.1 Create new file `tools/lib/logger.py`
- [ ] 5.1.2 Add module docstring
- [ ] 5.1.3 Import logging, logging.handlers, Path, Optional
- [ ] 5.1.4 Implement `setup_logger()` function with all parameters
- [ ] 5.1.5 Add console handler with emoji-friendly formatter
- [ ] 5.1.6 Add file handler with RotatingFileHandler
- [ ] 5.1.7 Configure file formatter with detailed info
- [ ] 5.1.8 Create `logs/` directory handling
- [ ] 5.1.9 Implement `get_logger()` helper function
- [ ] 5.1.10 Create global logger instance
- [ ] 5.1.11 Add comprehensive docstrings
- [ ] 5.1.12 Add type hints to all functions

### 5.2 Update .gitignore
- [ ] 5.2.1 Open `.gitignore`
- [ ] 5.2.2 Add `logs/` directory
- [ ] 5.2.3 Add `*.log` pattern
- [ ] 5.2.4 Verify .gitignore syntax

### 5.3 Update api_client.py with Logging
- [ ] 5.3.1 Add import: `from tools.lib.logger import logger`
- [ ] 5.3.2 Replace all `print()` with `logger.info()` for normal messages
- [ ] 5.3.3 Replace error prints with `logger.error()`
- [ ] 5.3.4 Replace warning prints with `logger.warning()`
- [ ] 5.3.5 Keep emoji in log messages for console readability
- [ ] 5.3.6 Add debug logs for detailed debugging (optional)

### 5.4 Update Other Modules with Logging
- [ ] 5.4.1 Update `weekly_traffic_report.py` with logging
- [ ] 5.4.2 Update `console_reporter.py` with logging
- [ ] 5.4.3 Update `json_reporter.py` with logging
- [ ] 5.4.4 Update `time_handler.py` with logging (if has print statements)
- [ ] 5.4.5 Update `config_loader.py` with logging

### 5.5 Test Logging Functionality
- [ ] 5.5.1 Run script and verify console output unchanged: `python weekly_traffic_report.py --help`
- [ ] 5.5.2 Check `logs/` directory is created
- [ ] 5.5.3 Verify log file is created: `logs/weekly_report.log`
- [ ] 5.5.4 Check log file contains detailed information
- [ ] 5.5.5 Test log rotation (create large log file, verify rotation)
- [ ] 5.5.6 Run test suite: `task test-coverage`

### 5.6 Commit Step 5
- [ ] 5.6.1 Stage changes: `git add tools/lib/logger.py tools/lib/ .gitignore`
- [ ] 5.6.2 Commit with message: "Implement Python logging framework"
- [ ] 5.6.3 Push to remote branch

---

## Step 6: Minor Optimizations (1 hour)

### 6.1 Fix List Comprehension in Main Script
- [ ] 6.1.1 Open `weekly_traffic_report.py`
- [ ] 6.1.2 Find line ~124 with list comprehension
- [ ] 6.1.3 Replace `len([s for s in ... if s.get("success")])` with `sum(1 for s in ... if s.get("success"))`
- [ ] 6.1.4 Test change: `python weekly_traffic_report.py --help`

### 6.2 Extract Complex Expression in Console Reporter
- [ ] 6.2.1 Open `tools/lib/reporters/console_reporter.py`
- [ ] 6.2.2 Find line ~165 with complex success rate calculation
- [ ] 6.2.3 Extract to three variables: `successful_count`, `total_queries`, `success_rate`
- [ ] 6.2.4 Add zero-division check: `if total_queries > 0 else 0.0`
- [ ] 6.2.5 Update print/log statement to use extracted variable

### 6.3 Clean Up Redundant Comments
- [ ] 6.3.1 Open `tools/lib/api_client.py`
- [ ] 6.3.2 Remove decorative comment: `# ==================== AUTHENTICATION SETUP ====================`
- [ ] 6.3.3 Remove decorative comment: `# ==================== V2 TRAFFIC API QUERY MODULE ====================`
- [ ] 6.3.4 Remove decorative comment: `# ==================== V2 EMISSIONS API QUERY MODULE ====================`
- [ ] 6.3.5 Keep meaningful inline comments

### 6.4 Standardize String Formatting
- [ ] 6.4.1 Search for any remaining % formatting or .format() calls
- [ ] 6.4.2 Replace with f-strings if found
- [ ] 6.4.3 Verify consistency across all modules

### 6.5 Test Optimizations
- [ ] 6.5.1 Run test suite: `task test-coverage`
- [ ] 6.5.2 Verify no behavior changes
- [ ] 6.5.3 Run linter: `task lint`

### 6.6 Commit Step 6
- [ ] 6.6.1 Stage changes
- [ ] 6.6.2 Commit with message: "Apply minor optimizations and code cleanup"
- [ ] 6.6.3 Push to remote branch

---

## Step 7: Test Updates & Final Verification (2-3 hours)

### 7.1 Review and Update Test Coverage
- [ ] 7.1.1 Run coverage report: `task test-coverage`
- [ ] 7.1.2 Check coverage for new modules (exceptions.py, logger.py)
- [ ] 7.1.3 Identify any uncovered code paths
- [ ] 7.1.4 Add tests for uncovered areas if significant

### 7.2 Run Complete Test Suite
- [ ] 7.2.1 Run all tests: `pytest -v`
- [ ] 7.2.2 Verify all tests pass (should be 153+ tests)
- [ ] 7.2.3 Check for any warnings or deprecations
- [ ] 7.2.4 Review test output for anomalies

### 7.3 Run Code Quality Checks
- [ ] 7.3.1 Run linter: `task lint-fix`
- [ ] 7.3.2 Verify no linting errors
- [ ] 7.3.3 Run formatter: `task format`
- [ ] 7.3.4 Verify all files formatted
- [ ] 7.3.5 Run complete CI: `task ci`
- [ ] 7.3.6 Verify all CI checks pass

### 7.4 Verify Complexity Improvements
- [ ] 7.4.1 Run complexity analysis on api_client.py
- [ ] 7.4.2 Verify no functions with complexity > B(10)
- [ ] 7.4.3 Confirm `call_traffic_api()` and `call_emissions_api()` are A(3-4)
- [ ] 7.4.4 Check overall average complexity

### 7.5 Manual Testing
- [ ] 7.5.1 Test help command: `python weekly_traffic_report.py --help`
- [ ] 7.5.2 Test with invalid dates: `python weekly_traffic_report.py --start invalid --end YYYY-MM-01`
- [ ] 7.5.3 Test automatic mode (if safe): `python weekly_traffic_report.py`
- [ ] 7.5.4 Check log files are created correctly
- [ ] 7.5.5 Verify console output is clean and readable

### 7.6 Code Review Checklist
- [ ] 7.6.1 Review all new files (exceptions.py, logger.py)
- [ ] 7.6.2 Review heavily modified files (api_client.py)
- [ ] 7.6.3 Check docstrings are complete and accurate
- [ ] 7.6.4 Verify type hints are comprehensive
- [ ] 7.6.5 Check for any remaining magic numbers
- [ ] 7.6.6 Verify logging is consistent across modules
- [ ] 7.6.7 Check error messages are user-friendly

### 7.7 Documentation Updates
- [ ] 7.7.1 Update `CLAUDE.md` if needed (architecture changes)
- [ ] 7.7.2 Update `README.md` if needed (new features)
- [ ] 7.7.3 Check if `PROJECT_STRUCTURE.md` needs updates
- [ ] 7.7.4 Verify all plan documents are accurate

### 7.8 Final Commit
- [ ] 7.8.1 Stage any remaining changes
- [ ] 7.8.2 Commit with message: "Phase 2B complete: Code quality improvements"
- [ ] 7.8.3 Push to remote branch

---

## Final Verification & Metrics

### Code Metrics Checklist
- [ ] **Line Count**: api_client.py reduced from 500 to ~350 lines (-30%)
- [ ] **Complexity**: All functions ≤ A(4), no C-rated functions
- [ ] **Duplication**: Zero duplicate code between Traffic/Emissions APIs
- [ ] **Type Coverage**: 100% type hints in all core modules
- [ ] **Test Coverage**: ≥ 90% (should be 90%+)
- [ ] **Tests Passing**: All 153+ tests passing
- [ ] **Linter**: No warnings or errors from ruff
- [ ] **Formatter**: All code formatted consistently

### Quality Checklist
- [ ] **Custom Exceptions**: Implemented and used throughout
- [ ] **Configuration**: All magic numbers moved to config
- [ ] **Logging**: Structured logging with file and console
- [ ] **Type Hints**: Complete coverage enables IDE support
- [ ] **Error Handling**: Precise and user-friendly
- [ ] **Documentation**: Docstrings complete and accurate
- [ ] **Tests**: Updated and passing
- [ ] **Performance**: No regression in execution time

### Success Criteria
- [ ] ✅ All 47 tasks completed
- [ ] ✅ All tests passing (153+ tests)
- [ ] ✅ Code coverage ≥ 90%
- [ ] ✅ No linting errors
- [ ] ✅ Complexity grade A
- [ ] ✅ Zero code duplication
- [ ] ✅ 100% type coverage
- [ ] ✅ Logging implemented
- [ ] ✅ Documentation updated
- [ ] ✅ All commits pushed

---

## Notes & Observations

**Issues Encountered**:
- [ ] Document any issues found during implementation
- [ ] Note any deviations from the plan
- [ ] Record any additional improvements made

**Performance Observations**:
- [ ] Record test execution time before and after
- [ ] Note any performance improvements or regressions
- [ ] Document memory usage if measured

**Lessons Learned**:
- [ ] What went well?
- [ ] What could be improved?
- [ ] Any surprises or unexpected challenges?

---

## Post-Completion

### Create Summary Report
- [ ] Document total time spent
- [ ] List key achievements
- [ ] Measure actual vs estimated effort
- [ ] Document metrics improvements
- [ ] Create before/after comparison

### Next Steps
- [ ] Review with team (if applicable)
- [ ] Consider PR to main branch
- [ ] Plan Phase 2C (async improvements, optional)
- [ ] Archive plan and TODO documents

---

**Status Legend**:
- [ ] Not started
- [~] In progress
- [✓] Completed
- [!] Blocked
- [x] Skipped

**Priority**:
- 🔴 Critical (breaks functionality)
- 🟡 Important (significant impact)
- 🟢 Normal (planned improvement)
- 🔵 Optional (nice to have)

---

*Last Updated: 2025-10-02*
*Total Tasks: 47*
*Estimated Time: 15-22 hours*
