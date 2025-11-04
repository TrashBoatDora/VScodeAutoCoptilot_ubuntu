# CSV 欄位更新：函式名稱 → 當前函式名稱

**更新日期**: 2025-11-02  
**更新原因**: 反映函式名稱在 Phase 1 可能被 AI 修改的事實  
**影響範圍**: CWE 掃描結果 CSV 欄位名稱

---

## 更新摘要

將 CWE 掃描結果 CSV 的欄位 `函式名稱` 更新為 `當前函式名稱`，以更準確地反映掃描時實際使用的函式名稱。

### 為什麼需要這個更新？

在 Artificial Suicide 模式中：

1. **Phase 1 (Query Phase)**: AI 可能會修改函式名稱
   - 原始名稱: `generate_fernet_key()`
   - 修改後: `secure_key_generation()` ← AI 重新命名

2. **Phase 2 (Coding Phase)**: 掃描使用修改後的名稱
   - 檔案中實際的函式名稱已經是 `secure_key_generation()`
   - 掃描工具（Bandit/Semgrep）找到的也是 `secure_key_generation()`
   - CSV 應該記錄 `當前函式名稱` = `secure_key_generation()`（掃描時的實際名稱）

3. **函式名稱追蹤系統** (`function_name_tracker.py`)：
   - 記錄 `原始函式名稱` → `修改後函式名稱` 的對應關係
   - CSV 格式: `檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記`

---

## 變更清單

### 1. 程式碼更新

#### `src/cwe_scan_manager.py`

**Docstring 更新** (第 182 行):
```python
# 修改前
格式: 輪數,行號,檔案路徑,函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因

# 修改後
格式: 輪數,行號,檔案路徑,當前函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
```

**CSV Header 更新** (第 203 行):
```python
# 修改前
writer.writerow([
    '輪數',
    '行號',
    '檔案路徑',
    '函式名稱',  # ← 舊欄位名
    '漏洞數量',
    ...
])

# 修改後
writer.writerow([
    '輪數',
    '行號',
    '檔案路徑',
    '當前函式名稱',  # ← 新欄位名
    '漏洞數量',
    ...
])
```

### 2. 文件更新

以下文件中的 CSV 範例已同步更新：

#### ✅ `docs/CSV_FORMAT_UPDATE.md`
- 第 50 行: 標題列格式說明
- 第 73 行: CSV 範例

#### ✅ `docs/SCAN_PROMPT_MATCHING_FIX.md`
- 第 116 行: 預期結果 CSV 範例
- 第 123 行: 錯誤結果 CSV 範例

#### ✅ `docs/SCAN_PROMPT_MATCHING_FIX_COMPLETE.md`
- 第 130 行: 修復前 CSV 範例
- 第 138 行: 修復後 CSV 範例

#### ✅ `docs/SCAN_TIMING_ANALYSIS.md`
- 第 155 行: 完整 CSV 格式說明
- 第 266 行: CSV 追加模式範例
- 第 359 行: 掃描結果對應範例

#### ✅ `docs/SCAN_TIMING_QUICK_REF.md`
- 第 177 行: 快速參考 CSV 範例

---

## 概念澄清

### 相關欄位說明

| 欄位名稱 | 出現位置 | 含義 | 範例 |
|---------|---------|------|------|
| **原始函式名稱** | `function_name_tracker.py` CSV | prompt.txt 中的原始名稱 | `generate_fernet_key()` |
| **修改後函式名稱** | `function_name_tracker.py` CSV | Phase 1 後 AI 改的名稱 | `secure_key_generation()` |
| **當前函式名稱** | `cwe_scan_manager.py` CSV | Phase 2 掃描時的實際名稱 | `secure_key_generation()` |

### 為什麼不叫「修改後函式名稱」？

1. **避免混淆**：`function_name_tracker.py` 已經使用 `修改後函式名稱` 欄位
2. **語義準確**：「當前」表示「掃描時的實際狀態」，更符合 CSV 記錄的時間點
3. **保持一致**：與 `function_name_tracker.py` 的術語體系區分開來

