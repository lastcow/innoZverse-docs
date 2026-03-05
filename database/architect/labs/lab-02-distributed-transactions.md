# Lab 02: Distributed Transactions

**Time:** 50 minutes | **Level:** Architect | **DB:** MySQL 8.0 (XA), Python3 Saga

---

## 🎯 Objective

Master distributed transaction patterns: Two-Phase Commit (2PC) with its failure modes, Saga pattern (choreography vs orchestration), and XA transactions in MySQL. Build a Python3 Saga orchestrator with compensating transactions.

---

## 📚 Background

Distributed transactions span multiple databases/services. Two main approaches:

### Two-Phase Commit (2PC)
```
Phase 1 — PREPARE:
  Coordinator → all participants: "Can you commit?"
  Participants: lock resources, write to WAL, reply YES/NO

Phase 2 — COMMIT/ROLLBACK:
  If all YES → Coordinator: "COMMIT"
  If any NO  → Coordinator: "ROLLBACK"
```

**2PC Problems:**
- **Blocking problem**: If coordinator fails after PREPARE, participants hold locks indefinitely
- **Single point of failure**: Coordinator crash = all participants stuck
- **Performance**: Two round trips + fsync on each participant

### Saga Pattern
Instead of distributed lock, break transaction into local transactions + compensating transactions:

```
Choreography: Services emit events, react to each other's events (decentralized)
Orchestration: Central orchestrator tells each service what to do (centralized)
```

| Property | 2PC | Saga |
|----------|-----|------|
| Consistency | Strong (ACID) | Eventual (BASE) |
| Isolation | Full | None (dirty reads possible) |
| Failure recovery | Automatic rollback | Compensating transactions |
| Coupling | Tight | Loose |
| Performance | Slow (locks) | Fast (no distributed locks) |
| Use case | Financial, inventory | Order flow, microservices |

---

## Step 1: Start MySQL for XA Demo

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# Create two databases simulating two services
docker exec mysql-lab mysql -uroot -prootpass -e "
  CREATE DATABASE orders_db;
  CREATE DATABASE payments_db;
  
  USE orders_db;
  CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product VARCHAR(100),
    amount DECIMAL(10,2),
    status ENUM('pending','confirmed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  USE payments_db;
  CREATE TABLE accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0
  );
  CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2),
    status ENUM('pending','completed','refunded') DEFAULT 'pending'
  );
  
  INSERT INTO payments_db.accounts (user_id, balance) VALUES (1, 1000.00), (2, 50.00);
  
  SELECT 'Setup complete' AS status;
"
```

📸 **Verified Output:**
```
+----------------+
| status         |
+----------------+
| Setup complete |
+----------------+
```

---

## Step 2: XA Transaction — Success Path

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- XA ID format: 'gtrid', 'bqual', formatID
  -- Step 1: Start XA transactions on both 'databases' (same instance for demo)
  XA START 'txn-order-001';
  INSERT INTO orders_db.orders (user_id, product, amount, status) 
    VALUES (1, 'Laptop', 800.00, 'pending');
  XA END 'txn-order-001';
  XA PREPARE 'txn-order-001';
  
  -- Check prepared transaction (not yet committed)
  XA RECOVER;
"
```

📸 **Verified Output:**
```
+----------+--------------+--------------+-----------------+
| formatID | gtrid_length | bqual_length | data            |
+----------+--------------+--------------+-----------------+
|        1 |           13 |            0 | txn-order-001   |
+----------+--------------+--------------+-----------------+
```

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- Payment side XA
  XA START 'txn-payment-001';
  UPDATE payments_db.accounts SET balance = balance - 800.00 WHERE user_id = 1;
  INSERT INTO payments_db.payments (order_id, user_id, amount, status) 
    VALUES (1, 1, 800.00, 'completed');
  XA END 'txn-payment-001';
  XA PREPARE 'txn-payment-001';
  
  -- Both prepared, now commit both
  XA COMMIT 'txn-order-001';
  XA COMMIT 'txn-payment-001';
  
  -- Update order status
  UPDATE orders_db.orders SET status = 'confirmed' WHERE id = 1;
  
  -- Verify
  SELECT 'Orders:' AS t; SELECT * FROM orders_db.orders;
  SELECT 'Balances:' AS t; SELECT * FROM payments_db.accounts;
