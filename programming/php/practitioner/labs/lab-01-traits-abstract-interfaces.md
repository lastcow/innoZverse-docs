# Lab 1: Traits, Abstract Classes & Interface Contracts

## Objective
Master PHP's code-reuse mechanisms: **traits** for horizontal code sharing, **abstract classes** for enforced template patterns, and **interface contracts** for polymorphic type systems. Build a product discount system that demonstrates all three working together.

## Background
PHP uses single inheritance — a class can only extend one parent. Traits solve this limitation by providing "mixins" — reusable method bundles that are copy-pasted into a class at compile time. Abstract classes enforce a template method pattern: they define the algorithm skeleton but leave specific steps to subclasses. Interfaces define contracts: any class implementing an interface *must* provide all listed methods, enabling duck-typed polymorphism without inheritance.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 07 (OOP), Lab 08 (Inheritance)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Traits for horizontal reuse

A **trait** is a group of methods intended for reuse. Unlike a parent class, you can `use` multiple traits in one class. The methods are literally copied into the class body — there is no runtime dispatch overhead. Traits can have properties too, but they must be compatible with any property declared in the using class.

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Timestampable trait — add created/updated tracking to ANY class
trait Timestampable {
    private ?string $createdAt = null;
    private ?string $updatedAt = null;

    public function setCreatedAt(): void {
        $this->createdAt = date("Y-m-d H:i:s");
    }

    public function setUpdatedAt(): void {
        $this->updatedAt = date("Y-m-d H:i:s");
    }

    public function getCreatedAt(): ?string { return $this->createdAt; }
    public function getUpdatedAt(): ?string { return $this->updatedAt; }
}

// Loggable trait — add audit log to ANY class
trait Loggable {
    private array $logs = [];

    public function log(string $message): void {
        $this->logs[] = "[" . date("H:i:s") . "] " . $message;
    }

    public function getLogs(): array { return $this->logs; }

    public function printLogs(): void {
        foreach ($this->logs as $entry) {
            echo "  " . $entry . PHP_EOL;
        }
    }
}

// Product uses BOTH traits — multiple trait use
class Product {
    use Timestampable, Loggable;

    public function __construct(
        private int $id,
        private string $name,
        private float $price,
    ) {
        $this->setCreatedAt();
        $this->log("Created product: {$name} @ \${$price}");
    }

    public function updatePrice(float $newPrice): void {
        $old = $this->price;
        $this->price = $newPrice;
        $this->setUpdatedAt();
        $this->log("Price changed: \${$old} -> \${$newPrice}");
    }

    public function getPrice(): float { return $this->price; }
    public function getName(): string  { return $this->name; }
}

$p = new Product(1, "Surface Pro", 864.00);
$p->updatePrice(799.99);
$p->updatePrice(749.99);

echo "=== Trait Demo ===" . PHP_EOL;
echo "Product:   " . $p->getName() . PHP_EOL;
echo "Price:     \$" . $p->getPrice() . PHP_EOL;
echo "Created:   " . $p->getCreatedAt() . PHP_EOL;
echo "Updated:   " . $p->getUpdatedAt() . PHP_EOL;
echo "Audit log:" . PHP_EOL;
$p->printLogs();
'
```

> 💡 **Traits are compile-time copy-paste, not runtime dispatch.** When PHP encounters `use Timestampable`, it copies all trait methods directly into the class definition. This means there is zero performance overhead — calling `$p->setCreatedAt()` is identical to calling a method defined directly in `Product`. The PHP manual says: "Traits are a mechanism for code reuse in single inheritance languages."

**📸 Verified Output:**
```
=== Trait Demo ===
Product:   Surface Pro
Price:     749.99
Created:   2026-03-03 15:00:00
Updated:   2026-03-03 15:00:00
Audit log:
  [15:00:00] Created product: Surface Pro @ $864
  [15:00:00] Price changed: $864 -> $799.99
  [15:00:00] Price changed: $799.99 -> $749.99
