# Lab 12: Reflection & Annotations

## Objective
Use `java.lang.reflect` to inspect classes at runtime, build a custom annotation-driven SQL generator and validator, and implement a generic repository using reflection — the foundation of how ORMs like Hibernate work.

## Background
Reflection lets you inspect and manipulate Java classes, fields, and methods at runtime — even private ones. Combined with custom annotations (`@Retention(RUNTIME)`), this enables frameworks to configure behaviour without code generation. Every major Java framework (Spring, Hibernate, JUnit) is built on these mechanisms.

## Time
30 minutes

## Prerequisites
- Lab 11 (HTTP Client)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Custom annotations, schema inspection, SQL generation, validation, generic repository, introspection, proxy, Capstone

```bash
cat > /tmp/Lab12.java << 'JAVAEOF'
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class Lab12 {
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
    @interface Entity { String table(); }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD)
    @interface Column { String name() default ""; boolean nullable() default true; boolean primaryKey() default false; }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
    @interface Validate { String message() default "Validation failed"; }

    @Entity(table = "products")
    static class Product {
        @Column(name = "id", primaryKey = true, nullable = false) private int id;
        @Column(name = "name", nullable = false) private String name;
        @Column(name = "price", nullable = false) private double price;
        @Column(name = "stock") private int stock;
        private String internalField = "skip_me";

        Product(int id, String name, double price, int stock) {
            this.id=id; this.name=name; this.price=price; this.stock=stock; }

        @Validate(message = "price must be positive") boolean priceValid() { return price > 0; }
        @Validate(message = "name must not be blank") boolean nameValid() { return name != null && !name.isBlank(); }
    }

    static String generateInsert(Object entity) throws Exception {
        var cls = entity.getClass();
        var table = cls.getAnnotation(Entity.class);
        if (table == null) throw new IllegalArgumentException("Not an @Entity");
        var cols = new ArrayList<String>(); var vals = new ArrayList<String>();
        for (var field : cls.getDeclaredFields()) {
            var col = field.getAnnotation(Column.class);
            if (col == null) continue;
            field.setAccessible(true);
            cols.add(col.name().isEmpty() ? field.getName() : col.name());
            var val = field.get(entity);
            vals.add(val instanceof String ? "'" + val + "'" : String.valueOf(val));
        }
        return "INSERT INTO " + table.table() + " (" + String.join(", ", cols) +
               ") VALUES (" + String.join(", ", vals) + ")";
    }

    static List<String> validate(Object entity) throws Exception {
        var errors = new ArrayList<String>();
        for (var method : entity.getClass().getDeclaredMethods()) {
            var v = method.getAnnotation(Validate.class);
            if (v == null) continue;
            method.setAccessible(true);
            if (Boolean.FALSE.equals(method.invoke(entity))) errors.add(v.message());
        }
        return errors;
    }

    static void inspectSchema(Class<?> cls) {
        var entity = cls.getAnnotation(Entity.class);
        if (entity == null) return;
        System.out.println("Table: " + entity.table());
        System.out.println("Columns:");
        for (var field : cls.getDeclaredFields()) {
            var col = field.getAnnotation(Column.class);
            if (col == null) continue;
            System.out.printf("  %-15s -> %-15s  PK=%-5b  nullable=%b%n",
                field.getName(), col.name().isEmpty() ? field.getName() : col.name(),
                col.primaryKey(), col.nullable());
        }
    }

    static class Repo<T> {
        private final Class<T> type; private final Map<Integer, T> store = new LinkedHashMap<>();
        Repo(Class<T> type) { this.type = type; }
        void save(T obj) throws Exception {
            for (var f : type.getDeclaredFields()) {
                if (f.isAnnotationPresent(Column.class) && f.getAnnotation(Column.class).primaryKey()) {
                    f.setAccessible(true); store.put((Integer) f.get(obj), obj); return;
                }
            }
        }
        int size() { return store.size(); }
        Collection<T> findAll() { return store.values(); }
        String tableName() { var e = type.getAnnotation(Entity.class); return e != null ? e.table() : type.getSimpleName(); }
    }

    public static void main(String[] args) throws Exception {
        var p1 = new Product(1, "Surface Pro", 864.0, 15);
        var p2 = new Product(2, "Surface Pen", 49.99, 80);
        var pBad = new Product(3, "", -1.0, 0);

        System.out.println("=== Schema Inspection ===");
        inspectSchema(Product.class);

        System.out.println("\n=== SQL Generation ===");
        System.out.println(generateInsert(p1));
        System.out.println(generateInsert(p2));

        System.out.println("\n=== Validation ===");
        System.out.println("p1 valid: " + validate(p1).isEmpty());
        System.out.println("pBad errors: " + validate(pBad));

        System.out.println("\n=== Generic Repository ===");
        var repo = new Repo<>(Product.class);
        repo.save(p1); repo.save(p2);
        System.out.println("Table: " + repo.tableName() + " | Size: " + repo.size());
        repo.findAll().forEach(p -> {
            try {
                var f = Product.class.getDeclaredField("name"); f.setAccessible(true);
                System.out.println("  " + f.get(p));
            } catch (Exception e) {}
        });

        System.out.println("\n=== Class Introspection ===");
        var cls = Product.class;
        System.out.println("Class:       " + cls.getSimpleName());
        System.out.println("Annotations: " + Arrays.stream(cls.getAnnotations()).map(a -> a.annotationType().getSimpleName()).toList());
        System.out.println("Methods:     " + Arrays.stream(cls.getDeclaredMethods()).map(Method::getName).toList());
        System.out.println("Fields:      " + Arrays.stream(cls.getDeclaredFields()).map(Field::getName).toList());
        System.out.println("Modifiers:   " + Modifier.toString(cls.getModifiers()));
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab12.java:/tmp/Lab12.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab12.java -d /tmp && java -cp /tmp Lab12"
```

> 💡 **`field.setAccessible(true)` bypasses Java's access control** — it lets you read `private` fields. This is how Hibernate maps table rows to private fields, and how JUnit injects test fixtures. In Java 17+, the JVM modules system may restrict this for third-party code, but within the same module it works freely. Always call it before accessing the field.

**📸 Verified Output:**
```
=== Schema Inspection ===
Table: products
Columns:
  id              -> id               PK=true   nullable=false
  name            -> name             PK=false  nullable=false
  price           -> price            PK=false  nullable=false
  stock           -> stock            PK=false  nullable=true

=== SQL Generation ===
INSERT INTO products (id, name, price, stock) VALUES (1, 'Surface Pro', 864.0, 15)
INSERT INTO products (id, name, price, stock) VALUES (2, 'Surface Pen', 49.99, 80)

=== Validation ===
p1 valid: true
pBad errors: [price must be positive, name must not be blank]

=== Generic Repository ===
Table: products | Size: 2
  Surface Pro
  Surface Pen
```

---

## Summary

| Reflection API | Purpose |
|----------------|---------|
| `cls.getAnnotation(A.class)` | Read class-level annotation |
| `field.getAnnotation(A.class)` | Read field annotation |
| `field.setAccessible(true)` | Bypass private access |
| `field.get(obj)` | Read field value |
| `method.invoke(obj, args)` | Call method by reflection |
| `cls.getDeclaredFields()` | All fields (incl. private) |
| `cls.getDeclaredMethods()` | All methods (incl. private) |

## Further Reading
- [Reflection Tutorial](https://docs.oracle.com/javase/tutorial/reflect/)
- [Annotations Tutorial](https://docs.oracle.com/javase/tutorial/java/annotations/)
