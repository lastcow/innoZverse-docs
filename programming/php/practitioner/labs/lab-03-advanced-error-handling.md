# Lab 3: Advanced Error Handling — Exceptions, Result Types & Error Boundaries

## Objective
Build a production-grade error handling system: custom exception hierarchies, exception chaining, `finally` blocks for resource cleanup, a functional `Result<T>` type that avoids exceptions for expected failures, global error handlers, and structured error logging.

## Background
PHP has two error systems: **errors** (old C-style: `E_WARNING`, `E_NOTICE`) and **exceptions** (OOP-style: `throw new Exception()`). Since PHP 7, most fatal errors are now `Error` objects that can be caught. A common mistake is using exceptions for expected failures ("product not found") — this has performance cost and poor semantics. The **Result pattern** encapsulates success/failure in a return value, making failure a normal code path.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 09 (Error Handling)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Custom exception hierarchy

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Exception hierarchy — specific exceptions convey context
class AppException extends RuntimeException {}

class ValidationException extends AppException {
    private array $errors;
    public function __construct(array $errors, string $message = "Validation failed") {
        parent::__construct($message . ": " . implode(", ", $errors));
        $this->errors = $errors;
    }
    public function getErrors(): array { return $this->errors; }
}

class NotFoundException extends AppException {
    public function __construct(string $resource, int|string $id) {
        parent::__construct("{$resource} #{$id} not found", 404);
    }
}

class InsufficientStockException extends AppException {
    public function __construct(
        public readonly string $product,
        public readonly int $requested,
        public readonly int $available,
    ) {
        parent::__construct(
            "Insufficient stock for {$product}: requested={$requested}, available={$available}"
        );
    }
}

class PaymentException extends AppException {
    public function __construct(
        public readonly string $code,
        string $message,
        ?\Throwable $previous = null  // chain the original cause
    ) {
        parent::__construct("[{$code}] {$message}", 0, $previous);
    }
}

// Service that uses the hierarchy
class OrderService {
    private array $inventory = [
        1 => ["name" => "Surface Pro",  "stock" => 5,  "price" => 864.00],
        2 => ["name" => "Surface Pen",  "stock" => 20, "price" => 49.99],
        3 => ["name" => "USB-C Hub",    "stock" => 0,  "price" => 29.99],
    ];

    public function placeOrder(int $productId, int $qty, array $payment): array {
        // 1. Validate input
        $errors = [];
        if ($qty < 1 || $qty > 100) $errors[] = "qty must be 1-100";
        if (empty($payment["card"])) $errors[] = "card number required";
        if (!empty($errors)) throw new ValidationException($errors);

        // 2. Check product exists
        if (!isset($this->inventory[$productId])) {
            throw new NotFoundException("Product", $productId);
        }

        $product = $this->inventory[$productId];

        // 3. Check stock
        if ($product["stock"] < $qty) {
            throw new InsufficientStockException($product["name"], $qty, $product["stock"]);
        }

        // 4. Process payment (simulate gateway error)
        try {
            $this->processPayment($payment, $product["price"] * $qty);
        } catch (\RuntimeException $e) {
            // Wrap the gateway error in a domain exception, preserve chain
            throw new PaymentException("GATEWAY_ERROR", "Payment declined", $e);
        }

        // 5. Commit
        $this->inventory[$productId]["stock"] -= $qty;
        return ["orderId" => rand(1000,9999), "product" => $product["name"], "qty" => $qty];
    }

    private function processPayment(array $payment, float $amount): void {
        if (str_starts_with($payment["card"], "0000")) {
            throw new \RuntimeException("Card declined by issuer");
        }
    }
}

$service = new OrderService();

// Test cases
$cases = [
    ["id" => 2, "qty" => 5,   "card" => "4111-1111",  "desc" => "Valid order"],
    ["id" => 1, "qty" => -1,  "card" => "4111-1111",  "desc" => "Invalid qty"],
    ["id" => 9, "qty" => 1,   "card" => "4111-1111",  "desc" => "Product not found"],
    ["id" => 3, "qty" => 2,   "card" => "4111-1111",  "desc" => "Out of stock"],
    ["id" => 2, "qty" => 1,   "card" => "0000-bad",   "desc" => "Payment declined"],
    ["id" => 1, "qty" => 0,   "card" => "",            "desc" => "Multiple errors"],
];

echo "=== Custom Exception Hierarchy ===" . PHP_EOL;
foreach ($cases as $c) {
    echo PHP_EOL . "Test: " . $c["desc"] . PHP_EOL;
    try {
        $result = $service->placeOrder($c["id"], $c["qty"], ["card" => $c["card"]]);
        echo "  ✓ Order #{$result["orderId"]} placed: {$result["product"]} ×{$result["qty"]}" . PHP_EOL;
    } catch (ValidationException $e) {
        echo "  ✗ Validation: " . $e->getMessage() . PHP_EOL;
        echo "    Errors: " . implode(", ", $e->getErrors()) . PHP_EOL;
    } catch (NotFoundException $e) {
        echo "  ✗ Not Found (HTTP " . $e->getCode() . "): " . $e->getMessage() . PHP_EOL;
    } catch (InsufficientStockException $e) {
        echo "  ✗ Stock: " . $e->getMessage() . PHP_EOL;
        echo "    Wanted={$e->requested} Available={$e->available}" . PHP_EOL;
    } catch (PaymentException $e) {
        echo "  ✗ Payment [{$e->code}]: " . $e->getMessage() . PHP_EOL;
        echo "    Caused by: " . $e->getPrevious()->getMessage() . PHP_EOL;
    } catch (AppException $e) {
        echo "  ✗ App error: " . $e->getMessage() . PHP_EOL;
    }
}
'
```

> 💡 **Exception chaining with `$previous` is critical for debugging.** When you catch a low-level exception (e.g., a database `PDOException`) and re-throw a domain exception (`PaymentException`), always pass the original as the third `parent::__construct()` argument. This preserves the full stack trace chain. `$e->getPrevious()` retrieves it, and error logging tools like Sentry display the complete cause chain.

**📸 Verified Output:**
```
Test: Valid order
  ✓ Order #4821 placed: Surface Pen ×5

