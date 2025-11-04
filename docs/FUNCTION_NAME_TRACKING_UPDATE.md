# Function Name Tracking - 更新說明

## 版本資訊
- **原始版本**：2025-10-31 16:15（使用相似性匹配）
- **更新版本**：2025-10-31 16:30（使用行號定位）

## 主要變更

### 1. 函式名稱提取策略：相似性匹配 → 行號定位

#### 原始實作（已廢棄）
```python
# 搜尋所有函式，找出與原始名稱相似的
def extract_modified_function_name(filepath, original_name, project_path):
    # 讀取所有函式定義
    matches = re.findall(r'def\s+(\w+)\s*\(', content)
    
    # 使用字串包含或長度相近來尋找相似函式
    candidates = [m for m in matches if original_name in m or m in original_name]
    ...
```

**問題**：
- 可能匹配到錯誤的函式
- 無法處理完全重命名的情況
- 依賴模糊的相似性判斷

#### 新實作（推薦）
```python
# 步驟 1：找出原始函式所在行號（僅第 1 輪）
def find_original_function_line(filepath, original_name, project_path):
    pattern = rf'def\s+{re.escape(original_name_clean)}\s*\('
    for line_num, line in enumerate(lines, start=1):
        if re.search(pattern, line):
            return line_num

# 步驟 2：AI 修改後，從同一行號提取新函式名稱
def extract_modified_function_name_by_line(filepath, original_name, line_number, project_path):
    target_line = lines[line_number - 1]
    match = re.search(r'def\s+(\w+)\s*\(', target_line)
    return match.group(1) + '()'
```

**優點**：
- **精確定位**：直接使用行號，不會匹配錯
- **處理任意重命名**：無論名稱如何變化，只要在同一行就能提取
- **邏輯清晰**：搜尋原始函式 → AI 修改 → 提取新名稱

### 2. CSV 結構：單一檔案 → 資料夾結構

#### 原始實作（已廢棄）
```
ExecutionResult/Success/{project}/FunctionName_query.csv

內容：
檔案路徑,原始函式名稱,輪數,修改後函式名稱,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),1,generate_encryption_key(),2025-10-31 16:15:13
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),2,generate_secure_encryption_key(),2025-10-31 16:15:13
```

**問題**：
- 所有輪次混在同一個檔案，不易閱讀
- 難以快速查看單一輪次的變更

#### 新實作（推薦）
```
ExecutionResult/Success/{project}/FunctionName_query/
├── round1.csv
├── round2.csv
└── round3.csv
```

**round1.csv**：
```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),100,1,generate_encryption_key(),100,2025-10-31 16:29:50
```

**round2.csv**：
```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
airflow-core/src/airflow/models/dagbag.py,generate_fernet_key(),100,2,generate_secure_encryption_key(),100,2025-10-31 16:29:50
```

**優點**：
- **結構清晰**：每輪獨立檔案，易於閱讀和分析
- **包含行號**：記錄原始行號和修改後行號（通常相同）
- **易於擴展**：新增輪次只需新增檔案，不影響現有資料

## 程式碼變更摘要

### `src/function_name_tracker.py`

**新增方法**：
- `find_original_function_line()` - 搜尋原始函式行號
- `extract_modified_function_name_by_line()` - 根據行號提取新名稱

**修改方法**：
- `record_function_change()` - 新增 `original_line` 和 `modified_line` 參數，寫入到 `roundN.csv`
- `get_latest_function_name()` - 返回 `(name, line_number)` 元組
- `get_function_name_for_round()` - 返回 `(name, line_number)` 元組

**移除方法**：
- `extract_modified_function_name()` - 使用相似性匹配（已廢棄）

### `src/artificial_suicide_mode.py`

**新增邏輯（Phase 1）**：
```python
# 步驟 1：搜尋原始函式行號（僅第 1 輪）
if round_num == 1 and self.function_name_tracker:
    original_line_number = self.function_name_tracker.find_original_function_line(
        filepath=target_file,
        original_name=target_function_name,
        project_path=self.project_path
    )

# 步驟 2：AI 修改後，從行號提取新函式名稱
if line_to_check:
    result = self.function_name_tracker.extract_modified_function_name_by_line(
        filepath=target_file,
        original_name=target_function_name,
        line_number=line_to_check,
        project_path=self.project_path
    )
    
    if result:
        modified_name, modified_line = result
        self.function_name_tracker.record_function_change(
            filepath=target_file,
            original_name=target_function_name,
            modified_name=modified_name,
            round_num=round_num,
            original_line=original_line_number,
            modified_line=modified_line
        )
```

## 執行流程

### 第 1 輪
1. **搜尋原始函式行號**：`generate_fernet_key()` 在第 100 行
2. **發送 Query Prompt**：使用原始名稱
3. **AI 修改**：將第 100 行的函式改名為 `generate_encryption_key()`
4. **提取新名稱**：從第 100 行讀取 `generate_encryption_key()`
5. **記錄到 round1.csv**

### 第 2 輪
1. **查詢上一輪行號**：從追蹤器取得第 100 行
2. **發送 Query Prompt**：使用 `generate_encryption_key()`
3. **AI 修改**：將第 100 行改為 `generate_secure_encryption_key()`
4. **提取新名稱**：從第 100 行讀取 `generate_secure_encryption_key()`
5. **記錄到 round2.csv**

## 測試驗證

執行 `python test_function_name_tracker.py`：

✅ 測試 1：基本初始化和記錄功能（使用行號定位）
✅ 測試 2：查詢功能（返回名稱和行號元組）
✅ 測試 3：CSV 資料夾結構驗證

所有測試通過。

## 向後相容性

- ✅ 舊的 `FunctionName_query.csv` 檔案將被忽略
- ✅ 新系統自動建立 `FunctionName_query/` 資料夾
- ✅ 如果提取失敗，會使用原始函式名稱（向後相容）

## 效能影響

- **第 1 輪**：新增搜尋原始行號的步驟（每個函式約 1-5ms）
- **第 2+ 輪**：從內存中讀取行號（< 1ms）
- **提取名稱**：直接讀取指定行，效能優於掃描整個檔案

## 建議

1. **刪除舊資料**：如果有舊的 `FunctionName_query.csv`，建議手動刪除以避免混淆
2. **重新執行**：對於已完成的專案，建議重新執行以產生新格式的 CSV
3. **監控日誌**：注意 `"搜尋原始函式行號"` 和 `"提取修改後函式名稱"` 的日誌訊息

## 總結

更新後的實作使用**行號定位**策略，比原本的**相似性匹配**更加準確和可靠。同時，**資料夾結構的 CSV** 讓每輪的變更更加清晰易讀。這兩項改進顯著提升了函式名稱追蹤的精確度和可維護性。
