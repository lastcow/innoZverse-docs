# Lab 14: BCP & Disaster Recovery

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design Business Continuity Plans (BCP) aligned to NIST CSF
- Conduct Business Impact Analysis (BIA) and calculate RTO/RPO
- Design DR tiers and 3-2-1 backup strategies
- Build a Python BIA calculator with RTO/RPO compliance checking

---

## Step 1: BCP / DR Terminology

| Term | Definition |
|------|-----------|
| **RTO** | Recovery Time Objective — max acceptable downtime |
| **RPO** | Recovery Point Objective — max acceptable data loss |
| **MTTR** | Mean Time to Repair/Recover |
| **MTBF** | Mean Time Between Failures |
| **RLO** | Recovery Level Objective — % functionality needed |
| **BIA** | Business Impact Analysis — financial/operational impact of disruption |
| **MAO** | Maximum Acceptable Outage — absolute deadline before business ceases |

**Relationship:**
```
Incident occurs → Data loss window ← RPO → System restored
      ↑                                           ↑
      └───────────── RTO ─────────────────────────┘
      (RTO = elapsed time until operational)
      (RPO = data age at recovery point)
```

---

## Step 2: Business Impact Analysis (BIA) + RTO/RPO Calculator

```python
class BIACalculator:
    def __init__(self): self.systems = []
    def add_system(self, name, crit, rto, rpo, impact):
        self.systems.append({'name':name,'crit':crit,'rto':rto,'rpo':rpo,'impact':impact})
    def sla(self, crit):
        return {'Tier1':(1,0.25),'Tier2':(4,1),'Tier3':(24,4),'Tier4':(72,24)}.get(crit,(999,999))
    def report(self):
        print('=== Business Impact Analysis (BIA) ===')
        print('  System               Tier   RTO  RPO  Impact/hr  RTO_SLA  RPO_SLA  Status')
        total = 0
        for s in self.systems:
            r_rto, r_rpo = self.sla(s['crit'])
            ok = s['rto']<=r_rto and s['rpo']<=r_rpo
            risk = s['impact']*s['rto']
            total += risk
            print(f'  {s["name"]:<20} {s["crit"]:<6} {s["rto"]:<5}{s["rpo"]:<5}{s["impact"]:<11}{r_rto}h{"":5}{r_rpo}h{"":5}[{"PASS" if ok else "FAIL"}]')
        print(f'  Total Financial Risk at RTO: USD {total:,}')

b = BIACalculator()
b.add_system('Core Banking',    'Tier1',  2,  0.5, 50000)
b.add_system('Customer Portal', 'Tier2',  3,  1,   10000)
b.add_system('Email System',    'Tier3',  20, 4,   2000)
b.add_system('HR System',       'Tier4',  48, 24,  500)
b.report()
print()
print('DR Tiers: Hot (RTO<1h) | Warm (RTO 1-4h) | Cold (RTO 24-72h)')
```

📸 **Verified Output:**
```
=== Business Impact Analysis (BIA) ===
  System               Tier   RTO  RPO  Impact/hr  RTO_SLA  RPO_SLA  Status
  Core Banking         Tier1  2    0.5  50000      1h     0.25h     [FAIL]
  Customer Portal      Tier2  3    1    10000      4h     1h     [PASS]
  Email System         Tier3  20   4    2000       24h     4h     [PASS]
  HR System            Tier4  48   24   500        72h     24h     [PASS]
  Total Financial Risk at RTO: USD 194,000

DR Tiers: Hot (RTO<1h) | Warm (RTO 1-4h) | Cold (RTO 24-72h)
```

---

## Step 3: DR Tiers

| Tier | Name | RTO | RPO | Description | Cost |
|------|------|-----|-----|-------------|------|
| **Tier 6** | Hot Site | < 1 hour | < 15 min | Active-active; identical infrastructure | Very High |
| **Tier 5** | Warm Site | 1-4 hours | 1-4 hours | Standby systems, data replicated | High |
| **Tier 4** | Cold Site | 24-72 hours | 24 hours | Empty facility, equipment ordered/shipped | Medium |
| **Tier 3** | Electronic Vaulting | Days | 1-24 hours | Offsite backup, hardware sourced separately | Low |
| **Tier 2** | Backup & Restore | Days-weeks | 24+ hours | Tape/cloud backup, full rebuild | Very Low |

**Active-Active vs Active-Passive:**
```
Active-Active:
  Site A ←→ Site B (both serving traffic)
  RTO: seconds (DNS failover or load balancer)
  RPO: near-zero (synchronous replication)
  Cost: 2x infrastructure

Active-Passive:
  Site A (primary) → Site B (standby, replicated)
  RTO: minutes-hours (failover trigger + warm-up)
  RPO: minutes (asynchronous replication lag)
  Cost: ~1.5x infrastructure
```

---

## Step 4: 3-2-1 Backup Strategy

**3-2-1 rule:**
- **3** copies of data
- **2** different storage media types
- **1** offsite (geographically separate)

**Modern extension — 3-2-1-1-0:**
- 3 copies, 2 media, 1 offsite
- **1** offline/air-gapped (ransomware protection)
- **0** errors (verified backups)

