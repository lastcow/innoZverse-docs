# Text Processing (grep, awk, sed)

## grep — Search Text

```bash
grep "error" /var/log/syslog            # Find lines with "error"
grep -i "error" file.txt                # Case-insensitive
grep -r "TODO" /home/alice/projects/    # Recursive search
grep -n "error" file.txt                # Show line numbers
grep -v "debug" app.log                 # Invert — exclude matches
grep -c "error" app.log                 # Count matching lines
grep -E "error|warn|critical" app.log   # Extended regex (multiple patterns)

# Practical: find failed SSH logins
grep "Failed password" /var/log/auth.log | tail -20
```

## awk — Column-Based Processing

```bash
# Print specific columns (space-separated)
awk '{print $1, $3}' file.txt           # Print col 1 and 3
awk -F: '{print $1}' /etc/passwd        # Use : as delimiter, print usernames
awk '{sum += $1} END {print sum}' nums.txt  # Sum a column

# Practical: top 10 IPs from access log
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

## sed — Stream Editor

```bash
sed 's/old/new/' file.txt               # Replace first occurrence per line
sed 's/old/new/g' file.txt              # Replace all occurrences
sed -i 's/old/new/g' file.txt           # Edit file in-place
sed '/pattern/d' file.txt              # Delete lines matching pattern
sed -n '10,20p' file.txt               # Print lines 10-20
sed 's/^/>> /' file.txt               # Add prefix to each line
```

## Combining Tools with Pipes

```bash
# Find all unique error types in logs, sorted by frequency
grep "ERROR" app.log | awk '{print $5}' | sort | uniq -c | sort -rn

# Find processes using the most memory
ps aux | sort -k4 -rn | head -10

# Extract email addresses from a file
grep -Eo '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' file.txt
```

---

*Next: [Pipes & Redirection →](pipes-redirection.md)*
