# Lab 06: Reactive Streams with java.util.concurrent.Flow

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Java 9+ ships the Reactive Streams specification as `java.util.concurrent.Flow`. Learn to build `Publisher`/`Subscriber` pipelines with backpressure, compose `Processor` stages, handle errors, and understand how RxJava/Project Reactor implement these same interfaces.

---

## Step 1: Reactive Streams Specification

```
Reactive Streams (RS) contracts:
  1. Publisher<T>     — produces items, respects demand
  2. Subscriber<T>    — consumes items
  3. Subscription     — token controlling demand
  4. Processor<T,R>   — both Publisher AND Subscriber

Flow:
  Publisher.subscribe(Subscriber)
  → onSubscribe(Subscription)    // subscriber receives subscription
  → Subscription.request(n)      // subscriber requests n items
  → onNext(item) × n             // publisher emits up to n items
  → onComplete() | onError(t)    // terminal signal

Backpressure rule:
  Publisher MUST NOT emit more than request(n) items
```

---

## Step 2: SubmissionPublisher — Built-in Publisher

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;

public class SubmissionPublisherDemo {
    public static void main(String[] args) throws Exception {
        // SubmissionPublisher: bounded async publisher with backpressure
        SubmissionPublisher<String> publisher = new SubmissionPublisher<>();
        
        publisher.subscribe(new Subscriber<String>() {
            Subscription sub;
            
            @Override public void onSubscribe(Subscription s) {
                sub = s;
                s.request(Long.MAX_VALUE); // request all (no backpressure here)
            }
            @Override public void onNext(String item) {
                System.out.println("Received: " + item);
            }
            @Override public void onError(Throwable t) {
                System.err.println("Error: " + t.getMessage());
            }
            @Override public void onComplete() {
                System.out.println("Complete!");
            }
        });
        
        publisher.submit("Hello");
        publisher.submit("Reactive");
        publisher.submit("Streams");
        publisher.close(); // triggers onComplete
        
        Thread.sleep(100); // async delivery
    }
}
```

---

## Step 3: Backpressure — Controlled Demand

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;
import java.util.*;

public class BackpressureDemo {
    public static void main(String[] args) throws Exception {
        List<String> received = Collections.synchronizedList(new ArrayList<>());
        CountDownLatch latch = new CountDownLatch(1);
        
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        
        publisher.subscribe(new Subscriber<Integer>() {
            Subscription sub;
            int count = 0;
            
            public void onSubscribe(Subscription s) {
                sub = s;
                System.out.println("Subscribed - requesting 3 items (backpressure)");
                s.request(3); // only request 3 at a time
            }
            
            public void onNext(Integer item) {
                received.add("item-" + item);
                System.out.println("Received: " + item);
                count++;
                if (count % 3 == 0) {
                    System.out.println("Requesting 3 more...");
                    sub.request(3); // request next batch
                }
            }
            
            public void onError(Throwable t) { latch.countDown(); }
            
            public void onComplete() {
                System.out.println("Stream complete! Total: " + received.size());
                latch.countDown();
            }
        });
        
        for (int i = 1; i <= 6; i++) publisher.submit(i);
        publisher.close();
        latch.await(5, TimeUnit.SECONDS);
        System.out.println("Received items: " + received);
    }
}
```

📸 **Verified Output:**
```
Subscribed - requesting 3 items (backpressure)
Received: 1
Received: 2
Received: 3
Requesting 3 more...
Received: 4
Received: 5
Received: 6
Requesting 3 more...
Stream complete! Total: 6
Received items: [item-1, item-2, item-3, item-4, item-5, item-6]
```

---

## Step 4: Custom Publisher Implementation

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;
import java.util.concurrent.atomic.*;

public class RangePublisher implements Publisher<Integer> {
    private final int from, to;
    
    public RangePublisher(int from, int to) { this.from = from; this.to = to; }
    
    @Override
    public void subscribe(Subscriber<? super Integer> subscriber) {
        subscriber.onSubscribe(new RangeSubscription(subscriber, from, to));
    }
    
    static class RangeSubscription implements Subscription {
        private final Subscriber<? super Integer> subscriber;
        private final AtomicLong demand = new AtomicLong();
        private final AtomicBoolean cancelled = new AtomicBoolean();
        private final AtomicInteger current;
        private final int to;
        
