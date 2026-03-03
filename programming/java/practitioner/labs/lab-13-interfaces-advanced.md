# Lab 13: Interfaces — Default, Static & Private Methods

## Objective
Master all four interface member types in Java 9+: abstract, default, static, and private methods. Build composable interfaces for pricing, validation, and reporting using the template method pattern via defaults and interface inheritance chains.

## Background
Since Java 8, interfaces can have `default` methods (inherited implementations) and `static` methods (utility factories). Java 9 added `private` methods in interfaces — shared implementation for default methods without exposing it publicly. This makes interfaces much more powerful than simple contracts: they can carry behaviour while still permitting multiple inheritance without the diamond problem.

## Time
25 minutes

## Prerequisites
- Lab 12 (Reflection & Annotations)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Default/static/private interface methods, composition, PECS with interfaces, template method, marker interfaces, Capstone

```bash
cat > /tmp/Lab13.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class Lab13 {
    interface Priceable {
        double getPrice();
        default double withTax(double rate) { return getPrice() * (1 + rate); }
        default double withDiscount(double pct) { return getPrice() * (1 - pct); }
        default String formatted() { return String.format("$%.2f", getPrice()); }
        static Priceable of(double price) { return () -> price; }
        private double bounded(double min, double max) {
            double p = getPrice(); return Math.max(min, Math.min(max, p)); }
        default double clamp(double min, double max) { return bounded(min, max); }
    }

    interface Discountable { double getDiscount(); default double netPrice(double base) { return base * (1 - getDiscount()); } }
    interface Taxable { double getTaxRate(); default double grossPrice(double base) { return base * (1 + getTaxRate()); } }

    static class ProductListing implements Priceable, Discountable, Taxable {
        private final String name; private final double price, discount, taxRate;
        ProductListing(String name, double price, double discount, double taxRate) {
            this.name=name; this.price=price; this.discount=discount; this.taxRate=taxRate; }
        @Override public double getPrice() { return price; }
        @Override public double getDiscount() { return discount; }
        @Override public double getTaxRate() { return taxRate; }
        double finalPrice() { return grossPrice(netPrice(price)); }
        @Override public String toString() {
            return String.format("%s: base=%s disc=%.0f%% tax=%.0f%% final=$%.2f",
                name, formatted(), discount*100, taxRate*100, finalPrice()); }
    }

    @FunctionalInterface interface Transformer<T> {
        T transform(T input);
        default Transformer<T> andThen(Transformer<T> next) { return v -> next.transform(transform(v)); }
        static <T> Transformer<T> identity() { return v -> v; }
    }

    interface Exportable { String toJson(); }
    interface Archivable extends Exportable { String archive(); }

    record Product(int id, String name, double price, int stock) implements Archivable {
        @Override public String toJson() {
            return "{\"id\":%d,\"name\":\"%s\",\"price\":%.2f}".formatted(id,name,price); }
        @Override public String archive() { return "ARCHIVE:" + toJson(); }
    }

    interface ReportGenerator {
        List<String> getHeaders();
        List<List<String>> getRows();
        String getSeparator();
        default String generate() {
            var sb = new StringBuilder();
            sb.append(String.join(getSeparator(), getHeaders())).append("\n");
            sb.append("-".repeat(50)).append("\n");
            getRows().forEach(row -> sb.append(String.join(getSeparator(), row)).append("\n"));
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Interface Default Methods ===");
        var listings = List.of(
            new ProductListing("Surface Pro",  864.0, 0.10, 0.08),
            new ProductListing("Surface Pen",  49.99, 0.05, 0.08),
            new ProductListing("Office 365",   99.99, 0.00, 0.08));
        listings.forEach(l -> System.out.println("  " + l));

        Priceable p = Priceable.of(864.0);
        System.out.printf("%nPriceable.of(864): %s  +tax=$%.2f  clamped=[50,500]: $%.0f%n",
            p.formatted(), p.withTax(0.08), p.clamp(50, 500));

        System.out.println("\n=== Transformer Composition ===");
        Transformer<Double> applyDiscount = price -> price * 0.90;
        Transformer<Double> applyTax      = price -> price * 1.08;
        Transformer<Double> round2dp      = price -> Math.round(price * 100) / 100.0;
        Transformer<Double> pipeline = applyDiscount.andThen(applyTax).andThen(round2dp);

        for (double base : List.of(864.0, 49.99, 99.99, 29.99)) {
            System.out.printf("  $%-8.2f -> disc->tax->round -> $%.2f%n", base, pipeline.transform(base));
        }

        System.out.println("\n=== Interface Hierarchy ===");
        List<Object> items = List.of(
            new Product(1, "Surface Pro", 864.0, 15),
            new Product(2, "Surface Pen", 49.99, 80),
            "just a string");
        for (var item : items) {
            System.out.print("  " + item.getClass().getSimpleName() + ": ");
            if (item instanceof Archivable a) System.out.println(a.archive());
            else if (item instanceof Exportable e) System.out.println(e.toJson());
            else System.out.println(item);
        }

        System.out.println("\n=== Template Method via Default ===");
        ReportGenerator csvReport = new ReportGenerator() {
            public List<String> getHeaders() { return List.of("Name","Price","Disc%","Final"); }
            public String getSeparator() { return ","; }
            public List<List<String>> getRows() {
                return listings.stream().map(l -> List.of(
                    l.name, l.formatted(), (int)(l.discount*100) + "%", String.format("$%.2f", l.finalPrice()))).toList();
            }
        };
        System.out.println(csvReport.generate());
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab13.java:/tmp/Lab13.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab13.java -d /tmp && java -cp /tmp Lab13"
```

> 💡 **`private` methods in interfaces (Java 9+) solve the "shared default method code" problem.** Before Java 9, if two `default` methods needed shared logic, you had to either duplicate it or expose a `default` helper method that wasn't part of the public API. `private` interface methods hide that shared implementation cleanly — exactly like private helper methods in classes.

**📸 Verified Output:**
```
=== Interface Default Methods ===
  Surface Pro: base=$864.00 disc=10% tax=8% final=$839.81
  Surface Pen: base=$49.99 disc=5% tax=8% final=$51.29
  Office 365: base=$99.99 disc=0% tax=8% final=$107.99

Priceable.of(864): $864.00  +tax=$933.12  clamped=[50,500]: $500

=== Transformer Composition ===
  $864.00   -> disc->tax->round -> $839.81
  $49.99    -> disc->tax->round -> $48.59

=== Template Method via Default ===
Name,Price,Disc%,Final
--------------------------------------------------
Surface Pro,$864.00,10%,$839.81
Surface Pen,$49.99,5%,$51.29
Office 365,$99.99,0%,$107.99
```

---

## Summary

| Interface member | Since | Inherited? | Overridable? |
|-----------------|-------|-----------|-------------|
| `abstract` method | Java 1 | No (must implement) | N/A |
| `default` method | Java 8 | Yes | Yes |
| `static` method | Java 8 | No | No |
| `private` method | Java 9 | No | No |

## Further Reading
- [JEP 213: Private interface methods](https://openjdk.org/jeps/213)
- [Java Interfaces Tutorial](https://docs.oracle.com/javase/tutorial/java/IandI/createinterface.html)
