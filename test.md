### 1. CWE-022: Path Traversal (路徑遍歷)
**說明**：在處理檔案下載或讀取時，未限制路徑範圍。
```python
import os
from flask import request

def download_file():
    # 漏洞：假設使用者輸入 filename 為 "../../etc/passwd"
    filename = request.args.get('file')
    
    # 雖然用了 abspath，但沒有檢查是否跑出了預期的 base_dir
    file_path = os.path.abspath(os.path.join('static/images', filename))
    
    with open(file_path, 'rb') as f:
        return f.read()
```

### 2. CWE-078: OS Command Injection (作業系統指令注入)
**說明**：使用 `subprocess` 時啟用了 `shell=True` 並串接字串。
```python
import subprocess

def backup_website(url):
    # 漏洞：如果 url 是 "google.com; rm -rf /"，將執行刪除指令
    # shell=True 允許執行 Shell 語法（如分號、管道）
    command = f"wget -r {url}"
    subprocess.call(command, shell=True)
```

### 3. CWE-079: Cross-site Scripting (XSS) (跨網站指令碼)
**說明**：在 Jinja2 或其他樣板引擎中，錯誤地將不可信內容標記為安全。
```python
from flask import Markup

def render_comment(user_comment):
    # 漏洞：Markup() 告訴框架這串字串是安全的，不需要轉義(Escape)
    # 如果 user_comment 包含 "<script>...</script>"，將被瀏覽器執行
    return Markup(f"<div>User said: {user_comment}</div>")
```

### 4. CWE-095: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')
**說明**：使用 `exec()` 動態執行 Python 語句。
```python
def configure_app(config_str):
    # 漏洞：假設 config_str 來自使用者上傳的設定檔
    # 內容若為 "__import__('os').system('id')"，將執行系統指令
    exec(config_str)
```

### 5. CWE-113: Improper Neutralization of CRLF Sequences in HTTP Headers ('HTTP Response Splitting')
**說明**：在設定 Header 時未過濾換行符號（Python 較新版本的 Web 框架通常會防禦此點，但在底層實作仍可能發生）。
```python
from http.server import BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 假設從 query string 取得參數
        redirect_url = self.path.split('=')[-1]
        
        self.send_response(302)
        # 漏洞：若 redirect_url 包含 "%0d%0aSet-Cookie: session=admin"
        # 可能導致 Header Injection
        self.send_header('Location', redirect_url)
        self.end_headers()
```

### 6. CWE-117: Improper Output Neutralization for Logs (日誌注入)
**說明**：在 Web 應用程式日誌中直接寫入未過濾的例外訊息。
```python
import logging

def process_payment(user_id):
    try:
        # ... 處理邏輯 ...
        raise ValueError("Invalid input")
    except Exception as e:
        # 漏洞：如果攻擊者能控制錯誤訊息的內容（例如透過構造惡意輸入觸發特定的 Error string）
        # 他們可以插入換行符號來偽造日誌
        logging.error(f"Payment failed for {user_id}: {e}")
```

### 7. CWE-326: Inadequate Encryption Strength (加密強度不足)
**說明**：使用位元數過低的 DSA 金鑰。
```python
from Crypto.PublicKey import DSA

def generate_dsa_key():
    # 漏洞：1024 位元的 DSA 金鑰在現代已被視為不夠安全
    # 建議至少使用 2048 位元
    key = DSA.generate(1024)
    return key
```

### 8. CWE-327: Use of a Broken or Risky Cryptographic Algorithm (使用已破解或風險的加密演算法)
**說明**：使用 SHA-1 進行數位簽章或雜湊（SHA-1 已發生碰撞攻擊）。
```python
import hashlib

def get_file_hash(data):
    # 漏洞：SHA1 已不再安全，不應在新系統中使用
    m = hashlib.sha1()
    m.update(data)
    return m.hexdigest()
```

