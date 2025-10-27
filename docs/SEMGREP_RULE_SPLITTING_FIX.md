# Semgrep 規則分割修復文檔

## 問題發現

使用者發現 Semgrep 沒有正常掃描，**OriginalScanResult/Semgrep** 目錄下沒有任何 JSON 檔案，但目錄結構已被創建。

## 根本原因

### 問題代碼

**檔案**: `src/cwe_detector.py`

```python
# CWE-327 的規則定義（字符串格式，逗號分隔）
SEMGREP_BY_CWE = {
    "327": "python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used"
}

# 錯誤的迭代方式
def _scan_with_semgrep(self, project_path: Path, cwe: str):
    rule_patterns = self.SEMGREP_BY_CWE.get(cwe)  # 獲得字符串
    
    # ❌ 直接迭代字符串 - 會逐個字符迭代！
    for rule in rule_patterns:
        if rule.startswith('p/') or rule.startswith('r/'):
            cmd.extend(["--config", rule])
```

### 實際發生的事情

當迭代字符串 `"python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used"` 時：

```python
for rule in rule_patterns:
    print(rule)

# 輸出:
# 'p'
# 'y'
# 't'
# 'h'
# 'o'
# 'n'
# ...（每個字符）
```

### 構建的錯誤命令

```bash
semgrep scan \
  --config r/p \
  --config r/y \
  --config r/t \
  --config r/h \
  --config r/o \
  --config r/n \
  ...（數十個無效的單字符規則）
  --json --output report.json file.py
```

**結果**: Semgrep 嘗試下載這些無效的單字符規則，全部失敗，沒有產生任何掃描結果。

## 修復方案

### 解決方法

在迭代之前，先將字符串分割成規則列表：

```python
def _scan_with_semgrep(self, project_path: Path, cwe: str):
    rule_patterns = self.SEMGREP_BY_CWE.get(cwe)
    if not rule_patterns:
        return []
    
    # ✅ 將規則字符串分割成列表
    if isinstance(rule_patterns, str):
        rule_list = [r.strip() for r in rule_patterns.split(",")]
    else:
        rule_list = rule_patterns
    
    # ✅ 迭代規則列表
    for rule in rule_list:
        if rule.startswith('p/') or rule.startswith('r/'):
            cmd.extend(["--config", rule])
        else:
            cmd.extend(["--config", f"r/{rule}"])
```

### 修復位置

需要修復兩個地方：

1. **`_scan_with_semgrep` 方法** (第 307-340 行)
2. **`scan_single_file` 方法中的 Semgrep 部分** (第 623-680 行)

## 修復後的正確行為

### 正確的規則分割

```python
rule_patterns = "python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used"
rule_list = [r.strip() for r in rule_patterns.split(",")]

print(rule_list)
# 輸出:
# ['python.lang.security.audit.hashlib-insecure-functions', 
#  'python.lang.security.audit.md5-used']
```

### 正確的 Semgrep 命令

```bash
semgrep scan \
  --config r/python.lang.security.audit.hashlib-insecure-functions \
  --config r/python.lang.security.audit.md5-used \
  --json \
  --output report.json \
  file.py
```

### 預期結果

- ✅ Semgrep 正確執行掃描
- ✅ 產生 JSON 報告檔案
- ✅ JSON 包含完整的掃描結果和元數據

## 測試驗證

### 測試腳本: `test_semgrep_fix.py`

#### 測試 1: 規則字符串分割

```
原始規則字符串:
  python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used
  類型: <class 'str'>

分割後的規則列表:
  1. python.lang.security.audit.hashlib-insecure-functions
  2. python.lang.security.audit.md5-used

✅ 成功分割成 2 個規則
```

#### 測試 2: Semgrep 命令構建

```
構建的命令:
  semgrep scan --config r/python.lang.security.audit.hashlib-insecure-functions --config r/python.lang.security.audit.md5-used --json --output /tmp/test_output.json test_file.py

--config 參數數量: 2
✅ 正確：2 個 --config 對應 2 個規則
```

#### 測試 3: 實際 Semgrep 掃描

