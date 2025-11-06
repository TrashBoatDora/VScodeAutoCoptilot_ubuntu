# File Limit Implementation Summary

## 問題
檔案限制設為 1，但實際處理了 2 個函數。系統只記錄日誌但沒有真正執行限制。

## 實作概覽

### 修改的檔案
1. **`main.py`** - 主流程檔案
2. **`src/copilot_handler.py`** - Copilot 處理器

---

## 修改詳情

### 1. main.py - 主流程

#### 1.1 _process_all_projects() (Line ~303-340)
```python
# 新增: 計算並傳遞 max_lines_for_project
max_lines_for_project = None  # None 表示無限制
if self.max_files_limit > 0:
    project_file_count = config.count_project_prompt_lines(project.path)
    remaining_quota = self.max_files_limit - self.total_files_processed
    max_lines_for_project = min(remaining_quota, project_file_count)

# 傳遞 max_lines 給下層函數
success = self._process_single_project(project, max_lines=max_lines_for_project)
```

**變更**:
- 新增 `max_lines_for_project` 變數
- 計算剩餘配額並取 min(剩餘配額, 專案檔案數)
- 將限制傳遞給 `_process_single_project`

#### 1.2 _process_single_project() (Line ~366)
```python
def _process_single_project(self, project: ProjectInfo, max_lines: int = None) -> bool:
    # 傳遞 max_lines 給執行函數
    success = self._execute_project_automation(project, project_logger, max_lines=max_lines)
```

**變更**:
- 新增 `max_lines` 參數
- 傳遞給 `_execute_project_automation`

#### 1.3 _execute_project_automation() (Line ~424)
```python
def _execute_project_automation(self, project: ProjectInfo, project_logger, max_lines: int = None) -> bool:
    # AS Mode
    if artificial_suicide_mode:
        success, files_processed = self._execute_artificial_suicide_mode(
            project, artificial_suicide_rounds, project_logger, max_lines=max_lines
        )
        self.total_files_processed += files_processed  # 使用實際處理數量
    
    # Interaction Mode (多輪互動)
    elif interaction_enabled:
        success, files_processed = self.copilot_handler.process_project_with_iterations(
            project.path, max_rounds, max_lines=max_lines
        )
        self.total_files_processed += files_processed  # 使用實際處理數量
    
    # Normal Mode (一般模式)
    else:
        success, files_processed = self.copilot_handler.process_project_complete(
            project.path, use_smart_wait=self.use_smart_wait, max_lines=max_lines
        )
        self.total_files_processed += files_processed  # 使用實際處理數量
```

**變更**:
- 新增 `max_lines` 參數
- 所有 3 種模式都傳遞 `max_lines`
- 改為接收並使用 **實際處理的行數**（不再用 `config.count_project_prompt_lines`）

#### 1.4 _execute_artificial_suicide_mode() (Line ~602)
```python
def _execute_artificial_suicide_mode(
    self, 
    project: ProjectInfo, 
    num_rounds: int,
    project_logger,
    max_lines: int = None  # 新增
) -> Tuple[bool, int]:
```

**變更**:
- 新增 `max_lines` 參數
- AS Mode 已有內建的 `max_files_limit` 處理機制

---

### 2. src/copilot_handler.py - Copilot 處理器

#### 2.1 process_project_complete() (Line ~1176)
```python
def process_project_complete(
    self, project_path: str, use_smart_wait: bool = None, 
    round_number: int = 1, custom_prompt: str = None, 
    max_lines: int = None  # 新增
) -> Tuple[bool, int]:  # 返回值改為 (bool, int)
    
    # 檢查是否為專案專用模式
    prompt_source_mode = interaction_settings.get("prompt_source_mode", "global")
    
    if prompt_source_mode == "project" and custom_prompt is None:
        # 專案專用模式：調用逐行處理
        success, processed_lines, failed_lines = self.process_project_with_line_by_line(
            project_path, round_number, use_smart_wait, max_lines=max_lines
        )
        return success, processed_lines  # 返回實際處理行數
    
    # 全域模式：單次處理
    # ... 原有邏輯 ...
    return True, 1  # 返回成功和處理數=1
```

