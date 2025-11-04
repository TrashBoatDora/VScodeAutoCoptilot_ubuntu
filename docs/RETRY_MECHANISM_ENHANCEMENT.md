# 重試機制增強：全面重試 + 最大次數限制

**日期**: 2025-11-04  
**類型**: 功能增強 + Bug 修復

## 問題背景

### 原始問題

在 AS 模式執行中發現：
1. **第 8 行「無法複製回應」後沒有重試**，直接跳到第 9 行
2. **重試機制不完整**：只針對「回應不完整」重試，其他失敗類型（發送失敗、等待超時、複製失敗）都直接 break
3. **無最大重試次數限制**：理論上可能無限重試（雖然有指數退避）

### 「無法複製回應」的原因

`copilot_handler.copy_response()` 返回 `None` 的情況：

#### 1. **剪貼簿內容為空**（最常見）
```python
# 複製操作流程
1. Ctrl+F1 聚焦到 Copilot Chat 輸入框
2. Ctrl+↑ 聚焦到 Copilot 回應
3. Shift+F10 開啟右鍵選單
4. Down 定位到「複製」
5. Enter 執行複製
6. 檢查剪貼簿內容

# 如果剪貼簿為空或只有空白
if not response or len(response.strip()) == 0:
    return None  # 複製失敗
```

**可能原因**：
- Copilot 還在生成回應（聚焦到錯誤位置）
- VS Code 視窗失去焦點（鍵盤操作失敗）
- 右鍵選單沒有正確打開（Shift+F10 失敗）
- "複製" 選項位置變化（不是第一個 down）
- 系統剪貼簿被其他程式占用

#### 2. **Exception 異常**（少見）
- 鍵盤操作失敗（pyautogui 錯誤）
- pyperclip 無法訪問剪貼簿
- 系統剪貼簿被鎖定

#### 3. **內部重試 3 次後仍失敗**
`copy_response()` 內部已有重試機制（`config.COPILOT_COPY_RETRY_MAX = 3`），如果 3 次都失敗才返回 `None`。

### 原始代碼邏輯缺陷

**Phase 1 和 Phase 2 的問題**：

```python
# 發送 prompt
if not success:
    self.logger.error(f"  ❌ 第 {line_idx} 行：無法發送提示詞")
    break  # ← 直接 break，沒有重試！

# 等待回應
if not self.copilot_handler.wait_for_response():
    self.logger.error(f"  ❌ 第 {line_idx} 行：等待回應超時")
    break  # ← 直接 break，沒有重試！

# 複製回應
response = self.copilot_handler.copy_response()
if not response:
    self.logger.error(f"  ❌ 第 {line_idx} 行：無法複製回應內容")
    break  # ← 直接 break，沒有重試！（這就是第 8 行的問題）

# 檢查回應完整性
if is_response_incomplete(response):
    retry_count += 1
    wait_and_retry(...)
    continue  # ← 只有這個情況會重試！
```

**結果**：
- ✅ 回應不完整：重試
- ❌ 發送失敗：不重試
- ❌ 等待超時：不重試
- ❌ 複製失敗：不重試（← 第 8 行的問題）

## 解決方案

### 1. 新增 Config 設定

**文件**: `config/config.py`

```python
# Artificial Suicide 模式專用重試設定
AS_MODE_MAX_RETRY_PER_LINE = 10  # AS 模式中每一行的最大重試次數（包含所有失敗類型）
```

**說明**：
- 這是 AS 模式的**外層重試限制**（整個 while 循環）
- 不同於 `COPILOT_COPY_RETRY_MAX = 3`（copilot_handler 內部的複製重試）
- 涵蓋所有失敗類型：發送、等待、複製、回應不完整

### 2. 修改重試邏輯（Phase 1 & Phase 2）

#### A. 新增最大重試次數檢查

```python
retry_count = 0
line_success = False

# 持續重試直到回應完整（最多 AS_MODE_MAX_RETRY_PER_LINE 次）
while not line_success:
    try:
        # 檢查是否超過最大重試次數
        if retry_count >= config.AS_MODE_MAX_RETRY_PER_LINE:
            self.logger.error(f"  ❌ 第 {line_idx} 行：已達最大重試次數 ({config.AS_MODE_MAX_RETRY_PER_LINE} 次)，放棄該行")
            failed_lines.append(line_idx)
            break
        
        # 顯示重試次數
        if retry_count == 0:
            self.logger.info(f"  處理第 {line_idx}/{len(self.prompt_lines)} 行: ...")
        else:
            self.logger.info(f"  重試第 {line_idx} 行（第 {retry_count}/{config.AS_MODE_MAX_RETRY_PER_LINE} 次）")
```

