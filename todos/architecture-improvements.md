# Architecture Improvements TODO List

Based on architect-review recommendations, this document tracks all architectural improvements to be implemented.

## Status Legend
- [ ] Not Started
- [x] Completed
- [WIP] Work In Progress

---

## HIGH PRIORITY

### 1. Response Cache Security & Performance Enhancement
**Priority**: HIGH | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: Current cache uses pickle serialization which is slow and insecure (only 33.33% test coverage).

**Implementation Tasks**:
- [ ] Replace pickle with JSON serialization
- [ ] Store TTL timestamp in cache data structure
- [ ] Update cache key generation for JSON compatibility
- [ ] Add comprehensive cache tests (TTL expiration, cached_call, statistics)
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/cache/response_cache.py`
- `tests/test_response_cache.py` (new file)

**Estimated Time**: 2-3 hours

---

### 2. Retry Strategy with Jitter
**Priority**: HIGH | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Exponential backoff lacks jitter, can cause thundering herd problem.

**Implementation Tasks**:
- [ ] Create `_calculate_backoff_with_jitter()` function
- [ ] Update `_handle_rate_limit()` to use jitter
- [ ] Update `_handle_server_error()` to use jitter
- [ ] Add tests for jitter randomization
- [ ] Add configuration for max_delay parameter

**Files to Modify**:
- `tools/lib/api_client.py`
- `tests/test_api_functions.py`
- `config.template.json`

**Estimated Time**: 1-2 hours

---

### 3. Circuit Breaker Edge Case Tests
**Priority**: HIGH | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Circuit breaker coverage is 65.82% with missing HALF_OPEN state transitions.

**Implementation Tasks**:
- [ ] Add test for HALF_OPEN → OPEN transition on failure
- [ ] Add test for HALF_OPEN → CLOSED after success threshold
- [ ] Add test for time-based state recovery
- [ ] Add test for concurrent call handling
- [ ] Add test for state persistence across resets

**Files to Modify**:
- `tests/test_circuit_breaker.py` (new file)

**Estimated Time**: 2-3 hours

---

### 4. Input Validation & Sanitization
**Priority**: HIGH | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Date inputs from command line not validated before use.

**Implementation Tasks**:
- [ ] Create `validate_date_format()` function
- [ ] Add validation to argparse arguments
- [ ] Add tests for valid/invalid date formats
- [ ] Add error messages for invalid inputs
- [ ] Update documentation with date format examples

**Files to Modify**:
- `traffic.py`
- `tests/test_integration.py`

**Estimated Time**: 1 hour

---

### 5. Secrets Management
**Priority**: HIGH | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: Hardcoded `.edgerc` path, no support for environment variables or vaults.

**Implementation Tasks**:
- [ ] Create `tools/lib/secrets/` module
- [ ] Implement `SecretManager` class
- [ ] Add support for environment variables (AKAMAI_CLIENT_TOKEN, etc.)
- [ ] Add support for AWS Secrets Manager (optional)
- [ ] Update `setup_authentication()` to use SecretManager
- [ ] Add configuration for auth source selection
- [ ] Add tests for all secret sources
- [ ] Update documentation with secret management guide

**Files to Modify**:
- `tools/lib/secrets/__init__.py` (new)
- `tools/lib/secrets/manager.py` (new)
- `tools/lib/api_client.py`
- `config.template.json`
- `tests/test_secrets.py` (new)

**Estimated Time**: 4-5 hours

---

## MEDIUM PRIORITY

### 6. Service Container Lifecycle Management
**Priority**: MEDIUM | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: ServiceContainer lacks health checks and explicit initialization control.

**Implementation Tasks**:
- [ ] Add `initialize()` method for eager initialization
- [ ] Add `health_check()` method
- [ ] Add thread safety with lock
- [ ] Add `_initialized` flag
- [ ] Add tests for lifecycle management
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/container.py`
- `tests/test_container.py` (new)

**Estimated Time**: 2 hours

---

### 7. Timeout Strategy per API Type
**Priority**: MEDIUM | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Single timeout for all APIs - Traffic and Emissions may have different performance.

