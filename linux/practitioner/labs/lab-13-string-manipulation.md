# Lab 13: String Manipulation in Bash

## 🎯 Objective
Master Bash string operations: substring extraction, replacement, length, case conversion, and pattern matching.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Lab 6 (Shell Variables)

## 🔬 Lab Instructions

### Step 1: String Length
```bash
name="Hello, World!"
echo ${#name}
# 13

path="/usr/local/bin/script.sh"
echo "Path length: ${#path}"
# Path length: 26
```

### Step 2: Substring Extraction
```bash
# ${var:offset:length}
str="Ubuntu 22.04 LTS"
echo ${str:0:6}    # Ubuntu
echo ${str:7:5}    # 22.04
echo ${str: -3}    # LTS (negative = from end)
echo ${str:7}      # 22.04 LTS (to end)
```

### Step 3: Remove Prefix (# and ##)
```bash
path="/home/ubuntu/docs/report.txt"
echo ${path#/}          # home/ubuntu/docs/report.txt  (remove shortest match)
echo ${path##*/}        # report.txt  (remove longest match up to last /)

filename="report.tar.gz"
echo ${filename#*.}     # tar.gz
echo ${filename##*.}    # gz
```

### Step 4: Remove Suffix (% and %%)
```bash
filename="report.tar.gz"
echo ${filename%.*}     # report.tar
echo ${filename%%.*}    # report

url="https://example.com/page"
echo ${url%/*}          # https://example.com
```

### Step 5: String Replacement
```bash
sentence="the cat sat on the mat"
echo ${sentence/cat/dog}        # the dog sat on the mat  (first match)
echo ${sentence//at/AT}         # the cAT sAT on the mAT  (all matches)

path="/home/ubuntu/file.txt"
echo ${path/ubuntu/alice}       # /home/alice/file.txt
```

### Step 6: Case Conversion (Bash 4+)
```bash
str="Hello World"
echo ${str,,}    # hello world  (all lowercase)
echo ${str^^}    # HELLO WORLD  (all uppercase)
echo ${str^}     # Hello world  (first char uppercase)

# Practical: normalize input
answer="YES"
answer=${answer,,}   # normalize to lowercase
if [[ "$answer" == "yes" ]]; then echo "Confirmed"; fi
# Confirmed
```

### Step 7: Check if String Contains Substring
```bash
haystack="Ubuntu Linux 22.04"
needle="Linux"

if [[ "$haystack" == *"$needle"* ]]; then
    echo "Found: $needle"
else
    echo "Not found"
fi
# Found: Linux
```

### Step 8: Split String into Parts
```bash
# Using IFS to split
csv="apple,banana,cherry"
IFS=',' read -ra fruits <<< "$csv"
echo ${fruits[0]}   # apple
echo ${fruits[1]}   # banana
echo ${fruits[2]}   # cherry
echo "Count: ${#fruits[@]}"   # Count: 3
```

### Step 9: Trim Whitespace
```bash
str="   hello world   "
# Trim using sed
trimmed=$(echo "$str" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
echo "'$trimmed'"
# 'hello world'

# Or using parameter expansion
trimmed="${str#"${str%%[![:space:]]*}"}"
trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
echo "'$trimmed'"
# 'hello world'
```

### Step 10: Practical Script — Filename Parser
```bash
cat > ~/parse_filename.sh << 'EOF'
#!/bin/bash
filepath="$1"
filename="${filepath##*/}"       # base name
dirpart="${filepath%/*}"         # directory
ext="${filename##*.}"            # extension
base="${filename%.*}"            # name without ext

echo "Full path : $filepath"
echo "Directory : $dirpart"
echo "Filename  : $filename"
echo "Basename  : $base"
echo "Extension : $ext"
EOF
chmod +x ~/parse_filename.sh
~/parse_filename.sh /home/ubuntu/reports/sales_2026.csv
# Full path : /home/ubuntu/reports/sales_2026.csv
# Directory : /home/ubuntu/reports
# Filename  : sales_2026.csv
# Basename  : sales_2026
# Extension : csv
```

## ✅ Verification
```bash
str="Linux Rocks 2026"
echo ${#str}              # 17
echo ${str^^}             # LINUX ROCKS 2026
echo ${str/Rocks/Rules}   # Linux Rules 2026
echo ${str: -4}           # 2026
```

## 📝 Summary
- `${#var}` returns string length
- `${var:offset:length}` extracts substrings; negative offset counts from end
- `${var#pattern}` / `${var##pattern}` strips prefix (shortest/longest)
- `${var%pattern}` / `${var%%pattern}` strips suffix (shortest/longest)
- `${var/old/new}` replaces first; `${var//old/new}` replaces all
- `${var,,}` lowercases; `${var^^}` uppercases (Bash 4+)
