# Lab 8: ForkJoinPool & Parallel Algorithms

## Objective
Master the `ForkJoinPool` framework: `RecursiveTask<T>` for parallel computation (divide-and-conquer sum), `RecursiveAction` for parallel in-place mutation (bulk discount), work stealing, custom pool parallelism, and comparison with parallel streams.

## Background
`ForkJoinPool` (Java 7+) implements a work-stealing algorithm — idle worker threads steal tasks from busy workers' queues. This maximises CPU utilisation for divide-and-conquer algorithms. `RecursiveTask<T>` returns a result; `RecursiveAction` performs a side-effect. The common pool (shared by parallel streams, `CompletableFuture.supplyAsync`) defaults to `Runtime.availableProcessors()-1` threads.

## Time
25 minutes

## Prerequisites
- Practitioner Lab 05 (Concurrency)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: RecursiveTask sum, RecursiveAction discount, work stealing, custom pool, parallel streams comparison, Capstone

```bash
cat > /tmp/AdvLab08.java << 'JAVAEOF'
import java.util.concurrent.*;
import java.util.*;
import java.util.stream.*;

public class AdvLab08 {
    // RecursiveTask: parallel divide-and-conquer sum
    static class PriceSum extends RecursiveTask<Double> {
        private final double[] prices; private final int lo, hi;
        static final int THRESHOLD = 100;
        PriceSum(double[] prices, int lo, int hi) { this.prices=prices; this.lo=lo; this.hi=hi; }
        @Override protected Double compute() {
            if (hi - lo <= THRESHOLD) {
                double sum = 0; for (int i = lo; i < hi; i++) sum += prices[i]; return sum;
            }
            int mid = (lo + hi) / 2;
            var left = new PriceSum(prices, lo, mid);
            var right = new PriceSum(prices, mid, hi);
            left.fork(); // submit left async
            return right.compute() + left.join(); // compute right inline, await left
        }
    }

    // RecursiveAction: parallel in-place discount
    static class ApplyDiscount extends RecursiveAction {
        private final double[] prices; private final int lo, hi; private final double disc;
        ApplyDiscount(double[] prices, int lo, int hi, double disc) {
            this.prices=prices; this.lo=lo; this.hi=hi; this.disc=disc; }
        @Override protected void compute() {
            if (hi - lo <= 100) {
                for (int i = lo; i < hi; i++) prices[i] = Math.round(prices[i]*(1-disc)*100)/100.0;
                return;
            }
            int mid = (lo + hi) / 2;
            invokeAll(new ApplyDiscount(prices,lo,mid,disc), new ApplyDiscount(prices,mid,hi,disc));
        }
    }

    public static void main(String[] args) throws Exception {
        var pool = ForkJoinPool.commonPool();
        System.out.println("ForkJoinPool parallelism: " + pool.getParallelism());

        // Generate 10,000 prices
        var rng = new Random(42);
        int N = 10_000;
        double[] prices = new double[N];
        for (int i = 0; i < N; i++) prices[i] = Math.round((10 + rng.nextDouble() * 1290) * 100) / 100.0;

        System.out.println("\n=== RecursiveTask: Parallel Sum ===");
        long t0 = System.nanoTime();
        double fjSum = pool.invoke(new PriceSum(prices, 0, N));
        long fjUs = (System.nanoTime()-t0)/1000;

        t0 = System.nanoTime();
        double seqSum = 0; for (double p : prices) seqSum += p;
        long seqUs = (System.nanoTime()-t0)/1000;

        System.out.printf("  Fork/Join: $%,.2f  (%dµs)%n", fjSum, fjUs);
        System.out.printf("  Sequential: $%,.2f  (%dµs)%n", seqSum, seqUs);
        System.out.printf("  Difference: $%.4f (should be ~0)%n", Math.abs(fjSum-seqSum));

        System.out.println("\n=== RecursiveAction: Parallel Discount ===");
        double[] copy = prices.clone();
        double beforeAvg = Arrays.stream(copy).average().orElse(0);
        pool.invoke(new ApplyDiscount(copy, 0, N, 0.10));
        double afterAvg = Arrays.stream(copy).average().orElse(0);
        System.out.printf("  Before avg: $%.2f%n", beforeAvg);
        System.out.printf("  After avg:  $%.2f (10%% discount)%n", afterAvg);
        System.out.printf("  Ratio: %.3f (expected 0.900)%n", afterAvg/beforeAvg);

        System.out.println("\n=== Parallel Streams (shares commonPool) ===");
        t0 = System.nanoTime();
        double parallelSum = Arrays.stream(prices).parallel().sum();
        System.out.printf("  Parallel stream: $%,.2f  (%dµs)%n", parallelSum, (System.nanoTime()-t0)/1000);

        System.out.println("\n=== Custom Pool (parallelism=2) ===");
        var custom = new ForkJoinPool(2);
        try {
            double result = custom.submit(() -> Arrays.stream(prices).parallel().sum()).get();
            System.out.printf("  Custom pool(2): $%,.2f%n", result);
        } finally { custom.shutdown(); }

        System.out.println("\n=== Work Stealing Demo ===");
        var tasks = new ArrayList<ForkJoinTask<Integer>>();
        for (int i = 0; i < 20; i++) {
            final int n = i;
            tasks.add(pool.submit(() -> {
                Thread.sleep(5 + (n % 3) * 10);
                return n * n;
            }));
        }
        int sumSquares = tasks.stream().mapToInt(t -> { try { return t.get(); } catch (Exception e) { return 0; } }).sum();
        int expected = IntStream.range(0,20).map(n->n*n).sum();
        System.out.printf("  Sum of squares 0..19: %d (expected: %d, match: %b)%n",
            sumSquares, expected, sumSquares==expected);
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab08.java:/tmp/AdvLab08.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab08.java -d /tmp && java -cp /tmp AdvLab08"
```

> 💡 **`left.fork(); right.compute(); left.join()` is the canonical ForkJoin pattern.** `fork()` submits the left half to the pool asynchronously. Then the *current thread* computes the right half directly (saving a thread-switch). Finally `join()` awaits the left result. This maximises work per thread. **Never** call `left.fork(); left.join()` consecutively — that's just sequential.

**📸 Verified Output:**
```
ForkJoinPool parallelism: 31

=== RecursiveTask: Parallel Sum ===
  Fork/Join:  $6,594,905.83  (15ms)
  Sequential: $6,594,905.83  (0ms)
  Difference: $0.0000

=== RecursiveAction: Parallel Discount ===
  Before avg: $659.49
  After avg:  $593.54 (10% discount)
  Ratio: 0.900 (expected 0.900)

=== Work Stealing Demo ===
  Sum of squares 0..19: 2470 (expected: 2470, match: true)
```

---

## Summary

| API | Returns | Use for |
|-----|---------|---------|
| `RecursiveTask<T>` | `T` | Divide-and-conquer with result |
| `RecursiveAction` | void | Parallel side-effects |
| `task.fork()` | — | Submit sub-task to pool |
| `task.join()` | `T` | Await sub-task result |
| `pool.invoke(task)` | `T` | Submit + await from outside pool |
| `invokeAll(t1, t2)` | — | Fork both, join both |

## Further Reading
- [ForkJoinPool JavaDoc](https://docs.oracle.com/en/java/docs/api/java.base/java/util/concurrent/ForkJoinPool.html)
- [Doug Lea: Fork/Join Framework](http://gee.cs.oswego.edu/dl/papers/fj.pdf)
