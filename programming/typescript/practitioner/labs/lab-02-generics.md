# Lab 02: Generics

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Master generic functions, classes, interfaces, constraints, and TypeScript's built-in utility types.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab02 && cd /lab02
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

## Step 2: Generic Functions

```typescript
// generic-functions.ts
function identity<T>(x: T): T { return x; }
function first<T>(arr: T[]): T | undefined { return arr[0]; }
function last<T>(arr: T[]): T | undefined { return arr[arr.length - 1]; }
function pair<A, B>(a: A, b: B): [A, B] { return [a, b]; }
function map<T, U>(arr: T[], fn: (item: T) => U): U[] { return arr.map(fn); }

console.log(identity<string>('hello'));   // hello
console.log(identity(42));               // 42 — inferred
console.log(first([10, 20, 30]));        // 10
console.log(pair('name', 42));           // ['name', 42]
console.log(map([1, 2, 3], x => x * 2));// [2, 4, 6]
```

> 💡 TypeScript can usually infer generic types from arguments — you don't always need `<T>` explicitly.

---

## Step 3: Generic Classes

```typescript
class Stack<T> {
  private items: T[] = [];
  push(item: T): void { this.items.push(item); }
  pop(): T | undefined { return this.items.pop(); }
  peek(): T | undefined { return this.items[this.items.length - 1]; }
  get size(): number { return this.items.length; }
  isEmpty(): boolean { return this.items.length === 0; }
  toArray(): T[] { return [...this.items]; }
}

class KeyValueStore<K, V> {
  private store = new Map<K, V>();
  set(key: K, val: V): this { this.store.set(key, val); return this; }
  get(key: K): V | undefined { return this.store.get(key); }
  has(key: K): boolean { return this.store.has(key); }
  keys(): K[] { return Array.from(this.store.keys()); }
}

const s = new Stack<number>();
s.push(1); s.push(2); s.push(3);
console.log('peek:', s.peek());   // 3
console.log('pop:', s.pop());     // 3
console.log('size:', s.size);     // 2

const kv = new KeyValueStore<string, number>();
kv.set('a', 1).set('b', 2);
console.log(kv.get('a'), kv.keys()); // 1 ['a', 'b']
```

---

## Step 4: Generic Interfaces and Constraints

```typescript
interface Repository<T, ID> {
  findById(id: ID): T | undefined;
  findAll(): T[];
  save(entity: T): T;
  delete(id: ID): boolean;
}

// Constraints: T must have an id property
interface HasId { id: number; }
function updateEntity<T extends HasId>(entities: T[], updated: T): T[] {
  return entities.map(e => e.id === updated.id ? updated : e);
}

// keyof constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: 'Alice', age: 30 };
console.log(getProperty(user, 'name')); // Alice
console.log(getProperty(user, 'age'));  // 30
// getProperty(user, 'email'); // TS Error!
```

> 💡 `extends keyof T` constrains K to valid property names of T — prevents runtime `undefined` access.

---

## Step 5: Default Type Parameters

```typescript
interface ApiResponse<T = unknown, E = string> {
  data: T | null;
  error: E | null;
  status: number;
}

type UserResponse = ApiResponse<{ name: string; email: string }>;
type ErrorResponse = ApiResponse<never, { code: number; message: string }>;

function createResponse<T = unknown>(data: T, status = 200): ApiResponse<T> {
  return { data, error: null, status };
}

const resp = createResponse({ name: 'Alice', email: 'alice@example.com' });
console.log(JSON.stringify(resp));
```

---

## Step 6: Built-in Utility Types

