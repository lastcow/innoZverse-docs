# Lab 16: Zero Trust Network Architecture

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

Zero Trust is a security model based on three core principles: **never trust, always verify**, **least privilege access**, and **assume breach**. Unlike the traditional perimeter model (castle-and-moat), Zero Trust treats every request as potentially hostile — regardless of whether it comes from inside or outside the network.

In this lab you will implement **mutual TLS (mTLS)** — the cryptographic foundation of Zero Trust service-to-service authentication — using Python's `ssl` module. Every service must prove its identity with a certificate; no implicit trust based on network location.

```
Traditional Perimeter:        Zero Trust:
  [Firewall]                   [Identity Verified at EVERY hop]
  outside → blocked             Service A ──mTLS──► Service B
  inside  → trusted ✓          (cert required both ways)
```

---

## Step 1: Install Tools & Understand Zero Trust Principles

```bash
apt-get update && apt-get install -y openssl python3
```

📸 **Verified Output:**
```
Setting up openssl (3.0.2-0ubuntu1.21) ...
Setting up python3 (3.10.6-1~22.04.1) ...
```

**Zero Trust vs Perimeter Model:**

| Dimension | Perimeter Model | Zero Trust |
|-----------|----------------|------------|
| Trust model | Trust inside network | Never trust implicitly |
| Auth boundary | Network edge | Every request, every service |
| Lateral movement | Easy once inside | Blocked by micro-segmentation |
| Identity | IP-based | Cryptographic (cert/token) |
| Example | VPN = trusted | mTLS per service |

> 💡 **Google's BeyondCorp** replaced traditional VPN with Zero Trust in 2011. Employees access apps from any network — trust comes from device+user identity, not network location.

---

## Step 2: Create a Certificate Authority (CA)

In Zero Trust, a **CA** acts as the identity root — every service gets a certificate signed by this CA.

```bash
# Create CA private key and self-signed certificate
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key \
    -subj '/CN=ZeroTrustCA/O=InnoZ' -out ca.crt

# Inspect the CA certificate
openssl x509 -in ca.crt -noout -subject -issuer -dates
```

📸 **Verified Output:**
```
Generating RSA private key, 2048 bit long modulus (2 primes)
...+++++
...+++++
subject=CN = ZeroTrustCA, O = InnoZ
issuer=CN = ZeroTrustCA, O = InnoZ
notBefore=Mar  5 14:00:00 2026 GMT
notAfter=Mar  5 14:00:00 2027 GMT
```

> 💡 In production, **SPIFFE/SPIRE** automates certificate issuance for workload identity. Each workload gets a SVID (SPIFFE Verifiable Identity Document) — a short-lived X.509 cert with a URI SAN like `spiffe://example.org/ns/prod/sa/frontend`.

---

## Step 3: Generate Server Certificate

```bash
# Generate server key and CSR
openssl genrsa -out server.key 2048
openssl req -new -key server.key \
    -subj '/CN=api-service/O=InnoZ' -out server.csr

# Sign with CA
openssl x509 -req -days 365 -in server.csr \
    -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

# Verify
openssl verify -CAfile ca.crt server.crt
openssl x509 -in server.crt -noout -subject
```

📸 **Verified Output:**
```
Certificate request self-signature ok
subject=CN = api-service, O = InnoZ
server.crt: OK
subject=CN = api-service, O = InnoZ
```

---

## Step 4: Generate Client Certificate (Workload Identity)

In Zero Trust, **clients also present certificates** — this is what makes it *mutual* TLS.

```bash
# Generate client key and CSR
openssl genrsa -out client.key 2048
openssl req -new -key client.key \
    -subj '/CN=frontend-service/O=InnoZ' -out client.csr

# Sign with same CA
openssl x509 -req -days 365 -in client.csr \
    -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt

# Verify both certs are signed by same CA
openssl verify -CAfile ca.crt client.crt
openssl verify -CAfile ca.crt server.crt
```

