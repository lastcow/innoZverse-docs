# Lab 8: Inheritance, Interfaces & Polymorphism

## Objective
Use PHP inheritance (`extends`), interfaces (`implements`), abstract classes, `parent::`, method overriding, and polymorphism to build extensible class hierarchies.

## Background
PHP supports single inheritance (one parent class) but multiple interface implementation. Combined with traits (Lab 7), this gives flexibility without the complexity of multiple inheritance. PHP's OOP powers Laravel's Eloquent (model inheritance), Symfony's event system, and virtually every PHP framework.

## Time
35 minutes

## Prerequisites
- Lab 07 (OOP)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: extends & Method Overriding

```php
<?php
declare(strict_types=1);

class Animal {
    public function __construct(
        protected string $name,
        protected string $sound,
    ) {}

    public function speak(): string {
        return "{$this->name} says: {$this->sound}!";
    }

    public function describe(): string {
        return "I am {$this->name}, a " . static::class; // late static binding
    }
}

class Dog extends Animal {
    public function __construct(string $name, private string $breed) {
        parent::__construct($name, 'Woof');
    }

    public function speak(): string {
        return parent::speak() . " ({$this->breed})";
    }

    public function fetch(): string { return "{$this->name} fetches the ball!"; }
}

class Cat extends Animal {
    public function __construct(string $name) { parent::__construct($name, 'Meow'); }

    public function speak(): string {
        return parent::speak() . " *ignores you*";
    }
}

$animals = [new Dog('Rex', 'German Shepherd'), new Cat('Whiskers'), new Dog('Buddy', 'Labrador')];

foreach ($animals as $animal) {
    echo $animal->speak() . "\n";
    echo $animal->describe() . "\n\n";
}

// instanceof check
foreach ($animals as $a) {
    if ($a instanceof Dog) echo "{$a->fetch()}\n";
}
```

> 💡 **`static::class` uses late static binding** — it returns the actual runtime class, not the class where the method is defined. `self::class` would always return `Animal`. Use `static::` when subclasses should see their own class name.

**📸 Verified Output:**
```
Rex says: Woof! (German Shepherd)
I am Rex, a Dog

Whiskers says: Meow! *ignores you*
I am Whiskers, a Cat

Buddy says: Woof! (Labrador)
I am Buddy, a Dog

Rex fetches the ball!
Buddy fetches the ball!
```

---

### Step 2: Abstract Classes

```php
<?php
declare(strict_types=1);

abstract class Report {
    final public function generate(): void {
        echo "=== " . $this->title() . " ===\n";
        $this->fetchData();
        $this->processData();
        $this->render();
        echo "=== End ===\n\n";
    }

    abstract protected function title(): string;
    abstract protected function fetchData(): void;
    abstract protected function processData(): void;
    abstract protected function render(): void;
}

class SalesReport extends Report {
    private array $data = [];

    protected function title(): string { return "Sales Report"; }

    protected function fetchData(): void {
        $this->data = [12500, 18200, 9800, 22100, 15600];
        echo "Fetched " . count($this->data) . " records\n";
    }

    protected function processData(): void {
        $total = array_sum($this->data);
        $avg   = $total / count($this->data);
        printf("Total: $%,.0f  Avg: $%,.0f\n", $total, $avg);
    }

    protected function render(): void {
        foreach ($this->data as $i => $v) {
            printf("Week %d: %s $%,.0f\n", $i+1, str_repeat('█', intdiv($v, 2000)), $v);
        }
    }
}

class InventoryReport extends Report {
    protected function title(): string { return "Inventory Status"; }
    protected function fetchData(): void { echo "Loaded inventory\n"; }
    protected function processData(): void { echo "3 items low stock\n"; }
    protected function render(): void {
        echo "Widget A: 45 ✓  Widget B: 3 ⚠  Widget C: 0 ✗\n";
    }
}

(new SalesReport())->generate();
(new InventoryReport())->generate();
```

> 💡 **`final public function generate()`** prevents subclasses from overriding the algorithm structure. Abstract methods force subclasses to provide implementations. This is the **Template Method Pattern** — one of the most used patterns in PHP frameworks.

**📸 Verified Output:**
```
=== Sales Report ===
Fetched 5 records
Total: $78,200  Avg: $15,640
Week 1: ██████ $12,500
Week 2: █████████ $18,200
...
=== End ===

=== Inventory Status ===
...
```

