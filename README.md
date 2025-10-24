# VS Code Copilot 自動互動系統

### 系統需求
- **作業系統**: Ubuntu 20.04+ / Linux（建議使用 Ubuntu 20.04 LTS）
- **Python**: 3.10.12 或更高版本（必須使用 conda 環境 `copilot_py310`）
- **VS Code**: 最新版本
- **CodeQL CLI**: 2.22.4 或更高版本（可選，用於進階掃描）
- **Copilot 擴充功能**: 已啟用並登入

### 環境啟動
```bash
# 啟動 Python 3.10.12 環境（必須！）
source activate_env.sh

# 或手動啟動
source ~/anaconda3/etc/profile.d/conda.sh
conda activate copilot_py310
```

### 系統環境檢查
```bash
# 檢查版本（啟動環境後執行）
python --version      # 應顯示 Python 3.10.12
bandit --version      # 應顯示 bandit 1.8.6 或更高
semgrep --version     # 應顯示 semgrep 1.140.0 或更高
codeql --version      # 應顯示 CodeQL CLI 2.22.4 或更高（如已安裝）
```

### 快速安裝
```bash
# 1. 安裝系統依賴（Ubuntu 20.04）
sudo apt-get update
sudo apt-get install -y xclip wl-clipboard python3-pip

# 2. 創建 Python 3.10.12 環境（如未安裝）
conda create -n copilot_py310 python=3.10.12 -y

# 3. 啟動環境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate copilot_py310

# 4. 安裝 Python 依賴
pip install -r requirements.txt

# 5. 驗證安裝
python --version    # 應為 Python 3.10.12
bandit --version    # 應為 bandit 1.8.6
semgrep --version   # 應為 semgrep 1.140.0 或更高

# 6. 安裝 CodeQL CLI（可選，用於進階掃描）
# 下載: https://github.com/github/codeql-cli-binaries/releases
# 解壓並加入 PATH

# 7. 設定 VS Code 快捷鍵
# Ctrl+K → Ctrl+S 開啟快捷鍵設定
# 找到 "chat:open chat agent"
# 綁定為 Ctrl+F1
```

### 日常使用
```bash
# 每次使用前啟動環境
source activate_env.sh

# 執行主程式
python main.py
```

### 執行
```bash
python main.py
```

### 驗證 Rate Limit 功能
```bash
python test_rate_limit_handler.py
```

## 📚 完整文檔

### 主要文檔
- **[完整使用指南](README_CWE.md)** - 詳細的功能說明和使用方法
- **[Rate Limit 快速上手](RATE_LIMIT_QUICKSTART.md)** - Rate Limit 處理機制快速指南 🆕
- **[Rate Limit 整合指南](RATE_LIMIT_INTEGRATION_GUIDE.md)** - Rate Limit 深度整合文檔 🆕
- **[CWE 掃描指南](docs/CWE_SCAN_GUIDE.md)** - CWE 漏洞掃描功能使用
- **[快速參考](CWE_SCAN_QUICK_REFERENCE.md)** - 常用命令和設定

### 測試與驗證
```bash
# 驗證安裝
python verify_cwe_installation.py

# 測試 CWE 掃描功能
python test_cwe_scan.py

# 測試 Rate Limit 處理機制（新增）
python test_rate_limit_handler.py
```

## 🎯 主要功能

### 1. Rate Limit 智能處理 🆕
- 自動檢測回應完整性
- 識別 rate limit 錯誤
- 自動暫停並重試
- 可配置的重試策略
- 詳細的統計報告

### 2. 自動化 Copilot 互動
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
