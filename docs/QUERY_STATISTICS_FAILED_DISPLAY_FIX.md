# Query Statistics 掃描失敗顯示修復文檔

**修復日期**: 2025-11-08  
**問題編號**: N/A  
**修復範圍**: query_statistics.csv 中掃描失敗狀態的顯示

---

## 問題描述

在 `query_statistics.csv` 中，當某一輪的掃描狀態為 `failed` 時，CSV 會錯誤地顯示 `0` 而不是 `failed`。

### 問題範例

**掃描結果 CSV** (`CWE_Result/CWE-327/Bandit/{project}/第1輪/{project}_function_level_scan.csv`):
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,browser_use/agent/service.py,replace_url(),replace_url(),,,bandit,,,,failed,syntax error while parsing AST from file
```

**原本的 query_statistics.csv（錯誤）**:
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,0,,,,
```
→ 顯示 `0` 而不是 `failed`

**期望的 query_statistics.csv（正確）**:
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,failed,,,,
```
→ 應該顯示 `failed`

---

## 根本原因

在 `src/query_statistics.py` 的 `_read_round_scan()` 方法中，合併 Bandit 和 Semgrep 結果時的判斷邏輯有誤：

### 原始邏輯（錯誤）

```python
# 判斷掃描狀態：只要有一個成功就算成功
if b_status == 'success' or s_status == 'success':
    # ... 處理成功的情況
else:
    # 兩個都失敗（或都不存在）
    result[func_key] = (-1, 'failed')
```

**問題點**：
- 當 Bandit 狀態是 `'failed'` 而 Semgrep 狀態是 `'unknown'`（不存在）時
- 條件 `b_status == 'success' or s_status == 'success'` 為 False
- 進入 else 分支，應該標記為 failed
- 但後續處理時，可能因為其他邏輯導致顯示為 0

實際上，**只要有一個掃描器明確失敗，就應該優先標記為 failed**，而不是等兩個都失敗。

---

## 修復方案

### 修改文件
- **檔案**: `src/query_statistics.py`
- **方法**: `QueryStatistics._read_round_scan()`
- **行號**: 約 325-350 行

### 修復邏輯

將判斷順序改為：
1. **優先檢查失敗狀態**：如果有任何一個掃描器明確失敗 (`failed`)，立即標記為 failed
2. **然後檢查成功狀態**：如果至少有一個掃描器成功，使用成功的結果
3. **最後處理未知狀態**：如果兩個都是 unknown（都不存在記錄），標記為 failed

### 修復後的代碼

```python
# 合併結果：取最高漏洞數，並標記來源掃描器
all_functions = set(bandit_data.keys()) | set(semgrep_data.keys()) | set(bandit_status.keys()) | set(semgrep_status.keys())

for func_key in all_functions:
    bandit_vuln = bandit_data.get(func_key, 0)
    semgrep_vuln = semgrep_data.get(func_key, 0)
    b_status = bandit_status.get(func_key, 'unknown')
    s_status = semgrep_status.get(func_key, 'unknown')
    
    # 判斷掃描狀態：
    # 1. 如果有任何一個掃描器明確失敗 (failed)，優先標記為 failed
    # 2. 如果至少有一個掃描器成功，使用成功的結果
    # 3. 如果都是 unknown（兩個都不存在），標記為 failed
    
    if b_status == 'failed' or s_status == 'failed':
        # 至少有一個掃描器明確失敗，標記為 failed
        result[func_key] = (-1, 'failed')
    elif b_status == 'success' or s_status == 'success':
        # 至少有一個掃描器成功
        if bandit_vuln > semgrep_vuln:
            result[func_key] = (bandit_vuln, 'Bandit')
        elif semgrep_vuln > bandit_vuln:
            result[func_key] = (semgrep_vuln, 'Semgrep')
        elif bandit_vuln > 0:  # 相等且 > 0
            result[func_key] = (bandit_vuln, 'Bandit')  # 優先顯示 Bandit
        else:  # 都是 0
            result[func_key] = (0, '')  # 無漏洞，不標記掃描器
    else:
        # 兩個都是 unknown（都不存在記錄）
        result[func_key] = (-1, 'failed')  # 用 -1 表示 failed

