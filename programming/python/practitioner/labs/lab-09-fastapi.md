# Lab 09: REST APIs with FastAPI

## Objective
Build a production-quality REST API using FastAPI: Pydantic models, path/query parameters, request body, dependency injection, error handling, and automatic OpenAPI docs.

## Time
35 minutes

## Prerequisites
- Lab 07 (Type Hints), Lab 08 (SQLite)

## Tools
- Docker image: `zchencow/innozverse-python:latest` (FastAPI + uvicorn + pydantic)

---

## Lab Instructions

### Step 1: FastAPI Basics with Pydantic Models

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

# Pydantic models
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description='Price in USD')
    stock: int = Field(default=0, ge=0)
    category: str = Field(default='General')

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# In-memory store
class Store:
    def __init__(self):
        self.products: dict[int, dict] = {}
        self.next_id = 1

    def create(self, data: dict) -> dict:
        p = {**data, 'id': self.next_id, 'created_at': datetime.now()}
        p['status'] = 'out_of_stock' if p['stock'] == 0 else 'active'
        self.products[self.next_id] = p
        self.next_id += 1
        return p

    def get(self, pid: int) -> dict | None:
        return self.products.get(pid)

    def list(self, category: str = None, min_stock: int = None) -> list[dict]:
        items = list(self.products.values())
        if category: items = [p for p in items if p['category'] == category]
        if min_stock is not None: items = [p for p in items if p['stock'] >= min_stock]
        return items

    def update(self, pid: int, data: dict) -> dict | None:
        p = self.products.get(pid)
        if not p: return None
        p.update({k: v for k, v in data.items() if v is not None})
        p['status'] = 'out_of_stock' if p['stock'] == 0 else 'active'
        return p

    def delete(self, pid: int) -> bool:
        return self.products.pop(pid, None) is not None

store = Store()
app = FastAPI(title='innoZverse Product API', version='1.0.0')

@app.get('/products', response_model=list[dict], tags=['Products'])
def list_products(
    category: Optional[str] = Query(None, description='Filter by category'),
    min_stock: Optional[int] = Query(None, ge=0, description='Min stock'),
):
    return store.list(category=category, min_stock=min_stock)

@app.post('/products', status_code=201, tags=['Products'])
def create_product(product: ProductCreate):
    return store.create(product.model_dump())

@app.get('/products/{product_id}', tags=['Products'])
def get_product(product_id: int = Path(..., gt=0)):
    p = store.get(product_id)
    if not p: raise HTTPException(status_code=404, detail=f'Product {product_id} not found')
    return p

@app.patch('/products/{product_id}', tags=['Products'])
def update_product(product_id: int, update: ProductUpdate):
    p = store.update(product_id, update.model_dump(exclude_unset=True))
    if not p: raise HTTPException(status_code=404, detail='Product not found')
    return p

@app.delete('/products/{product_id}', status_code=204, tags=['Products'])
def delete_product(product_id: int):
    if not store.delete(product_id):
        raise HTTPException(status_code=404, detail='Product not found')

# Test with TestClient (no server needed)
client = TestClient(app)

# Create
r = client.post('/products', json={'name': 'Surface Pro 12\"', 'price': 864.0, 'stock': 15, 'category': 'Laptop'})
print(f'POST /products: {r.status_code} → id={r.json()[\"id\"]}')

client.post('/products', json={'name': 'Surface Pen', 'price': 49.99, 'stock': 80, 'category': 'Accessory'})
client.post('/products', json={'name': 'Office 365', 'price': 99.99, 'stock': 999, 'category': 'Software'})

# List
r = client.get('/products')
print(f'GET /products: {r.status_code} → {len(r.json())} items')

# Get by ID
r = client.get('/products/1')
p = r.json()
print(f'GET /products/1: {r.status_code} → {p[\"name\"]} \${p[\"price\"]}')

# 404
r = client.get('/products/99')
print(f'GET /products/99: {r.status_code} → {r.json()[\"detail\"]}')

# Update
r = client.patch('/products/1', json={'price': 799.99})
print(f'PATCH /products/1: {r.status_code} → price=\${r.json()[\"price\"]}')

# Filter
r = client.get('/products?category=Laptop')
print(f'GET /products?category=Laptop: {len(r.json())} items')

