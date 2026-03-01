# Performance Engineering

## CPU Profiling

```bash
# perf — Linux profiling tool
sudo perf top                           # Live CPU usage by function
sudo perf record -g -p <PID>           # Record with call graphs
sudo perf report                        # Analyze recorded data

# flamegraph generation
sudo perf record -F 99 -ag -- sleep 10
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

# strace — System call tracing
strace -c -p <PID>                     # Summary of syscalls
strace -e openat,read,write -p <PID>   # Specific syscalls

# ltrace — Library call tracing
ltrace -p <PID>
```

## Memory Analysis

```bash
# Detailed memory map
cat /proc/<PID>/smaps | grep -A 11 "heap"

# Detect memory leaks (Valgrind)
valgrind --leak-check=full --track-origins=yes ./myapp

# Memory usage breakdown
pmap -x <PID>

# OOM killer analysis
dmesg | grep -i "oom\|killed"
journalctl -k | grep -i oom
```

## Disk I/O Optimization

```bash
# Check I/O scheduler
cat /sys/block/sda/queue/scheduler
# Options: mq-deadline, bfq, none (for NVMe SSDs: none is best)

# Set scheduler
echo mq-deadline > /sys/block/sda/queue/scheduler

# Monitor I/O with iostat
iostat -x 1          # Extended stats every second
# Look for: await (latency), util% (saturation)

# Find I/O-heavy processes
iotop -o            # Only processes doing I/O
pidstat -d 1        # Per-process I/O stats
```

## Network Performance Tuning

```bash
# /etc/sysctl.conf - network tuning
net.ipv4.tcp_congestion_control = bbr    # Google's BBR algorithm
net.core.default_qdisc = fq
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# Enable BBR
modprobe tcp_bbr
echo "tcp_bbr" >> /etc/modules-load.d/modules.conf
```
