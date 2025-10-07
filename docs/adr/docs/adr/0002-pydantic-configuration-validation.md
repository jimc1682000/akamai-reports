# ADR-0002: Pydantic Configuration Validation

**Date**: 2025-10-07
**Status**: Accepted
**Deciders**: Development Team

## Context

The original configuration validation in `config_loader.py` used manual checks with ~130 lines of repetitive validation code:
- Manual type checking (`isinstance()`)
- Manual range validation (if/else chains)
- Manual field presence checks
- Hardcoded error messages
- No type hints for configuration structure

This approach had several problems:
1. **Verbose Code**: ~130 lines for validation logic
2. **Type Unsafe**: No compile-time type checking
3. **Error-Prone**: Easy to miss validation cases
4. **Poor Error Messages**: Generic error strings
5. **Maintenance Burden**: Every config change requires manual validation updates

Example of manual validation code:
```python
def _validate_cp_codes(self):
    cp_codes = self.config["business"]["cp_codes"]
    if not isinstance(cp_codes, list):
        raise ConfigurationError("cp_codes must be array")
    if len(cp_codes) == 0:
        raise ConfigurationError("cp_codes cannot be empty")
    for i, cp_code in enumerate(cp_codes):
        if not isinstance(cp_code, str):
            raise ConfigurationError(f"CP code at {i} must be string")
```

## Decision

We will use **Pydantic v2** for configuration validation with comprehensive models covering all configuration sections.

### Implementation

**Before (Manual Validation)**:
- 130 lines of validation code
- Separate validation methods for each section
- Type checking via isinstance()
- Range validation via if statements

**After (Pydantic Models)**:
- 220 lines of reusable Pydantic models (tools/lib/models/config_models.py)
- ~50 lines in ConfigLoader (reduction from 130)
- Automatic type checking
- Declarative field validation

```python
class APITimeoutsConfig(BaseModel):
    traffic: int = Field(60, gt=0, le=300, description="Timeout for Traffic API")
    emissions: int = Field(60, gt=0, le=300, description="Timeout for Emissions API")

class Config(BaseModel):
    api: APIConfig
    business: BusinessConfig
    reporting: ReportingConfig
    system: SystemConfig

    @model_validator(mode="after")
    def validate_service_mappings(self) -> "Config":
        """Validate all CP codes have service mappings"""
        cp_codes = set(self.business.cp_codes)
        mapped_codes = set(self.business.service_mappings.keys())
        unmapped = cp_codes - mapped_codes
        if unmapped:
            raise ValueError(f"CP codes missing service mappings: {', '.join(sorted(unmapped))}")
        return self
```

### Validation Features

1. **Field-Level Validation**:
   - Type constraints (int, str, float, list, dict)
   - Range constraints (gt, ge, lt, le)
   - Length constraints (min_length, max_length)
   - URL format validation

2. **Cross-Field Validation**:
   - Custom week requires custom_start_day
   - CP codes must have service mappings

3. **Error Messages**:
   - Structured field paths (e.g., "api -> endpoints -> traffic")
   - Automatic constraint violations
   - Helpful error context

## Alternatives Considered

### Alternative 1: JSON Schema Validation
**Pros**:
- Language-agnostic format
- Widely supported

**Cons**:
- No type hints integration
- Requires separate schema file
- Less Pythonic
- No compile-time checking with MyPy

**Reason for rejection**: Pydantic provides better Python integration and type safety.

### Alternative 2: dataclasses with manual validation
**Pros**:
- Standard library (Python 3.7+)
- Lightweight

**Cons**:
- Still requires manual validation logic
- No automatic range/format validation
- No built-in error formatting

**Reason for rejection**: Doesn't solve the core problem of verbose validation code.

### Alternative 3: attrs with validators
**Pros**:
- Less boilerplate than dataclasses
- Built-in validators

**Cons**:
- Less mature validation ecosystem than Pydantic
- Not as widely adopted for configuration
- No automatic JSON schema generation

**Reason for rejection**: Pydantic has better ecosystem and documentation for config validation.

## Consequences

### Positive

1. **Code Reduction**: 130 lines → 50 lines in ConfigLoader (-62%)
2. **Type Safety**: MyPy can catch configuration structure errors at compile-time
3. **Better Errors**: Field paths clearly show where validation failed
4. **Self-Documenting**: Field descriptions serve as inline documentation
5. **Maintainability**: Adding new config fields only requires updating models
6. **IDE Support**: Auto-completion for configuration structure
7. **Future-Proof**: Easy to add JSON schema export for documentation

### Negative

1. **New Dependency**: Adds pydantic to requirements
2. **Learning Curve**: Team needs to understand Pydantic syntax
3. **Test Updates**: Existing tests expect old error message format (need updates)
4. **Migration**: Old code using dict access patterns still works (backward compatible)

### Neutral

1. **Performance**: Pydantic validation adds ~1-2ms overhead (negligible for config loading)
2. **Complexity**: Moved from procedural validation to declarative models (different paradigm)

## Notes

- Pydantic v2 used for better performance and type hints
- Backward compatibility maintained by storing raw dict in `self.config`
- All 13 configuration sections covered by Pydantic models
- Validation errors formatted in Chinese for consistency with existing messages
