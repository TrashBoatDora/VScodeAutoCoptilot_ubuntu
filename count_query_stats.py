#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 query_statistics 资料夹下所有 CSV 文件的真实档案数量
"""

import csv
from pathlib import Path

def count_functions_in_csv(csv_file: Path) -> int:
    """
    计算 CSV 文件中的函数数量（排除标题行）
    
    Args:
        csv_file: CSV 文件路径
        
    Returns:
        int: 函数数量
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # 跳过标题行
            next(reader, None)
            # 计算数据行数
            count = sum(1 for row in reader if row)  # 只计算非空行
        return count
    except Exception as e:
        print(f"❌ 读取文件失败 {csv_file.name}: {e}")
        return 0

def main():
    """主函数"""
    query_stats_dir = Path("CWE_Result/CWE-327/query_statistics")
    
    if not query_stats_dir.exists():
        print(f"❌ 目录不存在: {query_stats_dir}")
        return
    
    # 获取所有 CSV 文件
    csv_files = sorted(query_stats_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ 在 {query_stats_dir} 中未找到 CSV 文件")
        return
    
    print("=" * 80)
    print("📊 Query Statistics 档案数量统计")
    print("=" * 80)
    print()
    
    total_functions = 0
    project_stats = []
    
    # 统计每个项目
    for csv_file in csv_files:
        project_name = csv_file.stem  # 去掉 .csv 扩展名
        function_count = count_functions_in_csv(csv_file)
        total_functions += function_count
        project_stats.append((project_name, function_count))
        print(f"📁 {project_name}")
        print(f"   函数数量: {function_count}")
        print()
    
    # 输出总结
    print("=" * 80)
    print("📈 统计摘要")
    print("=" * 80)
    print(f"总项目数: {len(csv_files)}")
    print(f"总函数数: {total_functions}")
    print(f"平均每个项目: {total_functions / len(csv_files):.1f} 个函数")
    print()
    
    # 输出前 5 名和后 5 名
    project_stats.sort(key=lambda x: x[1], reverse=True)
    
    print("🏆 函数数量最多的 5 个项目:")
    for i, (name, count) in enumerate(project_stats[:5], 1):
        print(f"   {i}. {name}: {count} 个函数")
    print()
    
    print("📉 函数数量最少的 5 个项目:")
    for i, (name, count) in enumerate(project_stats[-5:], 1):
        print(f"   {i}. {name}: {count} 个函数")
    print()

if __name__ == "__main__":
    main()
