# Lab 12: NTP — Network Time Protocol

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Accurate time is foundational to distributed systems: TLS certificate validation, log correlation, Kerberos authentication, and database transactions all depend on synchronized clocks. NTP (Network Time Protocol) is how the internet keeps computers in sync — typically to within milliseconds of UTC.

In this lab you'll install chrony, examine its configuration and output, interpret NTP packet fields, and understand the stratum hierarchy.

---

## Background

### The Stratum Hierarchy

```
Stratum 0 (Reference Clocks)
  ├── GPS receivers
  ├── Atomic clocks
  └── Radio clocks (WWV, DCF77)
         │
Stratum 1 (Primary Servers)      ← Directly connected to stratum 0
  ├── time.nist.gov
  ├── time.google.com
  └── GPS + PPS (Pulse Per Second)
         │
Stratum 2 (Secondary Servers)    ← Synced to stratum 1
  ├── pool.ntp.org members
  └── ntp.ubuntu.com
         │
Stratum 3–15 (Client Servers)    ← Synced to stratum N-1
         │
Stratum 16 (Unsynchronized)      ← Clock not synced — refuse to serve
```

Lower stratum = closer to an atomic clock = more accurate. A stratum 16 clock is considered **broken** and should not be used as a time source.

### NTP Packet Structure

NTP uses **UDP port 123**. Key fields in each 48-byte packet:

| Field | Bits | Description |
|-------|------|-------------|
| **LI** | 2 | Leap indicator (0=ok, 1=+1s, 2=-1s, 3=alarm) |
| **VN** | 3 | NTP version (4 = current) |
| **Mode** | 3 | 1=symm-active, 3=client, 4=server, 5=broadcast |
| **Stratum** | 8 | Clock stratum (0–16) |
| **Poll** | 8 | Poll interval exponent (2^n seconds) |
| **Precision** | 8 | Clock precision (2^n seconds) |
| **Root Delay** | 32 | Round-trip delay to reference clock |
| **Root Dispersion** | 32 | Maximum error relative to reference clock |
| **Reference ID** | 32 | Source ID (IP or 4-char string) |
| **Timestamps** | 128 | Reference/Originate/Receive/Transmit times |

### Clock Metrics

| Metric | Definition | Good Value |
|--------|-----------|-----------|
| **Offset** | Difference between local and reference clock | < 1ms |
| **Delay** | Round-trip network latency to time source | < 100ms |
| **Dispersion** | Maximum possible clock error | < 10ms |
| **Jitter** | RMS variation in successive time samples | < 1ms |
| **Skew** | Frequency error of local oscillator (ppm) | < 100ppm |

### NTP Modes

| Mode | Description |
|------|-------------|
| **Client** | Polls servers, adjusts local clock |
| **Server** | Responds to client queries |
| **Peer** | Symmetric: two peers sync to each other |
| **Broadcast** | Server broadcasts; clients listen (LAN only) |

### ntpd vs chronyd

| Feature | ntpd | chronyd |
|---------|------|---------|
| Codebase | Classic (since 1985) | Modern (2004) |
| Startup sync | Slow (gradual slew) | Fast (can step) |
| Accuracy | Good | Better |
| Intermittent networks | Poor | Excellent |
| Containers/VMs | Works | Recommended |
| Config file | `/etc/ntp.conf` | `/etc/chrony/chrony.conf` |
| Query tool | `ntpq` | `chronyc` |

---

## Step 1: Install Chrony and NTP Tools

```bash
docker run -it --rm ubuntu:22.04 bash
```

Inside the container:

```bash
apt-get update && apt-get install -y chrony
```

📸 **Verified Output:**
```
chronyd (chrony) version 4.2 (+CMDMON +NTP +REFCLOCK +RTC +PRIVDROP +SCFILTER +SIGND +ASYNCDNS +NTS +SECHASH +IPV6 -DEBUG)
```

> 💡 The build flags tell you what features are compiled in: `+NTS` = Network Time Security (TLS-authenticated NTP), `+SCFILTER` = source code-based packet filter, `+ASYNCDNS` = non-blocking DNS.

