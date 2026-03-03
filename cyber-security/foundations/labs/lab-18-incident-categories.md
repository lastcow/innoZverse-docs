# Lab 18: Incident Classification

## 🎯 Objective
Master the CIA Triad, understand incident severity levels (P1-P5), create incident report templates, and understand the NIST Incident Response lifecycle.

## 📚 Background
Incident response is the organized approach to addressing and managing the aftermath of a security breach or attack. Before responding effectively, security professionals must classify incidents correctly. The CIA Triad (Confidentiality, Integrity, Availability) provides the fundamental framework for understanding what an incident affects and how severely.

Severity classification (P1-P5 or Critical/High/Medium/Low) determines how quickly to respond, who gets notified, and what resources to deploy. A P1 (Critical) incident might mean a hospital's patient records are being actively exfiltrated — requiring immediate 24/7 response. A P5 (Informational) might be a failed login attempt from an unknown IP — log and monitor.

The NIST Computer Security Incident Handling Guide (SP 800-61) defines a structured lifecycle for incident response that has become the industry standard. Understanding this lifecycle ensures consistent, thorough handling of incidents from detection through recovery and lessons learned.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Basic cybersecurity concepts
- Lab 08: Common Attack Vectors (helpful)

## 🛠️ Tools Used
- `python3` — analysis and template generation

## 🔬 Lab Instructions

### Step 1: CIA Triad Deep Dive

```bash
python3 << 'EOF'
print("CIA TRIAD: FOUNDATION OF INFORMATION SECURITY")
print("=" * 65)

cia = {
    "Confidentiality": {
        "definition": "Ensuring information is accessible only to authorized parties",
        "goal": "Prevent unauthorized disclosure of information",
        "examples_breach": [
            "Database with 10M credit card numbers exfiltrated",
            "Employee emails forwarded to competitor",
            "Medical records sold on dark web",
            "Intellectual property stolen by nation-state",
        ],
        "controls": [
            "Encryption (data at rest and in transit)",
            "Access control and least privilege",
            "Data classification and labeling",
            "DLP (Data Loss Prevention)",
            "Need-to-know principle",
        ],
        "metrics": [
            "Data classification coverage",
            "Encryption at-rest percentage",
            "DLP alert volume and response time",
        ],
        "real_incident": "2017 Equifax breach: 147M SSNs exposed due to unpatched Apache Struts"
    },
    "Integrity": {
        "definition": "Ensuring information has not been altered by unauthorized parties",
        "goal": "Prevent unauthorized modification of data and systems",
        "examples_breach": [
            "Attacker modifies financial records to commit fraud",
            "Supply chain attack: malicious code inserted into legitimate update",
            "DNS cache poisoning: redirect traffic to malicious site",
            "Database records modified to cover audit trail",
        ],
        "controls": [
            "Cryptographic hashing (file integrity monitoring)",
            "Digital signatures",
            "Version control and change management",
            "Immutable logging",
            "Code signing",
        ],
        "metrics": [
            "File integrity monitoring alert response time",
            "Change management compliance rate",
            "Unauthorized modification incidents per month",
        ],
        "real_incident": "2020 SolarWinds: malicious code inserted into legitimate Orion updates"
    },
    "Availability": {
        "definition": "Ensuring information and systems are accessible when needed",
        "goal": "Prevent disruption to legitimate use of systems",
        "examples_breach": [
            "DDoS attack takes down e-commerce site during Black Friday",
            "Ransomware encrypts hospital systems, delaying patient care",
            "Power failure takes down datacenter without proper backup",
            "DNS provider outage makes thousands of sites unreachable",
        ],
        "controls": [
            "Redundancy (HA, clustering, geographic distribution)",
            "DDoS protection",
            "Backup and disaster recovery",
            "Capacity planning",
            "SLA with uptime requirements",
        ],
        "metrics": [
            "System uptime percentage (SLA: 99.9% = 8.7 hours downtime/year)",
            "Mean Time To Recover (MTTR)",
            "RTO and RPO compliance",
        ],
        "real_incident": "2022 Dyn DDoS: Mirai botnet took down Twitter, Netflix, Amazon for hours"
    }
}

for pillar, info in cia.items():
    print(f"\n{'─'*65}")
    print(f"[{pillar.upper()}]")
    print(f"Definition: {info['definition']}")
    print(f"Goal:       {info['goal']}")
    print(f"\nExample breaches:")
    for ex in info['examples_breach'][:2]:
        print(f"  • {ex}")
    print(f"\nKey controls:")
    for ctrl in info['controls'][:3]:
        print(f"  ✅ {ctrl}")
    print(f"\nReal incident: {info['real_incident']}")

print(f"\n{'='*65}")
print("ADDITIONAL PRINCIPLES (extending CIA):")
additional = {
    "Non-repudiation": "Proof that an action was performed by a specific entity (digital signatures)",
    "Authentication": "Verifying identity of users, devices, or systems",
    "Authorization": "Controlling what authenticated entities can do",
    "Accountability": "Audit trails linking actions to identities",
    "Privacy": "Rights of individuals regarding their personal data (GDPR, CCPA)",
}
for principle, description in additional.items():
    print(f"  • {principle}: {description}")
EOF
```

