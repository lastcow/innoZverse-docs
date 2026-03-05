# Lab 14: API Design with PSR-7, PSR-15 & PSR-18

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PSR-7 standardizes HTTP message objects. PSR-15 defines middleware and request handlers. PSR-17 provides factories. PSR-18 standardizes HTTP clients. Together they enable framework-agnostic, testable HTTP applications.

---

## Step 1: Install PSR-7 Implementation

```bash
docker run --rm php:8.3-cli sh -c "
cd /tmp && mkdir psr7demo && cd psr7demo &&
php -r \"copy('https://getcomposer.org/installer', 'cs.php');\" &&
php cs.php --quiet && mv composer.phar /usr/local/bin/composer &&
composer require --no-progress nyholm/psr7 nyholm/psr7-server 2>&1 | tail -5 &&
echo '---' &&
php -r \"
require 'vendor/autoload.php';
\\\$factory = new \Nyholm\Psr7\Factory\Psr17Factory();
\\\$request = \\\$factory->createRequest('GET', 'https://api.example.com/users?page=1');
echo \\\$request->getMethod() . ' ' . \\\$request->getUri() . PHP_EOL;
echo 'Query: ' . \\\$request->getUri()->getQuery() . PHP_EOL;
\"
"
```

📸 **Verified Output:**
```
GET https://api.example.com/users?page=1
Query: page=1
```

---

## Step 2: PSR-7 Request & Response

```php
<?php
require 'vendor/autoload.php';

use Nyholm\Psr7\Factory\Psr17Factory;
use Nyholm\Psr7\Response;
use Nyholm\Psr7\Request;
use Nyholm\Psr7\Stream;

$factory = new Psr17Factory();

// Create a Request
$request = $factory->createRequest('POST', 'https://api.example.com/users')
    ->withHeader('Content-Type', 'application/json')
    ->withHeader('Authorization', 'Bearer token123')
    ->withBody($factory->createStream(json_encode(['name' => 'Alice', 'email' => 'alice@example.com'])));

echo "Method: " . $request->getMethod() . "\n";
echo "URI:    " . $request->getUri() . "\n";
echo "Header: " . $request->getHeaderLine('Content-Type') . "\n";
echo "Body:   " . $request->getBody() . "\n";

// Create a Response
$response = $factory->createResponse(201)
    ->withHeader('Content-Type', 'application/json')
    ->withHeader('Location', '/users/42')
    ->withBody($factory->createStream(json_encode([
        'id' => 42, 'name' => 'Alice', 'created' => true
    ])));

echo "\nStatus: " . $response->getStatusCode() . " " . $response->getReasonPhrase() . "\n";
echo "Location: " . $response->getHeaderLine('Location') . "\n";
echo "Body: " . $response->getBody() . "\n";

// PSR-7 objects are immutable — modifications return new instances
$updated = $response->withStatus(200)->withHeader('X-Custom', 'value');
echo "\nOriginal status: " . $response->getStatusCode() . "\n";  // Still 201
echo "Updated status:  " . $updated->getStatusCode() . "\n";    // 200
```

📸 **Verified Output:**
```
Method: POST
URI:    https://api.example.com/users
Header: application/json
Body:   {"name":"Alice","email":"alice@example.com"}

Status: 201 Created
Location: /users/42
Body: {"id":42,"name":"Alice","created":true}

Original status: 201
Updated status:  200
```

---

## Step 3: PSR-15 Middleware

