# Lab 8: chmod — Changing File Permissions

## 🎯 Objective
Use `chmod` with both symbolic and octal notation to change file and directory permissions, and understand practical use cases for each.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 7 (Understanding Permissions)
- Understanding of rwx and octal notation

## 🔬 Lab Instructions

### Step 1: Set Up Test Files
```bash
mkdir ~/lab08
cd ~/lab08
touch script.sh config.conf data.txt private.key
ls -l
```

### Step 2: chmod with Octal Notation
```bash
# Set permissions to 644 (rw-r--r--)
chmod 644 data.txt
ls -l data.txt
# Output: -rw-r--r-- 1 student student 0 ...

# Set permissions to 755 (rwxr-xr-x) — typical for scripts
chmod 755 script.sh
ls -l script.sh
# Output: -rwxr-xr-x 1 student student 0 ...

# Set permissions to 600 (rw-------) — private file
chmod 600 private.key
ls -l private.key
# Output: -rw------- 1 student student 0 ...

# Set permissions to 400 (r--------) — read-only private
chmod 400 config.conf
ls -l config.conf
# Output: -r-------- 1 student student 0 ...
```

### Step 3: chmod with Symbolic Notation
Symbolic format: `[who][operator][permissions]`
- **who**: `u` (user/owner), `g` (group), `o` (other), `a` (all)
- **operator**: `+` (add), `-` (remove), `=` (set exactly)
- **permissions**: `r`, `w`, `x`

```bash
# Reset permissions first
chmod 000 data.txt
ls -l data.txt
# Output: ----------

# Add read permission for owner
chmod u+r data.txt
ls -l data.txt
# Output: -r--------

# Add write for owner
chmod u+w data.txt
ls -l data.txt
# Output: -rw-------

# Add read for group and other
chmod go+r data.txt
ls -l data.txt
# Output: -rw-r--r--
```

### Step 4: Remove Permissions Symbolically
```bash
chmod 755 script.sh
ls -l script.sh
# Output: -rwxr-xr-x

# Remove execute from group and other
chmod go-x script.sh
ls -l script.sh
# Output: -rwxr--r--

# Remove write from everyone
chmod a-w script.sh
ls -l script.sh
# Output: -r-xr--r--
```

### Step 5: Set Exact Permissions with `=`
```bash
# Set owner to rw, group to r, other to nothing
chmod u=rw,g=r,o= data.txt
ls -l data.txt
# Output: -rw-r-----
```

### Step 6: Make a Script Executable
```bash
cat > ~/lab08/hello.sh << 'EOF'
#!/bin/bash
echo "Hello from the script!"
EOF

# Try to run it without execute permission
ls -l ~/lab08/hello.sh
# Output: -rw-rw-r--

bash ~/lab08/hello.sh
# Works (bash interprets it)

./hello.sh
# Output: bash: ./hello.sh: Permission denied

# Add execute permission
chmod +x ~/lab08/hello.sh
ls -l ~/lab08/hello.sh
# Output: -rwxrwxr-x

./hello.sh
# Output: Hello from the script!
```

### Step 7: chmod on Directories
```bash
mkdir ~/lab08/testdir
ls -ld ~/lab08/testdir
# Output: drwxrwxr-x

# Remove execute from directory (breaks access!)
chmod go-x ~/lab08/testdir
ls ~/lab08/testdir
# Output: ls: cannot access '...': Permission denied

# Restore
chmod go+x ~/lab08/testdir
ls ~/lab08/testdir
# Works again
```

### Step 8: Recursive chmod with `-R`
```bash
mkdir -p ~/lab08/project/{src,docs,tests}
touch ~/lab08/project/src/main.py ~/lab08/project/docs/readme.md

ls -lR ~/lab08/project/

# Apply permissions recursively
chmod -R 755 ~/lab08/project/
ls -lR ~/lab08/project/
# All files and dirs are now 755
```

### Step 9: Practical Permission Scenarios
```bash
# Web server public directory: world-readable
chmod 755 ~/lab08/testdir

# Shared group collaboration directory
chmod 770 ~/lab08/testdir
# Owner and group can rwx, others get nothing

# Secure backup file
chmod 600 ~/lab08/private.key

# Configuration file (readable by all, writable by owner)
chmod 644 ~/lab08/config.conf
```

### Step 10: View Numeric Permissions with `stat`
```bash
stat --format="%a %n" ~/lab08/script.sh
stat --format="%a %n" ~/lab08/private.key
stat --format="%a %n" ~/lab08/data.txt
```

### Step 11: Set Permissions at Creation Time
```bash
# Use install command to copy with specific permissions
echo "data" > /tmp/source.txt
install -m 644 /tmp/source.txt ~/lab08/installed.txt
ls -l ~/lab08/installed.txt
# Output: -rw-r--r--
```

### Step 12: Clean Up
```bash
cd ~
rm -rf ~/lab08
```

## ✅ Verification
```bash
# Create a script and set appropriate permissions
echo '#!/bin/bash\necho "test"' > /tmp/test_chmod.sh
chmod 750 /tmp/test_chmod.sh
stat --format="%a %n" /tmp/test_chmod.sh
# Output: 750 /tmp/test_chmod.sh

ls -l /tmp/test_chmod.sh
# Output: -rwxr-x--- ...

rm /tmp/test_chmod.sh
```

## 📝 Summary
- `chmod` changes file permissions using octal (e.g., `644`) or symbolic (e.g., `u+x`) notation
- Octal is fast for absolute settings; symbolic is intuitive for adding/removing specific bits
- `+` adds permissions, `-` removes, `=` sets exactly
- `chmod -R` applies permissions recursively to directories and their contents
- Never use `777` in production — it gives everyone full access including write and execute
