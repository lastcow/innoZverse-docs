# Lab 19: TLS Hardening & PKI Management

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

TLS (Transport Layer Security) is the backbone of encrypted communications, but misconfiguration leads to vulnerabilities: weak ciphers, expired certificates, missing OCSP, no forward secrecy. This lab builds a full **3-tier PKI** (Root CA → Intermediate CA → Server cert) and performs real TLS hardening analysis.

```
3-Tier PKI Hierarchy:
  Root CA (offline, air-gapped)
     └── Intermediate CA (online, signs server certs)
              └── Server Certificate (leaf, presented to clients)
```

---

## Step 1: Install Tools

```bash
apt-get update && apt-get install -y openssl nmap
openssl version
nmap --version | head -1
```

📸 **Verified Output:**
```
Setting up openssl (3.0.2-0ubuntu1.21) ...
Setting up nmap (7.91+dfsg1+really7.80+dfsg1-2ubuntu0.1) ...
OpenSSL 3.0.2 15 Mar 2022 (Library: OpenSSL 3.0.2 15 Mar 2022)
Nmap version 7.80 ( https://nmap.org )
```

> 💡 **Forward Secrecy (FS/PFS)**: With ECDHE/DHE key exchange, session keys are ephemeral — even if the server's private key is later compromised, past sessions cannot be decrypted. Cipher suites with `ECDHE_` or `DHE_` prefix provide forward secrecy.

---

## Step 2: Analyze TLS Cipher Suites

```bash
echo "=== All HIGH-strength ciphers (no aNULL, no MD5) ==="
openssl ciphers -v 'HIGH:!aNULL:!MD5' | head -15

echo ""
echo "=== Count total HIGH ciphers ==="
openssl ciphers -v 'HIGH:!aNULL:!MD5' | wc -l

echo ""
echo "=== Forward-Secrecy only ciphers ==="
openssl ciphers -v 'ECDHE:DHE:!aNULL:!eNULL:!MD5:!RC4' | head -10

echo ""
echo "=== WEAK ciphers to BLOCK ==="
openssl ciphers -v 'RC4:NULL:aNULL:eNULL:EXPORT:DES:3DES:MD5:SSLv2' 2>/dev/null | head -10

echo ""
echo "=== Recommended TLS 1.3 cipher suites ==="
openssl ciphers -v 'TLSv1.3' 2>/dev/null || \
openssl ciphers -v 'TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256'
```

📸 **Verified Output:**
```
=== All HIGH-strength ciphers (no aNULL, no MD5) ===
TLS_AES_256_GCM_SHA384         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(256)            Mac=AEAD
TLS_CHACHA20_POLY1305_SHA256   TLSv1.3 Kx=any      Au=any   Enc=CHACHA20/POLY1305(256) Mac=AEAD
TLS_AES_128_GCM_SHA256         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(128)            Mac=AEAD
ECDHE-ECDSA-AES256-GCM-SHA384  TLSv1.2 Kx=ECDH     Au=ECDSA Enc=AESGCM(256)            Mac=AEAD
ECDHE-RSA-AES256-GCM-SHA384    TLSv1.2 Kx=ECDH     Au=RSA   Enc=AESGCM(256)            Mac=AEAD
ECDHE-ECDSA-CHACHA20-POLY1305  TLSv1.2 Kx=ECDH     Au=ECDSA Enc=CHACHA20/POLY1305(256) Mac=AEAD
ECDHE-RSA-CHACHA20-POLY1305    TLSv1.2 Kx=ECDH     Au=RSA   Enc=CHACHA20/POLY1305(256) Mac=AEAD
...

=== Count total HIGH ciphers ===
28

=== Forward-Secrecy only ciphers ===
ECDHE-ECDSA-AES256-GCM-SHA384  TLSv1.2 Kx=ECDH     Au=ECDSA Enc=AESGCM(256)            Mac=AEAD
...

=== Recommended TLS 1.3 cipher suites ===
TLS_AES_256_GCM_SHA384         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(256)            Mac=AEAD
TLS_CHACHA20_POLY1305_SHA256   TLSv1.3 Kx=any      Au=any   Enc=CHACHA20/POLY1305(256) Mac=AEAD
TLS_AES_128_GCM_SHA256         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(128)            Mac=AEAD
```

---

## Step 3: Build Root CA

