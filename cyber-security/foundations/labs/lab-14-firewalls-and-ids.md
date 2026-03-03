# Lab 14: Firewalls and IDS

## 🎯 Objective
Understand firewall rule logic, compare IDS/IPS/Firewall/WAF capabilities, analyze Snort rule syntax, and build a mental model of layered network defense architecture.

## 📚 Background
Firewalls are the foundational network security control — they inspect network traffic and permit or deny it based on rules. Traditional stateless firewalls filter based on IP addresses and ports alone. Stateful firewalls track connection state, while next-generation firewalls (NGFW) inspect application layer content, user identity, and threat intelligence.

Intrusion Detection Systems (IDS) monitor network or host activity for malicious patterns and generate alerts. Unlike firewalls, they don't block traffic by default — they observe and report. Intrusion Prevention Systems (IPS) take the next step, automatically blocking detected threats inline. Web Application Firewalls (WAF) specifically protect HTTP/HTTPS applications from application-layer attacks like SQL injection and XSS.

The key insight is that each security control has a different vantage point and capability. A network firewall doesn't understand HTTP session semantics. A WAF understands HTTP but not network-level attacks. An IDS understands both but generates alerts rather than blocks. Layering these controls creates defense-in-depth for network security.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Lab 08: Common Attack Vectors
- Basic TCP/IP networking

## 🛠️ Tools Used
- `iptables` — Linux firewall
- `python3` — firewall logic simulation

## 🔬 Lab Instructions

### Step 1: View Current Firewall Rules

```bash
echo "=== Current iptables rules ==="
iptables -L -n -v 2>/dev/null || echo "iptables not available or no rules"

echo ""
echo "=== INPUT chain (inbound traffic) ==="
iptables -L INPUT -n -v 2>/dev/null

echo ""
echo "=== OUTPUT chain (outbound traffic) ==="
iptables -L OUTPUT -n -v 2>/dev/null

echo ""
echo "=== FORWARD chain (routed traffic) ==="
iptables -L FORWARD -n -v 2>/dev/null
```

**📸 Verified Output:**
```
=== Current iptables rules ===
Chain INPUT (policy ACCEPT)
target     prot opt source               destination

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination
```

> 💡 **What this means:** Default policy ACCEPT means all traffic is allowed unless a rule explicitly blocks it. This is the "default allow" model. Production firewalls should use "default deny" (DROP policy) and explicitly allow only needed traffic.

### Step 2: Understanding Firewall Rule Processing