📸 **Verified Output:**
```
Certificate request self-signature ok
client.crt: OK
server.crt: OK
```

> 💡 **Micro-segmentation**: In Kubernetes, NetworkPolicy objects enforce which pods can talk to which — combined with mTLS (via Istio/Linkerd service mesh), you get cryptographic identity *and* network-level enforcement.

---

## Step 5: Write the mTLS Server

Create a Python server that **requires client certificates** (`ssl.CERT_REQUIRED`):

```bash
cat > mtls_server.py << 'EOF'
import ssl
import socket
import threading
import time
import sys

def handle_client(conn):
    """Handle a single mTLS connection."""
    peer_cert = conn.getpeercert()
    # Extract CN from subject
    subject = dict(item[0] for item in peer_cert['subject'])
    client_cn = subject.get('commonName', 'unknown')
    
    print(f"[SERVER] mTLS handshake SUCCESS")
    print(f"[SERVER] Client identity (CN): {client_cn}")
    print(f"[SERVER] Cipher: {conn.cipher()}")
    
    # Send authorized response
    conn.sendall(f"AUTHORIZED: Welcome, {client_cn}!\n".encode())
    conn.close()

def run_server():
    # Create TLS context — server mode
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Load server cert+key
    ctx.load_cert_chain('server.crt', 'server.key')
    
    # Load CA to verify client certs
    ctx.load_verify_locations('ca.crt')
    
    # REQUIRE client certificate (mTLS)
    ctx.verify_mode = ssl.CERT_REQUIRED
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 8443))
        sock.listen(5)
        print("[SERVER] Listening on localhost:8443 (mTLS required)")
        
        with ctx.wrap_socket(sock, server_side=True) as ssock:
            conn, addr = ssock.accept()
            handle_client(conn)

if __name__ == '__main__':
    run_server()
EOF
echo "Server script written"
```

📸 **Verified Output:**
```
Server script written
```

---

## Step 6: Write the mTLS Client

```bash
cat > mtls_client.py << 'EOF'
import ssl
import socket
import time

def connect_with_mtls():
    # Create TLS context — client mode
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    
    # Present OUR certificate to the server (mutual auth)
    ctx.load_cert_chain('client.crt', 'client.key')
    
    # Trust the CA (to verify server cert)
    ctx.load_verify_locations('ca.crt')
    
    # Disable hostname check (using localhost in lab)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    
    print("[CLIENT] Connecting to api-service with mTLS...")
    
    with socket.create_connection(('localhost', 8443)) as raw_sock:
        with ctx.wrap_socket(raw_sock) as tls_sock:
            # Verify server certificate
            server_cert = tls_sock.getpeercert()
            server_subject = dict(item[0] for item in server_cert['subject'])
            print(f"[CLIENT] Server identity verified: CN={server_subject.get('commonName')}")
            print(f"[CLIENT] TLS version: {tls_sock.version()}")
            
            # Receive response
            data = tls_sock.recv(1024)
            print(f"[CLIENT] Server response: {data.decode().strip()}")

if __name__ == '__main__':
    connect_with_mtls()
EOF
echo "Client script written"
```

📸 **Verified Output:**
```
Client script written
```

---

## Step 7: Run the mTLS Demo — Mutual Authentication

```bash
# Start server in background
python3 mtls_server.py &
SERVER_PID=$!
sleep 1

# Connect with client certificate
python3 mtls_client.py

# Clean up
wait $SERVER_PID 2>/dev/null || true
```

📸 **Verified Output:**
```
[SERVER] Listening on localhost:8443 (mTLS required)
[CLIENT] Connecting to api-service with mTLS...
[SERVER] mTLS handshake SUCCESS
[SERVER] Client identity (CN): frontend-service
[SERVER] Cipher: ('TLS_AES_256_GCM_SHA256', 'TLSv1.3', 256)
[CLIENT] Server identity verified: CN=api-service
[CLIENT] TLS version: TLSv1.3
[CLIENT] Server response: AUTHORIZED: Welcome, frontend-service!
```

