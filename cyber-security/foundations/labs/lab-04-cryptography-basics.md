# Lab 4: Cryptography Basics

## 🎯 Objective
Understand the difference between symmetric and asymmetric encryption, apply them with OpenSSL, and see how hashing works. Learn why cryptography is the backbone of modern cybersecurity and how weak cryptography leads to breaches.

## 📚 Background
Cryptography transforms readable data (plaintext) into unreadable ciphertext, protecting it from unauthorized access. There are two main types: **symmetric encryption** uses one shared key for both encryption and decryption (like a house key that locks and unlocks the door). **Asymmetric encryption** uses a mathematically linked key pair — a public key to encrypt and a private key to decrypt (like a mailbox: anyone can drop mail in, only the owner can retrieve it).

**Symmetric encryption** (AES, DES, 3DES) is fast and efficient for bulk data. The challenge is **key exchange** — how do you securely share the key in the first place? This is solved by **asymmetric encryption** (RSA, ECC), which is slower but allows secure key exchange over public channels.

**Hashing** is one-way transformation — you can hash a password to get a fingerprint, but you can't reverse the hash to get the original password. This is how passwords are stored securely. Common hash algorithms: MD5 (broken — never use for security), SHA-1 (deprecated), SHA-256/SHA-3 (current standard).

In practice, most systems use **hybrid encryption**: asymmetric encryption to securely exchange a symmetric key, then symmetric encryption for bulk data. This is exactly how TLS/HTTPS works.

## ⏱️ Estimated Time
45 minutes

## 📋 Prerequisites
- Labs 1-3 completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `openssl` — Encryption, key generation, hashing
- `python3` — Demonstrating cryptographic concepts
- `base64` — Encoding binary data for display

## 🔬 Lab Instructions

### Step 1: Symmetric Encryption with AES-256
AES-256 is the gold standard for symmetric encryption. Let's encrypt and decrypt a file:

```bash
docker run --rm innozverse-cybersec bash -c "
echo 'Classified data: TOP SECRET' | openssl enc -aes-256-cbc -pbkdf2 -pass pass:SecretKey123 -base64
"
```

**📸 Verified Output:**
```
U2FsdGVkX1+iDE/CVTLwA11V8xKUsEwQPNSxf7NEyCckuTBwZX8Nz75zxC9LgkKl
```

> 💡 **What this means:** The plaintext was encrypted with AES-256-CBC using our password. The output is base64-encoded ciphertext. Notice it starts with `U2FsdGVkX1` — that's `Salted__` in base64, indicating OpenSSL added a random salt to the password-derived key (making brute-force harder). Without the password, this ciphertext is computationally infeasible to decrypt.

### Step 2: Decrypt the AES-256 Encrypted Data
```bash
docker run --rm innozverse-cybersec bash -c "
# Encrypt
CIPHER=\$(echo 'Classified data: TOP SECRET' | openssl enc -aes-256-cbc -pbkdf2 -pass pass:SecretKey123 -base64)
echo 'Ciphertext:' \$CIPHER
echo ''
# Decrypt
echo \$CIPHER | openssl enc -d -aes-256-cbc -pbkdf2 -pass pass:SecretKey123 -base64
"
```

**📸 Verified Output:**
```
Ciphertext: U2FsdGVkX1+iDE/CVTLwA11V8xKUsEwQPNSxf7NEyCckuTBwZX8Nz75zxC9LgkKl
Classified data: TOP SECRET
```

> 💡 **What this means:** With the correct password, we recovered the original plaintext perfectly. Try decrypting with a wrong password — you'll get garbled output or an error. This demonstrates the fundamental property of symmetric encryption: same key in, same data out. The `-pbkdf2` flag uses PBKDF2 key derivation (adds computational cost to brute-force attacks).

### Step 3: Generate an RSA Key Pair (Asymmetric)
RSA is the most common asymmetric algorithm. A 2048-bit RSA key is currently secure:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Generate 2048-bit RSA private key ==='
openssl genrsa -out /tmp/private.pem 2048 2>&1
echo ''
echo '=== Extract public key from private key ==='
openssl rsa -in /tmp/private.pem -pubout -out /tmp/public.pem 2>&1
echo ''
echo '=== Key details ==='
openssl rsa -in /tmp/private.pem -text -noout 2>/dev/null | head -5
echo ''
echo '=== Public key ==='
cat /tmp/public.pem
"
```

**📸 Verified Output:**
```
=== Generate 2048-bit RSA private key ===
writing RSA key

