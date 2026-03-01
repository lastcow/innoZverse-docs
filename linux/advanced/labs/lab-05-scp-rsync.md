# Lab 5: File Transfer with rsync

## 🎯 Objective
Use rsync for efficient local file synchronization with dry-run, delete, and stats options to understand what will change before committing.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Advanced Lab 3: SSH Key Generation

## 🔬 Lab Instructions

### Step 1: Set Up Test Directories

```bash
mkdir -p /tmp/rsync-src/docs /tmp/rsync-src/scripts /tmp/rsync-dst

echo "Document 1" > /tmp/rsync-src/docs/report.txt
echo "Document 2" > /tmp/rsync-src/docs/notes.txt
echo "#!/bin/bash" > /tmp/rsync-src/scripts/deploy.sh
echo "#!/bin/bash" > /tmp/rsync-src/scripts/backup.sh
echo "Config v1" > /tmp/rsync-src/config.txt

find /tmp/rsync-src
```

### Step 2: Basic rsync

```bash
# -a: archive mode (recursive, preserves permissions, timestamps, symlinks)
# -v: verbose
# -z: compress during transfer
rsync -avz /tmp/rsync-src/ /tmp/rsync-dst/
```

**Expected output:**
```
sending incremental file list
./
config.txt
docs/
docs/notes.txt
docs/report.txt
scripts/
scripts/backup.sh
scripts/deploy.sh
...
sent 456 bytes  received 137 bytes  1186.00 bytes/sec
```

```bash
# Note: trailing / on source is important!
# /tmp/rsync-src/  = sync CONTENTS of src into dst
# /tmp/rsync-src   = sync src DIRECTORY INTO dst (creates src/ inside dst)

ls /tmp/rsync-dst
```

### Step 3: Dry Run (Preview Changes)

```bash
# --dry-run: show what WOULD happen without doing it
rsync -avz --dry-run /tmp/rsync-src/ /tmp/rsync-dst/
echo "Nothing changed (dry-run)"
```

```bash
# Make a change and preview the delta
echo "Updated content" > /tmp/rsync-src/config.txt
echo "New file" > /tmp/rsync-src/new-file.txt

rsync -avz --dry-run /tmp/rsync-src/ /tmp/rsync-dst/
echo ""
echo "Items above would be transferred"
```

```bash
# Now actually sync
rsync -avz /tmp/rsync-src/ /tmp/rsync-dst/
```

### Step 4: Show Statistics

```bash
# --stats: show detailed transfer statistics
rsync -avz --stats /tmp/rsync-src/ /tmp/rsync-dst/ 2>/dev/null | tail -15
```

**Expected output (excerpt):**
```
Number of files: 7 (reg: 6, dir: 1)
Number of files transferred: 0
Total file size: 89 bytes
Total transferred file size: 0 bytes
Speedup is 0.00
```

### Step 5: Delete Files Not in Source

```bash
# --delete: remove files in dst that don't exist in src
touch /tmp/rsync-dst/orphan-file.txt
ls /tmp/rsync-dst/

echo "Before delete sync:"
ls /tmp/rsync-dst/

rsync -avz --delete /tmp/rsync-src/ /tmp/rsync-dst/

echo "After delete sync:"
ls /tmp/rsync-dst/
```

**Expected output:**
```
Before: orphan-file.txt  config.txt  docs/  new-file.txt  scripts/
After:  config.txt  docs/  new-file.txt  scripts/
```

### Step 6: Include and Exclude Patterns

```bash
# Exclude specific files or patterns
rsync -avz --exclude="*.sh" --exclude="*.bak" /tmp/rsync-src/ /tmp/rsync-dst/
echo "Synced without .sh files"
```

```bash
# Exclude a directory
rsync -avz --exclude="scripts/" /tmp/rsync-src/ /tmp/rsync-dst/
ls /tmp/rsync-dst/
```

```bash
# Include only specific files
rsync -avz --include="*.txt" --include="*/" --exclude="*" /tmp/rsync-src/ /tmp/rsync-dst/
ls /tmp/rsync-dst/
```

### Step 7: Sync Only Changed Files (Checksum)

```bash
# --checksum: compare by checksum instead of size+time
rsync -avz --checksum /tmp/rsync-src/ /tmp/rsync-dst/

# --update: skip files that are newer in destination
rsync -avzu /tmp/rsync-src/ /tmp/rsync-dst/
```

### Step 8: Remote rsync Syntax (Reference)

```bash
cat > /tmp/rsync-remote-examples.txt << 'EOF'
# rsync over SSH (remote syntax):

# Local to Remote:
rsync -avz /local/path/ user@server:/remote/path/

# Remote to Local:
rsync -avz user@server:/remote/path/ /local/path/

# With custom SSH options:
rsync -avz -e "ssh -i ~/.ssh/mykey -p 2222" /local/ user@server:/remote/

# Remote to Remote (through local machine):
rsync -avz user@server1:/path/ user@server2:/path/

# Common production command:
rsync -avz --delete --stats --exclude="*.log" \
      /var/www/html/ user@webserver:/var/www/html/
EOF

cat /tmp/rsync-remote-examples.txt
```

## ✅ Verification

```bash
mkdir -p /tmp/rsync-verify-src /tmp/rsync-verify-dst
echo "test1" > /tmp/rsync-verify-src/file1.txt
echo "test2" > /tmp/rsync-verify-src/file2.txt

rsync -avz --dry-run /tmp/rsync-verify-src/ /tmp/rsync-verify-dst/ | grep -c "sending"
rsync -avz /tmp/rsync-verify-src/ /tmp/rsync-verify-dst/
echo "Synced files: $(ls /tmp/rsync-verify-dst | wc -l) (expect 2)"

rm -r /tmp/rsync-src /tmp/rsync-dst /tmp/rsync-verify-src /tmp/rsync-verify-dst /tmp/rsync-remote-examples.txt 2>/dev/null
echo "Advanced Lab 5 complete"
```

## 📝 Summary
- `rsync -avz src/ dst/` syncs contents of src into dst (trailing / matters)
- `-a` (archive) preserves permissions, timestamps, symlinks, owner, group
- `--dry-run` shows what would happen without making changes
- `--delete` removes files in destination that no longer exist in source
- `--stats` shows detailed transfer statistics
- `--exclude="pattern"` skips matching files; `--include` overrides excludes
- Remote syntax: `rsync -avz local/ user@host:/remote/`
