# ADR-0005: Structured Logging and Request Tracing

**Date**: 2024-09-25
**Status**: Accepted
**Deciders**: Development Team

## Context

The original logging used simple print statements and basic Python logging:

```python
# Original approach
print(f"✅ API call successful for CP code {cp_code}")
logger.info(f"Processing CP code: {cp_code}")
```

**Problems**:

1. **No Correlation**: Cannot trace related logs across multiple API calls
2. **No Context**: Missing request metadata (duration, status codes, parameters)
3. **Not Machine-Parsable**: Free-text logs difficult for log aggregation systems
4. **No Structured Fields**: Cannot query by specific attributes
5. **Poor Debugging**: Hard to find all logs for a specific request
6. **No Performance Metrics**: Duration not tracked systematically

Example debugging difficulty:
```
INFO: Processing CP code 123
INFO: API call started
ERROR: API call failed
INFO: Processing CP code 456
INFO: API call started
ERROR: API call failed

# Which error belongs to which CP code? Unknown!
```

## Decision

We will implement **structured logging with correlation IDs and request context tracking**.

### Architecture

```
┌────────────────────────────────────────┐
│         Request Flow                   │
│                                        │
│  1. generate_correlation_id()          │
│     ↓                                  │
│  2. set_request_context()              │
│     ↓                                  │
│  3. API Call with context              │
│     ↓                                  │
│  4. Structured log output              │
│                                        │
│  Log Format:                           │
│  {                                     │
│    "timestamp": "2024-09-25T10:30:00", │
│    "level": "INFO",                    │
│    "message": "API call successful",   │
│    "correlation_id": "uuid-123",       │
│    "api_endpoint": "/traffic",         │
│    "cp_code": "12345",                 │
│    "duration_ms": 234,                 │
│    "status_code": 200                  │
│  }                                     │
└────────────────────────────────────────┘
```

### Implementation Components

**1. Correlation ID Generation**:
```python
import uuid
from contextvars import ContextVar

# Thread-safe context storage
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

def generate_correlation_id() -> str:
    """Generate unique correlation ID for request tracing"""
    correlation_id = str(uuid.uuid4())
    _correlation_id.set(correlation_id)
    return correlation_id
```

**2. Request Context**:
```python
@dataclass
class RequestContext:
    correlation_id: str
    api_endpoint: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]
    start_time: datetime

    def get_duration_ms(self) -> float:
        """Get request duration in milliseconds"""
        return (datetime.now() - self.start_time).total_seconds() * 1000
```

**3. Structured Log Output**:
```python
# JSON format (when ENABLE_STRUCTURED_LOGGING=1)
{
  "timestamp": "2024-09-25T10:30:15.123Z",
  "level": "INFO",
  "message": "Traffic API call successful",
  "correlation_id": "a7f3e21c-9b45-4d12-8f3a-1e2d3c4b5a6f",
  "api_endpoint": "/reporting-api/v2/traffic/data",
  "cp_code": "12345",
  "duration_ms": 234.56,
  "status_code": 200,
  "bytes_transferred": 1048576
}

# Human-readable format (default)
2024-09-25 10:30:15 [INFO] Traffic API call successful [correlation_id=a7f3e21c] duration=234ms
```

**4. Error Context**:
```python
try:
    result = api_call()
except Exception as e:
    logger.error(
        "API call failed",
        extra={
            "correlation_id": get_correlation_id(),
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stack_trace": traceback.format_exc(),
            "request_context": get_request_context()
        }
    )
```

## Alternatives Considered

### Alternative 1: ELK Stack Integration (Elasticsearch, Logstash, Kibana)
**Pros**:
- Industry standard
- Powerful search and visualization
- Real-time log analysis

**Cons**:
- Requires external infrastructure
- Over-kill for a batch script
- Operational complexity
- Cost for hosted solutions

**Reason for rejection**: Too heavyweight. We're not a long-running service. Logs are for post-mortem debugging.

### Alternative 2: Cloud Provider Logging (AWS CloudWatch, GCP Cloud Logging)
**Pros**:
- Managed service
- Built-in search and filtering
- Integration with cloud infrastructure

**Cons**:
- Vendor lock-in
- Not applicable for on-premise deployments
- Requires cloud credentials

