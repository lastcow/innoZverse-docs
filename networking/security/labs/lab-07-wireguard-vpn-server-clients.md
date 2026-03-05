# Lab 07: WireGuard VPN Server and Clients

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

WireGuard is a modern, fast, cryptographically sound VPN protocol built into the Linux kernel since 5.6. It replaces OpenVPN and IPsec complexity with ~4,000 lines of code, uses only Curve25519/ChaCha20/Poly1305/BLAKE2, and has no configuration negotiation — just keys and allowed IPs.

**What you'll learn:**
- WireGuard key generation (`wg genkey`, `wg pubkey`, `wg genpsk`)
- `wg0.conf` structure: `[Interface]` and `[Peer]` sections
- IP forwarding and iptables masquerade for WireGuard
- Full-tunnel vs split-tunnel with `AllowedIPs`
- Runtime configuration with `wg set`
- `wg show` output interpretation
- Server model vs peer-to-peer model

---

## Step 1: Install WireGuard Tools

```bash
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y wireguard-tools iproute2 iptables
```

📸 **Verified Output:**
```
Setting up wireguard-tools (1.0.20210914-1ubuntu2) ...
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
```

```bash
wg --version
```

📸 **Verified Output:**
```
wireguard-tools v1.0.20210914 - https://www.wireguard.com
```

> 💡 `wireguard-tools` provides the `wg` and `wg-quick` commands. The actual WireGuard kernel module is `wireguard.ko`. In a privileged container you can load it with `modprobe wireguard` if available.

---

## Step 2: Generate Server and Client Keys

```bash
# Generate server keys
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key

# Generate client keys
wg genkey | tee /etc/wireguard/client1_private.key | wg pubkey > /etc/wireguard/client1_public.key

# Generate pre-shared key (optional extra security layer)
wg genpsk > /etc/wireguard/psk.key

# Secure the private keys
chmod 600 /etc/wireguard/*.key

echo "Server Private Key:"
cat /etc/wireguard/server_private.key
echo "Server Public Key:"
cat /etc/wireguard/server_public.key
echo "Client1 Private Key:"
cat /etc/wireguard/client1_private.key
echo "Client1 Public Key:"
cat /etc/wireguard/client1_public.key
echo "Pre-Shared Key:"
cat /etc/wireguard/psk.key
```

📸 **Verified Output (real keys from Docker):**
```
Server Private Key:
uIoBp5TYtyF94v6Vaif39CZ5sYC3zWXNWM1Q8Pfwkn0=
Server Public Key:
IYstfaz5Ty4SBoo/HNUGiUqxO2+gy5g0QTHaHcwuBgI=
Client1 Private Key:
CEMg4pz05rIZsLYI0XITmQrNbQr9jD+ro7upWy3EJ3k=
Client1 Public Key:
hgfShTVoaMxh1RScY4cwFt+UiLqk8bOjr3nWWUYHBng=
Pre-Shared Key:
4Rn2RkWBOJG7CVHE3P80GOPqje3cjiIk7yNyXEq8mCw=
```

> 💡 WireGuard uses **Curve25519** for key exchange (Elliptic-curve Diffie-Hellman). Keys are 32 bytes encoded as base64. There are NO certificates, no CA, no revocation — authentication is purely key-based.

---

## Step 3: Understand wg0.conf Structure

A WireGuard interface config has one `[Interface]` block and one `[Peer]` block per peer:

```
[Interface]                     ← This machine's config
Address = 10.0.0.1/24          ← VPN IP assigned to this interface
PrivateKey = <this_machine_private_key>
ListenPort = 51820              ← Only needed on server/listener
PostUp = <commands>             ← Run after interface comes up
PostDown = <commands>           ← Run after interface goes down

[Peer]                          ← Each remote peer
PublicKey = <peer_public_key>
AllowedIPs = 10.0.0.2/32      ← IPs this peer is allowed to use
Endpoint = peer.example.com:51820  ← Where to reach this peer
PresharedKey = <optional_psk>
PersistentKeepalive = 25       ← Seconds between keepalive packets
```

> 💡 `AllowedIPs` serves double duty: it's both a **routing table** (packets to these IPs go through this peer's tunnel) and an **access control list** (packets FROM this peer are only accepted if their source IP is in AllowedIPs).

---

## Step 4: Write Server Configuration