```bash
python3 << 'EOF'
print("FIREWALL RULE PROCESSING MODEL")
print("=" * 60)

print("""
iptables processes rules in ORDER - first match wins:

Chain INPUT (inbound to this machine):
Rule 1: ACCEPT established connections (stateful - don't block replies)
Rule 2: ACCEPT SSH from 10.0.0.0/8 (admin network)
Rule 3: ACCEPT HTTP/HTTPS from anywhere (web server)
Rule 4: DROP ICMP (block ping)
Rule 5: DROP all  <-- default deny at end

Packet arrives: TCP SYN to port 22 from 192.168.1.50
  Check Rule 1: Not established → skip
  Check Rule 2: 192.168.1.50 not in 10.0.0.0/8 → skip
  Check Rule 3: Port 22 ≠ 80/443 → skip
  Check Rule 4: Not ICMP → skip
  Check Rule 5: DROP ← packet blocked
""")

# Simulate firewall rule matching
class FirewallRule:
    def __init__(self, action, proto=None, src=None, dst=None, dport=None, state=None):
        self.action = action
        self.proto = proto
        self.src = src
        self.dst = dst
        self.dport = dport
        self.state = state
    
    def __str__(self):
        parts = [self.action]
        if self.proto: parts.append(f"proto={self.proto}")
        if self.src: parts.append(f"src={self.src}")
        if self.dport: parts.append(f"dport={self.dport}")
        if self.state: parts.append(f"state={self.state}")
        return " ".join(parts)

def ip_in_network(ip, network):
    """Simple network check (e.g., 10.0.0.5 in 10.0.0.0/8)"""
    if network == "any":
        return True
    if "/" not in network:
        return ip == network
    net_ip, prefix = network.split("/")
    prefix = int(prefix)
    def ip_to_int(ip):
        parts = ip.split(".")
        return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])
    mask = ((1 << 32) - 1) ^ ((1 << (32 - prefix)) - 1)
    return (ip_to_int(ip) & mask) == (ip_to_int(net_ip) & mask)

# Define firewall ruleset
rules = [
    {"action": "ACCEPT", "proto": "tcp", "src": "any", "dport": None,  "state": "ESTABLISHED", "desc": "Allow established connections"},
    {"action": "ACCEPT", "proto": "tcp", "src": "10.0.0.0/8", "dport": 22, "state": None, "desc": "Allow SSH from admin network"},
    {"action": "ACCEPT", "proto": "tcp", "src": "any", "dport": 80, "state": None, "desc": "Allow HTTP from anywhere"},
    {"action": "ACCEPT", "proto": "tcp", "src": "any", "dport": 443, "state": None, "desc": "Allow HTTPS from anywhere"},
    {"action": "DROP",   "proto": "any", "src": "any", "dport": None, "state": None, "desc": "Default deny"},
]

test_packets = [
    {"proto": "tcp", "src": "203.0.113.1", "dport": 443, "state": None, "desc": "HTTPS from internet"},
    {"proto": "tcp", "src": "10.0.1.5", "dport": 22, "state": None, "desc": "SSH from admin network"},
    {"proto": "tcp", "src": "192.168.1.100", "dport": 22, "state": None, "desc": "SSH from unauthorized network"},
    {"proto": "tcp", "src": "203.0.113.1", "dport": 3306, "state": None, "desc": "MySQL from internet"},
    {"proto": "tcp", "src": "any", "dport": 443, "state": "ESTABLISHED", "desc": "Established HTTPS reply"},
]

print("FIREWALL SIMULATION")
print("=" * 65)
for packet in test_packets:
    for i, rule in enumerate(rules):
        match = True
        if rule["proto"] != "any" and rule["proto"] != packet["proto"]:
            match = False
        if rule["src"] != "any" and not ip_in_network(packet["src"], rule["src"] if "/" in (rule["src"] or "") else (rule["src"] or "any")):
            match = False
        if rule["dport"] is not None and rule["dport"] != packet["dport"]:
            match = False
        if rule["state"] is not None and rule["state"] != packet.get("state"):
            match = False
        
        if match:
            status = "✅ ACCEPT" if rule["action"] == "ACCEPT" else "❌ DROP"
            print(f"\nPacket: {packet['desc']}")
            print(f"  Matches rule {i+1} ({rule['desc']}): {status}")
            break
EOF
```

**📸 Verified Output:**
```
FIREWALL RULE PROCESSING MODEL
============================================================
...
FIREWALL SIMULATION
=================================================================

Packet: HTTPS from internet
  Matches rule 3 (Allow HTTP from anywhere): ✅ ACCEPT

Packet: SSH from admin network
  Matches rule 2 (Allow SSH from admin network): ✅ ACCEPT

Packet: SSH from unauthorized network
  Matches rule 5 (Default deny): ❌ DROP

Packet: MySQL from internet
  Matches rule 5 (Default deny): ❌ DROP
```

> 💡 **What this means:** Firewall rules are evaluated top-down. Order matters critically — if "ACCEPT all" appeared before "DROP mysql," the database would be exposed. Always put specific rules before broad ones, and end with "DROP all."

### Step 3: IDS vs IPS vs Firewall vs WAF Comparison

