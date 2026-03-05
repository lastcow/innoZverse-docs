# Lab 11: REST API with Express.js

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build a complete REST API using Express.js: routing, middleware, `express.json()`, error handling middleware, and full CRUD endpoints.

---

## Step 1: Setup

```bash
# Inside Docker container
mkdir /app && cd /app
npm init -y
npm install express
```

---

## Step 2: Basic Express Server

```javascript
// server.js
const express = require('express');
const app = express();

// Built-in middleware
app.use(express.json());           // Parse JSON bodies
app.use(express.urlencoded({ extended: true })); // Parse form data

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// Simple route
app.get('/', (req, res) => {
  res.json({ message: 'Hello, Express!', timestamp: new Date().toISOString() });
});

app.listen(3000, () => console.log('Server on :3000'));
```

> 💡 Middleware functions have `(req, res, next)` signature. Call `next()` to pass to the next middleware/route. Call `next(err)` to skip to error handler.

---

## Step 3: Router — Organizing Routes

```javascript
// routes/users.js
const { Router } = require('express');
const router = Router();

// In-memory "database"
let users = [
  { id: 1, name: 'Alice', email: 'alice@example.com', role: 'admin' },
  { id: 2, name: 'Bob', email: 'bob@example.com', role: 'user' },
];
let nextId = 3;

// GET /users — list all (with optional filter)
router.get('/', (req, res) => {
  const { role, limit = 10, offset = 0 } = req.query;
  let result = role ? users.filter(u => u.role === role) : users;
  const total = result.length;
  result = result.slice(Number(offset), Number(offset) + Number(limit));
  res.json({ data: result, total, limit: Number(limit), offset: Number(offset) });
});

// GET /users/:id — get one
router.get('/:id', (req, res, next) => {
  const user = users.find(u => u.id === Number(req.params.id));
  if (!user) return next({ status: 404, message: `User ${req.params.id} not found` });
  res.json(user);
});

// POST /users — create
router.post('/', (req, res, next) => {
  const { name, email, role = 'user' } = req.body;
  if (!name || !email) return next({ status: 400, message: 'name and email required' });
  if (users.some(u => u.email === email)) {
    return next({ status: 409, message: 'Email already exists' });
  }
  const user = { id: nextId++, name, email, role };
  users.push(user);
  res.status(201).json(user);
});

// PUT /users/:id — full update
router.put('/:id', (req, res, next) => {
  const idx = users.findIndex(u => u.id === Number(req.params.id));
  if (idx === -1) return next({ status: 404, message: 'User not found' });
  const { name, email, role } = req.body;
  if (!name || !email) return next({ status: 400, message: 'name and email required' });
  users[idx] = { id: users[idx].id, name, email, role: role || 'user' };
  res.json(users[idx]);
});

// PATCH /users/:id — partial update
router.patch('/:id', (req, res, next) => {
  const idx = users.findIndex(u => u.id === Number(req.params.id));
  if (idx === -1) return next({ status: 404, message: 'User not found' });
  users[idx] = { ...users[idx], ...req.body, id: users[idx].id };
  res.json(users[idx]);
});

// DELETE /users/:id
router.delete('/:id', (req, res, next) => {
  const idx = users.findIndex(u => u.id === Number(req.params.id));
  if (idx === -1) return next({ status: 404, message: 'User not found' });
  users.splice(idx, 1);
  res.status(204).send();
});

module.exports = router;
```

---

## Step 4: Middleware Chain

```javascript
// middleware/auth.js
function requireAuth(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Missing token' });
  // In real app: verify JWT here
  if (token !== 'valid-token') return res.status(403).json({ error: 'Invalid token' });
  req.user = { id: 1, role: 'admin' }; // Attach to request
  next();
}

function requireRole(role) {
  return (req, res, next) => {
    if (!req.user || req.user.role !== role) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}

// middleware/validate.js
function validateBody(schema) {
  return (req, res, next) => {
    const errors = [];
    for (const [field, rules] of Object.entries(schema)) {
      if (rules.required && !req.body[field]) {
        errors.push(`${field} is required`);
      }
      if (rules.type && req.body[field] && typeof req.body[field] !== rules.type) {
        errors.push(`${field} must be ${rules.type}`);
      }
      if (rules.maxLength && req.body[field]?.length > rules.maxLength) {
        errors.push(`${field} max length is ${rules.maxLength}`);
      }
    }
    if (errors.length) return res.status(400).json({ errors });
    next();
  };
}

module.exports = { requireAuth, requireRole, validateBody };
```

