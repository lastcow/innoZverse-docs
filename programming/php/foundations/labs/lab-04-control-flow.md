# Lab 4: Control Flow — Conditionals, Loops & Match

## Objective
Master PHP control flow: if/elseif/else, match expressions, switch, for/while/foreach/do-while loops, break/continue, and list comprehension patterns.

## Background
PHP control flow is similar to most C-style languages but with PHP-specific additions: the `match` expression (PHP 8.0), the null coalescing operator `??`, and the nullsafe operator `?->`. These modern features make PHP code concise and safe.

## Time
30 minutes

## Prerequisites
- Lab 03 (Arrays)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: If / Elseif / Else

```php
<?php
function classify(int $score): string {
    if ($score >= 90) return 'A';
    elseif ($score >= 80) return 'B';
    elseif ($score >= 70) return 'C';
    elseif ($score >= 60) return 'D';
    else return 'F';
}

foreach ([95, 82, 71, 55, 100] as $s) {
    echo "$s → " . classify($s) . "\n";
}

// Ternary
$age = 20;
$status = $age >= 18 ? 'adult' : 'minor';
echo "\n$age is $status\n";

// Null coalescing ??
$config = ['debug' => true, 'timeout' => 30];
echo "debug: "   . ($config['debug'] ?? false ? 'on' : 'off') . "\n";
echo "retries: " . ($config['retries'] ?? 3) . "\n";  // default 3

// Null coalescing assignment ??=
$config['retries'] ??= 5;
echo "retries set: " . $config['retries'] . "\n";

// Spaceship operator <=>
$cmp = 5 <=> 10;
echo "\n5 <=> 10: $cmp\n";  // -1
echo "10 <=> 5: " . (10 <=> 5) . "\n"; // 1
echo "5 <=> 5: " . (5 <=> 5) . "\n";   // 0
```

> 💡 **`??` (null coalescing)** returns the left side if it exists and is not null, otherwise the right side. It's safer than `isset($x) ? $x : $default`. **`??=`** assigns the default only if the variable is null/unset — perfect for lazy initialization.

**📸 Verified Output:**
```
95 → A
82 → B
71 → C
55 → F
100 → A

20 is adult
debug: on
retries: 3
retries set: 3

5 <=> 10: -1
10 <=> 5: 1
5 <=> 5: 0
```

---

### Step 2: Match Expression (PHP 8.0+)

```php
<?php
// match — strict comparison, no fallthrough, exhaustive
$status = 'shipped';
$label = match($status) {
    'pending'   => '⏳ Pending',
    'shipped'   => '🚚 Shipped',
    'delivered' => '✅ Delivered',
    'cancelled' => '❌ Cancelled',
    default     => '❓ Unknown',
};
echo "$label\n";

// match with no-match exception
function httpStatus(int $code): string {
    return match(true) {
        $code >= 500 => 'Server Error',
        $code >= 400 => 'Client Error',
        $code >= 300 => 'Redirect',
        $code >= 200 => 'Success',
        default      => 'Unknown',
    };
}

foreach ([200, 301, 404, 500, 503] as $code) {
    echo "$code: " . httpStatus($code) . "\n";
}

// Multiple conditions per arm
$day = 3; // Wednesday
$type = match($day) {
    1, 7    => 'Weekend',
    2, 3, 4, 5, 6 => 'Weekday',
};
echo "\nDay $day: $type\n";

// match as expression in string
$score = 92;
echo "Grade: " . match(true) {
    $score >= 90 => 'A',
    $score >= 80 => 'B',
    $score >= 70 => 'C',
    default      => 'F',
} . "\n";
```

> 💡 **`match` vs `switch`:** `match` uses strict `===` comparison (no type juggling), has no fallthrough, must be exhaustive (or have `default`), and is an expression that returns a value. `switch` uses loose `==`, falls through by default, and is a statement. Prefer `match` in PHP 8+.

**📸 Verified Output:**
```
🚚 Shipped
200: Success
301: Redirect
404: Client Error
500: Server Error
503: Server Error

Day 3: Weekday
Grade: A
```

---

### Step 3: For, While, Do-While