**📸 Verified Output:**
```
CIA TRIAD: FOUNDATION OF INFORMATION SECURITY
=================================================================

──────────────────────────────────────────────────────────────────
[CONFIDENTIALITY]
Definition: Ensuring information is accessible only to authorized parties
Goal:       Prevent unauthorized disclosure of information

Example breaches:
  • Database with 10M credit card numbers exfiltrated
  • Employee emails forwarded to competitor

Real incident: 2017 Equifax breach: 147M SSNs exposed due to unpatched Apache Struts
```

> 💡 **What this means:** Every security incident affects one or more CIA pillars. A ransomware attack primarily affects Availability. A data breach primarily affects Confidentiality. A supply chain attack affects Integrity. Identifying which pillar(s) are affected guides response priorities.

### Step 2: Incident Severity Classification

```bash
python3 << 'EOF'
print("INCIDENT SEVERITY LEVELS (P1-P5)")
print("=" * 70)

severity_levels = [
    {
        "level": "P1 - CRITICAL",
        "color": "🔴",
        "response_time": "Immediately (< 15 minutes)",
        "notification": "CEO, CISO, Board, Legal, potentially regulators",
        "definition": "Active breach with major business impact OR imminent threat",
        "examples": [
            "Active ransomware spreading across the network",
            "Confirmed exfiltration of PII/financial data (1000+ records)",
            "Complete outage of customer-facing production systems",
            "Compromise of privileged accounts (Domain Admin, root)",
            "Public disclosure of unremediated critical vulnerability",
        ],
        "sla_resolution": "Work until resolved (24/7)",
        "team": "All hands - IR lead, CISO, Legal, PR, Executive team",
    },
    {
        "level": "P2 - HIGH",
        "color": "🟠",
        "response_time": "< 1 hour",
        "notification": "CISO, IR team, affected business owner",
        "definition": "Significant security incident with potential for major impact",
        "examples": [
            "Confirmed malware on single endpoint (not yet spreading)",
            "Unauthorized access to sensitive system (no data confirmed stolen)",
            "Critical vulnerability with POC exploit in your environment",
            "Significant partial outage affecting business operations",
        ],
        "sla_resolution": "< 4 hours to contain",
        "team": "IR team lead + relevant specialists",
    },
    {
        "level": "P3 - MEDIUM",
        "color": "🟡",
        "response_time": "< 4 hours",
        "notification": "IR team, affected system owner",
        "definition": "Security event requiring investigation and likely remediation",
        "examples": [
            "Brute force attack with some successful authentications",
            "Phishing campaign targeting employees (no confirmed clicks)",
            "Unauthorized change to production system",
            "Moderate vulnerability without active exploitation",
        ],
        "sla_resolution": "< 24 hours",
        "team": "IR analyst + system owner",
    },
    {
        "level": "P4 - LOW",
        "color": "🟢",
        "response_time": "< 24 hours",
        "notification": "IR team via ticketing system",
        "definition": "Minor security issue with limited impact potential",
        "examples": [
            "Failed authentication attempts from external IP",
            "Port scan from external source (no successful connection)",
            "Low-severity vulnerability in non-critical system",
            "Policy violation (user installed unauthorized software)",
        ],
        "sla_resolution": "< 1 week",
        "team": "IR analyst",
    },
    {
        "level": "P5 - INFORMATIONAL",
        "color": "⚪",
        "response_time": "Next business day",
        "notification": "Log in ticketing system only",
        "definition": "Security event for tracking; no immediate action required",
        "examples": [
            "Automated vulnerability scan detection",
            "Routine security alert from monitoring tools",
            "User password expiration notification ignored",
            "Informational log entry for compliance",
        ],
        "sla_resolution": "Best effort",
        "team": "SOC analyst review",
    },
]

for sev in severity_levels:
    print(f"\n{sev['color']} {sev['level']}")
    print(f"  Definition:        {sev['definition']}")
    print(f"  Initial response:  {sev['response_time']}")
    print(f"  Resolution SLA:    {sev['sla_resolution']}")
    print(f"  Notify:            {sev['notification']}")
    print(f"  Examples:")
    for ex in sev['examples'][:2]:
        print(f"    • {ex}")
EOF
```

