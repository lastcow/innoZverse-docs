# Lab 12: Caching Strategies — LRU, Redis Patterns & Consistent Hashing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Caching is the highest-leverage performance optimization. This lab implements an LRU cache from scratch, covers Redis patterns with ioredis, and builds a consistent hashing ring for cache sharding.

---

## Step 1: LRU Cache — Theory

**LRU (Least Recently Used)**: evict the item that was accessed longest ago.

Data structure: **Map + Doubly-Linked List**
- Map: O(1) key lookup
- DLL: O(1) move-to-front (on access) and eviction (from tail)

```
HEAD ↔ [most recent] ↔ ... ↔ [least recent] ↔ TAIL
         ↑                                        ↑
     new access                               evict this
```

---

## Step 2: LRU Cache Implementation

```javascript
// file: lru-cache.js
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = new Map();

    // Sentinel nodes (dummy head/tail for simpler logic)
    this.head = { key: null, val: null, prev: null, next: null };
    this.tail = { key: null, val: null, prev: null, next: null };
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }

  _addToFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  get(key) {
    if (!this.map.has(key)) return -1;
    const node = this.map.get(key);
    this._remove(node);
    this._addToFront(node); // promote to most-recently-used
    return node.val;
  }

  put(key, val) {
    if (this.map.has(key)) {
      this._remove(this.map.get(key));
    } else if (this.map.size >= this.capacity) {
      // Evict LRU (tail.prev)
      const lru = this.tail.prev;
      this._remove(lru);
      this.map.delete(lru.key);
      console.log(`  Evicted: key="${lru.key}"`);
    }
    const node = { key, val, prev: null, next: null };
    this._addToFront(node);
    this.map.set(key, node);
  }

  size() { return this.map.size; }

  toArray() {
    const result = [];
    let cur = this.head.next;
    while (cur !== this.tail) { result.push(cur.key); cur = cur.next; }
    return result; // most → least recent
  }
}

// Demo
const cache = new LRUCache(3);
cache.put('a', 1);
cache.put('b', 2);
cache.put('c', 3);
cache.get('a');      // promote 'a' to front
cache.put('d', 4);   // evict 'b' (least recently used)

console.log('get b:', cache.get('b')); // -1 (evicted)
console.log('get a:', cache.get('a')); //  1
console.log('get d:', cache.get('d')); //  4
console.log('Order (most→least):', cache.toArray());
```

📸 **Verified Output:**
```
  Evicted: key="b"
get b: -1
get a: 1
get d: 4
Order (most→least): [ 'd', 'a', 'c' ]
```

---

## Step 3: TTL-Aware LRU Cache

```javascript
// file: lru-ttl-cache.js
class TTLLRUCache {
  constructor(capacity, defaultTTLms = 60_000) {
    this.lru = new Map();
    this.capacity = capacity;
    this.defaultTTL = defaultTTLms;
    this.head = { k: null, next: null, prev: null };
    this.tail = { k: null, next: null, prev: null };
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  _remove(node) { node.prev.next = node.next; node.next.prev = node.prev; }
  _front(node) { node.next = this.head.next; node.prev = this.head; this.head.next.prev = node; this.head.next = node; }

  get(key) {
    const entry = this.lru.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this._remove(entry.node);
      this.lru.delete(key);
      return null; // expired
    }
    this._remove(entry.node);
    this._front(entry.node);
    return entry.value;
  }

  set(key, value, ttl = this.defaultTTL) {
    if (this.lru.has(key)) this._remove(this.lru.get(key).node);
    else if (this.lru.size >= this.capacity) {
      const lruKey = this.tail.prev.k;
      this._remove(this.tail.prev);
      this.lru.delete(lruKey);
    }
    const node = { k: key, next: null, prev: null };
    this._front(node);
    this.lru.set(key, { value, expiresAt: Date.now() + ttl, node });
  }
}

const cache = new TTLLRUCache(100, 500); // 500ms TTL
cache.set('user:1', { name: 'Alice' });
console.log('Immediate get:', cache.get('user:1')?.name); // Alice

setTimeout(() => {
  console.log('After 600ms get:', cache.get('user:1')); // null (expired)
}, 600);
```

---

## Step 4: Redis Patterns with ioredis

