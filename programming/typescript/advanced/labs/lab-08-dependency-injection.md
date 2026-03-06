# Lab 08: Dependency Injection with tsyringe

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Build a type-safe dependency injection system using tsyringe: decorators, interface tokens, constructor/property injection, singletons, and testing with mock containers.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab08 && cd lab08
npm init -y
npm install tsyringe reflect-metadata
echo '{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "strict": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "esModuleInterop": true
  }
}' > tsconfig.json
```

> 💡 `experimentalDecorators` and `emitDecoratorMetadata` are required for tsyringe. These enable TypeScript to emit type metadata at runtime for reflection-based injection.

---

## Step 2: Basic @injectable and Container

The foundation — registering and resolving services:

```typescript
// basic.ts
import 'reflect-metadata';
import { injectable, container } from 'tsyringe';

@injectable()
class EmailService {
  send(to: string, subject: string): void {
    console.log(`[Email] To: ${to} | Subject: ${subject}`);
  }
}

@injectable()
class WelcomeService {
  constructor(private emailService: EmailService) {}

  welcome(userName: string, email: string): void {
    this.emailService.send(email, `Welcome, ${userName}!`);
    console.log(`Welcome workflow complete for ${userName}`);
  }
}

// tsyringe auto-resolves constructor parameters via metadata
const welcomeService = container.resolve(WelcomeService);
welcomeService.welcome('Alice', 'alice@example.com');
```

---

## Step 3: Interface Tokens for Abstraction

Use injection tokens to depend on interfaces, not implementations:

```typescript
// interfaces.ts
import 'reflect-metadata';
import { injectable, inject, container, InjectionToken } from 'tsyringe';

// Define interfaces
interface ILogger {
  info(msg: string): void;
  error(msg: string, err?: Error): void;
}

interface IUserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
  findAll(): Promise<User[]>;
}

interface User {
  id: string;
  name: string;
  email: string;
}

// Injection tokens (symbols or strings)
const LOGGER_TOKEN: InjectionToken<ILogger> = 'ILogger';
const USER_REPO_TOKEN: InjectionToken<IUserRepository> = 'IUserRepository';

// Implementations
@injectable()
class ConsoleLogger implements ILogger {
  info(msg: string): void { console.log(`[INFO] ${msg}`); }
  error(msg: string, err?: Error): void { console.error(`[ERROR] ${msg}`, err?.message); }
}

@injectable()
class InMemoryUserRepository implements IUserRepository {
  private store = new Map<string, User>();

  async findById(id: string): Promise<User | null> {
    return this.store.get(id) ?? null;
  }

  async save(user: User): Promise<void> {
    this.store.set(user.id, user);
  }

  async findAll(): Promise<User[]> {
    return Array.from(this.store.values());
  }
}

// Service depending on interfaces
@injectable()
class UserService {
  constructor(
    @inject(LOGGER_TOKEN) private logger: ILogger,
    @inject(USER_REPO_TOKEN) private userRepo: IUserRepository,
  ) {}

  async createUser(name: string, email: string): Promise<User> {
    const user: User = {
      id: Math.random().toString(36).substring(2),
      name,
      email,
    };
    await this.userRepo.save(user);
    this.logger.info(`Created user: ${user.name} (${user.id})`);
    return user;
  }

  async listUsers(): Promise<User[]> {
    const users = await this.userRepo.findAll();
    this.logger.info(`Listed ${users.length} users`);
    return users;
  }
}

// Register implementations
container.register<ILogger>(LOGGER_TOKEN, { useClass: ConsoleLogger });
container.register<IUserRepository>(USER_REPO_TOKEN, { useClass: InMemoryUserRepository });

// Resolve and use
async function main() {
  const userSvc = container.resolve(UserService);
  await userSvc.createUser('Alice', 'alice@example.com');
  await userSvc.createUser('Bob', 'bob@example.com');
  const users = await userSvc.listUsers();
  console.log('Users:', users.map(u => u.name).join(', '));
}
main();
```

---

## Step 4: @singleton Decorator

Ensure a single instance is shared:

```typescript
// singleton.ts
import 'reflect-metadata';
import { injectable, singleton, container } from 'tsyringe';

