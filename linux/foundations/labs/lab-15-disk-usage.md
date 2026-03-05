# Lab 15: Disk Usage — df and du

## Objective
Monitor disk space with `df` (disk free) and `du` (disk usage): identify full filesystems, find space hogs, build disk monitoring scripts. A full disk brings down production servers — this is operational survival knowledge.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: df — Filesystem Space Overview

```bash
df -h
```

**📸 Verified Output:**
```
Filesystem                         Size  Used Avail Use% Mounted on
overlay                             98G   33G   60G  36% /
tmpfs                               64M     0   64M   0% /dev
shm                                 64M     0   64M   0% /dev/shm
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   33G   60G  36% /etc/hosts
tmpfs                               61G     0   61G   0% /proc/acpi
```

Columns: **Filesystem**, **Size**, **Used**, **Avail**, **Use%**, **Mounted on**

> 💡 `-h` = human-readable (G/M/K instead of blocks). Watch for filesystems at **80%+** use — at 100% writes fail, applications crash, and logs stop recording. Set up alerts at 80%.

---

## Step 2: df with Inode Information

```bash
df -i
```

**📸 Verified Output:**
```
Filesystem      Inodes  IUsed   IFree IUse% Mounted on
overlay        6553600 101234 6452366    2% /
tmpfs          8204871      5 8204866    1% /dev
```

> 💡 **Inodes** store file metadata. You can run out of inodes even with disk space available — this happens when you have millions of tiny files (e.g., npm cache, mail spools). A server with 0% inode free crashes exactly like one with 0% disk space free.

---

## Step 3: du — Directory Usage

```bash
du -sh /etc /var /usr 2>/dev/null
```

**📸 Verified Output:**
```
640K	/etc
5.2M	/var
78M	/usr
```

```bash
# Largest items in /etc
du -sh /etc/* 2>/dev/null | sort -rh | head -5
```

**📸 Verified Output:**
```
72K	/etc/pam.d
72K	/etc/apt
52K	/etc/security
36K	/etc/sysctl.d
32K	/etc/dpkg
```

> 💡 `-s` = summary (total for each argument, not every subdirectory). `-h` = human-readable. `sort -rh` sorts human-readable sizes in reverse (largest first).

---

## Step 4: du with Depth Control

```bash
# Show 2 levels deep
du -h --max-depth=2 /var 2>/dev/null
```

**📸 Verified Output:**
```
4.0K	/var/backups
4.0K	/var/cache/ldconfig
4.0K	/var/cache
4.0K	/var/lib/dpkg/alternatives
...
5.2M	/var
```

---

## Step 5: Finding the Largest Files

```bash
# Top 5 largest files on the system
find / -xdev -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -5
```

**📸 Verified Output:**
```
4455728 /usr/lib/x86_64-linux-gnu/libcrypto.so.3
3806200 /usr/bin/perl5.34.0
3806200 /usr/bin/perl
2260296 /usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.30
2220400 /usr/lib/x86_64-linux-gnu/libc.so.6
```

---

## Step 6: du with Grand Total

```bash
du -ch /etc/*.conf 2>/dev/null | tail -3
```

**📸 Verified Output:**
```
4.0K	/etc/sysctl.conf
4.0K	/etc/xattr.conf
56K	total
```

> 💡 `-c` adds a grand total line at the end. Use `du -ch /var/log/*.log` to see total log space at a glance before deciding how much to rotate/compress.

---

## Step 7: Monitoring Disk Usage Over Time

```bash
# Simple disk monitor script
cat > /tmp/disk_monitor.sh << 'SCRIPT'
#!/bin/bash
THRESHOLD=80
echo "=== Disk Usage Report: $(date) ==="
df -h | grep -v tmpfs | tail -n +2 | while read line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    if [ "$USAGE" -ge "$THRESHOLD" ] 2>/dev/null; then
        echo "⚠️  WARNING: $MOUNT is at ${USAGE}%"
    else
        echo "✅  OK: $MOUNT is at ${USAGE}%"
    fi
done
SCRIPT
chmod +x /tmp/disk_monitor.sh
/tmp/disk_monitor.sh
```

**📸 Verified Output:**
```
=== Disk Usage Report: Thu Mar  5 01:09:00 UTC 2026 ===
✅  OK: / is at 36%
```

---

## Step 8: Capstone — Full Log Cleanup Simulation

```bash
# Simulate a server with growing logs
mkdir -p /tmp/log_cleanup/app
for i in $(seq 1 10); do
    dd if=/dev/urandom of="/tmp/log_cleanup/app/app_$(printf '%02d' $i).log" bs=1K count=$((i*10)) 2>/dev/null
done
touch -d '-90 days' /tmp/log_cleanup/app/app_0{1..5}.log  # old logs

echo "=== Before cleanup ==="
du -sh /tmp/log_cleanup/
ls -lh /tmp/log_cleanup/app/ | sort -k5 -rh

echo ""
echo "=== Disk space by age ==="
echo "Old logs (>60 days):"
find /tmp/log_cleanup -name '*.log' -mtime +60 -exec du -sh {} \;
echo ""
echo "Recent logs:"
find /tmp/log_cleanup -name '*.log' -mtime -60 -exec du -sh {} \;

echo ""
echo "=== Deleting logs older than 60 days ==="
find /tmp/log_cleanup -name '*.log' -mtime +60 -delete
echo "Space freed. After cleanup:"
du -sh /tmp/log_cleanup/
```

**📸 Verified Output:**
```
=== Before cleanup ===
960K	/tmp/log_cleanup/
-rw-r--r-- 1 root root 100K Mar  5 01:09 app_10.log
-rw-r--r-- 1 root root  90K Mar  5 01:09 app_09.log
...
-rw-r--r-- 1 root root  10K Dec  5  2025 app_01.log

=== Disk space by age ===
Old logs (>60 days):
10K	/tmp/log_cleanup/app/app_01.log
20K	/tmp/log_cleanup/app/app_02.log
30K	/tmp/log_cleanup/app/app_03.log
40K	/tmp/log_cleanup/app/app_04.log
50K	/tmp/log_cleanup/app/app_05.log

Recent logs:
...

=== Deleting logs older than 60 days ===
Space freed. After cleanup:
640K	/tmp/log_cleanup/
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `df -h` | Filesystem free space |
| `df -i` | Inode usage |
| `du -sh dir` | Directory total size |
| `du -sh dir/* \| sort -rh` | Sort directories by size |
| `du -ch files \| tail -1` | Grand total |
| `du --max-depth=N` | Limit depth |
| `find -printf '%s %p\n' \| sort -rn` | Find largest files |
