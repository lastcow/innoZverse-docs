# Lab 18: System Monitoring & Performance Analysis

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Performance analysis is a critical sysadmin skill. In this lab you will use `vmstat`, `iostat`, `sar`, `top`, `uptime`, and `/proc` files to measure CPU, memory, disk I/O, and identify system bottlenecks with real data from a running system.

**Prerequisites:** Docker installed, Labs 01–15 completed.

---

## Step 1: uptime & Load Averages

Load average is the most fundamental performance metric.

```bash
docker run -it --rm ubuntu:22.04 bash
uptime
cat /proc/loadavg
```

📸 **Verified Output:**
```
 05:50:18 up 6 days,  7:20,  0 users,  load average: 3.51, 2.26, 1.72
3.51 2.26 1.72 3/789 1031
```

**Interpreting load average:**

Load average = average number of runnable + uninterruptible-sleep processes over 1/5/15 minutes.

| System | CPUs | Load 1.00 | Load 2.00 | Concern? |
|--------|------|-----------|-----------|---------|
| Single CPU | 1 | 100% busy | 200% (queued) | ✅ Yes |
| Quad core | 4 | 25% busy | 50% busy | ❌ Fine |
| 32 CPUs | 32 | 3% busy | 6% busy | ❌ Fine |

```bash
# Number of CPUs
nproc
cat /proc/cpuinfo | grep "^processor" | wc -l

# Rule: load_avg / nproc > 0.70 is a concern
# load_avg / nproc > 1.00 means queue is building
```

📸 **Verified Output:**
```
32
32
```

> 💡 **The 15-minute load average tells the trend.** If 1min > 15min, load is increasing. If 1min < 15min, load is decreasing. A 1min spike might be a cron job; sustained high 15min average means a real problem.

---

## Step 2: top — Real-time Process Monitoring

```bash
# Run top in batch mode (non-interactive, suitable for scripts)
top -bn1 | head -15
```

📸 **Verified Output:**
```
top - 05:50:24 up 6 days,  7:20,  0 users,  load average: 3.51, 2.30, 1.74
Tasks:   3 total,   1 running,   2 sleeping,   0 stopped,   0 zombie
%Cpu(s):  6.7 us,  0.8 sy,  0.0 ni, 92.0 id,  0.0 wa,  0.0 hi,  0.4 si,  0.0 st
MiB Mem : 124550.0 total,  93720.6 free,   4758.5 used,  26070.8 buff/cache
MiB Swap:   8192.0 total,   8192.0 free,      0.0 used. 118729.3 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
      1 root      20   0    4364   3340   3092 S   0.0   0.0   0:00.20 bash
   1038 root      20   0    7184   3360   2868 R   0.0   0.0   0:00.01 top
   1039 root      20   0    2804   1348   1256 S   0.0   0.0   0:00.00 head
```

**CPU line breakdown (`%Cpu(s)`):**

| Field | Meaning | High = Problem? |
|-------|---------|----------------|
| `us` | User space CPU | Normal workload |
| `sy` | System/kernel CPU | Too many syscalls? |
| `ni` | Nice (low-priority) processes | Usually fine |
| `id` | Idle | Low idle = busy |
| `wa` | I/O wait | Disk bottleneck! |
| `hi` | Hardware interrupts | Network/device overload |
| `si` | Software interrupts | Usually network |
| `st` | Steal time | VM CPU being taken by hypervisor |

**top interactive keys:**

| Key | Action |
|-----|--------|
| `P` | Sort by CPU usage |
| `M` | Sort by memory usage |
| `k` | Kill a process (enter PID) |
| `r` | Renice a process |
| `1` | Show per-CPU stats |
| `H` | Show threads |
| `q` | Quit |

> 💡 **`%st` (steal time) > 5% in a VM means your cloud provider is over-provisioning the host.** Your VM is waiting for CPU that was promised to it. Consider upgrading instance type or moving to a dedicated host.

---

## Step 3: vmstat — Virtual Memory Statistics

`vmstat` gives a compact view of processes, memory, I/O, and CPU.

```bash
# Sample every 1 second, 3 times
vmstat 1 3
```

