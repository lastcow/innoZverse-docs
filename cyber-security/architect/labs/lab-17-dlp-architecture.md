# Lab 17: DLP Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design a Data Loss Prevention (DLP) architecture
- Define data classification tiers
- Implement endpoint, network, and cloud DLP policies
- Build a Python PII/PAN/SSN/PHI content classifier

---

## Step 1: Data Classification Framework

**Four-tier classification model:**

| Tier | Label | Description | Examples |
|------|-------|-------------|---------|
| 1 | Public | Approved for public release | Press releases, public website |
| 2 | Internal | Internal use only | Policies, org charts, project docs |
| 3 | Confidential | Restricted; business sensitive | Financial data, strategy docs, contracts |
| 4 | Restricted | Highly sensitive; regulatory | PII, PAN, PHI, source code, credentials |

**Data sensitivity indicators:**
```
PII (Personally Identifiable Information):
  - Name + address combination
  - SSN, passport, national ID
  - Email address (alone or combined)
  - IP address (in some jurisdictions)

PAN (Primary Account Number):
  - Credit/debit card numbers
  - BAN (bank account numbers)

PHI (Protected Health Information):
  - Medical record numbers
  - Health diagnosis + patient identity
  - Insurance member IDs

IP (Intellectual Property):
  - Source code
  - Trade secrets
  - Patents, research data
```

---

## Step 2: DLP Content Classifier

```python
import re

patterns = {
    'SSN':         r'\b\d{3}-\d{2}-\d{4}\b',
    'Credit_Card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
    'Email':       r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'IP_Address':  r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'PHI_DOB':     r'\b(?:DOB|Date of Birth|born)[\s:]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    'Passport':    r'\b[A-Z]{1,2}[0-9]{6,9}\b',
}
sensitivity = {'SSN':'CRITICAL','Credit_Card':'CRITICAL','PHI_DOB':'HIGH','Passport':'HIGH','Email':'MEDIUM','IP_Address':'LOW'}

test_docs = [
    ('HR_Record.txt',    'Employee John Doe SSN: 123-45-6789, DOB: 01/15/1985, Email: john@corp.com'),
    ('Payment_Log.txt',  'Card: 4532015112830366, Amount: USD 500'),
    ('Server_Config.txt','Database host: 10.1.2.3, Port: 5432'),
    ('Clean_Doc.txt',    'Project roadmap for Q2 2024 deliverables and milestones'),
]

print('=== DLP Content Classifier ===')
for fname, content in test_docs:
    found = []
    for ptype, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found.append((ptype, sensitivity[ptype], matches[0]))
    classification = max((f[1] for f in found), key=lambda x: ['LOW','MEDIUM','HIGH','CRITICAL'].index(x), default='PUBLIC')
    print(f'  [{classification:<8}] {fname}')
    for ptype, sens, val in found:
        masked = val[:4] + '*'*(len(val)-8) + val[-4:] if len(val) > 8 else '****'
        print(f'           {sens}: {ptype} detected -> {masked}')
    if not found:
        print(f'           No sensitive data detected')
```

📸 **Verified Output:**
```
=== DLP Content Classifier ===
  [CRITICAL] HR_Record.txt
           CRITICAL: SSN detected -> 123-***6789
           MEDIUM: Email detected -> john*****.com
           HIGH: PHI_DOB detected -> DOB:*******1985
  [CRITICAL] Payment_Log.txt
           CRITICAL: Credit_Card detected -> 4532********0366
  [LOW     ] Server_Config.txt
           LOW: IP_Address detected -> ****
  [PUBLIC  ] Clean_Doc.txt
           No sensitive data detected
```

---

## Step 3: DLP Deployment Types

**Three deployment modes:**

**1. Endpoint DLP:**
- Agent on laptop/workstation
- Controls: copy to USB, print, email attachment, screenshot
- Can work offline (no network required)
- Examples: Forcepoint DLP, Symantec DLP, Microsoft Purview DLP

**2. Network DLP:**
- Inline (blocking) or out-of-band (monitoring)
- Inspects: email, web upload, FTP, cloud sync
- Requires SSL/TLS inspection for encrypted traffic
- Examples: Zscaler, McAfee Network DLP, Palo Alto WildFire

**3. Cloud DLP (CASB):**
- Scans data at rest in SaaS (SharePoint, Google Drive, Box)
- Controls sharing permissions, external sharing, public access
- API-based inspection of stored documents
- Examples: Microsoft Purview, Netskope, Skyhigh Security

```
User Action → Endpoint Agent (first check)
                    ↓ if allowed
              Network Proxy (second check, in transit)
                    ↓ if allowed
              Cloud CASB (third check, at rest in SaaS)
```

---

## Step 4: DLP Policy Design

**Policy structure:**
```
Policy: "Protect PAN data"
  Scope: All endpoints + email + web uploads
  Condition:
    Content contains: Credit card pattern (Luhn validated)
    AND NOT (destination IN approved_payment_systems)
  Action:
    Block: upload to non-approved sites
    Quarantine: email with attachment
    Alert: security team
    Notify: user ("This action was blocked by DLP")
    Log: forensic evidence (who, what, when, where)
```

