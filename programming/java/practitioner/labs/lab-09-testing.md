# Lab 9: Testing — JUnit-style with Built-in Assertions

## Objective
Build a comprehensive test suite for `ProductService` using Java's assertion mechanisms: grouped tests, parametric data-driven testing, edge case coverage, approximate numeric comparisons, and expected-exception testing.

## Background
JUnit 5 is the industry standard for Java testing, but its core patterns (grouping, parametrize, assertions, lifecycle) can be understood by building a minimal equivalent. This lab exercises the same test thinking you'll use with JUnit 5 — the patterns transfer directly. Understanding how tests work at the framework level makes you a better test author.

## Time
25 minutes

## Prerequisites
- Lab 08 (Design Patterns)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: assertEquals, assertTrue, assertThrows, parametrize, edge cases, mocking, coverage, Capstone

```bash
cat > /tmp/Lab09.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class Lab09 {
    record Product(int id, String name, double price, int stock) {
        boolean inStock() { return stock > 0; }
        double value() { return price * stock; }
        Product withPrice(double p) { return new Product(id, name, p, stock); }
        Product withStock(int s) { return new Product(id, name, price, s); }
    }

    static class ProductService {
        private final Map<Integer, Product> catalog = new LinkedHashMap<>();
        void add(Product p) { catalog.put(p.id(), p); }
        Optional<Product> findById(int id) { return Optional.ofNullable(catalog.get(id)); }
        List<Product> inStock() { return catalog.values().stream().filter(Product::inStock).toList(); }
        double totalValue() { return catalog.values().stream().mapToDouble(Product::value).sum(); }
        Optional<Product> cheapest() { return catalog.values().stream().min(Comparator.comparingDouble(Product::price)); }
        int size() { return catalog.size(); }
    }

    static int passed = 0, failed = 0;
    static void test(String name, Runnable fn) {
        try { fn.run(); System.out.println("  PASS: " + name); passed++; }
        catch (AssertionError e) { System.out.println("  FAIL: " + name + " -> " + e.getMessage()); failed++; }
        catch (Exception e) { System.out.println("  ERROR: " + name + " -> " + e.getMessage()); failed++; }
    }
    static void assertEquals(Object expected, Object actual, String msg) {
        if (!Objects.equals(expected, actual))
            throw new AssertionError(msg + ": expected=<" + expected + "> actual=<" + actual + ">");
    }
    static void assertTrue(boolean cond, String msg) { if (!cond) throw new AssertionError(msg); }
    static void assertFalse(boolean cond, String msg) { if (cond) throw new AssertionError(msg); }
    static void assertApprox(double expected, double actual, double tol, String msg) {
        if (Math.abs(expected - actual) > tol)
            throw new AssertionError(msg + ": expected~" + expected + " actual=" + actual);
    }
    static <E extends Exception> void assertThrows(Class<E> type, Runnable fn, String msg) {
        try { fn.run(); throw new AssertionError(msg + ": expected " + type.getSimpleName() + " not thrown"); }
        catch (Exception e) { if (!type.isInstance(e)) throw new AssertionError(msg + ": wrong exception: " + e.getClass().getSimpleName()); }
    }

    static ProductService makeService() {
        var svc = new ProductService();
        svc.add(new Product(1, "Surface Pro", 864.0, 15));
        svc.add(new Product(2, "Surface Pen", 49.99, 80));
        svc.add(new Product(3, "Office 365",  99.99, 999));
        svc.add(new Product(4, "USB-C Hub",   29.99, 0));
        return svc;
    }

    public static void main(String[] args) {
        System.out.println("=== ProductService Test Suite ===\n");

        System.out.println("-- findById --");
        test("findById existing", () -> {
            var svc = makeService();
            var p = svc.findById(1);
            assertTrue(p.isPresent(), "should be present");
            assertEquals("Surface Pro", p.get().name(), "name");
        });
        test("findById missing returns empty", () -> {
            assertFalse(makeService().findById(99).isPresent(), "should be absent");
        });

        System.out.println("\n-- inStock --");
        test("inStock returns only stocked products", () -> {
            var results = makeService().inStock();
            assertEquals(3, results.size(), "inStock count");
            assertTrue(results.stream().allMatch(Product::inStock), "all in stock");
        });
        test("USB-C Hub is OOS", () -> {
            assertFalse(makeService().findById(4).orElseThrow().inStock(), "USB-C Hub OOS");
        });

        System.out.println("\n-- analytics --");
        test("totalValue correct", () -> {
            assertApprox(116849.21, makeService().totalValue(), 0.01, "totalValue");
        });
        test("cheapest is USB-C Hub", () -> {
            assertEquals("USB-C Hub", makeService().cheapest().orElseThrow().name(), "cheapest");
        });

        System.out.println("\n-- immutability --");
        test("withPrice returns new record", () -> {
            var p = new Product(1, "Surface Pro", 864.0, 15);
            var p2 = p.withPrice(799.0);
            assertEquals(864.0, p.price(), "original unchanged");
            assertEquals(799.0, p2.price(), "new price");
        });
        test("records are value-equal", () -> {
            var p1 = new Product(1, "Surface Pro", 864.0, 15);
            var p2 = new Product(1, "Surface Pro", 864.0, 15);
            assertEquals(p1, p2, "records equal");
        });

        System.out.println("\n-- edge cases --");
        test("empty service totalValue=0", () -> {
            assertApprox(0.0, new ProductService().totalValue(), 0.001, "empty total");
        });
        test("cheapest on empty returns empty", () -> {
            assertFalse(new ProductService().cheapest().isPresent(), "empty cheapest");
        });
        test("duplicate id overwrites", () -> {
            var svc = new ProductService();
            svc.add(new Product(1, "Old", 100.0, 10));
            svc.add(new Product(1, "New", 200.0, 20));
            assertEquals(1, svc.size(), "still 1 product");
            assertEquals("New", svc.findById(1).get().name(), "overwritten");
        });

        System.out.println("\n-- parametrized data-driven --");
        record TestCase(int id, String expectedName, double expectedPrice) {}
        var cases = List.of(
            new TestCase(1, "Surface Pro", 864.0),
            new TestCase(2, "Surface Pen", 49.99),
            new TestCase(3, "Office 365",  99.99)
        );
        var svc = makeService();
        for (var tc : cases) {
            test("product[" + tc.id() + "] name=" + tc.expectedName(), () -> {
                var p = svc.findById(tc.id()).orElseThrow();
                assertEquals(tc.expectedName(), p.name(), "name");
                assertApprox(tc.expectedPrice(), p.price(), 0.001, "price");
            });
        }

        System.out.println("\n=== Results ===");
        System.out.printf("  %d passed, %d failed  (%d total)%n", passed, failed, passed+failed);
        if (failed > 0) System.exit(1);
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab09.java:/tmp/Lab09.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab09.java -d /tmp && java -cp /tmp Lab09"
```

