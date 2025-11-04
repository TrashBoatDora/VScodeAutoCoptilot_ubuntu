# Phase 2 檔案命名使用修改後的函式名稱

**更新日期**: 2025-11-02  
**更新原因**: Phase 2 的檔案命名應使用 Phase 1 修改後的函式名稱，而非原始名稱  
**影響範圍**: `ExecutionResult/Success/` 中 Phase 2 (Coding Phase) 的回應檔案命名

---

## 更新摘要

在 Artificial Suicide 模式中，Phase 1 (Query Phase) 可能會修改函式名稱。Phase 2 (Coding Phase) 的檔案命名現在會**動態使用修改後的函式名稱**，而非原始名稱。

### 問題描述

#### 修改前的行為

| 階段 | Prompt 中的函式 | 實際檔案中的函式 | 檔案命名使用 | ❌ 問題 |
|-----|---------------|----------------|------------|---------|
| Phase 1 | `generate_fernet_key()` | `generate_fernet_key()` | `generate_fernet_key()` | ✅ 正確 |
| Phase 1 結束 | - | **AI 改名為** `secure_key_gen()` | - | - |
| Phase 2 | `generate_fernet_key()` | `secure_key_gen()` | `generate_fernet_key()` | ❌ **不一致** |

**問題**：
- Phase 2 的檔案名稱使用原始名稱 `generate_fernet_key()`
- 但實際檔案中的函式已改名為 `secure_key_gen()`
- 造成檔案名稱與實際內容不符

#### 修改後的行為

| 階段 | Prompt 中的函式 | 實際檔案中的函式 | 檔案命名使用 | ✅ 改善 |
|-----|---------------|----------------|------------|---------|
| Phase 1 | `generate_fernet_key()` | `generate_fernet_key()` | `generate_fernet_key()` | ✅ 正確 |
| Phase 1 結束 | - | **AI 改名為** `secure_key_gen()` | - | - |
| Phase 2 | `generate_fernet_key()` | `secure_key_gen()` | `secure_key_gen()` | ✅ **一致** |

**改善**：
- Phase 2 自動從 `function_name_tracker` 取得修改後的名稱
- 檔案名稱與實際函式名稱一致
- 更容易追蹤和理解執行結果

---

## 變更清單

### 程式碼修改

檔案: `src/artificial_suicide_mode.py`

#### 1. Phase 2 開始前取得修改後的函式名稱 (第 558-569 行)

**新增邏輯**:
```python
for line_idx, line in enumerate(self.prompt_lines, start=1):
    # 解析 prompt 行
    target_file, target_function_name = self._parse_prompt_line(line)
    if not target_file or not target_function_name:
        self.logger.error(f"  ❌ 第 {line_idx} 行格式錯誤")
        failed_lines.append(line_idx)
        continue
    
    # === 取得修改後的函式名稱（如果 Phase 1 有修改）===
    current_function_name = target_function_name  # 預設使用原始名稱
    if self.function_name_tracker:
        # 嘗試從追蹤器取得修改後的名稱
        modified_name, _ = self.function_name_tracker.get_function_name_for_round(
            target_file, target_function_name, round_num
        )
        if modified_name:
            current_function_name = modified_name
            self.logger.debug(f"  📝 使用修改後的函式名稱: {target_function_name} → {current_function_name}")
        else:
            self.logger.debug(f"  📝 Phase 1 未修改函式名稱，使用原始名稱: {target_function_name}")
    
    # 後續處理使用 current_function_name...
```

**說明**:
- ✅ 從 `function_name_tracker` 查詢是否有修改後的名稱
- ✅ 如果有，使用修改後的名稱 (`current_function_name`)
- ✅ 如果沒有，保持使用原始名稱
- ✅ 記錄 debug 日誌，方便追蹤

#### 2. 儲存回應時使用修改後的函式名稱 (第 647 行)

**修改前**:
```python
save_success = self.copilot_handler.save_response_to_file(
    project_path=str(self.project_path),
    response=response,
    is_success=True,
    round_number=round_num,
    phase_number=2,  # 第 2 道
    line_number=line_idx,
    filename=filename,
    function_name=target_function_name,  # ❌ 使用原始名稱
    prompt_text=coding_prompt,
    total_lines=len(self.prompt_lines),
    retry_count=retry_count
)
```

**修改後**:
```python
save_success = self.copilot_handler.save_response_to_file(
    project_path=str(self.project_path),
    response=response,
    is_success=True,
    round_number=round_num,
    phase_number=2,  # 第 2 道
    line_number=line_idx,
    filename=filename,
    function_name=current_function_name,  # ✅ 使用修改後的函式名稱
    prompt_text=coding_prompt,
    total_lines=len(self.prompt_lines),
    retry_count=retry_count
)
```

