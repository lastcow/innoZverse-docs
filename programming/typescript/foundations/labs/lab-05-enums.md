# Lab 5: Enums, Literal Types & Discriminated Unions

## Objective
Use TypeScript enums (numeric, string, const), string literal unions, and discriminated union patterns for type-safe state machines.

## Time
25 minutes

## Prerequisites
- Lab 01–04

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Numeric Enums

```typescript
enum Direction { North, South, East, West }  // 0, 1, 2, 3
enum HttpStatus {
    OK = 200, Created = 201, NoContent = 204,
    BadRequest = 400, Unauthorized = 401, NotFound = 404,
    InternalError = 500,
}

function describeStatus(code: HttpStatus): string {
    switch (code) {
        case HttpStatus.OK:            return "✅ Success";
        case HttpStatus.Created:       return "✅ Resource created";
        case HttpStatus.NotFound:      return "❌ Not found";
        case HttpStatus.InternalError: return "💥 Server error";
        default:                       return `HTTP ${code}`;
    }
}

console.log(describeStatus(HttpStatus.OK));
console.log(describeStatus(HttpStatus.NotFound));
console.log("Direction.North =", Direction.North);
console.log("Direction[0] =", Direction[0]);  // reverse mapping
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
enum Color { Red = 'RED', Green = 'GREEN', Blue = 'BLUE' }
enum Size  { Small = 1, Medium = 2, Large = 4, XLarge = 8 }
const colors = Object.values(Color);
console.log('Colors:', colors.join(', '));
console.log('Size.Large:', Size.Large);
"
```

> 💡 **String enums** (`Red = 'RED'`) are more debuggable than numeric enums — the value appears in logs and serialized JSON. Numeric enums have **reverse mapping** (`Direction[0] === 'North'`) but string enums do not. Prefer string enums for API contracts and serialized data.

**📸 Verified Output:**
```
Colors: RED, GREEN, BLUE
Size.Large: 4
```

---

### Step 2: Const Enums & Literal Types

```typescript
// const enum — inlined at compile time (zero runtime overhead)
const enum Status {
    Active   = "active",
    Inactive = "inactive",
    Pending  = "pending",
}

const s: Status = Status.Active;
// Compiles to: const s = "active"  (no runtime object!)

// String literal union — simpler alternative to string enum
type OrderStatus = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";
type HttpMethod  = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

function canTransitionTo(from: OrderStatus, to: OrderStatus): boolean {
    const transitions: Record<OrderStatus, OrderStatus[]> = {
        pending:   ["confirmed", "cancelled"],
        confirmed: ["shipped", "cancelled"],
        shipped:   ["delivered"],
        delivered: [],
        cancelled: [],
    };
    return transitions[from].includes(to);
}

const transitions: [OrderStatus, OrderStatus][] = [
    ["pending", "confirmed"],  // valid
    ["pending", "delivered"],  // invalid
    ["shipped", "delivered"],  // valid
    ["delivered", "cancelled"],// invalid
];

transitions.forEach(([from, to]) => {
    const ok = canTransitionTo(from, to);
    console.log(\`  \${from} → \${to}: \${ok ? "✓" : "✗"}\`);
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Align = 'left' | 'center' | 'right';
function pad(s: string, width: number, align: Align = 'left'): string {
    if (align === 'left')   return s.padEnd(width);
    if (align === 'right')  return s.padStart(width);
    const half = Math.floor((width - s.length) / 2);
    return s.padStart(s.length + half).padEnd(width);
}
['left', 'center', 'right'].forEach(a => console.log('|' + pad('hi', 10, a as Align) + '|'));
"
```

> 💡 **`const enum` is inlined** — the compiler replaces every `Status.Active` with `"active"` literally. No enum object exists at runtime. This gives the fastest possible code but breaks if the enum is in a separate file used by JavaScript (no const enum runtime). Use `const enum` for internal TypeScript-only code.

**📸 Verified Output:**
```
|hi        |
|    hi    |
|        hi|
```

---

### Step 3: Discriminated Unions as State Machines

