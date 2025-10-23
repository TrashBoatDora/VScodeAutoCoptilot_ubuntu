# Semgrep 快速入門指南

## 5 分鐘開始使用 Semgrep

### 第一步：安裝

```bash
# 進入專案目錄
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction

# 安裝 Semgrep
pip install semgrep

# 驗證安裝
semgrep --version
```

### 第二步：執行測試

```bash
# 執行整合測試
python test_semgrep_integration.py
```

預期輸出：
```
✅ Semgrep 掃描器可用
📋 CWE-078: 發現 4 個漏洞
📋 CWE-502: 發現 1 個漏洞
✅✅✅ 所有測試通過！
```

### 第三步：掃描您的專案

```bash
# 方法 1: 使用主程式
python main.py

# 方法 2: 直接使用 Semgrep
semgrep scan --config r/python.lang.security ./your_project/
```

### 第四步：查看結果

掃描結果會儲存在：
```
cwe_scan_results/
├── your_project/
│   ├── bandit/
│   │   └── CWE-078/
│   │       └── report.json
│   └── semgrep/
│       └── CWE-078/
│           └── report.json
```

## 常用命令

### 掃描特定 CWE

```python
from src.cwe_detector import CWEDetector, ScannerType
from pathlib import Path

detector = CWEDetector()

# 只掃描 CWE-078 (命令注入)
results = detector.scan_project(
    Path("./project"),
    cwes=["078"],
    scanners=[ScannerType.SEMGREP]
)
```

### 比較兩個掃描器

```python
# 使用 Bandit
bandit_results = detector.scan_project(
    Path("./project"),
    cwes=["078"],
    scanners=[ScannerType.BANDIT]
)

# 使用 Semgrep
semgrep_results = detector.scan_project(
    Path("./project"),
    cwes=["078"],
    scanners=[ScannerType.SEMGREP]
)

# 同時使用
both_results = detector.scan_project(
    Path("./project"),
    cwes=["078"],
    scanners=None  # 使用所有
)
```

## 實用技巧

### 1. 掃描單一檔案

```bash
semgrep scan --config r/python.lang.security.audit.dangerous-system-call your_file.py
```

### 2. 使用特定規則集

```bash
# OWASP Top 10
semgrep scan --config p/owasp-top-ten ./

# 僅高嚴重性
semgrep scan --config r/python.lang.security --severity ERROR ./
```

### 3. 輸出為不同格式

```bash
# JSON 格式
semgrep scan --config r/python.lang.security --json -o results.json ./

# SARIF 格式（適合 CI/CD）
semgrep scan --config r/python.lang.security --sarif -o results.sarif ./

# 終端輸出
semgrep scan --config r/python.lang.security ./
```

## 支援的 CWE

✅ 完全支援的 CWE：

| CWE | 名稱 | Bandit | Semgrep |
|-----|------|--------|---------|
| 022 | Path Traversal | ✅ | ✅ |
| 078 | Command Injection | ✅ | ✅ |
| 095 | Code Injection | ✅ | ✅ |
| 502 | Deserialization | ✅ | ✅ |
| 943 | SQL Injection | ✅ | ✅ |

查看完整列表：
```bash
python -c "from src.cwe_detector import CWEDetector; print('\n'.join(CWEDetector.SUPPORTED_CWES))"
```

## 故障排除

### Q: Semgrep 執行很慢？

A: 使用 `--config auto` 或指定特定規則而非整個規則集：
```bash
# 慢（掃描所有規則）
semgrep scan --config r/python.lang.security ./

# 快（只掃描命令注入）
semgrep scan --config r/python.lang.security.audit.dangerous-system-call ./
```

### Q: 如何忽略誤報？

A: 在程式碼中添加註釋：
```python
# nosemgrep: python.lang.security.audit.dangerous-system-call
os.system(safe_command)
```

### Q: 如何更新規則？

A: Semgrep 會自動從 Registry 下載最新規則，也可以手動更新：
```bash
semgrep --update-rules
```

## 下一步

1. 📖 閱讀完整文件：`docs/SEMGREP_INTEGRATION.md`
2. 🔧 自訂規則配置
3. 🚀 整合到 CI/CD 流程
4. 📊 查看更多掃描報告範例

## 取得協助

- Semgrep 文件: https://semgrep.dev/docs/
- 規則瀏覽器: https://semgrep.dev/r
- 社群: https://go.semgrep.dev/slack