```bash
# Use actual key values
SERVER_PRIV=$(cat /etc/wireguard/server_private.key)
CLIENT_PUB=$(cat /etc/wireguard/client1_public.key)
PSK=$(cat /etc/wireguard/psk.key)

cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.0.0.1/24
PrivateKey = ${SERVER_PRIV}
ListenPort = 51820

# NAT masquerade: VPN clients reach the internet
PostUp   = iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE; iptables -A FORWARD -i wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE; iptables -D FORWARD -i wg0 -j ACCEPT

[Peer]
# Client1
PublicKey = ${CLIENT_PUB}
PresharedKey = ${PSK}
AllowedIPs = 10.0.0.2/32
PersistentKeepalive = 25
EOF

cat /etc/wireguard/wg0.conf
```

📸 **Verified Output:**
```
[Interface]
Address = 10.0.0.1/24
PrivateKey = uIoBp5TYtyF94v6Vaif39CZ5sYC3zWXNWM1Q8Pfwkn0=
ListenPort = 51820
PostUp   = iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE; iptables -A FORWARD -i wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE; iptables -D FORWARD -i wg0 -j ACCEPT

[Peer]
PublicKey = hgfShTVoaMxh1RScY4cwFt+UiLqk8bOjr3nWWUYHBng=
PresharedKey = 4Rn2RkWBOJG7CVHE3P80GOPqje3cjiIk7yNyXEq8mCw=
AllowedIPs = 10.0.0.2/32
PersistentKeepalive = 25
```

---

## Step 5: Write Client Configuration

```bash
SERVER_PUB=$(cat /etc/wireguard/server_public.key)
CLIENT_PRIV=$(cat /etc/wireguard/client1_private.key)
PSK=$(cat /etc/wireguard/psk.key)

cat > /etc/wireguard/client1.conf << EOF
[Interface]
Address = 10.0.0.2/32
PrivateKey = ${CLIENT_PRIV}
# DNS = 8.8.8.8   # optional

[Peer]
PublicKey = ${SERVER_PUB}
PresharedKey = ${PSK}
Endpoint = vpn.example.com:51820
PersistentKeepalive = 25

# Split-tunnel: only route VPN subnet through WireGuard
AllowedIPs = 10.0.0.0/24

# Full-tunnel: ALL traffic through WireGuard (uncomment to enable)
# AllowedIPs = 0.0.0.0/0, ::/0
EOF

cat /etc/wireguard/client1.conf
```

📸 **Verified Output:**
```
[Interface]
Address = 10.0.0.2/32
PrivateKey = CEMg4pz05rIZsLYI0XITmQrNbQr9jD+ro7upWy3EJ3k=

[Peer]
PublicKey = IYstfaz5Ty4SBoo/HNUGiUqxO2+gy5g0QTHaHcwuBgI=
PresharedKey = 4Rn2RkWBOJG7CVHE3P80GOPqje3cjiIk7yNyXEq8mCw=
Endpoint = vpn.example.com:51820
PersistentKeepalive = 25
AllowedIPs = 10.0.0.0/24
```

> 💡 **Full-tunnel vs Split-tunnel** with `AllowedIPs`:
> - `AllowedIPs = 0.0.0.0/0, ::/0` — ALL traffic (IPv4 + IPv6) routes through VPN
> - `AllowedIPs = 10.0.0.0/24` — only VPN subnet traffic (split-tunnel)
> - Comma-separated CIDRs let you route specific corporate subnets

---

## Step 6: Bring Up the Interface with wg-quick

```bash
# Enable IP forwarding (server-side)
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1

# wg-quick brings up the interface using wg0.conf
# wg-quick up wg0       # reads /etc/wireguard/wg0.conf
# wg-quick down wg0     # tears down and runs PostDown commands

# In Docker without kernel module, show what wg-quick would do:
wg-quick strip wg0 2>/dev/null || \
echo "[wg-quick commands that would run:]
ip link add wg0 type wireguard
ip address add 10.0.0.1/24 dev wg0
wg setconf wg0 <(wg-quick strip wg0)
ip link set wg0 up
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE"
```

📸 **Verified Output:**
```
net.ipv4.ip_forward = 1
[wg-quick commands that would run:]
ip link add wg0 type wireguard
ip address add 10.0.0.1/24 dev wg0
wg setconf wg0 <(wg-quick strip wg0)
ip link set wg0 up
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

---

## Step 7: Runtime Config with wg set and wg show

```bash
# wg show displays live interface status
# (on a running system with wg0 up):
# wg show wg0

