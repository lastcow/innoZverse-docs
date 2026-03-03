# Lab 7: OOP — Classes, Objects & Encapsulation

## Objective
Design PHP classes with properties, constructors, methods, access modifiers, readonly properties, and enums. Apply encapsulation, constructor promotion, and static members.

## Background
PHP has first-class OOP support since PHP 5, with major modernization in PHP 7.4 (typed properties), PHP 8.0 (constructor promotion, match, attributes), and PHP 8.1 (enums, readonly, intersection types). Modern PHP OOP is clean and expressive — Laravel, Symfony, and WordPress are all built on it.

## Time
40 minutes

## Prerequisites
- Lab 05 (Functions)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Classes & Constructor Promotion

```php
<?php
declare(strict_types=1);

class BankAccount {
    // Constructor promotion (PHP 8.0) — declare + assign in one
    public function __construct(
        private readonly string $accountId,
        private string          $owner,
        private float           $balance = 0.0,
        private int             $txnCount = 0,
    ) {}

    public function deposit(float $amount): void {
        if ($amount <= 0) throw new InvalidArgumentException("Deposit must be positive");
        $this->balance  += $amount;
        $this->txnCount++;
    }

    public function withdraw(float $amount): void {
        if ($amount <= 0) throw new InvalidArgumentException("Must be positive");
        if ($amount > $this->balance) throw new \RuntimeException("Insufficient funds");
        $this->balance  -= $amount;
        $this->txnCount++;
    }

    public function getBalance(): float  { return $this->balance; }
    public function getOwner(): string   { return $this->owner; }
    public function getTxnCount(): int   { return $this->txnCount; }
    public function getAccountId(): string { return $this->accountId; }

    public function __toString(): string {
        return sprintf("Account[%s, %s, $%.2f, %d txns]",
            $this->accountId, $this->owner, $this->balance, $this->txnCount);
    }
}

$acct = new BankAccount('ACC-001', 'Dr. Chen', 1000.0);
$acct->deposit(500);
$acct->withdraw(200);
echo $acct . "\n";
echo "Balance: $" . $acct->getBalance() . "\n";

try { $acct->withdraw(10000); }
catch (\RuntimeException $e) { echo "Error: " . $e->getMessage() . "\n"; }
```

> 💡 **Constructor promotion** (PHP 8.0) eliminates boilerplate: `private string $name` in the constructor parameter list simultaneously declares the property and assigns the argument. `readonly` (PHP 8.1) makes a property writable only in the constructor — perfect for value objects.

**📸 Verified Output:**
```
Account[ACC-001, Dr. Chen, $1300.00, 2 txns]
Balance: $1300
Error: Insufficient funds
```

---

### Step 2: Enums (PHP 8.1)

```php
<?php
declare(strict_types=1);

// Pure enum
enum Status {
    case Pending;
    case Active;
    case Suspended;
    case Closed;

    public function label(): string {
        return match($this) {
            Status::Pending   => '⏳ Pending',
            Status::Active    => '✅ Active',
            Status::Suspended => '⚠️  Suspended',
            Status::Closed    => '❌ Closed',
        };
    }

    public function isActive(): bool {
        return $this === Status::Active;
    }
}

// Backed enum (has scalar value)
enum Priority: int {
    case Low    = 1;
    case Medium = 5;
    case High   = 10;
    case Critical = 100;

    public function label(): string {
        return $this->name . " (P{$this->value})";
    }
}

enum HttpMethod: string {
    case GET    = 'GET';
    case POST   = 'POST';
    case PUT    = 'PUT';
    case DELETE = 'DELETE';
}

// Usage
$status = Status::Active;
echo $status->label() . "\n";
echo "isActive: " . ($status->isActive() ? 'yes' : 'no') . "\n";

// Backed enum — from value
$p = Priority::from(10);
echo $p->label() . "\n";
echo "Value: " . $p->value . "\n";
echo "Name: "  . $p->name . "\n";

// tryFrom — no exception on bad value
$method = HttpMethod::tryFrom('PATCH');
echo "PATCH: " . ($method?->value ?? 'not found') . "\n";

// List all cases
echo "\nAll priorities:\n";
foreach (Priority::cases() as $case) {
    echo "  " . $case->label() . "\n";
}
```

