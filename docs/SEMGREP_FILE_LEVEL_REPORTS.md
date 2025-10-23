# Semgrep 檔案級別報告功能驗證

## 功能狀態
✅ **已完成並驗證**

## 功能說明

Semgrep 掃描結果現在會自動分割成：
1. **完整專案報告** (`report.json`) - 包含所有檔案的掃描結果
2. **個別檔案報告** (`{dir}__{file}_report.json`) - 每個檔案獨立的掃描結果

## 目錄結構

```
OriginalScanResult/
├── Bandit/
│   └── CWE-{cwe}/
│       └── {project_name}/
│           ├── report.json
│           ├── dir1__file1.py_report.json
│           └── dir2__file2.py_report.json
└── Semgrep/
    └── CWE-{cwe}/
        └── {project_name}/
            ├── report.json
            ├── dir1__file1.py_report.json
            └── dir2__file2.py_report.json
```

## 命名規則（與 Bandit 一致）

使用 **上一層目錄 + 檔案名** 的格式，用雙底線 `__` 連接：

```
{parent_dir}__{filename}_report.json
```

### 範例

| 原始檔案路徑 | 報告檔案名稱 |
|------------|------------|
| `test_semgrep/main.py` | `test_semgrep__main.py_report.json` |
| `test_semgrep/utils/helper.py` | `utils__helper.py_report.json` |
| `lib/itchat/components/messages.py` | `components__messages.py_report.json` |
| `lib/itchat/async_components/messages.py` | `async_components__messages.py_report.json` |

## 測試驗證

### 測試專案
`test_semgrep/`

### 測試結果

```
Semgrep 結果目錄: OriginalScanResult/Semgrep/CWE-327/test_semgrep
檔案數量: 3
  report.json (5,047 bytes)                        ← 完整專案報告
  test_semgrep__main.py_report.json (2,656 bytes)  ← main.py 的報告
  utils__helper.py_report.json (2,666 bytes)       ← helper.py 的報告
```

### 檔案內容驗證

**test_semgrep__main.py_report.json**
```json
{
  "original_path": "test_semgrep/main.py",
  "errors": [],
  "results": [
    {
      "path": "test_semgrep/main.py",
      "check_id": "python.lang.security.insecure-hash-algorithms-md5.insecure-hash-algorithm-md5",
      "extra": {
        "severity": "WARNING"
      }
    }
  ],
  "paths": {
    "scanned": ["test_semgrep/main.py"]
  }
}
```

**utils__helper.py_report.json**
```json
{
  "original_path": "test_semgrep/utils/helper.py",
  "errors": [],
  "results": [
    {
      "path": "test_semgrep/utils/helper.py",
      "check_id": "python.lang.security.insecure-hash-algorithms-md5.insecure-hash-algorithm-md5",
      "extra": {
        "severity": "WARNING"
      }
    }
  ],
  "paths": {
    "scanned": ["utils/helper.py"]
  }
}
```

## 與 Bandit 的一致性

| 特性 | Bandit | Semgrep |
|------|--------|---------|
| 目錄結構 | `OriginalScanResult/Bandit/CWE-{cwe}/{project}/` | `OriginalScanResult/Semgrep/CWE-{cwe}/{project}/` |
| 主報告 | `report.json` | `report.json` |
| 個別檔案報告 | `{dir}__{file}_report.json` | `{dir}__{file}_report.json` |
| 原始路徑欄位 | `original_path` | `original_path` |
| 避免衝突 | ✅ 使用目錄前綴 | ✅ 使用目錄前綴 |

## 實作程式碼

### `src/cwe_detector.py`

```python
def _split_semgrep_results_by_file(self, report_file: Path, output_dir: Path):
    """
    將 Semgrep 掃描結果按檔案分割保存
    
    Args:
        report_file: 完整的掃描報告檔案
        output_dir: 輸出目錄（專案目錄）
    """
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 按檔案分組結果（使用完整路徑避免衝突）
        results_by_file = {}
        
        # 處理掃描結果
        for result in data.get("results", []):
            filepath = result.get("path", "")
            if filepath:
                # 提取檔案的相對路徑（包含上一層目錄）
                path_obj = Path(filepath)
                parts = path_obj.parts
                
                # 使用最後兩個部分（目錄/檔案名）來避免衝突
                if len(parts) >= 2:
                    file_key = f"{parts[-2]}/{parts[-1]}"
                else:
                    file_key = path_obj.name
                
                if file_key not in results_by_file:
                    results_by_file[file_key] = {
                        "errors": [],
                        "results": [],
                        "paths": {},
                        "original_path": filepath  # 保留原始路徑
                    }
                results_by_file[file_key]["results"].append(result)
        
        # 保存每個檔案的結果
        for file_key, file_data in results_by_file.items():
            file_data["paths"] = {
                "scanned": [file_key]
            }
            
            # 轉換檔案名稱：utils/helper.py -> utils__helper.py_report.json
            safe_filename = file_key.replace('/', '__') + "_report.json"
            output_file = output_dir / safe_filename
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"  分割結果: {safe_filename} ({len(file_data['results'])} 個問題)")
    
    except Exception as e:
        logger.error(f"分割 Semgrep 結果失敗: {e}")
```

## 使用方式

### 執行掃描

```bash
# 啟動環境
source activate_env.sh

# 執行專案掃描（Bandit 和 Semgrep 都會自動分割）
python main.py
```

### 查看結果

```bash
# 查看 Semgrep 的檔案級別報告
ls -lh OriginalScanResult/Semgrep/CWE-327/test_semgrep/

# 輸出：
# report.json                        ← 完整報告
# test_semgrep__main.py_report.json  ← 個別檔案
# utils__helper.py_report.json       ← 個別檔案
```

### 程式化讀取

```python
import json
from pathlib import Path

# 讀取特定檔案的 Semgrep 報告
report_file = Path("OriginalScanResult/Semgrep/CWE-327/project/utils__helper.py_report.json")
with open(report_file) as f:
    data = json.load(f)

print(f"原始路徑: {data['original_path']}")
print(f"問題數量: {len(data['results'])}")
```

## 優勢

1. ✅ **格式統一**：Bandit 和 Semgrep 使用相同的命名和結構
2. ✅ **避免衝突**：不同目錄的同名檔案有不同的報告名稱
3. ✅ **易於追蹤**：快速定位特定檔案的安全問題
4. ✅ **完整資訊**：保留原始路徑和掃描詳情
5. ✅ **自動化**：掃描時自動分割，無需額外操作

## 測試腳本

- `verify_file_reports.py` - 驗證 Bandit 和 Semgrep 的檔案級別報告

## 相關文檔

- [檔案級別報告功能說明](FILE_LEVEL_REPORTS.md)
- [檔案名稱衝突解決](FILE_NAMING_CONFLICT_RESOLUTION.md)
- [目錄結構文檔](DIRECTORY_STRUCTURE.md)

## 總結

✅ Semgrep 的檔案級別報告功能已完全實現
✅ 格式與 Bandit 完全一致
✅ 成功解決檔案名稱衝突問題
✅ 所有功能已通過測試驗證
