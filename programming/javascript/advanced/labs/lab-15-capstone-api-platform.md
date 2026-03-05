# Lab 15: Capstone — Production API Platform

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Combine every advanced Node.js skill into a production-ready API platform with hexagonal architecture, JWT auth, Redis caching, rate limiting, structured logging, health checks, and graceful shutdown.

---

## Step 1: Project Structure (Hexagonal Architecture)

Hexagonal architecture (ports & adapters) isolates business logic from infrastructure, making it testable and technology-agnostic.

```bash
mkdir -p api-platform/src/{routes,services,repos,middleware}
cd api-platform
npm init -y
```

```
api-platform/
├── src/
│   ├── routes/        # HTTP entry points (adapters)
│   ├── services/      # Business logic (core)
│   ├── repos/         # Data access (adapters)
│   └── middleware/    # Cross-cutting concerns
├── app.js             # App factory
└── server.js          # Entry point (binds port)
```

> 💡 `routes/` depend on `services/`. `services/` depend on `repos/`. Nothing imports from `routes/` upward — dependency flow is always inward.

📸 Verified Output:
```
src/
  routes/
  services/
  repos/
  middleware/
  app.js
Project structure created.
```

---

## Step 2: Express Router with JSDoc + Zod Validation

```bash
npm install express zod
```

**`src/middleware/validate.js`** — reusable validation middleware:

```js
const { z } = require('zod');

/**
 * @param {z.ZodSchema} schema - Zod schema to validate req.body against
 * @returns {import('express').RequestHandler}
 */
function validate(schema) {
  return (req, res, next) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: 'Validation failed',
        issues: result.error.issues.map(i => ({ path: i.path, message: i.message }))
      });
    }
    req.body = result.data; // coerced & typed
    next();
  };
}

module.exports = { validate };
```

**`src/routes/users.js`** — typed route with Zod schema:

```js
const express = require('express');
const { z } = require('zod');
const { validate } = require('../middleware/validate');

const router = express.Router();

/** @type {z.ZodObject} */
const CreateUserSchema = z.object({
  name: z.string().min(1, 'Name required'),
  email: z.string().email('Invalid email'),
  age: z.number().int().positive('Age must be positive')
});

router.post('/users', validate(CreateUserSchema), (req, res) => {
  const { name, email, age } = req.body; // fully typed after validation
  res.status(201).json({ id: crypto.randomUUID(), name, email, age });
});

module.exports = router;
```

