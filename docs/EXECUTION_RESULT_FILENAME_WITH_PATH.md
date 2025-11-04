# ExecutionResult 檔案命名包含完整路徑

**更新日期**: 2025-11-02  
**更新原因**: 回應儲存檔案命名應包含完整路徑資訊，而非只有檔案名稱  
**影響範圍**: `ExecutionResult/Success/` 目錄下的 Copilot 回應 Markdown 檔案命名

---

## 更新摘要

將 ExecutionResult 中 Copilot 回應的檔案命名從**只包含檔案名稱**改為**包含完整路徑**，以便更清楚地識別不同目錄下的同名檔案。

### 命名規則變更

#### 修改前（只有檔案名稱）
```
第1行_base_coder.py_show_send_output().md
第2行_test_onboarding.py_test_generate_pkce_codes().md
      ^^^^^^^^^^^^^^^^ (只有檔案名，無路徑資訊)
```

**問題**：
- 無法區分不同目錄下的同名檔案
- 例如：`tests/basic/test_onboarding.py` 和 `tests/advanced/test_onboarding.py` 都會被命名為 `test_onboarding.py`

#### 修改後（包含完整路徑）
```
第1行_aider__coders__base_coder.py_show_send_output().md
第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ (完整路徑，/ 替換為 __)
```

**改善**：
- 完整保留檔案的目錄結構資訊
- 不同目錄的同名檔案可明確區分
- 與 prompt.txt 中的路徑格式一致（更容易對應）

---

## 路徑轉換規則

由於檔案名稱不能包含 `/` 字元，我們將路徑分隔符號替換為雙底線 `__`：

| 原始路徑 | 檔案命名中的路徑 |
|---------|----------------|
| `aider/coders/base_coder.py` | `aider__coders__base_coder.py` |
| `tests/basic/test_onboarding.py` | `tests__basic__test_onboarding.py` |
| `airflow/providers/aws/sensor.py` | `airflow__providers__aws__sensor.py` |
| `simple.py` | `simple.py` |

---

## 變更清單

### 程式碼修改

檔案: `src/artificial_suicide_mode.py`

#### 1. Phase 1 (Query Phase) - 第 367 行

**修改前**:
```python
# 提取檔名（不含路徑）
filename = Path(target_file).name

if retry_count == 0:
    self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {filename}|{target_function_name}")
```

**修改後**:
```python
# 提取檔案路徑（保留完整路徑，將 / 替換為 __）
filename = target_file.replace('/', '__')

if retry_count == 0:
    self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {target_file}|{target_function_name}")
```

**變更說明**:
- ✅ 使用 `target_file.replace('/', '__')` 保留完整路徑
- ✅ 日誌也改為顯示完整路徑 `target_file`（而非簡短的 `filename`）

#### 2. Phase 2 (Coding Phase) - 第 572 行

**修改前**:
```python
# 提取檔名（不含路徑）
filename = Path(target_file).name

if retry_count == 0:
    self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {filename}|{target_function_name}")
```

**修改後**:
```python
# 提取檔案路徑（保留完整路徑，將 / 替換為 __）
filename = target_file.replace('/', '__')

if retry_count == 0:
    self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: {target_file}|{target_function_name}")
```

**變更說明**:
- ✅ 兩個階段使用相同的路徑轉換邏輯
- ✅ 確保 Phase 1 和 Phase 2 的檔案命名一致

---

## 檔案命名格式

### 完整命名規則

```
第{line_number}行_{filepath_with_double_underscores}_{function_name}.md
```

**範例**：

| prompt.txt 內容 | 生成的檔案名稱 |
|----------------|--------------|
| `aider/coders/base_coder.py\|show_send_output()` | `第1行_aider__coders__base_coder.py_show_send_output().md` |
| `tests/basic/test_onboarding.py\|test_generate_pkce_codes()` | `第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md` |
| `airflow/providers/aws/sensor.py\|get_next_poke_interval()` | `第3行_airflow__providers__aws__sensor.py_get_next_poke_interval().md` |
| `simple.py\|main()` | `第1行_simple.py_main().md` |

---

## 目錄結構範例

