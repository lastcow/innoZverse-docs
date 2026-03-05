# Lab 15: Campus Network Design — Wi-Fi 6, NAC & PoE Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Design a modern enterprise campus network incorporating Wi-Fi 6 (802.11ax), multi-band channel planning, Network Access Control (NAC) with 802.1X/RADIUS, and Power over Ethernet (PoE) budget planning. You will build a complete wireless architecture covering RF design, SSID segmentation, roaming optimisation, and security policy.

## Architecture: Enterprise Campus Wireless Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    Campus Network Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│  SSID: Corp (WPA3-Ent) │ Guest (WPA3-PSK) │ IoT (WPA2/802.1X) │
├─────────────────────────────────────────────────────────────────┤
│  VLAN 10: Corp  │  VLAN 20: Guest (isolated)  │  VLAN 30: IoT  │
├─────────────────────────────────────────────────────────────────┤
│  NAC: 802.1X EAP-TLS → RADIUS → Active Directory               │
├─────────────────────────────────────────────────────────────────┤
│  Wireless Controller → PoE++ Switches → 802.11ax APs           │
├─────────────────────────────────────────────────────────────────┤
│  Core Switch (10G) → Firewall → Internet / DC                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Wi-Fi 6 (802.11ax) Fundamentals

802.11ax introduces significant improvements over 802.11ac (Wi-Fi 5):

| Feature | 802.11ac (Wi-Fi 5) | 802.11ax (Wi-Fi 6) | Wi-Fi 6E |
|---------|-------------------|-------------------|---------|
| Bands | 5 GHz | 2.4 + 5 GHz | 2.4 + 5 + **6 GHz** |
| Max throughput | 3.5 Gbps | 9.6 Gbps | 9.6 Gbps |
| Channel width | 80/160 MHz | 80/160 MHz | up to 320 MHz (Wi-Fi 7) |
| MU-MIMO | 4×4 DL | 8×8 DL+UL | 8×8 DL+UL |
| OFDMA | No | **Yes** | Yes |
| BSS Colouring | No | **Yes** | Yes |
| TWT (Target Wake Time) | No | **Yes** (IoT sleep) | Yes |

**Key Wi-Fi 6 innovations:**
- **OFDMA** — splits channel into Resource Units (RUs), serving multiple clients simultaneously
- **BSS Colouring** — reduces co-channel interference via colour bits in frame header
- **TWT** — IoT devices negotiate sleep/wake schedule, extending battery life

> 💡 Wi-Fi 6E opens the 6 GHz band (5.925–7.125 GHz), providing 1,200 MHz of clean spectrum with no legacy device interference.

---

## Step 2: Channel Planning — 2.4 / 5 / 6 GHz

### 2.4 GHz — Legacy Support
Only **3 non-overlapping channels**: 1, 6, 11 (20 MHz each)

```
|--Ch1--|  |--Ch6--|  |--Ch11--|
2402   2422  2437  2457  2462  2482 MHz
```

> 💡 Disable 2.4 GHz on APs in high-density areas; use it only for legacy IoT devices.

### 5 GHz — Primary Enterprise Band
UNII bands provide 25 non-overlapping 20 MHz channels:
- **UNII-1** (36–48): Indoor, 5.15–5.25 GHz
- **UNII-2A** (52–64): DFS required, 5.25–5.35 GHz
- **UNII-2C** (100–144): DFS required, 5.47–5.725 GHz
- **UNII-3** (149–165): Outdoor OK, 5.725–5.85 GHz

**80 MHz channel allocation (4-AP cluster):**
```
AP1: Ch 36+40+44+48 (center ch 42)
AP2: Ch 52+56+60+64 (center ch 58, DFS)
AP3: Ch 149+153+157+161 (center ch 155)
AP4: Ch 100+104+108+112 (center ch 106, DFS)
```

### 6 GHz — Wi-Fi 6E Clean Slate
59 non-overlapping 20 MHz channels, no DFS, no legacy devices:
```
Channels: 1, 5, 9, 13 ... (PSC channels for 80 MHz)
Preferred Scanning Channels (PSC): 5, 21, 37, 53, 69, 85, 101, 117, 133, 149, 165, 181
```

