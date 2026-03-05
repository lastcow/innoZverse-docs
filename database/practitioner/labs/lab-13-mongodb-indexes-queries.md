# Lab 13: MongoDB Indexes and Query Optimization

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MongoDB 7

MongoDB indexes work similarly to SQL indexes — they are B-tree (or specialized) structures that speed up queries. Without indexes, every query does a full collection scan (COLLSCAN).

---

## Step 1 — Setup: Products Collection

```javascript
use shopdb

db.products.drop()
db.products.insertMany([
  { name: "Laptop Pro",       category: "Electronics", price: 1299.99, stock: 50,  tags: ["laptop","portable"],   brand: "TechCo",   rating: 4.5, createdAt: new Date("2024-01-01") },
  { name: "Wireless Mouse",   category: "Electronics", price: 29.99,  stock: 200, tags: ["mouse","wireless"],     brand: "PeriphCo", rating: 4.2, createdAt: new Date("2024-01-05") },
  { name: "Mechanical Keyboard", category: "Electronics", price: 89.99, stock: 150, tags: ["keyboard","mechanical"], brand: "TypeCo",   rating: 4.7, createdAt: new Date("2024-01-10") },
  { name: "Running Shoes",    category: "Sports",      price: 79.99,  stock: 100, tags: ["shoes","running"],      brand: "SportCo",  rating: 4.3, createdAt: new Date("2024-01-15") },
  { name: "Python Book",      category: "Books",       price: 39.99,  stock: 75,  tags: ["python","programming"], brand: "LearnCo",  rating: 4.8, createdAt: new Date("2024-01-20") },
  { name: "Coffee Maker",     category: "Kitchen",     price: 49.99,  stock: 80,  tags: ["coffee","appliance"],   brand: "BrewCo",   rating: 3.9, createdAt: new Date("2024-01-25") },
  { name: "Smart Watch",      category: "Electronics", price: 299.99, stock: 60,  tags: ["watch","smart","wearable"], brand: "TechCo", rating: 4.1, createdAt: new Date("2024-01-30") }
])
print("Total products:", db.products.countDocuments())
```

---

## Step 2 — Single Field Index

```javascript
// Without index: COLLSCAN
let plan1 = db.products.find({ brand: "TechCo" }).explain("executionStats")
print("Without index - stage:", plan1.executionStats.executionStages.stage)
print("Docs examined:", plan1.executionStats.totalDocsExamined)

// Create single field index
db.products.createIndex({ brand: 1 })  // 1 = ascending, -1 = descending

// With index: IXSCAN
let plan2 = db.products.find({ brand: "TechCo" }).explain("executionStats")
print("With index - stage:", plan2.queryPlanner.winningPlan.stage)
print("Docs returned:", plan2.executionStats.nReturned)
print("Keys examined:", plan2.executionStats.totalKeysExamined)
```

📸 **Verified Output:**
```
Without index - stage: COLLSCAN
Docs examined: 7
With index - stage: FETCH
Docs returned: 2
Keys examined: 2
```

> 💡 The `FETCH` stage means MongoDB used an index (IXSCAN) then fetched documents from the collection. `COLLSCAN` means no index was used — read all documents.

---

## Step 3 — Compound Index

```javascript
// Compound index: multiple fields
// Order matters! Use ESR rule: Equality → Sort → Range
db.products.createIndex({ category: 1, price: -1 })

// This query uses the compound index efficiently
let res = db.products.find(
  { category: "Electronics", price: { $lt: 200 } }
).sort({ price: -1 })

res.forEach(p => print(p.name, "$" + p.price))

// Check the plan
let plan = db.products.find(
  { category: "Electronics", price: { $lt: 200 } }
).sort({ price: -1 }).explain("executionStats")
print("Stage:", plan.queryPlanner.winningPlan.stage)
print("Keys examined:", plan.executionStats.totalKeysExamined)
print("Docs returned:", plan.executionStats.nReturned)
```

📸 **Verified Output:**
```
Mechanical Keyboard $89.99
Wireless Mouse $29.99
Stage: FETCH
Keys examined: 2
Docs returned: 2
```

> 💡 **ESR Rule** for compound index column order: **E**quality fields first, then **S**ort fields, then **R**ange fields. This matches MongoDB's query execution order.

---

## Step 4 — Multikey Index (Arrays)

```javascript
// Multikey index: automatically created when indexing an array field
db.products.createIndex({ tags: 1 })

// MongoDB creates one index entry per array element
let plan = db.products.find({ tags: "laptop" }).explain("executionStats")
print("Multikey:", plan.queryPlanner.winningPlan.inputStage?.isMultiKey)
print("Docs returned:", plan.executionStats.nReturned)

// Array queries use the multikey index
db.products.find({ tags: { $in: ["laptop", "running"] } })
  .forEach(p => print(p.name, p.tags))

db.products.find({ tags: { $all: ["smart", "watch"] } })
  .forEach(p => print(p.name, p.tags))
```

📸 **Verified Output:**
```
Laptop Pro ["laptop","portable"]
Running Shoes ["shoes","running"]
Smart Watch ["watch","smart","wearable"]
```

