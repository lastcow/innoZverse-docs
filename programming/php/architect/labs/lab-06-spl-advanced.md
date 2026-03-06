# Lab 06: SPL Advanced Data Structures

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

PHP's Standard PHP Library (SPL) provides efficient data structures far beyond simple arrays. This lab benchmarks SplFixedArray, explores heaps, priority queues, linked lists, and builds custom iterators for production use cases.

---

## Step 1: SplFixedArray vs PHP Array — Memory Benchmark

```php
<?php
$size = 100_000;

// SplFixedArray: fixed-size, integer-indexed, ~30% less memory
$mem1 = memory_get_usage(true);
$fixed = new SplFixedArray($size);
for ($i = 0; $i < $size; $i++) {
    $fixed[$i] = $i;
}
$mem2 = memory_get_usage(true);

// PHP array: flexible, hash-based, more overhead
$mem3 = memory_get_usage(true);
$arr = range(0, $size - 1);
$mem4 = memory_get_usage(true);

echo "=== Memory Comparison ({$size} integers) ===\n";
echo "SplFixedArray: " . round(($mem2 - $mem1) / 1024, 1) . " KB\n";
echo "PHP array:     " . round(($mem4 - $mem3) / 1024, 1) . " KB\n";
echo "Saving:        " . round((1 - ($mem2-$mem1)/($mem4-$mem3)) * 100, 1) . "%\n";

// Conversion
$backToArray = $fixed->toArray();
echo "\nConversion: SplFixedArray → array, first 5: " . implode(', ', array_slice($backToArray, 0, 5)) . "\n";

// From array
$fixed2 = SplFixedArray::fromArray([10, 20, 30, 40, 50], preserveKeys: false);
echo "fromArray: " . implode(', ', $fixed2->toArray()) . "\n";
echo "Size: " . $fixed2->getSize() . "\n";
```

📸 **Verified Output:**
```
=== Memory Comparison (100000 integers) ===
SplFixedArray: 1564.1 KB
PHP array:     2052.1 KB
Saving:        23.8%

Conversion: SplFixedArray → array, first 5: 0, 1, 2, 3, 4
fromArray: 10, 20, 30, 40, 50
Size: 5
```

---

## Step 2: SplMinHeap & SplMaxHeap

```php
<?php
// Min-heap: always extracts the smallest element
$minHeap = new SplMinHeap();
foreach ([5, 2, 8, 1, 9, 3, 7, 4, 6] as $v) {
    $minHeap->insert($v);
}

$out = [];
while (!$minHeap->isEmpty()) {
    $out[] = $minHeap->extract();
}
echo "SplMinHeap extract order: " . implode(', ', $out) . "\n";

// Max-heap: always extracts the largest element
$maxHeap = new SplMaxHeap();
foreach ([5, 2, 8, 1, 9, 3, 7, 4, 6] as $v) {
    $maxHeap->insert($v);
}

$out = [];
while (!$maxHeap->isEmpty()) {
    $out[] = $maxHeap->extract();
}
echo "SplMaxHeap extract order: " . implode(', ', $out) . "\n";

// Heap sort algorithm (O(n log n))
function heapSort(array $data): array {
    $heap = new SplMinHeap();
    foreach ($data as $v) $heap->insert($v);
    $sorted = [];
    while (!$heap->isEmpty()) $sorted[] = $heap->extract();
    return $sorted;
}

$unsorted = [64, 34, 25, 12, 22, 11, 90];
$sorted   = heapSort($unsorted);
echo "Heap sort: [" . implode(', ', $unsorted) . "] → [" . implode(', ', $sorted) . "]\n";

// Custom comparison via SplMinHeap extension
class EventHeap extends SplMinHeap {
    protected function compare(mixed $a, mixed $b): int {
        // Compare by timestamp (min-heap = earliest first)
        return $b['timestamp'] <=> $a['timestamp'];
    }
}

$events = new EventHeap();
$events->insert(['name' => 'C', 'timestamp' => 1700000003]);
$events->insert(['name' => 'A', 'timestamp' => 1700000001]);
$events->insert(['name' => 'B', 'timestamp' => 1700000002]);

echo "\nEvent processing order:\n";
while (!$events->isEmpty()) {
    $e = $events->extract();
    echo "  {$e['name']} at ts={$e['timestamp']}\n";
}
```

