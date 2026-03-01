# Lab 12: One-Time Scheduling with at

## 🎯 Objective
Schedule one-time tasks using `at`, manage the at queue with `atq` and `atrm`, and understand the `batch` command for load-based execution.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Basic shell knowledge

## 🔬 Lab Instructions

### Step 1: Install at
```bash
sudo apt install -y at
sudo systemctl enable --now atd
systemctl status atd
# ● atd.service - Deferred execution scheduler
#    Active: active (running)
```

### Step 2: Schedule a Simple Task
```bash
echo "echo 'Hello from at' >> /tmp/at_output.log" | at now + 1 minute
# warning: commands will be executed using /bin/sh
# job 1 at Sun Mar  1 06:02:00 2026
```

### Step 3: View the at Queue
```bash
atq
# 1    Sun Mar  1 06:02:00 2026 a ubuntu
```

### Step 4: Inspect a Scheduled Job
```bash
at -c 1
# #!/bin/sh
# ...environment variables...
# echo 'Hello from at' >> /tmp/at_output.log
```

### Step 5: Schedule Using Different Time Formats
```bash
# at accepts many time formats
echo "date >> /tmp/at_output.log" | at 06:30
echo "date >> /tmp/at_output.log" | at noon tomorrow
echo "date >> /tmp/at_output.log" | at now + 2 hours

atq
# 1   ...
# 2   ...
# 3   ...
```

### Step 6: Remove a Scheduled Job
```bash
atq
# 3   Mon Mar  2 12:00:00 2026 a ubuntu

atrm 3
atq
# (job 3 is gone)
```

### Step 7: Use at with a Script File
```bash
cat > /tmp/at_script.sh << 'EOF'
#!/bin/bash
echo "System info at $(date)" >> /tmp/at_output.log
uptime >> /tmp/at_output.log
free -h >> /tmp/at_output.log
EOF

at -f /tmp/at_script.sh now + 1 minute
# job 5 at Sun Mar  1 06:03:00 2026
```

### Step 8: Use batch for Load-Based Scheduling
```bash
# batch runs when system load drops below 1.5
echo "sleep 2 && echo 'batch done' >> /tmp/at_output.log" | batch
# job 6 at Sun Mar  1 06:01:00 2026

atq
# 6   Sun Mar  1 06:01:00 2026 b ubuntu  (note 'b' for batch queue)
```

### Step 9: Wait and Verify Results
```bash
sleep 70
cat /tmp/at_output.log
# Hello from at
# Sun Mar  1 06:02:01 UTC 2026
# System info at Sun Mar  1 06:03:01 UTC 2026
#  06:03:01 up 2 days,  load average: 0.01, 0.01, 0.00
```

### Step 10: Clean Up
```bash
# Remove all remaining at jobs
atq | awk '{print $1}' | xargs -r atrm
atq
# (empty)
rm -f /tmp/at_output.log /tmp/at_script.sh
```

## ✅ Verification
```bash
atq        # should be empty after cleanup
systemctl is-active atd   # active
```

## 📝 Summary
- `at` schedules one-time future commands; `atq` lists; `atrm` removes
- Time formats: `now + N minutes/hours`, `HH:MM`, `noon tomorrow`
- `at -f script.sh` reads commands from a file
- `batch` runs when system load is low (queue type 'b')
- Output from at jobs is emailed by default; redirect to file if needed