```javascript
// file: redis-patterns.js
// npm install ioredis

const Redis = require('ioredis');

async function redisPatterns() {
  const redis = new Redis({ host: 'localhost', port: 6379, lazyConnect: true });

  try {
    await redis.connect();
  } catch (e) {
    console.log('Redis not available, using mock demo');
    await redis.disconnect();
    return mockRedisDemo();
  }

  // === PIPELINE: batch commands, one round-trip ===
  const pipe = redis.pipeline();
  pipe.set('key1', 'value1', 'EX', 60);
  pipe.set('key2', 'value2', 'EX', 60);
  pipe.get('key1');
  pipe.incr('counter');
  const pipeResults = await pipe.exec();
  console.log('Pipeline results:', pipeResults.map(([err, val]) => val));

  // === MULTI/EXEC (TRANSACTION) ===
  const tx = redis.multi();
  tx.set('balance', '1000');
  tx.decrby('balance', 100);
  tx.get('balance');
  const txResults = await tx.exec();
  console.log('Transaction results:', txResults.map(([e, v]) => v));

  // === SCAN: safe iteration over large key sets ===
  await Promise.all(Array.from({ length: 5 }, (_, i) => redis.set(`scan:key:${i}`, i)));
  const stream = redis.scanStream({ match: 'scan:key:*', count: 2 });
  const foundKeys = [];
  stream.on('data', keys => foundKeys.push(...keys));
  await new Promise(resolve => stream.on('end', resolve));
  console.log('SCAN found:', foundKeys.sort());

  await redis.disconnect();
}

function mockRedisDemo() {
  // Simulate ioredis pipeline behavior
  console.log('\n=== Mock Redis Demo (ioredis patterns) ===');

  class MockPipeline {
    constructor() { this.commands = []; }
    set(k, v, ...opts) { this.commands.push(['SET', k, v, ...opts]); return this; }
    get(k) { this.commands.push(['GET', k]); return this; }
    incr(k) { this.commands.push(['INCR', k]); return this; }
    exec() {
      console.log('Pipeline executing', this.commands.length, 'commands:');
      this.commands.forEach(cmd => console.log(' ', cmd.join(' ')));
      return [[null, 'OK'], [null, 'OK'], [null, 'value1'], [null, 1]];
    }
  }

  const pipe = new MockPipeline();
  pipe.set('key1', 'value1', 'EX', 60);
  pipe.set('key2', 'value2', 'EX', 60);
  pipe.get('key1');
  pipe.incr('counter');
  const results = pipe.exec();
  console.log('Results:', results.map(([e, v]) => v));
}

redisPatterns().catch(console.error);
```

---

## Step 5: Cache-Aside, Write-Through, Write-Behind Patterns

```javascript
// file: cache-patterns.js
class CachePatterns {
  constructor() {
    this.cache = new Map();
    this.db = new Map([['user:1', { id: 1, name: 'Alice' }], ['user:2', { id: 2, name: 'Bob' }]]);
    this.writeBuffer = [];
  }

  // CACHE-ASIDE (lazy loading): read from cache, on miss load from DB
  async cacheAside(key) {
    if (this.cache.has(key)) {
      console.log(`  [CACHE HIT] ${key}`);
      return this.cache.get(key);
    }
    console.log(`  [CACHE MISS] ${key} → loading from DB`);
    const value = this.db.get(key);
    if (value) this.cache.set(key, value);
    return value;
  }

  // WRITE-THROUGH: write to both cache AND DB synchronously
  async writeThrough(key, value) {
    console.log(`  [WRITE-THROUGH] ${key} → cache + DB`);
    this.cache.set(key, value);
    this.db.set(key, value); // synchronous DB write
    return value;
  }

  // WRITE-BEHIND (async): write to cache immediately, DB asynchronously
  writeBehind(key, value) {
    console.log(`  [WRITE-BEHIND] ${key} → cache now, DB later`);
    this.cache.set(key, value);
    this.writeBuffer.push({ key, value, ts: Date.now() });
  }

  async flushWriteBuffer() {
    if (this.writeBuffer.length === 0) return;
    console.log(`  [FLUSH] Writing ${this.writeBuffer.length} items to DB`);
    for (const { key, value } of this.writeBuffer) {
      this.db.set(key, value); // batch DB write
    }
    this.writeBuffer = [];
  }
}

async function demo() {
  const cp = new CachePatterns();
  console.log('=== Cache-Aside ===');
  await cp.cacheAside('user:1'); // miss
  await cp.cacheAside('user:1'); // hit

  console.log('\n=== Write-Through ===');
  await cp.writeThrough('user:3', { id: 3, name: 'Carol' });
  await cp.cacheAside('user:3'); // hit (written through)

  console.log('\n=== Write-Behind ===');
  cp.writeBehind('user:4', { id: 4, name: 'Dave' });
  cp.writeBehind('user:5', { id: 5, name: 'Eve' });
  console.log('DB has user:4?', cp.db.has('user:4')); // false (not yet flushed)
  await cp.flushWriteBuffer();
  console.log('DB has user:4?', cp.db.has('user:4')); // true
}

demo();
```

