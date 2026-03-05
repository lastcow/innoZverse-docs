# Lab 03: Advanced Streams

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Deep dive into advanced stream patterns: object mode streams, Transform stream implementation, `stream.compose`, WHATWG Web Streams API, error handling, and `highWaterMark` tuning.

---

## Step 1: Object Mode Streams

```javascript
const { Readable, Writable, Transform } = require('node:stream');

// Object mode: pass JS objects instead of Buffers
const objectReadable = Readable.from([
  { id: 1, name: 'Alice', score: 95 },
  { id: 2, name: 'Bob', score: 72 },
  { id: 3, name: 'Charlie', score: 88 }
]); // Readable.from creates object mode automatically for non-strings

// Object mode Transform
class ScoreNormalizer extends Transform {
  constructor() { super({ objectMode: true }); }

  _transform(record, enc, cb) {
    cb(null, {
      ...record,
      grade: record.score >= 90 ? 'A' : record.score >= 80 ? 'B' : 'C',
      normalized: (record.score / 100).toFixed(2)
    });
  }
}

// Object mode Writable
const results = [];
const collector = new Writable({
  objectMode: true,
  write(obj, enc, cb) { results.push(obj); cb(); }
});

objectReadable
  .pipe(new ScoreNormalizer())
  .pipe(collector);

collector.on('finish', () => {
  console.log('Processed:', JSON.stringify(results, null, 2));
});
```

---

## Step 2: Custom Transform Streams

```javascript
const { Transform } = require('node:stream');

// Line-by-line processor
class LineTransform extends Transform {
  #buffer = '';

  constructor(options = {}) {
    super({ ...options, readableObjectMode: true });
  }

  _transform(chunk, encoding, callback) {
    this.#buffer += chunk.toString();
    const lines = this.#buffer.split('\n');
    this.#buffer = lines.pop() ?? ''; // Keep incomplete line
    for (const line of lines) {
      if (line.trim()) this.push(line);
    }
    callback();
  }

  _flush(callback) {
    if (this.#buffer.trim()) this.push(this.#buffer);
    callback();
  }
}

// CSV Parser Transform
class CSVParser extends Transform {
  #headers = null;

  constructor() { super({ objectMode: true }); }

  _transform(line, enc, cb) {
    const values = line.split(',').map(v => v.trim());
    if (!this.#headers) {
      this.#headers = values;
    } else {
      const obj = Object.fromEntries(this.#headers.map((h, i) => [h, values[i] ?? null]));
      this.push(obj);
    }
    cb();
  }
}

// Usage
const { Readable } = require('node:stream');
const csv = `name,age,city
Alice,30,New York
Bob,25,San Francisco
Charlie,35,Austin`;

const results = [];
const stream = Readable.from(csv);
stream
  .pipe(new LineTransform())
  .pipe(new CSVParser())
  .on('data', obj => results.push(obj))
  .on('end', () => console.log('Parsed:', results));
```

---

## Step 3: stream.compose

```javascript
const { compose, Transform, Readable, Writable } = require('node:stream');
const { promisify } = require('node:util');
const pipeline = promisify(require('node:stream').pipeline);

// stream.compose combines multiple streams into one
const upperCase = new Transform({
  transform(chunk, enc, cb) { cb(null, chunk.toString().toUpperCase()); }
});

const addNewline = new Transform({
  transform(chunk, enc, cb) { cb(null, chunk + '\n'); }
});

const countBytes = new Transform({
  transform(chunk, enc, cb) {
    this.totalBytes = (this.totalBytes || 0) + chunk.length;
    cb(null, chunk);
  }
});

// Compose into single transform
const composed = compose(upperCase, addNewline, countBytes);

const results = [];
await pipeline(
  Readable.from(['hello ', 'world']),
  composed,
  new Writable({ write(chunk, enc, cb) { results.push(chunk.toString()); cb(); } })
);
console.log(results.join(''));
```

---

## Step 4: WHATWG Web Streams

```javascript
// Node.js 18+ has Web Streams API built-in
const { ReadableStream, WritableStream, TransformStream } = require('node:stream/web');

// Create ReadableStream
const readable = new ReadableStream({
  start(controller) {
    controller.enqueue('Hello, ');
    controller.enqueue('Web ');
    controller.enqueue('Streams!');
    controller.close();
  }
});

// TransformStream
const upperCase = new TransformStream({
  transform(chunk, controller) {
    controller.enqueue(chunk.toUpperCase());
  }
});

// Pipe WHATWG streams
const output = [];
const writable = new WritableStream({
  write(chunk) { output.push(chunk); }
});

await readable.pipeThrough(upperCase).pipeTo(writable);
console.log(output.join('')); // HELLO, WEB STREAMS!

// Interop: WHATWG <-> Node.js streams
const { Readable } = require('node:stream');
const nodeReadable = Readable.fromWeb(readable); // WHATWG -> Node
const webReadable = Readable.toWeb(nodeReadable); // Node -> WHATWG
```

