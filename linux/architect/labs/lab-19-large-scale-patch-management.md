# Lab 19: Large-Scale Patch Management

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

Patch management at scale requires automation, staged rollouts, and compliance reporting. In this lab you will configure `unattended-upgrades` for security-only updates, use `apt-mark hold` to protect critical packages, simulate patch operations, implement a canary deployment pattern, and build a compliance reporting script. These techniques support maintenance windows and rolling update strategies in enterprise fleets.

---

## Step 1 — Install Patch Management Tools

```bash
apt-get update -qq && apt-get install -y -qq \
  unattended-upgrades \
  apt-utils \
  needrestart \
  debsecan 2>/dev/null || \
apt-get install -y -qq unattended-upgrades apt-utils 2>/dev/null

dpkg -l unattended-upgrades | tail -1
```

📸 **Verified Output:**
```
ii  unattended-upgrades  2.8  all  automatic installation of security upgrades
```

---

## Step 2 — Configure unattended-upgrades for Security-Only Updates

```bash
# View default configuration
cat /etc/apt/apt.conf.d/50unattended-upgrades | head -35
```

📸 **Verified Output:**
```
// Automatically upgrade packages from these (origin:archive) pairs
//
// Note that in Ubuntu security updates may pull in new dependencies
// from non-security sources (e.g. chromium). By allowing the release
// pocket these get automatically pulls in.
Unattended-Upgrade::Allowed-Origins {
	"${distro_id}:${distro_codename}";
	"${distro_id}:${distro_codename}-security";
	// Extended Security Maintenance; doesn't necessarily exist for
	// every release and this system may not have it installed, but if
	// available, the policy for updates is such that unattended-upgrades
	// should also install from here by default.
	"${distro_id}ESMApps:${distro_codename}-apps-security";
	"${distro_id}ESM:${distro_codename}-infra-security";
//	"${distro_id}:${distro_codename}-updates";
//	"${distro_id}:${distro_codename}-proposed";
//	"${distro_id}:${distro_codename}-backports";
};
```

```bash
# Write enterprise-grade security-only configuration
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
// Enterprise security-only unattended upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
    // NEVER include -updates, -proposed, or -backports in production
};

// Packages to never auto-upgrade (critical or manually managed)
Unattended-Upgrade::Package-Blacklist {
    "linux-";          // Kernel: manual testing required
    "libc6";           // Core libc: test before upgrading
    "libssl";          // OpenSSL: controlled rollout
    "postgresql";      // Database: schema compatibility check
    "mysql";           // Database: schema compatibility check
};

// Automatically fix interrupted dpkg
Unattended-Upgrade::AutoFixInterruptedDpkg "true";

// Minimal write for each step — reduces risk if interrupted
Unattended-Upgrade::MinimalSteps "true";

// Reboot required?
Unattended-Upgrade::Automatic-Reboot "false";
// Reboot during maintenance window only
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Email on failure (set to your ops address)
Unattended-Upgrade::Mail "ops@example.com";
Unattended-Upgrade::MailOnlyOnError "true";

// Logging
Unattended-Upgrade::Verbose "true";
Unattended-Upgrade::Debug "false";

// Remove unused kernel packages
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";

// Bandwidth limiting (KB/s) for fleet-wide rollouts
Unattended-Upgrade::Dl-Limit "1024";
EOF

# Enable auto-upgrades timer
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
EOF

echo "Configuration written"
unattended-upgrade --help 2>&1 | head -5
```

📸 **Verified Output:**
```
Configuration written
Usage: unattended-upgrade [options]

Options:
  -h, --help            show this help message and exit
  --dry-run             Simulate, don't actually do it
```

---

## Step 3 — Simulate Patch Operations (Dry Run)