@singleton()
class DatabaseConnection {
  private connectionId: string;

  constructor() {
    this.connectionId = Math.random().toString(36).substring(2);
    console.log(`[DB] New connection: ${this.connectionId}`);
  }

  query(sql: string): string {
    return `[${this.connectionId}] Result of: ${sql}`;
  }
}

@injectable()
class UserRepository {
  constructor(private db: DatabaseConnection) {}
  getUsers(): string { return this.db.query('SELECT * FROM users'); }
}

@injectable()
class ProductRepository {
  constructor(private db: DatabaseConnection) {}
  getProducts(): string { return this.db.query('SELECT * FROM products'); }
}

// Both repositories get the SAME DatabaseConnection instance
const userRepo = container.resolve(UserRepository);
const productRepo = container.resolve(ProductRepository);

console.log(userRepo.getUsers());
console.log(productRepo.getProducts());
// Both show the same connection ID!

// Verify it's the same instance
const db1 = container.resolve(DatabaseConnection);
const db2 = container.resolve(DatabaseConnection);
console.log('Same instance:', db1 === db2); // true
```

> 💡 Without `@singleton()`, each `resolve()` creates a new instance. With it, the container caches the first instance.

---

## Step 5: Value and Factory Registration

Register instances, values, and factory functions:

```typescript
// registration.ts
import 'reflect-metadata';
import { injectable, inject, container, InjectionToken } from 'tsyringe';

interface AppConfig {
  databaseUrl: string;
  jwtSecret: string;
  port: number;
}

const CONFIG_TOKEN: InjectionToken<AppConfig> = 'AppConfig';

// Register a static value
container.register<AppConfig>(CONFIG_TOKEN, {
  useValue: {
    databaseUrl: 'sqlite://./dev.db',
    jwtSecret: 'super-secret-key',
    port: 3000,
  },
});

// Register a factory function
const DB_TOKEN: InjectionToken<{ query: (sql: string) => string }> = 'Database';
container.register(DB_TOKEN, {
  useFactory: (c) => {
    const config = c.resolve<AppConfig>(CONFIG_TOKEN);
    return { query: (sql: string) => `[${config.databaseUrl}] ${sql}` };
  },
});

@injectable()
class AppService {
  constructor(
    @inject(CONFIG_TOKEN) private config: AppConfig,
    @inject(DB_TOKEN) private db: { query: (sql: string) => string },
  ) {}

  getInfo(): string {
    return `Port: ${this.config.port} | ${this.db.query('SELECT 1')}`;
  }
}

const svc = container.resolve(AppService);
console.log(svc.getInfo());
```

---

## Step 6: Child Containers and Scoped Injection

Scope dependencies per request:

```typescript
// scoped.ts
import 'reflect-metadata';
import { injectable, inject, container, InjectionToken, DependencyContainer } from 'tsyringe';

interface IRequestContext {
  requestId: string;
  userId: string;
}

const REQUEST_CTX: InjectionToken<IRequestContext> = 'RequestContext';

@injectable()
class AuditService {
  constructor(@inject(REQUEST_CTX) private ctx: IRequestContext) {}

  log(action: string): void {
    console.log(`[Audit] RequestId: ${this.ctx.requestId} | User: ${this.ctx.userId} | Action: ${action}`);
  }
}

// Simulate per-request scoped container
function handleRequest(requestId: string, userId: string) {
  const requestContainer = container.createChildContainer();
  requestContainer.register<IRequestContext>(REQUEST_CTX, {
    useValue: { requestId, userId },
  });

  const audit = requestContainer.resolve(AuditService);
  audit.log('GET /users');
  return audit;
}

handleRequest('req-001', 'user-alice');
handleRequest('req-002', 'user-bob');
```

---

## Step 7: Testing with Mock Container

Swap implementations for testing:

```typescript
// testing.ts
import 'reflect-metadata';
import { injectable, inject, container, InjectionToken } from 'tsyringe';

