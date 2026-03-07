# Lab 06: Event Sourcing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Event sourcing in Go: Event interface, EventStore with optimistic concurrency, Aggregate Apply/Record pattern, read model Projections, snapshot pattern, and in-memory implementation (production: SQLite/PostgreSQL backend).

---

## Step 1: Core Event Types

```go
package eventsourcing

import (
	"encoding/json"
	"time"
)

// Event: immutable fact that something happened
type Event struct {
	AggregateID string
	Type        string
	Version     int
	Data        json.RawMessage
	OccurredAt  time.Time
	Metadata    map[string]string // correlation_id, causation_id, user_id
}

// Aggregate: entity rebuilt from its event stream
type Aggregate interface {
	AggregateID() string
	Version() int
	Apply(event Event)
	UncommittedEvents() []Event
	MarkEventsAsCommitted()
}

// EventStore: append-only log of domain events
type EventStore interface {
	Append(aggregateID string, expectedVersion int, events []Event) error
	Load(aggregateID string) ([]Event, error)
	LoadFrom(aggregateID string, fromVersion int) ([]Event, error)
}
```

---

## Step 2: In-Memory EventStore with Optimistic Concurrency

```go
package eventsourcing

import (
	"fmt"
	"sync"
)

type InMemoryEventStore struct {
	mu     sync.RWMutex
	events map[string][]Event
}

func NewInMemoryEventStore() *InMemoryEventStore {
	return &InMemoryEventStore{events: make(map[string][]Event)}
}

func (s *InMemoryEventStore) Append(id string, expectedVersion int, events []Event) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	existing := s.events[id]
	if len(existing) != expectedVersion {
		return fmt.Errorf("optimistic concurrency: expected v%d, current v%d",
			expectedVersion, len(existing))
	}

	for i, e := range events {
		e.AggregateID = id
		e.Version = expectedVersion + i + 1
		s.events[id] = append(s.events[id], e)
	}
	return nil
}

func (s *InMemoryEventStore) Load(id string) ([]Event, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	events := make([]Event, len(s.events[id]))
	copy(events, s.events[id])
	return events, nil
}

func (s *InMemoryEventStore) LoadFrom(id string, fromVersion int) ([]Event, error) {
	all, err := s.Load(id)
	if err != nil {
		return nil, err
	}
	result := make([]Event, 0)
	for _, e := range all {
		if e.Version >= fromVersion {
			result = append(result, e)
		}
	}
	return result, nil
}
```

---

## Step 3: Order Aggregate

```go
package domain

import (
	"encoding/json"
	"fmt"
	"time"
)

type Money struct {
	Amount   float64
	Currency string
}

type OrderItem struct {
	ProductID string
	Name      string
	Quantity  int
	Price     Money
}

type OrderStatus string

const (
	StatusPending   OrderStatus = "pending"
	StatusConfirmed OrderStatus = "confirmed"
	StatusShipped   OrderStatus = "shipped"
	StatusCancelled OrderStatus = "cancelled"
)

// Domain events (value objects)
type OrderCreated    struct { CustomerID string; CreatedAt time.Time }
type ItemAdded       struct { Item OrderItem }
type OrderConfirmed  struct { ConfirmedAt time.Time }
type OrderShipped    struct { TrackingID string; ShippedAt time.Time }
type OrderCancelled  struct { Reason string; CancelledAt time.Time }

// Order aggregate — rebuilt from events
type Order struct {
	id         string
	version    int
	customerID string
	status     OrderStatus
	items      []OrderItem
	total      Money

	uncommitted []Event
}

func (o *Order) Apply(event Event) {
	switch event.Type {
	case "OrderCreated":
		var data OrderCreated
		json.Unmarshal(event.Data, &data)
		o.id = event.AggregateID
		o.customerID = data.CustomerID
		o.status = StatusPending

	case "ItemAdded":
		var data ItemAdded
		json.Unmarshal(event.Data, &data)
		o.items = append(o.items, data.Item)
		o.total.Amount += data.Item.Price.Amount * float64(data.Item.Quantity)
		o.total.Currency = data.Item.Price.Currency

	case "OrderConfirmed":
		o.status = StatusConfirmed

	case "OrderShipped":
		o.status = StatusShipped

	case "OrderCancelled":
		o.status = StatusCancelled
	}
	o.version = event.Version
}

// Command handler: validate + record events
func (o *Order) AddItem(item OrderItem) error {
	if o.status != StatusPending {
		return fmt.Errorf("cannot add items to order in status: %s", o.status)
	}

	data, _ := json.Marshal(ItemAdded{Item: item})
	event := Event{Type: "ItemAdded", Data: data, OccurredAt: time.Now()}
	o.record(event)
	o.Apply(event) // Apply locally for immediate state
	return nil
}

func (o *Order) Confirm() error {
	if o.status != StatusPending {
		return fmt.Errorf("cannot confirm order in status: %s", o.status)
	}
	if len(o.items) == 0 {
		return fmt.Errorf("cannot confirm empty order")
	}

	data, _ := json.Marshal(OrderConfirmed{ConfirmedAt: time.Now()})
	event := Event{Type: "OrderConfirmed", Data: data, OccurredAt: time.Now()}
	o.record(event)
	o.Apply(event)
	return nil
}

func (o *Order) record(e Event) {
	o.uncommitted = append(o.uncommitted, e)
}

func (o *Order) UncommittedEvents() []Event    { return o.uncommitted }
func (o *Order) MarkEventsAsCommitted()         { o.uncommitted = nil }
func (o *Order) AggregateID() string            { return o.id }
func (o *Order) Version() int                   { return o.version }
func (o *Order) Status() OrderStatus            { return o.status }
func (o *Order) Total() Money                   { return o.total }
func (o *Order) Items() []OrderItem             { return o.items }
```

