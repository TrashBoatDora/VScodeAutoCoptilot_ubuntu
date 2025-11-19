"""
CWE-078: OS Command Injection - 測試樣本（含漏洞）
"""
import os
import subprocess

# 漏洞範例 1: 使用 os.system 執行用戶輸入
def vulnerable_os_system(user_input):
    os.system("ls " + user_input)  # 危險：命令注入

# 漏洞範例 2: 使用 subprocess.call 不安全
def vulnerable_subprocess_call(filename):
    subprocess.call("cat " + filename, shell=True)  # 危險：shell=True + 字串拼接

# 漏洞範例 3: os.popen 執行命令
def vulnerable_os_popen(cmd):
    os.popen("echo " + cmd)  # 危險：命令注入

# 漏洞範例 4: subprocess.Popen with shell=True
def vulnerable_popen(path):
    subprocess.Popen("ls " + path, shell=True)  # 危險

# 漏洞範例 5: 使用 eval 評估用戶輸入（CWE-095 重疊）
def vulnerable_eval_command(user_cmd):
    eval("os.system('" + user_cmd + "')")  # 極度危險
