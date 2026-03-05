# Lab 11: Incident Response Framework

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Apply NIST SP 800-61 incident response lifecycle
- Build IR playbooks for ransomware, breach, and insider threats
- Define RACI matrix and communication plan
- Implement a Python incident timeline builder

---

## Step 1: NIST SP 800-61 IR Lifecycle

```
┌──────────────┐
│  PREPARATION │  ← IR plan, playbooks, tools, training, tabletops
└──────┬───────┘
       │
┌──────▼───────────────┐
│  DETECTION &         │  ← SIEM alerts, threat intel, user reports
│  ANALYSIS            │     Log analysis, triage, severity assessment
└──────┬───────────────┘
       │
┌──────▼───────────────┐
│  CONTAINMENT,        │
│  ERADICATION &       │  ← Isolate, remove malware, patch, restore
│  RECOVERY            │
└──────┬───────────────┘
       │
┌──────▼───────────────┐
│  POST-INCIDENT       │  ← Lessons learned, process improvements
│  ACTIVITY            │     Threat intel update, detection improvement
└──────────────────────┘
```

**Incident severity levels:**

| Level | Name | Examples | Response Time |
|-------|------|---------|--------------|
| SEV1 | Critical | Ransomware, active breach, data exfil | Immediate (< 15 min) |
| SEV2 | High | Compromised admin account, C2 detected | < 1 hour |
| SEV3 | Medium | Phishing success, malware detection | < 4 hours |
| SEV4 | Low | Policy violation, failed login attempts | < 24 hours |

---

## Step 2: Incident Timeline Builder + Triage

```python
import datetime

class IncidentTimeline:
    def __init__(self, incident_id):
        self.id = incident_id
        self.events = []

    def add(self, timestamp, phase, action, actor):
        self.events.append({'ts': timestamp, 'phase': phase, 'action': action, 'actor': actor})

    def triage(self, ioc_type, severity):
        playbooks = {
            'ransomware': ['Isolate host', 'Snapshot memory', 'Disable network', 'Notify CISO', 'Engage IR team'],
            'data_breach': ['Identify scope', 'Revoke credentials', 'Preserve logs', 'Legal notification', 'Containment'],
            'insider':     ['HR involvement', 'Account suspension', 'Evidence preservation', 'Legal review']
        }
        print(f'  Triage: {ioc_type} | Severity: {severity}')
        actions = playbooks.get(ioc_type, ['Investigate'])
        for i, a in enumerate(actions, 1):
            print(f'    Step {i}: {a}')

    def report(self):
        print(f'=== Incident Timeline: {self.id} ===')
        for e in sorted(self.events, key=lambda x: x['ts']):
            print(f'  [{e["ts"]}] [{e["phase"]:<10}] {e["action"]} (by {e["actor"]})')

tl = IncidentTimeline('IR-2024-042')
tl.add('2024-01-15 08:32', 'DETECT',   'EDR alert: ransomware signature detected',    'EDR System')
tl.add('2024-01-15 08:35', 'TRIAGE',   'L1 analyst confirms true positive',           'analyst1')
tl.add('2024-01-15 08:40', 'CONTAIN',  'Host WIN-DC01 isolated from network',         'SOC-L2')
tl.add('2024-01-15 08:55', 'ANALYSE',  'Memory dump collected, IOCs extracted',       'forensics')
tl.add('2024-01-15 10:00', 'REMEDIATE','Malware removed, OS rebuilt from golden image','IR Team')
tl.add('2024-01-15 12:00', 'RECOVER',  'Host restored, monitoring enhanced',          'IT Ops')
tl.report()
print()
tl.triage('ransomware', 'CRITICAL')
```

📸 **Verified Output:**
```
=== Incident Timeline: IR-2024-042 ===
  [2024-01-15 08:32] [DETECT    ] EDR alert: ransomware signature detected (by EDR System)
  [2024-01-15 08:35] [TRIAGE    ] L1 analyst confirms true positive (by analyst1)
  [2024-01-15 08:40] [CONTAIN   ] Host WIN-DC01 isolated from network (by SOC-L2)
  [2024-01-15 08:55] [ANALYSE   ] Memory dump collected, IOCs extracted (by forensics)
  [2024-01-15 10:00] [REMEDIATE ] Malware removed, OS rebuilt from golden image (by IR Team)
  [2024-01-15 12:00] [RECOVER   ] Host restored, monitoring enhanced (by IT Ops)

  Triage: ransomware | Severity: CRITICAL
    Step 1: Isolate host
    Step 2: Snapshot memory
    Step 3: Disable network
    Step 4: Notify CISO
    Step 5: Engage IR team
```

---

## Step 3: Ransomware Response Playbook

**Phase 1: Detect & Triage (0-15 minutes)**
- [ ] Confirm alert is not false positive (EDR + SIEM correlation)
- [ ] Identify affected hosts (blast radius assessment)
- [ ] Determine data classification of affected systems
- [ ] Assign incident severity (SEV1 for confirmed ransomware)
- [ ] Notify SOC L2, IR lead, CISO

**Phase 2: Containment (15-60 minutes)**
- [ ] Isolate affected hosts via EDR (network isolation mode)
- [ ] Block known C2 IPs/domains at firewall
- [ ] Disable compromised accounts
- [ ] Snapshot affected systems (preserve evidence)
- [ ] Identify patient zero (initial infection vector)

