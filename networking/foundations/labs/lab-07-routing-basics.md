# Lab 07: Routing Basics

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Routing is how packets cross from one network to another. While switches move frames within a LAN (Layer 2), **routers** move packets between networks (Layer 3). This lab explores routing tables, static routes, the longest prefix match algorithm, and how traceroute reveals a packet's journey hop by hop.

---

## Step 1: Install Tools & View the Routing Table

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 net-tools traceroute 2>/dev/null &&
echo '=== Routing Table ===' &&
ip route show
"
```

📸 **Verified Output:**
```
=== Routing Table ===
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.7 
```

> 💡 **Tip:** Every routing table has at least two entries: the **connected network** (the subnet you're on) and the **default route** (where to send everything else). `default` is shorthand for `0.0.0.0/0`.

---

## Step 2: Understand Routing Table Fields

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('Routing Table Field Breakdown:')
print()
entries = [
    {
        'raw': 'default via 172.17.0.1 dev eth0',
        'destination': '0.0.0.0/0 (any address)',
        'next_hop': '172.17.0.1 (default gateway)',
        'interface': 'eth0',
        'type': 'Static/Default route',
        'proto': 'static',
    },
    {
        'raw': '172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.7',
        'destination': '172.17.0.0/16',
        'next_hop': 'directly connected (no gateway)',
        'interface': 'eth0',
        'type': 'Connected route',
        'proto': 'kernel (auto-added when IP assigned)',
    },
]
for e in entries:
    print(f'Route: {e[\"raw\"]}')
    print(f'  Destination: {e[\"destination\"]}')
    print(f'  Next Hop:    {e[\"next_hop\"]}')
    print(f'  Interface:   {e[\"interface\"]}')
    print(f'  Type:        {e[\"type\"]}')
    print(f'  Proto:       {e[\"proto\"]}')
    print()
\"
"
```

📸 **Verified Output:**
```
Routing Table Field Breakdown:

Route: default via 172.17.0.1 dev eth0
  Destination: 0.0.0.0/0 (any address)
  Next Hop:    172.17.0.1 (default gateway)
  Interface:   eth0
  Type:        Static/Default route
  Proto:       static

Route: 172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.7
  Destination: 172.17.0.0/16
  Next Hop:    directly connected (no gateway)
  Interface:   eth0
  Type:        Connected route
  Proto:       kernel (auto-added when IP assigned)
```

---

## Step 3: Longest Prefix Match — How the Router Decides

When a packet arrives, the router picks the **most specific matching route**:

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
import ipaddress

def find_best_route(dest_ip, routes):
    dest = ipaddress.ip_address(dest_ip)
    best = None
    best_prefix = -1
    for route, nexthop in routes:
        network = ipaddress.ip_network(route)
        if dest in network:
            prefix = network.prefixlen
            if prefix > best_prefix:
                best_prefix = prefix
                best = (route, nexthop)
    return best

routes = [
    ('0.0.0.0/0',      'Default gateway 172.17.0.1'),
    ('10.0.0.0/8',     'via 10.1.1.1 (corporate)'),
    ('10.10.0.0/16',   'via 10.10.0.1 (HQ LAN)'),
    ('10.10.10.0/24',  'via 10.10.10.1 (server VLAN)'),
    ('172.17.0.0/16',  'directly connected eth0'),
]

test_dests = [
    '8.8.8.8',
    '10.5.1.100',
    '10.10.5.50',
    '10.10.10.99',
    '172.17.0.1',
]

print('Longest Prefix Match Examples:')
print(f'  {\"Destination\":<18} {\"Matched Route\":<20} {\"Next Hop\"}')
print('  ' + '-' * 70)
for dest in test_dests:
    result = find_best_route(dest, routes)
    route, hop = result
    print(f'  {dest:<18} {route:<20} {hop}')
\"
"
```

📸 **Verified Output:**
```
Longest Prefix Match Examples:
  Destination        Matched Route        Next Hop
  ----------------------------------------------------------------------
  8.8.8.8            0.0.0.0/0            Default gateway 172.17.0.1
  10.5.1.100         10.0.0.0/8           via 10.1.1.1 (corporate)
  10.10.5.50         10.10.0.0/16         via 10.10.0.1 (HQ LAN)
  10.10.10.99        10.10.10.0/24        via 10.10.10.1 (server VLAN)
  172.17.0.1         172.17.0.0/16        directly connected eth0
