# Coding Instruction 功能 - 快速參考

## 🎯 一句話說明
在非 AS 模式下使用專案提示詞時，可自動解析 `prompt.txt` 並套用 `coding_instruction.txt` 模板。

## 📋 快速啟用步驟

### 1. 準備 prompt.txt
在專案目錄下創建 `prompt.txt`：
```
src/file1.py|function1()、function2()
src/file2.py|function3()
```

### 2. 啟動腳本
```bash
python main.py
```

### 3. UI 設定
在第二個設定介面：
1. 選擇「使用專案專用提示詞」
2. ✅ 勾選「使用 Coding Instruction 模板」

### 4. 執行
系統自動處理每一行 prompt。

## 🔧 工作原理

```
原始 Prompt                解析                 套用模板
───────────────────────────────────────────────────────────
src/file.py|func1()、func2()
           ↓
      只取第一個函式          檔案: src/file.py
                           函式: func1()
                              ↓
                         coding_instruction.txt
                              ↓
                    Please check src/file.py's
                    func1() function, and...
```

## 📝 模板內容

位置：`assets/prompt-template/coding_instruction.txt`

```
Please check {target_file}'s {target_function_name} function, 
and directly implement the code to complete this function.
```

變數：
- `{target_file}` - 檔案路徑
- `{target_function_name}` - 函式名稱

## ⚙️ 核心函數

### `_parse_and_extract_first_function(prompt_line)`
解析 prompt 行，提取第一個函式。

```python
輸入：src/file.py|func1()、func2()
輸出：('src/file.py', 'func1()')
```

### `_apply_coding_instruction_template(filepath, function_name)`
套用模板。

```python
輸入：filepath='src/file.py', function_name='func1()'
輸出：完整的 prompt 字串
```

## 🧪 測試

```bash
python tests/test_coding_instruction.py
```

預期輸出：所有測試通過 ✅

## 📊 儲存格式

回應儲存在 `ExecutionResult/Success/{project}/第N輪/`

檔案內容包含：
- 原始 Prompt
- 解析結果（檔案、函式）
- 處理後的 Prompt
- 實際發送內容（如有串接）
- Copilot 回應

## ⚠️ 注意事項

1. **僅專案模式**：此功能僅在「使用專案專用提示詞」時可用
2. **格式要求**：prompt.txt 必須符合 `filepath|function()` 格式
3. **只取第一個**：如有多個函式（用「、」分隔），只處理第一個
4. **不影響 AS**：Artificial Suicide 模式不受影響

## 🔍 疑難排解

| 問題 | 解決方法 |
|------|---------|
| 選項被停用 | 確認已選擇「使用專案專用提示詞」 |
| 無法套用模板 | 檢查 `assets/prompt-template/coding_instruction.txt` 是否存在 |
| 解析失敗 | 檢查 prompt.txt 格式（必須有 `\|` 分隔符） |
| 函式名稱錯誤 | 確認函式名稱包含括號（如 `function()`） |

## 📚 相關文件

- 詳細說明：`docs/CODING_INSTRUCTION_FEATURE.md`
- 實現總結：`docs/CODING_INSTRUCTION_IMPLEMENTATION_SUMMARY.md`
- 測試腳本：`tests/test_coding_instruction.py`

## 🎉 狀態

✅ 已完成並測試  
✅ 所有功能正常運作  
✅ 不影響現有功能

---
最後更新：2025-11-04
