# Lab 5: Concurrency — Threads, ExecutorService & CompletableFuture

## Objective
Master Java concurrency: `ExecutorService` thread pools, `CountDownLatch`, `CompletableFuture` pipelines, `ConcurrentHashMap`, and atomic operations for thread-safe inventory management.

## Background
Java concurrency is managed through the `java.util.concurrent` package. Rather than creating raw `Thread` objects, modern Java uses `ExecutorService` to manage thread pools efficiently. `CompletableFuture` (Java 8+) enables non-blocking async pipelines with composition operators like `thenApply`, `thenCompose`, and `allOf`.

## Time
30 minutes

## Prerequisites
- Lab 04 (Exception Handling)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Thread pool, CompletableFuture pipeline, CAS inventory, parallel price fetch, Capstone

```bash
cat > /tmp/Lab05.java << 'JAVAEOF'
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.stream.*;

public class Lab05 {
    record Product(int id, String name, double price) {}

    static class Inventory {
        private final ConcurrentHashMap<Integer, AtomicInteger> stock = new ConcurrentHashMap<>();
        void add(int id, int qty) { stock.computeIfAbsent(id, k -> new AtomicInteger(0)).addAndGet(qty); }
        boolean reserve(int id, int qty) {
            var s = stock.get(id);
            if (s == null) return false;
            while (true) {
                int cur = s.get();
                if (cur < qty) return false;
                if (s.compareAndSet(cur, cur - qty)) return true;
            }
        }
        int get(int id) { return stock.getOrDefault(id, new AtomicInteger(0)).get(); }
    }

    static double fetchPrice(int id, double base) {
        try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return Math.round(base * 0.95 * 100) / 100.0;
    }

    public static void main(String[] args) throws Exception {
        var executor = Executors.newFixedThreadPool(4);
        var latch = new CountDownLatch(5);
        var results = new ConcurrentLinkedQueue<String>();

        for (int i = 1; i <= 5; i++) {
            final int id = i;
            executor.submit(() -> {
                results.add("  Task-" + id + " on " + Thread.currentThread().getName());
                latch.countDown();
            });
        }
        latch.await(2, TimeUnit.SECONDS);
        results.stream().sorted().forEach(System.out::println);
        System.out.println("All tasks done");

        var products = List.of(
            new Product(1, "Surface Pro", 864.0),
            new Product(2, "Surface Pen", 49.99),
            new Product(3, "Office 365",  99.99));

        long t0 = System.currentTimeMillis();
        List<CompletableFuture<String>> futures = products.stream()
            .map(p -> CompletableFuture
                .supplyAsync(() -> fetchPrice(p.id(), p.price()), executor)
                .thenApply(live -> String.format("  %s: base=$%.2f live=$%.2f", p.name(), p.price(), live)))
            .toList();

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("\nParallel price fetch (" + (System.currentTimeMillis()-t0) + "ms):");
        futures.forEach(f -> System.out.println(f.join()));

        var orderResult = CompletableFuture
            .supplyAsync(() -> "Surface Pro validated", executor)
            .thenApply(s -> s + " -> charged $864.00")
            .thenApply(s -> s + " -> order #1001")
            .exceptionally(e -> "Order failed: " + e.getMessage())
            .join();
        System.out.println("\nPipeline: " + orderResult);

        var inv = new Inventory();
        inv.add(1, 100);
        var tasks = new ArrayList<CompletableFuture<Boolean>>();
        for (int i = 0; i < 10; i++) {
            tasks.add(CompletableFuture.supplyAsync(() -> inv.reserve(1, 5), executor));
        }
        CompletableFuture.allOf(tasks.toArray(new CompletableFuture[0])).join();
        long succeeded = tasks.stream().filter(f -> f.join()).count();
        System.out.printf("%nConcurrent reserves: %d/10 succeeded, stock remaining=%d%n", succeeded, inv.get(1));
        executor.shutdown();
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab05.java:/tmp/Lab05.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab05.java -d /tmp && java -cp /tmp Lab05"
```

> 💡 **`compareAndSet` (CAS) is the key to lock-free concurrency.** Instead of using `synchronized`, CAS atomically checks whether the current value equals an expected value, and only updates if it does. If another thread modified the value meanwhile, CAS fails — and the `while(true)` loop retries. This is much faster than locking for low-contention scenarios.

**📸 Verified Output:**
```
  Task-1 on pool-1-thread-1
  Task-2 on pool-1-thread-2
  Task-3 on pool-1-thread-3
  Task-4 on pool-1-thread-4
  Task-5 on pool-1-thread-4
All tasks done

Parallel price fetch (110ms):
  Surface Pro: base=$864.00 live=$820.80
  Surface Pen: base=$49.99 live=$47.49
  Office 365: base=$99.99 live=$94.99

Pipeline: Surface Pro validated -> charged $864.00 -> order #1001

Concurrent reserves: 10/10 succeeded, stock remaining=50
```

---

## Summary

| API | Use for |
|-----|---------|
| `Executors.newFixedThreadPool(n)` | Bounded thread pool |
| `CountDownLatch(n)` | Wait for N tasks to complete |
| `CompletableFuture.supplyAsync` | Async computation in pool |
| `thenApply` | Transform result (like `map`) |
| `allOf(...).join()` | Wait for all futures |
| `exceptionally` | Handle errors in pipeline |
| `ConcurrentHashMap` | Thread-safe map |
| `AtomicInteger.compareAndSet` | Lock-free CAS update |

## Further Reading
- [Java Concurrency in Practice (Goetz)](https://jcip.net/)
- [CompletableFuture](https://docs.oracle.com/en/java/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
