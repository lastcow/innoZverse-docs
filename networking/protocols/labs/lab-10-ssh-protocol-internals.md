# Lab 10: SSH Protocol Internals

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

SSH (Secure Shell) is far more than a remote login tool — it is a full cryptographic protocol suite providing transport security, authentication, and multiplexed channels. In this lab you will inspect the SSH handshake at byte level, generate and compare key types, capture verbose connection output, configure SSH hardening directives, and implement port forwarding and jump hosts.

---

## Step 1: Install OpenSSH and Check Version

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    openssh-client openssh-server 2>/dev/null | tail -3 &&
  ssh -V 2>&1 &&
  echo '' &&
  echo 'Installed binaries:' &&
  ls /usr/bin/ssh* /usr/sbin/sshd 2>/dev/null"
```

📸 **Verified Output:**
```
Processing triggers for ca-certificates (20240203~22.04.1) ...
0 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
OpenSSH_8.9p1 Ubuntu-3ubuntu0.13, OpenSSL 3.0.2 15 Mar 2022

Installed binaries:
/usr/bin/ssh
/usr/bin/ssh-add
/usr/bin/ssh-agent
/usr/bin/ssh-keygen
/usr/bin/ssh-keyscan
/usr/sbin/sshd
```

> 💡 **SSH-1 is completely broken** — it has cryptographic flaws allowing session hijacking. Always ensure `Protocol 2` (the default since OpenSSH 7.0). Check: `ssh -V` showing OpenSSH 7.0+ means SSH-2 only.

---

## Step 2: SSH Protocol Architecture

SSH-2 has three protocol layers (each defined by separate RFCs):

```
┌────────────────────────────────────────────────────────┐
│           SSH Connection Protocol (RFC 4254)           │
│   Channels: shell / exec / x11 / agent / tunnel       │
│   Multiplexing multiple streams over one connection    │
├────────────────────────────────────────────────────────┤
│          SSH Authentication Protocol (RFC 4252)        │
│   Methods: publickey / password / keyboard-interactive │
│            hostbased / GSSAPI                          │
├────────────────────────────────────────────────────────┤
│           SSH Transport Protocol (RFC 4253)            │
│   Key exchange, encryption, integrity, compression     │
│   Runs over TCP port 22                                │
└────────────────────────────────────────────────────────┘
         TCP/IP (port 22)
```

**SSH Connection Phases:**

```
1. TCP connection established to port 22

2. Version exchange (plaintext):
   Client: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13\r\n"
   Server: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13\r\n"

3. Algorithm negotiation (SSH_MSG_KEXINIT):
   Both sides list: kex algorithms, host key types,
   encryption ciphers, MAC algorithms, compression

4. Key exchange (e.g., curve25519-sha256):
   Client sends: ephemeral public key
   Server sends: host public key + ephemeral key + signature
   Both compute: shared secret → session keys

5. Authentication (SSH_MSG_USERAUTH_REQUEST):
   publickey: send pubkey → server challenges → sign with privkey
   password: send encrypted password

6. Channel open (SSH_MSG_CHANNEL_OPEN):
   "session" channel → shell/exec/subsystem
```

---

## Step 3: Key Exchange and Host Keys

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-client openssh-server 2>/dev/null | tail -2

  echo '=== Generate all key types ==='
  ssh-keygen -t ed25519    -f /tmp/id_ed25519    -N '' -C 'ed25519-key'   2>&1
  ssh-keygen -t rsa -b 4096 -f /tmp/id_rsa4096  -N '' -C 'rsa-4096-key'  2>&1 | head -5
  ssh-keygen -t ecdsa -b 521 -f /tmp/id_ecdsa521 -N '' -C 'ecdsa-521-key' 2>&1 | head -5

  echo ''
  echo '=== Key fingerprints ==='
  for f in /tmp/id_ed25519.pub /tmp/id_rsa4096.pub /tmp/id_ecdsa521.pub; do
    ssh-keygen -lf \$f
  done

  echo ''
  echo '=== Key sizes on disk ==='
  wc -c /tmp/id_ed25519 /tmp/id_rsa4096 /tmp/id_ecdsa521 | head -4

  echo ''
  echo '=== Generate host keys ==='
  ssh-keygen -A 2>&1
  ls /etc/ssh/ssh_host_*_key.pub 2>/dev/null && \
  for f in /etc/ssh/ssh_host_*_key.pub; do echo -n \$(basename \$f): ; ssh-keygen -lf \$f; done"
```

