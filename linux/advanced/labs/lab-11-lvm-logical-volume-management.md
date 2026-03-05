# Lab 11: LVM — Logical Volume Management

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

LVM (Logical Volume Manager) adds a flexible abstraction layer between physical disks and filesystems. You can resize volumes online, create snapshots, and span data across multiple disks without repartitioning.

---

## Prerequisites

```bash
docker run -it --rm --privileged ubuntu:22.04 bash
apt-get update -qq && apt-get install -y lvm2
```

---

## Step 1: Create Loopback Devices (Virtual Disks)

In this lab we simulate physical disks using loopback devices — image files mounted as block devices.

```bash
# Create two 100 MiB disk images
dd if=/dev/zero of=/tmp/disk1.img bs=1M count=100
dd if=/dev/zero of=/tmp/disk2.img bs=1M count=100

# Create explicit loop device nodes (required in privileged Docker)
mknod /dev/loop60 b 7 60 2>/dev/null || true
mknod /dev/loop61 b 7 61 2>/dev/null || true

# Attach the images to loop devices
losetup /dev/loop60 /tmp/disk1.img
losetup /dev/loop61 /tmp/disk2.img

# Verify
losetup -a | grep loop6
```

📸 **Verified Output:**
```
100+0 records in
100+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.366 s, 286 MB/s
/dev/loop60: [0118]:2111721 (/tmp/disk1.img)
/dev/loop61: [0118]:2111722 (/tmp/disk2.img)
```

> 💡 `losetup -f --show /file.img` auto-selects the next free loop device and prints it — useful in scripts.

---

## Step 2: Initialize Physical Volumes (PVs)

```bash
# Mark devices as LVM physical volumes
pvcreate /dev/loop60 /dev/loop61

# Inspect a PV
pvdisplay /dev/loop60
```

📸 **Verified Output:**
```
  Physical volume "/dev/loop60" successfully created.
  Physical volume "/dev/loop61" successfully created.

  --- Physical volume ---
  PV Name               /dev/loop60
  VG Name               
  PV Size               100.00 MiB / not usable 4.00 MiB
  Allocatable           NO
  PE Size               0   
  Total PE              0
  Free PE               0
  Allocated PE          0
  PV UUID               lShb6x-3o1q-GQd2-kJLR-gYd7-t4et-9brl3S
```

> 💡 The "not usable 4.00 MiB" is reserved for LVM metadata (stored at the start of the PV).

---

## Step 3: Create a Volume Group (VG)

A Volume Group pools multiple PVs into one storage reservoir.

```bash
# Create VG from both PVs
vgcreate vg_data /dev/loop60 /dev/loop61

# Inspect the VG
vgdisplay vg_data
```

📸 **Verified Output:**
```
  Volume group "vg_data" successfully created

  --- Volume group ---
  VG Name               vg_data
  System ID             
  Format                lvm2
  Metadata Areas        2
  VG Access             read/write
  VG Status             resizable
  Cur LV                0
  Cur PV                2
  Act PV                2
  VG Size               192.00 MiB
  PE Size               4.00 MiB
  Total PE              48
  Alloc PE / Size       0 / 0   
  Free  PE / Size       48 / 192.00 MiB
  VG UUID               g4lLLb-XjFZ-bfPz-MASN-21E8-Th3Y-tmSIa0
```

> 💡 PE (Physical Extent) is LVM's allocation unit — default 4 MiB. All LV sizes are multiples of the PE size.

---

## Step 4: Create a Logical Volume (LV) and Format It

```bash
# Create a 60 MiB logical volume
lvcreate --zero n -L 60M -n lv_data vg_data

# Create device nodes (needed in Docker containers)
vgmknodes vg_data

# Inspect the LV
lvdisplay /dev/mapper/vg_data-lv_data

# Format with ext4
mkfs.ext4 /dev/mapper/vg_data-lv_data
```

📸 **Verified Output:**
```
  WARNING: Logical volume vg_data/lv_data not zeroed.
  Logical volume "lv_data" created.

  --- Logical volume ---
  LV Path                /dev/vg_data/lv_data
  LV Name                lv_data
  VG Name                vg_data
  LV Status              available
  LV Size                60.00 MiB

Creating filesystem with 15360 4k blocks and 15360 inodes
Allocating group tables:   done                            
Writing inode tables:   done                            
Creating journal (1024 blocks): done
Writing superblocks and filesystem accounting information: done
```

---

## Step 5: Mount and Use the Logical Volume

```bash
mkdir -p /mnt/lv_data
mount /dev/mapper/vg_data-lv_data /mnt/lv_data

df -h /mnt/lv_data
echo "LVM test data" > /mnt/lv_data/test.txt
cat /mnt/lv_data/test.txt
```

📸 **Verified Output:**
```
Filesystem                   Size  Used Avail Use% Mounted on
/dev/mapper/vg_data-lv_data   56M   24K   52M   1% /mnt/lv_data

LVM test data
```

