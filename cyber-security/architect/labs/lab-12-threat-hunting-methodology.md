# Lab 12: Threat Hunting Methodology

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Apply PEAK framework for structured threat hunting
- Build hypothesis-driven hunts using MITRE ATT&CK
- Detect lateral movement, persistence, and C2 patterns
- Implement a Python log analyser for lateral movement detection

---

## Step 1: Threat Hunting Philosophy

**What is threat hunting?**
> Proactive, human-led investigation to find threats that have evaded automated detection. Assumes breach has occurred; seeks evidence.

**Hunting vs monitoring:**
| Monitoring | Hunting |
|-----------|---------|
| Reactive (alert-driven) | Proactive (hypothesis-driven) |
| Automated | Human-led |
| Known-bad detection | Unknown/novel threat discovery |
| L1/L2 analyst | L3 senior analyst |
| Continuous | Sprint-based (2-4 week cycles) |

**PEAK Framework (Prepare, Execute, Act on Knowledge):**
```
PREPARE:
  - Define hypothesis (what TTP are we hunting?)
  - Identify required data sources
  - Validate data availability and quality
  - Define success criteria

EXECUTE:
  - Collect and filter relevant data
  - Apply hunting technique (statistical, pattern, ML)
  - Investigate anomalies
  - Document findings

ACT on KNOWLEDGE:
  - If threat found: escalate to IR
  - Regardless: create detection rule from findings
  - Update threat intel (MISP)
  - Improve data collection gaps
```

---

## Step 2: MITRE ATT&CK — Hunt Hypotheses

**Hypothesis structure:**
```
"Threat actors using [TTP: T1021.002 - SMB/Windows Admin Shares]
 may be conducting lateral movement using the svc_backup service account
 based on [threat intel: APT28 campaign] or [observed anomaly: after-hours logins]"
```

**High-priority TTPs to hunt (financial sector):**

| ATT&CK ID | Technique | Hunt Signal |
|-----------|---------|------------|
| T1078 | Valid Accounts | Unusual login times, locations |
| T1021.002 | SMB Lateral Movement | Horizontal login spread, ADMIN$ access |
| T1003.001 | LSASS Memory Dump | Event ID 4688 + lsass.exe access |
| T1059.001 | PowerShell | Encoded commands, download cradles |
| T1105 | Ingress Tool Transfer | Outbound downloads from unexpected processes |
| T1071.001 | HTTP C2 | Beaconing patterns, high periodicity connections |
| T1053.005 | Scheduled Tasks | New tasks pointing to unusual locations |

---

## Step 3: Windows Event IDs for Hunting

| Event ID | Description | Hunt Value |
|---------|-----------|-----------|
| 4624 | Successful logon | Lateral movement, after-hours access |
| 4625 | Failed logon | Brute force, password spray |
| 4648 | Logon with explicit credentials | Pass-the-hash, pass-the-ticket |
| 4688 | New process created (+ cmdline with Sysmon) | Suspicious processes, execution |
| 4697 | Service installed | Persistence mechanisms |
| 4698 | Scheduled task created | Persistence |
| 4719 | System audit policy changed | Defence evasion |
| 4720 | User account created | Backdoor accounts |
| 4732 | Member added to security-enabled group | Privilege escalation |
| 7045 | New service installed | Persistence, malware installation |

> 💡 **Enable Sysmon** — it adds critical fields to Event 4688 (full command line, parent process, hash). Without Sysmon, Windows process auditing is severely limited.

---

## Step 4: Lateral Movement Detector

