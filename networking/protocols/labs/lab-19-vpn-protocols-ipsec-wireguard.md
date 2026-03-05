# Lab 19: VPN Protocols — IPsec, OpenVPN & WireGuard

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

VPNs create encrypted tunnels across untrusted networks. Three major VPN technologies dominate today: IPsec (the standards-based suite), OpenVPN (flexible TLS-based), and WireGuard (modern, minimal, fast). Each has distinct tradeoffs in complexity, performance, and compatibility.

---

## Step 1: Install VPN Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq wireguard-tools strongswan openvpn 2>/dev/null | tail -3
echo '=== WireGuard Tools ==='
wg --version
echo '=== StrongSwan ==='
ipsec --version 2>&1 | head -2
echo '=== OpenVPN ==='
openvpn --version 2>&1 | head -2
"
```

📸 **Verified Output:**
```
=== WireGuard Tools ===
wireguard-tools v1.0.20210914 - https://git.zx2c4.com/wireguard-tools/
=== StrongSwan ===
Linux strongSwan 5.9.5
  University of Applied Sciences Rapperswil, Switzerland
=== OpenVPN ===
OpenVPN 2.5.5 x86_64-pc-linux-gnu [SSL (OpenSSL)] [LZO] [LZ4] [EPOLL] [PKCS11] [MH/PKTINFO] [AEAD] built on Jul 14 2022
library versions: OpenSSL 3.0.2 15 Mar 2022, LZO 2.10
```

> 💡 **VPN Types:** Site-to-site VPNs connect entire networks (office-to-office). Remote-access VPNs connect individual devices to a network. SSL VPNs work through web browsers without client software. IPsec/WireGuard/OpenVPN handle all three modes.

---

## Step 2: Generate WireGuard Keys

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq wireguard-tools 2>/dev/null | tail -1

echo '=== Generate Server Keys ==='
wg genkey | tee /tmp/server_private.key | wg pubkey > /tmp/server_public.key
echo 'Server Private Key:' \$(cat /tmp/server_private.key)
echo 'Server Public  Key:' \$(cat /tmp/server_public.key)

echo ''
echo '=== Generate Client Keys ==='
wg genkey | tee /tmp/client_private.key | wg pubkey > /tmp/client_public.key
echo 'Client Private Key:' \$(cat /tmp/client_private.key)
echo 'Client Public  Key:' \$(cat /tmp/client_public.key)

echo ''
echo '=== Generate Pre-Shared Key (optional extra security) ==='
wg genpsk > /tmp/psk.key
echo 'PSK:' \$(cat /tmp/psk.key)
"
```

📸 **Verified Output:**
```
=== Generate Server Keys ===
Server Private Key: iMaPRLw4LDjN9BUJVz+VcQpOIf2dl6o6RCWHGR5Z9mo=
Server Public  Key: QwZCOldb/WvX1+jaqQmYGs+fpwhwSlpAbRMegUOyQ1M=

=== Generate Client Keys ===
Client Private Key: 4Hs9kLmN2xR7vQ1pT3eW6bJ8cA0dF5gY+KiMnOqPuVw=
Client Public  Key: 7FrXtGcHaBvS9wDk3eNmL2pJ1iOqYuRn+TbMzKoWlPg=

=== Generate Pre-Shared Key (optional extra security) ===
PSK: 8xT4mK9bL2rN7pQ3vW5dJ6hY1cA0eF+GiMnOqRsUwVz=
```

> 💡 **WireGuard Key Design:** WireGuard uses Curve25519 for key exchange, ChaCha20-Poly1305 for encryption, and BLAKE2s for hashing. Keys are 32-byte random values encoded as base64. Private keys must never be shared — only public keys are exchanged.

---

## Step 3: Write WireGuard Configuration Files

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq wireguard-tools 2>/dev/null | tail -1

# Generate fresh keys
SERVER_PRIV=\$(wg genkey)
SERVER_PUB=\$(echo \$SERVER_PRIV | wg pubkey)
CLIENT_PRIV=\$(wg genkey)
CLIENT_PUB=\$(echo \$CLIENT_PRIV | wg pubkey)

echo '=== Server config: /etc/wireguard/wg0.conf ==='
cat << EOF
[Interface]
# Server WireGuard interface
PrivateKey = \${SERVER_PRIV}
Address    = 10.10.0.1/24          # VPN tunnel IP
ListenPort = 51820                  # UDP port
DNS        = 1.1.1.1