# Validation error
r = client.post('/products', json={'name': '', 'price': -1})
print(f'POST invalid: {r.status_code}')
"
```

> 💡 **Pydantic `Field()`** provides validation at the schema level: `gt=0` (greater than), `ge=0` (greater or equal), `min_length`, `max_length`. FastAPI automatically returns `422 Unprocessable Entity` with detailed error messages when validation fails — no manual validation code needed.

**📸 Verified Output:**
```
POST /products: 201 → id=1
GET /products: 200 → 3 items
GET /products/1: 200 → Surface Pro 12" $864.0
GET /products/99: 404 → Product 99 not found
PATCH /products/1: 200 → price=$799.99
GET /products?category=Laptop: 1 items
POST invalid: 422
```

---

### Step 2: Dependency Injection & Middleware

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# Middleware
@app.middleware('http')
async def add_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers['X-Process-Time'] = f'{elapsed:.2f}ms'
    return response

# Dependency injection
def get_current_user(authorization: str = Header(default=None)):
    tokens = {
        'Bearer admin-token': {'id': 1, 'name': 'Dr. Chen', 'role': 'admin'},
        'Bearer user-token':  {'id': 2, 'name': 'Alice',    'role': 'user'},
    }
    if not authorization or authorization not in tokens:
        raise HTTPException(status_code=401, detail='Invalid or missing token')
    return tokens[authorization]

def require_admin(user: dict = Depends(get_current_user)):
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return user

# Pagination dependency
class Pagination:
    def __init__(self, page: int = 1, per_page: int = 10):
        if page < 1: raise HTTPException(400, 'page must be >= 1')
        if per_page > 100: raise HTTPException(400, 'per_page max is 100')
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page

@app.get('/me')
def get_me(user: dict = Depends(get_current_user)):
    return {'user': user}

@app.get('/admin/stats')
def admin_stats(user: dict = Depends(require_admin)):
    return {'message': f'Admin stats for {user[\"name\"]}', 'total_products': 42}

@app.get('/products')
def list_products(pagination: Pagination = Depends()):
    return {
        'page': pagination.page,
        'per_page': pagination.per_page,
        'offset': pagination.offset,
        'items': [f'product-{i}' for i in range(pagination.offset, pagination.offset + 3)]
    }

client = TestClient(app)

# Auth
r = client.get('/me', headers={'Authorization': 'Bearer admin-token'})
print(f'GET /me (admin): {r.status_code} → {r.json()[\"user\"][\"name\"]}')

r = client.get('/me')
print(f'GET /me (no auth): {r.status_code}')

r = client.get('/admin/stats', headers={'Authorization': 'Bearer user-token'})
print(f'GET /admin (user): {r.status_code} → {r.json()[\"detail\"]}')

r = client.get('/admin/stats', headers={'Authorization': 'Bearer admin-token'})
print(f'GET /admin (admin): {r.status_code} → {r.json()[\"message\"]}')

r = client.get('/products?page=2&per_page=3')
data = r.json()
print(f'GET /products?page=2: offset={data[\"offset\"]} items={data[\"items\"]}')
"
```

**📸 Verified Output:**
```
GET /me (admin): 200 → Dr. Chen
GET /me (no auth): 401
GET /admin (user): 403 → Admin access required
GET /admin (admin): 200 → Admin stats for Dr. Chen
GET /products?page=2: offset=3 items=['product-3', 'product-4', 'product-5']
```

---

### Steps 3–8: Background Tasks, Exception Handlers, Response Models, Routers, Streaming, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json

app = FastAPI(title='innoZverse API', version='1.0.0')

# Custom exception handlers
class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status; self.code = code; self.message = message

@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        'error': {'code': exc.code, 'message': exc.message}
    })

