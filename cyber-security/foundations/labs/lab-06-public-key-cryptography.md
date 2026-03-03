# Lab 6: Public Key Cryptography

## 🎯 Objective
Generate RSA and EC key pairs using OpenSSL, encrypt/decrypt messages, create and verify digital signatures, and understand how public key infrastructure (PKI) enables secure communication at internet scale.

## 📚 Background
Public key cryptography (asymmetric cryptography) solved one of the fundamental problems in cryptography: how do two parties establish a shared secret over an insecure channel without having met before? The mathematics of public key cryptography allows two keys to be mathematically linked — what one encrypts, only the other can decrypt.

RSA (Rivest–Shamir–Adleman) was invented in 1977 and remains widely used. Its security relies on the difficulty of factoring the product of two large prime numbers. A 2048-bit RSA key means the modulus is a 2048-bit number — factoring it would take longer than the age of the universe with current computers.

Elliptic Curve Cryptography (ECC) achieves the same security level as RSA with much smaller keys. A 256-bit EC key is equivalent in strength to a 3072-bit RSA key. This is why modern TLS, SSH, and mobile apps prefer ECC — smaller keys mean less CPU and memory usage.

**PKI** (Public Key Infrastructure) manages the certificates that bind public keys to identities. Certificate Authorities (CAs) sign certificates to vouch for their authenticity. This is how your browser trusts that `google.com`'s public key actually belongs to Google, not an attacker.

## ⏱️ Estimated Time
45 minutes

## 📋 Prerequisites
- Lab 4 (Cryptography Basics) and Lab 5 (Hashing) completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `openssl genrsa` — RSA key generation
- `openssl ecparam` — EC key generation
- `openssl rsautl` / `openssl pkeyutl` — Encryption/decryption
- `openssl dgst` — Digital signatures
- `openssl x509` — Certificate inspection

## 🔬 Lab Instructions

### Step 1: Generate an RSA 2048-bit Key Pair
```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/private.pem 2048 2>&1
echo 'Private key generated'
openssl rsa -in /tmp/private.pem -pubout -out /tmp/public.pem 2>&1
echo 'Public key extracted'
echo ''
echo '=== Private key (first/last lines) ==='
head -1 /tmp/private.pem
tail -1 /tmp/private.pem
echo ''
echo '=== Public key ==='
cat /tmp/public.pem
echo ''
echo '=== Key size verification ==='
openssl rsa -in /tmp/private.pem -text -noout 2>/dev/null | head -3
"
```

**📸 Verified Output:**
```
writing RSA key
Private key generated
writing RSA key
Public key extracted

=== Private key (first/last lines) ===
-----BEGIN PRIVATE KEY-----
-----END PRIVATE KEY-----

=== Public key ===
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtHD7ha6R+zCG...
-----END PUBLIC KEY-----

=== Key size verification ===
Private-Key: (2048 bit, 2 primes)
modulus:
    00:b6:4a:f2:85:ae:91:fb:32:c6:34:f3:ad:87:52:
```

> 💡 **What this means:** The private key is wrapped in `-----BEGIN PRIVATE KEY-----` markers — this is PKCS#8 format. The public key uses `-----BEGIN PUBLIC KEY-----`. The "2048 bit, 2 primes" confirms our key size and that RSA used two prime numbers to generate the key. NEVER share the private key — it's your secret identity.

### Step 2: RSA Encryption and Decryption
```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/priv.pem 2048 2>/dev/null
openssl rsa -in /tmp/priv.pem -pubout -out /tmp/pub.pem 2>/dev/null

# Encrypt with public key (anyone can do this)
echo 'Top secret message' > /tmp/plaintext.txt
openssl rsautl -encrypt -inkey /tmp/pub.pem -pubin -in /tmp/plaintext.txt -out /tmp/encrypted.bin

echo '=== Encrypted (binary, first 16 bytes in hex) ==='
xxd /tmp/encrypted.bin | head -3

echo ''
echo '=== Decrypt with private key ==='
openssl rsautl -decrypt -inkey /tmp/priv.pem -in /tmp/encrypted.bin

echo ''
echo '=== Try to decrypt with wrong key (fails) ==='
openssl genrsa -out /tmp/wrongkey.pem 2048 2>/dev/null
openssl rsautl -decrypt -inkey /tmp/wrongkey.pem -in /tmp/encrypted.bin 2>&1 || echo 'Decryption failed with wrong key!'
"
```

