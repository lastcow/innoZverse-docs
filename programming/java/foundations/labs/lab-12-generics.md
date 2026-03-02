# Lab 12: Generics

## Objective
Write generic classes and methods, use bounded type parameters, understand wildcards (`? extends`, `? super`), and apply the PECS principle (Producer Extends, Consumer Super).

## Background
Generics enable type-safe, reusable code — a single `Stack<T>` works for `String`, `Integer`, or any type, with compile-time type checking. Without generics you'd cast everywhere and discover `ClassCastException` at runtime. Understanding generics deeply unlocks the Collections framework, Streams, Optional, and every modern Java library.

## Time
40 minutes

## Prerequisites
- Lab 06 (OOP)
- Lab 08 (Interfaces)
- Lab 09 (Collections)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Generic Classes

```java
// GenericClasses.java
import java.util.*;

public class GenericClasses {

    static class Box<T> {
        private T value;

        Box(T value) { this.value = value; }
        T get() { return value; }
        void set(T value) { this.value = value; }

        <R> Box<R> map(java.util.function.Function<T, R> fn) {
            return new Box<>(fn.apply(value));
        }

        @Override
        public String toString() { return "Box[" + value + "]"; }
    }

    static class Pair<A, B> {
        final A first;
        final B second;

        Pair(A first, B second) { this.first = first; this.second = second; }

        Pair<B, A> swap() { return new Pair<>(second, first); }

        static <X, Y> Pair<X, Y> of(X x, Y y) { return new Pair<>(x, y); }

        @Override
        public String toString() { return "(" + first + ", " + second + ")"; }
    }

    public static void main(String[] args) {
        Box<String> strBox = new Box<>("Hello");
        Box<Integer> intBox = new Box<>(42);

        System.out.println(strBox);
        System.out.println(intBox);

        Box<Integer> lengthBox = strBox.map(String::length);
        System.out.println("Length: " + lengthBox);

        // Type inference
        var pair = Pair.of("Alice", 95);
        System.out.println("\nPair: " + pair);
        System.out.println("Swapped: " + pair.swap());

        // Diamond operator
        List<Pair<String, Integer>> scores = new ArrayList<>();
        scores.add(Pair.of("Alice", 95));
        scores.add(Pair.of("Bob", 87));
        scores.add(Pair.of("Carol", 92));

        scores.stream()
            .sorted((a, b) -> Integer.compare(b.second, a.second))
            .forEach(p -> System.out.printf("  %-10s %d%n", p.first, p.second));
    }
}
```

> 💡 **Type parameters** (`<T>`, `<A, B>`) are replaced at compile time with actual types. The diamond `<>` lets the compiler infer the type from context. Generics exist only at compile time — at runtime all `Box<String>` and `Box<Integer>` are just `Box` (type erasure).

**📸 Verified Output:**
```
Box[Hello]
Box[42]
Length: Box[5]

Pair: (Alice, 95)
Swapped: (95, Alice)
  Alice      95
  Carol      92
  Bob        87
```

---

### Step 2: Generic Methods

```java
// GenericMethods.java
import java.util.*;

public class GenericMethods {

    // Type parameter on method
    static <T> List<T> repeat(T item, int times) {
        List<T> result = new ArrayList<>();
        for (int i = 0; i < times; i++) result.add(item);
        return result;
    }

    static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    static <T extends Comparable<T>> T clamp(T value, T min, T max) {
        if (value.compareTo(min) < 0) return min;
        if (value.compareTo(max) > 0) return max;
        return value;
    }

    static <T> void swap(T[] arr, int i, int j) {
        T tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
    }

    static <K, V> Map<V, K> invertMap(Map<K, V> map) {
        Map<V, K> result = new HashMap<>();
        map.forEach((k, v) -> result.put(v, k));
        return result;
    }

    public static void main(String[] args) {
        System.out.println(repeat("hello", 3));
        System.out.println(repeat(42, 4));

        System.out.println("\nmax(3, 7): " + max(3, 7));
        System.out.println("max(\"apple\", \"banana\"): " + max("apple", "banana"));

        System.out.println("\nclamp(15, 0, 10): " + clamp(15, 0, 10));
        System.out.println("clamp(-5, 0, 10): " + clamp(-5, 0, 10));
        System.out.println("clamp(5, 0, 10):  " + clamp(5, 0, 10));

        Integer[] arr = {1, 2, 3, 4, 5};
        swap(arr, 0, 4);
        System.out.println("\nAfter swap(0,4): " + Arrays.toString(arr));

        Map<String, Integer> map = Map.of("one", 1, "two", 2, "three", 3);
        Map<Integer, String> inverted = invertMap(map);
        System.out.println("\nInverted: " + new TreeMap<>(inverted));
    }
}
```

