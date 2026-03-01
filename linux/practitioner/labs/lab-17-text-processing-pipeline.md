# Lab 17: Text Processing Pipeline

## 🎯 Objective
Build real-world text processing pipelines to parse /etc/passwd, extract users sorted by UID, and format output with awk.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Labs 2 (awk), 3 (sed), 4 (cut/sort/uniq)

## 🔬 Lab Instructions

### Step 1: Understand the Data Source

```bash
# /etc/passwd structure: user:x:UID:GID:comment:home:shell
head -5 /etc/passwd
wc -l /etc/passwd
```

```bash
# Quick summary
echo "Total accounts: $(wc -l < /etc/passwd)"
echo "Bash users:     $(grep -c '/bin/bash$' /etc/passwd)"
echo "Nologin users:  $(grep -c 'nologin' /etc/passwd)"
echo "System users:   $(awk -F: '$3 < 1000' /etc/passwd | wc -l)"
echo "Regular users:  $(awk -F: '$3 >= 1000' /etc/passwd | wc -l)"
```

### Step 2: Extract Users Sorted by UID

```bash
# Extract username and UID, sort numerically
cut -d: -f1,3 /etc/passwd | sort -t: -k2 -n | head -10
```

```bash
# Format with awk
awk -F: '{ printf "UID: %6d  User: %-20s\n", $3, $1 }' /etc/passwd | sort -n | head -10
```

**Expected output:**
```
UID:      0  User: root
UID:      1  User: daemon
UID:      2  User: bin
...
```

### Step 3: Filter and Transform

```bash
# Only regular users (UID >= 1000)
awk -F: '$3 >= 1000 { print $1, $3, $6, $7 }' /etc/passwd
```

```bash
# Only users with bash shell
awk -F: '$7 ~ /bash$/ { printf "%-20s UID=%-6d Home=%s\n", $1, $3, $6 }' /etc/passwd
```

### Step 4: Generate a User Report

```bash
cat > /tmp/user-report.sh << 'EOF'
#!/bin/bash
echo "========================================"
echo "         USER ACCOUNT REPORT"
echo "========================================"
echo ""
echo "--- All Accounts by UID ---"
awk -F: '{ printf "  %-20s UID=%-6d Shell=%s\n", $1, $3, $7 }' /etc/passwd | sort -k2 -n -t=

echo ""
echo "--- Shell Distribution ---"
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn | awk '{ printf "  %3d  %s\n", $1, $2 }'

echo ""
echo "--- Summary ---"
echo "  Total accounts: $(wc -l < /etc/passwd)"
echo "  Bash users:     $(awk -F: '$7 ~ /bash/' /etc/passwd | wc -l)"
echo "  System (UID<1000):  $(awk -F: '$3 < 1000' /etc/passwd | wc -l)"
echo "  Regular (UID>=1000): $(awk -F: '$3 >= 1000' /etc/passwd | wc -l)"
EOF

bash /tmp/user-report.sh
```

### Step 5: Multi-File Pipeline

```bash
# Join /etc/passwd and /etc/shadow info (readable fields only)
# passwd field 1=user, shadow field 1=user, field 2=password hash (not visible)
join -t: -1 1 -2 1 \
    <(sort -t: -k1 /etc/passwd) \
    <(sort -t: -k1 /etc/group) \
    2>/dev/null | head -5 | cut -d: -f1,3,4 | head -5 || echo "join output shown above"
```

```bash
# More practical: combine passwd with group membership
awk -F: '{ print $1, $3 }' /etc/passwd | while read user uid; do
    groups=$(grep -w "$user" /etc/group 2>/dev/null | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    printf "%-20s UID=%-6d Groups=%s\n" "$user" "$uid" "${groups:-none}"
done | head -10
```

### Step 6: Data Transformation Pipeline

```bash
# Transform /etc/passwd into a different format (CSV)
echo "username,uid,gid,home,shell"
awk -F: '{ printf "%s,%s,%s,%s,%s\n", $1, $3, $4, $6, $7 }' /etc/passwd | head -10
```

```bash
# Create an HTML table (plain text version)
echo "<table>"
echo "  <tr><th>User</th><th>UID</th><th>Shell</th></tr>"
awk -F: '{ printf "  <tr><td>%s</td><td>%s</td><td>%s</td></tr>\n", $1, $3, $7 }' /etc/passwd | head -5
echo "</table>"
```

### Step 7: Validate Data Integrity

```bash
# Check for duplicate UIDs in /etc/passwd
echo "=== Duplicate UIDs ==="
cut -d: -f3 /etc/passwd | sort -n | uniq -d | while read uid; do
    grep ":${uid}:" /etc/passwd | cut -d: -f1,3
done
echo "(none = OK)"

# Check for accounts with empty passwords
echo "=== Accounts with no password field ==="
awk -F: '$2 == "" { print $1 }' /etc/passwd
echo "(none = OK)"
```

## ✅ Verification

```bash
echo "=== Pipeline test: users sorted by UID ==="
awk -F: '{ print $3, $1 }' /etc/passwd | sort -n | head -5

echo "=== Shell count ==="
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn | head -3

rm /tmp/user-report.sh 2>/dev/null
echo "Practitioner Lab 17 complete"
```

## 📝 Summary
- `cut -d: -f1,3 /etc/passwd | sort -t: -k2 -n` extracts and sorts by UID
- `awk -F: '$3 >= 1000'` filters to regular users
- `printf "%-20s %5d\n"` formats aligned columns
- `uniq -c | sort -rn` counts and ranks occurrences
- Build reports by composing `cut`, `sort`, `uniq`, `awk` in pipelines
- Always test each step of the pipeline independently before combining
