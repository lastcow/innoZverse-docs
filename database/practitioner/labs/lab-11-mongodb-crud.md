# Lab 11: MongoDB CRUD Operations

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MongoDB 7

MongoDB stores data as BSON documents (like JSON) in collections. Unlike SQL rows, documents are schema-flexible — each can have different fields. This lab covers all CRUD operations with `mongosh`.

---

## Step 1 — Setup: Connect and Create Collection

```bash
# Start MongoDB
docker run -d --name mongo-lab mongo:7
sleep 5
docker exec -it mongo-lab mongosh
```

```javascript
// Select (or create) a database
use shopdb

// MongoDB creates the database and collection
// on first insert — no CREATE TABLE needed
db.products.drop()  // clean start if re-running
```

> 💡 MongoDB databases and collections are created lazily — they don't exist until you insert a document. `use shopdb` just sets the current database context.

---

## Step 2 — insertOne and insertMany

```javascript
// insertOne: single document
let r1 = db.products.insertOne({
  name:     "Laptop Pro",
  category: "Electronics",
  price:    1299.99,
  stock:    50,
  tags:     ["laptop", "portable", "premium"],
  specs:    { ram: "16GB", storage: "512GB SSD", weight: "1.4kg" },
  isActive: true
})
print("Inserted ID:", r1.insertedId)
```

```javascript
// insertMany: batch insert
let r2 = db.products.insertMany([
  { name: "Wireless Mouse",    category: "Electronics", price: 29.99,  stock: 200, tags: ["mouse","wireless"] },
  { name: "Mechanical Keyboard", category: "Electronics", price: 89.99, stock: 150, tags: ["keyboard","mechanical"] },
  { name: "Running Shoes",     category: "Sports",      price: 79.99,  stock: 100, tags: ["shoes","running"] },
  { name: "Python Book",       category: "Books",       price: 39.99,  stock: 75,  tags: ["python","programming"] },
  { name: "Coffee Maker",      category: "Kitchen",     price: 49.99,  stock: 80,  tags: ["coffee","appliance"] }
])
print("Inserted:", r2.insertedCount, "documents")
print("Total:", db.products.countDocuments())
```

📸 **Verified Output:**
```
Inserted ID: ObjectId('69a9a7605a5ce2c1708563b1')
Inserted: 5 documents
Total: 6
```

---

## Step 3 — findOne and find with Filters

```javascript
// findOne: returns first matching document
let laptop = db.products.findOne({ name: "Laptop Pro" })
print("Found:", laptop.name, "- $" + laptop.price)
print("Specs:", JSON.stringify(laptop.specs))

// find: returns cursor of all matches
// Equality filter
db.products.find({ category: "Electronics" }).forEach(p =>
  print(p.name, "$" + p.price)
)
```

📸 **Verified Output:**
```
Found: Laptop Pro - $1299.99
Specs: {"ram":"16GB","storage":"512GB SSD","weight":"1.4kg"}
Laptop Pro $1299.99
Wireless Mouse $29.99
Mechanical Keyboard $89.99
```

---

## Step 4 — Comparison and Logical Operators

```javascript
// Comparison operators
db.products.find({ price: { $lt: 50 } })
  .forEach(p => print(p.name, "$" + p.price))

db.products.find({ price: { $gte: 40, $lte: 100 } })
  .forEach(p => print(p.name, "$" + p.price))

// $in: match any value in array
db.products.find({ category: { $in: ["Electronics", "Books"] } })
  .forEach(p => print(p.name, p.category))

// $and: explicit AND (default is implicit AND)
db.products.find({
  $and: [
    { category: "Electronics" },
    { price: { $lt: 100 } }
  ]
}).forEach(p => print(p.name, "$" + p.price))

// $or: at least one condition
db.products.find({
  $or: [
    { price: { $lt: 35 } },
    { category: "Sports" }
  ]
}).forEach(p => print(p.name, "$" + p.price))

// $not: negate
db.products.find({ price: { $not: { $gt: 100 } } })
  .forEach(p => print(p.name, "$" + p.price))
```

📸 **Verified Output (price < 50):**
```
Wireless Mouse $29.99
Python Book $39.99
Coffee Maker $49.99
```

> 💡 MongoDB field names are case-sensitive. `{ Name: "Laptop" }` will NOT match a document with `{ name: "Laptop" }`.

---

## Step 5 — Projection, Sort, Skip, Limit

```javascript
// Projection: 1 = include, 0 = exclude
// _id is included by default; set to 0 to exclude
db.products.find(
  { category: "Electronics" },
  { name: 1, price: 1, _id: 0 }  // include name, price; exclude _id
).forEach(p => print(p.name, "$" + p.price))

// Sort: 1 = ascending, -1 = descending
db.products.find()
  .sort({ price: -1 })  // highest price first
  .limit(3)
  .forEach(p => print(p.name, "$" + p.price))

// Pagination
let page = 2, pageSize = 2
db.products.find()
  .sort({ price: 1 })
  .skip((page - 1) * pageSize)
  .limit(pageSize)
  .forEach(p => print(p.name, "$" + p.price))
```

---

