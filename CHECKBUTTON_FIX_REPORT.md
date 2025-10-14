# 勾選框統計更新問題修正報告

**日期**: 2025-10-14  
**問題**: 勾選專案後，統計顯示不更新（一直顯示「已選擇: 0 個專案」）

---

## 🐛 問題分析

### 原始代碼
```python
checkbox = ttk.Checkbutton(
    item_frame,
    variable=var,
    command=self.update_stats  # ← 使用 command 參數
)
```

### 問題原因
`ttk.Checkbutton` 的 `command` 參數在某些情況下可能不會在變數改變時立即觸發，特別是：
1. 當勾選框快速點擊時
2. 當透過程式碼設定變數時（如全選/全不選）
3. UI 更新延遲

---

## 🔧 修正方案

### 方案：使用變數追蹤（Variable Trace）

改用 Tkinter 的變數追蹤機制，直接監聽 `BooleanVar` 的變化。

#### 修正後代碼
```python
def _create_project_item(self, parent, project: dict):
    """創建單個專案項目"""
    item_frame = ttk.Frame(parent)
    item_frame.pack(fill="x", padx=5, pady=3)
    
    # 勾選框
    var = tk.BooleanVar(value=False)
    self.project_vars[project['name']] = var
    
    # ✅ 使用 trace 監聽變數變化（更可靠）
    var.trace('w', lambda *args: self.update_stats())
    
    checkbox = ttk.Checkbutton(
        item_frame,
        variable=var  # ← 移除 command 參數
    )
    checkbox.pack(side="left", padx=(0, 10))
    # ...
```

#### 增強 update_stats 方法
```python
def update_stats(self):
    """更新統計資訊"""
    selected_count = sum(1 for var in self.project_vars.values() if var.get())
    text = f"已選擇: {selected_count} 個專案"
    self.stats_label.config(text=text)
    self.stats_label.update_idletasks()  # ✅ 強制立即更新 UI
    logger.debug(f"統計更新: {text}")     # ✅ 調試日誌
```

---

## 📊 對比

| 方法 | 優點 | 缺點 | 可靠性 |
|------|------|------|--------|
| **command** | 簡單直接 | 可能不觸發 | ⭐⭐⭐ |
| **trace** | 監聽變數變化 | 稍微複雜 | ⭐⭐⭐⭐⭐ |

---

## 🧪 測試

### 簡單測試
```bash
python test_checkbutton.py
```

這個測試程式會創建 5 個勾選框，驗證：
1. 單個勾選是否更新統計
2. 全選按鈕是否更新統計
3. 全不選按鈕是否更新統計

### 完整測試
```bash
python test_project_selector_fixed.py
```

---

## ✅ 驗證步驟

1. **啟動專案選擇器**
   ```bash
   python main.py
   ```

2. **點擊「瀏覽專案」按鈕**

3. **測試單個勾選**
   - 勾選一個專案
   - 檢查左下角是否顯示「已選擇: 1 個專案」

4. **測試多個勾選**
   - 勾選第二個專案
   - 檢查是否顯示「已選擇: 2 個專案」

5. **測試快速選擇**
   - 點擊「全選」→ 應顯示全部數量
   - 點擊「全不選」→ 應顯示「已選擇: 0 個專案」
   - 點擊「反選」→ 數量應該反轉

6. **測試取消勾選**
   - 取消勾選一個專案
   - 檢查數量是否減少

---

## 🔍 調試方法

如果統計仍然不更新，檢查控制台日誌：

```bash
# 應該看到類似輸出：
2025-10-14 16:00:00,000 - ProjectSelectorUI - DEBUG - 統計更新: 已選擇: 1 個專案
2025-10-14 16:00:01,000 - ProjectSelectorUI - DEBUG - 統計更新: 已選擇: 2 個專案
2025-10-14 16:00:02,000 - ProjectSelectorUI - DEBUG - 統計更新: 已選擇: 0 個專案
```

如果看不到這些日誌，說明：
1. `trace` 沒有被觸發 → 檢查變數綁定
2. `update_stats()` 沒有被調用 → 檢查 lambda 函數

---

## 📝 技術細節

### Tkinter 變數追蹤

```python
# trace 方法簽名
var.trace(mode, callback)

# mode 選項:
# 'w' - write: 變數被寫入時觸發
# 'r' - read: 變數被讀取時觸發
# 'u' - undefine: 變數被刪除時觸發

# 使用 'w' 監聽變數變化
var.trace('w', lambda *args: self.update_stats())
```

### 為什麼使用 lambda?

```python
# ❌ 錯誤：會立即調用函數
var.trace('w', self.update_stats())

# ✅ 正確：傳遞函數引用
var.trace('w', lambda *args: self.update_stats())
```

`trace` 的回調函數會接收 3 個參數：
- `name`: 變數名稱
- `index`: 陣列索引（如果是陣列變數）
- `mode`: 觸發模式

使用 `lambda *args` 忽略這些參數。

---

## 🎯 預期結果

修正後，勾選框應該：

✅ **單個勾選** → 立即更新統計  
✅ **快速連續勾選** → 每次都更新  
✅ **全選按鈕** → 更新為總數  
✅ **全不選按鈕** → 更新為 0  
✅ **反選按鈕** → 正確計算反轉後的數量  
✅ **取消勾選** → 數量減少  

---

## 🔄 回退方案

如果 `trace` 方法仍然有問題，可以回退到強制更新方案：

```python
def _create_project_item(self, parent, project: dict):
    # ...
    def on_check():
        self.root.after(10, self.update_stats)  # 延遲 10ms 更新
    
    checkbox = ttk.Checkbutton(
        item_frame,
        variable=var,
        command=on_check
    )
```

---

## 📌 總結

### 修正內容
1. ✅ 從 `command` 改為 `trace` 監聽變數變化
2. ✅ 增加 `update_idletasks()` 強制 UI 更新
3. ✅ 增加調試日誌輸出

### 修正檔案
- `src/project_selector_ui.py`
  - `_create_project_item()` 方法
  - `update_stats()` 方法

### 測試檔案
- `test_checkbutton.py` - 簡單測試
- `test_project_selector_fixed.py` - 完整測試

---

**修正完成時間**: 2025-10-14  
**狀態**: ✅ 已修正，等待測試驗證
