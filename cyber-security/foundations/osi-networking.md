# OSI Model & Networking

## The OSI Model

| Layer | Name | Protocol Examples | Data Unit |
|-------|------|-------------------|-----------|
| 7 | Application | HTTP, SMTP, DNS, FTP | Data |
| 6 | Presentation | SSL/TLS, JPEG, ASCII | Data |
| 5 | Session | NetBIOS, RPC | Data |
| 4 | Transport | TCP, UDP | Segment |
| 3 | Network | IP, ICMP, OSPF | Packet |
| 2 | Data Link | Ethernet, Wi-Fi (802.11) | Frame |
| 1 | Physical | Cables, Radio, Fiber | Bits |

## TCP vs UDP

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Yes (3-way handshake) | No |
| Reliability | Guaranteed delivery | Best-effort |
| Order | Ordered | No guarantee |
| Speed | Slower | Faster |
| Use cases | HTTP, SSH, FTP | DNS, VoIP, Gaming |

## Common Ports

| Port | Protocol | Service |
|------|----------|---------|
| 21 | TCP | FTP |
| 22 | TCP | SSH |
| 25 | TCP | SMTP |
| 53 | UDP/TCP | DNS |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |
| 3306 | TCP | MySQL |
| 3389 | TCP | RDP |
| 5432 | TCP | PostgreSQL |
| 6379 | TCP | Redis |

## Network Commands

```bash
nmap -sV 192.168.1.1            # Service version scan
nmap -p- 192.168.1.1            # All 65535 ports
nmap -sn 192.168.1.0/24        # Ping sweep
tcpdump -i eth0 port 80         # Capture HTTP traffic
wireshark                        # GUI packet capture
```
