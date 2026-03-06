# Lab 06: Strict Mode & Null Safety

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

`strictNullChecks`, optional chaining (`?.`), nullish coalescing (`??`), non-null assertion (`!`), definite assignment (`!`), and strict tsconfig flags.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab06 && cd /lab06
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

> 💡 `"strict": true` enables: `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`, `alwaysStrict`.

---

## Step 2: strictNullChecks

```typescript
// Without strictNullChecks: null/undefined assignable to any type (dangerous!)
// With strictNullChecks: must explicitly handle null/undefined

function getLength(str: string | null): number {
  // str.length  // Error! str could be null
  if (str === null) return 0;
  return str.length;  // TypeScript narrows to string
}

function getUser(id: number): { name: string } | null {
  if (id === 1) return { name: 'Alice' };
  return null;
}

const user = getUser(2);
// console.log(user.name);  // Error! user could be null

if (user !== null) {
  console.log(user.name);  // safe
}

console.log(getLength('hello'));  // 5
console.log(getLength(null));     // 0
```

---

## Step 3: Optional Chaining (?.)

```typescript
interface Address {
  street?: string;
  city?: string;
  country?: string;
}
interface Profile {
  bio?: string;
  address?: Address;
}
interface User {
  id: number;
  name: string;
  profile?: Profile;
}

const user: User = { id: 1, name: 'Alice' };

// Without optional chaining (verbose and error-prone)
const city1 = user.profile && user.profile.address && user.profile.address.city;

// With optional chaining (clean!)
const city2 = user.profile?.address?.city;

// Works with methods and array indexing too
const users: User[] = [{ id: 1, name: 'Alice' }];
const firstCity = users[0]?.profile?.address?.city;

// Optional method call
type Service = { start?: () => void };
const svc: Service = {};
svc.start?.();  // safe — does nothing if start is undefined

console.log(city2);      // undefined
console.log(firstCity);  // undefined
```

---

## Step 4: Nullish Coalescing (??) and Optional Assignment

```typescript
// ?? vs || : ?? only falls back on null/undefined (not 0, '', false)
const a = null ?? 'default';        // 'default'
const b = undefined ?? 'default';   // 'default'
const c = 0 ?? 'default';           // 0  (not 'default'!)
const d = '' ?? 'default';          // '' (not 'default'!)
const e = false ?? 'default';       // false

// Combined ?. and ??
interface Config { db?: { host?: string; port?: number } }
const config: Config = { db: { host: 'localhost' } };
const host = config.db?.host ?? 'default-host';
const port = config.db?.port ?? 5432;

console.log(a, b, c, d, e);    // default default 0  false
console.log(host, port);        // localhost 5432

// Nullish assignment ??=
let cached: string | null = null;
cached ??= 'computed-value';
console.log(cached);  // 'computed-value'
cached ??= 'other';   // not reassigned — cached already truthy
console.log(cached);  // still 'computed-value'
```

---

## Step 5: Non-Null Assertion (!)

```typescript
// Use ! when YOU know the value isn't null, but TypeScript can't prove it
// Use sparingly — it bypasses type safety!

function findElement(id: string): HTMLElement | null {
  // Simulated DOM lookup
  return id === 'root' ? { id } as any : null;
}

// Tell TypeScript "trust me, this isn't null"
const root = findElement('root')!;
console.log(root.id);  // safe at runtime in this case

// Better alternative: explicit check
const el = findElement('root');
if (!el) throw new Error('Root element not found');
console.log(el.id);  // TypeScript narrows automatically

// Another common use: regex match
const dateStr = '2024-01-15';
const match = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/)!;
const [, year, month, day] = match;  // ! asserts match isn't null
console.log(year, month, day);  // 2024 01 15
```

> 💡 Prefer explicit checks over `!`. Reserve `!` for cases where null genuinely can't occur but TypeScript can't infer it.

---

## Step 6: Definite Assignment Assertion (!:)

```typescript
class DataLoader {
  // ! tells TypeScript "this will be assigned before use"
  private data!: string[];
  private initialized!: boolean;

  async initialize(): Promise<void> {
    this.data = ['item1', 'item2', 'item3'];
    this.initialized = true;
  }

  getItems(): string[] {
    if (!this.initialized) throw new Error('Not initialized');
    return this.data;
  }
}

class Config {
  // Definite assignment for fields set in a separate init method
  host!: string;
  port!: number;

  load(env: NodeJS.ProcessEnv): void {
    this.host = env['HOST'] ?? 'localhost';
    this.port = parseInt(env['PORT'] ?? '3000');
  }
}

const loader = new DataLoader();
loader.initialize().then(() => console.log(loader.getItems()));
```

---

## Step 7: Strict tsconfig Flags Explained

```typescript
// This file illustrates what each flag catches:

// noImplicitAny: prevents implicitly 'any' typed variables
function implicit(x: any) {  // must explicitly type
  return x;
}

// strictFunctionTypes: covariant/contravariant function checking
type Callback = (value: string) => void;
// const cb: Callback = (value: string | number) => {};  // Error in strict mode

// strictBindCallApply: types .bind/.call/.apply properly
function greet(name: string): string { return `Hello, ${name}`; }
const bound = greet.bind(null, 'Alice');
const result: string = bound();  // TypeScript knows return type
console.log(result);

// noUncheckedIndexedAccess (add to tsconfig for extra safety)
const arr = [1, 2, 3];
const first = arr[0];  // number | undefined with noUncheckedIndexedAccess

// strictPropertyInitialization (covered in step 6)
console.log('Strict mode OK');
```

---

## Step 8: Capstone — Null-Safe API Client

```typescript
// Save as lab06-capstone.ts
interface Config { db?: { host?: string; port?: number } }
const config: Config = { db: { host: 'localhost' } };
const host = config.db?.host ?? 'default';
const port = config.db?.port ?? 5432;
console.log(host, port);

function isString(x: unknown): x is string { return typeof x === 'string'; }
const val: unknown = 'hello';
if (isString(val)) console.log(val.toUpperCase());

const el: string | null = 'exists';
console.log(el!.length);

console.log('Null safety OK');
```

Run:
```bash
ts-node -P tsconfig.json lab06-capstone.ts
```

📸 **Verified Output:**
```
localhost 5432
HELLO
6
Null safety OK
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| strictNullChecks | `"strict": true` | Prevents null/undefined errors |
| Optional chaining | `a?.b?.c` | Safe property access |
| Nullish coalescing | `a ?? 'default'` | Fallback on null/undefined only |
| Non-null assertion | `value!` | Tell TS you know it's not null |
| Definite assignment | `field!: Type` | Promise to assign before use |
| Nullish assignment | `a ??= value` | Assign only if null/undefined |
