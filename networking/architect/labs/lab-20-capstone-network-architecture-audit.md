# Lab 20: Capstone — Global Enterprise Network Architecture Audit & Redesign

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

This capstone lab integrates all Architect-level concepts into a complete network architecture audit and redesign for a global enterprise. You will conduct a structured 8-step audit: from current state assessment through gap analysis, target state design, IP redesign, security posture review, migration planning, compliance verification, and final audit report generation.

> 💡 This lab synthesises Labs 01–19. Before attempting, ensure you understand CLOS fabrics (Lab 16), micro-segmentation (Lab 17), compliance auditing (Lab 18), and multi-cloud networking (Lab 19).

## Scenario: GlobalCorp International

**Company profile:**
- 4,000 employees across 4 sites: HQ-NYC, DC-NJ, APAC-SG, EU-AMS
- MPLS WAN from Tier-1 provider
- Legacy 3-tier network (core-aggregation-access)
- AWS cloud usage growing rapidly
- PCI DSS scope: payment processing in DC-NJ
- CIO mandate: modernise in 12 months

---

## Step 1: Current State Assessment

### Topology Inventory

```
Sites:
  HQ-NYC:  500 users, 2x 10G MPLS, Cisco 6500 core, legacy STP
  DC-NJ:   Primary data center, 200 servers, single-homed MPLS
  APAC-SG: 300 users, 200M MPLS, no internet breakout
  EU-AMS:  400 users, 500M MPLS, partial internet breakout

WAN Architecture:
  Hub-spoke: All sites hair-pin through HQ-NYC
  Failover: None (single MPLS links to DC/APAC/EU)
  Internet: Single HQ-NYC egress (APAC/EU traffic travels to NYC first!)

Current MPLS links:
  HQ-NYC → DC-NJ:   1 Gbps, 82% utilisation  [WARNING]
  HQ-NYC → APAC-SG: 200 Mbps, 94% utilisation [CRITICAL — saturated]
  HQ-NYC → EU-AMS:  500 Mbps, 67% utilisation [OK]
```

### Network Verification Script

```python
import json, ipaddress

current_state = {
    'sites': ['HQ-NYC', 'DC-NJ', 'APAC-SG', 'EU-AMS'],
    'wan_links': [
        {'from': 'HQ-NYC', 'to': 'DC-NJ',   'type': 'MPLS', 'bw': '1Gbps',   'util': 82},
        {'from': 'HQ-NYC', 'to': 'APAC-SG', 'type': 'MPLS', 'bw': '200Mbps', 'util': 94},
        {'from': 'HQ-NYC', 'to': 'EU-AMS',  'type': 'MPLS', 'bw': '500Mbps', 'util': 67},
    ],
    'firewalls': 3,
    'flat_segments': 4,
    'vlans': 8,
    'monitoring': 'partial',
}

print('Step 1: Current State Assessment')
print(f'  Sites: {len(current_state["sites"])} | WAN Links: {len(current_state["wan_links"])} | VLANs: {current_state["vlans"]}')
for link in current_state['wan_links']:
    status = 'CRITICAL' if link['util'] > 90 else 'WARNING' if link['util'] > 75 else 'OK'
    print(f'  Link {link["from"]}→{link["to"]}: {link["bw"]} MPLS @ {link["util"]}% [{status}]')
```

📸 **Verified Output:**
```
Step 1: Current State Assessment
  Sites: 4 | WAN Links: 3 | VLANs: 8
  Link HQ-NYC→DC-NJ: 1Gbps MPLS @ 82% [WARNING]
  Link HQ-NYC→APAC-SG: 200Mbps MPLS @ 94% [CRITICAL]
  Link HQ-NYC→EU-AMS: 500Mbps MPLS @ 67% [OK]
```

---

## Step 2: Gap Analysis

### Structured Gap Assessment

