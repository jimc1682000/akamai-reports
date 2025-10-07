# ADR-0004: Dependency Injection with Service Container

**Date**: 2024-09-26
**Status**: Accepted
**Deciders**: Development Team

## Context

The original codebase had **tight coupling** between components with direct instantiation and global state:

```python
# Original approach - tight coupling
def call_traffic_api(cp_code, start, end):
    config = ConfigLoader("config.json")  # Direct instantiation
    config.load_config()

    # Hardcoded dependencies
    auth = setup_authentication(config)
    session = requests.Session()

    # Direct HTTP call
    response = session.get(url, auth=auth)
```

**Problems**:

1. **Untestable**: Cannot mock dependencies easily
2. **Tightly Coupled**: Functions create their own dependencies
3. **No Reusability**: Config loaded multiple times
4. **Hard to Test**: Requires actual config.json file
5. **No Lifecycle Management**: Resources not properly cleaned up
6. **Global State**: Singleton patterns scattered throughout

Example testing difficulty:
```python
# Original - requires actual config file
def test_call_traffic_api():
    result = call_traffic_api("123", start, end)  # Loads real config!
    assert result is not None
```

## Decision

We will implement **lightweight dependency injection using a ServiceContainer** with lazy initialization.

### Architecture

```
┌──────────────────────────────────┐
│      ServiceContainer            │
│                                  │
│  ┌────────────────────────────┐ │
│  │  Registered Services       │ │
│  │                            │ │
│  │  • config_loader           │ │
│  │  • auth_handler            │ │
│  │  • api_client              │ │
│  │  • circuit_breaker         │ │
│  │  • cache                   │ │
│  └────────────────────────────┘ │
│                                  │
│  Lazy Initialization             │
│  ├─ get() → creates on first use│
│  └─ reset() → clears cache      │
└──────────────────────────────────┘
```

### Implementation

**ServiceContainer Pattern**:
```python
class ServiceContainer:
    """Lightweight dependency injection container"""

    def __init__(self):
        self._services = {}
        self._instances = {}

    def register(self, name: str, factory: Callable):
        """Register a service factory"""
        self._services[name] = factory

    def get(self, name: str):
        """Get service (lazy initialization)"""
        if name not in self._instances:
            factory = self._services[name]
            self._instances[name] = factory()
        return self._instances[name]

    def reset(self):
        """Clear all cached instances"""
        self._instances.clear()
```

**Usage Pattern**:
```python
# Setup (in main script or test setup)
container = ServiceContainer()
container.register("config_loader", lambda: ConfigLoader("config.json"))
container.register("auth", lambda: setup_authentication(container.get("config_loader")))

# Use (in functions)
def call_traffic_api(cp_code, start, end, container):
    config = container.get("config_loader")
    auth = container.get("auth")
    # ... use dependencies
```

**Testing Benefits**:
```python
# Testing - inject mocks easily
def test_call_traffic_api():
    container = ServiceContainer()
    container.register("config_loader", lambda: MockConfigLoader())
    container.register("auth", lambda: MockAuth())

    result = call_traffic_api("123", start, end, container)
    assert result is not None  # No actual config file needed!
```

## Alternatives Considered

### Alternative 1: Full DI Framework (dependency-injector, injector)
**Pros**:
- Feature-rich (scopes, auto-wiring, providers)
- Well-tested and maintained
- Industry standard patterns

**Cons**:
- Heavy dependency for our use case
- Steep learning curve
- Over-engineering for a batch script
- Requires significant refactoring

**Reason for rejection**: Too heavyweight for our needs. ~100 lines of custom code vs 15KB+ dependency.

### Alternative 2: Function parameter injection (manual)
**Pros**:
- No framework needed
- Explicit dependencies
- Easy to understand

**Cons**:
- Function signatures become very long
- Tedious to pass dependencies down call stack
- No centralized lifecycle management

Example of parameter explosion:
```python
def call_traffic_api(cp_code, start, end, config, auth, session, circuit_breaker, cache):
    # 8 parameters!
```

**Reason for rejection**: Leads to parameter drilling and verbose function signatures.

### Alternative 3: Global singletons
**Pros**:
- Simple access pattern
- No parameter passing

**Cons**:
- Global state (hard to test)
- Hidden dependencies
- Thread-safety issues
- Initialization order problems

**Reason for rejection**: Makes testing difficult and hides dependencies.

## Consequences

### Positive

1. **Testability**: Easy to inject mocks for testing
   ```python
   container.register("api_client", lambda: MockAPIClient())
   ```

2. **Loose Coupling**: Functions depend on abstractions, not concrete implementations

3. **Lifecycle Management**:
   - Lazy initialization (only create when needed)
   - Centralized cleanup with `reset()`

4. **Configuration Hot-Reload**: `container.reset()` + reload config

5. **Clear Dependencies**: Container registration shows all dependencies upfront

6. **No External Dependencies**: Simple ~100 line implementation

### Negative

1. **Additional Abstraction**: One more concept to understand

2. **Verbose Setup**: Requires container setup code
   ```python
   container.register("service_a", lambda: ServiceA())
   container.register("service_b", lambda: ServiceB())
   # ... more registrations
   ```

3. **Parameter Addition**: Functions need `container` parameter
   - Before: `call_api(cp_code)`
   - After: `call_api(cp_code, container)`

4. **Migration Effort**: Existing code needs refactoring

### Neutral

1. **Not True DI**: No auto-wiring or decorators (by design)
2. **Manual Registration**: Must explicitly register services

## Migration Strategy

**Phase 1**: Core infrastructure (config, auth)
```python
container.register("config_loader", lambda: ConfigLoader())
container.register("auth", lambda: setup_authentication(container.get("config_loader")))
```

**Phase 2**: API clients
```python
container.register("api_client", lambda: APIClient(container.get("config_loader")))
```

**Phase 3**: Feature modules (circuit breaker, cache)
```python
container.register("circuit_breaker", lambda: CircuitBreaker())
container.register("cache", lambda: ResponseCache())
```

**Phase 4**: Test infrastructure
- Create test fixtures for common mock containers
- Helper functions for test setup

## Design Principles

1. **Simplicity Over Features**: Keep it simple, avoid over-engineering
2. **Explicit Over Implicit**: Require manual registration (no auto-wiring magic)
3. **Lazy Initialization**: Create instances only when first requested
4. **Stateless Container**: Container itself has no business logic
5. **Optional Adoption**: Can coexist with existing code during migration

## Example Use Cases

**Use Case 1: Unit Testing**
```python
def test_api_error_handling():
    container = ServiceContainer()
    container.register("api_client", lambda: FailingAPIClient())  # Mock that always fails

    result = call_traffic_api("123", start, end, container)
    assert result["success"] is False
```

**Use Case 2: Integration Testing**
```python
def test_with_real_config():
    container = ServiceContainer()
    container.register("config_loader", lambda: ConfigLoader("test-config.json"))
    # ... real config, mock API
```

**Use Case 3: Development vs Production**
```python
# Development - use caching
container.register("cache", lambda: ResponseCache(enabled=True))

# Production - no caching
container.register("cache", lambda: ResponseCache(enabled=False))
```

## Notes

- Implemented in commit bc413a4
- Used for config_loader, auth_handler, circuit_breaker
- ~100 lines of code in `tools/lib/container.py`
- No external dependencies required
- Follows YAGNI principle (You Aren't Gonna Need It)
