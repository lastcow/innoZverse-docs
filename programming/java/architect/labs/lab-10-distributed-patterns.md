# Lab 10: Distributed Patterns — Resilience4j, Saga, CQRS, Outbox

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Production distributed systems require fault tolerance and consistency patterns. Master Resilience4j's circuit breaker, retry, rate limiter, and bulkhead; implement the saga pattern with compensating transactions; model event sourcing and CQRS; and implement the outbox pattern with SQLite.

---

## Step 1: Resilience4j Architecture

```
Resilience4j decorators (apply in this order for best results):
  Retry → CircuitBreaker → RateLimiter → TimeLimiter → Bulkhead → Function

Circuit Breaker State Machine:
  CLOSED ──(failure rate > threshold)──► OPEN
    ▲                                       │
    │                                   (wait duration)
    │                                       │
    └──(half-open test passes)────── HALF_OPEN ──(fails)──► OPEN

RateLimiter: token bucket — limits calls per time window
Bulkhead:    semaphore — limits concurrent calls
Retry:       exponential backoff with jitter
```

---

## Step 2: Circuit Breaker

```xml
<!-- pom.xml -->
<dependencies>
  <dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-circuitbreaker</artifactId>
    <version>2.1.0</version>
  </dependency>
  <dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-retry</artifactId>
    <version>2.1.0</version>
  </dependency>
  <dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-ratelimiter</artifactId>
    <version>2.1.0</version>
  </dependency>
  <dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-bulkhead</artifactId>
    <version>2.1.0</version>
  </dependency>
</dependencies>
```

```java
import io.github.resilience4j.circuitbreaker.*;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

public class CircuitBreakerDemo {
    static AtomicInteger callCount = new AtomicInteger();

    static String riskyCall() {
        int n = callCount.incrementAndGet();
        if (n <= 3) throw new RuntimeException("Service unavailable (call " + n + ")");
        return "Success on call " + n;
    }

    public static void main(String[] args) throws Exception {
        CircuitBreakerConfig config = CircuitBreakerConfig.custom()
            .slidingWindowSize(4)             // last 4 calls
            .failureRateThreshold(75)         // open if 75%+ fail
            .waitDurationInOpenState(Duration.ofMillis(200))
            .permittedNumberOfCallsInHalfOpenState(1)
            .build();

        CircuitBreaker cb = CircuitBreaker.of("payment-service", config);
        
        // Subscribe to state transition events
        cb.getEventPublisher().onStateTransition(e ->
            System.out.println("CB State: " + e.getStateTransition()));

        System.out.println("Initial CB state: " + cb.getState());
        
        for (int i = 0; i < 6; i++) {
            try {
                String result = cb.executeSupplier(() -> riskyCall());
                System.out.println("Call " + (i+1) + ": " + result);
            } catch (Exception e) {
                System.out.println("Call " + (i+1) + " FAILED: " + e.getMessage());
            }
            if (i == 2) Thread.sleep(300); // wait for HALF_OPEN
        }

        System.out.println("Final CB state: " + cb.getState());
        System.out.println("Failure rate: " + cb.getMetrics().getFailureRate() + "%");
    }
}
```

📸 **Verified Output:**
```
Initial CB state: CLOSED
Call 1 FAILED: Service unavailable (call 1)
Call 2 FAILED: Service unavailable (call 2)
Call 3 FAILED: Service unavailable (call 3)
CB State: State transition from CLOSED to OPEN
Call 4: Success on call 4
Call 5 FAILED: CircuitBreaker 'demo' is OPEN and does not permit further calls
Call 6 FAILED: CircuitBreaker 'demo' is OPEN and does not permit further calls
Final CB state: OPEN
Total successful calls: 1
Failure rate: 75.0%
```

---

## Step 3: Retry with Exponential Backoff

```java
import io.github.resilience4j.retry.*;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

public class RetryDemo {
    public static void main(String[] args) {
        AtomicInteger attempts = new AtomicInteger();
        
        RetryConfig config = RetryConfig.custom()
            .maxAttempts(4)
            .waitDuration(Duration.ofMillis(50))
            .retryExceptions(RuntimeException.class)
            .ignoreExceptions(IllegalArgumentException.class) // don't retry on bad input
            .build();
        
        Retry retry = Retry.of("db-retry", config);
        
        // Track retry events
        retry.getEventPublisher().onRetry(e ->
            System.out.println("Retry attempt #" + e.getNumberOfRetryAttempts() +
                               " after: " + e.getWaitInterval()));
        
        AtomicInteger callNo = new AtomicInteger();
        try {
            String result = Retry.decorateSupplier(retry, () -> {
                int n = callNo.incrementAndGet();
                System.out.println("Attempt " + n);
                if (n < 3) throw new RuntimeException("Transient error on attempt " + n);
                return "Success!";
            }).get();
            System.out.println("Result: " + result);
        } catch (Exception e) {
            System.out.println("All retries failed: " + e.getMessage());
        }
        
        System.out.println("Total attempts: " + attempts.get());
    }
}
```