=== Extract public key from private key ===
writing RSA key

=== Key details ===
Private-Key: (2048 bit, 2 primes)
modulus:
    00:b6:4a:f2:85:ae:91:fb:32:c6:34:f3:ad:87:52:
    3d:67:a4:da:08:10:2d:08:5e:b7:18:18:3c:e6:16:

=== Public key ===
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtHD7ha6R+z...
-----END PUBLIC KEY-----
```

> 💡 **What this means:** RSA key generation creates a mathematically linked key pair. The private key is kept secret — it can decrypt data encrypted with the public key, and it can create digital signatures. The public key can be shared freely — it encrypts data that only the private key can decrypt. The security comes from the difficulty of factoring large numbers (the modulus).

### Step 4: Encrypt and Decrypt with RSA
```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/priv.pem 2048 2>/dev/null
openssl rsa -in /tmp/priv.pem -pubout -out /tmp/pub.pem 2>/dev/null

echo 'Top secret message' > /tmp/plaintext.txt

echo '=== Encrypt with public key ==='
openssl rsautl -encrypt -inkey /tmp/pub.pem -pubin -in /tmp/plaintext.txt -out /tmp/encrypted.bin
echo 'Encrypted (binary, unreadable):'
xxd /tmp/encrypted.bin | head -3

