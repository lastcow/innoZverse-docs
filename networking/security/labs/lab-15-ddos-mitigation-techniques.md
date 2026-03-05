# Lab 15: DDoS Mitigation Techniques

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Distributed Denial of Service (DDoS) attacks attempt to exhaust server resources — bandwidth, connection tables, or application threads — to deny service to legitimate users. This lab covers SYN flood mitigation with kernel SYN cookies, iptables rate limiting, connection tracking, null routing (blackhole routing), and fail2ban for application-layer defence — all verified with real Docker output.

---

## Step 1 — DDoS Attack Taxonomy

```
┌─────────────────────────────────────────────────────────┐
│                    DDoS Attack Types                    │
├───────────────────┬─────────────────┬───────────────────┤
│  Layer 3/4        │  Layer 4        │  Layer 7          │
│  (Volumetric)     │  (Protocol)     │  (Application)    │
├───────────────────┼─────────────────┼───────────────────┤
│ UDP flood         │ SYN flood       │ HTTP GET/POST flood│
│ ICMP flood        │ ACK flood       │ Slowloris         │
│ DNS amplification │ RST flood       │ SSL renegotiation │
│ NTP amplification │ Ping of Death   │ CC attack         │
│ Memcached amp.    │ Land attack     │ API abuse         │
└───────────────────┴─────────────────┴───────────────────┘
```

| Attack Type | Target Resource | Mitigation Layer |
|-------------|----------------|-----------------|
| Volumetric | Bandwidth | Upstream scrubbing/CDN |
| Protocol (SYN flood) | Connection table | SYN cookies, rate limits |
| Application (HTTP flood) | CPU/memory/threads | WAF, fail2ban, limits |

---

## Step 2 — Install Tools

```bash
apt-get update -qq && apt-get install -y iptables iproute2 netcat-openbsd
```

📸 **Verified Output:**
```
Setting up iptables (1.8.7-1ubuntu5.2) ...
Setting up iproute2 (5.15.0-1ubuntu2) ...
```

---

## Step 3 — SYN Flood Mitigation with SYN Cookies

A SYN flood exhausts the half-open connection table by sending millions of SYN packets without completing the 3-way handshake.

### Check SYN Cookies Status

```bash
sysctl net.ipv4.tcp_syncookies
```

📸 **Verified Output:**
```
net.ipv4.tcp_syncookies = 1
```

### Enable SYN Cookies (if not already active)

```bash
# Enable immediately (no reboot required)
sysctl -w net.ipv4.tcp_syncookies=1

# Make persistent across reboots
echo 'net.ipv4.tcp_syncookies = 1' >> /etc/sysctl.conf
sysctl -p /etc/sysctl.conf

# Additional SYN flood hardening
sysctl -w net.ipv4.tcp_syn_retries=2          # Fewer SYN retries
sysctl -w net.ipv4.tcp_synack_retries=2       # Fewer SYN-ACK retries
sysctl -w net.ipv4.tcp_max_syn_backlog=4096   # Larger backlog queue
```

### How SYN Cookies Work

```
Normal 3-way handshake:
  Client ──[SYN]──────────────────→ Server (allocates state)
  Client ←─[SYN-ACK]────────────── Server
  Client ──[ACK]──────────────────→ Server (connection established)

SYN Cookie (no state allocated until ACK received):
  Client ──[SYN]──────────────────→ Server
  Server encodes ISN = f(src_ip, src_port, dst_ip, dst_port, secret)
  Client ←─[SYN-ACK, ISN=cookie]── Server (NO state stored!)
  Client ──[ACK, ISN+1]───────────→ Server (validates cookie, THEN allocates)
```

> 💡 **Tip:** SYN cookies sacrifice some TCP options (SACK, window scaling) but allow the server to survive SYN floods without table exhaustion. The kernel auto-activates cookies when the backlog is full, even without `tcp_syncookies=1`.

---

## Step 4 — iptables Rate Limiting

### SYN Rate Limiting with --limit module

```bash
# Accept SYN packets at 1/second with burst of 3
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT

# Drop all remaining SYN packets (those exceeding the rate)
iptables -A INPUT -p tcp --syn -j DROP

# Verify rules
iptables -L INPUT -v -n
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp flags:0x17/0x02 limit: avg 1/sec burst 3
    0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp flags:0x17/0x02
```

### Hashlimit Module (per-source rate limiting)

The `hashlimit` module tracks rates **per source IP** — far more effective than global `--limit`:

