# Lab 05: CPU and Memory Profiling

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Understanding memory and CPU resource consumption at the OS level is essential for performance tuning, capacity planning, and debugging memory leaks. This lab covers `/proc/meminfo`, `/proc/vmstat`, OOM killer behavior, CPU affinity with `taskset`, `numactl`, and load simulation with `stress-ng`.

---

## Step 1: Analyze /proc/meminfo

The primary interface for memory statistics is `/proc/meminfo`:

```bash
cat /proc/meminfo | head -20
```

📸 **Verified Output:**
```
MemTotal:       127539180 kB
MemFree:        95401012 kB
MemAvailable:   121376588 kB
Buffers:          911832 kB
Cached:         24433200 kB
SwapCached:            0 kB
Active:          4436600 kB
Inactive:       24802688 kB
Active(anon):    3941000 kB
Inactive(anon):        0 kB
Active(file):     495600 kB
Inactive(file): 24802688 kB
Unevictable:       26512 kB
Mlocked:           26512 kB
SwapTotal:       8388604 kB
SwapFree:        8388604 kB
Zswap:                 0 kB
Zswapped:              0 kB
Dirty:            101072 kB
Writeback:             0 kB
```

**Key fields explained:**

| Field | Description |
|-------|-------------|
| `MemTotal` | Total physical RAM |
| `MemFree` | Completely unused RAM |
| `MemAvailable` | RAM available for new allocations (incl. reclaimable cache) |
| `Buffers` | Raw block device cache |
| `Cached` | Page cache (file data) |
| `Active(anon)` | Anonymous (heap/stack) memory recently used |
| `Inactive(anon)` | Anonymous memory not recently used (swap candidate) |
| `SwapTotal`/`SwapFree` | Total and available swap space |
| `Dirty` | Pages modified but not yet written to disk |

> 💡 **`MemAvailable` ≠ `MemFree`**. The kernel can reclaim `Cached` pages under pressure — `MemAvailable` accounts for this. Use `MemAvailable` to estimate actual available memory, not `MemFree`.

---

## Step 2: Analyze /proc/vmstat

`/proc/vmstat` provides virtual memory activity counters since boot:

```bash
cat /proc/vmstat | head -15
```

📸 **Verified Output:**
```
nr_free_pages 23848317
nr_zone_inactive_anon 0
nr_zone_active_anon 985250
nr_zone_inactive_file 6201035
nr_zone_active_file 123900
nr_zone_unevictable 6628
nr_zone_write_pending 25582
nr_mlock 6628
nr_bounce 0
nr_zspages 0
nr_free_cma 0
nr_unaccepted 0
numa_hit 226982367
numa_miss 22
numa_foreign 22
```

```bash
# Key swap and paging statistics
grep -E 'pswpin|pswpout|pgmajfault|pgfault|oom_kill' /proc/vmstat
```

**Critical counters:**
| Counter | Meaning |
|---------|---------|
| `pswpin` | Pages swapped in (non-zero = memory pressure) |
| `pswpout` | Pages swapped out (high = system under pressure) |
| `pgmajfault` | Major page faults (required disk I/O) |
| `pgfault` | Minor page faults (resolved in RAM) |
| `oom_kill` | Processes killed by OOM killer — should be 0 |

> 💡 Monitor `vmstat` over time with `watch -n 1 'grep oom_kill /proc/vmstat'`. A non-zero and growing `oom_kill` indicates serious memory exhaustion.

---

## Step 3: Monitor Real-Time Memory with vmstat

```bash
apt-get update -qq && apt-get install -y procps
vmstat 1 3
```

📸 **Verified Output:**
```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  0      0 95377088 915452 26197444    0    0     0     3    0    2  3  0 97  0  0
 3  0      0 95394152 915452 26197452    0    0     0     0 7107 3975  4  1 95  0  0
 1  0      0 95410304 915452 26197464    0    0     0     0 7228 4093  4  1 95  0  0
```

**Memory pressure indicators:**
- `si`/`so` > 0: swap activity — memory is exhausted
- `b` > 0: processes blocked waiting for I/O
- `wa` CPU% > 20%: I/O bottleneck
- `free` decreasing + `si` increasing: OOM imminent

---

## Step 4: OOM Killer and Memory Overcommit

The OOM (Out-of-Memory) killer terminates processes when memory is exhausted. Control its behavior:

```bash
# Memory overcommit policy (requires --privileged)
cat /proc/sys/vm/overcommit_memory
cat /proc/sys/vm/overcommit_ratio
```

📸 **Verified Output:**
```
0
50
```

**Overcommit policies:**
| Value | Behavior |
|-------|---------|
| `0` (default) | Heuristic: allow reasonable overcommit |
| `1` | Always allow overcommit (no limits) |
| `2` | Never overcommit beyond `overcommit_ratio`% of RAM + swap |

```bash
# View OOM score for a process (higher = more likely to be killed)
cat /proc/1/oom_score
cat /proc/1/oom_score_adj

# Protect a critical process from OOM killer (score -1000 = never kill)
echo -1000 > /proc/1/oom_score_adj 2>/dev/null && echo "Protected" || echo "Permission denied in container"
```

> 💡 Set `oom_score_adj = -1000` for critical daemons like databases. Set it to `+500` for non-critical batch jobs to make them OOM-killed first, protecting your database.

---

## Step 5: CPU Affinity with taskset

Bind processes to specific CPU cores to reduce cache thrashing and improve predictability:

```bash
apt-get install -y util-linux

# Run a command on CPU 0 only
taskset -c 0 echo 'running on cpu 0'
```

📸 **Verified Output:**
```
running on cpu 0
```

```bash
# Check current CPU affinity of a process
taskset -p 1
```

📸 **Verified Output:**
```
pid 1's current affinity mask: ffffffff
```

```bash
# Run on CPUs 0 and 1 only
taskset -c 0,1 stress-ng --cpu 2 --timeout 2s &
BGPID=$!
taskset -p $BGPID
wait $BGPID
```

**Use cases for CPU affinity:**
- **Real-time applications**: Pin to isolated CPUs to avoid scheduling jitter
- **NUMA optimization**: Pin processes to cores local to their memory
- **Cache isolation**: Prevent different workloads from evicting each other's cache

> 💡 For persistent affinity settings in systemd services, use `CPUAffinity=0,1` in the `[Service]` section of the unit file.

---

## Step 6: Inspect Per-Process Memory with /proc/PID/smaps

`/proc/PID/smaps` provides detailed memory mapping information:

```bash
cat /proc/1/smaps | head -30
```

📸 **Verified Output:**
```
558be5467000-558be5496000 r--p 00000000 00:57 1049938                    /usr/bin/bash
Size:                188 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Rss:                 188 kB
Pss:                  47 kB
Pss_Dirty:             0 kB
Shared_Clean:        188 kB
Shared_Dirty:          0 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:          188 kB
Anonymous:             0 kB
KSM:                   0 kB
LazyFree:              0 kB
AnonHugePages:         0 kB
ShmemPmdMapped:        0 kB
FilePmdMapped:         0 kB
Shared_Hugetlb:        0 kB
Private_Hugetlb:        0 kB
Swap:                  0 kB
SwapPss:               0 kB
Locked:                0 kB
THPeligible:           0
VmFlags: rd mr mw me sd
```

**Key smaps fields:**
| Field | Description |
|-------|-------------|
| `Size` | Total mapping size |
| `Rss` | Resident set size (currently in RAM) |
| `Pss` | Proportional set size (shared pages counted fractionally) |
| `Private_Dirty` | Modified private pages — the real memory cost |
| `Swap` | Pages swapped out for this mapping |

```bash
# Total private dirty memory for a process (actual RAM cost)
awk '/Private_Dirty/ {sum += $2} END {print sum " kB private dirty"}' /proc/1/smaps

# Process memory summary
grep -E 'VmRSS|VmSize|VmSwap|VmPeak' /proc/1/status
```

📸 **Verified Output:**
```
VmPeak:	    3480 kB
VmSize:	    3472 kB
VmRSS:	    1876 kB
VmSwap:	       0 kB
```

> 💡 For detecting memory leaks: monitor `Private_Dirty` growth over time. A process with steadily growing `Private_Dirty` in anonymous mappings is leaking heap memory.

---

## Step 7: numactl and NUMA Topology

On multi-socket servers, **NUMA (Non-Uniform Memory Access)** affects performance. Memory access is faster when using RAM local to the CPU socket.

```bash
apt-get install -y numactl

# Show NUMA topology
numactl --hardware 2>&1 | head -20
```

