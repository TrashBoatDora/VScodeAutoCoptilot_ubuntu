#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試腳本：驗證 query_statistics 修復

測試重新生成 query_statistics.csv，確認：
1. Bandit 的漏洞被正確記錄
2. 第2輪會正確跳過已發現漏洞的函數
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.query_statistics import QueryStatistics
from src.logger import get_logger

def test_query_statistics_fix():
    """測試修復後的邏輯"""
    logger = get_logger("TestQueryStatsFix")
    
    # 初始化
    project_name = "aider__CWE-327__CAL-ALL-6b42874e__M-call"
    cwe_type = "327"
    total_rounds = 10
    
    logger.info("=" * 80)
    logger.info("測試 QueryStatistics 修復")
    logger.info("=" * 80)
    
    # 初始化 QueryStatistics
    qs = QueryStatistics(
        project_name=project_name,
        cwe_type=cwe_type,
        total_rounds=total_rounds
    )
    
    # 測試讀取第1輪掃描結果
    logger.info("\n📊 測試讀取第1輪掃描結果...")
    round1_data = qs._read_round_scan(1)
    
    if round1_data:
        logger.info(f"✅ 成功讀取第1輪數據，共 {len(round1_data)} 個函數")
        for func_key, (vuln_count, scanner) in round1_data.items():
            if vuln_count == -1:
                logger.info(f"  {func_key}: failed")
            elif vuln_count > 0:
                logger.info(f"  {func_key}: {vuln_count} ({scanner})")
            else:
                logger.info(f"  {func_key}: 0 (無漏洞)")
        
        # 檢查 aider/models.py
        models_key = "aider/models.py"
        if models_key in round1_data:
            vuln_count, scanner = round1_data[models_key]
            if vuln_count > 0:
                logger.info(f"\n✅ aider/models.py 正確記錄漏洞: {vuln_count} ({scanner})")
            else:
                logger.error(f"\n❌ aider/models.py 漏洞未被正確記錄: {vuln_count}")
        else:
            logger.error(f"\n❌ aider/models.py 不在掃描結果中")
    else:
        logger.error("❌ 無法讀取第1輪掃描結果")
    
    # 更新第1輪結果到 CSV
    logger.info("\n📝 更新第1輪結果到 CSV...")
    success = qs.update_round_result(1)
    
    if success:
        logger.info("✅ 第1輪更新成功")
        
        # 測試 should_skip_function
        logger.info("\n🔍 測試 should_skip_function...")
        
        test_functions = [
            "aider/coders/base_coder.py_show_send_output()",
            "aider/models.py_send_completion()",
            "aider/onboarding.py_generate_pkce_codes()",
            "tests/basic/test_onboarding.py_test_generate_pkce_codes()"
        ]
        
        for func_key in test_functions:
            should_skip = qs.should_skip_function(func_key)
            logger.info(f"  {func_key}: {'⏭️  應跳過' if should_skip else '▶️  繼續攻擊'}")
        
        # 檢查 aider/models.py 是否應該被跳過
        models_func_key = "aider/models.py_send_completion()"
        should_skip = qs.should_skip_function(models_func_key)
        
        if should_skip:
            logger.info(f"\n✅ aider/models.py 將在第2輪被正確跳過")
        else:
            logger.error(f"\n❌ aider/models.py 應該被跳過但未被標記")
    else:
        logger.error("❌ 第1輪更新失敗")
    
    logger.info("\n" + "=" * 80)
    logger.info("測試完成")
    logger.info("=" * 80)
    
    # 讀取並顯示更新後的 CSV
    logger.info("\n📄 顯示更新後的 query_statistics.csv:")
    csv_path = qs.csv_path
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    else:
        logger.error("CSV 檔案不存在")

if __name__ == "__main__":
    test_query_statistics_fix()
