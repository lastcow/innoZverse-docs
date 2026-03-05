# Lab 10: Node.js Core Modules

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master Node.js built-in modules: `fs` (promises API), `path`, `os`, `crypto` (UUID/hashing/HMAC), `Buffer`, and stream basics — all without installing dependencies.

---

## Step 1: fs/promises — File System

```javascript
const fs = require('node:fs/promises');
const path = require('node:path');

// Writing, reading, and working with files
async function fileOperations() {
  const tmpDir = '/tmp/node-lab';

  // Create directory (recursive = no error if exists)
  await fs.mkdir(tmpDir, { recursive: true });

  // Write a file
  await fs.writeFile(path.join(tmpDir, 'hello.txt'), 'Hello, Node.js!\n', 'utf8');

  // Append to file
  await fs.appendFile(path.join(tmpDir, 'hello.txt'), 'Second line\n');

  // Read file
  const content = await fs.readFile(path.join(tmpDir, 'hello.txt'), 'utf8');
  console.log('File content:', content.trim());

  // Write JSON
  const data = { users: ['Alice', 'Bob'], count: 2 };
  await fs.writeFile(
    path.join(tmpDir, 'data.json'),
    JSON.stringify(data, null, 2)
  );

  // Read JSON
  const raw = await fs.readFile(path.join(tmpDir, 'data.json'), 'utf8');
  console.log('JSON data:', JSON.parse(raw).count, 'users');

  // List directory
  const files = await fs.readdir(tmpDir);
  console.log('Files:', files);

  // File stats
  const stats = await fs.stat(path.join(tmpDir, 'hello.txt'));
  console.log('File size:', stats.size, 'bytes');
  console.log('Is file:', stats.isFile());

  // Cleanup
  await fs.rm(tmpDir, { recursive: true });
}

fileOperations().catch(console.error);
```

> 💡 Always use `node:fs/promises` (the promise-based API) over the callback-based `fs`. Add the `node:` prefix to make it clear it's a built-in.

---

## Step 2: path — Working with File Paths

```javascript
const path = require('node:path');

// Basic path operations
console.log(path.join('/usr', 'local', 'bin'));       // /usr/local/bin
console.log(path.join('/usr', '../etc', 'hosts'));    // /etc/hosts
console.log(path.resolve('relative', 'path'));         // Absolute path

// Parse and format
const parsed = path.parse('/home/user/documents/file.test.js');
console.log(parsed);
// {
//   root: '/',
//   dir: '/home/user/documents',
//   base: 'file.test.js',
//   ext: '.js',
//   name: 'file.test'
// }

const formatted = path.format({
  dir: '/home/user',
  name: 'script',
  ext: '.js'
});
console.log(formatted); // /home/user/script.js

// Common path utilities
console.log(path.dirname('/home/user/file.js'));  // /home/user
console.log(path.basename('/home/user/file.js')); // file.js
console.log(path.basename('/path/to/file.test.js', '.js')); // file.test
console.log(path.extname('archive.tar.gz'));       // .gz

// Normalize (remove ../ and ./)
console.log(path.normalize('/usr/./local/../lib')); // /usr/lib

// Check if absolute
console.log(path.isAbsolute('/etc/hosts'));   // true
console.log(path.isAbsolute('relative/path')); // false

// Relative path between two paths
console.log(path.relative('/home/user', '/home/user/docs/file.js')); // docs/file.js
```

---

## Step 3: os — Operating System Info

```javascript
const os = require('node:os');
const path = require('node:path');

// System information
console.log('Platform:', os.platform());    // linux/darwin/win32
console.log('Architecture:', os.arch());    // x64/arm64
console.log('Node version:', process.version); // v20.x.x
console.log('Hostname:', os.hostname());

// Memory
const totalMem = os.totalmem();
const freeMem = os.freemem();
console.log(`Memory: ${(freeMem / 1e9).toFixed(1)}GB free of ${(totalMem / 1e9).toFixed(1)}GB`);

// CPUs
const cpus = os.cpus();
console.log(`CPUs: ${cpus.length}x ${cpus[0].model}`);

// User info
const user = os.userInfo();
console.log('User:', user.username);
console.log('Home:', user.homedir);
console.log('Tmp:', os.tmpdir());

// Network interfaces
const interfaces = os.networkInterfaces();
const loopback = interfaces['lo']?.[0];
if (loopback) console.log('Loopback IP:', loopback.address);

// System uptime
console.log('Uptime:', Math.round(os.uptime() / 60), 'minutes');

// OS constants
console.log('EOL:', os.EOL === '\n' ? '\\n (Unix)' : '\\r\\n (Windows)');
console.log('Path delimiter:', path.delimiter); // : or ;
```

