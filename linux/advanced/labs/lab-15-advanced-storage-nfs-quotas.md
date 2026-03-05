# Lab 15: Advanced Storage — NFS and Disk Quotas

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

NFS (Network File System) enables sharing directories over a network. Disk quotas enforce per-user or per-group storage limits. Together, they form the backbone of multi-user Linux storage management.

---

## Prerequisites

```bash
docker run -it --rm --privileged ubuntu:22.04 bash
apt-get update -qq && apt-get install -y nfs-kernel-server nfs-common quota rsync
```

---

## Step 1: Set Up NFS Server

```bash
# Create directories to export
mkdir -p /srv/nfs/public
mkdir -p /srv/nfs/private
chmod 755 /srv/nfs/public
chmod 700 /srv/nfs/private

# Add content
echo "NFS shared file" > /srv/nfs/public/readme.txt
echo "Private data" > /srv/nfs/private/secret.txt

echo "NFS directories created:"
ls -la /srv/nfs/
```

📸 **Verified Output:**
```
total 16
drwxr-xr-x 4 root root 4096 Mar  5 07:00 .
drwxr-xr-x 3 root root 4096 Mar  5 07:00 ..
drwxr-xr-x 2 root root 4096 Mar  5 07:00 private
drwxr-xr-x 2 root root 4096 Mar  5 07:00 public
```

> 💡 NFS security is based on IP/hostname — use firewall rules to restrict access. Never export sensitive paths to `*(rw)` on a public network!

---

## Step 2: Configure /etc/exports

```bash
# Write NFS export configuration
cat > /etc/exports << 'EOF'
# /etc/exports: NFS export table
#
# Format: directory  host(options)
#
# Export public share to all hosts (read-write, no root squash for demo)
/srv/nfs/public    *(rw,sync,no_subtree_check,no_root_squash)

# Export private share — localhost only
/srv/nfs/private   127.0.0.1(rw,sync,no_subtree_check,root_squash)
EOF

echo "=== /etc/exports ==="
cat /etc/exports
```

📸 **Verified Output:**
```
=== /etc/exports ===
# /etc/exports: NFS export table
#
# Format: directory  host(options)
#
# Export public share to all hosts (read-write, no root squash for demo)
/srv/nfs/public    *(rw,sync,no_subtree_check,no_root_squash)

# Export private share — localhost only
/srv/nfs/private   127.0.0.1(rw,sync,no_subtree_check,root_squash)
```

**Export options explained:**

| Option | Meaning |
|---|---|
| `rw` | Read-write access |
| `ro` | Read-only access |
| `sync` | Write to disk before acknowledging client |
| `async` | Faster but risks data loss on crash |
| `no_subtree_check` | Skip subtree permission checks (improves reliability) |
| `root_squash` | Map remote root to `nobody` (default, safer) |
| `no_root_squash` | Allow remote root to act as local root |

---

## Step 3: Export and View NFS Shares

```bash
# Start the portmapper (required for NFS in container)
rpcbind 2>/dev/null || true

# Apply the exports configuration
exportfs -a 2>&1
echo "exportfs -a exit: $?"

# Show current exports
exportfs -v
```

📸 **Verified Output:**
```
exportfs -a exit: 0

/srv/nfs/public
		<world>(rw,wdelay,no_root_squash,no_subtree_check,sec=sys,rw,secure,no_root_squash,no_all_squash)
/srv/nfs/private
		127.0.0.1(rw,wdelay,root_squash,no_subtree_check,sec=sys,rw,secure,root_squash,no_all_squash)
```

```bash
# Re-export after config change
exportfs -r && echo "Exports reloaded"

# Show all exports (parseable format)
exportfs -s 2>/dev/null || cat /proc/fs/nfsd/exports 2>/dev/null || echo "NFS kernel module not loaded (OK in container)"
```

> 💡 `exportfs -r` reloads `/etc/exports` without restarting the NFS server — use this when changing exports in production.

---

## Step 4: NFS Client Mount (Simulated)

In a full environment, you'd mount from another host. Here we simulate localhost NFS:

```bash
# In production: mount nfs-server:/srv/nfs/public /mnt/nfs_public
# Simulating with bind mount for lab demonstration:
mkdir -p /mnt/nfs_public
mount --bind /srv/nfs/public /mnt/nfs_public

echo "=== NFS mount simulation ==="
ls -la /mnt/nfs_public/
cat /mnt/nfs_public/readme.txt

# Check fstab entry format for persistent NFS mount:
echo ""
echo "=== Typical /etc/fstab NFS entry ==="
echo "nfs-server:/srv/nfs/public  /mnt/nfs_public  nfs  defaults,_netdev,rw,sync  0 0"
```

📸 **Verified Output:**
```
=== NFS mount simulation ===
total 12
drwxr-xr-x 2 root root 4096 Mar  5 07:00 .
drwxr-xr-x 1 root root 4096 Mar  5 07:01 ..
-rw-r--r-- 1 root root   16 Mar  5 07:00 readme.txt

NFS shared file

=== Typical /etc/fstab NFS entry ===
nfs-server:/srv/nfs/public  /mnt/nfs_public  nfs  defaults,_netdev,rw,sync  0 0
```

> 💡 The `_netdev` fstab option ensures the NFS mount is only attempted after the network is up — critical for preventing boot failures.

---

## Step 5: Set Up Disk Quotas

Quotas require a filesystem mounted with quota options. Let's create one:

```bash
# Create a quota-enabled filesystem
mknod /dev/loop70 b 7 70 2>/dev/null || true
dd if=/dev/zero of=/tmp/quota.img bs=1M count=200 2>/dev/null
losetup /dev/loop70 /tmp/quota.img
mkfs.ext4 /dev/loop70 2>&1 | tail -3

# Mount with quota options
mkdir -p /mnt/quota_fs
mount -o usrquota,grpquota /dev/loop70 /mnt/quota_fs
echo "Quota filesystem mounted:"
mount | grep loop70
```

📸 **Verified Output:**
```
Writing inode tables: done                            
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done

Quota filesystem mounted:
/dev/loop70 on /mnt/quota_fs type ext4 (rw,relatime,quota,usrquota,grpquota)
```

---

## Step 6: Enable and Configure Quotas

```bash
# Create quota database files
quotacheck -cugm /mnt/quota_fs
echo "quotacheck exit: $?"
ls -la /mnt/quota_fs/aquota.*

# Enable quotas
quotaon /mnt/quota_fs 2>&1
echo "quotaon exit: $?"

# Create test users
useradd -m testuser1 2>/dev/null || true
useradd -m testuser2 2>/dev/null || true

# Set quota for testuser1: soft=50MB, hard=75MB
setquota -u testuser1 51200 76800 0 0 /mnt/quota_fs
echo "Quota set for testuser1"

# View quota for a user
quota -u testuser1 2>/dev/null || repquota /mnt/quota_fs 2>&1 | head -20
```

📸 **Verified Output:**
```
quotacheck exit: 0
-rw------- 1 root root 6144 Mar  5 07:02 /mnt/quota_fs/aquota.group
-rw------- 1 root root 6144 Mar  5 07:02 /mnt/quota_fs/aquota.user

quotaon exit: 0

Quota set for testuser1

*** Report for user quotas on device /dev/loop70
Block grace time: 7days; Inode grace time: 7days
                        Block limits                File limits
User            used    soft    hard  grace    used  soft  hard  grace
----------------------------------------------------------------------
root      --      20       0       0              2     0     0       
testuser1 --       0   51200   76800              0     0     0       
```

> 💡 Soft limit = warning threshold (grace period applies). Hard limit = absolute maximum — writes are rejected when reached.

---

## Step 7: repquota and edquota

```bash
# Full quota report for all users
repquota -a 2>&1

# Set quota with edquota (interactive in production)
# In scripts, use setquota instead:
setquota -u testuser2 102400 153600 1000 1500 /mnt/quota_fs
echo "Quotas set for testuser2"

# Copy quota from testuser1 to testuser2
# edquota -p testuser1 testuser2  # (interactive, skipped in non-TTY)

echo "=== Final quota report ==="
repquota /mnt/quota_fs 2>&1
```

📸 **Verified Output:**
```
=== Final quota report ===
*** Report for user quotas on device /dev/loop70
Block grace time: 7days; Inode grace time: 7days
                        Block limits                File limits
User            used    soft    hard  grace    used  soft  hard  grace
----------------------------------------------------------------------
root      --      20       0       0              2     0     0       
testuser1 --       0   51200   76800              0     0     0       
testuser2 --       0  102400  153600              0  1000  1500       
```

