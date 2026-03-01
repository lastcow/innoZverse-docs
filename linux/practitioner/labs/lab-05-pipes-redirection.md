# Lab 5: Pipes and Advanced Redirection

## 🎯 Objective
Build complex command pipelines, use `tee` to split output, and leverage process substitution for advanced data flow patterns.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Foundations Lab 19 (I/O redirection basics)
- Basic knowledge of grep, sort, awk

## 🔬 Lab Instructions

### Step 1: Review the Pipe Operator
```bash
# | connects stdout of left command to stdin of right command
cat /etc/passwd | grep bash | cut -d: -f1
# cat → grep → cut → terminal

# Equivalent (more efficient):
grep bash /etc/passwd | cut -d: -f1
```

### Step 2: Build Multi-Stage Pipelines
```bash
# Top 5 CPU-consuming processes
ps aux | sort -k3 -rn | head -6 | tail -5

# Count unique IPs in auth.log
grep "Failed" /var/log/auth.log 2>/dev/null | \
  grep -oP "\b\d+\.\d+\.\d+\.\d+\b" | \
  sort | uniq -c | sort -rn | head -5

# Find largest files in /var/log
find /var/log -type f -printf "%s %p\n" 2>/dev/null | \
  sort -rn | head -10
```

### Step 3: The tee Command — Split Output
```bash
# tee sends output to BOTH a file and stdout
echo "important data" | tee /tmp/tee_output.txt
# Prints to screen AND saves to file
cat /tmp/tee_output.txt
# Output: important data

# Append mode with -a
echo "more data" | tee -a /tmp/tee_output.txt

# tee in the middle of a pipeline
ls /etc | tee /tmp/etc_list.txt | wc -l
# tee saves the list; wc -l counts the items
cat /tmp/etc_list.txt | head -5
```

### Step 4: tee to Multiple Files
```bash
echo "data" | tee /tmp/file1.txt /tmp/file2.txt /tmp/file3.txt
cat /tmp/file1.txt /tmp/file2.txt /tmp/file3.txt
# All three files have "data"
```

### Step 5: Process Substitution with <()
```bash
# <(command) treats command output as a file
# Compare two command outputs
diff <(ls /etc | sort) <(ls /usr/share | sort) | head -10

# Paste two command outputs side by side
paste <(echo -e "a\nb\nc") <(echo -e "1\n2\n3")
# Output:
# a    1
# b    2
# c    3

# Sort and diff
diff <(sort /etc/passwd) <(sort /etc/group) | head -5
```

### Step 6: Process Substitution with >()
```bash
# >() redirects to a command's stdin
# Duplicate pipeline to two commands
ls /etc | tee >(grep conf > /tmp/conf_files.txt) >(grep log > /tmp/log_files.txt) > /dev/null
cat /tmp/conf_files.txt | head -5
cat /tmp/log_files.txt | head -5
```

### Step 7: Named Pipes (FIFOs)
```bash
# Create a named pipe
mkfifo /tmp/mypipe

# In one terminal: write to the pipe
echo "data through pipe" > /tmp/mypipe &

# Read from the pipe
cat /tmp/mypipe
# Output: data through pipe

rm /tmp/mypipe
```

### Step 8: xargs — Build Commands from Input
```bash
# xargs takes stdin and passes it as arguments
echo "file1 file2 file3" | xargs touch
ls file1 file2 file3
rm file1 file2 file3

# One argument per line with -I {}
find /tmp -name "*.txt" -print0 | xargs -0 ls -la

# Parallel execution with -P
find /var/log -name "*.log" 2>/dev/null | xargs -P 4 -I {} wc -l {} 2>/dev/null | head -5
```

### Step 9: Here String
```bash
# <<< passes a string as stdin to a command
wc -w <<< "count these words please"
# Output: 4

# Useful for variable processing
myvar="hello world"
wc -c <<< "$myvar"
```

### Step 10: Subshell and Command Grouping
```bash
# () runs commands in a subshell
(cd /tmp && ls && pwd)
pwd  # Still in original directory

# {} groups commands in current shell
{ echo "line1"; echo "line2"; echo "line3"; } > /tmp/grouped.txt
cat /tmp/grouped.txt

# Redirect grouped output
{ df -h; echo "---"; free -h; } | tee /tmp/system_report.txt
```

### Step 11: Combining Redirection and Pipes
```bash
# Save stderr to file while passing stdout through pipe
ls /etc /nonexistent 2>/tmp/errors.txt | wc -l
cat /tmp/errors.txt

# Swap stdout and stderr
ls /nonexistent 3>&2 2>&1 1>&3

# Count lines while also displaying them
cat /etc/passwd | tee /dev/stderr | wc -l 2>&1 | tail -1
```

### Step 12: Practical Pipeline — System Health Snapshot
```bash
{
  echo "=== $(date) ==="
  echo ""
  echo "Top 5 CPU processes:"
  ps aux --sort=-%cpu | awk 'NR<=6 && NR>1 {printf "  %-20s %.1f%%\n", $11, $3}'
  echo ""
  echo "Disk Usage:"
  df -h | grep -v tmpfs | awk 'NR>1 {printf "  %-20s %s\n", $6, $5}'
} | tee /tmp/health_snapshot.txt

cat /tmp/health_snapshot.txt

# Clean up
rm -f /tmp/tee_output.txt /tmp/etc_list.txt /tmp/file*.txt
rm -f /tmp/conf_files.txt /tmp/log_files.txt /tmp/grouped.txt
rm -f /tmp/errors.txt /tmp/system_report.txt /tmp/health_snapshot.txt
```

## ✅ Verification
```bash
# Verify tee splits output correctly
echo "test" | tee /tmp/tee_verify.txt | wc -c
# Output: 5 (goes to stdout AND file)
cat /tmp/tee_verify.txt
# Output: test

# Verify process substitution
diff <(echo "same") <(echo "same")
# Output: (nothing — files are identical)

diff <(echo "left") <(echo "right")
# Output: shows difference

rm /tmp/tee_verify.txt
```

## 📝 Summary
- `|` connects stdout of one command to stdin of the next — chain as many as needed
- `tee` splits output to both stdout and a file simultaneously; `-a` for append mode
- `<(cmd)` process substitution treats command output as a file — perfect for `diff` and `paste`
- `xargs` builds command lines from stdin — use `-P` for parallel execution
- `{}` groups commands and redirects their combined output; `()` does the same in a subshell
- Complex pipelines are Linux's superpower — combine simple tools into powerful workflows

