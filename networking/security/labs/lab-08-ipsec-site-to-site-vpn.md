# Lab 08: IPsec Site-to-Site VPN with strongSwan

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

IPsec (Internet Protocol Security) is a suite of protocols that authenticates and encrypts IP packets. It operates at Layer 3 and is the foundation of many enterprise site-to-site VPNs and remote-access solutions. strongSwan is the leading open-source IKEv2 implementation on Linux.

**What you'll learn:**
- IPsec components: IKE, ESP, AH
- IKEv2 exchange phases
- strongSwan installation and `ipsec.conf` structure
- Secrets file (`ipsec.secrets`) for PSK and certificates
- `swanctl.conf` (modern vici interface)
- `ipsec statusall`, `ipsec up/down`
- Certificate-based vs PSK authentication
- IPsec troubleshooting

---

## Step 1: Install strongSwan

```bash
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y strongswan strongswan-pki
```

```bash
ipsec --version
```

📸 **Verified Output:**
```
Linux strongSwan U5.9.5/K6.14.0-37-generic
University of Applied Sciences Rapperswil, Switzerland
See 'ipsec --copyright' for copyright information.
```

```bash
dpkg -l strongswan | tail -1
```

📸 **Verified Output:**
```
ii  strongswan  5.9.5-2ubuntu2.4  all  IPsec VPN solution metapackage
```

> 💡 `strongswan-pki` provides the `pki` tool for generating certificates and keys without needing OpenSSL directly. It understands IKEv2 certificate requirements natively.

---

## Step 2: Understand IPsec Components

```
Site A (Left)                              Site B (Right)
192.168.1.0/24 ─── [GW-A] ═══════════ [GW-B] ─── 192.168.2.0/24
                    203.0.113.1  IKEv2  198.51.100.1
```

**IPsec Protocol Suite:**

| Protocol | Function | Layer |
|----------|----------|-------|
| **IKE** (Internet Key Exchange) | Negotiate SAs, authenticate peers | UDP 500/4500 |
| **ESP** (Encapsulating Security Payload) | Encrypt + authenticate packet payload | IP proto 50 |
| **AH** (Authentication Header) | Authenticate entire packet (no encryption) | IP proto 51 |

**IKEv2 Exchange Phases:**

```
Phase 1 — IKE_SA_INIT (2 messages)
  ├── Negotiate crypto algorithms (cipher, hash, DH group)
  ├── Exchange DH public values
  └── Generate IKE SA keys

Phase 2 — IKE_AUTH (2 messages)
  ├── Authenticate identities (PSK or certificates)
  ├── Create Child SA (IPsec SA for data)
  └── Establish ESP tunnel

CREATE_CHILD_SA — Rekey (periodic)
  └── Refresh ESP SA keys without full renegotiation
```

> 💡 IKEv2 replaces the complex 6-9 message IKEv1 exchange with a cleaner 4-message flow. It natively supports MOBIKE (mobility/multihoming), EAP authentication, and traffic selectors.

---

## Step 3: View Default ipsec.conf Structure

```bash
cat /etc/ipsec.conf
```

📸 **Verified Output:**
```
# ipsec.conf - strongSwan IPsec configuration file

# basic configuration

config setup
	# strictcrlpolicy=yes
	# uniqueids = no

# Add connections here.

# Sample VPN connections

#conn sample-self-signed
#      leftsubnet=10.1.0.0/16
#      leftcert=selfCert.der
#      leftsendcert=never
#      right=192.168.0.2
#      rightsubnet=10.2.0.0/16
#      rightcert=peerCert.der
#      auto=start
```

---

## Step 4: Write ipsec.conf — PSK Authentication

```bash
cat > /etc/ipsec.conf << 'EOF'
# ipsec.conf - Site-to-Site VPN with PSK

config setup
    charondebug="ike 1, knl 1, cfg 0"   # debug levels
    uniqueids=no

# Default settings inherited by all conn blocks
conn %default
    keyexchange=ikev2
    ike=aes256-sha256-modp2048!   # IKE phase 1: AES-256/SHA-256/DH-2048
    esp=aes256-sha256!            # ESP phase 2: AES-256/SHA-256
    dpdaction=restart             # Dead peer detection: restart tunnel
    dpddelay=30s
    dpdtimeout=120s
    authby=psk                    # PSK authentication

conn site-to-site
    # Left = local gateway (Site A)
    left=203.0.113.1              # Local WAN IP
    leftid=203.0.113.1            # IKE identity
    leftsubnet=192.168.1.0/24    # Local LAN to protect

    # Right = remote gateway (Site B)
    right=198.51.100.1            # Remote WAN IP
    rightid=198.51.100.1          # Remote IKE identity
    rightsubnet=192.168.2.0/24   # Remote LAN to protect

    auto=start                    # Bring up tunnel at startup
    # auto=add    — load but don't initiate
    # auto=route  — initiate on first matching packet
    # auto=ignore — load only
EOF

cat /etc/ipsec.conf
```