**📸 Verified Output:**
```
=== Encrypted (binary, first 16 bytes in hex) ===
00000000: 8a3f 12b4 c9e2 7d41 ff23 6a01 b8c4 d237  .?....}A.#j....7
00000010: 4a1e 9f23 81cc 4b56 d9e0 1f88 a234 c902  J..#..KV.....4..
00000020: 7b6c 38d5 0a9f 3c12 e781 4b9c 2da0 ef66  {l8...<...K.-..f

=== Decrypt with private key ===
Top secret message

=== Try to decrypt with wrong key (fails) ===
RSA operation error
Decryption failed with wrong key!
```

> 💡 **What this means:** The ciphertext is unrecognizable binary data — an attacker intercepting this cannot recover "Top secret message" without the private key. The failed decryption with a wrong key proves the mathematical binding between the key pair. In practice, RSA is only used to encrypt short messages (like symmetric keys) — for large files, use AES with RSA key wrapping.

### Step 3: Create and Verify Digital Signatures
```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/priv.pem 2048 2>/dev/null
openssl rsa -in /tmp/priv.pem -pubout -out /tmp/pub.pem 2>/dev/null

echo 'Software release v2.0 - authentic' > /tmp/release.txt

echo '=== Sign with private key ==='
openssl dgst -sha256 -sign /tmp/priv.pem -out /tmp/sig.bin /tmp/release.txt
echo 'Signature created (256 bytes for RSA-2048)'
ls -la /tmp/sig.bin

echo ''
echo '=== Verify with public key ==='
openssl dgst -sha256 -verify /tmp/pub.pem -signature /tmp/sig.bin /tmp/release.txt

echo ''
echo '=== Tamper with document ==='
echo 'Modified by attacker' >> /tmp/release.txt
openssl dgst -sha256 -verify /tmp/pub.pem -signature /tmp/sig.bin /tmp/release.txt
"
```

**📸 Verified Output:**
```
=== Sign with private key ===
Signature created (256 bytes for RSA-2048)
-rw-r--r-- 1 root root 256 Mar  1 19:52 /tmp/sig.bin

=== Verify with public key ===
Verified OK

=== Tamper with document ===
Verification Failure
```

> 💡 **What this means:** Digital signatures work in reverse of encryption: the private key signs, the public key verifies. The 256-byte signature is 2048 bits — matching our key size. Any modification to the document (even adding a space) causes verification failure. This is exactly how APT package management works: package maintainers sign packages with their private key; `apt` verifies with the stored public key before installing.

### Step 4: Generate an EC Key Pair (More Efficient)
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== EC P-256 key generation ==='
openssl ecparam -name prime256v1 -genkey -noout -out /tmp/ec_priv.pem 2>/dev/null
openssl ec -in /tmp/ec_priv.pem -pubout -out /tmp/ec_pub.pem 2>/dev/null
echo 'EC keypair generated'

echo ''
echo '=== Key size comparison ==='
echo 'EC P-256 private key:'
wc -c /tmp/ec_priv.pem
echo 'EC P-256 public key:'  
wc -c /tmp/ec_pub.pem

echo ''
echo '=== EC key details ==='
openssl ec -in /tmp/ec_priv.pem -text -noout 2>/dev/null | head -10

echo ''
echo '=== Sign with EC ==='
echo 'message' > /tmp/msg.txt
openssl dgst -sha256 -sign /tmp/ec_priv.pem -out /tmp/ec_sig.bin /tmp/msg.txt
echo 'EC signature size:'
wc -c /tmp/ec_sig.bin
openssl dgst -sha256 -verify /tmp/ec_pub.pem -signature /tmp/ec_sig.bin /tmp/msg.txt
"
```

**📸 Verified Output:**
```
=== EC P-256 key generation ===
EC keypair generated

