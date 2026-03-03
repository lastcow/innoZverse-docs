# Lab 3: Interfaces, Type Aliases & Utility Types

## Objective
Use advanced interface patterns, built-in utility types (`Partial`, `Required`, `Pick`, `Omit`, `Record`, `Readonly`), mapped types, and conditional types to express complex data shapes.

## Background
TypeScript's type system goes far beyond basic annotations. Utility types let you transform existing types — create a "partial" version of an interface for updates, pick only the fields you need, or make everything readonly. Mapped types and conditional types give you a "type-level programming" capability that catches entire classes of bugs at compile time.

## Time
30 minutes

## Prerequisites
- Lab 01, Lab 02

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Interface Patterns

```typescript
// Base interface
interface Entity {
    readonly id: number;
    createdAt: string;
    updatedAt: string;
}

// Extending interfaces
interface User extends Entity {
    name: string;
    email: string;
    role: "admin" | "user" | "guest";
}

interface Product extends Entity {
    name: string;
    price: number;
    stock: number;
    category: string;
}

// Interface merging (declaration merging)
interface Window {
    appVersion: string;  // Adds to existing Window interface
}

// Callable interface
interface Formatter {
    (value: number): string;           // call signature
    currency: (value: number) => string;  // property
    percent: (value: number) => string;
}

// Constructable interface
interface ProductConstructor {
    new (name: string, price: number): Product;
}

// Index signatures
interface Cache<T> {
    [key: string]: T;
    size: number;  // can mix named + index signatures
}

const user: User = {
    id: 1,
    name: "Dr. Chen",
    email: "chen@example.com",
    role: "admin",
    createdAt: "2026-01-01",
    updatedAt: "2026-03-02",
};

console.log(`${user.name} (${user.role})`);

// Readonly interface
interface ImmutablePoint {
    readonly x: number;
    readonly y: number;
}
const p: ImmutablePoint = { x: 3, y: 4 };
// p.x = 5; // Error: Cannot assign to 'x' because it is a read-only property
console.log(`Point: (${p.x}, ${p.y})`);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
interface Timestamped { createdAt: Date; updatedAt: Date; }
interface Named { name: string; }
interface Tagged { tags: string[]; }
// Multiple interface extension
interface Article extends Timestamped, Named, Tagged {
    content: string;
    published: boolean;
}
const a: Article = {
    name: 'TypeScript Interfaces',
    content: 'Deep dive...',
    published: true,
    tags: ['ts', 'programming'],
    createdAt: new Date(),
    updatedAt: new Date(),
};
console.log(a.name, '| tags:', a.tags.join(', '));
"
```

> 💡 **Interface declaration merging** lets you add properties to existing interfaces — including built-in ones like `Window`, `Array`, or `HTMLElement`. This is how DefinitelyTyped (the @types packages) augment third-party libraries. It's a double-edged sword: powerful for library authors, dangerous if overused.

**📸 Verified Output:**
```
TypeScript Interfaces | tags: ts, programming
```

---

### Step 2: Built-in Utility Types

