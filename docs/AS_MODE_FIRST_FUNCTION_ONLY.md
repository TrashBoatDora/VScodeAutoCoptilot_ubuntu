# AS 模式也只處理第一個函式 - 重要發現

## 發現時間
**2025-11-04** - 在實作非 AS 模式 CSV 格式變更時

## 重要發現
在實作過程中發現，**AS (Artificial Suicide) 模式實際上也只處理每行 prompt 的第一個函式**，與非 AS 模式行為一致。

## 證據

### 1. `artificial_suicide_mode.py::_parse_prompt_line()` (line 200-213)
```python
def _parse_prompt_line(self, line: str):
    """
    解析單行 prompt，格式: filepath|function_name
    支援多個函數名稱（用逗號或頓號分隔），但只取第一個
    """
    parts = line.strip().split('|')
    # ... 解析 filepath ...
    
    # 分割多個函數名稱
    if '、' in functions_part or ',' in functions_part or '，' in functions_part:
        functions = re.split(r'[、,，]+', functions_part)
    else:
        functions = [functions_part]
    
    # 取第一個函數  ← 關鍵：只取第一個
    first_function = functions[0].strip()
    
    # 確保函數名稱包含括號（如果沒有則添加）
    if not first_function.endswith('()'):
        first_function = first_function + '()'
    
    self.logger.debug(f"解析 prompt: {filepath} | {first_function} (共 {len(functions)} 個函數)")
    
    return (filepath, first_function)
```

### 2. CWE 掃描呼叫 (line 754-762)
```python
if self.cwe_scan_manager:
    try:
        # 構造只包含當前處理函數的 prompt（匹配實際發送的 prompt）
        # 格式: filepath|function_name (只取第一個函數)
        single_function_prompt = f"{target_file}|{target_function_name}"
        
        # 呼叫函式級別掃描（會自動追加到 CSV）
        scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
            project_path=self.project_path,
            project_name=self.project_path.name,
            prompt_content=single_function_prompt,  # 只掃描實際處理的函數
            cwe_type=self.target_cwe,
            round_number=round_num,
            line_number=line_idx
        )
```

### 3. Query 統計初始化 (line 237-244)
```python
# 步驟 0.5：初始化 Query 統計 CSV
self.logger.info("📊 初始化 Query 統計...")
# 解析每一行，只取第一個函數
function_list = []
for line in self.prompt_lines:
    filepath, first_function = self._parse_prompt_line(line)  # 只取第一個
    if filepath and first_function:
        function_list.append(f"{filepath}_{first_function}")
```

## 影響

### 原本的錯誤理解
最初實作時認為：
- AS 模式：提取並掃描**所有函式**
- 非 AS 模式：只提取並掃描**第一個函式**

### 實際正確行為
經過代碼審查後發現：
- **AS 模式**：只處理第一個函式（`_parse_prompt_line()` line 203）
- **非 AS 模式**：只處理第一個函式（與 Coding Instruction 一致）
- **統一行為**：所有模式都只處理第一個函式

### 修正的實作
原本在 `extract_function_targets_from_prompt()` 中有條件判斷：
```python
# 錯誤的實作（已修正）
if not self.function_name_tracker and func_names:
    func_names = [func_names[0]]  # 只在非 AS 模式限制
```

修正後統一處理：
```python
# 正確的實作
if func_names:
    func_names = [func_names[0]]  # 所有模式都只取第一個
```

## 為什麼 AS 模式也只處理第一個函式？

### 設計考量
1. **聚焦分析**：AS 模式的目的是測試 Copilot 是否會生成不安全的程式碼，聚焦於單一函式可以更精確地追蹤其演變

2. **函式名稱追蹤**：AS 模式需要追蹤函式在多輪中的名稱變化，處理多個函式會增加複雜度

3. **Prompt 構造**：每一行 prompt 實際上對應一次完整的 Query + Coding 流程，多個函式會造成混淆

4. **實用性考量**：如果要測試多個函式，使用者應該在 prompt.txt 中分多行寫，這樣可以：
   - 獨立追蹤每個函式的攻擊結果
   - 在 Query 統計中清楚記錄每個函式的成功/失敗狀態
   - 支援跳過已攻擊成功的函式

## 使用建議

### Prompt.txt 正確寫法
如果需要測試多個函式，應該分多行寫：

```
✓ 正確（所有模式適用）
crypto.py|encrypt()
crypto.py|decrypt()
crypto.py|hash_password()

✗ 錯誤（只會處理第一個）
crypto.py|encrypt()、decrypt()、hash_password()
```

### AS 模式範例
**prompt.txt**:
```
auth.py|login()、logout()、register()
crypto.py|encrypt()、decrypt()
```

**實際處理**:
- 第 1 行：只處理 `login()`（忽略 `logout()` 和 `register()`）
- 第 2 行：只處理 `encrypt()`（忽略 `decrypt()`）

**建議改寫**:
```
auth.py|login()
auth.py|logout()
auth.py|register()
crypto.py|encrypt()
crypto.py|decrypt()
```

## 測試驗證

### 測試案例
```python
# 測試輸入
prompt_multi_functions = """test1.py|func1()、func2()、func3()
test2.py|funcA(), funcB()"""

# AS 模式結果
targets = extract_function_targets_from_prompt(prompt_multi_functions)
# test1.py: ['func1()']  ← 只取第一個
# test2.py: ['funcA()']  ← 只取第一個

# 保護機制測試
# 即使 prompt 包含多個函式，也只會提取第一個
✅ 測試通過
```

## 相關文檔
- `NON_AS_MODE_CSV_FORMAT_AND_SCAN_SCOPE.md`: 完整技術文檔（已更新）
- `NON_AS_MODE_CSV_QUICK_REF.md`: 快速參考（已更新）
- `NON_AS_MODE_CSV_FORMAT_SUMMARY.md`: 總結報告（已更新）

## 結論
這個發現很重要，因為它：
1. **修正了理解**：AS 模式不是處理所有函式，而是只處理第一個
2. **簡化了實作**：不需要區分 AS 和非 AS 模式的函式提取邏輯
3. **統一了行為**：所有模式都遵循相同的「只處理第一個函式」原則
4. **改進了文檔**：更新了所有相關文檔以反映正確的行為

這也解釋了為什麼 `artificial_suicide_mode.py` 中要構造 `single_function_prompt` - 因為它本來就只處理單一函式！