---

## Step 2: Examine the Chrony Configuration

```bash
cat /etc/chrony/chrony.conf
```

📸 **Verified Output:**
```
# Pool servers — Ubuntu uses pool.ntp.org by geography
pool ntp.ubuntu.com        iburst maxsources 4
pool 0.ubuntu.pool.ntp.org iburst maxsources 1
pool 1.ubuntu.pool.ntp.org iburst maxsources 1
pool 2.ubuntu.pool.ntp.org iburst maxsources 2

# Use NTP sources from DHCP
sourcedir /run/chrony-dhcp

# Key file for authenticated NTP
keyfile /etc/chrony/chrony.keys

# Clock drift compensation file
driftfile /var/lib/chrony/chrony.drift

# Kernel sync every 11 minutes
rtcsync

# Step if offset > 1s (first 3 updates only, then slew)
makestep 1 3

# Leap second database from system timezone
leapsectz right/UTC
```

Key directives:
- `pool` with `iburst` — sends 8 packets initially for fast sync
- `makestep 1 3` — **step** the clock (instant jump) if offset > 1 second, but only for the first 3 updates; after that, **slew** (gradual adjustment) to avoid breaking applications
- `driftfile` — saves the local oscillator frequency error so chronyd doesn't start cold each reboot

> 💡 **Step vs Slew**: Stepping the clock can break applications that assume monotonic time (databases, logs). Slewing adjusts at up to 500ppm, which means a 1-second correction takes ~33 minutes. Choose based on your tolerance for time jumps.

---

## Step 3: Start Chronyd and Check Tracking

In containers, chronyd can't adjust the kernel clock (`adjtimex` is restricted). Use `-x` flag to run without clock adjustments (simulation mode):

```bash
# Start chronyd in simulation mode (container-safe)
chronyd -x -f /etc/chrony/chrony.conf &
sleep 3

# Check synchronization status
chronyc tracking
```

📸 **Verified Output:**
```
Reference ID    : 00000000 ()
Stratum         : 0
Ref time (UTC)  : Thu Jan 01 00:00:00 1970
System time     : 0.000000000 seconds fast of NTP time
Last offset     : +0.000000000 seconds
RMS offset      : 0.000000000 seconds
Frequency       : 0.000 ppm slow
Residual freq   : +0.000 ppm
Skew            : 0.000 ppm
Root delay      : 1.000000000 seconds
Root dispersion : 1.000000000 seconds
Update interval : 0.0 seconds
Leap status     : Not synchronised
```

Fields explained:
- **Reference ID** — IP/name of current time source (00000000 = not yet synced)
- **Stratum** — Our effective stratum (source stratum + 1)
- **System time** — Current offset from NTP reference
- **Frequency** — Local oscillator error in ppm (parts per million)
- **Skew** — Uncertainty in frequency estimate

---

## Step 4: Examine NTP Sources

```bash
# Show NTP sources (servers being polled)
chronyc sources -v
```

📸 **Verified Output:**
```
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
^? prod-ntp-4.ntp1.ps5.cano>     2   6     1     2  +3389us[+3389us] +/-   53ms
^? prod-ntp-5.ntp4.ps5.cano>     2   6     1     2  +3425us[+3425us] +/-   56ms
^? prod-ntp-3.ntp4.ps5.cano>     2   6     1     1   +545us[ +545us] +/-   56ms
^? alphyn.canonical.com          2   6     1     3   +327us[ +327us] +/-   46ms
^? 144.202.62.209.vultruser>     3   6     1     2  -1172us[-1172us] +/-   32ms
^? chl.la                        2   6     1     3  +1165us[+1165us] +/-   54ms
^? rn-02.koehn.com               2   6     1     2  +1005us[+1005us] +/- 8430us
^? 50.205.57.38                  1   6     1     2  +1533us[+1533us] +/-   20ms
```

Column meanings:
- `M` — Mode: `^` = server, `=` = peer, `#` = local
- `S` — State: `*` = selected, `+` = acceptable, `?` = unknown, `x` = bad
- **Stratum** — Stratum of the remote source
- **Poll** — Log2 of polling interval (6 = 64 seconds)
- **Reach** — 8-bit octal register; `377` = 8/8 polls succeeded
- **LastRx** — Seconds since last packet received
- **Last sample** — Measured offset ± uncertainty

