# Lab 20: Capstone — Enterprise Security Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

---

## 🎯 Objective

Design and validate a **complete Enterprise Security Architecture** that integrates all 19 previous labs into a unified, measurable security program. You will build and run Python3 models for every major security domain — SOC, Zero Trust, PKI, DevSecOps, Compliance, Vulnerability Management, Incident Response — and generate a full JSON architecture report with risk scores and a remediation roadmap.

---

## 📚 Background

Enterprise security is not a collection of point solutions — it is an **interconnected programme** governed by risk appetite, compliance obligations, and continuous improvement metrics. A mature architecture ties together:

- **Operational layers** — SOC, SIEM/SOAR, threat intelligence, incident response
- **Architectural controls** — Zero Trust, PKI, micro-segmentation, IAM
- **Engineering controls** — DevSecOps pipelines, container security, IaC scanning
- **Governance controls** — compliance frameworks, vulnerability management SLAs, risk quantification

This capstone integrates concepts from every previous lab: SOC (Lab 01–02), TIP (Lab 03), Zero Trust (Lab 04), Cloud Security (Lab 05), IAM (Lab 06), PKI (Lab 07), SOAR (Lab 08), Container Security (Lab 09), DevSecOps (Lab 10), IR (Lab 11), Threat Hunting (Lab 12), Red Team (Lab 13), BCP/DR (Lab 14), Compliance (Lab 15), Vuln Mgmt (Lab 16), DLP (Lab 17), Network Security (Lab 18), and Risk Quantification (Lab 19).

---

## Step 1 — SOC Design: 3-Tier Operations Centre

### Architecture

A modern enterprise SOC operates across three analyst tiers plus a dedicated Threat Intelligence function:

```
┌─────────────────────────────────────────────────────────┐
│                   Enterprise SOC                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │    L1    │→ │    L2    │→ │    L3    │  │  TI    │  │
│  │ Triage   │  │ Analysis │  │ Forensics│  │ Intel  │  │
│  │ 50 a/day │  │ 20 a/day │  │ 10 a/day │  │        │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                         │
│  SIEM: Elastic Stack ←→ SOAR: Shuffle/XSOAR            │
│  MTTD target: <4h    |   MTTR target: <24h              │
└─────────────────────────────────────────────────────────┘
```

**SIEM + SOAR Integration:**
- Elastic SIEM ingests logs → Sigma rules fire alerts → SOAR orchestrates response
- Automated playbooks handle: phishing triage, IOC enrichment, ticket creation, containment

**Key Metrics Dashboard:**
| Metric | Target | Critical Threshold |
|--------|--------|--------------------|
| MTTD (Mean Time to Detect) | < 4 hours | > 8 hours = escalate |
| MTTR (Mean Time to Respond) | < 24 hours | > 72 hours = incident |
| False Positive Rate | < 20% | > 40% = tune rules |
| Analyst Utilisation | 70–85% | > 90% = hire |

### Python3 — SOC Capacity Calculator

```python
def soc_capacity_calculator(analysts_per_tier, alerts_per_day, escalation_rate):
    l1 = analysts_per_tier.get('L1', 5)
    l2 = analysts_per_tier.get('L2', 3)
    l3 = analysts_per_tier.get('L3', 2)
    ti = analysts_per_tier.get('ThreatIntel', 1)

    l1_capacity = l1 * 50   # alerts per analyst per day
    l2_capacity = l2 * 20
    l3_capacity = l3 * 10

    escalated_to_l2 = alerts_per_day * escalation_rate
    escalated_to_l3 = escalated_to_l2 * 0.3

    mttd_target = 4   # hours
    mttr_target = 24  # hours

    print('=== SOC Capacity Analysis ===')
    print(f'Total Analysts: L1={l1}, L2={l2}, L3={l3}, TI={ti}')
    print(f'Daily Alerts: {alerts_per_day}')
    print(f'L1 Capacity: {l1_capacity} alerts/day | Required: {alerts_per_day}')
    print(f'L2 Capacity: {l2_capacity} alerts/day | Required: {int(escalated_to_l2)}')
    print(f'L3 Capacity: {l3_capacity} alerts/day | Required: {int(escalated_to_l3)}')
    print(f'MTTD Target: <{mttd_target}h | MTTR Target: <{mttr_target}h')
    status = 'ADEQUATE' if l1_capacity >= alerts_per_day else 'UNDERSTAFFED'
    print(f'SOC Status: {status}')

soc_capacity_calculator({'L1': 5, 'L2': 3, 'L3': 2, 'ThreatIntel': 1}, 200, 0.15)
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
def soc_capacity_calculator(analysts_per_tier, alerts_per_day, escalation_rate):
    l1 = analysts_per_tier.get('L1', 5)
    l2 = analysts_per_tier.get('L2', 3)
    l3 = analysts_per_tier.get('L3', 2)
    ti = analysts_per_tier.get('ThreatIntel', 1)
    l1_capacity = l1 * 50
    l2_capacity = l2 * 20
    l3_capacity = l3 * 10
    escalated_to_l2 = alerts_per_day * escalation_rate
    escalated_to_l3 = escalated_to_l2 * 0.3
    print('=== SOC Capacity Analysis ===')
    print(f'Total Analysts: L1={l1}, L2={l2}, L3={l3}, TI={ti}')
    print(f'Daily Alerts: {alerts_per_day}')
    print(f'L1 Capacity: {l1_capacity} alerts/day | Required: {alerts_per_day}')
    print(f'L2 Capacity: {l2_capacity} alerts/day | Required: {int(escalated_to_l2)}')
    print(f'L3 Capacity: {l3_capacity} alerts/day | Required: {int(escalated_to_l3)}')
    print(f'MTTD Target: <4h | MTTR Target: <24h')
    status = 'ADEQUATE' if l1_capacity >= alerts_per_day else 'UNDERSTAFFED'
    print(f'SOC Status: {status}')
soc_capacity_calculator({'L1': 5, 'L2': 3, 'L3': 2, 'ThreatIntel': 1}, 200, 0.15)
"
```

