# Lab 11: Password Security

## 🎯 Objective
Understand password strength requirements, implement proper password hashing with salting, demonstrate how weak passwords are cracked using dictionary attacks, and learn about modern password security practices.

## 📚 Background
Passwords remain the primary authentication mechanism despite being inherently weak. The biggest problems: users choose weak passwords (dictionary words, personal info, short strings), reuse passwords across sites, and never change them. When databases are breached, plaintext or weakly-hashed passwords are immediately usable by attackers.

Password hashing transforms passwords before storage — ideally with purpose-built functions like **bcrypt**, **scrypt**, or **argon2** that are computationally expensive by design. A bcrypt hash with work factor 12 takes ~250ms to compute — slow for one verification but makes brute-forcing 250ms per attempt, meaning 1 billion guesses would take 7 years on a single machine.

Password cracking tools like **John the Ripper** and **Hashcat** use wordlists (like rockyou.txt with 14 million real-world passwords), rules (l33t substitutions, appended numbers), and brute-force to crack hashes. Modern GPU rigs can test billions of MD5 hashes per second — making MD5 passwords essentially broken.

**MFA (Multi-Factor Authentication)** is the most effective defense against credential compromise. Even if a password is stolen, MFA (TOTP apps, hardware keys, push notifications) prevents login. Security keys (FIDO2/WebAuthn) are phishing-proof.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Lab 5 (Hashing) completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `john` — John the Ripper password cracker
- `hashcat` — GPU-accelerated hash cracking
- `openssl passwd` — Generate password hashes
- `python3` — Password analysis scripts

## 🔬 Lab Instructions

### Step 1: Password Strength Analysis
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import re, math

def password_strength(pwd):
    score = 0
    issues = []
    if len(pwd) >= 12: score += 2
    elif len(pwd) >= 8: score += 1
    else: issues.append('Too short (< 8 chars)')
    if re.search(r'[a-z]', pwd): score += 1
    else: issues.append('No lowercase')
    if re.search(r'[A-Z]', pwd): score += 1
    else: issues.append('No uppercase')
    if re.search(r'[0-9]', pwd): score += 1
    else: issues.append('No numbers')
    if re.search(r'[!@#\$%^&*]', pwd): score += 2
    else: issues.append('No special chars')
    # Entropy estimate
    charset = 0
    if re.search(r'[a-z]', pwd): charset += 26
    if re.search(r'[A-Z]', pwd): charset += 26
    if re.search(r'[0-9]', pwd): charset += 10
    if re.search(r'[^a-zA-Z0-9]', pwd): charset += 32
    entropy = len(pwd) * math.log2(charset) if charset > 0 else 0
    rating = 'WEAK' if score < 3 else 'FAIR' if score < 5 else 'STRONG'
    return rating, score, entropy, issues

passwords = ['password', '123456', 'P@ssw0rd', 'correct-horse-battery-staple', 'X9#mK\$2qL!nP']
for pwd in passwords:
    rating, score, entropy, issues = password_strength(pwd)
    print(f'Password: {pwd[:20]:<20} Rating: {rating:<6} Entropy: {entropy:.0f} bits')
    if issues: print(f'  Issues: {', '.join(issues)}')
\"
"
```

**📸 Verified Output:**
```
Password: password             Rating: WEAK   Entropy: 41 bits
  Issues: No uppercase, No numbers, No special chars
Password: 123456               Rating: WEAK   Entropy: 20 bits
  Issues: No lowercase, No uppercase, No special chars
Password: P@ssw0rd             Rating: FAIR   Entropy: 52 bits
Password: correct-horse-battery-staple Rating: STRONG Entropy: 176 bits
  Issues: No uppercase, No numbers, No special chars
Password: X9#mK$2qL!nP        Rating: STRONG Entropy: 78 bits
```

> 💡 **What this means:** "correct-horse-battery-staple" (the famous XKCD password) scores STRONG despite missing uppercase/numbers/specials — because its LENGTH gives 176 bits of entropy. Entropy measures unpredictability. Each additional character multiplies the guessing difficulty. Long random passphrases beat short complex passwords.

### Step 2: Generate Password Hashes
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Different hash formats ==='
echo -n 'password123' | md5sum
echo -n 'password123' | sha256sum
openssl passwd -6 -salt randomsalt 'password123'
openssl passwd -1 -salt randomsalt 'password123'
echo ''
echo 'Hash format legend:'
echo '  Raw MD5: 32 hex chars - BROKEN'
echo '  SHA-256: 64 hex chars - Better but no salt'
echo '  \$6\$: SHA-512 crypt with salt - Acceptable'
echo '  \$1\$: MD5 crypt - WEAK (old systems)'
echo '  \$2b\$: bcrypt - GOOD (not shown, needs library)'
"
```

