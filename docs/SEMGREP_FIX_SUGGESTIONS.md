# Semgrep 規則修復建議
生成時間: /home/ai/AISecurityProject/VSCode_CopilotAutoInteraction

## 需要修復的規則

### CWE-079

**當前規則**:
```python
"079": "r/python.flask.security.xss"
```

**建議規則**:
```python
"079": "r/python.lang.security.audit.xss.string-html-format"
```

**修改原因**: 規則更新或修正

### CWE-095

**當前規則**:
```python
"095": "r/python.lang.security.audit.eval-detected"
```

**建議規則**:
```python
"095": "r/python.lang.security.audit.dangerous-code-exec,r/python.lang.security.audit.eval-detected"
```

**修改原因**: 規則更新或修正

### CWE-327

**當前規則**:
```python
"327": "r/python.lang.security.audit.md5-used"
```

**建議規則**:
```python
"327": "r/python.lang.security.audit.md5-used,r/python.lang.security.audit.hashlib-insecure-functions"
```

**修改原因**: 規則更新或修正

### CWE-347

**當前規則**:
```python
"347": "r/python.jwt.security.jwt-none-alg"
```

**建議規則**:
```python
"347": "r/python.jwt.security.jwt-hardcoded-secret,r/python.jwt.security.jwt-decode-verify-false"
```

**修改原因**: 規則更新或修正

### CWE-502

**當前規則**:
```python
"502": "r/python.lang.security.deserialization.avoid-pyyaml-load"
```

**建議規則**:
```python
"502": "r/python.lang.security.deserialization.avoid-pyyaml-load,r/python.lang.security.audit.avoid-pickle"
```

**修改原因**: 規則更新或修正

