# Lab 13: Elasticsearch & Kibana Log Indexing

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Elasticsearch is a distributed, RESTful search and analytics engine built on Apache Lucene. It stores JSON documents in **indices**, distributes them across **shards**, and enables full-text search via **analyzers**. Kibana is the visualization UI for the Elastic Stack. This lab covers installation, configuration, index mappings, Query DSL, and Index Lifecycle Management (ILM).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Elasticsearch Cluster                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Index: logs-2024.01.01                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │  Primary     │  │  Primary     │  │ Primary  │  │   │
│  │  │  Shard 0     │  │  Shard 1     │  │ Shard 2  │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │   │
│  │         │                 │               │         │   │
│  │  ┌──────▼───────┐  ┌──────▼───────┐  ┌────▼─────┐  │   │
│  │  │  Replica     │  │  Replica     │  │ Replica  │  │   │
│  │  │  Shard 0     │  │  Shard 1     │  │ Shard 2  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Node 1 (master+data)  Node 2 (data)  Node 3 (data)        │
│                                                             │
│  Client → Elasticsearch REST API :9200                      │
│  Kibana → Elasticsearch :9200 → Browser :5601              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Add Elasticsearch Repository and Check Package

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null
apt-get install -y -qq wget curl gnupg apt-transport-https 2>/dev/null

# Import Elastic GPG key
wget -q -O - https://artifacts.elastic.co/GPG-KEY-elasticsearch \
  | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg 2>/dev/null && \
  echo 'GPG key imported OK'

# Add Elastic 8.x repo
echo 'deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main' \
  | tee /etc/apt/sources.list.d/elastic-8.x.list

apt-get update -qq 2>/dev/null
apt-cache show elasticsearch 2>/dev/null | grep -E '^(Package|Version)' | head -4
"
```

📸 **Verified Output:**
```
GPG key imported OK
deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main
Package: elasticsearch
Version: 8.19.12
Package: elasticsearch
Version: 8.19.11
```

> 💡 Elasticsearch 8.x enables security by default (TLS + basic auth). For development/testing, add `xpack.security.enabled: false` to `elasticsearch.yml`. Never disable security in production — use the auto-generated `elastic` user password from first startup.

---

## Step 2: Configure elasticsearch.yml

```bash
docker run --rm ubuntu:22.04 bash -c "
mkdir -p /tmp/es-config

cat > /tmp/es-config/elasticsearch.yml << 'EOF'
# ======================== Elasticsearch Configuration =========================

# Cluster
cluster.name: production-logs
node.name: es-node-1

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

# Network
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# Discovery (single node for dev; use zen discovery for multi-node)
discovery.type: single-node

# Security (dev: disabled; prod: enabled with TLS)
xpack.security.enabled: false
xpack.security.http.ssl.enabled: false

# JVM heap (set to 50% of RAM, max 31GB)
# Configure via jvm.options: -Xms4g -Xmx4g

# Index settings (applied to new indices)
# action.auto_create_index: false   # Prevent accidental index creation

# Shard allocation
cluster.routing.allocation.disk.threshold_enabled: true
cluster.routing.allocation.disk.watermark.low: 85%
cluster.routing.allocation.disk.watermark.high: 90%
cluster.routing.allocation.disk.watermark.flood_stage: 95%

# Thread pools
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000
EOF

echo '=== elasticsearch.yml ==='
cat /tmp/es-config/elasticsearch.yml
"
```

📸 **Verified Output:**
```
=== elasticsearch.yml ===
# ======================== Elasticsearch Configuration =========================

cluster.name: production-logs
node.name: es-node-1

path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

discovery.type: single-node

xpack.security.enabled: false
...
```

> 💡 JVM heap is the most critical tuning parameter. Set `-Xms` and `-Xmx` to the same value to prevent heap resizing. Elasticsearch is memory-hungry: leave 50% of RAM for the OS page cache (Lucene uses OS page cache heavily for segment reads).

---

## Step 3: _cat APIs for Cluster Inspection

```bash
docker run --rm ubuntu:22.04 bash -c "
# Simulate _cat API responses (as would appear against a running cluster)
echo '=== GET /_cat/health?v ==='
cat << 'EOF'
epoch      timestamp cluster          status node.total node.data shards pri relo init unassign pending_tasks max_task_wait_time active_shards_percent
1706745600 12:00:00  production-logs  green           3         3     30  15    0    0        0             0                  -                100.0%
EOF

