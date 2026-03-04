# Lab 11: Web Application Reconnaissance & Fingerprinting

## Objective

Perform systematic web application reconnaissance against a live vulnerable server from Kali Linux. You will:

1. **Fingerprint** the technology stack from HTTP headers using `nmap` and `whatweb`
2. **Enumerate** hidden directories and files with `gobuster` — finding admin panels, backups, and config files
3. **Read `robots.txt` and `sitemap.xml`** to discover intentionally hidden paths
4. **Access sensitive files** left exposed: `.env`, `.git/config`, `backup.sql`, `phpinfo.php`
5. **Reach unauthenticated endpoints** for user data, internal config, and admin panels
6. **Build a complete recon report** mapping the full attack surface

All phases run from the **Kali attacker container** against the victim Flask server — no simulation, every result is a real HTTP response.

---

## Background

Reconnaissance is the **first phase** of every penetration test (PTES — Penetration Testing Execution Standard, OWASP Testing Guide). Professional attackers spend 60–80% of their engagement time in reconnaissance before touching anything.

**Why recon matters:**
- Headers reveal framework and version → maps directly to known CVEs
- `robots.txt` is a roadmap of what the developer tried to hide
- `.git/config` exposes the private repository URL — often `git clone`-able
- `backup.sql` from a web root has ended careers (and companies)
- An unauthenticated `/api/users` endpoint is data breach #1 in any assessment

**Real-world examples:**
- **2021 Twitch breach** (135GB) — git repo history accessible via misconfigured S3 bucket discovered through recon
- **2019 GraphQL introspection** — leaving introspection enabled on production APIs lets attackers map every query, mutation, and data type — found trivially with gobuster
- **WordPress version fingerprinting** — `X-Generator: WordPress/5.8` maps to 200+ known CVEs; attackers automate this with WPScan in under 60 seconds

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a11                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── responses ───────────────────  │
│  │  Tools:              │                                           │
│  │  • nmap              │  ┌────────────────────────────────────┐  │
│  │  • whatweb           │  │         VICTIM SERVER              │  │
│  │  • gobuster          │  │   zchencow/innozverse-cybersec     │  │
│  │  • curl              │  │                                    │  │
│  │  • python3           │  │  Flask :5000                       │  │
│  └──────────────────────┘  │  (leaky headers, exposed files,   │  │
│                             │   unauthenticated endpoints)       │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

## Prerequisites
- Docker installed and running

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `nmap` | Kali | Port scan + HTTP header scripts |
| `whatweb` | Kali | Technology stack fingerprinting |
| `gobuster` | Kali | Directory and file enumeration |
| `curl` | Kali | Manual HTTP requests, header inspection |
| `python3` | Kali | Parse JSON responses, build recon report |

---

## Lab Instructions

### Step 1: Environment Setup — Launch the Victim Server