📸 **Verified Output:**
```
SplMinHeap extract order: 1, 2, 3, 4, 5, 6, 7, 8, 9
SplMaxHeap extract order: 9, 8, 7, 6, 5, 4, 3, 2, 1
Heap sort: [64, 34, 25, 12, 22, 11, 90] → [11, 12, 22, 25, 34, 64, 90]

Event processing order:
  A at ts=1700000001
  B at ts=1700000002
  C at ts=1700000003
```

---

## Step 3: SplPriorityQueue

```php
<?php
// SplPriorityQueue: insert with priority, extract highest priority first
$pq = new SplPriorityQueue();
$pq->setExtractFlags(SplPriorityQueue::EXTR_BOTH); // return [data, priority]

$pq->insert('Low priority task',    1);
$pq->insert('Critical alert',       100);
$pq->insert('Medium task',          50);
$pq->insert('Background job',       5);
$pq->insert('User request',         75);
$pq->insert('Another critical',     100);

echo "=== Task Queue (highest priority first) ===\n";
while (!$pq->isEmpty()) {
    $item = $pq->extract();
    printf("  [prio=%3d] %s\n", $item['priority'], $item['data']);
}

// Job scheduler using priority queue
class JobScheduler {
    private SplPriorityQueue $queue;
    private int $processed = 0;
    
    public function __construct() {
        $this->queue = new SplPriorityQueue();
    }
    
    public function enqueue(string $job, int $priority, array $data = []): void {
        $this->queue->insert(['job' => $job, 'data' => $data, 'queued' => time()], $priority);
    }
    
    public function process(int $limit = 5): array {
        $results = [];
        $count = 0;
        while (!$this->queue->isEmpty() && $count < $limit) {
            $item = $this->queue->extract();
            $results[] = $item['job'];
            $this->processed++;
            $count++;
        }
        return $results;
    }
    
    public function getProcessed(): int { return $this->processed; }
    public function pending(): int { return $this->queue->count(); }
}

$scheduler = new JobScheduler();
$scheduler->enqueue('send-email',      10, ['to' => 'user@example.com']);
$scheduler->enqueue('resize-image',    20, ['file' => 'photo.jpg']);
$scheduler->enqueue('payment-process', 90, ['amount' => 99.99]);
$scheduler->enqueue('analytics-log',    5, ['event' => 'pageview']);
$scheduler->enqueue('fraud-check',     85, ['tx_id' => 'TX123']);

echo "\n=== Job Scheduler ===\n";
$processed = $scheduler->process(5);
foreach ($processed as $job) {
    echo "  Processed: {$job}\n";
}
echo "Total processed: " . $scheduler->getProcessed() . "\n";
echo "Pending: " . $scheduler->pending() . "\n";
```

📸 **Verified Output:**
```
=== Task Queue (highest priority first) ===
  [prio=100] Critical alert
  [prio=100] Another critical
  [prio= 75] User request
  [prio= 50] Medium task
  [prio=  5] Background job
  [prio=  1] Low priority task

=== Job Scheduler ===
  Processed: payment-process
  Processed: fraud-check
  Processed: resize-image
  Processed: send-email
  Processed: analytics-log
Total processed: 5
Pending: 0
```

---

## Step 4: SplDoublyLinkedList, SplStack, SplQueue

