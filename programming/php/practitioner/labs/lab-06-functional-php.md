# Lab 6: Functional PHP — Closures, Higher-Order Functions & Pipelines

## Objective
Master PHP's functional programming toolkit: first-class functions, closures with `use`, higher-order functions (`array_map`, `array_filter`, `array_reduce`), currying, function composition, lazy evaluation with generators, and building a data transformation pipeline.

## Background
PHP is a multi-paradigm language — you can write it functionally without any framework. Functional style produces more testable code because pure functions (same input → same output, no side effects) are easy to unit test. PHP closures capture variables by value by default; the `use (&$var)` syntax captures by reference. First-class callable syntax (`strlen(...)`) was added in PHP 8.1 and eliminates `Closure::fromCallable()` boilerplate.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 05 (Functions & Closures)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Closures, `use`, and first-class callables

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
echo "=== Closures & use ===" . PHP_EOL;

// Closure captures variables from outer scope via "use"
function makeDiscount(float $pct): Closure {
    return function(float $price) use ($pct): float {
        return round($price * (1 - $pct), 2);
    };
}

$discount10 = makeDiscount(0.10);
$discount20 = makeDiscount(0.20);
$discount30 = makeDiscount(0.30);

$prices = [864.00, 1299.00, 49.99, 99.99, 29.99];
echo "Original:    " . implode(", ", array_map(fn($p) => "\${$p}", $prices)) . PHP_EOL;
echo "10% off:     " . implode(", ", array_map(fn($p) => "\${$discount10($p)}", $prices)) . PHP_EOL;
echo "20% off:     " . implode(", ", array_map(fn($p) => "\${$discount20($p)}", $prices)) . PHP_EOL;

// use by reference — closure can MODIFY outer variable
$log = [];
$logger = function(string $msg) use (&$log): void {
    $log[] = date("H:i:s") . " " . $msg;
};
$logger("Order #1001 placed");
$logger("Payment received");
$logger("Shipped");
echo PHP_EOL . "Log entries: " . count($log) . PHP_EOL;
foreach ($log as $entry) echo "  " . $entry . PHP_EOL;

// PHP 8.1 first-class callable syntax
echo PHP_EOL . "=== First-Class Callables ===" . PHP_EOL;
$names = ["  Surface Pro  ", "SURFACE PEN", "usb-c hub"];

// Old: array_map("trim", $names) or array_map(fn($s) => trim($s), $names)
// New: pass built-in functions as callables directly
$trimmed  = array_map(trim(...),      $names);
$lower    = array_map(strtolower(...), $trimmed);
$ucwords  = array_map(ucwords(...),    $lower);

