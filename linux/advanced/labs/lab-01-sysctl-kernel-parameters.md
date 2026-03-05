# Lab 01: Kernel Parameter Tuning with sysctl

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

The Linux kernel exposes hundreds of tunable parameters through the `sysctl` interface and the `/proc/sys/` virtual filesystem. These parameters control networking, memory management, security hardening, and system behavior — all at runtime, without rebooting. This lab covers reading, modifying, and persisting kernel parameters safely.

---

## Step 1: Explore the /proc/sys/ Hierarchy

The `/proc/sys/` filesystem mirrors the sysctl namespace as a directory tree.

```bash
ls /proc/sys/
```

📸 **Verified Output:**
```
abi  debug  dev  fs  kernel  net  user  vm
```

Each subdirectory corresponds to a sysctl namespace:

```bash
ls /proc/sys/net/ipv4/ | head -10
```

📸 **Verified Output:**
```
conf
fib_multipath_hash_fields
fib_multipath_hash_policy
fib_multipath_hash_seed
fib_multipath_use_neigh
fib_notify_on_flag_change
fwmark_reflect
icmp_echo_enable_probe
icmp_echo_ignore_all
icmp_echo_ignore_broadcasts
```

> 💡 Every file under `/proc/sys/` maps 1:1 to a `sysctl` key — slashes become dots. So `/proc/sys/net/ipv4/ip_forward` → `net.ipv4.ip_forward`.

---

## Step 2: Read Parameters with sysctl -a

List all available kernel parameters (983+ on a typical system):

```bash
sysctl -a 2>/dev/null | wc -l
```

📸 **Verified Output:**
```
983
```

Read specific parameters:

```bash
sysctl net.ipv4.ip_forward
sysctl vm.swappiness
sysctl fs.file-max
sysctl kernel.panic
sysctl net.core.somaxconn
```

📸 **Verified Output:**
```
net.ipv4.ip_forward = 1
vm.swappiness = 60
fs.file-max = 9223372036854775807
kernel.panic = 0
net.core.somaxconn = 4096
```

> 💡 You can also read directly from `/proc/sys/`: `cat /proc/sys/net/ipv4/ip_forward` — the output is identical.

---

## Step 3: Understand Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `net.ipv4.ip_forward` | Enable IPv4 packet forwarding (routing) | `0` (off), `1` (on) |
| `vm.swappiness` | How aggressively kernel uses swap (0–100) | `60` default |
| `fs.file-max` | Max open file descriptors system-wide | varies |
| `kernel.panic` | Seconds before auto-reboot on panic (`0` = never) | `0` |
| `net.core.somaxconn` | Max TCP connection backlog per socket | `128`–`4096` |

Read security-relevant parameters:

```bash
sysctl -a 2>/dev/null | grep -E 'kernel\.(hostname|ostype|pid_max|dmesg_restrict|kptr_restrict|perf_event_paranoid|randomize_va_space)'
```

📸 **Verified Output:**
```
kernel.dmesg_restrict = 1
kernel.hostname = 0649ea85b24b
kernel.kptr_restrict = 1
kernel.ostype = Linux
kernel.perf_event_paranoid = 4
kernel.pid_max = 4194304
kernel.randomize_va_space = 2
```

> 💡 `kernel.randomize_va_space = 2` means full ASLR (Address Space Layout Randomization) is enabled — a key defense against exploit techniques.

---

## Step 4: Runtime Changes with sysctl -w

Changes made with `-w` take effect immediately but are **not** persistent across reboots:

```bash
# Check current swappiness
sysctl vm.swappiness

# Change it
sysctl -w vm.swappiness=10

# Verify
sysctl vm.swappiness
```

📸 **Verified Output:**
```
vm.swappiness = 60
vm.swappiness = 10
vm.swappiness = 10
```

You can also write directly to `/proc/sys/`:

```bash
echo 0 > /proc/sys/net/ipv4/ip_forward
cat /proc/sys/net/ipv4/ip_forward
```

📸 **Verified Output:**
```
0
```

