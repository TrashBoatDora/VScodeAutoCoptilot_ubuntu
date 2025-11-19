#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semgrep 規則修復與驗證腳本

此腳本用於：
1. 驗證當前 Semgrep 規則的有效性
2. 提供修復建議
3. 自動測試修復後的規則
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.logger import get_logger

logger = get_logger("SemgrepFix")


# 建議的規則修復
SUGGESTED_RULES = {
    "022": "r/python.lang.security.audit.path-traversal-open",
    "078": "r/python.lang.security.audit.dangerous-subprocess-use",
    "079": "r/python.lang.security.audit.xss.string-html-format",
    "095": "r/python.lang.security.audit.dangerous-code-exec,r/python.lang.security.audit.eval-detected",
    "113": "r/python.django.security.injection.header-injection",
    "326": "r/python.cryptography.security.insufficient-dsa-key-size",
    "327": "r/python.lang.security.audit.md5-used,r/python.lang.security.audit.hashlib-insecure-functions",
    "329": "r/python.cryptography.security.insecure-cipher-mode-ecb",
    "347": "r/python.jwt.security.jwt-hardcoded-secret,r/python.jwt.security.jwt-decode-verify-false",
    "377": "r/python.lang.security.audit.insecure-temp-file",
    "502": "r/python.lang.security.deserialization.avoid-pyyaml-load,r/python.lang.security.audit.avoid-pickle",
    "643": "r/python.lxml.security.xpath-injection",
    "760": "r/python.cryptography.security.insufficient-rsa-key-size",
    "918": "r/python.requests.security.disabled-cert-validation",
    "943": "r/python.django.security.injection.sql.sql-injection-db-cursor-execute",
}


def check_rule_validity(rule: str) -> Tuple[bool, str]:
    """
    檢查 Semgrep 規則是否有效
    
    Args:
        rule: Semgrep 規則 ID
        
    Returns:
        (是否有效, 錯誤訊息)
    """
    try:
        # 創建臨時測試檔案
        test_file = Path("/tmp/test_semgrep_rule.py")
        test_file.write_text("print('test')\n")
        
        # 嘗試使用規則掃描
        cmd = ["semgrep", "scan", "--config", rule, "--json", str(test_file)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            text=True
        )
        
        # 清理測試檔案
        test_file.unlink(missing_ok=True)
        
        # 檢查結果
        if result.returncode in [0, 1]:  # 0 = 無發現, 1 = 有發現
            return True, "規則有效"
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"規則無效: {error_msg[:100]}"
            
    except subprocess.TimeoutExpired:
        return False, "規則驗證超時"
    except Exception as e:
        return False, f"驗證失敗: {str(e)}"


def validate_all_rules(rules_dict: Dict[str, str]) -> Dict[str, List[Tuple[str, bool, str]]]:
    """
    驗證所有規則的有效性
    
    Args:
        rules_dict: CWE 到規則的映射
        
    Returns:
        驗證結果字典
    """
    results = {}
    
    for cwe, rules in rules_dict.items():
        logger.info(f"驗證 CWE-{cwe} 的規則...")
        
        # 分割規則（如果有多個）
        if isinstance(rules, str):
            rule_list = [r.strip() for r in rules.split(",")]
        else:
            rule_list = rules
        
        cwe_results = []
        for rule in rule_list:
            is_valid, message = check_rule_validity(rule)
            cwe_results.append((rule, is_valid, message))
            
            status = "✅" if is_valid else "❌"
            logger.info(f"  {status} {rule}: {message}")
        
        results[cwe] = cwe_results
    
    return results


