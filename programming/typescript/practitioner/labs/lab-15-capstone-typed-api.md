# Lab 15: Capstone — Fully Typed Express REST API

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

CAPSTONE: Fully typed Express REST API with Zod schemas, typed middleware stack, Result<T,E> error handling, typed env vars, 100% strict TypeScript.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab15 && cd /lab15
npm init -y
npm install express zod
npm install --save-dev @types/express @types/node typescript
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
EOF
```

---

## Step 2: Typed Environment Variables

```typescript
// src/env.ts
import { z } from 'zod';

const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3000').transform(Number),
  HOST: z.string().default('localhost'),
  JWT_SECRET: z.string().default('dev-secret-change-in-production'),
  DB_URL: z.string().optional(),
});

export type Env = z.infer<typeof EnvSchema>;

function loadEnv(): Env {
  const result = EnvSchema.safeParse(process.env);
  if (!result.success) {
    console.error('❌ Invalid environment variables:');
    result.error.issues.forEach(i => {
      console.error(`  ${i.path.join('.')}: ${i.message}`);
    });
    process.exit(1);
  }
  return result.data;
}

export const env = loadEnv();
```

---

## Step 3: Result<T, E> Error Handling

```typescript
// src/result.ts
export type Ok<T>  = { ok: true;  value: T };
export type Err<E> = { ok: false; error: E };
export type Result<T, E = Error> = Ok<T> | Err<E>;

export const ok  = <T>(value: T): Ok<T>   => ({ ok: true, value });
export const err = <E>(error: E): Err<E>  => ({ ok: false, error });

export function isOk<T, E>(r: Result<T, E>): r is Ok<T>   { return r.ok; }
export function isErr<T, E>(r: Result<T, E>): r is Err<E> { return !r.ok; }

// Typed error types
export interface AppError {
  code: string;
  message: string;
  statusCode: number;
  details?: unknown;
}

export const notFound  = (msg: string): AppError => ({ code: 'NOT_FOUND', message: msg, statusCode: 404 });
export const badRequest = (msg: string, details?: unknown): AppError =>
  ({ code: 'BAD_REQUEST', message: msg, statusCode: 400, details });
export const serverError = (msg: string): AppError => ({ code: 'INTERNAL', message: msg, statusCode: 500 });
```

---

## Step 4: Zod Schemas (Request/Response)

```typescript
// src/schemas/user.ts
import { z } from 'zod';

export const CreateUserSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email().toLowerCase(),
  role: z.enum(['admin', 'user', 'guest']).default('user'),
});

export const UpdateUserSchema = CreateUserSchema.partial();

export const UserSchema = CreateUserSchema.extend({
  id: z.number().int().positive(),
  createdAt: z.string().datetime(),
});

export const PaginationSchema = z.object({
  page: z.string().default('1').transform(Number),
  limit: z.string().default('10').transform(n => Math.min(Number(n), 100)),
});

export type CreateUserDto = z.infer<typeof CreateUserSchema>;
export type UpdateUserDto = z.infer<typeof UpdateUserSchema>;
export type User = z.infer<typeof UserSchema>;
```

---

## Step 5: Typed Middleware Stack

```typescript
// src/middleware.ts
import { Request, Response, NextFunction } from 'express';
import { ZodType } from 'zod';
import { badRequest } from './result';

// Validation middleware factory
export function validateBody<T>(schema: ZodType<T>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      const err = badRequest('Validation failed', result.error.issues);
      res.status(400).json({ error: err });
      return;
    }
    req.body = result.data;
    next();
  };
}

export function validateQuery<T>(schema: ZodType<T>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      res.status(400).json({ error: badRequest('Invalid query parameters') });
      return;
    }
    (req as any).validatedQuery = result.data;
    next();
  };
}

// Request ID + timing
export function requestLogger(req: Request, res: Response, next: NextFunction): void {
  const id = Math.random().toString(36).slice(2, 9);
  const start = Date.now();
  req.requestId = id;
  res.setHeader('X-Request-Id', id);
  res.on('finish', () => {
    console.log(`${req.method} ${req.path} ${res.statusCode} ${Date.now() - start}ms [${id}]`);
  });
  next();
}

// Global error handler
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction): void {
  console.error(`[ERROR] ${req.method} ${req.path}:`, err.message);
  res.status(500).json({ error: serverError('Internal server error') });
}
```

---

## Step 6: Typed Service Layer

```typescript
// src/services/user.service.ts
import { Result, ok, err, notFound, badRequest, AppError } from '../result';
import { User, CreateUserDto, UpdateUserDto } from '../schemas/user';

export class UserService {
  private users = new Map<number, User>();
  private nextId = 1;

  async findAll(): Promise<Result<User[]>> {
    return ok(Array.from(this.users.values()));
  }

  async findById(id: number): Promise<Result<User, AppError>> {
    const user = this.users.get(id);
    if (!user) return err(notFound(`User ${id} not found`));
    return ok(user);
  }

