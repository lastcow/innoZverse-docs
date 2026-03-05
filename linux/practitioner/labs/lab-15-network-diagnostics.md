# Lab 15: Network Diagnostics

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

This lab covers the essential toolkit for diagnosing network problems: testing connectivity with `ping`, tracing packet paths with `traceroute`/`tracepath`, resolving DNS with `dig`/`nslookup`, inspecting socket states with `ss`, testing ports with `netcat`, and profiling HTTP with `curl` timing.

---

## Step 1: ping — Testing Connectivity

```bash
apt-get update -qq && apt-get install -y iputils-ping

# Basic ping (3 packets)
ping -c 3 8.8.8.8

# Ping with timeout and interval
ping -c 5 -W 2 -i 0.5 8.8.8.8

# Ping by hostname
ping -c 2 google.com
```

> 💡 Flags: `-c N` = send N packets (without it, ping runs forever); `-W N` = wait N seconds for each reply (timeout); `-i N` = interval between packets in seconds. RTT (round-trip time) in ms tells you latency. Packet loss % shows reliability. No response could mean: host down, firewall blocking ICMP, or routing failure.

📸 **Verified Output:**
```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=2.03 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=1.94 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=1.36 ms

--- 8.8.8.8 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
rtt min/avg/max/mdev = 1.363/1.779/2.031/0.296 ms
```

---

## Step 2: traceroute — Path Discovery

`traceroute` reveals every router hop between you and a destination.

```bash
apt-get update -qq && apt-get install -y traceroute

# Trace route to Google DNS (max 5 hops for speed)
traceroute -m 5 8.8.8.8

# UDP traceroute (default)
traceroute 8.8.8.8

# ICMP traceroute (sometimes gets further through firewalls)
traceroute -I 8.8.8.8
```

> 💡 `traceroute` works by sending packets with increasing TTL (Time To Live). Each router decrements TTL by 1; when TTL hits 0, the router sends back ICMP "time exceeded" — revealing its IP. `* * *` means a router didn't respond (filtered) — not necessarily a problem if the final destination responds.

📸 **Verified Output:**
```
traceroute to 8.8.8.8 (8.8.8.8), 5 hops max, 60 byte packets
 1  172.17.0.1 (172.17.0.1)  0.086 ms  0.042 ms  0.047 ms
 2  104.167.196.1 (104.167.196.1)  1.151 ms  0.525 ms  0.570 ms
 3  100.64.0.18 (100.64.0.18)  1.420 ms 100.64.0.17  1.180 ms  1.073 ms
 4  te0-1-0-0.rcr21.b002802-2.mia01.atlas.cogentco.com (38.104.91.121)  1.936 ms
 5  port-channel9.core1.mia1.he.net (184.105.65.48)  1.797 ms
```

---

## Step 3: tracepath — MTU Discovery

`tracepath` is similar to `traceroute` but also discovers Path MTU (Maximum Transmission Unit).

```bash
apt-get update -qq && apt-get install -y iputils-tracepath

# Trace with MTU discovery
tracepath -m 5 8.8.8.8

# tracepath to a hostname
tracepath -m 8 google.com
```

> 💡 `pmtu` (Path MTU) is the largest packet size that can traverse the entire path without fragmentation. The standard Ethernet MTU is 1500 bytes. If you see `pmtu 1500` that's normal. A smaller value (e.g., 1400) indicates a link on the path uses a smaller MTU (common with VPNs and tunnels). MTU mismatches cause mysterious connection hangs.

📸 **Verified Output:**
```
 1?: [LOCALHOST]                      pmtu 1500
 1:  172.17.0.1                                            0.129ms 
 1:  172.17.0.1                                            0.085ms 
 2:  104.167.196.1                                         1.142ms 
 3:  100.64.0.17                                           1.077ms asymm  4 
 4:  te0-1-0-0.rcr21.b002802-2.mia01.atlas.cogentco.com    2.889ms 
 5:  be3411.ccr22.mia01.atlas.cogentco.com                 2.871ms 
     Too many hops: pmtu 1500
     Resume: pmtu 1500 
```

---

## Step 4: DNS Diagnostics with dig and nslookup

```bash
apt-get update -qq && apt-get install -y dnsutils

# Basic DNS lookup (A record)
dig example.com A +short

# Full dig output with timing
dig example.com

# Query specific DNS server
dig @8.8.8.8 example.com

# MX records (mail servers)
dig example.com MX +short

# Reverse DNS lookup (PTR)
dig -x 8.8.8.8 +short

# nslookup (interactive or one-shot)
nslookup example.com
nslookup example.com 8.8.8.8
```

