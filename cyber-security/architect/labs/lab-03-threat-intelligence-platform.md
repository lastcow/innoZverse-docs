# Lab 03: Threat Intelligence Platform

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Architect a Threat Intelligence Platform (TIP)
- Build STIX 2.1 objects and bundles
- Implement TAXII 2.1 sharing protocol
- Apply the Diamond Model and MITRE ATT&CK integration

---

## Step 1: Threat Intelligence Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              INTELLIGENCE SOURCES                            │
│  OSINT  │  Commercial  │  ISAC  │  Government  │  Internal  │
└─────────┴──────┬────────┴────────┴──────────────┴────────────┘
                 │
    ┌────────────▼──────────────┐
    │   TAXII 2.1 Collection    │  ← Pull/push sharing
    └────────────┬──────────────┘
                 │
    ┌────────────▼──────────────┐
    │   TIP Core (MISP/OpenCTI) │
    │   ┌──────────────────┐   │
    │   │  STIX 2.1 Store  │   │  ← Indicators, TTPs, actors
    │   └──────────────────┘   │
    │   ┌──────────────────┐   │
    │   │  IOC Lifecycle   │   │  ← Active/expired/revoked
    │   └──────────────────┘   │
    │   ┌──────────────────┐   │
    │   │  ATT&CK Mapping  │   │  ← TTP enrichment
    │   └──────────────────┘   │
    └────────────┬──────────────┘
                 │
    ┌────────────▼──────────────┐
    │   Consumers               │
    │  SIEM │ Firewall │ EDR    │  ← Automated blocking/detection
    └───────────────────────────┘
```

---

## Step 2: STIX 2.1 Object Model

**STIX Domain Objects (SDOs):**

| Object Type | Purpose | Example |
|------------|---------|---------|
| `indicator` | Detectable pattern (IOC) | Malicious IP, hash, domain |
| `malware` | Malware family description | Ransomware family details |
| `threat-actor` | Adversary profile | APT28, Lazarus Group |
| `attack-pattern` | TTP (MITRE ATT&CK) | T1059.001 PowerShell |
| `campaign` | Coordinated attack activity | Operation Aurora |
| `course-of-action` | Mitigation/response | Patch CVE-2021-44228 |
| `relationship` | Links objects together | indicator → indicates → malware |

**STIX Pattern Examples:**
```
# IP address indicator
[ipv4-addr:value = '192.168.99.1']