def generate_fix_report(current_rules: Dict[str, str], 
                        suggested_rules: Dict[str, str]) -> str:
    """
    生成修復報告
    
    Args:
        current_rules: 當前規則
        suggested_rules: 建議規則
        
    Returns:
        修復報告內容
    """
    report = []
    report.append("# Semgrep 規則修復建議\n")
    report.append(f"生成時間: {Path.cwd()}\n\n")
    
    report.append("## 需要修復的規則\n\n")
    
    for cwe in sorted(current_rules.keys()):
        current = current_rules.get(cwe, "")
        suggested = suggested_rules.get(cwe, "")
        
        if current != suggested:
            report.append(f"### CWE-{cwe}\n\n")
            report.append(f"**當前規則**:\n```python\n\"{cwe}\": \"{current}\"\n```\n\n")
            report.append(f"**建議規則**:\n```python\n\"{cwe}\": \"{suggested}\"\n```\n\n")
            report.append("**修改原因**: 規則更新或修正\n\n")
    
    return "".join(report)


def main():
    """主函數"""
    logger.info("=" * 60)
    logger.info("Semgrep 規則驗證與修復工具")
    logger.info("=" * 60)
    
    # 導入當前規則
    from src.cwe_detector import CWEDetector
    detector = CWEDetector()
    current_rules = detector.SEMGREP_BY_CWE
    
    # 步驟 1: 驗證當前規則
    logger.info("\n步驟 1: 驗證當前規則的有效性")
    logger.info("-" * 60)
    
    current_results = validate_all_rules(current_rules)
    
    # 統計結果
    total_rules = sum(len(results) for results in current_results.values())
    valid_rules = sum(
        sum(1 for _, is_valid, _ in results if is_valid)
        for results in current_results.values()
    )
    invalid_rules = total_rules - valid_rules
    
    logger.info("\n" + "=" * 60)
    logger.info(f"驗證完成: {valid_rules}/{total_rules} 個規則有效")
    logger.info(f"需要修復: {invalid_rules} 個規則")
    logger.info("=" * 60)
    
    # 步驟 2: 列出需要修復的規則
    if invalid_rules > 0:
        logger.info("\n需要修復的規則:")
        for cwe, results in current_results.items():
            for rule, is_valid, message in results:
                if not is_valid:
                    logger.error(f"  CWE-{cwe}: {rule}")
                    logger.error(f"    原因: {message}")
    
    # 步驟 3: 驗證建議規則
    logger.info("\n步驟 2: 驗證建議規則的有效性")
    logger.info("-" * 60)
    
    suggested_results = validate_all_rules(SUGGESTED_RULES)
    
    suggested_valid = sum(
        sum(1 for _, is_valid, _ in results if is_valid)
        for results in suggested_results.values()
    )
    suggested_total = sum(len(results) for results in suggested_results.values())
    
    logger.info("\n" + "=" * 60)
    logger.info(f"建議規則驗證: {suggested_valid}/{suggested_total} 個規則有效")
    logger.info("=" * 60)
    
    # 步驟 4: 生成修復報告
    logger.info("\n步驟 3: 生成修復報告")
    logger.info("-" * 60)
    
    report = generate_fix_report(current_rules, SUGGESTED_RULES)
    report_file = project_root / "docs" / "SEMGREP_FIX_SUGGESTIONS.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"修復報告已保存: {report_file}")
    
    # 總結
    logger.info("\n" + "=" * 60)
    logger.info("總結")
    logger.info("=" * 60)
    logger.info(f"✅ 當前有效規則: {valid_rules}/{total_rules}")
    logger.info(f"❌ 需要修復規則: {invalid_rules}")
    logger.info(f"💡 建議規則有效: {suggested_valid}/{suggested_total}")
    
    if invalid_rules > 0:
        logger.info("\n建議操作:")
        logger.info("1. 查看修復報告: docs/SEMGREP_FIX_SUGGESTIONS.md")
        logger.info("2. 更新 src/cwe_detector.py 中的 SEMGREP_BY_CWE")
        logger.info("3. 重新運行測試: python tests/test_semgrep_scanner.py")
    else:
        logger.info("\n🎉 所有規則都有效！")
    
    return 0 if invalid_rules == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
