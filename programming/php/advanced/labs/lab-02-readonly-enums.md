# Lab 02: Readonly Properties, Classes & Enums

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PHP 8.1 introduced readonly properties and enums. PHP 8.2 added readonly classes. Together these features enable immutable value objects and type-safe constants with behavior.

---

## Step 1: Readonly Properties (PHP 8.1)

```php
<?php
class Point {
    public function __construct(
        public readonly float $x,
        public readonly float $y,
    ) {}
}

$p = new Point(3.0, 4.0);
echo "$p->x, $p->y\n";  // 3, 4

try {
    $p->x = 1.0;  // Fatal error
} catch (\Error $e) {
    echo $e->getMessage() . "\n";
}
```

📸 **Verified Output:**
```
3, 4
Cannot modify readonly property Point::$x
```

> 💡 Readonly properties can only be written **once**, during initialization (in the constructor). Uninitialized readonly properties cannot be read.

---

## Step 2: Readonly Classes (PHP 8.2)

Marking a class `readonly` makes ALL properties readonly automatically:

```php
<?php
readonly class Money {
    public function __construct(
        public int $amount,
        public string $currency,
    ) {}

    public function add(Money $other): static {
        if ($this->currency !== $other->currency) {
            throw new \InvalidArgumentException("Currency mismatch");
        }
        return new static($this->amount + $other->amount, $this->currency);
    }

    public function __toString(): string {
        return "{$this->amount} {$this->currency}";
    }
}

$price = new Money(1000, 'USD');
$tax   = new Money(80, 'USD');
$total = $price->add($tax);

echo "Price: $price\n";
echo "Tax:   $tax\n";
echo "Total: $total\n";
```

📸 **Verified Output:**
```
Price: 1000 USD
Tax:   80 USD
Total: 1080 USD
```

> 💡 Readonly classes cannot have non-readonly properties. They work perfectly as value objects and DTOs.

---

## Step 3: Pure Enums

Pure enums have named cases but no backing value:

```php
<?php
enum Direction {
    case North;
    case South;
    case East;
    case West;

    public function opposite(): self {
        return match($this) {
            Direction::North => Direction::South,
            Direction::South => Direction::North,
            Direction::East  => Direction::West,
            Direction::West  => Direction::East,
        };
    }

    public function label(): string {
        return match($this) {
            Direction::North => '↑ North',
            Direction::South => '↓ South',
            Direction::East  => '→ East',
            Direction::West  => '← West',
        };
    }
}

$d = Direction::North;
echo $d->label() . "\n";
echo $d->opposite()->label() . "\n";
echo $d->name . "\n";
```

📸 **Verified Output:**
```
↑ North
↓ South
North
```

---

## Step 4: Backed Enums (int and string)

```php
<?php
enum Status: string {
    case Active   = 'active';
    case Inactive = 'inactive';
    case Pending  = 'pending';

    public function label(): string {
        return ucfirst($this->value);
    }

    public function isActive(): bool {
        return $this === self::Active;
    }
}

// from() throws ValueError on unknown value
$s = Status::from('active');
echo $s->label() . "\n";
echo $s->name . "\n";
echo $s->value . "\n";

// tryFrom() returns null on unknown value
$unknown = Status::tryFrom('deleted');
echo ($unknown === null ? 'null' : $unknown->name) . "\n";

// cases() returns all enum cases
foreach (Status::cases() as $case) {
    echo $case->name . ': ' . $case->value . "\n";
}
```

📸 **Verified Output:**
```
Active
Active
active
null
Active: active
Inactive: inactive
Pending: pending
```

---

## Step 5: Enum with Interface and Constants

```php
<?php
interface HasColor {
    public function color(): string;
}

enum Suit: string implements HasColor {
    case Hearts   = 'H';
    case Diamonds = 'D';
    case Clubs    = 'C';
    case Spades   = 'S';

    const DEFAULT = self::Hearts;

    public function color(): string {
        return match($this) {
            self::Hearts, self::Diamonds => 'red',
            self::Clubs,  self::Spades   => 'black',
        };
    }

    public function symbol(): string {
        return match($this) {
            self::Hearts   => '♥',
            self::Diamonds => '♦',
            self::Clubs    => '♣',
            self::Spades   => '♠',
        };
    }
}

foreach (Suit::cases() as $suit) {
    printf("%-10s %s  color=%-5s  value=%s\n",
        $suit->name, $suit->symbol(), $suit->color(), $suit->value
    );
}

echo "Default: " . Suit::DEFAULT->name . "\n";
```

📸 **Verified Output:**
```
Hearts     ♥  color=red    value=H
Diamonds   ♦  color=red    value=D
Clubs      ♣  color=black  value=C
Spades     ♠  color=black  value=S
Default: Hearts
```

---

## Step 6: Enum in match Expression

