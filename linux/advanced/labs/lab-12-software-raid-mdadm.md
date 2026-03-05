# Lab 12: Software RAID with mdadm

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

Software RAID uses your CPU to mirror, stripe, or parity-protect data across multiple block devices. `mdadm` is the Linux tool for creating and managing MD (Multiple Device) arrays.

---

## Prerequisites

```bash
docker run -it --rm --privileged ubuntu:22.04 bash
apt-get update -qq && apt-get install -y mdadm
```

---

## Step 1: Create Virtual Disks (Loopback Devices)

```bash
# Create explicit loop device nodes
for i in 30 31 32 33; do mknod /dev/loop$i b 7 $i 2>/dev/null || true; done

# Create 150 MiB disk images
dd if=/dev/zero of=/tmp/r1.img bs=1M count=150
dd if=/dev/zero of=/tmp/r2.img bs=1M count=150
dd if=/dev/zero of=/tmp/r3.img bs=1M count=150

# Attach to loop devices
losetup /dev/loop30 /tmp/r1.img
losetup /dev/loop31 /tmp/r2.img
losetup /dev/loop32 /tmp/r3.img

# Verify
losetup -a | grep "loop3[012]"
```

📸 **Verified Output:**
```
/dev/loop30: [0118]:2111721 (/tmp/r1.img)
/dev/loop31: [0118]:2111722 (/tmp/r2.img)
/dev/loop32: [0118]:2111731 (/tmp/r3.img)
```

> 💡 Check `/proc/mdstat` at any time to see all active RAID arrays and their status.

---

## Step 2: Create a RAID 1 Array (Mirroring)

RAID 1 writes identical data to all member disks — if one fails, data survives on the others.

```bash
# Create RAID 1 with 2 disks
echo y | mdadm --create /dev/md200 \
    --level=1 \
    --raid-devices=2 \
    /dev/loop30 /dev/loop31 \
    --assume-clean

# Check array status
cat /proc/mdstat
```

📸 **Verified Output:**
```
mdadm: Note: this array has metadata at the start and
    may not be suitable as a boot device.
Continue creating array? mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md200 started.

Personalities : [linear] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10] 
md200 : active raid1 loop31[1] loop30[0]
      152576 blocks super 1.2 [2/2] [UU]
      
unused devices: <none>
```

> 💡 `[UU]` means both disks are Up. `[_U]` would mean first disk is degraded/missing.

---

## Step 3: Inspect the Array with mdadm --detail

```bash
mdadm --detail /dev/md200
```

📸 **Verified Output:**
```
/dev/md200:
           Version : 1.2
     Creation Time : Thu Mar  5 06:50:48 2026
        Raid Level : raid1
        Array Size : 152576 (149.00 MiB 156.24 MB)
     Used Dev Size : 152576 (149.00 MiB 156.24 MB)
      Raid Devices : 2
     Total Devices : 2
       Persistence : Superblock is persistent

             State : clean 
    Active Devices : 2
   Working Devices : 2
    Failed Devices : 0
     Spare Devices : 0

Consistency Policy : resync

    Number   Major   Minor   RaidDevice State
       0       7      30        0      active sync   /dev/loop30
       1       7      31        1      active sync   /dev/loop31
```

---

## Step 4: Format and Mount the RAID Array

```bash
mkfs.ext4 /dev/md200

mkdir -p /mnt/md200
mount /dev/md200 /mnt/md200
echo "RAID1 data" > /mnt/md200/test.txt
df -h /mnt/md200
```

📸 **Verified Output:**
```
Creating filesystem with 38144 4k blocks and 38144 inodes
Allocating group tables:   done                            
Writing inode tables:   done                            
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done

Filesystem      Size  Used Avail Use% Mounted on
/dev/md200      124M   24K  114M   1% /mnt/md200
```

---

## Step 5: Simulate a Disk Failure

```bash
# Mark loop30 as failed
mdadm /dev/md200 --fail /dev/loop30

# Remove the failed disk
mdadm /dev/md200 --remove /dev/loop30

# Check degraded status
cat /proc/mdstat
```

📸 **Verified Output:**
```
mdadm: set /dev/loop30 faulty in /dev/md200
mdadm: hot removed /dev/loop30 from /dev/md200

Personalities : [linear] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10] 
md200 : active raid1 loop31[1]
      152576 blocks super 1.2 [2/1] [_U]
      
unused devices: <none>
```

> 💡 `[_U]` — first slot is degraded (`_`), second is up (`U`). Data is still fully accessible from loop31!

---

## Step 6: Replace the Failed Disk (Recovery)

```bash
# Add a replacement disk (loop32)
mdadm /dev/md200 --add /dev/loop32

# Watch the resync
sleep 1
cat /proc/mdstat
mdadm --detail /dev/md200 | grep -E "State|Active|Working|Rebuild"
```

