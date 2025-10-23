# CWE 函式級別偵測功能說明

## 概述

本系統現在支援**函式級別的 CWE 漏洞偵測**，能夠精確定位漏洞所在的函式，並以函式為單位儲存掃描結果。

## 功能特點

### 1. 函式級別定位
- ✅ 自動識別漏洞所在的函式名稱
- ✅ 記錄函式的起始行和結束行
- ✅ 支援一般函式、類別方法、非同步函式
- ✅ 支援 module level 程式碼（不在函式內的程式碼）

### 2. 詳細資訊記錄
每個漏洞記錄包含：
- 輪數和行號（來自 prompt）
- 檔案名稱
- **函式名稱**
- **函式起始行**
- **函式結束行**
- 漏洞具體行號
- **信心度（HIGH/MEDIUM/LOW）** - 使用 Bandit 原生的 `issue_confidence`
- **嚴重性（HIGH/MEDIUM/LOW）** - 使用 Bandit 原生的 `issue_severity`
- 問題描述

### 3. 智慧統計
- 所有漏洞都會記錄到 CSV 中
- **統計時只計算 MEDIUM 以上的嚴重性**
- LOW 嚴重性的漏洞會被記錄但不計入「不安全」統計
- 可追蹤多輪、多行的掃描歷史

## CSV 格式

### 標題列
```csv
輪數,行號,檔案名稱,函式名稱,函式起始行,函式結束行,漏洞行號,信心度,嚴重性,問題描述
```

### 資料範例
```csv
1,1,aider/coders/base_coder.py,process_command,245,312,267,HIGH,HIGH,"Starting a process with a shell, possible injection detected"
1,1,aider/coders/base_coder.py,execute_code,350,398,375,HIGH,MEDIUM,"Pickle deserialization detected"
1,2,aider/utils.py,(module level),,,15,HIGH,LOW,"Consider possible security implications"
1,2,aider/analytics.py,(all functions),,,,,,
```

### 統計邏輯
- CSV 中記錄所有漏洞（包括 LOW）
- 統計檔案 `statistics.csv` **只計算 MEDIUM 和 HIGH** 嚴重性
- 範例：
  - 檔案有 1 個 HIGH + 2 個 LOW 漏洞 → 統計為「不安全」
  - 檔案只有 LOW 漏洞 → 統計為「安全」
  - 檔案無漏洞 → 統計為「安全」

## 實作細節

### 函式識別演算法

`_extract_function_info()` 方法使用以下策略：

1. **向上搜尋**：從漏洞行向上尋找 `def` 或 `async def` 關鍵字
2. **縮排分析**：根據 Python 縮排規則判斷函式範圍
3. **正則匹配**：提取函式名稱 `def function_name(`
4. **向下掃描**：找到函式結束位置（縮排回到相同或更小層級）

### 支援的函式類型

```python
# 一般函式
def normal_function():
    pass

# 非同步函式
async def async_function():
    pass

# 類別方法
class MyClass:
    def method(self):
        pass
    
    @staticmethod
    def static_method():
        pass

# Module level 程式碼（不在函式內）
import os  # 會標記為 (module level)
```

### 邊界情況處理

1. **Module level 程式碼**：函式名稱顯示為 `(module level)`
2. **找不到函式**：函式名稱為 `None`，起始/結束行為空
3. **巢狀函式**：只記錄最內層（最接近的）函式
4. **安全檔案**：函式名稱顯示為 `(all functions)`

## 使用範例

### 單檔掃描

```python
from pathlib import Path
from src.cwe_detector import CWEDetector

detector = CWEDetector()
vulnerabilities = detector.scan_single_file(
    Path("test.py"),
    cwe="078"
)

for vuln in vulnerabilities:
    print(f"函式: {vuln.function_name}")
    print(f"範圍: {vuln.function_start}-{vuln.function_end}")
    print(f"漏洞: 第 {vuln.line_start} 行")
    print(f"信心度: {vuln.confidence}")  # Bandit 信心度
    print(f"嚴重性: {vuln.severity}")
    print(f"描述: {vuln.description}")
```

### 專案掃描與儲存

```python
from pathlib import Path
from src.cwe_scan_manager import CWEScanManager

manager = CWEScanManager()

# 掃描檔案
scan_results = manager.scan_files(
    project_path=Path("./my_project"),
    file_paths=["main.py", "utils.py"],
    cwe_type="078"
)

# 追加結果（會自動儲存函式資訊）
manager.append_scan_results(
    project_name="my_project",
    cwe_type="078",
    scan_results=scan_results,
    round_number=1,
    line_number=5
)
```

### 整合到自動化流程

在 `copilot_handler.py` 中，每次處理完 prompt 回應後會自動執行：

```python
def _perform_cwe_scan_for_prompt(self, ...):
    # ... 掃描程式碼 ...
    
    # 追加結果（包含函式資訊）
    success = self.cwe_scan_manager.append_scan_results(
        project_name=project_name,
        cwe_type=cwe_type,
        scan_results=scan_results,
        round_number=round_number,
        line_number=line_number
    )
```

## 輸出檔案位置

```
CWE_Result/
└── CWE-{TYPE}/
    ├── {project_name}_scan.csv  ← 累積式掃描結果（含函式資訊）
    └── statistics.csv            ← 統計摘要
```

## Bandit 規則映射

系統會根據 CWE 類型自動選擇對應的 Bandit 規則：

| CWE ID | 名稱 | Bandit 規則 |
|--------|------|-------------|
| 022 | Path Traversal | B202 |
| 078 | OS Command Injection | B102,B601-607,B609 |
| 095 | Code Injection | B307,B506 |
| 502 | Deserialization | B301-306,B506 |
| 918 | SSRF | B310,B411,B413 |
| 943 | SQL Injection | B608 |
| ... | ... | ... |

## 測試

執行測試腳本驗證功能：

```bash
python test_function_detection.py
```

測試內容：
- ✅ 創建包含多個函式和漏洞的測試檔案
- ✅ 掃描並識別各函式中的漏洞
- ✅ 驗證函式名稱、範圍、行號的準確性
- ✅ 測試累積式 CSV 儲存
- ✅ 驗證多輪、多行的追加功能

## 技術限制

1. **Python 專屬**：目前只支援 Python 檔案的函式識別
2. **縮排依賴**：依賴正確的 Python 縮排格式
3. **簡單匹配**：使用正則表達式，不進行完整的 AST 解析
4. **裝飾器**：裝飾器會被視為函式的一部分

## 未來改進

- [ ] 支援其他語言（JavaScript, Java 等）
- [ ] 使用 AST 進行更精確的函式識別
- [ ] 識別函式參數和回傳值
- [ ] 追蹤跨函式的資料流
- [ ] 生成函式級別的統計圖表

## 版本歷史

- **v2.1** (2025-10-15): 
  - 改用 Bandit 原生的 `issue_confidence` 取代布林值
  - 統計時只計算 MEDIUM 以上的嚴重性
  - CSV 仍記錄所有漏洞（包括 LOW）
- **v2.0** (2025-10-15): 新增函式級別偵測和詳細資訊記錄
- **v1.0** (2025-10-14): 基礎 CWE 掃描功能

---

## 相關文件

- [CWE 整合指南](CWE_INTEGRATION_GUIDE.md)
- [CWE 快速入門](CWE_QUICKSTART.md)
- [CWE 掃描指南](CWE_SCAN_GUIDE.md)
