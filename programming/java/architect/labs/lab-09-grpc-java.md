# Lab 09: gRPC with Java

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Build production gRPC services in Java: define services, create in-process servers for testing, use blocking and async stubs, implement server-streaming, add interceptors, and propagate deadlines. All examples verified with the gRPC in-process transport.

---

## Step 1: gRPC Architecture

```
gRPC Communication Models:
  Unary         — request/response (like REST)
  Server-stream — 1 request, N responses
  Client-stream — N requests, 1 response
  Bidirectional — N requests, N responses

Stack:
  Java Application
       │
  gRPC Stub (blocking / async / future)
       │
  Protocol Buffers serialization
       │
  HTTP/2 framing
       │
  TLS (optional)
       │
  Network

Key classes:
  ServerBuilder          — configure and start gRPC server
  ManagedChannel         — client connection pool
  ServerInterceptor      — server-side middleware
  ClientInterceptor      — client-side middleware
  Metadata               — HTTP/2 headers
  Status / StatusCode    — gRPC error codes
  StreamObserver         — async response handler
```

---

## Step 2: Service Definition (Manual, No Protoc)

In production you'd use `.proto` files and the `protoc-gen-grpc-java` plugin. Here we define services manually using `MethodDescriptor`:

```java
import io.grpc.*;
import io.grpc.stub.*;

public class ServiceDefinition {
    static final String SERVICE_NAME = "com.lab.Greeter";
    
    // Custom marshaller for String messages
    static class StringMarshaller implements MethodDescriptor.Marshaller<String> {
        @Override
        public java.io.InputStream stream(String value) {
            return new java.io.ByteArrayInputStream(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        @Override
        public String parse(java.io.InputStream stream) {
            try { return new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8); }
            catch (Exception e) { throw new RuntimeException(e); }
        }
    }
    
    static final MethodDescriptor<String, String> SAY_HELLO =
        MethodDescriptor.<String, String>newBuilder()
            .setType(MethodDescriptor.MethodType.UNARY)
            .setFullMethodName(MethodDescriptor.generateFullMethodName(SERVICE_NAME, "SayHello"))
            .setRequestMarshaller(new StringMarshaller())
            .setResponseMarshaller(new StringMarshaller())
            .build();
    
    static final MethodDescriptor<String, String> CHAT =
        MethodDescriptor.<String, String>newBuilder()
            .setType(MethodDescriptor.MethodType.SERVER_STREAMING)
            .setFullMethodName(MethodDescriptor.generateFullMethodName(SERVICE_NAME, "Chat"))
            .setRequestMarshaller(new StringMarshaller())
            .setResponseMarshaller(new StringMarshaller())
            .build();
}
```

---

## Step 3: In-Process Server and Unary Call

```xml
<!-- pom.xml -->
<dependencies>
  <dependency>
    <groupId>io.grpc</groupId><artifactId>grpc-netty-shaded</artifactId><version>1.58.0</version>
  </dependency>
  <dependency>
    <groupId>io.grpc</groupId><artifactId>grpc-core</artifactId><version>1.58.0</version>
  </dependency>
  <dependency>
    <groupId>io.grpc</groupId><artifactId>grpc-stub</artifactId><version>1.58.0</version>
  </dependency>
  <dependency>
    <groupId>io.grpc</groupId><artifactId>grpc-inprocess</artifactId><version>1.58.0</version>
  </dependency>
</dependencies>
```

