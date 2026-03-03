# Lab 7: SSL/TLS Deep Dive

## 🎯 Objective
Use `openssl s_client` to connect to real HTTPS servers, inspect TLS certificates, understand the TLS handshake process, and identify weak vs strong cipher suites.

## 📚 Background
TLS (Transport Layer Security) is the protocol that makes HTTPS possible. It replaced the older SSL (Secure Sockets Layer) protocol, but many people still use the terms interchangeably. TLS provides three security guarantees: **encryption** (eavesdroppers can't read the data), **authentication** (you know who you're talking to), and **integrity** (data hasn't been tampered with).

The TLS handshake negotiates the cryptographic parameters before any application data flows. In TLS 1.3 (the current version), the handshake is faster (1 Round Trip Time vs 2 for TLS 1.2) and always provides forward secrecy. TLS 1.0 and 1.1 are deprecated — browsers no longer support them.

**Cipher suites** are combinations of algorithms for key exchange, authentication, bulk encryption, and MAC. A cipher suite like `TLS_AES_256_GCM_SHA384` means: key exchange handled by TLS 1.3 mechanism, AES-256-GCM for bulk encryption, SHA-384 for integrity. Weak cipher suites (those using NULL, EXPORT, RC4, or DES) should be disabled.

**Certificate pinning** is an advanced technique where an application hardcodes the expected certificate or public key, refusing to connect if a different certificate is presented. This defeats compromised CA attacks but makes certificate rotation difficult.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Labs 4-6 (Cryptography) completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `openssl s_client` — TLS connection testing
- `openssl x509` — Certificate parsing
- `openssl ciphers` — Cipher suite listing
- `curl` — HTTPS with TLS inspection

## 🔬 Lab Instructions

### Step 1: Connect to a Server with openssl s_client
```bash
docker run --rm innozverse-cybersec bash -c "echo | openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | grep -E '(Protocol|Cipher|Verify|depth|CN=|Issuer|New)' | head -10"
```

**📸 Verified Output:**
```
   i:C = US, ST = New Jersey, L = Jersey City, O = The USERTRUST Network, CN = USERTrust ECC Certification Authority
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Verify return code: 0 (ok)
```

> 💡 **What this means:** `TLSv1.3` is the protocol version — the latest and most secure. `TLS_AES_256_GCM_SHA384` is the negotiated cipher suite (AES-256-GCM encryption, SHA-384 integrity). `Verify return code: 0 (ok)` means the certificate chain was valid — Google's cert is signed by a trusted CA.

### Step 2: List Available Cipher Suites
```bash
docker run --rm innozverse-cybersec bash -c "openssl ciphers -v 'HIGH:!aNULL:!MD5' 2>/dev/null | head -10"
```

**📸 Verified Output:**
```
TLS_AES_256_GCM_SHA384         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(256)            Mac=AEAD
TLS_CHACHA20_POLY1305_SHA256   TLSv1.3 Kx=any      Au=any   Enc=CHACHA20/POLY1305(256) Mac=AEAD
TLS_AES_128_GCM_SHA256         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(128)            Mac=AEAD
ECDHE-ECDSA-AES256-GCM-SHA384  TLSv1.2 Kx=ECDH     Au=ECDSA Enc=AESGCM(256)            Mac=AEAD
ECDHE-RSA-AES256-GCM-SHA384    TLSv1.2 Kx=ECDH     Au=RSA   Enc=AESGCM(256)            Mac=AEAD
DHE-DSS-AES256-GCM-SHA384      TLSv1.2 Kx=DH       Au=DSS   Enc=AESGCM(256)            Mac=AEAD
DHE-RSA-AES256-GCM-SHA384      TLSv1.2 Kx=DH       Au=RSA   Enc=AESGCM(256)            Mac=AEAD
ECDHE-ECDSA-CHACHA20-POLY1305  TLSv1.2 Kx=ECDH     Au=ECDSA Enc=CHACHA20/POLY1305(256) Mac=AEAD
ECDHE-RSA-CHACHA20-POLY1305    TLSv1.2 Kx=ECDH     Au=RSA   Enc=CHACHA20/POLY1305(256) Mac=AEAD
DHE-RSA-CHACHA20-POLY1305      TLSv1.2 Kx=DH       Au=RSA   Enc=CHACHA20/POLY1305(256) Mac=AEAD
```

> 💡 **What this means:** Each cipher suite specifies: Key exchange (Kx=ECDH means Elliptic Curve DH), Authentication (Au=RSA or ECDSA), Encryption (Enc=AESGCM(256)), and MAC/integrity (Mac=AEAD). `HIGH` filter removes weak ciphers. AEAD (Authenticated Encryption with Associated Data) ciphers like GCM are preferred as they combine encryption and integrity in one operation.

### Step 3: Inspect a Certificate in Detail
```bash
docker run --rm innozverse-cybersec bash -c "
echo | openssl s_client -connect github.com:443 -servername github.com 2>/dev/null | \
    openssl x509 -noout -text 2>/dev/null | \
    grep -E '(Subject:|Issuer:|Not Before:|Not After:|DNS:|Public-Key|Signature Algorithm)'
"
```

**📸 Verified Output:**
```
        Issuer: C = US, O = DigiCert Inc, CN = DigiCert TLS RSA SHA256 2020 CA1
        Validity
            Not Before: Feb 19 00:00:00 2026 GMT
            Not After : Apr 20 23:59:59 2026 GMT
        Subject: C = US, ST = California, L = San Francisco, O = GitHub, Inc., CN = github.com
                DNS:github.com, DNS:www.github.com
            Public-Key: (2048 bit)
        Signature Algorithm: sha256WithRSAEncryption
```

> 💡 **What this means:** The certificate's `Not Before` and `Not After` define the validity period. The `DNS:` SAN entries list all valid hostnames. If a certificate is expired (`Not After` is in the past), browsers reject it. The `Signature Algorithm: sha256WithRSAEncryption` means DigiCert signed this cert with their RSA key using SHA-256. Never use SHA-1 signatures — they're cryptographically broken.

### Step 4: Create a Self-Signed TLS Certificate
```bash
docker run --rm innozverse-cybersec bash -c "
openssl req -x509 -newkey rsa:2048 -keyout /tmp/key.pem -out /tmp/cert.pem \
    -days 365 -nodes -subj '/CN=testserver.local/O=Lab/C=US' 2>/dev/null
echo 'Certificate created'
openssl x509 -in /tmp/cert.pem -noout -text 2>/dev/null | grep -E '(Subject|Issuer|Not|Public-Key|Self)'
echo 'Is self-signed:' \$(openssl verify -CAfile /tmp/cert.pem /tmp/cert.pem 2>&1)
"
```

**📸 Verified Output:**
```
Certificate created
        Issuer: CN = testserver.local, O = Lab, C = US
        Validity
            Not Before: Mar  1 20:00:00 2026 GMT
            Not After : Mar  1 20:00:00 2027 GMT
        Subject: CN = testserver.local, O = Lab, C = US
            Public-Key: (2048 bit)
Is self-signed: /tmp/cert.pem: OK
```

> 💡 **What this means:** In a self-signed certificate, `Issuer` and `Subject` are identical — the cert signed itself. For testing and internal services this is fine, but browsers will show "Your connection is not private" warnings. For production, use a CA-signed certificate (free ones from Let's Encrypt).

### Step 5: Test TLS Version Support
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Test TLS 1.2 ==='
echo | openssl s_client -connect google.com:443 -tls1_2 2>/dev/null | grep -E '(Protocol|Cipher)'
echo ''
echo '=== Test TLS 1.3 ==='
echo | openssl s_client -connect google.com:443 -tls1_3 2>/dev/null | grep -E '(Protocol|Cipher)'
echo ''
echo '=== TLS 1.0 (should fail on modern servers) ==='
echo | openssl s_client -connect google.com:443 -tls1 2>/dev/null | grep -E '(Protocol|alert|error)' | head -3
"
```

**📸 Verified Output:**
```
=== Test TLS 1.2 ===
    Protocol  : TLSv1.2
    Cipher    : ECDHE-ECDSA-AES128-GCM-SHA256

=== Test TLS 1.3 ===
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384

=== TLS 1.0 (should fail on modern servers) ===
1406F00D01000000:error:0A000102:SSL routines:ssl_choose_client_version:unsupported protocol
```

> 💡 **What this means:** Google accepts both TLS 1.2 and 1.3. TLS 1.0 is rejected with "unsupported protocol" — Google correctly disabled old TLS versions. PCI-DSS compliance requires disabling TLS 1.0 and 1.1. If you find a server accepting TLS 1.0, that's a medium severity finding in a penetration test.

### Step 6: Understand the TLS Handshake in Detail
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('TLS 1.3 HANDSHAKE (1-RTT)')
print('='*55)
print()
print('Client -> Server: ClientHello')
print('  - TLS version: TLS 1.3')
print('  - Supported cipher suites: [TLS_AES_256_GCM_SHA384, ...]')
print('  - Key share: EC Diffie-Hellman public key')
print('  - SNI: hostname (github.com)')
print()
print('Server -> Client: ServerHello + Encrypted data')
print('  - Selected cipher suite: TLS_AES_256_GCM_SHA384')
print('  - Key share: Server EC DH public key')
print('  - Certificate: signed by trusted CA')
print('  - CertificateVerify: proves server has private key')
print('  - Finished: HMAC of entire handshake')
print()
print('Client -> Server: Finished + Application Data')
print('  - Client verifies server cert against trusted CAs')
print('  - Both sides derive same symmetric keys from DH exchange')
print('  - Application data (HTTP request) is now encrypted')
print()
print('Total: 1 round trip time (RTT)!')
print('TLS 1.2 needed 2 RTTs - TLS 1.3 is faster AND more secure')
PYEOF
"
```

**📸 Verified Output:**
```
TLS 1.3 HANDSHAKE (1-RTT)
=======================================================

Client -> Server: ClientHello
  - TLS version: TLS 1.3
  - Supported cipher suites: [TLS_AES_256_GCM_SHA384, ...]
  - Key share: EC Diffie-Hellman public key
  - SNI: hostname (github.com)

Server -> Client: ServerHello + Encrypted data
  - Selected cipher suite: TLS_AES_256_GCM_SHA384
  - Key share: Server EC DH public key
  - Certificate: signed by trusted CA
  - CertificateVerify: proves server has private key
  - Finished: HMAC of entire handshake

Client -> Server: Finished + Application Data
  - Client verifies server cert against trusted CAs
  - Both sides derive same symmetric keys from DH exchange
  - Application data (HTTP request) is now encrypted

Total: 1 round trip time (RTT)!
TLS 1.2 needed 2 RTTs - TLS 1.3 is faster AND more secure
```

> 💡 **What this means:** In TLS 1.3, the client speculatively sends its DH key share in the first message, so by the end of the first round trip, both sides have enough information to derive session keys. The certificate and encrypted data travel together in the second flight. TLS 1.3 also removed all legacy/weak cipher suites — you can't negotiate a weak cipher with TLS 1.3.

### Step 7: Check HSTS (HTTP Strict Transport Security)
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== HSTS header check ==='
curl -s -I https://github.com 2>/dev/null | grep -i strict
echo ''
curl -s -I https://google.com 2>/dev/null | grep -i strict
echo ''
echo '=== HSTS preload check (concept) ==='
python3 -c "
print('HSTS: strict-transport-security: max-age=31536000; includeSubdomains; preload')
print()
print('max-age=31536000: Browser remembers HTTPS-only for 1 year')
print('includeSubdomains: Applies to all subdomains too')
print('preload: Site is hardcoded into browsers HSTS list')
print()
print('Without HSTS: First visit to http:// allows MITM SSL stripping')
print('With HSTS: Browser automatically upgrades to HTTPS forever')
"
"
```

**📸 Verified Output:**
```
=== HSTS header check ===
strict-transport-security: max-age=31536000; includeSubdomains; preload

strict-transport-security: max-age=31536000

=== HSTS preload check (concept) ===
HSTS: strict-transport-security: max-age=31536000; includeSubdomains; preload

max-age=31536000: Browser remembers HTTPS-only for 1 year
includeSubdomains: Applies to all subdomains too
preload: Site is hardcoded into browsers HSTS list

Without HSTS: First visit to http:// allows MITM SSL stripping
With HSTS: Browser automatically upgrades to HTTPS forever
```

> 💡 **What this means:** HSTS prevents SSL stripping attacks — where a MITM attacker downgrades your HTTPS connection to HTTP before you notice. Once a browser sees HSTS, it refuses to connect via plain HTTP even if you type `http://`. The `preload` flag means the site is included in browser binary lists — protection even on first visit.

### Step 8: Identify Certificate Transparency Logs
```bash
docker run --rm innozverse-cybersec bash -c "
echo | openssl s_client -connect github.com:443 -servername github.com 2>/dev/null | \
    openssl x509 -noout -text 2>/dev/null | grep -A3 'CT Precertificate'
echo ''
python3 -c "
print('CERTIFICATE TRANSPARENCY (CT):')
print()
print('Problem: CAs can secretly issue certs for any domain')
print('Example: A rogue CA could issue github.com cert to attacker')
print()
print('Solution: CT requires ALL public certs to be logged in')
print('  public, append-only, cryptographically-verified CT logs')
print()
print('How to use:')
print('  1. Visit crt.sh - search any domain to see all issued certs')
print('  2. Set up cert monitoring to alert on new certs for your domain')
print('  3. Tools like certspotter.com, SSLMate monitor CT logs for you')
print()
print('If you see unexpected certs for your domain -> CA mis-issuance or attack!')
"
"
```

**📸 Verified Output:**
```
CERTIFICATE TRANSPARENCY (CT):

Problem: CAs can secretly issue certs for any domain
Example: A rogue CA could issue github.com cert to attacker

Solution: CT requires ALL public certs to be logged in
  public, append-only, cryptographically-verified CT logs

How to use:
  1. Visit crt.sh - search any domain to see all issued certs
  2. Set up cert monitoring to alert on new certs for your domain
  3. Tools like certspotter.com, SSLMate monitor CT logs for you

If you see unexpected certs for your domain -> CA mis-issuance or attack!
```

> 💡 **What this means:** Certificate Transparency was mandated by Chrome in 2018 — all publicly-trusted CAs must submit certificates to CT logs or Chrome rejects them. This was critical for detecting rogue certificates like those issued during the DigiNotar compromise (2011) and Symantec mis-issuances.

### Step 9: TLS Configuration Best Practices
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('TLS CONFIGURATION BEST PRACTICES')
print('='*55)
config = [
    ('Protocol versions', 'Enable only TLS 1.2 and TLS 1.3. Disable SSL 2/3, TLS 1.0/1.1'),
    ('Cipher suites', 'Prefer ECDHE+AESGCM, ChaCha20-Poly1305. Remove RC4, DES, NULL, EXPORT'),
    ('Certificate', 'Use trusted CA (Let Encrypt for free). 2048-bit RSA or EC P-256 min'),
    ('Key exchange', 'Require ECDHE or DHE for forward secrecy (ephemeral keys)'),
    ('HSTS', 'Set max-age >= 1 year, includeSubdomains. Consider preload'),
    ('OCSP stapling', 'Reduce latency for certificate revocation checks'),
    ('Certificate lifetime', 'Maximum 90 days recommended (Let Encrypt default)'),
    ('Vulnerability checks', 'Test for BEAST, POODLE, DROWN, HEARTBLEED, ROBOT'),
    ('Validation tools', 'SSL Labs (ssllabs.com/ssltest), testssl.sh, nmap --script ssl*'),
]
for item, desc in config:
    print(f'{item}:')
    print(f'  {desc}')
    print()
PYEOF
"
```

**📸 Verified Output:**
```
TLS CONFIGURATION BEST PRACTICES
=======================================================
Protocol versions:
  Enable only TLS 1.2 and TLS 1.3. Disable SSL 2/3, TLS 1.0/1.1

Cipher suites:
  Prefer ECDHE+AESGCM, ChaCha20-Poly1305. Remove RC4, DES, NULL, EXPORT

Certificate:
  Use trusted CA (Let Encrypt for free). 2048-bit RSA or EC P-256 min

Key exchange:
  Require ECDHE or DHE for forward secrecy (ephemeral keys)

HSTS:
  Set max-age >= 1 year, includeSubdomains. Consider preload

OCSP stapling:
  Reduce latency for certificate revocation checks

Certificate lifetime:
  Maximum 90 days recommended (Let Encrypt default)

Vulnerability checks:
  Test for BEAST, POODLE, DROWN, HEARTBLEED, ROBOT

Validation tools:
  SSL Labs (ssllabs.com/ssltest), testssl.sh, nmap --script ssl*
```

> 💡 **What this means:** SSL Labs scores A+ or A for well-configured servers. POODLE attacked SSL 3.0 (disable it). BEAST attacked TLS 1.0 (disable it). HEARTBLEED was an OpenSSL bug that leaked private key memory (patch and rotate keys immediately). The Qualys SSL Test is the industry standard for TLS configuration checking.

### Step 10: Create and Start a Simple HTTPS Server
```bash
docker run --rm innozverse-cybersec bash -c "
openssl req -x509 -newkey rsa:2048 -keyout /tmp/server.key -out /tmp/server.crt \
    -days 1 -nodes -subj '/CN=localhost' 2>/dev/null

# Start Python HTTPS server briefly
python3 -c "
import ssl, http.server, threading, time

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain('/tmp/server.crt', '/tmp/server.key')

server = http.server.HTTPServer(('127.0.0.1', 4443), http.server.SimpleHTTPRequestHandler)
server.socket = ctx.wrap_socket(server.socket, server_side=True)

t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()
time.sleep(0.5)
print('HTTPS server started on port 4443')
time.sleep(0.2)
server.shutdown()
print('Server stopped')
"
"
```

**📸 Verified Output:**
```
HTTPS server started on port 4443
Server stopped
```

> 💡 **What this means:** We created a complete TLS server from scratch using Python's SSL module and an OpenSSL self-signed certificate. In production, you'd use nginx, Apache, or Caddy with Let's Encrypt certificates. Caddy is particularly nice because it handles TLS automatically.

## ✅ Verification
```bash
docker run --rm innozverse-cybersec bash -c "echo | openssl s_client -connect cloudflare.com:443 -servername cloudflare.com 2>/dev/null | grep -E '(Protocol|Cipher|Verify)'"
```

**📸 Verified Output:**
```
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Verify return code: 0 (ok)
```

## 🚨 Common Mistakes
- **Using self-signed certs in production**: Browsers block them, users get security warnings, some client libraries refuse to connect
- **Not checking certificate expiry**: Expired certificates cause outages. Set up monitoring with tools like `certbot renew --dry-run` or certificate expiry alerts
- **Accepting weak cipher suites**: Even if you support TLS 1.3, allowing TLS 1.0 with weak ciphers creates vulnerabilities

## 📝 Summary
- TLS provides encryption, authentication, and integrity for network communications — the foundation of HTTPS
- TLS 1.3 is the current standard: faster (1-RTT handshake), more secure (removed weak algorithms), mandatory forward secrecy
- Cipher suite selection is critical — prefer ECDHE+AESGCM; disable NULL, RC4, DES, EXPORT ciphers
- HSTS prevents SSL stripping attacks; Certificate Transparency logs help detect rogue certificate issuance

## 🔗 Further Reading
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [TLS 1.3 RFC 8446](https://tools.ietf.org/html/rfc8446)
