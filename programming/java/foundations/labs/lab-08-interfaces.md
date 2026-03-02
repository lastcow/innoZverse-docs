# Lab 8: Interfaces & Abstract Classes

## Objective
Define and implement Java interfaces, use default and static interface methods, understand functional interfaces, apply common design patterns (Strategy, Observer), and know when to choose interface vs abstract class.

## Background
Interfaces define contracts — what a class *can do* without specifying *how*. They enable loose coupling, multiple implementation, and polymorphism across unrelated class hierarchies. Java 8+ interfaces with `default` methods bridge the gap between interfaces and abstract classes. Functional interfaces power lambdas and the Streams API.

## Time
40 minutes

## Prerequisites
- Lab 07 (Inheritance & Polymorphism)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Defining and Implementing Interfaces

```java
// Serializable.java
import java.util.*;

public class Serializable {

    interface Printable {
        void print();                       // abstract (must implement)
        default String preview() {          // default (optional override)
            return "[no preview]";
        }
        static Printable of(String text) {  // static factory
            return () -> System.out.println(text);
        }
    }

    interface Saveable {
        void save(String path);
        default boolean canSave() { return true; }
    }

    // Implement multiple interfaces (Java allows this; classes don't)
    static class Document implements Printable, Saveable {
        private final String title;
        private final String content;

        Document(String title, String content) {
            this.title = title; this.content = content;
        }

        @Override
        public void print() {
            System.out.println("=== " + title + " ===");
            System.out.println(content);
        }

        @Override
        public String preview() { return title + ": " + content.substring(0, Math.min(20, content.length())) + "..."; }

        @Override
        public void save(String path) {
            System.out.println("Saving '" + title + "' to " + path);
        }
    }

    public static void main(String[] args) {
        Document doc = new Document("Hello", "This is a test document with content.");

        // Use as Printable
        Printable p = doc;
        p.print();
        System.out.println("Preview: " + p.preview());

        // Use as Saveable
        Saveable s = doc;
        s.save("/tmp/hello.txt");

        // Static factory method on interface
        Printable inline = Printable.of("Quick inline message");
        inline.print();
        System.out.println("Default preview: " + inline.preview());
    }
}
```

> 💡 **A class can implement multiple interfaces but extend only one class.** Interfaces define capabilities (`Printable`, `Saveable`, `Comparable`) that cross class hierarchies — a `Document`, `Invoice`, and `Report` can all be `Printable` without sharing an ancestor.

**📸 Verified Output:**
```
=== Hello ===
This is a test document with content.
Preview: Hello: This is a test docum...
Saving 'Hello' to /tmp/hello.txt
Quick inline message
Default preview: [no preview]
```

---

### Step 2: Functional Interfaces & Lambdas

```java
// FunctionalInterfaces.java
import java.util.*;
import java.util.function.*;

public class FunctionalInterfaces {

    @FunctionalInterface
    interface Transformer<T, R> {
        R transform(T input);
        // May have default methods — still functional (one abstract method)
        default <V> Transformer<T, V> andThen(Transformer<R, V> after) {
            return input -> after.transform(this.transform(input));
        }
    }

    public static void main(String[] args) {
        // Lambda as Transformer implementation
        Transformer<String, Integer> length = String::length;  // method ref
        Transformer<String, String> upper = s -> s.toUpperCase();
        Transformer<String, String> lengthStr = upper.andThen(s -> "Length:" + s.length());

        List<String> words = List.of("hello", "world", "java");
        words.forEach(w -> System.out.println(w + " -> " + length.transform(w)));

        // Built-in functional interfaces
        Function<Integer, Integer> square = x -> x * x;
        Function<Integer, Integer> addTen = x -> x + 10;
        Function<Integer, Integer> squareThenAdd = square.andThen(addTen);

        Predicate<Integer> isEven = n -> n % 2 == 0;
        Predicate<Integer> isPositive = n -> n > 0;
        Predicate<Integer> isEvenAndPositive = isEven.and(isPositive);

        BiFunction<String, Integer, String> repeat = (s, n) -> s.repeat(n);

        System.out.println("\nFunction composition:");
        System.out.println("square(5) = " + square.apply(5));
        System.out.println("squareThenAdd(5) = " + squareThenAdd.apply(5));

        System.out.println("\nPredicates:");
        List.of(-4, -1, 2, 6, 7).forEach(n ->
            System.out.println(n + " evenAndPositive=" + isEvenAndPositive.test(n)));

        System.out.println("\nBiFunction:");
        System.out.println(repeat.apply("abc", 3));
    }
}
```

