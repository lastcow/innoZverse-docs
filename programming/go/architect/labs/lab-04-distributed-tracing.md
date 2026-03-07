# Lab 04: Distributed Tracing with OpenTelemetry

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

OpenTelemetry Go: TracerProvider, Tracer.Start, SpanContext, W3C TraceContext propagation, OTLP gRPC exporter, Prometheus metrics client, and pprof HTTP endpoint.

---

## Step 1: OpenTelemetry SDK Setup

```go
package telemetry

import (
	"context"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
)

func InitTracing(ctx context.Context) (func(), error) {
	// OTLP gRPC exporter
	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint("otel-collector:4317"),
		otlptracegrpc.WithInsecure(),
	)
	if err != nil {
		return nil, err
	}

	// Resource: service metadata
	res := resource.NewWithAttributes(
		semconv.SchemaURL,
		semconv.ServiceName("my-service"),
		semconv.ServiceVersion("1.0.0"),
		semconv.DeploymentEnvironment("production"),
	)

	// TracerProvider with batching
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
		sdktrace.WithSampler(sdktrace.ParentBased(
			sdktrace.TraceIDRatioBased(0.1), // 10% sampling
		)),
	)

	otel.SetTracerProvider(tp)

	return func() {
		tp.Shutdown(ctx)
	}, nil
}
```

---

## Step 2: Creating Spans

```go
package service

import (
	"context"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
	"go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("my-service")

func GetUser(ctx context.Context, userID string) (*User, error) {
	// Start span
	ctx, span := tracer.Start(ctx, "GetUser",
		trace.WithSpanKind(trace.SpanKindServer),
		trace.WithAttributes(
			attribute.String("user.id", userID),
		),
	)
	defer span.End()

	// Add attributes dynamically
	span.SetAttributes(
		semconv.DBSystemSqlite,
		semconv.DBOperationName("SELECT"),
	)

	user, err := db.FindUser(ctx, userID)
	if err != nil {
		// Record error with stack trace
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return nil, err
	}

	span.SetAttributes(attribute.String("user.role", string(user.Role)))
	span.SetStatus(codes.Ok, "")
	return user, nil
}
```

---

## Step 3: W3C TraceContext Propagation

```go
package middleware

import (
	"net/http"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
)

// HTTP middleware: extract trace context from incoming request
func TracingMiddleware(next http.Handler) http.Handler {
	propagator := otel.GetTextMapPropagator()
	tracer := otel.Tracer("http-middleware")

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract: traceparent: 00-{traceId}-{spanId}-{flags}
		ctx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))

		ctx, span := tracer.Start(ctx, r.Method+" "+r.URL.Path)
		defer span.End()

		// Propagate to downstream HTTP calls
		outReq, _ := http.NewRequestWithContext(ctx, "GET", "http://service-b/api", nil)
		propagator.Inject(ctx, propagation.HeaderCarrier(outReq.Header))
		// outReq.Header now contains: traceparent, tracestate

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
```

---

## Step 4: Prometheus Metrics

```go
package metrics

import (
	"net/http"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	// Counter: total requests
	RequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	// Histogram: request duration
	RequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets, // .005, .01, .025...
		},
		[]string{"method", "path"},
	)

	// Gauge: active connections
	ActiveConnections = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "http_active_connections",
		Help: "Number of active HTTP connections",
	})
)

// Expose /metrics endpoint
func ServeMetrics(addr string) {
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(addr, nil)
}

// Usage in handler:
// timer := prometheus.NewTimer(RequestDuration.WithLabelValues("GET", "/users"))
// defer timer.ObserveDuration()
// RequestsTotal.WithLabelValues("GET", "/users", "200").Inc()
```

---

## Step 5: pprof Integration

```go
package main

import (
	"log"
	"net/http"
	_ "net/http/pprof"  // Side effect: registers /debug/pprof/* routes
)

func main() {
	// pprof endpoints at /debug/pprof/
	go func() {
		log.Println("pprof at :6060/debug/pprof/")
		http.ListenAndServe(":6060", nil)
	}()

	// In production: restrict to internal network only!
	// mux := http.NewServeMux()
	// mux.Handle("/debug/pprof/", http.HandlerFunc(pprof.Index))

	// Usage:
	// go tool pprof http://localhost:6060/debug/pprof/heap
	// go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
	// go tool pprof http://localhost:6060/debug/pprof/goroutine
	// go tool pprof http://localhost:6060/debug/pprof/trace?seconds=5
}
```

---

## Step 6: Structured Logging with slog (Go 1.21+)

