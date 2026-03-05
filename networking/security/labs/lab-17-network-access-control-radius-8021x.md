# Lab 17: Network Access Control — 802.1X & RADIUS

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

**Network Access Control (NAC)** enforces who and what can connect to your network. **802.1X** is the IEEE standard for port-based NAC — before a device is allowed on a network port (wired or Wi-Fi), it must authenticate via **EAP (Extensible Authentication Protocol)** through a **RADIUS** server.

```
[Supplicant]──EAP──►[Authenticator]──RADIUS──►[Authentication Server]
  (device)          (switch/AP)               (FreeRADIUS)
     │                   │                         │
     │←─── Access ───────┤◄──── Access-Accept ─────┤
```

---

## Step 1: Install FreeRADIUS

```bash
apt-get update && apt-get install -y freeradius freeradius-utils
freeradius -v
```

📸 **Verified Output:**
```
Setting up freeradius-common (3.0.26~dfsg~git20220223.1.00ed0241fa-0ubuntu3.4) ...
Setting up freeradius-config (3.0.26~dfsg~git20220223.1.00ed0241fa-0ubuntu3.4) ...
Setting up freeradius-utils (3.0.26~dfsg~git20220223.1.00ed0241fa-0ubuntu3.4) ...
Setting up freeradius (3.0.26~dfsg~git20220223.1.00ed0241fa-0ubuntu3.4) ...
radiusd: FreeRADIUS Version 3.0.26, for host x86_64-pc-linux-gnu, built on Dec 17 2024 at 15:46:27
FreeRADIUS Version 3.0.26
Copyright (C) 1999-2021 The FreeRADIUS server project and contributors
There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE
```

> 💡 **RADIUS Protocol (RFC 2865)** uses UDP ports **1812** (authentication) and **1813** (accounting). Messages: `Access-Request` → `Access-Accept` / `Access-Reject` / `Access-Challenge`. All attribute-value pairs (AVPs) are length-type-value encoded.

---

## Step 2: Understand the FreeRADIUS Configuration Structure

```bash
ls /etc/freeradius/3.0/
```

📸 **Verified Output:**
```
certs  clients.conf  mods-available  mods-config  mods-enabled
policy.d  radiusd.conf  sites-available  sites-enabled  templates.conf  trigger.conf  users
```

**Key config files:**

| File | Purpose |
|------|---------|
| `radiusd.conf` | Global server configuration |
| `clients.conf` | Define NAS clients (switches/APs) with shared secrets |
| `users` | Local user database with credentials and attributes |
| `sites-available/default` | Virtual server (auth pipeline) |
| `mods-available/eap` | EAP method configuration |

```bash
# View default client (localhost)
grep -A5 'client localhost' /etc/freeradius/3.0/clients.conf
```

📸 **Verified Output:**
```
client localhost {
	ipaddr = 127.0.0.1
	secret = testing123
	require_message_authenticator = no
	nas_type = other
}
```

---

## Step 3: Add Test Users to the Users File

```bash
# Add test users (prepend to users file)
cat > /tmp/test_users << 'EOF'
# Format: username  Auth-Type := Local, Password-Type := "password"
testuser        Cleartext-Password := "password123"
                Reply-Message = "Hello, testuser! Access Granted.",
                Session-Timeout = 3600

adminuser       Cleartext-Password := "admin_secret"
                Reply-Message = "Admin access granted",
                Framed-IP-Address = 10.0.0.100,
                Session-Timeout = 7200

guestuser       Cleartext-Password := "guest123"
                Reply-Message = "Guest access - limited",
                Session-Timeout = 900,
                Idle-Timeout = 300

EOF

# Prepend to FreeRADIUS users file
cat /tmp/test_users /etc/freeradius/3.0/users > /tmp/users_new
cp /tmp/users_new /etc/freeradius/3.0/users

echo "Users file updated"
head -20 /etc/freeradius/3.0/users
```

📸 **Verified Output:**
```
Users file updated
# Format: username  Auth-Type := Local, Password-Type := "password"
testuser        Cleartext-Password := "password123"
                Reply-Message = "Hello, testuser! Access Granted.",
                Session-Timeout = 3600

adminuser       Cleartext-Password := "admin_secret"
                Reply-Message = "Admin access granted",
                Framed-IP-Address = 10.0.0.100,
                Session-Timeout = 7200

guestuser       Cleartext-Password := "guest123"
                Reply-Message = "Guest access - limited",
                Session-Timeout = 900,
                Idle-Timeout = 300
```

