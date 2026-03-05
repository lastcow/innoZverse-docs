# Lab 09: Redis with Node.js

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Use Redis via `ioredis`: String/Hash/List/Set/ZSet operations, pipelining, pub/sub, Lua scripting, and Redis Streams with consumer groups.

> **Note:** This lab requires a running Redis server. For local practice:
> ```bash
> docker run -d --name redis -p 6379:6379 redis:7
> ```
> The code examples are designed to be educational even without a live Redis instance.

---

## Step 1: Setup & Connection

```javascript
const Redis = require('ioredis');

// Single connection
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD,
  db: 0,
  retryStrategy(times) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  lazyConnect: false
});

redis.on('connect', () => console.log('Redis connected'));
redis.on('error', (err) => console.error('Redis error:', err.message));
redis.on('close', () => console.log('Redis disconnected'));

// Connection check
async function ping() {
  const result = await redis.ping();
  console.log('Ping:', result); // PONG
}

// Cluster connection
const cluster = new Redis.Cluster([
  { port: 7000, host: '127.0.0.1' },
  { port: 7001, host: '127.0.0.1' }
]);
```

---

## Step 2: String Operations

```javascript
// Basic String operations
async function stringOps(redis) {
  // SET / GET
  await redis.set('user:name', 'Alice');
  console.log(await redis.get('user:name')); // Alice

  // SET with expiry
  await redis.set('session:abc', JSON.stringify({ userId: 1 }), 'EX', 3600);
  console.log(await redis.ttl('session:abc')); // ~3600

  // SET if not exists
  const result = await redis.setnx('lock:resource', '1');
  console.log('Got lock:', result === 1);

  // Atomic counter
  await redis.set('counter', 0);
  await redis.incr('counter');
  await redis.incr('counter');
  await redis.incrby('counter', 5);
  console.log(await redis.get('counter')); // 7

  // Multiple keys
  await redis.mset('a', '1', 'b', '2', 'c', '3');
  const values = await redis.mget('a', 'b', 'c', 'd');
  console.log(values); // ['1', '2', '3', null]

  // JSON storage
  await redis.set('user:1', JSON.stringify({ id: 1, name: 'Alice' }));
  const user = JSON.parse(await redis.get('user:1'));
  console.log(user);
}
```

---

## Step 3: Hash Operations

```javascript
async function hashOps(redis) {
  // HSET / HGET
  await redis.hset('user:1', {
    name: 'Alice',
    email: 'alice@example.com',
    age: '30',
    role: 'admin'
  });

  console.log(await redis.hget('user:1', 'name'));  // Alice
  console.log(await redis.hgetall('user:1'));        // All fields

  // Increment field
  await redis.hincrby('user:1', 'age', 1);

  // Check field exists
  console.log(await redis.hexists('user:1', 'email')); // 1

  // Delete fields
  await redis.hdel('user:1', 'role');

  // All keys/values
  console.log(await redis.hkeys('user:1'));
  console.log(await redis.hvals('user:1'));
  console.log(await redis.hlen('user:1'));
}
```

---

## Step 4: List, Set, ZSet Operations

```javascript
async function collectionOps(redis) {
  // List — ordered, allows duplicates
  await redis.rpush('queue', 'task1', 'task2', 'task3');
  console.log(await redis.llen('queue'));       // 3
  console.log(await redis.lrange('queue', 0, -1)); // all items
  console.log(await redis.lpop('queue'));        // task1 (FIFO)
  console.log(await redis.rpop('queue'));        // task3 (LIFO)
  // Blocking pop (waits up to 5s for item)
  // const [key, value] = await redis.blpop('queue', 5);

  // Set — unique values
  await redis.sadd('tags', 'js', 'node', 'redis', 'js'); // 'js' added once
  console.log(await redis.smembers('tags'));   // 3 items
  console.log(await redis.sismember('tags', 'js')); // 1

  // Set operations
  await redis.sadd('tags2', 'node', 'docker', 'linux');
  console.log(await redis.sunion('tags', 'tags2'));
  console.log(await redis.sinter('tags', 'tags2'));
  console.log(await redis.sdiff('tags', 'tags2'));

  // Sorted Set (ZSet) — unique, ordered by score
  await redis.zadd('leaderboard', 95, 'Alice', 88, 'Bob', 92, 'Charlie');
  console.log(await redis.zrange('leaderboard', 0, -1, 'WITHSCORES'));
  console.log(await redis.zrevrangebyscore('leaderboard', '+inf', '-inf', 'WITHSCORES', 'LIMIT', 0, 3));
  console.log(await redis.zrank('leaderboard', 'Alice')); // 0-indexed rank
  await redis.zincrby('leaderboard', 5, 'Bob'); // Bob's score += 5
}
```

