# Query Statistics 多個函式名稱問題修復文檔

**修復日期**: 2025-11-08  
**問題編號**: N/A  
**修復範圍**: query_statistics.csv 中函式名稱欄位顯示多個函式的問題

---

## 問題描述

在 `query_statistics.csv` 中，當 `prompt.txt` 的某行包含多個函式名稱（用頓號「、」分隔）時，CSV 會錯誤地顯示所有函式名稱，而不是只顯示第一個。

### 問題範例

**prompt.txt**:
```
browser_use/dom/views.py|__hash__()、parent_branch_hash()
examples/apps/news-use/news_monitor.py|monitor()、run_once()、save_article()
```

**錯誤的 query_statistics.csv**:
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__、parent_branch_hash,0,,,,
examples/apps/news-use/news_monitor.py,monitor、run_once、save_article,0,,,,
```
→ 顯示了所有函式名稱

**正確的 query_statistics.csv**:
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__,0,,,,
examples/apps/news-use/news_monitor.py,monitor,0,,,,
```
→ 應該只顯示第一個函式名稱

---

## 根本原因

雖然在 AS 模式的 `_parse_prompt_line()` 方法中正確提取了第一個函式，但在 query_statistics.py 中有兩個地方沒有過濾多個函式名稱：

1. **`_split_function_key()`**：當分離檔案路徑和函式名稱後，如果函式名稱包含頓號「、」，會保留所有函式
2. **`_read_current_csv()`**：讀取現有CSV時，直接使用了"函式名稱"欄位，沒有過濾

### 問題流程

1. 初始化時，`function_list` 是正確的（只有第一個函式）
2. 但如果CSV中已經有多個函式名稱（例如從舊版本產生的），`_read_current_csv()` 會讀取並保留
3. 更新CSV時，`_write_updated_csv()` 再次寫入多個函式名稱，導致問題持續存在

---

## 修復方案

### 修改文件
- **檔案**: `src/query_statistics.py`
- **方法**: `_split_function_key()`, `_read_current_csv()`

### 修復邏輯

在兩個關鍵方法中添加過濾邏輯，只保留第一個函式名稱：

#### 1. `_split_function_key()` 修復

```python
def _split_function_key(self, function_key: str) -> tuple:
    """分離檔案路徑和函數名稱"""
    # ... 現有邏輯 ...
    
    filepath = parts[0] + '.py'
    function_name = parts[1]
    
    # 🔧 修復：如果函式名稱包含多個函式（用頓號分隔），只取第一個
    if '、' in function_name:
        function_name = function_name.split('、')[0].strip()
    
    return (filepath, function_name)
```

#### 2. `_read_current_csv()` 修復

```python
def _read_current_csv(self) -> Optional[Dict[str, Dict]]:
    """讀取現有的 CSV 檔案"""
    # ... 讀取CSV ...
    
    filepath = row.get('檔案路徑', '').strip()
    function_name = row.get('函式名稱', '').strip()
    
    # 🔧 修復：如果函式名稱包含多個函式（用頓號分隔），只取第一個
    if '、' in function_name:
        function_name = function_name.split('、')[0].strip()
    
    function_key = f"{filepath}::{function_name}"
    # ...
```

---

## 測試驗證

### 測試腳本輸出

**修復前**:
```
⚠️  警告：包含多個函式名稱！
  函式名稱: __hash__、parent_branch_hash
```

**修復後**:
```
✅ 正確：只有一個函式名稱
  函式名稱: __hash__
```

### 測試結果

| 檔案路徑 | 原始 prompt.txt | 修復前 CSV | 修復後 CSV |
|---------|----------------|-----------|-----------|
| browser_use/dom/views.py | `__hash__()、parent_branch_hash()` | `__hash__、parent_branch_hash` | ✅ `__hash__` |
| examples/apps/news-use/news_monitor.py | `monitor()、run_once()、save_article()` | `monitor、run_once、save_article` | ✅ `monitor` |

---

## 影響範圍

### 正面影響
1. **一致性**：確保只顯示第一個函式名稱，與 AS 模式的處理邏輯一致
2. **可讀性**：CSV 更簡潔，不會顯示不相關的函式名稱
3. **正確性**：符合系統設計原則（只掃描第一個函式）

### 相容性
- ✅ **向後相容**：修復會自動過濾舊CSV中的多個函式名稱
- ✅ **AS模式**：與 `_parse_prompt_line()` 的邏輯一致
- ✅ **非AS模式**：同樣適用（如果使用多函式格式）

---

## 為什麼只取第一個函式？

根據系統設計：

1. **AS 模式規定**：`artificial_suicide_mode.py` line 198, 261, 785 明確說明「只取第一個函數」
2. **CWE 掃描限制**：`cwe_scan_manager.py` line 112 說明「統一只取第一個函式」
3. **Coding Instruction 一致性**：確保 Query Phase 和 Coding Phase 處理同一個函式
4. **避免混淆**：防止在不同階段處理不同函式導致結果不一致

---

## 修復前後對比

### 修復前（錯誤）
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__、parent_branch_hash,0,,,,
```
→ 包含多個函式名稱，容易混淆

### 修復後（正確）
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/dom/views.py,__hash__,0,,,,
```
→ 只顯示第一個函式，清晰明確

---

## 相關文件

- `src/query_statistics.py`: Query 統計生成器（核心修復）
- `src/artificial_suicide_mode.py`: AS 模式（`_parse_prompt_line` 提取第一個函式）
- `src/cwe_scan_manager.py`: CWE 掃描管理器（`extract_function_targets_from_prompt` 只取第一個函式）

---

## 後續建議

1. **重新生成舊專案的統計**：如果有舊的 query_statistics.csv 包含多個函式名稱，重新執行統計生成
2. **統一格式規範**：在文檔中明確說明 prompt.txt 的格式，雖然支援多個函式，但系統只會處理第一個
3. **添加驗證**：在初始化時可以添加警告，提示用戶如果 prompt.txt 包含多個函式，只有第一個會被處理

---

## 修復摘要

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| 函式名稱顯示 | 所有函式（用頓號分隔） | 只顯示第一個函式 |
| 與 AS 模式一致性 | 不一致 | ✅ 一致 |
| CSV 可讀性 | 混亂 | ✅ 清晰 |
| 系統設計原則 | 違反 | ✅ 符合 |

✅ **修復完成，測試通過**