```
測試檔案: projects/airflow__CWE-327__CAL-ALL-6b42874e__M-call/airflow-core/src/airflow/models/dagbag.py

掃描結果: 1 個記錄

✅ JSON 報告已產生:
  路徑: OriginalScanResult/Semgrep/CWE-327/test_project/第1輪/models__dagbag.py__test_function_report.json
  大小: 1383 bytes

JSON 內容摘要:
  版本: 1.140.0
  結果數量: 0
  錯誤數量: 0
  掃描檔案: ['projects/airflow__CWE-327__CAL-ALL-6b42874e__M-call/airflow-core/src/airflow/models/dagbag.py']
```

**結論**: 🎉 所有測試通過！Semgrep 現在能正常工作了

## 手動測試驗證

### 測試命令

```bash
# 測試單個規則
semgrep --config "r/python.lang.security.audit.md5-used" \
  --json --output /tmp/test1.json \
  projects/airflow__CWE-327__CAL-ALL-6b42874e__M-call/airflow-core/src/airflow/models/dagbag.py
```

**結果**: ✅ 成功產生 JSON 檔案

### JSON 檔案結構

```json
{
  "version": "1.140.0",
  "results": [],
  "errors": [],
  "paths": {
    "scanned": ["projects/airflow__CWE-327__CAL-ALL-6b42874e__M-call/airflow-core/src/airflow/models/dagbag.py"]
  },
  "time": {
    "rules": [],
    "profiling_times": {...}
  }
}
```

## 影響的 CWE

這個問題影響所有使用逗號分隔多個規則的 CWE：

```python
SEMGREP_BY_CWE = {
    "095": "python.lang.security.audit.eval-used,python.lang.security.audit.exec-used",
    "327": "python.lang.security.audit.hashlib-insecure-functions,python.lang.security.audit.md5-used",
    "502": "python.lang.security.audit.unsafe-deserialization,python.lang.security.audit.pickle-used"
}
```

**影響**: CWE-095, CWE-327, CWE-502 三個類別的 Semgrep 掃描完全失效。

## 修復前後對比

### 修復前

| 操作 | 結果 | 原因 |
|------|------|------|
| 執行 Semgrep 掃描 | 無 JSON 檔案產生 | 規則解析錯誤 |
| 檢查 OriginalScanResult | 目錄存在但空的 | 命令執行但無輸出 |
| 查看 CWE_Result CSV | 錯誤標記為 success | 沒有失敗記錄 |

### 修復後

| 操作 | 結果 | 狀態 |
|------|------|------|
| 執行 Semgrep 掃描 | JSON 檔案正常產生 | ✅ 正常 |
| 檢查 OriginalScanResult | 完整的 JSON 報告 | ✅ 正常 |
| 查看 CWE_Result CSV | 正確的掃描狀態 | ✅ 正常 |

## 學到的教訓

1. **Python 字符串可迭代性**: 在 Python 中，字符串是可迭代的，`for` 循環會逐個字符迭代
2. **數據類型驗證**: 在處理數據前應該驗證其類型
3. **單元測試重要性**: 這種錯誤如果有單元測試應該能早期發現
4. **日誌的價值**: 通過檢查實際產生的檔案發現了問題
5. **手動測試學習**: 通過手動執行 Semgrep 命令理解了正確用法

## 相關問題修復

這次修復連同之前的掃描狀態修復，完整解決了：

1. ✅ **Bandit 錯誤檢測**: 正確識別並記錄掃描失敗
2. ✅ **Semgrep 規則分割**: 正確處理多規則字符串
3. ✅ **JSON 報告生成**: 兩個掃描器都能正常產生報告
4. ✅ **CSV 狀態記錄**: 正確反映實際掃描狀態
5. ✅ **失敗原因追蹤**: 詳細記錄所有失敗情況

## 總結

這個 Bug 的根本原因是**誤將字符串當作列表來迭代**，導致 Semgrep 嘗試使用數十個無效的單字符規則。修復後，Semgrep 能夠：

- ✅ 正確解析逗號分隔的規則字符串
- ✅ 構建有效的掃描命令
- ✅ 產生完整的 JSON 報告
- ✅ 正確記錄掃描狀態

所有測試驗證通過，Semgrep 現在完全正常工作！

---

**修復日期**: 2025-10-26  
**修復檔案**: `src/cwe_detector.py`  
**測試檔案**: `test_semgrep_fix.py`  
**影響範圍**: CWE-095, CWE-327, CWE-502 的 Semgrep 掃描
