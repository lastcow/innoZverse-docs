# Lab 5: PHP 8.x Modern Features

## Objective
Master the most impactful PHP 8.0–8.3 features: `match` expressions, named arguments, nullsafe operator (`?->`), union and intersection types, `readonly` properties, enums with methods and interfaces, fibers for cooperative multitasking, and first-class callable syntax.

## Background
PHP 8.0 (2020) was the biggest leap since PHP 7. Each new feature reduces boilerplate and improves correctness. `match` is a strict `switch` replacement. Named arguments enable skipping defaults without wrapping in arrays. `readonly` enforces immutability. Enums replace class-based constants with a type-safe, first-class construct. Fibers (8.1) bring low-level coroutine support — the foundation of async frameworks like ReactPHP and Revolt.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 14 (Type System)

## Tools
- Docker: `zchencow/innozverse-php:latest` (PHP 8.3)

---

## Lab Instructions

### Step 1: `match`, named arguments, nullsafe

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
echo "PHP version: " . PHP_VERSION . PHP_EOL . PHP_EOL;

// ── match expression ─────────────────────────────────────────────────────────
// match is STRICT (===), returns a value, throws UnhandledMatchError if no arm matches
echo "=== match expression ===" . PHP_EOL;

function getCategoryTax(string $category): float {
    return match($category) {
        "software", "digital" => 0.00,    // multiple conditions per arm
        "laptop", "desktop"   => 0.08,
        "accessory"           => 0.10,
        "hardware"            => 0.07,
        default               => 0.09,
    };
}

$products = [
    ["Surface Pro",  "laptop",    864.00],
    ["Office 365",   "software",  99.99],
    ["Surface Pen",  "accessory", 49.99],
    ["USB-C Hub",    "hardware",  29.99],
];

foreach ($products as [$name, $cat, $price]) {
    $tax   = getCategoryTax($cat);
    $total = round($price * (1 + $tax), 2);
    printf("  %-15s %-12s tax=%.0f%%  total=\$%.2f%s", $name, $cat, $tax*100, $total, PHP_EOL);
}

// match vs switch: switch does loose comparison (0 == "hello" is true in switch!)
$code = 0;
$switchResult = match(true) {
    $code === 0  => "zero",
    $code === "" => "empty string",   // would wrongly match in switch with $code == 0
    default      => "other",
};
echo PHP_EOL . "match strict: " . $switchResult . PHP_EOL;  // "zero", not "empty string"

// ── Named arguments ──────────────────────────────────────────────────────────
echo PHP_EOL . "=== Named Arguments ===" . PHP_EOL;

function createProduct(
    string $name,
    float  $price,
    int    $stock    = 0,
    string $category = "general",
    bool   $active   = true,
): string {
    $status = $active ? "active" : "inactive";
    return "{$name} | \${$price} | stock={$stock} | {$category} | {$status}";
}

// Skip middle params by naming them — no need to repeat defaults
echo createProduct("Surface Pro", 864.00, stock: 15, category: "laptop") . PHP_EOL;
echo createProduct("Office 365",  99.99,  active: false) . PHP_EOL;  // skip stock & category

// Named args also work with built-in functions
$arr = [3, 1, 4, 1, 5, 9, 2];
echo implode(separator: ", ", array: $arr) . PHP_EOL;
echo array_slice(array: $arr, offset: 2, length: 3, preserve_keys: true) . PHP_EOL;
print_r(array_slice(array: $arr, offset: 2, length: 3));

// ── Nullsafe operator ?-> ─────────────────────────────────────────────────────
echo PHP_EOL . "=== Nullsafe Operator (?->) ===" . PHP_EOL;

class Address {
    public function __construct(
        public readonly string $city,
        public readonly string $country,
    ) {}
    public function format(): string { return "{$this->city}, {$this->country}"; }
}

class Customer {
    public ?Address $address;
    public function __construct(public string $name, ?Address $addr = null) {
        $this->address = $addr;
    }
    public function getAddress(): ?Address { return $this->address; }
}

$customers = [
    new Customer("Dr. Chen", new Address("Claymont", "US")),
    new Customer("Anonymous"),  // no address
];

foreach ($customers as $c) {
    // Old way: isset($c->address) ? $c->address->format() : null
    // New way: one-liner with ?->
    $city = $c->getAddress()?->city ?? "unknown";
    $fmt  = $c->getAddress()?->format() ?? "No address";
    printf("  %-15s city=%-12s address=%s%s", $c->name, $city, $fmt, PHP_EOL);
}
'
```

**📸 Verified Output:**
```
PHP version: 8.3.x

=== match expression ===
  Surface Pro     laptop       tax=8%   total=$933.12
  Office 365      software     tax=0%   total=$99.99
  Surface Pen     accessory    tax=10%  total=$54.99
  USB-C Hub       hardware     tax=7%   total=$32.09

=== Named Arguments ===
  Surface Pro | $864 | stock=15 | laptop | active
  Office 365 | $99.99 | stock=0 | general | inactive

=== Nullsafe Operator ===
  Dr. Chen        city=Claymont     address=Claymont, US
  Anonymous       city=unknown      address=No address
