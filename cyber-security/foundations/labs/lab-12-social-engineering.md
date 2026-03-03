# Lab 12: Social Engineering

## 🎯 Objective
Understand social engineering attack types, identify phishing indicators, analyze URLs for spoofing, examine email headers, and learn SPF/DKIM/DMARC email authentication mechanisms.

## 📚 Background
Social engineering is the art of manipulating people into performing actions or divulging information rather than attacking technical systems directly. It exploits fundamental human traits: trust, fear, urgency, authority, curiosity, and the desire to be helpful. Cybersecurity professionals often say that humans are the weakest link — but properly trained humans can also be the strongest security control.

Phishing is the most common form of social engineering, using deceptive emails or messages to trick recipients into clicking malicious links, opening infected attachments, or entering credentials on fake websites. Spear phishing is targeted phishing with personalized content about the victim, making it far more convincing. Business Email Compromise (BEC) scams — where attackers impersonate executives to authorize fraudulent wire transfers — cost businesses billions annually.

Email authentication protocols (SPF, DKIM, DMARC) were created specifically to combat email spoofing. Understanding how they work helps security professionals both configure them correctly and recognize when they're absent or misconfigured.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Basic understanding of email and URLs
- Lab 03: DNS Fundamentals (helpful)

## 🛠️ Tools Used
- `python3` — URL analysis and header parsing
- `curl` — checking email records

## 🔬 Lab Instructions

### Step 1: Social Engineering Attack Types

```bash
python3 << 'EOF'
attacks = {
    "Phishing": {
        "description": "Mass emails impersonating legitimate organizations",
        "example": "Email from 'paypa1.com' claiming your account is suspended",
        "success_rate": "3-5% click rate (at scale = millions of victims)",
        "indicators": ["Generic greeting ('Dear Customer')", "Urgency", "Suspicious link", "Unexpected email"],
        "real_example": "2016 John Podesta email - password phishing - led to DNC breach"
    },
    "Spear Phishing": {
        "description": "Targeted phishing with personalized content about the victim",
        "example": "Email to Bob from 'IT dept' referencing his actual project name and manager",
        "success_rate": "~30% - highly effective due to personalization",
        "indicators": ["Looks legitimate but verify via phone", "References real details (OSINT gathered)"],
        "real_example": "2011 RSA SecureID breach - spear phishing Excel attachment"
    },
    "Whaling": {
        "description": "Spear phishing targeting executives (CEO, CFO, C-suite)",
        "example": "CEO receives email appearing to be from board member requesting urgent wire transfer",
        "success_rate": "High - executives often bypass security controls",
        "indicators": ["Executive target + financial request + urgency"],
        "real_example": "Mattel CFO wired $3M to fraudsters impersonating new CEO"
    },
    "Vishing": {
        "description": "Voice phishing - attacks via phone calls",
        "example": "Call claiming to be IRS threatening arrest unless gift cards purchased",
        "success_rate": "Variable - harder to verify caller identity",
        "indicators": ["Urgent action required", "Requests gift cards/wire", "Caller ID spoofed"],
        "real_example": "2020 Twitter hack - vishing IT support to get VPN credentials"
    },
    "Smishing": {
        "description": "SMS phishing - attacks via text messages",
        "example": "Text: 'Your package could not be delivered. Click here: amaz0n-delivery.com'",
        "success_rate": "Higher than email phishing (people trust SMS more)",
        "indicators": ["Suspicious links in SMS", "Unexpected package/bank messages"],
        "real_example": "FluBot Android malware spread via smishing"
    },
    "Pretexting": {
        "description": "Creating a fabricated scenario to gain trust before asking for information",
        "example": "Attacker calls HR pretending to be IT, needs to verify employee's SSN for a 'system migration'",
        "success_rate": "Very high - people want to be helpful",
        "indicators": ["Unusual request from 'authority'", "Requests sensitive information"],
        "real_example": "Hewlett-Packard spying scandal - private investigators used pretexting"
    },
    "Baiting": {
        "description": "Leaving infected USB drives or CDs in public hoping someone will plug them in",
        "example": "USB drive labeled 'Salary Information 2024' left in company parking lot",
        "success_rate": "~48% plug rate in studies",
        "indicators": ["Found USB/media devices", "Unexpected media in workplace"],
        "real_example": "Stuxnet spread via infected USB drives to air-gapped networks"
    },
}

for attack, info in attacks.items():
    print(f"\n{'='*65}")
    print(f"ATTACK: {attack}")
    print(f"Description: {info['description']}")
    print(f"Example:     {info['example']}")
    print(f"Success:     {info['success_rate']}")
    print(f"Real case:   {info['real_example']}")
EOF
```