```typescript
type NetworkState =
    | { state: "idle" }
    | { state: "loading"; url: string; startTime: number }
    | { state: "success"; data: unknown; duration: number }
    | { state: "error"; error: Error; retries: number };

function describeState(s: NetworkState): string {
    switch (s.state) {
        case "idle":    return "Ready";
        case "loading": return \`Loading \${s.url} (\${Date.now() - s.startTime}ms)\`;
        case "success": return \`Done in \${s.duration}ms\`;
        case "error":   return \`Failed: \${s.error.message} (retry \${s.retries})\`;
    }
}

// State transitions
function startLoading(url: string): Extract<NetworkState, { state: "loading" }> {
    return { state: "loading", url, startTime: Date.now() };
}

function succeed(data: unknown): Extract<NetworkState, { state: "success" }> {
    return { state: "success", data, duration: 42 };
}

function fail(err: Error, retries: number): Extract<NetworkState, { state: "error" }> {
    return { state: "error", error: err, retries };
}

const states: NetworkState[] = [
    { state: "idle" },
    startLoading("https://api.example.com/products"),
    succeed([{ id: 1, name: "Surface Pro" }]),
    fail(new Error("Timeout after 30s"), 2),
];

states.forEach(s => console.log(" ", describeState(s)));
```

> 💡 **`Extract<NetworkState, { state: 'loading' }>`** filters a union to only the variants matching a shape. It's the type-level equivalent of `filter`. Use it for factory functions that produce specific union variants, ensuring the return type precisely matches what you return.

**📸 Verified Output:**
```
  Ready
  Loading https://api.example.com/products (0ms)
  Done in 42ms
  Failed: Timeout after 30s (retry 2)
```

---

### Steps 4–8: Enum Utilities, Object Enums, Exhaustiveness, Flags, Capstone

```typescript
// Step 4: Object enum (no enum keyword — better tree-shaking)
const Priority = { Low: 1, Medium: 5, High: 10, Critical: 100 } as const;
type Priority = typeof Priority[keyof typeof Priority]; // 1 | 5 | 10 | 100

// Step 5: Exhaustive switch
type Fruit = "apple" | "banana" | "cherry";
function fruitEmoji(f: Fruit): string {
    switch (f) {
        case "apple":  return "🍎";
        case "banana": return "🍌";
        case "cherry": return "🍒";
    }
    // TypeScript errors here if a case is missing (unreachable)
}

// Step 6: Bit flags with const enum
const Permission = {
    None:    0,
    Read:    1 << 0,  // 1
    Write:   1 << 1,  // 2
    Delete:  1 << 2,  // 4
    Admin:   1 << 3,  // 8
} as const;
type Permission = typeof Permission[keyof typeof Permission];

function hasPermission(userPerms: number, required: number): boolean {
    return (userPerms & required) === required;
}

const adminPerms = Permission.Read | Permission.Write | Permission.Delete | Permission.Admin;
console.log("Can read:", hasPermission(adminPerms, Permission.Read));
console.log("Can write:", hasPermission(adminPerms, Permission.Write));

const readOnlyPerms = Permission.Read;
console.log("ReadOnly can delete:", hasPermission(readOnlyPerms, Permission.Delete));

// Step 7: Enum to array
const fruits: Fruit[] = ["apple", "banana", "cherry"];
fruits.forEach(f => console.log(fruitEmoji(f)));

// Step 8: Capstone — order state machine
type OrderEvent =
    | { type: "CONFIRM" }
    | { type: "SHIP"; trackingId: string }
    | { type: "DELIVER" }
    | { type: "CANCEL"; reason: string };

type OrderState = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";

function reducer(state: OrderState, event: OrderEvent): OrderState {
    switch (state) {
        case "pending":
            if (event.type === "CONFIRM") return "confirmed";
            if (event.type === "CANCEL")  return "cancelled";
            return state;
        case "confirmed":
            if (event.type === "SHIP")    return "shipped";
            if (event.type === "CANCEL")  return "cancelled";
            return state;
        case "shipped":
            if (event.type === "DELIVER") return "delivered";
            return state;
        default: return state;
    }
}

let orderState: OrderState = "pending";
const events: OrderEvent[] = [
    { type: "CONFIRM" },
    { type: "SHIP", trackingId: "TRK-001" },
    { type: "DELIVER" },
];

events.forEach(e => {
    const next = reducer(orderState, e);
    console.log(\`\${orderState} --[\${e.type}]--> \${next}\`);
    orderState = next;
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const Perm = { Read: 1, Write: 2, Delete: 4 } as const;
const admin = Perm.Read | Perm.Write | Perm.Delete;
const reader = Perm.Read;
const check = (p: number, req: number) => (p & req) === req;
console.log('admin can delete:', check(admin, Perm.Delete));
console.log('reader can write:', check(reader, Perm.Write));
"
```

**📸 Verified Output:**
```
admin can delete: true
reader can write: false
```

---

## Summary

Enums and literal types make TypeScript's type system practical for real-world modeling. You've covered numeric/string/const enums, string literal unions, discriminated unions as state machines, bit flags, and a Redux-style order state machine reducer.

## Further Reading
- [TypeScript Enums](https://www.typescriptlang.org/docs/handbook/enums.html)
- [Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
