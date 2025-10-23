#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整測試：驗證兩種掃描方式都使用新格式
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.cwe_scan_manager import CWEScanManager
from src.logger import get_logger

logger = get_logger("TestBothFormats")


def test_both_scan_methods():
    """測試兩種掃描方式的格式"""
    
    # 創建測試專案
    test_project = Path("/tmp/test_both_formats")
    test_project.mkdir(exist_ok=True)
    
    test_file = test_project / "vulnerable.py"
    test_file.write_text('''import os
import pickle

def high_vuln(user_input):
    """HIGH 嚴重性"""
    os.system("cat " + user_input)

def medium_vuln(data):
    """MEDIUM 嚴重性"""
    return pickle.loads(data)

def safe():
    return "OK"
''', encoding='utf-8')
    
    scan_manager = CWEScanManager(output_dir=Path("/tmp/test_both_formats_result"))
    
    logger.info("=" * 80)
    logger.info("測試 1: scan_from_prompt() 方法（舊的整體掃描）")
    logger.info("=" * 80)
    
    prompt = "請幫我定位到vulnerable.py的high_vuln()的函式..."
    
    success1, result1 = scan_manager.scan_from_prompt(
        project_path=test_project,
        project_name="test_scan_from_prompt",
        prompt_content=prompt,
        cwe_type="078"
    )
    
    if success1:
        scan_file1, stats_file1 = result1
        logger.info(f"\n✅ 方法 1 成功: {scan_file1}")
        
        with open(scan_file1, 'r', encoding='utf-8') as f:
            header1 = f.readline().strip()
            logger.info(f"標題: {header1}")
            
        if "信心度" in header1 and "嚴重性" in header1:
            logger.info("✅ 使用新格式（包含信心度和嚴重性）")
        else:
            logger.error("❌ 使用舊格式")
    
    logger.info("\n" + "=" * 80)
    logger.info("測試 2: append_scan_results() 方法（逐行掃描）")
    logger.info("=" * 80)
    
    # 模擬逐行掃描
    scan_results = scan_manager.scan_files(
        project_path=test_project,
        file_paths=["vulnerable.py"],
        cwe_type="078"
    )
    
    success2 = scan_manager.append_scan_results(
        project_name="test_append",
        cwe_type="078",
        scan_results=scan_results,
        round_number=1,
        line_number=1
    )
    
    if success2:
        scan_file2 = Path("/tmp/test_both_formats_result/CWE-078/test_append_scan.csv")
        logger.info(f"\n✅ 方法 2 成功: {scan_file2}")
        
        with open(scan_file2, 'r', encoding='utf-8') as f:
            header2 = f.readline().strip()
            logger.info(f"標題: {header2}")
            
        if "信心度" in header2 and "嚴重性" in header2:
            logger.info("✅ 使用新格式（包含信心度和嚴重性）")
        else:
            logger.error("❌ 使用舊格式")
    
    logger.info("\n" + "=" * 80)
    logger.info("格式對比")
    logger.info("=" * 80)
    
    logger.info("\n方法 1 (scan_from_prompt) 的 CSV 內容:")
    logger.info("-" * 80)
    with open(scan_file1, 'r', encoding='utf-8') as f:
        print(f.read())
    
    logger.info("\n方法 2 (append_scan_results) 的 CSV 內容:")
    logger.info("-" * 80)
    with open(scan_file2, 'r', encoding='utf-8') as f:
        print(f.read())
    
    logger.info("\n" + "=" * 80)
    logger.info("結論")
    logger.info("=" * 80)
    
    expected_cols = ["輪數", "行號", "檔案名稱", "函式名稱", "函式起始行", "函式結束行", "漏洞行號", "信心度", "嚴重性", "問題描述"]
    
    with open(scan_file1, 'r', encoding='utf-8') as f:
        header1 = f.readline().strip().split(',')
    
    with open(scan_file2, 'r', encoding='utf-8') as f:
        header2 = f.readline().strip().split(',')
    
    if header1 == expected_cols and header2 == expected_cols:
        logger.info("✅✅✅ 兩種方法都使用相同的新格式！")
        logger.info(f"欄位數量: {len(expected_cols)}")
        logger.info(f"包含: 信心度, 嚴重性, 函式資訊")
    else:
        logger.error("❌ 格式不一致或不正確")
        logger.error(f"方法 1: {header1}")
        logger.error(f"方法 2: {header2}")
        logger.error(f"預期: {expected_cols}")


if __name__ == "__main__":
    test_both_scan_methods()