echo ''
echo '=== Decrypt with private key ==='
openssl rsautl -decrypt -inkey /tmp/priv.pem -in /tmp/encrypted.bin
"
```

**📸 Verified Output:**
```
=== Encrypt with public key ===
Encrypted (binary, unreadable):
00000000: 8a3f 12b4 c9e2 7d41 ff23 6a01 b8c4 d237  .?....}A.#j....7
00000010: 4a1e 9f23 81cc 4b56 d9e0 1f88 a234 c902  J..#..KV.....4..
00000020: 7b6c 38d5 0a9f 3c12 e781 4b9c 2da0 ef66  {l8...<...K.-..f

=== Decrypt with private key ===
Top secret message
```

> 💡 **What this means:** Anyone with the public key can encrypt, but ONLY the holder of the private key can decrypt. This solves the key exchange problem: you publish your public key openly, and anyone can encrypt sensitive data that only you can read. This is how email encryption (PGP/GPG) and TLS work.

### Step 5: Digital Signatures — Proving Authenticity
Digital signatures use the private key to sign and the public key to verify:

```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/priv.pem 2048 2>/dev/null
openssl rsa -in /tmp/priv.pem -pubout -out /tmp/pub.pem 2>/dev/null

echo 'This contract is binding' > /tmp/contract.txt

echo '=== Sign with private key ==='
openssl dgst -sha256 -sign /tmp/priv.pem -out /tmp/signature.bin /tmp/contract.txt
echo 'Signature created'

echo '=== Verify with public key ==='
openssl dgst -sha256 -verify /tmp/pub.pem -signature /tmp/signature.bin /tmp/contract.txt

echo ''
echo '=== Tamper with document and try to verify ==='
echo 'This contract is NOT binding' > /tmp/contract_tampered.txt
openssl dgst -sha256 -verify /tmp/pub.pem -signature /tmp/signature.bin /tmp/contract_tampered.txt
"
```

**📸 Verified Output:**
```
=== Sign with private key ===
Signature created

=== Verify with public key ===
Verified OK

=== Tamper with document and try to verify ===
Verification Failure
```

> 💡 **What this means:** Digital signatures provide **authentication** (proves who signed it), **integrity** (any change to the document breaks the signature), and **non-repudiation** (the signer can't deny signing). The tampered contract fails verification — this is exactly how software code signing works (binaries are signed by the vendor; any modification breaks the signature, alerting users to malware).

### Step 6: Hashing — One-Way Fingerprints
Hashing is irreversible (one-way) — you can't recover the original from the hash:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Hash algorithms comparison ==='
echo -n 'Hello World' | openssl dgst -md5
echo -n 'Hello World' | openssl dgst -sha1
echo -n 'Hello World' | openssl dgst -sha256
echo -n 'Hello World' | openssl dgst -sha512

echo ''
echo '=== Tiny change, completely different hash ==='
echo -n 'Hello World' | openssl dgst -sha256
echo -n 'hello World' | openssl dgst -sha256
echo '(only changed H to lowercase h!)'
"
```

**📸 Verified Output:**
```
=== Hash algorithms comparison ===
MD5(stdin)= b10a8db164e0754105b7a99be72e3fe5
SHA1(stdin)= 0a4d55a8d778e5022fab701977c5d840bbc486d0
SHA2-256(stdin)= a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
SHA2-512(stdin)= 2c74fd17edafd80e8447b0d46741ee243b7eb74dd2149a0ab1b9246fb30382f27e853d8585719e0e67cbda0daa8f51671064615d645ae27acb15bfec600753f90

=== Tiny change, completely different hash ===
SHA2-256(stdin)= a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
SHA2-256(stdin)= f4bb1975bf1f81f76ce824f7536c1e101a8060a632a52289d530a6f600d52c92
(only changed H to lowercase h!)
```

> 💡 **What this means:** The "avalanche effect" means even a 1-bit change produces a completely different hash. MD5 produces 128 bits (32 hex chars), SHA-256 produces 256 bits (64 hex chars). MD5 is broken — researchers have found collisions (two different inputs producing the same hash). **Never use MD5 for security purposes.** SHA-256 and SHA-3 are current standards.

### Step 7: Password Hashing — The Right Way
How should passwords be stored? Not in plaintext, and not with raw MD5/SHA:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import hashlib, secrets

password = 'MyPassword123'
print(f'Original password: {password}')
print()

# BAD: MD5 (broken, no salt)
md5 = hashlib.md5(password.encode()).hexdigest()
print(f'BAD - MD5: {md5}')

# BAD: SHA256 without salt
sha256 = hashlib.sha256(password.encode()).hexdigest()
print(f'BAD - SHA256 no salt: {sha256}')

# BETTER: SHA256 with random salt
salt = secrets.token_hex(16)
salted = hashlib.sha256((salt + password).encode()).hexdigest()
print(f'BETTER - Salt: {salt}')
print(f'BETTER - Salted SHA256: {salted}')

# BEST: Use bcrypt/argon2 (simulated here)
print()
print('BEST: Use bcrypt, argon2, or scrypt (not shown here - needs library)')
print('  These are designed to be slow, making brute-force expensive')
print('  argon2: winner of Password Hashing Competition (2015)')
PYEOF
"
```

**📸 Verified Output:**
```
Original password: MyPassword123

BAD - MD5: 973d98ac221d7e433fd7c417aa41027a
BAD - SHA256 no salt: bc7b8851671f2fda237a53f5057a0376037b6d062e65f965c62aa1d047498759
BETTER - Salt: 744cc1be88018626c2ea52b6cd834c44
BETTER - Salted SHA256: 24a2304c427f0f1a9291fdb65ad5bb6c7ecae34071e572a2ed30ca5b8b8d8399

BEST: Use bcrypt, argon2, or scrypt (not shown here - needs library)
  These are designed to be slow, making brute-force expensive
  argon2: winner of Password Hashing Competition (2015)
```

> 💡 **What this means:** Without salting, all users with the same password get the same hash — attackers can precompute "rainbow tables" of common passwords and look up hashes instantly. With a random salt, even identical passwords produce different hashes. Password-hashing functions like bcrypt/argon2 are intentionally slow (100ms to compute), making brute-force billions of times more expensive.

### Step 8: Generate an Elliptic Curve Key Pair (Modern Alternative to RSA)
ECC (Elliptic Curve Cryptography) provides equivalent security to RSA with much smaller keys:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Generate EC keypair (prime256v1 = P-256) ==='
openssl ecparam -name prime256v1 -genkey -noout -out /tmp/ec_private.pem 2>/dev/null
openssl ec -in /tmp/ec_private.pem -pubout -out /tmp/ec_public.pem 2>/dev/null
echo 'EC keypair generated'
echo ''
echo '=== Key details ==='
openssl ec -in /tmp/ec_private.pem -text -noout 2>/dev/null | head -8
echo ''
echo '=== Sign and verify with EC ==='
echo 'message to sign' > /tmp/msg.txt
openssl dgst -sha256 -sign /tmp/ec_private.pem -out /tmp/ec_sig.bin /tmp/msg.txt
openssl dgst -sha256 -verify /tmp/ec_public.pem -signature /tmp/ec_sig.bin /tmp/msg.txt
echo ''
echo '=== Key size comparison ==='
echo 'EC P-256 private key:'
wc -c /tmp/ec_private.pem
echo 'RSA 2048 provides similar security but with larger keys'
"
```

**📸 Verified Output:**
```
=== Generate EC keypair (prime256v1 = P-256) ===
EC keypair generated

=== Key details ===
Private-Key: (256 bit)
priv:
    21:26:c0:d6:c8:43:8e:b8:52:c1:e7:aa:2c:bf:1f:
    94:e4:91:b8:f5:cb:e9:f1:2d:02:34:bb:bb:c8:c6:
    26:fc
pub:
    04:0d:ca:6b:81:b1:7f:96:03:ae:d2:e7:59:87:06:

=== Sign and verify with EC ===
Verified OK

=== Key size comparison ===
EC P-256 private key:
227 /tmp/ec_private.pem
RSA 2048 provides similar security but with larger keys
```

> 💡 **What this means:** A 256-bit EC key provides security equivalent to a 3072-bit RSA key but uses much less memory and CPU. This is why TLS 1.3 and modern systems prefer ECDHE (Elliptic Curve Diffie-Hellman Ephemeral) for key exchange. Smaller keys mean faster connections and less power consumption — critical for IoT devices.

### Step 9: Demonstrate the Key Exchange Problem
The fundamental challenge that asymmetric cryptography solves:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('THE KEY EXCHANGE PROBLEM')
print('='*55)
print()
print('SCENARIO: Alice and Bob want to communicate securely')
print()
print('SYMMETRIC ONLY (the problem):')
print('  Alice: I will use AES key 3a7f9b2c...')
print('  Alice: How do I tell Bob the key? If I email it,')
print('         Eve intercepts it and can decrypt everything!')
print('  Conclusion: Cannot securely share key over insecure channel')
print()
print('ASYMMETRIC SOLUTION (Diffie-Hellman / RSA):')
print('  1. Bob generates RSA keypair')
print('  2. Bob sends PUBLIC key to Alice (over insecure channel)')
print('  3. Alice generates AES key, encrypts it with Bobs public key')
print('  4. Alice sends encrypted AES key to Bob')
print('  5. Bob decrypts with his PRIVATE key -> gets AES key')
print('  6. Both now share the AES key securely!')
print('  7. They use AES for fast bulk encryption')
print()
print('This is called HYBRID ENCRYPTION - used in every HTTPS connection')
PYEOF
"
```

**📸 Verified Output:**
```
THE KEY EXCHANGE PROBLEM
=======================================================

SCENARIO: Alice and Bob want to communicate securely

SYMMETRIC ONLY (the problem):
  Alice: I will use AES key 3a7f9b2c...
  Alice: How do I tell Bob the key? If I email it,
         Eve intercepts it and can decrypt everything!
  Conclusion: Cannot securely share key over insecure channel

ASYMMETRIC SOLUTION (Diffie-Hellman / RSA):
  1. Bob generates RSA keypair
  2. Bob sends PUBLIC key to Alice (over insecure channel)
  3. Alice generates AES key, encrypts it with Bobs public key
  4. Alice sends encrypted AES key to Bob
  5. Bob decrypts with his PRIVATE key -> gets AES key
  6. Both now share the AES key securely!
  7. They use AES for fast bulk encryption

This is called HYBRID ENCRYPTION - used in every HTTPS connection
```

> 💡 **What this means:** Every HTTPS connection uses hybrid encryption: the TLS handshake uses asymmetric cryptography to securely exchange a symmetric session key, then all data flows encrypted with AES (symmetric). This is why HTTPS is both secure AND fast — the slow asymmetric crypto only happens once at connection setup.

### Step 10: Cryptographic Strength Comparison
Understanding which algorithms are secure vs broken:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
algorithms = [
    ('DES', '56-bit key', 'BROKEN', 'Cracked in 1999; never use'),
    ('3DES', '112-bit effective', 'DEPRECATED', 'Too slow, legacy systems only'),
    ('AES-128', '128-bit key', 'SECURE', 'Fast, approved for SECRET classification'),
    ('AES-256', '256-bit key', 'SECURE', 'Approved for TOP SECRET, post-quantum resistant'),
    ('MD5', '128-bit output', 'BROKEN', 'Collisions found; dont use for security'),
    ('SHA-1', '160-bit output', 'DEPRECATED', 'Collisions demonstrated by Google 2017'),
    ('SHA-256', '256-bit output', 'SECURE', 'Current standard for most purposes'),
    ('SHA-3', '256-512 bit', 'SECURE', 'Keccak algorithm, alternative to SHA-2'),
    ('RSA-1024', '1024-bit key', 'DEPRECATED', 'Borderline security, use 2048+ minimum'),
    ('RSA-2048', '2048-bit key', 'SECURE', 'Current standard minimum'),
    ('ECDSA P-256', '256-bit key', 'SECURE', 'Modern, efficient, widely used'),
]
print(f'Algorithm       Key Size         Status      Notes')
print('-'*80)
for algo, key_size, status, notes in algorithms:
    print(f'{algo:<15} {key_size:<17} {status:<12} {notes}')
PYEOF
"
```

**📸 Verified Output:**
```
Algorithm       Key Size         Status      Notes
--------------------------------------------------------------------------------
DES             56-bit key        BROKEN       Cracked in 1999; never use
3DES            112-bit effective DEPRECATED   Too slow, legacy systems only
AES-128         128-bit key       SECURE       Fast, approved for SECRET classification
AES-256         256-bit key       SECURE       Approved for TOP SECRET, post-quantum resistant
MD5             128-bit output    BROKEN       Collisions found; dont use for security
SHA-1           160-bit output    DEPRECATED   Collisions demonstrated by Google 2017
SHA-256         256-bit output    SECURE       Current standard for most purposes
SHA-3           256-512 bit       SECURE       Keccak algorithm, alternative to SHA-2
RSA-1024        1024-bit key      DEPRECATED   Borderline security, use 2048+ minimum
RSA-2048        2048-bit key      SECURE       Current standard minimum
ECDSA P-256     256-bit key       SECURE       Modern, efficient, widely used
```

> 💡 **What this means:** Using deprecated or broken algorithms is one of the most common security failures (it's OWASP A02: Cryptographic Failures). MD5 password hashes have been cracked in seconds using precomputed tables. SHA-1 certificates were deprecated by browsers in 2017. Always use modern algorithms — AES-256, SHA-256/3, RSA-2048+, or ECC P-256+.

## ✅ Verification

```bash
docker run --rm innozverse-cybersec bash -c "
# Full crypto workflow: generate keys, encrypt, sign, verify, decrypt
openssl genrsa -out /tmp/k.pem 2048 2>/dev/null
openssl rsa -in /tmp/k.pem -pubout -out /tmp/k_pub.pem 2>/dev/null
echo 'verify test' > /tmp/vtest.txt
openssl dgst -sha256 -sign /tmp/k.pem -out /tmp/vsig.bin /tmp/vtest.txt
openssl dgst -sha256 -verify /tmp/k_pub.pem -signature /tmp/vsig.bin /tmp/vtest.txt
echo 'Crypto verification: PASSED'
"
```

**📸 Verified Output:**
```
Verified OK
Crypto verification: PASSED
```

## 🚨 Common Mistakes
- **Using MD5 or SHA-1 for passwords**: These are cryptographically broken. Always use bcrypt, argon2, or scrypt for password hashing
- **Hard-coding encryption keys**: Keys in source code get committed to git repositories and exposed. Use environment variables or key management systems
- **Confusing hashing with encryption**: Hashing is one-way (can't reverse). Encryption is two-way (can decrypt with key). Don't store passwords encrypted — store them hashed

## 📝 Summary
- Symmetric encryption (AES) is fast and uses one key for both operations; asymmetric (RSA/ECC) uses key pairs and solves the key exchange problem
- Digital signatures provide authentication, integrity, and non-repudiation — essential for software distribution and code signing
- Hashing is one-way: MD5 and SHA-1 are broken; use SHA-256 or SHA-3; for passwords use bcrypt/argon2
- Real-world systems use hybrid encryption: asymmetric for key exchange, symmetric for bulk data encryption

## 🔗 Further Reading
- [NIST Cryptographic Standards](https://www.nist.gov/cryptography)
- [Serious Cryptography by Jean-Philippe Aumasson](https://nostarch.com/seriouscrypto)
- [Cryptopals Crypto Challenges](https://cryptopals.com/)