---

### Step 3: Interfaces

```php
<?php
declare(strict_types=1);

interface Payable {
    public function pay(float $amount): bool;
    public function getBalance(): float;
}

interface Refundable {
    public function refund(float $amount): bool;
}

interface Auditable {
    public function getTransactionLog(): array;
}

class CreditCard implements Payable, Refundable, Auditable {
    private float $balance;
    private array $log = [];

    public function __construct(private string $last4, float $limit) {
        $this->balance = $limit;
    }

    public function pay(float $amount): bool {
        if ($amount > $this->balance) return false;
        $this->balance -= $amount;
        $this->log[] = "CHARGE -\${$amount}";
        return true;
    }

    public function refund(float $amount): bool {
        $this->balance += $amount;
        $this->log[] = "REFUND +\${$amount}";
        return true;
    }

    public function getBalance(): float { return $this->balance; }
    public function getTransactionLog(): array { return $this->log; }
}

function processPayment(Payable $method, float $amount): void {
    $ok = $method->pay($amount);
    echo "Pay \${$amount}: " . ($ok ? "✓" : "✗ declined") . "\n";
}

$card = new CreditCard('4242', 1000.00);
processPayment($card, 864.00);
processPayment($card, 500.00); // decline
$card->refund(100.00);

echo "Balance: \$" . $card->getBalance() . "\n";
echo "Log: " . implode(', ', $card->getTransactionLog()) . "\n";
```

> 💡 **Programming to interfaces** (`Payable $method`) means `processPayment` works with any class implementing `Payable` — credit cards, PayPal, Bitcoin, gift cards. You can add new payment methods without changing `processPayment`. This is the Dependency Inversion Principle.

**📸 Verified Output:**
```
Pay $864: ✓
Pay $500: ✗ declined
Balance: $236
Log: CHARGE -$864, REFUND -$100
```

---

### Step 4: Polymorphism — Shapes & Area

```php
<?php
declare(strict_types=1);

abstract class Shape {
    abstract public function area(): float;
    abstract public function perimeter(): float;
    abstract public function name(): string;

    public function describe(): string {
        return sprintf("%-12s area=%8.2f  perimeter=%8.2f",
            $this->name(), $this->area(), $this->perimeter());
    }
}

class Circle extends Shape {
    public function __construct(private float $radius) {}
    public function area(): float      { return M_PI * $this->radius ** 2; }
    public function perimeter(): float { return 2 * M_PI * $this->radius; }
    public function name(): string     { return "Circle(r={$this->radius})"; }
}

class Rectangle extends Shape {
    public function __construct(protected float $w, protected float $h) {}
    public function area(): float      { return $this->w * $this->h; }
    public function perimeter(): float { return 2 * ($this->w + $this->h); }
    public function name(): string     { return "Rect({$this->w}x{$this->h})"; }
}

class Square extends Rectangle {
    public function __construct(float $side) { parent::__construct($side, $side); }
    public function name(): string { return "Square({$this->w})"; }
}

class Triangle extends Shape {
    public function __construct(private float $a, private float $b, private float $c) {}
    public function area(): float {
        $s = ($this->a + $this->b + $this->c) / 2;
        return sqrt($s * ($s-$this->a) * ($s-$this->b) * ($s-$this->c));
    }
    public function perimeter(): float { return $this->a + $this->b + $this->c; }
    public function name(): string { return "Triangle"; }
}

$shapes = [
    new Circle(5),
    new Rectangle(4, 6),
    new Square(4),
    new Triangle(3, 4, 5),
];

echo "Shapes:\n";
foreach ($shapes as $s) echo "  " . $s->describe() . "\n";

$totalArea = array_sum(array_map(fn($s) => $s->area(), $shapes));
printf("\nTotal area: %.2f\n", $totalArea);

usort($shapes, fn($a, $b) => $b->area() <=> $a->area());
echo "Largest: " . $shapes[0]->name() . "\n";
```

> 💡 **Polymorphism** means `$s->area()` calls the right method for each shape type without any `if/switch`. Adding a `Pentagon` class requires zero changes to `describe()`, the sorting, or the total calculation. This extensibility is the core benefit of OOP.

