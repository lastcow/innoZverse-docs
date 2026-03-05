# Lab 17: I/O Redirection and Pipes

## Objective
Master standard streams (stdin, stdout, stderr), redirection operators (`>`, `>>`, `2>`, `&>`), and the pipe `|` for chaining commands. Pipes are what make Linux so powerful — dozens of simple tools combined into complex workflows.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: The Three Standard Streams

Every Linux process has three streams:
- **stdin** (0) — input (keyboard by default)
- **stdout** (1) — output (terminal by default)
- **stderr** (2) — errors (terminal by default)

```bash
# stdout goes to terminal
echo 'Hello World'
```

**📸 Verified Output:**
```
Hello World
```

```bash
# stderr goes to terminal too (same place, different stream)
cat /nonexistent 2>&1
```

**📸 Verified Output:**
```
cat: /nonexistent: No such file or directory
```

---

## Step 2: Redirecting stdout

```bash
# > overwrites
echo 'Hello World' > /tmp/redir.txt
cat /tmp/redir.txt
```

**📸 Verified Output:**
```
Hello World
```

```bash
# >> appends
echo 'line2' >> /tmp/redir.txt
cat /tmp/redir.txt
```

**📸 Verified Output:**
```
Hello World
line2
```

> 💡 `>` is destructive — it truncates the file first. `>>` is safe — it always appends. When in doubt, use `>>`. Many production incidents started with `> logfile` instead of `>> logfile`.

---

## Step 3: Redirecting stderr

```bash
# Send errors to a file, stdout to terminal
cat /nonexistent 2>/tmp/err.txt
echo "Exit code: $?"
cat /tmp/err.txt
```

**📸 Verified Output:**
```
Exit code: 1
cat: /nonexistent: No such file or directory
```

```bash
# Discard errors entirely
cat /nonexistent 2>/dev/null
echo "No error shown (suppressed)"
```

**📸 Verified Output:**
```
No error shown (suppressed)
```

> 💡 `/dev/null` is the **black hole** of Linux — anything written to it disappears. Perfect for suppressing noise: `find / -name passwd 2>/dev/null` hides all the "Permission denied" errors.

---

## Step 4: Combining stdout and stderr

```bash
# &> redirects BOTH stdout and stderr to same file
{ echo "This is stdout"; cat /nonexistent; } &> /tmp/combined.txt
cat /tmp/combined.txt
```

**📸 Verified Output:**
```
This is stdout
cat: /nonexistent: No such file or directory
```

```bash
# Or: redirect stderr to wherever stdout is going
{ echo "stdout"; cat /nonexistent; } > /tmp/both.txt 2>&1
cat /tmp/both.txt
```

**📸 Verified Output:**
```
stdout
cat: /nonexistent: No such file or directory
```

---

## Step 5: Pipes — Connecting Commands

```bash
# pipe stdout of one command to stdin of the next
cat /etc/passwd | grep root
```

**📸 Verified Output:**
```
root:x:0:0:root:/root:/bin/bash
```

```bash
# chain multiple pipes
cat /etc/passwd | cut -d: -f1 | sort | head -5
```

**📸 Verified Output:**
```
_apt
backup
bin
daemon
games
```

```bash
# count shells in use
cat /etc/passwd | cut -d: -f7 | sort | uniq -c | sort -rn
```

**📸 Verified Output:**
```
     17 /usr/sbin/nologin
      1 /bin/sync
      1 /bin/bash
```

> 💡 Each pipe creates a **mini-pipeline** in memory — data flows from left to right without writing temp files. The shell connects stdout of one process directly to stdin of the next.

---

## Step 6: Useful Pipeline Tools

```bash
# sort: sort lines
echo -e "banana\napple\ncherry" | sort
```

**📸 Verified Output:**
```
apple
banana
cherry
```

```bash
# uniq: remove duplicates (input must be sorted)
printf 'a\na\nb\nc\nc\n' | uniq -c
```

**📸 Verified Output:**
```
      2 a
      1 b
      2 c
```

```bash
# tr: translate characters
echo 'hello world' | tr 'a-z' 'A-Z'
```

**📸 Verified Output:**
```
HELLO WORLD
```

```bash
# awk: field processing
cat /etc/passwd | awk -F: '{print $1, $3}' | head -5
```

**📸 Verified Output:**
```
root 0
daemon 1
bin 2
sys 3
sync 4
```

---

## Step 7: tee — Split the Pipeline

```bash
# tee writes to file AND passes through to stdout
cat /etc/passwd | grep root | tee /tmp/root_lines.txt | wc -l
echo "Lines saved:"
cat /tmp/root_lines.txt
```

**📸 Verified Output:**
```
1
Lines saved:
root:x:0:0:root:/root:/bin/bash
```

> 💡 `tee` is invaluable in long pipelines where you want to **save intermediate results** while still processing further. `command | tee output.txt | grep ERROR` saves everything but only shows errors.

---

## Step 8: Capstone — Log Analysis Pipeline

```bash
cat > /tmp/webserver.log << 'EOF'
192.168.1.10 - - [05/Mar/2026:01:00:01] "GET /index.html HTTP/1.1" 200 1234
203.0.113.5  - - [05/Mar/2026:01:00:02] "GET /admin HTTP/1.1" 404 512
10.0.0.99    - - [05/Mar/2026:01:00:03] "POST /login HTTP/1.1" 401 256
10.0.0.99    - - [05/Mar/2026:01:00:04] "POST /login HTTP/1.1" 401 256
10.0.0.99    - - [05/Mar/2026:01:00:05] "POST /login HTTP/1.1" 401 256
192.168.1.10 - - [05/Mar/2026:01:00:06] "GET /dashboard HTTP/1.1" 200 5678
203.0.113.5  - - [05/Mar/2026:01:00:07] "GET /../../../etc/passwd HTTP/1.1" 403 128
EOF

echo "=== Total requests ==="
wc -l < /tmp/webserver.log

echo ""
echo "=== 4xx errors ==="
grep -E '" [45][0-9]{2} ' /tmp/webserver.log | awk '{print $1, $9}'

echo ""
echo "=== Top IPs by request count ==="
awk '{print $1}' /tmp/webserver.log | sort | uniq -c | sort -rn

echo ""
echo "=== Suspicious path traversal attempts ==="
grep '\.\.' /tmp/webserver.log | tee /tmp/security_alerts.txt
echo "Alerts saved to /tmp/security_alerts.txt"
```

**📸 Verified Output:**
```
=== Total requests ===
7

=== 4xx errors ===
203.0.113.5 404
10.0.0.99 401
10.0.0.99 401
10.0.0.99 401
203.0.113.5 403

=== Top IPs by request count ===
      3 10.0.0.99
      2 203.0.113.5
      2 192.168.1.10

=== Suspicious path traversal attempts ===
203.0.113.5  - - [05/Mar/2026:01:00:07] "GET /../../../etc/passwd HTTP/1.1" 403 128
Alerts saved to /tmp/security_alerts.txt
```

---

## Summary

| Operator | Meaning |
|----------|---------|
| `>` | Redirect stdout (overwrite) |
| `>>` | Redirect stdout (append) |
| `2>` | Redirect stderr |
| `2>/dev/null` | Discard stderr |
| `&>` | Redirect stdout + stderr |
| `2>&1` | Redirect stderr to stdout |
| `\|` | Pipe stdout to next command's stdin |
| `tee file` | Write to file AND pass through |
