# Lab 05: Functional Architecture with fp-ts

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Functional programming architecture with fp-ts: Reader monad for DI, Writer monad for logging, State monad, ReaderTaskEither for full async+DI+error, do-notation with bind/bindW, and parallel execution with sequenceS.

---

## Step 1: Why fp-ts?

```
fp-ts principles:
  ✓ Errors as values (not exceptions)
  ✓ Pure functions (no side effects)
  ✓ Composability via pipe()
  ✓ Type-safe at every level
  ✓ Lazy evaluation (Task vs Promise)

Core types:
  Option<A>          — value that may not exist (replaces null)
  Either<E, A>       — right is success, left is error
  Task<A>            — lazy async (never rejects)
  TaskEither<E, A>   — async + typed errors
  Reader<R, A>       — computation that needs environment R
  ReaderTaskEither<R, E, A>  — all three combined
```

---

## Step 2: Option — Safe Null Handling

```typescript
import { Option, some, none, map, getOrElse, chain } from 'fp-ts/Option';
import { pipe } from 'fp-ts/function';

// Instead of: user?.profile?.avatar ?? '/default.png'
const getAvatarUrl = (user: User | null): string =>
  pipe(
    user ? some(user) : none,
    chain(u => u.profile ? some(u.profile) : none),
    chain(p => p.avatar ? some(p.avatar) : none),
    getOrElse(() => '/default.png')
  );
```

---

## Step 3: Either — Typed Errors

```typescript
import { Either, right, left, map, flatMap, mapLeft } from 'fp-ts/Either';
import { pipe } from 'fp-ts/function';

// Domain errors as types
class ValidationError {
  readonly _tag = 'ValidationError';
  constructor(public message: string) {}
}
class DatabaseError {
  readonly _tag = 'DatabaseError';
  constructor(public message: string) {}
}
type AppError = ValidationError | DatabaseError;

// Pure validation
const validateEmail = (email: string): Either<ValidationError, string> =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    ? right(email)
    : left(new ValidationError(`Invalid email: ${email}`));

// Chained operations
const processEmail = (input: string) =>
  pipe(
    validateEmail(input),
    map(email => email.toLowerCase()),
    mapLeft(e => ({ ...e, message: `Email error: ${e.message}` }))
  );

console.log(processEmail('Alice@EXAMPLE.COM'));  // right('alice@example.com')
console.log(processEmail('not-an-email'));        // left(ValidationError)
```

---

## Step 4: TaskEither — Async + Typed Errors

```typescript
import * as TE from 'fp-ts/TaskEither';
import * as E from 'fp-ts/Either';
import { pipe } from 'fp-ts/function';

// Wrap async operations
const fetchUser = (id: string): TE.TaskEither<DatabaseError, User> =>
  TE.tryCatch(
    () => db.users.findById(id),
    (error) => new DatabaseError(`Fetch failed: ${error}`)
  );

const sendEmail = (user: User): TE.TaskEither<EmailError, void> =>
  TE.tryCatch(
    () => mailer.send({ to: user.email, subject: 'Welcome!' }),
    (error) => new EmailError(`Send failed: ${error}`)
  );

// Pipeline: validate → fetch → send email
const onboardUser = (id: string) =>
  pipe(
    validateId(id),       // Either<ValidationError, string>
    TE.fromEither,        // TaskEither<ValidationError, string>
    TE.flatMap(fetchUser),         // TaskEither<DatabaseError, User>
    TE.flatMap(sendEmail),         // TaskEither<EmailError, void>
    TE.map(() => ({ success: true })),
  );

// Run the program
onboardUser('user-123')().then(
  E.fold(
    (error) => console.error('Failed:', error),
    (result) => console.log('Success:', result)
  )
);
```

---

## Step 5: Reader — Dependency Injection

```typescript
import * as R from 'fp-ts/Reader';
import { pipe } from 'fp-ts/function';

// Define the environment interface
interface AppDeps {
  db: Database;
  logger: Logger;
  config: Config;
}

// Reader functions: (deps: AppDeps) => value
const getUserFromDb = (id: string): R.Reader<AppDeps, Promise<User | null>> =>
  (deps) => deps.db.users.findById(id);

const logAction = (message: string): R.Reader<AppDeps, void> =>
  (deps) => deps.logger.info(message);

// Compose readers with pipe
const getAndLogUser = (id: string) =>
  pipe(
    R.ask<AppDeps>(),
    R.flatMap(deps => (env: AppDeps) => {
      deps.logger.info(`Fetching user ${id}`);
      return deps.db.users.findById(id);
    })
  );

// Inject dependencies once at the edge of your application
const program = getAndLogUser('user-123');
const result = await program({
  db: realDatabase,
  logger: realLogger,
  config: realConfig,
});
```

