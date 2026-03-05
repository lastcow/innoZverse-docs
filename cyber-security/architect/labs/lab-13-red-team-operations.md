# Lab 13: Red Team Operations

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design red team rules of engagement and operational scope
- Apply threat modelling (STRIDE/PASTA/attack trees)
- Map attack paths using MITRE ATT&CK and Dijkstra's algorithm
- Understand C2 architecture and purple team methodology

---

## Step 1: Red Team vs Penetration Testing

| Aspect | Penetration Test | Red Team |
|--------|----------------|---------|
| Goal | Find vulnerabilities | Test detection & response capability |
| Duration | Days-weeks | Weeks-months |
| Scope | Defined scope (systems/apps) | Goal-based (e.g., "exfil crown jewels") |
| Stealth | Not required | Required (emulate real adversary) |
| Notification | IT team often notified | Only exec/legal/HR ("white team") |
| Deliverable | Vulnerability list | Detection gap report + attack narrative |
| Audience | Technical (IT/Security) | Executive + SOC |

---

## Step 2: Rules of Engagement

**ROE document must include:**

```
RED TEAM ENGAGEMENT — RULES OF ENGAGEMENT

Authorisation:
  - Signed by: CISO + CEO
  - Scope: [Company name] production environment
  - Duration: 2024-02-01 to 2024-04-30

Authorised activities:
  - Physical access: Building A only
  - Network: 10.0.0.0/8 (corporate), *.corp.com
  - Social engineering: phishing only (no vishing/impersonation)
  - Credentials: discovered/obtained only (no pre-supplied creds)

PROHIBITED:
  - Any systems processing real payment card data
  - Production databases containing PHI
  - DoS/DDoS attacks
  - Data destruction or modification
  - Third-party infrastructure

Emergency stop:
  - Red team leader contacts: [CISO phone]
  - All activity halts within 5 minutes
  - Evidence preserved, systems restored

Evidence handling:
  - All captured data: encrypted, deleted within 30 days post-report
  - Chain of custody for any credentials found
```

---

## Step 3: Threat Modelling — STRIDE

**STRIDE threat categories:**

| Threat | Description | Control |
|--------|-----------|---------|
| **S**poofing | Claiming false identity | Authentication (MFA) |
| **T**ampering | Modifying data/code | Integrity checks, digital signatures |
| **R**epudiation | Denying actions | Audit logging, non-repudiation |
| **I**nformation Disclosure | Unauthorised data access | Encryption, access control |
| **D**enial of Service | Disrupting availability | Rate limiting, redundancy |
| **E**levation of Privilege | Gaining higher rights | Least privilege, RBAC |

**STRIDE applied to a web application login:**
```
1. Login form:
   S: Fake login page (credential phishing)
   T: Modify POST data (parameter tampering)
   I: Password in plaintext (network sniff)
   D: Login flood (brute force, lock accounts)
   E: SQL injection → admin bypass

2. Session token:
   S: Token prediction/theft (session hijacking)
   T: Token manipulation (JWT alg=none)
   R: Action without attribution (anonymous token)
   I: Token in URL (logs, referer header)
```

---

## Step 4: PASTA Threat Modelling

**PASTA (Process for Attack Simulation and Threat Analysis) — 7 stages:**

```
Stage 1: Define Objectives
  Business: Protect customer PII; ensure payment availability
  Security: Data confidentiality, system integrity, SOC detection

Stage 2: Define Technical Scope
  Components: Web app, API, database, payment gateway

Stage 3: Application Decomposition
  Data flow: Browser → CDN → WAF → App Server → DB → Payment API

Stage 4: Threat Analysis
  Threat actors: External attacker, insider, nation-state
  Applicable CVEs: Known vulns in tech stack

Stage 5: Vulnerability & Weakness Analysis
  SAST results, pentest history, dependency CVEs

Stage 6: Attack Modelling
  Attack trees for each threat actor
  Most likely attack path per actor

Stage 7: Risk & Impact Analysis
  Business impact per attack scenario
  Risk score = Likelihood × Impact
  Priority for remediation
```

---

## Step 5: Attack Path Graph — Dijkstra

```python
import heapq

# ATT&CK techniques as nodes, edges = (from, to, cost, technique)
graph = {
    'Initial Access':     [('Execution', 2, 'T1566-Phishing'), ('Valid Accounts', 3, 'T1078')],
    'Execution':          [('Persistence', 2, 'T1059-PowerShell'), ('Privilege Escalation', 4, 'T1055')],
    'Valid Accounts':     [('Lateral Movement', 2, 'T1021-RDP'), ('Persistence', 1, 'T1098')],
    'Persistence':        [('Defense Evasion', 2, 'T1036-Masquerading')],
    'Privilege Escalation': [('Credential Access', 1, 'T1003-Mimikatz')],
    'Credential Access':  [('Lateral Movement', 1, 'T1550-PTH')],
    'Defense Evasion':    [('Discovery', 1, 'T1083-File-Discovery')],
    'Lateral Movement':   [('Collection', 2, 'T1039'), ('Impact', 5, 'T1486-Ransomware')],
    'Discovery':          [('Collection', 1, 'T1005-LocalData')],
    'Collection':         [('Exfiltration', 2, 'T1041-C2'), ('Impact', 3, 'T1486-Ransomware')],
    'Exfiltration':       [('Impact', 1, 'T1567-Web')],
    'Impact':             []
}

def dijkstra(graph, start, end):
    dist = {n: float('inf') for n in graph}
    dist[start] = 0
    prev = {}
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w, tech in graph.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = (u, tech)
                heapq.heappush(pq, (nd, v))
    path = []
    node = end
    while node in prev:
        node, tech = prev[node]
        path.insert(0, (node, tech))
    path.append((end, ''))
    return dist[end], path

cost, path = dijkstra(graph, 'Initial Access', 'Impact')
print('=== Attack Path Graph (Dijkstra Shortest Path) ===')
print(f'Shortest attack path cost: {cost}')
print('Path:')
for i, (node, tech) in enumerate(path):
    prefix = '->' if i > 0 else 'START'
    tech_str = f' [{tech}]' if tech else ''
    print(f'  {prefix} {node}{tech_str}')
print()
print('MITRE Kill Chain: Recon -> Resource Dev -> Initial Access -> Execution -> Persistence')
print('                  -> Priv Esc -> Defense Evasion -> Credential Access -> Lateral Movement')
print('                  -> Collection -> Exfiltration -> Impact')
```

