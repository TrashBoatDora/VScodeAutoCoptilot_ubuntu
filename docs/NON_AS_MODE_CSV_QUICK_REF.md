# 非 AS 模式 CSV 格式快速參考

## 關鍵變更
- **CSV 欄位**：AS 模式用 2 欄記錄函式名稱，非 AS 模式只用 1 欄
- **掃描範圍**：**所有模式都只處理第一個函式**（AS 和非 AS 一致）

## CSV 格式對比

### AS 模式（13 欄）
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
```

### 非 AS 模式（12 欄）
```csv
輪數,行號,檔案路徑,函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
```

## 模式判斷
```python
if cwe_scan_manager.function_name_tracker:
    # AS 模式
else:
    # 非 AS 模式
```

## 函式提取範圍

### Prompt 格式
```
crypto.py|func1()、func2()、func3()
```

### AS 和非 AS 模式（統一行為）
- 提取：`['func1()']`
- 只處理第 1 個函式

**重要發現**：AS 模式在 `artificial_suicide_mode.py` (line 756) 已經構造為單一函式：
```python
single_function_prompt = f"{target_file}|{target_function_name}"
```

## 修改位置
1. `cwe_scan_manager.py::_save_function_level_csv()` (line 170-370)
   - CSV 標題列（根據模式選擇欄位）
   - 名稱查詢邏輯（新增 `function_name` 變數）
   - 資料列寫入（3 處：failed/vulns/success）

2. `cwe_scan_manager.py::extract_function_targets_from_prompt()` (line 88-128)
   - 統一只取第一個函式：`func_names = [func_names[0]]`

## 測試
```bash
python tests/test_csv_format_changes.py
```

## 相關文檔
- `NON_AS_MODE_CSV_FORMAT_AND_SCAN_SCOPE.md`: 完整說明
- `CODING_INSTRUCTION_FEATURE.md`: Coding Instruction 功能
