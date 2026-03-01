# Lab 4: File Creation and Viewing

## 🎯 Objective
Learn to create files with `touch`, view them with `cat`, `less`, `more`, `head`, and `tail`, and understand when to use each tool.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–3
- Comfort with navigating the filesystem

## 🔬 Lab Instructions

### Step 1: Create an Empty File with `touch`
```bash
cd ~
touch myfile.txt
ls -la myfile.txt
# Output: -rw-rw-r-- 1 student student 0 Mar  1 05:42 myfile.txt
# Notice: size is 0 — file is empty
```

### Step 2: Create Multiple Files at Once
```bash
touch file1.txt file2.txt file3.txt
ls *.txt
# Output: file1.txt  file2.txt  file3.txt  myfile.txt

# Use brace expansion
touch report_{jan,feb,mar}.txt
ls report_*.txt
# Output: report_feb.txt  report_jan.txt  report_mar.txt
```

### Step 3: Update File Timestamp with `touch`
```bash
# touch on an existing file updates its modification timestamp
touch myfile.txt
ls -la myfile.txt
# The timestamp is now updated to now
```

### Step 4: Write Content to a File
```bash
# Use echo and redirection to write text
echo "Hello, Linux World!" > myfile.txt
echo "This is line 2." >> myfile.txt
echo "And this is line 3." >> myfile.txt
```

### Step 5: View File Content with `cat`
`cat` prints the entire file to the terminal — best for short files.

```bash
cat myfile.txt
# Output:
# Hello, Linux World!
# This is line 2.
# And this is line 3.

# Show line numbers
cat -n myfile.txt
# Output:
#      1  Hello, Linux World!
#      2  This is line 2.
#      3  And this is line 3.
```

### Step 6: Create a Larger File for Paging Practice
```bash
# Generate 100 lines
seq 1 100 | awk '{print "Line " $1 ": The quick brown fox jumps over the lazy dog."}' > bigfile.txt
wc -l bigfile.txt
# Output: 100 bigfile.txt
```

### Step 7: View with `less` (Best for Large Files)
```bash
less bigfile.txt
# Navigation inside less:
# Arrow keys: scroll line by line
# Space / PgDn: next page
# b / PgUp: previous page
# /text: search forward
# n: next search match
# G: go to end
# q: quit
```

### Step 8: View with `more` (Simpler Pager)
```bash
more bigfile.txt
# Space: next page
# Enter: next line
# q: quit
# less is generally preferred over more
```

### Step 9: View the First Lines with `head`
```bash
# Default: first 10 lines
head bigfile.txt
# Output: Line 1 through Line 10

# Specify number of lines
head -n 5 bigfile.txt
# Output: Line 1 through Line 5

# First 20 bytes
head -c 20 bigfile.txt
```

### Step 10: View the Last Lines with `tail`
```bash
# Default: last 10 lines
tail bigfile.txt
# Output: Line 91 through Line 100

# Specify number of lines
tail -n 5 bigfile.txt
# Output: Line 96 through Line 100

# Follow a file in real time (great for logs!)
tail -f /var/log/syslog
# Press Ctrl+C to stop following
```

### Step 11: Concatenate Multiple Files with `cat`
```bash
echo "Part 1" > part1.txt
echo "Part 2" > part2.txt
echo "Part 3" > part3.txt

cat part1.txt part2.txt part3.txt
# Output:
# Part 1
# Part 2
# Part 3

# Combine into one file
cat part1.txt part2.txt part3.txt > combined.txt
cat combined.txt
```

### Step 12: View File Metadata
```bash
# Count lines, words, characters
wc myfile.txt
# Output: 3  12  58 myfile.txt
# (lines words bytes filename)

wc -l bigfile.txt   # lines only
wc -w myfile.txt    # words only
wc -c myfile.txt    # bytes only
```

## ✅ Verification
```bash
# Create a file, write content, view it with different tools
echo -e "Alpha\nBeta\nGamma\nDelta\nEpsilon" > /tmp/verify.txt

head -n 3 /tmp/verify.txt
# Output: Alpha, Beta, Gamma

tail -n 2 /tmp/verify.txt
# Output: Delta, Epsilon

wc -l /tmp/verify.txt
# Output: 5 /tmp/verify.txt

rm /tmp/verify.txt
```

## 📝 Summary
- `touch` creates empty files or updates timestamps; supports brace expansion for bulk creation
- `cat` displays entire files — use it for short files; `-n` adds line numbers
- `less` is the preferred pager for large files — fully navigable and searchable
- `head -n N` shows the first N lines; `tail -n N` shows the last N lines
- `tail -f` follows a file live — essential for watching log files in real time
