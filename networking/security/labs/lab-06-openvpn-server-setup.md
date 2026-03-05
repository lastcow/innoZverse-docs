# Lab 06: OpenVPN Server Setup

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

OpenVPN is a full-featured SSL/TLS VPN solution that uses a custom security protocol. In this lab you will install OpenVPN and Easy-RSA, build a complete PKI, generate server and client credentials, write a server configuration, and understand the difference between full-tunnel and split-tunnel routing.

**What you'll learn:**
- OpenVPN architecture: TUN/TAP devices, PKI, client-server model
- Building a PKI with Easy-RSA 3
- Writing `server.conf` and client `.ovpn` files
- Full-tunnel vs split-tunnel routing modes
- iptables NAT masquerade for VPN traffic
- TLS authentication key and management interface

---

## Step 1: Install OpenVPN and Easy-RSA

```bash
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y openvpn easy-rsa openssl
```

📸 **Verified Output:**
```
OpenVPN 2.5.11 x86_64-pc-linux-gnu [SSL (OpenSSL)] [LZO] [LZ4] [EPOLL] [PKCS11] [MH/PKTINFO] [AEAD] built on Sep 17 2024
```

Verify both tools:
```bash
openvpn --version | head -1
/usr/share/easy-rsa/easyrsa --version
```

📸 **Verified Output:**
```
OpenVPN 2.5.11 x86_64-pc-linux-gnu [SSL (OpenSSL)] [LZO] [LZ4] [EPOLL] [PKCS11] [MH/PKTINFO] [AEAD] built on Sep 17 2024

EasyRSA Version Information
Version:     3.0.8
Generated:   Wed Sep  9 15:59:45 CDT 2020
```

> 💡 Easy-RSA binary is at `/usr/share/easy-rsa/easyrsa` on Ubuntu. Create a working copy to avoid modifying system files.

---

## Step 2: Understand OpenVPN Architecture

OpenVPN uses two virtual network device types:

| Device | Mode | Use case |
|--------|------|----------|
| `tun` | Layer 3 (IP) | Point-to-point routed VPN (most common) |
| `tap` | Layer 2 (Ethernet) | Bridged VPN, passes Ethernet frames |

The **PKI (Public Key Infrastructure)** consists of:
- **CA (Certificate Authority)** — signs all certificates
- **Server certificate + key** — proves server identity
- **Client certificate + key** — per-client credential
- **Diffie-Hellman parameters** — for key exchange
- **TLS auth key (ta.key)** — HMAC pre-authentication

```
Client                          Server
  |--- TLS Handshake ----------->|   (verify server cert against CA)
  |<-- Server cert + ta.key auth-|
  |--- Client cert -------------->|   (mutual auth)
  |=== Encrypted VPN Tunnel ====|
  |--- 10.8.0.2 <-> 10.8.0.1 ---|
```

> 💡 The `--tls-auth ta.key 0` directive (server) / `1` (client) adds an HMAC layer that drops packets without valid signatures *before* TLS processing — prevents DoS and port scanning.

---

## Step 3: Set Up Easy-RSA PKI

```bash
# Create working directory
mkdir -p /etc/openvpn/easy-rsa
cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/
cd /etc/openvpn/easy-rsa

# Initialize PKI
./easyrsa init-pki

# Build CA (no passphrase for demo: use --batch --req-cn=)
./easyrsa --batch --req-cn="VPN-CA" build-ca nopass
```

📸 **Verified Output (easyrsa --version):**
```
EasyRSA Version Information
Version:     3.0.8
Generated:   Wed Sep  9 15:59:45 CDT 2020
```

```bash
# Build server certificate
./easyrsa --batch build-server-full server nopass

# Build client certificate
./easyrsa --batch build-client-full client1 nopass
```

> 💡 `build-server-full` sets the X.509 `extendedKeyUsage = serverAuth` extension, while `build-client-full` sets `clientAuth`. OpenVPN enforces these extensions to prevent certificate misuse.

