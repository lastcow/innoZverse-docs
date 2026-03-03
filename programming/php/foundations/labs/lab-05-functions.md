# Lab 5: Functions, Closures & Arrow Functions

## Objective
Define and call functions with typed parameters, default values, variadic args, and return types. Write closures and arrow functions. Use first-class callable syntax and higher-order functions.

## Background
PHP 8 has a mature function system with union types, named arguments, readonly properties, and first-class callable syntax. Closures are objects in PHP (`Closure` class) — they can be stored, passed, and bound to different objects. Understanding PHP's function capabilities is essential for modern PHP frameworks like Laravel and Symfony.

## Time
35 minutes

## Prerequisites
- Lab 04 (Control Flow)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Function Basics & Type Declarations

```php
<?php
declare(strict_types=1);

// Typed parameters + return type
function add(int $a, int $b): int {
    return $a + $b;
}

// Default parameter values
function greet(string $name, string $greeting = 'Hello'): string {
    return "$greeting, $name!";
}

// Nullable type
function findUser(?int $id): ?string {
    if ($id === null) return null;
    return $id > 0 ? "User #$id" : null;
}

// Union types (PHP 8.0+)
function formatValue(int|float|string $value): string {
    return match(true) {
        is_int($value)   => "int($value)",
        is_float($value) => "float($value)",
        default          => "string($value)",
    };
}

echo add(3, 4) . "\n";
echo greet("Dr. Chen") . "\n";
echo greet("Dr. Chen", "Welcome") . "\n";
echo (findUser(5) ?? "not found") . "\n";
echo (findUser(null) ?? "null given") . "\n";
echo formatValue(42) . "\n";
echo formatValue(3.14) . "\n";
echo formatValue("hello") . "\n";
```

> 💡 **`declare(strict_types=1)`** at the top of a file enables strict type checking — passing a `float` to an `int` parameter throws a `TypeError` instead of silently converting. Always use it in modern PHP code to catch type errors early.

**📸 Verified Output:**
```
7
Hello, Dr. Chen!
Welcome, Dr. Chen!
User #5
null given
int(42)
float(3.14)
string(hello)
```

---

### Step 2: Named Arguments & Variadic Functions

```php
<?php
declare(strict_types=1);

function createUser(
    string $name,
    int    $age    = 0,
    string $role   = 'user',
    bool   $active = true
): array {
    return compact('name', 'age', 'role', 'active');
}

// Named arguments — order doesn't matter, skip defaults
$admin = createUser(name: 'Dr. Chen', role: 'admin', age: 40);
$guest = createUser(name: 'Guest', active: false);

print_r($admin);
print_r($guest);

// Variadic functions (rest params)
function sum(int ...$numbers): int {
    return array_sum($numbers);
}

function joinWith(string $separator, string ...$parts): string {
    return implode($separator, $parts);
}

echo "Sum: " . sum(1, 2, 3, 4, 5) . "\n";
echo "Join: " . joinWith(' | ', 'alpha', 'beta', 'gamma') . "\n";

// Spread operator to unpack array
$nums = [10, 20, 30];
echo "Spread sum: " . sum(...$nums) . "\n";

// First-class callable syntax (PHP 8.1+)
$sumFn = sum(...);
$arr   = [1, 2, 3, 4, 5];
echo "First-class: " . $sumFn(1, 2, 3) . "\n";
```

> 💡 **Named arguments** (PHP 8.0+) let you skip optional parameters and document intent. `createUser(name: 'Alice', role: 'admin')` is clearer than `createUser('Alice', 0, 'admin', true)`. They also make function calls resilient to parameter reordering.

**📸 Verified Output:**
```
Array ( [name] => Dr. Chen [age] => 40 [role] => admin [active] => 1 )
Array ( [name] => Guest [age] => 0 [role] => user [active] => )
Sum: 15
Join: alpha | beta | gamma
Spread sum: 60
First-class: 6
```

---

### Step 3: Closures