**變更**:
- 新增 `max_lines` 參數
- **返回值改為 `Tuple[bool, int]`**（原為 `Tuple[bool, Optional[str]]`）
- 專案專用模式：呼叫 `process_project_with_line_by_line` 並返回實際行數
- 全域模式：返回 `1`（處理了 1 個 prompt）

#### 2.2 process_project_with_line_by_line() (Line ~823)
```python
def process_project_with_line_by_line(
    self, project_path: str, round_number: int = 1, 
    use_smart_wait: bool = None, 
    max_lines: int = None  # 新增
) -> Tuple[bool, int, List[str]]:
    
    # 載入提示詞行
    prompt_lines = self.load_project_prompt_lines(project_path)
    
    # 應用行數限制 ⭐ 核心邏輯
    original_line_count = len(prompt_lines)
    if max_lines is not None and max_lines > 0:
        prompt_lines = prompt_lines[:max_lines]  # 切片限制
        self.logger.info(f"📊 檔案限制已啟用: 原有 {original_line_count} 行，限制處理前 {max_lines} 行")
    
    total_lines = len(prompt_lines)  # 使用限制後的行數
    # ... 逐行處理邏輯 ...
    
    return successful_lines > 0, successful_lines, failed_lines
```

**變更**:
- 新增 `max_lines` 參數
- **在讀取 prompt_lines 後立即應用限制**（`prompt_lines[:max_lines]`）
- 記錄限制資訊到日誌

#### 2.3 process_project_with_iterations() (Line ~1463)
```python
def process_project_with_iterations(
    self, project_path: str, max_rounds: int = None, 
    max_lines: int = None  # 新增
) -> Tuple[bool, int]:  # 返回值改為 (bool, int)
    
    prompt_source_mode = interaction_settings.get("prompt_source_mode", config.PROMPT_SOURCE_MODE)
    
    if prompt_source_mode == "project":
        return self._process_project_with_project_prompts(
            project_path, max_rounds, interaction_settings, max_lines=max_lines
        )
    
    if not interaction_settings["interaction_enabled"]:
        success, processed = self.process_project_complete(
            project_path, round_number=1, max_lines=max_lines
        )
        return success, processed
    
    # 多輪互動邏輯...
    # 全域模式返回 1（處理了 1 個 prompt）
    return success_count > 0, 1
```

**變更**:
- 新增 `max_lines` 參數
- **返回值改為 `Tuple[bool, int]`**（原為 `bool`）
- 傳遞 `max_lines` 給所有子函數
- 返回實際處理的行數

#### 2.4 _process_project_with_project_prompts() (Line ~1069)
```python
def _process_project_with_project_prompts(
    self, project_path: str, max_rounds: int = None, 
    interaction_settings: dict = None, 
    max_lines: int = None  # 新增
) -> Tuple[bool, int]:  # 返回值改為 (bool, int)
    
    # 單輪情況
    if not interaction_settings.get("interaction_enabled", True):
        success, successful_lines, failed_lines = self.process_project_with_line_by_line(
            project_path, round_number=1, max_lines=max_lines
        )
        return success, successful_lines
    
    # 多輪情況
    # 應用行數限制
    prompt_lines = self.load_project_prompt_lines(project_path)
    original_line_count = len(prompt_lines)
    if max_lines is not None and max_lines > 0:
        self.logger.info(f"📊 檔案限制已啟用: 原有 {original_line_count} 行，每輪限制處理前 {max_lines} 行")
    
    first_round_successful_lines = 0
    
    for round_num in range(1, max_rounds + 1):
        success, successful_lines, failed_lines = self.process_project_with_line_by_line(
            project_path, round_number=round_num, max_lines=max_lines
        )
        
        if round_num == 1:
            first_round_successful_lines = successful_lines
    
    # 返回第一輪實際處理的行數（不乘以輪數，避免重複計算）
    return overall_success and (first_round_successful_lines > 0), first_round_successful_lines
```

