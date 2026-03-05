# Lab 04: Zero Trust Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Apply NIST SP 800-207 Zero Trust Architecture principles
- Design PEP/PDP/PA components
- Implement micro-segmentation strategy
- Build a Zero Trust policy engine simulator

---

## Step 1: NIST SP 800-207 Zero Trust Principles

**Core tenets:**
1. Verify explicitly — always authenticate and authorise based on all available data points
2. Use least-privilege access — limit user access with JIT and JEA
3. Assume breach — minimise blast radius, segment access, verify end-to-end encryption

**NIST SP 800-207 Pillars:**

| Pillar | Description | Technologies |
|--------|-----------|--------------|
| **Identity** | Strong identity as the control plane | MFA, OIDC, SAML, PAM |
| **Device** | Device health as access prerequisite | MDM, EDR, device certificates |
| **Network** | Micro-segmentation; no implicit trust | SDN, firewall, encrypted tunnels |
| **Workload** | Secure applications and APIs | WAF, API gateway, service mesh |
| **Data** | Classify and protect data | DLP, encryption, CASB |
| **Visibility** | Continuous monitoring and analytics | SIEM, UEBA, telemetry |

---

## Step 2: PEP/PDP/PA Architecture

```
  Subject (User/Device)
         │
         ▼
┌────────────────────┐
│  Policy Enforcement │  ← PEP: controls access to resource
│  Point (PEP)       │     (proxy, API gateway, network switch)
└────────┬───────────┘
         │ access request
         ▼
┌────────────────────┐
│  Policy Decision   │  ← PDP: evaluates policy + signals
│  Point (PDP)       │     (identity, device, threat intel)
└────────┬───────────┘
         │ policy query
         ▼
┌────────────────────┐
│  Policy            │  ← PA: manages and distributes policies
│  Administrator (PA)│     (IdP, device management, SIEM feed)
└────────────────────┘
         │
    ┌────┴─────┐
    │ Enterprise│  ← Protected Resources
    │ Resource  │
    └───────────┘
```

**Signal inputs to PDP:**
- Identity provider (IdP) — verified user identity, MFA status
- Device compliance — MDM status, EDR health score, patch level
- Threat intelligence — user risk score (UEBA), IP reputation
- Request context — time of day, geolocation, resource sensitivity

---

## Step 3: BeyondCorp Model (Google's ZTA)

**BeyondCorp principles (translated to enterprise):**
1. Networks are not trusted; all access via encrypted channels
2. Device inventory and device trust assessed continuously
3. Access based on user + device; not network location
4. All access to services is authenticated and authorised

**Implementation layers:**
```
User authenticates to IdP (MFA required)
  → Device certificate validated against MDM
  → Risk score calculated (UEBA anomaly + threat intel)
  → Access proxy (PEP) receives go/no-go from PDP
  → Session recorded and monitored continuously
```

---

## Step 4: Zero Trust Policy Engine Simulator

```python
class ZeroTrustPolicyEngine:
    def __init__(self):
        self.policies = []

    def add_policy(self, name, conditions, action):
        self.policies.append({'name': name, 'conditions': conditions, 'action': action})

    def evaluate(self, request):
        print(f'=== Zero Trust Policy Evaluation ===')
        print(f'Subject  : {request["user"]} (role={request["role"]})')
        print(f'Device   : trust_score={request["device_trust"]}, compliant={request["compliant"]}')
        print(f'Resource : {request["resource"]} via {request["network"]}')
        print()
        for policy in self.policies:
            conds = policy['conditions']
            match = all([
                request.get('role') in conds.get('roles', [request.get('role')]),
                request.get('device_trust', 0) >= conds.get('min_trust', 0),
                request.get('compliant') == conds.get('compliant', request.get('compliant')),
                request.get('network') in conds.get('networks', [request.get('network')])
            ])
            status = 'MATCH' if match else '     '
            print(f'  [{status}] {policy["name"]} -> {policy["action"] if match else "skip"}')
            if match:
                print(f'  Decision: {policy["action"].upper()}')
                return policy['action']
        print('  Decision: DENY (no policy matched)')
        return 'deny'

engine = ZeroTrustPolicyEngine()
engine.add_policy('CorpAdmin Full Access',
    {'roles': ['admin'], 'min_trust': 80, 'compliant': True, 'networks': ['corporate', 'vpn']},
    'allow')
engine.add_policy('Employee Read-Only',
    {'roles': ['employee'], 'min_trust': 60, 'compliant': True, 'networks': ['corporate', 'vpn']},
    'allow-readonly')
engine.add_policy('Deny Untrusted Device',
    {'roles': ['admin', 'employee'], 'min_trust': 0, 'compliant': False, 'networks': ['internet', 'corporate', 'vpn']},
    'deny')

req = {'user': 'alice', 'role': 'admin', 'device_trust': 92, 'compliant': True,
       'resource': '/hr/payroll', 'network': 'vpn'}
engine.evaluate(req)
print()
print('NIST SP 800-207 Pillars: Identity | Device | Network | Workload | Data | Visibility')
```

