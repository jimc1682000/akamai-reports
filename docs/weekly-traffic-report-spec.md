# 週報流量數據腳本需求規格

## 專案概述

開發自動化週報腳本，用於定期抓取 Akamai CDN 流量數據，提供業務團隊週報和計費預估功能。

### 背景
- Akamai Traffic Reports (V1) 即將於 2025-11-05 (GUI) / 2026-02-05 (API) 停止服務
- 需要建立基於 V2 API 的自動化數據抓取機制
- 根據前期分析，確立了準確的計費預估公式：`Daily Usage ≈ V2 API Edge × 1.0`

## 功能需求

### 1. 數據抓取項目

#### V2 Traffic API (delivery/traffic/current)
使用 `time5minutes` 維度，抓取以下 Edge 流量數據：

- **總體 Edge 流量** - 所有配置的 CP codes 的總和，單位 TB (實際 CP codes 請查詢 Akamai Console)
- **服務 1** - CP code PLACEHOLDER_CP_CODE_001 (服務描述請參考 config.json)，單位 TB
- **服務 2** - CP code PLACEHOLDER_CP_CODE_002 (服務描述請參考 config.json)，單位 TB
- **服務 3** - CP code PLACEHOLDER_CP_CODE_003 (服務描述請參考 config.json)，單位 GB
- **服務 4** - CP code PLACEHOLDER_CP_CODE_004 (服務描述請參考 config.json)，單位 GB

#### V2 Emissions API (delivery/traffic/emissions)
使用 `time1day` 維度和 `country` 過濾，抓取以下地區 Edge 流量數據：

- **地區 1** - 單位 TB
- **地區 2** - 單位 TB
- **地區 3** - 單位 TB

### 2. 時間處理需求

#### 預設模式（自動）
- 計算並使用上週時間範圍（週日 00:00 UTC+0 ~ 週六 23:59 UTC+0）
- 週期定義：週日為一週開始，週六為一週結束
- 執行命令：`python weekly_traffic_report.py`

#### 手動模式（指定時間）
- 支援命令行參數指定任意時間範圍
- 時間自動轉換為 UTC+0 格式
- 執行命令：`python weekly_traffic_report.py --start YYYY-MM-DD --end YYYY-MM-DD`

#### 首次測試
- 目標時間範圍：YYYY-MM-DD ~ YYYY-MM-DD (週日~週六)
- 時區：UTC+0

### 3. 計費預估功能

基於前期數據分析結果，提供準確的計費預估：
```
預估計費用量 = V2 API 總 Edge 流量 × 1.0
```

## 技術規格

### API 配置詳情

#### V2 Traffic API 配置
```json
{
  "dimensions": ["time5minutes"],
  "metrics": ["edgeBytesSum"],
  "filters": [{
    "dimensionName": "cpcode",
    "operator": "IN_LIST",
    "expressions": ["PLACEHOLDER_CP_CODE_XXX", ...] // 多個 CP codes (實際值請查詢 Akamai Console)
  }],
  "sortBys": [{"name": "time5minutes", "sortOrder": "ASCENDING"}],
  "limit": 50000
}
```

#### V2 Emissions API 配置
```json
{
  "dimensions": ["time1day", "country"],
  "metrics": ["edgeBytesSum"],
  "filters": [{
    "dimensionName": "cpcode",
    "operator": "IN_LIST",
    "expressions": ["PLACEHOLDER_CP_CODE_XXX", ...] // 多個 CP codes (實際值請查詢 Akamai Console)
  }, {
    "dimensionName": "country",
    "operator": "IN_LIST",
    "expressions": ["REGION_CODE_1", "REGION_CODE_2", "REGION_CODE_3"]
  }],
  "limit": 50000
}
```

### CP Codes 配置

**實際 CP codes 請查詢 Akamai Console，並配置於 config.json**

```python
# 總共需配置的 CP codes 數量依業務需求而定 需要配置
# 請參考 config.template.json 的格式

ALL_CP_CODES = [
    "PLACEHOLDER_CP_CODE_001",
    "PLACEHOLDER_CP_CODE_002",
    # ... 數量依業務需求而定
]

# 特殊服務對應 (實際配置請參考 config.json)
SERVICE_MAPPINGS = {
    "PLACEHOLDER_CP_CODE_001": {"name": "服務名稱1", "unit": "TB"},
    "PLACEHOLDER_CP_CODE_002": {"name": "服務名稱2", "unit": "TB"},
    "PLACEHOLDER_CP_CODE_003": {"name": "服務名稱3", "unit": "GB"},
    "PLACEHOLDER_CP_CODE_004": {"name": "服務名稱4", "unit": "GB"}
}

# 地區對應
REGION_MAPPINGS = {
    "REGION_CODE_1": "地區名稱 1",
    "REGION_CODE_2": "地區名稱 2",
    "REGION_CODE_3": "地區名稱 3"
}
```