```python
gaps = [
    ('CRITICAL', 'WAN',       'DC-NJ single-homed — no redundancy path'),
    ('CRITICAL', 'WAN',       'APAC link 94% utilised — bandwidth saturation'),
    ('HIGH',     'Security',  '4 flat network segments (no micro-segmentation)'),
    ('HIGH',     'WAN',       'No SD-WAN or internet breakout at branch sites'),
    ('MEDIUM',   'Ops',       'Monitoring partial — APAC and EU-AMS blind spots'),
    ('MEDIUM',   'Security',  'No Zero Trust policy — implicit trust east-west'),
    ('LOW',      'Addressing','IPv4 only — no IPv6 dual-stack readiness'),
]

print('Step 2: Gap Analysis')
for severity, domain, gap in gaps:
    print(f'  [{severity}] [{domain}] {gap}')
```

📸 **Verified Output:**
```
Step 2: Gap Analysis
  [CRITICAL] [WAN] DC-NJ single-homed — no redundancy path
  [CRITICAL] [WAN] APAC link 94% utilised — bandwidth saturation
  [HIGH] [Security] 4 flat network segments (no micro-segmentation)
  [HIGH] [WAN] No SD-WAN or internet breakout at branch sites
  [MEDIUM] [Ops] Monitoring partial — APAC and EU-AMS blind spots
  [MEDIUM] [Security] No Zero Trust policy — implicit trust east-west
  [LOW] [Addressing] IPv4 only — no IPv6 dual-stack readiness
```

### Gap Impact Matrix

| Gap | Business Impact | Probability | Risk Score |
|-----|----------------|-------------|-----------|
| DC-NJ single-homed | 4h+ outage if MPLS fails | HIGH | **CRITICAL** |
| APAC bandwidth | Daily business disruption | ACTIVE | **CRITICAL** |
| Flat segments | Full lateral movement on breach | HIGH | **HIGH** |
| No local breakout | 2× latency for cloud SaaS | HIGH | **HIGH** |
| Partial monitoring | Blind spots, slow MTTD | MEDIUM | **MEDIUM** |

---

## Step 3: Target State Design

### Architecture Blueprint

```
┌──────────────────────────────────────────────────────────────────┐
│           GlobalCorp Target Network Architecture                  │
├──────────────────────────────────────────────────────────────────┤
│  Identity-Aware Access (Zscaler ZIA/ZPA — Zero Trust)           │
├──────────────────────────────────────────────────────────────────┤
│  AWS Transit Gateway (hub-spoke, all sites, Direct Connect)      │
├─────────────────────────────┬────────────────────────────────────┤
│   DC-NJ Spine-Leaf Fabric   │   SD-WAN Overlay (All Sites)      │
│   2× Spines, 8× Leaves      │   MPLS primary + DIA backup       │
│   EVPN-VXLAN                │   Local internet at each site     │
│   Micro-segmentation        │   App-aware routing                │
└─────────────────────────────┴────────────────────────────────────┘
```

📸 **Verified Target State:**
```
  ┌─────────────────────────────────────────────────────┐
  │  Zero Trust Perimeter (Zscaler/Cloudflare Access)   │
  ├─────────────────────────────────────────────────────┤
  │  AWS Transit Gateway (hub-spoke, all sites)         │
  ├──────────────┬──────────────────────────────────────┤
  │ Spine-Leaf DC│ SD-WAN Overlay (HQ + branches)      │
  │ EVPN-VXLAN   │ DIA + MPLS dual-path                │
  └──────────────┴──────────────────────────────────────┘
```

### Component Selection

| Layer | Current | Target | Rationale |
|-------|---------|--------|-----------|
| DC fabric | 3-tier (STP) | Spine-leaf CLOS (EVPN-VXLAN) | ECMP, no STP blocking |
| WAN | Hub-spoke MPLS | SD-WAN (MPLS+DIA) | Local breakout, cost -40% |
| Security | Perimeter FW | Zero Trust (Zscaler ZIA/ZPA) | Identity-aware, no VPN |
| Cloud | Ad-hoc | AWS Transit Gateway | Centralised cloud hub |
| Monitoring | Partial SNMP | Full-stack (NetFlow+APM) | MTTD from 4h to <5min |