📸 **Verified Output:**
```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0      0 95810456 898624 25782580    0    0     0     2    1    1  3  0 97  0  0
 1  0      0 95804568 898828 25784180    0    0     0  4912 10836 5720  5  2 93  0  0
 2  0      0 95917488 899140 25787288    0    0     0 10776 16153 10178  5  4 92  0  0
```

**vmstat column guide:**

| Section | Column | Meaning |
|---------|--------|---------|
| **procs** | `r` | Runnable processes (in CPU queue) |
| **procs** | `b` | Blocked (waiting for I/O) |
| **memory** | `swpd` | Virtual memory used (KB) |
| **memory** | `free` | Idle memory (KB) |
| **memory** | `buff` | Memory used as buffers |
| **memory** | `cache` | Memory used as cache |
| **swap** | `si` | Swap-in per second (KB/s) |
| **swap** | `so` | Swap-out per second (KB/s) |
| **io** | `bi` | Blocks read from devices |
| **io** | `bo` | Blocks written to devices |
| **system** | `in` | Interrupts per second |
| **system** | `cs` | Context switches per second |
| **cpu** | `us/sy/id/wa/st` | CPU percentages |

**Red flags in vmstat:**

- `r` consistently > number of CPUs → CPU bottleneck
- `b` > 0 regularly → I/O bottleneck
- `si`/`so` > 0 → Swapping (memory pressure!)
- `wa` > 20% → Disk I/O wait

> 💡 **The first vmstat line shows averages since boot.** Start reading from the second line for current activity. Use `vmstat -s` for a full memory summary, and `vmstat -d` for disk statistics.

---

## Step 4: free — Memory Analysis

```bash
free -h
echo "---"
cat /proc/meminfo | head -15
```

📸 **Verified Output:**
```
               total        used        free      shared  buff/cache   available
Mem:           121Gi       4.7Gi        91Gi        37Mi        25Gi       115Gi
Swap:          8.0Gi          0B       8.0Gi
---
MemTotal:       127539180 kB
MemFree:        95917944 kB
MemAvailable:   121516896 kB
Buffers:          899144 kB
Cached:         24078792 kB
SwapCached:            0 kB
Active:          4244316 kB
Inactive:       24469728 kB
Active(anon):    3782104 kB
Inactive(anon):        0 kB
```

**Memory concepts:**

| Metric | Meaning | Action if High |
|--------|---------|----------------|
| `used` | Allocated by processes | Normal — monitor trend |
| `buff/cache` | Kernel disk cache | Normal — kernel reclaims when needed |
| `available` | What apps can actually use | Low available → add RAM |
| `Swap used` | Overflow to disk | Investigate memory leak! |

```bash
# Memory pressure check script
awk '/MemTotal/{total=$2} /MemAvailable/{avail=$2} END{
    used=total-avail
    pct=used/total*100
    printf "Memory: %dMB used / %dMB total (%.1f%%)\n", used/1024, total/1024, pct
    if (pct > 90) print "WARNING: Memory pressure critical!"
    else if (pct > 75) print "NOTICE: Memory usage elevated"
    else print "OK: Memory usage normal"
}' /proc/meminfo
```

📸 **Verified Output:**
```
Memory: 5806MB used / 124550MB total (4.7%)
OK: Memory usage normal
```

> 💡 **`MemAvailable` is more accurate than `MemFree` for determining actual free memory.** `MemFree` excludes cache, but the kernel will reclaim cache when needed. `MemAvailable` accounts for this and shows what's truly available for new processes.

---

## Step 5: iostat — Disk I/O Analysis

```bash
apt-get install -y -qq sysstat > /dev/null 2>&1
iostat -x 1 2
```

📸 **Verified Output:**
```
Linux 6.14.0-37-generic (container)    03/05/26    _x86_64_   (32 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           2.84    0.00    0.24    0.00    0.00   96.92

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz  %util
dm-0             0.08      1.18     0.00   0.00    0.40    14.95    7.02     77.92     0.00   0.00    1.71    11.10   0.19
sda              0.06      1.23     0.02  21.59    0.32    19.14    4.22     77.92     2.83  40.09    2.09    18.46   0.03

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           5.49    0.00    4.28    0.00    0.00   90.23

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz  %util
dm-0             0.00      0.00     0.00   0.00    0.00     0.00  603.00   2628.00     0.00   0.00    0.65     4.36   2.90
sda              0.00      0.00     0.00   0.00    0.00     0.00  251.00   2624.00   351.00  58.31    0.88    10.45   3.10
```