```bash
# Allow max 10 new connections per second per source IP
iptables -A INPUT -p tcp --syn \
  -m hashlimit \
  --hashlimit-name syn_rate \
  --hashlimit-above 10/sec \
  --hashlimit-burst 20 \
  --hashlimit-mode srcip \
  -j DROP

# Rate limit ICMP (anti-ping flood)
iptables -A INPUT -p icmp \
  -m hashlimit \
  --hashlimit-name icmp_rate \
  --hashlimit-above 1/sec \
  --hashlimit-burst 5 \
  --hashlimit-mode srcip \
  -j DROP
```

> 💡 **Tip:** The `--limit` module applies a **global** token bucket. Use `hashlimit --hashlimit-mode srcip` to rate-limit **per attacker IP** — this prevents one source from consuming the global budget.

---

## Step 5 — Connection Tracking Limits

```bash
# View current connection tracking table
cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null || echo "0 (module not loaded)"
cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null || echo "65536 (default)"

# Increase conntrack table size
sysctl -w net.netfilter.nf_conntrack_max=131072

# Reduce timeouts to expire stale entries faster
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_sent=10
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600

# Limit connections per IP with iptables connlimit
iptables -A INPUT -p tcp --dport 80 \
  -m connlimit --connlimit-above 50 --connlimit-mask 32 \
  -j REJECT --reject-with tcp-reset
```

### Monitor Connection Stats with ss

```bash
ss -s
```

📸 **Verified Output:**
```
Total: 5
TCP:   46 (estab 0, closed 46, orphaned 1, timewait 3)

Transport Total     IP        IPv6
RAW	  0         0         0        
UDP	  0         0         0        
TCP	  0         0         0        
INET	  0         0         0        
FRAG	  0         0         0        
```

```bash
# During attack: watch TIME_WAIT states accumulate
watch -n1 'ss -an | grep -c TIME_WAIT'

# Show top connection sources
ss -an | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

---

## Step 6 — Null Routing (Blackhole Routing)

When an attacker's source IP is known, null routing drops traffic at the **routing layer** — more efficient than iptables (no rule evaluation):

```bash
# Blackhole a single attacking IP
ip route add blackhole 192.168.100.5/32

# Blackhole an entire attacking subnet
ip route add blackhole 192.168.100.0/24

# Verify blackhole routes
ip route show type blackhole
```

📸 **Verified Output:**
```
blackhole 192.168.100.0/24
```

```bash
# Remove blackhole route when attack subsides
ip route del blackhole 192.168.100.0/24

# RTBH (Remote Triggered Black Hole) — BGP-based null routing
# Announce victim IP with community 666 to upstream ISP:
# ip route add 203.0.113.10/32 via 192.0.2.1 tag 666
```

> 💡 **Tip:** For volumetric attacks exceeding your uplink capacity, RTBH (Remote Triggered Black Hole) routing via BGP community `666` instructs your upstream ISP to drop traffic **before it reaches your network**. This is the only effective mitigation for >10Gbps floods.

---

## Step 7 — fail2ban for Application-Layer Protection

fail2ban monitors log files and automatically blocks IPs that exhibit attack patterns:

```bash
apt-get install -y fail2ban 2>/dev/null

# Show default jail configuration structure
cat /etc/fail2ban/jail.conf | grep -A5 '\[DEFAULT\]' | head -15

# Create custom jail for HTTP flood
cat > /etc/fail2ban/jail.d/http-flood.conf << 'EOF'
[http-flood]
enabled  = true
port     = http,https
filter   = http-flood
logpath  = /var/log/nginx/access.log
maxretry = 100
findtime = 60
bantime  = 3600
action   = iptables-multiport[name=HTTP, port="http,https", protocol=tcp]
EOF

# Create matching filter
mkdir -p /etc/fail2ban/filter.d
cat > /etc/fail2ban/filter.d/http-flood.conf << 'EOF'
[Definition]
failregex = ^<HOST> - .* "(GET|POST|HEAD) .*" (200|404|301|302)
ignoreregex =
EOF

echo "fail2ban config created"
ls /etc/fail2ban/jail.d/
```

```bash
# fail2ban-client commands
fail2ban-client status                    # Show all active jails
fail2ban-client status http-flood        # Show banned IPs for jail
fail2ban-client set http-flood unbanip 1.2.3.4   # Unban an IP
fail2ban-client set http-flood banip 1.2.3.4      # Manually ban
```

> 💡 **Tip:** Set `bantime = -1` for permanent bans of known malicious IPs. Use `findtime` (observation window) and `maxretry` to tune sensitivity — lower `findtime` catches faster floods but may miss slow, distributed HTTP attacks.

---

## Step 8 — Capstone: Multi-Layer DDoS Defence Configuration

**Deploy a complete defence stack:**

```bash
#!/bin/bash
# Complete DDoS mitigation hardening script

