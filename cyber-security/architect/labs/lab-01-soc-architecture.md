# Lab 01: SOC Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design a Security Operations Centre (SOC) tier model
- Understand SOC operational models (in-house, MSSP, hybrid)
- Architect a SIEM pipeline
- Calculate and interpret SOC performance metrics

---

## Step 1: SOC Tier Model

A mature SOC operates across four functional tiers:

| Tier | Role | Responsibilities |
|------|------|-----------------|
| **L1** | Triage Analyst | Alert monitoring, initial triage, ticket creation, escalation |
| **L2** | Incident Handler | Deep investigation, containment decisions, playbook execution |
| **L3** | Senior Analyst / Threat Hunter | Threat hunting, custom detections, malware analysis, forensics |
| **TI** | Threat Intelligence | IOC management, threat actor tracking, MITRE ATT&CK mapping |

> 💡 **L1 handles volume; L3 handles depth.** A well-tuned SIEM should allow L1 to close 70%+ of alerts within SLA.

---

## Step 2: SOC Operational Models

**In-House SOC**
- Full control, best for regulated industries (banking, defence)
- High CAPEX: staff, SIEM licenses, 24/7 shifts
- Suitable for organisations with >500 employees and dedicated security budget

**MSSP (Managed Security Service Provider)**
- Low setup cost, immediate 24/7 coverage
- Less customisation; shared analyst pool
- Risk: limited knowledge of your environment

**Hybrid SOC**
- MSSP handles L1/monitoring; internal team handles L2/L3 and TI
- Best of both worlds — most common enterprise model
- Requires clear escalation SLAs and runbook handoff

---

## Step 3: SIEM Architecture

```
Log Sources → Beats/Agents → [Message Queue: Kafka] → [Logstash/Ingest Pipeline]
                                                              ↓
                                              Elasticsearch (Hot/Warm/Cold)
                                                              ↓
                                              Kibana / SIEM Detection Rules
                                                              ↓
                                              Alert → SOAR → Case Management
```

**Key SIEM components:**
- **Collectors**: Beats (Filebeat, Winlogbeat, Packetbeat), Syslog agents
- **Processing**: Logstash pipelines — parse, normalise, enrich (GeoIP, threat intel)
- **Storage**: Elasticsearch indices with ILM (Index Lifecycle Management)
- **Analytics**: Detection rules (EQL, Sigma), ML anomaly detection
- **Response**: Integration with SOAR platforms (Splunk SOAR, Palo Alto XSOAR)

---

## Step 4: SOC Metrics — Key Performance Indicators

| Metric | Definition | Target |
|--------|-----------|--------|
| **MTTD** | Mean Time to Detect — time from incident start to detection | < 4 hours |
| **MTTR** | Mean Time to Respond — time from detection to containment | < 24 hours |
| **False Positive Rate** | FP alerts / total alerts | < 30% |
| **Alert-to-Case Ratio** | Cases opened / total alerts | > 5% indicates under-investigation |
| **Analyst Utilisation** | % time on alert triage vs. proactive work | < 80% reactive |
| **Dwell Time** | Time attacker is undetected in environment | < 7 days |

---

## Step 5: Build the SOC Metrics Calculator

```python
class SOCMetrics:
    def __init__(self, alerts, true_positives, false_positives, mttd_hours, mttr_hours):
        self.alerts = alerts
        self.tp = true_positives
        self.fp = false_positives
        self.mttd = mttd_hours
        self.mttr = mttr_hours

    def false_positive_rate(self):
        return round(self.fp / self.alerts * 100, 2)

    def detection_rate(self):
        return round(self.tp / self.alerts * 100, 2)

    def soc_efficiency_score(self):
        fpr = self.false_positive_rate()
        score = max(0, 100 - fpr - (self.mttd * 2) - (self.mttr * 0.5))
        return round(score, 1)

    def sla_status(self):
        return {
            'MTTD': 'PASS' if self.mttd <= 4 else 'FAIL',
            'MTTR': 'PASS' if self.mttr <= 24 else 'FAIL',
            'FPR':  'PASS' if self.false_positive_rate() <= 30 else 'FAIL'
        }

    def report(self):
        print('=== SOC Performance Metrics ===')
        print(f'Total Alerts        : {self.alerts}')
        print(f'True Positives      : {self.tp}')
        print(f'False Positives     : {self.fp}')
        print(f'False Positive Rate : {self.false_positive_rate()}%')
        print(f'Detection Rate      : {self.detection_rate()}%')
        print(f'MTTD                : {self.mttd}h')
        print(f'MTTR                : {self.mttr}h')
        print(f'SOC Efficiency Score: {self.soc_efficiency_score()}/100')
        print('--- SLA Status ---')
        for k, v in self.sla_status().items():
            print(f'  {k}: {v}')
        tiers = {
            'L1': 'Alert triage & initial response',
            'L2': 'Deep investigation & containment',
            'L3': 'Threat hunting & forensics',
            'TI': 'Threat intelligence & proactive defence'
        }
        print('--- SOC Tier Functions ---')
        for t, f in tiers.items():
            print(f'  [{t}] {f}')

soc = SOCMetrics(alerts=1200, true_positives=180, false_positives=360, mttd_hours=3.5, mttr_hours=18)
soc.report()
```