**📸 Verified Output:**
```
=================================================================
ATTACK: Phishing
Description: Mass emails impersonating legitimate organizations
Example:     Email from 'paypa1.com' claiming your account is suspended
Success:     3-5% click rate (at scale = millions of victims)
Real case:   2016 John Podesta email - password phishing - led to DNC breach
...
```

> 💡 **What this means:** Social engineering works because it exploits psychology, not technology. Even technically sophisticated people fall for well-crafted attacks — awareness training and verification procedures are the primary defense.

### Step 2: Phishing Indicator Checklist

```bash
python3 << 'EOF'
print("PHISHING EMAIL INDICATOR CHECKLIST")
print("=" * 60)

indicators = [
    # (Category, Indicator, Red Flag Description)
    ("SENDER", "Generic greeting", "Dear Customer/User instead of your name"),
    ("SENDER", "Spoofed domain", "paypa1.com, amaz0n.com, g00gle.com"),
    ("SENDER", "Mismatched Reply-To", "From: ceo@company.com but Reply-To: evil@gmail.com"),
    ("SENDER", "Unexpected sender", "IT dept you've never heard from"),
    ("CONTENT", "Urgent language", "'Act NOW or your account will be DELETED'"),
    ("CONTENT", "Fear/threat", "'Legal action will be taken unless...'"),
    ("CONTENT", "Too good to be true", "'You've won $1,000,000!'"),
    ("CONTENT", "Grammar/spelling errors", "Legitimate orgs proofread carefully"),
    ("CONTENT", "Generic signature", "No specific company contact info"),
    ("CONTENT", "Request for credentials", "Legitimate orgs NEVER ask for passwords in email"),
    ("LINKS", "Hover reveals different URL", "Link text says paypal.com but URL is evil.com"),
    ("LINKS", "URL shorteners", "bit.ly, tinyurl hiding malicious destinations"),
    ("LINKS", "Lookalike domains", "support-microsoft.com vs microsoft.com"),
    ("LINKS", "HTTP not HTTPS", "Legitimate login pages always use HTTPS"),
    ("ATTACHMENTS", "Unexpected attachments", "Unexpected Word docs, Excel files, PDFs"),
    ("ATTACHMENTS", "Executable files", ".exe, .bat, .ps1, .vbs attachments"),
    ("ATTACHMENTS", "Password-protected zips", "Bypasses email security scanning"),
    ("TIMING", "After recent news event", "COVID-19 relief scams after pandemic started"),
    ("TIMING", "Tax season", "IRS scams spike February-April"),
    ("TIMING", "Holiday shopping", "Amazon/UPS/FedEx scams spike November-December"),
]

categories = {}
for cat, indicator, description in indicators:
    categories.setdefault(cat, []).append((indicator, description))

for category, items in categories.items():
    print(f"\n[{category}]")
    for indicator, description in items:
        print(f"  🚩 {indicator}")
        print(f"     → {description}")

print()
print("GOLDEN RULE: If in doubt, verify out-of-band")
print("  (Call the sender using a KNOWN GOOD number, not one in the email)")
EOF
```

**📸 Verified Output:**
```
PHISHING EMAIL INDICATOR CHECKLIST
============================================================

[SENDER]
  🚩 Generic greeting
     → Dear Customer/User instead of your name
  🚩 Spoofed domain
     → paypa1.com, amaz0n.com, g00gle.com
...
GOLDEN RULE: If in doubt, verify out-of-band
  (Call the sender using a KNOWN GOOD number, not one in the email)
```

> 💡 **What this means:** No single indicator proves phishing, but multiple indicators together are a strong signal. Teach users to pause and check before clicking — one click on a phishing link can lead to a major breach.

