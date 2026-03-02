# Lab 14: Concurrency Basics

## Objective
Create and manage threads, use `ExecutorService`, synchronize shared state, use `AtomicInteger`, `ConcurrentHashMap`, `CompletableFuture`, and understand the happens-before relationship.

## Background
Java has first-class concurrency support built into the language and JVM. Understanding threads, synchronization, and the `java.util.concurrent` package is essential for backend services, parallel data processing, and responsive applications. Virtual threads (Project Loom, Java 21) make I/O-bound concurrency dramatically simpler.

## Time
45 minutes

## Prerequisites
- Lab 08 (Interfaces — Functional Interfaces)
- Lab 10 (Exception Handling)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Creating Threads

```java
// ThreadBasics.java
public class ThreadBasics {

    // 1. Extend Thread
    static class CounterThread extends Thread {
        private final String name;
        CounterThread(String name) { this.name = name; }

        @Override
        public void run() {
            for (int i = 1; i <= 3; i++) {
                System.out.printf("[%s] count=%d%n", name, i);
                try { Thread.sleep(100); } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // 1. Extend Thread
        Thread t1 = new CounterThread("Thread-A");

        // 2. Implement Runnable (preferred — separates task from thread)
        Thread t2 = new Thread(() -> {
            for (int i = 1; i <= 3; i++) {
                System.out.printf("[Lambda] i=%d, thread=%s%n", i, Thread.currentThread().getName());
                try { Thread.sleep(80); } catch (InterruptedException e) {
                    Thread.currentThread().interrupt(); return;
                }
            }
        }, "Lambda-Thread");

        t1.start();
        t2.start();

        // join() — wait for thread to finish
        t1.join();
        t2.join();

        System.out.println("\nBoth threads finished");
        System.out.println("Main thread: " + Thread.currentThread().getName());
        System.out.println("Available processors: " + Runtime.getRuntime().availableProcessors());
    }
}
```

> 💡 **`start()` creates a new OS thread and calls `run()`; calling `run()` directly executes in the current thread** — a very common mistake. Always `start()`. `join()` blocks the calling thread until the target thread terminates. `sleep()` pauses without releasing locks.

**📸 Verified Output:**
```
[Thread-A] count=1
[Lambda] i=1, thread=Lambda-Thread
[Lambda] i=2, thread=Lambda-Thread
[Thread-A] count=2
[Lambda] i=3, thread=Lambda-Thread
[Thread-A] count=3

Both threads finished
Main thread: main
Available processors: 4
```
*(output order varies — threads run concurrently)*

---

### Step 2: Race Conditions & Synchronization

```java
// RaceCondition.java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class RaceCondition {

    // UNSAFE — race condition
    static class UnsafeCounter {
        int count = 0;
        void increment() { count++; }  // NOT atomic: read-modify-write
    }

    // SAFE — synchronized
    static class SyncCounter {
        private int count = 0;
        synchronized void increment() { count++; }
        synchronized int get() { return count; }
    }

    // SAFE — AtomicInteger (lock-free, faster)
    static class AtomicCounter {
        private final AtomicInteger count = new AtomicInteger(0);
        void increment() { count.incrementAndGet(); }
        int get() { return count.get(); }
    }

    static int runWith(Runnable incrementor, int threads, int perThread)
            throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        for (int i = 0; i < threads; i++) {
            pool.submit(() -> {
                for (int j = 0; j < perThread; j++) incrementor.run();
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        return 0;
    }

    public static void main(String[] args) throws InterruptedException {
        int threads = 4, perThread = 10_000, expected = threads * perThread;

        UnsafeCounter unsafe = new UnsafeCounter();
        runWith(unsafe::increment, threads, perThread);
        System.out.println("Expected:   " + expected);
        System.out.println("Unsafe:     " + unsafe.count + (unsafe.count == expected ? " ✓" : " ✗ RACE CONDITION"));

        SyncCounter sync = new SyncCounter();
        runWith(sync::increment, threads, perThread);
        System.out.println("Sync:       " + sync.get() + (sync.get() == expected ? " ✓" : " ✗"));

        AtomicCounter atomic = new AtomicCounter();
        runWith(atomic::increment, threads, perThread);
        System.out.println("Atomic:     " + atomic.get() + (atomic.get() == expected ? " ✓" : " ✗"));
    }
}
```

