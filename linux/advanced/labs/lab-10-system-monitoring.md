# Lab 10: System Monitoring

## 🎯 Objective
Monitor system performance using `top`, `htop`, `vmstat`, `iostat`, and `sar` to identify resource bottlenecks.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Basic understanding of CPU, memory, and I/O concepts

## 🔬 Lab Instructions

### Step 1: top — Real-Time Process Monitor
```bash
top
# top - 06:01:23 up 2 days, 14:22,  1 user,  load average: 0.08, 0.05, 0.01
# Tasks: 102 total,   1 running, 101 sleeping,   0 stopped,   0 zombie
# %Cpu(s):  2.0 us,  0.5 sy,  0.0 ni, 97.4 id,  0.1 wa,  0.0 hi,  0.0 si
# MiB Mem : 1987.0 total,  823.4 free,  456.2 used,  707.4 buff/cache
# MiB Swap:  975.0 total,  975.0 free,    0.0 used. 1434.8 avail Mem
#
# PID   USER  PR  NI    VIRT    RES    SHR S  %CPU  %MEM  TIME+    COMMAND
# 1234  root  20   0  200000  10000   7000 S   1.3   0.5   0:02.34  sshd

# Key commands in top:
# q = quit   M = sort by memory   P = sort by CPU
# k = kill   1 = show per-CPU     h = help
```

### Step 2: top — Non-Interactive (for Scripts)
```bash
# Single snapshot, batch mode
top -bn1 | head -20
# Useful for scripts

# Show only first 10 processes
top -bn1 | grep -A10 PID

# CPU usage summary
top -bn1 | grep '%Cpu'
# %Cpu(s):  2.0 us,  0.5 sy,  0.0 ni, 97.4 id,  0.1 wa ...

# Memory summary
top -bn1 | grep 'MiB Mem'
# MiB Mem : 1987.0 total,  823.4 free,  456.2 used
```

### Step 3: htop — Enhanced Interactive Monitor
```bash
sudo apt install -y htop

htop
# (interactive — press F10 or q to quit)
# Shows colored bars for CPU, memory, swap
# F5: tree view   F6: sort   F4: filter
# F9: kill signal  Space: tag processes

# Run non-interactively
htop --no-color -d 10 &
HTOP_PID=$!
sleep 2
kill $HTOP_PID 2>/dev/null || true
echo "htop demonstrated"
```

### Step 4: vmstat — Virtual Memory Statistics
```bash
# Single snapshot
vmstat
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
#  0  0      0 843612  12340 723456    0    0     1     2   50  100  2  1 97  0  0

# Continuous (every 1 second, 5 times)
vmstat 1 5
# procs  memory    swap  io  system  cpu
# r  b   free ...
# 0  0   843000 ...   (repeat 5x)

# Key fields:
# r = runnable processes   b = blocked processes
# si/so = swap in/out      bi/bo = block I/O in/out
# us/sy/id/wa = user/system/idle/wait CPU %
```

### Step 5: vmstat — Memory and Disk Stats
```bash
# Show disk statistics
vmstat -d
# disk- ------------reads------------ ------------writes-----------
#         total merged sectors      ms  total merged sectors      ms
# sda      1234     56   78901    2345   5678     90  123456    7890

# Show slabs (kernel memory allocations)
vmstat -m | head -10
# Cache                  Num  Total   Size  Pages
# ext4_inode_cache      5000   5000    720     44
```

### Step 6: iostat — I/O Statistics
```bash
sudo apt install -y sysstat

# CPU and I/O summary
iostat
# Linux 5.15.0 (myserver)   03/01/2026   _x86_64_  (2 CPU)
#
# avg-cpu:  %user   %nice %system %iowait  %steal   %idle
#            2.00    0.00    0.50    0.10    0.00   97.40
#
# Device             tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
# sda               1.50         8.00        25.00     123456     987654

# Extended stats, 1 second interval
iostat -x 1 3
# Device  r/s  rkB/s  rrqm/s  %rrqm  r_await rareq-sz  w/s  wkB/s  ... %util
# sda    0.50   4.00    0.00   0.00    0.50    8.00    1.00  12.50  ...   0.20

# %util shows how busy the disk is (near 100% = saturated)
```

