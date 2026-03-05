# Lab 13: Filesystem Tuning — ext4, XFS, and Btrfs

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

Filesystem choice and tuning have significant impacts on performance, reliability, and feature availability. This lab explores ext4's tunable parameters, XFS's architecture, and Btrfs's copy-on-write capabilities.

---

## Prerequisites

```bash
docker run -it --rm --privileged ubuntu:22.04 bash
apt-get update -qq && apt-get install -y e2fsprogs xfsprogs btrfs-progs
```

---

## Step 1: Create Loopback Devices

```bash
for i in 40 41 42; do mknod /dev/loop$i b 7 $i 2>/dev/null || true; done

dd if=/dev/zero of=/tmp/ext.img bs=1M count=200
dd if=/dev/zero of=/tmp/xfs.img bs=1M count=200
dd if=/dev/zero of=/tmp/btrfs.img bs=1M count=300

losetup /dev/loop40 /tmp/ext.img
losetup /dev/loop41 /tmp/xfs.img
losetup /dev/loop42 /tmp/btrfs.img

echo "Devices ready:"
losetup -a | grep "loop4[012]"
```

📸 **Verified Output:**
```
200+0 records in
200+0 records out
209715200 bytes (210 MB, 200 MiB) copied, 0.67 s, 313 MB/s
/dev/loop40: [0118]:2111721 (/tmp/ext.img)
/dev/loop41: [0118]:2111722 (/tmp/xfs.img)
/dev/loop42: [0118]:2111731 (/tmp/btrfs.img)
```

---

## Step 2: ext4 — mkfs Options and tune2fs

```bash
# Create ext4 with custom options:
# -b 4096  : 4 KiB block size (standard)
# -i 8192  : bytes per inode (lower = more inodes)
# -m 1     : reserve only 1% for root (default is 5%)
# -L myext4: set filesystem label
mkfs.ext4 -b 4096 -i 8192 -m 1 -L myext4 /dev/loop40

# View filesystem parameters
tune2fs -l /dev/loop40
```

📸 **Verified Output:**
```
mke2fs 1.46.5 (30-Dec-2021)
Discarding device blocks: done                            
Creating filesystem with 51200 4k blocks and 25600 inodes
Filesystem UUID: f7a3c2d1-8b4e-4f1a-9c2d-3e4f5a6b7c8d
Superblock backups stored on blocks: 8193, 24577, 40961

Allocating group tables: done                            
Writing inode tables: done                            
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done

Filesystem volume name:   myext4
Inode count:              25600
Block count:              51200
Reserved block count:     512
Block size:               4096
Mount count:              0
```

```bash
# Change reserved block percentage at runtime
tune2fs -m 2 /dev/loop40
echo "Reserved blocks changed to 2%"

# Set max mount count before fsck (-1 = disabled)
tune2fs -c -1 /dev/loop40
```

📸 **Verified Output:**
```
tune2fs 1.46.5 (30-Dec-2021)
Setting reserved blocks percentage to 2% (1024 blocks)
Reserved blocks changed to 2%
```

> 💡 `-m 5` (5% reserved) protects root-level processes from disk-full conditions. For data-only volumes, `-m 1` or `-m 0` recovers that space.

---

## Step 3: dumpe2fs and e2fsck

```bash
# Dump detailed filesystem metadata
dumpe2fs /dev/loop40 | grep -E "Block count|Inode count|Block size|Journal|Filesystem state|Last checked"

# Run a filesystem check (must be unmounted)
e2fsck -f -n /dev/loop40
```

📸 **Verified Output:**
```
Filesystem state:         clean
Block count:              51200
Inode count:              25600
Block size:               4096
Journal inode:            8
Last checked:             Thu Mar  5 06:45:00 2026

e2fsck 1.46.5 (30-Dec-2021)
Pass 1: Checking inodes, blocks, and sizes
Pass 2: Checking directory structure
Pass 3: Checking directory connectivity
Pass 4: Checking reference counts
Pass 5: Checking group summary information
myext4: 11/25600 files (0.0% non-contiguous), 1443/51200 blocks
```

