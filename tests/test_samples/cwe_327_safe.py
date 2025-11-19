"""
CWE-327: Broken Cryptography - 安全範例（無漏洞）
"""
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# 安全範例 1: 使用 SHA256
def safe_sha256_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()  # 安全：SHA256

# 安全範例 2: 使用 SHA512
def safe_sha512_hash(password):
    return hashlib.sha512(password.encode()).hexdigest()  # 安全：SHA512

# 安全範例 3: 使用 bcrypt 雜湊密碼
def safe_bcrypt_password(password):
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)  # 安全：bcrypt

# 安全範例 4: 使用 cryptography 函式庫
def safe_cryptography_hash(data):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data.encode())
    return digest.finalize()  # 安全：現代加密庫

# 安全範例 5: 使用 PBKDF2 衍生金鑰
def safe_pbkdf2_key(password, salt):
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())  # 安全：PBKDF2
