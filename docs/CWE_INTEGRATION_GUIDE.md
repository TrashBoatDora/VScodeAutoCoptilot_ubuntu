# CWE 漏洞檢測整合指南

## 概述

本專案已整合 CodeQL-query_derive 的 CWE 漏洞檢測功能，可以自動掃描 Python 專案中的安全漏洞，並生成針對性的 Copilot 提示詞。

## 功能特點

### 1. 多重掃描器支援
- **Bandit**: Python 安全問題靜態分析工具
- **Semgrep**: 多語言程式碼掃描工具
- **CodeQL**: 進階程式碼查詢引擎（需預先建立 database）

### 2. 支援的 CWE 類型

| CWE ID | 名稱 | 描述 |
|--------|------|------|
| CWE-022 | Path Traversal | 路徑穿越 |
| CWE-078 | OS Command Injection | 作業系統命令注入 |
| CWE-079 | Cross-site Scripting (XSS) | 跨站腳本攻擊 |
| CWE-095 | Code Injection | 程式碼注入 |
| CWE-113 | HTTP Response Splitting | HTTP 回應分割 |
| CWE-117 | Log Injection | 日誌注入 |
| CWE-326 | Inadequate Encryption | 加密強度不足 |
| CWE-327 | Broken Cryptography | 使用已破解的加密演算法 |
| CWE-329 | CBC without Random IV | CBC 模式未使用隨機 IV |
| CWE-347 | JWT Signature Bypass | JWT 簽章驗證繞過 |
| CWE-377 | Insecure Temporary File | 不安全的臨時檔案 |
| CWE-502 | Deserialization | 不受信任資料的反序列化 |
| CWE-643 | XPath Injection | XPath 注入 |
| CWE-760 | Predictable Salt | 使用可預測的鹽值 |
| CWE-918 | SSRF | 伺服器端請求偽造 |
| CWE-943 | SQL Injection | SQL 注入 |
| CWE-1333 | Inefficient Regex | 低效率正則表達式 |

### 3. 自動提示詞生成
- **詳細模式 (detailed)**: 包含完整的漏洞位置、函數名稱和修復建議
- **簡化模式 (simple)**: 只列出要掃描的 CWE 類型
- **專注模式 (focused)**: 針對單一 CWE 類型的深入分析

## 安裝依賴

### 1. 安裝 Bandit
```bash
# 在專案的 venv 中安裝
source .venv/bin/activate
pip install bandit
```

### 2. 安裝 Semgrep
```bash
# 在專案的 venv 中安裝
pip install semgrep
```

### 3. 安裝 CodeQL（可選）
```bash
# 下載 CodeQL
wget https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.16.1/codeql-bundle-linux64.tar.gz

# 解壓縮
tar -xvzf codeql-bundle-linux64.tar.gz

# 添加到 PATH
export PATH=$PATH:/path/to/codeql

# 下載查詢 library
codeql pack download codeql/python-queries
```

## 使用方式

### 方式一：在主程式中啟用（推薦）

1. **啟動時自動顯示設定介面**

執行主程式時，會自動彈出 CWE 掃描設定對話框：

```bash
python main.py
```

在對話框中可以：
- 啟用/停用 CWE 掃描
- 選擇要掃描的 CWE 類型
- 設定提示詞模式
- 選擇是否整合既有的 CodeQL 結果

2. **在配置檔中啟用**

編輯 `config/config.py`：

```python
# CWE 漏洞掃描設定
CWE_SCAN_ENABLED = True  # 啟用 CWE 掃描
CWE_PROMPT_MODE = "detailed"  # 提示詞模式
CWE_INTEGRATE_CODEQL_JSON = True  # 整合 CodeQL 結果
CWE_USE_GENERATED_PROMPT = True  # 使用生成的提示詞
```

### 方式二：獨立使用掃描工具

#### 掃描單一專案
```bash
# 掃描專案並生成提示詞
python -m src.cwe_detector /path/to/project

# 掃描特定 CWE
python -m src.cwe_detector /path/to/project --cwes 078 095 502

# 指定輸出目錄
python -m src.cwe_detector /path/to/project --output ./results
```

#### 掃描單一檔案
```bash
python -m src.cwe_detector --single-file /path/to/file.py --cwe 078
```

#### 使用整合管理器
```bash
# 掃描並生成提示詞
python -m src.cwe_integration_manager /path/to/project

# 整合既有的 CodeQL 結果
python -m src.cwe_integration_manager /path/to/project \
    --codeql-json /path/to/codeql_output.json

# 批次掃描多個專案
python -m src.cwe_integration_manager /path/to/projects_dir --batch
```

### 方式三：整合既有的 CodeQL 結果

如果你已經使用 CodeQL-query_derive 掃描過專案：

```bash
# 1. 確保 CodeQL JSON 結果存在
ls ../CodeQL-query_derive/python_query_output/project_name/project_name.json

# 2. 在配置中啟用整合
CWE_INTEGRATE_CODEQL_JSON = True
CWE_CODEQL_JSON_DIR = PROJECT_ROOT.parent / "CodeQL-query_derive" / "python_query_output"

# 3. 執行主程式，會自動載入 CodeQL 結果
python main.py
```

## 工作流程

### 自動化流程（主程式整合）

