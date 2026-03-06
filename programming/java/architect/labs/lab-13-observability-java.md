# Lab 13: Observability — OpenTelemetry + Micrometer

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Production observability requires distributed traces, metrics, and structured logs. Implement OpenTelemetry Java SDK for distributed tracing with W3C TraceContext propagation, Micrometer for metrics (Counter/Timer/Gauge), and structured JSON logging with SLF4J/Logback.

---

## Step 1: Observability Pillars

```
Three pillars of observability:
  TRACES  — distributed execution paths (WHO called WHAT and WHEN)
  METRICS — aggregated numeric measurements (HOW MANY, HOW FAST, HOW BIG)
  LOGS    — discrete events with context (WHAT HAPPENED)

OpenTelemetry unifies all three:
  Traces  → OTel SDK → OTLP → Jaeger/Tempo
  Metrics → OTel SDK → OTLP → Prometheus/Victoria
  Logs    → OTel SDK → OTLP → Loki/Elasticsearch

Java ecosystem:
  Traces:  OpenTelemetry Java SDK (opentelemetry-sdk)
  Metrics: Micrometer (micrometer-core) → OTel bridge or Prometheus
  Logs:    SLF4J + Logback (with JSON appender) → MDC for trace correlation
```

---

## Step 2: OpenTelemetry SDK Setup

```xml
<!-- pom.xml -->
<dependencies>
  <dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-sdk</artifactId>
    <version>1.32.0</version>
  </dependency>
  <dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-core</artifactId>
    <version>1.12.0</version>
  </dependency>
</dependencies>
```

```java
import io.opentelemetry.api.*;
import io.opentelemetry.api.trace.*;
import io.opentelemetry.sdk.trace.*;
import io.opentelemetry.sdk.trace.export.*;
import io.opentelemetry.sdk.trace.data.*;
import io.opentelemetry.sdk.common.CompletableResultCode;
import java.util.*;

public class OTelSetup {
    // Custom in-memory exporter (replaces InMemorySpanExporter in older versions)
    static List<SpanData> capturedSpans = Collections.synchronizedList(new ArrayList<>());
    
    static class CollectingExporter implements SpanExporter {
        public CompletableResultCode export(Collection<SpanData> spans) {
            capturedSpans.addAll(spans);
            return CompletableResultCode.ofSuccess();
        }
        public CompletableResultCode flush() { return CompletableResultCode.ofSuccess(); }
        public CompletableResultCode shutdown() { return CompletableResultCode.ofSuccess(); }
    }
    
    public static SdkTracerProvider buildTracerProvider() {
        return SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(new CollectingExporter()))
            .build();
    }
}
```

---

## Step 3: Creating Spans and Hierarchies

```java
import io.opentelemetry.api.trace.*;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;

public class SpanDemo {
    public static void demo(Tracer tracer) throws Exception {
        // Parent span
        Span parentSpan = tracer.spanBuilder("process-order")
            .setAttribute("order.id", "ORD-001")
            .setAttribute("order.customer", "Alice")
            .startSpan();
        
        try (Scope parentScope = parentSpan.makeCurrent()) {
            // Child span — automatically linked to current span
            Span validateSpan = tracer.spanBuilder("validate-payment")
                .setAttribute("payment.method", "credit-card")
                .setAttribute("payment.amount", 99.99)
                .startSpan();
            
            try (Scope validateScope = validateSpan.makeCurrent()) {
                Thread.sleep(10); // simulate work
                validateSpan.addEvent("card-validated",
                    io.opentelemetry.api.common.Attributes.of(
                        io.opentelemetry.api.common.AttributeKey.stringKey("card.last4"), "4242"
                    ));
                validateSpan.setStatus(StatusCode.OK);
            } finally {
                validateSpan.end();
            }
            
            // Sibling span
            Span shippingSpan = tracer.spanBuilder("create-shipment")
                .startSpan();
            try (Scope shippingScope = shippingSpan.makeCurrent()) {
                Thread.sleep(5);
                shippingSpan.setAttribute("tracking.number", "TRACK-XYZ-001");
            } finally {
                shippingSpan.end();
            }
            
            parentSpan.setStatus(StatusCode.OK);
        } finally {
            parentSpan.end();
        }
    }
}
```

---

## Step 4: W3C TraceContext Propagation