---

## Step 5: Error Handling Middleware

```javascript
// middleware/errorHandler.js

// 404 handler (must be after all routes)
function notFound(req, res, next) {
  next({ status: 404, message: `Route ${req.method} ${req.path} not found` });
}

// Error handler (must have 4 params!)
function errorHandler(err, req, res, next) {
  const status = err.status || err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  // Log server errors
  if (status >= 500) {
    console.error(`[ERROR] ${status}: ${message}`);
    console.error(err.stack);
  }

  res.status(status).json({
    error: {
      status,
      message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    }
  });
}

module.exports = { notFound, errorHandler };
```

---

## Step 6: Complete Server Assembly

```javascript
// app.js
const express = require('express');
const app = express();

// Core middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request ID middleware
app.use((req, res, next) => {
  req.id = Math.random().toString(36).slice(2, 9);
  res.setHeader('X-Request-Id', req.id);
  next();
});

// Health check (no auth needed)
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), pid: process.pid });
});

// API routes
const usersRouter = require('./routes/users');
app.use('/api/users', usersRouter);

// 404 and error handlers (MUST be last)
app.use((req, res, next) => next({ status: 404, message: 'Not Found' }));
app.use((err, req, res, next) => {
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal Error' });
});

module.exports = app;
```

---

## Step 7: Testing the API

```bash
# In Docker: npm install express && node server.js &
# Then test:

# List users
curl http://localhost:3000/api/users

# Get user
curl http://localhost:3000/api/users/1

# Create user
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@example.com"}'

# Update user
curl -X PATCH http://localhost:3000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}'

# Delete user
curl -X DELETE http://localhost:3000/api/users/2
```

---

## Step 8: Capstone — Inline Demo

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null && npm install express --quiet > /dev/null 2>&1

node -e '
const express = require(\"/tmp/node_modules/express\");
const app = express();
app.use(express.json());

let items = [
  { id: 1, name: \"Widget\", price: 9.99 },
  { id: 2, name: \"Gadget\", price: 24.99 }
];
let nextId = 3;

app.get(\"/items\", (req, res) => res.json(items));
app.get(\"/items/:id\", (req, res) => {
  const item = items.find(i => i.id === +req.params.id);
  item ? res.json(item) : res.status(404).json({ error: \"Not found\" });
});
app.post(\"/items\", (req, res) => {
  const item = { id: nextId++, ...req.body };
  items.push(item);
  res.status(201).json(item);
});
app.delete(\"/items/:id\", (req, res) => {
  items = items.filter(i => i.id !== +req.params.id);
  res.status(204).send();
});
app.use((err, req, res, next) => res.status(err.status || 500).json({ error: err.message }));

const server = app.listen(3333, async () => {
  const http = require(\"http\");
  const get = (path) => new Promise((resolve, reject) => {
    http.get(\"http://localhost:3333\" + path, (res) => {
      let data = \"\";
      res.on(\"data\", d => data += d);
      res.on(\"end\", () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    }).on(\"error\", reject);
  });
  
  const list = await get(\"/items\");
  console.log(\"GET /items:\", list.status, JSON.stringify(list.body.map(i => i.name)));
  const one = await get(\"/items/1\");
  console.log(\"GET /items/1:\", one.status, one.body.name);
  const notFound = await get(\"/items/999\");
  console.log(\"GET /items/999:\", notFound.status, notFound.body.error);
  server.close();
});
'
"
```

📸 **Verified Output:**
```
GET /items: 200 ["Widget","Gadget"]
GET /items/1: 200 Widget
GET /items/999: 404 Not found
```

---

## Summary

| Express Feature | Code | Purpose |
|----------------|------|---------|
| `express.json()` | `app.use(express.json())` | Parse JSON request bodies |
| Route params | `req.params.id` | `/users/:id` |
| Query strings | `req.query.filter` | `/users?role=admin` |
| Router | `express.Router()` | Modular route grouping |
| Middleware | `(req, res, next) => {}` | Auth, logging, validation |
| Error middleware | `(err, req, res, next) => {}` | Centralized error handling |
| Status codes | `res.status(201).json({})` | HTTP semantics |
| 404 handler | After all routes | Catch unmatched routes |