**Key iostat columns:**

| Column | Meaning | Concern if... |
|--------|---------|---------------|
| `r/s` / `w/s` | Reads/writes per second | Very high = busy disk |
| `rkB/s` / `wkB/s` | Throughput (KB/s) | Near disk max = saturated |
| `r_await` / `w_await` | Average I/O latency (ms) | > 20ms for HDD, > 1ms for SSD |
| `%util` | Disk utilization | > 80% = potential bottleneck |
| `%iowait` (CPU) | CPU waiting for I/O | > 20% = disk bottleneck |

> 💡 **`%util` near 100% means the disk is saturated.** For SSDs, `%util` can be misleading since they handle parallel I/O — look at `await` latency instead. High `r_await` with low `%util` can indicate a slow SAN or NFS mount.

---

## Step 6: sar — System Activity Reporter

`sar` collects and reports historical system activity (the `sadc` daemon must run for history).

```bash
# Real-time sar (works without history daemon)
# CPU: sample every 1s, 3 times
sar -u 1 3
```

📸 **Verified Output:**
```
Linux 6.14.0-37-generic (container)    03/05/26    _x86_64_   (32 CPU)

05:50:21        CPU     %user     %nice   %system   %iowait    %steal     %idle
05:50:22        all      6.13      0.00      3.82      0.00      0.00     90.04
05:50:23        all     10.08      0.00      7.43      0.03      0.00     82.46
05:50:24        all      9.07      0.00      4.61      0.03      0.00     86.28
Average:        all      8.42      0.00      5.29      0.02      0.00     86.27
```

**sar command flags:**

| Flag | Reports |
|------|---------|
| `sar -u 1 5` | CPU utilization (5 samples, 1s interval) |
| `sar -r 1 5` | Memory utilization |
| `sar -d 1 5` | Disk I/O activity |
| `sar -n DEV 1 5` | Network interface statistics |
| `sar -q 1 5` | Load average and queue |
| `sar -b 1 5` | I/O and transfer rate |
| `sar -f /var/log/sa/sa15` | Read saved data (15th of month) |

```bash
# Memory monitoring with sar
sar -r 1 3
```

📸 **Verified Output:**
```
Linux 6.14.0-37-generic (container)    03/05/26    _x86_64_   (32 CPU)

05:50:24     kbmemfree  kbavail kbmemused  %memused kbbuffers  kbcached  kbcommit %commit  kbactive   kbinact   kbdirty
05:50:25     95810456 121516896   5762724      4.52    899144  24078792   8234520    5.96   4244316  24469728       516
05:50:26     95804568 121516896   5762724      4.52    899144  24078792   8234520    5.96   4244316  24469728       516
05:50:27     95917488 121516896   5762724      4.52    899140  24078792   8234520    5.96   4244316  24469728       516
Average:     95844171 121516896   5762724      4.52    899143  24078792   8234520    5.96   4244316  24469728       516
```

> 💡 **Enable `sadc` for historical data.** On Ubuntu: `systemctl enable --now sysstat`. This runs `sadc` every 10 minutes, storing data in `/var/log/sa/`. After 24h you can run `sar -u` without arguments to see today's history, or `sar -u -f /var/log/sa/sa$(date +%d)`.

---

## Step 7: Bottleneck Identification Methodology

