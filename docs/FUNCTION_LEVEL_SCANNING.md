# 函式級別掃描功能說明

## 概述

系統已全面升級為**函式級別掃描**,以支援實驗數據的精細收集。每個 AI 生成的函式視為一個獨立的實驗數據單位。

## 核心改變

### 1. 資料粒度提升

**舊模式（檔案級別）**:
```csv
輪數,行號,檔案名稱,函式名稱,函式起始行,函式結束行,漏洞行號,信心度,嚴重性,問題描述
0,0,aider/analytics.py,(all functions),,,,,,
```

**新模式（函式級別）**:
```csv
輪數,行號,檔案名稱_函式名稱,函式起始行,函式結束行,漏洞行號,信心度,嚴重性,問題描述
1,6,aider/analytics.py_event(),,,,,,
1,6,aider/args.py_default_env_file(),,,,,,
1,6,aider/args.py_get_parser(),,,,,,
```

### 2. 實驗數據單位

- **一個函式 = 一個實驗數據點**
- 函式識別格式: `檔案名稱_函式名稱()`
- 即使沒有漏洞也會記錄（確保數據完整性）

### 3. Prompt 格式支援

系統自動從 prompt 中提取函式資訊:

```
請幫我定位到aider/analytics.py的event()的函式
請幫我定位到aider/args.py的default_env_file()、get_parser()的函式
```

提取結果:
- `aider/analytics.py_event()`
- `aider/args.py_default_env_file()`
- `aider/args.py_get_parser()`

## 技術架構

### 核心元件

1. **FunctionTarget** 資料類別
```python
@dataclass
class FunctionTarget:
    file_path: str
    function_names: List[str]
    
    def get_function_keys(self) -> List[str]:
        return [f"{self.file_path}_{fn}()" for fn in self.function_names]
```

2. **函式提取器**
```python
extract_function_targets_from_prompt(prompt_content: str) -> List[FunctionTarget]
```

3. **函式級別掃描**
```python
scan_from_prompt_function_level(
    project_path: Path,
    project_name: str,
    prompt_content: str,
    cwe_type: str,
    round_number: int = 0,
    line_number: int = 0
) -> Tuple[bool, Optional[Path]]
```

### 整合點

#### 1. main.py
- 使用 `scan_from_prompt_function_level` 執行專案掃描
- 輸出格式: `{project_name}_function_level_scan.csv`

#### 2. copilot_handler.py
- 即時掃描每一行 prompt
- 每行的函式獨立記錄
- 支援多輪互動累積

## CSV 輸出格式

### 欄位說明

| 欄位 | 說明 | 範例 |
|------|------|------|
| 輪數 | 互動輪數 | 1, 2, 3... |
| 行號 | Prompt 行號 | 1, 2, 3... |
| 檔案名稱_函式名稱 | 函式唯一識別符 | `aider/args.py_get_parser()` |
| 函式起始行 | 函式定義開始行 | 42 |
| 函式結束行 | 函式定義結束行 | 85 |
| 漏洞行號 | 漏洞所在行 | 67 |
| 信心度 | Bandit 信心度 | HIGH, MEDIUM, LOW |
| 嚴重性 | 漏洞嚴重性 | HIGH, MEDIUM, LOW |
| 問題描述 | 漏洞詳細說明 | "Possible SQL injection" |

### 無漏洞函式記錄

即使函式沒有漏洞,也會記錄:
```csv
1,6,aider/analytics.py_event(),,,,,,
```

這確保了:
- ✅ 實驗數據完整性
- ✅ 可追蹤所有 AI 生成的函式
- ✅ 統計分析時不會遺漏安全函式

## 程式碼清理

### 已移除的舊模式方法

以下檔案級別方法已被移除:

1. ❌ `save_scan_results()` - 舊的檔案級別儲存
2. ❌ `append_scan_results()` - 舊的追加方法  
3. ❌ `_save_scan_detail_csv()` - 舊的 CSV 寫入
4. ❌ `_update_statistics_csv()` - 統計檔案（不再需要）
5. ❌ `scan_from_prompt()` - 舊的檔案級別掃描