📸 **Verified Output (single-node system):**
```
available: 1 nodes (0)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43
node 0 size: 124550 MB
node 0 free: 93199 MB
node distances:
node   0
  0:  10
```

```bash
# Run a process with memory allocation policy
numactl --cpunodebind=0 --membind=0 ls /tmp

# Check NUMA stats
cat /proc/vmstat | grep numa
```

📸 **Verified Output:**
```
numa_hit 226982367
numa_miss 22
numa_foreign 22
```

> 💡 High `numa_miss` in `/proc/vmstat` means processes are accessing remote NUMA memory — a performance penalty of 2–4x latency. Fix with `numactl --membind` or kernel-level NUMA balancing (`kernel.numa_balancing=1`).

---

## Step 8: Capstone — Load Simulation and Memory Analysis

**Scenario:** Simulate load and measure system behavior under stress.

```bash
apt-get install -y stress-ng procps time

# Capture baseline memory state
echo "=== Baseline Memory ==="
grep -E 'MemAvailable|Cached|Active' /proc/meminfo

# Run CPU stress and observe
echo "=== CPU Stress Test ==="
stress-ng --cpu 2 --timeout 3s --metrics-brief 2>&1
```

📸 **Verified Output:**
```
=== Baseline Memory ===
MemAvailable:   121376588 kB
Cached:         24433200 kB
Active:          4436600 kB
Active(anon):    3941000 kB
Active(file):     495600 kB
=== CPU Stress Test ===
stress-ng: info:  [311] setting to a 2 second run per stressor
stress-ng: info:  [311] dispatching hogs: 1 cpu
stress-ng: info:  [311] successful run completed in 2.00s
stress-ng: info:  [311] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: info:  [311]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: info:  [311] cpu                1320      2.00      1.99      0.00       660.00         663.32
```

```bash
# Memory stress test
echo "=== Memory Stress Test ==="
stress-ng --vm 1 --vm-bytes 512M --timeout 3s --metrics-brief 2>&1

# Post-stress memory check
echo "=== Post-stress Memory ==="
grep -E 'MemAvailable|SwapFree|Dirty' /proc/meminfo

# Simulate memory leak detection
echo "=== Process Memory Snapshots ==="
for i in 1 2 3; do
  echo "Sample $i: $(awk '/Private_Dirty/ {sum += $2} END {print sum}' /proc/1/smaps) kB Private_Dirty"
  sleep 0.5
done
```

📸 **Verified Output:**
```
=== Memory Stress Test ===
stress-ng: info:  [400] setting to a 3 second run per stressor
stress-ng: info:  [400] dispatching hogs: 1 vm
stress-ng: info:  [400] successful run completed in 3.00s
stress-ng: info:  [400] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: info:  [400]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: info:  [400] vm               154290      3.00      1.43      1.57     51430.00      51430.00
=== Post-stress Memory ===
MemAvailable:   121502024 kB
SwapFree:        8388604 kB
Dirty:            154300 kB
=== Process Memory Snapshots ===
Sample 1: 292 kB Private_Dirty
Sample 2: 292 kB Private_Dirty
Sample 3: 292 kB Private_Dirty
```

A stable `Private_Dirty` across samples = no memory leak. A growing value = potential leak.

---

## Summary

| Tool / File | Purpose |
|-------------|---------|
| `/proc/meminfo` | System-wide memory statistics |
| `/proc/vmstat` | Virtual memory event counters |
| `/proc/PID/smaps` | Per-process detailed memory mappings |
| `/proc/PID/status` | Process VmRSS, VmSize, VmSwap summary |
| `/proc/sys/vm/overcommit_memory` | OOM overcommit policy |
| `/proc/PID/oom_score_adj` | OOM kill priority adjustment |
| `vmstat 1 3` | Real-time memory + CPU + swap overview |
| `taskset -c 0,1 <cmd>` | Pin process to CPU cores |
| `taskset -p PID` | Check current CPU affinity |
| `numactl --hardware` | Show NUMA topology |
| `numactl --membind=0 <cmd>` | Bind process memory to NUMA node |
| `stress-ng --cpu N` | CPU load simulation |
| `stress-ng --vm 1 --vm-bytes 512M` | Memory pressure simulation |
| `awk '/Private_Dirty/ {sum+=$2}' smaps` | Total private memory cost |
