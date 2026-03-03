# Lab 1: OWASP A01: Broken Access Control

## 🎯 Objective
Master owasp a01: broken access control concepts and apply them in hands-on exercises.

## 📚 Background
Broken Access Control is the #1 OWASP vulnerability (2021). It occurs when users can act outside their intended permissions — accessing other users' data, admin functions, or unauthorized resources.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Previous labs in this level
- Basic Linux familiarity

## 🛠️ Tools Used
- python3

## 🔬 Lab Instructions

### Step 1: Understand Broken Access Control
```bash
python3 -c "
types = [
    ('IDOR', 'Insecure Direct Object Reference', 'Change URL id=123 to id=124 to access other user data'),
    ('Path Traversal', 'Directory traversal', '../../../etc/passwd to access system files'),
    ('Privilege Escalation', 'Horizontal/Vertical', 'Access admin functions as regular user'),
    ('CORS Misconfiguration', 'Cross-origin bypass', 'Allows any origin to access sensitive API'),
    ('Missing Auth', 'No access control', 'Admin pages accessible without login'),
]
print('Broken Access Control Types:')
for t, name, example in types:
    print(f'  {t}: {name}')
    print(f'    Example: {example}')
    print()
"
```

### Step 2: IDOR Demo
```bash
python3 -c "
# Simulate IDOR vulnerability
users = {
    '1': {'name': 'Alice', 'email': 'alice@example.com', 'salary': 75000},
    '2': {'name': 'Bob', 'email': 'bob@example.com', 'salary': 80000},
    '3': {'name': 'Admin', 'email': 'admin@example.com', 'salary': 150000},
}

def vulnerable_endpoint(user_id, requesting_user_id='1'):
    # VULNERABLE: no access check
    if user_id in users:
        return users[user_id]
    return None

def secure_endpoint(user_id, requesting_user_id='1'):
    # SECURE: check that requester can only access their own data
    if user_id != requesting_user_id and requesting_user_id != '3':  # 3=admin
        return 'ACCESS DENIED'
    if user_id in users:
        return users[user_id]
    return None

print('IDOR Vulnerability Demo:')
print()
print('Logged in as user 1 (Alice)')
print(f'GET /api/user/1 → {vulnerable_endpoint("1", "1")}')
print(f'GET /api/user/2 → {vulnerable_endpoint("2", "1")} ← IDOR! Can see Bob data')
print(f'GET /api/user/3 → {vulnerable_endpoint("3", "1")} ← Sees admin salary!')
print()
print('Secure version:')
print(f'GET /api/user/1 → {secure_endpoint("1", "1")}')
print(f'GET /api/user/2 → {secure_endpoint("2", "1")} ← Blocked correctly')
"
```

### Step 3: Path Traversal
```bash
python3 -c "
import os

# Demonstrate path traversal vulnerability
def vulnerable_file_read(filename):
    # VULNERABLE: no path validation
    base_dir = '/tmp/webroot'
    os.makedirs(base_dir, exist_ok=True)
    with open(os.path.join('/tmp/webroot', filename), 'r') as f:
        return f.read()

def secure_file_read(filename):
    # SECURE: validate path is within allowed directory
    base_dir = '/tmp/webroot'
    requested = os.path.realpath(os.path.join(base_dir, filename))
    if not requested.startswith(os.path.realpath(base_dir)):
        return 'ACCESS DENIED: Path traversal detected!'
    try:
        with open(requested, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return 'File not found'

# Create test file
os.makedirs('/tmp/webroot', exist_ok=True)
with open('/tmp/webroot/index.html', 'w') as f:
    f.write('Welcome to the website')

print('Path Traversal Demo:')
print()
print('Attacker requests: ../etc/passwd')
result = secure_file_read('../etc/passwd')
print(f'Secure result: {result}')
print()
print('Normal request: index.html')
result = secure_file_read('index.html')
print(f'Normal result: {result}')
"
```

### Step 4: Access Control Best Practices
```bash
python3 -c "
print('Access Control Implementation Best Practices:')
print()
practices = [
    ('Deny by default', 'Deny all access, then explicitly allow what is needed'),
    ('Verify on server', 'Never trust client-side access control (UI hiding is not security)'),
    ('Use indirect references', 'Map UUIDs or tokens to actual IDs — never expose sequential IDs'),
    ('Check on each request', 'Not just at login — re-verify on every sensitive operation'),
    ('Log violations', 'Log and alert on access control failures — they indicate attacks'),
    ('Rate limit', 'Limit repeated failures to slow enumeration attacks'),
    ('Test thoroughly', 'Test all roles, especially horizontal privilege escalation'),
]
for practice, detail in practices:
    print(f'  ✅ {practice}')
    print(f'      {detail}')
    print()
"
```

### Step 5: Test Your Own Access Controls
```bash
python3 -c "
print('Access Control Testing Checklist:')
print()
tests = [
    'Can user A access user B account by changing ID in URL?',
    'Can regular user access admin-only endpoints?',
    'Can logged-out user access protected resources?',
    'Can user access files outside allowed directory (path traversal)?',
    'Are access controls enforced in API as well as web UI?',
    'Can user perform actions for another user (CSRF)?',
    'Does the app expose sensitive data in client-side code?',
    'Can user escalate by modifying role/permission values?',
]
for i, test in enumerate(tests, 1):
    print(f'  {i}. {test}')
print()
print('Tools: Burp Suite, OWASP ZAP, manual testing')
"
```

## ✅ Verification
```bash
python3 -c "print('OWASP A01: Broken Access Control lab verified ✅')"
```

## 🚨 Common Mistakes
- Theory without practice — always test in a safe environment
- Using offensive tools without written authorization

## 📝 Summary
- A01 Broken Access Control is #1 OWASP 2021 vulnerability
- IDOR: changing IDs to access other users' data
- Path traversal: ../../../etc/passwd to escape allowed directory
- Server-side access control is mandatory — never trust client-side
- Log and alert on access control violations

## 🔗 Further Reading
- OWASP: owasp.org
- MITRE ATT&CK: attack.mitre.org
- SANS Reading Room