```python
from collections import defaultdict

logs = [
    {'ts': '08:01', 'eid': 4624, 'user': 'svc_backup', 'src': '10.1.1.10', 'dst': '10.1.1.20', 'type': 'Network'},
    {'ts': '08:02', 'eid': 4624, 'user': 'svc_backup', 'src': '10.1.1.10', 'dst': '10.1.1.30', 'type': 'Network'},
    {'ts': '08:03', 'eid': 4624, 'user': 'svc_backup', 'src': '10.1.1.10', 'dst': '10.1.1.40', 'type': 'Network'},
    {'ts': '08:04', 'eid': 4624, 'user': 'svc_backup', 'src': '10.1.1.10', 'dst': '10.1.1.50', 'type': 'Network'},
    {'ts': '08:05', 'eid': 4624, 'user': 'svc_backup', 'src': '10.1.1.10', 'dst': '10.1.1.60', 'type': 'Network'},
    {'ts': '08:10', 'eid': 4688, 'user': 'admin',      'src': '10.1.1.20', 'dst': None, 'proc': 'mimikatz.exe'},
    {'ts': '08:12', 'eid': 4648, 'user': 'admin',      'src': '10.1.1.20', 'dst': '10.1.1.5',  'type': 'Explicit'},
    {'ts': '08:15', 'eid': 4624, 'user': 'bob',         'src': '192.168.1.5', 'dst': '10.1.1.20', 'type': 'Interactive'},
]

print('=== Threat Hunting: Lateral Movement Detector ===')

# Hunt 1: Horizontal login spread (>3 unique destinations)
user_dsts = defaultdict(set)
for e in logs:
    if e['eid'] == 4624 and e.get('dst'):
        user_dsts[e['user']].add(e['dst'])

print('\nHunt 1: Horizontal Login Spread (T1021)')
for user, dsts in user_dsts.items():
    if len(dsts) >= 3:
        print(f'  [ALERT] {user} logged into {len(dsts)} hosts: {sorted(dsts)}')
        print(f'          MITRE: T1021.002 (SMB/WinRM), T1078 (Valid Accounts)')

# Hunt 2: Credential dumping process
print('\nHunt 2: Credential Dumping Process (T1003)')
for e in logs:
    if e['eid'] == 4688:
        proc = e.get('proc', '')
        if any(t in proc.lower() for t in ['mimikatz', 'procdump', 'lsass']):
            print(f'  [ALERT] Suspicious process: {proc} by {e["user"]} at {e["ts"]}')
            print(f'          MITRE: T1003.001 (LSASS Memory)')

# Hunt 3: External-to-internal
print('\nHunt 3: External Source Login (T1133)')
for e in logs:
    if e['eid'] == 4624 and e.get('src', '').startswith('192.168'):
        print(f'  [ALERT] External src {e["src"]} authenticated to internal host at {e["ts"]}')
        print(f'          MITRE: T1133 (External Remote Services)')
```

📸 **Verified Output:**
```
=== Threat Hunting: Lateral Movement Detector ===

Hunt 1: Horizontal Login Spread (T1021)
  [ALERT] svc_backup logged into 5 hosts: ['10.1.1.20', '10.1.1.30', '10.1.1.40', '10.1.1.50', '10.1.1.60']
          MITRE: T1021.002 (SMB/WinRM), T1078 (Valid Accounts)

Hunt 2: Credential Dumping Process (T1003)
  [ALERT] Suspicious process: mimikatz.exe by admin at 08:10
          MITRE: T1003.001 (LSASS Memory)

Hunt 3: External Source Login (T1133)
  [ALERT] External src 192.168.1.5 authenticated to internal host at 08:15
          MITRE: T1133 (External Remote Services)
```

---

## Step 5: TTP-Based Hunt — C2 Beaconing

**C2 beaconing characteristics:**
- Regular periodic connections (jitter ±10-30%)
- Small request, larger response pattern
- Uncommon destination (new domain, CDN abuse)
- Process making network connection: Office apps, notepad, non-browser

**Statistical approach:**
```python
import statistics

# Simulated connection intervals (seconds)
intervals = [295, 302, 298, 305, 301, 297, 303, 299, 304, 298]
mean_interval = statistics.mean(intervals)
std_dev = statistics.stdev(intervals)
jitter = std_dev / mean_interval * 100

print(f'Mean interval: {mean_interval:.1f}s')
print(f'Std dev: {std_dev:.1f}s')
print(f'Jitter: {jitter:.1f}%')
print(f'Verdict: {"BEACON SUSPECTED" if jitter < 15 else "Normal traffic"}')
# Output:
# Mean interval: 300.2s
# Std dev: 3.2s
# Jitter: 1.1%
# Verdict: BEACON SUSPECTED
```