```go
package logging

import (
	"context"
	"log/slog"
	"os"
	"go.opentelemetry.io/otel/trace"
)

// Create logger with trace context
func NewLogger() *slog.Logger {
	return slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
}

// Add trace context to log entries
func WithTrace(ctx context.Context, logger *slog.Logger) *slog.Logger {
	span := trace.SpanFromContext(ctx)
	sc := span.SpanContext()
	if !sc.IsValid() {
		return logger
	}
	return logger.With(
		slog.String("trace_id", sc.TraceID().String()),
		slog.String("span_id",  sc.SpanID().String()),
	)
}

// Usage:
// log := WithTrace(ctx, logger)
// log.Info("Processing request", "user_id", userID, "action", "create_order")
// Output: {"level":"INFO","trace_id":"abc...","span_id":"123...","user_id":"u-1","action":"create_order"}
```

---

## Step 7: Baggage Propagation

```go
package context

import (
	"go.opentelemetry.io/otel/baggage"
)

// Baggage: key-value pairs propagated across service boundaries
// Like distributed global variables (use sparingly!)

func AddBaggage(ctx context.Context, userID, tenantID string) context.Context {
	userMember, _   := baggage.NewMember("user_id", userID)
	tenantMember, _ := baggage.NewMember("tenant_id", tenantID)
	bag, _ := baggage.New(userMember, tenantMember)
	return baggage.ContextWithBaggage(ctx, bag)
}

func GetBaggage(ctx context.Context) (userID, tenantID string) {
	bag := baggage.FromContext(ctx)
	return bag.Member("user_id").Value(), bag.Member("tenant_id").Value()
}
```

---

## Step 8: Capstone — Tracing Pattern Demo

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
  \"context\"
  \"fmt\"
  \"time\"
)

type Span struct {
  Name       string
  TraceID    string
  SpanID     string
  Attributes map[string]interface{}
  Status     string
  StartTime  time.Time
}

type Tracer struct{ spans []*Span }

func (t *Tracer) Start(ctx context.Context, name string) (context.Context, *Span) {
  s := &Span{Name: name, TraceID: \"trace-abc123\",
    SpanID: fmt.Sprintf(\"span-%d\", len(t.spans)+1),
    Attributes: make(map[string]interface{}), Status: \"UNSET\", StartTime: time.Now()}
  t.spans = append(t.spans, s)
  return ctx, s
}

func (s *Span) SetAttribute(k string, v interface{}) { s.Attributes[k] = v }
func (s *Span) SetStatus(status string)              { s.Status = status }
func (s *Span) End()                                 {}

func main() {
  tracer := &Tracer{}
  ctx := context.Background()
  fmt.Println(\"=== OpenTelemetry Tracing Pattern ===\")
  _, s1 := tracer.Start(ctx, \"processHTTPRequest\")
  s1.SetAttribute(\"http.method\", \"GET\")
  s1.SetAttribute(\"http.url\", \"/api/users/123\")
  s1.SetAttribute(\"http.status_code\", 200)
  s1.SetStatus(\"OK\"); s1.End()
  _, s2 := tracer.Start(ctx, \"db.query\")
  s2.SetAttribute(\"db.system\", \"postgresql\")
  s2.SetAttribute(\"db.operation\", \"SELECT\")
  s2.SetStatus(\"OK\"); s2.End()
  for _, s := range tracer.spans {
    fmt.Printf(\"Span: %s (traceId=%s, spanId=%s)\\n\", s.Name, s.TraceID, s.SpanID)
    for k, v := range s.Attributes { fmt.Printf(\"  %s = %v\\n\", k, v) }
    fmt.Printf(\"  Status: %s\\n\", s.Status)
  }
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
=== OpenTelemetry Tracing Pattern ===
Span: processHTTPRequest (traceId=trace-abc123, spanId=span-1)
  http.method = GET
  http.url = /api/users/123
  http.status_code = 200
  Status: OK
Span: db.query (traceId=trace-abc123, spanId=span-2)
  db.system = postgresql
  db.operation = SELECT
  Status: OK
```

---

## Summary

| Feature | OTel API | Notes |
|---------|---------|-------|
| Tracer creation | `otel.Tracer("name")` | Per-package tracer |
| Span creation | `tracer.Start(ctx, name)` | Returns new ctx |
| Attributes | `span.SetAttributes(...)` | Semantic conventions |
| Error recording | `span.RecordError(err)` | Auto stack trace |
| HTTP propagation | `propagator.Extract/Inject` | W3C TraceContext |
| Baggage | `baggage.New(members...)` | Cross-service kv |
| Sampling | `TraceIDRatioBased(0.1)` | 10% in production |
| Prometheus | `promauto.New*` | Auto-register |