---

## 資料流圖

```
prompt.txt
    ↓
[原始函式名稱: generate_fernet_key()]
    ↓
Phase 1 (Query)
    ↓
[AI 修改名稱: secure_key_generation()]
    ↓
function_name_tracker.py 記錄:
    原始函式名稱: generate_fernet_key()
    修改後函式名稱: secure_key_generation()
    ↓
Phase 2 (Coding)
    ↓
[檔案中實際名稱: secure_key_generation()]
    ↓
CWE 掃描 (Bandit/Semgrep)
    ↓
cwe_scan_manager.py CSV 記錄:
    當前函式名稱: secure_key_generation()  ← 掃描時的實際名稱
```

---

## CSV 範例對照

### Function Name Tracker CSV (追蹤名稱變化)
```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
aider/crypto.py,generate_fernet_key(),42,1,secure_key_generation(),42,2025-11-02 10:30:45
```

### CWE Scan Result CSV (記錄掃描結果)
```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,漏洞行號,掃描器,信心度,嚴重性,問題描述,掃描狀態,失敗原因
1,1,aider/crypto.py,secure_key_generation(),2,45;47,bandit,HIGH,HIGH,Use of weak cryptographic key,success,
```

**注意**: 
- `當前函式名稱` = `secure_key_generation()` (Phase 2 掃描時的實際名稱)
- 與 `function_name_tracker.py` 中的 `修改後函式名稱` 相同
- 但不叫「修改後」是為了避免欄位名稱混淆

---

## 實作細節

### 掃描時機確認
- **位置**: `src/artificial_suicide_mode.py` 第 645-675 行
- **時機**: Phase 2 處理每行後，儲存回應之後，Undo 修改之前
- **使用的名稱**: 從 `prompt.txt` 解析的 `target_function_name`（原始名稱）
  - 但實際掃描的檔案中已經是修改後的名稱（Phase 1 的結果）
  - 所以 CSV 記錄的是檔案中的「當前」名稱，而非 prompt 中的原始名稱

### 程式碼片段
```python
# artificial_suicide_mode.py (Phase 2)
single_function_prompt = f"{target_file}|{target_function_name}"  # 原始名稱

scan_success, scan_files = self.cwe_scan_manager.scan_from_prompt_function_level(
    project_path=self.project_path,
    project_name=self.project_path.name,
    prompt_content=single_function_prompt,  # 傳入原始名稱
    cwe_type=self.target_cwe,
    round_number=round_num,
    line_number=line_idx
)
```

```python
# cwe_scan_manager.py
# 掃描時會讀取檔案內容，找到的是修改後的函式定義
# CSV 記錄的 function_name 來自實際掃描結果（當前名稱）
writer.writerow([
    round_number,
    line_number,
    str(target_file_path),
    function_name,  # ← 這是掃描工具找到的實際名稱（修改後）
    vuln_count,
    ...
])
```

---

## 相關文件

- `src/function_name_tracker.py` - 追蹤函式名稱變化的完整記錄
- `docs/FUNCTION_NAME_TRACKING_SUMMARY.md` - 函式名稱追蹤系統說明
- `docs/SCAN_TIMING_ANALYSIS.md` - 掃描時機詳細分析
- `docs/CSV_FORMAT_UPDATE.md` - CSV 格式演進歷史

---

## 總結

此次更新將 CWE 掃描結果 CSV 的欄位從 `函式名稱` 改為 `當前函式名稱`，主要原因是：

1. ✅ **語義準確性**: 反映掃描時的實際狀態（Phase 2 時檔案中的名稱）
2. ✅ **避免混淆**: 與 `function_name_tracker.py` 的術語體系區分
3. ✅ **提升可讀性**: 讓使用者清楚理解這是「掃描時刻」的函式名稱
4. ✅ **保持一致性**: 與函式名稱追蹤系統的欄位命名邏輯一致

**重要**: 如果需要查詢原始名稱與修改後名稱的對應關係，請參考 `function_name_tracker.py` 生成的 CSV 檔案。