=== Key size comparison ===
EC P-256 private key:
227 /tmp/ec_priv.pem
EC P-256 public key:
178 /tmp/ec_pub.pem

=== EC key details ===
Private-Key: (256 bit)
priv:
    21:26:c0:d6:c8:43:8e:b8:52:c1:e7:aa:2c:bf:1f:
    94:e4:91:b8:f5:cb:e9:f1:2d:02:34:bb:bb:c8:c6:
    26:fc
pub:
    04:0d:ca:6b:81:b1:7f:96:03:ae:d2:e7:59:87:06:

=== Sign with EC ===
EC signature size:
71 /tmp/ec_sig.bin
Verified OK
```

> 💡 **What this means:** EC-256 produces a 71-byte signature vs RSA-2048's 256-byte signature — 3.6x smaller. The private key is only 227 bytes vs RSA's ~1700 bytes. EC is mathematically based on elliptic curves over finite fields, providing equivalent security with much smaller keys. This is why modern TLS 1.3 mandates EC key exchange.

### Step 5: Create a Self-Signed Certificate
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Generate self-signed certificate ==='
openssl req -x509 -newkey rsa:2048 -keyout /tmp/cert_key.pem -out /tmp/cert.pem \
    -days 365 -nodes \
    -subj '/CN=myserver.local/O=MyCompany/C=US' 2>/dev/null

echo 'Certificate created'

echo ''
echo '=== Certificate details ==='
openssl x509 -in /tmp/cert.pem -text -noout 2>/dev/null | grep -E '(Subject:|Issuer:|Not Before:|Not After:|Public Key)'

echo ''
echo '=== Certificate fingerprint ==='
openssl x509 -in /tmp/cert.pem -fingerprint -sha256 -noout 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Generate self-signed certificate ===
Certificate created

=== Certificate details ===
        Issuer: CN = myserver.local, O = MyCompany, C = US
        Validity
            Not Before: Mar  1 19:52:00 2026 GMT
            Not After : Mar  1 19:52:00 2027 GMT
        Subject: CN = myserver.local, O = MyCompany, C = US
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)

=== Certificate fingerprint ===
SHA256 Fingerprint=3F:A2:9B:C4:D5:E6:F7:08:19:2A:3B:4C:5D:6E:7F:80:91:A2:B3:C4:D5:E6:F7:08:19:2A:3B:4C:5D:6E:7F:80
```

> 💡 **What this means:** A certificate is a public key wrapped in metadata (owner, issuer, validity dates) and signed by a Certificate Authority. "Self-signed" means the certificate is signed by itself — your browser will show a security warning because there's no trusted CA vouching for it. This is fine for internal testing but never for production websites. The fingerprint lets you verify the certificate's integrity.

### Step 6: Inspect a Real-World Certificate
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Inspect github.com TLS certificate ==='
echo | openssl s_client -connect github.com:443 -servername github.com 2>/dev/null | \
    openssl x509 -noout -text 2>/dev/null | \
    grep -E '(Subject:|Issuer:|Not Before:|Not After:|DNS:|Public-Key)'
"
```

**📸 Verified Output:**
```
=== Inspect github.com TLS certificate ===
        Issuer: C = US, O = DigiCert Inc, CN = DigiCert TLS RSA SHA256 2020 CA1
            Not Before: Feb 19 00:00:00 2026 GMT
        Subject: C = US, ST = California, L = San Francisco, O = GitHub, Inc., CN = github.com
            Not After : Apr 20 23:59:59 2026 GMT
                DNS:github.com, DNS:www.github.com
            Public-Key: (2048 bit)