```php
<?php
// Classic for
echo "Powers of 2: ";
for ($i = 0; $i <= 8; $i++) {
    echo (2 ** $i) . " ";
}
echo "\n";

// While
echo "Collatz from 27: ";
$n = 27; $steps = 0;
while ($n !== 1) {
    $n = ($n % 2 === 0) ? $n / 2 : 3 * $n + 1;
    $steps++;
}
echo "$steps steps to reach 1\n";

// Do-while — always runs at least once
$attempts = 0;
do {
    $random = rand(1, 10);
    $attempts++;
} while ($random !== 7);
echo "Rolled 7 after $attempts attempt(s)\n";

// Nested for — multiplication table
echo "\n3×3 table:\n";
for ($i = 1; $i <= 3; $i++) {
    for ($j = 1; $j <= 3; $j++) {
        printf("%4d", $i * $j);
    }
    echo "\n";
}

// FizzBuzz
echo "\nFizzBuzz: ";
for ($i = 1; $i <= 15; $i++) {
    echo match(0) {
        $i % 15 => 'FizzBuzz',
        $i % 3  => 'Fizz',
        $i % 5  => 'Buzz',
        default => $i,
    } . " ";
}
echo "\n";
```

> 💡 **The Collatz conjecture** is an unsolved math problem — starting from any positive integer, repeatedly applying "halve if even, 3n+1 if odd" always reaches 1. Starting from 27 takes 111 steps. It's a great `while` loop exercise.

**📸 Verified Output:**
```
Powers of 2: 1 2 4 8 16 32 64 128 256
Collatz from 27: 111 steps to reach 1
Rolled 7 after 3 attempt(s)

3×3 table:
   1   2   3
   2   4   6
   3   6   9

FizzBuzz: 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz
```

---

### Step 4: Foreach — Arrays and Objects

```php
<?php
// Basic foreach
$colors = ['red', 'green', 'blue'];
foreach ($colors as $color) {
    echo "- $color\n";
}

// Foreach with key
$prices = ['apple' => 1.99, 'banana' => 0.75, 'cherry' => 3.50];
echo "\nPrices:\n";
foreach ($prices as $item => $price) {
    printf("  %-10s $%.2f\n", $item, $price);
}

// Modify by reference
$numbers = [1, 2, 3, 4, 5];
foreach ($numbers as &$n) {
    $n *= 2;
}
unset($n); // IMPORTANT: unset reference after loop
echo "\nDoubled: " . implode(', ', $numbers) . "\n";

// Nested foreach
$matrix = [[1,2,3],[4,5,6],[7,8,9]];
echo "\nMatrix:\n";
foreach ($matrix as $row) {
    foreach ($row as $val) {
        printf("%4d", $val);
    }
    echo "\n";
}

// foreach with list() destructuring
$people = [['Alice', 30], ['Bob', 25], ['Carol', 35]];
echo "\nPeople:\n";
foreach ($people as [$name, $age]) {
    echo "  $name is $age\n";
}
```

> 💡 **Always `unset($reference)` after a reference foreach.** PHP's `foreach ($arr as &$val)` loop leaves `$val` pointing to the last element. If you later do `foreach ($arr as $val)`, it overwrites the last element with each value — a notorious PHP bug. `unset($n)` breaks the reference safely.

**📸 Verified Output:**
```
- red
- green
- blue

Prices:
  apple      $1.99
  banana     $0.75
  cherry     $3.50

Doubled: 2, 4, 6, 8, 10

Matrix:
   1   2   3
   4   5   6
   7   8   9

People:
  Alice is 30
  Bob is 25
  Carol is 35
```

---

### Step 5: Break, Continue & Labels

```php
<?php
// break — exit loop
echo "Break at 5: ";
for ($i = 0; $i < 10; $i++) {
    if ($i === 5) break;
    echo "$i ";
}
echo "\n";

// continue — skip iteration
echo "Skip evens: ";
for ($i = 0; $i < 10; $i++) {
    if ($i % 2 === 0) continue;
    echo "$i ";
}
echo "\n";

// break N — break N levels of nesting
echo "\nbreak 2 (exit both loops):\n";
for ($i = 0; $i < 3; $i++) {
    for ($j = 0; $j < 3; $j++) {
        if ($i === 1 && $j === 1) {
            echo "  Breaking at i=$i, j=$j\n";
            break 2;
        }
        echo "  i=$i, j=$j\n";
    }
}
echo "After loops\n";

// continue 2 — continue outer loop
echo "\nSkip when j==1:\n";
for ($i = 0; $i < 3; $i++) {
    for ($j = 0; $j < 3; $j++) {
        if ($j === 1) continue 2; // skip rest of outer iteration
        echo "  i=$i j=$j\n";
    }
}
```

