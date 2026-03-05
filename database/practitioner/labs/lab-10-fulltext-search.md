# Lab 10: Full-Text Search

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

Full-text search goes beyond `LIKE '%keyword%'` — it understands language (stemming, stop words, ranking), supports complex queries (AND/OR/NOT/proximity), and uses inverted indexes for performance.

---

## Step 1 — MySQL: FULLTEXT Index Setup

```sql
USE labdb;

CREATE TABLE articles (
  id    INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255),
  body  TEXT,
  FULLTEXT(title, body)  -- Composite FULLTEXT index
);

INSERT INTO articles (title, body) VALUES
  ('Introduction to MySQL',
   'MySQL is a popular relational database management system. It uses SQL for queries.'),
  ('Advanced SQL Queries',
   'Learn about joins, subqueries, window functions and CTEs in SQL databases.'),
  ('NoSQL vs SQL Databases',
   'Comparing document stores like MongoDB with relational databases like MySQL and PostgreSQL.'),
  ('Database Performance Tuning',
   'Indexing strategies, query optimization and connection pooling improve database performance.'),
  ('Redis Caching Strategies',
   'Cache-aside, write-through and write-behind patterns with Redis for high performance apps.');
```

> 💡 FULLTEXT indexes in MySQL require `InnoDB` (MySQL 5.6+) or `MyISAM`. Minimum word length is controlled by `innodb_ft_min_token_size` (default 3 chars).

---

## Step 2 — MySQL: Natural Language Mode

```sql
-- Natural language mode (default): ranks results by relevance
SELECT id, title,
  MATCH(title, body) AGAINST('MySQL database' IN NATURAL LANGUAGE MODE) AS relevance
FROM articles
WHERE MATCH(title, body) AGAINST('MySQL database' IN NATURAL LANGUAGE MODE)
ORDER BY relevance DESC;
```

📸 **Verified Output:**
```
id  title                        relevance
1   Introduction to MySQL        0.47506874799728394
4   Database Performance Tuning  0.31671249866485596
3   NoSQL vs SQL Databases       0.15835624933242798
```

