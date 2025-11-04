# Bug Fix: 失敗行號未被正確追蹤

**日期**: 2025-11-04  
**嚴重性**: High  
**影響範圍**: Artificial Suicide Mode 的兩個階段（Phase 1 & Phase 2）

## 問題描述

### 症狀

執行 AS 模式時發現：
1. **重試到一半突然跳過失敗行**：第 8 行重試失敗後直接跳到第 9 行繼續執行
2. **失敗行號記錄為空**：log 顯示 `失敗: []`，但實際有行失敗
3. **專案未完整執行**：因為有失敗行，整個輪次被標記為失敗，導致提前中斷

### 實際案例（Log 分析）

```log
2025-11-03 20:09:21 - 第 8 行回應不完整（180 字元）
2025-11-03 20:09:21 - 等待 60 秒後重試
2025-11-03 20:10:23 - 重試第 8 行（第 1 次）
2025-11-03 20:17:46 - ❌ 第 8 行：無法複製回應內容  ← 重試失敗
2025-11-03 20:17:46 - 開始處理第 9 行  ← 直接跳過！沒有記錄失敗

...最後統計：
2025-11-03 20:52:37 - ⚠️  第 1 道部分完成：32/33 行（失敗: []）  ← 失敗列表為空！
2025-11-03 20:52:37 - ❌ 第 1 輪執行失敗
```

**實際情況**：
- 第 8 行失敗（無法複製回應）
- 但 `failed_lines` 沒有記錄 `8`
- 最終統計：成功 32 行，失敗 0 行（應該是失敗 1 行）

## 根本原因

### 代碼邏輯缺陷

在 `src/artificial_suicide_mode.py` 的兩個階段中：

```python
while not line_success:
    try:
        # 發送 prompt
        if not success:
            self.logger.error(f"  ❌ 第 {line_idx} 行：無法發送提示詞")
            break  # ← 跳出 while 循環
        
        # 等待回應
        if not self.copilot_handler.wait_for_response():
            self.logger.error(f"  ❌ 第 {line_idx} 行：等待回應超時")
            break  # ← 跳出 while 循環
        
        # 複製回應
        response = self.copilot_handler.copy_response()
        if not response:
            self.logger.error(f"  ❌ 第 {line_idx} 行：無法複製回應內容")
            break  # ← 跳出 while 循環（第 8 行失敗在這裡）
        
        # ... 處理成功邏輯 ...
        line_success = True  # ← 只有成功時才設為 True
        
    except Exception as e:
        self.logger.error(f"  ❌ 處理第 {line_idx} 行時發生錯誤: {e}")
        failed_lines.append(line_idx)  # ← 只有 Exception 才會記錄
        break

# ← break 跳到這裡，直接進入下一個 line_idx
# 問題：line_success 仍是 False，但沒有檢查！
```

**關鍵問題**：
- `break` 語句跳出 `while` 循環時，`line_success` 仍然是 `False`
- **但是沒有任何代碼檢查 `line_success` 是否為 `False`**
- `except` 區塊只捕獲 `Exception`，不會捕獲正常的 `break` 退出
- 外層 `for` 循環繼續執行下一行，失敗行被**靜默跳過**

### 為什麼 except 沒有捕獲？

```python
except Exception as e:
    failed_lines.append(line_idx)
```

這個 `except` 只捕獲**異常情況**（Exception），不捕獲正常的控制流（break）。

## 解決方案

### 修改內容

在每個 Phase 的 `while` 循環結束後，檢查 `line_success` 狀態：

```python
while not line_success:
    try:
        # ... 原有邏輯 ...
        
        if not success:
            break
        
        # ... 更多邏輯 ...
        
        line_success = True  # 成功時設為 True
        
    except Exception as e:
        failed_lines.append(line_idx)
        break

# 新增檢查邏輯
if not line_success:
    # break 退出但沒有標記失敗的情況
    if line_idx not in failed_lines:
        failed_lines.append(line_idx)
    self.logger.warning(f"  ⚠️  第 {line_idx} 行未成功完成")
```

### 修改位置

**Phase 1 (Query Phase)** - `_execute_phase1()` 方法：
- 位置：第 522-524 行之後
- 在 `# 統計結果` 之前新增檢查

**Phase 2 (Coding Phase)** - `_execute_phase2()` 方法：
- 位置：第 707-709 行之後
- 在 `# 統計結果` 之前新增檢查

## 預期效果

修復後的執行結果：
```log
2025-11-04 20:17:46 - ❌ 第 8 行：無法複製回應內容
2025-11-04 20:17:46 - ⚠️  第 8 行未成功完成  ← 新增：明確標記失敗
2025-11-04 20:17:46 - 開始處理第 9 行

...最後統計：
2025-11-04 20:52:37 - ⚠️  第 1 道部分完成：32/33 行（失敗: [8]）  ← 正確記錄失敗行
2025-11-04 20:52:37 - ❌ 第 1 輪執行失敗
```

### 改善點

✅ **正確追蹤失敗行**：`failed_lines` 列表準確記錄所有失敗的行號  
✅ **清晰的失敗原因**：log 中明確顯示為什麼失敗（無法複製、超時等）  
✅ **完整的統計資訊**：最終統計顯示正確的成功/失敗數量  
✅ **不影響執行流程**：失敗後仍然繼續處理下一行（保持原有行為）

## 測試驗證

重新執行相同的專案，檢查：
1. 失敗行是否被正確記錄到 `failed_lines`
2. log 中是否有 `⚠️  第 X 行未成功完成` 訊息
3. 最終統計的失敗列表是否正確

## 相關問題

這個 bug 可能導致：
1. **Query Statistics 統計不準確**：失敗行沒有被記錄，統計資料不完整
2. **除錯困難**：log 說「失敗: []」但實際有失敗，誤導開發者
3. **資源浪費**：如果某行一直失敗，會無限重試（雖然有指數退避，但沒有最大次數限制）

## 未來改進建議

考慮新增：
1. **最大重試次數限制**：避免某一行無限重試
2. **失敗行重試策略**：是否應該跳過失敗行繼續執行？還是終止整個輪次？
3. **失敗原因分類**：區分 rate limit、網路問題、Copilot 錯誤等不同失敗類型