```java
import io.opentelemetry.api.trace.*;
import io.opentelemetry.context.*;
import io.opentelemetry.context.propagation.*;
import java.util.*;

public class TraceContextPropagation {
    // Inject trace context into HTTP headers
    static Map<String, String> injectHeaders(Context context, TextMapPropagator propagator) {
        Map<String, String> headers = new HashMap<>();
        propagator.inject(context, headers, Map::put);
        return headers;
    }
    
    // Extract trace context from HTTP headers
    static Context extractContext(Map<String, String> headers, TextMapPropagator propagator) {
        return propagator.extract(Context.root(), headers,
            (carrier, key) -> carrier.get(key));
    }
    
    public static void main(String[] args) {
        // W3C TraceContext headers:
        // traceparent: 00-{traceId}-{spanId}-{flags}
        // tracestate: vendor-specific metadata
        
        String traceId = "0af7651916cd43dd8448eb211c80319c";
        String spanId  = "b7ad6b7169203331";
        String traceparent = "00-" + traceId + "-" + spanId + "-01";
        
        System.out.println("W3C TraceContext format:");
        System.out.println("  traceparent: " + traceparent);
        System.out.println("  version:     00");
        System.out.println("  trace-id:    " + traceId + " (128-bit)");
        System.out.println("  parent-id:   " + spanId + " (64-bit)");
        System.out.println("  flags:       01 (sampled)");
        System.out.println();
        System.out.println("Propagation: inject headers on outbound, extract on inbound");
        System.out.println("All spans in distributed call share the same trace-id");
    }
}
```

---

## Step 5: Micrometer Metrics

```java
import io.micrometer.core.instrument.*;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.core.instrument.Timer;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

public class MicrometerDemo {
    public static void main(String[] args) throws Exception {
        MeterRegistry registry = new SimpleMeterRegistry();
        
        // Counter: monotonically increasing value
        Counter requestCounter = Counter.builder("http.requests.total")
            .tag("method", "GET")
            .tag("status", "200")
            .description("Total HTTP requests")
            .register(registry);
        
        requestCounter.increment(5);
        System.out.println("Counter: " + requestCounter.count()); // 5.0
        
        // Timer: measures duration distribution
        Timer latencyTimer = Timer.builder("http.request.duration")
            .tag("endpoint", "/api/users")
            .publishPercentiles(0.50, 0.95, 0.99)
            .publishPercentileHistogram()
            .register(registry);
        
        // Record actual durations
        latencyTimer.record(Duration.ofMillis(42));
        latencyTimer.record(Duration.ofMillis(85));
        latencyTimer.record(Duration.ofMillis(200));
        
        // Record a timed block
        latencyTimer.record(() -> {
            try { Thread.sleep(10); } catch (InterruptedException e) {}
        });
        
        System.out.println("Timer count: " + latencyTimer.count());
        System.out.printf("Timer mean: %.1fms%n", latencyTimer.mean(TimeUnit.MILLISECONDS));
        
        // Gauge: current value (can go up and down)
        AtomicLong activeConnections = new AtomicLong(0);
        Gauge.builder("db.connections.active", activeConnections, AtomicLong::doubleValue)
            .description("Active DB connections")
            .register(registry);
        
        activeConnections.set(15);
        System.out.println("Gauge: " + registry.find("db.connections.active").gauge().value());
        
        // DistributionSummary: size/amount distributions
        DistributionSummary requestSize = DistributionSummary.builder("http.request.size")
            .baseUnit("bytes")
            .publishPercentiles(0.5, 0.95)
            .register(registry);
        
        requestSize.record(1024);
        requestSize.record(2048);
        System.out.println("Size count: " + requestSize.count() + ", mean: " + requestSize.mean() + " bytes");
        
        // List all meters
        System.out.println("\nRegistered meters:");
        registry.getMeters().forEach(m -> System.out.println("  " + m.getId().getName()));
    }
}
```

---

## Step 6: Structured Logging with SLF4J + Logback

```xml
<!-- logback.xml for JSON structured logging -->
<configuration>
  <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
      <!-- Fields added automatically: @timestamp, level, message, logger, thread -->
      <customFields>{"service":"order-service","version":"1.2.0"}</customFields>
    </encoder>
  </appender>
  <root level="INFO">
    <appender-ref ref="JSON"/>
  </root>
</configuration>
```

```java
import org.slf4j.*;

public class StructuredLoggingDemo {
    private static final Logger log = LoggerFactory.getLogger(StructuredLoggingDemo.class);
    
    public static void logWithContext(String traceId, String userId, String action) {
        // MDC: Mapped Diagnostic Context — thread-local key/value store
        MDC.put("traceId", traceId);
        MDC.put("userId", userId);
        MDC.put("action", action);
        
        try {
            log.info("Processing request");
            log.debug("Request details: action={} userId={}", action, userId);
            // JSON output includes MDC fields automatically:
            // {"@timestamp":"2026-03-06T12:00:00Z","level":"INFO",
            //  "message":"Processing request",
            //  "traceId":"abc123","userId":"user-42","action":"order"}
        } finally {
            MDC.clear(); // always clear in try-finally
        }
    }
    
    // OTel → MDC bridge (trace correlation in logs)
    // io.opentelemetry.instrumentation:opentelemetry-logback-mdc-1.0
    // Automatically adds: traceId, spanId, traceFlags to MDC
}
```

---

## Step 7: JVM Metrics Concepts

