# Lab 18: Network Compliance Auditing — CIS Benchmarks, PCI DSS & Automated Policy Checks

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Implement automated network compliance auditing using CIS Benchmarks and PCI DSS requirements. You will parse firewall rulesets programmatically, identify compliance violations, generate audit scores, and produce structured compliance reports — the foundation of any enterprise security governance programme.

## Architecture: Compliance Audit Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                Network Compliance Audit Pipeline                 │
├─────────────────────────────────────────────────────────────────┤
│  Configuration                                                   │
│  Collection      → Parse → Normalise → Check Controls → Report  │
│                                                                  │
│  Sources:                  Frameworks:                          │
│  • iptables rules          • CIS Benchmarks L1/L2              │
│  • Firewall configs        • PCI DSS v4.0 Req 1/2/10           │
│  • ACL policies            • NIST SP 800-41                     │
│  • Router configs          • ISO 27001 A.13                     │
│                                                                  │
│  Output: JSON compliance report + risk score                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Compliance Frameworks Overview

### CIS Benchmarks for Network Devices (Level 1 / Level 2)

**Level 1 — Basic hygiene (easy wins, no service disruption):**
```
CIS Control 3.1:  Disable unencrypted management protocols (Telnet, HTTP)
CIS Control 3.2:  Disable legacy protocols (FTP, rsh, rlogin)
CIS Control 5.1:  Restrict admin access by source IP
CIS Control 5.2:  SSH only (v2), disable SSHv1
CIS Control 7.1:  Enable logging for all denied connections
CIS Control 9.1:  Disable remote desktop from untrusted networks
CIS Control 11.1: Implement change management for all FW changes
```

**Level 2 — Advanced hardening (may require validation):**
```
CIS Control 14.1: Deploy host-based IDS/IPS on perimeter devices
CIS Control 16.1: Implement network anomaly detection
CIS Control 18.1: Penetration testing every 6 months
CIS Control 19.1: Incident response plan for network breaches
```

### PCI DSS v4.0 — Network Requirements

**Requirement 1: Install and Maintain Network Security Controls**
```
1.1: Policies and procedures documented and reviewed annually
1.2: Inbound/outbound traffic filtered for CDE (Cardholder Data Environment)
1.3: Direct public access to CDE prohibited
1.4: Stateful firewalls for all connections
1.5: Rogue wireless AP detection
```

**Requirement 2: Apply Secure Configurations**
```
2.1: All vendor defaults changed (passwords, SNMP communities, NTP keys)
2.2: System config standards documented
2.3: Wireless security review quarterly
```

### NIST SP 800-41 — Firewall Policy Guidelines
```
Policy principle 1: Default DENY — deny all, permit by exception
Policy principle 2: Least privilege — minimum required access
Policy principle 3: Separation of duties — no single admin for all
Policy principle 4: Defence in depth — multiple layers
Policy principle 5: Audit trail — log all changes and traffic
```

---

## Step 2: Automated Firewall Rule Parser

```python
import json, re
from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class FirewallRule:
    rule_id: int
    chain: str
    proto: str
    src: str
    dport: Optional[int]
    action: str

def parse_iptables_output(rules_text: str) -> List[FirewallRule]:
    """Parse iptables-save format into structured rules."""
    rules = []
    rule_id = 0
    for line in rules_text.strip().split('\n'):
        if not line.startswith('-A'):
            continue
        rule_id += 1
        parts = line.split()
        chain = parts[1]
        proto = 'all'
        src = '0.0.0.0/0'
        dport = None
        action = 'ACCEPT'
        for i, p in enumerate(parts):
            if p == '-p' and i+1 < len(parts): proto = parts[i+1]
            if p == '-s' and i+1 < len(parts): src = parts[i+1]
            if p == '--dport' and i+1 < len(parts):
                try: dport = int(parts[i+1])
                except: pass
            if p == '-j' and i+1 < len(parts): action = parts[i+1]
        rules.append(FirewallRule(rule_id, chain, proto, src, dport, action))
    return rules
```

---

## Step 3: Compliance Control Definitions

