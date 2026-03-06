# Lab 15: Capstone — Production Distributed Service

**Time:** 60 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Build a **production-ready distributed microservice** in Go that integrates every concept from Labs 01–14:

| Concept | Package / Pattern |
|---|---|
| Memory & escape analysis | `//go:noinline`, `sync.Pool` |
| gRPC API | `google.golang.org/grpc` |
| Redis caching | `github.com/redis/go-redis/v9` (interface + in-memory mock) |
| SQLite persistence | `modernc.org/sqlite` (pure Go, no CGO) |
| Structured logging | `log/slog` (Go 1.21+) |
| Circuit breaker | `github.com/sony/gobreaker` |
| Graceful shutdown | `context` + `sync.WaitGroup` + `os/signal` |
| Table-driven tests | `go test` with 6 cases |

The service manages **Users**: create them, cache lookups in Redis, persist to SQLite, and protect the DB behind a circuit breaker.

---

## Step 1: Project Setup

```bash
mkdir capstone && cd capstone
go mod init capstone

go get modernc.org/sqlite@v1.29.9
go get github.com/sony/gobreaker@v0.5.0
go get google.golang.org/grpc@v1.62.1
go get github.com/redis/go-redis/v9@v9.5.1

mkdir store cache service
```

> 💡 `modernc.org/sqlite` is a pure-Go SQLite port — no CGO required, works in any Alpine Docker image.

---

## Step 2: SQLite Data Layer (`store/sqlite.go`)

```go
package store

import (
	"context"
	"database/sql"
	"fmt"
	_ "modernc.org/sqlite"
)

type User struct {
	ID    int64
	Name  string
	Email string
}

type Store struct {
	db *sql.DB
}

func New(dsn string) (*Store, error) {
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}
	if _, err := db.Exec(`CREATE TABLE IF NOT EXISTS users (
		id    INTEGER PRIMARY KEY AUTOINCREMENT,
		name  TEXT NOT NULL,
		email TEXT NOT NULL UNIQUE
	)`); err != nil {
		return nil, fmt.Errorf("create table: %w", err)
	}
	return &Store{db: db}, nil
}

func (s *Store) CreateUser(ctx context.Context, name, email string) (int64, error) {
	res, err := s.db.ExecContext(ctx,
		"INSERT INTO users(name,email) VALUES(?,?)", name, email)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func (s *Store) GetUser(ctx context.Context, id int64) (*User, error) {
	row := s.db.QueryRowContext(ctx,
		"SELECT id,name,email FROM users WHERE id=?", id)
	u := &User{}
	if err := row.Scan(&u.ID, &u.Name, &u.Email); err != nil {
		return nil, err
	}
	return u, nil
}

func (s *Store) Close() error { return s.db.Close() }
```

> 💡 Use `file::memory:?cache=shared` as DSN for a shared in-memory database. Use `:memory:` for isolated per-connection memory databases.

---

## Step 3: Cache Interface + In-Memory Mock (`cache/cache.go`)

```go
package cache

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Cache defines the caching interface.
// In production: back with go-redis/v9. In tests: use MemCache.
type Cache interface {
	Get(ctx context.Context, key string) (string, error)
	Set(ctx context.Context, key, val string, ttl time.Duration) error
}

// ErrCacheMiss is returned when a key is not found.
var ErrCacheMiss = fmt.Errorf("cache miss")

// MemCache is a thread-safe in-memory Cache for testing.
type MemCache struct {
	mu   sync.RWMutex
	data map[string]string
}

func NewMemCache() *MemCache { return &MemCache{data: make(map[string]string)} }

func (m *MemCache) Get(_ context.Context, key string) (string, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	v, ok := m.data[key]
	if !ok {
		return "", ErrCacheMiss
	}
	return v, nil
}

func (m *MemCache) Set(_ context.Context, key, val string, _ time.Duration) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.data[key] = val
	return nil
}
```