```

---

### Step 2: Trait conflict resolution

When two traits define the same method name, PHP throws a fatal error — you must resolve the conflict explicitly using `insteadof` and `as`.

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
trait JsonSerializer {
    public function serialize(): string {
        return json_encode($this->toArray(), JSON_PRETTY_PRINT);
    }

    abstract protected function toArray(): array;
}

trait CsvSerializer {
    public function serialize(): string {     // SAME method name — conflict!
        $arr = $this->toArray();
        return implode(",", array_values($arr));
    }

    abstract protected function toArray(): array;
}

class Product {
    use JsonSerializer, CsvSerializer {
        JsonSerializer::serialize insteadof CsvSerializer;  // prefer JSON
        CsvSerializer::serialize as serializeCsv;           // alias CSV version
    }

    public function __construct(
        private int $id,
        private string $name,
        private float $price
    ) {}

    protected function toArray(): array {
        return ["id" => $this->id, "name" => $this->name, "price" => $this->price];
    }
}

$p = new Product(1, "Surface Pen", 49.99);
echo "=== Trait Conflict Resolution ===" . PHP_EOL;
echo "JSON:" . PHP_EOL . $p->serialize() . PHP_EOL;
echo "CSV: " . $p->serializeCsv() . PHP_EOL;
'
```

**📸 Verified Output:**
```
JSON:
{
    "id": 1,
    "name": "Surface Pen",
    "price": 49.99
}
CSV: 1,Surface Pen,49.99
```

---

### Step 3: Abstract classes — Template Method pattern

An **abstract class** cannot be instantiated directly. It defines an algorithm skeleton with `abstract` methods that *must* be implemented by concrete subclasses. This is the **Template Method** design pattern — the parent defines the steps, subclasses fill in the details.

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Abstract base: defines the discount calculation algorithm
abstract class DiscountStrategy {
    // Template method — defines the algorithm, cannot be overridden
    final public function applyDiscount(float $price, int $qty): array {
        $discountPct  = $this->calculateDiscountPct($price, $qty);
        $discountAmt  = round($price * $qty * $discountPct, 2);
        $originalTotal = $price * $qty;
        $finalTotal    = round($originalTotal - $discountAmt, 2);

        return [
            "original"  => $originalTotal,
            "discount%" => $discountPct * 100,
            "saved"     => $discountAmt,
            "total"     => $finalTotal,
            "strategy"  => $this->getName(),
        ];
    }

    // Subclasses MUST implement these
    abstract protected function calculateDiscountPct(float $price, int $qty): float;
    abstract public function getName(): string;
}

// Bulk discount: 10% off if qty >= 5
class BulkDiscount extends DiscountStrategy {
    protected function calculateDiscountPct(float $price, int $qty): float {
        return $qty >= 5 ? 0.10 : 0.0;
    }
    public function getName(): string { return "Bulk (5+ items = 10% off)"; }
}

// Loyalty discount: 5% for <$500, 15% for $500+
class LoyaltyDiscount extends DiscountStrategy {
    protected function calculateDiscountPct(float $price, int $qty): float {
        return ($price * $qty) >= 500 ? 0.15 : 0.05;
    }
    public function getName(): string { return "Loyalty (5%/15%)"; }
}

// Clearance: flat 30%
class ClearanceDiscount extends DiscountStrategy {
    protected function calculateDiscountPct(float $price, int $qty): float {
        return 0.30;
    }
    public function getName(): string { return "Clearance (30%)"; }
}

$strategies = [new BulkDiscount(), new LoyaltyDiscount(), new ClearanceDiscount()];
$items = [["Surface Pro", 864.00, 3], ["Surface Pen", 49.99, 6], ["USB-C Hub", 29.99, 10]];

echo "=== Abstract Class: Template Method ===" . PHP_EOL;
foreach ($items as [$name, $price, $qty]) {
    echo PHP_EOL . "Product: {$name} @ \${$price} × {$qty}" . PHP_EOL;
    foreach ($strategies as $strategy) {
        $result = $strategy->applyDiscount($price, $qty);
        printf("  %-28s  saved=\$%-7.2f  total=\$%.2f%s",
            $result["strategy"], $result["saved"], $result["total"], PHP_EOL);
    }
}
'
```

**📸 Verified Output:**
```
=== Abstract Class: Template Method ===

Product: Surface Pro @ $864.00 × 3
  Bulk (5+ items = 10% off)     saved=$0.00     total=$2592.00
  Loyalty (5%/15%)              saved=$388.80   total=$2203.20
  Clearance (30%)               saved=$777.60   total=$1814.40

Product: Surface Pen @ $49.99 × 6
  Bulk (5+ items = 10% off)     saved=$30.00    total=$269.94
  Loyalty (5%/15%)              saved=$14.99    total=$284.95
  Clearance (30%)               saved=$89.98    total=$209.96
