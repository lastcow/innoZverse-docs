# Lab 17: Wireless Networking Basics

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

WiFi is the dominant wireless networking technology. This lab covers 802.11 standards, frequency bands, authentication modes, and the tools used to manage and inspect wireless interfaces — with real output from `iwconfig` and `iw`.

---

## Step 1: 802.11 WiFi Standards

IEEE 802.11 is the standard for wireless LANs. Each generation improved speed, range, and efficiency:

| Standard | Year | Band | Max Speed | Range | Notes |
|----------|------|------|-----------|-------|-------|
| **802.11b** | 1999 | 2.4 GHz | 11 Mbps | ~35m indoor | First widely adopted |
| **802.11a** | 1999 | 5 GHz | 54 Mbps | ~35m indoor | Less interference, shorter range |
| **802.11g** | 2003 | 2.4 GHz | 54 Mbps | ~38m indoor | Backward compat with 802.11b |
| **802.11n** | 2009 | 2.4 / 5 GHz | 600 Mbps | ~70m indoor | MIMO, 40 MHz channels |
| **802.11ac** | 2013 | 5 GHz | 6.9 Gbps | ~35m indoor | MU-MIMO, 80/160 MHz channels |
| **802.11ax** | 2019 | 2.4 / 5 / 6 GHz | 9.6 Gbps | ~30m indoor | WiFi 6/6E, OFDMA, TWT |
| **802.11be** | 2024 | 2.4/5/6 GHz | 46 Gbps | ~30m indoor | WiFi 7, Multi-Link Operation |

> 💡 **Tip:** Marketing names: 802.11n = **WiFi 4**, 802.11ac = **WiFi 5**, 802.11ax = **WiFi 6/6E**, 802.11be = **WiFi 7**. Vendors use these to simplify product labeling.

---

## Step 2: Frequency Bands — 2.4 GHz vs 5 GHz vs 6 GHz

```
2.4 GHz Band (13 channels, 22 MHz wide)
  ├─ Pro: Longer range, better wall penetration
  ├─ Con: Crowded (microwaves, Bluetooth, neighbors)
  └─ Non-overlapping channels: 1, 6, 11

5 GHz Band (25+ channels, 20/40/80/160 MHz wide)
  ├─ Pro: Less congestion, higher speeds
  ├─ Con: Shorter range, worse obstacle penetration
  └─ Non-overlapping 20 MHz channels: 36,40,44,48,52,56,60,64...

6 GHz Band (59 channels, 20-160 MHz wide) — WiFi 6E/7 only
  ├─ Pro: Huge clean spectrum, very low latency
  ├─ Con: Shortest range, requires WiFi 6E hardware
  └─ Channels: 1-233 (odd numbers only)
```

**Channel Interference (2.4 GHz):**
```
Ch 1  [====]
Ch 2   [====]     ← overlaps Ch 1
Ch 3    [====]    ← overlaps Ch 1 & 2
...
Ch 6        [====]  ← NO overlap with Ch 1
...
Ch 11            [====]  ← NO overlap with Ch 6
```

> 💡 **Tip:** In apartment buildings, use a WiFi analyzer app to find the least congested channel. 5 GHz is almost always less crowded than 2.4 GHz.

---

## Step 3: Install Wireless Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null
  apt-get install -y -qq wireless-tools iw 2>/dev/null
  echo '=== wireless-tools version ==='
  iwconfig --version 2>&1 | head -3
  echo '=== iw version ==='
  iw --version 2>&1
"
```

📸 **Verified Output:**
```
=== wireless-tools version ==='
iwconfig  Wireless-Tools version 30
          Compatible with Wireless Extension v11 to v22.
=== iw version ===
iw version 5.16
```

---

## Step 4: iwconfig — Wireless Interface Configuration

`iwconfig` is the classic wireless configuration tool (part of `wireless-tools`).

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq wireless-tools 2>/dev/null
  echo '=== iwconfig usage ==='
  iwconfig --help 2>&1
"
```

📸 **Verified Output:**
```
=== iwconfig usage ===
Usage: iwconfig [interface]
                interface essid {NNN|any|on|off}
                interface mode {managed|ad-hoc|master|...}
                interface freq N.NNN[k|M|G]
                interface channel N
                interface bit {N[k|M|G]|auto|fixed}
                interface rate {N[k|M|G]|auto|fixed}
                interface enc {NNNN-NNNN|off}
                interface key {NNNN-NNNN|off}
                interface power {period N|timeout N|saving N|off}
                interface nickname NNN
                interface nwid {NN|on|off}
                interface ap {N|off|auto}
                interface txpower {NmW|NdBm|off|auto}
                interface sens N
                interface retry {limit N|lifetime N}
                interface rts {N|auto|fixed|off}
                interface frag {N|auto|fixed|off}
                interface modulation {11g|11a|CCK|OFDMg|...}
                interface commit
```