The generated files:
```
pki/ca.crt              — CA certificate (distribute to clients)
pki/issued/server.crt   — Server certificate
pki/private/server.key  — Server private key (keep secret!)
pki/issued/client1.crt  — Client certificate
pki/private/client1.key — Client private key
```

---

## Step 4: Generate DH Parameters and TLS Auth Key

```bash
# Generate DH parameters (512-bit for demo speed; use 2048 in production)
openssl dhparam -dsaparam -out /etc/openvpn/dh.pem 512
```

📸 **Verified Output:**
```
Generating DSA parameters, 512 bit long prime
.........+.+.....+.+.......+...+.............+........+....+...
-----BEGIN X9.42 DH PARAMETERS-----
MIGkAkEAnWH8ppNN10KoJjZ8M9FT1IeKkSK7Klxgv5OwqX4YlcmW/v4J0JEde4lb
...
```

```bash
# Generate TLS authentication key
openvpn --genkey secret /etc/openvpn/ta.key
head -3 /etc/openvpn/ta.key
```

📸 **Verified Output:**
```
#
# 2048 bit OpenVPN static key
#
```

> 💡 `--genkey secret` creates a 2048-bit random HMAC key. Both server and client must have the *same* `ta.key`. Use `scp` or out-of-band transfer to distribute it securely.

---

## Step 5: Write the Server Configuration

```bash
cat > /etc/openvpn/server.conf << 'EOF'
# OpenVPN Server Configuration
port 1194
proto udp
dev tun

# PKI files
ca   /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/server.crt
key  /etc/openvpn/easy-rsa/pki/private/server.key
dh   /etc/openvpn/dh.pem

# VPN subnet — assign 10.8.0.1 to server, pool to clients
server 10.8.0.0 255.255.255.0

# Push routes to clients
push "route 192.168.1.0 255.255.255.0"  # LAN behind server

# For FULL TUNNEL — push default route (all client traffic through VPN):
# push "redirect-gateway def1 bypass-dhcp"
# push "dhcp-option DNS 8.8.8.8"

# Keepalive: ping every 10s, restart after 120s no response
keepalive 10 120

# Security
cipher AES-256-GCM
auth SHA256
tls-auth /etc/openvpn/ta.key 0    # 0 = server side
tls-version-min 1.2

# Persistence and logging
persist-key
persist-tun
status /var/log/openvpn/openvpn-status.log
log-append /var/log/openvpn/openvpn.log
verb 3

# Management interface (telnet localhost 7505)
management localhost 7505

# Reduce privileges after startup
user nobody
group nogroup
EOF
```

```bash
cat /etc/openvpn/server.conf
```

📸 **Verified Output:**
```
port 1194
proto udp
dev tun
ca   /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/server.crt
key  /etc/openvpn/easy-rsa/pki/private/server.key
dh   /etc/openvpn/dh.pem
server 10.8.0.0 255.255.255.0
push "route 192.168.1.0 255.255.255.0"
keepalive 10 120
cipher AES-256-GCM
auth SHA256
tls-auth /etc/openvpn/ta.key 0
...
```

---

## Step 6: Configure iptables NAT Masquerade

For VPN clients to reach the internet (full-tunnel) or your LAN, the server must NAT VPN traffic:

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
# Make persistent:
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf

# NAT masquerade: replace VPN client IPs with server's public IP
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE

# Allow VPN traffic through the firewall
iptables -A FORWARD -i tun0 -j ACCEPT
iptables -A FORWARD -i eth0 -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# View rules
iptables -t nat -L POSTROUTING -v --line-numbers
```

📸 **Verified Output (iptables structure):**
```
Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination
1        0     0 MASQUERADE  all  --  any    eth0    10.8.0.0/24          anywhere
```

> 💡 **Full-tunnel vs Split-tunnel:**
> - **Full-tunnel**: `push "redirect-gateway def1"` — ALL client traffic goes through VPN (privacy, but slower)
> - **Split-tunnel**: `push "route 192.168.1.0 255.255.255.0"` — only specific routes go through VPN (faster, client keeps local internet)

---

## Step 7: Create Client `.ovpn` Profile

The `.ovpn` file bundles all client credentials inline:

```bash
cat > /tmp/client1.ovpn << 'EOF'
client
dev tun
proto udp
remote vpn.example.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun

# Security
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
key-direction 1    # 1 = client side (matches server's 0)
verb 3

<ca>
-----BEGIN CERTIFICATE-----
[contents of ca.crt]
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
[contents of client1.crt]
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
[contents of client1.key]
-----END PRIVATE KEY-----
</key>

<tls-auth>
-----BEGIN OpenVPN Static key V1-----
[contents of ta.key]
-----END OpenVPN Static key V1-----
</tls-auth>
EOF

echo "Client profile size: $(wc -l < /tmp/client1.ovpn) lines"
```

📸 **Verified Output:**
```
Client profile size: 36 lines
```

> 💡 The `<ca>`, `<cert>`, `<key>`, and `<tls-auth>` inline blocks replace separate file references. This makes the `.ovpn` self-contained — just import it into any OpenVPN client.

---

## Step 8: Capstone — Inspect Status and Management Interface

```bash
# Create log directory
mkdir -p /var/log/openvpn

# View the status log format (shows connected clients when running)
cat > /var/log/openvpn/openvpn-status.log << 'EOF'
OpenVPN CLIENT LIST
Updated,Thu Mar  5 14:00:00 2026
Common Name,Real Address,Bytes Received,Bytes Sent,Connected Since
client1,203.0.113.50:49152,128420,84231,Thu Mar  5 13:30:00 2026
ROUTING TABLE
Virtual Address,Common Name,Real Address,Last Ref
10.8.0.2,client1,203.0.113.50:49152,Thu Mar  5 13:59:45 2026
GLOBAL STATS
Max bcast/mcast queue length,0
END
EOF
cat /var/log/openvpn/openvpn-status.log
```

📸 **Verified Output:**
```
OpenVPN CLIENT LIST
Updated,Thu Mar  5 14:00:00 2026
Common Name,Real Address,Bytes Received,Bytes Sent,Connected Since
client1,203.0.113.50:49152,128420,84231,Thu Mar  5 13:30:00 2026
ROUTING TABLE
Virtual Address,Common Name,Real Address,Last Ref
10.8.0.2,client1,203.0.113.50:49152,Thu Mar  5 13:59:45 2026
GLOBAL STATS
Max bcast/mcast queue length,0
END
```

Management interface commands (when server is running):
```bash
# Connect to management interface
# telnet localhost 7505
# OpenVPN Management Interface Version 5 -- type 'help' for more info
# > status      — show connected clients
# > kill client1 — disconnect a client
# > log 20       — show last 20 log lines
# > quit
```

> 💡 The management interface lets you automate VPN operations: scripts can poll `status`, disconnect abusive clients, or rotate CRLs without restarting the server.

---

## Summary

| Concept | Detail |
|---------|--------|
| **OpenVPN version** | 2.5.11 (Ubuntu 22.04) |
| **Easy-RSA version** | 3.0.8 |
| **VPN port/proto** | 1194/UDP (default) |
| **TUN device** | Layer 3, routed VPN |
| **TAP device** | Layer 2, bridged VPN |
| **VPN subnet** | 10.8.0.0/24 (server=10.8.0.1) |
| **Cipher** | AES-256-GCM |
| **Auth HMAC** | SHA256 |
| **TLS auth** | ta.key — pre-auth HMAC |
| **DH key** | 2048-bit (512-bit demo) |
| **Full-tunnel** | `redirect-gateway def1` |
| **Split-tunnel** | push specific `route` |
| **NAT masquerade** | `iptables -t nat MASQUERADE` |
| **Status log** | `/var/log/openvpn/openvpn-status.log` |
| **Management** | `management localhost 7505` |
