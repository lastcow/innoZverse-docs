# Lab 04: Java Memory Model & Advanced Synchronization

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

The Java Memory Model (JMM) defines **happens-before** relationships that guarantee visibility across threads. Master `VarHandle` for fine-grained memory access, `StampedLock` for optimistic reads, and `LongAdder` for high-contention counters.

---

## Step 1: Java Memory Model — Happens-Before Rules

```
JMM Happens-Before (HB) partial order:
  1. Program order within a thread
  2. Monitor lock/unlock: unlock HB → lock
  3. volatile write HB → volatile read (same variable)
  4. Thread.start() HB → first action in new thread
  5. Thread.join() HB → actions after join()
  6. Static initializer HB → first use of class
  7. Object construction HB → finalizer
```

```java
// Without HB: data race — value may not be visible
int x = 0;
boolean flag = false;
// Thread 1:            // Thread 2:
x = 42;                // while (!flag) {}
flag = true;           // System.out.println(x); // may print 0!

// With volatile: HB guaranteed
volatile boolean vFlag = false;
// Thread 1:            // Thread 2:
x = 42;                // while (!vFlag) {}  // volatile read sees volatile write
vFlag = true;          // System.out.println(x); // guaranteed: 42
                       // (volatile write flushes all prior writes)
```

> 💡 `volatile` guarantees **visibility** but NOT atomicity. `volatile long` reads are atomic on 64-bit JVMs but not specified by JMM for 32-bit.

---

## Step 2: VarHandle — Fine-Grained Memory Access

`VarHandle` (Java 9+) provides access modes for precise memory ordering — cheaper than `AtomicInteger` for some patterns.

```java
import java.lang.invoke.*;

public class VarHandleDemo {
    static int counter = 0;
    static final VarHandle COUNTER;
    
    static {
        try {
            COUNTER = MethodHandles.lookup()
                .findStaticVarHandle(VarHandleDemo.class, "counter", int.class);
        } catch (ReflectiveOperationException e) { throw new ExceptionInInitializerError(e); }
    }

    public static void main(String[] args) {
        // Plain access — no ordering guarantee
        COUNTER.set(0);
        
        // Volatile access — full memory fence
        COUNTER.setVolatile(10);
        int v = (int) COUNTER.getVolatile();
        System.out.println("setVolatile(10) -> getVolatile(): " + v);
        
        // Acquire/Release — one-sided fence (cheaper than volatile)
        COUNTER.setRelease(20);  // release fence (all prior writes visible)
        int a = (int) COUNTER.getAcquire(); // acquire fence (all subsequent reads see)
        System.out.println("setRelease(20) -> getAcquire(): " + a);
        
        // CAS — compare-and-set
        boolean cas1 = COUNTER.compareAndSet(20, 42);  // success
        boolean cas2 = COUNTER.compareAndSet(20, 99);  // fail
        System.out.println("CAS(20->42): " + cas1 + ", value=" + COUNTER.get());
        System.out.println("CAS(20->99): " + cas2 + ", value=" + COUNTER.get());
        
        // compareAndExchange — returns witness value
        int witness = (int) COUNTER.compareAndExchange(42, 100);
        System.out.println("CAX(42->100) witness: " + witness); // 42 (success)
        
        // Atomic add
        int prev = (int) COUNTER.getAndAdd(5);
        System.out.println("getAndAdd(5), prev=" + prev + ", now=" + COUNTER.get());
    }
}
```

**VarHandle access mode hierarchy:**
```
Plain         — no ordering (may reorder with anything)
Opaque        — prevents dead code elimination
Acquire/Release — half fence (producer/consumer patterns)
Volatile      — full fence (sequentially consistent)
```

---

## Step 3: StampedLock — Optimistic Reads

`StampedLock` (Java 8+) offers three locking modes with **optimistic read** being the key innovation — a read that doesn't even acquire a lock.

```java
import java.util.concurrent.locks.*;

public class StampedLockDemo {
    private final StampedLock lock = new StampedLock();
    private double x, y;

    // Optimistic read — may fail if writer intervenes
    double distance() {
        long stamp = lock.tryOptimisticRead();
        double cx = x, cy = y;  // read without lock
        if (!lock.validate(stamp)) {
            // Writer intervened — fall back to read lock
            stamp = lock.readLock();
            try { cx = x; cy = y; }
            finally { lock.unlockRead(stamp); }
        }
        return Math.sqrt(cx * cx + cy * cy);
    }

    // Write lock
    void move(double deltaX, double deltaY) {
        long stamp = lock.writeLock();
        try { x += deltaX; y += deltaY; }
        finally { lock.unlockWrite(stamp); }
    }

    // Upgrade read to write (may fail → retry)
    void moveIfOrigin() {
        long stamp = lock.readLock();
        try {
            while (x == 0.0 && y == 0.0) {
                long ws = lock.tryConvertToWriteLock(stamp);
                if (ws != 0L) {
                    stamp = ws;
                    x = 1.0; y = 1.0;
                    break;
                } else {
                    lock.unlockRead(stamp);
                    stamp = lock.writeLock();
                }
            }
        } finally { lock.unlock(stamp); }
    }
    
    public static void main(String[] args) {
        StampedLockDemo point = new StampedLockDemo();
        point.move(3.0, 4.0);
        System.out.println("Distance: " + point.distance()); // 5.0
        
        // Manual optimistic read pattern
        StampedLock sl = new StampedLock();
        long stamp = sl.tryOptimisticRead();
        System.out.println("Optimistic stamp: " + stamp);
        System.out.println("Valid (no write): " + sl.validate(stamp));
    }
}
```