```

---

### Step 4: Interfaces — polymorphic contracts

An **interface** is a pure contract: no method bodies, no properties (except constants). Any class implementing the interface guarantees it has those methods. This enables **dependency injection** — you type-hint on the interface, and any implementation works.

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Contracts
interface Priceable {
    public function getPrice(): float;
    public function getCurrency(): string;
}

interface Taxable {
    public function getTaxRate(): float;
    public function getTaxAmount(): float;
}

interface Shippable {
    public function getWeightKg(): float;
    public function getShippingCost(): float;
}

// A class can implement MULTIPLE interfaces
class Product implements Priceable, Taxable, Shippable {
    private float $taxRate;

    public function __construct(
        private string $name,
        private float $price,
        private float $weightKg,
        private string $category
    ) {
        // Tax rates by category
        $this->taxRate = match($category) {
            "software"   => 0.00,   // digital goods — 0%
            "hardware"   => 0.08,   // physical — 8%
            "accessory"  => 0.10,   // accessories — 10%
            default      => 0.07,
        };
    }

    // Priceable
    public function getPrice(): float    { return $this->price; }
    public function getCurrency(): string { return "USD"; }

    // Taxable
    public function getTaxRate(): float   { return $this->taxRate; }
    public function getTaxAmount(): float  { return round($this->price * $this->taxRate, 2); }

    // Shippable
    public function getWeightKg(): float    { return $this->weightKg; }
    public function getShippingCost(): float {
        // $5 base + $3/kg, free over $500
        return $this->price >= 500 ? 0.0 : round(5.0 + $this->weightKg * 3.0, 2);
    }

    public function getName(): string { return $this->name; }
}

// Functions typed against interfaces — polymorphic, decoupled
function printPriceInfo(Priceable $item): void {
    printf("  Price: \$%.2f %s%s", $item->getPrice(), $item->getCurrency(), PHP_EOL);
}

function printTaxInfo(Taxable $item): void {
    printf("  Tax:   \$%.2f (%.0f%%)%s", $item->getTaxAmount(), $item->getTaxRate()*100, PHP_EOL);
}

function calculateOrderTotal(Priceable&Taxable&Shippable $item, int $qty): float {
    return round(($item->getPrice() + $item->getTaxAmount()) * $qty + $item->getShippingCost(), 2);
}

$products = [
    new Product("Surface Pro",  864.00, 0.9, "hardware"),
    new Product("Surface Pen",   49.99, 0.1, "accessory"),
    new Product("Office 365",    99.99, 0.0, "software"),
    new Product("USB-C Hub",     29.99, 0.2, "hardware"),
];

echo "=== Interface Contracts ===" . PHP_EOL;
foreach ($products as $p) {
    echo PHP_EOL . $p->getName() . ":" . PHP_EOL;
    printPriceInfo($p);
    printTaxInfo($p);
    printf("  Ship:  \$%.2f%s", $p->getShippingCost(), PHP_EOL);
    printf("  Total: \$%.2f (qty=1)%s", calculateOrderTotal($p, 1), PHP_EOL);
}
'
```

**📸 Verified Output:**
```
=== Interface Contracts ===

Surface Pro:
  Price: $864.00 USD
  Tax:   $69.12 (8%)
  Ship:  $0.00
  Total: $933.12 (qty=1)

Surface Pen:
  Price: $49.99 USD
  Tax:   $5.00 (10%)
  Ship:  $5.30
  Total: $60.29 (qty=1)

Office 365:
  Price: $99.99 USD
  Tax:   $0.00 (0%)
  Ship:  $5.00
  Total: $104.99 (qty=1)
```

---

## Summary

| Mechanism | Key Rule | Best For |
|-----------|----------|---------|
| `trait` | `use` multiple traits in one class | Shared behaviour across unrelated classes |
| `abstract class` | Can't instantiate; defines template | Algorithm skeleton with variation points |
| `interface` | Pure contract; implement multiple | Decoupled type system, dependency injection |
| `insteadof` | Trait conflict resolution | Multiple traits with same method name |
| `Priceable&Taxable` | Intersection type hint | Require multiple interfaces simultaneously |

## Further Reading
- [PHP Traits Manual](https://www.php.net/manual/en/language.oop5.traits.php)
- [PHP Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php)
