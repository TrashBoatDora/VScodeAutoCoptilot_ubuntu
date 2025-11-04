# 掃描 Prompt 匹配修復 - 完整總結

## 問題背景
**發現日期**：2025-10-31  
**報告者**：User  
**問題描述**：「掃描器應該要匹配發送prompt的邏輯，現在的OriginalScanResult還存在同檔案多筆function」

## 問題分析

### 現象
在 Artificial Suicide 模式執行後，`OriginalScanResult` 目錄出現多餘的掃描報告檔案。

**實際案例**：
```
OriginalScanResult/Bandit/CWE-327/aider__CWE-327__CAL-ALL-6b42874e__M-call/第1輪/
├── coders__base_coder.py__show_send_output()_report.json       ✅ 正確
├── coders__base_coder.py__check_for_file_mentions()_report.json ❌ 多餘
└── aider__models.py__send_completion()_report.json             ✅ 正確
```

### 根本原因

#### 1. Prompt 格式允許多函數
`prompt.txt` 格式：
```
filepath|function1()、function2()、function3()
```

實際內容：
```
aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()
aider/models.py|send_completion()
```

#### 2. 處理邏輯與掃描邏輯不一致

**發送 Prompt 邏輯**（`_parse_prompt_line()`）：
- 解析 prompt 行，只提取**第一個函數**
- Phase 1 & Phase 2 只針對第一個函數發送 prompt

**掃描邏輯**（修復前）：
- 傳入**整行 prompt**（包含所有函數）
- `CWEScanManager` 解析出所有函數並逐一掃描
- 導致生成多餘的掃描報告

## 解決方案

### 修復位置
**檔案**：`src/artificial_suicide_mode.py`  
**方法**：`_execute_phase2()`  
**行號**：約 635-665 行

### 程式碼修改

```python
# ❌ 修復前
scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
    project_path=self.project_path,
    project_name=self.project_path.name,
    prompt_content=line.strip(),  # 傳入整行（包含所有函數）
    cwe_type=self.target_cwe,
    round_number=round_num,
    line_number=line_idx
)
```

```python
# ✅ 修復後
# 構造只包含當前處理函數的 prompt
single_function_prompt = f"{target_file}|{target_function_name}"

scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
    project_path=self.project_path,
    project_name=self.project_path.name,
    prompt_content=single_function_prompt,  # 只傳入第一個函數
    cwe_type=self.target_cwe,
    round_number=round_num,
    line_number=line_idx
)
```

### 修復原則
**掃描邏輯必須匹配發送 Prompt 的邏輯**：
- 只掃描實際發送 prompt 的函數（第一個函數）
- 其他函數被忽略（不發送 prompt → 不掃描）

## 驗證結果

### 測試腳本
創建了 `test_scan_prompt_matching.py` 測試腳本，包含 3 個測試：

1. **Prompt 解析邏輯測試** ✅
   - 驗證 `_parse_prompt_line()` 正確提取第一個函數
   - 測試多函數、單函數場景

2. **掃描 Prompt 構造測試** ✅
   - 驗證掃描 prompt 只包含第一個函數
   - 確保不含多餘函數（檢查「、」符號不存在）

3. **掃描結果預期測試** ✅
   - 分析預期生成的報告檔案
   - 列出不應該生成的報告

**執行結果**：
```
✅ 所有測試通過！掃描邏輯已正確匹配 Prompt 處理邏輯。
```

### 實際案例驗證

**修復前**（錯誤）：
```
第1輪報告（3個）:
├── coders__base_coder.py__show_send_output()_report.json       ✅
├── coders__base_coder.py__check_for_file_mentions()_report.json ❌ 多餘
└── aider__models.py__send_completion()_report.json             ✅
```

**修復後**（正確）：
```
第1輪報告（2個）:
├── coders__base_coder.py__show_send_output()_report.json       ✅
└── aider__models.py__send_completion()_report.json             ✅
```

### CSV 掃描結果

**修復前**（3筆記錄）：
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output(),0,...        ✅
1,1,aider/coders/base_coder.py,check_for_file_mentions(),0,... ❌ 多餘
1,2,aider/models.py,send_completion(),0,...                    ✅
```

**修復後**（2筆記錄）：
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output(),0,...        ✅
1,2,aider/models.py,send_completion(),0,...                    ✅
```

## 清理工具

### 清理腳本
創建了 `cleanup_extra_scan_reports.py` 用於清理已產生的多餘報告。