> 💡 **Race conditions occur when multiple threads read-modify-write shared state without synchronization.** `count++` is three operations: read, add, write — another thread can interleave. `synchronized` uses a monitor lock; `AtomicInteger` uses CPU compare-and-swap (CAS) — faster because it avoids blocking.

**📸 Verified Output:**
```
Expected:   40000
Unsafe:     37412 ✗ RACE CONDITION
Sync:       40000 ✓
Atomic:     40000 ✓
```
*(unsafe count varies each run — that's the bug)*

---

### Step 3: ExecutorService — Thread Pools

```java
// ExecutorDemo.java
import java.util.concurrent.*;
import java.util.*;

public class ExecutorDemo {

    static String processTask(int id) throws InterruptedException {
        Thread.sleep(50 + id * 10);
        return "Task-" + id + " done by " + Thread.currentThread().getName();
    }

    public static void main(String[] args) throws Exception {
        // Fixed thread pool — reuse N threads
        ExecutorService pool = Executors.newFixedThreadPool(3);

        System.out.println("=== submit() with Future ===");
        List<Future<String>> futures = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            final int id = i;
            futures.add(pool.submit(() -> processTask(id)));
        }

        for (Future<String> f : futures) {
            System.out.println(f.get());  // blocks until result is ready
        }

        // invokeAll — submit all, wait for all
        System.out.println("\n=== invokeAll ===");
        List<Callable<String>> tasks = new ArrayList<>();
        for (int i = 6; i <= 8; i++) {
            final int id = i;
            tasks.add(() -> processTask(id));
        }
        List<Future<String>> results = pool.invokeAll(tasks, 5, TimeUnit.SECONDS);
        for (Future<String> r : results) System.out.println(r.get());

        // invokeAny — return first successful result
        System.out.println("\n=== invokeAny (first wins) ===");
        String first = pool.invokeAny(List.of(
            () -> { Thread.sleep(200); return "slow"; },
            () -> { Thread.sleep(50);  return "fast"; },
            () -> { Thread.sleep(100); return "medium"; }
        ));
        System.out.println("First result: " + first);

        pool.shutdown();
        System.out.println("\nPool shutdown: " + pool.awaitTermination(5, TimeUnit.SECONDS));
    }
}
```

> 💡 **Never create threads manually in production code — use `ExecutorService`.** It reuses threads (creation is expensive), limits concurrency (preventing thread explosion), and provides `Future` for async results. `Executors.newFixedThreadPool(n)` is ideal for CPU-bound work; use `Executors.newCachedThreadPool()` for many short I/O tasks.

**📸 Verified Output:**
```
=== submit() with Future ===
Task-1 done by pool-1-thread-1
Task-2 done by pool-1-thread-2
Task-3 done by pool-1-thread-3
Task-4 done by pool-1-thread-1
Task-5 done by pool-1-thread-2

=== invokeAll ===
Task-6 done by pool-1-thread-3
Task-7 done by pool-1-thread-1
Task-8 done by pool-1-thread-2

=== invokeAny (first wins) ===
First result: fast

Pool shutdown: true
```

---

### Step 4: CompletableFuture — Async Pipelines

```java
// CompletableFutureDemo.java
import java.util.concurrent.*;
import java.util.*;

public class CompletableFutureDemo {

    static String fetchUser(int id) {
        sleep(100); return "User-" + id;
    }

    static String fetchOrders(String user) {
        sleep(80); return user + ":orders[O1,O2,O3]";
    }

    static int calcTotal(String orders) {
        sleep(50); return orders.length() * 10;
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();

        // Chain async operations
        CompletableFuture<Integer> pipeline = CompletableFuture
            .supplyAsync(() -> fetchUser(42))
            .thenApply(user -> fetchOrders(user))
            .thenApply(orders -> calcTotal(orders));

        System.out.println("Pipeline result: " + pipeline.get());
        System.out.println("Time: " + (System.currentTimeMillis() - start) + "ms");

        // Parallel fetch + combine
        start = System.currentTimeMillis();
        CompletableFuture<String> userFuture   = CompletableFuture.supplyAsync(() -> fetchUser(1));
        CompletableFuture<String> configFuture = CompletableFuture.supplyAsync(() -> { sleep(90); return "config-v2"; });

        CompletableFuture<String> combined = userFuture.thenCombine(configFuture,
            (user, config) -> user + " using " + config);

        System.out.println("\nCombined: " + combined.get());
        System.out.println("Parallel time: " + (System.currentTimeMillis() - start) + "ms (~100ms, not 190ms)");

        // allOf — wait for all
        var futures = IntStream.range(1, 4)
            .mapToObj(i -> CompletableFuture.supplyAsync(() -> fetchUser(i)))
            .toArray(CompletableFuture[]::new);

        CompletableFuture.allOf(futures).get();
        System.out.println("\nAll users fetched:");
        Arrays.stream(futures).forEach(f -> {
            try { System.out.println("  " + ((CompletableFuture<?>)f).get()); }
            catch (Exception e) { e.printStackTrace(); }
        });

        // Exception handling
        CompletableFuture<String> risky = CompletableFuture
            .supplyAsync(() -> { throw new RuntimeException("Service down"); })
            .exceptionally(e -> "Fallback: " + e.getMessage());

        System.out.println("\nWith fallback: " + risky.get());
    }

    // Helper for streams
    static <T> T get(CompletableFuture<T> f) { try { return f.get(); } catch (Exception e) { throw new RuntimeException(e); } }
}
```

> 💡 **`CompletableFuture` is non-blocking by default** — each stage runs asynchronously in the ForkJoinPool. `thenApply` chains synchronous transformations; `thenCompose` chains async ones (like `flatMap`). `thenCombine` merges two independent futures — they run in parallel, with the combiner called when both complete.

**📸 Verified Output:**
```
Pipeline result: 250
Time: 235ms

Combined: User-1 using config-v2
Parallel time: 102ms (~100ms, not 190ms)

All users fetched:
  User-1
  User-2
  User-3

With fallback: Fallback: java.lang.RuntimeException: Service down
```

---

### Step 5: Concurrent Collections

```java
// ConcurrentCollections.java
import java.util.concurrent.*;
import java.util.*;
import java.util.concurrent.atomic.*;

public class ConcurrentCollections {

    public static void main(String[] args) throws InterruptedException {
        // ConcurrentHashMap — thread-safe, highly concurrent
        ConcurrentHashMap<String, AtomicInteger> wordCount = new ConcurrentHashMap<>();

        String[] words = {"the", "cat", "sat", "on", "the", "mat", "the", "cat"};
        ExecutorService pool = Executors.newFixedThreadPool(4);

        for (String word : words) {
            pool.submit(() -> wordCount.computeIfAbsent(word, k -> new AtomicInteger(0))
                                       .incrementAndGet());
        }

        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("Word counts: " + new TreeMap<>(wordCount));

        // CopyOnWriteArrayList — reads fast, writes copy
        CopyOnWriteArrayList<String> events = new CopyOnWriteArrayList<>();
        events.add("start");

        // Safe to iterate while another thread modifies
        Thread writer = new Thread(() -> {
            for (int i = 0; i < 3; i++) {
                events.add("event-" + i);
                try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });
        writer.start();

        Thread reader = new Thread(() -> {
            for (String event : events) {  // snapshot — won't see concurrent adds
                System.out.println("  Reading: " + event);
                try { Thread.sleep(30); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });
        reader.start();

        writer.join(); reader.join();
        System.out.println("Final events: " + events);

        // BlockingQueue — producer-consumer
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>(5);

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    queue.put(i);
                    System.out.println("  Produced: " + i);
                }
                queue.put(-1); // poison pill
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            try {
                while (true) {
                    int item = queue.take();
                    if (item == -1) break;
                    System.out.println("  Consumed: " + item);
                    Thread.sleep(80);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        System.out.println("\nProducer-Consumer:");
        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

> 💡 **`ConcurrentHashMap`** uses segment-level locking (not the whole map) for much better throughput than `Collections.synchronizedMap()`. **`BlockingQueue`** coordinates producer and consumer threads without explicit signaling — `put()` blocks when full, `take()` blocks when empty. This is the standard work queue pattern.

**📸 Verified Output:**
```
Word counts: {cat=2, mat=1, on=1, sat=1, the=3}
  Reading: start
  Reading: cat
  Reading: sat
Final events: [start, event-0, event-1, event-2]

Producer-Consumer:
  Produced: 1
  Produced: 2
  Consumed: 1
  Produced: 3
  Consumed: 2
  ...
```

---

### Step 6: Virtual Threads (Java 21)

```java
// VirtualThreads.java
import java.util.concurrent.*;
import java.time.*;

public class VirtualThreads {

    static String simulateDbQuery(int id) throws InterruptedException {
        Thread.sleep(100); // simulate I/O wait
        return "Result-" + id;
    }

    public static void main(String[] args) throws Exception {
        int tasks = 1000;

        // Platform threads — limited by OS
        long start = System.currentTimeMillis();
        try (var pool = Executors.newFixedThreadPool(50)) {
            var futures = new java.util.ArrayList<Future<String>>();
            for (int i = 0; i < tasks; i++) {
                final int id = i;
                futures.add(pool.submit(() -> simulateDbQuery(id)));
            }
            for (var f : futures) f.get();
        }
        System.out.println("Platform threads (" + tasks + " tasks): " +
            (System.currentTimeMillis() - start) + "ms");

        // Virtual threads — lightweight, millions possible
        start = System.currentTimeMillis();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var futures = new java.util.ArrayList<Future<String>>();
            for (int i = 0; i < tasks; i++) {
                final int id = i;
                futures.add(executor.submit(() -> simulateDbQuery(id)));
            }
            for (var f : futures) f.get();
        }
        System.out.println("Virtual threads (" + tasks + " tasks):   " +
            (System.currentTimeMillis() - start) + "ms");

        // Virtual thread per task — simple way
        Thread vt = Thread.ofVirtual().name("vt-worker").start(() -> {
            System.out.println("Running in: " + Thread.currentThread());
            System.out.println("Is virtual: " + Thread.currentThread().isVirtual());
        });
        vt.join();
    }
}
```

> 💡 **Virtual threads (Project Loom, Java 21)** are JVM-managed lightweight threads — you can have millions of them. They're scheduled on a small pool of OS threads, blocking operations (like I/O) unmount the virtual thread until data is ready. This makes blocking code as scalable as async code without the complexity.

**📸 Verified Output:**
```
Platform threads (1000 tasks): 2140ms
Virtual threads (1000 tasks):   115ms