> 💡 **`<T extends Comparable<T>>`** is a bounded type parameter — `T` must implement `Comparable<T>`. This lets you call `compareTo()` inside the method. Without the bound, the compiler doesn't know `T` has any methods. Bounds enable generic algorithms that work on any compatible type.

**📸 Verified Output:**
```
[hello, hello, hello]
[42, 42, 42, 42]

max(3, 7): 7
max("apple", "banana"): banana

clamp(15, 0, 10): 10
clamp(-5, 0, 10): 0
clamp(5, 0, 10):  5

After swap(0,4): [5, 2, 3, 4, 1]

Inverted: {1=one, 2=two, 3=three}
```

---

### Step 3: Bounded Type Parameters

```java
// BoundedTypes.java
import java.util.*;

public class BoundedTypes {

    // Upper bound: T must be a Number subtype
    static <T extends Number> double sum(List<T> list) {
        return list.stream().mapToDouble(Number::doubleValue).sum();
    }

    static <T extends Number & Comparable<T>> T findMax(List<T> list) {
        if (list.isEmpty()) throw new NoSuchElementException();
        T max = list.get(0);
        for (T item : list) if (item.compareTo(max) > 0) max = item;
        return max;
    }

    // Multiple bounds: T extends A & B & C
    interface Printable { void print(); }
    interface Saveable  { void save();  }

    static class Document implements Printable, Saveable, Comparable<Document> {
        final String title;
        Document(String t) { this.title = t; }
        public void print() { System.out.println("Print: " + title); }
        public void save()  { System.out.println("Save:  " + title); }
        public int compareTo(Document o) { return title.compareTo(o.title); }
        public String toString() { return "Doc(" + title + ")"; }
    }

    static <T extends Printable & Saveable & Comparable<T>> void processAll(List<T> items) {
        List<T> sorted = new ArrayList<>(items);
        Collections.sort(sorted);
        sorted.forEach(item -> { item.print(); item.save(); });
    }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2, 3, 4, 5);
        List<Double>  dbls = List.of(1.5, 2.5, 3.5);

        System.out.println("sum(ints): " + sum(ints));
        System.out.println("sum(doubles): " + sum(dbls));
        System.out.println("max(ints): " + findMax(ints));

        System.out.println();
        processAll(List.of(
            new Document("Zebra Report"),
            new Document("Alpha Report"),
            new Document("Moon Report")
        ));
    }
}
```

> 💡 **Multiple bounds** use `&`: `<T extends Number & Comparable<T>>`. The class bound (if any) must come first, followed by interface bounds. This lets you call methods from all bounded types within the generic method. It's used in the JDK itself: `<T extends Object & Comparable<? super T>>` for `Collections.max()`.

**📸 Verified Output:**
```
sum(ints): 15.0
sum(doubles): 7.5
max(ints): 5

Print: Alpha Report
Save:  Alpha Report
Print: Moon Report
Save:  Moon Report
Print: Zebra Report
Save:  Zebra Report
```

---

### Step 4: Wildcards — `?`, `? extends`, `? super`

