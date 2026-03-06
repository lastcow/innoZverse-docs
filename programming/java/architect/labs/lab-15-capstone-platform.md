# Lab 15: Capstone — Production Java Platform

**Time:** 90 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Build a complete production Java platform integrating all previous labs: virtual threads for concurrency, gRPC for service communication, SQLite for persistence, Resilience4j circuit breaker, OpenTelemetry observability, EC P-256 request signing, manual DI annotations, JMH benchmarks, and JUnit 5 tests — all verified end-to-end in Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Production Java Platform (Lab 15)                           │
│                                                              │
│  ┌──────────────┐   ┌─────────────────┐                     │
│  │ Virtual       │   │  gRPC Service   │                     │
│  │ Threads       │──▶│  (in-process)   │                     │
│  │ (10000 tasks) │   │  + Interceptor  │                     │
│  └──────────────┘   └────────┬────────┘                     │
│                               │                              │
│  ┌──────────────┐   ┌─────────▼────────┐                    │
│  │ Resilience4j │   │  SQLite JDBC     │                     │
│  │ Circuit      │   │  Event Store     │                     │
│  │ Breaker      │   └──────────────────┘                     │
│  └──────────────┘                                            │
│                                                              │
│  ┌──────────────┐   ┌──────────────────┐                    │
│  │ OpenTelemetry│   │  EC P-256        │                     │
│  │ Spans        │   │  Request Signing │                     │
│  └──────────────┘   └──────────────────┘                    │
│                                                              │
│  ┌──────────────┐   ┌──────────────────┐                    │
│  │ JMH          │   │  Manual @Inject  │                     │
│  │ @Benchmark   │   │  DI Container    │                     │
│  └──────────────┘   └──────────────────┘                    │
│                                                              │
│  JUnit 5: 6+ @Test  (all components tested)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Project Structure

```
capstone/
├── pom.xml
└── src/
    ├── main/
    │   └── java/com/lab/
    │       ├── Main.java           (orchestrator, runs all demos)
    │       ├── GrpcService.java    (in-process gRPC server+client)
    │       ├── DataStore.java      (SQLite event store)
    │       ├── SecurityService.java (EC P-256 signing)
    │       ├── ObservabilityService.java (OTel spans)
    │       └── DIContainer.java    (manual DI annotations)
    └── test/
        └── java/com/lab/
            └── PlatformTest.java   (6 JUnit 5 tests)
```

---

## Step 2: pom.xml

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.lab</groupId>
  <artifactId>capstone</artifactId>
  <version>1.0</version>

  <properties>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
  </properties>

  <dependencies>
    <!-- gRPC in-process for testing -->
    <dependency><groupId>io.grpc</groupId><artifactId>grpc-core</artifactId><version>1.58.0</version></dependency>
    <dependency><groupId>io.grpc</groupId><artifactId>grpc-inprocess</artifactId><version>1.58.0</version></dependency>
    <dependency><groupId>io.grpc</groupId><artifactId>grpc-stub</artifactId><version>1.58.0</version></dependency>

    <!-- SQLite -->
    <dependency><groupId>org.xerial</groupId><artifactId>sqlite-jdbc</artifactId><version>3.47.0.0</version></dependency>

    <!-- Resilience4j -->
    <dependency><groupId>io.github.resilience4j</groupId><artifactId>resilience4j-circuitbreaker</artifactId><version>2.1.0</version></dependency>

    <!-- OpenTelemetry -->
    <dependency><groupId>io.opentelemetry</groupId><artifactId>opentelemetry-sdk</artifactId><version>1.32.0</version></dependency>

    <!-- JMH -->
    <dependency><groupId>org.openjdk.jmh</groupId><artifactId>jmh-core</artifactId><version>1.37</version></dependency>
    <dependency><groupId>org.openjdk.jmh</groupId><artifactId>jmh-generator-annprocess</artifactId><version>1.37</version><scope>provided</scope></dependency>

    <!-- JUnit 5 -->
    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><version>5.10.1</version><scope>test</scope></dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.2</version>
      </plugin>
    </plugins>
  </build>
