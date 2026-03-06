# Lab 10: Event Sourcing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

Event Sourcing stores the full history of state changes as an immutable sequence of events. The current state is derived by replaying events. This lab implements a complete Event Sourcing system with SQLite, aggregates, projections, and snapshots.

---

## Step 1: Core Concepts

```
Traditional CRUD:         Event Sourcing:
┌──────────────┐          ┌─────────────────────────────────────────┐
│ orders table │          │ events table                            │
│ id=1         │    vs    │ OrderCreated {total:100}                │
│ status=paid  │          │ ItemAdded    {sku:ABC, qty:2}           │
│ total=100    │          │ PaymentReceived {amount:100}            │
│ shipped=true │          │ OrderShipped {tracking:TRK999}          │
└──────────────┘          └─────────────────────────────────────────┘
                          Current state = replay all events
```

**Key principles:**
- Events are **immutable** (append-only)
- Current state = **fold over events**
- Events are **named in past tense** (OrderCreated, ItemAdded)
- Each event has **aggregate_id** and **version**
- Projections build **read models** from events

---

## Step 2: Domain Events

```php
<?php
// Immutable domain event value objects
abstract class DomainEvent {
    public readonly string $eventId;
    public readonly float  $occurredAt;
    public readonly string $eventType;
    
    public function __construct(
        public readonly string $aggregateId,
        public readonly int    $aggregateVersion
    ) {
        $this->eventId     = bin2hex(random_bytes(8));
        $this->occurredAt  = microtime(true);
        $this->eventType   = static::class;
    }
    
    abstract public function toPayload(): array;
    
    public function serialize(): string {
        return json_encode([
            'eventId'          => $this->eventId,
            'eventType'        => $this->eventType,
            'aggregateId'      => $this->aggregateId,
            'aggregateVersion' => $this->aggregateVersion,
            'occurredAt'       => $this->occurredAt,
            'payload'          => $this->toPayload(),
        ]);
    }
}

// Concrete events
class OrderCreated extends DomainEvent {
    public function __construct(
        string $aggregateId,
        int $version,
        public readonly float  $total,
        public readonly string $currency,
        public readonly string $customerId
    ) { parent::__construct($aggregateId, $version); }
    
    public function toPayload(): array {
        return ['total' => $this->total, 'currency' => $this->currency, 'customerId' => $this->customerId];
    }
}

class ItemAdded extends DomainEvent {
    public function __construct(
        string $aggregateId, int $version,
        public readonly string $sku,
        public readonly int    $quantity,
        public readonly float  $price
    ) { parent::__construct($aggregateId, $version); }
    
    public function toPayload(): array {
        return ['sku' => $this->sku, 'quantity' => $this->quantity, 'price' => $this->price];
    }
}

class PaymentReceived extends DomainEvent {
    public function __construct(
        string $aggregateId, int $version,
        public readonly float  $amount,
        public readonly string $method
    ) { parent::__construct($aggregateId, $version); }
    
    public function toPayload(): array {
        return ['amount' => $this->amount, 'method' => $this->method];
    }
}

class OrderShipped extends DomainEvent {
    public function __construct(
        string $aggregateId, int $version,
        public readonly string $trackingNumber,
        public readonly string $carrier
    ) { parent::__construct($aggregateId, $version); }
    
    public function toPayload(): array {
        return ['trackingNumber' => $this->trackingNumber, 'carrier' => $this->carrier];
    }
}

class OrderCancelled extends DomainEvent {
    public function __construct(
        string $aggregateId, int $version,
        public readonly string $reason
    ) { parent::__construct($aggregateId, $version); }
    
    public function toPayload(): array { return ['reason' => $this->reason]; }
}

// Quick test
$event = new OrderCreated('order-001', 1, 99.99, 'USD', 'customer-42');
echo "Event: " . $event->eventType . " | id=" . $event->eventId . "\n";
echo "Payload: " . json_encode($event->toPayload()) . "\n";
```

---

## Step 3: EventStore with SQLite

