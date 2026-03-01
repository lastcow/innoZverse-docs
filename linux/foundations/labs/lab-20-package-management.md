# Lab 20: Package Management with apt

## 🎯 Objective
Learn to manage software packages on Ubuntu using `apt`: update package lists, install and remove software, and inspect installed packages with `dpkg`.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- sudo access on the system
- Internet connectivity

## 🔬 Lab Instructions

### Step 1: Understand the Package System
Ubuntu uses the APT (Advanced Package Tool) system to manage `.deb` packages.

```bash
# apt: high-level, user-friendly tool
# dpkg: low-level package management
# /etc/apt/sources.list: where packages come from

cat /etc/apt/sources.list
# Shows configured repositories
```

### Step 2: Update Package Lists
Before installing, always update the package index:

```bash
sudo apt update
# Output: Hit/Get lines (downloading package metadata)
# Output: All packages are up to date.

# This does NOT install anything — it just refreshes the index
```

### Step 3: Check for Upgradeable Packages
```bash
apt list --upgradable
# Shows packages with newer versions available

# Count upgradeable packages
apt list --upgradable 2>/dev/null | wc -l
```

### Step 4: Upgrade Installed Packages
```bash
# Upgrade all packages
sudo apt upgrade -y
# -y auto-answers "yes" to prompts

# Full upgrade (may remove conflicting packages)
sudo apt full-upgrade -y
```

### Step 5: Search for Packages
```bash
# Search by name or description
apt search tree
# Shows packages matching "tree"

apt search "text editor" | head -20

# Get info about a specific package before installing
apt show nano
# Shows description, version, dependencies, size
```

### Step 6: Install a Package
```bash
# Install tree
sudo apt install tree -y
# Output: Reading package lists, Building dependency tree...
# Shows what will be installed and disk usage
# Installs automatically due to -y

tree --version
# Verify installation
```

### Step 7: Install Multiple Packages at Once
```bash
sudo apt install htop curl wget -y
# All three installed in one command

# Verify
which htop curl wget
# Output: /usr/bin/htop  /usr/bin/curl  /usr/bin/wget
```

### Step 8: Remove a Package
```bash
# Remove the package but keep config files
sudo apt remove tree -y
# tree is removed, but any config it left behind stays

which tree
# Output: (not found)

# Remove package AND its configuration files
sudo apt purge tree -y
```

### Step 9: Autoremove Unused Dependencies
```bash
# After removing packages, orphaned dependencies may remain
sudo apt autoremove -y
# Removes packages no longer needed by anything

# Combine with purge
sudo apt autoremove --purge -y
```

### Step 10: List Installed Packages with `dpkg`
```bash
# List all installed packages
dpkg -l
# Output: columns: desired, status, name, version, architecture, description
# ii = installed OK

# List installed packages with a filter
dpkg -l | grep "^ii" | grep "python"

# Count installed packages
dpkg -l | grep "^ii" | wc -l
```

### Step 11: Find Which Package Provides a File
```bash
# What package does /usr/bin/ls belong to?
dpkg -S /usr/bin/ls
# Output: coreutils: /usr/bin/ls

dpkg -S /etc/hosts
# Output: base-files: /etc/hosts

# List all files installed by a package
dpkg -L coreutils | head -20
```

### Step 12: Clean Package Cache
```bash
# APT keeps downloaded .deb files in cache
du -sh /var/cache/apt/archives/

# Remove cached files for packages that are no longer installed
sudo apt clean
# Removes ALL cached .deb files

du -sh /var/cache/apt/archives/
# Should be smaller now

# List package actions history
cat /var/log/apt/history.log | tail -30
```

## ✅ Verification
```bash
# Verify apt workflow
sudo apt update
apt show curl 2>/dev/null | grep -E "Package|Version|Installed-Size"

dpkg -l curl 2>/dev/null | grep "^ii"
# If curl is installed, shows its entry

dpkg -S /usr/bin/curl 2>/dev/null
# Output: curl: /usr/bin/curl
```

## 📝 Summary
- `apt update` refreshes the package index — always run this before installing
- `apt install package` installs software; `apt remove package` removes it; `apt purge` removes with config
- `apt upgrade` updates installed packages to their latest versions
- `apt search keyword` finds packages; `apt show package` gives detailed info
- `dpkg -l` lists installed packages; `dpkg -S /path` finds which package owns a file
- `apt autoremove` cleans up orphaned dependencies; `apt clean` removes cached package files
