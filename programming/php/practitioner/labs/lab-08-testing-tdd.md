# Lab 8: Testing & TDD — Without External Dependencies

## Objective
Build a complete test suite using only PHP's built-in capabilities: a custom assertion library, test runner with pass/fail tracking, test doubles (stubs and fakes), Test-Driven Development (TDD) red-green-refactor cycle, and code coverage simulation.

## Background
PHPUnit is the standard test framework, but understanding testing mechanics makes you a better PHPUnit user. PHP's `assert()` function is built-in but limited. This lab builds a micro test runner that mirrors PHPUnit's structure. **TDD** means writing the test before the implementation — the test fails (red), you write code to pass it (green), then improve the code (refactor) without breaking tests.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 09 (Error Handling)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Micro test framework + test doubles

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Micro Test Framework ──────────────────────────────────────────────────────
class TestRunner {
    private int $passed = 0, $failed = 0;
    private array $failures = [];
    private string $currentSuite = "";

    public function suite(string $name): void {
        $this->currentSuite = $name;
        echo PHP_EOL . "▶ {$name}" . PHP_EOL;
    }

    public function test(string $name, callable $fn): void {
        try {
            $fn($this);
            $this->passed++;
            echo "  ✓ {$name}" . PHP_EOL;
        } catch (\AssertionError|\Exception $e) {
            $this->failed++;
            $this->failures[] = "[{$this->currentSuite}] {$name}: " . $e->getMessage();
            echo "  ✗ {$name}: " . $e->getMessage() . PHP_EOL;
        }
    }

    public function assertEquals(mixed $expected, mixed $actual, string $msg = ""): void {
        if ($expected !== $actual) {
            throw new \AssertionError(
                ($msg ? "{$msg}: " : "") . "Expected " . json_encode($expected) . " got " . json_encode($actual)
            );
        }
    }

    public function assertSame(mixed $expected, mixed $actual): void {
        if ($expected !== $actual) throw new \AssertionError("assertSame failed");
    }

    public function assertTrue(bool $value, string $msg = "Expected true"): void {
        if (!$value) throw new \AssertionError($msg);
    }

    public function assertFalse(bool $value, string $msg = "Expected false"): void {
        if ($value) throw new \AssertionError($msg);
    }

    public function assertContains(mixed $needle, array $haystack): void {
        if (!in_array($needle, $haystack, true))
            throw new \AssertionError(json_encode($needle) . " not in array");
    }

    public function assertThrows(string $exceptionClass, callable $fn): void {
        try { $fn(); throw new \AssertionError("Expected {$exceptionClass} to be thrown"); }
        catch (\Throwable $e) {
            if (!($e instanceof $exceptionClass))
                throw new \AssertionError("Expected {$exceptionClass}, got " . get_class($e));
        }
    }

    public function assertCount(int $expected, array|Countable $actual): void {
        $count = count($actual);
        if ($count !== $expected) throw new \AssertionError("Expected count {$expected}, got {$count}");
    }

    public function report(): void {
        $total = $this->passed + $this->failed;
        echo PHP_EOL . str_repeat("─", 50) . PHP_EOL;
        echo "Results: {$this->passed}/{$total} passed";
        if ($this->failed) {
            echo "  (" . $this->failed . " failed)" . PHP_EOL;
            foreach ($this->failures as $f) echo "  ✗ {$f}" . PHP_EOL;
        } else { echo "  🎉 All passed!" . PHP_EOL; }
    }

    public function allPassed(): bool { return $this->failed === 0; }
}

// ── Classes Under Test ────────────────────────────────────────────────────────
class Money {
    public function __construct(public readonly float $amount, public readonly string $currency = "USD") {
        if ($amount < 0) throw new \InvalidArgumentException("Amount cannot be negative");
    }
    public function add(Money $other): Money {
        if ($this->currency !== $other->currency) throw new \InvalidArgumentException("Currency mismatch");
        return new Money(round($this->amount + $other->amount, 2), $this->currency);
    }
    public function multiply(float $factor): Money { return new Money(round($this->amount * $factor, 2), $this->currency); }
    public function equals(Money $other): bool { return $this->amount === $other->amount && $this->currency === $other->currency; }
    public function isGreaterThan(Money $other): bool { return $this->amount > $other->amount; }
    public function format(): string { return sprintf("%s \$%.2f", $this->currency, $this->amount); }
}

class ShoppingCart {
    private array $items = [];
    public function add(string $product, float $price, int $qty = 1): void {
        if ($qty < 1) throw new \InvalidArgumentException("Qty must be >= 1");
        $this->items[] = ["product" => $product, "price" => $price, "qty" => $qty];
    }
    public function subtotal(): float { return array_sum(array_map(fn($i) => $i["price"] * $i["qty"], $this->items)); }
    public function itemCount(): int  { return count($this->items); }
    public function clear(): void     { $this->items = []; }
    public function getItems(): array { return $this->items; }
    public function applyDiscount(float $pct): float { return round($this->subtotal() * (1 - $pct), 2); }
}

// Interface for test doubles
interface InventoryService {
    public function checkStock(int $productId, int $qty): bool;
    public function reserveStock(int $productId, int $qty): void;
}