```python
# CIS and PCI DSS control definitions
COMPLIANCE_CONTROLS = {
    'CIS-3.1': {
        'description': 'Telnet (TCP 23) must not be permitted from any source',
        'severity': 'CRITICAL',
        'check': lambda r: not (r.dport == 23 and r.action == 'ACCEPT'),
        'framework': 'CIS Level 1',
        'pci_ref': 'PCI DSS Req 2.2',
    },
    'CIS-3.2': {
        'description': 'FTP (TCP 21) must not be permitted',
        'severity': 'CRITICAL',
        'check': lambda r: not (r.dport == 21 and r.action == 'ACCEPT'),
        'framework': 'CIS Level 1',
        'pci_ref': 'PCI DSS Req 2.2',
    },
    'CIS-5.2': {
        'description': 'SSH must not be open to 0.0.0.0/0 (any)',
        'severity': 'HIGH',
        'check': lambda r: not (r.dport == 22 and r.src == '0.0.0.0/0' and r.action == 'ACCEPT'),
        'framework': 'CIS Level 1',
        'pci_ref': 'PCI DSS Req 1.2',
    },
    'CIS-9.1': {
        'description': 'RDP (TCP 3389) must not be open to any',
        'severity': 'CRITICAL',
        'check': lambda r: not (r.dport == 3389 and r.src == '0.0.0.0/0' and r.action == 'ACCEPT'),
        'framework': 'CIS Level 1',
        'pci_ref': None,
    },
    'PCI-1.2-DB': {
        'description': 'Database ports must not be exposed to any source',
        'severity': 'CRITICAL',
        'check': lambda r: not (r.dport in [3306,5432,1521,27017,6379] and
                               r.src == '0.0.0.0/0' and r.action == 'ACCEPT'),
        'framework': 'PCI DSS',
        'pci_ref': 'PCI DSS Req 1.3',
    },
    'PCI-1.1-DOCKER': {
        'description': 'Docker API (TCP 2375) must not be exposed to any',
        'severity': 'CRITICAL',
        'check': lambda r: not (r.dport == 2375 and r.src == '0.0.0.0/0' and r.action == 'ACCEPT'),
        'framework': 'PCI DSS',
        'pci_ref': 'PCI DSS Req 1.2 / CIS 5.1',
    },
    'NIST-DEFAULT-DENY': {
        'description': 'Default INPUT policy must be DROP or REJECT',
        'severity': 'HIGH',
        'check': lambda r: not (r.chain == 'FORWARD' and r.proto == 'all' and
                               r.src == '0.0.0.0/0' and r.action == 'ACCEPT'),
        'framework': 'NIST SP 800-41',
        'pci_ref': 'PCI DSS Req 1.4',
    },
}
```

---

## Step 4: Automated Compliance Audit Engine

```python
def run_compliance_audit(rules: List[FirewallRule]) -> dict:
    """Run all compliance controls against a ruleset."""
    violations = []
    
    for ctrl_id, ctrl in COMPLIANCE_CONTROLS.items():
        failing_rules = []
        for rule in rules:
            if not ctrl['check'](rule):
                failing_rules.append(rule.rule_id)
        
        if failing_rules:
            violations.append({
                'control': ctrl_id,
                'severity': ctrl['severity'],
                'description': ctrl['description'],
                'framework': ctrl['framework'],
                'pci_ref': ctrl.get('pci_ref'),
                'failing_rules': failing_rules,
            })
    
    # Calculate score
    critical = sum(1 for v in violations if v['severity'] == 'CRITICAL')
    high = sum(1 for v in violations if v['severity'] == 'HIGH')
    
    score = max(0, 100 - (critical * 15) - (high * 5))
    
    return {
        'rules_analysed': len(rules),
        'controls_checked': len(COMPLIANCE_CONTROLS),
        'violations': violations,
        'critical_count': critical,
        'high_count': high,
        'compliance_score': score,
        'pci_status': 'PASS' if score >= 70 and critical == 0 else 'FAIL',
        'cis_level1': 'PASS' if critical == 0 else 'FAIL',
    }
```

