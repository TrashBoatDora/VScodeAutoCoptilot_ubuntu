#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修正後的專案選擇器
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))

from src.project_selector_ui import show_project_selector

def main():
    """測試專案選擇器"""
    print("=" * 60)
    print("專案選擇器測試（修正版）")
    print("=" * 60)
    print()
    print("請測試以下功能：")
    print("1. 勾選一個專案，檢查左下角是否顯示 '已選擇: 1 個專案'")
    print("2. 勾選多個專案，檢查數量是否正確更新")
    print("3. 使用快速選擇按鈕（全選、全不選、反選）")
    print("4. 確認時應顯示警告訊息（將清除執行記錄）")
    print()
    input("按 Enter 開始測試...")
    print()
    
    # 顯示專案選擇器
    projects_dir = Path(__file__).parent / "projects"
    selected_projects, clean_history, cancelled = show_project_selector(projects_dir)
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    if cancelled:
        print("❌ 使用者取消選擇")
        return 1
    
    print(f"✅ 選擇完成")
    print(f"\n選中的專案 ({len(selected_projects)} 個):")
    for project in sorted(selected_projects):
        print(f"  • {project}")
    
    print(f"\n清理歷史記錄: {clean_history} (應該永遠是 True)")
    
    if clean_history:
        print("✅ 清理選項正確（固定為 True）")
    else:
        print("❌ 錯誤：清理選項應該固定為 True")
    
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
