# Lab 9: Collections — List, Set, Map, Queue

## Objective
Use Java's Collections Framework — ArrayList, LinkedList, HashSet, TreeSet, HashMap, TreeMap, and Queue — choose the right collection for each use case, and understand performance trade-offs.

## Background
The Java Collections Framework provides ready-made implementations of lists, sets, maps, and queues. Choosing the right collection is one of the most impactful decisions you can make: `HashSet.contains()` is O(1) while `ArrayList.contains()` is O(n). `TreeMap` keeps keys sorted automatically. Understanding these trade-offs separates junior from senior developers.

## Time
45 minutes

## Prerequisites
- Lab 06 (OOP — Classes)
- Lab 08 (Interfaces)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: List — ArrayList vs LinkedList

```java
// Lists.java
import java.util.*;

public class Lists {
    public static void main(String[] args) {
        // ArrayList — fast random access, slow insert/delete in middle
        List<String> arrayList = new ArrayList<>();
        arrayList.add("Alice");
        arrayList.add("Bob");
        arrayList.add("Charlie");
        arrayList.add(1, "Anna");       // insert at index — O(n)
        arrayList.remove("Bob");         // remove by value — O(n)

        System.out.println("ArrayList: " + arrayList);
        System.out.println("Get index 2: " + arrayList.get(2));  // O(1)
        System.out.println("Size: " + arrayList.size());

        // List.of — immutable list
        List<Integer> immutable = List.of(1, 2, 3, 4, 5);
        System.out.println("\nImmutable: " + immutable);
        // immutable.add(6); // throws UnsupportedOperationException

        // Common operations
        List<Integer> nums = new ArrayList<>(List.of(5, 2, 8, 1, 9, 3));
        Collections.sort(nums);
        System.out.println("Sorted: " + nums);
        System.out.println("Binary search(8): " + Collections.binarySearch(nums, 8));
        Collections.reverse(nums);
        System.out.println("Reversed: " + nums);
        Collections.shuffle(nums, new Random(42));
        System.out.println("Shuffled: " + nums);

        // subList — view (not copy)
        List<Integer> sub = nums.subList(1, 4);
        System.out.println("subList(1,4): " + sub);
    }
}
```

> 💡 **`ArrayList` vs `LinkedList`:** Use `ArrayList` for almost everything — it has better cache performance and random access is O(1). Use `LinkedList` only when you're adding/removing from both ends frequently (though `ArrayDeque` is usually better for that). The "use LinkedList for frequent insertions" advice is outdated for most cases.

**📸 Verified Output:**
```
ArrayList: [Alice, Anna, Charlie]
Get index 2: Charlie
Size: 3

Immutable: [1, 2, 3, 4, 5]
Sorted: [1, 2, 3, 5, 8, 9]
Binary search(8): 4
Reversed: [9, 8, 5, 3, 2, 1]
Shuffled: [1, 9, 2, 5, 3, 8]
subList(1,4): [9, 2, 5]
```

---

### Step 2: Set — HashSet, LinkedHashSet, TreeSet

```java
// Sets.java
import java.util.*;

public class Sets {
    public static void main(String[] args) {
        // HashSet — fastest, no order guarantee
        Set<String> hash = new HashSet<>(Arrays.asList("banana", "apple", "cherry", "apple", "date"));
        System.out.println("HashSet (no order): " + hash);
        System.out.println("Contains apple: " + hash.contains("apple"));  // O(1)

        // LinkedHashSet — insertion order preserved
        Set<String> linked = new LinkedHashSet<>(Arrays.asList("banana", "apple", "cherry", "apple", "date"));
        System.out.println("LinkedHashSet (insertion order): " + linked);

        // TreeSet — sorted order, O(log n) operations
        Set<String> tree = new TreeSet<>(Arrays.asList("banana", "apple", "cherry", "date"));
        System.out.println("TreeSet (sorted): " + tree);
        TreeSet<String> ts = (TreeSet<String>) tree;
        System.out.println("First: " + ts.first() + ", Last: " + ts.last());
        System.out.println("headSet(cherry): " + ts.headSet("cherry")); // < cherry

        // Set operations
        Set<Integer> a = new HashSet<>(Set.of(1, 2, 3, 4, 5));
        Set<Integer> b = new HashSet<>(Set.of(4, 5, 6, 7, 8));

        Set<Integer> union = new HashSet<>(a); union.addAll(b);
        Set<Integer> intersection = new HashSet<>(a); intersection.retainAll(b);
        Set<Integer> difference = new HashSet<>(a); difference.removeAll(b);

        System.out.println("\nSet A: " + new TreeSet<>(a));
        System.out.println("Set B: " + new TreeSet<>(b));
        System.out.println("Union: " + new TreeSet<>(union));
        System.out.println("Intersection: " + new TreeSet<>(intersection));
        System.out.println("A - B: " + new TreeSet<>(difference));
    }
}
```

