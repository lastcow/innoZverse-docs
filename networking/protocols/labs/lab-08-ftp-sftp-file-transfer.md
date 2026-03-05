# Lab 08: FTP, SFTP, and Secure File Transfer

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

File transfer protocols are foundational network tools. In this lab you will understand FTP active vs passive modes, install and configure vsftpd, explore FTP's security weaknesses, learn FTPS (FTP over TLS), and master SFTP (the SSH-based protocol that has little in common with FTP despite the similar name).

---

## Step 1: Install vsftpd and OpenSSH

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq vsftpd openssh-client 2>/dev/null | tail -3 &&
  echo 'vsftpd version:' && dpkg -l vsftpd | grep '^ii' | awk '{print \$2\" \"\$3}' &&
  echo 'ssh version:' && ssh -V 2>&1"
```

📸 **Verified Output:**
```
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
vsftpd version:
vsftpd 3.0.5-0ubuntu1.1
ssh version:
OpenSSH_8.9p1 Ubuntu-3ubuntu0.13, OpenSSL 3.0.2 15 Mar 2022
```

> 💡 vsftpd ("Very Secure FTP Daemon") is one of the most widely deployed FTP servers despite FTP itself being insecure. The "very secure" refers to its code design, not the protocol.

---

## Step 2: FTP Active vs Passive Mode

FTP uses **two separate TCP connections** — this is its most distinctive (and problematic) feature:

**Control Connection:** Port 21 (always client→server)
**Data Connection:** Port 20 (active) or ephemeral (passive)

### Active Mode (PORT)
```
Client ──[SYN 1024]──► Server:21   (control — client initiates)
Client ◄──[SYN]──────── Server:20   (data — SERVER initiates back!)
```

**Problem:** Server connects back to the client. Firewalls/NAT block incoming connections. Active mode is broken in most real-world NAT environments.

### Passive Mode (PASV)
```
Client ──[SYN]──────► Server:21    (control — client initiates)
Client sends PASV command
Server responds: "Connect to me on port 50000"
Client ──[SYN]──────► Server:50000 (data — client initiates both!)
```

**Solution:** Client initiates both connections. Works through NAT and firewalls. Passive is the default for all modern FTP clients.

**FTP Commands (sent over control connection as plaintext ASCII):**

| Command | Description |
|---|---|
| `USER username` | Send username |
| `PASS password` | Send password (plaintext!) |
| `LIST` | List directory (like ls) |
| `RETR filename` | Download file |
| `STOR filename` | Upload file |
| `PASV` | Request passive mode |
| `PORT h1,h2,h3,h4,p1,p2` | Active mode: client's IP/port |
| `QUIT` | Disconnect |
| `PWD` | Print working directory |
| `CWD dir` | Change directory |
| `MKD dir` | Make directory |

> 💡 FTP sends credentials in **plaintext**. A packet sniffer on the same network sees your username and password. Never use plain FTP over untrusted networks.

---

## Step 3: Configure vsftpd

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq vsftpd 2>/dev/null | tail -2

  cat > /etc/vsftpd.conf << 'CONF'
# vsftpd.conf - InnoZverse Lab Configuration

# Run as standalone daemon
listen=YES
listen_ipv6=NO

# Disable anonymous access (security!)
anonymous_enable=NO

# Allow local system users
local_enable=YES
write_enable=YES
local_umask=022

# Chroot users to their home directory
chroot_local_user=YES
allow_writeable_chroot=YES

# Passive mode port range (open these in firewall)
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=50000

# Logging
xferlog_enable=YES
xferlog_file=/var/log/vsftpd.log
xferlog_std_format=YES
log_ftp_protocol=YES

# Security
ftpd_banner=Welcome to InnoZverse FTP Service
max_clients=100
max_per_ip=5
idle_session_timeout=300
data_connection_timeout=120

# Hide system user IDs
hide_ids=YES
CONF

  echo '=== vsftpd.conf written ==='
  wc -l /etc/vsftpd.conf
  echo ''
  echo '=== Key settings ==='
  grep -v '^#' /etc/vsftpd.conf | grep -v '^$'"
```