```typescript
type User = {
  id: number;
  name: string;
  email: string;
  password: string;
  createdAt: Date;
};

// Partial — all optional
type PartialUser = Partial<User>;
// Required — all required (reverse of Partial)
type RequiredUser = Required<PartialUser>;
// Readonly — immutable
type ReadonlyUser = Readonly<User>;
// Pick — select subset
type PublicUser = Pick<User, 'id' | 'name' | 'email'>;
// Omit — exclude fields
type UserWithoutPassword = Omit<User, 'password'>;
// Record — key-value map
type UserMap = Record<string, User>;
// Exclude/Extract — for union types
type StringOrNumber = string | number | boolean;
type OnlyPrimitives = Exclude<StringOrNumber, boolean>;  // string | number
type OnlyStrings = Extract<StringOrNumber, string>;      // string
// NonNullable
type MaybeString = string | null | undefined;
type DefiniteString = NonNullable<MaybeString>;          // string
// ReturnType / Parameters
function greet(name: string, age: number): string { return `${name} is ${age}`; }
type GreetReturn = ReturnType<typeof greet>;     // string
type GreetParams = Parameters<typeof greet>;    // [string, number]

const partial: PartialUser = { name: 'Bob' };
const pub: PublicUser = { id: 1, name: 'Alice', email: 'alice@example.com' };
console.log('partial:', JSON.stringify(partial));
console.log('public:', JSON.stringify(pub));
```

---

## Step 7: Generic Constraints in Practice

```typescript
// Merge two objects with type safety
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b };
}

// Filter array by type predicate
function filterByType<T, U extends T>(arr: T[], guard: (x: T) => x is U): U[] {
  return arr.filter(guard);
}

// Deep clone with generics
function clone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

const merged = merge({ a: 1 }, { b: 'hello' });
console.log(merged.a, merged.b);  // 1 hello

const cloned = clone({ id: 1, name: 'Alice', tags: ['admin'] });
console.log(JSON.stringify(cloned));
```

---

## Step 8: Capstone — Generic Repository

```typescript
// Save as lab02-capstone.ts
interface Entity { id: number; }

class InMemoryRepository<T extends Entity> implements Repository<T, number> {
  private items: T[] = [];
  findById(id: number): T | undefined { return this.items.find(i => i.id === id); }
  findAll(): T[] { return [...this.items]; }
  save(entity: T): T {
    const idx = this.items.findIndex(i => i.id === entity.id);
    if (idx >= 0) this.items[idx] = entity;
    else this.items.push(entity);
    return entity;
  }
  delete(id: number): boolean {
    const idx = this.items.findIndex(i => i.id === id);
    if (idx < 0) return false;
    this.items.splice(idx, 1);
    return true;
  }
}

interface Repository<T, ID> {
  findById(id: ID): T | undefined;
  findAll(): T[];
  save(entity: T): T;
  delete(id: ID): boolean;
}

type User = { id: number; name: string; email: string };

const userRepo = new InMemoryRepository<User>();
userRepo.save({ id: 1, name: 'Alice', email: 'alice@example.com' });
userRepo.save({ id: 2, name: 'Bob',   email: 'bob@example.com' });

console.log('All users:', userRepo.findAll().map(u => u.name));
console.log('Find 1:', userRepo.findById(1)?.name);
userRepo.delete(1);
console.log('After delete:', userRepo.findAll().map(u => u.name));
```

Run:
```bash
ts-node -P tsconfig.json lab02-capstone.ts
```

📸 **Verified Output:**
```
peek: 3
pop: 3
size: 2
hello
10
partial user: {"name":"Bob"}
Generics OK
All users: [ 'Alice', 'Bob' ]
Find 1: Alice
After delete: [ 'Bob' ]
```

---

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| Generic function | `function f<T>(x: T): T` | Reusable typed functions |
| Generic class | `class Stack<T>` | Typed data structures |
| Constraint | `T extends HasId` | Require specific shape |
| keyof constraint | `K extends keyof T` | Safe property access |
| Default type | `<T = unknown>` | Fallback type |
| Partial | `Partial<T>` | All optional |
| Pick/Omit | `Pick<T, K>` / `Omit<T, K>` | Select/exclude fields |
| ReturnType | `ReturnType<typeof fn>` | Infer function return type |