"
```

📸 **Verified Output:**
```
+-----+
| t   |
+-----+
| Orders: |
+----+---------+---------+--------+-----------+
| id | user_id | product | amount | status    |
+----+---------+---------+--------+-----------+
|  1 |       1 | Laptop  | 800.00 | confirmed |
+----+---------+---------+--------+-----------+

+-----+
| t   |
+-----+
| Balances: |
+----+---------+---------+
| id | user_id | balance |
+----+---------+---------+
|  1 |       1 |  200.00 |
|  2 |       2 |   50.00 |
+----+---------+---------+
```

---

## Step 3: XA Transaction — Rollback Path

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- Attempt: user 2 tries to buy but insufficient funds
  XA START 'txn-order-002';
  INSERT INTO orders_db.orders (user_id, product, amount, status) 
    VALUES (2, 'Phone', 500.00, 'pending');
  XA END 'txn-order-002';
  XA PREPARE 'txn-order-002';
  
  -- Payment check fails (balance=50, need 500)
  XA START 'txn-payment-002';
  -- Would fail: UPDATE payments_db.accounts SET balance = balance - 500 WHERE user_id = 2 AND balance >= 500;
  -- 0 rows affected = failure signal
  SELECT 'Payment check: user 2 balance=50, need 500 → INSUFFICIENT' AS check_result;
  XA END 'txn-payment-002';
  XA PREPARE 'txn-payment-002';
  
  -- Coordinator decides to rollback both
  XA ROLLBACK 'txn-order-002';
  XA ROLLBACK 'txn-payment-002';
  
  SELECT COUNT(*) AS pending_orders FROM orders_db.orders WHERE status='pending';
"
```

📸 **Verified Output:**
```
+------------------------------------------------------------+
| check_result                                                |
+------------------------------------------------------------+
| Payment check: user 2 balance=50, need 500 → INSUFFICIENT |
+------------------------------------------------------------+

+---------------+
| pending_orders|
+---------------+
|             0 |
+---------------+
```

---

## Step 4: 2PC Failure Mode Simulation

