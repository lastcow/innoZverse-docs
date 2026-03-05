# Lab 09: Container & Kubernetes Security

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Architect container security from image to runtime
- Understand Kubernetes admission controllers and Pod Security Standards
- Design network policies and secrets management
- Build a Kubernetes YAML security policy validator

---

## Step 1: Container Security Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                  CONTAINER SECURITY LAYERS               │
│                                                         │
│  1. BUILD TIME          2. DEPLOY TIME      3. RUNTIME  │
│  ┌────────────┐        ┌─────────────┐    ┌──────────┐ │
│  │Image scan  │        │Admission    │    │Falco     │ │
│  │Base image  │   →    │Controllers  │ →  │Runtime   │ │
│  │SBOM gen    │        │Pod Security │    │Detection │ │
│  │Secret scan │        │Standards    │    │Network   │ │
│  │Dockerfile  │        │Network      │    │Policies  │ │
│  │lint        │        │Policies     │    │          │ │
│  └────────────┘        └─────────────┘    └──────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Step 2: Image Security

**Base image selection:**
- Use minimal base images: `distroless`, `alpine`, `scratch`
- Never use `latest` tag — always pin to digest: `nginx@sha256:abc...`
- Build from official images; verify provenance (Sigstore/Cosign)

**Dockerfile security:**
```dockerfile
# BAD
FROM ubuntu:latest
RUN apt install -y curl wget
COPY . /app
CMD ["python", "app.py"]

# GOOD
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    adduser --disabled-password --gecos '' appuser
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8080
CMD ["python", "-m", "gunicorn", "app:app"]
```

**Image scanning tools:**
| Tool | Type | Integration |
|------|------|------------|
| Trivy | Open source | CI/CD, registry |
| Snyk | Commercial | IDE, CI/CD |
| Grype | Open source | CI/CD |
| AWS ECR | Cloud-native | Registry scan |
| Prisma Cloud | Commercial | Full lifecycle |

---

## Step 3: Pod Security Standards

**Three enforcement levels:**

| Level | Description | Who Should Use |
|-------|-----------|----------------|
| **Privileged** | No restrictions | System namespaces (kube-system) |
| **Baseline** | Minimum restrictions, blocks known privesc | Most workloads |
| **Restricted** | Hardened, follows security best practices | Security-sensitive workloads |

**Restricted policy enforces:**
- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities: drop: [ALL]`
- `seccompProfile: RuntimeDefault`
- No hostPath volumes

**Apply PSS to namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

---

## Step 4: Kubernetes Security Policy Validator

```python
manifests = [
    {
        'name': 'insecure-pod',
        'spec': {
            'containers': [{
                'name': 'app',
                'image': 'nginx:latest',
                'securityContext': {'privileged': True, 'runAsRoot': True},
                'resources': {}
            }]
        },
        'metadata': {'labels': {}}
    },
    {
        'name': 'secure-pod',
        'spec': {
            'containers': [{
                'name': 'app',
                'image': 'nginx:1.25.3',
                'securityContext': {
                    'privileged': False,
                    'runAsNonRoot': True,
                    'readOnlyRootFilesystem': True,
                    'allowPrivilegeEscalation': False
                },
                'resources': {
                    'limits': {'cpu': '500m', 'memory': '256Mi'},
                    'requests': {'cpu': '100m', 'memory': '64Mi'}
                }
            }]
        },
        'metadata': {'labels': {'app': 'web'}}
    }
]

def validate(manifest):
    findings = []
    for c in manifest['spec']['containers']:
        sc = c.get('securityContext', {})
        if sc.get('privileged'):                             findings.append('CRITICAL: privileged=true')
        if not sc.get('runAsNonRoot'):                       findings.append('HIGH: runAsNonRoot not set')
        if not sc.get('readOnlyRootFilesystem'):             findings.append('MEDIUM: readOnlyRootFilesystem not set')
        if not sc.get('allowPrivilegeEscalation') == False:  findings.append('HIGH: allowPrivilegeEscalation not explicitly false')
        if ':latest' in c.get('image', ''):                  findings.append('MEDIUM: using :latest tag')
        if not c.get('resources', {}).get('limits'):         findings.append('MEDIUM: no resource limits')
    return findings

print('=== Kubernetes Security Policy Validator ===')
for m in manifests:
    findings = validate(m)
    status = 'FAIL' if findings else 'PASS'
    print(f'  [{status}] {m["name"]}')
    for f in findings:
        print(f'         {f}')

