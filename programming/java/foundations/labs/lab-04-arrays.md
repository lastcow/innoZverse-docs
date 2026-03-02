# Lab 4: Arrays & Multi-Dimensional Arrays

## Objective
Declare, initialize, and manipulate single and multi-dimensional arrays in Java, use `Arrays` utility methods, and understand the difference between arrays and references.

## Background
Arrays are Java's fundamental data structure — a fixed-size, ordered collection of elements of the same type. Unlike JavaScript arrays, Java arrays have a fixed length set at creation time. Understanding arrays is prerequisite to collections, matrices, and algorithm implementation.

## Time
35 minutes

## Prerequisites
- Lab 02 (Variables & Primitives)
- Lab 03 (Strings)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Declaring and Initializing Arrays

```java
// ArrayBasics.java
import java.util.Arrays;

public class ArrayBasics {
    public static void main(String[] args) {
        // Declaration and allocation
        int[] scores = new int[5];        // default: all zeros
        String[] names = new String[3];   // default: all null

        // Initialize with values
        scores[0] = 95; scores[1] = 87; scores[2] = 92;
        scores[3] = 78; scores[4] = 88;

        // Initializer shorthand
        double[] prices = {19.99, 5.49, 12.00, 8.75};
        String[] colors = {"red", "green", "blue"};

        System.out.println("Length: " + scores.length);
        System.out.println("scores[2]: " + scores[2]);
        System.out.println("Arrays.toString: " + Arrays.toString(scores));
        System.out.println("Prices: " + Arrays.toString(prices));
    }
}
```

> 💡 **Arrays in Java are objects** — `scores.length` (no parentheses) is a field, not a method. Array indices are zero-based. Accessing out-of-bounds throws `ArrayIndexOutOfBoundsException`.

**📸 Verified Output:**
```
Length: 5
scores[2]: 92
Arrays.toString: [95, 87, 92, 78, 88]
Prices: [19.99, 5.49, 12.0, 8.75]
```

---

### Step 2: Iterating Arrays

```java
// ArrayIteration.java
import java.util.Arrays;

public class ArrayIteration {
    public static void main(String[] args) {
        int[] nums = {3, 7, 1, 9, 4, 6, 2, 8, 5};

        // Traditional for loop
        int sum = 0;
        for (int i = 0; i < nums.length; i++) {
            sum += nums[i];
        }
        System.out.println("Sum: " + sum);

        // Enhanced for-each (read-only)
        int max = nums[0];
        for (int n : nums) {
            if (n > max) max = n;
        }
        System.out.println("Max: " + max);

        // Sort and binary search
        int[] sorted = nums.clone();
        Arrays.sort(sorted);
        System.out.println("Sorted: " + Arrays.toString(sorted));

        int idx = Arrays.binarySearch(sorted, 7);
        System.out.println("Index of 7: " + idx);

        // Fill
        int[] zeros = new int[5];
        Arrays.fill(zeros, 42);
        System.out.println("Filled: " + Arrays.toString(zeros));
    }
}
```

> 💡 **`Arrays.binarySearch` requires a sorted array.** Always sort first. It returns the index if found, or a negative value if not. Use `Arrays.sort()` which uses dual-pivot quicksort — O(n log n).

**📸 Verified Output:**
```
Sum: 45
Max: 9
Sorted: [1, 2, 3, 4, 5, 6, 7, 8, 9]
Index of 7: 6
Filled: [42, 42, 42, 42, 42]
```

---

### Step 3: Array Copying

