# CWE 漏洞檢測 - 簡化版快速入門

## 🎯 簡化後的功能

我們簡化了 CWE 掃描功能，**只使用 Bandit** 作為掃描器，這樣：
- ✅ 安裝更簡單（只需 `pip install bandit`）
- ✅ 掃描更快速（不需要複雜的規則配置）
- ✅ 程式碼更簡潔（減少依賴和複雜度）
- ✅ 涵蓋大部分常見的 Python 安全問題

## ⚡ 3 分鐘快速開始

### 步驟 1: 安裝 Bandit

```bash
# 進入專案目錄
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction

# 啟動虛擬環境
source .venv/bin/activate

# 安裝 Bandit
pip install bandit

# 或者安裝所有依賴
pip install -r requirements.txt
```

### 步驟 2: 測試安裝

```bash
# 檢查 Bandit 是否正確安裝
bandit --version

# 執行整合測試
python tests/test_cwe_integration.py
```

### 步驟 3: 啟用 CWE 掃描

編輯 `config/config.py`:

```python
# 將 CWE_SCAN_ENABLED 改為 True
CWE_SCAN_ENABLED = True
```

### 步驟 4: 開始使用

```bash
# 運行主程式，會自動顯示 CWE 設定對話框
python main.py
```

## 📋 支援的 CWE 類型（17 種）

Bandit 支援以下 CWE 類型：

| CWE | 名稱 | 嚴重性 | Bandit 規則 |
|-----|------|--------|-------------|
| 022 | Path Traversal | 高 | B202 |
| 078 | OS Command Injection | 嚴重 | B102, B601-609 |
| 079 | Cross-site Scripting | 高 | B704 |
| 095 | Code Injection | 嚴重 | B307, B506 |
| 113 | HTTP Response Splitting | 中 | B201 |
| 117 | Log Injection | 中 | B608 |
| 326 | Inadequate Encryption | 高 | B505 |
| 327 | Broken Cryptography | 高 | B324, B502-504 |
| 329 | CBC without Random IV | 中 | B507 |
| 347 | JWT Signature Bypass | 高 | B506 |
| 377 | Insecure Temporary File | 中 | B108 |
| 502 | Deserialization | 嚴重 | B301-306, B506 |
| 643 | XPath Injection | 高 | B320 |
| 760 | Predictable Salt | 中 | B303 |
| 918 | SSRF | 嚴重 | B310, B411, B413 |
| 943 | SQL Injection | 嚴重 | B608 |
| 1333 | Inefficient Regex | 低 | B110 |

## 💡 使用範例

### 範例 1: 掃描單一專案

```bash
# 基本掃描
python -m src.cwe_detector ./projects/example_project

# 只掃描高風險 CWE（命令注入、SQL 注入、反序列化）
python -m src.cwe_detector ./projects/example_project --cwes 078 943 502

# 查看掃描報告
cat ./cwe_scan_results/example_project_cwe_report.json

# 查看生成的提示詞
cat ./prompts/cwe_generated/example_project_prompt.txt
```

### 範例 2: 掃描單一檔案

```bash
# 掃描特定檔案是否有命令注入問題
python -m src.cwe_detector --single-file ./src/utils.py --cwe 078
```

### 範例 3: 整合 CodeQL 結果

```bash
# 如果你已經有 CodeQL 的掃描結果
python -m src.cwe_integration_manager ./projects/awesome-python \
    --codeql-json ../CodeQL-query_derive/python_query_output/awesome-python/awesome-python.json
```

### 範例 4: 批次掃描

```bash
# 一次掃描多個專案
python -m src.cwe_integration_manager ./projects --batch

# 查看批次掃描總結
cat ./prompts/batch_scan_summary.json
```

## 🔧 配置選項

在 `config/config.py` 中：

```python
# 啟用/停用 CWE 掃描
CWE_SCAN_ENABLED = True  # 改為 True 啟用

# 提示詞模式
CWE_PROMPT_MODE = "detailed"  # "detailed", "simple", "focused"

# 是否整合 CodeQL 結果
CWE_INTEGRATE_CODEQL_JSON = True

# 是否使用生成的提示詞（會覆蓋原有提示詞）
CWE_USE_GENERATED_PROMPT = True

# 要掃描的 CWE 列表（空列表 = 全部掃描）
CWE_SCAN_CWES = []  # 或指定如 ["078", "943", "502"]
```