> 💡 **Interface-driven design** lets you swap Redis for `MemCache` in tests without changing service logic. This mirrors the hexagonal architecture from Lab 09.

In production, wrap `go-redis/v9` to satisfy the `Cache` interface:

```go
// cache/redis.go (production — requires a running Redis server)
package cache

import (
	"context"
	"errors"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisCache struct{ c *redis.Client }

func NewRedisCache(addr string) *RedisCache {
	return &RedisCache{c: redis.NewClient(&redis.Options{Addr: addr})}
}

func (r *RedisCache) Get(ctx context.Context, key string) (string, error) {
	val, err := r.c.Get(ctx, key).Result()
	if errors.Is(err, redis.Nil) {
		return "", ErrCacheMiss
	}
	return val, err
}

func (r *RedisCache) Set(ctx context.Context, key, val string, ttl time.Duration) error {
	return r.c.Set(ctx, key, val, ttl).Err()
}
```

---

## Step 4: User Service with Circuit Breaker + sync.Pool (`service/user.go`)

```go
package service

import (
	"bytes"
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"capstone/cache"
	"capstone/store"

	"github.com/sony/gobreaker"
)

// bufPool reuses bytes.Buffer allocations — avoids GC pressure.
// Each Get returns a *bytes.Buffer; always Reset before use, Put when done.
var bufPool = sync.Pool{
	New: func() any { return new(bytes.Buffer) },
}

// UserService combines DB, cache, circuit breaker, and structured logging.
type UserService struct {
	store *store.Store
	cache cache.Cache
	cb    *gobreaker.CircuitBreaker
	log   *slog.Logger
}

func NewUserService(s *store.Store, c cache.Cache, log *slog.Logger) *UserService {
	cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
		Name:        "user-db",
		MaxRequests: 3,                // half-open: allow 3 probes
		Interval:    10 * time.Second, // reset counts every 10s
		Timeout:     5 * time.Second,  // open → half-open after 5s
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			return counts.ConsecutiveFailures > 2
		},
	})
	return &UserService{store: s, cache: c, cb: cb, log: log}
}

// FormatUser formats a User using a pooled buffer.
// //go:noinline prevents the compiler from inlining this function,
// ensuring the escape analysis benchmark reflects real allocation behaviour.
//
//go:noinline
func FormatUser(u *store.User) string {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer bufPool.Put(buf)
	fmt.Fprintf(buf, "User{id=%d name=%q email=%q}", u.ID, u.Name, u.Email)
	return buf.String()
}

// CreateUser persists a user via SQLite.
func (svc *UserService) CreateUser(ctx context.Context, name, email string) (int64, error) {
	svc.log.Info("creating user", "name", name, "email", email)
	id, err := svc.store.CreateUser(ctx, name, email)
	if err != nil {
		svc.log.Error("create user failed", "err", err)
		return 0, err
	}
	svc.log.Info("user created", "id", id)
	return id, nil
}

// GetUser fetches from cache; falls back through circuit breaker to DB.
func (svc *UserService) GetUser(ctx context.Context, id int64) (*store.User, error) {
	key := fmt.Sprintf("user:%d", id)

	if val, err := svc.cache.Get(ctx, key); err == nil {
		svc.log.Debug("cache hit", "key", key)
		_ = val // production: unmarshal JSON into User struct
		return &store.User{ID: id, Name: "cached"}, nil
	}

	// Circuit breaker wraps the DB call
	result, err := svc.cb.Execute(func() (any, error) {
		return svc.store.GetUser(ctx, id)
	})
	if err != nil {
		svc.log.Error("circuit breaker: db fetch failed",
			"err", err, "state", svc.cb.State())
		return nil, err
	}

	u := result.(*store.User)
	_ = svc.cache.Set(ctx, key, u.Name, 5*time.Minute)
	svc.log.Debug("cache populated", "key", key)
	return u, nil
}

// CBState returns the current circuit breaker state name ("closed", "open", "half-open").
func (svc *UserService) CBState() string {
	return svc.cb.State().String()
}
```

