# Lab 19: Security Metrics & Risk Quantification

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Apply FAIR (Factor Analysis of Information Risk) model
- Build a Monte Carlo simulation for risk quantification
- Define and track security KPIs (MTTD/MTTR/patch compliance)
- Calculate security ROI and communicate risk in financial terms

---

## Step 1: FAIR Risk Model

**FAIR decomposition:**
```
Risk
├── Loss Event Frequency (LEF)
│   ├── Threat Event Frequency (TEF) — how often does the threat act?
│   └── Vulnerability (VULN) — likelihood threat succeeds if it acts
│       ├── Threat Capability (TCAP) — threat actor's skill level
│       └── Resistance Strength (RS) — strength of your controls
│
└── Loss Magnitude (LM)
    ├── Primary Loss — direct costs (response, recovery, notification)
    │   ├── Response costs
    │   ├── Replacement costs
    │   └── Competitive advantage loss
    └── Secondary Loss — indirect costs (fines, litigation, reputation)
        ├── Regulatory fines
        ├── Lawsuit settlements
        └── Customer churn revenue
```

**Annual Loss Exposure (ALE):**
```
ALE = LEF × LM
    = (TEF × VULN) × Loss Magnitude
```

---

## Step 2: FAIR Monte Carlo Simulation

```python
import random, statistics

random.seed(42)
SIMULATIONS = 1000

def pert_random(low, likely, high):
    """PERT distribution approximation using beta distribution"""
    alpha = 1 + 4 * (likely - low) / (high - low)
    beta  = 1 + 4 * (high - likely) / (high - low)
    r = random.betavariate(alpha, beta)
    return low + r * (high - low)

# Scenario: External data breach via phishing
results = []
for _ in range(SIMULATIONS):
    tef  = pert_random(1, 3, 12)           # threat events/year (1-12, likely=3)
    vuln = pert_random(0.1, 0.3, 0.6)      # vulnerability probability 10-60%
    lef  = tef * vuln                      # Loss Event Frequency
    lm   = pert_random(50000, 200000, 2000000)  # loss magnitude USD
    ale  = lef * lm                        # Annual Loss Exposure
    results.append(ale)

results.sort()
p10 = results[int(0.10 * SIMULATIONS)]
p50 = results[int(0.50 * SIMULATIONS)]
p90 = results[int(0.90 * SIMULATIONS)]
mean = statistics.mean(results)

print('=== FAIR Monte Carlo Risk Model ===')
print(f'Scenario  : External data breach')
print(f'Simulations: {SIMULATIONS}')
print(f'TEF range : 1-12 events/year (likely=3)')
print(f'VULN range: 10%-60% (likely=30%)')
print(f'LM range  : USD 50K-2M (likely=200K)')
print()
print('=== Annual Loss Exposure (ALE) Results ===')
print(f'  P10 (best case)   : USD {p10:>12,.0f}')
print(f'  P50 (median)      : USD {p50:>12,.0f}')
print(f'  P90 (worst case)  : USD {p90:>12,.0f}')
print(f'  Mean              : USD {mean:>12,.0f}')
print()
print('Security ROI: Control cost USD 150,000 | Risk reduction 60%')
print(f'  Risk reduced      : USD {p50*0.6:>12,.0f}')
print(f'  Net benefit       : USD {p50*0.6-150000:>12,.0f}')
```

📸 **Verified Output:**
```
=== FAIR Monte Carlo Risk Model ===
Scenario  : External data breach
Simulations: 1000
TEF range : 1-12 events/year (likely=3)
VULN range: 10%-60% (likely=30%)
LM range  : USD 50K-2M (likely=200K)

=== Annual Loss Exposure (ALE) Results ===
  P10 (best case)   : USD      126,280
  P50 (median)      : USD      423,509
  P90 (worst case)  : USD    1,379,118
  Mean              : USD      627,303

Security ROI: Control cost USD 150,000 | Risk reduction 60%
  Risk reduced      : USD      254,105
  Net benefit       : USD      104,105
```

---

## Step 3: FAIR — Multiple Scenario Comparison

**Compare scenarios to prioritise investment:**

| Scenario | ALE (P50) | Control Cost | Risk Reduction | ROI |
|---------|---------|-------------|--------------|-----|
| Data breach via phishing | USD 423K | USD 150K (MFA) | 70% | 97% |
| Ransomware attack | USD 1.2M | USD 200K (EDR) | 80% | 380% |
| Insider data theft | USD 180K | USD 100K (DLP) | 60% | 8% |
| DDoS attack | USD 50K | USD 30K (CDN) | 90% | 50% |

**Investment decision:**
- Rank by ROSI (Return on Security Investment)
- `ROSI = (Risk Reduced - Control Cost) / Control Cost × 100%`
- Prioritise controls with highest ROSI
- Present P10/P50/P90 range to board (not single point)

> 💡 **Why Monte Carlo?** — Single-point estimates create false precision. Ransomware could cost USD 500K or USD 50M depending on extent of encryption, data sensitivity, and regulatory exposure. Monte Carlo communicates this uncertainty honestly.

---

## Step 4: Security KPIs

**Operational KPIs:**

| KPI | Formula | Target | Measurement Cadence |
|-----|---------|--------|-------------------|
| MTTD | Time from incident start to detection | < 4 hours | Per incident |
| MTTR | Time from detection to containment | < 24 hours | Per incident |
| Patch compliance | % assets patched within SLA | > 95% | Weekly |
| Vulnerability density | Critical CVEs per 100 assets | < 5 | Monthly |
| Phishing click rate | % users clicking test phishes | < 5% | Quarterly |
| MFA adoption | % accounts with MFA enabled | > 99% | Monthly |
| Alert-to-case ratio | Cases opened / alerts received | 5-15% | Weekly |

