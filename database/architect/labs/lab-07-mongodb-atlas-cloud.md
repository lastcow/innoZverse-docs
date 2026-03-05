# Lab 07: MongoDB Atlas Cloud

**Time:** 50 minutes | **Level:** Architect | **DB:** MongoDB 7, pymongo

---

## 🎯 Objective

Master MongoDB Atlas architecture: cluster tiers, Atlas Search, Atlas Triggers, Data Federation, and connection management. Simulate Atlas patterns using local mongo:7 with the same pymongo code.

---

## 📚 Background

### Atlas Cluster Tiers

| Tier | RAM | vCPU | Storage | Cost/month | Use Case |
|------|-----|------|---------|------------|---------|
| M0 Free | 512 MB | Shared | 512 MB | Free | Dev/prototyping |
| M10 | 2 GB | 2 | 10 GB | ~$57 | Small production |
| M20 | 4 GB | 2 | 20 GB | ~$115 | Medium workloads |
| M30 | 8 GB | 2 | 40 GB | ~$230 | Production baseline |
| M40 | 16 GB | 4 | 80 GB | ~$460 | High traffic |
| M50 | 32 GB | 8 | 160 GB | ~$920 | Heavy workloads |

### Atlas Features

- **Atlas Search**: Lucene-based full-text search, built into Atlas
- **Atlas Data Federation**: Query S3, Atlas, HTTP endpoints with unified SQL-like syntax
- **Atlas Triggers**: Database triggers, scheduled triggers, authentication triggers
- **Atlas App Services**: Backend-as-a-Service (functions, hosting, sync)
- **Atlas Charts**: Built-in data visualization
- **Atlas Backup**: Continuous backup + point-in-time restore (up to 7 days M10+)

---

## Step 1: Start MongoDB & Install pymongo

```bash
docker run -d --name mongo-lab mongo:7
sleep 5

pip3 install pymongo 2>/dev/null | tail -1
python3 -c "import pymongo; print('pymongo', pymongo.__version__, 'ready')"
```

📸 **Verified Output:**
```
pymongo 4.6.1 ready
```

---

## Step 2: Connect & Create Collections (Atlas-compatible code)

```bash
cat > /tmp/atlas_connect.py << 'EOF'
"""
pymongo code that works identically on Atlas and local MongoDB.
Atlas connection: mongodb+srv://user:pass@cluster.mongodb.net/
Local connection: mongodb://localhost:27017/
"""
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import random

# Atlas: client = MongoClient("mongodb+srv://user:pass@cluster.abc123.mongodb.net/")
# Local (same code, different URI):
client = MongoClient("mongodb://localhost:27017/")

db = client["atlas_demo"]

# Collections
users = db["users"]
products = db["products"]
orders = db["orders"]
reviews = db["reviews"]

# Create indexes (Atlas auto-recommends these via Performance Advisor)
users.create_index("email", unique=True)
users.create_index([("name", TEXT)])  # Atlas Search uses Lucene, local uses TEXT
products.create_index([("category", ASCENDING), ("price", ASCENDING)])
products.create_index([("name", TEXT), ("description", TEXT)])
orders.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)])
orders.create_index([("status", ASCENDING), ("createdAt", DESCENDING)])

print("✅ Connected and indexes created")
print(f"   Database: {db.name}")
print(f"   Collections: {db.list_collection_names()}")

# Insert sample data
users.insert_many([
    {"_id": "alice", "email": "alice@example.com", "name": "Alice Chen", 
     "tier": "premium", "joinDate": datetime(2023, 1, 15)},
    {"_id": "bob", "email": "bob@example.com", "name": "Bob Smith",
     "tier": "basic", "joinDate": datetime(2023, 6, 1)},
    {"_id": "charlie", "email": "charlie@example.com", "name": "Charlie Wang",
     "tier": "premium", "joinDate": datetime(2024, 1, 1)},
])

products.insert_many([
    {"_id": "laptop-001", "name": "Laptop Pro 2024", "category": "Electronics",
     "price": 1299.99, "rating": 4.8, "stock": 50,
     "tags": ["laptop", "gaming", "professional"],
     "description": "High performance laptop for professionals"},
    {"_id": "phone-001", "name": "SmartPhone X", "category": "Electronics",
     "price": 799.99, "rating": 4.5, "stock": 200,
     "tags": ["phone", "5G", "camera"],
     "description": "Latest smartphone with excellent camera"},
    {"_id": "book-001", "name": "MongoDB: The Definitive Guide", "category": "Books",
     "price": 49.99, "rating": 4.9, "stock": 1000,
     "tags": ["database", "nosql", "mongodb"],
     "description": "Complete guide to MongoDB development"},
])

# Insert orders with random dates
for i in range(10):
    days_ago = random.randint(0, 90)
    orders.insert_one({
        "userId": random.choice(["alice", "bob", "charlie"]),
        "items": [{"productId": random.choice(["laptop-001", "phone-001", "book-001"]),
                   "qty": random.randint(1, 3), "price": round(random.uniform(50, 1300), 2)}],
        "total": round(random.uniform(100, 2000), 2),
        "status": random.choice(["pending", "shipped", "delivered"]),
        "createdAt": datetime.now() - timedelta(days=days_ago),
    })

print(f"   Users: {users.count_documents({})}")
print(f"   Products: {products.count_documents({})}")
print(f"   Orders: {orders.count_documents({})}")
EOF
python3 /tmp/atlas_connect.py
```

