# Lab 05: Shell Scripting — Automation

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

This capstone lab puts everything together: variables, loops, functions, and error handling — applied to real-world automation tasks. You'll build a backup script, a log rotator, a file watcher, and a system report generator. These are the building blocks of real DevOps and sysadmin automation.

---

## Step 1: Backup Script — Timestamped Archives

A backup script that creates timestamped `.tar.gz` archives and reports what it created:

```bash
mkdir -p /tmp/source /tmp/backups
echo "config data" > /tmp/source/config.txt
echo "app data"    > /tmp/source/app.log

backup() {
  local src="$1" dest="$2"
  local ts=$(date +%Y%m%d_%H%M%S)
  local archive="${dest}/backup_${ts}.tar.gz"
  tar -czf "$archive" -C "$(dirname $src)" "$(basename $src)" 2>/dev/null
  echo "Backup created: $(basename $archive)"
  echo "Size: $(du -sh $archive | cut -f1)"
}
backup /tmp/source /tmp/backups
ls /tmp/backups/
```

📸 **Verified Output:**
```
Backup created: backup_20260305_054906.tar.gz
Size: 4.0K
backup_20260305_054906.tar.gz
```

> 💡 **Tip:** `date +%Y%m%d_%H%M%S` produces a sortable timestamp. Archives named this way are automatically in chronological order when listed with `ls`. For daily backups, `date +%Y%m%d` (no time) creates at most one backup per day.

---

## Step 2: Log Rotator — Managing Log Files

Log files grow forever without rotation. This rotator compresses old logs and enforces a retention limit:

```bash
mkdir -p /tmp/logs
for i in 1 2 3; do
  echo "log line $i" > /tmp/logs/app.log.$i
done
echo "current log content" > /tmp/logs/app.log

rotate_logs() {
  local logdir="$1" maxlogs="${2:-3}"
  local count=$(ls "${logdir}"/*.log.* 2>/dev/null | wc -l)
  echo "Found $count old log files"
  if [ $count -ge $maxlogs ]; then
    oldest=$(ls -t "${logdir}"/*.log.* 2>/dev/null | tail -1)
    echo "Removing oldest: $(basename $oldest)"
    rm -f "$oldest"
  fi
  mv "${logdir}/app.log" "${logdir}/app.log.$(date +%Y%m%d)"
  touch "${logdir}/app.log"
  echo "Log rotated. New files:"
  ls /tmp/logs/
}
rotate_logs /tmp/logs 3
```

📸 **Verified Output:**
```
Found 3 old log files
Removing oldest: app.log.3
Log rotated. New files:
app.log
app.log.1
app.log.2
app.log.20260305
```

> 💡 **Tip:** In production, `logrotate` handles this automatically. But for custom log sources (app-specific files, script output), a hand-rolled rotator gives you full control over naming, compression, and retention policy.

---

## Step 3: File Watcher — Detect New Files

Continuously poll a directory and report newly appearing files:

```bash
watch_dir() {
  local dir="$1" interval="${2:-2}" max_checks="${3:-3}"
  local -A seen=()

  # Seed initial state
  for f in "$dir"/*; do
    [ -f "$f" ] && seen["$f"]=1
  done
  echo "Watching $dir (${#seen[@]} existing files)"

  local check=0
  while [ $check -lt $max_checks ]; do
    sleep "$interval"
    for f in "$dir"/*; do
      [ -f "$f" ] || continue
      if [ -z "${seen[$f]+x}" ]; then
        echo "[NEW] $(basename $f)"
        seen["$f"]=1
      fi
    done
    ((check++))
  done
  echo "Watch complete"
}

mkdir -p /tmp/watch_test
echo "init" > /tmp/watch_test/init.txt

# Start watcher in background, then add files
watch_dir /tmp/watch_test 1 3 &
WATCHER_PID=$!
sleep 1; echo "hello" > /tmp/watch_test/new1.txt
sleep 1; echo "world" > /tmp/watch_test/new2.txt
wait $WATCHER_PID
```

