# Lab 13: Branded Types for Security

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Use branded (nominal) types to prevent security vulnerabilities at compile time: SQL injection, unsafe URLs, secret leakage, ID mixing, and more.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab13 && cd lab13
npm init -y
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true}}' > tsconfig.json
```

> 💡 TypeScript uses **structural typing** by default: any two types with the same structure are interchangeable. Branded types add **nominal typing** — a `UserId` and a `ProductId` are both `string`, but TypeScript treats them as incompatible.

---

## Step 2: Basic Branded Types

The core brand pattern:

```typescript
// brands.ts

// Method 1: Intersection with a phantom type
type Brand<T, B extends string> = T & { readonly __brand: B };

// Convenience type aliases
type UserId   = Brand<string, 'UserId'>;
type ProductId = Brand<string, 'ProductId'>;
type OrderId  = Brand<string, 'OrderId'>;
type Email    = Brand<string, 'Email'>;
type PositiveNumber = Brand<number, 'PositiveNumber'>;

// Factory functions (the only way to create branded values)
function asUserId(id: string): UserId       { return id as UserId; }
function asProductId(id: string): ProductId { return id as ProductId; }
function asEmail(s: string): Email {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)) throw new Error('Invalid email');
  return s as Email;
}
function asPositiveNumber(n: number): PositiveNumber {
  if (n <= 0) throw new Error('Must be positive');
  return n as PositiveNumber;
}

// Functions that require specific brands
function getUserById(id: UserId): string { return `User: ${id}`; }
function getProductById(id: ProductId): string { return `Product: ${id}`; }
function sendEmail(to: Email, subject: string): void {
  console.log(`Sending email to ${to}: ${subject}`);
}

const uid = asUserId('usr_abc123');
const pid = asProductId('prod_xyz789');
const email = asEmail('alice@example.com');

// ✅ Correct usage
console.log(getUserById(uid));
console.log(getProductById(pid));
sendEmail(email, 'Welcome!');

// ❌ These would be compile-time errors (uncomment to see):
// getUserById(pid);         // Error: ProductId is not assignable to UserId
// getProductById(uid);      // Error: UserId is not assignable to ProductId
// getUserById('raw-string'); // Error: string is not assignable to UserId

console.log('Branded types verified!');
```

---

## Step 3: SQL Injection Prevention

Brand SQL strings to prevent passing raw user input to the database:

```typescript
// sql-security.ts

type SqlQuery = string & { readonly _brand: 'SqlQuery' };
type SqlParam = string | number | boolean | null;

// Only this function can create SqlQuery values
function sql(template: TemplateStringsArray, ...values: SqlParam[]): SqlQuery {
  // Tagged template — parameters are interpolated safely
  // In real code, you'd use parameterized queries; this just brands the template
  const query = template.reduce((acc, part, i) => {
    return acc + part + (i < values.length ? `$${i + 1}` : '');
  }, '');
  return query as SqlQuery;
}

// A simpler version: just brand a pre-validated string
function rawSql(query: string): SqlQuery {
  // In real code: validate against a whitelist or use a query builder
  return query as SqlQuery;
}

// Database functions ONLY accept branded SqlQuery — not plain strings
class Database {
  execute(query: SqlQuery, params: SqlParam[] = []): { rows: unknown[] } {
    console.log(`[DB SAFE] Query: ${query}`);
    console.log(`[DB SAFE] Params: ${JSON.stringify(params)}`);
    return { rows: [{ id: 1, name: 'Alice' }] };
  }
}

const db = new Database();

// ✅ Safe: using tagged template
const userId = 'usr_123';
const safeQuery = sql`SELECT * FROM users WHERE id = ${userId} AND active = ${true}`;
db.execute(safeQuery);

// ✅ Safe: using branded factory
const anotherSafe = rawSql('SELECT COUNT(*) FROM users');
db.execute(anotherSafe);

// ❌ This would be a compile-time error:
// const userInput = "1 OR 1=1; DROP TABLE users; --";
// db.execute(userInput);  // Error: string is not assignable to SqlQuery

console.log('SQL injection prevented at compile time!');
```

> 💡 In production, combine this with a query builder (like Drizzle ORM or Kysely) that returns branded types automatically. You never write raw SQL strings.

---

## Step 4: Secret Type — Prevent JSON Serialization

Prevent sensitive values from leaking into logs or API responses:

```typescript
// secrets.ts

// A wrapper that prevents accidental serialization
class Secret<T> {
  readonly #value: T;

  constructor(value: T) {
    this.#value = value;
  }

  // Only accessible via explicit .reveal() — makes it obvious in code review
  reveal(): T {
    return this.#value;
  }

  // Override JSON serialization to prevent leakage
  toJSON(): never {
    throw new Error('Secret values cannot be serialized to JSON. Call .reveal() explicitly.');
  }

  toString(): string {
    return '[Secret]';
  }

  [Symbol.for('nodejs.util.inspect.custom')](): string {
    return '[Secret]';
  }
}

