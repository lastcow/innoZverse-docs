# Lab 10: EU AI Act Compliance

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

The EU AI Act is the world's first comprehensive AI regulation, effective August 2024. This lab covers risk classification, high-risk AI requirements, GPAI obligations, conformity assessment, and comparison with NIST AI RMF — with a practical compliance checker.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    EU AI Act Risk Pyramid                    │
├──────────────────────────────────────────────────────────────┤
│  🔴 UNACCEPTABLE RISK - PROHIBITED                          │
│  Social scoring, real-time biometric surveillance (public), │
│  subliminal manipulation, emotion recognition (work/school)  │
├──────────────────────────────────────────────────────────────┤
│  🟠 HIGH RISK - REGULATED (Title III)                       │
│  Critical infrastructure, education, employment, credit,    │
│  law enforcement, migration, justice administration          │
├──────────────────────────────────────────────────────────────┤
│  🟡 LIMITED RISK - TRANSPARENCY OBLIGATIONS                 │
│  Chatbots (disclose AI), deepfakes (label), emotion AI      │
├──────────────────────────────────────────────────────────────┤
│  🟢 MINIMAL RISK - FREE USE                                 │
│  Spam filters, AI games, recommendation systems             │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Risk Tier Classification

**Unacceptable Risk (Article 5 - PROHIBITED):**

| System | Prohibition |
|--------|------------|
| Social scoring by governments | Mass surveillance, scoring citizens by social behavior |
| Real-time biometric ID in public | Facial recognition in public spaces (exceptions: terrorism, missing persons) |
| Subliminal manipulation | Bypass conscious decision-making to harm users |
| Exploiting vulnerabilities | Target vulnerable groups (age, disability) |
| Predictive policing | Assess crime risk based on profiling |
| Emotion recognition (work/schools) | Analyze emotions of employees or students |

**High-Risk (Annex III Categories):**

| Category | Examples |
|----------|---------|
| Critical infrastructure | AI in electricity grids, water systems, transport |
| Education | Student admission, assessment systems |
| Employment | CV screening, promotion decisions, work monitoring |
| Essential services | Credit scoring, insurance risk, social benefits |
| Law enforcement | Polygraphs, deepfake detection, crime prediction |
| Migration | Asylum decisions, visa applications |
| Justice | Court decisions, evidence evaluation |
| Biometric categorization | Categorize people by race, religion, political views |

> 💡 If your AI system directly influences a HIGH-RISK decision, you must comply with all Title III requirements. "Influencing" includes systems where output is not legally binding but practically determinative.

---

## Step 2: High-Risk AI Requirements (Title III)

Organizations deploying high-risk AI must implement:

**1. Risk Management System (Article 9):**
```
- Continuous risk identification and analysis
- Testing procedures for each foreseeable risk
- Residual risk evaluation after mitigation
- Documentation of risk management activities
- Annual review minimum
```

**2. Data Governance (Article 10):**
```
- Training data: relevant, representative, error-free
- Documented data collection and processing practices
- Bias detection and mitigation in training data
- Special category data: only when strictly necessary with safeguards
```

**3. Technical Documentation (Article 11):**
```
- System architecture and design choices
- Training methodology and data sources
- Performance metrics and test results
- Cybersecurity measures
- Environmental impact (energy consumption)
```

**4. Transparency (Article 13):**
```
- Clear instructions for use
- AI system identification (users know they're using AI)
- Capabilities and limitations disclosure
- Human oversight requirements
```

**5. Human Oversight (Article 14):**
```
- Technical capability for human overseers to intervene
- Understanding what system does and can't do
- Ability to disregard/override AI outputs
- Monitoring for anomalies
```

**6. Accuracy, Robustness, Cybersecurity (Article 15):**
```
- Appropriate accuracy levels for intended purpose
- Resilience to errors, faults, and inconsistencies
- Robustness to adversarial manipulation
- Redundancy/fail-safe mechanisms
```

---

## Step 3: GPAI (General Purpose AI) Obligations

GPAI models (GPT-4, Claude, Gemini, Llama 2/3) have specific obligations.

**Tier 1: All GPAI models:**
```
- Technical documentation (capabilities, limitations, training data)
- Copyright compliance for training data
- Summary of training data (even if confidential)
- EU AI Office compliance cooperation
```

**Tier 2: GPAI with Systemic Risk (>10^25 FLOPs training compute):**
```
Additional requirements:
- Adversarial testing (red-teaming)
- Incident reporting to EU AI Office
- Cybersecurity protection
- Energy efficiency reporting
```

