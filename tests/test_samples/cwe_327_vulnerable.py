"""
CWE-327: Broken Cryptography - 測試樣本（含漏洞）
"""
import hashlib
import md5  # 已棄用的模組

# 漏洞範例 1: 使用 MD5 雜湊
def vulnerable_md5_hash(data):
    return hashlib.md5(data.encode()).hexdigest()  # 危險：MD5 不安全

# 漏洞範例 2: 使用 SHA1
def vulnerable_sha1_hash(password):
    return hashlib.sha1(password.encode()).hexdigest()  # 危險：SHA1 不安全

# 漏洞範例 3: 使用棄用的 md5 模組
def vulnerable_old_md5(text):
    m = md5.new()  # 危險：棄用的模組
    m.update(text.encode())
    return m.hexdigest()

# 漏洞範例 4: 弱加密用於密碼雜湊
def vulnerable_password_hash(password):
    salt = "fixed_salt"  # 也有 CWE-760 問題
    return hashlib.md5((password + salt).encode()).digest()  # 危險

# 漏洞範例 5: 使用 MD5 驗證完整性
def vulnerable_checksum(file_content):
    return hashlib.md5(file_content).hexdigest()  # 危險：用於完整性檢查
