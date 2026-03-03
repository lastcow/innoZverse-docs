# Lab 3: Functional Interfaces, Optional & Method References

## Objective
Master Java's built-in functional interfaces (`Function`, `Predicate`, `BiFunction`, `Consumer`, `Supplier`, `UnaryOperator`), compose them into pipelines, and use `Optional` for null-safe chaining.

## Background
Functional interfaces are the backbone of Java lambdas — any interface with a single abstract method is a functional interface. The `java.util.function` package provides ~43 ready-made ones. `Optional<T>` replaces null-checks with expressive, chainable operations that make absent-value handling visible and safe.

## Time
25 minutes

## Prerequisites
- Lab 02 (Streams & Lambdas)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Step 1: Custom Functional Interfaces & Composition

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab03.java << 'EOF'
import java.util.*;
import java.util.function.*;

public class Lab03 {
    @FunctionalInterface interface PriceTransformer {
        double apply(double price, double factor);
    }
    @FunctionalInterface interface Validator<T> {
        boolean test(T t);
        default Validator<T> and(Validator<T> other) { return v -> test(v) && other.test(v); }
        default Validator<T> or(Validator<T> other) { return v -> test(v) || other.test(v); }
        default Validator<T> negate() { return v -> !test(v); }
    }

    record Product(String name, double price, int stock) {}

    static Optional<Product> findCheapest(List<Product> products, double maxPrice) {
        return products.stream().filter(p -> p.price() <= maxPrice)
            .min(Comparator.comparingDouble(Product::price));
    }

    public static void main(String[] args) {
        PriceTransformer discount = (price, pct) -> Math.round(price * (1 - pct) * 100) / 100.0;
        PriceTransformer markup  = (price, factor) -> price * factor;
        System.out.println(\"Discounted: \$\" + discount.apply(864.0, 0.15));
        System.out.println(\"Marked up:  \$\" + markup.apply(864.0, 1.20));

        Validator<Product> hasStock   = p -> p.stock() > 0;
        Validator<Product> affordable = p -> p.price() < 200;
        Validator<Product> both = hasStock.and(affordable);

        var products = List.of(
            new Product(\"Surface Pro\", 864.0, 15),
            new Product(\"Surface Pen\",  49.99, 80),
            new Product(\"USB-C Hub\",    29.99,  0),
            new Product(\"Office 365\",   99.99, 999)
        );
        products.stream().filter(both::test)
            .forEach(p -> System.out.println(\"  Affordable+stock: \" + p.name()));

        // Optional chaining
        var cheap = findCheapest(products, 60.0);
        System.out.println(cheap.map(p -> p.name() + \" @ \$\" + p.price()).orElse(\"Not found\"));
        System.out.println(findCheapest(products, 10.0).orElse(null));

        cheap.ifPresent(p -> System.out.println(\"Got: \" + p.name()));
        var fallback = findCheapest(products, 10.0)
            .or(() -> Optional.of(new Product(\"Default\", 0.0, 0)));
        System.out.println(\"Fallback: \" + fallback.get().name());

        // Method references
        Function<String, String> upper = String::toUpperCase;
        Comparator<Product> byPrice = Comparator.comparingDouble(Product::price);
        products.stream().sorted(byPrice).map(Product::name).map(upper)
            .forEach(n -> System.out.print(n + \" \"));
        System.out.println();

        // Built-in interfaces
        Predicate<Integer> isEven = n -> n % 2 == 0;
        Predicate<Integer> isPos  = n -> n > 0;
        System.out.println(isEven.and(isPos).test(4) + \" \" + isEven.and(isPos).test(-2));

        BiFunction<String, Double, String> label = (name, price) -> name + \"=\$\" + price;
        System.out.println(label.apply(\"Surface Pro\", 864.0));

        UnaryOperator<Double> round2 = d -> Math.round(d * 100) / 100.0;
        System.out.println(round2.apply(864.999));

        // Function composition
        Function<Double, Double> applyTax     = p -> p * 1.08;
        Function<Double, Double> applyDiscount = p -> p * 0.90;
        Function<Double, Double> pipeline = applyDiscount.andThen(applyTax).andThen(round2);
        System.out.println(\"Pipeline \$864 → \$\" + pipeline.apply(864.0));

        // Supplier & Consumer
        Supplier<Product> defaultProduct = () -> new Product(\"Default\", 0.0, 0);
        Consumer<Product> print = p -> System.out.println(\"Product: \" + p.name() + \" @\$\" + p.price());
        Consumer<Product> logStock = p -> System.out.println(\"Stock: \" + p.stock());
        Consumer<Product> both2 = print.andThen(logStock);
        both2.accept(defaultProduct.get());
    }
}
EOF
javac /tmp/Lab03.java -d /tmp && java -cp /tmp Lab03"
```

> 💡 **`Optional.or()` vs `orElseGet()`:** `Optional.or()` returns a new `Optional<T>` (so you can keep chaining), while `orElseGet()` unwraps to a `T`. Use `or()` when you want to provide a fallback `Optional`, and `orElseGet()` when you want the actual value. Never use `get()` without `isPresent()` — it throws `NoSuchElementException`.

**📸 Verified Output:**
```
Discounted: $734.4
Marked up:  $1036.8
  Affordable+stock: Surface Pen
  Affordable+stock: Office 365
USB-C Hub @ $29.99
null
Got: USB-C Hub
Fallback: Default
USB-C HUB SURFACE PEN OFFICE 365 SURFACE PRO
true false
Surface Pro=$864.0
865.0
Pipeline $864 → $839.81
Product: Default @$0.0
Stock: 0
```

---

## Summary

| Interface | Signature | Use for |
|-----------|-----------|---------|
| `Function<T,R>` | `R apply(T t)` | Transform T → R |
| `BiFunction<T,U,R>` | `R apply(T,U)` | Two-input transform |
| `UnaryOperator<T>` | `T apply(T t)` | Transform T → T |
| `Predicate<T>` | `boolean test(T)` | Filter condition |
| `Consumer<T>` | `void accept(T)` | Side-effect action |
| `Supplier<T>` | `T get()` | Lazy value factory |
| `Comparator<T>` | `int compare(a,b)` | Ordering |

## Further Reading
- [java.util.function](https://docs.oracle.com/en/java/docs/api/java.base/java/util/function/package-summary.html)
- [Optional](https://docs.oracle.com/en/java/docs/api/java.base/java/util/Optional.html)