## Step 6 — updateOne and updateMany

```javascript
// $set: set field values
db.products.updateOne(
  { name: "Wireless Mouse" },
  { $set: { price: 34.99, "specs.color": "black" } }
)
let mouse = db.products.findOne({ name: "Wireless Mouse" })
print("Updated Mouse price:", mouse.price, "color:", mouse.specs?.color)

// $inc: increment numeric field
db.products.updateOne(
  { name: "Wireless Mouse" },
  { $inc: { stock: -10 } }  // sold 10
)
print("Stock after sale:", db.products.findOne({ name: "Wireless Mouse" }).stock)

// $push: append to array
db.products.updateMany(
  { category: "Electronics" },
  { $push: { tags: "sale" } }
)
print("Electronics with sale tag:", db.products.countDocuments({ tags: "sale" }))

// $pull: remove from array
db.products.updateOne(
  { name: "Laptop Pro" },
  { $pull: { tags: "sale" } }
)

// $unset: remove a field
db.products.updateOne(
  { name: "Coffee Maker" },
  { $unset: { specs: "" } }
)
```

📸 **Verified Output:**
```
Updated Mouse price: 34.99 color: black
Stock after sale: 190
Electronics with sale tag: 3
```

---

## Step 7 — deleteOne, deleteMany, and findOneAndUpdate

```javascript
// deleteOne: remove first matching document
let del = db.products.deleteOne({ name: "Coffee Maker" })
print("Deleted:", del.deletedCount, "document")
print("Remaining:", db.products.countDocuments())

// deleteMany: remove all matching
db.products.deleteMany({ stock: { $lt: 50 } })

// findOneAndUpdate: atomic read-modify (returns document)
let updated = db.products.findOneAndUpdate(
  { name: "Wireless Mouse" },
  { $set: { price: 24.99 }, $inc: { stock: 50 } },
  { returnDocument: "after" }  // "before" returns original
)
print("Updated doc:", updated.name, "price:", updated.price, "stock:", updated.stock)

// findOneAndDelete: atomic read-delete
let deleted = db.products.findOneAndDelete({ name: "Python Book" })
print("Deleted doc:", deleted?.name)

// upsert: insert if not found, update if found
db.products.updateOne(
  { name: "New Product" },
  { $set: { category: "Test", price: 9.99, stock: 10 } },
  { upsert: true }
)
print("After upsert:", db.products.countDocuments({ name: "New Product" }))
```

---

## Step 8 — Capstone: Product Catalog CRUD Application

```javascript
// Complete CRUD workflow for a product catalog

use ecommerce

// 1. Create initial catalog
db.catalog.insertMany([
  { sku: "ELEC-001", name: "Smart TV 55\"",    category: "Electronics", price: 799.99, stock: 30, ratings: [] },
  { sku: "ELEC-002", name: "Bluetooth Speaker", category: "Electronics", price: 59.99,  stock: 120, ratings: [] },
  { sku: "CLTH-001", name: "Winter Jacket",      category: "Clothing",    price: 129.99, stock: 45, ratings: [] }
])

// 2. Customer rates a product
db.catalog.updateOne(
  { sku: "ELEC-001" },
  {
    $push: { ratings: { userId: "user:123", score: 4.5, comment: "Great picture quality!" } },
    $inc: { ratingCount: 1 }
  }
)

// 3. Compute average rating (without aggregation)
let tv = db.catalog.findOne({ sku: "ELEC-001" })
let avgRating = tv.ratings.reduce((sum, r) => sum + r.score, 0) / tv.ratings.length
print("Avg rating:", avgRating)

// 4. Bulk price update for a sale
let saleResult = db.catalog.updateMany(
  { category: "Electronics", price: { $lte: 100 } },
  { $mul: { price: 0.9 } }  // $mul: multiply field value
)
print("Items discounted:", saleResult.modifiedCount)

// 5. Low stock alert
db.catalog.find({ stock: { $lt: 40 } })
  .forEach(p => print("LOW STOCK:", p.name, "- only", p.stock, "left"))

// 6. Verify final state
db.catalog.find({}, { sku: 1, name: 1, price: 1, stock: 1, _id: 0 })
  .sort({ price: -1 })
  .forEach(p => print(p.sku, p.name, "$" + p.price.toFixed(2), "stock:", p.stock))
```

---

## Summary

| Operation | Command | Filter Example |
|-----------|---------|----------------|
| Insert one | `insertOne({...})` | — |
| Insert many | `insertMany([...])` | — |
| Find one | `findOne({field: val})` | `{ price: { $lt: 50 } }` |
| Find many | `find({}).sort().limit()` | `{ $or: [{a:1},{b:2}] }` |
| Update one | `updateOne(filter, {$set:{}})` | Uses `$set`, `$inc`, `$push` |
| Update many | `updateMany(filter, update)` | Same operators |
| Delete one | `deleteOne(filter)` | Any filter |
| Delete many | `deleteMany(filter)` | Any filter |
| Atomic update | `findOneAndUpdate(f, u, opts)` | `returnDocument: "after"` |
| Upsert | `updateOne(f, u, {upsert:true})` | Inserts if not found |
