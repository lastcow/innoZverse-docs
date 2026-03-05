# Lab 02: SIEM Design with Elastic

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Architect an Elastic SIEM for enterprise deployment
- Design index strategies and data lifecycle management
- Build Sigma detection rules and translate to EQL
- Tune SIEM performance and reduce false positives

---

## Step 1: Elastic SIEM Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│  Endpoints  │  Network  │  Cloud  │  Apps  │  Identity      │
└──────┬──────┴─────┬─────┴────┬────┴───┬────┴──────┬─────────┘
       │            │          │        │           │
┌──────▼────────────▼──────────▼────────▼───────────▼─────────┐
│                BEATS / AGENTS                                │
│  Filebeat │ Winlogbeat │ Packetbeat │ Auditbeat │ Metricbeat │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │  Logstash / Ingest    │  ← Parse, enrich, filter
              │  Pipelines            │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │    Elasticsearch      │
              │  Hot → Warm → Cold    │  ← ILM policy
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │  Kibana Security      │
              │  Detection Rules      │  ← EQL / Sigma / ML
              │  SIEM Dashboards      │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │  SOAR / Alerting      │  ← PagerDuty, XSOAR
              └───────────────────────┘
```

---

## Step 2: Data Ingestion — Beats Configuration

**Winlogbeat** — Windows event logs (critical event IDs):
```yaml
winlogbeat.event_logs:
  - name: Security
    event_id: 4624, 4625, 4648, 4688, 4698, 4719, 4720, 4732, 4756
  - name: System
  - name: Microsoft-Windows-Sysmon/Operational
output.logstash:
  hosts: ["logstash:5044"]
```

**Filebeat** — Linux syslog / application logs:
```yaml
filebeat.inputs:
  - type: log
    paths: ["/var/log/auth.log", "/var/log/syslog"]
    fields:
      log_type: syslog
  - type: log
    paths: ["/var/log/nginx/access.log"]
    fields:
      log_type: nginx
```

> 💡 **Use Elastic Agent + Fleet** in modern deployments — single agent replaces individual Beats and enables central policy management.

---

## Step 3: Index Strategy

**Naming Convention:**
```
logs-<data_stream>-<namespace>
  logs-endpoint.events.process-production
  logs-windows.security-production
  logs-network.flow-production
  logs-cloud.aws.cloudtrail-production
```

**ECS (Elastic Common Schema)** — standardise field names:
```
event.category   : process, network, authentication
event.type       : start, end, allowed, denied
host.name        : endpoint hostname
user.name        : authenticated user
process.name     : process name
network.direction: inbound, outbound
```

---

## Step 4: Hot/Warm/Cold Tier Strategy

| Tier | Retention | Storage Type | Replicas | Use Case |
|------|-----------|-------------|---------|----------|
| **Hot** | 0–7 days | NVMe SSD | 1 | Active ingest + real-time search |
| **Warm** | 7–30 days | SSD | 0 | Investigation, compressed |
| **Cold** | 30–365 days | HDD / Object | 0 | Compliance, frozen snapshots |
| **Frozen** | 365+ days | S3 / Azure Blob | 0 | Long-term archive, searchable |

**ILM Policy Example:**
```json
{
  "policy": {
    "phases": {
      "hot":   {"actions": {"rollover": {"max_size": "50gb", "max_age": "1d"}}},
      "warm":  {"min_age": "7d",  "actions": {"shrink": {"number_of_shards": 1}, "forcemerge": {"max_num_segments": 1}}},
      "cold":  {"min_age": "30d", "actions": {"freeze": {}}},
      "delete":{"min_age": "365d","actions": {"delete": {}}}
    }
  }
}
```

---

## Step 5: Sigma Rule Parser + EQL Query Builder

```python
import re, json, yaml

sigma_rule = """
title: Suspicious PowerShell Encoded Command
status: experimental
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|contains|all:
            - powershell
            - -EncodedCommand
    condition: selection
level: high
tags:
    - attack.execution
    - attack.t1059.001
"""

rule = yaml.safe_load(sigma_rule)
print('=== Sigma Rule Parser ===')
print(f'Title  : {rule["title"]}')
print(f'Level  : {rule["level"]}')
print(f'Status : {rule["status"]}')
print(f'Tags   : {", ".join(rule["tags"])}')

# Build EQL query
terms = rule['detection']['selection']['CommandLine|contains|all']
eql_parts = ' and '.join([f'process.command_line : "*{t}*"' for t in terms])
eql = f'process where {eql_parts}'
print()
print('=== Generated EQL Query ===')
print(eql)

