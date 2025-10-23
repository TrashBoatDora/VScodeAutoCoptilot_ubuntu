#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 prompt 路徑提取功能
"""

import re
from pathlib import Path

def extract_file_paths_from_prompt(prompt_content: str):
    """
    從 prompt 內容中提取檔案路徑
    格式：請幫我定位到{檔案路徑}的{函式名稱}的函式
    """
    file_paths = []
    seen_paths = set()
    
    # 正則表達式模式
    pattern = r'請幫我定位到([a-zA-Z0-9_/\-\.]+\.py)的'
    
    matches = re.findall(pattern, prompt_content)
    
    for match in matches:
        cleaned_path = match.strip()
        if cleaned_path and cleaned_path not in seen_paths:
            file_paths.append(cleaned_path)
            seen_paths.add(cleaned_path)
    
    return file_paths


# 測試
if __name__ == "__main__":
    # 讀取實際的 prompt.txt
    prompt_file = Path("projects/aider__CWE-022__CAL-ALL-6b42874e__M-call/prompt.txt")
    
    if not prompt_file.exists():
        print(f"❌ 檔案不存在: {prompt_file}")
        exit(1)
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    print("=" * 70)
    print("測試 Prompt 路徑提取")
    print("=" * 70)
    
    # 提取路徑
    file_paths = extract_file_paths_from_prompt(prompt_content)
    
    print(f"\n✅ 成功提取 {len(file_paths)} 個檔案路徑：\n")
    
    # 分組顯示
    from collections import defaultdict
    by_dir = defaultdict(list)
    
    for path in file_paths:
        if '/' in path:
            dir_name = path.split('/')[0]
        else:
            dir_name = '根目錄'
        by_dir[dir_name].append(path)
    
    # 按目錄顯示
    for dir_name in sorted(by_dir.keys()):
        print(f"\n📁 {dir_name}/ ({len(by_dir[dir_name])} 個檔案)")
        for path in sorted(by_dir[dir_name]):
            print(f"   ✓ {path}")
    
    print("\n" + "=" * 70)
    print(f"總計: {len(file_paths)} 個檔案")
    print("=" * 70)
    
    # 檢查是否有任何檔案不存在
    print("\n檢查檔案是否存在...")
    project_path = Path("projects/aider__CWE-022__CAL-ALL-6b42874e__M-call")
    
    not_found = []
    for file_path in file_paths:
        full_path = project_path / file_path
        if not full_path.exists():
            not_found.append(file_path)
    
    if not_found:
        print(f"\n⚠️  {len(not_found)} 個檔案不存在:")
        for path in not_found:
            print(f"   ❌ {path}")
    else:
        print(f"\n✅ 所有 {len(file_paths)} 個檔案都存在！")
    
    print("\n" + "=" * 70)