#### B. 將所有 `break` 改為 `continue`（加上重試邏輯）

**發送失敗 → 重試**：
```python
if not success:
    self.logger.error(f"  ❌ 第 {line_idx} 行：無法發送提示詞")
    retry_count += 1
    self.logger.warning(f"  ⏳ 發送失敗，等待後重試（第 {retry_count} 次）")
    wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
    
    # 清空輸入框準備重試
    pyautogui.hotkey('ctrl', 'f1')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.5)
    continue  # ← 改為重試
```

**等待超時 → 重試**：
```python
if not self.copilot_handler.wait_for_response():
    self.logger.error(f"  ❌ 第 {line_idx} 行：等待回應超時")
    retry_count += 1
    self.logger.warning(f"  ⏳ 等待超時，將重試（第 {retry_count} 次）")
    wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
    
    # 清空輸入框準備重試
    pyautogui.hotkey('ctrl', 'f1')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.5)
    continue  # ← 改為重試
```

**複製失敗 → 重試**（修復第 8 行問題）：
```python
response = self.copilot_handler.copy_response()
if not response:
    self.logger.error(f"  ❌ 第 {line_idx} 行：無法複製回應內容")
    retry_count += 1
    self.logger.warning(f"  ⏳ 複製失敗，將重試（第 {retry_count} 次）")
    wait_and_retry(60, line_idx, round_num, self.logger, retry_count)
    
    # 清空輸入框準備重試
    pyautogui.hotkey('ctrl', 'f1')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.5)
    continue  # ← 改為重試（解決第 8 行問題）
```

**回應不完整 → 重試**（原有邏輯，保持不變）：
```python
if is_response_incomplete(response):
    self.logger.warning(f"  ⚠️  第 {line_idx} 行回應不完整，將等待後重試")
    retry_count += 1
    wait_and_retry(1800, line_idx, round_num, self.logger, retry_count)  # 30 分鐘
    
    # 清空輸入框準備重試
    pyautogui.hotkey('ctrl', 'f1')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.5)
    continue
```

### 3. 修改的檔案

**config/config.py**:
- 新增 `AS_MODE_MAX_RETRY_PER_LINE = 10`

**src/artificial_suicide_mode.py**:
- 新增 import: `from config import config`
- Phase 1 (`_execute_phase1()`):
  - 新增最大重試次數檢查
  - 發送失敗 → 重試（原本 break）
  - 等待超時 → 重試（原本 break）
  - 複製失敗 → 重試（原本 break）
- Phase 2 (`_execute_phase2()`):
  - 新增最大重試次數檢查
  - 發送失敗 → 重試（原本 break）
  - 等待超時 → 重試（原本 break）
  - 複製失敗 → 重試（原本 break）

## 重試策略詳解

### 等待時間策略

| 失敗類型 | 等待時間 | 策略 | 原因 |
|---------|---------|------|------|
| **發送失敗** | 60 秒（指數退避） | `wait_and_retry(60, ...)` | 可能是 VS Code 窗口問題 |
| **等待超時** | 60 秒（指數退避） | `wait_and_retry(60, ...)` | 可能是 Copilot 沒回應 |
| **複製失敗** | 60 秒（指數退避） | `wait_and_retry(60, ...)` | 可能是焦點問題 |
| **回應不完整** | 1800 秒（30 分鐘）| `wait_and_retry(1800, ...)` | Rate limit，需要長時間等待 |

**指數退避公式**：`10 * (6 ** retry_count)` 秒
- 第 1 次：60 秒（實際上是 `10 * 6^1`，但這裡固定 60）
- 第 2 次：360 秒
- 第 3 次：2160 秒
- ...

### 最大重試次數

```
AS_MODE_MAX_RETRY_PER_LINE = 10

例如：
- 第 1-3 次：複製失敗
- 第 4-5 次：等待超時
- 第 6 次：回應不完整
- 第 7 次：成功

總共重試 7 次 < 10 次，成功完成。
```

### 兩層重試機制

```
外層重試（AS 模式）：AS_MODE_MAX_RETRY_PER_LINE = 10 次
    ↓
內層重試（copilot_handler）：COPILOT_COPY_RETRY_MAX = 3 次
```

**範例流程**：
```
第 1 次外層重試：
  → copy_response() 內部重試 3 次
  → 3 次都失敗，返回 None
  → 外層捕獲，等待 60 秒

第 2 次外層重試：
  → copy_response() 內部重試 3 次
  → 第 2 次成功，返回 response
  → 外層成功，繼續處理
```