```
Primary data:    Production database (NVMe SSD)
Backup copy 1:   Daily snapshot to local NAS (different media)
Backup copy 2:   Daily replication to DR site (offsite)
Offline backup:  Weekly tape or S3 Object Lock (ransomware-proof)

Verification:
  - Monthly restore test: verify backup integrity
  - Annual full DR drill: restore to DR site, test functionality
  - Automated backup monitoring: alert if backup fails
```

> 💡 **Ransomware invalidates non-air-gapped backups** — if your backup target is network-reachable, ransomware can encrypt it too. Immutable backups (AWS S3 Object Lock, Azure Immutable Blob) or offline tapes are essential.

---

## Step 5: Ransomware Recovery Plan

**Specific considerations for ransomware:**

**Before a ransomware event:**
- Immutable backups (S3 Object Lock WORM, NetApp SnapLock)
- Network segmentation (isolate backup infrastructure)
- AD tiering (prevent ransomware from reaching backup admin accounts)
- Offline backup: weekly tape, offsite storage

**During ransomware recovery:**
```
Hour 0:    Alert confirmed; isolate affected systems
Hour 1:    Activate IR team; assess blast radius
Hour 2:    Identify patient zero; determine backup integrity
Hour 3:    Begin restore from last known-clean backup
Hour 4-24: Progressive restoration (critical → non-critical)
Hour 24+:  Monitor for re-infection; patch initial vector
Week 1-2:  Full restoration; post-incident review
```

**To pay or not to pay ransom:**
| Factor | Consideration |
|--------|--------------|
| Legal | Sanctions risk if paying OFAC-listed group |
| Insurance | Cyber policy may require specific actions |
| Practical | Payment doesn't guarantee decryption |
| Ethical | Funding future attacks |
| Alternative | Clean backups available? |

---

## Step 6: NIST CSF Recover Function

**NIST CSF 2.0 — Recover (RC):**

| Subcategory | Description |
|------------|-------------|
| RC.RP-1 | Recovery plan executed per IR objectives |
| RC.RP-2 | Recovery decisions incorporate business impact |
| RC.RP-3 | Recovery activities communicated to stakeholders |
| RC.IM-1 | Recovery plans incorporate lessons learned |
| RC.CO-3 | Recovery activities communicated to internal/external parties |

**Recovery order framework:**
```
Priority 1 (< 4 hours):    Life-safety systems, emergency communications
Priority 2 (< 24 hours):   Core business operations, payment processing
Priority 3 (< 72 hours):   Supporting systems, customer-facing services
Priority 4 (< 1 week):     Administrative systems, reporting
Priority 5 (< 2 weeks):    Non-critical, archival, development
```

---

## Step 7: BCP Testing

**Testing types:**
| Type | Description | Frequency |
|------|-----------|-----------|
| Document review | Review plans for accuracy | Annual |
| Tabletop exercise | Discussion-based scenario | Quarterly |
| Walkthrough | Physical walkthrough of procedures | Semi-annual |
| Simulation | Controlled environment rehearsal | Annual |
| Parallel test | DR systems run alongside production | Annual |
| Full interruption | Production cut over to DR (risk!) | Every 2-3 years |

**Tabletop scenario example:**
```
Scenario: Ransomware hits primary data centre at 2 AM Friday
  Q1: Who is notified first? (timeline)
  Q2: How do we confirm backup integrity?
  Q3: Which systems restore first?
  Q4: Who authorises customer communication?
  Q5: When do we invoke the DR contract?
  Q6: How do we verify no re-infection before reconnecting?
```

---

## Step 8: Capstone — Enterprise DR Architecture

**Scenario:** Financial services, core banking, RTO 1h / RPO 15min

```
DR Architecture:

Primary Site (London DC):
  - Core banking: 3-tier architecture
  - Replication: synchronous to DR site (RPO: near-zero)
  - Application: active-passive

DR Site (Frankfurt DC, 600km):
  - Hot standby: pre-provisioned, powered on
  - Synchronous DB replication (NetApp SnapMirror)
  - Application servers: standby, ready in 15 min
  - Failover: automated (Pacemaker) or manual

Cloud Tier (AWS eu-central-1):
  - Second backup: daily snapshot to S3
  - S3 Object Lock: WORM, 7-year retention
  - Glacier for archive: 10-year compliance

Backup Strategy:
  - Every 15 min: transaction log to DR site
  - Hourly: snapshot to DR NAS
  - Daily: backup to S3 (Frankfurt)
  - Weekly: offline tape to Iron Mountain

Testing:
  - Failover drill: quarterly (no customer impact)
  - Full DR test: annual (weekend, planned maintenance window)
  - Backup restore test: monthly (random sample)
  - Tabletop: quarterly (different scenarios)

RTO/RPO validation:
  - RTO target: 1 hour | Last test: 47 minutes ✅
  - RPO target: 15 minutes | Last test: 8 minutes ✅
  - Next test: 2024-06-15
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| RTO | Max downtime; drives DR tier selection |
| RPO | Max data loss; drives replication frequency |
| BIA | Financial impact + criticality rating per system |
| DR Tiers | Hot (<1h) → Warm (1-4h) → Cold (24-72h) |
| 3-2-1-1-0 | 3 copies, 2 media, 1 offsite, 1 offline, 0 errors |
| Ransomware DR | Immutable backups + offline copy are non-negotiable |
| NIST CSF RC | Recover: execute plan, communicate, incorporate lessons |