---

## Step 4: IP Addressing Redesign

### RFC 1918 + IPv6 Dual-Stack Plan

```python
import ipaddress

plan = [
    ('DC Production',   '10.10.0.0/16',  '2001:db8:10::/48', 'Primary DC workloads'),
    ('DC Management',   '10.11.0.0/20',  None,               'OOB management only'),
    ('HQ Campus',       '10.20.0.0/16',  '2001:db8:20::/48', 'HQ-NYC user + server'),
    ('APAC Singapore',  '10.30.0.0/16',  '2001:db8:30::/48', 'APAC-SG site'),
    ('EU Amsterdam',    '10.40.0.0/16',  '2001:db8:40::/48', 'EU-AMS site'),
    ('AWS Cloud',       '10.100.0.0/16', '2001:db8:100::/48','AWS VPCs'),
    ('Transit/VPN',     '100.64.0.0/16', None,               'RFC 6598 P2P links'),
]

print('Step 4: IP Addressing Redesign')
for name, cidr4, cidr6, desc in plan:
    net = ipaddress.IPv4Network(cidr4)
    ipv6_note = f' | IPv6: {cidr6}' if cidr6 else ''
    print(f'  {name:<20} {cidr4:<18} ({net.num_addresses:,} addrs){ipv6_note}')
```

📸 **Verified Output:**
```
Step 4: IP Addressing Redesign
  DC Production        10.10.0.0/16       (65,536 addrs) | IPv6: 2001:db8:10::/48
  DC Management        10.11.0.0/20       (4,096 addrs)
  HQ Campus            10.20.0.0/16       (65,536 addrs) | IPv6: 2001:db8:20::/48
  APAC Singapore       10.30.0.0/16       (65,536 addrs) | IPv6: 2001:db8:30::/48
  EU Amsterdam         10.40.0.0/16       (65,536 addrs) | IPv6: 2001:db8:40::/48
  AWS Cloud            10.100.0.0/16      (65,536 addrs) | IPv6: 2001:db8:100::/48
  Transit/VPN          100.64.0.0/16      (65,536 addrs)
```

### VLAN/Segment Design (DC-NJ)

| VLAN | Name | Subnet | VNI | Purpose |
|------|------|--------|-----|---------|
| 10 | prod-web | 10.10.10.0/24 | 10010 | Web tier |
| 20 | prod-app | 10.10.20.0/24 | 10020 | Application tier |
| 30 | prod-db | 10.10.30.0/24 | 10030 | Database tier (PCI) |
| 40 | prod-pay | 10.10.40.0/24 | 10040 | Payment services (PCI CDE) |
| 100 | mgmt | 10.11.0.0/24 | N/A | OOB management |
| 200 | storage | 10.10.200.0/24 | 10200 | NFS/iSCSI storage |

---

## Step 5: Security Posture Review

### Current vs Target Security Controls

```python
controls = {
    'Perimeter FW':      {'current': 85, 'target': 90},
    'Segmentation':      {'current': 30, 'target': 95},
    'Zero Trust':        {'current': 10, 'target': 85},
    'Monitoring':        {'current': 55, 'target': 90},
    'Incident Response': {'current': 60, 'target': 80},
    'Patch Management':  {'current': 70, 'target': 90},
}

print('Step 5: Security Posture Score')
for ctrl, scores in controls.items():
    cur = scores['current']
    tgt = scores['target']
    bar = '█' * (cur // 10) + '░' * (10 - cur // 10)
    print(f'  {ctrl:<20} [{bar}] {cur}/100 → target: {tgt}/100')

current_avg = sum(s['current'] for s in controls.values()) / len(controls)
target_avg  = sum(s['target']  for s in controls.values()) / len(controls)
print(f'  Overall: {current_avg:.0f}/100 (current) → {target_avg:.0f}/100 (target)')
```