📸 **Verified Output:**
```
=== Attack Path Graph (Dijkstra Shortest Path) ===
Shortest attack path cost: 10
Path:
  START Initial Access [T1078]
  -> Valid Accounts [T1021-RDP]
  -> Lateral Movement [T1486-Ransomware]
  -> Impact

MITRE Kill Chain: Recon -> Resource Dev -> Initial Access -> Execution -> Persistence
                  -> Priv Esc -> Defense Evasion -> Credential Access -> Lateral Movement
                  -> Collection -> Exfiltration -> Impact
```

---

## Step 6: C2 Framework Architecture (Concepts)

**C2 (Command & Control) components:**
```
Implant (on target)
  ↕ encrypted HTTPS/DNS/ICMP
Redirector (cloud VPS)
  ↕ authenticated channel
Team Server (red team infra)
  ↕
Operator console (Cobalt Strike, Sliver, Havoc)
```

**Operational security (OPSEC) for red teams:**
- Use domain fronting or CDN fronting for C2 traffic
- Rotate infrastructure; never reuse burned infrastructure
- HTTPS with valid certificate (Let's Encrypt on redirector)
- C2 profile mimics legitimate software (e.g., Microsoft Teams traffic)
- Kill switch: implant removes itself if specific conditions met

**Blue team detection of C2:**
- Beaconing analysis (regular periodic connections)
- JA3/JA3S TLS fingerprinting
- Domain age and reputation
- Certificate Subject/Issuer anomalies
- Unusual process making outbound connections

> ⚠️ **Legal note**: C2 infrastructure and offensive tooling are for authorised red team engagements only. All activities require written authorisation.

---

## Step 7: Purple Team Methodology

**Purple team vs Red team:**
- **Red team**: covert, adversarial, tests detection without telling defenders
- **Purple team**: collaborative, adversary simulation with blue team present
- **Purpose**: accelerate detection rule development; immediate feedback loop

**Purple team exercise format:**
```
1. Pre-exercise (1 week before):
   - Select 5-10 ATT&CK techniques based on threat intel
   - Confirm log sources available for each technique
   - Define detection success criteria

2. Exercise day:
   For each technique:
     a. Red executes technique (documented)
     b. Blue checks: did SIEM alert? (within 5 min)
     c. Result: Detected / Detected-late / Missed
     d. If missed: create detection rule on the spot
     e. Re-execute to validate new detection

3. Post-exercise:
   - Detection coverage improvement report
   - ATT&CK Navigator heatmap update
   - Detection rules committed to SIEM
   - Recommendations for log source gaps
```

---

## Step 8: Capstone — Red Team Report Structure

**Professional red team report structure:**

```
Executive Summary (1-2 pages):
  - Engagement objectives and duration
  - Critical findings (non-technical language)
  - Business risk of each finding
  - Top 5 recommendations

Attack Narrative:
  - Day-by-day timeline of attack path
  - Initial access method and success rate
  - Lateral movement path (with host names)
  - Objectives achieved: [list]
  - Objectives NOT achieved: [list with why]

Technical Findings (by kill chain phase):
  Recon:
    - Finding: LinkedIn enumeration exposed 3 admin accounts
    - Impact: Targeted phishing for credential theft
    - Evidence: Screenshots, tool output
    - Recommendation: LinkedIn visibility policy

  Initial Access:
    - Finding: Phishing success rate: 12/50 (24%)
    - Finding: MFA bypass via SIM swap (2 accounts)
    - Impact: Initial foothold achieved in 4 hours

  [Continue for each phase...]

Detection Coverage Analysis:
  - % of techniques detected by SOC
  - Time to detection per technique
  - False negatives by category
  - ATT&CK heatmap: red (not detected) / green (detected)

Remediation Roadmap:
  - Priority 1 (immediate, < 30 days): [list]
  - Priority 2 (short-term, < 90 days): [list]
  - Priority 3 (strategic, < 1 year): [list]
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Red team vs pentest | Red team = detection test; pentest = vulnerability finding |
| ROE | Written, signed authorisation; explicit prohibitions |
| STRIDE | 6 threat categories: Spoofing, Tampering, Repudiation, Info Disclosure, DoS, EoP |
| PASTA | 7-stage risk-centric threat modelling |
| Attack graph | Dijkstra finds shortest (lowest-cost) attack path |
| C2 | Implant ↔ Redirector ↔ Team Server; OPSEC critical |
| Purple team | Collaborative; accelerates detection development |
