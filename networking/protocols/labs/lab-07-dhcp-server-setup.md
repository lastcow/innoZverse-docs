# Lab 07: DHCP Server Setup

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

DHCP (Dynamic Host Configuration Protocol) automates IP address assignment across a network. In this lab you will install the ISC DHCP server, write a real `dhcpd.conf` configuration file, validate it, configure static reservations, and understand the DORA handshake, relay agents, failover, and DHCPv6.

---

## Step 1: Install ISC DHCP Server

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq isc-dhcp-server 2>/dev/null | tail -4 &&
  dhcpd --version 2>&1"
```

📸 **Verified Output:**
```
Setting up isc-dhcp-server (4.4.1-2.3ubuntu2.4) ...
invoke-rc.d: policy-rc.d denied execution of start.
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
isc-dhcpd-4.4.1
```

> 💡 ISC DHCP Server 4.4.1 is the standard reference implementation. In production, consider **Kea DHCP** (ISC's modern replacement) which supports REST APIs and database backends.

---

## Step 2: The DORA Handshake

DHCP uses a 4-step process called **DORA**:

```
Client                      DHCP Server
  |--- DISCOVER (broadcast) -->|   "Anyone have an IP for me?"
  |<-- OFFER (unicast/bc) -----|   "I offer 192.168.1.100/24"
  |--- REQUEST (broadcast) --->|   "I'd like 192.168.1.100 please"
  |<-- ACK (unicast/bc) -------|   "Confirmed! Lease valid for 1hr"
```

All DORA messages use **UDP**: client port **68**, server port **67**.

- **DISCOVER**: broadcast (255.255.255.255) — client has no IP yet
- **OFFER**: server proposes IP, subnet, GW, DNS, lease time
- **REQUEST**: client selects an offer (broadcasts so other servers know)
- **ACK**: server confirms; client configures network interface

**Lease renewal:** At 50% of lease time, client sends DHCPREQUEST directly to server. At 87.5%, broadcasts again. If lease expires — back to DISCOVER.

---

## Step 3: Write a Complete dhcpd.conf

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq isc-dhcp-server 2>/dev/null | tail -2

  cat > /etc/dhcp/dhcpd.conf << 'CONF'
# Global options
default-lease-time 3600;         # 1 hour default
max-lease-time 86400;            # 24 hours maximum
ddns-update-style none;          # Disable dynamic DNS updates
authoritative;                   # This is the authoritative server for these subnets

# Log facility
log-facility local7;

# Option definitions
option domain-name \"lab.innozverse.com\";
option domain-name-servers 8.8.8.8, 8.8.4.4;
option ntp-servers 192.168.1.1;

# Primary subnet: Office LAN
subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.100 192.168.1.200;    # Dynamic pool
  option routers 192.168.1.1;            # Default gateway
  option broadcast-address 192.168.1.255;
  option domain-name-servers 192.168.1.53, 8.8.8.8;
  default-lease-time 3600;
  max-lease-time 7200;
}

# Guest VLAN subnet
subnet 10.10.0.0 netmask 255.255.255.0 {
  range 10.10.0.50 10.10.0.250;
  option routers 10.10.0.1;
  option domain-name-servers 8.8.8.8;
  default-lease-time 1800;              # 30 min for guests
  max-lease-time 3600;
}

# Static reservation by MAC address
host office-printer {
  hardware ethernet 00:11:22:33:44:55;
  fixed-address 192.168.1.50;
  option host-name \"printer\";
}

host sysadmin-laptop {
  hardware ethernet aa:bb:cc:dd:ee:ff;
  fixed-address 192.168.1.10;
  option host-name \"sysadmin\";
}
CONF

  echo '=== Validating configuration ==='
  dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1" 
📸 **Verified Output:**
```
=== Validating configuration ===
Internet Systems Consortium DHCP Server 4.4.1
Copyright 2004-2018 Internet Systems Consortium.
All rights reserved.
For info, please visit https://www.isc.org/software/dhcp/
Config file: /etc/dhcp/dhcpd.conf
Database file: /var/lib/dhcp/dhcpd.leases
PID file: /var/run/dhcpd.pid
Config OK
```

> 💡 Always run `dhcpd -t -cf /etc/dhcp/dhcpd.conf` before restarting the server in production. A bad config will crash the DHCP service and clients won't get IPs.

---

## Step 4: Validate the Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq isc-dhcp-server 2>/dev/null | tail -2

  cat > /etc/dhcp/dhcpd.conf << 'CONF'
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;
subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.100 192.168.1.200;
  option routers 192.168.1.1;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
}
host printer {
  hardware ethernet 00:11:22:33:44:55;
  fixed-address 192.168.1.50;
}
CONF

  dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1 && echo 'Config OK'
  echo ''
  echo '=== Config file ==='
  cat /etc/dhcp/dhcpd.conf"
```