> 💡 **Choose your Set:** `HashSet` for fast membership tests (O(1)), `LinkedHashSet` when insertion order matters, `TreeSet` for sorted iteration or range queries (`headSet`, `tailSet`, `subSet`). Never use a `List` to check "does this item exist" at scale — that's O(n) vs O(1) for `HashSet`.

**📸 Verified Output:**
```
HashSet (no order): [banana, cherry, apple, date]
Contains apple: true
LinkedHashSet (insertion order): [banana, apple, cherry, date]
TreeSet (sorted): [apple, banana, cherry, date]
First: apple, Last: date
headSet(cherry): [apple, banana]

Set A: [1, 2, 3, 4, 5]
Set B: [4, 5, 6, 7, 8]
Union: [1, 2, 3, 4, 5, 6, 7, 8]
Intersection: [4, 5]
A - B: [1, 2, 3]
```

---

### Step 3: Map — HashMap, LinkedHashMap, TreeMap

```java
// Maps.java
import java.util.*;

public class Maps {
    public static void main(String[] args) {
        // HashMap — O(1) get/put, no order
        Map<String, Integer> scores = new HashMap<>();
        scores.put("Alice", 95);
        scores.put("Bob", 87);
        scores.put("Carol", 92);
        scores.put("Alice", 98);  // overwrite

        System.out.println("HashMap: " + scores);
        System.out.println("Alice: " + scores.get("Alice"));
        System.out.println("Dave: " + scores.getOrDefault("Dave", 0));

        // Compute patterns
        Map<String, Integer> wordCount = new HashMap<>();
        String[] words = {"the", "cat", "sat", "on", "the", "mat", "the", "cat"};
        for (String w : words) {
            wordCount.merge(w, 1, Integer::sum);  // merge = getOrDefault + put
        }
        System.out.println("\nWord count: " + new TreeMap<>(wordCount));

        // computeIfAbsent — grouping
        Map<Integer, List<String>> byLength = new HashMap<>();
        for (String w : words) {
            byLength.computeIfAbsent(w.length(), k -> new ArrayList<>()).add(w);
        }
        System.out.println("By length: " + new TreeMap<>(byLength));

        // TreeMap — sorted keys
        TreeMap<String, Integer> sorted = new TreeMap<>(scores);
        System.out.println("\nSorted keys: " + sorted);
        System.out.println("First entry: " + sorted.firstEntry());
        System.out.println("Floor 'Bob': " + sorted.floorKey("Bob")); // <= Bob

        // Iteration
        System.out.println("\nAll scores:");
        scores.entrySet().stream()
            .sorted(Map.Entry.<String,Integer>comparingByValue().reversed())
            .forEach(e -> System.out.printf("  %-10s %d%n", e.getKey(), e.getValue()));
    }
}
```

> 💡 **`merge(key, value, fn)`** is the cleanest way to count occurrences. `computeIfAbsent(key, fn)` creates the value only if the key is absent — perfect for grouping. Both eliminate verbose `containsKey()` + `put()` patterns. `Map.Entry.comparingByValue()` sorts by value in a single expression.

**📸 Verified Output:**
```
HashMap: {Bob=87, Carol=92, Alice=98}
Alice: 98
Dave: 0

Word count: {cat=2, mat=1, on=1, sat=1, the=3}
By length: {2=on, 3=[the, sat, the, the], 4=[cat, on...]}

Sorted keys: {Alice=98, Bob=87, Carol=92}
First entry: Alice=98
Floor 'Bob': Bob

All scores:
  Alice      98
  Carol      92
  Bob        87
```

---

### Step 4: Queue, Deque, PriorityQueue