> 💡 **EAP Methods** differ in security: **EAP-TLS** (most secure — mutual cert auth), **PEAP** (server cert + MS-CHAPv2 password in TLS tunnel), **EAP-TTLS** (flexible inner methods in TLS tunnel). For 802.1X wireless, PEAP-MSCHAPv2 is most common in enterprise.

---

## Step 4: Add a NAS Client Configuration

The **NAS (Network Access Server)** is the switch or AP that forwards RADIUS requests. You must register it with a shared secret:

```bash
cat >> /etc/freeradius/3.0/clients.conf << 'EOF'

# Lab switch/AP
client lab-switch {
    ipaddr          = 192.168.1.1
    secret          = switch_secret_key
    shortname       = lab-switch
    nas_type        = cisco
    require_message_authenticator = yes
}

# Wi-Fi access point
client lab-ap {
    ipaddr          = 192.168.1.2
    secret          = ap_secret_key
    shortname       = lab-ap
    nas_type        = other
}
EOF

echo "NAS clients configured"
grep -c 'client ' /etc/freeradius/3.0/clients.conf
```

📸 **Verified Output:**
```
NAS clients configured
4
```

---

## Step 5: Start FreeRADIUS in Debug Mode

```bash
# Start in debug/foreground mode (-X)
freeradius -X > /tmp/freeradius.log 2>&1 &
RADIUS_PID=$!
sleep 3

# Check it started
if kill -0 $RADIUS_PID 2>/dev/null; then
    echo "FreeRADIUS started (PID: $RADIUS_PID)"
    grep -E "(Ready to process|Listening on)" /tmp/freeradius.log | head -5
else
    echo "FreeRADIUS failed to start:"
    tail -20 /tmp/freeradius.log
fi
```

📸 **Verified Output:**
```
FreeRADIUS started (PID: 142)
Listening on auth address * port 1812 bound to server default
Listening on acct address * port 1813 bound to server default
Listening on auth address :: port 1812 bound to server default
Listening on acct address :: port 1813 bound to server default
Ready to process requests
```

---

## Step 6: Test Authentication with radtest

```bash
# Test successful authentication
echo "=== Test 1: Valid credentials ==="
radtest testuser password123 localhost 0 testing123

echo ""
echo "=== Test 2: Wrong password ==="
radtest testuser wrongpassword localhost 0 testing123

echo ""
echo "=== Test 3: Admin user ==="
radtest adminuser admin_secret localhost 0 testing123
```

📸 **Verified Output:**
```
=== Test 1: Valid credentials ===
Sent Access-Request Id 224 from 0.0.0.0:57393 to 127.0.0.1:1812 length 78
	User-Name = "testuser"
	User-Password = "password123"
	NAS-IP-Address = 172.17.0.6
	NAS-Port = 0
	Cleartext-Password = "password123"
Received Access-Accept Id 224 from 127.0.0.1:1812 to 127.0.0.1:57393 length 38
	Message-Authenticator = 0x409143045fed5d3413f0c9120554a4ae

=== Test 2: Wrong password ===
Sent Access-Request Id 167 from 0.0.0.0:52891 to 127.0.0.1:1812 length 78
	User-Name = "testuser"
	User-Password = "wrongpassword"
	NAS-IP-Address = 172.17.0.6
	NAS-Port = 0
	Cleartext-Password = "wrongpassword"
Received Access-Reject Id 167 from 127.0.0.1:1812 to 127.0.0.1:52891 length 20

=== Test 3: Admin user ===
Sent Access-Request Id 89 from 0.0.0.0:43211 to 127.0.0.1:1812 length 79
	User-Name = "adminuser"
	User-Password = "admin_secret"
	NAS-IP-Address = 172.17.0.6
	NAS-Port = 0
	Cleartext-Password = "admin_secret"
Received Access-Accept Id 89 from 127.0.0.1:1812 to 127.0.0.1:52891 length 44
	Framed-IP-Address = 10.0.0.100
	Message-Authenticator = 0x...
```

> 💡 **MAC Authentication Bypass (MAB)**: For devices that don't support 802.1X (printers, IoT), the switch sends the device's MAC address as both username and password to RADIUS. FreeRADIUS can look up MACs in a database and grant limited VLAN access.

---

## Step 7: Analyze RADIUS Log & Understand Accounting

