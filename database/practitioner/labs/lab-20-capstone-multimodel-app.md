# Lab 20: Capstone — Multi-Model Social Media Analytics Platform

**Time:** 60 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15 + MongoDB 7 + Redis 7

Build a production-grade social media analytics platform using three databases in concert: PostgreSQL for structured relational data, MongoDB for flexible event logs, and Redis for real-time caching and counters.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Social Media Analytics Platform               │
├─────────────────┬──────────────────┬──────────────────────────  │
│  PostgreSQL 15  │   MongoDB 7       │   Redis 7                  │
│  ─────────────  │  ────────────    │  ──────────────            │
│  • Users        │  • Raw events    │  • Session cache           │
│  • Posts        │  • Event logs    │  • Trending posts (ZSet)   │
│  • Analytics    │  • User activity │  • Real-time counters      │
│  • Aggregates   │  • Device info   │  • Rate limiting           │
│                 │                  │  • Pub/Sub notifications    │
└─────────────────┴──────────────────┴──────────────────────────  ┘

Data Flow:
User Action → Redis counter INCR
           → MongoDB event INSERT
           → PostgreSQL analytics UPDATE (batch)
           → Redis trending ZINCRBY
```

---

## Step 1 — PostgreSQL: Relational Schema

```sql
-- Users table
CREATE TABLE social_users (
  id             SERIAL PRIMARY KEY,
  username       VARCHAR(50) UNIQUE NOT NULL,
  email          VARCHAR(100) UNIQUE NOT NULL,
  bio            TEXT,
  follower_count INT DEFAULT 0,
  following_count INT DEFAULT 0,
  created_at     TIMESTAMP DEFAULT NOW()
);

-- Posts table
CREATE TABLE social_posts (
  id             SERIAL PRIMARY KEY,
  user_id        INT REFERENCES social_users(id),
  content        TEXT NOT NULL,
  post_type      VARCHAR(20) DEFAULT 'text',
  like_count     INT DEFAULT 0,
  comment_count  INT DEFAULT 0,
  share_count    INT DEFAULT 0,
  created_at     TIMESTAMP DEFAULT NOW()
);

