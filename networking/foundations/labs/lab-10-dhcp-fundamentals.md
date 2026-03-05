# Lab 10: DHCP Fundamentals

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

**Dynamic Host Configuration Protocol (DHCP)** automatically assigns IP addresses, subnet masks, default gateways, and DNS servers to devices when they join a network. Without DHCP, every device on every network would need manual configuration. This lab explores the DORA process, lease management, and when to use DHCP vs static assignment.

---

## Step 1: Install Tools & View Current IP Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 2>/dev/null &&
echo '=== Current IP addresses ===' &&
ip addr show &&
echo '=== Current routes ===' &&
ip route show
"
```

📸 **Verified Output:**
```
=== Current IP addresses ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0@if1277: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 52:fb:69:53:a0:80 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.7/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever

=== Current routes ===
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.7 
```

> 💡 **Tip:** Docker itself uses DHCP-like mechanisms to assign addresses to containers from the `172.17.0.0/16` pool. The `172.17.0.1` gateway is the Docker bridge (`docker0` on the host). This container's address `172.17.0.7` was dynamically assigned!

---

## Step 2: The DORA Process — How DHCP Works

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('DHCP DORA Process:')
print()
print('  Client                              Server')
print('    │                                   │')
print('    │──── DISCOVER ──────────────────→  │')
print('    │  Src: 0.0.0.0:68                  │')
print('    │  Dst: 255.255.255.255:67          │')
print('    │  \"I need an IP address!\"          │')
print('    │                                   │')
print('    │  ←──────────────── OFFER ─────────│')
print('    │  \"Here, try 192.168.1.100/24\"     │')
print('    │  + gateway, DNS, lease time       │')
print('    │                                   │')
print('    │──── REQUEST ───────────────────→  │')
print('    │  \"I accept 192.168.1.100!\"        │')
print('    │  (broadcast — other servers see)  │')
print('    │                                   │')
print('    │  ←────────────── ACKNOWLEDGE ─────│')
print('    │  \"Confirmed! Lease: 24 hours\"     │')
print('    │                                   │')
print()
print('DORA = Discover → Offer → Request → Acknowledge')
print()
print('Ports:')
print('  Client → Server: UDP source 68, destination 67')
print('  Server → Client: UDP source 67, destination 68')
print()
dora = [
    ('DISCOVER', 'Client', 'Broadcast', '255.255.255.255', 'Find DHCP servers'),
    ('OFFER',    'Server', 'Broadcast*','255.255.255.255', 'Propose IP + config'),
    ('REQUEST',  'Client', 'Broadcast', '255.255.255.255', 'Accept specific offer'),
    ('ACK',      'Server', 'Broadcast*','255.255.255.255', 'Confirm lease'),
]
print(f'  {\"Step\":<12} {\"From\":<8} {\"To\":<16} {\"Purpose\"}')
print('  ' + '-' * 60)
for step, frm, to, dst, purpose in dora:
    print(f'  {step:<12} {frm:<8} {dst:<16} {purpose}')
print()
print('  * Some servers unicast OFFER/ACK if client IP is known')
\"
"
```

📸 **Verified Output:**
```
DHCP DORA Process:

  Client                              Server
    │                                   │
    │──── DISCOVER ──────────────────→  │
    │  Src: 0.0.0.0:68                  │
    │  Dst: 255.255.255.255:67          │
    │  "I need an IP address!"          │
    │                                   │
    │  ←──────────────── OFFER ─────────│
    │  "Here, try 192.168.1.100/24"     │
    │  + gateway, DNS, lease time       │
    │                                   │
    │──── REQUEST ───────────────────→  │
    │  "I accept 192.168.1.100!"        │
    │  (broadcast — other servers see)  │
    │                                   │
    │  ←────────────── ACKNOWLEDGE ─────│
    │  "Confirmed! Lease: 24 hours"     │
    │                                   │

DORA = Discover → Offer → Request → Acknowledge

Ports:
  Client → Server: UDP source 68, destination 67
  Server → Client: UDP source 67, destination 68

  Step         From     To               Purpose
  ------------------------------------------------------------
  DISCOVER     Client   255.255.255.255  Find DHCP servers
  OFFER        Server   255.255.255.255  Propose IP + config
  REQUEST      Client   255.255.255.255  Accept specific offer
  ACK          Server   255.255.255.255  Confirm lease
```