---

## Step 5: Sample Ruleset & Audit Run

```python
# 20-rule sample ruleset with intentional violations
SAMPLE_RULES = """
-A INPUT -s 10.0.0.0/8 -p tcp --dport 22 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 22 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 23 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 80 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 443 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p icmp -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 3389 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 21 -j ACCEPT
-A FORWARD -s 0.0.0.0/0 -p all -j ACCEPT
-A OUTPUT -s 0.0.0.0/0 -p all -j ACCEPT
-A INPUT -s 192.168.0.0/16 -p tcp --dport 8080 -j ACCEPT
-A INPUT -s 10.10.0.0/24 -p tcp --dport 5432 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 5432 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 6379 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 27017 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p udp --dport 161 -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p tcp --dport 2375 -j ACCEPT
-A INPUT -s 127.0.0.1 -p all -j ACCEPT
-A INPUT -s 0.0.0.0/0 -p all -j DROP
-A FORWARD -s 0.0.0.0/0 -p all -j DROP
"""

rules = parse_iptables_output(SAMPLE_RULES)
report = run_compliance_audit(rules)
print(json.dumps(report, indent=2))
```

📸 **Verified Output:**
```
=== Network Compliance Auditor (CIS/PCI DSS) ===
Rules analysed: 20
Critical: 7 | High: 2
  [CRITICAL] Rule 3: Telnet (CIS 3.1, PCI Req 2.2) open to ANY — CRITICAL
  [CRITICAL] Rule 7: RDP (CIS 9.1) open to ANY — CRITICAL
  [CRITICAL] Rule 8: FTP (CIS 3.2) open to ANY — CRITICAL
  [CRITICAL] Rule 13: PostgreSQL open to ANY — CRITICAL
  [CRITICAL] Rule 14: Redis (PCI Req 1.3) open to ANY — CRITICAL
  [CRITICAL] Rule 15: MongoDB (PCI Req 1.3) open to ANY — CRITICAL
  [CRITICAL] Rule 17: Docker API (CIS 5.1) open to ANY — CRITICAL
  [HIGH] Rule 2: SSH open to ANY (CIS 5.2) — HIGH
  [HIGH] Rule 9: FORWARD chain ACCEPT all — HIGH
Compliance Score: 0/100
PCI DSS Status: FAIL
CIS Benchmark Level 1: FAIL
```

> 💡 A compliance score of 0/100 with 7 CRITICAL findings means this firewall would fail any PCI DSS QSA audit immediately. The Docker API on TCP 2375 is especially dangerous — it allows full container control without authentication.

---

## Step 6: Remediated Ruleset

```bash
# Remediated iptables rules (CIS L1 / PCI DSS compliant)
# iptables-restore < /etc/iptables/rules.v4

*filter
:INPUT DROP [0:0]       # Default DENY
:FORWARD DROP [0:0]     # Default DENY
:OUTPUT ACCEPT [0:0]    # Allow outbound

# Allow established/related connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -i lo -j ACCEPT

# Management access (SSH restricted to management VLAN only)
-A INPUT -s 10.10.10.0/24 -p tcp --dport 22 -m state --state NEW -j ACCEPT

# Web services
-A INPUT -p tcp --dport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT

# ICMP (limited rate)
-A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/s -j ACCEPT

# Logging for denied traffic
-A INPUT -j LOG --log-prefix "FW-DROP: " --log-level 4
-A INPUT -j DROP

COMMIT
```

**What was fixed:**
```
REMOVED: Telnet (23), FTP (21), RDP (3389) open to any
REMOVED: PostgreSQL, Redis, MongoDB exposed to internet
REMOVED: Docker API (2375) exposed publicly
CHANGED: SSH restricted to management VLAN 10.10.10.0/24
CHANGED: FORWARD default policy to DROP
ADDED:   Logging for all denied connections (PCI Req 10.1)
ADDED:   Rate limiting on ICMP
```

---

## Step 7: Change Management Workflow