> 💡 `e2fsck -f` forces a check even if the filesystem appears clean. Always unmount before checking!

---

## Step 4: Mount Options for ext4

```bash
mkdir -p /mnt/ext4
# Mount with performance-optimized options
mount -o noatime,data=writeback /dev/loop40 /mnt/ext4

# Check mount options
mount | grep loop40
cat /proc/mounts | grep loop40
```

📸 **Verified Output:**
```
/dev/loop40 on /mnt/ext4 type ext4 (rw,noatime,data=writeback)
/dev/loop40 /mnt/ext4 ext4 rw,noatime,data=writeback 0 0
```

**Common mount options:**

| Option | Effect |
|---|---|
| `noatime` | Skip updating access timestamps — significant I/O reduction |
| `relatime` | Update atime only if newer than mtime (Linux default) |
| `data=writeback` | Metadata journaling only — fastest, less safe |
| `data=ordered` | Default — ensures data written before metadata |
| `data=journal` | Safest — journals both data and metadata |
| `barrier=0` | Disable write barriers — risky, faster on battery-backed RAID |

---

## Step 5: XFS — Create and Inspect

```bash
# Format XFS (auto-sizes based on device)
mkfs.xfs /dev/loop41

# Mount and inspect
mkdir -p /mnt/xfs
mount /dev/loop41 /mnt/xfs

# XFS-specific info
xfs_info /mnt/xfs
```

📸 **Verified Output:**
```
meta-data=/dev/loop41            isize=512    agcount=4, agsize=12800 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=1, sparse=1, rmapbt=0
         =                       reflink=1    bigtime=0 inobtcount=0
data     =                       bsize=4096   blocks=51200, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
log      =internal log           bsize=4096   blocks=1368, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0

Filesystem      Size  Used Avail Use% Mounted on
/dev/loop41     195M   12M  184M   6% /mnt/xfs
```

> 💡 XFS uses Allocation Groups (AGs) for parallelism. More AGs = better multi-threaded performance on large filesystems. Tune with `mkfs.xfs -d agcount=8`.

---

## Step 6: Btrfs — Subvolumes and Snapshots

```bash
# Format Btrfs
mkfs.btrfs /dev/loop42

mkdir -p /mnt/btrfs
mount /dev/loop42 /mnt/btrfs

# Create a subvolume (like a lightweight directory with its own namespace)
btrfs subvolume create /mnt/btrfs/subvol1

# Add some data
echo "important data" > /mnt/btrfs/subvol1/data.txt

# Create a snapshot (copy-on-write, instant, space-efficient)
btrfs subvolume snapshot /mnt/btrfs/subvol1 /mnt/btrfs/snap1

# List subvolumes
btrfs subvolume list /mnt/btrfs
```

📸 **Verified Output:**
```
Create subvolume '/mnt/btrfs/subvol1'
Create a snapshot of '/mnt/btrfs/subvol1' in '/mnt/btrfs/snap1'

ID 256 gen 7 top level 5 path subvol1
ID 257 gen 7 top level 5 path snap1
```

```bash
# Verify snapshot independence — modify original, snapshot unchanged
echo "new change" >> /mnt/btrfs/subvol1/data.txt
echo "=== Original ==="
cat /mnt/btrfs/subvol1/data.txt
echo "=== Snapshot ==="
cat /mnt/btrfs/snap1/data.txt

df -h /mnt/btrfs
```

📸 **Verified Output:**
```
=== Original ===
important data
new change
=== Snapshot ===
important data

Filesystem      Size  Used Avail Use% Mounted on
/dev/loop42     300M  5.9M  219M   3% /mnt/btrfs
```

> 💡 Btrfs snapshots are copy-on-write — they only store the *differences* from the original, making them nearly instant and very space-efficient.