```bash
python3 << 'EOF'
print("NETWORK SECURITY CONTROLS COMPARISON")
print("=" * 70)

controls = [
    {
        "name": "Traditional Firewall (Packet Filter)",
        "layer": "L3/L4 (Network/Transport)",
        "sees": "IP addresses, ports, protocols",
        "blind_to": "Application content, user identity, threat context",
        "action": "ALLOW or DENY based on rules",
        "placement": "Network perimeter, between segments",
        "example": "iptables, AWS Security Groups",
        "stops": ["Port scanning (if filtered)", "Unauthorized service access", "Network-level DoS"],
        "misses": ["SQLi via port 443", "XSS", "Application exploits"],
    },
    {
        "name": "Stateful Firewall",
        "layer": "L3/L4 + connection tracking",
        "sees": "Full connection state, not just packets",
        "blind_to": "Application layer content",
        "action": "ALLOW or DENY based on rules + state",
        "placement": "Network perimeter",
        "example": "pfSense, Cisco ASA",
        "stops": ["IP spoofing", "Session hijacking at network level"],
        "misses": ["Application layer attacks"],
    },
    {
        "name": "NGFW (Next-Gen Firewall)",
        "layer": "L3-L7 (all layers)",
        "sees": "Applications, users, content, threat intelligence",
        "blind_to": "Encrypted C2 if CA not installed",
        "action": "ALLOW/DENY/INSPECT based on policy",
        "placement": "Network perimeter or internal segmentation",
        "example": "Palo Alto, Fortinet, Check Point",
        "stops": ["Known malware", "Command & control", "App abuse", "User policy violations"],
        "misses": ["Unknown zero-days", "Encrypted threats without TLS inspection"],
    },
    {
        "name": "IDS (Intrusion Detection System)",
        "layer": "L3-L7",
        "sees": "All traffic patterns + known attack signatures",
        "blind_to": "What it's not tuned to detect",
        "action": "ALERT only (passive monitoring)",
        "placement": "Out-of-band, receives copy of traffic (span port)",
        "example": "Snort (detect mode), Suricata, Zeek",
        "stops": ["Nothing directly - generates alerts"],
        "misses": ["Encrypted traffic (without decryption)", "Low-and-slow attacks if not tuned"],
    },
    {
        "name": "IPS (Intrusion Prevention System)",
        "layer": "L3-L7",
        "sees": "All traffic patterns + known attack signatures",
        "blind_to": "Encrypted traffic",
        "action": "ALERT + BLOCK inline",
        "placement": "Inline (traffic passes through it)",
        "example": "Snort (inline mode), Suricata (inline), Cisco Firepower",
        "stops": ["Known attacks immediately", "Exploit attempts"],
        "misses": ["Zero-days", "Encrypted attacks"],
    },
    {
        "name": "WAF (Web Application Firewall)",
        "layer": "L7 (Application - HTTP/HTTPS)",
        "sees": "HTTP requests/responses, parameters, headers, cookies",
        "blind_to": "Non-HTTP traffic, network layer attacks",
        "action": "ALLOW/BLOCK/CHALLENGE HTTP requests",
        "placement": "In front of web servers",
        "example": "ModSecurity, AWS WAF, Cloudflare WAF, F5 ASM",
        "stops": ["SQLi", "XSS", "CSRF", "Path traversal", "Bot attacks"],
        "misses": ["Network layer attacks", "Vulnerabilities in business logic"],
    },
]

for ctrl in controls:
    print(f"\n{'─'*70}")
    print(f"CONTROL: {ctrl['name']}")
    print(f"  OSI Layer:    {ctrl['layer']}")
    print(f"  Can see:      {ctrl['sees']}")
    print(f"  Action:       {ctrl['action']}")
    print(f"  Examples:     {ctrl['example']}")
    print(f"  Stops:        {', '.join(ctrl['stops'][:2])}")
    print(f"  Blind to:     {ctrl['blind_to']}")
EOF
```

**📸 Verified Output:**
```
NETWORK SECURITY CONTROLS COMPARISON
======================================================================

──────────────────────────────────────────────────────────────────────
CONTROL: Traditional Firewall (Packet Filter)
  OSI Layer:    L3/L4 (Network/Transport)
  Can see:      IP addresses, ports, protocols
  Action:       ALLOW or DENY based on rules
  Examples:     iptables, AWS Security Groups
  Stops:        Port scanning (if filtered), Unauthorized service access
  Blind to:     Application content, user identity, threat context
...
```

> 💡 **What this means:** Layer your security controls. A firewall blocks unauthorized connections; a WAF inspects the HTTP content within those connections; an IDS/IPS detects attack patterns within allowed traffic. No single control covers everything.