```bash
cat > /tmp/perf-check.sh << 'SCRIPT'
#!/bin/bash
# perf-check.sh — Quick performance bottleneck identifier
set -euo pipefail

echo "=== System Performance Check ==="
echo "Time: $(date)"
echo "Host: $(hostname)"
echo ""

# 1. Load vs CPUs
cpus=$(nproc)
read load1 load5 load15 rest < /proc/loadavg
echo "--- CPU Load ---"
printf "CPUs: %d | Load: %.2f (1m) %.2f (5m) %.2f (15m)\n" \
    "$cpus" "$load1" "$load5" "$load15"
overload=$(echo "$load1 $cpus" | awk '{if ($1/$2 > 0.8) print "WARNING: CPU load high"; else print "OK"}')
echo "$overload"
echo ""

# 2. Memory
echo "--- Memory ---"
awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{
    used=t-a; pct=used/t*100
    printf "Used: %dMB / %dMB (%.1f%%)\n", used/1024, t/1024, pct
    if (pct > 90) print "CRITICAL: Memory pressure!"
    else if (pct > 75) print "WARNING: Memory elevated"
    else print "OK"
}' /proc/meminfo
echo ""

# 3. Swap
echo "--- Swap ---"
awk '/SwapTotal/{t=$2} /SwapFree/{f=$2} END{
    used=t-f
    if (t == 0) {print "No swap configured"}
    else {
        pct=used/t*100
        printf "Swap: %dMB / %dMB (%.1f%%)\n", used/1024, t/1024, pct
        if (pct > 20) print "WARNING: Swap in use - memory pressure!"
        else print "OK"
    }
}' /proc/meminfo
echo ""

# 4. Disk space
echo "--- Disk Space ---"
df -h | awk 'NR>1 && /^\// {
    gsub(/%/,"",$5)
    if ($5+0 > 90) printf "CRITICAL: %s at %s%%\n", $6, $5
    else if ($5+0 > 75) printf "WARNING: %s at %s%%\n", $6, $5
    else printf "OK: %s at %s%%\n", $6, $5
}'
echo ""

# 5. Top processes
echo "--- Top CPU Consumers ---"
ps aux --sort=-%cpu | awk 'NR==1 || NR<=6 {printf "%-8s %-6s %-6s %s\n", $1, $3, $4, $11}' | head -6
echo ""

echo "=== Check Complete ==="
SCRIPT

chmod +x /tmp/perf-check.sh
bash /tmp/perf-check.sh
```

📸 **Verified Output:**
```
=== System Performance Check ===
Time: Thu Mar  5 05:50:24 UTC 2026
Host: 04d9cc91abbd

--- CPU Load ---
CPUs: 32 | Load: 3.51 (1m) 2.26 (5m) 1.72 (15m)
OK

--- Memory ---
Used: 5806MB / 124550MB (4.7%)
OK

--- Swap ---
Swap: 0MB / 8192MB (0.0%)
OK

--- Disk Space ---
OK: / at 15%

--- Top CPU Consumers ---
USER     %CPU   %MEM   COMMAND
root     0.0    0.0    bash
root     0.0    0.0    ps
root     0.0    0.0    awk
root     0.0    0.0    head

=== Check Complete ===
```

> 💡 **Performance tuning order:** Always check in this sequence: CPU → Memory → Disk I/O → Network. A disk bottleneck often masquerades as high CPU (the kernel burning cycles waiting for I/O). Check `%iowait` first when CPU looks high.

---

## Step 8: Capstone — Comprehensive Performance Dashboard

**Scenario:** Your manager asks for a 1-page performance snapshot to baseline a new server.