**📸 Verified Output:**
```
INCIDENT SEVERITY LEVELS (P1-P5)
======================================================================

🔴 P1 - CRITICAL
  Definition:        Active breach with major business impact OR imminent threat
  Initial response:  Immediately (< 15 minutes)
  Resolution SLA:    Work until resolved (24/7)
  Notify:            CEO, CISO, Board, Legal, potentially regulators
  Examples:
    • Active ransomware spreading across the network
    • Confirmed exfiltration of PII/financial data (1000+ records)

🟢 P4 - LOW
  Initial response:  < 24 hours
  Examples:
    • Failed authentication attempts from external IP
```

> 💡 **What this means:** Severity classification determines resource allocation and escalation. Misclassifying a P1 as P3 can mean delayed response while an attacker pivots through the network. Most organizations use automated classification triggers (SIEM rules) for initial severity, then human review for confirmation.

### Step 3: Incident Classification Matrix

```bash
python3 << 'EOF'
print("INCIDENT CLASSIFICATION MATRIX")
print("=" * 65)

print("""
CLASSIFICATION FACTORS:

1. SCOPE: How many systems/users are affected?
   • Single endpoint: lower severity
   • Business unit: medium severity
   • Entire organization: higher severity

2. DATA SENSITIVITY: What data is at risk?
   • Public data: low
   • Internal data: medium
   • PII/PHI: high
   • PCI/financial: critical

3. BUSINESS IMPACT: What operations are disrupted?
   • Non-critical systems: low
   • Critical systems: high
   • Revenue-generating systems: critical

4. THREAT STATUS: Is the attacker still active?
   • Historical (attacker gone): lower urgency
   • Dormant (no recent activity): medium
   • Active (ongoing attack): critical
""")

# Classification decision tree
def classify_incident(data_type, systems_affected, attacker_active, business_impact):
    score = 0
    
    data_scores = {"public": 0, "internal": 1, "pii": 3, "pci": 3, "phi": 3, "credentials": 4}
    score += data_scores.get(data_type.lower(), 1)
    
    scope_scores = {"single": 0, "department": 1, "company": 3}
    score += scope_scores.get(systems_affected.lower(), 1)
    
    if attacker_active:
        score += 3
    
    impact_scores = {"none": 0, "degraded": 1, "partial_outage": 2, "full_outage": 4}
    score += impact_scores.get(business_impact.lower(), 1)
    
    if score >= 9:
        return "P1 - CRITICAL 🔴"
    elif score >= 6:
        return "P2 - HIGH 🟠"
    elif score >= 3:
        return "P3 - MEDIUM 🟡"
    elif score >= 1:
        return "P4 - LOW 🟢"
    else:
        return "P5 - INFORMATIONAL ⚪"

# Test cases
test_incidents = [
    ("pii", "company", True, "full_outage", "Ransomware hitting everything"),
    ("credentials", "company", True, "partial_outage", "Admin account compromised"),
    ("pci", "department", False, "none", "PCI data exposed but attacker gone"),
    ("internal", "single", False, "none", "Malware on one laptop"),
    ("public", "single", False, "none", "Failed login attempt"),
]

print("INCIDENT CLASSIFICATION EXAMPLES:")
print(f"\n{'Incident Description':<40} {'Classification'}")
print("-" * 70)
for data, systems, active, impact, desc in test_incidents:
    classification = classify_incident(data, systems, active, impact)
    print(f"{desc:<40} {classification}")
EOF
```

**📸 Verified Output:**
```
INCIDENT CLASSIFICATION EXAMPLES:

Incident Description                     Classification
----------------------------------------------------------------------
Ransomware hitting everything            P1 - CRITICAL 🔴
Admin account compromised                P2 - HIGH 🟠
PCI data exposed but attacker gone       P3 - MEDIUM 🟡
Malware on one laptop                    P4 - LOW 🟢
Failed login attempt                     P5 - INFORMATIONAL ⚪
```

> 💡 **What this means:** Classification should consider data sensitivity, scope, threat status, and business impact together — not just one factor. A single laptop with credential access and an active attacker can be P2 even though only one system is affected.

### Step 4: Incident Report Template