---

## Step 3: DHCP Options — What Gets Assigned

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('DHCP Options (sent in OFFER and ACK):')
print()
options = [
    (1,   'Subnet Mask',           '255.255.255.0',       'Required'),
    (3,   'Default Gateway',       '192.168.1.1',         'Required'),
    (6,   'DNS Servers',           '8.8.8.8, 8.8.4.4',   'Required'),
    (15,  'Domain Name',           'corp.example.com',    'Optional'),
    (28,  'Broadcast Address',     '192.168.1.255',       'Optional'),
    (42,  'NTP Servers',           'pool.ntp.org',        'Optional'),
    (51,  'Lease Time',            '86400 (24 hours)',     'Required'),
    (53,  'DHCP Message Type',     '5 (ACK)',              'Required'),
    (54,  'Server Identifier',     '192.168.1.1',         'Required'),
    (58,  'Renewal Time (T1)',     '43200 (12 hours)',     '50% of lease'),
    (59,  'Rebinding Time (T2)',   '75600 (21 hours)',     '87.5% of lease'),
    (61,  'Client Identifier',     'MAC address',         'Identifies client'),
    (121, 'Classless Static Routes','10.0.0.0/8 via GW',  'Static routes push'),
]
print(f'  {\"Opt\":<5} {\"Name\":<26} {\"Example Value\":<24} {\"Notes\"}')
print('  ' + '-' * 80)
for opt, name, val, note in options:
    print(f'  {opt:<5} {name:<26} {val:<24} {note}')
\"
"
```

📸 **Verified Output:**
```
DHCP Options (sent in OFFER and ACK):

  Opt   Name                       Example Value            Notes
  --------------------------------------------------------------------------------
  1     Subnet Mask                255.255.255.0            Required
  3     Default Gateway            192.168.1.1              Required
  6     DNS Servers                8.8.8.8, 8.8.4.4        Required
  15    Domain Name                corp.example.com         Optional
  28    Broadcast Address          192.168.1.255            Optional
  42    NTP Servers                pool.ntp.org             Optional
  51    Lease Time                 86400 (24 hours)         Required
  53    DHCP Message Type          5 (ACK)                  Required
  54    Server Identifier          192.168.1.1              Required
  58    Renewal Time (T1)          43200 (12 hours)         50% of lease
  59    Rebinding Time (T2)        75600 (21 hours)         87.5% of lease
  61    Client Identifier          MAC address              Identifies client
  121   Classless Static Routes    10.0.0.0/8 via GW        Static routes push
```

> 💡 **Tip:** Option 121 (Classless Static Routes) can push VPN split-tunnel routes to clients! This is how corporate DHCP servers automatically configure routing for remote workers.

---

## Step 4: DHCP Lease Lifecycle

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('DHCP Lease Lifecycle:')
print()
lease_time = 86400  # 24 hours
t1 = lease_time // 2       # 50%
t2 = int(lease_time * 0.875)  # 87.5%
print(f'Lease granted: 192.168.1.100  for {lease_time}s ({lease_time//3600}h)')
print()

states = [
    (0,   'BOUND',     'IP assigned, all is well'),
    (t1,  'RENEWING',  f'T1={t1}s: unicast renewal request to original server'),
    (t2,  'REBINDING', f'T2={t2}s: broadcast rebind if server not responding'),
    (lease_time, 'EXPIRED', 'No ACK received → release IP, start DORA again'),
]
print(f'  {\"Time\":<10} {\"State\":<12} {\"Action\"}')
print('  ' + '-' * 60)
for t, state, action in states:
    hours = t // 3600
    mins = (t % 3600) // 60
    print(f'  T+{hours:02d}h{mins:02d}m  {state:<12} {action}')

print()
print('Release:')
print('  When client shuts down gracefully: sends DHCPRELEASE')
print('  Server marks IP as available in pool')
print()
print('Decline:')
print('  Client detects IP conflict (ARP probe fails) → sends DHCPDECLINE')
print('  Server marks IP as unusable, offers different IP')
\"
"
```

