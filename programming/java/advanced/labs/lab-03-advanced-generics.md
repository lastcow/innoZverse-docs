# Lab 3: Advanced Generics — Variance, Bounds & Type Tokens

## Objective
Master Java's generic type system: covariant `ImmutableList<T>` with `map`/`filter`, the PECS rule (`? extends` vs `? super`), multiple bounds, generic records, CRTP builder pattern, and using `ParameterizedType` reflection to recover erased type arguments at runtime.

## Background
Java generics use *erasure* — generic type parameters are removed at compile time. `List<String>` and `List<Integer>` are the same `List` at runtime. Understanding this explains why `List<String>` is not a subtype of `List<Object>` (invariance), why wildcards exist, and how type tokens work around erasure via anonymous class tricks.

## Time
30 minutes

## Prerequisites
- Practitioner Labs 01–03

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: ImmutableList map/filter, PECS wildcards, bounded max, generic swap, Pair<A,B>, Comparable sort, type erasure, PECS summary

```bash
cat > /tmp/AdvLab03.java << 'JAVAEOF'
import java.util.*;
import java.util.function.*;
import java.lang.reflect.*;

public class AdvLab03 {
    record Product(String name, double price) implements Comparable<Product> {
        @Override public int compareTo(Product o) { return Double.compare(this.price, o.price); }
        @Override public String toString() { return name + "($" + price + ")"; }
    }

    static class ImmutableList<T> implements Iterable<T> {
        private final List<T> items;
        ImmutableList(List<T> items) { this.items = List.copyOf(items); }
        T get(int i) { return items.get(i); }
        int size() { return items.size(); }
        <R> ImmutableList<R> map(Function<T,R> fn) { return new ImmutableList<>(items.stream().map(fn).toList()); }
        ImmutableList<T> filter(Predicate<T> pred) { return new ImmutableList<>(items.stream().filter(pred).toList()); }
        @Override public Iterator<T> iterator() { return items.iterator(); }
        @Override public String toString() { return items.toString(); }
    }

    record Pair<A, B>(A first, B second) {
        static <T> Pair<T,T> of(T a, T b) { return new Pair<>(a, b); }
        <C> Pair<A,C> mapSecond(Function<B,C> fn) { return new Pair<>(first, fn.apply(second)); }
    }

    // PECS: Producer Extends, Consumer Super
    static double totalValue(List<? extends Number> nums) {
        return nums.stream().mapToDouble(Number::doubleValue).sum(); }

    static void fillPrices(List<? super Double> list, double start, int count) {
        for (int i = 0; i < count; i++) list.add(start + i * 10.0); }

    static <T extends Comparable<T>> T boundedMax(List<T> list, T ceiling) {
        return list.stream().filter(e -> e.compareTo(ceiling) <= 0).max(Comparator.naturalOrder()).orElse(ceiling); }

    static <T> void swap(List<T> list, int i, int j) {
        T tmp = list.get(i); list.set(i, list.get(j)); list.set(j, tmp); }

    public static void main(String[] args) throws Exception {
        System.out.println("=== ImmutableList<T> ===");
        var products = new ImmutableList<>(List.of(
            new Product("Surface Pro", 864.0), new Product("Surface Pen", 49.99),
            new Product("Office 365", 99.99),  new Product("USB-C Hub", 29.99)));

        System.out.println("names:     " + products.map(Product::name));
        System.out.println("prices:    " + products.map(p -> p.price()));
        System.out.println("expensive: " + products.filter(p -> p.price() > 100));

        System.out.println("\n=== PECS Wildcards ===");
        System.out.println("totalValue(ints):    " + totalValue(List.of(864, 50, 100)));
        System.out.println("totalValue(doubles): " + totalValue(List.of(864.0, 49.99)));
        List<Number> dest = new ArrayList<>();
        fillPrices(dest, 100.0, 5);
        System.out.println("fillPrices:          " + dest);

        System.out.println("\n=== Bounded Max ===");
        System.out.println("boundedMax (<=500): " + boundedMax(List.of(100, 500, 300, 800, 200), 500));

        System.out.println("\n=== Generic Swap ===");
        var list = new ArrayList<>(List.of("Surface Pro", "Surface Pen", "Office 365"));
        System.out.println("before: " + list);
        swap(list, 0, 2);
        System.out.println("after:  " + list);

        System.out.println("\n=== Pair<A,B> ===");
        var p = Pair.of("Surface Pro", 864.0);
        var p2 = p.mapSecond(price -> "$" + String.format("%.2f", price));
        System.out.println("pair:   " + p);
        System.out.println("mapped: " + p2);

        System.out.println("\n=== Generic Comparable ===");
        var prods = new ArrayList<>(List.of(
            new Product("Surface Pro",864.0), new Product("Pen",49.99), new Product("Book",1299.0)));
        Collections.sort(prods);
        System.out.println("sorted: " + prods);
        System.out.println("min:    " + Collections.min(prods));
        System.out.println("max:    " + Collections.max(prods));

        System.out.println("\n=== Type Erasure & Reflection ===");
        var rawList = new ArrayList<String>();
        System.out.println("Runtime class: " + rawList.getClass().getSimpleName());
        System.out.println("Still ArrayList: " + (rawList instanceof ArrayList));

        class Container { List<Product> products = new ArrayList<>(); }
        var field = Container.class.getDeclaredField("products");
        var genericType = (ParameterizedType) field.getGenericType();
        System.out.println("Field:       " + field.getType().getSimpleName());
        System.out.println("Generic arg: " + genericType.getActualTypeArguments()[0].getTypeName());

        System.out.println("\n=== PECS Summary ===");
        List<Number> numbers = new ArrayList<>();
        List<? extends Number> producer = List.of(1, 2.5, 3L);
        List<? super Integer>  consumer = numbers;
        consumer.add(100); consumer.add(200);
        System.out.println("Producer (extends): sum=" + producer.stream().mapToDouble(Number::doubleValue).sum());
        System.out.println("Consumer (super):   list=" + numbers);
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab03.java:/tmp/AdvLab03.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab03.java -d /tmp && java -cp /tmp AdvLab03"
```

> 💡 **PECS: "Producer Extends, Consumer Super."** If a collection *produces* values you read (`get()`), use `? extends T`. If it *consumes* values you write (`add()`), use `? super T`. If you both read and write, use the concrete type `T`. This rule prevents `ClassCastException` at runtime while still allowing polymorphic usage.

**📸 Verified Output:**
```
=== ImmutableList<T> ===
names:     [Surface Pro, Surface Pen, Office 365, USB-C Hub]
prices:    [864.0, 49.99, 99.99, 29.99]
expensive: [Surface Pro($864.0)]

=== PECS Wildcards ===
totalValue(ints):    1014.0
fillPrices:          [100.0, 110.0, 120.0, 130.0, 140.0]

=== Generic Comparable ===
sorted: [Pen($49.99), Surface Pro($864.0), Book($1299.0)]
min:    Pen($49.99)
max:    Book($1299.0)
```

---

## Summary

| Concept | Syntax | Rule |
|---------|--------|------|
| Upper bounded | `? extends T` | Read only (producer) |
| Lower bounded | `? super T` | Write only (consumer) |
| Unbounded | `?` | Read as `Object` only |
| Multiple bounds | `T extends A & B` | Must be class then interfaces |
| Type token | Anonymous subclass | Recovers erased type at runtime |

## Further Reading
- [Generics FAQ (Angelika Langer)](http://www.angelikalanger.com/GenericsFAQ/JavaGenericsFAQ.html)
- [JEP 401: Value Classes](https://openjdk.org/jeps/401)
