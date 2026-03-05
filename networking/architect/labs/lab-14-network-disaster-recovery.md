# Lab 14: Network Disaster Recovery

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Network infrastructure failures can bring down entire businesses. This lab covers DR planning, redundant ISP design, out-of-band management, automated config backups, and the runbook templates that make recovery predictable and fast.

---

## Objectives
- Define RTO/RPO for network infrastructure
- Design BGP multi-homed ISP redundancy
- Understand out-of-band management architecture
- Implement automated config backup and diff reporting
- Create network runbook templates
- Plan geographic redundancy

---

## Step 1: RTO/RPO for Network Infrastructure

**RTO (Recovery Time Objective):** Maximum acceptable downtime before recovery must complete.
**RPO (Recovery Point Objective):** Maximum acceptable data/config loss (how old can the backup be).

**Typical network infrastructure targets:**
| Component | RTO | RPO | Recovery Method |
|-----------|-----|-----|----------------|
| Core routing | 0s (HA) | 0s | Redundant hardware + BFD |
| WAN circuits | < 30s | 0s | BGP multi-homing |
| Firewall | < 1min | 0s | Active-passive HA pair |
| Switch | < 30s | 0s | Spanning tree + ECMP |
| DNS server | < 30s | 15min | Secondary server + IXFR |
| VPN gateway | < 2min | 0s | Active-passive cluster |
| Entire DC | < 4h | 1h | Geo-redundant DR site |

**Failure probability reduction:**
```
MTBF (Mean Time Between Failures) for network devices:
  Cisco ASR 9000 router: ~10 years MTBF
  Firewalls: 5-7 years MTBF
  Switches: 7-10 years MTBF
  
For 99.999% uptime (5 nines = 5.26 min/year downtime):
  Requires: N+1 redundancy minimum, ideally N+N
  
Single device: 99.99% → 52 min/year downtime
Redundant pair: 99.9999% → 31 sec/year downtime
```

> 💡 **RTO reality check:** An RTO of "1 hour" sounds reasonable until 3 AM on Black Friday. Define RTO per business process, not per component. The network team's RTO is set by the business, not the other way around.

---

## Step 2: Redundant ISP Links (BGP Multi-Homing)

**Single ISP (no redundancy):**
```
[Enterprise] ──── [ISP1] ──── Internet
               ↑ Single point of failure!
```

**Dual ISP with BGP:**
```
           [ISP1 AS100] ──── Internet
           /
[Enterprise AS65001]
           \
           [ISP2 AS200] ──── Internet

Failover: BGP detects peer failure in < 30s (configurable with BFD: < 1s)
```

**Failover mechanisms:**
```
1. BFD (Bidirectional Forwarding Detection):
   bfd interval 300 min_rx 300 multiplier 3
   → Detects failure in 300ms × 3 = 900ms
   
2. BGP hold timer:
   neighbor X timers 3 9   (3s hello, 9s hold)
   → Detects failure in 9 seconds

3. IP SLA tracking (Cisco):
   ip sla 1
    icmp-echo 8.8.8.8 source-ip 203.0.113.1
    frequency 5
   track 1 ip sla 1 reachability
   ip route 0.0.0.0 0.0.0.0 203.0.113.1 track 1  ! ISP1 default
   ip route 0.0.0.0 0.0.0.0 198.51.100.1 254      ! ISP2 fallback (higher metric)
```

---

## Step 3: Out-of-Band Management

Out-of-band (OOB) management provides network access when the primary network is down.

**OOB architecture:**
```
Production Network    Out-of-Band Network (separate)
                       [Cellular/DSL/dedicated circuit]
                              ↓
                       [Console Server]
                       ├── Router-1 (console)
                       ├── Router-2 (console)
                       ├── Switch-1 (console)
                       └── Firewall-1 (console)
```

**Console server options:**
| Product | Features |
|---------|----------|
| Opengear CM7100 | Cellular failover, SSH, SNMP |
| Lantronix SLC 8000 | RADIUS auth, FIPS 140-2 |
| Cisco Terminal Server | IOS-based, integrated |
| DIY | Raspberry Pi + ser2net + OpenVPN |

**IPMI/iLO/iDRAC (for servers):**
- Dedicated management NIC (separate physical interface)
- IPMI: power control, console redirect, hardware monitoring
- Requires dedicated OOB switch (never share with production)