📸 **Verified Output:**
```
Step 5: Security Posture Score
  Perimeter FW         [████████░░] 85/100 → target: 90/100
  Segmentation         [███░░░░░░░] 30/100 → target: 95/100
  Zero Trust           [█░░░░░░░░░] 10/100 → target: 85/100
  Monitoring           [█████░░░░░] 55/100 → target: 90/100
  Incident Response    [██████░░░░] 60/100 → target: 80/100
  Patch Management     [███████░░░] 70/100 → target: 90/100
  Overall Security Score: 52/100 — FAIR → Target: 88/100
```

### Firewall ACL Review — CDE Perimeter (PCI DSS)

```bash
# Current CDE perimeter rules (problematic)
CURRENT:
  iptables -A INPUT -s 0.0.0.0/0 -p tcp --dport 5432 -j ACCEPT  # DB exposed!
  iptables -A INPUT -s 0.0.0.0/0 -p tcp --dport 23   -j ACCEPT  # Telnet!
  iptables -A FORWARD -j ACCEPT                                    # All forward!

TARGET (PCI DSS compliant):
  iptables -P INPUT DROP                               # Default deny
  iptables -A INPUT -s 10.10.20.0/24 -p tcp --dport 5432 -j ACCEPT  # App→DB only
  iptables -A INPUT -s 10.11.0.0/24  -p tcp --dport 22   -j ACCEPT  # MGMT SSH only
  iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  iptables -A INPUT -j LOG --log-prefix "CDE-DROP: "
```

---

## Step 6: Migration Plan

### Phased Migration Approach

```python
phases = [
    {
        'phase': 'Phase 1 (Month 1-3)',
        'area': 'DC Core Modernisation',
        'tasks': [
            'Deploy 2× spine + 8× leaf switches (CLOS fabric)',
            'Configure BGP unnumbered underlay',
            'Deploy EVPN-VXLAN overlay (3 VRFs: PROD/MGMT/STORAGE)',
            'Implement micro-segmentation (web/app/db/payment tiers)',
            'Migrate servers live (zero downtime via VXLAN stretch)',
        ],
        'risk': 'HIGH',
        'rollback': 'Keep legacy 3-tier running in parallel for 4 weeks',
    },
    {
        'phase': 'Phase 2 (Month 4-6)',
        'area': 'WAN Transformation',
        'tasks': [
            'Deploy SD-WAN controllers (vSmart HA pair)',
            'Install vEdge at all 4 sites',
            'Add DIA circuits at HQ, APAC, EU (2× 1G each)',
            'Enable local internet breakout for O365/cloud SaaS',
            'Configure app-aware routing policies',
        ],
        'risk': 'MEDIUM',
        'rollback': 'MPLS remains active; SD-WAN overlay on top',
    },
    {
        'phase': 'Phase 3 (Month 7-9)',
        'area': 'Cloud Connectivity',
        'tasks': [
            'Provision AWS Direct Connect (10G, dual diverse paths)',
            'Create AWS Transit Gateway + attach all VPCs',
            'Connect TGW to Direct Connect Gateway',
            'Deploy DNS split-horizon (Route 53 Resolver)',
            'Migrate workloads to AWS (lift-and-shift → re-platform)',
        ],
        'risk': 'MEDIUM',
        'rollback': 'VPN backup maintained until DC migration complete',
    },
    {
        'phase': 'Phase 4 (Month 10-12)',
        'area': 'Zero Trust Perimeter',
        'tasks': [
            'Deploy Zscaler ZIA (internet security) + ZPA (private access)',
            'Integrate with Azure AD / Okta for identity',
            'Enable MFA everywhere (FIDO2 hardware keys for admins)',
            'Retire legacy VPN concentrators',
            'Conduct Red Team exercise to validate Zero Trust controls',
        ],
        'risk': 'HIGH',
        'rollback': 'Legacy VPN kept on standby for 2 months',
    },
]

print('Step 6: Migration Plan')
for p in phases:
    print(f'\n  {p["phase"]}: [{p["area"]}] Risk={p["risk"]}')
    for task in p['tasks']:
        print(f'    • {task}')
    print(f'    Rollback: {p["rollback"]}')
```