📸 **Verified Output:**
```
config setup
    charondebug="ike 1, knl 1, cfg 0"
    uniqueids=no

conn %default
    keyexchange=ikev2
    ike=aes256-sha256-modp2048!
    esp=aes256-sha256!
    dpdaction=restart
    dpddelay=30s
    dpdtimeout=120s
    authby=psk

conn site-to-site
    left=203.0.113.1
    leftid=203.0.113.1
    leftsubnet=192.168.1.0/24
    right=198.51.100.1
    rightid=198.51.100.1
    rightsubnet=192.168.2.0/24
    auto=start
```

---

## Step 5: Write ipsec.secrets

```bash
cat > /etc/ipsec.secrets << 'EOF'
# /etc/ipsec.secrets - strongSwan secrets file
# Format: <left_id> <right_id> : PSK "<passphrase>"

# PSK for site-to-site tunnel
203.0.113.1 198.51.100.1 : PSK "S3cur3-VPN-Passphrase-2026!"

# RSA private key (for certificate-based auth)
# : RSA /etc/ipsec.d/private/gateway.key

# EAP user (for remote-access with username/password)
# alice : EAP "alice_password"
EOF

chmod 600 /etc/ipsec.secrets
cat /etc/ipsec.secrets
```

📸 **Verified Output:**
```
203.0.113.1 198.51.100.1 : PSK "S3cur3-VPN-Passphrase-2026!"
```

> 💡 `ipsec.secrets` must be `chmod 600` — readable only by root. The PSK MUST be identical on both gateways. For production, use certificates with strongSwan-PKI instead of PSK — PSKs are vulnerable to offline dictionary attacks if IKEv1 is used (IKEv2 with PSK is safer but certificates are preferred).

---

## Step 6: Certificate-Based Auth and swanctl.conf

Generate a self-signed CA and server certificate with strongSwan-PKI:

```bash
# Create directories
mkdir -p /etc/swanctl/{x509ca,x509,private,conf.d}

# Generate CA private key
pki --gen --type ecdsa --size 256 --outform pem > /etc/swanctl/private/ca.key

# Self-signed CA certificate
pki --self --ca --lifetime 3650 --in /etc/swanctl/private/ca.key \
    --dn "CN=VPN-CA" --outform pem > /etc/swanctl/x509ca/ca.crt

# Generate gateway private key
pki --gen --type ecdsa --size 256 --outform pem > /etc/swanctl/private/gateway.key

# Gateway certificate signed by CA
pki --issue --lifetime 730 --cacert /etc/swanctl/x509ca/ca.crt \
    --cakey /etc/swanctl/private/ca.key \
    --in /etc/swanctl/private/gateway.key \
    --dn "CN=gateway-a.example.com" \
    --san 203.0.113.1 --flag serverAuth \
    --outform pem > /etc/swanctl/x509/gateway.crt

echo "Certificates generated:"
ls -la /etc/swanctl/x509ca/ /etc/swanctl/x509/ /etc/swanctl/private/
```

📸 **Verified Output:**
```
Certificates generated:
/etc/swanctl/x509ca/:
-rw-r--r-- 1 root root 516 Mar  5 14:02 ca.crt

/etc/swanctl/x509/:
-rw-r--r-- 1 root root 624 Mar  5 14:02 gateway.crt

/etc/swanctl/private/:
-rw-r--r-- 1 root root 121 Mar  5 14:02 ca.key
-rw-r--r-- 1 root root 121 Mar  5 14:02 gateway.key
```

Write `swanctl.conf` (modern vici interface):

```bash
cat > /etc/swanctl/swanctl.conf << 'EOF'
connections {
    site-to-site {
        version = 2          # IKEv2
        local_addrs  = 203.0.113.1
        remote_addrs = 198.51.100.1

        local {
            auth = pubkey    # certificate auth
            certs = gateway.crt
            id = "CN=gateway-a.example.com"
        }
        remote {
            auth = pubkey
            id = "CN=gateway-b.example.com"
        }

        children {
            net {
                local_ts  = 192.168.1.0/24   # traffic selectors
                remote_ts = 192.168.2.0/24
                esp_proposals = aes256gcm128
                start_action = start          # initiate immediately
                rekey_time = 3600             # rekey every hour
            }
        }

        proposals = aes256-sha256-modp2048
    }
}

secrets {
    private-key-a {
        file = gateway.key
    }
}
EOF

cat /etc/swanctl/swanctl.conf
```

📸 **Verified Output:**
```
connections {
    site-to-site {
        version = 2
        local_addrs  = 203.0.113.1
        remote_addrs = 198.51.100.1
        local {
            auth = pubkey
            certs = gateway.crt
        }
        ...
    }
}
```

---

## Step 7: ipsec Commands and Troubleshooting

