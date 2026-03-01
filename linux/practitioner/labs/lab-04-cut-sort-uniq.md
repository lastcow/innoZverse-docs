# Lab 4: cut, sort, and uniq

## 🎯 Objective
Extract columns with cut, sort data with multiple keys, and count/deduplicate with uniq.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 19: I/O Redirection Basics

## 🔬 Lab Instructions

### Step 1: Extract Fields with cut

```bash
# -d sets delimiter, -f selects field(s)
cut -d: -f1 /etc/passwd | head -10
```

**Expected output:**
```
root
daemon
bin
...
```

```bash
# Extract multiple fields
cut -d: -f1,7 /etc/passwd | head -10
```

```bash
# Extract a range of fields
cut -d: -f1-4 /etc/passwd | head -5
```

```bash
# Extract by character position
echo "2026-03-01 Sunday" | cut -c1-10
```

**Expected output:**
```
2026-03-01
```

```bash
# Cut from a CSV
cat > /tmp/data.csv << 'EOF'
name,age,city,role
Alice,30,London,engineer
Bob,25,Paris,designer
Carol,35,Berlin,manager
Dave,28,Tokyo,developer
EOF

cut -d, -f1,3 /tmp/data.csv
```

**Expected output:**
```
name,city
Alice,London
Bob,Paris
Carol,Berlin
Dave,Tokyo
```

### Step 2: Sort Lines

```bash
# Default alphabetical sort
cut -d: -f1 /etc/passwd | sort | head -10
```

```bash
# Sort /etc/passwd alphabetically
sort /etc/passwd | head -5
```

```bash
# Sort numerically by UID (field 3)
sort -t: -k3 -n /etc/passwd | head -10
```

**Expected output:**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
```

```bash
# Sort in reverse order
sort -t: -k3 -n -r /etc/passwd | head -5
```

```bash
# Sort CSV by second column (age) numerically
sort -t, -k2 -n /tmp/data.csv
```

### Step 3: Sort Unique and Remove Duplicates

```bash
# -u flag removes duplicates during sort
echo -e "banana\napple\ncherry\napple\nbanana" | sort -u
```

**Expected output:**
```
apple
banana
cherry
```

```bash
# Stable sort preserving order of equal elements
sort -s -t: -k7 /etc/passwd | head -10
```

### Step 4: Count Duplicates with uniq

```bash
# uniq requires sorted input
echo -e "apple\napple\nbanana\napple\ncherry\nbanana" | sort | uniq
```

```bash
# -c: count occurrences
echo -e "apple\napple\nbanana\napple\ncherry\nbanana" | sort | uniq -c
```

**Expected output:**
```
      3 apple
      2 banana
      1 cherry
```

```bash
# Sort by count (most common first)
echo -e "apple\napple\nbanana\napple\ncherry\nbanana" | sort | uniq -c | sort -rn
```

**Expected output:**
```
      3 apple
      2 banana
      1 cherry
```

### Step 5: Combine cut, sort, uniq for Real Analysis

```bash
# Find most common shells
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn
```

**Expected output:**
```
     20 /usr/sbin/nologin
      5 /bin/false
      2 /bin/bash
...
```

```bash
# Find duplicate usernames (should be none in valid /etc/passwd)
cut -d: -f1 /etc/passwd | sort | uniq -d
echo "Duplicate count: $(cut -d: -f1 /etc/passwd | sort | uniq -d | wc -l)"
```

```bash
# Extract unique cities from CSV
cut -d, -f3 /tmp/data.csv | tail -n +2 | sort | uniq -c
```

### Step 6: Advanced sort Keys

```bash
# Sort by multiple keys: first by field 7, then field 1
sort -t: -k7,7 -k1,1 /etc/passwd | head -10
```

```bash
# Sort human-readable sizes (for du output)
du -sh /usr/* 2>/dev/null | sort -rh | head -5
```

```bash
# Sort by last modified time
ls -lt /tmp | head -10
```

## ✅ Verification

```bash
echo "=== Most common shells ===" && cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn | head -5
echo "=== Users sorted by UID ===" && sort -t: -k3 -n /etc/passwd | cut -d: -f1,3 | head -5
echo "=== CSV name column ===" && cut -d, -f1 /tmp/data.csv | sort
rm /tmp/data.csv
echo "Practitioner Lab 4 complete"
```

## 📝 Summary
- `cut -d: -f1` extracts field 1 from colon-delimited input
- `cut -c1-10` extracts characters 1-10 from each line
- `sort -t: -k3 -n` sorts by field 3 numerically
- `sort -r` reverses; `sort -u` removes duplicates; `sort -h` handles human sizes
- `uniq -c` counts occurrences (must have sorted input)
- Combine: `cut | sort | uniq -c | sort -rn` for frequency analysis