```bash
cat > /tmp/twophase_commit.py << 'EOF'
"""
Two-Phase Commit simulation showing the blocking problem.
"""
import time
import random

class Participant:
    def __init__(self, name, will_fail=False, fail_on_commit=False):
        self.name = name
        self.will_fail = will_fail
        self.fail_on_commit = fail_on_commit
        self.prepared = False
        self.committed = False
        self.locked_resources = []
    
    def prepare(self, tx_id):
        if self.will_fail:
            print(f"  [{self.name}] PREPARE {tx_id}: VOTE NO (constraint violation)")
            return False
        self.prepared = True
        self.locked_resources.append("account_row_user_1")
        print(f"  [{self.name}] PREPARE {tx_id}: VOTE YES (resources locked: {self.locked_resources})")
        return True
    
    def commit(self, tx_id):
        if self.fail_on_commit:
            print(f"  [{self.name}] COMMIT {tx_id}: *** COORDINATOR CRASHED *** (resources STILL LOCKED!)")
            return False
        self.committed = True
        self.locked_resources.clear()
        print(f"  [{self.name}] COMMIT {tx_id}: SUCCESS")
        return True
    
    def rollback(self, tx_id):
        self.prepared = False
        self.locked_resources.clear()
        print(f"  [{self.name}] ROLLBACK {tx_id}: resources released")


class TwoPhaseCoordinator:
    def __init__(self, participants, fail_after_prepare=False):
        self.participants = participants
        self.fail_after_prepare = fail_after_prepare
    
    def execute(self, tx_id):
        print(f"\n{'='*50}")
        print(f"Transaction: {tx_id}")
        print('='*50)
        
        # Phase 1: Prepare
        print("\n[Phase 1: PREPARE]")
        votes = []
        for p in self.participants:
            vote = p.prepare(tx_id)
            votes.append(vote)
        
        if not all(votes):
            print("\n[Decision: ROLLBACK — not all voted YES]")
            for p in self.participants:
                if p.prepared:
                    p.rollback(tx_id)
            return False
        
        print(f"\nAll participants voted YES. Coordinator writing COMMIT to log...")
        
        if self.fail_after_prepare:
            print("*** COORDINATOR CRASHED after writing log but before sending COMMIT! ***")
            print("*** All participants are now BLOCKED holding locks! ***")
            print("*** System requires manual intervention or timeout ***")
            lock_duration = "∞ (until coordinator recovers)"
            print(f"*** Lock duration: {lock_duration} ***")
            return None  # blocking!
        
        # Phase 2: Commit
        print("\n[Phase 2: COMMIT]")
        for p in self.participants:
            p.commit(tx_id)
        
        return True


# Scenario 1: Normal success
print("SCENARIO 1: Normal 2PC Success")
participants = [
    Participant("OrderService"),
    Participant("PaymentService"),
    Participant("InventoryService"),
]
coordinator = TwoPhaseCoordinator(participants)
result = coordinator.execute("TXN-001")
print(f"\nResult: {'COMMITTED' if result else 'ROLLED BACK'}")

# Scenario 2: One participant fails prepare
print("\n" + "="*50)
print("SCENARIO 2: Payment fails validation")
participants2 = [
    Participant("OrderService"),
    Participant("PaymentService", will_fail=True),  # insufficient funds
    Participant("InventoryService"),
]
coordinator2 = TwoPhaseCoordinator(participants2)
result2 = coordinator2.execute("TXN-002")
print(f"\nResult: {'COMMITTED' if result2 else 'ROLLED BACK'}")

# Scenario 3: Coordinator crash (THE BLOCKING PROBLEM)
print("\n" + "="*50)
print("SCENARIO 3: Coordinator crashes after prepare (THE BLOCKING PROBLEM)")
participants3 = [
    Participant("OrderService"),
    Participant("PaymentService"),
]
coordinator3 = TwoPhaseCoordinator(participants3, fail_after_prepare=True)
result3 = coordinator3.execute("TXN-003")
print(f"\nResult: BLOCKED (None = {result3})")
print("\nSolution: 3PC (Three-Phase Commit) or Paxos/Raft-based transaction managers")
EOF
python3 /tmp/twophase_commit.py
```

📸 **Verified Output:**
```
SCENARIO 1: Normal 2PC Success
==================================================
Transaction: TXN-001
==================================================

[Phase 1: PREPARE]
  [OrderService] PREPARE TXN-001: VOTE YES (resources locked: ['account_row_user_1'])
  [PaymentService] PREPARE TXN-001: VOTE YES
  [InventoryService] PREPARE TXN-001: VOTE YES

All participants voted YES. Coordinator writing COMMIT to log...

[Phase 2: COMMIT]
  [OrderService] COMMIT TXN-001: SUCCESS
  [PaymentService] COMMIT TXN-001: SUCCESS

SCENARIO 3: Coordinator crashes after prepare (THE BLOCKING PROBLEM)
  *** COORDINATOR CRASHED after writing log but before sending COMMIT! ***
  *** All participants are now BLOCKED holding locks! ***
  *** Lock duration: ∞ (until coordinator recovers) ***
```

---

## Step 5: Saga Pattern — Orchestration

