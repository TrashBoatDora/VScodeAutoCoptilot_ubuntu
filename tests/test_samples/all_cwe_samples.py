"""
所有 CWE 漏洞範例 - 用於測試 Semgrep 檢測能力
包含 17 種常見的安全漏洞
"""

# ============================================================
# CWE-022: Path Traversal (路徑遍歷)
# ============================================================
import os
from flask import request

def cwe_022_path_traversal():
    """漏洞代碼：直接使用使用者輸入拼接路徑"""
    filename = request.args.get('filename')
    file_path = os.path.join("/var/www/html/uploads", filename)
    
    # 如果 filename 是 "../../../etc/passwd"，將導致敏感檔案洩漏
    with open(file_path, 'r') as f:
        data = f.read()
    return data


# ============================================================
# CWE-078: OS Command Injection (作業系統指令注入)
# ============================================================
def cwe_078_command_injection():
    """漏洞代碼：直接拼接字串執行系統指令"""
    user_input = input("Enter IP to ping: ")
    
    # 攻擊者輸入 "127.0.0.1; rm -rf /" 即可執行惡意指令
    os.system("ping -c 1 " + user_input)


# ============================================================
# CWE-079: Cross-site Scripting (XSS)
# ============================================================
from flask import Flask

app = Flask(__name__)

@app.route('/hello')
def cwe_079_xss():
    """漏洞代碼：直接回傳 HTML"""
    name = request.args.get('name')
    # 若 name 為 "<script>alert(1)</script>" 將會執行
    return f"<h1>Hello {name}</h1>"


# ============================================================
# CWE-095: Eval Injection (動態代碼執行)
# ============================================================
def cwe_095_eval_injection():
    """漏洞代碼：直接 eval 使用者輸入"""
    user_input = input("Enter a math expression: ")
    
    # 攻擊者輸入 "__import__('os').system('ls')" 即可執行指令
    result = eval(user_input)
    return result


# ============================================================
# CWE-113: HTTP Response Splitting (HTTP 回應分割)
# ============================================================
from flask import Response

def cwe_113_response_splitting():
    """漏洞代碼：未過濾換行符號"""
    val = request.args.get('lang')
    resp = Response("Content")
    # 若 val 包含 "\r\nSet-Cookie: session_id=attacker"，可注入 Header
    resp.headers['Content-Language'] = val
    return resp


# ============================================================
# CWE-117: Log Injection (日誌注入)
# ============================================================
import logging

def cwe_117_log_injection():
    """漏洞代碼：日誌中包含未經過濾的使用者輸入"""
    logging.basicConfig(level=logging.INFO)
    username = input("Enter username: ")
    
    # 若 username 為 "admin \n [INFO] User root logged in"，日誌將被偽造
    logging.info("User login attempt: " + username)


# ============================================================
# CWE-326: Inadequate Encryption Strength (加密強度不足)
# ============================================================
from Crypto.PublicKey import RSA

def cwe_326_weak_encryption():
    """漏洞代碼：生成 512 位元的 RSA 金鑰"""
    # 現代標準至少需 2048 位元
    key = RSA.generate(512)
    return key


# ============================================================
# CWE-327: Broken Cryptographic Algorithm (使用已破解的加密演算法)
# ============================================================
import hashlib

def cwe_327_broken_crypto():
    """漏洞代碼：使用 MD5 進行雜湊"""
    data = b"sensitive data"
    # MD5 已不再抗碰撞
    hash_object = hashlib.md5(data)
    return hash_object.hexdigest()


# ============================================================
# CWE-329: Predictable IV with CBC Mode (可預測的初始化向量)
# ============================================================
from Crypto.Cipher import AES

def cwe_329_predictable_iv():
    """漏洞代碼：使用固定的 IV"""
    key = b'sixteen byte key'
    # IV 必須是隨機的，不能固定
    iv = b'0000000000000000'
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher


# ============================================================
# CWE-347: Improper Signature Verification (未驗證加密簽章)
# ============================================================
import jwt

def cwe_347_jwt_no_verify():
    """漏洞代碼：解碼但不驗證簽名"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    # 攻擊者可以偽造任意 payload
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded


# ============================================================
# CWE-377: Insecure Temporary File (不安全的暫存檔)
# ============================================================
def cwe_377_insecure_temp_file():
    """漏洞代碼：手動建立可預測的暫存檔名"""
    # 可能導致 Race Condition 或符號連結攻擊
    filename = "/tmp/temp_data.txt"
    with open(filename, 'w') as f:
        f.write("sensitive data")


# ============================================================
# CWE-502: Deserialization of Untrusted Data (反序列化不可信資料)
# ============================================================
import pickle

def cwe_502_unsafe_deserialization(data):
    """漏洞代碼：直接反序列化"""
    # 若 data 包含惡意構造的 class，可執行任意代碼
    obj = pickle.loads(data)
    return obj


# ============================================================
# CWE-643: XPath Injection (XPath 注入)
# ============================================================
from lxml import etree

def cwe_643_xpath_injection(user, password):
    """漏洞代碼：XPath 注入"""
    xml = etree.parse("users.xml")
    # 若 user 輸入 "' or '1'='1"，將繞過驗證
    query = "/users/user[name/text()='" + user + "' and password/text()='" + password + "']"
    results = xml.xpath(query)
    return results


# ============================================================
# CWE-760: Predictable Salt (使用可預測鹽值)
# ============================================================
def cwe_760_predictable_salt():
    """漏洞代碼：Salt 是硬編碼的固定值"""
    password = "user_password"
    # 容易遭受彩虹表攻擊
    salt = "fixed_salt_value"
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed


# ============================================================
# CWE-918: Server-Side Request Forgery (SSRF)
# ============================================================
import requests

@app.route('/proxy')
def cwe_918_ssrf():
    """漏洞代碼：直接存取使用者提供的 URL"""
    url = request.args.get('url')
    # 攻擊者可存取內部服務，例如 "http://169.254.169.254/latest/meta-data/"
    return requests.get(url).content


# ============================================================
# CWE-943: NoSQL Injection (NoSQL 注入)
# ============================================================
from pymongo import MongoClient

client = MongoClient()
db = client.db

def cwe_943_nosql_injection(username, password):
    """漏洞代碼：直接將使用者輸入作為查詢條件"""
    # 若攻擊者傳送 password 為 {"$ne": null}，則可繞過密碼檢查
    user = db.users.find_one({"username": username, "password": password})
    return user


# ============================================================
# CWE-1333: Regular Expression DoS (ReDoS)
# ============================================================
import re

def cwe_1333_redos(user_input):
    """漏洞代碼：巢狀量詞導致災難性回溯"""
    # 攻擊者輸入 "aaaaaaaaaaaaaaaaaaaaX" 可能導致 DoS
    pattern = re.compile(r"(a+)+b")
    match = pattern.match(user_input)
    return match