---

## Step 6: Persistence Hunt — Scheduled Tasks

**Hunt: new scheduled tasks pointing to suspicious locations**

```
Elastic query:
  event.code: "4698" AND NOT
  winlog.event_data.TaskContentXml: "*\\Windows\\*"

Suspicious paths:
  %APPDATA%, %TEMP%, %PUBLIC%, %PROGRAMDATA%
  UNC paths (\\server\share\)
  Base64 encoded commands
  Downloads from internet (Invoke-WebRequest, curl)
```

**Registry run key persistence:**
```
Hunt: New values in Run keys
Paths:
  HKLM\Software\Microsoft\Windows\CurrentVersion\Run
  HKCU\Software\Microsoft\Windows\CurrentVersion\Run
  HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon

Sysmon Event 13: RegistryValueSet
Filter: TargetObject contains "Run" AND Image NOT IN trusted_apps
```

---

## Step 7: Hunting Cycle and Documentation

**2-week hunt sprint:**
```
Week 1:
  Day 1-2: Hypothesis development + data prep
  Day 3-4: Initial data collection + basic analysis
  Day 5:   Anomaly identification + pivoting

Week 2:
  Day 1-2: Deep investigation of anomalies
  Day 3:   Correlation with threat intel
  Day 4:   Detection rule creation
  Day 5:   Hunt report + findings brief
```

**Hunt report template:**
```
Hunt ID:    HT-2024-007
Hypothesis: Lateral movement via service accounts
Data sources used: Security event logs (4624, 4648), Sysmon
Period:     2024-01-08 to 2024-01-22
Analyst:    hunter@corp.com

Findings:
  - 3 service accounts showing horizontal login spread
  - 1 instance of mimikatz.exe detected (already contained)
  - 2 new scheduled tasks pointing to %TEMP%

Detections created:
  - SIEM rule: service_account_horizontal_spread
  - SIEM rule: suspicious_scheduled_task_location

Recommendations:
  - Disable svc_backup network logon rights
  - Implement PAM for service accounts
  - Enable PowerShell ScriptBlock logging
```

---

## Step 8: Capstone — Threat Hunting Programme

**Scenario:** Build a threat hunting function for an energy sector SOC

```
Hunting Programme Design:

Team:
  - 2 dedicated threat hunters (L3)
  - Part-time: 1 threat intelligence analyst
  - Tools: Elastic SIEM, Velociraptor, osquery, MISP

Data Sources:
  - Windows: Sysmon + Security logs (all servers)
  - Network: Zeek + Suricata (core switches)
  - Cloud: CloudTrail + VPC Flow Logs
  - Identity: AD audit logs + privileged session logs
  - OT: Purdue model logs (where available)

Hunt Calendar (quarterly rotation):
  Q1: Lateral movement + credential access
  Q2: Persistence + defence evasion
  Q3: C2 + exfiltration
  Q4: Cloud-specific hunts + supply chain

ATT&CK Coverage Tracking:
  - Target: Hunt coverage for 50% of ATT&CK Enterprise
  - Current: 35% coverage (mapped in ATT&CK Navigator)
  - Priority: ICS/OT techniques (ATT&CK for ICS)

Threat Intel Integration:
  - FS-ISAC feeds for energy sector TTPs
  - CISA alerts ingested within 24 hours
  - MISP: share hunt findings as indicators

Metrics:
  - Hunts completed per quarter: 4+
  - Threats discovered per hunt: track over time
  - Detection rules created per hunt: 2+
  - Mean time threat was resident before discovery
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| PEAK Framework | Prepare → Execute → Act on Knowledge |
| Hypothesis | "Threat actor using [TTP] may be [doing X] based on [signal]" |
| Key Event IDs | 4624 (logon), 4688 (process), 4648 (explicit creds), 4698 (sched task) |
| Lateral movement | Horizontal login spread >3 hosts, admin share access |
| C2 detection | Statistical beaconing (low jitter = automated = beacon) |
| Sysmon | Essential: full command line, hashes, network connections |
| Hunt output | Detections + recommendations + threat intel updates |
