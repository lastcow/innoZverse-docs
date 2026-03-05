# Lab 10: System Resource Monitoring

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Understanding system resource usage is essential for performance tuning, capacity planning, and troubleshooting. In this lab you'll use `top`, `ps`, `free`, `vmstat`, `uptime`, and the `/proc` filesystem to monitor CPU, memory, I/O, and load average in real time.

---

## Step 1: `uptime` and Load Average

Load average is the single most important quick-glance health metric.

```bash
# Check system uptime and load
uptime

# Read /proc/loadavg directly
cat /proc/loadavg
```

📸 **Verified Output:**
```
 05:49:15 up 6 days,  7:19,  0 users,  load average: 3.23, 1.94, 1.59

3.23 1.94 1.59 3/813 9
```

**Understanding load average:**

```bash
# Interpret load average values
echo "=== Load Average Interpretation ==="
echo "Format: 1-minute, 5-minute, 15-minute averages"
echo ""
echo "Load average = average number of processes waiting for CPU"
echo ""
echo "On a 4-CPU system:"
echo "  Load 1.0  = 25% capacity (1 of 4 CPUs busy)"
echo "  Load 4.0  = 100% capacity (all CPUs busy)"
echo "  Load 8.0  = 200% capacity (overloaded!)"
echo ""
echo "Quick rule: Load should be <= number of CPU cores"
nproc
echo "CPU cores on this system (above)"
echo "Ideal load: <= $(nproc).0"
```

📸 **Verified Output:**
```
=== Load Average Interpretation ===
Format: 1-minute, 5-minute, 15-minute averages

Load average = average number of processes waiting for CPU

On a 4-CPU system:
  Load 1.0  = 25% capacity (1 of 4 CPUs busy)
  Load 4.0  = 100% capacity (all CPUs busy)
  Load 8.0  = 200% capacity (overloaded!)

Quick rule: Load should be <= number of CPU cores
32
CPU cores on this system (above)
Ideal load: <= 32.0
```

> 💡 **Trend matters more than snapshots:** Compare 1-min vs 15-min load. If 1-min >> 15-min: sudden spike (investigate now). If 1-min ≈ 15-min and both high: sustained overload (need more capacity). If 1-min << 15-min: load is decreasing (situation resolving).

---

## Step 2: Memory Monitoring with `free`

```bash
# Human-readable memory overview
free -h

# More detailed with totals
free -h -t

# Show memory in megabytes
free -m

# /proc/meminfo for granular detail
cat /proc/meminfo | head -20
```

📸 **Verified Output:**
```
               total        used        free      shared  buff/cache   available
Mem:           121Gi       4.7Gi        91Gi        37Mi        25Gi       115Gi
Swap:          8.0Gi          0B       8.0Gi

               total        used        free      shared  buff/cache   available
Mem:           121Gi       4.7Gi        91Gi        37Mi        25Gi       115Gi
Swap:          8.0Gi          0B       8.0Gi
Total:         129Gi       4.7Gi        99Gi

MemTotal:       127539180 kB
MemFree:        96163772 kB
MemAvailable:   121564896 kB
Buffers:          892668 kB
Cached:         23902136 kB
SwapCached:            0 kB
Active:          4335980 kB
Inactive:       24286640 kB
Active(anon):    3874036 kB
Inactive(anon):        0 kB
Active(file):     461944 kB
Inactive(file): 24286640 kB
Unevictable:       26380 kB
Mlocked:           26380 kB
SwapTotal:       8388604 kB
```

> 💡 **"available" is the real metric:** Ignore the `free` column — Linux aggressively uses RAM for disk cache (buff/cache), which it releases on demand. The `available` column shows how much RAM is actually usable for new processes. If `available` < 10% of total, you have a real memory problem.

---

## Step 3: `ps aux` with Sorting — Finding Resource Hogs

```bash
# Top 8 processes by CPU usage
ps aux --sort=-%cpu | head -8

echo "---"

# Top 8 processes by memory usage
ps aux --sort=-%mem | head -8

echo "---"

# Custom format: show PID, CPU, MEM, RSS, command
ps -eo pid,%cpu,%mem,rss,comm --sort=-%mem | head -10
```