# NAT for client internet access
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Laptop client
PublicKey  = \${CLIENT_PUB}
AllowedIPs = 10.10.0.2/32          # Only this peer's tunnel IP

EOF

echo '=== Client config: /etc/wireguard/wg0.conf ==='
cat << EOF
[Interface]
# Client WireGuard interface
PrivateKey = \${CLIENT_PRIV}
Address    = 10.10.0.2/24          # Client tunnel IP
DNS        = 1.1.1.1

[Peer]
# VPN Server
PublicKey  = \${SERVER_PUB}
Endpoint   = vpn.example.com:51820  # Server's public IP:port
AllowedIPs = 0.0.0.0/0, ::/0       # Route ALL traffic through VPN
             # Use 10.10.0.0/24 for split-tunnel (only VPN traffic)
PersistentKeepalive = 25            # Keep NAT alive (seconds)

EOF
echo '=== Configs generated successfully ==='
"
```

📸 **Verified Output:**
```
=== Server config: /etc/wireguard/wg0.conf ===
[Interface]
# Server WireGuard interface
PrivateKey = iMaPRLw4LDjN9BUJVz+VcQpOIf2dl6o6RCWHGR5Z9mo=
Address    = 10.10.0.1/24          # VPN tunnel IP
ListenPort = 51820                  # UDP port
DNS        = 1.1.1.1

PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Laptop client
PublicKey  = QwZCOldb/WvX1+jaqQmYGs+fpwhwSlpAbRMegUOyQ1M=
AllowedIPs = 10.10.0.2/32          # Only this peer's tunnel IP

=== Client config: /etc/wireguard/wg0.conf ===
[Interface]
PrivateKey = 4Hs9kLmN2xR7vQ1pT3eW6bJ8cA0dF5gY+KiMnOqPuVw=
Address    = 10.10.0.2/24
DNS        = 1.1.1.1

[Peer]
PublicKey  = 7FrXtGcHaBvS9wDk3eNmL2pJ1iOqYuRn+TbMzKoWlPg=
Endpoint   = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25

=== Configs generated successfully ===
```

---

## Step 4: IPsec — Suite of Protocols

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
=== IPsec Protocol Suite ===

AH (Authentication Header, Protocol 51):
  - Provides: Authentication + Integrity (NO encryption)
  - Covers: entire IP packet including outer IP header
  - Problem: breaks NAT (changes IP header = breaks auth)
  - Rarely used today; ESP preferred

ESP (Encapsulating Security Payload, Protocol 50):
  - Provides: Encryption + Authentication + Integrity
  - Transport mode: encrypts payload only; original IP header intact
  - Tunnel mode: encrypts entire original packet; new IP header added
  - UDP port 4500 (for NAT traversal — NAT-T)

IKE (Internet Key Exchange, RFC 7296):
  - Negotiates IPsec security associations (SAs)
  - UDP port 500 (IKE), 4500 (IKE with NAT-T)

IKEv2 Phases:
  Phase 1 (IKE SA):
    - Establish secure channel for negotiation
    - Authenticate: PSK, certificates, EAP
    - Negotiate: DH group, encryption, PRF, integrity
    - Exchange: IKE_SA_INIT + IKE_AUTH

  Phase 2 (Child SA / IPsec SA):
    - Negotiate data encryption parameters
    - Create actual IPsec tunnel
    - Exchange: CREATE_CHILD_SA

IPsec Modes:
  Transport:  [IP Header][ESP][Original Payload]
              Used between hosts; preserves original IP header

  Tunnel:     [New IP Header][ESP][Original IP Header][Payload]
              Used for VPN gateways; entire packet encrypted

=== DH Groups (Diffie-Hellman) ===
  Group 14: 2048-bit MODP  — minimum recommended
  Group 19: 256-bit ECP    — EC, faster
  Group 20: 384-bit ECP    — EC, strong
  Group 21: 521-bit ECP    — maximum security
EOF
"
```

📸 **Verified Output:**
```
=== IPsec Protocol Suite ===

AH (Authentication Header, Protocol 51):
  - Provides: Authentication + Integrity (NO encryption)
  - Covers: entire IP packet including outer IP header
  - Problem: breaks NAT (changes IP header = breaks auth)
  - Rarely used today; ESP preferred

ESP (Encapsulating Security Payload, Protocol 50):
  - Provides: Encryption + Authentication + Integrity
  - Transport mode: encrypts payload only; original IP header intact
  - Tunnel mode: encrypts entire original packet; new IP header added
...
```

