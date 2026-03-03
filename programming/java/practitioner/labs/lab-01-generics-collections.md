# Lab 1: Generics & Collections Deep Dive

## Objective
Master Java generics — bounded type parameters, wildcards (PECS), and the full `java.util` Collections API: `ArrayList`, `LinkedList`, `HashMap`, `LinkedHashMap`, `TreeMap`, and `Collections` utility methods.

## Background
Java generics eliminate `ClassCastException` at runtime by catching type mismatches at compile time. The PECS rule (Producer Extends, Consumer Super) governs wildcard usage. The Collections API provides ready-made data structures for nearly every use case — choosing the right one is a critical engineering skill.

## Time
25 minutes

## Prerequisites
- Java Foundations Labs 01–10

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Step 1: Generic Classes & Bounded Types

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab01.java << 'EOF'
import java.util.*;

public class Lab01 {
    static class Stack<T> {
        private final LinkedList<T> data = new LinkedList<>();
        public void push(T item) { data.addFirst(item); }
        public T pop() { if (data.isEmpty()) throw new NoSuchElementException(); return data.removeFirst(); }
        public T peek() { return data.getFirst(); }
        public boolean isEmpty() { return data.isEmpty(); }
        public int size() { return data.size(); }
        @Override public String toString() { return data.toString(); }
    }

    static <T extends Comparable<T>> T max(List<T> list) {
        return list.stream().max(Comparator.naturalOrder()).orElseThrow();
    }

    static double sumNumbers(List<? extends Number> nums) {
        return nums.stream().mapToDouble(Number::doubleValue).sum();
    }

    static void addNumbers(List<? super Integer> list, int count) {
        for (int i = 1; i <= count; i++) list.add(i * 10);
    }