### Step 3: URL Analysis for Spoofing Detection

```bash
python3 << 'EOF'
from urllib.parse import urlparse
import re

def analyze_url(url):
    """Analyze a URL for phishing indicators."""
    issues = []
    indicators = []
    
    try:
        parsed = urlparse(url if url.startswith('http') else 'http://' + url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        
        # Check for HTTP vs HTTPS
        if url.startswith('http://'):
            issues.append("Uses HTTP (not HTTPS) - credentials sent unencrypted")
        
        # Check for suspicious TLD
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.click']
        for tld in suspicious_tlds:
            if hostname.endswith(tld):
                issues.append(f"Suspicious TLD: {tld}")
        
        # Check for brand names in subdomain (not main domain)
        brands = ['paypal', 'amazon', 'google', 'microsoft', 'apple', 'netflix', 'bank']
        domain_parts = hostname.split('.')
        if len(domain_parts) >= 3:
            for brand in brands:
                if brand in domain_parts[0] and brand not in '.'.join(domain_parts[-2:]):
                    issues.append(f"Brand '{brand}' in subdomain but not main domain")
        
        # Check for typosquatting patterns
        typo_patterns = [
            ('paypa1', 'paypal'), ('g00gle', 'google'), ('amaz0n', 'amazon'),
            ('rn' , 'm'), ('micros0ft', 'microsoft'), ('arnazon', 'amazon')
        ]
        for typo, real in typo_patterns:
            if typo in hostname:
                issues.append(f"Possible typosquatting: '{typo}' resembles '{real}'")
        
        # Check for IP address as hostname
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if ip_pattern.match(hostname):
            issues.append("IP address as hostname - legitimate sites use domain names")
        
        # Check for excessively long URL
        if len(url) > 100:
            issues.append(f"Suspicious URL length: {len(url)} chars (may be obfuscating destination)")
        
        # Check for multiple redirectors
        if url.count('http') > 1:
            issues.append("Multiple 'http' in URL - possible URL redirect chain")
        
        return hostname, issues
    
    except Exception as e:
        return url, [f"Could not parse URL: {e}"]

test_urls = [
    "https://www.paypal.com/login",
    "http://paypa1.com/account/verify",
    "https://paypal.security-alert.tk/login",
    "http://192.168.1.100/banking/login",
    "https://microsoft.com.maliciousdomain.com/login",
    "https://login.amazon.com/ap/signin",
    "http://amaz0n.com/order-confirm?id=12345&return=http://evil.com",
    "https://www.google.com",
]

print("URL PHISHING ANALYSIS")
print("=" * 70)
for url in test_urls:
    hostname, issues = analyze_url(url)
    status = "✅ LOOKS LEGITIMATE" if not issues else f"🚨 SUSPICIOUS ({len(issues)} issues)"
    print(f"\nURL: {url}")
    print(f"Status: {status}")
    for issue in issues:
        print(f"  ⚠️  {issue}")
EOF
```

**📸 Verified Output:**
```
URL PHISHING ANALYSIS
======================================================================

URL: https://www.paypal.com/login
Status: ✅ LOOKS LEGITIMATE

URL: http://paypa1.com/account/verify
Status: 🚨 SUSPICIOUS (2 issues)
  ⚠️  Uses HTTP (not HTTPS)
  ⚠️  Possible typosquatting: 'paypa1' resembles 'paypal'

URL: https://microsoft.com.maliciousdomain.com/login
Status: 🚨 SUSPICIOUS (1 issues)
  ⚠️  Brand 'microsoft' in subdomain but not main domain
```

> 💡 **What this means:** The domain is the part between the last two dots before the path (e.g., `microsoft.com` in `login.microsoft.com`). Attackers put legitimate brand names in subdomains (`microsoft.com.evil.com`) to confuse users.

### Step 4: Email Header Analysis

