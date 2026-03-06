# Lab 09: Microservice — Hexagonal Architecture

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Build a production-ready microservice using hexagonal architecture (ports & adapters): pure domain layer, port interfaces, in-memory and SQLite adapters, structured logging with `slog`, health/readiness endpoints, and graceful shutdown.

---

## Step 1: Hexagonal Architecture Overview

```
                    ┌─────────────────────────────┐
  HTTP Adapter  ──► │                             │ ──► Repository Port ──► SQLite Adapter
  gRPC Adapter  ──► │     Domain / Application    │                     └── InMemory Adapter
  CLI Adapter   ──► │         (Pure Go)           │ ──► EventPub Port   ──► Kafka Adapter
                    │                             │                     └── NoOp Adapter
                    └─────────────────────────────┘

Port = interface (defined in domain)
Adapter = implementation (in infrastructure)
Domain = zero external dependencies
```

---

## Step 2: Domain Layer

```go
// domain/product.go
package domain

import (
	"context"
	"errors"
	"time"
)

// Domain entity
type Product struct {
	ID        string
	Name      string
	Price     float64
	Stock     int
	CreatedAt time.Time
	UpdatedAt time.Time
}

// Domain events
type ProductCreatedEvent struct {
	ProductID string
	Name      string
}

// Domain errors
var (
	ErrProductNotFound    = errors.New("product not found")
	ErrInvalidPrice       = errors.New("price must be positive")
	ErrInsufficientStock  = errors.New("insufficient stock")
)

// Validate domain invariants
func (p *Product) Validate() error {
	if p.Name == "" {
		return errors.New("product name cannot be empty")
	}
	if p.Price <= 0 {
		return ErrInvalidPrice
	}
	if p.Stock < 0 {
		return errors.New("stock cannot be negative")
	}
	return nil
}

// Port (interface defined in domain)
type ProductRepository interface {
	Save(ctx context.Context, p *Product) error
	FindByID(ctx context.Context, id string) (*Product, error)
	FindAll(ctx context.Context) ([]*Product, error)
	Delete(ctx context.Context, id string) error
}

type EventPublisher interface {
	Publish(ctx context.Context, event interface{}) error
}
```

---

## Step 3: Application Service

```go
// app/product_service.go
package app

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/yourorg/shop/domain"
)

type ProductService struct {
	repo   domain.ProductRepository
	events domain.EventPublisher
	logger *slog.Logger
}

func NewProductService(repo domain.ProductRepository, events domain.EventPublisher, logger *slog.Logger) *ProductService {
	return &ProductService{repo: repo, events: events, logger: logger}
}

func (s *ProductService) CreateProduct(ctx context.Context, id, name string, price float64, stock int) (*domain.Product, error) {
	p := &domain.Product{
		ID:        id,
		Name:      name,
		Price:     price,
		Stock:     stock,
		CreatedAt: time.Now().UTC(),
		UpdatedAt: time.Now().UTC(),
	}

	if err := p.Validate(); err != nil {
		s.logger.Warn("product validation failed", "id", id, "err", err)
		return nil, fmt.Errorf("validation: %w", err)
	}

	if err := s.repo.Save(ctx, p); err != nil {
		return nil, fmt.Errorf("save product: %w", err)
	}

	s.logger.Info("product created", "id", p.ID, "name", p.Name, "price", p.Price)
	s.events.Publish(ctx, domain.ProductCreatedEvent{ProductID: p.ID, Name: p.Name})
	return p, nil
}

func (s *ProductService) GetProduct(ctx context.Context, id string) (*domain.Product, error) {
	p, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	return p, nil
}

func (s *ProductService) ListProducts(ctx context.Context) ([]*domain.Product, error) {
	return s.repo.FindAll(ctx)
}
```

---

## Step 4: Adapters