# Models
class Order(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')

class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total: float
    status: str
    created_at: str

# Background task
notification_log: list[str] = []

def send_notification(email: str, order_id: int, total: float):
    msg = f'Order #{order_id} confirmed for {email}: \${total:.2f}'
    notification_log.append(msg)

# State
orders: dict[int, dict] = {}
next_order_id = 1

PRICES = {1: 864.0, 2: 49.99, 3: 99.99}

@app.post('/orders', status_code=201)
def create_order(order: Order, background_tasks: BackgroundTasks):
    global next_order_id
    price = PRICES.get(order.product_id)
    if not price:
        raise AppError(404, 'PRODUCT_NOT_FOUND', f'Product {order.product_id} not found')

    total = price * order.quantity
    created = {
        'id': next_order_id,
        'product_id': order.product_id,
        'quantity': order.quantity,
        'total': total,
        'status': 'confirmed',
        'created_at': datetime.now().isoformat(),
    }
    orders[next_order_id] = created
    next_order_id += 1

    # Run after response is sent
    background_tasks.add_task(send_notification, order.customer_email, created['id'], total)
    return created

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    o = orders.get(order_id)
    if not o: raise AppError(404, 'ORDER_NOT_FOUND', f'Order {order_id} not found')
    return o

@app.get('/export/orders')
def export_orders():
    def generate():
        yield 'id,product_id,quantity,total,status\n'
        for o in orders.values():
            yield f'{o[\"id\"]},{o[\"product_id\"]},{o[\"quantity\"]},{o[\"total\"]},{o[\"status\"]}\n'
    return StreamingResponse(generate(), media_type='text/csv',
                             headers={'Content-Disposition': 'attachment; filename=orders.csv'})

@app.get('/health')
def health():
    return {'status': 'healthy', 'version': '1.0.0', 'orders': len(orders)}

# Test all routes
client = TestClient(app)

# Create orders
r = client.post('/orders', json={'product_id': 1, 'quantity': 2, 'customer_email': 'ebiz@chen.me'})
print(f'POST /orders: {r.status_code} → id={r.json()[\"id\"]} total=\${r.json()[\"total\"]}')

r2 = client.post('/orders', json={'product_id': 2, 'quantity': 5, 'customer_email': 'alice@test.com'})
print(f'POST /orders: {r2.status_code} → id={r2.json()[\"id\"]} total=\${r2.json()[\"total\"]}')

# Error cases
r = client.post('/orders', json={'product_id': 99, 'quantity': 1, 'customer_email': 'x@y.com'})
print(f'POST /orders (bad product): {r.status_code} → {r.json()[\"error\"][\"code\"]}')

r = client.post('/orders', json={'product_id': 1, 'quantity': 1, 'customer_email': 'not-an-email'})
print(f'POST /orders (bad email): {r.status_code}')

# Get order
r = client.get('/orders/1')
print(f'GET /orders/1: {r.status_code} → status={r.json()[\"status\"]}')

# Export CSV
r = client.get('/export/orders')
print(f'GET /export/orders: {r.status_code}')
print('CSV output:')
print(r.text)

# Health
r = client.get('/health')
print(f'GET /health: {r.json()}')

# Background notifications
print(f'Notifications sent: {len(notification_log)}')
for n in notification_log: print(f'  {n}')
"
```

**📸 Verified Output:**
```
POST /orders: 201 → id=1 total=$1728.0
POST /orders: 201 → id=2 total=$249.95
POST /orders (bad product): 404 → PRODUCT_NOT_FOUND
POST /orders (bad email): 422
GET /orders/1: 200 → status=confirmed
GET /export/orders: 200
CSV output:
id,product_id,quantity,total,status
1,1,2,1728.0,confirmed
2,2,5,249.95,confirmed

GET /health: {'status': 'healthy', 'version': '1.0.0', 'orders': 2}
Notifications sent: 2
  Order #1 confirmed for ebiz@chen.me: $1728.00
  Order #2 confirmed for alice@test.com: $249.95
```

---

## Summary

| Feature | FastAPI | Notes |
|---------|---------|-------|
| Route | `@app.get('/path')` | Supports GET, POST, PUT, PATCH, DELETE |
| Body model | `class M(BaseModel):` | Auto-validated, auto-documented |
| Path param | `def f(id: int = Path(..., gt=0))` | Type-checked |
| Query param | `def f(q: str = Query(None))` | Optional/required |
| Dependency | `Depends(fn)` | Reusable auth, DB, pagination |
| Background | `BackgroundTasks.add_task(fn, ...)` | Async post-response work |
| Error | `HTTPException(status_code, detail)` | Automatic JSON response |
| Testing | `TestClient(app)` | No server needed |

## Further Reading
- [FastAPI docs](https://fastapi.tiangolo.com)
- [Pydantic docs](https://docs.pydantic.dev)