echo "=== Step 1: SYN Cookie hardening ==="
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_syn_retries=2
sysctl -w net.ipv4.tcp_synack_retries=2
sysctl -w net.ipv4.tcp_max_syn_backlog=4096
echo "SYN cookies: $(sysctl -n net.ipv4.tcp_syncookies)"

echo ""
echo "=== Step 2: iptables rate limiting ==="
# Flush existing rules
iptables -F INPUT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Rate limit new TCP connections (per source IP)
iptables -A INPUT -p tcp --syn \
  -m hashlimit \
  --hashlimit-name conn_rate \
  --hashlimit-above 20/min \
  --hashlimit-burst 5 \
  --hashlimit-mode srcip \
  -j DROP

# SYN global rate limit
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# ICMP rate limit
iptables -A INPUT -p icmp --icmp-type echo-request \
  -m limit --limit 1/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

echo ""
iptables -L INPUT -v -n

echo ""
echo "=== Step 3: Null route known attack sources ==="
ip route add blackhole 10.0.0.0/8 2>/dev/null && \
  echo "Blackholed: 10.0.0.0/8"
ip route show type blackhole

echo ""
echo "=== Step 4: Connection stats ==="
ss -s

echo ""
echo "=== Mitigation stack active ==="
```

📸 **Verified Output (key sections):**
```
=== Step 1: SYN Cookie hardening ===
net.ipv4.tcp_syncookies = 1
SYN cookies: 1

=== Step 2: iptables rate limiting ===
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0           
    0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp flags:0x17/0x02 ... limit: avg 20/min burst 5
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp flags:0x17/0x02 limit: avg 1/sec burst 3
    0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp flags:0x17/0x02
    0     0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            limit: avg 1/sec burst 5
    0     0 DROP       icmp --  *      *       0.0.0.0/0            0.0.0.0/0           

=== Step 3: Null route known attack sources ===
blackhole 10.0.0.0/8

=== Step 4: Connection stats ===
Total: 5
TCP: 46 (estab 0, closed 46, orphaned 1, timewait 3)
```

---

## DDoS Defence Architecture

```
Internet
    │
    ▼
┌───────────────────────────────────────────┐
│  CDN / Scrubbing Centre (Cloudflare, etc) │  ← Absorbs volumetric attacks
│  BGP Anycast / RTBH                       │  ← Upstream null routing
└───────────────────────┬───────────────────┘
                        │ Clean traffic only
                        ▼
┌───────────────────────────────────────────┐
│  Edge Router / Firewall                   │
│  - BPF/XDP filtering (kernel bypass)      │  ← Sub-microsecond drop
│  - ip route blackhole <attacker>          │  ← Null routing
└───────────────────────┬───────────────────┘
                        ▼
┌───────────────────────────────────────────┐
│  iptables / nftables                      │
│  - SYN rate limiting (hashlimit)          │  ← Per-source rate control
│  - connlimit (max connections per IP)     │
│  - conntrack state validation             │
└───────────────────────┬───────────────────┘
                        ▼
┌───────────────────────────────────────────┐
│  Kernel TCP Stack                         │
│  - tcp_syncookies=1                       │  ← No state SYN handling
│  - tcp_max_syn_backlog=4096               │
└───────────────────────┬───────────────────┘
                        ▼
┌───────────────────────────────────────────┐
│  Application Layer                        │
│  - fail2ban (log-based ban)               │  ← HTTP flood blocking
│  - nginx connection limits                │
│  - WAF (ModSecurity/Cloudflare rules)     │
└───────────────────────────────────────────┘
```

---

## Summary

| Technique | Tool/Command | Attack Type |
|-----------|-------------|-------------|
| SYN cookies | `sysctl net.ipv4.tcp_syncookies=1` | SYN flood |
| Global SYN rate limit | `iptables --limit 1/s --limit-burst 3` | SYN flood |
| Per-IP rate limit | `iptables -m hashlimit --hashlimit-mode srcip` | Distributed flood |
| Connection limit | `iptables -m connlimit --connlimit-above 50` | HTTP flood |
| Null routing | `ip route add blackhole <IP>` | All types |
| BGP RTBH | Upstream ISP routing community 666 | Volumetric |
| fail2ban | `fail2ban-client status <jail>` | Application layer |
| Connection stats | `ss -s` | Monitoring |
| Watch TIME_WAIT | `watch ss -an | grep -c TIME_WAIT` | SYN/TCP flood |
| BPF/XDP filtering | eBPF programs at NIC driver level | High-rate floods |
| CDN scrubbing | Cloudflare / AWS Shield / Akamai | Volumetric |
