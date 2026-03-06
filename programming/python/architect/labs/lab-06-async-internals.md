# Lab 06: Async Internals

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Understanding asyncio's internals — the event loop, selectors, Future scheduling, and contextvars — lets you write high-performance async code and debug concurrency issues systematically.

## Step 1: The Event Loop Internals

```python
import asyncio
import selectors

# Get the current event loop
loop = asyncio.new_event_loop()
print(f"Event loop type: {type(loop).__name__}")
print(f"Selector: {type(loop._selector).__name__}")

# _ready queue: callbacks to execute in next iteration
print(f"Ready queue: {loop._ready}")

# _scheduled: future callbacks (heapq by time)
print(f"Scheduled queue: {loop._scheduled}")

loop.close()
```

> 💡 `asyncio` on Linux uses `EpollSelector`, macOS uses `KqueueSelector`, and Windows uses `SelectSelector`. All implement the same `selectors.BaseSelector` interface.

## Step 2: `selectors` — I/O Multiplexing

```python
import selectors
import socket

sel = selectors.DefaultSelector()
print(f"Selector type: {type(sel).__name__}")

# Create a pair of connected sockets for demo
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('127.0.0.1', 0))  # OS assigns port
server_sock.listen(1)
server_sock.setblocking(False)
port = server_sock.getsockname()[1]

# Register the server socket for read events
sel.register(server_sock, selectors.EVENT_READ, data="server")
print(f"Server listening on port {port}")
print(f"Registered {len(sel.get_map())} socket(s)")

# Check what's registered
for fd, key in sel.get_map().items():
    print(f"  fd={fd}, events={'READ' if key.events & selectors.EVENT_READ else 'WRITE'}, data={key.data!r}")

server_sock.close()
sel.close()
```

## Step 3: `asyncio.Future` Internals

```python
import asyncio

async def inspect_future():
    loop = asyncio.get_event_loop()
    
    # Create a raw Future
    fut = loop.create_future()
    print(f"Future state: {fut._state}")  # PENDING
    print(f"Done: {fut.done()}")
    
    # Add a callback
    def on_done(f):
        print(f"Callback triggered, result={f.result()}")
    
    fut.add_done_callback(on_done)
    
    # Schedule result setting
    loop.call_soon(fut.set_result, "hello world")
    
    # Await the future
    result = await fut
    print(f"Future result: {result!r}")
    print(f"Future state: {fut._state}")  # FINISHED

asyncio.run(inspect_future())
```

## Step 4: Task Scheduling and Execution Order

```python
import asyncio
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="none")

order = []

async def handle_request(req_id: str):
    token = request_id.set(req_id)
    order.append(f"start: {request_id.get()}")
    await asyncio.sleep(0)        # yield control
    order.append(f"end: {request_id.get()}")  # still correct req_id
    request_id.reset(token)

async def main():
    tasks = [
        asyncio.create_task(handle_request("req-1")),
        asyncio.create_task(handle_request("req-2")),
        asyncio.create_task(handle_request("req-3")),
    ]
    await asyncio.gather(*tasks)
    for item in order:
        print(item)

asyncio.run(main())
```

📸 **Verified Output:**
```
start: req-1
start: req-2
start: req-3
end: req-1
end: req-2
end: req-3
```

> 💡 `ContextVar` is essential for request-scoped state in async servers. Unlike `threading.local`, it works correctly across coroutines: each task gets its own context copy.

## Step 5: `loop.call_soon` vs `loop.call_later` vs `loop.call_at`

```python
import asyncio
import time

async def scheduling_demo():
    loop = asyncio.get_event_loop()
    results = []
    
    start = loop.time()
    
    # call_later: schedule after delay
    loop.call_later(0.02, lambda: results.append(f"call_later(20ms) at {(loop.time()-start)*1000:.0f}ms"))
    loop.call_later(0.01, lambda: results.append(f"call_later(10ms) at {(loop.time()-start)*1000:.0f}ms"))
    
    # call_soon: schedule for next iteration
    loop.call_soon(lambda: results.append(f"call_soon at {(loop.time()-start)*1000:.0f}ms"))
    
    # call_at: schedule at absolute time
    loop.call_at(start + 0.03, lambda: results.append(f"call_at(30ms) at {(loop.time()-start)*1000:.0f}ms"))
    
    await asyncio.sleep(0.05)  # wait for all to fire
    
    print("Execution order:")
    for r in results:
        print(f"  {r}")

asyncio.run(scheduling_demo())
```

## Step 6: Async Generators

```python
import asyncio

async def agen_range(start, stop, step=1, delay=0.0):
    """Async generator with optional delay between yields."""
    i = start
    while i < stop:
        if delay > 0:
            await asyncio.sleep(delay)
        yield i
        i += step

async def async_pipeline():
    # Use async for with async generator
    squares = [x async for x in agen_range(0, 10)]
    print(f"Squares 0-9: {[x**2 for x in squares]}")
    
    # Chained async generators
    async def filter_even(agen):
        async for x in agen:
            if x % 2 == 0:
                yield x
    
    async def multiply(agen, factor):
        async for x in agen:
            yield x * factor
    
    source = agen_range(0, 20)
    evens = filter_even(source)
    doubled = multiply(evens, 2)
    
    result = [x async for x in doubled]
    print(f"Even numbers × 2: {result}")

asyncio.run(async_pipeline())
```