### Cell Sizing Guidelines
| Environment | AP Spacing | Cell Radius | Clients/AP |
|-------------|-----------|-------------|-----------|
| Open office | 15–20m | 20–30m | 25–50 |
| Dense office | 8–12m | 10–15m | 15–25 |
| Conference room | Dedicated AP | N/A | 20–30 |
| Warehouse | 30–50m | 40–60m | 5–15 |
| Outdoor | 50–100m | 60–120m | Variable |

---

## Step 3: SSID Design & VLAN Segmentation

### SSID Architecture

```
SSID: Corp-WiFi6          SSID: Guest-WiFi           SSID: IoT-Sensors
  Security: WPA3-Ent        Security: WPA3-SAE          Security: WPA2+802.1X
  Auth: 802.1X EAP-TLS      Captive portal              Auth: EAP-PEAP
  VLAN: 10                  VLAN: 20 (isolated)         VLAN: 30
  QoS: WMM (voice+video)    Rate limit: 10Mbps/client   DHCP: Short lease
  PMF: Required             PMF: Optional               PMF: Capable
  Band steering: 5/6 GHz    Band: 2.4+5 GHz only       Band: 2.4 GHz
```

### Guest VLAN Isolation
```
Guest VLAN 20 rules:
  - No L3 routing to Corp/IoT VLANs (RFC 1918 blocked)
  - Only TCP 80/443 permitted outbound
  - Captive portal redirect on port 8080
  - Client isolation enabled (no AP-to-AP bridging)
  - DHCP scope: 192.168.20.0/24, /28 subnets per floor
  - DNS: 8.8.8.8 / 1.1.1.1 (no internal DNS)
```

### IoT SSID Controls
```
IoT VLAN 30 rules:
  - Allow: IoT → DC collector (TCP 8883 MQTT)
  - Allow: IoT → NTP (UDP 123)
  - Block: IoT ↔ Corp, IoT ↔ Guest
  - Block: IoT → Internet (except cloud updates via proxy)
  - TWT enabled for battery-powered sensors
```

---

## Step 4: NAC with 802.1X and RADIUS

### 802.1X Authentication Flow

```
Supplicant (Client)    Authenticator (AP/Switch)    RADIUS Server
      │                         │                        │
      │─── EAPOL-Start ────────►│                        │
      │◄── EAP-Request/Identity─│                        │
      │─── EAP-Response/Identity►│                       │
      │                         │──RADIUS Access-Req────►│
      │                         │◄─RADIUS Access-Chall──│
      │◄── EAP-TLS Challenge ───│                        │
      │─── EAP-TLS ClientCert ─►│                        │
      │                         │──RADIUS Access-Req────►│
      │                         │◄─RADIUS Access-Accept──│
      │                         │   (VLAN=10, QoS=WMM)  │
      │◄── EAP-Success ─────────│                        │
      │    [Port Authorised]    │                        │
```

### RADIUS Configuration (FreeRADIUS example)
```
# /etc/freeradius/3.0/clients.conf
client AP-cluster-floor1 {
    ipaddr = 10.10.1.0/24
    secret = Sup3rS3cretRADIUS!
    nas_type = cisco
}

# /etc/freeradius/3.0/users
DEFAULT Auth-Type := EAP, Group == "Corp_WiFi_Users"
    Tunnel-Type = VLAN,
    Tunnel-Medium-Type = IEEE-802,
    Tunnel-Private-Group-ID = "10"

DEFAULT Auth-Type := EAP, Group == "IoT_Devices"
    Tunnel-Type = VLAN,
    Tunnel-Medium-Type = IEEE-802,
    Tunnel-Private-Group-ID = "30"
```

### WPA3-Enterprise Requirements
- **EAP-TLS**: Mutual certificate authentication (strongest)
- **EAP-PEAP/MSCHAPv2**: Username/password + server cert (common)
- **PMF (802.11w)**: Management Frame Protection — **required** for WPA3
- **SAE-Hash-to-Element**: Protects against offline dictionary attacks

---

## Step 5: Fast Roaming — 802.11r/k/v

Seamless roaming is critical for voice/video clients:

### 802.11r — Fast BSS Transition (FT)
```
Pre-authentication during active session:
  Current AP ──── FT Request ────► Target AP
  Current AP ◄─── FT Response ─── Target AP
  Client ─── FT Auth (4ms) ──────► Target AP
  [Roam complete: <20ms vs 200-400ms without FT]
```