**說明**:
- ✅ 將 `target_function_name` 改為 `current_function_name`
- ✅ 檔案命名自動反映 Phase 1 的修改結果

---

## 實際效果

### 範例 1: AI 修改了函式名稱

**prompt.txt**:
```
crypto/utils.py|generate_fernet_key()
```

**Phase 1 執行**:
- AI 將函式改名為 `secure_key_generation()`
- `function_name_tracker` 記錄: `generate_fernet_key()` → `secure_key_generation()`

**檔案命名結果**:

| 階段 | 檔案名稱 | 說明 |
|-----|---------|------|
| Phase 1 (Query) | `第1行_crypto__utils.py_generate_fernet_key().md` | ✅ 使用原始名稱（此時還沒改） |
| Phase 2 (Coding) | `第1行_crypto__utils.py_secure_key_generation().md` | ✅ 使用修改後的名稱 |

### 範例 2: AI 沒有修改函式名稱

**prompt.txt**:
```
auth/login.py|authenticate_user()
```

**Phase 1 執行**:
- AI 沒有修改函式名稱
- `function_name_tracker` 沒有記錄變更

**檔案命名結果**:

| 階段 | 檔案名稱 | 說明 |
|-----|---------|------|
| Phase 1 (Query) | `第1行_auth__login.py_authenticate_user().md` | ✅ 使用原始名稱 |
| Phase 2 (Coding) | `第1行_auth__login.py_authenticate_user().md` | ✅ 仍使用原始名稱（因為沒改） |

---

## 目錄結構範例

### 修改前（名稱不一致）
```
ExecutionResult/Success/aider__CWE-327/第1輪/
├── 第1道/  (Query Phase)
│   └── 第1行_crypto__utils.py_generate_fernet_key().md  ← 原始名稱
└── 第2道/  (Coding Phase)
    └── 第1行_crypto__utils.py_generate_fernet_key().md  ← ❌ 還是原始名稱（但實際已改名）
```

**問題**：從檔案名稱看不出函式已經被改名

### 修改後（名稱一致）
```
ExecutionResult/Success/aider__CWE-327/第1輪/
├── 第1道/  (Query Phase)
│   └── 第1行_crypto__utils.py_generate_fernet_key().md  ← 原始名稱
└── 第2道/  (Coding Phase)
    └── 第1行_crypto__utils.py_secure_key_generation().md  ← ✅ 修改後的名稱
```

**改善**：檔案名稱清楚反映函式已被改名

---

## 日誌輸出變更

### 修改前
```log
  處理第 1/42 行: crypto/utils.py|generate_fernet_key()
  ✅ 第 1 行回應完整
  ✅ Copilot 儲存回應 - 檔案: 第1行_crypto__utils.py_generate_fernet_key().md
```

### 修改後（有修改名稱）
```log
  處理第 1/42 行: crypto/utils.py|generate_fernet_key()
  📝 使用修改後的函式名稱: generate_fernet_key() → secure_key_generation()
  ✅ 第 1 行回應完整
  ✅ Copilot 儲存回應 - 檔案: 第1行_crypto__utils.py_secure_key_generation().md
```

### 修改後（沒有修改名稱）
```log
  處理第 1/42 行: auth/login.py|authenticate_user()
  📝 Phase 1 未修改函式名稱，使用原始名稱: authenticate_user()
  ✅ 第 1 行回應完整
  ✅ Copilot 儲存回應 - 檔案: 第1行_auth__login.py_authenticate_user().md
```

---

## 與其他系統的整合

### 與 function_name_tracker 的關係

**function_name_tracker.py** 記錄函式名稱變化：

```csv
檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
crypto/utils.py,generate_fernet_key(),15,1,secure_key_generation(),15,2025-11-02 14:30:00
```

**Phase 2 檔案命名**:
```
第1行_crypto__utils.py_secure_key_generation().md
                      ^^^^^^^^^^^^^^^^^^^^^^^^^ (從 tracker 查詢得到)
```

**資料流**:
1. Phase 1 結束後，`function_name_tracker` 記錄變更
2. Phase 2 開始前，從 `function_name_tracker` 查詢修改後的名稱
3. Phase 2 檔案命名使用查詢到的名稱

### 與 CWE 掃描的關係

CWE 掃描 CSV 記錄**當前函式名稱**（修改後）：

```csv
輪數,行號,檔案路徑,當前函式名稱,漏洞數量,...
1,1,crypto/utils.py,secure_key_generation(),2,...
```

**一致性**:
- Phase 2 檔案名稱 = `secure_key_generation()`
- CWE 掃描記錄 = `secure_key_generation()`
- 兩者完全一致 ✅

---

## 特殊情況處理

### 情況 1: function_name_tracker 未啟用

如果 `self.function_name_tracker` 為 `None`：

