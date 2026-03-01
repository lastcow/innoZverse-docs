# Network Fundamentals

Understanding how networks work is the foundation of cybersecurity.

## The OSI Model

| Layer | Name | Examples |
|-------|------|---------|
| 7 | Application | HTTP, SMTP, DNS |
| 6 | Presentation | SSL/TLS, JPEG |
| 5 | Session | NetBIOS, RPC |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, ICMP |
| 2 | Data Link | Ethernet, Wi-Fi |
| 1 | Physical | Cables, Radio |

## Key Protocols

### TCP vs UDP
- **TCP** — Reliable, ordered, connection-based (HTTP, SSH, FTP)
- **UDP** — Fast, connectionless, no guarantee (DNS, VoIP, Gaming)

### Common Ports
| Port | Protocol | Service |
|------|----------|---------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |
| 53 | UDP | DNS |
| 3306 | TCP | MySQL |
| 3389 | TCP | RDP |

## Basic Network Commands

```bash
nmap -sV 192.168.1.1        # Scan host, detect versions
nmap -p 1-1000 192.168.1.0/24  # Scan port range on subnet
tcpdump -i eth0              # Capture packets
netstat -tlnp                # Show open ports
traceroute google.com        # Trace network path
```

## Subnetting Basics

```
IP: 192.168.1.100
Subnet: /24 = 255.255.255.0
Network: 192.168.1.0
Broadcast: 192.168.1.255
Hosts: 192.168.1.1 - 192.168.1.254
```

---
*Next: [Ethical Hacking Basics →](ethical-hacking-basics.md)*
