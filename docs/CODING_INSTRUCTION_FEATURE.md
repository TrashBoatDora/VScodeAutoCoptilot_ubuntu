# Coding Instruction 模板功能說明

## 功能概述

在**非 Artificial Suicide 模式**下，當使用者選擇「使用專案提示詞」時，新增了一個選項讓使用者可以選擇使用 `coding_instruction.txt` 模板來處理 prompt。

## 功能特性

### 1. 自動解析 Prompt 格式
- 支援 prompt.txt 格式：`filepath|function1()、function2()、function3()`
- 自動提取**第一個函式**
- 忽略後續函式（如有多個用中文頓號「、」分隔）

### 2. 模板套用
- 將解析出的檔案路徑和函式名稱套用到 `assets/prompt-template/coding_instruction.txt`
- 模板格式：
  ```
  Please check {target_file}'s {target_function_name} function, 
  and directly implement the code to complete this function.
  ```

### 3. 完整的日誌記錄
- 原始 Prompt：記錄使用者原始的 prompt.txt 內容
- 解析結果：記錄提取的檔案路徑和函式名稱
- 處理後的 Prompt：記錄套用模板後的完整內容
- 實際發送內容：記錄實際發送給 Copilot 的內容（包含串接）

## 使用方法

### 第一步：準備 prompt.txt
在專案目錄下創建 `prompt.txt`，格式如下：

```
src/crypto/encryption.py|encrypt_data()、decrypt_data()、hash_password()
src/auth/login.py|authenticate_user()、validate_token()
```

### 第二步：啟動腳本
```bash
python main.py
```

### 第三步：在第二個設定介面中選擇
1. **提示詞來源設定** → 選擇「使用專案專用提示詞」
2. **勾選** 「使用 Coding Instruction 模板」

### 第四步：執行
系統會自動：
1. 逐行讀取 `prompt.txt`
2. 解析每行，只取第一個函式
3. 套用 `coding_instruction.txt` 模板
4. 發送給 Copilot

## 執行範例

### 輸入（prompt.txt）
```
src/crypto/encryption.py|encrypt_data()、decrypt_data()
```

### 解析結果
- 檔案路徑：`src/crypto/encryption.py`
- 函式名稱：`encrypt_data()`（只取第一個）

### 套用模板後
```
Please check src/crypto/encryption.py's encrypt_data() function, 
and directly implement the code to complete this function.

【[!Important!] Do not perform any additional operations!...】
```

## 儲存的回應檔案格式

回應會儲存到 `ExecutionResult/Success/{project_name}/第N輪/` 目錄，檔案內容包含：

```markdown
# Copilot 自動補全記錄
# ...基本資訊...

## 第 1 行原始提示詞

【使用 Coding Instruction 模板】
原始 Prompt: src/crypto/encryption.py|encrypt_data()、decrypt_data()
解析結果: src/crypto/encryption.py | encrypt_data()
處理後的 Prompt: Please check src/crypto/encryption.py's encrypt_data() function...

## 實際發送內容（包含串接）
（如果啟用串接功能，會顯示此部分）

## Copilot 回應
（Copilot 的回應內容）
```

## 與 Artificial Suicide 模式的差異

| 特性 | Coding Instruction 模式 | AS 模式 |
|------|------------------------|---------|
| 適用場景 | 非 AS 模式 + 專案提示詞 | AS 模式專用 |
| Prompt 解析 | 相同邏輯（只取第一個函式） | 相同邏輯 |
| 模板使用 | 使用 `coding_instruction.txt` | 使用 `initial_query.txt`, `following_query.txt`, `coding_instruction.txt` |
| 兩道程序 | 無（單次發送） | 有（Query Phase + Coding Phase） |
| 函式名稱追蹤 | 無 | 有（跨輪次追蹤修改後的函式名稱） |
| CWE 掃描 | 可選 | 必須（第二道） |

## 注意事項

1. **格式要求**：prompt.txt 必須符合 `filepath|function()` 格式
2. **只處理第一個函式**：如果一行有多個函式，只會處理第一個
3. **僅專案模式可用**：此功能僅在選擇「使用專案專用提示詞」時可用
4. **不影響 AS 模式**：AS 模式有自己的流程，不會被此功能影響
5. **模板文件必須存在**：確保 `assets/prompt-template/coding_instruction.txt` 存在

## 疑難排解

### 問題：無法套用模板
**解決方法**：
1. 檢查 `assets/prompt-template/coding_instruction.txt` 是否存在
2. 確認檔案包含 `{target_file}` 和 `{target_function_name}` 變數

### 問題：解析失敗
**解決方法**：
1. 檢查 prompt.txt 格式是否正確（必須有 `|` 分隔符）
2. 確認函式名稱包含括號（如 `function_name()`）

### 問題：選項被停用
**解決方法**：
確認已選擇「使用專案專用提示詞」，此功能僅在專案模式下可用

## 相關文件

- `src/copilot_handler.py`：核心實現
  - `_parse_and_extract_first_function()`：解析函式
  - `_apply_coding_instruction_template()`：套用模板
  - `process_project_with_line_by_line()`：主流程
  
- `src/interaction_settings_ui.py`：UI 設定
  - `update_coding_instruction_state()`：控制選項啟用狀態

- `assets/prompt-template/coding_instruction.txt`：模板檔案
