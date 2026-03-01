# Lab 10: Users and Groups

## 🎯 Objective
Understand Linux user and group management by examining /etc/passwd and /etc/group, using id, whoami, and groups commands.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 9: chown and chgrp

## 🔬 Lab Instructions

### Step 1: Identify Yourself

```bash
whoami
id
id -u
id -g
id -un
id -gn
```

### Step 2: Explore Your Group Memberships

```bash
groups
id -G
id -Gn
```

### Step 3: Understand /etc/passwd Structure

```bash
# /etc/passwd: username:password:UID:GID:GECOS:home:shell
grep "^$(whoami):" /etc/passwd
```

**Expected output:**
```
zchen:x:1000:1000::/home/zchen:/bin/bash
```

```bash
head -5 /etc/passwd
wc -l /etc/passwd
awk -F: '$3 < 1000 {print $1, $3}' /etc/passwd | head -10
awk -F: '$3 >= 1000 {print $1, $3, $7}' /etc/passwd
```

### Step 4: Understand /etc/group Structure

```bash
# /etc/group: groupname:password:GID:members
head -10 /etc/group
grep "$(whoami)" /etc/group
grep "^sudo:" /etc/group
wc -l /etc/group
```

### Step 5: Look Up Other Users

```bash
grep "^root:" /etc/passwd
awk -F: '{print $1 "	" $6 "	" $7}' /etc/passwd | head -10
grep "/bin/bash$" /etc/passwd
grep -E "/(nologin|false)$" /etc/passwd | head -10
```

### Step 6: Check Login and Session Info

```bash
who
echo "USER: $USER"
echo "HOME: $HOME"
echo "SHELL: $SHELL"
grep "^$(whoami):" /etc/passwd | cut -d: -f6
```

## ✅ Verification

```bash
echo "=== User Identity Check ==="
echo "Username: $(whoami)"
echo "UID: $(id -u)"
echo "GID: $(id -g)"
echo "Groups: $(groups)"
echo ""
echo "=== /etc/passwd entry ==="
grep "^$(whoami):" /etc/passwd
echo ""
echo "=== Group memberships from /etc/group ==="
grep "$(whoami)" /etc/group | cut -d: -f1
echo "Lab 10 complete"
```

## 📝 Summary
- `whoami` shows your username; `id` shows full identity with all group IDs
- `groups` lists all groups you belong to by name
- `/etc/passwd` has 7 fields: username, x, UID, GID, comment, home, shell
- `/etc/group` has 4 fields: name, x, GID, member list
- UIDs below 1000 are typically system accounts; 1000+ are regular users
- `awk -F:` is the standard tool for parsing colon-separated files