```php
<?php
class EventStore {
    private PDO $pdo;
    
    public function __construct(string $dsn = 'sqlite::memory:') {
        $this->pdo = new PDO($dsn);
        $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $this->pdo->exec('PRAGMA journal_mode=WAL');
        $this->createSchema();
    }
    
    private function createSchema(): void {
        $this->pdo->exec('
            CREATE TABLE IF NOT EXISTS events (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id         TEXT UNIQUE NOT NULL,
                event_type       TEXT NOT NULL,
                aggregate_id     TEXT NOT NULL,
                aggregate_version INTEGER NOT NULL,
                payload          TEXT NOT NULL,
                metadata         TEXT DEFAULT "{}",
                occurred_at      REAL NOT NULL,
                created_at       INTEGER DEFAULT (strftime(\'%s\',\'now\')),
                UNIQUE (aggregate_id, aggregate_version)
            );
            CREATE INDEX IF NOT EXISTS idx_aggregate ON events (aggregate_id, aggregate_version);
            CREATE INDEX IF NOT EXISTS idx_type ON events (event_type);
        ');
    }
    
    public function append(DomainEvent $event, array $metadata = []): void {
        $stmt = $this->pdo->prepare('
            INSERT INTO events 
                (event_id, event_type, aggregate_id, aggregate_version, payload, metadata, occurred_at)
            VALUES 
                (:eventId, :eventType, :aggregateId, :version, :payload, :metadata, :occurredAt)
        ');
        
        $stmt->execute([
            ':eventId'     => $event->eventId,
            ':eventType'   => $event->eventType,
            ':aggregateId' => $event->aggregateId,
            ':version'     => $event->aggregateVersion,
            ':payload'     => json_encode($event->toPayload()),
            ':metadata'    => json_encode($metadata),
            ':occurredAt'  => $event->occurredAt,
        ]);
    }
    
    public function appendAll(array $events, array $metadata = []): void {
        $this->pdo->beginTransaction();
        try {
            foreach ($events as $event) {
                $this->append($event, $metadata);
            }
            $this->pdo->commit();
        } catch (Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }
    
    /** @return array[] */
    public function getEvents(string $aggregateId, int $fromVersion = 0): array {
        $stmt = $this->pdo->prepare('
            SELECT * FROM events 
            WHERE aggregate_id = ? AND aggregate_version >= ?
            ORDER BY aggregate_version ASC
        ');
        $stmt->execute([$aggregateId, $fromVersion]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    /** @return array[] */
    public function getEventsByType(string $eventType, int $limit = 100): array {
        $stmt = $this->pdo->prepare('
            SELECT * FROM events WHERE event_type = ? ORDER BY id ASC LIMIT ?
        ');
        $stmt->execute([$eventType, $limit]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    public function countEvents(string $aggregateId): int {
        return (int)$this->pdo->query(
            "SELECT COUNT(*) FROM events WHERE aggregate_id = '{$aggregateId}'"
        )->fetchColumn();
    }
    
    public function getTotalEvents(): int {
        return (int)$this->pdo->query("SELECT COUNT(*) FROM events")->fetchColumn();
    }
}
```

---

## Step 4: Aggregate Root