```typescript
interface User {
    id: number;
    name: string;
    email: string;
    password: string;
    role: "admin" | "user";
    createdAt: string;
}

// Partial<T> — all properties optional (for updates)
type UserUpdate = Partial<User>;
const update: UserUpdate = { name: "New Name" }; // valid

// Required<T> — all optional properties become required
interface Config {
    host?: string;
    port?: number;
    ssl?: boolean;
}
type RequiredConfig = Required<Config>;
// const c: RequiredConfig = { host: "localhost" }; // Error: missing port, ssl

// Pick<T, K> — select specific properties
type PublicUser = Pick<User, "id" | "name" | "role">;
const pub: PublicUser = { id: 1, name: "Dr. Chen", role: "admin" };
console.log("Public:", pub);

// Omit<T, K> — exclude specific properties
type SafeUser = Omit<User, "password">;  // never expose passwords
const safe: SafeUser = {
    id: 1, name: "Dr. Chen", email: "chen@example.com",
    role: "admin", createdAt: "2026-01-01",
};
console.log("Safe:", safe.name, "- no password field");

// Record<K, V> — object with specific keys
type CategoryPrices = Record<"Laptop" | "Accessory" | "Software", number>;
const prices: CategoryPrices = { Laptop: 864, Accessory: 49.99, Software: 99.99 };
console.log("Prices:", prices);

// Readonly<T> — all properties immutable
type ImmutableUser = Readonly<User>;
const frozen: ImmutableUser = {
    id: 1, name: "Dr. Chen", email: "c@c.com",
    password: "hashed", role: "admin", createdAt: "2026-01-01",
};
// frozen.name = "Other"; // Error: readonly

// ReturnType<T> and Parameters<T>
function createUser(name: string, role: "admin" | "user"): User {
    return { id: 1, name, email: "", password: "", role, createdAt: "" };
}
type CreateUserReturn = ReturnType<typeof createUser>;   // User
type CreateUserParams = Parameters<typeof createUser>;  // [string, "admin" | "user"]
console.log("Types inferred from function signature");
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
interface Product { id: number; name: string; price: number; stock: number; }
type ProductSummary = Pick<Product, 'name' | 'price'>;
type ProductUpdate = Partial<Omit<Product, 'id'>>;
const p: ProductSummary = { name: 'Surface Pro', price: 864 };
const u: ProductUpdate = { price: 799 };
console.log('Summary:', JSON.stringify(p));
console.log('Update:', JSON.stringify(u));
"
```

> 💡 **`Omit<User, 'password'>`** is the most important utility type for APIs — create a type without sensitive fields. `Pick` and `Omit` are complementary: use `Pick` when you want a few fields, `Omit` when you want all-but-a-few. Both produce new types without modifying the original.

**📸 Verified Output:**
```
Summary: {"name":"Surface Pro","price":864}
Update: {"price":799}
```

---

### Step 3: Mapped Types

```typescript
// Mapped type — transform all properties of a type
type Nullable<T> = { [K in keyof T]: T[K] | null };
type Optional<T> = { [K in keyof T]?: T[K] };
type Stringify<T> = { [K in keyof T]: string };

interface Product {
    id: number;
    name: string;
    price: number;
    inStock: boolean;
}

type NullableProduct  = Nullable<Product>;
type StringProduct    = Stringify<Product>;

const nullProd: NullableProduct = { id: 1, name: "Test", price: null, inStock: null };
console.log("Nullable:", nullProd.price); // null is valid

// Remove optional modifier (-?)
type Complete<T> = { [K in keyof T]-?: T[K] };

// Remap keys
type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
};

type ProductGetters = Getters<Product>;
// has: getId(): number, getName(): string, getPrice(): number, getInStock(): boolean

const getters: ProductGetters = {
    getId: () => 1,
    getName: () => "Surface Pro",
    getPrice: () => 864,
    getInStock: () => true,
};
console.log(getters.getName());
console.log(getters.getPrice());

// Filter properties by type
type NumberProps<T> = {
    [K in keyof T as T[K] extends number ? K : never]: T[K]
};
type ProductNumbers = NumberProps<Product>; // { id: number; price: number }
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type EventMap = { click: MouseEvent; keydown: KeyboardEvent; input: InputEvent };
type EventHandlers = { [K in keyof EventMap as \`on\${Capitalize<K>}\`]?: (e: EventMap[K]) => void };
// Shows type remapping
type Keys = keyof EventHandlers;
const handler: EventHandlers = { onClick: (e) => console.log('clicked') };
console.log('Handler keys would be: onClick, onKeydown, onInput');
handler.onClick?.({} as MouseEvent);
"
```

> 💡 **Mapped types + key remapping** (`as \`get\${Capitalize<...>}\``) lets you generate new types from old ones — adding prefixes, converting names, filtering by value type. This is how TypeScript's own `Partial`, `Readonly`, and `Required` utility types are implemented internally.

**📸 Verified Output:**
```
Handler keys would be: onClick, onKeydown, onInput
clicked
```

---

### Step 4: Conditional Types

