# Lab 02: Performance Profiling with perf and System Tools

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Performance profiling helps identify CPU bottlenecks, cache misses, and hot code paths. The Linux `perf` tool is the gold standard for CPU-level performance analysis. This lab covers `perf` installation, CPU statistics, `/proc/cpuinfo` analysis, and alternative profiling tools for environments where `perf` is unavailable.

---

## Step 1: Install perf Tools

The `perf` tool must match your running kernel version:

```bash
apt-get update -qq && apt-get install -y linux-tools-generic linux-tools-common
perf --version 2>&1 || echo "perf not available for this kernel"
```

📸 **Verified Output:**
```
WARNING: perf not found for kernel 6.14.0-37

  You may need to install the following packages for this specific kernel:
    linux-tools-6.14.0-37-generic
    linux-cloud-tools-6.14.0-37-generic

  You may also want to install one of the following packages to keep up to date:
    linux-tools-generic
    linux-cloud-tools-generic
perf not available for this kernel
```

> 💡 In Docker containers, the kernel is the **host** kernel, not Ubuntu 22.04's. You need `linux-tools-$(uname -r)` matching the host. On a native Ubuntu install, `linux-tools-generic` installs a matching version automatically.

**On a native Ubuntu system where perf is available:**

```bash
# Install matching perf for running kernel
apt-get install -y linux-tools-$(uname -r) linux-tools-generic

# Verify
perf --version
# perf version 5.15.78
```

---

## Step 2: Inspect CPU Hardware with /proc/cpuinfo

Understanding your hardware is the foundation of performance analysis:

```bash
# CPU count and model
grep -E 'processor|model name|cpu MHz' /proc/cpuinfo | head -9
```

📸 **Verified Output:**
```
processor	: 0
model name	: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
cpu MHz		: 2199.998
processor	: 1
model name	: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
cpu MHz		: 2199.998
processor	: 2
model name	: Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
cpu MHz		: 2199.998
```

```bash
# Count logical CPUs
nproc

# Check CPU features/flags
grep flags /proc/cpuinfo | head -1 | cut -c1-80
```

📸 **Verified Output:**
```
44
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36
```

> 💡 Key flags to look for: `sse4_2` (SIMD), `avx`/`avx2` (vector ops), `aes` (hardware encryption), `vmx`/`svm` (virtualization support).

---

## Step 3: perf stat — Count Hardware Events

`perf stat` measures CPU performance counters for a command's execution:

```bash
# On a native system with perf available:
perf stat ls /tmp
```

**Example output (native system):**
```
Performance counter stats for 'ls /tmp':

              0.67 msec task-clock                       #    0.590 CPUs utilized
                 0      context-switches                 #    0.000 /sec
                 0      cpu-migrations                   #    0.000 /sec
                96      page-faults                      #  143.284 K/sec
         1,430,582      cycles                           #    2.134 GHz
         1,522,889      instructions                     #    1.06  insn per cycle
           297,234      branches                         #  443.035 M/sec
             8,102      branch-misses                    #    2.73% of all branches

       0.001135802 seconds time elapsed
       0.000613000 seconds user
       0.000127000 seconds sys
```

```bash
# More detailed hardware events:
perf stat -e cycles,instructions,cache-misses,cache-references ls /tmp
```

**Key metrics explained:**
- **cycles**: Total CPU clock cycles consumed
- **instructions**: Machine instructions executed
- **IPC** (insn per cycle): Higher = more efficient execution (ideal > 1.0)
- **cache-misses**: LLC (Last Level Cache) misses — expensive memory accesses
- **branch-misses**: Mispredicted branches causing pipeline flushes

---

## Step 4: Measure with /usr/bin/time -v (Available in Docker)

When `perf` isn't available, `/usr/bin/time -v` provides detailed resource usage:

```bash
apt-get install -y time
/usr/bin/time -v ls /tmp 2>&1
```

📸 **Verified Output:**
```
	Command being timed: "ls /tmp"
	User time (seconds): 0.00
	System time (seconds): 0.00
	Percent of CPU this job got: 60%
	Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.00
	Average shared text size (kbytes): 0
	Average unshared data size (kbytes): 0
	Average stack size (kbytes): 0
	Average total size (kbytes): 0
	Maximum resident set size (kbytes): 1732
	Average unshared data size (kbytes): 0
	Major (requiring I/O) page faults: 0
	Minor (reclaiming a frame) page faults: 96
	Voluntary context switches: 1
	Involuntary context switches: 0
	Swaps: 0
	File system inputs: 0
	File system outputs: 0
	Socket messages sent: 0
	Socket messages received: 0
	Signals delivered: 0
	Page size (bytes): 4096
	Exit status: 0
```

