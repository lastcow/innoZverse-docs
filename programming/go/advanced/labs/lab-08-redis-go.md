# Lab 08: Redis with go-redis/v9

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master go-redis/v9: String/Hash/Sorted Set operations, Pipeline/TxPipeline, Pub/Sub, and Redis Streams. Run with a live Redis container.

---

## Step 1: Client Setup

```go
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

func newRedisClient() *redis.Client {
	return redis.NewClient(&redis.Options{
		Addr:         "localhost:6379",
		Password:     "",   // no auth
		DB:           0,    // default DB
		DialTimeout:  2 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		PoolSize:     10,
	})
}

// Cluster client (for production Redis Cluster)
func newClusterClient() *redis.ClusterClient {
	return redis.NewClusterClient(&redis.ClusterOptions{
		Addrs: []string{
			"redis-node1:7000",
			"redis-node2:7001",
			"redis-node3:7002",
		},
	})
}

func main() {
	ctx := context.Background()
	rdb := newRedisClient()
	defer rdb.Close()

	// Ping
	pong, err := rdb.Ping(ctx).Result()
	if err != nil {
		fmt.Println("Redis not available:", err)
		return
	}
	fmt.Println("PING:", pong)
}
```

Start Redis:
```bash
docker run -d --name redis-go-lab -p 6379:6379 redis:7-alpine
sleep 1
```

---

## Step 2: String Operations

```go
func stringOps(ctx context.Context, rdb *redis.Client) {
	// SET with TTL
	rdb.Set(ctx, "session:abc123", "user:42", 30*time.Minute)

	// GET
	val, err := rdb.Get(ctx, "session:abc123").Result()
	if err == redis.Nil {
		fmt.Println("Key not found")
	} else if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("session:", val)
	}

	// INCR / INCRBY (atomic counter)
	rdb.Set(ctx, "page:views", 0, 0)
	rdb.Incr(ctx, "page:views")
	rdb.IncrBy(ctx, "page:views", 5)
	count, _ := rdb.Get(ctx, "page:views").Int64()
	fmt.Println("page views:", count) // 6

	// SETNX (set if not exists) — distributed lock basis
	set, _ := rdb.SetNX(ctx, "lock:resource", "worker-1", 10*time.Second).Result()
	fmt.Println("lock acquired:", set)

	// GETDEL (get and delete atomically, Redis 6.2+)
	rdb.Set(ctx, "temp:key", "temp_value", time.Minute)
	rdb.Del(ctx, "temp:key")

	// Cleanup
	rdb.Del(ctx, "session:abc123", "page:views", "lock:resource")
}
```

---

## Step 3: Hash Operations

```go
func hashOps(ctx context.Context, rdb *redis.Client) {
	// HSET multiple fields
	rdb.HSet(ctx, "user:1",
		"name", "Alice",
		"email", "alice@example.com",
		"age", "30",
		"role", "admin",
	)

	// HGET single field
	name, _ := rdb.HGet(ctx, "user:1", "name").Result()
	fmt.Println("name:", name)

	// HGETALL
	user, _ := rdb.HGetAll(ctx, "user:1").Result()
	fmt.Printf("user:1 = %v\n", user)

	// HINCRBY (atomic increment on hash field)
	rdb.HSet(ctx, "stats:api", "requests", 0, "errors", 0)
	rdb.HIncrBy(ctx, "stats:api", "requests", 100)
	rdb.HIncrBy(ctx, "stats:api", "errors", 3)
	stats, _ := rdb.HGetAll(ctx, "stats:api").Result()
	fmt.Printf("api stats: %v\n", stats)

	// Cleanup
	rdb.Del(ctx, "user:1", "stats:api")
}
```

---

## Step 4: Sorted Set — Leaderboard

```go
func sortedSetOps(ctx context.Context, rdb *redis.Client) {
	key := "leaderboard:weekly"

	// ZADD scores
	rdb.ZAdd(ctx, key,
		redis.Z{Score: 9850, Member: "alice"},
		redis.Z{Score: 12300, Member: "bob"},
		redis.Z{Score: 7500, Member: "carol"},
		redis.Z{Score: 15000, Member: "dave"},
		redis.Z{Score: 11200, Member: "eve"},
	)

	// ZREVRANGE with scores (top N players)
	top3, _ := rdb.ZRevRangeWithScores(ctx, key, 0, 2).Result()
	fmt.Println("Top 3:")
	for i, z := range top3 {
		fmt.Printf("  #%d %s: %.0f\n", i+1, z.Member, z.Score)
	}

	// ZRANK (0-indexed rank)
	rank, _ := rdb.ZRevRank(ctx, key, "alice").Result()
	fmt.Printf("alice rank: #%d\n", rank+1)

	// ZRANGEBYSCORE
	mid, _ := rdb.ZRangeByScoreWithScores(ctx, key, &redis.ZRangeBy{
		Min: "10000", Max: "+inf",
	}).Result()
	fmt.Printf("Players with 10k+: %d\n", len(mid))

	rdb.Del(ctx, key)
}
```

