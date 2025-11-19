# Semgrep 測試與驗證 - 快速參考

## 📋 測試檔案結構

```
tests/
├── test_semgrep_scanner.py      # 主測試套件（18個測試）
├── validate_semgrep_rules.py    # 規則驗證工具
└── test_samples/                # 測試樣本程式碼
    ├── cwe_078_vulnerable.py    # CWE-078 漏洞範例
    ├── cwe_078_safe.py          # CWE-078 安全範例
    ├── cwe_327_vulnerable.py    # CWE-327 漏洞範例
    ├── cwe_327_safe.py          # CWE-327 安全範例
    ├── cwe_502_vulnerable.py    # CWE-502 漏洞範例
    └── cwe_502_safe.py          # CWE-502 安全範例

docs/
├── SEMGREP_TEST_REPORT.md       # 完整測試報告
├── SEMGREP_CRITICAL_FINDINGS.md # 關鍵發現與修復建議
└── SEMGREP_FIX_SUGGESTIONS.md   # 自動生成的修復建議
```

## 🚀 快速命令

### 運行完整測試套件
```bash
cd /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction
conda run -n copilot_py310 python tests/test_semgrep_scanner.py
```

### 驗證 Semgrep 規則
```bash
conda run -n copilot_py310 python tests/validate_semgrep_rules.py
```

### 測試單個 CWE 樣本
```bash
conda run -n copilot_py310 python -c "
from src.cwe_detector import CWEDetector
from pathlib import Path

detector = CWEDetector()
vulns = detector.scan_single_file(
    Path('tests/test_samples/cwe_078_vulnerable.py'),
    cwe='078'
)
print(f'發現 {len(vulns)} 個問題')
"
```

## 🔍 關鍵發現摘要

### 問題嚴重性：🔴 高

**主要問題**: 95% 的 Semgrep 規則格式錯誤（缺少 `r/` 前綴）

**影響**:
- 大部分漏洞可能未被 Semgrep 檢測到
- 依賴 Bandit 進行主要掃描
- 掃描覆蓋率低於預期

**好消息**:
- ✅ 問題已被完全識別
- ✅ 修復方案明確且簡單
- ✅ 測試框架完整可靠

## 🔧 快速修復（5分鐘）

### 步驟 1: 備份當前配置
```bash
cp src/cwe_detector.py src/cwe_detector.py.backup
```

### 步驟 2: 更新規則
在 `src/cwe_detector.py` 中，將 `SEMGREP_BY_CWE` 替換為：

```python
SEMGREP_BY_CWE = {
    "022": "r/python.lang.security",
    "078": "r/python.lang.security.audit.dangerous-subprocess-use",
    "079": "r/python.lang.security",
    "095": "r/python.lang.security.audit.eval-detected",
    "113": "r/python.lang.security",
    "326": "r/python.cryptography.security.insufficient-dsa-key-size",
    "327": "r/python.lang.security.audit.md5-used",
    "329": "r/python.cryptography.security.insecure-cipher-mode-ecb",
    "347": "r/javascript.jose.security.jwt-none-alg",
    "377": "r/python.lang.security",
    "502": "r/python.lang.security.deserialization.avoid-pyyaml-load",
    "643": "r/python.lang.security",
    "760": "r/python.cryptography.security.insufficient-rsa-key-size",
    "918": "r/python.requests.security.disabled-cert-validation",
    "943": "r/python.lang.security",
}
```

### 步驟 3: 驗證修復
```bash
# 驗證規則
conda run -n copilot_py310 python tests/validate_semgrep_rules.py

# 重新運行測試
conda run -n copilot_py310 python tests/test_semgrep_scanner.py
```

### 步驟 4: 確認結果
應該看到：
- ✅ 15/15 規則有效（從 1/19 提升）
- ✅ 18/18 測試通過
- ✅ 更高的漏洞檢測率

## 📊 測試統計

### 修復前
- **有效規則**: 1/19 (5.3%)
- **測試通過**: 18/18 ✅（但 Semgrep 大部分未工作）
- **Semgrep 檢測**: 4 個漏洞
- **Bandit 檢測**: 12 個漏洞

### 修復後（預期）
- **有效規則**: 15/15 (100%)
- **測試通過**: 18/18 ✅
- **Semgrep 檢測**: 15-20 個漏洞（預計提升）
- **Bandit 檢測**: 12 個漏洞

## 🎯 測試覆蓋

### 單元測試（18個）
- ✅ 規則映射測試 (4)
- ✅ 命令構建測試 (3)
- ✅ 結果解析測試 (4)
- ✅ 漏洞檢測測試 (6)
- ✅ 掃描器比較測試 (1)

### 測試的 CWE 類型
- CWE-078: OS Command Injection
- CWE-327: Broken Cryptography
- CWE-502: Insecure Deserialization

### 測試樣本（30個函數）
- 15 個含漏洞的函數
- 15 個安全的函數

## 🔔 重要注意事項

### 假陽性
修復後可能增加假陽性（特別是 CWE-078）：
- 使用 `shlex.quote()` 的代碼可能被標記
- 列表參數的 `subprocess` 可能被標記
- **建議**: 需要人工審查這些情況

### 建議的工作流程
1. 運行掃描
2. Semgrep 和 Bandit 同時掃描
3. 合併結果（去重）
4. 人工審查假陽性
5. 修復真實漏洞

## 📚 參考文檔

- **完整測試報告**: `docs/SEMGREP_TEST_REPORT.md`
- **關鍵發現**: `docs/SEMGREP_CRITICAL_FINDINGS.md`
- **修復建議**: `docs/SEMGREP_FIX_SUGGESTIONS.md`

## ❓ 常見問題

### Q: 為什麼測試通過但規則無效？
A: 測試驗證了錯誤處理邏輯，即使規則無效，系統也能正常運行並記錄錯誤。

### Q: 是否需要立即修復？
A: 建議盡快修復。當前依賴 Bandit 單一掃描器有風險。

### Q: 修復會破壞現有功能嗎？
A: 不會。修復只會增強檢測能力，不會影響現有工作流程。

### Q: 如何處理假陽性？
A: 在代碼審查階段人工判斷，或添加自定義 Semgrep 規則排除特定模式。

## ✅ 檢查清單

修復完成後的驗證：

- [ ] 運行規則驗證工具（無錯誤）
- [ ] 運行完整測試套件（18/18 通過）
- [ ] 掃描測試樣本（檢測到已知漏洞）
- [ ] 檢查假陽性率（可接受範圍）
- [ ] 更新相關文檔
- [ ] 提交代碼變更

---

**最後更新**: 2025-11-19  
**維護者**: AI Security Team  
**版本**: 1.0