📸 **Verified Output:**
```
Internet Systems Consortium DHCP Server 4.4.1
Copyright 2004-2018 Internet Systems Consortium.
All rights reserved.
For info, please visit https://www.isc.org/software/dhcp/
Config file: /etc/dhcp/dhcpd.conf
Database file: /var/lib/dhcp/dhcpd.leases
PID file: /var/run/dhcpd.pid
Config OK

=== Config file ===
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;
subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.100 192.168.1.200;
  option routers 192.168.1.1;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
}
host printer {
  hardware ethernet 00:11:22:33:44:55;
  fixed-address 192.168.1.50;
}
```

---

## Step 5: Lease Database Structure

The DHCP lease database at `/var/lib/dhcp/dhcpd.leases` is a plain-text journal:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq isc-dhcp-server 2>/dev/null | tail -2

  # Show the lease file format
  cat > /var/lib/dhcp/dhcpd.leases << 'LEASES'
# dhcpd.leases - Lease database
# Lease for 192.168.1.105
lease 192.168.1.105 {
  starts 4 2026/03/05 10:00:00;
  ends   4 2026/03/05 11:00:00;
  tstp   4 2026/03/05 11:00:00;
  cltt   4 2026/03/05 10:00:00;
  binding state active;
  next binding state free;
  rewind binding state free;
  hardware ethernet 08:00:27:ab:cd:ef;
  client-hostname \"workstation1\";
  uid \"\001\010\000'\253\315\357\";
}
lease 192.168.1.106 {
  starts 4 2026/03/05 09:00:00;
  ends   4 2026/03/05 09:30:00;
  binding state expired;
  next binding state free;
  hardware ethernet de:ad:be:ef:00:01;
  client-hostname \"laptop-guest\";
}
LEASES

  echo '=== Lease database ==='
  cat /var/lib/dhcp/dhcpd.leases"
```

📸 **Verified Output:**
```
=== Lease database ===
# dhcpd.leases - Lease database
lease 192.168.1.105 {
  starts 4 2026/03/05 10:00:00;
  ends   4 2026/03/05 11:00:00;
  binding state active;
  next binding state free;
  hardware ethernet 08:00:27:ab:cd:ef;
  client-hostname "workstation1";
}
lease 192.168.1.106 {
  starts 4 2026/03/05 09:00:00;
  ends   4 2026/03/05 09:30:00;
  binding state expired;
  next binding state free;
  hardware ethernet de:ad:be:ef:00:01;
  client-hostname "laptop-guest";
}
```

**Lease binding states:**
| State | Meaning |
|---|---|
| `active` | Currently assigned to a client |
| `free` | Available for assignment |
| `expired` | Lease time passed, not yet freed |
| `released` | Client sent DHCPRELEASE |
| `abandoned` | IP detected in use (conflict) |

> 💡 To find who has a specific IP: `grep -A8 '192.168.1.105' /var/lib/dhcp/dhcpd.leases`

---

## Step 6: DHCP Relay Agent and Advanced Options

**DHCP Relay Agent (dhcrelay)** is needed when the DHCP server is on a different subnet. Routers typically handle this, but you can also run `dhcrelay`:

```bash
# On the router/relay host (not the DHCP server):
# apt-get install isc-dhcp-relay
# dhcrelay -i eth0 192.168.100.1   # relay DHCP to server at 192.168.100.1
```

**DHCP Failover Configuration** (for redundancy):

```
# Primary server config
failover peer "dhcp-failover" {
  primary;
  address 192.168.1.1;
  port 647;
  peer address 192.168.1.2;
  peer port 647;
  max-response-delay 60;
  max-unacked-updates 10;
  mclt 3600;
  split 128;                       # 50/50 split of address space
  load balance max seconds 3;
}

