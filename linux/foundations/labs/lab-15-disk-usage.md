# Lab 15: Disk Usage

## 🎯 Objective
Monitor disk space usage with df and du, understand filesystem layout, and use lsblk to view block device structure.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 14: grep Basics

## 🔬 Lab Instructions

### Step 1: Check Filesystem Space with df

```bash
df -h
```

**Expected output:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        98G   15G   79G  16% /
tmpfs            13G  1.3M   13G   1% /run
...
```

```bash
df -h -x tmpfs -x devtmpfs
df -k /
df -i
```

### Step 2: Check Directory Size with du

```bash
du -sh ~
du -sh /tmp
du -sh /usr/* 2>/dev/null | sort -rh | head -10
```

### Step 3: Find Large Files and Directories

```bash
du -sh /tmp/* 2>/dev/null | head -10 2>/dev/null | sort -rh | head -10
du -sh /usr/*/ 2>/dev/null | sort -rh | head -5
du -h --max-depth=1 / 2>/dev/null | sort -rh | head -10
```

### Step 4: Create Test Files to Measure

```bash
mkdir -p /tmp/du-lab
dd if=/dev/zero of=/tmp/du-lab/file1mb.bin bs=1024 count=1024 2>/dev/null
dd if=/dev/zero of=/tmp/du-lab/file512k.bin bs=512 count=1024 2>/dev/null

du -sh /tmp/du-lab/*
du -sh /tmp/du-lab/
```

### Step 5: View Block Device Layout with lsblk

```bash
lsblk
```

**Expected output:**
```
NAME                      MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
sda                         8:0    0   256G  0 disk
├─sda1                      8:1    0     1G  0 part /boot/efi
├─sda2                      8:2    0     2G  0 part /boot
└─sda3                      8:3    0 252.9G  0 part
  └─ubuntu--vg-ubuntu--lv 252:0    0   100G  0 lvm  /
```

```bash
lsblk -f
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS
```

### Step 6: Combine df and du

```bash
echo "=== Filesystem Usage ===" && df -h /
echo "=== Top 5 in /var ===" && du -sh /var/* 2>/dev/null | sort -rh | head -5
```

```bash
df -h | awk 'NR>1 && $5+0 > 80 {print "WARNING: " $0}'
df -h | awk 'NR>1 && $5+0 <= 80 {print "OK: " $0}' | head -5
```

## ✅ Verification

```bash
echo "=== Root filesystem ===" && df -h /
echo "=== Home dir size ===" && du -sh ~
echo "=== /tmp contents ===" && du -sh /tmp/* 2>/dev/null | head -10 2>/dev/null | sort -rh | head -5
echo "=== Block devices ===" && lsblk | head -10

rm -r /tmp/du-lab 2>/dev/null
echo "Lab 15 complete"
```

## 📝 Summary
- `df -h` shows available and used space for all mounted filesystems
- `df -i` shows inode usage (number of files)
- `du -sh directory` shows total size in human-readable format
- `du -sh /path/*` shows sizes of each item in a directory
- `sort -rh` sorts human-readable sizes in reverse order (largest first)
- `lsblk` shows the physical disk and partition layout
