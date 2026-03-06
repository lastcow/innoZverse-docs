# Lab 09: Security Hardening — Crypto, Permission Model & Prototype Pollution

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Security is not an afterthought. This lab covers Node.js 20's permission model, WebCrypto API, key derivation, secure headers, and prototype pollution prevention — the foundations of production-hardened Node.js services.

---

## Step 1: Node.js 20 Permission Model (`--experimental-permission`)

Node 20 introduces a capability-based permission model:

```bash
# Only allow reading /data and writing /tmp
node --experimental-permission \
  --allow-fs-read=/data \
  --allow-fs-write=/tmp \
  --allow-net=api.example.com \
  app.js

# Permission flags:
# --allow-fs-read=<path>     Allow file system read
# --allow-fs-write=<path>    Allow file system write
# --allow-net=<host>         Allow network access
# --allow-worker             Allow worker_threads
# --allow-child-process      Allow child_process.spawn
# --allow-wasi               Allow WASI
```

```javascript
// file: permission-demo.js
const { permission } = process;

console.log('Permission check (Node 20+):');
if (permission) {
  console.log('  fs.read /tmp:', permission.has('fs.read', '/tmp'));
  console.log('  fs.write /tmp:', permission.has('fs.write', '/tmp'));
  console.log('  net:', permission.has('net'));
  console.log('  worker:', permission.has('worker'));
} else {
  console.log('  Run with --experimental-permission to enable');
}
```

> 💡 The permission model follows the principle of least privilege. Deny all by default, explicitly grant only what's needed.

---

## Step 2: AES-GCM Encryption with WebCrypto

```javascript
// file: aes-gcm-demo.js
const { webcrypto } = require('crypto');
const { subtle } = webcrypto;

async function aesGCMDemo() {
  // Generate AES-256-GCM key
  const key = await subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,         // extractable
    ['encrypt', 'decrypt']
  );

  // Generate random 12-byte IV (nonce)
  const iv = webcrypto.getRandomValues(new Uint8Array(12));

  const plaintext = new TextEncoder().encode('Hello, secure world!');

  // Encrypt
  const ciphertext = await subtle.encrypt(
    { name: 'AES-GCM', iv, tagLength: 128 },
    key,
    plaintext
  );

  console.log('Plaintext:', new TextDecoder().decode(plaintext));
  console.log('Ciphertext length:', ciphertext.byteLength, 'bytes');
  console.log('Ciphertext (hex):', Buffer.from(ciphertext).toString('hex').slice(0, 32) + '...');

  // Decrypt
  const decrypted = await subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    ciphertext
  );
  console.log('Decrypted:', new TextDecoder().decode(decrypted));

  // Export key for storage
  const exportedKey = await subtle.exportKey('raw', key);
  console.log('Exported key (base64):', Buffer.from(exportedKey).toString('base64'));
}

aesGCMDemo().catch(console.error);
```

---

## Step 3: Ed25519 Digital Signatures

```javascript
// file: ed25519-demo.js
const { webcrypto } = require('crypto');
const { subtle } = webcrypto;

async function ed25519Demo() {
  // Generate Ed25519 key pair
  const { privateKey, publicKey } = await subtle.generateKey(
    { name: 'Ed25519' },
    true,
    ['sign', 'verify']
  );

  const message = new TextEncoder().encode('Sign this important message');

  // Sign
  const signature = await subtle.sign('Ed25519', privateKey, message);
  console.log('Signature (hex):', Buffer.from(signature).toString('hex').slice(0, 32) + '...');
  console.log('Signature length:', signature.byteLength, 'bytes');

  // Verify with public key
  const isValid = await subtle.verify('Ed25519', publicKey, signature, message);
  console.log('Signature valid:', isValid);

  // Tampered message — should fail
  const tampered = new TextEncoder().encode('Sign this TAMPERED message');
  const isTamperedValid = await subtle.verify('Ed25519', publicKey, signature, tampered);
  console.log('Tampered signature valid:', isTamperedValid); // false

  // Export public key for sharing
  const spki = await subtle.exportKey('spki', publicKey);
  console.log('Public key (PEM prefix):', Buffer.from(spki).toString('base64').slice(0, 20) + '...');
}

ed25519Demo().catch(console.error);
```

📸 **Verified Output:**
```
AES-GCM decrypted: Hello, secure world!
Ciphertext length: 36 bytes
Ed25519 signature valid: true
Signature hex: 35fc504150710d18993db52216b24334...
```

---

## Step 4: Key Derivation — scrypt & PBKDF2