> 💡 **PHP Enums** (8.1) are first-class types — not just constants. Pure enums are for semantic labels; backed enums carry a `string` or `int` value for serialization. They can implement interfaces, have methods, and work with `match` exhaustiveness checks. Use them instead of `const PENDING = 1` patterns.

**📸 Verified Output:**
```
✅ Active
isActive: yes
High (P10)
Value: 10
Name: High

PATCH: not found

All priorities:
  Low (P1)
  Medium (P5)
  High (P10)
  Critical (P100)
```

---

### Step 3: Readonly Properties & Value Objects

```php
<?php
declare(strict_types=1);

// Value object — immutable, equality by value
class Money {
    public function __construct(
        public readonly float  $amount,
        public readonly string $currency,
    ) {
        if ($amount < 0) throw new \InvalidArgumentException("Amount cannot be negative");
        if (strlen($currency) !== 3) throw new \InvalidArgumentException("Currency must be 3 chars");
    }

    public function add(Money $other): self {
        if ($this->currency !== $other->currency)
            throw new \LogicException("Cannot add different currencies");
        return new self($this->amount + $other->amount, $this->currency);
    }

    public function multiply(float $factor): self {
        return new self(round($this->amount * $factor, 2), $this->currency);
    }

    public function equals(Money $other): bool {
        return $this->amount === $other->amount && $this->currency === $other->currency;
    }

    public function __toString(): string {
        return number_format($this->amount, 2) . ' ' . $this->currency;
    }
}

$price    = new Money(864.00, 'USD');
$tax      = $price->multiply(0.08);
$shipping = new Money(0.00, 'USD');
$total    = $price->add($tax)->add($shipping);

echo "Price:    $price\n";
echo "Tax:      $tax\n";
echo "Shipping: $shipping\n";
echo "Total:    $total\n";

echo "\nEquals check: " . ($price->equals(new Money(864.00, 'USD')) ? 'yes' : 'no') . "\n";

// Readonly prevents modification
try {
    $price->amount = 0; // TypeError
} catch (\Error $e) {
    echo "Readonly blocked: " . $e->getMessage() . "\n";
}
```

> 💡 **Value objects are immutable** — operations return new instances instead of modifying state. `Money::add()` returns a new `Money`, leaving the originals unchanged. This prevents subtle bugs where shared money objects are accidentally modified. Readonly properties enforce immutability at the language level.

**📸 Verified Output:**
```
Price:    864.00 USD
Tax:      69.12 USD
Shipping: 0.00 USD
Total:    933.12 USD

Equals check: yes
Readonly blocked: Cannot modify readonly property Money::$amount
```

---

### Step 4: Static Members & Singleton

```php
<?php
declare(strict_types=1);

class Registry {
    private static ?self $instance = null;
    private array $data = [];
    private static int $instanceCount = 0;

    private function __construct() {
        self::$instanceCount++;
    }

    public static function getInstance(): self {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    public function set(string $key, mixed $value): void {
        $this->data[$key] = $value;
    }

    public function get(string $key, mixed $default = null): mixed {
        return $this->data[$key] ?? $default;
    }

    public static function getInstanceCount(): int {
        return self::$instanceCount;
    }
}

// Same instance every time
$r1 = Registry::getInstance();
$r2 = Registry::getInstance();

$r1->set('app.name', 'innoZverse');
$r1->set('app.version', '1.0');

echo $r2->get('app.name') . "\n";    // r1 and r2 are the same object
echo $r2->get('app.version') . "\n";
echo "Same instance: " . ($r1 === $r2 ? 'yes' : 'no') . "\n";
echo "Instances created: " . Registry::getInstanceCount() . "\n";

// Static factory methods
class Color {
    private function __construct(
        public readonly int $r,
        public readonly int $g,
        public readonly int $b,
    ) {}

    public static function fromHex(string $hex): self {
        $hex = ltrim($hex, '#');
        return new self(
            hexdec(substr($hex, 0, 2)),
            hexdec(substr($hex, 2, 2)),
            hexdec(substr($hex, 4, 2)),
        );
    }

    public static function fromRgb(int $r, int $g, int $b): self {
        return new self($r, $g, $b);
    }

    public function toHex(): string {
        return sprintf('#%02x%02x%02x', $this->r, $this->g, $this->b);
    }

    public function __toString(): string {
        return "rgb({$this->r}, {$this->g}, {$this->b})";
    }
}

$blue = Color::fromHex('#0078d4');
$red  = Color::fromRgb(255, 0, 0);
echo "\n$blue → " . $blue->toHex() . "\n";
echo "$red\n";
```