---

## Step 4: Projection — Read Model

```go
package projection

// Read model: denormalized view optimized for queries
type OrderSummary struct {
	ID         string
	CustomerID string
	Status     string
	ItemCount  int
	Total      float64
	LastUpdated time.Time
}

type OrderProjection struct {
	mu      sync.RWMutex
	summaries map[string]*OrderSummary
}

func (p *OrderProjection) Handle(event Event) {
	p.mu.Lock()
	defer p.mu.Unlock()

	switch event.Type {
	case "OrderCreated":
		var data OrderCreated
		json.Unmarshal(event.Data, &data)
		p.summaries[event.AggregateID] = &OrderSummary{
			ID: event.AggregateID, CustomerID: data.CustomerID,
			Status: "pending", LastUpdated: event.OccurredAt,
		}
	case "ItemAdded":
		if s := p.summaries[event.AggregateID]; s != nil {
			var data ItemAdded
			json.Unmarshal(event.Data, &data)
			s.ItemCount++
			s.Total += data.Item.Price.Amount * float64(data.Item.Quantity)
			s.LastUpdated = event.OccurredAt
		}
	case "OrderConfirmed":
		if s := p.summaries[event.AggregateID]; s != nil {
			s.Status = "confirmed"; s.LastUpdated = event.OccurredAt
		}
	}
}

func (p *OrderProjection) GetSummary(id string) (*OrderSummary, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	s, ok := p.summaries[id]
	return s, ok
}
```

---

## Step 5: Snapshot Pattern

```go
package eventsourcing

// Snapshot: materialized state at a version, reduces replay cost
type Snapshot struct {
	AggregateID string
	Version     int
	State       json.RawMessage
	CreatedAt   time.Time
}

const SnapshotInterval = 50 // Take snapshot every 50 events

type SnapshotStore struct {
	mu        sync.Mutex
	snapshots map[string]*Snapshot
}

func (s *SnapshotStore) Save(id string, version int, state interface{}) error {
	data, err := json.Marshal(state)
	if err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.snapshots[id] = &Snapshot{
		AggregateID: id,
		Version:     version,
		State:       data,
		CreatedAt:   time.Now(),
	}
	return nil
}

// Loading with snapshot:
func LoadOrderWithSnapshot(id string, store EventStore, snapshotStore *SnapshotStore) (*Order, error) {
	order := &Order{}

	// 1. Try to load from snapshot first
	if snap, ok := snapshotStore.Load(id); ok {
		json.Unmarshal(snap.State, order)
		// 2. Replay only events AFTER snapshot
		events, err := store.LoadFrom(id, snap.Version+1)
		if err != nil {
			return nil, err
		}
		for _, e := range events {
			order.Apply(e)
		}
		return order, nil
	}

	// 3. No snapshot: replay all events
	events, err := store.Load(id)
	if err != nil {
		return nil, err
	}
	for _, e := range events {
		order.Apply(e)
	}
	return order, nil
}
```

---

## Step 6: Repository Pattern for Aggregates

```go
package repository

type OrderRepository struct {
	eventStore    EventStore
	snapshotStore *SnapshotStore
	projection    *OrderProjection
}

func (r *OrderRepository) Save(order *Order) error {
	events := order.UncommittedEvents()
	if len(events) == 0 {
		return nil
	}

	err := r.eventStore.Append(order.AggregateID(), order.Version()-len(events), events)
	if err != nil {
		return fmt.Errorf("save aggregate: %w", err)
	}

	order.MarkEventsAsCommitted()

	// Update projection
	for _, e := range events {
		r.projection.Handle(e)
	}

	// Save snapshot if needed
	if order.Version()%SnapshotInterval == 0 {
		r.snapshotStore.Save(order.AggregateID(), order.Version(), order)
	}

	return nil
}
```

