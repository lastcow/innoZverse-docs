# Lab 10: Type Guards & Assertions

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

User-defined type guards (`is`), assertion functions (`asserts x is T`), the `satisfies` operator, branded/nominal types, opaque types.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab10 && cd /lab10
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

## Step 2: User-Defined Type Guards (is)

```typescript
// Type guard: narrows type in calling scope
function isString(x: unknown): x is string {
  return typeof x === 'string';
}

function isNumber(x: unknown): x is number {
  return typeof x === 'number';
}

type Cat = { kind: 'cat'; meow(): void };
type Dog = { kind: 'dog'; bark(): void };
type Pet = Cat | Dog;

function isCat(pet: Pet): pet is Cat { return pet.kind === 'cat'; }
function isDog(pet: Pet): pet is Dog { return pet.kind === 'dog'; }

const val: unknown = 'hello';
if (isString(val)) console.log(val.toUpperCase()); // TypeScript knows it's string

const pet: Pet = { kind: 'cat', meow() { console.log('Meow!'); } };
if (isCat(pet)) pet.meow();  // Safe: TypeScript narrows to Cat

// Array type guard
function isStringArray(arr: unknown): arr is string[] {
  return Array.isArray(arr) && arr.every(i => typeof i === 'string');
}
const arr: unknown = ['a', 'b', 'c'];
if (isStringArray(arr)) console.log(arr.join(', ')); // TypeScript: string[]
```

---

## Step 3: Generic Type Guards

```typescript
interface User { id: number; name: string; email: string }
interface Post { id: number; title: string; content: string }

// Generic type guard with required properties
function hasProperties<T extends object>(obj: unknown, ...props: (keyof T)[]): obj is T {
  if (typeof obj !== 'object' || obj === null) return false;
  return props.every(p => p in obj);
}

function isUser(obj: unknown): obj is User {
  return hasProperties<User>(obj, 'id', 'name', 'email');
}

function isPost(obj: unknown): obj is Post {
  return hasProperties<Post>(obj, 'id', 'title', 'content');
}

const data: unknown = { id: 1, name: 'Alice', email: 'alice@example.com' };
if (isUser(data)) {
  console.log(`User: ${data.name} <${data.email}>`);
}
```

---

## Step 4: Assertion Functions

```typescript
// Assertion functions throw if condition fails, narrow type if not
function assert(condition: unknown, msg?: string): asserts condition {
  if (!condition) throw new Error(msg ?? 'Assertion failed');
}

function assertIsString(val: unknown): asserts val is string {
  if (typeof val !== 'string') throw new TypeError(`Expected string, got ${typeof val}`);
}

function assertNonNull<T>(val: T, name?: string): asserts val is NonNullable<T> {
  if (val === null || val === undefined) {
    throw new Error(`${name ?? 'Value'} must not be null or undefined`);
  }
}

const config = { port: 3000, host: 'localhost' };
const port: unknown = config.port;
assertIsString(String(port));

let user: { name: string } | null = null;
try {
  assertNonNull(user, 'user');
} catch (e: any) {
  console.log(e.message);  // user must not be null or undefined
}

user = { name: 'Alice' };
assertNonNull(user, 'user');
console.log(user.name);  // TypeScript: user is { name: string }
```

---

## Step 5: The `satisfies` Operator

```typescript
// satisfies: validates type without widening
type RGB = [number, number, number];
type Color = RGB | string;
type Palette = Record<string, Color>;

// Without satisfies: TypeScript widens types, losing info
const palette1: Palette = {
  red: [255, 0, 0],
  green: '#00ff00',
};
// palette1.red is Color, not [number, number, number]
// palette1.red[0] — Error! Color doesn't have indexer

// With satisfies: TypeScript validates AND keeps narrow types
const palette2 = {
  red: [255, 0, 0],
  green: '#00ff00',
  blue: [0, 0, 255],
} satisfies Palette;

// palette2.red is [number, number, number] — still narrow!
console.log(palette2.red[0]);    // 255 — works!
console.log(palette2.green.toUpperCase()); // '#00FF00' — string methods!

// Another use: config validation
type Config = { host: string; port: number; debug?: boolean };
const serverConfig = {
  host: 'localhost',
  port: 3000,
  // debug: 'yes',  // satisfies would catch this!
} satisfies Config;

console.log(serverConfig.port);  // 3000
```