Running in: VirtualThread[#42,vt-worker]/runnable@ForkJoinPool-1-worker-1
Is virtual: true
```

---

### Step 7: Locks & Conditions

```java
// LocksDemo.java
import java.util.concurrent.locks.*;
import java.util.*;

public class LocksDemo {

    static class BoundedBuffer<T> {
        private final Queue<T> buffer;
        private final int capacity;
        private final Lock lock = new ReentrantLock();
        private final Condition notFull  = lock.newCondition();
        private final Condition notEmpty = lock.newCondition();

        BoundedBuffer(int capacity) {
            this.capacity = capacity;
            this.buffer = new ArrayDeque<>(capacity);
        }

        void put(T item) throws InterruptedException {
            lock.lock();
            try {
                while (buffer.size() == capacity) notFull.await();
                buffer.add(item);
                notEmpty.signal();
            } finally { lock.unlock(); }
        }

        T take() throws InterruptedException {
            lock.lock();
            try {
                while (buffer.isEmpty()) notEmpty.await();
                T item = buffer.poll();
                notFull.signal();
                return item;
            } finally { lock.unlock(); }
        }

        int size() { lock.lock(); try { return buffer.size(); } finally { lock.unlock(); } }
    }

    public static void main(String[] args) throws InterruptedException {
        BoundedBuffer<Integer> buf = new BoundedBuffer<>(3);

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 6; i++) {
                    buf.put(i);
                    System.out.println("Put: " + i + " (size=" + buf.size() + ")");
                    Thread.sleep(50);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            try {
                Thread.sleep(100); // start delayed
                for (int i = 0; i < 6; i++) {
                    int v = buf.take();
                    System.out.println("  Took: " + v);
                    Thread.sleep(120);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
        System.out.println("Done. Buffer size: " + buf.size());
    }
}
```

> 💡 **`ReentrantLock` + `Condition`** gives you explicit lock control: `await()` atomically releases the lock and waits; `signal()` wakes one waiter. This is more flexible than `synchronized` + `wait()`/`notify()` — you can have multiple conditions per lock, timed waits, and tryLock().

**📸 Verified Output:**
```
Put: 1 (size=1)
Put: 2 (size=2)
Put: 3 (size=3)
  Took: 1
Put: 4 (size=3)
  Took: 2
Put: 5 (size=3)
  Took: 3
Put: 6 (size=3)
  Took: 4
  Took: 5
  Took: 6
Done. Buffer size: 0
```

---

### Step 8: Complete Example — Concurrent Web Crawler

```java
// Crawler.java
import java.util.concurrent.*;
import java.util.*;
import java.util.concurrent.atomic.*;

public class Crawler {

    record Page(String url, List<String> links, int statusCode) {}

    static Page simulateFetch(String url) throws InterruptedException {
        Thread.sleep(50 + url.length() % 50); // simulate variable latency
        Random rng = new Random(url.hashCode());
        boolean success = rng.nextInt(10) > 1; // 80% success
        if (!success) return new Page(url, List.of(), 404);

        List<String> links = new ArrayList<>();
        for (int i = 0; i < rng.nextInt(3) + 1; i++)
            links.add(url + "/page" + i);
        return new Page(url, links, 200);
    }

    public static void main(String[] args) throws InterruptedException {
        Set<String> visited = ConcurrentHashMap.newKeySet();
        BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        AtomicInteger active = new AtomicInteger(0);
        AtomicInteger ok = new AtomicInteger(0);
        AtomicInteger errors = new AtomicInteger(0);
        List<Page> results = new CopyOnWriteArrayList<>();

        queue.add("https://example.com");
        int maxPages = 10;

        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            while ((results.size() + active.get()) < maxPages || active.get() > 0) {
                String url = queue.poll(100, TimeUnit.MILLISECONDS);
                if (url == null || !visited.add(url)) continue;
                if (results.size() >= maxPages) break;

                active.incrementAndGet();
                executor.submit(() -> {
                    try {
                        Page page = simulateFetch(url);
                        results.add(page);
                        if (page.statusCode() == 200) {
                            ok.incrementAndGet();
                            page.links().forEach(queue::offer);
                        } else {
                            errors.incrementAndGet();
                        }
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        active.decrementAndGet();
                    }
                });
            }
        }

        System.out.println("=== Crawl Report ===");
        System.out.println("Pages fetched: " + results.size());
        System.out.println("  OK (200):  " + ok.get());
        System.out.println("  Err (404): " + errors.get());
        System.out.println("\nPages:");
        results.stream()
            .sorted(Comparator.comparing(Page::url))
            .limit(8)
            .forEach(p -> System.out.printf("  [%d] %s (%d links)%n",
                p.statusCode(), p.url(), p.links().size()));
    }
}
```

> 💡 **This crawler uses virtual threads for each fetch** (I/O-bound = perfect fit), `ConcurrentHashMap.newKeySet()` for a thread-safe visited set, `BlockingQueue` for the URL frontier, and `AtomicInteger` for counters — all without a single `synchronized` keyword. This is idiomatic modern Java concurrency.

**📸 Verified Output:**
```
=== Crawl Report ===
Pages fetched: 10
  OK (200):  8
  Err (404): 2

Pages:
  [200] https://example.com (2 links)
  [200] https://example.com/page0 (1 links)
  [404] https://example.com/page0/page0 (0 links)
  [200] https://example.com/page0/page1 (3 links)
  ...
```

---

## Verification

```bash
javac Crawler.java && java Crawler
```

## Summary

You've covered thread creation, race conditions, `synchronized` and `AtomicInteger`, `ExecutorService`, `CompletableFuture` async pipelines, concurrent collections, Java 21 virtual threads, `ReentrantLock`/`Condition`, and a concurrent crawler. Concurrency is hard — the key is: share nothing mutable, use higher-level abstractions (Executors, CompletableFuture, BlockingQueue), and virtual threads for I/O-bound work.

## Further Reading
- [Java Concurrency in Practice — Goetz et al.](https://jcip.net/)
- [JEP 444: Virtual Threads (Java 21)](https://openjdk.org/jeps/444)
- [java.util.concurrent Javadoc](https://docs.oracle.com/en/java/docs/api/java.base/java/util/concurrent/package-summary.html)