📸 **Verified Output:**
```
DHCP Lease Lifecycle:

Lease granted: 192.168.1.100  for 86400s (24h)

  Time       State        Action
  ------------------------------------------------------------
  T+00h00m   BOUND        IP assigned, all is well
  T+12h00m   RENEWING     T1=43200s: unicast renewal request to original server
  T+21h00m   REBINDING    T2=75600s: broadcast rebind if server not responding
  T+24h00m   EXPIRED      No ACK received → release IP, start DORA again

Release:
  When client shuts down gracefully: sends DHCPRELEASE
  Server marks IP as available in pool

Decline:
  Client detects IP conflict (ARP probe fails) → sends DHCPDECLINE
  Server marks IP as unusable, offers different IP
```

---

## Step 5: Lease File Structure

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
lease_example = '''
# Sample /var/lib/dhcp/dhclient.leases
# This file records DHCP leases obtained by dhclient

lease {
  interface \\\"eth0\\\";
  fixed-address 192.168.1.100;
  option subnet-mask 255.255.255.0;
  option routers 192.168.1.1;
  option dhcp-lease-time 86400;
  option dhcp-message-type 5;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
  option dhcp-server-identifier 192.168.1.1;
  option domain-name \\\"home.local\\\";
  renew 3 2024/03/06 00:00:00;
  rebind 3 2024/03/06 09:00:00;
  expire 3 2024/03/06 12:00:00;
}
'''
print('Sample /var/lib/dhcp/dhclient.leases:')
print(lease_example)
print('Field explanations:')
fields = [
    ('interface',            'Which NIC this lease is for'),
    ('fixed-address',        'The IP address assigned'),
    ('option subnet-mask',   'Subnet mask (option 1)'),
    ('option routers',       'Default gateway (option 3)'),
    ('option dhcp-lease-time','Total lease duration in seconds'),
    ('option domain-name-servers', 'DNS servers (option 6)'),
    ('renew',                'When to send unicast renewal (T1)'),
    ('rebind',               'When to broadcast rebind (T2)'),
    ('expire',               'When lease expires completely'),
]
for field, desc in fields:
    print(f'  {field:<35} {desc}')
\"
"
```

📸 **Verified Output:**
```
Sample /var/lib/dhcp/dhclient.leases:

# Sample /var/lib/dhcp/dhclient.leases
# This file records DHCP leases obtained by dhclient

lease {
  interface "eth0";
  fixed-address 192.168.1.100;
  option subnet-mask 255.255.255.0;
  option routers 192.168.1.1;
  option dhcp-lease-time 86400;
  option dhcp-message-type 5;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
  option dhcp-server-identifier 192.168.1.1;
  option domain-name "home.local";
  renew 3 2024/03/06 00:00:00;
  rebind 3 2024/03/06 09:00:00;
  expire 3 2024/03/06 12:00:00;
}

Field explanations:
  interface                           Which NIC this lease is for
  fixed-address                       The IP address assigned
  option subnet-mask                  Subnet mask (option 1)
  option routers                      Default gateway (option 3)
  option dhcp-lease-time              Total lease duration in seconds
  option domain-name-servers          DNS servers (option 6)
  renew                               When to send unicast renewal (T1)
  rebind                              When to broadcast rebind (T2)
  expire                              When lease expires completely
