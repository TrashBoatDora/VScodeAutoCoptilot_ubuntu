# CWE 掃描 Prompt 匹配修復文檔

## 問題描述

### 發現時間
2025-10-31

### 問題現象
在 Artificial Suicide 模式執行時，`OriginalScanResult` 目錄中出現**同一檔案的多個函數報告**，即使該輪次只處理了其中一個函數。

### 問題根源

#### 1. Prompt 格式
`prompt.txt` 的格式允許一行包含多個函數：
```
filepath|function1()、function2()、function3()
```

例如實際案例：
```
aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()
aider/models.py|send_completion()
```

#### 2. 處理邏輯不一致
- **Phase 1 & Phase 2 發送 prompt**：只處理**第一個函數**（通過 `_parse_prompt_line()` 只提取第一個函數）
- **Phase 2 CWE 掃描**：卻傳入了**整行 prompt**（包含所有函數）

#### 3. 程式碼位置
`src/artificial_suicide_mode.py` 的 `_execute_phase2()` 方法：

```python
# ❌ 錯誤的做法（修復前）
scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
    project_path=self.project_path,
    project_name=self.project_path.name,
    prompt_content=line.strip(),  # ❌ 使用原始 prompt 行（包含所有函數）
    cwe_type=self.target_cwe,
    round_number=round_num,
    line_number=line_idx
)
```

#### 4. 結果影響
對於 prompt 行：`aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()`

**實際處理**：
- Phase 1 Query：只請 AI 修改 `show_send_output()`
- Phase 2 Coding：只請 AI 補 `show_send_output()` 的漏洞代碼

**但掃描結果**：
- 生成了 `show_send_output()_report.json` ✅
- **多生成了** `check_for_file_mentions()_report.json` ❌（不應該掃描）

## 解決方案

### 修復原則
**掃描邏輯應該匹配發送 prompt 的邏輯**：只掃描實際處理的函數（第一個函數）。

### 程式碼修改

**檔案**：`src/artificial_suicide_mode.py`  
**方法**：`_execute_phase2()`  
**位置**：CWE 掃描部分

```python
# ✅ 正確的做法（修復後）
# 構造只包含當前處理函數的 prompt（匹配實際發送的 prompt）
# 格式: filepath|function_name (只取第一個函數)
single_function_prompt = f"{target_file}|{target_function_name}"

# 呼叫函式級別掃描（會自動追加到 CSV）
scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
    project_path=self.project_path,
    project_name=self.project_path.name,
    prompt_content=single_function_prompt,  # ✅ 只掃描實際處理的函數
    cwe_type=self.target_cwe,
    round_number=round_num,
    line_number=line_idx
)
```

### 關鍵變化

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| 傳入參數 | `line.strip()` (整行) | `f"{target_file}\|{target_function_name}"` (單函數) |
| 掃描函數數量 | 該檔案的所有函數 | 只掃描當前處理的函數 |
| 報告生成 | 多個（不符合實際處理） | 單個（符合實際處理） |

## 驗證方式

### 測試案例
使用包含多函數的 prompt.txt：
```
aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()
aider/models.py|send_completion()
```

### 預期結果（修復後）

#### 第1輪 OriginalScanResult 結構
```
OriginalScanResult/Bandit/CWE-327/{project}/第1輪/
  ├── coders__base_coder.py__show_send_output()_report.json  ✅ 只有第一個函數
  └── aider__models.py__send_completion()_report.json        ✅ 只有第一個函數
```

**不應該出現**：
- ❌ `coders__base_coder.py__check_for_file_mentions()_report.json`

#### CSV 掃描結果
每行 prompt 只應該有**1筆記錄**（對應第一個函數）：

```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output(),2,...
1,2,aider/models.py,send_completion(),1,...
```

### 修復前的錯誤結果
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output(),2,...
1,1,aider/coders/base_coder.py,check_for_file_mentions(),0,...  ❌ 不應該掃描
1,2,aider/models.py,send_completion(),1,...
```

## 相關模組

### 受影響的模組
1. **artificial_suicide_mode.py**：修復位置
   - `_execute_phase2()` 方法中的掃描呼叫

2. **cwe_scan_manager.py**：掃描執行者
   - `scan_from_prompt_function_level()` 方法解析 prompt
   - `extract_function_targets_from_prompt()` 提取函數列表

3. **cwe_detector.py**：實際掃描器
   - `scan_single_file()` 生成原始報告檔案

### 邏輯流程（修復後）

```
Phase 2 處理第 N 行
  ├─ 1. 解析 prompt：取第一個函數
  │    input: "filepath|func1()、func2()"
  │    output: filepath="...", target_function_name="func1()"
  │
  ├─ 2. 發送 coding prompt：只針對 func1()
  │    template: "請為 {target_function_name} 補充漏洞代碼"
  │
  ├─ 3. 收到回應並儲存
  │
  └─ 4. CWE 掃描：只掃描 func1() ✅
       input: "filepath|func1()"  (不包含 func2)
       output: 只生成 filepath__func1()_report.json
```

## 測試建議

### 單元測試（建議新增）
測試 `_parse_prompt_line()` 和掃描呼叫的一致性：

```python
def test_scan_matches_prompt_processing():
    """測試掃描的函數應該與實際處理的函數一致"""
    prompt_line = "test.py|func1()、func2()、func3()"
    
    # 解析 prompt（只取第一個）
    filepath, func_name = as_mode._parse_prompt_line(prompt_line)
    assert func_name == "func1()"
    
    # 構造掃描 prompt（應該只包含第一個函數）
    scan_prompt = f"{filepath}|{func_name}"
    assert scan_prompt == "test.py|func1()"
    assert "func2" not in scan_prompt
    assert "func3" not in scan_prompt
```

### 整合測試
執行完整的 Artificial Suicide 流程，檢查：
1. `OriginalScanResult` 中每行只有1個報告檔案
2. CSV 中每行只有1筆掃描記錄
3. 函數名稱與 ExecutionResult 中儲存的回應一致

## 注意事項

### 未來開發建議
如果需要支援**一行處理多個函數**，應該：
1. 修改 `_execute_phase1()` 和 `_execute_phase2()` 的循環邏輯
2. 對每個函數分別發送 prompt 和掃描
3. 更新 `FunctionName_query` 追蹤邏輯以支援一行多函數

### 目前設計限制
- 一行 prompt 只處理第一個函數
- 其他函數會被忽略（不發送 prompt、不掃描）
- 如果需要處理所有函數，應該拆成多行：
  ```
  filepath|func1()
  filepath|func2()
  filepath|func3()
  ```

## 修復日期
2025-10-31

## 相關文檔
- `docs/FUNCTION_NAME_TRACKING.md`：函數名稱追蹤功能
- `docs/CSV_FORMAT_UPDATE.md`：CSV 格式說明
- `.github/copilot-instructions.md`：專案架構說明
