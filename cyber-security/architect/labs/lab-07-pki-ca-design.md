# Lab 07: PKI & CA Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Objectives
- Design a 3-tier PKI hierarchy (Root → Intermediate → Issuing CA)
- Build and verify a real certificate chain with OpenSSL
- Understand CRL vs OCSP and OCSP stapling
- Apply SPIFFE/SPIRE for workload identity

---

## Step 1: 3-Tier PKI Hierarchy

```
┌────────────────────────────────────────────┐
│           ROOT CA (Offline)                │
│   - Self-signed, 20-year validity          │
│   - Stored in HSM, air-gapped              │
│   - Only signs Intermediate CA certs       │
│   - Key ceremony required to use           │
└──────────────────┬─────────────────────────┘
                   │
┌──────────────────▼─────────────────────────┐
│        INTERMEDIATE CA (Online/Offline)    │
│   - Signed by Root CA, 10-year validity    │
│   - Can be taken offline for security      │
│   - Only signs Issuing CA certs            │
└──────────────────┬─────────────────────────┘
                   │
┌──────────────────▼─────────────────────────┐
│         ISSUING CA (Online, 24/7)          │
│   - Signed by Intermediate CA              │
│   - 5-year validity                        │
│   - Issues end-entity certificates         │
│   - Runs CRL/OCSP responder                │
└──────────────────┬─────────────────────────┘
                   │
          End-Entity Certificates
     (TLS, Code Signing, Client Auth, Email)
```

**Why 3 tiers?**
- Root CA offline = impossible to compromise without physical access
- Intermediate CA revocation doesn't invalidate all end-entity certs
- Issuing CA can be region/purpose-specific without changing root trust

---

## Step 2: Build 3-Tier PKI with OpenSSL

```bash
# Run with Ubuntu 22.04 image
docker run -it --rm ubuntu:22.04 bash

# Install OpenSSL
apt-get update -qq && apt-get install -y -qq openssl

# CA extension config
cat > /tmp/ca_ext.cnf << 'EOF'
[ca_ext]
basicConstraints = critical, CA:true
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

mkdir -p /pki/{root,int,iss}

# --- ROOT CA ---
openssl genrsa -out /pki/root/root.key 2048
openssl req -new -x509 -days 7300 -key /pki/root/root.key \
  -out /pki/root/root.crt \
  -subj '/CN=InnoZverse Root CA/O=InnoZverse/C=US' \
  -extensions ca_ext -config /tmp/ca_ext.cnf

# --- INTERMEDIATE CA ---
openssl genrsa -out /pki/int/int.key 2048
openssl req -new -key /pki/int/int.key -out /pki/int/int.csr \
  -subj '/CN=InnoZverse Intermediate CA/O=InnoZverse/C=US'
openssl x509 -req -days 3650 -in /pki/int/int.csr \
  -CA /pki/root/root.crt -CAkey /pki/root/root.key -CAcreateserial \
  -extfile /tmp/ca_ext.cnf -extensions ca_ext -out /pki/int/int.crt

# --- ISSUING CA ---
openssl genrsa -out /pki/iss/iss.key 2048
openssl req -new -key /pki/iss/iss.key -out /pki/iss/iss.csr \
  -subj '/CN=InnoZverse Issuing CA/O=InnoZverse/C=US'
openssl x509 -req -days 1825 -in /pki/iss/iss.csr \
  -CA /pki/int/int.crt -CAkey /pki/int/int.key -CAcreateserial \
  -extfile /tmp/ca_ext.cnf -extensions ca_ext -out /pki/iss/iss.crt

# Verify chain
cat /pki/int/int.crt /pki/root/root.crt > /pki/chain.crt
openssl verify -CAfile /pki/chain.crt /pki/iss/iss.crt
```

📸 **Verified Output:**
```
=== 3-Tier PKI Build Complete ===
Root CA:
subject=CN = InnoZverse Root CA, O = InnoZverse, C = US
notBefore=Mar  5 16:10:43 2026 GMT
notAfter=Feb 28 16:10:43 2046 GMT
Intermediate CA:
subject=CN = InnoZverse Intermediate CA, O = InnoZverse, C = US
notBefore=Mar  5 16:10:43 2026 GMT
notAfter=Mar  2 16:10:43 2036 GMT
Issuing CA:
subject=CN = InnoZverse Issuing CA, O = InnoZverse, C = US
notBefore=Mar  5 16:10:44 2026 GMT
notAfter=Mar  4 16:10:44 2031 GMT
Chain Verification:
/pki/iss/iss.crt: OK
```

---

## Step 3: Certificate Types

| Type | Key Usage | Extended Key Usage | Use Case |
|------|----------|-------------------|---------|
| TLS Server | Digital Signature | Server Authentication | HTTPS, mTLS |
| TLS Client | Digital Signature | Client Authentication | mTLS, VPN |
| Code Signing | Digital Signature | Code Signing | Software packages |
| Email (S/MIME) | Digital Signature, Key Encipherment | Email Protection | Signed email |
| CA Certificate | Key Cert Sign, CRL Sign | - | CA hierarchy |

---

## Step 4: CRL vs OCSP vs OCSP Stapling

