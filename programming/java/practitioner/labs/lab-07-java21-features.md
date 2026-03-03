# Lab 7: Java 21 Features — Records, Sealed Classes & Pattern Matching

## Objective
Master Java 21's three biggest language features: **records** (immutable data carriers with compact constructors), **sealed interfaces** (restricted class hierarchies), and **pattern matching switch** (exhaustive, type-safe dispatch).

## Background
Java 21 (LTS) finalised several major language improvements. Records eliminate boilerplate for data classes — the compiler auto-generates `equals`, `hashCode`, `toString`, and accessors. Sealed interfaces let you define closed hierarchies where the compiler knows every subtype, enabling exhaustive pattern matching. Together they bring algebraic data types to Java.

## Time
30 minutes

## Prerequisites
- Lab 06 (File I/O)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Records, sealed interface, pattern switch, guarded patterns, text blocks, `instanceof`, Capstone

```bash
cat > /tmp/Lab07.java << 'JAVAEOF'
import java.util.*;
import java.util.stream.*;

public class Lab07 {
    sealed interface Shape permits Shape.Circle, Shape.Rectangle, Shape.Triangle {
        double area();
        record Circle(double radius) implements Shape {
            public double area() { return Math.PI * radius * radius; }
        }
        record Rectangle(double width, double height) implements Shape {
            public double area() { return width * height; }
        }
        record Triangle(double base, double height) implements Shape {
            public double area() { return 0.5 * base * height; }
        }
    }

    static String describeShape(Shape s) {
        return switch (s) {
            case Shape.Circle c    when c.radius() > 10 -> "Large circle r=" + c.radius();
            case Shape.Circle c                         -> "Circle r=" + c.radius();
            case Shape.Rectangle r when r.width() == r.height() -> "Square side=" + r.width();
            case Shape.Rectangle r                      -> "Rect " + r.width() + "x" + r.height();
            case Shape.Triangle t                       -> "Triangle b=" + t.base() + " h=" + t.height();
        };
    }

    sealed interface OrderResult permits OrderResult.Success, OrderResult.Failure {
        record Success(int orderId, double total, String confirmation) implements OrderResult {}
        record Failure(String code, String reason) implements OrderResult {}
    }

    static OrderResult processOrder(String product, int qty, double price) {
        if (qty <= 0) return new OrderResult.Failure("INVALID_QTY", "qty must be > 0");
        if (price <= 0) return new OrderResult.Failure("INVALID_PRICE", "price must be > 0");
        int id = 1001 + product.hashCode() % 100;
        return new OrderResult.Success(Math.abs(id), qty * price, "CONF-" + Math.abs(id));
    }

    record Product(String name, double price, int stock) {
        Product {
            if (name == null || name.isBlank()) throw new IllegalArgumentException("name required");
            if (price <= 0) throw new IllegalArgumentException("price must be > 0");
            if (stock < 0) throw new IllegalArgumentException("stock must be >= 0");
        }
        boolean inStock() { return stock > 0; }
        double value() { return price * stock; }
        Product withPrice(double newPrice) { return new Product(name, newPrice, stock); }
        Product withStock(int newStock) { return new Product(name, price, newStock); }
    }

    public static void main(String[] args) {
        var p1 = new Product("Surface Pro", 864.0, 15);
        var p2 = p1.withPrice(799.99).withStock(20);
        System.out.println("p1: " + p1);
        System.out.println("p2: " + p2);
        System.out.println("Equal names: " + p1.name().equals(p2.name()));
        System.out.println("p1 value: $" + p1.value());

        List<Shape> shapes = List.of(
            new Shape.Circle(5.0), new Shape.Circle(15.0),
            new Shape.Rectangle(4.0, 4.0), new Shape.Rectangle(3.0, 7.0),
            new Shape.Triangle(6.0, 8.0));

        System.out.println("\nShapes:");
        shapes.forEach(s -> System.out.printf("  %-35s area=%.2f%n", describeShape(s), s.area()));
        System.out.printf("Total area: %.2f%n", shapes.stream().mapToDouble(Shape::area).sum());

        System.out.println("\nOrders:");
        List.of(
            processOrder("Surface Pro", 2, 864.0),
            processOrder("Surface Pen", -1, 49.99),
            processOrder("Office 365", 3, 99.99)
        ).forEach(result -> {
            switch (result) {
                case OrderResult.Success s ->
                    System.out.printf("  \u2713 #%d total=$%.2f conf=%s%n", s.orderId(), s.total(), s.confirmation());
                case OrderResult.Failure f ->
                    System.out.printf("  \u2717 [%s] %s%n", f.code(), f.reason());
            }
        });

        Object obj = new Product("Surface Book", 1299.0, 5);
        if (obj instanceof Product p && p.inStock()) {
            System.out.println("\nPattern match: " + p.name() + " in stock, value=$" + p.value());
        }

        String json = """
                {
                  "name": "%s",
                  "price": %.2f,
                  "inStock": %b
                }
                """.formatted(p1.name(), p1.price(), p1.inStock());
        System.out.println("\nText block JSON:\n" + json);
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab07.java:/tmp/Lab07.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab07.java -d /tmp && java -cp /tmp Lab07"
```

> 💡 **Sealed interface + pattern switch = exhaustive dispatch.** When all `case` branches are listed for a sealed type, the compiler proves the switch is exhaustive — no default needed, and no runtime `MatchException`. Add a new permitted subtype and the compiler instantly flags every switch that's incomplete. This is the Java equivalent of Rust's `match` or Haskell's ADTs.

**📸 Verified Output:**
```
p1: Product[name=Surface Pro, price=864.0, stock=15]
p2: Product[name=Surface Pro, price=799.99, stock=20]
Equal names: true
p1 value: $12960.0

Shapes:
  Circle r=5.0                        area=78.54
  Large circle r=15.0                 area=706.86
  Square side=4.0                     area=16.00
  Rect 3.0x7.0                        area=21.00
  Triangle b=6.0 h=8.0                area=24.00
Total area: 846.40

Orders:
  ✓ #... total=$1728.00 conf=CONF-...
  ✗ [INVALID_QTY] qty must be > 0
  ✓ #... total=$299.97 conf=CONF-...

Pattern match: Surface Book in stock, value=$6495.0
```

---

## Summary

| Feature | Java Version | Key benefit |
|---------|-------------|-------------|
| Records | 16 (final) | Auto `equals/hashCode/toString`, immutable |
| Compact constructor | 16 | Validation in records without boilerplate |
| Sealed classes/interfaces | 17 (final) | Closed hierarchies, exhaustive switching |
| Pattern matching `instanceof` | 16 (final) | Combine type check + cast in one step |
| Pattern matching switch | 21 (final) | Exhaustive type dispatch with guards |
| Text blocks | 15 (final) | Multi-line string literals |

## Further Reading
- [JEP 395: Records](https://openjdk.org/jeps/395)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441)
