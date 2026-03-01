# Lab 20: Automation Project — System Health Report

## 🎯 Objective
Build a complete, production-quality system health report script covering hostname, uptime, CPU load, memory, disk, and top processes — all without sudo.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- All previous Practitioner labs
- Foundations Labs 15, 16, 18

## 🔬 Lab Instructions

### Step 1: Plan the Report

```bash
cat > /tmp/health-plan.txt << 'EOF'
System Health Report Sections:
1. System Identity   - hostname, OS, kernel, uptime
2. CPU Load          - load averages, CPU count
3. Memory Usage      - total, used, free, cache
4. Disk Usage        - per-filesystem usage
5. Top Processes     - by CPU and memory
6. Network Summary   - active connections (no sudo)
7. Service Status    - key services
8. Report Summary    - overall health score
EOF
cat /tmp/health-plan.txt
```

### Step 2: Build Helper Functions

```bash
cat > /tmp/health-lib.sh << 'EOF'
#!/bin/bash
# Helper functions for health report

# Color codes
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

# Print section header
section() {
    echo ""
    echo "════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════"
}

# Print key-value pair
kv() {
    printf "  %-25s %s\n" "$1:" "$2"
}

# Format bytes to human readable
human_bytes() {
    local bytes=$1
    if [[ $bytes -ge 1073741824 ]]; then
        printf "%.1f GB" "$(echo "scale=1; $bytes/1073741824" | bc 2>/dev/null || echo $bytes)"
    elif [[ $bytes -ge 1048576 ]]; then
        printf "%.1f MB" "$(echo "scale=1; $bytes/1048576" | bc 2>/dev/null || echo $bytes)"
    else
        printf "%d KB" "$((bytes/1024))"
    fi
}
EOF

source /tmp/health-lib.sh
section "TEST SECTION"
kv "Key" "Value"
echo "Helper functions loaded"
```

### Step 3: System Identity Section

```bash
cat > /tmp/section-identity.sh << 'EOF'
#!/bin/bash
source /tmp/health-lib.sh

section "SYSTEM IDENTITY"
kv "Hostname" "$(hostname)"
kv "FQDN" "$(hostname -f 2>/dev/null || hostname)"
kv "IP Address" "$(hostname -I 2>/dev/null | awk '{print $1}')"
kv "OS" "$(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"
kv "Kernel" "$(uname -r)"
kv "Architecture" "$(uname -m)"
kv "Uptime" "$(uptime -p)"
kv "Users Logged In" "$(who | wc -l)"
kv "Report Generated" "$(date '+%Y-%m-%d %H:%M:%S %Z')"
EOF

bash /tmp/section-identity.sh
```

### Step 4: CPU and Load Section

```bash
cat > /tmp/section-cpu.sh << 'EOF'
#!/bin/bash
source /tmp/health-lib.sh

section "CPU & LOAD AVERAGE"

CPU_COUNT=$(grep -c "^processor" /proc/cpuinfo)
MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
LOAD=$(cat /proc/loadavg)
LOAD1=$(echo $LOAD | cut -d' ' -f1)
LOAD5=$(echo $LOAD | cut -d' ' -f2)
LOAD15=$(echo $LOAD | cut -d' ' -f3)
PROCS=$(echo $LOAD | cut -d' ' -f4)

kv "CPU Model" "$MODEL"
kv "CPU Count" "$CPU_COUNT cores"
kv "Load (1m/5m/15m)" "$LOAD1 / $LOAD5 / $LOAD15"
kv "Running/Total Procs" "$PROCS"

# Check load warning
LOAD_INT=${LOAD1%.*}
if [[ $LOAD_INT -gt $((CPU_COUNT * 2)) ]]; then
    echo "  ⚠️  HIGH LOAD: $LOAD1 on $CPU_COUNT CPU(s)"
fi
EOF

bash /tmp/section-cpu.sh
```

### Step 5: Memory Section