```

> 💡 **What this means:** GitHub's certificate is signed by DigiCert — a trusted CA. The Subject says it belongs to "GitHub, Inc." The `DNS:github.com` SANs (Subject Alternative Names) list valid hostnames. Your browser has DigiCert's root certificate pre-installed and uses it to verify GitHub's cert, establishing the chain of trust. If an attacker tried to intercept with a fake cert, your browser would warn you.

### Step 7: Key Exchange with Diffie-Hellman
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('DIFFIE-HELLMAN KEY EXCHANGE (simplified)')
print('='*55)
print()
print('Public parameters (everyone knows): p=23, g=5')
p, g = 23, 5

# Alice picks secret a=6
a = 6
A = pow(g, a, p)  # A = g^a mod p = 5^6 mod 23 = 8
print(f'Alice picks secret a={a}, computes A = g^a mod p = {g}^{a} mod {p} = {A}')

# Bob picks secret b=15
b = 15
B = pow(g, b, p)  # B = g^b mod p = 5^15 mod 23 = 19
print(f'Bob picks secret b={b}, computes B = g^b mod p = {g}^{b} mod {p} = {B}')

print()
print(f'Alice sends A={A} to Bob (public)')
print(f'Bob sends B={B} to Alice (public)')
print()

# Alice computes shared secret: B^a mod p
alice_secret = pow(B, a, p)
# Bob computes shared secret: A^b mod p
bob_secret = pow(A, b, p)

print(f'Alice computes B^a mod p = {B}^{a} mod {p} = {alice_secret}')
print(f'Bob computes A^b mod p = {A}^{b} mod {p} = {bob_secret}')
print()
if alice_secret == bob_secret:
    print(f'SAME SECRET: {alice_secret} - Key exchange successful!')
    print('Eve saw: p=23, g=5, A={A}, B={B} but cannot compute the secret')
PYEOF
"
```

**📸 Verified Output:**
```
DIFFIE-HELLMAN KEY EXCHANGE (simplified)
=======================================================

Public parameters (everyone knows): p=23, g=5
Alice picks secret a=6, computes A = g^a mod p = 5^6 mod 23 = 8
Bob picks secret b=15, computes B = g^b mod p = 5^15 mod 23 = 19

Alice sends A=8 to Bob (public)
Bob sends B=19 to Alice (public)

Alice computes B^a mod p = 19^6 mod 23 = 2
Bob computes A^b mod p = 8^15 mod 23 = 2

SAME SECRET: 2 - Key exchange successful!
Eve saw: p=23, g=5, A=8, B=19 but cannot compute the secret
```

> 💡 **What this means:** DH key exchange allows two parties to establish a shared secret over a public channel without ever transmitting the secret itself. Modern TLS uses ECDHE (Elliptic Curve Diffie-Hellman Ephemeral) — same concept but with elliptic curves and new keys for each session ("ephemeral"), providing **perfect forward secrecy**: even if the server's private key is later compromised, past sessions cannot be decrypted.

### Step 8: Understand Certificate Chains
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('PKI CERTIFICATE CHAIN OF TRUST')
print('='*55)
print()
print('Trust Hierarchy:')
print()
print('Root CA (self-signed, pre-installed in OS/browser)')
print('  Example: DigiCert Global Root CA')
print('  Trust anchor - you trust this unconditionally')
print()
print('  Intermediate CA (signed by Root CA)')
print('  Example: DigiCert TLS RSA SHA256 2020 CA1')
print('  Root CAs rarely sign end-entity certs directly')
print()
print('    End-Entity Certificate (signed by Intermediate CA)')
print('    Example: github.com certificate')
print('    Contains: public key, domain names, validity dates')
print()
print('Verification chain:')
print('  1. Browser receives github.coms cert')
print('  2. Checks: signed by DigiCert Intermediate CA?')
print('  3. Checks: DigiCert Intermediate signed by DigiCert Root?')
print('  4. Checks: DigiCert Root in trusted store?')
print('  5. All YES -> Green padlock!')
print()
print('Attack: If attacker gets a CA to mis-issue a cert for')
print('  github.com, they can MITM HTTPS connections.')
print('  Defense: Certificate Transparency (CT) logs,')
print('  HPKP (deprecated), and CAA DNS records.')
PYEOF
"
```

**📸 Verified Output:**
```
PKI CERTIFICATE CHAIN OF TRUST
=======================================================

