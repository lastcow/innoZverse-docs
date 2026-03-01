# Lab 14: grep Basics

## 🎯 Objective
Use `grep` to search for patterns in files and command output, with practical options like `-i`, `-r`, `-n`, `-v`, and `-l`.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 4 and 13
- Understanding of files and pipelines basics

## 🔬 Lab Instructions

### Step 1: Basic grep Syntax
```bash
# grep pattern file
grep "root" /etc/passwd
# Output: root:x:0:0:root:/root:/bin/bash
# Prints every line containing "root"
```

### Step 2: Case-Insensitive Search with `-i`
```bash
grep "ROOT" /etc/passwd
# Output: (nothing — case-sensitive by default)

grep -i "ROOT" /etc/passwd
# Output: root:x:0:0:root:/root:/bin/bash
# -i makes the search case-insensitive
```

### Step 3: Show Line Numbers with `-n`
```bash
grep -n "bash" /etc/passwd
# Output:
# 1:root:x:0:0:root:/root:/bin/bash
# 32:student:x:1000:1000:...:/bin/bash
# Shows line number before each match
```

### Step 4: Invert Match with `-v` (Show Non-Matching Lines)
```bash
# Show lines that do NOT contain nologin
grep -v "nologin" /etc/passwd
# Shows all lines without "nologin" in them

# Count non-matching lines
grep -v "nologin" /etc/passwd | wc -l
```

### Step 5: Search Recursively with `-r`
```bash
# Search all files under /etc for "ubuntu"
grep -r "ubuntu" /etc 2>/dev/null | head -5
# Searches all files recursively
# Outputs: filename:matching_line
```

### Step 6: Show Only Filenames with `-l`
```bash
# List files that CONTAIN the pattern (not the matching lines)
grep -rl "ubuntu" /etc 2>/dev/null
# Output: just filenames, one per line

# List files that DON'T contain the pattern
grep -rL "ubuntu" /etc 2>/dev/null | head -5
```

### Step 7: Count Matches with `-c`
```bash
# Count matching lines in a file
grep -c "bash" /etc/passwd
# Output: 2 (number of lines containing "bash")

# Count in multiple files
grep -c "root" /etc/passwd /etc/group
# Output:
# /etc/passwd:1
# /etc/group:4
```

### Step 8: Create a Test File and Practice
```bash
cat > /tmp/greptest.txt << 'EOF'
The quick brown fox
A quick brown dog
A lazy cat
The fox ran away
FOX and DOG are animals
Line with numbers: 12345
Email: user@example.com
IP address: 192.168.1.100
EOF
```

### Step 9: Search with Basic Patterns
```bash
# Find lines with "fox"
grep "fox" /tmp/greptest.txt
# Output: The quick brown fox, The fox ran away

# Find lines starting with "The"
grep "^The" /tmp/greptest.txt
# Output: The quick brown fox, The fox ran away

# Find lines ending with "animals"
grep "animals$" /tmp/greptest.txt
# Output: FOX and DOG are animals

# Match any single character with .
grep "f.x" /tmp/greptest.txt
# Output: The quick brown fox, The fox ran away
```

### Step 10: Use grep with Pipes
```bash
# Filter ps output for specific processes
ps aux | grep "bash"
# Shows bash processes

# Find files containing a pattern then filter
ls /etc | grep ".conf"
# Shows .conf files in /etc

# Chain multiple greps
cat /etc/passwd | grep "bash" | grep -v "root"
# Shows users with bash but not root
```

### Step 11: Show Context Around Matches
```bash
# Show 2 lines AFTER the match
grep -A 2 "fox" /tmp/greptest.txt

# Show 2 lines BEFORE the match
grep -B 2 "cat" /tmp/greptest.txt

# Show 2 lines AROUND the match
grep -C 2 "cat" /tmp/greptest.txt
```

### Step 12: Search for Fixed Strings with `-F`
```bash
# By default, grep treats the pattern as a regex
# . * + ? [ ] are special regex characters

# To search literally for "192.168.1.100" (dots are literal)
grep -F "192.168.1.100" /tmp/greptest.txt
# Output: IP address: 192.168.1.100

# Without -F, dot matches any character:
grep "192.168.1.100" /tmp/greptest.txt
# Also works here, but in regex 168.1 would match "168X1" too

# Clean up
rm /tmp/greptest.txt
```

## ✅ Verification
```bash
# Search the system passwd file
grep -n "bash" /etc/passwd
# Should show root and your user with line numbers

grep -c "nologin" /etc/passwd
# Should show a positive number

grep -v "nologin" /etc/passwd | grep -v "false" | wc -l
# Shows users with actual login shells
```

## 📝 Summary
- `grep pattern file` searches for lines matching a pattern
- `-i` = case-insensitive; `-n` = show line numbers; `-v` = invert (show non-matches)
- `-r` = recursive search in directories; `-l` = show filenames only; `-c` = count matches
- `^` matches start of line; `$` matches end; `.` matches any character
- `-A`, `-B`, `-C` show context lines around matches — useful for log analysis
- Pipe output into grep to filter any command's output: `cmd | grep pattern`
