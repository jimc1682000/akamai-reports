# Weekly Traffic Report Refactoring - Complete Plan

**Project**: Akamai V2 Traffic Reports
**Branch**: `feature/refactor-weekly-report`
**Created**: 2025-10-02
**Status**: Phase 1 Complete, Phase 2 Pending

## 🎯 Objective

Refactor the 1080-line `weekly_traffic_report.py` into a modular architecture to improve:
- Code maintainability
- Testability
- Reusability
- Readability

## 📐 Architecture Design

### Before Refactoring
```
weekly_traffic_report.py (1080 lines)
├── Authentication (1 function)
├── Utility Functions (3 functions)
├── Time Handling (5 functions)
├── API Client (8 functions)
├── Report Generation (3 functions)
└── Main Function (1 function)
```

### After Refactoring
```
tools/lib/
├── utils.py                    # 3 utility functions
├── time_handler.py             # 5 time handling functions
├── api_client.py               # 8 API functions
├── reporters/
│   ├── __init__.py
│   ├── csv_reporter.py         # CSV reports (existing)
│   ├── console_reporter.py     # Console reports (2 functions)
│   └── json_reporter.py        # JSON reports (1 function)
└── config_loader.py            # Configuration (existing)

weekly_traffic_report.py (~100 lines)
└── main() - orchestration only
```

## 📦 Module Breakdown

### 1. tools/lib/utils.py (✅ Completed)
**Purpose**: Common utility functions for data conversion and formatting

**Functions**:
- `bytes_to_tb(bytes_value)` - Convert bytes to TB
- `bytes_to_gb(bytes_value)` - Convert bytes to GB
- `format_number(number, decimal_places=2)` - Format numbers with separators

**Lines**: ~50
**Tests**: From test_utility_functions.py (43 tests)

### 2. tools/lib/time_handler.py (✅ Completed)
**Purpose**: Time range calculation and date parsing

**Functions**:
- `get_last_week_range(week_start_offset, week_duration_days)` - Calculate last week
- `get_last_week_range_with_config(config_loader)` - Calculate with config
- `parse_date_string(date_string, end_of_day)` - Parse date strings
- `validate_time_range(start_date, end_date)` - Validate time ranges
- `get_time_range(args, config_loader)` - Unified time range getter

**Lines**: ~150
**Tests**: From test_time_functions.py (19 tests)

### 3. tools/lib/api_client.py (⏳ Pending)
**Purpose**: All Akamai API interactions

**Functions**:
- `setup_authentication()` - Initialize EdgeGrid auth
- `call_traffic_api(...)` - Call V2 Traffic API with retry
- `call_emissions_api(...)` - Call V2 Emissions API with retry
- `get_total_edge_traffic(...)` - Query total traffic
- `get_service_traffic(...)` - Query service traffic
- `get_all_service_traffic(...)` - Query all services
- `get_regional_traffic(...)` - Query regional traffic
- `get_all_regional_traffic(...)` - Query all regions

**Lines**: ~350
**Tests**: From test_api_functions.py (28 tests)

**Dependencies**:
- requests
- akamai.edgegrid (EdgeGridAuth, EdgeRc)
- tools.lib.config_loader
- time

### 4. tools/lib/reporters/console_reporter.py (⏳ Pending)
**Purpose**: Generate formatted console reports

**Functions**:
- `generate_weekly_report(...)` - Generate main weekly report
- `print_summary_stats(...)` - Print quick summary

**Lines**: ~200
**Tests**: From test_report_functions.py (partial, ~10 tests)

**Dependencies**:
- datetime
- tools.lib.utils
- tools.lib.config_loader

### 5. tools/lib/reporters/json_reporter.py (⏳ Pending)
**Purpose**: Save report data to JSON

**Functions**:
- `save_report_data(...)` - Save JSON report file

**Lines**: ~80
**Tests**: From test_report_functions.py (partial, ~7 tests)

**Dependencies**:
- json
- datetime

### 6. tools/lib/reporters/csv_reporter.py (⏳ Move)
**Purpose**: Generate CSV reports for V1/V2 comparison

**Status**: Already exists in `tools/lib/`, needs to move to `tools/lib/reporters/`

**Functions**: 4 static methods in CSVReporter class

### 7. tools/lib/reporters/__init__.py (⏳ Pending)
**Purpose**: Export all reporter modules

**Content**:
```python
from tools.lib.reporters.console_reporter import generate_weekly_report, print_summary_stats
from tools.lib.reporters.json_reporter import save_report_data
from tools.lib.reporters.csv_reporter import CSVReporter

__all__ = [
    'generate_weekly_report',
    'print_summary_stats',
    'save_report_data',
    'CSVReporter',
]
```

### 8. weekly_traffic_report.py (⏳ Refactor)
**Purpose**: Main orchestration script