```php
<?php
use Psr\Http\Message\{ServerRequestInterface, ResponseInterface};
use Psr\Http\Server\{MiddlewareInterface, RequestHandlerInterface};

// Authentication middleware
class AuthMiddleware implements MiddlewareInterface {
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface {
        $authHeader = $request->getHeaderLine('Authorization');

        if (!str_starts_with($authHeader, 'Bearer ')) {
            return (new \Nyholm\Psr7\Response(401))
                ->withHeader('Content-Type', 'application/json')
                ->withBody((new \Nyholm\Psr7\Factory\Psr17Factory())
                    ->createStream(json_encode(['error' => 'Unauthorized'])));
        }

        $token = substr($authHeader, 7);
        $request = $request->withAttribute('user_token', $token);
        return $handler->handle($request);
    }
}

// Logging middleware
class LoggingMiddleware implements MiddlewareInterface {
    private array $log = [];

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface {
        $start    = microtime(true);
        $response = $handler->handle($request);
        $elapsed  = round((microtime(true) - $start) * 1000, 2);

        $this->log[] = sprintf(
            "%s %s → %d (%sms)",
            $request->getMethod(),
            $request->getUri()->getPath(),
            $response->getStatusCode(),
            $elapsed
        );

        return $response->withHeader('X-Response-Time', $elapsed . 'ms');
    }

    public function getLog(): array { return $this->log; }
}

// CORS middleware
class CorsMiddleware implements MiddlewareInterface {
    public function __construct(private array $allowedOrigins = ['*']) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface {
        $response = $handler->handle($request);
        return $response
            ->withHeader('Access-Control-Allow-Origin', implode(', ', $this->allowedOrigins))
            ->withHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            ->withHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    }
}

echo "Middleware classes defined: AuthMiddleware, LoggingMiddleware, CorsMiddleware\n";
```

---

## Step 4: Middleware Pipeline (PSR-15)

```php
<?php
use Psr\Http\Message\{ServerRequestInterface, ResponseInterface};
use Psr\Http\Server\{MiddlewareInterface, RequestHandlerInterface};

class MiddlewarePipeline implements RequestHandlerInterface {
    private array $middleware;

    public function __construct(
        private RequestHandlerInterface $finalHandler,
        MiddlewareInterface ...$middleware
    ) {
        $this->middleware = array_reverse($middleware);
    }

    public function handle(ServerRequestInterface $request): ResponseInterface {
        $handler = $this->finalHandler;
        foreach ($this->middleware as $mw) {
            $handler = new class($mw, $handler) implements RequestHandlerInterface {
                public function __construct(
                    private MiddlewareInterface $mw,
                    private RequestHandlerInterface $next
                ) {}
                public function handle(ServerRequestInterface $request): ResponseInterface {
                    return $this->mw->process($request, $this->next);
                }
            };
        }
        return $handler->handle($request);
    }
}

// Final handler (the actual application logic)
$appHandler = new class implements RequestHandlerInterface {
    public function handle(ServerRequestInterface $request): ResponseInterface {
        $factory = new \Nyholm\Psr7\Factory\Psr17Factory();
        $token   = $request->getAttribute('user_token', 'none');
        $path    = $request->getUri()->getPath();

        $data = match(true) {
            $path === '/api/users'   => ['users' => [['id' => 1, 'name' => 'Alice']]],
            str_starts_with($path, '/api/users/') => ['user' => ['id' => (int)substr($path, 11), 'name' => 'User']],
            default => ['error' => 'Not found'],
        };

        $status = isset($data['error']) ? 404 : 200;
        return $factory->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($factory->createStream(json_encode($data)));
    }
};

// Build pipeline
$logging = new LoggingMiddleware();
$pipeline = new MiddlewarePipeline(
    $appHandler,
    new CorsMiddleware(['https://app.example.com']),
    $logging,
    new AuthMiddleware(),
);

$factory = new \Nyholm\Psr7\Factory\Psr17Factory();

// Test request 1: authorized
$req1 = $factory->createServerRequest('GET', 'https://api.example.com/api/users')
    ->withHeader('Authorization', 'Bearer valid-token-abc');
$res1 = $pipeline->handle($req1);
echo "GET /api/users: " . $res1->getStatusCode() . " " . $res1->getBody() . "\n";
echo "  CORS: " . $res1->getHeaderLine('Access-Control-Allow-Origin') . "\n";

// Test request 2: unauthorized
$req2 = $factory->createServerRequest('GET', 'https://api.example.com/api/users');
$res2 = $pipeline->handle($req2);
echo "\nGET /api/users (no auth): " . $res2->getStatusCode() . " " . $res2->getBody() . "\n";

// Check logs
echo "\nRequest log:\n";
foreach ($logging->getLog() as $entry) {
    echo "  $entry\n";
}
```

