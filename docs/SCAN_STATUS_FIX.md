# 掃描狀態錯誤修復文檔

## 問題描述

### 發現的問題

使用者發現一個嚴重的數據完整性問題：

1. **OriginalScanResult/Semgrep** 目錄下沒有任何掃描結果檔案
2. **CWE_Result** 的 CSV 統計卻顯示 `scan_status: success`
3. 違反了基本原則：**沒有掃描依據就不能產生成功的結果**

### 問題影響

這會導致：
- 研究數據不可信（假陽性：聲稱安全但實際上沒掃描）
- 安全風險（可能存在漏洞但被錯誤標記為安全）
- 統計數據失真（成功率虛高）

## 根本原因分析

### 1. Semgrep 掃描失敗時沒有創建失敗記錄

**檔案**: `src/cwe_detector.py`

**問題代碼** (第 650-660 行):
```python
try:
    subprocess.run(cmd, capture_output=True, timeout=60, text=True)
    if original_output_file.exists():
        vulns = self._parse_semgrep_results(...)
        all_vulns.extend(vulns)
    # ❌ 沒有 else 分支處理檔案不存在的情況
except Exception as e:
    logger.error(f"Semgrep 單檔掃描失敗: {e}")
    # ❌ 只記錄錯誤，沒有創建失敗記錄
```

**後果**: 當 Semgrep 掃描失敗時，返回空列表，導致下游邏輯誤判為成功。

### 2. CSV 生成邏輯預設為 Success

**檔案**: `src/cwe_scan_manager.py`

**問題代碼** (第 227 行):
```python
scan_status = 'success'  # ❌ 預設成功
```

**問題代碼** (第 298-313 行):
```python
else:
    # 沒有漏洞：也要記錄（作為實驗數據點）
    writer.writerow([
        ...
        'success',  # ❌ 沒有檢查是否真的進行了掃描
        ''
    ])
```

**後果**: 即使沒有找到任何掃描結果，也會記錄為 `success`。

### 3. 檔案不存在時直接返回空列表

**檔案**: `src/cwe_detector.py`

**問題代碼** (第 527-529 行):
```python
if not file_path.exists():
    logger.error(f"檔案不存在: {file_path}")
    return []  # ❌ 返回空列表，沒有失敗記錄
```

**後果**: 無法區分「檔案不存在」和「掃描成功但沒發現漏洞」。

## 修復方案

### 修復 1: Semgrep 掃描失敗時創建失敗記錄

**檔案**: `src/cwe_detector.py` (第 649-707 行)

```python
try:
    result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
    
    if original_output_file.exists():
        vulns = self._parse_semgrep_results(...)
        all_vulns.extend(vulns)
    else:
        # ✅ 掃描失敗：沒有產生輸出檔案
        logger.warning(f"Semgrep 掃描失敗，未產生輸出檔案 (return code: {result.returncode})")
        
        # ✅ 創建失敗記錄
        error_msg = result.stderr.strip() if result.stderr else "No output file generated"
        vuln = CWEVulnerability(
            cwe_id=cwe,
            file_path=str(file_path),
            line_start=0,
            line_end=0,
            function_name=function_name,
            scanner=ScannerType.SEMGREP,
            scan_status='failed',
            failure_reason=f"Semgrep failed to generate output (code {result.returncode}): {error_msg[:200]}",
            severity='',
            description=''
        )
        all_vulns.append(vuln)
        
except subprocess.TimeoutExpired:
    # ✅ 創建超時失敗記錄
    vuln = CWEVulnerability(
        cwe_id=cwe,
        file_path=str(file_path),
        line_start=0,
        line_end=0,
        function_name=function_name,
        scanner=ScannerType.SEMGREP,
        scan_status='failed',
        failure_reason="Semgrep scan timeout (60 seconds)",
        severity='',
        description=''
    )
    all_vulns.append(vuln)
    
except Exception as e:
    # ✅ 創建異常失敗記錄
    vuln = CWEVulnerability(
        cwe_id=cwe,
        file_path=str(file_path),
        line_start=0,
        line_end=0,
        function_name=function_name,
        scanner=ScannerType.SEMGREP,
        scan_status='failed',
        failure_reason=f"Semgrep scan exception: {str(e)}",
        severity='',
        description=''
    )
    all_vulns.append(vuln)
```

