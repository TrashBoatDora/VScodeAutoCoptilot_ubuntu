# OriginalScanResult 檔案命名簡化

**更新日期**: 2025-11-02  
**更新原因**: 簡化原始掃描結果檔案命名，移除函式名稱部分  
**影響範圍**: `OriginalScanResult/` 目錄下的所有掃描報告檔案命名

---

## 更新摘要

簡化 OriginalScanResult 中原始掃描報告的檔案命名規則，**移除函式名稱部分**，只保留檔案名稱。

### 命名規則變更

#### 修改前
```
basic__test_onboarding.py__test_generate_pkce_codes()_report.json
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^ (函式名稱)
coders__base_coder.py__show_send_output()_report.json
                       ^^^^^^^^^^^^^^^^^^^ (函式名稱)
```

#### 修改後
```
basic__test_onboarding.py_report.json  ← 只保留檔案名稱
coders__base_coder.py_report.json      ← 只保留檔案名稱
```

---

## 變更原因

1. **降低複雜度**: 檔案名稱過長且包含特殊字元（括號），不利於管理和閱讀
2. **統一命名**: 所有掃描報告使用一致的命名格式（檔案名 + `_report.json`）
3. **避免衝突**: 同一個檔案的多次掃描結果會自動覆蓋（因為檔案名相同）
4. **簡化邏輯**: 不需要根據是否有函式名稱來決定命名格式

### 重要說明

- **掃描範圍不變**: 掃描仍然針對檔案中的特定函式，只是報告檔案名稱簡化
- **CSV 記錄完整**: `CWE_Result/` 中的 CSV 檔案仍然記錄完整的 `當前函式名稱`
- **報告內容不變**: JSON 報告內容仍然包含完整的函式級別掃描結果

---

## 變更清單

### 程式碼修改

檔案: `src/cwe_detector.py`

#### 1. Bandit 函式級別掃描 (第 658-671 行)

**修改前**:
```python
# 使用目錄前綴和函式名稱來命名，避免不同目錄下的同名檔案衝突
file_parts = file_path.parts
if len(file_parts) >= 2:
    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
else:
    base_name = file_path.name

# 如果有函式名稱，加入到檔案名中
if function_name:
    safe_filename = f"{base_name}__{function_name}_report.json"
else:
    safe_filename = f"{base_name}_report.json"
    
original_output_file = original_output_dir / safe_filename
```

**修改後**:
```python
# 使用目錄前綴和檔案名稱（不包含函式名稱）
file_parts = file_path.parts
if len(file_parts) >= 2:
    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
else:
    base_name = file_path.name

# 只使用檔案名稱，不加入函式名稱
safe_filename = f"{base_name}_report.json"
    
original_output_file = original_output_dir / safe_filename
```

#### 2. Bandit 單檔掃描 (第 676-680 行)

**修改前**:
```python
# 如果有函式名稱，加入到檔案名中
if function_name:
    original_output_file = original_output_dir / f"{file_path.name}__{function_name}_report.json"
else:
    original_output_file = original_output_dir / f"{file_path.name}_report.json"
```

**修改後**:
```python
# 只使用檔案名稱（不包含函式名稱）
original_output_file = original_output_dir / f"{file_path.name}_report.json"
```

#### 3. Semgrep 函式級別掃描 (第 708-721 行)

**修改前**:
```python
# 使用目錄前綴和函式名稱來命名，避免不同目錄下的同名檔案衝突
file_parts = file_path.parts
if len(file_parts) >= 2:
    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
else:
    base_name = file_path.name

# 如果有函式名稱，加入到檔案名中
if function_name:
    safe_filename = f"{base_name}__{function_name}_report.json"
else:
    safe_filename = f"{base_name}_report.json"
    
original_output_file = original_output_dir / safe_filename
```

**修改後**:
```python
# 使用目錄前綴和檔案名稱（不包含函式名稱）
file_parts = file_path.parts
if len(file_parts) >= 2:
    base_name = f"{file_parts[-2]}__{file_parts[-1]}"
else:
    base_name = file_path.name

# 只使用檔案名稱，不加入函式名稱
safe_filename = f"{base_name}_report.json"
    
original_output_file = original_output_dir / safe_filename
```

#### 4. Semgrep 單檔掃描 (第 726-730 行)

**修改前**:
```python
# 如果有函式名稱，加入到檔案名中
if function_name:
    original_output_file = original_output_dir / f"{file_path.name}__{function_name}_report.json"
else:
    original_output_file = original_output_dir / f"{file_path.name}_report.json"
```

**修改後**:
```python
# 只使用檔案名稱（不包含函式名稱）
original_output_file = original_output_dir / f"{file_path.name}_report.json"
```

---

## 目錄結構範例

### 修改前的檔案結構
```
OriginalScanResult/
├── Bandit/
│   └── CWE-327/
│       └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
│           └── 第1輪/
│               ├── basic__test_onboarding.py__test_generate_pkce_codes()_report.json
│               ├── coders__base_coder.py__show_send_output()_report.json
│               └── coders__base_coder.py__check_for_file_mentions()_report.json
└── Semgrep/
    └── CWE-327/
        └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
            └── 第1輪/
                ├── basic__test_onboarding.py__test_generate_pkce_codes()_report.json
                ├── coders__base_coder.py__show_send_output()_report.json
                └── coders__base_coder.py__check_for_file_mentions()_report.json
```

### 修改後的檔案結構
```
OriginalScanResult/
├── Bandit/
│   └── CWE-327/
│       └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
│           └── 第1輪/
│               ├── basic__test_onboarding.py_report.json     ← 簡化
│               └── coders__base_coder.py_report.json         ← 簡化（覆蓋）
└── Semgrep/
    └── CWE-327/
        └── aider__CWE-327__CAL-ALL-6b42874e__M-call/
            └── 第1輪/
                ├── basic__test_onboarding.py_report.json     ← 簡化
                └── coders__base_coder.py_report.json         ← 簡化（覆蓋）
```

