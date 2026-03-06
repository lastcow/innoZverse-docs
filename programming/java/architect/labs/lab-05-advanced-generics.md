# Lab 05: Advanced Generics

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Go beyond basic `List<T>` usage. Master PECS (Producer Extends, Consumer Super), defeat type erasure with the TypeToken pattern, apply recursive generic bounds, and combine sealed interfaces with generics for algebraic data types.

---

## Step 1: PECS — Producer Extends, Consumer Super

The golden rule: **"PECS" — Producer Extends, Consumer Super**

```
? extends T  →  you can READ from it  (it PRODUCES T)
? super T    →  you can WRITE to it   (it CONSUMES T)
```

```java
import java.util.*;

public class PECSDemo {
    // PRODUCER: ? extends Number → reads numbers from the list
    static double sum(List<? extends Number> producer) {
        double total = 0;
        for (Number n : producer) total += n.doubleValue();
        return total;
    }

    // CONSUMER: ? super Integer → writes integers into the list
    static void fill(List<? super Integer> consumer, int count) {
        for (int i = 1; i <= count; i++) consumer.add(i);
    }

    // BOTH: transform producer → consumer
    static <T extends Number> void copy(List<? extends T> src, List<? super T> dst) {
        for (T item : src) dst.add(item);
    }

    public static void main(String[] args) {
        // Producer: can read from List<Integer> or List<Double>
        List<Integer> ints = Arrays.asList(1, 2, 3, 4, 5);
        List<Double> doubles = Arrays.asList(1.5, 2.5, 3.5);
        System.out.println("Sum of ints:    " + sum(ints));    // 15.0
        System.out.println("Sum of doubles: " + sum(doubles)); // 7.5

        // Consumer: can write to List<Number> or List<Object>
        List<Number> nums = new ArrayList<>();
        fill(nums, 3); // writes 1, 2, 3
        System.out.println("Consumer added: " + nums);

        // Copy: Integer producer → Number consumer
        List<Number> dest = new ArrayList<>();
        copy(ints, dest);
        System.out.println("Copied: " + dest);
    }
}
```

> 💡 `Collections.copy(dst, src)` uses exactly this pattern: `copy(List<? super T> dest, List<? extends T> src)`

---

## Step 2: Type Erasure and Heap Pollution

```java
import java.lang.reflect.*;
import java.util.*;

public class TypeErasureDemo {
    public static void main(String[] args) throws Exception {
        // At runtime, List<Integer> == List<String> after erasure
        List<Integer> ints = new ArrayList<>();
        List<String> strs = new ArrayList<>();
        System.out.println("Same class: " + (ints.getClass() == strs.getClass())); // true!
        System.out.println("Class name: " + ints.getClass().getName()); // java.util.ArrayList

        // Heap pollution: @SuppressWarnings("unchecked") bypasses generics
        List rawList = new ArrayList<String>();
        rawList.add("hello");
        rawList.add(42); // compiles! No generic check on raw type
        // List<String> polluted = rawList; // ClassCastException at runtime

        // Reifiable types vs non-reifiable
        // int[].class — reifiable
        // String[].class — reifiable
        // List<String>[].class — NOT allowed (non-reifiable, erased to List[])
        System.out.println("int[] is reifiable: " + (int[].class.isArray()));

        // Generic array creation (forbidden, requires @SuppressWarnings)
        // List<String>[] arr = new List<String>[10]; // COMPILE ERROR
        @SuppressWarnings("unchecked")
        List<String>[] arr = new List[10]; // raw type workaround
        arr[0] = new ArrayList<>();
        arr[0].add("safe with raw array");
        System.out.println("Generic array workaround: " + arr[0].get(0));
    }
}
```

---

## Step 3: TypeToken Pattern — Capturing Generic Types at Runtime

