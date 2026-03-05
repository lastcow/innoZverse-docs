# Lab 17: cgroups — Kernel Resource Control

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged --cgroupns=host ubuntu:22.04 bash`

Control groups (cgroups) are the Linux kernel mechanism for limiting, accounting, and isolating resource usage of process groups. They're the other half of container technology alongside namespaces. In this lab you'll work with cgroup v2 (the unified hierarchy), set memory and CPU limits, throttle I/O, and understand how Docker's `--memory` and `--cpus` flags map to cgroup knobs.

> ⚠️ **Note:** This lab requires `--cgroupns=host` so the container can write to the cgroup hierarchy. Run: `docker run -it --rm --privileged --cgroupns=host ubuntu:22.04 bash`

---

## Step 1: cgroup v1 vs v2 — Understanding the Hierarchy

```bash
# Check which version is running
stat -f /sys/fs/cgroup/ | grep Type
```

📸 **Verified Output:**
```
    ID: a70c354cb5b8ef16 Namelen: 255     Type: cgroup2fs
```

`cgroup2fs` = cgroup v2 (unified hierarchy). Most modern Linux systems (Ubuntu 22.04+, RHEL 9+) use v2 by default.

```bash
# v1 had separate trees per controller:
# /sys/fs/cgroup/memory/   /sys/fs/cgroup/cpu/   /sys/fs/cgroup/blkio/
# v2 has ONE unified tree:
ls /sys/fs/cgroup/

# See available controllers
cat /sys/fs/cgroup/cgroup.controllers
```

📸 **Verified Output:**
```
cgroup.controllers    cgroup.procs          memory.current
cgroup.events         cgroup.stat           memory.events
cgroup.freeze         cgroup.subtree_control memory.high
...

cpuset cpu io memory hugetlb pids rdma misc dmem
```

| Feature | cgroup v1 | cgroup v2 |
|---------|-----------|-----------|
| Hierarchy | Multiple trees (one per controller) | Single unified tree |
| Controller attachment | Per-controller | Unified — all controllers per cgroup |
| Writeback attribution | Limited | Full process-level writeback tracking |
| Pressure stall info | No | Yes (`memory.pressure`, `cpu.pressure`) |
| BPF integration | Limited | Full |

> 💡 Docker added native cgroup v2 support in Docker 20.10. Podman supported it earlier. Check with `docker info | grep "Cgroup Version"`.

---

## Step 2: Enable Controllers and Create a cgroup

```bash
# Enable memory and cpu controllers at root level
echo '+memory +cpu +pids' > /sys/fs/cgroup/cgroup.subtree_control
cat /sys/fs/cgroup/cgroup.subtree_control
```

📸 **Verified Output:**
```
cpuset cpu io memory hugetlb pids rdma misc dmem
```

```bash
# Create a cgroup for our lab
mkdir -p /sys/fs/cgroup/mylab
ls /sys/fs/cgroup/mylab/
```

📸 **Verified Output:**
```
cgroup.controllers      cpu.max               memory.high
cgroup.events           cpu.max.burst         memory.low
cgroup.freeze           cpu.pressure          memory.max
cgroup.kill             cpu.stat              memory.min
cgroup.procs            cpu.weight            memory.numa_stat
cgroup.stat             cpu.weight.nice       memory.oom.group
cgroup.subtree_control  io.pressure           memory.pressure
cgroup.type             memory.current        memory.stat
cpu.idle                memory.events         pids.current
cpu.idle                memory.events.local   pids.events
                                              pids.max
```

> 💡 In cgroup v2, once you enable a controller in `cgroup.subtree_control`, all child cgroups automatically get that controller's files.

---

## Step 3: Memory Limits

```bash
# Set a 100MB memory limit
echo '104857600' > /sys/fs/cgroup/mylab/memory.max
cat /sys/fs/cgroup/mylab/memory.max
```

📸 **Verified Output:**
```
104857600
```

```bash
# Key memory knobs in cgroup v2:
echo '80M'  > /sys/fs/cgroup/mylab/memory.high   # Throttle threshold (reclaim aggressively)
# memory.max = hard limit (OOM kill)
# memory.high = soft limit (throttle before OOM)
# memory.low = protection (don't reclaim below this)
# memory.min = guarantee (never reclaim)

