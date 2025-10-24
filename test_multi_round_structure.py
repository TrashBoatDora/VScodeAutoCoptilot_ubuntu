#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試多輪互動的目錄結構
驗證 CWE_Result 和 OriginalScanResult 是否正確建立輪數資料夾
"""

import sys
from pathlib import Path
import tempfile
import shutil

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))

from src.cwe_scan_manager import CWEScanManager

def test_multi_round_directory_structure():
    """測試多輪互動的目錄結構"""
    
    print("=" * 80)
    print("測試多輪互動的目錄結構")
    print("=" * 80)
    
    # 創建測試專案目錄
    test_project_dir = Path("projects/test_multi_round")
    test_project_dir.mkdir(parents=True, exist_ok=True)
    
    # 創建測試 Python 檔案
    test_file = test_project_dir / "crypto_test.py"
    test_file.write_text("""
import hashlib

def weak_function():
    # CWE-327: 使用弱加密 MD5
    return hashlib.md5(b"test").hexdigest()
""")
    
    print(f"\n✅ 測試專案已創建: {test_project_dir}")
    print(f"  - crypto_test.py")
    
    # 創建臨時輸出目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "CWE_Result"
        original_scan_dir = Path(temp_dir) / "OriginalScanResult"
        
        # 初始化掃描管理器
        cwe_scan_manager = CWEScanManager(output_dir)
        # 手動設置原始掃描目錄（模擬真實情況）
        cwe_scan_manager.detector.original_scan_dir = original_scan_dir
        cwe_scan_manager.detector.bandit_original_dir = original_scan_dir / "Bandit"
        cwe_scan_manager.detector.semgrep_original_dir = original_scan_dir / "Semgrep"
        cwe_scan_manager.detector.bandit_original_dir.mkdir(parents=True, exist_ok=True)
        cwe_scan_manager.detector.semgrep_original_dir.mkdir(parents=True, exist_ok=True)
        
        project_name = "test_multi_round"
        cwe_type = "327"
        
        # 模擬多輪互動掃描
        rounds = [1, 2, 3]
        
        for round_num in rounds:
            print(f"\n{'=' * 80}")
            print(f"模擬第 {round_num} 輪掃描")
            print(f"{'=' * 80}")
            
            # 創建 prompt 內容
            prompt_content = f"請幫我定位到crypto_test.py的weak_function()的函式"
            
            # 執行掃描
            success, result_files = cwe_scan_manager.scan_from_prompt_function_level(
                project_path=test_project_dir,
                project_name=project_name,
                prompt_content=prompt_content,
                cwe_type=cwe_type,
                round_number=round_num,
                line_number=1
            )
            
            if success:
                print(f"✅ 第 {round_num} 輪掃描完成")
            else:
                print(f"❌ 第 {round_num} 輪掃描失敗")
        
        # 驗證目錄結構
        print(f"\n{'=' * 80}")
        print("驗證目錄結構")
        print(f"{'=' * 80}")
        
        # 檢查 CWE_Result 結構
        print(f"\n📁 CWE_Result 目錄結構:")
        cwe_result_base = output_dir / f"CWE-{cwe_type}"
        
        for scanner in ["Bandit", "Semgrep"]:
            scanner_dir = cwe_result_base / scanner / project_name
            print(f"\n  {scanner}:")
            
            if scanner_dir.exists():
                round_dirs = sorted([d for d in scanner_dir.iterdir() if d.is_dir()])
                print(f"    專案目錄: {scanner_dir}")
                print(f"    輪數資料夾數量: {len(round_dirs)}")
                
                for round_dir in round_dirs:
                    csv_files = list(round_dir.glob("*.csv"))
                    print(f"      - {round_dir.name}/ ({len(csv_files)} 個 CSV)")
                    for csv_file in csv_files:
                        print(f"          • {csv_file.name}")
                
                # 驗證是否包含所有輪次
                expected_rounds = {f"第{i}輪" for i in rounds}
                actual_rounds = {d.name for d in round_dirs}
                
                if expected_rounds == actual_rounds:
                    print(f"    ✅ 所有輪次都存在: {sorted(actual_rounds)}")
                else:
                    missing = expected_rounds - actual_rounds
                    print(f"    ❌ 缺少輪次: {missing}")
            else:
                print(f"    ❌ 目錄不存在: {scanner_dir}")
        
        # 檢查 OriginalScanResult 結構
        print(f"\n📁 OriginalScanResult 目錄結構:")
        
        for scanner in ["Bandit", "Semgrep"]:
            scanner_dir = original_scan_dir / scanner / f"CWE-{cwe_type}" / project_name
            print(f"\n  {scanner}:")
            
            if scanner_dir.exists():
                round_dirs = sorted([d for d in scanner_dir.iterdir() if d.is_dir()])
                print(f"    專案目錄: {scanner_dir}")
                print(f"    輪數資料夾數量: {len(round_dirs)}")
                
                for round_dir in round_dirs:
                    json_files = list(round_dir.glob("*.json"))
                    print(f"      - {round_dir.name}/ ({len(json_files)} 個 JSON)")
                    for json_file in json_files:
                        print(f"          • {json_file.name}")
                
                # 驗證是否包含所有輪次
                expected_rounds = {f"第{i}輪" for i in rounds}
                actual_rounds = {d.name for d in round_dirs}
                
                if expected_rounds == actual_rounds:
                    print(f"    ✅ 所有輪次都存在: {sorted(actual_rounds)}")
                else:
                    missing = expected_rounds - actual_rounds
                    print(f"    ❌ 缺少輪次: {missing}")
            else:
                print(f"    ❌ 目錄不存在: {scanner_dir}")
        
        # 顯示完整的目錄樹
        print(f"\n{'=' * 80}")
        print("完整目錄樹")
        print(f"{'=' * 80}")
        
        import os
        
        print(f"\nCWE_Result/")
        for root, dirs, files in os.walk(output_dir):
            level = len(Path(root).relative_to(output_dir).parts)
            indent = "  " * level
            print(f"{indent}{Path(root).name}/")
            sub_indent = "  " * (level + 1)
            for file in sorted(files):
                print(f"{sub_indent}{file}")
        
        print(f"\nOriginalScanResult/")
        for root, dirs, files in os.walk(original_scan_dir):
            level = len(Path(root).relative_to(original_scan_dir).parts)
            indent = "  " * level
            print(f"{indent}{Path(root).name}/")
            sub_indent = "  " * (level + 1)
            for file in sorted(files):
                print(f"{sub_indent}{file}")
        
        print(f"\n{'=' * 80}")
        print("測試完成！")
        print(f"{'=' * 80}")
        
        # 詢問是否保留測試專案
        try:
            keep = input("\n是否保留測試專案？(y/n，預設 n): ").strip().lower()
            if keep != 'y':
                shutil.rmtree(test_project_dir)
                print(f"✅ 測試專案已刪除: {test_project_dir}")
            else:
                print(f"ℹ️  測試專案已保留: {test_project_dir}")
        except KeyboardInterrupt:
            print(f"\nℹ️  測試專案已保留: {test_project_dir}")

if __name__ == "__main__":
    test_multi_round_directory_structure()