---

## Step 6: Branded / Nominal Types

```typescript
// TypeScript is structurally typed — two identical shapes are compatible
// Branded types add "nominal" safety

declare const brand: unique symbol;
type Brand<T, B> = T & { readonly [brand]: B };

// Specific branded types
type UserId   = Brand<number, 'UserId'>;
type PostId   = Brand<number, 'PostId'>;
type Email    = Brand<string, 'Email'>;
type Password = Brand<string, 'Password'>;

function createUserId(id: number): UserId   { return id as UserId; }
function createPostId(id: number): PostId   { return id as PostId; }
function createEmail(email: string): Email {
  if (!/^[^@]+@[^@]+\.[^@]+$/.test(email)) throw new Error('Invalid email');
  return email as Email;
}

function getUser(id: UserId): void {
  console.log(`Fetching user ${id}`);
}

const userId = createUserId(1);
const postId = createPostId(1);

getUser(userId);
// getUser(postId); // Error! Argument of type 'PostId' is not assignable to 'UserId'
// getUser(1);      // Error! '1' is not assignable to 'UserId'

const email = createEmail('alice@example.com');
console.log(email.includes('@'));  // string methods still work
console.log('Branded types OK');
```

---

## Step 7: Opaque Types Pattern

```typescript
// Stronger opaque type using module encapsulation
interface SqlQueryBrand { readonly _sqlQueryBrand: unique symbol; }
type SqlQuery = string & SqlQueryBrand;

// Only this function can create SqlQuery values
function sql(strings: TemplateStringsArray, ...values: unknown[]): SqlQuery {
  // In real code, use parameterized queries
  const query = strings.reduce((acc, str, i) => {
    return acc + str + (values[i] !== undefined ? `$${i}` : '');
  }, '');
  return query as SqlQuery;
}

// Type-safe database function
function executeQuery(query: SqlQuery): void {
  console.log('Executing:', query);
}

const userQuery = sql`SELECT * FROM users WHERE id = ${1}`;
executeQuery(userQuery);

// executeQuery('SELECT * FROM users'); // Error! Not a SqlQuery
const rawStr = 'SELECT * FROM users';
// executeQuery(rawStr); // Error! Prevents SQL injection
```

---

## Step 8: Capstone — Full Type Safety Demo

```typescript
// Save as lab10-capstone.ts
type Cat = { kind: 'cat'; meow(): void };
type Dog2 = { kind: 'dog'; bark(): void };
type Pet = Cat | Dog2;

function isCat(pet: Pet): pet is Cat { return pet.kind === 'cat'; }

const pet: Pet = { kind: 'cat', meow() { console.log('Meow!'); } };
if (isCat(pet)) pet.meow();

type RGB = [number, number, number];
type Palette = Record<string, RGB | string>;
const palette = { red: [255, 0, 0], green: '#00ff00' } satisfies Palette;
console.log(palette.red[0]);

type UserId = string & { readonly _brand: 'UserId' };
function createUserId(id: string): UserId { return id as UserId; }
const uid = createUserId('user-123');
console.log(uid);
console.log('Type guards OK');
```

Run:
```bash
ts-node -P tsconfig.json lab10-capstone.ts
```

📸 **Verified Output:**
```
Meow!
255
user-123
Type guards OK
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| Type guard | `x is T` return type | Narrow type in calling scope |
| Assertion | `asserts x is T` | Throw or narrow |
| satisfies | `value satisfies Type` | Validate without widening |
| Branded type | `T & { _brand: B }` | Prevent type confusion |
| Unique symbol | `unique symbol` | True nominal typing |
| Opaque type | Module-private brand | Maximum type safety |
