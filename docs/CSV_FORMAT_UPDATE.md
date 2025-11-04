# CSV 格式更新總結

## 修改日期
2025-10-31

## 修改目的
將 CSV 統計文件中的檔案路徑和函數名稱分離成兩個獨立欄位，並簡化掃描結果（移除函式起始/結束行），因為每個檔案只改動一個函數。

## 主要修改

### 1. `src/query_statistics.py`

#### 新增方法
- **`_split_function_key(function_key)`**: 將 `filepath_function()` 格式分離成 `(filepath, function_name)`
  - 使用 `.py_` 作為分隔標記（因為檔案路徑一定以 `.py` 結尾）
  - 向後兼容：如果找不到 `.py_`，則使用最後一個底線分割

#### 修改的方法
- **`initialize_csv()`**: 
  - 表頭從 `['file_function\Round n', ...]` 改為 `['檔案路徑', '函式名稱', ...]`
  - 每行數據分為檔案路徑和函數名稱兩個欄位

- **`_read_current_csv()`**:
  - 讀取分離的 `檔案路徑` 和 `函式名稱` 欄位
  - 組合成 `filepath::function_name` 格式的內部 key

- **`_write_updated_csv()`**:
  - 將內部 key 拆分回檔案路徑和函數名稱
  - 寫入時使用兩個獨立欄位

- **`_write_csv_batch()`**:
  - 批次模式也更新為新格式

- **`should_skip_function(function_key)`**:
  - 接受 `filepath_function()` 格式
  - 內部轉換為 `filepath::function_name` 進行查找

- **`_read_round_scan(round_num)`**:
  - 讀取掃描結果 CSV 時，分別讀取 `檔案路徑` 和 `函式名稱` 欄位
  - 組合成 `filepath_function_name` 格式進行匹配

- **`_find_original_key(function_key, round_data)`**:
  - 從 `filepath::function_name` 格式找到原始掃描結果的 key

### 2. `src/cwe_scan_manager.py`

#### 修改的方法
- **`_save_function_level_scan_results()`**:
  - **表頭更新**: 從 `['輪數', '行號', '檔案名稱_函式名稱', '函式起始行', '函式結束行', ...]` 
    改為 `['輪數', '行號', '檔案路徑', '當前函式名稱', '漏洞數量', ...]`
  - **移除欄位**: `函式起始行` 和 `函式結束行`
  - **數據寫入**: 使用 `target.file_path` 和 `func_name` 分開寫入
  - **移除變數**: 不再追踪 `func_start` 和 `func_end`

### 3. `src/artificial_suicide_mode.py`

#### 維持不變
- `_parse_prompt_line()` 方法已經正確解析檔案路徑和函數名稱
- 初始化統計時使用 `f"{filepath}_{first_function}"` 格式
- 這個格式與 `QueryStatistics._split_function_key()` 完全兼容

## 新的 CSV 格式

### query_statistics.csv
```csv
檔案路徑,函式名稱,round1,round2,round3,QueryTimes
airflow-core/src/airflow/api_fastapi/auth/tokens.py,avalidated_claims,2 (Bandit),,#,1
airflow-core/src/airflow/lineage/hook.py,_generate_key,0,1 (Bandit),#,2
```

### function_level_scan.csv (Bandit/Semgrep)
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,airflow-core/src/airflow/api_fastapi/auth/tokens.py,avalidated_claims,2,"45,67",bandit,HIGH,MEDIUM,Use of weak cryptographic key,success,
```

## 優點

1. **更清晰的數據結構**: 檔案路徑和函數名稱分開，易於閱讀和處理
2. **簡化掃描邏輯**: 不再需要追踪函式起始/結束行（因為每個檔案只改一個函數）
3. **更好的兼容性**: 支持函數名稱中包含底線的情況
4. **向後兼容**: 保留了舊格式的解析邏輯作為備用

## 測試結果

- ✅ CSV 格式正確分離檔案路徑和函數名稱
- ✅ 統計功能正常運作
- ✅ 無語法錯誤
- ✅ 函數名稱中包含底線的情況處理正確（如 `_generate_key`, `_decode_and_validate_azure_jwt`）

## 向後兼容性

- 如果遇到無法用 `.py_` 分割的 key，會退回到使用最後一個底線分割
- 舊的掃描結果文件無法直接使用，需要重新掃描