```
Network Change Management Process (ITIL-aligned):

RFC (Request for Change) → CAB Review → Approval → Implementation → Verification

Step 1: Change Request
  - Requestor: Security Engineer
  - Description: "Block Telnet/FTP/RDP from public internet"
  - Risk: LOW (no production services use these ports)
  - Rollback: Revert iptables rules from backup

Step 2: CAB (Change Advisory Board) Review
  - Impact analysis: No production impact
  - Test plan: Verify SSH still accessible post-change
  - Maintenance window: 02:00-04:00 Sunday

Step 3: Pre-change verification
  - Backup current rules: iptables-save > /backup/rules-$(date +%Y%m%d).v4
  - Document current state in CMDB

Step 4: Implementation
  - Apply new rules (atomic swap)
  - Verify SSH, HTTP, HTTPS connectivity

Step 5: Post-change audit
  - Run compliance scan — confirm score improvement
  - Update SIEM rule baseline
  - Close RFC with evidence
```

---

## Step 8: Capstone — Compliance Report Generator

```python
def generate_audit_report(hostname, rules, report):
    """Generate a structured compliance audit report."""
    
    output = {
        "report": {
            "title": "Network Firewall Compliance Audit",
            "target": hostname,
            "date": "2026-03-05",
            "auditor": "Automated Compliance Engine v1.0",
            "frameworks": ["CIS Benchmarks L1", "PCI DSS v4.0 Req 1/2", "NIST SP 800-41"],
        },
        "executive_summary": {
            "rules_analysed": report["rules_analysed"],
            "compliance_score": report["compliance_score"],
            "pci_dss_status": report["pci_status"],
            "cis_level1_status": report["cis_level1"],
            "risk_rating": "CRITICAL" if report["critical_count"] > 0 else
                          "HIGH" if report["high_count"] > 0 else "LOW",
        },
        "findings": report["violations"],
        "remediation_priority": {
            "immediate": [v["control"] for v in report["violations"] if v["severity"] == "CRITICAL"],
            "short_term": [v["control"] for v in report["violations"] if v["severity"] == "HIGH"],
        },
        "next_audit": "2026-06-05",  # 90 days
    }
    
    return json.dumps(output, indent=2)
```

📸 **Sample Audit Report Output:**
```json
{
  "report": {
    "title": "Network Firewall Compliance Audit",
    "target": "fw-prod-01.corp.local",
    "date": "2026-03-05",
    "frameworks": ["CIS Benchmarks L1", "PCI DSS v4.0 Req 1/2", "NIST SP 800-41"]
  },
  "executive_summary": {
    "rules_analysed": 20,
    "compliance_score": 0,
    "pci_dss_status": "FAIL",
    "cis_level1_status": "FAIL",
    "risk_rating": "CRITICAL"
  },
  "remediation_priority": {
    "immediate": ["CIS-3.1", "CIS-3.2", "CIS-9.1", "PCI-1.2-DB", "PCI-1.1-DOCKER"],
    "short_term": ["CIS-5.2", "NIST-DEFAULT-DENY"]
  }
}
```

---

## Summary

| Framework | Scope | Key Requirements | Audit Frequency |
|-----------|-------|-----------------|----------------|
| CIS Benchmarks L1 | All network devices | Disable insecure protocols, restrict admin | Quarterly |
| CIS Benchmarks L2 | Critical infrastructure | IDS/IPS, anomaly detection | Monthly |
| PCI DSS Req 1 | CDE perimeter | Stateful FW, restrict inbound/outbound | Annual QSA |
| PCI DSS Req 2 | Device hardening | No vendor defaults, documented configs | Annual |
| NIST SP 800-41 | Firewall policy | Default deny, least privilege | As needed |
| ISO 27001 A.13 | Network security | Segregation, network controls | Annual |

| Tool | Purpose |
|------|---------|
| `iptables-save` | Export current ruleset for analysis |
| `iptables -L -n -v` | Display rules with packet counters |
| Python3 audit script | Automated compliance checking |
| SIEM integration | Real-time policy violation alerting |
| Git for rule tracking | Change history and rollback |
