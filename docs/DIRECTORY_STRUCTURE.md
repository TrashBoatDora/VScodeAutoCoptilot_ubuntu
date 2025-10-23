# CWE 掃描結果目錄結構說明

## 目錄用途說明

本系統使用以下兩個目錄來儲存 CWE 掃描相關的結果：

### 1. `CWE_Result/` - 統計結果目錄 📊

**用途**: 儲存經過處理和統計的掃描結果

**格式**: CSV

**結構**:
```
CWE_Result/
├── CWE-022/
│   ├── Bandit/
│   │   └── {專案名稱}_function_level_scan.csv
│   └── Semgrep/
│       └── {專案名稱}_function_level_scan.csv
├── CWE-078/
│   ├── Bandit/
│   └── Semgrep/
...
```

**內容**: 
- 函式級別的漏洞統計
- 包含欄位：輪數、行號、檔案名稱_函式名稱、函式起始行、函式結束行、漏洞數量、漏洞行號、掃描器、信心度、嚴重性、問題描述、掃描狀態、失敗原因

**用途場景**:
- 實驗數據收集
- 統計分析
- 生成報告
- Excel 或數據分析工具處理

---

### 2. `OriginalScanResult/` - 原始掃描結果目錄 📁

**用途**: 儲存 Bandit 和 Semgrep 工具的原生掃描結果

**格式**: JSON

**結構**:
```
OriginalScanResult/
├── Bandit/
│   └── CWE-{CWE編號}/
│       └── {專案名稱}/
│           └── report.json
└── Semgrep/
    └── CWE-{CWE編號}/
        └── {專案名稱}/
            └── report.json
```

**內容**:
- 掃描工具的完整原始輸出
- 包含所有錯誤、警告和漏洞詳情
- 保留工具的原生數據結構

**用途場景**:
- 深入分析具體漏洞
- 驗證系統處理的正確性
- 使用掃描工具的其他功能
- 二次分析和研究

---

## ⚠️ 已廢棄的目錄

### `cwe_scan_results/` - 已廢棄 ❌

**狀態**: 已移除（舊版設計遺留）

**原因**:
- 這是舊版設計的中間目錄
- 實際上不儲存任何內容
- 造成混淆且浪費磁碟空間
- 已被 `OriginalScanResult/` 取代

**遷移**:
- 如果您的系統中還有這個目錄，可以安全地刪除
- 使用提供的清理腳本：`./cleanup_cwe_scan_results.sh`

---

## 目錄對比表

| 目錄 | 用途 | 格式 | 內容 | 狀態 |
|-----|------|------|------|------|
| `CWE_Result/` | 統計結果 | CSV | 函式級別統計 | ✅ 使用中 |
| `OriginalScanResult/` | 原始結果 | JSON | 完整掃描輸出 | ✅ 使用中 |
| `cwe_scan_results/` | (無) | - | (空) | ❌ 已廢棄 |

---

## 使用範例

### 查看統計結果（CSV）

```bash
# 查看特定專案的 Bandit 統計結果
cat CWE_Result/CWE-078/Bandit/my_project_function_level_scan.csv

# 使用表格工具查看
column -t -s',' CWE_Result/CWE-078/Bandit/my_project_function_level_scan.csv | less -S
```

### 查看原始結果（JSON）

```bash
# 查看 Bandit 原始掃描結果
cat OriginalScanResult/Bandit/CWE-078/my_project/report.json | jq '.'

# 查看 Semgrep 原始掃描結果
cat OriginalScanResult/Semgrep/CWE-079/my_project/report.json | jq '.results'

# 統計漏洞數量
cat OriginalScanResult/Bandit/CWE-078/my_project/report.json | jq '.metrics.total_issues'
```

---

## 清理與維護

### 清理廢棄目錄

```bash
# 自動清理 cwe_scan_results 目錄
./cleanup_cwe_scan_results.sh
```

### 清理舊的掃描結果

```bash
# 清理超過 30 天的原始掃描結果
find OriginalScanResult -name "report.json" -mtime +30 -delete

# 清理超過 30 天的統計結果
find CWE_Result -name "*.csv" -mtime +30 -delete
```

### 備份重要結果

```bash
# 備份統計結果
tar -czf CWE_Result_backup_$(date +%Y%m%d).tar.gz CWE_Result/

# 備份原始掃描結果
tar -czf OriginalScanResult_backup_$(date +%Y%m%d).tar.gz OriginalScanResult/
```

---

## 常見問題

### Q: 為什麼有兩個目錄？

**A**: 
- `CWE_Result/` 用於統計分析，格式簡潔易於處理
- `OriginalScanResult/` 用於深入分析，保留完整資訊

### Q: cwe_scan_results 是什麼？

**A**: 
這是舊版設計遺留的目錄，現已廢棄。如果存在，可以安全刪除。

### Q: 如何選擇使用哪個目錄？

**A**:
- 需要統計分析 → `CWE_Result/` (CSV)
- 需要詳細資訊 → `OriginalScanResult/` (JSON)
- 需要驗證正確性 → `OriginalScanResult/` (JSON)

### Q: 這些目錄會自動清理嗎？

**A**: 
不會。需要手動清理或設置定期清理任務。

---

## 相關文件

- [CWE 掃描指南](CWE_SCAN_GUIDE.md)
- [函式級別掃描](FUNCTION_LEVEL_SCANNING.md)
- [CWE 整合指南](CWE_INTEGRATION_GUIDE.md)