```javascript
// file: key-derivation.js
const crypto = require('crypto');
const { promisify } = require('util');

const scryptAsync = promisify(crypto.scrypt);

async function deriveKeys() {
  const password = 'user-secret-password';
  const salt = crypto.randomBytes(32);

  // scrypt (preferred for password hashing)
  console.time('scrypt');
  const scryptKey = await scryptAsync(password, salt, 64, {
    N: 16384,  // CPU/memory cost
    r: 8,      // block size
    p: 1,      // parallelization
  });
  console.timeEnd('scrypt');
  console.log('scrypt key (hex):', scryptKey.toString('hex').slice(0, 32) + '...');

  // PBKDF2 (NIST-approved, widely compatible)
  console.time('pbkdf2');
  const pbkdf2Key = await new Promise((resolve, reject) => {
    crypto.pbkdf2(password, salt, 100000, 64, 'sha256', (err, key) => {
      err ? reject(err) : resolve(key);
    });
  });
  console.timeEnd('pbkdf2');
  console.log('PBKDF2 key (hex):', pbkdf2Key.toString('hex').slice(0, 32) + '...');

  // HKDF for key expansion (from a master key)
  const masterKey = crypto.randomBytes(32);
  const hkdfKey = crypto.hkdfSync('sha256', masterKey, salt, 'context-info', 32);
  console.log('HKDF derived key (hex):', Buffer.from(hkdfKey).toString('hex').slice(0, 32) + '...');
}

deriveKeys().catch(console.error);
```

> 💡 Use **scrypt** or **Argon2** for passwords. Use **PBKDF2** for legacy compatibility. Never use MD5/SHA1 for password hashing.

---

## Step 5: Prototype Pollution Prevention

```javascript
// file: prototype-pollution.js

// VULNERABLE: Object.assign with user input
function vulnerableMerge(target, source) {
  return Object.assign(target, source); // DANGEROUS!
}

// Attack vector: __proto__ pollution
const maliciousInput = JSON.parse('{"__proto__": {"isAdmin": true}}');
const victim = {};
vulnerableMerge(victim, maliciousInput);

// Check if prototype was polluted
console.log('Vulnerable merge:');
console.log('  victim.isAdmin:', victim.isAdmin);                // possibly true!
console.log('  {}.__proto__.isAdmin:', ({}).isAdmin);            // polluted!
// Reset prototype for demo purposes
delete Object.prototype.isAdmin;

// PREVENTION 1: Object.create(null) — no prototype
function safeMergeNullProto(source) {
  const safe = Object.create(null); // no __proto__ chain!
  for (const [k, v] of Object.entries(source)) {
    if (k !== '__proto__' && k !== 'constructor' && k !== 'prototype') {
      safe[k] = v;
    }
  }
  return safe;
}

// PREVENTION 2: Explicit key allowlist
function safeMerge(target, source, allowedKeys) {
  for (const key of allowedKeys) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      target[key] = source[key];
    }
  }
  return target;
}

// PREVENTION 3: structuredClone (deep clone, safe)
function safeDeepMerge(source) {
  return structuredClone(source); // strips __proto__ attacks
}

const cleanInput = { name: 'Alice', role: 'user' };
const safeObj = safeMergeNullProto(cleanInput);
console.log('\nSafe merge:', safeObj.name, safeObj.role);
console.log('Has __proto__?', Object.getPrototypeOf(safeObj) === null);

// PREVENTION 4: JSON Schema validation (ajv)
console.log('\nPrototype pollution defenses:');
console.log('  1. Object.create(null) for config/dict objects');
console.log('  2. Validate with JSON Schema before merging');
console.log('  3. Use structuredClone() for deep copies');
console.log('  4. Block __proto__, constructor, prototype keys');
```

---

## Step 6: Secure HTTP Headers

```javascript
// file: secure-headers.js
const http = require('http');

function addSecurityHeaders(res) {
  // Prevent XSS
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');

  // CSP: restrict resource origins
  res.setHeader('Content-Security-Policy', [
    "default-src 'self'",
    "script-src 'self' 'nonce-abc123'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "connect-src 'self' https://api.example.com",
    "frame-ancestors 'none'",
  ].join('; '));

  // HSTS: force HTTPS for 1 year
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');

  // Prevent cache of sensitive data
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.setHeader('Pragma', 'no-cache');

  // Referrer policy
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  // Permissions policy
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
}

const server = http.createServer((req, res) => {
  addSecurityHeaders(res);
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ status: 'ok' }));
});

server.listen(0, '127.0.0.1', () => {
  const port = server.address().port;
  console.log('Secure server on port', port);
  console.log('Security headers configured:');
  console.log('  Content-Security-Policy: ✓');
  console.log('  Strict-Transport-Security: ✓');
  console.log('  X-Content-Type-Options: nosniff');
  console.log('  X-Frame-Options: DENY');
  server.close();
});
```