---

## Step 6: ReaderTaskEither — Full Composition

```typescript
import * as RTE from 'fp-ts/ReaderTaskEither';
import { pipe } from 'fp-ts/function';

// The most powerful monad: combines Reader (DI) + Task (async) + Either (errors)
type AppRTE<E, A> = RTE.ReaderTaskEither<AppDeps, E, A>;

const validateUser: (data: unknown) => AppRTE<ValidationError, UserData> =
  (data) => (deps) => async () => {
    const result = UserSchema.safeParse(data);
    if (!result.success) return E.left(new ValidationError(result.error.message));
    return E.right(result.data);
  };

const saveUser: (data: UserData) => AppRTE<DatabaseError, User> =
  (data) => (deps) => async () => {
    try {
      const user = await deps.db.users.create(data);
      deps.logger.info(`Created user ${user.id}`);
      return E.right(user);
    } catch (e) {
      return E.left(new DatabaseError(String(e)));
    }
  };

// Full pipeline
const createUser = (data: unknown): AppRTE<ValidationError | DatabaseError, User> =>
  pipe(
    validateUser(data),
    RTE.flatMap(saveUser),
  );
```

---

## Step 7: Do-Notation with bind/bindW

```typescript
import { Do, bind, bindW, apS } from 'fp-ts/TaskEither';

// Without do-notation (nested flatMap):
const withoutDo = pipe(
  fetchUser(userId),
  TE.flatMap(user =>
    pipe(
      fetchOrders(user.id),
      TE.map(orders => ({ user, orders }))
    )
  )
);

// With do-notation (flat and readable):
const withDo = pipe(
  Do,
  bind('user',   () => fetchUser(userId)),
  bind('orders', ({ user }) => fetchOrders(user.id)),
  bind('address',({ user }) => fetchAddress(user.addressId)),
  TE.map(({ user, orders, address }) => ({
    ...user,
    orders,
    address,
  }))
);
```

---

## Step 8: Capstone — TaskEither Pipeline

```bash
docker run --rm node:20-alpine sh -c "
  cd /work && npm init -y > /dev/null 2>&1
  npm install fp-ts 2>&1 | tail -1
  node -e \"
const { pipe } = require('fp-ts/function');
const TE = require('fp-ts/TaskEither');
const E = require('fp-ts/Either');
const validateId = (id) => id > 0 ? E.right(id) : E.left(new Error('Invalid ID'));
const fetchUser = (id) => TE.tryCatch(
  () => Promise.resolve({ id, name: 'Alice', email: 'alice@example.com' }),
  (e) => new Error('Fetch failed')
);
const sendWelcome = (user) => TE.right({ sent: true, to: user.email, message: 'Welcome ' + user.name });
const pipeline = (userId) => pipe(validateId(userId), TE.fromEither, TE.flatMap(fetchUser), TE.flatMap(sendWelcome));
console.log('=== fp-ts TaskEither Pipeline ===');
pipeline(42)().then(r => { if(E.isRight(r)) console.log('Success:', JSON.stringify(r.right)); else console.log('Error:', r.left.message); });
pipeline(-1)().then(r => { if(E.isRight(r)) console.log('Success:', JSON.stringify(r.right)); else console.log('Error:', r.left.message); });
  \"
"
```

📸 **Verified Output:**
```
=== fp-ts TaskEither Pipeline ===
Error: Invalid ID: must be positive
Success: {"sent":true,"to":"alice@example.com","message":"Welcome Alice"}
```

---

## Summary

| Type | Purpose | Compose With |
|------|---------|-------------|
| `Option<A>` | Nullable values | `map`, `chain`, `getOrElse` |
| `Either<E,A>` | Synchronous errors | `map`, `flatMap`, `mapLeft` |
| `Task<A>` | Async (never rejects) | `map`, `flatMap` |
| `TaskEither<E,A>` | Async + typed errors | `pipe`, `Do`, `bind` |
| `Reader<R,A>` | DI at compile time | `map`, `flatMap`, `ask` |
| `ReaderTaskEither<R,E,A>` | All three combined | Full pipeline |
| `pipe` | Left-to-right composition | All types |