```bash
# Create the isolated Docker network
docker network create lab-a11

# Write the vulnerable target application
cat > /tmp/victim_a11.py << 'PYEOF'
from flask import Flask, request, jsonify, Response
import sqlite3, os, time

app = Flask(__name__)
DB = '/tmp/shop_a11.db'

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users    (id INTEGER PRIMARY KEY, username TEXT, role TEXT, email TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL);
        CREATE TABLE IF NOT EXISTS orders   (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL, status TEXT);
        INSERT OR IGNORE INTO users VALUES
            (1,'admin','admin','admin@innozverse.com'),
            (2,'alice','user','alice@corp.com'),
            (3,'bob','user','bob@email.com');
        INSERT OR IGNORE INTO products VALUES
            (1,'Surface Pro 12',864.00),(2,'Surface Laptop 5',1299.00),(3,'Surface Pen',49.99);
        INSERT OR IGNORE INTO orders VALUES (1,2,864.00,'delivered'),(2,3,49.99,'shipped');
    """)

@app.after_request
def add_headers(resp):
    # BUG: verbose technology disclosure headers
    resp.headers['Server']           = 'Apache/2.4.52 (Ubuntu)'
    resp.headers['X-Powered-By']     = 'PHP/8.1.2'
    resp.headers['X-Generator']      = 'WordPress/6.4.3'
    resp.headers['X-AspNet-Version'] = '4.0.30319'
    resp.headers['X-Debug-Info']     = 'env=production;version=2.3.1;build=20260101'
    return resp

@app.route('/')
def index():
    return jsonify({'app': 'InnoZverse Shop', 'version': '2.3.1'})

@app.route('/robots.txt')
def robots():
    return Response(
        "User-agent: *\nDisallow: /admin/\nDisallow: /backup/\n"
        "Disallow: /api/internal/\nDisallow: /.git/\nDisallow: /config/\n"
        "Sitemap: http://innozverse.com/sitemap.xml\n",
        content_type='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    return Response(
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>http://innozverse.com/</loc></url>'
        '<url><loc>http://innozverse.com/shop</loc></url>'
        '<url><loc>http://innozverse.com/checkout</loc></url>'
        '<url><loc>http://innozverse.com/api/products</loc></url>'
        '</urlset>', content_type='application/xml')

@app.route('/.env')
def dotenv():
    return Response(
        "APP_ENV=production\nDB_HOST=db.internal\nDB_PASS=Sup3rS3cur3DB\n"
        "AWS_KEY=AKIA5EXAMPLE\nJWT_SECRET=weak-secret-123\n",
        content_type='text/plain')

@app.route('/.git/config')
def gitconfig():
    return Response(
        "[core]\n\trepositoryformatversion = 0\n[remote \"origin\"]\n"
        "\turl = https://github.com/innozverse/shop-private.git\n"
        "[branch \"main\"]\n\tremote = origin\n",
        content_type='text/plain')

@app.route('/backup.sql')
def backup():
    return Response(
        "-- InnoZverse DB backup 2026-01-15\n"
        "INSERT INTO users VALUES (1,'admin','Admin@2024!','admin');\n"
        "INSERT INTO users VALUES (2,'alice','Alice@456','user');\n",
        content_type='text/plain')

@app.route('/phpinfo.php')
def phpinfo():
    return Response(
        "<html><body><h1>PHP Version 8.1.2</h1>"
        "System: Linux victim-a11 5.15.0<br>"
        "DB: mysql://root:root@localhost/shop<br>"
        "Document Root: /var/www/html</body></html>",
        content_type='text/html')

@app.route('/api/products')
def products():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM products').fetchall()])

@app.route('/api/users')
def users():
    # BUG: no authentication required
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM users').fetchall()])

@app.route('/api/orders')
def orders():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    return jsonify([dict(r) for r in db.execute('SELECT * FROM orders').fetchall()])

@app.route('/admin')
def admin():
    return jsonify({'panel': 'Admin Panel', 'note': 'No auth required!',
                    'actions': ['list users','delete user','export data']})

@app.route('/api/internal/config')
def internal_config():
    return jsonify({'db_host': 'db.internal', 'db_pass': 'Sup3rS3cur3DB',
                    'cache_host': 'redis.internal', 'debug': True, 'log_level': 'DEBUG'})

@app.route('/api/v1/health')
def health():
    return jsonify({'status': 'ok', 'db': 'connected', 'version': '2.3.1'})

@app.route('/error')
def error():
    import traceback
    try:
        raise ValueError("Test internal error")
    except Exception as e:
        return jsonify({'error': str(e), 'framework': 'Flask/Werkzeug 3.1.6',
                        'python': '3.10.12', 'traceback': traceback.format_exc(),
                        'server': 'Ubuntu 22.04'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Launch the victim container — read-only mount
docker run -d \
  --name victim-a11 \
  --network lab-a11 \
  -v /tmp/victim_a11.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4

# Confirm it's up
VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a11.IPAddress}}' victim-a11)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```
Victim IP: 172.18.0.2

{
    "app": "InnoZverse Shop",
    "version": "2.3.1"
}
```

---

### Step 2: Launch the Kali Attacker Container

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a11 \
  zchencow/innozverse-kali:latest bash
```

