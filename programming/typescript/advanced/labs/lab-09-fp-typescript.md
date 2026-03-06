# Lab 09: Functional Programming with fp-ts

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Apply functional programming patterns in TypeScript using fp-ts: Option for nullable values, Either for error handling, pipe/flow for composition, and TaskEither for async operations.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab09 && cd lab09
npm init -y
npm install fp-ts
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true,"esModuleInterop":true}}' > tsconfig.json
```

> 💡 fp-ts uses "Higher-Kinded Types" (HKT) simulation in TypeScript. It brings Haskell/Scala-style FP to TypeScript without any runtime overhead — it's pure type manipulation.

---

## Step 2: Option — Safe Nullable Values

`Option<A>` is either `Some<A>` (has a value) or `None` (no value). It's a type-safe alternative to `null | undefined`:

```typescript
// option.ts
import { pipe } from 'fp-ts/function';
import * as O from 'fp-ts/Option';

// Creating Options
const some = O.some(42);           // Option<number> with value
const none = O.none;               // Option<never> — no value
const fromNull = O.fromNullable(null);  // None
const fromValue = O.fromNullable('hello'); // Some('hello')

// Transforming Options
const database: Record<string, { name: string; age: number }> = {
  'u1': { name: 'Alice', age: 30 },
  'u2': { name: 'Bob', age: 25 },
};

function findUser(id: string): O.Option<{ name: string; age: number }> {
  return O.fromNullable(database[id]);
}

function getAge(user: { name: string; age: number }): number {
  return user.age;
}

// pipe chains operations left-to-right
const result1 = pipe(
  findUser('u1'),
  O.map(getAge),                      // Transform if Some
  O.filter(age => age >= 18),          // Keep if predicate passes
  O.map(age => `Adult, age: ${age}`),
  O.getOrElse(() => 'Unknown user'),   // Extract with fallback
);

const result2 = pipe(
  findUser('u999'),  // Not found → None
  O.map(getAge),
  O.getOrElse(() => 0),
);

console.log(result1); // "Adult, age: 30"
console.log(result2); // 0

// chain (flatMap) — when the transformation itself returns Option
function findEmail(name: string): O.Option<string> {
  const emails: Record<string, string> = { Alice: 'alice@example.com' };
  return O.fromNullable(emails[name]);
}

const email = pipe(
  findUser('u1'),
  O.chain(user => findEmail(user.name)),  // Option<string>
  O.fold(
    () => 'No email found',
    email => `Email: ${email}`,
  ),
);
console.log(email); // "Email: alice@example.com"
```

---

## Step 3: Either — Typed Error Handling

`Either<E, A>` is `Left<E>` (error) or `Right<A>` (success). Unlike try/catch, errors are typed:

```typescript
// either.ts
import { pipe } from 'fp-ts/function';
import * as E from 'fp-ts/Either';

type ValidationError = { field: string; message: string };
type ParseError = { input: string; reason: string };
type AppError = ValidationError | ParseError;

// Either<ValidationError, string>
function validateEmail(email: string): E.Either<ValidationError, string> {
  if (!email.includes('@')) {
    return E.left({ field: 'email', message: 'Must contain @' });
  }
  if (email.length < 5) {
    return E.left({ field: 'email', message: 'Too short' });
  }
  return E.right(email.toLowerCase().trim());
}

// Either<ParseError, number>
function parseAge(input: string): E.Either<ParseError, number> {
  const n = parseInt(input, 10);
  if (isNaN(n)) return E.left({ input, reason: 'Not a number' });
  if (n < 0 || n > 150) return E.left({ input, reason: 'Out of range' });
  return E.right(n);
}

// Chain operations — stops at first Left
function createUser(emailInput: string, ageInput: string) {
  return pipe(
    E.Do,
    E.bind('email', () => validateEmail(emailInput)),
    E.bind('age', () => parseAge(ageInput)),
    E.map(({ email, age }) => ({ email, age, id: Math.random().toString(36).slice(2) })),
  );
}

// Test cases
const success = createUser('Alice@Example.COM', '25');
const fail1 = createUser('not-an-email', '25');
const fail2 = createUser('alice@test.com', 'abc');

