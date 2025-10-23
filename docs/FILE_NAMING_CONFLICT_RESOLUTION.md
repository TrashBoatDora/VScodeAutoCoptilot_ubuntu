# 檔案級別報告功能更新 - 解決檔案名稱衝突

## 更新日期
2025-10-23

## 問題描述

在之前的實現中，檔案級別報告使用簡單的檔案名稱（如 `messages.py_report.json`），這會導致以下問題：

1. **檔案名稱衝突**：不同目錄下的同名檔案會互相覆蓋
   - `lib/itchat/components/messages.py` → `messages.py_report.json`
   - `lib/itchat/async_components/messages.py` → `messages.py_report.json` ⚠️ 覆蓋！

2. **無法區分來源**：從檔案名稱無法得知原始檔案的位置

## 解決方案

### 新的命名規則

使用 **上一層目錄 + 檔案名** 的格式，並用雙底線 `__` 連接：

```
{parent_dir}__{filename}_report.json
```

### 範例對照

| 原始檔案路徑 | 舊命名 | 新命名 |
|------------|--------|--------|
| `lib/itchat/components/messages.py` | `messages.py_report.json` | `components__messages.py_report.json` |
| `lib/itchat/async_components/messages.py` | `messages.py_report.json` | `async_components__messages.py_report.json` |
| `translate/baidu/baidu_translate.py` | `baidu_translate.py_report.json` | `baidu__baidu_translate.py_report.json` |
| `voice/ali/ali_api.py` | `ali_api.py_report.json` | `ali__ali_api.py_report.json` |

## 實際測試結果

### 測試專案
`chatgpt-on-wechat__CWE-327__CAL-ALL-6b42874e__M-call`

### 掃描結果

#### Bandit 結果目錄
```
OriginalScanResult/Bandit/CWE-327/chatgpt-on-wechat__CWE-327__CAL-ALL-6b42874e__M-call/
├── report.json                                  ← 完整專案報告
├── async_components__messages.py_report.json    ← lib/itchat/async_components/messages.py
├── components__messages.py_report.json          ← lib/itchat/components/messages.py
└── baidu__baidu_translate.py_report.json        ← translate/baidu/baidu_translate.py
```

#### 檔案內容驗證

**async_components__messages.py_report.json**
```json
{
  "original_path": "projects/.../lib/itchat/async_components/messages.py",
  "metrics": {
    "total_issues": 1
  },
  "results": [
    {
      "filename": "projects/.../lib/itchat/async_components/messages.py",
      "line_number": 317
    }
  ]
}
```

**components__messages.py_report.json**
```json
{
  "original_path": "projects/.../lib/itchat/components/messages.py",
  "metrics": {
    "total_issues": 1
  },
  "results": [
    {
      "filename": "projects/.../lib/itchat/components/messages.py",
      "line_number": 318
    }
  ]
}
```

✅ **兩個檔案成功分離，沒有覆蓋問題！**

## 程式碼變更

### 修改檔案
- `src/cwe_detector.py`
  - `_split_bandit_results_by_file()` 方法
  - `_split_semgrep_results_by_file()` 方法

### 核心邏輯

```python
# 提取檔案的相對路徑（包含上一層目錄）
filepath = Path(filename)
parts = filepath.parts

# 使用最後兩個部分（目錄/檔案名）來避免衝突
if len(parts) >= 2:
    file_key = f"{parts[-2]}/{parts[-1]}"
else:
    file_key = filepath.name

# 轉換檔案名稱：components/messages.py -> components__messages.py_report.json
safe_filename = file_key.replace('/', '__') + "_report.json"
```

### 新增欄位

每個檔案報告現在包含 `original_path` 欄位，記錄完整的原始路徑：

```json
{
  "original_path": "projects/.../lib/itchat/async_components/messages.py",
  "errors": [],
  "results": [...],
  "metrics": {...}
}
```

## 優勢

1. ✅ **避免檔案覆蓋**：不同目錄的同名檔案有不同的報告名稱
2. ✅ **易於識別**：從檔案名稱可以看出原始檔案的上一層目錄
3. ✅ **保留完整資訊**：`original_path` 欄位記錄完整路徑
4. ✅ **向後兼容**：對於單層目錄結構，仍使用簡單檔案名
5. ✅ **自動生成**：掃描時自動分割，無需額外操作

## 使用方式

### 執行掃描

```bash
# 啟動環境
source activate_env.sh

# 執行專案掃描
python main.py
```

### 查找特定檔案的報告

```bash
# 查找 messages.py 的所有報告
find OriginalScanResult -name "*messages.py_report.json"

# 輸出範例:
# OriginalScanResult/Bandit/CWE-327/project/async_components__messages.py_report.json
# OriginalScanResult/Bandit/CWE-327/project/components__messages.py_report.json
```

### 程式化讀取

```python
from pathlib import Path
import json

# 讀取特定檔案的報告
report_file = Path("OriginalScanResult/Bandit/CWE-327/project/components__messages.py_report.json")
with open(report_file) as f:
    data = json.load(f)

print(f"原始路徑: {data['original_path']}")
print(f"問題數量: {data['metrics']['total_issues']}")
```

## 測試驗證

### 測試腳本
`test_file_naming.py` - 驗證新的檔案命名邏輯

### 測試案例

1. ✅ 同名檔案不同目錄 - 成功分離
2. ✅ 原始路徑正確記錄 - 通過
3. ✅ 問題數量正確統計 - 通過
4. ✅ 行號資訊正確對應 - 通過

## 相關文件

- [檔案級別報告功能說明](FILE_LEVEL_REPORTS.md)
- [目錄結構文檔](DIRECTORY_STRUCTURE.md)
- [CWE 掃描實作總結](CWE_SCAN_IMPLEMENTATION_SUMMARY.md)

## 未來改進

1. 可考慮使用更多層級的目錄資訊（如需要）
2. 可新增配置選項讓使用者自訂命名規則
3. 可新增檔案索引功能，快速查找特定檔案的報告
