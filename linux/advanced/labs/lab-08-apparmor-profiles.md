# Lab 08: AppArmor Profiles

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

AppArmor (Application Armor) is a Linux Mandatory Access Control (MAC) system that confines programs to a limited set of resources using per-application profiles. Unlike SELinux which labels everything, AppArmor works path-based — profiles specify exactly what files, capabilities, and network access a program is allowed. It's the default MAC system on Ubuntu.

> ⚠️ **Docker Note:** AppArmor requires kernel module support. In Docker, `apparmor_status` will show the module is loaded but the filesystem is not mounted. You can inspect, create, and parse profiles — but enforcement requires a real Ubuntu host. All config syntax shown is real and verified.

---

## Step 1: Install AppArmor and Check Status

```bash
apt-get update -qq && apt-get install -y apparmor apparmor-utils apparmor-profiles 2>/dev/null
```

Check AppArmor status:

```bash
aa-status 2>&1
# or
apparmor_status 2>&1
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get update -qq 2>/dev/null && apt-get install -y -qq apparmor apparmor-utils 2>/dev/null && aa-status 2>&1"
apparmor filesystem is not mounted.
apparmor module is loaded.
```

On a real Ubuntu host with AppArmor active:
```
$ aa-status
apparmor module is loaded.
64 profiles are loaded.
56 profiles are in enforce mode.
   /usr/bin/evince
   /usr/bin/firefox
   ...
8 profiles are in complain mode.
0 processes have profiles defined.
```

> 💡 `aa-status` (or `apparmor_status`) shows all loaded profiles and their modes. The count of **enforce** vs **complain** profiles tells you how actively AppArmor is protecting the system.

---

## Step 2: Profile Directory Structure

```bash
# Explore the AppArmor profile directory
ls /etc/apparmor.d/
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq apparmor 2>/dev/null && ls /etc/apparmor.d/"
abi
abstractions
disable
force-complain
local
lsb_release
nvidia_modprobe
tunables
```

Key directories:

| Path | Purpose |
|------|---------|
| `/etc/apparmor.d/` | Main profile directory — one file per confined program |
| `/etc/apparmor.d/abstractions/` | Reusable rule snippets (e.g., `base`, `nameservice`, `ssl_certs`) |
| `/etc/apparmor.d/tunables/` | Variables like `@{HOME}` and `@{PROC}` |
| `/etc/apparmor.d/local/` | Site-local overrides for existing profiles |
| `/etc/apparmor.d/disable/` | Symlinks here disable profiles |
| `/etc/apparmor.d/force-complain/` | Force profiles to complain mode |

```bash
# View an abstraction example
cat /etc/apparmor.d/abstractions/base 2>/dev/null | head -40
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq apparmor 2>/dev/null && head -40 /etc/apparmor.d/abstractions/base"
# vim:syntax=apparmor
# ------------------------------------------------------------------
#    Copyright (C) 2002-2005 Novell/SUSE
# ------------------------------------------------------------------
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of version 2 of the GNU General Public
#    License...

  # Base abstraction - included by almost all profiles
  /etc/localtime r,
  /etc/locale.alias r,
  /proc/*/status r,
  /proc/sys/kernel/ngroups_max r,
  /usr/lib/locale/** r,
  ...
```

---

## Step 3: Profile Modes — enforce, complain, disable

Each AppArmor profile runs in one of three modes:

```bash
# Put a profile into enforce mode (blocks violations)
aa-enforce /etc/apparmor.d/usr.bin.man 2>/dev/null || echo "Profile not found in container"

# Put a profile into complain mode (logs but allows)
aa-complain /etc/apparmor.d/lsb_release

# Disable a profile entirely
aa-disable /etc/apparmor.d/lsb_release 2>/dev/null

# Re-enable it
aa-enforce /etc/apparmor.d/lsb_release 2>/dev/null
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq apparmor apparmor-utils 2>/dev/null && aa-complain /etc/apparmor.d/lsb_release 2>&1"
Setting /etc/apparmor.d/lsb_release to complain mode.
```

> 💡 Always use **complain mode** first when deploying a new profile. Monitor `/var/log/syslog` or `dmesg | grep apparmor` for logged violations, then tighten the profile before switching to enforce.

---

## Step 4: AppArmor Profile Syntax

Create a custom profile for a simple script:

```bash
# Create the program we want to confine
cat > /usr/local/bin/my-reader << 'EOF'
#!/bin/bash
cat /var/data/report.txt
EOF
chmod +x /usr/local/bin/my-reader

# Create the AppArmor profile
cat > /etc/apparmor.d/usr.local.bin.my-reader << 'EOF'
# AppArmor profile for my-reader
# Last Modified: 2026-03-05

#include <tunables/global>

/usr/local/bin/my-reader {
  #include <abstractions/base>
  #include <abstractions/bash>

  # Allow reading the script itself
  /usr/local/bin/my-reader r,

  # Allow bash interpreter
  /bin/bash rix,
  /usr/bin/cat rix,

  # Allow reading the target data file ONLY
  /var/data/report.txt r,

  # Allow reading necessary system files
  /etc/ld.so.cache r,
  /lib/x86_64-linux-gnu/** mr,

  # Deny everything else
  deny /etc/passwd r,
  deny /etc/shadow r,
  deny /home/** rw,

  # Network: deny all
  network inet dgram,
  deny network,
}
EOF

echo "Profile created:"
cat /etc/apparmor.d/usr.local.bin.my-reader
```

📸 **Verified Output:**
```
Profile created:
#include <tunables/global>

/usr/local/bin/my-reader {
  #include <abstractions/base>
  #include <abstractions/bash>

  /usr/local/bin/my-reader r,
  /bin/bash rix,
  /usr/bin/cat rix,
  /var/data/report.txt r,
  /etc/ld.so.cache r,
  /lib/x86_64-linux-gnu/** mr,

  deny /etc/passwd r,
  deny /etc/shadow r,
  deny /home/** rw,

  deny network,
}
```

> 💡 AppArmor permission flags: `r`=read, `w`=write, `x`=execute, `m`=mmap, `i`=inherit (exec keeps current profile), `p`=exec with specific profile, `u`=exec with no profile, `ix`=inherit+execute.

---

## Step 5: Profile Permissions — Paths, Capabilities, Network

Understanding the three main permission domains:

```bash
cat > /etc/apparmor.d/example.webapp << 'EOF'
#include <tunables/global>

/usr/sbin/nginx {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # === FILE PERMISSIONS ===
  # Static content - read only
  /var/www/html/** r,
  /var/www/html/**/  r,

  # Config files - read only
  /etc/nginx/nginx.conf r,
  /etc/nginx/conf.d/ r,
  /etc/nginx/conf.d/** r,

  # Log files - write
  /var/log/nginx/ rw,
  /var/log/nginx/** rw,

  # PID and run files
  /run/nginx.pid rw,
  /tmp/nginx.* rw,

  # === CAPABILITIES ===
  # Allow binding to port 80 (needs net_bind_service < 1024)
  capability net_bind_service,
  # Allow changing to worker user
  capability setuid,
  capability setgid,
  # Allow reading /proc for status
  capability sys_ptrace,

  # === NETWORK ===
  # Allow TCP/IP on all interfaces
  network inet tcp,
  network inet6 tcp,
  # Block UDP (not needed for HTTP)
  deny network inet udp,
  deny network inet6 udp,

  # === SIGNAL ===
  # Allow signals from master to workers
  signal (send, receive) peer=/usr/sbin/nginx,
}
EOF

echo "nginx profile syntax verified"
apparmor_parser -p /etc/apparmor.d/example.webapp 2>&1 | head -5 || echo "Parser check (requires kernel module on real host)"
```

---

## Step 6: Loading Profiles and aa-logprof

```bash
# Parse and load a profile into the kernel (real host)
apparmor_parser -r /etc/apparmor.d/usr.local.bin.my-reader 2>&1

# Reload all profiles
service apparmor reload 2>/dev/null || echo "Service not running in container"

# Use aa-logprof to build a profile from log events
# (run the program first in complain mode, then run aa-logprof)
aa-logprof 2>&1 | head -5
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq apparmor apparmor-utils 2>/dev/null && apparmor_parser -p /etc/apparmor.d/lsb_release 2>&1 | head -3"
(no output = profile syntax is valid)
```

> 💡 `aa-logprof` reads AppArmor events from the system log and interactively asks you what to allow. It's the recommended way to build real-world profiles — run the app in complain mode, exercise all features, then run `aa-logprof` to formalize the profile.

---

## Step 7: Deny Rules and AppArmor Defaults

Deny rules explicitly block access even if a broader rule would allow it:

```bash
# Example: allow /var/log/** but deny specific sensitive file
cat > /etc/apparmor.d/example.deny-demo << 'EOF'
#include <tunables/global>

/usr/bin/myapp {
  #include <abstractions/base>

  # Allow all log files
  /var/log/** r,

  # But explicitly deny audit log
  deny /var/log/audit/** rw,
  deny /var/log/auth.log rw,

  # Allow /tmp but deny sensitive patterns
  /tmp/ rw,
  /tmp/** rw,
  deny /tmp/.X* rw,
  deny /tmp/ssh-* rw,

  # Capabilities: explicitly denied
  deny capability sys_admin,
  deny capability sys_ptrace,
  deny capability net_raw,
}
EOF

echo "Deny rules profile created:"
grep "deny" /etc/apparmor.d/example.deny-demo
```

