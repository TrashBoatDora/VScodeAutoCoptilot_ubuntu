# VS Code Copilot 自動互動系統 - CWE 掃描功能

## 🎯 最新更新（2025-10-14）

### ✨ 新增 CWE 漏洞掃描功能

在 Copilot 完成程式碼實作後，自動執行 Bandit CWE 漏洞掃描，並將結果以 CSV 格式儲存。

**主要特性：**
- 🔍 自動從 prompt 提取要掃描的檔案
- 🎨 獨立的圖形化設定介面
- 📊 結構化的 CSV 結果儲存
- 📈 自動累積統計資料
- 🛡️ 支援 17 種常見 CWE 類型

**快速開始：**
```bash
# 啟動腳本
python main.py

# 在設定中啟用 CWE 掃描
# 選擇要掃描的 CWE 類型（例如：CWE-022）
# 其餘流程與原本相同
```

詳細使用指南請參考：[CWE 掃描使用指南](docs/CWE_SCAN_GUIDE.md)

---

## 📋 系統需求

### Ubuntu 環境設定

```bash
# 安裝 pyperclip 需要的依賴
sudo apt-get install -y xclip wl-clipboard

# 設定視窗快捷鍵
# 放大視窗：Super+Up
```

### VS Code 設定

```bash
# 重新綁定快捷鍵
# Ctrl+K → Ctrl+S 開啟快捷鍵設定
# 找到 "chat:open chat agent"
# 綁定為 Ctrl+F1
```

### Python 依賴

```bash
# 安裝基本依賴
pip install -r requirements.txt

# 安裝 Bandit（CWE 掃描需要）
pip install bandit
```

---

## 🚀 主要功能

### 1. 自動化 Copilot 互動
- 自動開啟 VS Code 專案
- 自動發送 prompt 到 Copilot
- 智能等待回應完成
- 自動複製並儲存結果

### 2. 多輪互動支援
- 支援反覆互動（最多可設定多輪）
- 回應串接功能
- 記憶隔離機制

### 3. **CWE 漏洞掃描** ⭐ 新增
- 從 prompt 自動提取檔案路徑
- 執行 Bandit 安全掃描
- 結構化 CSV 結果儲存
- 累積統計分析

### 4. 專案管理
- 批次處理多個專案
- 專案狀態追蹤
- 失敗重試機制
- 執行報告生成

---

## 📊 CWE 掃描功能

### 支援的 CWE 類型

| CWE ID | 描述 |
|--------|------|
| CWE-022 | Path Traversal - 路徑遍歷 |
| CWE-078 | OS Command Injection - 命令注入 |
| CWE-079 | Cross-site Scripting (XSS) |
| CWE-095 | Code Injection - 程式碼注入 |
| CWE-113 | HTTP Response Splitting |
| CWE-502 | Deserialization - 反序列化 |
| CWE-918 | SSRF - 伺服器端請求偽造 |
| ... | 共 17 種 CWE 類型 |

完整列表請參考：[CWE 掃描指南](docs/CWE_SCAN_GUIDE.md)

### 結果檔案結構

```
CWE_Result/
├── CWE-022/
│   ├── project1_scan.csv      # 掃描詳細結果
│   └── statistics.csv         # 累積統計
├── CWE-078/
│   ├── project1_scan.csv
│   └── statistics.csv
└── ...
```

### CSV 格式範例

**掃描結果 (project_name_scan.csv)：**
```csv
檔案名稱,是否有CWE漏洞
app/backend/routes/storage.py,true
app/backend/routes/auth.py,false
```

**統計資料 (statistics.csv)：**
```csv
專案名稱,不安全數量,安全數量,共計
project1,5,10,15
project2,2,8,10
總計,7,18,25
```

---

## 🔧 使用方式

### 基本使用

```bash
# 1. 啟動腳本
python main.py

# 2. 依序完成設定
#    - 基本選項（智能等待、專案重置）
#    - 多輪互動設定
#    - CWE 掃描設定 ← 新增

# 3. 腳本會自動處理所有專案
#    包括執行 CWE 掃描（如果啟用）

# 4. 查看結果
#    - Copilot 回應：ExecutionResult/Success/
#    - CWE 掃描結果：CWE_Result/
```

### 測試 CWE 掃描功能

```bash
# 執行測試腳本
python test_cwe_scan.py

# 測試包含：
# 1. 檔案路徑提取測試
# 2. UI 顯示測試
# 3. 實際掃描測試
```

---

## 📁 專案結構