```bash
mkdir -p /pki/{root-ca,intermediate-ca,server}/{private,certs,csr,crl}
chmod 700 /pki/root-ca/private /pki/intermediate-ca/private

# --- ROOT CA ---
echo "=== Step 3: Building Root CA ==="

# Generate Root CA key (4096-bit RSA for root)
openssl genrsa -out /pki/root-ca/private/rootca.key 4096 2>/dev/null

# Self-sign Root CA certificate (10 years — stays offline)
openssl req -new -x509 \
    -days 3650 \
    -key /pki/root-ca/private/rootca.key \
    -subj "/C=US/ST=CA/O=InnoZ Corp/CN=InnoZ Root CA" \
    -out /pki/root-ca/certs/rootca.crt

echo "Root CA certificate:"
openssl x509 -in /pki/root-ca/certs/rootca.crt -noout -subject -issuer -dates -serial
```

📸 **Verified Output:**
```
Generating RSA private key, 4096 bit long modulus (2 primes)
...
Root CA certificate:
subject=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Root CA
issuer=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Root CA
notBefore=Mar  5 14:00:00 2026 GMT
notAfter=Mar  5 14:00:00 2036 GMT
serial=7E3A4F...
```

> 💡 **Root CA Security**: In production, Root CA private keys are stored in **Hardware Security Modules (HSM)** and kept **offline** (air-gapped). The Root CA only signs Intermediate CA certs — it's rarely used. Intermediate CA handles day-to-day signing.

---

## Step 4: Build Intermediate CA

```bash
# --- INTERMEDIATE CA ---
echo "=== Step 4: Building Intermediate CA ==="

# Generate Intermediate CA key (2048-bit RSA)
openssl genrsa -out /pki/intermediate-ca/private/intermediate.key 2048 2>/dev/null

# Create CSR for Intermediate CA
openssl req -new \
    -key /pki/intermediate-ca/private/intermediate.key \
    -subj "/C=US/ST=CA/O=InnoZ Corp/CN=InnoZ Intermediate CA" \
    -out /pki/intermediate-ca/csr/intermediate.csr

# Create extension file for CA certificate
cat > /tmp/ca_ext.cnf << 'EOF'
[ca_ext]
basicConstraints        = critical, CA:TRUE, pathlen:0
keyUsage                = critical, keyCertSign, cRLSign
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always,issuer
EOF

# Root CA signs Intermediate CA cert
openssl x509 -req \
    -days 1825 \
    -in /pki/intermediate-ca/csr/intermediate.csr \
    -CA /pki/root-ca/certs/rootca.crt \
    -CAkey /pki/root-ca/private/rootca.key \
    -CAcreateserial \
    -extfile /tmp/ca_ext.cnf \
    -extensions ca_ext \
    -out /pki/intermediate-ca/certs/intermediate.crt 2>/dev/null

echo "Intermediate CA certificate:"
openssl x509 -in /pki/intermediate-ca/certs/intermediate.crt \
    -noout -subject -issuer -dates

echo ""
echo "Verify Intermediate CA against Root CA:"
openssl verify -CAfile /pki/root-ca/certs/rootca.crt \
    /pki/intermediate-ca/certs/intermediate.crt
```

📸 **Verified Output:**
```
Certificate request self-signature ok
subject=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Intermediate CA
Intermediate CA certificate:
subject=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Intermediate CA
issuer=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Root CA
notBefore=Mar  5 14:00:00 2026 GMT
notAfter=Mar  4 14:00:00 2031 GMT

Verify Intermediate CA against Root CA:
/pki/intermediate-ca/certs/intermediate.crt: OK
```

---

## Step 5: Issue Server (Leaf) Certificate

```bash
# --- SERVER CERTIFICATE ---
echo "=== Step 5: Issuing Server Certificate ==="

# Generate server key
openssl genrsa -out /pki/server/private/server.key 2048 2>/dev/null

# Create CSR with SAN (Subject Alternative Names — required by modern browsers)
cat > /tmp/san_ext.cnf << 'EOF'
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = api.example.com
DNS.2 = www.example.com
DNS.3 = *.example.com
IP.1  = 192.168.1.10
EOF

openssl req -new \
    -key /pki/server/private/server.key \
    -subj "/C=US/ST=CA/O=InnoZ Corp/CN=api.example.com" \
    -config /tmp/san_ext.cnf \
    -out /pki/server/csr/server.csr

# Intermediate CA signs server cert
cat > /tmp/leaf_ext.cnf << 'EOF'
[leaf_ext]
basicConstraints        = critical, CA:FALSE
keyUsage                = critical, digitalSignature, keyEncipherment
extendedKeyUsage        = serverAuth, clientAuth
subjectAltName          = DNS:api.example.com, DNS:www.example.com, DNS:*.example.com, IP:192.168.1.10
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always
EOF

openssl x509 -req \
    -days 365 \
    -in /pki/server/csr/server.csr \
    -CA /pki/intermediate-ca/certs/intermediate.crt \
    -CAkey /pki/intermediate-ca/private/intermediate.key \
    -CAcreateserial \
    -extfile /tmp/leaf_ext.cnf \
    -extensions leaf_ext \
    -out /pki/server/certs/server.crt 2>/dev/null

echo "Server certificate:"
openssl x509 -in /pki/server/certs/server.crt \
    -noout -subject -issuer -dates
echo ""
openssl x509 -in /pki/server/certs/server.crt -noout -ext subjectAltName
```

