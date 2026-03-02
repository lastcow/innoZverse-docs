# Lab 6: OOP — Classes, Objects & Encapsulation

## Objective
Design and implement Java classes with fields, constructors, methods, and proper encapsulation. Use access modifiers, getters/setters, `this`, `static` members, and records.

## Background
Object-Oriented Programming is Java's core paradigm. Classes are blueprints; objects are instances. Encapsulation — hiding implementation details behind a public interface — makes code maintainable. Java 16+ records reduce boilerplate for pure data classes. Understanding class design is the foundation for everything from Android apps to enterprise Spring Boot services.

## Time
40 minutes

## Prerequisites
- Lab 02 (Variables & Primitives)
- Lab 05 (Control Flow)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Your First Class

```java
// BankAccount.java
public class BankAccount {
    // Fields (instance variables)
    private String owner;
    private String accountId;
    private double balance;
    private int transactionCount;

    // Constructor
    public BankAccount(String owner, String accountId, double initialDeposit) {
        this.owner = owner;
        this.accountId = accountId;
        this.balance = initialDeposit;
        this.transactionCount = 1;
    }

    // Methods
    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Deposit must be positive");
        balance += amount;
        transactionCount++;
    }

    public void withdraw(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Withdrawal must be positive");
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount;
        transactionCount++;
    }

    // Getters
    public double getBalance() { return balance; }
    public String getOwner() { return owner; }
    public String getAccountId() { return accountId; }
    public int getTransactionCount() { return transactionCount; }

    @Override
    public String toString() {
        return String.format("BankAccount[%s, owner=%s, balance=$%.2f, txns=%d]",
            accountId, owner, balance, transactionCount);
    }

    public static void main(String[] args) {
        BankAccount acct = new BankAccount("Dr. Chen", "ACC-001", 1000.00);
        System.out.println(acct);

        acct.deposit(500.00);
        acct.withdraw(200.00);
        acct.deposit(50.00);

        System.out.println(acct);
        System.out.printf("Balance: $%.2f%n", acct.getBalance());

        try {
            acct.withdraw(10000.00);
        } catch (IllegalStateException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }
}
```

> 💡 **`private` fields + `public` methods** is encapsulation. External code can't directly modify `balance` — it must go through `deposit()`/`withdraw()`, which enforce business rules. This is how you prevent invalid state: `balance` can never go negative.

**📸 Verified Output:**
```
BankAccount[ACC-001, owner=Dr. Chen, balance=$1000.00, txns=1]
BankAccount[ACC-001, owner=Dr. Chen, balance=$1350.00, txns=4]
Balance: $1350.00
Error: Insufficient funds
```

---

### Step 2: Constructors & Constructor Chaining

```java
// Rectangle.java
public class Rectangle {
    private final double width;
    private final double height;

    // Primary constructor
    public Rectangle(double width, double height) {
        if (width <= 0 || height <= 0)
            throw new IllegalArgumentException("Dimensions must be positive");
        this.width = width;
        this.height = height;
    }

    // this() — delegates to primary constructor
    public Rectangle(double side) {
        this(side, side);  // square
    }

    // Default 1x1
    public Rectangle() {
        this(1.0);
    }

    public double area() { return width * height; }
    public double perimeter() { return 2 * (width + height); }
    public boolean isSquare() { return width == height; }

    public Rectangle scaled(double factor) {
        return new Rectangle(width * factor, height * factor);
    }

    @Override
    public String toString() {
        return String.format("Rectangle(%.1f × %.1f)", width, height);
    }

    public static void main(String[] args) {
        Rectangle r1 = new Rectangle(5, 3);
        Rectangle r2 = new Rectangle(4);      // square
        Rectangle r3 = new Rectangle();       // 1×1

        System.out.println(r1 + " area=" + r1.area() + " square=" + r1.isSquare());
        System.out.println(r2 + " area=" + r2.area() + " square=" + r2.isSquare());
        System.out.println(r3);

        Rectangle big = r1.scaled(2);
        System.out.println("Scaled 2x: " + big + " area=" + big.area());
    }
}
```