---

## Step 5: Pipeline & TxPipeline

```go
func pipelineOps(ctx context.Context, rdb *redis.Client) {
	// Pipeline: batch commands, reduce RTTs
	pipe := rdb.Pipeline()
	setCmd := pipe.Set(ctx, "pk1", "v1", 0)
	setCmd2 := pipe.Set(ctx, "pk2", "v2", 0)
	getCmd := pipe.Get(ctx, "pk1")
	incrCmd := pipe.Incr(ctx, "pipeline:counter")

	cmds, err := pipe.Exec(ctx)
	fmt.Printf("Pipeline: %d commands, err=%v\n", len(cmds), err)
	fmt.Println("  GET pk1:", getCmd.Val())
	fmt.Println("  INCR counter:", incrCmd.Val())
	_ = setCmd; _ = setCmd2

	// TxPipeline: MULTI/EXEC (atomic)
	txPipe := rdb.TxPipeline()
	txPipe.Set(ctx, "tx:balance", 100, 0)
	txPipe.DecrBy(ctx, "tx:balance", 30)
	getBalance := txPipe.Get(ctx, "tx:balance")
	_, err = txPipe.Exec(ctx)
	fmt.Printf("TxPipeline balance: %s (err=%v)\n", getBalance.Val(), err)

	rdb.Del(ctx, "pk1", "pk2", "pipeline:counter", "tx:balance")
}
```

> 💡 **Pipeline vs TxPipeline:** Pipeline sends all commands in one batch (not atomic). TxPipeline wraps in `MULTI/EXEC` (atomic). For optimistic locking, use `WATCH` + `TxPipelined`.

---

## Step 6: Pub/Sub

```go
func pubsubDemo(ctx context.Context, rdb *redis.Client) {
	// Subscribe
	sub := rdb.Subscribe(ctx, "notifications", "alerts")
	defer sub.Close()

	// Publish from another goroutine
	go func() {
		time.Sleep(50 * time.Millisecond)
		rdb.Publish(ctx, "notifications", `{"type":"order","id":"123"}`)
		rdb.Publish(ctx, "alerts", `{"severity":"low","msg":"high CPU"}`)
		rdb.Publish(ctx, "notifications", `{"type":"payment","id":"456"}`)
	}()

	// Receive messages
	received := 0
	timeoutCtx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()

	ch := sub.Channel()
	for received < 3 {
		select {
		case msg := <-ch:
			fmt.Printf("Channel: %s | Message: %s\n", msg.Channel, msg.Payload)
			received++
		case <-timeoutCtx.Done():
			return
		}
	}
}
```

---

## Step 7: Redis Streams

```go
func streamsDemo(ctx context.Context, rdb *redis.Client) {
	stream := "order:events"

	// XADD — append to stream
	for i := 1; i <= 3; i++ {
		id, _ := rdb.XAdd(ctx, &redis.XAddArgs{
			Stream: stream,
			Values: map[string]interface{}{
				"order_id": fmt.Sprintf("ord-%d", i),
				"amount":   fmt.Sprintf("%.2f", float64(i)*49.99),
				"user_id":  "user:42",
			},
		}).Result()
		fmt.Printf("XADD id: %s\n", id)
	}

	// XLEN
	length, _ := rdb.XLen(ctx, stream).Result()
	fmt.Printf("Stream length: %d\n", length)

	// XREAD — read from beginning
	msgs, _ := rdb.XRead(ctx, &redis.XReadArgs{
		Streams: []string{stream, "0"}, // "0" = from beginning
		Count:   10,
	}).Result()

	for _, streamMsgs := range msgs {
		for _, msg := range streamMsgs.Messages {
			fmt.Printf("  ID=%s order_id=%s amount=%s\n",
				msg.ID, msg.Values["order_id"], msg.Values["amount"])
		}
	}

	// Consumer group (for distributed processing)
	rdb.XGroupCreateMkStream(ctx, stream, "processors", "0")
	rdb.Del(ctx, stream)
}
```

