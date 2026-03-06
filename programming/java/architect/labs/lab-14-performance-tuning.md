# Lab 14: Performance Tuning — JMH, GC, JIT

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Measure what you optimize: use JMH (Java Microbenchmark Harness) for reliable micro-benchmarks, configure GC for different workloads, analyze GC logs, tune JIT compilation, and understand the Epsilon GC for pure throughput measurement.

---

## Step 1: Why Microbenchmarking is Hard

```
JVM Optimizations that fool naive benchmarks:
  Dead code elimination  — JIT removes code with no observable side effects
  Constant folding       — JIT computes constant expressions at compile time
  Loop unrolling         — JIT replicates loop body to reduce overhead
  Inlining               — JIT copies callee body into caller
  Warmup                 — first N iterations use interpreter, not JIT
  GC pauses              — garbage collection adds latency noise
  OSR                    — on-stack replacement changes benchmark behavior mid-run

JMH solutions:
  Blackhole.consume()   — prevents dead code elimination
  @Fork(1+)             — fresh JVM per benchmark
  @Warmup               — discard initial results
  @Measurement          — only measure after warmup
  @State                — isolate benchmark state
  @BenchmarkMode        — throughput, average time, sample time
```

---

## Step 2: JMH Setup

```xml
<!-- pom.xml -->
<dependencies>
  <dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-core</artifactId>
    <version>1.37</version>
  </dependency>
  <dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-generator-annprocess</artifactId>
    <version>1.37</version>
    <scope>provided</scope>
  </dependency>
</dependencies>
```

```java
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.*;
import org.openjdk.jmh.runner.options.*;
import org.openjdk.jmh.infra.Blackhole;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Benchmark)
@Warmup(iterations = 2, time = 1, timeUnit = TimeUnit.SECONDS)
@Measurement(iterations = 3, time = 1, timeUnit = TimeUnit.SECONDS)
@Fork(0) // 0 = same JVM, 1+ = forked JVM (recommended for production benchmarks)
public class StringBenchmark {
    
    private String input = "Hello, World!";
    
    @Benchmark
    public String stringConcat() {
        return "Hello" + " " + "World" + "!";
    }
    
    @Benchmark
    public String stringBuilder() {
        return new StringBuilder()
            .append("Hello").append(" ").append("World").append("!")
            .toString();
    }
    
    @Benchmark
    public int stringLength(Blackhole bh) {
        // Use Blackhole to prevent dead code elimination
        int len = input.length();
        bh.consume(len); // tell JMH this result is "used"
        return len;
    }
    
    public static void main(String[] args) throws Exception {
        Options opts = new OptionsBuilder()
            .include(StringBenchmark.class.getSimpleName())
            .forks(0)
            .warmupIterations(1)
            .measurementIterations(2)
            .build();
        new Runner(opts).run();
    }
}
```

---

## Step 3: Benchmark Modes and Scopes

```java
import org.openjdk.jmh.annotations.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

// Mode.Throughput    — operations per second (higher = better)
// Mode.AverageTime   — average time per op (lower = better)
// Mode.SampleTime    — sample individual durations
// Mode.SingleShotTime — single cold invocation (no warmup)
// Mode.All           — all of the above

@State(Scope.Benchmark)     // one instance per benchmark run
class BenchmarkState {
    List<Integer> data;
    @Setup(Level.Trial) // called once before all iterations
    public void setup() {
        data = new ArrayList<>();
        for (int i = 0; i < 10000; i++) data.add(i);
    }
    @TearDown(Level.Trial) // called once after all iterations
    public void teardown() { data = null; }
}

@State(Scope.Thread) // one instance per thread
class ThreadState {
    Random random;
    @Setup public void setup() { random = new Random(); }
}

@State(Scope.Group) // shared within a thread group
class GroupState {
    volatile int value;
}
```

---

## Step 4: GC Algorithm Selection

```bash
# Available GC algorithms in JDK 21:
# G1GC (default) — balanced throughput + latency, generational
java -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:G1HeapRegionSize=4m \
     -Xmx4g -Xms4g Main

# ZGC — ultra-low latency (<10ms pauses), scales to TB heaps
java -XX:+UseZGC \
     -XX:ZCollectionInterval=0 \
     -Xmx4g Main

# Shenandoah — concurrent evacuation, predictable latency
java -XX:+UseShenandoahGC \
     -XX:ShenandoahGCHeuristics=adaptive Main

# ParallelGC — max throughput, tolerate pauses (batch workloads)
java -XX:+UseParallelGC \
     -XX:GCTimeRatio=99 \
     -XX:MaxGCPauseMillis=500 Main

# SerialGC — single-threaded, small heaps (<100MB), containers
java -XX:+UseSerialGC Main

# EpsilonGC — NO GC (OOM on exhaustion), only for benchmarks!
java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC Main
```

> 💡 Use **Epsilon GC** in JMH benchmarks with `@Fork(0)` to eliminate GC noise entirely — but set a large enough heap.

---

## Step 5: GC Log Analysis

```bash
# Enable detailed GC logging (Java 9+)
java -Xlog:gc*:file=/tmp/gc.log:time,uptime,pid,level,tags \
     -Xms512m -Xmx512m Main

# Specific log selectors:
java -Xlog:gc:stdout:time             # basic GC events
java -Xlog:gc+heap:stdout:time        # heap sizes
java -Xlog:gc+stats:stdout            # GC statistics
java -Xlog:safepoint:stdout           # JVM safepoints
java -Xlog:gc*=debug:file=gc.log      # everything (verbose)

# Key patterns in GC log:
# [GC] Pause Young (Normal) (G1 Evacuation Pause)   → minor GC
# [GC] Pause Full (Ergonomics)                       → full GC (investigate!)
# [GC] Concurrent Mark Cycle                         → G1 background cycle
```

