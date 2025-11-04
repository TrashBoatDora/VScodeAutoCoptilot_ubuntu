# 檔案數量限制功能實施總結

## 更改概述

新增了檔案數量限制功能，允許使用者在第一個 UI 對話框中設定總共要處理的檔案數量上限。這對於處理大量專案時特別有用，可以避免自動化腳本執行時間過長。

## 修改的檔案

### 1. `config/config.py`
**新增內容**：
- 添加 `MAX_FILES_TO_PROCESS = None` 配置項（預設無限制）
- 檔案數量限制相關註解

**影響**：
- 提供全域配置項（雖然實際限制由 UI 設定）

---

### 2. `src/ui_manager.py`
**新增內容**：
- 在 `__init__` 中添加 `self.max_files_to_process = 0` 屬性
- 在 `show_options_dialog()` 中添加「📊 檔案數量限制」UI 區塊：
  - 勾選框：啟用/停用限制
  - Spinbox：設定最大檔案數（1~10,000）
  - 說明文字
- 添加 `_update_limit_state()` 方法控制 Spinbox 啟用/停用
- 修改返回值從 5 個元組擴展為 6 個元組（新增 `max_files_to_process`）
- 視窗高度從 650 增加到 750

**影響**：
- 使用者可在第一個對話框中設定檔案數量限制
- 返回值需要在 `main.py` 中相應更新

---

### 3. `main.py`
**新增內容**：
- 導入 `Tuple` 型別
- 在 `HybridUIAutomationScript.__init__()` 中添加：
  - `self.total_files_processed = 0`（全域計數器）
  - `self.max_files_limit = 0`（最大限制）
- 在 `run()` 中：
  - 接收並設定 `max_files_to_process`
  - 記錄檔案限制狀態到日誌
- 在 `_process_all_projects()` 中：
  - 處理每個專案前檢查檔案數量限制
  - 計算專案檔案數（`config.count_project_prompt_lines()`）
  - 判斷是否達到限制，決定跳過或部分處理
  - 記錄詳細的配額信息到日誌
  - 處理結束後輸出檔案處理統計
- 在 `_execute_project_automation()` 中：
  - AS 模式：接收並累計 `files_processed`
  - 一般模式：處理後計算並累計檔案數
  - 多輪互動模式：處理後計算並累計檔案數
- 修改 `_execute_artificial_suicide_mode()` 的返回類型為 `Tuple[bool, int]`
  - 傳遞 `max_files_limit` 和 `files_processed_so_far` 給 AS 模式
  - 接收並返回實際處理的檔案數

**影響**：
- 主流程支援檔案數量限制
- 跨專案累計檔案數
- 詳細的日誌輸出

---

### 4. `src/artificial_suicide_mode.py`
**新增內容**：
- 導入 `Tuple` 型別
- 在 `__init__()` 中添加參數：
  - `max_files_limit: int = 0`
  - `files_processed_so_far: int = 0`
- 添加屬性：
  - `self.max_files_limit`
  - `self.files_processed_so_far`
  - `self.files_processed_in_project = 0`
- 在 `__init__()` 中實現檔案限制邏輯：
  - 計算剩餘配額
  - 截斷 `prompt_lines` 以符合限制
  - 記錄日誌
- 修改 `execute()` 的返回類型為 `Tuple[bool, int]`：
  - 如果沒有行要處理，返回 `(True, 0)`
  - 執行結束前記錄 `files_processed_in_project`
  - 返回 `(success, files_processed_in_project)`

**影響**：
- AS 模式完全支援檔案數量限制
- 可正確處理部分專案（只處理前 N 行）
- 返回實際處理的檔案數供主腳本累計

---

### 5. 新增檔案

#### `test_file_limit.py`
**內容**：
- `test_count_prompt_lines()`：測試計算專案檔案數的功能
- `test_file_limit_logic()`：測試檔案限制邏輯的各種情況

**用途**：
- 驗證檔案計數功能
- 測試限制邏輯的正確性