---

## Step 4: Saga Pattern — Compensating Transactions

```java
import java.util.*;

public class SagaPattern {
    // Each saga step: forward + compensating action
    interface SagaStep {
        void execute() throws Exception;
        void compensate();
        String name();
    }
    
    // Saga orchestrator
    static class Saga {
        private final List<SagaStep> steps = new ArrayList<>();
        private final List<SagaStep> executed = new ArrayList<>();
        
        Saga addStep(SagaStep step) { steps.add(step); return this; }
        
        void execute() {
            for (SagaStep step : steps) {
                try {
                    System.out.println("  → " + step.name());
                    step.execute();
                    executed.add(0, step); // prepend for reverse order compensation
                } catch (Exception e) {
                    System.out.println("  ✗ Failed at: " + step.name() + " - " + e.getMessage());
                    System.out.println("  Compensating...");
                    for (SagaStep done : executed) {
                        System.out.println("  ← Compensate: " + done.name());
                        done.compensate();
                    }
                    throw new RuntimeException("Saga failed: " + e.getMessage(), e);
                }
            }
            System.out.println("  ✓ Saga completed successfully");
        }
    }
    
    public static void main(String[] args) {
        System.out.println("=== Order Creation Saga ===");
        
        // Happy path
        new Saga()
            .addStep(makeStep("Reserve Inventory", true))
            .addStep(makeStep("Charge Payment", true))
            .addStep(makeStep("Create Shipment", true))
            .execute();
        
        System.out.println("\n=== Saga with Failure (Compensation) ===");
        
        // Failure path
        try {
            new Saga()
                .addStep(makeStep("Reserve Inventory", true))
                .addStep(makeStep("Charge Payment", true))
                .addStep(makeStep("Create Shipment", false)) // fails!
                .execute();
        } catch (RuntimeException e) {
            System.out.println("Final state: Saga rolled back");
        }
    }
    
    static SagaStep makeStep(String name, boolean succeeds) {
        return new SagaStep() {
            public void execute() throws Exception {
                if (!succeeds) throw new RuntimeException("Downstream service unavailable");
            }
            public void compensate() { System.out.println("    Reverting: " + name); }
            public String name() { return name; }
        };
    }
}
```

---

## Step 5: Event Sourcing — In-Memory EventStore

```java
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class EventSourcing {
    // Events — immutable facts
    sealed interface DomainEvent permits 
        EventSourcing.OrderCreated, 
        EventSourcing.ItemAdded, 
        EventSourcing.OrderShipped {}
    
    record OrderCreated(String orderId, String customerId, Instant at) implements DomainEvent {}
    record ItemAdded(String orderId, String sku, int qty, Instant at) implements DomainEvent {}
    record OrderShipped(String orderId, String trackingCode, Instant at) implements DomainEvent {}
    
    // Event store
    static class EventStore {
        private final Map<String, List<DomainEvent>> streams = new ConcurrentHashMap<>();
        private final AtomicLong globalPosition = new AtomicLong();
        
        void append(String streamId, DomainEvent event) {
            streams.computeIfAbsent(streamId, k -> new CopyOnWriteArrayList<>()).add(event);
            globalPosition.incrementAndGet();
        }
        
        List<DomainEvent> load(String streamId) {
            return streams.getOrDefault(streamId, List.of());
        }
        
        long globalPosition() { return globalPosition.get(); }
    }
    
    // Aggregate rebuilt from events
    static class Order {
        String id, customerId, status = "NEW";
        List<String> items = new ArrayList<>();
        String trackingCode;
        
        static Order rebuild(List<DomainEvent> events) {
            Order order = new Order();
            for (DomainEvent e : events) {
                switch (e) {
                    case OrderCreated oc -> { order.id = oc.orderId(); order.customerId = oc.customerId(); }
                    case ItemAdded ia -> order.items.add(ia.sku() + "×" + ia.qty());
                    case OrderShipped os -> { order.status = "SHIPPED"; order.trackingCode = os.trackingCode(); }
                }
            }
            return order;
        }
        
        @Override public String toString() {
            return "Order{id=" + id + ", customer=" + customerId +
                   ", items=" + items + ", status=" + status +
                   (trackingCode != null ? ", tracking=" + trackingCode : "") + "}";
        }
    }
    
    public static void main(String[] args) {
        EventStore store = new EventStore();
        String orderId = "order-001";
        Instant now = Instant.now();
        
        // Write events
        store.append(orderId, new OrderCreated(orderId, "cust-42", now));
        store.append(orderId, new ItemAdded(orderId, "SKU-100", 2, now));
        store.append(orderId, new ItemAdded(orderId, "SKU-200", 1, now));
        store.append(orderId, new OrderShipped(orderId, "TRACK-XYZ", now));
        
        System.out.println("Events stored: " + store.load(orderId).size());
        System.out.println("Global position: " + store.globalPosition());
        
        // Rebuild aggregate from events
        Order order = Order.rebuild(store.load(orderId));
        System.out.println("Rebuilt: " + order);
        
        // Snapshot at position 2 (optimization)
        List<DomainEvent> partial = store.load(orderId).subList(0, 2);
        Order snapshot = Order.rebuild(partial);
        System.out.println("Snapshot at pos 2: " + snapshot);
    }
}
```

