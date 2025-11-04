# 非 AS 模式 CSV 格式與掃描範圍修改文檔

## 變更時間
**2025-11-04**

## 變更目的
在非 Artificial Suicide (AS) 模式下，為了與 Coding Instruction 模板處理邏輯保持一致：
1. **CSV 欄位簡化**：非 AS 模式不需要追蹤函式名稱變更，因此 CSV 不需要「修改前函式名稱」、「修改後函式名稱」兩欄
2. **掃描範圍統一**：所有模式（AS 和非 AS）都統一只掃描每行 prompt 的第一個函式

**重要發現**：經過代碼審查，AS 模式在 `artificial_suicide_mode.py` (line 756) 已經將 prompt 構造為單一函式：
```python
single_function_prompt = f"{target_file}|{target_function_name}"
```
因此 AS 模式實際上也是只處理第一個函式，與非 AS 模式行為一致。

## 變更內容

### 1. CSV 欄位變更 (`cwe_scan_manager.py::_save_function_level_csv()`)

#### AS 模式（有 `function_name_tracker`）
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,crypto.py,vulnerable_encrypt,secure_encrypt_v2,2,45,bandit,HIGH,MEDIUM,Use of weak crypto,success,
```

**原因**：AS 模式會在 Query 階段要求 Copilot 修改函式名稱，需要記錄「修改前」和「修改後」的名稱以追蹤函式演變。

#### 非 AS 模式（無 `function_name_tracker`）
```csv
輪數,行號,檔案路徑,函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,crypto.py,vulnerable_encrypt,2,45,bandit,HIGH,MEDIUM,Use of weak crypto,success,
```

**原因**：非 AS 模式不會要求 Copilot 修改函式名稱，函式名稱在整個執行過程中保持不變，只需要單一「函式名稱」欄位。

### 2. 掃描範圍統一 (`cwe_scan_manager.py::extract_function_targets_from_prompt()`)

#### 重要發現
經過代碼審查發現，**AS 模式和非 AS 模式都只處理第一個函式**：

- **AS 模式**：在 `artificial_suicide_mode.py` (line 203-206) 解析 prompt 時就只取第一個函式：
  ```python
  def _parse_prompt_line(self, line: str):
      # 取第一個函數
      first_function = functions[0].strip()
      return (filepath, first_function)
  ```
  然後在呼叫 CWE 掃描時構造單一函式 prompt (line 756)：
  ```python
  single_function_prompt = f"{target_file}|{target_function_name}"
  ```

- **非 AS 模式**：使用 Coding Instruction 模板時，`_parse_and_extract_first_function()` 也只取第一個函式

因此，`extract_function_targets_from_prompt()` 統一只提取第一個函式是正確的行為。

#### 變更邏輯
```python
def extract_function_targets_from_prompt(self, prompt_content: str) -> List[FunctionTarget]:
    """
    從 prompt 內容中提取函式目標（檔案+函式名稱），格式為每行: {檔案}|{函式}
    
    注意：
    - AS 模式會在呼叫此函式前，已經將 prompt 構造為單一函式（artificial_suicide_mode.py line 756）
    - 非 AS 模式使用 Coding Instruction 模板時，也會只處理第一個函式
    - 因此此函式統一只提取每行的第一個函式
    """
    # ... 解析邏輯 ...
    
    # 統一只取第一個函式
    if func_names:
        func_names = [func_names[0]]
```

#### 行為示例

**輸入 prompt.txt**：
```
crypto.py|func1()、func2()、func3()
auth.py|login()、logout()
```

**AS 模式行為**：
- `artificial_suicide_mode.py` 解析：第 1 行取 `func1()`，第 2 行取 `login()`
- 構造 prompt：`crypto.py|func1()` 和 `auth.py|login()`
- CWE 掃描：只掃描 `func1()` 和 `login()`

**非 AS 模式行為**：
- Coding Instruction 解析：第 1 行取 `func1()`，第 2 行取 `login()`
- CWE 掃描：只掃描 `func1()` 和 `login()`

**結論**：兩種模式行為完全一致，都只處理第一個函式。

### 3. 模式檢測方式

系統透過 `function_name_tracker` 的存在與否來判斷執行模式：

```python
# 在 cwe_scan_manager.py 中
if self.function_name_tracker:
    # AS 模式邏輯
    # - 使用「修改前/後函式名稱」兩欄
    # - 提取並掃描所有函式