**CRL (Certificate Revocation List):**
- Periodic publication of revoked certificate serial numbers
- Client downloads CRL file (can be large, MB-sized)
- Latency: up to CRL validity period (24-72 hours)
- Suitable for: infrequent revocation, offline environments

**OCSP (Online Certificate Status Protocol):**
- Real-time query: "Is cert #1234567 still valid?"
- Response: good / revoked / unknown
- Latency: network round-trip to OCSP responder
- Privacy concern: OCSP responder knows which sites you visit

**OCSP Stapling:**
- Server pre-fetches OCSP response and includes in TLS handshake
- Client doesn't need separate OCSP request
- Signed by CA — client can verify offline
- Best practice for all modern TLS deployments

```
Without stapling:
  Client → Server (TLS Hello)
  Client → OCSP Responder (cert status check)  ← extra round-trip
  OCSP Responder → Client (status)
  Client → Server (continue)

With stapling:
  Client → Server (TLS Hello)
  Server → Client (TLS + pre-fetched OCSP response)  ← single round-trip
```

---

## Step 5: HSM (Hardware Security Module)

**HSM roles in PKI:**
- Stores private keys in tamper-resistant hardware
- Key material never leaves HSM in plaintext
- Performs cryptographic operations (sign/verify) inside HSM
- FIPS 140-2 Level 3 required for Root/Intermediate CA keys

**HSM options:**
| Type | Example | Use Case |
|------|---------|---------|
| Physical HSM | Thales Luna, Entrust nShield | On-prem Root CA |
| Cloud HSM | AWS CloudHSM, Azure Dedicated HSM | Cloud PKI |
| Virtual HSM | HashiCorp Vault, SoftHSM2 | Dev/test only |

> 💡 **Root CA key ceremony**: Formal, witnessed procedure to generate Root CA keys. Involves: multiple key custodians (M-of-N access), auditor, video recording, Faraday cage, offline air-gapped workstation. Documented with chain-of-custody forms.

---

## Step 6: Certificate Lifecycle Automation

**Manual certificate management problems:**
- Expired certificates → service outages
- Lost private keys → re-issuance delays
- Untracked certificates → shadow IT

**Certificate automation options:**
- **ACME protocol**: Let's Encrypt, ZeroSSL — automated renewal
- **cert-manager** (Kubernetes): automatic cert provisioning/renewal
- **Venafi / CertCentral**: enterprise certificate lifecycle management
- **AWS ACM**: managed TLS certs for AWS services

**cert-manager workflow:**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: web-tls
spec:
  secretName: web-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - web.corp.com
  renewBefore: 360h  # Renew 15 days before expiry
```

---

## Step 7: SPIFFE / SPIRE (Workload Identity)

**Problem**: How do microservices prove their identity to each other without managing certificates manually?

**SPIFFE (Secure Production Identity Framework for Everyone):**
- Standard for workload identity: `spiffe://trust-domain/path/service-name`
- SVID (SPIFFE Verifiable Identity Document): X.509 cert or JWT
- Workload API: local socket, no secrets stored in environment vars

**SPIRE (SPIFFE Runtime Environment):**
```
SPIRE Server:
  - Signs SVIDs using intermediate CA
  - Maintains workload registration entries
  - Issues SVIDs via Node API

SPIRE Agent (per node):
  - Attests node identity (AWS IID, TPM, k8s service account)
  - Issues SVIDs to local workloads via Workload API
  - Short-lived certs: 1-24 hour TTL (auto-rotated)
```

---

## Step 8: Capstone — Enterprise PKI Design

**Scenario:** Design PKI for 10,000-employee enterprise with cloud + on-prem

```
PKI Architecture:

Root CA (Offline):
  - Thales Luna Network HSM (FIPS 140-2 Level 3)
  - 4096-bit RSA key, SHA-256, 20-year validity
  - Air-gapped vault storage, key ceremony annually
  - 3-of-5 custodian M-of-N access

Intermediate CA (Semi-online):
  - 2x redundant (active/standby)
  - 4096-bit RSA, 10-year validity
  - Stored in AWS CloudHSM

Issuing CAs (Online, purpose-specific):
  - TLS Issuing CA (web/API certificates)
  - Client Auth CA (VPN, 802.1X device certs)
  - Code Signing CA (software packages)
  - Email (S/MIME CA)

Automation:
  - cert-manager for Kubernetes workloads
  - ACME for public-facing TLS (Let's Encrypt)
  - Venafi for enterprise certificate lifecycle
  - SPIRE for microservice identity

Revocation:
  - OCSP responders: 2x per region (HA)
  - OCSP stapling enabled on all nginx/Apache
  - CRL published every 24 hours to CDN
  - 90-day CRL validity for offline environments

Monitoring:
  - Certificate expiry alerts: 90/30/7 days
  - Unauthorised CA detection: Certificate Transparency logs
  - Monthly certificate inventory audit
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| 3-tier PKI | Root (offline) → Intermediate → Issuing → End-entity |
| Root CA | Air-gapped, HSM, key ceremony, offline |
| CRL | Periodic revocation list; latency up to validity period |
| OCSP | Real-time revocation check; privacy concern |
| OCSP Stapling | Server pre-fetches OCSP; best of both worlds |
| HSM | FIPS 140-2 L3; keys never leave hardware |
| SPIFFE/SPIRE | Workload identity; SVIDs replace static credentials |