```java
import io.grpc.*;
import io.grpc.inprocess.*;
import io.grpc.stub.*;
import java.util.concurrent.*;

public class UnaryCallDemo {
    public static void main(String[] args) throws Exception {
        String serverName = InProcessServerBuilder.generateName();
        
        // Build server with service handler
        Server server = InProcessServerBuilder.forName(serverName)
            .directExecutor()
            .addService(ServerServiceDefinition.builder(SERVICE_NAME)
                .addMethod(SAY_HELLO, ServerCalls.asyncUnaryCall(
                    (request, responseObserver) -> {
                        String response = "Hello, " + request + "!";
                        responseObserver.onNext(response);
                        responseObserver.onCompleted();
                    }))
                .build())
            .build()
            .start();
        
        // Build client channel
        ManagedChannel channel = InProcessChannelBuilder
            .forName(serverName)
            .directExecutor()
            .build();
        
        // Make unary call
        ClientCall<String, String> call = channel.newCall(SAY_HELLO, CallOptions.DEFAULT);
        CompletableFuture<String> result = new CompletableFuture<>();
        
        call.start(new ClientCall.Listener<String>() {
            @Override public void onMessage(String message) { result.complete(message); }
            @Override public void onClose(Status status, Metadata trailers) {
                if (!status.isOk()) result.completeExceptionally(status.asException());
            }
        }, new Metadata());
        call.sendMessage("World");
        call.halfClose();
        call.request(1);
        
        System.out.println("Response: " + result.get(5, TimeUnit.SECONDS));
        
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        server.shutdown().awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

---

## Step 4: Server Streaming

```java
import io.grpc.*;
import io.grpc.inprocess.*;
import io.grpc.stub.*;
import java.util.*;
import java.util.concurrent.*;

public class ServerStreamingDemo {
    public static void main(String[] args) throws Exception {
        String serverName = InProcessServerBuilder.generateName();
        CountDownLatch latch = new CountDownLatch(1);
        List<String> responses = new CopyOnWriteArrayList<>();
        
        // Server streams multiple responses
        Server server = InProcessServerBuilder.forName(serverName)
            .directExecutor()
            .addService(ServerServiceDefinition.builder(SERVICE_NAME)
                .addMethod(CHAT, ServerCalls.asyncServerStreamingCall(
                    (request, responseObserver) -> {
                        String[] words = request.split(" ");
                        for (String word : words) {
                            responseObserver.onNext("Echo: " + word);
                        }
                        responseObserver.onCompleted();
                    }))
                .build())
            .build().start();
        
        ManagedChannel channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();
        ClientCall<String, String> call = channel.newCall(CHAT, CallOptions.DEFAULT);
        
        call.start(new ClientCall.Listener<String>() {
            @Override public void onMessage(String m) {
                responses.add(m);
                call.request(1); // request next message
            }
            @Override public void onClose(Status s, Metadata t) { latch.countDown(); }
        }, new Metadata());
        call.sendMessage("Hello World Stream");
        call.halfClose();
        call.request(1); // initial request
        
        latch.await(5, TimeUnit.SECONDS);
        System.out.println("Streamed responses: " + responses);
        
        channel.shutdown(); server.shutdown();
    }
}
```

---

## Step 5: Interceptors

```java
import io.grpc.*;
import io.grpc.inprocess.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class InterceptorDemo {
    // Server interceptor for logging + metrics
    static class LoggingInterceptor implements ServerInterceptor {
        AtomicLong requestCount = new AtomicLong();
        
        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            
            long id = requestCount.incrementAndGet();
            String method = call.getMethodDescriptor().getFullMethodName();
            System.out.println("[Interceptor] Request #" + id + " → " + method);
            
            // Check for auth token
            String token = headers.get(Metadata.Key.of("x-auth-token", Metadata.ASCII_STRING_MARSHALLER));
            if (token == null) {
                System.out.println("[Interceptor] Warning: no auth token");
            }
            
            // Wrap the call to track completion
            return next.startCall(new ForwardingServerCall.SimpleForwardingServerCall<>(call) {
                @Override public void close(Status status, Metadata trailers) {
                    System.out.println("[Interceptor] Response #" + id + " status=" + status.getCode());
                    super.close(status, trailers);
                }
            }, headers);
        }
    }
    
    public static void main(String[] args) throws Exception {
        String serverName = InProcessServerBuilder.generateName();
        LoggingInterceptor interceptor = new LoggingInterceptor();
        
        Server server = InProcessServerBuilder.forName(serverName)
            .directExecutor()
            .intercept(interceptor) // server-wide interceptor
            .addService(ServerServiceDefinition.builder(SERVICE_NAME)
                .addMethod(SAY_HELLO, ServerCalls.asyncUnaryCall(
                    (req, obs) -> { obs.onNext("Hello, " + req); obs.onCompleted(); }))
                .build())
            .build().start();
        
        ManagedChannel channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();
        
        // Make 2 calls
        for (int i = 0; i < 2; i++) {
            ClientCall<String, String> call = channel.newCall(SAY_HELLO, CallOptions.DEFAULT);
            CompletableFuture<String> f = new CompletableFuture<>();
            call.start(new ClientCall.Listener<String>() {
                public void onMessage(String m) { f.complete(m); }
                public void onClose(Status s, Metadata t) { if(!s.isOk()) f.completeExceptionally(s.asException()); }
            }, new Metadata());
            call.sendMessage("Client-" + i); call.halfClose(); call.request(1);
            System.out.println("Response: " + f.get(5, TimeUnit.SECONDS));
        }
        
        System.out.println("Total intercepted: " + interceptor.requestCount.get());
        channel.shutdown(); server.shutdown();
    }
}
```

---

## Step 6: Deadline Propagation

```java
import io.grpc.*;
import io.grpc.inprocess.*;
import java.util.concurrent.*;

