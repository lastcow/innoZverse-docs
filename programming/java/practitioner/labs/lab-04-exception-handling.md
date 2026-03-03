# Lab 4: Exception Handling & Custom Exceptions

## Objective
Build a typed exception hierarchy, practice multi-catch, try-with-resources, `finally`, and implement the **Result type** pattern using sealed interfaces for exception-free error propagation.

## Background
Java distinguishes checked exceptions (must be declared/caught) from unchecked `RuntimeException` subclasses (optional). Well-designed exception hierarchies with meaningful error codes let callers react to specific failures without parsing message strings. The `Result<T>` pattern (borrowed from functional languages) is increasingly popular in Java 21 codebases.

## Time
25 minutes

## Prerequisites
- Lab 03 (Functional Interfaces)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Step 1: Custom Exception Hierarchy

```bash
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Lab04.java << 'EOF'
import java.util.*;
import java.util.function.*;

public class Lab04 {
    static class AppException extends RuntimeException {
        private final String code;
        AppException(String code, String msg) { super(msg); this.code = code; }
        public String getCode() { return code; }
        @Override public String toString() { return \"[\" + code + \"] \" + getMessage(); }
    }
    static class ProductNotFoundException extends AppException {
        ProductNotFoundException(int id) { super(\"PRODUCT_NOT_FOUND\", \"Product \" + id + \" not found\"); }
    }
    static class InsufficientStockException extends AppException {
        InsufficientStockException(String name, int req, int avail) {
            super(\"INSUFFICIENT_STOCK\", name + \": requested \" + req + \" but only \" + avail); }
    }
    static class ValidationException extends AppException {
        ValidationException(String f, String m) { super(\"VALIDATION_ERROR\", f + \": \" + m); }
    }

    record Product(int id, String name, double price, int stock) {}
    static Map<Integer, Product> catalog = new HashMap<>(Map.of(
        1, new Product(1, \"Surface Pro\", 864.0, 15),
        2, new Product(2, \"Surface Pen\", 49.99, 80)));

    static Product getProduct(int id) {
        var p = catalog.get(id);
        if (p == null) throw new ProductNotFoundException(id);
        return p;
    }

    static void placeOrder(int productId, int qty) {
        if (qty <= 0) throw new ValidationException(\"qty\", \"must be > 0, got \" + qty);
        var p = getProduct(productId);
        if (p.stock() < qty) throw new InsufficientStockException(p.name(), qty, p.stock());
        catalog.put(productId, new Product(p.id(), p.name(), p.price(), p.stock() - qty));
        System.out.printf(\"  \u2713 Order: %d x %s @ \$%.2f = \$%.2f (stock now %d)%n\",
            qty, p.name(), p.price(), qty * p.price(), p.stock() - qty);
    }

    sealed interface Result<T> permits Result.Ok, Result.Err {
        record Ok<T>(T value) implements Result<T> {}
        record Err<T>(String code, String message) implements Result<T> {}
        static <T> Result<T> of(Supplier<T> fn) {
            try { return new Ok<>(fn.get()); }
            catch (AppException e) { return new Err<>(e.getCode(), e.getMessage()); }
        }
        default boolean isOk() { return this instanceof Ok; }
    }

    public static void main(String[] args) {
        try { placeOrder(1, 3); } catch (AppException e) { System.out.println(\"Error: \" + e); }
        try { placeOrder(99, 1); } catch (ProductNotFoundException e) { System.out.println(\"Caught: \" + e); }
        try { placeOrder(2, 100); } catch (InsufficientStockException e) { System.out.println(\"Caught: \" + e); }
        try { placeOrder(1, -5); } catch (ValidationException e) { System.out.println(\"Caught: \" + e); }

        // Multi-catch
        for (int id : new int[]{1, 99, 2}) {
            try { var p = getProduct(id); System.out.println(\"Found: \" + p.name()); }
            catch (ProductNotFoundException | ValidationException e) { System.out.println(\"Handled: \" + e.getCode()); }
        }

        // Result type
        System.out.println(\"\\nResult type:\");
        Result<Product> r1 = Result.of(() -> getProduct(1));
        Result<Product> r2 = Result.of(() -> getProduct(99));
        if (r1 instanceof Result.Ok<Product> ok) System.out.println(\"r1 ok: \" + ok.value().name());
        if (r2 instanceof Result.Err<Product> err) System.out.println(\"r2 err: \" + err.code() + \" - \" + err.message());

        // finally
        System.out.println(\"\\nFinally:\");
        try {
            try { placeOrder(99, 1); }
            finally { System.out.println(\"  [finally] cleanup\"); }
        } catch (AppException e) { System.out.println(\"  [catch] \" + e.getCode()); }
    }
}
EOF
javac /tmp/Lab04.java -d /tmp && java -cp /tmp Lab04"
```

> 💡 **`RuntimeException` vs checked exceptions:** Checked exceptions (like `IOException`) force callers to handle them — good for recoverable conditions callers must plan for. `RuntimeException` subclasses are unchecked — good for programming errors and domain violations where every call site shouldn't be cluttered with `try/catch`. Modern Java style prefers unchecked exceptions with descriptive codes over checked exceptions.

**📸 Verified Output:**
```
  ✓ Order: 3 x Surface Pro @ $864.00 = $2592.00 (stock now 12)
Caught: [PRODUCT_NOT_FOUND] Product 99 not found
Caught: [INSUFFICIENT_STOCK] Surface Pen: requested 100 but only 80
Caught: [VALIDATION_ERROR] qty: must be > 0, got -5
Found: Surface Pro
Handled: PRODUCT_NOT_FOUND
Found: Surface Pen

Result type:
r1 ok: Surface Pro
r2 err: PRODUCT_NOT_FOUND - Product 99 not found

Finally:
  [finally] cleanup
  [catch] PRODUCT_NOT_FOUND
```

---

## Summary

| Pattern | Use when |
|---------|----------|
| Custom `RuntimeException` hierarchy | Domain-specific errors with error codes |
| Multi-catch `A \| B` | Same handling for multiple exception types |
| `finally` | Guaranteed cleanup (always runs) |
| `try-with-resources` | Auto-close `AutoCloseable` resources |
| `Result<T>` sealed | Exception-free error propagation in functional pipelines |

## Further Reading
- [Java Exception Handling](https://docs.oracle.com/javase/tutorial/essential/exceptions/)
- [Sealed Interfaces](https://openjdk.org/jeps/395)