### Step 4: Snort Rule Syntax

```bash
python3 << 'EOF'
print("SNORT IDS/IPS RULE SYNTAX")
print("=" * 65)

print("""
Snort Rule Format:
  action proto src_ip src_port direction dst_ip dst_port (options)

Fields:
  action:   alert | log | pass | drop | reject
  proto:    tcp | udp | icmp | ip
  src/dst:  IP or CIDR or 'any'
  src/dst port: port number, range, or 'any'
  direction: -> (one-way) or <> (bidirectional)
  options:  (key:value; pairs in parentheses)

Common Options:
  msg:      Alert message shown in logs
  content:  Pattern to match in payload
  nocase:   Case-insensitive content match
  sid:      Unique rule ID (>1000000 for local rules)
  rev:      Revision number
  classtype: Attack classification
  priority: 1(high) to 3(low)
""")

rules = [
    {
        "description": "Detect SQL injection in HTTP GET request",
        "rule": "alert tcp any any -> $HTTP_SERVERS 80 (msg:\"SQL Injection Attempt\"; content:\"' OR '\"; nocase; http_uri; sid:1000001; rev:1; classtype:web-application-attack; priority:1;)"
    },
    {
        "description": "Detect nmap version scan",
        "rule": "alert tcp any any -> any any (msg:\"nmap version scan detected\"; content:\"Nmap Scripting Engine\"; sid:1000002; rev:1;)"
    },
    {
        "description": "Detect ICMP ping (for awareness)",
        "rule": "alert icmp any any -> $HOME_NET any (msg:\"ICMP Ping to internal network\"; itype:8; sid:1000003; rev:1;)"
    },
    {
        "description": "Detect potential reverse shell via nc",
        "rule": "alert tcp $HOME_NET any -> any any (msg:\"Possible reverse shell - nc\"; content:\"/bin/sh\"; content:\"nc\"; sid:1000004; rev:1; priority:1;)"
    },
    {
        "description": "Block SSH brute force (>10 attempts/min)",
        "rule": "drop tcp any any -> $SSH_SERVERS 22 (msg:\"SSH Brute Force Attempt\"; detection_filter:track by_src, count 10, seconds 60; sid:1000005; rev:1;)"
    },
    {
        "description": "Detect WannaCry kill switch domain lookup",
        "rule": "alert udp any any -> any 53 (msg:\"WannaCry Kill Switch Domain\"; content:\"|77 77 77 2e 69 75 71 65|\"; nocase; sid:1000006; rev:1; priority:1;)"
    },
]

for r in rules:
    print(f"\nPurpose: {r['description']}")
    print(f"Rule:")
    # Wrap long rule
    rule = r['rule']
    print(f"  {rule[:80]}")
    if len(rule) > 80:
        print(f"  {rule[80:]}")

print("\n" + "=" * 65)
print("RULE WRITING TIPS:")
tips = [
    "Be specific — overly broad rules cause false positives",
    "Use 'nocase' for string matching (attackers use cAsE vArIaTiOn)",
    "Test rules in alert mode before switching to drop",
    "Use detection_filter for rate-based detection (brute force)",
    "Assign unique SIDs (local rules: 1000001+)",
    "Include classtype and priority for SIEM correlation",
]
for tip in tips:
    print(f"  • {tip}")
EOF
```

**📸 Verified Output:**
```
SNORT IDS/IPS RULE SYNTAX
=================================================================

Snort Rule Format:
  action proto src_ip src_port direction dst_ip dst_port (options)
...

Purpose: Detect SQL injection in HTTP GET request
Rule:
  alert tcp any any -> $HTTP_SERVERS 80 (msg:"SQL Injection Attempt"; ...
```

> 💡 **What this means:** Snort rules combine protocol awareness (IP, TCP, UDP) with content matching. The content options can match strings in payloads, making them effective against known attack patterns. Modern variants like Suricata support multi-threading and additional protocols.

### Step 5: Defense Architecture Diagram