```java
// Wildcards.java
import java.util.*;

public class Wildcards {

    // Unbounded wildcard — read-only, any type
    static void printList(List<?> list) {
        list.forEach(e -> System.out.print(e + " "));
        System.out.println();
    }

    // Upper bounded — Producer (read from list)
    static double totalArea(List<? extends Shape> shapes) {
        return shapes.stream().mapToDouble(Shape::area).sum();
    }

    // Lower bounded — Consumer (write to list)
    static void addNumbers(List<? super Integer> list, int count) {
        for (int i = 1; i <= count; i++) list.add(i);
    }

    interface Shape { double area(); }
    record Circle(double r) implements Shape { public double area() { return Math.PI*r*r; } }
    record Rect(double w, double h) implements Shape { public double area() { return w*h; } }

    public static void main(String[] args) {
        // Unbounded
        printList(List.of(1, 2, 3));
        printList(List.of("a", "b", "c"));

        // Upper bound — can read as Shape, can't add
        List<Circle> circles = new ArrayList<>(List.of(new Circle(3), new Circle(5)));
        List<Rect> rects = new ArrayList<>(List.of(new Rect(4, 2), new Rect(3, 3)));

        System.out.printf("Circle area: %.2f%n", totalArea(circles));
        System.out.printf("Rect area:   %.2f%n", totalArea(rects));
        // circles.add(new Rect(...)) — compile error (good!)

        // Lower bound — can add Integer or subtypes
        List<Number> numbers = new ArrayList<>();
        addNumbers(numbers, 5);
        System.out.println("Added: " + numbers);

        List<Object> objects = new ArrayList<>();
        addNumbers(objects, 3);
        System.out.println("Objects: " + objects);

        // PECS: Producer Extends, Consumer Super
        // Copy from src (produces) to dst (consumes)
        List<Integer> src = List.of(1, 2, 3, 4, 5);
        List<Number> dst = new ArrayList<>();
        copyList(src, dst);
        System.out.println("Copied: " + dst);
    }

    // PECS example
    static <T> void copyList(List<? extends T> src, List<? super T> dst) {
        dst.addAll(src);
    }
}
```

> 💡 **PECS — Producer Extends, Consumer Super:** If a parameter *provides* (produces) values for you to read → `? extends T`. If a parameter *accepts* (consumes) values you write → `? super T`. `Collections.copy(dst, src)` uses `List<? super T>` for dst and `List<? extends T>` for src — the canonical PECS example.

**📸 Verified Output:**
```
1 2 3
a b c
Circle area: 106.81
Rect area:   17.00
Added: [1, 2, 3, 4, 5]
Objects: [1, 2, 3]
Copied: [1, 2, 3, 4, 5]
```

---

### Step 5: Generic Data Structures

```java
// GenericStack.java
import java.util.*;

public class GenericStack {

    static class Stack<T> implements Iterable<T> {
        private Object[] elements;
        private int size = 0;

        @SuppressWarnings("unchecked")
        Stack(int capacity) { elements = new Object[capacity]; }

        void push(T item) {
            if (size == elements.length) grow();
            elements[size++] = item;
        }

        @SuppressWarnings("unchecked")
        T pop() {
            if (isEmpty()) throw new EmptyStackException();
            T item = (T) elements[--size];
            elements[size] = null; // prevent memory leak
            return item;
        }

        @SuppressWarnings("unchecked")
        T peek() {
            if (isEmpty()) throw new EmptyStackException();
            return (T) elements[size - 1];
        }

        boolean isEmpty() { return size == 0; }
        int size() { return size; }

        private void grow() {
            elements = Arrays.copyOf(elements, elements.length * 2);
        }

        @Override
        public Iterator<T> iterator() {
            return new Iterator<T>() {
                int i = size;
                public boolean hasNext() { return i > 0; }
                @SuppressWarnings("unchecked")
                public T next() { return (T) elements[--i]; }
            };
        }
    }

    public static void main(String[] args) {
        Stack<String> stack = new Stack<>(4);
        stack.push("first");
        stack.push("second");
        stack.push("third");

        System.out.println("Size: " + stack.size());
        System.out.println("Peek: " + stack.peek());
        System.out.println("Pop: " + stack.pop());
        System.out.println("Pop: " + stack.pop());

        // Iterable support
        Stack<Integer> numStack = new Stack<>(8);
        for (int i = 1; i <= 6; i++) numStack.push(i);
        System.out.print("\nIteration (top to bottom): ");
        for (int n : numStack) System.out.print(n + " ");
        System.out.println();

        // Auto-grow
        Stack<Double> bigStack = new Stack<>(2);
        for (int i = 0; i < 10; i++) bigStack.push(i * 1.5);
        System.out.println("Grew to size: " + bigStack.size());
    }
}
```