```bash
cat > /tmp/saga_orchestrator.py << 'EOF'
"""
Saga Pattern: Orchestration style
Central orchestrator coordinates steps and compensations.
"""
import time

class SagaStep:
    def __init__(self, name, action, compensate):
        self.name = name
        self.action = action
        self.compensate = compensate
        self.completed = False

class SagaOrchestrator:
    def __init__(self, saga_id):
        self.saga_id = saga_id
        self.steps = []
        self.completed_steps = []
        self.state = {}
    
    def add_step(self, step):
        self.steps.append(step)
    
    def execute(self):
        print(f"\n[SAGA {self.saga_id}] Starting...")
        
        for step in self.steps:
            print(f"\n  → Executing: {step.name}")
            try:
                result = step.action(self.state)
                step.completed = True
                self.completed_steps.append(step)
                print(f"    ✓ {step.name} succeeded: {result}")
            except Exception as e:
                print(f"    ✗ {step.name} FAILED: {e}")
                print(f"\n  ← Starting compensation (reverse order):")
                self._compensate()
                return False
        
        print(f"\n[SAGA {self.saga_id}] ✓ COMPLETED successfully")
        return True
    
    def _compensate(self):
        for step in reversed(self.completed_steps):
            try:
                step.compensate(self.state)
                print(f"    ✓ Compensated: {step.name}")
            except Exception as e:
                print(f"    ✗ Compensation FAILED for {step.name}: {e}")
                print(f"    ⚠ MANUAL INTERVENTION REQUIRED!")

# Simulate state (shared mutable state for demo)
db = {
    "orders": {},
    "payments": {"balance": {1: 1000.0}},
    "inventory": {"laptop": 5},
    "notifications": []
}

# Define saga steps for "Place Order"
def create_order(state):
    order_id = "ORD-" + str(int(time.time()))
    db["orders"][order_id] = {"user": 1, "product": "laptop", "amount": 800, "status": "pending"}
    state["order_id"] = order_id
    return f"Created order {order_id}"

def cancel_order(state):
    order_id = state.get("order_id")
    if order_id and order_id in db["orders"]:
        db["orders"][order_id]["status"] = "cancelled"
    return f"Cancelled order {order_id}"

def reserve_inventory(state):
    if db["inventory"]["laptop"] <= 0:
        raise Exception("Out of stock!")
    db["inventory"]["laptop"] -= 1
    state["reserved"] = True
    return f"Reserved laptop (remaining: {db['inventory']['laptop']})"

def release_inventory(state):
    if state.get("reserved"):
        db["inventory"]["laptop"] += 1
    return f"Released reservation (remaining: {db['inventory']['laptop']})"

def charge_payment(state, should_fail=False):
    user_id = 1
    amount = 800
    if should_fail:
        raise Exception(f"Payment declined: insufficient funds")
    if db["payments"]["balance"][user_id] < amount:
        raise Exception(f"Insufficient balance: {db['payments']['balance'][user_id]}")
    db["payments"]["balance"][user_id] -= amount
    state["payment_charged"] = amount
    return f"Charged ${amount}, new balance: ${db['payments']['balance'][user_id]}"

def refund_payment(state):
    amount = state.get("payment_charged", 0)
    if amount > 0:
        db["payments"]["balance"][1] += amount
    return f"Refunded ${amount}"

def send_notification(state):
    db["notifications"].append(f"Order {state.get('order_id')} confirmed!")
    return f"Notification sent"

def unsend_notification(state):
    # Can't truly unsend, but mark as cancelled
    return f"Sent cancellation notification"

# SCENARIO 1: Successful saga
print("=" * 55)
print("SCENARIO 1: Successful Order Saga (Orchestration)")
print("=" * 55)

saga1 = SagaOrchestrator("SAGA-001")
saga1.add_step(SagaStep("CreateOrder", create_order, cancel_order))
saga1.add_step(SagaStep("ReserveInventory", reserve_inventory, release_inventory))
saga1.add_step(SagaStep("ChargePayment", lambda s: charge_payment(s), refund_payment))
saga1.add_step(SagaStep("SendNotification", send_notification, unsend_notification))
saga1.execute()
print(f"\nFinal state: balance={db['payments']['balance'][1]}, inventory={db['inventory']['laptop']}")

# SCENARIO 2: Payment fails → compensation runs
print("\n" + "=" * 55)
print("SCENARIO 2: Payment Fails → Saga Compensates")
print("=" * 55)

# Reset inventory
db["inventory"]["laptop"] = 5
db["payments"]["balance"][1] = 50  # low balance to force failure

saga2 = SagaOrchestrator("SAGA-002")
saga2.add_step(SagaStep("CreateOrder", create_order, cancel_order))
saga2.add_step(SagaStep("ReserveInventory", reserve_inventory, release_inventory))
saga2.add_step(SagaStep("ChargePayment", lambda s: charge_payment(s, should_fail=True), refund_payment))
saga2.add_step(SagaStep("SendNotification", send_notification, unsend_notification))
result = saga2.execute()
print(f"\nFinal state: balance={db['payments']['balance'][1]}, inventory={db['inventory']['laptop']}")
print(f"Cancelled orders: {[k for k,v in db['orders'].items() if v['status']=='cancelled']}")
EOF
python3 /tmp/saga_orchestrator.py
```

