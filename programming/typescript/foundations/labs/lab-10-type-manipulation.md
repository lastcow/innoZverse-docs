# Lab 10: Type Manipulation — keyof, typeof, Template Literals & More

## Objective
Master advanced TypeScript type manipulation: `keyof`, `typeof`, indexed access types, template literal types, mapped types with modifiers, and building complex type utilities.

## Time
30 minutes

## Prerequisites
- Lab 03 (Interfaces), Lab 06 (Generics)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: keyof & typeof

```typescript
interface Product {
    id: number;
    name: string;
    price: number;
    stock: number;
    category: string;
}

// keyof — produces union of property names
type ProductKeys = keyof Product;  // "id" | "name" | "price" | "stock" | "category"

// typeof — get type of a value (at type level)
const defaultConfig = { host: "localhost", port: 3000, debug: false, timeout: 30 };
type Config = typeof defaultConfig;  // { host: string; port: number; debug: boolean; timeout: number }

// keyof typeof — keys of an object value
type ConfigKey = keyof typeof defaultConfig;  // "host" | "port" | "debug" | "timeout"

function getConfig<K extends keyof typeof defaultConfig>(key: K): (typeof defaultConfig)[K] {
    return defaultConfig[key];
}

console.log(getConfig("host"));    // string
console.log(getConfig("port"));    // number
console.log(getConfig("debug"));   // boolean

// typeof on functions
function add(a: number, b: number) { return a + b; }
type AddFn = typeof add;  // (a: number, b: number) => number
type AddReturn = ReturnType<typeof add>;  // number
type AddParams = Parameters<typeof add>;  // [number, number]

// keyof for generic lookup
function pluck<T, K extends keyof T>(items: T[], key: K): T[K][] {
    return items.map(item => item[key]);
}

const products: Product[] = [
    { id: 1, name: "Surface Pro", price: 864, stock: 15, category: "Laptop" },
    { id: 2, name: "Surface Pen", price: 49.99, stock: 80, category: "Accessory" },
];

console.log(pluck(products, "name"));    // ["Surface Pro", "Surface Pen"]
console.log(pluck(products, "price"));   // [864, 49.99]
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const colors = { red: '#ff0000', green: '#00ff00', blue: '#0000ff' } as const;
type ColorName = keyof typeof colors;
type ColorValue = (typeof colors)[ColorName];
function getColor(name: ColorName): ColorValue { return colors[name]; }
(['red', 'green', 'blue'] as ColorName[]).forEach(c => console.log(c, getColor(c)));
"
```

> 💡 **`as const`** freezes an object literal's types to their literal values — `{ port: 3000 }` has type `{ port: number }` normally, but `{ port: 3000 } as const` has type `{ readonly port: 3000 }`. Combined with `typeof`, you get precise literal types for all values.

**📸 Verified Output:**
```
red #ff0000
green #00ff00
blue #0000ff
```

---

### Step 2: Indexed Access Types

```typescript
interface Order {
    id: number;
    customer: {
        name: string;
        email: string;
        address: {
            street: string;
            city: string;
            country: string;
        };
    };
    items: {
        productId: number;
        name: string;
        price: number;
        quantity: number;
    }[];
    status: "pending" | "confirmed" | "shipped" | "delivered";
    total: number;
}

// Indexed access — drill into types
type Customer      = Order["customer"];
type Address       = Order["customer"]["address"];
type OrderItem     = Order["items"][number];  // element type of array
type OrderStatus   = Order["status"];  // "pending" | "confirmed" | "shipped" | "delivered"
type ItemPrice     = Order["items"][number]["price"]; // number

// Use in functions
function formatAddress(addr: Address): string {
    return `${addr.street}, ${addr.city}, ${addr.country}`;
}

function calcItemTotal(item: OrderItem): number {
    return item.price * item.quantity;
}

const order: Order = {
    id: 1001,
    customer: { name: "Dr. Chen", email: "chen@example.com",
                address: { street: "950 Ridge Rd", city: "Claymont", country: "US" } },
    items: [
        { productId: 1, name: "Surface Pro", price: 864, quantity: 1 },
        { productId: 2, name: "Surface Pen", price: 49.99, quantity: 2 },
    ],
    status: "confirmed",
    total: 963.98,
};

console.log(formatAddress(order.customer.address));
order.items.forEach(item => console.log(`  ${item.name}: $${calcItemTotal(item)}`));
console.log("Status:", order.status);
```

> 💡 **`Type["items"][number]`** gets the element type of an array property — it's the TypeScript equivalent of "what's in this array?" This is essential for writing utilities that operate on array elements without duplicating the interface definition.

**📸 Verified Output:**
```
950 Ridge Rd, Claymont, US
  Surface Pro: $864
  Surface Pen: $99.98
Status: confirmed
```

---

### Steps 3–8: Template Literals, Mapped Modifiers, Recursive, Deep Utilities, as const, Capstone

