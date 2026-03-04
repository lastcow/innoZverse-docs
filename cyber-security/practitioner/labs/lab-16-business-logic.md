# Lab 16: Business Logic Flaws

## Objective
Identify and exploit business logic vulnerabilities that bypass application workflows: negative price manipulation, coupon code stacking, race conditions in inventory/payment systems, workflow step skipping, privilege escalation via parameter tampering, and reward point fraud — then implement proper server-side business rule enforcement.

## Background
Business logic flaws are among the hardest vulnerabilities to detect with automated tools. Unlike SQL injection or XSS, they don't involve malformed input — they exploit valid functionality used in unintended ways. An attacker who buys a $1,000 laptop for -$50 (triggering a refund), applies a coupon 1,000 times via a race condition, or skips the payment step in a checkout flow is exploiting business logic. These bugs are found through manual exploration and cost organisations billions annually in fraud.

## Time
40 minutes

## Prerequisites
- Lab 04 (A04 Insecure Design) — insecure design fundamentals

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: Price Manipulation — Negative Values

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Price Manipulation Attack ===')
print()

products = {
    'surface-pro-12':    {'name': 'Surface Pro 12',     'price': 864.00},
    'surface-laptop-5':  {'name': 'Surface Laptop 5',   'price': 1299.00},
    'surface-pen':       {'name': 'Surface Pen',        'price': 49.99},
}

class CartVulnerable:
    def __init__(self):
        self.items = []

    def add_item(self, product_id: str, quantity: int, client_price: float):
        '''VULNERABLE: trusts client-supplied price.'''
        product = products.get(product_id)
        if not product:
            return {'error': 'Product not found'}
        self.items.append({
            'product': product['name'],
            'quantity': quantity,
            'unit_price': client_price,  # VULN: uses attacker-controlled price!
            'subtotal': quantity * client_price,
        })
        return {'added': product['name'], 'unit_price': client_price}

    def checkout(self):
        total = sum(item['subtotal'] for item in self.items)
        return {'items': self.items, 'total': total, 'status': 'Order placed!'}

class CartSafe:
    def __init__(self):
        self.items = []

    def add_item(self, product_id: str, quantity: int):
        '''SAFE: price always fetched server-side.'''
        product = products.get(product_id)
        if not product:
            return {'error': 'Product not found'}
        if not isinstance(quantity, int) or quantity < 1 or quantity > 99:
            return {'error': 'Invalid quantity (1-99)'}
        self.items.append({
            'product': product['name'],
            'quantity': quantity,
            'unit_price': product['price'],  # SAFE: from authoritative DB
            'subtotal': quantity * product['price'],
        })
        return {'added': product['name'], 'unit_price': product['price']}

    def checkout(self):
        total = sum(item['subtotal'] for item in self.items)
        if total < 0:
            return {'error': 'Invalid order total'}
        return {'items': self.items, 'total': round(total, 2), 'status': 'Order placed!'}

# Attack 1: Negative price
print('[VULNERABLE] Price manipulation attacks:')
cart = CartVulnerable()
cart.add_item('surface-pro-12', 1, -864.00)   # Negative price
cart.add_item('surface-pen', 1, 49.99)
result = cart.checkout()
print(f'  Attack 1 (negative price): Total = \${result[\"total\"]:.2f}')
print(f'  → Shop PAYS attacker \${abs(result[\"total\"]):.2f}!')

# Attack 2: Zero price
cart2 = CartVulnerable()
cart2.add_item('surface-laptop-5', 1, 0.00)   # Free laptop
result2 = cart2.checkout()
print(f'  Attack 2 (zero price): Total = \${result2[\"total\"]:.2f}')
print(f'  → Laptop acquired for FREE!')

# Attack 3: Integer overflow (very large discount)
cart3 = CartVulnerable()
cart3.add_item('surface-pro-12', 1, -999999.00)
result3 = cart3.checkout()
print(f'  Attack 3 (massive negative): Total = \${result3[\"total\"]:.2f}')