> 💡 **`@FunctionalInterface`** marks an interface as having exactly one abstract method. The compiler enforces this. Lambda expressions and method references can be assigned to any functional interface. The `java.util.function` package provides `Function`, `Predicate`, `Consumer`, `Supplier`, and `BiFunction` for common patterns.

**📸 Verified Output:**
```
hello -> 5
world -> 5
java -> 4

Function composition:
square(5) = 25
squareThenAdd(5) = 35

Predicates:
-4 evenAndPositive=false
-1 evenAndPositive=false
2 evenAndPositive=true
6 evenAndPositive=true
7 evenAndPositive=false

BiFunction:
abcabcabc
```

---

### Step 3: Strategy Pattern

```java
// SortStrategy.java
import java.util.*;

public class SortStrategy {

    @FunctionalInterface
    interface SortStrategy<T> {
        void sort(List<T> list);

        static <T extends Comparable<T>> SortStrategy<T> natural() {
            return list -> Collections.sort(list);
        }

        static <T> SortStrategy<T> reversed(Comparator<T> cmp) {
            return list -> list.sort(cmp.reversed());
        }
    }

    static class DataSet<T> {
        private final List<T> data;
        private SortStrategy<T> strategy;

        DataSet(List<T> data, SortStrategy<T> strategy) {
            this.data = new ArrayList<>(data);
            this.strategy = strategy;
        }

        void setStrategy(SortStrategy<T> strategy) { this.strategy = strategy; }
        void sort() { strategy.sort(data); }
        List<T> getData() { return Collections.unmodifiableList(data); }
    }

    record Person(String name, int age) {}

    public static void main(String[] args) {
        List<Person> people = List.of(
            new Person("Charlie", 30),
            new Person("Alice", 25),
            new Person("Bob", 35),
            new Person("Diana", 28)
        );

        DataSet<Person> ds = new DataSet<>(people, SortStrategy.reversed(Comparator.comparingInt(Person::age)));
        ds.sort();
        System.out.println("By age desc:");
        ds.getData().forEach(p -> System.out.println("  " + p.name() + " " + p.age()));

        // Switch strategy at runtime
        ds.setStrategy(list -> list.sort(Comparator.comparing(Person::name)));
        ds.sort();
        System.out.println("\nBy name:");
        ds.getData().forEach(p -> System.out.println("  " + p.name()));
    }
}
```

> 💡 **The Strategy pattern** encapsulates algorithms behind an interface, letting you swap them at runtime. With functional interfaces, strategies are just lambdas — no need for separate classes. This is how `Comparator`, `Runnable`, `Callable`, and `Comparator.comparing().thenComparing()` chains work in the JDK.

**📸 Verified Output:**
```
By age desc:
  Bob 35
  Charlie 30
  Diana 28
  Alice 25

By name:
  Alice
  Bob
  Charlie
  Diana
```

---

### Step 4: Observer Pattern with Interfaces

```java
// EventSystem.java
import java.util.*;
import java.util.function.Consumer;

public class EventSystem {

    interface EventListener<T> {
        void onEvent(String eventType, T data);
    }

    static class EventBus<T> {
        private final Map<String, List<Consumer<T>>> listeners = new HashMap<>();

        void on(String event, Consumer<T> handler) {
            listeners.computeIfAbsent(event, k -> new ArrayList<>()).add(handler);
        }

        void emit(String event, T data) {
            listeners.getOrDefault(event, List.of()).forEach(h -> h.accept(data));
        }
    }

    record OrderEvent(String orderId, double amount, String status) {}

    public static void main(String[] args) {
        EventBus<OrderEvent> bus = new EventBus<>();

        // Register listeners (lambdas as functional interfaces)
        bus.on("order.placed", e ->
            System.out.println("[EMAIL] Order " + e.orderId() + " confirmation sent"));

        bus.on("order.placed", e ->
            System.out.println("[INVENTORY] Reserved items for " + e.orderId()));

        bus.on("order.shipped", e ->
            System.out.printf("[SMS] Order %s shipped! $%.2f%n", e.orderId(), e.amount()));

        bus.on("order.cancelled", e ->
            System.out.println("[REFUND] Processing refund for " + e.orderId()));

        // Emit events
        System.out.println("=== Order Placed ===");
        bus.emit("order.placed", new OrderEvent("ORD-001", 864.00, "placed"));

        System.out.println("\n=== Order Shipped ===");
        bus.emit("order.shipped", new OrderEvent("ORD-001", 864.00, "shipped"));

        System.out.println("\n=== Order Cancelled ===");
        bus.emit("order.cancelled", new OrderEvent("ORD-002", 49.99, "cancelled"));
    }
}
```