public class DeadlineDemo {
    public static void main(String[] args) throws Exception {
        String serverName = InProcessServerBuilder.generateName();
        
        Server server = InProcessServerBuilder.forName(serverName)
            .directExecutor()
            .addService(ServerServiceDefinition.builder(SERVICE_NAME)
                .addMethod(SAY_HELLO, ServerCalls.asyncUnaryCall(
                    (req, obs) -> {
                        try {
                            Thread.sleep(500); // simulate slow operation
                        } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                        obs.onNext("Late response");
                        obs.onCompleted();
                    }))
                .build())
            .build().start();
        
        ManagedChannel channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();
        
        // Set 100ms deadline — server takes 500ms → DEADLINE_EXCEEDED
        CallOptions opts = CallOptions.DEFAULT.withDeadlineAfter(100, TimeUnit.MILLISECONDS);
        ClientCall<String, String> call = channel.newCall(SAY_HELLO, opts);
        
        CompletableFuture<Status> statusFuture = new CompletableFuture<>();
        call.start(new ClientCall.Listener<String>() {
            public void onMessage(String m) {}
            public void onClose(Status s, Metadata t) { statusFuture.complete(s); }
        }, new Metadata());
        call.sendMessage("Test"); call.halfClose(); call.request(1);
        
        Status status = statusFuture.get(5, TimeUnit.SECONDS);
        System.out.println("Deadline exceeded: " + (status.getCode() == Status.Code.DEADLINE_EXCEEDED));
        System.out.println("Status code: " + status.getCode());
        
        channel.shutdown(); server.shutdown();
    }
}
```

> 💡 Deadlines propagate across services automatically via gRPC context. Always set deadlines at the edge and let gRPC propagate them.

---

## Step 7: Error Handling with Status

```java
// gRPC Status codes map to HTTP/2 and gRPC errors:
// Status.OK              (0)  — success
// Status.CANCELLED       (1)  — client cancelled
// Status.NOT_FOUND       (5)  — resource not found
// Status.ALREADY_EXISTS  (6)  — resource already exists
// Status.UNAUTHENTICATED (16) — no credentials
// Status.PERMISSION_DENIED(7) — credentials insufficient
// Status.UNAVAILABLE     (14) — service down, retry
// Status.DEADLINE_EXCEEDED(4) — timeout

// Server: throw StatusException or StatusRuntimeException
// responseObserver.onError(Status.NOT_FOUND
//     .withDescription("User " + userId + " not found")
//     .withCause(cause)
//     .asRuntimeException());

// Client: catch StatusRuntimeException
// try {
//     stub.getUser(request);
// } catch (StatusRuntimeException e) {
//     Status status = e.getStatus();
//     switch (status.getCode()) {
//         case NOT_FOUND -> handleNotFound();
//         case UNAVAILABLE -> retryWithBackoff();
//         case UNAUTHENTICATED -> refreshToken();
//     }
// }

