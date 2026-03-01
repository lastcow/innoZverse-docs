# Lab 11: The nano Text Editor

## 🎯 Objective
Understand how to use the nano text editor. Learn nano's keyboard shortcuts and practice file operations using echo and cat as safe alternatives.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 10: Users and Groups

## 🔬 Lab Instructions

### Step 1: Check if nano is Available

```bash
which nano
nano --version | head -2
```

**Expected output:**
```
/usr/bin/nano
GNU nano, version 6.x
```

### Step 2: nano Key Reference

nano is a terminal text editor. Key shortcuts (^ means Ctrl):

```text
OPEN/SAVE/EXIT:
  nano filename   Open a file
  Ctrl+O          Save (WriteOut), then Enter to confirm
  Ctrl+X          Exit nano

NAVIGATION:
  Ctrl+A          Go to beginning of line
  Ctrl+E          Go to end of line
  Ctrl+Y          Page Up
  Ctrl+V          Page Down
  Ctrl+_          Go to specific line number

EDITING:
  Ctrl+K          Cut current line
  Ctrl+U          Paste (Uncut)
  Ctrl+6          Mark text for selection

SEARCH:
  Ctrl+W          Search for text
  Ctrl+\          Search and replace
  Alt+W           Find next occurrence

OTHER:
  Ctrl+G          Display help
  Ctrl+C          Show cursor position
```

### Step 3: Create Files Without Opening an Editor

```bash
cat > /tmp/myconfig.conf << 'EOF'
# Application Configuration
server_name = webserver01
listen_port = 8080
debug_mode = false
log_file = /var/log/app.log
max_workers = 4
EOF

cat /tmp/myconfig.conf
```

**Expected output:**
```
# Application Configuration
server_name = webserver01
listen_port = 8080
debug_mode = false
log_file = /var/log/app.log
max_workers = 4
```

### Step 4: Simulate Editing — Append Content

```bash
cat >> /tmp/myconfig.conf << 'EOF'
timeout = 30
retry_count = 3
EOF

cat /tmp/myconfig.conf
```

### Step 5: Simulate Editing — Replace a Line

```bash
sed -i 's/debug_mode = false/debug_mode = true/' /tmp/myconfig.conf
grep debug_mode /tmp/myconfig.conf
```

**Expected output:**
```
debug_mode = true
```

### Step 6: Create a Script File

```bash
cat > /tmp/greet.sh << 'EOF'
#!/bin/bash
NAME=${1:-"World"}
echo "Hello, $NAME!"
echo "Today is $(date +%A, %B %d, %Y)"
EOF

chmod +x /tmp/greet.sh
bash /tmp/greet.sh Linux
```

**Expected output:**
```
Hello, Linux!
Today is Sunday, March 01, 2026
```

### Step 7: Practice File Creation Workflow

```bash
cat > /tmp/nano-practice.txt << 'EOF'
Line 1: First entry
Line 2: Second entry
Line 3: Third entry
EOF

echo "File created:"
cat -n /tmp/nano-practice.txt

echo "After appending:"
echo "Line 4: Added by append" >> /tmp/nano-practice.txt
cat -n /tmp/nano-practice.txt

echo "After modification:"
sed -i 's/First/Modified First/' /tmp/nano-practice.txt
cat -n /tmp/nano-practice.txt
```

## ✅ Verification

```bash
cat > /tmp/lab11-verify.txt << 'EOF'
Test file for Lab 11
nano would be used to create this interactively
EOF

wc -l /tmp/lab11-verify.txt
head -1 /tmp/lab11-verify.txt

rm /tmp/lab11-verify.txt /tmp/nano-practice.txt /tmp/myconfig.conf /tmp/greet.sh 2>/dev/null
echo "Lab 11 complete"
```

## 📝 Summary
- nano is a terminal text editor started with `nano filename`
- `Ctrl+O` saves; `Ctrl+X` exits; `Ctrl+W` searches
- nano shows shortcuts at the bottom of the screen (^ = Ctrl)
- For scripts and automation, use `echo`, `cat`, and heredocs instead
- `sed -i` modifies files in-place without opening an interactive editor
- nano is ideal for quick edits on servers without a GUI