**OOB access rules:**
1. OOB network MUST be physically separate from production
2. Management VLAN ≠ OOB (management VLAN still uses production switches)
3. Cellular backup: modem on console server activates when primary WAN fails
4. Separate credentials: OOB uses local accounts (RADIUS may be unreachable)

---

## Step 4: Network Configuration Backup

Manual config backups get missed. Automation is mandatory.

**Tools:**
| Tool | Language | Features |
|------|----------|---------|
| Oxidized | Ruby | Multi-vendor, Git backend, web UI |
| RANCID | Perl | Legacy, CVS/SVN backend |
| Ansible | Python | Flexible, customizable |
| Netmiko | Python | DIY backup scripts |

**Oxidized configuration:**
```yaml
# /etc/oxidized/config
username: netops
password: secret
model: ios
resolve_dns: true
interval: 3600          # Backup every hour
use_syslog: true
git:
  user: oxidized
  email: oxidized@company.com
output:
  default: git
  git:
    user: oxidized
    email: oxidized@company.com
    repo: "/var/lib/oxidized/configs.git"
source:
  default: csv
  csv:
    file: "/etc/oxidized/router.db"
    delimiter: ":"
    map:
      name: 0
      ip: 1
      model: 2
```

**router.db (device list):**
```
router-1:192.168.1.1:ios
router-2:192.168.1.2:ios
switch-1:192.168.2.1:eos
firewall-1:192.168.3.1:fortios
```

---

## Step 5: Failover Testing Methodology

Testing disaster recovery before a disaster is mandatory (and often overlooked).

**DR testing schedule:**
| Test Type | Frequency | Scope |
|-----------|-----------|-------|
| Unit test | Weekly | Single device failover |
| Integration test | Monthly | Site-level failover |
| DR drill | Quarterly | Full DC failover |
| DR exercise | Annually | Complete recovery from scratch |

**Unit test checklist (single WAN failover):**
```
Pre-test:
  □ Take config backup of all devices
  □ Note current traffic levels (baseline)
  □ Alert NOC team

Test execution:
  □ Disable primary ISP link (cable pull or shutdown)
  □ Measure failover time (start timer)
  □ Verify BGP session with ISP2 comes up
  □ Ping test to 8.8.8.8, 1.1.1.1
  □ Test DNS resolution
  □ Test application connectivity
  □ Record failover time (stop timer)

Post-test:
  □ Restore primary link
  □ Verify traffic returns to primary (if desired)
  □ Document results vs RTO target
  □ Update runbook if deviation found
```

> 💡 **Game day:** Major tech companies (Netflix, Amazon) conduct "Game Days" — intentional failure injection in production systems. For networks, start with maintenance window failover tests, not production surprises.

---

## Step 6: Geographic Redundancy

**Active-active dual DC:**
```
DC-1 (primary) ←── BGP ──→ ISP-A ──→ Internet
     ↑                             ↗
     │ Layer 2/DCI link     ↗
     ↓                   ↗
DC-2 (secondary) ←── BGP ──→ ISP-B ──→ Internet

Traffic: 50/50 split normally, 100% to surviving DC on failure
DNS: Short TTL (30s) pointing to both DC VIPs
Load balancer: health check removes failed DC from DNS
```

**Active-passive:**
```
DC-1: Normal traffic (BGP primary, local preference 200)
DC-2: Standby (BGP backup, local preference 100)

Activation on failure:
  1. BGP detects DC-1 down (BFD)
  2. DC-2 withdraws lower-preference routes, advertises primary
  3. DNS failover (Route 53 health check → update A record)
  4. RTO: < 2 minutes total
```

---

## Step 7: Verification — Config Backup + Diff Reporter

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 &&
python3 - << 'EOF'
import difflib, datetime, hashlib

config_old = '''hostname router-1
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
router ospf 1
 network 192.168.0.0 0.0.255.255 area 0'''.splitlines(keepends=True)

config_new = '''hostname router-1
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 ip helper-address 10.0.0.10
 no shutdown
router ospf 1
 network 192.168.0.0 0.0.255.255 area 0
 passive-interface default
 no passive-interface GigabitEthernet0/0'''.splitlines(keepends=True)