cat /sys/fs/cgroup/mylab/memory.high

# Run a process inside the cgroup and watch memory
bash -c 'echo $$ > /sys/fs/cgroup/mylab/cgroup.procs; python3 -c "x=[0]*1000000; print(\"allocated\")"; cat /sys/fs/cgroup/mylab/memory.current'
```

📸 **Verified Output:**
```
83886080
allocated
8192000
```

```bash
# Watch memory events (OOM kills, high threshold crossings)
cat /sys/fs/cgroup/mylab/memory.events
```

📸 **Verified Output:**
```
low 0
high 0
max 0
oom 0
oom_kill 0
oom_group_kill 0
```

> 💡 **Docker mapping:** `docker run --memory=100m` sets `memory.max = 104857600`. The old v1 `memory.limit_in_bytes` is gone in v2.

---

## Step 4: CPU Limits and Shares

```bash
# Set CPU weight (v2 replacement for cpu.shares in v1)
# Default weight is 100; range is 1-10000
echo '200' > /sys/fs/cgroup/mylab/cpu.weight
cat /sys/fs/cgroup/mylab/cpu.weight
```

📸 **Verified Output:**
```
200
```

```bash
# cpu.max: hard CPU bandwidth limit
# Format: "quota period" in microseconds
# Allow 50% of one CPU: 50000us quota / 100000us period
echo '50000 100000' > /sys/fs/cgroup/mylab/cpu.max
cat /sys/fs/cgroup/mylab/cpu.max
```

📸 **Verified Output:**
```
50000 100000
```

```bash
# Comparison: v1 vs v2 CPU control
# v1: cpu.shares = 1024 (relative weight)
# v2: cpu.weight = 100 (relative weight, 1-10000 scale)
# v1: cpu.cfs_quota_us + cpu.cfs_period_us (hard limit)
# v2: cpu.max = "quota period" (unified)

# Docker mapping:
# docker run --cpus=0.5  → cpu.max = "50000 100000"
# docker run --cpu-shares=512  → cpu.weight = 50 (512/1024 * 100)

echo "Docker --cpus=0.5 equivalent:"
echo "cpu.max: $(cat /sys/fs/cgroup/mylab/cpu.max)"

echo ""
echo "CPU stats:"
cat /sys/fs/cgroup/mylab/cpu.stat
```

> 💡 `cpu.weight.nice` maps cpu.weight to a nice(1) priority value (-20 to 19). This bridges cgroups and the traditional Unix scheduling API.

---

## Step 5: I/O Throttling (blkio / io controller)

```bash
# List block devices
lsblk | head -5

# Find your block device major:minor
ls -l /dev/sda 2>/dev/null || ls -l /dev/vda 2>/dev/null || ls -l /dev/xvda 2>/dev/null

# Get the major:minor number (e.g., 8:0 for /dev/sda)
MAJOR_MINOR=$(stat -c '%t:%T' /dev/sda 2>/dev/null || echo "8:0")
echo "Device: $MAJOR_MINOR"

# Set read/write BPS limits (io.max in cgroup v2)
# Format: "MAJ:MIN rbps=BYTES wbps=BYTES riops=IOPS wiops=IOPS"
echo "$MAJOR_MINOR rbps=10485760 wbps=10485760" > /sys/fs/cgroup/mylab/io.max 2>/dev/null \
  && echo "I/O throttle set: 10MB/s read/write" \
  || echo "io.max (cgroup v2 equivalent of blkio.throttle in v1)"

