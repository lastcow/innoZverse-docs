# Lab 12: grep — Searching Text Like a Pro

## Objective
Use `grep` to search files and command output: case-insensitive search, line numbers, inverted match, count, regex patterns, and recursive search. `grep` is the #1 tool for log analysis and config auditing.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Basic grep

```bash
printf 'apple\nbanana\napricot\nblueberry\ncherry\n' > /tmp/fruits.txt
cat /tmp/fruits.txt
```

**📸 Verified Output:**
```
apple
banana
apricot
blueberry
cherry
```

```bash
grep 'a' /tmp/fruits.txt
```

**📸 Verified Output:**
```
apple
banana
apricot
```

> 💡 `grep` prints every line that **contains** the pattern. By default it's case-sensitive — `grep 'Apple'` would find nothing in this file.

---

## Step 2: Case-Insensitive Search (-i)

```bash
grep -i 'APPLE' /tmp/fruits.txt
```

**📸 Verified Output:**
```
apple
```

---

## Step 3: Show Line Numbers (-n)

```bash
grep -n 'an' /tmp/fruits.txt
```

**📸 Verified Output:**
```
2:banana
```

> 💡 `-n` is essential when reviewing config files — it shows you exactly which line to go to in your editor: `grep -n 'PermitRootLogin' /etc/ssh/sshd_config`

---

## Step 4: Inverted Match (-v)

```bash
grep -v 'a' /tmp/fruits.txt
```

**📸 Verified Output:**
```
blueberry
cherry
```

> 💡 `-v` (inVert) prints lines that **don't** match. Extremely useful for filtering out noise: `grep -v '^#' /etc/ssh/sshd_config` removes all comment lines.

---

## Step 5: Count Matches (-c)

```bash
grep -c 'a' /tmp/fruits.txt
```

**📸 Verified Output:**
```
3
```

---

## Step 6: Extended Regex (-E) — Multiple Patterns

```bash
grep -E '^[ab]' /tmp/fruits.txt
```

**📸 Verified Output:**
```
apple
banana
apricot
blueberry
```

```bash
grep -E 'apple|cherry' /tmp/fruits.txt
```

**📸 Verified Output:**
```
apple
cherry
```

> 💡 `-E` enables **extended regular expressions**: `|` (or), `+` (one or more), `?` (zero or one), `{n,m}` (repeat). `-E` is equivalent to the `egrep` command.

---

## Step 7: grep on System Files

```bash
grep -E '^root|^daemon' /etc/passwd
```

**📸 Verified Output:**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

```bash
# Count packages installed
dpkg -l | grep -c '^ii'
```

**📸 Verified Output:**
```
105
```

```bash
# Find install events in dpkg log
grep 'install' /var/log/dpkg.log | head -3
```

**📸 Verified Output:**
```
2026-02-10 14:05:00 startup archives install
2026-02-10 14:05:00 install base-passwd:amd64 <none> 3.5.52build1
2026-02-10 14:05:00 status half-installed base-passwd:amd64 3.5.52build1
```

---

## Step 8: Capstone — Log Threat Hunting

```bash
cat > /tmp/auth.log << 'EOF'
Mar  5 00:01:02 server sshd[1234]: Accepted password for alice from 10.0.0.5 port 22
Mar  5 00:01:15 server sshd[1235]: Failed password for root from 192.168.99.1 port 54321
Mar  5 00:01:16 server sshd[1235]: Failed password for root from 192.168.99.1 port 54322
Mar  5 00:01:17 server sshd[1235]: Failed password for root from 192.168.99.1 port 54323
Mar  5 00:01:45 server sudo[2001]: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/bash
Mar  5 00:02:00 server sshd[1236]: Accepted publickey for bob from 10.0.0.6 port 22
Mar  5 00:02:30 server sshd[1237]: Failed password for invalid user hacker from 203.0.113.5 port 8822
EOF

echo "=== Failed login attempts ==="
grep 'Failed password' /tmp/auth.log

echo ""
echo "=== Unique attacker IPs ==="
grep 'Failed password' /tmp/auth.log | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | sort -u

echo ""
echo "=== Privilege escalation (sudo) ==="
grep 'sudo' /tmp/auth.log

echo ""
echo "=== Successful logins ==="
grep 'Accepted' /tmp/auth.log | grep -oE 'for [a-z]+ from' | sort | uniq -c
```

**📸 Verified Output:**
```
=== Failed login attempts ===
Mar  5 00:01:15 server sshd[1235]: Failed password for root from 192.168.99.1 port 54321
Mar  5 00:01:16 server sshd[1235]: Failed password for root from 192.168.99.1 port 54322
Mar  5 00:01:17 server sshd[1235]: Failed password for root from 192.168.99.1 port 54323
Mar  5 00:02:30 server sshd[1237]: Failed password for invalid user hacker from 203.0.113.5 port 8822

=== Unique attacker IPs ===
192.168.99.1
203.0.113.5

=== Privilege escalation (sudo) ===
Mar  5 00:01:45 server sudo[2001]: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/bash

=== Successful logins ===
      1 for alice from
      1 for bob from
```

---

## Summary

| Option | Meaning |
|--------|---------|
| `grep 'pattern' file` | Basic search |
| `grep -i` | Case-insensitive |
| `grep -n` | Show line numbers |
| `grep -v` | Invert (exclude matches) |
| `grep -c` | Count matching lines |
| `grep -E` | Extended regex (`|`, `+`, `?`) |
| `grep -o` | Print only the matching part |
| `grep -r` | Recursive search in directories |
| `grep -l` | Print filenames only |
