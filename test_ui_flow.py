#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的 UI 流程
"""

import sys
from pathlib import Path

# 設定模組搜尋路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.ui_manager import UIManager

def main():
    """測試 UI 流程"""
    print("=" * 60)
    print("UI 管理器測試")
    print("=" * 60)
    print()
    
    # 創建 UI 管理器
    ui_manager = UIManager()
    
    # 顯示選項對話框
    print("正在顯示選項對話框...")
    selected_projects, use_smart_wait, clean_history = ui_manager.show_options_dialog()
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    print(f"\n選中的專案 ({len(selected_projects)} 個):")
    for project in sorted(selected_projects):
        print(f"  • {project}")
    
    print(f"\n使用智能等待: {'是' if use_smart_wait else '否'}")
    print(f"清理歷史記錄: {'是' if clean_history else '否'}")
    
    # 如果需要清理，執行清理
    if clean_history and selected_projects:
        print("\n" + "=" * 60)
        print("執行清理")
        print("=" * 60)
        print()
        
        confirm = input("確定要執行清理嗎？(y/N): ").strip().lower()
        if confirm == 'y':
            success = ui_manager.clean_project_history(selected_projects)
            if success:
                print("\n✅ 清理成功！")
            else:
                print("\n❌ 清理失敗！")
        else:
            print("\n⏭️  跳過清理")
    
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷")
        sys.exit(1)
