# Lab 07: Kafka with kafka-go

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Use `segmentio/kafka-go` to build producers and consumers: topic management, consumer groups, partition routing via message keys, context-based cancellation, and exactly-once semantics concepts.

---

## Step 1: kafka-go Concepts

```
Kafka Architecture:
  Producer ──► Topic ──► Partition[0] ──► Consumer Group A
                     └── Partition[1] ──► Consumer Group A
                     └── Partition[2] ──► Consumer Group A
                                      └── Consumer Group B (independent)

Message key → consistent partition routing (same key → same partition)
Consumer group → each partition assigned to exactly one consumer in the group
```

---

## Step 2: Writer (Producer)

```go
// producer.go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/segmentio/kafka-go"
)

func newWriter(brokers []string, topic string) *kafka.Writer {
	return &kafka.Writer{
		Addr:  kafka.TCP(brokers...),
		Topic: topic,

		// Balancer: routes messages to partitions
		// kafka.LeastBytes    → minimize partition size
		// kafka.RoundRobin    → even distribution
		// kafka.Hash          → key-based (consistent routing!)
		Balancer: &kafka.Hash{},

		// Batching
		BatchSize:    100,
		BatchTimeout: 10 * time.Millisecond,

		// Required acks before considering a write successful
		RequiredAcks: kafka.RequireAll, // -1: all in-sync replicas

		// Async writes (fire-and-forget), lower latency but no error feedback
		Async: false,

		// Compression
		Compression: kafka.Snappy,
	}
}

func produce(w *kafka.Writer, userID string, eventType string, payload []byte) error {
	msg := kafka.Message{
		Key:   []byte(userID),   // same userID → same partition → ordered
		Value: payload,
		Headers: []kafka.Header{
			{Key: "event-type", Value: []byte(eventType)},
			{Key: "timestamp", Value: []byte(time.Now().UTC().Format(time.RFC3339))},
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return w.WriteMessages(ctx, msg)
}

func produceBatch(w *kafka.Writer, msgs []kafka.Message) error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return w.WriteMessages(ctx, msgs...)
}
```

---

## Step 3: Reader (Consumer)

```go
// consumer.go
package main

import (
	"context"
	"fmt"
	"log"

	"github.com/segmentio/kafka-go"
)

func newReader(brokers []string, topic, groupID string) *kafka.Reader {
	return kafka.NewReader(kafka.ReaderConfig{
		Brokers: brokers,
		Topic:   topic,
		GroupID: groupID, // consumer group name

		// Offset management
		// kafka.FirstOffset  → start from beginning
		// kafka.LastOffset   → start from newest
		StartOffset: kafka.FirstOffset,

		// MinBytes/MaxBytes control fetch behavior
		MinBytes: 1,        // don't wait if there's data
		MaxBytes: 10 << 20, // 10MB max

		// CommitInterval: auto-commit every N ms
		// CommitInterval: time.Second,
	})
}

func consume(ctx context.Context, r *kafka.Reader) error {
	defer r.Close()

	for {
		msg, err := r.FetchMessage(ctx) // fetch but don't commit
		if err != nil {
			if ctx.Err() != nil {
				return nil // graceful shutdown
			}
			return fmt.Errorf("fetch: %w", err)
		}

		// Process message
		log.Printf("msg: partition=%d offset=%d key=%s value=%s",
			msg.Partition, msg.Offset, msg.Key, msg.Value)

		// Extract headers
		for _, h := range msg.Headers {
			log.Printf("  header: %s=%s", h.Key, h.Value)
		}

		// Commit AFTER successful processing (at-least-once semantics)
		if err := r.CommitMessages(ctx, msg); err != nil {
			return fmt.Errorf("commit: %w", err)
		}
	}
}
```

---

## Step 4: Consumer Group Rebalancing

```go
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/segmentio/kafka-go"
)

func runConsumerGroup(brokers []string, topic, groupID string, numWorkers int) {
	var wg sync.WaitGroup
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			r := kafka.NewReader(kafka.ReaderConfig{
				Brokers: brokers,
				Topic:   topic,
				GroupID: groupID,
			})
			defer r.Close()

			fmt.Printf("Worker %d started\n", workerID)
			for {
				msg, err := r.ReadMessage(ctx) // ReadMessage auto-commits
				if err != nil {
					if ctx.Err() != nil {
						fmt.Printf("Worker %d shutting down\n", workerID)
						return
					}
					fmt.Printf("Worker %d error: %v\n", workerID, err)
					return
				}
				fmt.Printf("Worker %d: partition=%d offset=%d key=%s\n",
					workerID, msg.Partition, msg.Offset, msg.Key)
			}
		}(i)
	}
	wg.Wait()
}
```