> 💡 **`this(...)` constructor chaining** avoids duplicating initialization logic. The delegating constructor must call `this(...)` as its first statement. Mark fields `final` when they shouldn't change after construction — the compiler enforces this.

**📸 Verified Output:**
```
Rectangle(5.0 × 3.0) area=15.0 square=false
Rectangle(4.0 × 4.0) area=16.0 square=true
Rectangle(1.0 × 1.0)
Scaled 2x: Rectangle(10.0 × 6.0) area=60.0
```

---

### Step 3: Static Members — Class-Level State

```java
// Counter.java
public class Counter {
    // static — shared across ALL instances
    private static int totalCreated = 0;
    private static final int MAX_COUNT = 1000;

    // instance — unique to each object
    private final int id;
    private int count;
    private final String name;

    public Counter(String name) {
        this.name = name;
        this.id = ++totalCreated;
        this.count = 0;
    }

    public void increment() {
        if (count >= MAX_COUNT) throw new IllegalStateException("Max reached");
        count++;
    }

    public void increment(int n) {
        for (int i = 0; i < n; i++) increment();
    }

    public int getCount() { return count; }
    public int getId() { return id; }

    // Static factory method (alternative to constructor)
    public static Counter of(String name, int initialCount) {
        Counter c = new Counter(name);
        c.increment(initialCount);
        return c;
    }

    // Static utility
    public static int getTotalCreated() { return totalCreated; }

    @Override
    public String toString() {
        return String.format("Counter#%d(%s)=%d", id, name, count);
    }

    public static void main(String[] args) {
        Counter a = new Counter("alpha");
        Counter b = Counter.of("beta", 5);
        Counter c = new Counter("gamma");

        a.increment(3);
        b.increment(2);

        System.out.println(a);
        System.out.println(b);
        System.out.println(c);
        System.out.println("Total counters created: " + Counter.getTotalCreated());

        // Static final constant
        System.out.println("Max count allowed: " + Counter.MAX_COUNT);
    }
}
```

> 💡 **`static` belongs to the class, not instances.** `totalCreated` increments every time `new Counter()` is called, regardless of which instance you're looking at. Static factory methods (`of()`) are preferred over constructors when: the name conveys meaning, you want to return cached instances, or the return type might differ.

**📸 Verified Output:**
```
Counter#1(alpha)=3
Counter#2(beta)=7
Counter#3(gamma)=0
Total counters created: 3
Max count allowed: 1000
```

---

### Step 4: Records — Immutable Data Classes

```java
// Records.java
import java.util.List;

public class Records {

    // record auto-generates: constructor, accessors, equals, hashCode, toString
    record Point(double x, double y) {
        // Compact constructor — validation
        Point {
            if (Double.isNaN(x) || Double.isNaN(y))
                throw new IllegalArgumentException("Coordinates cannot be NaN");
        }

        // Custom methods allowed
        double distanceTo(Point other) {
            double dx = this.x - other.x, dy = this.y - other.y;
            return Math.sqrt(dx*dx + dy*dy);
        }

        Point translate(double dx, double dy) {
            return new Point(x + dx, y + dy);  // records are immutable
        }
    }

    record Person(String firstName, String lastName, int age) {
        // Derived accessor
        String fullName() { return firstName + " " + lastName; }

        // Static factory
        static Person of(String full, int age) {
            String[] parts = full.split(" ", 2);
            return new Person(parts[0], parts.length > 1 ? parts[1] : "", age);
        }
    }

    public static void main(String[] args) {
        Point p1 = new Point(0, 0);
        Point p2 = new Point(3, 4);

        System.out.println("p1: " + p1);
        System.out.println("p2: " + p2);
        System.out.printf("Distance: %.1f%n", p1.distanceTo(p2));
        System.out.println("p1 translated: " + p1.translate(1, 2));

        // Structural equality (not reference)
        Point p3 = new Point(3, 4);
        System.out.println("p2.equals(p3): " + p2.equals(p3));  // true

        // Person record
        Person p = Person.of("Dr. Chen", 40);
        System.out.println("\n" + p.fullName() + " age=" + p.age());

        // Records work great in lists
        List<Person> team = List.of(
            new Person("Alice", "Smith", 30),
            new Person("Bob", "Jones", 25),
            new Person("Carol", "Lee", 35)
        );
        team.stream()
            .sorted((a, b) -> Integer.compare(a.age(), b.age()))
            .forEach(person -> System.out.println("  " + person.fullName() + " " + person.age()));
    }
}
```