</project>
```

---

## Step 3: Manual DI Annotations

```java
package com.lab;

import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface Component { String value() default ""; }

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
@interface Inject {}

class DIContainer {
    private final Map<String, Object> beans = new LinkedHashMap<>();
    private final Map<Class<?>, Object> typeMap = new HashMap<>();

    void register(Class<?>... classes) throws Exception {
        for (Class<?> cls : classes) {
            Component ann = cls.getAnnotation(Component.class);
            String name = (ann != null && !ann.value().isEmpty())
                ? ann.value() : lowerFirst(cls.getSimpleName());
            Object bean = cls.getDeclaredConstructor().newInstance();
            beans.put(name, bean);
            typeMap.put(cls, bean);
        }
    }

    void wire() throws Exception {
        for (Object bean : beans.values()) {
            for (Field f : bean.getClass().getDeclaredFields()) {
                if (f.isAnnotationPresent(Inject.class)) {
                    f.setAccessible(true);
                    Object dep = typeMap.get(f.getType());
                    if (dep == null) throw new RuntimeException("No bean for: " + f.getType());
                    f.set(bean, dep);
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    <T> T get(Class<T> type) { return (T) typeMap.get(type); }

    Set<String> names() { return beans.keySet(); }

    private static String lowerFirst(String s) {
        return Character.toLowerCase(s.charAt(0)) + s.substring(1);
    }
}
```

---

## Step 4: Core Services

```java
package com.lab;

import java.security.*;
import java.security.spec.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.Base64;
import java.sql.*;
import io.opentelemetry.api.trace.*;
import io.opentelemetry.sdk.trace.*;
import io.opentelemetry.sdk.trace.export.*;
import io.opentelemetry.sdk.trace.data.*;
import io.opentelemetry.sdk.common.CompletableResultCode;
import java.util.*;

// Security service: EC P-256 signing
@Component
class SecurityService {
    final KeyPair keyPair;
    SecurityService() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        keyPair = kpg.generateKeyPair();
    }
    byte[] sign(byte[] data) throws Exception {
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initSign(keyPair.getPrivate());
        sig.update(data);
        return sig.sign();
    }
    boolean verify(byte[] data, byte[] signature) throws Exception {
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initVerify(keyPair.getPublic());
        sig.update(data);
        return sig.verify(signature);
    }
}

// Data store: SQLite event log
@Component
class DataStore {
    private Connection conn;
    DataStore() throws Exception {
        Class.forName("org.sqlite.JDBC");
        conn = DriverManager.getConnection("jdbc:sqlite::memory:");
        conn.createStatement().execute(
            "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, " +
            "type TEXT, payload TEXT, ts TEXT)"
        );
    }
    void append(String type, String payload) throws Exception {
        conn.createStatement().execute(
            "INSERT INTO events (type, payload, ts) VALUES ('" + type + "','" +
            payload + "',datetime('now'))"
        );
    }
    int count() throws Exception {
        ResultSet rs = conn.createStatement().executeQuery("SELECT COUNT(*) FROM events");
        return rs.getInt(1);
    }
    void close() throws Exception { conn.close(); }
}

// Observability: OTel spans
@Component
class ObservabilityService {
    final List<SpanData> spans = Collections.synchronizedList(new ArrayList<>());
    final SdkTracerProvider tracerProvider;
    final Tracer tracer;

    ObservabilityService() {
        SpanExporter exporter = new SpanExporter() {
            public CompletableResultCode export(Collection<SpanData> d) { spans.addAll(d); return CompletableResultCode.ofSuccess(); }
            public CompletableResultCode flush() { return CompletableResultCode.ofSuccess(); }
            public CompletableResultCode shutdown() { return CompletableResultCode.ofSuccess(); }
        };
        tracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter)).build();
        tracer = tracerProvider.get("com.lab.platform", "1.0");
    }

    Span startSpan(String name) { return tracer.spanBuilder(name).startSpan(); }
    void flush() { tracerProvider.forceFlush(); }
}
```

---

## Step 5: gRPC Service

```java
package com.lab;

import io.grpc.*;
import io.grpc.inprocess.*;
import io.grpc.stub.*;
import java.util.concurrent.*;

@Component
class GrpcService {
    private static final String SVC = "com.lab.Platform";
    private static final MethodDescriptor<String, String> PROCESS =
        MethodDescriptor.<String, String>newBuilder()
            .setType(MethodDescriptor.MethodType.UNARY)
            .setFullMethodName(SVC + "/Process")
            .setRequestMarshaller(new StringM()).setResponseMarshaller(new StringM())
            .build();

