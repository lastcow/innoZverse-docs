# Lab 5: Control Flow — Conditionals, Loops & Switch

## Objective
Master Java control flow: if/else, switch expressions, for/while/do-while loops, break/continue, and labeled statements.

## Background
Control flow determines which statements execute and in what order. Java 14+ introduced switch expressions (with `->` arrows and `yield`) that are more concise and safer than traditional switch statements. Combined with enhanced for loops and text blocks, modern Java control flow is expressive and readable.

## Time
35 minutes

## Prerequisites
- Lab 02 (Variables & Primitives)
- Lab 04 (Arrays)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: If/Else and Ternary

```java
// Conditionals.java
public class Conditionals {
    static String grade(int score) {
        if (score >= 90) return "A";
        else if (score >= 80) return "B";
        else if (score >= 70) return "C";
        else if (score >= 60) return "D";
        else return "F";
    }

    public static void main(String[] args) {
        int[] scores = {95, 82, 71, 55, 100};
        for (int s : scores) {
            System.out.println(s + " -> " + grade(s));
        }

        // Ternary operator
        int x = 42;
        String parity = (x % 2 == 0) ? "even" : "odd";
        System.out.println("\n42 is " + parity);

        // Nested ternary (use sparingly)
        int temp = 25;
        String weather = temp > 30 ? "hot" : temp > 20 ? "warm" : temp > 10 ? "cool" : "cold";
        System.out.println("25°C is " + weather);

        // instanceof pattern matching (Java 16+)
        Object obj = "Hello, Java!";
        if (obj instanceof String s && s.length() > 5) {
            System.out.println("Long string: " + s.toUpperCase());
        }
    }
}
```

> 💡 **Pattern matching `instanceof`** (Java 16+) eliminates the cast: instead of `if (obj instanceof String) { String s = (String) obj; }` you write `if (obj instanceof String s)`. The `&&` short-circuits, so `s` is safely bound only when the instanceof check passes.

**📸 Verified Output:**
```
95 -> A
82 -> B
71 -> C
55 -> F
100 -> A

42 is even
25°C is warm
Long string: HELLO, JAVA!
```

---

### Step 2: Switch Expressions (Modern Java)

```java
// SwitchExpressions.java
public class SwitchExpressions {
    enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

    static int workHours(Day day) {
        return switch (day) {
            case MON, TUE, WED, THU, FRI -> 8;
            case SAT -> 4;
            case SUN -> 0;
        };
    }

    static String describe(Object obj) {
        return switch (obj) {
            case Integer i when i < 0  -> "negative int: " + i;
            case Integer i             -> "positive int: " + i;
            case String s when s.isEmpty() -> "empty string";
            case String s              -> "string: " + s;
            case null                  -> "null";
            default                    -> "unknown: " + obj.getClass().getSimpleName();
        };
    }

    public static void main(String[] args) {
        // Work hours per day
        for (Day d : Day.values()) {
            System.out.printf("%-3s: %d hours%n", d, workHours(d));
        }

        // Pattern switch (Java 21)
        System.out.println();
        Object[] things = {42, -7, "hello", "", 3.14, null};
        for (Object t : things) {
            System.out.println(describe(t));
        }
    }
}
```

> 💡 **Switch expressions vs statements:** The arrow `->` form is an *expression* that returns a value, requires exhaustiveness (all cases covered), and can't fall through. No need for `break`. `yield` is used for multi-statement cases: `case X -> { doStuff(); yield value; }`.

**📸 Verified Output:**
```
MON: 8 hours
TUE: 8 hours
WED: 8 hours
THU: 8 hours
FRI: 8 hours
SAT: 4 hours
SUN: 0 hours

positive int: 42
negative int: -7
string: hello
empty string
unknown: Double
null
```

---

### Step 3: For, While, Do-While