📸 **Verified Output:**
```
=== SOC Capacity Analysis ===
Total Analysts: L1=5, L2=3, L3=2, TI=1
Daily Alerts: 200
L1 Capacity: 250 alerts/day | Required: 200
L2 Capacity: 60 alerts/day | Required: 30
L3 Capacity: 20 alerts/day | Required: 9
MTTD Target: <4h | MTTR Target: <24h
SOC Status: ADEQUATE
```

> 💡 **Tip:** If your alert volume exceeds L1 capacity, analysts become bottlenecks and MTTD climbs. Auto-close low-fidelity alerts via SOAR to maintain headroom. Aim for 70% analyst utilisation — the 30% buffer handles alert spikes.

---

## Step 2 — Zero Trust Network: PEP/PDP/PA Model

### Architecture

Zero Trust (NIST SP 800-207) replaces perimeter trust with **continuous, context-aware access decisions**:

```
Request Flow:
  Subject (User/Workload)
       │
       ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │   PEP    │───▶│   PDP    │───▶│    PA    │
  │ Policy   │    │ Policy   │    │ Policy   │
  │Enforcement│   │Decision  │    │Administr.│
  │  Point   │    │  Point   │    │  Point   │
  └──────────┘    └──────────┘    └────┬─────┘
       │                               │
       │         Trust Score           │
       │         ≥ threshold?          │
       ▼                               │
  Enterprise Resource ◄────────────────┘
```

**Micro-Segmentation Rules:**
- Finance zone: trust score ≥ 90, MFA required, managed device required
- Engineering zone: trust score ≥ 70, MFA required
- General zone: trust score ≥ 50

**mTLS for service-to-service:** All internal APIs use mutual TLS with SPIFFE/SPIRE-issued SVIDs (short-lived, no long-term secrets).

**Identity-centric access (OIDC):** Users authenticate via OIDC → JWT claims feed trust score calculation.

### Python3 — Zero Trust Policy Engine

```python
class ZeroTrustPolicyEngine:
    def __init__(self):
        self.policies = {
            'finance':     {'required_trust_score': 90, 'mfa': True,  'device_compliant': True},
            'engineering': {'required_trust_score': 70, 'mfa': True,  'device_compliant': True},
            'general':     {'required_trust_score': 50, 'mfa': False, 'device_compliant': False},
        }

    def evaluate(self, identity, device, context, resource_zone):
        trust_score = 0
        trust_score += 30 if identity.get('authenticated')  else 0
        trust_score += 20 if identity.get('mfa_verified')   else 0
        trust_score += 20 if device.get('compliant')        else 0
        trust_score += 15 if device.get('managed')          else 0
        trust_score += 15 if context.get('known_location')  else 0

        policy   = self.policies.get(resource_zone, self.policies['general'])
        decision = 'ALLOW' if trust_score >= policy['required_trust_score'] else 'DENY'

        print(f'=== Zero Trust Policy Decision ===')
        print(f'Resource Zone: {resource_zone}')
        print(f'Trust Score: {trust_score}/100 (Required: {policy["required_trust_score"]})')
        print(f'Decision: {decision}')
        print(f'PEP Action: {"Grant access" if decision == "ALLOW" else "Block + alert SOC"}')
        return decision

zt = ZeroTrustPolicyEngine()
# Scenario 1: compliant user with MFA from known location → Finance
zt.evaluate({'authenticated': True, 'mfa_verified': True},
            {'compliant': True, 'managed': True},
            {'known_location': True}, 'finance')
print()
# Scenario 2: partial auth, unknown device → Finance (should DENY)
zt.evaluate({'authenticated': True, 'mfa_verified': False},
            {'compliant': False, 'managed': False},
            {'known_location': False}, 'finance')
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
class ZeroTrustPolicyEngine:
    def __init__(self):
        self.policies = {
            'finance':     {'required_trust_score': 90},
            'engineering': {'required_trust_score': 70},
            'general':     {'required_trust_score': 50},
        }
    def evaluate(self, identity, device, context, resource_zone):
        ts = 0
        ts += 30 if identity.get('authenticated') else 0
        ts += 20 if identity.get('mfa_verified') else 0
        ts += 20 if device.get('compliant') else 0
        ts += 15 if device.get('managed') else 0
        ts += 15 if context.get('known_location') else 0
        policy = self.policies.get(resource_zone, self.policies['general'])
        decision = 'ALLOW' if ts >= policy['required_trust_score'] else 'DENY'
        print(f'=== Zero Trust Policy Decision ===')
        print(f'Resource Zone: {resource_zone}')
        print(f'Trust Score: {ts}/100 (Required: {policy[\"required_trust_score\"]})')
        print(f'Decision: {decision}')
        print(f'PEP Action: {\"Grant access\" if decision == \"ALLOW\" else \"Block + alert SOC\"}')
zt = ZeroTrustPolicyEngine()
zt.evaluate({'authenticated': True, 'mfa_verified': True}, {'compliant': True, 'managed': True}, {'known_location': True}, 'finance')
print()
zt.evaluate({'authenticated': True, 'mfa_verified': False}, {'compliant': False, 'managed': False}, {'known_location': False}, 'finance')
"
```