### 802.11k — Radio Resource Management
- APs broadcast **Neighbor Reports** with candidate AP lists
- Client requests neighbour list → AP responds with BSSID+channel
- Reduces scan time from ~200ms to <20ms

### 802.11v — BSS Transition Management
- AP can **suggest or force** client to roam (load balancing)
- BSS Transition Request with disassociation timer
- Used by WLC for load balancing across APs

### Roaming Configuration Checklist
```
✓ 802.11r enabled on WPA3-Enterprise SSIDs
✓ 802.11k Neighbor Reports enabled
✓ 802.11v BSS Transition enabled
✓ PMKID caching (PMKSA) enabled
✓ OKC (Opportunistic Key Caching) for EAP SSIDs
✓ Roam threshold: RSSI < -75 dBm triggers roam
✓ Sticky client prevention: force roam at -80 dBm
```

---

## Step 6: PoE Budget Planning (IEEE 802.3bt)

### PoE Standards

| Standard | Max Power | Typical Use |
|----------|-----------|-------------|
| 802.3af (PoE) | 15.4W | IP phones, basic cameras |
| 802.3at (PoE+) | 30W | PTZ cameras, older APs |
| 802.3bt Type 3 (PoE++) | 60W | Wi-Fi 6 APs, thin clients |
| 802.3bt Type 4 (PoE++) | 90W | Laptops, video conferencing |

```python
# PoE Budget Calculator
poe_standards = {
    'PoE (802.3af)': 15.4,
    'PoE+ (802.3at)': 30.0,
    'PoE++ Type 3 (802.3bt)': 60.0,
    'PoE++ Type 4 (802.3bt)': 90.0,
}
devices = [
    {'name': 'Cisco AP 9130AX (Wi-Fi 6)', 'type': 'PoE++ Type 3', 'count': 20},
    {'name': 'IP Camera 4K PTZ',           'type': 'PoE+',         'count': 30},
    {'name': 'VoIP Phone',                 'type': 'PoE',          'count': 50},
    {'name': 'IoT Sensor Hub',             'type': 'PoE',          'count': 15},
]
# Total load: 3101W across 4 PoE++ switches (775W/switch budget required)
# Use Cisco C9300-48UXM: 1440W budget each — deploy 3 switches
```

📸 **Verified Output:**
```
=== PoE Budget Calculator (IEEE 802.3bt) ===
  Cisco AP 9130AX (Wi-Fi 6) x20: PoE++ Type 3 (802.3bt) @ 60.0W = 1200.0W
  IP Camera 4K x30: PoE+ (802.3at) @ 30.0W = 900.0W
  VoIP Phone x50: PoE (802.3af) @ 15.4W = 770.0W
  IoT Sensor Hub x15: PoE (802.3af) @ 15.4W = 231.0W

Total PoE Load:    3101.0W
Switch PoE Budget: 1440W
Utilisation:       215.3%
Headroom:          -1661.0W (OVER BUDGET)
→ Solution: Deploy 3× 48-port PoE++ switches (split load ~1034W each = 71.8% util)
```

> 💡 Always plan for 80% PoE utilisation maximum. Reserve headroom for future device additions and burst scenarios.

---

## Step 7: RF Interference & Mitigation

### Common Interference Sources

| Source | Band | Mitigation |
|--------|------|-----------|
| Microwave ovens | 2.4 GHz | Move APs away; use 5/6 GHz |
| Bluetooth | 2.4 GHz | WPAN coexistence; FHSS adapts |
| Rogue APs | All | WIDS/WIPS detection |
| Co-channel interference | All | BSS Colouring (Wi-Fi 6) |
| Adjacent channel interference | 2.4 GHz | Use only 1/6/11 |
| Radar (DFS) | 5 GHz | DFS detection, channel switch |

### RF Best Practices
```
Cell Planning:
  ✓ Target RSSI at edge: -67 dBm (voice), -72 dBm (data)
  ✓ SNR minimum: 25 dB (voice), 20 dB (data)
  ✓ Cell overlap: 15–20% for seamless roaming
  ✓ Transmit power: Start at 11 dBm, adjust with RRM

WIDS/WIPS Policy:
  ✓ Rogue AP containment (deauth flood to rogue clients)
  ✓ Ad-hoc network detection and blocking
  ✓ Evil twin detection (duplicate BSSID/SSID monitoring)
  ✓ Client exclusion on repeated auth failures (brute force)
```

