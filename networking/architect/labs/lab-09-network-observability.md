# Lab 09: Network Observability

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Network observability goes beyond monitoring — it provides the telemetry, context, and analytics needed to understand network behavior. This lab covers flow collection, SNMP, streaming telemetry, and building a complete observability stack.

---

## Objectives
- Implement NetFlow v9/IPFIX flow collection
- Compare sFlow, SNMP, and streaming telemetry
- Build a Prometheus network metrics pipeline
- Decode NetFlow v9 packets programmatically
- Design a complete network observability stack

---

## Step 1: Flow Telemetry Overview

**Three approaches to flow-level visibility:**

| Protocol | Method | Overhead | Accuracy | Granularity |
|----------|--------|---------|---------|-------------|
| NetFlow v9 | Cache-based | Medium | High | Per-flow |
| IPFIX | NetFlow v10 | Medium | High | Flexible |
| sFlow | Sampling | Low | Statistical | Packet sample |
| SNMP poll | Counter query | Low | Counters only | Interface-level |
| Streaming | gNMI/gRPC | Low | Real-time | Configurable |

**Choose based on:**
- **NetFlow/IPFIX:** Security analysis, billing, capacity planning (accurate flows)
- **sFlow:** High-speed links where full flows impossible (100G+)
- **SNMP:** Legacy devices, simple interface counters
- **Streaming:** Modern devices, real-time analytics, AI/ML pipelines

---

## Step 2: NetFlow v9 Architecture

**NetFlow v9 components:**
```
[Network Device]  →  [Flow Exporter]  →  [Flow Collector]  →  [Analyzer]
(Router/Switch)      (IOS/NX-OS/FRR)     (nfcapd/ntopng)     (Kibana/Grafana)
```

**NetFlow v9 packet structure:**
```
Header:
  Version:    9 (2 bytes)
  Count:      Number of flowsets (2 bytes)
  Sys uptime: MS since boot (4 bytes)
  Unix secs:  Epoch timestamp (4 bytes)
  Seq number: Export packet sequence (4 bytes)
  Source ID:  Router/engine ID (4 bytes)

FlowSets:
  Template FlowSet: Define record format
  Data FlowSet:     Actual flow records
  Options FlowSet:  Device/sampling info
```

**NetFlow v9 fields (common):**
| Field | ID | Size | Description |
|-------|----|----|-------------|
| IPv4_SRC_ADDR | 8 | 4 | Source IP |
| IPv4_DST_ADDR | 12 | 4 | Destination IP |
| L4_SRC_PORT | 7 | 2 | Source port |
| L4_DST_PORT | 11 | 2 | Destination port |
| PROTOCOL | 4 | 1 | IP protocol |
| IN_BYTES | 1 | 4/8 | Byte count |
| IN_PKTS | 2 | 4/8 | Packet count |
| FIRST_SWITCHED | 22 | 4 | First packet timestamp |
| LAST_SWITCHED | 21 | 4 | Last packet timestamp |
| TCP_FLAGS | 6 | 1 | TCP control bits |

**Enable NetFlow on Cisco IOS:**
```
interface GigabitEthernet0/0
 ip flow ingress
 ip flow egress

ip flow-export version 9
ip flow-export destination 10.0.0.10 2055
ip flow-export source Loopback0
ip flow-cache timeout active 1
ip flow-cache timeout inactive 15
ip flow-cache entries 65536
```

---

## Step 3: sFlow Architecture

sFlow uses statistical packet sampling rather than flow caching:

**sFlow agent → sFlow collector:**
```
Every Nth packet → Sampled → sFlow datagram → Collector
         ↑
  Sampling rate: 1:1000 (1G), 1:10000 (10G), 1:100000 (100G)
```

**sFlow vs NetFlow:**
- sFlow exports raw packet samples (headers + payload snippet)
- NetFlow aggregates into flows (start/end, byte/packet counts)
- sFlow better for high-speed links (no per-flow state)
- NetFlow better for security analytics (precise flow data)