---

## Step 4: crypto — Cryptographic Operations

```javascript
const { randomUUID, createHash, createHmac, randomBytes, scryptSync, timingSafeEqual } = require('node:crypto');

// Random UUID (v4)
const id1 = randomUUID();
const id2 = randomUUID();
console.log('UUID:', id1);
console.log('Unique:', id1 !== id2); // true

// Hashing
function hash(data, algorithm = 'sha256') {
  return createHash(algorithm).update(data).digest('hex');
}
console.log('MD5:', hash('hello', 'md5'));
console.log('SHA256:', hash('hello').slice(0, 16) + '...');

// HMAC — for message authentication
function hmac(key, data) {
  return createHmac('sha256', key).update(data).digest('hex');
}
const signature = hmac('secret-key', 'important message');
console.log('HMAC:', signature.slice(0, 16) + '...');

// Password hashing with scrypt
function hashPassword(password) {
  const salt = randomBytes(16);
  const key = scryptSync(password, salt, 64);
  return salt.toString('hex') + ':' + key.toString('hex');
}

function verifyPassword(password, hash) {
  const [saltHex, keyHex] = hash.split(':');
  const salt = Buffer.from(saltHex, 'hex');
  const key = Buffer.from(keyHex, 'hex');
  const derived = scryptSync(password, salt, 64);
  return timingSafeEqual(key, derived); // Constant-time comparison
}

const passwordHash = hashPassword('my-secure-password');
console.log('Verify correct:', verifyPassword('my-secure-password', passwordHash));
console.log('Verify wrong:', verifyPassword('wrong-password', passwordHash));
```

---

## Step 5: Buffer — Binary Data

```javascript
// Creating Buffers
const buf1 = Buffer.alloc(8);          // 8 bytes, zeroed
const buf2 = Buffer.alloc(8, 0xFF);    // 8 bytes, filled with 0xFF
const buf3 = Buffer.from('Hello!');    // From string (UTF-8 by default)
const buf4 = Buffer.from([0x48, 0x65, 0x6c, 0x6c, 0x6f]); // From bytes

console.log(buf1);    // <Buffer 00 00 00 00 00 00 00 00>
console.log(buf3.toString()); // Hello!

// Encoding conversions
const str = 'Hello, 世界!';
const utf8Buf = Buffer.from(str, 'utf8');
console.log('UTF-8 bytes:', utf8Buf.length); // 17 (multibyte chars)
console.log('Hex:', utf8Buf.toString('hex').slice(0, 20) + '...');
console.log('Base64:', utf8Buf.toString('base64'));

// Back to string
const decoded = Buffer.from(utf8Buf.toString('base64'), 'base64').toString('utf8');
console.log('Decoded:', decoded); // Hello, 世界!

// Concatenate
const part1 = Buffer.from('Hello, ');
const part2 = Buffer.from('World!');
const combined = Buffer.concat([part1, part2]);
console.log(combined.toString()); // Hello, World!

// Copy
const source = Buffer.from([1, 2, 3, 4, 5]);
const dest = Buffer.alloc(3);
source.copy(dest, 0, 1, 4); // dest, destStart, sourceStart, sourceEnd
console.log(dest); // <Buffer 02 03 04>

// Slice (shares memory with original)
const slice = source.subarray(1, 4);
console.log(slice); // <Buffer 02 03 04>
```

---

## Step 6: Stream Basics

```javascript
const { Readable, Writable, Transform, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

// Readable stream from string
async function readableFromString() {
  const chunks = [];
  const readable = Readable.from(['chunk1 ', 'chunk2 ', 'chunk3']);
  for await (const chunk of readable) chunks.push(chunk);
  console.log('Readable:', chunks.join(''));
}

// Custom Transform
class CounterTransform extends Transform {
  #count = 0;
  _transform(chunk, encoding, callback) {
    this.#count++;
    this.push(chunk); // Pass through
    callback();
  }
  get count() { return this.#count; }
}

// Pipeline
async function pipelineDemo() {
  const chunks = [];
  const counter = new CounterTransform();

  await pipelineAsync(
    Readable.from(['hello ', 'world', '!']),
    counter,
    new Writable({
      write(chunk, enc, cb) { chunks.push(chunk.toString()); cb(); }
    })
  );

  console.log('Output:', chunks.join(''));
  console.log('Chunks processed:', counter.count);
}

readableFromString();
pipelineDemo();
```

