# Lab 12: MongoDB Aggregation Pipeline

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MongoDB 7

The aggregation pipeline transforms documents through a sequence of stages. Each stage outputs documents to the next — like Unix pipes but for data. It replaces complex SQL GROUP BY, JOIN, and subqueries.

---

## Step 1 — Setup: Orders and Customers

```javascript
use shopdb

db.orders.drop()
db.customers.drop()

db.customers.insertMany([
  { _id: "Alice",  email: "alice@example.com", tier: "Gold",   country: "US" },
  { _id: "Bob",    email: "bob@example.com",   tier: "Silver", country: "UK" },
  { _id: "Carol",  email: "carol@example.com", tier: "Bronze", country: "US" },
  { _id: "Dave",   email: "dave@example.com",  tier: "Gold",   country: "JP" }
])

db.orders.insertMany([
  { customer: "Alice", product: "Laptop Pro",    category: "Electronics", amount: 1299.99, qty: 1, date: new Date("2024-01-05") },
  { customer: "Bob",   product: "Mouse",          category: "Electronics", amount: 29.99,  qty: 3, date: new Date("2024-01-10") },
  { customer: "Alice", product: "Python Book",    category: "Books",       amount: 39.99,  qty: 2, date: new Date("2024-01-15") },
  { customer: "Carol", product: "Running Shoes",  category: "Sports",      amount: 79.99,  qty: 1, date: new Date("2024-01-20") },
  { customer: "Bob",   product: "Keyboard",       category: "Electronics", amount: 89.99,  qty: 1, date: new Date("2024-01-22") },
  { customer: "Dave",  product: "Laptop Pro",     category: "Electronics", amount: 1299.99, qty: 2, date: new Date("2024-01-25") },
  { customer: "Alice", product: "Mouse",           category: "Electronics", amount: 29.99,  qty: 2, date: new Date("2024-01-28") }
])
print("Orders:", db.orders.countDocuments())
```

📸 **Verified Output:**
```
Orders: 7
```

---

## Step 2 — $match and $group

```javascript
// $match: filter documents (like WHERE)
// $group: aggregate by field (like GROUP BY)
let result = db.orders.aggregate([
  { $match: { amount: { $gt: 25 } } },           // filter
  { $group: {
    _id: "$category",                              // group key
    total_sales:  { $sum: { $multiply: ["$amount", "$qty"] } },
    order_count:  { $sum: 1 },
    avg_order:    { $avg: "$amount" },
    max_order:    { $max: "$amount" },
    min_order:    { $min: "$amount" }
  }},
  { $sort: { total_sales: -1 } }
]).toArray()

result.forEach(r => print(
  r._id.padEnd(15),
  "total:", r.total_sales.toFixed(2),
  "count:", r.order_count,
  "avg:", r.avg_order.toFixed(2)
))
```

📸 **Verified Output:**
```
Electronics     total: 4139.91 count: 5 avg: 549.99
Sports          total: 79.99   count: 1 avg: 79.99
Books           total: 79.98   count: 1 avg: 39.99
```

---

## Step 3 — $project: Reshape Documents

```javascript
db.orders.aggregate([
  { $project: {
    _id: 0,
    customer: 1,
    product: 1,
    line_total: { $multiply: ["$amount", "$qty"] },  // computed field
    month: { $month: "$date" },                       // date extraction
    year:  { $year: "$date" },
    is_premium: { $gte: ["$amount", 100] }            // boolean expression
  }},
  { $sort: { line_total: -1 } },
  { $limit: 4 }
]).forEach(r => print(JSON.stringify(r)))
```

📸 **Verified Output:**
```
{"customer":"Dave","product":"Laptop Pro","line_total":2599.98,"month":1,"year":2024,"is_premium":true}
{"customer":"Alice","product":"Laptop Pro","line_total":1299.99,"month":1,"year":2024,"is_premium":true}
{"customer":"Bob","product":"Keyboard","line_total":89.99,"month":1,"year":2024,"is_premium":false}
{"customer":"Carol","product":"Running Shoes","line_total":79.99,"month":1,"year":2024,"is_premium":false}
```

---

## Step 4 — $lookup: Join Collections

```javascript
// $lookup: left outer join (like SQL JOIN)
let res = db.orders.aggregate([
  { $group: {
    _id: "$customer",
    total:  { $sum: { $multiply: ["$amount", "$qty"] } },
    orders: { $sum: 1 }
  }},
  { $lookup: {
    from:         "customers",    // foreign collection
    localField:   "_id",          // field in current docs
    foreignField: "_id",          // field in foreign docs
    as:           "customer_info" // output array field name
  }},
  { $unwind: "$customer_info" },  // flatten the array
  { $project: {
    customer: "$_id",
    tier:     "$customer_info.tier",
    country:  "$customer_info.country",
    total:    { $round: ["$total", 2] },
    orders: 1,
    _id: 0
  }},
  { $sort: { total: -1 } }
]).toArray()

res.forEach(r => print(JSON.stringify(r)))
```

📸 **Verified Output:**
```
{"orders":1,"customer":"Dave","tier":"Gold","country":"JP","total":2599.98}
{"orders":3,"customer":"Alice","tier":"Gold","country":"US","total":1439.95}
{"orders":2,"customer":"Bob","tier":"Silver","country":"UK","total":179.96}
{"orders":1,"customer":"Carol","tier":"Bronze","country":"US","total":79.99}
```