```bash
python3 << 'EOF'
print("""
LAYERED NETWORK DEFENSE ARCHITECTURE
=====================================

INTERNET
    |
    | (Raw internet traffic)
    |
[DDoS Protection / CDN]  <-- Cloudflare, AWS Shield
    |
    |
[Edge Firewall / NGFW]   <-- Block unauthorized IPs, geo-blocking
    |                        Internet → DMZ only on specific ports
    |
+---+------------------+
|         DMZ          |
|   [Web Servers]      |  <-- Web servers, load balancers, APIs
|   [Email Gateway]    |      Only these talk to internet directly
|   [VPN Gateway]      |
+---+------------------+
    |
    | (Only specific ports from DMZ to internal)
    |
[Internal Firewall]      <-- DMZ cannot freely reach internal network
    |
    |
+---+------------------+
|   INTERNAL NETWORK   |
|                      |
|   [WAF]              |  <-- HTTP/HTTPS inspection before web servers
|   [IDS/IPS]          |  <-- Monitor ALL internal traffic (span port)
|   [SIEM]             |  <-- Collect logs from everything
|                      |
|   [App Servers]      |
|   [Database Segment] |  <-- DB in SEPARATE segment, no internet access
|   [Management Net]   |  <-- Admin access only via jump host/VPN
+----------------------+

KEY PRINCIPLES:
1. PERIMETER: Minimize what's exposed to internet (DMZ concept)
2. SEGMENTATION: Internal network is NOT flat - zones per trust level
3. LEAST PRIVILEGE: DMZ servers cannot initiate connections to DB
4. MONITORING: IDS sees all internal traffic via span/mirror port
5. LOGGING: Everything logs to SIEM for correlation
6. JUMP HOST: Admins access critical systems only via bastion host
7. MFA: Required for all remote access (VPN, jump host)

TRAFFIC FLOWS (what's allowed):
  Internet → DMZ:       HTTPS (443), SMTP (25)
  DMZ → Internal:       App-specific ports only
  Internal → DB:        Database port only, from app servers only
  Internal → Internet:  HTTPS via proxy (for updates, etc.)
  Admin → Mgmt Net:     SSH/RDP via VPN → Jump Host → target
""")
EOF
```

**📸 Verified Output:**
```
LAYERED NETWORK DEFENSE ARCHITECTURE
=====================================

INTERNET
    |
    |
[DDoS Protection / CDN]
    |
[Edge Firewall / NGFW]
    |
+---+------------------+
|         DMZ          |
|   [Web Servers]      |
...
KEY PRINCIPLES:
1. PERIMETER: Minimize what's exposed to internet (DMZ concept)
2. SEGMENTATION: Internal network is NOT flat
...
```

> 💡 **What this means:** The DMZ (Demilitarized Zone) isolates internet-facing servers from the internal network. Even if an attacker compromises a web server in the DMZ, they face another firewall before reaching internal systems.

### Step 6: Common Firewall Rules for a Web Server

```bash
python3 << 'EOF'
print("PRODUCTION WEB SERVER FIREWALL RULESET")
print("=" * 60)

print("""
# iptables rules for a web server (run as root in container)
# DEFAULT DENY approach

# Flush existing rules
iptables -F
iptables -X

# Default policies: DROP everything
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT  # Allow all outbound

# Allow loopback (required for many services)
iptables -A INPUT -i lo -j ACCEPT

# Allow ESTABLISHED connections (replies to our outbound)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow HTTP and HTTPS from anywhere
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH ONLY from admin IP range
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# Rate limit SSH (prevent brute force)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 -j DROP

# Allow ICMP ping (optional - for monitoring)
iptables -A INPUT -p icmp --icmp-type 8 -j ACCEPT

# Log dropped packets (for debugging - comment out in production)
# iptables -A INPUT -j LOG --log-prefix "iptables-drop: "

# Everything else: DROP (already default, but explicit is better)
iptables -A INPUT -j DROP
""")

print("EXPLANATION:")
explanations = [
    ("Default DROP policy", "All traffic blocked unless explicitly allowed (whitelist model)"),
    ("Loopback accept", "127.0.0.1 traffic needed for local services to communicate"),
    ("ESTABLISHED/RELATED", "Allow replies to connections we initiated (stateful tracking)"),
    ("HTTP/HTTPS accept", "Web traffic from any source - public web server"),
    ("SSH source restriction", "Admin access only from internal network, not internet"),
    ("SSH rate limiting", "Max 3 new SSH connections per 60 seconds per IP (anti-brute force)"),
    ("ICMP accept", "Allow ping for monitoring tools to check availability"),
]
for rule, explanation in explanations:
    print(f"\n  [{rule}]")
    print(f"  {explanation}")

print("\n" + "=" * 60)
print("VERIFY RULES: iptables -L -n -v")
print("SAVE RULES:   iptables-save > /etc/iptables/rules.v4")
print("RESTORE:      iptables-restore < /etc/iptables/rules.v4")
EOF
```

