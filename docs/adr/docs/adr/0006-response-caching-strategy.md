# ADR-0006: Response Caching Strategy

**Date**: 2024-09-24
**Status**: Accepted
**Deciders**: Development Team

## Context

During development and testing, developers repeatedly call the same API endpoints with identical parameters:

```python
# Development workflow
for i in range(10):  # Testing/debugging loop
    result = call_traffic_api(cp_code, start_date, end_date)
    # Make code changes
    # Run again...
```

**Problems**:

1. **Slow Development Cycle**: Each test run makes real API calls (3-5s each)
2. **API Rate Limit Risk**: Repeated calls during testing burn through rate limits
3. **Unnecessary Network I/O**: Fetching same data repeatedly
4. **Time Wasted**: Developer waits for API responses for unchanged queries
5. **Cost**: API quota consumption during development

Example: Testing a report format change
- 10 test iterations × 5 API calls × 3 seconds = **150 seconds wasted**
- All fetching identical data!

## Decision

We will implement **file-based response caching with TTL and SHA256 cache keys** for development/testing environments.

### Architecture

```
┌────────────────────────────────────────────┐
│         API Call Flow                      │
│                                            │
│  1. Generate cache key (SHA256)            │
│     hash(function_name + parameters)       │
│                                            │
│  2. Check cache                            │
│     ├─ Hit → Return cached response        │
│     └─ Miss → Call API                     │
│                                            │
│  3. Store response                         │
│     .cache/responses/abc123.json           │
│     {                                      │
│       "data": {...},                       │
│       "timestamp": "2024-09-24T10:00:00",  │
│       "ttl": 7200                          │
│     }                                      │
└────────────────────────────────────────────┘
```

### Implementation

**1. Cache Key Generation**:
```python
import hashlib

def _cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate cache key from function name and parameters"""
    key_parts = [func_name]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()
```

**2. Cache Storage**:
```python
def _save_to_cache(key: str, response: Dict[str, Any], ttl: int):
    """Save response to cache file"""
    cache_dir = Path(".cache/responses")
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "data": response,
        "timestamp": datetime.now().isoformat(),
        "ttl": ttl
    }

    cache_file = cache_dir / f"{key}.json"
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2)
```

**3. Cache Retrieval with TTL**:
```python
def _get_from_cache(key: str) -> Optional[Dict[str, Any]]:
    """Get response from cache if valid"""
    cache_file = Path(f".cache/responses/{key}.json")

    if not cache_file.exists():
        return None

    with open(cache_file) as f:
        cache_data = json.load(f)

    # Check TTL
    cached_time = datetime.fromisoformat(cache_data["timestamp"])
    age_seconds = (datetime.now() - cached_time).total_seconds()

    if age_seconds > cache_data["ttl"]:
        return None  # Expired

    return cache_data["data"]
```

**4. Integration Decorator**:
```python
def cached_response(ttl: int = 7200):  # 2 hours default
    """Decorator to cache API responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not os.getenv("ENABLE_API_CACHE"):
                return func(*args, **kwargs)  # Disabled

            cache_key = _cache_key(func.__name__, *args, **kwargs)
            cached = _get_from_cache(cache_key)

            if cached:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached

            # Cache miss - call API
            response = func(*args, **kwargs)
            _save_to_cache(cache_key, response, ttl)
            return response

        return wrapper
    return decorator
```

### Configuration

**Enable for Development**:
```bash
# Enable caching (development/testing only)
export ENABLE_API_CACHE=1

# Run script
python traffic.py
```

**Disable for Production**:
```bash
# Production - no cache
unset ENABLE_API_CACHE
python traffic.py
```

**Cache Management**:
```python
# Clear entire cache
clear_cache()  # Removes .cache/responses/*.json

# Get cache statistics
stats = get_cache_stats()
# {"total_entries": 45, "total_size_mb": 12.3, "oldest_entry": "2024-09-20"}
```

## Alternatives Considered

### Alternative 1: Redis/Memcached
**Pros**:
- Fast in-memory caching
- Distributed caching support
- Automatic TTL expiration
- Production-ready

**Cons**:
- Requires external service
- Overkill for development use case
- Operational complexity
- Not needed for batch script

**Reason for rejection**: Too heavyweight. File-based cache sufficient for development needs.