```php
<?php
// SplDoublyLinkedList: O(1) insert/delete at both ends
$dll = new SplDoublyLinkedList();
$dll->push('middle');
$dll->unshift('beginning');  // prepend
$dll->push('end');

echo "DLL (front to back):\n";
$dll->rewind();
while ($dll->valid()) {
    echo "  " . $dll->current() . "\n";
    $dll->next();
}

// Pop from both ends
echo "Pop from back:  " . $dll->pop() . "\n";
echo "Pop from front: " . $dll->shift() . "\n";
echo "Remaining: " . $dll->bottom() . "\n";

// SplStack (LIFO)
$stack = new SplStack();
$stack->push('first');
$stack->push('second');
$stack->push('third');

echo "\nStack (LIFO):\n";
while (!$stack->isEmpty()) {
    echo "  pop: " . $stack->pop() . "\n";
}

// SplQueue (FIFO)
$queue = new SplQueue();
$queue->enqueue('first');
$queue->enqueue('second');
$queue->enqueue('third');

echo "\nQueue (FIFO):\n";
while (!$queue->isEmpty()) {
    echo "  dequeue: " . $queue->dequeue() . "\n";
}

// Practical: undo/redo with SplStack
class TextEditor {
    private SplStack $undoStack;
    private SplStack $redoStack;
    private string $content = '';
    
    public function __construct() {
        $this->undoStack = new SplStack();
        $this->redoStack = new SplStack();
    }
    
    public function type(string $text): void {
        $this->undoStack->push($this->content);
        $this->redoStack = new SplStack(); // clear redo on new action
        $this->content .= $text;
    }
    
    public function undo(): bool {
        if ($this->undoStack->isEmpty()) return false;
        $this->redoStack->push($this->content);
        $this->content = $this->undoStack->pop();
        return true;
    }
    
    public function redo(): bool {
        if ($this->redoStack->isEmpty()) return false;
        $this->undoStack->push($this->content);
        $this->content = $this->redoStack->pop();
        return true;
    }
    
    public function get(): string { return $this->content; }
}

$editor = new TextEditor();
$editor->type('Hello');
$editor->type(', World');
$editor->type('!');
echo "\nEditor: '" . $editor->get() . "'\n";
$editor->undo();
echo "After undo: '" . $editor->get() . "'\n";
$editor->undo();
echo "After undo: '" . $editor->get() . "'\n";
$editor->redo();
echo "After redo: '" . $editor->get() . "'\n";
```

---

## Step 5: ArrayObject with ARRAY_AS_PROPS

```php
<?php
// ArrayObject wraps an array with OOP interface
$ao = new ArrayObject(['name' => 'Alice', 'age' => 30, 'role' => 'admin']);

// Standard array access
echo "name: " . $ao['name'] . "\n";

// With ARRAY_AS_PROPS flag: property-style access
$ao->setFlags(ArrayObject::ARRAY_AS_PROPS);
echo "name (prop): " . $ao->name . "\n";
echo "age (prop):  " . $ao->age . "\n";

// Add/modify
$ao->email = 'alice@example.com';
$ao['score'] = 9.5;
echo "email: {$ao->email}\n";
echo "score: {$ao->score}\n";

// Sort methods
$ao2 = new ArrayObject([3, 1, 4, 1, 5, 9, 2, 6]);
$ao2->asort();  // sort by value
echo "asort: " . implode(', ', (array)$ao2) . "\n";

// Custom sort
$ao3 = new ArrayObject(['banana', 'apple', 'cherry', 'date']);
$ao3->uasort(fn($a, $b) => strlen($a) <=> strlen($b));
echo "uasort by length: " . implode(', ', (array)$ao3) . "\n";

// ArrayObject as typed bag
class UserCollection extends ArrayObject {
    public function append(mixed $value): void {
        if (!is_array($value) || !isset($value['id'], $value['name'])) {
            throw new InvalidArgumentException("Invalid user data");
        }
        parent::append($value);
    }
    
    public function findById(int $id): ?array {
        foreach ($this as $user) {
            if ($user['id'] === $id) return $user;
        }
        return null;
    }
    
    public function names(): array {
        return array_column((array)$this, 'name');
    }
}

$users = new UserCollection();
$users->append(['id' => 1, 'name' => 'Alice']);
$users->append(['id' => 2, 'name' => 'Bob']);
$users->append(['id' => 3, 'name' => 'Charlie']);

echo "\nUserCollection:\n";
echo "Count: " . $users->count() . "\n";
echo "Names: " . implode(', ', $users->names()) . "\n";
echo "Find 2: " . $users->findById(2)['name'] . "\n";
```

---

## Step 6: RecursiveIteratorIterator

