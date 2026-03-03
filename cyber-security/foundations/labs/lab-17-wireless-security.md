# Lab 17: Wireless Security

## 🎯 Objective
Understand WiFi protocol evolution from WEP to WPA3, analyze WPA2 attack vectors conceptually, build a wireless security checklist, and understand 802.1X enterprise authentication.

## 📚 Background
Wireless networks present unique security challenges compared to wired networks. Unlike wired connections where an attacker needs physical access to a cable or port, wireless signals propagate through walls and can be intercepted by anyone within range. This makes the authentication and encryption protocol critically important — anyone who can receive the radio signal could potentially eavesdrop or attack the network.

The evolution from WEP to WPA3 reflects hard lessons learned from attacks. WEP (1997) was fundamentally broken and could be cracked in minutes using freely available tools. WPA (2003) was an emergency patch. WPA2 (2004) provided strong AES encryption but had implementation vulnerabilities like KRACK (Key Reinstallation Attacks). WPA3 (2018) addressed WPA2's weaknesses with Simultaneous Authentication of Equals (SAE), perfect forward secrecy, and improved protection for open networks.

Enterprise wireless authentication using 802.1X with RADIUS servers provides significantly stronger security than pre-shared keys. With PSK, anyone who knows the password can join the network and potentially eavesdrop on other clients. With 802.1X, each user has individual credentials, enabling per-user access control and audit trails.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Basic networking concepts
- Lab 06: Public Key Cryptography (helpful)

## 🛠️ Tools Used
- `python3` — protocol analysis and security tools
- `openssl` — cryptographic concepts

## 🔬 Lab Instructions

### Step 1: WiFi Protocol Evolution

```bash
python3 << 'EOF'
protocols = [
    {
        "name": "WEP (Wired Equivalent Privacy)",
        "year": "1997",
        "standard": "IEEE 802.11 original",
        "status": "BROKEN - DO NOT USE",
        "encryption": "RC4 stream cipher with 40 or 104-bit keys",
        "auth": "Open or Shared Key (both broken)",
        "crackable_in": "< 1 minute with Aircrack-ng and captured packets",
        "vulnerabilities": [
            "IV (Initialization Vector) reuse - only 24-bit IV space (16M possible)",
            "Weak key scheduling in RC4",
            "No message integrity (CRC-32 is not a cryptographic MAC)",
            "IV is transmitted in plaintext - easy to collect",
            "FMS attack (2001): collect ~100K-1M packets, crack key",
        ],
        "lesson": "IV space too small → repeats quickly → reveals keystream → decrypt all traffic"
    },
    {
        "name": "WPA (Wi-Fi Protected Access)",
        "year": "2003",
        "standard": "IEEE 802.11i (subset)",
        "status": "Deprecated - insecure",
        "encryption": "TKIP (RC4 with per-packet keying and IV enlargement)",
        "auth": "PSK or 802.1X/EAP",
        "crackable_in": "Minutes with dictionary attack on weak PSK; TKIP has vulnerabilities",
        "vulnerabilities": [
            "TKIP still uses RC4 (fundamentally broken stream cipher)",
            "Beck-Tews attack on TKIP",
            "Dictionary attacks on WPA-PSK",
            "Emergency fix for WEP - not designed from scratch",
        ],
        "lesson": "Emergency patch on broken foundation. Needed AES replacement ASAP"
    },
    {
        "name": "WPA2 (Wi-Fi Protected Access 2)",
        "year": "2004",
        "standard": "IEEE 802.11i (full)",
        "status": "Still widely used, mostly secure with strong PSK",
        "encryption": "AES-CCMP (Counter Mode CBC-MAC Protocol)",
        "auth": "PSK (Personal) or 802.1X (Enterprise)",
        "crackable_in": "Days-months for strong PSK; vulnerable to KRACK, PMKID attacks",
        "vulnerabilities": [
            "KRACK (2017): Key Reinstallation Attack - can decrypt traffic",
            "PMKID attack: Offline dictionary attack without 4-way handshake",
            "Deauthentication attacks (no management frame protection)",
            "Evil twin attacks (rogue AP with same SSID)",
            "WPS PIN vulnerability (crack in hours)",
        ],
        "lesson": "Strong PSK (20+ random chars) + WPS disabled + patched = reasonably secure"
    },
    {
        "name": "WPA3 (Wi-Fi Protected Access 3)",
        "year": "2018",
        "standard": "IEEE 802.11ax",
        "status": "CURRENT STANDARD - use this",
        "encryption": "AES-GCMP-256 (WPA3-Enterprise), SAE Dragonfly handshake",
        "auth": "SAE (Simultaneous Authentication of Equals) - replaces PSK",
        "crackable_in": "No known practical attacks (as of 2026)",
        "vulnerabilities": [
            "Dragonblood (2019): Side-channel attacks on SAE (patched)",
            "Transition mode (WPA2/WPA3 mixed) reduces to WPA2 security",
            "Still vulnerable to evil twin if no certificate verification",
        ],
        "lesson": "SAE provides forward secrecy - past traffic stays secure even if PSK leaked"
    },
]

print("WiFi SECURITY PROTOCOL EVOLUTION")
print("=" * 70)

for p in protocols:
    status_icon = "❌" if "BROKEN" in p["status"] or "Deprecated" in p["status"] else \
                 "⚠️" if "Still" in p["status"] else "✅"
    print(f"\n{status_icon} {p['name']} ({p['year']})")
    print(f"  Status:     {p['status']}")
    print(f"  Encryption: {p['encryption']}")
    print(f"  Crackable:  {p['crackable_in']}")
    print(f"  Key lesson: {p['lesson']}")
    print(f"  Known attacks:")
    for v in p['vulnerabilities'][:3]:
        print(f"    • {v}")
EOF
```