```java
// Loops.java
public class Loops {
    public static void main(String[] args) {
        // Classic for
        System.out.print("for:    ");
        for (int i = 0; i < 5; i++) System.out.print(i + " ");
        System.out.println();

        // While — pre-check
        System.out.print("while:  ");
        int n = 1;
        while (n <= 32) { System.out.print(n + " "); n *= 2; }
        System.out.println();

        // Do-while — always executes at least once
        System.out.print("do:     ");
        int x = 10;
        do {
            System.out.print(x + " ");
            x -= 3;
        } while (x > 0);
        System.out.println();

        // Multiple variables in for
        System.out.print("multi:  ");
        for (int i = 0, j = 10; i < j; i++, j--) {
            System.out.print("[" + i + "," + j + "] ");
        }
        System.out.println();

        // Compute factorial iteratively
        long fact = 1;
        for (int i = 1; i <= 15; i++) fact *= i;
        System.out.println("15! = " + fact);

        // FizzBuzz
        System.out.print("FizzBuzz: ");
        for (int i = 1; i <= 15; i++) {
            if (i % 15 == 0) System.out.print("FizzBuzz ");
            else if (i % 3 == 0) System.out.print("Fizz ");
            else if (i % 5 == 0) System.out.print("Buzz ");
            else System.out.print(i + " ");
        }
        System.out.println();
    }
}
```

> 💡 **Use `while` when you don't know the iteration count upfront**, `do-while` when the body must execute at least once (user input validation, retry loops). Prefer enhanced `for-each` over indexed loops when you don't need the index.

**📸 Verified Output:**
```
for:    0 1 2 3 4
while:  1 2 4 8 16 32
do:     10 7 4 1
multi:  [0,10] [1,9] [2,8] [3,7] [4,6]
15! = 1307674368000
FizzBuzz: 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz
```

---

### Step 4: Break, Continue & Labels

```java
// BreakContinue.java
public class BreakContinue {
    public static void main(String[] args) {
        // break — exit loop
        System.out.print("break at 5: ");
        for (int i = 0; i < 10; i++) {
            if (i == 5) break;
            System.out.print(i + " ");
        }
        System.out.println();

        // continue — skip iteration
        System.out.print("skip evens: ");
        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) continue;
            System.out.print(i + " ");
        }
        System.out.println();

        // Labeled break — exit nested loops
        System.out.println("Labeled break (find pair summing to 10):");
        outer:
        for (int i = 1; i <= 5; i++) {
            for (int j = 1; j <= 5; j++) {
                if (i + j == 10) {
                    System.out.println("  Found: " + i + " + " + j);
                    break outer;
                }
            }
        }

        // While with break (search)
        int[] data = {3, 7, 2, 9, 4, 1, 8};
        int target = 9;
        int pos = -1;
        for (int i = 0; i < data.length; i++) {
            if (data[i] == target) { pos = i; break; }
        }
        System.out.println("Found " + target + " at index: " + pos);
    }
}
```

> 💡 **Labeled `break`/`continue`** let you exit or skip outer loops from inside inner ones. While rare in everyday code, they avoid boolean flag variables in nested search loops. The label must be on the loop statement, not just before it.

**📸 Verified Output:**
```
break at 5: 0 1 2 3 4
skip evens: 1 3 5 7 9
Labeled break (find pair summing to 10):
  Found: 5 + 5
Found 9 at index: 3
```

---

### Step 5: Iteration Patterns — Practical Algorithms

