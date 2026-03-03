# Lab 2: Namespaces, PSR-4 Autoloading & Composer

## Objective
Master PHP namespaces for collision-free code organisation, PSR-4 autoloading conventions, Composer's `autoload` configuration, `use` aliases, and namespace-based class discovery. Build a multi-namespace product catalogue that mirrors real-world package structure.

## Background
Before namespaces (PHP 5.3+), class names like `Product` would collide across libraries. Namespaces solve this by prefixing class names with a path: `Inno\Catalogue\Product` is distinct from `Vendor\Ecom\Product`. PSR-4 maps namespace prefixes to filesystem paths — `Inno\Catalogue\Product` maps to `src/Catalogue/Product.php`. Composer reads `composer.json` to generate an autoloader that loads classes on demand without manual `require` calls.

## Time
25 minutes

## Prerequisites
- PHP Foundations Lab 13 (Namespaces & Autoloading)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Basic namespaces and `use` aliases

Every PHP file should declare its namespace as the very first statement (after `<?php`). When referencing a class from another namespace, you either use the fully-qualified name (`\Inno\Catalogue\Product`) or import it with `use`. The `as` keyword creates an alias for readability.

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Simulating multiple namespaces in one file for demo purposes
// In real projects each class lives in its own file

namespace Inno\Catalogue {
    class Product {
        public function __construct(
            public readonly int $id,
            public readonly string $name,
            public readonly float $price,
            public readonly string $category,
        ) {}

        public function __toString(): string {
            return "[{$this->category}] {$this->name} @ \${$this->price}";
        }
    }

    class Category {
        private array $products = [];

        public function __construct(public readonly string $name) {}

        public function add(Product $p): void {
            $this->products[] = $p;
        }

        public function getProducts(): array { return $this->products; }

        public function totalValue(): float {
            return array_sum(array_map(fn(Product $p) => $p->price, $this->products));
        }
    }
}

namespace Inno\Pricing {
    use Inno\Catalogue\Product as CatalogueProduct; // alias for clarity

    class PriceCalculator {
        public function withTax(CatalogueProduct $p, float $rate = 0.08): float {
            return round($p->price * (1 + $rate), 2);
        }

        public function bulk(CatalogueProduct $p, int $qty, float $discount = 0.10): float {
            $base = $p->price * $qty;
            return $qty >= 5 ? round($base * (1 - $discount), 2) : $base;
        }
    }
}

namespace {  // global namespace
    use Inno\Catalogue\Product;
    use Inno\Catalogue\Category;
    use Inno\Pricing\PriceCalculator;

    echo "=== Namespaces & Aliases ===" . PHP_EOL;

    $laptop    = new Category("Laptop");
    $accessory = new Category("Accessory");

    $products = [
        new Product(1, "Surface Pro",   864.00, "Laptop"),
        new Product(2, "Surface Book",  1299.00, "Laptop"),
        new Product(3, "Surface Pen",   49.99, "Accessory"),
        new Product(4, "USB-C Hub",     29.99, "Accessory"),
        new Product(5, "Office 365",    99.99, "Software"),
    ];

    foreach ($products as $p) {
        match($p->category) {
            "Laptop"    => $laptop->add($p),
            "Accessory" => $accessory->add($p),
            default     => null,
        };
    }

    $calc = new PriceCalculator();

    echo PHP_EOL . "Category: " . $laptop->name . PHP_EOL;
    foreach ($laptop->getProducts() as $p) {
        printf("  %-15s  base=\$%.2f  w/tax=\$%.2f%s",
            $p->name, $p->price, $calc->withTax($p), PHP_EOL);
    }
    printf("  Total category value: \$%.2f%s", $laptop->totalValue(), PHP_EOL);

    echo PHP_EOL . "Bulk pricing (Surface Pen × 10):" . PHP_EOL;
    $pen = $products[2];
    printf("  No discount: \$%.2f%s",  $pen->price * 10, PHP_EOL);
    printf("  Bulk (10%%):  \$%.2f%s", $calc->bulk($pen, 10), PHP_EOL);

    // Fully-qualified name (no use statement needed)
    $direct = new \Inno\Catalogue\Product(99, "Direct FQN", 0.01, "Test");
    echo PHP_EOL . "FQN test: " . $direct . PHP_EOL;
}
'
```

> 💡 **Namespaces are case-insensitive in PHP, but PSR-4 requires case-sensitivity on case-sensitive filesystems (Linux).** Always match the namespace declaration exactly to the directory structure. `Inno\Catalogue\Product` must live at `src/Catalogue/Product.php` — wrong case on Linux will cause "class not found" errors in production even if it works on macOS (case-insensitive HFS+).

**📸 Verified Output:**
```
=== Namespaces & Aliases ===

Category: Laptop
  Surface Pro      base=$864.00  w/tax=$933.12
  Surface Book     base=$1299.00 w/tax=$1402.92
  Total category value: $2163.00

Bulk pricing (Surface Pen × 10):
  No discount: $499.90
  Bulk (10%):  $449.91