> 💡 **Records are perfect for DTOs, value objects, and API responses.** They're immutable by default (all fields are `final`). The compact constructor lets you add validation without rewriting the full constructor. Use records instead of Lombok's `@Data` in modern Java.

**📸 Verified Output:**
```
p1: Point[x=0.0, y=0.0]
p2: Point[x=3.0, y=4.0]
Distance: 5.0
p1 translated: Point[x=1.0, y=2.0]
p2.equals(p3): true

Dr. Chen age=40
  Bob Jones 25
  Alice Smith 30
  Carol Lee 35
```

---

### Step 5: equals, hashCode & toString

```java
// EqualsHashCode.java
import java.util.*;

public class EqualsHashCode {

    static class Product {
        private final String sku;
        private final String name;
        private double price;

        Product(String sku, String name, double price) {
            this.sku = Objects.requireNonNull(sku, "SKU required");
            this.name = Objects.requireNonNull(name, "Name required");
            this.price = price;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof Product p)) return false;
            return Objects.equals(sku, p.sku);  // SKU is identity
        }

        @Override
        public int hashCode() {
            return Objects.hash(sku);
        }

        @Override
        public String toString() {
            return String.format("Product{sku='%s', name='%s', price=%.2f}", sku, name, price);
        }
    }

    public static void main(String[] args) {
        Product p1 = new Product("SKU-001", "Widget A", 9.99);
        Product p2 = new Product("SKU-001", "Widget A", 9.99);  // same SKU
        Product p3 = new Product("SKU-002", "Widget B", 14.99);

        System.out.println("p1 == p2 (ref): " + (p1 == p2));        // false
        System.out.println("p1.equals(p2): " + p1.equals(p2));      // true (same SKU)
        System.out.println("p1.equals(p3): " + p1.equals(p3));      // false

        // HashMap requires consistent equals + hashCode
        Map<Product, Integer> inventory = new HashMap<>();
        inventory.put(p1, 100);
        inventory.put(p2, 200);  // same SKU → overwrites
        inventory.put(p3, 50);

        System.out.println("\nInventory size: " + inventory.size());  // 2, not 3
        System.out.println("SKU-001 stock: " + inventory.get(p1));   // 200

        // HashSet deduplication
        Set<Product> catalog = new HashSet<>(Arrays.asList(p1, p2, p3));
        System.out.println("Unique products: " + catalog.size());    // 2
    }
}
```

> 💡 **The `equals`/`hashCode` contract:** if `a.equals(b)` then `a.hashCode() == b.hashCode()`. Breaking this contract silently breaks `HashMap`, `HashSet`, and `HashTable`. Use `Objects.equals()` (null-safe) and `Objects.hash()` to implement correctly.

**📸 Verified Output:**
```
p1 == p2 (ref): false
p1.equals(p2): true
p1.equals(p3): false

Inventory size: 2
SKU-001 stock: 200
Unique products: 2
```

---

### Step 6: Inner Classes & Nested Types