## 預期效果

### 修復前（第 8 行案例）

```log
20:09:21 - 第 8 行回應不完整（180 字元）
20:09:21 - 等待 60 秒後重試
20:10:23 - 重試第 8 行（第 1 次）
20:17:46 - ❌ 第 8 行：無法複製回應內容  ← 直接 break，沒有重試
20:17:46 - 開始處理第 9 行  ← 跳過了第 8 行
```

### 修復後（預期）

```log
20:09:21 - 第 8 行回應不完整（180 字元）
20:09:21 - 等待 60 秒後重試
20:10:23 - 重試第 8 行（第 1/10 次）
20:17:46 - ❌ 第 8 行：無法複製回應內容
20:17:46 - ⏳ 複製失敗，將重試（第 2 次）  ← 新增重試
20:17:46 - 等待 60 秒後重試
20:18:46 - 重試第 8 行（第 2/10 次）  ← 繼續重試
20:19:30 - ✅ 收到回應 (250 字元)
20:19:30 - ✅ 第 8 行回應完整
20:19:30 - ✅ 第 8 行處理完成（經過 2 次重試）
20:19:32 - 開始處理第 9 行  ← 第 8 行成功後才處理第 9 行
```

### 達到最大次數（預期）

```log
20:00:00 - 處理第 X 行
20:01:00 - 重試第 X 行（第 1/10 次）
20:02:00 - 重試第 X 行（第 2/10 次）
...
20:09:00 - 重試第 X 行（第 9/10 次）
20:10:00 - 重試第 X 行（第 10/10 次）
20:11:00 - ❌ 第 X 行：已達最大重試次數 (10 次)，放棄該行
20:11:00 - ⚠️  第 X 行未成功完成  ← 標記失敗
20:11:00 - 開始處理第 X+1 行
```

## 與其他 Bug Fix 的配合

這個修改與 `BUG_FIX_FAILED_LINES_NOT_TRACKED.md` 配合：

1. **重試機制增強**（本文檔）：
   - 所有失敗類型都會重試
   - 有最大次數限制
   
2. **失敗行號追蹤**（另一個 bug fix）：
   - 當達到最大次數或 Exception 時，正確記錄 `failed_lines`
   - 最終統計顯示正確的失敗列表

**結合效果**：
```python
# 重試機制增強
if retry_count >= config.AS_MODE_MAX_RETRY_PER_LINE:
    self.logger.error(f"已達最大重試次數，放棄該行")
    failed_lines.append(line_idx)  # ← 記錄失敗
    break

# ... while 循環結束 ...

# 失敗行號追蹤
if not line_success:
    if line_idx not in failed_lines:
        failed_lines.append(line_idx)  # ← 雙重保險
    self.logger.warning(f"第 {line_idx} 行未成功完成")
```

## 測試驗證

1. **重新執行 airflow 專案**，檢查：
   - 第 8 行是否會重試（而不是直接跳到第 9 行）
   - 重試次數是否正確顯示（`X/10`）
   - 達到最大次數時是否正確放棄並記錄

2. **檢查 log 輸出**：
   - 是否有 `⏳ 複製失敗，將重試` 訊息
   - 是否有 `已達最大重試次數` 訊息
   - `failed_lines` 列表是否正確

3. **驗證最終統計**：
   ```log
   ⚠️  第 1 道部分完成：32/33 行（失敗: [8]）  ← 正確記錄失敗行
   ```

## 相關問題

### 為什麼複製失敗要等 60 秒？

- 複製失敗通常是因為焦點問題或 Copilot 還在生成
- 60 秒等待時間足夠讓 Copilot 完成生成或恢復焦點
- 搭配指數退避，後續重試會等待更長時間

### 為什麼不是每次失敗都等 30 分鐘？

- 只有「回應不完整」才可能是 rate limit，需要 30 分鐘
- 其他失敗類型（發送、等待、複製）不是 rate limit，等 1 分鐘即可
- 避免不必要的長時間等待

### 10 次重試次數夠嗎？

根據指數退避策略：
```
第 1 次：60 秒
第 2 次：360 秒（6 分鐘）
第 3 次：2160 秒（36 分鐘）
...
第 10 次：60466176 秒（約 700 天）
```

實際上，如果前 3-4 次都失敗，通常表示有系統性問題（Copilot 掛掉、VS Code 崩潰等），繼續重試也沒有意義。10 次是合理的上限。