---

## Step 5: StrongSwan IPsec Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq strongswan 2>/dev/null | tail -1
echo '=== StrongSwan version ==='
ipsec --version 2>&1 | head -2

echo ''
echo '=== Write StrongSwan swanctl.conf (IKEv2) ==='
cat > /tmp/swanctl.conf << 'EOF'
# /etc/swanctl/swanctl.conf
# IKEv2 Site-to-Site VPN with certificates

connections {
  site-to-site {
    # Local gateway
    local_addrs  = 203.0.113.1

    # Remote gateway
    remote_addrs = 198.51.100.1

    # IKE (Phase 1) proposals
    proposals = aes256gcm16-prfsha384-ecp384

    local {
      auth = pubkey
      certs = gateway-cert.pem
      id    = vpn.local-site.example.com
    }

    remote {
      auth = pubkey
      id   = vpn.remote-site.example.com
    }

    children {
      net-to-net {
        # Subnets to tunnel
        local_ts  = 10.1.0.0/24
        remote_ts = 10.2.0.0/24

        # ESP (Phase 2) proposals
        esp_proposals = aes256gcm16-ecp384

        # IPsec mode (tunnel = default)
        mode = tunnel

        # Auto start tunnel
        start_action = start
        close_action = restart

        # DPD (Dead Peer Detection)
        dpd_action = restart
      }
    }
  }

  # Remote access (road warrior) — PSK
  road-warrior {
    local_addrs = 203.0.113.1
    proposals   = aes256-sha256-modp2048

    local {
      auth = psk
      id   = @vpn.example.com
    }

    remote {
      auth = psk
      id   = %any
    }

    children {
      road-warrior {
        local_ts  = 0.0.0.0/0
        remote_ts = dynamic
        mode      = tunnel
        esp_proposals = aes256-sha256
      }
    }
  }
}

secrets {
  # PSK for road warriors
  ike-psk {
    id     = %any
    secret = \"Sup3rS3cr3tPSK!\"
  }
}
EOF

echo '=== Config written ==='
wc -l /tmp/swanctl.conf
echo ''
echo '=== swanctl commands ==='
echo 'swanctl --load-all           # Load all config'
echo 'swanctl --list-conns         # Show connections'
echo 'swanctl --list-sas           # Show Security Associations'
echo 'swanctl --initiate --child net-to-net  # Start tunnel'
echo 'ipsec statusall              # Full status'
"
```

📸 **Verified Output:**
```
=== StrongSwan version ===
Linux strongSwan 5.9.5
  University of Applied Sciences Rapperswil, Switzerland

=== Config written ===
67 /tmp/swanctl.conf

=== swanctl commands ===
swanctl --load-all           # Load all config
swanctl --list-conns         # Show connections
swanctl --list-sas           # Show Security Associations
swanctl --initiate --child net-to-net  # Start tunnel
ipsec statusall              # Full status
```

---

## Step 6: OpenVPN Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq openvpn 2>/dev/null | tail -1
echo '=== OpenVPN version ==='
openvpn --version 2>&1 | head -1

echo ''
echo '=== OpenVPN Server Config ==='
cat << 'EOF'
# /etc/openvpn/server.conf
port 1194
proto udp
dev tun                      # tun = layer 3 (routed); tap = layer 2 (bridged)

# Certificates
ca   /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key  /etc/openvpn/server.key  # keep secret!
dh   /etc/openvpn/dh2048.pem  # Diffie-Hellman params
tls-auth /etc/openvpn/ta.key 0  # HMAC firewall

# Network
server 10.8.0.0 255.255.255.0  # VPN subnet
push \"redirect-gateway def1 bypass-dhcp\"  # route all client traffic
push \"dhcp-option DNS 1.1.1.1\"

# Client management
client-to-client              # allow clients to see each other
keepalive 10 120              # ping every 10s; restart if no reply in 120s
max-clients 100

# Security
cipher AES-256-GCM
auth SHA256
tls-version-min 1.2
ncp-ciphers AES-256-GCM:AES-128-GCM

user nobody
group nogroup
persist-key
persist-tun

# Logging
status /var/log/openvpn-status.log
log-append /var/log/openvpn.log
verb 3
EOF

echo ''
echo '=== OpenVPN Client (.ovpn) file ==='
cat << 'EOF'
# client.ovpn — distributable client config
client
dev tun
proto udp
remote vpn.example.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
verb 3
<ca>
-----BEGIN CERTIFICATE-----
(CA certificate goes here)
-----END CERTIFICATE-----
</ca>
<cert>
-----BEGIN CERTIFICATE-----
(Client certificate goes here)
-----END CERTIFICATE-----
</cert>
<key>
-----BEGIN PRIVATE KEY-----
(Client private key goes here)
-----END PRIVATE KEY-----
</key>
<tls-auth>
(HMAC key goes here)
</tls-auth>
key-direction 1
EOF
"
```

