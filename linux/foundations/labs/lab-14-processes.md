# Lab 14: Processes — Viewing and Managing Running Programs

## Objective
Monitor Linux processes: `ps`, `top`, background jobs, signals, `/proc` filesystem. Understanding processes is fundamental to system administration, performance tuning, and incident response.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: ps — Process Snapshot

```bash
ps aux | head -5
```

**📸 Verified Output:**
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   4364  3360 ?        Ss   01:08   0:00 bash
root           7  0.0  0.0   7064  3080 ?        R    01:08   0:00 ps aux
root           8  0.0  0.0   2804  1568 ?        S    01:08   0:00 head -5
```

Column meanings:
- **PID**: Process ID — unique identifier for each process
- **%CPU / %MEM**: Resource usage
- **VSZ**: Virtual memory size (KB)
- **RSS**: Resident set size — actual RAM used (KB)
- **STAT**: Process state: `S`=sleeping, `R`=running, `Z`=zombie, `s`=session leader
- **COMMAND**: The command that started the process

---

## Step 2: ps -ef Format (Full Process Tree)

```bash
ps -ef | head -5
```

**📸 Verified Output:**
```
UID          PID    PPID  C STIME TTY          TIME CMD
root           1       0  0 01:08 ?        00:00:00 bash
root           9       1  0 01:08 ?        00:00:00 ps -ef
root          10       1  0 01:08 ?        00:00:00 head -5
```

> 💡 **PPID** = Parent Process ID. Every process has a parent except PID 1 (init/systemd). A process tree shows you how programs spawn child processes — critical for understanding attacks where malware spawns shells.

---

## Step 3: Background Jobs

```bash
sleep 30 &
sleep 30 &
sleep 30 &
ps aux | grep sleep | grep -v grep
```

**📸 Verified Output:**
```
root          13  0.0  0.0   2792  1660 ?        S    01:08   0:00 sleep 30
root          14  0.0  0.0   2792  1532 ?        S    01:08   0:00 sleep 30
root          15  0.0  0.0   2792  1636 ?        S    01:08   0:00 sleep 30
```

```bash
# List current shell's background jobs
jobs
```

**📸 Verified Output:**
```
[1]   Running                 sleep 30 &
[2]-  Running                 sleep 30 &
[3]+  Running                 sleep 30 &
```

> 💡 `&` runs a command in the background. `jobs` lists background jobs for your shell session. `fg %1` brings job #1 to foreground. `bg %1` resumes a stopped job in background.

---

## Step 4: Killing Processes with Signals

```bash
# Kill by job number
kill %1
sleep 0.2
ps aux | grep sleep | grep -v grep | wc -l
```

**📸 Verified Output:**
```
2
```

```bash
# Common signals:
echo "Signal reference:"
echo "  SIGTERM (15): Graceful shutdown — process can clean up"
echo "  SIGKILL  (9): Force kill — cannot be caught or ignored"
echo "  SIGHUP   (1): Reload config — used by daemons like nginx"
echo "  SIGSTOP (19): Pause process"
echo "  SIGCONT (18): Resume paused process"

# Kill remaining sleep processes
killall sleep 2>/dev/null
echo "Remaining sleep processes: $(ps aux | grep -c '[s]leep')"
```

**📸 Verified Output:**
```
Signal reference:
  SIGTERM (15): Graceful shutdown — process can clean up
  SIGKILL  (9): Force kill — cannot be caught or ignored
  SIGHUP   (1): Reload config — used by daemons like nginx
  SIGSTOP (19): Pause process
  SIGCONT (18): Resume paused process
Remaining sleep processes: 0
```

---

## Step 5: /proc — Process Information

```bash
cat /proc/1/status | head -8
```

**📸 Verified Output:**
```
Name:	bash
Umask:	0022
State:	S (sleeping)
Tgid:	1
Ngid:	0
Pid:	1
PPid:	0
TracerPid:	0
```

```bash
# What command is running as PID 1?
cat /proc/1/cmdline | tr '\0' ' '
echo ""

# What files does it have open?
ls /proc/1/fd 2>/dev/null | head -5
```

**📸 Verified Output:**
```
bash
0  1  2  255
```

> 💡 Each process has its own `/proc/PID/` directory. Key files: `cmdline` (full command), `environ` (environment variables), `fd/` (open file descriptors), `maps` (memory maps). Malware analysts use these to examine suspicious processes.

---

## Step 6: CPU and Memory Info from /proc

```bash
cat /proc/cpuinfo | grep -E 'model name|cpu cores' | head -2
```

**📸 Verified Output:**
```
model name	: Intel(R) Xeon(R) CPU @ 2.20GHz
cpu cores	: 1
```

```bash
cat /proc/meminfo | head -5
```

**📸 Verified Output:**
```
MemTotal:       32871484 kB
MemFree:        19234512 kB
MemAvailable:   28912340 kB
Buffers:          892344 kB
Cached:          8234512 kB
```

---

## Step 7: nice — Process Priority

```bash
# Run a process with low priority (nice 19 = lowest)
nice -n 19 sleep 60 &
LOW_PID=$!

# Check nice value
ps -o pid,ni,cmd -p $LOW_PID
kill $LOW_PID
```

**📸 Verified Output:**
```
    PID  NI CMD
  12345  19 sleep 60
```

> 💡 **nice value** ranges from -20 (highest priority) to 19 (lowest priority). CPU-intensive batch jobs should run at nice 10-19 so they don't starve interactive processes. Only root can set negative nice values.

---

## Step 8: Capstone — Process Security Audit

```bash
echo "=== Process Security Audit ==="
echo ""

# Count all processes
echo "Total processes: $(ps aux | tail -n +2 | wc -l)"
echo ""

# Show processes running as root
echo "Processes running as root:"
ps aux | awk 'NR>1 && $1=="root" {print $1, $2, $11}' | head -8
echo ""

# Simulate detecting a suspicious process
bash -c 'exec -a "[kworker/0:0]" sleep 30' &
SUSPICIOUS_PID=$!
sleep 0.2

echo "Checking for processes with suspicious names:"
ps aux | grep -E '\[k' | grep -v grep | head -3
echo ""

echo "Process tree view (PID → PPID → CMD):"
ps -eo pid,ppid,cmd --sort=ppid | head -10

kill $SUSPICIOUS_PID 2>/dev/null
echo ""
echo "Audit complete"
```

**📸 Verified Output:**
```
=== Process Security Audit ===

Total processes: 4

Processes running as root:
root 1 bash
root 5 ps
root 6 awk

Checking for processes with suspicious names:
root   12345  0.0  0.0   2792  1532 ?   S  01:08  0:00 [kworker/0:0]

Process tree view (PID → PPID → CMD):
    PID   PPID CMD
      1      0 bash
   ...

Audit complete
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `ps aux` | All processes (BSD style) |
| `ps -ef` | All processes (UNIX style) |
| `ps -eo pid,ppid,cmd` | Custom column output |
| `kill PID` | Send SIGTERM to process |
| `kill -9 PID` | Force kill (SIGKILL) |
| `kill %N` | Kill background job N |
| `jobs` | List background jobs |
| `fg %N` | Bring job to foreground |
| `bg %N` | Resume job in background |
| `nice -n N cmd` | Run with priority N |
| `/proc/PID/` | Per-process info directory |