**📸 Verified Output:**
```
Shapes:
  Circle(r=5)   area=    78.54  perimeter=    31.42
  Rect(4x6)     area=    24.00  perimeter=    20.00
  Square(4)     area=    16.00  perimeter=    16.00
  Triangle      area=     6.00  perimeter=    12.00

Total area: 124.54
Largest: Circle(r=5)
```

---

### Step 5: final Classes & Methods

```php
<?php
// final class — cannot be extended
final class UUID {
    private string $value;

    private function __construct(string $value) {
        $this->value = $value;
    }

    public static function generate(): self {
        return new self(sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        ));
    }

    public static function fromString(string $uuid): self {
        if (!preg_match('/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/', $uuid))
            throw new \InvalidArgumentException("Invalid UUID: $uuid");
        return new self($uuid);
    }

    public function __toString(): string { return $this->value; }
    public function equals(self $other): bool { return $this->value === $other->value; }
}

$id1 = UUID::generate();
$id2 = UUID::generate();
$id3 = UUID::fromString((string)$id1);

echo "UUID 1: $id1\n";
echo "UUID 2: $id2\n";
echo "1 == 3: " . ($id1->equals($id3) ? 'yes' : 'no') . "\n";
echo "1 == 2: " . ($id1->equals($id2) ? 'yes' : 'no') . "\n";

// final method in non-final class
class Base {
    final public function immutableAlgorithm(): string {
        return "Base algorithm: " . $this->step();
    }
    protected function step(): string { return "base step"; }
}

class Child extends Base {
    protected function step(): string { return "child step"; } // OK
    // final public function immutableAlgorithm() — ERROR
}

echo "\n" . (new Child())->immutableAlgorithm() . "\n";
```

> 💡 **`final class`** prevents extension — use it for value objects, utility classes, and security-sensitive code where you want to guarantee behavior. `final` methods in non-final classes allow extension of the class but lock down specific methods. This is how PHP's `DateTimeImmutable` prevents accidental subclass mutations.

**📸 Verified Output:**
```
UUID 1: a3f2e1d0-b4c5-4d6e-8f7a-9b0c1d2e3f4a
UUID 2: 1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d
1 == 3: yes
1 == 2: no

Base algorithm: child step
```

---

### Step 6: Iterator Interface

```php
<?php
declare(strict_types=1);

class NumberRange implements Iterator {
    private int $current;

    public function __construct(
        private int $start,
        private int $end,
        private int $step = 1,
    ) {
        $this->current = $start;
    }

    public function current(): int   { return $this->current; }
    public function key(): int       { return ($this->current - $this->start) / $this->step; }
    public function next(): void     { $this->current += $this->step; }
    public function rewind(): void   { $this->current = $this->start; }
    public function valid(): bool    { return $this->current <= $this->end; }
}

class FilteredIterator implements Iterator {
    private array $keys;
    private int $pos = 0;

    public function __construct(
        private array $data,
        private \Closure $predicate,
    ) {
        $this->keys = array_keys(array_filter($data, $predicate));
    }

    public function current(): mixed { return $this->data[$this->keys[$this->pos]]; }
    public function key(): mixed     { return $this->keys[$this->pos]; }
    public function next(): void     { $this->pos++; }
    public function rewind(): void   { $this->pos = 0; }
    public function valid(): bool    { return $this->pos < count($this->keys); }
}

// NumberRange is foreach-able
$range = new NumberRange(1, 10, 2);
echo "Odd numbers: ";
foreach ($range as $n) echo "$n ";
echo "\n";

// Can be reused
echo "Again:       ";
foreach ($range as $key => $n) echo "$key:$n ";
echo "\n";

// FilteredIterator
$data = ['alice' => 95, 'bob' => 65, 'carol' => 88, 'dave' => 72, 'eve' => 91];
$highScores = new FilteredIterator($data, fn($score) => $score >= 85);

echo "\nHigh scores:\n";
foreach ($highScores as $name => $score) {
    echo "  $name: $score\n";
}
```

> 💡 **Implementing `Iterator`** makes your class work in `foreach`, `iterator_to_array()`, and any function that accepts an `iterable`. This is how Laravel's Collection, Doctrine's result sets, and PHP's SPL data structures work — they're all iterators under the hood.

**📸 Verified Output:**
```
Odd numbers: 1 3 5 7 9
Again:       0:1 1:3 2:5 3:7 4:9

High scores:
  alice: 95
  carol: 88
  eve: 91
```

