#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 CWE 掃描的函式級別偵測功能
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.cwe_detector import CWEDetector
from src.cwe_scan_manager import CWEScanManager
from src.logger import get_logger

logger = get_logger("TestFunctionDetection")


def create_test_file():
    """創建包含多個函式和漏洞的測試檔案"""
    test_file = Path("/tmp/test_multiple_functions.py")
    
    code = '''import os
import pickle
import subprocess

def safe_function():
    """這個函式是安全的"""
    print("Hello, World!")
    return True

def vulnerable_function1(user_input):
    """CWE-078: OS Command Injection"""
    # 不安全的命令執行
    os.system("ls " + user_input)
    return user_input

def another_safe_function(data):
    """這個函式也是安全的"""
    cleaned = data.strip()
    return cleaned.upper()

def vulnerable_function2(serialized_data):
    """CWE-502: Unsafe Deserialization"""
    # 不安全的反序列化
    obj = pickle.loads(serialized_data)
    return obj

def vulnerable_function3(cmd):
    """CWE-078: Another command injection"""
    # 使用 subprocess 但仍然不安全
    subprocess.call(cmd, shell=True)

class MyClass:
    def safe_method(self):
        """類中的安全方法"""
        return "safe"
    
    def vulnerable_method(self, path):
        """CWE-078: Method with vulnerability"""
        os.system(f"cat {path}")

def final_safe_function():
    """最後一個安全函式"""
    return 42
'''
    
    test_file.write_text(code, encoding='utf-8')
    logger.info(f"測試檔案已創建: {test_file}")
    return test_file


def test_function_detection():
    """測試函式級別的漏洞偵測"""
    logger.info("=" * 60)
    logger.info("開始測試函式級別的 CWE 漏洞偵測")
    logger.info("=" * 60)
    
    # 創建測試檔案
    test_file = create_test_file()
    
    # 初始化檢測器
    detector = CWEDetector()
    
    # 掃描 CWE-078 (OS Command Injection)
    logger.info("\n📋 掃描 CWE-078 (OS Command Injection)...")
    vulnerabilities = detector.scan_single_file(test_file, "078")
    
    logger.info(f"\n發現 {len(vulnerabilities)} 個漏洞:")
    logger.info("-" * 60)
    
    for i, vuln in enumerate(vulnerabilities, 1):
        logger.info(f"\n漏洞 #{i}:")
        logger.info(f"  檔案: {vuln.file_path}")
        logger.info(f"  函式: {vuln.function_name or '(未知)'}")
        logger.info(f"  函式範圍: 第 {vuln.function_start} 行 - 第 {vuln.function_end} 行")
        logger.info(f"  漏洞行號: {vuln.line_start}")
        logger.info(f"  信心度: {vuln.confidence}")  # 新增
        logger.info(f"  嚴重性: {vuln.severity}")
        logger.info(f"  描述: {vuln.description}")
    
    # 測試掃描管理器的累積儲存功能
    logger.info("\n" + "=" * 60)
    logger.info("測試掃描管理器的函式級別累積儲存")
    logger.info("=" * 60)
    
    scan_manager = CWEScanManager(output_dir=Path("/tmp/test_cwe_results"))
    
    # 模擬多輪掃描
    for round_num in range(1, 3):
        for line_num in range(1, 3):
            logger.info(f"\n📝 第 {round_num} 輪 / 第 {line_num} 行")
            
            # 掃描檔案
            scan_results = scan_manager.scan_files(
                project_path=Path("/tmp"),
                file_paths=["test_multiple_functions.py"],
                cwe_type="078"
            )
            
            # 追加結果
            success = scan_manager.append_scan_results(
                project_name="test_project",
                cwe_type="078",
                scan_results=scan_results,
                round_number=round_num,
                line_number=line_num
            )
            
            if success:
                logger.info(f"  ✅ 結果已追加")
            else:
                logger.error(f"  ❌ 結果追加失敗")
    
    # 顯示最終 CSV 檔案
    csv_file = Path("/tmp/test_cwe_results/CWE-078/test_project_scan.csv")
    if csv_file.exists():
        logger.info("\n" + "=" * 60)
        logger.info(f"最終 CSV 檔案內容: {csv_file}")
        logger.info("=" * 60)
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    
    logger.info("\n" + "=" * 60)
    logger.info("測試完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_function_detection()
