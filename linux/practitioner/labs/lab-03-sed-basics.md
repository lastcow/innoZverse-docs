# Lab 3: sed Basics

## 🎯 Objective
Use sed to transform text files: substitute patterns, delete lines, print specific ranges, and make in-place edits.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Foundations Lab 14: grep Basics

## 🔬 Lab Instructions

### Step 1: Set Up Test Files

```bash
cat > /tmp/sed-test.txt << 'EOF'
server_host=localhost
server_port=8080
database_host=db.example.com
database_port=5432
debug=true
log_level=debug
max_workers=4
environment=development
EOF
```

### Step 2: Substitute with s/old/new/

```bash
# Basic substitution (first occurrence per line)
sed 's/localhost/production-server/' /tmp/sed-test.txt
```

```bash
# Global substitution (all occurrences)
sed 's/host/HOST/g' /tmp/sed-test.txt
```

```bash
# Case-insensitive (GNU sed)
sed 's/debug/DEBUG/gi' /tmp/sed-test.txt
```

```bash
# Use different delimiter (useful when pattern contains /)
sed 's|=development|=production|' /tmp/sed-test.txt
```

### Step 3: In-Place Editing with -i

```bash
cp /tmp/sed-test.txt /tmp/sed-inplace.txt

# -i.bak creates a backup before editing
sed -i.bak 's/development/production/' /tmp/sed-inplace.txt

echo "=== Modified file ===" && cat /tmp/sed-inplace.txt | grep environment
echo "=== Backup file ===" && cat /tmp/sed-inplace.bak | grep environment
```

### Step 4: Delete Lines with d

```bash
# Delete lines matching a pattern
sed '/debug/d' /tmp/sed-test.txt
```

```bash
# Delete lines by line number
sed '3d' /tmp/sed-test.txt
```

```bash
# Delete a range of lines
sed '2,4d' /tmp/sed-test.txt
```

```bash
# Delete blank lines
printf "line1\n\nline2\n\nline3\n" | sed '/^$/d'
```

### Step 5: Print with -n and p

```bash
# -n suppresses default output; p prints explicitly
sed -n '2,4p' /tmp/sed-test.txt
```

**Expected output:**
```
server_port=8080
database_host=db.example.com
database_port=5432
```

```bash
# Print lines matching a pattern
sed -n '/database/p' /tmp/sed-test.txt
```

```bash
# Print line numbers with =
sed -n '/debug/=' /tmp/sed-test.txt
```

### Step 6: Address Ranges

```bash
# Apply substitution only to lines 1-3
sed '1,3s/=/-/' /tmp/sed-test.txt
```

```bash
# Apply substitution from pattern to end
sed '/database/,$s/host/HOST/' /tmp/sed-test.txt
```

```bash
# Apply substitution only on lines matching pattern
sed '/server/s/=/ = /' /tmp/sed-test.txt
```

### Step 7: Multiple Commands with -e

```bash
sed -e 's/localhost/webserver/' -e 's/development/production/' /tmp/sed-test.txt
```

```bash
# Or use semicolons
sed 's/debug/DISABLED/;s/development/production/' /tmp/sed-test.txt
```

### Step 8: Insert and Append Lines

```bash
# Insert a line BEFORE line 1
sed '1i\# Configuration File' /tmp/sed-test.txt | head -5
```

```bash
# Append a line AFTER last line
sed '$a\# End of config' /tmp/sed-test.txt | tail -3
```

```bash
# Append after matching line
sed '/max_workers/a\min_workers=1' /tmp/sed-test.txt | grep -A1 workers
```

## ✅ Verification

```bash
echo "=== Substitute test ===" && sed 's/localhost/prod-host/' /tmp/sed-test.txt | grep server_host
echo "=== Delete test ===" && sed '/debug/d' /tmp/sed-test.txt | grep -c debug
echo "=== Print range test ===" && sed -n '1,3p' /tmp/sed-test.txt | wc -l

rm /tmp/sed-test.txt /tmp/sed-inplace.txt /tmp/sed-inplace.bak 2>/dev/null
echo "Practitioner Lab 3 complete"
```

## 📝 Summary
- `sed 's/old/new/'` substitutes first match; `s/old/new/g` substitutes all
- `-i` edits in-place; `-i.bak` creates a backup first
- `sed '/pattern/d'` deletes matching lines; `sed 'Nd'` deletes line N
- `sed -n 'Np'` prints only line N; `-n '/pattern/p'` prints matching lines
- Address ranges: `sed '2,5s/old/new/'` applies only to lines 2-5
- `-e` allows multiple commands: `sed -e 'cmd1' -e 'cmd2'`