#### `docs/FILE_LIMIT_FEATURE.md`
**內容**：
- 功能概述
- 使用方式
- 檔案數量計算方式
- 限制行為（3 種情況）
- 技術實現細節
- 日誌輸出範例
- 適用場景
- 注意事項
- 未來改進建議

**用途**：
- 使用者文檔
- 開發者參考

---

## 功能特性

### ✅ 已實現

1. **UI 設定**：在第一個對話框中提供檔案數量限制設定
2. **全域計數**：跨專案累計處理的檔案數
3. **檔案計算**：基於 `prompt.txt` 的行數，與輪數無關
4. **部分處理**：當專案檔案數超過剩餘配額時，只處理部分行
5. **AS 模式支援**：Artificial Suicide 模式完全支援此功能
6. **一般模式支援**：一般互動模式和多輪互動模式也支援此功能
7. **詳細日誌**：輸出詳細的配額和處理統計信息
8. **測試腳本**：提供測試腳本驗證功能

### 🎯 核心邏輯

```python
# 檢查檔案數量限制
if self.max_files_limit > 0:
    project_file_count = config.count_project_prompt_lines(project.path)
    
    # 已達限制 → 跳過專案
    if self.total_files_processed >= self.max_files_limit:
        break
    
    # 部分處理 → 只處理部分檔案
    remaining_quota = self.max_files_limit - self.total_files_processed
    if project_file_count > remaining_quota:
        # AS 模式會在初始化時自動截斷 prompt_lines
        # 一般模式會完整處理，但計數會受限
```

---

## 測試結果

### 邏輯測試（`test_file_limit.py`）

```
✅ 測試案例 1: 無限制 → 完整處理
✅ 測試案例 2: 足夠配額 → 完整處理
✅ 測試案例 3: 部分配額 → 部分處理
✅ 測試案例 4: 已達限制 → 跳過專案
✅ 測試案例 5: 已超限制 → 跳過專案
```

### 編譯檢查

```
✅ main.py: No errors found
✅ src/ui_manager.py: No errors found
✅ src/artificial_suicide_mode.py: No errors found
✅ config/config.py: No errors found
```

---

## 使用範例

### 情況 1：限制處理 50 個檔案

```
選擇專案：project_A (20 行), project_B (25 行), project_C (30 行)
設定限制：50 個檔案

執行結果：
- project_A: 完整處理 20 個檔案 ✅
- project_B: 完整處理 25 個檔案 ✅
- project_C: 只處理前 5 個檔案 ⚠️（剩餘配額: 5）
- 總計: 50 個檔案
```

### 情況 2：無限制

```
選擇專案：project_A (20 行), project_B (25 行), project_C (30 行)
不勾選限制或設定為 0

執行結果：
- project_A: 完整處理 20 個檔案 ✅
- project_B: 完整處理 25 個檔案 ✅
- project_C: 完整處理 30 個檔案 ✅
- 總計: 75 個檔案
```

---

## 注意事項

1. **計數方式**：
   - 檔案數 = `prompt.txt` 的行數
   - 與輪數無關（10 輪處理 1 行仍算 1 個檔案）

2. **累計計算**：
   - 跨所有專案累計
   - 不會每個專案重新計算

3. **AS 模式**：
   - 在初始化時截斷 `prompt_lines`
   - 返回實際處理的檔案數

4. **一般模式**：
   - 完整處理專案（不截斷）
   - 處理後計算檔案數並累計

5. **部分處理**：
   - 只有 AS 模式支援真正的部分處理（截斷 prompt_lines）
   - 一般模式會完整處理專案，但累計時會記錄

---

## 未來改進方向

1. **一般模式部分處理**：實現一般模式的部分處理（目前只有 AS 模式支援）
2. **優先級設定**：允許為專案設定優先級
3. **斷點續傳**：記住上次處理位置，下次繼續
4. **動態調整**：根據執行時間或系統負載調整限制
5. **統計報告**：在最終報告中顯示檔案處理統計

---

**實施日期**：2025-11-05
**實施者**：GitHub Copilot
**測試狀態**：✅ 邏輯測試通過，編譯檢查通過
**文檔狀態**：✅ 已完成