```php
<?php
enum HttpMethod: string {
    case GET    = 'GET';
    case POST   = 'POST';
    case PUT    = 'PUT';
    case DELETE = 'DELETE';
    case PATCH  = 'PATCH';
}

function handleRequest(HttpMethod $method, string $path): string {
    return match($method) {
        HttpMethod::GET    => "Fetching $path",
        HttpMethod::POST   => "Creating resource at $path",
        HttpMethod::PUT    => "Replacing resource at $path",
        HttpMethod::DELETE => "Deleting $path",
        HttpMethod::PATCH  => "Patching $path",
    };
}

foreach (HttpMethod::cases() as $method) {
    echo handleRequest($method, '/api/users') . "\n";
}
```

📸 **Verified Output:**
```
Fetching /api/users
Creating resource at /api/users
Replacing resource at /api/users
Deleting /api/users
Patching /api/users
```

> 💡 Enums work in `match` with identity comparison (`===`). No need for `->value` comparison.

---

## Step 7: Enum as Type — No Invalid States

```php
<?php
enum Permission: int {
    case Read    = 1;
    case Write   = 2;
    case Execute = 4;
    case Admin   = 255;

    public function includes(self $other): bool {
        return ($this->value & $other->value) === $other->value;
    }
}

class FileAccess {
    public function __construct(
        private readonly string $filename,
        private readonly Permission $permission,
    ) {}

    public function canWrite(): bool {
        return $this->permission->includes(Permission::Write);
    }

    public function describe(): string {
        return "{$this->filename}: {$this->permission->name} (value={$this->permission->value})";
    }
}

$files = [
    new FileAccess('readme.txt', Permission::Read),
    new FileAccess('config.php', Permission::Write),
    new FileAccess('admin.log', Permission::Admin),
];

foreach ($files as $f) {
    $write = $f->canWrite() ? 'writable' : 'read-only';
    echo $f->describe() . " [$write]\n";
}
```

📸 **Verified Output:**
```
readme.txt: Read (value=1) [read-only]
config.php: Write (value=2) [writable]
admin.log: Admin (value=255) [writable]
```

---

## Step 8: Capstone — Immutable State Machine

Combine readonly classes and enums for a type-safe order processing state machine:

```php
<?php
enum OrderStatus: string {
    case Draft     = 'draft';
    case Confirmed = 'confirmed';
    case Shipped   = 'shipped';
    case Delivered = 'delivered';
    case Cancelled = 'cancelled';

    public function canTransitionTo(self $next): bool {
        return match($this) {
            self::Draft     => in_array($next, [self::Confirmed, self::Cancelled]),
            self::Confirmed => in_array($next, [self::Shipped, self::Cancelled]),
            self::Shipped   => $next === self::Delivered,
            self::Delivered => false,
            self::Cancelled => false,
        };
    }

    public function label(): string {
        return ucfirst($this->value);
    }
}

readonly class Order {
    public function __construct(
        public int $id,
        public string $item,
        public float $total,
        public OrderStatus $status = OrderStatus::Draft,
    ) {}

    public function transition(OrderStatus $newStatus): static {
        if (!$this->status->canTransitionTo($newStatus)) {
            throw new \LogicException(
                "Cannot transition from {$this->status->label()} to {$newStatus->label()}"
            );
        }
        return new static($this->id, $this->item, $this->total, $newStatus);
    }

    public function __toString(): string {
        return "Order#{$this->id} [{$this->item}] \${$this->total} → {$this->status->label()}";
    }
}

$order = new Order(42, 'PHP Book', 49.99);
echo $order . "\n";

$order = $order->transition(OrderStatus::Confirmed);
echo $order . "\n";

$order = $order->transition(OrderStatus::Shipped);
echo $order . "\n";

$order = $order->transition(OrderStatus::Delivered);
echo $order . "\n";

try {
    $order->transition(OrderStatus::Cancelled);  // Should fail
} catch (\LogicException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

📸 **Verified Output:**
```
Order#42 [PHP Book] $49.99 → Draft
Order#42 [PHP Book] $49.99 → Confirmed
Order#42 [PHP Book] $49.99 → Shipped
Order#42 [PHP Book] $49.99 → Delivered
Error: Cannot transition from Delivered to Cancelled
```

---

## Summary

| Feature | Syntax | PHP Version |
|---|---|---|
| Readonly property | `public readonly Type $prop` | 8.1+ |
| Readonly class | `readonly class Foo {}` | 8.2+ |
| Pure enum | `enum Suit { case Hearts; }` | 8.1+ |
| Backed enum (string) | `enum Status: string { case A = 'a'; }` | 8.1+ |
| Backed enum (int) | `enum Perm: int { case R = 1; }` | 8.1+ |
| Get all cases | `Status::cases()` | 8.1+ |
| From value (strict) | `Status::from('active')` | 8.1+ |
| From value (safe) | `Status::tryFrom('unknown')` → null | 8.1+ |
| Enum implements interface | `enum Foo: string implements Bar {}` | 8.1+ |
| Enum constants | `const DEFAULT = self::CaseName;` | 8.1+ |