### 修復 2: 檔案不存在時創建失敗記錄

**檔案**: `src/cwe_detector.py` (第 527-563 行)

```python
if not file_path.exists():
    logger.error(f"檔案不存在: {file_path}")
    
    # ✅ 為每個可用的掃描器創建失敗記錄
    failure_records = []
    
    if ScannerType.BANDIT in self.available_scanners and cwe in self.BANDIT_BY_CWE:
        vuln = CWEVulnerability(
            cwe_id=cwe,
            file_path=str(file_path),
            line_start=0,
            line_end=0,
            function_name=function_name,
            scanner=ScannerType.BANDIT,
            scan_status='failed',
            failure_reason=f"File does not exist: {file_path}",
            severity='',
            description=''
        )
        failure_records.append(vuln)
    
    if ScannerType.SEMGREP in self.available_scanners and cwe in self.SEMGREP_BY_CWE:
        vuln = CWEVulnerability(
            cwe_id=cwe,
            file_path=str(file_path),
            line_start=0,
            line_end=0,
            function_name=function_name,
            scanner=ScannerType.SEMGREP,
            scan_status='failed',
            failure_reason=f"File does not exist: {file_path}",
            severity='',
            description=''
        )
        failure_records.append(vuln)
    
    return failure_records
```

### 修復 3: CSV 生成邏輯改為預設失敗

**檔案**: `src/cwe_scan_manager.py` (第 217-269 行)

```python
# ✅ 預設為未知狀態
scan_status = 'unknown'
failure_reason = ''
has_scan_record = False  # ✅ 標記是否找到任何掃描記錄

if file_result and file_result.details:
    for vuln in file_result.details:
        # 檢查是否是掃描失敗記錄
        if vuln.scan_status == 'failed':
            if scanner_filter is None or (vuln.scanner and vuln.scanner.value == scanner_filter):
                scan_status = 'failed'
                failure_reason = vuln.failure_reason or 'Unknown error'
                has_scan_record = True
                break
        # 檢查是否是目標函式的記錄
        elif vuln.function_name == func_name or (vuln.scan_status == 'success' and not vuln.function_name):
            if scanner_filter is None or (vuln.scanner and vuln.scanner.value == scanner_filter):
                has_scan_record = True
                if vuln.function_name == func_name:
                    func_vulns.append(vuln)
                    # ... 記錄函式資訊 ...

# ✅ 判斷最終狀態
if scan_status == 'failed':
    # 已經標記為失敗
    pass
elif has_scan_record:
    # ✅ 找到了掃描記錄（可能有漏洞，也可能沒漏洞但掃描成功）
    scan_status = 'success'
else:
    # ✅ 沒有找到任何掃描記錄 → 標記為失敗
    scan_status = 'failed'
    failure_reason = f'No scan results found for {scanner_filter or "any scanner"}'
```

## 驗證測試

### 測試腳本: `test_scan_status_fix.py`

#### 測試 1: Semgrep 掃描失敗檢測

**測試場景**: 掃描不存在的檔案

**預期結果**: 
- Bandit 創建 1 個失敗記錄
- Semgrep 創建 1 個失敗記錄

**實際結果**: ✅ 通過
```
✅ 找到 2 個失敗記錄:
  - 掃描器: bandit
    狀態: failed
    原因: File does not exist: /tmp/nonexistent_test_file.py
  - 掃描器: semgrep
    狀態: failed
    原因: File does not exist: /tmp/nonexistent_test_file.py
```

#### 測試 2: 沒有掃描結果時的 CSV 生成

