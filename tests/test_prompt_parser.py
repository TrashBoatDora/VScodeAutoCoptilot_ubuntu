#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 prompt 解析器
驗證新的格式解析邏輯
"""

def parse_prompt_line(prompt_line: str) -> tuple:
    """
    解析 prompt.txt 的單行
    格式: filepath|function1()、function2()、function3()（多個函數用中文頓號分隔）
    只取第一個函數
    
    Returns:
        (filepath, first_function_name)
    """
    parts = prompt_line.strip().split('|')
    if len(parts) != 2:
        print(f"❌ Prompt 格式錯誤（應為 filepath|function_name）: {prompt_line}")
        return ("", "")
    
    filepath = parts[0].strip()
    functions_part = parts[1].strip()
    
    # 分隔多個函數（使用中文頓號「、」或逗號）
    functions = []
    for separator in ['、', ',']:
        if separator in functions_part:
            functions = [f.strip() for f in functions_part.split(separator)]
            break
    
    # 如果沒有分隔符，就是單一函數
    if not functions:
        functions = [functions_part]
    
    # 取第一個函數
    first_function = functions[0].strip()
    
    # 確保函數名稱包含括號（如果沒有則添加）
    if not first_function.endswith('()'):
        first_function = first_function + '()'
    
    print(f"✅ 解析 prompt: {filepath} | {first_function} (共 {len(functions)} 個函數)")
    
    return (filepath, first_function)


if __name__ == "__main__":
    # 測試案例
    test_cases = [
        "airflow-core/src/airflow/api_fastapi/auth/tokens.py|avalidated_claims()、generate()",
        "airflow-core/src/airflow/lineage/hook.py|_generate_key()",
        "providers/fab/src/airflow/providers/fab/auth_manager/security_manager/override.py|_decode_and_validate_azure_jwt()、_get_authentik_token_info()、add_register_user()、add_user()、auth_user_db()、check_password()、reset_password()",
        "task-sdk/src/airflow/sdk/bases/sensor.py|_get_next_poke_interval()",
    ]
    
    print("=" * 80)
    print("測試 Prompt 解析器")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}:")
        print(f"輸入: {test_case}")
        filepath, function_name = parse_prompt_line(test_case)
        print(f"輸出: filepath='{filepath}', function='{function_name}'")
        
        # 生成 function_key（用於統計）
        function_key = f"{filepath}_{function_name}"
        print(f"統計鍵值: {function_key}")
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
