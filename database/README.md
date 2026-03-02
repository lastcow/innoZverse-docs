# Database

![Database Hero](assets/hero-banner.svg)

> **Data is the foundation of every application. Master how to store, query, and scale it.**
> From your first SQL query to designing globally distributed databases — every concept is taught hands-on with real engines.

---

![Level Overview](assets/levels-diagram.svg)

---

## 🗺️ Choose Your Level

<table data-view="cards">
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th data-hidden data-card-target data-type="content-ref"></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>Relational model, SQL basics, SELECT/JOIN/GROUP BY, schema design, ERDs. Set up MySQL and PostgreSQL from scratch.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚙️ Practitioner</strong></td>
      <td>Advanced SQL, subqueries, window functions, indexing strategies, ACID transactions, and hands-on NoSQL with MongoDB and Redis.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🔴 Advanced</strong></td>
      <td>Replication, sharding, query optimisation with EXPLAIN, database security, encryption, backup strategies and high availability.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
    <tr>
      <td><strong>🏛️ Architect</strong></td>
      <td>Distributed systems, CAP theorem, cloud databases (AWS RDS, DynamoDB, MongoDB Atlas), data warehousing and large-scale migrations.</td>
      <td><a href="architect/">architect/</a></td>
    </tr>
  </tbody>
</table>

---

## 📋 Curriculum Overview

{% tabs %}
{% tab title="🌱 Foundations" %}
**Learn to think in tables, rows, and relationships**

| Labs | Topics |
|------|--------|
| 1–5  | Relational model, installing MySQL/PostgreSQL, CREATE/INSERT/SELECT |
| 6–10 | WHERE, ORDER BY, GROUP BY, HAVING, aggregate functions |
| 11–15 | JOINs (INNER, LEFT, RIGHT, FULL), subqueries, views |
| 16–20 | Database design, normalisation (1NF–3NF), ERD, foreign keys, constraints |

**Databases:** MySQL 8, PostgreSQL 15
{% endtab %}

{% tab title="⚙️ Practitioner" %}
**Go beyond basics — write queries that perform**

| Labs | Topics |
|------|--------|
| 1–5  | Window functions, CTEs, recursive queries, stored procedures |
| 6–10 | Indexing strategy, EXPLAIN ANALYSE, slow query log, covering indexes |
| 11–15 | ACID transactions, isolation levels, deadlocks, row locking |
| 16–20 | MongoDB CRUD, aggregation pipeline; Redis data structures, pub/sub, caching |

**Databases:** MySQL, PostgreSQL, MongoDB, Redis
{% endtab %}

{% tab title="🔴 Advanced" %}
**Build databases that survive failure and scale under load**

| Labs | Topics |
|------|--------|
| 1–5  | MySQL/PostgreSQL replication (primary-replica), binary log |
| 6–10 | Horizontal sharding, partitioning, consistent hashing |
| 11–15 | Query profiling, buffer pool tuning, connection pooling (PgBouncer) |
| 16–20 | Encryption at rest/transit, audit logging, backup & point-in-time recovery |

**Tools:** pgBouncer, ProxySQL, mysqldump, pg_dump, Percona
{% endtab %}

{% tab title="🏛️ Architect" %}
**Design data systems at cloud and enterprise scale**

| Labs | Topics |
|------|--------|
| 1–5  | Distributed databases, CAP theorem, eventual consistency, Paxos/Raft |
| 6–10 | AWS RDS (multi-AZ, read replicas), DynamoDB, Aurora Serverless |
| 11–15 | MongoDB Atlas, data warehousing (Redshift, BigQuery concepts) |
| 16–20 | Schema migrations at scale, zero-downtime deployments, data governance |

**Platforms:** AWS RDS, DynamoDB, MongoDB Atlas, Snowflake concepts
{% endtab %}
{% endtabs %}

---

## ⚡ Lab Format

Every lab uses a real database engine running locally or in Docker:

{% hint style="success" %}
**Each lab includes:**
- 🎯 **Objective** — clear goal with real-world application
- 📚 **Background** — why this concept matters and when to use it
- 🔬 **Step-by-step instructions** — real SQL and shell commands
- 📸 **Verified output** — actual query results from live database runs
- 📊 **Diagrams** — ERDs and execution plans where relevant
- 🚨 **Common mistakes** — pitfalls and how to avoid them
{% endhint %}

---

## 🏆 Certifications Aligned

| Certification | Relevant Levels |
|---|---|
| **Oracle MySQL 8 Developer** | Foundations + Practitioner |
| **PostgreSQL Associate (EDB)** | Foundations + Practitioner |
| **MongoDB Certified Developer** | Practitioner + Advanced |
| **AWS Certified Database Specialty** | Advanced + Architect |
| **Google Professional Data Engineer** | Architect |
| **Snowflake SnowPro Core** | Architect |

---

## 🚀 Start Here

{% hint style="info" %}
**New to databases?** Start at [Lab 1: Introduction to Relational Databases](foundations/labs/lab-01-relational-model.md) — no prior SQL knowledge needed.

**Already know SQL?** Jump to [Lab 1: Advanced SQL — Window Functions](practitioner/labs/lab-01-window-functions.md) to master the features most developers skip.

**Working with NoSQL?** Head to [Lab 16: MongoDB Fundamentals](practitioner/labs/lab-16-mongodb-fundamentals.md) for hands-on document database work.
{% endhint %}

{% hint style="warning" %}
**Environment:** Labs use **MySQL 8** and **PostgreSQL 15** via Docker. MongoDB and Redis labs use Docker containers. All commands tested on Ubuntu 22.04.
{% endhint %}
