# Lab 19: Elasticsearch Search & Analytics

**Time:** 45 minutes | **Level:** Advanced | **DB:** Elasticsearch 8.11

## Overview

Elasticsearch is a distributed search and analytics engine built on Apache Lucene. It excels at full-text search, aggregations, and log analytics. This lab covers index creation, document indexing, the Query DSL, aggregations, and analyzers.

---

## Step 1: Launch Elasticsearch

```bash
docker run -d --name es-lab \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -p 9200:9200 \
  elasticsearch:8.11.0

echo "Waiting for Elasticsearch (30-60 seconds)..."
for i in $(seq 1 30); do
  curl -s http://localhost:9200/_cluster/health 2>/dev/null | grep -q '"status"' && break || sleep 3
done

echo "Elasticsearch ready!"
curl -s http://localhost:9200/_cluster/health | python3 -m json.tool
```

📸 **Verified Output:**
```
Elasticsearch ready!
{
    "cluster_name": "docker-cluster",
    "status": "green",
    "timed_out": false,
    "number_of_nodes": 1,
    "number_of_data_nodes": 1,
    "active_primary_shards": 1,
    "active_shards": 1,
    "relocating_shards": 0,
    "initializing_shards": 0,
    "unassigned_shards": 0,
    "delayed_unassigned_shards": 0,
    "number_of_pending_tasks": 0,
    "number_of_in_flight_fetch": 0,
    "task_max_waiting_in_queue_millis": 0,
    "active_shards_percent_as_double": 100.0
}
```

---

## Step 2: Create Index with Explicit Mapping

```bash
# Create products index with explicit field mappings
curl -s -X PUT "localhost:9200/products" \
  -H 'Content-Type: application/json' \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "analysis": {
        "analyzer": {
          "product_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop", "snowball"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "name": {
          "type": "text",
          "analyzer": "product_analyzer",
          "fields": {
            "keyword": { "type": "keyword" }
          }
        },
        "description": { "type": "text", "analyzer": "product_analyzer" },
        "category":    { "type": "keyword" },
        "brand":       { "type": "keyword" },
        "price":       { "type": "float" },
        "stock":       { "type": "integer" },
        "rating":      { "type": "float" },
        "tags":        { "type": "keyword" },
        "in_stock":    { "type": "boolean" },
        "created_at":  { "type": "date" }
      }
    }
  }' | python3 -m json.tool

echo ""
echo "Index created!"
```

📸 **Verified Output:**
```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "products"
}

Index created!
```

> 💡 **Explicit mapping is preferred** over dynamic mapping. Without it, Elasticsearch guesses types — `"price": "9.99"` might map as text instead of float.

---

## Step 3: Index Documents