**Content**: (~100 lines)
```python
#!/usr/bin/env python3
import argparse
from tools.lib.config_loader import load_configuration
from tools.lib.api_client import (
    setup_authentication,
    get_total_edge_traffic,
    get_all_service_traffic,
    get_all_regional_traffic,
)
from tools.lib.time_handler import get_time_range
from tools.lib.reporters import (
    generate_weekly_report,
    print_summary_stats,
    save_report_data,
)

def main():
    # 1. Parse arguments
    # 2. Load configuration
    # 3. Setup authentication
    # 4. Get time range
    # 5. Query APIs
    # 6. Generate reports
    # 7. Display results
    pass

if __name__ == "__main__":
    exit(main())
```

## 🧪 Testing Strategy

### Test File Reorganization

| Original Test File | New Test File | Tests | Notes |
|-------------------|---------------|-------|-------|
| test_utility_functions.py | test_utils.py | 43 | Rename, update imports |
| test_time_functions.py | test_time_handler.py | 19 | Rename, update imports |
| test_api_functions.py | test_api_client.py | 28 | Rename, update imports |
| test_report_functions.py | test_console_reporter.py + test_json_reporter.py | 17 | Split into 2 files |
| test_config_loader.py | test_config_loader.py | 38 | Keep as-is |
| test_integration.py | test_integration.py | 10 | Update imports only |
| **Total** | **6 files** | **153** | **Maintain 90%+ coverage** |

### Coverage Requirements

- Each new module: ≥ 90% coverage
- Overall project: ≥ 90% coverage
- All 153 tests must pass
- Pre-commit hooks must pass

## 📋 Implementation Phases

### Phase 1: Foundation (✅ Completed - Commit 8ef8c42)

- [x] Create `tools/lib/utils.py`
- [x] Create `tools/lib/time_handler.py`
- [x] Create `tools/lib/reporters/` directory
- [x] Update `.gitignore` to allow `tools/lib/`
- [x] Commit with WIP message

### Phase 2: API & Reporters (⏳ In Progress)

- [ ] Create `tools/lib/api_client.py`
- [ ] Move `csv_reporter.py` to `tools/lib/reporters/`
- [ ] Create `tools/lib/reporters/console_reporter.py`
- [ ] Create `tools/lib/reporters/json_reporter.py`
- [ ] Create `tools/lib/reporters/__init__.py`

### Phase 3: Main Script Refactoring

- [ ] Refactor `weekly_traffic_report.py`
- [ ] Update all imports
- [ ] Remove extracted functions
- [ ] Verify functionality

### Phase 4: Testing

- [ ] Rename/reorganize test files
- [ ] Update all test imports
- [ ] Run full test suite
- [ ] Verify 90%+ coverage
- [ ] Fix any failing tests

### Phase 5: Documentation & Cleanup

- [ ] Update README.md
- [ ] Update CLAUDE.md
- [ ] Update PROJECT_STRUCTURE.md
- [ ] Final commit
- [ ] Merge to main branch

## 🎯 Success Metrics

- ✅ Main script reduced from 1080 lines to ~100 lines (90% reduction)
- ✅ 6 well-organized modules with single responsibilities
- ✅ All 153 tests passing
- ✅ Code coverage maintained at 90%+
- ✅ Pre-commit hooks passing
- ✅ No functionality regression
- ✅ Improved code maintainability

## 🔧 Technical Decisions

### Why This Structure?

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Reusability**: Utils and time_handler can be used by other scripts
3. **Testability**: Each module can be tested independently
4. **Maintainability**: Easier to locate and modify specific functionality
5. **Reporters Grouping**: All report generation logic in one place

### Import Strategy

Use absolute imports from project root:
```python
from tools.lib.utils import bytes_to_tb
from tools.lib.time_handler import get_time_range
from tools.lib.api_client import setup_authentication
from tools.lib.reporters import generate_weekly_report
```

### Backward Compatibility

- Main script interface unchanged
- Command-line arguments unchanged
- Output format unchanged
- Configuration format unchanged

## 📚 References

- Original file: `weekly_traffic_report.py` (1080 lines)
- Test suite: `tests/` (153 tests, 90%+ coverage)
- Configuration: `tools/lib/config_loader.py`
- Documentation: `CLAUDE.md`, `README.md`, `PROJECT_STRUCTURE.md`

## 📝 Notes for Next Session

1. Start with creating `api_client.py` - it's the largest module (~350 lines)
2. Extract functions from `weekly_traffic_report.py` lines 33-683
3. Ensure all imports and dependencies are correct
4. Test each module incrementally
5. Update tests only after all modules are created
6. Final integration testing before commit

## 🔗 Related Documents

- TODOs: `todos/refactor-weekly-report-phase2.md`
- Git branch: `feature/refactor-weekly-report`
- Base branch: `feature/config-refactoring`