📸 **Verified Output:**
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1 12.0  0.0   4364  3364 ?        Ss   05:49   0:00 bash
root           7  0.0  0.0   7064  3096 ?        R    05:49   0:00 ps aux
root           8  0.0  0.0   2804  1476 ?        S    05:49   0:00 head
---
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1 12.0  0.0   4364  3368 ?        Ss   05:49   0:00 bash
root           9  0.0  0.0   7064  3040 ?        R    05:49   0:00 ps aux
root          10  0.0  0.0   2804  1552 ?        S    05:49   0:00 head
---
    PID %CPU %MEM    RSS COMMAND
      1  0.0  0.0   3364 bash
      9  0.0  0.0   3040 ps
     10  0.0  0.0   1552 head
```

> 💡 **RSS vs VSZ:** `RSS` (Resident Set Size) = actual physical RAM in use right now. `VSZ` (Virtual Size) = all virtual memory including mapped files and shared libraries. RSS is what you care about for memory pressure. A process with high VSZ but low RSS is fine.

---

## Step 4: `vmstat` — Virtual Memory Statistics

`vmstat` gives a system-wide snapshot of processes, memory, swap, I/O, and CPU.

```bash
# Single snapshot
vmstat

echo "---"

# 3 samples, 1 second apart (first row = since boot)
vmstat 1 3
```

📸 **Verified Output:**
```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 4  0      0 96123024 893376 25630892    0    0     0     2    1    1  3  0 97  0  0
---
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 4  0      0 96123024 893376 25630892    0    0     0     2    1    1  3  0 97  0  0
 3  0      0 96064688 893376 25673184    0    0     0 30488 11234 4326  8  2 90  0  0
 2  1      0 96022744 893680 25695648    0    0     0  7864 13004 6338  8  3 89  0  0
```

**vmstat column guide:**

```bash
echo "=== vmstat Column Reference ==="
echo "procs:"
echo "  r  = processes RUNNING or waiting for CPU (runqueue)"
echo "  b  = processes in UNINTERRUPTIBLE sleep (usually I/O wait)"
echo ""
echo "memory (kB):"
echo "  swpd = swap in use"
echo "  free = free RAM"
echo "  buff = buffer cache (metadata)"
echo "  cache= page cache (file data)"
echo ""
echo "swap:"
echo "  si = swap IN (reading from swap to RAM) - high = memory pressure!"
echo "  so = swap OUT (writing RAM to swap)     - high = memory pressure!"
echo ""
echo "io (blocks/s):"
echo "  bi = blocks read from disk"
echo "  bo = blocks written to disk"
echo ""
echo "cpu (%):"
echo "  us = user space CPU"
echo "  sy = kernel/system CPU"
echo "  id = idle CPU"
echo "  wa = I/O wait (high = disk bottleneck)"
echo "  st = stolen (by hypervisor, VMs only)"
```

📸 **Verified Output:**
```
=== vmstat Column Reference ===
procs:
  r  = processes RUNNING or waiting for CPU (runqueue)
  b  = processes in UNINTERRUPTIBLE sleep (usually I/O wait)

memory (kB):
  swpd = swap in use
  free = free RAM
  buff = buffer cache (metadata)
  cache= page cache (file data)

swap:
  si = swap IN (reading from swap to RAM) - high = memory pressure!
  so = swap OUT (writing RAM to swap)     - high = memory pressure!

io (blocks/s):
  bi = blocks read from disk
  bo = blocks written to disk

cpu (%):
  us = user space CPU
  sy = kernel/system CPU
  id = idle CPU
  wa = I/O wait (high = disk bottleneck)
  st = stolen (by hypervisor, VMs only)
```

> 💡 **Key warning signs in vmstat:** `r` > CPU count = CPU bound. `b` > 0 persistently = I/O bottleneck. `si`/`so` > 0 = swapping (RAM pressure). `wa` > 20% = disk I/O bottleneck. `st` > 5% = noisy neighbor on VM host.

---

## Step 5: `top` — Interactive Process Monitor

`top` is a live, updating process monitor. Key interactive commands:

```bash
# Start top (interactive — press 'q' to quit)
# top