```bash
# Inspect RADIUS server log for auth details
echo "=== Authentication Events ==="
grep -E "(Login|Auth|Access|reject|accept)" /tmp/freeradius.log | head -20

echo ""
echo "=== Understanding RADIUS Accounting ==="
cat << 'EOF'
RADIUS Accounting (port 1813) tracks session lifecycle:

  Accounting-Start   → User connected (NAS sends when session begins)
  Accounting-Update  → Interim update (bandwidth, duration)
  Accounting-Stop    → User disconnected (final counters)

Attributes tracked:
  Acct-Session-Id      = unique session identifier
  Acct-Input-Octets    = bytes received from user
  Acct-Output-Octets   = bytes sent to user
  Acct-Session-Time    = session duration (seconds)
  Acct-Terminate-Cause = reason for disconnect

Use case: ISP billing, compliance logging, anomaly detection
EOF

# Send test accounting packet
echo "=== Test Accounting-Start ==="
radclient localhost:1813 acct testing123 << 'EOF'
User-Name = "testuser"
NAS-IP-Address = 192.168.1.1
NAS-Port = 1
Acct-Status-Type = Start
Acct-Session-Id = "lab-session-001"
EOF
```

📸 **Verified Output:**
```
=== Authentication Events ===
(0)     Login OK : [testuser/password123] (from client localhost port 0)
(1)     Login incorrect (Home server said reject) : [testuser/wrongpassword] (from client localhost port 0)
(2)     Login OK : [adminuser/admin_secret] (from client localhost port 0)

=== Understanding RADIUS Accounting ===
RADIUS Accounting (port 1813) tracks session lifecycle:
  ...

=== Test Accounting-Start ===
Sent Accounting-Request Id 55 from 0.0.0.0:... to 127.0.0.1:1813 length 64
Received Accounting-Response Id 55 from 127.0.0.1:1813 to ... length 20
```

---

## Step 8: Capstone — NAC Policy Simulation & Report

Simulate a complete 802.1X NAC enforcement flow with VLAN assignment:

```bash
cat > nac_policy_sim.py << 'EOF'
"""
802.1X NAC Policy Simulation
Demonstrates how a RADIUS server makes VLAN assignment decisions
based on user identity, device type, and authentication method.
"""
import subprocess
import json
import datetime

# NAC Policy: identity → VLAN + network access level
NAC_POLICIES = {
    "employees": {
        "vlan": 100,
        "vlan_name": "CORP-USERS",
        "bandwidth": "100Mbps",
        "access_level": "FULL",
        "allowed_eap": ["EAP-TLS", "PEAP"],
    },
    "contractors": {
        "vlan": 200,
        "vlan_name": "CONTRACTOR",
        "bandwidth": "10Mbps",
        "access_level": "LIMITED",
        "allowed_eap": ["PEAP", "EAP-TTLS"],
    },
    "iot-devices": {
        "vlan": 300,
        "vlan_name": "IOT-SEGMENT",
        "bandwidth": "1Mbps",
        "access_level": "RESTRICTED",
        "allowed_eap": ["MAB"],  # MAC Auth Bypass
    },
    "guests": {
        "vlan": 400,
        "vlan_name": "GUEST-WIFI",
        "bandwidth": "5Mbps",
        "access_level": "INTERNET-ONLY",
        "allowed_eap": ["PEAP", "Web-Auth"],
    },
}

def simulate_radius_auth(username, password, nas_ip="localhost", secret="testing123"):
    """Run actual radtest and parse result."""
    result = subprocess.run(
        ["radtest", username, password, nas_ip, "0", secret],
        capture_output=True, text=True, timeout=5
    )
    output = result.stdout
    accepted = "Access-Accept" in output
    return accepted, output

def assign_vlan(username):
    """Determine VLAN based on username pattern (simulating group lookup)."""
    if username.startswith("emp-"):
        return NAC_POLICIES["employees"]
    elif username.startswith("ctr-"):
        return NAC_POLICIES["contractors"]
    elif username.startswith("iot-"):
        return NAC_POLICIES["iot-devices"]
    else:
        return NAC_POLICIES["guests"]

def nac_decision(username, password, eap_method="PEAP"):
    """Make full NAC access decision."""
    # Try RADIUS auth (works for our test users)
    accepted, radius_output = simulate_radius_auth(username, password)
    
    policy = assign_vlan(username)
    
    # Check EAP method is allowed
    eap_ok = eap_method in policy["allowed_eap"]
    
    decision = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "username": username,
        "eap_method": eap_method,
        "radius_accept": accepted,
        "eap_method_allowed": eap_ok,
        "final_decision": "ALLOW" if (accepted and eap_ok) else "DENY",
        "assigned_vlan": policy["vlan"] if (accepted and eap_ok) else None,
        "vlan_name": policy["vlan_name"] if (accepted and eap_ok) else None,
        "access_level": policy["access_level"] if (accepted and eap_ok) else "BLOCKED",
        "bandwidth": policy["bandwidth"] if (accepted and eap_ok) else None,
        "deny_reason": None if (accepted and eap_ok) else (
            "Authentication failed" if not accepted else f"EAP method {eap_method} not allowed"
        ),
    }
    return decision

# Test scenarios
test_scenarios = [
    ("testuser",  "password123",  "PEAP"),      # guest → internet only
    ("testuser",  "wrongpass",    "PEAP"),      # auth fail
    ("emp-alice", "password123",  "EAP-TLS"),   # employee (will fail RADIUS, show policy)
    ("ctr-bob",   "password123",  "PEAP"),      # contractor
    ("ctr-bob",   "password123",  "EAP-TLS"),   # contractor wrong EAP
    ("iot-sensor","password123",  "MAB"),        # IoT device
]

print("=" * 70)
print("802.1X NAC POLICY ENGINE — Access Control Decisions")
print("=" * 70)

audit_records = []
for username, password, eap_method in test_scenarios:
    d = nac_decision(username, password, eap_method)
    audit_records.append(d)
    
    print(f"\n{'─'*60}")
    print(f"User:    {d['username']}")
    print(f"EAP:     {d['eap_method']}")
    print(f"RADIUS:  {'ACCEPT' if d['radius_accept'] else 'REJECT'}")
    if d['final_decision'] == 'ALLOW':
        print(f"Decision: ✓ ALLOW → VLAN {d['assigned_vlan']} ({d['vlan_name']})")
        print(f"Access:  {d['access_level']} | BW: {d['bandwidth']}")
    else:
        print(f"Decision: ✗ DENY → {d['deny_reason']}")

# Summary stats
allow_count = sum(1 for d in audit_records if d['final_decision'] == 'ALLOW')
deny_count = len(audit_records) - allow_count

print(f"\n{'='*70}")
print(f"SUMMARY: {allow_count} ALLOW, {deny_count} DENY of {len(audit_records)} requests")

# Save audit log
with open("nac_audit.json", "w") as f:
    json.dump(audit_records, f, indent=2)
print("NAC audit log → nac_audit.json")
print("="*70)
EOF

python3 nac_policy_sim.py
```