### Alternative 2: Python's functools.lru_cache
**Pros**:
- Built-in to Python
- Zero configuration
- Fast (in-memory)

**Cons**:
- Process-scoped (lost on script restart)
- No TTL support
- No disk persistence
- Cannot inspect cache

**Reason for rejection**: Cache lost on every script run. Defeats purpose for development workflow.

### Alternative 3: HTTP caching headers
**Pros**:
- Standard mechanism
- requests library supports it
- Server-controlled TTL

**Cons**:
- Depends on server cache headers
- Akamai APIs may not send proper headers
- No control over cache behavior

**Reason for rejection**: Cannot rely on server-side caching for our use case.

### Alternative 4: No caching
**Pros**:
- No complexity
- Always fresh data

**Cons**:
- Slow development cycle
- Wastes API quota
- Poor developer experience

**Reason for rejection**: Unacceptable developer experience during testing.

## Consequences

### Positive

1. **Fast Development Cycle**:
   - First run: 45s (real API calls)
   - Subsequent runs: <1s (cached responses)
   - **45x speedup for cached scenarios**

2. **API Quota Conservation**:
   - Testing doesn't burn through rate limits
   - Can iterate on code without API concerns

3. **Offline Development**:
   - Can work on report formatting without network
   - Cache enables airplane coding

4. **Inspectable Cache**:
   - Cache files are human-readable JSON
   - Can manually inspect cached responses
   - Easy to debug caching issues

5. **No External Dependencies**:
   - File-based, no Redis/Memcached needed
   - Standard library only (hashlib, json, pathlib)

6. **Simple Management**:
   ```python
   clear_cache()           # Clear all cached responses
   get_cache_stats()       # Inspect cache state
   ```

### Negative

1. **Stale Data Risk**:
   - Cached data may become outdated
   - Mitigation: 2-hour TTL default, can clear cache manually

2. **Disk Space Usage**:
   - API responses stored on disk
   - Typical cache size: ~10-50MB
   - Mitigation: Clear old caches periodically

3. **Cache Invalidation Complexity**:
   - No automatic invalidation on config changes
   - Developer must clear cache manually when needed

4. **Not Production-Safe**:
   - Must be disabled in production (via env var)
   - Risk of using stale data if accidentally enabled

5. **SHA256 Key Collisions** (theoretical):
   - Hash collisions possible but astronomically rare
   - Probability: ~0% for our scale

### Mitigation Strategies

1. **Environment Variable Guard**:
   ```python
   if not os.getenv("ENABLE_API_CACHE"):
       return func(*args, **kwargs)  # Skip cache
   ```

2. **TTL Defaults**:
   - API responses: 2 hours (7200s)
   - Short enough to prevent very stale data

3. **Gitignore Cache Directory**:
   ```
   .cache/
   ```

4. **Cache Stats API**:
   ```python
   stats = get_cache_stats()
   # Shows age of oldest entry, total size
   ```

## Cache Key Examples

```python
# Example 1: Traffic API
call_traffic_api(cp_code="12345", start="2024-09-01", end="2024-09-07")
# Key: sha256("call_traffic_api|12345|2024-09-01|2024-09-07")
# → a7f3e21c9b454d128f3a1e2d3c4b5a6f...

# Example 2: Different parameters
call_traffic_api(cp_code="67890", start="2024-09-01", end="2024-09-07")
# Key: sha256("call_traffic_api|67890|2024-09-01|2024-09-07")
# → Different hash, separate cache entry
```

## Performance Impact

**Development Workflow** (10 iterations):
- Without cache: 10 × 45s = **450 seconds (7.5 minutes)**
- With cache: 45s + 9 × 0.5s = **49.5 seconds**
- **Improvement: 89% faster**

**Production**:
- No impact (cache disabled by default)

## Directory Structure

```
.cache/
└── responses/
    ├── a7f3e21c9b454d128f3a1e2d3c4b5a6f.json
    ├── b8f4e32d0c564e238g4b2f3e4d5c6b7g.json
    └── ...
```

## Notes

- Implemented in `tools/lib/cache.py`
- Cache disabled by default (opt-in for development)
- TTL configurable per-function via decorator parameter
- SHA256 ensures unique keys for different parameter combinations
- Cache files are JSON for easy inspection and manual editing
- `.cache/` directory in `.gitignore` to prevent committing cached data