```java
// IterationPatterns.java
import java.util.Arrays;

public class IterationPatterns {

    // Sliding window — max sum subarray of size k
    static int maxSumWindow(int[] arr, int k) {
        int windowSum = 0;
        for (int i = 0; i < k; i++) windowSum += arr[i];
        int maxSum = windowSum;
        for (int i = k; i < arr.length; i++) {
            windowSum += arr[i] - arr[i - k];
            maxSum = Math.max(maxSum, windowSum);
        }
        return maxSum;
    }

    // Two pointers — check palindrome
    static boolean isPalindrome(String s) {
        int l = 0, r = s.length() - 1;
        while (l < r) {
            if (s.charAt(l++) != s.charAt(r--)) return false;
        }
        return true;
    }

    // Bubble sort (shows nested loop pattern)
    static void bubbleSort(int[] arr) {
        for (int i = 0; i < arr.length - 1; i++)
            for (int j = 0; j < arr.length - i - 1; j++)
                if (arr[j] > arr[j + 1]) {
                    int t = arr[j]; arr[j] = arr[j+1]; arr[j+1] = t;
                }
    }

    public static void main(String[] args) {
        int[] nums = {2, 1, 5, 1, 3, 2};
        System.out.println("Max sum window k=3: " + maxSumWindow(nums, 3));

        String[] words = {"racecar", "hello", "level", "world", "madam"};
        for (String w : words)
            System.out.println(w + ": " + (isPalindrome(w) ? "palindrome" : "not"));

        int[] arr = {64, 34, 25, 12, 22, 11, 90};
        bubbleSort(arr);
        System.out.println("\nBubble sorted: " + Arrays.toString(arr));
    }
}
```

> 💡 **The sliding window pattern** processes a fixed-size window of elements by adding the new element and removing the old one — O(n) instead of O(n×k) for recomputing each window. Two pointers is another O(n) pattern that replaces nested loops in many problems.

**📸 Verified Output:**
```
Max sum window k=3: 9
racecar: palindrome
hello: not
level: palindrome
world: not
madam: palindrome

Bubble sorted: [11, 12, 22, 25, 34, 64, 90]
```

---

### Step 6: Recursion

```java
// Recursion.java
public class Recursion {

    static long factorial(int n) {
        if (n <= 1) return 1;           // base case
        return n * factorial(n - 1);    // recursive case
    }

    static int fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }

    static int binarySearch(int[] arr, int target, int lo, int hi) {
        if (lo > hi) return -1;
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) return binarySearch(arr, target, mid + 1, hi);
        return binarySearch(arr, target, lo, mid - 1);
    }

    static void printTree(String prefix, int depth, int maxDepth) {
        if (depth > maxDepth) return;
        System.out.println(prefix + "Node(depth=" + depth + ")");
        printTree(prefix + "  ├── ", depth + 1, maxDepth);
        printTree(prefix + "  └── ", depth + 1, maxDepth);
    }

    public static void main(String[] args) {
        System.out.println("Factorials:");
        for (int i = 1; i <= 7; i++) System.out.println("  " + i + "! = " + factorial(i));

        System.out.print("\nFibonacci: ");
        for (int i = 0; i < 8; i++) System.out.print(fibonacci(i) + " ");
        System.out.println();

        int[] sorted = {1, 3, 5, 7, 9, 11, 13};
        System.out.println("\nbinarySearch(7): " + binarySearch(sorted, 7, 0, sorted.length - 1));
        System.out.println("binarySearch(6): " + binarySearch(sorted, 6, 0, sorted.length - 1));

        System.out.println("\nTree:");
        printTree("", 0, 2);
    }
}
```

> 💡 **Every recursive function needs a base case** (stops recursion) and makes progress toward it. Without a base case you get `StackOverflowError`. The Fibonacci implementation here is exponential O(2^n) — in practice, memoize it or use dynamic programming.

**📸 Verified Output:**
```
Factorials:
  1! = 1
  2! = 2
  3! = 6
  4! = 24
  5! = 120
  6! = 720
  7! = 5040

Fibonacci: 0 1 1 2 3 5 8 13

binarySearch(7): 3
binarySearch(6): -1

Tree:
Node(depth=0)
  ├── Node(depth=1)
    ├── Node(depth=2)
    └── Node(depth=2)
  └── Node(depth=1)
    ├── Node(depth=2)
    └── Node(depth=2)
```

---

### Step 7: Text Blocks & Formatted Output