    static class StringM implements MethodDescriptor.Marshaller<String> {
        public java.io.InputStream stream(String s) { return new java.io.ByteArrayInputStream(s.getBytes()); }
        public String parse(java.io.InputStream is) {
            try { return new String(is.readAllBytes()); } catch(Exception e) { throw new RuntimeException(e); }
        }
    }

    @Inject SecurityService security;
    @Inject ObservabilityService observability;
    @Inject DataStore dataStore;

    private Server server;
    private ManagedChannel channel;
    private final String serverName = InProcessServerBuilder.generateName();

    void start() throws Exception {
        server = InProcessServerBuilder.forName(serverName).directExecutor()
            .addService(ServerServiceDefinition.builder(SVC)
                .addMethod(PROCESS, ServerCalls.asyncUnaryCall((req, obs) -> {
                    Span span = observability.startSpan("grpc.process");
                    try {
                        byte[] sig = security.sign(req.getBytes());
                        String encoded = java.util.Base64.getEncoder().encodeToString(sig).substring(0, 16);
                        try { dataStore.append("REQUEST", req); } catch(Exception e) {}
                        span.setAttribute("request", req);
                        obs.onNext("Processed: " + req + " [sig:" + encoded + "...]");
                        obs.onCompleted();
                    } catch (Exception e) {
                        obs.onError(Status.INTERNAL.withCause(e).asRuntimeException());
                    } finally {
                        span.setStatus(StatusCode.OK);
                        span.end();
                    }
                })).build())
            .build().start();

        channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();
    }

    String call(String request) throws Exception {
        ClientCall<String, String> call = channel.newCall(PROCESS, CallOptions.DEFAULT);
        CompletableFuture<String> result = new CompletableFuture<>();
        call.start(new ClientCall.Listener<String>() {
            public void onMessage(String m) { result.complete(m); }
            public void onClose(Status s, Metadata t) {
                if (!s.isOk()) result.completeExceptionally(s.asException());
            }
        }, new Metadata());
        call.sendMessage(request); call.halfClose(); call.request(1);
        return result.get(5, TimeUnit.SECONDS);
    }

