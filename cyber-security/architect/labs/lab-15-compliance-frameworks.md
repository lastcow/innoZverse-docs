# Lab 15: Compliance Frameworks

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Understand ISO 27001, SOC 2 Type II, NIST CSF 2.0, PCI DSS v4.0, CIS Controls v8
- Map controls across frameworks to identify overlap
- Conduct a compliance gap analysis
- Build a Python compliance gap analyser

---

## Step 1: Framework Overview

| Framework | Publisher | Scope | Audience |
|-----------|---------|-------|---------|
| ISO 27001:2022 | ISO/IEC | ISMS; risk-based | Global enterprises |
| SOC 2 Type II | AICPA | Cloud/SaaS service providers | US services |
| NIST CSF 2.0 | NIST | Cybersecurity risk management | US critical infra |
| PCI DSS v4.0 | PCI SSC | Payment card data | Cardholder data handling |
| CIS Controls v8 | CIS | Prioritised security actions | All organisations |

---

## Step 2: ISO 27001:2022 — ISMS Controls

**ISO 27001 Annex A control domains (2022 version):**

| Clause | Domain | Controls |
|--------|--------|---------|
| A.5 | Organisational controls | 37 controls (policies, supply chain, IR) |
| A.6 | People controls | 8 controls (screening, training, remote work) |
| A.7 | Physical controls | 14 controls (physical security, clean desk) |
| A.8 | Technological controls | 34 controls (access, crypto, secure development) |

**New controls in 2022 version:**
- A.5.7: Threat intelligence
- A.5.23: Cloud services security
- A.8.8: Management of technical vulnerabilities
- A.8.16: Monitoring activities
- A.8.28: Secure coding

**ISMS lifecycle (PDCA cycle):**
```
PLAN:  Risk assessment → risk treatment → ISMS documentation
DO:    Implement controls → train staff → operate processes
CHECK: Internal audit → management review → monitor KPIs
ACT:   Corrective actions → continual improvement
```

---

## Step 3: SOC 2 Type II — Trust Services Criteria

**Five Trust Services Categories:**

| Category | Abbreviation | Key Focus |
|---------|-------------|----------|
| Security | CC (Common Criteria) | Logical/physical access, monitoring |
| Availability | A | System availability per SLAs |
| Processing Integrity | PI | Complete, accurate, timely processing |
| Confidentiality | C | Protect confidential information |
| Privacy | P | Personal information collection/use |

**Critical Common Criteria:**

| Criteria | Description |
|---------|-----------|
| CC6.1 | Logical access controls (authentication, MFA) |
| CC6.2 | Access provisioning/deprovisioning |
| CC6.3 | Role-based access; minimum necessary |
| CC7.1 | Vulnerability management |
| CC7.2 | Intrusion detection/monitoring |
| CC7.3 | Incident response procedures |
| CC8.1 | Change management |
| CC9.2 | Vendor risk management |

**Type I vs Type II:**
- **Type I**: Point-in-time — controls exist and are suitably designed
- **Type II**: Period of time (min 6 months) — controls operated effectively

---

## Step 4: NIST CSF 2.0 Functions

**Six functions (CSF 2.0 added "Govern"):**

```
GOVERN  → Policies, risk strategy, supply chain, oversight
IDENTIFY → Asset management, risk assessment, threat intel
PROTECT  → Access control, training, data security, platform security
DETECT   → Continuous monitoring, anomaly detection, SIEM
RESPOND  → IR planning, communications, mitigation
RECOVER  → Recovery planning, improvements, communications
```

**NIST CSF 2.0 Tiers:**
- **Tier 1 – Partial**: Ad-hoc, risk not formalised
- **Tier 2 – Risk Informed**: Risk aware but not organisation-wide
- **Tier 3 – Repeatable**: Organisation-wide, formal policies
- **Tier 4 – Adaptive**: Adaptive, lessons learned, threat-informed

---

## Step 5: PCI DSS v4.0 Requirements

**12 PCI DSS Requirements:**

