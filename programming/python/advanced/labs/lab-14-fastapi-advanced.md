# Lab 14: Advanced FastAPI — Lifespan, Middleware & WebSockets

## Objective
Build production-grade FastAPI services: lifespan context managers for startup/shutdown, custom middleware for auth/logging/rate-limiting, WebSocket connections, background task queues, Server-Sent Events (SSE), and OpenAPI customisation.

## Background
FastAPI's `lifespan` replaces deprecated `on_startup`/`on_shutdown` hooks with a clean async context manager. Custom middleware lets you inject cross-cutting concerns (auth, tracing, rate-limiting) without touching individual route handlers. These patterns are how real production APIs are built.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 09 (FastAPI basics)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Lifespan — Startup & Shutdown

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager
import asyncio

# Shared application state
class AppState:
    db_pool:   list = []
    cache:     dict = {}
    ready:     bool = False
    start_count: int = 0

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP — runs before first request
    print('  [startup] Connecting to database...')
    await asyncio.sleep(0.01)  # simulate async DB connect
    state.db_pool = [f'conn-{i}' for i in range(5)]
    state.cache   = {}
    state.ready   = True
    state.start_count += 1
    print(f'  [startup] Ready: {len(state.db_pool)} connections, cache empty')

    yield  # <-- app runs here

    # SHUTDOWN — runs after last request
    print(f'  [shutdown] Closing {len(state.db_pool)} connections...')
    state.db_pool.clear()
    state.ready = False
    print('  [shutdown] Clean exit')

app = FastAPI(title='innoZverse API', version='2.0.0', lifespan=lifespan)

@app.get('/health')
def health():
    return {
        'status': 'healthy' if state.ready else 'starting',
        'db_connections': len(state.db_pool),
        'cache_keys': len(state.cache),
    }

@app.get('/products/{pid}')
async def get_product(pid: int):
    key = f'product:{pid}'
    if key in state.cache:
        return {'source': 'cache', **state.cache[key]}
    # Simulate DB lookup using pool
    conn = state.db_pool[pid % len(state.db_pool)]
    product = {'id': pid, 'name': f'Product-{pid}', 'price': pid * 9.99}
    state.cache[key] = product
    return {'source': 'db', 'conn': conn, **product}

# TestClient triggers lifespan automatically
with TestClient(app) as client:
    print()
    r = client.get('/health')
    print(f'GET /health: {r.json()}')

    r1 = client.get('/products/1')
    print(f'GET /products/1 (first):  source={r1.json()[\"source\"]}')
    r2 = client.get('/products/1')
    print(f'GET /products/1 (second): source={r2.json()[\"source\"]}')
    r3 = client.get('/products/2')
    print(f'GET /products/2:          source={r3.json()[\"source\"]}')
    print(f'Cache size: {len(state.cache)}')
"
```

> 💡 **`lifespan` replaces `on_startup`/`on_shutdown`** because it's a proper async context manager — guarantees cleanup even if startup raises an exception, and lets you use `async with` resources across the full app lifetime. Database connection pools, ML model loading, and background task workers all belong in `lifespan`.

**📸 Verified Output:**
```
  [startup] Connecting to database...
  [startup] Ready: 5 connections, cache empty

GET /health: {'status': 'healthy', 'db_connections': 5, 'cache_keys': 0}
GET /products/1 (first):  source=db
GET /products/1 (second): source=cache
GET /products/2:          source=db
Cache size: 2
  [shutdown] Closing 5 connections...
  [shutdown] Clean exit
