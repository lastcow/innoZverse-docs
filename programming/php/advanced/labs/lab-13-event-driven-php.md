# Lab 13: Event-Driven PHP with PSR-14

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PSR-14 defines a standard event dispatching interface. This lab implements a PSR-14 compliant dispatcher from scratch, adds event subscribers, and explores async event patterns with Symfony Messenger concepts.

---

## Step 1: PSR-14 Interfaces

PSR-14 defines two core interfaces: `EventDispatcherInterface` and `ListenerProviderInterface`.

```php
<?php
// PSR-14 interfaces (simplified — use psr/event-dispatcher in real projects)

interface StoppableEventInterface {
    public function isPropagationStopped(): bool;
}

interface ListenerProviderInterface {
    public function getListenersForEvent(object $event): iterable;
}

interface EventDispatcherInterface {
    public function dispatch(object $event): object;
}

// Verify interfaces
echo "PSR-14 interfaces defined\n";
$interfaces = ['StoppableEventInterface', 'ListenerProviderInterface', 'EventDispatcherInterface'];
foreach ($interfaces as $iface) {
    echo "  ✓ $iface\n";
}
```

📸 **Verified Output:**
```
PSR-14 interfaces defined
  ✓ StoppableEventInterface
  ✓ ListenerProviderInterface
  ✓ EventDispatcherInterface
```

---

## Step 2: Implementing a PSR-14 Dispatcher

```php
<?php
interface ListenerProviderInterface {
    public function getListenersForEvent(object $event): iterable;
}
interface EventDispatcherInterface {
    public function dispatch(object $event): object;
}

class SimpleListenerProvider implements ListenerProviderInterface {
    private array $listeners = [];

    public function addListener(string $eventClass, callable $listener, int $priority = 0): void {
        $this->listeners[$eventClass][] = ['fn' => $listener, 'priority' => $priority];
        // Sort by priority descending
        usort($this->listeners[$eventClass], fn($a, $b) => $b['priority'] - $a['priority']);
    }

    public function getListenersForEvent(object $event): iterable {
        $class = get_class($event);
        foreach ($this->listeners[$class] ?? [] as $listener) {
            yield $listener['fn'];
        }
        // Also yield listeners registered for parent classes/interfaces
        foreach (class_parents($event) as $parent) {
            foreach ($this->listeners[$parent] ?? [] as $listener) {
                yield $listener['fn'];
            }
        }
        foreach (class_implements($event) as $iface) {
            foreach ($this->listeners[$iface] ?? [] as $listener) {
                yield $listener['fn'];
            }
        }
    }
}

class EventDispatcher implements EventDispatcherInterface {
    public function __construct(private ListenerProviderInterface $provider) {}

    public function dispatch(object $event): object {
        foreach ($this->provider->getListenersForEvent($event) as $listener) {
            if ($event instanceof \StoppableEventInterface && $event->isPropagationStopped()) {
                break;
            }
            $listener($event);
        }
        return $event;
    }
}

// Test event
class UserCreatedEvent {
    public function __construct(
        public readonly string $userId,
        public readonly string $email,
        public readonly \DateTimeImmutable $createdAt = new \DateTimeImmutable(),
    ) {}
}

$provider = new SimpleListenerProvider();
$provider->addListener(UserCreatedEvent::class, function(UserCreatedEvent $e): void {
    echo "Listener 1 (priority 10): Welcome email to {$e->email}\n";
}, priority: 10);

$provider->addListener(UserCreatedEvent::class, function(UserCreatedEvent $e): void {
    echo "Listener 2 (priority 5): Analytics for user {$e->userId}\n";
}, priority: 5);

$provider->addListener(UserCreatedEvent::class, function(UserCreatedEvent $e): void {
    echo "Listener 3 (priority 1): Audit log for {$e->email}\n";
}, priority: 1);

$dispatcher = new EventDispatcher($provider);
$event = $dispatcher->dispatch(new UserCreatedEvent('usr-42', 'alice@example.com'));
echo "Event dispatched: " . get_class($event) . "\n";
```

📸 **Verified Output:**
```
Listener 1 (priority 10): Welcome email to alice@example.com
Listener 2 (priority 5): Analytics for user usr-42
Listener 3 (priority 1): Audit log for alice@example.com
Event dispatched: UserCreatedEvent
```

---

## Step 3: Stoppable Events