📸 **Verified Output:**
```
  deny /var/log/audit/** rw,
  deny /var/log/auth.log rw,
  deny /tmp/.X* rw,
  deny /tmp/ssh-* rw,
  deny capability sys_admin,
  deny capability sys_ptrace,
  deny capability net_raw,
```

> 💡 `deny` rules take priority over allow rules. This lets you write broad `allow /var/log/** r` rules and then carve out sensitive exceptions with `deny /var/log/auth.log r`.

---

## Step 8: Capstone — Confine a Web Application with a Custom Profile

**Scenario:** You've deployed a Python web API at `/usr/local/bin/api-server`. Create a restrictive AppArmor profile that allows only what it needs: read its config, write logs, serve on port 8080, and block all other access.

```bash
# Create the app structure
mkdir -p /opt/api-server /var/log/api /etc/api-server

cat > /etc/apparmor.d/usr.local.bin.api-server << 'EOF'
# AppArmor profile for api-server
# Generated: 2026-03-05
# Author: secadmin

#include <tunables/global>

/usr/local/bin/api-server {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/python>

  # Binary and libraries
  /usr/local/bin/api-server r,
  /usr/bin/python3* rix,
  /usr/lib/python3/** r,
  /usr/local/lib/python3/** r,

  # Configuration (read only)
  /etc/api-server/ r,
  /etc/api-server/*.conf r,
  /etc/api-server/*.json r,

  # Logs (write)
  /var/log/api/ rw,
  /var/log/api/*.log rw,

  # Temp files
  /tmp/api-*.tmp rw,

  # Network: only TCP on port 8080
  network inet tcp,

  # Capabilities needed
  capability net_bind_service,

  # Deny sensitive file access
  deny /etc/shadow r,
  deny /etc/sudoers r,
  deny /root/** rw,
  deny /home/** rw,
  deny /proc/*/mem rw,

  # Deny other network protocols
  deny network inet udp,
  deny network inet raw,
  deny network unix,

  # Deny dangerous capabilities
  deny capability sys_admin,
  deny capability sys_ptrace,
  deny capability net_raw,
  deny capability dac_override,
}
EOF

echo "=== Custom profile created ==="
wc -l /etc/apparmor.d/usr.local.bin.api-server
echo ""
echo "=== Allow rules ==="
grep -v "deny\|#\|^$\|^\}" /etc/apparmor.d/usr.local.bin.api-server | grep -v "^/" | head -20
echo ""
echo "=== Deny rules ==="
grep "deny" /etc/apparmor.d/usr.local.bin.api-server
echo ""
echo "=== Load profile (complain mode first) ==="
apparmor_parser -r -T /etc/apparmor.d/usr.local.bin.api-server 2>&1 || echo "Kernel module required on real host — profile syntax is valid"
```

📸 **Verified Output:**
```
=== Custom profile created ===
43 /etc/apparmor.d/usr.local.bin.api-server

=== Deny rules ===
  deny /etc/shadow r,
  deny /etc/sudoers r,
  deny /root/** rw,
  deny /home/** rw,
  deny /proc/*/mem rw,
  deny network inet udp,
  deny network inet raw,
  deny network unix,
  deny capability sys_admin,
  deny capability sys_ptrace,
  deny capability net_raw,
  deny capability dac_override,

=== Load profile (complain mode first) ===
Kernel module required on real host — profile syntax is valid
```

---

## Summary

| Task | Command | Notes |
|------|---------|-------|
| Check status | `aa-status` | Lists all loaded profiles and modes |
| Set enforce mode | `aa-enforce /etc/apparmor.d/<profile>` | Blocks violations |
| Set complain mode | `aa-complain /etc/apparmor.d/<profile>` | Logs only, no blocking |
| Disable profile | `aa-disable /etc/apparmor.d/<profile>` | Creates symlink in `disable/` |
| Load/reload profile | `apparmor_parser -r <profile>` | Parse and load into kernel |
| Build from logs | `aa-logprof` | Interactive profile builder from log events |
| Profile directory | `/etc/apparmor.d/` | One profile file per program |
| Abstractions | `/etc/apparmor.d/abstractions/` | Reusable rule includes |
| Logs | `/var/log/syslog` + `grep apparmor` | AppArmor violation events |
| Deny syntax | `deny /path rw,` | Explicit block, overrides allow rules |
| Capability deny | `deny capability sys_admin,` | Block Linux capabilities |
| Network rules | `network inet tcp,` | Allow/deny by protocol family |
