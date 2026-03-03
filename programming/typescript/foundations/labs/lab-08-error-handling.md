# Lab 8: Error Handling in TypeScript

## Objective
Handle errors with type safety: typed Error classes, Result/Either types, discriminated unions for errors, exhaustive handling, and `never` for impossible states.

## Time
30 minutes

## Prerequisites
- Lab 02 (Functions), Lab 05 (Enums)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Typed Error Classes

```typescript
// Custom error hierarchy
class AppError extends Error {
    constructor(
        message: string,
        public readonly code: string,
        public readonly context?: Record<string, unknown>,
    ) {
        super(message);
        this.name = this.constructor.name;
        // Fix prototype chain (needed for `instanceof`)
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

class ValidationError extends AppError {
    constructor(
        public readonly field: string,
        message: string,
        public readonly value?: unknown,
    ) {
        super(message, "VALIDATION_ERROR", { field, value });
    }
}

class NotFoundError extends AppError {
    constructor(resource: string, id: number | string) {
        super(`${resource} #${id} not found`, "NOT_FOUND", { resource, id });
    }
}

class NetworkError extends AppError {
    constructor(url: string, public readonly statusCode: number) {
        super(`HTTP ${statusCode} from ${url}`, "NETWORK_ERROR", { url, statusCode });
    }
}

// Usage
function processAge(input: string): number {
    const age = parseInt(input);
    if (isNaN(age)) throw new ValidationError("age", `'${input}' is not a number`, input);
    if (age < 0 || age > 150) throw new ValidationError("age", `Age ${age} out of range`, age);
    return age;
}