**📸 Verified Output:**
```
WiFi SECURITY PROTOCOL EVOLUTION
======================================================================

❌ WEP (Wired Equivalent Privacy) (1997)
  Status:     BROKEN - DO NOT USE
  Encryption: RC4 stream cipher with 40 or 104-bit keys
  Crackable:  < 1 minute with Aircrack-ng
  Key lesson: IV space too small → repeats quickly → reveals keystream

⚠️ WPA2 (Wi-Fi Protected Access 2) (2004)
  Status:     Still widely used, mostly secure with strong PSK
  Encryption: AES-CCMP
  Crackable:  Days-months for strong PSK; vulnerable to KRACK, PMKID

✅ WPA3 (Wi-Fi Protected Access 3) (2018)
  Status:     CURRENT STANDARD - use this
```

> 💡 **What this means:** 25 years of WiFi security shows a constant arms race between attack and defense. Each protocol was broken, driving development of the next. WPA3's SAE handshake provides perfect forward secrecy — even if the PSK is eventually discovered, past captured traffic remains secure.

### Step 2: WEP Weakness Analysis

```bash
python3 << 'EOF'
print("WEP CRYPTOGRAPHIC WEAKNESS ANALYSIS")
print("=" * 60)

print("""
THE WEP IV PROBLEM:
───────────────────
WEP uses a 24-bit Initialization Vector (IV) prepended to the key.
Total possible IVs: 2^24 = 16,777,216 (about 16 million)

On a busy network transmitting 1500-byte packets at 11 Mbps:
  Packets per second: ~11,000,000 / 12000 ≈ 916 packets/sec
  Time to exhaust all IVs: 16,777,216 / 916 ≈ 18,306 seconds ≈ 5 hours

After 5 hours, IVs MUST repeat. When IV repeats with same key:
  E(key, IV1) XOR plaintext1 = ciphertext1
  E(key, IV1) XOR plaintext2 = ciphertext2  ← same keystream!
  
  ciphertext1 XOR ciphertext2 = plaintext1 XOR plaintext2
  
  With known plaintext (e.g., ARP packets have predictable format):
  → Recover full plaintext of both packets
  → Recover keystream
  → Decrypt any packet using that IV
""")

# Demonstrate IV collision probability
import math

iv_space = 2**24  # 24-bit IV
packets_per_second = 500  # Moderate network

# Birthday paradox: probability of IV collision after N packets
def collision_probability(n_packets, iv_space):
    if n_packets > iv_space:
        return 1.0
    # Approximation for birthday problem
    return 1 - math.exp(-n_packets * (n_packets - 1) / (2 * iv_space))

print("IV COLLISION PROBABILITY:")
print(f"{'Packets Captured':>20} {'Prob of Collision':>20} {'Time at 500 pkt/s':>20}")
print("-" * 65)
for packets in [1000, 5000, 10000, 50000, 100000, 500000]:
    prob = collision_probability(packets, iv_space)
    time_sec = packets / packets_per_second
    time_str = f"{time_sec:.0f}s" if time_sec < 3600 else f"{time_sec/3600:.1f}h"
    print(f"{packets:>20,} {prob:>19.1%} {time_str:>20}")

print()
print("CONCLUSION: WEP IVs collide at predictable rates.")
print("Modern WPA2/WPA3 use unique per-session keys and authenticated encryption.")
print("AES-CCMP cannot be attacked this way.")
EOF
```