# Hot/Warm/Cold tier model
print()
print('=== Elastic Index Tier Strategy ===')
tiers = [
    ('hot',  '0-7 days',   'NVMe SSD', 'Active search + ingest'),
    ('warm', '7-30 days',  'SSD',       'Read-only, compressed'),
    ('cold', '30-365 days','HDD/Object','Frozen, searchable snapshots'),
]
print(f'  {"Tier":<6} {"Retention":<12} {"Storage":<14} {"Usage"}')
for t in tiers:
    print(f'  {t[0]:<6} {t[1]:<12} {t[2]:<14} {t[3]}')
```

📸 **Verified Output:**
```
=== Sigma Rule Parser ===
Title  : Suspicious PowerShell Encoded Command
Level  : high
Status : experimental
Tags   : attack.execution, attack.t1059.001

=== Generated EQL Query ===
process where process.command_line : "*powershell*" and process.command_line : "*-EncodedCommand*"

=== Elastic Index Tier Strategy ===
  Tier   Retention    Storage        Usage
  hot    0-7 days     NVMe SSD       Active search + ingest
  warm   7-30 days    SSD            Read-only, compressed
  cold   30-365 days  HDD/Object     Frozen, searchable snapshots
```

---

## Step 6: SIEM Detection Rules

**Rule Categories:**

| Category | Example Rule | ATT&CK |
|----------|-------------|--------|
| Execution | PowerShell encoded command | T1059.001 |
| Persistence | Scheduled task creation | T1053.005 |
| Lateral Movement | Admin share access | T1021.002 |
| Credential Access | LSASS memory access | T1003.001 |
| Exfiltration | Large DNS query volume | T1048.003 |
| Defence Evasion | Security log cleared | T1070.001 |

**EQL Examples:**
```
# Ransomware: mass file rename
file where event.type == "rename" and
  file.extension in ("locked", "encrypted", "ransom") and
  count() > 100 by host.name

# Pass-the-Hash
authentication where
  winlog.event_data.LogonType == "3" and
  winlog.event_data.LmPackageName == "NTLM V1"

# DNS tunnelling
dns where length(dns.question.name) > 52 and
  dns.question.type == "TXT"
```

---

## Step 7: SIEM Tuning Methodology

**Tuning cycle (monthly):**
1. Pull top-10 alert sources by volume
2. Identify FP patterns (benign software, maintenance windows)
3. Add exceptions (allowlists, time-based suppression)
4. Validate rule still catches TP with red team test
5. Document changes in SIEM change log

**Tuning techniques:**
- **Allowlisting**: Exclude known-good processes (`svchost.exe` from `C:\Windows\System32`)
- **Risk scoring**: Adjust rule severity based on asset criticality
- **Aggregation**: Group similar alerts into single case (same user, same hour)
- **Baseline**: ML-based anomaly detection for user behaviour (UEBA)

> 💡 **Target FPR < 20%** for mature SIEM. Start with the 5 highest-volume, lowest-fidelity rules and tune them first for immediate impact.

---

## Step 8: Capstone — SIEM Architecture Design

**Scenario:** Design Elastic SIEM for 5,000-endpoint enterprise

**Architecture Decisions:**

```
Cluster topology:
  - 3x Master nodes (t3.medium, 8GB RAM)
  - 6x Hot data nodes (m5.xlarge, 32GB RAM, 2TB NVMe)
  - 3x Warm data nodes (m5.large, 16GB RAM, 8TB HDD)
  - 2x Coordinating nodes (load-balance queries)

Ingest capacity:
  - Target: 50,000 EPS (events per second)
  - Logstash: 4 nodes, 8-worker pipelines
  - Kafka: 3-broker cluster for buffering

Index strategy:
  - Daily rollover at 50GB or 1 day
  - ILM: hot 7d → warm 30d → cold 90d → delete 365d

Detection coverage (MITRE ATT&CK):
  - 80 detection rules covering 40 ATT&CK techniques
  - ML jobs: unusual process, unusual network, rare command line
  - Sigma rules imported via sigma-cli → EQL conversion

Estimated cost:
  - AWS: ~USD 8,000/month (cluster + storage)
  - Elastic license: USD 3,000/month (Platinum)
  - Total: USD 132,000/year
```

---

## Summary

| Component | Design Choice | Rationale |
|-----------|-------------|-----------|
| Agents | Elastic Agent + Fleet | Centralised management |
| Schema | ECS (Elastic Common Schema) | Normalised field names |
| Hot tier | NVMe SSD, 7 days | Fast search for active incidents |
| Warm tier | SSD, 30 days | Investigation window |
| Cold tier | HDD/Object, 365 days | Compliance retention |
| Detection | EQL + Sigma + ML | Multi-layer detection |
| Tuning | Monthly FPR review | Maintain < 20% FPR |