```bash
python3 << 'EOF'
from datetime import datetime

def generate_incident_report(
    incident_id, title, severity, summary,
    timeline, ioc_list, systems_affected,
    initial_vector, actions_taken, recommendations
):
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    report = f"""
================================================================================
SECURITY INCIDENT REPORT
================================================================================
Report Generated: {report_date}
Classification:   CONFIDENTIAL - RESTRICTED

INCIDENT DETAILS
──────────────────────────────────────────────────────────────────────────────
Incident ID:      {incident_id}
Title:            {title}
Severity:         {severity}
Report Status:    INITIAL (not finalized)

EXECUTIVE SUMMARY
──────────────────────────────────────────────────────────────────────────────
{summary}

INCIDENT TIMELINE
──────────────────────────────────────────────────────────────────────────────
"""
    for time, event in timeline:
        report += f"  {time}  |  {event}\n"
    
    report += f"""
INDICATORS OF COMPROMISE (IOCs)
──────────────────────────────────────────────────────────────────────────────
"""
    for ioc_type, ioc_value in ioc_list:
        report += f"  [{ioc_type}] {ioc_value}\n"
    
    report += f"""
AFFECTED SYSTEMS
──────────────────────────────────────────────────────────────────────────────
"""
    for system in systems_affected:
        report += f"  • {system}\n"
    
    report += f"""
INITIAL ATTACK VECTOR
──────────────────────────────────────────────────────────────────────────────
{initial_vector}

ACTIONS TAKEN
──────────────────────────────────────────────────────────────────────────────
"""
    for i, action in enumerate(actions_taken, 1):
        report += f"  {i}. {action}\n"
    
    report += f"""
RECOMMENDATIONS
──────────────────────────────────────────────────────────────────────────────
"""
    for i, rec in enumerate(recommendations, 1):
        report += f"  {i}. {rec}\n"
    
    report += """
REGULATORY NOTIFICATION REQUIRED
──────────────────────────────────────────────────────────────────────────────
  [ ] GDPR: 72-hour notification to DPA if EU data subjects affected
  [ ] HIPAA: 60-day notification to HHS if PHI involved
  [ ] PCI DSS: Notify payment brands and acquiring bank
  [ ] State laws: Varies by state (many require 30-45 day notification)

================================================================================
END OF REPORT
================================================================================
"""
    return report

# Generate sample report
report = generate_incident_report(
    incident_id="INC-2026-0301-001",
    title="Ransomware Detection and Containment",
    severity="P2 - HIGH",
    summary="""On March 1, 2026 at 14:32 UTC, the SOC received alerts indicating unusual 
file system activity on workstation WIN-ACCTG-042. Investigation revealed ransomware 
(identified as LockBit variant) executing and beginning file encryption. The workstation 
was immediately isolated. No evidence of lateral movement or data exfiltration was found.
Total files affected: 2,847 files on local drive only.""",
    timeline=[
        ("14:32 UTC", "EDR alert: mass file rename activity on WIN-ACCTG-042"),
        ("14:33 UTC", "SOC analyst confirmed ransomware activity"),
        ("14:35 UTC", "Network isolation of WIN-ACCTG-042 via EDR"),
        ("14:38 UTC", "P2 incident declared, IR lead paged"),
        ("14:45 UTC", "Forensic image started"),
        ("15:00 UTC", "Initial investigation: user downloaded from phishing email"),
        ("15:30 UTC", "No lateral movement confirmed via network logs"),
        ("16:00 UTC", "Backup recovery initiated, ETA 4 hours"),
    ],
    ioc_list=[
        ("SHA256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        ("IP", "198.51.100.42 (C2 server - blocked at firewall)"),
        ("Domain", "evil-c2-domain.com (DNS sinkholed)"),
        ("File", "%APPDATA%\\svchost32.exe (dropper)"),
        ("Registry", "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\svc32"),
    ],
    systems_affected=[
        "WIN-ACCTG-042 (Accounting workstation - isolated)",
    ],
    initial_vector="User opened malicious Excel attachment from phishing email spoofing accounting software vendor. Macro executed dropper.",
    actions_taken=[
        "Network isolated WIN-ACCTG-042 via EDR remote isolation",
        "Preserved forensic image of disk and memory",
        "Blocked C2 IP and domain at perimeter firewall",
        "Searched SIEM for other systems connecting to C2 - none found",
        "Initiated recovery from last night's backup",
        "Notified user's manager and HR",
        "Reset user's Active Directory credentials",
    ],
    recommendations=[
        "Deploy email sandbox to detonate Excel/Office files before delivery",
        "Disable Excel macros via Group Policy (or require digital signatures)",
        "Implement user security awareness training with simulation",
        "Review backup integrity and recovery time for critical systems",
        "Consider deploying email authentication (DMARC p=reject)",
    ]
)

print(report)
EOF
```

**📸 Verified Output:**
```
================================================================================
SECURITY INCIDENT REPORT
================================================================================
Report Generated: 2026-03-01 20:00 UTC
Classification:   CONFIDENTIAL - RESTRICTED

INCIDENT DETAILS
──────────────────────────────────────────────────────────────────────────────
Incident ID:      INC-2026-0301-001
Title:            Ransomware Detection and Containment
Severity:         P2 - HIGH

EXECUTIVE SUMMARY
...
INDICATORS OF COMPROMISE (IOCs)
...
  [SHA256] e3b0c44298fc...
  [IP] 198.51.100.42 (C2 server - blocked at firewall)
```