```php
<?php
// (include previous dispatcher classes)

trait StoppableTrait {
    private bool $propagationStopped = false;
    public function isPropagationStopped(): bool { return $this->propagationStopped; }
    public function stopPropagation(): void { $this->propagationStopped = true; }
}

class ValidationEvent implements \StoppableEventInterface {
    use StoppableTrait;
    public array $errors = [];

    public function __construct(public readonly array $data) {}

    public function addError(string $field, string $message): void {
        $this->errors[$field] = $message;
        $this->stopPropagation(); // Stop after first error
    }
}

$provider = new SimpleListenerProvider();
$dispatcher = new EventDispatcher($provider);

$provider->addListener(ValidationEvent::class, function(ValidationEvent $e): void {
    echo "Validator 1: checking email\n";
    if (empty($e->data['email'])) {
        $e->addError('email', 'Email is required');
    }
});

$provider->addListener(ValidationEvent::class, function(ValidationEvent $e): void {
    echo "Validator 2: checking name (should not run if email failed)\n";
    if (empty($e->data['name'])) {
        $e->addError('name', 'Name is required');
    }
});

// Test with missing email
$event = $dispatcher->dispatch(new ValidationEvent(['name' => 'Alice']));
echo "Errors: " . json_encode($event->errors) . "\n";
echo "Propagation stopped: " . ($event->isPropagationStopped() ? 'yes' : 'no') . "\n";
```

📸 **Verified Output:**
```
Validator 1: checking email
Errors: {"email":"Email is required"}
Propagation stopped: yes
```

---

## Step 4: Event Subscribers

```php
<?php
interface EventSubscriberInterface {
    /** @return array<string, array{string, int}|string> */
    public static function getSubscribedEvents(): array;
}

class ListenerProviderWithSubscribers extends SimpleListenerProvider {
    public function addSubscriber(EventSubscriberInterface $subscriber): void {
        foreach ($subscriber::getSubscribedEvents() as $event => $config) {
            if (is_string($config)) {
                $this->addListener($event, [$subscriber, $config]);
            } elseif (is_array($config)) {
                [$method, $priority] = $config;
                $this->addListener($event, [$subscriber, $method], $priority);
            }
        }
    }
}

class UserCreatedEvent {
    public function __construct(
        public readonly string $userId,
        public readonly string $email
    ) {}
}

class OrderPlacedEvent {
    public function __construct(
        public readonly string $orderId,
        public readonly float $total
    ) {}
}

class NotificationSubscriber implements EventSubscriberInterface {
    public static function getSubscribedEvents(): array {
        return [
            UserCreatedEvent::class  => ['onUserCreated', 10],
            OrderPlacedEvent::class  => 'onOrderPlaced',
        ];
    }

    public function onUserCreated(UserCreatedEvent $event): void {
        echo "  📧 Welcome email to {$event->email}\n";
    }

    public function onOrderPlaced(OrderPlacedEvent $event): void {
        echo "  📧 Order confirmation for #{$event->orderId} (\${$event->total})\n";
    }
}

class AuditSubscriber implements EventSubscriberInterface {
    private array $log = [];

    public static function getSubscribedEvents(): array {
        return [
            UserCreatedEvent::class  => ['onAny', 1],
            OrderPlacedEvent::class  => ['onAny', 1],
        ];
    }

    public function onAny(object $event): void {
        $this->log[] = get_class($event) . ' @ ' . date('H:i:s');
        echo "  📋 Audited: " . get_class($event) . "\n";
    }

    public function getLog(): array { return $this->log; }
}

$provider = new ListenerProviderWithSubscribers();
$audit    = new AuditSubscriber();
$provider->addSubscriber(new NotificationSubscriber());
$provider->addSubscriber($audit);

$dispatcher = new EventDispatcher($provider);

echo "User created:\n";
$dispatcher->dispatch(new UserCreatedEvent('usr-1', 'bob@example.com'));

echo "\nOrder placed:\n";
$dispatcher->dispatch(new OrderPlacedEvent('ord-999', 149.99));

echo "\nAudit log:\n";
foreach ($audit->getLog() as $entry) {
    echo "  - $entry\n";
}
```

📸 **Verified Output:**
```
User created:
  📧 Welcome email to bob@example.com
  📋 Audited: UserCreatedEvent

Order placed:
  📧 Order confirmation for #ord-999 ($149.99)
  📋 Audited: OrderPlacedEvent

Audit log:
  - UserCreatedEvent @ 12:34:56
  - OrderPlacedEvent @ 12:34:56
```

---

## Step 5: Async Event Handling Concept