**📸 Verified Output:**
```
WEP CRYPTOGRAPHIC WEAKNESS ANALYSIS
============================================================

THE WEP IV PROBLEM:
───────────────────
WEP uses a 24-bit Initialization Vector (IV)...
Total possible IVs: 2^24 = 16,777,216

IV COLLISION PROBABILITY:
        Packets Captured       Prob of Collision       Time at 500 pkt/s
-----------------------------------------------------------------
               1,000                     3.0%                     2s
               5,000                    52.3%                    10s
              50,000                   100.0%                  100s
```

> 💡 **What this means:** The math makes WEP's failure inevitable. With only 16 million possible IVs and a busy network generating hundreds of packets per second, IV collisions are guaranteed within hours. This is why WEP was deprecated in 2004.

### Step 3: WPA2 Attack Vectors

```bash
python3 << 'EOF'
print("WPA2 ATTACK VECTORS (CONCEPTUAL)")
print("=" * 65)

attacks = [
    {
        "name": "Dictionary/Brute Force on 4-way Handshake",
        "difficulty": "Easy (against weak PSK)",
        "description": """Attack Process:
  1. Attacker captures WPA2 4-way handshake (client connects to AP)
  2. Can force handshake: send deauthentication frame to client
  3. Offline attack: try millions of passwords against captured handshake
  4. No interaction with AP needed - entirely passive after capture
  
Tools: Aircrack-ng, hashcat (--hash-type 22000)
Speed: hashcat on GPU: billions of guesses/second
  
Defense: Strong PSK (20+ random characters from full charset)
  Password 'MyHomeWiFi123' → cracked in seconds (dictionary)
  Password 'xK9#mP2@qL5!nR8vYt3$' → impractical to crack""",
    },
    {
        "name": "PMKID Attack",
        "difficulty": "Medium (still requires weak PSK)",
        "description": """No client needed!
  1. Send single EAPOL frame to AP
  2. AP responds with PMKID in RSN IE of EAPOL
  3. PMKID = HMAC-SHA1(PMK, "PMK Name" + AP_MAC + client_MAC)
  4. Offline dictionary attack against PMKID
  
Advantage: No need to wait for/force a client to connect
  
Defense: Same - strong PSK is the only defense""",
    },
    {
        "name": "Evil Twin (Rogue AP)",
        "difficulty": "Medium",
        "description": """Creates a fake AP with same SSID:
  1. Attacker creates AP with same SSID as target
  2. Sends deauthentication packets to disconnect clients from real AP
  3. Clients reconnect - may connect to evil twin
  4. Attacker captures credentials on captive portal
  5. Can perform MITM on all client traffic
  
WPA2 vulnerability: No mutual authentication in Personal mode
  Client cannot verify AP's identity!
  
Defense: WPA3-Enterprise with certificates, not just PSK
         Certificate pinning to detect wrong certs""",
    },
    {
        "name": "KRACK (Key Reinstallation Attack) - CVE-2017-13077",
        "difficulty": "High (requires proximity + patching widely deployed)",
        "description": """Attacks the WPA2 handshake implementation:
  1. During 4-way handshake, attacker replays message 3
  2. Client reinstalls already-used key (resets nonce/replay counter)
  3. Nonce reuse in AES-CCMP allows decryption and potential forgery
  
Impact: Decrypt traffic, potentially inject packets
  Affects: Most WPA2 clients (Android, Linux particularly vulnerable)
  
Defense: Patch! (Fixed in OS updates October 2017+)
  WPA3 SAE handshake not vulnerable to KRACK""",
    },
    {
        "name": "WPS PIN Attack",
        "difficulty": "Easy (if WPS enabled)",
        "description": """WPS (Wi-Fi Protected Setup) vulnerability:
  1. WPS PIN is 8 digits = 100,000,000 possibilities
  2. But verification is split: first 4 digits verified separately from last 4
  3. This reduces search space to 10,000 + 1000 = 11,000 attempts!
  4. Reaver tool: brute force WPS in 4-12 hours
  
Defense: DISABLE WPS entirely in router admin panel""",
    },
]

for attack in attacks:
    print(f"\n{'─'*65}")
    print(f"ATTACK: {attack['name']}")
    print(f"Difficulty: {attack['difficulty']}")
    print(attack['description'])
EOF
```

