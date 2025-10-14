#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試專案選擇器 UI
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.project_selector_ui import show_project_selector

def main():
    """測試專案選擇器"""
    print("=" * 60)
    print("專案選擇器測試")
    print("=" * 60)
    print()
    
    # 顯示專案選擇器
    projects_dir = Path(__file__).parent.parent / "projects"
    selected_projects, clean_history, cancelled = show_project_selector(projects_dir)
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    if cancelled:
        print("❌ 使用者取消選擇")
    else:
        print(f"✅ 選擇完成")
        print(f"\n選中的專案 ({len(selected_projects)} 個):")
        for project in sorted(selected_projects):
            print(f"  • {project}")
        
        print(f"\n清理歷史記錄: {'是' if clean_history else '否'}")
    
    print()
    return 0 if not cancelled else 1


if __name__ == "__main__":
    sys.exit(main())
