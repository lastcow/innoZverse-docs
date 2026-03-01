# Lab 16: Process Basics

## 🎯 Objective
View running processes with `ps aux` and `top`, understand process states, and manage processes with `kill`.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic terminal skills

## 🔬 Lab Instructions

### Step 1: What Is a Process?
A process is a running instance of a program. Each process has a unique PID (Process ID).

```bash
# Your current shell is a process
echo $$
# Output: 12345 (your bash PID)

# Parent process
echo $PPID
# Output: 12344 (the process that started your shell)
```

### Step 2: List Processes with `ps`
```bash
# Show your own processes
ps
# Output:
#   PID TTY          TIME CMD
# 12345 pts/0    00:00:00 bash
# 12360 pts/0    00:00:00 ps

# Show ALL processes for ALL users
ps aux
# Output:
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# root         1  0.0  0.1 167852 11340 ?        Ss   05:00   0:02 /sbin/init
# ...
```

### Step 3: Understand `ps aux` Columns
```
USER:  Owner of the process
PID:   Process ID (unique identifier)
%CPU:  CPU usage percentage
%MEM:  Memory usage percentage
VSZ:   Virtual memory size (KB) — total allocated
RSS:   Resident Set Size (KB) — actual physical memory
TTY:   Terminal (? = no terminal)
STAT:  Process state
START: When it started
TIME:  Total CPU time consumed
COMMAND: The command being run
```

### Step 4: Understand Process States (STAT column)
```
R:  Running or runnable
S:  Sleeping (waiting for event)
D:  Uninterruptible sleep (usually I/O)
T:  Stopped (paused)
Z:  Zombie (finished but parent hasn't cleaned up)
s:  Session leader
l:  Multi-threaded
+:  In foreground process group
<:  High priority
N:  Low priority
```

```bash
ps aux | grep -v grep | grep "^root" | head -10
```

### Step 5: Search for Specific Processes
```bash
# Find bash processes
ps aux | grep bash

# Find processes by name with pgrep
pgrep bash
# Output: list of PIDs

pgrep -l bash
# Output: PID and name
```

### Step 6: Display a Process Tree
```bash
# Show process hierarchy
ps auxf
# or
pstree
# or
pstree -p  # with PIDs
```

### Step 7: Monitor Processes Interactively with `top`
```bash
top
# Interactive display updating every 3 seconds

# Key shortcuts in top:
# q:         quit
# k:         kill a process (prompts for PID then signal)
# r:         renice (change priority)
# M:         sort by memory usage
# P:         sort by CPU usage (default)
# 1:         toggle per-CPU view
# h:         help
```

### Step 8: Run a Background Process
```bash
# Start a long-running process in the background
sleep 300 &
# Output: [1] 12400
# [1] = job number, 12400 = PID

# List background jobs
jobs
# Output: [1]+  Running   sleep 300 &

# See it in ps
ps aux | grep "sleep 300"
```

### Step 9: Kill a Process
```bash
# Get the PID of the sleep process
ps aux | grep "sleep 300" | grep -v grep

# Kill by PID (sends SIGTERM = graceful shutdown)
kill 12400   # replace with actual PID

# Verify it's gone
ps aux | grep "sleep 300"
# Output: (nothing, or just the grep itself)
```

### Step 10: Different Kill Signals
```bash
# Start another sleep process
sleep 600 &
SLEEP_PID=$!
echo "Sleep PID: $SLEEP_PID"

# SIGTERM (15) — polite request to terminate
kill -15 $SLEEP_PID
# or simply: kill $SLEEP_PID

# If a process ignores SIGTERM, use SIGKILL (9)
sleep 600 &
SLEEP_PID=$!
kill -9 $SLEEP_PID
# SIGKILL cannot be caught or ignored — process is immediately destroyed

# Kill by name with pkill
sleep 300 &
sleep 300 &
pkill sleep
# Kills all processes named "sleep"
```

### Step 11: Bring a Process to Foreground
```bash
sleep 300 &
# [1] 12500

# Bring job 1 to foreground
fg %1
# Now it's running in the foreground

# Send it to background again with Ctrl+Z (suspend) then bg
# Press Ctrl+Z
bg %1
# Process resumes in background
```

### Step 12: View Process Details with `/proc`
```bash
# Each process has a directory in /proc/<PID>
cat /proc/$$/status | head -20
# Shows detailed status of your bash process

cat /proc/$$/cmdline | tr '\0' ' '
# Shows the command that started this process
```

## ✅ Verification
```bash
# Start a process, find it, kill it
sleep 999 &
TEST_PID=$!
echo "Started sleep with PID: $TEST_PID"

ps aux | grep "sleep 999" | grep -v grep
# Should show the process

kill $TEST_PID
sleep 1
ps aux | grep "sleep 999" | grep -v grep
# Should be empty — process is dead
echo "Process killed successfully"
```

## 📝 Summary
- Every running program is a process with a unique PID
- `ps aux` lists all processes; `pgrep name` finds PIDs by name
- `top` gives an interactive real-time view of processes and system resources
- `kill PID` sends SIGTERM (graceful); `kill -9 PID` sends SIGKILL (immediate/forced)
- `&` runs a process in the background; `fg` brings it forward; `jobs` lists background jobs
- Process state in `ps` output: R=running, S=sleeping, D=I/O wait, Z=zombie