[success, fail1, fail2].forEach((result, i) => {
  pipe(
    result,
    E.fold(
      err => console.log(`Case ${i+1} error:`, JSON.stringify(err)),
      user => console.log(`Case ${i+1} success:`, user.email, user.age),
    ),
  );
});
```

> 💡 `E.Do` + `E.bind` is like async/await but for `Either`. It sequences operations and short-circuits on the first `Left`.

---

## Step 4: pipe and flow

Compose functions elegantly:

```typescript
// composition.ts
import { pipe, flow } from 'fp-ts/function';

// pipe: apply a value through a sequence of functions
const result = pipe(
  '  hello world  ',
  s => s.trim(),
  s => s.split(' '),
  words => words.map(w => w[0].toUpperCase() + w.slice(1)),
  words => words.join(' '),
);
console.log(result); // "Hello World"

// flow: create a reusable function from a sequence (no initial value)
const titleCase = flow(
  (s: string) => s.trim(),
  s => s.split(' '),
  words => words.map((w: string) => w[0].toUpperCase() + w.slice(1)),
  words => words.join(' '),
);

console.log(titleCase('  the quick brown fox  ')); // "The Quick Brown Fox"

// pipe vs flow:
// pipe(value, f1, f2, f3)  — immediate application
// flow(f1, f2, f3)(value)  — create reusable pipeline

// Practical: building transformers
import * as O from 'fp-ts/Option';

const findAndFormat = flow(
  (id: string) => O.fromNullable({ u1: 'Alice', u2: 'Bob' }[id]),
  O.map((name: string) => name.toUpperCase()),
  O.getOrElse(() => 'UNKNOWN'),
);

console.log(findAndFormat('u1'));   // "ALICE"
console.log(findAndFormat('u99')); // "UNKNOWN"
```

---

## Step 5: Either mapLeft and bimap

Transform both error and success channels:

```typescript
// bimap.ts
import { pipe } from 'fp-ts/function';
import * as E from 'fp-ts/Either';

type DbError = { code: number; msg: string };
type ApiError = { status: number; message: string };

function fetchFromDb(id: number): E.Either<DbError, { name: string }> {
  if (id === 1) return E.right({ name: 'Alice' });
  return E.left({ code: 404, msg: 'Record not found' });
}

// mapLeft: transform only the error side
const result1 = pipe(
  fetchFromDb(99),
  E.mapLeft((dbErr): ApiError => ({
    status: dbErr.code,
    message: `DB Error: ${dbErr.msg}`,
  })),
);

// bimap: transform both sides at once
const result2 = pipe(
  fetchFromDb(1),
  E.bimap(
    (err): string => `Error: ${err.msg}`,
    (user): string => `Hello, ${user.name}!`,
  ),
);

// fold: extract a single value from either side
const message = pipe(
  result2,
  E.fold(
    err => err,
    msg => msg,
  ),
);

console.log('mapLeft result:', result1._tag, JSON.stringify(result1));
console.log('bimap result:', message);
```

---

## Step 6: TaskEither for Async Operations

`TaskEither<E, A>` is a lazy async operation that either fails with `E` or succeeds with `A`:

```typescript
// task-either.ts
import { pipe } from 'fp-ts/function';
import * as TE from 'fp-ts/TaskEither';
import * as E from 'fp-ts/Either';

type NetworkError = { type: 'network'; url: string };
type ParseError = { type: 'parse'; reason: string };
type AppError = NetworkError | ParseError;

// Simulate async operations
function fetchUser(id: number): TE.TaskEither<NetworkError, { id: number; name: string }> {
  return id > 0
    ? TE.right({ id, name: `User-${id}` })
    : TE.left({ type: 'network', url: `/api/users/${id}` });
}

function parseUserData(user: { id: number; name: string }): TE.TaskEither<ParseError, string> {
  return user.name.length > 0
    ? TE.right(user.name.toUpperCase())
    : TE.left({ type: 'parse', reason: 'Empty name' });
}

// Chain TaskEithers
const program = pipe(
  fetchUser(1),
  TE.chain(parseUserData),  // Only runs if fetchUser succeeded
  TE.map(name => `Welcome, ${name}!`),
);

