# Lab 10: Network Reconnaissance

## 🎯 Objective
Use nmap to perform network reconnaissance on localhost. Understand port states, service detection with -sV, script scanning with -sC, and how defenders detect scanning activity.

## 📚 Background
Network reconnaissance is the process of discovering hosts, ports, and services on a target network. It is the first technical step in any penetration test and what attackers do before launching attacks. Understanding reconnaissance helps defenders know what information is exposed and how to detect scanning activity.

**Nmap** (Network Mapper) is the industry standard for network reconnaissance. It can discover live hosts, open ports, running services, operating system versions, and run security scripts against targets. Nmap uses various scan techniques: TCP connect scans (-sT), SYN scans (-sS), UDP scans (-sU), and more.

**Port states** detected by nmap: open (service listening), closed (no service, host reachable), filtered (firewall blocking), open|filtered (can't determine), and unfiltered. Understanding these states is crucial for interpreting scan results.

**Nmap Scripting Engine (NSE)** extends nmap with scripts for vulnerability detection, service enumeration, and exploitation. Scripts can detect default credentials, check for known CVEs, enumerate SMB shares. The `-sC` flag runs default scripts.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Labs 1-9 completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `nmap` — Network scanner
- `nc` — Netcat for creating test services
- `python3` — HTTP server for scanning targets

## 🔬 Lab Instructions

### Step 1: Basic Host Discovery
```bash
docker run --rm innozverse-cybersec bash -c "nmap -sn 127.0.0.1 2>/dev/null"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:52 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000018s latency).
Nmap done: 1 IP address (1 host up) scanned in 0.04 seconds
```

> 💡 **What this means:** `-sn` (ping scan) checks if a host is up without scanning ports. `Host is up` with nearly zero latency — loopback is local. On a real network, add `-Pn` to skip host discovery and scan anyway (some hosts block ping but have open ports).

### Step 2: Default TCP Port Scan (Top 1000 Ports)
```bash
docker run --rm innozverse-cybersec bash -c "nmap 127.0.0.1 2>/dev/null"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:52 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000018s latency).
All 1000 scanned ports on localhost (127.0.0.1) are closed

Nmap done: 1 IP address (1 host up) scanned in 0.94 seconds
```

> 💡 **What this means:** By default, nmap scans the 1000 most common ports. "All 1000 scanned ports are closed" — a clean system with no exposed services is a good security posture. Attackers interpret this as no easy entry points.

### Step 3: Scan Specific Ports with Service Version Detection
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 8181 &>/dev/null &)
sleep 0.5
nmap -sV -p 8181 127.0.0.1 2>/dev/null
"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:57 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000076s latency).

PORT     STATE SERVICE VERSION
8181/tcp open  http    SimpleHTTPServer 0.6 (Python 3.10.12)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 6.90 seconds
```

> 💡 **What this means:** `-sV` probes open ports to determine service version. nmap identified "SimpleHTTPServer 0.6 (Python 3.10.12)" — giving an attacker the exact software version to search for CVEs. Defense: suppress server banners (`server_tokens off` in nginx).

### Step 4: Script Scan (-sC)
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 8282 &>/dev/null &)
sleep 0.5
nmap -sC -p 8282 127.0.0.1 2>/dev/null
"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:58 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000038s latency).

PORT     STATE SERVICE
8282/tcp open  unknown
|_http-title: Directory listing for /

Nmap done: 1 IP address (1 host up) scanned in 0.05 seconds
```

> 💡 **What this means:** The `-sC` flag ran NSE scripts including `http-title` which retrieved the web page title: "Directory listing for /" — this tells an attacker that directory listing is enabled, exposing all files on the server. Other NSE scripts check for default credentials, heartbleed, SMB vulnerabilities.

### Step 5: Aggressive Scan (-A)
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 8383 &>/dev/null &)
sleep 0.5
nmap -A -p 8383 127.0.0.1 2>/dev/null
"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:58 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000038s latency).

PORT     STATE SERVICE VERSION
8383/tcp open  http    SimpleHTTPServer 0.6 (Python 3.10.12)
|_http-title: Directory listing for /
|_http-server-header: SimpleHTTP/0.6 Python/3.10.12

Service Info: OS: Linux