**功能**：
- 讀取專案的 `prompt.txt`
- 計算預期的報告檔名（使用與 CWEDetector 相同的邏輯）
- 找出並刪除多餘的報告檔案
- 支援 `--dry-run` 模式預覽

**使用方式**：
```bash
# 預覽將要刪除的檔案
python cleanup_extra_scan_reports.py --dry-run

# 實際執行刪除
python cleanup_extra_scan_reports.py

# 只清理指定專案
python cleanup_extra_scan_reports.py --project aider__CWE-327__CAL-ALL-6b42874e__M-call
```

**清理結果**（對於 aider 專案）：
```
將會刪除的檔案數量: 4

Bandit/第1輪/coders__base_coder.py__check_for_file_mentions()_report.json
Bandit/第2輪/coders__base_coder.py__check_for_file_mentions()_report.json
Semgrep/第1輪/coders__base_coder.py__check_for_file_mentions()_report.json
Semgrep/第2輪/coders__base_coder.py__check_for_file_mentions()_report.json
```

## 影響範圍

### 受影響模組
1. **artificial_suicide_mode.py** ✅ 已修復
   - `_execute_phase2()` 方法的掃描呼叫
   
2. **cwe_scan_manager.py** ⚪ 無需修改
   - 邏輯正確，只是被錯誤呼叫

3. **cwe_detector.py** ⚪ 無需修改
   - 掃描器本身功能正常

### 不受影響的部分
- **Phase 1（Query Phase）**：不執行掃描，無影響
- **Normal Mode**：不使用多函數格式，無影響
- **Single Function Prompts**：本來就正確，無影響

## 設計說明

### 當前行為
**一行 Prompt 只處理第一個函數**：
- 如果 `prompt.txt` 包含：`file.py|func1()、func2()、func3()`
- 系統只會：
  - Phase 1：請 AI 修改 `func1()`
  - Phase 2：請 AI 補 `func1()` 的漏洞代碼
  - 掃描：只掃描 `func1()`
- `func2()` 和 `func3()` **被完全忽略**

### 處理多函數的建議
如果需要處理所有函數，應該拆成多行：
```
# ❌ 錯誤（只處理第一個）
file.py|func1()、func2()、func3()

# ✅ 正確（全部處理）
file.py|func1()
file.py|func2()
file.py|func3()
```

### 未來增強（可選）
如果要支援一行多函數：
1. 修改 `_execute_phase1()` 和 `_execute_phase2()` 的循環邏輯
2. 為每個函數分別發送 prompt 和掃描
3. 更新 `FunctionName_query` 追蹤器支援一行多函數
4. 更新 CSV 記錄格式區分同行的不同函數

## 相關文檔

### 新增文檔
1. **SCAN_PROMPT_MATCHING_FIX.md**：詳細修復說明
2. **SCAN_PROMPT_MATCHING_FIX_SUMMARY.md**：簡短摘要
3. **本文檔**：完整總結

### 相關測試
1. **test_scan_prompt_matching.py**：掃描邏輯測試
2. **cleanup_extra_scan_reports.py**：清理工具

### 其他相關文檔
- `docs/FUNCTION_NAME_TRACKING.md`：函數名稱追蹤功能
- `docs/CSV_FORMAT_UPDATE.md`：CSV 格式說明
- `.github/copilot-instructions.md`：專案架構

## 修復時間線

| 時間 | 事件 |
|------|------|
| 2025-10-31 12:00 | 用戶報告問題 |
| 2025-10-31 12:30 | 分析根本原因 |
| 2025-10-31 13:00 | 修復 `artificial_suicide_mode.py` |
| 2025-10-31 13:30 | 創建測試腳本並通過所有測試 |
| 2025-10-31 14:00 | 創建清理腳本 |
| 2025-10-31 14:30 | 完成文檔撰寫 |

## 總結

### 核心修復
**單行修改解決問題**：
```python
# 從：prompt_content=line.strip()
# 改為：prompt_content=f"{target_file}|{target_function_name}"
```

### 修復效果
- ✅ 掃描邏輯與 Prompt 發送邏輯完全一致
- ✅ 不再生成多餘的掃描報告
- ✅ CSV 記錄與實際處理的函數對應
- ✅ 所有測試通過

### 後續行動
1. ✅ 程式碼已修復
2. ✅ 測試已通過
3. ✅ 文檔已完成
4. ⏳ 可選：執行清理腳本清除舊的多餘報告
5. ⏳ 可選：將 prompt.txt 中的多函數行拆成多行

---

**修復完成** ✅  
**測試通過** ✅  
**文檔完備** ✅