> 💡 **Rebalancing:** When a consumer joins or leaves a group, Kafka rebalances partition assignments. During rebalance, consumption pauses briefly. Use `FetchMessage` + `CommitMessages` for manual control.

---

## Step 5: Exactly-Once Semantics (Concept)

```go
package main

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/segmentio/kafka-go"
)

// EOS requires:
// 1. Producer: idempotent writes (enable.idempotence=true) + transactions
// 2. Consumer: read-committed isolation + manual offset commit in same transaction

func processExactlyOnce(ctx context.Context, r *kafka.Reader, db *sql.DB) error {
	msg, err := r.FetchMessage(ctx)
	if err != nil {
		return err
	}

	// Begin DB transaction
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Process message AND store offset atomically
	_, err = tx.ExecContext(ctx,
		"INSERT INTO events (key, value, partition, offset) VALUES (?, ?, ?, ?)",
		string(msg.Key), string(msg.Value), msg.Partition, msg.Offset)
	if err != nil {
		return err
	}

	// Commit DB first, then Kafka offset
	if err := tx.Commit(); err != nil {
		return err
	}

	// Commit Kafka offset (if DB commit failed, we'll reprocess — that's ok, dedup by offset)
	return r.CommitMessages(ctx, msg)
}

func main() {
	fmt.Println("EOS concept demonstrated — requires real Kafka for verification")
	fmt.Println("Strategies:")
	fmt.Println("  1. At-most-once:  commit before processing (may lose messages)")
	fmt.Println("  2. At-least-once: commit after processing (may duplicate messages)")
	fmt.Println("  3. Exactly-once:  idempotent consumer + transactional producer")
}
```

---

## Step 6: Topic Management

```go
package main

import (
	"context"
	"fmt"
	"net"

	"github.com/segmentio/kafka-go"
)

func createTopic(brokerAddr, topic string, partitions, replicationFactor int) error {
	conn, err := kafka.Dial("tcp", brokerAddr)
	if err != nil {
		return err
	}
	defer conn.Close()

	controller, err := conn.Controller()
	if err != nil {
		return err
	}

	controllerConn, err := kafka.Dial("tcp",
		net.JoinHostPort(controller.Host, fmt.Sprintf("%d", controller.Port)))
	if err != nil {
		return err
	}
	defer controllerConn.Close()

	return controllerConn.CreateTopics(kafka.TopicConfig{
		Topic:             topic,
		NumPartitions:     partitions,
		ReplicationFactor: replicationFactor,
	})
}

func listTopics(brokerAddr string) ([]string, error) {
	conn, err := kafka.Dial("tcp", brokerAddr)
	if err != nil {
		return nil, err
	}
	defer conn.Close()

	partitions, err := conn.ReadPartitions()
	if err != nil {
		return nil, err
	}

	topics := make(map[string]bool)
	for _, p := range partitions {
		topics[p.Topic] = true
	}

	result := make([]string, 0, len(topics))
	for t := range topics {
		result = append(result, t)
	}
	return result, nil
}
```

---

## Step 7: API Demo (Without Live Kafka)

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/kafkademo
cd /tmp/kafkademo
cat > go.mod << 'EOF'
module kafkademo
go 1.22
EOF
go get github.com/segmentio/kafka-go@v0.4.47 2>/dev/null

cat > main.go << 'GOEOF'
package main

import (
	\"context\"
	\"fmt\"
	\"time\"
	\"github.com/segmentio/kafka-go\"
)

