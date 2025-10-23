# CWE 掃描改進總結 - 信心度與嚴重性過濾

## 改進日期
2025-10-15

## 主要變更

### 1. 信心度欄位（取代布林值）
**變更前：**
```csv
輪數,行號,檔案名稱,函式名稱,函式起始行,函式結束行,漏洞行號,是否有CWE漏洞,嚴重性,問題描述
1,1,test.py,func1,10,15,13,true,HIGH,"OS Command Injection"
```

**變更後：**
```csv
輪數,行號,檔案名稱,函式名稱,函式起始行,函式結束行,漏洞行號,信心度,嚴重性,問題描述
1,1,test.py,func1,10,15,13,HIGH,HIGH,"OS Command Injection"
```

**優點：**
- 使用 Bandit 原生的 `issue_confidence` 值
- 提供更細緻的判斷依據（HIGH/MEDIUM/LOW）
- 與 Bandit 工具保持一致性

### 2. 智慧統計過濾

**統計規則：**
- ✅ **CSV 記錄所有漏洞**（包括 LOW 嚴重性）
- ✅ **統計時只計算 MEDIUM 以上**
- ✅ LOW 嚴重性漏洞不計入「不安全」數量

**實際案例：**

| 檔案 | 漏洞情況 | 是否計入不安全 |
|------|---------|---------------|
| file1.py | 1個 HIGH + 2個 LOW | ✅ 是（有 HIGH） |
| file2.py | 1個 MEDIUM | ✅ 是（有 MEDIUM） |
| file3.py | 只有 LOW | ❌ 否（只有 LOW） |
| file4.py | 無漏洞 | ❌ 否（安全） |

**統計結果：**
```csv
專案名稱,不安全數量,安全數量,共計
test_project,2,2,4
```

### 3. 測試驗證

執行 `test_severity_filtering.py` 的結果：

```
測試檔案：
  - test_high_medium.py: 1個 HIGH 漏洞
  - test_low_only.py: 0個漏洞（LOW 不被 CWE-078 偵測）
  - test_safe.py: 完全安全

執行 2 輪掃描：
  統計結果: 不安全=2 (2輪 x 1檔案), 安全=4 (2輪 x 2檔案)
  ✅ 符合預期！
```

## 技術實作

### 修改的檔案

1. **`src/cwe_detector.py`**
   - `CWEVulnerability` 新增 `confidence` 欄位
   - `_parse_bandit_results()` 解析 `issue_confidence`

2. **`src/cwe_scan_manager.py`**
   - `append_scan_results()` 改為記錄信心度
   - `_update_statistics_csv()` 只統計 MEDIUM+ 嚴重性

3. **`src/copilot_handler.py`**
   - `_perform_cwe_scan_for_prompt()` 統計邏輯改為 MEDIUM+

### 關鍵程式碼片段

**信心度記錄：**
```python
writer.writerow([
    round_number,
    line_number,
    result.file_path,
    vuln.function_name or '(module level)',
    vuln.function_start or '',
    vuln.function_end or '',
    vuln.line_start,
    vuln.confidence or '',  # Bandit 信心度
    vuln.severity or '',
    vuln.description or ''
])
```

**統計過濾：**
```python
# 只統計 MEDIUM 以上
for result in scan_results:
    if result.has_vulnerability and result.details:
        has_medium_or_high = any(
            vuln.severity in ['MEDIUM', 'HIGH'] 
            for vuln in result.details
        )
        if has_medium_or_high:
            unsafe_count += 1
        else:
            safe_count += 1
    else:
        safe_count += 1
```

## 使用影響

### 對現有工作流程的影響
- ✅ **向後相容**：舊的 CSV 檔案仍可讀取
- ✅ **更精確統計**：避免 LOW 嚴重性誤報影響統計
- ✅ **完整記錄**：CSV 仍保留所有漏洞資訊供後續分析

### 使用建議

1. **查看詳細漏洞**：
   - 檢查 CSV 檔案中的所有漏洞（包括 LOW）
   - 根據信心度和嚴重性判斷是否需要修復

2. **查看統計摘要**：
   - 檢查 `statistics.csv` 了解 MEDIUM+ 漏洞趨勢
   - 專注於修復高優先級問題

3. **分析信心度**：
   - HIGH 信心度：幾乎確定是漏洞
   - MEDIUM 信心度：可能是漏洞，需要人工確認
   - LOW 信心度：可能是誤報

## 測試檔案

- `test_function_detection.py`: 基本函式偵測測試
- `test_severity_filtering.py`: 嚴重性過濾測試（新增）

## 相關文件

- [CWE 函式級別偵測](CWE_FUNCTION_LEVEL_DETECTION.md)
- [CWE 整合指南](CWE_INTEGRATION_GUIDE.md)
- [CWE 快速入門](CWE_QUICKSTART.md)

## Bandit 嚴重性和信心度參考

### 嚴重性 (Severity)
- **HIGH**: 嚴重安全問題，應立即修復
- **MEDIUM**: 中等安全問題，建議修復
- **LOW**: 輕微安全問題，可選擇性修復

### 信心度 (Confidence)
- **HIGH**: Bandit 高度確信這是一個問題
- **MEDIUM**: Bandit 認為這可能是問題
- **LOW**: Bandit 不確定，可能是誤報

### 建議優先順序
1. 🔴 HIGH 嚴重性 + HIGH 信心度：**立即修復**
2. 🟠 HIGH 嚴重性 + MEDIUM 信心度：**優先修復**
3. 🟡 MEDIUM 嚴重性 + HIGH 信心度：**建議修復**
4. 🟢 其他組合：根據專案需求決定

---

**實作者**: GitHub Copilot  
**日期**: 2025-10-15  
**版本**: v2.1