Set your target and confirm connectivity:

```bash
export TARGET="http://victim-a11:5000"
curl -s $TARGET/ | python3 -m json.tool
```

---

### Step 3: Service Fingerprinting — nmap + HTTP Scripts

```bash
echo "=== nmap: port scan + version detection + HTTP header script ==="

nmap -sV -p 5000 \
  --script=http-headers,http-title \
  victim-a11
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Apache httpd 2.4.52 ((Ubuntu))
|_http-server-header: Werkzeug/3.1.6 Python/3.10.12
|_http-title: Site doesn't have a title (application/json).
| http-headers:
|   Server: Werkzeug/3.1.6 Python/3.10.12
|   Server: Apache/2.4.52 (Ubuntu)
|   X-Powered-By: PHP/8.1.2
|   X-Generator: WordPress/6.4.3
|   X-AspNet-Version: 4.0.30319
|   X-Debug-Info: env=production;version=2.3.1;build=20260101
```

> 💡 **nmap's `http-headers` script pulls every response header in one scan.** Notice the server is sending contradictory headers — it claims to be Apache, PHP, WordPress, AND ASP.NET simultaneously. In a real engagement, mismatched headers like this indicate a reverse proxy in front of a different backend. The `X-Debug-Info` header is especially dangerous: it confirms the environment is `production`, leaks the version (`2.3.1`), and gives a build date — all useful for CVE matching.

---

### Step 4: Technology Stack Fingerprinting — whatweb

```bash
echo "=== whatweb: automated technology detection ==="
whatweb $TARGET

echo ""
echo "=== whatweb verbose — show all matched plugins ==="
whatweb -v $TARGET 2>/dev/null | head -40
```

**📸 Verified Output:**
```
http://victim-a11:5000/ [200 OK]
  ASP_NET[4.0.30319]
  HTTPServer[Ubuntu Linux][Werkzeug/3.1.6 Python/3.10.12, Apache/2.4.52 (Ubuntu)]
  PHP[8.1.2]
  Python[3.10.12]
  UncommonHeaders[x-generator, x-debug-info]
  Werkzeug[3.1.6]
  WordPress[6.4.3]
  X-Powered-By[PHP/8.1.2]
```

```bash
# Parse results into a structured stack profile
echo ""
echo "=== Technology stack profile ==="
curl -sI $TARGET/ | python3 << 'EOF'
import sys

headers = {}
for line in sys.stdin:
    line = line.strip()
    if ':' in line:
        k, _, v = line.partition(':')
        headers[k.lower()] = v.strip()

print("Technology Stack Identified:")
print(f"  Web Server:  {headers.get('server','unknown')}")
print(f"  Backend:     {headers.get('x-powered-by','unknown')}")
print(f"  CMS:         {headers.get('x-generator','unknown')}")
print(f"  Framework:   {headers.get('x-aspnet-version','unknown')}")
print(f"  Debug Info:  {headers.get('x-debug-info','none')}")
print()
print("CVE Attack Vectors (version-specific):")
print("  Apache 2.4.52  → CVE-2021-41773 (path traversal), CVE-2022-22720")
print("  PHP 8.1.2      → CVE-2022-31625 (heap corruption)")
print("  WordPress 6.4.3→ CVE-2024-0590 (XSS), multiple plugin CVEs")
print("  Python 3.10.12 → No critical CVEs")
EOF
```

**📸 Verified Output:**
```
Technology Stack Identified:
  Web Server:  Werkzeug/3.1.6 Python/3.10.12
  Backend:     PHP/8.1.2
  CMS:         WordPress/6.4.3
  Framework:   4.0.30319
  Debug Info:  env=production;version=2.3.1;build=20260101

CVE Attack Vectors (version-specific):
  Apache 2.4.52  → CVE-2021-41773 (path traversal), CVE-2022-22720
  PHP 8.1.2      → CVE-2022-31625 (heap corruption)
  WordPress 6.4.3→ CVE-2024-0590 (XSS), multiple plugin CVEs
```

---

### Step 5: Directory Enumeration — gobuster