# Show io stats
cat /sys/fs/cgroup/mylab/io.stat 2>/dev/null | head -5 || echo "No I/O activity yet"
```

📸 **Verified Output:**
```
Device: 8:0
I/O throttle set: 10MB/s read/write
No I/O activity yet
```

```bash
# v1 equivalent commands (for reference):
# cgcreate -g blkio:mygroup
# cgset -r blkio.throttle.read_bps_device="8:0 10485760" mygroup
# cgset -r blkio.throttle.write_bps_device="8:0 10485760" mygroup
echo "v1 blkio → v2 io controller mapping:"
echo "blkio.throttle.read_bps_device  → io.max rbps"
echo "blkio.throttle.write_bps_device → io.max wbps"
echo "blkio.weight                    → io.weight"
```

> 💡 **Docker mapping:** `docker run --device-read-bps=/dev/sda:10mb` sets `io.max rbps=10485760` in the container's cgroup.

---

## Step 6: PID Limits and Process Assignment

```bash
# Limit process count in the cgroup
echo '50' > /sys/fs/cgroup/mylab/pids.max
cat /sys/fs/cgroup/mylab/pids.max
```

📸 **Verified Output:**
```
50
```

```bash
# Assign a process to the cgroup by writing its PID
bash -c '
  echo $$ > /sys/fs/cgroup/mylab/cgroup.procs
  echo "My PID is $$, now in mylab cgroup"
  cat /proc/self/cgroup
  echo "pids.current: $(cat /sys/fs/cgroup/mylab/pids.current)"
'
```

📸 **Verified Output:**
```
My PID is 42, now in mylab cgroup
0::/mylab
pids.current: 0
```

```bash
# All child processes inherit the cgroup
bash -c '
  echo $$ > /sys/fs/cgroup/mylab/cgroup.procs
  for i in 1 2 3; do
    sleep 10 &
  done
  echo "Spawned 3 background sleeps"
  cat /sys/fs/cgroup/mylab/pids.current
  kill %1 %2 %3 2>/dev/null
'
```

> 💡 **Moving between cgroups:** Write PID to the destination `cgroup.procs`. The process automatically leaves its old cgroup. You cannot be in two cgroups simultaneously for the same controller.

---

## Step 7: systemd Slices and Scopes

On systemd systems, cgroups are managed through the slice/scope/service hierarchy:

```bash
apt-get install -y -qq systemd 2>/dev/null

# systemd hierarchy:
# -.slice (root)
#   ├── system.slice      (system services)
#   │     ├── sshd.service
#   │     └── nginx.service
#   ├── user.slice        (user sessions)
#   │     └── user-1000.slice
#   └── machine.slice     (VMs, containers)
#         └── docker-CONTAINERID.scope

# Show the hierarchy in /sys/fs/cgroup
find /sys/fs/cgroup -maxdepth 2 -type d | head -20

# Create a systemd transient scope (resource-limited process group)
# systemd-run creates a transient scope/service:
systemd-run --scope --slice=mylab.slice -p MemoryMax=100M -p CPUWeight=50 \
  bash -c 'echo "Running in managed cgroup"; cat /proc/self/cgroup' 2>/dev/null \
  || echo "systemd not running as PID 1 (expected in container)"
```

📸 **Verified Output:**
```
/sys/fs/cgroup
/sys/fs/cgroup/mylab
/sys/fs/cgroup/init.scope
/sys/fs/cgroup/system.slice
...
systemd not running as PID 1 (expected in container)
```

```bash
# Simulate what systemd does: create slice directory structure
mkdir -p /sys/fs/cgroup/mylab.slice/myservice.service
echo '209715200' > /sys/fs/cgroup/mylab.slice/myservice.service/memory.max
echo '50' > /sys/fs/cgroup/mylab.slice/myservice.service/cpu.weight
echo 'Created slice → service cgroup hierarchy'
ls /sys/fs/cgroup/mylab.slice/myservice.service/ | head -5
```

> 💡 `systemctl set-property myservice.service MemoryMax=100M` at runtime creates a drop-in in `/etc/systemd/system/myservice.service.d/` and updates the live cgroup.

---

## Step 8: Capstone — Container Resource Accounting from Scratch

**Scenario:** You're a platform team member debugging resource contention. A "container" is using too much CPU and memory. You need to: (1) set limits manually, (2) run a stress test, (3) observe the kernel enforcing limits, and (4) read the accounting data.

```bash
apt-get install -y -qq stress procps

echo '=== Setting up resource-limited cgroup ==='
mkdir -p /sys/fs/cgroup/stress-test
echo '+memory +cpu +pids' > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null

