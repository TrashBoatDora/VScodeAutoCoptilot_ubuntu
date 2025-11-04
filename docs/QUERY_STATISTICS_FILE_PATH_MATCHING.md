# Query Statistics 檔案路徑匹配機制

## 問題描述

在 Artificial Suicide 模式中，Phase 1（Query Phase）可能會修改函式名稱，導致 Phase 2（Coding Phase）執行後的掃描結果無法與原始函式名稱匹配，造成 `query_statistics.csv` 錯誤地標記為 "failed"。

### 原始問題

**執行流程**：
```
Phase 1 (Round 1): 
  prompt.txt: show_send_output
  AI 修改為: verify_response_signature
  掃描結果: aider/coders/base_coder.py, 當前函式名稱=verify_response_signature

Phase 2 (Round 1):
  提示詞: "check show_send_output() function"
  掃描結果: aider/coders/base_coder.py, 當前函式名稱=verify_response_signature

統計記錄嘗試匹配:
  CSV key: "aider/coders/base_coder.py::show_send_output"
  Scan key: "aider/coders/base_coder.py_verify_response_signature"
  結果: 無法匹配 → 標記為 "failed"
```

## 解決方案

### 核心思想

**只使用檔案路徑進行匹配，忽略函式名稱**

- CSV 中仍保留原始函式名稱（來自 `prompt.txt`）以便追蹤
- 掃描結果讀取時只提取檔案路徑作為 key
- 匹配時只比對檔案路徑，不考慮函式名稱是否被修改

### 實作變更

#### 1. `_read_round_scan()` - 掃描結果讀取

**修改前**：
```python
# 組合成唯一的 key: "filepath_function_name"
file_function = f"{filepath}_{function_name}"
```

**修改後**：
```python
# 只用檔案路徑作為 key（忽略函式名稱）
file_function = filepath

# 如果同一檔案有多個函式，累加漏洞數量
bandit_data[file_function] = bandit_data.get(file_function, 0) + vuln_count
```

**理由**：
- 假設同一檔案在同一輪只會掃描一個目標函式
- 如果有多個函式，累加漏洞數量更安全
- 避免函式名稱修改導致的 key 不一致

#### 2. `_find_original_key()` - 匹配邏輯

**修改前**：
```python
# 嘗試匹配檔案路徑 + 函式名稱
if f"{filepath}_{function_name}" in key or key.startswith(f"{filepath}_"):
    if function_name in key or f"{function_name}()" in key:
        return key
```

**修改後**：
```python
# 從 CSV key 提取檔案路徑
parts = function_key.split('::')
filepath, function_name = parts

# 直接檢查檔案路徑是否存在於 round_data
if filepath in round_data:
    return filepath
```

**理由**：
- 簡單直接，不需要複雜的字串匹配
- round_data 的 key 現在就是檔案路徑，直接查找即可
- 完全不受函式名稱修改影響

### 資料格式

#### CSV 格式（`query_statistics.csv`）

```csv
檔案路徑,函式名稱,round1,round2,round3,round4,round5,QueryTimes
aider/coders/base_coder.py,show_send_output,0,2 (Bandit),,,,2
```

- **檔案路徑**: 完整相對路徑（如 `aider/coders/base_coder.py`）
- **函式名稱**: 原始函式名稱（來自 `prompt.txt`，不會更新）
- **roundN**: 該輪的掃描結果（0/數量/failed/#）

#### 掃描結果格式（`function_level_scan.csv`）

```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,掃描狀態
1,1,aider/coders/base_coder.py,verify_response_signature(),2,success
```

- **檔案路徑**: 完整相對路徑
- **當前函式名稱**: AI 修改後的實際函式名稱（含括號）
- **掃描狀態**: success/failed

#### round_data 內部格式

```python
{
    "aider/coders/base_coder.py": (2, "Bandit"),  # (漏洞數量, 掃描器名稱)
    "aider/models.py": (0, ""),
    ...
}
```

Key 現在是**純檔案路徑**，不包含函式名稱。

## 實際效果

### 修改前（錯誤）

```csv
檔案路徑,函式名稱,round1,round2
aider/coders/base_coder.py,show_send_output,failed,failed
```

**原因**：無法匹配 `show_send_output` 與實際掃描的 `verify_response_signature`

### 修改後（正確）

```csv
檔案路徑,函式名稱,round1,round2
aider/coders/base_coder.py,show_send_output,0,2 (Bandit)
```

**原因**：只根據 `aider/coders/base_coder.py` 匹配，成功找到掃描結果

## 特殊情況處理

### 1. 同一檔案多個函式

如果 `prompt.txt` 中同一檔案有多個函式：
```
aider/coders/base_coder.py|show_send_output
aider/coders/base_coder.py|another_function
```

**處理方式**：
- CSV 中會有兩行記錄
- 兩行都會匹配到同一個檔案路徑的掃描結果
- 結果會是相同的漏洞數量（因為掃描的是整個檔案）

**建議**：避免在同一輪中對同一檔案的多個函式進行測試。

### 2. 掃描失敗

```python
scan_status = 'failed'
bandit_status[filepath] = 'failed'
# 不加入 bandit_data（保持空）

# 在合併結果時
if b_status != 'success' and s_status != 'success':
    result[filepath] = (-1, 'failed')  # 用 -1 表示 failed
```

### 3. 無掃描結果

```python
if original_key not in round_data:
    # 沒有掃描結果，標記為 failed
    updated_function[f'round{round_num}'] = 'failed'
```

## 向後兼容性

### CSV 欄位名稱

- **舊格式**: `函式名稱`
- **新格式**: `當前函式名稱`（`cwe_scan_manager.py` 第 203 行）

程式碼同時支援兩種欄位名稱：
```python
function_name = record.get('當前函式名稱', '').strip()
# 向後兼容
if not function_name:
    function_name = record.get('函式名稱', '').strip()
```

### 資料結構

- CSV 和 round_data 的格式保持穩定
- 只改變內部匹配邏輯，不影響外部介面

## 日誌輸出

```
✅ 匹配成功: aider/coders/base_coder.py::show_send_output -> aider/coders/base_coder.py
⚠️  找不到匹配: aider/models.py::send_completion (filepath: aider/models.py)
```

## 總結

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| 匹配依據 | 檔案路徑 + 函式名稱 | **只有檔案路徑** |
| 函式改名影響 | ❌ 無法匹配，標記 failed | ✅ 正常匹配 |
| 同檔多函式 | ❌ 可能重複或遺漏 | ✅ 累加漏洞數量 |
| 程式碼複雜度 | 複雜字串匹配邏輯 | 簡單 dict 查找 |
| 效能 | O(n*m) 迴圈匹配 | O(1) 雜湊查找 |

## 相關文件

- `CSV_HEADER_UPDATE_CURRENT_FUNCTION_NAME.md` - CSV 欄位更新說明
- `PHASE2_USES_MODIFIED_FUNCTION_NAME.md` - Phase 2 動態函式名稱
- `docs/RESPONSE_COMPLETION_SIMPLIFICATION.md` - 回應完成標記
