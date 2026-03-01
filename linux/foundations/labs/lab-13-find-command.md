# Lab 13: The find Command

## 🎯 Objective
Master the `find` command to search for files by name, type, size, modification time, and execute actions on the results.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Labs 1–6
- Familiarity with file types and permissions

## 🔬 Lab Instructions

### Step 1: Basic find Syntax
```bash
# find [where] [what criteria] [what to do]
find /tmp -name "*.txt"

# Find everything in home directory
find ~ -maxdepth 1
```

### Step 2: Find by Name
```bash
# Exact filename match
find / -name "passwd" 2>/dev/null
# Output: /etc/passwd

# Case-insensitive search
find /etc -iname "hosts"
# Matches hosts, Hosts, HOSTS

# Wildcard in name
find /etc -name "*.conf" 2>/dev/null | head -10
# Lists .conf files in /etc
```

### Step 3: Find by File Type
```bash
# -type f = regular file
# -type d = directory
# -type l = symbolic link
# -type b = block device
# -type c = character device

find /etc -type d | head -10
# Lists only directories in /etc

find /dev -type c | head -10
# Lists character devices
```

### Step 4: Find by Size
```bash
# Exact size: -size N (N = 512-byte blocks)
# +N = greater than N, -N = less than N
# c = bytes, k = kilobytes, M = megabytes, G = gigabytes

# Find files larger than 10MB
find /var -size +10M 2>/dev/null

# Find files smaller than 1KB
find /tmp -size -1k

# Find files exactly 0 bytes (empty files)
find /tmp -size 0
```

### Step 5: Find by Modification Time
```bash
# -mtime N: modified N days ago
# -mtime +N: more than N days ago
# -mtime -N: less than N days ago
# -mmin: same but in minutes

# Files modified in the last 24 hours
find /var/log -mtime -1 2>/dev/null | head -5

# Files modified more than 7 days ago
find /tmp -mtime +7

# Files modified in the last 60 minutes
find /var/log -mmin -60 2>/dev/null | head -5
```

### Step 6: Find by Permissions
```bash
# Find world-writable files (security risk!)
find /tmp -perm -o+w -type f 2>/dev/null

# Find setuid files (run as owner, often root)
find /usr/bin -perm -4000 2>/dev/null
# Shows programs like passwd, sudo

# Find files with exact permissions 644
find ~ -perm 644 -type f | head -5
```

### Step 7: Find by Owner
```bash
# Find files owned by specific user
find /home -user $USER -type f | head -5

# Find files owned by root
find /etc -user root -type f | head -5

# Find files with no owner (orphaned)
find / -nouser 2>/dev/null | head -5
```

### Step 8: Combining Criteria with AND, OR, NOT
```bash
# AND (default — both conditions must be true)
find /etc -type f -name "*.conf" | head -5

# OR: use -o
find /tmp -name "*.txt" -o -name "*.log" | head -5

# NOT: use !
find /etc -type f ! -name "*.conf" | head -5
```

### Step 9: Execute Commands on Found Files with `-exec`
```bash
# Create test files
mkdir -p /tmp/findtest
touch /tmp/findtest/file{1..5}.txt
touch /tmp/findtest/data{1..3}.csv

# Print details of found files
find /tmp/findtest -name "*.txt" -exec ls -l {} \;
# {} is replaced by each found file
# \; ends the -exec command

# Count lines in each file
find /tmp/findtest -name "*.txt" -exec wc -l {} \;
```

### Step 10: Use `-exec` with `+` for Efficiency
```bash
# {} \; runs the command once per file
# {} + passes ALL files to the command at once (more efficient)

find /tmp/findtest -name "*.txt" -exec ls -l {} +
# ls is called once with all files as arguments
```

### Step 11: Delete Found Files with `-delete`
```bash
# Create some temp files
touch /tmp/findtest/old_{1..3}.tmp

# Find and delete all .tmp files
find /tmp/findtest -name "*.tmp" -delete
ls /tmp/findtest/
# .tmp files are gone
```

### Step 12: Practical Examples
```bash
# Find large log files
find /var/log -name "*.log" -size +1M 2>/dev/null

# Find recently modified config files
find /etc -name "*.conf" -mtime -7 2>/dev/null

# Find and print recently created files
find /tmp -mmin -10 -type f

# Find files and copy them to a directory
mkdir /tmp/txtbackup
find /tmp/findtest -name "*.txt" -exec cp {} /tmp/txtbackup/ \;
ls /tmp/txtbackup/

# Clean up
rm -rf /tmp/findtest /tmp/txtbackup
```

## ✅ Verification
```bash
# Create test structure and use find
mkdir -p /tmp/findverify
touch /tmp/findverify/test.txt
touch /tmp/findverify/test.log
mkdir /tmp/findverify/subdir

# Find all files (not dirs)
find /tmp/findverify -type f
# Output: /tmp/findverify/test.txt  /tmp/findverify/test.log

# Find dirs only
find /tmp/findverify -type d
# Output: /tmp/findverify  /tmp/findverify/subdir

rm -rf /tmp/findverify
```

## 📝 Summary
- `find [path] [criteria]` is a powerful file search tool that works recursively
- Filter by name (`-name`), type (`-type`), size (`-size`), time (`-mtime/-mmin`), owner (`-user`)
- `-exec cmd {} \;` runs a command for each file found; `{} +` is more efficient for bulk operations
- `-delete` removes found files — use carefully, always test with `-print` first
- Combine criteria with AND (default), OR (`-o`), NOT (`!`) for precise searches
