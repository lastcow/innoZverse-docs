# Lab 10: Users and Groups

## 🎯 Objective
Understand Linux user and group management: check identity with `whoami` and `id`, read `/etc/passwd` and `/etc/group`, and manage users with `adduser` and `groups`.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Labs 7–9 (Permissions and Ownership)
- sudo access

## 🔬 Lab Instructions

### Step 1: Identify Your Current User
```bash
whoami
# Output: student

who
# Output: student  pts/0  2026-03-01 05:42 (:0)
# Shows all logged-in users

w
# More detailed: shows what each user is running
```

### Step 2: Get Detailed Identity Info
```bash
id
# Output: uid=1000(student) gid=1000(student) groups=1000(student),4(adm),27(sudo)

id -u    # UID number only
id -g    # Primary GID only
id -G    # All GIDs
id -un   # Username only
```

### Step 3: Read `/etc/passwd`
Each line in `/etc/passwd` describes one user account:
```bash
cat /etc/passwd | head -5
# Output format:
# username:password:UID:GID:GECOS:home:shell
# root:x:0:0:root:/root:/bin/bash
# daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin

# Look at your own entry
grep "^$USER:" /etc/passwd
# Output: student:x:1000:1000:student,,,:/home/student:/bin/bash

# Fields:
# student  = username
# x        = password placeholder (actual hash in /etc/shadow)
# 1000     = UID
# 1000     = GID
# student,,, = GECOS (full name, room, etc.)
# /home/student = home directory
# /bin/bash     = login shell
```

### Step 4: View System Users vs Regular Users
```bash
# UIDs 0-999: system/service accounts
# UIDs 1000+: regular human users

awk -F: '$3 >= 1000 && $3 < 65534 {print $1, $3}' /etc/passwd
# Output: student 1000

# System users (no login shell)
awk -F: '$7 ~ /nologin|false/ {print $1, $3}' /etc/passwd | head -10
```

### Step 5: Read `/etc/group`
```bash
cat /etc/group | head -10
# Format: groupname:password:GID:members
# root:x:0:
# sudo:x:27:student

# See groups you're in
grep $USER /etc/group
# Shows all lines where your username appears
```

### Step 6: List Your Group Memberships
```bash
groups
# Output: student adm sudo

groups root
# Output: root : root

# Number of groups
id -Gn | tr ' ' '\n' | wc -l
```

### Step 7: Create a New User with `adduser`
```bash
# adduser is the friendly interactive command (Ubuntu)
sudo adduser testuser
# Prompts for:
# - Password (enter twice)
# - Full name (optional, press Enter to skip)
# - Room number, phone (optional)

# Verify creation
grep testuser /etc/passwd
# Output: testuser:x:1001:1001:,,,:/home/testuser:/bin/bash

ls /home/
# Output: student  testuser
```

### Step 8: Create a User Without Home Directory
```bash
sudo useradd --no-create-home --shell /usr/sbin/nologin serviceaccount
grep serviceaccount /etc/passwd
# Output: serviceaccount:x:1002:1002::/home/serviceaccount:/usr/sbin/nologin
```

### Step 9: Add a User to a Group
```bash
# Add testuser to the sudo group
sudo usermod -aG sudo testuser
# -a = append (don't remove from other groups)
# -G = supplementary groups

# Verify
groups testuser
# Output: testuser : testuser sudo

id testuser
# Shows updated group membership
```

### Step 10: Switch to Another User with `su`
```bash
# Switch to testuser
su - testuser
# Enter testuser's password

# Now you're testuser
whoami
# Output: testuser

id
# Shows testuser's identity

# Return to your original user
exit
whoami
# Output: student
```

### Step 11: Create a Group and Add Users
```bash
# Create a new group
sudo groupadd developers

# Add users to it
sudo usermod -aG developers testuser
sudo usermod -aG developers $USER

# Verify
grep developers /etc/group
# Output: developers:x:1003:testuser,student
```

### Step 12: Remove a User
```bash
# Remove the test user and their home directory
sudo deluser --remove-home testuser
sudo deluser serviceaccount

# Verify
grep testuser /etc/passwd
# Output: (nothing)
ls /home/
# Output: student (testuser dir is gone)

# Remove the group
sudo groupdel developers
```

## ✅ Verification
```bash
# Confirm your user info is complete
echo "Username: $(whoami)"
echo "UID: $(id -u)"
echo "Primary Group: $(id -gn)"
echo "All Groups: $(groups)"

grep "^$(whoami):" /etc/passwd
# Should show your user's entry

grep "^$(id -gn):" /etc/group
# Should show your primary group's entry
```

## 📝 Summary
- `whoami` shows current username; `id` shows UID, GID, and all group memberships
- `/etc/passwd` stores user account info (not passwords — those are in `/etc/shadow`)
- `/etc/group` stores group definitions and memberships
- `adduser` (Ubuntu) is the friendly way to create users interactively
- `usermod -aG group user` adds a user to a group without removing them from others
- Regular users have UIDs ≥ 1000; UIDs 0–999 are reserved for system accounts
