# VS Code Copilot 自動互動系統

## 🚀 快速開始

### 系統需求
- Ubuntu / Linux
- Python 3.8+
- VS Code
- Copilot 擴充功能

### 快速安裝
```bash
# 1. 安裝系統依賴（Ubuntu）
sudo apt-get install -y xclip wl-clipboard

# 2. 安裝 Python 依賴
pip install -r requirements.txt

# 3. 安裝 Bandit（CWE 掃描需要）
pip install bandit

# 4. 設定 VS Code 快捷鍵
# Ctrl+K → Ctrl+S 開啟快捷鍵設定
# 找到 "chat:open chat agent"
# 綁定為 Ctrl+F1
```

### 執行
```bash
python main.py
```

## 📚 完整文檔

### 主要文檔
- **[完整使用指南](README_CWE.md)** - 詳細的功能說明和使用方法
- **[CWE 掃描指南](docs/CWE_SCAN_GUIDE.md)** - CWE 漏洞掃描功能使用
- **[快速參考](CWE_SCAN_QUICK_REFERENCE.md)** - 常用命令和設定

### 測試與驗證
```bash
# 驗證安裝
python verify_cwe_installation.py

# 測試 CWE 掃描功能
python test_cwe_scan.py
```

## 🎯 主要功能

### 1. 自動化 Copilot 互動
- 自動開啟專案
- 自動發送 prompt
- 智能等待回應
- 自動儲存結果

### 2. 多輪互動支援
- 反覆互動功能
- 回應串接
- 記憶隔離

### 3. CWE 漏洞掃描 ⭐
- 支援 17 種 CWE 類型
- 自動從 prompt 提取檔案
- CSV 格式結果儲存
- 累積統計分析

### 4. 專案管理
- 批次處理
- 狀態追蹤
- 執行報告

## 📂 專案結構

```
├── main.py                      # 主程式
├── src/                         # 核心模組
│   ├── copilot_handler.py       # Copilot 互動
│   ├── cwe_scan_manager.py      # CWE 掃描管理
│   ├── cwe_scan_ui.py           # CWE 設定 UI
│   └── ...
├── config/                      # 配置
├── projects/                    # 待處理專案
├── ExecutionResult/             # 執行結果
├── CWE_Result/                  # CWE 掃描結果
└── docs/                        # 詳細文檔

```

## ⚙️ 配置

程式啟動時會顯示三個設定視窗：
1. **基本選項** - 智能等待、專案重置
2. **多輪互動設定** - 輪數、回應串接
3. **CWE 掃描設定** - CWE 類型選擇

## 🔧 常見問題

### Bandit 未安裝？
```bash
pip install bandit
```

### 剪貼簿問題？
```bash
sudo apt-get install -y xclip wl-clipboard
```

### VS Code 快捷鍵設定
按 `Ctrl+K` 再按 `Ctrl+S`，搜尋 "chat:open"，設定為 `Ctrl+F1`

## 📞 問題回報

如有問題，請建立 Issue。

---

**版本**: 1.1.0  
**最後更新**: 2025-10-14  
**授權**: 研究與學習用途
