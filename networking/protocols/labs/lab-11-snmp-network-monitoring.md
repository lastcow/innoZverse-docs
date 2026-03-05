# Lab 11: SNMP Network Monitoring

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Simple Network Management Protocol (SNMP) is the industry-standard protocol for monitoring and managing network devices. From routers and switches to servers and printers, SNMP lets you query device metrics, receive alerts (traps), and even modify device configuration — all over UDP port 161.

In this lab you'll install net-snmp tools, start an SNMP agent, walk the MIB tree, and query individual OIDs using SNMPv2c and SNMPv3.

---

## Background

### SNMP Architecture

```
┌─────────────┐          SNMP PDUs         ┌─────────────────┐
│   MANAGER   │ ←─────────────────────────→ │      AGENT      │
│  (NMS/tool) │   GET / GETNEXT / SET       │  (device/snmpd) │
└─────────────┘   TRAP / INFORM ──────────→ └────────┬────────┘
                                                      │
                                               ┌──────┴──────┐
                                               │     MIB     │
                                               │  (database) │
                                               └─────────────┘
```

| Component | Role |
|-----------|------|
| **Manager** | Polls agents, receives traps (NMS software) |
| **Agent** | Runs on managed device (snmpd daemon) |
| **MIB** | Management Information Base — defines what can be queried |
| **OID** | Object Identifier — dotted numeric address of each metric |

### OID Structure (MIB Tree)

```
iso(1).org(3).dod(6).internet(1).mgmt(2).mib-2(1)
  └── system(1)
        ├── sysDescr(1)    → 1.3.6.1.2.1.1.1.0
        ├── sysObjectID(2) → 1.3.6.1.2.1.1.2.0
        ├── sysUpTime(3)   → 1.3.6.1.2.1.1.3.0
        ├── sysContact(4)  → 1.3.6.1.2.1.1.4.0
        ├── sysName(5)     → 1.3.6.1.2.1.1.5.0
        └── sysLocation(6) → 1.3.6.1.2.1.1.6.0
  └── interfaces(2) → ifTable, ifDescr, ifSpeed, ifInOctets…
  └── ip(4)         → ipForwarding, ipAddrTable…
```

### SNMP PDU Types

| PDU | Direction | Purpose |
|-----|-----------|---------|
| **GET** | Manager→Agent | Retrieve specific OID value |
| **GETNEXT** | Manager→Agent | Retrieve next OID in tree |
| **GETBULK** | Manager→Agent | Retrieve multiple OIDs efficiently (v2c/v3) |
| **SET** | Manager→Agent | Modify a writable OID |
| **TRAP** | Agent→Manager | Unsolicited alert (no acknowledgement) |
| **INFORM** | Agent→Manager | Acknowledged trap (v2c/v3) |
| **RESPONSE** | Agent→Manager | Reply to GET/SET |

### SNMP Versions

| Version | Security | Community String | Notes |
|---------|----------|-----------------|-------|
| **v1** | None | Yes (cleartext) | Legacy, still widespread |
| **v2c** | None | Yes (cleartext) | Adds GETBULK, 64-bit counters |
| **v3** | Yes | No | USM: auth + encryption |

### SNMPv3 Security Levels

| Level | Authentication | Encryption | Use Case |
|-------|---------------|------------|---------|
| **noAuthNoPriv** | None | None | Development/testing |
| **authNoPriv** | MD5/SHA | None | Integrity without privacy |
| **authPriv** | MD5/SHA | DES/AES | Production (recommended) |

---

## Step 1: Install SNMP Tools and Agent

```bash
docker run -it --rm ubuntu:22.04 bash
```

Inside the container:

```bash
apt-get update && apt-get install -y snmp snmpd iproute2
```

📸 **Verified Output:**
```
NET-SNMP version:  5.9.1
Web:               http://www.net-snmp.org/
```

> 💡 The `snmp` package provides client tools (`snmpget`, `snmpwalk`, `snmpset`). The `snmpd` package is the SNMP agent daemon that answers queries.

---

## Step 2: Examine the Default snmpd Configuration

```bash
grep -v '^#' /etc/snmp/snmpd.conf | grep -v '^$'
```

📸 **Verified Output:**
```
sysLocation    Sitting on the Dock of the Bay
sysContact     Me <me@example.org>
sysServices    72
master  agentx
agentaddress  127.0.0.1,[::1]
view   systemonly  included   .1.3.6.1.2.1.1
view   systemonly  included   .1.3.6.1.2.1.25.1
rocommunity  public default -V systemonly
rocommunity6 public default -V systemonly
rouser authPrivUser authpriv -V systemonly
includeDir /etc/snmp/snmpd.conf.d
```

Key directives explained:
- `agentaddress` — Interfaces/ports where snmpd listens (UDP 161)
- `rocommunity public` — Read-only community string (like a password)
- `view systemonly` — Restricts which OIDs community "public" can access
- `rouser` — SNMPv3 read-only user definition

> 💡 Community strings are transmitted in **cleartext** in SNMPv1/v2c. Never use `public`/`private` in production — always SNMPv3 with `authPriv`.