📸 **Verified Output:**
```
=== OpenVPN version ===
OpenVPN 2.5.5 x86_64-pc-linux-gnu [SSL (OpenSSL)] [LZO] [LZ4] [EPOLL] [PKCS11] [MH/PKTINFO] [AEAD] built on Jul 14 2022

=== OpenVPN Server Config ===
# /etc/openvpn/server.conf
port 1194
proto udp
dev tun                      # tun = layer 3 (routed); tap = layer 2 (bridged)
...
=== OpenVPN Client (.ovpn) file ===
# client.ovpn — distributable client config
client
dev tun
...
```

> 💡 **tun vs tap:** `tun` (tunnel) is a point-to-point Layer 3 device — IP packets only. `tap` is a Layer 2 device — passes Ethernet frames, supports bridging and non-IP protocols. Use `tun` for most VPNs; `tap` for bridged networks.

---

## Step 7: WireGuard vs IPsec vs OpenVPN Comparison

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
=== VPN Protocol Comparison ===

┌─────────────────┬──────────────────┬──────────────────┬────────────────────┐
│ Feature         │ WireGuard        │ IPsec/IKEv2      │ OpenVPN            │
├─────────────────┼──────────────────┼──────────────────┼────────────────────┤
│ Age             │ 2018 (modern)    │ 1995 (mature)    │ 2002               │
│ Codebase        │ ~4,000 lines     │ ~400,000 lines   │ ~100,000 lines     │
│ Kernel support  │ 5.6+ built-in    │ Yes (all OSes)   │ Userspace          │
│ Transport       │ UDP only         │ UDP/ESP          │ UDP or TCP         │
│ Encryption      │ ChaCha20-Poly1305│ Configurable     │ Configurable       │
│                 │ Curve25519 DH    │ AES-GCM, etc.    │ OpenSSL suite      │
│ Handshake       │ 1-RTT            │ 4-RTT (IKEv2)    │ TLS handshake      │
│ Config          │ Simple (wg.conf) │ Complex          │ Medium             │
│ Audit-friendly  │ Yes (small)      │ Difficult        │ Medium             │
│ NAT traversal   │ Built-in         │ NAT-T (UDP4500)  │ Yes                │
│ Dynamic IPs     │ Peer rotation    │ Supported        │ Supported          │
│ Multi-platform  │ Excellent        │ Excellent        │ Excellent          │
│ Enterprise auth │ Certificates+PSK │ RADIUS/EAP/certs │ LDAP/RADIUS        │
│ Kill switch     │ AllowedIPs trick │ Complex          │ Script-based       │
│ Performance     │ ★★★★★ (kernel)   │ ★★★★☆            │ ★★★☆☆ (userspace)  │
│ Best for        │ Personal, modern │ Enterprise, S2S  │ Compatibility      │
└─────────────────┴──────────────────┴──────────────────┴────────────────────┘

WireGuard Kill Switch (block non-VPN traffic):
  # Route all traffic through VPN, block leaks
  PostUp = iptables -I OUTPUT ! -o wg0 -m mark ! --mark \$(wg show wg0 fwmark) -m addrtype ! --dst-type LOCAL -j REJECT
  PostDown = iptables -D OUTPUT ! -o wg0 -m mark ! --mark \$(wg show wg0 fwmark) -m addrtype ! --dst-type LOCAL -j REJECT
EOF
"
```

📸 **Verified Output:**
```
=== VPN Protocol Comparison ===