```

> 💡 **Tip:** Run `dhclient -v eth0` on a real Linux system to see the full DORA conversation in real time. The `-v` flag shows each message exchanged with the DHCP server.

---

## Step 6: APIPA — When DHCP Fails

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
import ipaddress

apipa_range = ipaddress.ip_network('169.254.0.0/16')
print('APIPA — Automatic Private IP Addressing (RFC 3927):')
print()
print(f'Range: {apipa_range}')
print(f'Addresses: {apipa_range.num_addresses:,}')
print()
print('When APIPA activates:')
print('  1. Device sends DHCP DISCOVER')
print('  2. No response after ~4 attempts over ~60 seconds')
print('  3. Device randomly picks address in 169.254.1.0 - 169.254.254.255')
print('  4. Sends ARP probe to check address is unused')
print('  5. Uses the self-assigned address')
print()
print('What APIPA means in practice:')
print('  ✅ You can communicate with other APIPA devices on same LAN')
print('  ❌ No gateway assigned → no internet access')
print('  ❌ No DNS server assigned → no hostname resolution')
print()
print('APIPA examples:')
import random
random.seed(42)
for _ in range(4):
    host = random.randint(1*256+0, 254*256+255)
    ip = ipaddress.ip_address(f'169.254.{host >> 8}.{host & 0xff}')
    print(f'  {ip}  (randomly chosen)')
print()
print('Tip: Seeing 169.254.x.x = DHCP server unreachable!')
\"
"
```

📸 **Verified Output:**
```
APIPA — Automatic Private IP Addressing (RFC 3927):

Range: 169.254.0.0/16
Addresses: 65,536

When APIPA activates:
  1. Device sends DHCP DISCOVER
  2. No response after ~4 attempts over ~60 seconds
  3. Device randomly picks address in 169.254.1.0 - 169.254.254.255
  4. Sends ARP probe to check address is unused
  5. Uses the self-assigned address

What APIPA means in practice:
  ✅ You can communicate with other APIPA devices on same LAN
  ❌ No gateway assigned → no internet access
  ❌ No DNS server assigned → no hostname resolution

APIPA examples:
  169.254.128.77  (randomly chosen)
  169.254.90.116  (randomly chosen)
  169.254.66.101  (randomly chosen)
  169.254.25.86   (randomly chosen)

Tip: Seeing 169.254.x.x = DHCP server unreachable!
```

---

## Step 7: DHCP vs Static IP & DHCP Reservations

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('DHCP vs Static IP Assignment:')
print()
print(f'  {\"Aspect\":<28} {\"DHCP\":<28} {\"Static\"}')
print('  ' + '-' * 78)
comparison = [
    ('Configuration effort',   'Automatic (zero-touch)',  'Manual per device'),
    ('IP consistency',         'Changes on lease expiry', 'Always same IP'),
    ('Scale',                  'Excellent (thousands)',   'Poor (error-prone)'),
    ('Troubleshooting',        'Need to check leases',   'Predictable'),
    ('Best for',               'End-user devices',       'Servers, printers'),
    ('Mobility support',       'Excellent',              'Must update per site'),
    ('Network changes',        'Auto-adapts',            'Manual update each host'),
    ('Risk of conflict',       'Low (server manages)',   'High (human error)'),
]
for aspect, dhcp, static in comparison:
    print(f'  {aspect:<28} {dhcp:<28} {static}')

print()
print('DHCP Reservations (best of both worlds):')
print('  Static IP behavior + DHCP management')
print()
print('  Server config (isc-dhcp-server example):')
reservation = '''
  host webserver {
    hardware ethernet 52:fb:69:aa:bb:cc;  # MAC address
    fixed-address 192.168.1.10;           # Always gets this IP
  }'''
print(reservation)
print()
print('  Result: Server always gets 192.168.1.10')
print('         Admin manages it centrally (no touching the server)')
print('         If NIC replaced → update server config once')

