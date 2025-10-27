# VSCode Controller 簡化說明

## 📋 簡化日期
2025-10-26

## 🎯 簡化目標
將 `vscode_controller.py` 從 443 行簡化為 209 行，移除所有不必要的複雜邏輯。

## ✅ 移除的內容

### 1. **PID 監控機制** ❌
- 移除 `psutil` 依賴
- 移除 `pre_existing_vscode_pids` 追蹤
- 移除 `is_vscode_running()` 方法
- 移除 `vscode_process` 變數

**原因**：不需要追蹤進程，只需要開啟和關閉視窗即可。

### 2. **複雜的關閉方法** ❌
- 移除 `close_all_vscode_instances()` 方法（使用 Alt+F4）
- 移除 `ensure_clean_environment()` 方法
- 移除 `restart_vscode()` 方法

**原因**：統一使用 `Ctrl+W` 關閉當前視窗，不需要關閉所有實例。

### 3. **視窗焦點管理** ❌
- 移除 `focus_vscode_window()` 方法
- 移除 `_maximize_window_direct()` 方法
- 移除複雜的焦點切換邏輯

**原因**：直接在開啟時最大化即可，不需要額外的焦點管理。

### 4. **等待與驗證機制** ❌
- 移除 `wait_for_vscode_ready()` 方法
- 移除多次檢查 VS Code 是否啟動的循環
- 移除複雜的驗證邏輯

**原因**：只需要簡單等待固定時間即可。

### 5. **其他輔助方法** ❌
- 移除 `save_all_files()` 方法
- 移除 `vscode_ui_initializer` 依賴

**原因**：不需要這些額外功能。

## ✨ 保留的核心功能

### 1. **開啟專案** ✅
```python
def open_project(self, project_path: str, wait_for_load: bool = True) -> bool:
    # 1. 檢查路徑
    # 2. 使用命令列開啟
    # 3. 等待載入
    # 4. 最大化視窗
```

### 2. **關閉專案** ✅
```python
def close_current_project(self) -> bool:
    # 統一使用 Ctrl+W 關閉當前視窗
    pyautogui.hotkey('ctrl', 'w')
```

### 3. **清除 Copilot 記憶** ✅
```python
def clear_copilot_memory(self, modification_action: str = "keep") -> bool:
    # 執行清除記憶命令序列
    # 處理保存對話提示
```

### 4. **取得專案資訊** ✅
```python
def get_current_project_info(self) -> Optional[dict]:
    # 返回專案名稱、路徑、是否存在
```

## 🔧 統一的關閉方法

### 之前（混亂）：
- `close_all_vscode_instances()` 使用 `Alt+F4`
- `close_current_project()` 使用 `Ctrl+W`
- `ensure_clean_environment()` 檢查後關閉

### 之後（簡化）：
- **只有** `close_current_project()` 使用 `Ctrl+W`
- **效果**：只關閉當前專案視窗，不影響其他 VS Code 視窗

## 📊 簡化效果

| 項目 | 之前 | 之後 | 改善 |
|------|------|------|------|
| 程式碼行數 | 443 行 | 209 行 | -52.8% |
| 方法數量 | 15 個 | 4 個 | -73.3% |
| 依賴套件 | psutil + 其他 | 只有基本套件 | 更輕量 |
| 複雜度 | 高（PID 追蹤、多次驗證）| 低（簡單流程）| 大幅降低 |

## 🎯 執行流程

### 簡化後的流程：
```
1. 開啟專案
   ↓
2. 等待 VS Code 載入（固定時間）
   ↓
3. 最大化視窗
   ↓
4. 清除 Copilot 記憶
   ↓
5. 處理 Copilot Chat（Artificial Suicide 或一般模式）
   ↓
6. 關閉當前專案視窗（Ctrl+W）
   ↓
7. 繼續下一個專案
```

## ✅ 修正的問題

1. **關閉視窗問題**：之前 `close_current_project()` 會調用 `close_all_vscode_instances()`，導致關閉所有 VS Code 視窗（包括執行腳本的視窗）
2. **複雜性問題**：移除不必要的 PID 追蹤和驗證機制
3. **一致性問題**：統一使用 `Ctrl+W` 作為關閉方法

## 🚀 優勢

1. **更簡單**：程式碼減少一半以上
2. **更可靠**：移除複雜的進程監控，減少出錯機會
3. **更快速**：不需要多次檢查和驗證
4. **更明確**：流程清晰，容易理解和維護

## 📝 注意事項

1. 不再追蹤 VS Code 進程 PID
2. 不再驗證 VS Code 是否真的啟動
3. 只依賴固定的等待時間
4. 使用 `Ctrl+W` 關閉視窗（不會影響其他視窗）

## 🔄 向後相容性

所有對外的介面保持不變：
- `open_project(project_path, wait_for_load=True)`
- `close_current_project()`
- `clear_copilot_memory(modification_action="keep")`
- `get_current_project_info()`

便捷函數也保持相同：
- `open_project()`
- `close_current_project()`