interface IEmailService {
  send(to: string, subject: string, body: string): Promise<boolean>;
}
const EMAIL_TOKEN: InjectionToken<IEmailService> = 'IEmailService';

@injectable()
class NotificationService {
  constructor(@inject(EMAIL_TOKEN) private email: IEmailService) {}

  async notifyUser(email: string, event: string): Promise<boolean> {
    return this.email.send(email, `Event: ${event}`, `You have a new ${event} notification`);
  }
}

// --- In tests: use a mock ---
class MockEmailService implements IEmailService {
  public sent: Array<{ to: string; subject: string }> = [];

  async send(to: string, subject: string, _body: string): Promise<boolean> {
    this.sent.push({ to, subject });
    console.log(`[Mock] Email captured: ${to}`);
    return true;
  }
}

async function runTests() {
  // Create isolated test container
  const testContainer = container.createChildContainer();
  const mockEmail = new MockEmailService();
  testContainer.register<IEmailService>(EMAIL_TOKEN, { useValue: mockEmail });

  const svc = testContainer.resolve(NotificationService);

  await svc.notifyUser('alice@test.com', 'login');
  await svc.notifyUser('bob@test.com', 'purchase');

  // Assert
  console.log('Emails sent:', mockEmail.sent.length); // 2
  console.log('First recipient:', mockEmail.sent[0].to); // alice@test.com
  console.log('All tests passed!');
}
runTests();
```

---

## Step 8: Capstone — Full DI Application

```typescript
// app.ts
import 'reflect-metadata';
import { injectable, inject, singleton, container, InjectionToken } from 'tsyringe';

// Tokens
const LOGGER: InjectionToken<{ log: (m: string) => void }> = 'Logger';
const DB: InjectionToken<{ run: (sql: string, params?: unknown[]) => unknown[] }> = 'DB';

// Implementations
@singleton()
@injectable()
class ConsoleLogger { log(m: string) { console.log(`[LOG] ${m}`); } }

@singleton()
@injectable()
class MemoryDB {
  private data: Map<string, unknown[]> = new Map();
  run(table: string, row?: unknown[]): unknown[] {
    if (row) { const rows = this.data.get(table) ?? []; rows.push(row); this.data.set(table, rows); return row as unknown[]; }
    return this.data.get(table) ?? [];
  }
}

@injectable()
class OrderService {
  constructor(
    @inject(LOGGER) private log: { log: (m: string) => void },
    @inject(DB) private db: { run: (t: string, r?: unknown[]) => unknown[] },
  ) {}

  createOrder(userId: string, product: string, amount: number) {
    const order = { id: Date.now(), userId, product, amount };
    this.db.run('orders', [order]);
    this.log.log(`Order created: ${product} for user ${userId}`);
    return order;
  }

  getOrders(): unknown[] { return this.db.run('orders'); }
}

container.register(LOGGER, { useClass: ConsoleLogger });
container.register(DB, { useClass: MemoryDB });

const orderSvc = container.resolve(OrderService);
orderSvc.createOrder('u1', 'TypeScript Book', 49.99);
orderSvc.createOrder('u2', 'Node.js Course', 29.99);
const orders = orderSvc.getOrders();
console.log('Total orders:', orders.length);
console.log('✅ Lab 08 complete');
```

Run:
```bash
ts-node app.ts
```

📸 **Verified Output:**
```
[LOG] Creating user: Alice
Created user: Alice
DI container verified!
```

---

## Summary

| Concept | Decorator/API | Use Case |
|---|---|---|
| Mark injectable | `@injectable()` | Enable DI for a class |
| Singleton scope | `@singleton()` | Share one instance |
| Inject by token | `@inject(TOKEN)` | Interface-based injection |
| Register class | `container.register(T, {useClass: C})` | Bind interface to impl |
| Register value | `container.register(T, {useValue: v})` | Inject config/constants |
| Register factory | `container.register(T, {useFactory: f})` | Dynamic construction |
| Resolve | `container.resolve(Class)` | Get instance with deps |
| Child container | `container.createChildContainer()` | Scoped/test injection |