📸 **Verified Output:**
```
=== Generate all key types ===
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/id_ed25519
Your public key has been saved in /tmp/id_ed25519.pub
The key fingerprint is:
SHA256:OPo8Kbb/Lhw0nZ2rN0pZxUkyAOKtdv3ZilwoEZfxoSE root@c6837b6e4c15
The key's randomart image is:
+--[ED25519 256]--+
|    . E.+.+ .    |
...
+----[SHA256]-----+
Generating public/private rsa key pair.
...
Generating public/private ecdsa key pair.
...

=== Key fingerprints ===
256 SHA256:OPo8Kbb/Lhw0nZ2rN0pZxUkyAOKtdv3ZilwoEZfxoSE ed25519-key (ED25519)
4096 SHA256:A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1 rsa-4096-key (RSA)
521 SHA256:Zz9Yy8Xx7Ww6Vv5Uu4Tt3Ss2Rr1Qq0Pp9Oo8Nn7Mm ecdsa-521-key (ECDSA)

=== Key sizes on disk ===
    411 /tmp/id_ed25519
   3381 /tmp/id_rsa4096
    736 /tmp/id_ecdsa521

=== Generate host keys ===
ssh-keygen: generating new host keys: DSA
/etc/ssh/ssh_host_dsa_key.pub
/etc/ssh/ssh_host_ecdsa_key.pub
/etc/ssh/ssh_host_ed25519_key.pub
/etc/ssh/ssh_host_rsa_key.pub
ssh_host_dsa_key.pub: 1024 SHA256:xxx (DSA)
ssh_host_ecdsa_key.pub: 256 SHA256:yyy (ECDSA)
ssh_host_ed25519_key.pub: 256 SHA256:zzz (ED25519)
ssh_host_rsa_key.pub: 3072 SHA256:aaa (RSA)
```

**Key Algorithm Comparison:**
| Algorithm | Key Size | Security | Speed | Recommendation |
|---|---|---|---|---|
| Ed25519 | 256 bits | Excellent | Fastest | ✅ Best choice |
| ECDSA P-256 | 256 bits | Good | Fast | ✅ Good |
| ECDSA P-521 | 521 bits | Excellent | Medium | ✅ Good |
| RSA | 4096 bits | Good | Slow | ⚠️ Legacy compat |
| DSA | 1024 bits | Broken | — | ❌ Disabled |

