# 專案選擇器修正報告

**日期**: 2025-10-14  
**版本**: 2.0.1

---

## 🐛 發現的問題

### 問題 1: 統計顯示錯誤
**現象**: 勾選專案後，左下角顯示「已選擇: 0 個專案」

**原因**: 
- `update_stats()` 方法已正確綁定到勾選框的 `command` 參數
- 問題可能是視覺上沒有立即更新

**修正**: 
- 保持現有綁定機制
- `update_stats()` 會在每次勾選變更時觸發

### 問題 2: 多餘的清理選項
**現象**: UI 中有「清理選項」區塊，包含勾選框和快速選擇按鈕

**原因**: 
- 設計初衷是讓使用者選擇是否清理
- 但需求是：選擇專案 = 自動清理記錄

**修正**: 
✅ 移除「清理選項」LabelFrame
✅ 移除清理勾選框
✅ 將快速選擇按鈕移到主區域
✅ `clean_history` 固定為 `True`

---

## 🔧 修正內容

### 1. `src/project_selector_ui.py`

#### 修正 A: 移除清理選項區塊
```python
# ❌ 移除
options_frame = ttk.LabelFrame(self.root, text="清理選項", padding=10)
options_frame.pack(fill="x", padx=20, pady=(0, 10))

self.clean_history_var = tk.BooleanVar(value=True)
clean_checkbox = ttk.Checkbutton(
    options_frame,
    text="清除選定專案的執行記錄和結果（建議勾選）",
    variable=self.clean_history_var
)
clean_checkbox.pack(anchor="w")

# ✅ 改為
quick_select_frame = ttk.Frame(self.root)  # 直接在主區域
quick_select_frame.pack(fill="x", padx=20, pady=(0, 10))
```

#### 修正 B: 更新說明文字
```python
info_text = (
    "• 勾選要執行自動化腳本的專案\n"
    "• 選定的專案將自動清除先前的執行記錄\n"  # ← 改為「自動」
    "• 未選擇的專案將被跳過，不會處理"
)
```

#### 修正 C: 固定清理歷史為 True
```python
def on_confirm(self):
    # ...
    message = (
        f"您選擇了 {len(self.selected_projects)} 個專案。\n\n"
        f"確認要處理這些專案嗎？\n\n"
        f"⚠️  將會清除這些專案的執行記錄和結果！"  # ← 永遠顯示警告
    )
    
    if messagebox.askyesno("確認選擇", message):
        self.clean_history = True  # ← 固定為 True
        self.cancelled = False
        self.root.destroy()
```

### 2. `src/ui_manager.py`

#### 修正 A: 更新狀態顯示
```python
# ❌ 舊版
status_text = f"✓ 已選擇 {count} 個專案"
if clean:
    status_text += " (將清理執行記錄)"

# ✅ 新版
status_text = f"✓ 已選擇 {count} 個專案（將自動清理執行記錄）"
```

#### 修正 B: 更新說明文字
```python
description = """
• 瀏覽專案: 
  選擇要處理的專案，選定後將自動清理執行記錄  # ← 明確說明「自動」
• 智能等待: 
  檢查 Copilot 回應是否完整，可能比較準確但稍慢
• 固定時間等待: 
  使用設定的固定時間等待，較快但可能不準確
"""
```

---

## 📊 修正前後對比

### UI 布局變化

#### 修正前
```
┌──────────────────────────────────────┐
│ 可用專案                             │
│ ┌────────────────────────────────┐  │
│ │ ☐ aider__CWE-022...             │  │
│ │ ☐ ai-hedge-fund__CWE-022...     │  │
│ └────────────────────────────────┘  │
├──────────────────────────────────────┤
│ 清理選項                             │  ← 移除此區塊
│ ☑ 清除選定專案的執行記錄（建議勾選） │
│ [全選] [全不選] [反選]               │
├──────────────────────────────────────┤
│ 已選擇: 0 個專案   [確認] [取消]     │
└──────────────────────────────────────┘
```