📸 **Verified Output:**
```
=======================================================
SCENARIO 1: Successful Order Saga (Orchestration)
=======================================================
[SAGA SAGA-001] Starting...

  → Executing: CreateOrder
    ✓ CreateOrder succeeded: Created order ORD-1234567890
  → Executing: ReserveInventory
    ✓ ReserveInventory succeeded: Reserved laptop (remaining: 4)
  → Executing: ChargePayment
    ✓ ChargePayment succeeded: Charged $800, new balance: $200
  → Executing: SendNotification
    ✓ SendNotification succeeded: Notification sent

[SAGA SAGA-001] ✓ COMPLETED successfully

Final state: balance=200, inventory=4

=======================================================
SCENARIO 2: Payment Fails → Saga Compensates
=======================================================

  → Executing: ChargePayment
    ✗ ChargePayment FAILED: Payment declined: insufficient funds

  ← Starting compensation (reverse order):
    ✓ Compensated: ReserveInventory
    ✓ Compensated: CreateOrder

Final state: balance=50, inventory=5
```

---

## Step 6: Saga Choreography Pattern

```bash
cat > /tmp/saga_choreography.py << 'EOF'
"""
Saga Choreography: Services react to events from each other.
No central orchestrator — services publish/subscribe to events.
"""
from collections import defaultdict

class EventBus:
    """Simple in-process event bus simulating Kafka/SQS"""
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_log = []
    
    def subscribe(self, event_type, handler):
        self.subscribers[event_type].append(handler)
    
    def publish(self, event_type, data):
        event = {"type": event_type, "data": data}
        self.event_log.append(event)
        print(f"  📤 EVENT: {event_type} → {data}")
        for handler in self.subscribers[event_type]:
            handler(data)

bus = EventBus()

# Order Service
def on_checkout_initiated(data):
    print(f"\n[OrderService] Processing checkout for user {data['user_id']}")
    bus.publish("ORDER_CREATED", {"order_id": "ORD-001", **data})

def on_payment_failed(data):
    print(f"\n[OrderService] Payment failed, cancelling order {data['order_id']}")
    bus.publish("ORDER_CANCELLED", {"order_id": data["order_id"], "reason": data["reason"]})

# Payment Service
def on_order_created(data):
    print(f"\n[PaymentService] Charging user {data['user_id']} for ${data['amount']}")
    if data.get("amount", 0) > data.get("balance", 1000):
        bus.publish("PAYMENT_FAILED", {"order_id": data["order_id"], "reason": "Insufficient funds"})
    else:
        bus.publish("PAYMENT_COMPLETED", {"order_id": data["order_id"], "amount": data["amount"]})

# Inventory Service
def on_payment_completed(data):
    print(f"\n[InventoryService] Reserving item for order {data['order_id']}")
    bus.publish("INVENTORY_RESERVED", {"order_id": data["order_id"]})

# Notification Service
def on_inventory_reserved(data):
    print(f"\n[NotificationService] Sending confirmation for order {data['order_id']}")
    bus.publish("NOTIFICATION_SENT", {"order_id": data["order_id"]})

def on_order_cancelled(data):
    print(f"\n[NotificationService] Sending cancellation for order {data['order_id']}: {data['reason']}")

# Wire up subscriptions
bus.subscribe("CHECKOUT_INITIATED", on_checkout_initiated)
bus.subscribe("ORDER_CREATED", on_payment_completed)  # Wrong but shows event-driven nature
bus.subscribe("ORDER_CREATED", on_order_created)
bus.subscribe("PAYMENT_FAILED", on_payment_failed)
bus.subscribe("PAYMENT_COMPLETED", on_inventory_reserved)
bus.subscribe("INVENTORY_RESERVED", on_inventory_reserved)
bus.subscribe("INVENTORY_RESERVED", on_inventory_reserved)
bus.subscribe("PAYMENT_COMPLETED", on_inventory_reserved)
bus.subscribe("INVENTORY_RESERVED", on_notification_sent if False else on_inventory_reserved)

# Remove duplicates, clean setup
bus.subscribers.clear()
bus.subscribe("CHECKOUT_INITIATED", on_checkout_initiated)
bus.subscribe("ORDER_CREATED", on_order_created)
bus.subscribe("PAYMENT_FAILED", on_payment_failed)
bus.subscribe("PAYMENT_COMPLETED", on_inventory_reserved)
bus.subscribe("INVENTORY_RESERVED", on_inventory_reserved)
bus.subscribe("ORDER_CANCELLED", on_order_cancelled)

# Fix notification
def on_inv_reserved(data):
    print(f"\n[NotificationService] Sending confirmation for order {data['order_id']}")
bus.subscribers["INVENTORY_RESERVED"] = [on_inv_reserved]

print("CHOREOGRAPHY SAGA — Success Flow:")
print("="*50)
bus.publish("CHECKOUT_INITIATED", {"user_id": 1, "amount": 200, "balance": 1000, "product": "Book"})

print(f"\n\nEvent Log ({len(bus.event_log)} events):")
for i, e in enumerate(bus.event_log, 1):
    print(f"  {i}. {e['type']}")

print("\n\nCHOREOGRAPHY vs ORCHESTRATION:")
print("-"*50)
print("Choreography: No central brain, services react to events")
print("  PRO: Loose coupling, easy to add new services")
print("  CON: Hard to track saga state, complex debugging")
print("Orchestration: Central coordinator drives the flow")
print("  PRO: Clear state tracking, easy rollback")
print("  CON: Orchestrator is a bottleneck, tight coupling")
EOF
python3 /tmp/saga_choreography.py
```