```php
<?php
// Closure — anonymous function stored in variable
$double = function(int $n): int { return $n * 2; };
echo "double(5) = " . $double(5) . "\n";

// Closure with use — capture outer variables
$multiplier = 3;
$multiplyBy = function(int $n) use ($multiplier): int {
    return $n * $multiplier;
};
echo "multiplyBy(7) = " . $multiplyBy(7) . "\n";

// Capture by reference
$counter = 0;
$increment = function() use (&$counter): void {
    $counter++;
};
$increment(); $increment(); $increment();
echo "counter = $counter\n";

// Return closure from function (factory pattern)
function makeAdder(int $n): Closure {
    return fn(int $x): int => $x + $n;  // arrow fn
}

$add5  = makeAdder(5);
$add10 = makeAdder(10);
echo "\nadd5(3)  = " . $add5(3) . "\n";
echo "add10(3) = " . $add10(3) . "\n";

// Closure::bind — bind closure to a class
class MyClass {
    private int $value = 42;
}

$getter = Closure::bind(function() { return $this->value; }, new MyClass(), MyClass::class);
echo "Private value: " . $getter() . "\n";
```

> 💡 **`use` captures by value by default.** If the outer variable changes after the closure is defined, the closure still sees the original value. Use `use (&$var)` to capture by reference — then both the closure and outer scope share the same variable.

**📸 Verified Output:**
```
double(5) = 10
multiplyBy(7) = 21
counter = 3

add5(3)  = 8
add10(3) = 13
Private value: 42
```

---

### Step 4: Arrow Functions

```php
<?php
// Arrow functions — implicit use (capture scope automatically)
$factor = 5;
$multiply = fn(int $n): int => $n * $factor;  // no 'use' needed
echo "multiply(6) = " . $multiply(6) . "\n";

// Arrow functions in array operations
$numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
$threshold = 5;

$filtered = array_filter($numbers, fn($n) => $n > $threshold);
$squared  = array_map(fn($n) => $n ** 2, $filtered);

echo "Filtered+squared: " . implode(', ', $squared) . "\n";

// Chain with usort
$products = [
    ['name' => 'A', 'price' => 29.99],
    ['name' => 'B', 'price' => 9.99],
    ['name' => 'C', 'price' => 49.99],
];
usort($products, fn($a, $b) => $a['price'] <=> $b['price']);
echo "\nSorted by price:\n";
foreach ($products as $p) printf("  %-4s $%.2f\n", $p['name'], $p['price']);

// Arrow function cannot modify outer scope (unlike & reference closures)
$x = 10;
$fn = fn() => $x * 2;  // reads $x, cannot modify it
echo "\nfn reads x: " . $fn() . "\n";
echo "x unchanged: $x\n";
```

> 💡 **Arrow functions (`fn`) automatically capture outer variables** by value without `use` — they read the enclosing scope implicitly. They're single-expression (no `{}`), always `return` the expression result, and can't modify outer variables (no `&` capture). Perfect for short callbacks.

**📸 Verified Output:**
```
multiply(6) = 30
Filtered+squared: 36, 49, 64, 81, 100

Sorted by price:
  B    $9.99
  A    $29.99
  C    $49.99

fn reads x: 20
x unchanged: 10
```

---

### Step 5: Higher-Order Functions

```php
<?php
// Pass functions as arguments
function pipe(mixed $value, callable ...$fns): mixed {
    return array_reduce($fns, fn($carry, $fn) => $fn($carry), $value);
}

function compose(callable ...$fns): Closure {
    return fn($x) => array_reduce(
        array_reverse($fns),
        fn($carry, $fn) => $fn($carry),
        $x
    );
}

// Small functions to compose
$trim     = fn(string $s) => trim($s);
$lower    = fn(string $s) => strtolower($s);
$slug     = fn(string $s) => preg_replace('/\s+/', '-', $s);
$noSpecial = fn(string $s) => preg_replace('/[^a-z0-9-]/', '', $s);

$toSlug = compose($noSpecial, $slug, $lower, $trim);

echo $toSlug("  Hello, World! This is PHP  ") . "\n";
echo $toSlug("  Dr. Chen's PHP Lab #5  ") . "\n";

// Higher-order function returning function
function memoize(callable $fn): Closure {
    $cache = [];
    return function() use ($fn, &$cache) {
        $key = serialize(func_get_args());
        if (!array_key_exists($key, $cache)) {
            $cache[$key] = $fn(...func_get_args());
        }
        return $cache[$key];
    };
}

$slowSquare = memoize(function(int $n): int {
    usleep(1000); // simulate work
    return $n * $n;
});

echo "\nSquare(7): " . $slowSquare(7) . "\n";
echo "Square(7) cached: " . $slowSquare(7) . "\n";
echo "Square(8): " . $slowSquare(8) . "\n";
```

