# Lab 19: I/O Redirection Basics

## 🎯 Objective
Understand standard input, output, and error streams, and redirect them using `>`, `>>`, `<`, `2>`, and `/dev/null`.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic terminal usage

## 🔬 Lab Instructions

### Step 1: Understand Standard Streams
Every process has three default file descriptors:
```
0 = stdin  (standard input)  — keyboard by default
1 = stdout (standard output) — terminal by default
2 = stderr (standard error)  — terminal by default
```

```bash
# Commands read from stdin and write to stdout/stderr
cat         # reads from keyboard (stdin), writes to terminal (stdout)
# Type something, press Enter, Ctrl+D to stop
```

### Step 2: Redirect stdout with `>`
```bash
# Send output to a file instead of the terminal
echo "Hello, world!" > /tmp/output.txt
cat /tmp/output.txt
# Output: Hello, world!

# IMPORTANT: > OVERWRITES the file
echo "Second line" > /tmp/output.txt
cat /tmp/output.txt
# Output: Second line  (first line is GONE!)
```

### Step 3: Append stdout with `>>`
```bash
echo "Line one" > /tmp/append.txt
echo "Line two" >> /tmp/append.txt
echo "Line three" >> /tmp/append.txt
cat /tmp/append.txt
# Output:
# Line one
# Line two
# Line three
```

### Step 4: Redirect a Command's Output to a File
```bash
# Save ls output to a file
ls -la /etc > /tmp/etc_listing.txt
wc -l /tmp/etc_listing.txt
cat /tmp/etc_listing.txt | head -5

# Save ps output
ps aux > /tmp/processes.txt
grep "bash" /tmp/processes.txt
```

### Step 5: Redirect stdin with `<`
```bash
# Provide file as input instead of keyboard
cat < /etc/hostname
# Output: ubuntu  (same as cat /etc/hostname, but using redirection)

# Sort the contents of a file
sort < /tmp/etc_listing.txt | head -5

# Count lines from a file via stdin
wc -l < /etc/passwd
# Output: 42  (just the number, no filename)
```

### Step 6: Redirect stderr with `2>`
```bash
# Generate an error
ls /nonexistent
# Output: ls: cannot access '/nonexistent': No such file or directory
# This goes to stderr

# Redirect stderr to a file
ls /nonexistent 2> /tmp/errors.txt
cat /tmp/errors.txt
# Output: ls: cannot access '/nonexistent': No such file or directory

# stdout goes to terminal as normal, stderr goes to file
ls / 2> /tmp/errors.txt
# Lists / normally (stdout to terminal), no error output visible
```

### Step 7: Separate stdout and stderr
```bash
# Send stdout and stderr to different files
ls / /nonexistent > /tmp/stdout.txt 2> /tmp/stderr.txt

cat /tmp/stdout.txt
# Output: contents of /

cat /tmp/stderr.txt
# Output: error for /nonexistent
```

### Step 8: Redirect Both stdout and stderr to One File
```bash
# Method 1: redirect stderr to stdout, then redirect stdout
ls / /nonexistent > /tmp/all_output.txt 2>&1
# 2>&1 means "send stderr to the same place as stdout"
cat /tmp/all_output.txt
# Output: both directory listing and error

# Method 2: shorthand (bash 4+)
ls / /nonexistent &> /tmp/all_output2.txt
cat /tmp/all_output2.txt
```

### Step 9: Discard Output with `/dev/null`
```bash
# /dev/null is a black hole — anything written to it is discarded

# Suppress stdout
ls / > /dev/null
# No output

# Suppress stderr (hide error messages)
ls /nonexistent 2> /dev/null
# No output, no error message

# Suppress EVERYTHING
ls / /nonexistent &> /dev/null
# Total silence
```

### Step 10: Here Document (heredoc)
```bash
# Provide multiple lines of input directly in the script
cat > /tmp/myconfig.txt << EOF
[settings]
debug=false
port=8080
host=localhost
EOF

cat /tmp/myconfig.txt
# Output:
# [settings]
# debug=false
# port=8080
# host=localhost
```

### Step 11: Pipe vs Redirect
```bash
# PIPE: connects stdout of one command to stdin of another
cat /etc/passwd | grep "bash" | cut -d: -f1
# (file → cat → grep → cut → terminal)

# REDIRECT: connects to a file
cat /etc/passwd > /tmp/passwd_copy.txt
# (file → cat → file)

# You can combine both!
cat /etc/passwd | grep "bash" > /tmp/bash_users.txt
cat /tmp/bash_users.txt
```

### Step 12: Practical Examples
```bash
# Log command output with timestamp
echo "=== $(date) ===" >> /tmp/mylog.txt
df -h >> /tmp/mylog.txt
echo "" >> /tmp/mylog.txt

cat /tmp/mylog.txt

# Run a command silently (ignore all output)
apt list --installed 2>/dev/null | wc -l

# Clean up
rm -f /tmp/output.txt /tmp/append.txt /tmp/etc_listing.txt
rm -f /tmp/processes.txt /tmp/errors.txt /tmp/stdout.txt /tmp/stderr.txt
rm -f /tmp/all_output.txt /tmp/all_output2.txt /tmp/myconfig.txt
rm -f /tmp/bash_users.txt /tmp/passwd_copy.txt /tmp/mylog.txt
```

## ✅ Verification
```bash
# Test all redirection types
echo "stdout" > /tmp/rtest_out.txt
echo "stderr" 2> /tmp/rtest_err.txt
ls /missing 2> /tmp/rtest_err2.txt

cat /tmp/rtest_out.txt
# Output: stdout

cat /tmp/rtest_err2.txt
# Output: ls: cannot access...

rm /tmp/rtest_*.txt
```

## 📝 Summary
- Three standard streams: stdin (0), stdout (1), stderr (2)
- `>` redirects stdout to a file (overwrites); `>>` appends
- `<` redirects a file to stdin
- `2>` redirects stderr to a file; `2>&1` redirects stderr to stdout's destination
- `&>` or `> file 2>&1` captures both stdout and stderr in one file
- `/dev/null` discards everything written to it — use to silence noisy commands