**測試場景**: 空的掃描結果字典

**預期結果**: 
- 所有函式記錄為 `failed`
- 失敗原因: "No scan results found for semgrep"

**實際結果**: ✅ 通過
```
函式: test/file.py_test_func1()
  狀態: failed
  原因: No scan results found for semgrep

函式: test/file.py_test_func2()
  狀態: failed
  原因: No scan results found for semgrep

統計:
  Success: 0
  Failed: 2

✅ 正確：沒有掃描結果時記錄為 failed
```

## 修復前後對比

### 修復前

| 情況 | OriginalScanResult | CWE_Result CSV | 問題 |
|------|-------------------|----------------|------|
| Semgrep 未執行 | 無檔案 | `success` | ❌ 錯誤標記為成功 |
| Semgrep 執行失敗 | 無檔案 | `success` | ❌ 錯誤標記為成功 |
| 檔案不存在 | 無檔案 | `success` | ❌ 錯誤標記為成功 |
| 掃描超時 | 無檔案 | `success` | ❌ 錯誤標記為成功 |

### 修復後

| 情況 | OriginalScanResult | CWE_Result CSV | 狀態 |
|------|-------------------|----------------|------|
| Semgrep 未執行 | 無檔案 | `failed` + 失敗原因 | ✅ 正確 |
| Semgrep 執行失敗 | 無檔案 | `failed` + 錯誤訊息 | ✅ 正確 |
| 檔案不存在 | 無檔案 | `failed` + "File does not exist" | ✅ 正確 |
| 掃描超時 | 無檔案 | `failed` + "timeout" | ✅ 正確 |
| 掃描成功無漏洞 | 有 JSON | `success` + 漏洞數=0 | ✅ 正確 |
| 掃描成功有漏洞 | 有 JSON | `success` + 漏洞詳情 | ✅ 正確 |

## 數據完整性原則

修復後系統遵循以下原則：

1. **✅ 無依據不標記成功**: 沒有原始掃描結果檔案 → 必須標記為 `failed`
2. **✅ 失敗必須有原因**: 所有 `failed` 記錄都包含具體的失敗原因
3. **✅ 成功必須有證據**: `success` 記錄必須對應到實際的掃描結果檔案
4. **✅ 雙掃描器一致性**: Bandit 和 Semgrep 使用相同的失敗處理邏輯
5. **✅ 可追溯性**: 從 CSV 記錄可以追溯到原始 JSON 檔案

## 影響範圍

### 受影響的功能

1. **函式級別掃描**: `scan_from_prompt_function_level()`
2. **單檔掃描**: `scan_single_file()`
3. **CSV 報告生成**: `_save_function_level_csv()`
4. **Artificial Suicide 模式**: 依賴掃描結果的所有功能

### 相容性

- ✅ **向後相容**: CSV 格式未改變
- ✅ **現有程式碼**: 不影響其他模組
- ✅ **測試通過**: 所有現有測試仍然通過

## 建議的後續改進

1. **增強錯誤分類**: 區分「檔案不存在」、「語法錯誤」、「掃描器錯誤」等
2. **重試機制**: 對暫時性失敗（如超時）實施自動重試
3. **告警通知**: 當失敗率超過閾值時發送警報
4. **趨勢分析**: 追蹤失敗率趨勢，識別系統性問題
5. **詳細日誌**: 記錄完整的掃描器輸出到單獨的日誌檔案

## 總結

這次修復解決了一個嚴重的數據完整性問題，確保：

- **不再產生虛假的成功記錄**
- **所有失敗情況都被正確追蹤**
- **研究數據具有可信度和可追溯性**
- **符合安全研究的嚴謹性要求**

修復通過了所有測試驗證，並且不影響現有功能的正常運作。

---

**修復日期**: 2025-10-26  
**修復檔案**: 
- `src/cwe_detector.py`
- `src/cwe_scan_manager.py`

**測試檔案**: 
- `test_scan_status_fix.py`