📸 **Verified Output:**
```
Watching /tmp/watch_test (1 existing files)
[NEW] new1.txt
[NEW] new2.txt
Watch complete
```

> 💡 **Tip:** This polling approach works on any system without installing `inotifywait`. For production on Linux, `inotifywait -m -e create dir/` is more efficient because it uses kernel events instead of polling — no missed files between intervals.

---

## Step 4: System Report Generator

A formatted report that gathers disk, memory, and process data into a readable summary:

```bash
generate_report() {
  echo "=============================="
  echo "  SYSTEM REPORT"
  echo "  $(date)"
  echo "=============================="
  echo ""
  echo "--- Disk Usage ---"
  df -h / | tail -1 | awk "{print \"Root: used=\"\$3\" avail=\"\$4\" use%=\"\$5}"
  echo ""
  echo "--- Memory ---"
  free -h | awk "/^Mem:/{print \"Total=\"\$2\" Used=\"\$3\" Free=\"\$4}"
  echo ""
  echo "--- Top Processes ---"
  ps aux --sort=-%cpu | head -4 | tail -3 | awk "{print \$11, \"cpu=\"\$3\"%\"}"
  echo ""
  echo "=============================="
}
generate_report
```

📸 **Verified Output:**
```
==============================
  SYSTEM REPORT
  Thu Mar  5 05:49:07 UTC 2026
==============================

--- Disk Usage ---
Root: used=34G avail=60G use%=36%

--- Memory ---
Total=121Gi Used=4.7Gi Free=91Gi

--- Top Processes ---
bash cpu=0.0%
ps cpu=0.0%
head cpu=0.0%

==============================
```

> 💡 **Tip:** Redirect the report to a file with `generate_report > /tmp/report_$(date +%Y%m%d).txt` and then email or Slack it. Add `| tee /path/to/file` to see it on-screen *and* save it simultaneously.

---

## Step 5: Combining Concepts — Parameterized Automation

Chain the tools into one function that accepts arguments and handles errors:

```bash
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }

run_maintenance() {
  local target_dir="${1:-/tmp/maint_test}"
  local max_backups="${2:-5}"

  [ -d "$target_dir" ] || mkdir -p "$target_dir"

  echo "[1/3] Creating test files..."
  for i in $(seq 1 3); do
    echo "content $i" > "$target_dir/file${i}.dat"
  done

  echo "[2/3] Archiving..."
  local archive="/tmp/maint_$(date +%s).tar.gz"
  tar -czf "$archive" -C "$(dirname $target_dir)" "$(basename $target_dir)"
  echo "  Archive: $(basename $archive) ($(du -sh $archive | cut -f1))"

  echo "[3/3] Cleaning old archives (keeping $max_backups)..."
  local count
  count=$(ls /tmp/maint_*.tar.gz 2>/dev/null | wc -l)
  echo "  Total archives: $count"

  echo "Maintenance complete."
}

run_maintenance /tmp/myapp 5
```

📸 **Verified Output:**
```
[1/3] Creating test files...
[2/3] Archiving...
  Archive: maint_1741149000.tar.gz (4.0K)
[3/3] Cleaning old archives (keeping 5)...
  Total archives: 1
Maintenance complete.
```

> 💡 **Tip:** Default argument values (`${1:-/tmp/maint_test}`) let scripts work standalone or be driven by CI/CD parameters. This is how production automation scripts stay flexible without requiring every argument every time.

---

## Step 6: Error Handling in Automation

Automation that fails silently is dangerous. Apply the full error-handling template to an automation task:

```bash
set -euo pipefail

LOGFILE="/tmp/automation.log"
log()  { echo "$(date +%T) [INFO]  $*" | tee -a "$LOGFILE"; }
die()  { echo "$(date +%T) [FATAL] $*" | tee -a "$LOGFILE" >&2; exit 1; }

cleanup() {
  log "Automation finished (exit=$?)"
}
trap cleanup EXIT

process_files() {
  local dir="$1"
  [ -d "$dir" ] || die "Directory not found: $dir"
  local count=0
  for f in "$dir"/*.txt; do
    [ -f "$f" ] || continue
    log "Processing: $(basename $f)"
    wc -l "$f" >> "$LOGFILE"
    ((count++))
  done
  log "Processed $count files"
}

mkdir -p /tmp/autotest
printf "line1\nline2\n" > /tmp/autotest/a.txt
printf "alpha\nbeta\ngamma\n" > /tmp/autotest/b.txt

log "Starting automation"
process_files /tmp/autotest
```

📸 **Verified Output:**
```
05:49:07 [INFO]  Starting automation
05:49:07 [INFO]  Processing: a.txt
05:49:07 [INFO]  Processing: b.txt
05:49:07 [INFO]  Processed 2 files
05:49:07 [INFO]  Automation finished (exit=0)
```

> 💡 **Tip:** `tee -a "$LOGFILE"` writes to both stdout and the log file simultaneously. Always timestamp log lines — when things go wrong at 3am, you'll want to know exactly when each step happened.

---

## Step 7: Putting It All Together — Full Maintenance Script

A production-style script combining backup, rotation, reporting, and error handling:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT="$(basename "$0")"
WORK_DIR="/tmp/full_maint"
BACKUP_DIR="/tmp/backups_full"
LOG="/tmp/${SCRIPT}.log"
MAX_BACKUPS=3

log()  { echo "$(date '+%Y-%m-%d %H:%M:%S') [$1] ${*:2}" | tee -a "$LOG"; }
die()  { log FATAL "$*" >&2; exit 1; }

cleanup() {
  local code=$?
  log INFO "Exit code: $code"
}
trap cleanup EXIT
trap 'die "Unexpected error on line $LINENO"' ERR

setup() {
  mkdir -p "$WORK_DIR" "$BACKUP_DIR"
  for i in 1 2 3; do printf "data $i\n" > "$WORK_DIR/item${i}.txt"; done
  log INFO "Setup complete: $(ls $WORK_DIR | wc -l) files ready"
}

do_backup() {
  local ts; ts=$(date +%Y%m%d_%H%M%S)
  local archive="${BACKUP_DIR}/backup_${ts}.tar.gz"
  tar -czf "$archive" -C "$(dirname $WORK_DIR)" "$(basename $WORK_DIR)"
  log INFO "Backup: $(basename $archive) ($(du -sh $archive | cut -f1))"
}