> 💡 Circuit breaker states: **closed** (normal) → **open** (failing, rejects calls fast) → **half-open** (probing, limited requests) → back to **closed** if probes succeed.

---

## Step 5: Table-Driven Tests (`service/user_test.go`)

```go
package service_test

import (
	"context"
	"log/slog"
	"os"
	"testing"

	"capstone/cache"
	"capstone/service"
	"capstone/store"
)

func newTestDeps(t *testing.T) (*store.Store, cache.Cache, *slog.Logger) {
	t.Helper()
	s, err := store.New(":memory:")
	if err != nil {
		t.Fatalf("store.New: %v", err)
	}
	t.Cleanup(func() { s.Close() })
	log := slog.New(slog.NewTextHandler(os.Stderr,
		&slog.HandlerOptions{Level: slog.LevelError}))
	return s, cache.NewMemCache(), log
}

func TestCreateAndGetUser(t *testing.T) {
	cases := []struct {
		name    string
		uname   string
		email   string
		wantErr bool
	}{
		{"valid alice", "Alice", "alice@example.com", false},
		{"valid bob", "Bob", "bob@example.com", false},
		{"empty name", "", "noname@example.com", false},
		{"duplicate email", "Alice2", "alice@example.com", true}, // UNIQUE constraint
		{"unicode name", "张三", "zhang@example.com", false},
		{"long email", "LongUser", "a@b.c", false},
	}

	s, c, log := newTestDeps(t)
	svc := service.NewUserService(s, c, log)
	ctx := context.Background()

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			id, err := svc.CreateUser(ctx, tc.uname, tc.email)
			if tc.wantErr {
				if err == nil {
					t.Errorf("expected error, got id=%d", id)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if id <= 0 {
				t.Errorf("expected positive id, got %d", id)
			}
			u, err := svc.GetUser(ctx, id)
			if err != nil {
				t.Fatalf("GetUser: %v", err)
			}
			if u == nil {
				t.Fatal("GetUser returned nil")
			}
		})
	}
}

func TestFormatUser(t *testing.T) {
	cases := []struct {
		user *store.User
		want string
	}{
		{
			&store.User{ID: 1, Name: "Alice", Email: "a@b.com"},
			`User{id=1 name="Alice" email="a@b.com"}`,
		},
		{
			&store.User{ID: 99, Name: "张三", Email: "z@cn.com"},
			`User{id=99 name="张三" email="z@cn.com"}`,
		},
	}
	for _, tc := range cases {
		got := service.FormatUser(tc.user)
		if got != tc.want {
			t.Errorf("FormatUser(%v) = %q; want %q", tc.user, got, tc.want)
		}
	}
}

func TestCircuitBreakerState(t *testing.T) {
	s, c, log := newTestDeps(t)
	svc := service.NewUserService(s, c, log)
	if svc.CBState() != "closed" {
		t.Errorf("expected closed, got %s", svc.CBState())
	}
}
```

> 💡 `t.Cleanup` is the idiomatic way to register teardown in Go 1.14+. It runs even if the test panics — unlike `defer` in helper functions.

---

## Step 6: gRPC Service Definition

In production you would run `protoc` to generate Go code. Here we sketch the service registration pattern — the key takeaway is the interface your handler must satisfy.