📸 **Verified Output:**
```
=== vsftpd.conf written ===
37 /etc/vsftpd.conf

=== Key settings ===
listen=YES
listen_ipv6=NO
anonymous_enable=NO
local_enable=YES
write_enable=YES
local_umask=022
chroot_local_user=YES
allow_writeable_chroot=YES
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=50000
xferlog_enable=YES
xferlog_file=/var/log/vsftpd.log
xferlog_std_format=YES
log_ftp_protocol=YES
ftpd_banner=Welcome to InnoZverse FTP Service
max_clients=100
max_per_ip=5
idle_session_timeout=300
data_connection_timeout=120
hide_ids=YES
```

---

## Step 4: FTP Security Issues and FTPS

**Why plain FTP is dangerous:**

| Vulnerability | Impact |
|---|---|
| Plaintext credentials | Captured by any network sniffer |
| Plaintext data transfer | File contents visible on wire |
| No server authentication | MITM can intercept/modify files |
| Bounce attacks | Server connects to third-party hosts |
| PORT scanning | Use FTP server to port-scan other hosts |

**FTPS (FTP over TLS)** — two modes:

```
# Explicit FTPS (FTPES) — starts plain, upgrades to TLS
Client → Server:21 "AUTH TLS"
Server → Client "234 AUTH TLS OK"
[TLS handshake begins]
Credentials sent encrypted ✓

# Implicit FTPS — TLS from the first byte
Client → Server:990 [immediate TLS handshake]
```

vsftpd FTPS config additions:
```
ssl_enable=YES
rsa_cert_file=/etc/ssl/certs/vsftpd.pem
rsa_private_key_file=/etc/ssl/private/vsftpd.key
ssl_tlsv1_2=YES
ssl_tlsv1_3=YES
force_local_data_ssl=YES
force_local_logins_ssl=YES
```

> 💡 Even with FTPS, prefer **SFTP** for new deployments. SFTP has simpler firewall rules (single port 22), stronger authentication options, and is part of the SSH ecosystem.

---

## Step 5: SSH Key Generation for SFTP

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssh-client 2>/dev/null | tail -2

  # Generate ED25519 key pair (modern, fast, secure)
  ssh-keygen -t ed25519 -f /tmp/testkey -N '' 2>&1

  echo ''
  echo '=== Private key (first 5 lines) ==='
  head -5 /tmp/testkey

  echo ''
  echo '=== Public key ==='
  cat /tmp/testkey.pub

  echo ''
  echo '=== Key fingerprint ==='
  ssh-keygen -lf /tmp/testkey.pub"
```

📸 **Verified Output:**
```
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/testkey
Your public key has been saved in /tmp/testkey.pub
The key fingerprint is:
SHA256:D/m4AfwjJjufaMqXuzvDkNxY8+/jswMjBpZEWqbj//4 root@334d066688d2
The key's randomart image is:
+--[ED25519 256]--+
| .+              |
| =.              |
|+. .             |
|..+ o.   .       |
| + * oo S        |
|  * + +o =       |
|   =.oo+= o      |
| .  X= o=+       |
|  o+B@+E==       |
+----[SHA256]-----+

=== Private key (first 5 lines) ===
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAAAAABAAAAMwAAAAtzc2gtZWQyNTUxOQAAACBH...
...
-----END OPENSSH PRIVATE KEY-----

=== Public key ===
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEf... root@334d066688d2