> 💡 `dig` output includes: `ANSWER SECTION` (the results), `Query time` (DNS server latency), `SERVER` (which nameserver answered). `+short` strips everything except the answer. Always check both the answer AND which server responded — wrong server = stale cache or misconfiguration.

📸 **Verified Output:**
```
# dig example.com A +short
104.18.26.120
104.18.27.120

# nslookup example.com (tail)
Name:    example.com
Address: 2606:4700::6812:1a78
Name:    example.com
Address: 2606:4700::6812:1b78
```

---

## Step 5: /etc/resolv.conf and /etc/hosts

```bash
# DNS server configuration
cat /etc/resolv.conf

# Static hostname mappings
cat /etc/hosts

# Add a temporary static mapping
echo "93.184.216.34  mytest.example" >> /etc/hosts
ping -c 1 mytest.example

# Check NSS resolution order
cat /etc/nsswitch.conf | grep hosts

# Test full resolution chain
getent hosts example.com
getent hosts localhost
```

> 💡 `/etc/hosts` is checked BEFORE DNS (by default). This makes it useful for: overriding DNS in dev (point domain to local server), blocking sites (point to 127.0.0.1), and quick testing. `/etc/resolv.conf` lists nameservers (`nameserver` lines) and search domains (`search` line for short hostname expansion). Docker auto-generates this file.

📸 **Verified Output:**
```
# /etc/resolv.conf (Docker-generated)
nameserver 8.8.8.8
search .

# /etc/hosts
127.0.0.1   localhost
::1         localhost ip6-localhost ip6-loopback
172.17.0.6  a389f683e619

# nsswitch.conf hosts line:
hosts:          files dns
```

---

## Step 6: Socket States with ss

```bash
apt-get update -qq && apt-get install -y iproute2

# Show connection states
ss -tan | head -20

# Filter by state
ss -tan state established
ss -tan state time-wait
ss -tan state listen

# Show with process information
ss -tlnp

# Watching connection changes live
watch -n 1 'ss -tan | grep -c ESTABLISHED'
```

> 💡 **TCP socket states:** `LISTEN` = waiting for connections; `ESTABLISHED` = active connection; `TIME_WAIT` = connection closed, waiting for late packets (normal, lasts ~60s); `CLOSE_WAIT` = remote closed, local hasn't (possible app bug if many); `SYN_SENT` = actively connecting. A server with thousands of `TIME_WAIT` is seeing normal high traffic. Thousands of `CLOSE_WAIT` may indicate a connection leak.

📸 **Verified Output:**
```
State  Recv-Q Send-Q Local Address:Port   Peer Address:Port  Process
# (Docker minimal container - no active connections to services)

# ss -s summary:
Total: 2
TCP:   39 (estab 0, closed 39, orphaned 4, timewait 3)
```

---

## Step 7: netcat (nc) — Port Testing

```bash
apt-get update -qq && apt-get install -y netcat-openbsd

# Test if a port is open (TCP connect test)
nc -zv example.com 80 2>&1
nc -zv example.com 443 2>&1

# Test port with timeout
nc -zv -w 3 example.com 22 2>&1

# Test multiple ports quickly
for port in 22 80 443 8080 3306; do
  nc -zv -w 2 example.com $port 2>&1 | tail -1
done

# Create a simple listener (for testing - in another terminal)
# nc -l 8888               # Listen on port 8888
# nc localhost 8888        # Connect to it

# UDP port test
nc -zuv 8.8.8.8 53 2>&1   # Test DNS UDP port
```

> 💡 `nc -zv` = scan mode (zero I/O) + verbose. Exit code 0 = port open; non-zero = closed or filtered. The difference: **closed** sends TCP RST (fast fail); **filtered** times out (slow, firewall DROP). Use `-w` to set timeout and avoid hanging. `nc` can also create simple TCP servers/clients — great for testing network connectivity between two machines.

📸 **Verified Output:**
```
Connection to example.com (104.18.27.120) 80 port [tcp/*] succeeded!
Connection to example.com (104.18.27.120) 443 port [tcp/*] succeeded!
```

---

## Step 8: Capstone — Network Diagnostic Runbook

**Scenario:** A web application is unreachable. Run a systematic diagnostic to identify whether the issue is DNS, routing, firewall, or application-level.