Nmap done: 1 IP address (1 host up) scanned in 7.24 seconds
```

> 💡 **What this means:** `-A` (aggressive) combines version detection, script scan, OS detection, and traceroute. The `http-server-header` script extracted the full server banner. OS detection identified Linux. This single command gives attackers a complete picture of the target. Note: `-A` is noisy and easily detected by IDS/IPS.

### Step 6: TCP SYN vs TCP Connect Scan
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 8484 &>/dev/null &)
sleep 0.5
echo '=== TCP Connect scan (-sT) ==='
nmap -sT -p 8484 127.0.0.1 2>/dev/null | grep -E 'PORT|STATE|open|closed'
echo ''
echo 'SYN scan (-sS) requires root/raw sockets'
echo 'TCP Connect: full 3-way handshake - appears in server logs'
echo 'SYN scan: sends SYN, gets SYN-ACK, sends RST - stealthier'
"
```

**📸 Verified Output:**
```
=== TCP Connect scan (-sT) ===
PORT     STATE SERVICE
8484/tcp open  unknown

SYN scan (-sS) requires root/raw sockets
TCP Connect: full 3-way handshake - appears in server logs
SYN scan: sends SYN, gets SYN-ACK, sends RST - stealthier
```

> 💡 **What this means:** TCP Connect (`-sT`) completes the full handshake and appears in application logs. SYN scan (`-sS`) sends SYN, receives SYN-ACK, then sends RST without completing the handshake — potentially evading application-level logging but still visible to network IDS. Modern IDS easily detects both.

### Step 7: UDP Scanning
```bash
docker run --rm innozverse-cybersec bash -c "nmap -sU -p 53,123,161 127.0.0.1 2>/dev/null"
```

**📸 Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:58 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000040s latency).

PORT    STATE         SERVICE
53/udp  closed        domain
123/udp closed        ntp
161/udp closed|filtered snmp

Nmap done: 1 IP address (1 host up) scanned in 1.44 seconds
```

> 💡 **What this means:** UDP scanning is harder than TCP — there's no SYN-ACK for open UDP ports. "closed" means ICMP port unreachable was received. "open|filtered" means no response — could be open or filtered. Port 161 (SNMP) with "closed|filtered" is good — SNMP with default community strings "public/private" is a major vulnerability found on routers and switches.

### Step 8: All-Port Scan and Output Formats
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 12345 &>/dev/null &)
sleep 0.5
echo '=== All-port scan (brief demo) ==='
nmap -p 12340-12350 127.0.0.1 2>/dev/null | grep -E 'PORT|STATE|12345'
echo ''
echo '=== nmap output formats ==='
echo 'nmap -oN output.txt     # Normal format'
echo 'nmap -oX output.xml     # XML format (for tools)'
echo 'nmap -oG output.gnmap   # Grepable format'
echo 'nmap -oA output         # All three formats'
"
```

**📸 Verified Output:**
```
=== All-port scan (brief demo) ===
PORT      STATE  SERVICE
12340/tcp closed unknown
12341/tcp closed unknown
12342/tcp closed unknown
12343/tcp closed unknown
12344/tcp closed unknown
12345/tcp open   italk
12346/tcp closed unknown
12347/tcp closed unknown
12348/tcp closed unknown
12349/tcp closed unknown
12350/tcp closed unknown

=== nmap output formats ===
nmap -oN output.txt     # Normal format
nmap -oX output.xml     # XML format (for tools)
nmap -oG output.gnmap   # Grepable format
nmap -oA output         # All three formats
```

> 💡 **What this means:** `-p-` scans all 65535 ports (we used a small range for speed). Services sometimes run on non-standard ports — only scanning the top 1000 misses them. In real penetration tests, `-p-` is standard. Save output with `-oA` for later analysis with tools like Metasploit or custom scripts.

### Step 9: NSE Scripts for Security Testing
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== NSE script categories ==='
ls /usr/share/nmap/scripts/ 2>/dev/null | head -10
echo '...'
echo ''
echo '=== Common security-relevant scripts ==='
echo 'nmap --script vuln target          # Run all vuln scripts'
echo 'nmap --script http-shellshock      # Check for Shellshock'
echo 'nmap --script smb-vuln-ms17-010    # Check EternalBlue'
echo 'nmap --script ssl-heartbleed       # Check Heartbleed'
echo 'nmap --script http-auth            # Check HTTP auth'
echo 'nmap --script default              # Same as -sC'
"
```

**📸 Verified Output:**
```
=== NSE script categories ===
acarsd-info.nse
address-info.nse
afp-brute.nse
afp-ls.nse
afp-path-vuln.nse
afp-serverinfo.nse
afp-showmount.nse
ajp-auth.nse
ajp-brute.nse
ajp-headers.nse
...