---

## Step 7: Useful Utility Modules

```javascript
const { promisify, callbackify, inspect, isDeepStrictEqual } = require('node:util');
const { EventEmitter } = require('node:events');

// promisify — convert callback-style to promise
const sleep = promisify(setTimeout);
(async () => {
  await sleep(10);
  console.log('Slept 10ms');
})();

// Deep equality check
const obj1 = { a: 1, b: { c: [1, 2, 3] } };
const obj2 = { a: 1, b: { c: [1, 2, 3] } };
console.log(isDeepStrictEqual(obj1, obj2)); // true
console.log(obj1 === obj2); // false (different references)

// util.inspect — better console output
const complex = { fn: () => {}, sym: Symbol('test'), buf: Buffer.from('hi') };
console.log(inspect(complex, { depth: 2, colors: false }));

// EventEmitter patterns
const emitter = new EventEmitter();
emitter.setMaxListeners(20); // Increase from default 10
const { once } = require('node:events');
(async () => {
  const promise = once(emitter, 'ready'); // Wait for single event
  setTimeout(() => emitter.emit('ready', 'GO!'), 10);
  const [value] = await promise;
  console.log('Ready event:', value);
})();
```

---

## Step 8: Capstone — Core Modules All Together

```javascript
const { randomUUID, createHash, createHmac } = require('node:crypto');
const { platform, cpus, totalmem, freemem } = require('node:os');
const path = require('node:path');

console.log('UUID:', randomUUID());
console.log('SHA256:', createHash('sha256').update('hello').digest('hex').slice(0,16) + '...');
console.log('HMAC:', createHmac('sha256', 'secret').update('data').digest('hex').slice(0,16) + '...');
console.log('Platform:', platform());
console.log('Path join:', path.join('/usr', 'local', 'bin'));
console.log('Path ext:', path.extname('file.test.js'));
const buf = Buffer.from('Hello, World!');
console.log('Buffer hex:', buf.toString('hex').slice(0,20) + '...');
console.log('Buffer base64:', buf.toString('base64'));
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const { randomUUID, createHash, createHmac } = require(\"crypto\");
const { platform, cpus, totalmem, freemem } = require(\"os\");
const path = require(\"path\");
console.log(\"UUID:\", randomUUID());
console.log(\"SHA256:\", createHash(\"sha256\").update(\"hello\").digest(\"hex\").slice(0,16) + \"...\");
console.log(\"HMAC:\", createHmac(\"sha256\", \"secret\").update(\"data\").digest(\"hex\").slice(0,16) + \"...\");
console.log(\"Platform:\", platform());
console.log(\"Path join:\", path.join(\"/usr\", \"local\", \"bin\"));
console.log(\"Path ext:\", path.extname(\"file.test.js\"));
const buf = Buffer.from(\"Hello, World!\");
console.log(\"Buffer hex:\", buf.toString(\"hex\").slice(0,20) + \"...\");
console.log(\"Buffer base64:\", buf.toString(\"base64\"));
'"
```

📸 **Verified Output:**
```
UUID: dec11e52-e445-46ea-aa25-64da84ddc779
SHA256: 2cf24dba5fb0a30e...
HMAC: 1b2c16b75bd2a870...
Platform: linux
Path join: /usr/local/bin
Path ext: .js
Buffer hex: 48656c6c6f2c20576f72...
Buffer base64: SGVsbG8sIFdvcmxkIQ==
```

*(UUIDs are random — your UUID will differ)*

---

## Summary

| Module | Key APIs | Use Case |
|--------|---------|----------|
| `node:fs/promises` | `readFile`, `writeFile`, `mkdir`, `stat` | File I/O operations |
| `node:path` | `join`, `resolve`, `parse`, `basename`, `extname` | Cross-platform paths |
| `node:os` | `platform()`, `cpus()`, `totalmem()`, `tmpdir()` | System information |
| `node:crypto` | `randomUUID`, `createHash`, `createHmac`, `scryptSync` | Cryptography |
| `Buffer` | `from`, `alloc`, `concat`, `copy`, `toString` | Binary data handling |
| `node:stream` | `Readable`, `Writable`, `Transform`, `pipeline` | Streaming data |
| `node:util` | `promisify`, `inspect`, `isDeepStrictEqual` | Utilities |