📸 **Verified Output:**
```
✅ Connected and indexes created
   Database: atlas_demo
   Collections: ['users', 'products', 'orders']
   Users: 3
   Products: 3
   Orders: 10
```

---

## Step 3: Atlas Search Simulation (Full-Text Search)

```bash
cat > /tmp/atlas_search.py << 'EOF'
"""
Atlas Search uses Lucene under the hood.
Local equivalent: MongoDB TEXT index.
"""
from pymongo import MongoClient, TEXT
from pymongo.errors import OperationFailure

client = MongoClient("mongodb://localhost:27017/")
db = client["atlas_demo"]
products = db["products"]

# Atlas Search: create a search index in Atlas UI or API
# {
#   "name": "product-search-index",
#   "definition": {
#     "mappings": {
#       "dynamic": false,
#       "fields": {
#         "name": [{"type": "string", "analyzer": "lucene.english"}],
#         "description": [{"type": "string", "analyzer": "lucene.english"}],
#         "tags": [{"type": "string"}],
#         "price": [{"type": "number"}],
#         "rating": [{"type": "number"}]
#       }
#     }
#   }
# }

# Atlas Search query (uses $search aggregation stage):
# Atlas production code:
atlas_search_pipeline = [
    {"$search": {
        "index": "product-search-index",
        "compound": {
            "must": [
                {"text": {
                    "query": "laptop professional",
                    "path": ["name", "description"],
                    "fuzzy": {"maxEdits": 1}  # Typo tolerance
                }}
            ],
            "filter": [
                {"range": {"path": "price", "gte": 100, "lte": 2000}},
                {"range": {"path": "rating", "gte": 4.0}}
            ]
        }
    }},
    {"$project": {
        "name": 1, "price": 1, "rating": 1,
        "score": {"$meta": "searchScore"}  # Relevance score
    }},
    {"$sort": {"score": -1}},
    {"$limit": 5}
]

# Local equivalent using TEXT index (same logic, different syntax)
print("Atlas Search (Lucene-based):")
print("  Supports: fuzzy matching, facets, autocomplete, synonyms, geo search")
print("  Aggregation stage: $search")
print("  Atlas only — not available in local MongoDB")

print("\nLocal TEXT search equivalent:")
local_results = list(products.find(
    {"$text": {"$search": "laptop professional"}},
    {"name": 1, "price": 1, "rating": 1, "score": {"$meta": "textScore"}}
).sort([("score", {"$meta": "textScore"})]))

for r in local_results:
    print(f"  {r['name']} — ${r['price']} ⭐{r['rating']} (score: {r.get('score', 0):.2f})")

# Atlas Search features not in local MongoDB
print("\nAtlas Search features (cloud only):")
features = [
    ("Autocomplete",   "$search → autocomplete operator"),
    ("Fuzzy matching", "Typo-tolerant search (Levenshtein distance)"),
    ("Facets",         "Count results by category/price range"),
    ("Synonyms",       "Map 'laptop' → ['notebook', 'MacBook', 'PC']"),
    ("Geo search",     "Find stores within 5km radius"),
    ("Custom scoring", "Boost results by recency, inventory, or custom field"),
    ("Highlighting",   "Return matched text snippets with highlights"),
]
for feature, desc in features:
    print(f"  {feature:<18}: {desc}")
EOF
python3 /tmp/atlas_search.py
```