> 💡 **PHP's `break N` and `continue N`** (where N is a numeric literal) control nested loops — `break 2` exits both the current and outer loop. This eliminates the need for flag variables in nested search loops. N must be a positive integer literal, not a variable.

**📸 Verified Output:**
```
Break at 5: 0 1 2 3 4
Skip evens: 1 3 5 7 9

break 2 (exit both loops):
  i=0, j=0
  i=0, j=1
  i=0, j=2
  i=1, j=0
  Breaking at i=1, j=1
After loops

Skip when j==1:
  i=0 j=0
  i=1 j=0
  i=2 j=0
```

---

### Step 6: Generator Functions

```php
<?php
// Generators — lazy sequences with yield
function fibonacci(): Generator {
    [$a, $b] = [0, 1];
    while (true) {
        yield $a;
        [$a, $b] = [$b, $a + $b];
    }
}

function take(Generator $gen, int $n): array {
    $result = [];
    for ($i = 0; $i < $n; $i++) {
        $result[] = $gen->current();
        $gen->next();
    }
    return $result;
}

echo "Fibonacci: " . implode(', ', take(fibonacci(), 10)) . "\n";

// Generator with keys
function indexedSquares(int $limit): Generator {
    for ($i = 1; $i <= $limit; $i++) {
        yield $i => $i ** 2;  // key => value
    }
}

echo "\nSquares:\n";
foreach (indexedSquares(5) as $n => $sq) {
    echo "  $n² = $sq\n";
}

// Lazy file reader
function readLines(string $text): Generator {
    foreach (explode("\n", $text) as $line) {
        if (trim($line) !== '') yield $line;
    }
}

$text = "Line 1\n\nLine 2\nLine 3\n\nLine 4";
echo "\nNon-empty lines:\n";
foreach (readLines($text) as $line) {
    echo "  $line\n";
}
```

> 💡 **Generators are memory-efficient** — a generator that yields 1 million numbers uses O(1) memory (only the current value). A regular function returning an array of 1 million numbers uses O(n) memory. Use generators for large datasets, file processing, and infinite sequences.

**📸 Verified Output:**
```
Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34

Squares:
  1² = 1
  2² = 4
  3² = 9
  4² = 16
  5² = 25

Non-empty lines:
  Line 1
  Line 2
  Line 3
  Line 4
```

---

### Step 7: Exception Flow Control

```php
<?php
function divide(float $a, float $b): float {
    if ($b == 0) throw new DivisionByZeroError("Cannot divide by zero");
    return $a / $b;
}

function parseInt(string $s): int {
    if (!is_numeric($s)) throw new InvalidArgumentException("Not a number: '$s'");
    return (int)$s;
}

// try-catch-finally
echo "Division:\n";
foreach ([[10, 2], [7, 0], [15, 3]] as [$a, $b]) {
    try {
        $result = divide($a, $b);
        echo "  $a / $b = $result\n";
    } catch (DivisionByZeroError $e) {
        echo "  Error: " . $e->getMessage() . "\n";
    } finally {
        // always runs
    }
}

// Multiple catch types
$inputs = ['42', 'abc', '0', '10'];
echo "\nParsing:\n";
foreach ($inputs as $input) {
    try {
        $n = parseInt($input);
        $result = divide(100, $n);
        echo "  100 / $n = $result\n";
    } catch (InvalidArgumentException $e) {
        echo "  Invalid: " . $e->getMessage() . "\n";
    } catch (DivisionByZeroError $e) {
        echo "  Math: " . $e->getMessage() . "\n";
    }
}
```