```java
// ArrayCopy.java
import java.util.Arrays;

public class ArrayCopy {
    public static void main(String[] args) {
        int[] original = {1, 2, 3, 4, 5};

        // Reference copy (WRONG way — both point to same array)
        int[] ref = original;
        ref[0] = 99;
        System.out.println("After ref change, original[0]: " + original[0]); // 99!

        // Proper copy methods
        int[] fresh = {1, 2, 3, 4, 5};

        // clone()
        int[] cloned = fresh.clone();
        cloned[0] = 99;
        System.out.println("After clone change, fresh[0]: " + fresh[0]); // 1 (unchanged)

        // Arrays.copyOf — can change size
        int[] bigger = Arrays.copyOf(fresh, 8);  // pads with 0
        System.out.println("Bigger: " + Arrays.toString(bigger));

        // Arrays.copyOfRange — slice
        int[] slice = Arrays.copyOfRange(fresh, 1, 4);  // [1..3]
        System.out.println("Slice [1,4): " + Arrays.toString(slice));

        // System.arraycopy — fastest bulk copy
        int[] dest = new int[5];
        System.arraycopy(fresh, 1, dest, 0, 3); // src, srcPos, dst, dstPos, len
        System.out.println("arraycopy: " + Arrays.toString(dest));
    }
}
```

> 💡 **Arrays are reference types** — assigning an array variable copies the reference, not the data. `int[] b = a` means both variables point to the same memory. Always use `.clone()`, `Arrays.copyOf()`, or `System.arraycopy()` for true copies.

**📸 Verified Output:**
```
After ref change, original[0]: 99
After clone change, fresh[0]: 1
Bigger: [1, 2, 3, 4, 5, 0, 0, 0]
Slice [1,4): [2, 3, 4]
arraycopy: [2, 3, 4, 0, 0]
```

---

### Step 4: 2D Arrays — Matrices

```java
// Matrix.java
import java.util.Arrays;

public class Matrix {
    public static void main(String[] args) {
        // 3x3 matrix
        int[][] matrix = {
            {1, 2, 3},
            {4, 5, 6},
            {7, 8, 9}
        };

        // Access: matrix[row][col]
        System.out.println("Center: " + matrix[1][1]);
        System.out.println("Rows: " + matrix.length);
        System.out.println("Cols: " + matrix[0].length);

        // Print matrix
        System.out.println("\nMatrix:");
        for (int[] row : matrix) {
            for (int val : row) {
                System.out.printf("%4d", val);
            }
            System.out.println();
        }

        // Matrix transpose
        int rows = matrix.length, cols = matrix[0].length;
        int[][] transposed = new int[cols][rows];
        for (int r = 0; r < rows; r++)
            for (int c = 0; c < cols; c++)
                transposed[c][r] = matrix[r][c];

        System.out.println("\nTransposed:");
        for (int[] row : transposed) System.out.println(Arrays.toString(row));

        // Jagged array (rows of different lengths)
        int[][] triangle = new int[4][];
        for (int i = 0; i < 4; i++) {
            triangle[i] = new int[i + 1];
            Arrays.fill(triangle[i], i + 1);
        }
        System.out.println("\nJagged:");
        for (int[] row : triangle) System.out.println(Arrays.toString(row));
    }
}
```

> 💡 **Java 2D arrays are arrays of arrays** — `int[][]` is literally an `int[]` whose elements are `int[]` objects. This allows jagged arrays (rows of different lengths), which are common in triangle problems, Pascal's triangle, and adjacency lists.

**📸 Verified Output:**
```
Center: 5
Rows: 3
Cols: 3

Matrix:
   1   2   3
   4   5   6
   7   8   9

Transposed:
[1, 4, 7]
[2, 5, 8]
[3, 6, 9]

Jagged:
[1]
[2, 2]
[3, 3, 3]
[4, 4, 4, 4]
```

---

### Step 5: Common Array Algorithms