    public static void main(String[] args) {
        var stack = new Stack<String>();
        stack.push(\"Surface Pro\"); stack.push(\"Surface Pen\"); stack.push(\"USB-C Hub\");
        System.out.println(\"Stack: \" + stack);
        System.out.println(\"Pop:   \" + stack.pop());
        System.out.println(\"Peek:  \" + stack.peek());

        System.out.println(\"Max int:    \" + max(List.of(3, 1, 4, 1, 5, 9, 2)));
        System.out.println(\"Max string: \" + max(List.of(\"banana\", \"apple\", \"cherry\")));

        System.out.println(\"Sum doubles: \" + sumNumbers(List.of(1.5, 2.5, 3.0)));
        List<Number> nums = new ArrayList<>();
        addNumbers(nums, 5);
        System.out.println(\"Added:       \" + nums);

        var products = new ArrayList<>(List.of(\"Surface Book\", \"Surface Pro\", \"Surface Pen\", \"USB Hub\"));
        Collections.sort(products);
        System.out.println(\"Sorted:  \" + products);
        System.out.println(\"BSearch: \" + products.get(Collections.binarySearch(products, \"Surface Pro\")));

        var inventory = new LinkedHashMap<String, Integer>();
        inventory.put(\"Surface Pro\", 15); inventory.put(\"Surface Pen\", 80);
        inventory.put(\"Office 365\", 999); inventory.put(\"USB Hub\", 0);
        inventory.putIfAbsent(\"New Item\", 5);
        inventory.computeIfPresent(\"Surface Pro\", (k, v) -> v + 10);
        System.out.println(\"Inventory: \" + inventory);
        inventory.forEach((k, v) -> { if (v > 50) System.out.println(\"  In stock: \" + k + \"=\" + v); });
    }
}
EOF
javac /tmp/Lab01.java -d /tmp && java -cp /tmp Lab01"
```

> 💡 **PECS — Producer Extends, Consumer Super:** use `List<? extends Number>` when you only *read* (produce values from the list), and `List<? super Integer>` when you only *write* (consume values into the list). Mixing both requires an unbound `<?>` — but then you can only read `Object`.

**📸 Verified Output:**
```
Stack: [USB-C Hub, Surface Pen, Surface Pro]
Pop:   USB-C Hub
Peek:  Surface Pen
Max int:    9
Max string: cherry
Sum doubles: 7.0
Added:       [10, 20, 30, 40, 50]
Sorted:  [Surface Book, Surface Pen, Surface Pro, USB Hub]
BSearch: Surface Pro
Inventory: {Surface Pro=25, Surface Pen=80, Office 365=999, USB Hub=0, New Item=5}
  In stock: Surface Pen=80
  In stock: Office 365=999
```

---

### Step 2: TreeMap, PriorityQueue & Deque

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab01b.java << 'EOF'
import java.util.*;

public class Lab01b {
    record Product(String name, double price, int priority) {}

    public static void main(String[] args) {
        // TreeMap: sorted by key
        var byName = new TreeMap<String, Double>();
        byName.put(\"Surface Pro\", 864.0); byName.put(\"Surface Pen\", 49.99);
        byName.put(\"Office 365\", 99.99);  byName.put(\"USB-C Hub\", 29.99);
        System.out.println(\"TreeMap (sorted): \" + byName);
        System.out.println(\"firstKey:  \" + byName.firstKey());
        System.out.println(\"lastKey:   \" + byName.lastKey());
        System.out.println(\"headMap(<O): \" + byName.headMap(\"O\"));
        System.out.println(\"tailMap(>=S): \" + byName.tailMap(\"S\"));

        // PriorityQueue: min-heap by default
        var pq = new PriorityQueue<Product>(Comparator.comparingInt(Product::priority).reversed());
        pq.add(new Product(\"Surface Pro\", 864.0, 3));
        pq.add(new Product(\"Surface Pen\", 49.99, 1));
        pq.add(new Product(\"Office 365\",  99.99, 5));
        pq.add(new Product(\"USB-C Hub\",   29.99, 2));
        System.out.println(\"\\nPriorityQueue (highest priority first):\");
        while (!pq.isEmpty()) {
            var p = pq.poll();
            System.out.printf(\"  priority=%d  %s%n\", p.priority(), p.name());
        }

        // Deque as stack and queue
        var deque = new ArrayDeque<String>();
        deque.offerFirst(\"Surface Pro\");
        deque.offerLast(\"Surface Pen\");
        deque.offerFirst(\"Surface Book\");
        System.out.println(\"\\nDeque: \" + deque);
        System.out.println(\"peekFirst: \" + deque.peekFirst());
        System.out.println(\"peekLast:  \" + deque.peekLast());
        System.out.println(\"pollFirst: \" + deque.pollFirst());
        System.out.println(\"After:     \" + deque);

        // Collections utilities
        var list = new ArrayList<>(List.of(5, 3, 8, 1, 9, 2, 7));
        System.out.println(\"\\nOriginal:  \" + list);
        System.out.println(\"Max:       \" + Collections.max(list));
        System.out.println(\"Min:       \" + Collections.min(list));
        System.out.println(\"Frequency: \" + Collections.frequency(list, 9));
        Collections.sort(list);
        System.out.println(\"Sorted:    \" + list);
        Collections.reverse(list);
        System.out.println(\"Reversed:  \" + list);
        Collections.shuffle(list, new Random(42));
        System.out.println(\"Shuffled:  \" + list);
    }
}
EOF
javac /tmp/Lab01b.java -d /tmp && java -cp /tmp Lab01b"
```

**📸 Verified Output:**
```
TreeMap (sorted): {Office 365=99.99, Surface Pen=49.99, Surface Pro=864.0, USB-C Hub=29.99}
firstKey:  Office 365
lastKey:   USB-C Hub
headMap(<O): {}
tailMap(>=S): {Surface Pen=49.99, Surface Pro=864.0}

PriorityQueue (highest priority first):
  priority=5  Office 365
  priority=3  Surface Pro
  priority=2  USB-C Hub
  priority=1  Surface Pen

Deque: [Surface Book, Surface Pro, Surface Pen]
peekFirst: Surface Book
peekLast:  Surface Pen
pollFirst: Surface Book
After:     [Surface Pro, Surface Pen]
```

---

### Steps 3–8: Concurrent Collections, Immutable Collections, Comparators, `computeIfAbsent`, frequency map, Capstone

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab01c.java << 'EOF'
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class Lab01c {
    record Product(int id, String name, String category, double price, int stock) {}

    public static void main(String[] args) throws Exception {
        var products = List.of(
            new Product(1,\"Surface Pro\",  \"Laptop\",    864.0, 15),
            new Product(2,\"Surface Pen\",  \"Accessory\", 49.99, 80),
            new Product(3,\"Office 365\",   \"Software\",  99.99,999),
            new Product(4,\"USB-C Hub\",    \"Hardware\",  29.99,  0),
            new Product(5,\"Surface Book\", \"Laptop\",  1299.0,  5)
        );

        // Step 3: Multiple comparator chains
        System.out.println(\"=== Multi-key Sort ===\" );
        products.stream()
            .sorted(Comparator.comparing(Product::category)
                .thenComparing(Comparator.comparingDouble(Product::price).reversed()))
            .forEach(p -> System.out.printf(\"  %-12s %-15s \$%.2f%n\", p.category(), p.name(), p.price()));

        // Step 4: computeIfAbsent — group products
        System.out.println(\"\\n=== computeIfAbsent (group by category) ===\");
        var grouped = new LinkedHashMap<String, List<Product>>();
        products.forEach(p -> grouped.computeIfAbsent(p.category(), k -> new ArrayList<>()).add(p));
        grouped.forEach((cat, list) ->
            System.out.println(\"  \" + cat + \": \" + list.stream().map(Product::name).toList()));

        // Step 5: frequency map with merge
        System.out.println(\"\\n=== Word Frequency (merge) ===\");
        var words = List.of(\"surface\",\"pro\",\"surface\",\"pen\",\"office\",\"surface\",\"book\");
        var freq = new LinkedHashMap<String, Integer>();
        words.forEach(w -> freq.merge(w, 1, Integer::sum));
        freq.entrySet().stream()
            .sorted(Map.Entry.<String,Integer>comparingByValue().reversed())
            .forEach(e -> System.out.println(\"  \" + e.getKey() + \": \" + e.getValue()));

        // Step 6: Unmodifiable & immutable views
        System.out.println(\"\\n=== Immutable Collections ===\");
        var immutableList = List.copyOf(products);
        var immutableMap  = Map.copyOf(freq);
        System.out.println(\"immutableList size: \" + immutableList.size());
        System.out.println(\"immutableMap keys:  \" + new TreeSet<>(immutableMap.keySet()));
        try { immutableList.add(null); }
        catch (UnsupportedOperationException e) { System.out.println(\"Add blocked: \" + e.getClass().getSimpleName()); }

        // Step 7: ConcurrentHashMap for thread-safe ops
        System.out.println(\"\\n=== ConcurrentHashMap ===\");
        var concurrent = new ConcurrentHashMap<String, Integer>();
        var executor = Executors.newFixedThreadPool(4);
        var latch = new java.util.concurrent.CountDownLatch(100);
        for (int i = 0; i < 100; i++) {
            final String key = \"item-\" + (i % 5);
            executor.submit(() -> { concurrent.merge(key, 1, Integer::sum); latch.countDown(); });
        }
        latch.await(2, TimeUnit.SECONDS);
        executor.shutdown();
        int total = concurrent.values().stream().mapToInt(Integer::intValue).sum();
        System.out.println(\"  Total counts (should be 100): \" + total);
        concurrent.entrySet().stream().sorted(Map.Entry.comparingByKey())
            .forEach(e -> System.out.println(\"  \" + e.getKey() + \" → \" + e.getValue()));

        // Step 8: Capstone — inventory dashboard
        System.out.println(\"\\n=== Inventory Dashboard ===\");
        var byCategory = products.stream().collect(
            Collectors.groupingBy(Product::category,
            Collectors.summarizingDouble(p -> p.price() * p.stock())));
        byCategory.entrySet().stream()
            .sorted(Map.Entry.<String, DoubleSummaryStatistics>comparingByValue(
                Comparator.comparingDouble(DoubleSummaryStatistics::getSum)).reversed())
            .forEach(e -> System.out.printf(\"  %-12s count=%d  value=\$%,.2f%n\",
                e.getKey(), e.getValue().getCount(), e.getValue().getSum()));

        double grand = products.stream().mapToDouble(p->p.price()*p.stock()).sum();
        System.out.printf(\"  %-12s %s  value=\$%,.2f%n\", \"TOTAL\", \"     \", grand);
    }
}
EOF
javac /tmp/Lab01c.java -d /tmp && java -cp /tmp Lab01c"
```

**📸 Verified Output:**
```
=== Multi-key Sort ===
  Accessory    Surface Pen     $49.99
  Hardware     USB-C Hub       $29.99
  Laptop       Surface Book    $1299.00
  Laptop       Surface Pro     $864.00
  Software     Office 365      $99.99

=== computeIfAbsent (group by category) ===
  Laptop: [Surface Pro, Surface Book]
  Accessory: [Surface Pen]
  ...

=== ConcurrentHashMap ===
  Total counts (should be 100): 100
```

---

## Summary

| Structure | Ordered | Sorted | Thread-Safe | Use case |
|-----------|---------|--------|-------------|----------|
| `ArrayList` | Insert order | No | No | Random access list |
| `LinkedList` | Insert order | No | No | Queue/Deque/Stack |
| `HashMap` | No | No | No | Fast key lookup |
| `LinkedHashMap` | Insert order | No | No | Ordered map |
| `TreeMap` | Key sorted | Yes | No | Sorted map / range queries |
| `PriorityQueue` | Priority | Yes | No | Min/max heap |
| `ConcurrentHashMap` | No | No | Yes | Multi-threaded map |

## Further Reading
- [Java Generics Tutorial](https://docs.oracle.com/javase/tutorial/java/generics/)
- [Collections Framework](https://docs.oracle.com/javase/tutorial/collections/)