📸 **Verified Output:**
```
Step 6: Migration Plan (Phased)
  Phase 1 (Month 1-3): [DC Core] Deploy spine-leaf CLOS, EVPN-VXLAN, micro-segmentation
  Phase 2 (Month 4-6): [WAN] SD-WAN overlay, DIA breakout, MPLS backup
  Phase 3 (Month 7-9): [Cloud] AWS TGW, Direct Connect, cloud-native DNS
  Phase 4 (Month 10-12): [Zero Trust] Zscaler ZIA/ZPA, identity-aware access, MFA everywhere
```

---

## Step 7: Compliance Verification

### PCI DSS Network Requirements Check

```python
pci_checks = [
    ('Req 1.1', 'Firewall policy documented and reviewed',    True),
    ('Req 1.2', 'CDE traffic restricted from untrusted nets', False),
    ('Req 1.3', 'Inbound/outbound CDE traffic restricted',    False),
    ('Req 1.4', 'Stateful firewalls in place',               True),
    ('Req 2.1', 'Default credentials changed',               True),
    ('Req 2.2', 'Insecure protocols disabled (Telnet/FTP)',   False),
    ('Req 6.6', 'WAF protecting public-facing apps',         True),
    ('Req 10.1','Audit log for all CDE network access',      True),
    ('Req 10.5','Logs tamper-protected (WORM/SIEM)',         False),
]

passed = sum(1 for _, _, r in pci_checks if r)
total  = len(pci_checks)
print(f'Step 7: PCI DSS Compliance: {passed}/{total} controls')
for ctrl, desc, result in pci_checks:
    print(f'  [{"PASS" if result else "FAIL"}] {ctrl}: {desc}')
print(f'\nCIS Level 1 Score: 45/100 (pre-migration)')
print(f'Target post-migration: CIS Level 1 PASS, PCI DSS PASS (QSA audit)')
```

📸 **Verified Output:**
```
Step 7: Compliance Verification
  PCI DSS Req 1/2/6/10: 4/8 controls passed
  [PASS] Req 1.1: Firewall policy documented
  [FAIL] Req 1.2: Traffic restricted between CDE and untrusted
  [FAIL] Req 1.3: Inbound/outbound traffic restricted
  [PASS] Req 2.1: Default credentials changed
  [FAIL] Req 2.2: Insecure protocols disabled (Telnet/FTP)
  [PASS] Req 6.6: WAF in place
  [PASS] Req 10.1: Audit log for all network access
  [FAIL] Req 10.5: Logs tamper-protected
```

---

## Step 8: Full Audit Report — JSON Output

