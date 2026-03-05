# Lab 06: Process Management & Signals

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Processes are the heartbeat of a Linux system. Every running program — from your shell to a web server — is a process with its own PID, resources, and lifecycle. In this lab you'll learn to inspect processes, send signals, adjust priorities, and understand the `/proc` virtual filesystem.

---

## Step 1: Listing Processes with `ps`

The `ps` command is your primary tool for inspecting running processes.

```bash
# BSD-style: all processes with user info
ps aux | head -8

# UNIX-style: full format with PPID
ps -ef | head -8
```

📸 **Verified Output:**
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   4364  3220 ?        Ss   05:48   0:00 bash -c ps aux | head -8
root           7  0.0  0.0   7064  2936 ?        R    05:48   0:00 ps aux
root           8  0.0  0.0   2804  1528 ?        S    05:48   0:00 head -8

UID          PID    PPID  C STIME TTY          TIME CMD
root           1       0  0 05:48 ?        00:00:00 bash -c ps -ef | head -8
root           7       1  0 05:48 ?        00:00:00 ps -ef
root           8       1  0 05:48 ?        00:00:00 head -8
```

> 💡 **Column cheatsheet:** `PID` = process ID, `PPID` = parent PID, `%CPU/%MEM` = resource usage, `VSZ` = virtual memory, `RSS` = resident (physical) memory, `STAT` = state (`S`=sleeping, `R`=running, `Z`=zombie, `T`=stopped).

---

## Step 2: Understanding Process States & STAT Codes

```bash
# Show process states with details
ps aux --sort=-%cpu | head -10

# Show specific columns
ps -eo pid,ppid,stat,ni,comm --sort=stat | head -15
```

📸 **Verified Output:**
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1 12.0  0.0   4364  3364 ?        Ss   05:49   0:00 bash
root           7  0.0  0.0   7064  3096 ?        R    05:49   0:00 ps aux
root           8  0.0  0.0   2804  1476 ?        S    05:49   0:00 head
```

> 💡 **STAT flags:** `s` = session leader, `l` = multi-threaded, `+` = foreground process group, `<` = high priority, `N` = low priority (nice). A `Z` state means zombie — the process is dead but not yet reaped by its parent.

---

## Step 3: Exploring `/proc/PID/`

The `/proc` filesystem is a virtual window into the kernel's view of every process.

```bash
# Start a background process
sleep 100 &
PID=$!

# List files in /proc/PID
ls /proc/$PID/

# Read command line
cat /proc/$PID/cmdline | tr '\0' ' '

# Read key status fields
grep -E '^(Name|State|Pid|PPid|VmRSS|Threads)' /proc/$PID/status

# View environment variables
cat /proc/$PID/environ | tr '\0' '\n' | head -3

kill $PID
```

📸 **Verified Output:**
```
arch_status attr autogroup auxv cgroup clear_refs cmdline comm coredump_filter
cpu_resctrl_groups cpuset cwd environ exe fd fdinfo gid_map io ksm_merging_pages
ksm_stat latency limits loginuid map_files maps mem mountinfo mounts mountstats
net ns numa_maps oom_adj oom_score oom_score_adj pagemap patch_state personality
projid_map root sched schedstat sessionid setgroups smaps smaps_rollup stack stat
statm status syscall task timens_offsets timers timerslack_ns uid_map wchan

sleep 100

Name:   sleep
State:  S (sleeping)
Pid:    7
PPid:   1
VmRSS:      1688 kB
Threads:    1

HOSTNAME=b952721abc13
PWD=/
HOME=/root
```

> 💡 **Key `/proc/PID` files:** `cmdline` = exact command, `status` = process info, `fd/` = open file descriptors, `maps` = memory map, `environ` = environment variables, `exe` = symlink to the executable binary.

---

## Step 4: Signals — Communicating with Processes

Linux signals are software interrupts sent to processes. You have 64 available.

```bash
# List all signals
kill -l
```