```

---

### Step 2: Custom Middleware — Auth, Logging & Rate Limiting

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
import time, collections

app = FastAPI()

# Middleware 1: Request timing
@app.middleware('http')
async def timing_middleware(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    response.headers['X-Process-Time'] = f'{elapsed:.2f}ms'
    response.headers['X-Request-ID']   = str(id(request))
    return response

# Middleware 2: API key authentication
VALID_KEYS = {
    'inz_admin_key123': {'name': 'Dr. Chen', 'role': 'admin', 'rate_limit': 1000},
    'inz_user_key456':  {'name': 'Alice',    'role': 'user',  'rate_limit': 100},
}

@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    # Skip auth for public endpoints
    if request.url.path in ('/health', '/docs', '/openapi.json'):
        return await call_next(request)

    api_key = request.headers.get('X-API-Key') or request.query_params.get('api_key')
    if not api_key or api_key not in VALID_KEYS:
        return JSONResponse({'error': 'Invalid or missing API key'}, status_code=401)

    user = VALID_KEYS[api_key]
    request.state.user = user  # attach to request state
    response = await call_next(request)
    response.headers['X-Authenticated-As'] = user['name']
    return response

# Middleware 3: Rate limiting (in-memory, per API key)
_rate_windows: dict = collections.defaultdict(list)

@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next):
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key not in VALID_KEYS:
        return await call_next(request)

    limit  = VALID_KEYS[api_key]['rate_limit']
    window = 60  # 1-minute window
    now    = time.time()
    calls  = _rate_windows[api_key]
    # Remove calls outside the window
    _rate_windows[api_key] = [t for t in calls if now - t < window]

    if len(_rate_windows[api_key]) >= limit:
        return JSONResponse({'error': f'Rate limit exceeded: {limit}/min'}, status_code=429)

    _rate_windows[api_key].append(now)
    response = await call_next(request)
    response.headers['X-RateLimit-Remaining'] = str(limit - len(_rate_windows[api_key]))
    return response

@app.get('/health')
def health(): return {'status': 'ok'}

@app.get('/products')
def list_products(request: Request):
    user = request.state.user
    return {'user': user['name'], 'role': user['role'], 'products': ['Surface Pro', 'Surface Pen']}

@app.get('/admin/stats')
def admin_stats(request: Request):
    if request.state.user['role'] != 'admin':
        raise HTTPException(403, 'Admin only')
    return {'total_products': 42, 'total_orders': 1337}

client = TestClient(app)

# Public endpoint (no auth)
r = client.get('/health')
print(f'GET /health:           {r.status_code}  time={r.headers.get(\"X-Process-Time\",\"?\")}')

# Authenticated as admin
r = client.get('/products', headers={'X-API-Key': 'inz_admin_key123'})
print(f'GET /products (admin): {r.status_code}  as={r.headers.get(\"X-Authenticated-As\")}  remain={r.headers.get(\"X-RateLimit-Remaining\")}')

# No API key
r = client.get('/products')
print(f'GET /products (no key): {r.status_code}  {r.json()[\"error\"]}')

# User tries admin endpoint
r = client.get('/admin/stats', headers={'X-API-Key': 'inz_user_key456'})
print(f'GET /admin (user): {r.status_code}  {r.json()[\"detail\"]}')

# Admin gets stats
r = client.get('/admin/stats', headers={'X-API-Key': 'inz_admin_key123'})
print(f'GET /admin (admin): {r.status_code}  {r.json()}')
"
```

**📸 Verified Output:**
```
GET /health:           200  time=0.23ms
GET /products (admin): 200  as=Dr. Chen  remain=999
GET /products (no key): 401  Invalid or missing API key
GET /admin (user): 403  Admin only
GET /admin (admin): 200  {'total_products': 42, 'total_orders': 1337}
```

---

### Steps 3–8: Dependency chains, Background queues, SSE, Exception handlers, OpenAPI, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator
import asyncio, json, time, collections

# Step 3: Dependency chains
app = FastAPI()

# Layer 1: extract token
def get_token(request: Request) -> str:
    token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    if not token: raise HTTPException(401, 'Bearer token required')
    return token

# Layer 2: validate token → user
TOKENS = {'admin-tok': {'id':1,'name':'Dr. Chen','role':'admin','scopes':['read','write','admin']},
          'user-tok':  {'id':2,'name':'Alice',   'role':'user', 'scopes':['read']}}
def get_user(token: str = Depends(get_token)) -> dict:
    user = TOKENS.get(token)
    if not user: raise HTTPException(401, 'Invalid token')
    return user

# Layer 3: require specific role
def require_admin(user: dict = Depends(get_user)) -> dict:
    if 'admin' not in user.get('scopes', []): raise HTTPException(403, 'Admin scope required')
    return user

def require_scope(scope: str):
    def check(user: dict = Depends(get_user)):
        if scope not in user.get('scopes', []):
            raise HTTPException(403, f'Scope {scope!r} required')
        return user
    return check

@app.get('/me')
def get_me(user: dict = Depends(get_user)):
    return user

@app.get('/admin/users')
def list_users(user: dict = Depends(require_admin)):
    return {'users': list(TOKENS.values()), 'requested_by': user['name']}

@app.get('/products')
def list_products(user: dict = Depends(require_scope('read'))):
    return {'products': ['Surface Pro','Surface Pen'], 'visible_to': user['name']}

# Step 4: Background task queue
class JobQueue:
    def __init__(self): self.jobs = []; self.results = {}

queue = JobQueue()

def process_order(order_id: int, total: float, email: str):
    time.sleep(0.01)  # simulate work
    result = {'order_id': order_id, 'status': 'processed', 'confirmation': f'CONF-{order_id:04d}'}
    queue.results[order_id] = result
    print(f'  [BG] Order #{order_id} processed for {email}: \${total:.2f}')

class OrderCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity:   int = Field(..., gt=0)
    email:      str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')

order_counter = 0
@app.post('/orders', status_code=202)
def create_order(order: OrderCreate, tasks: BackgroundTasks,
                 user: dict = Depends(require_scope('write'))):
    global order_counter
    order_counter += 1
    oid = order_counter
    total = order.quantity * 864.0  # simplified
    tasks.add_task(process_order, oid, total, order.email)
    return {'order_id': oid, 'status': 'accepted', 'message': 'Processing in background'}

