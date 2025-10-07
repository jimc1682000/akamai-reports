# Commit Message Guide

本文檔說明如何撰寫符合 Conventional Commits 規範的 commit 訊息。

## 為什麼要使用 Conventional Commits？

1. **自動化 CHANGELOG 生成** - 使用 git-cliff 自動生成結構化的變更日誌
2. **語義化版本控制** - 根據 commit 類型自動決定版本號升級（major/minor/patch）
3. **更好的協作** - 團隊成員能快速理解每個變更的目的
4. **自動化工具整合** - CI/CD 工具可以根據 commit 類型執行不同的動作

## Commit Message 格式

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### 基本範例

```bash
feat(api): add V2 emissions API support
fix(config): correct CP code validation logic
docs(readme): update installation instructions
```

### 完整範例

```bash
feat(cache): implement response caching with TTL

Add a file-based caching system for API responses to reduce
unnecessary API calls during development and testing.

- SHA256-based cache keys
- Configurable TTL (default: 2 hours)
- Cache statistics tracking
- Enable via ENABLE_API_CACHE=1 environment variable

Closes #42
```

## Commit Types

| Type | 說明 | 版本影響 | 範例 |
|------|------|----------|------|
| `feat` | 新增功能 | MINOR (0.1.0 → 0.2.0) | `feat(api): add pagination support` |
| `fix` | Bug 修復 | PATCH (0.1.0 → 0.1.1) | `fix(auth): resolve token expiry issue` |
| `docs` | 文檔更新 | 無 | `docs(api): update endpoint documentation` |
| `refactor` | 重構代碼 | PATCH | `refactor(parser): simplify date handling` |
| `test` | 測試相關 | 無 | `test(integration): add circuit breaker tests` |
| `chore` | 雜項任務 | 無 | `chore(deps): update requests to 2.31.0` |
| `perf` | 性能優化 | PATCH | `perf(cache): add connection pooling` |
| `style` | 代碼格式 | 無 | `style: fix code formatting` |
| `ci` | CI/CD 變更 | 無 | `ci: add GitHub Actions workflow` |
| `build` | 構建系統 | 無 | `build: update webpack config` |
| `security` | 安全性改進 | PATCH | `security: sanitize log output` |
| `revert` | 回退變更 | 視情況 | `revert: revert feat(api) commit` |

## Scope（可選）

Scope 描述變更影響的範圍，常見範例：

- `api` - API 相關變更
- `config` - 配置系統
- `cache` - 快取機制
- `auth` - 認證相關
- `test` - 測試相關
- `docs` - 文檔相關
- `deps` - 依賴套件

## Subject（必填）

Subject 是對變更的簡短描述（建議 50 字元以內）：

**✅ 好的範例**：
```bash
feat(api): add retry mechanism for failed requests
fix(config): handle missing configuration file
docs(readme): clarify installation steps
```

**❌ 不好的範例**：
```bash
update code
fix bug
wip
```

**撰寫建議**：
- 使用祈使句（"add" 而非 "added"）
- 不要大寫開頭（除非是專有名詞）
- 結尾不要加句號
- 描述做了什麼，而非為什麼做

## Breaking Changes

如果變更包含不向下兼容的修改，使用 `!` 標記：

```bash
feat(api)!: change response format to v2 schema

BREAKING CHANGE: The API response format has changed.
Clients must update to handle the new format.
```

## 使用 Commitizen 輔助工具

### 互動式 Commit

```bash
# 啟動互動式 commit 工具
cz commit

# 或使用縮寫
cz c
```

工具會引導你逐步完成：
1. 選擇 commit 類型
2. 輸入 scope（可選）
3. 輸入簡短描述
4. 輸入詳細說明（可選）
5. 選擇是否為 breaking change

### 直接使用 Git Commit

```bash
# 標準用法（會自動驗證）
git commit -m "feat(api): add new endpoint"

# 不符合規範會被拒絕
git commit -m "updated some files"  # ❌ 會失敗
```

## 常見問題

### Q1: 如果忘記遵循規範怎麼辦？

A: Pre-commit hook 會自動檢查並拒絕不符合規範的 commit。你需要修改 commit message：

```bash
# 修改最後一次 commit 訊息
git commit --amend

# 或使用 commitizen
cz commit --amend
```

### Q2: 一次變更涉及多個類型怎麼辦？

A: 選擇最主要的變更類型，或將變更拆分成多個 commit：

```bash
# 方案 1: 選擇主要類型
git commit -m "feat(api): add caching with tests"

# 方案 2: 拆分 commits（推薦）
git add src/cache.py
git commit -m "feat(cache): implement response caching"

git add tests/test_cache.py
git commit -m "test(cache): add cache functionality tests"
```

### Q3: Merge commits 需要遵循規範嗎？

A: Merge commits 通常會自動生成訊息，不需要特別遵循規範。但如果手動編輯 merge commit，建議遵循規範。

### Q4: 如何暫時跳過驗證？

A: 不建議跳過驗證，但緊急情況下可以使用：

```bash
git commit --no-verify -m "emergency fix"
```

## 完整工作流程範例

```bash
# 1. 開發新功能
vim src/new_feature.py

# 2. 執行代碼品質檢查
task quality

# 3. 執行測試
task test-coverage

# 4. 暫存變更
git add src/new_feature.py

# 5. 使用 commitizen 創建 commit
cz commit
# 或直接使用 git commit
git commit -m "feat(feature): implement new feature with caching"

# 6. Push 到遠端
git push origin main
```

## 檢查現有 Commits

```bash
# 查看最近的 commits 是否符合規範
git log --oneline -10

# 使用 commitizen 驗證特定範圍的 commits
cz check --rev-range HEAD~10..HEAD
```

## 參考資源

- [Conventional Commits 官方規範](https://www.conventionalcommits.org/)
- [Commitizen 官方文檔](https://commitizen-tools.github.io/commitizen/)
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)
- [Semantic Versioning](https://semver.org/)

---

**提示**：如果對 commit 訊息有疑問，使用 `cz commit` 互動式工具會是最安全的選擇！
