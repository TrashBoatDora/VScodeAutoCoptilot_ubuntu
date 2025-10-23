#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試嚴重性過濾功能 - 只統計 MEDIUM 以上的漏洞
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.cwe_detector import CWEDetector
from src.cwe_scan_manager import CWEScanManager
from src.logger import get_logger

logger = get_logger("TestSeverityFiltering")


def create_test_files():
    """創建包含不同嚴重性漏洞的測試檔案"""
    
    # 檔案 1: 包含 HIGH 和 MEDIUM 嚴重性漏洞
    test_file1 = Path("/tmp/test_high_medium.py")
    code1 = '''import os
import pickle

def high_severity_vuln(user_input):
    """HIGH 嚴重性 - OS Command Injection"""
    os.system("ls " + user_input)

def medium_severity_vuln(data):
    """MEDIUM 嚴重性 - Pickle deserialization"""
    return pickle.loads(data)
'''
    test_file1.write_text(code1, encoding='utf-8')
    logger.info(f"測試檔案 1 (HIGH + MEDIUM): {test_file1}")
    
    # 檔案 2: 只包含 LOW 嚴重性漏洞
    test_file2 = Path("/tmp/test_low_only.py")
    code2 = '''import pickle

# LOW 嚴重性 - 只是 import pickle
def safe_function():
    return "This is safe"
'''
    test_file2.write_text(code2, encoding='utf-8')
    logger.info(f"測試檔案 2 (LOW only): {test_file2}")
    
    # 檔案 3: 完全安全
    test_file3 = Path("/tmp/test_safe.py")
    code3 = '''def completely_safe():
    """這個檔案完全安全"""
    return 42

def another_safe():
    print("Hello, World!")
'''
    test_file3.write_text(code3, encoding='utf-8')
    logger.info(f"測試檔案 3 (完全安全): {test_file3}")
    
    return [test_file1, test_file2, test_file3]


def test_severity_filtering():
    """測試嚴重性過濾功能"""
    logger.info("=" * 60)
    logger.info("測試嚴重性過濾功能 - 只統計 MEDIUM 以上")
    logger.info("=" * 60)
    
    # 創建測試檔案
    test_files = create_test_files()
    
    # 初始化掃描管理器
    scan_manager = CWEScanManager(output_dir=Path("/tmp/test_severity_results"))
    
    # 掃描檔案
    logger.info("\n" + "=" * 60)
    logger.info("開始掃描測試檔案")
    logger.info("=" * 60)
    
    for round_num in range(1, 3):
        logger.info(f"\n📝 第 {round_num} 輪掃描")
        
        # 掃描所有檔案
        scan_results = scan_manager.scan_files(
            project_path=Path("/tmp"),
            file_paths=[
                "test_high_medium.py",
                "test_low_only.py",
                "test_safe.py"
            ],
            cwe_type="078"
        )
        
        # 顯示詳細結果
        logger.info("\n" + "-" * 60)
        logger.info("掃描結果詳情:")
        logger.info("-" * 60)
        
        for result in scan_results:
            logger.info(f"\n檔案: {result.file_path}")
            logger.info(f"  有漏洞: {result.has_vulnerability}")
            
            if result.details:
                for vuln in result.details:
                    logger.info(f"  - 函式: {vuln.function_name}")
                    logger.info(f"    信心度: {vuln.confidence}")
                    logger.info(f"    嚴重性: {vuln.severity}")
                    logger.info(f"    描述: {vuln.description[:50]}...")
        
        # 追加結果
        success = scan_manager.append_scan_results(
            project_name="severity_test",
            cwe_type="078",
            scan_results=scan_results,
            round_number=round_num,
            line_number=1
        )
        
        if success:
            logger.info(f"\n✅ 第 {round_num} 輪結果已追加")
        else:
            logger.error(f"\n❌ 第 {round_num} 輪結果追加失敗")
    
    # 顯示最終 CSV
    csv_file = Path("/tmp/test_severity_results/CWE-078/severity_test_scan.csv")
    if csv_file.exists():
        logger.info("\n" + "=" * 60)
        logger.info(f"最終 CSV 檔案內容: {csv_file}")
        logger.info("=" * 60)
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    
    # 顯示統計檔案
    stats_file = Path("/tmp/test_severity_results/CWE-078/statistics.csv")
    if stats_file.exists():
        logger.info("\n" + "=" * 60)
        logger.info(f"統計檔案內容 (只計算 MEDIUM+): {stats_file}")
        logger.info("=" * 60)
        with open(stats_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    
    logger.info("\n" + "=" * 60)
    logger.info("測試完成")
    logger.info("=" * 60)
    
    # 驗證統計
    logger.info("\n預期結果:")
    logger.info("  - test_high_medium.py: 不安全 (有 HIGH 和 MEDIUM)")
    logger.info("  - test_low_only.py: 安全 (只有 LOW，不計入)")
    logger.info("  - test_safe.py: 安全 (無漏洞)")
    logger.info("  - 統計: 不安全=2 (2輪 x 1檔案), 安全=4 (2輪 x 2檔案)")


if __name__ == "__main__":
    test_severity_filtering()
