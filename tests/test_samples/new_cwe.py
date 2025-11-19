# vuln_samples.py
# 範例檔案：每個函式都有一個容易被安全掃描器判為對應 CWE 的不安全用法
# 注意：這些函式都**不要在生產環境執行**；檔案最後沒有呼叫任何危險函式。

SUPPORTED_CWES = [
    "022", "078", "079", "095", "113", "117",
    "326", "327", "329", "347", "377", "502",
    "643", "760", "918", "943", "1333"
]

# --------------------------------------------------------------------
# Imports that some examples use
import os
import subprocess
import hashlib
import logging
import pickle          # 不安全反序列化示範
import tempfile
import re
import sqlite3
from xml.etree import ElementTree as ET

# Optional crypto imports for examples (may not be installed in all envs)
try:
    from Crypto.Cipher import AES  # pycryptodome
except Exception:
    AES = None

# --------------------------------------------------------------------
# CWE-022: Path Traversal (不當限制路徑)
def cwe_022_path_traversal(user_path):
    """
    直接用使用者輸入拼接路徑，沒有正規化或檢查 ../ 等特殊元素。
    靜態掃描器會標示出 path join / open 時未驗證路徑。
    """
    base = "/var/app/data"
    target = os.path.join(base, user_path)  # vulnerable: 不做 normpath / 檢查
    # Vulnerable file open (示範用，不要呼叫)
    with open(target, "r") as f:
        return f.read()


# --------------------------------------------------------------------
# CWE-078: OS Command Injection
def cwe_078_os_cmd_injection(user_input):
    """
    使用 shell=True 並把未過濾的使用者輸入放進命令字串 -> OS command injection
    """
    cmd = f"ls -la {user_input}"  # vulnerable: 未做 shell escaping / validation
    subprocess.call(cmd, shell=True)  # <- 不要實際執行；只是為了讓掃描器標出來
    return cmd


# --------------------------------------------------------------------
# CWE-079: Cross-Site Scripting (XSS)
def cwe_079_xss(user_html_fragment):
    """
    將未編碼的使用者輸入直接插入 HTML 回應 -> XSS (reflected / stored)
    """
    # 假設這會直接回傳給使用者的 HTML
    html = f"<html><body>Welcome, {user_html_fragment}</body></html>"
    return html


# --------------------------------------------------------------------
# CWE-095: Eval/Code Injection (動態評估指令)
def cwe_095_eval_injection(user_code):
    """
    直接 eval 未經淨化的輸入 -> Eval injection
    """
    result = eval(user_code)  # 不要執行；示範不安全模式
    return f"eval({user_code})  # 示範危險寫法"


# --------------------------------------------------------------------
# CWE-113: HTTP Response Splitting / header CRLF injection
def cwe_113_response_splitting(header_value):
    """
    將未過濾的字串放到 HTTP header 中，若含 CRLF 可能造成 response splitting
    """
    # 示範用的 raw header 建構
    raw_header = "Set-Cookie: session=" + header_value + "\r\n"
    # 實際 web framework 中若直接將 raw_header 寫入 response 會有問題
    return raw_header


# --------------------------------------------------------------------
# CWE-117: Improper Output Neutralization for Logs (log injection)
def cwe_117_log_injection(user_input):
    """
    直接把原始使用者輸入寫入 log（可能包含 CRLF，偽造或干擾日誌）
    """
    logger = logging.getLogger("vuln_example")
    logger.setLevel(logging.DEBUG)
    # 下面直接寫入未淨化的使用者輸入
    logger.info("User action: %s", user_input)  # 可能導致 log injection


# --------------------------------------------------------------------
# CWE-326 / CWE-327: 不足或已破壞的加密演算法
def cwe_326_327_weak_hash(password):
    """
    使用 MD5 / SHA1 等已被視為弱或不適合的雜湊演算法來處理密碼或簽章
    """
    md5 = hashlib.md5(password.encode()).hexdigest()   # CWE-327 範例（破損/風險演算法）
    sha1 = hashlib.sha1(password.encode()).hexdigest() # 同為弱雜湊示範
    return md5, sha1


# --------------------------------------------------------------------
# CWE-329: Generation of Predictable IV with CBC Mode
def cwe_329_predictable_iv(key, plaintext):
    """
    在 CBC 模式下使用可預測/固定 IV（如全 0） -> 可被檢出為弱加密實踐
    需要 pycryptodome 才能實際執行；此範例以示範為主，靜態掃描器可標示出 IV 的固定值。
    """
    if AES is None:
        return "AES module not available - illustrative function"
    iv = b"\x00" * 16   # **可預測的 IV**（示範危險）
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    # 注意：未處理 padding 等，這只是示範
    ct = cipher.encrypt(plaintext)
    return ct