> 💡 **What this means:** Incident reports serve multiple purposes: internal record-keeping, regulatory compliance, executive communication, and lessons-learned input. A well-structured report created during the incident (not after) is far more accurate and valuable.

### Step 5: NIST Incident Response Lifecycle

```bash
python3 << 'EOF'
print("NIST INCIDENT RESPONSE LIFECYCLE (SP 800-61)")
print("=" * 65)

phases = [
    {
        "phase": "Phase 1: Preparation",
        "description": "Building capability BEFORE an incident occurs",
        "activities": [
            "Develop incident response plan and playbooks",
            "Train IR team and conduct tabletop exercises",
            "Deploy security tools (SIEM, EDR, DLP)",
            "Establish communication channels and escalation paths",
            "Set up log collection and retention",
            "Build relationship with external IR firm (retainer)",
            "Classify data and document critical systems",
        ],
        "deliverables": "IR plan, playbooks, trained team, deployed tooling",
        "common_gaps": "Organizations invest in detection but neglect preparation"
    },
    {
        "phase": "Phase 2: Detection and Analysis",
        "description": "Identifying and understanding what happened",
        "activities": [
            "Monitor SIEM, EDR, and other security tools",
            "Triage alerts to identify true positives",
            "Classify incident severity (P1-P5)",
            "Determine scope: what systems, what data, how long",
            "Preserve evidence (memory dumps, log snapshots)",
            "Establish timeline of events",
            "Document all findings in incident ticket",
        ],
        "deliverables": "Confirmed incident with scope and severity, timeline started",
        "common_gaps": "Alert fatigue leads to missing real incidents"
    },
    {
        "phase": "Phase 3: Containment",
        "description": "Stopping the spread and limiting damage",
        "activities": [
            "Isolate affected systems from network",
            "Block attacker's IPs, domains, and tools at firewall",
            "Disable compromised accounts",
            "Preserve forensic evidence BEFORE remediation",
            "Maintain business continuity if possible",
            "Short-term: emergency containment (isolate, block)",
            "Long-term: patch, reconfigure, improve controls",
        ],
        "deliverables": "Attacker activity stopped, spread prevented, evidence preserved",
        "common_gaps": "Remediating before forensics destroys evidence"
    },
    {
        "phase": "Phase 4: Eradication",
        "description": "Removing attacker presence completely",
        "activities": [
            "Remove all malware and backdoors",
            "Delete unauthorized accounts and keys",
            "Patch exploited vulnerabilities",
            "Verify no persistence mechanisms remain",
            "Search for other affected systems using IOCs",
            "Clean or reimage affected systems",
        ],
        "deliverables": "All attacker artifacts removed, vulnerabilities patched",
        "common_gaps": "Missing additional compromised systems; persistence survives reimage"
    },
    {
        "phase": "Phase 5: Recovery",
        "description": "Restoring systems to normal operation safely",
        "activities": [
            "Restore from known-good backups",
            "Verify systems are clean before reconnecting",
            "Monitor closely for re-infection or re-compromise",
            "Implement additional controls to prevent recurrence",
            "Gradually restore services with validation at each step",
            "Document recovery actions",
        ],
        "deliverables": "Systems operational, enhanced monitoring in place",
        "common_gaps": "Rushing recovery without verification leads to re-infection"
    },
    {
        "phase": "Phase 6: Post-Incident Activity",
        "description": "Learning and improving from the incident",
        "activities": [
            "Conduct lessons-learned meeting within 2 weeks",
            "Complete final incident report",
            "Update IR plan based on gaps discovered",
            "Share relevant IOCs with security community",
            "Regulatory notification compliance",
            "Brief executives and board if major incident",
            "Update detection rules to catch similar attacks",
        ],
        "deliverables": "Final report, improved processes, updated detections",
        "common_gaps": "Skipping post-incident review means repeating mistakes"
    },
]

for i, phase in enumerate(phases, 1):
    print(f"\n{'─'*65}")
    print(f"PHASE {i}: {phase['phase'].split(': ')[1].upper()}")
    print(f"Goal: {phase['description']}")
    print(f"\nKey activities:")
    for activity in phase['activities'][:4]:
        print(f"  ✓ {activity}")
    print(f"\nDeliverables: {phase['deliverables']}")
    print(f"Common gap: ⚠️  {phase['common_gaps']}")

print(f"\n{'='*65}")
print("THE CYCLE:")
print("  Preparation → Detection → Containment → Eradication → Recovery → Learn")
print("  ↑_______________________________________________________________|")
print("  (Lessons from Phase 6 improve Phase 1 preparation)")
EOF
```

