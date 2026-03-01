# Lab 4: cut, sort, and uniq

## 🎯 Objective
Process text columns with `cut`, sort output with `sort`, and find unique/duplicate lines with `uniq` — the essential trio for text data processing.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 14 (grep basics)
- Basic understanding of delimiters and fields

## 🔬 Lab Instructions

### Step 1: The cut Command — Extract Fields
```bash
# -d: delimiter, -f: field number(s)
echo "alice:1000:Engineering:Senior" | cut -d: -f1
# Output: alice

echo "alice:1000:Engineering:Senior" | cut -d: -f1,3
# Output: alice:Engineering

echo "alice:1000:Engineering:Senior" | cut -d: -f2-4
# Output: 1000:Engineering:Senior
```

### Step 2: cut on Real Files
```bash
# Extract usernames from /etc/passwd
cut -d: -f1 /etc/passwd | head -10

# Extract username and shell
cut -d: -f1,7 /etc/passwd | head -10

# Extract by character position
echo "2026-03-01 08:00:00" | cut -c1-10
# Output: 2026-03-01 (date portion)

echo "2026-03-01 08:00:00" | cut -c12-
# Output: 08:00:00 (time portion)
```

### Step 3: Create a Dataset
```bash
cat > /tmp/data.txt << 'EOF'
banana 5 0.99
apple 12 0.50
cherry 3 2.49
apple 8 0.50
banana 2 0.99
date 10 1.50
cherry 7 2.49
apple 4 0.50
EOF
```

### Step 4: Basic sort
```bash
# Alphabetical sort (default)
sort /tmp/data.txt

# Reverse alphabetical
sort -r /tmp/data.txt
```

### Step 5: Numeric Sort with -n
```bash
# Sort by second field (quantity) numerically
sort -k2 -n /tmp/data.txt
# Without -n: "12" < "2" (alphabetical!)

# Sort by price (field 3), descending
sort -k3 -rn /tmp/data.txt
```

### Step 6: Sort with Custom Delimiter
```bash
# Sort /etc/passwd by UID (field 3)
sort -t: -k3 -n /etc/passwd | head -10

# Sort by multiple fields: first by name, then by qty
sort -k1,1 -k2,2n /tmp/data.txt
```

### Step 7: Remove Duplicate Lines with uniq
```bash
# Sort first (uniq only works on ADJACENT duplicates)
sort /tmp/data.txt | uniq

# uniq on unsorted: only adjacent duplicates removed
echo -e "a\nb\na\nc\nb" | uniq
# Output: a b a c b (still has duplicates!)

echo -e "a\nb\na\nc\nb" | sort | uniq
# Output: a b c
```

### Step 8: Count Occurrences with uniq -c
```bash
# Count how many times each fruit appears
cut -f1 -d' ' /tmp/data.txt | sort | uniq -c
# Output:
#   3 apple
#   2 banana
#   2 cherry
#   1 date

# Sort by count descending
cut -f1 -d' ' /tmp/data.txt | sort | uniq -c | sort -rn
```

### Step 9: Show Only Duplicates or Unique Lines
```bash
# Show only lines that appear MORE than once (-d)
cut -f1 -d' ' /tmp/data.txt | sort | uniq -d
# Output: apple banana cherry

# Show only lines that appear EXACTLY once (-u)
cut -f1 -d' ' /tmp/data.txt | sort | uniq -u
# Output: date
```

### Step 10: Practical Pipeline — Top IPs in Log
```bash
# Simulate an access log
cat > /tmp/access.log << 'EOF'
192.168.1.10 GET /index.html 200
10.0.0.5 POST /login 401
192.168.1.10 GET /about.html 200
203.0.113.5 GET /index.html 200
10.0.0.5 POST /login 401
10.0.0.5 POST /login 401
192.168.1.20 GET /index.html 200
192.168.1.10 GET /api/data 200
EOF

# Top IPs by request count
cut -d' ' -f1 /tmp/access.log | sort | uniq -c | sort -rn
```

### Step 11: Sort Versions and Mixed Data
```bash
# Version-aware sort
echo -e "1.10\n1.9\n1.2\n2.0" | sort -V
# Output: 1.2 1.9 1.10 2.0 (correct version order)

# Sort human-readable sizes
du -sh /var/log/* 2>/dev/null | sort -rh | head -5
```

### Step 12: Clean Up
```bash
rm -f /tmp/data.txt /tmp/access.log
```

## ✅ Verification
```bash
# Pipeline: extract, sort, count
echo -e "red\nblue\nred\ngreen\nblue\nred" | sort | uniq -c | sort -rn
# Output:
#   3 red
#   2 blue
#   1 green

cut -d: -f1 /etc/passwd | sort | head -5
# First 5 usernames alphabetically
```

## 📝 Summary
- `cut -d: -f1,3` extracts specific fields using a delimiter
- `sort -n` sorts numerically; `-r` reverses; `-k` specifies the sort key field
- `sort -k1,1 -k2,2n` enables multi-column sorting
- `uniq` removes adjacent duplicates — always sort first for true deduplication
- `uniq -c` counts occurrences; `-d` shows duplicates; `-u` shows unique-only lines
- The `cut | sort | uniq -c | sort -rn` pipeline is a classic frequency analysis pattern