# --------------------------------------------------------------------
# CWE-347: Improper Verification of Cryptographic Signature
def cwe_347_bad_sig_verify(message, signature, pubkey=None):
    """
    範例：未正確驗證簽章，甚至直接跳過驗證或用不安全的比較方式（示範）
    """
    # 錯誤做法範例：只要 signature 存在就相信
    if signature:
        return True  # 不做實際驗證 -> vulnerable
    return False


# --------------------------------------------------------------------
# CWE-377: Insecure Temporary File
def cwe_377_insecure_tempfile(data):
    """
    使用過時/不安全的 tempfile.mktemp() 或 predictable tempfile name -> race condition / TOCTTOU
    """
    tmp_name = tempfile.mktemp()  # mktemp() is insecure and deprecated
    with open(tmp_name, "w") as f:
        f.write(data)
    return tmp_name


# --------------------------------------------------------------------
# CWE-502: Deserialization of Untrusted Data
def cwe_502_insecure_deserialize(serialized_blob):
    """
    直接用 pickle.loads() 反序列化未經信任的輸入 -> 任意程式碼執行風險
    """
    obj = pickle.loads(serialized_blob)  # 不要在不信任資料上執行
    return "pickle.loads(...)  # 示範不安全反序列化"


# --------------------------------------------------------------------
# CWE-643: XPath Injection
def cwe_643_xpath_injection(user_query):
    """
    使用者內容直接拼入 XPath 查詢 -> XPath injection
    """
    xml_data = """
    <users>
      <user><name>alice</name></user>
      <user><name>bob</name></user>
    </users>
    """
    root = ET.fromstring(xml_data)
    # vulnerable: 直接把 user_query 串進 xpath
    xpath_expr = f".//user[name='{user_query}']"
    results = root.findall(xpath_expr)  # 靜態示範，不執行
    return xpath_expr


# --------------------------------------------------------------------
# CWE-760: Use of a One-Way Hash with a Predictable Salt
def cwe_760_predictable_salt(password):
    """
    使用固定/可預測的 salt 來 hash 密碼 -> 易受彩虹表/字典攻擊
    """
    predictable_salt = b"STATIC_SALT"
    derived = hashlib.pbkdf2_hmac('sha256', password.encode(), predictable_salt, 10000)
    return derived.hex()


# --------------------------------------------------------------------
# CWE-918: Server-Side Request Forgery (SSRF)
def cwe_918_ssrf(user_url):
    """
    伺服器接受一個 URL 並代表伺服器向該 URL 發出請求（未檢查目標是否為內部資源）-> SSRF
    """
    # 不要實際發送請求；這邊只是示範組合
    import requests
    resp = requests.get(user_url, timeout=3)  # 可能造成 SSRF
    return f"requests.get({user_url})  # 示範 SSRF 情境"


# --------------------------------------------------------------------
# CWE-943: Improper Neutralization of Special Elements in Data Query Logic (Query Injection)
def cwe_943_query_injection(username):
    """
    以字串拼接方式產生 SQL 查詢 -> SQL injection / query-injection
    """
    conn = sqlite3.connect(":memory:")
    # vulnerable: 直接拼接 username 到 SQL
    query = f"SELECT * FROM users WHERE username = '{username}';"
    cur = conn.cursor()
    cur.execute(query)  # 示範：不要在不信任的輸入上執行
    return query


# --------------------------------------------------------------------
# CWE-1333: Inefficient Regular Expression Complexity (ReDoS)
def cwe_1333_regex_dos(user_input):
    """
    使用具有指數級複雜度的正則 (例如 (a+)+) 並把使用者輸入套用 -> 可能引起 CPU 耗盡
    """
    bad_pattern = re.compile(r'^(a+)+$')  # 很容易造成 catastrophic backtracking
    m = bad_pattern.match(user_input)  # 不要在未受限的長度上執行
    return bad_pattern.pattern


# --------------------------------------------------------------------
# 注意：下列所有危險函式都**不在此檔案被呼叫**。掃描器應以靜態分析或動態掃描（在受控環境）來檢測這些模式。
if __name__ == "__main__":
    print("vuln_samples 模組載入。請勿在生產環境執行示範中的危險函式。")