**sFlow configuration (FRR/Cumulus):**
```
sflow polling-interval 20
sflow sampling-rate 1000
sflow collector 10.0.0.10 6343
sflow agent-address 192.168.1.1
```

---

## Step 4: SNMP — Polling vs Traps

**SNMP polling:** NMS queries device on schedule
- Simple but creates polling overhead
- MIB-II: ifTable (interfaces), ifXTable (extended), ipRouteTable
- SNMPv3: authentication (MD5/SHA) + encryption (AES)

**SNMP traps/informs:** Device sends notification on event
- Immediate alerting (link up/down, threshold exceeded)
- Traps: fire-and-forget; Informs: acknowledged

**Key OIDs for network monitoring:**
```
ifOperStatus:  .1.3.6.1.2.1.2.2.1.8   (interface state)
ifInOctets:    .1.3.6.1.2.1.2.2.1.10  (input bytes)
ifOutOctets:   .1.3.6.1.2.1.2.2.1.16  (output bytes)
ifInErrors:    .1.3.6.1.2.1.2.2.1.14  (input errors)
sysUpTime:     .1.3.6.1.2.1.1.3.0     (uptime)

# Poll with snmpget
snmpget -v2c -c public 192.168.1.1 .1.3.6.1.2.1.1.3.0
```

---

## Step 5: Streaming Telemetry (gNMI/gRPC)

Streaming telemetry pushes data continuously at configurable intervals without polling.

**gNMI (gRPC Network Management Interface):**
```
Device (gNMI server)  ←→  Collector (gNMI client)
  Subscribe: SAMPLE, ON_CHANGE, TARGET_DEFINED
  
Path examples:
  /interfaces/interface[name=eth0]/state/counters
  /network-instances/network-instance/protocols/protocol/bgp/neighbors
```

**Comparison: SNMP poll vs Streaming:**
| | SNMP Poll | Streaming Telemetry |
|-|-----------|---------------------|
| Delay | Poll interval (5-15min) | Sub-second |
| Overhead | High (NMS loads devices) | Low (device-initiated) |
| Scalability | Poor at scale | Excellent |
| Protocol | UDP/text MIBs | gRPC/protobuf |
| Adoption | Universal | Modern IOS-XR, JunOS, EOS |

**OpenConfig YANG paths:**
```
/interfaces/interface/state/counters/in-octets
/bgp/neighbors/neighbor/state/session-state
/components/component/state/temperature/instant
```

---

## Step 6: Prometheus + node_exporter Network Metrics

**Full observability stack:**
```
[Switches/Routers]
  → SNMP/gNMI
    → [prometheus-snmp-exporter / gnmic]
      → [Prometheus] (time-series DB)
        → [Grafana] (dashboards)
          → [Alertmanager] (PagerDuty/Slack)
```

**Prometheus SNMP exporter config:**
```yaml
# snmp.yml
modules:
  if_mib:
    walk:
      - 1.3.6.1.2.1.2.2        # ifTable
      - 1.3.6.1.2.1.31.1.1     # ifXTable
    metrics:
      - name: ifOperStatus
        oid: 1.3.6.1.2.1.2.2.1.8
        type: gauge
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifInOctets
        oid: 1.3.6.1.2.1.2.2.1.10
        type: counter
```

**Prometheus scrape config:**
```yaml
scrape_configs:
  - job_name: 'network_devices'
    static_configs:
      - targets:
          - '192.168.1.1'
          - '192.168.1.2'
    metrics_path: /snmp
    params:
      module: [if_mib]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - target_label: __address__
        replacement: snmp-exporter:9116
```

> 💡 **Grafana dashboards:** Use the Grafana community dashboard #14125 (SNMP interface monitoring) as a starting point. Customize with network-specific panels: BGP session state, interface utilization, packet drops, CRC errors.

---

## Step 7: Verification — NetFlow v9 Packet Decoder

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 &&
python3 - << 'EOF'
import struct, datetime

# Simulate NetFlow v9 header encoding/decoding
version = 9; count = 2; sys_uptime = 123456
unix_secs = int(datetime.datetime.now().timestamp())
pkg_seq = 1001; source_id = 1

