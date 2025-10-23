# 單檔掃描檔案命名改進

## 更新日期
2025-10-23

## 問題描述

在之前的實現中，單檔掃描（`scan_single_file`）使用簡單的檔案名稱儲存結果：

```
OriginalScanResult/Bandit/single_file/CWE-327/
├── messages.py_report.json  ← 第一個 messages.py
└── messages.py_report.json  ← 第二個 messages.py (被覆蓋！)
```

這導致不同目錄下的同名檔案互相覆蓋，無法保留所有掃描結果。

## 解決方案

### 新的命名規則

與專案掃描保持一致，使用 **上一層目錄 + 檔案名** 的格式：

```
{parent_dir}__{filename}_report.json
```

### 範例對照

| 原始檔案路徑 | 舊命名 | 新命名 |
|------------|--------|--------|
| `lib/itchat/components/messages.py` | `messages.py_report.json` | `components__messages.py_report.json` |
| `lib/itchat/async_components/messages.py` | `messages.py_report.json` | `async_components__messages.py_report.json` |

## 修改內容

### 1. Bandit 單檔掃描

**檔案**: `src/cwe_detector.py`  
**方法**: `scan_single_file()`

```python
# 舊程式碼
output_file = output_dir / f"{file_path.name}_report.json"

# 新程式碼
# 使用目錄前綴來命名，避免不同目錄下的同名檔案衝突
file_parts = file_path.parts
if len(file_parts) >= 2:
    safe_filename = f"{file_parts[-2]}__{file_parts[-1]}_report.json"
else:
    safe_filename = f"{file_path.name}_report.json"

output_file = output_dir / safe_filename
```

### 2. Semgrep 單檔掃描

**檔案**: `src/cwe_detector.py`  
**方法**: `scan_single_file()`

之前 Semgrep 單檔掃描直接調用 `_scan_with_semgrep()`，這會導致命名問題。

**修改後**：在 `scan_single_file()` 中為 Semgrep 添加專門的處理邏輯：

```python
# Semgrep 單檔掃描也需要使用目錄前綴命名
rule_patterns = self.SEMGREP_BY_CWE.get(cwe)
if rule_patterns:
    output_dir = self.semgrep_original_dir / "single_file" / f"CWE-{cwe}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用目錄前綴來命名
    file_parts = file_path.parts
    if len(file_parts) >= 2:
        safe_filename = f"{file_parts[-2]}__{file_parts[-1]}_report.json"
    else:
        safe_filename = f"{file_path.name}_report.json"
    
    output_file = output_dir / safe_filename
    
    # ... 構建並執行 Semgrep 命令 ...
```

## 測試驗證

### 測試案例

掃描兩個不同目錄下的 `messages.py`：

1. `lib/itchat/components/messages.py`
2. `lib/itchat/async_components/messages.py`

### 測試結果

#### Bandit 結果
```
OriginalScanResult/Bandit/single_file/CWE-327/
├── components__messages.py_report.json          ← components/messages.py
└── async_components__messages.py_report.json    ← async_components/messages.py
```

#### Semgrep 結果
```
OriginalScanResult/Semgrep/single_file/CWE-327/
├── components__messages.py_report.json          ← components/messages.py
└── async_components__messages.py_report.json    ← async_components/messages.py
```

### 檔案內容驗證

**async_components__messages.py_report.json** (Bandit)
```json
{
  "results": [
    {
      "filename": "...async_components/messages.py",
      "line_number": 307,
      "issue_text": "Use of weak MD5 hash for security..."
    }
  ]
}
```

**async_components__messages.py_report.json** (Semgrep)
```json
{
  "results": [
    {
      "path": "...async_components/messages.py",
      "check_id": "python.lang.security.insecure-hash-algorithms-md5..."
    }
  ]
}
```

✅ **兩個檔案成功分離，沒有覆蓋問題！**

## 完整目錄結構

```
OriginalScanResult/
├── Bandit/
│   ├── single_file/
│   │   └── CWE-327/
│   │       ├── components__messages.py_report.json
│   │       └── async_components__messages.py_report.json
│   └── CWE-327/
│       └── {project_name}/
│           ├── report.json
│           ├── components__messages.py_report.json
│           └── async_components__messages.py_report.json
└── Semgrep/
    ├── single_file/
    │   └── CWE-327/
    │       ├── components__messages.py_report.json
    │       └── async_components__messages.py_report.json
    └── CWE-327/
        └── {project_name}/
            ├── report.json
            ├── components__messages.py_report.json
            └── async_components__messages.py_report.json
```

## 統一性

現在所有掃描模式（專案掃描和單檔掃描）都使用相同的命名規則：

| 掃描模式 | 儲存位置 | 命名格式 |
|---------|---------|---------|
| 專案掃描 | `OriginalScanResult/{Scanner}/CWE-{cwe}/{project}/` | `{dir}__{file}_report.json` |
| 單檔掃描 | `OriginalScanResult/{Scanner}/single_file/CWE-{cwe}/` | `{dir}__{file}_report.json` |

## 優勢

1. ✅ **避免覆蓋**：不同目錄的同名檔案有獨立的報告
2. ✅ **命名一致**：單檔掃描和專案掃描使用相同規則
3. ✅ **易於識別**：從檔案名稱可以看出原始檔案的上層目錄
4. ✅ **格式統一**：Bandit 和 Semgrep 使用相同格式
5. ✅ **自動化**：掃描時自動應用命名規則

## 使用方式

### 執行單檔掃描

```python
from pathlib import Path
from src.cwe_detector import CWEDetector

detector = CWEDetector()

# 掃描單一檔案
file_path = Path("lib/itchat/components/messages.py")
vulnerabilities = detector.scan_single_file(file_path, "327")
```

### 查看結果

```bash
# 查看單檔掃描結果
ls -lh OriginalScanResult/Bandit/single_file/CWE-327/
ls -lh OriginalScanResult/Semgrep/single_file/CWE-327/
```

## 相關文檔

- [檔案級別報告功能說明](FILE_LEVEL_REPORTS.md)
- [檔案名稱衝突解決](FILE_NAMING_CONFLICT_RESOLUTION.md)
- [Semgrep 檔案級別報告](SEMGREP_FILE_LEVEL_REPORTS.md)

## 總結

✅ 單檔掃描檔案命名問題已解決  
✅ Bandit 和 Semgrep 都已更新  
✅ 與專案掃描保持一致的命名規則  
✅ 成功避免檔案名稱衝突  
✅ 所有功能已通過測試驗證
