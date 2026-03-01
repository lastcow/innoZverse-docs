# Pipes & Redirection

## Output Redirection

```bash
command > file.txt          # Write output to file (overwrite)
command >> file.txt         # Append output to file
command 2> errors.txt       # Redirect stderr to file
command 2>&1 > all.txt      # Redirect both stdout and stderr
command > /dev/null         # Discard output
```

## Input Redirection

```bash
command < file.txt          # Read input from file
mysql -u root -p db < dump.sql  # Import SQL from file
```

## Pipes — Chain Commands

```bash
command1 | command2         # Output of 1 becomes input of 2

# Examples
ls -la | grep ".txt"        # List only .txt files
cat /etc/passwd | wc -l    # Count users
ps aux | grep nginx         # Find nginx processes
history | grep "git"        # Find git commands in history
```

## tee — Split Output

```bash
# Write to file AND display on screen
command | tee output.txt
command | tee -a output.txt     # Append instead of overwrite
```

## Practical Examples

```bash
# Find top 5 largest files
du -sh /* 2>/dev/null | sort -rh | head -5

# Count errors per hour in logs
grep "ERROR" app.log | awk '{print $1, $2}' | cut -d: -f1 | uniq -c

# Monitor a log file and filter
tail -f /var/log/nginx/access.log | grep --line-buffered "404"
```

---

*Next: [Shell Scripting Basics →](shell-scripting-basics.md)*