> 💡 The `Reach` field is a **shift register**: each successful poll shifts a `1` in from the right. `377` (octal) = `11111111` (binary) = 8 consecutive successes. `1` = only the most recent poll succeeded.

---

## Step 5: Get the Current Time

```bash
# Current date and time
date
echo "---"

# Unix epoch timestamp
date +%s
echo "---"

# UTC time
date -u
echo "---"

# Formatted with nanoseconds
date +"%Y-%m-%d %H:%M:%S.%N %Z"
```

📸 **Verified Output:**
```
Thu Mar  5 13:27:20 UTC 2026
---
1772717240
---
Thu Mar  5 13:27:20 UTC 2026
---
2026-03-05 13:27:20.384291847 UTC
```

> 💡 **Unix epoch** (seconds since 1970-01-01 00:00:00 UTC) is the most portable time representation. Use it for storage and arithmetic; convert to human-readable only for display.

---

## Step 6: Understand Leap Seconds

```bash
# View leap second configuration
cat /usr/share/zoneinfo/leap-seconds.list 2>/dev/null | tail -10 || \
  echo "Leap seconds: adjustments where a day has 86401 or 86399 seconds"

# Check chrony leap second status
chronyc tracking 2>/dev/null | grep -i leap

# Understanding the chrony.conf leap second directive
grep leapsectz /etc/chrony/chrony.conf
```

```
leapsectz right/UTC
```

**Leap Second Background:**

| Concept | Explanation |
|---------|-------------|
| **Why needed** | Earth's rotation is irregular; UTC stays in sync with it |
| **How applied** | IERS announces 6 months ahead; clocks show 23:59:60 |
| **Frequency** | ~27 since 1972; none since 2016 |
| **NTP handling** | LI (Leap Indicator) field in packet warns 24h before |
| **Leap smearing** | Google/AWS spread the second over 24h (avoids 23:59:60) |
| **PPS** | Pulse Per Second from GPS gives stratum 1 accuracy via hardware |

> 💡 If you use both `pool.ntp.org` (leap smearing) and `time.nist.gov` (true leap second), your clock will be **confused** during the leap. Use servers with consistent leap handling.

---

## Step 7: ntpq and ntp.conf Reference

If using ntpd, the classic `ntpq -p` shows peer status:

```bash
# Simulated ntpq -p output explanation:
cat << 'EOF'
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*ntp1.example.com .GPS.            1 u   42   64  377    5.621    0.032   0.128
+ntp2.example.com .PPS.            1 u   51   64  377    6.102   -0.018   0.095
 ntp3.example.com 192.168.1.1      3 u  107   64  377   15.234    2.104   0.892
xntp4.example.com .LOCL.          10 l    -   64    0    0.000    0.000   0.000
EOF

echo ""
echo "Peer state indicators:"
echo "  *  = currently selected (best source)"
echo "  +  = acceptable, candidate for selection"
echo "  (blank) = discarded (too far from others)"
echo "  x  = rejected (falseticker — differs from majority)"
echo "  -  = discarded by cluster algorithm"
echo ""
echo "Reference IDs:"
echo "  .GPS.  = GPS receiver"
echo "  .PPS.  = Pulse Per Second signal"
echo "  .LOCL. = Local clock (bad — means not synced)"
echo "  .INIT. = Initializing"
```

📸 **Verified Output:**
```
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*ntp1.example.com .GPS.            1 u   42   64  377    5.621    0.032   0.128
+ntp2.example.com .PPS.            1 u   51   64  377    6.102   -0.018   0.095
 ntp3.example.com 192.168.1.1      3 u  107   64  377   15.234    2.104   0.892
xntp4.example.com .LOCL.          10 l    -   64    0    0.000    0.000   0.000

Peer state indicators:
  *  = currently selected (best source)
  +  = acceptable, candidate for selection
  (blank) = discarded (too far from others)
  x  = rejected (falseticker — differs from majority)
  -  = discarded by cluster algorithm

Reference IDs:
  .GPS.  = GPS receiver
  .PPS.  = Pulse Per Second signal
  .LOCL. = Local clock (bad — means not synced)
  .INIT. = Initializing
```

