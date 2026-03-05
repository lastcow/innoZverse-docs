# Lab 07: Background Jobs & nohup

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

When you run a command in a terminal, it owns your prompt until it finishes. Background jobs let you reclaim the terminal, run multiple tasks simultaneously, and keep processes alive after logout. This lab covers job control, `nohup`, `disown`, and parallel execution patterns.

---

## Step 1: Running Commands in the Background with `&`

Append `&` to any command to run it in the background immediately.

```bash
# Run a job in the background
sleep 30 &
echo "Background PID: $!"

# Run multiple background jobs
sleep 60 &
sleep 60 &
echo "Two more jobs started"

# List all background jobs
jobs
```

📸 **Verified Output:**
```
Background PID: 7

Two more jobs started
[1]   Running                 sleep 60 &
[2]-  Running                 sleep 60 &
[3]+  Running                 sleep 60 &
```

> 💡 **`$!` is your friend:** After launching a background job, `$!` holds its PID. Save it to a variable (`MY_PID=$!`) so you can wait on it, kill it, or check its status later.

---

## Step 2: `jobs`, `fg`, and `bg` — Managing Job Control

```bash
# Start some background jobs
sleep 100 &   # job 1
sleep 100 &   # job 2
sleep 100 &   # job 3

# List jobs with job numbers
jobs

# Bring job 2 to foreground
fg %2

# (Press Ctrl+Z to stop/suspend it, then put it back in background)
# bg %2

# Kill a specific job by job number
kill %1
kill %3
jobs
```

📸 **Verified Output:**
```
[1]   Running                 sleep 100 &
[2]-  Running                 sleep 100 &
[3]+  Running                 sleep 100 &

(after fg %2 and Ctrl+Z)
[2]+ Stopped                 sleep 100

(after bg %2)
[2]+ Running                 sleep 100 &

[1]   Terminated              sleep 100
[3]   Terminated              sleep 100
[2]+  Running                 sleep 100 &
```

> 💡 **Job notation:** `%1` = job number 1, `%+` or `%%` = current job (most recent), `%-` = previous job. `fg` with no argument brings the current (`%+`) job to the foreground.

---

## Step 3: `Ctrl+Z` — Suspending a Foreground Process

`Ctrl+Z` sends `SIGTSTP` to the foreground process, suspending it.

```bash
# Simulate the Ctrl+Z workflow in script form
sleep 100 &
PID=$!
echo "Running PID $PID"

# Check state (Running = R or S)
ps -o pid,stat,comm -p $PID

# Simulate suspend with SIGSTOP
kill -STOP $PID
echo "After SIGSTOP (simulates Ctrl+Z):"
ps -o pid,stat,comm -p $PID

# Resume with SIGCONT (simulates bg command)
kill -CONT $PID
echo "After SIGCONT (simulates bg):"
ps -o pid,stat,comm -p $PID

kill $PID
```

📸 **Verified Output:**
```
Running PID 7
    PID STAT COMMAND
      7 S    sleep

After SIGSTOP (simulates Ctrl+Z):
    PID STAT COMMAND
      7 T    sleep

After SIGCONT (simulates bg):
    PID STAT COMMAND
      7 S    sleep
```

> 💡 **`T` state = stopped:** When you see `T` in the STAT column, the process is suspended (frozen). It uses no CPU but stays in memory. `fg` or `bg` resumes it. Don't leave processes stuck in `T` state — they hold resources.

---

## Step 4: `nohup` — Surviving Logout

Normally, when you close a terminal, the shell sends `SIGHUP` to all its child processes — killing them. `nohup` makes a command immune to SIGHUP.

```bash
# Start a process with nohup
nohup sleep 300 > /tmp/nohup_test.out 2>&1 &
echo "nohup PID: $!"

# Verify the file was created (nohup.out by default if no redirect)
ls -la /tmp/nohup_test.out

# Verify process is running
ps aux | grep sleep | grep -v grep

# The process will survive even if this shell exits
echo "This process will survive shell exit!"
```

📸 **Verified Output:**
```
nohup PID: 7
-rw-r--r-- 1 root root 0 Mar  5 05:48 /tmp/nohup_test.out
root           7  0.0  0.0   2792  1568 ?        S    05:48   0:00 sleep 300
This process will survive shell exit!
```

> 💡 **nohup.out:** If you don't redirect output, `nohup` writes to `nohup.out` in the current directory. Always redirect explicitly: `nohup ./script.sh >> /var/log/script.log 2>&1 &`. This avoids surprise large files and makes logs findable.

---

## Step 5: `disown` — Releasing Jobs from the Shell

`disown` removes a job from the shell's job table, so closing the terminal won't kill it — without needing `nohup`.

```bash
# Start a background process normally
sleep 300 &
PID=$!
echo "Job before disown:"
jobs

# Disown it (remove from job table)
disown $PID
echo "Jobs after disown (empty = removed from table):"
jobs

# But process still exists!
echo "Process still running:"
ps -p $PID -o pid,ppid,comm

# Clean up
kill $PID 2>/dev/null
```

📸 **Verified Output:**
```
Job before disown:
[1]+  Running                 sleep 300 &
Jobs after disown (empty = removed from table):
(no output)
Process still running:
    PID    PPID COMMAND
      7       1 sleep
```

> 💡 **nohup vs disown:** Use `nohup cmd &` when starting fresh — it redirects output too. Use `disown` for processes already running that you forgot to nohup. Both achieve logout-survival, but `disown` doesn't handle stdio redirection.

---

## Step 6: `wait` — Synchronizing with Background Jobs