else:
    # 非 AS 模式邏輯
    # - 使用單一「函式名稱」欄
    # - 只提取並掃描第一個函式
```

**AS 模式設定流程**：
1. `artificial_suicide_mode.py` 建立 `FunctionNameTracker`
2. 執行 `execute()` 時將 tracker 設定到 `cwe_scan_manager`：
   ```python
   if self.cwe_scan_manager:
       self.cwe_scan_manager.function_name_tracker = self.function_name_tracker
   ```

**非 AS 模式**：
- `copilot_handler.py` 初始化 `CWEScanManager` 時不傳入 tracker
- `function_name_tracker` 保持為 `None`

## 實作細節

### 修改的檔案與函式

#### `src/cwe_scan_manager.py`

1. **`_save_function_level_csv()` (line 170-350)**
   - 修改標題列：根據 `self.function_name_tracker` 是否存在，寫入不同的欄位
   - 修改名稱查詢邏輯：新增 `function_name` 變數用於非 AS 模式
   - 修改資料列寫入：在三個寫入點（failed, vulns, success）分別處理 AS 和非 AS 模式

2. **`extract_function_targets_from_prompt()` (line 88-120)**
   - 新增非 AS 模式檢查：`if not self.function_name_tracker`
   - 限制函式列表為第一個元素：`func_names = [func_names[0]]`
   - 更新日誌訊息：標註模式資訊

### 關鍵程式碼片段

#### CSV 標題列
```python
# 寫入標題（僅在需要時）
if write_header:
    # AS 模式：使用「修改前/後函式名稱」兩欄
    # 非 AS 模式：使用單一「函式名稱」欄
    if self.function_name_tracker:
        writer.writerow([
            '輪數', '行號', '檔案路徑',
            '修改前函式名稱', '修改後函式名稱',
            '漏洞數量', '漏洞行號', '掃描器',
            '信心度', '嚴重性', '問題描述',
            '掃描狀態', '失敗原因'
        ])
    else:
        writer.writerow([
            '輪數', '行號', '檔案路徑',
            '函式名稱',
            '漏洞數量', '漏洞行號', '掃描器',
            '信心度', '嚴重性', '問題描述',
            '掃描狀態', '失敗原因'
        ])
```

#### 函式名稱處理
```python
# 為每個目標函式寫一列
for target in function_targets:
    for func_name in target.function_names:
        # 查詢修改前和修改後的函式名稱（僅在 AS 模式下）
        function_name = func_name  # 預設使用原始名稱（非 AS 模式）
        before_name = func_name    # AS 模式使用
        after_name = func_name     # AS 模式使用
        
        if self.function_name_tracker:
            # AS 模式：查詢修改前/後名稱
            try:
                before_name, _ = self.function_name_tracker.get_function_name_for_round(
                    target.file_path, func_name, round_number
                )
                # ... 查詢 after_name ...
            except Exception as e:
                self.logger.warning(f"⚠️  查詢函式名稱失敗: {e}，使用原始名稱")
```

#### 資料列寫入（以 success 為例）
```python
else:
    # 沒有漏洞但掃描成功：記錄安全狀態
    if self.function_name_tracker:
        writer.writerow([
            round_number, line_number, target.file_path,
            before_name, after_name,  # AS 模式：兩個名稱欄位
            0, '', scanner_filter or '',
            '', '', '', 'success', ''
        ])
    else:
        writer.writerow([
            round_number, line_number, target.file_path,
            function_name,  # 非 AS 模式：單一名稱欄位
            0, '', scanner_filter or '',
            '', '', '', 'success', ''
        ])
```

## 與 Coding Instruction 功能的一致性

### Coding Instruction 模板處理
在 `copilot_handler.py::_parse_and_extract_first_function()` 中：
```python
def _parse_and_extract_first_function(self, prompt_line: str) -> tuple:
    """
    解析 prompt 行並提取第一個函式
    
    格式: filepath|function1()、function2()
    返回: (filepath, function1())  # 只取第一個
    """
    # ... 解析邏輯 ...
    functions = re.split(r'[、,，\s]+', functions_str)
    first_function = functions[0] if functions else None
    return filepath, first_function