**Strategic KPIs (board-level):**

| KPI | Description |
|-----|-----------|
| Cyber risk exposure (FAIR) | Financial risk in USD (P50 ALE) |
| Security maturity score | NIST CSF or CIS maturity level |
| Compliance posture | % controls implemented vs required |
| Security investment ratio | Security budget / total IT budget (target: 10-15%) |
| Cyber insurance coverage | Coverage adequate vs FAIR P90 scenario |

---

## Step 5: Security ROI Models

**Model 1: Risk Reduction Value**
```
Security Control: MFA deployment
  Before MFA: Phishing-to-breach rate = 35%
  After MFA:  Phishing-to-breach rate = 3%
  Reduction:  91% fewer successful phishing attacks

  Annual loss before: USD 500K (FAIR estimate)
  Risk reduction 91%: saves USD 455K
  MFA deployment cost: USD 100K (first year)
  ROSI = (455K - 100K) / 100K = 355%
```

**Model 2: Regulatory Penalty Avoidance**
```
Scenario: GDPR breach without encryption
  Potential fine: 4% global revenue (worst case)
  Company revenue: USD 100M
  Potential fine: USD 4M
  Probability of breach in 3 years: 30% (FAIR estimate)
  Expected loss: USD 1.2M

  Encryption deployment cost: USD 80K
  Risk reduced to 5% with encryption:
  New expected loss: USD 200K
  Savings: USD 1M
  ROSI = (1M - 80K) / 80K = 1,150%
```

---

## Step 6: Communicating Risk to the Board

**What boards care about:**
- Financial impact (dollar amounts, not CVSS scores)
- Regulatory risk (fines, regulatory action)
- Reputational risk (customer trust, share price)
- Business continuity (revenue impact of outage)
- Comparison to peers (are we better/worse than industry?)

**Board-ready risk summary:**
```
Cyber Risk Dashboard — Q1 2024

Top 3 Risks by ALE:
  1. Ransomware (USD 1.2M ALE | Controls: 82% effective)
  2. Data breach (USD 423K ALE | Controls: 74% effective)
  3. Insider threat (USD 180K ALE | Controls: 68% effective)

Investment request: USD 350K
  → EDR upgrade (ransomware risk -80%)
  → MFA for all staff (phishing risk -70%)
  → Expected ALE reduction: USD 1.1M
  → Net ROI: 214% over 3 years

Current posture:
  NIST CSF Tier: 3 (Repeatable) — targeting Tier 4 by Q4
  Compliance: ISO 27001 ✅ | PCI DSS ✅ | GDPR gap: 2 controls
  Incident response: MTTD 3.2h ✅ | MTTR 14h ✅
```

---

## Step 7: Security Budget Benchmarking

**Industry benchmarks:**
| Industry | Security/IT Budget % | Security/Revenue % |
|---------|--------------------|--------------------|
| Financial Services | 15-20% | 0.5-0.7% |
| Healthcare | 10-15% | 0.3-0.5% |
| Technology | 8-12% | 0.4-0.6% |
| Retail | 8-12% | 0.1-0.3% |
| Government | 10-15% | varies |

**Gartner benchmark:**
- Average: 11.6% of IT budget for security
- High performers: > 15%
- Minimum viable: 7-8%

---

## Step 8: Capstone — Risk Quantification for CISO Report

**Scenario:** Annual risk report for Fortune 500 financial services CISO

```
Executive Risk Summary — Annual FAIR Assessment

Methodology:
  - 12 risk scenarios modelled
  - 10,000 Monte Carlo simulations per scenario
  - Data sources: breach cost studies, company financials, incident history

Top 5 Risks (P50 ALE):

Rank  Scenario                  P50 ALE      P90 ALE       Controls
1     Ransomware attack          USD 3.2M     USD 24M       EDR, backups, IR plan
2     Third-party breach         USD 2.1M     USD 18M       TPRM, contract clauses
3     Phishing/BEC               USD 1.8M     USD 12M       MFA, email security
4     Cloud misconfiguration     USD 890K     USD 4.2M      CSPM, IaC scanning
5     Insider data theft         USD 450K     USD 2.1M      DLP, PAM, UEBA

Total residual risk (P50): USD 8.4M/year
Total residual risk (P90): USD 60.3M/year

Proposed investments (USD 2.8M):
  - EDR expansion: USD 800K → ransomware risk -75%
  - Zero Trust (MFA + ZPA): USD 1.2M → phishing/BEC risk -80%
  - TPRM programme: USD 400K → third-party risk -40%
  - CSPM expansion: USD 400K → cloud risk -60%

Expected outcomes:
  - Total ALE reduction: USD 6.2M
  - 3-year NPV: USD 15.8M
  - ROSI: 464%

Cyber insurance:
  - Current coverage: USD 10M
  - P90 scenario: USD 60.3M
  - Recommendation: increase to USD 25M coverage
  - Premium estimate: USD 450K/year (vs USD 60M uninsured tail)

KPI benchmarks vs last year:
  MTTD: 3.2h (↓ from 5.1h) ✅
  MTTR: 14h  (↓ from 22h)  ✅
  Patch compliance: 97% (↑ from 91%) ✅
  Phishing click: 4.2% (↓ from 8.1%) ✅
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| FAIR | LEF × LM = ALE; decomposes risk into measurable factors |
| Monte Carlo | 1000+ simulations; produces P10/P50/P90 range |
| PERT distribution | Low/likely/high → realistic distribution for estimates |
| ROSI | (Risk reduced - control cost) / control cost |
| KPIs | MTTD, MTTR, patch compliance, phishing rate, MFA adoption |
| Board communication | Dollar amounts + P50/P90 range + investment ROI |
| Benchmark | 10-15% IT budget for security; compare to peers |