        RangeSubscription(Subscriber<? super Integer> sub, int from, int to) {
            this.subscriber = sub;
            this.current = new AtomicInteger(from);
            this.to = to;
        }
        
        @Override
        public void request(long n) {
            if (n <= 0) { subscriber.onError(new IllegalArgumentException("n must be > 0")); return; }
            demand.addAndGet(n);
            drain();
        }
        
        private void drain() {
            while (demand.get() > 0 && !cancelled.get()) {
                int val = current.getAndIncrement();
                if (val > to) { subscriber.onComplete(); return; }
                demand.decrementAndGet();
                subscriber.onNext(val);
            }
        }
        
        @Override public void cancel() { cancelled.set(true); }
    }
    
    public static void main(String[] args) throws Exception {
        CountDownLatch latch = new CountDownLatch(1);
        new RangePublisher(1, 5).subscribe(new Subscriber<Integer>() {
            public void onSubscribe(Subscription s) { s.request(Long.MAX_VALUE); }
            public void onNext(Integer i) { System.out.println("Item: " + i); }
            public void onError(Throwable t) { latch.countDown(); }
            public void onComplete() { System.out.println("Done"); latch.countDown(); }
        });
        latch.await();
    }
}
```

> 💡 The `drain()` loop is the heart of a Publisher — it emits items respecting demand while checking for cancellation.

---

## Step 5: Processor — Transform Pipeline

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;
import java.util.function.*;

public class MapProcessor<T, R> extends SubmissionPublisher<R>
        implements Processor<T, R> {
    
    private final Function<T, R> mapper;
    private Subscription upstream;
    
    public MapProcessor(Function<T, R> mapper) { this.mapper = mapper; }
    
    @Override
    public void onSubscribe(Subscription subscription) {
        this.upstream = subscription;
        subscription.request(Long.MAX_VALUE);
    }
    
    @Override
    public void onNext(T item) {
        submit(mapper.apply(item)); // transform and re-publish
    }
    
    @Override
    public void onError(Throwable throwable) { closeExceptionally(throwable); }
    
    @Override
    public void onComplete() { close(); }
    
    public static void main(String[] args) throws Exception {
        CountDownLatch latch = new CountDownLatch(1);
        
        // Pipeline: RangePublisher → MapProcessor (x*2) → MapProcessor (toString) → Subscriber
        SubmissionPublisher<Integer> source = new SubmissionPublisher<>();
        MapProcessor<Integer, Integer> doubler = new MapProcessor<>(x -> x * 2);
        MapProcessor<Integer, String> stringer = new MapProcessor<>(x -> "val=" + x);
        
        source.subscribe(doubler);
        doubler.subscribe(stringer);
        stringer.subscribe(new Subscriber<String>() {
            public void onSubscribe(Subscription s) { s.request(Long.MAX_VALUE); }
            public void onNext(String s) { System.out.println("Pipeline output: " + s); }
            public void onError(Throwable t) { latch.countDown(); }
            public void onComplete() { System.out.println("Pipeline complete"); latch.countDown(); }
        });
        
        for (int i = 1; i <= 4; i++) source.submit(i);
        source.close();
        latch.await(5, TimeUnit.SECONDS);
    }
}
```

---

## Step 6: Error Handling and Cancellation

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;

public class ErrorHandlingDemo {
    public static void main(String[] args) throws Exception {
        CountDownLatch latch = new CountDownLatch(1);
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        
        publisher.subscribe(new Subscriber<Integer>() {
            Subscription sub;
            int count = 0;
            
            public void onSubscribe(Subscription s) {
                sub = s;
                s.request(10);
            }
            
            public void onNext(Integer item) {
                count++;
                System.out.println("Processing item: " + item);
                if (item == 3) {
                    // Explicit cancellation
                    System.out.println("Cancelling at item 3");
                    sub.cancel();
                    latch.countDown();
                }
            }
            
            public void onError(Throwable t) {
                System.out.println("onError: " + t.getMessage());
                latch.countDown();
            }
            
            public void onComplete() { System.out.println("onComplete"); latch.countDown(); }
        });
        
        for (int i = 1; i <= 10; i++) {
            publisher.submit(i);
            Thread.sleep(5);
        }
        
        latch.await(5, TimeUnit.SECONDS);
        publisher.close();
        System.out.println("Cancellation test complete");
        
        // closeExceptionally for error propagation
        SubmissionPublisher<String> ep = new SubmissionPublisher<>();
        CountDownLatch el = new CountDownLatch(1);
        ep.subscribe(new Subscriber<String>() {
            public void onSubscribe(Subscription s) { s.request(Long.MAX_VALUE); }
            public void onNext(String s) {}
            public void onError(Throwable t) { System.out.println("onError received: " + t.getMessage()); el.countDown(); }
            public void onComplete() { el.countDown(); }
        });
        ep.closeExceptionally(new RuntimeException("Upstream failure"));
        el.await(2, TimeUnit.SECONDS);
    }
}
```

---

## Step 7: Comparison — Flow vs RxJava vs Reactor

```java
// java.util.concurrent.Flow (JDK built-in, verbose but portable):
publisher.subscribe(subscriber);

