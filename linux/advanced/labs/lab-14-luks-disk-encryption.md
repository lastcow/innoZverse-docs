# Lab 14: LUKS Disk Encryption

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

LUKS (Linux Unified Key Setup) is the standard for block-level disk encryption on Linux. It sits between the raw block device and the filesystem, transparently encrypting all data at rest using AES.

---

## Prerequisites

```bash
docker run -it --rm --privileged ubuntu:22.04 bash
apt-get update -qq && apt-get install -y cryptsetup
```

---

## Step 1: Create a Loopback Device for Encryption

```bash
# Create a 100 MiB "virtual disk"
dd if=/dev/zero of=/tmp/encrypted.img bs=1M count=100

# Attach to a loop device
mknod /dev/loop50 b 7 50 2>/dev/null || true
losetup /dev/loop50 /tmp/encrypted.img

echo "Device ready:"
losetup -a | grep loop50

# Verify the raw device (no filesystem yet)
file -s /dev/loop50
```

📸 **Verified Output:**
```
100+0 records in
100+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.365 s, 287 MB/s

/dev/loop50: [0118]:2111721 (/tmp/encrypted.img)
/dev/loop50: data
```

> 💡 LUKS works with any block device: physical disks, partitions, LVM volumes, or loopback devices.

---

## Step 2: Format the Device with LUKS

```bash
# Save the passphrase to a keyfile (for scripted use)
echo "MySecurePassphrase123" > /tmp/keyfile
chmod 600 /tmp/keyfile

# Format the device with LUKS2 (default in modern cryptsetup)
cryptsetup luksFormat --batch-mode --key-file /tmp/keyfile /dev/loop50

echo "LUKS format complete. Exit: $?"
```

📸 **Verified Output:**
```
WARNING: Device /dev/loop50 already contains a 'data' superblock signature.

WARNING!
========
This will overwrite data on /dev/loop50 irrevocably.

LUKS format complete. Exit: 0
```

> 💡 `--batch-mode` suppresses the interactive confirmation prompt. Never use this without being sure about the device! In production, type `YES` manually.

---

## Step 3: Inspect LUKS Header with luksDump

```bash
cryptsetup luksDump /dev/loop50
```

📸 **Verified Output:**
```
LUKS header information
Version:       	2
Epoch:         	3
Metadata area: 	16384 [bytes]
Keyslots area: 	16744448 [bytes]
UUID:          	54d2c3d2-2fdc-481d-a1e3-9ad967602c21
Label:         	(no label)
Subsystem:     	(no subsystem)
Flags:       	(no flags)

Data segments:
  0: crypt
	offset: 16777216 [bytes]
	length: (whole device)
	cipher: aes-xts-plain64
	sector size: 512

Keyslots:
  0: luks2
	Key:        512 bits
	Priority:   normal
	Cipher:     aes-xts-plain64
	Cipher key: 512 bits
	PBKDF:      argon2id
	Time cost:  4
	Memory:     1048576
	Threads:    4
	Salt:       ...
	AF stripes: 4000
	AF hash:    sha256
	Area offset:32768 [bytes]
	Area length:258048 [bytes]
	Digest ID:  0
```

> 💡 LUKS2 supports up to 32 key slots — you can have multiple passphrases or keyfiles that all unlock the same volume. The actual encryption key is stored encrypted in each slot.

---

## Step 4: Open the Encrypted Device

```bash
# Open/unlock the LUKS device — creates /dev/mapper/secure_vol
cryptsetup luksOpen --key-file /tmp/keyfile /dev/loop50 secure_vol

# Check the status
cryptsetup status secure_vol
```

📸 **Verified Output:**
```
/dev/mapper/secure_vol is active and is in use.
  type:    LUKS2
  cipher:  aes-xts-plain64
  keysize: 512 bits
  key location: keyring
  device:  /dev/loop50
  loop:    /tmp/encrypted.img
  sector size:  512
  offset:  32768 sectors
  size:    172032 sectors
  mode:    read/write
```

```bash
# The decrypted device appears in /dev/mapper/
ls -la /dev/mapper/
```

📸 **Verified Output:**
```
total 0
drwxr-xr-x  2 root root      80 Mar  5 06:52 .
drwxr-xr-x 18 root root    3760 Mar  5 06:52 ..
crw-------  1 root root 10, 236 Mar  5 06:51 control
brw-rw----  1 root disk 252,   0 Mar  5 06:52 secure_vol
```

---

## Step 5: Create a Filesystem and Mount

```bash
# Create a filesystem on the DECRYPTED device (not the raw LUKS device)
mkfs.ext4 /dev/mapper/secure_vol

mkdir -p /mnt/secure
mount /dev/mapper/secure_vol /mnt/secure
echo "Encrypted filesystem mounted OK"

df -h /mnt/secure

# Write sensitive data
echo "TOP SECRET: server credentials" > /mnt/secure/secrets.txt
ls -la /mnt/secure/
```

📸 **Verified Output:**
```
mke2fs 1.46.5 (30-Dec-2021)
Creating filesystem with 21504 4k blocks and 21504 inodes

Writing inode tables: done                            
Creating journal (1024 blocks): done
Writing superblocks and filesystem accounting information: done

Encrypted filesystem mounted OK

Filesystem              Size  Used Avail Use% Mounted on
/dev/mapper/secure_vol   75M   24K   69M   1% /mnt/secure

total 24
drwxr-xr-x 3 root root  4096 Mar  5 06:52 .
drwxr-xr-x 1 root root  4096 Mar  5 06:52 ..
drwx------ 2 root root 16384 Mar  5 06:52 lost+found
-rw-r--r-- 1 root root    32 Mar  5 06:52 secrets.txt
```