```typescript
// Conditional type — type-level if/else
type IsString<T> = T extends string ? "yes" : "no";

type A = IsString<string>;  // "yes"
type B = IsString<number>;  // "no"
type C = IsString<"hello">; // "yes" — string literal extends string

// Distributive conditional types
type Flatten<T> = T extends Array<infer Item> ? Item : T;

type F1 = Flatten<number[]>;    // number
type F2 = Flatten<string[]>;    // string
type F3 = Flatten<number>;      // number (not array)

// Extract and Exclude (built-in, implemented as conditional types)
type MyExtract<T, U> = T extends U ? T : never;
type MyExclude<T, U> = T extends U ? never : T;

type NumOrStr = number | string | boolean;
type OnlyNum = MyExtract<NumOrStr, number>;   // number
type NoNum   = MyExclude<NumOrStr, number>;   // string | boolean

// NonNullable
type MaybeNull = string | number | null | undefined;
type NonNull = NonNullable<MaybeNull>;  // string | number

// infer — extract type from within
type UnpackPromise<T> = T extends Promise<infer R> ? R : T;
type PromiseString  = UnpackPromise<Promise<string>>;  // string
type PromiseNumber  = UnpackPromise<Promise<number>>;  // number
type NotAPromise    = UnpackPromise<string>;            // string

// Function return type extraction
type ReturnOf<F> = F extends (...args: unknown[]) => infer R ? R : never;
const double = (n: number) => n * 2;
type DoubleReturn = ReturnOf<typeof double>;  // number

console.log("Conditional types work at compile time");
console.log("IsString<string> = yes");
console.log("IsString<number> = no");

// Runtime use of conditional logic
function processValue<T>(value: T): T extends string ? string : number {
    if (typeof value === "string") return value.toUpperCase() as any;
    return (value as any) * 2;
}
console.log(processValue("hello"));  // HELLO
console.log(processValue(21));       // 42
```

> 💡 **`infer` keyword** lets you extract types from within other types. `T extends Promise<infer R>` means "if T is a Promise of something, call that something R." This is how `ReturnType<F>`, `Awaited<T>`, and `Parameters<F>` are implemented in TypeScript's standard library.

**📸 Verified Output:**
```
Conditional types work at compile time
IsString<string> = yes
IsString<number> = no
HELLO
42
```

---

### Step 5: Template Literal Types

```typescript
// Template literal types (TypeScript 4.1+)
type EventName = "click" | "focus" | "blur" | "keydown";
type Handler = `on${Capitalize<EventName>}`;
// "onClick" | "onFocus" | "onBlur" | "onKeydown"

type CSSProperty = "margin" | "padding" | "border";
type CSSDirection = "Top" | "Bottom" | "Left" | "Right";
type CSSLonghand = `${CSSProperty}${CSSDirection}`;
// "marginTop" | "marginBottom" | ... (12 combinations)

// API endpoint typing
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type ApiEndpoint = "/users" | "/products" | "/orders";
type ApiRoute = `${HttpMethod} ${ApiEndpoint}`;
// "GET /users" | "GET /products" | ... (12 combinations)

// Version strings
type SemVer = `${number}.${number}.${number}`;
// TypeScript 4.x: not perfect, but useful for documentation

// Real-world: typed event system
type EventPayloads = {
    userCreated: { id: number; name: string };
    userDeleted: { id: number };
    productAdded: { id: number; price: number };
};

type EventListener<T extends keyof EventPayloads> = (payload: EventPayloads[T]) => void;
type AllListeners = { [K in keyof EventPayloads]?: EventListener<K> };

const listeners: AllListeners = {
    userCreated: ({ id, name }) => console.log(`User created: #${id} ${name}`),
    productAdded: ({ id, price }) => console.log(`Product #${id}: $${price}`),
};

listeners.userCreated?.({ id: 1, name: "Dr. Chen" });
listeners.productAdded?.({ id: 42, price: 864 });