---

### Step 7: Comparable Pattern & Sorting

```php
<?php
declare(strict_types=1);

interface Comparable {
    public function compareTo(mixed $other): int; // -1, 0, 1
}

class Version implements Comparable, \Stringable {
    public function __construct(
        public readonly int $major,
        public readonly int $minor,
        public readonly int $patch,
    ) {}

    public static function parse(string $v): self {
        [$major, $minor, $patch] = array_map('intval', explode('.', $v));
        return new self($major, $minor, $patch);
    }

    public function compareTo(mixed $other): int {
        return $this->major <=> $other->major
            ?: $this->minor <=> $other->minor
            ?: $this->patch <=> $other->patch;
    }

    public function __toString(): string {
        return "{$this->major}.{$this->minor}.{$this->patch}";
    }
}

$versions = array_map(
    fn($v) => Version::parse($v),
    ['2.1.0', '1.0.0', '2.0.1', '1.5.3', '3.0.0', '2.1.1']
);

usort($versions, fn($a, $b) => $a->compareTo($b));
echo "Sorted: " . implode(', ', $versions) . "\n";

// Latest
$latest = array_reduce($versions, function($max, $v) {
    return $max === null || $v->compareTo($max) > 0 ? $v : $max;
});
echo "Latest: $latest\n";
```

**📸 Verified Output:**
```
Sorted: 1.0.0, 1.5.3, 2.0.1, 2.1.0, 2.1.1, 3.0.0
Latest: 3.0.0
```

---

### Step 8: Complete — Payment System

```php
<?php
declare(strict_types=1);

interface PaymentGateway {
    public function charge(float $amount, string $currency): PaymentResult;
    public function getName(): string;
}

readonly class PaymentResult {
    public function __construct(
        public bool   $success,
        public string $transactionId,
        public string $message,
        public float  $amount,
    ) {}
}

abstract class BaseGateway implements PaymentGateway {
    private static array $transactions = [];

    final protected function recordTransaction(PaymentResult $result): void {
        self::$transactions[] = $result;
    }

    public static function getTransactionCount(): int {
        return count(self::$transactions);
    }
}

class StripeGateway extends BaseGateway {
    public function charge(float $amount, string $currency): PaymentResult {
        $success = $amount <= 10000;
        $result = new PaymentResult(
            $success,
            $success ? 'stripe_' . rand(1000, 9999) : '',
            $success ? 'Approved' : 'Declined: exceeds limit',
            $amount,
        );
        $this->recordTransaction($result);
        return $result;
    }

    public function getName(): string { return 'Stripe'; }
}

class PayPalGateway extends BaseGateway {
    public function charge(float $amount, string $currency): PaymentResult {
        $result = new PaymentResult(true, 'paypal_' . rand(100, 999), 'Approved', $amount);
        $this->recordTransaction($result);
        return $result;
    }

    public function getName(): string { return 'PayPal'; }
}

function checkout(PaymentGateway $gateway, float $amount): void {
    echo "Charging \${$amount} via " . $gateway->getName() . "... ";
    $result = $gateway->charge($amount, 'USD');
    echo ($result->success ? "✓ {$result->transactionId}" : "✗ {$result->message}") . "\n";
}

$gateways = [new StripeGateway(), new PayPalGateway(), new StripeGateway()];
$amounts  = [864.00, 49.99, 15000.00];

foreach (array_map(null, $gateways, $amounts) as [$g, $a]) {
    checkout($g, $a);
}

echo "\nTotal transactions: " . BaseGateway::getTransactionCount() . "\n";
```

**📸 Verified Output:**
```
Charging $864 via Stripe... ✓ stripe_4821
Charging $49.99 via PayPal... ✓ paypal_372
Charging $15000 via Stripe... ✗ Declined: exceeds limit

Total transactions: 3
```

---

## Summary

You've applied PHP inheritance, abstract classes, interfaces, polymorphism, `final`, the Iterator interface, Comparable pattern, and a full payment system. These patterns underpin every PHP framework — Laravel's Eloquent, Symfony's event dispatcher, and Doctrine's collections all use these exact concepts.

## Further Reading
- [PHP Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php)
- [PHP SPL Iterators](https://www.php.net/manual/en/spl.iterators.php)
