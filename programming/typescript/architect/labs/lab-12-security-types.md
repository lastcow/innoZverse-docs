# Lab 12: Security Through Types

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Security engineering with TypeScript's type system: branded types for injection prevention (SqlQuery/HtmlString/UrlPath), `Opaque<T,Tag>`, `Secret<T>` that redacts in `JSON.stringify`, type-safe CSRF flow, and compile-time permission system via type intersections.

---

## Step 1: Branded Types for Injection Prevention

```typescript
// Prevent SQL injection by making raw strings incompatible with query functions
declare const SqlQueryBrand:  unique symbol;
declare const HtmlStringBrand: unique symbol;
declare const UrlPathBrand:   unique symbol;
declare const UserInputBrand: unique symbol;

type SqlQuery   = string & { readonly [SqlQueryBrand]:   typeof SqlQueryBrand  };
type HtmlString = string & { readonly [HtmlStringBrand]: typeof HtmlStringBrand };
type UrlPath    = string & { readonly [UrlPathBrand]:    typeof UrlPathBrand   };
type UserInput  = string & { readonly [UserInputBrand]:  typeof UserInputBrand  };

// Only trusted creation functions can make these types
function sql(strings: TemplateStringsArray, ...params: (string | number)[]): SqlQuery {
  const paramPlaceholders = params.map(() => '?').join(', ');
  return strings.raw.join(paramPlaceholders) as SqlQuery;
}

function sanitizeHtml(raw: string): HtmlString {
  const escaped = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  return escaped as HtmlString;
}

function validateUrlPath(path: string): UrlPath {
  if (!/^\/[\w/-]*$/.test(path)) throw new Error(`Invalid URL path: ${path}`);
  return path as UrlPath;
}

// Functions ONLY accept branded types — raw strings are ERRORS at compile time
function executeQuery(query: SqlQuery): Promise<unknown[]> {
  return db.execute(query);
}

function renderHtml(html: HtmlString): void {
  element.innerHTML = html; // Safe — we know it's sanitized
}

// Usage:
executeQuery(sql`SELECT * FROM users WHERE id = ${userId}`); // ✓ OK
// executeQuery("SELECT * FROM users");                        // ✗ Error: string ≠ SqlQuery
// executeQuery(userInput);                                    // ✗ Error: UserInput ≠ SqlQuery
```

---

## Step 2: Generic Opaque Type

```typescript
// Generic Opaque<T, Tag> pattern
declare const OpaqueTag: unique symbol;
type Opaque<T, Tag extends string> = T & {
  readonly [OpaqueTag]: Tag;
};

// Create specific branded types
type UserId    = Opaque<string, 'UserId'>;
type OrderId   = Opaque<string, 'OrderId'>;
type ProductId = Opaque<string, 'ProductId'>;
type Cents     = Opaque<number, 'Cents'>;

// Factory functions
const UserId    = (id: string):    UserId    => id as UserId;
const OrderId   = (id: string):    OrderId   => id as OrderId;
const ProductId = (id: string):    ProductId => id as ProductId;
const Cents     = (amount: number): Cents     => {
  if (!Number.isInteger(amount) || amount < 0)
    throw new Error('Cents must be non-negative integer');
  return amount as Cents;
};

// Functions with opaque types prevent ID confusion
function getOrder(orderId: OrderId, userId: UserId): Promise<Order> {
  return db.orders.find({ id: orderId, userId });
}

const userId  = UserId('user-123');
const orderId = OrderId('order-456');

getOrder(orderId, userId); // ✓ OK
// getOrder(userId, orderId); // ✗ Error: UserId is not OrderId
// getOrder('order-456', 'user-123'); // ✗ Error: string is not OrderId
```

---

## Step 3: Secret<T> — Redact Sensitive Data