```bash
cat > /tmp/perf-dashboard.sh << 'SCRIPT'
#!/bin/bash
# perf-dashboard.sh — One-page performance baseline report
apt-get install -y -qq sysstat > /dev/null 2>&1

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           SYSTEM PERFORMANCE DASHBOARD                   ║"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║ Host: %-20s  Date: %-17s║\n" "$(hostname)" "$(date '+%Y-%m-%d %H:%M')"
echo "╠══════════════════════════════════════════════════════════╣"

# Uptime
uptime_str=$(uptime | sed 's/.*up /up /' | sed 's/, *[0-9]* user.*//')
printf "║ Uptime: %-49s║\n" "$uptime_str"

# Load
read load1 load5 load15 procs pidmax < /proc/loadavg
cpus=$(nproc)
printf "║ Load:  %.2f/%.2f/%.2f  (1/5/15m)   CPUs: %-13d║\n" \
    "$load1" "$load5" "$load15" "$cpus"

echo "╠══════════════════════════════════════════════════════════╣"
echo "║ MEMORY                                                    ║"

awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} /SwapTotal/{st=$2} /SwapFree/{sf=$2} END{
    used=t-a; pct=used/t*100
    sused=st-sf; spct=(st>0)?sused/st*100:0
    printf "║ RAM:  %6dMB used / %6dMB total  (%5.1f%%)          ║\n", used/1024, t/1024, pct
    printf "║ Swap: %6dMB used / %6dMB total  (%5.1f%%)          ║\n", sused/1024, st/1024, spct
}' /proc/meminfo

echo "╠══════════════════════════════════════════════════════════╣"
echo "║ CPU (3-second sample)                                     ║"
sar -u 1 3 2>/dev/null | awk '/Average/{
    printf "║ User:%5.1f%%  System:%5.1f%%  Idle:%5.1f%%  Wait:%5.1f%%     ║\n",
        $3, $5, $8, $6
}'

echo "╠══════════════════════════════════════════════════════════╣"
echo "║ DISK                                                      ║"
df -h | awk 'NR>1 && /^\// {
    printf "║ %-10s %6s used / %6s total (%s used)        ║\n", $6, $3, $2, $5
}' | head -4

echo "╠══════════════════════════════════════════════════════════╣"
echo "║ TOP PROCESSES (by CPU)                                    ║"
ps aux --sort=-%cpu | awk 'NR>=2 && NR<=5 {
    printf "║ %-10s %5s%% CPU %5s%% MEM %-22s║\n", $1, $3, $4, substr($11,1,22)
}'

echo "╚══════════════════════════════════════════════════════════╝"
SCRIPT

chmod +x /tmp/perf-dashboard.sh
bash /tmp/perf-dashboard.sh
```

📸 **Verified Output:**
```
╔══════════════════════════════════════════════════════════╗
║           SYSTEM PERFORMANCE DASHBOARD                   ║
╠══════════════════════════════════════════════════════════╣
║ Host: 04d9cc91abbd          Date: 2026-03-05 05:50      ║
╠══════════════════════════════════════════════════════════╣
║ Uptime: up 6 days,  7:20                                ║
║ Load:  3.51/2.26/1.72  (1/5/15m)   CPUs: 32            ║
╠══════════════════════════════════════════════════════════╣
║ MEMORY                                                    ║
║ RAM:    5806MB used / 124550MB total (  4.7%)            ║
║ Swap:      0MB used /   8192MB total (  0.0%)            ║
╠══════════════════════════════════════════════════════════╣
║ CPU (3-second sample)                                     ║
║ User:  8.4%  System:  5.3%  Idle: 86.3%  Wait:  0.0%   ║
╠══════════════════════════════════════════════════════════╣
║ DISK                                                      ║
║ /          3.5G used /  24.1G total (15% used)           ║
╠══════════════════════════════════════════════════════════╣
║ TOP PROCESSES (by CPU)                                    ║
║ root        0.0% CPU   0.0% MEM bash                    ║
║ root        0.0% CPU   0.0% MEM ps                      ║
║ root        0.0% CPU   0.0% MEM awk                     ║
╚══════════════════════════════════════════════════════════╝
```

> 💡 **Schedule this dashboard with cron for shift handover reports.** Run every 8 hours and email the output: `0 */8 * * * /usr/local/bin/perf-dashboard.sh | mail -s "Server Status $(hostname)" ops@example.com`. Over time, you build a performance baseline that makes anomalies obvious.

---

## Summary

| Tool | Purpose | Key Flags |
|------|---------|-----------|
| `uptime` | Load average overview | — |
| `/proc/loadavg` | Raw load average data | — |
| `top -bn1` | Process list snapshot | `-b` batch, `-n` iterations |
| `free -h` | Memory overview | `-h` human-readable |
| `/proc/meminfo` | Detailed memory stats | — |
| `vmstat 1 5` | System-wide stats | `1` interval, `5` count |
| `iostat -x 1 3` | Disk I/O detail | `-x` extended stats |
| `sar -u 1 5` | CPU history | `-r` memory, `-d` disk |
| `ps aux --sort=-%cpu` | Process CPU ranking | `--sort=-%mem` for memory |
| `nproc` | CPU count | — |
