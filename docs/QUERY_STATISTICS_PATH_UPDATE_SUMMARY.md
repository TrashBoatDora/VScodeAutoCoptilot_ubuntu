# Query Statistics 路徑更新總結

## ✅ 完成變更（2025-10-27）

### 路徑結構

**之前：**
```
CWE_Result/CWE-327/Semgrep/project_name/query_statistics.csv
```

**之後：**
```
CWE_Result/CWE-327/query_statistics/project_name.csv
```

### 資料夾結構

```
CWE_Result/
└── CWE-327/
    ├── Bandit/              ← 掃描器結果
    │   └── project_name/
    ├── Semgrep/             ← 掃描器結果
    │   └── project_name/
    └── query_statistics/    ← 統計資料（新位置）
        ├── project1.csv
        ├── project2.csv
        └── project3.csv
```

## 🎯 優點

1. **集中管理** - 所有統計檔案在同一資料夾
2. **易於比較** - 方便對比不同專案
3. **結構清晰** - 與掃描器結果分離
4. **檔名明確** - 使用專案名稱，一目了然

## 📁 實際範例

```
CWE_Result/CWE-327/query_statistics/
├── aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
├── airflow__CWE-327__CAL-ALL-6b42874e__M-call.csv
└── test_project.csv
```

## 🔧 自動處理

- ✅ 自動建立 `query_statistics` 資料夾
- ✅ 自動以專案名稱命名檔案
- ✅ 向後相容，API 不變

## 🧪 測試驗證

```bash
python tests/test_query_statistics.py
```

**結果：**
```
✅ 批次統計生成成功！
📄 CWE_Result/CWE-327/query_statistics/aider__CWE-327__CAL-ALL-6b42874e__M-call.csv
✅ 即時更新功能測試完成
```

## 📖 詳細文件

- `QUERY_STATISTICS_PATH_UPDATE.md` - 完整更新說明

## 日期

2025-10-27