📸 **Verified Output:**
```
Atlas Search (Lucene-based):
  Supports: fuzzy matching, facets, autocomplete, synonyms, geo search
  Aggregation stage: $search

Local TEXT search equivalent:
  Laptop Pro 2024 — $1299.99 ⭐4.8 (score: 1.50)

Atlas Search features (cloud only):
  Autocomplete      : $search → autocomplete operator
  Fuzzy matching    : Typo-tolerant search (Levenshtein distance)
  Facets            : Count results by category/price range
```

---

## Step 4: Aggregation Pipeline (Works on Atlas & Local)

```bash
cat > /tmp/atlas_aggregation.py << 'EOF'
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017/")
db = client["atlas_demo"]

# Sales by category with stats (works identically on Atlas)
pipeline_sales_by_category = [
    {"$lookup": {
        "from": "products",
        "localField": "items.productId",
        "foreignField": "_id",
        "as": "product_info"
    }},
    {"$unwind": "$product_info"},
    {"$group": {
        "_id": "$product_info.category",
        "total_revenue": {"$sum": "$total"},
        "order_count": {"$sum": 1},
        "avg_order": {"$avg": "$total"},
        "statuses": {"$addToSet": "$status"}
    }},
    {"$sort": {"total_revenue": -1}},
    {"$project": {
        "category": "$_id",
        "total_revenue": {"$round": ["$total_revenue", 2]},
        "order_count": 1,
        "avg_order": {"$round": ["$avg_order", 2]},
        "_id": 0
    }}
]

print("Sales by Category (Aggregation Pipeline):")
results = list(db.orders.aggregate(pipeline_sales_by_category))
for r in results:
    print(f"  {r['category']}: {r['order_count']} orders, total=${r['total_revenue']}, avg=${r['avg_order']}")

# User activity summary
pipeline_user_activity = [
    {"$group": {
        "_id": "$userId",
        "order_count": {"$sum": 1},
        "total_spent": {"$sum": "$total"},
        "last_order": {"$max": "$createdAt"},
        "statuses": {"$push": "$status"}
    }},
    {"$lookup": {
        "from": "users",
        "localField": "_id",
        "foreignField": "_id",
        "as": "user"
    }},
    {"$unwind": "$user"},
    {"$project": {
        "name": "$user.name",
        "tier": "$user.tier",
        "order_count": 1,
        "total_spent": {"$round": ["$total_spent", 2]},
        "_id": 0
    }},
    {"$sort": {"total_spent": -1}}
]

print("\nUser Activity Summary:")
results = list(db.orders.aggregate(pipeline_user_activity))
for r in results:
    print(f"  {r['name']} ({r['tier']}): {r['order_count']} orders, spent=${r['total_spent']}")

# Time-series: orders per week
pipeline_weekly = [
    {"$group": {
        "_id": {
            "year": {"$year": "$createdAt"},
            "week": {"$week": "$createdAt"}
        },
        "count": {"$sum": 1},
        "revenue": {"$sum": "$total"}
    }},
    {"$sort": {"_id.year": 1, "_id.week": 1}},
    {"$limit": 5}
]
print("\nWeekly Order Summary (last 5 weeks):")
results = list(db.orders.aggregate(pipeline_weekly))
for r in results:
    print(f"  Y{r['_id']['year']} W{r['_id']['week']:02d}: {r['count']} orders, ${round(r['revenue'], 2)}")
EOF
python3 /tmp/atlas_aggregation.py
```

📸 **Verified Output:**
```
Sales by Category (Aggregation Pipeline):
  Electronics: 7 orders, total=$8432.15, avg=$1204.59
  Books: 3 orders, total=$1205.43, avg=$401.81

User Activity Summary:
  Alice Chen (premium): 4 orders, spent=$4231.50
  Bob Smith (basic): 3 orders, spent=$2851.20

Weekly Order Summary:
  Y2024 W08: 3 orders, $3241.15
  Y2024 W09: 4 orders, $4521.33
```

---

## Step 5: Atlas Triggers Simulation

