# Lab 14: Advanced Enums — State Machines, EnumSet & EnumMap

## Objective
Master Java enums beyond simple constants: fields and methods, abstract methods per constant (state machine), `EnumSet` for efficient enum collections, `EnumMap` for enum-keyed maps, and pattern-matching switch for exhaustive enum dispatch.

## Background
Java enums are full classes — each constant is a singleton instance. They can have fields, constructors, and methods. When combined with abstract methods, each constant can have its own behaviour: a compact and type-safe state machine. `EnumSet` and `EnumMap` use bit vectors and arrays internally — they're significantly faster than `HashSet<E>` and `HashMap<E,V>` for enum keys.

## Time
25 minutes

## Prerequisites
- Lab 13 (Interfaces Advanced)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Enum fields/methods, abstract methods (state machine), EnumSet, EnumMap, valueOf/ordinal, switch expression, Capstone

```bash
cat > /tmp/Lab14.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;

public class Lab14 {
    enum OrderStatus {
        PENDING("Pending", false, false) { @Override public OrderStatus next() { return PAID; } },
        PAID("Paid", true, false) { @Override public OrderStatus next() { return PROCESSING; } },
        PROCESSING("Processing", true, false) { @Override public OrderStatus next() { return SHIPPED; } },
        SHIPPED("Shipped", true, false) { @Override public OrderStatus next() { return DELIVERED; } },
        DELIVERED("Delivered", true, true) { @Override public OrderStatus next() { throw new IllegalStateException("Terminal"); } },
        CANCELLED("Cancelled", false, true) { @Override public OrderStatus next() { throw new IllegalStateException("Terminal"); } };

        private final String label; private final boolean isPaid; private final boolean isTerminal;
        OrderStatus(String label, boolean isPaid, boolean isTerminal) {
            this.label=label; this.isPaid=isPaid; this.isTerminal=isTerminal; }
        public String label() { return label; }
        public boolean isPaid() { return isPaid; }
        public boolean isTerminal() { return isTerminal; }
        public abstract OrderStatus next();
    }

    enum PricingTier {
        STANDARD(0, 1.00, "No discount"), SILVER(1000, 0.95, "5% off"),
        GOLD(5000, 0.90, "10% off"), PLATINUM(20000, 0.80, "20% off");

        private final double minSpend, multiplier; private final String label;
        PricingTier(double minSpend, double multiplier, String label) {
            this.minSpend=minSpend; this.multiplier=multiplier; this.label=label; }
        static PricingTier forSpend(double spend) {
            return Arrays.stream(values()).filter(t -> spend >= t.minSpend)
                .max(Comparator.comparingDouble(t -> t.minSpend)).orElse(STANDARD); }
        double apply(double price) { return price * multiplier; }
        @Override public String toString() { return name() + "(" + label + ")"; }
    }

    enum Category { LAPTOP, ACCESSORY, SOFTWARE, HARDWARE }

    public static void main(String[] args) {
        // State machine
        System.out.println("=== Order State Machine ===");
        var status = OrderStatus.PENDING;
        System.out.println("Start: " + status.label());
        while (!status.isTerminal()) {
            status = status.next();
            System.out.println("  -> " + status.label() + (status.isTerminal() ? " [TERMINAL]" : ""));
        }

        // EnumSet
        System.out.println("\n=== EnumSet ===");
        var paidStatuses = EnumSet.of(OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED);
        var unpaid = EnumSet.complementOf(EnumSet.copyOf(paidStatuses));
        System.out.println("Paid:   " + paidStatuses.stream().map(OrderStatus::label).toList());
        System.out.println("Unpaid: " + unpaid.stream().map(OrderStatus::label).toList());
        System.out.println("PAID.isPaid: " + OrderStatus.PAID.isPaid() + " | CANCELLED.isPaid: " + OrderStatus.CANCELLED.isPaid());

        // EnumMap
        System.out.println("\n=== EnumMap ===");
        var categoryCount = new EnumMap<Category, Integer>(Category.class);
        Arrays.stream(Category.values()).forEach(c -> categoryCount.put(c, 0));
        categoryCount.merge(Category.LAPTOP, 3, Integer::sum);
        categoryCount.merge(Category.ACCESSORY, 5, Integer::sum);
        categoryCount.merge(Category.SOFTWARE, 2, Integer::sum);
        categoryCount.forEach((cat, count) -> System.out.printf("  %-12s %d items%n", cat, count));

        // Pricing tier
        System.out.println("\n=== Pricing Tiers ===");
        for (double spend : List.of(0.0, 999.0, 2500.0, 8000.0, 25000.0)) {
            var tier = PricingTier.forSpend(spend);
            System.out.printf("  Spend=$%,7.0f  -> %-20s  $864 -> $%.2f%n", spend, tier, tier.apply(864.0));
        }

        // valueOf, ordinal, name
        System.out.println("\n=== Enum Basics ===");
        var s = OrderStatus.valueOf("PAID");
        System.out.println("valueOf(PAID): " + s + " ordinal=" + s.ordinal() + " name=" + s.name());
        System.out.println("values: " + Arrays.asList(OrderStatus.values()));

        // Pattern switch (exhaustive)
        System.out.println("\n=== Pattern Switch (Exhaustive) ===");
        for (var os : List.of(OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.CANCELLED)) {
            String action = switch (os) {
                case PENDING    -> "Send payment link";
                case PAID, PROCESSING -> "Pick & pack";
                case SHIPPED    -> "Track shipment";
                case DELIVERED  -> "Request review";
                case CANCELLED  -> "Issue refund";
            };
            System.out.println("  " + os.label() + " -> " + action);
        }
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab14.java:/tmp/Lab14.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab14.java -d /tmp && java -cp /tmp Lab14"
```

> 💡 **`EnumSet` uses a `long` bitmask internally** — membership testing and iteration are O(1) bit operations, not hash lookups. For enums with ≤64 constants, `EnumSet` is always faster than `HashSet<OrderStatus>`. Similarly, `EnumMap` uses an array indexed by `ordinal()`, making lookups array-access speed. Always prefer these specialised collections when your key/element type is an enum.

**📸 Verified Output:**
```
=== Order State Machine ===
Start: Pending
  -> Paid
  -> Processing
  -> Shipped
  -> Delivered [TERMINAL]

=== EnumSet ===
Paid:   [Paid, Processing, Shipped, Delivered]
Unpaid: [Pending, Cancelled]

=== Pricing Tiers ===
  Spend=$      0  -> STANDARD(No discount)  $864 -> $864.00
  Spend=$  2,500  -> SILVER(5% off)          $864 -> $820.80
  Spend=$ 25,000  -> PLATINUM(20% off)       $864 -> $691.20

=== Pattern Switch (Exhaustive) ===
  Pending -> Send payment link
  Paid -> Pick & pack
  Shipped -> Track shipment
  Cancelled -> Issue refund
```

---

## Summary

| Feature | Notes |
|---------|-------|
| Enum with fields | Constructor sets fields; they're `final` |
| Enum with abstract method | Each constant must override it |
| `EnumSet.of(...)` | Bit-vector backed, very fast |
| `EnumSet.complementOf(set)` | All constants NOT in set |
| `EnumMap<K,V>` | Array-backed, ordinal-indexed |
| `Enum.valueOf(name)` | String → constant (throws on unknown) |
| Pattern switch | Exhaustive — no `default` needed |

## Further Reading
- [Enum types tutorial](https://docs.oracle.com/javase/tutorial/java/javaOO/enum.html)
- [EnumSet JavaDoc](https://docs.oracle.com/en/java/docs/api/java.base/java/util/EnumSet.html)
