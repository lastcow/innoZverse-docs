# Networking Fundamentals

## Network Configuration

```bash
ip addr show                    # Show all interfaces and IPs
ip addr show eth0               # Show specific interface
ip route show                   # Show routing table
ip link set eth0 up             # Bring interface up
```

## DNS & Connectivity

```bash
ping google.com                 # Test basic connectivity
ping -c 4 8.8.8.8              # Ping 4 times
traceroute google.com           # Trace route to host
dig google.com                  # DNS lookup
nslookup google.com             # Alternative DNS lookup
host google.com                 # Simple DNS query
curl ifconfig.me                # Get your public IP
```

## Ports & Connections

```bash
ss -tlnp                        # TCP listening ports with process
ss -ulnp                        # UDP listening ports
netstat -tlnp                   # Alternative (older)
lsof -i :80                     # What's using port 80?
lsof -i :443                    # What's using port 443?
```

## Network Scanning (Nmap)

```bash
nmap 192.168.1.1                # Basic scan
nmap -sV 192.168.1.1            # Detect service versions
nmap -p 22,80,443 192.168.1.1  # Specific ports
nmap -sn 192.168.1.0/24        # Ping sweep (no port scan)
```

## Downloading & Transferring

```bash
wget https://example.com/file.zip           # Download file
curl -O https://example.com/file.zip        # Download with curl
scp file.txt alice@192.168.1.100:/tmp/      # Secure copy to remote
rsync -avz /local/ user@server:/remote/     # Sync directories
```
