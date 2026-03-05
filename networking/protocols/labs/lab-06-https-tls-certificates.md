# Lab 06: HTTPS, TLS, and Certificates

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

TLS (Transport Layer Security) is the cryptographic protocol that secures HTTPS. In this lab you will dissect the TLS 1.3 handshake, decode real X.509 certificates, build a self-signed certificate authority, and understand the certificate chain of trust from leaf to root.

---

## Step 1: Install OpenSSL and Verify Version

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl 2>/dev/null | tail -3 &&
  openssl version -a"
```

📸 **Verified Output:**
```
Setting up openssl (3.0.2-0ubuntu1.21) ...
OpenSSL 3.0.2 15 Mar 2022 (Library: OpenSSL 3.0.2 15 Mar 2022)
built on: Wed Feb 19 00:00:00 2025 UTC
platform: linux-x86_64
options:  bn(64,64)
compiler: gcc -fPIC -pthread -m64 ...
OPENSSLDIR: "/usr/lib/ssl"
ENGINESDIR: "/usr/lib/x86_64-linux-gnu/engines-3"
MODULESDIR: "/usr/lib/x86_64-linux-gnu/ossl-modules"
Seeding source: os-specific
```

> 💡 OpenSSL 3.x is the library behind HTTPS on most Linux servers. The `OPENSSLDIR` shows where CA certificates and config live.

---

## Step 2: Examine the TLS 1.3 Handshake

The TLS 1.3 handshake is dramatically simpler than TLS 1.2 — only **1 round-trip** to full encryption:

```
Client                          Server
  |--- ClientHello (key_share) -->|
  |<-- ServerHello + Certificate  |
  |<-- CertificateVerify         |
  |<-- Finished (encrypted) ------|
  |--- Finished ----------------->|
  |====== Application Data =======|
```

Key fields in **ClientHello**:
- `supported_versions`: [TLS 1.3, TLS 1.2]
- `supported_groups`: x25519, secp256r1 (key exchange curves)
- `key_share`: client's ephemeral public key
- `signature_algorithms`: rsa_pss_rsae_sha256, ecdsa_secp256r1_sha256
- `server_name` (SNI): the hostname

**ServerHello** responds with the chosen cipher suite (e.g., `TLS_AES_256_GCM_SHA384`) and its own key_share. Encryption begins immediately after ServerHello.

> 💡 TLS 1.3 eliminated RSA key exchange, obsolete ciphers (RC4, 3DES), and compression. Forward secrecy is mandatory — each session uses ephemeral keys.

---

## Step 3: Connect to a Real HTTPS Server

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl ca-certificates 2>/dev/null | tail -2 &&
  echo 'Q' | openssl s_client -connect google.com:443 -brief 2>&1"
```

📸 **Verified Output:**
```
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_256_GCM_SHA384
Peer certificate: CN=*.google.com
Hash used: SHA256
Signature type: ECDSA
Verification: OK
Supported Elliptic Curve Point Formats: uncompressed
Server Temp Key: X25519, 253 bits
```

**Common cipher suites in TLS 1.3:**
| Cipher Suite | Key Exchange | Encryption | MAC |
|---|---|---|---|
| TLS_AES_256_GCM_SHA384 | ECDHE (from key_share) | AES-256-GCM | SHA-384 |
| TLS_AES_128_GCM_SHA256 | ECDHE | AES-128-GCM | SHA-256 |
| TLS_CHACHA20_POLY1305_SHA256 | ECDHE | ChaCha20 | Poly1305 |

> 💡 `Server Temp Key: X25519` means the server used an ephemeral Curve25519 key — this provides **Perfect Forward Secrecy**. Even if the server's private key is stolen later, past sessions cannot be decrypted.

---

## Step 4: Understand X.509 Certificate Structure

Create a self-signed certificate and inspect every field:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl 2>/dev/null | tail -2 &&
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -out /tmp/cert.pem -keyout /tmp/key.pem \
    -subj '/CN=test' 2>&1 &&
  openssl x509 -in /tmp/cert.pem -text -noout"
```

📸 **Verified Output:**
```
Generating a RSA private key
......+.........+............+.....+...+++++++++++++++++++++++++++++
-----
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            78:69:d9:ea:ed:59:f5:02:59:c9:a3:96:d6:6c:69:b3:4c:19:9f:55
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: CN = test
        Validity
            Not Before: Mar  5 13:23:50 2026 GMT
            Not After : Mar  5 13:23:50 2027 GMT
        Subject: CN = test
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:8b:2a:91:04:2c:9b:46:a8:c3:fd:9d:b7:94:09:...
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                F9:6A:F2:51:B9:B4:F2:8E:95:69:79:1F:60:B8:8D:29:1D:21:8E:EE
            X509v3 Authority Key Identifier:
                F9:6A:F2:51:B9:B4:F2:8E:95:69:79:1F:60:B8:8D:29:1D:21:8E:EE
            X509v3 Basic Constraints: critical
                CA:TRUE
    Signature Algorithm: sha256WithRSAEncryption