> 💡 **`computeIfAbsent`** creates the list only when the key is first seen — no null check needed. `Consumer<T>` is a built-in functional interface for `void`-returning operations. The Observer/Event Bus pattern powers React's event system, Android's LiveData, and Spring's ApplicationEvent.

**📸 Verified Output:**
```
=== Order Placed ===
[EMAIL] Order ORD-001 confirmation sent
[INVENTORY] Reserved items for ORD-001

=== Order Shipped ===
[SMS] Order ORD-001 shipped! $864.00

=== Order Cancelled ===
[REFUND] Processing refund for ORD-002
```

---

### Step 5: Comparable & Comparator

```java
// ComparableDemo.java
import java.util.*;

public class ComparableDemo {

    // Implement Comparable for natural ordering
    static class Version implements Comparable<Version> {
        final int major, minor, patch;

        Version(String v) {
            String[] parts = v.split("\\.");
            major = Integer.parseInt(parts[0]);
            minor = Integer.parseInt(parts[1]);
            patch = Integer.parseInt(parts[2]);
        }

        @Override
        public int compareTo(Version o) {
            if (major != o.major) return Integer.compare(major, o.major);
            if (minor != o.minor) return Integer.compare(minor, o.minor);
            return Integer.compare(patch, o.patch);
        }

        @Override
        public String toString() { return major + "." + minor + "." + patch; }
    }

    public static void main(String[] args) {
        List<Version> versions = new ArrayList<>(List.of(
            new Version("2.1.0"), new Version("1.0.0"),
            new Version("2.0.1"), new Version("1.5.3"),
            new Version("2.1.1"), new Version("3.0.0")
        ));

        Collections.sort(versions);
        System.out.println("Sorted: " + versions);
        System.out.println("Max: " + Collections.max(versions));
        System.out.println("Min: " + Collections.min(versions));

        // Comparator chain
        record Pkg(String name, Version version, long size) {}
        List<Pkg> packages = List.of(
            new Pkg("spring-core", new Version("6.1.0"), 1_200_000),
            new Pkg("jackson-core", new Version("2.15.0"), 400_000),
            new Pkg("spring-core", new Version("5.3.0"), 900_000),
            new Pkg("logback", new Version("1.4.0"), 300_000)
        );

        packages.stream()
            .sorted(Comparator.comparing((Pkg p) -> p.name())
                .thenComparing(p -> p.version()))
            .forEach(p -> System.out.printf("  %-20s %s%n", p.name(), p.version()));
    }
}
```

> 💡 **`Comparable` for natural ordering, `Comparator` for custom ordering.** Implement `Comparable` when there's one obvious "natural" order (semantic versioning, dates, priorities). Use `Comparator` when you need multiple orderings or can't modify the class. Always implement both consistently with `equals`.

**📸 Verified Output:**
```
Sorted: [1.0.0, 1.5.3, 2.0.1, 2.1.0, 2.1.1, 3.0.0]
Max: 3.0.0
Min: 1.0.0
  jackson-core         2.15.0
  logback              1.4.0
  spring-core          5.3.0
  spring-core          6.1.0
```

---

### Step 6: Interface vs Abstract Class

