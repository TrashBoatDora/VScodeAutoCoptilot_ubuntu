# CWE 掃描功能 - 快速參考

## 🚀 快速開始

### 1. 啟動腳本
```bash
python main.py
```

### 2. 設定 CWE 掃描
在 CWE 掃描設定視窗中：
- ✅ 勾選「啟用 CWE 掃描功能」
- 選擇 CWE 類型（例如：CWE-022）
- 確認輸出目錄（預設：./CWE_Result）
- 點擊「確認」

### 3. 自動執行
腳本會在處理每個專案時自動執行 CWE 掃描

### 4. 查看結果
```bash
# 掃描詳細結果
cat CWE_Result/CWE-022/{project_name}_scan.csv

# 統計資料
cat CWE_Result/CWE-022/statistics.csv
```

---

## 📋 支援的 CWE 類型（17 種）

| ID | 描述 |
|----|------|
| 022 | Path Traversal |
| 078 | OS Command Injection |
| 079 | XSS |
| 095 | Code Injection |
| 113 | HTTP Response Splitting |
| 117 | Log Injection |
| 326 | Weak Encryption |
| 327 | Broken Cryptography |
| 329 | CBC without Random IV |
| 347 | JWT Vulnerabilities |
| 377 | Insecure Temporary File |
| 502 | Deserialization |
| 643 | XPath Injection |
| 760 | Predictable Salt |
| 918 | SSRF |
| 943 | SQL Injection |
| 1333 | ReDoS |

---

## 📂 結果檔案結構

```
CWE_Result/
└── CWE-{type}/
    ├── {project}_scan.csv    # 詳細結果
    └── statistics.csv        # 統計（累積）
```

---

## 📊 CSV 格式

### 詳細結果
```csv
檔案名稱,是否有CWE漏洞
app/routes/storage.py,true
app/routes/auth.py,false
```

### 統計資料
```csv
專案名稱,不安全數量,安全數量,共計
project1,5,10,15
總計,5,10,15
```

---

## 🧪 測試功能

```bash
# 執行測試
python test_cwe_scan.py

# 驗證安裝
python verify_cwe_installation.py
```

---

## 🔧 常見問題

### Q: 未提取到檔案路徑？
**A:** 確認 prompt 格式包含明確的檔案路徑，例如：
```
請幫我定位到 app/backend/routes/storage.py 的函式
```

### Q: 掃描結果為空？
**A:** 
1. 檢查 Bandit 是否安裝：`bandit --version`
2. 確認選擇的 CWE 類型適合目標檔案
3. 檢查檔案是否存在

### Q: Bandit 未安裝？
**A:**
```bash
pip install bandit
```

---

## 📖 詳細文件

- [完整使用指南](docs/CWE_SCAN_GUIDE.md)
- [實作總結](docs/CWE_SCAN_IMPLEMENTATION_SUMMARY.md)
- [主 README](README_CWE.md)

---

## 🎯 執行流程

```
啟動 → 基本設定 → 互動設定 → CWE設定 → 處理專案
                                    ↓
                          開啟 → 發送 → 等待 → 掃描 → 儲存
```

---

## 💡 提示

1. **首次使用**：選擇 CWE-022（最常見）
2. **Prompt 格式**：確保包含完整檔案路徑
3. **結果查看**：用 Excel 開啟 CSV 檔案
4. **累積統計**：會自動追加，不會覆蓋

---

**快速聯絡：** 有問題請建立 Issue  
**版本：** 1.0.0  
**最後更新：** 2025-10-14
