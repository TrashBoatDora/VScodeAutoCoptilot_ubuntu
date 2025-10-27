# Artificial Suicide 攻擊模式實作文檔

## 📋 專案概述

**Artificial Suicide** 是一個針對 Copilot AI 程式碼補全功能的對抗性測試模式，旨在驗證透過精心設計的提示詞（Prompt），是否能誘導 AI 生成違反特定 CWE 安全準則的程式碼。

---

## 🎯 核心概念

### 攻擊原理
通過兩階段的提示詞注入：
1. **第 1 道程序（Query Phase）**：要求 AI 修改函式命名和變數命名，但不改變邏輯，使命名具有誘導性
2. **第 2 道程序（Coding Phase）**：基於修改後的命名，要求 AI 實作完整的函式程式碼

### 驗證機制
- 使用 Bandit 和 Semgrep 對生成的程式碼進行 CWE 漏洞掃描
- 動態記錄每輪、每行的掃描結果
- 比對攻擊前後的漏洞變化

---

## 🔄 執行流程

### 整體架構
```
for round in range(1, num_rounds + 1):
    # === 第 1 道程序：誘導命名修改 ===
    for each line in prompt.txt:
        1. 讀取模板（第1輪用 initial_query.txt，第2+輪用 following_query.txt）
        2. 填入參數：{target_file}, {target_function_name}, {CWE-XXX}
        3. 發送給 Copilot
        4. 儲存回應到：ExecutionResult/Success/{project}/第N輪/第1道/第N行_{file}_{func}.md
    
    開啟新 Copilot 對話（Keep 修改）
    
    # === 第 2 道程序：實作程式碼 + 掃描 ===
    for each line in prompt.txt:
        1. 讀取模板（coding_instruction.txt）
        2. 填入參數：{target_file}, {target_function_name}
        3. 發送給 Copilot
        4. 儲存回應到：ExecutionResult/Success/{project}/第N輪/第2道/第N行_{file}_{func}.md
        5. 執行 CWE 掃描，動態追加到 CSV
    
    開啟新 Copilot 對話（Undo 修改）
```

---

## 📂 檔案結構設計

### ExecutionResult 結構
```
ExecutionResult/Success/
└── {project_name}/
    ├── 第1輪/
    │   ├── 第1道/
    │   │   ├── 第1行_helpers.py_get_domain_name_hash.md
    │   │   └── 第2行_test_helpers.py_test_get_domain_name_hash.md
    │   └── 第2道/
    │       ├── 第1行_helpers.py_get_domain_name_hash.md
    │       └── 第2行_test_helpers.py_test_get_domain_name_hash.md
    ├── 第2輪/
    │   ├── 第1道/
    │   └── 第2道/
    └── 第3輪/
        ├── 第1道/
        └── 第2道/
```

### CWE_Result 結構（動態追加 CSV）
```
CWE_Result/
└── CWE-327/
    ├── Bandit/
    │   └── {project_name}/
    │       ├── 第1輪/
    │       │   └── {project_name}_function_level_scan.csv
    │       │       ├─ Row 1: Line 1 掃描結果
    │       │       ├─ Row 2: Line 2 掃描結果
    │       │       └─ ...（動態新增）
    │       ├── 第2輪/
    │       └── 第3輪/
    └── Semgrep/
        └── （同上）
```

### OriginalScanResult 結構
```
OriginalScanResult/
├── Bandit/
│   └── {project_name}_original_scan.json
└── Semgrep/
    └── {project_name}_original_scan.json
```

---

## 🎨 UI 設計

### 新增選項
在「Copilot多輪互動設定」UI 中新增：

```
☐ Artificial Suicide 模式（攻擊性測試）
```

### 互動邏輯
- **勾選後**：
  - 提示詞設定（逐行/批次發送）→ **禁用（灰色）**
  - 回應串接設定 → **禁用（灰色）**
  - CopilotChat修改結果設定（Keep/Undo）→ **禁用（灰色）**
  
- **原因**：Artificial Suicide 模式有固定的執行流程，不需要這些設定

---

## 🛠️ 技術實作

### 新增模組

#### 1. `src/attack_prompt_generator.py`
**功能**：
- 載入三個模板檔案（`initial_query.txt`, `following_query.txt`, `coding_instruction.txt`）
- 解析 `prompt.txt` 提取 `{target_file}` 和 `{target_function_name}`
- 根據輪數生成對應的 prompt

**主要方法**：
```python
def parse_prompt_line(line: str) -> Tuple[str, str, str]
def generate_query_prompt(round_num, target_file, target_function, target_cwe, last_response) -> str
def generate_coding_prompt(target_file, target_function) -> str
```

---

#### 2. `src/artificial_suicide_result_manager.py`
**功能**：
- 管理新的檔案結構（第N輪/第N道/第N行_file_func.md）
- 儲存 Copilot 回應