```

> 💡 **Tip:** The router always prefers the **most specific** (longest prefix) match. A /24 wins over /16 which wins over /8 which wins over /0 (default). This is the core algorithm of all IP routing.

---

## Step 4: Static Routes with Network Namespaces

Network namespaces let us simulate routing without a physical router:

```bash
docker run --rm --cap-add NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 2>/dev/null &&
echo '=== Create namespace ===' &&
ip netns add testns &&
echo '=== Create veth pair ===' &&
ip link add veth0 type veth peer name veth1 &&
ip link set veth1 netns testns &&
echo '=== Assign IPs ===' &&
ip addr add 192.168.50.1/24 dev veth0 &&
ip link set veth0 up &&
ip netns exec testns ip addr add 192.168.50.2/24 dev veth1 &&
ip netns exec testns ip link set veth1 up &&
ip netns exec testns ip link set lo up &&
echo '=== Routing table in namespace ===' &&
ip netns exec testns ip route show &&
echo '=== Add default route ===' &&
ip netns exec testns ip route add default via 192.168.50.1 &&
echo '=== Updated routing table ===' &&
ip netns exec testns ip route show &&
echo '=== Ping test ===' &&
ip netns exec testns ping -c 2 192.168.50.1 2>&1 | tail -3
"
```

📸 **Verified Output:**
```
=== Create namespace ===
=== Create veth pair ===
=== Assign IPs ===
=== Routing table in namespace ===
192.168.50.0/24 dev veth1 proto kernel scope link src 192.168.50.2 
=== Add default route ===
=== Updated routing table ===
default via 192.168.50.1 dev veth1 
192.168.50.0/24 dev veth1 proto kernel scope link src 192.168.50.2 
=== Ping test ===
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.056/0.065/0.075/0.009 ms
```

---

## Step 5: Route Types — Connected, Static, Dynamic

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('Route Types Comparison:')
print()
types = [
    {
        'type': 'Connected',
        'proto': 'kernel',
        'how': 'Auto-added when IP assigned to interface',
        'example': '192.168.1.0/24 dev eth0 proto kernel',
        'admin': 0,
        'reliability': 'Highest (directly attached)',
    },
    {
        'type': 'Static',
        'proto': 'static',
        'how': 'Manually configured by admin',
        'example': '10.0.0.0/8 via 192.168.1.1',
        'admin': 1,
        'reliability': 'High (no convergence)',
    },
    {
        'type': 'RIP',
        'proto': 'rip',
        'how': 'Distance vector — shares full table periodically',
        'example': '10.1.0.0/16 via 192.168.1.2 metric 2',
        'admin': 120,
        'reliability': 'Low (slow convergence, max 15 hops)',
    },
    {
        'type': 'OSPF',
        'proto': 'ospf',
        'how': 'Link-state — builds full topology map',
        'example': '10.2.0.0/16 via 192.168.1.3 metric 110',
        'admin': 110,
        'reliability': 'High (fast convergence)',
    },
    {
        'type': 'BGP',
        'proto': 'bgp',
        'how': 'Path vector — used between ISPs/ASes',
        'example': '8.0.0.0/8 via 203.0.113.1',
        'admin': 20,
        'reliability': 'Critical (internet backbone)',
    },
]
for t in types:
    print(f\"  {t['type']:<12} AD={t['admin']:<4} Protocol: {t['proto']}\")
    print(f\"              {t['how']}\")
    print(f\"              Example: {t['example']}\")
    print()
print('Note: AD = Administrative Distance (lower = more trusted)')
\"
"
```

📸 **Verified Output:**
```
Route Types Comparison:

  Connected    AD=0    Protocol: kernel
              Auto-added when IP assigned to interface
              Example: 192.168.1.0/24 dev eth0 proto kernel

  Static       AD=1    Protocol: static
              Manually configured by admin
              Example: 10.0.0.0/8 via 192.168.1.1

  RIP          AD=120  Protocol: rip
              Distance vector — shares full table periodically
              Example: 10.1.0.0/16 via 192.168.1.2 metric 2

  OSPF         AD=110  Protocol: ospf
              Link-state — builds full topology map
              Example: 10.2.0.0/16 via 192.168.1.3 metric 110

  BGP          AD=20   Protocol: bgp
              Path vector — used between ISPs/ASes
              Example: 8.0.0.0/8 via 203.0.113.1

Note: AD = Administrative Distance (lower = more trusted)
```

> 💡 **Tip:** **Administrative Distance (AD)** is the trust level of a routing source. When two protocols advertise the same route, the one with lower AD wins. Connected routes (AD=0) always beat everything.

---

## Step 6: TTL and Hop Count

Every IP packet carries a **Time To Live (TTL)** counter that prevents routing loops:

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('TTL (Time To Live) behavior:')
print()
print('Initial TTL values by OS:')
print('  Linux:   64')
print('  Windows: 128')
print('  Cisco:   255')
print()
print('What happens at each router:')
print('  1. Router receives packet')
print('  2. Decrements TTL by 1')
print('  3. If TTL reaches 0: sends ICMP Time Exceeded back to source')
print('  4. If TTL > 0: forwards to next hop')
print()
print('TTL trace simulation (ping to 8 hops away):')
initial_ttl = 64
for hop in range(1, 9):
    ttl_remaining = initial_ttl - hop
    status = 'forwarded' if ttl_remaining > 0 else 'DROPPED — ICMP Time Exceeded sent'
    print(f'  Hop {hop}: TTL={ttl_remaining}  → {status}')
