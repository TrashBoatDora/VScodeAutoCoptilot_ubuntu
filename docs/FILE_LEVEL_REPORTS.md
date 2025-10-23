# 檔案級別掃描報告功能說明

## 功能概述

現在掃描結果會同時保存：
1. **完整專案報告** (`report.json`) - 包含專案中所有檔案的掃描結果
2. **個別檔案報告** (`{filename}_report.json`) - 每個檔案單獨的掃描結果

這樣可以更方便地追蹤和分析特定檔案的安全問題。

## 目錄結構

```
OriginalScanResult/
├── Bandit/
│   └── CWE-{cwe}/
│       └── {專案名稱}/
│           ├── report.json                    ← 完整專案報告
│           ├── file1.py_report.json          ← 個別檔案報告
│           └── file2.py_report.json          ← 個別檔案報告
└── Semgrep/
    └── CWE-{cwe}/
        └── {專案名稱}/
            ├── report.json                    ← 完整專案報告
            ├── file1.py_report.json          ← 個別檔案報告
            └── file2.py_report.json          ← 個別檔案報告
```

## 範例

### Bandit 檔案級別報告

檔案：`OriginalScanResult/Bandit/CWE-327/test_project/weak_crypto.py_report.json`

```json
{
  "errors": [],
  "results": [
    {
      "code": "10     \"\"\"使用 MD5（不安全）\"\"\"\n11     return hashlib.md5(data.encode()).hexdigest()\n12 \n",
      "col_offset": 11,
      "end_col_offset": 37,
      "filename": "test_project/weak_crypto.py",
      "issue_confidence": "HIGH",
      "issue_cwe": {
        "id": 327,
        "link": "https://cwe.mitre.org/data/definitions/327.html"
      },
      "issue_severity": "HIGH",
      "issue_text": "Use of weak MD5 hash for security. Consider usedforsecurity=False",
      "line_number": 11,
      "line_range": [11],
      "more_info": "https://bandit.readthedocs.io/en/1.8.6/plugins/b324_hashlib.html",
      "test_id": "B324",
      "test_name": "hashlib"
    }
  ],
  "metrics": {
    "total_issues": 2,
    "by_severity": {
      "HIGH": 2
    }
  }
}
```

### 檔案報告結構說明

每個檔案級別報告包含：

1. **errors** (陣列)
   - 該檔案的解析或掃描錯誤
   - 如果檔案有語法錯誤等問題會記錄在這裡

2. **results** (陣列)
   - 該檔案中發現的所有安全問題
   - 每個問題包含完整的詳細資訊

3. **metrics** (物件)
   - `total_issues`: 該檔案的問題總數
   - `by_severity`: 按嚴重性分類的統計
     - `HIGH`: 高嚴重性問題數量
     - `MEDIUM`: 中嚴重性問題數量
     - `LOW`: 低嚴重性問題數量

## 使用方式

### 方法 1: 使用測試腳本

```bash
# 啟動 conda 環境
conda activate copilot_py310

# 執行測試
python test_file_split.py
```

### 方法 2: 在程式碼中使用

```python
from pathlib import Path
from src.cwe_detector import CWEDetector

detector = CWEDetector()

# 掃描專案
vulnerabilities = detector.scan_project(
    project_path=Path('test_project'),
    cwes=['327'],
    scanners=None
)

# 檔案級別報告會自動生成在:
# OriginalScanResult/Bandit/CWE-327/test_project/*.py_report.json
# OriginalScanResult/Semgrep/CWE-327/test_project/*.py_report.json
```

## 測試結果

使用 `test_project` 進行測試：

```
總共 3 個檔案:
  ✓ more_weak_crypto.py_report.json (1,631 bytes)
    - 結果: 2 個問題
    - 統計: 2 個問題
    - 嚴重性: {'HIGH': 2}
    
  ✓ report.json (4,077 bytes)
    - 結果: 4 個問題
    
  ✓ weak_crypto.py_report.json (1,556 bytes)
    - 結果: 2 個問題
    - 統計: 2 個問題
    - 嚴重性: {'HIGH': 2}
```

## 優勢

1. **易於追蹤**：快速定位特定檔案的安全問題
2. **便於對照**：可以直接對應原始碼檔案查看問題
3. **統計清晰**：每個檔案有獨立的問題統計
4. **完整保留**：同時保留完整專案報告和檔案級別報告
5. **自動生成**：掃描時自動分割，無需額外操作

## 實作細節

- **Bandit 分割**: `src/cwe_detector.py` 中的 `_split_bandit_results_by_file()` 方法
- **Semgrep 分割**: `src/cwe_detector.py` 中的 `_split_semgrep_results_by_file()` 方法
- **自動調用**: 在 `_scan_with_bandit()` 和 `_scan_with_semgrep()` 中自動執行分割

## 注意事項

1. 如果某個檔案沒有發現問題，則不會生成該檔案的報告
2. 檔案名稱使用檔案基本名稱（不含路徑）+ `_report.json`
3. 分割功能不影響原有的完整報告生成
4. 錯誤資訊會被正確分配到對應的檔案報告中