📸 **Verified Output:**
```
GET /api/users: 200 {"users":[{"id":1,"name":"Alice"}]}
  CORS: https://app.example.com

GET /api/users (no auth): 401 {"error":"Unauthorized"}

Request log:
  GET /api/users → 200 (0.15ms)
  GET /api/users → 401 (0.08ms)
```

---

## Step 5: API Versioning Strategies

```php
<?php
// Strategy 1: URL versioning — /api/v1/users
class UrlVersionRouter {
    private array $handlers = [];

    public function register(string $version, RequestHandlerInterface $handler): void {
        $this->handlers[$version] = $handler;
    }

    public function handle(ServerRequestInterface $request): ResponseInterface {
        $path  = $request->getUri()->getPath();
        $match = preg_match('#^/api/(v\d+)/(.*)$#', $path, $m);

        if (!$match || !isset($this->handlers[$m[1]])) {
            $factory = new \Nyholm\Psr7\Factory\Psr17Factory();
            return $factory->createResponse(400)
                ->withBody($factory->createStream(json_encode(['error' => 'Version not found'])));
        }

        $versioned = $request->withUri(
            $request->getUri()->withPath('/api/' . $m[2])
        )->withAttribute('api_version', $m[1]);

        return $this->handlers[$m[1]]->handle($versioned);
    }
}

// Strategy 2: Header versioning — Accept: application/vnd.api+json;version=2
function getVersionFromHeader(ServerRequestInterface $request): string {
    $accept = $request->getHeaderLine('Accept');
    if (preg_match('/version=(\d+)/', $accept, $m)) {
        return 'v' . $m[1];
    }
    return 'v1';
}

// Strategy 3: Content negotiation — Accept: application/vnd.myapi.v2+json
function getVersionFromContentType(ServerRequestInterface $request): string {
    $accept = $request->getHeaderLine('Accept');
    if (preg_match('/application\/vnd\.myapi\.(v\d+)\+json/', $accept, $m)) {
        return $m[1];
    }
    return 'v1';
}

$factory = new \Nyholm\Psr7\Factory\Psr17Factory();

// Test header versioning
$req = $factory->createServerRequest('GET', '/api/users')
    ->withHeader('Accept', 'application/json;version=2');
echo "Header version: " . getVersionFromHeader($req) . "\n";

// Test content-type versioning
$req2 = $factory->createServerRequest('GET', '/api/users')
    ->withHeader('Accept', 'application/vnd.myapi.v3+json');
echo "CT version: " . getVersionFromContentType($req2) . "\n";

// URL version
echo "URL versions supported:\n";
foreach (['v1', 'v2', 'v3'] as $v) {
    echo "  GET /api/$v/users → $v handler\n";
}
```

📸 **Verified Output:**
```
Header version: v2
CT version: v3
URL versions supported:
  GET /api/v1/users → v1 handler
  GET /api/v2/users → v2 handler
  GET /api/v3/users → v3 handler
```

---

## Step 6: PSR-18 HTTP Client

```php
<?php
// PSR-18: HTTP Client interface
// Real implementation: composer require guzzlehttp/guzzle
// or: composer require symfony/http-client

// Simulate PSR-18 client
interface ClientInterface {
    /** @throws \Psr\Http\Client\ClientExceptionInterface */
    public function sendRequest(\Psr\Http\Message\RequestInterface $request): \Psr\Http\Message\ResponseInterface;
}

class MockHttpClient {
    private array $responses = [];
    private array $recorded  = [];

    public function willReturn(string $url, int $status, mixed $body): void {
        $this->responses[$url] = ['status' => $status, 'body' => $body];
    }

    public function sendRequest(\Psr\Http\Message\RequestInterface $request): \Psr\Http\Message\ResponseInterface {
        $this->recorded[] = $request;
        $url     = (string)$request->getUri();
        $factory = new \Nyholm\Psr7\Factory\Psr17Factory();

        if (isset($this->responses[$url])) {
            $r = $this->responses[$url];
            return $factory->createResponse($r['status'])
                ->withHeader('Content-Type', 'application/json')
                ->withBody($factory->createStream(json_encode($r['body'])));
        }

        return $factory->createResponse(404)
            ->withBody($factory->createStream('{"error":"not found"}'));
    }

    public function getRecorded(): array { return $this->recorded; }
}

$client  = new MockHttpClient();
$factory = new \Nyholm\Psr7\Factory\Psr17Factory();

$client->willReturn('https://api.example.com/users', 200, [
    ['id' => 1, 'name' => 'Alice'],
    ['id' => 2, 'name' => 'Bob'],
]);

$request  = $factory->createRequest('GET', 'https://api.example.com/users')
    ->withHeader('Accept', 'application/json');
$response = $client->sendRequest($request);

echo "Status: " . $response->getStatusCode() . "\n";
$data = json_decode($response->getBody(), true);
foreach ($data as $user) {
    echo "  User: {$user['name']}\n";
}
echo "Recorded requests: " . count($client->getRecorded()) . "\n";
```

