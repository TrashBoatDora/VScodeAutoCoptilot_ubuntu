# Query Statistics 掃描失敗顯示修復 - 快速參考

## 修復內容

✅ **修復日期**: 2025-11-08  
✅ **影響範圍**: query_statistics.csv 的掃描失敗狀態顯示  
✅ **核心文件**: `src/query_statistics.py`

---

## 修復前後對比

### 修復前（錯誤）
當掃描狀態為 `failed` 時，query_statistics.csv 顯示 `0`：

```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,0,,,,
```
→ **誤導**：0 表示無漏洞，但實際上是掃描失敗

### 修復後（正確）
當掃描狀態為 `failed` 時，query_statistics.csv 正確顯示 `failed`：

```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,failed,,,,
```
→ **正確**：明確標示掃描失敗，可以立即識別問題

---

## 修復邏輯

在 `_read_round_scan()` 中改變判斷順序：

**原始邏輯（錯誤）**：
1. 檢查是否有成功
2. 都不成功 → failed

**修復後（正確）**：
1. **優先檢查 failed**：有任何掃描器失敗 → failed
2. 檢查是否有成功 → 使用成功結果
3. 都是 unknown → failed

---

## query_statistics.csv 欄位值說明

| 值 | 意義 | 何時出現 |
|----|------|----------|
| `數字` (如 `3`) | 發現漏洞數量 | 掃描成功且發現漏洞 |
| `0` | 無漏洞 | 掃描成功但未發現漏洞 |
| **`failed`** | 掃描失敗 | 語法錯誤、超時、檔案不存在等 |
| `#` | 已跳過 | 前幾輪已發現漏洞 |
| `All-Safe` | 全部安全 | 所有輪次都無漏洞 |
| 空白 | 未執行 | 該輪尚未掃描 |

---

## 測試驗證

```bash
# 測試已通過
✅ 掃描失敗時正確顯示 'failed'
✅ 掃描成功無漏洞時正確顯示 '0'
```

### 測試案例
- `browser_use/agent/service.py` | `replace_url`: failed ✅
- `browser_use/dom/views.py` | `__hash__`: 0 ✅

---

## 影響的文件

修復後，以下路徑的 CSV 文件將正確顯示 failed 狀態：

```
CWE_Result/CWE-{type}/query_statistics/{project}.csv
```

---

## 如何重新生成統計

如果需要更新舊專案的 query_statistics.csv：

```python
from pathlib import Path
from src.query_statistics import QueryStatistics

# 讀取函式列表
function_list = []
with open(f"projects/{project_name}/prompt.txt", 'r') as f:
    for line in f:
        if '|' in line:
            filepath, funcname = line.strip().split('|', 1)
            function_list.append(f"{filepath}_{funcname}()")

# 創建統計器
generator = QueryStatistics(
    project_name=project_name,
    cwe_type="327",
    total_rounds=4,
    function_list=function_list
)

# 初始化並更新所有輪次
generator.initialize_csv()
for round_num in range(1, 5):
    generator.update_round_result(round_num)
```

---

## 常見問題

**Q: 為什麼要顯示 failed 而不是 0？**  
A: 0 表示「掃描成功但無漏洞」，failed 表示「掃描失敗無結果」。兩者意義完全不同，混淆會導致誤判。

**Q: 什麼情況會導致 failed？**  
A: 常見原因包括：
- 語法錯誤（syntax error while parsing AST）
- 檔案不存在
- 掃描超時
- 編碼問題

**Q: 如果 Bandit 失敗但 Semgrep 成功，會顯示什麼？**  
A: 修復後會顯示 `failed`（優先顯示失敗狀態）。這確保不會遺漏任何掃描問題。

**Q: 舊的 query_statistics.csv 會自動更新嗎？**  
A: 不會。需要重新執行統計生成（見上方腳本）。

---

## 相關文檔

- 詳細文檔: `docs/QUERY_STATISTICS_FAILED_DISPLAY_FIX.md`
- 掃描結果聚合: `docs/VULNERABILITY_AGGREGATION_FIX.md`
- 原始指南: `.github/copilot-instructions.md`
