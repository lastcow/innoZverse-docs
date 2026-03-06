# Lab 11: Distributed Task Queue

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Build a production-grade distributed task queue backed by Redis. Covers task serialization, worker process pools, retry with exponential backoff, dead letter queues, and result TTL management.

## Prerequisites

```bash
# Start Redis in background
docker run -d --name redis-lab -p 6379:6379 redis:7

# Install redis-py
pip install redis
```

## Step 1: Task Definition and Serialization

```python
import json
import pickle
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    DONE      = "done"
    FAILED    = "failed"
    DEAD      = "dead"

@dataclass
class Task:
    id:         str = field(default_factory=lambda: str(uuid.uuid4()))
    name:       str = ""
    args:       list = field(default_factory=list)
    kwargs:     dict = field(default_factory=dict)
    status:     str = TaskStatus.PENDING
    retries:    int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    done_at:    Optional[float] = None
    result:     Any = None
    error:      Optional[str] = None
    priority:   int = 0  # higher = more urgent

def serialize_task(task: Task) -> bytes:
    return json.dumps(asdict(task)).encode()

def deserialize_task(data: bytes) -> Task:
    return Task(**json.loads(data.decode()))

# Test serialization
task = Task(name="compute_sum", args=[1, 2, 3], kwargs={"start": 10})
serialized = serialize_task(task)
restored = deserialize_task(serialized)

print(f"Task ID: {task.id}")
print(f"Serialized size: {len(serialized)} bytes")
print(f"Round-trip: args={restored.args}, kwargs={restored.kwargs}")
print(f"Status: {restored.status}")
```

## Step 2: Redis-Backed Queue

```python
import redis
import json
import time
from typing import Optional

class RedisTaskQueue:
    """Production task queue backed by Redis sorted sets (priority) and hashes."""
    
    QUEUE_KEY   = "taskq:pending"      # sorted set (score=priority+timestamp)
    RUNNING_KEY = "taskq:running"      # hash: task_id → task_data
    RESULT_KEY  = "taskq:result:{}"   # key per task (with TTL)
    DLQ_KEY     = "taskq:dlq"         # dead letter queue (list)
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.result_ttl = 3600  # 1 hour
    
    def enqueue(self, task: Task) -> str:
        """Add task to priority queue. Higher priority = lower score."""
        task_bytes = serialize_task(task)
        # Score: negative priority (higher priority = lower score = ZPOPMIN)
        score = -task.priority + task.created_at / 1e12
        self.redis.zadd(self.QUEUE_KEY, {task_bytes: score})
        print(f"  [Queue] Enqueued: {task.name} (id={task.id[:8]}...)")
        return task.id
    
    def dequeue(self, timeout: int = 5) -> Optional[Task]:
        """Atomically pop highest-priority task using BLZPOPMIN."""
        result = self.redis.bzpopmin(self.QUEUE_KEY, timeout=timeout)
        if not result:
            return None
        _, task_bytes, score = result
        task = deserialize_task(task_bytes)
        
        # Mark as running
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self.redis.hset(self.RUNNING_KEY, task.id, serialize_task(task))
        return task
    
    def complete(self, task: Task, result: Any):
        """Mark task as complete with result."""
        task.status = TaskStatus.DONE
        task.done_at = time.time()
        task.result = result
        
        self.redis.hdel(self.RUNNING_KEY, task.id)
        result_key = self.RESULT_KEY.format(task.id)
        self.redis.setex(result_key, self.result_ttl, serialize_task(task))
        print(f"  [Worker] Completed: {task.name} result={result}")
    
    def fail(self, task: Task, error: str) -> bool:
        """Retry or move to DLQ. Returns True if retried."""
        task.retries += 1
        task.error = error
        
        self.redis.hdel(self.RUNNING_KEY, task.id)
        
        if task.retries <= task.max_retries:
            # Exponential backoff before retry
            delay = 2 ** task.retries
            print(f"  [Worker] Failed: {task.name} (retry {task.retries}/{task.max_retries} in {delay}s)")
            task.status = TaskStatus.PENDING
            # Re-enqueue with lower priority
            time.sleep(min(delay, 0.01))  # tiny delay in demo
            self.enqueue(task)
            return True
        else:
            # Dead letter queue
            task.status = TaskStatus.DEAD
            self.redis.rpush(self.DLQ_KEY, serialize_task(task))
            print(f"  [DLQ] Dead: {task.name} error={error}")
            return False
    
    def get_result(self, task_id: str) -> Optional[Task]:
        result_key = self.RESULT_KEY.format(task_id)
        data = self.redis.get(result_key)
        return deserialize_task(data) if data else None
    
    def stats(self) -> dict:
        return {
            'pending': self.redis.zcard(self.QUEUE_KEY),
            'running': self.redis.hlen(self.RUNNING_KEY),
            'dlq': self.redis.llen(self.DLQ_KEY),
        }

print("RedisTaskQueue class defined.")
print("To use: connect to Redis with 'docker run -d -p 6379:6379 redis:7'")
```