```python
current_function_name = target_function_name  # 預設使用原始名稱
if self.function_name_tracker:
    # 這段不會執行
    ...
# current_function_name 保持為原始名稱
```

**結果**: Phase 2 檔案仍使用原始名稱（向後相容）

### 情況 2: Phase 1 沒有記錄（查詢失敗）

如果 `get_function_name_for_round()` 返回 `None`：

```python
modified_name, _ = self.function_name_tracker.get_function_name_for_round(
    target_file, target_function_name, round_num
)
if modified_name:  # None -> False
    current_function_name = modified_name
else:
    # 執行這裡，使用原始名稱
    self.logger.debug(f"  📝 Phase 1 未修改函式名稱，使用原始名稱: {target_function_name}")
```

**結果**: 使用原始名稱（安全回退）

### 情況 3: 多輪執行

**第 1 輪**:
- Phase 1: `generate_fernet_key()` → `secure_key_gen()` (第一次改名)
- Phase 2 檔案: `第1行_crypto__utils.py_secure_key_gen().md`

**第 2 輪**:
- Phase 1: `secure_key_gen()` → `crypto_key_generator()` (第二次改名)
- Phase 2 檔案: `第1行_crypto__utils.py_crypto_key_generator().md`

**說明**: 每輪都會查詢該輪的修改後名稱，支援多輪變更

---

## 影響分析

### ✅ 優點

1. **名稱一致性**: Phase 2 檔案名稱與實際函式名稱一致
2. **易於追蹤**: 從檔案名稱可看出函式是否被改名
3. **改善可讀性**: 不需要查看 `function_name_tracker` 就能了解當前狀態
4. **自動化**: 無需手動更新，系統自動查詢並使用修改後的名稱
5. **向後相容**: 如果沒有修改，仍使用原始名稱（行為不變）

### ⚠️ 注意事項

1. **Phase 1 與 Phase 2 檔案名稱可能不同**: 這是**預期行為**，反映函式名稱的變化
2. **依賴 function_name_tracker**: 如果追蹤器故障，會回退到使用原始名稱
3. **日誌級別**: 使用 `debug` 級別記錄，需要開啟 DEBUG 模式才能看到詳細日誌

---

## 驗證方式

### 檢查修改是否生效

執行 Artificial Suicide 模式後，檢查檔案名稱：

```bash
# 檢查同一行的 Phase 1 和 Phase 2 檔案
ls -la ExecutionResult/Success/*/第1輪/第1道/第1行*.md
ls -la ExecutionResult/Success/*/第1輪/第2道/第1行*.md

# 如果函式名稱不同，表示修改生效
# Phase 1: 第1行_crypto__utils.py_generate_fernet_key().md
# Phase 2: 第1行_crypto__utils.py_secure_key_generation().md
```

### 檢查日誌輸出

```bash
# 查看最新的日誌檔案
tail -f logs/automation__*.log | grep "使用修改後的函式名稱"

# 應該看到：
# 📝 使用修改後的函式名稱: generate_fernet_key() → secure_key_generation()
```

### 比對 function_name_tracker

```bash
# 查看 function_name_tracker 記錄
cat Function_Name_Changes/*/function_name_changes.csv

# 範例輸出：
# 檔案路徑,原始函式名稱,原始行號,輪數,修改後函式名稱,修改後行號,時間戳記
# crypto/utils.py,generate_fernet_key(),15,1,secure_key_generation(),15,2025-11-02 14:30:00

# Phase 2 檔案名稱應該使用 "修改後函式名稱" 欄位的值
```

---

## 相關文件

- `src/artificial_suicide_mode.py` - AS 模式主程式（包含 Phase 2 檔案命名邏輯）
- `src/function_name_tracker.py` - 函式名稱追蹤器（記錄名稱變更）
- `docs/EXECUTION_RESULT_FILENAME_WITH_PATH.md` - 檔案路徑命名說明
- `docs/FUNCTION_NAME_TRACKING_SUMMARY.md` - 函式名稱追蹤系統說明

---

## 總結

此次更新讓 Phase 2 (Coding Phase) 的檔案命名**動態使用修改後的函式名稱**：

1. ✅ **查詢追蹤器**: 從 `function_name_tracker` 查詢是否有修改後的名稱
2. ✅ **動態使用**: 如果有修改，使用修改後的名稱；如果沒有，使用原始名稱
3. ✅ **名稱一致**: Phase 2 檔案名稱與實際函式名稱一致
4. ✅ **記錄日誌**: Debug 日誌記錄名稱使用情況
5. ✅ **向後相容**: 沒有 tracker 或沒有修改時，仍使用原始名稱

**重要提醒**: 
- Phase 1 仍然使用**原始函式名稱**（因為此時還沒改）
- Phase 2 使用**修改後的函式名稱**（如果 Phase 1 有改的話）
- 這種差異是**預期行為**，反映了函式名稱的演變過程