```

### CWE 掃描處理
在 `cwe_scan_manager.py::extract_function_targets_from_prompt()` 中：
```python
def extract_function_targets_from_prompt(self, prompt_content: str) -> List[FunctionTarget]:
    # ... 解析邏輯 ...
    func_names = re.split(r'[、,，\s]+', func_name)
    func_names = [fn for fn in func_names if fn]
    
    # 非 AS 模式：只取第一個函式（與 Coding Instruction 模板處理邏輯一致）
    if not self.function_name_tracker and func_names:
        func_names = [func_names[0]]
```

#### 函式提取範圍
```python
def extract_function_targets_from_prompt(self, prompt_content: str) -> List[FunctionTarget]:
    # ... 解析邏輯 ...
    func_names = re.split(r'[、,，\s]+', func_name)
    func_names = [fn for fn in func_names if fn]
    
    # 統一只取第一個函式
    # - AS 模式：artificial_suicide_mode.py 已經只傳入單一函式 (line 756)
    # - 非 AS 模式：與 Coding Instruction 模板處理邏輯一致
    if func_names:
        func_names = [func_names[0]]
```

**保持一致性的原因**：
- **AS 模式**：`artificial_suicide_mode.py::_parse_prompt_line()` (line 203) 已經只取第一個函式
- **非 AS 模式 + Coding Instruction**：`copilot_handler.py::_parse_and_extract_first_function()` 也只取第一個函式
- **統一行為**：所有模式都只處理第一個函式，確保 Copilot 分析範圍與 CWE 掃描範圍完全一致

## 測試驗證

### 測試腳本
`tests/test_csv_format_changes.py`

### 測試項目
1. **AS 模式 CSV 欄位測試**
   - ✅ 驗證標題列包含「修改前函式名稱」、「修改後函式名稱」
   - ✅ 驗證不包含單一「函式名稱」欄位
   - ✅ 驗證資料列正確填入兩個名稱欄位

2. **非 AS 模式 CSV 欄位測試**
   - ✅ 驗證標題列包含單一「函式名稱」
   - ✅ 驗證不包含「修改前/後函式名稱」欄位
   - ✅ 驗證資料列正確填入名稱欄位

3. **函式提取範圍測試**
   - ✅ 統一只提取第一個函式（AS 和非 AS 模式相同）
   - ✅ AS 模式實際傳入時已經是單一函式
   - ✅ 保護機制：即使傳入多個函式也只取第一個

### 測試執行結果
```bash
$ python tests/test_csv_format_changes.py

測試 1: AS 模式（有 function_name_tracker）- 應有「修改前/後函式名稱」兩欄
✅ CSV 欄位: ['輪數', '行號', '檔案路徑', '修改前函式名稱', '修改後函式名稱', ...]
✅ AS 模式欄位驗證通過

測試 2: 非 AS 模式（無 function_name_tracker）- 應只有「函式名稱」一欄
✅ CSV 欄位: ['輪數', '行號', '檔案路徑', '函式名稱', ...]
✅ 非 AS 模式欄位驗證通過

測試 3: 統一只提取每行的第一個函式（AS 和非 AS 模式相同）
[非 AS 模式]
提取結果: test1.py: ['func1()'], test2.py: ['funcA()']
✅ 非 AS 模式：正確只提取第一個函式

[AS 模式]
注意：AS 模式在 artificial_suicide_mode.py 中會構造單一函式 prompt
提取結果: test1.py: ['func1()'], test2.py: ['funcA()']
✅ AS 模式：正確處理單一函式輸入

[保護機制測試]
✅ 保護機制：正確限制為第一個函式

✅ 所有測試通過！

總結:
1. ✅ AS 模式使用「修改前函式名稱」、「修改後函式名稱」兩欄
2. ✅ 非 AS 模式使用單一「函式名稱」欄
3. ✅ AS 和非 AS 模式都統一只提取並掃描每行的第一個函式
4. ✅ AS 模式在呼叫掃描前已經構造為單一函式 prompt
```

## 相關文檔
- `CODING_INSTRUCTION_FEATURE.md`: Coding Instruction 模板功能完整說明
- `CODING_INSTRUCTION_IMPLEMENTATION_SUMMARY.md`: 實作總結
- `RESPONSE_CHAINING_LABEL_FIX.md`: 回應串接標籤修正（與 Coding Instruction 相關）

## 使用情境

### 情境 1: 非 AS 模式 + Coding Instruction 模板
```
使用者設定：
- 提示詞來源：使用專案提示詞
- Coding Instruction Template：✓ 勾選
- Artificial Suicide 模式：✗ 未勾選

