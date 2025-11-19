"""
CWE-502: Deserialization of Untrusted Data - 安全範例（無漏洞）
"""
import json
import yaml

# 安全範例 1: 使用 JSON 反序列化
def safe_json_load(json_string):
    return json.loads(json_string)  # 安全：JSON 不執行代碼

# 安全範例 2: 使用 yaml.safe_load
def safe_yaml_load(yaml_string):
    return yaml.safe_load(yaml_string)  # 安全：safe_load 限制類型

# 安全範例 3: 使用 JSON 從檔案載入
def safe_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)  # 安全

# 安全範例 4: 使用白名單驗證 pickle（相對安全）
def safe_pickle_with_validation(data, allowed_classes):
    import pickle
    import io
    
    class SafeUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if f"{module}.{name}" in allowed_classes:
                return super().find_class(module, name)
            raise pickle.UnpicklingError(f"Class {module}.{name} not allowed")
    
    return SafeUnpickler(io.BytesIO(data)).load()  # 相對安全

# 安全範例 5: 只處理原生 Python 類型
def safe_literal_eval(string_data):
    import ast
    return ast.literal_eval(string_data)  # 安全：只評估字面量