public class StatusCodeDemo {
    public static void main(String[] args) {
        System.out.println("gRPC Status → HTTP mapping:");
        System.out.println("  OK            → 200");
        System.out.println("  NOT_FOUND     → 404");
        System.out.println("  UNAVAILABLE   → 503");
        System.out.println("  PERMISSION_DENIED → 403");
        System.out.println("  DEADLINE_EXCEEDED → 504");
    }
}
```

---

## Step 8: Capstone — gRPC In-Process Server + Client

```java
package com.lab;

import io.grpc.*;
import io.grpc.inprocess.*;
import io.grpc.stub.*;
import java.util.concurrent.*;

public class Main {
    static final String SERVICE = "com.lab.Greeter";
    static final MethodDescriptor<String, String> SAY_HELLO =
        MethodDescriptor.<String, String>newBuilder()
            .setType(MethodDescriptor.MethodType.UNARY)
            .setFullMethodName(SERVICE + "/SayHello")
            .setRequestMarshaller(new StringMarshaller())
            .setResponseMarshaller(new StringMarshaller())
            .build();

    static class StringMarshaller implements MethodDescriptor.Marshaller<String> {
        public java.io.InputStream stream(String s) { return new java.io.ByteArrayInputStream(s.getBytes()); }
        public String parse(java.io.InputStream is) {
            try { return new String(is.readAllBytes()); } catch(Exception e) { throw new RuntimeException(e); }
        }
    }

    public static void main(String[] args) throws Exception {
        String name = InProcessServerBuilder.generateName();
        Server server = InProcessServerBuilder.forName(name)
            .directExecutor()
            .addService(ServerServiceDefinition.builder(SERVICE)
                .addMethod(SAY_HELLO, ServerCalls.asyncUnaryCall(
                    (req, observer) -> { observer.onNext("Hello, " + req + "!"); observer.onCompleted(); }))
                .build())
            .build().start();
        System.out.println("gRPC server started (in-process): " + name);

        ManagedChannel channel = InProcessChannelBuilder.forName(name).directExecutor().build();
        ClientCall<String, String> call = channel.newCall(SAY_HELLO, CallOptions.DEFAULT);
        CompletableFuture<String> response = new CompletableFuture<>();
        call.start(new ClientCall.Listener<String>() {
            public void onMessage(String m) { response.complete(m); }
            public void onClose(Status s, Metadata t) { if(!s.isOk()) response.completeExceptionally(new Exception(s.toString())); }
        }, new Metadata());
        call.sendMessage("World"); call.halfClose(); call.request(1);

        System.out.println("gRPC response: " + response.get(5, TimeUnit.SECONDS));
        System.out.println("ManagedChannel state: " + channel.getState(false));
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        server.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("gRPC unary call: SUCCESS");
    }
}
```

```bash
# Maven project with grpc-inprocess dependency
cd /tmp/grpc && mvn compile exec:java -Dexec.mainClass=com.lab.Main -q 2>/dev/null
```

📸 **Verified Output:**
```
gRPC server started (in-process): 0ac116c6-e831-4081-b7c5-634a146fa6c7
gRPC response: Hello, World!
ManagedChannel state: READY
gRPC unary call: SUCCESS
```

---

## Summary

| Concept | API/Class | Purpose |
|---|---|---|
| Service definition | `ServerServiceDefinition` | Bind methods to handlers |
| Unary handler | `ServerCalls.asyncUnaryCall()` | Single request/response |
| Server streaming | `asyncServerStreamingCall()` | Multiple responses |
| Client channel | `ManagedChannel` | Connection pool to server |
| Call options | `CallOptions.withDeadlineAfter()` | Timeout, credentials |
| Server interceptor | `ServerInterceptor` | Logging, auth, metrics |
| Status codes | `Status.Code.*` | gRPC error classification |
| In-process transport | `InProcessServerBuilder` | Test without network |