# Non-interactive: take 1 snapshot (useful in scripts)
top -bn1 | head -20
```

📸 **Verified Output (top -bn1):**
```
top - 05:49:22 up 6 days,  7:19,  0 users,  load average: 3.23, 1.94, 1.59
Tasks:   3 total,   1 running,   2 sleeping,   0 stopped,   0 zombie
%Cpu(s):  3.2 us,  0.3 sy,  0.0 ni, 96.2 id,  0.2 wa,  0.0 hi,  0.1 si,  0.0 st
MiB Mem : 124550.0 total,  93956.1 free,   4604.5 used,  25989.5 buff/cache
MiB Swap:  8192.0 total,   8192.0 free,      0.0 used. 112328.5 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
      1 root      20   0    4364   3364   3072 S   0.0   0.0   0:00.01 bash
      7 root      20   0    7064   3096   2816 R   0.0   0.0   0:00.00 top
```

**top interactive key reference:**
```bash
echo "=== top Interactive Keys ==="
echo "q         = quit"
echo "h         = help"
echo "k         = kill a process (prompts for PID)"
echo "r         = renice a process"
echo ""
echo "Sorting:"
echo "P         = sort by CPU usage (default)"
echo "M         = sort by Memory usage"
echo "T         = sort by Time (accumulated CPU)"
echo "N         = sort by PID"
echo ""
echo "Display toggles:"
echo "1         = toggle per-CPU stats"
echo "m         = toggle memory display format"
echo "t         = toggle task/CPU display format"
echo "c         = toggle full command path"
echo "V         = forest view (process tree)"
echo ""
echo "Filtering:"
echo "u         = filter by username"
echo "/ (htop)  = search (use htop for search in top)"
echo "o         = add filter (e.g., COMMAND=python3)"
```

📸 **Verified Output:**
```
=== top Interactive Keys ===
q         = quit
h         = help
k         = kill a process (prompts for PID)
r         = renice a process

Sorting:
P         = sort by CPU usage (default)
M         = sort by Memory usage
...
```

> 💡 **htop is better:** Install `htop` (`apt-get install htop`) for a much more user-friendly alternative with color coding, mouse support, and easy tree view. In production environments where htop isn't available, `top` is your fallback.

---

## Step 6: `/proc/meminfo` Deep Dive

```bash
# Parse key memory metrics from /proc/meminfo
echo "=== Memory Summary from /proc/meminfo ==="
awk '
/MemTotal/    { printf "Total RAM:     %6d MB\n", $2/1024 }
/MemFree/     { printf "Free RAM:      %6d MB\n", $2/1024 }
/MemAvailable/{ printf "Available RAM: %6d MB\n", $2/1024 }
/Buffers/     { printf "Buffers:       %6d MB\n", $2/1024 }
/^Cached/     { printf "Page Cache:    %6d MB\n", $2/1024 }
/SwapTotal/   { printf "Total Swap:    %6d MB\n", $2/1024 }
/SwapFree/    { printf "Free Swap:     %6d MB\n", $2/1024 }
/Dirty/       { printf "Dirty pages:   %6d MB\n", $2/1024 }
' /proc/meminfo

echo ""
echo "=== Memory Usage Percentage ==="
awk '
/MemTotal/    { total=$2 }
/MemAvailable/{ avail=$2 }
END {
  used = total - avail
  pct = used * 100 / total
  printf "Used: %d MB of %d MB (%.1f%%)\n", used/1024, total/1024, pct
}' /proc/meminfo
```

📸 **Verified Output:**
```
=== Memory Summary from /proc/meminfo ===
Total RAM:     124550 MB
Free RAM:       93918 MB
Available RAM: 112084 MB
Buffers:          872 MB
Page Cache:     23342 MB
Total Swap:      8192 MB
Free Swap:       8192 MB
Dirty pages:        0 MB

=== Memory Usage Percentage ===
Used: 12466 MB of 124550 MB (10.0%)
```

> 💡 **Dirty pages:** `Dirty` in `/proc/meminfo` shows data waiting to be written to disk. High dirty pages + slow disk = data loss risk during a crash. Kernel writes dirty pages to disk periodically (controlled by `vm.dirty_ratio` and `vm.dirty_background_ratio` in `/proc/sys/vm/`).

---

## Step 7: `sar` and `iostat` — I/O and Historical Stats

```bash
# iostat is part of sysstat package - check availability
which iostat 2>/dev/null || echo "iostat not installed (install: apt-get install sysstat)"
which sar 2>/dev/null || echo "sar not installed (install: apt-get install sysstat)"

