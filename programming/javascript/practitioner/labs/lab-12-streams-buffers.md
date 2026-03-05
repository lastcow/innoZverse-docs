# Lab 12: Streams & Buffers

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master Node.js streams: Readable, Writable, Transform, and Duplex streams; piping; backpressure; `stream.pipeline`; and Buffer operations (alloc/from/concat/copy/slice).

---

## Step 1: Readable Streams

```javascript
const { Readable } = require('node:stream');

// Create from iterable
const fromArray = Readable.from([1, 2, 3, 4, 5]);
fromArray.on('data', chunk => process.stdout.write(String(chunk) + ' '));
fromArray.on('end', () => console.log('(end)'));

// Create custom Readable
class NumberStream extends Readable {
  constructor(start, end, options) {
    super({ ...options, objectMode: true });
    this.current = start;
    this.end = end;
  }
  _read() {
    if (this.current <= this.end) {
      this.push(this.current++);
    } else {
      this.push(null); // Signal end
    }
  }
}

const nums = new NumberStream(1, 5);
(async () => {
  for await (const n of nums) {
    process.stdout.write(n + ' ');
  }
  console.log();
})();

// Consuming with async iteration (recommended modern approach)
async function readAll(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return chunks;
}
```

---

## Step 2: Writable Streams

```javascript
const { Writable } = require('node:stream');

// Custom writable — collect chunks
class CollectorStream extends Writable {
  #chunks = [];
  #encoding;

  constructor(encoding = 'utf8') {
    super();
    this.#encoding = encoding;
  }

  _write(chunk, encoding, callback) {
    this.#chunks.push(chunk);
    callback(); // Signal ready for more data
  }

  getContent() {
    return Buffer.concat(this.#chunks).toString(this.#encoding);
  }
}

// Usage
const collector = new CollectorStream();
collector.write('Hello, ');
collector.write('World');
collector.write('!');
collector.end();
collector.on('finish', () => {
  console.log('Collected:', collector.getContent()); // Hello, World!
});

// Backpressure — handle drain event
function writeWithBackpressure(writable, data) {
  return new Promise((resolve, reject) => {
    const canContinue = writable.write(data);
    if (!canContinue) {
      writable.once('drain', resolve);
    } else {
      resolve();
    }
  });
}
```

> 💡 Always handle backpressure! If `write()` returns `false`, wait for the `'drain'` event before writing more.

---

## Step 3: Transform Streams

```javascript
const { Transform } = require('node:stream');

// UpperCase transform
class UpperCaseTransform extends Transform {
  _transform(chunk, encoding, callback) {
    callback(null, chunk.toString().toUpperCase());
  }
}

// Line counter transform
class LineCounter extends Transform {
  #count = 0;

  _transform(chunk, encoding, callback) {
    const lines = chunk.toString().split('\n');
    this.#count += lines.length - 1;
    callback(null, chunk); // Pass through unchanged
  }

  _flush(callback) {
    this.emit('lineCount', this.#count);
    callback();
  }

  get lineCount() { return this.#count; }
}

// JSON stringify transform (object mode -> string)
class JSONStringifyTransform extends Transform {
  constructor() {
    super({ writableObjectMode: true, readableObjectMode: false });
  }
  _transform(obj, encoding, callback) {
    callback(null, JSON.stringify(obj) + '\n');
  }
}

// Compose transforms
const { Readable, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);
```

---

## Step 4: Duplex Streams

```javascript
const { Duplex } = require('node:stream');

// Duplex — both readable and writable (independent)
class EchoStream extends Duplex {
  _read() {} // Nothing to push proactively

  _write(chunk, encoding, callback) {
    this.push(chunk.toString().toUpperCase()); // Echo back uppercased
    callback();
  }
}

const echo = new EchoStream();
echo.on('data', chunk => console.log('Echo:', chunk.toString()));
echo.write('hello');
echo.write('world');
echo.end();

// PassThrough — transparent stream (useful for inserting into pipelines)
const { PassThrough } = require('node:stream');
const spy = new PassThrough();
spy.on('data', chunk => console.log('Data flowing:', chunk.length, 'bytes'));
```

---

## Step 5: Pipeline

```javascript
const { Readable, Writable, Transform, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

class UpperCaseTransform extends Transform {
  _transform(chunk, enc, cb) {
    cb(null, chunk.toString().toUpperCase());
  }
}

class CSVParser extends Transform {
  #headers = null;
  constructor() { super({ objectMode: true }); }
  _transform(chunk, enc, cb) {
    const lines = chunk.toString().split('\n').filter(Boolean);
    for (const line of lines) {
      const values = line.split(',');
      if (!this.#headers) { this.#headers = values; continue; }
      const obj = Object.fromEntries(this.#headers.map((h, i) => [h, values[i]]));
      this.push(obj);
    }
    cb();
  }
}

// Pipeline with error handling
async function processStream() {
  const results = [];
  const upper = new UpperCaseTransform();
  const collect = new Writable({
    write(chunk, enc, cb) { results.push(chunk.toString()); cb(); }
  });

  await pipelineAsync(
    Readable.from(['hello ', 'world', '!']),
    upper,
    collect
  );

  return results.join('');
}

processStream().then(r => console.log('Pipeline result:', r));
```