echo ''
echo '=== GET /_cat/nodes?v ==='
cat << 'EOF'
ip          heap.percent ram.percent cpu load_1m load_5m load_15m node.role   master name
10.0.1.10            45          72   8    0.80    0.75     0.70 cdfhilmrstw *      es-node-1
10.0.1.11            38          68   5    0.55    0.60     0.58 cdfhilrstw  -      es-node-2
10.0.1.12            42          70   6    0.62    0.58     0.55 cdfhilrstw  -      es-node-3
EOF

echo ''
echo '=== GET /_cat/indices?v&s=index ==='
cat << 'EOF'
health status index                uuid                   pri rep docs.count docs.deleted store.size pri.store.size
green  open   .kibana_1            abc123def456           1   0          12            0     56.2kb         56.2kb
green  open   logs-2024.01.01      xyz789abc012           3   1     845231          125    823.4mb        411.7mb
green  open   logs-2024.01.02      def456xyz789           3   1    1024567          203      1.1gb        562.3mb
green  open   metrics-2024.01.01   ghi789jkl012           1   1      52431            0     24.8mb         12.4mb
EOF

echo ''
echo '=== GET /_cat/shards?v&index=logs-2024.01.01 ==='
cat << 'EOF'
index            shard prirep state   docs  store ip          node
logs-2024.01.01  0     p      STARTED 281743 137.5mb 10.0.1.10  es-node-1
logs-2024.01.01  0     r      STARTED 281743 137.5mb 10.0.1.11  es-node-2
logs-2024.01.01  1     p      STARTED 281744 137.4mb 10.0.1.11  es-node-2
logs-2024.01.01  1     r      STARTED 281744 137.4mb 10.0.1.12  es-node-3
logs-2024.01.01  2     p      STARTED 281744 136.8mb 10.0.1.12  es-node-3
logs-2024.01.01  2     r      STARTED 281744 136.8mb 10.0.1.10  es-node-1
EOF
"
```

📸 **Verified Output:**
```
=== GET /_cat/health?v ===
epoch      timestamp cluster          status node.total node.data shards pri relo init unassign ...
1706745600 12:00:00  production-logs  green           3         3     30  15    0    0        0 ...

=== GET /_cat/nodes?v ===
ip          heap.percent ram.percent cpu load_1m ... node.role   master name
10.0.1.10            45          72   8    0.80  ... cdfhilmrstw *      es-node-1
...
```

> 💡 Cluster status: **green** = all primary + replica shards assigned; **yellow** = primaries assigned, some replicas missing (single-node is always yellow unless `number_of_replicas: 0`); **red** = unassigned primaries — data may be unavailable. Monitor with `GET /_cluster/health`.

---

## Step 4: Index Mappings

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== PUT /logs-template (index template with mappings) ==='
cat << 'EOF'
PUT _index_template/logs-template
{
  \"index_patterns\": [\"logs-*\"],
  \"template\": {
    \"settings\": {
      \"number_of_shards\": 3,
      \"number_of_replicas\": 1,
      \"refresh_interval\": \"30s\",
      \"codec\": \"best_compression\"
    },
    \"mappings\": {
      \"dynamic\": \"strict\",
      \"properties\": {
        \"@timestamp\": {
          \"type\": \"date\",
          \"format\": \"strict_date_optional_time||epoch_millis\"
        },
        \"message\": {
          \"type\": \"text\",
          \"analyzer\": \"standard\",
          \"fields\": {
            \"keyword\": {\"type\": \"keyword\", \"ignore_above\": 256}
          }
        },
        \"level\": {\"type\": \"keyword\"},
        \"service\": {\"type\": \"keyword\"},
        \"host\": {
          \"properties\": {
            \"name\": {\"type\": \"keyword\"},
            \"ip\": {\"type\": \"ip\"}
          }
        },
        \"http\": {
          \"properties\": {
            \"method\": {\"type\": \"keyword\"},
            \"status_code\": {\"type\": \"short\"},
            \"url\": {\"type\": \"keyword\"},
            \"response_time_ms\": {\"type\": \"float\"}
          }
        },
        \"user_id\": {\"type\": \"keyword\"},
        \"geo\": {\"type\": \"geo_point\"},
        \"tags\": {\"type\": \"keyword\"}
      }
    }
  }
}
EOF

echo ''
echo '=== Field type reference ==='
cat << 'EOF'
text     - full-text search, analyzed (tokenized, lowercased, stemmed)
keyword  - exact match, aggregations, sorting (not analyzed)
date     - ISO8601 or epoch_millis; stored as long internally
long     - 64-bit integer
float    - 32-bit float
boolean  - true/false
ip       - IPv4/IPv6, supports CIDR range queries
geo_point- lat/lon pairs, supports radius/bounding-box queries
nested   - array of objects with independent field queries
object   - flat mapping of nested JSON (fields flattened)
EOF
"
```