["25", "abc", "-1", "200"].forEach(input => {
    try {
        console.log(`age=${processAge(input)}`);
    } catch (e) {
        if (e instanceof ValidationError) {
            console.log(`ValidationError[${e.field}]: ${e.message}`);
        } else {
            throw e;
        }
    }
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
class ApiError extends Error {
    constructor(public statusCode: number, message: string) {
        super(message);
        this.name = 'ApiError';
        Object.setPrototypeOf(this, ApiError.prototype);
    }
}
try {
    throw new ApiError(404, 'User not found');
} catch (e) {
    if (e instanceof ApiError) console.log(e.name + ' ' + e.statusCode + ': ' + e.message);
}
"
```

> 💡 **`Object.setPrototypeOf(this, new.target.prototype)`** is essential when extending `Error` in TypeScript compiled to ES5. Without it, `instanceof` checks fail — `new ValidationError() instanceof ValidationError` returns `false`. With ES2015 target in tsconfig, this isn't needed.

**📸 Verified Output:**
```
ApiError 404: User not found
```

---

### Step 2: Result Type Pattern

```typescript
// Typed Result — errors as values, not exceptions
type Success<T> = { readonly ok: true;  readonly value: T };
type Failure<E> = { readonly ok: false; readonly error: E };
type Result<T, E = Error> = Success<T> | Failure<E>;

const ok  = <T>(value: T): Success<T>   => ({ ok: true, value });
const err = <E>(error: E): Failure<E>   => ({ ok: false, error });

// Chaining
function mapResult<T, U, E>(result: Result<T, E>, fn: (val: T) => U): Result<U, E> {
    return result.ok ? ok(fn(result.value)) : result;
}

function flatMapResult<T, U, E>(result: Result<T, E>, fn: (val: T) => Result<U, E>): Result<U, E> {
    return result.ok ? fn(result.value) : result;
}

// Application
function parseNumber(s: string): Result<number, string> {
    const n = parseFloat(s);
    return isNaN(n) ? err(`'${s}' is not a number`) : ok(n);
}

function divide(a: number, b: number): Result<number, string> {
    return b === 0 ? err("Division by zero") : ok(a / b);
}

function squareRoot(n: number): Result<number, string> {
    return n < 0 ? err(`Cannot sqrt negative: ${n}`) : ok(Math.sqrt(n));
}

// Compose pipeline
function compute(aStr: string, bStr: string): Result<string, string> {
    return flatMapResult(
        flatMapResult(
            flatMapResult(parseNumber(aStr), a =>
                flatMapResult(parseNumber(bStr), b => divide(a, b))
            ),
            squareRoot
        ),
        n => ok(n.toFixed(4))
    );
}

[["16", "4"], ["25", "0"], ["abc", "4"], ["-4", "1"]].forEach(([a, b]) => {
    const r = compute(a, b);
    if (r.ok) console.log(`  √(${a}/${b}) = ${r.value}`);
    else      console.log(`  √(${a}/${b}) → Error: ${r.error}`);
});
```

> 💡 **Result as a value** makes errors explicit in the type signature — `Result<number, string>` tells callers this can fail. Unlike exceptions, errors can't be accidentally ignored. Libraries like `neverthrow` and `fp-ts` provide production-ready Result implementations with richer combinators.

**📸 Verified Output:**
```
  √(16/4) = 2.0000
  √(25/0) → Error: Division by zero
  √(abc/4) → Error: 'abc' is not a number
  √(-4/1) → Error: Cannot sqrt negative: -4
```

---

### Steps 3–8: Either Type, Error Boundaries, Async Errors, Exhaustive, Retry, Capstone

```typescript
// Step 3: Error union types
type ParseError = { type: "PARSE_ERROR"; input: string; message: string };
type NetworkError2 = { type: "NETWORK_ERROR"; url: string; status: number };
type AuthError = { type: "AUTH_ERROR"; reason: string };
type AppErr = ParseError | NetworkError2 | AuthError;

function handleError(err: AppErr): string {
    switch (err.type) {
        case "PARSE_ERROR":   return `Parse failed: ${err.message} (input: ${err.input})`;
        case "NETWORK_ERROR": return `HTTP ${err.status} from ${err.url}`;
        case "AUTH_ERROR":    return `Auth denied: ${err.reason}`;
    }
}

const errors: AppErr[] = [
    { type: "PARSE_ERROR", input: "abc", message: "not a number" },
    { type: "NETWORK_ERROR", url: "/api/users", status: 404 },
    { type: "AUTH_ERROR", reason: "token expired" },
];

errors.forEach(e => console.log(handleError(e)));

// Step 4: Async error handling
async function safeFetch<T>(url: string, fallback: T): Promise<T> {
    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return await resp.json() as T;
    } catch (e) {
        console.error(`Fetch failed: ${url}`, (e as Error).message);
        return fallback;
    }
}

// Step 5: Never for exhaustiveness
function assertNever(x: never): never {
    throw new Error(`Unhandled: ${JSON.stringify(x)}`);
}

type Color = "red" | "green" | "blue";
function colorCode(c: Color): number {
    switch (c) {
        case "red":   return 0xff0000;
        case "green": return 0x00ff00;
        case "blue":  return 0x0000ff;
        default:      return assertNever(c);
    }
}

["red", "green", "blue"].forEach((c: string) => {
    console.log(`${c}: #${colorCode(c as Color).toString(16).padStart(6, "0")}`);
});

// Step 6: Retry with exponential backoff
async function withRetry<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    baseDelayMs: number = 100,
): Promise<T> {
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (e) {
            if (attempt === maxRetries) throw e;
            const delay = baseDelayMs * Math.pow(2, attempt);
            console.log(`  Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
            await new Promise(r => setTimeout(r, delay));
        }
    }
    throw new Error("Unreachable");
}

// Step 7: Error boundary pattern
class ErrorBoundary {
    private handlers = new Map<string, (err: Error) => void>();

    on(errorType: string, handler: (err: Error) => void): this {
        this.handlers.set(errorType, handler);
        return this;
    }

    async wrap<T>(fn: () => Promise<T>): Promise<T | undefined> {
        try {
            return await fn();
        } catch (e) {
            const err = e as Error;
            const handler = this.handlers.get(err.constructor.name)
                          ?? this.handlers.get("Error");
            if (handler) { handler(err); return undefined; }
            throw e;
        }
    }
}

// Step 8: Capstone — typed error handling pipeline
type ParsedInput = { name: string; price: number; stock: number };
type ValidationErrors = Record<string, string>;

function validateProduct(raw: Record<string, unknown>): Result<ParsedInput, ValidationErrors> {
    const errors: ValidationErrors = {};
    if (!raw.name || typeof raw.name !== "string" || raw.name.length < 2)
        errors.name = "Name must be at least 2 characters";
    if (!raw.price || typeof raw.price !== "number" || raw.price <= 0)
        errors.price = "Price must be positive";
    if (raw.stock !== undefined && typeof raw.stock !== "number")
        errors.stock = "Stock must be a number";

    return Object.keys(errors).length > 0 ? err(errors) : ok({
        name: raw.name as string,
        price: raw.price as number,
        stock: (raw.stock as number) ?? 0,
    });
}

const testInputs = [
    { name: "Surface Pro", price: 864, stock: 15 },
    { name: "X", price: -10 },
    { price: 49.99 },
];

testInputs.forEach((input, i) => {
    const result = validateProduct(input);
    if (result.ok) {
        console.log(`✓ Input ${i+1}: ${result.value.name} $${result.value.price}`);
    } else {
        console.log(`✗ Input ${i+1}:`);
        Object.entries(result.error).forEach(([f, m]) => console.log(`  - ${f}: ${m}`));
    }
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Res<T> = { ok: true; value: T } | { ok: false; error: string };
const ok = <T>(v: T): Res<T> => ({ ok: true, value: v });
const err = (e: string): Res<never> => ({ ok: false, error: e });
const parse = (s: string): Res<number> => isNaN(+s) ? err('NaN') : ok(+s);
['42', 'abc', '3.14'].forEach(s => {
    const r = parse(s);
    console.log(s, '->', r.ok ? 'number: ' + r.value : 'error: ' + r.error);
});
"
```

**📸 Verified Output:**
```
42 -> number: 42
abc -> error: NaN
3.14 -> number: 3.14
```

---

## Summary

TypeScript error handling is explicit and type-safe. You've covered typed Error subclasses, the Result pattern, error union discriminated types, async error handling, exhaustiveness with `never`, retry with backoff, and a full product validation pipeline.

## Further Reading
- [TypeScript Error Handling](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [neverthrow library](https://github.com/supermacro/neverthrow)