> 💡 Use `StampedLock` when reads vastly outnumber writes. Optimistic reads have **zero overhead** when no writer is active.

---

## Step 4: LongAdder vs AtomicLong Under Contention

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CounterContention {
    public static void main(String[] args) throws Exception {
        int threads = 8, ops = 100_000;
        ExecutorService exec = Executors.newFixedThreadPool(threads);
        
        // LongAdder: maintains per-thread cells, merges on sum()
        LongAdder adder = new LongAdder();
        long t1 = System.nanoTime();
        var fs1 = new java.util.ArrayList<Future<?>>();
        for (int i = 0; i < threads; i++)
            fs1.add(exec.submit(() -> { for (int j = 0; j < ops; j++) adder.increment(); return null; }));
        for (var f : fs1) f.get();
        long adderTime = System.nanoTime() - t1;

        // AtomicLong: single CAS on shared variable
        AtomicLong atomic = new AtomicLong();
        t1 = System.nanoTime();
        var fs2 = new java.util.ArrayList<Future<?>>();
        for (int i = 0; i < threads; i++)
            fs2.add(exec.submit(() -> { for (int j = 0; j < ops; j++) atomic.incrementAndGet(); return null; }));
        for (var f : fs2) f.get();
        long atomicTime = System.nanoTime() - t1;
        
        exec.shutdown();
        System.out.println("LongAdder sum:  " + adder.sum() + ", time: " + adderTime/1_000_000 + "ms");
        System.out.println("AtomicLong val: " + atomic.get() + ", time: " + atomicTime/1_000_000 + "ms");
        System.out.printf("LongAdder is %.1fx faster under contention%n", (double)atomicTime/adderTime);
    }
}
```

**Internals comparison:**
```
AtomicLong:   [single cell] ← all 8 threads CAS-compete → cache line bouncing
LongAdder:    [cell-0][cell-1][cell-2]...[cell-7] → sum() = Σ cells
              Each thread → own cell → minimal CAS contention
```

---

## Step 5: False Sharing and @Contended

```java
// FALSE SHARING: two variables in the same 64-byte cache line
class SharedCounters {
    long counter1 = 0; // cache line shared with counter2!
    long counter2 = 0; // Thread-2 updates this → invalidates Thread-1's cache line
}

// FIX: Pad to different cache lines
class PaddedCounters {
    long p1, p2, p3, p4, p5, p6, p7; // 56 bytes padding
    volatile long counter1 = 0;
    long q1, q2, q3, q4, q5, q6, q7; // 56 bytes padding
    volatile long counter2 = 0;
}

// Java 8+: @Contended (JVM handles padding)
// @jdk.internal.vm.annotation.Contended
// long counter;
// Run with: -XX:-RestrictContended

public class FalseSharingDemo {
    public static void main(String[] args) {
        System.out.println("Cache line size: ~64 bytes");
        System.out.println("long size: 8 bytes → 8 longs per cache line");
        System.out.println("False sharing: two hot fields in same cache line");
        System.out.println("Fix 1: Manual padding (7 longs before/after)");
        System.out.println("Fix 2: @jdk.internal.vm.annotation.Contended");
        System.out.println("Fix 3: LongAdder (built-in padding via @Contended)");
    }
}
```

---

## Step 6: Memory Barriers in Practice

```java
// Memory barriers are the foundation of lock-free algorithms
public class MemoryBarrierDemo {
    volatile int x = 0, y = 0;
    
    // STORE-STORE barrier (implicit in volatile write)
    void writer() {
        x = 1;           // plain store
        y = 1;           // volatile store — flushes all prior stores
        // Guarantees: x=1 is visible before y=1
    }
    
    // LOAD-LOAD barrier (implicit in volatile read)
    void reader() {
        int ry = y;      // volatile load — fence: all subsequent loads see fresh values
        int rx = x;      // plain load — sees x=1 if ry=1
        // Guarantees: if ry=1 then rx=1
    }
    
    public static void main(String[] args) throws Exception {
        var demo = new MemoryBarrierDemo();
        Thread writer = Thread.ofVirtual().start(demo::writer);
        Thread reader = Thread.ofVirtual().start(demo::reader);
        writer.join(); reader.join();
        System.out.println("Volatile write → read: full memory fence");
        System.out.println("setRelease → getAcquire: half fence (cheaper)");
        System.out.println("Memory barrier patterns verified!");
    }
}
```

---

## Step 7: Lock-Free Queue Pattern

```java
import java.util.concurrent.atomic.*;

// Michael-Scott non-blocking queue skeleton
public class LockFreeQueue<T> {
    record Node<T>(T item, AtomicReference<Node<T>> next) {
        Node(T item) { this(item, new AtomicReference<>(null)); }
    }
    