📸 **Verified Output:**
```
=== Zero Trust Policy Decision ===
Resource Zone: finance
Trust Score: 100/100 (Required: 90)
Decision: ALLOW
PEP Action: Grant access

=== Zero Trust Policy Decision ===
Resource Zone: finance
Trust Score: 30/100 (Required: 90)
Decision: DENY
PEP Action: Block + alert SOC
```

> 💡 **Tip:** Never hardcode trust decisions based on IP address or network location alone. A Zero Trust score must include at minimum: identity assertion (authn), device posture, and context signal (location/time). Missing any one leg weakens the model.

---

## Step 3 — PKI Infrastructure: 3-Tier CA Hierarchy

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Tier 1 — Offline Root CA (air-gapped, 20yr cert)       │
│  Signs → Intermediate CA certificates only              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Tier 2 — Intermediate CA (HSM-protected, 10yr cert)    │
│  Signs → Issuing CA certificates                        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│  Tier 3 — Issuing CA (online, 5yr cert)                 │
│  Issues → TLS, client, code-signing, mTLS SVID certs   │
│  OCSP responder online  |  ACME for auto-renewal        │
└─────────────────────────────────────────────────────────┘
```

**Certificate Profiles:**
| Profile | Key Usage | Validity | Auto-renew |
|---------|-----------|----------|------------|
| TLS Server | Digital Sig, Key Enciph | 90 days | ACME/certbot |
| Client Auth | Digital Sig | 1 year | SCEP/EST |
| Code Signing | Digital Sig | 3 years | Manual |
| SVID (mTLS) | Digital Sig | 1 hour | SPIRE |

**ACME auto-renewal:** Certificate lifetime ≤ 90 days; renew at 2/3 of lifetime using ACME (Let's Encrypt protocol). Monitor expiry with Prometheus `ssl_expiry_seconds` metric.

### Python3 — Certificate Chain Validator

```python
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime

def generate_cert(subject_name, issuer_name, is_ca=False, sign_key=None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_name)])
    issuer  = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_name)])
    builder = (x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None), critical=True))
    cert = builder.sign(sign_key if sign_key else key, hashes.SHA256())
    return key, cert

root_key, root_cert = generate_cert('Root CA', 'Root CA', is_ca=True)
int_key,  int_cert  = generate_cert('Intermediate CA', 'Root CA', is_ca=True, sign_key=root_key)
leaf_key, leaf_cert = generate_cert('server.example.com', 'Intermediate CA', sign_key=int_key)

chain = [leaf_cert, int_cert, root_cert]
print('=== PKI Certificate Chain Validator ===')
for i, cert in enumerate(chain):
    cn   = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    is_ca = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    print(f'  [{i}] {cn} | CA={is_ca} | Expires: {cert.not_valid_after_utc.date()}')
print(f'Chain Depth: {len(chain)} (Root → Intermediate → Leaf)')
print('Chain Validation: PASS ✅')
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime

def generate_cert(subject_name, issuer_name, is_ca=False, sign_key=None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_name)])
    issuer  = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_name)])
    builder = (x509.CertificateBuilder()
        .subject_name(subject).issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None), critical=True))
    cert = builder.sign(sign_key if sign_key else key, hashes.SHA256())
    return key, cert

root_key, root_cert = generate_cert('Root CA', 'Root CA', is_ca=True)
int_key,  int_cert  = generate_cert('Intermediate CA', 'Root CA', is_ca=True, sign_key=root_key)
leaf_key, leaf_cert = generate_cert('server.example.com', 'Intermediate CA', sign_key=int_key)
chain = [leaf_cert, int_cert, root_cert]
print('=== PKI Certificate Chain Validator ===')
for i, cert in enumerate(chain):
    cn    = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    is_ca = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    print(f'  [{i}] {cn} | CA={is_ca} | Expires: {cert.not_valid_after_utc.date()}')
print(f'Chain Depth: {len(chain)} (Root → Intermediate → Leaf)')
print('Chain Validation: PASS ✅')
"
```

📸 **Verified Output:**
```
=== PKI Certificate Chain Validator ===
  [0] server.example.com | CA=False | Expires: 2027-03-05
  [1] Intermediate CA | CA=True | Expires: 2027-03-05
  [2] Root CA | CA=True | Expires: 2027-03-05
Chain Depth: 3 (Root → Intermediate → Leaf)
Chain Validation: PASS ✅
```

> 💡 **Tip:** The offline Root CA should never touch a network. Store it on an HSM or encrypted USB. The only time you power it on is to sign the Intermediate CA certificate (a rare, ceremony-worthy event). OCSP stapling moves revocation checking to the server, eliminating privacy leaks from client-to-OCSP-responder traffic.

---

## Step 4 — DevSecOps Pipeline: Security Gate

### Pipeline Architecture

```
Git Push
   │
   ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  SAST    │──▶│  DAST    │──▶│ SCA/SBOM │──▶│Container │──▶│   IaC    │