prompt.txt 內容：
crypto.py|encrypt()、decrypt()、hash_password()
auth.py|login()、logout()

執行結果：
- 第 1 輪第 1 行：
  * 套用模板處理：只處理 encrypt()
  * CWE 掃描：只掃描 encrypt()
  * CSV 記錄：輪數=1, 行號=1, 檔案路徑=crypto.py, 函式名稱=encrypt()
  
- 第 1 輪第 2 行：
  * 套用模板處理：只處理 login()
  * CWE 掃描：只掃描 login()
  * CSV 記錄：輪數=1, 行號=2, 檔案路徑=auth.py, 函式名稱=login()
```

### 情境 2: AS 模式
```
使用者設定：
- Artificial Suicide 模式：✓ 勾選
- 攻擊輪數：2

prompt.txt 內容：
crypto.py|encrypt()、decrypt()

執行結果：
- 第 1 輪第 1 行 Phase 1 (Query)：
  * `_parse_prompt_line()` 解析：只取 encrypt()
  * AI 修改函式名稱：encrypt() → secure_encrypt_v2()
  * FunctionNameTracker 記錄：(crypto.py, encrypt) → round 1 → secure_encrypt_v2
  * 構造 prompt：`crypto.py|encrypt()`（只包含第一個函式）
  * CWE 掃描：只掃描 encrypt()
  * CSV 記錄：
    - 輪數=1, 行號=1, 檔案=crypto.py, 修改前=encrypt, 修改後=secure_encrypt_v2

- 第 2 輪第 1 行 Phase 1 (Query)：
  * AI 再次修改：secure_encrypt_v2() → ultra_secure_encrypt()
  * FunctionNameTracker 記錄：round 2 → ultra_secure_encrypt
  * CWE 掃描：掃描 secure_encrypt_v2()（使用第 2 輪的名稱）
  * CSV 記錄：
    - 輪數=2, 行號=1, 修改前=secure_encrypt_v2, 修改後=ultra_secure_encrypt
```

**重要**：AS 模式的 prompt.txt 中即使寫了多個函式（例如 `encrypt()、decrypt()`），也只會處理第一個。

## 向後相容性
- **不影響現有 AS 模式**：AS 模式的 CSV 格式和掃描行為完全不變
- **只影響非 AS 模式**：非 AS 模式的 CSV 格式簡化，掃描範圍縮小（但這正是預期行為）

## 注意事項

1. **模式檢測依據**
   - 判斷依據：`self.function_name_tracker is not None`
   - AS 模式會主動設定 tracker，非 AS 模式保持 `None`

2. **CSV 欄位數量差異**
   - AS 模式：13 個欄位
   - 非 AS 模式：12 個欄位（少了一個名稱欄位）
   - 讀取 CSV 時需注意欄位數量

3. **函式名稱一致性**
   - 非 AS 模式：CSV 中的「函式名稱」= prompt.txt 中的第一個函式
   - AS 模式：CSV 中的「修改前函式名稱」= prompt.txt 中的原始名稱，「修改後函式名稱」= AI 修改後的名稱

4. **多函式處理**
   - **重要**：AS 和非 AS 模式都只處理第一個函式
   - 如果需要處理多個函式，應該在 prompt.txt 中分多行寫
   - 例如：
     ```
     # ✓ 正確（會處理兩個函式）
     crypto.py|encrypt()
     crypto.py|decrypt()
     
     # ✗ 錯誤（只會處理第一個函式 encrypt()）
     crypto.py|encrypt()、decrypt()
     ```

## 總結
此次修改確保了：
1. **CSV 格式差異化**：AS 模式追蹤函式名稱變更（兩欄），非 AS 模式不需要（一欄）
2. **掃描範圍統一**：所有模式都只處理第一個函式，確保與 Copilot 分析範圍一致
3. **代碼一致性**：`extract_function_targets_from_prompt()` 統一只提取第一個函式，適用於所有模式
4. **向後相容**：AS 模式原本就是只處理第一個函式，此修改不影響現有行為
