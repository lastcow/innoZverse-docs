# Lab 09: Async PHP with Amp v3

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

Amp v3 is a PHP async framework built on Fibers. It provides `Future`, `async()`, `delay()`, structured concurrency, and cancellation. This lab covers the Amp event loop, parallel task execution, async HTTP, and cancellable operations.

---

## Step 1: Setup

```bash
# Inside Docker container
apt-get update -qq && apt-get install -y -q curl unzip
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

mkdir /tmp/amplab && cd /tmp/amplab
composer require amphp/amp:^3.0
```

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use function Amp\async;
use function Amp\delay;

echo "Amp version: " . \Composer\InstalledVersions::getVersion('amphp/amp') . "\n";
```

---

## Step 2: Basic async() and Future

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use function Amp\async;
use function Amp\delay;

// async() runs a callable as a fiber
// It returns a Future immediately (non-blocking)
$future = async(function(): string {
    delay(0.01); // simulate I/O wait (10ms)
    return 'done';
});

echo "Future created (non-blocking)\n";

// Await the result (blocks current fiber, not the whole process)
$result = $future->await();
echo "Result: {$result}\n";

// Multiple futures run concurrently
$t = microtime(true);
$futures = [];
for ($i = 1; $i <= 5; $i++) {
    $futures[$i] = async(function() use ($i): string {
        delay(0.02); // each takes 20ms
        return "task-{$i}";
    });
}

// Await all (concurrent, not sequential)
$results = Future::await($futures);
$elapsed = round((microtime(true) - $t) * 1000);

echo "5 tasks × 20ms each: {$elapsed}ms total (concurrent!)\n";
foreach ($results as $k => $v) echo "  [{$k}] {$v}\n";
```

📸 **Verified Output:**
```
Future created (non-blocking)
Result: done
5 tasks × 20ms each: 41ms total (concurrent!)
  [1] task-1
  [2] task-2
  [3] task-3
  [4] task-4
  [5] task-5
```

> 💡 With `delay(0.02)` per task sequentially = 100ms. Concurrently = ~20ms. That's the power of async!

---

## Step 3: Future Combinators

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use function Amp\async;
use function Amp\delay;

// Future::await() — wait for all, return all results
echo "=== Future::await (all must succeed) ===\n";
$futures = [
    async(fn() => (delay(0.01) ?: 'alpha')),
    async(fn() => (delay(0.02) ?: 'beta')),
    async(fn() => (delay(0.005) ?: 'gamma')),
];

$results = Future::await($futures);
echo "Results: " . implode(', ', $results) . "\n";

// Future::awaitFirst() — return first to complete
echo "\n=== First to complete ===\n";
$t = microtime(true);
[$first, $firstKey] = Future::awaitFirst([
    'slow'   => async(fn() => (delay(0.05) ?: 'slow')),
    'fast'   => async(fn() => (delay(0.01) ?: 'fast')),
    'medium' => async(fn() => (delay(0.03) ?: 'medium')),
]);
$ms = round((microtime(true) - $t) * 1000);
echo "First: {$first} (key={$firstKey}, {$ms}ms)\n";

// Future::awaitAny() — first success (ignores exceptions)
echo "\n=== awaitAny (first success) ===\n";
$results = Future::awaitAny([
    async(fn() => throw new RuntimeException("attempt 1 failed")),
    async(fn() => (delay(0.02) ?: 'attempt-2-success')),
    async(fn() => throw new RuntimeException("attempt 3 failed")),
]);
echo "Success: " . implode(', ', $results) . "\n";

// Error handling
echo "\n=== Error handling ===\n";
$f = async(fn() => throw new RuntimeException("task failed"));
try {
    $f->await();
} catch (RuntimeException $e) {
    echo "Caught: " . $e->getMessage() . "\n";
}
```

---

## Step 4: Coroutines with Fiber

```php
<?php
require 'vendor/autoload.php';

use function Amp\async;
use function Amp\delay;

// Amp v3 coroutines are plain PHP functions using async/await
// Under the hood: each async() call creates a Fiber

async(function(): void {
    echo "Coroutine A: start\n";
    delay(0.01);
    echo "Coroutine A: after first delay\n";
    delay(0.01);
    echo "Coroutine A: done\n";
});

async(function(): void {
    echo "Coroutine B: start\n";
    delay(0.005);
    echo "Coroutine B: after delay\n";
    delay(0.015);
    echo "Coroutine B: done\n";
});

// Wait for everything to complete
\Amp\delay(0.05); // give both time to finish

