# Lab 01: PHP 8.1 Fibers & Cooperative Multitasking

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

Fibers introduce first-class coroutine support in PHP 8.1. Unlike threads, Fibers cooperatively yield control — enabling async-style patterns without extensions.

---

## Step 1: Your First Fiber

A Fiber wraps a callable. Control only switches when explicitly suspended or resumed.

```php
<?php
$fiber = new Fiber(function(): string {
    echo "Fiber: starting\n";
    $value = Fiber::suspend('paused here');
    echo "Fiber: resumed with '$value'\n";
    return 'done';
});

$suspended = $fiber->start();       // Run until first suspend
echo "Main: fiber suspended with '$suspended'\n";
$fiber->resume('hello');            // Resume with a value
echo "Main: fiber returned: " . $fiber->getReturn() . "\n";
```

📸 **Verified Output:**
```
Fiber: starting
Main: fiber suspended with 'paused here'
Fiber: resumed with 'hello'
Main: fiber returned: done
```

> 💡 `Fiber::suspend()` is a static method called **inside** the fiber. `$fiber->resume()` is called **outside**.

---

## Step 2: Fiber Lifecycle States

```php
<?php
$fiber = new Fiber(function(): void {
    Fiber::suspend();
});

var_dump($fiber->isStarted());      // false
var_dump($fiber->isSuspended());    // false

$fiber->start();

var_dump($fiber->isStarted());      // true
var_dump($fiber->isSuspended());    // true
var_dump($fiber->isRunning());      // false

$fiber->resume();

var_dump($fiber->isTerminated());   // true
```

📸 **Verified Output:**
```
bool(false)
bool(false)
bool(true)
bool(true)
bool(false)
bool(true)
```

> 💡 A Fiber can only be in one state at a time: Not Started → Running → Suspended ⇄ Running → Terminated.

---

## Step 3: Passing Values In and Out

```php
<?php
$fiber = new Fiber(function(): string {
    $val1 = Fiber::suspend('first suspend');
    echo "Got: $val1\n";
    $val2 = Fiber::suspend('second suspend');
    echo "Got: $val2\n";
    return 'fiber done';
});

$r1 = $fiber->start();
echo "Suspended with: $r1\n";

$r2 = $fiber->resume('hello');
echo "Suspended with: $r2\n";

$fiber->resume('world');
echo "Return: " . $fiber->getReturn() . "\n";
echo "isTerminated: " . ($fiber->isTerminated() ? 'true' : 'false') . "\n";
```

📸 **Verified Output:**
```
Suspended with: first suspend
Got: hello
Suspended with: second suspend
Got: world
Return: fiber done
isTerminated: true
```

---

## Step 4: Fiber Exception Handling

```php
<?php
$fiber = new Fiber(function(): void {
    try {
        Fiber::suspend('ready');
    } catch (\Exception $e) {
        echo "Fiber caught: " . $e->getMessage() . "\n";
        Fiber::suspend('handled');
    }
});

$fiber->start();
$result = $fiber->throw(new \Exception('injected error'));
echo "After throw, suspended with: $result\n";
$fiber->resume();
```

📸 **Verified Output:**
```
Fiber caught: injected error
After throw, suspended with: handled
```

> 💡 `$fiber->throw(Throwable)` injects an exception at the suspension point inside the fiber.

---

## Step 5: Simple Cooperative Scheduler

```php
<?php
class Scheduler {
    private array $fibers = [];

    public function add(callable $task): void {
        $this->fibers[] = new Fiber($task);
    }

    public function run(): void {
        // Start all fibers
        foreach ($this->fibers as $fiber) {
            $fiber->start();
        }
        // Round-robin resume until all done
        while (true) {
            $allDone = true;
            foreach ($this->fibers as $fiber) {
                if (!$fiber->isTerminated()) {
                    $allDone = false;
                    $fiber->resume();
                }
            }
            if ($allDone) break;
        }
    }
}

$scheduler = new Scheduler();

$scheduler->add(function(): void {
    echo "Task A: step 1\n";
    Fiber::suspend();
    echo "Task A: step 2\n";
    Fiber::suspend();
    echo "Task A: done\n";
});

$scheduler->add(function(): void {
    echo "Task B: step 1\n";
    Fiber::suspend();
    echo "Task B: done\n";
});

$scheduler->run();
```

📸 **Verified Output:**
```
Task A: step 1
Task B: step 1
Task A: step 2
Task B: done
Task A: done
```

---

## Step 6: Coroutine Pipeline Pattern

Chain fibers as processing stages:

```php
<?php
function producer(): \Generator {
    $items = ['apple', 'banana', 'cherry'];
    foreach ($items as $item) {
        $fiber = new Fiber(function() use ($item): string {
            Fiber::suspend("processing: $item");
            return strtoupper($item);
        });
        $msg = $fiber->start();
        echo "Stage 1 - $msg\n";
        $fiber->resume();
        yield $fiber->getReturn();
    }
}

foreach (producer() as $result) {
    echo "Stage 2 - Result: $result\n";
}
```

📸 **Verified Output:**
```
Stage 1 - processing: apple
Stage 2 - Result: APPLE
Stage 1 - processing: banana
Stage 2 - Result: BANANA
Stage 1 - processing: cherry
Stage 2 - Result: CHERRY
```

---

## Step 7: Simulated Async I/O

```php
<?php
class FakeAsyncDB {
    public static function query(string $sql): Fiber {
        return new Fiber(function() use ($sql): array {
            echo "DB: starting query '$sql'\n";
            Fiber::suspend('pending');
            // Simulate result after "I/O"
            return ['id' => 1, 'name' => 'Alice', 'query' => $sql];
        });
    }
}

// Launch two concurrent queries
$q1 = FakeAsyncDB::query('SELECT user');
$q2 = FakeAsyncDB::query('SELECT orders');

$q1->start();  // Both start
$q2->start();

// "I/O completes" — resume both
$q1->resume();
$q2->resume();

$r1 = $q1->getReturn();
$r2 = $q2->getReturn();

echo "Query 1: {$r1['name']} (from {$r1['query']})\n";
echo "Query 2 complete: {$r2['query']}\n";
```

📸 **Verified Output:**
```
DB: starting query 'SELECT user'
DB: starting query 'SELECT orders'
Query 1: Alice (from SELECT user)
Query 2 complete: SELECT orders
```

> 💡 This pattern forms the basis of real async PHP frameworks like ReactPHP and Amp v3.

---

## Step 8: Capstone — Task Runner with Priorities

Build a priority-aware cooperative task runner:

```php
<?php
class PriorityTaskRunner {
    private array $tasks = [];

    public function schedule(string $name, callable $fn, int $priority = 0): void {
        $this->tasks[] = [
            'name' => $name,
            'fiber' => new Fiber($fn),
            'priority' => $priority,
            'started' => false,
        ];
        usort($this->tasks, fn($a, $b) => $b['priority'] - $a['priority']);
    }

    public function run(): void {
        // Start all
        foreach ($this->tasks as &$task) {
            $suspended = $task['fiber']->start();
            $task['started'] = true;
            if ($suspended) {
                echo "[{$task['name']}] yielded: $suspended\n";
            }
        }
        unset($task);

        // Resume until all done
        while (true) {
            $active = array_filter($this->tasks, fn($t) => !$t['fiber']->isTerminated());
            if (empty($active)) break;
            foreach ($active as &$task) {
                $result = $task['fiber']->resume();
                if ($task['fiber']->isTerminated()) {
                    echo "[{$task['name']}] completed → " . $task['fiber']->getReturn() . "\n";
                } elseif ($result) {
                    echo "[{$task['name']}] yielded: $result\n";
                }
            }
            unset($task);
        }
    }
}

$runner = new PriorityTaskRunner();

$runner->schedule('LowPriority', function(): string {
    Fiber::suspend('low-step-1');
    Fiber::suspend('low-step-2');
    return 'low-done';
}, priority: 1);

$runner->schedule('HighPriority', function(): string {
    Fiber::suspend('high-step-1');
    return 'high-done';
}, priority: 10);

$runner->schedule('MidPriority', function(): string {
    Fiber::suspend('mid-step-1');
    return 'mid-done';
}, priority: 5);

$runner->run();
```

📸 **Verified Output:**
```
[HighPriority] yielded: high-step-1
[MidPriority] yielded: mid-step-1
[LowPriority] yielded: low-step-1
[HighPriority] completed → high-done
[MidPriority] completed → mid-done
[LowPriority] yielded: low-step-2
[LowPriority] completed → low-done
```

---

## Summary

| Concept | Method/Feature | Notes |
|---|---|---|
| Create Fiber | `new Fiber(callable)` | Wraps any callable |
| Start execution | `$fiber->start(...$args)` | Returns first suspended value |
| Suspend from inside | `Fiber::suspend($value)` | Static method inside fiber |
| Resume from outside | `$fiber->resume($value)` | Returns next suspended value |
| Inject exception | `$fiber->throw(Throwable)` | Throws at suspension point |
| Get return value | `$fiber->getReturn()` | Only after termination |
| Check state | `isStarted/isSuspended/isRunning/isTerminated` | Mutually exclusive states |
| Use case | Cooperative multitasking | Schedulers, async I/O simulation |