func main() {
	// Demonstrate kafka-go API shapes without a running broker
	w := &kafka.Writer{
		Addr:     kafka.TCP(\"localhost:9092\"),
		Topic:    \"user-events\",
		Balancer: &kafka.Hash{},
		BatchSize: 100,
		BatchTimeout: 10 * time.Millisecond,
	}
	_ = w

	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers: []string{\"localhost:9092\"},
		Topic:   \"user-events\",
		GroupID: \"analytics-service\",
		StartOffset: kafka.FirstOffset,
	})
	_ = r

	msgs := []kafka.Message{
		{Key: []byte(\"user:1\"), Value: []byte(\"{\\\"action\\\":\\\"login\\\"}\")},
		{Key: []byte(\"user:2\"), Value: []byte(\"{\\\"action\\\":\\\"purchase\\\"}\")},
		{Key: []byte(\"user:1\"), Value: []byte(\"{\\\"action\\\":\\\"logout\\\"}\")},
	}

	fmt.Printf(\"Producer ready: topic=%s balancer=Hash\\n\", \"user-events\")
	fmt.Printf(\"Consumer ready: groupID=%s offset=FirstOffset\\n\", \"analytics-service\")
	fmt.Printf(\"Messages prepared: %d\\n\", len(msgs))
	fmt.Println(\"Key routing: user:1 → always same partition (ordered)\")

	// Message headers
	msg := kafka.Message{
		Key:   []byte(\"user:1\"),
		Value: []byte(\"{\\\"event\\\":\\\"order_placed\\\"}\"),
		Headers: []kafka.Header{
			{Key: \"content-type\", Value: []byte(\"application/json\")},
			{Key: \"trace-id\", Value: []byte(\"abc123\")},
		},
	}
	fmt.Printf(\"\\nMessage: key=%s headers=%d\\n\", msg.Key, len(msg.Headers))
	for _, h := range msg.Headers {
		fmt.Printf(\"  %s: %s\\n\", h.Key, h.Value)
	}

	// Context cancellation pattern
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = ctx
	fmt.Println(\"\\nContext-based cancellation: consumer respects ctx.Done()\")
	fmt.Println(\"Semantics: commit after process = at-least-once delivery\")
}
GOEOF
go run main.go 2>&1"
```

📸 **Verified Output:**
```
Producer ready: topic=user-events balancer=Hash
Consumer ready: groupID=analytics-service offset=FirstOffset
Messages prepared: 3
Key routing: user:1 → always same partition (ordered)

Message: key=user:1 headers=2
  content-type: application/json
  trace-id: abc123

Context-based cancellation: consumer respects ctx.Done()
Semantics: commit after process = at-least-once delivery
```

---

## Step 8: Capstone — Producer + Consumer Pattern

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

// Event types
type OrderEvent struct {
	OrderID   string    `json:"order_id"`
	UserID    string    `json:"user_id"`
	Amount    float64   `json:"amount"`
	Timestamp time.Time `json:"timestamp"`
}

// Producer helper: serialize and send
func sendOrderEvent(/* w *kafka.Writer, */ event OrderEvent) error {
	data, err := json.Marshal(event)
	if err != nil {
		return err
	}
	fmt.Printf("Would send: key=%s value=%s\n", event.UserID, data)
	return nil
}

// Consumer helper: deserialize and process
func processOrderEvent(key, value []byte) error {
	var event OrderEvent
	if err := json.Unmarshal(value, &event); err != nil {
		return err
	}
	fmt.Printf("Processing order: %s for user %s ($%.2f)\n",
		event.OrderID, event.UserID, event.Amount)
	return nil
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = ctx

	events := []OrderEvent{
		{OrderID: "ord-1", UserID: "user:42", Amount: 99.99, Timestamp: time.Now()},
		{OrderID: "ord-2", UserID: "user:7", Amount: 24.99, Timestamp: time.Now()},
		{OrderID: "ord-3", UserID: "user:42", Amount: 149.99, Timestamp: time.Now()},
	}

	fmt.Println("=== Producing events ===")
	for _, e := range events {
		sendOrderEvent(e)
	}

	fmt.Println("\n=== Consuming events ===")
	for _, e := range events {
		data, _ := json.Marshal(e)
		processOrderEvent([]byte(e.UserID), data)
	}

	fmt.Println("\nNote: user:42 events always go to same partition (ordered delivery)")
}
```

---

## Summary

| Concept | API | Notes |
|---------|-----|-------|
| Producer | `kafka.Writer{Balancer: &kafka.Hash{}}` | Key → partition routing |
| Consumer | `kafka.NewReader(kafka.ReaderConfig{GroupID: ...})` | Group auto-rebalance |
| Manual commit | `r.FetchMessage` + `r.CommitMessages` | At-least-once |
| Auto commit | `r.ReadMessage` | Simpler, same semantics |
| Batch send | `w.WriteMessages(ctx, msgs...)` | Higher throughput |
| Cancellation | `context.WithCancel(ctx)` | Graceful shutdown |

**Key Takeaways:**
- Same message key → same partition → ordered delivery for that key
- Consumer groups provide horizontal scaling with each partition owned by one consumer
- `FetchMessage` + `CommitMessages` gives you control over at-least-once delivery
- Exactly-once requires idempotent consumer (dedup) or transactional API
- Always handle `ctx.Err()` in consumer loop for graceful shutdown