```bash
apt-get update -qq && apt-get install -y \
  iputils-ping traceroute iputils-tracepath \
  dnsutils iproute2 netcat-openbsd curl

TARGET="example.com"
TARGET_IP="93.184.216.34"

echo "==============================="
echo " NETWORK DIAGNOSTIC REPORT"
echo " Target: $TARGET"
echo "==============================="
echo ""

echo "--- [1] DNS Resolution ---"
dig "$TARGET" A +short
if [ $? -eq 0 ]; then
  echo "✓ DNS: OK"
else
  echo "✗ DNS: FAILED — check /etc/resolv.conf and nameservers"
fi
echo ""

echo "--- [2] Ping Test (ICMP) ---"
ping -c 3 -W 2 "$TARGET_IP" 2>&1
if [ $? -eq 0 ]; then
  echo "✓ ICMP: Reachable"
else
  echo "⚠ ICMP: No response (may be filtered, not necessarily down)"
fi
echo ""

echo "--- [3] Port 80 Test ---"
nc -zv -w 5 "$TARGET" 80 2>&1
echo "--- [4] Port 443 Test ---"
nc -zv -w 5 "$TARGET" 443 2>&1
echo ""

echo "--- [5] HTTP Response ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$TARGET")
echo "HTTP Status: $HTTP_CODE"
echo ""

echo "--- [6] Full Request Timing ---"
curl -s -o /dev/null -w "
  DNS lookup:    %{time_namelookup}s
  TCP connect:   %{time_connect}s
  TLS handshake: %{time_appconnect}s
  First byte:    %{time_starttransfer}s
  Total:         %{time_total}s
" "https://$TARGET"
echo ""

echo "--- [7] Traceroute (5 hops) ---"
traceroute -m 5 "$TARGET_IP" 2>&1
echo ""

echo "--- [8] Local Network Config ---"
echo "Default route:"
ip route show | grep default
echo "DNS servers:"
grep nameserver /etc/resolv.conf
echo ""

echo "--- [9] Socket States ---"
ss -s
echo ""

echo "==============================="
echo " DIAGNOSTIC COMPLETE"
echo "==============================="
```

> 💡 **Diagnosis decision tree:** DNS fails → check `/etc/resolv.conf` and `nameserver`. DNS OK, ping fails → routing or firewall issue. Ping OK, port closed → application not running or firewall blocking specific port. Port open, HTTP fails → application error (check app logs). HTTP slow → check timing breakdown for which phase is slow (DNS/TLS/TTFB).

📸 **Verified Output (excerpt):**
```
===============================
 NETWORK DIAGNOSTIC REPORT
 Target: example.com
===============================

--- [1] DNS Resolution ---
104.18.26.120
104.18.27.120
✓ DNS: OK

--- [2] Ping Test (ICMP) ---
PING 93.184.216.34: 3 packets transmitted, 3 received, 0% packet loss
✓ ICMP: Reachable

--- [3] Port 80 Test ---
Connection to example.com 80 port [tcp/*] succeeded!

--- [5] HTTP Response ---
HTTP Status: 200

--- [6] Full Request Timing ---
  DNS lookup:    0.004455s
  TCP connect:   0.032176s
  TLS handshake: 0.241946s
  First byte:    0.270799s
  Total:         0.271010s
```

---

## Summary

| Tool / Command | Purpose |
|----------------|---------|
| `ping -c N HOST` | Test ICMP connectivity, measure RTT |
| `ping -W N` | Set per-packet timeout (seconds) |
| `traceroute HOST` | Show each router hop to destination |
| `tracepath HOST` | Trace + discover Path MTU |
| `dig HOST A +short` | DNS A record lookup (brief) |
| `dig @SERVER HOST` | Query specific DNS server |
| `dig -x IP` | Reverse DNS lookup (PTR record) |
| `nslookup HOST` | Interactive/one-shot DNS query |
| `cat /etc/resolv.conf` | View DNS server configuration |
| `cat /etc/hosts` | View static hostname mappings |
| `getent hosts NAME` | Resolve via full NSS chain |
| `ss -tan` | Show TCP sockets with state |
| `ss -s` | Socket statistics summary |
| `nc -zv HOST PORT` | Test if TCP port is open |
| `nc -zuv HOST PORT` | Test if UDP port is open |
| `curl -w "fmt" URL` | HTTP timing breakdown |
| `ip route show` | View routing table |
| DNS → Ping → Port → HTTP | Systematic diagnostic order |