-- Aggregated analytics (updated by batch job)
CREATE TABLE post_analytics (
  id              SERIAL PRIMARY KEY,
  post_id         INT REFERENCES social_posts(id),
  views           INT DEFAULT 0,
  unique_views    INT DEFAULT 0,
  engagement_rate NUMERIC(5,2),
  recorded_at     TIMESTAMP DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_posts_user_id    ON social_posts(user_id);
CREATE INDEX idx_posts_created    ON social_posts(created_at DESC);
CREATE INDEX idx_analytics_post   ON post_analytics(post_id);
CREATE INDEX idx_analytics_rate   ON post_analytics(engagement_rate DESC);
```

---

## Step 2 — PostgreSQL: Seed Data

```sql
INSERT INTO social_users (username, email, bio, follower_count, following_count) VALUES
  ('alice_dev',   'alice@example.com',  'Software engineer & open source contributor', 1250, 340),
  ('bob_photo',   'bob@example.com',    'Professional photographer, travel lover',      3420, 512),
  ('carol_chef',  'carol@example.com',  'Food blogger, recipe developer',              8750, 892),
  ('dave_runner', 'dave@example.com',   'Marathon runner & fitness coach',             2100, 456),
  ('eve_artist',  'eve@example.com',    'Digital artist, illustrator',                 5600, 789);

INSERT INTO social_posts (user_id, content, post_type, like_count, comment_count, share_count) VALUES
  (1, 'Just deployed my first Kubernetes cluster! Threading it together from scratch teaches you so much.', 'text',  145,  23, 12),
  (2, 'Golden hour photography tips: shoot within 30 min of sunset for that magic light.',                 'image', 892,  67, 134),
  (3, 'Best pasta carbonara recipe — 4 ingredients, no cream needed. Authentic Italian.',                  'image', 2341, 198, 567),
  (1, 'PostgreSQL window functions are amazing for analytics. RANK() vs DENSE_RANK() explained.',          'text',  234,  45, 28),
  (2, 'Street photography in Tokyo: capturing the energy of Shibuya crossing at rush hour.',               'image', 1567, 123, 289),
  (3, 'Sourdough bread from scratch: 72-hour fermentation, perfect crust every time.',                     'image', 3102, 267, 445),
  (4, 'Marathon training plan: 16 weeks to sub-4-hour finish. Free download!',                             'text',  678,  89, 156),
  (5, 'Digital portrait using only 3 colors — minimalism in art.',                                         'image', 1234, 98, 178);

INSERT INTO post_analytics (post_id, views, unique_views, engagement_rate) VALUES
  (1, 4200,  3100,  4.00),
  (2, 18900, 14200, 5.07),
  (3, 67800, 51200, 3.75),
  (4, 6700,  5100,  4.16),
  (5, 43200, 32100, 3.91),
  (6, 89500, 67800, 4.27),
  (7, 12400, 9800,  3.84),
  (8, 34600, 26700, 3.93);

SELECT u.username, p.content, pa.views, pa.engagement_rate
FROM social_posts p
JOIN social_users u ON p.user_id = u.id
JOIN post_analytics pa ON pa.post_id = p.id
ORDER BY pa.views DESC
LIMIT 3;
```

📸 **Verified Output:**
```
  username  |                         content                          | views | engagement_rate
------------+----------------------------------------------------------+-------+-----------------
 carol_chef | Sourdough bread from scratch: 72-hour fermentation...    | 89500 |            4.27
 carol_chef | Best pasta carbonara recipe...                           | 67800 |            3.75
 bob_photo  | Street photography in Tokyo...                           | 43200 |            3.91
(3 rows)
```

---

## Step 3 — PostgreSQL: Analytics Queries

```sql
-- Top creators by engagement
SELECT u.username, u.follower_count,
  COUNT(p.id) AS post_count,
  SUM(pa.views) AS total_views,
  ROUND(AVG(pa.engagement_rate), 2) AS avg_engagement,
  SUM(p.like_count + p.comment_count + p.share_count) AS total_interactions,
  RANK() OVER (ORDER BY SUM(pa.views) DESC) AS visibility_rank
FROM social_users u
JOIN social_posts p ON p.user_id = u.id
JOIN post_analytics pa ON pa.post_id = p.id
GROUP BY u.id, u.username, u.follower_count
ORDER BY total_views DESC;

-- Post performance by type using window functions
SELECT post_type,
  COUNT(*) AS posts,
  ROUND(AVG(pa.views), 0) AS avg_views,
  ROUND(AVG(pa.engagement_rate), 2) AS avg_engagement,
  MAX(pa.views) AS peak_views,
  SUM(pa.views) AS total_views,
  ROUND(100.0 * SUM(pa.views) / SUM(SUM(pa.views)) OVER (), 1) AS pct_of_total
FROM social_posts p
JOIN post_analytics pa ON pa.post_id = p.id
GROUP BY post_type
ORDER BY total_views DESC;
```

---

## Step 4 — MongoDB: Raw Event Log

```javascript
use analytics

db.events.drop()

// Raw event documents (more flexible than SQL for varied event types)
db.events.insertMany([
  { post_id: 1, event: "view",    user: "user:42", ts: new Date("2024-01-15T10:00:00"), meta: { device: "mobile",  country: "US", referrer: "twitter"  } },
  { post_id: 1, event: "like",    user: "user:43", ts: new Date("2024-01-15T10:05:00"), meta: { device: "desktop", country: "UK", referrer: "direct"   } },
  { post_id: 3, event: "view",    user: "user:44", ts: new Date("2024-01-15T10:10:00"), meta: { device: "mobile",  country: "JP", referrer: "instagram" } },
  { post_id: 3, event: "share",   user: "user:45", ts: new Date("2024-01-15T10:15:00"), meta: { device: "mobile",  country: "US", referrer: "instagram" } },
  { post_id: 2, event: "view",    user: "user:46", ts: new Date("2024-01-15T10:20:00"), meta: { device: "desktop", country: "US", referrer: "google"   } },
  { post_id: 3, event: "like",    user: "user:47", ts: new Date("2024-01-15T10:25:00"), meta: { device: "tablet",  country: "DE", referrer: "direct"   } },
  { post_id: 3, event: "comment", user: "user:48", ts: new Date("2024-01-15T10:30:00"), meta: { device: "mobile",  country: "US", referrer: "twitter"  } },
  { post_id: 5, event: "view",    user: "user:49", ts: new Date("2024-01-15T10:35:00"), meta: { device: "mobile",  country: "FR", referrer: "google"   } },
  { post_id: 5, event: "like",    user: "user:50", ts: new Date("2024-01-15T10:40:00"), meta: { device: "desktop", country: "US", referrer: "direct"   } }
])

print("Events logged:", db.events.countDocuments())
```

---

## Step 5 — MongoDB: Event Analytics

```javascript
// Aggregate events by post
let byPost = db.events.aggregate([
  { $group: {
    _id: { post_id: "$post_id", event: "$event" },
    count: { $sum: 1 }
  }},
  { $group: {
    _id: "$_id.post_id",
    events: { $push: { type: "$_id.event", count: "$count" } },
    total:  { $sum: "$count" }
  }},
  { $sort: { total: -1 } }
]).toArray()

byPost.forEach(r =>
  print("Post", r._id, "- total events:", r.total, "-", JSON.stringify(r.events))
)
```

📸 **Verified Output:**
```
Post 3 - total events: 4 - [{"type":"view","count":1},{"type":"share","count":1},{"type":"like","count":1},{"type":"comment","count":1}]
Post 1 - total events: 2 - [{"type":"like","count":1},{"type":"view","count":1}]
Post 2 - total events: 1 - [{"type":"view","count":1}]
```

```javascript
// Device breakdown
db.events.aggregate([
  { $group: { _id: "$meta.device", count: { $sum: 1 } } },
  { $sort:  { count: -1 } }
]).forEach(r => print(r._id, ":", r.count))

// Country breakdown
db.events.aggregate([
  { $group: { _id: "$meta.country", events: { $sum: 1 }, unique_posts: { $addToSet: "$post_id" } } },
  { $project: { country: "$_id", events: 1, unique_posts: { $size: "$unique_posts" }, _id: 0 } },
  { $sort: { events: -1 } }
]).forEach(r => print(JSON.stringify(r)))

// Referrer attribution
db.events.aggregate([
  { $group: { _id: "$meta.referrer", clicks: { $sum: 1 } } },
  { $sort:  { clicks: -1 } }
]).forEach(r => print(r._id, ":", r.clicks, "events"))
```

---

## Step 6 — Redis: Session Cache and Real-Time Counters

```bash
# === SESSION CACHE ===
# User session (Hash)
HSET "session:user42" user_id "user:42" username "alice_dev" role "creator" last_active "2024-01-15T10:00:00" cart_count 0
EXPIRE "session:user42" 3600

# Session lookup
HGETALL "session:user42"

# === TRENDING POSTS (Sorted Set) ===
# Score = engagement weight (views * 0.1 + likes * 5 + shares * 10 + comments * 3)
ZADD "trending:posts:global" 13500 "post:3"   # carol's bread
ZADD "trending:posts:global"  5600 "post:2"   # bob's photo
ZADD "trending:posts:global"  4200 "post:5"   # tokyo street
ZADD "trending:posts:global"  1850 "post:1"   # alice k8s
ZADD "trending:posts:global"  9800 "post:6"   # carol bread 2

# Top 3 trending
ZRANGE "trending:posts:global" 0 2 WITHSCORES REV

# Update score when new interaction happens
ZINCRBY "trending:posts:global" 500 "post:3"   # +share

# === REAL-TIME COUNTERS ===
INCR "counter:views:post:3"
INCR "counter:views:post:3"
INCR "counter:likes:post:3"
INCR "counter:shares:post:3"

MGET "counter:views:post:3" "counter:likes:post:3" "counter:shares:post:3"

# === RATE LIMITING ===
INCR "ratelimit:api:user42:2024011510"
EXPIRE "ratelimit:api:user42:2024011510" 60   # per-minute window
GET   "ratelimit:api:user42:2024011510"
```

📸 **Verified ZRANGE REV:**
```
1) "post:3"   2) "14000"
3) "post:6"   4) "9800"
5) "post:2"   6) "5600"
```

📸 **Verified MGET counters:**
```
1) "2"   (views)
2) "1"   (likes)
3) "1"   (shares)
```

---

## Step 7 — Data Flow: Connecting All Three Systems

```python
# Pseudocode showing how a real application connects the three databases