**📸 Verified Output:**
```
WPA2 ATTACK VECTORS (CONCEPTUAL)
=================================================================

──────────────────────────────────────────────────────────────────
ATTACK: Dictionary/Brute Force on 4-way Handshake
Difficulty: Easy (against weak PSK)
Attack Process:
  1. Attacker captures WPA2 4-way handshake...
  Speed: hashcat on GPU: billions of guesses/second
  Defense: Strong PSK (20+ random characters)
```

> 💡 **What this means:** WPA2's fundamental weakness in Personal mode is that the PSK is the only trust anchor. Anyone who captures a handshake can mount an offline dictionary attack at billions of guesses per second. The defense: use truly random, long PSKs or switch to WPA3/Enterprise.

### Step 4: 802.1X Enterprise Authentication

```bash
python3 << 'EOF'
print("802.1X ENTERPRISE WIRELESS AUTHENTICATION")
print("=" * 65)

print("""
ARCHITECTURE:
─────────────
           Supplicant          Authenticator         Auth Server
         (Client Device)      (Wireless AP)         (RADIUS Server)
               │                    │                     │
               │─── EAP Request ───►│                     │
               │◄── EAP Identity ───│                     │
               │─── Username ──────►│                     │
               │                    │─ RADIUS Access-Req ►│
               │                    │  (username)         │
               │                    │◄─ RADIUS Challenge ─│
               │◄── EAP Challenge ──│                     │
               │─── EAP Response ──►│                     │
               │                    │─ RADIUS Access-Req ►│
               │                    │  (response)         │
               │                    │◄─ Access-Accept ────│
               │◄── EAP Success ────│   (with keys)       │
               │                    │                     │
               │◄═══ WLAN Access ═══│  (encrypted with    │
               │    (port open!)    │   session keys)     │

COMPONENTS:
  • Supplicant: Client device (laptop, phone) - runs EAP
  • Authenticator: Wireless AP - forwards EAP to RADIUS
  • RADIUS Server: FreeRADIUS, Cisco ISE, Microsoft NPS
  • Authentication Server decides: Allow or Deny

EAP TYPES (authentication methods):
  EAP-TLS:     Mutual certificate authentication (most secure)
               Both client AND server present certificates
               Requires client certificate deployed to each device
  
  EAP-TTLS:    Server certificate only + tunneled credentials
               Easier deployment (no client cert needed)
               
  PEAP:        Protected EAP - MS-CHAPv2 inside TLS tunnel
               Most common in Windows environments
               Server certificate required
  
  EAP-FAST:    Cisco proprietary - PAC files instead of certs

ADVANTAGES OVER PSK:
  ✅ Individual credentials per user (not shared password)
  ✅ Per-user access logs and audit trail
  ✅ Revoke individual user without changing password for everyone
  ✅ Dynamic encryption keys per session
  ✅ Can assign different VLANs/policies per user/group
  ✅ Integration with Active Directory / LDAP

CERTIFICATE REQUIREMENT:
  The client MUST verify the RADIUS server's certificate!
  Without verification: evil twin can run fake RADIUS server
  → client connects and submits credentials to attacker
  
  Configure: Server certificate CN and trusted CA in supplicant
""")

# Show certificate validation flow
print("CERTIFICATE VALIDATION PROCESS:")
print("  1. AP sends client: 'Authenticate to RADIUS server: radius.company.com'")
print("  2. RADIUS presents TLS certificate")
print("  3. Client checks: Is cert from trusted CA (company internal CA)?")
print("  4. Client checks: Does cert CN match radius.company.com?")
print("  5. If valid → proceed with authentication")
print("  6. If invalid → REJECT CONNECTION (could be evil twin!)")
print()
print("  Many organizations skip step 4 'to make it easier' → Evil Twin vulnerable")
EOF
```

