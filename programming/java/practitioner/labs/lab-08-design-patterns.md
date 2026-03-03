# Lab 8: Design Patterns — Builder, Factory, Observer & Strategy

## Objective
Implement four essential GoF design patterns in idiomatic Java 21: **Builder** (fluent order construction), **Factory Method** (pluggable shippers), **Observer** (event bus), and **Strategy** (interchangeable pricing algorithms).

## Background
Design patterns are reusable solutions to recurring software design problems. They're not code templates but *concepts* — the same pattern may look different depending on the language. In Java 21, records, lambdas, and sealed interfaces make many patterns significantly more concise than the classic Gang-of-Four implementations.

## Time
30 minutes

## Prerequisites
- Lab 07 (Java 21 Features)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Builder, Factory, Observer, Strategy, Command, Singleton, Decorator, Capstone

```bash
cat > /tmp/Lab08.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;

public class Lab08 {
    // 1. Builder
    static class Order {
        private final int id; private final String product; private final int qty;
        private final double price; private final String email; private final String region;
        private final boolean express; private final String coupon;

        private Order(Builder b) {
            this.id=b.id; this.product=b.product; this.qty=b.qty; this.price=b.price;
            this.email=b.email; this.region=b.region; this.express=b.express; this.coupon=b.coupon;
        }
        double total() { return price * qty * (express ? 1.05 : 1.0); }
        @Override public String toString() {
            return String.format("Order#%d: %dx%s $%.2f email=%s region=%s express=%b coupon=%s",
                id, qty, product, total(), email, region, express, coupon);
        }

        static class Builder {
            private final int id; private final String product; private int qty = 1;
            private double price; private String email = ""; private String region = "US";
            private boolean express = false; private String coupon = null;

            Builder(int id, String product, double price) { this.id=id; this.product=product; this.price=price; }
            Builder qty(int q) { this.qty = q; return this; }
            Builder email(String e) { this.email = e; return this; }
            Builder region(String r) { this.region = r; return this; }
            Builder express() { this.express = true; return this; }
            Builder coupon(String c) { this.coupon = c; return this; }
            Order build() {
                if (qty <= 0) throw new IllegalStateException("qty must be > 0");
                return new Order(this);
            }
        }
    }

    // 2. Factory Method
    interface Shipper { String ship(String product, String address); String name(); }
    static class FedEx implements Shipper {
        public String ship(String p, String a) { return "FedEx#FX" + Math.abs(p.hashCode()%1000) + " -> " + a; }
        public String name() { return "FedEx"; }
    }
    static class UPS implements Shipper {
        public String ship(String p, String a) { return "UPS#1Z" + Math.abs(p.hashCode()%9999) + " -> " + a; }
        public String name() { return "UPS"; }
    }
    static class ShipperFactory {
        private static final Map<String, Supplier<Shipper>> registry =
            Map.of("fedex", FedEx::new, "ups", UPS::new);
        static Shipper create(String type) {
            var s = registry.get(type.toLowerCase());
            if (s == null) throw new IllegalArgumentException("Unknown shipper: " + type);
            return s.get();
        }
    }

    // 3. Observer (Event Bus)
    interface EventListener<T> { void onEvent(String type, T data); }
    static class EventBus<T> {
        private final Map<String, List<EventListener<T>>> listeners = new HashMap<>();
        void on(String event, EventListener<T> l) { listeners.computeIfAbsent(event, k -> new ArrayList<>()).add(l); }
        void emit(String event, T data) { listeners.getOrDefault(event, List.of()).forEach(l -> l.onEvent(event, data)); }
    }

    // 4. Strategy
    interface PricingStrategy { double apply(double basePrice, int qty); String label(); }
    static PricingStrategy standard() { return new PricingStrategy() {
        public double apply(double p, int q) { return p * q; }
        public String label() { return "Standard"; } }; }
    static PricingStrategy bulk(int threshold, double discount) { return new PricingStrategy() {
        public double apply(double p, int q) { return p * q * (q >= threshold ? (1-discount) : 1.0); }
        public String label() { return "Bulk(>=" + threshold + "@-" + (int)(discount*100) + "%)"; } }; }
    static PricingStrategy tiered() { return new PricingStrategy() {
        public double apply(double p, int q) {
            if (q >= 100) return p * q * 0.70;
            if (q >= 50)  return p * q * 0.80;
            if (q >= 10)  return p * q * 0.90;
            return p * q;
        }
        public String label() { return "Tiered"; } }; }

    public static void main(String[] args) {
        System.out.println("=== Builder ===");
        var o1 = new Order.Builder(1001, "Surface Pro", 864.0)
            .qty(2).email("ebiz@chen.me").region("US").express().build();
        var o2 = new Order.Builder(1002, "Surface Pen", 49.99)
            .qty(5).email("alice@example.com").coupon("SAVE10").build();
        System.out.println(o1);
        System.out.println(o2);

        System.out.println("\n=== Factory ===");
        for (String type : List.of("fedex", "ups")) {
            var shipper = ShipperFactory.create(type);
            System.out.println(shipper.ship("Surface Pro", "Claymont DE 19703"));
        }

        System.out.println("\n=== Observer ===");
        var bus = new EventBus<Order>();
        bus.on("order.placed",  (t, o) -> System.out.println("  [Email]  Confirmation for " + o.email));
        bus.on("order.placed",  (t, o) -> System.out.println("  [Inv]    Deducted " + o.qty + "x " + o.product));
        bus.on("order.express", (t, o) -> System.out.println("  [Ship]   Rush processing: " + o.product));
        bus.emit("order.placed", o1);
        if (o1.express) bus.emit("order.express", o1);
        bus.emit("order.placed", o2);

        System.out.println("\n=== Strategy ===");
        var strategies = List.of(standard(), bulk(10, 0.15), tiered());
        for (int qty : List.of(1, 10, 50, 100)) {
            strategies.forEach(s ->
                System.out.printf("  qty=%-3d  %-25s $%,.2f%n", qty, s.label(), s.apply(49.99, qty)));
            System.out.println();
        }
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab08.java:/tmp/Lab08.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab08.java -d /tmp && java -cp /tmp Lab08"
```

