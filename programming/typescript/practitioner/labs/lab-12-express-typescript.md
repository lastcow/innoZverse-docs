# Lab 12: Express + TypeScript

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Express with `@types/express`: typed Request/Response/NextFunction, Request augmentation, typed middleware, Zod validation middleware.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab12 && cd /lab12
npm init -y
npm install express zod
npm install --save-dev @types/express @types/node
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true
  }
}
EOF
```

---

## Step 2: Basic Typed Route Handlers

```typescript
// routes/users.ts
import { Request, Response, NextFunction } from 'express';

// Typed route handler
export function getUsers(req: Request, res: Response): void {
  const users = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob',   email: 'bob@example.com' },
  ];
  res.json({ data: users });
}

// Typed params/query
interface UserParams { id: string }
interface UserQuery  { format?: 'full' | 'minimal' }

export function getUser(
  req: Request<UserParams, unknown, unknown, UserQuery>,
  res: Response
): void {
  const { id } = req.params;
  const { format } = req.query;
  const user = { id: Number(id), name: 'Alice', email: 'alice@example.com' };
  if (format === 'minimal') {
    res.json({ id: user.id, name: user.name });
  } else {
    res.json(user);
  }
}
```

---

## Step 3: Request Interface Augmentation

```typescript
// types/express.d.ts
import { User } from '../models';

declare global {
  namespace Express {
    interface Request {
      user?: User;
      requestId?: string;
      startTime?: number;
    }
  }
}

// Now req.user, req.requestId, req.startTime are typed everywhere
```

---

## Step 4: Typed Middleware

```typescript
// middleware/auth.ts
import { Request, Response, NextFunction } from 'express';

export interface AuthRequest extends Request {
  user: { id: number; name: string; role: string };
}

export function authenticate(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const token = req.headers['authorization']?.replace('Bearer ', '');
  if (!token) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  // In real code: verify JWT
  (req as AuthRequest).user = { id: 1, name: 'Alice', role: 'admin' };
  next();
}

export function requestId(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  req.requestId = Math.random().toString(36).slice(2);
  req.startTime = Date.now();
  res.setHeader('X-Request-Id', req.requestId);
  next();
}

export function logger(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  res.on('finish', () => {
    const dur = req.startTime ? Date.now() - req.startTime : 0;
    console.log(`${req.method} ${req.path} ${res.statusCode} ${dur}ms [${req.requestId}]`);
  });
  next();
}
```

---

## Step 5: Zod Validation Middleware

```typescript
// middleware/validate.ts
import { Request, Response, NextFunction } from 'express';
import { z, ZodType } from 'zod';

export function validateBody<T>(schema: ZodType<T>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(400).json({
        error: 'Validation failed',
        issues: result.error.issues.map(i => ({
          path: i.path.join('.'),
          message: i.message,
        })),
      });
      return;
    }
    req.body = result.data;  // Replace with validated, transformed data
    next();
  };
}

export function validateQuery<T>(schema: ZodType<T>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      res.status(400).json({ error: 'Invalid query', issues: result.error.issues });
      return;
    }
    next();
  };
}
```

---

## Step 6: Full Express Application

```typescript
// app.ts
import express from 'express';
import { z } from 'zod';

const app = express();
app.use(express.json());

// Zod schemas
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'guest']).default('user'),
});

type CreateUserDto = z.infer<typeof CreateUserSchema>;

// In-memory store
const users: (CreateUserDto & { id: number })[] = [];
let nextId = 1;

// Validation middleware
function validateBody<T>(schema: z.ZodType<T>) {
  return (req: express.Request, res: express.Response, next: express.NextFunction): void => {
    const r = schema.safeParse(req.body);
    if (!r.success) { res.status(400).json({ error: r.error.issues }); return; }
    req.body = r.data;
    next();
  };
}

// Routes
app.get('/users', (req, res) => {
  res.json({ data: users });
});

app.post('/users', validateBody(CreateUserSchema), (req: express.Request, res) => {
  const user = { ...req.body as CreateUserDto, id: nextId++ };
  users.push(user);
  res.status(201).json({ data: user });
});

app.get('/users/:id', (req, res) => {
  const user = users.find(u => u.id === Number(req.params.id));
  if (!user) { res.status(404).json({ error: 'Not found' }); return; }
  res.json({ data: user });
});

export default app;
```

---

## Step 7: Error Handling Middleware

```typescript
// middleware/error.ts
import { Request, Response, NextFunction } from 'express';

class AppError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// Error handler must have 4 params
function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction  // must be declared even if unused
): void {
  if (err instanceof AppError) {
    res.status(err.statusCode).json({
      error: err.message,
      details: err.details,
    });
    return;
  }
  console.error(err);
  res.status(500).json({ error: 'Internal server error' });
}

// Async route wrapper (avoids try/catch in every route)
function asyncHandler<T>(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<T>
) {
  return (req: Request, res: Response, next: NextFunction): void => {
    fn(req, res, next).catch(next);
  };
}
```

---

## Step 8: Capstone — Verifiable Server Test

```typescript
// Save as lab12-capstone.ts
import express from 'express';
import { z } from 'zod';
import http from 'http';

const app = express();
app.use(express.json());

const UserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});
type User = z.infer<typeof UserSchema> & { id: number };
const users: User[] = [];

app.get('/health', (_, res) => res.json({ status: 'ok' }));
app.post('/users', (req, res) => {
  const r = UserSchema.safeParse(req.body);
  if (!r.success) { res.status(400).json({ error: 'Invalid' }); return; }
  const user = { ...r.data, id: users.length + 1 };
  users.push(user);
  res.status(201).json(user);
});
app.get('/users', (_, res) => res.json(users));

const server = http.createServer(app);
server.listen(0, () => {
  const addr = server.address() as { port: number };
  console.log(`Server on port ${addr.port}`);

  // Test it
  const opts = { hostname: 'localhost', port: addr.port, method: 'POST',
    path: '/users', headers: { 'Content-Type': 'application/json' } };
  const req = http.request(opts, res => {
    let body = '';
    res.on('data', d => body += d);
    res.on('end', () => {
      const user = JSON.parse(body);
      console.log('Created user:', user.name, user.id);
      server.close(() => console.log('Express TypeScript OK'));
    });
  });
  req.write(JSON.stringify({ name: 'Alice', email: 'alice@example.com' }));
  req.end();
});
```

Run:
```bash
ts-node -P tsconfig.json lab12-capstone.ts
```

📸 **Verified Output:**
```
Server on port [dynamic]
Created user: Alice 1
Express TypeScript OK
```

---

## Summary

| Concept | Pattern |
|---------|---------|
| Typed handler | `(req: Request<P,B,Q>, res: Response)` |
| Request augmentation | `declare global { namespace Express { interface Request { ... } } }` |
| Typed middleware | `(req, res, next: NextFunction): void` |
| Zod validation | `schema.safeParse(req.body)` |
| Error middleware | 4 params `(err, req, res, next)` |
| Async wrapper | `fn(...).catch(next)` |
