# Lab 5: Advanced JDBC — Window Functions, CTEs & Upsert

## Objective
Go beyond basic CRUD with SQLite: SQL window functions (`RANK`, `SUM OVER`), recursive and non-recursive CTEs, `ON CONFLICT DO UPDATE` upsert, `CREATE INDEX` performance, batch-insert 100 orders, and JSON extraction with `json_extract()`.

## Background
Window functions compute aggregates across a "window" of rows relative to each row — without collapsing the result set like `GROUP BY`. They're indispensable for rankings, running totals, moving averages, and percentile analysis. CTEs (`WITH`) make complex queries readable by naming sub-queries. These are standard SQL 2003 features supported by SQLite 3.25+, PostgreSQL, MySQL 8+, and SQL Server.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 10 (JDBC & SQLite)

## Tools
- Docker: `zchencow/innozverse-java:latest`
- SQLite JDBC (via Maven)

---

## Lab Instructions

### Steps 1–8: Schema + batch insert, window RANK, running total SUM OVER, CTE rollup, JSON functions, upsert, partial index, Capstone

```bash
# Step 1: Download JDBC driver (first run only)
docker run --rm zchencow/innozverse-java:latest sh -c "
mvn dependency:get \
  -Dartifact=org.xerial:sqlite-jdbc:3.47.0.0 \
  -Dmaven.repo.local=/tmp/repo -q 2>/dev/null && \
ls /tmp/repo/org/xerial/sqlite-jdbc/3.47.0.0/*.jar"
```

```bash
cat > /tmp/AdvLab05.java << 'JAVAEOF'
import java.sql.*;
import java.util.*;

public class AdvLab05 {
    public static void main(String[] args) throws Exception {
        Class.forName("org.sqlite.JDBC");
        try (var conn = DriverManager.getConnection("jdbc:sqlite::memory:")) {
            conn.setAutoCommit(false);
            conn.createStatement().executeUpdate("PRAGMA journal_mode=WAL");
            conn.createStatement().executeUpdate(
                "CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, stock INTEGER)");
            conn.createStatement().executeUpdate(
                "CREATE TABLE orders(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, qty INTEGER, total REAL, region TEXT)");

            // Batch insert products
            try (var ps = conn.prepareStatement("INSERT INTO products VALUES(?,?,?,?,?)")) {
                Object[][] products = {
                    {1,"Surface Pro","Laptop",864.0,15},{2,"Surface Pen","Accessory",49.99,80},
                    {3,"Office 365","Software",99.99,999},{4,"USB-C Hub","Hardware",29.99,0},
                    {5,"Surface Book","Laptop",1299.0,5}};
                for (var r : products) {
                    ps.setInt(1,(int)r[0]); ps.setString(2,(String)r[1]);
                    ps.setString(3,(String)r[2]); ps.setDouble(4,(double)r[3]); ps.setInt(5,(int)r[4]);
                    ps.addBatch();
                }
                ps.executeBatch();
            }
            // Batch insert 100 orders
            var rng = new Random(42);
            String[] regions = {"North","South","East","West"};
            double[] prices = {864.0,49.99,99.99,29.99,1299.0};
            try (var ps = conn.prepareStatement("INSERT INTO orders(product_id,qty,total,region) VALUES(?,?,?,?)")) {
                for (int i = 0; i < 100; i++) {
                    int pid = rng.nextInt(5)+1; int qty = rng.nextInt(10)+1;
                    ps.setInt(1,pid); ps.setInt(2,qty); ps.setDouble(3,prices[pid-1]*qty);
                    ps.setString(4,regions[rng.nextInt(4)]); ps.addBatch();
                }
                ps.executeBatch();
            }
            conn.commit();
            System.out.println("Seeded 5 products + 100 orders");

            // Window function: RANK by revenue within category + overall
            System.out.println("\n=== Window Functions: Revenue Rank ===");
            var rs = conn.createStatement().executeQuery(
                "SELECT p.name, p.category, SUM(o.total) as revenue," +
                " RANK() OVER(PARTITION BY p.category ORDER BY SUM(o.total) DESC) as cat_rank," +
                " RANK() OVER(ORDER BY SUM(o.total) DESC) as overall_rank" +
                " FROM products p JOIN orders o ON p.id=o.product_id" +
                " GROUP BY p.id ORDER BY overall_rank");
            while (rs.next())
                System.out.printf("  #%-2d [cat#%d] %-15s %-10s $%,.0f%n",
                    rs.getInt("overall_rank"), rs.getInt("cat_rank"),
                    rs.getString("name"), rs.getString("category"), rs.getDouble("revenue"));

            // Running total with SUM OVER
            System.out.println("\n=== Running Total (SUM OVER) ===");
            rs = conn.createStatement().executeQuery(
                "SELECT region, SUM(total) as region_revenue," +
                " SUM(SUM(total)) OVER(ORDER BY SUM(total) DESC) as running_total" +
                " FROM orders GROUP BY region ORDER BY region_revenue DESC");
            while (rs.next())
                System.out.printf("  %-6s rev=$%,.0f  running=$%,.0f%n",
                    rs.getString("region"), rs.getDouble("region_revenue"), rs.getDouble("running_total"));

            // CTE: category rollup with % share
            System.out.println("\n=== CTE: Category Rollup ===");
            rs = conn.createStatement().executeQuery(
                "WITH stats AS (SELECT p.category, COUNT(DISTINCT p.id) cnt, SUM(o.qty) units, SUM(o.total) revenue" +
                " FROM products p JOIN orders o ON p.id=o.product_id GROUP BY p.category)," +
                " totals AS (SELECT SUM(revenue) grand FROM stats)" +
                " SELECT s.*, ROUND(s.revenue*100.0/t.grand,1) pct FROM stats s, totals t ORDER BY s.revenue DESC");
            while (rs.next())
                System.out.printf("  %-12s products=%d  units=%4d  revenue=$%,.0f  (%.1f%%)%n",
                    rs.getString("category"), rs.getInt("cnt"), rs.getInt("units"),
                    rs.getDouble("revenue"), rs.getDouble("pct"));

            // JSON functions
            System.out.println("\n=== JSON in SQLite ===");
            conn.createStatement().executeUpdate("CREATE TABLE events(id INTEGER PRIMARY KEY, payload TEXT)");
            try (var ps = conn.prepareStatement("INSERT INTO events(payload) VALUES(?)")) {
                ps.setString(1, "{\"type\":\"order\",\"product\":\"Surface Pro\",\"amount\":864.0,\"region\":\"US\"}"); ps.executeUpdate();
                ps.setString(1, "{\"type\":\"refund\",\"product\":\"USB-C Hub\",\"amount\":29.99,\"region\":\"EU\"}"); ps.executeUpdate();
            }
            conn.commit();
            rs = conn.createStatement().executeQuery(
                "SELECT json_extract(payload,'$.type') as type, json_extract(payload,'$.product') as product, " +
                "json_extract(payload,'$.amount') as amount FROM events");
            while (rs.next())
                System.out.printf("  %-8s  %-15s  $%.2f%n", rs.getString("type"), rs.getString("product"), rs.getDouble("amount"));

            // Upsert (ON CONFLICT DO UPDATE)
            System.out.println("\n=== Upsert ===");
            conn.createStatement().executeUpdate(
                "CREATE TABLE price_cache(product_id INTEGER PRIMARY KEY, live_price REAL)");
            conn.createStatement().executeUpdate("INSERT INTO price_cache VALUES(1,820.0),(2,47.5)");
            conn.commit();
            try (var ps = conn.prepareStatement(
                    "INSERT INTO price_cache(product_id,live_price) VALUES(?,?) " +
                    "ON CONFLICT(product_id) DO UPDATE SET live_price=excluded.live_price")) {
                ps.setInt(1,1); ps.setDouble(2,799.99); ps.executeUpdate(); // update existing
                ps.setInt(1,3); ps.setDouble(2,95.00);  ps.executeUpdate(); // insert new
            }
            conn.commit();
            rs = conn.createStatement().executeQuery("SELECT * FROM price_cache ORDER BY product_id");
            while (rs.next())
                System.out.printf("  pid=%-2d  $%.2f%n", rs.getInt("product_id"), rs.getDouble("live_price"));
        }
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab05.java:/tmp/AdvLab05.java zchencow/innozverse-java:latest sh -c "
mvn dependency:get -Dartifact=org.xerial:sqlite-jdbc:3.47.0.0 -Dmaven.repo.local=/tmp/repo -q 2>/dev/null
JDBC=/tmp/repo/org/xerial/sqlite-jdbc/3.47.0.0/sqlite-jdbc-3.47.0.0.jar
javac -cp \$JDBC /tmp/AdvLab05.java -d /tmp && java -cp /tmp:\$JDBC AdvLab05"
```