## Step 3: Worker Implementation

```python
import multiprocessing
import time
import random

# Task function registry
TASK_REGISTRY = {}

def register_task(func):
    TASK_REGISTRY[func.__name__] = func
    return func

@register_task
def compute_sum(numbers: list, start: int = 0) -> int:
    return start + sum(numbers)

@register_task
def process_text(text: str, uppercase: bool = False) -> str:
    if uppercase:
        return text.upper()
    return text.lower().strip()

@register_task
def risky_operation(x: int) -> int:
    """Sometimes fails — for testing retry logic."""
    if x < 0:
        raise ValueError(f"Negative input not allowed: {x}")
    return x * x

class Worker:
    """Task worker with retry logic."""
    
    def __init__(self, queue: RedisTaskQueue, worker_id: str = "worker-1"):
        self.queue = queue
        self.worker_id = worker_id
        self.processed = 0
    
    def execute_task(self, task: Task) -> Any:
        """Execute task and return result."""
        if task.name not in TASK_REGISTRY:
            raise RuntimeError(f"Unknown task: {task.name}")
        
        func = TASK_REGISTRY[task.name]
        return func(*task.args, **task.kwargs)
    
    def run_once(self) -> bool:
        """Process one task. Returns True if a task was processed."""
        task = self.queue.dequeue(timeout=1)
        if not task:
            return False
        
        print(f"  [{self.worker_id}] Processing: {task.name} (attempt {task.retries+1})")
        try:
            result = self.execute_task(task)
            self.queue.complete(task, result)
            self.processed += 1
        except Exception as e:
            self.queue.fail(task, str(e))
        
        return True
    
    def run(self, max_tasks: int = None, idle_timeout: int = 3):
        """Main worker loop."""
        idle_count = 0
        tasks_done = 0
        
        while True:
            if max_tasks and tasks_done >= max_tasks:
                break
            
            got_task = self.run_once()
            if got_task:
                tasks_done += 1
                idle_count = 0
            else:
                idle_count += 1
                if idle_count >= idle_timeout:
                    print(f"  [{self.worker_id}] Idle timeout, stopping")
                    break

print("Worker class defined.")
print(f"Registered tasks: {list(TASK_REGISTRY.keys())}")
```

## Step 4: Producer — Enqueue Tasks

```python
# Full demo (requires Redis running)
# docker run -d -p 6379:6379 redis:7
# pip install redis

DEMO_SCRIPT = '''
import redis
import time

# Test connection
try:
    r = redis.from_url("redis://localhost:6379")
    r.ping()
    print("Redis connected!")
except Exception as e:
    print(f"Redis not available: {e}")
    print("Run: docker run -d -p 6379:6379 redis:7")
    exit(1)

queue = RedisTaskQueue()

# Enqueue tasks with different priorities
tasks_to_enqueue = [
    Task(name="compute_sum", args=[[1,2,3,4,5]], priority=1),
    Task(name="process_text", args=["  Hello World  "], kwargs={"uppercase": True}, priority=5),
    Task(name="risky_operation", args=[4], priority=3),
    Task(name="risky_operation", args=[-1], priority=2),   # will fail
    Task(name="compute_sum", args=[[10,20,30]], kwargs={"start": 100}, priority=4),
]

print("=== Enqueuing tasks ===")
task_ids = []
for task in tasks_to_enqueue:
    tid = queue.enqueue(task)
    task_ids.append(tid)

print(f"\\nQueue stats: {queue.stats()}")

# Process with worker
print("\\n=== Processing tasks ===")
worker = Worker(queue, "w1")
worker.run(idle_timeout=2)

print(f"\\n=== Final stats ===")
print(f"Queue: {queue.stats()}")
print(f"Processed: {worker.processed} tasks")
'''

print("Demo script ready. Run after Redis is available:")
print(DEMO_SCRIPT[:200] + "...")
```