```bash
python3 << 'EOF'
# Sample email headers to analyze (simplified example)
sample_headers = """From: "PayPal Support" <support@paypa1-secure.com>
To: victim@company.com
Subject: URGENT: Your PayPal Account Has Been Suspended!
Date: Mon, 01 Mar 2026 20:00:00 +0000
Message-ID: <random123@paypa1-secure.com>
Reply-To: collect-data@evil-harvester.ru
Received: from mail.paypa1-secure.com (198.51.100.5)
  by mx.company.com (mx01.company.com) with SMTP
X-Originating-IP: 198.51.100.5
X-Spam-Status: No, score=2.1
Authentication-Results: mx.company.com;
  spf=fail (domain of paypa1-secure.com does not designate 198.51.100.5 as permitted sender)
  dkim=none (no signature)
  dmarc=fail (p=REJECT) header.from=paypa1-secure.com
"""

print("EMAIL HEADER ANALYSIS")
print("=" * 65)
print("\nRaw headers:")
print(sample_headers)

print("=" * 65)
print("RED FLAGS FOUND:")
red_flags = [
    ("From domain", "paypa1-secure.com", "Typosquatting PayPal + unusual 'secure' addition"),
    ("Reply-To", "evil-harvester.ru", "Replies go to Russia, not PayPal!"),
    ("SPF", "FAIL", "Sending IP not authorized by paypa1-secure.com DNS record"),
    ("DKIM", "none", "No digital signature - cannot verify message authenticity"),
    ("DMARC", "FAIL (p=REJECT)", "Email fails DMARC policy - should be rejected"),
    ("Subject", "URGENT: ... SUSPENDED!", "Classic urgency + fear tactic"),
    ("Originating IP", "198.51.100.5", "Check this IP in threat intelligence databases"),
]

for field, value, explanation in red_flags:
    print(f"\n  🚩 {field}: {value}")
    print(f"     {explanation}")

print("\n" + "=" * 65)
print("VERDICT: HIGH CONFIDENCE PHISHING")
print("Action: Report to IT security team, do NOT click any links")
print("        Delete email immediately")
EOF
```

**📸 Verified Output:**
```
EMAIL HEADER ANALYSIS
=================================================================

Raw headers:
From: "PayPal Support" <support@paypa1-secure.com>
...
Authentication-Results: mx.company.com;
  spf=fail ...
  dkim=none
  dmarc=fail ...

RED FLAGS FOUND:

  🚩 From domain: paypa1-secure.com
     Typosquatting PayPal + unusual 'secure' addition

  🚩 Reply-To: evil-harvester.ru
     Replies go to Russia, not PayPal!

  🚩 SPF: FAIL
     Sending IP not authorized...
```

> 💡 **What this means:** Email headers contain a wealth of forensic information. The Authentication-Results header is most important — SPF fail + DKIM none + DMARC fail is a strong phishing indicator your email gateway should block automatically.

### Step 5: SPF, DKIM, and DMARC Explained

