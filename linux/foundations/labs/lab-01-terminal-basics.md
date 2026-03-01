# Lab 1: Terminal Basics

## 🎯 Objective
Get comfortable with the Linux terminal: logging in, understanding the prompt, running basic commands like `pwd`, `ls`, and `clear`, and navigating your first shell session.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Access to an Ubuntu 22.04 system (physical, VM, or cloud)
- A user account with login credentials

## 🔬 Lab Instructions

### Step 1: Open a Terminal
On a desktop Ubuntu system, press **Ctrl+Alt+T** to open the terminal emulator. On a server, you will be at a terminal after logging in via SSH or directly.

You will see a prompt similar to:
```bash
student@ubuntu:~$
```
This tells you: `username@hostname:current_directory$`

### Step 2: Identify Your Current Location with `pwd`
`pwd` stands for **Print Working Directory**. It shows where you are in the filesystem.

```bash
pwd
# Expected output:
# /home/student
```

### Step 3: List Files and Directories with `ls`
`ls` lists the contents of the current directory.

```bash
ls
# Shows files and directories in your home folder
```

Try with options for more detail:
```bash
ls -l
# Long format: permissions, owner, size, date, name

ls -la
# Long format including hidden files (starting with .)

ls -lh
# Human-readable file sizes (KB, MB, GB)
```

### Step 4: Understand the Prompt Components
Look at your prompt:
```bash
student@ubuntu:~$
# student  = your username
# ubuntu   = hostname of the machine
# ~        = shorthand for your home directory (/home/student)
# $        = regular user (# means root)
```

### Step 5: Clear the Screen with `clear`
When the screen gets cluttered:
```bash
clear
# Clears terminal output
# Shortcut: Ctrl+L does the same thing
```

### Step 6: Use `echo` to Print Text
```bash
echo "Hello, Linux!"
# Output: Hello, Linux!

echo $USER
# Prints your current username

echo $HOME
# Prints your home directory path
```

### Step 7: Check the Date and Time
```bash
date
# Output: Sun Mar  1 05:42:00 UTC 2026

date +"%Y-%m-%d"
# Output: 2026-03-01
```

### Step 8: View System Uptime
```bash
uptime
# Output: 05:42:00 up 2 days,  3:15,  1 user,  load average: 0.00, 0.01, 0.00
```

### Step 9: Use Command History
The shell keeps a history of commands you've run:
```bash
history
# Lists numbered history of past commands

# Press Up/Down arrows to cycle through previous commands
# Ctrl+R to reverse search through history
```

### Step 10: Use Tab Completion
Tab completion saves time and avoids typos:
```bash
# Type 'ls /et' then press Tab
ls /et<TAB>
# Auto-completes to: ls /etc/

# Press Tab twice to see all options when there are multiple matches
ls /etc/ap<TAB><TAB>
```

### Step 11: Learn About a Command with `type`
```bash
type ls
# Output: ls is aliased to `ls --color=auto'

type pwd
# Output: pwd is a shell builtin

type date
# Output: date is /usr/bin/date
```

### Step 12: Exit the Terminal Session
```bash
exit
# Or press Ctrl+D to logout/close the session
```

## ✅ Verification
Run these commands to confirm you understand terminal basics:

```bash
# Print your working directory
pwd
# Should show: /home/yourusername

# List home directory contents
ls -lah ~
# Should show files including hidden ones like .bashrc

# Show username and hostname
echo "User: $USER on $(hostname)"
# Output: User: student on ubuntu
```

## 📝 Summary
- The terminal prompt shows `user@host:directory$` — read it to know your context
- `pwd` tells you where you are; `ls` shows what's there
- `clear` (or Ctrl+L) cleans the screen; `exit` (or Ctrl+D) closes the session
- Tab completion and command history (Up arrow, Ctrl+R) dramatically speed up your workflow
- `echo` prints text and variables; `date` and `uptime` show system state