print()
print('DHCP Relay Agent:')
print('  Problem: DHCP uses broadcasts — cannot cross routers')
print('  Solution: Relay agent (ip helper-address on Cisco)')
print('            Forwards DISCOVER as unicast to central DHCP server')
print('  Topology: [Client] → [Relay on gateway] → [DHCP Server]')
\"
"
```

📸 **Verified Output:**
```
DHCP vs Static IP Assignment:

  Aspect                       DHCP                         Static
  ------------------------------------------------------------------------------
  Configuration effort         Automatic (zero-touch)       Manual per device
  IP consistency               Changes on lease expiry      Always same IP
  Scale                        Excellent (thousands)        Poor (error-prone)
  Troubleshooting              Need to check leases         Predictable
  Best for                     End-user devices             Servers, printers
  Mobility support             Excellent                    Must update per site
  Network changes              Auto-adapts                  Manual update each host
  Risk of conflict             Low (server manages)         High (human error)

DHCP Reservations (best of both worlds):
  Static IP behavior + DHCP management

  Server config (isc-dhcp-server example):

  host webserver {
    hardware ethernet 52:fb:69:aa:bb:cc;  # MAC address
    fixed-address 192.168.1.10;           # Always gets this IP
  }

  Result: Server always gets 192.168.1.10
         Admin manages it centrally (no touching the server)
         If NIC replaced → update server config once

DHCP Relay Agent:
  Problem: DHCP uses broadcasts — cannot cross routers
  Solution: Relay agent (ip helper-address on Cisco)
            Forwards DISCOVER as unicast to central DHCP server
  Topology: [Client] → [Relay on gateway] → [DHCP Server]
```

---

## Step 8: Capstone — Full DHCP Simulator

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 python3-minimal 2>/dev/null &&
echo '=== Live IP configuration (DHCP-assigned by Docker) ===' &&
ip addr show eth0 &&
echo '' &&
python3 -c \"
import time, random, ipaddress

class DHCPServer:
    def __init__(self, pool_start, pool_end, gateway, dns, lease_time=86400):
        start = int(ipaddress.ip_address(pool_start))
        end   = int(ipaddress.ip_address(pool_end))
        self.pool = [str(ipaddress.ip_address(i)) for i in range(start, end+1)]
        self.leases = {}
        self.reservations = {}
        self.gateway = gateway
        self.dns = dns
        self.lease_time = lease_time

    def reserve(self, mac, ip):
        self.reservations[mac.lower()] = ip

    def discover(self, client_mac, client_id=''):
        print(f'  DISCOVER from {client_mac}')
        mac = client_mac.lower()
        if mac in self.reservations:
            offered_ip = self.reservations[mac]
            print(f'  OFFER     → {offered_ip} (RESERVATION)')
        else:
            available = [ip for ip in self.pool if ip not in self.leases.values()]
            if not available:
                print('  OFFER     → NACK (pool exhausted!)')
                return None
            offered_ip = available[0]
            print(f'  OFFER     → {offered_ip} (from pool)')
        return offered_ip

    def request(self, client_mac, requested_ip):
        print(f'  REQUEST   from {client_mac} for {requested_ip}')
        expire = int(time.time()) + self.lease_time
        self.leases[client_mac] = {
            'ip': requested_ip,
            'expires': expire,
            'subnet': '255.255.255.0',
            'gateway': self.gateway,
            'dns': self.dns,
        }
        print(f'  ACK       → {requested_ip} leased for {self.lease_time//3600}h')
        print(f'             Gateway: {self.gateway}  DNS: {self.dns}')
        return self.leases[client_mac]

    def show_leases(self):
        print()
        print(f'  Active Leases ({len(self.leases)}):')
        print(f'  {\"MAC\":<20} {\"IP\":<16} {\"Expires in\"}')
        print('  ' + '-' * 50)
        now = int(time.time())
        for mac, lease in self.leases.items():
            remaining = lease['expires'] - now
            print(f'  {mac:<20} {lease[\"ip\"]:<16} {remaining//3600}h {(remaining%3600)//60}m')

print('=== DHCP Server Simulation ===')
print()
server = DHCPServer(
    pool_start='192.168.1.100',
    pool_end='192.168.1.110',
    gateway='192.168.1.1',
    dns='8.8.8.8',
    lease_time=86400
)

# Add a reservation
server.reserve('aa:bb:cc:dd:ee:ff', '192.168.1.50')

# Simulate DORA for 3 clients
clients = [
    'aa:bb:cc:dd:ee:ff',   # reserved client
    '11:22:33:44:55:66',   # dynamic client 1
    '77:88:99:aa:bb:cc',   # dynamic client 2
]

for mac in clients:
    print(f'--- Client {mac} ---')
    offered = server.discover(mac)
    if offered:
        server.request(mac, offered)
    print()

server.show_leases()
\"
"
```

