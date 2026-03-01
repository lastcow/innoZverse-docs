# Lab 16: Process Basics

## 🎯 Objective
Understand Linux processes using ps, view running processes, filter by user, and learn about signals with kill -l.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 15: Disk Usage

## 🔬 Lab Instructions

### Step 1: List Processes with ps aux

```bash
ps aux | head -20
```

**Expected output:**
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0  25788 15932 ?        Ss   Feb26   0:57 /sbin/init
...
```

```bash
# Column meanings:
# USER=owner, PID=process ID, %CPU/%MEM=resources
# VSZ=virtual memory, RSS=physical RAM, STAT=state
# STAT values: S=sleeping, R=running, Z=zombie, T=stopped

ps aux | wc -l
```

### Step 2: List Processes with ps -ef

```bash
ps -ef | head -20
```

**Expected output:**
```
UID          PID    PPID  C STIME TTY          TIME CMD
root           1       0  0 Feb26 ?        00:00:57 /sbin/init
```

### Step 3: Find Your Own Processes

```bash
ps aux | grep "^$(whoami)"
ps -u $(whoami)
ps -u $(whoami) -o pid,ppid,%cpu,%mem,stat,command
```

### Step 4: Find Specific Processes

```bash
# The [b]ash trick prevents grep from showing itself
ps aux | grep "[b]ash"
ps aux | grep "[s]shd" | head -5
echo "Current shell PID: $$"
ps -p $$
```

### Step 5: Sort Processes by Resource Usage

```bash
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10
ps -eo pid,ppid,%mem,%cpu,command --sort=-%mem | head -10
```

### Step 6: List Signals with kill -l

```bash
kill -l
```

**Expected output:**
```
 1) SIGHUP       2) SIGINT       3) SIGQUIT      4) SIGILL
...
 9) SIGKILL     ...  15) SIGTERM  ...
```

```bash
echo "Signal 1  = SIGHUP  - Hang up / reload config"
echo "Signal 2  = SIGINT  - Interrupt (Ctrl+C)"
echo "Signal 9  = SIGKILL - Force kill (cannot be ignored)"
echo "Signal 15 = SIGTERM - Graceful termination (default)"
echo "Signal 19 = SIGSTOP - Stop process (cannot be ignored)"
```

## ✅ Verification

```bash
echo "=== Your processes ==="
ps -u $(whoami) -o pid,ppid,stat,command | head -10
echo ""
echo "=== Total process count ==="
ps aux | wc -l
echo ""
echo "=== Available signals ==="
kill -l | head -4
echo ""
echo "=== Current shell PID: $$ ==="
echo "Lab 16 complete"
```

## 📝 Summary
- `ps aux` shows all processes (BSD format); `ps -ef` shows all (UNIX format)
- Each process has a PID, PPID (parent), and runs as a specific user
- `ps aux | grep "[pattern]"` finds specific processes (bracket trick)
- `ps aux --sort=-%cpu` shows top CPU consumers
- `kill -l` lists all signals — 9 (SIGKILL) force kills, 15 (SIGTERM) is graceful
- `$$` holds the current shell's PID
