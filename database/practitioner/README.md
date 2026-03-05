# ⚙️ Practitioner — Database Labs

> **Go beyond basics — write queries that perform and build polyglot data solutions.**
> Advanced SQL, indexing strategies, ACID transactions, and hands-on NoSQL with MongoDB and Redis.

**Technologies:** MySQL 8, PostgreSQL 15, MongoDB 7, Redis 7

---

## 🚀 Start Here → [Lab 01: Window Functions](labs/lab-01-window-functions.md)

---

## 📋 Lab Index

| # | Lab | DB | Topics |
|---|-----|----|--------|
| 01 | [Window Functions](labs/lab-01-window-functions.md) | PostgreSQL 15 | OVER, PARTITION BY, RANK, ROW_NUMBER, LAG/LEAD, NTILE |
| 02 | [CTEs & Recursive Queries](labs/lab-02-ctes-recursive-queries.md) | PostgreSQL 15 | WITH, recursive CTEs, tree traversal, hierarchies |
| 03 | [Stored Procedures & Functions](labs/lab-03-stored-procedures-functions.md) | MySQL 8 | CREATE PROCEDURE, FUNCTION, DECLARE, loops, cursors |
| 04 | [Triggers & Events](labs/lab-04-triggers-events.md) | MySQL 8 | BEFORE/AFTER triggers, event scheduler, audit patterns |
| 05 | [Advanced Indexing](labs/lab-05-advanced-indexing.md) | PostgreSQL 15 | Partial, composite, covering, GIN, GiST, BRIN indexes |
| 06 | [EXPLAIN & Query Optimization](labs/lab-06-explain-query-optimization.md) | PostgreSQL 15 | EXPLAIN ANALYZE, seq scan vs index scan, query plans |
| 07 | [Transactions & Isolation Levels](labs/lab-07-transactions-isolation-levels.md) | PostgreSQL 15 | Read Uncommitted/Committed/Repeatable Read/Serializable |
| 08 | [Deadlocks](labs/lab-08-deadlocks-detection-prevention.md) | MySQL 8 | Deadlock detection, prevention, SHOW INNODB STATUS |
| 09 | [Connection Pooling](labs/lab-09-connection-pooling.md) | PostgreSQL 15 | PgBouncer setup, pool modes, connection limits |
| 10 | [Full-Text Search](labs/lab-10-fulltext-search.md) | MySQL 8, PostgreSQL | MATCH AGAINST, tsvector/tsquery, GIN indexes |
| 11 | [MongoDB CRUD](labs/lab-11-mongodb-crud.md) | MongoDB 7 | insertOne/Many, find, updateOne, deleteOne, filters |
| 12 | [MongoDB Aggregation Pipeline](labs/lab-12-mongodb-aggregation-pipeline.md) | MongoDB 7 | $match, $group, $sort, $lookup, $unwind, $project |
| 13 | [MongoDB Indexes & Queries](labs/lab-13-mongodb-indexes-queries.md) | MongoDB 7 | createIndex, explain, compound, text, TTL indexes |
| 14 | [Redis Data Structures](labs/lab-14-redis-data-structures.md) | Redis 7 | Strings, hashes, lists, sets, sorted sets, HyperLogLog |
| 15 | [Redis Pub/Sub & Streams](labs/lab-15-redis-pubsub-streams.md) | Redis 7 | PUBLISH/SUBSCRIBE, Streams, consumer groups, XREAD |
| 16 | [Redis Caching Patterns](labs/lab-16-redis-caching-patterns.md) | Redis 7 | Cache-aside, write-through, write-behind, TTL, eviction |
| 17 | [PostgreSQL JSONB Advanced](labs/lab-17-postgresql-jsonb-advanced.md) | PostgreSQL 15 | JSONB operators, path queries, GIN indexes, aggregation |
| 18 | [Database Security](labs/lab-18-database-security.md) | MySQL 8 | Users, GRANT/REVOKE, SSL, password policies |
| 19 | [Backup & Restore](labs/lab-19-backup-restore.md) | MySQL 8, PostgreSQL | mysqldump, pg_dump, restore, point-in-time recovery |
| 20 | [Capstone: Multi-Model App Database](labs/lab-20-capstone-multimodel-app.md) | MySQL+MongoDB+Redis | Full app: relational + document + cache integration |

---

## 🗂️ Learning Path

### SQL Mastery (Labs 1–10)
Window functions and CTEs are the most-asked SQL interview topics. Master these before NoSQL.

### NoSQL (Labs 11–16)
MongoDB for documents, Redis for speed. Learn when to use each.

### Advanced Topics (Labs 17–20)
JSONB power user, security hardening, backup strategies, capstone.

---

## 🛠️ Setup

```bash
# PostgreSQL
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15

# MongoDB
docker run -d --name mongo-lab mongo:7

# Redis
docker run -d --name redis-lab redis:7-alpine

# MySQL
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
```
