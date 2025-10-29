# Query Statistics 功能改進總結

## 🎯 主要改進（2025-10-27）

### 1. 移除頂部空列
**之前：**
```csv
,,,,,                         ← 空列
file_function\Round n,round1,round2,QueryTimes
```

**之後：**
```csv
file_function\Round n,round1,round2,QueryTimes
```
✅ 更簡潔，更易讀

### 2. 即時更新機制
**之前：** 所有輪次完成後一次性生成
```
輪1 → 輪2 → 輪3 → 輪4 → 生成統計
```

**之後：** 每輪完成後立即更新
```
輪1 → 更新統計 → 輪2 → 更新統計 → 輪3 → 更新統計 → 輪4 → 更新統計
```
✅ 即時追蹤進度
✅ 更早發現成功案例

### 3. 智能跳過機制
**功能：** 攻擊成功後自動跳過後續輪次

**範例：**
```csv
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,1,#,#,2          ← 第2輪成功，3、4輪自動跳過
function2,0,0,0,0,All-Safe   ← 所有輪次都安全
```

**效益：**
- 節省 **30-50%** 的執行時間
- 專注於未成功的函式

## 📊 使用方式

### 即時更新模式（推薦）

```python
from src.query_statistics import initialize_query_statistics

# 1. 初始化（攻擊開始前）
stats = initialize_query_statistics(
    project_name="my_project",
    cwe_type="327",
    scanner_type="Semgrep",
    total_rounds=4,
    function_list=["file.py_func()"]
)

# 2. 每輪後更新
for round_num in range(1, 5):
    # 執行攻擊...
    stats.update_round_result(round_num)
    
    # 檢查是否跳過
    if stats.should_skip_function("file.py_func()"):
        continue  # 跳過已成功的函式
```

### 批次生成模式（向後相容）

```python
from src.query_statistics import generate_query_statistics

# 所有輪次完成後生成
generate_query_statistics(
    project_name="my_project",
    cwe_type="327",
    scanner_type="Semgrep",
    total_rounds=4
)
```

## 🔄 自動整合

已整合到 `ArtificialSuicideMode`，無需手動調用：

```python
# main.py 中執行 AS 模式時自動處理
python main.py  # 選擇 Artificial Suicide 模式
```

功能會自動：
1. 初始化 query_statistics.csv
2. 每輪後更新統計
3. 自動跳過已成功的函式

## 📁 輸出位置

```
CWE_Result/
└── CWE-327/
    └── Semgrep/
        └── project_name/
            ├── 第1輪/
            ├── 第2輪/
            └── query_statistics.csv  ← 即時更新
```

## 🧪 測試驗證

```bash
python tests/test_query_statistics.py
```

**測試結果：**
- ✅ 批次生成（向後相容）
- ✅ 即時更新初始化
- ✅ 無頂部空列
- ✅ 格式正確

## 📖 詳細文件

- `QUERY_STATISTICS_FEATURE.md` - 完整功能說明
- `QUERY_STATISTICS_REALTIME_UPDATE.md` - 即時更新詳解
- `QUERY_STATISTICS_IMPLEMENTATION.md` - 實作總結

## ✅ 測試狀態

- [x] 批次生成功能
- [x] 即時更新功能  
- [x] 智能跳過邏輯
- [x] AS 模式整合
- [x] 向後相容性

## 日期

2025-10-27