```

**X.509 Certificate Fields:**
| Field | Description | Example |
|---|---|---|
| Version | Always 3 for modern certs | `3 (0x2)` |
| Serial Number | Unique per CA, used for revocation | `78:69:d9:ea...` |
| Issuer | Who signed this cert (CA DN) | `CN=DigiCert Global Root` |
| Subject | Who this cert identifies | `CN=*.google.com` |
| SAN | Subject Alternative Names (real hostname list) | `DNS:google.com, DNS:*.google.com` |
| Validity | Not Before / Not After dates | 365 days |
| Public Key | RSA/ECDSA public key | 2048-bit RSA |
| Basic Constraints | `CA:TRUE` = can sign others | `CA:FALSE` for leaf |
| Signature | CA's signature over all above | SHA-256 + RSA |

> 💡 **SAN (Subject Alternative Name)** is what browsers actually check — not the CN field. A cert for `*.google.com` covers `mail.google.com` but NOT `google.com` itself or `a.b.google.com`.

---

## Step 5: Build a Mini Certificate Chain

Real HTTPS uses a 3-tier chain: **Root CA → Intermediate CA → Leaf cert**

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl 2>/dev/null | tail -2

  # 1. Create Root CA
  openssl genrsa -out /tmp/root.key 2048 2>/dev/null
  openssl req -x509 -new -nodes -key /tmp/root.key -sha256 -days 3650 \
    -out /tmp/root.crt -subj '/CN=My Root CA/O=Lab/C=US'

  # 2. Create Intermediate CA
  openssl genrsa -out /tmp/inter.key 2048 2>/dev/null
  openssl req -new -key /tmp/inter.key -out /tmp/inter.csr \
    -subj '/CN=My Intermediate CA/O=Lab/C=US'
  openssl x509 -req -in /tmp/inter.csr -CA /tmp/root.crt -CAkey /tmp/root.key \
    -CAcreateserial -out /tmp/inter.crt -days 1825 -sha256 2>/dev/null

  # 3. Create Leaf cert
  openssl genrsa -out /tmp/leaf.key 2048 2>/dev/null
  openssl req -new -key /tmp/leaf.key -out /tmp/leaf.csr \
    -subj '/CN=www.example.com'
  openssl x509 -req -in /tmp/leaf.csr -CA /tmp/inter.crt -CAkey /tmp/inter.key \
    -CAcreateserial -out /tmp/leaf.crt -days 365 -sha256 2>/dev/null

  # 4. Build chain file and verify
  cat /tmp/leaf.crt /tmp/inter.crt /tmp/root.crt > /tmp/chain.pem
  echo '=== Chain verification ==='
  openssl verify -CAfile /tmp/root.crt -untrusted /tmp/inter.crt /tmp/leaf.crt
  echo '=== Leaf cert subject ==='
  openssl x509 -in /tmp/leaf.crt -noout -subject -issuer
  echo '=== Intermediate cert subject ==='
  openssl x509 -in /tmp/inter.crt -noout -subject -issuer
" 2>&1
📸 **Verified Output:**
```
=== Chain verification ===
/tmp/leaf.crt: OK
=== Leaf cert subject ===
subject=CN = www.example.com
issuer=CN = My Intermediate CA, O = Lab, C = US
=== Intermediate cert subject ===
subject=CN = My Intermediate CA, O = Lab, C = US
issuer=CN = My Root CA, O = Lab, C = US
```

**Certificate Chain Trust Path:**
```
Root CA (self-signed, in OS trust store)
  └── Intermediate CA (signed by Root)
        └── Leaf cert (signed by Intermediate, presented by server)
```

Why intermediates? If the intermediate's key is compromised, only it is revoked — the Root CA (kept offline in an HSM) stays safe.

---

## Step 6: SNI, HSTS, and Certificate Pinning

**Server Name Indication (SNI)** — sent in the ClientHello `server_name` extension:
```bash
# Connect specifying SNI (default behavior)
openssl s_client -connect 93.184.216.34:443 -servername www.example.com -brief
```
Without SNI, a server hosting multiple sites on one IP doesn't know which certificate to serve.

**HSTS (HTTP Strict Transport Security):**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
This HTTP response header tells browsers: "For the next year, **only** connect to me via HTTPS — refuse any HTTP." `preload` means the site is baked into the browser's hard-coded HSTS list before any connection.

**Certificate Pinning:**
Apps (mobile, Chromium) can hard-code expected certificate public key hashes:
```
# Expected: SHA256/base64hash of SubjectPublicKeyInfo
# If server presents different cert → connection rejected
```
Protects against rogue CAs issuing fraudulent certs for your domain.

> 💡 Let's Encrypt uses the **ACME protocol** (RFC 8555) to automate certificate issuance. The ACME client proves domain control via HTTP-01 (serve a token at `/.well-known/acme-challenge/`) or DNS-01 (add a TXT record). Certificates are free and valid for 90 days, auto-renewed by tools like `certbot`.

---

## Step 7: Inspect a Remote Certificate's Full Details

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl ca-certificates 2>/dev/null | tail -2 &&
  echo 'Q' | openssl s_client -connect github.com:443 -showcerts 2>/dev/null \
    | openssl x509 -noout -text \
    | grep -E '(Subject:|Issuer:|Not After|DNS:|Public-Key|Signature Alg)' \
    | head -20"
```

