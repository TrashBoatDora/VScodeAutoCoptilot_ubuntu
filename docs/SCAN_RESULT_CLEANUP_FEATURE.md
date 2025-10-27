# 掃描結果清理功能說明

## 功能概述

在使用者通過 UI 選定要執行的專案後，系統會自動清理這些專案之前的掃描結果記錄，確保每次重新掃描都是全新的狀態。

## 清理範圍

當使用者在 UI 中選定專案後，系統會完全移除以下目錄和檔案：

### 1. 原始掃描結果 (OriginalScanResult)

這是掃描器（Bandit/Semgrep）直接輸出的原始 JSON 報告：

```
OriginalScanResult/
├── Bandit/
│   └── CWE-*/
│       └── {專案名稱}/          ← 完整目錄刪除
│           ├── 第1輪/
│           │   ├── file1__func1_report.json
│           │   └── file2__func2_report.json
│           └── 第2輪/
│               └── ...
└── Semgrep/
    └── CWE-*/
        └── {專案名稱}/          ← 完整目錄刪除
            └── 第1輪/
                └── ...
```

**清理結果**: 整個 `{專案名稱}/` 目錄及其所有子目錄和檔案都會被刪除

### 2. 處理後的掃描統計 (CWE_Result)

這是處理後的 CSV 格式統計資料：

```
CWE_Result/
└── CWE-*/
    ├── Bandit/
    │   └── {專案名稱}/          ← 完整目錄刪除
    │       ├── 第1輪/
    │       │   └── {專案名稱}_function_level_scan.csv
    │       └── 第2輪/
    │           └── ...
    └── Semgrep/
        └── {專案名稱}/          ← 完整目錄刪除
            └── 第1輪/
                └── ...
```

**清理結果**: 整個 `{專案名稱}/` 目錄及其所有子目錄和檔案都會被刪除

### 3. 執行結果記錄 (ExecutionResult)

```
ExecutionResult/
├── Success/
│   └── {專案名稱}/              ← 完整目錄刪除
│       ├── {專案名稱}_第1輪.md
│       └── {專案名稱}_第2輪.md
├── AutomationLog/
│   └── {專案名稱}_*.txt         ← 檔案刪除
└── AutomationReport/
    └── {專案名稱}_*.json        ← 檔案刪除
```

### 4. 專案狀態記錄

清理後，`projects/automation_status.json` 中的專案狀態會被重置為 `pending`。

## 使用方式

### 方法 1: 通過 UI 自動清理（推薦）

1. 運行主程式：
   ```bash
   python main.py
   ```

2. 在「選擇要處理的專案」對話框中點擊「📁 瀏覽專案」

3. 在專案選擇器中：
   - 單擊選擇/取消選擇專案
   - Shift + 單擊進行範圍選擇
   - Ctrl + 單擊進行多選
   - 或使用「全選」按鈕

4. 點擊「✓ 確認」

5. 系統會顯示警告：
   ```
   ⚠️  將會清除這些專案的執行記錄和結果！
   ```

6. 確認後，系統會自動清理選定專案的所有掃描結果

### 方法 2: 程式化調用

```python
from src.ui_manager import UIManager

# 創建 UI 管理器實例
ui_manager = UIManager()

# 清理指定專案的掃描結果
project_names = {
    "airflow__CWE-327__CAL-ALL-6b42874e__M-call",
    "apache-airflow__CWE-89__CAL-ALL-abc123__M-sql"
}

success = ui_manager.clean_project_history(project_names)

if success:
    print("✅ 清理成功")
else:
    print("❌ 清理失敗")
```

## 清理統計資訊

清理過程會即時顯示詳細統計：

```
🧹 開始清理 2 個專案的執行記錄（不備份）...

📂 清理專案: airflow__CWE-327__CAL-ALL-6b42874e__M-call
  ✅ 已刪除Bandit原始掃描: OriginalScanResult/Bandit/CWE-327/airflow__CWE-327__CAL-ALL-6b42874e__M-call/ (15.32 KB)
  ✅ 已刪除Semgrep原始掃描: OriginalScanResult/Semgrep/CWE-327/airflow__CWE-327__CAL-ALL-6b42874e__M-call/ (18.45 KB)
  ✅ 已刪除執行結果目錄 (125.67 KB)
  ✅ 已刪除Bandit結果目錄: CWE-327/Bandit/airflow__CWE-327__CAL-ALL-6b42874e__M-call/ (2.15 KB)
  ✅ 已刪除Semgrep結果目錄: CWE-327/Semgrep/airflow__CWE-327__CAL-ALL-6b42874e__M-call/ (2.08 KB)

============================================================
✅ 清理完成！
============================================================
📊 清理統計:
  - 已清理項目: 10 個
  - 釋放空間: 0.16 MB
  - 清理專案: 2 個
============================================================
```