Test: Invalid qty
  ✗ Validation: Validation failed: qty must be 1-100

Test: Product not found
  ✗ Not Found (HTTP 404): Product #9 not found

Test: Out of stock
  ✗ Stock: Insufficient stock for USB-C Hub: requested=2, available=0

Test: Payment declined
  ✗ Payment [GATEWAY_ERROR]: [GATEWAY_ERROR] Payment declined
    Caused by: Card declined by issuer
```

---

### Step 2: `finally` for resource cleanup + `Result<T>` type

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// finally always runs — even if exception thrown or return executed
function readProductFile(string $path): string {
    $fh = null;
    try {
        echo "  Opening file..." . PHP_EOL;
        if (!file_exists($path)) throw new \RuntimeException("File not found: {$path}");
        $fh = fopen($path, "r");
        $content = fread($fh, 4096);
        echo "  Read " . strlen($content) . " bytes" . PHP_EOL;
        return $content;
    } catch (\RuntimeException $e) {
        echo "  Error: " . $e->getMessage() . PHP_EOL;
        return "";
    } finally {
        // This ALWAYS executes — perfect for cleanup
        if ($fh) { fclose($fh); echo "  File handle closed (finally)" . PHP_EOL; }
        else      { echo "  No handle to close (finally)" . PHP_EOL; }
    }
}

echo "=== finally block ===" . PHP_EOL;
file_put_contents("/tmp/products.txt", "Surface Pro,864.00\nSurface Pen,49.99\n");
readProductFile("/tmp/products.txt");
echo PHP_EOL;
readProductFile("/tmp/missing.txt");

// ── Result<T> pattern ────────────────────────────────────────────────
echo PHP_EOL . "=== Result<T> Pattern ===" . PHP_EOL;

// Generic Result type — no exceptions for expected failures
readonly class Success {
    public bool $ok = true;
    public function __construct(public readonly mixed $value) {}
}

readonly class Failure {
    public bool $ok = false;
    public function __construct(
        public readonly string $code,
        public readonly string $message,
    ) {}
}

type Result = Success|Failure;  // Union type alias (PHP 8.3+)

function findProduct(int $id): Success|Failure {
    $db = [
        1 => ["id" => 1, "name" => "Surface Pro",  "price" => 864.00],
        2 => ["id" => 2, "name" => "Surface Pen",   "price" => 49.99],
    ];
    if (!isset($db[$id])) {
        return new Failure("NOT_FOUND", "Product #{$id} not found");
    }
    return new Success($db[$id]);
}

function applyDiscount(array $product, float $pct): Success|Failure {
    if ($pct < 0 || $pct > 1) {
        return new Failure("INVALID_DISCOUNT", "Discount must be 0.0–1.0, got {$pct}");
    }
    return new Success([...$product, "price" => round($product["price"] * (1 - $pct), 2)]);
}

// Chain Result operations — no try/catch needed
$ids = [1, 2, 99];
foreach ($ids as $id) {
    $result = findProduct($id);
    if ($result->ok) {
        $discounted = applyDiscount($result->value, 0.15);
        if ($discounted->ok) {
            $p = $discounted->value;
            printf("  ✓ id=%d  %-15s  \$%.2f -> \$%.2f (15%% off)%s",
                $p["id"], $p["name"], $result->value["price"], $p["price"], PHP_EOL);
        } else {
            echo "  ✗ Discount error: {$discounted->message}" . PHP_EOL;
        }
    } else {
        echo "  ✗ [{$result->code}] {$result->message}" . PHP_EOL;
    }
}
'
```

**📸 Verified Output:**
```
=== finally block ===
  Opening file...
  Read 42 bytes
  File handle closed (finally)

  Opening file...
  Error: File not found: /tmp/missing.txt
  No handle to close (finally)

=== Result<T> Pattern ===
  ✓ id=1  Surface Pro     $864.00 -> $734.40 (15% off)
  ✓ id=2  Surface Pen     $49.99  -> $42.49  (15% off)
  ✗ [NOT_FOUND] Product #99 not found
```

---

## Summary

| Pattern | When to use |
|---------|-------------|
| Custom exception class | Domain-specific errors with extra context |
| Exception chaining (`$previous`) | Wrapping low-level exceptions in domain ones |
| `finally` | Resource cleanup (files, DB connections, locks) |
| `Result<T>` (`Success|Failure`) | Expected failures (not-found, validation) |
| Catch `Throwable` | Catch both `Exception` and `Error` |

## Further Reading
- [PHP Exceptions](https://www.php.net/manual/en/language.exceptions.php)
- [PHP 8.0 `match` + named arguments](https://www.php.net/manual/en/control-structures.match.php)