=== Common security-relevant scripts ===
nmap --script vuln target          # Run all vuln scripts
nmap --script http-shellshock      # Check for Shellshock
nmap --script smb-vuln-ms17-010    # Check EternalBlue
nmap --script ssl-heartbleed       # Check Heartbleed
nmap --script http-auth            # Check HTTP auth
nmap --script default              # Same as -sC
```

> 💡 **What this means:** NSE has 600+ scripts covering everything from brute-forcing to vulnerability detection. `--script smb-vuln-ms17-010` checks for EternalBlue — the vulnerability exploited by WannaCry ransomware. These scripts dramatically expand nmap from a port scanner to a lightweight vulnerability scanner.

### Step 10: Detecting Port Scans (Defender Perspective)
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
print('PORT SCAN DETECTION METHODS:')
print()
indicators = [
    'Rapid connections to many sequential ports from one IP',
    'High rate of TCP RST (connection refused) responses',
    'Half-open connections (SYN without completing handshake)',
    'Connections to honeypot ports (ports that should never receive traffic)',
    'Nmap signature patterns in packet payloads',
    'Source IP appearing in threat intelligence feeds',
]
for i in indicators:
    print(f'  - {i}')
print()
print('NMAP TIMING TEMPLATES:')
timings = [
    ('-T0', 'Paranoid', '5 min between probes', 'Evades most detection'),
    ('-T1', 'Sneaky', '15 sec between probes', 'Slow but still detectable'),
    ('-T3', 'Normal', 'Default', 'Standard speed'),
    ('-T5', 'Insane', 'Fastest possible', 'Very noisy, triggers alerts'),
]
for flag, name, delay, detection in timings:
    print(f'  {flag} ({name}): {delay} - {detection}')
print()
print('DEFENSES: fail2ban, psad, Snort/Suricata IDS, SIEM correlation rules')
\"
"
```

**📸 Verified Output:**
```
PORT SCAN DETECTION METHODS:

  - Rapid connections to many sequential ports from one IP
  - High rate of TCP RST (connection refused) responses
  - Half-open connections (SYN without completing handshake)
  - Connections to honeypot ports (ports that should never receive traffic)
  - Nmap signature patterns in packet payloads
  - Source IP appearing in threat intelligence feeds

NMAP TIMING TEMPLATES:
  -T0 (Paranoid): 5 min between probes - Evades most detection
  -T1 (Sneaky): 15 sec between probes - Slow but still detectable
  -T3 (Normal): Default - Standard speed
  -T5 (Insane): Fastest possible - Very noisy, triggers alerts

DEFENSES: fail2ban, psad, Snort/Suricata IDS, SIEM correlation rules
```

> 💡 **What this means:** Well-monitored networks detect port scans in seconds. Cloud providers (AWS, Azure) have built-in scanning detection and will block your IP. Honeypot ports (ports that should never receive traffic) are especially useful — any connection to them is immediately suspicious. Canary tokens and HoneyBadger implement this pattern.

## ✅ Verification
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 9876 &>/dev/null &)
sleep 0.5
nmap -sV -p 9876 127.0.0.1 2>/dev/null | grep -E 'PORT|VERSION'
"
```

**📸 Verified Output:**
```
PORT     STATE SERVICE VERSION
9876/tcp open  http    SimpleHTTPServer 0.6 (Python 3.10.12)
```

## 🚨 Common Mistakes
- **Scanning without authorization**: Port scanning systems you don't own or have permission to test is illegal in many jurisdictions. Always get written authorization.
- **Only scanning top 1000 ports**: Real services run on non-standard ports. Use `-p-` to scan all 65535 ports for comprehensive coverage.
- **Ignoring UDP ports**: Critical services like DNS (53), SNMP (161), and DHCP (67/68) use UDP. A TCP-only scan misses these.

## 📝 Summary
- Nmap is the industry standard for network reconnaissance; -sV detects service versions, -sC runs security scripts, -A combines all for comprehensive results
- Open ports reveal running services; service version detection enables CVE searching; script scanning detects specific vulnerabilities
- All reconnaissance leaves traces; defenders use fail2ban, IDS/IPS, and SIEM correlation to detect and block scanning
- Always obtain written authorization before scanning; unauthorized scanning violates laws and terms of service

## 🔗 Further Reading
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [Shodan.io - See what's exposed on the internet](https://www.shodan.io/)
- [NSE Script Documentation](https://nmap.org/nsedoc/)