📸 **Verified Output:**
```
=== PUT /logs-template (index template with mappings) ===
PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
...
```

> 💡 Use `"dynamic": "strict"` in production to reject documents with unmapped fields — this prevents mapping explosions (ES has a default limit of 1000 fields per index). Use `"dynamic": "true"` only for exploration. Add `"fields": {"keyword": {...}}` to text fields you need to both search and aggregate.

---

## Step 5: Query DSL

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== Elasticsearch Query DSL Examples ==='
cat << 'EOF'

1. MATCH query (full-text search on analyzed field):
POST /logs-*/_search
{
  \"query\": {
    \"match\": {
      \"message\": \"connection refused timeout\"
    }
  }
}

2. TERM query (exact match on keyword field):
POST /logs-*/_search
{
  \"query\": {
    \"term\": {\"level\": \"ERROR\"}
  }
}

3. RANGE query (date/numeric range):
POST /logs-*/_search
{
  \"query\": {
    \"range\": {
      \"@timestamp\": {
        \"gte\": \"2024-01-01T00:00:00Z\",
        \"lte\": \"2024-01-02T00:00:00Z\"
      }
    }
  }
}

4. BOOL query (compound: must/should/must_not/filter):
POST /logs-*/_search
{
  \"query\": {
    \"bool\": {
      \"must\": [
        {\"match\": {\"message\": \"error\"}},
        {\"term\": {\"service\": \"api-gateway\"}}
      ],
      \"filter\": [
        {\"range\": {
          \"@timestamp\": {\"gte\": \"now-1h\"}
        }},
        {\"term\": {\"level\": \"ERROR\"}}
      ],
      \"must_not\": [
        {\"term\": {\"user_id\": \"healthcheck\"}}
      ]
    }
  },
  \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}],
  \"size\": 100,
  \"_source\": [\"@timestamp\", \"message\", \"service\", \"http.status_code\"]
}

5. AGGREGATION query (count errors by service):
POST /logs-*/_search
{
  \"size\": 0,
  \"query\": {\"term\": {\"level\": \"ERROR\"}},
  \"aggs\": {
    \"errors_by_service\": {
      \"terms\": {\"field\": \"service\", \"size\": 10},
      \"aggs\": {
        \"error_rate_over_time\": {
          \"date_histogram\": {
            \"field\": \"@timestamp\",
            \"calendar_interval\": \"1h\"
          }
        }
      }
    }
  }
}
EOF
"
```

📸 **Verified Output:**
```
=== Elasticsearch Query DSL Examples ===