```java
import java.lang.reflect.*;
import java.util.*;

public class TypeTokenDemo {
    // TypeToken captures the generic type via anonymous subclass
    public static abstract class TypeToken<T> {
        public final Type type;
        
        protected TypeToken() {
            // getGenericSuperclass() returns ParameterizedType for anonymous subclass
            Type superClass = getClass().getGenericSuperclass();
            if (superClass instanceof ParameterizedType pt) {
                this.type = pt.getActualTypeArguments()[0];
            } else {
                throw new IllegalArgumentException("Missing type parameter");
            }
        }
        
        @SuppressWarnings("unchecked")
        public Class<T> getRawType() {
            if (type instanceof ParameterizedType pt) return (Class<T>) pt.getRawType();
            return (Class<T>) type;
        }
        
        @Override public String toString() { return type.getTypeName(); }
    }
    
    // Usage: inject type-safe container
    static class TypeSafeCache {
        private final Map<TypeToken<?>, Object> cache = new HashMap<>();
        
        @SuppressWarnings("unchecked")
        public <T> T get(TypeToken<T> token) {
            return (T) cache.get(token);
        }
        
        public <T> void put(TypeToken<T> token, T value) {
            cache.put(token, value);
        }
    }
    
    public static void main(String[] args) {
        // Capture complex generic types at runtime
        var listInt = new TypeToken<List<Integer>>() {};
        var mapStrList = new TypeToken<Map<String, List<Integer>>>() {};
        var simpleStr = new TypeToken<String>() {};
        
        System.out.println("TypeToken captured: " + listInt);
        System.out.println("TypeToken captured: " + mapStrList);
        System.out.println("Raw type of List<Integer>: " + listInt.getRawType().getSimpleName());
        
        // Gson and Jackson use this pattern
        // new TypeToken<List<MyDto>>() {}.getType() → used for deserializing JSON
    }
}
```

---

## Step 4: Recursive Generic Bounds

```java
import java.util.*;

public class RecursiveGenericsDemo {
    // T must be comparable to itself
    static <T extends Comparable<T>> T max(List<T> list) {
        return list.stream().max(Comparator.naturalOrder()).orElseThrow();
    }
    
    // Builder pattern: fluent API preserves subtype
    static abstract class Builder<B extends Builder<B>> {
        String name;
        
        @SuppressWarnings("unchecked")
        public B name(String name) { this.name = name; return (B) this; }
        
        abstract Object build();
    }
    
    static class PersonBuilder extends Builder<PersonBuilder> {
        int age;
        
        public PersonBuilder age(int age) { this.age = age; return this; }
        
        @Override public String build() { return "Person{name=" + name + ", age=" + age + "}"; }
    }
    
    // Enum-like self-referential pattern
    interface Comparable2<T extends Comparable2<T>> {
        int compareTo2(T other);
        default boolean isLessThan(T other) { return compareTo2(other) < 0; }
    }
    
    public static void main(String[] args) {
        System.out.println("Max of [3,1,4,1,5,9]: " + max(Arrays.asList(3,1,4,1,5,9)));
        System.out.println("Max of [apple,banana,cherry]: " + max(Arrays.asList("apple","banana","cherry")));
        
        // Fluent builder — method chaining preserves PersonBuilder type
        String person = new PersonBuilder().name("Alice").age(30).build();
        System.out.println("Builder: " + person);
    }
}
```

---

## Step 5: Sealed Interfaces + Generics (Java 17+)

```java
// Algebraic data types — sealed interface + generics
public class SealedGenericsDemo {
    // Result<T> — Either Success or Failure
    sealed interface Result<T> permits Result.Success, Result.Failure {
        record Success<T>(T value) implements Result<T> {}
        record Failure<T>(String error) implements Result<T> {}
        
        default boolean isSuccess() { return this instanceof Success<T>; }
        
        @SuppressWarnings("unchecked")
        default T getOrElse(T defaultValue) {
            return switch (this) {
                case Success<T> s -> s.value();
                case Failure<T> f -> defaultValue;
            };
        }
        
        default <U> Result<U> map(java.util.function.Function<T, U> mapper) {
            return switch (this) {
                case Success<T> s -> new Success<>(mapper.apply(s.value()));
                case Failure<T> f -> new Failure<>(f.error());
            };
        }
    }
    
    static Result<Integer> parseInt(String s) {
        try { return new Result.Success<>(Integer.parseInt(s)); }
        catch (NumberFormatException e) { return new Result.Failure<>("Not a number: " + s); }
    }
    
    public static void main(String[] args) {
        var r1 = parseInt("42");
        var r2 = parseInt("abc");
        
        System.out.println("parseInt('42'):  " + r1.getOrElse(-1));  // 42
        System.out.println("parseInt('abc'): " + r2.getOrElse(-1));  // -1
        System.out.println("Map *2: " + r1.map(x -> x * 2).getOrElse(-1)); // 84
        
        // Pattern match exhaustive
        String msg = switch (r2) {
            case Result.Success<Integer> s -> "Got: " + s.value();
            case Result.Failure<Integer> f -> "Error: " + f.error();
        };
        System.out.println(msg);
    }
}
```

---

## Step 6: Wildcard Capture Pattern

