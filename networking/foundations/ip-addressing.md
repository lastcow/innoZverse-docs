# IP Addressing & Subnetting

## IPv4 Addresses

An IPv4 address is 32 bits, written as 4 octets:
```
192.168.1.100
│   │   │ │
│   │   │ └── Host: 100
│   │   └──── Host: 1  
│   └──────── Network: 168
└──────────── Network: 192
```

## IP Address Classes

| Class | Range | Default Mask | Use |
|-------|-------|-------------|-----|
| A | 1.0.0.0 – 126.255.255.255 | /8 | Large networks |
| B | 128.0.0.0 – 191.255.255.255 | /16 | Medium networks |
| C | 192.0.0.0 – 223.255.255.255 | /24 | Small networks |

## Private IP Ranges (RFC 1918)

```
10.0.0.0/8          # 16 million addresses
172.16.0.0/12       # 1 million addresses  
192.168.0.0/16      # 65,536 addresses
```

## CIDR Notation & Subnetting

```
192.168.1.0/24
            │
            └── 24 bits = network, 8 bits = hosts
                = 256 addresses, 254 usable

/24 = 255.255.255.0    → 254 hosts
/25 = 255.255.255.128  → 126 hosts
/26 = 255.255.255.192  → 62 hosts
/27 = 255.255.255.224  → 30 hosts
/28 = 255.255.255.240  → 14 hosts
/30 = 255.255.255.252  → 2 hosts (point-to-point links)
```

## Subnet Calculation

```bash
# Install ipcalc
sudo apt install ipcalc

ipcalc 192.168.1.0/24
# Network:   192.168.1.0/24
# Broadcast: 192.168.1.255
# HostMin:   192.168.1.1
# HostMax:   192.168.1.254
# Hosts/Net: 254
```

## IPv6

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
# 128-bit, written as 8 groups of 4 hex digits
# Shortened: 2001:db8:85a3::8a2e:370:7334
```
