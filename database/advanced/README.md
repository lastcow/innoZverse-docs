# 🔴 Advanced — Database Labs

> **Build databases that survive failure and scale under load.**
> Replication, sharding, query optimization, encryption, backup, and high availability across MySQL, PostgreSQL, MongoDB, Redis, Cassandra, and Elasticsearch.

**Technologies:** MySQL 8, PostgreSQL 15, MongoDB, Redis, Cassandra 4, Elasticsearch

---

## 🚀 Start Here → [Lab 01: MySQL Replication](labs/lab-01-mysql-replication.md)

---

## 📋 Lab Index

| # | Lab | DB | Topics |
|---|-----|----|--------|
| 01 | [MySQL Replication](labs/lab-01-mysql-replication.md) | MySQL 8 | Primary-replica setup, binlog, SHOW REPLICA STATUS |
| 02 | [PostgreSQL Streaming Replication](labs/lab-02-postgresql-streaming-replication.md) | PostgreSQL 15 | WAL streaming, pg_basebackup, replication slots |
| 03 | [MySQL Group Replication](labs/lab-03-mysql-group-replication.md) | MySQL 8 | Multi-primary, consensus, automatic failover |
| 04 | [Table Partitioning](labs/lab-04-table-partitioning.md) | MySQL 8, PostgreSQL | RANGE, LIST, HASH partitioning, partition pruning |
| 05 | [Sharding Concepts](labs/lab-05-sharding-concepts.md) | MySQL 8 | Horizontal sharding, consistent hashing, ProxySQL routing |
| 06 | [Query Profiling & Slow Log](labs/lab-06-query-profiling-slow-log.md) | MySQL 8 | slow_query_log, pt-query-digest, profiling |
| 07 | [Buffer Pool & Memory Tuning](labs/lab-07-buffer-pool-memory-tuning.md) | MySQL 8 | innodb_buffer_pool_size, page flushing, memory hierarchy |
| 08 | [InnoDB Internals](labs/lab-08-innodb-internals.md) | MySQL 8 | B+tree, MVCC, undo log, redo log, change buffer |
| 09 | [PostgreSQL WAL & MVCC](labs/lab-09-postgresql-wal-mvcc.md) | PostgreSQL 15 | WAL files, LSN, MVCC visibility, dead tuples, VACUUM |
| 10 | [ProxySQL Routing](labs/lab-10-proxysql-routing.md) | MySQL 8 | Read/write splitting, query rules, connection pooling |
| 11 | [PgBouncer Advanced](labs/lab-11-pgbouncer-advanced.md) | PostgreSQL 15 | Transaction/session pooling, SSL, monitoring |
| 12 | [Database Encryption](labs/lab-12-database-encryption.md) | MySQL 8, PostgreSQL | TDE, binlog encryption, pg_crypto, keyring plugins |
| 13 | [Audit Logging](labs/lab-13-audit-logging.md) | MySQL 8, PostgreSQL | MySQL audit plugin, pgaudit, compliance logging |
| 14 | [Point-in-Time Recovery](labs/lab-14-point-in-time-recovery.md) | MySQL 8 | binlog-based PITR, mysqlbinlog, restore workflow |
| 15 | [MongoDB Replica Sets](labs/lab-15-mongodb-replica-sets.md) | MongoDB 7 | Primary/secondary/arbiter, elections, oplog |
| 16 | [MongoDB Sharding](labs/lab-16-mongodb-sharding.md) | MongoDB 7 | Shard key, mongos, config servers, chunk migration |
| 17 | [Redis Cluster & Sentinel](labs/lab-17-redis-cluster-sentinel.md) | Redis 7 | Redis Cluster slots, Sentinel auto-failover |
| 18 | [Cassandra Wide-Column](labs/lab-18-cassandra-wide-column.md) | Cassandra 4.1 | Keyspace, table, CQL, consistency levels, compaction |
| 19 | [Elasticsearch Search Engine](labs/lab-19-elasticsearch-search.md) | Elasticsearch 8 | Inverted index, mappings, query DSL, aggregations |
| 20 | [Capstone: HA Database Architecture](labs/lab-20-capstone-ha-database.md) | Multi-stack | MySQL Group Replication + ProxySQL + Redis Sentinel |

---

## 🗂️ Learning Path

### Replication & HA (Labs 1–5)
Start here for production reliability. Replication is the foundation of every HA architecture.

### Performance Tuning (Labs 6–11)
Buffer pool, MVCC internals, slow query analysis — the skills that make you a performance expert.

### Security & Operations (Labs 12–14)
Encryption, audit logging, and recovery procedures for compliance and production ops.

### NoSQL Deep Dive (Labs 15–19)
MongoDB replication/sharding, Redis cluster, Cassandra, and Elasticsearch internals.

---

## 🛠️ Setup

```bash
# MySQL with binlog enabled
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass \
  --log-opt max-size=10m mysql:8.0 \
  --server-id=1 --log-bin=mysql-bin --binlog-format=ROW

# PostgreSQL
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass \
  -e POSTGRES_INITDB_ARGS="--wal-level=replica" postgres:15

# Cassandra (needs 60s to start)
docker run -d --name cass-lab cassandra:4.1
sleep 60

# Elasticsearch
docker run -d --name es-lab -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" elasticsearch:8.11.0
```
