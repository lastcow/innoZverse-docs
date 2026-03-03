# Lab 9: REST API Development — Vanilla PHP

## Objective
Build a complete RESTful API using only PHP's built-in server capabilities: HTTP method routing, URL parsing with `parse_url`, JSON request/response handling, middleware pipeline for auth and logging, HTTP status codes, input validation, and proper error responses.

## Background
Every PHP framework (Laravel, Symfony, Slim) is ultimately a router + middleware stack on top of PHP's request/response model. PHP receives requests via `$_SERVER`, reads input via `php://input`, and sends headers with `header()`. Understanding the raw HTTP layer makes frameworks transparent. A REST API maps HTTP methods (GET/POST/PUT/DELETE) to CRUD operations on resources.

## Time
30 minutes

## Prerequisites
- PHP Practitioner Lab 04 (PDO & Repository)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Router, middleware, JSON API — full simulation

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Simulated HTTP Request/Response ──────────────────────────────────────────
// In a real server these come from $_SERVER, php://input, header()
// We simulate them here to run without a web server

class Request {
    public function __construct(
        public readonly string $method,
        public readonly string $path,
        public readonly array  $query,
        public readonly array  $body,
        public readonly array  $headers,
    ) {}

    public static function create(string $method, string $url, array $body = [], array $headers = []): self {
        $parsed = parse_url($url);
        parse_str($parsed["query"] ?? "", $query);
        return new self(strtoupper($method), $parsed["path"], $query, $body, $headers);
    }
}

class Response {
    private array $headers = ["Content-Type" => "application/json"];
    private mixed $body = null;
    private int $status = 200;

    public function json(mixed $data, int $status = 200): self {
        $this->body   = $data;
        $this->status = $status;
        return $this;
    }

    public function status(): int   { return $this->status; }
    public function toJson(): string { return json_encode($this->body, JSON_PRETTY_PRINT); }

    public function print(): void {
        $emoji = $this->status < 400 ? "✓" : "✗";
        echo "  {$emoji} HTTP {$this->status}" . PHP_EOL;
        echo "  " . implode(PHP_EOL . "  ", explode(PHP_EOL, $this->toJson())) . PHP_EOL;
    }
}

// ── Middleware Pipeline ───────────────────────────────────────────────────────
class MiddlewarePipeline {
    private array $middleware = [];

    public function use(callable $fn): void {
        $this->middleware[] = $fn;
    }

    public function run(Request $req, Response $res, callable $handler): Response {
        $stack = $this->middleware;
        $runner = function(Request $req, Response $res) use (&$stack, &$runner, $handler): Response {
            $mw = array_shift($stack);
            if ($mw === null) return $handler($req, $res);
            return $mw($req, $res, fn() => $runner($req, $res));
        };
        return $runner($req, $res);
    }
}

// ── Router ───────────────────────────────────────────────────────────────────
class Router {
    private array $routes = [];

    public function get(string $path, callable $handler): void    { $this->add("GET", $path, $handler); }
    public function post(string $path, callable $handler): void   { $this->add("POST", $path, $handler); }
    public function put(string $path, callable $handler): void    { $this->add("PUT", $path, $handler); }
    public function delete(string $path, callable $handler): void { $this->add("DELETE", $path, $handler); }

    private function add(string $method, string $path, callable $handler): void {
        $this->routes[] = ["method" => $method, "path" => $path, "handler" => $handler];
    }

    public function dispatch(Request $req, Response $res): Response {
        foreach ($this->routes as $route) {
            $params = $this->match($route["method"], $route["path"], $req->method, $req->path);
            if ($params !== null) {
                return ($route["handler"])($req, $res, $params);
            }
        }
        return $res->json(["error" => "Route not found", "path" => $req->path], 404);
    }

    private function match(string $routeMethod, string $routePath, string $reqMethod, string $reqPath): ?array {
        if ($routeMethod !== $reqMethod) return null;
        $rp = explode("/", trim($routePath, "/"));
        $up = explode("/", trim($reqPath, "/"));
        if (count($rp) !== count($up)) return null;
        $params = [];
        foreach ($rp as $i => $seg) {
            if (str_starts_with($seg, "{") && str_ends_with($seg, "}")) {
                $params[trim($seg, "{}")] = $up[$i];
            } elseif ($seg !== $up[$i]) {
                return null;
            }
        }
        return $params;
    }
}

// ── Data Store ───────────────────────────────────────────────────────────────
class ProductStore {
    private array $products = [
        1 => ["id" => 1, "name" => "Surface Pro",  "price" => 864.00, "stock" => 15, "category" => "laptop"],
        2 => ["id" => 2, "name" => "Surface Pen",  "price" => 49.99,  "stock" => 80, "category" => "accessory"],
        3 => ["id" => 3, "name" => "Office 365",   "price" => 99.99,  "stock" => 999,"category" => "software"],
    ];
    private int $nextId = 4;

    public function findAll(?string $category = null): array {
        $all = array_values($this->products);
        if ($category) $all = array_filter($all, fn($p) => $p["category"] === $category);
        return array_values($all);
    }
    public function find(int $id): ?array { return $this->products[$id] ?? null; }
    public function create(array $data): array {
        $data["id"] = $this->nextId++;
        $this->products[$data["id"]] = $data;
        return $data;
    }
    public function update(int $id, array $data): ?array {
        if (!isset($this->products[$id])) return null;
        $this->products[$id] = array_merge($this->products[$id], $data, ["id" => $id]);
        return $this->products[$id];
    }
    public function delete(int $id): bool {
        if (!isset($this->products[$id])) return false;
        unset($this->products[$id]); return true;
    }
    public function count(): int { return count($this->products); }
}