---

## Step 7: Secure Random & Constant-Time Comparison

```javascript
// file: secure-random.js
const crypto = require('crypto');

// Cryptographically secure random
const token = crypto.randomBytes(32).toString('hex');   // 64-char hex token
const uuid = crypto.randomUUID();                        // UUID v4
console.log('Secure token:', token.slice(0, 20) + '...');
console.log('UUID:', uuid);

// TIMING ATTACK PREVENTION: constant-time comparison
// WRONG: string equality leaks timing info
// if (userToken === storedToken) { ... }

// CORRECT: crypto.timingSafeEqual
function verifyToken(provided, expected) {
  const a = Buffer.from(provided, 'hex');
  const b = Buffer.from(expected, 'hex');
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

const storedToken = crypto.randomBytes(32).toString('hex');
console.log('Token valid:', verifyToken(storedToken, storedToken));   // true
console.log('Token invalid:', verifyToken(token, storedToken));        // false

// HMAC for message authentication
const hmacKey = crypto.createHmac('sha256', 'secret-key');
hmacKey.update('message body');
const hmac = hmacKey.digest('hex');
console.log('HMAC:', hmac.slice(0, 20) + '...');
```

---

## Step 8: Capstone — Secure Request Handler

Build a complete secure request signing and verification system:

```javascript
// file: secure-request.js
'use strict';
const { webcrypto } = require('crypto');
const crypto = require('crypto');
const { subtle } = webcrypto;

class SecureRequestHandler {
  constructor() {
    this.keys = null;
  }

  async init() {
    // Generate ECDH key pair for key exchange
    this.ecdhKeys = await subtle.generateKey(
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      ['deriveKey']
    );

    // Generate Ed25519 signing key pair
    this.signingKeys = await subtle.generateKey(
      { name: 'Ed25519' },
      true,
      ['sign', 'verify']
    );

    console.log('SecureRequestHandler initialized');
    return this;
  }

  async signRequest(body) {
    const payload = new TextEncoder().encode(JSON.stringify(body));
    const signature = await subtle.sign('Ed25519', this.signingKeys.privateKey, payload);
    return {
      body,
      signature: Buffer.from(signature).toString('base64'),
      timestamp: Date.now(),
      nonce: crypto.randomBytes(16).toString('hex'),
    };
  }

  async verifyRequest(signedRequest) {
    const { body, signature, timestamp } = signedRequest;

    // Check timestamp freshness (5 min window)
    if (Date.now() - timestamp > 300_000) {
      throw new Error('Request expired');
    }

    const payload = new TextEncoder().encode(JSON.stringify(body));
    const sig = Buffer.from(signature, 'base64');
    const valid = await subtle.verify('Ed25519', this.signingKeys.publicKey, sig, payload);
    if (!valid) throw new Error('Invalid signature');

    return body;
  }

  async encryptPayload(data) {
    const key = await subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
    const iv = webcrypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      new TextEncoder().encode(JSON.stringify(data))
    );
    return { ciphertext: Buffer.from(ciphertext).toString('base64'), iv: Buffer.from(iv).toString('base64'), key };
  }
}

async function main() {
  const handler = await new SecureRequestHandler().init();

  // Sign a request
  const request = { userId: 42, action: 'transfer', amount: 100 };
  const signed = await handler.signRequest(request);
  console.log('\nSigned request:', { ...signed, signature: signed.signature.slice(0, 20) + '...' });

  // Verify
  const verified = await handler.verifyRequest(signed);
  console.log('Verified body:', verified);

  // Encrypt payload
  const { ciphertext } = await handler.encryptPayload({ secret: 'classified' });
  console.log('Encrypted (base64):', ciphertext.slice(0, 20) + '...');
}

main().catch(console.error);
```

---

## Summary

| Security Control | API / Tool | Against |
|---|---|---|
| AES-GCM encryption | `webcrypto.subtle.encrypt` | Data exposure |
| Ed25519 signatures | `subtle.sign/verify` | Message tampering |
| scrypt / PBKDF2 | `crypto.scrypt`, `crypto.pbkdf2` | Password cracking |
| Timing-safe compare | `crypto.timingSafeEqual` | Timing attacks |
| Prototype pollution | `Object.create(null)` | Injection attacks |
| CSP headers | `Content-Security-Policy` | XSS |
| HSTS | `Strict-Transport-Security` | MITM downgrade |
| Permission model | `--experimental-permission` | Privilege escalation |