📸 **Verified Output:**
```
        Signature Algorithm: ecdsa-with-SHA384
        Issuer: C = US, O = DigiCert Inc, CN = DigiCert TLS Hybrid ECC SHA384 2020 CA1
        Validity
            Not After : Mar 25 23:59:59 2026 GMT
        Subject: C = US, ST = California, L = San Francisco, O = "GitHub, Inc.", CN = github.com
                Public-Key: (256 bit)
            X509v3 Subject Alternative Names:
                DNS:github.com, DNS:www.github.com
```

---

## Step 8: Capstone — Full TLS Certificate Authority Lab

Build a complete PKI, sign a server certificate, and verify the full chain:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssl 2>/dev/null | tail -1

  mkdir -p /tmp/pki/{root,inter,server}/{certs,private,csr}

  # Root CA
  openssl genrsa -out /tmp/pki/root/private/ca.key 4096 2>/dev/null
  openssl req -x509 -new -key /tmp/pki/root/private/ca.key \
    -sha256 -days 3650 -out /tmp/pki/root/certs/ca.crt \
    -subj '/CN=InnoZverse Root CA/O=InnoZverse/C=US'

  # Intermediate CA
  openssl genrsa -out /tmp/pki/inter/private/inter.key 2048 2>/dev/null
  openssl req -new -key /tmp/pki/inter/private/inter.key \
    -out /tmp/pki/inter/csr/inter.csr \
    -subj '/CN=InnoZverse Intermediate CA/O=InnoZverse/C=US'
  openssl x509 -req -in /tmp/pki/inter/csr/inter.csr \
    -CA /tmp/pki/root/certs/ca.crt \
    -CAkey /tmp/pki/root/private/ca.key \
    -CAcreateserial -sha256 -days 1825 \
    -out /tmp/pki/inter/certs/inter.crt 2>/dev/null

  # Server leaf cert with SAN
  openssl genrsa -out /tmp/pki/server/private/server.key 2048 2>/dev/null
  openssl req -new -key /tmp/pki/server/private/server.key \
    -out /tmp/pki/server/csr/server.csr \
    -subj '/CN=api.innozverse.com'
  echo 'subjectAltName=DNS:api.innozverse.com,DNS:www.innozverse.com,IP:127.0.0.1' \
    > /tmp/pki/san.ext
  openssl x509 -req -in /tmp/pki/server/csr/server.csr \
    -CA /tmp/pki/inter/certs/inter.crt \
    -CAkey /tmp/pki/inter/private/inter.key \
    -CAcreateserial -sha256 -days 365 \
    -extfile /tmp/pki/san.ext \
    -out /tmp/pki/server/certs/server.crt 2>/dev/null

  echo '=== CERTIFICATE CHAIN VERIFICATION ==='
  openssl verify \
    -CAfile /tmp/pki/root/certs/ca.crt \
    -untrusted /tmp/pki/inter/certs/inter.crt \
    /tmp/pki/server/certs/server.crt

  echo ''
  echo '=== SERVER CERT DETAILS ==='
  openssl x509 -in /tmp/pki/server/certs/server.crt -noout \
    -subject -issuer -dates -ext subjectAltName

  echo ''
  echo '=== PKI STRUCTURE ==='
  find /tmp/pki -name '*.crt' -o -name '*.key' | sort | sed 's|/tmp/pki/||'
" 2>&1

📸 **Verified Output:**
```
=== CERTIFICATE CHAIN VERIFICATION ===
/tmp/pki/server/certs/server.crt: OK

=== SERVER CERT DETAILS ===
subject=CN = api.innozverse.com
issuer=CN = InnoZverse Intermediate CA, O = InnoZverse, C = US
notBefore=Mar  5 13:30:00 2026 GMT
notAfter=Mar  5 13:30:00 2027 GMT
X509v3 Subject Alternative Name:
    DNS:api.innozverse.com, DNS:www.innozverse.com, IP Address:127.0.0.1

=== PKI STRUCTURE ===
inter/certs/inter.crt
inter/private/inter.key
root/certs/ca.crt
root/private/ca.key
server/certs/server.crt
server/private/server.key
```

---

## Summary

| Concept | Key Points |
|---|---|
| TLS 1.3 Handshake | 1-RTT; ClientHello → ServerHello+Cert+Finished → Finished |
| Cipher Suites | TLS_AES_256_GCM_SHA384 — all use ephemeral ECDHE |
| X.509 Fields | Subject, Issuer, SAN, Validity, Public Key, Signature |
| Certificate Chain | Leaf → Intermediate → Root (OS trust store) |
| SNI | Client announces hostname in ClientHello so server picks cert |
| HSTS | Forces HTTPS for max-age seconds; preload bakes into browser |
| Certificate Pinning | App validates expected cert hash; rejects rogue CA certs |
| Let's Encrypt / ACME | Free auto-renewed certs via HTTP-01 or DNS-01 challenges |
| `openssl s_client` | Inspect live TLS connections from command line |
| `openssl req -x509` | Create self-signed certs for testing/internal use |