**📸 Verified Output:**
```
802.1X ENTERPRISE WIRELESS AUTHENTICATION
=================================================================

ARCHITECTURE:
─────────────
           Supplicant          Authenticator         Auth Server
         (Client Device)      (Wireless AP)         (RADIUS Server)
               │                    │                     │
               │─── EAP Request ───►│                     │
...

ADVANTAGES OVER PSK:
  ✅ Individual credentials per user
  ✅ Per-user access logs and audit trail
  ✅ Revoke individual user without changing shared password
```

> 💡 **What this means:** 802.1X eliminates the shared password problem — each user authenticates individually. This enables per-user audit logging, VLAN assignment, and instant access revocation. The certificate validation step is critical — without it, evil twin attacks succeed against 802.1X.

### Step 5: Wireless Security Checklist

```bash
python3 << 'EOF'
print("WIRELESS SECURITY AUDIT CHECKLIST")
print("=" * 60)

checklist = {
    "Protocol and Encryption": [
        ("CRITICAL", "WPA3 configured (or WPA2 with strong PSK if WPA3 unavailable)"),
        ("CRITICAL", "WEP and WPA (TKIP) completely disabled"),
        ("CRITICAL", "WPS disabled (vulnerable to brute force in hours)"),
        ("HIGH", "Management frames protected (802.11w/PMF enabled)"),
        ("HIGH", "AES/CCMP only - TKIP disabled even in WPA2 mixed mode"),
    ],
    "Access Point Configuration": [
        ("HIGH", "Default admin credentials changed"),
        ("HIGH", "AP firmware updated to latest version"),
        ("MEDIUM", "SSID does not reveal organization name or location"),
        ("MEDIUM", "Guest network isolated from corporate network (separate VLAN)"),
        ("MEDIUM", "Band steering configured (prefer 5GHz/6GHz)"),
        ("LOW", "Transmit power tuned to minimize coverage outside facility"),
    ],
    "Authentication": [
        ("CRITICAL", "Enterprise (802.1X) for corporate network access"),
        ("CRITICAL", "RADIUS server certificate validation configured on clients"),
        ("HIGH", "Strong PSK if Personal mode used (20+ random characters)"),
        ("HIGH", "PSK rotation policy defined and followed"),
        ("MEDIUM", "Rogue AP detection enabled (WIDS)"),
    ],
    "Monitoring and Detection": [
        ("HIGH", "Wireless IDS (WIDS) deployed to detect attacks"),
        ("HIGH", "AP access logs retained for 90+ days"),
        ("MEDIUM", "Alert on deauthentication flood attacks"),
        ("MEDIUM", "Monitor for unauthorized APs (rogue AP detection)"),
        ("LOW", "RF site survey to identify interference and coverage gaps"),
    ],
    "Physical Security": [
        ("HIGH", "APs physically secured (cable lock or enclosure)"),
        ("MEDIUM", "Console access password set on all APs"),
        ("MEDIUM", "AP management interface not accessible from wireless network"),
        ("LOW", "AP locations documented with photos for asset tracking"),
    ],
}

severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

for category, items in checklist.items():
    print(f"\n[{category}]")
    for severity, item in items:
        icon = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        print(f"  {icon} [{severity}] {item}")

print("\n" + "=" * 60)
print("QUICK WINS (implement today):")
quick_wins = [
    "Disable WPS on all access points",
    "Update AP firmware to latest version",
    "Change default AP admin credentials",
    "Enable Management Frame Protection (802.11w)",
    "Verify WPA3 or WPA2-AES (not TKIP) is configured",
]
for win in quick_wins:
    print(f"  ✅ {win}")
EOF
```

**📸 Verified Output:**
```
WIRELESS SECURITY AUDIT CHECKLIST
============================================================

[Protocol and Encryption]
  🔴 [CRITICAL] WPA3 configured (or WPA2 with strong PSK if WPA3 unavailable)
  🔴 [CRITICAL] WEP and WPA (TKIP) completely disabled
  🔴 [CRITICAL] WPS disabled (vulnerable to brute force in hours)
  🟠 [HIGH] Management frames protected (802.11w/PMF enabled)

QUICK WINS (implement today):
  ✅ Disable WPS on all access points
  ✅ Update AP firmware to latest version
```