**注意**: 如果 `prompt.txt` 中同一個檔案有多個函式（如之前的問題），現在只會保留最後一次掃描的結果（檔案會被覆蓋）。但根據 [SCAN_PROMPT_MATCHING_FIX](SCAN_PROMPT_MATCHING_FIX_COMPLETE.md)，系統已經確保每行只處理第一個函式，所以不會有重複掃描同一檔案的情況。

---

## 影響分析

### ✅ 優點

1. **檔案名稱更簡潔**: 從 60+ 字元縮短到 30 字元左右
2. **避免特殊字元**: 移除括號 `()` 等特殊字元，提升跨平台相容性
3. **統一命名格式**: 所有報告檔案使用一致的 `{filename}_report.json` 格式
4. **簡化程式碼邏輯**: 移除 `if function_name` 條件判斷

### ⚠️ 注意事項

1. **檔案覆蓋行為**: 同一檔案的多次掃描會覆蓋之前的報告
   - **實際影響**: 無，因為系統已確保每個檔案在每輪只掃描一次
   - **參考**: [SCAN_PROMPT_MATCHING_FIX](SCAN_PROMPT_MATCHING_FIX_COMPLETE.md)

2. **歷史檔案不相容**: 舊的包含函式名稱的報告檔案不會自動更新
   - **建議**: 如需統一，可手動刪除舊的 `OriginalScanResult/` 目錄

3. **函式資訊查詢**: 無法從檔案名稱直接看出掃描的函式
   - **解決方案**: 查看 `CWE_Result/` 中的 CSV 檔案，有完整的 `當前函式名稱` 欄位
   - **解決方案 2**: 查看 JSON 報告內容，包含完整的函式級別漏洞資訊

---

## 相關系統整合

### 與 CSV 記錄的關係

CSV 檔案 (`CWE_Result/`) 仍然記錄完整資訊：

```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,aider/coders/base_coder.py,show_send_output(),2,45;47,bandit,HIGH,HIGH,Use of weak crypto,success,
1,2,tests/basic/test_onboarding.py,test_generate_pkce_codes(),0,,bandit,,,,success,
```

**重要**: 
- 原始 JSON 報告檔案名稱簡化（只含檔案名）
- CSV 記錄仍然包含完整的函式名稱資訊
- 兩者透過 `檔案路徑` + `輪數` + `行號` 關聯

### 與 Function Name Tracker 的關係

`function_name_tracker.py` 追蹤函式名稱變化，不受影響：

```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
aider/crypto.py,generate_fernet_key(),42,1,secure_key_generation(),42,2025-11-02 10:30:45
```

**獨立性**: 檔案命名簡化不影響函式名稱追蹤功能。

---

## 驗證方式

### 檢查修改是否生效

```bash
# 執行掃描後，檢查 OriginalScanResult 檔案名稱
find OriginalScanResult/ -name "*_report.json" | head -10

# 應該看到類似這樣的輸出（不含函式名稱）:
# OriginalScanResult/Bandit/CWE-327/project_name/第1輪/basic__test_onboarding.py_report.json
# OriginalScanResult/Bandit/CWE-327/project_name/第1輪/coders__base_coder.py_report.json

# 檢查是否還有舊格式（包含函式名稱和括號）
find OriginalScanResult/ -name "*()_report.json"

# 如果有輸出，表示是舊的報告檔案
```

### 清理舊檔案（可選）

```bash
# 如果想移除所有舊的報告檔案（包含函式名稱的）
find OriginalScanResult/ -name "*()_report.json" -delete

# 或者直接清空整個目錄
rm -rf OriginalScanResult/*
```

---

## 回退方式

如果需要恢復到包含函式名稱的命名方式，可以 revert 以下修改：

```bash
git diff HEAD src/cwe_detector.py  # 查看變更
git checkout HEAD -- src/cwe_detector.py  # 恢復檔案
```

或手動將程式碼中的：
```python
# 只使用檔案名稱，不加入函式名稱
safe_filename = f"{base_name}_report.json"
```

改回：
```python
# 如果有函式名稱，加入到檔案名中
if function_name:
    safe_filename = f"{base_name}__{function_name}_report.json"
else:
    safe_filename = f"{base_name}_report.json"
```

---

## 相關文件

- `src/cwe_detector.py` - CWE 掃描器主程式（包含檔案命名邏輯）
- `docs/SCAN_PROMPT_MATCHING_FIX_COMPLETE.md` - 掃描匹配修復說明
- `docs/CSV_HEADER_UPDATE_CURRENT_FUNCTION_NAME.md` - CSV 欄位更新說明
- `docs/SCAN_TIMING_ANALYSIS.md` - 掃描時機詳細分析

---

## 總結

此次更新簡化了 OriginalScanResult 中原始掃描報告的檔案命名：

1. ✅ **移除函式名稱**: 檔案名稱不再包含 `__{function_name}()` 部分
2. ✅ **統一命名格式**: 所有報告使用 `{filename}_report.json` 格式
3. ✅ **降低複雜度**: 檔案名稱更簡潔，避免特殊字元
4. ✅ **簡化程式碼**: 移除條件判斷邏輯

**重要提醒**: 
- CSV 記錄仍然包含完整的函式名稱資訊（`當前函式名稱` 欄位）
- JSON 報告內容不變，仍然包含函式級別的漏洞詳情
- 檔案命名簡化不影響掃描準確性和資料完整性