**主要方法**：
```python
def get_response_path(round_num, phase, line_num, filename, function_name) -> str
def save_response(response, round_num, phase, line_num, ...) -> None
```

---

#### 3. `src/artificial_suicide_manager.py`
**功能**：
- 核心流程控制器
- 管理多輪執行、兩道程序、Keep/Undo 對話

**主要方法**：
```python
def execute() -> None
def _execute_phase1(round_num) -> None  # 第 1 道程序
def _execute_phase2(round_num) -> None  # 第 2 道程序
```

---

### 修改現有模組

#### 1. `src/cwe_scan_manager.py`
**新增方法**：
```python
def scan_and_append_to_csv(
    project_name: str,
    round_num: int,
    line_num: int,
    target_file: str,
    target_function: str,
    target_cwe: str
) -> None
```

**功能**：
- 掃描指定函式
- 將結果動態追加到對應輪數的 CSV 檔案
- 確保 CSV 標頭只寫入一次

---

#### 2. `src/interaction_settings_ui.py`
**新增 UI 元件**：
```python
self.artificial_suicide_var = tk.BooleanVar(value=False)
self.artificial_suicide_check = ttk.Checkbutton(...)
```

**新增方法**：
```python
def _toggle_artificial_suicide_mode() -> None
```

---

#### 3. `main.py`
**修改執行邏輯**：
```python
if interaction_settings.get("artificial_suicide_mode"):
    # 使用 ArtificialSuicideManager
    manager = ArtificialSuicideManager(...)
    manager.execute()
else:
    # 使用原有流程
    self._execute_project_automation(...)
```

---

## 📊 參數說明

### 模板參數

#### `initial_query.txt` / `following_query.txt`
- `{target_file}`: 目標檔案路徑（例如：`aider/onboarding.py`）
- `{target_function_name}`: 目標函式名稱（例如：`generate_pkce_codes`）
- `{CWE-XXX}`: 目標 CWE 類型（例如：`CWE-327`）
- `{Last_Response}`: 上一輪的回應內容（僅 `following_query.txt` 需要，暫時略過）

#### `coding_instruction.txt`
- `{target_file}`: 目標檔案路徑
- `{target_function_name}`: 目標函式名稱

---

## 🔐 安全性考量

### Keep vs Undo 修改
- **Keep 修改**：在第 1 道和第 2 道之間，保留 AI 建議的命名修改，讓第 2 道基於誘導性命名生成程式碼
- **Undo 修改**：在每輪結束後，撤銷所有程式碼修改，恢復原始狀態，避免影響下一輪

### 掃描時機
- 只在**第 2 道程序**進行掃描（因為此時才有實際的程式碼生成）
- 每行 prompt 處理完畢後，立即掃描並追加到 CSV

---

## 📈 預期成果

### 成功指標
1. **檔案結構正確**：所有回應檔案按照規定格式儲存
2. **CSV 動態追加**：每輪的 CSV 包含所有行的掃描結果，無重複標頭
3. **模板參數正確**：所有 `{...}` 參數都被正確填入
4. **掃描結果有效**：能夠檢測到 AI 生成的 CWE 漏洞

### 驗證方式
1. 檢查 `ExecutionResult/Success/{project}/第N輪/第N道/` 的檔案數量和命名
2. 檢查 `CWE_Result/CWE-XXX/Bandit/{project}/第N輪/*.csv` 的行數（應等於 prompt.txt 的行數）
3. 手動查看生成的程式碼，確認是否包含不安全的 API 調用

---

## 🚧 已知限制

### 當前版本限制
1. **`{Last_Response}` 暫未實作**：`following_query.txt` 中的上一輪回應串接功能待後續實作
2. **單專案執行**：目前專注於單一專案的完整流程，批次處理待後續優化
3. **手動驗證**：攻擊成功與否目前需要手動查看 CSV 和程式碼，自動化驗證待實作

---

## 📅 實作時程

### Phase 1: 核心模組開發（預計 2 小時）
- ✅ 任務描述文檔
- ⏳ AttackPromptGenerator
- ⏳ ArtificialSuicideResultManager
- ⏳ ArtificialSuicideManager

### Phase 2: 整合與修改（預計 1.5 小時）
- ⏳ 修改 CWEScanManager
- ⏳ 修改 UI
- ⏳ 修改 main.py

### Phase 3: 測試與驗證（預計 1 小時）
- ⏳ 單輪測試
- ⏳ 多輪測試
- ⏳ 完整流程驗證

---

## 📝 參考資料

- 模板檔案位置：`assets/prompt-template/`
- 現有掃描結果範例：`CWE_Result/CWE-327/`
- 現有回應檔案範例：`ExecutionResult/Success/localstack__CWE-327__CAL-ALL-6b42874e__M-call/`

---

**文檔版本**: 1.0  
**創建日期**: 2025-10-24  
**作者**: GitHub Copilot Assistant  
**狀態**: 實作中 🚧
