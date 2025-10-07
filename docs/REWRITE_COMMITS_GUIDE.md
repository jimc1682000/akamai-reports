# Commit History Rewrite Guide

本指南說明如何將現有的非 Conventional Commits 格式改寫為標準格式。

## ⚠️ 重要警告

**重寫 commit 歷史會：**
- 改變所有 commit SHA
- 需要 force push 到遠端
- 可能影響其他協作者（如果有的話）

**只在以下情況執行：**
- ✅ 你已經備份了 repository
- ✅ 沒有其他人正在使用這個分支
- ✅ 你了解 git rebase 的風險

## 📋 需要重寫的 Commits

| 原始訊息 | 建議的新訊息 | 類型 |
|---------|-------------|------|
| `Initial commit: Akamai V2 Traffic Reporting System` | `feat: initialize Akamai V2 Traffic Reporting System` | feat |
| `Implement Dependency Injection Pattern` | `feat(di): implement Dependency Injection pattern with ServiceContainer` | feat |
| `Implement Circuit Breaker Pattern` | `feat(resilience): implement Circuit Breaker pattern for API protection` | feat |
| `Implement Concurrent API Calls` | `feat(performance): implement concurrent API calls with ThreadPoolExecutor` | feat |
| `Fix integration tests for ServiceContainer pattern` | `fix(tests): fix integration tests for ServiceContainer pattern` | fix |
| `Implement Structured Logging` | `feat(logging): implement structured logging with JSON format` | feat |
| `Fix test_get_all_regional_traffic for concurrent execution` | `fix(tests): fix test_get_all_regional_traffic for concurrent execution` | fix |
| `Implement Response Caching System` | `feat(cache): implement response caching system with TTL` | feat |
| `Merge pull request #1 ...` | 保持不變（merge commits 可以不遵循規範） | - |

## 🚀 方法 1：使用自動化腳本（推薦）

```bash
# 執行互動式重寫腳本
./scripts/interactive_rewrite.sh
```

腳本會：
1. 自動創建備份分支
2. 顯示需要重寫的 commits
3. 打開互動式 rebase 編輯器
4. 提供重寫建議檔案

## 🔧 方法 2：手動執行（完全控制）

### 步驟 1: 創建備份

```bash
# 創建備份分支
git branch backup-before-rewrite-$(date +%Y%m%d)

# 確認備份
git branch -l "backup-*"
```

### 步驟 2: 開始互動式 Rebase

```bash
# 從 root commit 開始 rebase
git rebase -i --root
```

### 步驟 3: 在編輯器中標記要修改的 Commits

編輯器會顯示類似：

```
pick ce41f4f Initial commit: Akamai V2 Traffic Reporting System
pick c9ddcce Implement Dependency Injection Pattern
pick c776566 Implement Circuit Breaker Pattern
pick 729f50b Implement Concurrent API Calls
pick 9afefd2 Fix integration tests for ServiceContainer pattern
pick 7418fc4 Implement Structured Logging
pick 458e093 Fix test_get_all_regional_traffic for concurrent execution
pick bf2af87 Implement Response Caching System
...
```

**將需要修改的 commits 的 `pick` 改為 `reword` (或簡寫 `r`)**：

```
reword ce41f4f Initial commit: Akamai V2 Traffic Reporting System
reword c9ddcce Implement Dependency Injection Pattern
reword c776566 Implement Circuit Breaker Pattern
reword 729f50b Implement Concurrent API Calls
reword 9afefd2 Fix integration tests for ServiceContainer pattern
reword 7418fc4 Implement Structured Logging
reword 458e093 Fix test_get_all_regional_traffic for concurrent execution
reword bf2af87 Implement Response Caching System
pick ff55105 Merge pull request #1 from jimc1682000/feature/architecture-improvements
pick 3a032ed fix: Update .gitguardian.yaml with correct syntax
...
```

保存並關閉編輯器。

### 步驟 4: 逐個修改 Commit Messages

Git 會依次打開編輯器讓你修改每個標記為 `reword` 的 commit：

**Commit 1:**
```
原始: Initial commit: Akamai V2 Traffic Reporting System
改為: feat: initialize Akamai V2 Traffic Reporting System
```