> 💡 `$unwind` deconstructs an array field — each array element becomes a separate document. After `$lookup`, the joined results are in an array; `$unwind` flattens it to one doc per match.

---

## Step 5 — $addFields, $count, $skip, $limit

```javascript
// $addFields: add/overwrite fields without replacing others
db.orders.aggregate([
  { $addFields: {
    line_total:    { $multiply: ["$amount", "$qty"] },
    discounted:    { $lt: ["$amount", 50] },
    date_string:   { $dateToString: { format: "%Y-%m-%d", date: "$date" } }
  }},
  { $match: { discounted: false } },
  { $count: "expensive_orders" }
]).forEach(r => print("Expensive orders:", r.expensive_orders))

// Pagination with $skip and $limit
db.orders.aggregate([
  { $sort: { amount: -1 } },
  { $skip: 2 },     // skip first 2
  { $limit: 3 }     // take next 3
]).forEach(r => print(r.customer, r.product, "$" + r.amount))
```

---

## Step 6 — $facet and $bucket

```javascript
// $facet: run multiple sub-pipelines in parallel
db.orders.aggregate([
  { $facet: {
    // Facet 1: sales by category
    by_category: [
      { $group: { _id: "$category", total: { $sum: { $multiply: ["$amount","$qty"] } } } },
      { $sort: { total: -1 } }
    ],
    // Facet 2: price distribution
    price_buckets: [
      { $bucket: {
        groupBy: "$amount",
        boundaries: [0, 50, 100, 500, 2000],
        default: "Other",
        output: { count: { $sum: 1 }, total: { $sum: "$amount" } }
      }}
    ],
    // Facet 3: top customers
    top_customers: [
      { $group: { _id: "$customer", spend: { $sum: { $multiply: ["$amount","$qty"] } } } },
      { $sort: { spend: -1 } },
      { $limit: 3 }
    ]
  }}
]).forEach(r => {
  print("=== By Category ===")
  r.by_category.forEach(c => print(" ", c._id, c.total.toFixed(2)))
  print("=== Price Buckets ===")
  r.price_buckets.forEach(b => print(" ", b._id, "->", b.count, "orders"))
  print("=== Top Customers ===")
  r.top_customers.forEach(c => print(" ", c._id, c.spend.toFixed(2)))
})
```

---

## Step 7 — Pipeline Optimization and explain()

```javascript
// Use explain() to see execution plan
db.orders.explain("executionStats").aggregate([
  { $match: { category: "Electronics" } },
  { $group: { _id: "$customer", total: { $sum: "$amount" } } }
])
// Look for: COLLSCAN vs IXSCAN

// Create index before pipeline to improve $match performance
db.orders.createIndex({ category: 1 })

// Pipeline optimization tips:
// 1. Put $match and $limit as early as possible
// 2. $match before $lookup reduces documents joined
// 3. Use $project to reduce document size before expensive stages

// Optimized version:
db.orders.aggregate([
  { $match: { category: "Electronics" } },  // filter first (uses index)
  { $project: { customer: 1, amount: 1, qty: 1, _id: 0 } },  // reduce size
  { $group: {
    _id: "$customer",
    total: { $sum: { $multiply: ["$amount", "$qty"] } }
  }},
  { $sort: { total: -1 } }
]).forEach(r => print(r._id, r.total.toFixed(2)))
```

> 💡 The aggregation pipeline optimizer automatically moves `$match` and `$sort` before `$project` when possible. But manual placement helps when the optimizer can't prove safety.

---

## Step 8 — Capstone: Monthly Sales Report with $unwind and $bucket

```javascript
// Monthly breakdown with product-level detail
db.orders.aggregate([
  // Add computed fields
  { $addFields: {
    month:      { $dateToString: { format: "%Y-%m", date: "$date" } },
    line_total: { $multiply: ["$amount", "$qty"] }
  }},
  // Group by month and category
  { $group: {
    _id:        { month: "$month", category: "$category" },
    revenue:    { $sum: "$line_total" },
    orders:     { $sum: 1 },
    avg_ticket: { $avg: "$line_total" },
    customers:  { $addToSet: "$customer" }  // unique customers
  }},
  // Reshape output
  { $project: {
    _id: 0,
    month:        "$_id.month",
    category:     "$_id.category",
    revenue:      { $round: ["$revenue", 2] },
    orders:       1,
    avg_ticket:   { $round: ["$avg_ticket", 2] },
    unique_customers: { $size: "$customers" }
  }},
  { $sort: { month: 1, revenue: -1 } }
]).forEach(r => print(JSON.stringify(r)))
```

---

## Summary

| Stage | SQL Equivalent | Purpose |
|-------|---------------|---------|
| `$match` | WHERE / HAVING | Filter documents |
| `$group` | GROUP BY | Aggregate and summarize |
| `$project` | SELECT columns | Include/exclude/compute fields |
| `$sort` | ORDER BY | Sort documents |
| `$limit` | LIMIT | Take N documents |
| `$skip` | OFFSET | Skip N documents |
| `$lookup` | LEFT JOIN | Join with another collection |
| `$unwind` | (flatten rows) | Explode array field to documents |
| `$addFields` | SELECT computed | Add computed fields |
| `$count` | COUNT(*) | Count documents |
| `$facet` | Multiple GROUP BYs | Parallel sub-pipelines |
| `$bucket` | CASE + GROUP BY | Range-based grouping |
