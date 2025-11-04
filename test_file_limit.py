#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試檔案數量限制功能
"""

from pathlib import Path
from config.config import config

def test_count_prompt_lines():
    """測試計算 prompt.txt 行數的功能"""
    print("=" * 60)
    print("測試 prompt.txt 行數計算功能")
    print("=" * 60)
    
    # 測試專案目錄
    projects_dir = Path(__file__).parent / "projects"
    
    if not projects_dir.exists():
        print(f"❌ 專案目錄不存在: {projects_dir}")
        return
    
    # 列出所有專案
    projects = [p for p in projects_dir.iterdir() if p.is_dir()]
    
    if not projects:
        print(f"❌ 在 {projects_dir} 中沒有找到任何專案")
        return
    
    print(f"\n找到 {len(projects)} 個專案：\n")
    
    total_lines = 0
    for project in sorted(projects):
        line_count = config.count_project_prompt_lines(str(project))
        total_lines += line_count
        
        if line_count > 0:
            print(f"  ✅ {project.name}: {line_count} 行")
        else:
            print(f"  ⚠️  {project.name}: 沒有 prompt.txt 或檔案為空")
    
    print(f"\n{'=' * 60}")
    print(f"總計: {total_lines} 個檔案（基於所有專案的 prompt.txt 行數）")
    print(f"{'=' * 60}")

def test_file_limit_logic():
    """測試檔案限制邏輯"""
    print("\n" + "=" * 60)
    print("測試檔案限制邏輯")
    print("=" * 60)
    
    # 模擬場景
    test_cases = [
        {"max_limit": 0, "processed": 0, "project_lines": 10, "desc": "無限制"},
        {"max_limit": 100, "processed": 0, "project_lines": 10, "desc": "足夠配額"},
        {"max_limit": 100, "processed": 95, "project_lines": 10, "desc": "部分配額"},
        {"max_limit": 100, "processed": 100, "project_lines": 10, "desc": "已達限制"},
        {"max_limit": 100, "processed": 105, "project_lines": 10, "desc": "已超限制"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        max_limit = case["max_limit"]
        processed = case["processed"]
        project_lines = case["project_lines"]
        desc = case["desc"]
        
        print(f"\n測試案例 {i}: {desc}")
        print(f"  最大限制: {max_limit}")
        print(f"  已處理: {processed}")
        print(f"  專案檔案數: {project_lines}")
        
        if max_limit > 0:
            if processed >= max_limit:
                print(f"  結果: ❌ 跳過專案（已達限制）")
            else:
                remaining = max_limit - processed
                if project_lines > remaining:
                    print(f"  結果: ⚠️  部分處理（僅處理前 {remaining} 個檔案）")
                else:
                    print(f"  結果: ✅ 完整處理（剩餘配額: {remaining}）")
        else:
            print(f"  結果: ✅ 完整處理（無限制）")

if __name__ == "__main__":
    test_count_prompt_lines()
    test_file_limit_logic()
    print("\n✅ 測試完成！")