**Policy exceptions:**
- Payment team → can send PAN to approved payment processors
- Finance → can share financial data to auditors (approved domain)
- Legal → can export data to legal hold systems

> 💡 **Start with monitoring mode** — never deploy DLP in block mode from day one. Run monitor-only for 30-60 days; tune false positives; then progressively enable blocking on highest-risk channels.

---

## Step 5: DLP for Regulated Data

**GDPR Article 25 — Data Protection by Design:**
- Privacy considerations built into systems from the start
- Data minimisation: collect only what's necessary
- Purpose limitation: use data only for stated purpose
- DLP is a technical measure for Article 25 compliance

**GDPR DLP requirements:**
```
Article 25 obligations:
  - Pseudonymisation of PII where possible
  - Data minimisation in processing
  - Prevent unauthorised access/transfer

DLP technical controls:
  - Block PII leaving EU to non-adequate countries
  - Monitor and alert on bulk PII exports
  - Enforce data retention: auto-delete after retention period
  - Right to erasure: identify PII location for DSAR fulfillment
```

**PCI DSS DLP:**
- Prevent PAN transmission outside CDE (Cardholder Data Environment)
- Monitor for PAN in unexpected locations (DLP scan of file shares)
- Truncate PAN in logs (mask all but last 4 digits)

---

## Step 6: Content Inspection Techniques

| Technique | Description | Use Case |
|---------|-----------|---------|
| Regex patterns | Match text patterns | SSN, PAN, email, passport |
| Exact data match (EDM) | Hash-based exact match of records | Employee HR database |
| Document fingerprinting | Hash-based match of document structure | Confidential templates |
| ML classification | Model-based content classification | Unstructured text |
| OCR | Extract text from images/PDFs | Scanned documents |
| Luhn algorithm | Validate credit card numbers mathematically | Reduce PAN false positives |

**Luhn algorithm (credit card validation):**
```python
def luhn_check(card_number):
    digits = [int(d) for d in str(card_number)]
    for i in range(len(digits)-2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0

print(luhn_check(4532015112830366))  # True (valid Visa)
print(luhn_check(1234567890123456))  # False (invalid)
```

---

## Step 7: Insider Threat and DLP

**Insider threat indicators in DLP logs:**
- Bulk download before resignation (UEBA + DLP correlation)
- After-hours uploads to personal cloud storage
- Repeated DLP policy violations
- Access to data outside normal job function

**UEBA + DLP integration:**
```
Risk score trigger:
  - User on HR departure list (risky employee)
  + DLP: uploaded 500+ files to Dropbox
  + UEBA: access to finance data outside normal pattern
  = HIGH RISK ALERT → trigger investigation workflow
```

---

## Step 8: Capstone — Enterprise DLP Programme

**Scenario:** Financial services firm; GDPR + PCI DSS; 5,000 employees

```
DLP Programme Architecture:

Data Discovery (first 30 days):
  - Scan: network shares, SharePoint, OneDrive, email archives
  - Tools: Microsoft Purview scanner
  - Goal: inventory all locations of PAN, PII, PHI

Classification rollout:
  - Week 1-4: Auto-classification for Office documents (Purview labels)
  - Week 4-8: User training + manual classification for sensitive docs
  - Week 8+: Enforce classification at creation (default label)

Endpoint DLP (weeks 1-12):
  - Deploy Microsoft Purview DLP on all Windows endpoints
  - Monitor mode: 30 days (tune false positives)
  - Block mode: USB copy of PAN (day 31 onwards)
  - Alert mode: email with CC/SSN attachment

Network DLP (weeks 4-16):
  - Zscaler for all internet traffic (proxy)
  - SSL inspection: all non-financial sites
  - Block: PAN upload to non-approved sites
  - Monitor: PII in email to external addresses

Cloud DLP (weeks 8-20):
  - Microsoft Purview: scan SharePoint/OneDrive
  - Block: external sharing of Restricted data
  - Monitor: sharing of Confidential data to non-org
  - Auto-quarantine: publicly accessible documents with PAN

Metrics:
  - DLP incidents per week (trending)
  - False positive rate: < 5% (target)
  - Blocked transfers: track by data type
  - Policy coverage: 100% endpoints within 90 days
  - GDPR Article 25: evidence for compliance review
```

---

## Summary

| Component | Key Points |
|---------|-----------|
| Data classification | Public → Internal → Confidential → Restricted |
| Content inspection | Regex, EDM, fingerprinting, ML, OCR |
| Endpoint DLP | Agent-based; controls USB, print, screenshot |
| Network DLP | Inline proxy; inspect email, web, FTP |
| Cloud DLP | CASB; scan SaaS at rest; control sharing |
| GDPR Article 25 | Privacy by design; DLP as technical safeguard |
| Luhn check | Validate PAN to reduce false positives |