| Req | Title |
|-----|-------|
| 1 | Install and maintain network security controls |
| 2 | Apply secure configurations to all system components |
| 3 | Protect stored account data |
| 4 | Protect cardholder data in transit with strong cryptography |
| 5 | Protect all systems and networks from malicious software |
| 6 | Develop and maintain secure systems and software |
| 7 | Restrict access to system components by business need-to-know |
| 8 | Identify users and authenticate access to system components |
| 9 | Restrict physical access to cardholder data |
| 10 | Log and monitor all access to system components |
| 11 | Test security of systems and networks regularly |
| 12 | Support information security with organisational policies |

**Key PCI DSS v4.0 changes:**
- Requirement 6.3.3: All software protected from known vulnerabilities
- Requirement 8.4.2: MFA required for ALL access into CDE (not just remote)
- Requirement 11.6.1: Detect unauthorised changes to payment pages
- Customised approach: flexibility to meet intent rather than prescribed method

---

## Step 6: Compliance Gap Analyser

```python
controls = {
    'Access Control':       {'ISO27001': 'A.9',    'SOC2': 'CC6.1', 'NIST_CSF': 'PR.AC', 'PCI_DSS': 'Req.7',  'CIS': 'CIS-5'},
    'Encryption':           {'ISO27001': 'A.10',   'SOC2': 'CC6.7', 'NIST_CSF': 'PR.DS', 'PCI_DSS': 'Req.3',  'CIS': 'CIS-3'},
    'Incident Response':    {'ISO27001': 'A.16',   'SOC2': 'CC7.3', 'NIST_CSF': 'RS.RP', 'PCI_DSS': 'Req.12', 'CIS': 'CIS-17'},
    'Vulnerability Mgmt':   {'ISO27001': 'A.12.6', 'SOC2': 'CC7.1', 'NIST_CSF': 'ID.RA', 'PCI_DSS': 'Req.6',  'CIS': 'CIS-7'},
    'Logging & Monitoring': {'ISO27001': 'A.12.4', 'SOC2': 'CC7.2', 'NIST_CSF': 'DE.CM', 'PCI_DSS': 'Req.10', 'CIS': 'CIS-8'},
}
implemented = {
    'Access Control': True, 'Encryption': True,
    'Incident Response': False, 'Vulnerability Mgmt': True, 'Logging & Monitoring': False
}
frameworks = ['ISO27001', 'SOC2', 'NIST_CSF', 'PCI_DSS', 'CIS']
print('=== Compliance Gap Analyser ===')
print(f'  {"Control":<22} {"Status":<8}', ' '.join(f'{f:<10}' for f in frameworks))
gaps = 0
for ctrl, mapping in controls.items():
    status = 'IMPL' if implemented.get(ctrl) else 'GAP'
    if status == 'GAP': gaps += 1
    refs = ' '.join(f'{mapping[f]:<10}' for f in frameworks)
    print(f'  {ctrl:<22} [{status}]   {refs}')
total = len(controls) * len(frameworks)
covered = (len(controls) - gaps) * len(frameworks)
print(f'  Coverage: {covered}/{total} control-framework mappings ({covered/total*100:.0f}%)')
print(f'  Gaps identified: {gaps} controls need remediation')
```

📸 **Verified Output:**
```
=== Compliance Gap Analyser ===
  Control                Status   ISO27001   SOC2       NIST_CSF   PCI_DSS    CIS
  Access Control         [IMPL]   A.9        CC6.1      PR.AC      Req.7      CIS-5
  Encryption             [IMPL]   A.10       CC6.7      PR.DS      Req.3      CIS-3
  Incident Response      [GAP]   A.16       CC7.3      RS.RP      Req.12     CIS-17
  Vulnerability Mgmt     [IMPL]   A.12.6     CC7.1      ID.RA      Req.6      CIS-7
  Logging & Monitoring   [GAP]   A.12.4     CC7.2      DE.CM      Req.10     CIS-8
  Coverage: 15/25 control-framework mappings (60%)
  Gaps identified: 2 controls need remediation
```

