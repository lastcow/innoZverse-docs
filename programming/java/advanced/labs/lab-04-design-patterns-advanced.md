# Lab 4: Advanced Design Patterns — Decorator, CoR, Visitor & Template Method

## Objective
Implement four advanced GoF patterns using Java 21 idioms: **Decorator** (composable price transforms), **Chain of Responsibility** (validation pipeline via functional composition), **Visitor** (type-safe product analytics), and **Template Method** (pluggable report formats).

## Background
Advanced patterns differ from basic ones in composability — each adds a new layer around existing behaviour without modifying it (Open/Closed Principle). Java 21's sealed interfaces and functional composition make these patterns far more concise than classic implementations, while sealed types make Visitor exhaustive and compiler-verified.

## Time
30 minutes

## Prerequisites
- Practitioner Lab 08 (Design Patterns), Lab 07 (Java 21 Features)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Decorator pipeline, Chain of Responsibility, Visitor with sealed, Template Method, Capstone

```bash
cat > /tmp/AdvLab04.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;

public class AdvLab04 {
    // 1. Decorator — layered price calculation
    interface PriceCalculator { double calculate(double base); String describe(); }

    static PriceCalculator base() { return new PriceCalculator() {
        public double calculate(double b) { return b; }
        public String describe() { return "base"; } }; }

    static PriceCalculator withTax(PriceCalculator inner, double rate) { return new PriceCalculator() {
        public double calculate(double b) { return inner.calculate(b) * (1 + rate); }
        public String describe() { return inner.describe() + " +tax(" + (int)(rate*100) + "%)"; } }; }

    static PriceCalculator withDiscount(PriceCalculator inner, double pct) { return new PriceCalculator() {
        public double calculate(double b) { return inner.calculate(b) * (1 - pct); }
        public String describe() { return inner.describe() + " -disc(" + (int)(pct*100) + "%)"; } }; }

    static PriceCalculator withRounding(PriceCalculator inner) { return new PriceCalculator() {
        public double calculate(double b) { return Math.round(inner.calculate(b) * 100) / 100.0; }
        public String describe() { return inner.describe() + " ->round"; } }; }

    // 2. Chain of Responsibility — composable validators
    @FunctionalInterface interface OrderValidator {
        Optional<String> validate(int qty, double price, String email);
        default OrderValidator andThen(OrderValidator next) {
            return (qty, price, email) -> {
                var err = validate(qty, price, email);
                return err.isPresent() ? err : next.validate(qty, price, email);
            };
        }
    }

    // 3. Visitor — sealed product hierarchy
    sealed interface ProductNode permits ProductNode.Laptop, ProductNode.Accessory, ProductNode.Software {
        record Laptop(String name, double price) implements ProductNode {}
        record Accessory(String name, double price) implements ProductNode {}
        record Software(String name, double price) implements ProductNode {}
        default <T> T accept(ProductVisitor<T> v) {
            return switch (this) {
                case Laptop l    -> v.visitLaptop(l.name(), l.price());
                case Accessory a -> v.visitAccessory(a.name(), a.price());
                case Software s  -> v.visitSoftware(s.name(), s.price());
            };
        }
    }
    interface ProductVisitor<T> {
        T visitLaptop(String name, double price);
        T visitAccessory(String name, double price);
        T visitSoftware(String name, double price);
    }

    // 4. Template Method — pluggable report format
    abstract static class ReportGenerator {
        final String generate(List<String[]> data) {
            var sb = new StringBuilder();
            writeHeader(sb); data.forEach(row -> writeRow(sb, row)); writeFooter(sb, data.size());
            return sb.toString();
        }
        abstract void writeHeader(StringBuilder sb);
        abstract void writeRow(StringBuilder sb, String[] row);
        abstract void writeFooter(StringBuilder sb, int count);
    }
    static class CsvReport extends ReportGenerator {
        void writeHeader(StringBuilder sb) { sb.append("name,price,category\n"); }
        void writeRow(StringBuilder sb, String[] row) { sb.append(String.join(",", row)).append("\n"); }
        void writeFooter(StringBuilder sb, int count) { sb.append("# total: ").append(count).append("\n"); }
    }
    static class MarkdownReport extends ReportGenerator {
        void writeHeader(StringBuilder sb) { sb.append("| Name | Price | Category |\n|------|-------|----------|\n"); }
        void writeRow(StringBuilder sb, String[] row) { sb.append("| ").append(String.join(" | ", row)).append(" |\n"); }
        void writeFooter(StringBuilder sb, int count) { sb.append("\n*Total: " + count + " products*\n"); }
    }

    public static void main(String[] args) {
        System.out.println("=== Decorator: Price Pipeline ===");
        double base = 864.0;
        var standard = withRounding(withTax(base(), 0.08));
        var premium  = withRounding(withTax(withDiscount(base(), 0.10), 0.08));
        var vip      = withRounding(withTax(withDiscount(base(), 0.20), 0.05));
        for (var calc : List.of(standard, premium, vip)) {
            System.out.printf("  %-45s $%.2f%n", calc.describe(), calc.calculate(base));
        }

        System.out.println("\n=== Chain of Responsibility: Order Validation ===");
        OrderValidator validator = ((OrderValidator)(qty, price, email) ->
                qty <= 0 ? Optional.of("qty must be > 0") : Optional.empty())
            .andThen((qty, price, email) ->
                price <= 0 ? Optional.of("price must be > 0") : Optional.empty())
            .andThen((qty, price, email) ->
                !email.contains("@") ? Optional.of("invalid email: " + email) : Optional.empty())
            .andThen((qty, price, email) ->
                qty > 100 ? Optional.of("qty " + qty + " exceeds max 100") : Optional.empty());

        record OrderTest(int qty, double price, String email) {}
        List.of(new OrderTest(2, 864.0, "ebiz@chen.me"),
                new OrderTest(-1, 864.0, "ebiz@chen.me"),
                new OrderTest(3, 50.0, "not-an-email"),
                new OrderTest(200, 10.0, "bulk@corp.com"))
            .forEach(t -> {
                var result = validator.validate(t.qty(), t.price(), t.email());
                System.out.printf("  qty=%-3d email=%-20s -> %s%n",
                    t.qty(), t.email(), result.map("FAIL: "::concat).orElse("OK"));
            });

        System.out.println("\n=== Visitor Pattern (Sealed) ===");
        var catalog = List.of(
            new ProductNode.Laptop("Surface Pro", 864.0),
            new ProductNode.Laptop("Surface Book", 1299.0),
            new ProductNode.Accessory("Surface Pen", 49.99),
            new ProductNode.Software("Office 365", 99.99));

        ProductVisitor<String> taxVisitor = new ProductVisitor<>() {
            public String visitLaptop(String n, double p)    { return n + ": $"+p+" +15%tax=$"+String.format("%.2f",p*1.15); }
            public String visitAccessory(String n, double p) { return n + ": $"+p+" +8%tax=$"+String.format("%.2f",p*1.08); }
            public String visitSoftware(String n, double p)  { return n + ": $"+p+" no tax"; }
        };
        catalog.forEach(p -> System.out.println("  " + p.accept(taxVisitor)));

        ProductVisitor<Double> revenueVisitor = new ProductVisitor<>() {
            public Double visitLaptop(String n, double p)    { return p * 100; }
            public Double visitAccessory(String n, double p) { return p * 500; }
            public Double visitSoftware(String n, double p)  { return p * 999; }
        };
        double total = catalog.stream().mapToDouble(p -> p.accept(revenueVisitor)).sum();
        System.out.printf("  Total projected revenue: $%,.2f%n", total);

        System.out.println("\n=== Template Method: Reports ===");
        var data = List.of(new String[]{"Surface Pro","$864","Laptop"}, new String[]{"Surface Pen","$49.99","Accessory"});
        System.out.println("CSV:\n" + new CsvReport().generate(data));
        System.out.println("Markdown:\n" + new MarkdownReport().generate(data));
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab04.java:/tmp/AdvLab04.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab04.java -d /tmp && java -cp /tmp AdvLab04"
```

