#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的 CSV 格式
驗證檔案路徑和函數名稱分離的功能
"""

from pathlib import Path
from src.query_statistics import QueryStatistics

def test_query_statistics():
    """測試 QueryStatistics 的新格式"""
    print("=" * 80)
    print("測試 QueryStatistics - 新 CSV 格式")
    print("=" * 80)
    
    # 測試數據
    test_project = "test_project"
    test_cwe = "327"
    total_rounds = 3
    
    # 測試 function_list（格式：filepath_function()）
    function_list = [
        "airflow-core/src/airflow/api_fastapi/auth/tokens.py_avalidated_claims()",
        "airflow-core/src/airflow/lineage/hook.py__generate_key()",
        "providers/fab/src/airflow/providers/fab/auth_manager/security_manager/override.py__decode_and_validate_azure_jwt()",
    ]
    
    # 創建測試目錄
    test_result_path = Path(__file__).parent / "test_output"
    test_result_path.mkdir(exist_ok=True)
    
    # 初始化統計器
    print(f"\n📊 初始化統計器...")
    print(f"   專案: {test_project}")
    print(f"   CWE: {test_cwe}")
    print(f"   總輪數: {total_rounds}")
    print(f"   函數數量: {len(function_list)}")
    
    stats = QueryStatistics(
        project_name=test_project,
        cwe_type=test_cwe,
        total_rounds=total_rounds,
        function_list=function_list,
        base_result_path=test_result_path
    )
    
    # 測試 _split_function_key
    print(f"\n🔧 測試 _split_function_key 方法:")
    for func_key in function_list:
        filepath, function_name = stats._split_function_key(func_key)
        print(f"   輸入: {func_key}")
        print(f"   輸出: 檔案路徑='{filepath}', 函數名稱='{function_name}'")
        print()
    
    # 初始化 CSV
    print(f"📝 初始化 CSV 文件...")
    success = stats.initialize_csv()
    
    if success:
        print(f"   ✅ CSV 初始化成功")
        print(f"   路徑: {stats.csv_path}")
        
        # 讀取並顯示 CSV 內容
        print(f"\n📄 CSV 內容預覽:")
        with open(stats.csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    else:
        print(f"   ❌ CSV 初始化失敗")
        return False
    
    # 測試 _read_current_csv
    print(f"\n📖 測試讀取 CSV:")
    current_data = stats._read_current_csv()
    if current_data is not None:
        print(f"   ✅ 成功讀取 {len(current_data)} 筆資料")
        for key, data in list(current_data.items())[:2]:  # 只顯示前2筆
            print(f"   Key: {key}")
            print(f"   Data: {data}")
    else:
        print(f"   ❌ 讀取失敗")
        return False
    
    # 測試 should_skip_function
    print(f"\n🔍 測試 should_skip_function:")
    for func_key in function_list[:2]:
        should_skip = stats.should_skip_function(func_key)
        print(f"   {func_key}: {should_skip}")
    
    print("\n" + "=" * 80)
    print("✅ 所有測試完成")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        test_query_statistics()
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