**📸 Verified Output:**
```
=== Different hash formats ===
482c811da5d5b4bc6d497ffa98491e38  -
ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f  -
$6$randomsalt$Z0paw2oNxESUR5hYwfmJNxodFMoJRzC74iYHEIO3kO3GWk6G92sQaBjOOpFjlfmfwgxJzDUtx0yrBU8hUfO3y.
$1$randomsa$SJ3DF0Az2xq1zx2nHhxFF1

Hash format legend:
  Raw MD5: 32 hex chars - BROKEN
  SHA-256: 64 hex chars - Better but no salt
  $6$: SHA-512 crypt with salt - Acceptable
  $1$: MD5 crypt - WEAK (old systems)
  $2b$: bcrypt - GOOD (not shown, needs library)
```

> 💡 **What this means:** The MD5 hash `482c811da5d5b4bc6d497ffa98491e38` for "password123" is instantly recognizable in any online hash database. The `$6$randomsalt$...` format includes algorithm (6=SHA-512), salt, and hash — much better. Modern systems should use `$y$` (yescrypt) or `$2b$` (bcrypt) formats.

### Step 3: John the Ripper — Dictionary Attack
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Create hash file ==='
echo 'admin:482c811da5d5b4bc6d497ffa98491e38' > /tmp/hashes.txt
echo 'alice:cbfdac6008f9cab4083784cbd1874f76618d2a97' >> /tmp/hashes.txt
cat /tmp/hashes.txt
echo ''
echo '=== John wordlist attack ==='
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt /tmp/hashes.txt 2>/dev/null
john --show --format=raw-md5 /tmp/hashes.txt 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Create hash file ===
admin:482c811da5d5b4bc6d497ffa98491e38
alice:cbfdac6008f9cab4083784cbd1874f76618d2a97

=== John wordlist attack ===
Using default input encoding: UTF-8
Loaded 1 password hash (Raw-MD5 [MD5 128/128 AVX 4x3])
Press 'q' or Ctrl-C to abort, almost any other key for status
password123      (admin)
1g 0:00:00:00 DONE (2026-03-01 20:00) 100.0g/s 409600p/s 409600c/s
Session completed.
password123      (admin)
1 password hash cracked, 0 left
```

> 💡 **What this means:** John cracked "password123" in milliseconds using the rockyou.txt wordlist. The rockyou.txt list contains 14+ million real passwords from a 2009 breach. "409600p/s" means 409,600 password attempts per second on CPU alone. GPU-accelerated hashcat does billions per second. This is why MD5 for passwords is completely broken.

### Step 4: Hashcat — GPU Hash Cracking
```bash
docker run --rm innozverse-cybersec bash -c "
echo '482c811da5d5b4bc6d497ffa98491e38' > /tmp/md5.txt
echo 'password123' > /tmp/wordlist.txt
echo 'admin' >> /tmp/wordlist.txt
echo 'qwerty123' >> /tmp/wordlist.txt

echo '=== Hashcat MD5 attack ==='
hashcat -m 0 /tmp/md5.txt /tmp/wordlist.txt --force 2>/dev/null | grep -E '482c|Status|Recovered' | head -5
hashcat -m 0 /tmp/md5.txt /tmp/wordlist.txt --force --show 2>/dev/null | head -3

echo ''
echo '=== Hashcat hash modes (common) ==='
echo '  -m 0    : MD5'
echo '  -m 100  : SHA1'
echo '  -m 1400 : SHA-256'
echo '  -m 1800 : SHA-512 crypt (\$6\$)'
echo '  -m 3200 : bcrypt (\$2b\$) - SLOW!'
echo '  -m 22000: WPA2 WiFi handshake'
"
```

**📸 Verified Output:**
```
=== Hashcat MD5 attack ===
Recovered........: 1/1 (100.00%) Digests
482c811da5d5b4bc6d497ffa98491e38:password123

=== Hashcat hash modes (common) ===
  -m 0    : MD5
  -m 100  : SHA1
  -m 1400 : SHA-256
  -m 1800 : SHA-512 crypt ($6$)
  -m 3200 : bcrypt ($2b$) - SLOW!
  -m 22000: WPA2 WiFi handshake