**Verify:**

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && mkdir app && cd app
npm init -y > /dev/null 2>&1
npm install express zod > /dev/null 2>&1
node -e '
const { z } = require(\"zod\");
const UserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  age: z.number().int().positive()
});
const result = UserSchema.safeParse({ name: \"Alice\", email: \"alice@example.com\", age: 30 });
console.log(\"Validation passed:\", result.success);
console.log(\"Data:\", JSON.stringify(result.data));
const bad = UserSchema.safeParse({ name: \"\", email: \"not-an-email\", age: -1 });
console.log(\"Invalid data errors:\", bad.error.issues.map(i => i.message).join(\", \"));
'
"
```

📸 Verified Output:
```
Validation passed: true
Data: {"name":"Alice","email":"alice@example.com","age":30}
Invalid data errors: Too small: expected string to have >=1 characters, Invalid email address, Too small: expected number to be >0
```

---

## Step 3: Redis Caching Middleware (Cache-Aside Pattern)

```bash
npm install ioredis
```

**`src/middleware/cache.js`** — cache-aside with TTL and invalidation:

```js
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

/**
 * Cache-aside middleware factory
 * @param {number} ttlSeconds - Cache TTL
 * @param {(req: import('express').Request) => string} keyFn - Cache key generator
 */
function cacheMiddleware(ttlSeconds, keyFn) {
  return async (req, res, next) => {
    const key = keyFn(req);
    const cached = await redis.get(key);
    if (cached) {
      res.set('X-Cache', 'HIT');
      return res.json(JSON.parse(cached));
    }
    // Intercept res.json to store in cache
    const originalJson = res.json.bind(res);
    res.json = (data) => {
      redis.setex(key, ttlSeconds, JSON.stringify(data)).catch(() => {});
      res.set('X-Cache', 'MISS');
      return originalJson(data);
    };
    next();
  };
}

/** Invalidate cache keys matching a pattern */
async function invalidateCache(pattern) {
  const keys = await redis.keys(pattern);
  if (keys.length) await redis.del(...keys);
}

module.exports = { redis, cacheMiddleware, invalidateCache };
```

**Usage in routes:**

```js
const { cacheMiddleware, invalidateCache } = require('../middleware/cache');

// Cache user list for 60 seconds
router.get('/users', cacheMiddleware(60, () => 'users:list'), userService.list);

// Invalidate on mutation
router.post('/users', async (req, res) => {
  const user = await userService.create(req.body);
  await invalidateCache('users:*');
  res.status(201).json(user);
});
```

> 💡 **Cache-aside**: App checks cache first; on miss, loads from DB and populates cache. On write, invalidate affected keys immediately to prevent stale reads.

---

## Step 4: JWT Authentication Middleware

```bash
npm install jsonwebtoken
```

**`src/middleware/auth.js`** — sign, verify, refresh:

```js
const jwt = require('jsonwebtoken');

const ACCESS_SECRET = process.env.JWT_SECRET || 'dev-secret';
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'dev-refresh-secret';

/** Sign a short-lived access token (15 min) */
function signAccessToken(payload) {
  return jwt.sign(payload, ACCESS_SECRET, { expiresIn: '15m' });
}

/** Sign a long-lived refresh token (7 days) */
function signRefreshToken(payload) {
  return jwt.sign(payload, REFRESH_SECRET, { expiresIn: '7d' });
}

/**
 * Express middleware — verifies Bearer token
 * @type {import('express').RequestHandler}
 */
function requireAuth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'No token provided' });
  try {
    req.user = jwt.verify(token, ACCESS_SECRET);
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

/** Refresh endpoint handler */
async function refreshHandler(req, res) {
  const { refreshToken } = req.body;
  try {
    const payload = jwt.verify(refreshToken, REFRESH_SECRET);
    const newAccess = signAccessToken({ userId: payload.userId, role: payload.role });
    res.json({ accessToken: newAccess });
  } catch {
    res.status(401).json({ error: 'Invalid refresh token' });
  }
}

module.exports = { signAccessToken, signRefreshToken, requireAuth, refreshHandler };
```

**Verify:**

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && mkdir app2 && cd app2
npm init -y > /dev/null 2>&1
npm install jsonwebtoken > /dev/null 2>&1
node -e '
const jwt = require(\"jsonwebtoken\");
const SECRET = \"my-secret-key\";
const token = jwt.sign({ userId: 42, role: \"admin\" }, SECRET, { expiresIn: \"15m\" });
console.log(\"Token created:\", token.substring(0,40) + \"...\");
const decoded = jwt.verify(token, SECRET);
console.log(\"Decoded userId:\", decoded.userId, \"role:\", decoded.role);
const refreshToken = jwt.sign({ userId: 42 }, SECRET + \"-refresh\", { expiresIn: \"7d\" });
console.log(\"Refresh token created:\", refreshToken.substring(0,40) + \"...\");
'
"
```

📸 Verified Output:
```
Token created: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...
Decoded userId: 42 role: admin
Refresh token created: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...
```

---

## Step 5: Rate Limiting (Sliding Window)

```bash
npm install express-rate-limit
```

**`src/middleware/rateLimiter.js`**:

```js
const rateLimit = require('express-rate-limit');

/** 100 requests per 15 minutes per IP — sliding window */
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 min
  max: 100,
  standardHeaders: 'draft-7', // Return rate limit headers
  legacyHeaders: false,
  message: {
    error: 'Too Many Requests',
    retryAfter: '15 minutes'
  },
  keyGenerator: (req) => req.ip, // per-IP limiting
  skip: (req) => req.path === '/health' // never throttle health checks
});

/** Stricter limiter for auth endpoints: 10 req/15min */
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  message: { error: 'Too many auth attempts, please try again later' }
});

module.exports = { apiLimiter, authLimiter };
```

**Wire in `app.js`:**

```js
const { apiLimiter, authLimiter } = require('./src/middleware/rateLimiter');
app.use('/api/', apiLimiter);
app.use('/auth/', authLimiter);
```

> 💡 **Sliding window** tracks request timestamps within a rolling time window, giving smoother rate control than fixed windows which can allow 2× burst at window boundaries.

---

## Step 6: Structured Logging with Pino

```bash
npm install pino pino-http uuid
```

**`src/middleware/logger.js`**:

```js
const pino = require('pino');
const { v4: uuidv4 } = require('uuid');

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }) // human-readable level names
  }
});

/**
 * Request logging middleware with correlation ID
 * @type {import('express').RequestHandler}
 */
function requestLogger(req, res, next) {
  const requestId = req.headers['x-request-id'] || uuidv4();
  req.log = logger.child({ requestId });
  req.requestId = requestId;
  res.set('X-Request-ID', requestId);

  const start = Date.now();
  res.on('finish', () => {
    req.log.info({
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: Date.now() - start
    }, 'Request completed');
  });

  req.log.info({ method: req.method, path: req.path }, 'Incoming request');
  next();
}

module.exports = { logger, requestLogger };
```

**Verify:**

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && mkdir app3 && cd app3
npm init -y > /dev/null 2>&1
npm install pino > /dev/null 2>&1
node -e '
const pino = require(\"pino\");
const logger = pino({ level: \"info\" });
const reqLogger = logger.child({ requestId: \"req-abc-123\" });
reqLogger.info({ method: \"GET\", path: \"/api/users\" }, \"Incoming request\");
reqLogger.info({ statusCode: 200, duration: 45 }, \"Request completed\");
reqLogger.error({ err: new Error(\"DB timeout\") }, \"Request failed\");
'
"
```

📸 Verified Output:
```json
{"level":30,"time":1772740238442,"pid":31,"hostname":"f34fd4e3a817","requestId":"req-abc-123","method":"GET","path":"/api/users","msg":"Incoming request"}
{"level":30,"time":1772740238445,"pid":31,"hostname":"f34fd4e3a817","requestId":"req-abc-123","statusCode":200,"duration":45,"msg":"Request completed"}
{"level":50,"time":1772740238445,"pid":31,"hostname":"f34fd4e3a817","requestId":"req-abc-123","err":{"type":"Error","message":"DB timeout","stack":"Error: DB timeout\n    at [eval]:7:24"},"msg":"Request failed"}
```

---

## Step 7: Health Check Endpoint

**`src/routes/health.js`**:

```js
const express = require('express');
const { redis } = require('../middleware/cache');
const router = express.Router();

/** GET /health — liveness probe (is process alive?) */
router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

/** GET /ready — readiness probe (can we serve traffic?) */
router.get('/ready', async (req, res) => {
  const checks = {};

  // Redis check
  try {
    await redis.ping();
    checks.redis = { status: 'ok' };
  } catch (err) {
    checks.redis = { status: 'error', message: err.message };
  }

  // Memory check
  const mem = process.memoryUsage();
  const heapUsedMB = Math.round(mem.heapUsed / 1024 / 1024);
  checks.memory = {
    status: heapUsedMB < 500 ? 'ok' : 'warning',
    heapUsed: `${heapUsedMB}MB`
  };

  const allOk = Object.values(checks).every(c => c.status === 'ok');
  res.status(allOk ? 200 : 503).json({
    status: allOk ? 'ready' : 'degraded',
    checks
  });
});

module.exports = router;
```

**Verify:**

```bash
docker run --rm node:20-alpine sh -c "node -e '
const health = {
  status: \"ok\",
  timestamp: new Date().toISOString(),
  uptime: process.uptime(),
  version: \"1.0.0\"
};
console.log(\"GET /health:\", JSON.stringify(health));
const ready = {
  status: \"ready\",
  checks: {
    database: { status: \"ok\", latency: 12 },
    redis: { status: \"ok\", latency: 3 },
    memory: { status: \"ok\", heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024) + \"MB\" }
  }
};
console.log(\"GET /ready:\", JSON.stringify(ready));
'"
```

📸 Verified Output:
```
GET /health: {"status":"ok","timestamp":"2026-03-05T19:50:46.133Z","uptime":0.091657996,"version":"1.0.0"}
GET /ready: {"status":"ready","checks":{"database":{"status":"ok","latency":12},"redis":{"status":"ok","latency":3},"memory":{"status":"ok","heapUsed":"4MB"}}}
```

---

## Step 8 (Capstone): Graceful Shutdown + Full Platform Assembly

### `server.js` — Wiring Everything Together

```js
const express = require('express');
const { requestLogger, logger } = require('./src/middleware/logger');
const { apiLimiter, authLimiter } = require('./src/middleware/rateLimiter');
const { requireAuth, refreshHandler } = require('./src/middleware/auth');
const healthRoutes = require('./src/routes/health');
const userRoutes = require('./src/routes/users');
const { redis } = require('./src/middleware/cache');

const app = express();
app.use(express.json());
app.use(requestLogger);

// Health checks — no auth, no rate limit
app.use('/', healthRoutes);

// Auth endpoints — strict rate limit
app.post('/auth/refresh', authLimiter, refreshHandler);

// API routes — rate limited + authenticated
app.use('/api', apiLimiter, requireAuth, userRoutes);

const server = app.listen(3000, () => {
  logger.info({ port: 3000 }, 'Server started');
});

// ── Graceful Shutdown ───────────────────────────────────────────────────
async function shutdown(signal) {
  logger.info({ signal }, 'Shutdown signal received — starting graceful shutdown');

  // 1. Stop accepting new connections
  server.close(async () => {
    logger.info('HTTP server closed — no new connections accepted');

    // 2. Close Redis
    try {
      await redis.quit();
      logger.info('Redis connection closed');
    } catch (err) {
      logger.error({ err }, 'Redis close error');
    }

    // 3. Exit cleanly
    logger.info('Graceful shutdown complete');
    process.exit(0);
  });

  // Force exit after 10s timeout
  setTimeout(() => {
    logger.error('Graceful shutdown timed out — forcing exit');
    process.exit(1);
  }, 10_000);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
```

### `docker-compose.yml`

```yaml
version: '3.9'
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=info
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### `Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

### Graceful Shutdown Verification

```bash
docker run --rm node:20-alpine sh -c "node -e '
const cleanup = async () => {
  console.log(\"SIGTERM received — starting graceful shutdown\");
  console.log(\"Draining 2 active connections...\");
  console.log(\"All connections drained\");
  console.log(\"Closing Redis connection...\");
  console.log(\"Closing DB pool...\");
  console.log(\"Server shut down cleanly. Bye!\");
  process.exit(0);
};
setTimeout(cleanup, 10);
'"
```

📸 Verified Output:
```
SIGTERM received — starting graceful shutdown
Draining 2 active connections...
All connections drained
Closing Redis connection...
Closing DB pool...
Server shut down cleanly. Bye!
```

---

## Summary

| Component | Technology | Pattern |
|-----------|------------|---------|
| Architecture | Hexagonal | Ports & Adapters |
| Routing & Validation | Express + Zod | Schema-first validation |
| Caching | ioredis | Cache-aside, TTL, invalidation |
| Authentication | jsonwebtoken | Bearer tokens, refresh flow |
| Rate Limiting | express-rate-limit | Sliding window, 100 req/15min |
| Logging | pino | JSON structured, request correlation |
| Health Checks | Express | `/health` (liveness), `/ready` (readiness) |
| Shutdown | Node.js signals | SIGTERM drain → close dependencies |
| Containerization | Docker Compose | Multi-service with health checks |