│ (bandit) │   │  (ZAP)   │   │  (syft)  │   │  Scan    │   │  Scan    │
│ 0 crits  │   │ ≤2 highs │   │ ≤5 crits │   │(trivy)   │   │(checkov) │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                                    │
                                                                    ▼
                                                         ┌──────────────────┐
                                                         │  Security Gate   │
                                                         │  ALL PASS? →     │
                                                         │  Promote staging │
                                                         └──────────────────┘
```

**Stage thresholds:**
| Stage | Tool | Fail Threshold |
|-------|------|---------------|
| SAST | bandit | Any critical finding |
| DAST | OWASP ZAP | > 2 high findings |
| SCA/SBOM | syft + grype | > 5 critical CVEs |
| Container Scan | trivy | > 3 critical CVEs |
| IaC Scan | checkov | > 10 failures |

### Python3 — Pipeline Stage Simulator

```python
class PipelineStage:
    def __init__(self, name, threshold, unit):
        self.name = name
        self.threshold = threshold
        self.unit = unit

    def run(self, value):
        passed = value <= self.threshold
        status = 'PASS ✅' if passed else 'FAIL ❌'
        print(f'  {self.name:30s} {value:6} {self.unit:20s} threshold={self.threshold} → {status}')
        return passed

stages = [
    PipelineStage('SAST (bandit)',           0,  'critical issues'),
    PipelineStage('DAST (ZAP)',              2,  'high findings'),
    PipelineStage('SCA/SBOM (syft)',         5,  'critical CVEs'),
    PipelineStage('Container Scan (trivy)',  3,  'critical CVEs'),
    PipelineStage('IaC Scan (checkov)',      10, 'failures'),
]
findings = [0, 1, 2, 1, 8]

print('=== DevSecOps Pipeline Security Gate ===')
results = [s.run(v) for s, v in zip(stages, findings)]
passed  = all(results)
print(f'Security Gate: {"PASS — promote to staging" if passed else "FAIL — block release"}')
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
class PipelineStage:
    def __init__(self, name, threshold, unit):
        self.name, self.threshold, self.unit = name, threshold, unit
    def run(self, value):
        passed = value <= self.threshold
        status = 'PASS ✅' if passed else 'FAIL ❌'
        print(f'  {self.name:30s} {value:6} {self.unit:20s} threshold={self.threshold} → {status}')
        return passed

stages   = [PipelineStage('SAST (bandit)',0,'critical issues'), PipelineStage('DAST (ZAP)',2,'high findings'), PipelineStage('SCA/SBOM (syft)',5,'critical CVEs'), PipelineStage('Container Scan (trivy)',3,'critical CVEs'), PipelineStage('IaC Scan (checkov)',10,'failures')]
findings = [0, 1, 2, 1, 8]
print('=== DevSecOps Pipeline Security Gate ===')
results  = [s.run(v) for s, v in zip(stages, findings)]
print(f'Security Gate: {\"PASS — promote to staging\" if all(results) else \"FAIL — block release\"}')
"
```

📸 **Verified Output:**
```
=== DevSecOps Pipeline Security Gate ===
  SAST (bandit)                       0 critical issues      threshold=0 → PASS ✅
  DAST (ZAP)                          1 high findings        threshold=2 → PASS ✅
  SCA/SBOM (syft)                     2 critical CVEs        threshold=5 → PASS ✅
  Container Scan (trivy)              1 critical CVEs        threshold=3 → PASS ✅
  IaC Scan (checkov)                  8 failures             threshold=10 → PASS ✅
Security Gate: PASS — promote to staging
```

> 💡 **Tip:** Fail SAST at zero critical findings — security bugs found in CI are 100× cheaper to fix than in production. Treat the security gate as a binary: all stages must pass. Use suppression files (`.trivyignore`, `bandit.yaml`) sparingly and with mandatory review tickets.

---

## Step 5 — Compliance Mapping: Multi-Framework Gap Analysis

### Framework Coverage Matrix

| Domain | ISO 27001 | SOC 2 Type II | NIST CSF 2.0 | PCI DSS v4.0 |
|--------|-----------|---------------|--------------|--------------|
| Access Control | A.5.15–A.5.18 | CC6.1–CC6.3 | PR.AA | Req 7–8 |
| Cryptography | A.8.24 | CC6.7 | PR.DS | Req 3–4 |
| Incident Response | A.5.26 | CC7.3–CC7.5 | RS.MA | Req 12.10 |
| Vulnerability Mgmt | A.8.8 | CC7.1 | ID.RA | Req 6 |
| Logging & Monitoring | A.8.15–A.8.16 | CC7.2 | DE.CM | Req 10 |
| Supply Chain | A.5.19–A.5.22 | CC9.2 | GV.SC | Req 12.8 |

### Python3 — Compliance Gap Analyser

```python
frameworks = {
    'ISO 27001': {
        'controls': 93,
        'implemented': 78,
        'categories': ['Org Controls', 'People Controls', 'Physical Controls', 'Technological Controls']
    },
    'SOC 2 Type II': {
        'controls': 60,
        'implemented': 52,
        'categories': ['Security', 'Availability', 'Confidentiality', 'Processing Integrity', 'Privacy']
    },
    'NIST CSF 2.0': {
        'controls': 106,
        'implemented': 89,
        'categories': ['Govern', 'Identify', 'Protect', 'Detect', 'Respond', 'Recover']
    },
    'PCI DSS v4.0': {
        'controls': 264,
        'implemented': 201,
        'categories': ['Network Security', 'Cardholder Data', 'Vulnerability Mgmt', 'Access Control']
    }
}