**GPAI Threshold Context:**
```
GPT-4: ~10^25 FLOPs → Systemic risk tier
LLaMA-3-70B: ~10^23 FLOPs → Standard tier
Claude 3.5 Sonnet: Likely systemic risk tier
```

---

## Step 4: Conformity Assessment & CE Marking

High-risk AI must undergo conformity assessment before market placement.

**Assessment Paths:**

| System Type | Assessment Route |
|-------------|----------------|
| High-risk (most) | Internal assessment with documentation |
| Biometric ID systems | Third-party Notified Body assessment |
| Remote biometric (law enforcement) | Notified Body + national authority |
| GPAI systemic risk | EU AI Office oversight |

**CE Marking Process:**
```
1. Risk classification → high-risk determination
2. Technical documentation preparation
3. Conformity assessment (internal or third-party)
4. EU Declaration of Conformity
5. CE mark affixed to product
6. Register in EU database (Article 60)
7. Market surveillance compliance
```

**Registration Database:**
```
All high-risk AI systems must register in EU AI systems database:
- System name and version
- Provider details
- Intended purpose
- Countries of operation
- Status (in use, withdrawn, etc.)
```

---

## Step 5: NIST AI RMF Comparison

**NIST AI RMF (US, Voluntary) vs EU AI Act (EU, Mandatory):**

| Dimension | NIST AI RMF | EU AI Act |
|-----------|------------|-----------|
| **Nature** | Voluntary framework | Legal regulation |
| **Jurisdiction** | US (global influence) | EU (extraterritorial) |
| **Approach** | Risk-based, principles | Prescriptive requirements |
| **Core Functions** | GOVERN, MAP, MEASURE, MANAGE | Risk classification → requirements |
| **Enforcement** | Self-certification | Market surveillance, fines |
| **Fines** | None | Up to €35M or 7% global revenue |
| **Timeline** | Published 2023 | Effective Aug 2024 (phased) |

**NIST AI RMF Core Functions:**
```
GOVERN: Establish policies, culture, accountability
MAP: Categorize AI risks for specific contexts
MEASURE: Analyze and assess AI risks quantitatively
MANAGE: Prioritize and implement risk responses
```

**Key Alignment:**
```
Both emphasize: risk management, transparency, human oversight, documentation
EU AI Act adds: legal enforcement, CE marking, Notified Bodies, specific requirements
```

---

## Step 6: Implementation Timeline

**EU AI Act Phased Rollout:**

| Date | Milestone |
|------|-----------|
| Aug 2024 | Act enters into force |
| Feb 2025 | Prohibited practices take effect (Article 5) |
| Aug 2025 | GPAI obligations take effect |
| Aug 2026 | High-risk AI obligations (Annex III systems) |
| Aug 2027 | High-risk AI obligations (Annex II systems) |

**Compliance Roadmap for Enterprise:**
```
Now (2024-2025):
  → Inventory all AI systems
  → Classify by risk tier
  → Identify systems requiring compliance
  
2025:
  → Stop deploying prohibited systems
  → Begin high-risk documentation
  
2026:
  → Full high-risk compliance required
  → CE marking, registration, oversight mechanisms
```

---

## Step 7: AI Impact Assessment

Based on DPIA (Data Protection Impact Assessment) but for AI risks.

**AI Impact Assessment Template:**
```
1. System Description
   - Purpose, functionality, outputs
   - Who makes decisions? AI, human, combined?
   
2. Stakeholder Analysis
   - Who is affected? Any vulnerable groups?
   - What are the potential harms?
   
3. Risk Assessment
   - Probability × Impact for each risk
   - Fundamental rights impact
   
4. Mitigation Measures
   - Technical: explainability, human oversight
   - Organizational: training, policies
   
5. Residual Risk Sign-off
   - DPO approval
   - Legal counsel review
   - Business owner accountability
```

---