---

## Step 7: CIS Controls v8

**18 CIS Controls with Implementation Groups:**

| CIS | Control | IG1 | IG2 | IG3 |
|-----|---------|-----|-----|-----|
| 1 | Inventory of Enterprise Assets | ✅ | ✅ | ✅ |
| 2 | Inventory of Software Assets | ✅ | ✅ | ✅ |
| 3 | Data Protection | ✅ | ✅ | ✅ |
| 4 | Secure Configuration | ✅ | ✅ | ✅ |
| 5 | Account Management | ✅ | ✅ | ✅ |
| 6 | Access Control Management | ✅ | ✅ | ✅ |
| 7 | Continuous Vulnerability Management | | ✅ | ✅ |
| 8 | Audit Log Management | | ✅ | ✅ |
| 9 | Email and Web Browser Protections | ✅ | ✅ | ✅ |
| 10 | Malware Defences | ✅ | ✅ | ✅ |
| 11 | Data Recovery | ✅ | ✅ | ✅ |
| 12 | Network Infrastructure Management | | ✅ | ✅ |
| 13 | Network Monitoring and Defence | | ✅ | ✅ |
| 14 | Security Awareness & Skills Training | ✅ | ✅ | ✅ |
| 17 | Incident Response Management | | ✅ | ✅ |
| 18 | Penetration Testing | | | ✅ |

**IG1** = essential cyber hygiene (all organisations)  
**IG2** = for organisations handling sensitive data  
**IG3** = advanced organisations, full security programme

---

## Step 8: Capstone — Multi-Framework Compliance Programme

**Scenario:** FinTech startup needing ISO 27001, SOC 2 Type II, and PCI DSS simultaneously

```
Compliance Strategy: Integrated control framework

Approach:
  - Map all three frameworks to a unified control set
  - Implement once; satisfy multiple frameworks
  - Shared evidence repository (trust but verify)

Year 1 Timeline:
  Q1: Gap assessment + risk assessment
      - ISO 27001: scope definition + risk register
      - SOC 2: system description + criteria mapping
      - PCI DSS: CDE scoping + SAQ/QSA engagement

  Q2: Control implementation
      - Priority: Access control + encryption + logging
      - These three controls satisfy 60%+ of all three frameworks
      - Key: MFA, RBAC, full-disk encryption, SIEM deployment

  Q3: Evidence collection + testing
      - Internal audit against all three frameworks
      - Penetration test (required: PCI Req.11, SOC2 CC, ISO A.12.6)
      - Vulnerability management programme running

  Q4: Certification/attestation
      - ISO 27001: Certification audit (Stage 1 + Stage 2)
      - SOC 2: Type I attestation (audit period begins)
      - PCI DSS: SAQ-D or QSA ROC submission

Year 2: SOC 2 Type II period completes (6-12 months audit period)

Unified control matrix:
  - 85 unique controls satisfying all three frameworks
  - Without integration: 200+ controls
  - Efficiency gain: 57% reduction in compliance overhead

Budget estimate:
  - GRC platform (Vanta/Drata): USD 50K/year
  - QSA for PCI DSS: USD 40K/year
  - ISO 27001 certification: USD 25K
  - SOC 2 Type II audit: USD 30K
  - Internal GRC team: 1 FTE (USD 120K)
  Total: ~USD 265K Year 1
```

---

## Summary

| Framework | Key Feature | Certification |
|-----------|-----------|--------------|
| ISO 27001 | Risk-based ISMS; 93 Annex A controls | Third-party cert body |
| SOC 2 Type II | Trust Services Criteria; operating effectiveness | CPA firm attestation |
| NIST CSF 2.0 | 6 functions; tiered maturity; voluntary | Self-assessed |
| PCI DSS v4.0 | 12 requirements; MFA for all CDE access | QSA / SAQ |
| CIS Controls v8 | 18 controls; IG1/2/3 implementation groups | Self-assessed |
| Cross-mapping | Integrate frameworks to avoid control duplication | Unified programme |