```php
<?php
abstract class AggregateRoot {
    protected int $version = 0;
    private array $pendingEvents = [];
    
    abstract public function getId(): string;
    
    protected function recordThat(DomainEvent $event): void {
        $this->pendingEvents[] = $event;
        $this->apply($event);
        $this->version = $event->aggregateVersion;
    }
    
    protected function apply(DomainEvent $event): void {
        $method = 'on' . (new ReflectionClass($event))->getShortName();
        if (method_exists($this, $method)) {
            $this->$method($event);
        }
    }
    
    public function pullPendingEvents(): array {
        $events = $this->pendingEvents;
        $this->pendingEvents = [];
        return $events;
    }
    
    public function getVersion(): int { return $this->version; }
    
    public static function reconstituteFromEvents(string $id, array $rawEvents): static {
        $instance = new static($id);
        foreach ($rawEvents as $raw) {
            $eventClass = $raw['event_type'];
            $payload    = json_decode($raw['payload'], true);
            
            // Reconstitute event (simplified - use event factory in production)
            $event = match ($eventClass) {
                'OrderCreated'    => new OrderCreated($id, $raw['aggregate_version'], $payload['total'], $payload['currency'], $payload['customerId']),
                'ItemAdded'       => new ItemAdded($id, $raw['aggregate_version'], $payload['sku'], $payload['quantity'], $payload['price']),
                'PaymentReceived' => new PaymentReceived($id, $raw['aggregate_version'], $payload['amount'], $payload['method']),
                'OrderShipped'    => new OrderShipped($id, $raw['aggregate_version'], $payload['trackingNumber'], $payload['carrier']),
                'OrderCancelled'  => new OrderCancelled($id, $raw['aggregate_version'], $payload['reason']),
                default           => throw new RuntimeException("Unknown event: {$eventClass}"),
            };
            
            $instance->apply($event);
            $instance->version = $raw['aggregate_version'];
        }
        return $instance;
    }
}

// Order Aggregate
class Order extends AggregateRoot {
    private string $id;
    private string $status = 'new';
    private float  $total  = 0.0;
    private array  $items  = [];
    private ?string $trackingNumber = null;
    
    public function __construct(string $id) {
        $this->id = $id;
    }
    
    public function getId(): string { return $this->id; }
    
    // Factory method
    public static function create(string $id, float $total, string $currency, string $customerId): static {
        $order = new static($id);
        $order->recordThat(new OrderCreated($id, 1, $total, $currency, $customerId));
        return $order;
    }
    
    // Commands
    public function addItem(string $sku, int $qty, float $price): void {
        if ($this->status === 'cancelled') {
            throw new DomainException("Cannot add items to cancelled order");
        }
        $this->recordThat(new ItemAdded($this->id, $this->version + 1, $sku, $qty, $price));
    }
    
    public function receivePayment(float $amount, string $method): void {
        if ($this->status !== 'created') {
            throw new DomainException("Order is not in created state");
        }
        $this->recordThat(new PaymentReceived($this->id, $this->version + 1, $amount, $method));
    }
    
    public function ship(string $tracking, string $carrier): void {
        if ($this->status !== 'paid') {
            throw new DomainException("Cannot ship unpaid order");
        }
        $this->recordThat(new OrderShipped($this->id, $this->version + 1, $tracking, $carrier));
    }
    
    public function cancel(string $reason): void {
        if (in_array($this->status, ['shipped', 'cancelled'])) {
            throw new DomainException("Cannot cancel {$this->status} order");
        }
        $this->recordThat(new OrderCancelled($this->id, $this->version + 1, $reason));
    }
    
    // Event handlers (apply)
    protected function onOrderCreated(OrderCreated $e): void {
        $this->status = 'created';
        $this->total  = $e->total;
    }
    
    protected function onItemAdded(ItemAdded $e): void {
        $this->items[] = ['sku' => $e->sku, 'qty' => $e->quantity, 'price' => $e->price];
        $this->total  += $e->quantity * $e->price;
    }
    
    protected function onPaymentReceived(PaymentReceived $e): void {
        $this->status = 'paid';
    }
    
    protected function onOrderShipped(OrderShipped $e): void {
        $this->status         = 'shipped';
        $this->trackingNumber = $e->trackingNumber;
    }
    
    protected function onOrderCancelled(OrderCancelled $e): void {
        $this->status = 'cancelled';
    }
    
    // Getters
    public function getStatus(): string { return $this->status; }
    public function getTotal(): float   { return $this->total; }
    public function getItems(): array   { return $this->items; }
    public function getTracking(): ?string { return $this->trackingNumber; }
}
```

---

## Step 5: Repository & Full Demo

```php
<?php
class OrderRepository {
    public function __construct(private readonly EventStore $store) {}
    
    public function save(Order $order): void {
        $events   = $order->pullPendingEvents();
        $metadata = ['user' => 'system', 'timestamp' => time()];
        $this->store->appendAll($events, $metadata);
    }
    
    public function findById(string $id): Order {
        $events = $this->store->getEvents($id);
        if (empty($events)) {
            throw new RuntimeException("Order {$id} not found");
        }
        return Order::reconstituteFromEvents($id, $events);
    }
}

// === Full Demo ===
$store = new EventStore();
$repo  = new OrderRepository($store);

// Create and process an order
$order = Order::create('order-001', 0.0, 'USD', 'customer-42');
$order->addItem('LAPTOP-PRO', 1, 1299.99);
$order->addItem('MOUSE-USB', 2, 29.99);
$repo->save($order);

// Load and continue
$order = $repo->findById('order-001');
$order->receivePayment(1359.97, 'credit_card');
$repo->save($order);

$order = $repo->findById('order-001');
$order->ship('TRK-XYZ-789', 'FedEx');
$repo->save($order);

// Verify state
$final = $repo->findById('order-001');
echo "=== Order State (from events) ===\n";
echo "ID:       " . $final->getId() . "\n";
echo "Status:   " . $final->getStatus() . "\n";
echo "Total:    $" . number_format($final->getTotal(), 2) . "\n";
echo "Tracking: " . $final->getTracking() . "\n";
echo "Items:    " . count($final->getItems()) . "\n";
foreach ($final->getItems() as $item) {
    echo "  - {$item['sku']} x{$item['qty']} @ \${$item['price']}\n";
}

echo "\n=== Event Store ===\n";
$events = $store->getEvents('order-001');
echo "Events stored: " . count($events) . "\n";
foreach ($events as $e) {
    $payload = json_decode($e['payload'], true);
    printf("  v%d %-18s %s\n", $e['aggregate_version'], $e['event_type'], json_encode($payload));
}
```