1. MATCH query (full-text search on analyzed field):
POST /logs-*/_search
{
  "query": {
    "match": {
      "message": "connection refused timeout"
    }
  }
}
...
```

> 💡 Use `filter` context (inside `bool.filter`) instead of `must` for conditions that don't affect scoring (date ranges, exact matches). Filter results are cached, making them much faster for repeated queries. `must` affects the relevance `_score` — use it for full-text search where ranking matters.

---

## Step 6: Index Lifecycle Management (ILM)

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== ILM Policy: hot-warm-cold-delete ==='
cat << 'EOF'
PUT _ilm/policy/logs-lifecycle
{
  \"policy\": {
    \"phases\": {
      \"hot\": {
        \"min_age\": \"0ms\",
        \"actions\": {
          \"rollover\": {
            \"max_age\": \"1d\",
            \"max_primary_shard_size\": \"50gb\"
          },
          \"set_priority\": {\"priority\": 100}
        }
      },
      \"warm\": {
        \"min_age\": \"7d\",
        \"actions\": {
          \"shrink\": {\"number_of_shards\": 1},
          \"forcemerge\": {\"max_num_segments\": 1},
          \"set_priority\": {\"priority\": 50},
          \"allocate\": {
            \"require\": {\"box_type\": \"warm\"}
          }
        }
      },
      \"cold\": {
        \"min_age\": \"30d\",
        \"actions\": {
          \"set_priority\": {\"priority\": 0},
          \"allocate\": {
            \"require\": {\"box_type\": \"cold\"}
          },
          \"freeze\": {}
        }
      },
      \"delete\": {
        \"min_age\": \"90d\",
        \"actions\": {
          \"delete\": {}
        }
      }
    }
  }
}
EOF

echo ''
echo '=== ILM Phase transitions ==='
cat << 'EOF'
HOT   (0d-1d)   : Active writes, rollover at 50GB or 1 day
                  All primary shards on hot-tier nodes (SSD)
WARM  (7d-30d)  : Read-only, shrink to 1 shard, force-merge
                  Move to warm-tier nodes (HDD, cheaper)
COLD  (30d-90d) : Searchable but frozen (mounted from snapshot)
                  Very low storage cost
DELETE (90d+)   : Index deleted automatically
EOF
"
```

📸 **Verified Output:**
```
=== ILM Policy: hot-warm-cold-delete ===
PUT _ilm/policy/logs-lifecycle
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_primary_shard_size": "50gb"
          },
...
```

> 💡 ILM requires Data Streams or aliases with `is_write_index: true`. The rollover action creates a new index (`logs-000002`) when conditions are met, updating the alias to point to the new write index. Use `GET /<index>/_ilm/explain` to check current ILM phase and any errors.

---

## Step 7: Kibana Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/kibana.yml << 'EOF'
# Kibana server
server.host: 0.0.0.0
server.port: 5601
server.name: kibana-prod
server.publicBaseUrl: https://kibana.company.com

# Elasticsearch connection
elasticsearch.hosts: ['http://es-node-1:9200', 'http://es-node-2:9200']
elasticsearch.requestTimeout: 30000
elasticsearch.shardTimeout: 30000

# For Elasticsearch with security enabled:
# elasticsearch.username: kibana_system
# elasticsearch.password: kibana_password

# Kibana data
kibana.index: .kibana
kibana.defaultAppId: discover

# Logging
logging:
  appenders:
    file:
      type: file
      fileName: /var/log/kibana/kibana.log
      layout:
        type: json
  root:
    appenders: [default, file]
    level: info

# Saved objects encryption
# xpack.encryptedSavedObjects.encryptionKey: 'min-32-byte-long-strong-key-here'

# Alerting
xpack.alerting.maxEphemeralActionsPerAlert: 10

# Feature flags
xpack.fleet.enabled: true
xpack.apm.enabled: true
EOF

echo '=== kibana.yml ==='
cat /tmp/kibana.yml

echo ''
echo '=== Key Kibana API calls ==='
cat << 'EOF'
# Create index pattern (data view)
POST /api/saved_objects/index-pattern
{
  \"attributes\": {
    \"title\": \"logs-*\",
    \"timeFieldName\": \"@timestamp\"
  }
}