---

## Step 5: Pipeline & Multi (Transactions)

```javascript
async function pipelineOps(redis) {
  // Pipeline — batch commands, single network round trip
  const pipeline = redis.pipeline();
  pipeline.set('key1', 'value1');
  pipeline.set('key2', 'value2');
  pipeline.get('key1');
  pipeline.get('key2');
  pipeline.del('key1', 'key2');

  const results = await pipeline.exec();
  // [[null, 'OK'], [null, 'OK'], [null, 'value1'], [null, 'value2'], [null, 2]]
  results.forEach(([err, result]) => {
    if (err) console.error('Error:', err);
    else console.log('Result:', result);
  });

  // Multi (MULTI/EXEC) — atomic transaction
  const multi = redis.multi();
  multi.set('counter', 0);
  multi.incr('counter');
  multi.incr('counter');
  multi.get('counter');

  const txResults = await multi.exec();
  // All commands execute atomically
  console.log('Final counter:', txResults[3][1]); // 2

  // Optimistic locking with WATCH
  async function incrementSafely(key) {
    const result = await redis.watch(key);
    const currentValue = parseInt(await redis.get(key) || '0');

    const txResult = await redis.multi()
      .set(key, currentValue + 1)
      .exec();

    if (!txResult) throw new Error('Transaction failed — retry');
    return currentValue + 1;
  }
}
```

---

## Step 6: Pub/Sub

```javascript
const Redis = require('ioredis');

// Pub/Sub requires separate connections!
const publisher = new Redis();
const subscriber = new Redis();

async function pubSubDemo() {
  // Subscribe to channels
  await subscriber.subscribe('notifications', 'alerts');

  subscriber.on('message', (channel, message) => {
    console.log(`[${channel}] ${message}`);
    const data = JSON.parse(message);
    console.log('Received:', data);
  });

  // Pattern subscribe
  await subscriber.psubscribe('user:*');
  subscriber.on('pmessage', (pattern, channel, message) => {
    console.log(`[${pattern}] ${channel}: ${message}`);
  });

  // Publish
  await publisher.publish('notifications', JSON.stringify({
    type: 'USER_JOINED',
    userId: '123',
    timestamp: Date.now()
  }));

  await publisher.publish('user:online', JSON.stringify({ userId: '123' }));

  await subscriber.unsubscribe();
  await subscriber.quit();
  await publisher.quit();
}
```

---

## Step 7: Lua Scripting & Redis Streams

```javascript
// Lua scripting — atomic complex operations
async function luaScripting(redis) {
  // Rate limiter using Lua (atomic)
  const rateLimiterScript = `
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    
    local current = redis.call('INCR', key)
    if current == 1 then
      redis.call('EXPIRE', key, window)
    end
    
    if current > limit then
      return 0  -- Rate limited
    end
    return 1  -- Allowed
  `;

  const allowed = await redis.eval(rateLimiterScript, 1, 'rate:user:123', 10, 60);
  console.log('Request allowed:', allowed === 1);
}

// Redis Streams
async function redisStreams(redis) {
  // Add to stream
  const id = await redis.xadd('events', '*',
    'type', 'user.login',
    'userId', '123',
    'ip', '127.0.0.1'
  );
  console.log('Event ID:', id);

  // Read stream
  const entries = await redis.xrange('events', '-', '+', 'COUNT', 10);
  for (const [id, fields] of entries) {
    const event = {};
    for (let i = 0; i < fields.length; i += 2) event[fields[i]] = fields[i+1];
    console.log('Event:', id, event);
  }

  // Consumer group (for reliable processing)
  await redis.xgroup('CREATE', 'events', 'processors', '0', 'MKSTREAM').catch(() => {});
  const messages = await redis.xreadgroup('GROUP', 'processors', 'worker-1', 'COUNT', 10, 'STREAMS', 'events', '>');
  if (messages) {
    for (const [stream, entries] of messages) {
      for (const [id, fields] of entries) {
        // Process message
        await redis.xack('events', 'processors', id); // Acknowledge
      }
    }
  }
}
```