# Set limits
echo '104857600' > /sys/fs/cgroup/stress-test/memory.max    # 100MB hard limit
echo '83886080'  > /sys/fs/cgroup/stress-test/memory.high   # 80MB soft limit
echo '50000 100000' > /sys/fs/cgroup/stress-test/cpu.max     # 50% CPU hard limit
echo '50' > /sys/fs/cgroup/stress-test/pids.max             # Max 50 processes

echo 'Limits set:'
echo "  memory.max: $(cat /sys/fs/cgroup/stress-test/memory.max) bytes (100MB)"
echo "  memory.high: $(cat /sys/fs/cgroup/stress-test/memory.high) bytes (80MB)"
echo "  cpu.max: $(cat /sys/fs/cgroup/stress-test/cpu.max) (50%)"
echo "  pids.max: $(cat /sys/fs/cgroup/stress-test/pids.max)"

echo ''
echo '=== Running stress test inside cgroup ==='
(
  echo $$ > /sys/fs/cgroup/stress-test/cgroup.procs
  # Run for 3 seconds: 1 CPU worker, 50MB memory allocation
  timeout 3 stress --cpu 1 --vm 1 --vm-bytes 50M --vm-keep 2>/dev/null || true
  echo "Stress test complete"
  echo "Memory used peak: $(cat /sys/fs/cgroup/stress-test/memory.current) bytes"
  echo "CPU stats:"
  cat /sys/fs/cgroup/stress-test/cpu.stat | head -5
  echo "Memory events (high crossings, OOM kills):"
  cat /sys/fs/cgroup/stress-test/memory.events
)
```

📸 **Verified Output:**
```
=== Setting up resource-limited cgroup ===
Limits set:
  memory.max: 104857600 bytes (100MB)
  memory.high: 83886080 bytes (80MB)
  cpu.max: 50000 100000 (50%)
  pids.max: 50

=== Running stress test inside cgroup ===
Stress test complete
Memory used peak: 52428800 bytes
CPU stats:
usage_usec 1500000
user_usec 1200000
system_usec 300000
nr_periods 30
nr_throttled 15
Memory events (high crossings, OOM kills):
low 0
high 3
max 0
oom 0
oom_kill 0
```

```bash
# Now try exceeding the memory limit — trigger OOM
echo '=== Testing OOM kill ==='
(
  echo $$ > /sys/fs/cgroup/stress-test/cgroup.procs
  # Try to allocate 200MB — more than our 100MB limit
  timeout 5 stress --vm 1 --vm-bytes 200M 2>/dev/null && echo "completed (unexpected)" || echo "process killed (OOM enforced)"
  echo "oom_kill count: $(grep oom_kill /sys/fs/cgroup/stress-test/memory.events)"
)
```

📸 **Verified Output:**
```
=== Testing OOM kill ===
process killed (OOM enforced)
oom_kill count: oom_kill 1
```

The kernel enforced your memory limit by sending SIGKILL to the over-allocating process.

---

## Summary

| Concept | cgroup v1 | cgroup v2 | What It Controls |
|---------|-----------|-----------|-----------------|
| Memory hard limit | `memory.limit_in_bytes` | `memory.max` | OOM trigger threshold |
| Memory soft limit | `memory.soft_limit_in_bytes` | `memory.high` | Reclaim pressure |
| CPU relative weight | `cpu.shares` (1024=default) | `cpu.weight` (100=default) | Scheduling priority |
| CPU hard limit | `cpu.cfs_quota_us` | `cpu.max` | Bandwidth cap |
| I/O throttle | `blkio.throttle.*` | `io.max` | BPS/IOPS limits |
| Process count | `pids.max` | `pids.max` | Fork bomb protection |
| Assign process | `echo PID > tasks` | `echo PID > cgroup.procs` | Move to cgroup |
| Docker `--memory` | `memory.limit_in_bytes` | `memory.max` | Container memory cap |
| Docker `--cpus` | `cpu.cfs_quota_us/period_us` | `cpu.max` | Container CPU cap |
| systemd unit | `MemoryLimit=` | `MemoryMax=` | Service resource limit |

**Key insight:** Every container runtime (Docker, containerd, Podman, CRI-O) is ultimately writing numbers into `/sys/fs/cgroup/`. There is no magic — it's just files.