```bash
python3 << 'EOF'
print("EMAIL AUTHENTICATION: SPF, DKIM, DMARC")
print("=" * 65)

print("""
┌──────────────────────────────────────────────────────────────────┐
│                    EMAIL AUTHENTICATION FLOW                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SPF (Sender Policy Framework) - DNS TXT record                  │
│  ─────────────────────────────────────────────                   │
│  "Only these IP addresses are allowed to send email for          │
│   my domain"                                                      │
│                                                                   │
│  Example DNS record:                                             │
│  paypal.com. TXT "v=spf1 ip4:204.14.232.0/21 include:           │
│                    spf.protection.outlook.com ~all"              │
│                                                                   │
│  ~all = softfail (accept but mark)                               │
│  -all = hardfail (reject)                                        │
│  +all = allow all (DANGEROUS - don't use)                        │
│                                                                   │
│  Problem: SPF only checks envelope sender, not From header       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DKIM (DomainKeys Identified Mail) - Cryptographic signature     │
│  ──────────────────────────────────────────────────────────      │
│  "I cryptographically signed this email with my private key.     │
│   Verify it with my public key in DNS."                          │
│                                                                   │
│  Example DNS record (public key):                                │
│  selector._domainkey.paypal.com TXT "v=DKIM1; k=rsa; p=MIGf..." │
│                                                                   │
│  Header added to email:                                          │
│  DKIM-Signature: v=1; a=rsa-sha256; d=paypal.com;               │
│                  s=selector; bh=<body hash>; b=<signature>       │
│                                                                   │
│  DKIM proves the email content wasn't modified and came from     │
│  someone with access to paypal.com's private key                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DMARC (Domain-based Message Authentication) - Policy            │
│  ────────────────────────────────────────────────────            │
│  "If SPF and/or DKIM fail for my domain, here's what to do       │
│   and send me reports"                                           │
│                                                                   │
│  Example DNS record:                                             │
│  _dmarc.paypal.com TXT "v=DMARC1; p=reject; rua=mailto:         │
│                          dmarc@paypal.com; pct=100"              │
│                                                                   │
│  p=none:     Do nothing (monitoring mode)                        │
│  p=quarantine: Put in spam folder                                │
│  p=reject:   Reject the email (strongest protection)            │
│                                                                   │
│  DMARC aggregates SPF + DKIM and adds reporting                  │
└──────────────────────────────────────────────────────────────────┘
""")

print("CHECKING EMAIL AUTHENTICATION RECORDS:")
print("To check a domain's email auth configuration:")
print("  dig TXT _dmarc.paypal.com")
print("  dig TXT paypal.com | grep spf")
print("  dig TXT selector._domainkey.paypal.com")
print()
print("Online tools:")
print("  https://mxtoolbox.com/dmarc.aspx")
print("  https://dmarcly.com/tools/dmarc-check")

# Try to check a real domain
import subprocess
try:
    result = subprocess.run(['dig', '+short', 'TXT', '_dmarc.google.com'],
                          capture_output=True, text=True, timeout=5)
    if result.stdout:
        print(f"\nGoogle's DMARC record:")
        print(f"  {result.stdout.strip()}")
except:
    print("\n(DNS lookup for verification - run: dig TXT _dmarc.google.com)")
EOF
```

**📸 Verified Output:**
```
EMAIL AUTHENTICATION: SPF, DKIM, DMARC
=================================================================

┌──────────────────────────────────────────────────────────────────┐
│                    EMAIL AUTHENTICATION FLOW                      │
...
│  SPF (Sender Policy Framework) - DNS TXT record                  │
...
│  DKIM (DomainKeys Identified Mail) - Cryptographic signature     │
...
│  DMARC (Domain-based Message Authentication) - Policy            │
...
```

> 💡 **What this means:** Implement all three (SPF + DKIM + DMARC with p=reject) to prevent attackers from sending emails that appear to come from your domain. This is one of the most impactful email security configurations available.

### Step 6: Security Awareness Training Content

```bash
python3 << 'EOF'
print("SOCIAL ENGINEERING DEFENSE TRAINING")
print("=" * 60)

scenarios = [
    {
        "scenario": "You receive an email from IT saying your password expires today and to click here to reset it",
        "correct_action": "Do NOT click the link. Call IT directly using the internal phone directory number",
        "why": "IT should never send password reset links via email. Call to verify",
    },
    {
        "scenario": "Stranger in the parking lot asks you to badge them into the building - they say they forgot their badge",
        "correct_action": "Politely decline. Direct them to reception/security desk to get visitor pass",
        "why": "Tailgating is a common physical access technique. Even if genuine, they should go through proper channels",
    },
    {
        "scenario": "CEO calls your mobile asking you to urgently wire $50,000 to a vendor - CFO is unavailable",
        "correct_action": "Hang up. Call CEO's KNOWN number back. Verify through CFO's assistant. Follow wire transfer approval process",
        "why": "BEC (Business Email Compromise) and CEO fraud via phone is extremely common. Always verify through secondary channel",
    },
    {
        "scenario": "You find a USB drive labeled 'Confidential - Employee Salaries 2024' in the bathroom",
        "correct_action": "Do NOT plug it in. Turn it in to IT security immediately",
        "why": "Baiting attack. USB could contain malware that auto-runs on Windows and installs a backdoor",
    },
    {
        "scenario": "Pop-up says your computer is infected with 1,247 viruses - call 1-800-555-0199 NOW",
        "correct_action": "Close the browser tab (Ctrl+W or Alt+F4). Do not call the number",
        "why": "Tech support scam. Legitimate antivirus never asks you to call a phone number",
    },
]

for i, s in enumerate(scenarios, 1):
    print(f"\nScenario {i}: {s['scenario']}")
    print(f"  ✅ Correct Action: {s['correct_action']}")
    print(f"  💡 Why: {s['why']}")

print("\n" + "=" * 60)
print("THE 5 PRINCIPLES ATTACKERS EXPLOIT:")
principles = [
    ("Urgency", "Creates panic so you act without thinking"),
    ("Authority", "Impersonates boss, IT, IRS, police"),
    ("Social Proof", "'Everyone else has already updated their password'"),
    ("Reciprocity", "'I'm trying to help you - just need your ID'"),
    ("Scarcity", "'This offer expires in 10 minutes'"),
]
for principle, explanation in principles:
    print(f"  • {principle}: {explanation}")
EOF
```