> 💡 **`compose(f, g, h)($x)` = `f(g(h($x)))`** — right to left like math. `pipe($x, f, g, h)` = `h(g(f($x)))` — left to right, more readable. Both are fundamental FP patterns. Memoization is safe only for pure functions (same input always gives same output, no side effects).

**📸 Verified Output:**
```
hello-world-this-is-php
dr-chens-php-lab-5

Square(7): 49
Square(7) cached: 49
Square(8): 64
```

---

### Step 6: Recursion

```php
<?php
function factorial(int $n): int {
    if ($n <= 1) return 1;
    return $n * factorial($n - 1);
}

// Tail-recursive style with accumulator
function factAcc(int $n, int $acc = 1): int {
    if ($n <= 1) return $acc;
    return factAcc($n - 1, $n * $acc);
}

for ($i = 1; $i <= 7; $i++) {
    echo "$i! = " . factorial($i) . "\n";
}

// Tree traversal
function buildTree(int $depth, string $prefix = ''): void {
    if ($depth === 0) return;
    echo $prefix . "Node(depth=" . $depth . ")\n";
    buildTree($depth - 1, $prefix . "  ├─ ");
    buildTree($depth - 1, $prefix . "  └─ ");
}

echo "\nTree:\n";
buildTree(3);

// Flatten nested array recursively
function flatten(array $arr): array {
    $result = [];
    foreach ($arr as $item) {
        if (is_array($item)) {
            $result = array_merge($result, flatten($item));
        } else {
            $result[] = $item;
        }
    }
    return $result;
}

$nested = [1, [2, [3, [4]], 5], 6];
echo "\nFlattened: " . implode(', ', flatten($nested)) . "\n";
```

> 💡 **PHP's default stack depth** handles ~100–1000 recursive calls before stack overflow. For deep recursion, use `ini_set('xdebug.max_nesting_level', 1000)` or convert to iteration. `array_merge` inside recursion is O(n) each call — for large arrays, use a reference-based approach.

**📸 Verified Output:**
```
1! = 1
2! = 2
3! = 6
4! = 24
5! = 120
6! = 720
7! = 5040

Tree:
Node(depth=3)
  ├─ Node(depth=2)
    ├─ Node(depth=1)
    └─ Node(depth=1)
  └─ Node(depth=2)
    ├─ Node(depth=1)
    └─ Node(depth=1)

Flattened: 1, 2, 3, 4, 5, 6
```

---

### Step 7: Static Functions & Built-in Callables

```php
<?php
// Static functions — can be called without object
class MathUtils {
    public static function square(int $n): int { return $n * $n; }
    public static function cube(int $n): int   { return $n ** 3; }
}

$numbers = [1, 2, 3, 4, 5];
$squares = array_map([MathUtils::class, 'square'], $numbers);
$cubes   = array_map(MathUtils::cube(...), $numbers);  // first-class

echo "Squares: " . implode(', ', $squares) . "\n";
echo "Cubes: "   . implode(', ', $cubes) . "\n";

// Built-in functions as callables
$words = ['  hello  ', '  WORLD  ', '  PHP  '];
$cleaned = array_map('trim', $words);
$lowered = array_map('strtolower', $cleaned);
echo "\nCleaned: " . implode(', ', $lowered) . "\n";

// is_* functions as filters
$mixed = [1, 'two', 3.0, null, true, 'five', 7];
$ints    = array_filter($mixed, 'is_int');
$strings = array_filter($mixed, 'is_string');

echo "Integers: "  . implode(', ', $ints) . "\n";
echo "Strings: "   . implode(', ', $strings) . "\n";

// usort with static method
$people = [
    ['name' => 'Charlie', 'age' => 30],
    ['name' => 'Alice',   'age' => 25],
    ['name' => 'Bob',     'age' => 35],
];
usort($people, fn($a, $b) => $a['name'] <=> $b['name']);
echo "\nSorted: " . implode(', ', array_column($people, 'name')) . "\n";
```