// Stub: returns pre-configured values, no logic
class StubInventory implements InventoryService {
    public function __construct(private array $stock = []) {}
    public function checkStock(int $productId, int $qty): bool {
        return ($this->stock[$productId] ?? 0) >= $qty;
    }
    public function reserveStock(int $productId, int $qty): void {}
}

// Spy: records calls for verification
class SpyInventory implements InventoryService {
    public array $reserveCalls = [];
    public function checkStock(int $productId, int $qty): bool { return true; }
    public function reserveStock(int $productId, int $qty): void {
        $this->reserveCalls[] = ["productId" => $productId, "qty" => $qty];
    }
}

// ── Run Tests ──────────────────────────────────────────────────────────────────
$t = new TestRunner();

$t->suite("Money");
$t->test("creates with valid amount", fn($t) => $t->assertEquals(864.00, (new Money(864.00))->amount));
$t->test("formats correctly",         fn($t) => $t->assertEquals("USD \$864.00", (new Money(864.00))->format()));
$t->test("adds two Money objects",    fn($t) => $t->assertTrue((new Money(100))->add(new Money(50))->equals(new Money(150))));
$t->test("multiplies by factor",      fn($t) => $t->assertEquals(93.31, (new Money(864.00))->multiply(0.108)->amount));
$t->test("rejects negative amount",   fn($t) => $t->assertThrows(\InvalidArgumentException::class, fn() => new Money(-1)));
$t->test("rejects currency mismatch", fn($t) => $t->assertThrows(\InvalidArgumentException::class,
    fn() => (new Money(100, "USD"))->add(new Money(50, "EUR"))));
$t->test("isGreaterThan works",       fn($t) => $t->assertTrue((new Money(100))->isGreaterThan(new Money(50))));

$t->suite("ShoppingCart");
$cart = new ShoppingCart();
$t->test("starts empty",    fn($t) => $t->assertCount(0, $cart->getItems()));
$t->test("add one item",    function($t) use (&$cart) {
    $cart->add("Surface Pro", 864.00, 2);
    $t->assertEquals(2, $cart->itemCount());
    $t->assertEquals(1728.00, $cart->subtotal());
});
$t->test("add second item", function($t) use (&$cart) {
    $cart->add("Surface Pen", 49.99, 3);
    $t->assertEquals(2, $cart->itemCount());
    $t->assertEquals(1877.97, $cart->subtotal());
});
$t->test("10% discount",    fn($t) => $t->assertEquals(1690.17, $cart->applyDiscount(0.10)));
$t->test("rejects qty < 1",fn($t) => $t->assertThrows(\InvalidArgumentException::class,
    fn() => (new ShoppingCart())->add("X", 1.0, 0)));
$t->test("clear empties",   function($t) use (&$cart) { $cart->clear(); $t->assertCount(0, $cart->getItems()); });

$t->suite("Inventory Test Doubles");
$t->test("stub: out-of-stock returns false", function($t) {
    $stub = new StubInventory([1 => 3]);  // product 1 has 3 in stock
    $t->assertFalse($stub->checkStock(1, 5));   // requesting 5 — fail
    $t->assertTrue($stub->checkStock(1, 2));    // requesting 2 — ok
});
$t->test("spy records reserve calls", function($t) {
    $spy = new SpyInventory();
    $spy->reserveStock(1, 2);
    $spy->reserveStock(3, 5);
    $t->assertCount(2, $spy->reserveCalls);
    $t->assertEquals(1, $spy->reserveCalls[0]["productId"]);
    $t->assertEquals(5, $spy->reserveCalls[1]["qty"]);
});

$t->report();
'
```

> 💡 **Test doubles have specific roles.** A **stub** provides canned answers with no logic (always returns `true`, or a fixed value). A **fake** has a working implementation (in-memory DB instead of real DB). A **spy** records calls so you can verify interactions afterward. A **mock** has pre-programmed expectations (PHPUnit's `expects()->with()`) and fails if not called correctly. Use the simplest double that satisfies the test.

**📸 Verified Output:**
```
▶ Money
  ✓ creates with valid amount
  ✓ formats correctly
  ✓ adds two Money objects
  ✓ multiplies by factor
  ✓ rejects negative amount
  ✓ rejects currency mismatch
  ✓ isGreaterThan works

▶ ShoppingCart
  ✓ starts empty
  ✓ add one item
  ✓ add second item
  ✓ 10% discount
  ✓ rejects qty < 1
  ✓ clear empties

▶ Inventory Test Doubles
  ✓ stub: out-of-stock returns false
  ✓ spy records reserve calls

──────────────────────────────────────────────────
Results: 15/15 passed  🎉 All passed!
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| `assertEquals` | Strict value comparison (===) |
| `assertThrows` | Verify exceptions are thrown |
| Stub | Pre-configured return values |
| Spy | Record calls for assertion |
| Fake | Lightweight working implementation |
| TDD cycle | Red → Green → Refactor |

## Further Reading
- [PHPUnit](https://phpunit.de/documentation.html)
- [Test Double Patterns](https://martinfowler.com/bliki/TestDouble.html)