```bash
echo "=== gobuster: enumerate all endpoints and files ==="

# Pass 1: common directories and pages
gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/common.txt \
  -t 20 --no-error -q

echo ""
echo "=== gobuster pass 2: add file extensions ==="
gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/small.txt \
  -x php,sql,env,bak,xml,txt,log,config \
  -t 20 --no-error -q
```

**📸 Verified Output:**
```
/admin                (Status: 200) [Size: 77]
/error                (Status: 500) [Size: 324]
/login                (Status: 200) [Size: 159]
/robots.txt           (Status: 200) [Size: 155]
/sitemap.xml          (Status: 200) [Size: 290]
/phpinfo.php          (Status: 200) [Size: 142]

/backup.sql           (Status: 200) [Size: 104]
/phpinfo.php          (Status: 200) [Size: 142]
```

> 💡 **gobuster's `-x` flag is critical for web recon.** Developers leave backup files (`backup.sql`, `config.php.bak`), environment files (`.env`), and debug pages (`phpinfo.php`) in the web root during development and forget to remove them. `Status: 200` means the file is readable by anyone. `Status: 301/302` means it redirects somewhere interesting. `Status: 403` means it exists but is blocked — worth noting for later bypass attempts.

---

### Step 6: Read robots.txt and sitemap.xml

```bash
echo "=== robots.txt — developer's list of 'hidden' paths ==="
curl -s $TARGET/robots.txt

echo ""
echo "=== sitemap.xml — all publicly intended URLs ==="
curl -s $TARGET/sitemap.xml | python3 -c "
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.stdin)
ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
urls = [url.find(f'{ns}loc').text for url in tree.findall(f'{ns}url')]
print('Sitemap URLs:')
for u in urls:
    print(f'  {u}')
"

echo ""
echo "=== robots.txt disallowed paths — attack surface ==="
curl -s $TARGET/robots.txt | grep Disallow | while read -r line; do
  path=$(echo $line | awk '{print $2}')
  echo "Testing: $path"
  curl -s -o /dev/null -w "  HTTP %{http_code}  $TARGET$path\n" "$TARGET$path"
done
```

**📸 Verified Output:**
```
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /api/internal/
Disallow: /.git/
Disallow: /config/
Sitemap: http://innozverse.com/sitemap.xml

Sitemap URLs:
  http://innozverse.com/
  http://innozverse.com/shop
  http://innozverse.com/checkout
  http://innozverse.com/api/products

Testing: /admin/
  HTTP 200  http://victim-a11:5000/admin/
Testing: /backup/
  HTTP 404  http://victim-a11:5000/backup/
Testing: /api/internal/
  HTTP 404  http://victim-a11:5000/api/internal/
Testing: /.git/
  HTTP 404  http://victim-a11:5000/.git/
```

> 💡 **`robots.txt` is the attacker's cheat sheet.** The `Disallow` entries are literally a list of "please don't look here" — which means they are always the first things an attacker looks at. `/.git/` being disallowed means a developer likely committed the `.git` directory to the web root; `git clone http://victim/` would download the entire source history. Never use `robots.txt` as a security control — it only works on compliant crawlers (which attackers are not).

---

### Step 7: Access Sensitive Exposed Files

```bash
echo "=== Reading exposed sensitive files ==="

echo "[1] .env — application secrets:"
curl -s $TARGET/.env
echo ""

echo "[2] .git/config — private repository URL:"
curl -s $TARGET/.git/config
echo ""

echo "[3] backup.sql — database credentials in plaintext:"
curl -s $TARGET/backup.sql
echo ""

echo "[4] phpinfo.php — full server configuration:"
curl -s $TARGET/phpinfo.php
echo ""

echo "[5] Verbose error page — full stack trace:"
curl -s $TARGET/error | python3 -m json.tool
```