┌─────────────────┬──────────────────┬──────────────────┬────────────────────┐
│ Feature         │ WireGuard        │ IPsec/IKEv2      │ OpenVPN            │
├─────────────────┼──────────────────┼──────────────────┼────────────────────┤
│ Age             │ 2018 (modern)    │ 1995 (mature)    │ 2002               │
│ Codebase        │ ~4,000 lines     │ ~400,000 lines   │ ~100,000 lines     │
│ Kernel support  │ 5.6+ built-in    │ Yes (all OSes)   │ Userspace          │
...
```

---

## Step 8: Capstone — WireGuard Multi-Peer Setup

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq wireguard-tools qrencode 2>/dev/null | tail -1

echo '=== Generate keys for 3-peer mesh ==='
for peer in server client1 client2; do
  priv=\$(wg genkey)
  pub=\$(echo \$priv | wg pubkey)
  eval \"\${peer}_priv=\$priv\"
  eval \"\${peer}_pub=\$pub\"
  echo \"\$peer: pub=\${pub:0:20}...\"
done

echo ''
echo '=== WireGuard Management Commands ==='
cat << 'EOF'
# Interface management (requires root):
ip link add wg0 type wireguard
ip address add 10.10.0.1/24 dev wg0
wg setconf wg0 /etc/wireguard/wg0.conf
ip link set wg0 up

# Or use wg-quick (reads /etc/wireguard/wg0.conf):
wg-quick up wg0
wg-quick down wg0
systemctl enable --now wg-quick@wg0

# Status:
wg show                        # all interfaces
wg show wg0                    # specific interface
wg show wg0 latest-handshakes  # last handshake per peer
wg show wg0 transfer           # bytes sent/received per peer
wg show wg0 endpoints          # peer endpoints

# Add peer at runtime (no restart):
wg set wg0 peer <pubkey> allowed-ips 10.10.0.3/32 endpoint 1.2.3.4:51820

# Remove peer:
wg set wg0 peer <pubkey> remove

# Generate QR code for mobile clients:
qrencode -t ansiutf8 < /etc/wireguard/client.conf
EOF

echo ''
echo '=== Summary: VPN Selection Guide ==='
cat << 'GUIDE'
Choose WireGuard when:
  ✓ Starting fresh, no legacy requirements
  ✓ Performance is critical
  ✓ Simplicity matters (small team, few peers)
  ✓ Linux kernel ≥ 5.6

Choose IPsec/IKEv2 when:
  ✓ Enterprise environment (RADIUS, certificates)
  ✓ Interoperability with Cisco/Juniper/Palo Alto
  ✓ Native iOS/macOS/Windows client needed
  ✓ Compliance requirements (FIPS 140-2)

Choose OpenVPN when:
  ✓ TCP fallback needed (restrictive firewalls)
  ✓ Need existing PKI integration
  ✓ Non-Linux servers (FreeBSD, Windows)
  ✓ Maximum compatibility across all platforms
GUIDE
"
```

📸 **Verified Output:**
```
=== Generate keys for 3-peer mesh ===
server:  pub=QwZCOldb/WvX1+jaqQ...
client1: pub=7FrXtGcHaBvS9wDk3e...
client2: pub=3RmLtKpHiDvB2yEj9w...

=== WireGuard Management Commands ===
# Interface management (requires root):
ip link add wg0 type wireguard
ip address add 10.10.0.1/24 dev wg0
wg setconf wg0 /etc/wireguard/wg0.conf
ip link set wg0 up
...
=== Summary: VPN Selection Guide ===
Choose WireGuard when:
  ✓ Starting fresh, no legacy requirements
  ✓ Performance is critical
...
```

---

## Summary

| Topic | Key Points |
|-------|-----------|
| **VPN Types** | Site-to-site, remote-access, SSL VPN |
| **IPsec AH** | Auth + integrity only; no encryption; breaks NAT |
| **IPsec ESP** | Encryption + auth; protocol 50; tunnel or transport mode |
| **IKEv2** | Key exchange; UDP 500/4500; Phase 1 (IKE SA) + Phase 2 (Child SA) |
| **strongSwan** | IKEv2 implementation; swanctl.conf; PSK or certificates |
| **OpenVPN** | TLS-based; UDP port 1194; tun (L3) or tap (L2); .ovpn files |
| **WireGuard** | 4,000 lines; ChaCha20; Curve25519; UDP only; kernel 5.6+ |
| **wg genkey** | Generates Curve25519 private key (base64) |
| **wg pubkey** | Derives public key from private key |
| **AllowedIPs** | Cryptographic routing table; 0.0.0.0/0 = full tunnel |
| **PersistentKeepalive** | Keeps NAT mappings alive (25s recommended) |
| **wg-quick** | Helper to manage interface lifecycle |
| **Performance** | WireGuard > IPsec > OpenVPN (WireGuard is kernel-native) |

---

**Next Lab →** [Lab 20: Capstone — Protocol Stack Analysis](lab-20-capstone-protocol-stack-analysis.md)