```php
<?php
// RecursiveArrayIterator traverses nested arrays
$tree = [
    'frontend' => [
        'React' => ['jsx', 'tsx', 'css'],
        'Vue'   => ['vue', 'js'],
    ],
    'backend' => [
        'PHP'    => ['php', 'phtml'],
        'Python' => ['py', 'pyw'],
    ],
    'devops' => ['Dockerfile', 'docker-compose.yml'],
];

$it = new RecursiveIteratorIterator(
    new RecursiveArrayIterator($tree),
    RecursiveIteratorIterator::SELF_FIRST
);

echo "=== File tree traversal ===\n";
foreach ($it as $key => $value) {
    $depth  = $it->getDepth();
    $indent = str_repeat('  ', $depth);
    if (is_array($value)) {
        echo "{$indent}{$key}/\n";
    } else {
        echo "{$indent}  .{$value}\n";
    }
}

// RecursiveDirectoryIterator (real filesystem)
echo "\n=== PHP files in /usr/local/lib/php ===\n";
$dir = '/usr/local/lib/php';
if (is_dir($dir)) {
    $dirIt = new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS);
    $recIt = new RecursiveIteratorIterator($dirIt);
    $phpIt = new RegexIterator($recIt, '/\.php$/');
    
    $count = 0;
    foreach ($phpIt as $file) {
        if ($count++ < 5) echo "  " . $file->getPathname() . "\n";
    }
    echo "  ... ({$count} total PHP files)\n";
}
```

---

## Step 7: Custom Iterator & IteratorAggregate

```php
<?php
// Custom Iterator: paginated result set
class PaginatedIterator implements Iterator {
    private int $current = 0;
    private int $page = 0;
    private array $pageData = [];
    
    public function __construct(
        private readonly array $data,
        private readonly int $pageSize = 3
    ) {}
    
    private function loadPage(): void {
        $offset = $this->page * $this->pageSize;
        $this->pageData = array_slice($this->data, $offset, $this->pageSize);
    }
    
    public function rewind(): void   { $this->current = 0; $this->page = 0; $this->loadPage(); }
    public function current(): mixed { return $this->pageData[$this->current % $this->pageSize] ?? null; }
    public function key(): int       { return $this->page * $this->pageSize + ($this->current % $this->pageSize); }
    public function next(): void {
        $this->current++;
        if ($this->current % $this->pageSize === 0) {
            $this->page++;
            $this->loadPage();
        }
    }
    public function valid(): bool { return !empty($this->pageData) && isset($this->pageData[$this->current % $this->pageSize]); }
}

$data = range('A', 'L'); // A-L = 12 items
$iter = new PaginatedIterator($data, pageSize: 4);

foreach ($iter as $key => $value) {
    echo "[{$key}] {$value}  ";
}
echo "\n";

// IteratorAggregate: collection with lazy evaluation
class LazyTransformCollection implements IteratorAggregate {
    private array $transforms = [];
    
    public function __construct(private array $data) {}
    
    public function map(callable $fn): static {
        $new = clone $this;
        $new->transforms[] = fn($item) => $fn($item);
        return $new;
    }
    
    public function filter(callable $fn): static {
        $new = clone $this;
        $new->transforms[] = fn($item) => $fn($item) ? $item : null;
        return $new;
    }
    
    public function getIterator(): Traversable {
        return (function() {
            foreach ($this->data as $item) {
                foreach ($this->transforms as $transform) {
                    $item = $transform($item);
                    if ($item === null) continue 2;
                }
                yield $item;
            }
        })();
    }
}

$result = (new LazyTransformCollection(range(1, 20)))
    ->filter(fn($n) => $n % 2 === 0)     // even numbers
    ->map(fn($n) => $n * $n)              // square them
    ->filter(fn($n) => $n > 50);          // > 50

echo "\nLazy collection (even^2 > 50): ";
foreach ($result as $v) echo $v . " ";
echo "\n";
```

📸 **Verified Output:**
```
[0] A  [1] B  [2] C  [3] D  [4] E  [5] F  [6] G  [7] H  [8] I  [9] J  [10] K  [11] L

Lazy collection (even^2 > 50): 64 100 144 196 256 324 400
```

---

## Step 8: Capstone — High-Performance Data Pipeline

