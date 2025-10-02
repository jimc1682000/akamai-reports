# Akamai Traffic Reports - Project Structure

## 📁 Directory Structure

```
akamai-traffic/
├── weekly_traffic_report.py          # 主要週報生成腳本
├── tools/                            # 工具和函式庫目錄
│   ├── lib/                          # 可重用函式庫模組
│   │   ├── __init__.py               # 套件初始化
│   │   ├── config_loader.py          # 配置管理模組
│   │   └── csv_reporter.py           # CSV 報告生成工具
│   └── compare_v1_v2_apis.py         # V1/V2 API 比較工具
├── config.json                       # 配置檔案 (gitignored)
├── config.template.json              # 配置範本
├── .edgerc                           # Akamai 認證 (gitignored)
│
├── tests/                             # 單元測試
│   ├── test_config_loader.py
│   ├── test_time_functions.py
│   ├── test_utility_functions.py
│   ├── test_api_functions.py
│   ├── test_report_functions.py
│   └── test_integration.py
│
├── archive_investigation_scripts/     # 調查用腳本 (已歸檔)
│   ├── test_v1_api.py
│   ├── test_geoip_hypothesis.py
│   ├── test_all_regions.py
│   ├── test_metrics_comparison.py
│   ├── test_delivery_type.py
│   ├── test_api_metadata.py
│   └── test_tw_early_daterange.py
│
├── CLAUDE.md                          # Claude AI 專案指引
├── README.md                          # 專案說明
├── Taskfile.yml                       # Task 命令定義
└── requirements-test.txt              # 測試依賴

## 📊 Generated Reports (gitignored)

Example V1 vs V2 comparison report filenames:
- daily_v1_v2_comparison_YYYYMMDD_HHMMSS.csv       # ⭐ 最重要：每日逐日對比
- v1_daily_breakdown_YYYYMMDD_HHMMSS.csv           # V1 每日明細
- v2_daily_breakdown_YYYYMMDD_HHMMSS.csv           # V2 每日明細
- v1_v2_comparison_summary_YYYYMMDD_HHMMSS.csv     # 總體摘要
- v1_v2_detailed_comparison_YYYYMMDD_HHMMSS.csv    # 詳細分析

## 🛠️ Tools and Scripts

### Weekly Traffic Report (Production)
```bash
# Run weekly report using V2 APIs
python weekly_traffic_report.py

# Manual date range
python weekly_traffic_report.py --start YYYY-MM-DD --end YYYY-MM-DD
```

### V1 vs V2 API Comparison (For Analysis)
```bash
# Compare V1 and V2 API data for any date range
python tools/compare_v1_v2_apis.py --start YYYY-MM-01 --end YYYY-MM-30

# Output: 5 CSV files for detailed comparison
# - Summary comparison
# - V1 daily breakdown
# - V2 daily breakdown
# - Daily V1 vs V2 comparison
# - Detailed analysis with metadata
```

### CSV Reporter Module (Reusable Library)
The `tools/lib/csv_reporter.py` module provides standardized CSV generation:
- `CSVReporter.write_summary_csv()` - Summary comparison
- `CSVReporter.write_daily_breakdown_csv()` - Daily breakdown for one API
- `CSVReporter.write_daily_comparison_csv()` - Daily V1 vs V2 comparison
- `CSVReporter.write_detailed_comparison_csv()` - Detailed analysis

### Configuration Loader (Reusable Library)
The `tools/lib/config_loader.py` module handles all configuration management:
- External JSON configuration with validation
- Flexible week definition support
- Business parameter management (CP codes, regions, etc.)

## 🧪 Running Tests

```bash
# Complete CI pipeline
task ci

# Quick test
task test-quick

# Test with coverage
task test-coverage
```

## 📝 Data Analysis Notes

### V1 vs V2 API Comparison
The comparison tool generates 5 CSV files to analyze data differences between V1 and V2 APIs:
- Summary comparison
- Daily breakdown for each API
- Daily V1 vs V2 comparison
- Detailed analysis with metadata

Use these reports for API migration planning and validation.
