# Lab 7: Understanding File Permissions

## 🎯 Objective
Understand the Linux permission model by reading `ls -l` output, interpreting `rwx` meaning, and working with octal notation for permissions.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–6
- Basic file creation and navigation skills

## 🔬 Lab Instructions

### Step 1: View Permissions with `ls -l`
```bash
ls -l /etc/passwd
# Output: -rw-r--r-- 1 root root 2847 Mar  1 05:00 /etc/passwd
#          ^^^^^^^^^
#          Permission bits
```

### Step 2: Decode the Permission String
The 10-character string breaks down as:
```
- rw- r-- r--
│ │   │   └── Other (everyone else): read only
│ │   └─────── Group: read only
│ └─────────── Owner (user): read + write
└───────────── File type: - = file, d = directory, l = symlink
```

```bash
# Look at several files to practice reading
ls -l /etc/shadow
# Output: -rw-r----- root shadow  (owner rw, group r, other none)

ls -ld /tmp
# Output: drwxrwxrwt  (directory, all can rwx, t = sticky bit)

ls -la ~
# Shows permissions on your home directory files
```

### Step 3: Understand r, w, x for Files vs Directories
```bash
# For FILES:
# r (read)    = can read file content
# w (write)   = can modify file content
# x (execute) = can run as a program

# For DIRECTORIES:
# r (read)    = can list directory contents (ls)
# w (write)   = can create/delete files inside
# x (execute) = can enter (cd) and access files inside
```

### Step 4: The Three Permission Groups
```bash
# User (owner), Group, Other
# Example: rwxr-xr--
# User:  rwx = 7 (read + write + execute)
# Group: r-x = 5 (read + execute)
# Other: r-- = 4 (read only)
```

### Step 5: Learn Octal Notation
Each permission has a numeric value:
```
r = 4
w = 2
x = 1
- = 0
```

Add them together for each group:
```
rwx = 4+2+1 = 7
rw- = 4+2+0 = 6
r-x = 4+0+1 = 5
r-- = 4+0+0 = 4
--- = 0+0+0 = 0
```

Common permission sets:
```
755 = rwxr-xr-x  (executable scripts/dirs)
644 = rw-r--r--  (regular files)
600 = rw-------  (private files like SSH keys)
777 = rwxrwxrwx  (world-writable — avoid!)
```

### Step 6: View Permission Details on Different File Types
```bash
# Regular file
ls -l /etc/hosts
# Output: -rw-r--r-- 1 root root 220 ...

# Executable
ls -l /usr/bin/ls
# Output: -rwxr-xr-x 1 root root 138856 ...

# Directory
ls -ld /home
# Output: drwxr-xr-x 3 root root 4096 ...

# Symlink
ls -la /bin
# Output: lrwxrwxrwx 1 root root 7 ... /bin -> usr/bin
```

### Step 7: View Octal Permissions with `stat`
```bash
stat /etc/hosts
# Output includes: Access: (0644/-rw-r--r--)

stat --format="%a %n" /etc/hosts
# Output: 644 /etc/hosts

stat --format="%a %n" /usr/bin/ls
# Output: 755 /usr/bin/ls
```

### Step 8: Create Files and Observe Default Permissions
```bash
touch ~/perm_test.txt
ls -l ~/perm_test.txt
# Output: -rw-rw-r-- 1 student student 0 ...
# Default permissions are controlled by umask
```

### Step 9: Understand umask
```bash
umask
# Output: 0022  (or 0002 on some systems)

# umask subtracts from default permissions
# Default file: 666 - 022 = 644
# Default dir:  777 - 022 = 755

# Change umask temporarily
umask 0077
touch ~/private_test.txt
ls -l ~/private_test.txt
# Output: -rw------- (600 — only owner can read/write)

# Restore umask
umask 0022
```

### Step 10: Special Permissions — Setuid, Setgid, Sticky Bit
```bash
# Setuid (s in user execute position): runs as file owner
ls -l /usr/bin/passwd
# Output: -rwsr-xr-x root root ... (s = setuid)

# Sticky bit (t in other execute position): only owner can delete
ls -ld /tmp
# Output: drwxrwxrwt  (t = sticky bit)

# Setgid on directory: new files inherit group
ls -ld /var/mail
# Output: drwxrwsr-x (s in group execute)
```

### Step 11: Compare File and Directory Permission Effects
```bash
mkdir ~/permtest
echo "secret" > ~/permtest/data.txt

# Remove execute from directory
chmod 600 ~/permtest
cd ~/permtest
# Output: -bash: cd: /home/student/permtest: Permission denied

# Restore
chmod 700 ~/permtest
cd ~/permtest
ls
# Works now
cd ~
```

### Step 12: Clean Up
```bash
rm -f ~/perm_test.txt ~/private_test.txt
rm -rf ~/permtest
```

## ✅ Verification
```bash
# Read permissions correctly
stat --format="%a %n" /etc/passwd
# Output: 644 /etc/passwd

stat --format="%a %n" /usr/bin/sudo
# Output: 4755 /usr/bin/sudo  (4 = setuid)

# Decode manually:
# 644 = rw-r--r-- (user rw, group r, other r)
# 755 = rwxr-xr-x (user rwx, group rx, other rx)
```

## 📝 Summary
- The permission string has 10 characters: file type + user/group/other permissions
- `r=4, w=2, x=1` — add them to get the octal digit for each group
- Common permissions: 644 for files, 755 for directories and scripts, 600 for private files
- `stat` shows the numeric (octal) permission value
- Special bits: setuid (4xxx), setgid (2xxx), sticky (1xxx) add advanced control