### 修改前
```
ExecutionResult/
└── Success/
    └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
        └── 第1輪/
            ├── 第1道/  (Query Phase)
            │   ├── 第1行_base_coder.py_show_send_output().md  ← 只有檔案名
            │   └── 第2行_test_onboarding.py_test_generate_pkce_codes().md
            └── 第2道/  (Coding Phase)
                ├── 第1行_base_coder.py_show_send_output().md  ← 無法得知目錄
                └── 第2行_test_onboarding.py_test_generate_pkce_codes().md
```

### 修改後
```
ExecutionResult/
└── Success/
    └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
        └── 第1輪/
            ├── 第1道/  (Query Phase)
            │   ├── 第1行_aider__coders__base_coder.py_show_send_output().md  ← 包含完整路徑
            │   └── 第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md
            └── 第2道/  (Coding Phase)
                ├── 第1行_aider__coders__base_coder.py_show_send_output().md  ← 清楚知道在 aider/coders/ 目錄
                └── 第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md
```

---

## 實際案例對照

### 案例 1: 多層目錄結構

**prompt.txt**:
```
airflow/providers/amazon/aws/sensors/s3.py|S3KeySensor.poke()
airflow/providers/google/cloud/sensors/gcs.py|GCSObjectExistenceSensor.poke()
airflow/sensors/base.py|BaseSensorOperator.poke()
```

**修改前的檔案名稱**（無法區分）:
```
第1行_s3.py_S3KeySensor.poke().md       ← 不知道在哪個目錄
第2行_gcs.py_GCSObjectExistenceSensor.poke().md
第3行_base.py_BaseSensorOperator.poke().md
```

**修改後的檔案名稱**（清楚明瞭）:
```
第1行_airflow__providers__amazon__aws__sensors__s3.py_S3KeySensor.poke().md
第2行_airflow__providers__google__cloud__sensors__gcs.py_GCSObjectExistenceSensor.poke().md
第3行_airflow__sensors__base.py_BaseSensorOperator.poke().md
```

### 案例 2: 同名檔案在不同目錄

**prompt.txt**:
```
tests/unit/test_auth.py|test_login()
tests/integration/test_auth.py|test_login()
```

**修改前**（命名衝突）:
```
第1行_test_auth.py_test_login().md  ← 無法區分是 unit 還是 integration
第2行_test_auth.py_test_login().md  ← 同名，可能互相覆蓋
```

**修改後**（清楚區分）:
```
第1行_tests__unit__test_auth.py_test_login().md         ← unit 測試
第2行_tests__integration__test_auth.py_test_login().md  ← integration 測試
```

---

## 日誌輸出變更

### 修改前
```log
  處理第 1/42 行: base_coder.py|show_send_output()
  處理第 2/42 行: test_onboarding.py|test_generate_pkce_codes()
```

### 修改後
```log
  處理第 1/42 行: aider/coders/base_coder.py|show_send_output()
  處理第 2/42 行: tests/basic/test_onboarding.py|test_generate_pkce_codes()
```

**改善**:
- ✅ 日誌中顯示完整路徑，方便追蹤
- ✅ 與 prompt.txt 中的路徑格式一致

---

## 相關系統整合

### 與 prompt.txt 的關係

**prompt.txt 格式**:
```
filepath|function_name
```

**範例**:
```
aider/coders/base_coder.py|show_send_output()
tests/basic/test_onboarding.py|test_generate_pkce_codes()
```

**檔案命名對應**:
```
第1行_aider__coders__base_coder.py_show_send_output().md
第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md
```

**一致性**: 檔案名稱中的路徑部分與 prompt.txt 完全對應（只是 `/` 替換為 `__`）

### 與 CWE 掃描結果的關係

CSV 記錄（`CWE_Result/`）也使用完整路徑：

```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,aider/coders/base_coder.py,show_send_output(),2,...
1,2,tests/basic/test_onboarding.py,test_generate_pkce_codes(),0,...
```

**對應關係**:
- CSV 中的 `檔案路徑` = `aider/coders/base_coder.py`
- 檔案名稱中的路徑 = `aider__coders__base_coder.py`
- 可透過 `replace('__', '/')` 輕鬆轉換

### 與 OriginalScanResult 的關係

OriginalScanResult 也使用類似的路徑編碼：

```
OriginalScanResult/
└── Bandit/
    └── CWE-327/
        └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
            └── 第1輪/
                ├── coders__base_coder.py_report.json  ← 路徑編碼
                └── tests__basic__test_onboarding.py_report.json
```

**一致性**: 都使用 `__` 作為路徑分隔符號替代

---

## 影響分析

### ✅ 優點