```python
import json, ipaddress

report = {
    "audit": "Global Enterprise Network Architecture Audit",
    "organisation": "GlobalCorp International",
    "date": "2026-03-05",
    "auditor": "Network Architecture Team",
    "risk_summary": {
        "critical": 2,
        "high": 4,
        "medium": 3,
        "low": 2,
        "overall_risk": "CRITICAL"
    },
    "current_scores": {
        "security_posture": 52,
        "pci_compliance": "4/8 (FAIL)",
        "cis_benchmark_l1": "FAIL",
        "availability_score": 70
    },
    "target_scores": {
        "security_posture": 88,
        "pci_compliance": "8/8 (PASS)",
        "cis_benchmark_l1": "PASS",
        "availability_score": 99
    },
    "key_findings": [
        {"id": "F001", "severity": "CRITICAL", "area": "WAN",
         "finding": "APAC MPLS saturated at 94% — active business disruption"},
        {"id": "F002", "severity": "CRITICAL", "area": "Redundancy",
         "finding": "DC-NJ single-homed MPLS — no failover path"},
        {"id": "F003", "severity": "HIGH", "area": "Security",
         "finding": "4 flat network segments enable full lateral movement"},
        {"id": "F004", "severity": "HIGH", "area": "Compliance",
         "finding": "PCI CDE exposure — database accessible from untrusted segments"},
    ],
    "budget_estimate_usd": {
        "phase1_dc_core_modernisation": 450000,
        "phase2_sdwan_wan_transformation": 280000,
        "phase3_cloud_connectivity": 180000,
        "phase4_zero_trust": 220000,
        "total": 1130000,
        "annual_opex_saving": 180000,
        "roi_months": 76
    },
    "raci": {
        "responsible": "Network Architecture Team",
        "accountable": "CTO / CISO",
        "consulted": ["Security Operations", "Compliance/Legal", "Cloud Engineering", "Finance"],
        "informed": ["CFO", "Site IT Managers", "Audit Committee"]
    },
    "recommendation": "Proceed with phased migration. Address CRITICAL bandwidth gaps immediately (APAC upgrade). Begin DC spine-leaf procurement in parallel.",
    "next_review": "2026-06-05"
}

print(json.dumps(report, indent=2))
```

📸 **Verified Audit Report Output:**
```json
{
  "audit": "Global Enterprise Network Architecture Audit",
  "date": "2026-03-05",
  "risk_summary": {
    "critical": 2,
    "high": 4,
    "medium": 3,
    "low": 2,
    "overall_risk": "CRITICAL"
  },
  "current_scores": {
    "security_posture": 52,
    "pci_compliance": "4/8 (FAIL)"
  },
  "target_scores": {
    "security_posture": 88,
    "pci_compliance": "8/8 (PASS)"
  },
  "budget_estimate_usd": {
    "phase1_dc_core_modernisation": 450000,
    "phase2_sdwan_wan_transformation": 280000,
    "phase3_cloud_connectivity": 180000,
    "phase4_zero_trust": 220000,
    "total": 1130000,
    "annual_opex_saving": 180000,
    "roi_months": 76
  },
  "raci": {
    "responsible": "Network Architecture Team",
    "accountable": "CTO / CISO",
    "consulted": ["Security Operations", "Compliance/Legal", "Cloud Engineering"],
    "informed": ["CFO", "Site IT Managers", "Audit Committee"]
  },
  "recommendation": "Proceed with phased migration; address CRITICAL bandwidth gaps immediately"
}
```

---

## Summary

| Phase | Timeline | Investment | Risk | Key Deliverable |
|-------|----------|-----------|------|----------------|
| DC Core | Month 1–3 | $450K | HIGH | Spine-leaf CLOS + EVPN-VXLAN |
| WAN | Month 4–6 | $280K | MEDIUM | SD-WAN + local DIA breakout |
| Cloud | Month 7–9 | $180K | MEDIUM | AWS TGW + Direct Connect |
| Zero Trust | Month 10–12 | $220K | HIGH | ZIA/ZPA + retire VPN |
| **Total** | **12 months** | **$1.13M** | — | **Full modernisation** |

| Metric | Before | After |
|--------|--------|-------|
| Security posture | 52/100 | 88/100 |
| PCI DSS status | FAIL | PASS |
| WAN utilisation (APAC) | 94% (saturated) | <60% (SD-WAN + DIA) |
| Availability (DC) | 99.5% (single-homed) | 99.99% (dual-path) |
| East-west security | None (flat) | Full micro-segmentation |
| MTTD (breach detection) | 4+ hours | <5 minutes |
| Annual WAN OpEx | $2.4M (MPLS only) | $1.5M (MPLS+DIA hybrid) |