> 💡 **Static factory methods** (named constructors) are more expressive than constructors: `Color::fromHex('#ff0000')` and `Color::fromRgb(255,0,0)` both create the same type but communicate intent. They also allow caching — `Color::fromHex` could return a cached instance. Prefer them over multiple constructors.

**📸 Verified Output:**
```
innoZverse
1.0
Same instance: yes
Instances created: 1

rgb(0, 120, 212) → #0078d4
rgb(255, 0, 0)
```

---

### Step 5: Magic Methods

```php
<?php
declare(strict_types=1);

class DynamicObject {
    private array $properties = [];
    private array $callLog    = [];

    public function __get(string $name): mixed {
        return $this->properties[$name] ?? null;
    }

    public function __set(string $name, mixed $value): void {
        $this->properties[$name] = $value;
    }

    public function __isset(string $name): bool {
        return isset($this->properties[$name]);
    }

    public function __unset(string $name): void {
        unset($this->properties[$name]);
    }

    public function __call(string $name, array $args): mixed {
        $this->callLog[] = "$name(" . implode(', ', $args) . ")";
        return "Called $name with " . count($args) . " args";
    }

    public static function __callStatic(string $name, array $args): string {
        return "Static::$name()";
    }

    public function __toString(): string {
        return "DynamicObject(" . implode(', ', array_map(
            fn($k, $v) => "$k=$v",
            array_keys($this->properties),
            $this->properties
        )) . ")";
    }

    public function getCallLog(): array { return $this->callLog; }
}

$obj = new DynamicObject();
$obj->name = "PHP Magic";
$obj->version = 8.3;
echo "name: {$obj->name}\n";
echo "isset version: " . (isset($obj->version) ? 'yes' : 'no') . "\n";

echo $obj->doSomething('a', 'b') . "\n";
echo $obj->calculate(1, 2, 3) . "\n";
echo DynamicObject::staticMethod() . "\n";
echo $obj . "\n";
echo "Call log: " . implode(', ', $obj->getCallLog()) . "\n";
```

> 💡 **Magic methods** start with `__` and are called implicitly by PHP. `__get`/`__set` intercept property access, `__call` intercepts method calls on undefined methods. They power Laravel's Eloquent ORM (model attributes), PHP's proxy patterns, and dynamic API clients. Use them thoughtfully — they can hide bugs.

**📸 Verified Output:**
```
name: PHP Magic
isset version: yes
Called doSomething with 2 args
Called calculate with 3 args
Static::staticMethod()
DynamicObject(name=PHP Magic, version=8.3)
Call log: doSomething(a, b), calculate(1, 2, 3)
```

---

### Step 6: Traits

