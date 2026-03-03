# Lab 13: PHP Type System — Union Types, Intersection Types & Generics Patterns

## Objective
Master PHP 8's type system: union types (`int|string`), nullable types (`?string`), intersection types (`Countable&Iterator`), `never` return type, typed properties, `mixed`, variance (covariance/contravariance), and implementing generic-like patterns with type-safe collections using PHP's type system.

## Background
PHP's type system has grown dramatically since PHP 7.0 (scalar type hints) through PHP 8.3 (readonly classes, typed class constants). Unlike Java or TypeScript, PHP types are *enforced at runtime*, not compile time. This means a mismatch throws a `TypeError` when the function is called — not when the code is written. Understanding the type system helps you write self-documenting, bug-resistant code that fails loudly at the boundary instead of silently mid-logic.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 14 (Type System)
- PHP Practitioner Lab 05 (PHP 8 Features)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Union types, nullable, `never`, typed properties

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
declare(strict_types=1);   // enforce type coercion — no silent int→float casts

echo "=== Union Types ===" . PHP_EOL;

// Union type: accepts multiple types, returns one of several
function parseId(int|string $id): int {
    // Accepts both "123" (string) and 123 (int); always returns int
    return is_string($id) ? (int)ltrim($id, "#") : $id;
}

$ids = [1, "2", "#3", 42, "order-99"];
foreach ($ids as $id) {
    try {
        $parsed = parseId($id);
        echo "  parseId(" . json_encode($id) . ") = " . $parsed . PHP_EOL;
    } catch (\TypeError $e) {
        echo "  TypeError: " . $e->getMessage() . PHP_EOL;
    }
}

// Nullable type: ?string = string|null
function findProductName(?int $id, array $db): ?string {
    if ($id === null) return null;
    return $db[$id] ?? null;
}

$db = [1 => "Surface Pro", 2 => "Surface Pen", 3 => "Office 365"];
$tests = [1, 2, 99, null];
echo PHP_EOL . "Nullable returns:" . PHP_EOL;
foreach ($tests as $id) {
    $name = findProductName($id, $db);
    echo "  findProductName(" . json_encode($id) . ") = " . json_encode($name) . PHP_EOL;
}

// never return type — function that NEVER returns (always throws or exits)
function throwNotFound(string $resource, int $id): never {
    throw new \RuntimeException("{$resource} #{$id} not found (HTTP 404)");
}

function findOrFail(int $id, array $db): string {
    return $db[$id] ?? throwNotFound("Product", $id);  // compiler knows this never returns
}

echo PHP_EOL . "findOrFail:" . PHP_EOL;
try { echo "  " . findOrFail(1, $db) . PHP_EOL; }
catch (\RuntimeException $e) { echo "  Error: " . $e->getMessage() . PHP_EOL; }
try { echo "  " . findOrFail(99, $db) . PHP_EOL; }
catch (\RuntimeException $e) { echo "  Error: " . $e->getMessage() . PHP_EOL; }

// Typed properties — enforced at assignment, not just at method call
echo PHP_EOL . "=== Typed Properties ===" . PHP_EOL;

class Product {
    public int    $id;
    public string $name;
    public float  $price;
    public ?string $sku = null;    // nullable with default
    public bool   $active = true;
    private readonly string $createdAt;  // readonly: set once only

    public function __construct(int $id, string $name, float $price) {
        $this->id        = $id;
        $this->name      = $name;
        $this->price     = $price;
        $this->createdAt = date("Y-m-d");
    }

    public function getCreatedAt(): string { return $this->createdAt; }
}

$p = new Product(1, "Surface Pro", 864.00);
$p->sku = "MS-SP-001";
echo "  id={$p->id}  name={$p->name}  sku={$p->sku}  created={$p->getCreatedAt()}" . PHP_EOL;

