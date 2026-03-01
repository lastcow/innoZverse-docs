# Lab 3: sed Basics

## 🎯 Objective
Use `sed` (stream editor) to substitute text, delete lines, insert text, and edit files in-place on Ubuntu 22.04.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Lab 1 (grep advanced)
- Basic understanding of regular expressions

## 🔬 Lab Instructions

### Step 1: Basic sed Syntax
```bash
# sed 'command' file
# Commands: s (substitute), d (delete), i (insert), a (append), p (print)
echo "Hello World" | sed 's/World/Linux/'
# Output: Hello Linux
```

### Step 2: Substitution with s Command
```bash
# s/pattern/replacement/flags
# Default: replaces first occurrence per line
echo "cat cat cat" | sed 's/cat/dog/'
# Output: dog cat cat

# g flag: replace ALL occurrences
echo "cat cat cat" | sed 's/cat/dog/g'
# Output: dog dog dog

# i flag: case-insensitive (GNU sed)
echo "Cat CAT cat" | sed 's/cat/dog/gi'
# Output: dog dog dog
```

### Step 3: Create a Test File
```bash
cat > /tmp/sed_test.txt << 'EOF'
The quick brown fox
jumps over the lazy dog
The fox is clever
The dog is lazy
ERROR: something went wrong
INFO: all systems normal
EOF
```

### Step 4: Substitute in a File
```bash
# View original
cat /tmp/sed_test.txt

# Replace fox with cat (stdout only, file unchanged)
sed 's/fox/cat/g' /tmp/sed_test.txt

# Verify file is unchanged
cat /tmp/sed_test.txt
```

### Step 5: In-Place Editing with -i
```bash
# -i edits the file directly
cp /tmp/sed_test.txt /tmp/sed_backup.txt
sed -i 's/dog/wolf/g' /tmp/sed_test.txt
cat /tmp/sed_test.txt
# All "dog" are now "wolf"

# -i.bak creates a backup before editing
sed -i.bak 's/wolf/dog/g' /tmp/sed_test.txt
ls /tmp/sed_test.txt*
# Shows sed_test.txt and sed_test.txt.bak
```

### Step 6: Delete Lines with d
```bash
# Delete lines matching a pattern
sed '/ERROR/d' /tmp/sed_test.txt
# Output: all lines except the ERROR line

# Delete by line number
sed '1d' /tmp/sed_test.txt
# Deletes line 1

# Delete a range of lines
sed '2,4d' /tmp/sed_test.txt
# Deletes lines 2 through 4

# Delete empty lines
sed '/^$/d' /tmp/sed_test.txt
```

### Step 7: Print Specific Lines with p
```bash
# -n suppresses default output; p prints matching lines
sed -n '/ERROR/p' /tmp/sed_test.txt
# Prints only lines with ERROR (like grep)

# Print line numbers 2-4
sed -n '2,4p' /tmp/sed_test.txt

# Print last line
sed -n '$p' /tmp/sed_test.txt
```

### Step 8: Insert and Append Lines
```bash
# i inserts BEFORE the matched line
sed '/ERROR/i --- ALERT ---' /tmp/sed_test.txt

# a appends AFTER the matched line
sed '/ERROR/a --- Check logs ---' /tmp/sed_test.txt

# Insert before line 1 (add a header)
sed '1i # Log File Header' /tmp/sed_test.txt
```

### Step 9: Address Ranges
```bash
# Apply command only to lines 1-3
sed '1,3s/The/A/g' /tmp/sed_test.txt

# Apply from pattern to pattern
sed '/fox/,/clever/s/The/A/g' /tmp/sed_test.txt

# Apply to all lines EXCEPT line 1
sed '1!s/The/A/g' /tmp/sed_test.txt
```

### Step 10: Multiple Commands with -e or Semicolon
```bash
# Multiple substitutions in one command
sed 's/fox/cat/g; s/dog/wolf/g' /tmp/sed_test.txt

# Using -e for each command
sed -e 's/fox/cat/g' -e 's/dog/wolf/g' /tmp/sed_test.txt

# Multiline using a script file
cat > /tmp/sed_script.sed << 'EOF'
s/fox/cat/g
s/dog/wolf/g
/ERROR/d
EOF
sed -f /tmp/sed_script.sed /tmp/sed_test.txt
```

### Step 11: Practical Example — Edit Config File
```bash
cat > /tmp/app.conf << 'EOF'
debug=false
port=8080
host=localhost
max_connections=100
EOF

# Change port
sed -i 's/^port=.*/port=9090/' /tmp/app.conf

# Enable debug
sed -i 's/^debug=false/debug=true/' /tmp/app.conf

cat /tmp/app.conf
# Verify changes
```

### Step 12: Clean Up
```bash
rm -f /tmp/sed_test.txt /tmp/sed_test.txt.bak /tmp/sed_backup.txt
rm -f /tmp/sed_script.sed /tmp/app.conf
```

## ✅ Verification
```bash
echo "Hello World 2026" | sed 's/[0-9]\{4\}/YEAR/'
# Output: Hello World YEAR

echo -e "keep\ndelete me\nkeep" | sed '/delete/d'
# Output: keep (x2)

echo "aaa bbb ccc" | sed 's/\b[a-z]*/(&)/g'
# Output: (aaa) (bbb) (ccc)
```

## 📝 Summary
- `sed 's/pattern/replacement/g'` substitutes text; `g` replaces all occurrences per line
- `-i` edits files in-place; `-i.bak` creates a backup first
- `d` deletes matching lines; `p` with `-n` prints only matching lines
- `i` inserts before, `a` appends after matched lines
- Use `;` or multiple `-e` flags for multiple commands in one sed call
- Address ranges (`1,5`) or pattern ranges (`/start/,/end/`) restrict which lines are processed