```
1. 啟動 main.py
   ↓
2. 顯示 CWE 設定對話框（如果啟用）
   ↓
3. 對每個專案：
   a. 檢查是否有既有的 CodeQL JSON
   b. 執行 Bandit/Semgrep 掃描（如果需要）
   c. 整合所有掃描結果
   d. 生成針對性的提示詞
   e. 使用生成的提示詞與 Copilot 互動
   ↓
4. Copilot 根據提示詞修復漏洞
   ↓
5. 儲存修復結果
```

### 手動流程

```
1. 使用 CWE 檢測器掃描專案
   python -m src.cwe_detector /path/to/project
   
2. 生成掃描報告和提示詞
   ./cwe_scan_results/project_name_cwe_report.json
   ./prompts/cwe_generated/project_name_prompt.txt
   
3. 手動或自動將提示詞提供給 Copilot

4. Copilot 修復漏洞

5. 可選：重新掃描驗證修復結果
```

## 輸出結構

```
VSCode_CopilotAutoInteraction/
├── cwe_scan_results/              # 掃描結果目錄
│   ├── project_name/
│   │   ├── bandit/
│   │   │   └── CWE-078/
│   │   │       └── report.json
│   │   └── semgrep/
│   │       └── CWE-078/
│   │           └── rule_name.json
│   └── project_name_cwe_report.json  # 整合報告
├── prompts/
│   └── cwe_generated/             # 生成的提示詞
│       └── project_name_prompt.txt
└── ExecutionResult/
    └── Success/
        └── project_name/          # Copilot 修復結果
```

## 配置說明

在 `config/config.py` 中的 CWE 相關配置：

```python
# 是否啟用 CWE 掃描功能
CWE_SCAN_ENABLED = False

# CWE 掃描結果目錄
CWE_SCAN_OUTPUT_DIR = PROJECT_ROOT / "cwe_scan_results"

# CWE 生成的提示詞目錄
CWE_PROMPT_OUTPUT_DIR = PROMPTS_DIR / "cwe_generated"

# 提示詞模式: "detailed", "simple", "focused"
CWE_PROMPT_MODE = "detailed"

# 要掃描的 CWE 列表，空列表表示全部
CWE_SCAN_CWES = []

# 是否整合既有的 CodeQL JSON 結果
CWE_INTEGRATE_CODEQL_JSON = True

# CodeQL JSON 目錄
CWE_CODEQL_JSON_DIR = PROJECT_ROOT.parent / "CodeQL-query_derive" / "python_query_output"

# 是否使用 CWE 生成的提示詞
CWE_USE_GENERATED_PROMPT = True
```

## 範例

### 範例 1: 掃描專案並查看結果

```bash
# 掃描專案
python -m src.cwe_detector ./projects/example_project

# 查看掃描報告
cat ./cwe_scan_results/example_project_cwe_report.json

# 查看生成的提示詞
cat ./prompts/cwe_generated/example_project_prompt.txt
```

### 範例 2: 整合 CodeQL 結果

```bash
# 假設你已經用 CodeQL-query_derive 掃描過專案
# 專案名稱: awesome-python

# 使用整合管理器
python -m src.cwe_integration_manager ./projects/awesome-python \
    --codeql-json ../CodeQL-query_derive/python_query_output/awesome-python/awesome-python.json

# 查看生成的提示詞
cat ./prompts/cwe_generated/awesome-python_prompt.txt
```

### 範例 3: 批次掃描

```bash
# 批次掃描 projects 目錄下的所有專案
python -m src.cwe_integration_manager ./projects --batch

# 查看批次掃描總結
cat ./prompts/batch_scan_summary.json
```

## 疑難排解

### 1. 掃描器不可用

**問題**: 顯示「可用的掃描器: 」為空

**解決方法**:
```bash
# 確認 Bandit 安裝
which bandit
bandit --version

# 確認 Semgrep 安裝
which semgrep
semgrep --version

# 如果沒安裝，請安裝
pip install bandit semgrep
```

### 2. CodeQL 結果整合失敗

**問題**: 找不到 CodeQL JSON 檔案

**解決方法**:
```bash
# 檢查 CodeQL JSON 檔案位置
ls -la ../CodeQL-query_derive/python_query_output/*/

# 確認配置中的路徑正確
# 編輯 config/config.py 中的 CWE_CODEQL_JSON_DIR
```

### 3. 掃描超時

**問題**: 大型專案掃描超時

**解決方法**:
- 調整超時設定（在 `cwe_detector.py` 中的 `timeout` 參數）
- 分批掃描不同的 CWE 類型
- 只掃描特定目錄

## 進階用法

### 自訂 CWE 規則

如果需要添加新的 CWE 類型支援：

1. 在 `cwe_detector.py` 中添加 Bandit/Semgrep 規則映射
2. 在 `cwe_prompt_generator.py` 中添加 CWE 描述資訊
3. 在 `cwe_settings_ui.py` 中添加 UI 選項

### 整合到 CI/CD

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install bandit semgrep
      
      - name: Run CWE scan
        run: |
          python -m src.cwe_detector . --output ./scan-results
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: security-scan-results
          path: scan-results/
```

## 參考資料

- [Bandit 文檔](https://bandit.readthedocs.io/)
- [Semgrep 文檔](https://semgrep.dev/docs/)
- [CodeQL 文檔](https://codeql.github.com/docs/)
- [CWE 官方網站](https://cwe.mitre.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## 貢獻

如果你想要添加新功能或修復問題：

1. Fork 本專案
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 授權

本專案採用與原專案相同的授權協議。