```typescript
// Step 3: Template literal types
type EventName = "click" | "focus" | "blur";
type DOMEvent = `on${Capitalize<EventName>}`;  // "onClick" | "onFocus" | "onBlur"

type HttpVerb = "get" | "post" | "put" | "delete";
type CamelVerb = `${HttpVerb}${Capitalize<string>}`;

// Type-safe CSS properties
type Side = "top" | "right" | "bottom" | "left";
type SpacingProp = `margin${Capitalize<Side>}` | `padding${Capitalize<Side>}`;
// "marginTop" | "marginRight" | ... | "paddingTop" | ...

// Step 4: Mapped type modifiers
interface MutableProduct { name: string; price: number; stock: number; }

type Immutable<T>   = { readonly [K in keyof T]: T[K] };
type AllOptional<T> = { [K in keyof T]?: T[K] };
type AllRequired<T> = { [K in keyof T]-?: T[K] };  // remove optional
type MutableOf<T>   = { -readonly [K in keyof T]: T[K] }; // remove readonly

// Step 5: Deep Partial / Deep Required
type DeepPartial<T> = {
    [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

type DeepRequired<T> = {
    [K in keyof T]-?: T[K] extends object ? DeepRequired<T[K]> : NonNullable<T[K]>;
};

interface ServerConfig {
    db: { host: string; port: number; name?: string };
    cache?: { redis: { host: string; port: number } };
}

const partialConfig: DeepPartial<ServerConfig> = {
    db: { host: "localhost" }  // port and name are optional
};
console.log("Partial config:", JSON.stringify(partialConfig));

// Step 6: Type predicates for arrays
type NonNullableArray<T> = T extends null | undefined ? never : T;

function filterNull<T>(arr: (T | null | undefined)[]): T[] {
    return arr.filter((x): x is T => x != null);
}

const mixed = [1, null, 2, undefined, 3, null, 4];
const clean = filterNull(mixed);
console.log("Clean:", clean.join(", "));  // 1, 2, 3, 4

// Step 7: String manipulation types
type Camel<S extends string> =
    S extends `${infer Word}_${infer Rest}`
        ? `${Word}${Capitalize<Camel<Rest>>}`
        : S;

type CamelCase = Camel<"hello_world_test">;  // "helloWorldTest"

function toCamel<S extends string>(s: S): Camel<S> {
    return s.replace(/_([a-z])/g, (_, c) => c.toUpperCase()) as Camel<S>;
}

console.log(toCamel("hello_world_test"));    // helloWorldTest
console.log(toCamel("get_user_by_id"));      // getUserById

// Step 8: Capstone — schema builder with type inference
const schema = {
    string: (options?: { min?: number; max?: number }) => ({ type: "string" as const, ...options }),
    number: (options?: { min?: number; max?: number }) => ({ type: "number" as const, ...options }),
    boolean: ()                                        => ({ type: "boolean" as const }),
    array: <T>(of: T)                                 => ({ type: "array" as const, of }),
    optional: <T>(schema: T)                          => ({ ...schema as any, optional: true }),
};

const productSchema = {
    id:       schema.number({ min: 1 }),
    name:     schema.string({ min: 2, max: 100 }),
    price:    schema.number({ min: 0 }),
    stock:    schema.optional(schema.number({ min: 0 })),
    category: schema.string(),
    tags:     schema.optional(schema.array(schema.string())),
};

type InferSchema<S extends Record<string, { type: string; optional?: boolean }>> = {
    [K in keyof S as S[K]["optional"] extends true ? never : K]: InferType<S[K]>;
} & {
    [K in keyof S as S[K]["optional"] extends true ? K : never]?: InferType<S[K]>;
};

type InferType<T extends { type: string }> =
    T["type"] extends "string"  ? string  :
    T["type"] extends "number"  ? number  :
    T["type"] extends "boolean" ? boolean : unknown;

type Product2 = InferSchema<typeof productSchema>;
// { id: number; name: string; price: number; category: string; stock?: number; tags?: unknown }

const p: Product2 = { id: 1, name: "Surface Pro", price: 864, category: "Laptop" };
console.log("Product:", p.name, "$" + p.price);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
// keyof + indexed access pattern
const STATUS = { pending: 0, active: 1, suspended: 2, closed: 3 } as const;
type StatusCode = (typeof STATUS)[keyof typeof STATUS]; // 0 | 1 | 2 | 3
type StatusName = keyof typeof STATUS; // 'pending' | 'active' | ...
function statusLabel(code: StatusCode): StatusName {
    return Object.entries(STATUS).find(([,v]) => v === code)?.[0] as StatusName;
}
([0,1,2,3] as StatusCode[]).forEach(c => console.log(c, '->', statusLabel(c)));
"
```

**📸 Verified Output:**
```
0 -> pending
1 -> active
2 -> suspended
3 -> closed
```

---

## Summary

TypeScript's type manipulation capabilities are a programming language within a programming language. You've covered `keyof`, `typeof`, indexed access types, template literal types, mapped type modifiers, deep utility types, type predicates for arrays, string manipulation types, and a schema-to-type inference system.

## Further Reading
- [keyof Type Operator](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)
- [typeof Type Operator](https://www.typescriptlang.org/docs/handbook/2/typeof-types.html)
- [Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