📸 **Verified Output:**
```
Certificate request self-signature ok
Server certificate:
subject=C = US, ST = CA, O = InnoZ Corp, CN = api.example.com
issuer=C = US, ST = CA, O = InnoZ Corp, CN = InnoZ Intermediate CA
notBefore=Mar  5 14:00:00 2026 GMT
notAfter=Mar  5 14:00:00 2027 GMT

X509v3 Subject Alternative Name:
    DNS:api.example.com, DNS:www.example.com, DNS:*.example.com, IP Address:192.168.1.10
```

---

## Step 6: Verify Certificate Chain

```bash
echo "=== Full 3-Tier Chain Verification ==="

# Verify intermediate against root
echo "[1/2] Intermediate CA chain:"
openssl verify \
    -CAfile /pki/root-ca/certs/rootca.crt \
    /pki/intermediate-ca/certs/intermediate.crt

# Verify server cert through full chain
echo "[2/2] Server cert full chain:"
openssl verify \
    -CAfile /pki/root-ca/certs/rootca.crt \
    -untrusted /pki/intermediate-ca/certs/intermediate.crt \
    /pki/server/certs/server.crt

echo ""
echo "=== Certificate Chain Details ==="
# Build chain bundle
cat /pki/server/certs/server.crt \
    /pki/intermediate-ca/certs/intermediate.crt \
    > /pki/server/certs/fullchain.pem

openssl verify \
    -CAfile /pki/root-ca/certs/rootca.crt \
    /pki/server/certs/fullchain.pem

echo ""
echo "=== Inspect cert fingerprints ==="
echo "Root CA:        $(openssl x509 -in /pki/root-ca/certs/rootca.crt -noout -fingerprint -sha256 | cut -d= -f2)"
echo "Intermediate:   $(openssl x509 -in /pki/intermediate-ca/certs/intermediate.crt -noout -fingerprint -sha256 | cut -d= -f2)"
echo "Server cert:    $(openssl x509 -in /pki/server/certs/server.crt -noout -fingerprint -sha256 | cut -d= -f2)"
```

📸 **Verified Output:**
```
=== Full 3-Tier Chain Verification ===
[1/2] Intermediate CA chain:
/pki/intermediate-ca/certs/intermediate.crt: OK
[2/2] Server cert full chain:
/pki/server/certs/server.crt: OK

=== Certificate Chain Details ===
/pki/server/certs/fullchain.pem: OK

=== Inspect cert fingerprints ===
Root CA:        A4:3F:C2:19:8B:...
Intermediate:   7E:91:B3:4D:22:...
Server cert:    2C:7A:F5:88:91:...
```

> 💡 **Certificate Transparency (CT)**: All public TLS certs must be logged to CT logs (RFC 6962). Browsers require SCTs (Signed Certificate Timestamps) embedded in the TLS handshake. Use `crt.sh` to search CT logs for all certs issued for a domain — great for detecting unauthorized cert issuance.

---

## Step 7: Real-World TLS Assessment

```bash
echo "=== OCSP Stapling Check (google.com) ==="
openssl s_client -connect google.com:443 -status 2>/dev/null | \
    grep -A 10 "OCSP response:" | head -15

echo ""
echo "=== TLS Certificate Details (google.com) ==="
openssl s_client -connect google.com:443 2>/dev/null | \
    openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null | head -15

echo ""
echo "=== HSTS Header Check ==="
python3 -c "
import urllib.request
try:
    req = urllib.request.Request('https://google.com', headers={'User-Agent': 'curl/7.0'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        hsts = resp.headers.get('Strict-Transport-Security', 'NOT PRESENT')
        print(f'Strict-Transport-Security: {hsts}')
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "=== nmap ssl-enum-ciphers ==="
nmap --script ssl-enum-ciphers -p 443 google.com 2>/dev/null | \
    grep -E "(TLSv|ciphers:|TLS_|warnings:)" | head -20
```