> 💡 You cannot create a compound index where more than one field is an array. MongoDB cannot index multiple array fields in the same index — would cause a combinatorial explosion.

---

## Step 5 — Text Index and Wildcard Index

```javascript
// Text index: for full-text search
db.products.createIndex({ name: "text", brand: "text" })
// Only ONE text index allowed per collection

// Text search
db.products.find({ $text: { $search: "laptop portable" } })
  .forEach(p => print(p.name))

// With text score
db.products.find(
  { $text: { $search: "TechCo laptop" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
  .forEach(p => print(p.name, p.score?.toFixed(3)))

// Wildcard index: index all fields (useful for dynamic schemas)
db.products.createIndex({ "$**": 1 })

// Or wildcard on specific sub-document
// db.products.createIndex({ "specs.$**": 1 })
```

---

## Step 6 — TTL Index

```javascript
// TTL index: automatically delete documents after N seconds
db.sessions.drop()
db.sessions.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 3600 }  // delete after 1 hour
)

db.sessions.insertMany([
  { userId: "user:1", token: "abc123", createdAt: new Date() },
  { userId: "user:2", token: "def456", createdAt: new Date(Date.now() - 7200000) }  // 2 hours ago
])

print("Sessions inserted:", db.sessions.countDocuments())
print("Note: TTL background task runs every 60 seconds")
print("Sessions older than 1 hour will be deleted automatically")

// View all indexes on products
print("\nAll indexes on products:")
db.products.getIndexes().forEach(idx =>
  print(" ", idx.name, "->", JSON.stringify(idx.key), idx.unique ? "(unique)" : "")
)
```

📸 **Verified Output:**
```
All indexes on products:
  _id_ -> {"_id":1}
  brand_1 -> {"brand":1}
  category_1_price_-1 -> {"category":1,"price":-1}
  tags_1 -> {"tags":1}
  name_text_brand_text -> {"_fts":"text","_ftsx":1}
  $**_1 -> {"$**":1}
```

---

## Step 7 — Covered Queries and hint()

```javascript
// Covered query: all fields in query AND projection are in the index
// MongoDB never reads the actual documents — only the index
db.products.createIndex({ category: 1, price: 1, name: 1 })

// Covered: query on category, project only category+price+name (all indexed)
let coveredPlan = db.products.find(
  { category: "Electronics" },
  { category: 1, price: 1, name: 1, _id: 0 }  // _id excluded!
).explain("executionStats")
print("Stage:", coveredPlan.queryPlanner.winningPlan.inputStage?.stage)
// PROJECTION_COVERED = no FETCH (never reads documents)

// hint(): force a specific index
db.products.find({ category: "Electronics" })
  .hint({ brand: 1 })   // force brand index even if not optimal
  .explain("queryPlanner")
  .queryPlanner.winningPlan

// hint with name
db.products.find({ category: "Electronics" })
  .hint("category_1_price_-1")
  .forEach(p => print(p.name))
```

> 💡 A covered query is one where ALL fields needed (in filter AND projection) are in the index. Include `_id: 0` in projection to avoid fetching the document just for `_id`.

---

## Step 8 — Capstone: Index Strategy for E-Commerce Queries

```javascript
// Analyze and optimize a slow e-commerce query pattern

// Query 1: Find active Electronics sorted by rating
let q1 = db.products.find(
  { category: "Electronics", stock: { $gt: 0 } }
).sort({ rating: -1 }).limit(10)

// Create optimized compound index for this pattern
db.products.createIndex(
  { category: 1, stock: 1, rating: -1 },
  { name: "idx_cat_stock_rating" }
)

// Verify with explain
let plan = db.products.find(
  { category: "Electronics", stock: { $gt: 0 } }
).sort({ rating: -1 }).limit(10).explain("executionStats")
print("Stage:", plan.queryPlanner.winningPlan.stage)
print("Index used:", plan.queryPlanner.winningPlan.inputStage?.indexName)

// Query 2: Search by text + filter
// Note: text search cannot combine with other compound indexes in complex ways

// Query 3: Find by tags (multikey) with price range
db.products.find({
  tags: { $in: ["portable", "wearable"] },
  price: { $lte: 500 }
}).forEach(p => print(p.name, "$" + p.price))

// Index usage report
let stats = db.products.aggregate([{ $indexStats: {} }]).toArray()
stats.forEach(s => print(s.name, "- accesses:", s.accesses.ops))
```

---

## Summary

| Index Type | Created With | Use Case |
|-----------|-------------|----------|
| Single field | `createIndex({ field: 1 })` | Equality, range on one field |
| Compound | `createIndex({ a: 1, b: -1 })` | Multi-field queries (ESR order) |
| Multikey | Auto when field is array | Array containment (`$in`, `$all`) |
| Text | `createIndex({ field: "text" })` | Full-text `$text` search |
| Wildcard | `createIndex({ "$**": 1 })` | Dynamic/unknown field names |
| TTL | `createIndex` + `expireAfterSeconds` | Auto-expiring documents |
| Unique | `createIndex({ f: 1 }, { unique: true })` | Enforce uniqueness |
| Partial | `createIndex({ f: 1 }, { partialFilterExpression: {} })` | Subset of documents |