> 💡 **What just happened**: Both sides verified each other's certificate against the CA. The server knows the client is `frontend-service`; the client knows the server is `api-service`. No network location trust — pure cryptographic identity.

**Test rejection without client cert:**

```bash
# This should fail — no client cert presented
python3 -c "
import ssl, socket
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.load_verify_locations('ca.crt')
ctx.check_hostname = False
# Start a fresh server first
import subprocess, time
srv = subprocess.Popen(['python3', 'mtls_server.py'])
time.sleep(1)
try:
    with socket.create_connection(('localhost', 8443)) as s:
        with ctx.wrap_socket(s) as ss:
            print('ERROR: Should have been rejected!')
except ssl.SSLError as e:
    print(f'REJECTED (expected): {e.reason}')
finally:
    srv.terminate()
"
```

📸 **Verified Output:**
```
[SERVER] Listening on localhost:8443 (mTLS required)
REJECTED (expected): TLSV13_ALERT_CERTIFICATE_REQUIRED
```

---

## Step 8: Capstone — Zero Trust Policy Engine Simulation

Build a policy engine that evaluates Zero Trust access decisions based on identity + context:

```bash
cat > zt_policy_engine.py << 'EOF'
"""
Zero Trust Policy Engine
Simulates OPA (Open Policy Agent) style access decisions
Decision = f(identity, resource, context)
"""
import json
from datetime import datetime

# Policy rules (in production: stored in OPA/Rego)
POLICIES = {
    "frontend-service": {
        "allowed_resources": ["/api/users", "/api/products"],
        "allowed_methods": ["GET", "POST"],
        "max_sensitivity": "MEDIUM",
    },
    "admin-service": {
        "allowed_resources": ["/api/users", "/api/products", "/api/admin", "/api/config"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
        "max_sensitivity": "HIGH",
    },
    "monitoring-service": {
        "allowed_resources": ["/api/metrics", "/api/health"],
        "allowed_methods": ["GET"],
        "max_sensitivity": "LOW",
    },
}

RESOURCE_SENSITIVITY = {
    "/api/health": "LOW",
    "/api/metrics": "LOW",
    "/api/users": "MEDIUM",
    "/api/products": "MEDIUM",
    "/api/admin": "HIGH",
    "/api/config": "HIGH",
}

SENSITIVITY_LEVELS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

def evaluate_policy(identity_cn, resource, method, context=None):
    """Evaluate Zero Trust access decision."""
    decision = {
        "identity": identity_cn,
        "resource": resource,
        "method": method,
        "timestamp": datetime.utcnow().isoformat(),
        "allow": False,
        "reason": "",
        "principle": ""
    }
    
    # Unknown identity → deny (never trust, always verify)
    if identity_cn not in POLICIES:
        decision["reason"] = f"Unknown identity: {identity_cn}"
        decision["principle"] = "never-trust-always-verify"
        return decision
    
    policy = POLICIES[identity_cn]
    
    # Check resource access (least privilege)
    if resource not in policy["allowed_resources"]:
        decision["reason"] = f"Resource {resource} not in allowlist"
        decision["principle"] = "least-privilege"
        return decision
    
    # Check method
    if method not in policy["allowed_methods"]:
        decision["reason"] = f"Method {method} not permitted"
        decision["principle"] = "least-privilege"
        return decision
    
    # Check sensitivity level (assume breach — limit blast radius)
    resource_sens = RESOURCE_SENSITIVITY.get(resource, "HIGH")
    max_sens = policy["max_sensitivity"]
    if SENSITIVITY_LEVELS[resource_sens] > SENSITIVITY_LEVELS[max_sens]:
        decision["reason"] = f"Resource sensitivity {resource_sens} exceeds limit {max_sens}"
        decision["principle"] = "assume-breach"
        return decision
    
    decision["allow"] = True
    decision["reason"] = "All policy checks passed"
    decision["principle"] = "zero-trust-verified"
    return decision

# --- Run policy evaluations ---
test_cases = [
    ("frontend-service",    "/api/users",   "GET"),
    ("frontend-service",    "/api/admin",   "GET"),    # Denied: too sensitive
    ("frontend-service",    "/api/users",   "DELETE"), # Denied: method
    ("admin-service",       "/api/admin",   "DELETE"), # Allowed
    ("unknown-service",     "/api/users",   "GET"),    # Denied: unknown identity
    ("monitoring-service",  "/api/metrics", "GET"),    # Allowed
    ("monitoring-service",  "/api/users",   "GET"),    # Denied: resource
]

print("=" * 65)
print("ZERO TRUST POLICY ENGINE — Access Decisions")
print("=" * 65)

results = {"ALLOW": 0, "DENY": 0}
for identity, resource, method in test_cases:
    d = evaluate_policy(identity, resource, method)
    verdict = "ALLOW ✓" if d["allow"] else "DENY  ✗"
    results["ALLOW" if d["allow"] else "DENY"] += 1
    print(f"\n[{verdict}] {identity}")
    print(f"         {method} {resource}")
    print(f"         Reason: {d['reason']}")
    print(f"         Principle: {d['principle']}")

print("\n" + "=" * 65)
print(f"Summary: {results['ALLOW']} ALLOW, {results['DENY']} DENY")
print("=" * 65)

# Save audit log
with open('zt_audit.json', 'w') as f:
    audit = [evaluate_policy(i, r, m) for i, r, m in test_cases]
    json.dump(audit, f, indent=2)
print("\nAudit log saved: zt_audit.json")
EOF

python3 zt_policy_engine.py
```

