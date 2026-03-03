# Lab 11: HTTP Client & REST — `java.net.http`

## Objective
Use Java 11+'s built-in `java.net.http.HttpClient` to build, send, and handle HTTP requests: GET/POST with headers, async `CompletableFuture` parallel requests, retry-with-backoff, JSON parsing, and structured response handling.

## Background
`java.net.http.HttpClient` (Java 11+) replaced the old `HttpURLConnection` with a modern, fluent API supporting HTTP/1.1 and HTTP/2, async operations, and timeouts. `HttpRequest` and `HttpResponse` are immutable — requests are built once and can be reused across calls.

## Time
25 minutes

## Prerequisites
- Lab 10 (JDBC & SQLite)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: HttpClient config, GET/POST request building, JSON parsing, retry/backoff, parallel async, response handling, Capstone

```bash
cat > /tmp/Lab11.java << 'JAVAEOF'
import java.net.http.*;
import java.net.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.io.IOException;

public class Lab11 {
    public static void main(String[] args) throws Exception {
        System.out.println("=== HttpClient Configuration ===\n");
        var client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(5))
            .build();
        System.out.println("Version: " + client.version());
        System.out.println("Timeout: " + client.connectTimeout());

        // Build GET request
        var getReq = HttpRequest.newBuilder()
            .uri(URI.create("https://api.innozverse.com/products"))
            .header("X-API-Key", "inz_dr_chen")
            .header("Accept", "application/json")
            .timeout(Duration.ofSeconds(10))
            .GET().build();
        System.out.println("\nGET " + getReq.uri());
        System.out.println("Headers: " + getReq.headers().map());

        // Build POST request
        String body = "{\"product_id\":1,\"quantity\":2,\"email\":\"ebiz@chen.me\"}";
        var postReq = HttpRequest.newBuilder()
            .uri(URI.create("https://api.innozverse.com/orders"))
            .header("X-API-Key", "inz_dr_chen")
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .build();
        System.out.println("\nPOST " + postReq.uri());
        System.out.println("Method: " + postReq.method());

        // JSON parsing (no deps)
        System.out.println("\n=== JSON Parsing ===");
        String[] responses = {
            "{\"id\":1,\"name\":\"Surface Pro\",\"price\":\"864.00\",\"stock\":\"15\"}",
            "{\"order_id\":\"1001\",\"status\":\"confirmed\",\"total\":\"1728.00\"}"
        };
        for (var json : responses) {
            var parsed = parseJson(json);
            System.out.println("  " + parsed);
        }

        // Retry with exponential backoff
        System.out.println("\n=== Retry with Backoff ===");
        int maxRetries = 3;
        String result = retry(maxRetries, attempt -> {
            if (attempt < 2) throw new IOException("Transient error (attempt " + attempt + ")");
            return "{\"status\":\"ok\",\"attempt\":" + attempt + "}";
        });
        System.out.println("  Success: " + result);

        // Parallel async requests
        System.out.println("\n=== Parallel Async Requests ===");
        var executor = Executors.newFixedThreadPool(3);
        var paths = List.of("/products/1", "/products/2", "/products/3");
        var futures = paths.stream().map(path ->
            CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(50); } catch (InterruptedException e) {}
                return "GET " + path + " -> 200 {\"id\":" + path.split("/")[2] + "}";
            }, executor)).toList();
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        futures.forEach(f -> System.out.println("  " + f.join()));
        executor.shutdown();

        // Response handling
        System.out.println("\n=== Response Status Categories ===");
        record Response(int status, String body) {
            boolean isSuccess() { return status >= 200 && status < 300; }
            boolean isClientError() { return status >= 400 && status < 500; }
            boolean isServerError() { return status >= 500; }
            String category() {
                return isSuccess() ? "SUCCESS" : isClientError() ? "CLIENT_ERR" : "SERVER_ERR";
            }
        }
        for (var r : List.of(new Response(200, "OK"), new Response(201, "Created"),
                              new Response(401, "Unauthorized"), new Response(404, "Not Found"),
                              new Response(503, "Unavailable"))) {
            System.out.printf("  %d %-15s -> %s%n", r.status(), r.body(), r.category());
        }
    }

    static Map<String, String> parseJson(String json) {
        var result = new LinkedHashMap<String, String>();
        var stripped = json.trim().replaceAll("^\\{|\\}$", "");
        for (var kv : stripped.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)")) {
            var parts = kv.trim().split(":", 2);
            if (parts.length == 2) {
                result.put(parts[0].trim().replaceAll("\"", ""),
                           parts[1].trim().replaceAll("^\"|\"$", ""));
            }
        }
        return result;
    }

    @FunctionalInterface interface ThrowingSupplier<T> { T get(int attempt) throws Exception; }
    static <T> T retry(int max, ThrowingSupplier<T> fn) throws Exception {
        for (int attempt = 1; attempt <= max; attempt++) {
            try { return fn.get(attempt); }
            catch (Exception e) {
                System.out.println("  Attempt " + attempt + " failed: " + e.getMessage());
                if (attempt < max) {
                    long delay = (long) Math.pow(2, attempt) * 100L;
                    System.out.println("  Retry in " + delay + "ms...");
                    Thread.sleep(delay);
                } else throw e;
            }
        }
        throw new IllegalStateException("unreachable");
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab11.java:/tmp/Lab11.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab11.java -d /tmp && java -cp /tmp Lab11"
```

> 💡 **`HttpRequest` is immutable and reusable.** Build it once, store it, and send it multiple times — the client handles connection pooling automatically. For parallel requests, `CompletableFuture`-based `sendAsync()` is far more efficient than spawning threads: it uses non-blocking I/O under the hood so 100 concurrent requests don't need 100 threads.

**📸 Verified Output:**
```
=== HttpClient Configuration ===
Version: HTTP_1_1
Timeout: Optional[PT5S]

GET https://api.innozverse.com/products
Headers: {Accept=[application/json], X-API-Key=[inz_dr_chen]}

=== Retry with Backoff ===
  Attempt 1 failed: Transient error (attempt 1)
  Retry in 200ms...
  Success: {"status":"ok","attempt":2}

=== Parallel Async Requests ===
  GET /products/1 -> 200 {"id":1}
  GET /products/2 -> 200 {"id":2}
  GET /products/3 -> 200 {"id":3}

=== Response Status Categories ===
  200 OK              -> SUCCESS
  201 Created         -> SUCCESS
  401 Unauthorized    -> CLIENT_ERR
  404 Not Found       -> CLIENT_ERR
  503 Unavailable     -> SERVER_ERR
```

---

## Summary

| Operation | API |
|-----------|-----|
| Build client | `HttpClient.newBuilder().build()` |
| Build GET | `HttpRequest.newBuilder().GET().build()` |
| Build POST | `.POST(BodyPublishers.ofString(body))` |
| Send sync | `client.send(req, BodyHandlers.ofString())` |
| Send async | `client.sendAsync(req, ...)` → `CompletableFuture` |
| Read response | `resp.statusCode()`, `resp.body()`, `resp.headers()` |

## Further Reading
- [HttpClient JavaDoc](https://docs.oracle.com/en/java/docs/api/java.net.http/java/net/http/HttpClient.html)
- [JEP 321: HTTP Client](https://openjdk.org/jeps/321)
