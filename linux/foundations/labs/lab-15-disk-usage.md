# Lab 15: Disk Usage

## 🎯 Objective
Monitor filesystem usage with `df -h`, analyze directory sizes with `du -sh`, understand disk space consumption, and learn about the `ncdu` interactive tool.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic terminal skills

## 🔬 Lab Instructions

### Step 1: Check Filesystem Disk Space with `df`
```bash
df
# Output: filesystem sizes in 1K blocks (hard to read)

df -h
# Output: human-readable (KB, MB, GB, TB)
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1        50G   12G   36G  25% /
# tmpfs           2.0G     0  2.0G   0% /dev/shm
```

### Step 2: Understand `df -h` Output
```
Filesystem:  device or partition name
Size:        total size of the filesystem
Used:        how much is currently used
Avail:       how much is available
Use%:        percentage used — alert at 80-85%+
Mounted on:  where it's accessible in the directory tree
```

### Step 3: Show Specific Filesystem
```bash
# Check the filesystem where /home is
df -h /home
# Output: just the filesystem containing /home

df -h /
# Check root filesystem

df -h /tmp
# Check /tmp (may be tmpfs in memory)
```

### Step 4: Check Inode Usage
```bash
# Inodes track file metadata (name, permissions, etc.)
# You can run out of inodes even if space is available!
df -i
# Output: same format but showing inodes
# IFree = available inodes

df -ih
# Human-readable inode counts
```

### Step 5: Check Directory Size with `du`
```bash
du /home
# Output: size of every file in 1K blocks (verbose)

du -h /home
# Human-readable

du -sh /home
# -s = summary (total only, no subdirectory breakdown)
# Output: 1.2G    /home
```

### Step 6: Find the Largest Directories
```bash
# Show top-level dirs in /var sorted by size
du -sh /var/* 2>/dev/null | sort -rh | head -10
# -r = reverse sort (largest first)
# -h = understand human-readable sizes (10G > 1G)

# Find largest dirs in /home
du -sh ~/.[!.]* ~/* 2>/dev/null | sort -rh | head -10
```

### Step 7: Find Largest Files
```bash
# Find files larger than 100MB
find / -type f -size +100M 2>/dev/null | head -10

# Find the top 10 largest files
find / -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -10
```

### Step 8: Analyze Log Disk Usage
```bash
# Logs can fill up quickly
du -sh /var/log
du -sh /var/log/* 2>/dev/null | sort -rh | head -10
```

### Step 9: Install and Use ncdu (Interactive Disk Usage)
```bash
sudo apt install ncdu -y

# Analyze home directory interactively
ncdu ~
# Navigation:
# Up/Down: move through files/dirs
# Enter:   go into directory
# q:       quit
# d:       delete selected item (be careful!)
# ?:       help
```

### Step 10: Monitor Real-Time Disk Activity
```bash
# watch repeats a command every N seconds
watch -n 2 df -h
# Updates every 2 seconds
# Press Ctrl+C to stop
```

### Step 11: Disk Usage as Part of System Health Check
```bash
# Quick health check script
echo "=== Disk Health Check ==="
echo ""
echo "Filesystem Usage:"
df -h | grep -v tmpfs

echo ""
echo "Top 5 largest directories in /var:"
du -sh /var/* 2>/dev/null | sort -rh | head -5

echo ""
echo "Top 5 largest directories in /home:"
du -sh /home/*/ 2>/dev/null | sort -rh | head -5
```

### Step 12: Free Up Disk Space Tips
```bash
# Clean apt package cache
sudo apt clean
sudo apt autoremove -y

# Check after cleaning
df -h /

# Find and remove old log files (preview first!)
find /var/log -name "*.gz" -mtime +30 -type f | head -5
# sudo find /var/log -name "*.gz" -mtime +30 -delete

# Truncate a log file without deleting it (preserves file handle)
# sudo truncate -s 0 /var/log/syslog
```

## ✅ Verification
```bash
# Run a complete disk check
df -h
# Should show all filesystems

du -sh /var/log
# Should show a size

# Create, measure, delete a test file
dd if=/dev/zero of=/tmp/testfile bs=1M count=10 2>/dev/null
du -sh /tmp/testfile
# Output: 10M     /tmp/testfile

rm /tmp/testfile
```

## 📝 Summary
- `df -h` shows filesystem-level disk usage — watch for Use% approaching 80%+
- `du -sh directory` shows total size of a directory; omit `-s` for per-file detail
- Sort `du` output with `sort -rh` to find the biggest consumers
- Inode exhaustion (`df -i`) can fill a filesystem even when space remains
- `ncdu` is an interactive, ncurses-based disk usage browser — great for visual exploration