Run it:
```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
# (paste the code above)
"
```

📸 **Verified Output:**
```
=== SOC Performance Metrics ===
Total Alerts        : 1200
True Positives      : 180
False Positives     : 360
False Positive Rate : 30.0%
Detection Rate      : 15.0%
MTTD                : 3.5h
MTTR                : 18h
SOC Efficiency Score: 54.0/100
--- SLA Status ---
  MTTD: PASS
  MTTR: PASS
  FPR: PASS
--- SOC Tier Functions ---
  [L1] Alert triage & initial response
  [L2] Deep investigation & containment
  [L3] Threat hunting & forensics
  [TI] Threat intelligence & proactive defence
```

---

## Step 6: SOC Technology Stack

**Tier 1 — Alert Management:**
- SIEM: Elastic Security, Splunk ES, Microsoft Sentinel
- SOAR: Palo Alto XSOAR, Splunk SOAR, IBM Resilient
- Ticketing: ServiceNow, Jira

**Tier 2 — Investigation:**
- EDR: CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint
- Network: Zeek/Bro, Suricata, Darktrace
- Memory forensics: Volatility, Rekall

**Tier 3 — Hunting & Intelligence:**
- TIP: MISP, OpenCTI, Recorded Future
- Hunting: Elastic SIEM, Velociraptor, osquery

---

## Step 7: SOC Design Principles

1. **Detection-first mindset** — assume breach; focus on reducing dwell time
2. **Automation at L1** — auto-enrich and auto-close low-fidelity alerts
3. **Metrics-driven tuning** — review FPR weekly; update detection rules monthly
4. **People, Process, Technology** — 40% people investment, 30% process, 30% tools
5. **Purple team integration** — regular red/blue exercises to validate detections

> 💡 **The SOC maturity model**: Ad-hoc → Managed → Defined → Optimised. Most organisations are at "Managed"; targeting "Defined" (documented playbooks, SLAs, metrics) provides 3x improvement in MTTR.

---

## Step 8: Capstone — SOC Design Exercise

Design a SOC for a 2,000-employee financial services company:

**Requirements:**
- 24/7 monitoring
- Regulatory: PCI DSS, SOX, GDPR
- Budget: USD 3M/year
- Risk appetite: Low (zero-tolerance for payment card data breach)

**Recommended Architecture:**

```
Hybrid SOC Model:
  - MSSP (L1/L2 monitoring 24/7): USD 1.2M/year
  - Internal Security Team (L2/L3/TI): 4 FTEs x USD 150K = USD 600K
  - Technology (SIEM + SOAR + EDR): USD 800K
  - Training & Red Team: USD 400K

SIEM Strategy:
  - Microsoft Sentinel (cloud-native, Azure integration)
  - 90-day hot retention (NVMe), 365-day cold (Azure blob)
  - Detection coverage: MITRE ATT&CK tiers 1-3
  - SOAR playbooks: 25 automated, 15 semi-automated

Target KPIs:
  - MTTD: < 2 hours
  - MTTR: < 8 hours
  - FPR:  < 20%
  - Dwell time: < 24 hours
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| SOC Tiers | L1 triage → L2 investigate → L3 hunt → TI intelligence |
| SOC Models | In-house (control), MSSP (cost), Hybrid (best of both) |
| SIEM Pipeline | Collect → Parse → Normalise → Enrich → Detect → Alert |
| Key Metrics | MTTD (<4h), MTTR (<24h), FPR (<30%), Dwell time (<7d) |
| Efficiency Score | Formula: 100 - FPR% - MTTD*2 - MTTR*0.5 |
| Staffing | 3-5 analysts per shift; 24/7 = minimum 8 FTEs |