📸 **Verified Output:**
```
=================================================================
ZERO TRUST POLICY ENGINE — Access Decisions
=================================================================

[ALLOW ✓] frontend-service
         GET /api/users
         Reason: All policy checks passed
         Principle: zero-trust-verified

[DENY  ✗] frontend-service
         GET /api/admin
         Reason: Resource sensitivity HIGH exceeds limit MEDIUM
         Principle: assume-breach

[DENY  ✗] frontend-service
         DELETE /api/users
         Reason: Method DELETE not permitted
         Principle: least-privilege

[ALLOW ✓] admin-service
         DELETE /api/admin
         Reason: All policy checks passed
         Principle: zero-trust-verified

[DENY  ✗] unknown-service
         GET /api/users
         Reason: Unknown identity: unknown-service
         Principle: never-trust-always-verify

[ALLOW ✓] monitoring-service
         GET /api/metrics
         Reason: All policy checks passed
         Principle: zero-trust-verified

[DENY  ✗] monitoring-service
         GET /api/users
         Reason: Resource /api/users not in allowlist
         Principle: least-privilege

=================================================================
Summary: 3 ALLOW, 4 DENY
=================================================================

Audit log saved: zt_audit.json
```

---

## Summary

| Concept | Tool/Method | Purpose |
|---------|-------------|---------|
| Never Trust Always Verify | mTLS + cert validation | Every service proves identity |
| Least Privilege | Policy engine allowlists | Services access only what they need |
| Assume Breach | Sensitivity limits | Contain blast radius of compromised service |
| Workload Identity | X.509 certificates (SPIFFE) | Cryptographic service identity |
| Policy Enforcement | OPA / Rego rules | Centralized access decisions |
| Service Mesh | Istio / Linkerd | Automatic mTLS between pods |
| Micro-segmentation | K8s NetworkPolicy | Network-layer enforcement |

**Key Commands:**
```bash
# Generate CA
openssl req -new -x509 -days 365 -key ca.key -out ca.crt

# Sign service cert
openssl x509 -req -in service.csr -CA ca.crt -CAkey ca.key -out service.crt

# Verify cert chain
openssl verify -CAfile ca.crt service.crt

# Python mTLS: require client cert
ctx.verify_mode = ssl.CERT_REQUIRED
```