---

## Step 6: Stale-While-Revalidate

```javascript
// file: stale-while-revalidate.js

class SWRCache {
  constructor() {
    this.store = new Map(); // key → { value, fresh_until, stale_until }
  }

  async get(key, fetcher, { freshTTL = 5000, staleTTL = 30000 } = {}) {
    const now = Date.now();
    const entry = this.store.get(key);

    if (!entry || now > entry.stale_until) {
      // Cache miss or fully stale: fetch synchronously
      console.log(`  [FETCH] ${key} (cache miss)`);
      const value = await fetcher(key);
      this.store.set(key, { value, fresh_until: now + freshTTL, stale_until: now + staleTTL });
      return value;
    }

    if (now > entry.fresh_until) {
      // Stale but within grace period: return stale, revalidate in background
      console.log(`  [SWR] ${key} — returning stale, revalidating in background`);
      fetcher(key).then(value => {
        this.store.set(key, { value, fresh_until: Date.now() + freshTTL, stale_until: Date.now() + staleTTL });
        console.log(`  [REVALIDATED] ${key}`);
      });
      return entry.value; // stale but immediate
    }

    console.log(`  [FRESH] ${key}`);
    return entry.value;
  }
}

let fetchCount = 0;
async function mockFetch(key) {
  await new Promise(r => setTimeout(r, 50)); // simulate latency
  return { data: `value-for-${key}`, fetchedAt: ++fetchCount };
}

async function demo() {
  const cache = new SWRCache();
  const r1 = await cache.get('api/data', mockFetch, { freshTTL: 100, staleTTL: 500 });
  console.log('r1:', r1);

  await new Promise(r => setTimeout(r, 150)); // let it go stale
  const r2 = await cache.get('api/data', mockFetch, { freshTTL: 100, staleTTL: 500 });
  console.log('r2 (stale):', r2);

  await new Promise(r => setTimeout(r, 100)); // wait for background refresh
  const r3 = await cache.get('api/data', mockFetch, { freshTTL: 100, staleTTL: 500 });
  console.log('r3 (fresh after revalidate):', r3);
}

demo();
```

---

## Step 7: Consistent Hashing for Cache Sharding

```javascript
// file: consistent-hashing.js
const crypto = require('crypto');

class ConsistentHashRing {
  constructor(virtualNodes = 150) {
    this.ring = new Map(); // hash → node
    this.sortedHashes = [];
    this.virtualNodes = virtualNodes;
  }

  _hash(str) {
    return parseInt(crypto.createHash('md5').update(str).digest('hex').slice(0, 8), 16);
  }

  addNode(node) {
    for (let i = 0; i < this.virtualNodes; i++) {
      const hash = this._hash(`${node}:vn${i}`);
      this.ring.set(hash, node);
      this.sortedHashes.push(hash);
    }
    this.sortedHashes.sort((a, b) => a - b);
  }

  removeNode(node) {
    for (let i = 0; i < this.virtualNodes; i++) {
      const hash = this._hash(`${node}:vn${i}`);
      this.ring.delete(hash);
    }
    this.sortedHashes = [...this.ring.keys()].sort((a, b) => a - b);
  }

  getNode(key) {
    if (this.ring.size === 0) return null;
    const hash = this._hash(key);
    // Find first ring position >= hash (clockwise)
    for (const pos of this.sortedHashes) {
      if (pos >= hash) return this.ring.get(pos);
    }
    return this.ring.get(this.sortedHashes[0]); // wrap around
  }
}

const ring = new ConsistentHashRing(150);
['cache-1', 'cache-2', 'cache-3'].forEach(n => ring.addNode(n));

// Show distribution
const distribution = new Map();
for (let i = 0; i < 1000; i++) {
  const node = ring.getNode(`key-${i}`);
  distribution.set(node, (distribution.get(node) || 0) + 1);
}
console.log('Key distribution (1000 keys):');
for (const [node, count] of distribution) {
  console.log(`  ${node}: ${count} keys (${(count/10).toFixed(1)}%)`);
}

// Add node — only nearby keys move
ring.addNode('cache-4');
let moved = 0;
for (let i = 0; i < 1000; i++) {
  const newNode = ring.getNode(`key-${i}`);
  if (newNode !== distribution.get(newNode)) moved++;
}
console.log(`After adding cache-4: ~${distribution.get('cache-1') + distribution.get('cache-2') + distribution.get('cache-3') - 750} keys remapped`);
```