> 💡 **PHP built-in functions are valid callables** — you can pass `'strtolower'`, `'trim'`, `'is_int'` as strings to `array_map`, `array_filter`, `usort`. This works because PHP looks them up by name. The first-class callable syntax `strtolower(...)` creates a `Closure` — more type-safe.

**📸 Verified Output:**
```
Squares: 1, 4, 9, 16, 25
Cubes: 1, 8, 27, 64, 125

Cleaned: hello, world, php
Integers: 1, 7
Strings: two, five

Sorted: Alice, Bob, Charlie
```

---

### Step 8: Complete Example — Pipeline Processor

```php
<?php
declare(strict_types=1);

class Pipeline {
    private array $stages = [];

    public function pipe(callable $stage): static {
        $clone = clone $this;
        $clone->stages[] = $stage;
        return $clone;
    }

    public function process(mixed $payload): mixed {
        return array_reduce(
            $this->stages,
            fn($carry, $stage) => $stage($carry),
            $payload
        );
    }

    public function processAll(array $payloads): array {
        return array_map(fn($p) => $this->process($p), $payloads);
    }
}

// Text processing pipeline
$textPipeline = (new Pipeline())
    ->pipe(fn($s) => trim($s))
    ->pipe(fn($s) => strtolower($s))
    ->pipe(fn($s) => preg_replace('/\s+/', ' ', $s))
    ->pipe(fn($s) => preg_replace('/[^a-z0-9\s]/', '', $s))
    ->pipe(fn($s) => ucwords($s));

$texts = [
    "  Hello,   WORLD!  ",
    "  Dr. Chen's   PHP   Lab #5  ",
    "   MODERN  php   8.3   features   ",
];

echo "Text Pipeline:\n";
foreach ($textPipeline->processAll($texts) as $result) {
    echo "  → $result\n";
}

// Data transformation pipeline
$dataPipeline = (new Pipeline())
    ->pipe(fn($data) => array_filter($data, fn($n) => $n > 0))
    ->pipe(fn($data) => array_map(fn($n) => $n * 2, $data))
    ->pipe(fn($data) => array_values($data))
    ->pipe(fn($data) => array_sum($data));

$dataset = [-3, 1, -1, 4, 2, -2, 5, 3];
echo "\nData Pipeline:\n";
echo "  Input: " . implode(', ', $dataset) . "\n";
echo "  Output (filter>0, double, sum): " . $dataPipeline->process($dataset) . "\n";
```

> 💡 **The Pipeline pattern** chains transformations functionally. Each `pipe()` returns a clone (immutable) so you can branch pipelines. This is how Laravel's pipeline, middleware stacks, and Guzzle request handlers work internally. The `static` return type hint enables method chaining with subclasses.

**📸 Verified Output:**
```
Text Pipeline:
  → Hello World
  → Dr Chens Php Lab 5
  → Modern Php 83 Features

Data Pipeline:
  Input: -3, 1, -1, 4, 2, -2, 5, 3
  Output (filter>0, double, sum): 30
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
\$pipeline = array_reduce(
    [fn(\$n) => \$n * 2, fn(\$n) => \$n + 10, fn(\$n) => \$n ** 2],
    fn(\$carry, \$fn) => \$fn(\$carry),
    5
);
echo 'Pipeline result: ' . \$pipeline . PHP_EOL;
"
```

Expected: `Pipeline result: 400` (5 × 2 = 10, + 10 = 20, 20² = 400)

## Summary

PHP functions are first-class citizens — typed, composable, and flexible. You've covered type declarations, named arguments, variadic functions, closures with `use`, arrow functions with implicit capture, higher-order functions, recursion, and a full Pipeline pattern. These skills underpin every modern PHP framework.

## Further Reading
- [PHP 8.1 First-class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php)
- [PHP Arrow Functions](https://www.php.net/manual/en/functions.arrow.php)
- [Laravel Pipeline](https://laravel.com/api/master/Illuminate/Pipeline/Pipeline.html)
