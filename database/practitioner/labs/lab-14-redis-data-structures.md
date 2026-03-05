# Lab 14: Redis Data Structures

**Time:** 40 minutes | **Level:** Practitioner | **DB:** Redis 7

Redis is an in-memory data structure store. Unlike traditional databases, it natively understands Strings, Hashes, Lists, Sets, Sorted Sets — and many operations are O(1). This makes it ideal for caching, session storage, leaderboards, and real-time analytics.

---

## Step 1 — Setup and Connection

```bash
docker run -d --name redis-lab redis:7
sleep 2
docker exec -it redis-lab redis-cli

# Verify connection
PING
# PONG

# Clear all data (dev only!)
FLUSHALL
```

📸 **Verified Output:**
```
PONG
OK
```

---

## Step 2 — Strings: The Foundation

Strings are the simplest Redis type — a key maps to a byte sequence (binary-safe, up to 512MB).

```bash
# Basic SET / GET
SET user:1:name "Alice"
GET user:1:name
# "Alice"

SET user:1:age 30
GET user:1:age
# "30"

# Atomic increment / decrement
INCR  user:1:login_count   # 1
INCR  user:1:login_count   # 2
INCR  user:1:login_count   # 3
INCRBY user:1:login_count 10   # 13
DECR  user:1:login_count   # 12

# String with expiry (TTL in seconds)
SETEX session:abc123 3600 "user:1"
TTL   session:abc123    # 3600
# OR:
SET session:def456 "user:2" EX 1800

# Append
SET   greeting "Hello"
APPEND greeting ", World!"
GET   greeting              # "Hello, World!"
STRLEN greeting             # 13

# Atomic SET if Not eXists (NX)
SET lock:resource "locked" NX EX 30
# OK if acquired, (nil) if already exists
```

📸 **Verified Output:**
```
Alice
3600
Hello, World!
13
OK
```

> 💡 Redis strings are binary-safe — they can store JSON, images, serialized objects, anything. The limit is 512MB per value.

---

## Step 3 — Hashes: Object Storage

Hashes map string fields to string values — perfect for storing objects without serializing the whole thing.

```bash
# HSET: set one or multiple fields
HSET product:1001 name "Laptop Pro" price 1299.99 stock 50 category Electronics

# HGET: get single field
HGET product:1001 name     # "Laptop Pro"
HGET product:1001 price    # "1299.99"

# HGETALL: get all fields and values
HGETALL product:1001
# 1) "name"       2) "Laptop Pro"
# 3) "price"      4) "1299.99"
# 5) "stock"      6) "50"
# 7) "category"   8) "Electronics"

# HMGET: get multiple fields at once
HMGET product:1001 name price stock

# HINCRBY: increment numeric field
HINCRBY product:1001 stock -5   # 45 (sold 5)
HGET product:1001 stock         # "45"

# HINCRBYFLOAT: for floats
HINCRBYFLOAT product:1001 price 50.00  # 1349.99

# HDEL: delete a field
HDEL product:1001 category

# HEXISTS: check field existence
HEXISTS product:1001 name     # 1 (exists)
HEXISTS product:1001 color    # 0 (doesn't exist)

# HKEYS / HVALS / HLEN
HKEYS product:1001
HLEN  product:1001    # 3
```

📸 **Verified Output:**
```
4
Laptop Pro
1299.99
4
45
```

> 💡 Hashes are more memory-efficient than storing the same data as separate string keys. `user:1:name` + `user:1:email` + `user:1:age` costs 3 key overhead; `HSET user:1 name email age` costs 1.

---

## Step 4 — Lists: Ordered Sequences

Lists are ordered sequences of strings — insertion order preserved. Support both stack (LIFO) and queue (FIFO) patterns.

```bash
# RPUSH: push to right (end) — queue producer
RPUSH task:queue "process_order:1"
RPUSH task:queue "send_email:2"
RPUSH task:queue "generate_report:3"

# LPUSH: push to left (front) — priority insert
LPUSH task:queue "urgent:fix_bug"

# LRANGE: get elements (0 = first, -1 = last)
LRANGE task:queue 0 -1
# 1) "urgent:fix_bug"
# 2) "process_order:1"
# 3) "send_email:2"
# 4) "generate_report:3"

LLEN task:queue    # 4

# LPOP / RPOP: consume from list
LPOP task:queue    # "urgent:fix_bug"
RPOP task:queue    # "generate_report:3"

LRANGE task:queue 0 -1   # ["process_order:1", "send_email:2"]

# LINDEX: get by position
LINDEX task:queue 0     # "process_order:1"

# LSET: update by position
LSET task:queue 0 "process_order:1:UPDATED"

# LINSERT: insert before/after a pivot
LINSERT task:queue BEFORE "send_email:2" "pre_send_check"
LRANGE task:queue 0 -1

# BLPOP: blocking pop (waits up to N seconds for an element)
# BLPOP task:queue 5     # wait up to 5 seconds
```

📸 **Verified Output (LRANGE after pushes):**
```
1) "urgent:fix_bug"
2) "process_order:1"
3) "send_email:2"
4) "generate_report:3"
```

> 💡 Lists are ideal for **message queues** (RPUSH + BLPOP) and **activity feeds** (LPUSH + LRANGE 0 N). For a task queue, have producers RPUSH and workers BLPOP.

---

## Step 5 — Sets: Unique Collections

Sets are unordered collections of unique strings. O(1) add/remove/check, O(N) set operations.

