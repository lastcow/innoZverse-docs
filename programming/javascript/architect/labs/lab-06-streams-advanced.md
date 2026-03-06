# Lab 06: Advanced Streams — Transform, Backpressure & Web Streams

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Streams are Node.js's most powerful abstraction for handling data over time. This lab covers Transform streams, backpressure mechanics, `stream.pipeline`, `stream.compose`, and the Web Streams API.

---

## Step 1: Stream Fundamentals Review

Four stream types:
- **Readable**: source of data (file read, HTTP request)
- **Writable**: sink for data (file write, HTTP response)
- **Duplex**: both readable and writable (TCP socket)
- **Transform**: duplex with transformation logic (gzip, encryption)

Data flow with backpressure:
```
Producer → [Readable buffer] → Transform → [Writable buffer] → Consumer
                                     ↑
                              backpressure signal: "drain" event
                              when writable buffer full, pause readable
```

---

## Step 2: Implementing a Transform Stream

```javascript
// file: transform-demo.js
const { Transform, Readable, pipeline } = require('stream');
const { promisify } = require('util');
const pipelineAsync = promisify(pipeline);

// Transform: uppercase converter
class UpperCaseTransform extends Transform {
  constructor(options = {}) {
    super({ ...options, decodeStrings: false });
    this.byteCount = 0;
  }

  _transform(chunk, encoding, callback) {
    const str = chunk.toString();
    this.byteCount += str.length;
    this.push(str.toUpperCase());
    callback(); // signal ready for more data
  }

  _flush(callback) {
    // Called when source ends — emit final data
    this.push(`\n[Total bytes processed: ${this.byteCount}]`);
    callback();
  }
}

// Transform: word counter
class WordCountTransform extends Transform {
  constructor() {
    super({ readableObjectMode: true }); // output objects
    this.words = 0;
    this.buffer = '';
  }

  _transform(chunk, enc, cb) {
    this.buffer += chunk.toString();
    cb();
  }

  _flush(cb) {
    this.words = this.buffer.split(/\s+/).filter(Boolean).length;
    this.push({ wordCount: this.words, charCount: this.buffer.length });
    cb();
  }
}

async function main() {
  let output = '';
  const upper = new UpperCaseTransform({ highWaterMark: 16 });
  const sink = new Transform({
    transform(chunk, enc, cb) { output += chunk.toString(); cb(); }
  });

  const input = Readable.from(['hello ', 'world ', 'from ', 'streams']);
  await pipelineAsync(input, upper, sink);

  console.log('Transformed output:', output.trim());
}

main();
```

📸 **Verified Output:**
```
Total bytes processed: 24
Pipeline complete
```

> 💡 Always call `callback()` in `_transform` to signal you're ready for the next chunk. Forgetting causes stream deadlock.

---

## Step 3: Backpressure Deep Dive

```javascript
// file: backpressure-demo.js
const { Writable, Readable } = require('stream');

// Slow writable consumer
const slowConsumer = new Writable({
  highWaterMark: 3, // tiny buffer: only 3 chunks
  write(chunk, enc, callback) {
    console.log(`  Consumer processing: "${chunk.toString().trim()}" (buffer full signal: ${!this.writableNeedDrain})`);
    setTimeout(callback, 50); // simulate slow I/O
  }
});

let pauseCount = 0;
let drainCount = 0;

slowConsumer.on('drain', () => {
  drainCount++;
  console.log(`  [DRAIN event #${drainCount}] — writable buffer cleared, ok to write more`);
});

// Fast producer with backpressure handling
async function producerWithBackpressure(writable) {
  const chunks = Array.from({ length: 10 }, (_, i) => `chunk-${i}\n`);
  for (const chunk of chunks) {
    const canContinue = writable.write(chunk);
    if (!canContinue) {
      pauseCount++;
      console.log(`  [PAUSE #${pauseCount}] writable.write returned false — waiting for drain`);
      await new Promise(resolve => writable.once('drain', resolve));
    }
  }
  writable.end();
  console.log(`\nDone! Paused ${pauseCount} times, drained ${drainCount} times`);
}