## Step 7: `contextvars.ContextVar` — Request-Scoped State

```python
import asyncio
from contextvars import ContextVar, copy_context
import time

# Request context vars
request_id = ContextVar("request_id")
user_id = ContextVar("user_id", default="anonymous")
start_time = ContextVar("start_time")

async def middleware(req_id: str, uid: str, handler):
    """Middleware that sets context vars for the request."""
    r_token = request_id.set(req_id)
    u_token = user_id.set(uid)
    t_token = start_time.set(time.monotonic())
    
    try:
        return await handler()
    finally:
        elapsed = time.monotonic() - start_time.get()
        print(f"[{request_id.get()}] user={user_id.get()} elapsed={elapsed*1000:.1f}ms")
        request_id.reset(r_token)
        user_id.reset(u_token)
        start_time.reset(t_token)

async def get_user_data():
    """Business logic that reads context vars."""
    await asyncio.sleep(0.001)  # simulate I/O
    return {
        "request": request_id.get(),
        "user": user_id.get(),
    }

async def main():
    # Run 3 concurrent requests, each with their own context
    tasks = [
        asyncio.create_task(middleware("R001", "alice", get_user_data)),
        asyncio.create_task(middleware("R002", "bob",   get_user_data)),
        asyncio.create_task(middleware("R003", "carol", get_user_data)),
    ]
    results = await asyncio.gather(*tasks)
    print("Results:", results)

asyncio.run(main())
```

## Step 8: Capstone — Mini Event Loop

Implement a simplified event loop to understand the mechanism:

```python
import asyncio
import heapq
import selectors
import time
from typing import Any, Callable

class MiniEventLoop:
    """Simplified event loop demonstrating core asyncio mechanics."""
    
    def __init__(self):
        self._ready = []          # callbacks to run immediately
        self._scheduled = []      # (deadline, callback) heap
        self._selector = selectors.DefaultSelector()
        self._running = False
        self._stop = False
    
    def call_soon(self, callback: Callable, *args):
        self._ready.append((callback, args))
    
    def call_later(self, delay: float, callback: Callable, *args):
        deadline = time.monotonic() + delay
        heapq.heappush(self._scheduled, (deadline, id(callback), callback, args))
    
    def _run_once(self):
        now = time.monotonic()
        
        # Move ready scheduled callbacks to _ready queue
        while self._scheduled and self._scheduled[0][0] <= now:
            deadline, _, callback, args = heapq.heappop(self._scheduled)
            self._ready.append((callback, args))
        
        # Calculate timeout for selector
        if self._ready:
            timeout = 0
        elif self._scheduled:
            timeout = max(0, self._scheduled[0][0] - now)
        else:
            timeout = None
        
        # I/O polling
        events = self._selector.select(timeout)
        for key, event in events:
            callback, args = key.data
            self._ready.append((callback, args))
        
        # Run all ready callbacks
        ntodo = len(self._ready)
        for _ in range(ntodo):
            callback, args = self._ready.pop(0)
            callback(*args)
    
    def run(self, n_iterations: int = 10):
        self._running = True
        for _ in range(n_iterations):
            if not (self._ready or self._scheduled):
                break
            self._run_once()
        self._running = False
        self._selector.close()

# Demonstrate
loop = MiniEventLoop()
log = []

loop.call_soon(lambda: log.append("immediate-1"))
loop.call_soon(lambda: log.append("immediate-2"))
loop.call_later(0.01, lambda: log.append("10ms later"))
loop.call_later(0.02, lambda: log.append("20ms later"))
loop.call_soon(lambda: log.append("immediate-3"))

# Schedule another call_soon from within a callback
def chain():
    log.append("chain-1")
    loop.call_soon(lambda: log.append("chain-2"))

loop.call_soon(chain)

import time
time.sleep(0.025)  # pre-wait so scheduled items fire
loop.run(20)

print("Execution order:")
for item in log:
    print(f"  {item}")
```

📸 **Verified Output (contextvars):**
```
start: req-1
start: req-2
start: req-3
end: req-1
end: req-2
end: req-3
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| Event loop | `asyncio.get_event_loop()` | Core I/O scheduler |
| Selectors | `selectors.DefaultSelector` | OS-level I/O polling |
| Future | `loop.create_future()` | Promise-like value holder |
| Task scheduling | `call_soon/call_later/call_at` | Deferred execution |
| Async generators | `async def` + `yield` | Streaming data pipelines |
| `ContextVar` | `set/get/reset` | Request-scoped state |
| `copy_context()` | Context isolation | Run in different context |
| Mini event loop | Custom `_run_once` | Understand asyncio internals |