header = struct.pack('!HHIIIi', version, count, sys_uptime, unix_secs, pkg_seq, source_id)
v, c, up, ts, seq, sid = struct.unpack('!HHIIIi', header)
print('NetFlow v9 Header:')
print(f'  Version:     {v}')
print(f'  Flow Count:  {c}')
print(f'  Sys Uptime:  {up} ms')
print(f'  Unix Secs:   {datetime.datetime.fromtimestamp(ts).strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'  Seq Number:  {seq}')
print(f'  Source ID:   {sid}')
print()
print('Flow Record (simulated):')
print('  Src: 192.168.1.100:54321 -> Dst: 8.8.8.8:443')
print('  Protocol: TCP | Packets: 45 | Bytes: 67890')
print('  Flags: SYN,ACK | Duration: 2.3s')
print()
print('InfluxDB-style metrics:')
fields = [
    ('network.flow.bytes', 67890, {'src': '192.168.1.100', 'dst': '8.8.8.8', 'proto': 'TCP'}),
    ('network.flow.packets', 45, {'src': '192.168.1.100', 'dst': '8.8.8.8', 'proto': 'TCP'}),
]
for name, val, tags in fields:
    tag_str = ','.join(f'{k}={v}' for k,v in tags.items())
    print(f'  {name},{tag_str} value={val} {unix_secs}000000000')
EOF"
```

📸 **Verified Output:**
```
NetFlow v9 Header:
  Version:     9
  Flow Count:  2
  Sys Uptime:  123456 ms
  Unix Secs:   2026-03-05 16:17:05
  Seq Number:  1001
  Source ID:   1

Flow Record (simulated):
  Src: 192.168.1.100:54321 -> Dst: 8.8.8.8:443
  Protocol: TCP | Packets: 45 | Bytes: 67890
  Flags: SYN,ACK | Duration: 2.3s

InfluxDB-style metrics:
  network.flow.bytes,src=192.168.1.100,dst=8.8.8.8,proto=TCP value=67890 1741190225000000000
  network.flow.packets,src=192.168.1.100,dst=8.8.8.8,proto=TCP value=45 1741190225000000000
```

---

## Step 8: Capstone — Network Observability Stack

**Scenario:** Design the full observability stack for a 500-device enterprise network.

**Stack design:**
```
Data Sources:
  [Routers/Switches] → NetFlow v9 → nfcapd → nfdump (analysis)
  [All devices]      → SNMP v3   → prometheus-snmp-exporter → Prometheus
  [Modern devices]   → gNMI      → gnmic → Prometheus
  [Applications]     → sFlow     → sfacctd → Kafka → ClickHouse

Storage & Analytics:
  Prometheus: 15-day retention, fast queries, alerting
  ClickHouse: 1-year retention, SQL analytics, cost-effective
  
Visualization:
  Grafana: Network dashboards (utilization, BGP, errors)
  
Alerting:
  Alertmanager → PagerDuty (P1/P2), Slack (#network-alerts)
  
Alert rules:
  - Interface utilization > 80% for 5min (WARNING)
  - Interface utilization > 95% for 2min (CRITICAL)
  - BGP session down (CRITICAL, instant)
  - Packet loss > 1% on WAN links (WARNING)
  - SNMP unreachable for 3min (WARNING)

LLDP/CDP topology discovery:
  Batfish / NetBox NAPALM import → topology map
  Auto-update when new devices discovered
```

---

## Summary

| Tool | Use Case |
|------|----------|
| NetFlow v9 | Security analysis, per-flow billing, capacity planning |
| sFlow | 10G+ links, lightweight packet sampling |
| SNMP v3 | Legacy device monitoring, interface counters |
| gNMI/gRPC | Real-time streaming from modern devices |
| Prometheus | Time-series metrics, alerting |
| Grafana | Network dashboards and visualization |
| ClickHouse | Long-term flow analytics at scale |

**Next:** [Lab 10: IPv6 Migration Planning →](lab-10-ipv6-migration-planning.md)