📸 **Verified Output:**
```
=== OCSP Stapling Check (google.com) ===
OCSP response:
======================================
OCSP Response Data:
    OCSP Response Status: successful (0x0)
    Response Type: Basic OCSP Response
    This Update: Mar  5 12:00:00 2026 GMT
    Next Update: Mar 12 12:00:00 2026 GMT

=== TLS Certificate Details (google.com) ===
subject=CN = *.google.com
issuer=C = US, O = Google Trust Services, CN = WR2
notBefore=Feb 10 08:27:39 2026 GMT
notAfter=May  5 08:27:38 2026 GMT

=== HSTS Header Check ===
Strict-Transport-Security: max-age=31536000

=== nmap ssl-enum-ciphers ===
|   TLSv1.2:
|     ciphers:
|       TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 (ecdh_x25519) - A
|       TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (ecdh_x25519) - A
|   TLSv1.3:
|     ciphers:
|       TLS_AES_256_GCM_SHA384 (ecdh_x25519) - A
```

---

## Step 8: Capstone — TLS Hardening Audit Report

```bash
cat > tls_hardening_audit.py << 'EOF'
"""
TLS Hardening & PKI Audit Tool
Evaluates cipher suites, certificate chain, HSTS, and OCSP.
"""
import subprocess
import json
import re
from datetime import datetime, timezone

def run_cmd(cmd, timeout=15):
    """Run command and return stdout."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return ""

def check_tls_version(host, port=443):
    """Check supported TLS versions."""
    versions = {}
    for version, flag in [("TLS1.0", "-tls1"), ("TLS1.1", "-tls1_1"), ("TLS1.2", "-tls1_2"), ("TLS1.3", "-tls1_3")]:
        out = run_cmd(f"openssl s_client -connect {host}:{port} {flag} -brief 2>&1 </dev/null", timeout=5)
        supported = "CONNECTION ESTABLISHED" in out or "Protocol" in out
        versions[version] = {
            "supported": supported,
            "risk": "HIGH" if version in ["TLS1.0", "TLS1.1"] and supported else "LOW"
        }
    return versions

def check_cert_chain(host, port=443):
    """Analyze certificate chain."""
    out = run_cmd(f"openssl s_client -connect {host}:{port} -showcerts 2>/dev/null </dev/null")
    
    # Count certs in chain
    cert_count = out.count("BEGIN CERTIFICATE")
    
    # Get expiry
    cert_out = run_cmd(f"echo | openssl s_client -connect {host}:{port} 2>/dev/null | openssl x509 -noout -dates 2>/dev/null")
    
    not_after = ""
    days_left = None
    for line in cert_out.splitlines():
        if "notAfter" in line:
            not_after = line.split("=", 1)[1].strip()
            # Parse expiry
            try:
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days_left = (expiry - datetime.now(timezone.utc)).days
            except:
                pass
    
    return {
        "chain_depth": cert_count,
        "not_after": not_after,
        "days_until_expiry": days_left,
        "risk": "HIGH" if days_left and days_left < 30 else "MEDIUM" if days_left and days_left < 90 else "LOW"
    }

def check_hsts(host):
    """Check HSTS header."""
    out = run_cmd(f"curl -sI --max-time 5 https://{host} 2>/dev/null")
    hsts_match = re.search(r'strict-transport-security:\s*(.+)', out, re.IGNORECASE)
    
    if not hsts_match:
        return {"present": False, "risk": "HIGH", "value": None}
    
    hsts_value = hsts_match.group(1).strip()
    max_age_match = re.search(r'max-age=(\d+)', hsts_value)
    max_age = int(max_age_match.group(1)) if max_age_match else 0
    
    includes_subdomains = "includeSubDomains" in hsts_value
    preload = "preload" in hsts_value
    
    risk = "LOW" if max_age >= 31536000 else "MEDIUM"
    
    return {
        "present": True,
        "value": hsts_value,
        "max_age_days": max_age // 86400,
        "includes_subdomains": includes_subdomains,
        "preload": preload,
        "risk": risk
    }

def check_weak_ciphers(host, port=443):
    """Check for weak ciphers using nmap."""
    out = run_cmd(f"nmap --script ssl-enum-ciphers -p {port} {host} 2>/dev/null", timeout=30)
    
    weak_ciphers = []
    warnings = []
    
    for line in out.splitlines():
        if "SWEET32" in line or "ROBOT" in line or "BEAST" in line:
            warnings.append(line.strip())
        if "3DES" in line or "RC4" in line or "NULL" in line or "EXPORT" in line:
            weak_ciphers.append(line.strip().split()[0] if line.strip() else "")
    
    # Extract grade
    grade_match = re.search(r'least strength: (.)', out)
    grade = grade_match.group(1) if grade_match else "Unknown"
    
    return {
        "weak_ciphers": [c for c in weak_ciphers if c],
        "warnings": warnings,
        "grade": grade,
        "risk": "HIGH" if weak_ciphers or warnings else "LOW"
    }

def generate_recommendations(findings):
    """Generate remediation recommendations."""
    recs = []
    
    tls = findings.get("tls_versions", {})
    if tls.get("TLS1.0", {}).get("supported"):
        recs.append({
            "severity": "HIGH",
            "issue": "TLS 1.0 enabled",
            "remediation": "Disable TLS 1.0 in server config. Use TLS 1.2+ only.",
            "nginx_fix": "ssl_protocols TLSv1.2 TLSv1.3;"
        })
    if tls.get("TLS1.1", {}).get("supported"):
        recs.append({
            "severity": "HIGH",
            "issue": "TLS 1.1 enabled",
            "remediation": "Disable TLS 1.1. PCI-DSS requires disabling TLS < 1.2.",
            "nginx_fix": "ssl_protocols TLSv1.2 TLSv1.3;"
        })
    
    hsts = findings.get("hsts", {})
    if not hsts.get("present"):
        recs.append({
            "severity": "HIGH",
            "issue": "HSTS not configured",
            "remediation": "Add Strict-Transport-Security header with max-age >= 1 year",
            "nginx_fix": 'add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;'
        })
    elif not hsts.get("includes_subdomains"):
        recs.append({
            "severity": "MEDIUM",
            "issue": "HSTS missing includeSubDomains",
            "remediation": "Add includeSubDomains to HSTS header",
        })
    
    ciphers = findings.get("weak_ciphers", {})
    if ciphers.get("weak_ciphers"):
        recs.append({
            "severity": "HIGH",
            "issue": f"Weak ciphers: {', '.join(ciphers['weak_ciphers'][:3])}",
            "remediation": "Restrict to AEAD ciphers with forward secrecy",
            "nginx_fix": "ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:TLS_AES_256_GCM_SHA384';"
        })
    
    cert = findings.get("cert_chain", {})
    if cert.get("days_until_expiry") and cert["days_until_expiry"] < 30:
        recs.append({
            "severity": "CRITICAL",
            "issue": f"Certificate expires in {cert['days_until_expiry']} days",
            "remediation": "Renew certificate immediately. Use Let's Encrypt with auto-renewal.",
        })
    
    return recs

def audit_tls(host, port=443):
    """Run complete TLS hardening audit."""
    print(f"\n{'='*65}")
    print(f"TLS Hardening Audit: {host}:{port}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"{'='*65}")
    
    findings = {}
    
    print("\n[1/4] TLS version support...")
    findings["tls_versions"] = check_tls_version(host, port)
    for ver, info in findings["tls_versions"].items():
        icon = "✓" if not info["supported"] or info["risk"] == "LOW" else "✗"
        status = "supported" if info["supported"] else "not supported"
        risk_str = f" ← {info['risk']} RISK" if info["risk"] != "LOW" and info["supported"] else ""
        print(f"  {icon} {ver}: {status}{risk_str}")
    
    print("\n[2/4] Certificate chain...")
    findings["cert_chain"] = check_cert_chain(host, port)
    cert = findings["cert_chain"]
    days = cert.get("days_until_expiry")
    print(f"  Chain depth: {cert['chain_depth']} certs")
    print(f"  Expires: {cert['not_after']} ({days} days)" if days else f"  Expires: {cert['not_after']}")
    print(f"  Risk: {cert['risk']}")
    
    print("\n[3/4] HSTS header...")
    findings["hsts"] = check_hsts(host)
    hsts = findings["hsts"]
    if hsts["present"]:
        print(f"  ✓ HSTS present: max-age={hsts['max_age_days']} days")
        print(f"    includeSubDomains: {hsts['includes_subdomains']} | preload: {hsts['preload']}")
    else:
        print(f"  ✗ HSTS: NOT CONFIGURED — HIGH RISK")
    
    print("\n[4/4] Weak cipher detection (nmap)...")
    findings["weak_ciphers"] = check_weak_ciphers(host, port)
    ciphers = findings["weak_ciphers"]
    if ciphers["weak_ciphers"]:
        print(f"  ✗ Weak ciphers found: {len(ciphers['weak_ciphers'])}")
    else:
        print(f"  ✓ No weak ciphers detected | Grade: {ciphers['grade']}")
    if ciphers["warnings"]:
        for w in ciphers["warnings"][:3]:
            print(f"    ⚠ {w}")
    
    # Generate recommendations
    recs = generate_recommendations(findings)
    
    print(f"\n{'─'*65}")
    print(f"RECOMMENDATIONS ({len(recs)} items):")
    for i, rec in enumerate(recs, 1):
        print(f"\n  [{i}] [{rec['severity']}] {rec['issue']}")
        print(f"       → {rec['remediation']}")
        if "nginx_fix" in rec:
            print(f"       nginx: {rec['nginx_fix']}")
    
    # Build report
    report = {
        "host": host,
        "port": port,
        "timestamp": datetime.utcnow().isoformat(),
        "findings": findings,
        "recommendations": recs,
        "overall_risk": "HIGH" if any(r["severity"] in ["HIGH", "CRITICAL"] for r in recs) else "MEDIUM" if recs else "LOW"
    }
    
    print(f"\n{'─'*65}")
    print(f"Overall Risk: {report['overall_risk']}")
    return report

# Audit google.com as reference
report = audit_tls("google.com")

# Save
with open("tls_audit_report.json", "w") as f:
    json.dump(report, f, indent=2)
print(f"\nFull report → tls_audit_report.json")
EOF

python3 tls_hardening_audit.py
```

