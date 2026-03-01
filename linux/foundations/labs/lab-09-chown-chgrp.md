# Lab 9: chown and chgrp — Changing Ownership

## 🎯 Objective
Learn to change file ownership with `chown` and group ownership with `chgrp`, and use the `id` command to understand user and group identities.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 7–8 (Permissions and chmod)
- sudo access on the system

## 🔬 Lab Instructions

### Step 1: Understand Your Identity with `id`
```bash
id
# Output: uid=1000(student) gid=1000(student) groups=1000(student),4(adm),27(sudo)
# uid = user ID
# gid = primary group ID
# groups = all groups you belong to

id -u    # Just your UID
id -g    # Just your primary GID
id -un   # Just your username
id -gn   # Just your primary group name
```

### Step 2: Check Ownership of Files
```bash
ls -l /etc/passwd
# Output: -rw-r--r-- 1 root root 2847 ... /etc/passwd
#                      ^^^^ ^^^^
#                      user group

ls -l /var/log/syslog
# Output: -rw-r----- 1 syslog adm ...
```

### Step 3: Create Test Files and Check Ownership
```bash
mkdir ~/lab09
cd ~/lab09
touch myfile.txt mydir
ls -l
# Owner and group should be your username
```

### Step 4: Change File Owner with `chown`
```bash
# Create a file as root to demonstrate chown
sudo touch /tmp/rootfile.txt
ls -l /tmp/rootfile.txt
# Output: -rw-r--r-- 1 root root 0 ...

# Change owner to current user
sudo chown $USER /tmp/rootfile.txt
ls -l /tmp/rootfile.txt
# Output: -rw-r--r-- 1 student root 0 ...
# Owner changed, group still root
```

### Step 5: Change Owner and Group Together
```bash
# chown user:group syntax
sudo chown $USER:$USER /tmp/rootfile.txt
ls -l /tmp/rootfile.txt
# Output: -rw-r--r-- 1 student student 0 ...
```

### Step 6: Change Only the Group with `chown`
```bash
# Use :group syntax (no username before colon changes just the group)
sudo chown :root /tmp/rootfile.txt
ls -l /tmp/rootfile.txt
# Output: -rw-r--r-- 1 student root 0 ...
# Owner is still student, group changed to root
```

### Step 7: Use `chgrp` to Change Group
```bash
# chgrp is dedicated to changing group ownership
sudo chgrp $USER /tmp/rootfile.txt
ls -l /tmp/rootfile.txt
# Output: -rw-r--r-- 1 student student 0 ...
```

### Step 8: Recursive Ownership Change with `-R`
```bash
mkdir -p ~/lab09/project/{src,docs}
touch ~/lab09/project/src/main.py ~/lab09/project/docs/readme.md

# Change ownership recursively
sudo chown -R $USER:$USER ~/lab09/project/
ls -lR ~/lab09/project/
# All files should show your user:group
```

### Step 9: Change to a Different Group You Belong To
```bash
# View groups you're in
groups
# Output: student adm sudo

# Create a file and change its group
touch ~/lab09/shared.txt
chgrp adm ~/lab09/shared.txt
ls -l ~/lab09/shared.txt
# Output: -rw-rw-r-- 1 student adm ...

# Note: you can only chgrp to groups you're already a member of
# (unless you're root)
```

### Step 10: Understand Why Ownership Matters
```bash
# Create a file owned by root
sudo bash -c 'echo "root content" > /tmp/rootowned.txt'
sudo chmod 640 /tmp/rootowned.txt
ls -l /tmp/rootowned.txt
# Output: -rw-r----- 1 root root ...

# Try to read as non-root (group has r, other has nothing)
cat /tmp/rootowned.txt
# Output: cat: /tmp/rootowned.txt: Permission denied
# (if you're not in root's group)

# Root always wins
sudo cat /tmp/rootowned.txt
# Output: root content
```

### Step 11: Use `stat` to View Ownership Details
```bash
stat ~/lab09/myfile.txt
# Output includes:
# File: /home/student/lab09/myfile.txt
# Access: (0644/-rw-rw-r--)  Uid: (1000/student)   Gid: (1000/student)

# Quick format
stat --format="User: %U  Group: %G  Perms: %a" ~/lab09/myfile.txt
```

### Step 12: Real-World Example — Web Server Files
```bash
# Web servers typically need specific ownership
# Example: nginx files should be owned by www-data

# Check if www-data user exists
id www-data 2>/dev/null || echo "www-data user not found"

# In a real web server scenario:
sudo mkdir -p /var/www/mysite
sudo chown -R www-data:www-data /var/www/mysite
sudo chmod -R 755 /var/www/mysite
ls -ld /var/www/mysite

# Clean up
sudo rm -rf /var/www/mysite
rm -rf ~/lab09
rm -f /tmp/rootfile.txt /tmp/rootowned.txt
```

## ✅ Verification
```bash
# Verify ownership change works
sudo touch /tmp/ownertest.txt
sudo chown $USER:$USER /tmp/ownertest.txt
stat --format="User: %U  Group: %G" /tmp/ownertest.txt
# Output: User: student  Group: student

rm /tmp/ownertest.txt
```

## 📝 Summary
- `id` shows your UID, GID, and group memberships — crucial for troubleshooting permissions
- `chown user file` changes the owner; `chown user:group file` changes both at once
- `chgrp group file` changes only the group
- `-R` flag makes `chown` and `chgrp` work recursively on directories
- Only root can give files to another user; regular users can only change groups to ones they belong to