# File hash (MD5)
[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']

# Domain
[domain-name:value = 'malicious.example.com']

# Combined (IP + port)
[network-traffic:dst_ref.type = 'ipv4-addr' AND
 network-traffic:dst_ref.value = '10.0.0.1' AND
 network-traffic:dst_port = 4444]
```

---

## Step 3: TAXII 2.1 Protocol

**TAXII 2.1 API Endpoints:**
```
Discovery:     GET /taxii2/
API Root info: GET /{api_root}/
Collections:   GET /{api_root}/collections/
Objects:       GET /{api_root}/collections/{id}/objects/
Add objects:   POST /{api_root}/collections/{id}/objects/
```

**TAXII Envelope format:**
```json
{
  "more": false,
  "next": null,
  "objects": [
    { "type": "indicator", ... },
    { "type": "threat-actor", ... }
  ]
}
```

> 💡 **TAXII sharing models**: Push (producer sends to consumers), Pull (consumers fetch from producers), Hub-and-Spoke (central clearing house like FS-ISAC).

---

## Step 4: STIX 2.1 Builder + TAXII Envelope Creator

```python
import json, uuid, datetime

def stix_id(type_): return f'{type_}--{uuid.uuid4()}'
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')

indicator = {
    'type': 'indicator',
    'spec_version': '2.1',
    'id': stix_id('indicator'),
    'created': now,
    'modified': now,
    'name': 'Malicious IP - C2 Server',
    'indicator_types': ['malicious-activity'],
    'pattern': "[ipv4-addr:value = '192.168.99.1']",
    'pattern_type': 'stix',
    'valid_from': now,
    'confidence': 85
}

threat_actor = {
    'type': 'threat-actor',
    'spec_version': '2.1',
    'id': stix_id('threat-actor'),
    'created': now,
    'modified': now,
    'name': 'APT-EXAMPLE',
    'threat_actor_types': ['nation-state'],
    'sophistication': 'advanced',
    'resource_level': 'government'
}

bundle = {
    'type': 'bundle',
    'id': stix_id('bundle'),
    'objects': [indicator, threat_actor]
}

taxii_envelope = {
    'more': False,
    'next': None,
    'objects': bundle['objects']
}

print('=== STIX 2.1 Bundle ===')
print(f'Bundle ID    : {bundle["id"]}')
print(f'Objects      : {len(bundle["objects"])}')
print(f'Indicator    : {indicator["name"]}')
print(f'Pattern      : {indicator["pattern"]}')
print(f'Threat Actor : {threat_actor["name"]} ({threat_actor["sophistication"]})')
print()
print('=== TAXII 2.1 Envelope ===')
print(f'more  : {taxii_envelope["more"]}')
print(f'count : {len(taxii_envelope["objects"])} objects')
print('Diamond Model vertices: Adversary | Infrastructure | Capability | Victim')
```

📸 **Verified Output:**
```
=== STIX 2.1 Bundle ===
Bundle ID    : bundle--18034048-c84c-4653-8f75-ddfb43d17d85
Objects      : 2
Indicator    : Malicious IP - C2 Server
Pattern      : [ipv4-addr:value = '192.168.99.1']
Threat Actor : APT-EXAMPLE (advanced)

=== TAXII 2.1 Envelope ===
more  : False
count : 2 objects
Diamond Model vertices: Adversary | Infrastructure | Capability | Victim
```

---

## Step 5: Diamond Model of Intrusion Analysis

```
              Adversary
             /         \
            /           \
    Infrastructure ─── Capability
             \           /
              \         /
               Victim
```

**Vertices:**
- **Adversary**: Who (threat actor, motivation, intent)
- **Capability**: What (malware, exploit, technique)
- **Infrastructure**: How (C2 domains, IPs, bulletproof hosting)
- **Victim**: Target (industry, geography, role)

**Meta-features:** Timestamp, Phase, Result, Direction, Methodology, Resources

**Application:** For each intrusion event, populate all four vertices. Cross-reference events to identify campaigns (shared infrastructure or capability = same adversary).

---

## Step 6: IOC Lifecycle Management

| Stage | Description | Action |
|-------|-----------|--------|
| **Collection** | IOC received from feed/incident | Ingest to TIP |
| **Processing** | Deduplication, normalisation | Run through pipeline |
| **Analysis** | Context enrichment, confidence scoring | Analyst review |
| **Active** | Deployed to controls (firewall, EDR, SIEM) | Monitoring |
| **Review** | Periodic validity check | Re-score or revoke |
| **Expired** | TTL exceeded or indicator stale | Archive |
| **Revoked** | Confirmed false positive | Remove from controls |

**IOC confidence scoring:**
```
Score 0-30:  Low confidence — monitor only
Score 31-70: Medium — block on known-bad networks
Score 71-100: High — block globally + investigate
```

> 💡 **IOC decay**: IP-based IOCs lose relevance in 24-72 hours (shared hosting). Domain IOCs last 7-30 days. Hash IOCs are more durable but can be trivially changed by attackers.

---

## Step 7: MITRE ATT&CK Integration

**ATT&CK Navigator use cases:**
- Map detected TTPs to ATT&CK matrix
- Identify coverage gaps (unheatmapped techniques = blind spots)
- Compare threat actor profiles to your detection coverage

**TIP → SIEM → ATT&CK workflow:**
```
TIP: APT28 uses T1059.001 (PowerShell)
  → SIEM: Do we have a detection rule for T1059.001?
  → No → Create Sigma rule → Test with atomic red team
  → Yes → Review rule fidelity → Tune if needed
```

**MISP Galaxy integration:**
- Import ATT&CK galaxy clusters into MISP
- Tag events with ATT&CK technique IDs
- Export heatmap to ATT&CK Navigator

---

## Step 8: Capstone — TIP Architecture Design

**Scenario:** Design a TIP for a financial sector ISAC with 50 member organisations

```
Architecture: OpenCTI + MISP Federation

Central Hub (ISAC):
  - OpenCTI (primary TIP) with TAXII 2.1 server
  - MISP sync from member organisations
  - Analyst team: 3 FTEs for IOC curation

Member Integration:
  - TAXII pull: automated 15-minute polling
  - Confidence threshold: only share >60 confidence
  - TLP marking: TLP:GREEN for sharing, TLP:RED internal only

ATT&CK Coverage:
  - Track 15 threat actors targeting financial sector
  - Monitor 50+ TTPs common to sector
  - Weekly threat brief to member CISOs

Automation:
  - Auto-push high-confidence IOCs to member firewalls
  - SIEM rule generation from new malware campaigns
  - Bi-directional: members contribute their incidents
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| STIX 2.1 | JSON-based standard: indicators, malware, threat-actors, relationships |
| TAXII 2.1 | HTTP API for sharing STIX bundles (pull/push) |
| Diamond Model | Adversary ↔ Capability ↔ Infrastructure ↔ Victim |
| IOC Lifecycle | Collect → Process → Analyse → Active → Review → Expire/Revoke |
| ATT&CK Integration | Map TTPs to detection coverage; identify blind spots |
| TLP | Traffic Light Protocol: WHITE/GREEN/AMBER/RED for sharing scope |