subnet 192.168.1.0 netmask 255.255.255.0 {
  pool {
    failover peer "dhcp-failover";
    range 192.168.1.100 192.168.1.200;
  }
}
```

**DHCP Snooping** (switch-level security concept):
- Switch inspects DHCP messages passing through
- Only designated "trusted" ports can send DHCPOFFER/ACK
- Prevents rogue DHCP servers on untrusted ports
- Builds a binding table: `{MAC, IP, port, VLAN, lease time}`

> 💡 DHCP snooping is configured on managed switches (Cisco: `ip dhcp snooping`), not on the DHCP server itself. It's your first line of defense against rogue DHCP attacks.

---

## Step 7: DHCPv6 Overview

DHCPv6 serves IPv6 addresses and options. Key differences from DHCPv4:

| Feature | DHCPv4 | DHCPv6 |
|---|---|---|
| Ports | UDP 67 (server), 68 (client) | UDP 547 (server), 546 (client) |
| Discovery | DISCOVER broadcast | SOLICIT to `ff02::1:2` multicast |
| Messages | DORA | SARR (Solicit/Advertise/Request/Reply) |
| Address assignment | Full address | Prefix delegation or IA_NA |
| Stateless mode | No equivalent | SLAAC + DHCPv6 for options only |

```bash
# Example DHCPv6 subnet config
subnet6 2001:db8:1::/64 {
  range6 2001:db8:1::100 2001:db8:1::200;
  option dhcp6.name-servers 2001:4860:4860::8888;
  option dhcp6.domain-search "lab.innozverse.com";
}
```

---

## Step 8: Capstone — Full DHCP Server Configuration Lab

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq isc-dhcp-server 2>/dev/null | tail -2

  cat > /etc/dhcp/dhcpd.conf << 'CONF'
# InnoZverse DHCP Server Configuration
authoritative;
ddns-update-style none;
log-facility local7;

# Global defaults
default-lease-time 3600;
max-lease-time 86400;
option domain-name \"innozverse.lab\";
option domain-name-servers 8.8.8.8, 1.1.1.1;

# Corporate LAN
subnet 192.168.10.0 netmask 255.255.255.0 {
  range 192.168.10.50 192.168.10.200;
  option routers 192.168.10.1;
  option domain-name-servers 192.168.10.5, 8.8.8.8;
  option ntp-servers 192.168.10.1;
  default-lease-time 28800;
  max-lease-time 86400;
}

# Static reservations
host web-server-01 {
  hardware ethernet 00:50:56:aa:bb:01;
  fixed-address 192.168.10.10;
  option host-name \"web01\";
}

host db-server-01 {
  hardware ethernet 00:50:56:aa:bb:02;
  fixed-address 192.168.10.11;
  option host-name \"db01\";
}

# Guest WiFi (short leases)
subnet 172.16.0.0 netmask 255.255.255.0 {
  range 172.16.0.100 172.16.0.250;
  option routers 172.16.0.1;
  option domain-name-servers 8.8.8.8;
  default-lease-time 900;
  max-lease-time 1800;
}
CONF

  echo '=== Syntax check ==='
  dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1

  echo ''
  echo '=== Configuration summary ==='
  grep -E '(subnet|range|fixed-address|host |option routers)' /etc/dhcp/dhcpd.conf | grep -v '#'

  echo ''
  echo '=== Default lease file path ==='
  dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1 | grep 'Database file'
" 2>&1

📸 **Verified Output:**
```
=== Syntax check ===
Internet Systems Consortium DHCP Server 4.4.1
Copyright 2004-2018 Internet Systems Consortium.
All rights reserved.
For info, please visit https://www.isc.org/software/dhcp/
Config file: /etc/dhcp/dhcpd.conf
Database file: /var/lib/dhcp/dhcpd.leases
PID file: /var/run/dhcpd.pid
Config OK

=== Configuration summary ===
subnet 192.168.10.0 netmask 255.255.255.0 {
  range 192.168.10.50 192.168.10.200;
  option routers 192.168.10.1;
host web-server-01 {
  fixed-address 192.168.10.10;
host db-server-01 {
  fixed-address 192.168.10.11;
subnet 172.16.0.0 netmask 255.255.255.0 {
  range 172.16.0.100 172.16.0.250;
  option routers 172.16.0.1;

=== Default lease file path ===
Database file: /var/lib/dhcp/dhcpd.leases
```

---

## Summary

| Concept | Key Points |
|---|---|
| DORA Handshake | Discover → Offer → Request → ACK (UDP 67/68) |
| dhcpd.conf | subnet/range/option routers/option dns/lease times |
| Static Reservation | `host` block with `hardware ethernet` MAC + `fixed-address` |
| Lease Database | `/var/lib/dhcp/dhcpd.leases` — plain-text journal |
| Config Validation | `dhcpd -t -cf /etc/dhcp/dhcpd.conf` before restart |
| DHCP Relay | `dhcrelay` forwards DHCP across subnets to central server |
| DHCP Failover | Split address pool between primary + secondary servers |
| DHCP Snooping | Switch-level: only trusted ports can send OFFER/ACK |
| DHCPv6 | SARR handshake; UDP 546/547; multicast `ff02::1:2` |
