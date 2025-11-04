# 檔案數量限制功能說明

## 功能概述

新增的檔案數量限制功能允許使用者在第一個 UI 對話框中設定總共要處理的檔案數量上限。這對於處理大量專案時特別有用，可以避免自動化腳本執行時間過長。

## 使用方式

### 1. 啟動腳本

```bash
python main.py
```

### 2. 在第一個 UI 對話框中設定

在「📊 檔案數量限制」區塊中：

1. **勾選「限制總共處理的檔案數量」**
2. **設定最大處理檔案數**（範圍：1 ~ 10,000）
3. **如果不勾選**，則系統將處理所有選定專案的所有檔案（無限制）

### 3. 檔案數量計算方式

- **每個專案的檔案數 = prompt.txt 的行數**
- **與輪數無關**：即使設定為處理 10 輪，prompt.txt 中的 1 行仍然只算作處理 1 個檔案
- **累計計算**：系統會累計所有已處理專案的檔案數

### 4. 限制行為

#### 情況 1：專案檔案數小於剩餘配額
- **行為**：完整處理該專案
- **範例**：
  - 限制：100 個檔案
  - 已處理：80 個檔案
  - 專案 A 有 10 個檔案
  - **結果**：完整處理專案 A 的 10 個檔案

#### 情況 2：專案檔案數大於剩餘配額
- **行為**：部分處理（只處理到達限制為止）
- **範例**：
  - 限制：100 個檔案
  - 已處理：95 個檔案
  - 專案 A 有 10 個檔案
  - **結果**：只處理專案 A 的前 5 個檔案

#### 情況 3：已達到限制
- **行為**：跳過所有剩餘專案
- **範例**：
  - 限制：100 個檔案
  - 已處理：100 個檔案
  - **結果**：跳過所有後續專案

## 技術實現

### 核心組件

#### 1. Config 配置（`config/config.py`）

```python
# 檔案處理限制設定
MAX_FILES_TO_PROCESS = None  # 限制總共處理的檔案數量（None 表示無限制）

# 工具方法
@classmethod
def count_project_prompt_lines(cls, project_path: str):
    """計算專案專用提示詞的行數"""
    lines = cls.load_project_prompt_lines(project_path)
    return len(lines)
```

#### 2. UI 管理器（`src/ui_manager.py`）

在 `show_options_dialog()` 方法中添加：

```python
# 檔案數量限制設定
limit_enabled_var = tk.BooleanVar(value=False)
limit_count_var = tk.IntVar(value=100)

# 返回值包含 max_files_to_process
return (
    selected_projects, 
    use_smart_wait, 
    clean_history,
    artificial_suicide_enabled,
    artificial_suicide_rounds,
    max_files_to_process  # 新增
)
```

#### 3. 主腳本（`main.py`）

```python
class HybridUIAutomationScript:
    def __init__(self):
        # 檔案處理計數器
        self.total_files_processed = 0
        self.max_files_limit = 0
    
    def _process_all_projects(self, projects):
        for project in projects:
            # 檢查檔案數量限制
            if self.max_files_limit > 0:
                project_file_count = config.count_project_prompt_lines(project.path)
                
                # 已達限制
                if self.total_files_processed >= self.max_files_limit:
                    break
                
                # 部分處理
                remaining_quota = self.max_files_limit - self.total_files_processed
                if project_file_count > remaining_quota:
                    # 只處理部分檔案
                    pass
```

#### 4. Artificial Suicide 模式（`src/artificial_suicide_mode.py`）

```python
class ArtificialSuicideMode:
    def __init__(self, ..., max_files_limit=0, files_processed_so_far=0):
        self.max_files_limit = max_files_limit
        self.files_processed_so_far = files_processed_so_far
        self.files_processed_in_project = 0
        
        # 如果有檔案數量限制，計算本專案可處理的行數
        if self.max_files_limit > 0:
            remaining_quota = self.max_files_limit - self.files_processed_so_far
            if remaining_quota <= 0:
                self.prompt_lines = []
            elif len(self.prompt_lines) > remaining_quota:
                self.prompt_lines = self.prompt_lines[:remaining_quota]
    
    def execute(self) -> Tuple[bool, int]:
        # 執行完成後返回實際處理的檔案數
        self.files_processed_in_project = len(self.prompt_lines)
        return True, self.files_processed_in_project
```

## 日誌輸出

系統會在執行過程中輸出詳細的檔案處理統計信息：

```
📊 檔案數量限制已啟用: 最多處理 100 個檔案
📊 專案 project_A 有 10 個檔案（已處理: 0/100）
📊 已處理 10 個檔案（總計: 10）
📊 專案 project_B 有 50 個檔案（已處理: 10/100）
📊 已處理 50 個檔案（總計: 60）
⚠️  專案 project_C 有 50 個檔案，但只剩 40 個配額，將只處理前 40 個檔案
📊 已處理 40 個檔案（總計: 100）
⚠️  已達到檔案數量限制 (100/100)，停止處理剩餘 5 個專案
📊 檔案處理統計: 100/100
```

## 適用場景

1. **測試環境**：快速測試腳本功能，只處理少量檔案
2. **資源受限**：系統資源或時間有限，需要分批處理
3. **漸進式執行**：先處理一部分，觀察結果後再處理剩餘部分
4. **配額管理**：API 調用次數有限制時

## 注意事項

1. **計數方式**：只計算 prompt.txt 的行數，與實際執行輪數無關
2. **跨專案累計**：檔案數量是跨所有專案累計的，不是每個專案重新計算
3. **部分處理**：當專案被部分處理時，只會處理 prompt.txt 的前 N 行
4. **AS 模式支援**：Artificial Suicide 模式完全支援此功能
5. **一般模式支援**：一般互動模式和多輪互動模式也支援此功能

## 未來改進建議

1. **更精細的控制**：允許為每個專案設定不同的優先級
2. **斷點續傳**：記住上次處理到哪裡，下次從斷點繼續
3. **動態調整**：根據執行時間或系統負載動態調整限制
4. **統計報告**：在最終報告中顯示詳細的檔案處理統計

---

**最後更新日期**：2025-11-05
**功能版本**：v1.0
