# Lab 15: Redis Pub/Sub and Streams

**Time:** 40 minutes | **Level:** Practitioner | **DB:** Redis 7

Redis Pub/Sub enables real-time messaging (fire-and-forget, no persistence). Redis Streams (added in Redis 5.0) add persistence, consumer groups, and at-least-once delivery — making them suitable for event sourcing and reliable message queues.

---

## Step 1 — Pub/Sub: Concepts

```
Publisher                  Redis               Subscriber(s)
──────────              ──────────           ──────────────
PUBLISH channel msg  →   channel:msg    →   SUBSCRIBE channel
                                        →   SUBSCRIBE channel (multiple)
```

**Key characteristics:**
- Fire-and-forget: messages are lost if no subscriber is listening
- No message persistence
- Fan-out: one publish reaches all subscribers
- Pattern subscriptions: `PSUBSCRIBE events.*` matches multiple channels

---

## Step 2 — Pub/Sub: Basic Example

Open two terminals:

**Terminal 1 (subscriber):**
```bash
docker exec -it redis-lab redis-cli
SUBSCRIBE notifications
# Waiting for messages...
```

**Terminal 2 (publisher):**
```bash
docker exec -it redis-lab redis-cli
PUBLISH notifications "User Alice logged in"
PUBLISH notifications "New order #1234 placed"
PUBLISH notifications "System alert: high CPU"
```

**Terminal 1 sees:**
```
1) "message"
2) "notifications"
3) "User Alice logged in"

1) "message"
2) "notifications"
3) "New order #1234 placed"
```

> 💡 `SUBSCRIBE` blocks the connection — you can only issue `SUBSCRIBE`, `UNSUBSCRIBE`, `PSUBSCRIBE`, `PUNSUBSCRIBE`, or `QUIT` on a subscribed connection.

---

## Step 3 — Pattern Subscriptions with PSUBSCRIBE

**Terminal 1 (pattern subscriber):**
```bash
PSUBSCRIBE events.*
# Matches: events.user, events.order, events.system
```

**Terminal 2 (publisher):**
```bash
PUBLISH events.user   "alice:login"
PUBLISH events.order  "order:1234:placed"
PUBLISH events.system "cpu:85%"
PUBLISH other.channel "this won't match"
```

**Terminal 1 sees:**
```
1) "pmessage"
2) "events.*"         ← pattern matched
3) "events.user"      ← actual channel
4) "alice:login"      ← message
```

```bash
# Subscribe to multiple channels
SUBSCRIBE channel1 channel2 channel3

# Unsubscribe from specific channel
UNSUBSCRIBE channel2

# PUBSUB commands (admin)
PUBSUB CHANNELS          # list active channels
PUBSUB CHANNELS events.* # filter by pattern
PUBSUB NUMSUB notifications events.user  # subscriber counts
PUBSUB NUMPAT            # number of pattern subscriptions
```

---

## Step 4 — Redis Streams: Adding Messages

Redis Streams store data as append-only logs. Each entry has a unique ID and key-value fields.

```bash
# XADD: append to stream
# '*' = auto-generate ID (milliseconds-sequenceNumber)
XADD events:stream '*' event_type "page_view" user_id "user:1" url "/products" ip "192.168.1.1"
XADD events:stream '*' event_type "add_to_cart" user_id "user:2" product_id "prod:1001" quantity "2"
XADD events:stream '*' event_type "purchase" user_id "user:1" order_id "order:5001" amount "1299.99"

# XLEN: count messages
XLEN events:stream     # 3

# XRANGE: read messages (- = min ID, + = max ID)
XRANGE events:stream - +
```

📸 **Verified Output:**
```
1) 1) "1772726175603-0"
   2) 1) "event_type" 2) "page_view" 3) "user_id" 4) "user:1" ...
2) 1) "1772726175829-0"
   2) 1) "event_type" 2) "add_to_cart" ...
3) 1) "1772726176059-0"
   2) 1) "event_type" 2) "purchase" ...
```

> 💡 Stream IDs are `milliseconds-sequenceNumber`. You can specify explicit IDs like `XADD stream '1699900000000-0' ...` for deterministic testing or event replay.

---

## Step 5 — XREAD and Stream Trimming

```bash
# XREAD: read messages from one or more streams
XREAD COUNT 2 STREAMS events:stream 0    # from the beginning, max 2

# Non-blocking read of new messages (like BLPOP for streams)
# XREAD BLOCK 5000 STREAMS events:stream $
# ($  = only new messages after command is issued)

# Read from specific ID (get everything after a known message)
XREAD COUNT 10 STREAMS events:stream 1772726175829-0

# XREVRANGE: read in reverse (newest first)
XREVRANGE events:stream + - COUNT 2

# XRANGE with COUNT for pagination
XRANGE events:stream - + COUNT 2   # first 2
XRANGE events:stream 1772726175829-1 + COUNT 2  # next page

# Stream trimming: prevent unbounded growth
XADD events:stream MAXLEN 1000 '*' event_type "heartbeat"
# Keeps at most 1000 messages (approximate with ~)
XADD events:stream MAXLEN ~ 1000 '*' event_type "heartbeat"  # faster, approximate

# XTRIM: trim existing stream
XTRIM events:stream MAXLEN 100

# XDEL: delete specific message by ID
# XDEL events:stream 1772726175603-0
```