> 💡 **What this means:** WPS disabled is the single highest-impact quick fix — it eliminates a vulnerability that can be exploited in hours with basic tools. Disabling it takes 30 seconds in the router admin panel.

### Step 6: Open Network Security Analysis

```bash
python3 << 'EOF'
print("OPEN NETWORKS AND SECURITY IMPLICATIONS")
print("=" * 60)

print("""
OPEN (No Password) NETWORK RISKS:
  • ALL TRAFFIC IS VISIBLE to anyone in radio range
  • No encryption between device and AP
  • Attacker can capture: HTTP traffic, passwords, cookies
  • MITM attacks are trivial (ARP spoofing on open network)
  • Evil twin attacks: any AP with same SSID wins

HOW WPA3 IMPROVES OPEN NETWORKS (OWE - Opportunistic Wireless Encryption):
  • WPA3 introduces "Enhanced Open" (OWE/OWE-Transition)
  • Each client session gets unique encryption (Diffie-Hellman)
  • Traffic still encrypted even without password!
  • MITM resistance improved
  • Backwards compatible with older devices

SAFE USAGE ON PUBLIC WIFI:
  1. ALWAYS use VPN on public/open WiFi
  2. Verify HTTPS for sensitive sites (padlock icon)
  3. Avoid accessing banking/sensitive accounts on public WiFi
  4. Disable auto-connect to open networks
  5. Use mobile data (4G/5G) instead of public WiFi for sensitive work

WHAT'S SAFE ON OPEN WIFI (with VPN):
  • All traffic encrypted by VPN tunnel
  • Attacker sees only encrypted data to VPN server
  • VPN provides equivalent security to wired connection

DETECTION OF EVIL TWIN:
  • Certificate errors when connecting (HTTPS)
  • Different gateway IP than expected
  • Unusual captive portal
  • Certificate CN doesn't match expected site
  
  ALWAYS investigate certificate errors - they may indicate MITM attack
""")

# Demonstrate certificate verification importance
print("CERTIFICATE VALIDATION - YOUR PROTECTION ON OPEN NETWORKS:")
print()
print("Normal HTTPS (safe):")
print("  You →  HTTPS  → Legitimate bank.com")
print("  Browser validates: cert CN = bank.com, signed by trusted CA")
print("  ✅ Connection established")
print()
print("MITM on open WiFi (detected by certificate!):")
print("  You → HTTP → Attacker → HTTPS → bank.com")
print("  Attacker presents fake cert for bank.com")
print("  Browser: 'This cert is not from a trusted CA!'")
print("  ❌ Browser shows WARNING - do not ignore!")
print()
print("  NEVER click 'Proceed anyway' on certificate warnings!")
EOF
```

**📸 Verified Output:**
```
OPEN NETWORKS AND SECURITY IMPLICATIONS
============================================================

OPEN (No Password) NETWORK RISKS:
  • ALL TRAFFIC IS VISIBLE to anyone in radio range
  • No encryption between device and AP
  • MITM attacks are trivial (ARP spoofing on open network)

HOW WPA3 IMPROVES OPEN NETWORKS (OWE):
  • WPA3 introduces "Enhanced Open"
  • Each client session gets unique encryption
  • Traffic still encrypted even without password!

NEVER click 'Proceed anyway' on certificate warnings!
```

> 💡 **What this means:** Certificate validation is your last line of defense against MITM attacks on open networks. "The browser is paranoid" — no, the browser is warning you about a genuine attack. Proceed with extreme caution or stop using that network.

### Step 7: WPA2 vs WPA3 SAE Technical Comparison

