# Coding Instruction 功能實現總結

## 📋 需求回顧

在非 Artificial Suicide 模式下，當使用者選擇「使用專案提示詞」時：
1. 不直接發送原始 prompt
2. 解析 prompt.txt 每行（格式：`filepath|function1()、function2()`）
3. 只取出第一個函式
4. 將其塞入 `coding_instruction.txt` 模板中發送

## ✅ 已完成的工作

### 1. 核心功能實現（`src/copilot_handler.py`）

#### 新增的輔助函數

**`_parse_and_extract_first_function(prompt_line: str) -> tuple`**
- 功能：解析 prompt.txt 的單行，提取第一個函式
- 支援格式：`filepath|function1()、function2()、function3()`
- 返回：`(filepath, first_function_name)`
- 特性：
  - 複用 AS 模式的解析邏輯
  - 支援中文頓號「、」分隔多個函式
  - 自動補全括號（如果缺少）
  - 詳細的日誌記錄

**`_apply_coding_instruction_template(filepath: str, function_name: str) -> str`**
- 功能：將檔案路徑和函式名稱套用到 `coding_instruction.txt` 模板
- 模板位置：`assets/prompt-template/coding_instruction.txt`
- 返回：套用模板後的完整 prompt
- 特性：
  - 使用 Python `format()` 替換變數
  - 錯誤處理（模板不存在時返回空字串）
  - 詳細的日誌記錄

#### 修改的主流程

**`process_project_with_line_by_line()` 函數**
- 新增檢查：`use_coding_instruction` flag
- 處理流程：
  1. 載入互動設定，檢查是否啟用 Coding Instruction
  2. 對每一行 prompt：
     - 如果啟用：解析 → 套用模板 → 使用處理後的 prompt
     - 如果未啟用：直接使用原始 prompt
  3. 儲存時記錄完整資訊（原始、解析結果、處理後）
  
- 日誌記錄增強：
  - 原始 Prompt：使用者的原始內容
  - 解析結果：提取的檔案路徑和函式名稱
  - 處理後的 Prompt：套用模板後的內容
  - 實際發送內容：包含串接（如有啟用）的最終內容

### 2. UI 設定界面（`src/interaction_settings_ui.py`）

#### 新增的 UI 元件

**Coding Instruction 選項區塊**
- 位置：提示詞來源設定框架內
- 元件：
  - Checkbox：「使用 Coding Instruction 模板」
  - 說明文字：3 行說明（功能、格式、適用場景）
  
**狀態控制邏輯**
- `update_coding_instruction_state()` 方法：
  - 專案模式：啟用選項
  - 全域模式：停用選項並自動取消勾選
  
- `on_prompt_source_changed()` 方法：
  - 在提示詞來源改變時自動更新狀態

#### 設定持久化

**載入設定（`load_settings()`）**
```python
"use_coding_instruction": interaction_settings.get("use_coding_instruction", False)
```

**保存設定（`save_settings()` 和 `save_and_close()`）**
```python
"use_coding_instruction": self.settings.get("use_coding_instruction", False)
self.settings["use_coding_instruction"] = self.use_coding_instruction_var.get()
```

### 3. 文檔和測試

#### 使用文檔
- 檔案：`docs/CODING_INSTRUCTION_FEATURE.md`
- 內容：
  - 功能概述
  - 使用方法（4 個步驟）
  - 執行範例
  - 與 AS 模式的差異對比表
  - 疑難排解

#### 單元測試
- 檔案：`tests/test_coding_instruction.py`
- 測試內容：
  1. 函式解析功能（4 個測試案例）
  2. 模板套用功能（3 個測試案例）
  3. 端對端流程（完整流程驗證）
- 測試結果：✅ 所有測試通過

## 🎯 功能特性

### 核心特性
1. ✅ 自動解析 `filepath|function()` 格式
2. ✅ 只提取第一個函式（忽略後續函式）
3. ✅ 套用 `coding_instruction.txt` 模板
4. ✅ 詳細的日誌記錄（原始、解析、處理後）
5. ✅ 與現有功能無縫整合（不影響 AS 模式和全域模式）