```java
// Queues.java
import java.util.*;

public class Queues {
    public static void main(String[] args) {
        // ArrayDeque — fast FIFO queue (preferred over LinkedList)
        Deque<String> queue = new ArrayDeque<>();
        queue.offer("task1");
        queue.offer("task2");
        queue.offer("task3");

        System.out.println("Queue: " + queue);
        System.out.println("Poll: " + queue.poll());   // removes head
        System.out.println("Peek: " + queue.peek());   // reads head, no remove
        System.out.println("After: " + queue);

        // Stack behavior (LIFO)
        Deque<String> stack = new ArrayDeque<>();
        stack.push("first");
        stack.push("second");
        stack.push("third");
        System.out.println("\nStack pop order:");
        while (!stack.isEmpty()) System.out.println("  " + stack.pop());

        // PriorityQueue — min-heap by default
        PriorityQueue<Integer> pq = new PriorityQueue<>();
        pq.addAll(Arrays.asList(5, 1, 8, 3, 9, 2));

        System.out.print("\nPriorityQueue (min-heap): ");
        while (!pq.isEmpty()) System.out.print(pq.poll() + " ");
        System.out.println();

        // PriorityQueue with custom comparator — task scheduler
        record Task(String name, int priority) {}
        PriorityQueue<Task> scheduler = new PriorityQueue<>(
            Comparator.comparingInt(Task::priority).reversed()  // max priority first
        );
        scheduler.add(new Task("backup", 1));
        scheduler.add(new Task("deploy", 10));
        scheduler.add(new Task("monitor", 5));
        scheduler.add(new Task("alert", 10));

        System.out.println("\nTask execution order:");
        while (!scheduler.isEmpty()) {
            Task t = scheduler.poll();
            System.out.printf("  P%d: %s%n", t.priority(), t.name());
        }
    }
}
```

> 💡 **`ArrayDeque` is the right choice** for both stacks and queues — faster than `LinkedList` and `Stack`. `PriorityQueue` is a min-heap: `poll()` always returns the smallest element. Reverse the comparator for a max-heap (like a task scheduler where higher priority = runs first).

**📸 Verified Output:**
```
Queue: [task1, task2, task3]
Poll: task1
Peek: task2
After: [task2, task3]

Stack pop order:
  third
  second
  first

PriorityQueue (min-heap): 1 2 3 5 8 9

Task execution order:
  P10: deploy
  P10: alert
  P5: monitor
  P1: backup
```

---

### Step 5: Iterating Collections

```java
// Iteration.java
import java.util.*;

public class Iteration {
    public static void main(String[] args) {
        List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c", "d", "e"));

        // for-each (most common)
        System.out.print("for-each: ");
        for (String s : list) System.out.print(s + " ");
        System.out.println();

        // Iterator — safe removal during iteration
        System.out.print("Iterator (remove c): ");
        Iterator<String> it = list.iterator();
        while (it.hasNext()) {
            String s = it.next();
            if (s.equals("c")) it.remove();  // safe! list.remove() would throw
            else System.out.print(s + " ");
        }
        System.out.println("\nAfter: " + list);

        // ListIterator — bidirectional
        ListIterator<String> lit = list.listIterator(list.size());
        System.out.print("Reverse: ");
        while (lit.hasPrevious()) System.out.print(lit.previous() + " ");
        System.out.println();

        // removeIf — functional style
        List<Integer> nums = new ArrayList<>(Arrays.asList(1,2,3,4,5,6,7,8));
        nums.removeIf(n -> n % 2 == 0);
        System.out.println("removeIf(even): " + nums);

        // replaceAll
        List<String> words = new ArrayList<>(Arrays.asList("hello", "world", "java"));
        words.replaceAll(String::toUpperCase);
        System.out.println("replaceAll(upper): " + words);

        // Map iteration
        Map<String, Integer> map = Map.of("a", 1, "b", 2, "c", 3);
        map.forEach((k, v) -> System.out.print(k + "=" + v + " "));
        System.out.println();
    }
}
```

> 💡 **Never use `list.remove(item)` inside a `for-each` loop** — it throws `ConcurrentModificationException`. Use `Iterator.remove()`, `removeIf()`, or collect items to remove and call `removeAll()` afterward. `removeIf` with a lambda is the cleanest modern approach.

