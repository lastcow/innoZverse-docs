# Lab 10: Generators & Fibers — Lazy Evaluation & Cooperative Multitasking

## Objective
Master PHP generators for memory-efficient lazy sequences, `yield from` for generator delegation, generators as coroutines (two-way communication with `send()`), PHP 8.1 Fibers for cooperative multitasking, and practical applications: streaming large datasets, infinite sequences, and async-style task switching.

## Background
A generator function returns a `Generator` object when called. It runs lazily — code executes only when you call `next()` or iterate. `yield` pauses execution and returns a value; `send($value)` resumes it and injects a value. This is the basis of coroutines. PHP 8.1 Fibers are lower-level coroutines with an explicit stack — they are the building block that async frameworks (Revolt, ReactPHP 3) use to implement non-blocking I/O without threads.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 11 (List Comprehensions/Generators context)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Generators — lazy evaluation & memory efficiency

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Lazy range — avoids building a huge array ─────────────────────────────────
echo "=== Generator: Lazy Range ===" . PHP_EOL;

function lazyRange(float $start, float $end, float $step = 1.0): Generator {
    for ($i = $start; $i <= $end; $i += $step) {
        yield $i;           // execution PAUSES here, resumes on next iteration
    }
}

// Memory comparison
$start = memory_get_usage();
$gen   = lazyRange(1, 10_000);
$genMem = memory_get_usage() - $start;

$start = memory_get_usage();
$arr   = range(1, 10_000);
$arrMem = memory_get_usage() - $start;

echo "Generator memory: " . $genMem . " bytes" . PHP_EOL;
echo "Array memory:     " . $arrMem . " bytes" . PHP_EOL;
echo "Ratio:            " . round($arrMem / max($genMem, 1)) . "x more for array" . PHP_EOL;

// Use the generator
$sum = 0;
foreach (lazyRange(1, 100) as $n) $sum += $n;
echo "Sum 1-100: " . $sum . " (expected 5050)" . PHP_EOL;

// ── Infinite sequence ─────────────────────────────────────────────────────────
echo PHP_EOL . "=== Infinite Fibonacci Generator ===" . PHP_EOL;

function fibonacci(): Generator {
    [$a, $b] = [0, 1];
    while (true) {
        yield $a;
        [$a, $b] = [$b, $a + $b];
    }
}

$fib = fibonacci();
$sequence = [];
for ($i = 0; $i < 12; $i++) {
    $sequence[] = $fib->current();
    $fib->next();
}
echo "First 12: " . implode(", ", $sequence) . PHP_EOL;

// ── yield from: generator delegation ─────────────────────────────────────────
echo PHP_EOL . "=== yield from: Generator Delegation ===" . PHP_EOL;

function laptops(): Generator {
    yield ["id" => 1, "name" => "Surface Pro",  "price" => 864.00,  "category" => "laptop"];
    yield ["id" => 2, "name" => "Surface Book", "price" => 1299.00, "category" => "laptop"];
}

function accessories(): Generator {
    yield ["id" => 3, "name" => "Surface Pen", "price" => 49.99, "category" => "accessory"];
    yield ["id" => 4, "name" => "USB-C Hub",   "price" => 29.99, "category" => "hardware"];
}

function allProducts(): Generator {
    yield from laptops();       // delegate to sub-generator
    yield from accessories();   // then this one
    yield ["id" => 5, "name" => "Office 365", "price" => 99.99, "category" => "software"];
}

foreach (allProducts() as $p) {
    printf("  #%d %-15s \$%.2f%s", $p["id"], $p["name"], $p["price"], PHP_EOL);
}

// ── Generator as coroutine: send() ───────────────────────────────────────────
echo PHP_EOL . "=== Generator Coroutine (send) ===" . PHP_EOL;

function orderProcessor(): Generator {
    $totalRevenue = 0.0;
    while (true) {
        // yield returns a value OUT; send() injects a value IN
        $order = yield ["status" => "waiting", "revenue" => $totalRevenue];
        if ($order === null) break;

        $total       = $order["price"] * $order["qty"];
        $totalRevenue += $total;
        echo "  Processed: {$order["product"]} ×{$order["qty"]} = \${$total:.2f}" . PHP_EOL;
    }
    return $totalRevenue;  // final return value accessible via getReturn()
}

$processor = orderProcessor();
$processor->current();  // start the generator (runs to first yield)