### Step 7: sar — System Activity Reporter
```bash
# sar collects historical data (requires sysstat service)
sudo systemctl enable --now sysstat
sudo systemctl start sysstat

# View CPU history (today)
sar
# 06:00:01 AM  CPU  %user  %nice  %system  %iowait  %steal  %idle
# 06:10:01 AM  all   2.00   0.00     0.50     0.10    0.00  97.40

# View memory history
sar -r 1 5
# 06:01:01  kbmemfree  kbavail  kbmemused  %memused  ...

# View network history
sar -n DEV 1 3
# 06:01:01  IFACE  rxpck/s  txpck/s  rxkB/s  txkB/s ...
```

### Step 8: uptime and Load Average
```bash
uptime
#  06:01:23 up 2 days, 14:22,  1 user,  load average: 0.08, 0.05, 0.01

# Load averages are for 1, 5, 15 minutes
# Values > number of CPU cores indicate overload

# Check number of CPUs
nproc
# 2

# Load 0.08 on 2-core system = 4% utilized (normal)
# Load 4.0 on 2-core system = 200% (very high)

cat /proc/loadavg
# 0.08 0.05 0.01 1/102 4567
# (last: running/total processes, last PID created)
```

### Step 9: Monitor Memory with /proc
```bash
cat /proc/meminfo | head -20
# MemTotal:        2035000 kB
# MemFree:          843612 kB
# MemAvailable:    1469044 kB
# Buffers:           12340 kB
# Cached:           702456 kB
# SwapCached:            0 kB
# SwapTotal:        997372 kB
# SwapFree:         997372 kB
# ...

# Available memory is more useful than Free (includes reclaimable cache)
awk '/MemAvailable/{printf "Available: %.1f GB\n", $2/1024/1024}' /proc/meminfo
# Available: 1.4 GB
```

### Step 10: Create a Monitoring Snapshot Script
```bash
cat > ~/system_snapshot.sh << 'EOF'
#!/bin/bash
echo "=== System Snapshot: $(date) ==="

echo ""
echo "-- Uptime --"
uptime

echo ""
echo "-- CPU (top 5 processes) --"
ps aux --sort=-%cpu | awk 'NR>1 && NR<=6 {printf "  %-20s %5s%% CPU\n", $11, $3}'

echo ""
echo "-- Memory --"
free -h | awk 'NR<=2'
awk '/MemAvailable/{printf "  Available: %.1f GB\n", $2/1024/1024}' /proc/meminfo

echo ""
echo "-- Disk I/O --"
iostat -d 1 1 2>/dev/null | tail -5 || echo "  (sysstat not installed)"

echo ""
echo "-- Top 3 Disk Usage --"
df -h --output=pcent,target | grep -v Use | sort -rn | head -3
EOF
chmod +x ~/system_snapshot.sh
~/system_snapshot.sh
```

## ✅ Verification
```bash
top -bn1 | grep '%Cpu' | awk '{print "CPU idle:", $8"%"}'
free -m | awk '/^Mem:/{printf "Memory: %d/%dMB used\n", $3, $2}'
vmstat 1 2 | tail -1 | awk '{print "I/O wait:", $16"%"}'
```

## 📝 Summary
- `top` and `htop` provide real-time process and resource monitoring
- `vmstat 1 N` shows CPU, memory, and I/O statistics every second
- `iostat -x 1` shows extended disk I/O stats including `%util` (saturation)
- `sar` records historical performance data for post-mortem analysis
- Load average > number of CPUs indicates system overload
- `/proc/meminfo` and `/proc/loadavg` provide raw kernel-level stats