---

## Step 7: Event Bus for Cross-Aggregate Communication

```go
// After saving events, publish to event bus for other aggregates/projections
type DomainEventBus struct {
	handlers map[string][]func(Event)
}

func (b *DomainEventBus) Subscribe(eventType string, handler func(Event)) {
	b.handlers[eventType] = append(b.handlers[eventType], handler)
}

func (b *DomainEventBus) Publish(events []Event) {
	for _, e := range events {
		for _, h := range b.handlers[e.Type] {
			go h(e) // Async dispatch
		}
	}
}
```

---

## Step 8: Capstone — Event Sourcing Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main
import (\"fmt\"; \"time\")

type Event struct { AggregateID, Type string; Version int; Data map[string]interface{}; OccurredAt time.Time }

type EventStore struct { events map[string][]Event }
func NewEventStore() *EventStore { return &EventStore{events: make(map[string][]Event)} }
func (s *EventStore) Append(id string, expected int, events []Event) error {
  if len(s.events[id]) != expected { return fmt.Errorf(\"optimistic concurrency: expected v%d, got v%d\", expected, len(s.events[id])) }
  for i, e := range events { e.Version = expected+i+1; e.AggregateID = id; s.events[id] = append(s.events[id], e) }
  return nil
}
func (s *EventStore) Load(id string) []Event { return s.events[id] }

type OrderState struct { ID, Status string; Total float64; Items []string; Version int }
func (o *OrderState) Apply(e Event) {
  switch e.Type {
  case \"OrderCreated\": o.ID = e.AggregateID; o.Status = \"pending\"
  case \"ItemAdded\": o.Items = append(o.Items, e.Data[\"item\"].(string)); o.Total += e.Data[\"price\"].(float64)
  case \"OrderConfirmed\": o.Status = \"confirmed\"
  }; o.Version = e.Version
}
func Rebuild(id string, store *EventStore) OrderState {
  var s OrderState
  for _, e := range store.Load(id) { s.Apply(e) }
  return s
}

func main() {
  store := NewEventStore()
  id := \"order-001\"
  events := []Event{
    {Type:\"OrderCreated\",Data:map[string]interface{}{\"customerId\":\"c-1\"},OccurredAt:time.Now()},
    {Type:\"ItemAdded\",Data:map[string]interface{}{\"item\":\"MacBook Pro\",\"price\":1999.0},OccurredAt:time.Now()},
    {Type:\"ItemAdded\",Data:map[string]interface{}{\"item\":\"Magic Mouse\",\"price\":79.0},OccurredAt:time.Now()},
    {Type:\"ItemAdded\",Data:map[string]interface{}{\"item\":\"USB-C Hub\",\"price\":49.0},OccurredAt:time.Now()},
    {Type:\"OrderConfirmed\",Data:map[string]interface{}{},OccurredAt:time.Now()},
  }
  store.Append(id, 0, events)
  state := Rebuild(id, store)
  fmt.Println(\"=== Event Sourcing Demo ===\")
  fmt.Printf(\"Order ID:  %s\\nStatus:    %s\\nItems:     %v\\nTotal:     $%.2f\\nVersion:   %d\\nEvents:    %d stored\\n\",
    state.ID, state.Status, state.Items, state.Total, state.Version, len(store.Load(id)))
  err := store.Append(id, 0, []Event{{Type:\"Conflict\"}})
  fmt.Printf(\"\\nConflict write: %v\\n\", err)
  store.Append(id, 5, []Event{{Type:\"OrderShipped\",Data:map[string]interface{}{},OccurredAt:time.Now()}})
  fmt.Printf(\"Final version: %d\\n\", Rebuild(id, store).Version)
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== Event Sourcing Demo ===
Order ID:  order-001
Status:    confirmed
Items:     [MacBook Pro Magic Mouse USB-C Hub]
Total:     $2127.00
Version:   5
Events:    5 stored

Conflict write: optimistic concurrency: expected v0, got v5
Final version: 6
```

---

## Summary

| Component | Pattern | Guarantee |
|-----------|---------|-----------|
| Event | Immutable struct | Append-only audit log |
| EventStore | `Append(id, expectedVersion, events)` | Optimistic concurrency |
| Aggregate | `Apply(event)` pattern | Rebuild from any point |
| Projection | Event handler → read model | Eventual consistency |
| Snapshot | State @ version N | O(1) load after N events |
| Repository | Load+Save aggregate | Clean domain boundary |
| Event bus | Async cross-aggregate | Loose coupling |