# Export saved objects (dashboards, visualizations)
POST /api/saved_objects/_export
{\"type\": [\"dashboard\", \"visualization\", \"index-pattern\"]}

# Import saved objects
POST /api/saved_objects/_import?overwrite=true
--form file=@export.ndjson
EOF
"
```

📸 **Verified Output:**
```
=== kibana.yml ===
server.host: 0.0.0.0
server.port: 5601
server.name: kibana-prod
server.publicBaseUrl: https://kibana.company.com

elasticsearch.hosts: ['http://es-node-1:9200', 'http://es-node-2:9200']
...
```

> 💡 In Kibana 8.x, **Data Views** replaced **Index Patterns**. A Data View maps to one or more indices via a wildcard pattern and designates the `@timestamp` field. Create Data Views via Kibana UI → Stack Management → Data Views, or use the Saved Objects API.

---

## Step 8: Capstone — Production Log Indexing Setup

**Scenario:** Configure a 3-node Elasticsearch cluster to index application logs with a proper mapping, ILM policy, and Kibana data view for a production e-commerce platform.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget curl gnupg apt-transport-https 2>/dev/null

# Verify ES package availability
wget -q -O - https://artifacts.elastic.co/GPG-KEY-elasticsearch \
  | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg 2>/dev/null
echo 'deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main' \
  > /etc/apt/sources.list.d/elastic-8.x.list
apt-get update -qq 2>/dev/null

echo '=== Available Elasticsearch version ==='
apt-cache show elasticsearch 2>/dev/null | grep '^Version' | head -3

echo ''
echo '=== Production checklist ==='
cat << 'EOF'
[x] elasticsearch.yml: cluster.name, node.name, discovery.seed_hosts
[x] JVM heap: -Xms16g -Xmx16g (50% of RAM)
[x] system: vm.max_map_count=262144 (sysctl)
[x] system: ulimit -n 65535 (open files)
[x] ILM policy: hot(1d/50GB) -> warm(7d) -> cold(30d) -> delete(90d)
[x] Index template: strict mapping, 3 shards, 1 replica
[x] Kibana: elasticsearch.hosts list (all nodes for HA)
[x] Snapshots: registered S3/GCS repository for backups
[x] Monitoring: metricbeat -> .monitoring-es-* indices
EOF
"
```

📸 **Verified Output:**
```
=== Available Elasticsearch version ===
Version: 8.19.12
Version: 8.19.11
Version: 8.19.10

=== Production checklist ===
[x] elasticsearch.yml: cluster.name, node.name, discovery.seed_hosts
[x] JVM heap: -Xms16g -Xmx16g (50% of RAM)
[x] system: vm.max_map_count=262144 (sysctl)
...
```

> 💡 The most common production mistake: not setting `vm.max_map_count=262144` on the host. Elasticsearch requires this for memory-mapped files (Lucene segments). Add to `/etc/sysctl.conf`: `vm.max_map_count=262144` and run `sysctl -p`. Docker users: set on the host, not inside the container.

---

## Summary

| Concept | Key Details |
|---------|-------------|
| **Indices** | Logical namespace for documents; wildcards (`logs-*`) span multiple |
| **Shards** | Primary (write) + Replica (read/HA); set at index creation, immutable |
| **Mappings** | Field type definitions; `dynamic: strict` prevents unmapped fields |
| **Analyzers** | `standard`: tokenize + lowercase + filter; used for `text` fields only |
| **_cat APIs** | `/_cat/health`, `/_cat/nodes`, `/_cat/indices`, `/_cat/shards` |
| **Query DSL** | `match` (full-text), `term` (exact), `range`, `bool` (compound) |
| **Aggregations** | `terms`, `date_histogram`, `avg`, `percentiles` — analytics on top of search |
| **ILM** | hot→warm→cold→delete; rollover at size/age thresholds |
| **elasticsearch.yml** | `cluster.name`, `network.host`, `discovery.type`, `path.data/logs` |
| **kibana.yml** | `elasticsearch.hosts` (list for HA), `server.publicBaseUrl` |
| **ES 8.x latest** | Version 8.19.12 (from elastic apt repo as of 2025) |
| **JVM tuning** | `-Xms` = `-Xmx` = 50% RAM; max 31GB for compressed OOPs |
