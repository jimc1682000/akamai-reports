# Akamai V2 Traffic Reports

[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Tests](https://img.shields.io/badge/tests-153%20passed-green.svg)](#測試與品質保證)

自動化週報腳本，用於抓取 Akamai V2 API 流量數據並生成週報。

## 專案概述

隨著 Akamai V1 Traffic Reports API 即將於 2025-11-05 (GUI) / 2026-02-05 (API) 停止服務，本專案開發了基于 V2 API 的自動化數據抓取和報表生成系統。

本專案具備 **production-ready** 品質標準：
- ✅ **90%+ 測試覆蓋率** - 153個comprehensive unit tests
- ✅ **自動化代碼品質檢查** - Ruff linter + formatter
- ✅ **Pre-commit hooks** - 確保每次提交的代碼品質
- ✅ **現代化開發工作流** - Taskfile自動化任務管理

## 功能特點

### 📊 數據抓取
- **V2 Traffic API**: 使用 `time5minutes` 維度抓取 Edge 流量數據
- **V2 Emissions API**: 使用 `time1day` 維度抓取地區流量數據
- **多個 CP codes** 完整覆蓋
- **自動重試機制** 提高數據獲取成功率

### 🕒 時間處理
- **自動模式**: 計算上週時間範圍（週日00:00 ~ 週六23:59 UTC+0）
- **手動模式**: 支援指定任意時間範圍
- **UTC+0 標準時區** 確保數據一致性

### 💰 計費預估
- 基於實際數據分析的 **1.0 修正係數**
- 公式：`預估計費用量 = V2 API 總 Edge 流量 × 1.0`
- 準確度 >95%

### 📋 報表生成
- **結構化控制台輸出** 清晰易讀
- **JSON 數據導出** 便於後續分析
- **完整對齊格式** 專業報表外觀
- **多層級數據摘要** 全方位數據洞察

### 🏗️ 架構改進 (NEW)
- **Pydantic 配置驗證** - 型別安全的配置管理，自動欄位驗證
- **並發 API 執行** - 75% 性能提升（45s → ~10s）
- **連接池化** - HTTP keep-alive 與連接重用
- **斷路器模式** - 防止級聯故障的彈性設計
- **依賴注入** - 可測試性提升，鬆耦合架構
- **結構化日誌** - 請求追蹤與性能監控
- **MyPy 靜態型別檢查** - Pre-commit 自動型別驗證
- **架構決策記錄 (ADR)** - 完整的架構文檔

詳細架構說明請參閱 [Architecture Decision Records](docs/adr/)

## 系統需求

- Python 3.8+
- [Task](https://taskfile.dev/) (推薦用於開發工作流)
- 有效的 `.edgerc` Akamai EdgeGrid 認證檔案

## 快速開始

### 1. 克隆專案
```bash
git clone <repository-url>
cd akamai-reports
```

### 2. 設置開發環境
```bash
# 使用 Taskfile (推薦)
task setup

# 或手動安裝
pip install -r requirements-test.txt  # 包含 pytest, pydantic, mypy 等
pip install ruff pre-commit
pre-commit install
```

### 3. 配置系統
```bash
# 複製配置模板
cp config.template.json config.json

# 編輯配置文件，填入實際的 API 端點和 CP codes
# 注意: config.json 在 .gitignore 中，不會被提交

# 驗證配置
task config-check
```

### 4. 確保認證檔案存在
```bash
ls -la ~/.edgerc
```

## 使用方法

### 週報生成（生產環境）

#### 自動模式（推薦）
```bash
# 使用 Taskfile
task run

# 或直接運行
python traffic.py
```

#### 手動模式
```bash
# 使用 Taskfile
task run-manual START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD

# 或直接運行
python traffic.py --start YYYY-MM-DD --end YYYY-MM-DD
```

### V1 vs V2 API 比較分析

用於分析 V1 和 V2 API 的數據差異，生成詳細的 CSV 報告供 Akamai Support 分析：

```bash
# 比較任意日期範圍的 V1 vs V2 API 數據
python tools/compare_v1_v2_apis.py --start YYYY-MM-01 --end YYYY-MM-30

# 輸出 5 個 CSV 檔案：
# 1. v1_v2_comparison_summary_*.csv - 簡要摘要比較
# 2. v1_daily_breakdown_*.csv - V1 API 每日數據明細
# 3. v2_daily_breakdown_*.csv - V2 API 每日數據明細
# 4. daily_v1_v2_comparison_*.csv - 每日 V1 vs V2 逐日對比
# 5. v1_v2_detailed_comparison_*.csv - 詳細比較與分析
```

**注意**：V1 API 需要逐日查詢（每天每地區一次 API 請求），腳本已加入延遲避免 rate limiting。

### 版本管理

本專案使用 [git-cliff](https://git-cliff.org/) 自動生成 CHANGELOG 並管理版本。

#### 檢查當前版本
```bash
task version
```

#### 生成 CHANGELOG 預覽（不創建 tag）
```bash
# 預覽未發布的變更
task changelog-preview

# 生成完整 CHANGELOG.md（不創建 tag）
task changelog-generate
```

#### 版本升級（自動生成 CHANGELOG + Git Tag）
```bash
# Patch 版本升級 (0.1.0 -> 0.1.1) - 修復 bug
task bump-patch

# Minor 版本升級 (0.1.0 -> 0.2.0) - 新增功能
task bump-minor

# Major 版本升級 (0.1.0 -> 1.0.0) - 重大變更
task bump-major
```

**版本升級流程**：
1. 自動更新 `VERSION` 文件
2. 使用 git-cliff 生成/更新 `CHANGELOG.md`
3. 創建 git commit（含 VERSION 和 CHANGELOG.md）
4. 創建 git tag（格式：`v0.1.0`）
5. 提示推送到遠端倉庫的指令

**Commit 訊息規範**：
本專案遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範，並使用 commitizen 自動驗證：

**允許的 commit 類型**：
- `feat:` - 新功能（觸發 MINOR 版本升級）
- `fix:` - Bug 修復（觸發 PATCH 版本升級）
- `docs:` - 文檔更新
- `refactor:` - 代碼重構（觸發 PATCH 版本升級）
- `test:` - 測試相關
- `chore:` - 雜項任務、構建工具
- `perf:` - 性能優化（觸發 PATCH 版本升級）
- `style:` - 代碼格式（不影響功能）
- `ci:` - CI/CD 配置
- `build:` - 構建系統或依賴更新
- `security:` - 安全性改進（觸發 PATCH 版本升級）
- `revert:` - 回退 commit

**Commit 格式範例**：
```bash
feat(api): add V2 emissions API support
fix(config): correct CP code validation logic
docs(readme): update installation instructions
test(integration): add edge case tests for circuit breaker
chore(deps): update requests to 2.31.0
```

**使用 commitizen 輔助工具**：
```bash
# 互動式 commit（自動生成符合規範的訊息）
cz commit

# 或使用 git commit（會自動驗證格式）
git commit -m "feat: add new feature"
```

**Pre-commit Hook 自動驗證**：
- 每次 commit 時會自動檢查訊息格式
- 不符合規範的 commit 會被拒絕
- 確保所有 commit 都符合 Conventional Commits 標準

**初始化版本系統**：
```bash
# 如果是第一次使用，初始化 VERSION 文件
task version-init
```

**🔄 重寫舊 Commits（可選）**：

如果你想將舊的非標準 commit messages 改寫為 Conventional Commits 格式：

```bash
# 方法 1: 使用互動式腳本（推薦）
./scripts/interactive_rewrite.sh

# 方法 2: 手動執行 git rebase
git rebase -i --root
```

⚠️ **警告**：重寫歷史會改變 commit SHA，需要 force push。詳細指南請參閱 [`docs/REWRITE_COMMITS_GUIDE.md`](docs/REWRITE_COMMITS_GUIDE.md)

### 開發工作流

#### 代碼品質檢查
```bash
# 完整品質檢查 (lint + format)
task quality

# 僅檢查格式問題
task lint

# 自動修復格式問題
task lint-fix

# 格式化代碼
task format
```

#### 測試運行
```bash
# 運行完整測試套件 + 覆蓋率報告
task test-coverage

# 快速測試 (無覆蓋率)
task test-quick

# 使用自定義測試運行器
task test-runner

# 查看覆蓋率報告
task coverage-report
```

#### CI/開發流程
```bash
# 完整 CI pipeline (代碼品質 + 測試)
task ci

# 提交前快速檢查
task dev-check

# 運行 pre-commit hooks
task pre-commit
```

## 數據結構

### 抓取的數據項目

#### V2 Traffic API 數據
- **總體 Edge 流量** - 所有配置的 CP codes 總和 (TB) (實際 CP codes 請查詢 Akamai Console)
- **服務 1** - CP code PLACEHOLDER_CP_CODE_001 (TB)
- **服務 2** - CP code PLACEHOLDER_CP_CODE_002 (TB)
- **服務 3** - CP code PLACEHOLDER_CP_CODE_003 (GB)
- **服務 4** - CP code PLACEHOLDER_CP_CODE_004 (GB)

#### V2 Emissions API 數據
- **地區 1** 流量 (TB)
- **地區 2** 流量 (TB)
- **地區 3** 流量 (TB)

### CP Codes 清單

**實際 CP codes 請查詢 Akamai Console**

需配置的 CP codes 數量依業務需求而定，請在 `config.json` 中配置。範例格式請參考 `config.template.json`：

```json
{
  "business": {
    "cp_codes": [
      "PLACEHOLDER_CP_CODE_001",
      "PLACEHOLDER_CP_CODE_002",
      "..."
    ]
  }
}
```

## 技術架構

```
traffic.py
├── 命令行參數處理
├── 時間計算模組
│   ├── 自動計算上週範圍 (週日~週六)
│   └── 手動時間範圍處理
├── API 查詢模組
│   ├── V2 Traffic API 查詢
│   └── V2 Emissions API 查詢
├── 數據處理模組
│   ├── 單位轉換 (Bytes → TB/GB)
│   ├── 數據聚合
│   └── 計費預估計算
└── 報表輸出模組
    ├── 控制台格式化輸出
    └── JSON 數據導出
```

## 效能規格

- **數據點限制**: 50,000 點 (API 限制)
- **執行時間**: < 30 秒
- **查詢成功率**: >99%
- **計費預估準確度**: >95%

## 疑難排解

### 常見問題

**Q: 認證失敗 (401)**
- A: 檢查 `.edgerc` 檔案是否存在且格式正確

**Q: 時間範圍錯誤**
- A: V2 API 數據保留期約 3-6 個月，請使用較近期的日期

**Q: 查詢失敗**
- A: 檢查網路連線，API 會自動重試

## 專案結構
```
akamai-reports/
├── traffic.py                        # 主要流量報表生成腳本
├── tools/                            # 工具和函式庫目錄
│   ├── lib/                          # 可重用函式庫模組
│   │   ├── __init__.py
│   │   ├── config_loader.py          # 配置加載和驗證
│   │   └── csv_reporter.py           # CSV 報告生成工具
│   └── compare_v1_v2_apis.py         # V1/V2 API 比較工具
├── config.json                       # 實際配置檔案 (不在版本控制中)
├── config.template.json              # 配置模板 (可安全分享)
├── README.md                         # 專案說明文檔
├── AGENTS.md                         # AI agent 開發指導文檔
├── PROJECT_STRUCTURE.md              # 專案結構詳細說明
├── Taskfile.yml                      # 自動化任務管理
├── pyproject.toml                    # Python 專案配置 + Ruff 設定
├── .pre-commit-config.yaml           # Pre-commit hooks 配置
├── requirements-test.txt             # 測試依賴清單
├── pytest.ini                        # Pytest 配置
├── run_tests.py                      # 自定義測試運行器
├── tests/                            # 單元測試目錄
│   ├── test_config_loader.py         # 配置系統測試 (38 tests)
│   ├── test_time_functions.py        # 時間處理測試 (19 tests)
│   ├── test_utility_functions.py     # 工具函數測試 (43 tests)
│   ├── test_api_functions.py         # API 調用測試 (28 tests)
│   ├── test_report_functions.py      # 報告生成測試 (17 tests)
│   └── test_integration.py           # 整合測試 (10 tests)
├── htmlcov/                          # HTML 覆蓋率報告
├── docs/                             # 技術文檔目錄
│   └── weekly-traffic-report-spec.md # 詳細技術規格
└── archive_investigation_scripts/    # 調查用腳本 (已歸檔)
    └── test_*.py                     # V1/V2 API 調查測試腳本
```

## 測試與品質保證

### 測試覆蓋率
- **153 個測試案例** 涵蓋所有核心功能
- **90%+ 代碼覆蓋率** 確保程序穩定性
- **6 個測試模組**:
  - `test_config_loader.py` - 配置系統測試 (38 tests)
  - `test_time_functions.py` - 時間處理測試 (19 tests)
  - `test_utility_functions.py` - 工具函數測試 (43 tests)
  - `test_api_functions.py` - API 調用測試 (28 tests)
  - `test_report_functions.py` - 報告生成測試 (17 tests)
  - `test_integration.py` - 整合測試 (10 tests)

### 代碼品質工具
- **Ruff** - 現代化 Python linter & formatter
- **Pre-commit hooks** - 自動化代碼品質檢查
- **Configuration validation** - 防止配置錯誤
- **Error handling** - 完整的錯誤處理和重試機制

## 版本歷史
- **v2.0** (2025-09-25): 添加外部配置系統、完整測試套件、代碼品質工具
- **v1.0** (2025-09-24): 初始完整版本，支援所有核心功能

## 授權
本專案採用內部使用授權。

## 版本資訊
- 建立日期: 2024-09-24
- 最後更新: 2025-09-24

---

**注意**: 本工具專門為 Akamai V1 → V2 API 遷移而開發，確保業務連續性和數據準確性。