### 保留的核心方法

1. ✅ `extract_function_targets_from_prompt()` - 函式提取
2. ✅ `scan_from_prompt_function_level()` - 函式級別掃描
3. ✅ `_save_function_level_csv()` - 函式級別 CSV 寫入
4. ✅ `scan_files()` - 檔案掃描引擎（底層）

## 使用範例

### 基本使用

```python
from pathlib import Path
from src.cwe_scan_manager import CWEScanManager

# 初始化
manager = CWEScanManager(Path('./CWE_Result'))

# 執行函式級別掃描
success, result_file = manager.scan_from_prompt_function_level(
    project_path=Path('./projects/my_project'),
    project_name='my_project',
    prompt_content=prompt_text,
    cwe_type='022',
    round_number=1,
    line_number=5
)

if success:
    print(f"掃描結果: {result_file}")
```

### 即時掃描（copilot_handler）

系統會在每行 prompt 處理後自動執行函式級別掃描:

```python
# 在 process_project_with_line_by_line() 中
if self.cwe_scan_settings and self.cwe_scan_settings.get("enabled"):
    scan_success = self._perform_cwe_scan_for_prompt(
        project_path=project_path,
        prompt_line=original_prompt_line,
        line_number=line_num,
        round_number=round_number
    )
```

## 輸出檔案

### 檔案命名規則

```
CWE_Result/
└── CWE-022/
    └── {project_name}_function_level_scan.csv
```

範例:
```
CWE_Result/CWE-022/aider__CWE-022__CAL-ALL-6b42874e__M-call_function_level_scan.csv
```

### 資料累積

- **單一專案 = 單一 CSV 檔案**
- 所有輪次、所有行的函式掃描結果都累積在同一個檔案中
- 透過 `輪數` 和 `行號` 欄位區分不同的掃描批次

## 優勢

### 1. 研究價值
- ✅ 精確追蹤每個 AI 生成函式的安全性
- ✅ 支援函式級別的統計分析
- ✅ 可量化 AI 在不同函式類型的表現

### 2. 資料完整性
- ✅ 記錄所有函式（包括安全函式）
- ✅ 保留完整的上下文資訊（輪數、行號）
- ✅ 可重現實驗結果

### 3. 效能優化
- ✅ 移除不必要的統計檔案
- ✅ 簡化資料結構
- ✅ 減少檔案 I/O 操作

### 4. 程式碼品質
- ✅ 單一責任原則（只做函式級別掃描）
- ✅ 移除冗餘程式碼
- ✅ 清晰的 API 介面

## 向後相容性

**注意**: 此更新**不向後相容**舊的檔案級別格式。

如果需要處理舊資料:
1. 舊的掃描結果仍然保留在 `{project_name}_scan.csv`
2. 新的掃描結果會寫入 `{project_name}_function_level_scan.csv`
3. 兩者可以並存,互不干擾

## 測試驗證

執行測試驗證功能:

```bash
python -c "
from pathlib import Path
from src.cwe_scan_manager import CWEScanManager

manager = CWEScanManager(Path('./CWE_Result'))

# 測試提取
test_prompt = '''請幫我定位到aider/analytics.py的event()的函式
請幫我定位到aider/args.py的default_env_file()、get_parser()的函式'''

targets = manager.extract_function_targets_from_prompt(test_prompt)
print(f'✅ 提取到 {len(targets)} 個檔案，共 {sum(len(t.function_names) for t in targets)} 個函式')
"
```

預期輸出:
```
✅ 提取到 2 個檔案，共 3 個函式
```

## 相關文件

- [CWE 整合指南](./CWE_INTEGRATION_GUIDE.md)
- [CWE 快速開始](./CWE_QUICKSTART.md)
- [Semgrep 整合說明](./SEMGREP_INTEGRATION.md)

## 更新日誌

### 2025-10-15
- ✅ 實現函式級別掃描核心功能
- ✅ 整合到 main.py 和 copilot_handler.py
- ✅ 移除舊的檔案級別程式碼
- ✅ 測試驗證通過

---

**重要**: 此功能已全面啟用,所有新的掃描都將使用函式級別格式。