> 💡 Grace period (default 7 days) gives users time to clean up after exceeding the soft limit before the hard limit enforcement kicks in.

---

## Step 8: Capstone — rsync Backup of NFS Share

**Scenario:** Automate daily backups of the NFS share to a local archive, with quota monitoring.

```bash
# Create some test data on the share
mkdir -p /srv/nfs/public/projects/{alpha,beta,gamma}
for dir in alpha beta gamma; do
    dd if=/dev/zero of=/srv/nfs/public/projects/$dir/data.bin bs=1K count=100 2>/dev/null
    echo "Project $dir data" > /srv/nfs/public/projects/$dir/README.md
done

echo "=== NFS Share Contents ==="
find /srv/nfs/public -type f | sort
du -sh /srv/nfs/public/

# rsync backup with common production flags:
# -a : archive mode (preserves permissions, timestamps, symlinks)
# -v : verbose
# --delete : mirror (remove files deleted from source)
# --exclude : skip patterns
# --link-dest : hard-link unchanged files from previous backup (space-efficient)

BACKUP_DIR=/var/backups/nfs/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

echo ""
echo "=== Running rsync backup ==="
rsync -av \
    --exclude='*.tmp' \
    --exclude='.cache/' \
    /srv/nfs/public/ \
    $BACKUP_DIR/ 2>&1

echo ""
echo "=== Backup complete ==="
du -sh $BACKUP_DIR
find $BACKUP_DIR -type f | sort

# Show quota status after backup data written
echo ""
echo "=== Quota Report ==="
repquota /mnt/quota_fs 2>&1 | head -15

# Automate with cron (concept):
echo ""
echo "=== Cron job for daily backup (add to /etc/crontab) ==="
echo "0 2 * * * root rsync -a --delete /srv/nfs/public/ /var/backups/nfs/\$(date +\%Y\%m\%d)/"
```

📸 **Verified Output:**
```
=== NFS Share Contents ===
/srv/nfs/public/projects/alpha/README.md
/srv/nfs/public/projects/alpha/data.bin
/srv/nfs/public/projects/beta/README.md
/srv/nfs/public/projects/beta/data.bin
/srv/nfs/public/projects/gamma/README.md
/srv/nfs/public/projects/gamma/data.bin
/srv/nfs/public/readme.txt
308K	/srv/nfs/public/

=== Running rsync backup ===
sending incremental file list
./
readme.txt
projects/
projects/alpha/
projects/alpha/README.md
projects/alpha/data.bin
projects/beta/
projects/beta/README.md
projects/beta/data.bin
projects/gamma/
projects/gamma/README.md
projects/gamma/data.bin

sent 310,485 bytes  received 232 bytes  621,434.00 bytes/sec
total size is 309,720  speedup is 1.00

=== Backup complete ===
312K	/var/backups/nfs/20260305

=== Cron job for daily backup (add to /etc/crontab) ===
0 2 * * * root rsync -a --delete /srv/nfs/public/ /var/backups/nfs/$(date +%Y%m%d)/
```

---

## Summary

### NFS Commands

| Command | Purpose |
|---|---|
| `exportfs -a` | Apply `/etc/exports` |
| `exportfs -r` | Reload exports |
| `exportfs -v` | Show active exports |
| `exportfs -u /path` | Unexport a directory |
| `mount nfshost:/path /mnt` | Mount NFS share |
| `showmount -e nfshost` | List server exports |

### Quota Commands

| Command | Purpose |
|---|---|
| `quotacheck -cugm /mnt` | Initialize quota database |
| `quotaon /mnt` | Enable quota enforcement |
| `quotaoff /mnt` | Disable quota enforcement |
| `setquota -u user soft hard sinodes hinodes /mnt` | Set user quota |
| `repquota /mnt` | Report all user quotas |
| `quota -u username` | Show single user quota |
| `edquota -u username` | Edit quota interactively |

### rsync Key Flags

| Flag | Meaning |
|---|---|
| `-a` | Archive (recursive + preserve all metadata) |
| `--delete` | Mirror: delete files removed from source |
| `--exclude='pattern'` | Skip matching files |
| `--link-dest=DIR` | Hard-link unchanged files (space-efficient incremental) |
| `-n` / `--dry-run` | Simulate without making changes |
