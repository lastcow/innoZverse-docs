# Lab 3: Directory Navigation

## 🎯 Objective
Master moving around the Linux filesystem with `cd`, creating directories with `mkdir`, removing them with `rmdir`, and visualizing structure with `tree`.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1 and 2
- Familiarity with the terminal prompt

## 🔬 Lab Instructions

### Step 1: Print and Understand Your Current Directory
```bash
pwd
# Output: /home/student
```

### Step 2: Navigate with `cd`
```bash
# Go to /etc
cd /etc
pwd
# Output: /etc

# Go back to home directory
cd ~
pwd
# Output: /home/student

# Go back to previous directory
cd -
# Output: /etc  (prints the directory you came from)
```

### Step 3: Use Relative vs Absolute Paths
```bash
# Absolute path: starts with /
cd /usr/local/bin

# Relative path: starts from current directory
cd /usr
cd local/bin
pwd
# Output: /usr/local/bin

# Go up one level with ..
cd ..
pwd
# Output: /usr/local

# Go up two levels
cd ../..
pwd
# Output: /usr
```

### Step 4: Create a Directory with `mkdir`
```bash
# Go to home first
cd ~

# Create a single directory
mkdir myproject
ls -la | grep myproject

# Create nested directories in one command
mkdir -p myproject/src/utils
ls -R myproject
# Output:
# myproject:
# src
# myproject/src:
# utils
# myproject/src/utils:
```

### Step 5: Create Multiple Directories at Once
```bash
cd ~/myproject

# Create multiple dirs at once using brace expansion
mkdir -p docs tests config

ls
# Output: config  docs  src  tests
```

### Step 6: Navigate Into Nested Directories
```bash
cd ~/myproject/src/utils
pwd
# Output: /home/student/myproject/src/utils

# Jump back to home quickly
cd
pwd
# Output: /home/student
```

### Step 7: Install and Use `tree`
```bash
sudo apt install tree -y

# Show structure of myproject
tree ~/myproject
# Output:
# /home/student/myproject
# ├── config
# ├── docs
# ├── src
# │   └── utils
# └── tests
# 5 directories, 0 files

# Limit depth
tree ~/myproject -L 1
```

### Step 8: Remove Empty Directories with `rmdir`
```bash
# rmdir only works on EMPTY directories
rmdir ~/myproject/config
ls ~/myproject
# config is gone

# Trying to remove a non-empty directory fails
rmdir ~/myproject/src
# Output: rmdir: failed to remove 'src': Directory not empty
```

### Step 9: Remove Directories with Contents Using `rm -r`
```bash
# Remove src and everything inside
rm -r ~/myproject/src
tree ~/myproject
# Output:
# /home/student/myproject
# ├── docs
# └── tests
```

### Step 10: Use `ls` with Path Arguments
```bash
# You don't have to cd to see contents
ls /var/log
ls -la /etc/apt
```

### Step 11: Special Directory Shortcuts
```bash
# ~ is your home
echo ~
# Output: /home/student

# . is current directory
ls .

# .. is parent directory
ls ..

# / is root
ls /
```

### Step 12: Clean Up
```bash
# Remove the entire myproject directory
rm -r ~/myproject
ls ~
# myproject should be gone
```

## ✅ Verification
```bash
# Create, navigate, verify, clean up
mkdir -p /tmp/navtest/a/b/c
cd /tmp/navtest/a/b/c
pwd
# Output: /tmp/navtest/a/b/c

cd ../../..
pwd
# Output: /tmp/navtest

tree /tmp/navtest
# Should show the nested structure

rm -r /tmp/navtest
```

## 📝 Summary
- `cd <path>` navigates directories; `cd ~` goes home; `cd -` goes back; `cd ..` goes up
- Absolute paths start with `/`; relative paths start from your current location
- `mkdir -p` creates nested directories in one command
- `rmdir` removes only empty directories; `rm -r` removes directories and contents
- `tree` gives a visual view of directory structure
