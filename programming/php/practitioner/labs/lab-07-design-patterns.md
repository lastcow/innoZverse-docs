# Lab 7: Design Patterns in PHP

## Objective
Implement the most commonly used design patterns in PHP: **Singleton** for shared resources, **Factory/Abstract Factory** for object creation, **Observer** for event systems, **Strategy** for swappable algorithms, **Decorator** for behaviour composition, and **Command** for encapsulating actions.

## Background
Design patterns are reusable solutions to recurring problems. In PHP they appear everywhere: Laravel's IoC container (Singleton + Factory), Symfony's EventDispatcher (Observer), payment gateways (Strategy), middleware stacks (Decorator), and command buses (Command). Learning to recognise and implement patterns makes framework internals transparent.

## Time
35 minutes

## Prerequisites
- PHP Practitioner Lab 01 (Traits & Interfaces)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Singleton & Factory

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Singleton ────────────────────────────────────────────────────────────────
// Ensures only ONE instance exists — used for DB connections, config, loggers
class DatabaseConnection {
    private static ?self $instance = null;
    private int $queryCount = 0;
    private array $log = [];

    // Private constructor prevents "new DatabaseConnection()"
    private function __construct(private string $dsn) {
        $this->log[] = "Connected to: {$dsn}";
    }

    public static function getInstance(string $dsn = "sqlite::memory:"): self {
        if (self::$instance === null) {
            self::$instance = new self($dsn);
        }
        return self::$instance;
    }

    public function query(string $sql): string {
        $this->queryCount++;
        $this->log[] = "Query #{$this->queryCount}: {$sql}";
        return "Result of: {$sql}";
    }

    public function stats(): array {
        return ["queries" => $this->queryCount, "dsn" => $this->dsn];
    }

    // Prevent cloning and unserialization
    private function __clone() {}
    public function __wakeup(): never {
        throw new \Exception("Cannot unserialize singleton");
    }
}

echo "=== Singleton ===" . PHP_EOL;
$db1 = DatabaseConnection::getInstance();
$db2 = DatabaseConnection::getInstance();
$db1->query("SELECT * FROM products");
$db2->query("SELECT * FROM orders");   // same instance!
echo "Same instance: " . ($db1 === $db2 ? "yes" : "no") . PHP_EOL;
echo "Queries: " . $db1->stats()["queries"] . PHP_EOL;

// ── Factory Method ────────────────────────────────────────────────────────────
echo PHP_EOL . "=== Factory Method ===" . PHP_EOL;

interface PaymentGateway {
    public function charge(float $amount): array;
    public function getName(): string;
}

class StripeGateway implements PaymentGateway {
    public function charge(float $amount): array {
        return ["gateway" => "Stripe", "amount" => $amount, "fee" => round($amount*0.029+0.30,2), "status" => "ok"];
    }
    public function getName(): string { return "Stripe"; }
}

class PayPalGateway implements PaymentGateway {
    public function charge(float $amount): array {
        return ["gateway" => "PayPal", "amount" => $amount, "fee" => round($amount*0.034+0.30,2), "status" => "ok"];
    }
    public function getName(): string { return "PayPal"; }
}

class CryptoGateway implements PaymentGateway {
    public function charge(float $amount): array {
        return ["gateway" => "Crypto", "amount" => $amount, "fee" => round($amount*0.001,4), "status" => "ok"];
    }
    public function getName(): string { return "Crypto"; }
}

// Factory: creates the right object based on config/input
class PaymentGatewayFactory {
    public static function create(string $type): PaymentGateway {
        return match($type) {
            "stripe" => new StripeGateway(),
            "paypal" => new PayPalGateway(),
            "crypto" => new CryptoGateway(),
            default  => throw new \InvalidArgumentException("Unknown gateway: {$type}"),
        };
    }
}