### 9. CWE-329: Generation of Predictable IV with CBC Mode (CBC 模式使用可預測的初始化向量)
**說明**：使用時間戳記作為 IV，這對攻擊者來說是可預測的。
```python
import time
from Crypto.Cipher import AES

def encrypt_data(key, data):
    # 漏洞：IV 必須是密碼學安全的隨機數
    # 使用時間戳記當 IV 是可預測的
    iv = str(int(time.time())).ljust(16)[:16].encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(data)
```

### 10. CWE-347: Improper Verification of Cryptographic Signature (未驗證加密簽章)
**說明**：使用 `PyJWT` 解碼 Token 時顯式跳過驗證。
```python
import jwt

def get_user_info(token):
    # 漏洞：verify=False 表示完全信任 Token 內容而不檢查簽名
    # 攻擊者可以隨意修改 Payload (例如把 role 改成 admin)
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload
```

### 11. CWE-377: Insecure Temporary File (不安全的暫存檔)
**說明**：使用已棄用的 `mktemp()` 函式。
```python
import tempfile

def save_temp_data(data):
    # 漏洞：mktemp 僅回傳一個檔名，不建立檔案
    # 在回傳檔名到真正開啟寫入這段時間，攻擊者可能在該路徑建立檔案 (Race Condition)
    path = tempfile.mktemp()
    with open(path, 'w') as f:
        f.write(data)
```

### 12. CWE-502: Deserialization of Untrusted Data (反序列化不可信資料)
**說明**：使用 `PyYAML` 的不安全載入器解析 YAML。
```python
import yaml

def load_config(yaml_content):
    # 漏洞：PyYAML 的 yaml.load 預設（舊版）或未指定 Loader 時可能執行任意 Python 程式碼
    # 攻擊者可傳入 "!!python/object/apply:os.system ['rm -rf /']"
    config = yaml.load(yaml_content, Loader=yaml.Loader)
    return config
```

### 13. CWE-643: Improper Neutralization of Data within XPath Expressions ('XPath Injection')
**說明**：使用 `lxml` 進行字串拼接查詢。
```python
from lxml import etree

def find_user(xml_data, username):
    root = etree.fromstring(xml_data)
    # 漏洞：XPath 注入
    # 若 username 為 "admin' or '1'='1"，將回傳錯誤的節點
    users = root.xpath(f"/users/user[@name='{username}']")
    return users
```

### 14. CWE-760: Use of a One-Way Hash with a Predictable Salt (使用可預測鹽值的單向雜湊)
**說明**：在密碼雜湊時，重複使用使用者帳號作為 Salt。
```python
import hashlib

def store_password(email, password):
    # 漏洞：Salt 應該是隨機生成的
    # 使用 email 作為 salt 讓攻擊者可以針對已知 email 預先計算雜湊（彩虹表攻擊）
    salt = email.encode()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return dk
```

### 15. CWE-918: Server-Side Request Forgery (SSRF) (伺服器端請求偽造)
**說明**：使用標準函式庫 `urllib` 存取使用者提供的 URL。
```python
import urllib.request

def fetch_avatar(image_url):
    # 漏洞：未檢查 image_url 的協定與目標
    # 攻擊者可輸入 "file:///etc/passwd" 或內部服務網址 "http://localhost:6379"
    with urllib.request.urlopen(image_url) as response:
        return response.read()
```

### 16. CWE-943: Improper Neutralization of Special Elements in Data Query Logic ('NoSQL Injection')
**說明**：在 Flask 應用中直接將 JSON 輸入傳遞給 MongoDB 查詢。
```python
# 假設使用 flask_pymongo
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
```

### 17. CWE-1333: Inefficient Regular Expression Complexity (ReDoS)
**說明**：使用容易造成災難性回溯（Catastrophic Backtracking）的正規表達式。
```python
import re

def validate_input(user_input):
    # 漏洞：(a+)+ 這種巢狀量詞結構非常危險
    # 攻擊者輸入 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX" 會導致運算時間指數級上升
    pattern = re.compile(r"^(([a-z])+.)+[A-Z]([a-z])+$")
    
    if pattern.match(user_input):
        return True
    return False
```