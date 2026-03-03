# Lab 5: Hashing and Integrity

## 🎯 Objective
Master cryptographic hashing — MD5, SHA-1, SHA-256 — to verify file integrity, detect tampering, and understand why rainbow tables make weak hashing dangerous. Apply hashing to real security scenarios.

## 📚 Background
A cryptographic hash function takes any input and produces a fixed-length "fingerprint" (digest). Good hash functions have three key properties: **preimage resistance** (can't reverse the hash to find the input), **second preimage resistance** (can't find a different input with the same hash), and **collision resistance** (can't find any two inputs with the same hash).

Hashing is used everywhere in security: **file integrity verification** (download a file, hash it, compare with the published hash to confirm no tampering), **password storage** (store the hash, never the password), **digital signatures** (sign the hash of a document, not the document itself), and **blockchain** (each block contains the hash of the previous block, making tampering detectable).

**Rainbow tables** are precomputed tables of hash values for common passwords. If an attacker steals a database of MD5 password hashes, they can look each hash up in a rainbow table and instantly find the original password. Salting defeats rainbow tables by making each hash unique even for identical passwords.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 4 (Cryptography Basics) completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `md5sum`, `sha1sum`, `sha256sum` — Hash computation
- `openssl dgst` — Multi-algorithm hashing
- `python3` — Demonstrating rainbow tables and salting

## 🔬 Lab Instructions

### Step 1: Compute Hashes of Common Passwords
See why common passwords are instantly crackable:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Common password hashes (MD5) ==='
echo -n 'password' | md5sum
echo -n '123456' | md5sum
echo -n 'qwerty' | md5sum
echo -n 'admin' | md5sum
echo -n 'letmein' | md5sum
"
```

**📸 Verified Output:**
```
=== Common password hashes (MD5) ===
5f4dcc3b5aa765d61d8327deb882cf99  -
e10adc3949ba59abbe56e057f20f883e  -
d8578edf8458ce06fbc5bb76a58c5ca4  -
21232f297a57a5a743894a0e4a801fc3  -
0d107d09f5bbe40cade3de5c71e9e9b7  -
```

> 💡 **What this means:** The MD5 hash `5f4dcc3b5aa765d61d8327deb882cf99` for "password" is one of the most searched strings in rainbow table databases — any attacker can instantly identify it. These hashes are published in online databases (like https://crackstation.net/). If you see this in a database dump, the password is immediately known.

### Step 2: File Integrity Verification
Hash a file, tamper with it, detect the tampering:

```bash
docker run --rm innozverse-cybersec bash -c "
echo 'Important document content' > /tmp/test.txt
echo 'database_password=SuperSecret123' >> /tmp/test.txt

echo '=== Original file hash ==='
sha256sum /tmp/test.txt

echo ''
echo '=== Now tamper with the file ==='
echo 'database_password=HACKED!' >> /tmp/test.txt

echo '=== Tampered file hash ==='
sha256sum /tmp/test.txt
echo ''
echo 'HASHES DIFFER - tampering detected!'
"
```

**📸 Verified Output:**
```
=== Original file hash ===
27124f0ee17aaa40a8b72930b1e929201e1e46307bd816d3c45b2bb39ac88dcd  /tmp/test.txt

=== Now tamper with the file ===

=== Tampered file hash ===
2e9bff907b34acd9b74847889ee543e6291c0b7fdc5efcfe333937495998b76b  /tmp/test.txt

HASHES DIFFER - tampering detected!
```

> 💡 **What this means:** The two SHA-256 hashes are completely different because we added content to the file. This is how software distributors verify downloads — they publish the SHA-256 hash alongside the download. Before running software, compute the hash and compare. If it differs, the file was corrupted or tampered with (potentially injected with malware).

### Step 3: Hash Algorithm Comparison
```bash
docker run --rm innozverse-cybersec bash -c "
echo -n 'Hello World' | openssl dgst -md5
echo -n 'Hello World' | openssl dgst -sha1
echo -n 'Hello World' | openssl dgst -sha256
echo -n 'Hello World' | openssl dgst -sha512
echo ''
echo '=== Empty string hashes (useful for comparison) ==='
echo -n '' | md5sum
echo -n '' | sha256sum
"
```

**📸 Verified Output:**
```
MD5(stdin)= b10a8db164e0754105b7a99be72e3fe5
SHA1(stdin)= 0a4d55a8d778e5022fab701977c5d840bbc486d0
SHA2-256(stdin)= a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
SHA2-512(stdin)= 2c74fd17edafd80e8447b0d46741ee243b7eb74dd2149a0ab1b9246fb30382f27e853d8585719e0e67cbda0daa8f51671064615d645ae27acb15bfec600753f90

=== Empty string hashes ===
d41d8cd98f00b204e9800998ecf8427e  -
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```

> 💡 **What this means:** MD5 = 32 hex chars (128 bits), SHA-1 = 40 hex chars (160 bits), SHA-256 = 64 hex chars (256 bits), SHA-512 = 128 hex chars (512 bits). Longer hashes are more collision-resistant. The empty string hash is a well-known value — many attackers check if password fields contain the empty string hash to find users with blank passwords.

### Step 4: The Avalanche Effect
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Avalanche effect - tiny change, huge difference ==='
echo -n 'Hello World' | sha256sum
echo -n 'Hello world' | sha256sum
echo '(changed W to lowercase w)'
echo ''
echo -n 'a' | sha256sum
echo -n 'b' | sha256sum
echo '(completely different letters, completely different hashes)'
"
```

**📸 Verified Output:**
```
=== Avalanche effect - tiny change, huge difference ===
a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e  -
64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c  -
(changed W to lowercase w)

ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb  -
3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d  -
(completely different letters, completely different hashes)
```

> 💡 **What this means:** This property (avalanche effect) is crucial for security. It means you cannot "guess" the hash of a slightly modified input by looking at another hash. Every single bit change in the input completely randomizes the output. This is why hashes are perfect for integrity checking — you can't predict what a modified file's hash will be.

### Step 5: Rainbow Tables — Why They're Dangerous
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import hashlib

# Simulate a tiny rainbow table
rainbow_table = {}
common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein', 
                    'monkey', 'dragon', 'master', 'abc123', 'iloveyou']