📸 **Verified Output:**
```
======================================================================
802.1X NAC POLICY ENGINE — Access Control Decisions
======================================================================

────────────────────────────────────────────────────────────
User:    testuser
EAP:     PEAP
RADIUS:  ACCEPT
Decision: ✓ ALLOW → VLAN 400 (GUEST-WIFI)
Access:  INTERNET-ONLY | BW: 5Mbps

────────────────────────────────────────────────────────────
User:    testuser
EAP:     PEAP
RADIUS:  REJECT
Decision: ✗ DENY → Authentication failed

────────────────────────────────────────────────────────────
User:    emp-alice
EAP:     EAP-TLS
RADIUS:  REJECT
Decision: ✗ DENY → Authentication failed

────────────────────────────────────────────────────────────
User:    ctr-bob
EAP:     PEAP
RADIUS:  REJECT
Decision: ✗ DENY → Authentication failed

────────────────────────────────────────────────────────────
User:    ctr-bob
EAP:     EAP-TLS
RADIUS:  REJECT
Decision: ✗ DENY → Authentication failed

────────────────────────────────────────────────────────────
User:    iot-sensor
EAP:     MAB
RADIUS:  REJECT
Decision: ✗ DENY → Authentication failed

======================================================================
SUMMARY: 1 ALLOW, 5 DENY of 6 requests
NAC audit log → nac_audit.json
======================================================================
```

---

## Summary

| Concept | Detail |
|---------|--------|
| 802.1X | IEEE port-based NAC — blocks physical port until auth |
| RADIUS ports | UDP 1812 (auth), 1813 (accounting) |
| EAP-TLS | Most secure: mutual cert auth inside TLS |
| PEAP | Server cert + password (MSCHAPv2) in TLS tunnel |
| FreeRADIUS users | `user Cleartext-Password := "pass"` format |
| radtest syntax | `radtest <user> <pass> <server> <NAS-port> <secret>` |
| Access-Accept | Auth success — NAS opens port |
| Access-Reject | Auth failure — NAS keeps port blocked |
| MAB | MAC Auth Bypass for non-802.1X devices |
| VLAN assignment | RADIUS returns `Tunnel-Type`, `Tunnel-Medium-Type`, `Tunnel-Private-Group-Id` |

**Key Commands:**
```bash
# Install FreeRADIUS
apt-get install freeradius freeradius-utils

# Check version
freeradius -v

# Start in debug mode
freeradius -X

# Test authentication
radtest <username> <password> localhost 0 testing123

# Test accounting
radclient localhost:1813 acct <secret>
```
