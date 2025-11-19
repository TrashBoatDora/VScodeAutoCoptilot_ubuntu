"""
CWE-078: OS Command Injection - 安全範例（無漏洞）
Python 專案最佳實踐：優先使用 Python 內建函數，避免調用 subprocess
"""
import os
import pathlib
import shutil
import glob

# 安全範例 1: 使用 os.listdir 列出目錄（替代 ls 命令）
def safe_list_directory(directory):
    """安全：使用 Python 內建函數"""
    try:
        files = os.listdir(directory)
        return files
    except OSError as e:
        return []

# 安全範例 2: 使用 pathlib 操作文件系統（Python 3.4+）
def safe_check_file(file_path):
    """安全：使用 pathlib，面向對象的文件系統操作"""
    path = pathlib.Path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return None

# 安全範例 3: 使用 shutil 複製/移動文件（替代 cp/mv 命令）
def safe_copy_file(src, dst):
    """安全：使用 Python 標準庫"""
    try:
        shutil.copy2(src, dst)
        return True
    except (FileNotFoundError, PermissionError):
        return False

# 安全範例 4: 使用 glob 模式匹配（替代 find 命令）
def safe_find_files(pattern):
    """安全：使用 glob 搜索文件"""
    return glob.glob(pattern)

# 安全範例 5: 讀取文件內容（替代 cat 命令）
def safe_read_file(filename):
    """安全：使用 Python 文件操作"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return None