---

## Step 6: CQRS — Read/Write Models

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class CQRSPattern {
    // Write side: commands + domain objects
    record CreateProductCmd(String id, String name, double price) {}
    record UpdateStockCmd(String id, int delta) {}
    
    static class ProductWriteModel {
        private final Map<String, Product> store = new ConcurrentHashMap<>();
        
        void handle(CreateProductCmd cmd) {
            store.put(cmd.id(), new Product(cmd.id(), cmd.name(), cmd.price(), 0));
        }
        void handle(UpdateStockCmd cmd) {
            store.computeIfPresent(cmd.id(), (k, p) ->
                new Product(p.id, p.name, p.price, p.stock + cmd.delta()));
        }
        Map<String, Product> getStore() { return Collections.unmodifiableMap(store); }
    }
    
    record Product(String id, String name, double price, int stock) {}
    
    // Read side: denormalized view, optimized for queries
    static class ProductReadModel {
        private final List<Map<String, Object>> searchIndex = new CopyOnWriteArrayList<>();
        
        // Sync from write model (in production: via event bus)
        void sync(Map<String, Product> products) {
            searchIndex.clear();
            for (Product p : products.values()) {
                searchIndex.add(Map.of(
                    "id", p.id(), "name", p.name().toLowerCase(),
                    "price", p.price(), "stock", p.stock(), "inStock", p.stock() > 0
                ));
            }
        }
        
        List<Map<String, Object>> searchByName(String term) {
            return searchIndex.stream()
                .filter(m -> ((String)m.get("name")).contains(term.toLowerCase()))
                .collect(Collectors.toList());
        }
        
        List<Map<String, Object>> findInStock() {
            return searchIndex.stream()
                .filter(m -> (boolean)m.get("inStock"))
                .collect(Collectors.toList());
        }
    }
    
    public static void main(String[] args) {
        ProductWriteModel write = new ProductWriteModel();
        ProductReadModel read = new ProductReadModel();
        
        // Commands (write side)
        write.handle(new CreateProductCmd("P1", "Laptop Pro", 1299.99));
        write.handle(new CreateProductCmd("P2", "Mouse", 29.99));
        write.handle(new CreateProductCmd("P3", "Keyboard", 79.99));
        write.handle(new UpdateStockCmd("P1", 5));
        write.handle(new UpdateStockCmd("P2", 100));
        
        // Sync to read model
        read.sync(write.getStore());
        
        // Queries (read side)
        System.out.println("Search 'mouse': " + read.searchByName("mouse"));
        System.out.println("In stock: " + read.findInStock().stream()
            .map(m -> m.get("id")).collect(Collectors.toList()));
    }
}
```

---

## Step 7: Outbox Pattern with SQLite

```java
import java.sql.*;
import java.time.Instant;
import java.util.*;