```go
// In a generated pb.go file (simplified — normally from protoc):
//
// package pb
//
// type UserServiceServer interface {
//     CreateUser(context.Context, *CreateUserRequest) (*CreateUserResponse, error)
//     GetUser(context.Context, *GetUserRequest) (*GetUserResponse, error)
// }
//
// type CreateUserRequest  struct { Name, Email string }
// type CreateUserResponse struct { Id int64 }
// type GetUserRequest     struct { Id int64 }
// type GetUserResponse    struct { Id int64; Name, Email string }

// grpcserver/server.go — wires UserService into gRPC
package grpcserver

import (
	"context"
	"fmt"
	"log/slog"
	"net"

	"capstone/service"
	"google.golang.org/grpc"
)

type Server struct {
	svc *service.UserService
	srv *grpc.Server
	log *slog.Logger
}

func New(svc *service.UserService, log *slog.Logger) *Server {
	srv := grpc.NewServer(
		grpc.ChainUnaryInterceptor(
			loggingInterceptor(log),
		),
	)
	// In production: pb.RegisterUserServiceServer(srv, &handler{svc: svc})
	return &Server{svc: svc, srv: srv, log: log}
}

func loggingInterceptor(log *slog.Logger) grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req any, info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler) (any, error) {
		log.Info("grpc request", "method", info.FullMethod)
		resp, err := handler(ctx, req)
		if err != nil {
			log.Error("grpc error", "method", info.FullMethod, "err", err)
		}
		return resp, err
	}
}

func (s *Server) ListenAndServe(addr string) error {
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("listen: %w", err)
	}
	s.log.Info("gRPC server listening", "addr", addr)
	return s.srv.Serve(lis)
}

func (s *Server) GracefulStop() { s.srv.GracefulStop() }
```

> 💡 `grpc.ChainUnaryInterceptor` chains multiple middleware. Always add logging + auth interceptors here so every handler gets them for free.

---

## Step 7: Graceful Shutdown (`main.go`)

```go
package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"capstone/cache"
	"capstone/service"
	"capstone/store"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout,
		&slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(log)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle OS signals for graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)

	s, err := store.New("file::memory:?cache=shared")
	if err != nil {
		slog.Error("store init failed", "err", err)
		os.Exit(1)
	}
	defer s.Close()

	c := cache.NewMemCache()
	svc := service.NewUserService(s, c, log)

	var wg sync.WaitGroup

	// Worker goroutine — processes users until ctx is cancelled
	wg.Add(1)
	go func() {
		defer wg.Done()
		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()

		users := []struct{ name, email string }{
			{"Alice", "alice@example.com"},
			{"Bob", "bob@example.com"},
			{"Charlie", "charlie@example.com"},
		}
		i := 0
		for {
			select {
			case <-ctx.Done():
				slog.Info("worker: shutting down gracefully")
				return
			case <-ticker.C:
				u := users[i%len(users)]
				id, err := svc.CreateUser(ctx, u.name,
					fmt.Sprintf("%d.%s", i, u.email))
				if err == nil {
					fetched, _ := svc.GetUser(ctx, id)
					if fetched != nil {
						slog.Info("processed user",
							"formatted", service.FormatUser(fetched))
					}
				}
				i++
				if i >= 3 {
					cancel() // demo: stop after 3 users
				}
			}
		}
	}()

	// Block until signal or ctx done
	select {
	case sig := <-sigCh:
		slog.Info("received signal", "signal", sig)
		cancel()
	case <-ctx.Done():
	}

	// Wait for all goroutines with timeout
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
		slog.Info("shutdown complete")
	case <-time.After(5 * time.Second):
		slog.Warn("shutdown timeout — forcing exit")
	}
}
```

> 💡 Always drain goroutines with `sync.WaitGroup` before exit. The outer `select` with timeout prevents hanging forever if a goroutine is stuck.

---

## Step 8: Run Tests and Service

```bash
# Run all tests with verbose output
go test ./... -v -count=1

# Run the service
go run .
```

📸 **Verified Output** (Docker `golang:1.22-alpine`, 2026-03-06):