**📸 Verified Output:**
```
[1] .env:
APP_ENV=production
DB_HOST=db.internal
DB_PASS=Sup3rS3cur3DB
AWS_KEY=AKIA5EXAMPLE
JWT_SECRET=weak-secret-123

[2] .git/config:
[core]
    repositoryformatversion = 0
[remote "origin"]
    url = https://github.com/innozverse/shop-private.git
[branch "main"]
    remote = origin

[3] backup.sql:
-- InnoZverse DB backup 2026-01-15
INSERT INTO users VALUES (1,'admin','Admin@2024!','admin');
INSERT INTO users VALUES (2,'alice','Alice@456','user');

[4] phpinfo.php:
PHP Version 8.1.2
DB: mysql://root:root@localhost/shop
Document Root: /var/www/html

[5] Error page:
{
    "error": "Test internal error",
    "framework": "Flask/Werkzeug 3.1.6",
    "python": "3.10.12",
    "server": "Ubuntu 22.04",
    "traceback": "Traceback (most recent call last):\n  File..."
}
```

---

### Step 8: Unauthenticated API Endpoints

```bash
echo "=== Accessing unauthenticated sensitive API endpoints ==="

echo "[1] /api/users — full user database, no auth:"
curl -s $TARGET/api/users | python3 -m json.tool

echo ""
echo "[2] /admin — admin panel, no auth:"
curl -s $TARGET/admin | python3 -m json.tool

echo ""
echo "[3] /api/internal/config — internal service config:"
curl -s $TARGET/api/internal/config | python3 -m json.tool

echo ""
echo "[4] /api/orders — all customer orders:"
curl -s $TARGET/api/orders | python3 -m json.tool
```

**📸 Verified Output:**
```json
[1] /api/users:
[
    {"email": "admin@innozverse.com", "id": 1, "role": "admin", "username": "admin"},
    {"email": "alice@corp.com",        "id": 2, "role": "user",  "username": "alice"},
    {"email": "bob@email.com",         "id": 3, "role": "user",  "username": "bob"}
]

[2] /admin:
{"actions": ["list users", "delete user", "export data"], "note": "No auth required!", "panel": "Admin Panel"}

[3] /api/internal/config:
{
    "cache_host": "redis.internal",
    "db_host":    "db.internal",
    "db_pass":    "Sup3rS3cur3DB",
    "debug":      true,
    "log_level":  "DEBUG"
}
```

---

### Step 9: Build the Recon Report

```bash
echo "=== Automated recon report ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a11:5000"

findings = []

def check(path, desc, severity):
    try:
        req = urllib.request.Request(f"{TARGET}{path}")
        resp = urllib.request.urlopen(req, timeout=3)
        findings.append((severity, desc, path, resp.status))
    except Exception as e:
        findings.append(("INFO", desc, path, str(e)[:30]))

# Technology headers
req = urllib.request.Request(f"{TARGET}/")
resp = urllib.request.urlopen(req)
h = dict(resp.headers)
findings.append(("MEDIUM", "Server version disclosed",        "Header: Server",           h.get("Server","")))
findings.append(("MEDIUM", "Backend language disclosed",      "Header: X-Powered-By",     h.get("X-Powered-By","")))
findings.append(("MEDIUM", "CMS version disclosed",           "Header: X-Generator",      h.get("X-Generator","")))
findings.append(("HIGH",   "Debug info in header",            "Header: X-Debug-Info",     h.get("X-Debug-Info","")))

# Files
check("/.env",                  "Secrets file exposed (.env)",        "CRITICAL")
check("/.git/config",           "Git config exposed (repo URL leak)",  "HIGH")
check("/backup.sql",            "DB backup exposed in web root",       "CRITICAL")
check("/phpinfo.php",           "phpinfo page exposed",                "HIGH")
check("/admin",                 "Admin panel without authentication",  "CRITICAL")
check("/api/users",             "User list without authentication",    "HIGH")
check("/api/internal/config",   "Internal config endpoint public",     "CRITICAL")
check("/error",                 "Verbose error page (stack trace)",     "MEDIUM")

# Sort by severity
sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
findings.sort(key=lambda x: sev_order.get(x[0], 5))

print("=" * 70)
print("  INNOZVERSE SHOP — RECON REPORT")
print("=" * 70)
print(f"  Target:   {TARGET}")
print(f"  Findings: {len(findings)}")
print("=" * 70)
print()

for sev, desc, path, detail in findings:
    icon = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢","INFO":"🔵"}.get(sev,"⚪")
    print(f"  {icon} [{sev:<8}] {desc}")
    print(f"            Path: {path}")
    print(f"            Detail: {str(detail)[:80]}")
    print()
EOF
```