  async create(data: CreateUserDto): Promise<Result<User, AppError>> {
    // Check duplicate email
    const exists = Array.from(this.users.values())
      .some(u => u.email === data.email);
    if (exists) return err(badRequest(`Email ${data.email} already registered`));

    const user: User = {
      ...data,
      id: this.nextId++,
      createdAt: new Date().toISOString(),
    };
    this.users.set(user.id, user);
    return ok(user);
  }

  async update(id: number, data: UpdateUserDto): Promise<Result<User, AppError>> {
    const existing = this.users.get(id);
    if (!existing) return err(notFound(`User ${id} not found`));
    const updated: User = { ...existing, ...data };
    this.users.set(id, updated);
    return ok(updated);
  }

  async delete(id: number): Promise<Result<void, AppError>> {
    if (!this.users.has(id)) return err(notFound(`User ${id} not found`));
    this.users.delete(id);
    return ok(undefined);
  }
}
```

---

## Step 7: Typed Router

```typescript
// src/routes/users.ts
import { Router, Request, Response } from 'express';
import { UserService } from '../services/user.service';
import { CreateUserSchema, UpdateUserSchema } from '../schemas/user';
import { validateBody } from '../middleware';
import { isOk } from '../result';

const router = Router();
const service = new UserService();

router.get('/', async (req: Request, res: Response): Promise<void> => {
  const result = await service.findAll();
  if (isOk(result)) res.json({ data: result.value });
  else res.status(500).json({ error: result.error });
});

router.get('/:id', async (req: Request, res: Response): Promise<void> => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) {
    res.status(400).json({ error: 'Invalid ID' });
    return;
  }
  const result = await service.findById(id);
  if (isOk(result)) res.json({ data: result.value });
  else res.status(result.error.statusCode).json({ error: result.error });
});

router.post('/', validateBody(CreateUserSchema), async (req: Request, res: Response): Promise<void> => {
  const result = await service.create(req.body);
  if (isOk(result)) res.status(201).json({ data: result.value });
  else res.status(result.error.statusCode).json({ error: result.error });
});

router.patch('/:id', validateBody(UpdateUserSchema), async (req: Request, res: Response): Promise<void> => {
  const id = Number(req.params.id);
  const result = await service.update(id, req.body);
  if (isOk(result)) res.json({ data: result.value });
  else res.status(result.error.statusCode).json({ error: result.error });
});

router.delete('/:id', async (req: Request, res: Response): Promise<void> => {
  const id = Number(req.params.id);
  const result = await service.delete(id);
  if (isOk(result)) res.status(204).send();
  else res.status(result.error.statusCode).json({ error: result.error });
});

export { router as userRouter };
```

---

## Step 8: Capstone — Runnable API

```typescript
// Save as lab15-capstone.ts
import express from 'express';
import { z } from 'zod';
import http from 'http';

type Ok<T>  = { ok: true; value: T };
type Err<E> = { ok: false; error: E };
type Result<T, E = string> = Ok<T> | Err<E>;
const ok  = <T>(v: T): Ok<T>   => ({ ok: true, value: v });
const err = <E>(e: E): Err<E>  => ({ ok: false, error: e });

const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user'),
});
type User = z.infer<typeof CreateUserSchema> & { id: number };

const app = express();
app.use(express.json());

const users: User[] = [];

app.post('/users', (req, res) => {
  const r = CreateUserSchema.safeParse(req.body);
  if (!r.success) { res.status(400).json(err('Invalid')); return; }
  const user: User = { ...r.data, id: users.length + 1 };
  users.push(user);
  res.status(201).json(ok(user));
});

app.get('/users', (_, res) => res.json(ok(users)));

const server = http.createServer(app);
server.listen(0, async () => {
  const port = (server.address() as { port: number }).port;
  console.log('Server started on port', port);

  // Create user
  await new Promise<void>(resolve => {
    const req = http.request({
      hostname: 'localhost', port, method: 'POST', path: '/users',
      headers: { 'Content-Type': 'application/json' }
    }, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => {
        const result = JSON.parse(body);
        console.log('Created:', result.value.name, result.value.role, result.ok);
        resolve();
      });
    });
    req.write(JSON.stringify({ name: 'Alice', email: 'alice@example.com' }));
    req.end();
  });

  // List users
  await new Promise<void>(resolve => {
    http.get(`http://localhost:${port}/users`, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => {
        const result = JSON.parse(body);
        console.log('Users count:', result.value.length);
        resolve();
      });
    });
  });

  server.close(() => console.log('Capstone API OK'));
});
```

Run:
```bash
ts-node -P tsconfig.json lab15-capstone.ts
```

📸 **Verified Output:**
```
Server started on port [dynamic]
Created: Alice user true
Users count: 1
Capstone API OK
```

---

## Summary — Full Stack TypeScript Patterns

| Layer | Pattern | Library |
|-------|---------|---------|
| Environment | Zod schema validation | `zod` |
| Error handling | `Result<T, E>` discriminated union | Pure TS |
| Request validation | `validateBody(ZodSchema)` middleware | `zod` + `express` |
| Service layer | Returns `Result<T, AppError>` | Pure TS |
| Router | Typed params, body, response | `@types/express` |
| Config | `as const` + `z.infer<>` | `zod` |