```php
<?php
declare(strict_types=1);

trait Timestampable {
    private ?string $createdAt = null;
    private ?string $updatedAt = null;

    public function touch(): void {
        $now = date('Y-m-d H:i:s');
        if ($this->createdAt === null) $this->createdAt = $now;
        $this->updatedAt = $now;
    }

    public function getCreatedAt(): ?string { return $this->createdAt; }
    public function getUpdatedAt(): ?string { return $this->updatedAt; }
}

trait SoftDeletable {
    private ?string $deletedAt = null;

    public function delete(): void { $this->deletedAt = date('Y-m-d H:i:s'); }
    public function restore(): void { $this->deletedAt = null; }
    public function isDeleted(): bool { return $this->deletedAt !== null; }
}

trait Serializable2 {
    public function toArray(): array {
        return get_object_vars($this);
    }

    public function toJson(): string {
        return json_encode($this->toArray(), JSON_PRETTY_PRINT);
    }
}

class Post {
    use Timestampable, SoftDeletable, Serializable2;

    public function __construct(
        public readonly int    $id,
        public string          $title,
        public string          $content,
    ) {
        $this->touch();
    }
}

$post = new Post(1, 'Hello PHP 8', 'Content here...');
echo "Created: " . $post->getCreatedAt() . "\n";
echo "Deleted: " . ($post->isDeleted() ? 'yes' : 'no') . "\n";

$post->delete();
echo "Deleted: " . ($post->isDeleted() ? 'yes' : 'no') . "\n";

$post->restore();
$post->title = "Updated Title";
$post->touch();
echo "Updated: " . $post->getUpdatedAt() . "\n";
```

> 💡 **Traits** are "horizontal code reuse" — they inject methods and properties into classes without inheritance. A class can `use` multiple traits (unlike `extends` which is single). Use traits for cross-cutting concerns: logging, timestamps, soft delete, caching. Prefer interfaces + traits over deep inheritance hierarchies.

**📸 Verified Output:**
```
Created: 2026-03-02 14:30:00
Deleted: no
Deleted: yes
Updated: 2026-03-02 14:30:00
```

---

### Step 7: Interfaces & Abstract Classes in OOP

```php
<?php
declare(strict_types=1);

interface Renderable {
    public function render(): string;
}

interface Validatable {
    public function validate(): array; // returns error messages
    public function isValid(): bool;
}

abstract class FormField implements Renderable, Validatable {
    protected array $errors = [];

    public function __construct(
        protected string  $name,
        protected mixed   $value = null,
        protected bool    $required = false,
    ) {}

    public function isValid(): bool {
        $this->errors = $this->validate();
        return empty($this->errors);
    }

    abstract public function render(): string;
    abstract public function validate(): array;
}

class TextField extends FormField {
    public function __construct(
        string $name,
        mixed $value = null,
        bool $required = false,
        private int $minLength = 0,
        private int $maxLength = 255,
    ) {
        parent::__construct($name, $value, $required);
    }

    public function render(): string {
        $val = htmlspecialchars((string)($this->value ?? ''));
        return "<input type=\"text\" name=\"{$this->name}\" value=\"$val\">";
    }

    public function validate(): array {
        $errors = [];
        if ($this->required && empty($this->value))
            $errors[] = "{$this->name} is required";
        if (!empty($this->value) && strlen($this->value) < $this->minLength)
            $errors[] = "{$this->name} must be at least {$this->minLength} chars";
        return $errors;
    }
}

class EmailField extends FormField {
    public function render(): string {
        return "<input type=\"email\" name=\"{$this->name}\" value=\"{$this->value}\">";
    }

    public function validate(): array {
        $errors = [];
        if ($this->required && empty($this->value)) $errors[] = "Email required";
        if (!empty($this->value) && !filter_var($this->value, FILTER_VALIDATE_EMAIL))
            $errors[] = "Invalid email format";
        return $errors;
    }
}

$fields = [
    new TextField('username', '', required: true, minLength: 3),
    new EmailField('email', 'bad-email', required: true),
    new TextField('bio', 'A PHP developer', required: false),
];

foreach ($fields as $field) {
    $valid = $field->isValid();
    echo $field->render() . "\n";
    if (!$valid) echo "  Errors: " . implode(', ', $field->validate()) . "\n";
}
```

> 💡 **Abstract classes provide a template** — they can have concrete methods (shared implementation) and abstract methods (required overrides). Use abstract classes when subclasses share code; use interfaces when you only need to enforce a contract. A class can implement multiple interfaces but extend only one abstract class.