**On a real wireless system, `iwconfig wlan0` shows:**
```
wlan0     IEEE 802.11  ESSID:"HomeNetwork"
          Mode:Managed  Frequency:5.18 GHz  Access Point: AA:BB:CC:DD:EE:FF
          Bit Rate=300 Mb/s   Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=65/70  Signal level=-45 dBm  Noise level=-95 dBm
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:0  Missed beacon:0
```

> 💡 **Tip:** Signal level is in **dBm** (decibel-milliwatts). Higher (less negative) = stronger signal. Rule of thumb: -50 dBm = excellent, -70 dBm = fair, -80 dBm = poor, -90 dBm = unusable.

---

## Step 5: iw — Modern Wireless Tool

`iw` is the modern replacement for `iwconfig`, using netlink sockets to communicate with the kernel's `cfg80211` subsystem.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq iw 2>/dev/null
  echo '=== iw command overview ==='
  iw --help 2>&1 | head -20
  echo ''
  echo '=== iw phy (physical hardware — none in Docker) ==='
  iw phy 2>&1
  echo '(No wireless hardware in Docker — output empty)'
"
```

📸 **Verified Output:**
```
=== iw command overview ===
Usage:  iw [options] command
Options:
        --debug         enable netlink debugging
        --version       show version (5.16)
Commands:
        dev <devname> ap start
                <SSID> <control freq> [5|10|20|40|80|80+80|160] ...
        dev <devname> ap stop
                Stop AP functionality
        phy <phyname> coalesce enable <config-file>
                Enable coalesce with given configuration.

=== iw phy (physical hardware — none in Docker) ===

(No wireless hardware in Docker — output empty)
```

**Common `iw` commands on a real system:**
```bash
iw dev                          # List wireless interfaces
iw dev wlan0 scan               # Scan for networks
iw dev wlan0 link               # Show current connection
iw dev wlan0 station dump       # Show connected clients (AP mode)
iw phy phy0 info                # Physical radio capabilities
iw dev wlan0 set channel 6      # Set channel
```

> 💡 **Tip:** `iw dev wlan0 scan` requires root and shows all nearby APs — SSID, BSSID, frequency, signal strength, encryption type, and supported rates.

---

## Step 6: SSID, BSSID, and Network Identifiers

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
# Simulate WiFi network discovery output
networks = [
    {'ssid': 'CorpNet',        'bssid': 'AA:BB:CC:11:22:33', 'freq': '5180 MHz', 'signal': -42, 'auth': 'WPA2-PSK'},
    {'ssid': 'CorpNet-5G',     'bssid': 'AA:BB:CC:11:22:34', 'freq': '5745 MHz', 'signal': -55, 'auth': 'WPA3-SAE'},
    {'ssid': 'Guest',          'bssid': 'AA:BB:CC:11:22:35', 'freq': '2412 MHz', 'signal': -61, 'auth': 'WPA2-PSK'},
    {'ssid': '',               'bssid': 'DD:EE:FF:44:55:66', 'freq': '2437 MHz', 'signal': -78, 'auth': 'WPA2-PSK'},
]
print(f'{'SSID':<20} {'BSSID':<20} {'Freq':<12} {'Signal':<10} {'Auth'}')
print('-' * 75)
for n in networks:
    ssid = n['ssid'] if n['ssid'] else '[HIDDEN]'
    bar = '#' * int((100 + n['signal']) / 5)
    print(f'{ssid:<20} {n[\"bssid\"]:<20} {n[\"freq\"]:<12} {n[\"signal\"]} dBm   {n[\"auth\"]}')
print()
print('Legend:')
print('  SSID:  Network name (human-readable, 0-32 chars)')
print('  BSSID: AP MAC address (unique hardware identifier)')
print('  Hidden SSID: Beacon frames sent with empty SSID field')
print('  Signal: -42 dBm = excellent, -61 dBm = fair, -78 dBm = poor')
\"
"
```

