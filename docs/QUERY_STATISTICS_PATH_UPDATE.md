# Query Statistics 路徑結構更新

## 更新日期
2025-10-27

## 變更說明

### 舊的路徑結構
```
CWE_Result/
└── CWE-327/
    ├── Bandit/
    │   └── project_name/
    │       ├── 第1輪/
    │       └── 第2輪/
    └── Semgrep/
        └── project_name/
            ├── 第1輪/
            ├── 第2輪/
            └── query_statistics.csv  ← 在專案資料夾內
```

### 新的路徑結構
```
CWE_Result/
└── CWE-327/
    ├── Bandit/
    │   └── project_name/
    │       ├── 第1輪/
    │       └── 第2輪/
    ├── Semgrep/
    │   └── project_name/
    │       ├── 第1輪/
    │       └── 第2輪/
    └── query_statistics/  ← 新資料夾，與 Bandit、Semgrep 同層
        ├── project1.csv
        ├── project2.csv
        └── project3.csv
```

## 變更原因

1. **集中管理**：所有專案的統計資料集中在一個資料夾
2. **易於比較**：方便對比不同專案的攻擊難度
3. **清晰結構**：與掃描器結果分離，結構更清晰
4. **檔名明確**：使用專案名稱作為檔名，一目了然

## 檔名格式

**格式：** `{project_name}.csv`

**範例：**
- `aider__CWE-327__CAL-ALL-6b42874e__M-call.csv`
- `airflow__CWE-327__CAL-ALL-6b42874e__M-call.csv`
- `test_project.csv`

## 實際路徑範例

### 完整路徑
```
/home/ai/AISecurityProject/VSCode_CopilotAutoInteraction/CWE_Result/CWE-327/query_statistics/aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
```

### 相對路徑（從專案根目錄）
```
CWE_Result/CWE-327/query_statistics/aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
```

## 程式碼變更

### `src/query_statistics.py`

```python
# 舊版
self.project_result_path = (
    self.base_result_path / f"CWE-{cwe_type}" / scanner_type / project_name
)
self.csv_path = self.project_result_path / "query_statistics.csv"

# 新版
self.project_result_path = (
    self.base_result_path / f"CWE-{cwe_type}" / scanner_type / project_name
)
# query_statistics 資料夾（與 Bandit、Semgrep 同層）
self.query_stats_dir = self.base_result_path / f"CWE-{cwe_type}" / "query_statistics"
# CSV 檔案路徑（檔名改為專案名稱）
self.csv_path = self.query_stats_dir / f"{project_name}.csv"
```

## 資料夾自動建立

當執行統計生成時，`query_statistics` 資料夾會自動建立（如果不存在）：

```python
# 在 initialize_csv() 和 _write_csv_batch() 中
self.csv_path.parent.mkdir(parents=True, exist_ok=True)
```

## 測試驗證

```bash
python tests/test_query_statistics.py
```

**測試結果：**
```
✅ 批次統計生成成功！
📄 生成的檔案: CWE_Result/CWE-327/query_statistics/aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
```

## 資料夾結構驗證

```bash
tree CWE_Result/CWE-327/
```

**輸出：**
```
CWE_Result/CWE-327/
├── Bandit/
│   └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
│       ├── 第1輪/
│       └── 第2輪/
├── Semgrep/
│   └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
│       ├── 第1輪/
│       └── 第2輪/
└── query_statistics/
    ├── aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
    └── test_project.csv
```

## 優點

### 1. 集中管理
所有專案的統計資料都在同一個資料夾，便於：
- 查找和存取
- 批次處理
- 數據備份

### 2. 便於比較
可以輕鬆比較不同專案的攻擊難度：
```bash
# 列出所有統計檔案
ls CWE_Result/CWE-327/query_statistics/

# 快速檢視某個專案的統計
cat CWE_Result/CWE-327/query_statistics/project_name.csv
```

### 3. 擴展性佳
未來可以在 `query_statistics` 資料夾中添加：
- 彙總報告（`summary.csv`）
- 視覺化圖表（`charts/`）
- 比較分析（`comparison.csv`）

### 4. 結構清晰
```
CWE-327/
├── Bandit/          ← 掃描器結果
├── Semgrep/         ← 掃描器結果
└── query_statistics/ ← 統計分析
```
三個資料夾各司其職，職責清楚

## 向後相容性

✅ 完全向後相容
- API 沒有變更
- 使用方式不變
- 自動建立新資料夾結構

## 遷移指南

### 如果您有舊的統計檔案

**舊檔案位置：**
```
CWE_Result/CWE-327/Semgrep/project_name/query_statistics.csv
```

**遷移到新位置：**
```bash
# 建立新資料夾
mkdir -p CWE_Result/CWE-327/query_statistics

# 移動並重新命名
mv CWE_Result/CWE-327/Semgrep/project_name/query_statistics.csv \
   CWE_Result/CWE-327/query_statistics/project_name.csv
```

或使用 Python 腳本批次遷移：
```python
from pathlib import Path
import shutil

cwe_dir = Path("CWE_Result/CWE-327")
query_stats_dir = cwe_dir / "query_statistics"
query_stats_dir.mkdir(exist_ok=True)

for scanner in ["Bandit", "Semgrep"]:
    scanner_dir = cwe_dir / scanner
    for project_dir in scanner_dir.glob("*"):
        old_file = project_dir / "query_statistics.csv"
        if old_file.exists():
            new_file = query_stats_dir / f"{project_dir.name}.csv"
            shutil.move(str(old_file), str(new_file))
            print(f"遷移: {old_file} -> {new_file}")
```

## 相關檔案

- `src/query_statistics.py` - 路徑配置更新
- `tests/test_query_statistics.py` - 測試路徑更新
- `docs/QUERY_STATISTICS_PATH_UPDATE.md` - 本文件

## 注意事項

1. **自動建立**：新資料夾會自動建立，無需手動操作
2. **權限問題**：確保程式有寫入 `CWE_Result` 的權限
3. **檔名衝突**：如果同一個專案執行多次，會覆蓋舊的統計檔案
4. **跨 CWE 類型**：每個 CWE 類型都有獨立的 `query_statistics` 資料夾

## 更新日誌

- 2025-10-27：路徑結構更新，檔名改為專案名稱
- 2025-10-27：測試通過，功能正常