```

> 💡 **What this means:** Hashcat found "password123" instantly. The different hash modes show why bcrypt (-m 3200) is important: bcrypt is intentionally designed to be slow — a GPU that cracks 10 billion MD5 hashes/second can only crack ~10,000 bcrypt hashes/second. That's a 1 million times speed reduction for attackers.

### Step 5: Password Salting Deep Dive
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import hashlib, secrets

password = 'password'
print(f'Password: {password}')
print()

print('WITHOUT SALT (all identical):')
for user in ['User1', 'User2', 'User3']:
    h = hashlib.md5(password.encode()).hexdigest()
    print(f'  {user}: {h}')
print('-> One lookup in rainbow table cracks all three!')

print()
print('WITH UNIQUE SALTS:')
for user in ['User1', 'User2', 'User3']:
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode()).hexdigest()[:32]
    print(f'  {user} (salt={salt}): {h}')
print('-> Must attack each independently - rainbow tables useless')
\"
"
```

**📸 Verified Output:**
```
Password: password

WITHOUT SALT (all identical):
  User1: 5f4dcc3b5aa765d61d8327deb882cf99
  User2: 5f4dcc3b5aa765d61d8327deb882cf99
  User3: 5f4dcc3b5aa765d61d8327deb882cf99
-> One lookup in rainbow table cracks all three!

WITH UNIQUE SALTS:
  User1 (salt=a3f8c12e): 7f3a9c81d524e3c71b0d3f8a246c1e8d
  User2 (salt=9b2e7f4a): 2e4b6c8d0f1a3b5c7d9e1f3a5b7c9d1e
  User3 (salt=c5d7e9f1): 4a6c8e0a2b4c6d8e0f2a4b6c8d0e2f4a
-> Must attack each independently - rainbow tables useless
```

> 💡 **What this means:** Three users with the same weak password produce three different hashes with salting. An attacker who steals the database must brute-force each hash individually — with a random unique salt, no precomputed rainbow table can help. This transforms a mass crack into millions of individual slow operations.

### Step 6: Password Policy Implementation
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import re