return result
```

---

## 測試驗證

### 測試腳本
`test_query_statistics_failed.py`

### 測試案例

| 檔案路徑 | 函式名稱 | 掃描狀態 | 期望結果 | 實際結果 |
|---------|---------|---------|---------|---------|
| browser_use/agent/service.py | replace_url | failed | failed | ✅ failed |
| browser_use/dom/views.py | __hash__、parent_branch_hash | success (0 漏洞) | 0 | ✅ 0 |
| examples/apps/news-use/news_monitor.py | monitor、run_once、save_article | success (0 漏洞) | 0 | ✅ 0 |

### 測試結果
```
✅ 所有測試通過！

修復確認:
  - 掃描失敗時正確顯示 'failed'
  - 掃描成功無漏洞時正確顯示 '0'
```

---

## 影響範圍

### 正面影響
1. **狀態顯示準確**：掃描失敗時明確顯示 `failed`，不會誤導為無漏洞（0）
2. **問題診斷容易**：可以快速識別哪些函式的掃描出現問題
3. **數據完整性**：區分「掃描成功但無漏洞」和「掃描失敗無結果」

### 相容性
- ✅ **向後相容**：修復不影響現有的成功掃描記錄
- ✅ **AS模式**：支援所有輪次的掃描失敗顯示
- ✅ **非AS模式**：同樣支援
- ✅ **批次模式**：舊版的 `generate_statistics()` 方法也會受益

---

## query_statistics.csv 欄位值說明

| 值 | 意義 | 範例 |
|----|------|------|
| **數字** | 發現漏洞的數量 | `3` |
| **數字 (掃描器)** | 發現漏洞的數量及來源 | `2 (Bandit)` |
| **0** | 掃描成功但無漏洞 | `0` |
| **failed** | 掃描失敗（語法錯誤、超時等） | `failed` |
| **#** | 已在前幾輪發現漏洞，跳過此輪 | `#` |
| **All-Safe** | 所有輪次都掃描完成且無漏洞 | `All-Safe` |
| **空白** | 尚未執行該輪的掃描 | ` ` |

---

## 修復前後對比

### 修復前（錯誤）
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,0,,,,
```
→ 語法錯誤導致掃描失敗，但顯示為 0（誤導）

### 修復後（正確）
```csv
檔案路徑,函式名稱,round1,round2,round3,round4,QueryTimes
browser_use/agent/service.py,replace_url,failed,,,,
```
→ 正確顯示 failed，可以立即識別掃描問題

---

## 相關文件

- `src/query_statistics.py`: Query 統計生成器（核心修復）
- `src/cwe_scan_manager.py`: CWE 掃描管理器（產生掃描狀態）
- `src/cwe_detector.py`: CWE 檢測器（執行掃描並標記狀態）

---

## 後續建議

1. **重新生成舊專案的統計**：
   ```python
   from src.query_statistics import QueryStatistics
   
   generator = QueryStatistics(project_name, cwe_type, total_rounds, function_list)
   generator.initialize_csv()
   for round_num in range(1, total_rounds + 1):
       generator.update_round_result(round_num)
   ```

2. **監控掃描失敗率**：可以統計有多少函式顯示 `failed`，分析常見失敗原因

3. **改善錯誤處理**：對於常見的失敗原因（如語法錯誤），可以在掃描前預檢查

---

## 修復摘要

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| 掃描失敗顯示 | 0（誤導） | failed（正確） |
| 判斷邏輯 | 成功優先 | **失敗優先** |
| 狀態區分 | 不清楚 | 明確區分成功/失敗 |
| 問題診斷 | 困難 | 容易 |

✅ **修復完成，測試通過**
