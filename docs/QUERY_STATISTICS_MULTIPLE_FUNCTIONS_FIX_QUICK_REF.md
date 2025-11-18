# Query Statistics 多個函式名稱問題修復 - 快速參考

## 修復內容

✅ **修復日期**: 2025-11-08  
✅ **影響範圍**: query_statistics.csv 的函式名稱欄位  
✅ **核心文件**: `src/query_statistics.py`

---

## 修復前後對比

### 修復前（錯誤）
當 prompt.txt 包含多個函式時，CSV 顯示所有函式：

```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__、parent_branch_hash,0,,,,
examples/apps/news-use/news_monitor.py,monitor、run_once、save_article,0,,,,
```
→ **錯誤**：顯示了多個函式名稱

### 修復後（正確）
CSV 只顯示第一個函式：

```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__,0,,,,
examples/apps/news-use/news_monitor.py,monitor,0,,,,
```
→ **正確**：只顯示第一個函式名稱

---

## 修復邏輯

在兩個關鍵方法中添加過濾：

### 1. `_split_function_key()`
```python
# 如果函式名稱包含多個函式（用頓號分隔），只取第一個
if '、' in function_name:
    function_name = function_name.split('、')[0].strip()
```

### 2. `_read_current_csv()`
```python
# 如果函式名稱包含多個函式（用頓號分隔），只取第一個
if '、' in function_name:
    function_name = function_name.split('、')[0].strip()
```

---

## 為什麼只取第一個函式？

系統設計原則：

| 模組 | 說明 | 行號參考 |
|------|------|---------|
| AS 模式 | 明確規定只取第一個函數 | `artificial_suicide_mode.py` line 198, 261, 785 |
| CWE 掃描 | 統一只取第一個函式 | `cwe_scan_manager.py` line 112 |
| Coding Instruction | 確保處理同一個函式 | 避免 Query/Coding Phase 不一致 |

---

## 測試驗證

```
✅ 正確：只有一個函式名稱
  函式名稱: __hash__
  
✅ 正確：只有一個函式名稱
  函式名稱: monitor
```

---

## 影響的文件

修復後，以下路徑的 CSV 文件將正確顯示單一函式名稱：

```
CWE_Result/CWE-{type}/query_statistics/{project}.csv
```

---

## 如何重新生成統計

如果舊的 query_statistics.csv 包含多個函式名稱：

```python
from pathlib import Path
from src.query_statistics import QueryStatistics

# 讀取 prompt.txt 並只提取第一個函式
function_list = []
with open(f"projects/{project_name}/prompt.txt", 'r') as f:
    for line in f:
        parts = line.strip().split('|')
        if len(parts) == 2:
            filepath = parts[0].strip()
            functions_part = parts[1].strip()
            
            # 只取第一個函式
            if '、' in functions_part:
                first_function = functions_part.split('、')[0].strip()
            else:
                first_function = functions_part.strip()
            
            function_list.append(f"{filepath}_{first_function}")

# 重新初始化
generator = QueryStatistics(
    project_name=project_name,
    cwe_type="327",
    total_rounds=4,
    function_list=function_list
)
generator.initialize_csv()

# 更新所有輪次
for round_num in range(1, 5):
    generator.update_round_result(round_num)
```

---

## 常見問題

**Q: 為什麼 prompt.txt 允許多個函式但只處理第一個？**  
A: 保留多個函式名稱是為了記錄完整資訊，但系統設計只處理第一個以避免複雜性和不一致性。

**Q: 如果我想處理多個函式怎麼辦？**  
A: 需要在 prompt.txt 中為每個函式創建獨立的行：
```
filepath1|function1()
filepath1|function2()
filepath1|function3()
```

**Q: 修復後舊的CSV會自動更新嗎？**  
A: 修復後，讀取和寫入CSV時會自動過濾多個函式名稱。建議重新生成以確保一致性。

---

## 相關文檔

- 詳細文檔: `docs/QUERY_STATISTICS_MULTIPLE_FUNCTIONS_FIX.md`
- 掃描失敗顯示: `docs/QUERY_STATISTICS_FAILED_DISPLAY_FIX.md`
- 漏洞聚合: `docs/VULNERABILITY_AGGREGATION_FIX.md`
- 原始指南: `.github/copilot-instructions.md`