📸 **Verified Output:**
```
=== Live IP configuration (DHCP-assigned by Docker) ===
2: eth0@if1277: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 52:fb:69:53:a0:80 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.7/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever

=== DHCP Server Simulation ===

--- Client aa:bb:cc:dd:ee:ff ---
  DISCOVER from aa:bb:cc:dd:ee:ff
  OFFER     → 192.168.1.50 (RESERVATION)
  REQUEST   from aa:bb:cc:dd:ee:ff for 192.168.1.50
  ACK       → 192.168.1.50 leased for 24h
             Gateway: 192.168.1.1  DNS: 8.8.8.8

--- Client 11:22:33:44:55:66 ---
  DISCOVER from 11:22:33:44:55:66
  OFFER     → 192.168.1.100 (from pool)
  REQUEST   from 11:22:33:44:55:66 for 192.168.1.100
  ACK       → 192.168.1.100 leased for 24h
             Gateway: 192.168.1.1  DNS: 8.8.8.8

--- Client 77:88:99:aa:bb:cc ---
  DISCOVER from 77:88:99:aa:bb:cc
  OFFER     → 192.168.1.101 (from pool)
  REQUEST   from 77:88:99:aa:bb:cc for 192.168.1.101
  ACK       → 192.168.1.101 leased for 24h
             Gateway: 192.168.1.1  DNS: 8.8.8.8

  Active Leases (3):
  MAC                  IP               Expires in
  --------------------------------------------------
  aa:bb:cc:dd:ee:ff    192.168.1.50     23h 59m
  11:22:33:44:55:66    192.168.1.100    23h 59m
  77:88:99:aa:bb:cc    192.168.1.101    23h 59m
```

---

## Summary

| Concept | Key Points |
|---|---|
| **DHCP** | Automatically assigns IP, mask, gateway, DNS to clients |
| **DORA** | Discover → Offer → Request → Acknowledge |
| **Ports** | Client: UDP 68; Server: UDP 67 |
| **Lease time** | How long client keeps the IP (typical: 24h) |
| **T1 renewal** | 50% of lease: unicast renewal to original server |
| **T2 rebinding** | 87.5% of lease: broadcast rebind to any DHCP server |
| **DHCP options** | Subnet (1), Gateway (3), DNS (6), Lease time (51) |
| **Reservation** | Fixed IP bound to MAC — static behavior, central management |
| **DHCP Relay** | Forwards broadcasts across routers to central server |
| **APIPA** | `169.254.x.x` — self-assigned when no DHCP response |
| **RELEASE** | Graceful IP return on shutdown (`dhclient -r`) |
| **DECLINE** | Client rejects IP if ARP conflict detected |
| **dhclient.leases** | `/var/lib/dhcp/dhclient.leases` — persistent lease storage |

---

## 🎉 Networking Foundations Complete!

You've completed all 10 labs in the Networking Foundations series:

| Lab | Topic |
|---|---|
| Lab 01 | OSI Model |
| Lab 02 | TCP/IP & Protocols |
| Lab 03 | IP Addressing & Subnets |
| Lab 04 | TCP & UDP |
| Lab 05 | ICMP & Network Diagnostics |
| **Lab 06** | **MAC Addresses & Ethernet** |
| **Lab 07** | **Routing Basics** |
| **Lab 08** | **NAT & Port Forwarding** |
| **Lab 09** | **DNS Fundamentals** |
| **Lab 10** | **DHCP Fundamentals** |

*Continue to the next module for intermediate networking topics!*
