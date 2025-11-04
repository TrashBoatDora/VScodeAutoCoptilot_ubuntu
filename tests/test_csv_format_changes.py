#!/usr/bin/env python3
"""
測試 CSV 格式變更：AS 模式 vs 非 AS 模式

測試項目：
1. AS 模式（有 function_name_tracker）使用「修改前函式名稱」、「修改後函式名稱」兩欄
2. 非 AS 模式（無 function_name_tracker）使用單一「函式名稱」欄
3. 非 AS 模式只提取每行的第一個函式
"""

import sys
import tempfile
from pathlib import Path
import csv

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cwe_scan_manager import CWEScanManager, FunctionTarget
from src.function_name_tracker import FunctionNameTracker


def test_csv_columns_as_mode():
    """測試 AS 模式的 CSV 欄位"""
    print("=" * 80)
    print("測試 1: AS 模式（有 function_name_tracker）- 應有「修改前/後函式名稱」兩欄")
    print("=" * 80)
    
    # 建立臨時目錄
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 初始化 function_name_tracker（模擬 AS 模式）
        tracker = FunctionNameTracker(project_name="test_project")
        tracker.record_function_change(
            filepath="test.py", 
            original_name="original_func",
            modified_name="modified_func",
            round_num=1
        )
        
        # 建立 CWEScanManager（有 tracker = AS 模式）
        scan_manager = CWEScanManager(output_dir=tmpdir, function_name_tracker=tracker)
        
        # 準備測試資料
        csv_file = tmpdir / "test_as_mode.csv"
        function_targets = [
            FunctionTarget(file_path="test.py", function_names=["original_func"])
        ]
        scan_results = {}
        
        # 呼叫 _save_function_level_csv
        scan_manager._save_function_level_csv(
            csv_file, function_targets, scan_results, 
            round_number=1, line_number=1, append_mode=False
        )
        
        # 讀取 CSV 並檢查欄位
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            print(f"✅ CSV 欄位: {headers}")
            
            # 驗證欄位
            assert '修改前函式名稱' in headers, "AS 模式應包含「修改前函式名稱」欄位"
            assert '修改後函式名稱' in headers, "AS 模式應包含「修改後函式名稱」欄位"
            assert '函式名稱' not in headers or headers.count('函式名稱') == 0, "AS 模式不應有單一「函式名稱」欄位"
            
            print("✅ AS 模式欄位驗證通過")
            
            # 檢查資料行
            data_row = next(reader)
            print(f"✅ 資料行: {data_row}")
            before_idx = headers.index('修改前函式名稱')
            after_idx = headers.index('修改後函式名稱')
            print(f"   修改前函式名稱: {data_row[before_idx]}")
            print(f"   修改後函式名稱: {data_row[after_idx]}")


def test_csv_columns_non_as_mode():
    """測試非 AS 模式的 CSV 欄位"""
    print("\n" + "=" * 80)
    print("測試 2: 非 AS 模式（無 function_name_tracker）- 應只有「函式名稱」一欄")
    print("=" * 80)
    
    # 建立臨時目錄
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 建立 CWEScanManager（無 tracker = 非 AS 模式）
        scan_manager = CWEScanManager(output_dir=tmpdir, function_name_tracker=None)
        
        # 準備測試資料
        csv_file = tmpdir / "test_non_as_mode.csv"
        function_targets = [
            FunctionTarget(file_path="test.py", function_names=["test_function"])
        ]
        scan_results = {}
        
        # 呼叫 _save_function_level_csv
        scan_manager._save_function_level_csv(
            csv_file, function_targets, scan_results, 
            round_number=1, line_number=1, append_mode=False
        )
        
        # 讀取 CSV 並檢查欄位
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            print(f"✅ CSV 欄位: {headers}")
            
            # 驗證欄位
            assert '函式名稱' in headers, "非 AS 模式應包含「函式名稱」欄位"
            assert '修改前函式名稱' not in headers, "非 AS 模式不應有「修改前函式名稱」欄位"
            assert '修改後函式名稱' not in headers, "非 AS 模式不應有「修改後函式名稱」欄位"
            
            print("✅ 非 AS 模式欄位驗證通過")
            
            # 檢查資料行
            data_row = next(reader)
            print(f"✅ 資料行: {data_row}")
            func_idx = headers.index('函式名稱')
            print(f"   函式名稱: {data_row[func_idx]}")