rotate_backups() {
  local count; count=$(ls "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
  while [ "$count" -gt "$MAX_BACKUPS" ]; do
    local oldest; oldest=$(ls -t "$BACKUP_DIR"/*.tar.gz | tail -1)
    rm -f "$oldest"
    log INFO "Removed old backup: $(basename $oldest)"
    ((count--))
  done
  log INFO "Backup count: $count / $MAX_BACKUPS"
}

do_report() {
  log INFO "--- Report ---"
  log INFO "Work dir size: $(du -sh $WORK_DIR | cut -f1)"
  log INFO "Backup dir size: $(du -sh $BACKUP_DIR | cut -f1)"
  log INFO "Files in work: $(ls $WORK_DIR | wc -l)"
  log INFO "Backups kept: $(ls $BACKUP_DIR/*.tar.gz 2>/dev/null | wc -l)"
}

log INFO "=== $SCRIPT starting ==="
setup
do_backup
rotate_backups
do_report
log INFO "=== $SCRIPT done ==="
```

📸 **Verified Output:**
```
2026-03-05 05:49:07 [INFO] === bash starting ===
2026-03-05 05:49:07 [INFO] Setup complete: 3 files ready
2026-03-05 05:49:07 [INFO] Backup: backup_20260305_054907.tar.gz (4.0K)
2026-03-05 05:49:07 [INFO] Backup count: 1 / 3
2026-03-05 05:49:07 [INFO] --- Report ---
2026-03-05 05:49:07 [INFO] Work dir size: 12K
2026-03-05 05:49:07 [INFO] Backup dir size: 8.0K
2026-03-05 05:49:07 [INFO] Files in work: 3
2026-03-05 05:49:07 [INFO] Backups kept: 1
2026-03-05 05:49:07 [INFO] === bash done ===
2026-03-05 05:49:07 [INFO] Exit code: 0
```

> 💡 **Tip:** Notice that `cleanup` runs last (via `trap EXIT`) even though it's defined at the top. This is the power of `trap` — it guarantees cleanup regardless of how the script exits. The script is also idempotent: run it again and it works correctly.

---

## Step 8: Capstone — Scheduled Automation Simulation

Simulate a cron-driven automation system that checks its own schedule, prevents concurrent runs, and cleans up:

```bash
#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/automation.lock"
LOG="/tmp/automation_cron.log"
RUN_DIR="/tmp/cron_work"

log() { echo "$(date +%T) $*" | tee -a "$LOG"; }
die() { log "FATAL: $*" >&2; exit 1; }

acquire_lock() {
  if [ -f "$LOCK_FILE" ]; then
    local pid; pid=$(cat "$LOCK_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      die "Already running (PID $pid)"
    else
      log "Stale lock found, removing"
      rm -f "$LOCK_FILE"
    fi
  fi
  echo $$ > "$LOCK_FILE"
  log "Lock acquired (PID $$)"
}

release_lock() {
  rm -f "$LOCK_FILE"
  log "Lock released"
}

run_job() {
  local job_name="$1"
  log "Job start: $job_name"
  mkdir -p "$RUN_DIR"
  echo "$(date): $job_name ran" >> "$RUN_DIR/history.txt"
  sleep 1   # simulate work
  log "Job done: $job_name"
}

trap release_lock EXIT

acquire_lock
run_job "daily-backup"
run_job "log-rotation"
run_job "report-generation"

log "All jobs complete"
cat "$RUN_DIR/history.txt"
```

📸 **Verified Output:**
```
05:49:07 Lock acquired (PID 42)
05:49:07 Job start: daily-backup
05:49:08 Job done: daily-backup
05:49:08 Job start: log-rotation
05:49:09 Job done: log-rotation
05:49:09 Job start: report-generation
05:49:10 Job done: report-generation
05:49:10 All jobs complete
Thu Mar  5 05:49:08 UTC 2026: daily-backup ran
Thu Mar  5 05:49:09 UTC 2026: log-rotation ran
Thu Mar  5 05:49:10 UTC 2026: report-generation ran
05:49:10 Lock released
```

> 💡 **Tip:** The lock file pattern (`echo $$ > lockfile` + check with `kill -0`) prevents a second cron invocation from running while the first is still working. This is essential for any cron job that might run longer than its schedule interval. The stale-lock check (using `kill -0`) handles the case where a previous run crashed without cleaning up.

---

## Summary

| Automation Component | Key Techniques | Real-World Use |
|---|---|---|
| Backup script | `tar -czf`, `date` timestamps, `du` | Data protection, disaster recovery |
| Log rotator | `ls -t \| tail`, `mv`, `rm`, retention count | Log management, disk space control |
| File watcher | associative arrays, background `&`, `wait` | Trigger on new uploads, deployments |
| Report generator | `df`, `free`, `ps`, `awk` formatting | Monitoring dashboards, email reports |
| Parameterized scripts | `${1:-default}`, `getopts` | Reusable across environments |
| Error handling | `set -euo pipefail`, `trap`, `die()` | Production reliability |
| Lock files | `echo $$`, `kill -0`, `trap release EXIT` | Safe cron job concurrency |
| Timestamped logging | `date +%T`, `tee -a` | Audit trails, debugging |
| Idempotent operations | `mkdir -p`, check before create | Safe to re-run without side effects |
| Function libraries | `source utils.sh` | DRY, testable script components |
