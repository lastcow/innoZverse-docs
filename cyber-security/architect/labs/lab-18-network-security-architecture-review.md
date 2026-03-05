# Lab 18: Network Security Architecture Review

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Review network security architecture for segmentation gaps
- Analyse east-west vs north-south traffic flows
- Audit firewall rulesets for shadow and redundant rules
- Build a Python firewall rule conflict detector

---

## Step 1: Network Security Architecture Layers

```
Internet
    │
    ▼ north-south traffic (external → internal)
┌─────────────────────────────────────────────┐
│  Perimeter Layer                             │
│  DDoS Protection → WAF → Firewall → DMZ     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Core Network                                │
│  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │  Internet │  │  Corp     │  │   DMZ   │ │
│  │  Edge     │  │  Network  │  │         │ │
│  └───────────┘  └─────┬─────┘  └─────────┘ │
│                       │                     │
│             east-west (internal)            │
│   ┌──────────────────────────────────────┐  │
│   │  Microsegmentation                   │  │
│   │ Finance│HR│Dev│PCI Zone│Server Zone  │  │
│   └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**North-South vs East-West:**
| Direction | Description | Security Challenge |
|-----------|-----------|-------------------|
| North-South | Internet ↔ Internal | Traditional perimeter defence |
| East-West | Internal ↔ Internal | Lateral movement; often uninspected |

> 💡 **Modern attacks primarily use east-west movement** after initial compromise. Most breaches involve minimal north-south traffic after initial access. East-west traffic must be inspected and segmented.

---

## Step 2: Firewall Rule Conflict Detector

```python
from ipaddress import ip_network

rules = [
    {'id':1, 'action':'allow', 'src':'10.0.0.0/8',   'dst':'192.168.1.0/24', 'port':443, 'proto':'tcp'},
    {'id':2, 'action':'deny',  'src':'10.1.0.0/16',  'dst':'192.168.1.0/24', 'port':443, 'proto':'tcp'},  # shadowed by rule 1
    {'id':3, 'action':'allow', 'src':'10.0.0.0/8',   'dst':'192.168.1.0/24', 'port':80,  'proto':'tcp'},
    {'id':4, 'action':'allow', 'src':'10.0.0.0/8',   'dst':'192.168.1.0/24', 'port':80,  'proto':'tcp'},  # redundant with rule 3
    {'id':5, 'action':'deny',  'src':'0.0.0.0/0',    'dst':'0.0.0.0/0',      'port':None,'proto':'any'},
    {'id':6, 'action':'allow', 'src':'172.16.0.0/12','dst':'10.0.0.0/8',     'port':22,  'proto':'tcp'},
]

def subnet_contains(a, b):
    try: return ip_network(b, strict=False).subnet_of(ip_network(a, strict=False))
    except: return False

def rules_conflict(r1, r2):
    src_sub  = subnet_contains(r1['src'], r2['src'])
    dst_sub  = subnet_contains(r1['dst'], r2['dst'])
    port_match = r1['port'] == r2['port'] or r1['port'] is None
    proto_match = r1['proto'] == r2['proto'] or r1['proto'] == 'any'
    return src_sub and dst_sub and port_match and proto_match

print('=== Firewall Ruleset Conflict Detector ===')
shadows = []
redundant = []
for i, r1 in enumerate(rules):
    for r2 in rules[i+1:]:
        if r1['action'] != r2['action'] and rules_conflict(r1, r2):
            shadows.append((r1['id'], r2['id']))
        elif r1['action'] == r2['action'] and r1['src']==r2['src'] and r1['dst']==r2['dst'] and r1['port']==r2['port']:
            redundant.append((r1['id'], r2['id']))

print(f'  Total rules: {len(rules)}')
print()
print('Shadow Rules (earlier ALLOW shadows later DENY):')
for a, b in shadows: print(f'  Rule {a} SHADOWS Rule {b}')
print()
print('Redundant Rules (duplicate traffic match):')
for a, b in redundant: print(f'  Rule {a} REDUNDANT with Rule {b}')
print()
print('Recommendations:')
print('  - Reorder or remove shadow rules')
print('  - Delete redundant rules to reduce attack surface')
print('  - Implement least-privilege default-deny policy')
```

📸 **Verified Output:**
```
=== Firewall Ruleset Conflict Detector ===
  Total rules: 6

Shadow Rules (earlier ALLOW shadows later DENY):
  Rule 1 SHADOWS Rule 2
  Rule 5 SHADOWS Rule 6

Redundant Rules (duplicate traffic match):
  Rule 3 REDUNDANT with Rule 4

Recommendations:
  - Reorder or remove shadow rules
  - Delete redundant rules to reduce attack surface
  - Implement least-privilege default-deny policy
```

---

## Step 3: Traffic Flow Analysis Methodology

**Traffic flow review process:**
1. **Discover** — collect network diagrams, firewall configs, flow logs
2. **Map** — identify all traffic flows (source, destination, port, protocol)
3. **Categorise** — north-south (external), east-west (internal), management
4. **Analyse** — identify unexpected flows, overly permissive rules
5. **Remediate** — tighten rules, implement segmentation, remove unused rules

**Flow analysis data sources:**
| Source | Data Provided |
|--------|-------------|
| Firewall logs | Allow/deny decisions, rule hit counts |
| NetFlow/IPFIX | Traffic volumes, connection counts |
| VPC Flow Logs | Cloud network traffic |
| Zeek/Suricata | Deep packet inspection, protocol analysis |
| SIEM | Correlation of flow data with alerts |

---

## Step 4: Network Segmentation Design

**Segmentation models:**

**VLAN-based segmentation:**
```
VLAN 10: Production servers (10.1.0.0/24)
VLAN 20: Database servers (10.2.0.0/24)    ← no direct client access
VLAN 30: Corporate workstations (10.3.0.0/24)
VLAN 40: Management (10.4.0.0/24)          ← only ops team
VLAN 50: PCI CDE (10.5.0.0/24)            ← isolated, all traffic inspected
VLAN 99: Guest WiFi (192.168.99.0/24)     ← internet only, no internal access
```

**Firewall zone design:**
```
UNTRUST (Internet)
  → DMZ (public-facing: web, email, VPN)
  → TRUST (internal corporate)
    → RESTRICTED (PCI, finance, HR)
    → SERVERS (backend, databases)
    → MANAGEMENT (OOB, PAM)