1. **明確的檔案識別**: 可從檔案名稱直接看出完整路徑
2. **避免命名衝突**: 不同目錄的同名檔案不會互相覆蓋
3. **一致性提升**: 與 prompt.txt 格式對應，易於追蹤
4. **改善可讀性**: 日誌輸出也顯示完整路徑
5. **便於除錯**: 出問題時可快速定位到具體檔案

### ⚠️ 注意事項

1. **檔案名稱變長**: 深層目錄結構會導致較長的檔案名稱
   - 例如: `第1行_airflow__providers__amazon__aws__sensors__s3.py_S3KeySensor.poke().md`（88 字元）
   - **影響**: 檔案列表可能需要橫向捲動查看完整名稱

2. **路徑轉換**: 需要手動將 `__` 轉換回 `/` 才能得到原始路徑
   - **解決方案**: 可使用簡單的字串替換 `filename.replace('__', '/')`

3. **歷史檔案不相容**: 舊的只含檔案名稱的記錄不會自動更新
   - **建議**: 新執行的結果會使用新格式，舊檔案保持不變

---

## 驗證方式

### 檢查修改是否生效

執行 Artificial Suicide 模式後，檢查 ExecutionResult 目錄：

```bash
# 檢查新格式（應包含 __ 路徑分隔符號）
find ExecutionResult/Success/ -name "*.md" | grep "__" | head -5

# 範例輸出：
# ExecutionResult/Success/aider__CWE-327/第1輪/第1道/第1行_aider__coders__base_coder.py_show_send_output().md
# ExecutionResult/Success/aider__CWE-327/第1輪/第1道/第2行_tests__basic__test_onboarding.py_test_generate_pkce_codes().md
```

### 檢查日誌輸出

```bash
# 查看最新的日誌檔案
tail -f logs/automation__*.log | grep "處理第"

# 應該看到完整路徑：
# 處理第 1/42 行: aider/coders/base_coder.py|show_send_output()
# 處理第 2/42 行: tests/basic/test_onboarding.py|test_generate_pkce_codes()
```

---

## 路徑還原工具

如果需要將檔案名稱還原為原始路徑：

```python
def restore_filepath_from_filename(filename: str) -> str:
    """
    從 ExecutionResult 檔案名稱還原原始檔案路徑
    
    範例:
        第1行_aider__coders__base_coder.py_show_send_output().md
        → aider/coders/base_coder.py
    """
    # 移除前綴 "第N行_"
    parts = filename.split('_', 1)
    if len(parts) < 2:
        return filename
    
    content = parts[1]
    
    # 分離檔案路徑和函式名稱（最後一個 _ 後是函式名）
    last_underscore = content.rfind('_')
    if last_underscore == -1:
        filepath_encoded = content.replace('.md', '')
    else:
        filepath_encoded = content[:last_underscore]
    
    # 將 __ 還原為 /
    filepath = filepath_encoded.replace('__', '/')
    
    return filepath

# 測試
print(restore_filepath_from_filename(
    "第1行_aider__coders__base_coder.py_show_send_output().md"
))
# 輸出: aider/coders/base_coder.py
```

---

## 相關文件

- `src/artificial_suicide_mode.py` - AS 模式主程式（包含檔案命名邏輯）
- `src/copilot_handler.py` - 回應儲存處理（檔案命名實作）
- `docs/SCAN_TIMING_ANALYSIS.md` - 掃描時機分析
- `docs/CSV_HEADER_UPDATE_CURRENT_FUNCTION_NAME.md` - CSV 欄位更新說明

---

## 總結

此次更新將 ExecutionResult 中的檔案命名從**只包含檔案名稱**改為**包含完整路徑**：

1. ✅ **保留完整路徑資訊**: 使用 `target_file.replace('/', '__')` 轉換路徑
2. ✅ **避免命名衝突**: 不同目錄的同名檔案可明確區分
3. ✅ **提升一致性**: 與 prompt.txt 格式對應，易於追蹤
4. ✅ **改善可讀性**: 檔案名稱和日誌都顯示完整路徑
5. ✅ **便於除錯**: 出問題時可快速定位到具體檔案

**重要提醒**: 
- 檔案名稱會變長，但提供了更完整的資訊
- 與其他系統（CWE 掃描、OriginalScanResult）使用一致的路徑編碼方式
- 可透過簡單的字串替換還原原始路徑