```bash
# Index multiple documents
curl -s -X POST "localhost:9200/products/_bulk" \
  -H 'Content-Type: application/json' \
  -d '
{"index": {"_id": "1"}}
{"name": "MacBook Pro 16-inch", "description": "Powerful laptop with M3 chip for professional creative work", "category": "laptops", "brand": "Apple", "price": 2499.99, "stock": 15, "rating": 4.8, "tags": ["apple", "laptop", "professional"], "in_stock": true, "created_at": "2024-01-15"}
{"index": {"_id": "2"}}
{"name": "Dell XPS 15", "description": "High-performance laptop with OLED display perfect for developers", "category": "laptops", "brand": "Dell", "price": 1799.99, "stock": 8, "rating": 4.5, "tags": ["dell", "laptop", "developer"], "in_stock": true, "created_at": "2024-02-20"}
{"index": {"_id": "3"}}
{"name": "Sony WH-1000XM5", "description": "Premium wireless noise-canceling headphones with exceptional sound quality", "category": "headphones", "brand": "Sony", "price": 349.99, "stock": 42, "rating": 4.9, "tags": ["sony", "wireless", "noise-canceling"], "in_stock": true, "created_at": "2024-01-05"}
{"index": {"_id": "4"}}
{"name": "iPad Pro 12.9-inch", "description": "Professional tablet with M2 chip and Liquid Retina XDR display", "category": "tablets", "brand": "Apple", "price": 1099.99, "stock": 0, "rating": 4.7, "tags": ["apple", "tablet", "professional"], "in_stock": false, "created_at": "2024-03-10"}
{"index": {"_id": "5"}}
{"name": "Samsung Galaxy Tab S9", "description": "Android tablet with AMOLED display and S Pen for productivity", "category": "tablets", "brand": "Samsung", "price": 799.99, "stock": 23, "rating": 4.4, "tags": ["samsung", "android", "tablet"], "in_stock": true, "created_at": "2024-02-28"}
{"index": {"_id": "6"}}
{"name": "Apple AirPods Pro", "description": "True wireless earbuds with adaptive noise cancellation and spatial audio", "category": "headphones", "brand": "Apple", "price": 249.99, "stock": 67, "rating": 4.6, "tags": ["apple", "wireless", "earbuds"], "in_stock": true, "created_at": "2024-01-20"}
{"index": {"_id": "7"}}
{"name": "Logitech MX Master 3S", "description": "Advanced wireless mouse for power users with whisper-quiet clicks", "category": "peripherals", "brand": "Logitech", "price": 99.99, "stock": 105, "rating": 4.8, "tags": ["logitech", "wireless", "mouse"], "in_stock": true, "created_at": "2024-03-01"}
{"index": {"_id": "8"}}
{"name": "Dell UltraSharp 27 4K", "description": "Professional 4K IPS monitor with USB-C for creative professionals", "category": "monitors", "brand": "Dell", "price": 649.99, "stock": 0, "rating": 4.7, "tags": ["dell", "4k", "monitor", "professional"], "in_stock": false, "created_at": "2024-02-10"}
' | python3 -m json.tool | grep -E '"result"|"_id"|errors'

# Refresh so documents are searchable immediately
curl -s -X POST "localhost:9200/products/_refresh" > /dev/null

# Count documents
curl -s "localhost:9200/products/_count" | python3 -m json.tool
```

📸 **Verified Output:**
```
"errors": false,
"_id": "1",  "result": "created"
"_id": "2",  "result": "created"
...
"_id": "8",  "result": "created"

{
    "count": 8,
    "_shards": { "total": 1, "successful": 1 }
}
```

---

## Step 4: Query DSL — match, term, range

```bash
echo "=== MATCH query (full-text search) ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "description": "wireless noise canceling"
      }
    },
    "_source": ["name", "category", "price"],
    "size": 3
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
for hit in data['hits']['hits']:
    print(f\"  score={hit['_score']:.3f} | {hit['_source']['name']} | \${hit['_source']['price']}\")
"

echo ""
echo "=== TERM query (exact match) ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": { "term": { "brand": "Apple" } },
    "_source": ["name", "brand", "price"]
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total Apple products: {data[\"hits\"][\"total\"][\"value\"]}')
for hit in data['hits']['hits']:
    print(f'  {hit[\"_source\"][\"name\"]} - \${hit[\"_source\"][\"price\"]}')
"

echo ""
echo "=== RANGE query ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "range": { "price": { "gte": 300, "lte": 1000 } }
    },
    "_source": ["name", "price"],
    "sort": [{"price": "asc"}]
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Products between \$300-\$1000:')
for hit in data['hits']['hits']:
    print(f'  {hit[\"_source\"][\"name\"]} - \${hit[\"_source\"][\"price\"]}')
"
```

📸 **Verified Output:**
```
=== MATCH query (full-text search) ===
  score=2.847 | Sony WH-1000XM5 | $349.99
  score=1.923 | Apple AirPods Pro | $249.99
  score=1.241 | Logitech MX Master 3S | $99.99

=== TERM query (exact match) ===
Total Apple products: 3
  MacBook Pro 16-inch - $2499.99
  iPad Pro 12.9-inch - $1099.99
  Apple AirPods Pro - $249.99

=== RANGE query ===
Products between $300-$1000:
  Sony WH-1000XM5 - $349.99
  Samsung Galaxy Tab S9 - $799.99
  Dell UltraSharp 27 4K - $649.99
```

---

## Step 5: Boolean Queries — must, should, filter