> 💡 Natural Language Mode ignores words that appear in >50% of rows (they're not discriminating). With 5 rows, "database" appears in 4/5 = 80% — so it might be ignored. Use `IN BOOLEAN MODE` for exact control.

---

## Step 3 — MySQL: Boolean Mode

```sql
-- Boolean mode: precise control with operators
-- +word = must contain  -word = must NOT contain  * = wildcard

-- Must contain MySQL, must not contain NoSQL
SELECT id, title FROM articles
WHERE MATCH(title, body) AGAINST('+MySQL -NoSQL' IN BOOLEAN MODE);
```

📸 **Verified Output:**
```
id  title
1   Introduction to MySQL
```

```sql
-- Phrase search with quotes
SELECT id, title FROM articles
WHERE MATCH(title, body) AGAINST('"relational database"' IN BOOLEAN MODE);

-- Wildcard search
SELECT id, title FROM articles
WHERE MATCH(title, body) AGAINST('optim*' IN BOOLEAN MODE);

-- Word must be in title (boost)
SELECT id, title,
  MATCH(title, body) AGAINST('>MySQL <database' IN BOOLEAN MODE) AS score
FROM articles
WHERE MATCH(title, body) AGAINST('>MySQL <database' IN BOOLEAN MODE)
ORDER BY score DESC;
```

**Boolean mode operators:**
| Operator | Meaning |
|----------|---------|
| `+word` | Word must be present |
| `-word` | Word must be absent |
| `word*` | Wildcard prefix |
| `"phrase"` | Exact phrase |
| `>word` | Boost word's relevance |
| `<word` | Reduce word's relevance |
| `(group)` | Grouping |

---

## Step 4 — MySQL: Query Expansion Mode

```sql
-- First pass: find best matches
-- Second pass: add words from best matches, re-search
SELECT id, title FROM articles
WHERE MATCH(title, body)
  AGAINST('performance' WITH QUERY EXPANSION)
ORDER BY MATCH(title, body) AGAINST('performance' WITH QUERY EXPANSION) DESC;
```

> 💡 Query Expansion performs two-phase search: finds top results, extracts key terms, then re-searches with those terms. Useful for short queries but can return loosely related results.

---

## Step 5 — PostgreSQL: tsvector and tsquery

```sql
-- tsvector: preprocessed document representation
SELECT to_tsvector('english', 'PostgreSQL is an advanced relational database system');
-- 'advanced':4 'databas':6 'postgresql':1 'relat':5 'system':7
-- (positions and lexemes after stemming/stop-word removal)

-- tsquery: search expression
SELECT to_tsquery('english', 'postgresql & database');
-- 'postgresql' & 'databas'   (note: stemmed)

SELECT to_tsquery('english', 'query | optimization');
-- 'queri' | 'optim'

-- Phrase query (PostgreSQL 9.6+)
SELECT to_tsquery('english', 'relational <-> database');
-- Must appear adjacent
```

---

## Step 6 — PostgreSQL: Full-Text Search with GIN Index

```sql
CREATE TABLE pg_articles (
  id    SERIAL PRIMARY KEY,
  title TEXT,
  body  TEXT
);

CREATE INDEX idx_pg_articles_tsv
ON pg_articles
USING GIN(to_tsvector('english', title || ' ' || body));

INSERT INTO pg_articles (title, body) VALUES
  ('Introduction to PostgreSQL',
   'PostgreSQL is an advanced relational database system with powerful features.'),
  ('Advanced SQL Window Functions',
   'Window functions like ROW_NUMBER and RANK allow complex analytical queries in SQL.'),
  ('NoSQL vs Relational Databases',
   'Comparing document stores like MongoDB with relational systems like PostgreSQL.'),
  ('Database Performance Tuning',
   'Indexes query optimization vacuum and analyze improve PostgreSQL performance.'),
  ('Redis for Caching',
   'Cache-aside and write-through patterns with Redis improve application response time.');

-- Search with ranking
SELECT id, title,
  ts_rank(
    to_tsvector('english', title || ' ' || body),
    to_tsquery('english', 'postgresql & database')
  ) AS rank
FROM pg_articles
WHERE to_tsvector('english', title || ' ' || body)
  @@ to_tsquery('english', 'postgresql & database')
ORDER BY rank DESC;
```

📸 **Verified Output:**
```
 id |             title             |    rank
----+-------------------------------+------------
  1 | Introduction to PostgreSQL    | 0.16898341
  3 | NoSQL vs Relational Databases | 0.03977115
  4 | Database Performance Tuning   | 0.03977115
(3 rows)
```

---

## Step 7 — PostgreSQL: Stored tsvector + ts_headline

```sql
-- Optimal: store tsvector as a generated column
ALTER TABLE pg_articles
  ADD COLUMN tsv TSVECTOR
    GENERATED ALWAYS AS (
      to_tsvector('english', title || ' ' || body)
    ) STORED;

DROP INDEX idx_pg_articles_tsv;
CREATE INDEX idx_tsv ON pg_articles USING GIN(tsv);

-- ts_headline: highlight matching terms
SELECT title,
  ts_headline(
    'english',
    body,
    to_tsquery('english', 'database | performance'),
    'StartSel=<b>, StopSel=</b>, MaxFragments=2'
  ) AS snippet
FROM pg_articles
WHERE tsv @@ to_tsquery('english', 'database | performance')
ORDER BY ts_rank(tsv, to_tsquery('english', 'database | performance')) DESC;
```

> 💡 `ts_headline` is expensive (re-parses the original text). Don't use it in large batch queries — apply it only to the final result set after ranking and filtering.

---

## Step 8 — Capstone: Multi-Language Full-Text Search System

```sql
-- Build a blog search engine with multiple languages
CREATE TABLE multilang_posts (
  id         SERIAL PRIMARY KEY,
  title      TEXT NOT NULL,
  content    TEXT NOT NULL,
  language   TEXT NOT NULL DEFAULT 'english',
  author     TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  tsv        TSVECTOR
);

-- Update tsv based on language
CREATE OR REPLACE FUNCTION update_post_tsv()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.tsv := to_tsvector(NEW.language::regconfig,
                         NEW.title || ' ' || NEW.content);
  RETURN NEW;
END;
$$;

CREATE TRIGGER post_tsv_update
BEFORE INSERT OR UPDATE ON multilang_posts
FOR EACH ROW EXECUTE FUNCTION update_post_tsv();

CREATE INDEX idx_multilang_tsv ON multilang_posts USING GIN(tsv);

INSERT INTO multilang_posts (title, content, language, author) VALUES
  ('PostgreSQL Full Text Search', 'Learn how to implement powerful search with tsvector and tsquery. Ranking and highlighting.', 'english', 'Alice'),
  ('Advanced Database Indexing', 'GIN and GiST indexes for full text, arrays, and geometric data in PostgreSQL.', 'english', 'Bob'),
  ('Query Optimization Tips', 'EXPLAIN ANALYZE reveals execution plans. Use indexes wisely to avoid sequential scans.', 'english', 'Carol');

-- Search function
CREATE OR REPLACE FUNCTION search_posts(
  p_query TEXT,
  p_lang  TEXT DEFAULT 'english',
  p_limit INT  DEFAULT 10
)
RETURNS TABLE(
  id        INT,
  title     TEXT,
  author    TEXT,
  rank      FLOAT4,
  snippet   TEXT
) LANGUAGE plpgsql AS $$
DECLARE
  v_query TSQUERY := to_tsquery(p_lang::regconfig, p_query);
BEGIN
  RETURN QUERY
    SELECT p.id, p.title, p.author,
           ts_rank(p.tsv, v_query),
           ts_headline(p.language::regconfig, p.content, v_query)
    FROM multilang_posts p
    WHERE p.tsv @@ v_query
    ORDER BY ts_rank(p.tsv, v_query) DESC
    LIMIT p_limit;
END;
$$;

SELECT * FROM search_posts('index & search');
```

---

## Summary

| Feature | MySQL FULLTEXT | PostgreSQL FTS |
|---------|---------------|----------------|
| Index type | FULLTEXT index | GIN on tsvector |
| Search syntax | `MATCH() AGAINST()` | `@@` operator |
| Modes | Natural Language, Boolean, Query Expansion | `tsquery` with `&`, `|`, `!`, `<->` |
| Ranking | Built-in relevance score | `ts_rank()`, `ts_rank_cd()` |
| Highlighting | Not built-in | `ts_headline()` |
| Stored document | Not available | `TSVECTOR` column + trigger |
| Language support | Via ft_stopword_file | Multiple regconfig (english, french, etc.) |
