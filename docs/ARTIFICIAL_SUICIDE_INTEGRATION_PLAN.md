# Artificial Suicide 整合方案

## 📋 整合任務清單

基於現有程式碼分析，以下是具體的整合步驟：

---

## 1. UI 整合（src/interaction_settings_ui.py）

### 修改位置
在 `create_widgets()` 方法中，「啟用多輪互動功能」勾選框後面新增：

```python
# Artificial Suicide 模式
self.artificial_suicide_var = tk.BooleanVar(value=False)
artificial_suicide_checkbox = ttk.Checkbutton(
    main_frame,
    text="⚠️ Artificial Suicide 模式（攻擊性測試）",
    variable=self.artificial_suicide_var,
    command=self.on_artificial_suicide_changed
)
artificial_suicide_checkbox.pack(anchor="w", pady=10)
```

### 新增方法
```python
def on_artificial_suicide_changed(self):
    """當 Artificial Suicide 模式改變時"""
    enabled = self.artificial_suicide_var.get()
    
    if enabled:
        # 禁用衝突的設定
        # 1. 提示詞來源設定
        for widget in prompt_source_frame.winfo_children():
            self.set_widget_state(widget, "disabled")
        
        # 2. 回應串接設定
        self.include_previous_var.set(False)
        chaining_checkbox.config(state="disabled")
        
        # 3. 修改結果處理設定
        for widget in modification_action_frame.winfo_children():
            self.set_widget_state(widget, "disabled")
    else:
        # 恢復設定
        ...
```

### 更新 save_and_close()
```python
def save_and_close(self):
    # 新增
    self.settings["artificial_suicide_mode"] = self.artificial_suicide_var.get()
    ...
```

---

## 2. CWE 掃描整合（src/cwe_scan_manager.py）

### 新增方法
在 `CWEScanManager` 類別中新增：

```python
def scan_and_append_to_csv(
    self,
    project_name: str,
    project_path: Path,
    round_num: int,
    line_num: int,
    target_file: str,
    target_function: str,
    target_cwe: str
) -> bool:
    """
    掃描單一函式並動態追加到 CSV
    
    Args:
        project_name: 專案名稱
        project_path: 專案路徑
        round_num: 輪數
        line_num: 行號
        target_file: 目標檔案（相對路徑）
        target_function: 目標函式名稱
        target_cwe: 目標 CWE 類型（例如："327"）
    
    Returns:
        bool: 掃描是否成功
    """
    try:
        # 1. 建立 FunctionTarget
        function_target = FunctionTarget(
            file_path=target_file,
            function_names=[target_function]
        )
        
        # 2. 掃描檔案
        scan_results = self.scan_files(
            project_path=project_path,
            file_paths=[target_file],
            cwe_type=target_cwe
        )
        
        # 3. 組織為字典
        results_dict = {target_file: scan_results[0]}
        
        # 4. 儲存到 CSV（追加模式）
        csv_dir = self.output_dir / f"CWE-{target_cwe}" / "Bandit" / project_name / f"第{round_num}輪"
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_file = csv_dir / f"{project_name}_function_level_scan.csv"
        
        self._save_function_level_csv(
            file_path=csv_file,
            function_targets=[function_target],
            scan_results=results_dict,
            round_number=round_num,
            line_number=line_num,
            scanner_filter='bandit',
            append_mode=True  # 關鍵：使用追加模式
        )
        
        # 5. 同樣處理 Semgrep（如果需要）
        ...
        
        return True
        
    except Exception as e:
        self.logger.error(f"掃描並追加 CSV 失敗: {e}")
        return False
```

---

## 3. VSCode 控制器擴展（src/vscode_controller.py）

### 新增方法：Keep 修改
```python
def open_new_chat_keep_modifications(self) -> bool:
    """
    開啟新 Copilot 對話但保留程式碼修改
    
    方案：不做任何事，直接開啟新對話
    Copilot Chat 的 Ctrl+L 只會清除對話記憶，不會撤銷程式碼
    
    Returns:
        bool: 操作是否成功
    """
    try:
        self.logger.info("開啟新 Copilot 對話（保留程式碼修改）")
        
        # 方法 1：使用 Ctrl+L 清除對話
        pyautogui.hotkey('ctrl', 'f1')  # 聚焦到 Chat
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'l')  # 清除對話
        time.sleep(1)
        
        return True
        
    except Exception as e:
        self.logger.error(f"開啟新對話（Keep）失敗: {e}")
        return False
```

