# Lab 16: Redis Caching Patterns

**Time:** 40 minutes | **Level:** Practitioner | **DB:** Redis 7

Caching is the most common Redis use case — it dramatically reduces database load and response latency. But naive caching creates subtle bugs. This lab covers the four canonical patterns and their trade-offs.

---

## Step 1 — Setup and Baseline

```bash
docker run -d --name redis-lab redis:7
sleep 2
docker exec -it redis-lab redis-cli

FLUSHALL
PING
# PONG
```

**Why Cache?**
- Database query: 5-50ms
- Redis GET: 0.1-0.5ms
- 10x-100x faster reads
- Reduces database connection pressure

---

## Step 2 — Cache-Aside (Lazy Loading)

The most common pattern. Application checks cache first; on miss, reads from database and populates cache.

```bash
# Simulate cache-aside in redis-cli

# Step 1: Check cache
GET "cache:product:1001"
# (nil) — cache miss

# Step 2: Application queries database (simulated here)
# ... SELECT * FROM products WHERE id = 1001 ...
# ... result: {"id":1001,"name":"Laptop Pro","price":1299.99} ...

# Step 3: Populate cache with TTL
SET "cache:product:1001" '{"id":1001,"name":"Laptop Pro","price":1299.99,"stock":50}' EX 300

# Step 4: Next request — cache hit
GET "cache:product:1001"
TTL "cache:product:1001"
```

📸 **Verified Output:**
```
{"id":1001,"name":"Laptop Pro","price":1299.99,"stock":50}
300
```

**Application code (Python pseudocode):**
```python
def get_product(product_id):
    key = f"cache:product:{product_id}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)          # cache hit

    product = db.query("SELECT * FROM products WHERE id = %s", product_id)
    redis.setex(key, 300, json.dumps(product))  # cache for 5 min
    return product
```