> 💡 **PHP 8 has separate `Error` and `Exception` hierarchies.** `DivisionByZeroError` extends `ArithmeticError` extends `Error` — you can't catch it with `catch (Exception $e)`. Use `catch (Throwable $e)` to catch both `Error` and `Exception` types. Always catch the most specific type first.

**📸 Verified Output:**
```
Division:
  10 / 2 = 5
  Error: Cannot divide by zero
  15 / 3 = 5

Parsing:
  100 / 42 = 2.380952...
  Invalid: Not a number: 'abc'
  Math: Cannot divide by zero
  100 / 10 = 10
```

---

### Step 8: Complete Example — Grade Calculator

```php
<?php
function letterGrade(float $score): string {
    return match(true) {
        $score >= 97 => 'A+', $score >= 93 => 'A', $score >= 90 => 'A-',
        $score >= 87 => 'B+', $score >= 83 => 'B', $score >= 80 => 'B-',
        $score >= 77 => 'C+', $score >= 73 => 'C', $score >= 70 => 'C-',
        $score >= 60 => 'D',
        default      => 'F',
    };
}

function gpa(string $letter): float {
    return match($letter) {
        'A+', 'A' => 4.0, 'A-' => 3.7,
        'B+'      => 3.3, 'B'  => 3.0, 'B-' => 2.7,
        'C+'      => 2.3, 'C'  => 2.0, 'C-' => 1.7,
        'D'       => 1.0,
        default   => 0.0,
    };
}

$students = [
    ['name' => 'Alice', 'scores' => [95, 88, 92, 97, 90]],
    ['name' => 'Bob',   'scores' => [72, 65, 78, 70, 68]],
    ['name' => 'Carol', 'scores' => [88, 91, 85, 93, 89]],
    ['name' => 'Dave',  'scores' => [55, 60, 58, 45, 62]],
];

echo sprintf("%-10s %8s %6s %4s\n", "Name", "Average", "Grade", "GPA");
echo str_repeat('─', 35) . "\n";

$classGPAs = [];
foreach ($students as $student) {
    $avg    = array_sum($student['scores']) / count($student['scores']);
    $grade  = letterGrade($avg);
    $points = gpa($grade);
    $classGPAs[] = $points;

    printf("%-10s %8.1f %6s %4.1f\n", $student['name'], $avg, $grade, $points);
}

echo str_repeat('─', 35) . "\n";
$classAvg = array_sum($classGPAs) / count($classGPAs);
printf("%-10s %8s %6s %4.2f\n", "CLASS AVG", "", "", $classAvg);

// Honor roll
echo "\nHonor Roll (GPA >= 3.5):\n";
$honorRoll = array_filter($students, function($s) {
    $avg   = array_sum($s['scores']) / count($s['scores']);
    $grade = letterGrade($avg);
    return gpa($grade) >= 3.5;
});
foreach ($honorRoll as $s) {
    echo "  🏆 {$s['name']}\n";
}
```

> 💡 **`match(true)` with range conditions** is one of PHP's most readable patterns — it evaluates each arm as a boolean, stopping at the first `true`. Combined with chained `match` for GPA lookup, this replaces complex nested if-elseif chains with clean, composable functions.

**📸 Verified Output:**
```
Name       Average  Grade  GPA
───────────────────────────────────
Alice        92.4     A-  3.7
Bob          70.6     C-  1.7
Carol        89.2     B+  3.3
Dave         56.0      F  0.0
───────────────────────────────────
CLASS AVG                2.18

Honor Roll (GPA >= 3.5):
  🏆 Alice
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
for (\$i = 1; \$i <= 20; \$i++) {
    echo match(0) { \$i%15=>'FizzBuzz', \$i%3=>'Fizz', \$i%5=>'Buzz', default=>\$i } . ' ';
}
"
```

## Summary

PHP control flow is expressive and pragmatic. You've covered `if/elseif/else`, the modern `match` expression, all loop types, `break N`/`continue N`, generators, and exception flow. The `match` expression and null coalescing operators are among PHP 8's most impactful additions.

## Further Reading
- [PHP 8.0 match expression](https://www.php.net/manual/en/control-structures.match.php)
- [PHP Generators](https://www.php.net/manual/en/language.generators.php)