### 新增方法：Undo 修改
```python
def open_new_chat_undo_modifications(self) -> bool:
    """
    開啟新 Copilot 對話並撤銷程式碼修改
    
    方案：使用 Ctrl+Z 多次撤銷
    
    Returns:
        bool: 操作是否成功
    """
    try:
        self.logger.info("開啟新 Copilot 對話（撤銷程式碼修改）")
        
        # 1. 聚焦到編輯器
        pyautogui.hotkey('ctrl', '1')  # 假設編輯器在第一個分組
        time.sleep(0.5)
        
        # 2. 執行多次 Undo（假設最多修改 10 個地方）
        for _ in range(10):
            pyautogui.hotkey('ctrl', 'z')
            time.sleep(0.2)
        
        # 3. 清除 Copilot 對話
        pyautogui.hotkey('ctrl', 'f1')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(1)
        
        return True
        
    except Exception as e:
        self.logger.error(f"開啟新對話（Undo）失敗: {e}")
        return False
```

---

## 4. Copilot Handler 擴展（src/copilot_handler.py）

### 確認可用方法
- ✅ `_send_prompt_with_content()` - 可直接使用
- ✅ `open_copilot_chat()` - 可直接使用
- ❓ 接收回應的方法 - 需要查看完整程式碼

### 可能需要新增
```python
def send_and_receive(self, prompt: str, use_smart_wait: bool = True) -> str:
    """
    發送 prompt 並接收回應
    
    Args:
        prompt: 要發送的 prompt
        use_smart_wait: 是否使用智能等待
    
    Returns:
        str: Copilot 回應內容
    """
    # 實作細節需要參考現有的 process_project_complete() 方法
    ...
```

---

## 5. Main.py 整合

### 修改 _execute_project_automation()
在 main.py 中，檢查是否啟用 Artificial Suicide 模式：

```python
def _execute_project_automation(self, project: ProjectInfo, project_logger) -> bool:
    try:
        # 檢查是否啟用 Artificial Suicide 模式
        if self.interaction_settings and self.interaction_settings.get("artificial_suicide_mode"):
            return self._execute_artificial_suicide_mode(project, project_logger)
        else:
            return self._execute_normal_mode(project, project_logger)
    except Exception as e:
        ...
```

### 新增方法
```python
def _execute_artificial_suicide_mode(self, project: ProjectInfo, project_logger) -> bool:
    """執行 Artificial Suicide 攻擊模式"""
    from src.ArtificialSuicide.manager import ArtificialSuicideManager
    
    # 從 CWE 設定中取得目標 CWE
    target_cwe = self.cwe_scan_settings.get("cwe_type", "327")
    
    # 從互動設定中取得輪數
    num_rounds = self.interaction_settings.get("max_rounds", 3)
    
    # 初始化 Manager
    manager = ArtificialSuicideManager(
        project_path=project.path,
        project_name=project.name,
        target_cwe=f"CWE-{target_cwe}",
        num_rounds=num_rounds,
        copilot_handler=self.copilot_handler,
        vscode_controller=self.vscode_controller,
        error_handler=self.error_handler,
        cwe_scan_manager=self.cwe_scan_manager
    )
    
    # 執行
    success = manager.execute()
    
    return success
```

---

## 📅 實作順序建議

1. **CWE 掃描整合**（優先，最簡單）
   - 新增 `scan_and_append_to_csv()` 方法
   - 測試追加功能

2. **UI 整合**
   - 新增 Artificial Suicide 勾選框
   - 實作禁用邏輯

3. **VSCode 控制器擴展**
   - 實作 Keep/Undo 方法
   - 測試撤銷功能

4. **Main.py 整合**
   - 連接所有模組
   - 完整流程測試

---

## 🧪 測試計畫

### 單元測試
- [ ] 測試 `scan_and_append_to_csv()` 追加功能
- [ ] 測試 UI 禁用邏輯
- [ ] 測試 Keep/Undo 對話功能

### 整合測試
- [ ] 單輪完整流程（1 個 prompt 行）
- [ ] 多輪完整流程（2+ 個 prompt 行）
- [ ] 驗證檔案結構正確性
- [ ] 驗證 CSV 內容正確性

---

**創建日期**: 2025-10-25  
**狀態**: 規劃完成，待實作 🛠️