```java
// InnerClasses.java
public class InnerClasses {

    // Static nested class — no reference to outer
    static class Node<T> {
        T value;
        Node<T> next;
        Node(T value) { this.value = value; }
    }

    // Static nested builder
    static class Config {
        final String host;
        final int port;
        final boolean ssl;
        final int timeout;

        private Config(Builder b) {
            this.host = b.host; this.port = b.port;
            this.ssl = b.ssl; this.timeout = b.timeout;
        }

        static class Builder {
            String host = "localhost";
            int port = 8080;
            boolean ssl = false;
            int timeout = 30;

            Builder host(String h) { host = h; return this; }
            Builder port(int p) { port = p; return this; }
            Builder ssl(boolean s) { ssl = s; return this; }
            Builder timeout(int t) { timeout = t; return this; }
            Config build() { return new Config(this); }
        }

        @Override
        public String toString() {
            return String.format("Config{%s:%d ssl=%b timeout=%ds}", host, port, ssl, timeout);
        }
    }

    public static void main(String[] args) {
        // Builder pattern
        Config config = new Config.Builder()
            .host("api.innozverse.com")
            .port(443)
            .ssl(true)
            .timeout(60)
            .build();

        System.out.println(config);

        // Linked list with nested Node
        Node<Integer> head = new Node<>(1);
        head.next = new Node<>(2);
        head.next.next = new Node<>(3);

        System.out.print("List: ");
        for (Node<Integer> curr = head; curr != null; curr = curr.next)
            System.out.print(curr.value + " ");
        System.out.println();
    }
}
```

> 💡 **The Builder pattern** solves the "telescoping constructor" problem — instead of 5 constructors with different parameter combinations, you chain method calls and call `build()`. It also makes construction self-documenting: `.host("...").port(443).ssl(true)` reads like configuration, not a mystery list of arguments.

**📸 Verified Output:**
```
Config{api.innozverse.com:443 ssl=true timeout=60s}
List: 1 2 3
```

---

### Step 7: Object Lifecycle & Garbage Collection

```java
// ObjectLifecycle.java
import java.util.ArrayList;
import java.util.List;

public class ObjectLifecycle {

    static class Resource {
        private final String name;
        private boolean open;
        private static int activeCount = 0;

        Resource(String name) {
            this.name = name;
            this.open = true;
            activeCount++;
            System.out.println("  Opened: " + name + " (active=" + activeCount + ")");
        }

        void use() {
            if (!open) throw new IllegalStateException(name + " is closed");
            System.out.println("  Using: " + name);
        }

        void close() {
            if (open) {
                open = false;
                activeCount--;
                System.out.println("  Closed: " + name + " (active=" + activeCount + ")");
            }
        }

        static int getActiveCount() { return activeCount; }
    }

    public static void main(String[] args) {
        System.out.println("=== Resource lifecycle ===");
        Resource r1 = new Resource("DB Connection");
        Resource r2 = new Resource("File Handle");

        r1.use();
        r2.use();

        r1.close();
        System.out.println("Active after closing r1: " + Resource.getActiveCount());

        // Try-with-resources (AutoCloseable — shown conceptually)
        System.out.println("\n=== Memory reference types ===");
        List<int[]> list = new ArrayList<>();

        // Strong reference — GC won't collect
        int[] data = new int[1000];
        list.add(data);
        System.out.println("Objects: " + list.size());

        // Nulling reference allows GC
        list.clear();
        data = null;
        System.out.println("After clear+null, GC eligible");

        // Suggest GC (not guaranteed)
        System.gc();
        System.out.println("Memory: " + Runtime.getRuntime().freeMemory() / 1024 + " KB free");
    }
}
```

> 💡 **Java's Garbage Collector** reclaims memory automatically when objects have no more references. You can't force GC (`System.gc()` is a suggestion). For resource cleanup (files, DB connections, sockets), use `try-with-resources` with `AutoCloseable` — the JVM guarantees `close()` is called.

**📸 Verified Output:**
```
=== Resource lifecycle ===
  Opened: DB Connection (active=1)
  Opened: File Handle (active=2)
  Using: DB Connection
  Using: File Handle
  Closed: DB Connection (active=1)
Active after closing r1: 1

=== Memory reference types ===
Objects: 1
After clear+null, GC eligible
Memory: 25432 KB free
```