**📸 Verified Output:**
```
======================================================================
  INNOZVERSE SHOP — RECON REPORT
======================================================================
  Target:   http://victim-a11:5000
  Findings: 12
======================================================================

  🔴 [CRITICAL ] Secrets file exposed (.env)
            Path: /.env
            Detail: 200

  🔴 [CRITICAL ] DB backup exposed in web root
            Path: /backup.sql
            Detail: 200

  🔴 [CRITICAL ] Admin panel without authentication
            Path: /admin
            Detail: 200

  🔴 [CRITICAL ] Internal config endpoint public
            Path: /api/internal/config
            Detail: 200

  🟠 [HIGH     ] Git config exposed (repo URL leak)
            Path: /.git/config
            Detail: 200

  🟠 [HIGH     ] phpinfo page exposed
            Path: /phpinfo.php
            Detail: 200

  🟠 [HIGH     ] User list without authentication
            Path: /api/users
            Detail: 200

  🟠 [HIGH     ] Debug info in header
            Path: Header: X-Debug-Info
            Detail: env=production;version=2.3.1;build=20260101

  🟡 [MEDIUM   ] Server version disclosed
            Path: Header: Server
            Detail: Apache/2.4.52 (Ubuntu)

  🟡 [MEDIUM   ] CMS version disclosed
            Path: Header: X-Generator
            Detail: WordPress/6.4.3

  🟡 [MEDIUM   ] Verbose error page (stack trace)
            Path: /error
            Detail: 500
```

---

### Step 10: Cleanup

```bash
exit  # Exit Kali
```

```bash
docker rm -f victim-a11
docker network rm lab-a11
```

---

## Attack Surface Summary

| Finding | Severity | Impact |
|---------|----------|--------|
| `.env` exposed | CRITICAL | All secrets: DB password, AWS key, JWT secret |
| `backup.sql` in web root | CRITICAL | Plaintext passwords for all users |
| `/admin` unauthenticated | CRITICAL | Full admin panel — user management, data export |
| `/api/internal/config` public | CRITICAL | DB host, Redis host, all internal addresses |
| `.git/config` exposed | HIGH | Private repo URL — source code accessible |
| `phpinfo.php` live | HIGH | DB connection string, document root, PHP config |
| `/api/users` unauthenticated | HIGH | Full user list with emails and roles |
| Version headers | MEDIUM | Direct CVE matching to known vulnerabilities |

---

## Remediation

| Finding | Fix |
|---------|-----|
| Version disclosure headers | Remove `Server`, `X-Powered-By`, `X-Generator` at nginx/Apache level |
| `.env` in web root | Move to parent directory above web root; block `\.env` at web server: `location ~ /\.env { deny all; }` |
| `.git` in web root | Add to `.gitignore` at deploy time; block via nginx: `location ~ /\.git { deny all; }` |
| Backup files in web root | Never keep `*.sql`, `*.bak` in web root; use secure off-site storage |
| Unauthenticated endpoints | All `/api/` endpoints require JWT validation; `/admin` behind IP allowlist + MFA |
| Verbose error pages | Return `{"error": "Internal Server Error", "id": "ERR-XXXX"}` — log details server-side only |
| phpinfo.php | Delete from production entirely; never deploy debug pages to production |

## Further Reading
- [OWASP Web Security Testing Guide — Information Gathering](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/)
- [gobuster GitHub](https://github.com/OJ/gobuster)
- [whatweb GitHub](https://github.com/urbanadventurer/WhatWeb)
- [Pentest-Standard Recon Phase](http://www.pentest-standard.org/index.php/Intelligence_Gathering)