```java
// Trigger GC log analysis programmatically
public class GCDemo {
    public static void main(String[] args) throws Exception {
        Runtime rt = Runtime.getRuntime();
        System.out.printf("Heap before: used=%dMB, total=%dMB, max=%dMB%n",
            (rt.totalMemory() - rt.freeMemory()) / 1_000_000,
            rt.totalMemory() / 1_000_000,
            rt.maxMemory() / 1_000_000);
        
        // Allocate some garbage
        var list = new java.util.ArrayList<byte[]>();
        for (int i = 0; i < 100; i++) list.add(new byte[1_000_000]); // 100MB
        list.clear();
        
        System.gc(); // hint (not guaranteed)
        System.out.printf("Heap after GC: used=%dMB%n",
            (rt.totalMemory() - rt.freeMemory()) / 1_000_000);
    }
}
```

---

## Step 6: JIT Compilation Flags

```bash
# See what JIT is doing
java -XX:+PrintCompilation \
     -XX:+UnlockDiagnosticVMOptions \
     Main 2>&1 | head -30

# Compilation log format:
# [time] [id] [flags] class::method (bytes) @[tier]
# Flags: % = OSR, ! = exception handler, * = native, b = blocking

# Tiered compilation control
java -XX:+TieredCompilation         # default: enabled
java -XX:-TieredCompilation         # JIT only C2, skip C1

# Inlining tuning
java -XX:MaxInlineSize=35           # max bytecodes to inline (default 35)
java -XX:InlineSmallCode=1000       # inline if compiled code < 1000 bytes
java -XX:FreqInlineSize=325         # hot method inline threshold

# Print inlining decisions
java -XX:+PrintInlining \
     -XX:+UnlockDiagnosticVMOptions \
     Main 2>&1 | grep "inline\|callee"

# Disable specific optimizations for debugging
java -XX:+PrintCompilation \
     -XX:CompileCommand=dontinline,java/util/ArrayList.add \
     Main
```

---

## Step 7: String Interning and Constant Pool

```java
public class StringInternDemo {
    public static void main(String[] args) {
        // String literals → automatically interned (in constant pool)
        String a = "hello";
        String b = "hello";
        System.out.println("literals ==: " + (a == b)); // true — same pool reference

        // new String() → heap object, NOT interned
        String c = new String("hello");
        String d = new String("hello");
        System.out.println("new String ==: " + (c == d)); // false — different objects
        System.out.println("new String equals: " + c.equals(d)); // true — same content

        // String.intern() → return/add to pool
        String e = c.intern();
        System.out.println("interned ==: " + (a == e)); // true — same pool reference

        // Constant pool impact:
        // In loops: avoid new String("literal") — use literal directly
        // intern() cost: hash lookup in concurrent pool (ConcurrentHashMap-like)
        // G1/ZGC: string deduplication (-XX:+UseStringDeduplication) handles rest

        // Compact Strings (Java 9+): Latin-1 strings use byte[] (half the memory)
        String latin1 = "Hello World"; // byte[] internally
        String utf16 = "日本語テスト";  // char[] internally
        System.out.println("Compact Strings enabled by default since Java 9");
        System.out.println("latin1.length(): " + latin1.length());
        System.out.println("utf16.length(): " + utf16.length());
    }
}
```

---

## Step 8: Capstone — JMH Benchmark

```java
package com.lab;

import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.*;
import org.openjdk.jmh.runner.options.*;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Benchmark)
@Warmup(iterations = 1, time = 1)
@Measurement(iterations = 2, time = 1)
@Fork(0)
public class StringBenchmark {
    
    @Benchmark
    public String concat() {
        return "Hello" + " World!";
    }
    
    @Benchmark
    public String builder() {
        return new StringBuilder().append("Hello").append(" World!").toString();
    }
    
    public static void main(String[] a) throws Exception {
        new Runner(new OptionsBuilder()
            .include(StringBenchmark.class.getSimpleName())
            .forks(0)
            .warmupIterations(1)
            .measurementIterations(2)
            .build()).run();
    }
}
```

```bash
# Maven project with jmh-core + jmh-generator-annprocess
cd /tmp/jmhf && mvn compile exec:java -Dexec.mainClass=com.lab.StringBenchmark 2>/dev/null | grep -E '(Benchmark|avgt|builder|concat)'
```

📸 **Verified Output:**
```
Benchmark                Mode  Cnt   Score   Error  Units
StringBenchmark.builder  avgt    2  36.176          ns/op
StringBenchmark.concat   avgt    2   4.083          ns/op
```

> 💡 `concat` is faster because the JIT folds `"Hello" + " World!"` into a **compile-time constant** — demonstrating why benchmarking is tricky and why JMH's `Blackhole` matters for variable inputs.

---

## Summary

| Tool/Concept | CLI Flag / API | Purpose |
|---|---|---|
| JMH benchmark | `@Benchmark` + `Runner` | Reliable micro-benchmarks |
| Warmup | `@Warmup(iterations=N)` | JIT stabilization |
| Blackhole | `Blackhole.consume()` | Prevent dead code elimination |
| G1GC | `-XX:+UseG1GC` | Balanced throughput/latency |
| ZGC | `-XX:+UseZGC` | Sub-10ms pause times |
| EpsilonGC | `-XX:+UseEpsilonGC` | Benchmark without GC noise |
| GC logging | `-Xlog:gc*:file=gc.log` | Pause analysis |
| JIT logging | `-XX:+PrintCompilation` | Compilation analysis |
| String intern | `String.intern()` | Pool deduplication |
| Compact strings | Default Java 9+ | byte[] for Latin-1 |