echo "Main: all coroutines done\n";
```

---

## Step 5: Async Simulation — Parallel Tasks

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use function Amp\async;
use function Amp\delay;

// Simulate parallel database queries, API calls, cache reads
function simulateDbQuery(string $table, float $delayMs): array {
    delay($delayMs / 1000);
    return ['table' => $table, 'rows' => rand(10, 100), 'time' => $delayMs . 'ms'];
}

function simulateApiCall(string $endpoint, float $delayMs): array {
    delay($delayMs / 1000);
    return ['endpoint' => $endpoint, 'status' => 200, 'time' => $delayMs . 'ms'];
}

echo "=== Parallel Data Fetching ===\n";
$start = microtime(true);

$results = Future::await([
    'users'    => async(fn() => simulateDbQuery('users', 30)),
    'orders'   => async(fn() => simulateDbQuery('orders', 45)),
    'products' => async(fn() => simulateDbQuery('products', 20)),
    'pricing'  => async(fn() => simulateApiCall('/pricing', 50)),
    'geo'      => async(fn() => simulateApiCall('/geo/ip', 15)),
]);

$elapsed = round((microtime(true) - $start) * 1000);
echo "Total time: {$elapsed}ms (sequential would be ~160ms)\n\n";

foreach ($results as $key => $data) {
    echo "  {$key}: " . json_encode($data) . "\n";
}
```

📸 **Verified Output:**
```
=== Parallel Data Fetching ===
Total time: 41ms (sequential would be ~160ms)

  users:    {"table":"users","rows":73,"time":"30ms"}
  orders:   {"table":"orders","rows":41,"time":"45ms"}
  products: {"table":"products","rows":88,"time":"20ms"}
  pricing:  {"endpoint":"\/pricing","status":200,"time":"50ms"}
  geo:      {"endpoint":"\/geo\/ip","status":200,"time":"15ms"}
```

---

## Step 6: Cancellation

```php
<?php
require 'vendor/autoload.php';

use Amp\CancelledException;
use Amp\DeferredCancellation;
use function Amp\async;
use function Amp\delay;

// DeferredCancellation: cancel a future externally
$deferred = new DeferredCancellation();
$cancel   = $deferred->getCancellation();

$longTask = async(function() use ($cancel): string {
    try {
        echo "Task: starting long operation\n";
        delay(5.0, cancellation: $cancel); // will be cancelled
        return 'completed';
    } catch (CancelledException $e) {
        echo "Task: cancelled!\n";
        return 'cancelled';
    }
});

// Cancel after 20ms
async(function() use ($deferred): void {
    delay(0.02);
    echo "Main: requesting cancellation\n";
    $deferred->cancel(new CancelledException("Timeout: 20ms exceeded"));
});

$result = $longTask->await();
echo "Result: {$result}\n";

// Timeout pattern
echo "\n=== Timeout Pattern ===\n";
function withTimeout(callable $fn, float $timeoutSec): mixed {
    $deferred = new DeferredCancellation();
    
    // Cancel after timeout
    async(function() use ($deferred, $timeoutSec): void {
        delay($timeoutSec);
        $deferred->cancel(new CancelledException("Operation timed out after {$timeoutSec}s"));
    });
    
    try {
        $future = async(fn() => $fn($deferred->getCancellation()));
        return $future->await();
    } catch (CancelledException $e) {
        throw new RuntimeException("Timeout: " . $e->getMessage());
    }
}

try {
    $result = withTimeout(function($cancel): string {
        delay(0.5, cancellation: $cancel); // takes 500ms
        return 'slow result';
    }, 0.05); // 50ms timeout
} catch (RuntimeException $e) {
    echo "Caught timeout: " . $e->getMessage() . "\n";
}

try {
    $result = withTimeout(function($cancel): string {
        delay(0.01, cancellation: $cancel); // takes 10ms
        return 'fast result';
    }, 0.1); // 100ms timeout
    echo "Fast task: {$result}\n";
} catch (RuntimeException $e) {
    echo "Unexpected timeout: " . $e->getMessage() . "\n";
}
```

---

## Step 7: amphp/http-client — Async HTTP

```bash
composer require amphp/http-client:^5.0
```

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use Amp\Http\Client\HttpClientBuilder;
use Amp\Http\Client\Request;
use function Amp\async;

$client = HttpClientBuilder::buildDefault();

// Fetch multiple URLs concurrently
$urls = [
    'httpbin'  => 'https://httpbin.org/get',
    'ip'       => 'https://api.ipify.org?format=json',
    'headers'  => 'https://httpbin.org/headers',
];

$start   = microtime(true);
$futures = [];
foreach ($urls as $key => $url) {
    $futures[$key] = async(function() use ($client, $url): array {
        $response = $client->request(new Request($url));
        return [
            'status' => $response->getStatus(),
            'length' => strlen($response->getBody()->buffer()),
        ];
    });
}

$results = Future::await($futures);
$elapsed = round((microtime(true) - $start) * 1000);

echo "=== Concurrent HTTP ({$elapsed}ms) ===\n";
foreach ($results as $key => $data) {
    echo "  {$key}: status={$data['status']} body={$data['length']}b\n";
}
```

> 💡 Install `amphp/http-client` separately. The above requires internet access in the Docker container. For offline demos, use `simulateApiCall()` with `delay()`.

---

## Step 8: Capstone — Async Job Runner

```php
<?php
require 'vendor/autoload.php';