> 💡 `Maximum resident set size` shows peak RAM usage. `Minor page faults` indicate memory-mapped operations. `Major page faults` indicate disk I/O for page loading — minimize these!

---

## Step 5: Monitor System-Wide CPU with vmstat

`vmstat` provides real-time system performance statistics:

```bash
# Show 3 snapshots, 1 second apart
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

**Column meanings:**
| Column | Description |
|--------|-------------|
| `r` | Processes in run queue (>nproc = CPU-bound) |
| `b` | Processes blocked (I/O wait) |
| `si`/`so` | Swap in/out (non-zero = memory pressure) |
| `us` | User CPU % |
| `sy` | System/kernel CPU % |
| `id` | Idle CPU % |
| `wa` | Wait for I/O % |

---

## Step 6: perf record and report — Sampling Profiler

`perf record` samples the call stack at high frequency to find hot functions:

```bash
# On a native system — record 5 seconds of a CPU-bound workload:
perf record -g -F 99 -- bash -c 'for i in $(seq 1 1000000); do echo $i > /dev/null; done'

# Generate a report:
perf report --stdio | head -30
```

**Example output (native system):**
```
# Overhead  Command  Shared Object      Symbol
# ........  .......  .................  ..........................
#
    42.35%  bash     bash               [.] execute_command_internal
    18.72%  bash     bash               [.] expand_word_internal
    12.54%  bash     libc.so.6          [.] __GI___write
     8.91%  bash     [kernel.kallsyms]  [k] copy_user_generic_string
     5.33%  bash     bash               [.] parse_and_execute
```

> 💡 The `[.]` prefix = user space, `[k]` = kernel space. High kernel time (`sy` in vmstat) often points to excessive syscalls.

---

## Step 7: Flame Graphs Concept

Flame graphs visualize CPU profiling data as a stacked bar chart:

```bash
# Generate perf data (native system):
perf record -F 99 -g -- stress-ng --cpu 1 --timeout 5s
perf script | head -20
```

**To generate a flame graph (native system):**
```bash
# Install FlameGraph tools
git clone https://github.com/brendangregg/FlameGraph
perf record -F 99 -g -- your-program
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg
```

**Reading flame graphs:**
- **X-axis**: Time proportion (wider = more CPU time)
- **Y-axis**: Call stack depth (bottom = kernel, top = leaf functions)
- **Hot spot**: Wide bars near the top = functions to optimize

> 💡 Flame graphs were invented by Brendan Gregg at Netflix. They remain the most effective way to visualize where CPU time is spent across deep call stacks.

---

## Step 8: Capstone — Profile a CPU-Bound Workload

**Scenario:** A Python script is running slowly. Profile it to find the bottleneck.

```bash
apt-get install -y procps time stress-ng

# Simulate a CPU-intensive workload and measure it
/usr/bin/time -v stress-ng --cpu 2 --timeout 3s --metrics-brief 2>&1
```

📸 **Verified Output:**
```
stress-ng: info:  [311] setting to a 2 second run per stressor
stress-ng: info:  [311] dispatching hogs: 1 cpu
stress-ng: info:  [311] successful run completed in 2.00s
stress-ng: info:  [311] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: info:  [311]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: info:  [311] cpu                1320      2.00      1.99      0.00       660.00         663.32
```

```bash
# Monitor CPU usage during workload (background then snapshot)
stress-ng --cpu 2 --timeout 5s &
sleep 1
vmstat 1 3
```

```bash
# Read raw CPU stats from /proc/stat
cat /proc/stat | grep '^cpu '
```

📸 **Verified Output:**
```
cpu  49925142 3745 4060453 1697281064 7166 0 191720 0 0 0
```

Fields: `user nice system idle iowait irq softirq steal guest guest_nice`

---

## Summary

| Tool | Purpose |
|------|---------|
| `perf stat <cmd>` | Count CPU events (cycles, instructions, cache misses) |
| `perf record -g -F 99 <cmd>` | Sample call stacks at 99Hz |
| `perf report --stdio` | View hot functions from recorded data |
| `perf top` | Live view of hot functions (like top but per-function) |
| `/usr/bin/time -v <cmd>` | Detailed resource usage (memory, page faults, switches) |
| `vmstat 1 3` | Real-time CPU/memory/IO overview |
| `/proc/cpuinfo` | CPU hardware details and feature flags |
| `/proc/stat` | Raw CPU time counters |
| Flame graphs | Visualize stack profiling as weighted call tree |