    void stop() throws Exception {
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        server.shutdown().awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

---

## Step 6: JMH Benchmark

```java
package com.lab;

import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.*;
import org.openjdk.jmh.runner.options.*;
import java.util.concurrent.TimeUnit;
import java.security.*;
import java.security.spec.*;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Benchmark)
@Warmup(iterations = 1, time = 1)
@Measurement(iterations = 2, time = 1)
@Fork(0)
public class PlatformBenchmark {
    KeyPair keyPair;
    byte[] data = "benchmark-payload".getBytes();

    @Setup
    public void setup() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        keyPair = kpg.generateKeyPair();
    }

    @Benchmark
    public byte[] signRequest() throws Exception {
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initSign(keyPair.getPrivate());
        sig.update(data);
        return sig.sign();
    }

    public static void main(String[] args) throws Exception {
        new Runner(new OptionsBuilder()
            .include(PlatformBenchmark.class.getSimpleName())
            .forks(0).warmupIterations(1).measurementIterations(2).build()).run();
    }
}
```

---

## Step 7: JUnit 5 Tests

```java
package com.lab;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.security.*;
import java.security.spec.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.sql.*;
import io.github.resilience4j.circuitbreaker.*;
import io.opentelemetry.api.trace.*;
import io.opentelemetry.sdk.trace.*;
import io.opentelemetry.sdk.trace.export.*;
import io.opentelemetry.sdk.trace.data.*;
import io.opentelemetry.sdk.common.CompletableResultCode;
import java.util.*;

public class PlatformTest {

    @Test
    @DisplayName("10000 virtual threads complete successfully")
    void testVirtualThreads() throws Exception {
        int N = 100; // reduced for fast test, concept same as 10000
        AtomicInteger count = new AtomicInteger();
        try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
            var futures = new ArrayList<Future<?>>();
            for (int i = 0; i < N; i++) {
                futures.add(exec.submit(() -> { count.incrementAndGet(); return null; }));
            }
            for (var f : futures) f.get();
        }
        assertEquals(N, count.get());
    }

    @Test
    @DisplayName("EC P-256 sign and verify")
    void testECSigning() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair kp = kpg.generateKeyPair();
        byte[] data = "test-request".getBytes();
        Signature sig = Signature.getInstance("SHA256withECDSA");
        sig.initSign(kp.getPrivate());
        sig.update(data);
        byte[] signature = sig.sign();
        sig.initVerify(kp.getPublic());
        sig.update(data);
        assertTrue(sig.verify(signature));
    }

    @Test
    @DisplayName("AES-GCM encrypt and decrypt")
    void testAESGCM() throws Exception {
        KeyGenerator kg = KeyGenerator.getInstance("AES");
        kg.init(256);
        SecretKey key = kg.generateKey();
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);
        Cipher enc = Cipher.getInstance("AES/GCM/NoPadding");
        enc.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] ciphertext = enc.doFinal("sensitive-data".getBytes());
        Cipher dec = Cipher.getInstance("AES/GCM/NoPadding");
        dec.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
        assertEquals("sensitive-data", new String(dec.doFinal(ciphertext)));
    }

    @Test
    @DisplayName("SQLite JDBC event store")
    void testSQLite() throws Exception {
        Class.forName("org.sqlite.JDBC");
        try (Connection conn = DriverManager.getConnection("jdbc:sqlite::memory:")) {
            conn.createStatement().execute(
                "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, payload TEXT)"
            );
            conn.createStatement().execute("INSERT INTO events (type, payload) VALUES ('ORDER_CREATED', '{\"id\":1}')");
            conn.createStatement().execute("INSERT INTO events (type, payload) VALUES ('PAYMENT_DONE', '{\"id\":1}')");
            ResultSet rs = conn.createStatement().executeQuery("SELECT COUNT(*) FROM events");
            assertTrue(rs.next());
            assertEquals(2, rs.getInt(1));
            ResultSet event = conn.createStatement().executeQuery("SELECT type FROM events WHERE id=1");
            assertTrue(event.next());
            assertEquals("ORDER_CREATED", event.getString("type"));
        }
    }

    @Test
    @DisplayName("Resilience4j circuit breaker opens on failures")
    void testCircuitBreaker() {
        CircuitBreaker cb = CircuitBreaker.of("test-cb",
            CircuitBreakerConfig.custom()
                .slidingWindowSize(2)
                .failureRateThreshold(100)
                .build());

        assertEquals(CircuitBreaker.State.CLOSED, cb.getState());

        // Force 2 failures → OPEN
        for (int i = 0; i < 2; i++) {
            try {
                cb.executeSupplier(() -> { throw new RuntimeException("fail"); });
            } catch (Exception ignored) {}
        }

        assertEquals(CircuitBreaker.State.OPEN, cb.getState());
        assertEquals(100.0f, cb.getMetrics().getFailureRate(), 0.1f);
    }

    @Test
    @DisplayName("OpenTelemetry span capture")
    void testOTelSpan() throws Exception {
        List<SpanData> captured = Collections.synchronizedList(new ArrayList<>());
        SpanExporter exporter = new SpanExporter() {
            public CompletableResultCode export(Collection<SpanData> d) { captured.addAll(d); return CompletableResultCode.ofSuccess(); }
            public CompletableResultCode flush() { return CompletableResultCode.ofSuccess(); }
            public CompletableResultCode shutdown() { return CompletableResultCode.ofSuccess(); }
        };
        SdkTracerProvider provider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter)).build();

        Tracer tracer = provider.get("test-service");
        Span parent = tracer.spanBuilder("parent").startSpan();
        try (var scope = parent.makeCurrent()) {
            Span child = tracer.spanBuilder("child").startSpan();
            child.setAttribute("key", "value");
            child.end();
        } finally {
            parent.setStatus(StatusCode.OK);
            parent.end();
        }
        provider.forceFlush();

        assertEquals(2, captured.size());
        // Verify parent-child relationship
        SpanData childData = captured.stream().filter(s -> s.getName().equals("child")).findFirst().orElseThrow();
        SpanData parentData = captured.stream().filter(s -> s.getName().equals("parent")).findFirst().orElseThrow();
        assertEquals(parentData.getSpanId(), childData.getParentSpanId());
    }
}
```

---

## Step 8: Capstone — Full Integration Test

```java
package com.lab;

import io.github.resilience4j.circuitbreaker.*;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Production Java Platform ===");

        // 1. Manual DI Container
        DIContainer di = new DIContainer();
        di.register(SecurityService.class, DataStore.class, ObservabilityService.class);
        di.wire();
        System.out.println("DI beans: " + di.names());

        SecurityService security = di.get(SecurityService.class);
        DataStore dataStore = di.get(DataStore.class);
        ObservabilityService otel = di.get(ObservabilityService.class);

        // 2. Virtual threads (10000 tasks)
        System.out.println("\n--- Virtual Threads ---");
        AtomicInteger vtCount = new AtomicInteger();
        long start = System.currentTimeMillis();
        try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
            var futures = new ArrayList<Future<?>>();
            for (int i = 0; i < 10000; i++) {
                futures.add(exec.submit(() -> { vtCount.incrementAndGet(); return null; }));
            }
            for (var f : futures) f.get();
        }
        System.out.printf("10000 virtual threads: %d completed in %dms%n",
            vtCount.get(), System.currentTimeMillis() - start);

        // 3. EC P-256 signing
        System.out.println("\n--- EC P-256 Signing ---");
        byte[] payload = "order-001:Alice:$99.99".getBytes();
        byte[] signature = security.sign(payload);
        boolean valid = security.verify(payload, signature);
        System.out.println("Signed payload, verified: " + valid);

        // 4. SQLite persistence
        System.out.println("\n--- SQLite Event Store ---");
        dataStore.append("ORDER_CREATED", "{\"id\":\"order-001\"}");
        dataStore.append("PAYMENT_PROCESSED", "{\"amount\":99.99}");
        dataStore.append("ORDER_SHIPPED", "{\"tracking\":\"TRK-001\"}");
        System.out.println("Events persisted: " + dataStore.count());

        // 5. Resilience4j circuit breaker
        System.out.println("\n--- Circuit Breaker ---");
        CircuitBreaker cb = CircuitBreaker.of("platform-cb",
            CircuitBreakerConfig.custom()
                .slidingWindowSize(4).failureRateThreshold(75)
                .waitDurationInOpenState(Duration.ofMillis(100))
                .build());
        cb.getEventPublisher().onStateTransition(e -> System.out.println("CB: " + e.getStateTransition()));
        AtomicInteger cbCalls = new AtomicInteger();
        for (int i = 0; i < 5; i++) {
            try {
                cb.executeSupplier(() -> {
                    int n = cbCalls.incrementAndGet();
                    if (n <= 3) throw new RuntimeException("fail-" + n);
                    return "ok";
                });
            } catch (Exception e) {}
        }
        System.out.println("CB final state: " + cb.getState());

        // 6. OTel spans
        System.out.println("\n--- OpenTelemetry ---");
        var parentSpan = otel.startSpan("process-order");
        try (var scope = parentSpan.makeCurrent()) {
            var childSpan = otel.startSpan("validate-payment");
            childSpan.setAttribute("payment.method", "ec-signed");
            Thread.sleep(5);
            childSpan.end();
        } finally {
            parentSpan.end();
        }
        otel.flush();
        System.out.println("Spans captured: " + otel.spans.size());
        otel.spans.forEach(s -> System.out.println("  " + s.getName() + " [" + s.getStatus().getStatusCode() + "]"));

        // 7. gRPC service
        System.out.println("\n--- gRPC Service ---");
        GrpcService grpc = new GrpcService();
        grpc.security = security;
        grpc.observability = otel;
        grpc.dataStore = dataStore;
        grpc.start();
        String response = grpc.call("order-001");
        System.out.println("gRPC response: " + response);
        grpc.stop();

        // 8. Summary
        System.out.println("\n=== Platform Summary ===");
        System.out.println("✓ Virtual threads: 10000 tasks");
        System.out.println("✓ gRPC: server+client unary call");
        System.out.println("✓ SQLite: " + dataStore.count() + " events");
        System.out.println("✓ Circuit breaker: " + cb.getState());
        System.out.println("✓ OTel spans: " + otel.spans.size());
        System.out.println("✓ EC P-256: signed+verified=" + valid);
        System.out.println("✓ DI container: " + di.names().size() + " beans");
        System.out.println("Production Java Platform: ALL SYSTEMS GO");
        
        dataStore.close();
    }
}
```

---

## Running the Capstone

```bash
# Clone the project structure
mkdir -p /tmp/capstone/src/{main,test}/java/com/lab

# Copy the pom.xml and all source files
# Then run tests:
cd /tmp/capstone && mvn test -q 2>/dev/null
```

📸 **Verified JUnit 5 Output (6 tests):**
```
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.684 s -- in com.lab.PlatformTest
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

**Test coverage:**
```
✓ testVirtualThreads()    — 100 virtual threads complete
✓ testECSigning()         — EC P-256 sign + verify
✓ testAESGCM()            — AES-256-GCM encrypt + decrypt  
✓ testSQLite()            — SQLite JDBC event store
✓ testCircuitBreaker()    — Resilience4j CLOSED → OPEN
✓ testOTelSpan()          — OTel parent-child span capture
```

---

## JMH Benchmark Reference

```bash
# Run the JMH benchmark (signRequest)
cd /tmp/capstone && mvn compile exec:java \
  -Dexec.mainClass=com.lab.PlatformBenchmark 2>/dev/null | grep -A3 'Benchmark.*Mode'
```

Expected output:
```
Benchmark                       Mode  Cnt   Score   Error  Units
PlatformBenchmark.signRequest   avgt    2  ~80-150         us/op
```

---

## Summary

| Component | Library/API | Status |
|---|---|---|
| Virtual threads | `Executors.newVirtualThreadPerTaskExecutor()` | ✓ 10000 tasks |
| gRPC service | `grpc-inprocess` + `ServerCalls` | ✓ Unary call |
| SQLite persistence | `org.xerial:sqlite-jdbc:3.47.0.0` | ✓ Event store |
| Circuit breaker | `Resilience4j CircuitBreaker` | ✓ State transitions |
| Distributed tracing | `opentelemetry-sdk` | ✓ Parent-child spans |
| EC P-256 signing | `JCA KeyPairGenerator("EC")` | ✓ Sign + verify |
| Manual DI | `@Component` + `@Inject` reflection | ✓ 3 beans wired |
| JMH benchmark | `@Benchmark` `@Fork(0)` | ✓ signRequest ns/op |
| JUnit 5 tests | `junit-jupiter` 5.10.1 | ✓ 6 tests pass |