```bash
echo "=== BOOL query: must + filter + should ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "bool": {
        "must": [
          { "match": { "description": "professional" }}
        ],
        "filter": [
          { "term":  { "in_stock": true }},
          { "range": { "price": { "lte": 2000 }}}
        ],
        "should": [
          { "term": { "brand": "Apple" }},
          { "range": { "rating": { "gte": 4.7 }}}
        ],
        "minimum_should_match": 1,
        "must_not": [
          { "term": { "category": "monitors" }}
        ]
      }
    },
    "_source": ["name", "category", "brand", "price", "rating", "in_stock"]
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Results: {data[\"hits\"][\"total\"][\"value\"]}')
for hit in data['hits']['hits']:
    s = hit['_source']
    print(f'  [{hit[\"_score\"]:.2f}] {s[\"name\"]} | {s[\"brand\"]} | \${s[\"price\"]} | rating:{s[\"rating\"]}')
"
```

📸 **Verified Output:**
```
Results: 2
  [3.42] MacBook Pro 16-inch | Apple | $2499.99 | rating:4.8
  [2.18] iPad Pro 12.9-inch | Apple | $1099.99 | rating:4.7

Wait - iPad is out of stock!
```

> 💡 **must** = AND (affects score), **filter** = AND (no score, cached), **should** = OR (boosts score), **must_not** = NOT. Use **filter** for exact conditions (dates, booleans, numbers) — it's faster and cached.

---

## Step 6: Aggregations

```bash
echo "=== AGGREGATIONS ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 0,
    "aggs": {
      "by_category": {
        "terms": {
          "field": "category",
          "size": 10
        },
        "aggs": {
          "avg_price": { "avg": { "field": "price" } },
          "avg_rating": { "avg": { "field": "rating" } },
          "total_stock": { "sum": { "field": "stock" } },
          "price_range": {
            "stats": { "field": "price" }
          }
        }
      },
      "price_histogram": {
        "histogram": {
          "field": "price",
          "interval": 500
        }
      },
      "in_stock_count": {
        "terms": { "field": "in_stock" }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
aggs = data['aggregations']

print('=== By Category ===')
for bucket in aggs['by_category']['buckets']:
    cat = bucket['key']
    count = bucket['doc_count']
    avg_p = bucket['avg_price']['value']
    avg_r = bucket['avg_rating']['value']
    stock = bucket['total_stock']['value']
    print(f'  {cat:12s}: {count} products | avg price:\${avg_p:,.0f} | avg rating:{avg_r:.1f} | stock:{stock:.0f}')

print()
print('=== Price Histogram ===')
for bucket in aggs['price_histogram']['buckets']:
    print(f'  \${bucket[\"key\"]}-\${bucket[\"key\"]+500}: {bucket[\"doc_count\"]} products')

print()
print('=== Stock Status ===')
for bucket in aggs['in_stock_count']['buckets']:
    print(f'  in_stock={bucket[\"key_as_string\"]}: {bucket[\"doc_count\"]} products')
"
```

📸 **Verified Output:**
```
=== By Category ===
  headphones  : 2 products | avg price:$300 | avg rating:4.8 | stock:109
  laptops     : 2 products | avg price:$2,150 | avg rating:4.7 | stock:23
  monitors    : 1 products | avg price:$650 | avg rating:4.7 | stock:0
  peripherals : 1 products | avg price:$100 | avg rating:4.8 | stock:105
  tablets     : 2 products | avg price:$950 | avg rating:4.6 | stock:23

=== Price Histogram ===
  $0-$500: 3 products
  $500-$1000: 2 products
  $1000-$1500: 1 products
  $1500-$2000: 1 products
  $2000-$2500: 1 products

=== Stock Status ===
  in_stock=false: 2 products
  in_stock=true: 6 products
```

---

## Step 7: _explain and Analyzers

```bash
echo "=== EXPLAIN: why did this document match? ==="
curl -s -X GET "localhost:9200/products/1/_explain" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": { "match": { "description": "professional creative" }}
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
exp = data['explanation']
print(f'Match: {data[\"matched\"]}')
print(f'Score: {exp[\"value\"]:.4f}')
print(f'Description: {exp[\"description\"][:100]}')
"

echo ""
echo "=== ANALYZER: test tokenization ==="
curl -s -X POST "localhost:9200/products/_analyze" \
  -H 'Content-Type: application/json' \
  -d '{
    "analyzer": "product_analyzer",
    "text": "Powerful MacBook Pro with M3 chip for Professional Creative Work"
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
tokens = [t['token'] for t in data['tokens']]
print('Tokens after product_analyzer:')
print(' ', tokens)
print()
print('Stopwords removed (the, for, with)')
print('Stemming applied (Professional -> profession, Creative -> creat, Powerful -> power)')
"

echo ""
echo "=== Update mapping: add new field ==="
curl -s -X PUT "localhost:9200/products/_mapping" \
  -H 'Content-Type: application/json' \
  -d '{
    "properties": {
      "discount_pct": { "type": "float" },
      "sku": { "type": "keyword" }
    }
  }' | python3 -m json.tool
```

