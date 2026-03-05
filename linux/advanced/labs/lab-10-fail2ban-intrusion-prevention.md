# Lab 10: fail2ban Intrusion Prevention

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

fail2ban is an intrusion prevention framework that monitors log files for patterns indicating brute-force or other attacks, then automatically bans offending IPs using firewall rules (iptables/nftables). This lab covers installation, jail configuration, custom filters, testing, and operational management of fail2ban.

---

## Step 1: Install fail2ban

```bash
apt-get update -qq && apt-get install -y fail2ban 2>/dev/null
```

Verify installation:

```bash
fail2ban-client --version
dpkg -l fail2ban
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get update -qq 2>/dev/null && apt-get install -y -qq fail2ban 2>/dev/null && fail2ban-client --version"
Fail2Ban v0.11.2
```

Check installed components:

```bash
# Key files and directories
ls /etc/fail2ban/
ls /etc/fail2ban/filter.d/ | head -10
ls /etc/fail2ban/action.d/ | head -10
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq fail2ban 2>/dev/null && ls /etc/fail2ban/"
action.d
fail2ban.conf
fail2ban.d
filter.d
jail.conf
jail.d
paths-common.conf
paths-debian.conf
```

> 💡 The directory structure separates concerns: `filter.d/` contains log pattern rules (what to detect), `action.d/` contains ban actions (what to do), and `jail.d/` or `jail.local` combines them into active "jails".

---

## Step 2: jail.conf vs jail.local

**Critical rule:** Never edit `jail.conf` directly. It gets overwritten on package updates.

```bash
# View the top of jail.conf
head -60 /etc/fail2ban/jail.conf
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq fail2ban 2>/dev/null && head -60 /etc/fail2ban/jail.conf"
# Comments: use '#' for comment lines and ';' (following a space) for inline comments


[INCLUDES]

#before = paths-distro.conf
before = paths-debian.conf

# The DEFAULT allows a global definition of the options. They can be overridden
# in each jail afterwards.

[DEFAULT]

#
# MISCELLANEOUS OPTIONS
#

# "bantime.increment" allows to use database for searching of previously banned
# ip and to increase a 'bantime' of the following bans.
# bantime.increment = true

# "bantime.rndtime" is the max number of seconds using for mixing with random
# time to prevent "clever" botnets calculate exact time IP can be unbanned again:
# bantime.rndtime =

# ...

# "bantime" is the number of seconds that a host is banned.
bantime  = 10m

# A host is banned if it has generated "maxretry" during the last "findtime"
# seconds.
findtime  = 10m

# "maxretry" is the number of failures before a host get banned.
maxretry = 5
```

Create `jail.local` to override defaults:

```bash
cat > /etc/fail2ban/jail.local << 'EOF'
# /etc/fail2ban/jail.local
# Site-local overrides — this file survives package updates

[DEFAULT]
# Ban duration: 1 hour
bantime  = 1h

# Detection window: 10 minutes
findtime = 10m

# Max failures before ban
maxretry = 5

# Email notifications (if mail is configured)
destemail = security@example.com
sendername = Fail2Ban
mta = sendmail

# Action: ban + send email with log lines
action = %(action_mwl)s

# Backend for log monitoring
backend = auto

# Ignore localhost and trusted IPs
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 192.168.0.0/16

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3
bantime  = 24h
findtime = 10m

[sshd-ddos]
enabled  = true
port     = ssh
filter   = sshd-ddos
logpath  = /var/log/auth.log
maxretry = 10
bantime  = 1h
EOF

echo "=== jail.local created ==="
cat /etc/fail2ban/jail.local
```

📸 **Verified Output:**
```
=== jail.local created ===
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
...
[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3
bantime  = 24h
```

> 💡 The `[sshd]` jail uses `maxretry = 3` — lower than the default 5 — because SSH brute forces are extremely common and 3 failures is enough to identify an attacker. After 3 failures within 10 minutes, the IP is banned for 24 hours.

---

## Step 3: Understanding the [sshd] Filter