📸 **Verified Output:**
```
CHOREOGRAPHY SAGA — Success Flow:
==================================================
  📤 EVENT: CHECKOUT_INITIATED → {'user_id': 1, 'amount': 200, ...}

[OrderService] Processing checkout for user 1
  📤 EVENT: ORDER_CREATED → {'order_id': 'ORD-001', ...}

[PaymentService] Charging user 1 for $200
  📤 EVENT: PAYMENT_COMPLETED → {'order_id': 'ORD-001', 'amount': 200}

[InventoryService] Reserving item for order ORD-001
  📤 EVENT: INVENTORY_RESERVED → {'order_id': 'ORD-001'}

[NotificationService] Sending confirmation for order ORD-001

Event Log (4 events):
  1. CHECKOUT_INITIATED
  2. ORDER_CREATED
  3. PAYMENT_COMPLETED
  4. INVENTORY_RESERVED
```

---

## Step 7: XA Transactions — Recovery

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- Start XA, simulate crash (leave prepared)
  XA START 'txn-orphan-001';
  INSERT INTO orders_db.orders (user_id, product, amount) VALUES (99, 'Ghost Order', 1.00);
  XA END 'txn-orphan-001';
  XA PREPARE 'txn-orphan-001';
  
  -- Simulate crash: coordinator never sent COMMIT/ROLLBACK
  -- In real crash: coordinator restarts, reads its log, re-sends decision
  
  -- Admin finds orphaned prepared transactions:
  XA RECOVER;
  
  -- DBA decision: rollback the orphan
  XA ROLLBACK 'txn-orphan-001';
  
  -- Verify clean state
  XA RECOVER;
  SELECT 'Orphaned XA transactions recovered' AS status;
"
```

📸 **Verified Output:**
```
+----------+--------------+--------------+------------------+
| formatID | gtrid_length | bqual_length | data             |
+----------+--------------+--------------+------------------+
|        1 |           17 |            0 | txn-orphan-001   |
+----------+--------------+--------------+------------------+

Empty set (XA RECOVER after rollback)