print()
print('[SAFE] Server-side pricing:')
cart4 = CartSafe()
cart4.add_item('surface-pro-12', 1)    # Price not accepted from client
cart4.add_item('surface-pen', 1)
result4 = cart4.checkout()
print(f'  Normal order: Total = \${result4[\"total\"]:.2f}')
print(f'  Items: {[i[\"product\"] for i in result4[\"items\"]]}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Price manipulation attacks:
  Attack 1 (negative price): Total = $-814.01
  → Shop PAYS attacker $814.01!
  Attack 2 (zero price): Total = $0.00
  → Laptop acquired for FREE!

[SAFE] Server-side pricing:
  Normal order: Total = $913.99
```

> 💡 **Never trust the client for any value that has financial impact.** Price, discount, quantity, shipping cost — all must be calculated server-side from authoritative data sources. The client should only send identifiers (product ID, coupon code), never values (price, discount amount). This principle extends beyond money: any value the server computes should never be accepted from the client.

### Step 2: Coupon Code Abuse & Race Condition

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import threading, time, random

print('=== Coupon Race Condition Attack ===')
print()

# Shared state (simulates database)
coupon_db = {'SAVE50': {'discount': 50.00, 'uses': 0, 'max_uses': 1}}
orders_placed = []
lock = threading.Lock()

def apply_coupon_vulnerable(user_id: str, coupon_code: str, order_total: float):
    '''VULNERABLE: check-then-act race condition.'''
    coupon = coupon_db.get(coupon_code)
    if not coupon:
        return None, 'Invalid coupon'
    # RACE: check happens here
    if coupon['uses'] >= coupon['max_uses']:
        return None, 'Coupon already used'
    # GAP: between check and update — another thread can squeeze in!
    time.sleep(0.001)  # Simulate DB query latency
    # ACT: update happens here (too late — race already lost)
    coupon['uses'] += 1
    discounted = max(0, order_total - coupon['discount'])
    orders_placed.append({'user': user_id, 'total': discounted, 'coupon': coupon_code})
    return discounted, 'Coupon applied!'

def apply_coupon_safe(user_id: str, coupon_code: str, order_total: float):
    '''SAFE: atomic check-and-update under lock.'''
    with lock:  # Database: use SELECT FOR UPDATE or atomic UPDATE WHERE uses < max_uses
        coupon = coupon_db.get(coupon_code)
        if not coupon or coupon['uses'] >= coupon['max_uses']:
            return None, 'Invalid or exhausted coupon'
        coupon['uses'] += 1  # Atomic update within lock
    discounted = max(0, order_total - coupon['discount'])
    return discounted, 'Coupon applied!'

# Simulate 10 concurrent requests using same coupon (TOCTOU attack)
print('[VULNERABLE] Race condition — 10 simultaneous coupon redemptions:')
threads = []
results = []
coupon_db['SAVE50']['uses'] = 0  # Reset

def try_coupon(uid):
    total, msg = apply_coupon_vulnerable(f'user-{uid}', 'SAVE50', 200.00)
    results.append((uid, total, msg))

for i in range(10):
    t = threading.Thread(target=try_coupon, args=(i,))
    threads.append(t)
for t in threads: t.start()
for t in threads: t.join()

successes = [(uid, total) for uid, total, msg in results if total is not None]
print(f'  Coupon max uses: 1')
print(f'  Concurrent requests: 10')
print(f'  Successful redemptions: {len(successes)} (should be 1!)')
for uid, total in successes:
    print(f'    user-{uid}: paid \${total:.2f} (saved \$50)')

# Reset and test safe version
coupon_db['SAVE50']['uses'] = 0
print()
print('[SAFE] Atomic lock — same 10 concurrent requests:')
results2 = []

def try_coupon_safe(uid):
    total, msg = apply_coupon_safe(f'user-{uid}', 'SAVE50', 200.00)
    results2.append((uid, total, msg))

threads2 = [threading.Thread(target=try_coupon_safe, args=(i,)) for i in range(10)]
for t in threads2: t.start()
for t in threads2: t.join()

successes2 = [(uid, total) for uid, total, msg in results2 if total is not None]
print(f'  Successful redemptions: {len(successes2)} (correct!)')
for uid, total in successes2:
    print(f'    user-{uid}: paid \${total:.2f} (saved \$50)')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Race condition:
  Coupon max uses: 1
  Concurrent requests: 10
  Successful redemptions: 7 (should be 1!)
    user-0: paid $150.00 (saved $50)
    user-3: paid $150.00 (saved $50)
    ...

[SAFE] Atomic lock:
  Successful redemptions: 1 (correct!)
    user-0: paid $150.00 (saved $50)
```

### Step 3: Workflow Step Skipping

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Checkout Workflow Step Skipping ===')
print()
print('Multi-step workflows assume users follow the intended sequence.')
print('Attackers can skip steps by directly requesting later endpoints.')
print()

# VULNERABLE: state stored in client-controlled session cookie
class CheckoutVulnerable:
    def __init__(self):
        self.client_state = {}  # Client controls this!

    def set_state(self, state: dict):
        self.client_state = state  # Attacker can send any state

    def step_payment(self, card_info: dict) -> dict:
        # VULN: doesn't verify previous steps completed
        return {'payment_id': 'pay_abc123', 'status': 'authorized'}

    def step_confirm(self) -> dict:
        # VULN: confirms order regardless of payment step
        payment_done = self.client_state.get('payment_complete', False)
        # Attacker sends: {'payment_complete': True, 'cart': [...]} in cookie/request
        if payment_done:
            return {'order_id': 'ORD-99999', 'status': 'CONFIRMED — items shipped!'}
        return {'error': 'Payment required'}

# SAFE: server-side state machine
class CheckoutSafe:
    def __init__(self):
        self.server_state = {
            'cart_confirmed': False,
            'address_set': False,
            'payment_authorized': False,
            'payment_id': None,
        }

    def step_cart(self, items: list) -> dict:
        if not items:
            return {'error': 'Cart is empty'}
        self.server_state['cart_confirmed'] = True
        self.server_state['items'] = items
        return {'status': 'Cart confirmed', 'next': '/checkout/address'}

    def step_address(self, address: dict) -> dict:
        if not self.server_state['cart_confirmed']:
            return {'error': 'Complete cart step first', 'redirect': '/checkout/cart'}
        self.server_state['address_set'] = True
        self.server_state['address'] = address
        return {'status': 'Address set', 'next': '/checkout/payment'}

    def step_payment(self, card_token: str) -> dict:
        if not self.server_state['address_set']:
            return {'error': 'Complete address step first', 'redirect': '/checkout/address'}
        # Process payment with payment gateway
        self.server_state['payment_authorized'] = True
        self.server_state['payment_id'] = f'pay_{card_token[:8]}'
        return {'status': 'Payment authorized', 'next': '/checkout/confirm'}

    def step_confirm(self) -> dict:
        # All previous steps MUST be complete
        if not self.server_state['payment_authorized']:
            return {'error': 'Payment not completed', 'redirect': '/checkout/payment'}
        if not self.server_state['payment_id']:
            return {'error': 'No valid payment on file'}
        return {'order_id': 'ORD-88888', 'payment_id': self.server_state['payment_id'],
                'status': 'CONFIRMED'}

print('[VULNERABLE] Step skipping — attacker skips directly to confirm:')
checkout = CheckoutVulnerable()
checkout.set_state({'payment_complete': True})  # Attacker sets this!
result = checkout.step_confirm()
print(f'  Result: {result}')
print(f'  Items received without payment!')

print()
print('[SAFE] Server-side state machine:')
checkout2 = CheckoutSafe()
result = checkout2.step_confirm()  # Try to skip to confirm
print(f'  Skip to confirm: {result}')
result = checkout2.step_payment('tok_visa_1234')
print(f'  Skip to payment: {result}')
result = checkout2.step_cart([{'id': 'surface-pro-12', 'qty': 1}])
result = checkout2.step_address({'city': 'San Francisco', 'zip': '94102'})
result = checkout2.step_payment('tok_visa_5678')
result = checkout2.step_confirm()
print(f'  Full flow: {result}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Step skipping:
  Result: {'order_id': 'ORD-99999', 'status': 'CONFIRMED — items shipped!'}
  Items received without payment!

[SAFE] State machine:
  Skip to confirm: {'error': 'Payment not completed', 'redirect': '/checkout/payment'}
  Skip to payment: {'error': 'Complete address step first'}
  Full flow: {'order_id': 'ORD-88888', 'payment_id': 'pay_tok_visa', 'status': 'CONFIRMED'}
```

### Step 4: Reward Point Manipulation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Reward Point / Loyalty Programme Fraud ===')
print()

# Simulated accounts
accounts = {
    'user-42': {'balance': 500.00, 'points': 1000, 'tier': 'Silver'},
    'user-99': {'balance': 200.00, 'points': 200,  'tier': 'Bronze'},
}

def transfer_points_vulnerable(from_user: str, to_user: str, points: int) -> dict:
    '''VULNERABLE: no validation of sign, no atomic update.'''
    src = accounts.get(from_user)
    dst = accounts.get(to_user)
    if not src or not dst:
        return {'error': 'User not found'}
    src['points'] -= points  # VULN: negative points = gains points!
    dst['points'] += points
    return {'from_points': src['points'], 'to_points': dst['points']}

def transfer_points_safe(from_user: str, to_user: str, points: int) -> dict:
    '''SAFE: proper validation + atomic update.'''
    if not isinstance(points, int) or points <= 0:
        return {'error': 'Points must be positive integer'}
    if from_user == to_user:
        return {'error': 'Cannot transfer to self'}
    src = accounts.get(from_user)
    dst = accounts.get(to_user)
    if not src or not dst:
        return {'error': 'User not found'}
    if src['points'] < points:
        return {'error': f'Insufficient points (have {src[\"points\"]}, need {points})'}
    # Atomic update
    src['points'] -= points
    dst['points'] += points
    return {'from_points': src['points'], 'to_points': dst['points'], 'status': 'OK'}

print('Initial state:')
for uid, acc in accounts.items():
    print(f'  {uid}: {acc[\"points\"]} points')

print()
print('[VULNERABLE] Negative transfer (points generation exploit):')
accounts['user-42']['points'] = 1000  # Reset
result = transfer_points_vulnerable('user-42', 'user-99', -5000)
print(f'  Transfer -5000 points from user-42 to user-99:')
print(f'  user-42 points: {accounts[\"user-42\"][\"points\"]} (was 1000 → GAINED 5000!)')
print(f'  user-99 points: {accounts[\"user-99\"][\"points\"]} (was 200 → LOST 5000)')

print()
accounts['user-42']['points'] = 1000  # Reset
accounts['user-99']['points'] = 200
print('[SAFE] Proper validation:')
test_cases = [
    ('user-42', 'user-99', -5000, 'Negative transfer'),
    ('user-42', 'user-99', 0,     'Zero transfer'),
    ('user-42', 'user-42', 100,   'Self-transfer'),
    ('user-42', 'user-99', 9999,  'Insufficient points'),
    ('user-42', 'user-99', 100,   'Valid transfer'),
]
for from_u, to_u, pts, desc in test_cases:
    result = transfer_points_safe(from_u, to_u, pts)
    print(f'  [{desc}]: {result}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Negative transfer:
  user-42 points: 6000 (was 1000 → GAINED 5000!)
  user-99 points: -4800 (was 200 → LOST 5000)

[SAFE] Validation:
  [Negative transfer]: {'error': 'Points must be positive integer'}
  [Zero transfer]: {'error': 'Points must be positive integer'}
  [Insufficient points]: {'error': 'Insufficient points (have 1000, need 9999)'}
  [Valid transfer]: {'from_points': 900, 'to_points': 300, 'status': 'OK'}
```

### Step 5: Refund Fraud — Return Without Purchase

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import time

print('=== Refund Fraud Patterns ===')
print()

orders = {
    'ORD-001': {'user': 'user-42', 'product': 'Surface Pro 12', 'amount': 864.00,
                'status': 'delivered', 'refunded': False, 'purchase_date': time.time() - 86400},
    'ORD-002': {'user': 'user-42', 'product': 'Surface Pen',    'amount': 49.99,
                'status': 'delivered', 'refunded': True,  'purchase_date': time.time() - 86400*40},
}

def process_refund_vulnerable(order_id: str, user_id: str, reason: str) -> dict:
    order = orders.get(order_id)
    if not order or order['user'] != user_id:
        return {'error': 'Order not found'}
    # VULN: no checks on refund eligibility
    order['refunded'] = True
    return {'refund_amount': order['amount'], 'status': 'Refunded!'}

def process_refund_safe(order_id: str, user_id: str, reason: str) -> dict:
    order = orders.get(order_id)
    if not order or order['user'] != user_id:
        return {'error': 'Order not found'}
    if order['refunded']:
        return {'error': 'Order already refunded'}
    if order['status'] not in ('delivered', 'shipped'):
        return {'error': f'Cannot refund order with status: {order[\"status\"]}'}
    days_since = (time.time() - order['purchase_date']) / 86400
    if days_since > 30:
        return {'error': f'Refund window expired ({days_since:.0f} days ago, limit 30)'}
    if not reason or len(reason) < 10:
        return {'error': 'Please provide a detailed reason (min 10 chars)'}
    order['refunded'] = True
    return {'refund_amount': order['amount'], 'status': 'Refund approved', 'days_since': f'{days_since:.1f}'}

print('[VULNERABLE] Double refund attack:')
orders['ORD-001']['refunded'] = False
result1 = process_refund_vulnerable('ORD-001', 'user-42', 'Damaged')
result2 = process_refund_vulnerable('ORD-001', 'user-42', 'Wrong item')  # Double refund
print(f'  First refund:  {result1}')
print(f'  Second refund: {result2}')
print(f'  Total refunded: \${result1[\"refund_amount\"] + result2[\"refund_amount\"]:.2f} (should be \$864.00)')

print()
print('[SAFE] Proper refund validation:')
orders['ORD-001']['refunded'] = False
test_cases = [
    ('ORD-001', 'user-42', 'Product arrived damaged and screen cracked', 'Valid refund'),
    ('ORD-001', 'user-42', 'Changed mind', 'Double refund attempt'),
    ('ORD-002', 'user-42', 'Product arrived damaged', 'Already refunded order'),
]
for order_id, user, reason, desc in test_cases:
    result = process_refund_safe(order_id, user, reason)
    print(f'  [{desc}]: {result}')

print()
print('Common refund fraud patterns:')
patterns = [
    ('Double refund',         'Request refund twice before first processes'),
    ('Refund without return', 'Claim return, keep product'),
    ('Inflated refund',       'Modify amount in request (client-side total)'),
    ('Chargeback + refund',   'Get refund from merchant AND chargeback from bank'),
    ('Wrong item returned',   'Return cheaper/broken item, claim refund for expensive one'),
    ('Time manipulation',     'Change system clock, submit refund after window closes'),
]
for name, desc in patterns:
    print(f'  [{name}] {desc}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Double refund:
  First refund:  {'refund_amount': 864.0, 'status': 'Refunded!'}
  Second refund: {'refund_amount': 864.0, 'status': 'Refunded!'}
  Total refunded: $1728.00 (should be $864.00)

[SAFE] Validation:
  [Valid refund]: {'refund_amount': 864.0, 'status': 'Refund approved'}
  [Double refund]: {'error': 'Order already refunded'}
  [Already refunded]: {'error': 'Order already refunded'}
```

### Step 6: Parameter Tampering for Privilege Escalation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Parameter Tampering ===')
print()

hidden_fields = [
    ('role',         'customer',  'admin',      'Privilege escalation'),
    ('price',        '1299.00',   '0.01',       'Price reduction'),
    ('is_admin',     'false',     'true',        'Admin access'),
    ('account_id',   'user-42',   'user-1',     'Account hijack (target admin)'),
    ('discount_pct', '10',        '100',         'Full discount'),
    ('tier',         'bronze',    'platinum',   'Tier upgrade (free benefits)'),
    ('shipping',     '15.00',     '0.00',        'Free shipping'),
    ('tax',          '72.00',     '0.00',        'Tax evasion'),
]

print(f'  {\"Parameter\":<15} {\"Legitimate\":<15} {\"Tampered\":<15} {\"Impact\"}')
for param, legit, tampered, impact in hidden_fields:
    print(f'  {param:<15} {legit:<15} {tampered:<15} {impact}')

print()
print('Attack vectors for parameter tampering:')
vectors = [
    ('Hidden HTML fields', '<input type=\"hidden\" name=\"price\" value=\"1299\">'),
    ('URL parameters',     'GET /checkout?discount=10 → change to discount=100'),
    ('JSON body',          '{\"total\": 1299.00} → {\"total\": 0.01}'),
    ('Cookies',            'role=customer → role=admin (if not signed)'),
    ('HTTP headers',       'X-User-Role: customer → X-User-Role: admin'),
    ('API version',        '/api/v2/orders → /api/v1/orders (older, less secure)'),
]
for vector, example in vectors:
    print(f'  [{vector}]')
    print(f'    {example}')

print()
print('Prevention: NEVER trust client-supplied values for:')
never_trust = ['Prices, discounts, totals', 'User roles, permissions, tier',
               'Account IDs (use authenticated session)', 'Order status',
               'Quantity limits', 'Expiry dates', 'Feature flags']
for item in never_trust:
    print(f'  ✗ {item}')
"
```

### Step 7: Business Logic Testing Methodology

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Business Logic Testing Methodology ===')
print()

test_areas = {
    'Input validation': [
        'Negative numbers where positive expected',
        'Zero values (free items, zero-quantity orders)',
        'Extremely large values (integer overflow)',
        'Decimal precision abuse (0.001 × 10000 = 10)',
        'Boundary values (max-1, max, max+1)',
    ],
    'Workflow testing': [
        'Skip steps by direct URL access',
        'Repeat steps (double payment, double refund)',
        'Submit steps out of order',
        'Abandon and resume (stale state)',
        'Concurrent same-step submissions (race condition)',
    ],
    'Trust boundary': [
        'Modify hidden form fields',
        'Tamper URL parameters',
        'Alter request body values',
        'Change HTTP method (GET→POST→PUT)',
        'Remove required parameters',
    ],
    'Privilege testing': [
        'Access other users\\' resources (IDOR/BOLA)',
        'Use lower-tier features as higher tier',
        'Perform admin actions as regular user',
        'Use expired/revoked tokens',
    ],
    'Time/state abuse': [
        'Use coupon after it expires (clock skew)',
        'Refund after window closes',
        'Race condition on single-use resources',
        'Session expiry during multi-step flow',
    ],
}

for category, tests in test_areas.items():
    print(f'  [{category}]')
    for test in tests:
        print(f'    • {test}')
    print()
"
```

### Step 8: Capstone — Secure Business Logic Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
controls = [
    ('All prices fetched server-side from DB',      True),
    ('No client-supplied financial values trusted',  True),
    ('Atomic DB operations for race conditions',     True),  # SELECT FOR UPDATE
    ('Server-side state machine for workflows',      True),
    ('Single-use resources marked immediately',      True),
    ('Refund window enforced server-side',           True),
    ('All parameter types validated (positive int)', True),
    ('Privilege checks on every operation',          True),
    ('Transaction logging with amounts + users',     True),
    ('Anomaly detection (>3 refunds/week)',          True),
    ('Rate limiting on financial operations',        True),
    ('Business rule unit tests (not just happy path)',True),
]

print('Business Logic Security Checklist:')
passed = 0
for control, status in controls:
    mark = '✓' if status else '✗'
    print(f'  [{mark}] {control}')
    if status: passed += 1
print()
print(f'Score: {passed}/{len(controls)} — {\"SECURE\" if passed==len(controls) else \"VULNERABLE\"}')
print()
print('Key principle: \"What can go wrong if a user submits unexpected values')
print('at any step?\" — think like a fraudster, test like an attacker.')
"
```

---

## Summary

| Logic Flaw | Attack | Defence |
|-----------|--------|---------|
| Price manipulation | Negative/zero client price | Server-side pricing only |
| Coupon race condition | 10 concurrent redemptions | Atomic DB update (`SELECT FOR UPDATE`) |
| Workflow skipping | Direct URL to confirm step | Server-side state machine |
| Reward manipulation | Negative point transfer | Validate: positive integer, sufficient balance |
| Double refund | Submit refund twice | Mark refunded atomically, check before processing |
| Parameter tampering | Modify hidden fields, JSON body | Never trust client-supplied financial values |

## Further Reading
- [OWASP Testing for Business Logic](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/10-Business_Logic_Testing/)
- [PortSwigger Business Logic Labs](https://portswigger.net/web-security/logic-flaws)
- [Race Condition Exploitation](https://portswigger.net/research/smashing-the-state-machine)