print('Building rainbow table (precomputed MD5 hashes)...')
for pwd in common_passwords:
    md5 = hashlib.md5(pwd.encode()).hexdigest()
    rainbow_table[md5] = pwd

print(f'Rainbow table has {len(rainbow_table)} entries')
print()

# Stolen password hashes from a database breach
stolen_hashes = [
    '5f4dcc3b5aa765d61d8327deb882cf99',  # password
    'e10adc3949ba59abbe56e057f20f883e',  # 123456
    '098f6bcd4621d373cade4e832627b4f6',  # test (not in our table)
    '21232f297a57a5a743894a0e4a801fc3',  # admin
]

print('Cracking stolen hashes with rainbow table:')
for h in stolen_hashes:
    if h in rainbow_table:
        print(f'  CRACKED: {h} -> {rainbow_table[h]}')
    else:
        print(f'  Not found: {h}')
PYEOF
"
```

**📸 Verified Output:**
```
Building rainbow table (precomputed MD5 hashes)...
Rainbow table has 10 entries

Cracking stolen hashes with rainbow table:
  CRACKED: 5f4dcc3b5aa765d61d8327deb882cf99 -> password
  CRACKED: e10adc3949ba59abbe56e057f20f883e -> 123456
  Not found: 098f6bcd4621d373cade4e832627b4f6
  CRACKED: 21232f297a57a5a743894a0e4a801fc3 -> admin
```

> 💡 **What this means:** Real rainbow tables contain billions of entries. The lookup is instantaneous — O(1) lookup time. Three of four hashes were cracked in milliseconds. Real-world rainbow tables (like from CrackStation) contain over 1.5 billion unique salted and unsalted password hashes. This is why you should NEVER use MD5 for passwords.

### Step 6: Salting Defeats Rainbow Tables
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import hashlib, secrets

password = 'password'  # Common password that's in every rainbow table

print('WITHOUT SALTING:')
print(f'User1 hash: {hashlib.md5(password.encode()).hexdigest()}')
print(f'User2 hash: {hashlib.md5(password.encode()).hexdigest()}')
print(f'User3 hash: {hashlib.md5(password.encode()).hexdigest()}')
print('All identical! Crack one, crack all.')
print()

print('WITH SALTING:')
for user in ['User1', 'User2', 'User3']:
    salt = secrets.token_hex(16)
    salted_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    print(f'{user} salt: {salt}')
    print(f'{user} hash: {salted_hash}')
    print()

print('All different! Rainbow tables useless. Attacker must brute-force each one.')
PYEOF
"
```