> 💡 **Window functions don't reduce rows.** Unlike `GROUP BY` which collapses N rows into 1, `RANK() OVER(...)` assigns a rank to every row while keeping all rows in the result. `PARTITION BY category` resets the rank counter for each category. `ORDER BY SUM(total) DESC` inside the window determines ranking direction. This is how you get "rank within group" without a self-join.

**📸 Verified Output:**
```
Seeded 5 products + 100 orders

=== Window Functions: Revenue Rank ===
  #1  [cat#1] Surface Book    Laptop     $131,199
  #2  [cat#2] Surface Pro     Laptop     $95,040
  #3  [cat#1] Office 365      Software   $10,199
  ...

=== CTE: Category Rollup ===
  Laptop       products=2  units= 211  revenue=$226,239  (91.7%)
  Software     products=1  units= 102  revenue=$10,199   (4.1%)
  ...

=== Upsert ===
  pid=1   $799.99
  pid=2   $47.50
  pid=3   $95.00
```

---

## Summary

| SQL Feature | Syntax | Use for |
|-------------|--------|---------|
| Window RANK | `RANK() OVER(PARTITION BY x ORDER BY y)` | Rank within group |
| Running total | `SUM(col) OVER(ORDER BY x)` | Cumulative sum |
| CTE | `WITH name AS (SELECT ...)` | Named sub-query |
| Upsert | `ON CONFLICT(pk) DO UPDATE SET` | Insert or update |
| JSON extract | `json_extract(col, '$.key')` | Query JSON column |

## Further Reading
- [SQLite Window Functions](https://www.sqlite.org/windowfunctions.html)
- [SQL CTEs](https://www.sqlite.org/lang_with.html)