## 📊 輸出結構

```
cwe_scan_results/
├── project_name/
│   └── bandit/
│       ├── CWE-078/
│       │   └── report.json      # Bandit 掃描結果
│       ├── CWE-095/
│       │   └── report.json
│       └── ...
└── project_name_cwe_report.json # 整合報告

prompts/cwe_generated/
└── project_name_prompt.txt      # 生成的修復提示詞
```

## 🎨 UI 使用

運行 `python main.py` 後會顯示設定對話框：

1. ✅ 勾選「啟用 CWE 漏洞掃描」
2. 🎯 選擇要掃描的 CWE 類型（或點「全選」）
3. ⚙️ 選擇提示詞模式（建議使用 "detailed"）
4. 🔗 選擇是否整合既有的 CodeQL 結果
5. 💾 點擊「確定」開始掃描

## 🚀 工作流程

```
1. 啟動 main.py
   ↓
2. 在 UI 中選擇要掃描的 CWE
   ↓
3. Bandit 自動掃描專案
   ↓
4. 生成詳細的修復提示詞
   ↓
5. Copilot 根據提示詞修復漏洞
   ↓
6. 保存修復結果到 ExecutionResult/Success/
```

## 🐛 疑難排解

### Bandit 未安裝

```bash
# 檢查安裝
pip list | grep bandit

# 安裝
pip install bandit

# 測試
bandit --version
```

### 沒有發現漏洞

這是好事！表示專案相對安全。你可以：
1. 檢查是否選擇了正確的 CWE 類型
2. 確認專案目錄路徑正確
3. 查看日誌檔案 `logs/` 了解詳情

### UI 無法顯示

```bash
# 確保安裝了 tkinter
sudo apt-get install python3-tk

# 測試
python3 -c "import tkinter; print('OK')"
```

## 💪 優勢

相比使用多個掃描器：

1. **簡單** - 只需安裝一個工具
2. **快速** - 掃描速度更快
3. **穩定** - 更少的依賴問題
4. **夠用** - Bandit 已涵蓋大部分 Python 安全問題
5. **輕量** - 程式碼更簡潔，維護更容易

## 📚 進階用法

### 自訂 Bandit 配置

創建 `.bandit` 配置檔案：

```yaml
# .bandit
tests: [B201, B301, B302, B303]
exclude_dirs: ['/test/', '/venv/']
```

### 查看詳細的 Bandit 報告

```bash
# 直接使用 Bandit
bandit -r ./projects/example_project -f json -o report.json

# 查看 HTML 格式報告
bandit -r ./projects/example_project -f html -o report.html
```

### 整合到 Git Pre-commit Hook

創建 `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# 在提交前掃描變更的 Python 檔案
git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | while read file; do
    python -m src.cwe_detector --single-file "$file" --cwe 078
done
```

## 🎯 最佳實踐

1. **定期掃描** - 每次提交前掃描變更的檔案
2. **優先修復** - 先修復「嚴重」和「高」風險漏洞
3. **保留記錄** - 保存掃描報告追蹤改進
4. **團隊共享** - 將 CWE 設定加入版本控制
5. **持續學習** - 了解每種 CWE 的原理和修復方法

## 📖 相關文檔

- **Bandit 官方文檔**: https://bandit.readthedocs.io/
- **CWE 官方網站**: https://cwe.mitre.org/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/

## ✅ 檢查清單

使用前確認：
- [ ] 已安裝 Bandit (`pip install bandit`)
- [ ] 測試通過 (`python tests/test_cwe_integration.py`)
- [ ] 配置已更新 (`CWE_SCAN_ENABLED = True`)
- [ ] 了解支援的 CWE 類型
- [ ] 知道如何查看掃描結果

---

**簡化版本**: v1.1  
**最後更新**: 2025-10-14  
**只需要**: Bandit 🎯