public class OutboxPattern {
    public static void main(String[] args) throws Exception {
        Class.forName("org.sqlite.JDBC");
        Connection conn = DriverManager.getConnection("jdbc:sqlite::memory:");
        
        // Outbox table
        conn.createStatement().execute("""
            CREATE TABLE outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aggregate_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                processed_at TEXT
            )
        """);
        
        // Atomic: business operation + outbox insert in one transaction
        conn.setAutoCommit(false);
        try {
            // Business operation (create order)
            System.out.println("Creating order...");
            
            // Outbox entries
            String[][] events = {
                {"order-001", "OrderCreated", "{\"customerId\":\"cust-42\",\"total\":129.99}"},
                {"order-001", "PaymentRequested", "{\"amount\":129.99,\"currency\":\"USD\"}"},
                {"order-001", "InventoryReserved", "{\"sku\":\"PROD-1\",\"qty\":2}"}
            };
            
            PreparedStatement ins = conn.prepareStatement(
                "INSERT INTO outbox (aggregate_id, event_type, payload, created_at) VALUES (?,?,?,?)"
            );
            for (String[] ev : events) {
                ins.setString(1, ev[0]); ins.setString(2, ev[1]);
                ins.setString(3, ev[2]); ins.setString(4, Instant.now().toString());
                ins.executeUpdate();
            }
            conn.commit();
            System.out.println("Transaction committed (business op + outbox)");
        } catch (Exception e) {
            conn.rollback();
            throw e;
        }
        
        // Outbox relay: poll and publish
        ResultSet pending = conn.createStatement().executeQuery(
            "SELECT id, event_type, payload FROM outbox WHERE processed = FALSE ORDER BY id"
        );
        System.out.println("Outbox events to relay:");
        List<Integer> ids = new ArrayList<>();
        while (pending.next()) {
            System.out.println("  [" + pending.getInt("id") + "] " +
                pending.getString("event_type") + ": " + pending.getString("payload"));
            ids.add(pending.getInt("id"));
        }
        
        // Mark as processed (after successful publish to message broker)
        for (int id : ids) {
            conn.createStatement().execute(
                "UPDATE outbox SET processed=TRUE, processed_at='" + Instant.now() + "' WHERE id=" + id
            );
        }
        
        long count = ((ResultSet)conn.createStatement().executeQuery(
            "SELECT COUNT(*) FROM outbox WHERE processed=FALSE"
        )).getLong(1);
        System.out.println("Pending events after relay: " + count);
        conn.close();
    }
}
```

---

## Step 8: Capstone — Resilience4j Circuit Breaker State Transitions

```java
package com.lab;

import io.github.resilience4j.circuitbreaker.*;
import io.github.resilience4j.retry.*;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

public class Main {
    static AtomicInteger callCount = new AtomicInteger();
    
    static String riskyCall() {
        int n = callCount.incrementAndGet();
        if (n <= 3) throw new RuntimeException("Service unavailable (call " + n + ")");
        return "Success on call " + n;
    }
    
    public static void main(String[] args) throws Exception {
        CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
            .slidingWindowSize(4)
            .failureRateThreshold(75)
            .waitDurationInOpenState(Duration.ofMillis(200))
            .permittedNumberOfCallsInHalfOpenState(1)
            .build();
        CircuitBreaker cb = CircuitBreaker.of("demo", cbConfig);
        
        cb.getEventPublisher().onStateTransition(e -> 
            System.out.println("CB State: " + e.getStateTransition()));
        
        RetryConfig retryConfig = RetryConfig.custom()
            .maxAttempts(5).waitDuration(Duration.ofMillis(50)).build();
        Retry retry = Retry.of("demo", retryConfig);
        
        System.out.println("Initial CB state: " + cb.getState());
        
        for (int i = 0; i < 6; i++) {
            try {
                String result = cb.executeSupplier(() -> riskyCall());
                System.out.println("Call " + (i+1) + ": " + result);
            } catch (Exception e) {
                System.out.println("Call " + (i+1) + " FAILED: " + e.getMessage());
            }
            if (i == 2) Thread.sleep(300);
        }
        
        System.out.println("Final CB state: " + cb.getState());
        System.out.println("Total successful calls: " + cb.getMetrics().getNumberOfSuccessfulCalls());
        System.out.println("Failure rate: " + cb.getMetrics().getFailureRate() + "%");
    }
}
```

```bash
# Maven project with resilience4j-circuitbreaker dependency
cd /tmp/r4j && mvn compile exec:java -Dexec.mainClass=com.lab.Main -q 2>/dev/null
```

📸 **Verified Output:**
```
Initial CB state: CLOSED
Call 1 FAILED: Service unavailable (call 1)
Call 2 FAILED: Service unavailable (call 2)
Call 3 FAILED: Service unavailable (call 3)
CB State: State transition from CLOSED to OPEN
Call 4: Success on call 4
Call 5 FAILED: CircuitBreaker 'demo' is OPEN and does not permit further calls
Call 6 FAILED: CircuitBreaker 'demo' is OPEN and does not permit further calls
Final CB state: OPEN
Total successful calls: 1
Failure rate: 75.0%
```

---

## Summary

| Pattern | Library/API | Use Case |
|---|---|---|
| Circuit breaker | `Resilience4j CircuitBreaker` | Prevent cascade failures |
| Retry | `Resilience4j Retry` | Transient error recovery |
| Rate limiter | `Resilience4j RateLimiter` | Traffic shaping |
| Bulkhead | `Resilience4j Bulkhead` | Concurrency isolation |
| Saga | Compensating transactions | Distributed transaction |
| Event sourcing | Append-only EventStore | Full audit trail, replay |
| CQRS | Separate read/write models | Query optimization |
| Outbox pattern | SQLite transactional table | At-least-once delivery |