```typescript
// Secret<T>: prevents accidental logging/serialization of sensitive values
class Secret<T> {
  readonly #value: T;

  constructor(value: T) {
    this.#value = value;
  }

  // Only expose via explicit .expose() call — forces intentionality
  expose(): T {
    return this.#value;
  }

  // Redact in JSON serialization
  toJSON(): string {
    return '[REDACTED]';
  }

  // Redact in string coercion
  toString(): string {
    return '[REDACTED]';
  }

  // Redact in console.log (inspect)
  [Symbol.for('nodejs.util.inspect.custom')](): string {
    return 'Secret([REDACTED])';
  }
}

// Usage
const apiKey    = new Secret('sk-proj-abc123...');
const password  = new Secret('hunter2');
const jwtToken  = new Secret('eyJhbGc...');

// These all log '[REDACTED]'
console.log(apiKey);              // Secret([REDACTED])
console.log(JSON.stringify({ key: apiKey })); // {"key":"[REDACTED]"}

// Must explicitly expose to use
const headers = { Authorization: `Bearer ${jwtToken.expose()}` };

// In function signatures: callers know this is sensitive
async function authenticateUser(
  email: string,
  password: Secret<string>   // Forces caller to wrap password in Secret
): Promise<User> {
  const hash = await bcrypt.hash(password.expose(), 12);
  return db.users.findByEmailAndHash(email, hash);
}
```

---

## Step 4: Type-Safe CSRF Token Flow

```typescript
// CSRF token: must prove it came from server session
declare const CsrfTokenBrand: unique symbol;
type CsrfToken = string & { readonly [CsrfTokenBrand]: typeof CsrfTokenBrand };

// Server: generates and stores token
function generateCsrfToken(sessionId: string): CsrfToken {
  const token = crypto.randomUUID();
  sessionStore.set(sessionId, token);
  return token as CsrfToken;
}

// Server: validates token from request
function validateCsrfToken(
  token: string,              // From request header (untrusted)
  sessionId: string
): CsrfToken {                // Returns branded type only if valid
  const expected = sessionStore.get(sessionId);
  if (!expected || !timingSafeEqual(token, expected)) {
    throw new Error('Invalid CSRF token');
  }
  return token as CsrfToken;
}

// Mutation endpoints require validated CSRF token
async function createOrder(
  csrf: CsrfToken,            // Only validated tokens accepted
  data: CreateOrderInput
): Promise<Order> {
  return db.orders.create({ ...data, csrf: undefined });
}

// In request handler:
const csrf = validateCsrfToken(
  req.headers['x-csrf-token'] as string,
  req.session.id
);
const order = await createOrder(csrf, req.body); // ✓ Type-safe
```

---

## Step 5: Compile-Time Permission System

```typescript
// Role-based type intersections
type ReadOnly  = { readonly __read:  true };
type WriteOnly = { readonly __write: true };
type Admin     = { readonly __admin: true };

// Permission types
type UserPermission  = ReadOnly;
type EditorPermission = ReadOnly & WriteOnly;
type AdminPermission  = ReadOnly & WriteOnly & Admin;

// Context tagged with permissions
type UserContext<P> = {
  userId: string;
  permissions: P;
};

// Functions require specific permission level
function readData<P extends ReadOnly>(ctx: UserContext<P>): string[] {
  return db.publicData.findAll();
}

function writeData<P extends WriteOnly>(ctx: UserContext<P>, data: string): void {
  db.publicData.insert(data, ctx.userId);
}

function deleteAll<P extends Admin>(ctx: UserContext<P>): void {
  db.truncate();
}

// Usage:
const userCtx:   UserContext<UserPermission>   = { userId: '1', permissions: { __read: true } };
const adminCtx:  UserContext<AdminPermission>  = { userId: '2', permissions: { __read: true, __write: true, __admin: true } };

readData(userCtx);    // ✓ OK: user has ReadOnly
// writeData(userCtx);  // ✗ Error: UserPermission doesn't extend WriteOnly
// deleteAll(userCtx);  // ✗ Error: UserPermission doesn't extend Admin

writeData(adminCtx, 'data'); // ✓ OK: admin has WriteOnly
deleteAll(adminCtx);         // ✓ OK: admin has Admin
```