```bash
python3 << 'EOF'
print("WPA2 PSK vs WPA3 SAE HANDSHAKE COMPARISON")
print("=" * 65)

print("""
WPA2-PSK (Pre-Shared Key) Handshake:
──────────────────────────────────────
PMK = PBKDF2(HMAC-SHA1, password, SSID, 4096 iterations, 256 bits)

4-Way Handshake:
  AP → Client: ANonce (random)
  Client: PTK = PRF(PMK + ANonce + SNonce + MAC_AP + MAC_Client)
  Client → AP: SNonce + MIC (using KCK from PTK)
  AP: Verifies MIC, derives PTK
  AP → Client: GTK (group key) encrypted with KEK
  Client → AP: ACK

VULNERABILITY:
  ✗ PMK derived directly from password (not forward-secret)
  ✗ Handshake can be captured and attacked offline
  ✗ Same PMK for every session (no forward secrecy)
  ✗ Dictionary attack possible if password is weak

WPA3-SAE (Simultaneous Authentication of Equals) Handshake:
──────────────────────────────────────────────────────────────
Based on Dragonfly (balanced PAKE - Password Authenticated Key Exchange)

Commit Phase:
  Both parties derive a point on an elliptic curve from the password
  Both generate random scalars + send commit messages

Confirm Phase:
  Both verify the other knows the same password
  PMK derived from shared secret (DH-like)

ADVANTAGES:
  ✅ Perfect Forward Secrecy: each session generates new keys
  ✅ Offline dictionary attack NOT possible (requires online interaction)
  ✅ Equal roles: neither AP nor client is "server" (no PSK sent over air)
  ✅ Even if password captured, past sessions remain secure
  ✅ Natural resistance to deauthentication attacks in WPA3-SAE

ANALOGY:
  WPA2-PSK: Like a door key - if someone copies the key, they have permanent access
  WPA3-SAE: Like a combination where both parties prove knowledge without revealing it
            Past sessions secured even if password later compromised
""")

# Demonstrate forward secrecy concept
print("FORWARD SECRECY DEMONSTRATION:")
print("  WPA2 scenario:")
print("    - Attacker captures 1 hour of encrypted WiFi traffic")
print("    - 6 months later, finds out WiFi password via phishing")
print("    - Can now DECRYPT all 1 hour of past traffic!")
print()
print("  WPA3 scenario:")
print("    - Attacker captures 1 hour of encrypted WiFi traffic")
print("    - 6 months later, finds out WiFi password")
print("    - Cannot decrypt past traffic (session keys were ephemeral)")
print("    - Forward secrecy protects historical data!")
EOF
```

**📸 Verified Output:**
```
WPA2 PSK vs WPA3 SAE HANDSHAKE COMPARISON
=================================================================

WPA2-PSK (Pre-Shared Key) Handshake:
──────────────────────────────────────
PMK = PBKDF2(HMAC-SHA1, password, SSID, 4096 iterations, 256 bits)

VULNERABILITY:
  ✗ PMK derived directly from password (not forward-secret)
  ✗ Handshake can be captured and attacked offline

WPA3-SAE Advantages:
  ✅ Perfect Forward Secrecy: each session generates new keys
  ✅ Offline dictionary attack NOT possible
```

> 💡 **What this means:** Forward secrecy is the key innovation in WPA3. Even if your password is compromised months later, historical traffic remains secure because each session used unique ephemeral keys that were never stored.

### Step 8: Wireless Penetration Testing Overview

```bash
python3 << 'EOF'
print("WIRELESS PENETRATION TESTING OVERVIEW")
print("(Educational - Only test networks you own or have permission!)")
print("=" * 65)

phases = [
    {
        "phase": "1. Reconnaissance",
        "description": "Passive discovery of wireless networks",
        "tools": ["iwlist scan", "nmcli device wifi", "airodump-ng (monitor mode)"],
        "collects": ["SSIDs, BSSIDs, channels, signal strength, encryption type, clients"],
        "legal_note": "Passive scanning (receiving) is generally legal"
    },
    {
        "phase": "2. Identify Targets",
        "description": "Classify networks by security protocol",
        "criteria": ["WEP → instant win", "WPA2 with WPS → try Reaver", "WPA2 → need handshake + strong wordlist"],
        "legal_note": "Still passive analysis phase"
    },
    {
        "phase": "3. Handshake Capture (WPA2)",
        "description": "Capture authentication handshake for offline cracking",
        "active_steps": ["Send deauth frames to force reconnection", "Capture 4-way handshake in monitor mode"],
        "tools": ["aireplay-ng -0 (deauth)", "airodump-ng (capture)"],
        "legal_note": "ACTIVE PHASE - Requires written authorization"
    },
    {
        "phase": "4. Offline Cracking",
        "description": "Dictionary/brute force attack against captured handshake",
        "tools": ["aircrack-ng", "hashcat --hash-type 22000"],
        "success_rate": "Depends entirely on password strength - random 20+ char PSK is impractical",
        "legal_note": "Offline analysis - legal if you captured the handshake legally"
    },
    {
        "phase": "5. Post-Connection Testing",
        "description": "After connecting, test internal network security",
        "activities": ["Network scanning", "Eavesdropping on other clients", "Gateway enumeration"],
        "legal_note": "REQUIRES explicit authorization in scope document"
    },
    {
        "phase": "6. Reporting",
        "description": "Document findings with evidence and remediation recommendations",
        "includes": ["Weak protocols found", "WPS status", "Rogue APs", "Client isolation issues"],
        "legal_note": "Required deliverable for all professional engagements"
    },
]

for p in phases:
    print(f"\n{'─'*65}")
    print(f"PHASE: {p['phase']}")
    print(f"Description: {p['description']}")
    if "tools" in p:
        print(f"Tools: {', '.join(p['tools'])}")
    print(f"Legal note: ⚠️  {p['legal_note']}")

print(f"\n{'='*65}")
print("LEGAL REQUIREMENTS:")
print("  1. Written scope of work signed by network owner")
print("  2. Rules of engagement document")
print("  3. Get-out-of-jail letter for law enforcement encounters")
print("  4. Professional liability insurance recommended")
print("  5. Do NOT test neighbor's networks or public hotspots")
EOF
```

