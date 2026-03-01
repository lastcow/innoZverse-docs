# Lab 12: The at Command

## 🎯 Objective
Schedule one-time tasks using the at command (when available), understand the at queue, and use alternatives when at is not installed.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Practitioner Lab 11: Cron Jobs

## 🔬 Lab Instructions

### Step 1: Check if at is Available

```bash
which at 2>/dev/null && echo "at is installed" || echo "at is NOT installed on this system"
which atq 2>/dev/null && echo "atq is available" || echo "atq not available"
```

### Step 2: Understanding at Command

The `at` command schedules a one-time task to run at a specified future time.

Key differences from cron:
- **cron**: recurring jobs (run every N minutes/hours/days)
- **at**: one-time jobs (run once at a specific time)

```bash
cat > /tmp/at-syntax.txt << 'EOF'
AT COMMAND SYNTAX:
  at TIME
  at TIME DATE
  at now + N unit

TIME FORMATS:
  at 14:30          Run at 2:30 PM today
  at 2pm            Run at 2:00 PM today
  at midnight       Run at midnight
  at noon           Run at noon
  at now + 5 minutes  Run in 5 minutes
  at now + 2 hours    Run in 2 hours
  at now + 1 day      Run tomorrow at this time

DATE FORMATS:
  at 9am tomorrow
  at 3pm Jul 15
  at 10:00 2026-12-31

SUBMITTING A JOB:
  echo "command" | at now + 1 minute
  at now + 5 minutes << 'EOF'
    command1
    command2
  EOF

MANAGING JOBS:
  atq             List pending at jobs
  atrm JOB_ID     Remove a pending job
  at -l           Same as atq
EOF

cat /tmp/at-syntax.txt
```

### Step 3: Alternative: bash background with sleep

```bash
# When at is not available, use background sleep+command
# This runs a command after a delay in the background

echo "Scheduling a delayed task..."
(sleep 5 && echo "Delayed task executed at $(date)" >> /tmp/delayed-task.log) &
TASK_PID=$!
echo "Task scheduled as background process PID: $TASK_PID"
echo "Waiting for it..."
wait $TASK_PID
echo "Task completed:"
cat /tmp/delayed-task.log
```

### Step 4: systemd-run for One-Time Jobs (Modern Alternative)

```bash
# systemd-run can schedule one-time jobs
which systemd-run && echo "systemd-run available" || echo "systemd-run not found"
```

```bash
cat > /tmp/systemd-run-example.txt << 'EOF'
# Schedule a one-time job with systemd-run (requires systemd):
systemd-run --on-calendar="2026-03-01 18:00:00" /path/to/script.sh

# Run after a delay:
systemd-run --on-active=5min /path/to/script.sh

# List transient timers:
systemctl list-timers --no-pager
EOF

cat /tmp/systemd-run-example.txt
```

### Step 5: Create a Script for Delayed Execution

```bash
cat > /tmp/run-later.sh << 'EOF'
#!/bin/bash
# Usage: ./run-later.sh SECONDS "command"
# Schedules a command to run after SECONDS seconds

DELAY="${1:-60}"
COMMAND="${2:-echo 'task ran'}"

echo "[$(date)] Scheduling: $COMMAND"
echo "[$(date)] Will run in $DELAY seconds"

(
    sleep "$DELAY"
    echo "[$(date)] Running: $COMMAND"
    eval "$COMMAND"
) &

echo "[$(date)] Task scheduled as PID $!"
echo "Use 'kill $!' to cancel"
EOF

# Test with a 2-second delay
bash /tmp/run-later.sh 2 "echo 'Hello from the future'" &
SCHEDULER_PID=$!
wait $SCHEDULER_PID
echo "Done"
```

### Step 6: at Command Examples (Reference)

```bash
cat > /tmp/at-examples.txt << 'EOF'
# Example 1: Run a backup in 1 hour
echo "tar -czf /tmp/backup.tar.gz $HOME" | at now + 1 hour

# Example 2: Send notification at 5pm
echo "echo 'Time to go home!' > /tmp/reminder.txt" | at 5pm

# Example 3: Run at midnight
echo "/path/to/nightly-report.sh" | at midnight

# Example 4: List all pending jobs
atq

# Example 5: Remove job with ID 3
atrm 3

# Example 6: Submit multi-command job
at now + 10 minutes << 'ATEOF'
echo "Job started" >> /tmp/job.log
find /tmp -mtime +7 -delete 2>/dev/null
echo "Job completed" >> /tmp/job.log
ATEOF
EOF

cat /tmp/at-examples.txt
```

## ✅ Verification

```bash
which at 2>/dev/null && echo "at status: available" || echo "at status: not installed"
echo "Alternative demo:"
(sleep 1 && echo "Background task done") &
BGPID=$!
echo "Background PID: $BGPID"
wait $BGPID
echo "Background task completed"

rm /tmp/at-syntax.txt /tmp/at-examples.txt /tmp/at-examples.txt /tmp/run-later.sh /tmp/delayed-task.log /tmp/systemd-run-example.txt 2>/dev/null
echo "Practitioner Lab 12 complete"
```

## 📝 Summary
- `at` schedules one-time jobs; `cron` schedules recurring jobs
- `at now + 5 minutes` runs a job in 5 minutes
- `atq` lists pending jobs; `atrm ID` removes a job
- Common time formats: `at 2pm`, `at midnight`, `at now + 1 hour`
- When `at` is not available, use `(sleep N && command) &` as an alternative
- `systemd-run` is a modern alternative for one-time scheduled tasks