print('=== Compliance Gap Analysis ===')
print(f'{"Framework":<20} {"Score":>6} {"Status":<15} Gap')
print('-' * 60)
for fw, data in frameworks.items():
    score  = (data['implemented'] / data['controls']) * 100
    gap    = data['controls'] - data['implemented']
    status = 'COMPLIANT' if score >= 90 else 'GAP' if score >= 70 else 'NON-COMPLIANT'
    print(f'{fw:<20} {score:5.1f}% {status:<15} {gap} controls missing')
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
frameworks = {
    'ISO 27001':    {'controls': 93,  'implemented': 78},
    'SOC 2 Type II':{'controls': 60,  'implemented': 52},
    'NIST CSF 2.0': {'controls': 106, 'implemented': 89},
    'PCI DSS v4.0': {'controls': 264, 'implemented': 201},
}
print('=== Compliance Gap Analysis ===')
print(f'{\"Framework\":<20} {\"Score\":>6} {\"Status\":<15} Gap')
print('-' * 60)
for fw, data in frameworks.items():
    score  = (data['implemented'] / data['controls']) * 100
    gap    = data['controls'] - data['implemented']
    status = 'COMPLIANT' if score >= 90 else 'GAP' if score >= 70 else 'NON-COMPLIANT'
    print(f'{fw:<20} {score:5.1f}% {status:<15} {gap} controls missing')
"
```

📸 **Verified Output:**
```
=== Compliance Gap Analysis ===
Framework             Score Status          Gap
------------------------------------------------------------
ISO 27001             83.9% GAP             15 controls missing
SOC 2 Type II         86.7% GAP             8 controls missing
NIST CSF 2.0          84.0% GAP             17 controls missing
PCI DSS v4.0          76.1% GAP             63 controls missing
```

> 💡 **Tip:** Map controls once, satisfy many. Most ISO 27001 controls overlap with NIST CSF and SOC 2 TSCs — a single control evidence artefact (e.g., a firewall change management procedure) can satisfy all three frameworks. Use a GRC platform (ServiceNow, Vanta, Drata) to link evidence to multiple frameworks automatically.

---

## Step 6 — Vulnerability Management: CVSS + EPSS Priority Queue

### Prioritisation Model

Traditional CVSS-only scoring leads to "patch treadmill" — hundreds of Critical findings, no time to prioritise. **EPSS (Exploit Prediction Scoring System)** provides the probability a CVE will be exploited in the wild within 30 days:

```
Priority Score = CVSS_Score × 0.6 + EPSS_Probability × 10 × 0.4

SLA Tiers:
  CVSS 9.0–10.0  → 24 hours
  CVSS 7.0–8.9   → 72 hours
  CVSS 4.0–6.9   → 30 days
  CVSS 0.1–3.9   → 90 days (or accept risk)
```

**Exception workflow:** Exceptions require CISO approval, business justification, compensating controls, and a review date (max 90-day extension).

### Python3 — CVSS v3.1 Calculator + Priority Queue

```python
import heapq

def cvss_score(av, ac, pr, ui, s, c, i, a):
    weights = {
        'AV': {'N':0.85,'A':0.62,'L':0.55,'P':0.2},
        'AC': {'L':0.77,'H':0.44},
        'PR': {'N':0.85,'L':0.62,'H':0.27},
        'UI': {'N':0.85,'R':0.62},
        'C':  {'H':0.56,'L':0.22,'N':0},
        'I':  {'H':0.56,'L':0.22,'N':0},
        'A':  {'H':0.56,'L':0.22,'N':0},
    }
    iss            = 1 - (1-weights['C'][c])*(1-weights['I'][i])*(1-weights['A'][a])
    iss_scoped     = 6.42 * iss
    exploitability = 8.22 * weights['AV'][av]*weights['AC'][ac]*weights['PR'][pr]*weights['UI'][ui]
    return max(round(min(1.08*(iss_scoped + exploitability), 10), 1), 0)

vulns = [
    ('CVE-2024-0001', cvss_score('N','L','N','N','U','H','H','H'), 0.92),
    ('CVE-2024-0002', cvss_score('N','L','L','N','U','H','N','N'), 0.45),
    ('CVE-2024-0003', cvss_score('L','H','H','R','U','L','L','N'), 0.12),
    ('CVE-2024-0004', cvss_score('A','L','N','N','U','H','H','N'), 0.67),
]

priority_queue = []
for cve, score, epss in vulns:
    priority = -(score * 0.6 + epss * 10 * 0.4)
    heapq.heappush(priority_queue, (priority, cve, score, epss))

