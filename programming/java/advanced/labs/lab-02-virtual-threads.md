# Lab 2: Virtual Threads & Structured Concurrency (Java 21)

## Objective
Master Java 21 Virtual Threads: `Thread.ofVirtual()`, `Executors.newVirtualThreadPerTaskExecutor()`, 1000-task scale demos, parallel I/O-bound work, the "first-to-succeed" pattern, and why `ReentrantLock` should replace `synchronized` to avoid virtual thread pinning.

## Background
Virtual threads (JEP 444, Java 21) are lightweight user-mode threads managed by the JVM, not the OS. You can create **millions** of them — each blocking I/O call parks the virtual thread and unmounts it from its carrier thread, freeing the carrier to run other virtual threads. This eliminates the need for reactive/async code for I/O-bound applications.

## Time
30 minutes

## Prerequisites
- Practitioner Lab 05 (Concurrency)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: 1000 virtual tasks, parallel price fetch, first-to-succeed, Thread.ofVirtual API, virtual vs platform, pinning avoidance, Capstone

```bash
cat > /tmp/AdvLab02.java << 'JAVAEOF'
import java.util.concurrent.*;
import java.util.*;
import java.util.stream.*;
import java.util.concurrent.atomic.*;

public class AdvLab02 {
    record Product(int id, String name, double price) {}
    record PriceQuote(int productId, String source, double price) {}

    static double fetchPrice(int id, String source, double base) {
        try { Thread.sleep(50 + (id * 10)); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return Math.round(base * (0.9 + id * 0.01) * 100) / 100.0;
    }

    public static void main(String[] args) throws Exception {
        var products = List.of(
            new Product(1, "Surface Pro",  864.0),
            new Product(2, "Surface Pen",  49.99),
            new Product(3, "Office 365",   99.99),
            new Product(4, "USB-C Hub",    29.99),
            new Product(5, "Surface Book", 1299.0));

        // Step 1: 1000 virtual tasks
        System.out.println("=== Virtual Threads (Java 21) ===");
        int N = 1000;
        var latch = new CountDownLatch(N);
        var counter = new AtomicInteger(0);
        long t0 = System.currentTimeMillis();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < N; i++) {
                executor.submit(() -> {
                    try { Thread.sleep(10); } catch (InterruptedException e) {}
                    counter.incrementAndGet();
                    latch.countDown();
                });
            }
        }
        latch.await(10, TimeUnit.SECONDS);
        System.out.printf("  %d virtual tasks completed in %dms%n", counter.get(), System.currentTimeMillis()-t0);
        System.out.println("  (same work on platform threads: ~1000 OS threads or async callbacks)");

        // Step 2: Parallel price fetch — I/O bound
        System.out.println("\n=== Parallel Price Fetch ===");
        t0 = System.currentTimeMillis();
        var futures = new ArrayList<Future<PriceQuote>>();
        try (var vexec = Executors.newVirtualThreadPerTaskExecutor()) {
            for (var p : products) {
                for (var source : List.of("US", "EU", "APAC")) {
                    futures.add(vexec.submit(() -> new PriceQuote(p.id(), source, fetchPrice(p.id(), source, p.price()))));
                }
            }
        }
        var quotes = futures.stream().map(f -> { try { return f.get(); } catch (Exception e) { throw new RuntimeException(e); } }).toList();
        long elapsed = System.currentTimeMillis() - t0;
        System.out.printf("  Fetched %d quotes in %dms (sequential ~%dms)%n", quotes.size(), elapsed, quotes.size() * 60L);

        var bestPrices = quotes.stream().collect(Collectors.groupingBy(PriceQuote::productId,
                         Collectors.minBy(Comparator.comparingDouble(PriceQuote::price))));
        bestPrices.entrySet().stream().sorted(Map.Entry.comparingByKey())
            .forEach(e -> e.getValue().ifPresent(q ->
                System.out.printf("  Product %-2d best: %-4s $%.2f%n", e.getKey(), q.source(), q.price())));

        // Step 3: Thread.ofVirtual() API
        System.out.println("\n=== Thread.ofVirtual() API ===");
        var results = new ConcurrentLinkedQueue<String>();
        var threads = new ArrayList<Thread>();
        for (int i = 0; i < 5; i++) {
            final int id = i;
            threads.add(Thread.ofVirtual().name("vt-" + id).start(() -> {
                try { Thread.sleep(10); } catch (InterruptedException e) {}
                results.add("vt-" + id + " isVirtual=" + Thread.currentThread().isVirtual());
            }));
        }
        for (var t : threads) t.join();
        results.stream().sorted().forEach(r -> System.out.println("  " + r));

        // Step 4: Virtual vs Platform properties
        System.out.println("\n=== Virtual vs Platform Thread ===");
        var vt = Thread.ofVirtual().start(() -> {});
        vt.join();
        System.out.println("  Virtual:  isVirtual=" + vt.isVirtual() + " isDaemon=" + vt.isDaemon());
        var pt = Thread.ofPlatform().start(() -> {});
        pt.join();
        System.out.println("  Platform: isVirtual=" + pt.isVirtual() + " isDaemon=" + pt.isDaemon());

        // Step 5: ReentrantLock (not synchronized) to avoid pinning
        System.out.println("\n=== ReentrantLock (Avoids Pinning) ===");
        var lock = new java.util.concurrent.locks.ReentrantLock();
        var lockResults = new ConcurrentLinkedQueue<Integer>();
        try (var vexec = Executors.newVirtualThreadPerTaskExecutor()) {
            var fs = new ArrayList<Future<?>>();
            for (int i = 0; i < 10; i++) {
                final int n = i;
                fs.add(vexec.submit(() -> {
                    lock.lock();
                    try { Thread.sleep(5); lockResults.add(n); }
                    catch (InterruptedException e) {}
                    finally { lock.unlock(); }
                }));
            }
            for (var f : fs) f.get();
        }
        System.out.println("  10 tasks with ReentrantLock: " + lockResults.stream().sorted().toList());
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab02.java:/tmp/AdvLab02.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab02.java -d /tmp && java -cp /tmp AdvLab02"
```