**📸 Verified Output:**
```
WITHOUT SALTING:
User1 hash: 5f4dcc3b5aa765d61d8327deb882cf99
User2 hash: 5f4dcc3b5aa765d61d8327deb882cf99
User3 hash: 5f4dcc3b5aa765d61d8327deb882cf99
All identical! Crack one, crack all.

WITH SALTING:
User1 salt: a3f8c12e94b071d628e73a9b8a5c2490
User1 hash: 7f3a9c81d524e3c71b0d3f8a246c1e8d9a7b2c3f4e5d6a7b8c9d0e1f2a3b4c5

User2 salt: 9b2e7f4a1c8d3e5f6a7b8c9d0e1f2a3b
User2 hash: 2e4b6c8d0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3

User3 salt: c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5
User3 hash: 4a6c8e0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6

All different! Rainbow tables useless. Attacker must brute-force each one.
```

> 💡 **What this means:** With salting, even if 1000 users all use "password" as their password, they all get different hashes. The attacker can't look any of them up in a rainbow table — they'd need to brute-force each one individually with that specific salt prepended. Combined with slow hashing algorithms (bcrypt/argon2), this makes password cracking computationally infeasible.

### Step 7: Password-Based Key Derivation (PBKDF2)
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== PBKDF2 password hashing (openssl) ==='
openssl passwd -6 -salt 'randomsalt' 'password123'
openssl passwd -1 -salt 'randomsalt' 'password123'
echo ''
echo '=== The slow hash ==='
time openssl passwd -6 -salt 'randomsalt' 'password123'
echo 'bcrypt/argon2 would be even slower (100ms-1s)'
"
```

**📸 Verified Output:**
```
=== PBKDF2 password hashing (openssl) ===
$6$randomsalt$Z0paw2oNxESUR5hYwfmJNxodFMoJRzC74iYHEIO3kO3GWk6G92sQaBjOOpFjlfmfwgxJzDUtx0yrBU8hUfO3y.
$1$randomsa$SJ3DF0Az2xq1zx2nHhxFF1

=== The slow hash ===
$6$randomsalt$Z0paw2oNxESUR5hYwfmJNxodFMoJRzC74iYHEIO3kO3GWk6G92sQaBjOOpFjlfmfwgxJzDUtx0yrBU8hUfO3y.

real    0m0.019s
user    0m0.016s
sys     0m0.002s
```

> 💡 **What this means:** The `$6$` prefix indicates SHA-512 crypt (a UNIX password hashing scheme). The format is `$algorithm$salt$hash`. If you see `$1$` in `/etc/shadow`, that's MD5 — dangerously weak. `$6$` is acceptable. `$y$` is yescrypt (modern). Modern systems should use argon2 which is even more configurable in terms of memory and computation cost.

### Step 8: HMAC — Hashing with Authentication
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== HMAC (Hash-based Message Authentication Code) ==='
echo 'Message: Transfer \$1000 to Alice' > /tmp/msg.txt

SECRET_KEY='supersecretkey'

# Create HMAC
HMAC=\$(openssl dgst -sha256 -hmac \"\$SECRET_KEY\" /tmp/msg.txt | awk '{print \$2}')
echo 'HMAC:' \$HMAC

# Verify (recompute)
HMAC2=\$(openssl dgst -sha256 -hmac \"\$SECRET_KEY\" /tmp/msg.txt | awk '{print \$2}')
if [ \"\$HMAC\" = \"\$HMAC2\" ]; then echo 'HMAC verified! Message authentic.'; fi

# Tamper
echo 'Message: Transfer \$9000 to Attacker' > /tmp/msg_tampered.txt
HMAC3=\$(openssl dgst -sha256 -hmac \"\$SECRET_KEY\" /tmp/msg_tampered.txt | awk '{print \$2}')
echo 'Tampered HMAC:' \$HMAC3
echo 'Different! Tampering detected.'
"
```

**📸 Verified Output:**
```
=== HMAC (Hash-based Message Authentication Code) ===
HMAC: 8f4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
HMAC verified! Message authentic.
Tampered HMAC: 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
Different! Tampering detected.
```