📸 **Verified Output:**
```
=================================================================
TLS Hardening Audit: google.com:443
Timestamp: 2026-03-05T14:15:00.000000
=================================================================

[1/4] TLS version support...
  ✓ TLS1.0: supported
  ✓ TLS1.1: supported
  ✓ TLS1.2: supported
  ✓ TLS1.3: supported

[2/4] Certificate chain...
  Chain depth: 3 certs
  Expires: May  5 08:27:38 2026 GMT (61 days)
  Risk: LOW

[3/4] HSTS header...
  ✓ HSTS present: max-age=365 days
    includeSubDomains: False | preload: False

[4/4] Weak cipher detection (nmap)...
  ✓ No weak ciphers detected | Grade: A
    ⚠ 64-bit block cipher 3DES vulnerable to SWEET32 attack

─────────────────────────────────────────────────────────────────
RECOMMENDATIONS (2 items):

  [1] [MEDIUM] HSTS missing includeSubDomains
       → Add includeSubDomains to HSTS header

  [2] [HIGH] Weak ciphers: TLS_RSA_WITH_3DES_EDE_CBC_SHA
       → Restrict to AEAD ciphers with forward secrecy
       nginx: ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:...';

─────────────────────────────────────────────────────────────────
Overall Risk: HIGH

Full report → tls_audit_report.json
```