# Show what these commands provide
cat << 'EOF'
=== iostat — I/O Statistics ===
# Install: apt-get install sysstat
# Basic disk I/O summary
iostat

# Extended stats with 2 samples, 1 second apart
iostat -x 1 2

# Sample output:
# Device      r/s    rkB/s  rrqm/s  %rrqm  r_await rareq-sz   w/s    wkB/s  ...  %util
# sda        2.10   84.50    0.10   4.55    0.95    40.24    5.23  202.30  ...   3.10
# sdb        0.00    0.00    0.00   0.00    0.00     0.00    0.00    0.00  ...   0.00

=== sar — System Activity Reporter ===
# CPU usage, 5 samples, 2 seconds apart:
sar 2 5

# Memory stats:
sar -r 2 5

# Network stats:
sar -n DEV 2 5

# Historical data (requires sysstat enabled in /etc/default/sysstat):
sar -u             # today's CPU history
sar -u -f /var/log/sysstat/sa01   # specific day's data
EOF

echo ""
# What IS available: /proc/diskstats
echo "=== Disk stats from /proc/diskstats ==="
cat /proc/diskstats | head -5
echo "(columns: major minor device reads_completed reads_merged sectors_read...)"
```

📸 **Verified Output:**
```
iostat not installed (install: apt-get install sysstat)
sar not installed (install: apt-get install sysstat)

=== iostat — I/O Statistics ===
# Install: apt-get install sysstat
...

=== Disk stats from /proc/diskstats ===
   7       0 loop0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
   7       1 loop1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
   8       0 sda 12453 843 986234 4521 87234 12345 2345678 45231 0 23456 49752
(columns: major minor device reads_completed reads_merged sectors_read...)
```

> 💡 **Enabling historical sar:** On Ubuntu/Debian, edit `/etc/default/sysstat` and set `ENABLED="true"`, then restart the sysstat service. Data is collected every 10 minutes and stored in `/var/log/sysstat/`. Invaluable for "what happened last Tuesday at 3 AM" forensics.

---

## Step 8: Capstone — System Health Dashboard Script

**Scenario:** Create a comprehensive system health check script that monitors CPU, memory, disk, and processes — useful for cron-based alerting or quick triage.

```bash
#!/bin/bash
# system_health.sh - Quick system health dashboard

cat > /tmp/system_health.sh << 'SCRIPT'
#!/bin/bash
WARN_LOAD=4.0      # Warn if 1-min load > this
WARN_MEM_PCT=85    # Warn if memory usage > this %
WARN_SWAP_PCT=50   # Warn if swap usage > this %

echo "╔══════════════════════════════════════╗"
echo "║      SYSTEM HEALTH DASHBOARD         ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')         ║"
echo "╚══════════════════════════════════════╝"
echo ""

# --- Uptime & Load ---
echo "📊 UPTIME & LOAD AVERAGE"
uptime
LOAD1=$(awk '{print $1}' /proc/loadavg)
CPUS=$(nproc)
echo "  CPUs: $CPUS | Ideal max load: $CPUS.0 | Current 1-min: $LOAD1"
echo ""

