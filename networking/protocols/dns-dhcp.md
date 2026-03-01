# DNS & DHCP

## DNS — Domain Name System

DNS translates domain names to IP addresses.

### DNS Record Types

| Type | Purpose | Example |
|------|---------|---------|
| **A** | Domain → IPv4 | `example.com → 93.184.216.34` |
| **AAAA** | Domain → IPv6 | `example.com → 2606:2800::1` |
| **CNAME** | Alias | `www → example.com` |
| **MX** | Mail server | `@ → mail.example.com` |
| **TXT** | Text info | SPF, DKIM, verification |
| **NS** | Name servers | `example.com → ns1.registrar.com` |
| **PTR** | Reverse DNS | `93.184.216.34 → example.com` |

### DNS Lookup Commands

```bash
# Basic lookup
dig example.com
dig example.com A        # IPv4 only
dig example.com MX       # Mail records
dig example.com TXT      # Text records
dig @8.8.8.8 example.com # Use specific DNS server

# Reverse lookup
dig -x 8.8.8.8

# Trace DNS resolution
dig +trace example.com

# Quick tools
nslookup example.com
host example.com
```

### DNS Resolution Process

```
Browser → Local Cache → /etc/hosts → Resolver → Root → TLD → Authoritative
```

```bash
# View /etc/hosts
cat /etc/hosts

# Current DNS servers
cat /etc/resolv.conf

# Flush DNS cache (systemd)
sudo systemd-resolve --flush-caches
```

## DHCP — Dynamic Host Configuration Protocol

DHCP automatically assigns IP addresses to devices.

### DORA Process
```
Client      DHCP Server
  │── Discover ──→│    "Anyone have an IP for me?"
  │←── Offer ─────│    "I'll offer 192.168.1.50"
  │── Request ───→│    "I'll take 192.168.1.50"
  │←── Acknowledge│    "It's yours for 24 hours"
```

```bash
# Request new IP
sudo dhclient eth0

# View DHCP lease
cat /var/lib/dhcp/dhclient.leases

# Release IP
sudo dhclient -r eth0
```