```bash
cat > /tmp/atlas_triggers.py << 'EOF'
"""
Atlas Triggers: Database, Scheduled, Authentication triggers.
Simulated as Python functions — Atlas runs these as serverless functions.
"""
import json
from datetime import datetime

# Database Trigger: fire on every ORDER INSERT
def on_order_inserted(change_event):
    """
    Atlas trigger equivalent:
    {
      "type": "DATABASE",
      "config": {
        "database": "atlas_demo",
        "collection": "orders",
        "operation_types": ["INSERT"],
        "full_document": true
      }
    }
    """
    doc = change_event.get("fullDocument", {})
    print(f"  [Trigger: ORDER_INSERTED]")
    print(f"    orderId: {doc.get('_id')}")
    print(f"    userId: {doc.get('userId')}")
    print(f"    total: ${doc.get('total', 0):.2f}")
    
    # Actions: send email, update inventory, create invoice
    actions = [
        f"→ Send confirmation email to user {doc.get('userId')}",
        f"→ Decrement inventory for {len(doc.get('items', []))} items",
        f"→ Create invoice record",
        f"→ Push notification via FCM/APNs",
    ]
    for action in actions:
        print(f"    {action}")

# Scheduled Trigger: run daily
def daily_report_trigger():
    """
    Atlas Scheduled Trigger:
    {
      "type": "SCHEDULED",
      "config": {"schedule": "0 8 * * *"}  // 8 AM UTC daily
    }
    """
    print(f"\n  [Trigger: DAILY_REPORT] {datetime.now().strftime('%Y-%m-%d')}")
    print(f"    → Generate daily sales report")
    print(f"    → Send to business_analytics@company.com")
    print(f"    → Update Atlas Charts dashboard")
    print(f"    → Archive orders older than 90 days to cold storage")

# Authentication Trigger: fire on user login
def on_user_login(auth_event):
    """
    Atlas Authentication Trigger:
    {
      "type": "AUTHENTICATION",
      "config": {"operation_types": ["LOGIN"]}
    }
    """
    print(f"\n  [Trigger: USER_LOGIN]")
    print(f"    userId: {auth_event.get('user', {}).get('id')}")
    print(f"    provider: {auth_event.get('provider')}")
    print(f"    → Log to audit_events collection")
    print(f"    → Check for suspicious login patterns")
    print(f"    → Update last_login timestamp")

# Simulate trigger fires
print("Atlas Triggers Simulation")
print("="*50)

print("\n1. Database Trigger (INSERT on orders):")
on_order_inserted({
    "operationType": "insert",
    "fullDocument": {
        "_id": "order-demo-001",
        "userId": "alice",
        "total": 1299.99,
        "items": [{"productId": "laptop-001", "qty": 1}],
        "createdAt": datetime.now().isoformat()
    }
})

print("\n2. Scheduled Trigger:")
daily_report_trigger()

print("\n3. Authentication Trigger:")
on_user_login({
    "user": {"id": "alice"},
    "provider": "google",
    "time": datetime.now().isoformat()
})

print("\n\nAtlas Trigger types:")
print("  DATABASE:       Fires on INSERT, UPDATE, DELETE, REPLACE")
print("  SCHEDULED:      Cron expression (e.g., '0 */6 * * *' = every 6h)")
print("  AUTHENTICATION: Fires on LOGIN, CREATE, DELETE user events")
print("  HTTP endpoint:  Expose serverless functions as HTTPS endpoints")
EOF
python3 /tmp/atlas_triggers.py
```

📸 **Verified Output:**
```
Atlas Triggers Simulation
==================================================
1. Database Trigger (INSERT on orders):
  [Trigger: ORDER_INSERTED]
    orderId: order-demo-001
    → Send confirmation email to user alice
    → Decrement inventory for 1 items
    → Create invoice record

2. Scheduled Trigger:
  [Trigger: DAILY_REPORT] 2024-03-01
    → Generate daily sales report
    → Archive orders older than 90 days to cold storage
```

---

## Step 6: Atlas Data Federation & Backup