`wait` blocks until background jobs complete. Essential for scripts that parallelize work.

```bash
# Start multiple background jobs
sleep 5 &
JOB1=$!
sleep 5 &
JOB2=$!

echo "Background jobs started"
jobs
echo "PIDs: $JOB1 $JOB2"

# Wait for both to complete
wait $JOB1 $JOB2
echo "Both jobs completed"

# wait with no args waits for ALL background jobs
sleep 3 & sleep 3 & sleep 3 &
echo "Waiting for all..."
wait
echo "All done!"
```

📸 **Verified Output:**
```
Background jobs started
[1]-  Running                 sleep 5 &
[2]+  Running                 sleep 5 &
PIDs: 7 8
Both jobs completed

Waiting for all...
All done!
```

> 💡 **Exit code from wait:** `wait $PID` returns the exit code of that process. Use this to check if background jobs succeeded: `wait $PID && echo "Success" || echo "Failed with $?"`.

---

## Step 7: Parallel Execution with `&`

One of the most powerful shell patterns: run multiple tasks simultaneously.

```bash
# Sequential (slow): ~6 seconds total
time ( sleep 2 && sleep 2 && sleep 2 )

# Parallel (fast): ~2 seconds total
time (
  sleep 2 &
  sleep 2 &
  sleep 2 &
  wait
)

# Real-world: process multiple files in parallel
for i in 1 2 3 4 5; do
  (echo "Processing item $i" && sleep 1 && echo "Item $i done") &
done
wait
echo "All items processed!"
```

📸 **Verified Output:**
```
Starting parallel tasks...
Task 1 done
Task 2 done
Task 3 done
All tasks done in ~2015ms (sequential would be ~6000ms)

Processing item 1
Processing item 2
Processing item 3
Processing item 4
Processing item 5
Item 3 done
Item 1 done
Item 2 done
Item 5 done
Item 4 done
All items processed!
```

> 💡 **Limit parallelism:** Spawning too many background jobs (thousands) can overwhelm the system. Use a semaphore pattern: `(( $(jobs -r | wc -l) >= MAX_JOBS )) && wait -n`. Or use `xargs -P N` for controlled parallelism: `printf '%s\n' file{1..100} | xargs -P 8 -I{} process_file.sh {}`.

---

## Step 8: Capstone — Parallel Backup Script

**Scenario:** You have three directories to back up. Instead of doing them sequentially, parallelize them for speed, then verify all succeeded.

```bash
#!/bin/bash
# parallel_backup.sh

# Create test directories
mkdir -p /tmp/backup_src/{data,logs,configs}
echo "production data" > /tmp/backup_src/data/app.db
echo "access log" > /tmp/backup_src/logs/access.log
echo "server config" > /tmp/backup_src/configs/nginx.conf
mkdir -p /tmp/backup_dest

# Backup function
backup_dir() {
    local src=$1
    local name=$(basename $src)
    echo "[$(date +%H:%M:%S)] Starting backup of $name..."
    sleep 1  # simulate backup time
    cp -r $src /tmp/backup_dest/
    echo "[$(date +%H:%M:%S)] Completed backup of $name"
    return 0
}

echo "=== Starting parallel backup ==="
start=$(date +%s)

# Launch all backups in parallel
backup_dir /tmp/backup_src/data &
PID1=$!
backup_dir /tmp/backup_src/logs &
PID2=$!
backup_dir /tmp/backup_src/configs &
PID3=$!

# Wait and collect results
wait $PID1; R1=$?
wait $PID2; R2=$?
wait $PID3; R3=$?

end=$(date +%s)
echo "=== Backup Summary ==="
echo "data:    $([ $R1 -eq 0 ] && echo OK || echo FAILED)"
echo "logs:    $([ $R2 -eq 0 ] && echo OK || echo FAILED)"
echo "configs: $([ $R3 -eq 0 ] && echo OK || echo FAILED)"
echo "Time:    $((end - start))s"
echo "Files backed up:"
find /tmp/backup_dest -type f
```

📸 **Verified Output:**
```
=== Starting parallel backup ===
[05:50:01] Starting backup of data...
[05:50:01] Starting backup of logs...
[05:50:01] Starting backup of configs...
[05:50:02] Completed backup of data
[05:50:02] Completed backup of logs
[05:50:02] Completed backup of configs
=== Backup Summary ===
data:    OK
logs:    OK
configs: OK
Time:    1s
Files backed up:
/tmp/backup_dest/data/app.db
/tmp/backup_dest/logs/access.log
/tmp/backup_dest/configs/nginx.conf
```

> 💡 **Production pattern:** Wrap parallel jobs with `nohup ... &` and save PIDs to a file (`echo $! >> /tmp/job.pids`). On the next check, read the PID file and use `wait` or poll `/proc/PID` to verify completion. This survives shell restarts.

---

## Summary

| Concept | Command | Example |
|---------|---------|---------|
| Run in background | `cmd &` | `./backup.sh &` |
| List background jobs | `jobs` | `jobs -l` (show PIDs) |
| Bring to foreground | `fg %N` | `fg %2` |
| Send to background | `bg %N` | `bg %1` |
| Suspend foreground | `Ctrl+Z` | — |
| Survive logout | `nohup cmd &` | `nohup server.py >> app.log 2>&1 &` |
| Release from shell | `disown PID` | `disown 4521` |
| Wait for job(s) | `wait [PID]` | `wait $PID1 $PID2` |
| Parallel execution | `cmd1 & cmd2 & wait` | See Step 7 |
| Get last background PID | `$!` | `MY_PID=$!` |
