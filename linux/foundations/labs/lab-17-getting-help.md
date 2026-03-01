# Lab 17: Getting Help in Linux

## 🎯 Objective
Learn to find help for any Linux command using `man` pages, `--help` flags, `apropos`, `whatis`, and `info` — so you can always figure out how something works without searching the internet.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic navigation skills

## 🔬 Lab Instructions

### Step 1: The `--help` Flag
Most commands accept `--help` or `-h` for quick usage info:

```bash
ls --help
# Output: Usage and all options listed

cp --help | head -20
# Pipe through head to see just the beginning

grep --help | less
# Use less to page through long help output
```

### Step 2: Reading Man Pages with `man`
```bash
man ls
# Opens the manual page for ls
# Navigation: same as less (arrows, space, q to quit, / to search)
```

### Step 3: Navigate a Man Page
```
Keys inside man:
Space / PgDn:  next page
b / PgUp:      previous page
/pattern:      search forward
n:             next search match
N:             previous search match
G:             jump to end
gg:            jump to beginning
q:             quit
```

### Step 4: Understand Man Page Sections
Man pages are organized into numbered sections:
```
1:  User commands (ls, grep, find...)
2:  System calls (open, read, write...)
3:  Library functions (printf, malloc...)
4:  Special files (/dev/...)
5:  File formats (/etc/passwd...)
6:  Games
7:  Miscellaneous
8:  System administration commands (sudo, mount...)
```

```bash
# Specify a section number
man 5 passwd
# Shows format of /etc/passwd (section 5), not the passwd command

man 1 passwd
# Shows the passwd command (section 1)

# See which sections are available
man -k passwd
```

### Step 5: Search Man Pages with `apropos`
```bash
# Don't know the command name? Search by keyword
apropos "disk usage"
# Output: df (1) - report file system disk space usage
#         du (1) - estimate file space usage
#         ...

apropos "search files"
# Finds commands related to searching files

apropos "network"
# Lists all network-related man pages
```

### Step 6: Quick Description with `whatis`
```bash
whatis ls
# Output: ls (1) - list directory contents

whatis grep
# Output: grep (1) - print lines that match patterns

whatis passwd
# Output: passwd (1) - change user password
#         passwd (5) - the password file
```

### Step 7: Update the Man Page Database
```bash
# If apropos/whatis return nothing or errors, update the database
sudo mandb
# This rebuilds the man page index
```

### Step 8: Use `info` for GNU Commands
```bash
# info provides more detailed documentation for GNU tools
info ls
# Navigation:
# n: next node
# p: previous node
# u: up to parent
# Enter on a link: follow it
# q: quit

info coreutils
# Shows the full GNU coreutils documentation
```

### Step 9: Use `help` for Shell Builtins
```bash
# bash builtins don't have man pages — use help instead
help cd
# Shows help for the cd builtin

help echo
help read
help export

# List all builtins
help
```

### Step 10: Quick Reference with `tldr`
```bash
# Install tldr for community-maintained quick examples
sudo apt install tldr -y
tldr --update

tldr ls
# Shows practical examples:
# - ls
#   List directory contents.
#   
#   - List files one per line:
#     ls -1
#   - List all files, including hidden files:
#     ls -a

tldr find
tldr grep
```

### Step 11: Search Within a Man Page
```bash
man grep
# Now inside man, press /
# Type: recursive
# Press Enter to jump to the first match
# Press n for next match
```

### Step 12: Save Man Pages to Text Files
```bash
# Convert a man page to a text file
man ls | col -b > /tmp/ls_manual.txt
wc -l /tmp/ls_manual.txt

# Or use man -P cat to avoid pager
man -P cat ls | head -50

rm /tmp/ls_manual.txt
```

## ✅ Verification
```bash
# Use help to find a command for copying files
apropos "copy files"
# Should suggest cp

# Get quick info on df
whatis df
# Output: df (1) - report file system disk space usage

# Get help on a builtin
help pwd
# Shows pwd builtin description

# Use man to find the -h option for du
man du | grep -A2 "\-h,"
# Should show the human-readable option
```

## 📝 Summary
- `command --help` gives a quick summary of options — the fastest way to get help
- `man command` opens the full manual page — the authoritative reference
- `apropos keyword` finds commands when you don't know the name
- `whatis command` gives a one-line description of what a command does
- `help builtin` is used for bash builtins (cd, echo, export, etc.) since they lack man pages
- `tldr command` provides concise, practical examples — great supplement to man pages