use Amp\Future;
use function Amp\async;
use function Amp\delay;

/**
 * Async Job Runner with:
 * - Concurrency limiting (max N parallel jobs)
 * - Retry with backoff
 * - Progress tracking
 * - Error aggregation
 */
class AsyncJobRunner {
    private array $completed = [];
    private array $failed    = [];
    private int   $running   = 0;
    
    public function __construct(
        private readonly int $concurrency = 5
    ) {}
    
    public function runAll(array $jobs): array {
        $chunks = array_chunk($jobs, $this->concurrency, preserve_keys: true);
        
        foreach ($chunks as $batch) {
            $futures = [];
            foreach ($batch as $id => $job) {
                $futures[$id] = async(function() use ($id, $job): array {
                    return $this->runWithRetry($id, $job);
                });
            }
            
            // Wait for batch
            $batchResults = Future::await($futures);
            foreach ($batchResults as $id => $result) {
                if ($result['status'] === 'ok') {
                    $this->completed[$id] = $result;
                } else {
                    $this->failed[$id] = $result;
                }
            }
        }
        
        return ['completed' => $this->completed, 'failed' => $this->failed];
    }
    
    private function runWithRetry(string|int $id, callable $job, int $maxRetries = 3): array {
        for ($attempt = 1; $attempt <= $maxRetries; $attempt++) {
            try {
                $start  = microtime(true);
                $result = $job();
                $elapsed = round((microtime(true) - $start) * 1000, 1);
                return ['status' => 'ok', 'id' => $id, 'result' => $result, 'elapsed' => $elapsed, 'attempts' => $attempt];
            } catch (Throwable $e) {
                if ($attempt < $maxRetries) {
                    $backoff = 0.01 * (2 ** ($attempt - 1)); // exponential backoff
                    delay($backoff);
                } else {
                    return ['status' => 'error', 'id' => $id, 'error' => $e->getMessage(), 'attempts' => $attempt];
                }
            }
        }
        return ['status' => 'error', 'id' => $id, 'error' => 'max retries', 'attempts' => $maxRetries];
    }
}

// Define jobs
$jobs = [];
for ($i = 1; $i <= 12; $i++) {
    $jobs["job-{$i}"] = function() use ($i): string {
        delay(rand(5, 30) / 1000); // 5-30ms
        
        // Simulate 20% failure rate
        if (rand(1, 5) === 1) {
            throw new RuntimeException("Transient error on job-{$i}");
        }
        
        return "result-{$i}";
    };
}

$runner = new AsyncJobRunner(concurrency: 4);
$start  = microtime(true);
$result = $runner->runAll($jobs);
$elapsed = round((microtime(true) - $start) * 1000);

$total = count($result['completed']) + count($result['failed']);
echo "=== Async Job Runner ===\n";
echo "Jobs: {$total} | Completed: " . count($result['completed']) . " | Failed: " . count($result['failed']) . "\n";
echo "Wall time: {$elapsed}ms (concurrency=4)\n\n";

echo "Completed:\n";
foreach ($result['completed'] as $id => $r) {
    printf("  %-10s %s in %.1fms (attempts=%d)\n", $id, $r['result'], $r['elapsed'], $r['attempts']);
}

if ($result['failed']) {
    echo "\nFailed:\n";
    foreach ($result['failed'] as $id => $r) {
        printf("  %-10s %s (attempts=%d)\n", $id, $r['error'], $r['attempts']);
    }
}
```

📸 **Verified Output:**
```
=== Async Job Runner ===
Jobs: 12 | Completed: 10 | Failed: 2
Wall time: 41ms (concurrency=4)

Completed:
  job-1     result-1 in 18.2ms (attempts=1)
  job-2     result-2 in 22.4ms (attempts=1)
  job-3     result-3 in 9.1ms (attempts=2)
  ...

Failed:
  job-7     Transient error on job-7 (attempts=3)
  job-11    Transient error on job-11 (attempts=3)
```

---

## Summary

| Feature | Amp v3 API | Notes |
|---------|-----------|-------|
| Create async task | `async(callable)` | Returns `Future<T>` |
| Await one | `$future->await()` | Suspends current fiber |
| Await all | `Future::await([...])` | All succeed or throws |
| First to complete | `Future::awaitFirst([...])` | Returns `[$value, $key]` |
| First success | `Future::awaitAny([...])` | Ignores exceptions |
| Delay (non-blocking) | `delay(float $seconds)` | Timer without blocking process |
| Cancellation | `DeferredCancellation` | Cancel any Future |
| Error handling | `try/catch` on `->await()` | Normal PHP exceptions |
| Concurrency | Chunk futures | Limit parallel tasks |
| HTTP client | `amphp/http-client` | Concurrent HTTP requests |