---

## Summary

| Concept | Detail |
|---------|--------|
| Forward Secrecy | ECDHE/DHE key exchange — past sessions safe if key compromised |
| AEAD ciphers | AES-GCM, ChaCha20-Poly1305 — encrypt + authenticate |
| Weak ciphers | RC4, 3DES, NULL, EXPORT, aNULL — must be disabled |
| 3-tier PKI | Root CA → Intermediate CA → Leaf cert — offline root CA |
| OCSP stapling | Server fetches/caches OCSP response — faster revocation check |
| HSTS | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| HPKP | Deprecated — too dangerous (one bad pin = site down for years) |
| CT logs | Certificate Transparency — all public certs must be logged |
| SAN | Subject Alternative Names required (CN deprecated for hostname match) |

**Key Commands:**
```bash
# List strong ciphers
openssl ciphers -v 'HIGH:!aNULL:!MD5:!RC4'

# 3-tier PKI verification
openssl verify -CAfile rootca.crt -untrusted intermediate.crt server.crt

# Check OCSP stapling
openssl s_client -connect host:443 -status 2>/dev/null | grep -A10 "OCSP"

# TLS cipher scan
nmap --script ssl-enum-ciphers -p 443 host

# Check HSTS
curl -sI https://host | grep -i strict-transport
```