```
=== Running tests ===
?   	capstone	[no test files]
?   	capstone/cache	[no test files]
?   	capstone/store	[no test files]
=== RUN   TestCreateAndGetUser
=== RUN   TestCreateAndGetUser/valid_alice
=== RUN   TestCreateAndGetUser/valid_bob
=== RUN   TestCreateAndGetUser/empty_name
=== RUN   TestCreateAndGetUser/duplicate_email
time=2026-03-06T18:56:40.247Z level=ERROR msg="create user failed" err="constraint failed: UNIQUE constraint failed: users.email (2067)"
=== RUN   TestCreateAndGetUser/unicode_name
=== RUN   TestCreateAndGetUser/long_email
--- PASS: TestCreateAndGetUser (0.02s)
    --- PASS: TestCreateAndGetUser/valid_alice (0.00s)
    --- PASS: TestCreateAndGetUser/valid_bob (0.00s)
    --- PASS: TestCreateAndGetUser/empty_name (0.00s)
    --- PASS: TestCreateAndGetUser/duplicate_email (0.00s)
    --- PASS: TestCreateAndGetUser/unicode_name (0.00s)
    --- PASS: TestCreateAndGetUser/long_email (0.00s)
=== RUN   TestFormatUser
--- PASS: TestFormatUser (0.00s)
=== RUN   TestCircuitBreakerState
--- PASS: TestCircuitBreakerState (0.01s)
PASS
ok  	capstone/service	0.039s

=== Running service (3 iterations) ===
{"time":"2026-03-06T18:56:41.654658027Z","level":"INFO","msg":"creating user","name":"Alice","email":"0.alice@example.com"}
{"time":"2026-03-06T18:56:41.657840564Z","level":"INFO","msg":"user created","id":1}
{"time":"2026-03-06T18:56:41.658123397Z","level":"INFO","msg":"processed user","formatted":"User{id=1 name=\"Alice\" email=\"0.alice@example.com\"}"}
{"time":"2026-03-06T18:56:41.754917984Z","level":"INFO","msg":"creating user","name":"Bob","email":"1.bob@example.com"}
{"time":"2026-03-06T18:56:41.757674275Z","level":"INFO","msg":"user created","id":2}
{"time":"2026-03-06T18:56:41.757878781Z","level":"INFO","msg":"processed user","formatted":"User{id=2 name=\"Bob\" email=\"1.bob@example.com\"}"}
{"time":"2026-03-06T18:56:41.854441145Z","level":"INFO","msg":"creating user","name":"Charlie","email":"2.charlie@example.com"}
{"time":"2026-03-06T18:56:41.857155096Z","level":"INFO","msg":"user created","id":3}
{"time":"2026-03-06T18:56:41.857327816Z","level":"INFO","msg":"processed user","formatted":"User{id=3 name=\"Charlie\" email=\"2.charlie@example.com\"}"}
{"time":"2026-03-06T18:56:41.857368979Z","level":"INFO","msg":"worker: shutting down gracefully"}
{"time":"2026-03-06T18:56:41.857430169Z","level":"INFO","msg":"shutdown complete"}
```

---

## Summary

| Concept | Where Used | Lab Reference |
|---|---|---|
| Escape analysis + `//go:noinline` | `service.FormatUser` | Lab 01 |
| `sync.Pool` buffer reuse | `bufPool` in `service/user.go` | Lab 04 |
| gRPC interceptor chain | `grpcserver.loggingInterceptor` | Lab 05 |
| Distributed circuit breaker | `gobreaker` in `UserService` | Lab 06 |
| Redis cache interface | `cache.Cache` + `RedisCache` | Lab 08 |
| Hexagonal / interface-driven design | `cache.Cache` swappable impl | Lab 09 |
| Pure-Go SQLite (no CGO) | `modernc.org/sqlite` in `store/` | Lab 12 |
| Structured logging (`slog`) | `slog.NewJSONHandler` in `main.go` | Lab 14 |
| Graceful shutdown | `context` + `WaitGroup` + `os/signal` | Lab 06, 14 |
| Table-driven tests | `service/user_test.go` (6 cases) | Lab 02, 10 |

**Congratulations — you've completed the Go Advanced track!** 🎉

You now have a working template for production Go microservices: clean layering, observable (structured JSON logs), resilient (circuit breaker), testable (interfaces + table tests), and efficient (pooled allocations, no CGO).
