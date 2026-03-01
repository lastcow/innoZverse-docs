# Lab 5: File Transfer with scp and rsync

## 🎯 Objective
Transfer files securely using `scp` and efficiently sync directories with `rsync`, including `--delete`, bandwidth limiting, and dry-run modes.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- SSH key-based authentication configured (Lab 3)

## 🔬 Lab Instructions

### Step 1: Prepare Test Files
```bash
mkdir -p ~/transfer_lab/{source,dest}
echo "Hello from file1" > ~/transfer_lab/source/file1.txt
echo "Hello from file2" > ~/transfer_lab/source/file2.txt
mkdir -p ~/transfer_lab/source/subdir
echo "Nested file" > ~/transfer_lab/source/subdir/nested.txt

ls -la ~/transfer_lab/source/
# total 16
# -rw-rw-r-- 1 ubuntu ubuntu  18 ... file1.txt
# -rw-rw-r-- 1 ubuntu ubuntu  18 ... file2.txt
# drwxrwxr-x 2 ubuntu ubuntu 4096 ... subdir/
```

### Step 2: scp — Copy a Single File
```bash
# Syntax: scp [options] source destination
# Copy to remote:
# scp ~/transfer_lab/source/file1.txt ubuntu@192.168.1.100:/tmp/

# Copy from remote:
# scp ubuntu@192.168.1.100:/tmp/file1.txt ~/transfer_lab/dest/

# Local copy (for practice):
scp ~/transfer_lab/source/file1.txt ~/transfer_lab/dest/
ls ~/transfer_lab/dest/
# file1.txt
```

### Step 3: scp — Copy a Directory Recursively
```bash
# -r flag for recursive directory copy
scp -r ~/transfer_lab/source/ ~/transfer_lab/dest/source_copy/
# file1.txt     100%   18     ...
# file2.txt     100%   18     ...
# nested.txt    100%   12     ...

ls -R ~/transfer_lab/dest/
# dest/:
# file1.txt  source_copy/
# dest/source_copy/:
# file1.txt  file2.txt  subdir/
```

### Step 4: scp — With SSH Options
```bash
# Specify port, key, or other SSH options
# scp -P 2222 -i ~/.ssh/id_ed25519 file.txt user@host:/dest/

# Limit bandwidth (in Kbit/s):
# scp -l 1024 largefile.tar.gz user@host:/backup/
# (limits to 1 Mbit/s)

echo "scp options: -P port, -i key, -l bandwidth_kbit, -r recursive, -C compress"
```

### Step 5: rsync — Basic Sync
```bash
# rsync is faster than scp for incremental transfers
# Only transfers changed files

rsync ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_copy/
ls ~/transfer_lab/dest/rsync_copy/
# file1.txt  file2.txt  subdir/

# rsync local syntax: rsync SOURCE/ DESTINATION/
# (trailing slash on source = copy contents, not the directory itself)
```

### Step 6: rsync -avz — Archive, Verbose, Compressed
```bash
rsync -avz ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/
# sending incremental file list
# ./
# file1.txt
# file2.txt
# subdir/
# subdir/nested.txt
#
# sent 456 bytes  received 92 bytes  1096.00 bytes/sec
# total size is 48  speedup is 0.09

# -a = archive (preserves permissions, timestamps, symlinks, owner)
# -v = verbose
# -z = compress during transfer
```

### Step 7: rsync — Incremental Update
```bash
# Modify one file and sync again
echo "Updated content" >> ~/transfer_lab/source/file1.txt

rsync -avz ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/
# sending incremental file list
# file1.txt     <-- only changed file is transferred!
#
# sent 248 bytes  received 35 bytes  566.00 bytes/sec
# total size is 64  speedup is 0.23
```

### Step 8: rsync --delete — Mirror Exactly
```bash
# Create a file in dest that doesn't exist in source
touch ~/transfer_lab/dest/rsync_verbose/orphan_file.txt

# Without --delete: orphan_file.txt stays
rsync -avz ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/
ls ~/transfer_lab/dest/rsync_verbose/
# file1.txt  file2.txt  orphan_file.txt  subdir/  <-- orphan remains

# With --delete: exact mirror of source
rsync -avz --delete ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/
# deleting orphan_file.txt
ls ~/transfer_lab/dest/rsync_verbose/
# file1.txt  file2.txt  subdir/  <-- orphan removed
```

### Step 9: rsync --dry-run — Preview Changes
```bash
# Always test destructive operations with --dry-run first!
echo "extra file" > ~/transfer_lab/source/newfile.txt
touch ~/transfer_lab/dest/rsync_verbose/will_be_deleted.txt

rsync -avz --delete --dry-run ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/
# (dry run)
# sending incremental file list
# deleting will_be_deleted.txt
# newfile.txt
#
# sent 192 bytes  received 22 bytes  428.00 bytes/sec
# total size is 80  speedup is 0.37 (DRY RUN)
# (no actual changes made)
```

### Step 10: rsync Backup Script
```bash
cat > ~/rsync_backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail
SOURCE="${1:-$HOME/transfer_lab/source}"
DEST="${2:-$HOME/transfer_lab/backup}"
LOG="$HOME/transfer_lab/rsync_backup.log"

echo "=== Backup: $(date) ===" | tee -a "$LOG"
echo "Source: $SOURCE" | tee -a "$LOG"
echo "Dest  : $DEST" | tee -a "$LOG"

rsync -avz --delete \
    --exclude='*.tmp' \
    --exclude='.git/' \
    --log-file="$LOG" \
    "$SOURCE/" "$DEST/"

echo "Backup complete: $(date)" | tee -a "$LOG"
EOF
chmod +x ~/rsync_backup.sh
~/rsync_backup.sh
# === Backup: Sun Mar  1 06:01:00 UTC 2026 ===
# Source: /home/ubuntu/transfer_lab/source
# Dest  : /home/ubuntu/transfer_lab/backup
# Backup complete: Sun Mar  1 06:01:00 UTC 2026
```

## ✅ Verification
```bash
diff -r ~/transfer_lab/source/ ~/transfer_lab/dest/rsync_verbose/ 2>/dev/null \
  && echo "Directories are identical" \
  || echo "Differences found"
```

## 📝 Summary
- `scp -r source/ user@host:/dest/` copies directories recursively over SSH
- `rsync -avz source/ dest/` syncs with archive mode, verbose, and compression
- `rsync --delete` creates an exact mirror (removes files not in source)
- `rsync --dry-run` previews changes without applying them — always use before `--delete`
- `rsync --exclude='pattern'` skips files matching the pattern