```php
<?php
/**
 * High-performance data pipeline using SPL structures
 * Demonstrates: priority processing, efficient memory usage, streaming
 */

class DataPipeline {
    private SplPriorityQueue $inputQueue;
    private SplFixedArray $outputBuffer;
    private SplStack $errorStack;
    private int $bufferSize;
    private int $processed = 0;
    private int $errors = 0;
    
    public function __construct(int $bufferSize = 1000) {
        $this->bufferSize   = $bufferSize;
        $this->inputQueue   = new SplPriorityQueue();
        $this->outputBuffer = new SplFixedArray($bufferSize);
        $this->errorStack   = new SplStack();
    }
    
    public function ingest(array $record, int $priority = 50): void {
        $this->inputQueue->insert($record, $priority);
    }
    
    public function process(): void {
        $idx = 0;
        while (!$this->inputQueue->isEmpty() && $idx < $this->bufferSize) {
            $record = $this->inputQueue->extract();
            
            try {
                $transformed = $this->transform($record);
                $this->outputBuffer[$idx++] = $transformed;
                $this->processed++;
            } catch (Throwable $e) {
                $this->errorStack->push(['record' => $record, 'error' => $e->getMessage()]);
                $this->errors++;
            }
        }
        $this->outputBuffer->setSize($idx); // shrink to actual size
    }
    
    private function transform(array $record): array {
        if (!isset($record['value'])) throw new InvalidArgumentException("Missing value");
        return [
            'id'        => $record['id'],
            'value'     => $record['value'] * 2,
            'processed' => true,
            'score'     => sqrt($record['value']),
        ];
    }
    
    public function getResults(): array {
        return $this->outputBuffer->toArray();
    }
    
    public function stats(): array {
        return [
            'processed' => $this->processed,
            'errors'    => $this->errors,
            'pending'   => $this->inputQueue->count(),
        ];
    }
    
    public function getErrors(): array {
        $errors = [];
        while (!$this->errorStack->isEmpty()) {
            $errors[] = $this->errorStack->pop();
        }
        return $errors;
    }
}

$pipeline = new DataPipeline(bufferSize: 100);

// Ingest records with different priorities
for ($i = 1; $i <= 10; $i++) {
    $priority = match (true) {
        $i <= 3  => 90,  // high priority
        $i <= 7  => 50,  // medium
        default  => 10,  // low
    };
    $pipeline->ingest(['id' => $i, 'value' => $i * 10], $priority);
}

// Add a bad record
$pipeline->ingest(['id' => 99], 50); // missing 'value'

$start = microtime(true);
$pipeline->process();
$elapsed = round((microtime(true) - $start) * 1000, 2);

$stats   = $pipeline->stats();
$results = $pipeline->getResults();

echo "=== Pipeline Stats ===\n";
echo "Processed: {$stats['processed']}\n";
echo "Errors:    {$stats['errors']}\n";
echo "Time:      {$elapsed}ms\n";

echo "\n=== Results (first 5) ===\n";
foreach (array_slice($results, 0, 5) as $r) {
    if (!$r) continue;
    printf("  id=%2d value=%3d score=%.2f\n", $r['id'], $r['value'], $r['score']);
}

echo "\n=== Errors ===\n";
foreach ($pipeline->getErrors() as $err) {
    echo "  record id={$err['record']['id']}: {$err['error']}\n";
}
```

📸 **Verified Output:**
```
=== Pipeline Stats ===
Processed: 10
Errors:    1
Time:      0.12ms

=== Results (first 5) ===
  id= 1 value= 20 score=3.16
  id= 2 value= 40 score=4.47
  id= 3 value= 60 score=5.48
  id= 4 value= 80 score=6.32
  id= 5 value=100 score=7.07

=== Errors ===
  record id=99: Missing value
```

---

## Summary

| Structure | Class | Complexity | Best For |
|-----------|-------|------------|---------|
| Fixed array | `SplFixedArray` | O(1) access | Memory-efficient numeric arrays |
| Min-heap | `SplMinHeap` | O(log n) insert/extract | Priority queues, Dijkstra |
| Max-heap | `SplMaxHeap` | O(log n) insert/extract | Top-N problems |
| Priority queue | `SplPriorityQueue` | O(log n) | Job scheduling |
| Linked list | `SplDoublyLinkedList` | O(1) push/pop | Deque operations |
| Stack | `SplStack` | O(1) push/pop | Undo/redo, recursion simulation |
| Queue | `SplQueue` | O(1) enqueue/dequeue | BFS, work queues |
| Array object | `ArrayObject` | O(1) | Typed collections with OOP |
| Recursive iterator | `RecursiveIteratorIterator` | O(n) | Tree traversal |
| Custom iterator | `Iterator` interface | User-defined | Lazy evaluation, pagination |
