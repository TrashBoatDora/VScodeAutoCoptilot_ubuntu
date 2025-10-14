# CWE 整合功能快速入門

## 5 分鐘快速開始

### 步驟 1: 安裝依賴

```bash
# 進入專案目錄
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction

# 建立並啟動虛擬環境（如果還沒有）
python3 -m venv .venv
source .venv/bin/activate

# 安裝必要的安全掃描工具
pip install bandit semgrep

# 安裝原有依賴
pip install -r requirements.txt
```

### 步驟 2: 運行測試

```bash
# 測試 CWE 整合功能是否正常
python tests/test_cwe_integration.py
```

預期輸出：
```
=== 測試 CWE 檢測器 ===
可用掃描器: bandit, semgrep
✅ CWE 檢測器初始化成功

=== 測試提示詞生成器 ===
✅ 提示詞生成成功（長度: XXX 字元）

...

🎉 所有測試通過！CWE 整合功能已就緒
```

### 步驟 3: 測試單一專案掃描

```bash
# 掃描一個測試專案
python -m src.cwe_detector ./projects/example_project --cwes 078 095 502
```

### 步驟 4: 在主程式中使用

編輯 `config/config.py`，啟用 CWE 掃描：

```python
# CWE 漏洞掃描設定
CWE_SCAN_ENABLED = True  # 改為 True
```

然後執行主程式：

```bash
python main.py
```

程式會自動：
1. 顯示 CWE 設定對話框
2. 掃描專案中的漏洞
3. 生成針對性的提示詞
4. 使用 Copilot 修復漏洞

## 常見使用場景

### 場景 1: 掃描新專案

```bash
# 1. 掃描專案
python -m src.cwe_integration_manager ./projects/new_project

# 2. 查看掃描報告
cat ./cwe_scan_results/new_project_cwe_report.json

# 3. 查看生成的提示詞
cat ./prompts/cwe_generated/new_project_prompt.txt
```

### 場景 2: 整合既有的 CodeQL 結果

如果你已經用 `CodeQL-query_derive` 掃描過專案：

```bash
# 假設 CodeQL 結果在這裡：
# ../CodeQL-query_derive/python_query_output/awesome-python/awesome-python.json

# 整合 CodeQL 結果並生成提示詞
python -m src.cwe_integration_manager ./projects/awesome-python \
    --codeql-json ../CodeQL-query_derive/python_query_output/awesome-python/awesome-python.json
```

### 場景 3: 批次掃描多個專案

```bash
# 掃描 projects 目錄下的所有專案
python -m src.cwe_integration_manager ./projects --batch

# 查看批次掃描總結
cat ./prompts/batch_scan_summary.json
```

### 場景 4: 只掃描特定 CWE 類型

```bash
# 只掃描命令注入和 SQL 注入
python -m src.cwe_detector ./projects/example_project --cwes 078 943
```

## 設定選項說明

在 `config/config.py` 中可以調整的選項：

```python
# 是否啟用 CWE 掃描
CWE_SCAN_ENABLED = False  # 改為 True 以啟用

# 提示詞模式
CWE_PROMPT_MODE = "detailed"  # "detailed", "simple", "focused"

# 是否整合 CodeQL 結果
CWE_INTEGRATE_CODEQL_JSON = True

# 是否使用 CWE 生成的提示詞（會覆蓋原有提示詞）
CWE_USE_GENERATED_PROMPT = True

# 要掃描的 CWE 列表（空列表 = 全部掃描）
CWE_SCAN_CWES = []  # 或指定如 ["078", "095", "502"]
```

## UI 介面使用

執行主程式時，會自動顯示 CWE 設定對話框：

![CWE Settings UI](../assets/cwe_settings_ui_screenshot.png)

你可以：
1. ✅ 勾選「啟用 CWE 漏洞掃描」
2. 🎯 選擇要掃描的 CWE 類型（或點「全選」）
3. ⚙️ 選擇提示詞模式
4. 🔗 選擇是否整合既有的 CodeQL 結果
5. 💾 點擊「確定」保存設定

## 查看結果

### 掃描報告格式

`cwe_scan_results/project_name_cwe_report.json`:

```json
{
  "project": "example_project",
  "total_vulnerabilities": 5,
  "vulnerabilities_by_cwe": {
    "CWE-078": [
      {
        "file": "src/utils.py",
        "line_start": 42,
        "line_end": 42,
        "function": "execute_command",
        "scanner": "bandit",
        "severity": "HIGH",
        "description": "Use of shell=True identified"
      }
    ]
  }
}
```

### 提示詞格式

`prompts/cwe_generated/project_name_prompt.txt`:

```markdown
# 專案: example_project - 安全漏洞修復請求

## 任務說明
請協助修復本專案中檢測到的安全漏洞...

## CWE-078: OS Command Injection

**漏洞描述**: 不安全的命令執行可能允許攻擊者執行任意系統命令

**修復建議**: 避免使用 shell=True，使用參數列表而非字串

**發現 2 個此類型的漏洞**:

### 檔案: `src/utils.py`

1. **位置**: 第 42 行
   - **函數**: `execute_command`
   - **詳情**: Use of shell=True identified
   ...
```

## 疑難排解

### 問題 1: 沒有可用的掃描器

```bash
# 檢查安裝
pip list | grep -E "bandit|semgrep"

# 如果沒安裝，請安裝
pip install bandit semgrep
```

### 問題 2: CodeQL JSON 找不到

```bash
# 檢查 CodeQL 結果目錄
ls -la ../CodeQL-query_derive/python_query_output/

# 確認配置中的路徑
grep CWE_CODEQL_JSON_DIR config/config.py
```

### 問題 3: UI 無法顯示

確保已安裝 tkinter：

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# 測試 tkinter
python3 -c "import tkinter; print('OK')"
```

## 下一步

- 📖 閱讀完整文檔: [CWE_INTEGRATION_GUIDE.md](CWE_INTEGRATION_GUIDE.md)
- 🔧 自訂 CWE 規則和提示詞模板
- 🚀 整合到 CI/CD 流程
- 📊 分析批次掃描結果，優先修復高風險漏洞

## 需要幫助？

如有問題，請：
1. 查看 [完整文檔](CWE_INTEGRATION_GUIDE.md)
2. 運行測試腳本診斷問題
3. 查看日誌檔案 `logs/`