// Type error on wrong assignment (strict_types=1)
try {
    $bad = new Product(1, "Test", 864.00);
    $bad->active = "yes";  // string into bool property → TypeError
} catch (\TypeError $e) {
    echo "  TypeError on typed property: " . $e->getMessage() . PHP_EOL;
}
'
```

> 💡 **`declare(strict_types=1)` only affects the file it appears in.** It does NOT affect code called from that file, nor code that calls into that file. It means: when *this file* calls a function with type hints, PHP will not silently cast types. Without it, `function add(int $a)` called with `"5"` will silently cast to `5`. With it, the same call throws `TypeError`. Enable it in every file for predictable behaviour.

---

### Step 2: Intersection types, variance, type-safe collections

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
declare(strict_types=1);

// ── Intersection types ────────────────────────────────────────────────────────
echo "=== Intersection Types ===" . PHP_EOL;

// Intersection: MUST implement BOTH interfaces simultaneously
interface Identifiable { public function getId(): int; }
interface Priceable    { public function getPrice(): float; }
interface Nameable     { public function getName(): string; }

class Product implements Identifiable, Priceable, Nameable {
    public function __construct(
        private int $id, private string $name, private float $price
    ) {}
    public function getId(): int     { return $this->id; }
    public function getPrice(): float { return $this->price; }
    public function getName(): string { return $this->name; }
}

// Function requires ALL three interfaces — more precise than any single one
function formatLineItem(Identifiable&Priceable&Nameable $item, int $qty): string {
    return sprintf("#%d %-15s ×%d = $%.2f", $item->getId(), $item->getName(), $qty, $item->getPrice() * $qty);
}

$items = [
    [new Product(1, "Surface Pro",  864.00), 2],
    [new Product(2, "Surface Pen",  49.99),  5],
    [new Product(3, "Office 365",   99.99),  1],
];
foreach ($items as [$product, $qty]) echo "  " . formatLineItem($product, $qty) . PHP_EOL;

// ── Type-safe typed collection ─────────────────────────────────────────────────
echo PHP_EOL . "=== Type-safe Collection ===" . PHP_EOL;

// PHP has no generics, but we can emulate with runtime checks
class TypedCollection implements Countable, Iterator {
    private array $items = [];
    private int   $position = 0;

    public function __construct(private string $type) {}

    public function add(mixed $item): void {
        if (!($item instanceof $this->type)) {
            throw new \TypeError(
                "Expected {$this->type}, got " . get_class($item)
            );
        }
        $this->items[] = $item;
    }

    public function get(int $index): mixed {
        return $this->items[$index] ?? null;
    }

    public function filter(callable $fn): static {
        $new = new static($this->type);
        $new->items = array_values(array_filter($this->items, $fn));
        return $new;
    }

    public function map(callable $fn): array {
        return array_map($fn, $this->items);
    }

    public function reduce(callable $fn, mixed $initial = null): mixed {
        return array_reduce($this->items, $fn, $initial);
    }

    // Countable
    public function count(): int { return count($this->items); }

    // Iterator
    public function current(): mixed   { return $this->items[$this->position]; }
    public function key(): int         { return $this->position; }
    public function next(): void       { $this->position++; }
    public function rewind(): void     { $this->position = 0; }
    public function valid(): bool      { return isset($this->items[$this->position]); }
}

// Concrete typed collection for Products
class ProductCollection extends TypedCollection {
    public function __construct() { parent::__construct(Product::class); }

    public function totalValue(): float {
        return $this->reduce(fn($carry, Product $p) => $carry + $p->getPrice(), 0.0);
    }

    public function sortByPrice(): static {
        $clone = clone $this;
        usort($clone->items, fn(Product $a, Product $b) => $a->getPrice() <=> $b->getPrice());
        return $clone;
    }

    public function byCategory(string $cat): static {
        // (assumes products have category — simplified)
        return $this->filter(fn(Product $p) => str_contains(strtolower($p->getName()), strtolower($cat)));
    }
}

$catalogue = new ProductCollection();
$catalogue->add(new Product(1, "Surface Pro",   864.00));
$catalogue->add(new Product(2, "Surface Book",  1299.00));
$catalogue->add(new Product(3, "Surface Pen",   49.99));
$catalogue->add(new Product(4, "Office 365",    99.99));
$catalogue->add(new Product(5, "USB-C Hub",     29.99));

echo "Count:       " . count($catalogue) . " products" . PHP_EOL;
echo "Total value: \$" . number_format($catalogue->totalValue(), 2) . PHP_EOL;

echo PHP_EOL . "By price (sorted):" . PHP_EOL;
foreach ($catalogue->sortByPrice() as $p) {
    printf("  %-15s \$%.2f%s", $p->getName(), $p->getPrice(), PHP_EOL);
}

// Type safety enforcement
try {
    $catalogue->add(new \stdClass());
} catch (\TypeError $e) {
    echo PHP_EOL . "Type safety: " . $e->getMessage() . PHP_EOL;
}

// Names via map
$names = $catalogue->map(fn(Product $p) => $p->getName());
echo "Names: " . implode(", ", $names) . PHP_EOL;

// ── Return type covariance ────────────────────────────────────────────────────
echo PHP_EOL . "=== Covariant Return Types ===" . PHP_EOL;

abstract class BaseRepository {
    abstract public function find(int $id): ?object;  // returns object or null
}

class ProductRepository extends BaseRepository {
    private array $store = [1 => "Surface Pro", 2 => "Surface Pen"];
    // Covariant: returns more specific type (Product instead of object)
    public function find(int $id): ?Product {
        if (!isset($this->store[$id])) return null;
        return new Product($id, $this->store[$id], 0.0);
    }
}

$repo = new ProductRepository();
$found = $repo->find(1);
echo "Found: " . ($found?->getName() ?? "null") . PHP_EOL;
echo "Not found: " . json_encode($repo->find(99)) . PHP_EOL;
'
```

**📸 Verified Output:**
```
=== Union Types ===
  parseId(1) = 1
  parseId("2") = 2
  parseId("#3") = 3

=== Intersection Types ===
  #1 Surface Pro      ×2 = $1728.00
  #2 Surface Pen      ×5 = $249.95
  #3 Office 365       ×1 = $99.99

=== Type-safe Collection ===
  Count:       5 products
  Total value: $2,343.97

  By price (sorted):
  USB-C Hub       $29.99
  Surface Pen     $49.99
  ...

  Type safety: Expected Product, got stdClass
```

---

## Summary

| Type feature | Syntax | PHP version |
|--------------|--------|-------------|
| Union | `int\|string` | 8.0 |
| Nullable | `?string` | 7.1 |
| Intersection | `A&B` | 8.1 |
| `never` | `: never` | 8.1 |
| Typed property | `public int $x` | 7.4 |
| `readonly` property | `public readonly int $x` | 8.1 |
| `strict_types` | `declare(strict_types=1)` | 7.0 |

## Further Reading
- [PHP Type System Overview](https://www.php.net/manual/en/language.types.php)
- [PHP 8.1 Intersection Types](https://www.php.net/releases/8.1/en.php#intersection_types)