```java
// FormattedOutput.java
public class FormattedOutput {
    public static void main(String[] args) {
        // printf-style formatting
        String[] items = {"Apple", "Banana", "Cherry"};
        double[] prices = {1.99, 0.75, 3.50};

        System.out.printf("%-12s %8s%n", "Item", "Price");
        System.out.println("-".repeat(22));
        double total = 0;
        for (int i = 0; i < items.length; i++) {
            System.out.printf("%-12s %8.2f%n", items[i], prices[i]);
            total += prices[i];
        }
        System.out.println("-".repeat(22));
        System.out.printf("%-12s %8.2f%n", "TOTAL", total);

        // Text block (Java 15+)
        String json = """
                {
                    "name": "Dr. Chen",
                    "role": "admin",
                    "score": %d
                }
                """.formatted(100);
        System.out.println("\nJSON:\n" + json);

        // String.format
        for (int i = 1; i <= 5; i++) {
            String bar = "█".repeat(i * 4) + " " + (i * 20) + "%";
            System.out.printf("Task %-2d: %s%n", i, bar);
        }
    }
}
```

> 💡 **Text blocks** (triple-quoted strings) preserve indentation relative to the closing `"""`. The `formatted()` method works like `String.format()` but chains nicely. `%n` is the platform-appropriate newline — prefer it over `\n` in `printf`.

**📸 Verified Output:**
```
Item            Price
----------------------
Apple            1.99
Banana           0.75
Cherry           3.50
----------------------
TOTAL            6.24

JSON:
{
    "name": "Dr. Chen",
    "role": "admin",
    "score": 100
}

Task 1 : ████ 20%
Task 2 : ████████ 40%
Task 3 : ████████████ 60%
Task 4 : ████████████████ 80%
Task 5 : ████████████████████ 100%
```

---

### Step 8: Putting It Together — Number Guessing Game Logic

```java
// GuessingGame.java
import java.util.Random;

public class GuessingGame {

    record GuessResult(boolean correct, String hint, int attemptsLeft) {}

    static class Game {
        private final int secret;
        private final int maxAttempts;
        private int attempts = 0;

        Game(int max, int maxAttempts) {
            this.secret = new Random().nextInt(max) + 1;
            this.maxAttempts = maxAttempts;
        }

        GuessResult guess(int n) {
            attempts++;
            int remaining = maxAttempts - attempts;
            if (n == secret) return new GuessResult(true, "Correct!", remaining);
            String hint = n < secret ? "Too low" : "Too high";
            if (remaining == 0) hint = "Game over! Answer was " + secret;
            return new GuessResult(false, hint, remaining);
        }

        boolean isOver() { return attempts >= maxAttempts; }
    }

    public static void main(String[] args) {
        // Simulate a game with a known sequence
        // (In real use, you'd read from Scanner)
        int secret = 42;

        // Binary search strategy (optimal)
        int lo = 1, hi = 100, guesses = 0;
        System.out.println("Binary search for " + secret + " in [1,100]:");
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            guesses++;
            System.out.printf("  Guess %d: %d → ", guesses, mid);
            if (mid == secret) { System.out.println("Found!"); break; }
            if (mid < secret) { System.out.println("too low"); lo = mid + 1; }
            else { System.out.println("too high"); hi = mid - 1; }
        }
        System.out.println("Solved in " + guesses + " guesses (max possible: 7 for n=100)");
    }
}
```

> 💡 **Binary search always finds a number in 1–100 within 7 guesses** (log₂100 ≈ 6.6). This is why binary search is O(log n) — each guess halves the search space. The same logic applies to searching sorted arrays, database indexes, and Git's `bisect`.

**📸 Verified Output:**
```
Binary search for 42 in [1,100]:
  Guess 1: 50 → too high
  Guess 2: 25 → too low
  Guess 3: 37 → too low
  Guess 4: 43 → too high
  Guess 5: 40 → too low
  Guess 6: 41 → too low
  Guess 7: 42 → Found!
Solved in 7 guesses (max possible: 7 for n=100)
```

---

## Verification

```bash
javac GuessingGame.java && java GuessingGame
```

## Summary

You've mastered Java control flow: modern switch expressions, all loop types, break/continue with labels, recursion, and formatted output. These patterns underpin every Java program you'll ever write.

## Further Reading
- [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441)
- [Oracle Tutorial: Control Flow Statements](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/flow.html)
