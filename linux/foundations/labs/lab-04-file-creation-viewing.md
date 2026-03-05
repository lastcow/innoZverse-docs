# Lab 04: Creating and Viewing Files

## Objective
Create files in multiple ways, view their contents with different tools, and understand when to use `cat`, `head`, `tail`, `less`, and `wc`. These are the bread-and-butter commands for working with log files and config files.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Creating Empty Files with touch

```bash
touch /tmp/empty.txt
ls -la /tmp/empty.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 0 Mar  5 00:55 /tmp/empty.txt
```

> 💡 `touch` does two things: if the file doesn't exist it creates it (zero bytes). If it does exist, it updates the **access/modification timestamps** — useful in scripts to signal "this file was processed."

---

## Step 2: Writing Content with echo and Redirection

```bash
echo 'Hello, Linux!' > /tmp/hello.txt
cat /tmp/hello.txt
```

**📸 Verified Output:**
```
Hello, Linux!
```

```bash
# Append (>>) vs overwrite (>)
echo 'line2' >> /tmp/hello.txt
echo 'line3' >> /tmp/hello.txt
cat /tmp/hello.txt
```

**📸 Verified Output:**
```
Hello, Linux!
line2
line3
```

> 💡 `>` **overwrites** (destructive). `>>` **appends** (safe). This distinction prevents many accidental data losses. When in doubt, use `>>`.

---

## Step 3: Word Count with wc

```bash
wc /tmp/hello.txt
```

**📸 Verified Output:**
```
 3  4 26 /tmp/hello.txt
```

```bash
# Just lines, words, bytes separately
wc -l /tmp/hello.txt   # lines
wc -w /tmp/hello.txt   # words
wc -c /tmp/hello.txt   # bytes
```

**📸 Verified Output:**
```
3 /tmp/hello.txt
4 /tmp/hello.txt
26 /tmp/hello.txt
```

> 💡 `wc -l` is the fastest way to count entries in a log file. `wc -l /var/log/auth.log` instantly tells you how many authentication events occurred.

---

## Step 4: head and tail for Large Files

```bash
# Generate a 20-line file
seq 1 20 > /tmp/numbers.txt

head -5 /tmp/numbers.txt
```

**📸 Verified Output:**
```
1
2
3
4
5
```

```bash
tail -5 /tmp/numbers.txt
```

**📸 Verified Output:**
```
16
17
18
19
20
```

> 💡 **`tail -f /var/log/syslog`** is one of the most-used monitoring commands — it watches a log file live and prints new lines as they arrive. `-f` = follow.

---

## Step 5: Line Numbers with cat -n

```bash
cat -n /tmp/hello.txt
```

**📸 Verified Output:**
```
     1	Hello, Linux!
     2	line2
     3	line3
```

```bash
# Show non-printable characters
cat -A /tmp/hello.txt
```

**📸 Verified Output:**
```
Hello, Linux!$
line2$
line3$
```

> 💡 `cat -A` shows `$` at line endings (Unix-style `\n`). Windows files show `^M$` — the `^M` is a carriage return (`\r`). This causes "^M errors" when running Windows-created scripts on Linux.

---

## Step 6: Viewing Hex/Octal Content

```bash
echo 'ABC' | od -A x -t x1z
```

**📸 Verified Output:**
```
000000 41 42 43 0a                                      >ABC.<
000004
```

> 💡 `A=0x41`, `B=0x42`, `C=0x43`, `0a=\n` (newline). Understanding hex is essential for malware analysis, binary file parsing, and network packet inspection.

---

## Step 7: tee — Write and Display Simultaneously

```bash
echo "Security event detected at $(date)" | tee /tmp/security.log
cat /tmp/security.log
```

**📸 Verified Output:**
```
Security event detected at Thu Mar  5 00:55:00 UTC 2026
Security event detected at Thu Mar  5 00:55:00 UTC 2026
```

> 💡 `tee` is invaluable in scripts — it lets you **pipe output to a file AND to stdout at the same time**, so you can both log and display results. `command | tee output.log | grep ERROR`

---

## Step 8: Capstone — Parse a Simulated Log File

```bash
# Generate a realistic log file
cat > /tmp/access.log << 'EOF'
2026-03-05 00:01:23 INFO  User alice logged in from 192.168.1.10
2026-03-05 00:01:45 INFO  User bob logged in from 192.168.1.20
2026-03-05 00:02:10 ERROR Failed login for user admin from 10.0.0.99
2026-03-05 00:02:15 ERROR Failed login for user admin from 10.0.0.99
2026-03-05 00:02:20 ERROR Failed login for user admin from 10.0.0.99
2026-03-05 00:03:01 INFO  User alice accessed /etc/passwd
2026-03-05 00:03:45 WARN  Unusual process: nc -lvp 4444 by uid=1001
2026-03-05 00:04:00 ERROR Privilege escalation attempt by bob
EOF

echo "Total log entries:"; wc -l /tmp/access.log
echo ""
echo "First 3 entries:"; head -3 /tmp/access.log
echo ""
echo "Last 2 entries:"; tail -2 /tmp/access.log
echo ""
echo "Error count:"; grep -c "ERROR" /tmp/access.log
```

**📸 Verified Output:**
```
Total log entries:
8 /tmp/access.log

First 3 entries:
2026-03-05 00:01:23 INFO  User alice logged in from 192.168.1.10
2026-03-05 00:01:45 INFO  User bob logged in from 192.168.1.20
2026-03-05 00:02:10 ERROR Failed login for user admin from 10.0.0.99

Last 2 entries:
2026-03-05 00:03:45 WARN  Unusual process: nc -lvp 4444 by uid=1001
2026-03-05 00:04:00 ERROR Privilege escalation attempt by bob

Error count:
4
```

---

## Summary

| Command | Use Case |
|---------|---------|
| `touch file` | Create empty file / update timestamp |
| `echo 'text' > file` | Write/overwrite file |
| `echo 'text' >> file` | Append to file |
| `cat file` | Display entire file |
| `cat -n file` | Display with line numbers |
| `head -N file` | First N lines |
| `tail -N file` | Last N lines |
| `tail -f file` | Follow file in real time |
| `wc -l file` | Count lines |
| `tee file` | Write to file AND stdout |
