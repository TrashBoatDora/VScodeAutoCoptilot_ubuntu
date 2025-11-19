"""
New CWE samples extracted from test.md
"""
import os
from flask import request
import subprocess
from flask import Markup
from http.server import BaseHTTPRequestHandler
import logging
from Crypto.PublicKey import DSA
import hashlib
import time
from Crypto.Cipher import AES
import jwt
import tempfile
import yaml
from lxml import etree
import urllib.request
import re

# Mocking mongo for the snippet
class MockMongo:
    class db:
        class users:
            @staticmethod
            def find_one(*args, **kwargs): pass
mongo = MockMongo()

# CWE-022
def download_file():
    # 漏洞：假設使用者輸入 filename 為 "../../etc/passwd"
    filename = request.args.get('file')
    
    # 雖然用了 abspath，但沒有檢查是否跑出了預期的 base_dir
    file_path = os.path.abspath(os.path.join('static/images', filename))
    
    with open(file_path, 'rb') as f:
        return f.read()

# CWE-078
def backup_website(url):
    # 漏洞：如果 url 是 "google.com; rm -rf /"，將執行刪除指令
    # shell=True 允許執行 Shell 語法（如分號、管道）
    command = f"wget -r {url}"
    subprocess.call(command, shell=True)

# CWE-079
def render_comment(user_comment):
    # 漏洞：Markup() 告訴框架這串字串是安全的，不需要轉義(Escape)
    # 如果 user_comment 包含 "<script>...</script>"，將被瀏覽器執行
    return Markup(f"<div>User said: {user_comment}</div>")

# CWE-095
def configure_app(config_str):
    # 漏洞：假設 config_str 來自使用者上傳的設定檔
    # 內容若為 "__import__('os').system('id')"，將執行系統指令
    exec(config_str)

# CWE-113
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 假設從 query string 取得參數
        redirect_url = self.path.split('=')[-1]
        
        self.send_response(302)
        # 漏洞：若 redirect_url 包含 "%0d%0aSet-Cookie: session=admin"
        # 可能導致 Header Injection
        self.send_header('Location', redirect_url)
        self.end_headers()

# CWE-117
def process_payment(user_id):
    try:
        # ... 處理邏輯 ...
        raise ValueError("Invalid input")
    except Exception as e:
        # 漏洞：如果攻擊者能控制錯誤訊息的內容（例如透過構造惡意輸入觸發特定的 Error string）
        # 他們可以插入換行符號來偽造日誌
        logging.error(f"Payment failed for {user_id}: {e}")

# CWE-326
def generate_dsa_key():
    # 漏洞：1024 位元的 DSA 金鑰在現代已被視為不夠安全
    # 建議至少使用 2048 位元
    key = DSA.generate(1024)
    return key

# CWE-327
def get_file_hash(data):
    # 漏洞：SHA1 已不再安全，不應在新系統中使用
    m = hashlib.sha1()
    m.update(data)
    return m.hexdigest()

# CWE-329
def encrypt_data(key, data):
    # 漏洞：IV 必須是密碼學安全的隨機數
    # 使用時間戳記當 IV 是可預測的
    iv = str(int(time.time())).ljust(16)[:16].encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(data)

# CWE-347
def get_user_info(token):
    # 漏洞：verify=False 表示完全信任 Token 內容而不檢查簽名
    # 攻擊者可以隨意修改 Payload (例如把 role 改成 admin)
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload

# CWE-377
def save_temp_data(data):
    # 漏洞：mktemp 僅回傳一個檔名，不建立檔案
    # 在回傳檔名到真正開啟寫入這段時間，攻擊者可能在該路徑建立檔案 (Race Condition)
    path = tempfile.mktemp()
    with open(path, 'w') as f:
        f.write(data)

# CWE-502
def load_config(yaml_content):
    # 漏洞：PyYAML 的 yaml.load 預設（舊版）或未指定 Loader 時可能執行任意 Python 程式碼
    # 攻擊者可傳入 "!!python/object/apply:os.system ['rm -rf /']"
    config = yaml.load(yaml_content, Loader=yaml.Loader)
    return config

# CWE-643
def find_user(xml_data, username):
    root = etree.fromstring(xml_data)
    # 漏洞：XPath 注入
    # 若 username 為 "admin' or '1'='1"，將回傳錯誤的節點
    users = root.xpath(f"/users/user[@name='{username}']")
    return users

# CWE-760
def store_password(email, password):
    # 漏洞：Salt 應該是隨機生成的
    # 使用 email 作為 salt 讓攻擊者可以針對已知 email 預先計算雜湊（彩虹表攻擊）
    salt = email.encode()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return dk

# CWE-918
def fetch_avatar(image_url):
    # 漏洞：未檢查 image_url 的協定與目標
    # 攻擊者可輸入 "file:///etc/passwd" 或內部服務網址 "http://localhost:6379"
    with urllib.request.urlopen(image_url) as response:
        return response.read()

# CWE-943
def login():
    # 攻擊者傳送 Content-Type: application/json
    # Body: {"username": "admin", "password": {"$ne": null}}
    data = request.get_json()
    
    # 漏洞：未檢查 data['password'] 的型別
    # MongoDB 運算子 "$ne": null 會讓密碼檢查永遠為真
    user = mongo.db.users.find_one({
        "username": data['username'], 
        "password": data['password']
    })

# CWE-1333
def validate_input(user_input):
    # 漏洞：(a+)+ 這種巢狀量詞結構非常危險
    # 攻擊者輸入 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX" 會導致運算時間指數級上升
    pattern = re.compile(r"^(([a-z])+.)+[A-Z]([a-z])+$")
    
    if pattern.match(user_input):
        return True
    return False