**Implementation Tasks**:
- [ ] Update config schema to support per-API timeouts
- [ ] Add `get_api_timeout(api_type)` to ConfigLoader
- [ ] Update `_make_api_request_with_retry()` to use API-specific timeout
- [ ] Add tests for timeout configuration
- [ ] Update config.template.json with examples

**Files to Modify**:
- `config.template.json`
- `tools/lib/config_loader.py`
- `tools/lib/api_client.py`
- `tests/test_config_loader.py`

**Estimated Time**: 1-2 hours

---

### 8. Concurrent Client Connection Pooling
**Priority**: MEDIUM | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: No connection reuse in concurrent client - creates new connections each time.

**Implementation Tasks**:
- [ ] Add requests.Session to ConcurrentAPIClient
- [ ] Configure HTTPAdapter with connection pooling
- [ ] Add `shutdown()` method for cleanup
- [ ] Update tests to verify connection reuse
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/http/concurrent_client.py`
- `tests/test_concurrent_client.py` (new)

**Estimated Time**: 2-3 hours

---

### 9. Type Hints Coverage with MyPy
**Priority**: MEDIUM | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Inconsistent type hints, no static type checking.

**Implementation Tasks**:
- [ ] Add comprehensive type hints to all modules
- [ ] Add MyPy to pre-commit hooks
- [ ] Fix all MyPy errors
- [ ] Add `py.typed` marker file
- [ ] Configure MyPy strictness level

**Files to Modify**:
- All `.py` files (gradual addition)
- `.pre-commit-config.yaml`
- `pyproject.toml` or `mypy.ini` (new)

**Estimated Time**: 4-6 hours (spread across multiple sessions)

---

### 10. Container & Cache Test Coverage
**Priority**: MEDIUM | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Container (50%) and Cache (33%) have insufficient test coverage.

**Implementation Tasks**:
- [ ] Add container lifecycle tests
- [ ] Add container reset tests
- [ ] Add lazy loading verification tests
- [ ] Add cache TTL expiration tests
- [ ] Add cached_call functionality tests
- [ ] Add cache statistics tests

**Files to Modify**:
- `tests/test_container.py` (new)
- `tests/test_response_cache.py` (new)

**Estimated Time**: 3-4 hours

---

### 11. Sensitive Data Log Sanitization
**Priority**: MEDIUM | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Potential for sensitive data leakage in debug logs.

**Implementation Tasks**:
- [ ] Create `SanitizingLogger` wrapper
- [ ] Add pattern matching for sensitive fields
- [ ] Update logger initialization to use sanitizer
- [ ] Add tests for log sanitization
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/logger.py`
- `tests/test_logger.py`

**Estimated Time**: 2 hours

---

### 12. Prometheus Metrics Integration
**Priority**: MEDIUM | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: No metrics collection for monitoring systems.

**Implementation Tasks**:
- [ ] Add prometheus_client dependency
- [ ] Create metrics module with counters/histograms
- [ ] Instrument API calls with metrics
- [ ] Add circuit breaker state gauge
- [ ] Add metrics export endpoint (optional)
- [ ] Add tests for metrics collection
- [ ] Update documentation

**Files to Modify**:
- `requirements.txt`
- `tools/lib/metrics/__init__.py` (new)
- `tools/lib/api_client.py`
- `tests/test_metrics.py` (new)

**Estimated Time**: 3-4 hours

---

## LOW PRIORITY

### 13. Configuration Validation with Pydantic
**Priority**: LOW | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Manual configuration validation - use Pydantic for schema validation.