---

## Step 8: Capstone — Full Demo with Live Redis

```bash
# Start Redis
docker run -d --name redis-go-lab -p 6379:6379 redis:7-alpine
sleep 1

# Run demo
docker run --rm --network=host golang:1.22-alpine sh -c "
mkdir -p /tmp/redislab
cd /tmp/redislab
cat > go.mod << 'EOF'
module redislab
go 1.22
EOF
go get github.com/redis/go-redis/v9 2>/dev/null

cat > main.go << 'GOEOF'
package main

import (
	\"context\"
	\"fmt\"
	\"time\"
	\"github.com/redis/go-redis/v9\"
)

func main() {
	ctx := context.Background()
	rdb := redis.NewClient(&redis.Options{Addr: \"localhost:6379\"})
	defer rdb.Close()
	pong, _ := rdb.Ping(ctx).Result()
	fmt.Println(\"PING:\", pong)
	rdb.Set(ctx, \"greeting\", \"Hello Redis!\", 10*time.Second)
	val, _ := rdb.Get(ctx, \"greeting\").Result()
	fmt.Println(\"GET greeting:\", val)
	rdb.HSet(ctx, \"user:1\", \"name\", \"Alice\", \"age\", \"30\")
	user, _ := rdb.HGetAll(ctx, \"user:1\").Result()
	fmt.Printf(\"HGETALL user:1: name=%s age=%s\n\", user[\"name\"], user[\"age\"])
	rdb.ZAdd(ctx, \"leaderboard\",
		redis.Z{Score: 100, Member: \"Alice\"},
		redis.Z{Score: 200, Member: \"Bob\"},
		redis.Z{Score: 150, Member: \"Carol\"})
	top, _ := rdb.ZRevRangeWithScores(ctx, \"leaderboard\", 0, 2).Result()
	fmt.Println(\"Leaderboard:\")
	for _, z := range top { fmt.Printf(\"  %s: %.0f\n\", z.Member, z.Score) }
	pipe := rdb.Pipeline()
	pipe.Set(ctx, \"k1\", \"v1\", 0); pipe.Set(ctx, \"k2\", \"v2\", 0)
	cmds, _ := pipe.Exec(ctx)
	fmt.Printf(\"Pipeline: %d commands\n\", len(cmds))
	rdb.XAdd(ctx, &redis.XAddArgs{Stream: \"events\", Values: map[string]interface{}{\"type\": \"login\", \"user\": \"alice\"}})
	msgs, _ := rdb.XRead(ctx, &redis.XReadArgs{Streams: []string{\"events\", \"0\"}, Count: 10}).Result()
	fmt.Printf(\"Stream events: %d message\n\", len(msgs[0].Messages))
	rdb.Del(ctx, \"greeting\", \"user:1\", \"leaderboard\", \"k1\", \"k2\", \"events\")
	fmt.Println(\"Done\")
}
GOEOF
go run main.go"
```

📸 **Verified Output:**
```
PING: PONG
GET greeting: Hello Redis!
HGETALL user:1: name=Alice age=30
Leaderboard:
  Bob: 200
  Carol: 150
  Alice: 100
Pipeline: 2 commands
Stream events: 1 message
Done
```

---

## Summary

| Data Structure | Key Commands | Use Case |
|---------------|-------------|----------|
| String | `Set/Get/Incr/SetNX` | Sessions, counters, locks |
| Hash | `HSet/HGetAll/HIncrBy` | User profiles, config |
| Sorted Set | `ZAdd/ZRevRange/ZRank` | Leaderboards, priority queues |
| Pipeline | `rdb.Pipeline()` | Batch commands, reduce RTT |
| TxPipeline | `rdb.TxPipeline()` | Atomic MULTI/EXEC |
| Pub/Sub | `Subscribe/Publish` | Real-time notifications |
| Streams | `XAdd/XRead/XGroup` | Event sourcing, message queues |

**Key Takeaways:**
- `SetNX` + `Del` = basic distributed lock (use Redlock for production)
- Pipeline reduces latency by batching; TxPipeline adds atomicity
- Sorted sets are O(log N) for add/remove, O(log N + M) for range queries
- Redis Streams persist messages — Pub/Sub does not (fire-and-forget)
- Use `PoolSize` and timeouts to handle connection pool exhaustion