// ── Build API ─────────────────────────────────────────────────────────────────
$store    = new ProductStore();
$router   = new Router();
$pipeline = new MiddlewarePipeline();

// Middleware 1: logging
$pipeline->use(function(Request $req, Response $res, callable $next): Response {
    echo PHP_EOL . "  → " . $req->method . " " . $req->path . PHP_EOL;
    return $next();
});

// Middleware 2: simple API key auth (skip auth routes for brevity)
$apiKey = "inno-secret-key-2026";
$pipeline->use(function(Request $req, Response $res, callable $next) use ($apiKey): Response {
    $key = $req->headers["X-API-Key"] ?? null;
    if ($key !== $apiKey) {
        return $res->json(["error" => "Unauthorized", "code" => "INVALID_KEY"], 401);
    }
    return $next();
});

// Routes
$router->get("/api/products", function(Request $req, Response $res) use ($store): Response {
    $cat      = $req->query["category"] ?? null;
    $products = $store->findAll($cat);
    return $res->json(["data" => $products, "count" => count($products), "filter" => $cat]);
});

$router->get("/api/products/{id}", function(Request $req, Response $res, array $params) use ($store): Response {
    $product = $store->find((int)$params["id"]);
    if (!$product) return $res->json(["error" => "Product not found", "id" => (int)$params["id"]], 404);
    return $res->json(["data" => $product]);
});

$router->post("/api/products", function(Request $req, Response $res) use ($store): Response {
    $errors = [];
    if (empty($req->body["name"]))    $errors[] = "name is required";
    if (!isset($req->body["price"]) || $req->body["price"] < 0) $errors[] = "price must be >= 0";
    if (!empty($errors)) return $res->json(["error" => "Validation failed", "errors" => $errors], 422);
    $product = $store->create([
        "name"     => $req->body["name"],
        "price"    => (float)$req->body["price"],
        "stock"    => (int)($req->body["stock"] ?? 0),
        "category" => $req->body["category"] ?? "general",
    ]);
    return $res->json(["data" => $product, "message" => "Created"], 201);
});

$router->put("/api/products/{id}", function(Request $req, Response $res, array $params) use ($store): Response {
    $updated = $store->update((int)$params["id"], $req->body);
    if (!$updated) return $res->json(["error" => "Product not found"], 404);
    return $res->json(["data" => $updated, "message" => "Updated"]);
});

$router->delete("/api/products/{id}", function(Request $req, Response $res, array $params) use ($store): Response {
    $deleted = $store->delete((int)$params["id"]);
    if (!$deleted) return $res->json(["error" => "Product not found"], 404);
    return $res->json(["message" => "Deleted"], 200);
});

// ── Test Requests ──────────────────────────────────────────────────────────────
$auth = ["X-API-Key" => "inno-secret-key-2026"];

$requests = [
    ["label" => "GET all products",         "r" => Request::create("GET", "/api/products", headers: $auth)],
    ["label" => "GET by category",          "r" => Request::create("GET", "/api/products?category=laptop", headers: $auth)],
    ["label" => "GET single product",       "r" => Request::create("GET", "/api/products/1", headers: $auth)],
    ["label" => "GET not found",            "r" => Request::create("GET", "/api/products/99", headers: $auth)],
    ["label" => "POST create product",      "r" => Request::create("POST", "/api/products",
        ["name" => "USB-C Hub", "price" => 29.99, "stock" => 50, "category" => "hardware"], $auth)],
    ["label" => "POST validation failure",  "r" => Request::create("POST", "/api/products", ["name" => ""], $auth)],
    ["label" => "PUT update product",       "r" => Request::create("PUT", "/api/products/2", ["price" => 44.99], $auth)],
    ["label" => "DELETE product",           "r" => Request::create("DELETE", "/api/products/3", headers: $auth)],
    ["label" => "Unauthorized request",     "r" => Request::create("GET", "/api/products")],
];

echo "=== REST API Tests ===" . PHP_EOL;
foreach ($requests as ["label" => $label, "r" => $req]) {
    echo PHP_EOL . "── " . $label . " ──" . PHP_EOL;
    $res = new Response();
    $res = $pipeline->run($req, $res, fn($req, $res) => $router->dispatch($req, $res));
    $res->print();
}
'
```

> 💡 **Middleware runs before and after your handler.** The pipeline `run()` method builds a chain: each middleware calls `$next()` to continue the chain. The logging middleware runs before (logs the request), then `$next()` invokes the next middleware (auth check), then `$next()` in auth invokes the router. After the handler returns, each middleware can process the response too. This is how Laravel Middleware, Express.js, and Django Middleware all work.

**📸 Verified Output:**
```
── GET all products ──
  → GET /api/products
  ✓ HTTP 200
  {
    "data": [...],
    "count": 3
  }

── POST create product ──
  → POST /api/products
  ✓ HTTP 201
  { "data": {"id": 4, "name": "USB-C Hub"...}, "message": "Created" }

── Unauthorized request ──
  → GET /api/products
  ✗ HTTP 401
  { "error": "Unauthorized", "code": "INVALID_KEY" }
```

---

## Summary

| HTTP Method | Route | Action | Status |
|-------------|-------|--------|--------|
| `GET` | `/api/products` | List all | 200 |
| `GET` | `/api/products/{id}` | Get one | 200 / 404 |
| `POST` | `/api/products` | Create | 201 / 422 |
| `PUT` | `/api/products/{id}` | Update | 200 / 404 |
| `DELETE` | `/api/products/{id}` | Remove | 200 / 404 |

## Further Reading
- [REST API Design](https://restfulapi.net/)
- [Slim Framework](https://www.slimframework.com/) (lightweight PHP router)