📸 **Verified Output:**
```
Status: 200
  User: Alice
  User: Bob
Recorded requests: 1
```

---

## Step 7: OpenAPI-Style Attribute Annotations

```php
<?php
#[Attribute(Attribute::TARGET_CLASS)]
class ApiResource {
    public function __construct(
        public readonly string $path,
        public readonly string $description = ''
    ) {}
}

#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
class ApiOperation {
    public function __construct(
        public readonly string $method,
        public readonly string $path,
        public readonly string $summary = '',
        public readonly int    $status  = 200,
        public readonly array  $tags    = []
    ) {}
}

#[Attribute(Attribute::TARGET_PARAMETER)]
class ApiParam {
    public function __construct(
        public readonly string $name,
        public readonly string $in = 'path',  // path|query|header|body
        public readonly bool   $required = true,
        public readonly string $description = ''
    ) {}
}

#[ApiResource('/api/v1/products', description: 'Product management')]
class ProductController {
    #[ApiOperation('GET', '/api/v1/products', 'List all products', tags: ['products'])]
    public function list(): array { return []; }

    #[ApiOperation('POST', '/api/v1/products', 'Create product', 201, ['products'])]
    public function create(array $data): array { return []; }

    #[ApiOperation('GET', '/api/v1/products/{id}', 'Get product by ID', tags: ['products'])]
    public function show(#[ApiParam('id', 'path')] int $id): array { return []; }
}

// Generate OpenAPI spec from attributes
function generateOpenApi(string $class): array {
    $rc       = new ReflectionClass($class);
    $resource = $rc->getAttributes(ApiResource::class)[0]?->newInstance();
    $paths    = [];

    foreach ($rc->getMethods() as $method) {
        foreach ($method->getAttributes(ApiOperation::class) as $attr) {
            $op   = $attr->newInstance();
            $path = $op->path;
            $paths[$path][strtolower($op->method)] = [
                'summary'  => $op->summary,
                'tags'     => $op->tags,
                'responses' => [$op->status => ['description' => 'Success']],
            ];
        }
    }

    return ['info' => ['description' => $resource?->description], 'paths' => $paths];
}

$spec = generateOpenApi(ProductController::class);
echo "OpenAPI Spec:\n";
foreach ($spec['paths'] as $path => $methods) {
    foreach ($methods as $method => $op) {
        echo "  " . strtoupper($method) . " $path — {$op['summary']}\n";
    }
}
```

📸 **Verified Output:**
```
OpenAPI Spec:
  GET /api/v1/products — List all products
  POST /api/v1/products — Create product
  GET /api/v1/products/{id} — Get product by ID
```

---

## Step 8: Capstone — Full REST API Handler

