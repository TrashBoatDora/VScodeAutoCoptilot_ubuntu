#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試專案選擇器 - 檢查變數狀態
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent))

from src.project_selector_ui import show_project_selector
from src.logger import get_logger

logger = get_logger("DebugTest")

def main():
    """調試測試"""
    print("=" * 60)
    print("專案選擇器調試測試")
    print("=" * 60)
    print()
    print("請按照以下步驟測試：")
    print("1. 勾選 aider 專案")
    print("2. 觀察左下角統計是否顯示 '已選擇: 1 個專案'")
    print("3. 點擊「確認」按鈕")
    print("4. 查看控制台輸出")
    print()
    input("按 Enter 開始...")
    print()
    
    # 顯示專案選擇器
    projects_dir = Path(__file__).parent / "projects"
    
    logger.info("準備顯示專案選擇器")
    selected_projects, clean_history, cancelled = show_project_selector(projects_dir)
    
    print("\n" + "=" * 60)
    print("返回結果")
    print("=" * 60)
    
    if cancelled:
        print("❌ 使用者取消選擇")
        logger.warning("使用者取消選擇")
    else:
        print(f"✅ 選擇完成")
        print(f"\n選中的專案數量: {len(selected_projects)}")
        print(f"選中的專案:")
        for project in sorted(selected_projects):
            print(f"  • {project}")
        print(f"\n清理歷史: {clean_history}")
        
        logger.info(f"最終結果 - 專案: {selected_projects}, 清理: {clean_history}, 取消: {cancelled}")
        
        if not selected_projects:
            print("\n⚠️  警告：沒有選中任何專案！")
            print("這不應該發生，因為在對話框中已經勾選了專案。")
            print("請檢查上面的日誌輸出，查看 '收集到的專案' 和 '專案變數狀態'")
    
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