---

## Step 6: Type-Safe API Keys

```typescript
// Prevent mixing different API key types
type OpenAIKey   = Opaque<string, 'OpenAIKey'>;
type AnthropicKey = Opaque<string, 'AnthropicKey'>;
type GitHubToken  = Opaque<string, 'GitHubToken'>;

function createOpenAI(key: OpenAIKey): OpenAIClient { /* ... */ }
function createAnthropic(key: AnthropicKey): AnthropicClient { /* ... */ }

const openaiKey = process.env.OPENAI_KEY as OpenAIKey;
const anthropicKey = process.env.ANTHROPIC_KEY as AnthropicKey;

createOpenAI(openaiKey);       // ✓ Correct
// createOpenAI(anthropicKey); // ✗ Type error: AnthropicKey is not OpenAIKey
```

---

## Step 7: Validation Pipeline with Types

```typescript
// Validation result type — branded on success
type Validated<T> = T & { readonly __validated: true };

function validate<T>(schema: ZodSchema<T>, data: unknown): Validated<T> {
  const result = schema.parse(data); // throws on error
  return result as Validated<T>;
}

// Only validated data can be persisted
async function persistUser(user: Validated<NewUser>): Promise<User> {
  return db.users.insert(user);
}

const rawInput = req.body;
// persistUser(rawInput);          // ✗ Error: not Validated
const validUser = validate(NewUserSchema, rawInput);
persistUser(validUser);            // ✓ OK
```

---

## Step 8: Capstone — Branded Type Security

```bash
docker run --rm node:20-alpine sh -c "
  npm install -g typescript ts-node --quiet 2>/dev/null
  ts-node --transpile-only --compiler-options '{\"module\":\"commonjs\"}' -e '
// Branded type simulation (runtime verification of compile-time safety)
const SqlQueryBrand = Symbol(\"SqlQuery\");
function asSqlQuery(s) { return Object.assign(String(s), { [SqlQueryBrand]: true }); }
function isSqlQuery(s) { return typeof s === \"object\" && s !== null && SqlQueryBrand in s; }

class Secret {
  constructor(value) { this._value = value; }
  expose() { return this._value; }
  toJSON() { return \"[REDACTED]\"; }
  toString() { return \"[REDACTED]\"; }
}

const secret = new Secret(\"sk-proj-super-secret-key\");
const query  = asSqlQuery(\"SELECT * FROM users WHERE id = ?\");

console.log(\"=== Type Safety at Runtime ===\");
console.log(\"Secret in JSON:\", JSON.stringify({ apiKey: secret }));
console.log(\"Secret.toString():\", String(secret));
console.log(\"Secret.expose():\", secret.expose().substring(0, 10) + \"...\");
console.log(\"isSqlQuery(query):\", isSqlQuery(query));
console.log(\"isSqlQuery(rawStr):\", isSqlQuery(\"SELECT 1\"));
  '
"
```

📸 **Verified Output:**
```
=== Type Safety at Runtime ===
Secret in JSON: {"apiKey":"[REDACTED]"}
Secret.toString(): [REDACTED]
Secret.expose(): sk-proj-su...
isSqlQuery(query): true
isSqlQuery(rawStr): false
```

---

## Summary

| Pattern | Type | Prevents |
|---------|------|----------|
| Branded string | `SqlQuery`, `HtmlString` | SQL/XSS injection |
| Opaque ID | `Opaque<string,'UserId'>` | ID confusion bugs |
| Secret wrapper | `Secret<T>` | Accidental logging |
| CSRF token | Branded string | CSRF attacks |
| Permission types | Type intersection | Unauthorized access |
| Validated wrapper | `Validated<T>` | Unvalidated data persistence |