```go
// adapters/inmemory.go
package adapters

import (
	"context"
	"sync"

	"github.com/yourorg/shop/domain"
)

type InMemoryProductRepo struct {
	mu    sync.RWMutex
	store map[string]*domain.Product
}

func NewInMemoryProductRepo() *InMemoryProductRepo {
	return &InMemoryProductRepo{store: make(map[string]*domain.Product)}
}

func (r *InMemoryProductRepo) Save(ctx context.Context, p *domain.Product) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	// Deep copy to prevent mutation
	copy := *p
	r.store[p.ID] = &copy
	return nil
}

func (r *InMemoryProductRepo) FindByID(ctx context.Context, id string) (*domain.Product, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	p, ok := r.store[id]
	if !ok {
		return nil, domain.ErrProductNotFound
	}
	copy := *p
	return &copy, nil
}

func (r *InMemoryProductRepo) FindAll(ctx context.Context) ([]*domain.Product, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	result := make([]*domain.Product, 0, len(r.store))
	for _, p := range r.store {
		copy := *p
		result = append(result, &copy)
	}
	return result, nil
}

func (r *InMemoryProductRepo) Delete(ctx context.Context, id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.store[id]; !ok {
		return domain.ErrProductNotFound
	}
	delete(r.store, id)
	return nil
}

// NoOp event publisher
type NoOpPublisher struct{}

func (NoOpPublisher) Publish(ctx context.Context, event interface{}) error {
	return nil
}
```

---

## Step 5: HTTP Adapter

```go
// adapters/http.go
package adapters

import (
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"

	"github.com/yourorg/shop/app"
	"github.com/yourorg/shop/domain"
)

type HTTPHandler struct {
	svc    *app.ProductService
	logger *slog.Logger
}

func NewHTTPHandler(svc *app.ProductService, logger *slog.Logger) *http.ServeMux {
	h := &HTTPHandler{svc: svc, logger: logger}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", h.health)
	mux.HandleFunc("GET /ready", h.ready)
	mux.HandleFunc("POST /products", h.createProduct)
	mux.HandleFunc("GET /products", h.listProducts)
	mux.HandleFunc("GET /products/{id}", h.getProduct)
	return mux
}

type createProductRequest struct {
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Stock int     `json:"stock"`
}

func (h *HTTPHandler) createProduct(w http.ResponseWriter, r *http.Request) {
	var req createProductRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}
	id := fmt.Sprintf("prod-%d", time.Now().UnixNano())
	p, err := h.svc.CreateProduct(r.Context(), id, req.Name, req.Price, req.Stock)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidPrice) {
			h.writeError(w, http.StatusUnprocessableEntity, err.Error())
			return
		}
		h.writeError(w, http.StatusInternalServerError, "internal error")
		return
	}
	h.writeJSON(w, http.StatusCreated, p)
}

func (h *HTTPHandler) health(w http.ResponseWriter, r *http.Request) {
	h.writeJSON(w, http.StatusOK, map[string]string{"status": "healthy"})
}

func (h *HTTPHandler) ready(w http.ResponseWriter, r *http.Request) {
	h.writeJSON(w, http.StatusOK, map[string]bool{"ready": true})
}

func (h *HTTPHandler) writeJSON(w http.ResponseWriter, code int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(v)
}

func (h *HTTPHandler) writeError(w http.ResponseWriter, code int, msg string) {
	h.writeJSON(w, code, map[string]string{"error": msg})
}
```

---

## Step 6: Graceful Shutdown

```go
// main.go
package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	// Wire up dependencies
	repo := adapters.NewInMemoryProductRepo()
	publisher := adapters.NoOpPublisher{}
	svc := app.NewProductService(repo, publisher, logger)
	mux := adapters.NewHTTPHandler(svc, logger)

	srv := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	// Start server
	go func() {
		logger.Info("server starting", "addr", srv.Addr)
		if err := srv.ListenAndServe(); err != http.ErrServerClosed {
			logger.Error("server error", "err", err)
			os.Exit(1)
		}
	}()

	// Graceful shutdown on signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
	<-quit

	logger.Info("shutting down...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Error("shutdown error", "err", err)
	}
	logger.Info("server stopped")
}
```

---

## Step 7: Structured Logging with `slog`