### 數據處理要求

#### 週期定義
- **一週定義**：週日 00:00:00 UTC+0 ~ 週六 23:59:59 UTC+0
- **自動模式**：計算上一個完整週期
- **手動模式**：指定日期自動轉換為對應的 UTC+0 時間範圍

#### 單位轉換
- Bytes → TB：`bytes_value / (1024^4)`
- Bytes → GB：`bytes_value / (1024^3)`
- 保留小數點後 2 位精度

#### 計費預估計算
```python
billing_estimate = total_edge_tb * 1.0
```

### 輸出格式規格

```
==========================================
📊 週報流量數據 (YYYY-MM-DD ~ YYYY-MM-DD)
==========================================

🔍 V2 Traffic API 數據 (time5minutes):
   總Edge流量:           XXX.XX TB
   └─ 預估計費用量:      XXX.XX TB (×1.0)

   服務1 (CP_CODE_001):  XXX.XX TB
   服務2 (CP_CODE_002):  XXX.XX TB
   服務3 (CP_CODE_003):  XXX.XX GB
   服務4 (CP_CODE_004):  XXX.XX GB

🌏 V2 Emissions API 數據 (time1day):
   地區 1:            XXX.XX TB
   地區 2:            XXX.XX TB
   地區 3:          XXX.XX TB
   地區小計:             XXX.XX TB

📈 數據摘要:
   Traffic API 總計:     XXX.XX TB
   Emissions API 總計:   XXX.XX TB
   預估計費用量:         XXX.XX TB (×1.0)
```

## 系統架構

### 腳本結構
```
weekly_traffic_report.py
├── 命令行參數處理
├── 時間計算模組
│   ├── 自動計算上週範圍
│   └── 手動時間範圍處理
├── API 查詢模組
│   ├── V2 Traffic API 查詢
│   └── V2 Emissions API 查詢
├── 數據處理模組
│   ├── 單位轉換
│   ├── 數據聚合
│   └── 計費預估計算
└── 報表輸出模組
    └── 控制台格式化輸出
```

### 錯誤處理策略

#### API 限制處理
- 50,000 數據點限制檢查
- HTTP 錯誤碼處理
- 網路超時重試機制

#### 數據驗證
- 空值和異常值檢查
- CP code 存在性驗證
- 時間範圍合理性檢查

### 配置管理

#### 可配置項目
- CP codes 清單
- 計費預估係數 (1.0)
- API 端點 URLs
- 重試次數和超時設定
- 地區代碼對應

## 部署和使用

### 系統需求
- Python 3.8+
- `requests` 套件
- `akamai-edgegrid-auth` 套件
- 有效的 `.edgerc` 認證檔案

### 執行方式

#### 日常使用（自動上週）
```bash
cd /path/to/akamai-traffic
python weekly_traffic_report.py
```

#### 指定時間範圍
```bash
python weekly_traffic_report.py --start YYYY-MM-DD --end YYYY-MM-DD
```

#### 未來 Cron 整合（可選）
```bash
# 每週一中午12:00執行
0 12 * * 1 cd /path/to/akamai-traffic && python weekly_traffic_report.py
```

## 後續擴展規劃

### 短期擴展
- CSV/JSON 格式輸出選項
- 郵件通知功能
- 歷史數據比較

### 中期擴展
- 數據庫儲存整合
- Web Dashboard 介面
- 告警機制

### 長期規劃
- 多租戶支援
- 自動化報表排程系統
- 預測分析功能

## 測試計劃

### 功能測試
- 時間計算邏輯驗證
- API 查詢正確性測試
- 數據處理準確性驗證
- 輸出格式檢查

### 整合測試
- 完整流程端到端測試
- 不同時間範圍測試
- 錯誤情況處理測試

### 效能測試
- API 回應時間測量
- 大數據量處理測試
- 記憶體使用量監控

---

*文件版本: 1.0*
*建立日期: 2024-09-24*
*最後更新: 2024-09-24*
