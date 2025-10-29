# Query Statistics 即時更新功能

## 更新說明（2025-10-27）

根據使用者反饋，對 `query_statistics.csv` 功能進行了重大改進：

### 改進項目

1. **✅ 移除頂部空列**
   - 舊版：CSV 第一行是空白行
   - 新版：直接從表頭開始，更易讀

2. **✅ 即時更新機制**
   - 舊版：所有輪次完成後批次生成
   - 新版：每輪掃描後立即更新該輪欄位

3. **✅ 智能跳過機制**
   - `#` 標記意義：攻擊已成功，後續輪次自動跳過
   - 節省時間：已成功的函式不再重複攻擊

## CSV 格式對比

### 舊版格式
```csv
,,,,,
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,0,1,#,3
```

### 新版格式
```csv
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,0,1,#,3
```
→ 無頂部空列，更簡潔

## 使用方式

### 方式 1：即時更新（推薦）

```python
from src.query_statistics import initialize_query_statistics

# 1. 在攻擊開始前初始化
function_list = [
    "file1.py_func1()",
    "file2.py_func2()",
    ...
]

stats = initialize_query_statistics(
    project_name="my_project",
    cwe_type="327",
    scanner_type="Semgrep",
    total_rounds=4,
    function_list=function_list
)

# 2. 每輪攻擊後更新
for round_num in range(1, 5):
    # ... 執行該輪的攻擊和掃描 ...
    
    # 更新該輪統計
    stats.update_round_result(round_num)
    
    # 檢查是否應跳過某個函式
    if stats.should_skip_function("file1.py_func1()"):
        print("跳過，已攻擊成功")
```

### 方式 2：批次生成（向後相容）

```python
from src.query_statistics import generate_query_statistics

# 所有輪次完成後一次性生成
success = generate_query_statistics(
    project_name="my_project",
    cwe_type="327",
    scanner_type="Semgrep",
    total_rounds=4
)
```

## 即時更新流程

```
開始攻擊
    ↓
初始化 CSV（所有欄位為空）
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,,,,,
function2,,,,,
    ↓
第 1 輪攻擊 + 掃描
    ↓
更新第 1 輪結果
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,,,,         ← 未發現漏洞
function2,1,,,,         ← 發現 1 個漏洞
    ↓
第 2 輪攻擊 + 掃描（跳過 function2）
    ↓
更新第 2 輪結果
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,0,,,
function2,1,#,,,1       ← 已成功，標記 #，QueryTimes=1
    ↓
第 3 輪攻擊 + 掃描（跳過 function2）
    ↓
更新第 3 輪結果
file_function\Round n,round1,round2,round3,round4,QueryTimes
function1,0,0,2,,3      ← 本輪發現 2 個漏洞，QueryTimes=3
function2,1,#,#,,1      ← 持續標記 #
    ↓
第 4 輪攻擊 + 掃描（跳過 function1 和 function2）
    ↓
完成
```

## 智能跳過邏輯

### 判斷條件

函式會被跳過，當且僅當：
- CSV 中該函式的**任一輪次**欄位值 > 0

### 實際應用

```python
# 在每輪的第 1 道（Query Phase）和第 2 道（Coding Phase）開始前檢查
if stats.should_skip_function(function_key):
    logger.info(f"⏭️  跳過（已攻擊成功）")
    continue  # 跳過該函式
```

### 效益

假設有 100 個函式，4 輪攻擊：
- **無跳過機制**：100 × 4 = 400 次攻擊
- **有跳過機制**（假設平均第 2 輪成功 50%）：
  - 第 1 輪：100 次
  - 第 2 輪：100 次（50 個成功）
  - 第 3 輪：50 次（25 個成功）
  - 第 4 輪：25 次
  - 總計：275 次
  - **節省 31% 時間**

## 技術實作

### 核心方法

```python
class QueryStatistics:
    def initialize_csv(self) -> bool:
        """初始化 CSV，所有欄位為空"""
        
    def update_round_result(self, round_num: int) -> bool:
        """讀取該輪掃描結果，更新對應欄位"""
        
    def should_skip_function(self, function_key: str) -> bool:
        """判斷是否應跳過（已攻擊成功）"""
```

### 資料流

```
初始化
    ↓
讀取現有 CSV → 解析為 Dict
    ↓
讀取該輪掃描結果 → 解析為 Dict
    ↓
更新邏輯：
  - 若之前已發現漏洞 → 標記 #
  - 若本輪發現漏洞 → 記錄數量 + 更新 QueryTimes
  - 若本輪未發現 → 記錄 0
    ↓
寫回 CSV
```

### 邊界處理

1. **最後一輪仍未發現漏洞**
   - 標記 `QueryTimes = All-Safe`

2. **資料不完整**
   - 該輪沒有掃描結果 → 保持空白

3. **函式名稱簡化**
   - 移除 `.py` 和 `()`
   - `aider/coders/base_coder.py_show_send_output()` → `aider/coders/base_coder_show_send_output`

## 整合到 Artificial Suicide Mode

### 修改點

```python
# artificial_suicide_mode.py

def execute(self):
    # 步驟 0.5：初始化 Query 統計
    function_list = [...]  # 從 prompt.txt 提取
    self.query_stats = initialize_query_statistics(
        project_name=self.project_path.name,
        cwe_type=self.target_cwe,
        scanner_type="Semgrep",
        total_rounds=self.total_rounds,
        function_list=function_list
    )
    
    # 執行每一輪
    for round_num in range(1, self.total_rounds + 1):
        # 第 1 道 + 第 2 道
        self._execute_round(round_num)
        
        # 即時更新統計
        self.query_stats.update_round_result(round_num)
```

### Phase 1 & 2 修改

```python
def _execute_phase1(self, round_num):
    for line_idx, line in enumerate(self.prompt_lines):
        # 檢查是否應跳過
        if self.query_stats.should_skip_function(function_key):
            logger.info("⏭️  跳過（已攻擊成功）")
            continue
        
        # ... 正常執行攻擊 ...

def _execute_phase2(self, round_num):
    # 同樣的跳過邏輯
    ...
```

## 測試結果

### 批次生成測試（向後相容）
```
✅ 批次統計生成成功！
file_function\Round n,round1,round2,QueryTimes
aider/coders/base_coder_show_send_output,0,0,All-Safe
```
→ 無頂部空列 ✅

### 即時更新測試
```
✅ 初始化完成
file_function\Round n,round1,round2,round3,round4,QueryTimes
aider/coders/base_coder_show_send_output,,,,,
aider/models_send_completion,,,,,
```
→ 初始欄位為空 ✅

## 相關檔案

- `src/query_statistics.py` - 核心模組（已更新）
- `src/artificial_suicide_mode.py` - 整合點（已更新）
- `tests/test_query_statistics.py` - 測試腳本（已更新）
- `docs/QUERY_STATISTICS_REALTIME_UPDATE.md` - 本文件

## 向後相容性

- ✅ 舊的 `generate_query_statistics()` 仍可使用
- ✅ 新增 `initialize_query_statistics()` 用於即時更新
- ✅ 兩種模式輸出格式相同（除了頂部空列）

## 未來改進建議

1. **中斷恢復**
   - 支援從中斷的輪次恢復
   - 讀取現有 CSV 狀態繼續執行

2. **進度視覺化**
   - 實時顯示攻擊進度
   - 成功率統計

3. **並行攻擊優化**
   - 多函式同時攻擊
   - 動態調整並行數

## 更新日期

2025-10-27