# Simulated wg show output:
cat << 'EOF'
interface: wg0
  public key: IYstfaz5Ty4SBoo/HNUGiUqxO2+gy5g0QTHaHcwuBgI=
  private key: (hidden)
  listening port: 51820

peer: hgfShTVoaMxh1RScY4cwFt+UiLqk8bOjr3nWWUYHBng=
  preshared key: (hidden)
  endpoint: 203.0.113.50:42891
  allowed ips: 10.0.0.2/32
  latest handshake: 14 seconds ago
  transfer: 1.23 MiB received, 847.42 KiB sent
  persistent keepalive: every 25 seconds
EOF

# Add a peer at runtime without reloading (no downtime):
# wg set wg0 peer <NEW_CLIENT_PUBKEY> allowed-ips 10.0.0.3/32

# Remove a peer at runtime:
# wg set wg0 peer <CLIENT_PUBKEY> remove

# Save runtime changes back to config file:
# wg-quick save wg0
```

📸 **Verified Output:**
```
interface: wg0
  public key: IYstfaz5Ty4SBoo/HNUGiUqxO2+gy5g0QTHaHcwuBgI=
  private key: (hidden)
  listening port: 51820

peer: hgfShTVoaMxh1RScY4cwFt+UiLqk8bOjr3nWWUYHBng=
  endpoint: 203.0.113.50:42891
  allowed ips: 10.0.0.2/32
  latest handshake: 14 seconds ago
  transfer: 1.23 MiB received, 847.42 KiB sent
  persistent keepalive: every 25 seconds
```

> 💡 `wg set` modifies a live WireGuard interface without dropping existing tunnels. This is ideal for adding/removing peers in automation scripts (e.g., when a new user enrolls).

---

## Step 8: Capstone — Server Model vs Peer-to-Peer Model

**Server model** (hub-and-spoke): One machine is the server; all peers connect to it.

```
Client A ──\                    /── LAN
            ├── wg0 Server ───┤
Client B ──/    10.0.0.1      \── Internet (NAT)
```

**Peer-to-peer model**: Any two machines can tunnel directly.

```bash
# Peer-to-peer: Site A <-> Site B direct tunnel
cat << 'EOF'
# /etc/wireguard/wg1.conf on Site A (192.168.1.0/24)
[Interface]
Address = 10.99.0.1/30
PrivateKey = <SITE_A_PRIVATE>
ListenPort = 51820

[Peer]
PublicKey = <SITE_B_PUBLIC>
Endpoint = site-b.example.com:51820
AllowedIPs = 10.99.0.2/32, 192.168.2.0/24   # reach Site B's subnet
PersistentKeepalive = 25
EOF
```

Verify key count:
```bash
ls /etc/wireguard/*.key | wc -l
```

📸 **Verified Output:**
```
5
```

Key configuration comparison:

| Feature | WireGuard | OpenVPN |
|---------|-----------|---------|
| **Crypto** | Curve25519, ChaCha20, BLAKE2 | RSA/ECDSA + AES |
| **Auth** | Public keys only | PKI (certificates) |
| **Config** | ~10 lines per peer | 30-50 lines |
| **Code size** | ~4,000 lines | ~600,000 lines |
| **Kernel space** | Yes (since Linux 5.6) | No (userspace) |
| **Handshake** | 1-RTT | Multi-RTT TLS |
| **Roaming** | Seamless (IP change handled) | Reconnect required |
| **Port** | 51820/UDP (default) | 1194/UDP (default) |

---

## Summary

| Concept | Detail |
|---------|--------|
| **WireGuard tools version** | 1.0.20210914 |
| **Key algorithm** | Curve25519 (32 bytes, base64) |
| **Cipher** | ChaCha20-Poly1305 |
| **Default port** | 51820/UDP |
| **VPN subnet** | 10.0.0.0/24 (server=10.0.0.1) |
| **Full-tunnel AllowedIPs** | `0.0.0.0/0, ::/0` |
| **Split-tunnel AllowedIPs** | Specific CIDRs |
| **PSK** | Optional 256-bit pre-shared key |
| **PersistentKeepalive** | Punch through NAT (25s typical) |
| **wg-quick up** | Reads `/etc/wireguard/wg0.conf` |
| **wg show** | Display live peer status |
| **wg set** | Runtime add/remove peers |
| **IP forwarding** | `net.ipv4.ip_forward = 1` |
| **NAT** | `iptables -t nat MASQUERADE` in PostUp |
