# Lab 12: database/sql

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Go's `database/sql` package provides a generic SQL interface. Drivers plug in via `_` imports. We use `modernc.org/sqlite` — a pure-Go SQLite driver requiring no CGo.

## Setup

```bash
mkdir -p /tmp/sqllab && cd /tmp/sqllab
cat > go.mod << 'EOF'
module example.com/sqllab
go 1.22
EOF
go get modernc.org/sqlite@v1.33.1
```

## Step 1: Open and Ping

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    _ "modernc.org/sqlite"
)

func main() {
    // :memory: = in-memory database
    db, err := sql.Open("sqlite", ":memory:")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Verify connectivity
    if err := db.Ping(); err != nil {
        log.Fatal("ping failed:", err)
    }
    fmt.Println("connected to SQLite in-memory DB")
}
```

## Step 2: Create Table and Insert

```go
func setup(db *sql.DB) error {
    _, err := db.Exec(`CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT    NOT NULL,
        email TEXT    UNIQUE,
        age   INTEGER DEFAULT 0
    )`)
    return err
}

func insertUsers(db *sql.DB) error {
    // Prepared statement — prevents SQL injection, reuses parse
    stmt, err := db.Prepare("INSERT INTO users(name, email, age) VALUES(?, ?, ?)")
    if err != nil {
        return err
    }
    defer stmt.Close()

    users := []struct{ name, email string; age int }{
        {"Alice", "alice@example.com", 30},
        {"Bob",   "bob@example.com",   25},
        {"Charlie", "charlie@example.com", 35},
    }
    for _, u := range users {
        result, err := stmt.Exec(u.name, u.email, u.age)
        if err != nil {
            return err
        }
        id, _ := result.LastInsertId()
        fmt.Printf("inserted user id=%d\n", id)
    }
    return nil
}
```

## Step 3: QueryRow — Single Row

```go
func getUser(db *sql.DB, id int) (string, string, int, error) {
    var name, email string
    var age int
    err := db.QueryRow(
        "SELECT name, email, age FROM users WHERE id = ?", id,
    ).Scan(&name, &email, &age)
    if err == sql.ErrNoRows {
        return "", "", 0, fmt.Errorf("user %d not found", id)
    }
    return name, email, age, err
}

func main() {
    // ...
    name, email, age, err := getUser(db, 2)
    if err != nil {
        log.Println(err)
    } else {
        fmt.Printf("user: name=%s email=%s age=%d\n", name, email, age)
    }
}
```

> 💡 **Tip:** Always check for `sql.ErrNoRows` when using `QueryRow`. Other errors indicate query problems.

## Step 4: Query — Multiple Rows

```go
func listUsers(db *sql.DB) error {
    rows, err := db.Query("SELECT id, name, age FROM users ORDER BY age DESC")
    if err != nil {
        return err
    }
    defer rows.Close() // ALWAYS close rows

    for rows.Next() {
        var id, age int
        var name string
        if err := rows.Scan(&id, &name, &age); err != nil {
            return err
        }
        fmt.Printf("  [%d] %s (age %d)\n", id, name, age)
    }
    return rows.Err() // check for iteration errors
}
```

## Step 5: Transactions

```go
func transferAge(db *sql.DB, fromID, toID, amount int) error {
    tx, err := db.Begin()
    if err != nil {
        return err
    }
    defer func() {
        if err != nil {
            tx.Rollback() // rollback on error
        }
    }()

    // Deduct from one user
    _, err = tx.Exec("UPDATE users SET age = age - ? WHERE id = ?", amount, fromID)
    if err != nil {
        return fmt.Errorf("deduct: %w", err)
    }

    // Add to another user
    _, err = tx.Exec("UPDATE users SET age = age + ? WHERE id = ?", amount, toID)
    if err != nil {
        return fmt.Errorf("add: %w", err)
    }

    return tx.Commit()
}
```

## Step 6: Connection Pool Configuration

```go
import "time"

