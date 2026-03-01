# Lab 9: Changing Ownership with chown and chgrp

## 🎯 Objective
Use chown and chgrp to change file ownership, understand user and group concepts, and use id and groups commands.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 8: chmod

## 🔬 Lab Instructions

### Step 1: Check Your Identity

```bash
whoami
id
```

**Expected output:**
```
uid=1000(zchen) gid=1000(zchen) groups=1000(zchen),4(adm),27(sudo),...
```

```bash
groups
```

### Step 2: View Current Ownership

```bash
mkdir -p /tmp/own-lab
touch /tmp/own-lab/file1.txt /tmp/own-lab/file2.txt
ls -l /tmp/own-lab
stat /tmp/own-lab/file1.txt
```

**Expected output (stat includes):**
```
Uid: ( 1000/   zchen)   Gid: ( 1000/   zchen)
```

### Step 3: Change Group Ownership with chgrp

```bash
MY_GROUP=$(id -gn)
echo "Your primary group is: $MY_GROUP"
chgrp $MY_GROUP /tmp/own-lab/file1.txt
ls -l /tmp/own-lab/file1.txt
```

```bash
MY_GID=$(id -g)
chgrp $MY_GID /tmp/own-lab/file2.txt
ls -l /tmp/own-lab/file2.txt
```

### Step 4: Change Ownership with chown

```bash
MY_USER=$(whoami)
chown $MY_USER /tmp/own-lab/file1.txt
ls -l /tmp/own-lab/file1.txt
```

```bash
MY_USER=$(whoami)
MY_GROUP=$(id -gn)
chown ${MY_USER}:${MY_GROUP} /tmp/own-lab/file2.txt
ls -l /tmp/own-lab/file2.txt
```

```bash
# Change only the group using chown :group syntax
chown :$(id -gn) /tmp/own-lab/file1.txt
ls -l /tmp/own-lab/file1.txt
```

### Step 5: Recursive Ownership Change

```bash
mkdir -p /tmp/own-lab/project/src
touch /tmp/own-lab/project/src/app.py
touch /tmp/own-lab/project/README.md

MY_USER=$(whoami)
MY_GROUP=$(id -gn)
chown -R ${MY_USER}:${MY_GROUP} /tmp/own-lab/project
ls -lR /tmp/own-lab/project
```

### Step 6: Understand /etc/passwd and /etc/group

```bash
# /etc/passwd: username:x:UID:GID:GECOS:home:shell
grep "^$(whoami):" /etc/passwd
```

**Expected output:**
```
zchen:x:1000:1000::/home/zchen:/bin/bash
```

```bash
grep "^$(id -gn):" /etc/group
grep $(whoami) /etc/group
```

### Step 7: stat to Verify Ownership

```bash
stat -c "File: %n | Owner: %U (%u) | Group: %G (%g)" /tmp/own-lab/file1.txt
```

**Expected output:**
```
File: /tmp/own-lab/file1.txt | Owner: zchen (1000) | Group: zchen (1000)
```

## ✅ Verification

```bash
echo "User: $(whoami), UID: $(id -u), GID: $(id -g)"
echo "Groups: $(groups)"
touch /tmp/own-verify.txt
stat -c "Owner: %U | Group: %G" /tmp/own-verify.txt
rm /tmp/own-verify.txt
rm -rf /tmp/own-lab
echo "Lab 9 complete"
```

## 📝 Summary
- `whoami` shows your username; `id` shows UID, GID, and all group memberships
- `groups` lists all groups you belong to
- `chgrp groupname file` changes the group owner
- `chown username file` changes the user owner
- `chown user:group file` changes both simultaneously
- `chown -R` applies ownership changes recursively
- `/etc/passwd` stores user accounts; `/etc/group` stores group memberships