> 💡 Use `lvs` for a compact overview of all LVs: `lvs vg_data`

---

## Step 6: Extend a Logical Volume Online

One of LVM's biggest advantages — resize without unmounting!

```bash
# Extend LV by 20 MiB
lvextend -L +20M /dev/mapper/vg_data-lv_data

# Grow the filesystem to fill the new space
resize2fs /dev/mapper/vg_data-lv_data

# Confirm new size
df -h /mnt/lv_data
```

📸 **Verified Output:**
```
  Size of logical volume vg_data/lv_data changed from 60.00 MiB (15 extents) to 80.00 MiB (20 extents).
  Logical volume vg_data/lv_data successfully resized.

resize2fs 1.46.5 (30-Dec-2021)
Filesystem at /dev/mapper/vg_data-lv_data is mounted on /mnt/lv_data; on-line resizing required
The filesystem on /dev/mapper/vg_data-lv_data is now 20480 (4k) blocks long.

Filesystem                   Size  Used Avail Use% Mounted on
/dev/mapper/vg_data-lv_data   75M   24K   69M   1% /mnt/lv_data
```

> 💡 For XFS filesystems, use `xfs_growfs /mnt/lv_data` instead of `resize2fs`. XFS only supports online growth.

---

## Step 7: Extend the Volume Group (pvmove / vgextend)

When a VG runs out of space, add a new PV:

```bash
# Create a third disk
mknod /dev/loop62 b 7 62 2>/dev/null || true
dd if=/dev/zero of=/tmp/disk3.img bs=1M count=100 2>/dev/null
losetup /dev/loop62 /tmp/disk3.img

# Add it as a PV
pvcreate /dev/loop62

# Extend the VG with the new PV
vgextend vg_data /dev/loop62
vgdisplay vg_data | grep -E "VG Size|Free PE|Total PE"
```

📸 **Verified Output:**
```
  Physical volume "/dev/loop62" successfully created.
  Volume group "vg_data" successfully extended

  VG Size               288.00 MiB
  Total PE              72
  Free  PE / Size       52 / 208.00 MiB
```

**pvmove — Migrate data between PVs:**

```bash
# Move all extents off loop60 (to decommission it)
pvmove /dev/loop60 /dev/loop62

# Now remove loop60 from the VG
vgreduce vg_data /dev/loop60
pvremove /dev/loop60
```

> 💡 `pvmove` is non-destructive and works while the filesystem is mounted — great for disk replacement with no downtime.

---

## Step 8: Capstone — Thin Provisioning Concept

Thin provisioning lets you over-allocate storage — logical volumes appear larger than the actual physical backing. 

> ⚠️ Thin pools require `dm-thin-pool` kernel module. In this Docker environment we demonstrate the concept:

```bash
# Concept commands (require dm-thin-pool kernel module on real system):
# lvcreate --type thin-pool -L 60M -n thin_pool vg_data
# lvcreate --type thin -V 200M --thinpool vg_data/thin_pool -n thin_lv1
# lvcreate --type thin -V 200M --thinpool vg_data/thin_pool -n thin_lv2
# lvs vg_data

# On a real system, output would show:
# LV         VG      Attr       LSize   Pool       Data%  
# thin_pool  vg_data twi-a-tz-- 60.00m              0.00 
# thin_lv1   vg_data Vwi-a-tz-- 200.00m thin_pool  0.00 
# thin_lv2   vg_data Vwi-a-tz-- 200.00m thin_pool  0.00 
```

**Capstone Challenge:** Simulate a disk being decommissioned:

```bash
# 1. Create an LV that spans both loop60 and loop61
lvcreate --zero n -L 80M -n lv_span vg_data
vgmknodes vg_data

# 2. See which PV holds the LV's extents
pvdisplay -m /dev/loop60 | grep -A3 "Physical volume"

# 3. Move extents to free PV (loop62)
pvmove /dev/loop60 /dev/loop62

# 4. Remove decommissioned PV from VG
vgreduce vg_data /dev/loop60
echo "PV loop60 safely removed. VG continues operating."
```

---

## Summary

| Concept | Command | Purpose |
|---|---|---|
| Physical Volume | `pvcreate /dev/loop0` | Initialize disk for LVM |
| Volume Group | `vgcreate vg_name PV...` | Pool multiple PVs |
| Logical Volume | `lvcreate -L size -n name VG` | Create virtual disk |
| Inspect | `pvdisplay`, `vgdisplay`, `lvdisplay` | Show LVM info |
| Format | `mkfs.ext4 /dev/mapper/VG-LV` | Create filesystem |
| Extend LV | `lvextend -L +size /dev/VG/LV` | Grow logical volume |
| Grow FS | `resize2fs` / `xfs_growfs` | Expand filesystem |
| Add PV to VG | `vgextend VG /dev/newdisk` | Increase VG capacity |
| Migrate data | `pvmove /dev/old /dev/new` | Relocate extents |
| Thin pool | `lvcreate --type thin-pool` | Over-provision storage |