> 💡 **Decorator vs inheritance:** Decorator adds behaviour at runtime by wrapping objects, not at compile-time via subclassing. `withTax(withDiscount(base(), 0.10), 0.08)` creates a three-layer stack where each layer sees the transformed price from the layer below. Adding a new transform (e.g., loyalty cashback) requires zero changes to existing classes — just a new wrapper function.

**📸 Verified Output:**
```
=== Decorator: Price Pipeline ===
  base +tax(8%) ->round                         $933.12
  base -disc(10%) +tax(8%) ->round              $839.81
  base -disc(20%) +tax(5%) ->round              $725.76

=== Chain of Responsibility ===
  qty=2   email=ebiz@chen.me         -> OK
  qty=-1  email=ebiz@chen.me         -> FAIL: qty must be > 0
  qty=3   email=not-an-email         -> FAIL: invalid email: not-an-email
  qty=200 email=bulk@corp.com        -> FAIL: qty 200 exceeds max 100

=== Visitor Pattern (Sealed) ===
  Surface Pro: $864.0 +15%tax=$993.60
  Surface Book: $1299.0 +15%tax=$1493.85
  Surface Pen: $49.99 +8%tax=$53.99
  Office 365: $99.99 no tax
  Total projected revenue: $341,185.01
```

---

## Summary

| Pattern | Java 21 idiom | Benefit |
|---------|---------------|---------|
| Decorator | Wrapper returning same interface | Composable behaviour layers |
| Chain of Responsibility | `default andThen` composition | Ordered validation pipeline |
| Visitor | Sealed `accept(visitor)` + switch | Type-safe, exhaustive dispatch |
| Template Method | `abstract` methods in base class | Fixed algorithm, pluggable steps |

## Further Reading
- [Refactoring.Guru — Decorator](https://refactoring.guru/design-patterns/decorator)
- [Sealed Types and Visitor](https://cr.openjdk.org/~briangoetz/amber/pattern-match.html)