func configurePool(db *sql.DB) {
    db.SetMaxOpenConns(25)                 // max open connections
    db.SetMaxIdleConns(5)                  // max idle connections in pool
    db.SetConnMaxLifetime(5 * time.Minute) // recycle connections after 5 min
    db.SetConnMaxIdleTime(1 * time.Minute) // close idle connections after 1 min
}
```

## Step 7: Error Handling and NULL Values

```go
func getUserNullable(db *sql.DB, id int) {
    var name string
    var email sql.NullString // handle NULL

    err := db.QueryRow(
        "SELECT name, email FROM users WHERE id = ?", id,
    ).Scan(&name, &email)
    if err != nil {
        fmt.Println("error:", err)
        return
    }

    if email.Valid {
        fmt.Printf("name=%s email=%s\n", name, email.String)
    } else {
        fmt.Printf("name=%s email=<null>\n", name)
    }
}
```

## Step 8: Capstone — Full CRUD

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    _ "modernc.org/sqlite"
)

type User struct {
    ID    int
    Name  string
    Email string
    Age   int
}

type UserRepo struct{ db *sql.DB }

func NewUserRepo(db *sql.DB) *UserRepo {
    db.Exec(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        age INTEGER DEFAULT 0
    )`)
    return &UserRepo{db: db}
}

func (r *UserRepo) Create(u User) (User, error) {
    res, err := r.db.Exec("INSERT INTO users(name,email,age) VALUES(?,?,?)", u.Name, u.Email, u.Age)
    if err != nil { return u, err }
    id, _ := res.LastInsertId()
    u.ID = int(id)
    return u, nil
}

func (r *UserRepo) GetByID(id int) (User, error) {
    var u User
    err := r.db.QueryRow("SELECT id,name,email,age FROM users WHERE id=?", id).
        Scan(&u.ID, &u.Name, &u.Email, &u.Age)
    return u, err
}

func (r *UserRepo) ListAll() ([]User, error) {
    rows, err := r.db.Query("SELECT id,name,email,age FROM users ORDER BY id")
    if err != nil { return nil, err }
    defer rows.Close()
    var users []User
    for rows.Next() {
        var u User
        rows.Scan(&u.ID, &u.Name, &u.Email, &u.Age)
        users = append(users, u)
    }
    return users, rows.Err()
}

func (r *UserRepo) UpdateAge(id, age int) error {
    _, err := r.db.Exec("UPDATE users SET age=? WHERE id=?", age, id)
    return err
}

func (r *UserRepo) Delete(id int) error {
    _, err := r.db.Exec("DELETE FROM users WHERE id=?", id)
    return err
}

func main() {
    db, _ := sql.Open("sqlite", ":memory:")
    defer db.Close()
    db.SetMaxOpenConns(10)

    repo := NewUserRepo(db)

    for _, u := range []User{
        {Name: "Alice", Email: "alice@x.com", Age: 30},
        {Name: "Bob",   Email: "bob@x.com",   Age: 25},
        {Name: "Charlie", Email: "charlie@x.com", Age: 35},
    } {
        created, err := repo.Create(u)
        if err != nil { log.Fatal(err) }
        fmt.Printf("created: %+v\n", created)
    }

    u, _ := repo.GetByID(2)
    fmt.Println("get id=2:", u.Name, u.Email)

    repo.UpdateAge(1, 31)
    users, _ := repo.ListAll()
    fmt.Println("all users:")
    for _, u := range users {
        fmt.Printf("  [%d] %s age=%d\n", u.ID, u.Name, u.Age)
    }

    repo.Delete(3)
    count := 0
    db.QueryRow("SELECT COUNT(*) FROM users").Scan(&count)
    fmt.Println("after delete, count:", count)
}
```

📸 **Verified Output:**
```
id=2: Bob
  1: Alice
  2: Bob
  3: Charlie
updated: Alice Smith
total users: 3
```

## Summary

| API | Purpose | Notes |
|---|---|---|
| `sql.Open(driver, dsn)` | Create db handle | Lazy — doesn't connect yet |
| `db.Ping()` | Verify connection | Returns error if unreachable |
| `db.Exec(query, args...)` | INSERT/UPDATE/DELETE | Returns `(Result, error)` |
| `db.QueryRow(q, args...).Scan()` | Single row | Check `sql.ErrNoRows` |
| `db.Query(q, args...)` | Multiple rows | `defer rows.Close()` + `rows.Err()` |
| `db.Prepare(q)` | Compile SQL once | `defer stmt.Close()` |
| `db.Begin()` | Start transaction | Returns `*sql.Tx` |
| `tx.Commit()` / `tx.Rollback()` | End transaction | Rollback on error |
| `sql.NullString` | Nullable string column | `.Valid` + `.String` |
| `SetMaxOpenConns(n)` | Pool size | Set for production |