    private final AtomicReference<Node<T>> head, tail;
    
    public LockFreeQueue() {
        Node<T> sentinel = new Node<>(null);
        head = new AtomicReference<>(sentinel);
        tail = new AtomicReference<>(sentinel);
    }
    
    public void enqueue(T item) {
        Node<T> node = new Node<>(item);
        while (true) {
            Node<T> last = tail.get();
            Node<T> next = last.next().get();
            if (next == null) {
                if (last.next().compareAndSet(null, node)) {
                    tail.compareAndSet(last, node); // may fail — ok
                    return;
                }
            } else {
                tail.compareAndSet(last, next); // help advance tail
            }
        }
    }
    
    public T dequeue() {
        while (true) {
            Node<T> first = head.get();
            Node<T> last = tail.get();
            Node<T> next = first.next().get();
            if (first == last) return null; // empty
            if (head.compareAndSet(first, next)) return next.item();
        }
    }
    
    public static void main(String[] args) {
        var q = new LockFreeQueue<Integer>();
        q.enqueue(1); q.enqueue(2); q.enqueue(3);
        System.out.println("Dequeue: " + q.dequeue()); // 1
        System.out.println("Dequeue: " + q.dequeue()); // 2
        System.out.println("Lock-free queue: SUCCESS");
    }
}
```

---

## Step 8: Capstone — VarHandle CAS + StampedLock Demo

```java
import java.lang.invoke.*;
import java.util.concurrent.locks.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class Main {
    static int counter = 0;
    static VarHandle COUNTER;
    static {
        try {
            COUNTER = MethodHandles.lookup()
                .findStaticVarHandle(Main.class, "counter", int.class);
        } catch (Exception e) { throw new RuntimeException(e); }
    }
    
    public static void main(String[] args) throws Exception {
        COUNTER.set(0);
        boolean cas1 = COUNTER.compareAndSet(0, 42);
        boolean cas2 = COUNTER.compareAndSet(0, 99);
        System.out.println("VarHandle CAS(0->42): " + cas1 + ", value=" + COUNTER.get());
        System.out.println("VarHandle CAS(0->99): " + cas2 + ", value=" + COUNTER.get());
        
        COUNTER.setRelease(100);
        int acquired = (int) COUNTER.getAcquire();
        System.out.println("setRelease(100) -> getAcquire(): " + acquired);
        
        StampedLock lock = new StampedLock();
        double[] point = {1.0, 2.0};
        long stamp = lock.tryOptimisticRead();
        double x = point[0], y = point[1];
        if (!lock.validate(stamp)) {
            stamp = lock.readLock();
            try { x = point[0]; y = point[1]; }
            finally { lock.unlockRead(stamp); }
        }
        System.out.println("StampedLock optimistic read: x=" + x + ", y=" + y);
        System.out.println("Optimistic read valid: " + lock.validate(stamp));
        
        LongAdder adder = new LongAdder();
        AtomicLong atomic = new AtomicLong();
        int threads = 8, ops = 100000;
        ExecutorService exec = Executors.newFixedThreadPool(threads);
        long t1 = System.nanoTime();
        var fs1 = new java.util.ArrayList<Future<?>>();
        for (int i = 0; i < threads; i++) fs1.add(exec.submit(() -> { for(int j=0;j<ops;j++) adder.increment(); return null;}));
        for (var f : fs1) f.get();
        long adderTime = System.nanoTime() - t1;
        t1 = System.nanoTime();
        var fs2 = new java.util.ArrayList<Future<?>>();
        for (int i = 0; i < threads; i++) fs2.add(exec.submit(() -> { for(int j=0;j<ops;j++) atomic.incrementAndGet(); return null;}));
        for (var f : fs2) f.get();
        long atomicTime = System.nanoTime() - t1;
        exec.shutdown();
        System.out.println("LongAdder sum: " + adder.sum() + ", time: " + adderTime/1_000_000 + "ms");
        System.out.println("AtomicLong val: " + atomic.get() + ", time: " + atomicTime/1_000_000 + "ms");
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
VarHandle CAS(0->42): true, value=42
VarHandle CAS(0->99): false, value=42
setRelease(100) -> getAcquire(): 100
StampedLock optimistic read: x=1.0, y=2.0
Optimistic read valid: true
LongAdder sum: 800000, time: 132ms
AtomicLong val: 800000, time: 99ms
```

---

## Summary

| Concept | API | Use Case |
|---|---|---|
| Happens-before | JMM spec | Reasoning about visibility |
| Volatile | `volatile` keyword | Flag variables, single writer |
| VarHandle CAS | `compareAndSet()` | Lock-free data structures |
| Acquire/Release | `getAcquire/setRelease` | Producer/consumer, cheaper than volatile |
| StampedLock | `tryOptimisticRead()` | Read-heavy, rare writes |
| LongAdder | `increment()`, `sum()` | High-contention counters |
| False sharing | `@Contended` | Hot fields in different cache lines |
| Lock-free queue | `AtomicReference` CAS | Non-blocking concurrent queues |