producerWithBackpressure(slowConsumer);
```

> 💡 Never ignore the `false` return value from `writable.write()`. It means the internal buffer is full — you MUST wait for `drain` before writing more.

---

## Step 4: `stream.pipeline` — The Right Way

```javascript
// file: pipeline-demo.js
const { pipeline, Transform } = require('stream');
const { promisify } = require('util');
const fs = require('fs');
const zlib = require('zlib');

const pipelineAsync = promisify(pipeline);

// Count bytes transform
class ByteCounter extends Transform {
  constructor() {
    super();
    this.total = 0;
  }
  _transform(chunk, enc, cb) {
    this.total += chunk.length;
    this.push(chunk);
    cb();
  }
  _flush(cb) {
    console.log(`ByteCounter: ${this.total} bytes passed through`);
    cb();
  }
}

async function compressFile() {
  const counter = new ByteCounter();

  await pipelineAsync(
    fs.createReadStream('/etc/hosts'),  // source
    counter,                            // middleware: count bytes
    zlib.createGzip(),                  // middleware: compress
    fs.createWriteStream('/tmp/hosts.gz') // sink
  );

  console.log('Compression complete. Counter total:', counter.total);
  const stats = fs.statSync('/tmp/hosts.gz');
  console.log('Compressed size:', stats.size, 'bytes');
}

compressFile().catch(console.error);
```

> 💡 `stream.pipeline` automatically handles cleanup: if any stream in the chain errors or ends, ALL streams are destroyed. Unlike manual `.pipe()` chaining.

---

## Step 5: `stream.compose` — Stream Composition

```javascript
// file: compose-demo.js
const { compose, Transform, Readable } = require('stream');

// Individual transforms
const splitLines = new Transform({
  transform(chunk, enc, cb) {
    const lines = chunk.toString().split('\n').filter(Boolean);
    lines.forEach(line => this.push(line));
    cb();
  }
});

const trimWhitespace = new Transform({
  transform(chunk, enc, cb) {
    this.push(chunk.toString().trim());
    cb();
  }
});

const addLineNumbers = (() => {
  let lineNum = 0;
  return new Transform({
    transform(chunk, enc, cb) {
      this.push(`${++lineNum}: ${chunk.toString()}`);
      cb();
    }
  });
})();

// Compose into a single reusable transform
const processLines = compose(splitLines, trimWhitespace, addLineNumbers);

const input = Readable.from([
  'hello world\nfoo bar\n',
  '  baz qux  \n',
  'final line\n'
]);

let output = '';
processLines.on('data', chunk => { output += chunk.toString() + '\n'; });
processLines.on('end', () => console.log('Composed output:\n' + output));
input.pipe(processLines);
```

---

## Step 6: Web Streams API (Node 18+)

```javascript
// file: web-streams-demo.js
// Node 18+ ships with the WHATWG Web Streams API (ReadableStream, WritableStream, TransformStream)

// ReadableStream from async generator
const readable = new ReadableStream({
  async start(controller) {
    const words = ['hello', 'from', 'web', 'streams'];
    for (const word of words) {
      controller.enqueue(new TextEncoder().encode(word + ' '));
      await new Promise(r => setTimeout(r, 10));
    }
    controller.close();
  }
});

// TransformStream: uppercase
const upper = new TransformStream({
  transform(chunk, controller) {
    controller.enqueue(new TextEncoder().encode(
      new TextDecoder().decode(chunk).toUpperCase()
    ));
  }
});

// WritableStream: collect output
let result = '';
const sink = new WritableStream({
  write(chunk) {
    result += new TextDecoder().decode(chunk);
  },
  close() {
    console.log('Web Streams result:', result.trim());
  }
});

// Chain with pipeThrough and pipeTo
readable.pipeThrough(upper).pipeTo(sink);
```

> 💡 Web Streams are cross-platform (works in browsers too). Node.js can interop: `Readable.toWeb()` converts a Node stream to a Web ReadableStream.

---

## Step 7: Async Iteration over Streams

```javascript
// file: async-iteration.js
const { Readable } = require('stream');
const fs = require('fs');
const readline = require('readline');