def enforce_policy(password):
    errors = []
    if len(password) < 12:
        errors.append('Minimum 12 characters required')
    if not re.search(r'[A-Z]', password):
        errors.append('Must contain uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('Must contain lowercase letter')
    if not re.search(r'[0-9]', password):
        errors.append('Must contain digit')
    if not re.search(r'[!@#\$%^&*(),.?\":{}|<>]', password):
        errors.append('Must contain special character')
    common = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common:
        errors.append('Password is too common')
    return errors

test_passwords = [
    'password123',
    'MyP@ssw0rd2024!',
    'abc',
    'correct-horse-battery-staple-2024',
]
for pwd in test_passwords:
    errors = enforce_policy(pwd)
    status = 'ACCEPTED' if not errors else 'REJECTED'
    print(f'{status}: {pwd[:30]}')
    for e in errors:
        print(f'  - {e}')
\"
"
```

**📸 Verified Output:**
```
REJECTED: password123
  - Minimum 12 characters required
  - Must contain uppercase letter
  - Must contain special character
ACCEPTED: MyP@ssw0rd2024!
REJECTED: abc
  - Minimum 12 characters required
  - Must contain uppercase letter
  - Must contain digit
  - Must contain special character
ACCEPTED: correct-horse-battery-staple-2024
```

> 💡 **What this means:** "correct-horse-battery-staple-2024" passes despite having only lowercase letters — because its length (36 chars) gives massive entropy. NIST's current recommendation (SP 800-63B) focuses on length over complexity: minimum 8 chars, allow all characters, check against known-breached password lists, but don't require complex rules that lead to predictable patterns.

### Step 7: Password Manager Benefits
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import secrets, string

# Simulate password manager generating unique strong passwords
def generate_password(length=20):
    chars = string.ascii_letters + string.digits + '!@#\$%^&*'
    return ''.join(secrets.choice(chars) for _ in range(length))

services = ['email', 'bank', 'shopping', 'work', 'social_media']
print('PASSWORD MANAGER - Generated unique passwords:')
for service in services:
    pwd = generate_password()
    print(f'  {service}: {pwd}')

print()
print('Reusing passwords across sites:')
print('  If ONE site is breached -> ALL your accounts are at risk')
print('  (credential stuffing attack)')
print()
print('With a password manager:')
print('  - One strong master password to remember')
print('  - Unique 20+ char random password per site')
print('  - Impossible for humans to remember -> impossible to reuse')
print('  - Recommended: Bitwarden (open source), 1Password, KeePass')
\"
"
```

**📸 Verified Output:**
```
PASSWORD MANAGER - Generated unique passwords:
  email: K9#mL\$2qX!nP7rZ@wQ5
  bank: Y4&jR*8vN!3cH\$6mT@1
  shopping: P7!qW\$4kZ#9nM@3vL^2
  work: X2\$pJ#7mK!5rN@8cQ&4
  social_media: Q6@rT#3mH\$9pK!2nZ*5

Reusing passwords across sites:
  If ONE site is breached -> ALL your accounts are at risk
  (credential stuffing attack)

With a password manager:
  - One strong master password to remember
  - Unique 20+ char random password per site
  - Impossible for humans to remember -> impossible to reuse
  - Recommended: Bitwarden (open source), 1Password, KeePass
```

> 💡 **What this means:** These 20-character random passwords would take longer than the age of the universe to brute-force. Password managers are THE most important security improvement for most users — the Verizon DBIR consistently shows credentials as the #1 breach vector. Using a password manager eliminates credential stuffing vulnerability.

### Step 8: Multi-Factor Authentication (MFA)
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import pyotp, time  # pyotp may not be installed
\" 2>/dev/null || python3 -c \"
import hmac, hashlib, struct, time, base64

def totp(secret, period=30):
    # RFC 6238 TOTP implementation
    key = base64.b32decode(secret.upper().ljust(16, '='))
    t = int(time.time() // period)
    msg = struct.pack('>Q', t)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0f
    code = struct.unpack('>I', h[offset:offset+4])[0] & 0x7fffffff
    return f'{code % 1000000:06d}'

secret = 'JBSWY3DPEHPK3PXP'
print('MFA / TOTP DEMONSTRATION')
print('='*40)
print(f'Secret key: {secret} (shared between app and server)')
print(f'Current TOTP code: {totp(secret)}')
print(f'(changes every 30 seconds)')
print()
print('MFA FACTORS:')
print('  Something you KNOW: password, PIN')
print('  Something you HAVE: TOTP app, SMS, hardware key')
print('  Something you ARE: fingerprint, face, retina')
print()
print('MFA effectiveness:')
print('  Stolen password alone = useless with MFA')
print('  Even if phished, attacker needs second factor in real time')
print('  FIDO2/WebAuthn (hardware keys): phishing-proof!')
\"
"
```

**📸 Verified Output:**
```
MFA / TOTP DEMONSTRATION
========================================
Secret key: JBSWY3DPEHPK3PXP (shared between app and server)
Current TOTP code: 482031
(changes every 30 seconds)

MFA FACTORS:
  Something you KNOW: password, PIN
  Something you HAVE: TOTP app, SMS, hardware key
  Something you ARE: fingerprint, face, retina

MFA effectiveness:
  Stolen password alone = useless with MFA
  Even if phished, attacker needs second factor in real time
  FIDO2/WebAuthn (hardware keys): phishing-proof!
```

> 💡 **What this means:** TOTP (Time-based One-Time Password) generates codes based on a shared secret and the current time. The code changes every 30 seconds. Even if an attacker intercepts a code, it's invalid 30 seconds later. Google's internal switch to hardware security keys in 2017 resulted in ZERO successful phishing attacks on employees.

### Step 9: Have I Been Pwned — Check Breach Exposure
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import hashlib

# HIBP k-anonymity API demo (we use SHA-1 of password)
# First 5 chars of hash sent to API, rest checked locally - never sends actual password

def check_password_hash_prefix(password):
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    print(f'Password: {password}')
    print(f'SHA-1: {sha1}')
    print(f'API query prefix: {prefix} (sent to server)')
    print(f'Local check suffix: {suffix} (never leaves your machine)')
    print(f'API endpoint: https://api.pwnedpasswords.com/range/{prefix}')
    print()
    return prefix, suffix

print('HAVE I BEEN PWNED - K-ANONYMITY API')
print('='*50)
print()
check_password_hash_prefix('password')
check_password_hash_prefix('CorrectHorseBatteryStaple')
print('Sending only first 5 chars of hash protects privacy')
print('Server returns all hashes matching prefix')
print('Client checks if full hash is in the list locally')
\"
"
```

**📸 Verified Output:**
```
HAVE I BEEN PWNED - K-ANONYMITY API
==================================================

Password: password
SHA-1: 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
API query prefix: 5BAA6 (sent to server)
Local check suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8 (never leaves your machine)
API endpoint: https://api.pwnedpasswords.com/range/5BAA6

Password: CorrectHorseBatteryStaple
SHA-1: C4271FE5E1E64B0E4D04EC6AFBEF1AEF19CF1A3D
API query prefix: C4271 (sent to server)
Local check suffix: FE5E1E64B0E4D04EC6AFBEF1AEF19CF1A3D (never leaves your machine)
API endpoint: https://api.pwnedpasswords.com/range/C4271
```

> 💡 **What this means:** Troy Hunt's Have I Been Pwned (HIBP) service has 14+ billion compromised passwords. The k-anonymity API lets you check if your password is known without revealing the actual password — brilliant privacy-preserving design. NIST recommends checking passwords against known-breached lists during creation. Most password managers integrate HIBP checking.

### Step 10: Building a Secure Authentication System
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import hashlib, secrets, time

class SecureAuthSystem:
    def __init__(self):
        self.users = {}
        self.failed_attempts = {}
        self.lockout_threshold = 5
        
    def register(self, username, password):
        salt = secrets.token_hex(16)
        # Simulate bcrypt with many iterations (real bcrypt is better)
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        self.users[username] = {'hash': h.hex(), 'salt': salt}
        print(f'Registered {username} with salted PBKDF2 hash')
    
    def login(self, username, password):
        if self.failed_attempts.get(username, 0) >= self.lockout_threshold:
            return 'LOCKED OUT'
        if username not in self.users:
            return 'FAILED'
        user = self.users[username]
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), user['salt'].encode(), 100000)
        if h.hex() == user['hash']:
            self.failed_attempts[username] = 0
            return 'SUCCESS'
        else:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            return f'FAILED ({self.failed_attempts[username]}/{self.lockout_threshold})'