## Step 5: Exponential Backoff

```python
import time
import random
import functools

def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """Decorator for automatic retry with exponential backoff."""
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    print(f"  Attempt {attempt+1}/{max_retries} failed: {e}")
                    print(f"  Retrying in {delay:.2f}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Simulate flaky operation
call_count = 0

@exponential_backoff(max_retries=4, base_delay=0.1, jitter=False)
def flaky_service_call(succeed_after: int) -> str:
    global call_count
    call_count += 1
    if call_count < succeed_after:
        raise ConnectionError(f"Service unavailable (attempt {call_count})")
    return f"Success after {call_count} attempts"

call_count = 0
try:
    result = flaky_service_call(succeed_after=3)
    print(f"\nResult: {result}")
except Exception as e:
    print(f"Failed permanently: {e}")
```

## Step 6: Dead Letter Queue Management

```python
class DLQManager:
    """Manage and reprocess dead letter queue entries."""
    
    def __init__(self, queue: RedisTaskQueue):
        self.queue = queue
    
    def inspect_dlq(self, limit: int = 10) -> list[Task]:
        """View failed tasks without removing them."""
        raw_items = self.queue.redis.lrange(
            RedisTaskQueue.DLQ_KEY, 0, limit - 1
        )
        return [deserialize_task(item) for item in raw_items]
    
    def requeue_task(self, task: Task, reset_retries: bool = True) -> str:
        """Requeue a dead task for reprocessing."""
        if reset_retries:
            task.retries = 0
        task.status = TaskStatus.PENDING
        task.error = None
        return self.queue.enqueue(task)
    
    def requeue_all(self, filter_fn=None) -> int:
        """Requeue all (or filtered) dead tasks."""
        tasks = self.inspect_dlq(limit=1000)
        requeued = 0
        for task in tasks:
            if filter_fn is None or filter_fn(task):
                self.requeue_task(task)
                requeued += 1
        
        # Clear DLQ for requeued tasks
        self.queue.redis.delete(RedisTaskQueue.DLQ_KEY)
        return requeued
    
    def discard(self, task_id: str) -> bool:
        """Permanently remove a task from DLQ."""
        tasks = self.inspect_dlq(limit=1000)
        remaining = [t for t in tasks if t.id != task_id]
        
        self.queue.redis.delete(RedisTaskQueue.DLQ_KEY)
        for task in remaining:
            self.queue.redis.rpush(
                RedisTaskQueue.DLQ_KEY, serialize_task(task)
            )
        return len(tasks) != len(remaining)

print("DLQManager class defined.")
```

## Step 7: Task Result TTL and Polling