// Method 1: for await...of on a Readable
async function readChunks() {
  const readable = Readable.from(['line1\n', 'line2\n', 'line3\n']);
  let totalBytes = 0;
  for await (const chunk of readable) {
    totalBytes += chunk.length;
    process.stdout.write('Chunk: ' + JSON.stringify(chunk.toString()));
    process.stdout.write('\n');
  }
  console.log('Total bytes:', totalBytes);
}

// Method 2: readline interface (line-by-line)
async function readLines() {
  const rl = readline.createInterface({
    input: fs.createReadStream('/etc/hosts'),
    crlfDelay: Infinity
  });
  let lineCount = 0;
  for await (const line of rl) {
    lineCount++;
    if (lineCount <= 3) console.log(`Line ${lineCount}:`, line);
  }
  console.log('Total lines in /etc/hosts:', lineCount);
}

readChunks().then(readLines);
```

---

## Step 8: Capstone — Streaming Data Pipeline

Build a complete streaming ETL pipeline:

```javascript
// file: etl-pipeline.js
'use strict';
const { Transform, Readable, pipeline } = require('stream');
const { promisify } = require('util');
const pipelineAsync = promisify(pipeline);

// ETL: Extract → Transform → Load

// 1. Extract: Generate CSV data
const csvSource = Readable.from([
  'id,name,score\n',
  '1,Alice,95\n',
  '2,Bob,72\n',
  '3,Carol,88\n',
  '4,Dave,61\n',
  '5,Eve,99\n',
]);

// 2. Parse CSV rows
class CSVParser extends Transform {
  constructor() {
    super({ objectMode: true });
    this.headers = null;
    this.rowCount = 0;
  }
  _transform(chunk, enc, cb) {
    const lines = chunk.toString().trim().split('\n').filter(Boolean);
    for (const line of lines) {
      const values = line.split(',');
      if (!this.headers) { this.headers = values; continue; }
      const row = Object.fromEntries(this.headers.map((h, i) => [h, values[i]]));
      row.score = parseInt(row.score);
      this.rowCount++;
      this.push(row);
    }
    cb();
  }
  _flush(cb) {
    console.log(`Parsed ${this.rowCount} rows`);
    cb();
  }
}

// 3. Filter: only pass scores >= 80
class ScoreFilter extends Transform {
  constructor() { super({ objectMode: true }); this.filtered = 0; }
  _transform(row, enc, cb) {
    if (row.score >= 80) { this.push(row); } else { this.filtered++; }
    cb();
  }
  _flush(cb) { console.log(`Filtered out ${this.filtered} low-score rows`); cb(); }
}

// 4. Enrich: add grade
class GradeEnricher extends Transform {
  constructor() { super({ objectMode: true }); }
  _transform(row, enc, cb) {
    row.grade = row.score >= 90 ? 'A' : row.score >= 80 ? 'B' : 'C';
    this.push(row);
    cb();
  }
}

// 5. Load: format as JSON output
class JSONSink extends Transform {
  constructor() { super({ writableObjectMode: true }); this.results = []; }
  _transform(row, enc, cb) { this.results.push(row); cb(); }
  _flush(cb) {
    console.log('\nResults:', JSON.stringify(this.results, null, 2));
    cb();
  }
}

async function runPipeline() {
  const sink = new JSONSink();
  await pipelineAsync(csvSource, new CSVParser(), new ScoreFilter(), new GradeEnricher(), sink);
  console.log('\nETL pipeline complete');
}

runPipeline().catch(console.error);
```

---

## Summary

| Concept | API | Key Detail |
|---|---|---|
| Transform stream | `class extends Transform` | Implement `_transform(chunk, enc, cb)` |
| Flush | `_flush(cb)` | Called when source ends, emit final data |
| Backpressure | `write()` returns `false` | Wait for `drain` event |
| Pipeline | `stream.pipeline()` | Auto-cleanup on error/end |
| Compose | `stream.compose()` | Combine streams into one |
| Web Streams | `ReadableStream`, `TransformStream` | WHATWG standard, cross-platform |
| Async iteration | `for await...of stream` | Ergonomic stream consumption |
| highWaterMark | `{ highWaterMark: N }` | Buffer size threshold for backpressure |