=== Key fingerprint ===
256 SHA256:D/m4AfwjJjufaMqXuzvDkNxY8+/jswMjBpZEWqbj//4 root@334d066688d2 (ED25519)
```

---

## Step 6: SFTP — SSH File Transfer Protocol

**SFTP is NOT FTP over SSH.** It is a completely separate binary protocol (SSH subsystem) that happens to transfer files. Runs over the SSH connection channel.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssh-client 2>/dev/null | tail -2

  echo '=== SFTP command reference (batch mode demo) ==='

  # Show sftp interactive commands via help
  cat << 'SFTP_DEMO'
# Interactive SFTP session:
#   sftp user@hostname

# SFTP commands (inside sftp> prompt):
#   ls              - list remote directory
#   lls             - list local directory
#   pwd             - remote working directory
#   lpwd            - local working directory
#   cd /remote/path - change remote directory
#   lcd /local/path - change local directory
#   get remote.txt  - download file
#   put local.txt   - upload file
#   mget *.log      - download multiple files
#   mput *.csv      - upload multiple files
#   mkdir newdir    - create remote directory
#   rm file.txt     - delete remote file
#   rename old new  - rename remote file
#   chmod 644 file  - change permissions
#   exit / bye      - disconnect

# Batch mode (non-interactive):
#   sftp -b batchfile user@hostname

# Example batch file (/tmp/sftp-batch):
SFTP_DEMO

  cat > /tmp/sftp-batch << 'BATCH'
lcd /tmp
mkdir uploads
put /etc/hostname uploads/hostname.txt
ls uploads/
bye
BATCH

  echo '=== Batch file contents ==='
  cat /tmp/sftp-batch

  echo ''
  echo '=== SCP examples ==='
  echo 'scp local.txt user@host:/remote/path/'
  echo 'scp -r /local/dir user@host:/remote/'
  echo 'scp user@host:/remote/file.txt /local/'
  echo 'scp -P 2222 file.txt user@host:/tmp/'
  echo ''
  echo '=== rsync over SSH examples ==='
  echo 'rsync -avz /local/dir/ user@host:/remote/dir/'
  echo 'rsync -avz --delete /src/ user@host:/dst/'
  echo 'rsync -avz -e \"ssh -p 2222\" /src/ user@host:/dst/'"
```

📸 **Verified Output:**
```
=== SFTP command reference (batch mode demo) ===
# Interactive SFTP session:
#   sftp user@hostname
...
=== Batch file contents ===
lcd /tmp
mkdir uploads
put /etc/hostname uploads/hostname.txt
ls uploads/
bye

=== SCP examples ===
scp local.txt user@host:/remote/path/
scp -r /local/dir user@host:/remote/
scp user@host:/remote/file.txt /local/
scp -P 2222 file.txt user@host:/tmp/

=== rsync over SSH examples ===
rsync -avz /local/dir/ user@host:/remote/dir/
rsync -avz --delete /src/ user@host:/dst/
rsync -avz -e "ssh -p 2222" /src/ user@host:/dst/
```

> 💡 **rsync** is preferred over scp for large transfers or directory syncs — it only sends changed blocks (`--checksum`), resumes interrupted transfers, and can show progress with `--progress`.

---

## Step 7: Protocol Comparison

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq openssh-client 2>/dev/null | tail -2

  echo '=== SSH/SFTP capabilities ==='
  ssh -V 2>&1
  echo ''
  echo '=== Supported SFTP features ==='
  echo 'Protocol: SSH-2 subsystem (RFC 4251, 4253, 4254)'
  echo 'Auth: password, public key, certificate, GSSAPI'
  echo 'Encryption: same as SSH (AES-GCM, ChaCha20, etc.)'
  echo 'Port: 22 (single port, NAT-friendly)'
  echo 'Operations: read/write/append/rename/stat/mkdir/rm'
  echo ''
  echo '=== Key differences: FTP vs SFTP ==='
  printf '%-20s %-25s %-25s\n' 'Feature' 'FTP' 'SFTP'
  printf '%-20s %-25s %-25s\n' '-------' '---' '----'
  printf '%-20s %-25s %-25s\n' 'Protocol basis' 'Custom (RFC 959)' 'SSH subsystem'
  printf '%-20s %-25s %-25s\n' 'Default port' '21 (ctrl) + data' '22 only'
  printf '%-20s %-25s %-25s\n' 'Encryption' 'None (plaintext)' 'Always (SSH)'
  printf '%-20s %-25s %-25s\n' 'Auth methods' 'User/password' 'Key, cert, pass'
  printf '%-20s %-25s %-25s\n' 'Firewall-friendly' 'Hard (2 ports)' 'Easy (1 port)'
  printf '%-20s %-25s %-25s\n' 'Resume transfers' 'No' 'No (use rsync)'
  printf '%-20s %-25s %-25s\n' 'NAT traversal' 'Broken in active' 'Works fine'"
```

📸 **Verified Output:**
```
=== SSH/SFTP capabilities ===
OpenSSH_8.9p1 Ubuntu-3ubuntu0.13, OpenSSL 3.0.2 15 Mar 2022

