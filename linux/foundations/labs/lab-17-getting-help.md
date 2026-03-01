# Lab 17: Getting Help in Linux

## 🎯 Objective
Learn to find help using man pages, --help flags, type, which, whatis, and apropos commands.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 16: Process Basics

## 🔬 Lab Instructions

### Step 1: Use --help for Quick Reference

```bash
ls --help | head -20
cp --help | head -15
grep --help | head -20
```

### Step 2: Read Man Pages (non-interactive)

```bash
man -P cat ls 2>/dev/null | head -30
```

**Expected output:**
```
LS(1)                            User Commands                           LS(1)

NAME
       ls - list directory contents
...
```

```bash
man -P cat grep 2>/dev/null | head -40
```

```bash
echo "Section 1 = User commands (ls, grep, cp)"
echo "Section 2 = System calls (open, read, write)"
echo "Section 5 = File formats (/etc/passwd, fstab)"
echo "Section 8 = Admin commands (mount, iptables)"

man -P cat 5 passwd 2>/dev/null | head -20
```

### Step 3: Find Command Location with which

```bash
which ls
which bash
which python3
which grep
```

**Expected output:**
```
/usr/bin/ls
/usr/bin/bash
/usr/bin/python3
/usr/bin/grep
```

```bash
which vim && echo "vim is installed" || echo "vim not found"
which nmap && echo "nmap is installed" || echo "nmap not found"
```

### Step 4: Identify Command Type with type

```bash
type ls
type cd
type echo
type if
```

**Expected output:**
```
ls is /usr/bin/ls
cd is a shell builtin
echo is a shell builtin
if is a shell keyword
```

```bash
type -a echo
```

### Step 5: One-Line Descriptions with whatis

```bash
whatis 2>/dev/null ls
whatis 2>/dev/null grep
whatis 2>/dev/null bash
whatis 2>/dev/null passwd
```

**Expected output:**
```
ls (1)               - list directory contents
grep (1)             - print lines that match patterns
```

### Step 6: Search Man Pages with apropos

```bash
apropos "list files" 2>/dev/null | head -10
apropos network 2>/dev/null | head -10
apropos compress 2>/dev/null | head -10
```

### Step 7: Built-in Shell Help

```bash
help cd | head -15
help | head -20
help for | head -15
```

## ✅ Verification

```bash
echo "=== which locations ==="
which ls grep bash python3

echo "=== type results ==="
type ls
type cd
type echo

echo "=== whatis 2>/dev/null ==="
whatis 2>/dev/null ls 2>/dev/null
whatis 2>/dev/null grep 2>/dev/null

echo "=== man page excerpt ==="
man -P cat ls 2>/dev/null | head -10

echo "Lab 17 complete"
```

## 📝 Summary
- `command --help` gives a quick reference for most commands
- `man -P cat command` reads a man page without requiring an interactive pager
- Man pages are organized into sections: 1=user commands, 5=file formats, 8=admin
- `which command` shows the full path to an installed command
- `type command` shows whether something is a binary, shell builtin, or keyword
- `whatis 2>/dev/null command` gives a one-line description
- `apropos keyword` searches for commands related to a topic