> 💡 Direct writes to `/proc/sys/` and `sysctl -w` are equivalent. The proc interface is useful in scripts.

---

## Step 5: Persist Changes with sysctl.conf

Runtime changes vanish on reboot. To persist them, write to `/etc/sysctl.conf` or a drop-in file under `/etc/sysctl.d/`:

```bash
# Create a custom drop-in file
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-custom.conf
cat /etc/sysctl.d/99-custom.conf

# Apply it now
sysctl -p /etc/sysctl.d/99-custom.conf
```

📸 **Verified Output:**
```
net.ipv4.ip_forward=1
net.ipv4.ip_forward = 1
```

The `sysctl -p` command loads parameters from a file (default: `/etc/sysctl.conf`).

> 💡 Files in `/etc/sysctl.d/` are processed alphabetically. Use `99-` prefix so your overrides apply last, after any distro defaults.

---

## Step 6: Network Tuning Parameters

For high-throughput servers, tune these networking parameters:

```bash
# Show current network buffer sizes
sysctl net.core.rmem_max
sysctl net.core.wmem_max
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

📸 **Verified Output:**
```
net.core.rmem_max = 212992
net.core.wmem_max = 212992
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
```

A production web server config (`/etc/sysctl.d/99-network-tuning.conf`):

```ini
# Increase TCP backlog for high-traffic servers
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Larger socket buffers (256MB)
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456

# Enable IP forwarding (for routers/containers)
net.ipv4.ip_forward = 1
```

---

## Step 7: Security Hardening Parameters

Security-focused sysctl settings to harden a production system:

```bash
# View current security settings
sysctl kernel.dmesg_restrict
sysctl kernel.kptr_restrict
sysctl kernel.randomize_va_space
sysctl net.ipv4.conf.all.accept_redirects
```

A security hardening config (`/etc/sysctl.d/99-security.conf`):

```ini
# Prevent dmesg leaking kernel addresses to unprivileged users
kernel.dmesg_restrict = 1

# Hide kernel pointers from /proc (reduces exploit info)
kernel.kptr_restrict = 2

# Full ASLR (0=off, 1=partial, 2=full)
kernel.randomize_va_space = 2

# Disable ICMP redirect acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# SYN flood protection
net.ipv4.tcp_syncookies = 1

# Ignore broadcast pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0

# Log martian packets (unexpected source addresses)
net.ipv4.conf.all.log_martians = 1
```

> 💡 Run `sysctl -p /etc/sysctl.d/99-security.conf` to apply immediately, and it will auto-apply on next boot.

---

## Step 8: Capstone — Tune a Server for High Connections

**Scenario:** You're deploying a high-traffic API gateway. Apply and verify a complete tuning profile.

```bash
# Apply network performance tuning
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w vm.swappiness=10
sysctl -w kernel.panic=30

# Verify all changes
sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog vm.swappiness kernel.panic

# Persist to file
cat > /etc/sysctl.d/99-api-gateway.conf << 'EOF'
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
vm.swappiness = 10
kernel.panic = 30
net.ipv4.tcp_syncookies = 1
kernel.dmesg_restrict = 1
kernel.randomize_va_space = 2
EOF

sysctl -p /etc/sysctl.d/99-api-gateway.conf
```

📸 **Verified Output:**
```
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
vm.swappiness = 10
kernel.panic = 30
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
vm.swappiness = 10
kernel.panic = 30
net.ipv4.tcp_syncookies = 1
kernel.dmesg_restrict = 1
kernel.randomize_va_space = 2
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `sysctl -a` | List all kernel parameters |
| `sysctl <key>` | Read a single parameter |
| `sysctl -w <key>=<val>` | Set parameter at runtime (non-persistent) |
| `sysctl -p <file>` | Load parameters from a file |
| `cat /proc/sys/...` | Read parameter via filesystem |
| `echo val > /proc/sys/...` | Write parameter via filesystem |
| `/etc/sysctl.conf` | Default persistent config file |
| `/etc/sysctl.d/*.conf` | Drop-in config directory (preferred) |
| `sysctl -a \| grep <term>` | Search for parameters by name |