---

## Step 6: Close the Encrypted Device

```bash
# Unmount the filesystem first
umount /mnt/secure

# Close (lock) the LUKS device
cryptsetup luksClose secure_vol

echo "Device locked. Status:"
cryptsetup status secure_vol 2>&1

# Verify the raw device shows as encrypted data
file -s /dev/loop50
```

📸 **Verified Output:**
```
/dev/mapper/secure_vol is inactive.

/dev/loop50: LUKS encrypted file, ver 2 [, , sha256] UUID: 54d2c3d2-2fdc-481d-a1e3-9ad967602c21
```

> 💡 After `luksClose`, the decrypted device disappears from `/dev/mapper/`. The data on disk is fully encrypted — without the passphrase, it's unreadable.

---

## Step 7: Add a Second Key (luksAddKey)

```bash
# Add a second passphrase to key slot 1
echo "EmergencyPassphrase456" > /tmp/keyfile2
chmod 600 /tmp/keyfile2

cryptsetup luksAddKey \
    --key-file /tmp/keyfile \
    /dev/loop50 \
    /tmp/keyfile2

echo "Second key added. Exit: $?"

# Verify both key slots are active
cryptsetup luksDump /dev/loop50 | grep -E "^Keyslots:|  [0-9]+: luks"
```

📸 **Verified Output:**
```
Second key added. Exit: 0

Keyslots:
  0: luks2
  1: luks2
```

```bash
# Open using the SECOND keyfile to verify
cryptsetup luksOpen --key-file /tmp/keyfile2 /dev/loop50 secure_vol2
cryptsetup status secure_vol2 2>&1 | head -3
cryptsetup luksClose secure_vol2
```

> 💡 Common key slot uses: slot 0 = admin passphrase, slot 1 = recovery key, slot 2 = automation keyfile. Revoke a slot with `cryptsetup luksKillSlot /dev/sda1 1`.

---

## Step 8: Capstone — Auto-mount with /etc/crypttab

In production, encrypted devices are configured to unlock at boot via `/etc/crypttab`.

```bash
# Get the UUID of the LUKS device
LUKS_UUID=$(cryptsetup luksDump /dev/loop50 | grep "^UUID:" | awk '{print $2}')
echo "LUKS UUID: $LUKS_UUID"

# /etc/crypttab format:
# name          source-device       key-file    options
echo "# /etc/crypttab entry:"
echo "secure_vol   UUID=$LUKS_UUID   /etc/luks-keys/secure.key   luks"

# Write it (for demonstration)
mkdir -p /etc/luks-keys
cp /tmp/keyfile /etc/luks-keys/secure.key
chmod 600 /etc/luks-keys/secure.key

cat >> /etc/crypttab << EOF
secure_vol   UUID=$LUKS_UUID   /etc/luks-keys/secure.key   luks
EOF

echo "=== /etc/crypttab ==="
cat /etc/crypttab

# /etc/fstab entry for the decrypted device:
echo ""
echo "=== Corresponding /etc/fstab entry ==="
echo "/dev/mapper/secure_vol   /mnt/secure   ext4   defaults,noatime   0 2"

# Test the full unlock → mount workflow
cryptsetup luksOpen --key-file /etc/luks-keys/secure.key /dev/loop50 secure_vol
mount /dev/mapper/secure_vol /mnt/secure
echo "Auto-mount workflow complete:"
cat /mnt/secure/secrets.txt
```

📸 **Verified Output:**
```
LUKS UUID: 54d2c3d2-2fdc-481d-a1e3-9ad967602c21

# /etc/crypttab entry:
secure_vol   UUID=54d2c3d2-2fdc-481d-a1e3-9ad967602c21   /etc/luks-keys/secure.key   luks

=== /etc/crypttab ===
secure_vol   UUID=54d2c3d2-2fdc-481d-a1e3-9ad967602c21   /etc/luks-keys/secure.key   luks

=== Corresponding /etc/fstab entry ===
/dev/mapper/secure_vol   /mnt/secure   ext4   defaults,noatime   0 2

Auto-mount workflow complete:
TOP SECRET: server credentials
```

---

## Summary

| Command | Purpose |
|---|---|
| `cryptsetup luksFormat --batch-mode /dev/sda1` | Format device with LUKS |
| `cryptsetup luksOpen /dev/sda1 myname` | Unlock → create `/dev/mapper/myname` |
| `cryptsetup luksClose myname` | Lock the device |
| `cryptsetup status myname` | Show active mapping info |
| `cryptsetup luksDump /dev/sda1` | Show LUKS header details |
| `cryptsetup luksAddKey /dev/sda1 keyfile2` | Add a second key/passphrase |
| `cryptsetup luksKillSlot /dev/sda1 1` | Remove key slot 1 |
| `/etc/crypttab` | Auto-unlock at boot |
| `mkfs.ext4 /dev/mapper/myname` | Format decrypted device |

| LUKS2 Concept | Detail |
|---|---|
| Cipher | `aes-xts-plain64` (default, AES 256-bit) |
| Key slots | Up to 32 independent passphrases/keyfiles |
| PBKDF | `argon2id` — slow hash to resist brute force |
| Header size | 16 MiB — can be backed up with `cryptsetup luksHeaderBackup` |
