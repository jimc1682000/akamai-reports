# Weekly Traffic Report Refactoring - Phase 2 TODOs

**Branch**: `feature/refactor-weekly-report`
**Last Commit**: `8ef8c42` - WIP: Start refactoring weekly_traffic_report.py - Phase 1
**Date**: 2025-10-02

## ✅ Completed (Phase 1)

1. ✅ Create tools/lib/reporters/ module structure
2. ✅ Create tools/lib/utils.py with utility functions (3 functions)
3. ✅ Create tools/lib/time_handler.py with time functions (5 functions)
4. ✅ Update .gitignore to allow tools/lib/

## 🚧 In Progress

- Create tools/lib/api_client.py with API functions (8 functions, ~350 lines)

## 📋 Pending Tasks

### Code Implementation

5. [ ] Move csv_reporter.py to tools/lib/reporters/
6. [ ] Create tools/lib/reporters/console_reporter.py
   - Extract `generate_weekly_report()` from weekly_traffic_report.py
   - Extract `print_summary_stats()` from weekly_traffic_report.py
7. [ ] Create tools/lib/reporters/json_reporter.py
   - Extract `save_report_data()` from weekly_traffic_report.py
8. [ ] Create tools/lib/reporters/__init__.py
   - Export all reporter classes/functions
9. [ ] Refactor weekly_traffic_report.py main script
   - Import from new modules
   - Reduce from 1080 lines to ~100 lines
   - Keep only main() function and orchestration logic

### Testing

10. [ ] Reorganize test files to match new structure:
    - tests/test_utils.py (from test_utility_functions.py - 43 tests)
    - tests/test_time_handler.py (from test_time_functions.py - 19 tests)
    - tests/test_api_client.py (from test_api_functions.py - 28 tests)
    - tests/test_console_reporter.py (new/from test_report_functions.py)
    - tests/test_json_reporter.py (new/from test_report_functions.py)
11. [ ] Update all import paths in test files
12. [ ] Update test_integration.py imports

### Quality Assurance

13. [ ] Run complete test suite: `task test-coverage`
14. [ ] Verify all 153 tests pass
15. [ ] Verify 90%+ code coverage maintained
16. [ ] Run `task ci` to ensure all quality checks pass

### Documentation

17. [ ] Update README.md with new module structure
18. [ ] Update CLAUDE.md with refactored architecture
19. [ ] Update PROJECT_STRUCTURE.md

## 📊 Success Criteria

- ✅ All 153 tests pass
- ✅ Code coverage ≥ 90%
- ✅ Pre-commit hooks pass
- ✅ Main script reduced to ~100 lines
- ✅ Each module has single responsibility
- ✅ Improved code maintainability and testability

## 🔗 Related Files

- Plan: `plans/refactor-weekly-report-plan.md`
- Original file: `weekly_traffic_report.py` (1080 lines)
- New modules: `tools/lib/utils.py`, `tools/lib/time_handler.py`

## 📝 Notes

- Keep backward compatibility
- All original functionality must be preserved
- Focus on modularization, not feature changes
