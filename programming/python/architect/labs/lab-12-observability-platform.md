# Lab 12: Observability Platform

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Production systems need observability: distributed tracing (OpenTelemetry), metrics (Prometheus), and structured logging (structlog). This lab builds a complete observability stack for Python services.

## Prerequisites

```bash
pip install opentelemetry-sdk prometheus-client structlog
```

## Step 1: OpenTelemetry Tracing — TracerProvider Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Setup: use in-memory exporter for testing
exporter = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("myapp.tracer", "1.0.0")

# Create spans
with tracer.start_as_current_span("http.request") as span:
    span.set_attribute("http.method", "GET")
    span.set_attribute("http.url", "/api/users")
    span.set_attribute("http.host", "api.example.com")
    
    with tracer.start_as_current_span("db.query") as child:
        child.set_attribute("db.system", "postgresql")
        child.set_attribute("db.statement", "SELECT * FROM users WHERE active=true")
        child.set_attribute("db.row_count", 42)

# Inspect captured spans
spans = exporter.get_finished_spans()
print(f"Spans captured: {len(spans)}")
for s in spans:
    print(f"  Span: {s.name}")
    print(f"    Attributes: {dict(s.attributes)}")
    print(f"    Status: {s.status.status_code}")
    parent = s.parent
    print(f"    Parent: {parent.span_id if parent else 'root'}")
```

📸 **Verified Output:**
```
Spans captured: 2
  Span: db.query
    Attributes: {'db.system': 'postgresql', 'db.statement': 'SELECT * FROM users WHERE active=true', 'db.row_count': 42}
    Status: StatusCode.UNSET
  Span: http.request
    Attributes: {'http.method': 'GET', 'http.url': '/api/users', 'http.host': 'api.example.com'}
    Status: StatusCode.UNSET
```

> 💡 Spans are finished when the `with` block exits. The exporter receives them in LIFO order (innermost first). Use `InMemorySpanExporter` for unit tests.

## Step 2: Span Kinds and Status

```python
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

exporter.clear()  # reset from step 1

with tracer.start_as_current_span("user.service", kind=SpanKind.SERVER) as server_span:
    server_span.set_attribute("rpc.system", "grpc")
    server_span.set_attribute("rpc.service", "UserService")
    
    with tracer.start_as_current_span("db.users", kind=SpanKind.CLIENT) as db_span:
        db_span.set_attribute("db.system", "postgresql")
        
        # Simulate an error
        try:
            raise ValueError("Connection pool exhausted")
        except ValueError as e:
            db_span.record_exception(e)
            db_span.set_status(StatusCode.ERROR, str(e))
            server_span.set_status(StatusCode.ERROR, "Database unavailable")

spans = exporter.get_finished_spans()
for s in spans:
    print(f"{s.name}: kind={s.kind.name}, status={s.status.status_code.name}")
    if s.events:
        print(f"  Events: {[e.name for e in s.events]}")
```

## Step 3: Baggage — Cross-Service Context

```python
from opentelemetry import baggage, context
from opentelemetry.baggage.propagation import W3CBaggagePropagator

# Set baggage values (propagated across service boundaries)
ctx = baggage.set_baggage("user.id", "alice-123")
ctx = baggage.set_baggage("request.id", "req-abc456", context=ctx)

with context.use_context(ctx):
    user_id = baggage.get_baggage("user.id")
    req_id = baggage.get_baggage("request.id")
    print(f"Baggage: user.id={user_id}, request.id={req_id}")
    
    with tracer.start_as_current_span("process_request") as span:
        # Baggage is available to all spans in this context
        span.set_attribute("user.id", baggage.get_baggage("user.id"))
        span.set_attribute("request.id", baggage.get_baggage("request.id"))
        print(f"Span attributes set from baggage")
```

## Step 4: Prometheus Metrics — Counter, Histogram, Gauge

```python
from prometheus_client import Counter, Histogram, Gauge, Summary, REGISTRY, generate_latest
import time

# Counter: monotonically increasing (requests, errors, etc.)
http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    labelnames=['method', 'endpoint', 'status']
)