---

## Step 5: Error Handling in Streams

```javascript
const { pipeline, Transform, Readable, Writable } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

// stream.pipeline propagates errors and cleans up all streams
class ErrorableTransform extends Transform {
  _transform(chunk, enc, cb) {
    const str = chunk.toString();
    if (str.includes('ERROR')) {
      cb(new Error(`Bad data: ${str}`)); // Error propagates through pipeline
    } else {
      cb(null, str.toUpperCase());
    }
  }
}

async function safePipeline() {
  try {
    await pipelineAsync(
      Readable.from(['good', 'data', 'ERROR: bad', 'more']),
      new ErrorableTransform(),
      new Writable({ write(c, e, cb) { console.log(c.toString()); cb(); } })
    );
  } catch (err) {
    console.error('Pipeline failed:', err.message);
    // All streams are properly destroyed on error
  }
}

safePipeline();
```

---

## Step 6: highWaterMark Tuning

```javascript
const { Readable, Writable, Transform } = require('node:stream');

// highWaterMark controls buffer size before backpressure kicks in
// Too low = many pauses; Too high = memory usage

// Default: 16KB for binary streams, 16 objects for object mode
const tuned = new Transform({
  highWaterMark: 1024 * 64, // 64KB buffer (good for high-throughput)
  objectMode: false,
  transform(chunk, enc, cb) { cb(null, chunk); }
});

// Monitor backpressure
function createMonitoredWritable(name, hwm) {
  let pauses = 0;
  const writable = new Writable({
    highWaterMark: hwm,
    write(chunk, enc, cb) {
      setTimeout(cb, 1); // Simulate slow processing
    }
  });

  const originalWrite = writable.write.bind(writable);
  writable.write = function(chunk) {
    const result = originalWrite(chunk);
    if (!result) { pauses++; console.log(`${name}: backpressure #${pauses}`); }
    return result;
  };

  return writable;
}

// Metrics: track throughput
class ThroughputMonitor extends Transform {
  #bytes = 0; #start = Date.now();
  _transform(chunk, enc, cb) {
    this.#bytes += chunk.length;
    cb(null, chunk);
  }
  _flush(cb) {
    const secs = (Date.now() - this.#start) / 1000;
    console.log(`Throughput: ${(this.#bytes / secs / 1024).toFixed(1)} KB/s`);
    cb();
  }
}
```

---

## Step 7: Stream Performance Patterns

```javascript
const { Readable, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

// Parallel stream processing
async function parallelProcess(items, workerCount, processItem) {
  // Split items into chunks for parallel processing
  const chunkSize = Math.ceil(items.length / workerCount);
  const chunks = Array.from({ length: workerCount }, (_, i) =>
    items.slice(i * chunkSize, (i + 1) * chunkSize)
  );

  const results = await Promise.all(chunks.map(async chunk => {
    const processed = [];
    for (const item of chunk) {
      processed.push(await processItem(item));
    }
    return processed;
  }));

  return results.flat();
}
```

---

## Step 8: Capstone — Object Mode Pipeline

```javascript
const { Readable, Writable, Transform, pipeline } = require('node:stream');
const { promisify } = require('node:util');
const pipelineAsync = promisify(pipeline);

class UpperCaseTransform extends Transform {
  _transform(chunk, enc, cb) { cb(null, chunk.toString().toUpperCase()); }
}

const chunks = [];
(async () => {
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
const chunks = [];
(async () => {
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
Result: HELLO WORLD!
```

---

## Summary

| Feature | API | Use Case |
|---------|-----|----------|
| Object mode | `{ objectMode: true }` | Stream JS objects |
| Custom Transform | `_transform(chunk, enc, cb)` | Data transformation |
| `_flush` | Override in Transform | Process remaining buffer |
| `stream.compose` | `compose(t1, t2, t3)` | Combine streams |
| WHATWG streams | `ReadableStream`, `TransformStream` | Browser-compatible API |
| `stream.pipeline` | `pipeline(r, t, w, cb)` | Error-safe piping |
| `highWaterMark` | Constructor option | Buffer size tuning |
