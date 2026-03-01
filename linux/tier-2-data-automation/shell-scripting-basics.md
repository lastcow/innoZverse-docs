# Shell Scripting Basics

## Your First Script

```bash
#!/bin/bash
# Description: My first shell script
# Usage: ./hello.sh [name]

NAME=${1:-"World"}  # Use argument, or default to "World"
echo "Hello, $NAME!"
echo "Today: $(date +%Y-%m-%d)"
echo "Uptime: $(uptime -p)"
```

```bash
chmod +x hello.sh
./hello.sh
./hello.sh Alice
```

## Variables

```bash
# Assignment (no spaces around =)
NAME="Alice"
COUNT=42
TODAY=$(date +%Y-%m-%d)     # Command substitution

# Usage
echo "$NAME"
echo "Count is: ${COUNT}"
echo "Files: $(ls | wc -l)"
```

## Conditionals

```bash
# String comparison
if [ "$NAME" == "Alice" ]; then
    echo "Hello, Alice!"
elif [ "$NAME" == "Bob" ]; then
    echo "Hey Bob!"
else
    echo "Who are you?"
fi

# Number comparison
if [ "$COUNT" -gt 10 ]; then
    echo "More than 10"
fi

# File checks
[ -f file.txt ] && echo "File exists"
[ -d /tmp ]    && echo "Directory exists"
[ -x script.sh ] && echo "Script is executable"
```

## Loops

```bash
# For loop
for i in 1 2 3 4 5; do
    echo "Item: $i"
done

# For loop over files
for FILE in *.log; do
    echo "Processing: $FILE"
    gzip "$FILE"
done

# While loop
COUNT=0
while [ $COUNT -lt 5 ]; do
    echo "Count: $COUNT"
    ((COUNT++))
done
```

## Functions

```bash
backup_file() {
    local FILE=$1
    local DEST="/backup/$(date +%Y-%m-%d)/"
    mkdir -p "$DEST"
    cp "$FILE" "$DEST"
    echo "Backed up: $FILE → $DEST"
}

backup_file "/etc/nginx/nginx.conf"
```

## Practical Script: System Health Check

```bash
#!/bin/bash

echo "=== System Health Report ==="
echo "Date: $(date)"
echo "Uptime: $(uptime -p)"
echo ""
echo "--- Disk Usage ---"
df -h | grep -v tmpfs
echo ""
echo "--- Memory ---"
free -h
echo ""
echo "--- Top Processes ---"
ps aux --sort=-%cpu | head -6
```

---

*Next: [Cron Jobs & Scheduling →](cron-jobs-scheduling.md)*
