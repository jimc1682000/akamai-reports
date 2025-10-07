# ADR-0001: Circuit Breaker Pattern for API Resilience

## Status
**Accepted** - Implemented on 2025-10-05

## Context
Akamai Traffic Report 需要頻繁呼叫 V2 Traffic 和 Emissions APIs 來生成報表。在生產環境中觀察到以下問題：

### 問題
1. **API 偶爾會返回 5xx 錯誤**（約 2-5% 的請求）
2. **重試機制會加劇問題**：當 API 不穩定時，大量重試反而造成更多負載
3. **級聯失敗**：一個 API 的失敗會拖慢整個報表生成流程
4. **浪費資源**：對已知故障的 API 持續重試浪費時間和網路資源

### 業務影響
- Weekly report 生成時間從 10 秒增加到 2+ 分鐘（因為反覆重試）
- Cron job timeout（設定為 5 分鐘）
- 運維團隊需要手動重啟腳本

## Decision
實作 **Circuit Breaker Pattern**，具有以下特性：

### 設計
```
States: CLOSED → OPEN → HALF_OPEN → CLOSED
                    ↑_______|

CLOSED: 正常運行，允許所有請求
OPEN: API 失敗超過閾值，快速失敗不呼叫
HALF_OPEN: 等待後嘗試恢復，測試 API 是否修復
```

### 參數配置
- **Failure Threshold**: 3 次連續失敗 → OPEN
- **Recovery Timeout**: 30 秒後進入 HALF_OPEN
- **Success Threshold**: 2 次成功 → CLOSED
- **Per-API Instance**: Traffic 和 Emissions API 各自獨立的 circuit breaker

## Alternatives Considered

### 1. Simple Retry with Exponential Backoff
**優點**：
- 實作簡單
- 標準做法

**缺點**：
- ❌ 不能阻止對已知故障服務的請求
- ❌ API 大規模故障時會持續浪費資源
- ❌ 無法快速失敗

**為何不採用**：無法解決級聯失敗問題

### 2. Rate Limiter
**優點**：
- 控制請求頻率
- 保護 API 不被 overwhelm

**缺點**：
- ❌ 不能偵測 API 健康狀態
- ❌ 無法自動恢復
- ❌ 只是延遲問題，不是解決問題

**為何不採用**：治標不治本

### 3. Manual Failover
**優點**：
- 人工控制，靈活

**缺點**：
- ❌ 需要 24/7 人工監控
- ❌ 反應時間慢
- ❌ 不適合自動化 cron job

**為何不採用**：違反自動化原則

## Consequences

### Positive
✅ **快速失敗**：OPEN 狀態下立即返回錯誤（~1ms），不浪費時間
✅ **自動恢復**：30 秒後自動嘗試恢復，無需人工介入
✅ **保護 API**：減少對故障 API 的請求壓力
✅ **可觀測性**：記錄狀態轉換，便於監控和 debug

### Negative
⚠️ **額外複雜度**：需要維護狀態機邏輯
⚠️ **誤判風險**：短暫網路問題可能觸發 circuit open
⚠️ **測試困難**：需要模擬各種故障場景

### Mitigation
- 設定合理的閾值避免誤判（3 次失敗才 open）
- 完整的單元測試覆蓋所有狀態轉換（17 test cases）
- 詳細日誌記錄所有狀態變化

## Implementation
- **檔案**: `tools/lib/resilience/circuit_breaker.py`
- **測試**: `tests/test_circuit_breaker.py` (17 test cases)
- **使用**: Traffic API 和 Emissions API 各自獨立實例
- **監控**: 透過結構化日誌記錄狀態轉換

## References
- [Martin Fowler - Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Microsoft - Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- Implementation commit: `62a117f`

## Notes
考慮過 state persistence（狀態持久化），但因為這是 batch script（非長時間運行服務），每次執行都會重置狀態，因此延後到 V3.0。

---
**Last Updated**: 2025-10-07
**Author**: Development Team
**Reviewers**: Architecture Review Board