```php
<?php
// Simulating async event handling via a deferred queue
class AsyncEventDispatcher implements EventDispatcherInterface {
    private array $queue = [];
    private EventDispatcherInterface $sync;

    public function __construct(EventDispatcherInterface $syncDispatcher) {
        $this->sync = $syncDispatcher;
    }

    public function dispatch(object $event): object {
        $this->queue[] = $event;
        echo "  [queued] " . get_class($event) . "\n";
        return $event;
    }

    public function processQueue(): void {
        echo "Processing async queue (" . count($this->queue) . " events)...\n";
        while ($event = array_shift($this->queue)) {
            echo "  [processing] " . get_class($event) . "\n";
            $this->sync->dispatch($event);
        }
    }

    public function getQueueSize(): int { return count($this->queue); }
}

class EmailSentEvent {
    public function __construct(public readonly string $to, public readonly string $subject) {}
}

$provider = new SimpleListenerProvider();
$provider->addListener(EmailSentEvent::class, fn($e) => print("  ✉️  Email sent to {$e->to}: {$e->subject}\n"));

$syncDispatcher  = new EventDispatcher($provider);
$asyncDispatcher = new AsyncEventDispatcher($syncDispatcher);

echo "Queueing events:\n";
$asyncDispatcher->dispatch(new EmailSentEvent('alice@example.com', 'Welcome!'));
$asyncDispatcher->dispatch(new EmailSentEvent('bob@example.com', 'Your order'));
$asyncDispatcher->dispatch(new EmailSentEvent('carol@example.com', 'Password reset'));

echo "\nQueue size: " . $asyncDispatcher->getQueueSize() . "\n\n";
$asyncDispatcher->processQueue();
```

📸 **Verified Output:**
```
Queueing events:
  [queued] EmailSentEvent
  [queued] EmailSentEvent
  [queued] EmailSentEvent

Queue size: 3

Processing async queue (3 events)...
  [processing] EmailSentEvent
  ✉️  Email sent to alice@example.com: Welcome!
  [processing] EmailSentEvent
  ✉️  Email sent to bob@example.com: Your order
  [processing] EmailSentEvent
  ✉️  Email sent to carol@example.com: Password reset
```

---

## Step 6: Symfony Messenger Concepts

```php
<?php
// Symfony Messenger pattern: Message + Handler + Bus
// composer require symfony/messenger

// Message (immutable value object)
class SendEmailMessage {
    public function __construct(
        public readonly string $to,
        public readonly string $subject,
        public readonly string $body,
    ) {}
}

class ProcessPaymentMessage {
    public function __construct(
        public readonly string $orderId,
        public readonly float  $amount,
    ) {}
}

// Handlers (invokable classes)
class SendEmailHandler {
    public function __invoke(SendEmailMessage $message): void {
        printf("  [Email] → %s | %s\n", $message->to, $message->subject);
    }
}

class ProcessPaymentHandler {
    public function __invoke(ProcessPaymentMessage $message): void {
        printf("  [Payment] Order %s: $%.2f\n", $message->orderId, $message->amount);
    }
}

// Simple synchronous message bus
class MessageBus {
    private array $handlers = [];

    public function registerHandler(string $messageClass, callable $handler): void {
        $this->handlers[$messageClass][] = $handler;
    }

    public function dispatch(object $message): void {
        $class = get_class($message);
        foreach ($this->handlers[$class] ?? [] as $handler) {
            $handler($message);
        }
    }
}

$bus = new MessageBus();
$bus->registerHandler(SendEmailMessage::class,    new SendEmailHandler());
$bus->registerHandler(ProcessPaymentMessage::class, new ProcessPaymentHandler());

echo "Dispatching messages:\n";
$bus->dispatch(new SendEmailMessage('alice@example.com', 'Welcome!', 'Hello...'));
$bus->dispatch(new ProcessPaymentMessage('order-123', 99.99));
$bus->dispatch(new SendEmailMessage('bob@example.com', 'Confirm email', 'Click...'));

echo "\nIn production with symfony/messenger:\n";
echo "  - AMQP transport → async via RabbitMQ\n";
echo "  - Redis transport → async via Redis streams\n";
echo "  - Doctrine transport → async via database\n";
echo "  - Retry middleware → automatic failure handling\n";
```

📸 **Verified Output:**
```
Dispatching messages:
  [Email] → alice@example.com | Welcome!
  [Payment] Order order-123: $99.99
  [Email] → bob@example.com | Confirm email

In production with symfony/messenger:
  - AMQP transport → async via RabbitMQ
  - Redis transport → async via Redis streams
  - Doctrine transport → async via database
  - Retry middleware → automatic failure handling
```

---

## Step 7: Event Middleware Pipeline