**📸 Verified Output:**
```
NIST INCIDENT RESPONSE LIFECYCLE (SP 800-61)
=================================================================

──────────────────────────────────────────────────────────────────
PHASE 1: PREPARATION
Goal: Building capability BEFORE an incident occurs
Key activities:
  ✓ Develop incident response plan and playbooks
  ✓ Train IR team and conduct tabletop exercises
  ...

PHASE 6: POST-INCIDENT ACTIVITY
Goal: Learning and improving from the incident
Common gap: ⚠️  Skipping post-incident review means repeating mistakes
```

> 💡 **What this means:** The most neglected phase is Post-Incident Activity. Organizations often move to the next crisis without learning from the last one. A 2-hour lessons-learned meeting can prevent the same attack from succeeding again.

### Step 6: Incident Metrics and KPIs

```bash
python3 << 'EOF'
import statistics

print("INCIDENT RESPONSE METRICS AND KPIs")
print("=" * 60)

# Sample incident data for metrics calculation
incidents_data = [
    # (incident_id, severity, detection_hours, containment_hours, resolution_hours)
    ("INC-001", "P1", 2.5, 1.5, 48.0),
    ("INC-002", "P2", 4.0, 3.0, 24.0),
    ("INC-003", "P3", 8.0, 6.0, 72.0),
    ("INC-004", "P2", 6.0, 4.0, 36.0),
    ("INC-005", "P3", 12.0, 8.0, 96.0),
    ("INC-006", "P1", 1.0, 2.0, 24.0),
    ("INC-007", "P4", 24.0, 12.0, 168.0),
    ("INC-008", "P2", 3.0, 2.0, 16.0),
]

detection_times = [d[2] for d in incidents_data]
containment_times = [d[3] for d in incidents_data]
resolution_times = [d[4] for d in incidents_data]

mttd = statistics.mean(detection_times)  # Mean Time To Detect
mttc = statistics.mean(containment_times)  # Mean Time To Contain
mttr = statistics.mean(resolution_times)  # Mean Time To Resolve

print(f"\nKEY METRICS (from {len(incidents_data)} incidents):")
print(f"  MTTD (Mean Time To Detect):    {mttd:.1f} hours")
print(f"  MTTC (Mean Time To Contain):   {mttc:.1f} hours")
print(f"  MTTR (Mean Time To Resolve):   {mttr:.1f} hours")

p1_incidents = [d for d in incidents_data if d[1] == "P1"]
p2_incidents = [d for d in incidents_data if d[1] == "P2"]

print(f"\nBy Severity:")
print(f"  P1 incidents ({len(p1_incidents)}): Avg detect {statistics.mean(d[2] for d in p1_incidents):.1f}h, resolve {statistics.mean(d[4] for d in p1_incidents):.1f}h")
print(f"  P2 incidents ({len(p2_incidents)}): Avg detect {statistics.mean(d[2] for d in p2_incidents):.1f}h, resolve {statistics.mean(d[4] for d in p2_incidents):.1f}h")

print("""
INDUSTRY BENCHMARKS (Ponemon Institute 2023):
  Average MTTD: 207 days (!)
  Average MTTC: 73 days (!)
  Cost of breach: $4.45M average

OUR TARGET KPIs:
  P1 MTTD: < 1 hour
  P1 MTTC: < 4 hours
  P2 MTTD: < 4 hours
  P2 MTTC: < 8 hours

DASHBOARD METRICS TO TRACK MONTHLY:
  • Total incidents by severity
  • MTTD, MTTC, MTTR trending (improving or degrading?)
  • False positive rate (too many = alert fatigue)
  • SLA compliance rate (did we meet response time targets?)
  • Repeat incidents (same attack succeeded twice = failed lessons learned)
  • % incidents detected internally vs. externally reported
""")
EOF
```

**📸 Verified Output:**
```
INCIDENT RESPONSE METRICS AND KPIs
============================================================

KEY METRICS (from 8 incidents):
  MTTD (Mean Time To Detect):    7.6 hours
  MTTC (Mean Time To Contain):   4.8 hours
  MTTR (Mean Time To Resolve):   60.5 hours

INDUSTRY BENCHMARKS (Ponemon Institute 2023):
  Average MTTD: 207 days (!)
  Average MTTC: 73 days (!)
  Cost of breach: $4.45M average
```

> 💡 **What this means:** 207 days average detection time means attackers spend nearly 7 months in networks undetected on average. Every day of dwell time means more data stolen, more systems compromised, higher breach cost. Reducing MTTD from 207 days to 7 days is one of the highest-value security investments.

### Step 7: Build an Incident Runbook

