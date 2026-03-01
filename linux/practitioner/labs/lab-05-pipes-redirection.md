# Lab 5: Pipes and Redirection

## 🎯 Objective
Build multi-stage pipelines, combine commands with pipes, use tee to split streams, and master advanced redirection patterns.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 19: I/O Redirection Basics
- Foundations Lab 14: grep Basics

## 🔬 Lab Instructions

### Step 1: Basic Pipe Concept

```bash
# | sends stdout of left command to stdin of right command
ls /etc | head -5
```

```bash
# Chain multiple pipes
ls /etc | grep "\.conf$" | sort | head -10
```

```bash
# Count files in /etc
ls /etc | wc -l
```

### Step 2: Process List Pipelines

```bash
# ps aux | grep | awk | sort | head
ps aux | grep -v "^USER" | awk '{ print $1, $3, $11 }' | sort -k2 -rn | head -10
```

```bash
# Find top memory consumers
ps aux | grep -v "^USER" | awk '$4 > 0 { print $4, $11 }' | sort -rn | head -5
```

```bash
# Count processes by user
ps aux | grep -v "^USER" | awk '{ print $1 }' | sort | uniq -c | sort -rn | head -10
```

### Step 3: File Analysis Pipelines

```bash
# Count users with each shell type
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn
```

```bash
# Find the 3 highest UIDs
cut -d: -f1,3 /etc/passwd | sort -t: -k2 -rn | head -3
```

```bash
# List /etc files sorted by size
find /etc -maxdepth 1 -type f -exec ls -la {} \; 2>/dev/null | sort -k5 -rn | head -10
```

### Step 4: Use tee to Branch Pipelines

```bash
# tee writes to file AND passes to next command
ls /etc | tee /tmp/etc-list.txt | wc -l
echo "File has $(wc -l < /tmp/etc-list.txt) lines"
```

```bash
# Logging with tee: save and process simultaneously
ps aux | tee /tmp/process-snapshot.txt | grep "$(whoami)" | wc -l
echo "Total lines saved: $(wc -l < /tmp/process-snapshot.txt)"
```

### Step 5: Process Substitution

```bash
# <() creates a virtual file from command output
diff <(cut -d: -f1 /etc/passwd | sort) <(cut -d: -f1 /etc/group | sort) | head -20
```

```bash
# Paste two command outputs side by side
paste <(cut -d: -f1 /etc/passwd | head -5) <(cut -d: -f3 /etc/passwd | head -5)
```

### Step 6: Here-Documents and Here-Strings

```bash
# Heredoc (multi-line stdin)
cat << 'EOF'
This is line 1
This is line 2
This is line 3
EOF
```

```bash
# Here-string (single value to stdin)
grep "bash" <<< "/usr/bin/bash is the shell"
```

```bash
# Heredoc into command pipeline
cat << 'EOF' | sort | uniq -c
apple
banana
apple
cherry
banana
apple
EOF
```

### Step 7: Advanced Redirection Patterns

```bash
# Capture both stdout and stderr
ls /etc/passwd /nonexistent 2>&1 | head -5
```

```bash
# Run command, log errors, continue
find /etc -name "*.conf" 2>/dev/null | head -10
```

```bash
# Write to multiple files simultaneously
echo "test data" | tee /tmp/pipe-a.txt /tmp/pipe-b.txt > /dev/null
diff /tmp/pipe-a.txt /tmp/pipe-b.txt && echo "Files are identical"
```

### Step 8: Real-World Pipeline

```bash
# System report pipeline
echo "=== Top 5 CPU Processes ===" && \
ps aux --sort=-%cpu | grep -v "^USER" | head -6 | awk '{ printf "%-20s %5s%%\n", $11, $3 }'
```

```bash
echo "=== Filesystem Usage ===" && \
df -h | grep -v tmpfs | awk 'NR>1 { printf "%-30s %5s used\n", $6, $5 }'
```

## ✅ Verification

```bash
echo "=== Pipeline test ===" && ps aux | grep -v "^USER" | wc -l
echo "=== tee test ===" && echo "hello" | tee /tmp/lab5-verify.txt > /dev/null && cat /tmp/lab5-verify.txt
echo "=== Process substitution ===" && wc -l <(cat /etc/passwd) | awk '{print "Lines:", $1}'
rm /tmp/etc-list.txt /tmp/process-snapshot.txt /tmp/pipe-a.txt /tmp/pipe-b.txt /tmp/lab5-verify.txt 2>/dev/null
echo "Practitioner Lab 5 complete"
```

## 📝 Summary
- `|` connects commands: stdout of left becomes stdin of right
- Build pipelines: `ps aux | grep | awk | sort | head`
- `tee` splits output to file and stdout simultaneously
- Process substitution `<()` creates virtual file-like inputs
- Heredoc `<< 'EOF'` provides multi-line stdin to commands
- Here-string `<<<` sends a single string to stdin
