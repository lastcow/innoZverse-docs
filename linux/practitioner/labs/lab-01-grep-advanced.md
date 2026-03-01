# Lab 1: Advanced grep

## 🎯 Objective
Master advanced grep features: extended regex (-E), context lines (-A, -B, -C), multi-file search, and recursive directory search.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Foundations Lab 14: grep Basics
- Basic understanding of regular expressions

## 🔬 Lab Instructions

### Step 1: Set Up Test Files

```bash
mkdir -p /tmp/grep-adv

cat > /tmp/grep-adv/app.log << 'EOF'
2026-01-15 10:00:01 INFO  [web] Server started
2026-01-15 10:01:30 ERROR [web] Connection refused: port 8080
2026-01-15 10:01:31 ERROR [db]  Database timeout after 30s
2026-01-15 10:02:00 WARN  [web] Retry attempt 1
2026-01-15 10:02:05 WARN  [web] Retry attempt 2
2026-01-15 10:02:10 INFO  [db]  Connection restored
2026-01-15 10:03:00 INFO  [web] Request: GET /api/users 200
2026-01-15 10:03:01 INFO  [web] Request: POST /api/data 201
2026-01-15 10:04:00 ERROR [web] Request: DELETE /api/admin 403
2026-01-15 10:05:00 INFO  [web] Server shutting down
EOF

cat > /tmp/grep-adv/config.ini << 'EOF'
[server]
host = 0.0.0.0
port = 8080
workers = 4

[database]
host = db01.internal
port = 5432
name = appdb
user = appuser
EOF
```

### Step 2: Extended Regex with -E

```bash
grep -E "ERROR|WARN" /tmp/grep-adv/app.log
```

```bash
grep -E "[0-9]+" /tmp/grep-adv/app.log | head -5
```

```bash
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" /tmp/grep-adv/config.ini
```

```bash
grep -E "^2026-01-15 10:0[34]" /tmp/grep-adv/app.log
```

### Step 3: Context Lines — Before (-B), After (-A), Context (-C)

```bash
grep -A 2 "ERROR" /tmp/grep-adv/app.log
```

```bash
grep -B 2 "Connection restored" /tmp/grep-adv/app.log
```

```bash
grep -C 1 "WARN" /tmp/grep-adv/app.log
```

### Step 4: Search Multiple Files

```bash
grep "host" /tmp/grep-adv/config.ini /tmp/grep-adv/app.log
```

```bash
grep -i "error" /tmp/grep-adv/*.log
grep -l "ERROR" /tmp/grep-adv/*
grep -c "INFO" /tmp/grep-adv/*.log
```

### Step 5: Recursive Search with -r

```bash
mkdir -p /tmp/grep-adv/subdir
echo "database_url=postgres://user@host/db" > /tmp/grep-adv/subdir/settings.py
echo "redis_host=cache01.internal" >> /tmp/grep-adv/subdir/settings.py

grep -r "host" /tmp/grep-adv/
grep -rni "error" /tmp/grep-adv/
grep -rl "database" /tmp/grep-adv/
```

```bash
grep -r "ubuntu" /etc/apt/ 2>/dev/null | head -5
```

### Step 6: Other Useful grep Options

```bash
# -w: match whole words only
grep -w "port" /tmp/grep-adv/config.ini
```

```bash
# -o: print only the matched part
grep -Eo "[0-9]{4}-[0-9]{2}-[0-9]{2}" /tmp/grep-adv/app.log | head -5
```

**Expected output:**
```
2026-01-15
2026-01-15
...
```

```bash
# -P: Perl-compatible regex
grep -P "\d{2}:\d{2}:\d{2}" /tmp/grep-adv/app.log | head -3
```

### Step 7: Search in /etc

```bash
grep -r "^nameserver" /etc/resolv.conf 2>/dev/null || echo "no resolv.conf"
grep -rn "ubuntu" /etc/apt/sources.list 2>/dev/null | head -5
```

## ✅ Verification

```bash
echo "=== ERROR count ===" && grep -c "ERROR" /tmp/grep-adv/app.log
echo "=== WARN|ERROR lines ===" && grep -cE "ERROR|WARN" /tmp/grep-adv/app.log
echo "=== Context search ===" && grep -C 1 "Connection restored" /tmp/grep-adv/app.log | wc -l
echo "=== Recursive file count ===" && grep -rl "host" /tmp/grep-adv/ | wc -l
rm -r /tmp/grep-adv
echo "Practitioner Lab 1 complete"
```

## 📝 Summary
- `grep -E "pat1|pat2"` uses extended regex for OR matching
- `grep -A N` shows N lines after match; `-B N` before; `-C N` both
- Searching multiple files automatically shows filename prefix
- `grep -r` searches recursively through directory trees
- `grep -o` extracts only the matched portion
- `grep -w` matches whole words; prevents partial matches