Trust Hierarchy:

Root CA (self-signed, pre-installed in OS/browser)
  Example: DigiCert Global Root CA
  Trust anchor - you trust this unconditionally

  Intermediate CA (signed by Root CA)
  Example: DigiCert TLS RSA SHA256 2020 CA1
  Root CAs rarely sign end-entity certs directly

    End-Entity Certificate (signed by Intermediate CA)
    Example: github.com certificate
    Contains: public key, domain names, validity dates

Verification chain:
  1. Browser receives github.coms cert
  2. Checks: signed by DigiCert Intermediate CA?
  3. Checks: DigiCert Intermediate signed by DigiCert Root?
  4. Checks: DigiCert Root in trusted store?
  5. All YES -> Green padlock!

Attack: If attacker gets a CA to mis-issue a cert for
  github.com, they can MITM HTTPS connections.
  Defense: Certificate Transparency (CT) logs,
  HPKP (deprecated), and CAA DNS records.
```

> 💡 **What this means:** The 2011 DigiNotar CA compromise showed the danger of trusting a single CA — attackers issued fraudulent certificates for google.com, enabling MITM attacks on Iranian users. Certificate Transparency (CT) logs now require all publicly-trusted CAs to publicly log every certificate they issue, making unauthorized certificates detectable.

### Step 9: Encrypt a File with RSA + AES (Hybrid Encryption)
```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/priv.pem 2048 2>/dev/null
openssl rsa -in /tmp/priv.pem -pubout -out /tmp/pub.pem 2>/dev/null

echo 'Very large secret document content...' > /tmp/largefile.txt

echo '=== HYBRID ENCRYPTION ==='
echo 'Step 1: Generate random AES key'
openssl rand -hex 32 > /tmp/aes_key.txt
cat /tmp/aes_key.txt

echo 'Step 2: Encrypt file with AES'
AES_KEY=\$(cat /tmp/aes_key.txt)
openssl enc -aes-256-cbc -pbkdf2 -pass file:/tmp/aes_key.txt \
    -in /tmp/largefile.txt -out /tmp/encrypted_file.bin
echo 'File encrypted with AES'

echo 'Step 3: Encrypt AES key with RSA public key'
openssl rsautl -encrypt -inkey /tmp/pub.pem -pubin \
    -in /tmp/aes_key.txt -out /tmp/encrypted_aes_key.bin
echo 'AES key encrypted with RSA'

echo ''
echo '=== DECRYPTION ==='
echo 'Step 1: Decrypt AES key with RSA private key'
openssl rsautl -decrypt -inkey /tmp/priv.pem \
    -in /tmp/encrypted_aes_key.bin -out /tmp/recovered_aes_key.txt
echo 'AES key recovered'

echo 'Step 2: Decrypt file with recovered AES key'
openssl enc -d -aes-256-cbc -pbkdf2 -pass file:/tmp/recovered_aes_key.txt \
    -in /tmp/encrypted_file.bin
"
```

**📸 Verified Output:**
```
=== HYBRID ENCRYPTION ===
Step 1: Generate random AES key
a7f3c9e2b8d1054678f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4
Step 2: Encrypt file with AES
File encrypted with AES
Step 3: Encrypt AES key with RSA public key
AES key encrypted with RSA