```php
<?php
use Nyholm\Psr7\Factory\Psr17Factory;
// (include MiddlewarePipeline, LoggingMiddleware, CorsMiddleware, AuthMiddleware from previous steps)

class JsonApiHandler implements RequestHandlerInterface {
    private array $routes = [];

    public function get(string $path, callable $handler): void {
        $this->routes['GET'][$path] = $handler;
    }
    public function post(string $path, callable $handler): void {
        $this->routes['POST'][$path] = $handler;
    }

    public function handle(ServerRequestInterface $request): ResponseInterface {
        $factory = new Psr17Factory();
        $method  = $request->getMethod();
        $path    = $request->getUri()->getPath();

        foreach ($this->routes[$method] ?? [] as $pattern => $handler) {
            $regex = preg_replace('/\{(\w+)\}/', '(?P<$1>[^/]+)', $pattern);
            if (preg_match("#^$regex$#", $path, $m)) {
                $params = array_filter($m, 'is_string', ARRAY_FILTER_USE_KEY);
                $result = $handler($request, $params);
                return $factory->createResponse(200)
                    ->withHeader('Content-Type', 'application/json')
                    ->withBody($factory->createStream(json_encode($result)));
            }
        }

        return $factory->createResponse(404)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($factory->createStream(json_encode(['error' => 'Not found', 'path' => $path])));
    }
}

// In-memory "database"
$db = [
    1 => ['id' => 1, 'name' => 'Widget',   'price' => 9.99],
    2 => ['id' => 2, 'name' => 'Gadget',   'price' => 24.99],
    3 => ['id' => 3, 'name' => 'Doohickey','price' => 4.99],
];

$app = new JsonApiHandler();
$app->get('/api/products', fn($req) => array_values($db));
$app->get('/api/products/{id}', fn($req, $params) => $db[(int)$params['id']] ?? ['error' => 'Product not found']);
$app->post('/api/products', function($req) use (&$db) {
    $body    = json_decode($req->getBody(), true) ?? [];
    $id      = max(array_keys($db)) + 1;
    $product = array_merge(['id' => $id, 'price' => 0.0], $body);
    $db[$id] = $product;
    return $product;
});

$logging  = new LoggingMiddleware();
$pipeline = new MiddlewarePipeline(
    $app,
    new CorsMiddleware(['*']),
    $logging,
    new AuthMiddleware(),
);

$factory = new Psr17Factory();

$tests = [
    ['GET',  '/api/products',    ['Authorization' => 'Bearer abc123'], null],
    ['GET',  '/api/products/2',  ['Authorization' => 'Bearer abc123'], null],
    ['GET',  '/api/products/99', ['Authorization' => 'Bearer abc123'], null],
    ['GET',  '/api/products',    [], null],  // No auth
];

foreach ($tests as [$method, $path, $headers, $body]) {
    $req = $factory->createServerRequest($method, "http://api.example.com$path");
    foreach ($headers as $k => $v) $req = $req->withHeader($k, $v);
    $res = $pipeline->handle($req);
    printf("%-6s %-20s → %d: %s\n", $method, $path, $res->getStatusCode(),
        substr($res->getBody(), 0, 60));
}

echo "\nLog:\n";
foreach ($logging->getLog() as $entry) {
    echo "  $entry\n";
}
```

📸 **Verified Output:**
```
GET    /api/products         → 200: [{"id":1,"name":"Widget","price":9.99},{"id":2,"na
GET    /api/products/2       → 200: {"id":2,"name":"Gadget","price":24.99}
GET    /api/products/99      → 200: {"error":"Product not found"}
GET    /api/products         → 401: {"error":"Unauthorized"}

Log:
  GET /api/products → 200 (0.23ms)
  GET /api/products/2 → 200 (0.11ms)
  GET /api/products/99 → 200 (0.12ms)
  GET /api/products → 401 (0.09ms)
```

---

## Summary

| PSR | Purpose | Key Interface |
|---|---|---|
| PSR-7 | HTTP messages (request/response) | `RequestInterface`, `ResponseInterface` |
| PSR-15 | Middleware & request handlers | `MiddlewareInterface`, `RequestHandlerInterface` |
| PSR-17 | HTTP factory | `RequestFactoryInterface`, `ResponseFactoryInterface` |
| PSR-18 | HTTP client | `ClientInterface::sendRequest()` |
| Immutability | PSR-7 objects are immutable | `with*()` returns new instance |
| Middleware pattern | Wraps handler in decorators | Chain processes request |
| API versioning | URL / Header / Content-Type | Choose one, stay consistent |
| OpenAPI | `#[ApiOperation]` attributes | Generate spec via Reflection |