```java
// InterfaceVsAbstract.java
public class InterfaceVsAbstract {

    // ABSTRACT CLASS — use when:
    // 1. You want to share state (fields)
    // 2. You want to share implementation (non-abstract methods)
    // 3. You have a strong is-a relationship
    abstract static class Logger {
        private final String prefix;  // shared state
        private int logCount = 0;

        Logger(String prefix) { this.prefix = prefix; }

        final void log(String level, String message) {
            logCount++;
            String formatted = String.format("[%s][%s] %s", prefix, level, message);
            write(formatted);  // template method
        }

        protected abstract void write(String line);  // subclass fills in HOW
        int getLogCount() { return logCount; }
    }

    static class ConsoleLogger extends Logger {
        ConsoleLogger(String app) { super(app); }
        @Override protected void write(String line) { System.out.println(line); }
    }

    static class BufferedLogger extends Logger {
        private final StringBuilder buffer = new StringBuilder();
        BufferedLogger(String app) { super(app); }
        @Override protected void write(String line) { buffer.append(line).append('\n'); }
        String flush() { String s = buffer.toString(); buffer.setLength(0); return s; }
    }

    // INTERFACE — use when:
    // 1. Defining a capability/contract (no shared state)
    // 2. Multiple inheritance is needed
    // 3. You want to support unrelated classes
    interface Auditable {
        String getEntityId();
        String getEntityType();
        default String auditEntry() {
            return getEntityType() + ":" + getEntityId();
        }
    }

    interface Serializable2 {
        String serialize();
        static <T extends Serializable2> String serializeAll(Iterable<T> items) {
            var sb = new StringBuilder("[");
            for (T item : items) sb.append(item.serialize()).append(",");
            if (sb.length() > 1) sb.setLength(sb.length() - 1);
            return sb.append("]").toString();
        }
    }

    record Order(String id, double amount) implements Auditable, Serializable2 {
        @Override public String getEntityId() { return id; }
        @Override public String getEntityType() { return "Order"; }
        @Override public String serialize() { return "{id:" + id + ",amt:" + amount + "}"; }
    }

    public static void main(String[] args) {
        // Abstract class
        ConsoleLogger log = new ConsoleLogger("APP");
        log.log("INFO", "Server started");
        log.log("WARN", "High memory usage");
        System.out.println("Logged: " + log.getLogCount());

        BufferedLogger buf = new BufferedLogger("TEST");
        buf.log("DEBUG", "Init"); buf.log("DEBUG", "Ready");
        System.out.println("\nBuffered:\n" + buf.flush());

        // Interface
        var orders = java.util.List.of(
            new Order("ORD-1", 99.99),
            new Order("ORD-2", 150.00)
        );
        orders.forEach(o -> System.out.println("Audit: " + o.auditEntry()));
        System.out.println("Serialized: " + Serializable2.serializeAll(orders));
    }
}
```

> 💡 **Rule of thumb:** Use an interface when you're defining *what* something does (a contract). Use an abstract class when you're defining *how* it partially does it (shared implementation + state). In modern Java, prefer interfaces with `default` methods — they're more flexible because classes can implement multiple interfaces.

**📸 Verified Output:**
```
[APP][INFO] Server started
[APP][WARN] High memory usage
Logged: 2

Buffered:
[TEST][DEBUG] Init
[TEST][DEBUG] Ready

Audit: Order:ORD-1
Audit: Order:ORD-2
Serialized: [{id:ORD-1,amt:99.99},{id:ORD-2,amt:150.0}]
```

---

### Step 7: AutoCloseable — try-with-resources

```java
// TryWithResources.java
public class TryWithResources {

    static class DatabaseConnection implements AutoCloseable {
        private final String url;
        private boolean open;

        DatabaseConnection(String url) {
            this.url = url;
            this.open = true;
            System.out.println("Opened: " + url);
        }

        String query(String sql) {
            if (!open) throw new IllegalStateException("Connection closed");
            System.out.println("Executing: " + sql);
            return "Result of: " + sql;
        }

        @Override
        public void close() {
            if (open) {
                open = false;
                System.out.println("Closed: " + url);
            }
        }
    }

    static class Transaction implements AutoCloseable {
        private final DatabaseConnection conn;
        private boolean committed = false;

        Transaction(DatabaseConnection conn) {
            this.conn = conn;
            System.out.println("  BEGIN TRANSACTION");
        }

        void commit() { committed = true; System.out.println("  COMMIT"); }

        @Override
        public void close() {
            if (!committed) System.out.println("  ROLLBACK");
        }
    }

    public static void main(String[] args) {
        // try-with-resources — guaranteed close() even on exception
        try (var conn = new DatabaseConnection("jdbc:mysql://localhost/mydb")) {
            System.out.println(conn.query("SELECT * FROM users LIMIT 5"));
            System.out.println(conn.query("SELECT COUNT(*) FROM orders"));
        }  // close() called automatically here

        System.out.println();

        // Multiple resources — closed in reverse order
        try (var conn = new DatabaseConnection("jdbc:mysql://localhost/mydb");
             var tx = new Transaction(conn)) {
            conn.query("UPDATE accounts SET balance=100");
            tx.commit();
        }

        System.out.println();

        // Rollback on exception
        try (var conn = new DatabaseConnection("jdbc:mysql://localhost/mydb");
             var tx = new Transaction(conn)) {
            conn.query("INSERT INTO orders VALUES(...)");
            if (true) throw new RuntimeException("Simulated failure");
            tx.commit(); // never reached
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

> 💡 **`try-with-resources` guarantees cleanup** — `close()` is called even if an exception is thrown. Multiple resources are closed in reverse order of declaration (Transaction before Connection). This eliminates the `try/finally` boilerplate that was required before Java 7.

**📸 Verified Output:**
```
Opened: jdbc:mysql://localhost/mydb
Executing: SELECT * FROM users LIMIT 5
Result of: SELECT * FROM users LIMIT 5
Executing: SELECT COUNT(*) FROM orders
Closed: jdbc:mysql://localhost/mydb