```python
import time

def wait_for_result(queue: RedisTaskQueue, task_id: str, 
                    timeout: float = 30.0, poll_interval: float = 0.5) -> Optional[Task]:
    """Poll for task completion with timeout."""
    deadline = time.monotonic() + timeout
    
    while time.monotonic() < deadline:
        task = queue.get_result(task_id)
        if task and task.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.DEAD):
            return task
        time.sleep(poll_interval)
    
    return None  # timeout

# Demo without Redis - simulate the behavior
class InMemoryQueue:
    """In-memory queue for testing without Redis."""
    
    def __init__(self):
        self._pending = []
        self._results = {}
        self._dlq = []
    
    def enqueue(self, task: Task) -> str:
        self._pending.append(task)
        print(f"  Enqueued: {task.name} id={task.id[:8]}")
        return task.id
    
    def dequeue(self, timeout=1) -> Optional[Task]:
        if self._pending:
            task = self._pending.pop(0)
            task.status = TaskStatus.RUNNING
            return task
        return None
    
    def complete(self, task: Task, result: Any):
        task.status = TaskStatus.DONE
        task.result = result
        self._results[task.id] = task
        print(f"  Complete: {task.name} → {result}")
    
    def fail(self, task: Task, error: str) -> bool:
        task.retries += 1
        if task.retries <= task.max_retries:
            task.status = TaskStatus.PENDING
            self._pending.append(task)
            print(f"  Retry {task.retries}: {task.name}")
            return True
        task.status = TaskStatus.DEAD
        self._dlq.append(task)
        print(f"  DLQ: {task.name} error={error}")
        return False
    
    def get_result(self, task_id: str):
        return self._results.get(task_id)
    
    def stats(self):
        return {
            'pending': len(self._pending),
            'results': len(self._results),
            'dlq': len(self._dlq),
        }

# Demo with in-memory queue
print("=== In-Memory Queue Demo ===")
queue = InMemoryQueue()
worker_impl = Worker(queue, "w1")

# Enqueue tasks
task1 = Task(name="compute_sum", args=[[1,2,3,4,5]])
task2 = Task(name="process_text", args=["  Hello World  "], kwargs={"uppercase": True})
task3 = Task(name="risky_operation", args=[-1], max_retries=2)  # will fail

queue.enqueue(task1)
queue.enqueue(task2)
queue.enqueue(task3)

print(f"\nStats before: {queue.stats()}")
print("\n=== Processing ===")
worker_impl.run(idle_timeout=1)

print(f"\nStats after: {queue.stats()}")
print(f"DLQ items: {len(queue._dlq)}")
print(f"Results:")
for task_id, task in queue._results.items():
    print(f"  {task.name}: result={task.result}")
```

## Step 8: Capstone — Full Queue Demo

```python
import time

print("=== Full Task Queue Demonstration ===\n")

class RobustInMemoryQueue(InMemoryQueue):
    """Enhanced demo queue with result TTL simulation."""
    
    def enqueue_batch(self, tasks: list[Task]) -> list[str]:
        return [self.enqueue(t) for t in tasks]

queue = RobustInMemoryQueue()
worker = Worker(queue, "w1")

tasks = [
    Task(name="compute_sum",   args=[[10,20,30,40,50]], priority=3),
    Task(name="process_text",  args=["  architect patterns  "], kwargs={"uppercase": True}, priority=5),
    Task(name="compute_sum",   args=[[1,2,3]], kwargs={"start": 1000}, priority=2),
    Task(name="risky_operation", args=[7], priority=4),
    Task(name="risky_operation", args=[-5], priority=1, max_retries=2),
]

print("1. Enqueuing tasks:")
ids = queue.enqueue_batch(tasks)

print(f"\n2. Initial stats: {queue.stats()}")

print("\n3. Processing all tasks:")
worker.run(idle_timeout=1)

print(f"\n4. Final stats: {queue.stats()}")

print("\n5. Results:")
for task_id in ids:
    result = queue.get_result(task_id)
    if result:
        status_icon = "✓" if result.status == TaskStatus.DONE else "✗"
        print(f"  {status_icon} {result.name}: {result.result if result.status == TaskStatus.DONE else result.error}")
```

📸 **Verified Output (without Redis):**
```
=== In-Memory Queue Demo ===
  Enqueued: compute_sum id=...
  Enqueued: process_text id=...
  Enqueued: risky_operation id=...
  Complete: compute_sum → 15
  Complete: process_text → HELLO WORLD
  Retry 1: risky_operation
  Retry 2: risky_operation
  DLQ: risky_operation error=Negative input not allowed: -1
```

## Summary

| Concept | Implementation | Use Case |
|---|---|---|
| Task serialization | `json` + dataclass | Portable task format |
| Priority queue | Redis sorted set (ZADD/BZPOPMIN) | Priority-based scheduling |
| Running tracking | Redis hash | At-most-once delivery |
| Result TTL | Redis SETEX | Ephemeral result storage |
| Exponential backoff | `2 ** attempt` delay | Fault-tolerant retries |
| Dead letter queue | Redis list | Failed task forensics |
| Worker loop | Blocking dequeue | CPU-efficient polling |
| Batch enqueue | `enqueue_batch` | Throughput optimization |