**變更**:
- 新增 `max_lines` 參數
- **返回值改為 `Tuple[bool, int]`**（原為 `bool`）
- 多輪情況：只返回第一輪處理的行數（不乘以輪數）
- 記錄每輪限制資訊

---

## 執行流程示例

### 場景：檔案限制 = 1，專案有 2 行 prompt.txt

```
main.py:
├─ _process_all_projects()
│  ├─ max_files_limit = 1
│  ├─ total_files_processed = 0
│  ├─ remaining_quota = 1 - 0 = 1
│  ├─ max_lines_for_project = min(1, 2) = 1
│  └─ _process_single_project(project, max_lines=1)
│     └─ _execute_project_automation(project, logger, max_lines=1)
│        └─ copilot_handler.process_project_complete(path, max_lines=1)
│           └─ process_project_with_line_by_line(path, max_lines=1)
│              ├─ prompt_lines = ["line1", "line2"]
│              ├─ prompt_lines = prompt_lines[:1]  ⭐ 切片限制
│              ├─ prompt_lines = ["line1"]
│              ├─ 處理 1 行
│              └─ return (True, 1, [])  # 成功, 處理了1行, 無失敗
│           ← return (True, 1)  # 成功, 處理了1行
│        ← files_processed = 1
│        ← total_files_processed += 1  # 0 + 1 = 1
│     ← return True
│  ← return True
└─ 最終統計: total_files_processed = 1 ✅
```

---

## 測試驗證

### 預期結果（檔案限制 = 1）
```
AutomationReport:
  檔案處理限制: 1
  實際處理函數數: 1  ✅ (原為 2)
  CSV記錄總數: 1     ✅ (原為 0)
  完整執行專案數: 0  ⚠️  (1/2 未完整)
  未完整執行專案數: 1 ✅
```

### 測試命令
```bash
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction
python main.py

# 在啟動對話框中:
# - 選擇專案: aider__CWE-327__CAL-ALL-6b42874e__M-call
# - 互動設定: 關閉多輪互動, 提示詞來源=專案專用
# - 檔案數量限制: 1
# - CWE 掃描: 啟用, CWE-327

# 預期日誌:
# 📊 檔案限制已啟用: 原有 2 行，限制處理前 1 行
# 開始按行處理專案 aider__CWE-327__CAL-ALL-6b42874e__M-call，共 1 行提示詞
# 處理第 1/1 行...
# ✅ 第 1/1 行處理成功
# 📊 已處理 1 個檔案（總計: 1）
```

---

## 關鍵改進

### 1. 統一參數傳遞
所有處理路徑（AS模式、互動模式、一般模式）都支援 `max_lines` 參數。

### 2. 切片限制應用
在 `process_project_with_line_by_line` 中使用 `prompt_lines[:max_lines]` 直接限制行數。

### 3. 實際計數返回
所有 copilot_handler 方法返回 **實際處理的行數**，不再依賴 `count_project_prompt_lines`。

### 4. 防止重複計算
多輪互動模式只返回第一輪處理的行數，避免重複累加。

### 5. 清晰日誌
在應用限制時記錄詳細資訊（原始行數、限制行數）。

---

## 後續工作

1. ✅ 測試檔案限制 = 1 的執行
2. ✅ 驗證 AutomationReport 正確顯示
3. ✅ 檢查多輪互動模式的計數邏輯
4. ✅ 確認 AS 模式的限制機制

---

**實作完成時間**: 2025-11-06
**相關文檔**: 
- `docs/FILE_LIMIT_BUG_ANALYSIS.md` (問題分析)
- `docs/NON_AS_MODE_CSV_FIX.md` (CSV 路徑修正)