> 💡 **`@SuppressWarnings("unchecked")`** silences the cast warning from `Object[]` to `T[]`. This is necessary because Java can't create `T[]` directly (`new T[n]` is illegal — type erasure). The cast is safe here because we only store `T` instances, but the compiler can't verify it. Use this annotation minimally and only when the cast is provably safe.

**📸 Verified Output:**
```
Size: 3
Peek: third
Pop: third
Pop: second

Iteration (top to bottom): 6 5 4 3 2 1
Grew to size: 10
```

---

### Step 6: Type Inference & var

```java
// TypeInference.java
import java.util.*;
import java.util.function.*;

public class TypeInference {
    public static void main(String[] args) {
        // var — local variable type inference (Java 10+)
        var list = new ArrayList<String>();  // inferred as ArrayList<String>
        list.add("hello");
        list.add("world");
        var upper = list.stream().map(String::toUpperCase).toList();
        System.out.println(upper);

        // Method reference type inference
        Function<String, Integer> len = String::length;
        BiFunction<String, String, String> concat = String::concat;
        Comparator<String> cmp = String::compareTo;

        System.out.println(len.apply("hello"));
        System.out.println(concat.apply("foo", "bar"));

        var words = List.of("banana", "apple", "cherry");
        words.stream().sorted(cmp).forEach(System.out::println);

        // Diamond on anonymous class — not allowed, but records/lambdas work
        // Generic method inference
        var pair = makePair(42, "hello");  // infers Pair<Integer, String>
        System.out.println("\nInferred pair: " + pair);

        // Wildcard capture
        List<Integer> ints = new ArrayList<>(List.of(3, 1, 4, 1, 5, 9));
        sortAndPrint(ints);
    }

    record Pair<A, B>(A first, B second) {}

    static <A, B> Pair<A, B> makePair(A a, B b) { return new Pair<>(a, b); }

    // Wildcard capture helper
    static <T extends Comparable<T>> void sortAndPrint(List<T> list) {
        List<T> copy = new ArrayList<>(list);
        Collections.sort(copy);
        System.out.println("Sorted: " + copy);
    }
}
```

> 💡 **`var` doesn't mean dynamic typing** — the type is fixed at compile time, just inferred. `var x = new ArrayList<String>()` is exactly `ArrayList<String> x = new ArrayList<String>()`. Use `var` when the type is obvious from the right side; avoid it when it obscures what type you're working with.

**📸 Verified Output:**
```
[HELLO, WORLD]
5
foobar
apple
banana
cherry

Inferred pair: Pair[first=42, second=hello]
Sorted: [1, 1, 3, 4, 5, 9]
```

---

### Step 7: Generics with Reflection

```java
// GenericsReflection.java
import java.util.*;
import java.lang.reflect.*;

public class GenericsReflection {

    // Type token pattern — preserve type at runtime
    static class TypedList<T> {
        private final Class<T> type;
        private final List<T> items = new ArrayList<>();

        TypedList(Class<T> type) { this.type = type; }

        void add(Object item) {
            if (!type.isInstance(item))
                throw new ClassCastException("Expected " + type.getSimpleName() + ", got " + item.getClass().getSimpleName());
            items.add(type.cast(item));
        }

        List<T> getAll() { return Collections.unmodifiableList(items); }
        Class<T> getType() { return type; }
    }

    // Generic factory using reflection
    static <T> T create(Class<T> clazz) throws ReflectiveOperationException {
        return clazz.getDeclaredConstructor().newInstance();
    }

    public static void main(String[] args) throws Exception {
        // Type token
        TypedList<String> strings = new TypedList<>(String.class);
        strings.add("hello");
        strings.add("world");
        System.out.println("Type: " + strings.getType().getSimpleName());
        System.out.println("Items: " + strings.getAll());

        try {
            strings.add(42);  // wrong type
        } catch (ClassCastException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        // Generic factory
        ArrayList<?> list = create(ArrayList.class);
        System.out.println("\nCreated: " + list.getClass().getSimpleName());

        // getGenericSuperclass — inspect generic type info
        class StringList extends ArrayList<String> {}
        Type superType = StringList.class.getGenericSuperclass();
        System.out.println("Generic superclass: " + superType);
        if (superType instanceof ParameterizedType pt) {
            System.out.println("Type arg: " + pt.getActualTypeArguments()[0]);
        }
    }
}
```

