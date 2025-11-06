#!/usr/bin/env python3
"""
測試報告生成功能
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.project_manager import ProjectManager

def test_report_generation():
    """測試生成報告"""
    print("=" * 80)
    print("測試報告生成功能")
    print("=" * 80)
    
    # 初始化 ProjectManager
    projects_path = Path("projects")
    manager = ProjectManager(projects_path)
    
    # 掃描專案（這會加載狀態文件）
    print("\n掃描專案...")
    projects = manager.scan_projects()
    print(f"找到 {len(projects)} 個專案")
    
    # 模擬實際執行的數據
    total_files_processed = 100
    max_files_limit = 100
    
    # 生成報告
    print("\n正在生成報告...")
    report_file = manager.save_summary_report(
        total_files_processed=total_files_processed,
        max_files_limit=max_files_limit
    )
    
    if report_file:
        print(f"\n✅ 報告生成成功！")
        print(f"JSON 報告: {report_file}")
        txt_file = report_file.replace('.json', '.txt')
        print(f"TXT 報告:  {txt_file}")
        
        # 讀取並顯示 TXT 報告內容
        print("\n" + "=" * 80)
        print("TXT 報告內容預覽:")
        print("=" * 80)
        with open(txt_file, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("❌ 報告生成失敗")

if __name__ == "__main__":
    test_report_generation()