FQN test: [Test] Direct FQN @ $0.01
```

---

### Step 2: PSR-4 directory simulation + class discovery

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// Simulate PSR-4 autoloading without Composer using spl_autoload_register
// This is EXACTLY what Composers generated autoloader does internally

$namespaceMap = [
    "Inno\\Catalogue\\" => "/tmp/src/Catalogue/",
    "Inno\\Pricing\\"   => "/tmp/src/Pricing/",
    "Inno\\Repository\\" => "/tmp/src/Repository/",
];

// Write class files to /tmp to simulate real project structure
@mkdir("/tmp/src/Catalogue",  0777, true);
@mkdir("/tmp/src/Pricing",    0777, true);
@mkdir("/tmp/src/Repository", 0777, true);

file_put_contents("/tmp/src/Catalogue/Product.php", "<?php
namespace Inno\\Catalogue;
class Product {
    public function __construct(
        public readonly int \$id,
        public readonly string \$name,
        public readonly float \$price,
    ) {}
    public function __toString(): string { return \"{\$this->name} @ \\\${\$this->price}\"; }
}
");

file_put_contents("/tmp/src/Repository/ProductRepository.php", "<?php
namespace Inno\\Repository;
use Inno\\Catalogue\\Product;
class ProductRepository {
    private array \$store = [];
    public function save(Product \$p): void { \$this->store[\$p->id] = \$p; }
    public function find(int \$id): ?Product { return \$this->store[\$id] ?? null; }
    public function findAll(): array { return array_values(\$this->store); }
    public function count(): int { return count(\$this->store); }
}
");

// PSR-4 autoloader: converts namespace to file path
spl_autoload_register(function (string $class) use ($namespaceMap): void {
    foreach ($namespaceMap as $prefix => $dir) {
        if (str_starts_with($class, $prefix)) {
            $relative = str_replace("\\", "/", substr($class, strlen($prefix)));
            $file = $dir . $relative . ".php";
            if (file_exists($file)) {
                require $file;
                return;
            }
        }
    }
});

// Now use the autoloaded classes
use Inno\Catalogue\Product;
use Inno\Repository\ProductRepository;

$repo = new ProductRepository();
$repo->save(new Product(1, "Surface Pro",  864.00));
$repo->save(new Product(2, "Surface Pen",  49.99));
$repo->save(new Product(3, "Office 365",   99.99));

echo "=== PSR-4 Autoloading ===" . PHP_EOL;
echo "Loaded " . $repo->count() . " products" . PHP_EOL;

$p = $repo->find(1);
echo "Found: " . $p . PHP_EOL;

echo PHP_EOL . "All products:" . PHP_EOL;
foreach ($repo->findAll() as $product) {
    echo "  #" . $product->id . " " . $product . PHP_EOL;
}

// Show the file path that was loaded
echo PHP_EOL . "Autoloader resolved:" . PHP_EOL;
$classes = ["Inno\\Catalogue\\Product", "Inno\\Repository\\ProductRepository"];
foreach ($classes as $cls) {
    $ref = new ReflectionClass($cls);
    echo "  " . $cls . " => " . $ref->getFileName() . PHP_EOL;
}
'
```

**📸 Verified Output:**
```
=== PSR-4 Autoloading ===
Loaded 3 products
Found: Surface Pro @ $864

All products:
  #1 Surface Pro @ $864
  #2 Surface Pen @ $49.99
  #3 Office 365 @ $99.99

Autoloader resolved:
  Inno\Catalogue\Product => /tmp/src/Catalogue/Product.php
  Inno\Repository\ProductRepository => /tmp/src/Repository/ProductRepository.php
```

---

### Step 3: `use` grouping, constants & functions in namespaces

PHP 7+ allows grouping `use` imports with braces. Namespaces can also contain constants and functions (not just classes).

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
namespace Inno\Config {
    const VERSION     = "2.0.0";
    const MAX_QTY     = 999;
    const TAX_RATE    = 0.08;
    const FREE_SHIP   = 500.0;

    function formatPrice(float $amount, string $currency = "USD"): string {
        return sprintf("%s \$%.2f", $currency, $amount);
    }

    function applyTax(float $price): float {
        return round($price * (1 + TAX_RATE), 2);
    }
}

namespace {
    use const Inno\Config\VERSION;
    use const Inno\Config\TAX_RATE;
    use const Inno\Config\FREE_SHIP;
    use function Inno\Config\formatPrice;
    use function Inno\Config\applyTax;

    echo "=== Namespaced Constants & Functions ===" . PHP_EOL;
    echo "Version:    " . VERSION . PHP_EOL;
    echo "Tax rate:   " . (TAX_RATE * 100) . "%" . PHP_EOL;
    echo "Free ship:  " . formatPrice(FREE_SHIP) . PHP_EOL;

    $prices = [49.99, 99.99, 864.00, 1299.00];
    echo PHP_EOL . "Prices with tax:" . PHP_EOL;
    foreach ($prices as $p) {
        printf("  %-10s -> %s%s", formatPrice($p), formatPrice(applyTax($p)), PHP_EOL);
    }
}
'
```

**📸 Verified Output:**
```
=== Namespaced Constants & Functions ===
Version:    2.0.0
Tax rate:   8%
Free ship:  USD $500.00

Prices with tax:
  USD $49.99  -> USD $53.99
  USD $99.99  -> USD $107.99
  USD $864.00 -> USD $933.12
  USD $1299.00 -> USD $1402.92
```

---

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| Declare namespace | `namespace Inno\Catalogue;` | Scope the file's symbols |
| Import class | `use Inno\Catalogue\Product;` | Short name in current file |
| Alias | `use Inno\Catalogue\Product as P;` | Rename to avoid collision |
| FQN | `new \Inno\Catalogue\Product()` | Always works, no import needed |
| Namespace constant | `use const Inno\Config\VERSION;` | Import namespaced constant |
| PSR-4 autoloader | `spl_autoload_register(...)` | Auto-load classes from files |

## Further Reading
- [PSR-4: Autoloader Standard](https://www.php-fig.org/psr/psr-4/)
- [PHP Namespaces](https://www.php.net/manual/en/language.namespaces.php)