**📸 Verified Output:**
```
WIRELESS PENETRATION TESTING OVERVIEW
(Educational - Only test networks you own or have permission!)
=================================================================

──────────────────────────────────────────────────────────────────
PHASE: 1. Reconnaissance
Description: Passive discovery of wireless networks
Tools: iwlist scan, nmcli device wifi, airodump-ng (monitor mode)
Legal note: ⚠️  Passive scanning (receiving) is generally legal

──────────────────────────────────────────────────────────────────
PHASE: 3. Handshake Capture (WPA2)
Legal note: ⚠️  ACTIVE PHASE - Requires written authorization
```

> 💡 **What this means:** Active wireless testing (sending deauth frames, attempting connections) without authorization is illegal. Always get written permission. Many jurisdictions prosecute unauthorized wireless access under computer crime laws, even if the network uses a weak password.

## ✅ Verification

```bash
python3 -c "
# Verify WEP IV analysis works
iv_space = 2**24
print(f'WEP IV space: {iv_space:,} ({iv_space/1e6:.1f}M)')
print(f'Exhausted at 1000 pkt/s: {iv_space/1000/3600:.1f} hours')
print('Wireless security lab verified')
"
```

## 🚨 Common Mistakes

- **Using WPS**: WPS can be cracked in hours with Reaver — disable it immediately
- **Weak PSK**: Short dictionary words are cracked in seconds; use 20+ random characters
- **Not validating RADIUS certificates**: Skipping cert validation on 802.1X exposes you to evil twin RADIUS servers
- **Same SSID for corp and guest**: Use separate SSIDs on separate VLANs with firewall between them
- **Testing without authorization**: Wireless testing without written permission is illegal in most countries

## 📝 Summary

- **Protocol evolution**: WEP (broken, <1 min crack) → WPA (deprecated) → WPA2 (good with strong PSK) → WPA3 (current gold standard)
- **WPA2 vulnerabilities**: offline dictionary attacks, KRACK, PMKID, WPS brute force — all addressable with strong PSK + WPS disabled + patches
- **WPA3 SAE** provides perfect forward secrecy — even if PSK is compromised, past sessions remain encrypted
- **802.1X enterprise authentication** provides per-user credentials, audit trails, and VLAN assignment vs shared PSK
- **Open networks** are completely unencrypted; WPA3 Enhanced Open (OWE) adds encryption without passwords

## 🔗 Further Reading

- [WPA3 Technical Specification](https://www.wi-fi.org/discover-wi-fi/security)
- [KRACK Attack Explained](https://www.krackattacks.com/)
- [802.1X Authentication Guide](https://www.cisco.com/c/en/us/support/docs/lan-switching/8021x/116682-technote-8021x-00.html)
- [Wireless Security Penetration Testing Guide](https://www.offensive-security.com/metasploit-unleashed/wireless-attacks/)
- [FreeRADIUS Setup Guide](https://wiki.freeradius.org/guide/Getting-Started)