```java
// ArrayAlgorithms.java
import java.util.Arrays;

public class ArrayAlgorithms {

    static int[] twoSum(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++)
            for (int j = i + 1; j < nums.length; j++)
                if (nums[i] + nums[j] == target)
                    return new int[]{i, j};
        return new int[]{};
    }

    static void rotate(int[] arr, int k) {
        int n = arr.length;
        k = k % n;
        reverse(arr, 0, n - 1);
        reverse(arr, 0, k - 1);
        reverse(arr, k, n - 1);
    }

    static void reverse(int[] arr, int l, int r) {
        while (l < r) { int t = arr[l]; arr[l++] = arr[r]; arr[r--] = t; }
    }

    static int[] runningSum(int[] nums) {
        int[] result = new int[nums.length];
        result[0] = nums[0];
        for (int i = 1; i < nums.length; i++)
            result[i] = result[i - 1] + nums[i];
        return result;
    }

    public static void main(String[] args) {
        // Two Sum
        int[] nums = {2, 7, 11, 15};
        System.out.println("twoSum([2,7,11,15], 9): " + Arrays.toString(twoSum(nums, 9)));

        // Rotate
        int[] arr = {1, 2, 3, 4, 5};
        rotate(arr, 2);
        System.out.println("rotate by 2: " + Arrays.toString(arr));

        // Running sum
        int[] data = {3, 1, 2, 10, 1};
        System.out.println("runningSum: " + Arrays.toString(runningSum(data)));
    }
}
```

> 💡 **The rotate trick** (reverse all, reverse first k, reverse rest) runs in O(n) time and O(1) space — no extra array needed. This pattern — reversing sub-arrays to achieve rotation — is a classic interview technique worth memorizing.

**📸 Verified Output:**
```
twoSum([2,7,11,15], 9): [0, 1]
rotate by 2: [4, 5, 1, 2, 3]
runningSum: [3, 4, 6, 16, 17]
```

---

### Step 6: Arrays as Method Parameters & varargs

```java
// ArrayMethods.java
import java.util.Arrays;

public class ArrayMethods {

    // Arrays are passed by reference
    static void doubleAll(int[] arr) {
        for (int i = 0; i < arr.length; i++) arr[i] *= 2;
    }

    // Varargs — accepts 0 or more ints
    static int sum(int... numbers) {
        int total = 0;
        for (int n : numbers) total += n;
        return total;
    }

    // Return new array (functional style)
    static int[] doubled(int[] arr) {
        int[] result = new int[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = arr[i] * 2;
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 4, 5};

        // Mutation via reference
        doubleAll(nums);
        System.out.println("After doubleAll: " + Arrays.toString(nums));

        // Varargs
        System.out.println("sum(): " + sum());
        System.out.println("sum(1,2,3): " + sum(1, 2, 3));
        System.out.println("sum(array): " + sum(nums)); // pass array to varargs

        // Functional style
        int[] original = {1, 2, 3};
        int[] result = doubled(original);
        System.out.println("original: " + Arrays.toString(original)); // unchanged
        System.out.println("doubled: " + Arrays.toString(result));
    }
}
```

> 💡 **Varargs `int... numbers`** is syntactic sugar for `int[] numbers` — Java creates the array automatically. Under the hood `sum(1, 2, 3)` becomes `sum(new int[]{1, 2, 3})`. You can pass an explicit array too. Varargs must be the last parameter.

**📸 Verified Output:**
```
After doubleAll: [2, 4, 6, 8, 10]
sum(): 0
sum(1,2,3): 6
sum(array): 30
original: [1, 2, 3]
doubled: [2, 4, 6]
```

---

### Step 7: Sorting with Comparators

