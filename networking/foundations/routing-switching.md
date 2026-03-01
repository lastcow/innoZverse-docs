# Routing & Switching

## Switching (Layer 2)

Switches forward frames based on **MAC addresses** within a local network.

```bash
# View MAC address table on Linux
ip neigh show          # ARP cache (IP → MAC mappings)
arp -a                 # Alternative

# Get your MAC address
ip link show eth0
```

## Routing (Layer 3)

Routers forward packets based on **IP addresses** between networks.

```bash
# View routing table
ip route show
# default via 192.168.1.1 dev eth0   ← Default gateway
# 192.168.1.0/24 dev eth0            ← Local network

# Add a static route
ip route add 10.0.0.0/8 via 192.168.1.1

# Trace the path to a destination
traceroute google.com
tracepath google.com    # Alternative, no root required
```

## Routing Protocols

| Protocol | Type | Use Case |
|----------|------|----------|
| **OSPF** | Link-state | Enterprise internal routing |
| **BGP** | Path-vector | Internet routing (ISPs) |
| **EIGRP** | Hybrid | Cisco networks |
| **RIP** | Distance-vector | Small networks (legacy) |

## VLANs (Virtual LANs)

VLANs segment a physical network into logical networks:

```bash
# Create VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ip addr add 192.168.100.1/24 dev eth0.100
ip link set eth0.100 up
```