**Commit 2:**
```
原始: Implement Dependency Injection Pattern
改為: feat(di): implement Dependency Injection pattern with ServiceContainer
```

**Commit 3:**
```
原始: Implement Circuit Breaker Pattern
改為: feat(resilience): implement Circuit Breaker pattern for API protection
```

**Commit 4:**
```
原始: Implement Concurrent API Calls
改為: feat(performance): implement concurrent API calls with ThreadPoolExecutor
```

**Commit 5:**
```
原始: Fix integration tests for ServiceContainer pattern
改為: fix(tests): fix integration tests for ServiceContainer pattern
```

**Commit 6:**
```
原始: Implement Structured Logging
改為: feat(logging): implement structured logging with JSON format
```

**Commit 7:**
```
原始: Fix test_get_all_regional_traffic for concurrent execution
改為: fix(tests): fix test_get_all_regional_traffic for concurrent execution
```

**Commit 8:**
```
原始: Implement Response Caching System
改為: feat(cache): implement response caching system with TTL
```

每次修改後保存並關閉編輯器，Git 會自動繼續到下一個。

### 步驟 5: 驗證結果

```bash
# 查看重寫後的 commit history
git log --oneline -15

# 應該看到類似：
# abc1234 feat(cache): implement response caching system with TTL
# def5678 fix(tests): fix test_get_all_regional_traffic for concurrent execution
# ...
```

### 步驟 6: 推送到遠端（如果需要）

```bash
# 使用 --force-with-lease 更安全（會檢查遠端是否有新 commits）
git push --force-with-lease origin main

# 或使用一般 force push
git push --force origin main
```

## 🔄 如果出錯了怎麼辦？

### 在 Rebase 過程中中止

```bash
# 中止 rebase，恢復到 rebase 前的狀態
git rebase --abort
```

### Rebase 完成後想要撤銷

```bash
# 恢復到備份分支
git reset --hard backup-before-rewrite-20250107

# 查看目前狀態
git log --oneline -10
```

### 刪除備份分支（確認沒問題後）

```bash
# 列出所有備份分支
git branch -l "backup-*"

# 刪除特定備份
git branch -D backup-before-rewrite-20250107
```

## ✅ 完成後的清理

### 1. 更新 git-cliff 配置

重寫完成後，可以移除 `cliff.toml` 中的 legacy commit parsers：

```bash
# 編輯 cliff.toml，移除 "# Legacy commits" 區塊
```

### 2. 測試 CHANGELOG 生成

```bash
# 預覽 CHANGELOG
task changelog-preview

# 生成完整 CHANGELOG
task changelog-generate
```

### 3. 初始化版本系統

```bash
# 初始化版本號
task version-init

# 創建第一個正式版本
task bump-minor  # 會創建 v0.1.0
```

## 📊 Before & After 比較

### Before (非標準格式)
```
ce41f4f Initial commit: Akamai V2 Traffic Reporting System
c9ddcce Implement Dependency Injection Pattern
c776566 Implement Circuit Breaker Pattern
458e093 Fix test_get_all_regional_traffic for concurrent execution
```

### After (Conventional Commits)
```
abc1234 feat: initialize Akamai V2 Traffic Reporting System
def5678 feat(di): implement Dependency Injection pattern with ServiceContainer
ghi9012 feat(resilience): implement Circuit Breaker pattern for API protection
jkl3456 fix(tests): fix test_get_all_regional_traffic for concurrent execution
```

## 💡 最佳實踐

1. **在非工作時間執行** - 避免影響其他開發者
2. **先在本地驗證** - 確認 rebase 成功後再 push
3. **通知團隊成員** - 如果是共享分支，提前通知
4. **保留備份** - 至少保留備份幾天
5. **分步驟執行** - 不要急，每一步都確認正確

## 🔗 相關資源

- [Conventional Commits 規範](https://www.conventionalcommits.org/)
- [Git Rebase 文檔](https://git-scm.com/docs/git-rebase)
- [Git Force Push 安全指南](https://git-scm.com/docs/git-push#Documentation/git-push.txt---force-with-lease)

---

**提示**：如果你不確定或擔心出錯，可以先在測試分支上練習：
```bash
git checkout -b test-rewrite
./scripts/interactive_rewrite.sh
# 測試完成後刪除
git checkout main
git branch -D test-rewrite
```
