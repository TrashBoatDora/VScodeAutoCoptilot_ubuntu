#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Query Statistics 生成功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.query_statistics import generate_query_statistics, initialize_query_statistics

def test_batch_generation():
    """測試批次生成功能（舊版）"""
    print("🧪 測試 Query Statistics 批次生成功能")
    print("=" * 60)
    
    # 使用現有的專案資料進行測試
    project_name = "aider__CWE-327__CAL-ALL-6b42874e__M-call"
    cwe_type = "327"
    total_rounds = 2  # 目前有第1輪和第2輪的資料
    
    print(f"專案: {project_name}")
    print(f"CWE: {cwe_type}")
    print(f"總輪數: {total_rounds}")
    print("-" * 60)
    
    # 生成統計
    success = generate_query_statistics(
        project_name=project_name,
        cwe_type=cwe_type,
        total_rounds=total_rounds
    )
    
    if success:
        print("✅ 批次統計生成成功！")
        
        # 讀取並顯示結果（新路徑）
        result_path = Path(__file__).parent.parent / "CWE_Result" / f"CWE-{cwe_type}" / "query_statistics" / f"{project_name}.csv"
        
        if result_path.exists():
            print(f"\n📄 生成的檔案: {result_path}")
            print("\n內容預覽:")
            print("=" * 60)
            with open(result_path, 'r', encoding='utf-8') as f:
                print(f.read())
            print("=" * 60)
        else:
            print(f"⚠️  檔案未找到: {result_path}")
    else:
        print("❌ 批次統計生成失敗")
        return False
    
    return True

def test_incremental_update():
    """測試即時更新功能（新版）"""
    print("\n🧪 測試 Query Statistics 即時更新功能")
    print("=" * 60)
    
    project_name = "test_project"
    cwe_type = "327"
    total_rounds = 4
    
    # 假設的函式列表
    function_list = [
        "aider/coders/base_coder.py_show_send_output()",
        "aider/models.py_send_completion()",
        "aider/onboarding.py_generate_pkce_codes()",
        "tests/basic/test_onboarding.py_test_generate_pkce_codes()"
    ]
    
    print(f"專案: {project_name}")
    print(f"CWE: {cwe_type}")
    print(f"總輪數: {total_rounds}")
    print(f"函式數: {len(function_list)}")
    print("-" * 60)
    
    # 初始化
    stats = initialize_query_statistics(
        project_name=project_name,
        cwe_type=cwe_type,
        total_rounds=total_rounds,
        function_list=function_list
    )
    
    print("✅ 初始化完成")
    
    # 顯示初始 CSV（新路徑）
    result_path = Path(__file__).parent.parent / "CWE_Result" / f"CWE-{cwe_type}" / "query_statistics" / f"{project_name}.csv"
    
    if result_path.exists():
        print(f"\n📄 初始 CSV 內容:")
        print("=" * 60)
        with open(result_path, 'r', encoding='utf-8') as f:
            print(f.read())
        print("=" * 60)
    
    print("\n✅ 即時更新功能測試完成")
    return True

if __name__ == "__main__":
    success1 = test_batch_generation()
    success2 = test_incremental_update()
    sys.exit(0 if (success1 and success2) else 1)