**📸 Verified Output:**
```
SOCIAL ENGINEERING DEFENSE TRAINING
============================================================

Scenario 1: You receive an email from IT saying your password expires today...
  ✅ Correct Action: Do NOT click the link. Call IT directly...
  💡 Why: IT should never send password reset links via email.

Scenario 2: Stranger in the parking lot asks you to badge them in...
  ✅ Correct Action: Politely decline. Direct them to reception...
```

> 💡 **What this means:** Security awareness training with realistic scenarios is far more effective than generic "don't click links" advice. Practice identifying the psychological manipulation tactics — urgency and authority are the most commonly exploited.

### Step 7: Phishing Simulation Metrics

```bash
python3 << 'EOF'
# Typical phishing simulation metrics
print("PHISHING SIMULATION PROGRAM METRICS")
print("=" * 55)

simulation_data = {
    "Campaign 1 (Pre-training)": {
        "emails_sent": 500,
        "opened": 340,
        "clicked": 85,
        "submitted_credentials": 45,
        "reported_to_security": 12,
    },
    "Campaign 2 (After basic training)": {
        "emails_sent": 500,
        "opened": 280,
        "clicked": 42,
        "submitted_credentials": 18,
        "reported_to_security": 67,
    },
    "Campaign 3 (After advanced training)": {
        "emails_sent": 500,
        "opened": 250,
        "clicked": 18,
        "submitted_credentials": 5,
        "reported_to_security": 145,
    },
}

for campaign, data in simulation_data.items():
    click_rate = (data["clicked"] / data["emails_sent"]) * 100
    report_rate = (data["reported_to_security"] / data["emails_sent"]) * 100
    print(f"\n{campaign}:")
    print(f"  Emails sent:           {data['emails_sent']}")
    print(f"  Click rate:            {data['clicked']}/{data['emails_sent']} = {click_rate:.1f}%")
    print(f"  Credential submission: {data['submitted_credentials']}")
    print(f"  Reported to security:  {data['reported_to_security']} ({report_rate:.1f}%)")

print()
print("KEY INSIGHT: Training reduced clicks by 79% and")
print("             increased reporting by 1,108%!")
print()
print("Industry benchmarks:")
print("  Baseline click rate:     14-30%")
print("  After training target:   <5%")
print("  Best-in-class:           <2%")
print()
print("Remember: The REPORTING rate is as important as the click rate")
print("  Users who report are your 'human IDS' sensors")
EOF
```

**📸 Verified Output:**
```
PHISHING SIMULATION PROGRAM METRICS
=======================================================

Campaign 1 (Pre-training):
  Emails sent:           500
  Click rate:            85/500 = 17.0%
  Credential submission: 45
  Reported to security:  12 (2.4%)

Campaign 3 (After advanced training):
  Click rate:            18/500 = 3.6%
  Reported to security:  145 (29.0%)

KEY INSIGHT: Training reduced clicks by 79% and
             increased reporting by 1,108%!
```

> 💡 **What this means:** Security awareness training dramatically reduces phishing success rates. Equally important is building a reporting culture where employees feel safe and rewarded for reporting suspicious activity — even if they did click.

### Step 8: Build Your Defense Plan