@app.get('/orders/{oid}/status')
def order_status(oid: int, user: dict = Depends(get_user)):
    result = queue.results.get(oid)
    if not result: return {'order_id': oid, 'status': 'pending'}
    return result

# Step 5: Custom exception handler
class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code; self.message = message; self.status = status

@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(status_code=exc.status,
                        content={'error': {'code': exc.code, 'message': exc.message}})

@app.get('/products/{pid}')
def get_product(pid: int):
    products = {1:{'id':1,'name':'Surface Pro','price':864.0},
                2:{'id':2,'name':'Surface Pen','price':49.99}}
    if pid not in products:
        raise AppError('PRODUCT_NOT_FOUND', f'Product {pid} not found', 404)
    return products[pid]

# Step 6: Streaming response (SSE-like)
@app.get('/stream/prices')
def stream_prices(count: int = 5):
    def generate():
        import math, random
        for i in range(count):
            price = round(864.0 + math.sin(i) * 50 + random.uniform(-10,10), 2)
            event = json.dumps({'seq': i+1, 'price': price, 'ts': time.time()})
            yield f'data: {event}\n\n'
    return StreamingResponse(generate(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache'})

# Run all tests
client = TestClient(app)
print('=== Dependency Chain Tests ===')
r = client.get('/me', headers={'Authorization': 'Bearer admin-tok'})
print(f'GET /me (admin): {r.status_code} → {r.json()[\"name\"]}')

r = client.get('/me')
print(f'GET /me (no token): {r.status_code}')

r = client.get('/admin/users', headers={'Authorization': 'Bearer user-tok'})
print(f'GET /admin (user): {r.status_code} → {r.json()[\"detail\"]}')

r = client.get('/admin/users', headers={'Authorization': 'Bearer admin-tok'})
print(f'GET /admin (admin): {r.status_code} → {len(r.json()[\"users\"])} users')

print()
print('=== Background Tasks ===')
r = client.post('/orders', json={'product_id':1,'quantity':2,'email':'ebiz@chen.me'},
                headers={'Authorization': 'Bearer admin-tok'})
oid = r.json()['order_id']
print(f'POST /orders: {r.status_code} → id={oid} status={r.json()[\"status\"]}')
time.sleep(0.05)  # allow BG task
r = client.get(f'/orders/{oid}/status', headers={'Authorization': 'Bearer admin-tok'})
print(f'GET /orders/{oid}/status: {r.json()}')

print()
print('=== Custom Exception ===')
r = client.get('/products/99')
print(f'GET /products/99: {r.status_code} → {r.json()[\"error\"]}')
r = client.get('/products/1')
print(f'GET /products/1:  {r.status_code} → {r.json()[\"name\"]}')

print()
print('=== Streaming (SSE) ===')
r = client.get('/stream/prices?count=4')
print(f'GET /stream/prices: {r.status_code}')
for line in r.text.strip().split('\n\n')[:3]:
    if line.startswith('data: '):
        event = json.loads(line[6:])
        print(f'  seq={event[\"seq\"]}  price=\${event[\"price\"]}')

# Step 7: OpenAPI customisation
print()
print('=== OpenAPI Schema ===')
schema = client.get('/openapi.json').json()
print(f'Title:   {schema[\"info\"][\"title\"]}')
print(f'Version: {schema[\"info\"][\"version\"]}')
print(f'Paths:   {list(schema[\"paths\"].keys())}')
"
```

**📸 Verified Output:**
```
=== Dependency Chain Tests ===
GET /me (admin): 200 → Dr. Chen
GET /me (no token): 401
GET /admin (user): 403 → Admin scope required
GET /admin (admin): 200 → 2 users

=== Background Tasks ===
POST /orders: 202 → id=1 status=accepted
  [BG] Order #1 processed for ebiz@chen.me: $1728.00
GET /orders/1/status: {'order_id': 1, 'status': 'processed', 'confirmation': 'CONF-0001'}

=== Custom Exception ===
GET /products/99: 404 → {'code': 'PRODUCT_NOT_FOUND', 'message': 'Product 99 not found'}
GET /products/1:  200 → Surface Pro

=== Streaming (SSE) ===
GET /stream/prices: 200
  seq=1  price=$887.15
  seq=2  price=$912.23
  seq=3  price=$871.47
```

---

## Summary

| Feature | API | Purpose |
|---------|-----|---------|
| Lifespan | `@asynccontextmanager async def lifespan(app)` | Startup/shutdown hooks |
| Middleware | `@app.middleware('http')` | Cross-cutting concerns |
| Dependency chain | `Depends(fn)` nested | Layered auth/validation |
| Background tasks | `BackgroundTasks.add_task(fn, ...)` | Post-response work |
| SSE streaming | `StreamingResponse(generator, 'text/event-stream')` | Real-time push |
| Custom exception | `@app.exception_handler(MyExc)` | Structured error responses |
| Request state | `request.state.user = ...` | Per-request context |

## Further Reading
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
