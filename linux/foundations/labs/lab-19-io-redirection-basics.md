# Lab 19: I/O Redirection Basics

## 🎯 Objective
Master input/output redirection using >, >>, <, 2>, 2>&1, /dev/null, and tee.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 18: Environment Variables

## 🔬 Lab Instructions

### Step 1: Standard Streams

```text
stdin  (0) — Standard Input  (keyboard by default)
stdout (1) — Standard Output (screen by default)
stderr (2) — Standard Error  (screen by default)
```

### Step 2: Redirect stdout with >

```bash
echo "First line" > /tmp/output.txt
cat /tmp/output.txt
```

**Expected output:**
```
First line
```

```bash
echo "Second line" > /tmp/output.txt
cat /tmp/output.txt
```

**Expected output:**
```
Second line
```

```bash
ls /etc > /tmp/etc-list.txt
wc -l /tmp/etc-list.txt
head -5 /tmp/etc-list.txt
```

### Step 3: Append stdout with >>

```bash
echo "Line 1" > /tmp/append.txt
echo "Line 2" >> /tmp/append.txt
echo "Line 3" >> /tmp/append.txt
cat /tmp/append.txt
```

**Expected output:**
```
Line 1
Line 2
Line 3
```

```bash
echo "$(date): Job started" >> /tmp/my-job.log
echo "$(date): Processing..." >> /tmp/my-job.log
echo "$(date): Job complete" >> /tmp/my-job.log
cat /tmp/my-job.log
```

### Step 4: Redirect stdin with <

```bash
cat > /tmp/names.txt << 'EOF'
alice
bob
charlie
diana
EOF

wc -l < /tmp/names.txt
sort < /tmp/names.txt
```

### Step 5: Redirect stderr with 2>

```bash
ls /nonexistent/path 2>/tmp/errors.txt
echo "Exit code: $?"
cat /tmp/errors.txt
```

**Expected output:**
```
Exit code: 2
ls: cannot access '/nonexistent/path': No such file or directory
```

```bash
ls /etc/passwd /nonexistent 1>/tmp/out.txt 2>/tmp/err.txt
echo "=== stdout ===" && cat /tmp/out.txt
echo "=== stderr ===" && cat /tmp/err.txt
```

### Step 6: Merge stderr into stdout with 2>&1

```bash
ls /etc/passwd /nonexistent > /tmp/combined.txt 2>&1
cat /tmp/combined.txt
```

```bash
ls /etc/passwd /nonexistent &> /tmp/combined2.txt
cat /tmp/combined2.txt
```

### Step 7: Discard Output with /dev/null

```bash
ls /etc > /dev/null
echo "Exit code: $?"

ls /nonexistent 2>/dev/null
echo "No error shown"

ls /etc /nonexistent > /dev/null 2>&1
echo "All output suppressed"
```

### Step 8: Use tee to Split Output

```bash
echo "hello world" | tee /tmp/tee-test.txt
cat /tmp/tee-test.txt
```

```bash
ls /etc | tee /tmp/etc-files.txt | wc -l
echo "File has $(wc -l < /tmp/etc-files.txt) lines"
```

```bash
echo "first" | tee -a /tmp/tee-append.txt
echo "second" | tee -a /tmp/tee-append.txt
cat /tmp/tee-append.txt
```

## ✅ Verification

```bash
echo "Test output" > /tmp/lab19-verify.txt
echo "Appended" >> /tmp/lab19-verify.txt
wc -l < /tmp/lab19-verify.txt

ls /nonexistent 2>/dev/null && echo "found" || echo "not found (error suppressed)"

echo "verify" | tee /tmp/lab19-tee.txt > /dev/null
cat /tmp/lab19-tee.txt

rm /tmp/lab19*.txt /tmp/output.txt /tmp/append.txt /tmp/names.txt /tmp/errors.txt /tmp/out.txt /tmp/err.txt /tmp/combined*.txt /tmp/tee*.txt /tmp/etc-files.txt /tmp/my-job.log 2>/dev/null
echo "Lab 19 complete"
```

## 📝 Summary
- `>` redirects stdout to a file (overwrites); `>>` appends
- `<` reads stdin from a file instead of the keyboard
- `2>` redirects stderr; `2>&1` merges stderr into stdout
- `/dev/null` is a discard sink — output sent there is lost
- `tee` writes output to both a file and stdout simultaneously
- `&>` is bash shorthand for `>file 2>&1`
- Exit code `$?` is 0 for success, non-zero for failure
