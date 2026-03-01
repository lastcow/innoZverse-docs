# Network Security

## Defense in Depth

Layered security approach — multiple controls protect against different attack vectors.

```
Internet
    ↓
[Firewall / WAF]          ← Block malicious traffic
    ↓
[DMZ - Public services]   ← Web servers, load balancers
    ↓
[Internal Firewall]       ← Separate internal network
    ↓
[Internal Network]        ← Databases, internal services
    ↓
[Endpoint Security]       ← AV, EDR on each host
```

## Network Monitoring Tools

```bash
# Packet capture
tcpdump -i eth0                          # All traffic
tcpdump -i eth0 port 80                  # HTTP only
tcpdump -i eth0 host 192.168.1.100      # Specific host
tcpdump -i eth0 -w capture.pcap         # Save to file
wireshark capture.pcap                   # Analyze in GUI

# Network scanning
nmap -sV -sC 192.168.1.0/24            # Full scan
nmap --script vuln 192.168.1.100        # Vulnerability scan

# Bandwidth monitoring
iftop                                    # Real-time bandwidth
nethogs                                  # Per-process bandwidth
```

## VPN Setup (WireGuard)

```bash
# Install WireGuard
sudo apt install wireguard

# Generate keys
wg genkey | tee private.key | wg pubkey > public.key

# Server config (/etc/wireguard/wg0.conf)
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server-private-key>

[Peer]
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.2/32

# Start VPN
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0
```

## Intrusion Detection (Snort/Suricata)

```bash
# Install Suricata
sudo apt install suricata

# Run in IDS mode
sudo suricata -c /etc/suricata/suricata.yaml -i eth0

# View alerts
tail -f /var/log/suricata/fast.log
```