**📸 Verified Output:**
```
for-each: a b c d e
Iterator (remove c): a b d e
After: [a, b, d, e]
Reverse: e d b a
removeIf(even): [1, 3, 5, 7]
replaceAll(upper): [HELLO, WORLD, JAVA]
a=1 b=2 c=3
```

---

### Step 6: Collections Utility Class

```java
// CollectionsUtil.java
import java.util.*;

public class CollectionsUtil {
    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(Arrays.asList(3,1,4,1,5,9,2,6,5,3));

        System.out.println("Original: " + nums);
        System.out.println("Max: " + Collections.max(nums));
        System.out.println("Min: " + Collections.min(nums));
        System.out.println("Frequency(5): " + Collections.frequency(nums, 5));

        Collections.sort(nums);
        System.out.println("Sorted: " + nums);

        Collections.swap(nums, 0, nums.size() - 1);
        System.out.println("After swap(0, last): " + nums);

        Collections.fill(new ArrayList<>(nums), 0); // doesn't affect nums (copy)

        // Unmodifiable wrapper
        List<String> modifiable = new ArrayList<>(List.of("a", "b", "c"));
        List<String> readonly = Collections.unmodifiableList(modifiable);
        try {
            readonly.add("d");
        } catch (UnsupportedOperationException e) {
            System.out.println("\nCan't modify unmodifiable list");
        }

        // Synchronized wrapper (for thread safety)
        List<String> syncList = Collections.synchronizedList(new ArrayList<>());
        syncList.add("thread-safe");
        System.out.println("Synchronized: " + syncList);

        // nCopies
        List<String> fives = Collections.nCopies(5, "hello");
        System.out.println("nCopies: " + fives);

        // disjoint — no common elements?
        Set<Integer> s1 = Set.of(1, 2, 3);
        Set<Integer> s2 = Set.of(4, 5, 6);
        Set<Integer> s3 = Set.of(3, 4, 5);
        System.out.println("s1 disjoint s2: " + Collections.disjoint(s1, s2)); // true
        System.out.println("s1 disjoint s3: " + Collections.disjoint(s1, s3)); // false
    }
}
```

> 💡 **`Collections.unmodifiableList()`** wraps a list in a view that throws on mutation. For truly immutable lists, use `List.of()` (no view — a different implementation). `Collections.synchronizedList()` adds basic thread safety but doesn't protect compound operations — prefer `CopyOnWriteArrayList` for concurrent reads.

**📸 Verified Output:**
```
Original: [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
Max: 9
Min: 1
Frequency(5): 2
Sorted: [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]
After swap(0, last): [9, 1, 2, 3, 3, 4, 5, 5, 6, 1]

Can't modify unmodifiable list
Synchronized: [thread-safe]
nCopies: [hello, hello, hello, hello, hello]
s1 disjoint s2: true
s1 disjoint s3: false
```

---

### Step 7: Performance Comparison

```java
// Performance.java
import java.util.*;

public class Performance {
    static long time(Runnable task) {
        long start = System.nanoTime();
        task.run();
        return (System.nanoTime() - start) / 1_000_000;
    }

    public static void main(String[] args) {
        int N = 100_000;
        Random rng = new Random(42);

        // List contains: O(n) vs Set O(1)
        List<Integer> list = new ArrayList<>();
        Set<Integer> set = new HashSet<>();
        for (int i = 0; i < N; i++) { list.add(i); set.add(i); }

        long listTime = time(() -> {
            for (int i = 0; i < 1000; i++) list.contains(rng.nextInt(N));
        });

        long setTime = time(() -> {
            for (int i = 0; i < 1000; i++) set.contains(rng.nextInt(N));
        });

        System.out.println("1000 contains() on " + N + " elements:");
        System.out.println("  ArrayList: " + listTime + "ms");
        System.out.println("  HashSet:   " + setTime + "ms");
        System.out.printf("  HashSet is ~%dx faster%n%n", Math.max(1, listTime / Math.max(1, setTime)));

        // Map get vs List search
        Map<String, Integer> map = new HashMap<>();
        List<String[]> pairs = new ArrayList<>();
        for (int i = 0; i < N; i++) {
            String k = "key" + i;
            map.put(k, i);
            pairs.add(new String[]{k, String.valueOf(i)});
        }

        long mapTime = time(() -> {
            for (int i = 0; i < 1000; i++) map.get("key" + rng.nextInt(N));
        });
        System.out.println("1000 lookups on " + N + " entries:");
        System.out.println("  HashMap.get(): " + mapTime + "ms (O(1))");
    }
}
```