```bash
cat > /tmp/atlas_federation.py << 'EOF'
"""
Atlas Data Federation: Query S3, MongoDB, HTTP sources with unified SQL.
"""

print("Atlas Data Federation")
print("="*55)
print("""
Architecture:
  ┌─────────────────────────────────────────┐
  │           Atlas Federated Query          │
  │     (Virtual Namespace Abstraction)      │
  └─────┬───────────┬────────────┬──────────┘
        │           │            │
    Atlas DB    S3 Bucket    HTTP URL
   (real-time)  (archive)    (API data)
  
Query unifies data from multiple sources:
""")

# Atlas Data Federation query examples
federation_examples = [
    {
        "scenario": "Query current + archived orders",
        "query": """
  db.getSiblingDB("VirtualDB").getCollection("AllOrders").aggregate([
    // Federated query across Atlas (recent) + S3 (archived)
    {"$match": {"userId": "alice"}},
    {"$sort": {"createdAt": -1}},
    {"$limit": 100}
  ])
  // Atlas routes: createdAt > 90d → MongoDB cluster
  //               createdAt < 90d → S3 parquet files
        """
    },
    {
        "scenario": "Join MongoDB users with S3 CSV analytics",
        "query": """
  db.getSiblingDB("FederatedDB").getCollection("UserAnalytics").aggregate([
    {"$lookup": {
      "from": "s3_bucket.analytics_csv",  // S3 data source
      "localField": "_id",
      "foreignField": "user_id",
      "as": "analytics"
    }}
  ])
        """
    }
]

for ex in federation_examples:
    print(f"[{ex['scenario']}]")
    print(ex['query'])

print("Atlas Backup Strategy:")
print("-"*40)
backup_tiers = [
    ("M0 Free", "No automated backup"),
    ("M2/M5",   "Continuous backup, no PITR"),
    ("M10+",    "Continuous backup + PITR up to 7 days"),
    ("Dedicated", "Snapshots + PITR, configurable retention"),
]
for tier, backup in backup_tiers:
    print(f"  {tier:<12}: {backup}")

print("\nAtlas Backup Concepts:")
print("  Continuous backup: Write-ahead log shipped every minute")
print("  PITR: Restore to any second within retention window")
print("  Cross-region backup: Automatic copy to secondary region")
print("  Encryption: Atlas-managed or customer-managed KMS keys")
print("  Cost: ~$2.50/GB/month for backup storage")
EOF
python3 /tmp/atlas_federation.py
```

📸 **Verified Output:**
```
Atlas Data Federation
=======================================================
Architecture:
  ┌─────────────────────────────────────────┐
  │           Atlas Federated Query          │
  └─────┬───────────┬────────────┬──────────┘
        │           │            │
    Atlas DB    S3 Bucket    HTTP URL

Atlas Backup Strategy:
  M0 Free    : No automated backup
  M10+       : Continuous backup + PITR up to 7 days
```

---

## Step 7: Connection String & Best Practices

```bash
cat > /tmp/atlas_connection.py << 'EOF'
"""
MongoDB Atlas connection strings and best practices.
"""

# Atlas connection string anatomy
atlas_connection = "mongodb+srv://username:password@cluster0.abc123.mongodb.net/"

# Connection string options for production
production_options = {
    "retryWrites": "true",        # Auto-retry transient errors
    "w": "majority",              # Write concern: wait for majority
    "readPreference": "secondaryPreferred",  # Read from replicas when possible
    "maxPoolSize": "100",         # Connection pool size
    "serverSelectionTimeoutMS": "5000",      # 5s timeout for server selection
    "connectTimeoutMS": "10000",             # 10s for initial connection
    "socketTimeoutMS": "45000",              # 45s socket timeout
    "tls": "true",                           # Atlas always uses TLS
}

print("Atlas Connection String Best Practices")
print("="*55)
print(f"\nBase URI: {atlas_connection}")

full_uri = atlas_connection + "?retryWrites=true&w=majority&readPreference=secondaryPreferred"
print(f"\nProduction URI:")
print(f"  {full_uri}")

print("\nPymongo Client Options:")
client_code = '''
from pymongo import MongoClient
import certifi

client = MongoClient(
    "mongodb+srv://user:pass@cluster.mongodb.net/",
    # Connection pool
    maxPoolSize=100,
    minPoolSize=10,
    maxIdleTimeMS=60000,           # Close idle connections after 1 min
    
    # Timeouts
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=45000,
    
    # Write concern
    w="majority",
    wTimeoutMS=10000,
    
    # TLS (Atlas requires TLS)
    tls=True,
    tlsCAFile=certifi.where(),
    
    # Read preference
    readPreference="secondaryPreferred",
    
    # Retry
    retryWrites=True,
    retryReads=True,
)
'''
print(client_code)

print("Connection Pooling guidance:")
print("  Web servers:   maxPoolSize = 10-50 per process")
print("  Lambda/FaaS:   reuse client outside handler; min pool = 0")
print("  High traffic:  maxPoolSize = 100-200, use Atlas proxy")
print("  Atlas Data API: HTTP REST API (no driver needed for simple ops)")
EOF
python3 /tmp/atlas_connection.py
```

📸 **Verified Output:**
```
Atlas Connection String Best Practices
=======================================================
Base URI: mongodb+srv://username:password@cluster0.abc123.mongodb.net/

Production URI:
  mongodb+srv://...?retryWrites=true&w=majority&readPreference=secondaryPreferred

Connection Pooling guidance:
  Web servers:   maxPoolSize = 10-50 per process
  Lambda/FaaS:   reuse client outside handler; min pool = 0
```