```bash
# SADD: add members (duplicates ignored)
SADD online:users "alice" "bob" "carol" "dave"
SADD online:users "alice"   # 0 (already exists)

SADD premium:users "alice" "carol" "eve"
SADD admin:users  "alice" "frank"

# SMEMBERS: get all members
SMEMBERS online:users

# SCARD: count members
SCARD online:users    # 4

# SISMEMBER: check membership (O(1))
SISMEMBER online:users "alice"   # 1
SISMEMBER online:users "zara"    # 0

# SMISMEMBER: check multiple (Redis 6.2+)
SMISMEMBER online:users "alice" "bob" "zara"   # 1 1 0

# Set operations
SINTER  online:users premium:users   # Intersection: online AND premium
SUNION  online:users premium:users   # Union: online OR premium
SDIFF   online:users premium:users   # Difference: online but NOT premium

# Store result of set operation
SINTERSTORE active:premium online:users premium:users
SMEMBERS active:premium

# Remove members
SREM online:users "dave"
```

📸 **Verified Output:**
```
1) "alice"
2) "bob"
3) "carol"
4) "dave"
SINTER: alice, carol
SUNION: alice, bob, carol, dave, eve
SDIFF:  bob, dave
```

---

## Step 6 — Sorted Sets: Ranked Data

Sorted Sets are like Sets but each member has a **score** (float). Members are always sorted by score. Perfect for leaderboards, priority queues, time-series.

```bash
# ZADD: add member with score
ZADD leaderboard 9850 "Alice"
ZADD leaderboard 8720 "Bob"
ZADD leaderboard 9200 "Carol"
ZADD leaderboard 7500 "Dave"
ZADD leaderboard 9850 "Eve"    # same score as Alice

# ZRANGE: get members by rank (lowest score first)
ZRANGE leaderboard 0 -1 WITHSCORES

# ZRANGE REV: descending (Redis 6.2+)
ZRANGE leaderboard 0 4 WITHSCORES REV
# or: ZREVRANGE leaderboard 0 4 WITHSCORES

# ZINCRBY: add to score
ZINCRBY leaderboard 200 "Bob"    # Bob: 8920
ZINCRBY leaderboard 500 "Dave"   # Dave: 8000

# ZRANGEBYSCORE: get by score range
ZRANGEBYSCORE leaderboard 9000 "+inf" WITHSCORES
# Members with score >= 9000

# ZRANK / ZREVRANK: get position (0-indexed)
ZREVRANK leaderboard "Alice"   # 0 (top)
ZREVRANK leaderboard "Dave"    # 4 (lowest)

# ZSCORE: get score of a specific member
ZSCORE leaderboard "Carol"    # "9200"

# ZCOUNT: count members in score range
ZCOUNT leaderboard 8000 9500    # 3

# ZPOPMAX / ZPOPMIN: pop highest/lowest scoring
ZPOPMAX leaderboard 1    # Remove and return top scorer
```

📸 **Verified Output:**
```
ZRANGE REV:
1) "Eve"    2) "9850"
3) "Alice"  4) "9850"
5) "Carol"  6) "9200"
7) "Bob"    8) "8920"
9) "Dave"   10) "8000"

ZRANGEBYSCORE 9000 +inf:
Carol 9200
Alice 9850
Eve   9850
```

---

## Step 7 — Type Inspection and Key Management

```bash
# TYPE: check what type a key is
TYPE user:1:name         # string
TYPE product:1001        # hash
TYPE task:queue          # list
TYPE online:users        # set
TYPE leaderboard         # zset

# EXISTS / DEL
EXISTS user:1:name       # 1
DEL    user:1:name
EXISTS user:1:name       # 0

# EXPIRE: set TTL on any key
EXPIRE leaderboard 86400  # expire in 24 hours
TTL    leaderboard        # seconds remaining
PERSIST leaderboard       # remove TTL

# RENAME
RENAME leaderboard game:leaderboard

# SCAN: iterate keys (safe for production, unlike KEYS)
SCAN 0 MATCH "user:*" COUNT 100
```

---

## Step 8 — Capstone: Social Media Data Model

```bash
# Model a social media app in Redis

# User profile (Hash)
HSET user:1001 username alice name "Alice Smith" bio "Engineer" followers 1250 following 340

# Session (String with TTL)
SET session:tok_abc123 "user:1001" EX 3600

# User's feed (List — most recent first)
LPUSH feed:1001 "post:500" "post:499" "post:498"
LRANGE feed:1001 0 9    # latest 10 posts

# User's interests (Set)
SADD interests:1001 "technology" "python" "databases"

# Global trending tags (Sorted Set — score = mention count)
ZADD trending:tags 1523 "python" 987 "redis" 2341 "databases" 445 "docker"
ZRANGE trending:tags 0 4 WITHSCORES REV   # top 5 trending

# User notifications (List)
RPUSH notifications:1001 '{"type":"like","from":"bob","post":"post:500"}'
RPUSH notifications:1001 '{"type":"follow","from":"carol"}'

# Mutual followers (Set intersection)
SADD followers:1001 "bob" "carol" "dave"
SADD followers:1002 "alice" "carol" "eve"
SINTER followers:1001 followers:1002   # mutual: carol

# Daily active users (Set — track by day)
SADD dau:2024-01-15 "user:1001" "user:1002" "user:1003"
SCARD dau:2024-01-15    # 3 DAU

# Verify all keys created
SCAN 0 COUNT 100
```

---

## Summary

| Structure | Best For | Key Commands |
|-----------|---------|--------------|
| **String** | Simple values, counters, JSON blobs | GET/SET, INCR, SETEX |
| **Hash** | Object with multiple fields | HSET/HGET, HGETALL, HINCRBY |
| **List** | Queues, feeds, ordered history | LPUSH/RPUSH, LRANGE, BLPOP |
| **Set** | Unique membership, set math | SADD/SMEMBERS, SINTER/SUNION |
| **Sorted Set** | Leaderboards, ranked data | ZADD/ZRANGE, ZINCRBY, ZRANGEBYSCORE |
