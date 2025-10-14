#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的專案選擇器
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.project_selector_ui import show_project_selector

def main():
    print("=" * 60)
    print("測試新的專案選擇器")
    print("=" * 60)
    print("\n測試步驟：")
    print("1. 勾選一個或多個專案")
    print("2. 檢查左下角統計是否正確")
    print("3. 點擊確認，檢查是否正確返回\n")
    
    input("按 Enter 開始...")
    
    selected, clean, cancelled = show_project_selector()
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    if cancelled:
        print("❌ 已取消")
        return 1
    
    print(f"✅ 選擇成功")
    print(f"\n選中的專案 ({len(selected)} 個):")
    for project in sorted(selected):
        print(f"  • {project}")
    
    print(f"\n清理歷史: {clean} (固定為 True)")
    
    if selected:
        print("\n✅ 測試通過！")
        return 0
    else:
        print("\n❌ 測試失敗：沒有選中任何專案")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
