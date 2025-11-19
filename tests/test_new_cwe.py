#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Semgrep 對新 CWE 範例 (new_cwe.py) 的檢測能力
"""

from pathlib import Path
from src.cwe_detector import CWEDetector, ScannerType

def main():
    detector = CWEDetector()
    file_path = Path('tests/test_samples/new_cwe.py')
    
    # 測試所有支援的 CWE
    print('=' * 60)
    print('測試 Semgrep 對新 CWE 範例 (new_cwe.py) 的檢測能力')
    print('=' * 60)
    
    results = {}
    for cwe in detector.SUPPORTED_CWES:
        if cwe in detector.SEMGREP_BY_CWE:
            print(f'\n測試 CWE-{cwe}...')
            vulns = detector.scan_single_file(file_path, cwe)
            
            # 統計每個掃描器的結果
            semgrep_vulns = [v for v in vulns if v.scanner == ScannerType.SEMGREP]
            bandit_vulns = [v for v in vulns if v.scanner == ScannerType.BANDIT]
            
            # 只關注成功的掃描結果
            semgrep_success = [v for v in semgrep_vulns if v.scan_status == 'success' and v.line_start > 0]
            bandit_success = [v for v in bandit_vulns if v.scan_status == 'success' and v.line_start > 0]
            
            results[cwe] = {
                'semgrep': len(semgrep_success),
                'bandit': len(bandit_success),
                'total': len(vulns)
            }
            
            if semgrep_success:
                print(f'  ✅ Semgrep 檢測到 {len(semgrep_success)} 個漏洞')
                for v in semgrep_success[:3]:  # 只顯示前3個
                    desc = v.description[:60] if v.description else "No description"
                    print(f'     - 行 {v.line_start}: {desc}...')
            else:
                print(f'  ❌ Semgrep 未檢測到漏洞')
                
            if bandit_success:
                print(f'  ℹ️  Bandit 檢測到 {len(bandit_success)} 個漏洞')
    
    # 總結
    print('\n' + '=' * 60)
    print('檢測結果總結')
    print('=' * 60)
    
    semgrep_detected = sum(1 for r in results.values() if r['semgrep'] > 0)
    bandit_detected = sum(1 for r in results.values() if r['bandit'] > 0)
    total = len(results)
    
    print(f'Semgrep 成功檢測: {semgrep_detected}/{total} ({semgrep_detected*100//total}%)')
    print(f'Bandit 成功檢測: {bandit_detected}/{total} ({bandit_detected*100//total}%)')
    
    print(f'\n各 CWE 檢測詳情:')
    for cwe, result in sorted(results.items()):
        semgrep_status = '✅' if result['semgrep'] > 0 else '❌'
        bandit_status = '✅' if result['bandit'] > 0 else '❌'
        print(f'  CWE-{cwe}: Semgrep {semgrep_status} ({result["semgrep"]}), Bandit {bandit_status} ({result["bandit"]})')
    
    # 找出未檢測到的 CWE
    print(f'\n未檢測到的 CWE (兩個掃描器都失敗):')
    for cwe, result in sorted(results.items()):
        if result['semgrep'] == 0 and result['bandit'] == 0:
            print(f'  ⚠️  CWE-{cwe}: 需要檢查範例代碼或規則')

if __name__ == '__main__':
    main()