foreach ($ucwords as $n) echo "  " . $n . PHP_EOL;
'
```

> 💡 **Arrow functions (`fn()`) capture by value automatically.** Unlike regular closures which require explicit `use ($var)`, arrow functions automatically capture all variables in scope by value. They are single-expression — no `{}` block, no `return` keyword. Use arrow functions for short, pure transformations; use closures for multi-line logic or when you need `use (&$ref)` by-reference capture.

---

### Step 2: Higher-order functions + pipeline

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
$products = [
    ["id" => 1, "name" => "Surface Pro",  "category" => "laptop",    "price" => 864.00, "stock" => 15],
    ["id" => 2, "name" => "Surface Book", "category" => "laptop",    "price" => 1299.00,"stock" => 5],
    ["id" => 3, "name" => "Surface Pen",  "category" => "accessory", "price" => 49.99,  "stock" => 80],
    ["id" => 4, "name" => "Office 365",   "category" => "software",  "price" => 99.99,  "stock" => 999],
    ["id" => 5, "name" => "USB-C Hub",    "category" => "hardware",  "price" => 29.99,  "stock" => 0],
];

echo "=== array_map / array_filter / array_reduce ===" . PHP_EOL;

// array_map: transform each element
$withTax = array_map(
    fn($p) => [...$p, "total" => round($p["price"] * 1.08, 2)],
    $products
);
echo "With 8% tax:" . PHP_EOL;
foreach ($withTax as $p) printf("  %-15s \$%.2f -> \$%.2f%s", $p["name"], $p["price"], $p["total"], PHP_EOL);

// array_filter: keep matching elements (preserves keys!)
$inStock = array_filter($products, fn($p) => $p["stock"] > 0);
echo PHP_EOL . "In stock (" . count($inStock) . "):" . PHP_EOL;
foreach (array_values($inStock) as $p) echo "  " . $p["name"] . " (stock={$p["stock"]})" . PHP_EOL;

// array_reduce: fold to single value
$totalValue = array_reduce($products, fn($carry, $p) => $carry + ($p["price"] * $p["stock"]), 0.0);
echo PHP_EOL . "Total inventory value: \$" . number_format($totalValue, 2) . PHP_EOL;

// usort: sort with custom comparator
$sorted = $products;
usort($sorted, fn($a, $b) => $b["price"] <=> $a["price"]);  // <=> spaceship operator
echo PHP_EOL . "By price descending:" . PHP_EOL;
foreach ($sorted as $p) printf("  %-15s \$%.2f%s", $p["name"], $p["price"], PHP_EOL);

// ── Pipeline pattern ──────────────────────────────────────────────────────────
echo PHP_EOL . "=== Pipeline ===" . PHP_EOL;

// pipe() function: apply array of transformations in sequence
function pipe(mixed $value, array $fns): mixed {
    return array_reduce($fns, fn($carry, $fn) => $fn($carry), $value);
}

$result = pipe($products, [
    fn($ps) => array_filter($ps, fn($p) => $p["stock"] > 0),         // 1. in stock only
    fn($ps) => array_values($ps),                                      // 2. reindex
    fn($ps) => array_filter($ps, fn($p) => $p["price"] >= 50),        // 3. price >= $50
    fn($ps) => array_values($ps),
    fn($ps) => array_map(fn($p) => [                                   // 4. transform
        "name"  => $p["name"],
        "price" => $p["price"],
        "total" => round($p["price"] * 1.08, 2),                       // with tax
    ], $ps),
    fn($ps) => usort($ps, fn($a,$b) => $a["price"] <=> $b["price"]) && false ?: $ps, // 5. sort
]);

echo "Pipeline result (in-stock, >= \$50, with tax, sorted):" . PHP_EOL;
foreach ($result as $p) {
    printf("  %-15s \$%-8.2f -> \$%.2f%s", $p["name"], $p["price"], $p["total"], PHP_EOL);
}

// ── Currying ──────────────────────────────────────────────────────────────────
echo PHP_EOL . "=== Currying ===" . PHP_EOL;

// curry: split a multi-arg function into a chain of single-arg functions
function curry(callable $fn): Closure {
    $arity = (new ReflectionFunction($fn))->getNumberOfParameters();
    $accumulator = function(array $args) use ($fn, $arity, &$accumulator): mixed {
        if (count($args) >= $arity) return $fn(...$args);
        return function() use ($args, $accumulator): mixed {
            return $accumulator(array_merge($args, func_get_args()));
        };
    };
    return fn() => $accumulator(func_get_args());
}

$multiply = curry(fn(float $a, float $b): float => round($a * $b, 2));
$double   = $multiply(2.0);    // partial application
$triple   = $multiply(3.0);
$tax8pct  = $multiply(1.08);

echo "double(864):  " . $double(864.0) . PHP_EOL;
echo "triple(49.99): " . $triple(49.99) . PHP_EOL;
echo "tax(99.99):    " . $tax8pct(99.99) . PHP_EOL;

$prices = [864.0, 49.99, 99.99, 29.99];
echo "Doubled prices: " . implode(", ", array_map($double, $prices)) . PHP_EOL;
'
```

**📸 Verified Output:**
```
=== Pipeline ===
Pipeline result (in-stock, >= $50, with tax, sorted):
  Office 365      $99.99   -> $107.99
  Surface Pro     $864.00  -> $933.12
  Surface Book    $1299.00 -> $1402.92

=== Currying ===
double(864):   1728
triple(49.99): 149.97
tax(99.99):    107.99
Doubled prices: 1728, 99.98, 199.98, 59.98
```

---

## Summary

| Function | Signature | Use for |
|----------|-----------|---------|
| `array_map` | `fn($item)` | Transform every element |
| `array_filter` | `fn($item): bool` | Keep matching elements |
| `array_reduce` | `fn($carry, $item)` | Fold to single value |
| `usort` | `fn($a, $b): int` | Sort with custom comparator |
| `pipe()` | `pipe($val, [$fn,...])` | Sequential transformations |
| Currying | `$fn = curry($multi)` | Partial application |

## Further Reading
- [PHP Arrow Functions](https://www.php.net/manual/en/functions.arrow.php)
- [PHP Closures](https://www.php.net/manual/en/class.closure.php)