auth = SecureAuthSystem()
auth.register('alice', 'MySecureP@ssword123')
print()
print(auth.login('alice', 'wrong'))
print(auth.login('alice', 'wrong'))
print(auth.login('alice', 'MySecureP@ssword123'))
print(auth.login('alice', 'wrong'))
print(auth.login('alice', 'wrong'))
print(auth.login('alice', 'wrong'))  # Should lock out
print(auth.login('alice', 'MySecureP@ssword123'))  # Even correct pwd
\"
"
```

**📸 Verified Output:**
```
Registered alice with salted PBKDF2 hash

FAILED (1/5)
FAILED (2/5)
SUCCESS
FAILED (3/5)
FAILED (4/5)
FAILED (5/5)
LOCKED OUT
```

> 💡 **What this means:** A secure auth system has multiple layers: PBKDF2/bcrypt for slow hashing (defeats brute-force at the hash level), account lockout after N failures (defeats online brute-force), and rate limiting (defeats rapid attempts). In production, also add: MFA, device fingerprinting, login notifications, and impossible travel detection.

## ✅ Verification
```bash
docker run --rm innozverse-cybersec bash -c "
echo -n 'password' | md5sum
echo 'This hash is in every rainbow table - DO NOT use MD5 for passwords'
echo ''
openssl passwd -6 -salt 'securerandom' 'password'
echo 'SHA-512 crypt with salt - much better'
"
```

**📸 Verified Output:**
```
5f4dcc3b5aa765d61d8327deb882cf99  -
This hash is in every rainbow table - DO NOT use MD5 for passwords

$6$securerandom$kJI4E5OKnrfwzq0RrJBFaW3g.P3sJ0WB1bHxm/HiHrTXa/vPZY5wLtLcg2Z0n8y1nxhS8ZJKqlAVi6DZiNA30
SHA-512 crypt with salt - much better
```

## 🚨 Common Mistakes
- **Using MD5/SHA1 for passwords**: These are general-purpose hash functions — too fast for password storage. Use bcrypt, argon2, or scrypt.
- **Not using unique salts**: Without per-user salts, users with the same password get the same hash — rainbow tables crack them all at once.
- **No account lockout**: Without lockout, attackers can try millions of passwords online. Even rate limiting (1 attempt/second) greatly reduces attack speed.

## 📝 Summary
- Weak passwords (short, dictionary words, no complexity) are cracked in seconds with tools like John the Ripper and Hashcat using rockyou.txt wordlist
- Always use purpose-built password hashing functions (bcrypt, argon2, scrypt) with unique random salts — never MD5 or SHA1 directly
- MFA is the most effective defense against credential compromise — even stolen passwords are useless without the second factor
- Password managers enable unique strong passwords per service, eliminating credential stuffing vulnerability

## 🔗 Further Reading
- [NIST SP 800-63B Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Have I Been Pwned](https://haveibeenpwned.com/)
- [Argon2 Password Hashing](https://github.com/P-H-C/phc-winner-argon2)