### 用戶體驗
1. ✅ UI 選項僅在專案模式下可用（自動停用於全域模式）
2. ✅ 清晰的說明文字指引使用者
3. ✅ 完整的錯誤處理和警告訊息
4. ✅ 儲存的回應檔案包含完整資訊（便於追蹤和除錯）

### 兼容性
1. ✅ 不影響 Artificial Suicide 模式
2. ✅ 不影響全域提示詞模式
3. ✅ 支援與回應串接功能併用
4. ✅ 支援與 CWE 掃描功能併用

## 📊 程式碼變更統計

### 修改的檔案
1. `src/copilot_handler.py`
   - 新增 2 個輔助函數（共 ~80 行）
   - 修改 `process_project_with_line_by_line()` 函數
   - 修改日誌記錄邏輯

2. `src/interaction_settings_ui.py`
   - 新增 Coding Instruction UI 區塊（~50 行）
   - 新增 `update_coding_instruction_state()` 方法
   - 更新設定載入/保存邏輯

### 新增的檔案
1. `docs/CODING_INSTRUCTION_FEATURE.md`（使用文檔，~250 行）
2. `tests/test_coding_instruction.py`（測試腳本，~150 行）

### 總計
- 修改檔案：2 個
- 新增檔案：2 個
- 新增程式碼：約 530 行（包含註釋和文檔）

## 🔍 測試驗證

### 測試案例 1：函式解析
```python
輸入：src/crypto/encryption.py|encrypt_data()、decrypt_data()
結果：('src/crypto/encryption.py', 'encrypt_data()')  ✅
```

### 測試案例 2：模板套用
```python
輸入：filepath='src/crypto/encryption.py', function='encrypt_data()'
結果：Please check src/crypto/encryption.py's encrypt_data() function...  ✅
```

### 測試案例 3：端對端流程
```
1. 解析原始 prompt → 2. 套用模板 → 3. 生成最終 prompt  ✅
```

## 📝 使用範例

### 設定步驟
1. 準備 `prompt.txt`：
   ```
   src/crypto/encryption.py|encrypt_data()、decrypt_data()
   src/auth/login.py|authenticate_user()
   ```

2. 執行 `python main.py`

3. 在第二個設定介面：
   - 選擇「使用專案專用提示詞」
   - 勾選「使用 Coding Instruction 模板」

4. 系統自動處理並發送

### 執行結果
```
第 1 行：src/crypto/encryption.py|encrypt_data()、decrypt_data()
  ↓ 解析
檔案：src/crypto/encryption.py
函式：encrypt_data()（只取第一個）
  ↓ 套用模板
Please check src/crypto/encryption.py's encrypt_data() function, 
and directly implement the code to complete this function.
```

## 🎉 完成狀態

### 所有 TODO 項目已完成：
- [x] 分析並理解需求與現有流程
- [x] 設計新功能的集成點
- [x] 在互動設定 UI 添加新選項
- [x] 創建提示詞處理輔助函數
- [x] 修改 process_project_with_line_by_line 函數
- [x] 測試並驗證功能

### 驗證項目：
- ✅ UI 中新選項正確顯示和保存
- ✅ 非 AS 模式使用專案提示詞時正確解析並套用模板
- ✅ 原有的 AS 模式和全域提示詞模式不受影響
- ✅ 檔案保存時記錄原始和處理後的 prompt

## 🚀 後續建議

### 可選的增強功能（未來）
1. **多函式處理**：支援處理多個函式（目前只處理第一個）
2. **自定義模板**：允許使用者自定義模板變數
3. **預覽功能**：在 UI 中預覽處理後的 prompt
4. **模板驗證**：啟動時驗證模板檔案是否存在

### 維護建議
1. 定期檢查 `coding_instruction.txt` 模板是否存在
2. 如需修改模板格式，確保變數名稱一致（`{target_file}`, `{target_function_name}`）
3. 新增類似功能時，可參考此實現的架構

## 📚 相關文件

- 使用說明：`docs/CODING_INSTRUCTION_FEATURE.md`
- 測試腳本：`tests/test_coding_instruction.py`
- 核心實現：`src/copilot_handler.py` (行 378-457)
- UI 設定：`src/interaction_settings_ui.py` (行 267-309)

---

**實現日期**：2025-11-04  
**實現狀態**：✅ 完成並測試通過  
**兼容性**：完全兼容現有系統，不影響 AS 模式