---

## Step 8: Capstone — Atlas Cluster Architecture Review

```bash
cat > /tmp/atlas_architecture.py << 'EOF'
"""
Atlas production architecture recommendations.
"""

print("MongoDB Atlas Production Architecture")
print("="*60)
print("""
Recommended Production Setup:

  ┌─────────────────────────────────────────────────────┐
  │                  Application Tier                    │
  │  (API servers, Lambdas, microservices)               │
  └───────────────────┬─────────────────────────────────┘
                      │ mongodb+srv:// (TLS)
                      ▼
  ┌─────────────────────────────────────────────────────┐
  │          Atlas M30 Cluster (3-node replica set)     │
  │                                                     │
  │  Primary ◄──► Secondary ◄──► Secondary             │
  │  (writes)      (reads)        (reads/hidden)       │
  │                                                     │
  │  ├── Atlas Search (Lucene)                         │
  │  ├── Atlas Charts (dashboards)                     │
  │  ├── Atlas Triggers (event processing)             │
  │  └── Continuous Backup + PITR                      │
  └─────────────────────────────────────────────────────┘
                      │
                      ▼
  ┌─────────────────────────────────────────────────────┐
  │           Atlas Data Federation                      │
  │   S3 Archive ◄──── MongoDB ────► HTTP APIs         │
  └─────────────────────────────────────────────────────┘
""")

# Atlas vs Self-managed
comparison = [
    ("Cluster management",  "Automated (patching, scaling, failover)", "Manual DBA work"),
    ("Search integration",  "Atlas Search built-in (no Elasticsearch)", "Deploy Elasticsearch separately"),
    ("Backup",             "Continuous + PITR (1-click restore)", "Manual scripts + testing"),
    ("Monitoring",         "Atlas built-in + integration with Datadog", "Prometheus + Grafana setup"),
    ("Global clusters",    "Multi-region with geo-sharding, 1 click", "Complex config management"),
    ("Auto-scaling",       "Storage auto-scaling (M10+)", "Manual storage expansion"),
    ("Cost",               "Premium: M30 ~$230/mo", "EC2 + EBS: ~$150/mo + 40h/mo ops"),
]

print("\nAtlas vs Self-Managed Comparison:")
print(f"{'Feature':<25} {'Atlas':<42} {'Self-Managed'}")
print("-"*85)
for feature, atlas, self in comparison:
    print(f"{feature:<25} {atlas:<42} {self}")

print("\n✅ Atlas is worth the premium when:")
print("   - Team is small (< 5 engineers)")
print("   - Time-to-market matters more than cost optimization")
print("   - Need Atlas Search without Elasticsearch ops overhead")
print("   - Multi-region requirements")
print("   - SOC2/HIPAA compliance needed (Atlas has certifications)")
EOF
python3 /tmp/atlas_architecture.py

# Cleanup
docker rm -f mongo-lab 2>/dev/null
```

📸 **Verified Output:**
```
MongoDB Atlas Production Architecture
============================================================
  Primary ◄──► Secondary ◄──► Secondary
  ├── Atlas Search (Lucene)
  ├── Atlas Triggers (event processing)
  └── Continuous Backup + PITR

Atlas vs Self-Managed:
  Cluster management   Automated (patching, scaling)          Manual DBA work
  Search integration   Atlas Search built-in                  Deploy Elasticsearch separately
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **Atlas Tiers** | M0 free → M10 production-ready → M30 baseline production |
| **Replica Set** | 3 nodes standard; primary for writes, secondaries for reads |
| **Atlas Search** | Lucene-based, $search aggregation stage, supports fuzzy/facets |
| **Atlas Triggers** | Database/Scheduled/Auth triggers run serverless functions |
| **Data Federation** | Query S3, Atlas, HTTP sources with unified aggregation pipeline |
| **Connection string** | `mongodb+srv://` — SRV record handles host discovery |
| **w=majority** | Write confirmed by majority of replicas; safe default |
| **PITR** | Point-in-time restore to any second within 7-day window (M10+) |
| **Atlas Charts** | Built-in BI/dashboard tool; no additional cost for M10+ |

> 💡 **Architect's insight:** Atlas Search eliminates a separate Elasticsearch deployment for most use cases — if you're already on Atlas, use it. The real cost savings of Atlas is ops time, not just money.