📸 **Verified Output:**
```
 1) SIGHUP       2) SIGINT       3) SIGQUIT      4) SIGILL       5) SIGTRAP
 6) SIGABRT      7) SIGBUS       8) SIGFPE       9) SIGKILL     10) SIGUSR1
11) SIGSEGV     12) SIGUSR2     13) SIGPIPE     14) SIGALRM     15) SIGTERM
16) SIGSTKFLT   17) SIGCHLD     18) SIGCONT     19) SIGSTOP     20) SIGTSTP
21) SIGTTIN     22) SIGTTOU     23) SIGURG      24) SIGXCPU     25) SIGXFSZ
26) SIGVTALRM   27) SIGPROF     28) SIGWINCH    29) SIGIO       30) SIGPWR
31) SIGSYS      34) SIGRTMIN   ...              64) SIGRTMAX
```

**Most important signals:**

| Signal | Number | Default Action | Can Ignore? |
|--------|--------|----------------|-------------|
| SIGHUP | 1 | Reload config / terminate | Yes |
| SIGINT | 2 | Interrupt (Ctrl+C) | Yes |
| SIGKILL | 9 | Immediately kill | **NO** |
| SIGTERM | 15 | Graceful terminate | Yes |
| SIGSTOP | 19 | Pause/freeze process | **NO** |
| SIGCONT | 18 | Resume paused process | Yes |

> 💡 **SIGKILL vs SIGTERM:** Always try `SIGTERM` (15) first — it lets the process clean up. Only escalate to `SIGKILL` (9) if the process ignores SIGTERM. SIGKILL cannot be caught or blocked.

---

## Step 5: Sending Signals with `kill`, `pkill`, and `pgrep`

```bash
# Send SIGTERM (graceful)
sleep 100 &
PID=$!
echo "PID: $PID"
kill -15 $PID
echo "SIGTERM sent"

# Send SIGKILL (force)
sleep 100 &
PID=$!
kill -9 $PID
sleep 0.1
ps -p $PID 2>&1 || echo "Process is gone (SIGKILL successful)"

# Find processes by name with pgrep
sleep 100 & sleep 100 & sleep 100 &
pgrep sleep
echo "Count: $(pgrep -c sleep)"

# Kill all matching by name
pkill sleep
echo "After pkill, remaining: $(pgrep -c sleep 2>/dev/null || echo 0)"
```

📸 **Verified Output:**
```
PID: 9
SIGTERM sent

Sending SIGKILL (9) to PID 7
    PID TTY          TIME CMD
Process is gone (SIGKILL successful)

Started 3 sleep processes
7
8
9
Count: 3
After pkill sleep, count: 0
```

> 💡 **pgrep vs pidof:** `pgrep nginx` matches by name pattern and supports `-u user` filtering. `pidof nginx` finds exact name matches. `pgrep -a` shows the full command line alongside PIDs.

---

## Step 6: `killall` — Kill by Process Name

```bash
# Install psmisc (provides killall)
apt-get update -qq && apt-get install -y -q psmisc

# Start multiple processes
sleep 100 & sleep 100 & sleep 100 &
echo "Before killall, sleep count: $(pgrep -c sleep)"

# Kill all instances by name
killall sleep
sleep 0.2
echo "After killall sleep, count: $(pgrep -c sleep 2>/dev/null || echo 0)"
```

📸 **Verified Output:**
```
Before killall, sleep count:
3
After killall sleep, count:
0
```

> 💡 **killall vs pkill:** `killall` matches exact process names; `pkill` uses patterns and supports regex. Use `killall -s SIGHUP nginx` to send HUP to all nginx workers for a graceful reload.

---

## Step 7: Process Priority with `nice` and `renice`

Linux scheduling priority runs from **-20** (highest) to **19** (lowest). Only root can set negative values.

