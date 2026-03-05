# Lab 05: SPL Data Structures & Performance

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

The Standard PHP Library (SPL) provides specialized data structures with O(1) operations for specific access patterns. Knowing when to use them over plain arrays can significantly improve performance and code clarity.

---

## Step 1: SplStack — LIFO Stack

```php
<?php
$stack = new SplStack();

$stack->push('a');
$stack->push('b');
$stack->push('c');

echo "Top:  " . $stack->top() . "\n";    // c (peek)
echo "Pop:  " . $stack->pop() . "\n";    // c
echo "Pop:  " . $stack->pop() . "\n";    // b
echo "Size: " . $stack->count() . "\n";  // 1

// Iterate (top to bottom)
$stack->push('x');
$stack->push('y');
foreach ($stack as $item) {
    echo $item . " ";
}
echo "\n";
```

📸 **Verified Output:**
```
Top:  c
Pop:  c
Pop:  b
Size: 1
y x a 
```

> 💡 `SplStack` extends `SplDoublyLinkedList` with LIFO iteration mode. Use it for undo history, call stacks, and expression parsers.

---

## Step 2: SplQueue — FIFO Queue

```php
<?php
$queue = new SplQueue();

$queue->enqueue('first');
$queue->enqueue('second');
$queue->enqueue('third');

echo "Front: " . $queue->bottom() . "\n";   // first
echo "Dequeue: " . $queue->dequeue() . "\n"; // first
echo "Dequeue: " . $queue->dequeue() . "\n"; // second
echo "Remaining: " . $queue->count() . "\n"; // 1

// Use as task queue
$taskQueue = new SplQueue();
$taskQueue->setIteratorMode(SplQueue::IT_MODE_DELETE); // auto-dequeue on iterate

foreach (['task1', 'task2', 'task3'] as $t) {
    $taskQueue->enqueue($t);
}

foreach ($taskQueue as $task) {
    echo "Processing: $task\n";
}
echo "Empty: " . ($taskQueue->isEmpty() ? 'yes' : 'no') . "\n";
```

📸 **Verified Output:**
```
Front: first
Dequeue: first
Dequeue: second
Remaining: 1
Processing: task1
Processing: task2
Processing: task3
Empty: yes
```

---

## Step 3: SplPriorityQueue

```php
<?php
$pq = new SplPriorityQueue();
$pq->setExtractFlags(SplPriorityQueue::EXTR_BOTH);

$pq->insert('Low priority task',    1);
$pq->insert('High priority task',  10);
$pq->insert('Medium priority task', 5);
$pq->insert('Critical task',       100);
$pq->insert('Normal task',          3);

echo "Processing by priority:\n";
while (!$pq->isEmpty()) {
    $item = $pq->extract();
    printf("  [P=%3d] %s\n", $item['priority'], $item['data']);
}
```

📸 **Verified Output:**
```
Processing by priority:
  [P=100] Critical task
  [P= 10] High priority task
  [P=  5] Medium priority task
  [P=  3] Normal task
  [P=  1] Low priority task
```

> 💡 `SplPriorityQueue` is a max-heap. Higher numbers have higher priority. Use `EXTR_BOTH` to retrieve both data and priority.

---

## Step 4: SplMinHeap & SplMaxHeap

```php
<?php
// Min-heap: always extracts smallest
$minHeap = new SplMinHeap();
foreach ([5, 2, 8, 1, 9, 3] as $n) {
    $minHeap->insert($n);
}

echo "MinHeap order: ";
while (!$minHeap->isEmpty()) {
    echo $minHeap->extract() . " ";
}
echo "\n";

// Max-heap: always extracts largest
$maxHeap = new SplMaxHeap();
foreach ([5, 2, 8, 1, 9, 3] as $n) {
    $maxHeap->insert($n);
}

echo "MaxHeap order: ";
while (!$maxHeap->isEmpty()) {
    echo $maxHeap->extract() . " ";
}
echo "\n";

// Custom heap: sort by string length
class LengthMinHeap extends SplMinHeap {
    protected function compare(mixed $a, mixed $b): int {
        return strlen($b) <=> strlen($a);  // reversed for min-heap
    }
}

$lh = new LengthMinHeap();
foreach (['elephant', 'cat', 'hippopotamus', 'ox', 'dog'] as $w) {
    $lh->insert($w);
}

echo "By length: ";
while (!$lh->isEmpty()) {
    echo $lh->extract() . " ";
}
echo "\n";
```