```bash
python3 << 'EOF'
print("SOCIAL ENGINEERING DEFENSE FRAMEWORK")
print("=" * 60)

defenses = {
    "Technical Controls": [
        "Email gateway with SPF/DKIM/DMARC enforcement",
        "Email sandbox - detonate attachments safely",
        "URL filtering - block known malicious sites",
        "MFA on all systems (defeats credential phishing)",
        "Browser isolation for risky browsing",
        "Endpoint detection and response (EDR)",
    ],
    "Process Controls": [
        "Out-of-band verification for wire transfers",
        "Dual-approval for financial transactions >$X",
        "Vendor payment change verification process",
        "USB policy (disable USB ports on workstations)",
        "Visitor management and badge policy",
        "Clear incident reporting procedures",
    ],
    "People Controls": [
        "Regular phishing simulation exercises",
        "Security awareness training (annual + events)",
        "Just-in-time training when someone fails a sim",
        "No-blame reporting culture",
        "Reward reporting of suspicious activity",
        "Department-specific training (finance gets BEC training)",
    ],
    "Detective Controls": [
        "Email analytics for unusual patterns",
        "SIEM rules for multiple failed login attempts",
        "UEBA for behavioral anomalies",
        "Dark web monitoring for credential leaks",
        "Report phishing mailbox with auto-analysis",
    ],
}

for category, controls in defenses.items():
    print(f"\n[{category}]")
    for control in controls:
        print(f"  ✓ {control}")

print()
print("INCIDENT RESPONSE FOR SOCIAL ENGINEERING:")
print("  1. Contain: Disable compromised account immediately")
print("  2. Assess: What access did attacker have?")
print("  3. Investigate: Email logs, web logs, endpoint telemetry")
print("  4. Remediate: Reset passwords, revoke tokens")
print("  5. Notify: Legal/compliance requirements may apply")
print("  6. Learn: Update defenses based on attack technique")
EOF
```

**📸 Verified Output:**
```
SOCIAL ENGINEERING DEFENSE FRAMEWORK
============================================================

[Technical Controls]
  ✓ Email gateway with SPF/DKIM/DMARC enforcement
  ✓ Email sandbox - detonate attachments safely
  ...

[People Controls]
  ✓ Regular phishing simulation exercises
  ✓ No-blame reporting culture
  ...
```

> 💡 **What this means:** Effective social engineering defense requires all three control types working together. Technical controls alone cannot stop targeted phishing — humans need training. Process controls close gaps that tech can't address.

## ✅ Verification

```bash
python3 -c "
# Verify URL parsing works
from urllib.parse import urlparse
url = 'https://paypa1.com/login'
parsed = urlparse(url)
print(f'Domain: {parsed.netloc}')
print('paypa1' in parsed.netloc and 'Typosquatting detected!' or 'Clean URL')
print('Social engineering lab verified')
"
```

## 🚨 Common Mistakes

- **Thinking "it won't happen to me"**: Sophisticated attackers research targets thoroughly — anyone can be a victim
- **Trusting caller ID**: Caller ID is trivially spoofed. Always verify via known-good contact information
- **Not reporting suspicious emails**: Reporting helps security team block the campaign and protect colleagues
- **Security theater training**: Annual compliance videos don't improve behavior — regular simulations with feedback do
- **Technical-only defenses**: Email filters alone don't stop all phishing; human training is essential

## 📝 Summary

- **Social engineering** exploits human psychology (urgency, authority, trust) rather than technical vulnerabilities
- **Attack types** include phishing (mass), spear phishing (targeted), whaling (executives), vishing (voice), smishing (SMS), baiting, and pretexting
- **URL analysis** can reveal spoofed domains — check the actual domain (between last two dots), not just what appears in display text
- **SPF + DKIM + DMARC** together prevent domain spoofing — implement all three with p=reject policy
- **Training with phishing simulations** dramatically reduces click rates and increases reporting — build a no-blame reporting culture

## 🔗 Further Reading

- [SANS Social Engineering Defense](https://www.sans.org/white-papers/social-engineering/)
- [FBI BEC Advisory](https://www.ic3.gov/Home/BEC)
- [Google Phishing Quiz](https://phishingquiz.withgoogle.com/)
- [DMARC.org Implementation Guide](https://dmarc.org/overview/)
- [Have I Been Pwned](https://haveibeenpwned.com/)