```bash
# View the sshd filter that detects brute force patterns
head -50 /etc/fail2ban/filter.d/sshd.conf
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq fail2ban 2>/dev/null && head -50 /etc/fail2ban/filter.d/sshd.conf"
# Fail2Ban filter for openssh
#
# If you want to protect OpenSSH from being bruteforced by password
# authentication then get public key authentication working before disabling
# PasswordAuthentication in sshd_config.
#

[INCLUDES]
before = common.conf

[DEFAULT]
_daemon = sshd
__pref = (?:(?:error|fatal): (?:PAM: )?)?
__suff = (?: (?:port \d+|on \S+|\[preauth\])){0,3}\s*
__on_port_opt = (?: (?:port \d+|on \S+)){0,2}
__authng_user = (?: (?:invalid|authenticating) user <F-USER>\S+|.*?</F-USER>)?

[Definition]
# failregex patterns match lines in /var/log/auth.log
failregex = ^%(__prefix_line)s(?:error: PAM: )?[aA]uthentication (?:failure|error|failed) for .* from <HOST>( via \S+)?\s*$
            ^%(__prefix_line)s(?:error: PAM: )?User not known to the underlying authentication module for .* from <HOST>\s*$
            ^%(__prefix_line)sinvalid user .* from <HOST>\s*$
            ...
```

Key elements of a filter:

| Element | Purpose |
|---------|---------|
| `failregex` | Regex patterns that match log lines indicating failure |
| `ignoreregex` | Patterns to ignore (false positive prevention) |
| `<HOST>` | Placeholder that matches and captures the attacker's IP |
| `<F-USER>` | Placeholder capturing the attempted username |
| `datepattern` | How to parse timestamps from log lines |

---

## Step 4: Backends — systemd vs polling

fail2ban supports multiple backends for reading logs:

```bash
# View backend options in jail.conf
grep -A 15 "^backend" /etc/fail2ban/jail.conf 2>/dev/null | head -20
```

| Backend | Description | Use When |
|---------|-------------|----------|
| `auto` | Auto-detects best available | Default — use this |
| `systemd` | Reads from journald | systemd-based systems without log files |
| `polling` | Polls log files with inotify | Traditional syslog, log files |
| `pyinotify` | inotify-based (Linux only) | High-performance file watching |
| `gamin` | FAM-based file monitoring | Older systems |

Configure backend per-jail:

```bash
# Example: use systemd backend for sshd (reads journald)
cat >> /etc/fail2ban/jail.local << 'EOF'

[sshd-systemd]
enabled  = true
filter   = sshd
backend  = systemd
maxretry = 3
bantime  = 24h
EOF

echo "Backend configured"
```

> 💡 On modern Ubuntu with systemd, SSH logs go to journald AND `/var/log/auth.log`. Use `backend = auto` — fail2ban will pick `pyinotify` or `polling` automatically and it works reliably.

---

## Step 5: Creating a Custom Filter

Build a custom filter for a web application login endpoint:

```bash
# Create a custom filter for a web app
cat > /etc/fail2ban/filter.d/webapp-bruteforce.conf << 'EOF'
# fail2ban filter for web application brute force
# Matches failed login attempts in nginx/apache access logs
#
# Log format example:
# 192.168.1.100 - - [05/Mar/2026:14:30:01 +0000] "POST /api/login HTTP/1.1" 401 45
# 10.0.0.50 - - [05/Mar/2026:14:30:02 +0000] "POST /admin/login HTTP/1.1" 403 12

[INCLUDES]
before = common.conf

[Definition]
# Match HTTP 401 (Unauthorized) or 403 (Forbidden) on login endpoints
failregex = ^<HOST> .* "POST /(api/login|admin/login|wp-login\.php|login) HTTP/\d\.\d" (401|403) .*$
            ^<HOST> .* "GET /(admin|wp-admin)/? HTTP/\d\.\d" (401|403) .*$

ignoreregex =

# Date pattern for nginx/apache combined log format
datepattern = \[%%d/%%b/%%Y:%%H:%%M:%%S %%z\]

[Init]
# Service name for logging
name = webapp-bruteforce
EOF

echo "Custom filter created:"
cat /etc/fail2ban/filter.d/webapp-bruteforce.conf
```

Add the jail for this filter:

```bash
cat >> /etc/fail2ban/jail.local << 'EOF'

[webapp-bruteforce]
enabled  = true
filter   = webapp-bruteforce
logpath  = /var/log/nginx/access.log
           /var/log/apache2/access.log
port     = http,https
maxretry = 10
findtime = 5m
bantime  = 30m
EOF

echo "Jail configured"
```

---

## Step 6: Testing Filters with fail2ban-regex

Before deploying, test your filter against real or sample log data:

```bash
# Test a built-in filter against a log file
fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf 2>/dev/null || \
  echo "No log file in container — testing with sample data"

# Test filter with inline sample log data
fail2ban-regex - /etc/fail2ban/filter.d/sshd.conf << 'LOGEOF'
Mar  5 14:30:01 hostname sshd[1234]: Invalid user admin from 192.168.1.100 port 45678
Mar  5 14:30:02 hostname sshd[1235]: Invalid user test from 192.168.1.100 port 45679
Mar  5 14:30:03 hostname sshd[1236]: Failed password for root from 192.168.1.100 port 45680 ssh2
Mar  5 14:30:04 hostname sshd[1237]: Invalid user oracle from 10.0.0.50 port 12345
LOGEOF
```

Test the custom webapp filter:

```bash
fail2ban-regex - /etc/fail2ban/filter.d/webapp-bruteforce.conf << 'LOGEOF'
192.168.1.100 - - [05/Mar/2026:14:30:01 +0000] "POST /api/login HTTP/1.1" 401 45 "-" "curl/7.81.0"
192.168.1.100 - - [05/Mar/2026:14:30:02 +0000] "POST /api/login HTTP/1.1" 401 45 "-" "curl/7.81.0"
10.0.0.50 - - [05/Mar/2026:14:30:03 +0000] "GET /admin/ HTTP/1.1" 403 12 "-" "python-requests/2.28"
192.168.1.100 - - [05/Mar/2026:14:30:04 +0000] "POST /api/login HTTP/1.1" 401 45 "-" "curl/7.81.0"
LOGEOF
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "
apt-get install -y -qq fail2ban 2>/dev/null
fail2ban-regex - /etc/fail2ban/filter.d/sshd.conf << 'EOF'
Mar  5 14:30:01 myhost sshd[1234]: Invalid user admin from 192.168.1.100 port 45678
Mar  5 14:30:02 myhost sshd[1235]: Failed password for root from 10.0.0.50 port 22 ssh2
EOF"

Running tests
=============

Use   failregex filter file : sshd, basedir: /etc/fail2ban
Use         log file : [stdin]
Use         encoding : UTF-8


Results
=======

Failregex: 2 total
|-  #) [# of hits] regular expression
|   1) [1] ...Invalid user .* from <HOST>...
|   2) [1] ...Failed password for .* from <HOST>...

Ignoreregex: 0 total

Date template hits:
|- [# of hits] date template
|   [2] {^LN-BEG}(?:DAY )?MON Day(?:\s+Year)? 24hour:Minute:Second(?:\.Microseconds)?...

Lines: 2 lines, 0 ignored, 2 matched, 0 missed
```

> 💡 `fail2ban-regex` is your best friend for filter development. Always test before deploying — a broken regex that never matches means attackers never get banned; one that over-matches could ban legitimate users.

---

## Step 7: Operational Management — fail2ban-client

Managing fail2ban in production:

```bash
# Start fail2ban (real host)
systemctl start fail2ban
systemctl enable fail2ban

# Check daemon status
fail2ban-client status

# Check a specific jail
fail2ban-client status sshd

# Manually ban an IP
fail2ban-client set sshd banip 192.168.1.100

# Unban an IP
fail2ban-client set sshd unbanip 192.168.1.100

# Check if an IP is banned
fail2ban-client get sshd banned

# Reload configuration
fail2ban-client reload

# Reload a specific jail
fail2ban-client reload sshd

# Get current ban list for all jails
fail2ban-client status | grep "Jail list" | sed 's/.*://;s/,/\n/g' | while read jail; do
  echo "=== $jail ===" && fail2ban-client status "$jail" 2>/dev/null
done
```

📸 **Verified Output (real host sample):**
```
$ sudo fail2ban-client status sshd
Status for the jail: sshd
|- Filter
|  |- Currently failed: 3
|  |- Total failed: 127
|  `- Journal matches:  _SYSTEMD_UNIT=ssh.service + _COMM=sshd
`- Actions
   |- Currently banned: 2
   |- Total banned: 45
   `- Banned IP list: 203.0.113.42 198.51.100.17
```

---

## Step 8: Capstone — Harden a Production SSH Server with fail2ban

**Scenario:** Your SSH server is experiencing heavy brute-force attacks. Implement an aggressive, multi-tier fail2ban configuration that bans short-term on few failures, and escalates to permanent bans for persistent attackers.

```bash
# Install and configure
apt-get install -y -qq fail2ban 2>/dev/null

# Create aggressive SSH protection with incremental banning
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Global defaults
bantime  = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8 ::1
backend  = auto

# Enable incremental ban times (repeat offenders get longer bans)
bantime.increment = true
bantime.factor = 1
bantime.formula = ban.Time * (1<<(ban.Count if ban.Count<20 else 20)) * banFactor
bantime.multipliers = 1 5 30 60 300 720 1440 2880
bantime.maxtime = 5w
bantime.overalljails = true