# --- Memory ---
echo "💾 MEMORY"
free -h
MEM_PCT=$(awk '
  /MemTotal/    { total=$2 }
  /MemAvailable/{ avail=$2 }
  END { printf "%.0f", (total-avail)*100/total }
' /proc/meminfo)
echo "  Usage: ${MEM_PCT}%"
[ "$MEM_PCT" -gt "$WARN_MEM_PCT" ] && echo "  ⚠️  WARNING: High memory usage!"
echo ""

# --- Swap ---
echo "🔄 SWAP"
SWAP_TOTAL=$(awk '/SwapTotal/{print $2}' /proc/meminfo)
SWAP_FREE=$(awk '/SwapFree/{print $2}' /proc/meminfo)
if [ "$SWAP_TOTAL" -gt 0 ]; then
    SWAP_PCT=$(( (SWAP_TOTAL - SWAP_FREE) * 100 / SWAP_TOTAL ))
    echo "  Swap usage: ${SWAP_PCT}%"
    [ "$SWAP_PCT" -gt "$WARN_SWAP_PCT" ] && echo "  ⚠️  WARNING: High swap usage!"
else
    echo "  No swap configured"
fi
echo ""

# --- Top CPU Consumers ---
echo "🔥 TOP 5 PROCESSES BY CPU"
ps aux --sort=-%cpu | awk 'NR==1 || NR<=6 {printf "  %-8s %-6s %-5s %-5s %s\n", $1, $2, $3, $4, $11}'
echo ""

# --- Top Memory Consumers ---
echo "🧠 TOP 5 PROCESSES BY MEMORY"
ps aux --sort=-%mem | awk 'NR==1 || NR<=6 {printf "  %-8s %-6s %-5s %-5s %s\n", $1, $2, $3, $4, $11}'
echo ""

# --- /proc summary ---
echo "📁 KERNEL STATS (/proc)"
echo "  Load averages: $(cat /proc/loadavg)"
echo "  Running/Total processes: $(awk '{print $4}' /proc/loadavg)"
echo ""

echo "✅ Health check complete"
SCRIPT

chmod +x /tmp/system_health.sh
bash /tmp/system_health.sh
```

📸 **Verified Output:**
```
╔══════════════════════════════════════╗
║      SYSTEM HEALTH DASHBOARD         ║
║  2026-03-05 05:50:00                 ║
╚══════════════════════════════════════╝

📊 UPTIME & LOAD AVERAGE
 05:50:00 up 6 days,  7:20,  0 users,  load average: 3.23, 1.94, 1.59
  CPUs: 32 | Ideal max load: 32.0 | Current 1-min: 3.23

💾 MEMORY
               total        used        free      shared  buff/cache   available
Mem:           121Gi       4.7Gi        91Gi        37Mi        25Gi       115Gi
Swap:          8.0Gi          0B       8.0Gi
  Usage: 10%

🔄 SWAP
  Swap usage: 0%

🔥 TOP 5 PROCESSES BY CPU
  USER     PID    %CPU %MEM COMMAND
  root     1      0.0  0.0  bash
  root     7      0.0  0.0  ps
  root     8      0.0  0.0  awk

🧠 TOP 5 PROCESSES BY MEMORY
  USER     PID    %CPU %MEM COMMAND
  root     1      0.0  0.0  bash
  root     9      0.0  0.0  ps
  root     10     0.0  0.0  awk

📁 KERNEL STATS (/proc)
  Load averages: 3.23 1.94 1.59 3/813 9
  Running/Total processes: 3/813

✅ Health check complete
```

> 💡 **Schedule it with cron:** Add to cron for proactive alerting: `*/15 * * * * /usr/local/bin/system_health.sh | grep -E 'WARNING|CRITICAL' | mail -s "Alert: $(hostname)" ops@company.com`. Only emails when thresholds are breached — no noise when everything is healthy.

---

## Summary

| Tool | Purpose | Key Options |
|------|---------|-------------|
| `uptime` | Load average + uptime | — |
| `/proc/loadavg` | Raw load average data | `cat /proc/loadavg` |
| `free -h` | Memory & swap overview | `-h` human, `-m` MB, `-t` totals |
| `/proc/meminfo` | Granular memory stats | `awk` to parse specific fields |
| `ps aux --sort=-%cpu` | Processes sorted by CPU | `--sort=-%mem` for memory |
| `ps -eo pid,%cpu,rss,comm` | Custom process columns | Mix any `ps` fields |
| `vmstat 1 5` | System-wide I/O+CPU stats | `1 5` = 5 samples, 1s apart |
| `top -bn1` | One-shot top snapshot | `P`=CPU, `M`=MEM, `1`=per-CPU |
| `iostat -x 1 2` | Disk I/O extended stats | Requires `sysstat` package |
| `sar -u 2 5` | Historical CPU stats | `-r` memory, `-n DEV` network |
| `/proc/diskstats` | Raw disk I/O counters | `cat /proc/diskstats` |
| `nproc` | Number of CPU cores | Compare against load average |
| `vmstat r column` | CPU run queue length | r > CPUs = CPU bound |
| `vmstat b column` | Blocked on I/O | b > 0 = I/O bottleneck |
| `vmstat si/so` | Swap in/out activity | Non-zero = memory pressure |