**Implementation Tasks**:
- [ ] Create Pydantic models for config schema
- [ ] Update ConfigLoader to use Pydantic validation
- [ ] Add comprehensive validation tests
- [ ] Update error messages
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/config_loader.py`
- `tests/test_config_loader.py`

**Estimated Time**: 2-3 hours

---

### 14. Magic Numbers to Configuration
**Priority**: LOW | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Hardcoded values scattered in code (max_workers=3, etc.)

**Implementation Tasks**:
- [ ] Identify all magic numbers
- [ ] Add to config.template.json
- [ ] Update code to read from config
- [ ] Add tests for configurable values
- [ ] Update documentation

**Files to Modify**:
- `config.template.json`
- `tools/lib/api_client.py`
- `tools/lib/config_loader.py`
- `tests/test_config_loader.py`

**Estimated Time**: 1-2 hours

---

### 15. Architecture Decision Records (ADRs)
**Priority**: LOW | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: No formal documentation of architectural decisions.

**Implementation Tasks**:
- [ ] Create docs/adr/ directory
- [ ] Document circuit breaker decision
- [ ] Document dependency injection decision
- [ ] Document concurrent execution decision
- [ ] Document caching strategy
- [ ] Document tracing implementation
- [ ] Create ADR template

**Files to Create**:
- `docs/adr/0001-circuit-breaker-pattern.md`
- `docs/adr/0002-dependency-injection.md`
- `docs/adr/0003-concurrent-api-calls.md`
- `docs/adr/0004-response-caching.md`
- `docs/adr/0005-error-tracing.md`
- `docs/adr/template.md`

**Estimated Time**: 3-4 hours

---

### 16. API Documentation Enhancement
**Priority**: LOW | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: Some modules lack usage examples in docstrings.

**Implementation Tasks**:
- [ ] Add examples to all public API docstrings
- [ ] Add comprehensive parameter descriptions
- [ ] Add return value documentation
- [ ] Add exception documentation
- [ ] Generate API docs with Sphinx (optional)

**Files to Modify**:
- All public API modules

**Estimated Time**: 4-5 hours

---

### 17. Health Check Endpoint
**Priority**: LOW | **Complexity**: SIMPLE | **Status**: [ ]

**Issue**: No health check mechanism for monitoring.

**Implementation Tasks**:
- [ ] Create HealthChecker class
- [ ] Implement config/auth/circuit breaker checks
- [ ] Add cache health check
- [ ] Add version information
- [ ] Add tests
- [ ] Update documentation

**Files to Modify**:
- `tools/lib/health.py` (new)
- `tests/test_health.py` (new)

**Estimated Time**: 2 hours

---

## FUTURE ENHANCEMENTS (V3.0)

### 18. Circuit Breaker State Persistence
**Priority**: FUTURE | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: Circuit breaker state lost on restart.

**Note**: Deferred to future version - requires careful design for production deployment.

---

### 19. Abstract API Client Interface (Repository Pattern)
**Priority**: FUTURE | **Complexity**: MEDIUM | **Status**: [ ]

**Issue**: API client mixes HTTP logic and business logic.

**Note**: Deferred to V3.0 - requires significant refactoring.

---

### 20. Async/Await Migration
**Priority**: FUTURE | **Complexity**: COMPLEX | **Status**: [ ]

**Issue**: Thread-based concurrency - asyncio would be more efficient.

**Note**: Deferred to V3.0 - requires complete async rewrite.

---

## Implementation Order

### Phase 1: Quick Wins (1-2 days)
1. Input Validation & Sanitization
2. Retry Strategy with Jitter
3. Magic Numbers to Configuration
4. Timeout Strategy per API Type

### Phase 2: Testing & Quality (2-3 days)
5. Circuit Breaker Edge Case Tests
6. Container & Cache Test Coverage
7. Response Cache Security Enhancement

### Phase 3: Security & Observability (2-3 days)
8. Secrets Management
9. Sensitive Data Log Sanitization
10. Service Container Lifecycle Management

### Phase 4: Advanced Features (3-4 days)
11. Concurrent Client Connection Pooling
12. Prometheus Metrics Integration
13. Type Hints Coverage with MyPy

### Phase 5: Documentation (1-2 days)
14. Architecture Decision Records
15. API Documentation Enhancement
16. Health Check Endpoint
17. Configuration Validation with Pydantic

---

## Progress Tracking

**Total Items**: 20
**High Priority**: 5
**Medium Priority**: 7
**Low Priority**: 5
**Future**: 3

**Completed**: 0/20
**In Progress**: 0/20
**Not Started**: 20/20

**Last Updated**: 2025-10-04
