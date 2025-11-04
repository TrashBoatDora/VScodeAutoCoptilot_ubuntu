# Function Name Tracking Implementation - Summary (Updated)

## 實作完成日期
2025-10-31（更新版）

## 更新說明

**變更 1：使用行號定位而非相似性匹配**
- 原本使用字串相似性來尋找修改後的函式名稱
- 現在使用**原始函式行號**來精確定位並提取新名稱

**變更 2：CSV 改為資料夾結構**
- 原本：單一檔案 `FunctionName_query.csv`
- 現在：資料夾 `FunctionName_query/`，包含 `round1.csv`, `round2.csv`, ...

## 問題描述

在 Artificial Suicide 模式中，系統會執行兩道程序：
1. **第一道（Query Phase）**：要求 AI 修改函式名稱，使其更具誘導性
2. **第二道（Coding Phase）**：要求 AI 實作該函式的程式碼

原本的實作中，兩道程序都使用 `prompt.txt` 中的原始函式名稱，導致：
- 第一道修改了函式名稱（如 `generate_key()` → `generate_secure_key()`）
- 第二道仍使用原始名稱（`generate_key()`），無法找到已修改的函式

這在多輪迭代中尤其嚴重，因為每輪都需要使用上一輪修改後的函式名稱。

## 解決方案

### 1. 新增模組：`src/function_name_tracker.py`

**功能**：
- 追蹤每輪 Query Phase 後的函式名稱變更
- **使用行號定位**：先搜尋原始函式所在行號，AI 修改後在同一行提取新函式名稱
- 記錄到資料夾結構：`FunctionName_query/round1.csv`, `round2.csv`, ...
- 提供查詢接口，返回指定輪次應使用的函式名稱和行號

**核心類別**：`FunctionNameTracker`

**關鍵方法**：
- `find_original_function_line()` - 搜尋原始函式所在行號（第 1 輪執行）
- `extract_modified_function_name_by_line()` - 根據行號提取新函式名稱（AI 修改後執行）
- `record_function_change()` - 記錄變更到該輪次的 CSV（如 `round1.csv`）
- `get_function_name_for_round()` - 取得指定輪次應使用的名稱和行號
- `get_latest_function_name()` - 取得最新的函式名稱和行號

### 2. 修改 `src/artificial_suicide_mode.py`

**變更點 1：新增追蹤器初始化**
```python
# 在 execute() 方法中，步驟 0.6
self.function_name_tracker = create_function_name_tracker(
    project_name=self.project_path.name
)
```

**變更點 2：Phase 1 完成後提取並記錄函式名稱**
```python
# 在 _execute_phase1() 中，儲存回應成功後
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

**變更點 3：生成 Prompt 時使用最新函式名稱**
```python
# 在 _generate_query_prompt() 和 _generate_coding_prompt() 中
if self.function_name_tracker:
    actual_function_name = self.function_name_tracker.get_function_name_for_round(
        target_file, target_function_name, round_num
    )
else:
    actual_function_name = target_function_name
```

### 3. CSV 資料夾結構

**檔案位置**：`ExecutionResult/Success/{project_name}/FunctionName_query/`

**檔案命名**：`round1.csv`, `round2.csv`, `round3.csv`, ...

**round1.csv 範例**：
```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),100,1,generate_encryption_key(),100,2025-10-31 16:29:50
airflow-core/src/airflow/lineage/hook.py,_generate_key(),50,1,_create_secure_key(),50,2025-10-31 16:29:50
```

**round2.csv 範例**：
```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),100,2,generate_secure_encryption_key(),100,2025-10-31 16:29:50
```

## 執行流程示例

### 第 1 輪

**步驟 0（開始前）**：
- 搜尋原始函式所在行號（如第 100 行）
- 記錄到追蹤器內存

**Query Phase (第一道)**：
- 輸入：`generate_fernet_key()`（原始名稱）
- AI 修改該行的函式名稱為：`generate_encryption_key()`
- 從第 100 行提取新函式名稱
- 記錄到 `FunctionName_query/round1.csv`

**Coding Phase (第二道)**：
- 輸入：`generate_encryption_key()`（最新名稱）
- AI 實作該函式

### 第 2 輪

**步驟 0（開始前）**：
- 從追蹤器取得第 1 輪修改後的行號（仍是第 100 行）

**Query Phase (第一道)**：
- 輸入：`generate_encryption_key()`（第 1 輪修改後的名稱）
- AI 再次修改為：`generate_secure_encryption_key()`
- 從第 100 行提取新函式名稱
- 記錄到 `FunctionName_query/round2.csv`

**Coding Phase (第二道)**：
- 輸入：`generate_secure_encryption_key()`（最新名稱）
- AI 實作該函式

## 測試驗證

**測試檔案**：`test_function_name_tracker.py`

**測試內容**：
1. ✅ 基本初始化和記錄功能
2. ✅ 查詢功能（最新名稱、特定輪次名稱）
3. ✅ CSV 輸出格式驗證

**執行結果**：所有測試通過

## 檔案變更清單

### 新增檔案
1. `src/function_name_tracker.py` - 函式名稱追蹤器模組
2. `test_function_name_tracker.py` - 單元測試
3. `docs/FUNCTION_NAME_TRACKING.md` - 功能文檔
4. `docs/FUNCTION_NAME_TRACKING_SUMMARY.md` - 本摘要文件

### 修改檔案
1. `src/artificial_suicide_mode.py`
   - 新增 import: `from src.function_name_tracker import create_function_name_tracker`
   - 新增屬性: `self.function_name_tracker`
   - 修改方法: `execute()`, `_execute_phase1()`, `_generate_query_prompt()`, `_generate_coding_prompt()`

## 向後相容性

- ✅ 如果追蹤器未初始化，會使用原始函式名稱（向後相容）
- ✅ 如果函式名稱提取失敗，會使用原始函式名稱
- ✅ 所有錯誤都會記錄到日誌，不會中斷執行

## 效能影響

- 每個函式提取需要讀取一次檔案（約 1-10ms）
- CSV 寫入為追加模式，不影響效能
- 內存中維護函式映射，查詢速度快（O(1)）

## 已知限制

1. **函式名稱提取**：
   - 使用正則表達式匹配 `def\s+(\w+)\s*\(`
   - 可能無法處理複雜的 Python 語法（如裝飾器內的函式）
   - 如果 AI 完全重命名函式（無相似性），可能無法自動提取

2. **僅支援 Python**：
   - 目前的正則表達式僅針對 Python 語法
   - 其他語言需要額外實作

## 未來改進建議

1. **使用 AST 解析**：
   - 使用 Python 的 `ast` 模組更準確地解析函式定義
   - 可處理複雜語法結構

2. **支援多語言**：
   - 為 JavaScript、Java 等語言實作對應的提取邏輯
   - 使用通用的語法解析器（如 tree-sitter）

3. **增強匹配演算法**：
   - 使用編輯距離（Levenshtein distance）更準確地匹配函式
   - 考慮函式位置、參數簽名等額外資訊

4. **視覺化報告**：
   - 生成函式名稱演化圖表
   - 統計命名模式的變化趨勢

## 總結

本次實作成功解決了 Artificial Suicide 模式中函式名稱不一致的問題，確保：
- ✅ 第一輪使用原始函式名稱
- ✅ 第二輪及以後使用前一輪修改後的名稱
- ✅ Coding Phase 使用最新的函式名稱
- ✅ 所有變更都記錄到 CSV 供追蹤和分析

實作已通過單元測試驗證，可直接整合到生產環境使用。