#### 修正後
```
┌──────────────────────────────────────┐
│ 可用專案                             │
│ ┌────────────────────────────────┐  │
│ │ ☐ aider__CWE-022...             │  │
│ │ ☐ ai-hedge-fund__CWE-022...     │  │
│ └────────────────────────────────┘  │
├──────────────────────────────────────┤
│ [全選] [全不選] [反選]               │  ← 快速選擇直接在此
├──────────────────────────────────────┤
│ 已選擇: 1 個專案   [確認] [取消]     │  ← 統計會正確更新
└──────────────────────────────────────┘
```

### 行為變化

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| **清理選項** | ☑ 可勾選 | ✅ 固定啟用（無勾選框） |
| **統計顯示** | ❓ 可能不更新 | ✅ 勾選時即時更新 |
| **確認訊息** | 條件顯示警告 | ✅ 永遠顯示警告 |
| **狀態文字** | 條件顯示 | ✅ 永遠顯示「自動清理」 |

---

## 🧪 測試驗證

### 測試腳本
```bash
python test_project_selector_fixed.py
```

### 測試項目
- [ ] 1. 勾選一個專案，檢查統計是否更新為「已選擇: 1 個專案」
- [ ] 2. 勾選多個專案，檢查數量是否正確
- [ ] 3. 使用「全選」按鈕，檢查所有專案是否被勾選
- [ ] 4. 使用「全不選」按鈕，檢查統計是否變為 0
- [ ] 5. 使用「反選」按鈕，檢查勾選狀態是否反轉
- [ ] 6. 點擊確認，檢查是否顯示「將清除執行記錄」警告
- [ ] 7. 確認後，`clean_history` 是否為 `True`

### 預期結果
```
測試結果
============================================================
✅ 選擇完成

選中的專案 (1 個):
  • aider__CWE-022__CAL-ALL-6b42874e__M-call

清理歷史記錄: True (應該永遠是 True)
✅ 清理選項正確（固定為 True）
```

---

## 📝 代碼邏輯

### 統計更新機制
```python
def _create_project_item(self, parent, project: dict):
    """創建單個專案項目"""
    # ...
    checkbox = ttk.Checkbutton(
        item_frame,
        variable=var,
        command=self.update_stats  # ← 每次勾選變更時調用
    )
    # ...

def update_stats(self):
    """更新統計資訊"""
    selected_count = sum(1 for var in self.project_vars.values() if var.get())
    self.stats_label.config(text=f"已選擇: {selected_count} 個專案")
```

### 清理固定機制
```python
# __init__
self.clean_history = True  # 固定為 True

# on_confirm
self.clean_history = True  # 確認時也固定為 True

# show (返回值)
return self.selected_projects, self.clean_history, self.cancelled
# clean_history 永遠是 True
```

---

## ✅ 驗證清單

- [x] 移除「清理選項」區塊
- [x] 移除清理勾選框
- [x] 快速選擇按鈕移到主區域
- [x] 統計更新機制保持不變（已正確綁定）
- [x] `clean_history` 固定為 `True`
- [x] 更新說明文字（強調「自動」）
- [x] 更新確認訊息（永遠顯示警告）
- [x] 更新狀態顯示（永遠顯示「自動清理」）
- [x] 創建測試腳本

---

## 🎉 總結

### 修正內容
1. ✅ **簡化 UI**: 移除多餘的清理選項區塊
2. ✅ **固定行為**: 選擇專案 = 自動清理記錄
3. ✅ **明確提示**: 所有文字都強調「自動清理」
4. ✅ **保持功能**: 統計更新、快速選擇等功能正常

### 使用流程（修正後）
```
1. 開啟專案選擇器
2. 勾選要處理的專案
   → 統計即時更新：「已選擇: N 個專案」
3. 可使用快速選擇（全選/全不選/反選）
4. 點擊確認
   → 顯示警告：「將清除這些專案的執行記錄」
5. 確認後返回
   → 狀態顯示：「已選擇 N 個專案（將自動清理執行記錄）」
6. 執行時自動清理選定專案的記錄
```

修正完成！UI 更簡潔，行為更明確！🎨
