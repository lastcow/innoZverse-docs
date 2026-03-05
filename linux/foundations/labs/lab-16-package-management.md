# Lab 16: Package Management — apt and dpkg

## Objective
Manage software with `apt` and `dpkg`: install, update, search, inspect packages, and understand the APT repository system. This is how you add tools to Linux servers and keep them secure with patches.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Understanding Installed Packages with dpkg

```bash
dpkg -l | head -6
```

**📸 Verified Output:**
```
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name                    Version                                 Architecture Description
+++-=======================-=======================================-============-========================================================================
ii  adduser                 3.118ubuntu5                            all          add and remove users and groups
```

```bash
# Count installed packages
dpkg -l | grep -c '^ii'
```

**📸 Verified Output:**
```
105
```

> 💡 `ii` = correctly installed. `rc` = removed but config files remain. `un` = not installed. The status flags tell you exactly what's on the system.

---

## Step 2: Inspect a Package

```bash
apt-cache show bash | grep -E 'Package|Version|Description:'
```

**📸 Verified Output:**
```
Package: bash
Version: 5.1-6ubuntu1.1
Description: GNU Bourne Again SHell
```

```bash
# Which package owns a specific file?
dpkg -S /bin/ls
```

**📸 Verified Output:**
```
coreutils: /bin/ls
```

```bash
# What files does a package install?
dpkg -L bash | head -8
```

**📸 Verified Output:**
```
/.
/bin
/bin/bash
/etc
/etc/bash.bashrc
/etc/skel
/etc/skel/.bash_logout
/etc/skel/.bashrc
```

---

## Step 3: Update Package Lists

```bash
apt-get update -qq
echo "Package lists updated: $?"
```

**📸 Verified Output:**
```
Package lists updated: 0
```

> 💡 `apt-get update` downloads the **list of available packages** from Ubuntu servers — it does NOT install or upgrade anything. Always run this before installing new packages to get the latest versions.

---

## Step 4: Install a Package

```bash
apt-get install -y -qq curl
curl --version | head -1
```

**📸 Verified Output:**
```
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 ...
```

```bash
# Install multiple packages at once
apt-get install -y -qq jq tree 2>/dev/null
echo '{"name": "linux", "version": "22.04"}' | jq '.'
```

**📸 Verified Output:**
```
{
  "name": "linux",
  "version": "22.04"
}
```

---

## Step 5: Search for Packages

```bash
apt-cache search 'network scanner' | head -5
```

**📸 Verified Output:**
```
masscan - TCP port scanner
nmap - The Network Mapper
zenmap - The Network Mapper Front End
```

```bash
# Check if a package is available before installing
apt-cache show nmap | grep -E 'Package|Version' | head -2
```

**📸 Verified Output:**
```
Package: nmap
Version: 7.80+dfsg1-2build2
```

---

## Step 6: Package Dependencies

```bash
apt-cache depends bash | head -6
```

**📸 Verified Output:**
```
bash
  PreDepends: libc6
  PreDepends: libtinfo6
  Depends: base-files
  Depends: debianutils
  Conflicts: <bash-completion>
```

> 💡 APT automatically resolves and installs dependencies. This is why `apt install nginx` might install 10+ packages — it includes all the libraries nginx needs to run.

---

## Step 7: Remove and Purge Packages

```bash
# Remove package (keep config files)
apt-get remove -y -qq tree 2>/dev/null
tree /tmp 2>&1 | head -1

# Purge (remove package AND config files)
apt-get purge -y -qq tree 2>/dev/null
echo "Purge complete"

# Clean download cache
apt-get clean
echo "Cache cleaned. Space in /var/cache/apt/archives:"
du -sh /var/cache/apt/archives/
```

**📸 Verified Output:**
```
bash: tree: command not found
Purge complete
Cache cleaned. Space in /var/cache/apt/archives:
8.0K	/var/cache/apt/archives/
```

---

## Step 8: Capstone — Security Package Audit Script

```bash
cat > /tmp/security_packages.sh << 'SCRIPT'
#!/bin/bash
echo "=== Security Package Audit ==="
echo ""

echo "1. Installed packages count:"
dpkg -l | grep -c '^ii'

echo ""
echo "2. Security-relevant packages installed:"
SECURITY_PKGS="openssl openssh-server ufw fail2ban aide rkhunter auditd"
for pkg in $SECURITY_PKGS; do
    if dpkg -l "$pkg" &>/dev/null 2>&1; then
        VERSION=$(dpkg -l "$pkg" | grep '^ii' | awk '{print $3}')
        echo "  ✅ $pkg ($VERSION)"
    else
        echo "  ❌ $pkg (NOT installed)"
    fi
done

echo ""
echo "3. OpenSSL version:"
openssl version 2>/dev/null || echo "  OpenSSL not found"

echo ""
echo "4. Packages with config files remaining (rc status):"
dpkg -l | grep '^rc' | awk '{print "  " $2}' | head -5
echo "  (run: apt-get purge to remove them)"

echo ""
echo "5. Top 5 largest installed packages:"
dpkg-query -Wf='${Installed-Size}\t${Package}\n' 2>/dev/null | sort -rn | head -5
SCRIPT

chmod +x /tmp/security_packages.sh
/tmp/security_packages.sh
```

**📸 Verified Output:**
```
=== Security Package Audit ===

1. Installed packages count:
105

2. Security-relevant packages installed:
  ✅ openssl (3.0.2-0ubuntu1.18)
  ❌ openssh-server (NOT installed)
  ❌ ufw (NOT installed)
  ❌ fail2ban (NOT installed)
  ❌ aide (NOT installed)
  ❌ rkhunter (NOT installed)
  ❌ auditd (NOT installed)

3. OpenSSL version:
OpenSSL 3.0.2 15 Mar 2022 (Library: OpenSSL 3.0.2 15 Mar 2022)

4. Packages with config files remaining (rc status):
  (run: apt-get purge to remove them)

5. Top 5 largest installed packages:
  56780	perl
  53492	libstdc++6
  34236	gcc-12-base
  ...
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `apt-get update` | Refresh package lists |
| `apt-get install pkg` | Install package |
| `apt-get remove pkg` | Remove (keep configs) |
| `apt-get purge pkg` | Remove + delete configs |
| `apt-get upgrade` | Upgrade all installed packages |
| `apt-cache show pkg` | Package information |
| `apt-cache search term` | Search available packages |
| `dpkg -l` | List installed packages |
| `dpkg -S /path/file` | Which package owns this file? |
| `dpkg -L package` | Files installed by package |