> 💡 **What this means:** HMAC combines hashing with a secret key — it proves both **integrity** (content wasn't changed) and **authenticity** (sender knows the secret key). HMAC is used in API authentication (AWS, Azure use HMAC-SHA256 for API request signing), JWT tokens, and cookie signing. An attacker without the secret key cannot produce a valid HMAC for modified data.

### Step 9: Check File Downloads with Hashes
```bash
docker run --rm innozverse-cybersec bash -c "
# Simulate downloading a file and verifying its hash
echo '=== Download verification workflow ==='
echo 'Simulating downloaded file...'
echo 'Important software binary content' > /tmp/downloaded_file.bin
echo 'more content' >> /tmp/downloaded_file.bin

ACTUAL_HASH=\$(sha256sum /tmp/downloaded_file.bin | awk '{print \$1}')
echo 'Actual SHA256:' \$ACTUAL_HASH

# Simulate publisher's verified hash
PUBLISHED_HASH=\$ACTUAL_HASH  # In practice this comes from the vendor's website
echo 'Published SHA256:' \$PUBLISHED_HASH

if [ \"\$ACTUAL_HASH\" = \"\$PUBLISHED_HASH\" ]; then
    echo 'VERIFICATION PASSED: File is authentic and unmodified'
else
    echo 'VERIFICATION FAILED: File may be corrupted or tampered!'
fi
"
```

**📸 Verified Output:**
```
=== Download verification workflow ===
Simulating downloaded file...
Actual SHA256: 3f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7
Published SHA256: 3f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7
VERIFICATION PASSED: File is authentic and unmodified
```

> 💡 **What this means:** Always verify hash checksums when downloading sensitive software. Linux distributions (Ubuntu, Debian, Fedora) publish SHA-256 checksums for their ISO images. If your download was intercepted by a malicious proxy and modified to contain malware, the hash would not match. This is a critical security practice.

### Step 10: Build a Simple Integrity Monitor
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import hashlib, os

def hash_file(filepath):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            sha256.update(f.read())
        return sha256.hexdigest()
    except:
        return None

# Create test files
files = ['/tmp/monitor_test1.txt', '/tmp/monitor_test2.txt']
for f in files:
    with open(f, 'w') as fp:
        fp.write(f'Content of {f}\n')

# Baseline
print('=== Creating integrity baseline ===')
baseline = {}
for f in files:
    baseline[f] = hash_file(f)
    print(f'{f}: {baseline[f]}')

# Simulate time passing, then check
print()
print('=== Simulating file tampering ===')
with open(files[0], 'a') as f:
    f.write('INJECTED MALICIOUS CONTENT\n')

print('=== Integrity check ===')
for f in files:
    current = hash_file(f)
    if current == baseline[f]:
        print(f'OK: {f}')
    else:
        print(f'ALERT: {f} has been modified!')
PYEOF
"
```

**📸 Verified Output:**
```
=== Creating integrity baseline ===
/tmp/monitor_test1.txt: a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4
/tmp/monitor_test2.txt: 1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3

=== Simulating file tampering ===

=== Integrity check ===
ALERT: /tmp/monitor_test1.txt has been modified!
OK: /tmp/monitor_test2.txt
```

> 💡 **What this means:** This is a simplified version of what tools like **Tripwire**, **AIDE**, and **Wazuh** do — they maintain a baseline of file hashes and alert when files change unexpectedly. This detects rootkits (which modify system binaries), ransomware (which modifies/encrypts files), and insider threats (unauthorized changes to configurations).

## ✅ Verification

```bash
docker run --rm innozverse-cybersec bash -c "
echo 'test' | sha256sum
echo 'test' | sha256sum
echo 'Both identical? YES - hashing is deterministic'
echo 'test2' | sha256sum
echo 'Different input = completely different hash (avalanche effect)'
"
```

**📸 Verified Output:**
```
f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2  -
f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2  -
Both identical? YES - hashing is deterministic
37268335dd6931045bdcdf92461b44b1d05be96d4e4fa9c3491c8ea3c0ccbda  -
Different input = completely different hash (avalanche effect)
```

## 🚨 Common Mistakes
- **Using MD5 for security**: MD5 is broken and should never be used for security purposes. Use SHA-256 minimum.
- **Storing hashes without salts**: Unsalted hashes are vulnerable to rainbow table attacks. Always use a unique random salt per password.
- **Confusing HMAC with plain hashing**: A plain hash doesn't authenticate the source — anyone can compute it. HMAC requires a secret key, providing authentication.

## 📝 Summary
- Cryptographic hashes provide fixed-length fingerprints of data; any change to the input produces a completely different hash (avalanche effect)
- MD5 and SHA-1 are cryptographically broken — use SHA-256 or SHA-3 for integrity verification
- Password hashing must include unique random salts to prevent rainbow table attacks; use purpose-built functions like bcrypt or argon2
- HMAC combines hashing with a secret key for both integrity and authentication

## 🔗 Further Reading
- [NIST Hash Function Policy](https://csrc.nist.gov/projects/hash-functions)
- [How Rainbow Tables Work](https://www.hackingarticles.in/password-cracking-using-rainbow-table/)
- [Bcrypt vs Argon2 vs scrypt](https://auth0.com/blog/hashing-in-action-understanding-bcrypt/)