---

## Step 6: Buffer Deep Dive

```javascript
// Creating buffers
const buf1 = Buffer.alloc(8);         // Zeroed
const buf2 = Buffer.alloc(8, 0xAB);  // Filled
const buf3 = Buffer.from('Hello');
const buf4 = Buffer.from([72, 101, 108, 108, 111]); // ASCII

// Reading/writing numbers
const numBuf = Buffer.alloc(16);
numBuf.writeInt32LE(123456789, 0);  // Little-endian 32-bit int at offset 0
numBuf.writeInt32BE(987654321, 4);  // Big-endian 32-bit int at offset 4
numBuf.writeDoubleBE(3.14159, 8);   // 64-bit double at offset 8

console.log(numBuf.readInt32LE(0)); // 123456789
console.log(numBuf.readInt32BE(4)); // 987654321
console.log(numBuf.readDoubleBE(8).toFixed(5)); // 3.14159

// Encodings
const text = 'Hello, 世界';
const buffers = {
  utf8: Buffer.from(text, 'utf8'),
  hex: Buffer.from('48656c6c6f', 'hex'),
  base64: Buffer.from('SGVsbG8=', 'base64'),
};
console.log('utf8 length:', buffers.utf8.length);     // 13 bytes (multibyte CJK)
console.log('hex decoded:', buffers.hex.toString());  // Hello
console.log('b64 decoded:', buffers.base64.toString()); // Hello
```

---

## Step 7: Backpressure and highWaterMark

```javascript
const { Readable, Writable } = require('node:stream');

// highWaterMark controls the internal buffer size
const fastReadable = new Readable({
  highWaterMark: 1024, // 1KB buffer
  read(size) {
    this.push(Buffer.alloc(size, 'x')); // Push data
    this.push(null); // End
  }
});

const slowWritable = new Writable({
  highWaterMark: 512, // 512B buffer
  write(chunk, enc, callback) {
    // Simulate slow write
    setTimeout(callback, 10);
  }
});

// Without backpressure handling — can OOM
fastReadable.pipe(slowWritable); // pipe() handles backpressure automatically!

// Manual backpressure
async function copyWithBackpressure(readable, writable) {
  for await (const chunk of readable) {
    const canContinue = writable.write(chunk);
    if (!canContinue) {
      await new Promise(resolve => writable.once('drain', resolve));
    }
  }
  writable.end();
}
```

---

## Step 8: Capstone — Stream Pipeline

```javascript
const { Readable, Writable, Transform, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

class UpperCaseTransform extends Transform {
  _transform(chunk, enc, cb) { cb(null, chunk.toString().toUpperCase()); }
}

const buf1 = Buffer.alloc(4, 0);
const buf2 = Buffer.from([1, 2, 3, 4]);
const combined = Buffer.concat([buf1, buf2]);
console.log('Combined:', combined);

(async () => {
  const chunks = [];
  const readable = Readable.from(['hello ', 'world', '!']);
  const upper = new UpperCaseTransform();
  const writable = new Writable({
    write(chunk, enc, cb) { chunks.push(chunk.toString()); cb(); }
  });
  await pipelineAsync(readable, upper, writable);
  console.log('Result:', chunks.join(''));
})();
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const { Readable, Writable, Transform, pipeline } = require(\"stream\");
const { promisify } = require(\"util\");
const pipelineAsync = promisify(pipeline);
class UpperCaseTransform extends Transform {
  _transform(chunk, enc, cb) { cb(null, chunk.toString().toUpperCase()); }
}
const buf1 = Buffer.alloc(4, 0); const buf2 = Buffer.from([1, 2, 3, 4]);
const combined = Buffer.concat([buf1, buf2]);
console.log(\"Combined:\", combined);
(async () => {
  const chunks = [];
  const readable = Readable.from([\"hello \", \"world\", \"!\"]);
  const upper = new UpperCaseTransform();
  const writable = new Writable({
    write(chunk, enc, cb) { chunks.push(chunk.toString()); cb(); }
  });
  await pipelineAsync(readable, upper, writable);
  console.log(\"Result:\", chunks.join(\"\"));
})();
'"
```

📸 **Verified Output:**
```
Combined: <Buffer 00 00 00 00 01 02 03 04>
Result: HELLO WORLD!
```

---

## Summary

| Stream Type | Direction | Use Case |
|-------------|-----------|----------|
| Readable | Source (outward) | File read, HTTP response, data generation |
| Writable | Sink (inward) | File write, HTTP request, data consumption |
| Transform | Both | Compression, encryption, parsing |
| Duplex | Both (independent) | TCP sockets, crypto streams |
| PassThrough | Both (transparent) | Monitoring, spy streams |

| Buffer Method | Description |
|---------------|-------------|
| `Buffer.alloc(n)` | Allocate n zero bytes |
| `Buffer.from(str)` | Create from string |
| `Buffer.concat([b1,b2])` | Concatenate buffers |
| `buf.subarray(start,end)` | Slice (shared memory) |
| `buf.copy(target)` | Copy to another buffer |
| `buf.toString('base64')` | Encode to base64 |