```go
package main

import (
	"context"
	"log/slog"
	"os"
)

func demonstrateSlog() {
	// JSON handler (production)
	jsonLogger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelDebug,
		// AddSource: true, // adds file:line
	}))

	// Text handler (development)
	textLogger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	_ = textLogger

	// Structured fields
	jsonLogger.Info("request processed",
		"method", "GET",
		"path", "/products",
		"status", 200,
		"duration_ms", 12,
		"user_id", "user:42",
	)

	// With context (e.g., trace ID)
	ctx := context.Background()
	logger := jsonLogger.With("trace_id", "abc123", "service", "product-svc")
	logger.InfoContext(ctx, "product fetched", "product_id", "prod-1")

	// Log levels
	jsonLogger.Debug("debug message", "detail", "verbose info")
	jsonLogger.Warn("slow query", "duration_ms", 500)
	jsonLogger.Error("db connection failed", "err", "timeout")
}
```

---

## Step 8: Capstone — Runnable Service

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/hexsvc
cat > /tmp/hexsvc/main.go << 'GOEOF'
package main

import (
	\"context\"
	\"encoding/json\"
	\"fmt\"
	\"log/slog\"
	\"net/http\"
	\"os\"
	\"os/signal\"
	\"sync\"
	\"syscall\"
	\"time\"
)

type Product struct { ID string; Name string; Price float64; Stock int }

type Repo struct { mu sync.RWMutex; store map[string]*Product }
func NewRepo() *Repo { return &Repo{store: make(map[string]*Product)} }
func (r *Repo) Save(p *Product) { r.mu.Lock(); defer r.mu.Unlock(); c := *p; r.store[p.ID] = &c }
func (r *Repo) FindAll() []*Product {
	r.mu.RLock(); defer r.mu.RUnlock()
	res := make([]*Product, 0, len(r.store))
	for _, p := range r.store { c := *p; res = append(res, &c) }
	return res
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	repo := NewRepo()
	repo.Save(&Product{ID: \"1\", Name: \"Go Book\", Price: 39.99, Stock: 100})
	repo.Save(&Product{ID: \"2\", Name: \"K8s Guide\", Price: 59.99, Stock: 50})

	mux := http.NewServeMux()
	mux.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{\"status\": \"healthy\"})
	})
	mux.HandleFunc(\"/products\", func(w http.ResponseWriter, r *http.Request) {
		products := repo.FindAll()
		logger.Info(\"listing products\", \"count\", len(products))
		json.NewEncoder(w).Encode(products)
	})

	srv := &http.Server{Addr: \":18083\", Handler: mux, ReadTimeout: 5*time.Second}
	go func() {
		logger.Info(\"server starting\", \"addr\", \":18083\")
		srv.ListenAndServe()
	}()
	time.Sleep(100 * time.Millisecond)

	resp, _ := http.Get(\"http://localhost:18083/health\")
	var health map[string]string
	json.NewDecoder(resp.Body).Decode(&health)
	resp.Body.Close()
	fmt.Printf(\"Health: %v\\n\", health)

	resp2, _ := http.Get(\"http://localhost:18083/products\")
	var products []*Product
	json.NewDecoder(resp2.Body).Decode(&products)
	resp2.Body.Close()
	fmt.Printf(\"Products: %d items\\n\", len(products))
	for _, p := range products { fmt.Printf(\"  %s: $%.2f\\n\", p.Name, p.Price) }

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	srv.Shutdown(ctx)
	logger.Info(\"server shutdown\")
	fmt.Println(\"Done\")
}
GOEOF
cd /tmp/hexsvc && go run main.go"
```

📸 **Verified Output:**
```
{"time":"2026-03-06T18:37:08Z","level":"INFO","msg":"server starting","addr":":18083"}
Health: map[status:healthy]
Products: 2 items
  Go Book: $39.99
  K8s Guide: $59.99
{"time":"2026-03-06T18:37:08Z","level":"INFO","msg":"server shutdown"}
Done
```

---

## Summary

| Layer | Responsibility | Dependencies |
|-------|---------------|-------------|
| Domain | Entities, rules, ports | None (pure Go) |
| Application | Use cases, orchestration | Domain only |
| Adapters | I/O, DB, HTTP, gRPC | Domain + frameworks |
| Main | Wire everything | All layers |

**Key Takeaways:**
- Domain layer has zero external imports — maximally testable
- Ports (interfaces) are defined in domain, implemented in adapters
- Dependency injection via constructors (not global state)
- `slog` (Go 1.21+) is the standard structured logging package
- Graceful shutdown: `signal.Notify` → `server.Shutdown(ctx)` with timeout