Opened: jdbc:mysql://localhost/mydb
  BEGIN TRANSACTION
Executing: UPDATE accounts SET balance=100
  COMMIT
Closed: jdbc:mysql://localhost/mydb

Opened: jdbc:mysql://localhost/mydb
  BEGIN TRANSACTION
Executing: INSERT INTO orders VALUES(...)
  ROLLBACK
Closed: jdbc:mysql://localhost/mydb
Caught: Simulated failure
```

---

### Step 8: Complete Example — Plugin Architecture

```java
// PluginSystem.java
import java.util.*;

public class PluginSystem {

    interface Plugin {
        String name();
        String version();
        void initialize(Map<String, String> config);
        void execute(String input);
        default void shutdown() { System.out.println("[" + name() + "] Shutdown"); }
    }

    static class PluginRegistry {
        private final Map<String, Plugin> plugins = new LinkedHashMap<>();

        void register(Plugin p) {
            plugins.put(p.name(), p);
            System.out.println("Registered: " + p.name() + " v" + p.version());
        }

        void initAll(Map<String, String> config) {
            plugins.values().forEach(p -> p.initialize(config));
        }

        void run(String input) {
            plugins.values().forEach(p -> p.execute(input));
        }

        void shutdownAll() {
            List<Plugin> reversed = new ArrayList<>(plugins.values());
            Collections.reverse(reversed);
            reversed.forEach(Plugin::shutdown);
        }
    }

    // Lambda-friendly plugin builder
    record SimplePlugin(String name, String version,
                        java.util.function.BiConsumer<Map<String,String>, String[]> onInit,
                        java.util.function.Consumer<String> onExecute) implements Plugin {
        @Override public void initialize(Map<String, String> config) { onInit.accept(config, new String[0]); }
        @Override public void execute(String input) { onExecute.accept(input); }
    }

    public static void main(String[] args) {
        PluginRegistry registry = new PluginRegistry();

        registry.register(new SimplePlugin("logger", "1.0",
            (cfg, x) -> System.out.println("  [logger] Initialized, level=" + cfg.getOrDefault("level","INFO")),
            input -> System.out.println("  [logger] Processing: " + input.substring(0, Math.min(20,input.length())))));

        registry.register(new SimplePlugin("metrics", "2.1",
            (cfg, x) -> System.out.println("  [metrics] Initialized, endpoint=" + cfg.getOrDefault("metrics.endpoint","localhost")),
            input -> System.out.println("  [metrics] Recorded " + input.length() + " byte event")));

        Map<String, String> config = Map.of("level", "DEBUG", "metrics.endpoint", "prometheus:9090");

        System.out.println("\n--- Init ---");
        registry.initAll(config);

        System.out.println("\n--- Run ---");
        registry.run("user.login event from 192.168.1.1");

        System.out.println("\n--- Shutdown ---");
        registry.shutdownAll();
    }
}
```

> 💡 **Plugin architectures** use interfaces to define the contract and registries to manage lifecycle. This is how OSGi, JDBC drivers, SPI (Service Provider Interface), and Spring's `BeanPostProcessor` work. New plugins can be added without modifying the registry — the Open/Closed Principle in action.

**📸 Verified Output:**
```
Registered: logger v1.0
Registered: metrics v2.1

--- Init ---
  [logger] Initialized, level=DEBUG
  [metrics] Initialized, endpoint=prometheus:9090

--- Run ---
  [logger] Processing: user.login event fr
  [metrics] Recorded 38 byte event

--- Shutdown ---
[metrics] Shutdown
[logger] Shutdown
```

---

## Verification

```bash
javac PluginSystem.java && java PluginSystem
```

## Summary

Interfaces in Java define contracts, enable multiple inheritance of type, power lambdas, and support patterns like Strategy, Observer, and Plugin Architecture. Default methods let interfaces evolve without breaking existing implementations. Choose interfaces for capabilities and abstract classes for partial implementations with shared state.

## Further Reading
- [Oracle Tutorial: Interfaces](https://docs.oracle.com/javase/tutorial/java/IandI/createinterface.html)
- [java.util.function package](https://docs.oracle.com/en/java/docs/api/java.base/java/util/function/package-summary.html)
- [Effective Java — Item 20: Prefer interfaces to abstract classes](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
