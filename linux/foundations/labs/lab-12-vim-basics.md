# Lab 12: vim Text Editor Basics

## 🎯 Objective
Understand vim's modal editing system, learn essential commands, and practice file operations using cat/echo as safe alternatives.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Lab 11: nano Editor

## 🔬 Lab Instructions

### Step 1: Understand vim's Modal Editing

vim operates in distinct modes:

```text
NORMAL MODE (default):
  - Navigate and run commands
  - Press Esc to return here from any mode

INSERT MODE (editing text):
  - Press i to enter from Normal mode
  - Type text normally
  - Press Esc to return to Normal mode

VISUAL MODE (selecting text):
  - Press v to enter from Normal mode

COMMAND MODE (save, quit, search):
  - Press : from Normal mode
```

### Step 2: Check vim Availability

```bash
which vim || which vi
vim --version | head -3
```

### Step 3: Create Test Files Without Opening vim

```bash
cat > /tmp/vim-practice.txt << 'EOF'
The quick brown fox jumps over the lazy dog.
Linux is an open-source operating system.
vim is a powerful text editor used by developers.
Learning vim takes time but increases productivity.
The end of the file.
EOF

cat -n /tmp/vim-practice.txt
```

### Step 4: vim Navigation Commands Reference

```text
CURSOR MOVEMENT:
  h j k l     Left, Down, Up, Right
  w           Move forward one word
  b           Move backward one word
  0           Go to beginning of line
  $           Go to end of line
  gg          Go to first line of file
  G           Go to last line of file
  :N          Go to line N (e.g., :5)
  Ctrl+f      Page forward (down)
  Ctrl+b      Page backward (up)
```

### Step 5: vim Insert Mode Commands

```text
ENTERING INSERT MODE:
  i           Insert before cursor
  a           Insert after cursor (Append)
  I           Insert at beginning of line
  A           Insert at end of line
  o           Open new line below
  O           Open new line above

EXITING INSERT MODE:
  Esc         Return to Normal mode
```

### Step 6: vim Editing Commands (Normal mode)

```text
EDITING:
  x           Delete character under cursor
  dd          Delete (cut) current line
  yy          Yank (copy) current line
  p           Paste after cursor
  u           Undo last change
  Ctrl+r      Redo
  .           Repeat last command

SEARCH AND REPLACE:
  /pattern    Search forward
  n           Next search result
  :%s/old/new/g   Replace all occurrences
```

### Step 7: vim Save and Quit Commands

```text
COMMAND MODE (press : first):
  :w          Save the file
  :q          Quit (fails if unsaved changes)
  :wq         Save and quit
  :q!         Quit WITHOUT saving (force)
  ZZ          Save and quit (Normal mode shortcut)
```

### Step 8: Practice — Simulate vim Operations

```bash
# Simulate search and replace (like :%s/fox/cat/g in vim)
sed 's/fox/cat/g' /tmp/vim-practice.txt
```

```bash
# Extract specific lines (like :3,5p in vim)
sed -n '2,4p' /tmp/vim-practice.txt
```

```bash
# Show line numbers (like :set nu in vim)
cat -n /tmp/vim-practice.txt
```

```bash
# Count lines
wc -l /tmp/vim-practice.txt
```

### Step 9: Full vim Workflow Summary

```text
TYPICAL VIM WORKFLOW:
  1. vim filename     Open file
  2. i               Enter Insert mode
  3. (type content)  Write text
  4. Esc             Back to Normal mode
  5. :wq             Save and quit

TO QUIT WHEN STUCK:
  Esc Esc            Ensure you are in Normal mode
  :q!                Force quit without saving
```

### Step 10: Create a Script Using cat

```bash
cat > /tmp/system-info.sh << 'EOF'
#!/bin/bash
echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "User:     $(whoami)"
echo "Date:     $(date)"
echo "Uptime:   $(uptime -p)"
echo "Kernel:   $(uname -r)"
EOF

chmod +x /tmp/system-info.sh
bash /tmp/system-info.sh
```

## ✅ Verification

```bash
echo "vim location: $(which vim)"
echo "vim version: $(vim --version | head -1)"
echo "Practice file lines: $(wc -l < /tmp/vim-practice.txt)"
cat -n /tmp/vim-practice.txt
rm /tmp/vim-practice.txt /tmp/system-info.sh 2>/dev/null
echo "Lab 12 complete"
```

## 📝 Summary
- vim has three main modes: Normal (navigation), Insert (typing), Command (:)
- Press `i` to enter Insert mode; press `Esc` to return to Normal mode
- `:wq` saves and quits; `:q!` quits without saving
- `dd` deletes a line; `yy` copies; `p` pastes
- `:%s/old/new/g` replaces all occurrences in the file
- If stuck in vim: press `Esc` twice, then type `:q!` and press Enter
