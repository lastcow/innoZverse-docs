# Lab 11: Process Management

## 🎯 Objective
Manage Linux processes using kill signals, nice/renice for priority, ionice for I/O scheduling, and pgrep/pkill for finding and signaling processes.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Lab 10 (System Monitoring)

## 🔬 Lab Instructions

### Step 1: View Running Processes
```bash
ps aux | head -10
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# root         1  0.0  0.1 168680 11496 ?        Ss   Feb27   0:03 /sbin/init
# root         2  0.0  0.0      0     0 ?        S    Feb27   0:00 [kthreadd]

# Show process tree
ps axjf | head -20
# or
pstree -p | head -20
```

### Step 2: Kill Signals
```bash
# List all signals
kill -l
#  1) SIGHUP   2) SIGINT   3) SIGQUIT   9) SIGKILL  15) SIGTERM
# ...

# Common signals:
# SIGTERM (15): graceful shutdown request (default for kill)
# SIGKILL  (9): forceful immediate kill (cannot be caught)
# SIGHUP   (1): reload configuration
# SIGINT   (2): interrupt (like Ctrl+C)
# SIGSTOP (19): pause/suspend process
# SIGCONT (18): resume paused process

echo "Signal reference reviewed"
```

### Step 3: Sending Signals with kill
```bash
# Start a background sleep process
sleep 300 &
SLEEP_PID=$!
echo "Started sleep PID: $SLEEP_PID"

# Verify it's running
ps aux | grep "sleep 300" | grep -v grep
# ubuntu  12345  0.0  0.0   5484   580 pts/0   S   06:01   0:00 sleep 300

# Send SIGTERM (graceful, default)
kill $SLEEP_PID
sleep 0.5
ps aux | grep "$SLEEP_PID" | grep -v grep || echo "Process $SLEEP_PID terminated"
```

### Step 4: SIGKILL for Stubborn Processes
```bash
# Start a process that ignores SIGTERM (trap simulation)
bash -c 'trap "" TERM; sleep 300' &
STUB_PID=$!
echo "Started stubborn PID: $STUB_PID"

# SIGTERM won't work
kill -15 $STUB_PID
sleep 0.5
ps aux | grep "$STUB_PID" | grep -v grep && echo "Still running!"

# SIGKILL always works
kill -9 $STUB_PID
sleep 0.5
ps aux | grep "$STUB_PID" | grep -v grep || echo "Process killed"
```

### Step 5: pgrep and pkill
```bash
# Start some sleep processes
sleep 1000 &
sleep 2000 &
sleep 3000 &

# Find by name
pgrep sleep
# 12345
# 12346
# 12347

pgrep -a sleep
# 12345 sleep 1000
# 12346 sleep 2000
# 12347 sleep 3000

# Kill by name (sends SIGTERM to all matching)
pkill sleep
sleep 0.5
pgrep sleep || echo "All sleep processes terminated"
```

### Step 6: nice — Set Process Priority at Launch
```bash
# Priority range: -20 (highest) to +19 (lowest)
# Default nice value: 0

# Launch with low priority (nice 10)
nice -n 10 sleep 500 &
NICE_PID=$!

# Check the nice value
ps -o pid,ni,comm -p $NICE_PID
# PID  NI COMMAND
# 12345 10 sleep

# Only root can set negative nice values (higher priority)
# sudo nice -n -5 important_process
kill $NICE_PID 2>/dev/null || true
```

### Step 7: renice — Change Priority of Running Process
```bash
# Start a process with default priority
sleep 600 &
PROC_PID=$!

ps -o pid,ni,comm -p $PROC_PID
# PID  NI COMMAND
# 12345  0 sleep

# Lower priority (be nice to others)
renice +15 -p $PROC_PID
# 12345 (process ID) old priority 0, new priority 15

ps -o pid,ni,comm -p $PROC_PID
# PID  NI COMMAND
# 12345 15 sleep

kill $PROC_PID 2>/dev/null || true
```

### Step 8: ionice — I/O Scheduling Priority
```bash
# ionice controls I/O scheduling class and priority
# Classes:
# 1 = Realtime (highest, guaranteed I/O time)
# 2 = Best-effort (default, values 0-7, 0=highest)
# 3 = Idle (only gets I/O when nothing else needs it)

# Run a command with idle I/O priority (good for backups)
ionice -c 3 find /var -name "*.log" > /dev/null 2>&1 &
IONICE_PID=$!

# Check I/O class
ionice -p $IONICE_PID
# idle

# Renice I/O of existing process to best-effort, priority 7
ionice -c 2 -n 7 -p $IONICE_PID
ionice -p $IONICE_PID
# best-effort: prio 7

kill $IONICE_PID 2>/dev/null || true
```

### Step 9: Suspend and Resume Processes
```bash
# Start a process
sleep 999 &
PROC_PID=$!
echo "Running: $PROC_PID"

# Suspend it (SIGSTOP)
kill -STOP $PROC_PID
ps aux | grep "$PROC_PID" | grep -v grep
# ubuntu  12345  ... T  06:01   0:00 sleep 999   (T = stopped)

# Resume it (SIGCONT)
kill -CONT $PROC_PID
ps aux | grep "$PROC_PID" | grep -v grep
# ubuntu  12345  ... S  06:01   0:00 sleep 999   (S = sleeping/running)

kill $PROC_PID 2>/dev/null || true
```

### Step 10: Process Management Script
```bash
cat > ~/proc_monitor.sh << 'EOF'
#!/bin/bash
echo "=== Process Management Report: $(date) ==="

echo ""
echo "Top 5 CPU processes:"
ps aux --sort=-%cpu | awk 'NR>1 && NR<=6 {printf "  PID %-6s USER %-8s CPU %-5s %s\n", $2, $1, $3, $11}'

echo ""
echo "Top 5 Memory processes:"
ps aux --sort=-%mem | awk 'NR>1 && NR<=6 {printf "  PID %-6s USER %-8s MEM %-5s %s\n", $2, $1, $4, $11}'

echo ""
echo "Zombie processes:"
zombies=$(ps aux | awk '$8 == "Z" {print $2, $11}')
if [[ -n "$zombies" ]]; then
    echo "$zombies" | awk '{print "  " $0}'
else
    echo "  None"
fi

echo ""
echo "Process count by user:"
ps aux | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn | head -5 | awk '{printf "  %-10s %s processes\n", $2, $1}'
EOF
chmod +x ~/proc_monitor.sh
~/proc_monitor.sh
```

## ✅ Verification
```bash
# Start and kill a test process
sleep 999 &
PID=$!
pgrep -a sleep | grep 999
# 12345 sleep 999

kill $PID
sleep 0.2
pgrep -a sleep | grep "$PID" || echo "Process terminated"
```

## 📝 Summary
- `kill -15 PID` (SIGTERM) requests graceful shutdown; `kill -9 PID` forces it
- `pgrep name` finds PIDs by name; `pkill name` kills by name
- `nice -n VALUE cmd` sets CPU priority at launch; `renice VALUE -p PID` changes it
- Nice range: -20 (highest priority) to +19 (lowest); only root can go negative
- `ionice -c 3` gives idle I/O class (ideal for background backups)
- `kill -STOP PID` suspends; `kill -CONT PID` resumes a process