> 💡 **Parametrized tests eliminate copy-paste.** Instead of writing one test per product, store expected values in a `List<TestCase>` (using a record!) and loop over them. JUnit 5's `@ParameterizedTest` with `@MethodSource` does exactly this — the pattern is identical, just with annotations. Fewer tests, more coverage, less maintenance.

**📸 Verified Output:**
```
=== ProductService Test Suite ===

-- findById --
  PASS: findById existing
  PASS: findById missing returns empty

-- inStock --
  PASS: inStock returns only stocked products
  PASS: USB-C Hub is OOS

-- analytics --
  PASS: totalValue correct
  PASS: cheapest is USB-C Hub

-- immutability --
  PASS: withPrice returns new record
  PASS: records are value-equal

-- edge cases --
  PASS: empty service totalValue=0
  PASS: cheapest on empty returns empty
  PASS: duplicate id overwrites

-- parametrized data-driven --
  PASS: product[1] name=Surface Pro
  PASS: product[2] name=Surface Pen
  PASS: product[3] name=Office 365

=== Results ===
  14 passed, 0 failed  (14 total)
```

---

## Summary

| Assertion | Checks |
|-----------|--------|
| `assertEquals(expected, actual)` | Value equality |
| `assertTrue(cond)` | Condition is true |
| `assertFalse(cond)` | Condition is false |
| `assertApprox(exp, act, tol)` | Floating-point within tolerance |
| `assertThrows(Type, fn)` | Lambda throws expected exception |

**JUnit 5 equivalents:** `assertEquals`, `assertTrue`, `assertFalse`, `assertThat`, `assertThrows`, `@ParameterizedTest @MethodSource`.

## Further Reading
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito (mocking)](https://site.mockito.org/)
