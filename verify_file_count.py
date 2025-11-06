#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证实际处理的文件数与 query_statistics 的一致性
"""

import csv
import re
from pathlib import Path

def count_functions_in_csv(csv_file: Path) -> int:
    """计算 CSV 文件中的函数数量"""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # 跳过标题行
            count = sum(1 for row in reader if row)
        return count
    except Exception as e:
        print(f"❌ 读取文件失败 {csv_file.name}: {e}")
        return 0

def extract_project_names_from_log(log_file: Path):
    """从日志中提取项目处理顺序和实际处理的文件数"""
    project_order = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 匹配：📊 已處理 X 個檔案（總計: Y）
            match = re.search(r'📊 已處理 (\d+) 個檔案（總計: (\d+)）', line)
            if match:
                files_in_project = int(match.group(1))
                total_files = int(match.group(2))
                
                # 找到上一行的项目名称
                # 向上查找 "初始化 Artificial Suicide Mode: 專案=XXX"
                
            # 匹配：初始化 Artificial Suicide Mode: 專案=XXX
            match_project = re.search(r'初始化 Artificial Suicide Mode: 專案=([^,]+)', line)
            if match_project:
                project_name = match_project.group(1)
                
            # 匹配：Artificial Suicide 攻擊模式執行成功（處理了 X 個檔案）
            match_success = re.search(r'Artificial Suicide 攻擊模式執行成功（處理了 (\d+) 個檔案）', line)
            if match_success:
                files_processed = int(match_success.group(1))
                project_order.append((project_name, files_processed))
    
    return project_order

def main():
    """主函数"""
    print("=" * 80)
    print("🔍 验证文件数量一致性")
    print("=" * 80)
    print()
    
    # 1. 读取 query_statistics 的统计
    query_stats_dir = Path("CWE_Result/CWE-327/query_statistics")
    csv_files = sorted(query_stats_dir.glob("*.csv"))
    
    csv_stats = {}
    total_csv_functions = 0
    
    for csv_file in csv_files:
        project_name = csv_file.stem
        function_count = count_functions_in_csv(csv_file)
        csv_stats[project_name] = function_count
        total_csv_functions += function_count
    
    print(f"📊 Query Statistics CSV 统计:")
    print(f"   项目数: {len(csv_stats)}")
    print(f"   总函数数: {total_csv_functions}")
    print()
    
    # 2. 从日志读取实际处理顺序
    log_file = Path("logs/automation__20251106_004654.log")
    if log_file.exists():
        project_order = extract_project_names_from_log(log_file)
        
        print(f"📝 日志中记录的处理顺序:")
        total_log_files = 0
        for i, (project, files) in enumerate(project_order, 1):
            total_log_files += files
            # 提取项目简称（去掉 __CWE-327__ 后缀）
            short_name = project.split("__CWE-327__")[0] if "__CWE-327__" in project else project
            csv_count = csv_stats.get(project, 0)
            
            match_status = "✅" if files == csv_count else "❌"
            print(f"   {i:2}. {short_name:30} - 处理: {files:3} | CSV: {csv_count:3} {match_status}")
        
        print()
        print(f"📈 总计:")
        print(f"   日志处理总数: {total_log_files}")
        print(f"   CSV 记录总数: {total_csv_functions}")
        print(f"   差异: {total_csv_functions - total_log_files}")
    
    # 3. 检查是否有 CSV 文件但日志中没有对应项目
    print()
    print("🔍 额外的 CSV 文件（日志中没有的项目）:")
    processed_projects = {p for p, _ in project_order}
    extra_csvs = []
    for csv_name in csv_stats.keys():
        if csv_name not in processed_projects:
            extra_csvs.append((csv_name, csv_stats[csv_name]))
    
    if extra_csvs:
        for csv_name, count in extra_csvs:
            short_name = csv_name.split("__CWE-327__")[0] if "__CWE-327__" in csv_name else csv_name
            print(f"   - {short_name}: {count} 个函数")
            total_csv_functions += 0  # 这些不应该计入
    else:
        print("   （无）")
    
    print()
    print("=" * 80)
    print("🎯 结论:")
    if total_log_files == 100:
        print(f"   ✅ 日志显示正确处理了 100 个函数")
    else:
        print(f"   ❌ 日志显示处理了 {total_log_files} 个函数（预期 100）")
    
    if total_csv_functions == 111:
        print(f"   ❌ CSV 记录了 111 个函数（超出限制 11 个）")
    else:
        print(f"   📊 CSV 记录了 {total_csv_functions} 个函数")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