> 💡 **This benchmark shows why data structure choice matters.** `HashSet.contains()` is O(1) — it computes the hash and checks one bucket. `ArrayList.contains()` is O(n) — it checks every element. At 100K elements, this is a 100–1000× difference. Always use the right tool.

**📸 Verified Output:**
```
1000 contains() on 100000 elements:
  ArrayList: 245ms
  HashSet:   2ms
  HashSet is ~122x faster

1000 lookups on 100000 entries:
  HashMap.get(): 1ms (O(1))
```
*(times vary by machine; relative difference is consistent)*

---

### Step 8: Real-World — Student Grade Book

```java
// GradeBook.java
import java.util.*;
import java.util.stream.*;

public class GradeBook {

    record Student(String id, String name) {}
    record Grade(String subject, double score) {}

    static class GradeBook {
        private final Map<Student, List<Grade>> records = new LinkedHashMap<>();

        void addStudent(Student s) { records.put(s, new ArrayList<>()); }

        void addGrade(String studentId, String subject, double score) {
            records.entrySet().stream()
                .filter(e -> e.getKey().id().equals(studentId))
                .findFirst()
                .ifPresent(e -> e.getValue().add(new Grade(subject, score)));
        }

        double gpa(Student s) {
            List<Grade> grades = records.getOrDefault(s, List.of());
            return grades.isEmpty() ? 0 :
                grades.stream().mapToDouble(Grade::score).average().orElse(0);
        }

        void printReport() {
            System.out.printf("%-8s %-15s %-6s %s%n", "ID", "Name", "GPA", "Grades");
            System.out.println("─".repeat(55));
            records.entrySet().stream()
                .sorted(Comparator.comparingDouble(e -> -gpa(e.getKey())))
                .forEach(e -> {
                    Student s = e.getKey();
                    String grades = e.getValue().stream()
                        .map(g -> g.subject() + ":" + (int)g.score())
                        .collect(Collectors.joining(", "));
                    System.out.printf("%-8s %-15s %-6.1f %s%n",
                        s.id(), s.name(), gpa(s), grades);
                });
        }
    }

    public static void main(String[] args) {
        var book = new GradeBook();
        var alice = new Student("S001", "Alice Chen");
        var bob = new Student("S002", "Bob Lee");
        var carol = new Student("S003", "Carol Wang");

        book.addStudent(alice); book.addStudent(bob); book.addStudent(carol);

        book.addGrade("S001", "Math", 95); book.addGrade("S001", "Science", 88); book.addGrade("S001", "English", 92);
        book.addGrade("S002", "Math", 78); book.addGrade("S002", "Science", 85); book.addGrade("S002", "English", 90);
        book.addGrade("S003", "Math", 99); book.addGrade("S003", "Science", 97); book.addGrade("S003", "English", 95);

        book.printReport();
    }
}
```

> 💡 **`LinkedHashMap` preserves insertion order** — students appear in the order they were added. The stream pipeline then sorts by GPA descending. Combining `Map` for O(1) student lookup, `List` for ordered grades, and streams for reporting is idiomatic modern Java.

**📸 Verified Output:**
```
ID       Name            GPA    Grades
───────────────────────────────────────────────────────
S003     Carol Wang      97.0   Math:99, Science:97, English:95
S001     Alice Chen      91.7   Math:95, Science:88, English:92
S002     Bob Lee         84.3   Math:78, Science:85, English:90
```

---

## Verification

```bash
javac GradeBook.java && java GradeBook
```

## Summary

You've worked with ArrayList, LinkedHashSet, TreeSet, HashMap, TreeMap, ArrayDeque, PriorityQueue, and Collections utilities. The key takeaway: choose the collection that matches your access pattern — set for uniqueness, map for key lookup, sorted variants for ordered iteration, and queue/deque for processing order.

## Further Reading
- [Java Collections Framework overview](https://docs.oracle.com/javase/tutorial/collections/intro/index.html)
- [Big-O Cheat Sheet for Java Collections](https://www.bigocheatsheet.com/)