---

## Step 8: Capstone — Caching Pattern

```javascript
// Cache-aside pattern (educational, without live Redis)
class Cache {
  #store = new Map();
  #ttls = new Map();

  set(key, value, ttlMs = 60000) {
    this.#store.set(key, value);
    this.#ttls.set(key, Date.now() + ttlMs);
    return 'OK';
  }

  get(key) {
    const expiry = this.#ttls.get(key);
    if (!expiry || Date.now() > expiry) {
      this.#store.delete(key);
      this.#ttls.delete(key);
      return null;
    }
    return this.#store.get(key);
  }

  del(key) { this.#store.delete(key); this.#ttls.delete(key); return 1; }
  exists(key) { return this.get(key) !== null ? 1 : 0; }
}

async function cachedFetch(cache, key, fetchFn, ttl = 60000) {
  const cached = cache.get(key);
  if (cached !== null) { console.log('Cache HIT:', key); return JSON.parse(cached); }
  console.log('Cache MISS:', key);
  const data = await fetchFn();
  cache.set(key, JSON.stringify(data), ttl);
  return data;
}

const cache = new Cache();
const db = { users: { '1': { id: 1, name: 'Alice' } } };
const fetchUser = (id) => async () => db.users[id];

(async () => {
  const u1 = await cachedFetch(cache, 'user:1', fetchUser('1'));
  const u2 = await cachedFetch(cache, 'user:1', fetchUser('1')); // HIT
  console.log(u1.name, u2.name);
  console.log('Cache keys:', cache.exists('user:1'));
})();
```

**Run verification (simulated Redis):**
```bash
docker run --rm node:20-alpine sh -c "node -e '
// Simulate Redis cache operations
const store = new Map(); const ttls = new Map();
const redis = {
  set: (k, v, ex, ttl) => { store.set(k, v); ttls.set(k, Date.now() + (ttl||60)*1000); return \"OK\"; },
  get: (k) => { const exp = ttls.get(k); return (!exp || Date.now() > exp) ? null : store.get(k); },
  incr: (k) => { const v = parseInt(redis.get(k) || 0) + 1; redis.set(k, String(v)); return v; },
  del: (k) => { store.delete(k); ttls.delete(k); return 1; },
  exists: (k) => redis.get(k) !== null ? 1 : 0,
  sadd: (k, ...v) => { const s = new Set(store.get(k) ? JSON.parse(store.get(k)) : []); v.forEach(x => s.add(x)); store.set(k, JSON.stringify([...s])); return v.length; },
  smembers: (k) => JSON.parse(store.get(k) || \"[]\"),
};

redis.set(\"user:name\", \"Alice\"); console.log(\"GET:\", redis.get(\"user:name\"));
redis.set(\"counter\", \"0\"); [1,2,3].forEach(() => redis.incr(\"counter\")); console.log(\"Counter:\", redis.get(\"counter\"));
redis.sadd(\"tags\", \"js\", \"node\", \"redis\", \"js\"); console.log(\"Tags:\", redis.smembers(\"tags\"));
redis.del(\"user:name\"); console.log(\"After del:\", redis.exists(\"user:name\"));
'" 2>/dev/null
```

📸 **Verified Output (simulated):**
```
GET: Alice
Counter: 3
Tags: [ 'js', 'node', 'redis' ]
After del: 0
```

---

## Summary

| Data Type | Commands | Use Case |
|-----------|---------|----------|
| String | SET/GET/INCR/MSET | Simple values, counters, sessions |
| Hash | HSET/HGETALL/HINCRBY | Object storage (user profiles) |
| List | RPUSH/LPOP/BLPOP | Queues, recent items |
| Set | SADD/SMEMBERS/SINTER | Tags, unique members |
| ZSet | ZADD/ZRANGE/ZINCRBY | Leaderboards, rate limiting |
| Stream | XADD/XREAD/XGROUP | Event sourcing, message queues |
| Pipeline | `redis.pipeline()` | Batch multiple commands |
| Multi | `redis.multi()` | Atomic transactions |
| Pub/Sub | PUBLISH/SUBSCRIBE | Real-time messaging |
| Lua | `redis.eval()` | Complex atomic operations |