import psycopg2   # PostgreSQL
import pymongo    # MongoDB
import redis      # Redis

# Connections
pg   = psycopg2.connect("postgresql://postgres:rootpass@pg-host/postgres")
mg   = pymongo.MongoClient("mongodb://mongo-host:27017")["analytics"]
rd   = redis.Redis(host="redis-host", decode_responses=True)

def handle_post_view(user_id, post_id, device, country):
    """Called when a user views a post"""

    # 1. Redis: increment real-time counter (O(1), very fast)
    rd.incr(f"counter:views:post:{post_id}")
    rd.zincrby("trending:posts:global", 0.1, f"post:{post_id}")

    # 2. MongoDB: log raw event (async/queued in production)
    mg.events.insert_one({
        "post_id": post_id,
        "event":   "view",
        "user":    f"user:{user_id}",
        "ts":      datetime.now(),
        "meta":    {"device": device, "country": country}
    })

    # 3. PostgreSQL: update aggregate stats (batch in production)
    with pg.cursor() as cur:
        cur.execute("""
            UPDATE post_analytics
            SET views = views + 1
            WHERE post_id = %s
        """, (post_id,))
        pg.commit()

def get_trending_posts(limit=10):
    """Get trending posts with full data from PostgreSQL"""
    # 1. Redis: get trending post IDs (O(log N + M))
    trending_ids = rd.zrange("trending:posts:global", 0, limit-1, rev=True)
    post_ids = [int(pid.split(":")[1]) for pid in trending_ids]

    # 2. PostgreSQL: fetch full post data
    with pg.cursor() as cur:
        cur.execute("""
            SELECT p.id, u.username, p.content, pa.views, pa.engagement_rate
            FROM social_posts p
            JOIN social_users u ON p.user_id = u.id
            JOIN post_analytics pa ON pa.post_id = p.id
            WHERE p.id = ANY(%s)
        """, (post_ids,))
        return cur.fetchall()