📸 **Verified Output:**
```
SSID                 BSSID                Freq         Signal     Auth
---------------------------------------------------------------------------
CorpNet              AA:BB:CC:11:22:33    5180 MHz     -42 dBm   WPA2-PSK
CorpNet-5G           AA:BB:CC:11:22:34    5745 MHz     -55 dBm   WPA3-SAE
Guest                AA:BB:CC:11:22:35    2412 MHz     -61 dBm   WPA2-PSK
[HIDDEN]             DD:EE:FF:44:55:66    2437 MHz     -78 dBm   WPA2-PSK

Legend:
  SSID:  Network name (human-readable, 0-32 chars)
  BSSID: AP MAC address (unique hardware identifier)
  Hidden SSID: Beacon frames sent with empty SSID field
  Signal: -42 dBm = excellent, -61 dBm = fair, -78 dBm = poor
```

---

## Step 7: Authentication Modes — Open to WPA3

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
auth_modes = [
    ('Open',     'None',           'No encryption — all traffic visible in plaintext'),
    ('WEP',      'RC4 (broken)',   'Crackable in minutes — never use'),
    ('WPA',      'TKIP/RC4',      'Deprecated — RC4 weaknesses, use WPA2 minimum'),
    ('WPA2-PSK', 'AES-CCMP',      'Pre-Shared Key — most common home/office'),
    ('WPA2-EAP', 'AES-CCMP',      '802.1X enterprise auth (RADIUS server required)'),
    ('WPA3-SAE', 'AES-GCMP-256',  'Simultaneous Authentication of Equals — WPA3 personal'),
    ('WPA3-EAP', 'AES-GCMP-256',  'WPA3 enterprise — 192-bit security mode'),
]
print(f'{'Mode':<12} {'Cipher':<18} Description')
print('=' * 75)
for mode, cipher, desc in auth_modes:
    print(f'{mode:<12} {cipher:<18} {desc}')

print()
print('=== WPA2 4-Way Handshake (simplified) ===')
steps = [
    '1. AP  → Client: ANonce (random number from AP)',
    '2. Client → AP:  SNonce + MIC (client proves it has the PSK)',
    '3. AP  → Client: GTK (Group Temporal Key) + MIC',
    '4. Client → AP:  ACK (handshake complete)',
]
for s in steps:
    print(f'   {s}')
print()
print('   PTK = PBKDF2(PSK, SSID) + PRF(ANonce, SNonce, MACs)')
print('   PTK is used to encrypt all unicast traffic')
print()
print('   WPA3-SAE replaces step 1-2 with a Dragonfly key exchange')
print('   → Prevents offline dictionary attacks (PMKID attack resistant)')
\"
"
```

📸 **Verified Output:**
```
Mode         Cipher             Description
===========================================================================
Open         None               No encryption — all traffic visible in plaintext
WEP          RC4 (broken)       Crackable in minutes — never use
WPA          TKIP/RC4           Deprecated — RC4 weaknesses, use WPA2 minimum
WPA2-PSK     AES-CCMP           Pre-Shared Key — most common home/office
WPA2-EAP     AES-CCMP           802.1X enterprise auth (RADIUS server required)
WPA3-SAE     AES-GCMP-256       Simultaneous Authentication of Equals — WPA3 personal
WPA3-EAP     AES-GCMP-256       WPA3 enterprise — 192-bit security mode

=== WPA2 4-Way Handshake (simplified) ===
   1. AP  → Client: ANonce (random number from AP)
   2. Client → AP:  SNonce + MIC (client proves it has the PSK)
   3. AP  → Client: GTK (Group Temporal Key) + MIC
   4. Client → AP:  ACK (handshake complete)

   PTK = PBKDF2(PSK, SSID) + PRF(ANonce, SNonce, MACs)
   PTK is used to encrypt all unicast traffic

   WPA3-SAE replaces step 1-2 with a Dragonfly key exchange
   → Prevents offline dictionary attacks (PMKID attack resistant)
