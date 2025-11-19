# Copilot Auto Interaction - 環境移植指南

本專案使用 Conda 環境管理，以下說明如何在新機器上重建相同的環境。

## 必要條件

1. **Anaconda/Miniconda**
   - 下載並安裝: https://docs.conda.io/en/latest/miniconda.html
   - 確認安裝: `conda --version`

2. **系統需求**
   - Linux (Ubuntu 20.04+ 或相容系統)
   - Python 3.10.12 (由 Conda 自動安裝)
   - X11 環境 (用於 GUI 自動化)

## 快速安裝 (推薦)

```bash
# 1. 複製整個專案到新機器
git clone <repository-url>
cd VSCode_CopilotAutoInteraction

# 2. 執行自動安裝腳本
./install_env.sh
```

安裝腳本會自動:
- 檢查 Conda 是否已安裝
- 使用 `environment.yml` 建立完整環境
- 安裝所有必要的套件 (包含 Bandit 1.9.1 和 Semgrep 1.143.1)
- 驗證安裝結果

## 手動安裝

如果自動安裝腳本無法執行，可以手動操作:

### 方法 1: 使用 environment.yml (推薦)

```bash
# 建立環境
conda env create -f environment.yml

# 啟動環境
conda activate copilot_py310
```

### 方法 2: 使用 requirements.txt

```bash
# 建立基礎環境
conda create -n copilot_py310 python=3.10.12 -y

# 啟動環境
conda activate copilot_py310

# 安裝套件
pip install -r requirements.txt
```

## 驗證安裝

```bash
# 啟動環境
conda activate copilot_py310

# 檢查版本
python --version           # 應顯示 Python 3.10.12
bandit --version          # 應顯示 bandit 1.9.1
semgrep --version         # 應顯示 1.143.1

# 執行測試
python -m pytest tests/   # (如果有測試套件)
```

## 環境啟動

**使用快速腳本:**
```bash
source activate_env.sh
```

**手動啟動:**
```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate copilot_py310
```

## 主要套件版本

本環境包含以下關鍵套件:

- **安全掃描工具**
  - Bandit 1.9.1 (Python 安全漏洞掃描)
  - Semgrep 1.143.1 (多語言靜態分析)

- **自動化工具**
  - PyAutoGUI 0.9.54 (GUI 自動化)
  - OpenCV 4.12.0.88 (圖像處理)
  - Pillow 12.0.0 (圖像處理)

- **其他工具**
  - NumPy 2.2.6
  - Requests 2.32.5
  - PyYAML 6.0.3

完整套件清單請參考 `environment.yml` 和 `requirements.txt`。

## 常見問題

### Q: 安裝失敗，顯示 "CondaHTTPError"
**A:** 可能是網路問題或套件源問題。嘗試:
```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

### Q: Bandit 或 Semgrep 找不到
**A:** 確保環境已正確啟動:
```bash
conda activate copilot_py310
which bandit
which semgrep
```

### Q: GUI 自動化無法運作
**A:** 確認系統有 X11 環境:
```bash
echo $DISPLAY  # 應顯示 :0 或類似值
xdpyinfo       # 測試 X11 連接
```

### Q: 如何更新環境?
**A:** 當專案有新的套件需求時:
```bash
# 更新環境定義檔案
conda env export > environment.yml
pip freeze > requirements.txt

# 在新機器上重新安裝
./install_env.sh
```

## 移除環境

如果需要完全移除環境:
```bash
conda deactivate
conda env remove -n copilot_py310
```

## 技術支援

如遇到問題，請檢查:
1. `logs/` 目錄下的日誌檔案
2. 專案的 Issues 頁面
3. 相關文檔: `docs/` 目錄

---

**最後更新**: 2025-11-19  
**環境版本**: copilot_py310  
**Python 版本**: 3.10.12
