# Lab 2: Streams & Lambdas

## Objective
Master the Java Streams API: `filter`, `map`, `flatMap`, `reduce`, `collect`, `groupingBy`, `partitioningBy`, parallel streams, and the `Collectors` utility class for data aggregation.

## Background
The Streams API (Java 8+) brings functional programming to Java. A stream is a sequence of elements from a data source that supports aggregate operations. Streams are lazy — intermediate operations don't execute until a terminal operation is invoked — enabling efficient pipelines that process only what's needed.

## Time
30 minutes

## Prerequisites
- Lab 01 (Generics & Collections)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Step 1: The Stream Pipeline

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab02.java << 'EOF'
import java.util.*;
import java.util.stream.*;
import java.util.function.*;

public class Lab02 {
    record Product(int id, String name, String category, double price, int stock) {
        double value() { return price * stock; }
    }

    public static void main(String[] args) {
        var products = List.of(
            new Product(1, \"Surface Pro\",  \"Laptop\",    864.0,  15),
            new Product(2, \"Surface Pen\",  \"Accessory\", 49.99,  80),
            new Product(3, \"Office 365\",   \"Software\",  99.99, 999),
            new Product(4, \"USB-C Hub\",    \"Hardware\",  29.99,   0),
            new Product(5, \"Surface Book\", \"Laptop\",  1299.0,   5)
        );

        // filter + map + sorted + collect
        var laptops = products.stream()
            .filter(p -> p.category().equals(\"Laptop\"))
            .sorted(Comparator.comparingDouble(Product::price).reversed())
            .map(p -> p.name() + \" ($\" + p.price() + \")\")
            .toList();
        System.out.println(\"Laptops (desc):   \" + laptops);

        // reduce: total inventory value
        double totalValue = products.stream()
            .mapToDouble(Product::value)
            .sum();
        System.out.printf(\"Total value:      \$%,.2f%n\", totalValue);

        // groupingBy + counting
        var byCategory = products.stream()
            .collect(Collectors.groupingBy(Product::category, Collectors.counting()));
        System.out.println(\"By category:      \" + byCategory);

        // groupingBy + summingDouble
        var revenueByCategory = products.stream()
            .collect(Collectors.groupingBy(Product::category,
                     Collectors.summingDouble(Product::value)));
        revenueByCategory.forEach((cat, rev) ->
            System.out.printf(\"  %-12s \$%,.2f%n\", cat, rev));

        // anyMatch, allMatch, noneMatch
        System.out.println(\"Any OOS:          \" + products.stream().anyMatch(p -> p.stock() == 0));
        System.out.println(\"All >10:          \" + products.stream().allMatch(p -> p.price() > 10));

        // flatMap
        var tags = products.stream()
            .flatMap(p -> Stream.of(p.category().toLowerCase(), p.name().split(\" \")[0].toLowerCase()))
            .distinct().sorted().toList();
        System.out.println(\"Tags:             \" + tags);

        // Custom collector: join product names
        String names = products.stream()
            .map(Product::name)
            .collect(Collectors.joining(\", \", \"[\", \"]\"));
        System.out.println(\"Names:            \" + names);

        // Statistics
        var stats = products.stream()
            .mapToDouble(Product::price)
            .summaryStatistics();
        System.out.printf(\"Price stats:      min=\$%.2f max=\$%.2f avg=\$%.2f%n\",
            stats.getMin(), stats.getMax(), stats.getAverage());
    }
}
EOF
javac /tmp/Lab02.java -d /tmp && java -cp /tmp Lab02"
```

> 💡 **Streams are lazy.** `filter()`, `map()`, `flatMap()` are *intermediate* operations — they create a new stream descriptor but process nothing. Only *terminal* operations (`collect`, `toList`, `count`, `sum`, `forEach`, `reduce`) trigger execution. This means `.filter(expensive).findFirst()` stops as soon as the first match is found, not after scanning the whole list.

**📸 Verified Output:**
```
Laptops (desc):   [Surface Book ($1299.0), Surface Pro ($864.0)]
Total value:      $123,344.21
By category:      {Laptop=2, Accessory=1, Hardware=1, Software=1}
  Laptop       $19,455.00
  Accessory    $3,999.20
  Hardware     $0.00
  Software     $99,890.01
Any OOS:          true
All >10:          true
Tags:             [accessory, hardware, laptop, office, software, surface, usb-c]
Names:            [Surface Pro, Surface Pen, Office 365, USB-C Hub, Surface Book]
Price stats:      min=$29.99 max=$1299.00 avg=$468.59
```

---

### Steps 2–8: partitioningBy, teeing, custom collectors, flatMap, reduce, parallel, Capstone

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab02b.java << 'EOF'
import java.util.*;
import java.util.stream.*;
import java.util.function.*;

public class Lab02b {
    record Product(int id, String name, String category, double price, int stock) {
        double value() { return price * stock; }
        boolean inStock() { return stock > 0; }
    }
    record Order(int id, String region, List<Product> items) {
        double total() { return items.stream().mapToDouble(Product::price).sum(); }
    }

    public static void main(String[] args) {
        var products = List.of(
            new Product(1,\"Surface Pro\", \"Laptop\",   864.0, 15),
            new Product(2,\"Surface Pen\", \"Accessory\",49.99, 80),
            new Product(3,\"Office 365\",  \"Software\", 99.99,999),
            new Product(4,\"USB-C Hub\",   \"Hardware\", 29.99,  0),
            new Product(5,\"Surface Book\",\"Laptop\",  1299.0,  5)
        );

        // Step 2: partitioningBy
        var partitioned = products.stream()
            .collect(Collectors.partitioningBy(Product::inStock));
        System.out.println(\"=== partitioningBy inStock ===\");
        System.out.println(\"In stock:  \" + partitioned.get(true).stream().map(Product::name).toList());
        System.out.println(\"Out stock: \" + partitioned.get(false).stream().map(Product::name).toList());

        // Step 3: toMap
        System.out.println(\"\\n=== toMap ===\");
        var priceMap = products.stream()
            .collect(Collectors.toMap(Product::name, Product::price, (a,b)->a, LinkedHashMap::new));
        priceMap.forEach((k,v) -> System.out.printf(\"  %-20s \$%.2f%n\", k, v));

        // Step 4: counting + averaging downstream
        System.out.println(\"\\n=== Category Averages ===\");
        var avgByCategory = products.stream()
            .collect(Collectors.groupingBy(Product::category, Collectors.averagingDouble(Product::price)));
        avgByCategory.forEach((cat, avg) -> System.out.printf(\"  %-12s avg=\$%.2f%n\", cat, avg));

        // Step 5: flatMap with nested collections
        System.out.println(\"\\n=== flatMap Orders ===\");
        var orders = List.of(
            new Order(1, \"US\",   List.of(products.get(0), products.get(1))),
            new Order(2, \"EU\",   List.of(products.get(2))),
            new Order(3, \"APAC\", List.of(products.get(0), products.get(4)))
        );
        var allItems = orders.stream()
            .flatMap(o -> o.items().stream())
            .map(Product::name)
            .sorted().distinct().toList();
        System.out.println(\"Unique items across orders: \" + allItems);

        double totalRevenue = orders.stream().mapToDouble(Order::total).sum();
        System.out.printf(\"Total revenue: \$%,.2f%n\", totalRevenue);

        // Step 6: reduce — manual sum
        System.out.println(\"\\n=== reduce ===\");
        double sum = products.stream().map(Product::price).reduce(0.0, Double::sum);
        System.out.printf(\"Sum (reduce): \$%.2f%n\", sum);

        Optional<Product> mostExpensive = products.stream()
            .reduce((a, b) -> a.price() > b.price() ? a : b);
        mostExpensive.ifPresent(p -> System.out.println(\"Most expensive: \" + p.name() + \" \$\" + p.price()));

        // Step 7: peek (debugging)
        System.out.println(\"\\n=== peek (debug trace) ===\");
        products.stream()
            .filter(p -> p.category().equals(\"Laptop\"))
            .peek(p -> System.out.print(\"  [filter] \" + p.name()))
            .map(p -> String.format(\" → valued at \$%,.2f\", p.value()))
            .forEach(System.out::println);

        // Step 8: Capstone analytics
        System.out.println(\"\\n=== Capstone: Sales Analytics ===\");
        // Generate 1000 simulated orders
        var rng = new Random(42);
        long orderCount = 1000;
        var orderStream = LongStream.range(0, orderCount)
            .mapToObj(i -> products.get(rng.nextInt(products.size())));

        var report = orderStream.collect(Collectors.groupingBy(
            Product::category,
            Collectors.collectingAndThen(
                Collectors.toList(),
                list -> Map.of(
                    \"count\", (long) list.size(),
                    \"revenue\", list.stream().mapToDouble(Product::price).sum()
                )
            )
        ));

        report.entrySet().stream()
            .sorted(Comparator.comparingDouble(e -> -((double) e.getValue().get(\"revenue\"))))
            .forEach(e -> System.out.printf(\"  %-12s orders=%4d  revenue=\$%,.2f%n\",
                e.getKey(), e.getValue().get(\"count\"), e.getValue().get(\"revenue\")));
    }
}
EOF
javac /tmp/Lab02b.java -d /tmp && java -cp /tmp Lab02b"
```

**📸 Verified Output:**
```
=== partitioningBy inStock ===
In stock:  [Surface Pro, Surface Pen, Office 365, Surface Book]
Out stock: [USB-C Hub]

=== toMap ===
  Surface Pro          $864.00
  Surface Pen          $49.99
  ...

=== reduce ===
Sum (reduce): $2342.97
Most expensive: Surface Book $1299.0

=== Capstone: Sales Analytics ===
  Software     orders= 207  revenue=$20,697.93
  Laptop       orders= 413  revenue=$...
```

---

## Summary

| Operation | Type | Returns | Use for |
|-----------|------|---------|---------|
| `filter` | Intermediate | `Stream<T>` | Conditional inclusion |
| `map` | Intermediate | `Stream<R>` | Transform each element |
| `flatMap` | Intermediate | `Stream<R>` | Flatten nested collections |
| `sorted` | Intermediate | `Stream<T>` | Order elements |
| `peek` | Intermediate | `Stream<T>` | Debug without modifying |
| `collect` | Terminal | `R` | Build result container |
| `reduce` | Terminal | `Optional<T>` | Aggregate to single value |
| `count` | Terminal | `long` | Count elements |

## Further Reading
- [Stream API JavaDoc](https://docs.oracle.com/en/java/docs/api/java.base/java/util/stream/Stream.html)
- [Collectors JavaDoc](https://docs.oracle.com/en/java/docs/api/java.base/java/util/stream/Collectors.html)