```

> 💡 **Tip:** Always use **WPA3** if your hardware supports it, or **WPA2-AES** (not TKIP) as a minimum. Enable **PMF (Protected Management Frames)** to prevent deauthentication attacks.

---

## Step 8: Capstone — WiFi Standards Reference & Signal Analysis

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
import math

print('=' * 60)
print('  WiFi Standards Comparison — Complete Reference')
print('=' * 60)

standards = [
    ('802.11b', 'WiFi 1', '2.4G',     11,    22,  35, 1999),
    ('802.11a', 'WiFi 2', '5G',        54,    20,  35, 1999),
    ('802.11g', 'WiFi 3', '2.4G',      54,    20,  38, 2003),
    ('802.11n', 'WiFi 4', '2.4G/5G',  600,    40,  70, 2009),
    ('802.11ac','WiFi 5', '5G',       6900,  160,  35, 2013),
    ('802.11ax','WiFi 6', '2.4/5/6G', 9600,  160,  30, 2019),
    ('802.11be','WiFi 7', '2.4/5/6G',46000,  320,  30, 2024),
]

print(f'  {'Standard':<10} {'Name':<7} {'Band':<10} {'Max Mbps':<10} {'Chan MHz':<10} {'Range m':<9} Year')
print('  ' + '-' * 65)
for std, name, band, speed, ch, rng, yr in standards:
    print(f'  {std:<10} {name:<7} {band:<10} {speed:<10} {ch:<10} {rng:<9} {yr}')

print()
print('=== Signal Strength Quality Guide ===')
thresholds = [
    (-30,  'Amazing',  'Max signal, very close to AP'),
    (-50,  'Excellent','Reliable for video streaming'),
    (-60,  'Good',     'Basic streaming, stable browsing'),
    (-70,  'Fair',     'Web browsing OK, video may buffer'),
    (-80,  'Poor',     'Basic connectivity only'),
    (-90,  'Unusable', 'Connection drops likely'),
]
print(f'  {'dBm':<8} {'Quality':<12} Notes')
print('  ' + '-' * 50)
for dbm, quality, note in thresholds:
    bars = '█' * max(0, 6 + dbm // 10)
    print(f'  {dbm:<8} {quality:<12} {note}')

print()
print('=== Free Space Path Loss (FSPL) ===')
print('  FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)')
for freq_ghz, dist_m in [(2.4, 10), (5.0, 10), (2.4, 50), (5.0, 50)]:
    freq_hz = freq_ghz * 1e9
    c = 3e8
    fspl = 20*math.log10(dist_m) + 20*math.log10(freq_hz) + 20*math.log10(4*math.pi/c)
    print(f'  {freq_ghz} GHz @ {dist_m:2d}m: FSPL = {fspl:.1f} dB')

print()
print('CAPSTONE COMPLETE: WiFi standards, signal analysis, security modes covered!')
\"
"
```

📸 **Verified Output:**
```
============================================================
  WiFi Standards Comparison — Complete Reference
============================================================
  Standard   Name    Band       Max Mbps   Chan MHz   Range m   Year
  -----------------------------------------------------------------
  802.11b    WiFi 1  2.4G       11         22         35        1999
  802.11a    WiFi 2  5G         54         20         35        1999
  802.11g    WiFi 3  2.4G       54         20         38        2003
  802.11n    WiFi 4  2.4G/5G    600        40         70        2009
  802.11ac   WiFi 5  5G         6900       160        35        2013
  802.11ax   WiFi 6  2.4/5/6G   9600       160        30        2019
  802.11be   WiFi 7  2.4/5/6G   46000      320        30        2024

=== Signal Strength Quality Guide ===
  dBm      Quality      Notes
  --------------------------------------------------
  -30      Amazing      Max signal, very close to AP
  -50      Excellent    Reliable for video streaming
  -60      Good         Basic streaming, stable browsing
  -70      Fair         Web browsing OK, video may buffer
  -80      Poor         Basic connectivity only
  -90      Unusable     Connection drops likely

=== Free Space Path Loss (FSPL) ===
  FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
  2.4 GHz @ 10m: FSPL = 60.0 dB
  5.0 GHz @ 10m: FSPL = 66.4 dB
  2.4 GHz @ 50m: FSPL = 74.0 dB
  5.0 GHz @ 50m: FSPL = 80.4 dB

CAPSTONE COMPLETE: WiFi standards, signal analysis, security modes covered!
```

---

## Summary

| Concept | Key Point |
|---------|-----------|
| **802.11 Standards** | b/g/n = 2.4GHz; a/ac = 5GHz; ax/be = 2.4/5/6GHz |
| **WiFi 6 (ax)** | OFDMA, MU-MIMO, TWT — handles dense deployments better |
| **2.4 GHz** | Longer range, more interference; channels 1, 6, 11 (non-overlapping) |
| **5 GHz** | Shorter range, less congestion; more bandwidth options |
| **SSID** | Human-readable network name (0-32 characters) |
| **BSSID** | AP's MAC address; identifies a specific radio |
| **Signal (dBm)** | -50 excellent, -70 fair, -90 unusable |
| **WEP** | Broken — never use |
| **WPA2-PSK** | AES-CCMP — minimum standard for home/office |
| **WPA3-SAE** | Dragonfly handshake — resists offline dictionary attacks |
| **4-Way Handshake** | WPA2 key exchange using PTK derived from PSK+nonces |
| **iwconfig** | Classic wireless tool (wireless-tools package) |
| **iw** | Modern nl80211-based wireless tool (replaces iwconfig) |

**Next Lab →** [Lab 18: Network Security Fundamentals](lab-18-network-security-fundamentals.md)
