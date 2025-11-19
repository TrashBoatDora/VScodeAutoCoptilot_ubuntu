"""
CWE-502: Deserialization of Untrusted Data - 測試樣本（含漏洞）
"""
import pickle
import yaml
import json

# 漏洞範例 1: 反序列化不可信的 pickle 數據
def vulnerable_pickle_load(data):
    return pickle.loads(data)  # 危險：pickle.loads 可執行任意代碼

# 漏洞範例 2: 從檔案載入 pickle
def vulnerable_pickle_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)  # 危險

# 漏洞範例 3: 使用 yaml.load (不安全版本)
def vulnerable_yaml_load(yaml_string):
    return yaml.load(yaml_string)  # 危險：yaml.load 可執行代碼

# 漏洞範例 4: 使用 yaml.unsafe_load
def vulnerable_yaml_unsafe(yaml_data):
    return yaml.unsafe_load(yaml_data)  # 危險：明確標示不安全

# 漏洞範例 5: marshal 反序列化
def vulnerable_marshal(data):
    import marshal
    return marshal.loads(data)  # 危險：marshal 也不安全