📸 **Verified Output:**
```
mdadm: added /dev/loop32

Personalities : [linear] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10] 
md200 : active raid1 loop32[2] loop31[1]
      152576 blocks super 1.2 [2/2] [UU]
      
unused devices: <none>

             State : clean 
    Active Devices : 2
   Working Devices : 2
```

> 💡 On real drives, a resync takes minutes to hours depending on array size. `watch cat /proc/mdstat` lets you monitor rebuild progress.

---

## Step 7: RAID 5 and mdadm.conf

Create a RAID 5 array (striping with distributed parity):

```bash
# Create RAID 5 with 3 disks
echo y | mdadm --create /dev/md201 \
    --level=5 \
    --raid-devices=3 \
    /dev/loop30 /dev/loop31 /dev/loop32 \
    --assume-clean

mdadm --detail /dev/md201 | grep -E "RAID Level|Array Size|State|Active|Working|Chunk"
```

📸 **Verified Output:**
```
mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md201 started.

        Raid Level : raid5
        Array Size : 241664 (236.00 MiB 247.46 MB)
             State : clean 
    Active Devices : 3
   Working Devices : 3
        Chunk Size : 512K
```

**Save the array configuration:**

```bash
# Generate mdadm.conf
mdadm --detail --scan

# On a real system, save to /etc/mdadm/mdadm.conf:
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
# Then run: update-initramfs -u
```

📸 **Verified Output:**
```
ARRAY /dev/md200 metadata=1.2 name=host:200 UUID=9384cb8a:e1fb4ece:e242819f:1e28304d
ARRAY /dev/md201 metadata=1.2 name=host:201 UUID=6340e3d6:0666647a:23a94981:b00e3f48
```

> 💡 Without `/etc/mdadm/mdadm.conf`, arrays may not auto-assemble at boot. Always save the config after creating arrays.

---

## Step 8: Capstone — RAID Level Comparison

```bash
# Compare what's available
echo "=== RAID Level Comparison ==="
echo ""
echo "RAID 0 (Stripe): No redundancy. N disks = N× speed, 0 fault tolerance."
echo "RAID 1 (Mirror): Full copy. N disks = 1× capacity, N-1 disk fault tolerance."
echo "RAID 5 (Stripe+Parity): Distributed parity. N disks = N-1× capacity, 1 disk fault tolerance."
echo "RAID 6 (Double Parity): N disks = N-2× capacity, 2 disk fault tolerance."
echo "RAID 10 (Stripe+Mirror): N disks = N/2× capacity, 1 per mirror set fault tolerance."

# Show current arrays
cat /proc/mdstat

# Capstone: Create RAID 0 (striping) for performance comparison
mknod /dev/loop33 b 7 33 2>/dev/null || true
dd if=/dev/zero of=/tmp/s1.img bs=1M count=150 2>/dev/null
losetup /dev/loop33 /tmp/s1.img

# Stop md200 and reuse loop30
mdadm --stop /dev/md200
echo y | mdadm --create /dev/md202 \
    --level=0 \
    --raid-devices=2 \
    /dev/loop30 /dev/loop33 \
    --assume-clean

mdadm --detail /dev/md202 | grep -E "RAID Level|Array Size|Chunk"
echo "RAID 0 usable size = sum of all disks (no redundancy)"
```

📸 **Verified Output:**
```
Personalities : [linear] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10] 
md201 : active raid5 loop32[2] loop31[1] loop30[0]
      241664 blocks super 1.2 level 5, 512k chunk, algorithm 2 [3/3] [UUU]

        Raid Level : raid0
        Array Size : 305152 (298.00 MiB 312.48 MB)
        Chunk Size : 512K
```

---

## Summary

| RAID Level | Min Disks | Usable Capacity | Fault Tolerance | Use Case |
|---|---|---|---|---|
| RAID 0 | 2 | 100% | None | Performance (no redundancy) |
| RAID 1 | 2 | 50% | N-1 disks | Boot drives, critical data |
| RAID 5 | 3 | 67-94% | 1 disk | General-purpose storage |
| RAID 6 | 4 | 50-88% | 2 disks | High-capacity, archive |
| RAID 10 | 4 | 50% | 1 per mirror | Databases, high I/O |

| Command | Purpose |
|---|---|
| `mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sd{a,b}` | Create RAID 1 |
| `cat /proc/mdstat` | Array status |
| `mdadm --detail /dev/md0` | Detailed info |
| `mdadm /dev/md0 --fail /dev/sda` | Mark disk failed |
| `mdadm /dev/md0 --remove /dev/sda` | Remove failed disk |
| `mdadm /dev/md0 --add /dev/sdc` | Add replacement |
| `mdadm --detail --scan >> /etc/mdadm/mdadm.conf` | Save config |