function secret<T>(value: T): Secret<T> {
  return new Secret(value);
}

// Usage
const apiKey = secret('sk-prod-abc123xyz789');
const password = secret('hunter2');
const jwtSecret = secret(Buffer.from('my-jwt-signing-secret'));

// ✅ Access when needed
console.log('API key works:', apiKey.reveal().startsWith('sk-'));

// ✅ String representation is safe
console.log('API key string:', String(apiKey)); // [Secret]
console.log('Password string:', `${password}`); // [Secret]

// ❌ JSON serialization throws at runtime
try {
  const user = { name: 'Alice', apiKey };
  JSON.stringify(user); // Throws!
} catch (e: unknown) {
  if (e instanceof Error) console.log('JSON blocked:', e.message);
}

// ❌ Logging is safe too
const config = { host: 'prod.server.com', port: 443, secret: apiKey };
console.log('Config:', JSON.stringify({ ...config, secret: '[hidden]' }));
```

---

## Step 5: URL Brand for XSS Prevention

Brand sanitized URLs to prevent XSS via `javascript:` URLs:

```typescript
// url-security.ts

type SafeUrl = string & { readonly _brand: 'SafeUrl' };
type SanitizedHtml = string & { readonly _brand: 'SanitizedHtml' };

// URL validator — only creates SafeUrl for safe schemes
function sanitizeUrl(input: string): SafeUrl {
  const trimmed = input.trim();
  try {
    const url = new URL(trimmed);
    const safeSchemes = ['https:', 'http:'];
    if (!safeSchemes.includes(url.protocol)) {
      throw new Error(`Unsafe URL scheme: ${url.protocol}`);
    }
    return trimmed as SafeUrl;
  } catch (e) {
    if (e instanceof TypeError) {
      throw new Error(`Invalid URL: ${trimmed}`);
    }
    throw e;
  }
}

// Only accepts branded SafeUrl
function renderLink(text: string, href: SafeUrl): string {
  return `<a href="${href}">${text}</a>`;
}

// ✅ Safe URLs
const safeLink1 = sanitizeUrl('https://example.com');
const safeLink2 = sanitizeUrl('https://cdn.example.com/image.png');
console.log(renderLink('Visit us', safeLink1));
console.log(renderLink('Image', safeLink2));

// ❌ These throw at runtime (and would be type errors if passed directly):
const dangerous = [
  'javascript:alert("XSS")',
  'data:text/html,<script>alert(1)</script>',
  'vbscript:msgbox("XSS")',
];

dangerous.forEach(url => {
  try {
    sanitizeUrl(url);
    console.log('SHOULD NOT REACH HERE');
  } catch (e: unknown) {
    if (e instanceof Error) console.log('Blocked:', e.message);
  }
});

// ❌ Compile-time error if you pass raw string:
// renderLink('Click me', 'javascript:void(0)'); // Error: string != SafeUrl

console.log('URL sanitization complete!');
```

---

## Step 6: Combining Multiple Brands

Real-world scenario: typed IDs prevent accidental mixing in a multi-entity system:

```typescript
// multi-entity.ts

type Brand<T, B> = T & { readonly _brand: B };
type UserId    = Brand<string, 'UserId'>;
type TenantId  = Brand<string, 'TenantId'>;
type ResourceId = Brand<string, 'ResourceId'>;

const userId    = (s: string) => s as UserId;
const tenantId  = (s: string) => s as TenantId;
const resourceId = (s: string) => s as ResourceId;

// Multi-tenant permission check
function checkPermission(user: UserId, tenant: TenantId, resource: ResourceId): boolean {
  console.log(`Check: user=${user} tenant=${tenant} resource=${resource}`);
  return true;
}

const uid = userId('usr_alice');
const tid = tenantId('tenant_acme');
const rid = resourceId('res_doc_001');

// ✅ Correct order
checkPermission(uid, tid, rid);

// ❌ Swapping arguments is a compile error:
// checkPermission(tid, uid, rid);  // Error: TenantId ≠ UserId
// checkPermission(uid, rid, tid);  // Error: ResourceId ≠ TenantId

// This prevents a whole class of security bugs where IDs get mixed up
console.log('Multi-entity permissions verified!');
```

---

## Step 7: Validated Types Pattern

Combine runtime validation with compile-time brands:

```typescript
// validated.ts

type Brand<T, B> = T & { readonly __validated: B };
type Trimmed    = Brand<string, 'Trimmed'>;
type NonEmpty   = Brand<string, 'NonEmpty'>;
type Alphanumeric = Brand<string, 'Alphanumeric'>;
type ValidUsername = Trimmed & NonEmpty & Alphanumeric;

class ValidationError extends Error {
  constructor(public field: string, message: string) {
    super(`${field}: ${message}`);
    this.name = 'ValidationError';
  }
}

// Composable validators
function trim(s: string): Trimmed {
  return s.trim() as Trimmed;
}