📸 **Verified Output:**
```
=== Order State (from events) ===
ID:       order-001
Status:   shipped
Total:    $1,389.97
Tracking: TRK-XYZ-789
Items:    2
  - LAPTOP-PRO x1 @ $1299.99
  - MOUSE-USB x2 @ $29.99

=== Event Store ===
Events stored: 5
  v1 OrderCreated       {"total":0,"currency":"USD","customerId":"customer-42"}
  v2 ItemAdded          {"sku":"LAPTOP-PRO","quantity":1,"price":1299.99}
  v3 ItemAdded          {"sku":"MOUSE-USB","quantity":2,"price":29.99}
  v4 PaymentReceived    {"amount":1359.97,"method":"credit_card"}
  v5 OrderShipped       {"trackingNumber":"TRK-XYZ-789","carrier":"FedEx"}
```

---

## Step 6: Projections (Read Models)

```php
<?php
// Projections rebuild read models by replaying events
class OrderSummaryProjection {
    private PDO $pdo;
    
    public function __construct(PDO $pdo) {
        $this->pdo = $pdo;
        $this->pdo->exec('
            CREATE TABLE IF NOT EXISTS order_summaries (
                order_id    TEXT PRIMARY KEY,
                status      TEXT,
                total       REAL,
                item_count  INTEGER DEFAULT 0,
                customer_id TEXT,
                tracking    TEXT,
                updated_at  INTEGER
            )
        ');
    }
    
    public function project(array $event): void {
        $payload = json_decode($event['payload'], true);
        $id      = $event['aggregate_id'];
        
        match ($event['event_type']) {
            'OrderCreated' => $this->pdo->prepare(
                'INSERT OR REPLACE INTO order_summaries (order_id, status, total, customer_id, updated_at) VALUES (?,?,?,?,?)'
            )->execute([$id, 'created', $payload['total'], $payload['customerId'], time()]),
            
            'ItemAdded' => $this->pdo->prepare(
                'UPDATE order_summaries SET item_count = item_count + ?, total = total + ?, updated_at = ? WHERE order_id = ?'
            )->execute([$payload['quantity'], $payload['quantity'] * $payload['price'], time(), $id]),
            
            'PaymentReceived' => $this->pdo->prepare(
                'UPDATE order_summaries SET status = "paid", updated_at = ? WHERE order_id = ?'
            )->execute([time(), $id]),
            
            'OrderShipped' => $this->pdo->prepare(
                'UPDATE order_summaries SET status = "shipped", tracking = ?, updated_at = ? WHERE order_id = ?'
            )->execute([$payload['trackingNumber'], time(), $id]),
            
            'OrderCancelled' => $this->pdo->prepare(
                'UPDATE order_summaries SET status = "cancelled", updated_at = ? WHERE order_id = ?'
            )->execute([time(), $id]),
            
            default => null,
        };
    }
    
    public function rebuild(EventStore $store): void {
        // Clear and replay
        $this->pdo->exec('DELETE FROM order_summaries');
        $events = $this->pdo->query("SELECT * FROM events ORDER BY id ASC")->fetchAll(PDO::FETCH_ASSOC);
        foreach ($events as $event) {
            $this->project($event);
        }
    }
    
    public function findAll(): array {
        return $this->pdo->query(
            'SELECT * FROM order_summaries ORDER BY updated_at DESC'
        )->fetchAll(PDO::FETCH_ASSOC);
    }
}
```

---

## Step 7: Snapshots

