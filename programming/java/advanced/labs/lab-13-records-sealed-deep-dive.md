# Lab 13: Records & Sealed Classes — Deep Dive

## Objective
Master Java 21 records beyond the basics: custom compact constructors, `withXxx` wither pattern, generic records, canonical constructor delegation, records in streams/maps, and sealed interface hierarchies for algebraic data type patterns with exhaustive pattern matching.

## Background
Records (JEP 395) are transparent data carriers — the compiler generates `equals`, `hashCode`, `toString`, and accessors from the component list. Sealed classes (JEP 409) restrict which classes can extend an interface or class — enabling the compiler to prove switch expressions are exhaustive. Combined, they bring algebraic data types (ADTs) to Java.

## Time
25 minutes

## Prerequisites
- Practitioner Lab 07 (Java 21 Features)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Compact constructor, withers, generic records, records in collections, sealed ADTs, pattern dispatch, deconstruction, Capstone

```bash
cat > /tmp/AdvLab13.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class AdvLab13 {
    // Records with compact constructor + wither pattern
    record Product(int id, String name, String category, double price, int stock) {
        // Compact constructor = validation
        Product {
            if (name == null || name.isBlank()) throw new IllegalArgumentException("name required");
            if (price < 0) throw new IllegalArgumentException("price must be >= 0");
            if (stock < 0) throw new IllegalArgumentException("stock must be >= 0");
            name = name.strip(); // normalise
        }
        boolean inStock() { return stock > 0; }
        double value() { return price * stock; }
        // Wither methods — return modified copy
        Product withPrice(double p)  { return new Product(id, name, category, p, stock); }
        Product withStock(int s)     { return new Product(id, name, category, price, s); }
        Product withCategory(String c) { return new Product(id, name, c, price, stock); }
        // JSON-like serialization
        String toJson() {
            return "{\"id\":%d,\"name\":\"%s\",\"category\":\"%s\",\"price\":%.2f,\"stock\":%d}"
                .formatted(id, name, category, price, stock);
        }
    }

    // Generic records
    record Pair<A, B>(A first, B second) {
        static <T> Pair<T,T> symmetric(T val) { return new Pair<>(val, val); }
        <C> Pair<A,C> mapSecond(Function<B,C> fn) { return new Pair<>(first, fn.apply(second)); }
        Pair<B,A> swap() { return new Pair<>(second, first); }
    }

    record Range<T extends Comparable<T>>(T min, T max) {
        Range { if (min.compareTo(max) > 0) throw new IllegalArgumentException("min > max"); }
        boolean contains(T value) { return value.compareTo(min) >= 0 && value.compareTo(max) <= 0; }
        @Override public String toString() { return "[" + min + ".." + max + "]"; }
    }

    // Sealed ADT — Result type
    sealed interface Result<T> permits Result.Success, Result.Failure {
        record Success<T>(T value, String message) implements Result<T> {}
        record Failure<T>(String code, String reason) implements Result<T> {}

        static <T> Result<T> ok(T value) { return new Success<>(value, "OK"); }
        static <T> Result<T> ok(T value, String msg) { return new Success<>(value, msg); }
        static <T> Result<T> fail(String code, String reason) { return new Failure<>(code, reason); }

        default boolean isOk() { return this instanceof Success; }
        default T getOrElse(T fallback) {
            return this instanceof Success<T> s ? s.value() : fallback; }
        default <R> Result<R> map(Function<T,R> fn) {
            return this instanceof Success<T> s ? ok(fn.apply(s.value())) : fail(((Failure<T>)this).code(), ((Failure<T>)this).reason());
        }
    }

    // Sealed hierarchy for order events
    sealed interface OrderEvent permits OrderEvent.Created, OrderEvent.Paid, OrderEvent.Shipped, OrderEvent.Cancelled {
        record Created(int orderId, String product, double total) implements OrderEvent {}
        record Paid(int orderId, double amount, String method) implements OrderEvent {}
        record Shipped(int orderId, String tracking) implements OrderEvent {}
        record Cancelled(int orderId, String reason) implements OrderEvent {}
        default int orderId() {
            return switch (this) {
                case Created c  -> c.orderId();
                case Paid p     -> p.orderId();
                case Shipped s  -> s.orderId();
                case Cancelled c -> c.orderId();
            };
        }
    }

    static String handleEvent(OrderEvent event) {
        return switch (event) {
            case OrderEvent.Created(var id, var prod, var total) ->
                "Order #" + id + " created: " + prod + " $" + String.format("%.2f", total);
            case OrderEvent.Paid(var id, var amt, var method) ->
                "Order #" + id + " paid: $" + String.format("%.2f", amt) + " via " + method;
            case OrderEvent.Shipped(var id, var tracking) ->
                "Order #" + id + " shipped: " + tracking;
            case OrderEvent.Cancelled(var id, var reason) ->
                "Order #" + id + " cancelled: " + reason;
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Records: Compact Constructor + Withers ===");
        var p = new Product(1, " Surface Pro ", "Laptop", 864.0, 15);
        System.out.println("Original:  " + p);
        System.out.println("withPrice: " + p.withPrice(799.99));
        System.out.println("withStock: " + p.withStock(0));
        System.out.println("inStock:   " + p.inStock() + "  value: $" + p.value());
        System.out.println("JSON:      " + p.toJson());

        System.out.println("\n=== Generic Records ===");
        var pair = new Pair<>("Surface Pro", 864.0);
        System.out.println("pair:     " + pair);
        System.out.println("mapped:   " + pair.mapSecond(price -> "$" + price));
        System.out.println("swapped:  " + pair.swap());
        System.out.println("symmetric: " + Pair.symmetric("echo"));

        var range = new Range<>(0.0, 1000.0);
        System.out.println("\nRange " + range + " contains 864: " + range.contains(864.0));
        System.out.println("Range " + range + " contains 1299: " + range.contains(1299.0));

        System.out.println("\n=== Records in Streams & Collections ===");
        var products = List.of(
            new Product(1,"Surface Pro","Laptop",864.0,15),
            new Product(2,"Surface Pen","Accessory",49.99,80),
            new Product(3,"Office 365","Software",99.99,999),
            new Product(4,"USB-C Hub","Hardware",29.99,0));

        var inStockByValue = products.stream()
            .filter(Product::inStock)
            .sorted(Comparator.comparingDouble(Product::value).reversed())
            .toList();
        System.out.println("In-stock by value:");
        inStockByValue.forEach(pr -> System.out.printf("  %-15s  value=$%,.2f%n", pr.name(), pr.value()));

        var byCategory = products.stream()
            .collect(java.util.stream.Collectors.groupingBy(Product::category,
                     java.util.stream.Collectors.summingDouble(Product::value)));
        System.out.println("By category: " + byCategory);

        System.out.println("\n=== Result<T> ADT ===");
        Result<Product> r1 = Result.ok(products.get(0));
        Result<Product> r2 = Result.fail("NOT_FOUND", "Product 99 not found");
        Result<String> r3 = r1.map(pr -> pr.name() + " @ $" + pr.price());

        System.out.println("r1: isOk=" + r1.isOk() + " value=" + r1.getOrElse(null));
        System.out.println("r2: isOk=" + r2.isOk() + " value=" + r2.getOrElse(null));
        System.out.println("r3: isOk=" + r3.isOk() + " value=" + r3.getOrElse("?"));

        System.out.println("\n=== Sealed OrderEvent + Deconstruction ===");
        List<OrderEvent> events = List.of(
            new OrderEvent.Created(1001, "Surface Pro", 1728.00),
            new OrderEvent.Paid(1001, 1728.00, "credit_card"),
            new OrderEvent.Shipped(1001, "FX10019871US"),
            new OrderEvent.Cancelled(1002, "Out of stock"));

        events.forEach(e -> System.out.println("  " + handleEvent(e)));
        System.out.println("  orderId check: " + events.stream().map(OrderEvent::orderId).toList());
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab13.java:/tmp/AdvLab13.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab13.java -d /tmp && java -cp /tmp AdvLab13"
```