```bash
cat > /tmp/section-memory.sh << 'EOF'
#!/bin/bash
source /tmp/health-lib.sh

section "MEMORY USAGE"

MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_FREE=$(grep MemFree /proc/meminfo | awk '{print $2}')
MEM_AVAIL=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
MEM_CACHED=$(grep "^Cached:" /proc/meminfo | awk '{print $2}')
MEM_BUFFERS=$(grep "^Buffers:" /proc/meminfo | awk '{print $2}')
SWAP_TOTAL=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
SWAP_FREE=$(grep SwapFree /proc/meminfo | awk '{print $2}')

MEM_USED=$(( MEM_TOTAL - MEM_AVAIL ))
MEM_PCT=$(( (MEM_USED * 100) / MEM_TOTAL ))

kv "Total Memory" "$(( MEM_TOTAL / 1024 )) MB"
kv "Used Memory" "$(( MEM_USED / 1024 )) MB ($MEM_PCT%)"
kv "Available" "$(( MEM_AVAIL / 1024 )) MB"
kv "Cached/Buffers" "$(( MEM_CACHED / 1024 )) MB / $(( MEM_BUFFERS / 1024 )) MB"
kv "Swap Total" "$(( SWAP_TOTAL / 1024 )) MB"
kv "Swap Free" "$(( SWAP_FREE / 1024 )) MB"

[[ $MEM_PCT -gt 90 ]] && echo "  ⚠️  HIGH MEMORY: ${MEM_PCT}% used"
EOF

bash /tmp/section-memory.sh
```

### Step 6: Disk Section

```bash
cat > /tmp/section-disk.sh << 'EOF'
#!/bin/bash
source /tmp/health-lib.sh

section "DISK USAGE"

printf "  %-25s %6s %6s %6s %5s\n" "Filesystem" "Size" "Used" "Avail" "Use%"
printf "  %s\n" "$(printf '%.0s-' {1..55})"

df -h | grep -v tmpfs | grep -v "^Filesystem" | while read fs size used avail pct mount; do
    PCT_INT=${pct//%/}
    WARN=""
    [[ $PCT_INT -ge 90 ]] && WARN=" ⚠️  CRITICAL"
    [[ $PCT_INT -ge 80 && $PCT_INT -lt 90 ]] && WARN=" ⚠️  WARNING"
    printf "  %-25s %6s %6s %6s %5s%s\n" "$mount" "$size" "$used" "$avail" "$pct" "$WARN"
done
EOF

bash /tmp/section-disk.sh
```

### Step 7: Top Processes Section

```bash
cat > /tmp/section-processes.sh << 'EOF'
#!/bin/bash
source /tmp/health-lib.sh

section "TOP PROCESSES"

echo "  --- By CPU ---"
printf "  %-6s %-20s %6s %6s\n" "PID" "Command" "CPU%" "MEM%"
ps aux --sort=-%cpu | grep -v "^USER" | head -6 | awk '{ printf "  %-6s %-20s %6s %6s\n", $2, substr($11,1,20), $3, $4 }'

echo ""
echo "  --- By Memory ---"
printf "  %-6s %-20s %6s %6s\n" "PID" "Command" "MEM%" "RSS(KB)"
ps aux --sort=-%mem | grep -v "^USER" | head -6 | awk '{ printf "  %-6s %-20s %6s %6s\n", $2, substr($11,1,20), $4, $6 }'
EOF

bash /tmp/section-processes.sh
```

### Step 8: Assemble the Full Report

```bash
cat > /tmp/system-health-report.sh << 'EOF'
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
REPORT_FILE="/tmp/health-report-$(date +%Y%m%d-%H%M%S).txt"

# Run each section and capture output
{
    echo "SYSTEM HEALTH REPORT"
    echo "Generated: $(date)"
    echo "=========================================="
    bash /tmp/section-identity.sh
    bash /tmp/section-cpu.sh
    bash /tmp/section-memory.sh
    bash /tmp/section-disk.sh
    bash /tmp/section-processes.sh
    echo ""
    echo "=========================================="
    echo "Report complete"
} | tee "$REPORT_FILE"

echo ""
echo "Report saved to: $REPORT_FILE"
EOF

bash /tmp/system-health-report.sh
```

## ✅ Verification

```bash
echo "=== Report file created ==="
ls -la /tmp/health-report-*.txt 2>/dev/null | head -3

echo ""
echo "=== Report line count ==="
wc -l /tmp/health-report-*.txt 2>/dev/null | head -1

# Cleanup
rm /tmp/health-lib.sh /tmp/section-*.sh /tmp/system-health-report.sh /tmp/health-plan.txt 2>/dev/null
rm /tmp/health-report-*.txt 2>/dev/null
echo "Practitioner Lab 20 complete"
```

## 📝 Summary
- Modular scripts with helper functions improve readability and reuse
- Source helper libraries with `source file.sh` to share functions
- Use `/proc/meminfo` and `/proc/loadavg` for resource data without sudo
- `df -h | grep -v tmpfs` shows only real filesystems
- `ps aux --sort=-%cpu | head -6` shows top CPU consumers
- Combine all sections with `{ cmd1; cmd2; } | tee report.txt` for logging
- Always use `set -euo pipefail` in production automation scripts
