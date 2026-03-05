# Lab 08: SOAR Automation

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design SOAR platform architecture and playbook structure
- Implement trigger→enrich→contain→remediate→close pipeline
- Integrate API-driven response actions
- Build a Python SOAR playbook engine with decision tree

---

## Step 1: SOAR Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    SOAR PLATFORM                          │
│                                                          │
│  TRIGGERS                    INTEGRATIONS                │
│  ┌─────────────────┐         ┌───────────────────────┐  │
│  │ • SIEM alert    │         │ • EDR (CrowdStrike)    │  │
│  │ • Email report  │    ←→   │ • Firewall (Palo Alto) │  │
│  │ • Threat intel  │         │ • IAM (Active Directory│  │
│  │ • User report   │         │ • TIP (MISP)           │  │
│  │ • Ticket (ITSM) │         │ • Ticketing (ITSM)     │  │
│  └─────────────────┘         └───────────────────────┘  │
│                                                          │
│  PLAYBOOK ENGINE                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Trigger → Triage → Enrich → Contain → Remediate  │   │
│  │         → Notify → Close                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  CASE MANAGEMENT                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Case #IR-2024-042                                 │   │
│  │ Timeline | Evidence | Actions | Collaboration     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## Step 2: Playbook Design Principles

**Key design principles:**
1. **Atomic actions** — each action does one thing (enrich IP, isolate host)
2. **Idempotent** — running a playbook twice has same result
3. **Conditional branching** — severity-driven decisions
4. **Human-in-loop** — escalate when confidence is low
5. **Audit trail** — every action logged with timestamp, actor, result

**Playbook lifecycle:**
```
Design → Test (sandbox) → Stage (low-risk playbooks) → Production
                                    ↓
                         Monthly review + tuning
```

---

## Step 3: SOAR API Integration Patterns

**EDR API (CrowdStrike example):**
```python
import requests

def isolate_host(device_id, reason):
    """Isolate host via CrowdStrike API"""
    resp = requests.post(
        'https://api.crowdstrike.com/devices/actions/v2?action_name=contain',
        headers={'Authorization': f'Bearer {TOKEN}'},
        json={'ids': [device_id], 'comment': reason}
    )
    return resp.status_code == 200

def get_host_info(hostname):
    """Enrich: get device details"""
    resp = requests.get(
        f'https://api.crowdstrike.com/devices/queries/devices/v1?filter=hostname:"{hostname}"',
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    return resp.json()
```

**Threat Intel enrichment:**
```python
def enrich_ip(ip_address):
    """VirusTotal enrichment"""
    resp = requests.get(
        f'https://www.virustotal.com/api/v3/ip_addresses/{ip_address}',
        headers={'x-apikey': VT_KEY}
    )
    data = resp.json()
    return {
        'ip': ip_address,
        'malicious': data['data']['attributes']['last_analysis_stats']['malicious'],
        'country': data['data']['attributes']['country'],
        'asn': data['data']['attributes']['asn']
    }
```

---

## Step 4: SOAR Playbook Engine

```python
import json, time

class SOARPlaybook:
    def __init__(self, name):
        self.name = name
        self.steps = []

    def add_step(self, phase, action, auto=True):
        self.steps.append({'phase': phase, 'action': action, 'auto': auto})

    def run(self, alert):
        print(f'=== SOAR Playbook: {self.name} ===')
        print(f'Alert: {alert["type"]} | Severity: {alert["severity"]} | Source: {alert["source"]}')
        print()
        decisions = {}
        for step in self.steps:
            result = self._execute(step, alert, decisions)
            auto_label = '[AUTO]' if step['auto'] else '[MANUAL]'
            print(f'  {auto_label} [{step["phase"]:<12}] {step["action"]:<40} -> {result}')
            decisions[step['phase']] = result
        return decisions

    def _execute(self, step, alert, prev):
        phase = step['phase']
        if phase == 'TRIGGER':   return 'Alert received'
        if phase == 'TRIAGE':
            return 'CRITICAL' if alert['severity'] >= 8 else 'MEDIUM'
        if phase == 'ENRICH':    return f'IP={alert["source"]} -> country=CN, threat_score=87'
        if phase == 'CONTAIN':
            if prev.get('TRIAGE') == 'CRITICAL': return 'Host isolated + firewall rule added'
            return 'Monitoring enhanced'
        if phase == 'REMEDIATE': return 'Malware removed, credentials reset'
        if phase == 'NOTIFY':    return 'SOC L2 + CISO notified'
        if phase == 'CLOSE':     return 'Case #IR-2024-042 closed, lessons-learned filed'
        return 'Completed'

pb = SOARPlaybook('Ransomware Response')
for p, a, auto in [
    ('TRIGGER',   'Receive EDR alert', True),
    ('TRIAGE',    'Assess severity score', True),
    ('ENRICH',    'Query threat intel (VirusTotal/MISP)', True),
    ('CONTAIN',   'Isolate endpoint via EDR API', True),
    ('REMEDIATE', 'Remove payload + reset credentials', False),
    ('NOTIFY',    'Alert SOC team + management', True),
    ('CLOSE',     'Close case + update SIEM', True),
]:
    pb.add_step(p, a, auto)

alert = {'type': 'Ransomware Detected', 'severity': 9, 'source': '10.1.2.34'}
pb.run(alert)
```

📸 **Verified Output:**
```
=== SOAR Playbook: Ransomware Response ===
Alert: Ransomware Detected | Severity: 9 | Source: 10.1.2.34

  [AUTO]   [TRIGGER     ] Receive EDR alert                        -> Alert received
  [AUTO]   [TRIAGE      ] Assess severity score                    -> CRITICAL
  [AUTO]   [ENRICH      ] Query threat intel (VirusTotal/MISP)     -> IP=10.1.2.34 -> country=CN, threat_score=87
  [AUTO]   [CONTAIN     ] Isolate endpoint via EDR API             -> Host isolated + firewall rule added
  [MANUAL] [REMEDIATE   ] Remove payload + reset credentials       -> Malware removed, credentials reset
  [AUTO]   [NOTIFY      ] Alert SOC team + management              -> SOC L2 + CISO notified
  [AUTO]   [CLOSE       ] Close case + update SIEM                 -> Case #IR-2024-042 closed, lessons-learned filed
```

---

## Step 5: Playbook Library

**Standard playbook catalog:**

| Playbook | Trigger | Auto-Containment | SLA |
|---------|---------|-----------------|-----|
| Phishing Response | Email report / user click | Delete email, block sender | 1 hour |
| Ransomware Response | EDR alert | Isolate host, block C2 | 15 minutes |
| Brute Force | SIEM: >5 failed logins | Account lock, block IP | 30 minutes |
| Data Exfiltration | DLP alert | Revoke session, network block | 30 minutes |
| Insider Threat | UEBA anomaly | Soft block, HR notify | 4 hours |
| Malware Detected | AV/EDR | Quarantine file, isolate | 15 minutes |
| Cloud Misconfig | CSPM alert | Remediate config, notify | 2 hours |

---

## Step 6: Case Management Integration

**Case lifecycle:**
```
Alert → Auto-triage → Case created (if threshold met)
  → Case enriched (host, user, threat intel)
  → Assigned to analyst (round-robin or specialty routing)
  → Analyst investigation → actions logged
  → Resolution: confirmed / false positive
  → Post-incident: lessons learned → playbook update
```

**Case fields:**
```json
{
  "case_id": "IR-2024-042",
  "created": "2024-01-15T08:35:00Z",
  "severity": "critical",
  "type": "ransomware",
  "status": "open",
  "assigned_to": "analyst1",
  "assets": ["WIN-DC01", "10.1.2.34"],
  "indicators": ["hash:abc123", "ip:192.168.99.1"],
  "playbook": "ransomware-response",
  "actions": [...],
  "sla_deadline": "2024-01-15T09:35:00Z",
  "sla_status": "on-track"
}
```

---

## Step 7: SOAR Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Auto-resolution rate | Auto-closed cases / total cases | > 40% |
| MTTR (automated) | Time to containment for auto-playbooks | < 5 min |
| MTTR (manual) | Time to containment for human-in-loop | < 2 hours |
| Playbook success rate | Successful runs / total runs | > 95% |
| False positive rate | False cases / total cases | < 15% |

> 💡 **Build playbooks from the top-10 alert types first** — these typically represent 70% of volume. A well-tuned top-10 playbook set can automate 50%+ of analyst work within 6 months.

---

## Step 8: Capstone — SOAR Platform Design

**Scenario:** SOC with 50,000 alerts/day; 8 analysts; target 60% automation

```
SOAR Platform: Splunk SOAR (Phantom)

Automation targets:
  - Phishing: 95% auto (delete email, block domain, score user)
  - Malware: 80% auto (quarantine, isolate, enrich)
  - Brute force: 90% auto (block IP, lock account)
  - Data exfil: 50% auto (block session; analyst confirms scope)
  - Critical incidents: 20% auto (enrich + notify; human decides)

Integration stack:
  - EDR: CrowdStrike (isolate, contain, hunt)
  - Firewall: Palo Alto (block IP, block URL)
  - IAM: Active Directory (lock account, reset password)
  - Email: M365 (delete phishing, block sender)
  - TIP: MISP (IOC lookup, campaign context)
  - Ticketing: ServiceNow (case creation, SLA tracking)
  - Comms: Teams (SOC notifications, approvals)

Playbook count:
  - 30 fully automated playbooks
  - 20 semi-automated (human approval for destructive actions)
  - 10 notification-only (awareness, no action)

Expected outcomes:
  - Alert volume handled: 50,000/day (current) → 30,000 analyst-reviewed
  - MTTR: 45 min → 8 min (automated), 2h → 45 min (manual)
  - Analyst capacity freed: ~40% (available for proactive hunting)
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| SOAR pillars | Orchestration (APIs), Automation (no-human), Response (containment) |
| Playbook phases | Trigger → Triage → Enrich → Contain → Remediate → Notify → Close |
| Auto vs Manual | Critical containment = auto; destructive actions = human approval |
| Integration | EDR, firewall, IAM, TIP, ticketing — all via REST APIs |
| Case management | Every action tracked; SLA monitored; lessons learned |
| Automation target | 40-60% alert auto-resolution is mature SOC benchmark |