def test_extract_first_function_only():
    """測試統一只提取第一個函式（AS 和非 AS 模式都一樣）"""
    print("\n" + "=" * 80)
    print("測試 3: 統一只提取每行的第一個函式（AS 和非 AS 模式相同）")
    print("=" * 80)
    
    # 測試資料（每行有多個函式）
    prompt_multi_functions = """test1.py|func1()、func2()、func3()
test2.py|funcA(), funcB()
test3.py|single_func()"""
    
    # === 非 AS 模式 ===
    print("\n[非 AS 模式]")
    scan_manager_non_as = CWEScanManager(function_name_tracker=None)
    targets_non_as = scan_manager_non_as.extract_function_targets_from_prompt(prompt_multi_functions)
    
    print(f"提取結果（非 AS 模式）:")
    for target in targets_non_as:
        print(f"  {target.file_path}: {target.function_names}")
    
    # 驗證：每行應只有一個函式
    assert len(targets_non_as) == 3, "應提取 3 行"
    assert targets_non_as[0].function_names == ["func1()"], "第 1 行應只有 func1()"
    assert targets_non_as[1].function_names == ["funcA()"], "第 2 行應只有 funcA()"
    assert targets_non_as[2].function_names == ["single_func()"], "第 3 行應只有 single_func()"
    print("✅ 非 AS 模式：正確只提取第一個函式")
    
    # === AS 模式：實際上 AS 模式會在呼叫前就構造為單一函式 ===
    print("\n[AS 模式]")
    print("注意：AS 模式在 artificial_suicide_mode.py 中會構造單一函式 prompt")
    print("      例如: single_function_prompt = f\"{target_file}|{target_function_name}\"")
    print("      所以傳入 extract_function_targets_from_prompt 時已經是單一函式")
    
    # 模擬 AS 模式實際傳入的 prompt（已經是單一函式）
    prompt_as_mode_actual = """test1.py|func1()
test2.py|funcA()
test3.py|single_func()"""
    
    tracker = FunctionNameTracker(project_name="test_project")
    scan_manager_as = CWEScanManager(function_name_tracker=tracker)
    targets_as = scan_manager_as.extract_function_targets_from_prompt(prompt_as_mode_actual)
    
    print(f"提取結果（AS 模式 - 實際輸入）:")
    for target in targets_as:
        print(f"  {target.file_path}: {target.function_names}")
    
    # 驗證：AS 模式傳入時已經是單一函式
    assert len(targets_as) == 3, "應提取 3 行"
    assert len(targets_as[0].function_names) == 1, "第 1 行應有 1 個函式"
    assert len(targets_as[1].function_names) == 1, "第 2 行應有 1 個函式"
    assert len(targets_as[2].function_names) == 1, "第 3 行應有 1 個函式"
    print("✅ AS 模式：正確處理單一函式輸入")
    
    # === 測試保護機制：即使傳入多個函式也只取第一個 ===
    print("\n[保護機制測試]")
    print("即使 prompt 包含多個函式，也只會提取第一個")
    targets_protection = scan_manager_as.extract_function_targets_from_prompt(prompt_multi_functions)
    assert all(len(t.function_names) == 1 for t in targets_protection), "應該統一只取第一個函式"
    print("✅ 保護機制：正確限制為第一個函式")


def main():
    """執行所有測試"""
    try:
        test_csv_columns_as_mode()
        test_csv_columns_non_as_mode()
        test_extract_first_function_only()
        
        print("\n" + "=" * 80)
        print("✅ 所有測試通過！")
        print("=" * 80)
        print("\n總結:")
        print("1. ✅ AS 模式使用「修改前函式名稱」、「修改後函式名稱」兩欄")
        print("2. ✅ 非 AS 模式使用單一「函式名稱」欄")
        print("3. ✅ AS 和非 AS 模式都統一只提取並掃描每行的第一個函式")
        print("4. ✅ AS 模式在呼叫掃描前已經構造為單一函式 prompt")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