📸 **Verified Output:**
```
MinHeap order: 1 2 3 5 8 9 
MaxHeap order: 9 8 5 3 2 1 
By length: ox cat dog elephant hippopotamus 
```

---

## Step 5: SplFixedArray — Memory-Efficient Arrays

```php
<?php
$n = 100_000;

// SplFixedArray benchmark
$t1 = microtime(true);
$fixed = new SplFixedArray($n);
for ($i = 0; $i < $n; $i++) {
    $fixed[$i] = $i;
}
$t2 = microtime(true);
$fixedMem = memory_get_usage();

// PHP array benchmark
$t3 = microtime(true);
$arr = [];
for ($i = 0; $i < $n; $i++) {
    $arr[] = $i;
}
$t4 = microtime(true);

echo "SplFixedArray: " . round(($t2 - $t1) * 1000, 2) . "ms\n";
echo "PHP array:     " . round(($t4 - $t3) * 1000, 2) . "ms\n";
echo "Fixed size:    " . $fixed->getSize() . "\n";
echo "Fixed[42]:     " . $fixed[42] . "\n";

// Convert between array and SplFixedArray
$from = SplFixedArray::fromArray([10, 20, 30, 40, 50]);
echo "From array: " . implode(', ', $from->toArray()) . "\n";
```

📸 **Verified Output:**
```
SplFixedArray: 9.19ms
PHP array:     10.44ms
Fixed size:    100000
Fixed[42]:     42
From array: 10, 20, 30, 40, 50
```

> 💡 `SplFixedArray` uses ~30% less memory than a PHP array for large integer-indexed data, since it doesn't need hash table overhead.

---

## Step 6: SplObjectStorage — Object Registry

```php
<?php
class Connection {
    private static int $counter = 0;
    public readonly int $id;
    public function __construct(public string $host) {
        $this->id = ++self::$counter;
    }
    public function __toString(): string { return "Conn#{$this->id}@{$this->host}"; }
}

// SplObjectStorage: object → arbitrary data
$storage = new SplObjectStorage();

$c1 = new Connection('db1.local');
$c2 = new Connection('db2.local');
$c3 = new Connection('db3.local');

$storage->attach($c1, ['pool' => 'read',  'active' => true]);
$storage->attach($c2, ['pool' => 'write', 'active' => true]);
$storage->attach($c3, ['pool' => 'read',  'active' => false]);

echo "Total connections: " . $storage->count() . "\n";
echo "Has c1: " . ($storage->contains($c1) ? 'yes' : 'no') . "\n";

// Iterate with metadata
foreach ($storage as $conn) {
    $meta = $storage->getInfo();
    $active = $meta['active'] ? 'active' : 'inactive';
    echo "  $conn [{$meta['pool']}] $active\n";
}

// Remove
$storage->detach($c3);
echo "After detach: " . $storage->count() . "\n";
```

📸 **Verified Output:**
```
Total connections: 3
Has c1: yes
  Conn#1@db1.local [read] active
  Conn#2@db2.local [write] active
  Conn#3@db3.local [read] inactive
After detach: 2
```

---

## Step 7: SplDoublyLinkedList — Bidirectional Traversal

```php
<?php
$dll = new SplDoublyLinkedList();

// Push/unshift
$dll->push('C');
$dll->push('D');
$dll->unshift('A');
$dll->unshift('B');  // Will be at front? No — unshift prepends

// Actually: push appends, unshift prepends
// Order: B, A, C, D... wait let's check
$dll2 = new SplDoublyLinkedList();
$dll2->push('first');
$dll2->push('second');
$dll2->push('third');
$dll2->unshift('prepended');

echo "Forward:  ";
$dll2->setIteratorMode(SplDoublyLinkedList::IT_MODE_FIFO);
foreach ($dll2 as $v) echo "$v ";
echo "\n";

echo "Backward: ";
$dll2->setIteratorMode(SplDoublyLinkedList::IT_MODE_LIFO);
foreach ($dll2 as $v) echo "$v ";
echo "\n";

echo "Bottom: " . $dll2->bottom() . "\n";
echo "Top:    " . $dll2->top() . "\n";
```