```java
import java.util.*;

public class WildcardCaptureDemo {
    // Wildcard capture: name the wildcard for later use
    static <T> void swap(List<T> list, int i, int j) {
        T temp = list.get(i);
        list.set(i, list.get(j));
        list.set(j, temp);
    }
    
    // Helper method for wildcard capture
    static void swapWildcard(List<?> list, int i, int j) {
        swapHelper(list, i, j);
    }
    
    private static <T> void swapHelper(List<T> list, int i, int j) {
        T temp = list.get(i);
        list.set(i, list.get(j));
        list.set(j, temp);
    }
    
    // Bounded wildcards in method signatures
    static <T extends Comparable<? super T>> void sort(List<T> list) {
        Collections.sort(list); // T comparable to T or supertypes
    }
    
    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(Arrays.asList(3, 1, 4, 1, 5));
        swapWildcard(nums, 0, 4);
        System.out.println("After swap: " + nums);
        sort(nums);
        System.out.println("After sort: " + nums);
    }
}
```

---

## Step 7: Generic Methods and Type Inference

```java
import java.util.*;
import java.util.function.*;

public class TypeInferenceDemo {
    // Generic factory
    static <T> List<T> listOf(T... items) {
        return new ArrayList<>(Arrays.asList(items));
    }
    
    // Return type inference
    static <T> Optional<T> firstMatch(List<T> list, Predicate<T> pred) {
        return list.stream().filter(pred).findFirst();
    }
    
    // Multi-bound generics
    static <T extends Comparable<T> & java.io.Serializable> T clampedMax(List<T> list, T max) {
        T m = list.stream().max(Comparator.naturalOrder()).orElseThrow();
        return m.compareTo(max) > 0 ? max : m;
    }
    
    public static void main(String[] args) {
        var strings = listOf("a", "b", "c"); // type inferred as List<String>
        var numbers = listOf(1, 2, 3, 4, 5); // List<Integer>
        
        System.out.println("listOf: " + strings);
        System.out.println("firstMatch > 3: " + firstMatch(numbers, n -> n > 3));
        System.out.println("clampedMax([1..5], 3): " + clampedMax(numbers, 3));
        
        // Diamond operator <> — empty: always use!
        Map<String, List<Integer>> m = new HashMap<>(); // not Map<String, List<Integer>> m = new HashMap<String, List<Integer>>();
        System.out.println("Diamond operator: " + m.getClass().getSimpleName());
    }
}
```

---

## Step 8: Capstone — TypeToken + PECS Demo

```java
import java.lang.reflect.*;
import java.util.*;

public class Main {
    static abstract class TypeToken<T> {
        final Type type;
        TypeToken() { type = ((ParameterizedType)getClass().getGenericSuperclass()).getActualTypeArguments()[0]; }
        @Override public String toString() { return type.getTypeName(); }
    }

    static double sumList(List<? extends Number> list) {
        return list.stream().mapToDouble(Number::doubleValue).sum();
    }

    static void addNumbers(List<? super Integer> list, int count) {
        for (int i = 1; i <= count; i++) list.add(i);
    }

    static <T extends Comparable<T>> T max(List<T> list) {
        return list.stream().max(Comparator.naturalOrder()).orElseThrow();
    }

    public static void main(String[] args) {
        var token = new TypeToken<List<Map<String, Integer>>>(){};
        System.out.println("TypeToken captured: " + token);

        List<Integer> ints = Arrays.asList(1, 2, 3, 4, 5);
        List<Double> doubles = Arrays.asList(1.5, 2.5, 3.5);
        System.out.println("Sum of ints: " + sumList(ints));
        System.out.println("Sum of doubles: " + sumList(doubles));

        List<Number> nums = new ArrayList<>();
        addNumbers(nums, 3);
        System.out.println("Consumer added: " + nums);

        System.out.println("Max of [3,1,4,1,5,9]: " + max(Arrays.asList(3,1,4,1,5,9)));
        System.out.println("Max of [apple,banana,cherry]: " + max(Arrays.asList("apple","banana","cherry")));
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
TypeToken captured: java.util.List<java.util.Map<java.lang.String, java.lang.Integer>>
Sum of ints: 15.0
Sum of doubles: 7.5
Consumer added: [1, 2, 3]
Max of [3,1,4,1,5,9]: 9
Max of [apple,banana,cherry]: cherry
```

---

## Summary

| Concept | Syntax | Key Rule |
|---|---|---|
| Producer Extends | `List<? extends T>` | Read only, no writes |
| Consumer Super | `List<? super T>` | Write only (reads `Object`) |
| Type erasure | `List<T>` → `List` | Runtime has no type info |
| TypeToken | `new TypeToken<T>(){}` | Capture type via subclass |
| Recursive bound | `T extends Comparable<T>` | Self-referential constraints |
| Wildcard capture | helper method pattern | Named wildcard for set |
| Sealed + generics | `sealed interface Result<T>` | Algebraic data types |
| Multi-bound | `T extends A & B` | Multiple type constraints |
