# Artificial Suicide 實作進度報告

## 2025-10-24 工作記錄

### ✅ 完成項目

1. **創建模組資料夾結構**
   - 建立 `src/ArtificialSuicide/` 資料夾
   - 建立 `__init__.py` 模組入口

2. **實作 AttackPromptGenerator** (`src/ArtificialSuicide/attack_prompt_generator.py`)
   - 載入三個模板檔案（initial_query.txt, following_query.txt, coding_instruction.txt）
   - 解析 prompt.txt 格式（檔案路徑|函式名稱）
   - 生成第 1 道和第 2 道程序的 prompt
   - 模板參數驗證功能

3. **實作 ArtificialSuicideResultManager** (`src/ArtificialSuicide/result_manager.py`)
   - 生成新的檔案結構路徑（第N輪/第N道/第N行_filename_function.md）
   - 儲存 Copilot 回應到對應位置
   - 驗證檔案結構完整性

4. **實作 ArtificialSuicideManager** (`src/ArtificialSuicide/manager.py`)
   - 多輪執行流程控制
   - 第 1 道程序（Query Phase）執行邏輯
   - 第 2 道程序（Coding Phase + Scan）執行邏輯
   - Keep/Undo 對話管理框架

5. **撰寫文檔**
   - `docs/ARTIFICIAL_SUICIDE_IMPLEMENTATION.md` - 技術設計文檔
   - `docs/ARTIFICIAL_SUICIDE_PROGRESS.md` - 進度追蹤報告

### 📋 現有程式碼分析（2025-10-25）

#### 1. `src/interaction_settings_ui.py` 分析
**結構**：
- 使用 Tkinter 建立 UI
- 支援滾動視窗（Canvas + Scrollbar）
- 載入/儲存設定到 settings.json
- 已有：互動輪數、回應串接、修改結果處理等選項

**需要修改**：
- 新增「Artificial Suicide 模式」勾選框
- 勾選後禁用衝突設定（提示詞來源、回應串接、修改結果處理）
- 新增變數：`self.artificial_suicide_var`
- 更新 `save_and_close()` 方法加入新設定

#### 2. `src/copilot_handler.py` 分析
**核心功能**：
- `_send_prompt_with_content()` - 發送 prompt 到 Copilot
- `_safe_clipboard_copy()` - 安全的剪貼簿操作
- `open_copilot_chat()` - 開啟 Copilot Chat（Ctrl+F1）
- 支援 Rate Limit 檢測和重試

**可用介面**：
- 已有完整的 Copilot 互動機制
- Artificial Suicide Manager 可直接調用現有方法
- 需要確認：如何接收並儲存 Copilot 回應

#### 3. `src/vscode_controller.py` 分析
**核心功能**：
- `open_project()` - 開啟專案
- `close_all_vscode_instances()` - 關閉 VSCode（Alt+F4）
- `clear_copilot_memory(modification_action)` - 清除 Copilot 記憶 ✅

**Keep/Undo 實作機制（已完成）**：
```python
# 在 clear_copilot_memory() 中
# 1. 執行 Ctrl+L 清除對話
# 2. 檢測是否出現 NewChat_Save 對話框
# 3. 根據 modification_action 參數：
#    - "keep": 按 left → right → enter（保留修改）
#    - "revert": 按 left → left → enter（復原修改）
```

**可直接使用**：
- `vscode_controller.clear_copilot_memory("keep")` - 保留修改
- `vscode_controller.clear_copilot_memory("revert")` - 復原修改

#### 4. `src/cwe_scan_manager.py` 分析
**現有功能**：
- `scan_files()` - 掃描多個檔案
- `_save_function_level_csv()` - 儲存函式級別掃描結果
- 已支援 `append_mode` 參數（True=追加，False=覆寫）✅
- CSV 格式：輪數、行號、檔案名稱_函式名稱、漏洞資訊等

**無需修改的原因**：
- 原本設計就是「每輪逐行掃描」，符合 Artificial Suicide 的需求
- 每輪只儲存一次 CSV（在第 2 道程序進行掃描）
- 輪數 + 行號的組合保證了唯一性，不會有衝突
- 現有的逐行掃描機制已經完美支援我們的需求

**Artificial Suicide 使用方式**：
```python
# 在第 2 道程序中，逐行調用現有的掃描方法
for line_num, prompt_line in enumerate(prompt_lines, start=1):
    # 解析目標
    target_file, filename, function_name = parse_prompt_line(prompt_line)
    
    # 使用現有方法掃描（會自動追加到 CSV）
    # 這裡直接調用 copilot_handler 或 cwe_scan_manager 的現有邏輯即可
```

---

### 📊 關鍵理解總結

1. **Keep/Undo 已實作** ✅
   - 透過 `vscode_controller.clear_copilot_memory(action)` 控制
   - `action="keep"` → 第 1 道和第 2 道之間使用
   - `action="revert"` → 每輪結束後使用

2. **CWE 掃描無需修改** ✅
   - 現有機制已經支援逐行掃描
   - 輪數 + 行號確保唯一性
   - 第 2 道程序進行掃描不會有衝突

3. **Copilot 互動可直接使用** ✅
   - `copilot_handler._send_prompt_with_content()` 發送 prompt
   - 等待回應和儲存的邏輯已經完整

---