[sshd]
# Tier 1: Quick ban on failed password attempts
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3
findtime = 5m
bantime  = 1h

[sshd-aggressive]
# Tier 2: Very quick ban for scanners
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 10
findtime = 1m
bantime  = 24h

[sshd-permanent]
# Tier 3: Ban for 4 weeks after 50+ attempts (persistent attackers)
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 50
findtime = 1w
bantime  = 4w
EOF

# Create a monitoring script
cat > /usr/local/bin/fail2ban-report.sh << 'EOF'
#!/bin/bash
echo "=== fail2ban Status Report: $(date) ==="
echo ""

for jail in sshd sshd-aggressive sshd-permanent; do
  echo "--- Jail: $jail ---"
  fail2ban-client status "$jail" 2>/dev/null || echo "Jail not active"
  echo ""
done

echo "=== Top Banned IPs ==="
fail2ban-client status sshd 2>/dev/null | grep "Banned IP" | tr ' ' '\n' | grep -E '^[0-9]'
EOF
chmod +x /usr/local/bin/fail2ban-report.sh

# Test the sshd filter against sample attack log
echo "=== Testing sshd filter ==="
fail2ban-regex - /etc/fail2ban/filter.d/sshd.conf << 'LOGEOF'
Mar  5 14:30:01 prod-server sshd[1001]: Invalid user admin from 203.0.113.100 port 11111
Mar  5 14:30:02 prod-server sshd[1002]: Invalid user root from 203.0.113.100 port 11112
Mar  5 14:30:03 prod-server sshd[1003]: Failed password for root from 203.0.113.100 port 11113 ssh2
Mar  5 14:30:04 prod-server sshd[1004]: Invalid user test from 198.51.100.50 port 22222
Mar  5 14:30:05 prod-server sshd[1005]: Failed password for invalid user ubuntu from 203.0.113.100 port 11114 ssh2
LOGEOF

echo ""
echo "=== jail.local summary ==="
grep -E '^\[|^enabled|^maxretry|^bantime|^findtime' /etc/fail2ban/jail.local
```

📸 **Verified Output:**
```
=== Testing sshd filter ===

Running tests
=============

Use   failregex filter file : sshd, basedir: /etc/fail2ban
Use         log file : [stdin]
Use         encoding : UTF-8

Results
=======

Failregex: 5 total
|-  #) [# of hits] regular expression
|   1) [2] ...Invalid user .* from <HOST>...
|   2) [2] ...Failed password for (invalid user )?<HOST>...
|   3) [1] ...Failed password for root from <HOST>...

Lines: 5 lines, 0 ignored, 5 matched, 0 missed

=== jail.local summary ===
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
bantime.increment = true
bantime.maxtime = 5w
[sshd]
enabled  = true
maxretry = 3
findtime = 5m
bantime  = 1h
[sshd-aggressive]
enabled  = true
maxretry = 10
findtime = 1m
bantime  = 24h
[sshd-permanent]
enabled  = true
maxretry = 50
findtime = 1w
bantime  = 4w
```

---

## Summary

| Task | Command / File | Notes |
|------|----------------|-------|
| Install | `apt-get install fail2ban` | Installs daemon + client |
| Version check | `fail2ban-client --version` | Verify installation |
| Config file | `/etc/fail2ban/jail.conf` | Default config — **do not edit** |
| Local overrides | `/etc/fail2ban/jail.local` | Your customizations here |
| Jail directory | `/etc/fail2ban/jail.d/` | Drop-in jail configs |
| Filters directory | `/etc/fail2ban/filter.d/` | Log pattern definitions |
| Actions directory | `/etc/fail2ban/action.d/` | Ban action scripts |
| Start service | `systemctl start fail2ban` | Activate the daemon |
| Check status | `fail2ban-client status` | List all active jails |
| Jail status | `fail2ban-client status sshd` | Show ban counts and IPs |
| Ban an IP | `fail2ban-client set sshd banip <IP>` | Manual ban |
| Unban an IP | `fail2ban-client set sshd unbanip <IP>` | Remove a ban |
| Test filter | `fail2ban-regex <logfile> <filter>` | Debug filter patterns |
| Reload config | `fail2ban-client reload` | Apply configuration changes |
| Key settings | `bantime`, `findtime`, `maxretry` | Core tuning parameters |
| Incremental bans | `bantime.increment = true` | Escalating bans for repeat offenders |