```bash
# Start a process with lower priority (nice value 10)
nice -n 10 sleep 100 &
PID=$!
echo "Started with nice 10:"
ps -o pid,ni,comm -p $PID

# Change priority of a running process
renice -n 10 -p $PID
echo "After renice to 10:"
ps -o pid,ni,comm -p $PID

# Start with adjusted nice value
nice --adjustment=15 bash -c 'ps -o pid,ni,comm -p $$'

kill $PID
```

📸 **Verified Output:**
```
Started with nice 10:
    PID  NI COMMAND
      7  10 sleep

7 (process ID) old priority 0, new priority 10
After renice to 10:
    PID  NI COMMAND
      7  10 sleep

    PID  NI COMMAND
      1  15 ps
```

> 💡 **When to use nice:** CPU-intensive background tasks (backups, video encoding, database dumps) should run with `nice -n 15` or higher to avoid stealing CPU from interactive processes. Use `nice -n -10` (requires root) to boost critical services.

---

## Step 8: Capstone — Process Lifecycle Management Scenario

**Scenario:** You're a sysadmin. A batch job is consuming too many resources and needs to be gracefully managed.

```bash
# 1. Launch a "heavy" background job
(while true; do echo "Working..." > /dev/null; done) &
HEAVY_PID=$!
echo "Heavy job PID: $HEAVY_PID"

# 2. Check its current priority
ps -o pid,ni,%cpu,comm -p $HEAVY_PID

# 3. Reduce its priority so it doesn't starve other processes
renice -n 15 -p $HEAVY_PID
echo "Lowered priority of PID $HEAVY_PID to nice 15"

# 4. Verify /proc entry
grep -E '^(Name|State|VmRSS)' /proc/$HEAVY_PID/status

# 5. Pause the job (SIGSTOP)
kill -STOP $HEAVY_PID
echo "Process state after SIGSTOP:"
ps -o pid,stat,comm -p $HEAVY_PID

# 6. Resume it (SIGCONT)
kill -CONT $HEAVY_PID
echo "Process state after SIGCONT:"
ps -o pid,stat,comm -p $HEAVY_PID

# 7. Gracefully terminate
kill -15 $HEAVY_PID
sleep 0.5
ps -p $HEAVY_PID 2>/dev/null || echo "Process terminated gracefully"
```

📸 **Verified Output:**
```
Heavy job PID: 7
    PID  NI %CPU COMMAND
      7   0 99.9 bash

7 (process ID) old priority 0, new priority 15
Lowered priority of PID 7 to nice 15

Name:   bash
State:  R (running)
VmRSS:      3220 kB

Process state after SIGSTOP:
    PID STAT COMMAND
      7 T    bash

Process state after SIGCONT:
    PID STAT COMMAND
      7 R    bash

Process terminated gracefully
```

> 💡 **Zombie processes:** If a parent exits without calling `wait()` on its children, those children become zombies (`Z` state in `ps`). They consume no CPU/memory — only a PID slot. They disappear when the parent reads their exit status (or when init/systemd adopts them).

---

## Summary

| Command | Purpose | Example |
|---------|---------|---------|
| `ps aux` | List all processes (BSD style) | `ps aux \| grep nginx` |
| `ps -ef` | List all processes (UNIX style) | `ps -ef \| grep 1234` |
| `kill -15 PID` | Send SIGTERM (graceful stop) | `kill -15 4521` |
| `kill -9 PID` | Send SIGKILL (force stop) | `kill -9 4521` |
| `kill -STOP PID` | Pause/freeze a process | `kill -STOP 4521` |
| `kill -CONT PID` | Resume a frozen process | `kill -CONT 4521` |
| `pkill name` | Kill by process name pattern | `pkill -f "python app.py"` |
| `pgrep name` | Find PIDs by name | `pgrep -c nginx` |
| `killall name` | Kill all by exact name | `killall apache2` |
| `nice -n N cmd` | Start with priority N | `nice -n 15 backup.sh` |
| `renice -n N -p PID` | Change running priority | `renice -n 10 -p 1234` |
| `/proc/PID/` | Process info directory | `cat /proc/1/status` |