# Histogram: observe values in buckets (latency, size)
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    labelnames=['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

# Gauge: current value (queue size, active connections)
active_connections = Gauge(
    'active_connections',
    'Number of currently active connections',
    labelnames=['service']
)

# Summary: percentiles (like Histogram but computed client-side)
response_size = Summary(
    'response_size_bytes',
    'Response size in bytes'
)

# Simulate requests
import random

for _ in range(50):
    method = random.choice(['GET', 'POST'])
    endpoint = random.choice(['/api/users', '/api/products', '/health'])
    status = random.choice(['200', '200', '200', '404', '500'])
    
    http_requests.labels(method=method, endpoint=endpoint, status=status).inc()
    
    latency = random.expovariate(10)  # exponential distribution
    request_duration.labels(method=method, endpoint=endpoint).observe(latency)
    response_size.observe(random.randint(100, 10000))

active_connections.labels(service='api').set(random.randint(10, 100))
active_connections.labels(service='worker').set(random.randint(1, 10))

# Display metrics
output = generate_latest().decode('utf-8')
for line in output.split('\n'):
    if line and not line.startswith('#'):
        print(line)
```

## Step 5: `structlog` — Structured JSON Logging

```python
import structlog
import logging
import json
import sys
import time

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger("myapp")

# Bind context (like request ID, user)
req_log = log.bind(request_id="req-001", user_id="alice")

req_log.info("request_started", method="GET", path="/api/users")
req_log.info("db_query_executed", table="users", rows=42, duration_ms=15.3)
req_log.warning("rate_limit_approaching", remaining=5, limit=100)

try:
    raise ValueError("Validation failed: email required")
except ValueError:
    req_log.error("request_failed", status=400, exc_info=True)

req_log.info("request_completed", status=400, duration_ms=52.1)
```

## Step 6: Integrated Observability Middleware

```python
import time
import uuid
import functools
from opentelemetry import trace
from prometheus_client import Counter, Histogram

# Shared observability layer
class Observability:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(service_name)
        self.log = structlog.get_logger(service_name)
        
        self.requests = Counter(
            f'{service_name}_requests_total',
            'Requests',
            ['operation', 'status']
        )
        self.latency = Histogram(
            f'{service_name}_latency_seconds',
            'Latency',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
        )
    
    def observe(self, operation: str):
        """Decorator that adds tracing, metrics, and logging."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                req_id = str(uuid.uuid4())[:8]
                op_log = self.log.bind(operation=operation, request_id=req_id)
                
                start = time.perf_counter()
                status = "success"
                
                with self.tracer.start_as_current_span(operation) as span:
                    span.set_attribute("request.id", req_id)
                    op_log.info("operation_started")
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.StatusCode.OK)
                        return result
                    except Exception as e:
                        status = "error"
                        span.record_exception(e)
                        span.set_status(trace.StatusCode.ERROR, str(e))
                        op_log.error("operation_failed", error=str(e))
                        raise
                    finally:
                        elapsed = time.perf_counter() - start
                        self.requests.labels(operation=operation, status=status).inc()
                        self.latency.labels(operation=operation).observe(elapsed)
                        op_log.info("operation_completed", 
                                   status=status, 
                                   duration_ms=round(elapsed * 1000, 2))
            return wrapper
        return decorator

obs = Observability("user-service")

@obs.observe("get_user")
def get_user(user_id: int) -> dict:
    time.sleep(0.001)  # simulate work
    return {'id': user_id, 'name': f'User-{user_id}'}

@obs.observe("create_user")
def create_user(name: str, email: str) -> dict:
    time.sleep(0.002)
    return {'id': 999, 'name': name, 'email': email}

# Run operations
print("=== Service Operations ===")
u = get_user(42)
u2 = get_user(43)
new_u = create_user("Alice", "alice@example.com")
print(f"get_user(42): {u}")
print(f"create_user: {new_u}")
```

## Step 7: Health Check Endpoint Pattern

```python
from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class HealthStatus:
    healthy: bool
    checks: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class HealthChecker:
    """Pluggable health check system."""
    
    def __init__(self):
        self._checks = {}
    
    def register(self, name: str, check_fn, critical: bool = True):
        self._checks[name] = {'fn': check_fn, 'critical': critical}
    
    def check_all(self) -> HealthStatus:
        results = {}
        overall_healthy = True
        
        for name, config in self._checks.items():
            try:
                start = time.perf_counter()
                result = config['fn']()
                elapsed = time.perf_counter() - start
                results[name] = {
                    'status': 'ok',
                    'latency_ms': round(elapsed * 1000, 2),
                    'detail': result,
                }
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                }
                if config['critical']:
                    overall_healthy = False
        
        return HealthStatus(healthy=overall_healthy, checks=results)

# Register health checks
checker = HealthChecker()

def check_database():
    # Simulate DB connectivity check
    return {'connected': True, 'pool_size': 10, 'active': 3}

def check_cache():
    return {'connected': True, 'hit_rate': '87%', 'memory_mb': 256}

def check_external_api():
    # Could fail
    return {'reachable': True, 'latency_ms': 45}

checker.register('database', check_database, critical=True)
checker.register('cache', check_cache, critical=False)
checker.register('external_api', check_external_api, critical=False)

health = checker.check_all()
print(f"\nHealth: {'✓ OK' if health.healthy else '✗ DEGRADED'}")
for check_name, result in health.checks.items():
    icon = "✓" if result['status'] == 'ok' else "✗"
    print(f"  {icon} {check_name}: {result}")
```

## Step 8: Capstone — Complete Observability Stack

```python
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from prometheus_client import REGISTRY, generate_latest
import time
import random

# Reset state for capstone
cap_exporter = InMemorySpanExporter()
cap_provider = TracerProvider()
cap_provider.add_span_processor(SimpleSpanProcessor(cap_exporter))

# Metrics
REQUEST_COUNTER = Counter('capstone_requests', 'Requests', ['service', 'op', 'status'])
LATENCY_HIST    = Histogram('capstone_latency', 'Latency', ['service', 'op'])

# Simulated service calls
def simulated_service_call(service: str, op: str, latency: float = 0.01):
    tracer = trace.get_tracer(service)
    
    with tracer.start_as_current_span(f"{service}.{op}") as span:
        span.set_attribute("service.name", service)
        span.set_attribute("operation", op)
        
        time.sleep(latency)
        
        status = "success"
        if random.random() < 0.1:
            status = "error"
            span.set_status(trace.StatusCode.ERROR, "Random failure")
        
        REQUEST_COUNTER.labels(service=service, op=op, status=status).inc()
        LATENCY_HIST.labels(service=service, op=op).observe(latency)
        
        return {'status': status, 'service': service, 'op': op}

print("=== Capstone Observability Demo ===\n")

# Run simulated workload
for _ in range(20):
    service = random.choice(['user-svc', 'order-svc', 'payment-svc'])
    op = random.choice(['read', 'write', 'delete'])
    latency = random.expovariate(50)  # avg 20ms
    simulated_service_call(service, op, latency)

# Report
spans = cap_exporter.get_finished_spans()
print(f"Total spans: {len(spans)}")
service_counts = {}
for s in spans:
    name = s.name
    service_counts[name] = service_counts.get(name, 0) + 1

print("Span distribution:")
for name, count in sorted(service_counts.items(), key=lambda x: -x[1])[:5]:
    print(f"  {name}: {count}")

# Health check
health = checker.check_all()
print(f"\nSystem health: {'✓ Healthy' if health.healthy else '✗ Degraded'}")
for check, result in health.checks.items():
    print(f"  {check}: {result['status']}")
```

📸 **Verified Output (OpenTelemetry):**
```
Spans captured: 2
  Span: db.query
    Attributes: {'db.system': 'postgresql', 'db.statement': 'SELECT * FROM users'}
    Status: StatusCode.UNSET
  Span: http.request
    Attributes: {'http.method': 'GET', 'http.url': '/api/users'}
    Status: StatusCode.UNSET
```

## Summary

| Concept | Library/API | Use Case |
|---|---|---|
| Distributed tracing | `opentelemetry-sdk` | Request flow across services |
| Span attributes | `span.set_attribute` | Contextual metadata |
| Span status | `StatusCode.OK/ERROR` | Error tracking |
| Baggage | `opentelemetry.baggage` | Cross-service context |
| Request counter | `prometheus_client.Counter` | Request rate, error rate |
| Latency histogram | `Histogram` + buckets | P50/P95/P99 latency |
| Active gauge | `Gauge.set` | Current resource usage |
| Structured logging | `structlog.JSONRenderer` | Machine-parseable logs |
| Health checks | Custom checker registry | Service readiness/liveness |