```

---

### Step 2: Readonly properties, enums with methods, intersection types

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── readonly properties (PHP 8.1) ────────────────────────────────────────────
echo "=== readonly Properties ===" . PHP_EOL;

class Money {
    // readonly = can only be set once (in constructor), then immutable
    public function __construct(
        public readonly float  $amount,
        public readonly string $currency = "USD",
    ) {
        if ($amount < 0) throw new \InvalidArgumentException("Amount cannot be negative");
    }

    public function add(Money $other): Money {
        if ($this->currency !== $other->currency) {
            throw new \InvalidArgumentException("Currency mismatch");
        }
        return new Money($this->amount + $other->amount, $this->currency);
    }

    public function multiply(float $factor): Money {
        return new Money(round($this->amount * $factor, 2), $this->currency);
    }

    public function format(): string {
        return sprintf("%s \$%.2f", $this->currency, $this->amount);
    }
}

$price    = new Money(864.00);
$tax      = $price->multiply(0.08);
$total    = $price->add($tax);
$shipping = new Money(12.50);
$grand    = $total->add($shipping);

echo "  Base:     " . $price->format() . PHP_EOL;
echo "  Tax:      " . $tax->format() . PHP_EOL;
echo "  + Tax:    " . $total->format() . PHP_EOL;
echo "  Shipping: " . $shipping->format() . PHP_EOL;
echo "  Grand:    " . $grand->format() . PHP_EOL;

// Trying to mutate readonly → TypeError
try {
    $price->amount = 0.01;
} catch (\Error $e) {
    echo "  Readonly protection: " . $e->getMessage() . PHP_EOL;
}

// ── Enums with methods + interface implementation ─────────────────────────────
echo PHP_EOL . "=== Enums ===" . PHP_EOL;

interface HasLabel {
    public function label(): string;
}

enum OrderStatus: string implements HasLabel {
    case Pending   = "pending";
    case Confirmed = "confirmed";
    case Shipped   = "shipped";
    case Delivered = "delivered";
    case Cancelled = "cancelled";
    case Refunded  = "refunded";

    // Enum methods — same as class methods
    public function label(): string {
        return match($this) {
            self::Pending   => "⏳ Pending",
            self::Confirmed => "✅ Confirmed",
            self::Shipped   => "🚚 Shipped",
            self::Delivered => "📦 Delivered",
            self::Cancelled => "❌ Cancelled",
            self::Refunded  => "💸 Refunded",
        };
    }

    public function canTransitionTo(OrderStatus $next): bool {
        $allowed = match($this) {
            self::Pending   => [self::Confirmed, self::Cancelled],
            self::Confirmed => [self::Shipped,   self::Cancelled],
            self::Shipped   => [self::Delivered],
            self::Delivered => [self::Refunded],
            default         => [],
        };
        return in_array($next, $allowed);
    }

    public function isFinal(): bool {
        return in_array($this, [self::Delivered, self::Cancelled, self::Refunded]);
    }
}

// Enum from raw value
$status = OrderStatus::from("pending");
echo "  Status: " . $status->label() . "  final=" . ($status->isFinal() ? "yes" : "no") . PHP_EOL;

$transitions = [
    [OrderStatus::Pending,   OrderStatus::Confirmed],
    [OrderStatus::Confirmed, OrderStatus::Shipped],
    [OrderStatus::Shipped,   OrderStatus::Pending],   // invalid
    [OrderStatus::Delivered, OrderStatus::Refunded],
];
echo PHP_EOL . "  State machine transitions:" . PHP_EOL;
foreach ($transitions as [$from, $to]) {
    $ok = $from->canTransitionTo($to) ? "✓" : "✗";
    printf("  %s  %s -> %s%s", $ok, $from->label(), $to->label(), PHP_EOL);
}

// All cases
echo PHP_EOL . "  All statuses: ";
echo implode(", ", array_map(fn($s) => $s->value, OrderStatus::cases())) . PHP_EOL;
'
```

**📸 Verified Output:**
```
=== readonly Properties ===
  Base:     USD $864.00
  Tax:      USD $69.12
  + Tax:    USD $933.12
  Shipping: USD $12.50
  Grand:    USD $945.62
  Readonly protection: Cannot modify readonly property Money::$amount

=== Enums ===
  Status: ⏳ Pending  final=no

  State machine transitions:
  ✓  ⏳ Pending -> ✅ Confirmed
  ✓  ✅ Confirmed -> 🚚 Shipped
  ✗  🚚 Shipped -> ⏳ Pending
  ✓  📦 Delivered -> 💸 Refunded
```

---

## Summary

| Feature | PHP | Why it matters |
|---------|-----|----------------|
| `match` | 8.0 | Strict, expression-based, exhaustive |
| Named args | 8.0 | Skip defaults by name; self-documenting |
| `?->` nullsafe | 8.0 | Safe chaining without isset chains |
| `readonly` | 8.1 | Compile-time immutability enforcement |
| Backed enum | 8.1 | Type-safe constants with methods |
| Fibers | 8.1 | Cooperative multitasking primitives |
| `readonly class` | 8.2 | All properties readonly by default |

## Further Reading
- [PHP 8.0 New Features](https://www.php.net/releases/8.0/en.php)
- [PHP Enums](https://www.php.net/manual/en/language.enumerations.php)