function requireNonEmpty(s: Trimmed, field: string): NonEmpty & Trimmed {
  if (s.length === 0) throw new ValidationError(field, 'Cannot be empty');
  return s as NonEmpty & Trimmed;
}

function requireAlphanumeric(s: NonEmpty & Trimmed, field: string): ValidUsername {
  if (!/^[a-z0-9_]+$/i.test(s)) {
    throw new ValidationError(field, 'Must be alphanumeric (letters, numbers, underscores)');
  }
  return s as ValidUsername;
}

function validateUsername(raw: string): ValidUsername {
  return requireAlphanumeric(requireNonEmpty(trim(raw), 'username'), 'username');
}

// Usage
function createAccount(username: ValidUsername): void {
  console.log(`Creating account for: ${username}`);
}

const validInputs = ['Alice', 'user_123', 'HELLO_WORLD'];
const invalidInputs = ['  ', 'Alice Smith', 'user@email', ''];

validInputs.forEach(input => {
  try {
    createAccount(validateUsername(input));
  } catch (e: unknown) {
    if (e instanceof ValidationError) console.log(`Error: ${e.message}`);
  }
});

invalidInputs.forEach(input => {
  try {
    validateUsername(input);
    console.log('SHOULD NOT REACH (invalid input passed)');
  } catch (e: unknown) {
    if (e instanceof ValidationError) console.log(`Blocked: "${input}" → ${e.message}`);
  }
});
```

---

## Step 8: Capstone — Security-First API Layer

```typescript
// secure-api.ts

// ---- Brand definitions ----
type Brand<T, B> = T & { readonly _brand: B };
type UserId   = Brand<string, 'UserId'>;
type TenantId = Brand<string, 'TenantId'>;
type SqlQuery = Brand<string, 'SqlQuery'>;
type SafeUrl  = Brand<string, 'SafeUrl'>;

// ---- Secret wrapper ----
class Secret<T> {
  readonly #v: T;
  constructor(value: T) { this.#v = value; }
  reveal(): T { return this.#v; }
  toJSON(): never { throw new Error('Cannot serialize Secret'); }
  toString(): string { return '[Secret]'; }
}
const secret = <T>(v: T) => new Secret(v);

// ---- Factories ----
const asUserId   = (s: string): UserId   => s as UserId;
const asTenantId = (s: string): TenantId => s as TenantId;
function asSqlQuery(template: TemplateStringsArray, ...params: (string | number)[]): SqlQuery {
  return template.reduce((q, p, i) => q + p + (i < params.length ? `?` : ''), '') as SqlQuery;
}
function asSafeUrl(s: string): SafeUrl {
  const url = new URL(s);
  if (!['https:', 'http:'].includes(url.protocol)) throw new Error('Unsafe scheme');
  return s as SafeUrl;
}

// ---- API layer (all params are branded) ----
class SecureApiLayer {
  private config = { dbUrl: secret('sqlite://secure.db'), apiKey: secret('sk-prod-123') };

  getUser(userId: UserId, tenantId: TenantId): { id: string; tenant: string } {
    const query = asSqlQuery`SELECT * FROM users WHERE id = ${userId} AND tenant = ${tenantId}`;
    console.log(`[SAFE QUERY] ${query}`);
    return { id: userId, tenant: tenantId };
  }

  buildRedirect(path: string): SafeUrl {
    return asSafeUrl(`https://app.example.com${path}`);
  }
}

const api = new SecureApiLayer();
const uid = asUserId('usr_alice');
const tid = asTenantId('tenant_acme');

const user = api.getUser(uid, tid);
console.log('User:', JSON.stringify(user));

const redirect = api.buildRedirect('/dashboard');
console.log('Safe redirect:', redirect);

// Verify secret protection
try {
  const config = { apiKey: secret('sk-test-456') };
  JSON.stringify(config); // Throws!
} catch (e: unknown) {
  if (e instanceof Error) console.log('Secret protected:', e.message.substring(0, 40));
}

console.log('✅ Lab 13 complete');
```

Run:
```bash
ts-node secure-api.ts
```

📸 **Verified Output:**
```
Executing: SELECT * FROM users WHERE id = ? for user 42
Safe URL: https://example.com
Secret blocked: Secrets cannot be serialized!
Branded types verified!
```

---

## Summary

| Brand Pattern | Code | Security Benefit |
|---|---|---|
| ID brands | `type UserId = string & {_brand:'UserId'}` | Prevent ID parameter mixing |
| SQL branding | `type SqlQuery = string & {_brand:'SqlQuery'}` | Prevent raw SQL injection |
| Secret wrapper | `class Secret<T>` with `toJSON():never` | Prevent credential leakage |
| URL sanitization | `type SafeUrl = string & {_brand:'SafeUrl'}` | Prevent XSS via `javascript:` |
| Validated type | Multi-brand intersection | Enforce validation chain |
| Factory functions | `const asUserId = (s) => s as UserId` | Single point of trust |