📸 **Verified Output:**
```
Forward:  prepended first second third 
Backward: third second first prepended 
Bottom: prepended
Top:    third
```

---

## Step 8: Capstone — Performance Benchmark Suite

```php
<?php
function benchmark(string $name, callable $fn, int $iterations = 5): array {
    $times = [];
    for ($i = 0; $i < $iterations; $i++) {
        $start = microtime(true);
        $fn();
        $times[] = (microtime(true) - $start) * 1000;
    }
    $avg = array_sum($times) / count($times);
    return ['name' => $name, 'avg_ms' => round($avg, 3), 'min_ms' => round(min($times), 3)];
}

$n = 10_000;
$data = range(1, $n);

$results = [];

// Stack operations
$results[] = benchmark("SplStack push/pop x$n", function() use ($n) {
    $s = new SplStack();
    for ($i = 0; $i < $n; $i++) $s->push($i);
    while (!$s->isEmpty()) $s->pop();
});

$results[] = benchmark("Array stack push/pop x$n", function() use ($n) {
    $a = [];
    for ($i = 0; $i < $n; $i++) $a[] = $i;
    while (!empty($a)) array_pop($a);
});

// Queue operations
$results[] = benchmark("SplQueue enqueue/dequeue x$n", function() use ($n) {
    $q = new SplQueue();
    for ($i = 0; $i < $n; $i++) $q->enqueue($i);
    while (!$q->isEmpty()) $q->dequeue();
});

$results[] = benchmark("Array queue shift x$n", function() use ($n) {
    $a = [];
    for ($i = 0; $i < $n; $i++) $a[] = $i;
    while (!empty($a)) array_shift($a);  // O(n) each!
});

// Priority queue
$results[] = benchmark("SplPriorityQueue insert/extract x$n", function() use ($n) {
    $pq = new SplPriorityQueue();
    for ($i = 0; $i < $n; $i++) $pq->insert("task$i", rand(1, 100));
    while (!$pq->isEmpty()) $pq->extract();
});

echo str_pad("Operation", 40) . "Avg(ms)   Min(ms)\n";
echo str_repeat('-', 60) . "\n";
foreach ($results as $r) {
    printf("%-40s %8.3f  %8.3f\n", $r['name'], $r['avg_ms'], $r['min_ms']);
}

echo "\n💡 Key insight: array_shift() is O(n) — SplQueue::dequeue() is O(1)!\n";
```

📸 **Verified Output:**
```
Operation                               Avg(ms)   Min(ms)
------------------------------------------------------------
SplStack push/pop x10000                  0.821     0.753
Array stack push/pop x10000               0.514     0.476
SplQueue enqueue/dequeue x10000           0.916     0.862
Array queue shift x10000                 28.743    27.891
SplPriorityQueue insert/extract x10000    3.127     2.988

💡 Key insight: array_shift() is O(n) — SplQueue::dequeue() is O(1)!
```

---

## Summary

| Structure | Best For | Key Operations |
|---|---|---|
| `SplStack` | LIFO, undo, recursion | `push()`, `pop()`, `top()` |
| `SplQueue` | FIFO, task queue, BFS | `enqueue()`, `dequeue()`, `bottom()` |
| `SplPriorityQueue` | Priority scheduling | `insert($data, $priority)`, `extract()` |
| `SplMinHeap` | Find minimum fast | `insert()`, `extract()` O(log n) |
| `SplMaxHeap` | Find maximum fast | `insert()`, `extract()` O(log n) |
| `SplFixedArray` | Large integer arrays | 30% less memory than array |
| `SplObjectStorage` | Object → data map | `attach()`, `detach()`, `contains()` |
| `SplDoublyLinkedList` | Bidirectional traversal | `push()`, `unshift()`, `shift()`, `pop()` |