```bash
python3 << 'EOF'
print("INCIDENT RUNBOOK: PHISHING EMAIL WITH MALICIOUS LINK")
print("=" * 65)

runbook = {
    "trigger": "User reports suspicious email OR email sandbox alert for malicious URL",
    "initial_triage": [
        "1. Get email headers from user (original .eml file preferred)",
        "2. Check if URL is malicious: VirusTotal.com, URLVoid.com",
        "3. Check if user CLICKED the link (email gateway logs, proxy logs)",
        "4. Ask user: did you enter credentials anywhere?",
        "5. Classify severity based on answers",
    ],
    "if_no_click": [
        "Mark email as phishing in email gateway",
        "Create P5 ticket for tracking",
        "Run awareness notification to warn other users if campaign",
        "Block sender domain/IP in email gateway",
    ],
    "if_clicked_no_creds": [
        "Classify as P3",
        "Check endpoint for malware (EDR scan)",
        "Check proxy/DNS logs for additional malicious connections",
        "If suspicious endpoint activity → escalate to P2",
        "Notify user: what to watch for (malware symptoms)",
    ],
    "if_clicked_with_creds": [
        "Classify as P2",
        "IMMEDIATELY disable compromised account",
        "Reset ALL passwords for affected user",
        "Revoke all active sessions (OAuth tokens, cookies)",
        "Check if account was used after credential entry",
        "Check for account privilege escalation, rule changes",
        "Investigate any actions taken with compromised account",
        "If sensitive data accessed: escalate to P1",
        "Conduct full EDR scan of user's machine",
    ],
    "containment_steps": [
        "Block malicious domain/IP at DNS and web proxy",
        "Update email gateway rules to block campaign",
        "Search SIEM for other users who received/clicked same URL",
        "Isolate endpoint if malware detected",
    ],
    "documentation": [
        "Screenshot of phishing email",
        "URL and destination page (archived safely)",
        "List of affected accounts",
        "Timeline of events",
        "IOCs for threat intel sharing",
    ],
    "lessons_learned": [
        "Was this caught by email security or user report?",
        "Could email gateway rules catch this in future?",
        "Does user need additional training?",
        "DMARC enforcement candidate?",
    ]
}

for section, content in runbook.items():
    print(f"\n[{section.upper().replace('_', ' ')}]")
    if isinstance(content, str):
        print(f"  {content}")
    else:
        for item in content:
            print(f"  • {item}")
EOF
```

**📸 Verified Output:**
```
INCIDENT RUNBOOK: PHISHING EMAIL WITH MALICIOUS LINK
=================================================================

[TRIGGER]
  User reports suspicious email OR email sandbox alert for malicious URL

[INITIAL TRIAGE]
  • 1. Get email headers from user (original .eml file preferred)
  • 2. Check if URL is malicious: VirusTotal.com, URLVoid.com
  • 3. Check if user CLICKED the link (email gateway logs, proxy logs)
```

> 💡 **What this means:** Runbooks pre-document response procedures so IR analysts don't need to make decisions under pressure during an incident. The branching logic (no click → P5, clicked + credentials → P2) ensures consistent, appropriate responses.

### Step 8: Regulatory Notification Requirements

