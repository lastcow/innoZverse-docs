# Lab 3: OWASP A03: Injection Attacks

## 🎯 Objective
Master owasp a03: injection attacks concepts and apply them in hands-on exercises.

## 📚 Background
Injection vulnerabilities occur when untrusted data is sent as part of a command or query. SQL injection, command injection, LDAP injection, and XPath injection are all injection attacks. They remain one of the most dangerous vulnerability classes.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Previous labs in this level
- Basic Linux familiarity

## 🛠️ Tools Used
- python3, sqlite3

## 🔬 Lab Instructions

### Step 1: SQL Injection Demo (Safe Local SQLite)
```bash
python3 -c "
import sqlite3

# Create test database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE users (id INTEGER, username TEXT, password TEXT, role TEXT)')
cursor.execute("INSERT INTO users VALUES (1, 'alice', 'hash1', 'user')")
cursor.execute("INSERT INTO users VALUES (2, 'bob', 'hash2', 'user')")
cursor.execute("INSERT INTO users VALUES (3, 'admin', 'secret', 'admin')")
conn.commit()

def vulnerable_login(username, password):
    # VULNERABLE: string concatenation
    query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"
    print(f'  Query: {query}')
    cursor.execute(query)
    return cursor.fetchone()

def secure_login(username, password):
    # SECURE: parameterized query
    query = 'SELECT * FROM users WHERE username = ? AND password = ?'
    print(f'  Query: {query}')
    cursor.execute(query, (username, password))
    return cursor.fetchone()

print('=== SQL INJECTION DEMO ===')
print()
print('Normal login:')
result = vulnerable_login('alice', 'hash1')
print(f'  Result: {result}')
print()
print('SQLi bypass with: alice\'--')
result = vulnerable_login(\"alice'--\", 'anything')
print(f'  Result: {result}  ← BYPASSED AUTH!')
print()
print('\"OR 1=1-- attack:')
result = vulnerable_login(\"' OR 1=1--\", '')
print(f'  Result: {result}  ← GOT ADMIN!')
print()
print('Secure parameterized query:')
result = secure_login(\"' OR 1=1--\", '')
print(f'  Result: {result}  ← BLOCKED correctly')
"
```

### Step 2: Command Injection
```bash
python3 -c "
import subprocess, shlex

def vulnerable_ping(host):
    # VULNERABLE: shell=True with user input
    cmd = f'echo ping -c1 {host}'  # using echo to simulate safely
    print(f'Command would be: {cmd}')

def secure_ping(host):
    # SECURE: no shell, argument list
    if not all(c.isalnum() or c in '.-' for c in host):
        return 'Invalid hostname'
    cmd = ['ping', '-c1', host]
    print(f'Secure command: {cmd}')
    return 'validated'

print('Command Injection Demo:')
print()
normal = '127.0.0.1'
injection = '127.0.0.1; cat /etc/passwd'

print(f'Normal input: {normal}')
vulnerable_ping(normal)
print()
print(f'Injection attempt: {injection}')
vulnerable_ping(injection)
print('  ⚠️  Shell would execute BOTH commands!')
print()
print('Secure version:')
result = secure_ping(injection)
print(f'  Result: {result}')
"
```

### Step 3: Prevention Techniques
```bash
python3 -c "
print('Injection Prevention:')
print()
techniques = [
    ('Parameterized queries', 'ALWAYS use ? placeholders, never concatenate', '✅ Primary defense for SQLi'),
    ('Input validation', 'Whitelist allowed characters, reject everything else', '✅ Defense in depth'),
    ('Stored procedures', 'Database-side prepared statements', '✅ Additional SQLi protection'),
    ('Least privilege DB', 'App DB user can only SELECT/INSERT, not DROP', '✅ Limits damage'),
    ('WAF', 'Web Application Firewall detects injection patterns', '⚠️  Not a substitute for fixing code'),
    ('ORM', 'Object-Relational Mapper (SQLAlchemy, Django ORM)', '✅ Parameterized by default'),
    ('Escape output', 'HTML encode output to prevent XSS', '✅ Different layer, same principle'),
]
for technique, detail, status in techniques:
    print(f'{status} {technique}')
    print(f'      {detail}')
    print()
"
```

### Step 4: SQLi Impact Levels
```bash
python3 -c "
import sqlite3

conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE users (id INTEGER, name TEXT, email TEXT, credit_card TEXT)')
c.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com', '4111-1111-1111-1111')")
c.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com', '4222-2222-2222-2222')")
conn.commit()

impacts = [
    ('Authentication bypass', \"' OR 1=1--\"),
    ('Data dump', \"' UNION SELECT id,name,email,credit_card FROM users--\"),
    ('Schema discovery', \"' UNION SELECT 1,name,2,3 FROM sqlite_master WHERE type='table'--\"),
]

print('SQLi Impact Demonstration:')
for impact, payload in impacts:
    print(f'Impact: {impact}')
    print(f'Payload: {payload}')
    # Safe simulation
    print(f'Would expose: {'all user data including credit cards' if 'UNION' in payload else 'authentication bypass'}')
    print()
"
```

### Step 5: ORM Usage (Secure by Default)
```bash
python3 -c "
print('Why ORMs Are Safer:')
print()
print('Raw SQL (dangerous):')
print('  user_id = request.args.get("id")')
print('  query = f"SELECT * FROM users WHERE id = {user_id}"')
print()
print('ORM (SQLAlchemy - safe):')
print('  user = db.session.query(User).filter_by(id=user_id).first()')
print('  # Generates: SELECT * FROM users WHERE id = ?  (parameterized!)')
print()
print('Django ORM (safe):')
print('  user = User.objects.get(id=user_id)')
print('  # Generates: SELECT * FROM auth_user WHERE id = %s')
print()
print('ORMs generate parameterized queries automatically')
print('Vulnerable: ORM raw() or extra() with user input')
print('  User.objects.raw(f"SELECT * FROM users WHERE id={user_id}")  ← UNSAFE!')
"
```

## ✅ Verification
```bash
python3 -c "print('OWASP A03: Injection Attacks lab verified ✅')"
```

## 🚨 Common Mistakes
- Theory without practice — always test in a safe environment
- Using offensive tools without written authorization

## 📝 Summary
- Injection occurs when untrusted data is interpreted as commands
- SQLi bypasses authentication and extracts entire databases
- Always use parameterized queries / prepared statements
- Command injection: never use shell=True with user-supplied input
- ORMs provide parameterized queries by default — use them

## 🔗 Further Reading
- OWASP: owasp.org
- MITRE ATT&CK: attack.mitre.org
- SANS Reading Room
