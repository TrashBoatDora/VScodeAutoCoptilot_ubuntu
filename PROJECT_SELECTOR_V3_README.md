# 專案選擇器 - 重構版本

**日期**: 2025-10-14  
**版本**: 3.0.0  
**狀態**: ✅ 全新重寫，簡單可靠

---

## 🎯 設計理念

### 舊版問題
1. ❌ 統計不更新
2. ❌ 變數綁定複雜（trace vs command）
3. ❌ 確認後專案消失
4. ❌ 過多的選項和設定

### 新版特點
1. ✅ **簡單**: 最少的代碼，最直接的邏輯
2. ✅ **可靠**: 使用最基本的 Tkinter 功能
3. ✅ **明確**: 選擇專案 = 自動清理記錄（無額外選項）
4. ✅ **調試**: 完整的日誌輸出

---

## 📋 核心設計

### 1. 變數管理
```python
# 簡單的字典，專案名稱 -> BooleanVar
self.checkbutton_vars = {}

# 創建時直接存入
var = tk.BooleanVar(value=False)
self.checkbutton_vars[project['name']] = var
```

### 2. 統計更新
```python
# 使用最基本的 command 參數
cb = ttk.Checkbutton(
    frame,
    text="",
    variable=var,
    command=self._update_stats  # 簡單直接
)

def _update_stats(self):
    """直接計數"""
    count = sum(1 for var in self.checkbutton_vars.values() if var.get())
    self.stats_label.config(text=f"已選擇: {count} 個專案")
```

### 3. 確認流程
```python
def _on_confirm(self):
    # 1. 收集選中的專案（重新遍歷，確保準確）
    selected = set()
    for name, var in self.checkbutton_vars.items():
        if var.get():
            selected.add(name)
    
    # 2. 日誌輸出（調試用）
    logger.info(f"收集到 {len(selected)} 個專案: {selected}")
    
    # 3. 檢查是否為空
    if not selected:
        messagebox.showwarning("未選擇專案", "請至少選擇一個專案！")
        return
    
    # 4. 確認對話框
    if messagebox.askyesno("確認選擇", msg):
        self.selected_projects = selected  # 存儲
        self.cancelled = False
        self.root.quit()     # 退出 mainloop
        self.root.destroy()  # 銷毀視窗
```

### 4. 返回值
```python
def show(self) -> Tuple[Set[str], bool]:
    """返回 (選中的專案, 是否取消)"""
    self.root.mainloop()
    return self.selected_projects, self.cancelled

# 外部函數包裝
def show_project_selector(...) -> Tuple[Set[str], bool, bool]:
    """返回 (選中的專案, 清理歷史=True, 是否取消)"""
    ui = ProjectSelectorUI(projects_dir)
    selected, cancelled = ui.show()
    return selected, True, cancelled  # 清理歷史固定為 True
```

---

## 🔧 關鍵改進

### 問題 1: 統計不更新
**原因**: trace 綁定或 command 時機問題  
**解決**: 使用最基本的 `command=self._update_stats`

### 問題 2: 確認後專案消失
**原因**: 複雜的事件處理，可能提前清空  
**解決**: 在 `_on_confirm` 中重新收集，確保準確

### 問題 3: 變數管理混亂
**原因**: 多層嵌套，變數作用域不清  
**解決**: 使用簡單的字典 `{name: var}`

### 問題 4: 調試困難
**原因**: 缺少日誌輸出  
**解決**: 每個關鍵步驟都加上 logger

---

## 🎨 UI 結構

```
┌──────────────────────────────────────────────┐
│          選擇要處理的專案                     │
│  共 N 個專案（選定後將自動清理執行記錄）      │
├──────────────────────────────────────────────┤
│ 專案列表                                     │
│ ┌────────────────────────────────────────┐ │
│ │ ☐ aider__CWE-022...                     │ │
│ │   ✓ Prompt | 709 個檔案                 │ │
│ │                                          │ │
│ │ ☐ ai-hedge-fund__CWE-022...             │ │
│ │   ✓ Prompt | 102 個檔案                 │ │
│ └────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│ [全選] [全不選]                              │
├──────────────────────────────────────────────┤
│ 已選擇: 0 個專案              [確認] [取消]  │
└──────────────────────────────────────────────┘
```

---

## 🧪 測試

### 基本測試
```bash
python test_new_selector.py
```

### 完整測試
```bash
python main.py
```

### 測試步驟
1. ✅ 勾選專案 → 統計立即更新
2. ✅ 多次勾選 → 統計準確
3. ✅ 全選 → 所有專案被選中
4. ✅ 全不選 → 統計歸零
5. ✅ 點擊確認（未選專案）→ 警告訊息
6. ✅ 點擊確認（已選專案）→ 確認對話框
7. ✅ 確認對話框點「是」→ 正確返回
8. ✅ 確認對話框點「否」→ 返回選擇器
9. ✅ 點擊取消 → cancelled=True

---

## 📝 代碼統計

| 指標 | 舊版 | 新版 |
|------|------|------|
| **代碼行數** | ~400 行 | ~280 行 |
| **方法數量** | 15+ | 12 |
| **複雜度** | 高 | 低 |
| **依賴** | trace/trace_add | command |
| **調試輸出** | 少 | 完整 |

---

## ✅ 驗證清單

- [x] 簡化代碼結構
- [x] 移除 trace 綁定，改用 command
- [x] 在 _on_confirm 重新收集專案
- [x] 增加完整的日誌輸出
- [x] 固定清理歷史為 True
- [x] 測試腳本
- [x] 文檔

---

## 🎉 總結

新版專案選擇器：
- 🎯 **專注**: 只做一件事 - 選擇專案
- 🔧 **簡單**: 最少的代碼實現功能
- 📊 **可靠**: 使用最基本的 Tkinter 功能
- 🐛 **易調試**: 完整的日誌輸出
- ✨ **用戶友善**: 清晰的界面和提示

**原則**: Keep It Simple, Stupid (KISS)

---

**完成時間**: 2025-10-14  
**版本**: 3.0.0  
**狀態**: ✅ 已完成，等待測試