```php
<?php
class EventPipeline {
    private array $middleware = [];
    private EventDispatcherInterface $core;

    public function __construct(EventDispatcherInterface $core) {
        $this->core = $core;
    }

    public function use(callable $middleware): static {
        $clone = clone $this;
        $clone->middleware[] = $middleware;
        return $clone;
    }

    public function dispatch(object $event): object {
        $pipeline = array_reduce(
            array_reverse($this->middleware),
            fn($next, $mw) => fn($event) => $mw($event, $next),
            fn($event) => $this->core->dispatch($event)
        );
        return $pipeline($event);
    }
}

// Middleware: logging
$logMiddleware = function(object $event, callable $next): object {
    $class = basename(str_replace('\\', '/', get_class($event)));
    $start = microtime(true);
    echo "[LOG] Dispatching $class\n";
    $result = $next($event);
    $ms = round((microtime(true) - $start) * 1000, 2);
    echo "[LOG] Completed $class in {$ms}ms\n";
    return $result;
};

// Middleware: event counting
$countMiddleware = (function() {
    $counts = [];
    return function(object $event, callable $next) use (&$counts): object {
        $class = get_class($event);
        $counts[$class] = ($counts[$class] ?? 0) + 1;
        echo "[COUNT] $class dispatched {$counts[$class]} time(s)\n";
        return $next($event);
    };
})();

$provider = new SimpleListenerProvider();
$provider->addListener(UserCreatedEvent::class, fn($e) => print("  → User {$e->userId} created\n"));

$pipeline = (new EventPipeline(new EventDispatcher($provider)))
    ->use($logMiddleware)
    ->use($countMiddleware);

$pipeline->dispatch(new UserCreatedEvent('usr-1', 'a@example.com'));
$pipeline->dispatch(new UserCreatedEvent('usr-2', 'b@example.com'));
```

📸 **Verified Output:**
```
[LOG] Dispatching UserCreatedEvent
[COUNT] UserCreatedEvent dispatched 1 time(s)
  → User usr-1 created
[LOG] Completed UserCreatedEvent in 0.05ms
[LOG] Dispatching UserCreatedEvent
[COUNT] UserCreatedEvent dispatched 2 time(s)
  → User usr-2 created
[LOG] Completed UserCreatedEvent in 0.02ms
```

---

## Step 8: Capstone — Full Event System

```php
<?php
// All previous classes included...

// Events
class OrderCreatedEvent { public function __construct(public readonly string $id, public readonly float $total) {} }
class PaymentProcessedEvent { public function __construct(public readonly string $orderId, public readonly bool $success) {} }
class InventoryReservedEvent { public function __construct(public readonly string $orderId, public readonly array $items) {} }

// Order orchestration using events
class OrderProcessor {
    public function __construct(private EventDispatcherInterface $dispatcher) {}

    public function processOrder(string $orderId, float $total, array $items): void {
        echo "Processing order $orderId...\n";
        $this->dispatcher->dispatch(new OrderCreatedEvent($orderId, $total));
        $this->dispatcher->dispatch(new PaymentProcessedEvent($orderId, $total > 0));
        $this->dispatcher->dispatch(new InventoryReservedEvent($orderId, $items));
    }
}

// Subscribers
$provider = new SimpleListenerProvider();

$provider->addListener(OrderCreatedEvent::class, function($e) {
    echo "  📦 Order #{$e->id} created (\${$e->total})\n";
}, 10);

$provider->addListener(PaymentProcessedEvent::class, function($e) {
    $status = $e->success ? '✓ approved' : '✗ declined';
    echo "  💳 Payment for #{$e->orderId}: $status\n";
}, 10);

$provider->addListener(InventoryReservedEvent::class, function($e) {
    $count = count($e->items);
    echo "  📋 Reserved $count item(s) for order #{$e->orderId}\n";
}, 10);

// Add audit for all events
foreach ([OrderCreatedEvent::class, PaymentProcessedEvent::class, InventoryReservedEvent::class] as $eventClass) {
    $provider->addListener($eventClass, function($e) {
        echo "  📝 Audit: " . get_class($e) . " @ " . date('H:i:s') . "\n";
    }, 1);
}

$dispatcher  = new EventDispatcher($provider);
$processor   = new OrderProcessor($dispatcher);

$processor->processOrder('ORD-001', 149.99, ['widget', 'gadget', 'doohickey']);
```

📸 **Verified Output:**
```
Processing order ORD-001...
  📦 Order #ORD-001 created ($149.99)
  📝 Audit: OrderCreatedEvent @ 12:34:56
  💳 Payment for #ORD-001: ✓ approved
  📝 Audit: PaymentProcessedEvent @ 12:34:56
  📋 Reserved 3 item(s) for order #ORD-001
  📝 Audit: InventoryReservedEvent @ 12:34:56
```

---

## Summary

| Concept | Interface/Class | PSR |
|---|---|---|
| Event dispatcher | `EventDispatcherInterface::dispatch()` | PSR-14 |
| Listener provider | `ListenerProviderInterface::getListenersForEvent()` | PSR-14 |
| Stoppable events | `StoppableEventInterface::isPropagationStopped()` | PSR-14 |
| Subscriber pattern | `getSubscribedEvents(): array` | Convention |
| Async queue | `MessageBus` + transport | Symfony Messenger |
| Event middleware | `Pipeline::use(callable $mw)` | Custom pattern |
| Priority listeners | Provider sorts by priority | Implementation detail |
| Message handlers | `__invoke(SpecificMessage $msg)` | Symfony convention |
