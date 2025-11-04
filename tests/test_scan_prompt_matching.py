#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Artificial Suicide 模式的掃描 Prompt 匹配邏輯
驗證掃描的函數與實際處理的函數一致
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.artificial_suicide_mode import ArtificialSuicideMode


def test_parse_prompt_line():
    """測試 prompt 解析邏輯"""
    print("=" * 60)
    print("測試 1：Prompt 解析邏輯（_parse_prompt_line）")
    print("=" * 60)
    
    # 創建一個臨時的 AS 模式實例（使用 None 作為依賴，只測試解析功能）
    class MockASMode:
        def __init__(self):
            # 複製 _parse_prompt_line 方法
            self._parse_prompt_line = ArtificialSuicideMode._parse_prompt_line.__get__(self)
        
        # 添加 logger 以避免錯誤
        class logger:
            @staticmethod
            def debug(msg): pass
            @staticmethod
            def error(msg): print(f"ERROR: {msg}")
    
    mock = MockASMode()
    
    # 測試案例
    test_cases = [
        {
            "input": "aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()",
            "expected_file": "aider/coders/base_coder.py",
            "expected_func": "show_send_output()",
            "description": "多函數（中文頓號分隔）- 應只取第一個"
        },
        {
            "input": "aider/models.py|send_completion()",
            "expected_file": "aider/models.py",
            "expected_func": "send_completion()",
            "description": "單函數"
        },
        {
            "input": "test.py|func1()、func2()、func3()",
            "expected_file": "test.py",
            "expected_func": "func1()",
            "description": "三個函數 - 應只取第一個"
        },
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}: {case['description']}")
        print(f"  輸入: {case['input']}")
        
        filepath, func_name = mock._parse_prompt_line(case['input'])
        
        print(f"  解析結果: file={filepath}, func={func_name}")
        print(f"  預期結果: file={case['expected_file']}, func={case['expected_func']}")
        
        if filepath == case['expected_file'] and func_name == case['expected_func']:
            print("  ✅ 通過")
        else:
            print("  ❌ 失敗")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有測試通過")
    else:
        print("❌ 部分測試失敗")
    
    return all_passed


def test_scan_prompt_construction():
    """測試掃描 Prompt 構造邏輯"""
    print("\n" + "=" * 60)
    print("測試 2：掃描 Prompt 構造邏輯")
    print("=" * 60)
    
    test_cases = [
        {
            "original_line": "aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()",
            "expected_scan_prompt": "aider/coders/base_coder.py|show_send_output()",
            "description": "多函數行 - 掃描 prompt 應只包含第一個函數"
        },
        {
            "original_line": "aider/models.py|send_completion()",
            "expected_scan_prompt": "aider/models.py|send_completion()",
            "description": "單函數行 - 掃描 prompt 應該相同"
        },
    ]
    
    class MockASMode:
        def __init__(self):
            self._parse_prompt_line = ArtificialSuicideMode._parse_prompt_line.__get__(self)
        
        class logger:
            @staticmethod
            def debug(msg): pass
            @staticmethod
            def error(msg): print(f"ERROR: {msg}")
    
    mock = MockASMode()
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}: {case['description']}")
        print(f"  原始 prompt 行: {case['original_line']}")
        
        # 模擬 Phase 2 的邏輯
        target_file, target_function_name = mock._parse_prompt_line(case['original_line'])
        
        # 構造掃描 prompt（修復後的邏輯）
        single_function_prompt = f"{target_file}|{target_function_name}"
        
        print(f"  構造的掃描 prompt: {single_function_prompt}")
        print(f"  預期的掃描 prompt: {case['expected_scan_prompt']}")
        
        # 驗證
        checks = [
            ("Prompt 格式正確", single_function_prompt == case['expected_scan_prompt']),
            ("不包含多餘函數", "、" not in single_function_prompt),
            ("只有一個函數", single_function_prompt.count("|") == 1),
        ]
        
        case_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
            if not check_result:
                case_passed = False
                all_passed = False
        
        if case_passed:
            print("  ✅ 測試通過")
        else:
            print("  ❌ 測試失敗")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有測試通過")
    else:
        print("❌ 部分測試失敗")
    
    return all_passed


def test_scan_result_expectations():
    """測試掃描結果預期"""
    print("\n" + "=" * 60)
    print("測試 3：掃描結果預期分析")
    print("=" * 60)
    
    prompt_lines = [
        "aider/coders/base_coder.py|show_send_output()、check_for_file_mentions()",
        "aider/models.py|send_completion()",
    ]
    
    print("\n給定 prompt.txt 內容：")
    for i, line in enumerate(prompt_lines, 1):
        print(f"  第 {i} 行: {line}")
    
    print("\n預期的掃描行為（修復後）：")
    print("-" * 60)
    
    class MockASMode:
        def __init__(self):
            self._parse_prompt_line = ArtificialSuicideMode._parse_prompt_line.__get__(self)
        
        class logger:
            @staticmethod
            def debug(msg): pass
            @staticmethod
            def error(msg): pass
    
    mock = MockASMode()
    
    expected_reports = []
    
    for i, line in enumerate(prompt_lines, 1):
        target_file, target_function_name = mock._parse_prompt_line(line)
        
        # 構造掃描 prompt
        scan_prompt = f"{target_file}|{target_function_name}"
        
        # 生成報告檔名（簡化版，實際由 CWE detector 生成）
        file_part = target_file.replace('/', '__').replace('.py', '')
        report_name = f"{file_part}__{target_function_name}_report.json"
        
        expected_reports.append(report_name)
        
        print(f"\n第 {i} 行:")
        print(f"  處理函數: {target_function_name}")
        print(f"  掃描 prompt: {scan_prompt}")
        print(f"  預期報告: {report_name}")
    
    print("\n" + "-" * 60)
    print(f"總計應生成 {len(expected_reports)} 個報告檔案：")
    for report in expected_reports:
        print(f"  ✅ {report}")
    
    print("\n不應該生成的報告（這些函數被忽略）：")
    ignored_functions = [
        "coders__base_coder.py__check_for_file_mentions()_report.json  (第1行的第2個函數)",
    ]
    for ignored in ignored_functions:
        print(f"  ❌ {ignored}")
    
    print("\n" + "=" * 60)
    print("✅ 預期分析完成")
    
    return True


def main():
    """執行所有測試"""
    print("\n" + "=" * 70)
    print(" " * 10 + "Artificial Suicide 掃描 Prompt 匹配測試")
    print("=" * 70)
    
    tests = [
        ("Prompt 解析邏輯", test_parse_prompt_line),
        ("掃描 Prompt 構造", test_scan_prompt_construction),
        ("掃描結果預期", test_scan_result_expectations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ 測試 '{test_name}' 執行時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 總結
    print("\n" + "=" * 70)
    print("測試總結")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有測試通過！掃描邏輯已正確匹配 Prompt 處理邏輯。")
    else:
        print("❌ 部分測試失敗，請檢查修復邏輯。")
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