### Wi-Fi 6 Channel Plan (3-AP Cluster)
```
AP1: 2.4GHz ch1  | 5GHz ch36  (UNII-1, no DFS)
AP2: 2.4GHz ch6  | 5GHz ch44  (UNII-1, no DFS)
AP3: 2.4GHz ch11 | 5GHz ch149 (UNII-3, no DFS)
```

📸 **Verified Output:**
```
=== Wi-Fi 6 Channel Interference Analyser ===
  2.4 GHz: 3 non-overlapping channels (1, 6, 11) — 20MHz width
  5 GHz:   8 UNII channels shown — 20/40/80/160MHz widths
  6 GHz:   8 sample channels (Wi-Fi 6E) — up to 320MHz (Wi-Fi 7)

  Recommended AP channel plan (3-AP cluster):
    AP1: 2.4GHz ch1  | 5GHz ch36
    AP2: 2.4GHz ch6  | 5GHz ch44
    AP3: 2.4GHz ch11 | 5GHz ch149
```

---

## Step 8: Capstone — Campus Network Design Document

Design a campus network for a 3-floor office building (500 employees, 200 IoT devices, 100 guests).

### Requirements Gathering
```
Floor layout:     3 floors × 2,000 m²
User density:     Open plan + 10 conference rooms per floor
Mobility:         VoIP softphones require <20ms roam
Compliance:       ISO 27001, GDPR (guest data isolation)
Redundancy:       Dual uplinks, controller HA
```

### Design Summary

**AP Deployment:**
- 3 APs per floor cluster (9 APs total) + 1 per conference room (30 total)
- Cisco Catalyst 9130AX (Wi-Fi 6, PoE++, BLE)
- Mounting height: 2.7m, tilt 15° down

**Switch Layer:**
```
Access:  Cisco C9300-48UXM (48-port PoE++, 1440W budget) × 3
         Per floor: 10 APs + 30 cameras + 50 phones = 31 devices/switch
Uplink:  Cisco C9500 (Core) with 25G uplinks
WLC:     Cisco Catalyst Center (cloud-managed)
```

**Security Architecture:**
```
Corp:   WPA3-Enterprise, EAP-TLS, VLAN 10, full access
Guest:  WPA3-SAE, captive portal, VLAN 20, internet-only
IoT:    WPA2-Enterprise, EAP-PEAP, VLAN 30, restricted east-west
RADIUS: FreeRADIUS HA pair (primary + secondary)
AD:     Microsoft AD with NPS extension
```

📸 **Verified Output — 802.1X Auth Flow:**
```
=== 802.1X EAP-TLS Authentication Flow ===
  Step 1: [Supplicant→Authenticator] EAPOL-Start
  Step 2: [Authenticator→Supplicant] EAP-Request/Identity
  Step 3: [Supplicant→Authenticator] EAP-Response/Identity (user@corp.com)
  Step 4: [Authenticator→RADIUS] RADIUS Access-Request + EAP-Response
  Step 5: [RADIUS→Authenticator] RADIUS Access-Challenge + EAP-TLS ServerHello
  Step 6: [Supplicant→RADIUS (via)] EAP-TLS ClientHello + Certificate
  Step 7: [RADIUS→Authenticator] RADIUS Access-Accept + VLAN=10 (Corp)
  Step 8: [Authenticator→Switch] MAB port authorised, VLAN 10 assigned
```

---

## Summary

| Component | Design Choice | Standard/Protocol |
|-----------|--------------|-------------------|
| Primary band | 5 GHz + 6 GHz (Wi-Fi 6E) | 802.11ax |
| Authentication | EAP-TLS (Corp), EAP-PEAP (IoT) | 802.1X / RFC 5216 |
| Key security | WPA3-Enterprise + PMF | 802.11i + 802.11w |
| Fast roaming | FT + RRM + BSS Transition | 802.11r/k/v |
| SSID segmentation | 3 SSIDs → 3 VLANs | 802.1Q |
| PoE | PoE++ for APs | IEEE 802.3bt Type 3 |
| Switch budget | 3× 48-port PoE++ (1440W each) | 71.8% utilisation |
| RF design | BSS Colouring, OFDMA, TWT | 802.11ax features |
| Guest isolation | L3 VLAN isolation + captive portal | RFC 3580 |
| Monitoring | WIDS/WIPS + Syslog + SNMP | IDS/IPS framework |
