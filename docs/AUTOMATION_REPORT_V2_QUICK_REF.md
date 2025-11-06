# AutomationReport V2.0 快速參考

## 🚀 快速開始

### 報告位置
```
ExecutionResult/AutomationReport/
├── automation_report_{timestamp}.json  # JSON 格式
└── automation_report_{timestamp}.txt   # TXT 格式（易讀）
```

### 查看報告
```bash
# 查看最新的 TXT 報告
cat ExecutionResult/AutomationReport/automation_report_*.txt | tail -100

# 查看 JSON 報告
cat ExecutionResult/AutomationReport/automation_report_*.json | jq .
```

## 📊 報告結構

### TXT 報告
```
自動化執行報告
│
├── 📊 執行摘要
│   ├── 總專案數
│   ├── 已處理專案數
│   ├── 成功專案數
│   ├── 失敗專案數
│   ├── 待處理專案數
│   └── 成功率
│
├── 📈 函數處理統計
│   ├── 檔案處理限制
│   ├── 實際處理函數數
│   ├── CSV記錄總數
│   ├── 完整執行專案數
│   └── 未完整執行專案數
│
├── ⏱️ 性能指標
│   ├── 總處理時間
│   ├── 平均處理時間
│   └── 總處理時間_小時
│
├── ✅ 完整執行的專案列表
│   └── 專案名稱 + 函數數量（降序）
│
└── ⚠️ 未完整執行的專案列表
    └── 專案名稱 + 預期/實際/缺少數量
```

### JSON 報告
```json
{
  "report_metadata": {...},
  "execution_summary": {...},
  "function_statistics": {...},
  "performance_metrics": {...},
  "complete_projects": [...],
  "incomplete_projects": [...],
  "all_projects_detail": [...]
}
```

## 🔍 關鍵指標

### 函數處理統計
| 指標 | 說明 |
|------|------|
| 檔案處理限制 | max_files_limit 設定值 |
| 實際處理函數數 | total_files_processed 累計值 |
| CSV記錄總數 | 所有 query_statistics CSV 的總行數 |
| 完整執行專案數 | prompt.txt 行數 = CSV 記錄數 |
| 未完整執行專案數 | prompt.txt 行數 ≠ CSV 記錄數 |

### 專案狀態判定
- **完整執行**: `CSV記錄數 == prompt.txt非空行數 AND 行數 > 0`
- **未完整執行**: `CSV記錄數 != prompt.txt非空行數`

## 💡 使用場景

### 1. 驗證執行完整性
```bash
# 查看未完整執行的專案
grep -A 10 "未完整執行的專案" ExecutionResult/AutomationReport/automation_report_*.txt
```

### 2. 統計處理效率
```bash
# 查看性能指標
grep -A 5 "性能指標" ExecutionResult/AutomationReport/automation_report_*.txt
```

### 3. 分析專案分布
```bash
# 查看完整執行的專案（按函數數量排序）
grep -A 20 "完整執行的專案" ExecutionResult/AutomationReport/automation_report_*.txt
```

### 4. 檢查數據一致性
```python
import json

with open('ExecutionResult/AutomationReport/automation_report_latest.json', 'r') as f:
    report = json.load(f)

stats = report['function_statistics']
print(f"處理限制: {stats['檔案處理限制']}")
print(f"實際處理: {stats['實際處理函數數']}")
print(f"CSV總記錄: {stats['CSV記錄總數']}")
```

## 🛠️ 測試報告生成

### 運行測試
```bash
python tests/test_report_generation.py
```

### 測試輸出
- 生成兩個報告文件（JSON + TXT）
- 在終端顯示 TXT 報告內容
- 驗證數據統計邏輯

## ⚠️ 注意事項

### CSV 記錄數 vs 實際處理數
- CSV 記錄數可能 > 實際處理數
- 原因: 未完整項目的已處理部分會寫入 CSV
- 示例: 處理 100 函數，但 CSV 有 111 條記錄（包含未完整專案）

### 專案狀態更新
- 報告基於 CSV 文件和 prompt.txt 的**當前狀態**
- 如果手動修改 CSV 或 prompt.txt，需重新生成報告
- 報告生成時間戳反映生成時刻

## 📈 數據驗證檢查清單

✅ **執行完整性**
- [ ] 實際處理函數數 <= 檔案處理限制
- [ ] 完整執行專案的函數總和 <= 實際處理函數數
- [ ] CSV記錄總數 = 完整專案函數數 + 未完整專案函數數

✅ **專案分類**
- [ ] 完整執行專案數 + 未完整執行專案數 = CSV 檔案數量
- [ ] 每個專案的 CSV 記錄數 <= prompt.txt 行數

✅ **性能指標**
- [ ] 平均處理時間 = 總處理時間 / 已處理專案數
- [ ] 總處理時間_小時 = 總處理時間 / 3600

## 🔗 相關文件
- `docs/AUTOMATION_REPORT_V2.md`: 詳細更新說明
- `docs/AUTOMATION_REPORT_V2_SUMMARY.md`: 更新總結
- `src/project_manager.py`: 報告生成邏輯
- `tests/test_report_generation.py`: 測試腳本