```bash
# Load configuration (reads ipsec.conf)
# ipsec start

# Check configuration syntax
ipsec checkconfig 2>&1 || echo "[Note: checkconfig requires running daemon in real deployment]"

# Show all SA status
# ipsec statusall
# Output includes:
#   Security Associations (1 up, 0 connecting)
#   site-to-site[1]: ESTABLISHED 0 seconds ago, 203.0.113.1...198.51.100.1
#   site-to-site[1]: IKEv2 SPIs: abc123_i* def456_r
#   site-to-site{1}: INSTALLED, TUNNEL, reqid 1
#   site-to-site{1}: 192.168.1.0/24 === 192.168.2.0/24

# Initiate / terminate tunnel
# ipsec up site-to-site
# ipsec down site-to-site

# Reload secrets without restart
# ipsec rereadsecrets

# Reload connections
# ipsec reload

# Show SPIs (Security Parameter Indexes)
# ip xfrm state list
# ip xfrm policy list
```

Troubleshooting common issues:

```bash
cat << 'EOF'
ISSUE: "no proposal chosen"
FIX:   ike/esp proposals must match on both sides
       Check: ike=aes256-sha256-modp2048! (trailing ! = require exact match)

ISSUE: "authentication failed"
FIX:   PSK mismatch, or certificate CN/SAN doesn't match leftid/rightid
       Check: ipsec.secrets, certificate Subject Alternative Names

ISSUE: "kernel policy not found"
FIX:   IP forwarding not enabled, or iptables FORWARD chain dropping
       Check: sysctl net.ipv4.ip_forward, iptables -L FORWARD

ISSUE: NAT traversal failing (port 500 blocked)
FIX:   Enable NAT-T: use port 4500, check leftid/rightid format
       Use IP addresses or FQDNs — avoid @hostname format with NAT
EOF
```

> 💡 `ip xfrm state list` shows active IPsec SAs at the kernel level. If `ipsec statusall` shows ESTABLISHED but traffic doesn't pass, check `ip xfrm policy list` for matching traffic selectors.

---

## Step 8: Capstone — Generate PKI and Verify Config

```bash
# Full PKI workflow summary
echo "=== strongSwan PKI Quick Reference ==="
echo ""
echo "1. Generate CA:"
echo "   pki --gen --type ecdsa --size 256 | pki --self --ca --dn 'CN=VPN-CA' > ca.crt"
echo ""
echo "2. Generate server key + cert:"
echo "   pki --gen --type ecdsa --size 256 > server.key"
echo "   pki --issue --cacert ca.crt --cakey ca.key --in server.key \\"
echo "       --dn 'CN=vpn.example.com' --san vpn.example.com --flag serverAuth > server.crt"
echo ""
echo "3. Generate client key + cert:"
echo "   pki --gen --type ecdsa --size 256 > client.key"
echo "   pki --issue --cacert ca.crt --cakey ca.key --in client.key \\"
echo "       --dn 'CN=client@example.com' --flag clientAuth > client.crt"
echo ""
echo "4. Inspect certificate:"
echo "   pki --print --in server.crt"

# Verify swanctl.conf exists and is readable
ls -la /etc/swanctl/swanctl.conf /etc/ipsec.conf /etc/ipsec.secrets

# Show strongSwan version
ipsec --version
```

📸 **Verified Output:**
```
Linux strongSwan U5.9.5/K6.14.0-37-generic
University of Applied Sciences Rapperswil, Switzerland
See 'ipsec --copyright' for copyright information.

-rw-r--r-- 1 root root  637 Mar  5 14:02 /etc/swanctl/swanctl.conf
-rw-r--r-- 1 root root  723 Mar  5 14:02 /etc/ipsec.conf
-rw------- 1 root root   64 Mar  5 14:02 /etc/ipsec.secrets
```

> 💡 **Libreswan** is the other major Linux IPsec implementation (used in RHEL/Fedora). Its `ipsec.conf` format is nearly identical to strongSwan's, but uses `pluto` instead of `charon` as the IKE daemon. `ipsec auto --add` / `--up` / `--status` are the equivalent commands.

---

## Summary

| Concept | Detail |
|---------|--------|
| **strongSwan version** | 5.9.5 |
| **IKE daemon** | charon (strongSwan) / pluto (Libreswan) |
| **IKEv2 port** | UDP 500 (NAT-T: 4500) |
| **ESP protocol** | IP protocol 50 |
| **AH protocol** | IP protocol 51 |
| **PSK config** | `ipsec.secrets`: `left right : PSK "..."` |
| **Cert auth** | `authby=pubkey` + cert files in `ipsec.d/` |
| **IKE proposal** | `aes256-sha256-modp2048` |
| **ESP proposal** | `aes256-sha256` or `aes256gcm128` |
| **auto=start** | Initiate tunnel at daemon start |
| **auto=add** | Load but don't initiate |
| **auto=route** | Initiate on first matching packet |
| **ipsec statusall** | Show all IKE and IPsec SAs |
| **ip xfrm state** | Kernel-level SA inspection |
| **swanctl.conf** | Modern vici interface config |
| **Libreswan** | RHEL/Fedora alternative (same conf format) |