📸 **Verified Output:**
```
=== Zero Trust Policy Evaluation ===
Subject  : alice (role=admin)
Device   : trust_score=92, compliant=True
Resource : /hr/payroll via vpn

  [MATCH] CorpAdmin Full Access -> allow
  Decision: ALLOW

NIST SP 800-207 Pillars: Identity | Device | Network | Workload | Data | Visibility
```

---

## Step 5: Micro-Segmentation Design

**Traditional perimeter vs. ZTA segmentation:**
```
Traditional:          Zero Trust:
┌──────────────┐      ┌─────────────────────────┐
│   Trusted    │      │  Segment A  │  Segment B │
│   Internal   │  →   │ (Finance)   │  (HR)      │
│   Network    │      ├─────────────┼────────────┤
└──────────────┘      │  Segment C  │  Segment D │
                      │ (Dev/Test)  │  (PCI DSS) │
                      └─────────────────────────┘
                         ↑ All inter-segment traffic
                           requires explicit policy
```

**Segmentation strategies:**
- **VLAN-based**: Traditional, coarse-grained
- **SDN/Overlay**: VXLAN, VMware NSX, Cisco ACI — fine-grained
- **Identity-based**: Illumio, Guardicore — workload identity microsegmentation
- **Service mesh**: Istio/Linkerd — east-west traffic in Kubernetes

> 💡 **Start with crown-jewel segmentation**: Isolate your most sensitive assets (PCI zone, HR data, IP repositories) first. Complete micro-segmentation is a multi-year journey.

---

## Step 6: Identity-Centric Access (OIDC/SAML)

**OIDC flow for ZTA:**
```
User → IdP (authenticate + MFA)
  → IdP issues ID Token (JWT) + Access Token
  → Access Token sent to PEP (access proxy)
  → PEP validates token with PDP
  → PDP checks device trust, risk score
  → PEP grants/denies + logs session
```

**Device trust scoring:**
```
device_trust_score = (
    patch_compliance * 30 +    # 0-30 points
    edr_health * 25 +           # 0-25 points
    mdm_enrolled * 20 +         # 0-20 points
    certificate_valid * 15 +    # 0-15 points
    disk_encryption * 10        # 0-10 points
)
# Score > 80: Full access
# Score 50-79: Restricted access
# Score < 50: Block + remediation
```

---

## Step 7: ZTA Implementation Roadmap

**Phase 1 (0-6 months) — Foundation:**
- Deploy MFA for all users (FIDO2/WebAuthn preferred)
- Inventory all devices; enrol in MDM
- Implement IdP (Okta, Azure AD, Ping Identity)
- Enable conditional access policies

**Phase 2 (6-18 months) — Segmentation:**
- Deploy identity-aware proxy (PEP) for critical apps
- Implement SDN micro-segmentation for crown jewels
- Enable EDR on all endpoints
- Deploy PAM for privileged accounts

**Phase 3 (18-36 months) — Maturity:**
- UEBA for continuous risk scoring
- CASB for cloud app visibility
- Service mesh for Kubernetes east-west
- Automate PDP with ML-based risk decisions

---

## Step 8: Capstone — ZTA for Remote Workforce

**Scenario:** 3,000 remote employees; replace legacy VPN with ZTA

```
ZTA Design:
  Identity:
    - Azure AD with MFA (FIDO2 keys for privileged users)
    - Conditional Access policies: block legacy auth
    - PIM (Privileged Identity Management) for admin roles

  Device:
    - Intune MDM + Microsoft Defender for Endpoint
    - Device compliance score > 75 required for access
    - BYOD: separate compliance profile, read-only access

  Network:
    - Replace VPN with Zscaler Private Access (ZPA)
    - All traffic via encrypted tunnel to ZPA cloud
    - No split-tunnel — all traffic inspected

  Applications:
    - App-by-app access (no network-level trust)
    - OAuth 2.0 + OIDC for all web apps
    - SAM/SAML for legacy apps

  Monitoring:
    - All access logs to Microsoft Sentinel
    - UEBA enabled for insider threat detection
    - Monthly access review via Azure AD Access Reviews

  Timeline: 12 months | Cost: USD 450K implementation + USD 180K/year licenses
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| NIST SP 800-207 | Never trust, always verify; explicit trust per request |
| PEP | Enforces access decisions (proxy, gateway, switch) |
| PDP | Makes access decisions based on policy + signals |
| PA | Manages and distributes policies to PEPs |
| Micro-segmentation | Isolate workloads; deny all unless explicitly permitted |
| Device Trust | Score-based: patch + EDR + MDM + certificate |
| BeyondCorp | Access from network perimeter → user + device identity |