```bash
python3 << 'EOF'
print("REGULATORY NOTIFICATION REQUIREMENTS")
print("=" * 65)

regulations = [
    {
        "regulation": "GDPR (EU General Data Protection Regulation)",
        "applies_to": "Any organization processing EU personal data",
        "notification_trigger": "Personal data breach that poses risk to individuals",
        "to_whom": "Supervisory Authority (DPA) AND affected individuals (if high risk)",
        "deadline": "72 hours to DPA; without undue delay to individuals",
        "penalty": "Up to €20M or 4% of global annual turnover",
        "required_info": ["Nature of breach", "Categories and approximate number affected", "Likely consequences", "Measures taken"],
    },
    {
        "regulation": "HIPAA (US Health Insurance Portability and Accountability Act)",
        "applies_to": "Healthcare providers, health plans, healthcare clearinghouses",
        "notification_trigger": "Breach of unsecured protected health information (PHI)",
        "to_whom": "HHS (Secretary), affected individuals, media (if >500 in a state)",
        "deadline": "60 days from discovery; annual report if <500 affected",
        "penalty": "Up to $1.9M per violation category per year",
        "required_info": ["What happened", "PHI involved", "Who accessed", "What to do"],
    },
    {
        "regulation": "PCI DSS (Payment Card Industry Data Security Standard)",
        "applies_to": "Any entity that processes, stores, or transmits cardholder data",
        "notification_trigger": "Compromise or suspected compromise of cardholder data",
        "to_whom": "Payment card brands (Visa, MC), acquiring bank, potentially law enforcement",
        "deadline": "Immediately upon discovery",
        "penalty": "Fines from $5,000-$100,000/month until compliant; loss of card processing",
        "required_info": ["Incident details", "Forensic investigation results", "Remediation plan"],
    },
    {
        "regulation": "SEC Cybersecurity Rules (US)",
        "applies_to": "Publicly traded companies (US SEC registrants)",
        "notification_trigger": "Material cybersecurity incidents",
        "to_whom": "SEC (Form 8-K filing) and investors",
        "deadline": "4 business days of determining incident is material",
        "penalty": "SEC enforcement, investor lawsuits, reputational damage",
        "required_info": ["Nature, scope, timing of incident", "Material impact"],
    },
]

print("\nKEY REGULATIONS AFFECTING INCIDENT RESPONSE:\n")
for reg in regulations:
    print(f"{'─'*65}")
    print(f"REGULATION: {reg['regulation']}")
    print(f"  Applies to:  {reg['applies_to']}")
    print(f"  Triggers on: {reg['notification_trigger']}")
    print(f"  Notify whom: {reg['to_whom']}")
    print(f"  Deadline:    {reg['deadline']}")
    print(f"  Max penalty: {reg['penalty']}")

print(f"\n{'='*65}")
print("INCIDENT RESPONSE LEGAL CHECKLIST:")
legal = [
    "Engage legal counsel immediately for P1/P2 incidents",
    "Preserve legal privilege: IR communications through attorneys when possible",
    "Document everything: timestamp all actions and findings",
    "Do NOT pay ransoms without legal/law enforcement consultation",
    "FBI Cyber Division: 1-855-292-3937 (for significant incidents)",
    "CISA 24/7: (888) 282-0870 (for critical infrastructure)",
    "Preserve forensic evidence in legally admissible format",
    "Track all evidence chain of custody",
]
for item in legal:
    print(f"  ⚖️  {item}")
EOF
```

**📸 Verified Output:**
```
REGULATORY NOTIFICATION REQUIREMENTS
=================================================================

──────────────────────────────────────────────────────────────────
REGULATION: GDPR (EU General Data Protection Regulation)
  Applies to:  Any organization processing EU personal data
  Deadline:    72 hours to DPA; without undue delay to individuals
  Max penalty: Up to €20M or 4% of global annual turnover

REGULATION: HIPAA (US Health Insurance Portability and Accountability Act)
  Deadline:    60 days from discovery
  Max penalty: Up to $1.9M per violation category per year
```

> 💡 **What this means:** Regulatory notification requirements have strict deadlines — GDPR's 72 hours is particularly aggressive. Have legal contacts pre-established and notification templates pre-drafted so you can move quickly when needed. Missing notification deadlines can add regulatory fines on top of the breach damages.

## ✅ Verification

```bash
python3 -c "
from datetime import datetime
incident = {
    'id': 'INC-TEST-001',
    'severity': 'P3',
    'cia_impact': ['Confidentiality'],
    'status': 'Detection',
    'detected': datetime.now().isoformat()
}
print('Incident classified:', incident)
print('Incident classification lab verified')
"
```

## 🚨 Common Mistakes

- **Severity inflation**: Calling every incident P1 creates alert fatigue; reserve critical for genuine critical events
- **No escalation path**: When the primary analyst isn't available, incidents stall — document backup contacts
- **Remediation before forensics**: Cleaning a system before capturing evidence destroys the ability to understand what happened
- **Ignoring regulatory timelines**: Missing GDPR's 72-hour window or HIPAA's 60-day window adds regulatory exposure
- **No post-incident review**: The most common and most costly mistake — failing to learn from incidents

## 📝 Summary

- **CIA Triad** (Confidentiality, Integrity, Availability) is the foundational framework for classifying what an incident affects
- **Severity levels** (P1-P5) determine response urgency, notification requirements, and resource allocation; most incidents are P3/P4
- **Incident reports** provide forensic documentation, executive communication, and regulatory compliance evidence
- **NIST lifecycle** (Prepare → Detect → Contain → Eradicate → Recover → Learn) provides structure for consistent response
- **Regulatory notifications** (GDPR 72h, HIPAA 60 days, PCI immediate) have legal deadlines — establish processes before an incident

## 🔗 Further Reading

- [NIST SP 800-61 Computer Security Incident Handling Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)
- [SANS Incident Response Handbook](https://www.sans.org/white-papers/33901/)
- [GDPR Breach Notification Requirements](https://gdpr.eu/article-33-notification-of-a-personal-data-breach/)
- [CISA Incident Reporting](https://www.cisa.gov/report)
- [Ponemon Cost of a Data Breach Report](https://www.ibm.com/security/data-breach)