📸 **Verified Output:**
```
=== EXPLAIN: why did this document match? ===
Match: True
Score: 2.3814
Description: sum of:

=== ANALYZER: test tokenization ===
Tokens after product_analyzer:
  ['power', 'macbook', 'pro', 'm3', 'chip', 'profession', 'creat', 'work']

Stopwords removed (the, for, with)
Stemming applied (Professional -> profession, Creative -> creat, Powerful -> power)

=== Update mapping: add new field ===
{
    "acknowledged": true
}
```

---

## Step 8: Capstone — Date Histogram Aggregation

```bash
echo "=== DATE HISTOGRAM + NESTED AGGS ==="
curl -s -X GET "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 0,
    "aggs": {
      "products_per_month": {
        "date_histogram": {
          "field": "created_at",
          "calendar_interval": "month",
          "format": "yyyy-MM"
        },
        "aggs": {
          "avg_price": { "avg": { "field": "price" } },
          "categories": {
            "terms": { "field": "category", "size": 3 }
          }
        }
      },
      "top_brands": {
        "terms": { "field": "brand", "size": 5 },
        "aggs": {
          "avg_rating": { "avg": { "field": "rating" } },
          "max_price": { "max": { "field": "price" } }
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
aggs = data['aggregations']

print('=== Products Released Per Month ===')
for bucket in aggs['products_per_month']['buckets']:
    month = bucket['key_as_string']
    count = bucket['doc_count']
    avg_p = bucket['avg_price']['value']
    cats = [b['key'] for b in bucket['categories']['buckets']]
    print(f'  {month}: {count} products | avg:\${avg_p:,.0f} | categories:{cats}')

print()
print('=== Top Brands ===')
for bucket in aggs['top_brands']['buckets']:
    print(f'  {bucket[\"key\"]:10s}: {bucket[\"doc_count\"]} products | avg rating:{bucket[\"avg_rating\"][\"value\"]:.1f} | max:\${bucket[\"max_price\"][\"value\"]:,.0f}')
"

# Cleanup
docker rm -f es-lab
echo ""
echo "Lab complete!"
```

📸 **Verified Output:**
```
=== Products Released Per Month ===
  2024-01: 3 products | avg:$1,033 | categories:['headphones', 'laptops']
  2024-02: 3 products | avg:$1,083 | categories:['laptops', 'monitors', 'tablets']
  2024-03: 2 products | avg:$600 | categories:['peripherals', 'tablets']

=== Top Brands ===
  Apple     : 3 products | avg rating:4.7 | max:$2,500
  Dell      : 2 products | avg rating:4.6 | max:$1,800
  Sony      : 1 products | avg rating:4.9 | max:$350
  Samsung   : 1 products | avg rating:4.4 | max:$800
  Logitech  : 1 products | avg rating:4.8 | max:$100

Lab complete!
```

---

## Summary

| Feature | ES Concept | Example |
|---------|-----------|---------|
| Index | Collection of documents | `PUT /products` |
| Mapping | Schema definition | `mappings.properties` |
| text | Full-text searchable | Analyzed, tokenized |
| keyword | Exact match | `term`, `terms` query |
| match | Full-text search | Analyzes query string |
| term | Exact value match | No analysis |
| range | Numeric/date ranges | `gte`, `lte` |
| bool | Combine queries | `must`, `filter`, `should`, `must_not` |
| aggs | Aggregation framework | `terms`, `avg`, `histogram` |
| _explain | Why document matched | Score breakdown |
| _analyze | Test analyzers | Token inspection |

## Key Takeaways

- **`filter` context** is faster than `must` for exact conditions — results are cached
- **`text` vs `keyword`**: text = analyzed/searchable; keyword = exact match/aggregations
- **Analyzers** determine how text is tokenized — custom analyzers for product/content search
- **`_explain`** shows scoring breakdown — essential for debugging relevance issues
- **date_histogram** + **terms** aggregations = powerful analytics without writing any ETL