// RxJava 3 (adds operators, schedulers):
// Observable.range(1, 10)
//   .map(x -> x * 2)
//   .filter(x -> x > 5)
//   .subscribeOn(Schedulers.io())
//   .observeOn(AndroidSchedulers.mainThread())
//   .subscribe(System.out::println);

// Project Reactor (Spring ecosystem, Mono/Flux):
// Flux.range(1, 10)
//   .map(x -> x * 2)
//   .filter(x -> x > 5)
//   .publishOn(Schedulers.boundedElastic())
//   .subscribe(System.out::println);

// All three implement the same RS interfaces under the hood:
// Publisher<T>, Subscriber<T>, Subscription, Processor<T,R>

public class ComparisonNotes {
    public static void main(String[] args) {
        System.out.println("Flow API Comparison:");
        System.out.println("  JDK Flow    — built-in, no operators, portable");
        System.out.println("  RxJava 3    — rich operators, Android-friendly");
        System.out.println("  Reactor     — Spring ecosystem, Mono/Flux");
        System.out.println("  SmallRye    — MicroProfile reactive streams");
        System.out.println("All share: Publisher → onSubscribe → request(n) → onNext × n → onComplete");
    }
}
```

---

## Step 8: Capstone — Full Reactive Pipeline

```java
import java.util.concurrent.*;
import java.util.concurrent.Flow.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        List<String> received = Collections.synchronizedList(new ArrayList<>());
        CountDownLatch latch = new CountDownLatch(1);
        
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        
        publisher.subscribe(new Subscriber<Integer>() {
            Subscription sub;
            int count = 0;
            public void onSubscribe(Subscription s) {
                sub = s;
                System.out.println("Subscribed - requesting 3 items (backpressure)");
                s.request(3);
            }
            public void onNext(Integer item) {
                received.add("item-" + item);
                System.out.println("Received: " + item);
                count++;
                if (count % 3 == 0) { System.out.println("Requesting 3 more..."); sub.request(3); }
            }
            public void onError(Throwable t) { System.out.println("Error: " + t.getMessage()); latch.countDown(); }
            public void onComplete() { System.out.println("Stream complete! Total: " + received.size()); latch.countDown(); }
        });
        
        for (int i = 1; i <= 6; i++) publisher.submit(i);
        publisher.close();
        latch.await(5, TimeUnit.SECONDS);
        System.out.println("Received items: " + received);
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
Subscribed - requesting 3 items (backpressure)
Received: 1
Received: 2
Received: 3
Requesting 3 more...
Received: 4
Received: 5
Received: 6
Requesting 3 more...
Stream complete! Total: 6
Received items: [item-1, item-2, item-3, item-4, item-5, item-6]
```

---

## Summary

| Concept | Interface/Class | Key Method |
|---|---|---|
| Publisher | `Publisher<T>` | `subscribe(Subscriber)` |
| Subscriber | `Subscriber<T>` | `onNext/onError/onComplete` |
| Subscription | `Subscription` | `request(n)`, `cancel()` |
| Processor | `Processor<T,R>` | Both Publisher and Subscriber |
| Built-in publisher | `SubmissionPublisher<T>` | `submit()`, `close()` |
| Backpressure | `Subscription.request(n)` | Demand-driven flow control |
| Error propagation | `closeExceptionally()` | `onError()` called |
| Cancellation | `Subscription.cancel()` | Stop receiving items |
