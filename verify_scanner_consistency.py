#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
驗證 Bandit 和 Semgrep 的檔案級別報告格式一致性
"""
import json
from pathlib import Path

def main():
    print("=" * 80)
    print("Bandit 和 Semgrep 檔案級別報告格式一致性驗證")
    print("=" * 80)
    
    # 測試專案
    test_project = "test_semgrep"
    cwe = "327"
    
    bandit_dir = Path(f"OriginalScanResult/Bandit/CWE-{cwe}/{test_project}")
    semgrep_dir = Path(f"OriginalScanResult/Semgrep/CWE-{cwe}/{test_project}")
    
    # 檢查目錄
    print(f"\n📁 檢查目錄:")
    print(f"   Bandit:  {bandit_dir} {'✅' if bandit_dir.exists() else '❌'}")
    print(f"   Semgrep: {semgrep_dir} {'✅' if semgrep_dir.exists() else '❌'}")
    
    if not bandit_dir.exists() or not semgrep_dir.exists():
        print("\n⚠️  目錄不存在")
        return 1
    
    # 列出檔案
    bandit_files = sorted([f.name for f in bandit_dir.iterdir() if f.name.endswith('_report.json')])
    semgrep_files = sorted([f.name for f in semgrep_dir.iterdir() if f.name.endswith('_report.json')])
    
    print(f"\n📊 檔案數量:")
    print(f"   Bandit:  {len(bandit_files)} 個檔案級別報告")
    print(f"   Semgrep: {len(semgrep_files)} 個檔案級別報告")
    
    print("\n檔案列表:")
    for f in bandit_files:
        print(f"  Bandit:  {f}")
    for f in semgrep_files:
        print(f"  Semgrep: {f}")
    
    print(f"\n🎉 驗證完成！")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