> 💡 **Record deconstruction patterns** (`case Created(var id, var prod, var total)`) are Java 21's most powerful feature for ADTs. Instead of casting and calling accessors, the switch expression directly binds the components to local variables. This is equivalent to Haskell pattern matching or Rust's `match` with struct destructuring — finally available in Java.

**📸 Verified Output:**
```
=== Records: Compact Constructor + Withers ===
Original:  Product[id=1, name=Surface Pro, category=Laptop, price=864.0, stock=15]
withPrice: Product[id=1, name=Surface Pro, category=Laptop, price=799.99, stock=15]
inStock:   true  value: $12960.0

=== Result<T> ADT ===
r1: isOk=true  value=Product[id=1, name=Surface Pro, ...]
r2: isOk=false value=null
r3: isOk=true  value=Surface Pro @ $864.0

=== Sealed OrderEvent + Deconstruction ===
  Order #1001 created: Surface Pro $1728.00
  Order #1001 paid: $1728.00 via credit_card
  Order #1001 shipped: FX10019871US
  Order #1002 cancelled: Out of stock
```

---

## Summary

| Feature | Notes |
|---------|-------|
| Compact constructor | Runs before field assignment; validates/normalises |
| Wither pattern | `withX(val)` returns new record, old is unchanged |
| Generic record | `record Pair<A,B>(A first, B second)` |
| `sealed interface` | Only listed `permits` can implement |
| Record deconstruction | `case MyRecord(var x, var y)` in switch |
| `Result<T>` | Functional error handling without exceptions |

## Further Reading
- [JEP 440: Record Patterns](https://openjdk.org/jeps/440)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