**📸 Verified Output:**
```
<input type="text" name="username" value="">
  Errors: username is required
<input type="email" name="email" value="bad-email">
  Errors: Invalid email format
<input type="text" name="bio" value="A PHP developer">
```

---

### Step 8: Complete Example — Product Catalog

```php
<?php
declare(strict_types=1);

enum ProductStatus: string {
    case Active   = 'active';
    case Inactive = 'inactive';
    case OutOfStock = 'out_of_stock';
}

class Product {
    private static int $nextId = 1;

    public readonly int $id;
    private ProductStatus $status;

    public function __construct(
        public readonly string $name,
        public readonly string $category,
        private float          $price,
        private int            $stock,
    ) {
        $this->id     = self::$nextId++;
        $this->status = $stock > 0 ? ProductStatus::Active : ProductStatus::OutOfStock;
    }

    public function getPrice(): float  { return $this->price; }
    public function getStock(): int    { return $this->stock; }
    public function getStatus(): ProductStatus { return $this->status; }

    public function applyDiscount(float $pct): void {
        $this->price = round($this->price * (1 - $pct / 100), 2);
    }

    public function restock(int $qty): void {
        $this->stock  += $qty;
        $this->status  = ProductStatus::Active;
    }

    public function __toString(): string {
        return sprintf("#%d %-20s %-12s $%7.2f  %-12s (stock: %d)",
            $this->id, $this->name, $this->category,
            $this->price, $this->status->value, $this->stock);
    }
}

$products = [
    new Product('Surface Pro 12"', 'Laptop',    864.00, 15),
    new Product('Surface Pen',     'Accessory',  49.99, 80),
    new Product('USB-C Hub',       'Accessory',  29.99,  0),
    new Product('Office 365',      'Software',   99.99, 999),
];

echo "=== Product Catalog ===\n";
foreach ($products as $p) echo $p . "\n";

// Apply 10% discount to accessories
echo "\n=== After 10% discount on Accessories ===\n";
foreach ($products as $p) {
    if ($p->category === 'Accessory') $p->applyDiscount(10);
    echo $p . "\n";
}

// Restock out-of-stock
$usbHub = array_values(array_filter($products, fn($p) => $p->name === 'USB-C Hub'))[0];
$usbHub->restock(50);
echo "\nUSB-C Hub restocked: " . $usbHub . "\n";
```

> 💡 **`self::$nextId++`** in the constructor auto-increments a class-level counter — each new Product gets a unique ID without a database. This is the in-memory auto-increment pattern. In production, IDs come from a database sequence, but this pattern is useful for tests and prototypes.

**📸 Verified Output:**
```
=== Product Catalog ===
#1 Surface Pro 12"      Laptop       $ 864.00  active       (stock: 15)
#2 Surface Pen          Accessory    $  49.99  active       (stock: 80)
#3 USB-C Hub            Accessory    $  29.99  out_of_stock (stock: 0)
#4 Office 365           Software     $  99.99  active       (stock: 999)

=== After 10% discount on Accessories ===
#1 Surface Pro 12"      Laptop       $ 864.00  active       (stock: 15)
#2 Surface Pen          Accessory    $  44.99  active       (stock: 80)
#3 USB-C Hub            Accessory    $  26.99  out_of_stock (stock: 0)
#4 Office 365           Software     $  99.99  active       (stock: 999)

USB-C Hub restocked: #3 USB-C Hub            Accessory    $  26.99  active       (stock: 50)
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
enum Color { case Red; case Green; case Blue; }
\$c = Color::Green;
echo \$c->name . PHP_EOL;
"
```

## Summary

PHP 8 OOP is modern and expressive. You've covered constructor promotion, readonly properties, enums, value objects, static members, magic methods, traits, and a full product catalog. These patterns are exactly what you'll find in Laravel, Symfony, and every professional PHP codebase.

## Further Reading
- [PHP 8.1 Enums](https://www.php.net/manual/en/language.enumerations.php)
- [PHP Traits](https://www.php.net/manual/en/language.oop5.traits.php)
- [Constructor Promotion](https://www.php.net/manual/en/language.oop5.decon.php)