print()
print('Pod Security Standards: Privileged | Baseline | Restricted')
print('Admission Controllers: OPA/Gatekeeper, Kyverno, PSA')
```

📸 **Verified Output:**
```
=== Kubernetes Security Policy Validator ===
  [FAIL] insecure-pod
         CRITICAL: privileged=true
         HIGH: runAsNonRoot not set
         MEDIUM: readOnlyRootFilesystem not set
         HIGH: allowPrivilegeEscalation not explicitly false
         MEDIUM: using :latest tag
         MEDIUM: no resource limits
  [PASS] secure-pod

Pod Security Standards: Privileged | Baseline | Restricted
Admission Controllers: OPA/Gatekeeper, Kyverno, PSA
```

---

## Step 5: Admission Controllers

**Types of admission controllers:**

| Controller | Type | Use Case |
|-----------|------|---------|
| Pod Security Admission | Built-in | Enforce PSS levels |
| OPA/Gatekeeper | Webhook | Custom Rego policies |
| Kyverno | Webhook | YAML-native policies |
| ImagePolicyWebhook | Built-in | Require signed images |
| ValidatingWebhookConfiguration | Webhook | Custom validation |

**Kyverno policy example:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged-containers
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-privileged
      match:
        resources:
          kinds: [Pod]
      validate:
        message: "Privileged containers are not allowed"
        pattern:
          spec:
            containers:
              - securityContext:
                  privileged: "false"
```

---

## Step 6: Network Policies

**Default deny all + explicit allow:**
```yaml
# Default deny all ingress/egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

---
# Allow frontend → backend on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8080
```

> 💡 **CNI plugins that support NetworkPolicy**: Calico, Cilium, Weave. The default Kubernetes networking (kubenet) does NOT enforce NetworkPolicy — you must install a compliant CNI.

---

## Step 7: Secrets Management

**Kubernetes secrets problems:**
- Stored base64-encoded in etcd (not encrypted by default)
- Can be exposed via `kubectl get secret` to anyone with RBAC access
- Appear in environment variables (visible in `/proc`)

**Best practices:**
1. Enable etcd encryption at rest (`EncryptionConfiguration`)
2. Use external secrets manager (HashiCorp Vault, AWS Secrets Manager)
3. Inject secrets at runtime via CSI driver (no env vars)
4. RBAC: least privilege on secrets — workload SA only reads its own

**Vault + Kubernetes (CSI driver):**
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-db-creds
spec:
  provider: vault
  parameters:
    roleName: "db-app"
    objects: |
      - objectName: "db-password"
        secretPath: "secret/data/db"
        secretKey: "password"
```

---

## Step 8: Capstone — Kubernetes Security Architecture

**Scenario:** Production Kubernetes cluster for PCI DSS workloads

```
Cluster Hardening:
  - EKS (AWS) with private endpoint
  - Node groups: t3.large, locked down SGs
  - Kubernetes version: 1.29+ (LTS), auto-upgrade minor
  - etcd: AWS-managed, encrypted at rest (AES-256)

Image Security:
  - ECR private registry; no Docker Hub allowed
  - Trivy scanning in CI/CD; fail build if CRITICAL CVEs
  - Cosign image signing; verify in admission webhook
  - Base image policy: distroless or alpine only

Pod Security:
  - Namespace: production → PSS: Restricted
  - Namespace: system → PSS: Baseline
  - Kyverno: 15 policies (no latest tag, resource limits, no privesc)
  - OPA/Gatekeeper: compliance checks (PCI DSS specific)

Network:
  - Calico CNI with NetworkPolicy enforcement
  - Default deny all namespaces
  - Istio service mesh: mTLS between all services
  - Egress: only explicit allowlist

Secrets:
  - HashiCorp Vault (enterprise) via CSI driver
  - No secrets in environment variables
  - Vault dynamic secrets for DB credentials (1h TTL)
  - AWS KMS for envelope encryption

Runtime:
  - Falco: runtime threat detection
  - Rules: shell spawned in container, sensitive file access
  - Alerts: → SIEM → SOAR playbook
  - Kubernetes audit logs → CloudWatch → Splunk

Access:
  - No direct kubectl access in production
  - ArgoCD for GitOps deployments
  - Stern/Lens access via PAM session recording
  - RBAC: namespace-scoped; no cluster-admin in prod
```

---

## Summary

| Layer | Control | Implementation |
|-------|---------|----------------|
| Image | Scan + sign | Trivy, Cosign, ECR |
| Admission | Policy enforcement | Kyverno, Gatekeeper, PSA |
| Pod security | Hardened context | PSS Restricted, drop capabilities |
| Network | Micro-segmentation | NetworkPolicy + Istio mTLS |
| Secrets | External vault | HashiCorp Vault CSI driver |
| Runtime | Threat detection | Falco rules + SIEM alerting |