---

## Step 6 — Consumer Groups: Reliable Processing

Consumer groups allow multiple workers to process messages, track delivery, and handle failures.

```bash
# Create consumer group
# 0 = start from beginning; $ = start from now (new messages only)
XGROUP CREATE events:stream analytics-group 0 MKSTREAM

# XREADGROUP: read as a consumer in a group
# '>' = read new, undelivered messages
XREADGROUP GROUP analytics-group consumer-1 COUNT 2 STREAMS events:stream ">"
```

📸 **Verified Output:**
```
1) 1) "events:stream"
   2) 1) 1) "1772726175603-0"
         2) 1) "event_type" 2) "page_view" ...
      2) 1) "1772726175829-0"
         2) 1) "event_type" 2) "add_to_cart" ...
```

```bash
# Messages are "pending" until acknowledged
XPENDING events:stream analytics-group - + 10

# XACK: acknowledge processing complete
XACK events:stream analytics-group 1772726175603-0

# Another consumer claims remaining messages
XREADGROUP GROUP analytics-group consumer-2 COUNT 10 STREAMS events:stream ">"
XACK events:stream analytics-group 1772726175829-0 1772726176059-0

# View group info
XINFO GROUPS events:stream
```

📸 **Verified XINFO GROUPS:**
```
name          analytics-group
consumers     1
pending       1
last-delivered-id  1772726175829-0
entries-read  2
lag           1
```

---

## Step 7 — Multiple Consumer Groups and XCLAIM

```bash
# Multiple groups for different processing pipelines
XGROUP CREATE events:stream email-group    0
XGROUP CREATE events:stream metrics-group  0

# Each group independently processes the stream
XREADGROUP GROUP email-group   worker-A COUNT 5 STREAMS events:stream ">"
XREADGROUP GROUP metrics-group worker-B COUNT 5 STREAMS events:stream ">"

# If a consumer crashes, reclaim its pending messages
# View pending messages idle > 30000ms
XPENDING events:stream analytics-group - + 10

# XCLAIM: steal a pending message after timeout
# XCLAIM events:stream analytics-group consumer-2 30000 <message-id>

# XAUTOCLAIM: auto-claim idle messages (Redis 6.2+)
# XAUTOCLAIM events:stream analytics-group consumer-2 30000 0-0

# XINFO CONSUMERS: see consumer activity
XINFO CONSUMERS events:stream analytics-group
```

> 💡 The pending entry list (PEL) tracks messages delivered but not acknowledged. If a consumer crashes, its pending messages can be claimed by another consumer using `XCLAIM`.

---

## Step 8 — Capstone: Event Processing Pipeline

```bash
# Complete event streaming architecture

# 1. Multiple producers add events
XADD user:events '*' type "login"    user "alice" ts "1704067200000"
XADD user:events '*' type "purchase" user "alice" product "laptop" amount "1299.99"
XADD user:events '*' type "login"    user "bob"   ts "1704067260000"
XADD user:events '*' type "logout"   user "alice" ts "1704067380000"
XADD user:events '*' type "purchase" user "bob"   product "mouse"  amount "29.99"

# 2. Create specialized consumer groups
XGROUP CREATE user:events analytics  0 MKSTREAM
XGROUP CREATE user:events fraud      0 MKSTREAM
XGROUP CREATE user:events billing    0 MKSTREAM

# 3. Analytics worker processes all events
XREADGROUP GROUP analytics analytics-worker-1 COUNT 10 STREAMS user:events ">"

# 4. Fraud detection only cares about purchases
# (Filter in application code after reading from group)

# 5. View stream info
XINFO STREAM user:events

# 6. Monitor lag per group
XINFO GROUPS user:events

# 7. Set up rolling trim for storage management
XADD user:events MAXLEN ~ 10000 '*' type "heartbeat" user "system"

# 8. Consumer group reset (for replay)
XGROUP SETID user:events analytics 0   # replay from beginning

XLEN user:events
```

📸 **Verified XLEN:**
```
6
```

---

## Summary

| Feature | Pub/Sub | Streams |
|---------|---------|---------|
| Persistence | No | Yes (AOF/RDB) |
| Delivery guarantee | At-most-once | At-least-once (with groups) |
| Message history | None | Retained until XTRIM |
| Consumer groups | No | Yes (XGROUP) |
| Acknowledgment | N/A | XACK |
| Multiple consumers | Fan-out (all get all) | Partitioned (each message once per group) |
| Pattern matching | PSUBSCRIBE | Stream filter in app |
| Blocking read | SUBSCRIBE | XREAD BLOCK / BLPOP |
| Use case | Real-time notifications | Event sourcing, reliable queues |