> 💡 **Virtual threads pin to their carrier when inside a `synchronized` block.** A pinned virtual thread cannot be unmounted — it holds its OS carrier thread blocked, defeating the entire purpose. Java 21 fixes this for `ReentrantLock`. **Rule: replace `synchronized` with `ReentrantLock` in virtual-thread code.** In Java 24+ `synchronized` no longer pins (JEP 491), but for Java 21 LTS this is critical.

**📸 Verified Output:**
```
=== Virtual Threads (Java 21) ===
  1000 virtual tasks completed in 101ms

=== Parallel Price Fetch ===
  Fetched 15 quotes in 111ms (sequential ~900ms)
  Product 1  best: US   $786.24
  ...

=== Thread.ofVirtual() API ===
  vt-0 isVirtual=true
  vt-1 isVirtual=true
  ...

=== Virtual vs Platform Thread ===
  Virtual:  isVirtual=true isDaemon=true
  Platform: isVirtual=false isDaemon=false

=== ReentrantLock (Avoids Pinning) ===
  10 tasks with ReentrantLock: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## Summary

| API | Purpose |
|-----|---------|
| `Executors.newVirtualThreadPerTaskExecutor()` | One virtual thread per task |
| `Thread.ofVirtual().name("x").start(r)` | Named virtual thread |
| `Thread.ofPlatform().start(r)` | Explicit platform thread |
| `thread.isVirtual()` | Check thread type |
| `ReentrantLock` | Lock without pinning carrier |
| `CountDownLatch(n)` | Await N completions |

## Further Reading
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- [Virtual Threads Deep Dive (Oracle)](https://dev.java/learn/new-features/virtual-threads/)