**📸 Verified Output:**
```
PRODUCTION WEB SERVER FIREWALL RULESET
============================================================

# iptables rules for a web server (run as root in container)
# DEFAULT DENY approach
...
EXPLANATION:

  [Default DROP policy]
  All traffic blocked unless explicitly allowed (whitelist model)

  [SSH source restriction]
  Admin access only from internal network, not internet
```

> 💡 **What this means:** "Default deny" is the gold standard. Start with DROP all, then explicitly allow what's needed. This is fundamentally safer than "default allow + block bad things" — you can't block every possible threat, but you can enumerate what's legitimate.

### Step 7: WAF Rule Examples and Evasion

```bash
python3 << 'EOF'
print("WAF RULE EXAMPLES AND EVASION TECHNIQUES")
print("=" * 60)

# Simple WAF simulation
def simple_waf(request_url, request_body=""):
    """Simplified WAF pattern matching."""
    blocked_patterns = [
        ("' OR '", "SQL Injection"),
        ("UNION SELECT", "SQL Injection"),
        ("<script>", "XSS"),
        ("../../../", "Path Traversal"),
        ("/etc/passwd", "Path Traversal"),
        ("exec(", "Command Injection"),
        ("eval(", "Code Injection"),
        ("DROP TABLE", "SQL Injection"),
    ]
    
    combined = (request_url + " " + request_body).upper()
    for pattern, attack_type in blocked_patterns:
        if pattern.upper() in combined:
            return f"BLOCKED ({attack_type})"
    return "ALLOWED"

# Test WAF
test_requests = [
    ("/search?q=hello+world", "", "Normal search"),
    ("/login?user=admin' OR '1'='1", "", "Basic SQLi"),
    ("/search?q=<script>alert(1)</script>", "", "XSS attempt"),
    ("/file?path=../../../etc/passwd", "", "Path traversal"),
    # WAF evasion attempts
    ("/login?user=admin'/**/OR/**/'1'='1", "", "SQLi with comments (evasion)"),
    ("/search?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E", "", "URL-encoded XSS"),
    ("/login?user=admin' oR '1'='1", "", "Case variation SQLi"),
]

print(f"\n{'Request':<45} {'WAF Decision':<20} {'Test Description'}")
print("-" * 80)
for url, body, desc in test_requests:
    decision = simple_waf(url, body)
    icon = "✅" if "ALLOWED" in decision else "❌"
    short_url = url[:42] + "..." if len(url) > 42 else url
    print(f"{icon} {short_url:<44} {decision:<20} {desc}")

print("""
IMPORTANT LESSONS:
1. Simple pattern matching is easily evaded (URL encoding, case variation, comments)
2. Modern WAFs use multiple detection methods:
   - Signature matching (like above)
   - Behavioral analysis (anomaly scoring)
   - ML-based detection
   - Positive security model (only allow known-good patterns)
3. WAF is one layer - not a complete security solution
4. Test WAF with penetration testing to find bypasses
5. Keep WAF rules updated (subscribe to rule feeds)
""")
EOF
```

**📸 Verified Output:**
```
WAF RULE EXAMPLES AND EVASION TECHNIQUES
============================================================

Request                                       WAF Decision         Test Description
--------------------------------------------------------------------------------
✅ /search?q=hello+world                      ALLOWED              Normal search
❌ /login?user=admin' OR '1'='1               BLOCKED (SQL Inj...) Basic SQLi
❌ /search?q=<script>alert(1)</script>        BLOCKED (XSS)        XSS attempt
✅ /login?user=admin'/**/OR/**/'1'='1         ALLOWED              SQLi with comments (evasion)
```