## 測試驗證

提供了測試腳本 `test_clean_scan_results.py` 用於驗證清理功能：

```bash
python test_clean_scan_results.py
```

測試步驟：
1. 檢查清理前的掃描結果狀態
2. 執行清理操作
3. 檢查清理後的掃描結果狀態
4. 驗證所有結果是否完全清理

## 安全措施

### ⚠️ 重要提醒

- **不可逆操作**: 清理操作會直接刪除檔案，**不會備份**
- **完整刪除**: 會刪除整個專案目錄，包括所有輪次的掃描結果
- **確認機制**: UI 會在執行前顯示警告並要求確認

### 建議使用場景

1. **重新掃描**: 需要對專案進行全新的掃描測試
2. **清理磁碟空間**: 清除不再需要的舊掃描結果
3. **測試驗證**: 確保測試環境乾淨
4. **問題排查**: 清除可能有問題的舊數據

### 不建議的場景

- 如果需要保留歷史掃描結果進行比對分析
- 如果掃描結果用於報告或審計追蹤
- 在生產環境中未經確認的批量清理

## 實作細節

### 核心方法

`src/ui_manager.py` 中的 `clean_project_history()` 方法：

```python
def clean_project_history(self, project_names: set) -> bool:
    """
    清理指定專案的執行記錄和結果（直接刪除，不備份）
    
    Args:
        project_names: 要清理的專案名稱集合
        
    Returns:
        bool: 清理是否成功
    """
```

### 清理邏輯

1. **OriginalScanResult**: 使用 `shutil.rmtree()` 刪除完整專案目錄
2. **CWE_Result**: 使用 `shutil.rmtree()` 刪除完整專案目錄
3. **ExecutionResult**: 
   - Success: 刪除專案目錄
   - AutomationLog/AutomationReport: 使用 glob 匹配並刪除檔案
4. **錯誤處理**: 每個刪除操作都有 try-except 保護，失敗不會中斷整體流程

### 目錄結構檢查

清理前會檢查目錄是否存在：

```python
if project_dir.exists():
    shutil.rmtree(project_dir)
```

### 統計追蹤

- 統計已清理項目數量
- 計算釋放的磁碟空間（bytes → KB → MB）
- 即時輸出清理進度

## 相關文件

- `src/ui_manager.py` - 清理功能實作
- `src/project_selector_ui.py` - 專案選擇 UI
- `test_clean_scan_results.py` - 測試腳本
- `docs/BANDIT_SEMGREP_COMPARISON.md` - 掃描器比較
- `docs/SEMGREP_IMPLEMENTATION_SUMMARY.md` - Semgrep 實作說明

## 版本歷史

- **v1.0** (2025-10-26): 初始實作
  - 支援清理 OriginalScanResult
  - 支援清理 CWE_Result
  - 支援清理 ExecutionResult
  - 支援 Bandit 和 Semgrep 雙掃描器結構
  - 完整的統計資訊和錯誤處理

## 常見問題

### Q1: 清理操作可以撤銷嗎？

**A**: 不可以。清理操作會直接刪除檔案，不會備份。請在執行前確認。

### Q2: 如果清理過程中出錯會怎樣？

**A**: 每個刪除操作都有獨立的錯誤處理，單個項目清理失敗不會影響其他項目。錯誤會被記錄並在控制台顯示。

### Q3: 清理後專案狀態是什麼？

**A**: 清理後專案狀態會被重置為 `pending`，可以重新執行掃描。

### Q4: 可以只清理特定掃描器的結果嗎？

**A**: 目前不支援。清理會同時移除 Bandit 和 Semgrep 的結果。如需此功能，請修改 `clean_project_history()` 方法。

### Q5: 清理會影響專案源碼嗎？

**A**: 不會。清理只會刪除掃描結果和執行記錄，不會觸碰 `projects/{專案名稱}/` 中的源碼。

## 總結

掃描結果清理功能提供了一個便捷、安全的方式來管理專案的掃描歷史。通過 UI 的確認機制和詳細的統計資訊，使用者可以清楚地了解清理操作的影響，並在必要時重新開始全新的掃描流程。