**Phase 3: Eradication (1-4 hours)**
- [ ] Memory dump + forensic collection
- [ ] Malware analysis (identify strain, capabilities)
- [ ] Full disk scan on all endpoints
- [ ] Identify and patch initial entry vector
- [ ] Remove all malware artifacts

**Phase 4: Recovery (4-48 hours)**
- [ ] Restore from clean backup (pre-infection snapshot)
- [ ] Validate data integrity before reconnecting
- [ ] Monitor for re-infection indicators
- [ ] Progressive restoration (crown jewels last)
- [ ] Communicate status to business stakeholders

---

## Step 4: Data Breach Response Playbook

**Immediate actions (< 30 minutes):**
1. Identify data types affected (PII, PAN, PHI, IP)
2. Determine scope: how many records, which systems
3. Revoke compromised credentials immediately
4. Preserve log evidence (chain of custody)
5. Engage legal/privacy team

**Notification obligations:**
| Regulation | Notification Deadline | To Whom |
|-----------|---------------------|---------|
| GDPR | 72 hours | Supervisory Authority + affected individuals |
| HIPAA | 60 days | HHS + affected individuals (>500 records: media) |
| PCI DSS | Immediately | Acquirer/card brands |
| CCPA | "Expedient" | California AG + affected residents |
| State breach laws | Varies (30-90 days) | State AG + individuals |

> 💡 **Evidence preservation** is critical for regulatory investigations. Do NOT turn off compromised systems without memory imaging. Use read-only forensic images (dd or FTK Imager).

---

## Step 5: RACI Matrix

**For ransomware incident:**

| Activity | CISO | IR Lead | SOC Analyst | Legal | IT Ops | HR |
|---------|------|---------|------------|-------|--------|-----|
| Declare incident | A/R | R | I | I | I | I |
| Contain affected hosts | I | A | R | - | R | - |
| Evidence collection | I | A | R | C | R | - |
| External communication | A | R | - | R | - | - |
| Regulatory notification | A | C | - | R | - | - |
| Recovery authorization | A | R | - | - | R | - |
| Lessons learned | I | A | R | - | C | - |
| HR for insider threats | I | A | - | C | - | R |

**RACI key:** R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## Step 6: Evidence Collection

**Digital forensics evidence order (RFC 3227):**
1. CPU registers, cache, running processes (most volatile)
2. RAM / memory image
3. Network connections (netstat, ARP table)
4. Temporary files, swap space
5. Hard disk / file system image
6. Remote logging, audit logs
7. Physical media / archived data (least volatile)

**Chain of custody:**
```
Evidence Item: WIN-DC01 memory image
Collected by:  forensics@corp.com
Date/Time:     2024-01-15 08:55 UTC
Method:        WinPmem (raw memory acquisition)
Hash (SHA256): abc123...
Storage:       Encrypted USB, case evidence vault
Transferred to: Legal team - 2024-01-15 14:00 UTC
```

---

## Step 7: Communication Plan

**Internal notification tree:**
```
SEV1 Alert
  → SOC Lead (immediate, phone)
  → CISO (< 5 min, phone)
  → CTO/CEO (< 30 min, if data breach likely)
  → Legal (< 30 min)
  → PR/Comms (< 1 hour, if public disclosure likely)
  → Board (< 24 hours)
```

**External communication principles:**
- **Never** speculate about scope before knowing facts
- Prepare holding statement within 1 hour of SEV1
- Designate single spokesperson (CISO or Legal)
- Customer notification via secure channel (email + website)
- Regulator notification: documented, dated, via counsel

---

## Step 8: Capstone — IR Programme Design

**Scenario:** Build IR capability for 5,000-employee healthcare organisation

```
IR Programme Components:

1. IR Plan (document):
   - Scope, authority, contact tree
   - Severity definitions + escalation thresholds
   - External resource contacts (MSSP, forensics firm, legal, PR)
   - Regulatory notification checklists (HIPAA, GDPR, state laws)

2. Playbook library (15 playbooks):
   - Ransomware, data breach, insider threat
   - Phishing, BEC (business email compromise)
   - Cloud incident (AWS/Azure), DDoS
   - Medical device compromise, EHR breach

3. Tools:
   - EDR: CrowdStrike (isolation, memory forensics)
   - SOAR: Splunk SOAR (playbook automation)
   - Forensics: Velociraptor (fleet investigation)
   - Case management: Jira (with IR project template)

4. Testing programme:
   - Tabletop exercise: quarterly (different scenario each time)
   - Full simulation: annual (red team + IR response)
   - Playbook review: after every SEV1/2 incident

5. HIPAA requirements:
   - Breach < 500 records: annual HHS report + individual notice
   - Breach > 500 records: immediate HHS + media notification
   - Designated Privacy Officer as IR stakeholder
   - 6-year record retention for IR documentation

6. Metrics:
   - MTTD target: < 4 hours
   - MTTR target: < 8 hours (SEV1/2)
   - Regulatory notification: 100% within deadline
   - Post-incident review: 100% within 2 weeks
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| NIST SP 800-61 | Prepare → Detect → Contain/Eradicate/Recover → Post-incident |
| SEV levels | SEV1 (critical, immediate) → SEV4 (low, 24h) |
| Ransomware playbook | Isolate → snapshot → eradicate → restore from backup |
| RACI | Clear accountability; one A per activity |
| Evidence | Order: volatile first (RAM) → persistent (disk) |
| Chain of custody | Hash, document, secure storage |
| Notifications | GDPR 72h, HIPAA 60 days, PCI immediate |