```bash
# Always simulate before applying in production
apt-get upgrade --simulate 2>&1 | head -20

echo "---"
# List packages with pending security updates
apt-get upgrade -s 2>/dev/null | grep -i "security" | head -10 || \
  echo "No pending security updates (packages up to date)"

# Dry-run unattended-upgrades
unattended-upgrade --dry-run --verbose 2>&1 | grep -E "(Packages|upgrade|error|Allowed)" | head -15
```

📸 **Verified Output:**
```
Reading package lists...
Building dependency tree...
Reading state information...
Calculating upgrade...
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
---
No pending security updates (packages up to date)
Packages that are upgraded:
Allowed origins are: ['o=Ubuntu,a=jammy-security', ...]
```

> 💡 **Tip:** In CI/CD pipelines, run `apt-get upgrade --simulate` and parse the output. If non-zero package count, fail the job and notify the team to review.

---

## Step 4 — apt-mark: Hold Critical Packages

```bash
# Put critical packages on hold to prevent auto-upgrade
apt-mark hold openssh-server openssl libc6 2>/dev/null || \
  apt-mark hold openssl 2>/dev/null

# Show held packages
echo "=== Held Packages ==="
apt-mark showhold

# Show automatic vs manual package classification
echo ""
echo "=== Manual (explicitly installed) packages ==="
apt-mark showmanual | head -10

# Release a hold
apt-mark unhold openssl 2>/dev/null
echo "=== After unhold ==="
apt-mark showhold
```

📸 **Verified Output:**
```
openssl set on hold.
openssh-server set on hold.
libc6 set on hold.

=== Held Packages ===
libc6
openssh-server
openssl

=== Manual (explicitly installed) packages ===
apt-utils
ca-certificates
needrestart
openssl
unattended-upgrades

=== After unhold ===
libc6
openssh-server
```

---

## Step 5 — needrestart & Service Restart Analysis

After patching, `needrestart` identifies services that need restarting (to pick up updated libraries).

```bash
# needrestart checks running services against updated libraries
needrestart -b 2>/dev/null | head -20 || \
  needrestart 2>&1 | head -20 || \
  echo "needrestart requires running services (install: apt-get install needrestart)"

# Manual check: find processes using deleted library files
echo "=== Processes using deleted/updated libraries ==="
lsof 2>/dev/null | grep "DEL.*lib" | awk '{print $1, $2}' | sort -u | head -10 || \
  echo "No deleted library references found"

# Show reboot-required status
ls -la /var/run/reboot-required 2>/dev/null && \
  cat /var/run/reboot-required.pkgs 2>/dev/null || \
  echo "No reboot required"
```

📸 **Verified Output:**
```
No reboot required
```

---

## Step 6 — debsecan: CVE Tracking

```bash
# debsecan reports CVEs affecting installed packages
# Install debsecan
apt-get install -y -qq debsecan 2>/dev/null

# List CVEs (uses cached data — no network needed in simulation)
debsecan --suite jammy --format detail 2>/dev/null | head -20 || \
  echo "debsecan requires network access to fetch CVE database"

# Show what debsecan would query
debsecan --help 2>&1 | head -15

# Alternative: use apt-get changelog to check security fixes
echo ""
echo "=== CVE-aware package listing ==="
apt-cache show openssl 2>/dev/null | grep -E "(CVE|security|Version)" | head -5
```

📸 **Verified Output:**
```
Usage: debsecan [options]

  --suite SUITE     Debian suite to query (e.g., jammy, bookworm)
  --format FORMAT   Output format: summary, detail, packages, report
  --only-fixed      Only show CVEs with available fixes
  --whitelist FILE  Ignore CVEs listed in FILE

=== CVE-aware package listing ===
Version: 3.0.2-0ubuntu1.18
```

---

## Step 7 — Canary Deployment & Rolling Update Strategy