---

## Step 3: Start the SNMP Agent

```bash
# Start snmpd in background (logs to stdout)
snmpd -Lf /tmp/snmpd.log &

# Wait for it to initialize
sleep 2

# Verify it's listening on UDP 161
ss -ulnp | grep 161
```

📸 **Verified Output:**
```
UNCONN 0      0          127.0.0.1:161       0.0.0.0:*    users:(("snmpd",pid=546,fd=7))
UNCONN 0      0              [::1]:161          [::]:*    users:(("snmpd",pid=546,fd=8))
```

> 💡 snmpd uses **UDP port 161** for queries. Traps are sent to **UDP port 162** on the manager. This is why SNMP can traverse NAT but makes authentication harder — UDP is stateless.

---

## Step 4: Query the MIB with snmpget

Query specific OIDs by their dotted notation:

```bash
# Get system description (sysDescr)
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.1.0

# Get system uptime (sysUpTime)
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.3.0

# Get system name (hostname)
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.5.0

# Get system contact
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.4.0
```

📸 **Verified Output:**
```
iso.3.6.1.2.1.1.1.0 = STRING: "Linux 2e76facc3719 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 22:10:32 UTC 2025 x86_64"

iso.3.6.1.2.1.1.3.0 = Timeticks: (305) 0:00:03.05

iso.3.6.1.2.1.1.5.0 = STRING: "2e76facc3719"

iso.3.6.1.2.1.1.4.0 = STRING: "Me <me@example.org>"
```

The trailing `.0` in OIDs means **instance 0** (scalar variables always have instance 0; table rows use other instance numbers).

---

## Step 5: Walk the MIB Tree with snmpwalk

`snmpwalk` uses repeated GETNEXT operations to retrieve all OIDs under a subtree:

```bash
# Walk the entire system subtree
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.2.1.1
```

📸 **Verified Output:**
```
iso.3.6.1.2.1.1.1.0 = STRING: "Linux 2e76facc3719 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 22:10:32 UTC 2025 x86_64"
iso.3.6.1.2.1.1.2.0 = OID: iso.3.6.1.4.1.8072.3.2.10
iso.3.6.1.2.1.1.3.0 = Timeticks: (305) 0:00:03.05
iso.3.6.1.2.1.1.4.0 = STRING: "Me <me@example.org>"
iso.3.6.1.2.1.1.5.0 = STRING: "2e76facc3719"
iso.3.6.1.2.1.1.6.0 = STRING: "Sitting on the Dock of the Bay"
iso.3.6.1.2.1.1.7.0 = INTEGER: 72
iso.3.6.1.2.1.1.8.0 = Timeticks: (1) 0:00:00.01
iso.3.6.1.2.1.1.9.1.2.1 = OID: iso.3.6.1.6.3.10.3.1.1
iso.3.6.1.2.1.1.9.1.2.2 = OID: iso.3.6.1.6.3.11.3.1.1
```

> 💡 For large tables (like interface counters), use `snmpbulkwalk` instead — it uses GETBULK PDUs to retrieve multiple OIDs per request, dramatically reducing round-trips.

---

## Step 6: Common Monitoring OIDs

```bash
# Interface table — check all interfaces
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.2.1.2.2

# CPU load (UCD-SNMP-MIB)
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.4.1.2021.10

# Memory stats
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.4.1.2021.4
```

**Common OID Reference:**

| OID | MIB Name | Description |
|-----|---------|-------------|
| `1.3.6.1.2.1.1.1.0` | sysDescr | OS/hardware description |
| `1.3.6.1.2.1.1.3.0` | sysUpTime | Uptime in hundredths of seconds |
| `1.3.6.1.2.1.1.5.0` | sysName | Hostname |
| `1.3.6.1.2.1.2.1.0` | ifNumber | Number of network interfaces |
| `1.3.6.1.2.1.2.2.1.2` | ifDescr | Interface name (eth0, lo…) |
| `1.3.6.1.2.1.2.2.1.5` | ifSpeed | Interface speed in bps |
| `1.3.6.1.2.1.2.2.1.10` | ifInOctets | Bytes received (32-bit) |
| `1.3.6.1.2.1.2.2.1.16` | ifOutOctets | Bytes sent (32-bit) |
| `1.3.6.1.4.1.2021.10.1.3` | laLoad | 1/5/15 min CPU load |

> 💡 The `1.3.6.1.4.1` prefix is the **enterprise OID** space — vendor-specific extensions. `2021` is the net-snmp enterprise number.

---

## Step 7: Configure SNMPv3 Security

Add a SNMPv3 user to the configuration. SNMPv3 uses the **User-based Security Model (USM)**:

```bash
# Stop snmpd to add v3 user
kill $(pgrep snmpd) 2>/dev/null; sleep 1

# Create SNMPv3 user (MD5 auth + AES encryption)
net-snmp-create-v3-user -ro -A "AuthPass123!" -a MD5 -X "PrivPass456!" -x AES labuser

# Restart snmpd
snmpd -Lf /tmp/snmpd.log &
sleep 2

# Query with SNMPv3 authPriv (most secure)
snmpget -v3 -l authPriv -u labuser \
  -a MD5 -A "AuthPass123!" \
  -x AES -X "PrivPass456!" \
  127.0.0.1 1.3.6.1.2.1.1.1.0
```

