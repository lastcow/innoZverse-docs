# Lab 4: File Creation and Viewing

## 🎯 Objective
Learn to create files and view their contents using touch, cat, head, tail, wc, and the file command.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 3: Directory Navigation

## 🔬 Lab Instructions

### Step 1: Create Files with touch

```bash
touch /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**Expected output:**
```
-rw-rw-r-- 1 zchen zchen 0 Mar  1 17:00 /tmp/myfile.txt
```

```bash
touch /tmp/file1.txt /tmp/file2.txt /tmp/file3.txt
ls /tmp/file*.txt
```

### Step 2: Write Content to Files

```bash
echo "Line 1: Hello World" > /tmp/sample.txt
echo "Line 2: Linux is powerful" >> /tmp/sample.txt
echo "Line 3: Practice makes perfect" >> /tmp/sample.txt
echo "Line 4: Keep learning" >> /tmp/sample.txt
echo "Line 5: End of file" >> /tmp/sample.txt
```

```bash
cat > /tmp/config.txt << 'EOF'
server=web01
port=8080
debug=false
log_level=info
max_connections=100
EOF
```

### Step 3: View Files with cat

```bash
cat /tmp/sample.txt
```

**Expected output:**
```
Line 1: Hello World
Line 2: Linux is powerful
Line 3: Practice makes perfect
Line 4: Keep learning
Line 5: End of file
```

```bash
cat -n /tmp/sample.txt
```

### Step 4: View Start of Files with head

```bash
head -n 3 /tmp/sample.txt
```

**Expected output:**
```
Line 1: Hello World
Line 2: Linux is powerful
Line 3: Practice makes perfect
```

```bash
head -n 5 /etc/passwd
```

### Step 5: View End of Files with tail

```bash
tail -n 2 /tmp/sample.txt
```

**Expected output:**
```
Line 4: Keep learning
Line 5: End of file
```

```bash
head -n 4 /tmp/sample.txt | tail -n 2
```

**Expected output:**
```
Line 3: Practice makes perfect
Line 4: Keep learning
```

### Step 6: Count with wc

```bash
wc /tmp/sample.txt
```

**Expected output:**
```
 5 15 89 /tmp/sample.txt
```

```bash
wc -l /tmp/sample.txt
wc -w /tmp/sample.txt
wc -c /tmp/sample.txt
wc -l /etc/passwd
```

### Step 7: Identify File Type with file

```bash
file /tmp/sample.txt
```

**Expected output:**
```
/tmp/sample.txt: ASCII text
```

```bash
file /bin/ls
```

**Expected output:**
```
/bin/ls: ELF 64-bit LSB pie executable, x86-64, ...
```

```bash
file /etc/passwd /bin/bash /tmp/sample.txt
```

## ✅ Verification

```bash
echo "verification test" > /tmp/lab4-verify.txt
echo "second line" >> /tmp/lab4-verify.txt
echo "third line" >> /tmp/lab4-verify.txt

echo "Lines: $(wc -l < /tmp/lab4-verify.txt)"
echo "First: $(head -n 1 /tmp/lab4-verify.txt)"
echo "Last:  $(tail -n 1 /tmp/lab4-verify.txt)"
echo "Type:  $(file /tmp/lab4-verify.txt)"

rm /tmp/lab4-verify.txt /tmp/sample.txt /tmp/config.txt /tmp/myfile.txt /tmp/file*.txt 2>/dev/null
echo "Lab 4 complete"
```

## 📝 Summary
- `touch` creates empty files or updates timestamps
- `echo "text" > file` creates/overwrites; `echo "text" >> file` appends
- `cat` displays entire file; `cat -n` adds line numbers
- `head -n N` shows first N lines; `tail -n N` shows last N lines
- `wc -l` counts lines; `wc -w` words; `wc -c` characters
- `file` identifies the type of a file based on its content