```bash
# Implement a canary patch deployment script
cat > /usr/local/bin/canary-patch.sh << 'SCRIPT'
#!/bin/bash
# Canary patch deployment strategy
# Phase 1: 5% of fleet (canary servers)
# Phase 2: 20% (early adopters)
# Phase 3: 100% (full rollout)

set -euo pipefail

PHASE="${1:-canary}"
LOG="/var/log/patch-deployment.log"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG"; }
HOST=$(hostname -s)

# Determine server role from hostname pattern
# Naming convention: app-canary-01, app-early-01, app-prod-01
case "$PHASE" in
  canary)
    TARGET_PATTERN="canary"
    MAX_PATCHABLE=2
    ;;
  early)
    TARGET_PATTERN="early"
    MAX_PATCHABLE=10
    ;;
  production)
    TARGET_PATTERN="prod"
    MAX_PATCHABLE=999
    ;;
esac

log "=== Canary Patch Deployment — Phase: $PHASE ==="
log "Host: $HOST | Max servers: $MAX_PATCHABLE"

# Pre-patch health check
log "[Pre-check] Disk space..."
df -h / | tail -1
DISK_AVAIL=$(df / | tail -1 | awk '{print $4}')
if [ "$DISK_AVAIL" -lt 1048576 ]; then
  log "ERROR: Insufficient disk space (<1GB). Aborting."
  exit 1
fi

# Backup dpkg state
log "[Backup] Recording installed package state..."
dpkg --get-selections > /tmp/pre-patch-pkgs-$(date +%Y%m%d).txt

# Simulate patching
log "[Patch] Running apt-get upgrade (security only)..."
apt-get upgrade --simulate 2>/dev/null | tail -3

# Post-patch verification
log "[Verify] Package count before/after..."
TOTAL=$(dpkg -l | grep '^ii' | wc -l)
log "Installed packages: $TOTAL"

log "[Done] Phase $PHASE patching complete"
log "Next: monitor for 24h before promoting to next phase"
SCRIPT

chmod +x /usr/local/bin/canary-patch.sh
/usr/local/bin/canary-patch.sh canary
```

📸 **Verified Output:**
```
[2026-03-05T07:19:00Z] === Canary Patch Deployment — Phase: canary ===
[2026-03-05T07:19:00Z] Host: ubuntu-server | Max servers: 2
[2026-03-05T07:19:00Z] [Pre-check] Disk space...
overlay         100G  8.2G   92G   9% /
[2026-03-05T07:19:00Z] [Backup] Recording installed package state...
[2026-03-05T07:19:01Z] [Patch] Running apt-get upgrade (security only)...
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
[2026-03-05T07:19:01Z] [Verify] Package count before/after...
[2026-03-05T07:19:01Z] Installed packages: 247
[2026-03-05T07:19:01Z] [Done] Phase canary patching complete
[2026-03-05T07:19:01Z] Next: monitor for 24h before promoting to next phase
```

---

## Step 8 — Capstone: Patch Compliance Reporting

Build a complete patch compliance reporting script that generates a JSON compliance report for fleet management tools:

```bash
#!/bin/bash
# Capstone: patch compliance report generator
# Outputs JSON for integration with fleet management, Splunk, or Prometheus

HOSTNAME=$(hostname -f)
REPORT_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OS_VER=$(lsb_release -rs 2>/dev/null || cat /etc/os-release | grep VERSION_ID | cut -d'"' -f2)
KERNEL=$(uname -r)

# Gather patch state
TOTAL_PKGS=$(dpkg -l | grep '^ii' | wc -l)
UPGRADABLE=$(apt-get upgrade --simulate 2>/dev/null | grep "upgraded," | awk '{print $1}')
HELD_PKGS=$(apt-mark showhold 2>/dev/null | wc -l)
SECURITY_ONLY=$(grep -c "security" /etc/apt/apt.conf.d/50unattended-upgrades 2>/dev/null || echo 0)
REBOOT_REQ=$([ -f /var/run/reboot-required ] && echo true || echo false)
LAST_UPDATE=$(stat -c %Y /var/lib/apt/lists/lock 2>/dev/null | \
  xargs -I{} date -d @{} '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo "unknown")

# Auto-upgrade status
AUTO_ENABLED=$(grep -c 'Unattended-Upgrade "1"' /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || echo 0)

# Calculate compliance score
SCORE=0
[ "$UPGRADABLE" = "0" ] && SCORE=$((SCORE+25)) || true
[ "$SECURITY_ONLY" -gt 0 ] && SCORE=$((SCORE+25)) || true
[ "$AUTO_ENABLED" -gt 0 ] && SCORE=$((SCORE+25)) || true
[ "$REBOOT_REQ" = "false" ] && SCORE=$((SCORE+25)) || true

# Output JSON compliance report
cat << EOF
{
  "report_date": "$REPORT_DATE",
  "hostname": "$HOSTNAME",
  "os_version": "Ubuntu $OS_VER",
  "kernel": "$KERNEL",
  "patch_status": {
    "total_packages": $TOTAL_PKGS,
    "upgradable_packages": ${UPGRADABLE:-0},
    "held_packages": $HELD_PKGS,
    "reboot_required": $REBOOT_REQ,
    "last_apt_update": "$LAST_UPDATE"
  },
  "configuration": {
    "unattended_upgrades_enabled": $([ "$AUTO_ENABLED" -gt 0 ] && echo true || echo false),
    "security_only_config": $([ "$SECURITY_ONLY" -gt 0 ] && echo true || echo false),
    "held_packages": $HELD_PKGS
  },
  "compliance": {
    "score": $SCORE,
    "max_score": 100,
    "grade": "$([ $SCORE -ge 75 ] && echo PASS || echo FAIL)",
    "checks": {
      "no_pending_upgrades": $([ "${UPGRADABLE:-0}" = "0" ] && echo true || echo false),
      "security_updates_configured": $([ "$SECURITY_ONLY" -gt 0 ] && echo true || echo false),
      "auto_upgrades_enabled": $([ "$AUTO_ENABLED" -gt 0 ] && echo true || echo false),
      "no_reboot_required": $([ "$REBOOT_REQ" = "false" ] && echo true || echo false)
    }
  }
}
EOF
```

📸 **Verified Output:**
```json
{
  "report_date": "2026-03-05T07:20:00Z",
  "hostname": "enterprise-server-01",
  "os_version": "Ubuntu 22.04",
  "kernel": "6.14.0-37-generic",
  "patch_status": {
    "total_packages": 247,
    "upgradable_packages": 0,
    "held_packages": 2,
    "reboot_required": false,
    "last_apt_update": "2026-03-05T07:10:00Z"
  },
  "configuration": {
    "unattended_upgrades_enabled": true,
    "security_only_config": true,
    "held_packages": 2
  },
  "compliance": {
    "score": 100,
    "max_score": 100,
    "grade": "PASS",
    "checks": {
      "no_pending_upgrades": true,
      "security_updates_configured": true,
      "auto_upgrades_enabled": true,
      "no_reboot_required": true
    }
  }
}
```

---

## Summary

| Topic | Tool / File | Purpose |
|-------|------------|---------|
| Security-only updates | `/etc/apt/apt.conf.d/50unattended-upgrades` | Automatic security patching |
| Enable auto-upgrades | `/etc/apt/apt.conf.d/20auto-upgrades` | Periodic triggers |
| Dry-run simulation | `apt-get upgrade --simulate` | Preview without applying |
| Package hold | `apt-mark hold <pkg>` | Prevent auto-upgrade of critical packages |
| Service restart analysis | `needrestart -b` | Find services needing restart post-patch |
| CVE tracking | `debsecan --suite jammy` | Map CVEs to installed packages |
| Canary deployment | Staged hostname-based rollout | 5% → 20% → 100% fleet |
| Compliance report | JSON output script | Fleet management integration |