```java
// Micrometer JVM metrics (auto-configured in Spring Boot)
// In plain Java, use JvmMetrics binders:

// JvmMemoryMetrics: heap/non-heap used/committed/max per memory pool
// JvmGcMetrics: GC pause duration, GC count per collector
// JvmThreadMetrics: live threads, daemon threads, peak threads
// ProcessorMetrics: CPU usage (JVM process + system)
// FileDescriptorMetrics: open/max file descriptors

// Key JVM metrics to alert on:
// jvm.memory.used{area="heap"} / jvm.memory.max{area="heap"}  > 85% → GC pressure
// jvm.gc.pause{action="end of major GC"} > 200ms              → GC latency spike
// jvm.threads.live > (platform threads) 500                   → thread leak
// jvm.threads.peak sudden drop                                 → thread pool saturation

public class JVMMetricsDemo {
    public static void main(String[] args) {
        System.out.println("JVM metrics to register:");
        System.out.println("  new JvmMemoryMetrics().bindTo(registry)");
        System.out.println("  new JvmGcMetrics().bindTo(registry)");
        System.out.println("  new JvmThreadMetrics().bindTo(registry)");
        System.out.println("  new ProcessorMetrics().bindTo(registry)");
        System.out.println();
        System.out.println("Alert thresholds:");
        System.out.println("  heap usage > 85%: GC pressure");
        System.out.println("  major GC pause > 200ms: latency impact");
        System.out.println("  live threads > 500: possible thread leak");
        System.out.println("  CPU > 80% sustained: capacity issue");
    }
}
```

---

## Step 8: Capstone — OTel Spans + Micrometer

```java
package com.lab;

import io.opentelemetry.api.trace.*;
import io.opentelemetry.sdk.common.CompletableResultCode;
import io.opentelemetry.sdk.trace.*;
import io.opentelemetry.sdk.trace.export.*;
import io.opentelemetry.sdk.trace.data.*;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.*;

public class Main {
    static List<SpanData> capturedSpans = Collections.synchronizedList(new ArrayList<>());
    
    static class CollectingExporter implements SpanExporter {
        public CompletableResultCode export(Collection<SpanData> data) {
            capturedSpans.addAll(data);
            return CompletableResultCode.ofSuccess();
        }
        public CompletableResultCode flush() { return CompletableResultCode.ofSuccess(); }
        public CompletableResultCode shutdown() { return CompletableResultCode.ofSuccess(); }
    }
    
    public static void main(String[] args) throws Exception {
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(new CollectingExporter()))
            .build();
        
        Tracer tracer = tracerProvider.get("com.lab", "1.0");
        
        Span parent = tracer.spanBuilder("process-order")
            .setAttribute("order.id", "ORD-001")
            .startSpan();
        
        try (var scope = parent.makeCurrent()) {
            Span child = tracer.spanBuilder("validate-payment")
                .setAttribute("payment.method", "credit-card")
                .startSpan();
            Thread.sleep(10);
            child.addEvent("payment-validated");
            child.end();
        } finally {
            parent.setStatus(StatusCode.OK);
            parent.end();
        }
        
        tracerProvider.forceFlush();
        System.out.println("Spans captured: " + capturedSpans.size());
        for (SpanData span : capturedSpans) {
            System.out.println("  Span: " + span.getName() + " [" + span.getStatus().getStatusCode() + "]");
            System.out.println("    TraceId: " + span.getTraceId().substring(0,16) + "...");
        }
        
        MeterRegistry registry = new SimpleMeterRegistry();
        Counter requests = Counter.builder("http.requests").tag("method", "GET").register(registry);
        requests.increment(5);
        System.out.println("Micrometer counter: " + (int)requests.count());
        System.out.println("OTel + Micrometer: SUCCESS");
    }
}
```

```bash
# Maven project with opentelemetry-sdk + micrometer-core
cd /tmp/otel3 && mvn compile exec:java -Dexec.mainClass=com.lab.Main -q 2>/dev/null
```

📸 **Verified Output:**
```
Spans captured: 2
  Span: validate-payment [UNSET]
    TraceId: 1b2fe77e2c56c479...
  Span: process-order [OK]
    TraceId: 1b2fe77e2c56c479...
Micrometer counter: 5
OTel + Micrometer: SUCCESS
```

---

## Summary

| Concept | API/Class | Purpose |
|---|---|---|
| Tracer provider | `SdkTracerProvider` | Root trace configuration |
| Span creation | `tracer.spanBuilder()` | Start a trace segment |
| Span context | `makeCurrent()` / `Scope` | Parent-child linking |
| Span events | `span.addEvent()` | Record interesting moments |
| Span attributes | `span.setAttribute()` | Structured metadata |
| Span exporter | `SpanExporter` | Send spans to backend |
| W3C propagation | `traceparent` header | Cross-service trace IDs |
| Counter | `Counter.builder()` | Monotonic count |
| Timer | `Timer.builder()` | Duration distribution |
| Gauge | `Gauge.builder()` | Current value snapshot |
| MDC | `MDC.put()` | Log/trace correlation |