---

### Step 8: Complete Class — Shopping Cart

```java
// ShoppingCart.java
import java.util.*;

public class ShoppingCart {

    record Product(String name, double price) {}

    static class CartItem {
        final Product product;
        int quantity;

        CartItem(Product product, int quantity) {
            this.product = product;
            this.quantity = quantity;
        }

        double subtotal() { return product.price() * quantity; }

        @Override
        public String toString() {
            return String.format("  %-20s x%d  $%6.2f", product.name(), quantity, subtotal());
        }
    }

    private final String customer;
    private final List<CartItem> items = new ArrayList<>();
    private String coupon = null;

    ShoppingCart(String customer) { this.customer = customer; }

    void add(Product p, int qty) {
        // Consolidate duplicate products
        items.stream()
            .filter(i -> i.product.equals(p))
            .findFirst()
            .ifPresentOrElse(
                i -> i.quantity += qty,
                () -> items.add(new CartItem(p, qty))
            );
    }

    void applyCoupon(String code) { this.coupon = code; }

    double subtotal() { return items.stream().mapToDouble(CartItem::subtotal).sum(); }

    double discount() {
        return switch (coupon != null ? coupon : "") {
            case "SAVE10" -> subtotal() * 0.10;
            case "SAVE20" -> subtotal() * 0.20;
            default -> 0;
        };
    }

    double total() {
        double sub = subtotal();
        return sub - discount() + (sub > 100 ? 0 : 9.99);
    }

    void printReceipt() {
        System.out.println("═══ Order for " + customer + " ═══");
        items.forEach(System.out::println);
        System.out.println("─────────────────────────────────");
        System.out.printf("  Subtotal:%26s$%6.2f%n", "", subtotal());
        if (coupon != null) System.out.printf("  Discount (%s):%20s-$%5.2f%n", coupon, "", discount());
        double shipping = subtotal() > 100 ? 0 : 9.99;
        System.out.printf("  Shipping:%27s$%6.2f%n", "", shipping);
        System.out.println("═════════════════════════════════");
        System.out.printf("  TOTAL:%29s$%6.2f%n", "", total());
    }

    public static void main(String[] args) {
        ShoppingCart cart = new ShoppingCart("Dr. Chen");
        cart.add(new Product("Surface Pro 12\"", 864.00), 1);
        cart.add(new Product("Surface Pen", 49.99), 2);
        cart.add(new Product("USB-C Hub", 29.99), 1);
        cart.add(new Product("Surface Pen", 49.99), 1);  // consolidates
        cart.applyCoupon("SAVE10");
        cart.printReceipt();
    }
}
```

> 💡 **`ifPresentOrElse`** on Optional handles both "found" and "not found" in one readable expression. Combining records, streams, and switch expressions shows how modern Java is concise and expressive without external libraries.

**📸 Verified Output:**
```
═══ Order for Dr. Chen ═══
  Surface Pro 12"       x1   $864.00
  Surface Pen           x3   $149.97
  USB-C Hub             x1   $ 29.99
─────────────────────────────────
  Subtotal:                  $1043.96
  Discount (SAVE10):         -$104.40
  Shipping:                  $  0.00
═════════════════════════════════
  TOTAL:                     $ 939.56
```

---

## Verification

```bash
javac ShoppingCart.java && java ShoppingCart
```

## Summary

You've built complete Java classes with encapsulation, constructor chaining, static members, records, `equals`/`hashCode`, builders, and the shopping cart capstone. These patterns are the daily vocabulary of Java development.

## Further Reading
- [Oracle Tutorial: Classes and Objects](https://docs.oracle.com/javase/tutorial/java/javaOO/index.html)
- [JEP 395: Records](https://openjdk.org/jeps/395)
- [Effective Java — Item 17: Minimize mutability](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