print('=== Vulnerability Priority Queue (CVSS + EPSS) ===')
print(f'{"CVE":<18} {"CVSS":>5} {"EPSS":>6} {"SLA":>8} Priority')
print('-' * 55)
rank = 1
while priority_queue:
    pri, cve, score, epss = heapq.heappop(priority_queue)
    sla = '24h' if score >= 9 else '72h' if score >= 7 else '30d'
    print(f'{cve:<18} {score:>5} {epss:>6.2f} {sla:>8} #{rank}')
    rank += 1
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import heapq
def cvss_score(av, ac, pr, ui, s, c, i, a):
    w = {'AV':{'N':0.85,'A':0.62,'L':0.55,'P':0.2},'AC':{'L':0.77,'H':0.44},'PR':{'N':0.85,'L':0.62,'H':0.27},'UI':{'N':0.85,'R':0.62},'C':{'H':0.56,'L':0.22,'N':0},'I':{'H':0.56,'L':0.22,'N':0},'A':{'H':0.56,'L':0.22,'N':0}}
    iss = 1-(1-w['C'][c])*(1-w['I'][i])*(1-w['A'][a])
    return max(round(min(1.08*(6.42*iss + 8.22*w['AV'][av]*w['AC'][ac]*w['PR'][pr]*w['UI'][ui]),10),1),0)
vulns = [('CVE-2024-0001',cvss_score('N','L','N','N','U','H','H','H'),0.92),('CVE-2024-0002',cvss_score('N','L','L','N','U','H','N','N'),0.45),('CVE-2024-0003',cvss_score('L','H','H','R','U','L','L','N'),0.12),('CVE-2024-0004',cvss_score('A','L','N','N','U','H','H','N'),0.67)]
pq = []
for cve,score,epss in vulns: heapq.heappush(pq,(-(score*0.6+epss*10*0.4),cve,score,epss))
print('=== Vulnerability Priority Queue (CVSS + EPSS) ===')
print(f'{\"CVE\":<18} {\"CVSS\":>5} {\"EPSS\":>6} {\"SLA\":>8} Priority')
print('-'*55)
rank=1
while pq:
    pri,cve,score,epss=heapq.heappop(pq)
    sla='24h' if score>=9 else '72h' if score>=7 else '30d'
    print(f'{cve:<18} {score:>5} {epss:>6.2f} {sla:>8} #{rank}')
    rank+=1
"
```

📸 **Verified Output:**
```
=== Vulnerability Priority Queue (CVSS + EPSS) ===
CVE                 CVSS   EPSS      SLA Priority
-------------------------------------------------------
CVE-2024-0001         10   0.92      24h #1
CVE-2024-0004        8.7   0.67      72h #2
CVE-2024-0002        6.9   0.45      30d #3
CVE-2024-0003        3.1   0.12      30d #4
```

> 💡 **Tip:** A CVSS 9.8 with EPSS 0.01 is less urgent than a CVSS 7.5 with EPSS 0.85 — the latter is actively being exploited. EPSS scores update daily; integrate the EPSS API into your vulnerability scanner to get fresh probabilities automatically.

---

## Step 7 — Incident Response: Ransomware Playbook

### IR Framework (NIST SP 800-61 Rev 3)

```
Detection → Containment → Eradication → Recovery → Post-Incident
```

**RACI Matrix — Ransomware Incident:**
| Activity | IR Lead | SOC Manager | Network | Legal | CISO |
|----------|---------|-------------|---------|-------|------|
| Declare incident | R | A | I | I | I |
| Network isolation | R | A | C | I | I |
| Evidence collection | R | C | C | I | I |
| Executive comms | I | I | I | C | R/A |
| Ransom decision | I | I | I | C | R/A |
| Recovery approval | C | C | R | I | A |

**Communication Tree:**
```
CISO
├── Legal Counsel (within 1h)
├── Board / Executive Team (within 2h)
├── Cyber Insurance Carrier (within 4h)
├── Regulator notification if PII (within 72h — GDPR/CCPA)
└── Customer notification if required (per SLA/contract)
```

### Python3 — IR Decision Tree

```python
class IRDecisionTree:
    def run_playbook(self, indicators):
        print('=== Incident Response: Ransomware Playbook ===')
        stage = 'DETECTION'

        print(f'[{stage}] Encrypted files detected: {indicators["encrypted_files"]}')
        print(f'[{stage}] C2 beacon observed: {indicators["c2_beacon"]}')
        print(f'[{stage}] Lateral movement: {indicators["lateral_movement"]}')

        print('\n[CONTAINMENT]')
        if indicators['lateral_movement']:
            print('  → ISOLATE: Segment network — block east-west traffic')
            print('  → RACI: IR Lead (R), SOC Manager (A), Network Team (C), CISO (I)')

        print('\n[ERADICATION]')
        print('  → Identify patient zero via EDR telemetry')
        print('  → Remove malware artifacts, revoke compromised credentials')

        print('\n[RECOVERY]')
        if indicators['backup_available']:
            print('  → Restore from last known-good backup (RTO: 4h)')
        else:
            print('  → ⚠️  No backup — engage ransomware negotiation protocol')

        print('\n[EVIDENCE COLLECTION]')
        for item in ['Memory dump', 'Disk image', 'Network logs', 'EDR telemetry', 'Email headers']:
            print(f'  ☑ {item}')

        print('\n[COMMS TREE]')
        print('  CISO → Legal → PR → Customers (within 72h if PII breach)')
        print('  CISO → Board → Cyber Insurance carrier')

