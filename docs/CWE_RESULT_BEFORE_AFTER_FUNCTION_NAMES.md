# CWE_Result CSV 格式更新：修改前/修改後函式名稱

**日期**: 2025-11-03  
**類型**: CSV 格式調整

## 問題背景

在 Artificial Suicide 模式中：
- **Phase 1 (Query Phase)**: AI 修改函式名稱（例如 `show_send_output` → `compute_response_checksum`）
- **Phase 2 (Coding Phase)**: 基於修改後的名稱生成代碼並執行 CWE 掃描

原本的 CWE_Result CSV 只有一個「當前函式名稱」欄位，無法清楚記錄：
1. Phase 1 送出 prompt **前**的函式名稱（修改前）
2. Phase 1 回應**後**的新函式名稱（修改後）

## 解決方案

### CSV 格式調整

**舊格式**:
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
```

**新格式**:
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,...
```

### 欄位定義

| 欄位名稱 | 定義 | 來源 | 範例 |
|---------|------|------|------|
| **修改前函式名稱** | Phase 1 送出 prompt **前**的名稱 | FunctionName_query 的「當前函式名稱」 | `show_send_output` (Round 1)<br>`compute_response_checksum` (Round 2) |
| **修改後函式名稱** | Phase 1 回應**後**的新名稱 | FunctionName_query 的「修改後函式名稱」 | `compute_response_checksum` (Round 1)<br>`validate_message_integrity` (Round 2) |

### 與 FunctionName_query CSV 的對應關係

**FunctionName_query CSV 格式**:
```csv
輪數,原始行號,檔案路徑,原始函式名稱,當前函式名稱,修改後函式名稱,修改後行號,時間戳記
```

**對應關係**:
- CWE_Result 的「修改前函式名稱」 = FunctionName_query 的「當前函式名稱」
- CWE_Result 的「修改後函式名稱」 = FunctionName_query 的「修改後函式名稱」

這樣兩個 CSV 的函式名稱記錄就完全一致了。

## 修改檔案

### 1. src/cwe_scan_manager.py

**修改內容**:
1. **Import 新增**:
   ```python
   from src.function_name_tracker import FunctionNameTracker
   ```

2. **`__init__` 參數新增**:
   ```python
   def __init__(self, output_dir: Path = None, function_name_tracker: FunctionNameTracker = None):
       self.function_name_tracker = function_name_tracker
   ```

3. **`_save_function_level_csv` CSV Header 更新**:
   ```python
   writer.writerow([
       '輪數', '行號', '檔案路徑',
       '修改前函式名稱',  # 新增
       '修改後函式名稱',  # 新增
       '漏洞數量', '漏洞行號', '掃描器', '信心度', '嚴重性', '問題描述', '掃描狀態', '失敗原因'
   ])
   ```

4. **查詢 function_name_tracker 邏輯**:
   ```python
   # 查詢修改前和修改後的函式名稱
   before_name = func_name  # 預設使用原始名稱
   after_name = func_name   # 預設使用原始名稱
   
   if self.function_name_tracker:
       # 獲取「修改前」名稱（送出 prompt 前）
       before_name, _ = self.function_name_tracker.get_function_name_for_round(
           target.file_path, func_name, round_number
       )
       
       # 獲取「修改後」名稱（AI 回應後）
       key = (target.file_path, func_name)
       if key in self.function_name_tracker.function_mapping:
           for round_num, modified_name, _ in self.function_name_tracker.function_mapping[key]:
               if round_num == round_number:
                   after_name = modified_name
                   break
   ```

5. **所有 CSV 寫入處更新**:
   - 掃描失敗: `writer.writerow([..., before_name, after_name, ...])`
   - 有漏洞: `writer.writerow([..., before_name, after_name, ...])`
   - 無漏洞但成功: `writer.writerow([..., before_name, after_name, ...])`

### 2. src/artificial_suicide_mode.py

**修改內容**:
```python
# 步驟 0.6：初始化函式名稱追蹤器
self.function_name_tracker = create_function_name_tracker(
    project_name=self.project_path.name
)

# 將 function_name_tracker 傳遞給 cwe_scan_manager
if self.cwe_scan_manager:
    self.cwe_scan_manager.function_name_tracker = self.function_name_tracker
    self.logger.info("✅ 已將 function_name_tracker 傳遞給 CWE 掃描管理器")
```

### 3. src/query_statistics.py

**修改內容**:
將讀取欄位從「當前函式名稱」改為「修改後函式名稱」（因為 Phase 2 掃描時使用的是修改後的名稱）:

```python
# 注意：欄位名稱是「修改後函式名稱」（Phase 2 掃描時的實際名稱）
function_name = record.get('修改後函式名稱', '').strip()
```

**修改位置**:
- Bandit 結果讀取邏輯（第 265 行）
- Semgrep 結果讀取邏輯（第 301 行）

## 範例數據

### Round 1 範例

**FunctionName_query/round1.csv**:
```csv
輪數,原始行號,檔案路徑,原始函式名稱,當前函式名稱,修改後函式名稱,修改後行號,時間戳記
1,100,aider/coders/base_coder.py,show_send_output,show_send_output,compute_response_checksum,100,2025-11-03 10:00:00
```

**CWE_Result/.../CWE-327_Bandit_function_level_scan.csv**:
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output,compute_response_checksum,1,...
```

### Round 2 範例

**FunctionName_query/round2.csv**:
```csv
輪數,原始行號,檔案路徑,原始函式名稱,當前函式名稱,修改後函式名稱,修改後行號,時間戳記
2,100,aider/coders/base_coder.py,show_send_output,compute_response_checksum,validate_message_integrity,100,2025-11-03 10:05:00
```

**CWE_Result/.../CWE-327_Bandit_function_level_scan.csv**:
```csv
輪數,行號,檔案路徑,修改前函式名稱,修改後函式名稱,漏洞數量,...
2,1,aider/coders/base_coder.py,compute_response_checksum,validate_message_integrity,1,...
```

## 測試驗證

執行 AS 模式後，檢查：
1. **FunctionName_query CSV**: 「當前函式名稱」和「修改後函式名稱」都有正確的值
2. **CWE_Result CSV**: 「修改前函式名稱」和「修改後函式名稱」與 FunctionName_query 一致
3. **Query Statistics CSV**: 能正確讀取「修改後函式名稱」並匹配函式

## 預期效果

✅ CWE 掃描結果清楚記錄每一輪的函式名稱變化  
✅ 與 FunctionName_query 的記錄完全一致  
✅ Query Statistics 能正確匹配修改後的函式名稱  
✅ 更容易追蹤 AI 如何逐步修改函式名稱以誘導漏洞產生