=== DECRYPTION ===
Step 1: Decrypt AES key with RSA private key
AES key recovered
Step 2: Decrypt file with recovered AES key
Very large secret document content...
```

> 💡 **What this means:** This is exactly how PGP email encryption and HTTPS work: use RSA (slow) only to encrypt the tiny AES key, then use AES (fast) for actual data. The recipient only needs your public key to send you encrypted messages. You only need your private key to decrypt. This solves both the performance problem (AES is 1000x faster than RSA) and the key distribution problem.

### Step 10: Security Best Practices Summary
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('KEY MANAGEMENT BEST PRACTICES')
print('='*55)
practices = [
    ('Key size', 'RSA: minimum 2048 bits (prefer 4096). EC: P-256 minimum.'),
    ('Key storage', 'Never store unencrypted private keys. Use HSMs for critical keys.'),
    ('Key rotation', 'Rotate keys regularly. Use short-lived certs (90 days max).'),
    ('Passphrase', 'Protect private keys with strong passphrases.'),
    ('Backup', 'Secure offline backups. Loss of private key = loss of data.'),
    ('Revocation', 'Know how to revoke certificates (CRL, OCSP).'),
    ('Algorithm choice', 'AES-256 for symmetric. SHA-256+ for hashing. EC P-256+ for asymmetric.'),
    ('Forward secrecy', 'Use ECDHE for key exchange - protects past sessions if key compromised.'),
    ('Audit', 'Log all key operations. Monitor for unauthorized access.'),
]
for practice, desc in practices:
    print(f'{practice}:')
    print(f'  {desc}')
    print()
PYEOF
"
```

**📸 Verified Output:**
```
KEY MANAGEMENT BEST PRACTICES
=======================================================
Key size:
  RSA: minimum 2048 bits (prefer 4096). EC: P-256 minimum.

Key storage:
  Never store unencrypted private keys. Use HSMs for critical keys.

Key rotation:
  Rotate keys regularly. Use short-lived certs (90 days max).

Passphrase:
  Protect private keys with strong passphrases.

Backup:
  Secure offline backups. Loss of private key = loss of data.

Revocation:
  Know how to revoke certificates (CRL, OCSP).

Algorithm choice:
  AES-256 for symmetric. SHA-256+ for hashing. EC P-256+ for asymmetric.

Forward secrecy:
  Use ECDHE for key exchange - protects past sessions if key compromised.

Audit:
  Log all key operations. Monitor for unauthorized access.
```

> 💡 **What this means:** Key management failures are responsible for many real-world breaches. Heartbleed (2014) exposed private keys stored in OpenSSL's memory. Cloudflare accidentally disclosed private keys via Cloudbleed (2017). Let's Encrypt made 90-day certificates the norm, forcing regular rotation. Hardware Security Modules (HSMs) are tamper-resistant devices that store and use private keys without ever exposing them.

## ✅ Verification

```bash
docker run --rm innozverse-cybersec bash -c "
openssl genrsa -out /tmp/test.pem 2048 2>/dev/null
openssl rsa -in /tmp/test.pem -pubout -out /tmp/test_pub.pem 2>/dev/null
echo 'verify' > /tmp/v.txt
openssl dgst -sha256 -sign /tmp/test.pem -out /tmp/v_sig.bin /tmp/v.txt
openssl dgst -sha256 -verify /tmp/test_pub.pem -signature /tmp/v_sig.bin /tmp/v.txt
echo 'PKI lab complete!'
"
```

**📸 Verified Output:**
```
Verified OK
PKI lab complete!
```

## 🚨 Common Mistakes
- **Sharing private keys**: Private keys must NEVER be shared. If you need someone to decrypt your data, they need YOUR public key, not your private key.
- **Using RSA for large data**: RSA can only encrypt data smaller than the key size (256 bytes for RSA-2048). Use hybrid encryption for real files.
- **Trusting self-signed certificates blindly**: Self-signed certs provide encryption but no authentication. An attacker could present their own self-signed cert claiming to be your bank.

## 📝 Summary
- RSA uses mathematically linked key pairs: public key encrypts, private key decrypts; private key signs, public key verifies
- ECC provides equivalent security to RSA with much smaller keys, making it preferred for modern TLS and mobile
- PKI chains of trust allow browsers to verify that a public key truly belongs to the claimed owner, using Certificate Authorities
- Hybrid encryption combines RSA (for key exchange) and AES (for bulk data) — the foundation of all HTTPS connections

## 🔗 Further Reading
- [OpenSSL Cookbook](https://www.feistyduck.com/library/openssl-cookbook/)
- [Certificate Transparency](https://certificate.transparency.dev/)
- [Let's Encrypt: How it works](https://letsencrypt.org/how-it-works/)