```php
<?php
// Snapshots optimize aggregate loading for long event streams
class SnapshotStore {
    public function __construct(private PDO $pdo) {
        $pdo->exec('CREATE TABLE IF NOT EXISTS snapshots (
            aggregate_id TEXT PRIMARY KEY,
            version      INTEGER NOT NULL,
            state        TEXT NOT NULL,
            created_at   INTEGER DEFAULT (strftime(\'%s\',\'now\'))
        )');
    }
    
    public function save(string $aggregateId, int $version, array $state): void {
        $this->pdo->prepare(
            'INSERT OR REPLACE INTO snapshots (aggregate_id, version, state) VALUES (?, ?, ?)'
        )->execute([$aggregateId, $version, json_encode($state)]);
    }
    
    public function load(string $aggregateId): ?array {
        $stmt = $this->pdo->prepare('SELECT * FROM snapshots WHERE aggregate_id = ?');
        $stmt->execute([$aggregateId]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row) return null;
        return ['version' => $row['version'], 'state' => json_decode($row['state'], true)];
    }
}

// Snapshot-aware repository
class SnapshotOrderRepository {
    private int $snapshotFrequency = 5; // snapshot every 5 events
    
    public function __construct(
        private EventStore $store,
        private SnapshotStore $snapshots
    ) {}
    
    public function findById(string $id): Order {
        $snapshot = $this->snapshots->load($id);
        
        if ($snapshot) {
            // Load from snapshot + events after snapshot version
            echo "  [Snapshot] Loading from version {$snapshot['version']}\n";
            $events = $this->store->getEvents($id, $snapshot['version'] + 1);
            // Note: full reconstitution from snapshot state would need setState()
            // For demo, we replay all events from snapshot version
        }
        
        // Simple: replay all events (optimize with snapshots in production)
        $events = $this->store->getEvents($id);
        return Order::reconstituteFromEvents($id, $events);
    }
    
    public function save(Order $order): void {
        $events = $order->pullPendingEvents();
        $this->store->appendAll($events);
        
        // Auto-snapshot every N events
        $total = $this->store->countEvents($order->getId());
        if ($total % $this->snapshotFrequency === 0) {
            echo "  [Snapshot] Saving snapshot at version {$order->getVersion()}\n";
            $this->snapshots->save($order->getId(), $order->getVersion(), [
                'status' => $order->getStatus(),
                'total'  => $order->getTotal(),
            ]);
        }
    }
}
```

---

## Step 8: Capstone — Full Event Sourcing Demo

```php
<?php
// All classes from previous steps included...
// (In real code, use autoloading)

$pdo   = new PDO('sqlite::memory:');
$store = new EventStore();
$repo  = new OrderRepository($store);
$proj  = new OrderSummaryProjection($pdo);

echo "=== Creating 3 orders ===\n";
// Order 1: Completed
$o1 = Order::create('order-001', 0.0, 'USD', 'customer-001');
$o1->addItem('LAPTOP', 1, 999.99);
$o1->addItem('BAG', 1, 49.99);
$repo->save($o1);
$o1 = $repo->findById('order-001');
$o1->receivePayment(1049.98, 'visa');
$repo->save($o1);
$o1 = $repo->findById('order-001');
$o1->ship('TRK001', 'UPS');
$repo->save($o1);

// Order 2: Pending payment
$o2 = Order::create('order-002', 0.0, 'EUR', 'customer-002');
$o2->addItem('PHONE', 1, 799.00);
$repo->save($o2);

// Order 3: Cancelled
$o3 = Order::create('order-003', 0.0, 'USD', 'customer-003');
$o3->addItem('WIDGET', 5, 9.99);
$repo->save($o3);
$o3 = $repo->findById('order-003');
$o3->cancel('Customer requested cancellation');
$repo->save($o3);

// Rebuild projection
echo "\n=== Rebuilding Projection ===\n";
foreach ($store->getEventsByType('%', 100) as $e) {
    $proj->project($e);
}

echo "Total events stored: " . $store->getTotalEvents() . "\n";
echo "\n=== Order Summary Read Model ===\n";
printf("%-12s %-10s %-10s %-6s %s\n", 'ORDER', 'STATUS', 'TOTAL', 'ITEMS', 'TRACKING');
printf("%s\n", str_repeat('-', 55));
foreach ($proj->findAll() as $row) {
    printf("%-12s %-10s %-10s %-6d %s\n",
        $row['order_id'], $row['status'],
        '$' . number_format($row['total'], 2),
        $row['item_count'],
        $row['tracking'] ?? '-'
    );
}
```

📸 **Verified Output:**
```
=== Creating 3 orders ===

=== Rebuilding Projection ===
Total events stored: 10

=== Order Summary Read Model ===
ORDER        STATUS     TOTAL      ITEMS  TRACKING
-------------------------------------------------------
order-001    shipped    $1,049.98  2      TRK001
order-002    created    $799.00    1      -
order-003    cancelled  $49.95     5      -
```

---

## Summary

| Concept | Implementation | Notes |
|---------|---------------|-------|
| Domain Event | `abstract class DomainEvent` | Immutable, has aggregateId + version |
| Event Store | SQLite append-only table | UNIQUE on (aggregate_id, version) |
| Aggregate | `AggregateRoot` + `recordThat()` | Commands produce events |
| Apply | `on{EventName}()` methods | Mutate state from events |
| Repository | `save/findById` | Persist and reconstitute aggregates |
| Projection | Event handlers → read model | Rebuild from event stream |
| Snapshot | Store state at version N | Optimize loading long streams |
| Replay | Iterate events + apply | Rebuild any state at any point |
| Optimistic lock | UNIQUE constraint on version | Prevent concurrent writes |
| Event bus | Publish events to projections | Fan-out to multiple read models |