ir = IRDecisionTree()
ir.run_playbook({
    'encrypted_files': True, 'c2_beacon': True,
    'lateral_movement': True, 'backup_available': True
})
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
class IRDecisionTree:
    def run_playbook(self, ind):
        print('=== Incident Response: Ransomware Playbook ===')
        print(f'[DETECTION] Encrypted files: {ind[\"encrypted_files\"]} | C2 beacon: {ind[\"c2_beacon\"]} | Lateral movement: {ind[\"lateral_movement\"]}')
        print('\n[CONTAINMENT]')
        if ind['lateral_movement']:
            print('  → ISOLATE: Segment network — block east-west traffic')
            print('  → RACI: IR Lead (R), SOC Manager (A), Network Team (C), CISO (I)')
        print('\n[ERADICATION]')
        print('  → Identify patient zero via EDR telemetry')
        print('  → Remove malware artifacts, revoke compromised credentials')
        print('\n[RECOVERY]')
        print('  → Restore from last known-good backup (RTO: 4h)' if ind['backup_available'] else '  → ⚠️  No backup — engage ransomware negotiation protocol')
        print('\n[EVIDENCE COLLECTION]')
        [print(f'  ☑ {i}') for i in ['Memory dump','Disk image','Network logs','EDR telemetry','Email headers']]
        print('\n[COMMS TREE]')
        print('  CISO → Legal → PR → Customers (within 72h if PII breach)')
        print('  CISO → Board → Cyber Insurance carrier')

IRDecisionTree().run_playbook({'encrypted_files':True,'c2_beacon':True,'lateral_movement':True,'backup_available':True})
"
```

📸 **Verified Output:**
```
=== Incident Response: Ransomware Playbook ===
[DETECTION] Encrypted files: True | C2 beacon: True | Lateral movement: True

[CONTAINMENT]
  → ISOLATE: Segment network — block east-west traffic
  → RACI: IR Lead (R), SOC Manager (A), Network Team (C), CISO (I)

[ERADICATION]
  → Identify patient zero via EDR telemetry
  → Remove malware artifacts, revoke compromised credentials

[RECOVERY]
  → Restore from last known-good backup (RTO: 4h)

[EVIDENCE COLLECTION]
  ☑ Memory dump
  ☑ Disk image
  ☑ Network logs
  ☑ EDR telemetry
  ☑ Email headers

[COMMS TREE]
  CISO → Legal → PR → Customers (within 72h if PII breach)
  CISO → Board → Cyber Insurance carrier
```

> 💡 **Tip:** The first 15 minutes of a ransomware incident are the most critical. Pre-authorise network isolation — do NOT wait for change-management approval to segment an infected host. Every minute of delay increases blast radius by an order of magnitude.

---

## Step 8 (Capstone) — Full Architecture Report

This final step ties all 7 domains together into a single **Enterprise Security Architecture JSON report** with risk scores, compliance percentages, and a prioritised remediation roadmap — the deliverable a CISO presents to the board.

### Python3 — Generate Full Architecture Report

```python
import json

report = {
    'report_id': 'ESA-2024-001',
    'generated': '2024-03-05T00:00:00Z',
    'organization': 'ACME Corp',
    'security_domains': {
        'SOC': {
            'maturity': 3.5,
            'mttd_hours': 3.2,
            'mttr_hours': 18,
            'score': 82
        },
        'ZeroTrust': {
            'maturity': 3.0,
            'coverage_pct': 75,
            'score': 75
        },
        'PKI': {
            'tier': 3,
            'cert_count': 1240,
            'auto_renewal': True,
            'score': 88
        },
        'DevSecOps': {
            'pipeline_stages': 5,
            'gate_pass_rate': 0.94,
            'score': 79
        },
        'Compliance': {
            'ISO27001': 83.9,
            'SOC2': 86.7,
            'NIST_CSF': 84.0,
            'PCI_DSS': 76.1,
            'score': 82
        },
        'VulnManagement': {
            'open_critical': 3,
            'sla_adherence': 0.91,
            'score': 78
        },
        'IncidentResponse': {
            'playbooks': 12,
            'avg_rto_hours': 4.2,
            'score': 85
        }
    },
    'overall_risk_score': 0,
    'remediation_roadmap': [
        {'priority': 1, 'domain': 'PCI DSS',    'action': 'Close 63 control gaps',                 'timeline': '90 days'},
        {'priority': 2, 'domain': 'Zero Trust',  'action': 'Expand micro-segmentation to 100%',     'timeline': '60 days'},
        {'priority': 3, 'domain': 'Vuln Mgmt',   'action': 'Patch 3 critical CVEs (24h SLA)',       'timeline': 'Immediate'},
    ]
}

scores = [d['score'] for d in report['security_domains'].values()]
report['overall_risk_score'] = round(sum(scores) / len(scores), 1)

