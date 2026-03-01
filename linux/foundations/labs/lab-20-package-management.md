# Lab 20: Package Management (Read-Only)

## 🎯 Objective
Explore Ubuntu's package management using dpkg and apt-cache for read-only operations: listing installed packages and searching for software information.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 19: I/O Redirection Basics

## 🔬 Lab Instructions

### Step 1: List Installed Packages with dpkg -l 2>/dev/null | head -20 || true

```bash
dpkg -l | head -20
```

**Expected output:**
```
ii  adduser        3.118ubuntu5 all          add and remove users and groups
ii  apt            2.4.x        amd64        commandline package manager
...
```

```bash
dpkg -l | grep "^ii" | wc -l
echo "ii = installed correctly"
echo "rc = removed but config files remain"
```

### Step 2: Filter Installed Packages

```bash
dpkg -l | grep -i python | head -15
dpkg -l | grep -i "^ii.*bash"
dpkg -l | grep -iE "^ii.*(vim|nano|emacs)" | head -10
dpkg -l "lib*" | grep "^ii" | head -10
```

### Step 3: Check If a Package is Installed

```bash
dpkg -l bash
dpkg -l python3
dpkg -l vim
```

**Expected output for bash:**
```
ii  bash  5.1-6ubuntu1  amd64  GNU Bourne Again SHell
```

```bash
dpkg -l curl 2>/dev/null | grep "^ii" && echo "curl is installed" || echo "curl not installed"
dpkg -l wget 2>/dev/null | grep "^ii" && echo "wget is installed" || echo "wget not installed"
```

### Step 4: Show Package Details with dpkg -s and -L

```bash
dpkg -s bash | head -20
dpkg -L bash | head -15
```

**Expected output (dpkg -L):**
```
/.
/bin
/bin/bash
/usr/share/doc/bash
...
```

### Step 5: Find Which Package Owns a File

```bash
dpkg -S /bin/ls
```

**Expected output:**
```
coreutils: /usr/bin/ls
```

```bash
dpkg -S /usr/bin/bash
```

### Step 6: Search with apt-cache

```bash
apt-cache search python3 | head -10
apt-cache search "text editor" | head -10
apt-cache search "system monitor" | head -10
```

### Step 7: Show Package Information with apt-cache show

```bash
apt-cache show bash | head -20
apt-cache show python3 | grep -E "^(Package|Version|Description):" | head -10
```

### Step 8: Check Package Dependencies

```bash
apt-cache depends bash | head -15
apt-cache rdepends bash 2>/dev/null | head -15
apt-cache policy bash | head -10
```

## ✅ Verification

```bash
echo "=== Installed package count ==="
dpkg -l | grep "^ii" | wc -l

echo "=== Python packages installed ==="
dpkg -l | grep -i "^ii.*python3" | wc -l

echo "=== bash package info ==="
dpkg -s bash | grep -E "^(Package|Version|Status):"

echo "=== apt-cache search demo ==="
apt-cache search "text editor" | wc -l

echo "Lab 20 complete"
```

## 📝 Summary
- `dpkg -l` lists all installed packages; `grep "^ii"` filters installed ones
- `dpkg -l PACKAGE` checks if a specific package is installed
- `dpkg -s PACKAGE` shows detailed info about an installed package
- `dpkg -L PACKAGE` lists all files installed by a package
- `dpkg -S /path/to/file` shows which package owns a file
- `apt-cache search keyword` searches the package database without installing
- `apt-cache show PACKAGE` displays package details including dependencies
- All these commands are read-only — they never modify the system