```java
// ArraySorting.java
import java.util.Arrays;
import java.util.Comparator;

public class ArraySorting {
    record Student(String name, int grade, double gpa) {}

    public static void main(String[] args) {
        // Primitive sort (natural order)
        int[] nums = {5, 2, 8, 1, 9, 3};
        Arrays.sort(nums);
        System.out.println("Sorted ints: " + Arrays.toString(nums));

        // Object sort with Comparator
        Student[] students = {
            new Student("Alice", 12, 3.9),
            new Student("Bob", 11, 3.5),
            new Student("Carol", 12, 3.7),
            new Student("Dave", 11, 3.8),
        };

        // Sort by GPA descending
        Arrays.sort(students, (a, b) -> Double.compare(b.gpa(), a.gpa()));
        System.out.println("\nBy GPA desc:");
        for (Student s : students) System.out.printf("  %s: %.1f%n", s.name(), s.gpa());

        // Sort by grade then name
        Arrays.sort(students, Comparator.comparingInt(Student::grade)
                                        .thenComparing(Student::name));
        System.out.println("\nBy grade then name:");
        for (Student s : students) System.out.printf("  Grade %d: %s%n", s.grade(), s.name());
    }
}
```

> 💡 **`Comparator.comparing` chains** (`thenComparing`) make multi-key sorts readable. The `record` type (Java 16+) auto-generates constructor, accessors, `equals`, `hashCode`, and `toString` — perfect for data carriers.

**📸 Verified Output:**
```
Sorted ints: [1, 2, 3, 5, 8, 9]

By GPA desc:
  Alice: 3.9
  Dave: 3.8
  Carol: 3.7
  Bob: 3.5

By grade then name:
  Grade 11: Bob
  Grade 11: Dave
  Grade 12: Alice
  Grade 12: Carol
```

---

### Step 8: Array Utilities Wrap-up

```java
// ArrayUtils.java
import java.util.Arrays;

public class ArrayUtils {
    public static void main(String[] args) {
        // equals vs deepEquals
        int[] a = {1, 2, 3};
        int[] b = {1, 2, 3};
        System.out.println("Arrays.equals: " + Arrays.equals(a, b));   // true
        System.out.println("a == b: " + (a == b));                       // false

        int[][] m1 = {{1,2},{3,4}};
        int[][] m2 = {{1,2},{3,4}};
        System.out.println("deepEquals: " + Arrays.deepEquals(m1, m2));  // true

        // Stream from array
        int[] nums = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
        int sumEvens = Arrays.stream(nums)
            .filter(n -> n % 2 == 0)
            .sum();
        System.out.println("\nSum of evens: " + sumEvens);

        double avg = Arrays.stream(nums).average().orElse(0);
        System.out.printf("Average: %.1f%n", avg);

        // Convert to String[] and back
        String[] words = {"banana", "apple", "cherry", "date"};
        Arrays.sort(words);
        System.out.println("\nSorted words: " + Arrays.toString(words));

        // Parallel sort (for large arrays)
        int[] big = new int[1_000_000];
        Arrays.fill(big, 1);
        big[0] = 999_999;
        Arrays.parallelSort(big);
        System.out.println("parallelSort first: " + big[0]);
        System.out.println("parallelSort last: " + big[big.length - 1]);
    }
}
```

> 💡 **`Arrays.stream(arr)`** bridges arrays and the Streams API, giving you `filter`, `map`, `reduce`, `sum`, `average`, and more. `Arrays.parallelSort()` uses multiple CPU cores for large arrays — measurably faster than `Arrays.sort()` above ~10,000 elements.

**📸 Verified Output:**
```
Arrays.equals: true
a == b: false
deepEquals: true

Sum of evens: 30
Average: 5.5

Sorted words: [apple, banana, cherry, date]
parallelSort first: 1
parallelSort last: 999999
```

---

## Verification

```bash
javac ArrayUtils.java && java ArrayUtils
```

Expected: All outputs match verified output above.

## Summary

Arrays are Java's foundation for data storage. You've covered declaration, initialization, iteration, copying (reference vs value), 2D/jagged arrays, sorting with comparators, varargs, and bridging to Streams. Next stop: Collections, which solve the fixed-size limitation.

## Further Reading
- [Java Arrays docs](https://docs.oracle.com/en/java/docs/api/java.base/java/util/Arrays.html)
- [Oracle Java Tutorial: Arrays](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/arrays.html)