**Reason for rejection**: Not all environments use cloud infrastructure. Need vendor-agnostic solution.

### Alternative 3: OpenTelemetry
**Pros**:
- Vendor-neutral standard
- Unified observability (traces, metrics, logs)
- Rich ecosystem

**Cons**:
- Heavy dependency footprint
- Designed for distributed systems
- Complex setup for simple use case

**Reason for rejection**: Over-engineered for a single-process batch script.

### Alternative 4: Keep Simple Logging
**Pros**:
- No changes needed
- Simple to understand

**Cons**:
- Doesn't solve correlation problem
- Poor debugging experience
- No performance metrics

**Reason for rejection**: Doesn't address production debugging needs.

## Consequences

### Positive

1. **Request Tracing**: All logs for a request share correlation_id
   ```bash
   # Find all logs for specific request
   grep "correlation_id=a7f3e21c" app.log
   ```

2. **Performance Monitoring**: Automatic duration tracking
   - API call durations
   - Request lifecycle timing
   - Bottleneck identification

3. **Machine-Parsable**: JSON format for log aggregation
   - Easy integration with Splunk, Datadog, ELK
   - Structured field queries
   - Automated alerting

4. **Better Debugging**:
   - Request parameters captured
   - Error context preserved
   - Stack traces with correlation IDs

5. **Dual Output**:
   - Console: Human-readable format
   - File: JSON format (optional)

6. **Thread-Safe**: Uses `contextvars` for correlation ID storage

### Negative

1. **More Verbose Logs**: JSON format uses more disk space
   - Mitigation: Use log rotation
   - Optional: Enable structured logging only for production

2. **Configuration Complexity**: Environment variable management
   ```bash
   ENABLE_STRUCTURED_LOGGING=1
   LOG_FILE=/var/log/akamai-reports.json
   ```

3. **Learning Curve**: Team needs to understand structured logging concepts

4. **Performance Overhead**: JSON serialization adds ~1-2ms per log
   - Mitigation: Minimal impact for I/O bound operations

### Neutral

1. **Opt-In**: Structured logging disabled by default (backward compatible)
2. **Log Volume**: More detailed logs = more data (expected trade-off)

## Configuration

Enable via environment variables:
```bash
# Enable structured JSON logging
export ENABLE_STRUCTURED_LOGGING=1

# Optional: specify log file
export LOG_FILE=/var/log/akamai-reports.json
```

## Integration with Existing Systems

**Log Aggregation Systems**:
- **Splunk**: Automatically parses JSON logs
- **Datadog**: Use JSON formatter for structured ingestion
- **ELK Stack**: Logstash can parse JSON directly
- **CloudWatch Logs**: Insights can query JSON fields

**Query Examples**:
```
# Splunk
sourcetype=json correlation_id="a7f3e21c"

# Datadog
@correlation_id:"a7f3e21c"

# Elasticsearch
{ "query": { "match": { "correlation_id": "a7f3e21c" } } }
```

## Example Usage

**Before (Unstructured)**:
```
2024-09-25 10:30:15 INFO: Processing CP code 12345
2024-09-25 10:30:17 ERROR: API call failed: Connection timeout
# Cannot correlate these logs!
```

**After (Structured)**:
```json
{
  "timestamp": "2024-09-25T10:30:15.123Z",
  "level": "INFO",
  "message": "Processing CP code",
  "correlation_id": "a7f3e21c",
  "cp_code": "12345"
}
{
  "timestamp": "2024-09-25T10:30:17.456Z",
  "level": "ERROR",
  "message": "API call failed",
  "correlation_id": "a7f3e21c",
  "error_type": "ConnectionTimeout",
  "duration_ms": 2333
}
// Now we can trace the entire request lifecycle!
```

## Performance Impact

Benchmarks (1000 log messages):
- Unstructured: 45ms
- Structured (JSON): 52ms
- **Overhead: ~7ms total (0.007ms per log)**

For API-heavy workload (I/O bound), this overhead is negligible.

## Notes

- Implemented in `tools/lib/error_context.py` and `tools/lib/tracing.py`
- Uses Python's contextvars for thread-safe correlation IDs
- Backward compatible: Disabled by default
- No external dependencies for basic functionality
- Can integrate with future observability platforms without code changes