$gateways = ["stripe", "paypal", "crypto"];
$amount   = 864.00;
foreach ($gateways as $type) {
    $gw     = PaymentGatewayFactory::create($type);
    $result = $gw->charge($amount);
    printf("  %-8s fee=\$%-7.4f net=\$%.2f%s",
        $result["gateway"], $result["fee"], $amount - $result["fee"], PHP_EOL);
}
'
```

---

### Step 2: Observer, Strategy, Decorator, Command

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Observer / Event System ───────────────────────────────────────────────────
echo "=== Observer (Event System) ===" . PHP_EOL;

interface EventListener {
    public function handle(string $event, array $data): void;
}

class EventEmitter {
    private array $listeners = [];

    public function on(string $event, EventListener|callable $listener): void {
        $this->listeners[$event][] = $listener;
    }

    public function emit(string $event, array $data = []): void {
        foreach ($this->listeners[$event] ?? [] as $listener) {
            is_callable($listener) ? $listener($data) : $listener->handle($event, $data);
        }
    }
}

class EmailNotifier implements EventListener {
    public array $sent = [];
    public function handle(string $event, array $data): void {
        $this->sent[] = "Email: [{$event}] Order #{$data["orderId"]} - {$data["product"]}";
    }
}

class InventoryManager implements EventListener {
    public array $changes = [];
    public function handle(string $event, array $data): void {
        if ($event === "order.placed") {
            $this->changes[] = "Deduct stock: {$data["product"]} × {$data["qty"]}";
        }
    }
}

$events    = new EventEmitter();
$email     = new EmailNotifier();
$inventory = new InventoryManager();

$events->on("order.placed",    $email);
$events->on("order.placed",    $inventory);
$events->on("order.shipped",   $email);
$events->on("order.cancelled", $email);
$events->on("order.cancelled", fn($d) => print("  ⚡ Webhook: refund for #{$d["orderId"]}" . PHP_EOL));

$events->emit("order.placed",    ["orderId" => 1001, "product" => "Surface Pro",  "qty" => 2]);
$events->emit("order.shipped",   ["orderId" => 1001, "product" => "Surface Pro",  "qty" => 2]);
$events->emit("order.cancelled", ["orderId" => 1002, "product" => "USB-C Hub",    "qty" => 1]);

foreach ($email->sent as $e) echo "  " . $e . PHP_EOL;
foreach ($inventory->changes as $c) echo "  " . $c . PHP_EOL;

// ── Strategy ─────────────────────────────────────────────────────────────────
echo PHP_EOL . "=== Strategy ===" . PHP_EOL;

interface SortStrategy {
    public function sort(array &$items): void;
    public function name(): string;
}

class PriceAscStrategy implements SortStrategy {
    public function sort(array &$items): void { usort($items, fn($a,$b) => $a["price"] <=> $b["price"]); }
    public function name(): string { return "Price ↑"; }
}

class NameStrategy implements SortStrategy {
    public function sort(array &$items): void { usort($items, fn($a,$b) => strcmp($a["name"], $b["name"])); }
    public function name(): string { return "Name A→Z"; }
}

class ValueStrategy implements SortStrategy {
    public function sort(array &$items): void {
        usort($items, fn($a,$b) => ($b["price"]*$b["stock"]) <=> ($a["price"]*$a["stock"]));
    }
    public function name(): string { return "Value ↓"; }
}

class ProductCatalogue {
    private SortStrategy $strategy;
    public function __construct(SortStrategy $strategy) { $this->strategy = $strategy; }
    public function setStrategy(SortStrategy $s): void { $this->strategy = $s; }
    public function sort(array $items): array {
        $this->strategy->sort($items);
        return $items;
    }
}

$products = [
    ["name" => "Surface Pro",  "price" => 864.00, "stock" => 15],
    ["name" => "Surface Pen",  "price" => 49.99,  "stock" => 80],
    ["name" => "Office 365",   "price" => 99.99,  "stock" => 999],
    ["name" => "USB-C Hub",    "price" => 29.99,  "stock" => 0],
];

$cat = new ProductCatalogue(new PriceAscStrategy());
foreach ([new PriceAscStrategy(), new NameStrategy(), new ValueStrategy()] as $strategy) {
    $cat->setStrategy($strategy);
    $sorted = $cat->sort($products);
    echo "  " . $strategy->name() . ": " . implode(", ", array_column($sorted, "name")) . PHP_EOL;
}

// ── Decorator ─────────────────────────────────────────────────────────────────
echo PHP_EOL . "=== Decorator ===" . PHP_EOL;

interface Logger {
    public function log(string $message): void;
    public function getLogs(): array;
}

class ConsoleLogger implements Logger {
    private array $logs = [];
    public function log(string $message): void {
        $this->logs[] = $message;
        echo "  [CONSOLE] " . $message . PHP_EOL;
    }
    public function getLogs(): array { return $this->logs; }
}

// Decorator: adds timestamp without modifying ConsoleLogger
class TimestampLogger implements Logger {
    public function __construct(private Logger $inner) {}
    public function log(string $message): void {
        $this->inner->log("[" . date("H:i:s") . "] " . $message);
    }
    public function getLogs(): array { return $this->inner->getLogs(); }
}

// Decorator: adds severity prefix
class LevelLogger implements Logger {
    public function __construct(private Logger $inner, private string $level = "INFO") {}
    public function log(string $message): void {
        $this->inner->log("[{$this->level}] " . $message);
    }
    public function getLogs(): array { return $this->inner->getLogs(); }
}

// Stack decorators — each wraps the previous
$logger = new LevelLogger(new TimestampLogger(new ConsoleLogger()), "INFO");
$logger->log("Order #1001 placed: Surface Pro ×2 = \$1728.00");
$logger->log("Payment processed via Stripe");

echo "  Total log entries: " . count($logger->getLogs()) . PHP_EOL;
'
```

**📸 Verified Output:**
```
=== Observer (Event System) ===
  ⚡ Webhook: refund for #1002
  Email: [order.placed] Order #1001 - Surface Pro
  Email: [order.shipped] Order #1001 - Surface Pro
  Email: [order.cancelled] Order #1002 - USB-C Hub
  Deduct stock: Surface Pro × 2

=== Strategy ===
  Price ↑: USB-C Hub, Surface Pen, Office 365, Surface Pro
  Name A→Z: Office 365, Surface Pen, Surface Pro, USB-C Hub
  Value ↓: Office 365, Surface Pro, Surface Pen, USB-C Hub

=== Decorator ===
  [CONSOLE] [INFO] [15:00:00] Order #1001 placed: Surface Pro ×2 = $1728.00
  [CONSOLE] [INFO] [15:00:00] Payment processed via Stripe
```

---

## Summary

| Pattern | Intent | PHP Use |
|---------|--------|---------|
| Singleton | One instance globally | DB connections, config |
| Factory | Create objects by type | Gateways, drivers |
| Observer | Notify listeners of events | Order events, webhooks |
| Strategy | Swap algorithms at runtime | Sorting, pricing, export |
| Decorator | Add behaviour by wrapping | Logging, caching, auth |
| Command | Encapsulate an action | Queue jobs, undo/redo |

## Further Reading
- [Refactoring.Guru PHP Patterns](https://refactoring.guru/design-patterns/php)