> 💡 **Type tokens** (`Class<T>`) are the standard Java pattern to preserve generic type information at runtime (working around erasure). Libraries like Jackson, Gson, Spring, and Hibernate use this pattern extensively. `TypeReference<List<String>>` in Jackson is a more sophisticated version.

**📸 Verified Output:**
```
Type: String
Items: [hello, world]
Rejected: Expected String, got Integer

Created: ArrayList
Generic superclass: java.util.ArrayList<java.lang.String>
Type arg: class java.lang.String
```

---

### Step 8: Complete Example — Generic Repository

```java
// GenericRepository.java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class GenericRepository {

    interface Entity { String getId(); }

    static class Repository<T extends Entity> {
        private final Map<String, T> store = new LinkedHashMap<>();

        void save(T entity) { store.put(entity.getId(), entity); }

        Optional<T> findById(String id) { return Optional.ofNullable(store.get(id)); }

        List<T> findAll() { return new ArrayList<>(store.values()); }

        List<T> findWhere(Predicate<T> predicate) {
            return store.values().stream().filter(predicate).collect(Collectors.toList());
        }

        <R extends Comparable<R>> List<T> findAllSortedBy(Function<T, R> keyExtractor) {
            return store.values().stream()
                .sorted(Comparator.comparing(keyExtractor))
                .collect(Collectors.toList());
        }

        boolean delete(String id) { return store.remove(id) != null; }
        int count() { return store.size(); }
    }

    record User(String id, String name, String role, int age) implements Entity {}
    record Product(String id, String name, double price, int stock) implements Entity {}

    public static void main(String[] args) {
        var userRepo = new Repository<User>();
        userRepo.save(new User("U1", "Alice", "admin", 30));
        userRepo.save(new User("U2", "Bob", "user", 25));
        userRepo.save(new User("U3", "Carol", "user", 35));
        userRepo.save(new User("U4", "Dave", "admin", 28));

        System.out.println("Users: " + userRepo.count());
        userRepo.findById("U2").ifPresent(u -> System.out.println("Found: " + u.name()));

        System.out.println("\nAdmins:");
        userRepo.findWhere(u -> u.role().equals("admin"))
            .forEach(u -> System.out.println("  " + u.name() + " (age " + u.age() + ")"));

        System.out.println("\nSorted by age:");
        userRepo.findAllSortedBy(User::age)
            .forEach(u -> System.out.printf("  %-10s %d%n", u.name(), u.age()));

        // Same pattern works for Products
        var productRepo = new Repository<Product>();
        productRepo.save(new Product("P1", "Apple", 1.99, 100));
        productRepo.save(new Product("P2", "Banana", 0.75, 50));
        productRepo.save(new Product("P3", "Cherry", 3.50, 25));

        System.out.println("\nLow stock (< 60):");
        productRepo.findWhere(p -> p.stock() < 60)
            .forEach(p -> System.out.printf("  %-10s $%.2f (stock: %d)%n",
                p.name(), p.price(), p.stock()));
    }
}
```

> 💡 **A generic `Repository<T extends Entity>`** works for Users, Products, Orders — any entity with an ID. This is the Repository pattern used in Spring Data JPA. The `<R extends Comparable<R>>` on `findAllSortedBy` ensures you can only sort by comparable fields, catching type errors at compile time.

**📸 Verified Output:**
```
Users: 4
Found: Bob

Admins:
  Alice (age 30)
  Dave (age 28)

Sorted by age:
  Bob        25
  Dave       28
  Alice      30
  Carol      35

Low stock (< 60):
  Banana     $0.75 (stock: 50)
  Cherry     $3.50 (stock: 25)
```

---

## Verification

```bash
javac GenericRepository.java && java GenericRepository
```

## Summary

You've written generic classes, generic methods, bounded type parameters, wildcards with PECS, a generic stack, type inference with `var`, type tokens for reflection, and a generic repository. Generics are Java's most powerful compile-time safety mechanism — master them and you'll rarely see `ClassCastException`.

## Further Reading
- [Oracle Tutorial: Generics](https://docs.oracle.com/javase/tutorial/java/generics/index.html)
- [Effective Java — Chapter 5: Generics](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
