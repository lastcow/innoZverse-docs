# MongoDB

MongoDB is a document-oriented NoSQL database that stores data as JSON-like documents.

## Core Concepts

- **Database** → Database
- **Collection** → Table
- **Document** → Row
- **Field** → Column

## CRUD Operations

```javascript
// Connect
mongosh "mongodb://localhost:27017/innozverse"

// Insert
db.products.insertOne({
    name: "Surface Pro 12",
    category: "laptop",
    price: 999.99,
    specs: { ram: "16GB", storage: "512GB", cpu: "Snapdragon X" },
    tags: ["surface", "microsoft", "laptop"],
    stock: 50
})

db.products.insertMany([{...}, {...}])

// Find
db.products.find()
db.products.find({ category: "laptop" })
db.products.find({ price: { $gt: 500, $lt: 2000 } })
db.products.find({ tags: "surface" })
db.products.find({ "specs.ram": "16GB" })
db.products.findOne({ _id: ObjectId("...") })

// Projection (select specific fields)
db.products.find({}, { name: 1, price: 1, _id: 0 })

// Update
db.products.updateOne(
    { name: "Surface Pro 12" },
    { $set: { price: 899.99 }, $inc: { stock: -1 } }
)
db.products.updateMany(
    { category: "laptop" },
    { $set: { onSale: true } }
)

// Delete
db.products.deleteOne({ _id: ObjectId("...") })
db.products.deleteMany({ stock: 0 })

// Sort, limit, skip
db.products.find().sort({ price: -1 }).limit(10).skip(20)
```

## Aggregation Pipeline

```javascript
db.orders.aggregate([
    // Stage 1: Filter
    { $match: { status: "completed", createdAt: { $gte: new Date("2026-01-01") } } },

    // Stage 2: Join with products
    { $lookup: {
        from: "products",
        localField: "productId",
        foreignField: "_id",
        as: "product"
    }},

    // Stage 3: Unwind array
    { $unwind: "$product" },

    // Stage 4: Group and sum
    { $group: {
        _id: "$product.category",
        totalRevenue: { $sum: { $multiply: ["$quantity", "$product.price"] } },
        orderCount: { $sum: 1 }
    }},

    // Stage 5: Sort
    { $sort: { totalRevenue: -1 } }
])
```

## Indexes in MongoDB

```javascript
db.products.createIndex({ name: 1 })                    // Ascending
db.products.createIndex({ name: 1, category: -1 })     // Compound
db.products.createIndex({ name: "text", description: "text" })  // Text search
db.products.getIndexes()
```