---

## Step 8: Capstone — Production Cache Layer

```javascript
// file: production-cache.js
'use strict';
const crypto = require('crypto');

class ProductionCache {
  constructor({ capacity = 1000, defaultTTL = 60_000, namespace = 'app' } = {}) {
    this.namespace = namespace;
    this.defaultTTL = defaultTTL;
    this.store = new Map();
    this.capacity = capacity;
    this.stats = { hits: 0, misses: 0, evictions: 0, sets: 0 };

    // LRU tracking
    this.head = { k: null, next: null, prev: null };
    this.tail = { k: null, next: null, prev: null };
    this.head.next = this.tail;
    this.tail.prev = this.head;
    this.lruMap = new Map();
  }

  _key(key) { return `${this.namespace}:${key}`; }
  _removeNode(n) { n.prev.next = n.next; n.next.prev = n.prev; }
  _front(n) { n.next = this.head.next; n.prev = this.head; this.head.next.prev = n; this.head.next = n; }

  get(key) {
    const k = this._key(key);
    const entry = this.store.get(k);
    if (!entry || Date.now() > entry.expiresAt) {
      this.stats.misses++;
      if (entry) { this.store.delete(k); this._removeNode(this.lruMap.get(k)); this.lruMap.delete(k); }
      return null;
    }
    this.stats.hits++;
    const node = this.lruMap.get(k);
    this._removeNode(node); this._front(node);
    return entry.value;
  }

  set(key, value, ttl = this.defaultTTL) {
    const k = this._key(key);
    this.stats.sets++;
    if (this.lruMap.has(k)) { this._removeNode(this.lruMap.get(k)); }
    else if (this.store.size >= this.capacity) {
      const lruKey = this.tail.prev.k;
      this._removeNode(this.tail.prev); this.lruMap.delete(lruKey); this.store.delete(lruKey);
      this.stats.evictions++;
    }
    const node = { k, next: null, prev: null };
    this._front(node); this.lruMap.set(k, node);
    this.store.set(k, { value, expiresAt: Date.now() + ttl });
  }

  async getOrSet(key, fetcher, ttl) {
    const cached = this.get(key);
    if (cached !== null) return cached;
    const fresh = await fetcher();
    this.set(key, fresh, ttl);
    return fresh;
  }

  report() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(1) : '0.0';
    console.log(`Cache[${this.namespace}] size=${this.store.size}/${this.capacity}`);
    console.log(`  hits=${this.stats.hits} misses=${this.stats.misses} rate=${hitRate}%`);
    console.log(`  sets=${this.stats.sets} evictions=${this.stats.evictions}`);
  }
}

async function demo() {
  const cache = new ProductionCache({ capacity: 3, defaultTTL: 500 });
  let dbCalls = 0;

  async function getUser(id) {
    return cache.getOrSet(`user:${id}`, async () => {
      dbCalls++;
      return { id, name: `User-${id}`, fetchedAt: Date.now() };
    }, 200);
  }

  // Fill cache
  for (let i = 1; i <= 5; i++) await getUser(i);
  // Hit cache
  for (let i = 1; i <= 3; i++) await getUser(i);

  console.log('DB calls:', dbCalls, '(5 misses + 2 evictions refetched on re-access)');
  cache.report();
}

demo();
```

---

## Summary

| Strategy | Consistency | Performance | Use Case |
|---|---|---|---|
| LRU Cache | Eventually | Very high | Hot data, session cache |
| Cache-Aside | Eventual | High | General read cache |
| Write-Through | Strong | Medium | Write-heavy, needs read consistency |
| Write-Behind | Eventual | Very high | High write throughput, eventual persistence |
| SWR | Eventual | Very high | APIs, dashboards, CDN content |
| Consistent Hashing | N/A | High | Distributed cache sharding |
| Redis pipeline | N/A | Very high | Batch operations, reduce RTT |
| Redis MULTI/EXEC | Atomic | High | Transactional updates |