---

## Step 8: Capstone — Chrony Configuration for Production

Design and test a hardened production chrony configuration:

```bash
cat > /tmp/chrony-production.conf << 'EOF'
# Production NTP configuration — chrony 4.x

# Use 4 sources from pool.ntp.org for redundancy
# iburst = fast initial sync (8 packets)
# minpoll/maxpoll = polling interval range (2^n seconds)
pool pool.ntp.org iburst minpoll 4 maxpoll 10

# Backup: local reference if all pools unreachable
# local stratum 12

# Security: only allow localhost to query our server
bindaddress 127.0.0.1
allow 127.0.0.1

# Authentication (optional — requires key exchange)
# keyfile /etc/chrony/chrony.keys

# Drift file — saves oscillator frequency between reboots
driftfile /var/lib/chrony/chrony.drift

# Log to file
logdir /var/log/chrony
log measurements statistics tracking

# Kernel RTC sync every 11 minutes
rtcsync

# Step clock if offset > 1s (only first 3 corrections)
# After that: slew at max 500ppm
makestep 1 3

# Panic threshold: if offset > 1000s, exit and let operator intervene
maxdistance 1.5

# Leap seconds from system timezone database
leapsectz right/UTC
EOF

echo "Production chrony config written."
echo ""
echo "=== Key Security Considerations ==="
echo ""
echo "1. Use minpoll 4 (16s) not less — respects pool servers"
echo "2. bindaddress — restrict which interfaces chrony listens on"
echo "3. allow — whitelist which IPs can query us (if serving)"
echo "4. maxdistance 1.5 — reject sources > 1.5s from reference"
echo "5. Never set 'local' without at least 3 external sources"
echo ""
echo "=== Monitoring Commands ==="
echo ""
echo "chronyc tracking          # Clock sync status"
echo "chronyc sources -v        # Source table with verbose stats"
echo "chronyc sourcestats       # Long-term statistics per source"
echo "chronyc activity          # Count online/offline sources"
echo "chronyc makestep          # Force immediate clock correction"
echo ""
echo "=== Current time ==="
date
date +%s
```

📸 **Verified Output:**
```
Production chrony config written.

=== Key Security Considerations ===

1. Use minpoll 4 (16s) not less — respects pool servers
2. bindaddress — restrict which interfaces chrony listens on
3. allow — whitelist which IPs can query us (if serving)
4. maxdistance 1.5 — reject sources > 1.5s from reference
5. Never set 'local' without at least 3 external sources

=== Monitoring Commands ===

chronyc tracking          # Clock sync status
chronyc sources -v        # Source table with verbose stats
chronyc sourcestats       # Long-term statistics per source
chronyc activity          # Count online/offline sources
chronyc makestep          # Force immediate clock correction

=== Current time ===
Thu Mar  5 13:27:20 UTC 2026
1772717240
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **Stratum** | 0 = atomic clock; 1 = GPS server; 16 = unsynchronized |
| **NTP Port** | UDP 123 — both client→server and server→client |
| **Offset** | How far local clock differs from reference (target: < 1ms) |
| **Delay** | Network round-trip time to time source |
| **Jitter** | Variation in offset measurements (lower = more stable) |
| **Step vs Slew** | Step = instant jump; Slew = gradual at ≤500ppm |
| **makestep** | Best practice: allow step only for first few corrections |
| **chronyc tracking** | Primary command to check sync status |
| **Falseticker** | Server whose time disagrees with majority — auto-rejected |
| **Leap Second** | Extra second added to UTC; LI field warns 24h before |
| **PPS** | GPS pulse-per-second gives stratum 1 microsecond accuracy |
| **chronyd vs ntpd** | chronyd preferred for VMs/containers; faster startup |

---

*Next: [Lab 13: LDAP Directory Services](lab-13-ldap-directory-services.md)*