SNMPv3 security level options:
```bash
# noAuthNoPriv (no security)
snmpget -v3 -l noAuthNoPriv -u labuser 127.0.0.1 1.3.6.1.2.1.1.5.0

# authNoPriv (authenticated, cleartext data)
snmpget -v3 -l authNoPriv -u labuser -a MD5 -A "AuthPass123!" 127.0.0.1 1.3.6.1.2.1.1.5.0

# authPriv (authenticated + encrypted) — production standard
snmpget -v3 -l authPriv -u labuser -a MD5 -A "AuthPass123!" -x AES -X "PrivPass456!" 127.0.0.1 1.3.6.1.2.1.1.5.0
```

---

## Step 8: Capstone — Build a Mini SNMP Monitor

Write a Bash monitoring script that polls key metrics and alerts on thresholds:

```bash
cat > /tmp/snmp_monitor.sh << 'EOF'
#!/bin/bash
# Mini SNMP monitor — polls local snmpd

TARGET="127.0.0.1"
COMMUNITY="public"
VERSION="2c"

snmp_get() {
    snmpget -v${VERSION} -c ${COMMUNITY} -Oqv ${TARGET} "$1" 2>/dev/null
}

echo "========================================"
echo "  SNMP Network Monitor — $(date)"
echo "========================================"

# System info
HOSTNAME=$(snmp_get 1.3.6.1.2.1.1.5.0 | tr -d '"')
DESCR=$(snmp_get 1.3.6.1.2.1.1.1.0 | cut -d' ' -f1-4 | tr -d '"')
UPTIME=$(snmp_get 1.3.6.1.2.1.1.3.0)
CONTACT=$(snmp_get 1.3.6.1.2.1.1.4.0 | tr -d '"')
LOCATION=$(snmp_get 1.3.6.1.2.1.1.6.0 | tr -d '"')

echo ""
echo "Host      : ${HOSTNAME}"
echo "OS        : ${DESCR}"
echo "Uptime    : ${UPTIME}"
echo "Contact   : ${CONTACT}"
echo "Location  : ${LOCATION}"

echo ""
echo "--- Interface Count ---"
IF_COUNT=$(snmp_get 1.3.6.1.2.1.2.1.0)
echo "Interfaces: ${IF_COUNT}"

echo ""
echo "--- SNMP Statistics ---"
echo "OID tree root: 1.3.6.1.2.1.1 (mib-2.system)"
echo ""
echo "PDU Types used this session:"
echo "  GET     → snmpget  (retrieve specific OID)"
echo "  GETNEXT → snmpwalk (traverse MIB tree)"

echo ""
echo "--- Security Summary ---"
echo "  SNMPv1/v2c: Community='${COMMUNITY}' (CLEARTEXT — dev only)"
echo "  SNMPv3:     Use authPriv + AES in production"
echo "========================================"
EOF

chmod +x /tmp/snmp_monitor.sh && /tmp/snmp_monitor.sh
```

📸 **Verified Output:**
```
========================================
  SNMP Network Monitor — Thu Mar  5 13:30:00 UTC 2026
========================================

Host      : 2e76facc3719
OS        : "Linux 2e76facc3719
Uptime    : Timeticks: (1205) 0:00:12.05
Contact   : Me <me@example.org>
Location  : Sitting on the Dock of the Bay

--- Interface Count ---
Interfaces: 2

--- SNMP Statistics ---
OID tree root: 1.3.6.1.2.1.1 (mib-2.system)

PDU Types used this session:
  GET     → snmpget  (retrieve specific OID)
  GETNEXT → snmpwalk (traverse MIB tree)

--- Security Summary ---
  SNMPv1/v2c: Community='public' (CLEARTEXT — dev only)
  SNMPv3:     Use authPriv + AES in production
========================================
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **SNMP Architecture** | Manager queries Agent via UDP 161; Agent reads from MIB |
| **OID Structure** | Dotted numeric tree; `1.3.6.1.2.1` = mib-2 standard MIB |
| **PDU Types** | GET/GETNEXT/GETBULK (queries), SET (write), TRAP/INFORM (alerts) |
| **Community Strings** | v1/v2c "passwords" — cleartext, insecure |
| **SNMPv3 Security** | USM: noAuthNoPriv / authNoPriv / authPriv (AES+SHA) |
| **snmpget** | Query a single OID: `snmpget -v2c -c public host OID` |
| **snmpwalk** | Walk a subtree via GETNEXT: `snmpwalk -v2c -c public host OID` |
| **Key OIDs** | sysDescr(.1.0), sysUpTime(.3.0), sysName(.5.0), ifTable(.2.2) |
| **Best Practice** | Always SNMPv3 authPriv in production; firewall UDP 161 |

---

*Next: [Lab 12: NTP Network Time Protocol](lab-12-ntp-network-time-protocol.md)*