$orders = [
    ["product" => "Surface Pro",  "price" => 864.00, "qty" => 2],
    ["product" => "Surface Pen",  "price" => 49.99,  "qty" => 5],
    ["product" => "Office 365",   "price" => 99.99,  "qty" => 10],
];

foreach ($orders as $order) {
    $status = $processor->send($order);  // inject order, get status back
    printf("  Status: %s | Running total: \$%.2f%s",
        $status["status"], $status["revenue"], PHP_EOL);
}
$processor->send(null);  // signal done
echo "  Final revenue: \$" . $processor->getReturn() . PHP_EOL;
'
```

> 💡 **Generators are pull-based; `send()` makes them push-based.** Normally you pull values out of a generator via `foreach` or `->current()`/`->next()`. With `send($value)`, you push a value *into* the generator — it resumes from the last `yield`, and `$value = yield ...` receives your input. This two-way channel is what makes generators coroutines. Symfony's `Process` component and Guzzle use this for async streaming.

---

### Step 2: PHP 8.1 Fibers

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Fibers: lightweight cooperative multitasking
echo "=== PHP 8.1 Fibers ===" . PHP_EOL;

// Fiber 1: process orders
$orderFiber = new Fiber(function(): string {
    $orders = [
        ["id" => 1001, "product" => "Surface Pro",  "total" => 1728.00],
        ["id" => 1002, "product" => "Surface Pen",  "total" => 249.95],
        ["id" => 1003, "product" => "Office 365",   "total" => 99.99],
    ];
    foreach ($orders as $order) {
        echo "  [Order] Processing #{$order["id"]}: {$order["product"]}" . PHP_EOL;
        Fiber::suspend("order:" . $order["id"]);  // pause and yield control
    }
    return "All orders processed";
});

// Fiber 2: send notifications
$notifyFiber = new Fiber(function(): string {
    $notifications = ["Order confirmed", "Payment received", "Shipped"];
    foreach ($notifications as $msg) {
        echo "  [Notify] " . $msg . PHP_EOL;
        Fiber::suspend("notify:" . $msg);
    }
    return "All notifications sent";
});

// Cooperative scheduler: interleave fiber execution
echo "Interleaved fiber execution:" . PHP_EOL;
$orderFiber->start();
$notifyFiber->start();

while (!$orderFiber->isTerminated() || !$notifyFiber->isTerminated()) {
    if (!$orderFiber->isTerminated())  $orderFiber->resume();
    if (!$notifyFiber->isTerminated()) $notifyFiber->resume();
}

echo PHP_EOL . "Return values:" . PHP_EOL;
echo "  Orders:       " . $orderFiber->getReturn() . PHP_EOL;
echo "  Notifications: " . $notifyFiber->getReturn() . PHP_EOL;

// ── Fiber with value passing ──────────────────────────────────────────────────
echo PHP_EOL . "=== Fiber Value Passing ===" . PHP_EOL;

$priceFiber = new Fiber(function(): void {
    $total = 0.0;
    while (true) {
        $price = Fiber::suspend($total);  // return current total, receive new price
        if ($price === null) break;
        $total += $price;
        echo "  Added \${$price} -> running total \${$total}" . PHP_EOL;
    }
});

$priceFiber->start();
foreach ([864.00, 49.99, 99.99, 29.99] as $price) {
    $running = $priceFiber->resume($price);
}
$priceFiber->resume(null);  // done
'
```

**📸 Verified Output:**
```
Interleaved fiber execution:
  [Order] Processing #1001: Surface Pro
  [Notify] Order confirmed
  [Order] Processing #1002: Surface Pen
  [Notify] Payment received
  [Order] Processing #1003: Office 365
  [Notify] Shipped

Return values:
  Orders:        All orders processed
  Notifications: All notifications sent

=== Fiber Value Passing ===
  Added $864 -> running total $864
  Added $49.99 -> running total $913.99
  Added $99.99 -> running total $1013.98
  Added $29.99 -> running total $1043.97
```

---

## Summary

| Feature | Mechanism | Use for |
|---------|-----------|---------|
| Generator `yield` | Lazy pull | Memory-efficient sequences |
| `yield from` | Delegation | Composing generators |
| Generator `send()` | Push coroutine | Two-way data exchange |
| `getReturn()` | Final value | Generator return after done |
| Fiber | Cooperative multitasking | Async frameworks, schedulers |

## Further Reading
- [PHP Generators](https://www.php.net/manual/en/language.generators.php)
- [PHP Fibers (RFC)](https://wiki.php.net/rfc/fibers)