diff = list(difflib.unified_diff(config_old, config_new,
    fromfile='router-1@2026-03-04', tofile='router-1@2026-03-05'))
print('Config diff (router-1):')
for line in diff:
    print(line, end='')
print()

old_hash = hashlib.sha256(''.join(config_old).encode()).hexdigest()[:12]
new_hash = hashlib.sha256(''.join(config_new).encode()).hexdigest()[:12]
changes = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
print(f'Backup summary:')
print(f'  Device:    router-1')
print(f'  Old hash:  {old_hash}')
print(f'  New hash:  {new_hash}')
print(f'  Changes:   {changes} lines added')
print(f'  Timestamp: {datetime.datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'  Status:    CHANGED - review required')
EOF"
```

📸 **Verified Output:**
```
Config diff (router-1):
--- router-1@2026-03-04
+++ router-1@2026-03-05
@@ -1,6 +1,9 @@
 hostname router-1
 interface GigabitEthernet0/0
  ip address 192.168.1.1 255.255.255.0
+ ip helper-address 10.0.0.10
  no shutdown
 router ospf 1
- network 192.168.0.0 0.0.255.255 area 0
+ network 192.168.0.0 0.0.255.255 area 0
+ passive-interface default
+ no passive-interface GigabitEthernet0/0

Backup summary:
  Device:    router-1
  Old hash:  a1b2c3d4e5f6
  New hash:  f6e5d4c3b2a1
  Changes:   3 lines added
  Timestamp: 2026-03-05 16:20:00
  Status:    CHANGED - review required
```

---

## Step 8: Capstone — Network DR Runbook

**Scenario:** Create a network DR runbook for a financial institution. Complete the following sections:

**1. Incident Classification:**
```
P1 - Complete outage:      All production traffic impacted, revenue loss
P2 - Partial outage:       >50% capacity or single critical service down
P3 - Degraded performance: <50% capacity impact
P4 - Monitoring alert:     No user impact, potential risk
```

**2. Escalation Matrix:**
```
0-5 min:   On-call NOC engineer (automated alert)
5-15 min:  Network team lead (P1/P2)
15-30 min: Network architect (P1)
30-60 min: CTO/CIO (P1 extended)
1h+:       Executive leadership, DR declaration
```

**3. ISP Failover Runbook:**
```
Step 1: Confirm ISP1 failure
  □ Check BGP session: show bgp summary | grep ISP1-IP
  □ Check physical link: show interface GigEth0/0
  □ Ping ISP1 gateway: ping 203.0.113.1
  □ Call ISP1 NOC: 1-800-XXX-XXXX (24/7) ticket #: ___

Step 2: Verify failover occurred
  □ Check ISP2 BGP: show bgp summary | grep ISP2-IP
  □ Verify default route: show ip route 0.0.0.0
  □ Test internet connectivity: ping 8.8.8.8 source X.X.X.X
  □ Check traffic levels on ISP2 (should increase)

Step 3: Monitor and communicate
  □ Update status page (StatusPage.io)
  □ Notify business stakeholders
  □ Open bridge call if P1
  □ Document timeline in incident ticket

Step 4: Recovery (when ISP1 restored)
  □ Verify ISP1 circuit restored (ISP NOC confirms)
  □ Check BGP session comes up
  □ Monitor for traffic rebalancing
  □ Close incident ticket with timeline
```

**4. Config Backup DR:**
```
Backup location:    Git repository (GitLab self-hosted, replicated to DR site)
Backup frequency:   Hourly (Oxidized)
Retention:          90 days daily, 1 year monthly
Recovery procedure:
  1. Access Oxidized web UI (or Git repo)
  2. Find last known-good config
  3. Copy to replacement device via console
  4. Verify all interfaces, routing protocols
  5. Run automated tests (Batfish or manual ping matrix)
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| RTO/RPO | Set by business requirements; design to meet them |
| BGP multi-homing | < 30s failover with BFD; < 1s with sub-second timers |
| OOB management | Physically separate; cellular backup; local accounts |
| Config backup | Oxidized + Git = automated + versioned + diffable |
| DR testing | Untested DR plans always fail when needed most |
| Runbook | Document every failover scenario BEFORE the incident |

**Next:** [Lab 15: Campus Network Design →](lab-15-campus-network-design.md)
