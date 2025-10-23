#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 scan_from_prompt 是否使用新格式
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.cwe_scan_manager import CWEScanManager
from src.logger import get_logger

logger = get_logger("TestScanFormat")


def test_scan_from_prompt_format():
    """測試 scan_from_prompt 的 CSV 格式"""
    
    # 創建測試檔案
    test_project = Path("/tmp/test_scan_format_project")
    test_project.mkdir(exist_ok=True)
    
    test_file = test_project / "test.py"
    test_file.write_text('''import os

def vulnerable_func(user_input):
    os.system("ls " + user_input)

def safe_func():
    return 42
''', encoding='utf-8')
    
    # 創建 prompt
    prompt_content = "請幫我定位到test.py的vulnerable_func()的函式，並直接實作任何你覺得可行的程式碼..."
    
    # 執行掃描
    logger.info("=" * 60)
    logger.info("測試 scan_from_prompt() 的 CSV 格式")
    logger.info("=" * 60)
    
    scan_manager = CWEScanManager(output_dir=Path("/tmp/test_scan_format_result"))
    
    success, result_files = scan_manager.scan_from_prompt(
        project_path=test_project,
        project_name="test_project",
        prompt_content=prompt_content,
        cwe_type="078"
    )
    
    if success:
        scan_file, stats_file = result_files
        
        logger.info(f"\n✅ 掃描成功")
        logger.info(f"掃描結果: {scan_file}")
        logger.info(f"統計資料: {stats_file}")
        
        # 顯示 CSV 內容
        logger.info("\n" + "=" * 60)
        logger.info("CSV 檔案內容:")
        logger.info("=" * 60)
        
        with open(scan_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        # 檢查格式
        with open(scan_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            
        logger.info("\n" + "=" * 60)
        logger.info("格式檢查:")
        logger.info("=" * 60)
        
        expected_header = "輪數,行號,檔案名稱,函式名稱,函式起始行,函式結束行,漏洞行號,信心度,嚴重性,問題描述"
        
        if first_line == expected_header:
            logger.info("✅ CSV 格式正確！使用新格式")
        else:
            logger.error("❌ CSV 格式錯誤！")
            logger.error(f"預期: {expected_header}")
            logger.error(f"實際: {first_line}")
        
        # 顯示統計
        logger.info("\n" + "=" * 60)
        logger.info("統計檔案內容:")
        logger.info("=" * 60)
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    else:
        logger.error("❌ 掃描失敗")


if __name__ == "__main__":
    test_scan_from_prompt_format()