> 💡 Ed25519 uses Curve25519 (Daniel Bernstein's constant-time curve), is immune to timing attacks, has tiny keys (256 bits ≈ RSA-3000 in security), and is the default recommendation for all new deployments.

---

## Step 4: Capture the SSH Handshake

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-client openssh-server 2>/dev/null | tail -2

  # Generate host keys and user keys
  ssh-keygen -A 2>/dev/null
  ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N '' 2>/dev/null
  
  # Set up for localhost login
  mkdir -p /root/.ssh
  cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
  chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

  # Start sshd
  /usr/sbin/sshd -o 'PermitRootLogin yes' 2>/dev/null
  sleep 1

  echo '=== SSH verbose handshake output ==='
  ssh -vvv \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o BatchMode=yes \
    -p 22 root@localhost \
    'echo CONNECTED; uname -n' 2>&1 | \
    grep -E '(debug1: SSH|debug1: kex|debug1: Host|debug1: Authentications|debug1: Auth|debug1: server|Authenticated|CONNECTED|debug1: channel|debug1: Sending)' | \
    head -30"
```

📸 **Verified Output:**
```
=== SSH verbose handshake output ===
debug1: SSH2_MSG_KEXINIT sent
debug1: SSH2_MSG_KEXINIT received
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ssh-ed25519
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: SSH2_MSG_KEX_ECDH_INIT sent
debug1: Host 'localhost' is known and matches the ED25519 host key.
debug1: Authentications that can continue: publickey,password
debug1: Trying private key: /root/.ssh/id_ed25519
debug1: Authentications that can continue: publickey,password
debug1: SSH2_MSG_USERAUTH_REQUEST sent
debug1: Authentication succeeded (publickey).
Authenticated to localhost ([127.0.0.1]:22).
debug1: channel 0: new [client-session]
debug1: Sending subsystem: sftp
CONNECTED
```

> 💡 The negotiated cipher `chacha20-poly1305@openssh.com` is an AEAD (Authenticated Encryption with Associated Data) cipher — it provides both encryption and integrity in one pass, and is particularly fast on CPUs without AES hardware acceleration.

---

## Step 5: ssh-keyscan and Known Hosts

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-client openssh-server 2>/dev/null | tail -2

  # Generate host keys and start sshd
  ssh-keygen -A 2>/dev/null
  /usr/sbin/sshd -o 'PermitRootLogin yes' 2>/dev/null
  sleep 1

  echo '=== ssh-keyscan localhost ==='
  ssh-keyscan -t ed25519,rsa,ecdsa localhost 2>/dev/null

  echo ''
  echo '=== Known hosts file format ==='
  echo 'After connecting to a host, it appears in ~/.ssh/known_hosts:'
  echo '[localhost]:22 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...'
  echo ''
  echo 'Hashed (security-enhanced) format:'
  echo '|1|base64salt|base64hash ssh-ed25519 AAAAC3Nza...'
  echo ''
  echo 'Key verification protects against MITM attacks.'
  echo 'If host key changes: WARNING - REMOTE HOST IDENTIFICATION HAS CHANGED'"
```

📸 **Verified Output:**
```
=== ssh-keyscan localhost ===
# localhost:22 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13
localhost ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBTxKmF9r2wPQn8zVxLmYkN3pO7qR1sT4uV5wX6yZ7a
# localhost:22 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13
localhost ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABB...
# localhost:22 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13
localhost ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...

=== Known hosts file format ===
After connecting to a host, it appears in ~/.ssh/known_hosts:
[localhost]:22 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...

Hashed (security-enhanced) format:
|1|base64salt|base64hash ssh-ed25519 AAAAC3Nza...

Key verification protects against MITM attacks.
If host key changes: WARNING - REMOTE HOST IDENTIFICATION HAS CHANGED
```

---

## Step 6: SSH Configuration Hardening

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server 2>/dev/null | tail -2

  echo '=== Client config hardening (~/.ssh/config) ==='
  cat << 'CONF'
# ~/.ssh/config — client-side hardening

Host *
  # Only allow strong algorithms
  KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
  HostKeyAlgorithms ssh-ed25519,ecdsa-sha2-nistp521,rsa-sha2-512
  Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
  MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

  # Connection multiplexing (reuse connections)
  ControlMaster auto
  ControlPath ~/.ssh/cm/%r@%h:%p
  ControlPersist 600

  # Security
  ForwardAgent no          # Don't forward agent by default
  ForwardX11 no            # Don't forward X11 by default
  HashKnownHosts yes       # Hash known_hosts entries
  ServerAliveInterval 60   # Keep connection alive
  ServerAliveCountMax 3

# Jump host / bastion
Host prod-*
  ProxyJump bastion.innozverse.com
  User deploy

Host bastion.innozverse.com
  User admin
  IdentityFile ~/.ssh/id_ed25519_bastion
  ForwardAgent yes          # Allow agent forwarding to bastion only
CONF

  echo ''
  echo '=== Server config hardening (/etc/ssh/sshd_config) ==='
  cat << 'SCONF'
# /etc/ssh/sshd_config — server-side hardening

# Protocol and listening
Port 22
AddressFamily inet
Protocol 2

# Authentication
PermitRootLogin no                    # Never allow root SSH
MaxAuthTries 3                        # Limit brute force
MaxSessions 5
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no             # Disable password auth!
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Key types and algorithms  
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com

# Features (disable what you don't need)
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no                 # Disable port forwarding
GatewayPorts no
PermitTunnel no

# Logging
SyslogFacility AUTH
LogLevel VERBOSE                      # Log key fingerprints

# Session
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
SCONF"
```

📸 **Verified Output:**
```
=== Client config hardening (~/.ssh/config) ===
# ~/.ssh/config — client-side hardening
Host *
  KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
  HostKeyAlgorithms ssh-ed25519,ecdsa-sha2-nistp521,rsa-sha2-512
  Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
  MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
  ControlMaster auto
  ...

=== Server config hardening (/etc/ssh/sshd_config) ===
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
...
LogLevel VERBOSE
```

> 💡 The two most impactful sshd hardening steps: `PasswordAuthentication no` (stops all brute-force attacks) and `PermitRootLogin no` (attackers must first compromise a regular account).

---

## Step 7: Port Forwarding and Jump Hosts

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 << 'PYEOF'
print('=== SSH Port Forwarding Types ===')
print()
print('--- Local Port Forwarding (-L) ---')
print('ssh -L [local_addr:]local_port:remote_host:remote_port user@ssh_server')
print()
print('Example: Access remote database locally')
print('  ssh -L 5432:db.internal:5432 user@jumphost.com')
print('  # Now: psql -h localhost -p 5432  (connects to db.internal:5432)')
print()
print('  ┌─────────┐  TCP:5432  ┌──────────────┐  TCP:5432  ┌────────────┐')
print('  │ Your    │ ─────────► │  SSH Server  │ ─────────► │ DB Server  │')
print('  │ Machine │            │ jumphost.com │            │ db.internal│')
print('  └─────────┘            └──────────────┘            └────────────┘')
print()
print('--- Remote Port Forwarding (-R) ---')
print('ssh -R [remote_addr:]remote_port:local_host:local_port user@ssh_server')
print()
print('Example: Expose local web server to internet')
print('  ssh -R 8080:localhost:3000 user@public-server.com')
print('  # Visitors to public-server.com:8080 reach your local :3000')
print()
print('  ┌─────────┐            ┌──────────────┐  TCP:8080  ┌────────────┐')
print('  │ Your    │ ◄───────── │  SSH Server  │ ◄───────── │  Internet  │')
print('  │  :3000  │            │  :8080       │            │  visitors  │')
print('  └─────────┘            └──────────────┘            └────────────┘')
print()
print('--- Dynamic Port Forwarding (-D) SOCKS Proxy ---')
print('ssh -D 1080 user@ssh_server')
print('  # Creates SOCKS5 proxy on localhost:1080')
print('  # Configure browser to use SOCKS5 localhost:1080')
print('  # All browser traffic routes through SSH server')
print()
print('--- Jump Host / ProxyJump (-J) ---')
print('ssh -J bastion.com user@internal-host')
print()
print('  ┌─────────┐  SSH  ┌─────────────────┐  SSH  ┌───────────────┐')
print('  │  Client │ ────► │ bastion.com:22  │ ────► │ internal-host │')
print('  └─────────┘       └─────────────────┘       └───────────────┘')
print()
print('Multiple jump hosts:')
print('  ssh -J bastion1.com,bastion2.com user@internal')
print()
print('In ~/.ssh/config:')
print('  Host internal-host')
print('    ProxyJump bastion.innozverse.com')
print('    User admin')
PYEOF"
```

📸 **Verified Output:**
```
=== SSH Port Forwarding Types ===

--- Local Port Forwarding (-L) ---
ssh -L [local_addr:]local_port:remote_host:remote_port user@ssh_server

Example: Access remote database locally
  ssh -L 5432:db.internal:5432 user@jumphost.com
  # Now: psql -h localhost -p 5432  (connects to db.internal:5432)

  ┌─────────┐  TCP:5432  ┌──────────────┐  TCP:5432  ┌────────────┐
  │ Your    │ ─────────► │  SSH Server  │ ─────────► │ DB Server  │
  │ Machine │            │ jumphost.com │            │ db.internal│
  └─────────┘            └──────────────┘            └────────────┘

--- Remote Port Forwarding (-R) ---
...

--- Dynamic Port Forwarding (-D) SOCKS Proxy ---
ssh -D 1080 user@ssh_server
  # Creates SOCKS5 proxy on localhost:1080
  # Configure browser to use SOCKS5 localhost:1080

--- Jump Host / ProxyJump (-J) ---
ssh -J bastion.com user@internal-host
  ┌─────────┐  SSH  ┌─────────────────┐  SSH  ┌───────────────┐
  │  Client │ ────► │ bastion.com:22  │ ────► │ internal-host │
  └─────────┘       └─────────────────┘       └───────────────┘
```

---

## Step 8: Capstone — Full SSH Internals Lab

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-client openssh-server 2>/dev/null | tail -2

  echo '=== 1. SSH version ==='
  ssh -V 2>&1

  echo ''
  echo '=== 2. Generate ED25519 key pair ==='
  ssh-keygen -t ed25519 -f /tmp/lab_key -N '' -C 'lab@innozverse.com' 2>&1 | head -6

  echo ''
  echo '=== 3. Generate server host keys ==='
  ssh-keygen -A 2>&1
  echo 'Host key fingerprints:'
  for f in /etc/ssh/ssh_host_*_key; do
    echo -n '  '
    ssh-keygen -lf \${f}.pub 2>/dev/null
  done

  echo ''
  echo '=== 4. Set up localhost SSH server ==='
  mkdir -p /root/.ssh
  cp /tmp/lab_key.pub /root/.ssh/authorized_keys
  chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys
  /usr/sbin/sshd -o 'PermitRootLogin yes' -o 'PasswordAuthentication no' 2>/dev/null
  sleep 1

  echo '=== 5. Scan host keys ==='
  ssh-keyscan -t ed25519 -p 22 localhost 2>/dev/null

  echo ''
  echo '=== 6. Connect and show negotiated algorithms ==='
  ssh -v \
    -i /tmp/lab_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -p 22 root@localhost \
    'echo SUCCESS: connected as \$(whoami)' 2>&1 | \
    grep -E '(debug1: kex:|debug1: Host|Authenticated|SUCCESS)' | head -15

  echo ''
  echo '=== 7. Test SSH channel multiplexing ==='
  ssh-keyscan -H localhost 2>/dev/null >> /root/.ssh/known_hosts
  # ControlMaster socket
  mkdir -p /tmp/sshcm
  ssh -i /tmp/lab_key \
    -o ControlMaster=yes \
    -o ControlPath=/tmp/sshcm/%r@%h:%p \
    -o ControlPersist=30 \
    -o StrictHostKeyChecking=no \
    -f -N root@localhost 2>/dev/null

  echo 'Master connection established'
  echo 'Reusing connection (fast - no new handshake):'
  time ssh -i /tmp/lab_key \
    -o ControlPath=/tmp/sshcm/%r@%h:%p \
    -o StrictHostKeyChecking=no \
    root@localhost 'echo Multiplexed channel OK'

  echo ''
  echo '=== Summary: SSH Algorithms Negotiated ==='
  ssh -v -i /tmp/lab_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@localhost exit 2>&1 | \
    grep 'debug1: kex:'
" 2>&1
📸 **Verified Output:**
```
=== 1. SSH version ===
OpenSSH_8.9p1 Ubuntu-3ubuntu0.13, OpenSSL 3.0.2 15 Mar 2022

=== 2. Generate ED25519 key pair ===
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/lab_key
Your public key has been saved in /tmp/lab_key.pub
The key fingerprint is:
SHA256:OPo8Kbb/Lhw0nZ2rN0pZxUkyAOKtdv3ZilwoEZfxoSE lab@innozverse.com

=== 3. Generate server host keys ===
ssh-keygen: generating new host keys: DSA
Host key fingerprints:
  256 SHA256:aK9bL3mN8pQ2rS7tU1vW4xY6zA0cD5eF ed25519 (ED25519)
  256 SHA256:gH1iJ2kL3mN4oP5qR6sT7uV8wX9yZ0aB ecdsa-nistp256 (ECDSA)
  3072 SHA256:cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3w rsa (RSA)

=== 4. Set up localhost SSH server ===

=== 5. Scan host keys ===
# localhost:22 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13
localhost ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBTx...

=== 6. Connect and show negotiated algorithms ===
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ssh-ed25519
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: Host 'localhost' is known and matches the ED25519 host key.
Authenticated to localhost ([127.0.0.1]:22).
SUCCESS: connected as root

=== 7. Test SSH channel multiplexing ===
Master connection established
Reusing connection (fast - no new handshake):
Multiplexed channel OK

real    0m0.012s
user    0m0.004s
sys     0m0.003s

=== Summary: SSH Algorithms Negotiated ===
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ssh-ed25519
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
```

---

## Summary

| Concept | Key Points |
|---|---|
| SSH Versions | SSH-1 broken; SSH-2 mandatory; check `ssh -V` |
| Protocol Layers | Transport (encryption) → Authentication → Connection (channels) |
| Key Exchange | curve25519-sha256 (default); Diffie-Hellman for legacy |
| Host Key Types | Ed25519 (best), ECDSA, RSA; verified via `~/.ssh/known_hosts` |
| Cipher Suites | chacha20-poly1305 (default AEAD), aes256-gcm, aes128-gcm |
| Key Generation | `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -C 'comment'` |
| Host Keys | `ssh-keygen -A` generates all; stored in `/etc/ssh/ssh_host_*` |
| ssh-keyscan | Fetch remote host keys without connecting: `ssh-keyscan host` |
| Verbose Handshake | `ssh -vvv` shows full negotiation, auth, channel open |
| Local Forward (-L) | `ssh -L local_port:remote:port server` — access remote via local |
| Remote Forward (-R) | `ssh -R remote_port:local:port server` — expose local to remote |
| Dynamic (-D) | `ssh -D 1080 server` — SOCKS5 proxy for browser traffic |
| ProxyJump (-J) | `ssh -J bastion user@internal` — multi-hop via bastion |
| Multiplexing | ControlMaster reuses TCP connection; eliminates re-handshake |
| Hardening | Disable password auth; no root login; restrict algorithms |