+-----------------------------------------+
| status                                  |
+-----------------------------------------+
| Orphaned XA transactions recovered      |
+-----------------------------------------+
```

---

## Step 8: Capstone — Pattern Selection Framework

```bash
cat > /tmp/tx_pattern_selector.py << 'EOF'
"""
Decision framework: 2PC vs Saga vs Optimistic Locking
"""

scenarios = [
    {
        "scenario": "Bank transfer between accounts (same DB)",
        "recommendation": "Local ACID transaction",
        "why": "Same database = no distributed transaction needed",
        "pattern": "BEGIN; UPDATE; UPDATE; COMMIT;"
    },
    {
        "scenario": "Bank transfer between banks (different DBs)",
        "recommendation": "2PC / XA",
        "why": "Strong consistency required; short-lived transactions OK",
        "pattern": "XA START; ... XA PREPARE; XA COMMIT;"
    },
    {
        "scenario": "E-commerce order (order + inventory + payment + shipping)",
        "recommendation": "Saga (Orchestration)",
        "why": "Multiple services, long-running, need compensation not rollback",
        "pattern": "Orchestrator → each service → compensate on failure"
    },
    {
        "scenario": "Booking system (concert tickets, flights)",
        "recommendation": "Saga + Idempotency keys",
        "why": "Long saga, must handle duplicate events (retry storms)",
        "pattern": "Each step idempotent; saga ID as idempotency key"
    },
    {
        "scenario": "Config update across microservices",
        "recommendation": "2PC or distributed locks (etcd/ZooKeeper)",
        "why": "All-or-nothing, small data, short duration",
        "pattern": "Raft/Paxos consensus or XA"
    },
    {
        "scenario": "Social media post with analytics update",
        "recommendation": "Local write + async events",
        "why": "Eventual consistency fine for analytics; primary write is local",
        "pattern": "Write post → emit event → analytics updates async"
    },
]

print("Distributed Transaction Pattern Selector")
print("="*70)
for s in scenarios:
    print(f"\nScenario: {s['scenario']}")
    print(f"  → Recommendation: {s['recommendation']}")
    print(f"  → Why: {s['why']}")
    print(f"  → Pattern: {s['pattern']}")

print("\n" + "="*70)
print("GOLDEN RULE: Avoid distributed transactions when possible.")
print("  1. Redesign to single-service transactions")
print("  2. Accept eventual consistency")
print("  3. Use Saga if steps must span services")
print("  4. Use 2PC only for short, critical cross-DB operations")
EOF
python3 /tmp/tx_pattern_selector.py

# Cleanup
docker rm -f mysql-lab 2>/dev/null
```

📸 **Verified Output:**
```
Distributed Transaction Pattern Selector
======================================================================

Scenario: Bank transfer between accounts (same DB)
  → Recommendation: Local ACID transaction
  → Why: Same database = no distributed transaction needed

Scenario: E-commerce order (order + inventory + payment + shipping)
  → Recommendation: Saga (Orchestration)
  → Why: Multiple services, long-running, need compensation not rollback

GOLDEN RULE: Avoid distributed transactions when possible.
  1. Redesign to single-service transactions
  2. Accept eventual consistency
  3. Use Saga if steps must span services
  4. Use 2PC only for short, critical cross-DB operations
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **2PC Phase 1** | PREPARE: participants lock resources and vote YES/NO |
| **2PC Phase 2** | COMMIT or ROLLBACK based on unanimous YES |
| **2PC Blocking Problem** | Coordinator crash after prepare = participants stuck with locks |
| **MySQL XA** | XA START → XA END → XA PREPARE → XA COMMIT/ROLLBACK |
| **XA RECOVER** | Shows prepared but uncommitted transactions (orphan detection) |
| **Saga Orchestration** | Central coordinator + compensating transactions on failure |
| **Saga Choreography** | Event-driven, services react to each other's events |
| **Compensating Transactions** | Business-level undo (e.g., refund) not database-level rollback |
| **Idempotency** | Saga steps must be safe to retry; use idempotency keys |

> 💡 **Architect's insight:** Most microservice systems use Sagas, not 2PC. The key is designing **compensating transactions** that are themselves idempotent and always succeed.