// Accessor pattern
type Accessor<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
} & {
    [K in keyof T as `set${Capitalize<string & K>}`]: (val: T[K]) => void;
};
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Prefix<T extends string, P extends string> = \`\${P}\${T}\`;
type WithGet<T extends string> = Prefix<T, 'get'>;
type WithSet<T extends string> = Prefix<T, 'set'>;
type Keys = 'name' | 'age' | 'email';
// These would be: 'getname' | 'getage' | 'getemail'
console.log('Template literal types combine strings at the type level');
const route = (method: 'GET'|'POST', path: string) => method + ' ' + path;
console.log(route('GET', '/users'));
console.log(route('POST', '/products'));
"
```

> 💡 **Template literal types** generate string literal unions from combinations of other literals. `\`on\${Capitalize<EventName>}\`` produces 4 types from 4 events. `\`\${Method} \${Path}\`` produces 12 route types from 3 methods × 4 paths. This enables typed route definitions, event maps, and CSS-in-JS systems.

**📸 Verified Output:**
```
User created: #1 Dr. Chen
Product #42: $864
```

---

### Step 6: Discriminated Unions

```typescript
// Discriminated union — a union where one field ("kind") identifies the variant
type Shape =
    | { kind: "circle"; radius: number }
    | { kind: "rectangle"; width: number; height: number }
    | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
    switch (shape.kind) {
        case "circle":    return Math.PI * shape.radius ** 2;
        case "rectangle": return shape.width * shape.height;
        case "triangle":  return 0.5 * shape.base * shape.height;
    }
}

function perimeter(shape: Shape): number {
    switch (shape.kind) {
        case "circle":    return 2 * Math.PI * shape.radius;
        case "rectangle": return 2 * (shape.width + shape.height);
        case "triangle":  return shape.base * 3; // equilateral approximation
    }
}

const shapes: Shape[] = [
    { kind: "circle", radius: 5 },
    { kind: "rectangle", width: 4, height: 6 },
    { kind: "triangle", base: 3, height: 4 },
];

shapes.forEach(s => {
    console.log(`${s.kind}: area=${area(s).toFixed(2)}, perimeter=${perimeter(s).toFixed(2)}`);
});

// Exhaustiveness check with never
function assertNever(x: never): never {
    throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

function describeShape(shape: Shape): string {
    switch (shape.kind) {
        case "circle":    return `Circle with r=${shape.radius}`;
        case "rectangle": return `Rectangle ${shape.width}×${shape.height}`;
        case "triangle":  return `Triangle base=${shape.base}`;
        default:          return assertNever(shape); // TypeScript errors if case is missing
    }
}

shapes.forEach(s => console.log(describeShape(s)));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type ApiResponse<T> =
    | { status: 'success'; data: T }
    | { status: 'error'; code: number; message: string }
    | { status: 'loading' };

function handle<T>(r: ApiResponse<T>): string {
    switch (r.status) {
        case 'success': return 'Data: ' + JSON.stringify(r.data);
        case 'error':   return 'Error ' + r.code + ': ' + r.message;
        case 'loading': return 'Loading...';
    }
}

const responses: ApiResponse<{name: string}>[] = [
    { status: 'success', data: { name: 'Dr. Chen' } },
    { status: 'error', code: 404, message: 'Not found' },
    { status: 'loading' },
];
responses.forEach(r => console.log(handle(r)));
"
```

> 💡 **Discriminated unions + exhaustiveness checking** is TypeScript's killer pattern for state machines. If you add a new variant (e.g., `| { kind: "ellipse"; ... }`), TypeScript immediately errors at every `switch` statement that doesn't handle it. This is impossible in JavaScript — you'd only find the bug at runtime.

**📸 Verified Output:**
```
Data: {"name":"Dr. Chen"}
Error 404: Not found
Loading...
```

---

### Step 7: Recursive Types