```

> 💡 **The management zone is critical** — all out-of-band management (iDRAC, ILO, IPMI, bastion) should be isolated in a dedicated network segment. Compromising the management plane gives attackers access to all systems.

---

## Step 5: Firewall Ruleset Audit

**Audit checklist:**

**1. Default deny:**
```
✅ Last rule: deny all; log
✗  Any implicit permit at zone level
```

**2. Overly permissive rules:**
```
✗ Source: ANY (0.0.0.0/0) to internal resources
✗ Port: ANY (all ports allowed)
✗ Service: ANY on internet-facing rules
✅ Specific source IPs + specific ports
```

**3. Rule hygiene:**
```
✗ Shadow rules (never matched due to earlier rule)
✗ Redundant rules (duplicate match criteria)
✗ Disabled rules (orphaned, should be deleted)
✗ Rules without logging (can't audit or investigate)
✗ Rules older than 2 years without review
```

**4. High-risk rules to review:**
```
ANY-ANY allow rules
ANY source to management interfaces
Allow from UNTRUST to TRUST (should only be DMZ)
Allow from corporate to PCI CDE (should be restricted)
Wide port ranges (e.g., 1024-65535)
```

---

## Step 6: DMZ Architecture

**Screened subnet (three-legged DMZ):**
```
Internet → [External FW] → DMZ → [Internal FW] → Internal
                           ↕
                    Public-facing servers:
                    - Web/application servers
                    - Email gateway
                    - VPN concentrator
                    - DNS (public resolver)
                    - API gateway
```

**DMZ security principles:**
- DMZ servers should NOT be able to initiate connections to internal
- DMZ → Internal: only specific, required ports (DB port, LDAP for auth)
- Internal → DMZ: limited (admin access only via jump host)
- Internet → DMZ: WAF inspects all HTTP/HTTPS
- No direct Internet → Internal (not in DMZ)

---

## Step 7: Zero Trust Network Segmentation

**Moving from perimeter to ZTA network:**
```
Legacy: Big flat internal network (trusted zone)
  ✗ Lateral movement unrestricted once inside
  ✗ Service accounts can reach any system
  ✗ No visibility into east-west traffic

ZTA network:
  - SDN/microsegmentation: Illumio, VMware NSX
  - Identity-based workload policies
  - All east-west traffic inspected at host level
  - Default-deny: explicit allow per workload pair
  - Continuous monitoring of all traffic (NetFlow + Zeek)

Migration path:
  Phase 1: Deploy microsegmentation in monitor mode
  Phase 2: Enforce on crown-jewel segments (PCI, HR)
  Phase 3: Extend to all production workloads
  Phase 4: Enforce in test/dev environments
```

---

## Step 8: Capstone — Network Architecture Review

**Scenario:** Review network security for a 10,000-user enterprise, post-breach assessment

```
Assessment Methodology:

1. Architecture review (week 1):
   - Collect: firewall configs, network diagrams, VLAN table
   - Identify: flat network segments, excessive trust relationships
   - Interview: network team, SOC, application owners
   - Findings: 3 segments with ANY-ANY rules, no east-west inspection

2. Traffic analysis (week 2):
   - Collect NetFlow from core switches (30-day sample)
   - Identify: unexpected traffic patterns
   - Map: actual vs documented traffic flows
   - Findings: 47 undocumented inter-VLAN flows, 3 admin shares accessible from workstations

3. Firewall audit (week 3):
   - Run conflict detector against all 6 firewall configs (1,200 rules)
   - Findings: 142 shadow rules, 89 redundant rules, 23 rules with no logging
   - Risk: 12 rules allowing broad access from untrusted sources

4. Recommendations priority:
   Immediate (< 30 days):
     - Remove 12 high-risk overly permissive rules
     - Enable logging on all rules
     - Block workstation-to-workstation SMB (T1021.002 prevention)

   Short-term (30-90 days):
     - Clean up 89 redundant rules
     - Segment PCI CDE from corporate network
     - Deploy Zeek for east-west traffic inspection

   Strategic (90 days - 1 year):
     - Implement Illumio microsegmentation
     - ZTA network design for cloud workloads
     - Automate firewall rule review quarterly

5. Metrics:
   - Firewall rules audited: 1,200
   - Shadow rules found: 142 (12%)
   - Redundant rules found: 89 (7%)
   - Rules removed: 231
   - Attack surface reduction: estimated 35%
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| North-South | Internet ↔ internal; traditional perimeter |
| East-West | Internal ↔ internal; lateral movement risk |
| Shadow rules | Earlier broader rule prevents later rule from matching |
| Redundant rules | Duplicate rules; clean up to reduce complexity |
| DMZ | Screened subnet; public servers isolated from internal |
| Segmentation | VLAN → SDN → microsegmentation (ZTA) |
| Audit cycle | Quarterly firewall rule review; disable unused rules |