## Step 8: Capstone — Compliance Checker

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
class EUAIActChecker:
    def __init__(self, system_name):
        self.system_name = system_name
        self.scores = {}
    
    def check_risk_tier(self, use_case_category):
        unacceptable = ['social_scoring', 'subliminal_manipulation', 'real_time_biometric_public', 'emotion_recognition_workplace']
        high_risk = ['critical_infrastructure', 'education', 'employment', 'essential_services', 'law_enforcement', 'migration', 'justice', 'biometric_categorization']
        limited_risk = ['chatbot', 'deepfake', 'emotion_recognition_other']
        if use_case_category in unacceptable:
            return 'UNACCEPTABLE', 'System is PROHIBITED under EU AI Act'
        elif use_case_category in high_risk:
            return 'HIGH_RISK', 'Must comply with Title III requirements'
        elif use_case_category in limited_risk:
            return 'LIMITED_RISK', 'Transparency obligations apply'
        return 'MINIMAL_RISK', 'No specific obligations'
    
    def assess_high_risk_requirements(self, answers):
        requirements = {
            'risk_management_system': ('Has documented risk management system?', 3),
            'data_governance': ('Training data governance documented?', 3),
            'technical_documentation': ('Technical documentation complete?', 2),
            'record_keeping': ('Automatic logging enabled?', 2),
            'transparency': ('User transparency measures in place?', 3),
            'human_oversight': ('Human oversight mechanisms exist?', 3),
            'accuracy_robustness': ('Accuracy and robustness tested?', 3),
            'cybersecurity': ('Cybersecurity measures implemented?', 2),
        }
        total_score = 0
        max_score = sum(w for _, (_, w) in requirements.items())
        print(f'  High-Risk AI Requirements Assessment:')
        for req, (question, weight) in requirements.items():
            status = answers.get(req, False)
            score = weight if status else 0
            total_score += score
            icon = chr(10003) if status else chr(10007)
            print(f'    [{icon}] {question} (weight={weight})')
        pct = total_score / max_score * 100
        return total_score, max_score, pct

checker = EUAIActChecker('Enterprise Credit Scoring AI')
risk_tier, obligation = checker.check_risk_tier('employment')
print(f'=== EU AI Act Compliance Assessment ===')
print(f'System: {checker.system_name}')
print(f'Risk Tier: {risk_tier}')
print(f'Obligation: {obligation}')
print()

answers = {
    'risk_management_system': True,
    'data_governance': True,
    'technical_documentation': False,
    'record_keeping': True,
    'transparency': True,
    'human_oversight': False,
    'accuracy_robustness': True,
    'cybersecurity': True,
}
score, max_score, pct = checker.assess_high_risk_requirements(answers)
print()
compliance = 'COMPLIANT' if pct >= 80 else ('PARTIAL' if pct >= 60 else 'NON-COMPLIANT')
print(f'  Overall Score: {score}/{max_score} ({pct:.1f}%) -> {compliance}')
print()
print('NIST AI RMF vs EU AI Act:')
print('  NIST: GOVERN | MAP | MEASURE | MANAGE (voluntary, risk-based)')
print('  EU AI Act: legal requirements, conformity assessment, CE marking')
print('  Both: risk management, transparency, human oversight principles')
"
```

📸 **Verified Output:**
```
=== EU AI Act Compliance Assessment ===
System: Enterprise Credit Scoring AI
Risk Tier: HIGH_RISK
Obligation: Must comply with Title III requirements

  High-Risk AI Requirements Assessment:
    [✓] Has documented risk management system? (weight=3)
    [✓] Training data governance documented? (weight=3)
    [✗] Technical documentation complete? (weight=2)
    [✓] Automatic logging enabled? (weight=2)
    [✓] User transparency measures in place? (weight=3)
    [✗] Human oversight mechanisms exist? (weight=3)
    [✓] Accuracy and robustness tested? (weight=3)
    [✓] Cybersecurity measures implemented? (weight=2)

  Overall Score: 16/21 (76.2%) -> PARTIAL

NIST AI RMF vs EU AI Act:
  NIST: GOVERN | MAP | MEASURE | MANAGE (voluntary, risk-based)
  EU AI Act: legal requirements, conformity assessment, CE marking
  Both: risk management, transparency, human oversight principles
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Risk Tiers | Unacceptable (banned) → High → Limited → Minimal |
| High-Risk Requirements | Risk management, data governance, documentation, transparency, human oversight |
| GPAI | All models need documentation; >10^25 FLOPs → systemic risk tier |
| CE Marking | Conformity assessment required before market placement for high-risk AI |
| Timeline | Prohibited: Feb 2025; GPAI: Aug 2025; High-risk: Aug 2026 |
| NIST vs EU | Voluntary framework vs mandatory law; aligned principles, different enforcement |
| Fines | Up to €35M or 7% global annual turnover |

**Next Lab:** [Lab 11: AI Cost Optimization →](lab-11-ai-cost-optimization.md)