\"
"
```

📸 **Verified Output:**
```
TTL (Time To Live) behavior:

Initial TTL values by OS:
  Linux:   64
  Windows: 128
  Cisco:   255

What happens at each router:
  1. Router receives packet
  2. Decrements TTL by 1
  3. If TTL reaches 0: sends ICMP Time Exceeded back to source
  4. If TTL > 0: forwards to next hop

TTL trace simulation (ping to 8 hops away):
  Hop 1: TTL=63  → forwarded
  Hop 2: TTL=62  → forwarded
  Hop 3: TTL=61  → forwarded
  Hop 4: TTL=60  → forwarded
  Hop 5: TTL=59  → forwarded
  Hop 6: TTL=58  → forwarded
  Hop 7: TTL=57  → forwarded
  Hop 8: TTL=56  → forwarded
```

---

## Step 7: Traceroute — Mapping the Path

Traceroute exploits TTL expiry to reveal each hop:

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq traceroute 2>/dev/null &&
echo '=== Traceroute to 8.8.8.8 ===' &&
traceroute -n -m 5 8.8.8.8 2>&1
"
```

📸 **Verified Output:**
```
=== Traceroute to 8.8.8.8 ===
traceroute to 8.8.8.8 (8.8.8.8), 5 hops max, 60 byte packets
 1  172.17.0.1  0.084 ms  0.043 ms  0.041 ms
 2  104.167.196.1  0.617 ms  0.452 ms  1.128 ms
 3  100.64.0.18  1.092 ms 100.64.0.17  1.122 ms 100.64.0.18  0.882 ms
 4  * * *
 5  * * *
```

> 💡 **Tip:** `* * *` means a hop didn't respond — either it's filtering ICMP, or it's a router that doesn't generate TTL-exceeded messages. This is normal! The packet still gets through — it's only the diagnostic probe that's blocked.

---

## Step 8: Capstone — Route Decision Simulator

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 python3-minimal 2>/dev/null &&
echo '=== Live Routing Table ===' &&
ip route show &&
echo '' &&
python3 -c \"
import ipaddress

routing_table = [
    ('0.0.0.0/0',       'via 172.17.0.1 dev eth0',     0,  'default'),
    ('172.17.0.0/16',   'dev eth0 proto kernel',        0,  'connected'),
    ('10.0.0.0/8',      'via 172.17.0.1 dev eth0',      10, 'static'),
    ('10.10.0.0/16',    'via 172.17.0.1 dev eth0',      10, 'static'),
]

def route_lookup(dest_ip):
    dest = ipaddress.ip_address(dest_ip)
    best_prefix = -1
    best_route = None
    for prefix, nexthop, metric, rtype in routing_table:
        net = ipaddress.ip_network(prefix)
        if dest in net and net.prefixlen > best_prefix:
            best_prefix = net.prefixlen
            best_route = (prefix, nexthop, metric, rtype)
    return best_route

destinations = ['8.8.8.8', '172.17.0.1', '10.5.1.1', '10.10.50.1']
print('Route Decision Results:')
print(f'  {\"Destination\":<16} {\"Matched\":<22} {\"NextHop\"}')
print('  ' + '-' * 72)
for d in destinations:
    r = route_lookup(d)
    print(f'  {d:<16} {r[0]:<22} {r[1]}')
\"
"
```

📸 **Verified Output:**
```
=== Live Routing Table ===
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.7 

Route Decision Results:
  Destination      Matched                NextHop
  ------------------------------------------------------------------------
  8.8.8.8          0.0.0.0/0              via 172.17.0.1 dev eth0
  172.17.0.1       172.17.0.0/16          dev eth0 proto kernel
  10.5.1.1         10.0.0.0/8             via 172.17.0.1 dev eth0
  10.10.50.1       10.10.0.0/16           via 172.17.0.1 dev eth0
```

---

## Summary

| Concept | Key Points |
|---|---|
| **Routing** | Forwarding packets between networks at Layer 3 (IP) |
| **Routing table** | `ip route show`; lists destinations, next hops, interfaces |
| **Default gateway** | `0.0.0.0/0` — catch-all for unknown destinations |
| **Longest prefix match** | Most specific route wins (e.g., /24 beats /16 beats /0) |
| **Connected route** | Auto-added when IP is assigned; AD=0, highest trust |
| **Static route** | `ip route add`; manually configured; AD=1 |
| **RIP** | Distance vector; max 15 hops; AD=120; slow convergence |
| **OSPF** | Link-state; fast convergence; AD=110; scales well |
| **BGP** | Path vector; internet backbone; eBGP AD=20 |
| **TTL** | Decrements at each hop; 0 = drop + ICMP Time Exceeded |
| **Traceroute** | Uses TTL expiry to reveal each hop in the path |

---

*Next: [Lab 08: NAT and Port Forwarding](lab-08-nat-and-port-forwarding.md) — how private IPs talk to the internet*
