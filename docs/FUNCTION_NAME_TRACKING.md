# Function Name Tracking Feature

## 概述

在 Artificial Suicide 模式中，新增了函式名稱追蹤功能，用於記錄 AI 在每一輪 Query Phase 中修改的函式名稱，並確保後續輪次使用最新的函式名稱。

## 問題背景

在原始實作中，每輪的兩道程序（Query Phase 和 Coding Phase）都使用 `prompt.txt` 中的原始函式名稱作為模板變數。然而：

1. **第一道程序（Query Phase）**：AI 會將原始函式名稱修改為更具誘導性的名稱
2. **第二道程序（Coding Phase）**：仍使用原始函式名稱，導致 AI 無法找到已修改的函式

這造成了邏輯不一致，影響了 Artificial Suicide 攻擊的效果。

## 解決方案

### 1. 新增 `FunctionNameTracker` 模組

位置：`src/function_name_tracker.py`

功能：
- 追蹤每輪 Query Phase 後的函式名稱變更
- 將變更記錄到 `FunctionName_query.csv`
- 提供查詢介面，讓後續輪次可以取得最新的函式名稱

### 2. CSV 記錄格式

檔案路徑：`ExecutionResult/Success/{project_name}/FunctionName_query.csv`

欄位：
```csv
檔案路徑,原始函式名稱,輪數,修改後函式名稱,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),1,generate_encryption_key(),2025-10-31 16:15:13
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),2,generate_secure_encryption_key(),2025-10-31 16:15:13
```

### 3. 函式名稱提取策略

在 `extract_modified_function_name()` 方法中：

1. 讀取專案檔案內容
2. 使用正則表達式搜尋所有函式定義：`def\s+(\w+)\s*\(`
3. 尋找與原始名稱相似的函式（子字串匹配或長度相近）
4. 返回修改後的函式名稱

## 整合到 Artificial Suicide 模式

### 初始化階段

在 `execute()` 方法中，步驟 0.6：

```python
self.function_name_tracker = create_function_name_tracker(
    project_name=self.project_path.name
)
```

### Phase 1 完成後

在 `_execute_phase1()` 中，每行處理成功後：

```python
if self.function_name_tracker:
    modified_name = self.function_name_tracker.extract_modified_function_name(
        filepath=target_file,
        original_name=target_function_name,
        project_path=self.project_path
    )
    
    if modified_name and modified_name != target_function_name:
        self.function_name_tracker.record_function_change(
            filepath=target_file,
            original_name=target_function_name,
            modified_name=modified_name,
            round_num=round_num
        )
```

### 生成 Prompt 時

在 `_generate_query_prompt()` 和 `_generate_coding_prompt()` 中：

```python
# 取得該輪次應使用的函式名稱
if self.function_name_tracker:
    actual_function_name = self.function_name_tracker.get_function_name_for_round(
        target_file, target_function_name, round_num
    )
else:
    actual_function_name = target_function_name
```

## 邏輯流程

### 第 1 輪

1. **Query Phase**：
   - 使用原始函式名稱（如 `generate_fernet_key()`）
   - AI 修改為 `generate_encryption_key()`
   - 記錄到 CSV：Round 1

2. **Coding Phase**：
   - 使用最新函式名稱（`generate_encryption_key()`）
   - AI 可以正確找到已修改的函式

### 第 2 輪

1. **Query Phase**：
   - 使用第 1 輪修改的名稱（`generate_encryption_key()`）
   - AI 再次修改為 `generate_secure_encryption_key()`
   - 記錄到 CSV：Round 2

2. **Coding Phase**：
   - 使用最新函式名稱（`generate_secure_encryption_key()`）
   - 繼續正確的迭代過程

## API 參考

### `FunctionNameTracker` 類別

#### 主要方法

**`initialize_csv() -> bool`**
- 初始化 CSV 檔案（或載入現有資料）

**`extract_modified_function_name(filepath, original_name, project_path) -> Optional[str]`**
- 從專案檔案中提取修改後的函式名稱

**`record_function_change(filepath, original_name, modified_name, round_num) -> bool`**
- 記錄函式名稱變更到 CSV

**`get_latest_function_name(filepath, original_name) -> str`**
- 取得最新的函式名稱（所有輪次中的最新記錄）

**`get_function_name_for_round(filepath, original_name, target_round) -> str`**
- 取得指定輪次應使用的函式名稱
- 邏輯：第 1 輪使用原始名稱，第 N 輪使用第 N-1 輪的修改名稱

### 便捷函式

**`create_function_name_tracker(project_name, execution_result_path=None) -> FunctionNameTracker`**
- 建立並初始化追蹤器

## 測試

執行測試腳本：

```bash
python test_function_name_tracker.py
```

測試涵蓋：
1. 基本初始化和記錄功能
2. 查詢功能（最新名稱、特定輪次名稱）
3. CSV 輸出格式驗證

## 注意事項

1. **函式名稱提取限制**：
   - 依賴正則表達式匹配，可能無法處理所有 Python 語法變體
   - 如果 AI 完全重命名函式（無相似性），可能無法自動提取

2. **效能考量**：
   - 每次提取都需要讀取並解析檔案
   - 對於大型專案檔案可能略有延遲

3. **錯誤處理**：
   - 如果提取失敗，會使用原始函式名稱（向後相容）
   - 所有錯誤都會記錄到日誌

## 未來改進方向

1. **增強提取演算法**：
   - 使用 AST（抽象語法樹）解析 Python 檔案
   - 更準確地識別函式定義和變更

2. **支援多語言**：
   - 目前僅支援 Python
   - 可擴展至 JavaScript、Java 等語言

3. **視覺化報告**：
   - 生成函式名稱演化圖表
   - 追蹤命名模式的統計分析

## 相關檔案

- `src/function_name_tracker.py` - 追蹤器主模組
- `src/artificial_suicide_mode.py` - 整合點
- `test_function_name_tracker.py` - 單元測試
- `ExecutionResult/Success/{project}/FunctionName_query.csv` - 輸出檔案