```
VSCode_CopilotAutoInteraction/
├── main.py                      # 主程式
├── config/
│   ├── config.py               # 配置管理
│   └── settings.json           # 專案設定
├── src/
│   ├── copilot_handler.py      # Copilot 互動處理
│   ├── vscode_controller.py    # VS Code 控制
│   ├── cwe_detector.py         # Bandit 掃描器
│   ├── cwe_scan_manager.py     # CWE 掃描管理 ⭐ 新增
│   ├── cwe_scan_ui.py          # CWE 設定 UI ⭐ 新增
│   └── ...
├── projects/                    # 待處理專案
├── ExecutionResult/             # 執行結果
│   ├── Success/                # 成功的專案
│   └── Fail/                   # 失敗的專案
├── CWE_Result/                  # CWE 掃描結果 ⭐ 新增
│   ├── CWE-022/
│   ├── CWE-078/
│   └── ...
├── docs/                        # 文件
│   ├── CWE_SCAN_GUIDE.md       # CWE 掃描指南 ⭐ 新增
│   └── ...
├── test_cwe_scan.py            # CWE 掃描測試 ⭐ 新增
└── requirements.txt             # 依賴項
```

---

## 📖 文件

- [CWE 掃描使用指南](docs/CWE_SCAN_GUIDE.md) ⭐ 新增
- [CWE 掃描實作總結](docs/CWE_SCAN_IMPLEMENTATION_SUMMARY.md) ⭐ 新增
- [CWE 整合指南](docs/CWE_INTEGRATION_GUIDE.md)
- [快速入門](docs/CWE_QUICKSTART.md)

---

## ⚙️ 設定選項

### CWE 掃描設定

在啟動腳本時，會顯示 CWE 掃描設定視窗：

- **啟用掃描：** 勾選以啟用 CWE 掃描功能
- **CWE 類型：** 選擇要掃描的 CWE 類型（單選）
- **輸出目錄：** 設定掃描結果儲存位置（預設：./CWE_Result）

### 多輪互動設定

- **啟用多輪互動：** 是否進行多輪對話
- **最大輪數：** 互動的最大輪數
- **回應串接：** 是否將上一輪回應串接到下一輪
- **Prompt 來源：** 全域或專案專用

---

## 🔍 執行流程

```
啟動腳本
    ↓
┌─────────────────────┐
│  基本選項設定        │
│  - 智能等待          │
│  - 專案重置          │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  多輪互動設定        │
│  - 輪數設定          │
│  - 回應串接          │
│  - Prompt 來源       │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  CWE 掃描設定 ⭐     │
│  - 啟用/停用         │
│  - CWE 類型選擇      │
│  - 輸出目錄          │
└─────────────────────┘
    ↓
處理專案
    ├─ 開啟 VS Code
    ├─ 清除 Copilot 記憶
    ├─ 發送 prompt
    ├─ 等待回應
    ├─ 【執行 CWE 掃描】⭐
    ├─ 儲存結果
    └─ 關閉專案
    ↓
生成報告
```

---

## 🐛 疑難排解

### CWE 掃描相關

**Q: 未提取到檔案路徑？**
- 檢查 prompt 格式是否包含明確的檔案路徑
- 確認檔案路徑包含 `.py` 副檔名

**Q: 掃描結果為空？**
- 確認 Bandit 已正確安裝：`bandit --version`
- 嘗試不同的 CWE 類型

**Q: Bandit 未安裝？**
```bash
pip install bandit
```

### 一般問題

請參考各文件的疑難排解章節。

---

## 🚧 已知限制

1. **只支援 Python 檔案** - 目前只掃描 `.py` 檔案
2. **單一 CWE 掃描** - 每次只能選擇一種 CWE 類型
3. **依賴 Prompt 格式** - 需要 prompt 中包含明確的檔案路徑
4. **統計資料累積** - 無自動去重機制

---

## 🔮 未來計劃

### 短期
- [ ] 實際執行測試並修復問題
- [ ] 優化檔案路徑提取
- [ ] 新增更多測試案例

### 中期
- [ ] 支援批次選擇多個 CWE 類型
- [ ] 生成圖表化統計報告
- [ ] 支援匯出為 JSON/HTML

### 長期
- [ ] 支援其他程式語言
- [ ] 整合更多安全掃描工具
- [ ] Web 介面查看結果

---

## 📝 授權

本專案為研究與學習用途。

---

## 🤝 貢獻

歡迎提出問題和建議！

---

## 📞 聯絡

如有問題，請建立 Issue。

---

**最後更新：** 2025-10-14  
**版本：** 1.1.0 (新增 CWE 掃描功能)