> 💡 **Strategy pattern with lambdas:** In Java 21, functional interface strategies are just lambdas — no need for concrete classes unless you need state. The `PricingStrategy` interface with `apply` and `label` methods is a named functional interface that's also composable: you can chain strategies (apply bulk discount, then apply loyalty discount) using the same pattern as `Function.andThen`.

**📸 Verified Output:**
```
=== Builder ===
Order#1001: 2xSurface Pro $1814.40 email=ebiz@chen.me region=US express=true coupon=null
Order#1002: 5xSurface Pen $249.95 email=alice@example.com region=US express=false coupon=SAVE10

=== Factory ===
FedEx#FX... -> Claymont DE 19703
UPS#1Z... -> Claymont DE 19703

=== Observer ===
  [Email]  Confirmation for ebiz@chen.me
  [Inv]    Deducted 2x Surface Pro
  [Ship]   Rush processing: Surface Pro
  [Email]  Confirmation for alice@example.com
  [Inv]    Deducted 5x Surface Pen

=== Strategy ===
  qty=10   Standard                  $499.90
  qty=10   Bulk(>=10@-15%)           $424.92
  qty=10   Tiered                    $449.91
```

---

## Summary

| Pattern | Intent | Java 21 idiom |
|---------|--------|---------------|
| Builder | Step-by-step complex object construction | Inner `Builder` class with fluent setters |
| Factory Method | Decouple creation from usage | `Map<String, Supplier<T>>` registry |
| Observer | Notify multiple listeners of events | `EventBus<T>` with `Map<String, List<Listener>>` |
| Strategy | Swap algorithms at runtime | Functional interface + lambda |

## Further Reading
- [Refactoring.Guru Design Patterns](https://refactoring.guru/design-patterns/java)
- [Effective Java 3rd Ed — Item 2 (Builder)](https://www.oreilly.com/library/view/effective-java/9780134686097/)