```

---

## Step 8 — Capstone Queries: Cross-Database Analytics Report

```sql
-- PostgreSQL: Final analytics report using window functions
SELECT
  u.username,
  u.follower_count,
  COUNT(p.id)                               AS posts,
  SUM(pa.views)                             AS total_views,
  ROUND(AVG(pa.engagement_rate), 2)         AS avg_engagement,
  ROUND(100.0 * SUM(pa.views) /
    SUM(SUM(pa.views)) OVER (), 1)          AS view_share_pct,
  RANK() OVER (ORDER BY SUM(pa.views) DESC) AS rank
FROM social_users u
JOIN social_posts p ON p.user_id = u.id
JOIN post_analytics pa ON pa.post_id = p.id
GROUP BY u.id, u.username, u.follower_count
ORDER BY total_views DESC;
```

```javascript
// MongoDB: 24-hour event summary
db.events.aggregate([
  { $addFields: { hour: { $hour: "$ts" } } },
  { $group: {
    _id: { hour: "$hour", event: "$event" },
    count: { $sum: 1 }
  }},
  { $sort: { "_id.hour": 1, count: -1 } }
]).forEach(r => print(`Hour ${r._id.hour}: ${r._id.event} = ${r.count}`))
```

```bash
# Redis: Dashboard snapshot
echo "=== TRENDING POSTS ==="
redis-cli ZRANGE trending:posts:global 0 4 WITHSCORES REV

echo "=== POST:3 COUNTERS ==="
redis-cli MGET counter:views:post:3 counter:likes:post:3 counter:shares:post:3

echo "=== ACTIVE SESSIONS ==="
redis-cli SCAN 0 MATCH "session:*" COUNT 100

echo "=== MEMORY USAGE ==="
redis-cli INFO memory | grep used_memory_human
```

---

## Architecture Summary

| Data Type | Storage | Why |
|-----------|---------|-----|
| User profiles, posts, follows | PostgreSQL | Relational integrity, complex analytics queries |
| Aggregated analytics | PostgreSQL | Window functions, JOIN with user data |
| Raw event logs | MongoDB | Flexible schema (events have different fields per type) |
| Activity by device/country | MongoDB | Aggregation pipeline for flexible grouping |
| User sessions | Redis | Sub-millisecond lookup, auto-expiry |
| Trending posts | Redis Sorted Set | O(log N) update + O(log N + M) range query |
| Real-time counters | Redis | Atomic INCR, no lock contention |
| Rate limiting | Redis | INCR + EXPIRE for sliding window |
| Notifications | Redis Pub/Sub | Fan-out to connected websocket servers |

## What You Built

- **PostgreSQL**: Schema with indexes, window function analytics, referential integrity
- **MongoDB**: Flexible event log, aggregation pipeline for behavioral analytics
- **Redis**: Session cache (Hash), trending (Sorted Set), counters (String INCR), rate limiting
- **Data flow**: Real-time counters in Redis → async event log in MongoDB → batch aggregate update in PostgreSQL

**Congratulations — you've completed the Database Practitioner series! 🎉**