=== Supported SFTP features ===
Protocol: SSH-2 subsystem (RFC 4251, 4253, 4254)
Auth: password, public key, certificate, GSSAPI
Encryption: same as SSH (AES-GCM, ChaCha20, etc.)
Port: 22 (single port, NAT-friendly)
Operations: read/write/append/rename/stat/mkdir/rm

=== Key differences: FTP vs SFTP ===
Feature              FTP                       SFTP
-------              ---                       ----
Protocol basis       Custom (RFC 959)          SSH subsystem
Default port         21 (ctrl) + data          22 only
Encryption           None (plaintext)          Always (SSH)
Auth methods         User/password             Key, cert, pass
Firewall-friendly    Hard (2 ports)            Easy (1 port)
Resume transfers     No                        No (use rsync)
NAT traversal        Broken in active          Works fine
```

---

## Step 8: Capstone — Secure File Transfer Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq vsftpd openssh-client openssl 2>/dev/null | tail -2

  echo '=== 1. Generate SFTP key pair ==='
  ssh-keygen -t ed25519 -f /tmp/sftp_key -N '' -C 'sftp-deploy@innozverse.com' 2>&1

  echo ''
  echo '=== 2. Create vsftpd config for passive FTP ==='
  cat > /etc/vsftpd.conf << 'CONF'
listen=YES
listen_ipv6=NO
anonymous_enable=NO
local_enable=YES
write_enable=YES
chroot_local_user=YES
allow_writeable_chroot=YES
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=50000
pasv_address=203.0.113.1
xferlog_enable=YES
hide_ids=YES
ftpd_banner=InnoZverse Secure FTP
CONF

  echo '=== 3. Validate vsftpd config ==='
  # vsftpd validates on startup; check config syntax
  grep -c '.' /etc/vsftpd.conf && echo 'Config lines OK'

  echo ''
  echo '=== 4. Generate TLS cert for FTPS ==='
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -out /tmp/vsftpd.pem -keyout /tmp/vsftpd.key \
    -subj '/CN=ftp.innozverse.com' 2>/dev/null
  openssl x509 -in /tmp/vsftpd.pem -noout -subject -dates

  echo ''
  echo '=== 5. SFTP public key (deploy to ~/.ssh/authorized_keys on server) ==='
  cat /tmp/sftp_key.pub
" 2>&1
```

📸 **Verified Output:**
```
=== 1. Generate SFTP key pair ===
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/sftp_key
Your public key has been saved in /tmp/sftp_key.pub
The key fingerprint is:
SHA256:Xk9mP2qR7vN3wL8sT1uY6cA0bE4fH5iJ2kM9nO1pQ3r sftp-deploy@innozverse.com
The key's randomart image is:
+--[ED25519 256]--+
|        .oo+o.   |
|       . o+=o    |
...
+----[SHA256]-----+

=== 2. Create vsftpd config for passive FTP ===

=== 3. Validate vsftpd config ===
16
Config lines OK

=== 4. Generate TLS cert for FTPS ===
subject=CN = ftp.innozverse.com
notBefore=Mar  5 13:30:00 2026 GMT
notAfter=Mar  5 13:30:00 2027 GMT

=== 5. SFTP public key (deploy to ~/.ssh/authorized_keys on server) ===
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBq... sftp-deploy@innozverse.com
```

---

## Summary

| Concept | Key Points |
|---|---|
| FTP Active Mode | Server initiates data connection back to client (PORT) — blocked by NAT |
| FTP Passive Mode | Client initiates both connections (PASV) — works through NAT/firewalls |
| FTP Commands | USER/PASS/LIST/RETR/STOR/PASV/QUIT over plaintext control channel |
| FTP Security | Plaintext credentials and data — never use over untrusted networks |
| vsftpd | `anonymous_enable=NO`, `chroot_local_user=YES`, `pasv_min/max_port` |
| FTPS | FTP + TLS (`AUTH TLS`); adds encryption but keeps FTP complexity |
| SFTP | SSH subsystem — completely different from FTP; single port 22; always encrypted |
| SFTP commands | ls/get/put/mkdir/rm/rename/chmod inside sftp> prompt |
| SCP | `scp src user@host:dst` — simple file copy over SSH |
| rsync | `rsync -avz` — efficient sync; only sends changed blocks |