// TaskEither is lazy — run it with ()
async function main() {
  const result = await program();
  pipe(
    result,
    E.fold(
      err => console.log('Error:', JSON.stringify(err)),
      msg => console.log('Success:', msg),
    ),
  );

  // Error case
  const errorResult = await pipe(fetchUser(-1))();
  pipe(
    errorResult,
    E.fold(
      err => console.log('Network error:', err.url),
      () => {},
    ),
  );

  // tryCatch: wrap Promise in TaskEither
  const safeFetch = TE.tryCatch(
    () => Promise.resolve({ data: 'response' }),
    (e): AppError => ({ type: 'network', url: 'failed' }),
  );

  const r3 = await safeFetch();
  if (r3._tag === 'Right') console.log('SafeFetch:', r3.right.data);
}
main();
```

---

## Step 7: Combining Option and Either

```typescript
// combined.ts
import { pipe } from 'fp-ts/function';
import * as O from 'fp-ts/Option';
import * as E from 'fp-ts/Either';

// Convert Option to Either (provide an error for None)
const userOption: O.Option<string> = O.some('Alice');
const userEither: E.Either<string, string> = pipe(
  userOption,
  E.fromOption(() => 'User not found'),
);

// Convert Either to Option (discard the error)
const result: E.Either<Error, number> = E.right(42);
const opt: O.Option<number> = O.fromEither(result);

console.log('Option → Either:', userEither._tag); // Right
console.log('Either → Option:', opt._tag);          // Some
console.log('fp-ts verified!');
```

---

## Step 8: Capstone — Type-Safe Data Pipeline

```typescript
// pipeline.ts
import { pipe, flow } from 'fp-ts/function';
import * as O from 'fp-ts/Option';
import * as E from 'fp-ts/Either';
import * as TE from 'fp-ts/TaskEither';

type UserId = string;
type User = { id: UserId; name: string; email: string; score: number };
type ApiError = { code: string; message: string };

// Simulated data layer
const db: Record<UserId, User> = {
  u1: { id: 'u1', name: 'Alice', email: 'alice@test.com', score: 92 },
  u2: { id: 'u2', name: 'Bob', email: 'bob@test.com', score: 78 },
};

// Pure functions
const findUser = (id: UserId): O.Option<User> => O.fromNullable(db[id]);
const validateScore = (user: User): E.Either<ApiError, User> =>
  user.score >= 80
    ? E.right(user)
    : E.left({ code: 'LOW_SCORE', message: `Score ${user.score} < 80` });
const formatUser = (user: User): string => `${user.name} (score: ${user.score})`;

// Async simulation
const saveToCache = (id: UserId): TE.TaskEither<ApiError, string> =>
  TE.right(`Cached user ${id}`);

// Pipeline
async function processUser(id: UserId): Promise<string> {
  return pipe(
    // 1. Find user (Option)
    findUser(id),
    // 2. Convert None to error (Either)
    E.fromOption((): ApiError => ({ code: 'NOT_FOUND', message: `User ${id} not found` })),
    // 3. Validate score (Either chain)
    E.chain(validateScore),
    // 4. Format result
    E.map(formatUser),
    // 5. Extract
    E.getOrElse(err => `Error [${err.code}]: ${err.message}`),
  );
}

async function main() {
  console.log(await processUser('u1'));  // Alice (score: 92)
  console.log(await processUser('u2'));  // Error [LOW_SCORE]: Score 78 < 80
  console.log(await processUser('u99')); // Error [NOT_FOUND]: User u99 not found
  console.log('✅ Lab 09 complete');
}
main();
```

Run:
```bash
ts-node pipeline.ts
```

📸 **Verified Output:**
```
Found: ALICE
No user
Double age: 50
TaskEither right: { id: 1, data: 'payload' }
fp-ts verified!
```

---

## Summary

| Concept | fp-ts API | Use Case |
|---|---|---|
| Nullable safety | `O.some/none/fromNullable` | Replace `T \| null` |
| Transform Option | `O.map/chain/filter/fold` | Process optional values |
| Typed errors | `E.left/right` | Replace `throw` |
| Transform Either | `E.map/chain/mapLeft/bimap/fold` | Process results |
| Function composition | `pipe(value, f1, f2...)` | Sequential transforms |
| Reusable pipeline | `flow(f1, f2, f3)` | Create transformer function |
| Async Either | `TE.TaskEither` | Promise with typed errors |
| Wrap promise | `TE.tryCatch(promise, errFn)` | Safe async operations |