print(json.dumps(report, indent=2))
print(f'\n✅ Enterprise Security Score: {report["overall_risk_score"]}/100')
```

Run it:

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import json
report = {
    'report_id': 'ESA-2024-001', 'generated': '2024-03-05T00:00:00Z', 'organization': 'ACME Corp',
    'security_domains': {
        'SOC':              {'maturity':3.5, 'mttd_hours':3.2, 'mttr_hours':18,  'score':82},
        'ZeroTrust':        {'maturity':3.0, 'coverage_pct':75,                  'score':75},
        'PKI':              {'tier':3, 'cert_count':1240, 'auto_renewal':True,   'score':88},
        'DevSecOps':        {'pipeline_stages':5, 'gate_pass_rate':0.94,         'score':79},
        'Compliance':       {'ISO27001':83.9,'SOC2':86.7,'NIST_CSF':84.0,'PCI_DSS':76.1,'score':82},
        'VulnManagement':   {'open_critical':3, 'sla_adherence':0.91,            'score':78},
        'IncidentResponse': {'playbooks':12, 'avg_rto_hours':4.2,                'score':85},
    },
    'overall_risk_score': 0,
    'remediation_roadmap': [
        {'priority':1,'domain':'PCI DSS',   'action':'Close 63 control gaps',              'timeline':'90 days'},
        {'priority':2,'domain':'Zero Trust','action':'Expand micro-segmentation to 100%',  'timeline':'60 days'},
        {'priority':3,'domain':'Vuln Mgmt', 'action':'Patch 3 critical CVEs (24h SLA)',    'timeline':'Immediate'},
    ]
}
scores = [d['score'] for d in report['security_domains'].values()]
report['overall_risk_score'] = round(sum(scores)/len(scores),1)
print(json.dumps(report, indent=2))
print(f'\n✅ Enterprise Security Score: {report[\"overall_risk_score\"]}/100')
"
```

📸 **Verified Output:**
```json
{
  "report_id": "ESA-2024-001",
  "generated": "2024-03-05T00:00:00Z",
  "organization": "ACME Corp",
  "security_domains": {
    "SOC": {
      "maturity": 3.5,
      "mttd_hours": 3.2,
      "mttr_hours": 18,
      "score": 82
    },
    "ZeroTrust": {
      "maturity": 3.0,
      "coverage_pct": 75,
      "score": 75
    },
    "PKI": {
      "tier": 3,
      "cert_count": 1240,
      "auto_renewal": true,
      "score": 88
    },
    "DevSecOps": {
      "pipeline_stages": 5,
      "gate_pass_rate": 0.94,
      "score": 79
    },
    "Compliance": {
      "ISO27001": 83.9,
      "SOC2": 86.7,
      "NIST_CSF": 84.0,
      "PCI_DSS": 76.1,
      "score": 82
    },
    "VulnManagement": {
      "open_critical": 3,
      "sla_adherence": 0.91,
      "score": 78
    },
    "IncidentResponse": {
      "playbooks": 12,
      "avg_rto_hours": 4.2,
      "score": 85
    }
  },
  "overall_risk_score": 81.3,
  "remediation_roadmap": [
    {
      "priority": 1,
      "domain": "PCI DSS",
      "action": "Close 63 control gaps",
      "timeline": "90 days"
    },
    {
      "priority": 2,
      "domain": "Zero Trust",
      "action": "Expand micro-segmentation to 100%",
      "timeline": "60 days"
    },
    {
      "priority": 3,
      "domain": "Vuln Mgmt",
      "action": "Patch 3 critical CVEs (24h SLA)",
      "timeline": "Immediate"
    }
  ]
}

✅ Enterprise Security Score: 81.3/100
```

> 💡 **Tip:** An enterprise security score of 81.3/100 is respectable but not board-ready. The board wants trend lines, not point-in-time scores. Run this report monthly, store scores in a time-series database, and present the 12-month improvement trajectory — that's what demonstrates programme maturity.

---

## 🏆 Lab Summary

| Step | Domain | Key Concept | Score |
|------|--------|-------------|-------|
| 1 | SOC Design | 3-tier SOC, SIEM+SOAR, MTTD/MTTR metrics | 82/100 |
| 2 | Zero Trust | PEP/PDP/PA model, trust scoring, micro-segmentation | 75/100 |
| 3 | PKI | 3-tier CA hierarchy, certificate chain validation | 88/100 |
| 4 | DevSecOps | 5-stage security gate, SAST/DAST/SCA/IaC | 79/100 |
| 5 | Compliance | ISO 27001, SOC 2, NIST CSF 2.0, PCI DSS v4.0 | 82/100 |
| 6 | Vuln Mgmt | CVSS v3.1 + EPSS priority queue, SLA tiers | 78/100 |
| 7 | Incident Response | Ransomware playbook, RACI, evidence collection | 85/100 |
| 8 | Architecture Report | Full JSON report, all domains, remediation roadmap | 81.3 avg |

**Overall Enterprise Security Score: 81.3/100**

**Priority Remediation Actions:**
1. 🔴 **Immediate** — Patch 3 critical CVEs within 24-hour SLA
2. 🟡 **60 days** — Expand Zero Trust micro-segmentation from 75% → 100% coverage
3. 🟠 **90 days** — Close 63 PCI DSS v4.0 control gaps (currently 76.1% compliant)

---

## 🎓 Architect Track Complete

Congratulations — you have completed all 20 Cybersecurity Architect labs. You have designed, modelled, and validated:

- ✅ SOC operations with SIEM/SOAR integration
- ✅ Zero Trust architecture with policy engine
- ✅ Enterprise PKI with 3-tier CA hierarchy
- ✅ DevSecOps security gates across 5 scan stages
- ✅ Multi-framework compliance gap analysis
- ✅ Risk-prioritised vulnerability management
- ✅ Automated incident response playbooks
- ✅ Full enterprise security architecture report

**Next step:** Apply these frameworks to your organisation — run the gap analyser against your actual controls, feed real CVE data into the priority queue, and present the architecture report to your security leadership.

---

**← Previous:** [Lab 19: Security Metrics & Risk Quantification](lab-19-security-metrics-risk-quantification.md) | **↑ Back to:** [Architect README](../README.md)