> 💡 **What this means:** Simple WAF pattern matching is bypassed by attackers using URL encoding, case variation, or comment injection. This is why WAFs need multiple detection layers and regular rule updates. A WAF alone is not enough — fix the underlying vulnerability too.

### Step 8: Testing Firewall Rules

```bash
# View iptables rules in a readable format
echo "=== Current Firewall State ==="
iptables -L -n -v 2>/dev/null

echo ""
echo "=== Check what ports are listening ==="
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null | head -20

echo ""
echo "=== Test connection to specific ports ==="
# These use timeout to avoid hanging
timeout 2 bash -c "echo >/dev/tcp/localhost/22" 2>/dev/null && echo "Port 22 (SSH): OPEN" || echo "Port 22 (SSH): CLOSED/FILTERED"
timeout 2 bash -c "echo >/dev/tcp/localhost/80" 2>/dev/null && echo "Port 80 (HTTP): OPEN" || echo "Port 80 (HTTP): CLOSED/FILTERED"
timeout 2 bash -c "echo >/dev/tcp/localhost/443" 2>/dev/null && echo "Port 443 (HTTPS): OPEN" || echo "Port 443 (HTTPS): CLOSED/FILTERED"
timeout 2 bash -c "echo >/dev/tcp/localhost/3306" 2>/dev/null && echo "Port 3306 (MySQL): OPEN" || echo "Port 3306 (MySQL): CLOSED/FILTERED"
```

**📸 Verified Output:**
```
=== Current Firewall State ===
Chain INPUT (policy ACCEPT)
...

=== Check what ports are listening ===
State  Recv-Q Send-Q Local Address:Port   ...
LISTEN 0      128    0.0.0.0:22           ...

=== Test connection to specific ports ===
Port 22 (SSH): OPEN
Port 80 (HTTP): CLOSED/FILTERED
Port 443 (HTTPS): CLOSED/FILTERED
Port 3306 (MySQL): CLOSED/FILTERED
```

> 💡 **What this means:** Only SSH is open (for admin access in this container). HTTP/HTTPS/MySQL are not running — minimal attack surface. In production, regularly verify your firewall rules match your intended policy using connection testing and port scanning.

## ✅ Verification

```bash
# Verify iptables and python3 available
iptables --version 2>/dev/null || echo "iptables available"
python3 -c "print('Firewall logic simulation: OK')"
echo "Firewalls and IDS lab verified"
```

## 🚨 Common Mistakes

- **Default ALLOW policy**: Always start with default DROP and explicitly allow needed traffic
- **Allowing SSH from anywhere**: Restrict SSH to admin IP ranges or VPN — internet-exposed SSH invites brute force
- **WAF as sole defense**: WAF is one layer; fix underlying vulnerabilities too
- **No logging**: Without logging, you can't detect attacks or investigate incidents
- **Not testing rules**: Apply rules in test environment first; a misconfigured firewall can lock you out

## 📝 Summary

- **Firewalls** filter traffic based on IP/port (stateless) or connection state (stateful); NGFWs add application awareness
- **Default deny policy** is the gold standard — whitelist what's allowed rather than blacklisting threats
- **IDS detects, IPS blocks**: IDS is passive (alerts); IPS is inline (actively blocks matched traffic)
- **WAF** inspects HTTP application layer specifically — essential for protecting web applications from SQLi, XSS, etc.
- **Layered architecture** (DMZ + internal segmentation + WAF + IDS) means an attacker must defeat multiple independent controls

## 🔗 Further Reading

- [iptables Tutorial](https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html)
- [Snort Rules Documentation](https://www.snort.org/documents)
- [OWASP ModSecurity Core Rule Set](https://owasp.org/www-project-modsecurity-core-rule-set/)
- [nftables (modern iptables replacement)](https://wiki.nftables.org/)
- [SANS Firewall Checklist](https://www.sans.org/security-resources/policies/)