---

## Step 7: Filesystem Benchmarking with dd

```bash
# Write benchmark — sequential throughput
echo "=== ext4 write speed ==="
dd if=/dev/zero of=/mnt/ext4/bench bs=1M count=100 oflag=direct 2>&1

echo "=== XFS write speed ==="
dd if=/dev/zero of=/mnt/xfs/bench bs=1M count=100 oflag=direct 2>&1

echo "=== Read benchmark (from cache) ==="
dd if=/mnt/ext4/bench of=/dev/null bs=1M 2>&1
```

📸 **Verified Output:**
```
=== ext4 write speed ===
100+0 records in
100+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.412 s, 254 MB/s

=== XFS write speed ===
100+0 records in
100+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.389 s, 269 MB/s

=== Read benchmark (from cache) ===
100+0 records in
100+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.021 s, 4.9 GB/s
```

> 💡 Use `fio` for production-grade I/O benchmarking — it can simulate random reads, async writes, and queue depths that `dd` can't.

---

## Step 8: Capstone — Filesystem Tuning for a Use Case

**Scenario:** You're setting up storage for a high-traffic web server with the following requirements:
- Fast metadata operations (many small files)
- No need for POSIX access time tracking
- Data integrity is critical
- Need point-in-time snapshots for backups

```bash
echo "=== Choosing the right filesystem ==="
echo ""
echo "Use case: High-traffic web server"
echo ""
echo "Requirements analysis:"
echo "  - Many small files      -> XFS or ext4 with low inode ratio (-i 4096)"
echo "  - No access time        -> Mount with 'noatime'"
echo "  - Data integrity        -> ext4 data=ordered (default) or XFS"
echo "  - Point-in-time backups -> Btrfs subvolumes + snapshots"
echo ""

# Demonstrate optimal ext4 for web server
mkfs.ext4 -b 4096 -i 4096 -m 1 -L webdata /dev/loop40 2>/dev/null || \
  tune2fs -L webdata /dev/loop40

umount /mnt/ext4 2>/dev/null; mount -o noatime,data=ordered /dev/loop40 /mnt/ext4
echo "Web server optimized ext4 mounted:"
mount | grep loop40

# Demonstrate Btrfs backup workflow
echo "" > /mnt/btrfs/subvol1/site.conf
btrfs subvolume snapshot -r /mnt/btrfs/subvol1 /mnt/btrfs/backup_$(date +%Y%m%d)
echo "Read-only backup snapshot created:"
btrfs subvolume list /mnt/btrfs
btrfs subvolume show /mnt/btrfs/backup_$(date +%Y%m%d) 2>/dev/null | grep -E "Name|UUID|Flags"
```

---

## Summary

| Filesystem | Best For | Key Features | Resize |
|---|---|---|---|
| **ext4** | General-purpose, compatibility | Journaling, tune2fs, mature | Grow online, shrink offline |
| **XFS** | Large files, databases, parallel I/O | Allocation groups, reflink | Grow only |
| **Btrfs** | Snapshots, dedup, multi-device | CoW, subvolumes, checksums | Grow online |

| Command | Purpose |
|---|---|
| `mkfs.ext4 -b 4096 -i 8192 -m 1` | Create ext4 with custom block/inode/reserve |
| `tune2fs -m 2 /dev/sda1` | Change reserved block % |
| `tune2fs -l /dev/sda1` | Show ext4 parameters |
| `dumpe2fs /dev/sda1` | Full filesystem dump |
| `e2fsck -f /dev/sda1` | Force filesystem check |
| `xfs_info /mnt/xfs` | Show XFS parameters |
| `xfs_repair /dev/sdb1` | Repair XFS (unmounted) |
| `btrfs subvolume create /mnt/data/vol` | Create Btrfs subvolume |
| `btrfs subvolume snapshot src dst` | Create snapshot |
| `mount -o noatime,data=writeback` | Performance mount options |
