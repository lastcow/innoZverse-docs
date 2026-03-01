# System Monitoring & Performance

## Real-time Monitoring

```bash
top                     # Process viewer (press q to quit)
htop                    # Enhanced version (sudo apt install htop)
btop                    # Modern resource monitor

# Key shortcuts in top/htop:
# P = sort by CPU
# M = sort by memory
# k = kill process
# q = quit
```

## CPU & Memory

```bash
free -h                             # Memory usage (human-readable)
vmstat 1 5                          # System stats every 1s, 5 times
cat /proc/cpuinfo | grep "model name" | head -1
nproc                               # Number of CPU cores
lscpu                               # Detailed CPU info
```

## Disk I/O

```bash
df -h                   # Disk space usage
du -sh /var/log/        # Directory size
du -sh /* | sort -rh | head -10     # Largest top-level dirs
iostat -x 1             # Disk I/O stats (sysstat package)
iotop                   # Real-time disk I/O by process
```

## Logs & Journaling

```bash
journalctl -f                       # Follow system journal
journalctl -u nginx                 # Logs for specific service
journalctl --since "1 hour ago"     # Recent logs
journalctl -p err                   # Error-level and above
tail -f /var/log/syslog             # Traditional syslog
```

## Load Average

```bash
uptime
# 15:04:23 up 5 days,  2:10,  1 user,  load average: 0.42, 0.38, 0.35
#                                                       1min  5min  15min
# Rule of thumb: load avg > number of CPU cores = system is overloaded
```