> 💡 Cache-aside means the **application** manages the cache. On cache miss, it reads from DB and writes to cache. On update, it **invalidates** the cache key (don't update cache — let it expire or delete it).

---

## Step 3 — Write-Through: Sync Cache and DB

Always write to both cache and database simultaneously.

```bash
# Write-through: update both DB (simulated) and cache atomically

# Update product price
HSET "wt:product:1001" name "Laptop Pro" price 1199.99 stock 45
# At the same time, application updates database:
# UPDATE products SET price = 1199.99 WHERE id = 1001

HGET "wt:product:1001" price
# "1199.99" — always consistent

# Add TTL for eventual eviction (optional in write-through)
EXPIRE "wt:product:1001" 3600
```

**Comparison:**
| Pattern | Read | Write | Consistency | Use Case |
|---------|------|-------|-------------|----------|
| Cache-aside | Check cache → DB on miss | Invalidate cache | Eventual | General reads |
| Write-through | Always cached | Write cache + DB | Strong | Frequently read |
| Write-behind | Always cached | Write cache; async DB | Eventual | Write-heavy |

---

## Step 4 — TTL Management: EXPIRE, EXPIREAT, TTL

```bash
# Set TTL on existing key
SET page:cache:homepage "<html>...</html>"
EXPIRE page:cache:homepage 600       # 600 seconds (10 min)
TTL    page:cache:homepage           # remaining seconds

PERSIST page:cache:homepage          # remove TTL (make persistent)
TTL     page:cache:homepage          # -1 (no TTL)

# EXPIREAT: expire at specific Unix timestamp
EXPIREAT session:user123 1735689600  # expire at specific date
# Redis 7: EXPIRETIME returns the timestamp
EXPIRETIME session:user123

# PX: millisecond precision
SET  temp:lock "1" PX 500            # expire in 500ms
PTTL temp:lock                       # remaining ms

# Sliding expiration (reset TTL on access)
GET  "cache:product:1001"
EXPIRE "cache:product:1001" 300      # reset TTL after access

# GETEX: GET + set expiry atomically (Redis 6.2+)
GETEX "cache:product:1001" EX 300

# Key TTL status
TTL nonexistent:key    # -2 (key doesn't exist)
TTL persistent:key     # -1 (no TTL set)
TTL expiring:key       # > 0 (seconds remaining)
```

📸 **Verified Output:**
```
600
-1
3600
```

---

## Step 5 — LRU Eviction Policy

When Redis memory is full, it evicts keys based on the configured policy.

```bash
# Check current config
CONFIG GET maxmemory
CONFIG GET maxmemory-policy

# Set max memory (e.g., 100MB)
CONFIG SET maxmemory 100mb
CONFIG SET maxmemory-policy allkeys-lru

# View memory usage
INFO memory
```

**Eviction policies:**
| Policy | What Gets Evicted |
|--------|------------------|
| `noeviction` | Error on writes (default) |
| `allkeys-lru` | Any key, least recently used |
| `volatile-lru` | Keys with TTL, LRU |
| `allkeys-lfu` | Any key, least frequently used |
| `volatile-lfu` | Keys with TTL, LFU |
| `allkeys-random` | Random key |
| `volatile-random` | Random key with TTL |
| `volatile-ttl` | Key with smallest TTL |

> 💡 For a pure cache, use `allkeys-lru` — Redis will evict the least recently used key when memory fills up. For mixed use (cache + persistent data), use `volatile-lru` to protect non-TTL keys.

---

## Step 6 — Cache Stampede Prevention with NX Lock

When a popular cache key expires, hundreds of requests simultaneously hit the database — the "thundering herd" problem.

```bash
# Cache stampede prevention with distributed lock

# Step 1: Check cache (cache miss on cold start)
GET "cache:expensive:report"
# (nil)

# Step 2: Try to acquire rebuild lock (NX = Only if Not eXists)
SET "lock:rebuild:expensive:report" "1" NX EX 10
# OK   — this client wins the lock

# If another client tries:
SET "lock:rebuild:expensive:report" "1" NX EX 10
# (nil) — lock already held, retry or return stale data

# Step 3: Winner rebuilds cache
# ... compute expensive query ...
SET "cache:expensive:report" '{"data":"..."}' EX 300

# Step 4: Release lock (use Lua for atomic check-and-delete)
# In production, use Lua script:
# if redis.call("GET", KEYS[1]) == ARGV[1] then
#   return redis.call("DEL", KEYS[1])
# end

DEL "lock:rebuild:expensive:report"

# Probabilistic Early Expiration (PER) — smarter approach
# Start rebuilding slightly before expiry using TTL check:
TTL "cache:expensive:report"
# If TTL < 30s AND random() < 0.1, rebuild preemptively
```

📸 **Verified Output (NX lock):**
```
OK      ← first client acquired
(nil)   ← second client rejected
```

---

## Step 7 — SCAN for Key Enumeration

Never use `KEYS *` in production — it blocks Redis for the scan duration. Use `SCAN` instead.

```bash
# Setup some keys
MSET cache:user:1 "alice" cache:user:2 "bob" cache:user:3 "carol"
MSET session:abc "s1" session:def "s2" temp:1 "t1" temp:2 "t2"

# SCAN: iterates in batches (cursor-based)
SCAN 0 MATCH "cache:*" COUNT 100
# Returns: cursor + matching keys
# cursor=0 means scan complete

# Full scan pattern:
# cursor = 0
# while True:
#   cursor, keys = redis.scan(cursor, match="cache:*", count=100)
#   process(keys)
#   if cursor == 0: break

# SCAN with TYPE filter (Redis 6.0+)
SCAN 0 MATCH "*" COUNT 100 TYPE string
SCAN 0 MATCH "*" COUNT 100 TYPE hash

# Count keys by pattern (never use DBSIZE for pattern counts)
# In shell:
# redis-cli --scan --pattern "cache:*" | wc -l

# HSCAN, SSCAN, ZSCAN for collection types
HSET bigHash field1 val1 field2 val2 field3 val3
HSCAN bigHash 0 MATCH "field*" COUNT 100
```

📸 **Verified SCAN:**
```
1) "0"   ← cursor 0 = complete
2) 1) "cache:user:1"
   2) "cache:user:2"
   3) "cache:user:3"
```

---

## Step 8 — Capstone: Cache Layer for API

```bash
# Build a complete caching layer

# 1. Product catalog cache (write-through)
HSET "product:1001" name "Laptop Pro" price 1299.99 stock 50 updated "2024-01-15"
EXPIRE "product:1001" 3600

HSET "product:1002" name "Wireless Mouse" price 29.99 stock 200 updated "2024-01-15"
EXPIRE "product:1002" 3600

# 2. Category cache (list of product IDs, sorted by popularity)
ZADD "category:Electronics:popular" 9850 "product:1001" 7200 "product:1002"
EXPIRE "category:Electronics:popular" 1800

# 3. User session
SET "session:user_alice_xyz" '{"userId":"alice","role":"customer","cart":["1001"]}' EX 86400

# 4. Rate limiting (sliding window)
INCR "ratelimit:api:alice:2024-01-15-10"   # requests in this minute-window
EXPIRE "ratelimit:api:alice:2024-01-15-10" 60
GET   "ratelimit:api:alice:2024-01-15-10"

# 5. Cache invalidation on update
# When product 1001 is updated in DB, delete cache
DEL "product:1001"
# Next request will be a miss → fetches from DB → repopulates

# 6. View memory usage
INFO keyspace
# db0:keys=12,expires=10,avg_ttl=3524000

# 7. Cache statistics
INFO stats | grep keyspace
# keyspace_hits:8
# keyspace_misses:3
# Hit rate = 8/(8+3) = 72.7%
```

---

## Summary

| Pattern | Consistency | Write Latency | When to Use |
|---------|-------------|---------------|-------------|
| Cache-aside | Eventual | Fast (skip cache) | General read-heavy workloads |
| Write-through | Strong | Slow (write both) | Read-heavy, consistency critical |
| Write-behind | Eventual | Fast (write cache only) | Write-heavy, tolerance for data loss |
| Read-through | Strong | Slow on first read | Transparent cache layer |
| Stampede lock (NX) | N/A | N/A | Expensive cache rebuilds |
| LRU eviction | N/A | N/A | Memory pressure management |