```typescript
// Recursive type — type that references itself
type JSONValue =
    | string
    | number
    | boolean
    | null
    | JSONValue[]
    | { [key: string]: JSONValue };

const config: JSONValue = {
    app: { name: "innoZverse", version: "1.0" },
    features: ["dark_mode", "beta_api"],
    debug: false,
    maxRetries: 3,
    metadata: null,
};

function countValues(json: JSONValue): number {
    if (json === null || typeof json !== "object") return 1;
    if (Array.isArray(json)) return json.reduce((n, v) => n + countValues(v), 0);
    return Object.values(json).reduce((n, v) => n + countValues(v), 0);
}

console.log("JSON value count:", countValues(config));

// Tree type
type TreeNode<T> = {
    value: T;
    children: TreeNode<T>[];
};

function treeMap<T, U>(node: TreeNode<T>, fn: (val: T) => U): TreeNode<U> {
    return {
        value: fn(node.value),
        children: node.children.map(c => treeMap(c, fn)),
    };
}

const tree: TreeNode<number> = {
    value: 1,
    children: [
        { value: 2, children: [{ value: 4, children: [] }, { value: 5, children: [] }] },
        { value: 3, children: [{ value: 6, children: [] }] },
    ],
};

const doubled = treeMap(tree, n => n * 2);
console.log("Root doubled:", doubled.value);
console.log("Children:", doubled.children.map(c => c.value).join(", "));
```

**📸 Verified Output:**
```
JSON value count: 7
Root doubled: 2
Children: 4, 6
```

---

### Step 8: Complete — Type-Safe API Client

```typescript
// Type-safe REST API client using all concepts from this lab
interface Endpoints {
    "GET /products":      { params: never;              response: Product[] };
    "GET /products/:id":  { params: { id: number };     response: Product };
    "POST /products":     { params: ProductCreate;      response: Product };
    "PUT /products/:id":  { params: { id: number } & ProductUpdate; response: Product };
    "DELETE /products/:id": { params: { id: number };   response: void };
}

interface Product {
    id: number; name: string; price: number; stock: number; category: string;
}
type ProductCreate = Omit<Product, "id">;
type ProductUpdate = Partial<ProductCreate>;

type ApiMethod = keyof Endpoints;
type ApiParams<M extends ApiMethod> = Endpoints[M]["params"];
type ApiResponse<M extends ApiMethod> = Endpoints[M]["response"];

// Simulated type-safe API client
class ApiClient {
    private store: Product[] = [
        { id: 1, name: "Surface Pro", price: 864, stock: 15, category: "Laptop" },
        { id: 2, name: "Surface Pen", price: 49.99, stock: 80, category: "Accessory" },
    ];
    private nextId = 3;

    async request<M extends ApiMethod>(method: M, params: ApiParams<M>): Promise<ApiResponse<M>> {
        const p = params as any;
        if (method === "GET /products")     return this.store as any;
        if (method === "GET /products/:id") return this.store.find(x => x.id === p.id) as any;
        if (method === "POST /products") {
            const product = { id: this.nextId++, ...p };
            this.store.push(product);
            return product as any;
        }
        if (method === "DELETE /products/:id") {
            this.store = this.store.filter(x => x.id !== p.id);
            return undefined as any;
        }
        return null as any;
    }
}

(async () => {
    const client = new ApiClient();

    const all = await client.request("GET /products", null as never);
    console.log("All products:", all.map(p => p.name).join(", "));

    const one = await client.request("GET /products/:id", { id: 1 });
    console.log("Product #1:", one.name, "$" + one.price);

    const created = await client.request("POST /products", {
        name: "Office 365", price: 99.99, stock: 999, category: "Software"
    });
    console.log("Created:", created.name, "id=" + created.id);

    await client.request("DELETE /products/:id", { id: 2 });
    const remaining = await client.request("GET /products", null as never);
    console.log("After delete:", remaining.length, "products");
})();
```

> 💡 **`ApiParams<M>` and `ApiResponse<M>`** are indexed access types — they look up the `params` and `response` fields from the `Endpoints` interface using the method string as a key. This ties the request parameters and response type to the specific endpoint, making `client.request()` fully type-safe.

**📸 Verified Output:**
```
All products: Surface Pro, Surface Pen
Product #1: Surface Pro $864
Created: Office 365 id=3
After delete: 2 products
```

---

## Summary

TypeScript's type system is a full programming language at the type level. You've used built-in utility types, mapped types with key remapping, conditional types with `infer`, template literal types, discriminated unions with exhaustiveness checking, recursive types, and a fully type-safe API client. These patterns are used in every professional TypeScript codebase.

## Further Reading
- [Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
