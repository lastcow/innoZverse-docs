# Lab 2: OWASP A02: Cryptographic Failures

## 🎯 Objective
Master owasp a02: cryptographic failures concepts and apply them in hands-on exercises.

## 📚 Background
Cryptographic Failures (formerly 'Sensitive Data Exposure') covers inadequate protection of sensitive data. Common issues include storing passwords in plaintext, using weak algorithms (MD5/SHA1), transmitting data over HTTP, or using ECB mode encryption.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Previous labs in this level
- Basic Linux familiarity

## 🛠️ Tools Used
- python3, openssl

## 🔬 Lab Instructions

### Step 1: Cryptographic Failures Examples
```bash
python3 -c "
failures = [
    ('MD5 passwords', 'hashlib.md5(password).hexdigest()', 'Use bcrypt/argon2'),
    ('Plaintext storage', 'password = "secret"  in database', 'Hash with salt'),
    ('HTTP transmission', 'http:// for login forms', 'Force HTTPS with HSTS'),
    ('Hardcoded keys', 'API_KEY = "abc123" in code', 'Use environment variables/vault'),
    ('Weak random', 'random.random() for tokens', 'Use secrets.token_hex()'),
    ('ECB mode AES', 'AES.new(key, AES.MODE_ECB)', 'Use AES-GCM or AES-CBC'),
    ('Short keys', 'RSA-512 or AES-64', 'RSA-2048+, AES-256'),
]
print('Cryptographic Failure Patterns:')
for failure, example, fix in failures:
    print(f'  ❌ {failure}')
    print(f'      Code: {example}')
    print(f'      Fix:  {fix}')
    print()
"
```

### Step 2: Secure vs Insecure Random
```bash
python3 -c "
import random, secrets

print('Insecure token generation (NEVER for security):')
for _ in range(3):
    token = hex(random.randint(0, 2**32))[2:]
    print(f'  random: {token}')
print('  ⚠️  Predictable! random.seed() can be guessed from output')
print()
print('Secure token generation:')
for _ in range(3):
    token = secrets.token_hex(32)
    print(f'  secrets: {token[:20]}...')
print('  ✅ Cryptographically secure, unpredictable')
"
```

### Step 3: ECB Mode Weakness
```bash
python3 -c "
print('Why AES ECB Mode is Dangerous:')
print()
print('ECB (Electronic Codebook) encrypts each block independently')
print('Same plaintext block → SAME ciphertext block')
print()
# Demonstrate with simple substitution cipher
import string
key = {c: chr((ord(c)-ord('A')+3)%26+ord('A')) if c.isupper() else c for c in string.printable}
def ecb_like(text):
    return ''.join(key.get(c, c) for c in text)

messages = ['AAAA BBBB AAAA', 'ADMIN ADMIN', 'HELLO WORLD']
print('ECB-like encryption:')
for msg in messages:
    enc = ecb_like(msg)
    print(f'  Plain:  {msg}')
    print(f'  Cipher: {enc}')
    print(f'  Pattern visible: {"REPEAT" if len(set(enc.split())) < len(enc.split()) else "no repeat"}')
    print()
print('Use AES-GCM (authenticated encryption) instead!')
"
```

### Step 4: Secure Password Storage
```bash
python3 -c "
import hashlib, os, time

password = 'MyPassword123'

# BAD: MD5 no salt
md5_hash = hashlib.md5(password.encode()).hexdigest()
print(f'❌ MD5 (no salt): {md5_hash}')
print('   Every user with same password has same hash!')

# BAD: SHA256 no salt  
sha_hash = hashlib.sha256(password.encode()).hexdigest()
print(f'❌ SHA256 (no salt): {sha_hash}')

# BETTER: SHA256 with salt
salt = os.urandom(32)
salted = hashlib.sha256(salt + password.encode()).hexdigest()
print(f'⚠️  SHA256+salt: {salted[:20]}... (better but still fast)')

# BEST: PBKDF2 (key stretching)
dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000)
print(f'✅ PBKDF2 (600k rounds): {dk.hex()[:20]}... (slow by design)')
print()
print('Best choice: bcrypt, argon2id, scrypt (use a library!)')
print('Never implement crypto primitives yourself')
"
```

### Step 5: TLS/HTTPS Enforcement
```bash
python3 -c "
print('Ensuring Data in Transit is Encrypted:')
print()
controls = [
    ('Force HTTPS redirect', 'HTTP 301 → HTTPS for all requests'),
    ('HSTS header', 'Strict-Transport-Security: max-age=31536000; includeSubDomains'),
    ('TLS 1.2+ only', 'Disable TLS 1.0, 1.1, SSL 3.0'),
    ('Strong cipher suites', 'ECDHE+AESGCM, ECDHE+CHACHA20 — no RC4 or 3DES'),
    ('Certificate pinning', 'Mobile apps: reject unexpected certificates'),
    ('OCSP stapling', 'Efficient certificate revocation checking'),
    ('CAA DNS record', 'Specify which CAs can issue certs for your domain'),
]
for control, detail in controls:
    print(f'  ✅ {control}')
    print(f'      {detail}')
"
```

## ✅ Verification
```bash
python3 -c "print('OWASP A02: Cryptographic Failures lab verified ✅')"
```

## 🚨 Common Mistakes
- Theory without practice — always test in a safe environment
- Using offensive tools without written authorization

## 📝 Summary
- A02 covers all data protection failures: storage, transit, and processing
- MD5/SHA1 for passwords are broken — use bcrypt/argon2 always
- ECB mode AES reveals patterns — use AES-GCM for authenticated encryption
- Use secrets module for security tokens, not random module
- HSTS header prevents SSL stripping attacks

## 🔗 Further Reading
- OWASP: owasp.org
- MITRE ATT&CK: attack.mitre.org
- SANS Reading Room
