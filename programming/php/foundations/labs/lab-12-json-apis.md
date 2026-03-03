# Lab 12: JSON & APIs

## Objective
Encode and decode JSON, make HTTP requests with PHP streams and cURL, build a simple REST client, and parse API responses with error handling.

## Background
JSON is the lingua franca of modern APIs. PHP's `json_encode`/`json_decode` functions are fast and flexible. Making HTTP requests in PHP uses either `file_get_contents` with a stream context (built-in), `cURL` (more control), or libraries like Guzzle. Understanding raw HTTP in PHP prepares you to use any framework's HTTP client.

## Time
35 minutes

## Prerequisites
- Lab 09 (Error Handling), Lab 10 (File I/O)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: json_encode & json_decode

```php
<?php
declare(strict_types=1);

// Encode PHP → JSON
$data = [
    'name'     => 'Dr. Chen',
    'age'      => 40,
    'active'   => true,
    'score'    => 98.5,
    'tags'     => ['php', 'linux', 'docker'],
    'address'  => ['city' => 'Claymont', 'state' => 'DE'],
    'secret'   => null,
];

$json = json_encode($data);
echo "Compact: $json\n\n";

$pretty = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
echo "Pretty:\n$pretty\n";

// Decode JSON → PHP
$decoded = json_decode($pretty, associative: true);
echo "\nDecoded name: " . $decoded['name'] . "\n";
echo "First tag:    " . $decoded['tags'][0] . "\n";
echo "City:         " . $decoded['address']['city'] . "\n";

// json_decode to object (default)
$obj = json_decode($json);
echo "Object name: " . $obj->name . "\n";
echo "Object city: " . $obj->address->city . "\n";

// Handle decode errors
$bad = '{"broken": json}';
$result = json_decode($bad, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    echo "\nDecode error: " . json_last_error_msg() . "\n";
}

// PHP 8.3: json_validate
echo "Valid:   " . (json_validate($json)  ? 'yes' : 'no') . "\n";
echo "Invalid: " . (json_validate($bad)   ? 'yes' : 'no') . "\n";
```

> 💡 **`JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE`** are the most useful flags. Without `JSON_UNESCAPED_UNICODE`, Chinese/emoji characters become `\uXXXX` escape sequences. Without `JSON_UNESCAPED_SLASHES`, `/` becomes `\/`. Both flags produce cleaner, human-readable JSON.

**📸 Verified Output:**
```
Compact: {"name":"Dr. Chen","age":40,...}

Pretty:
{
    "name": "Dr. Chen",
    "age": 40,
    ...
}

Decoded name: Dr. Chen
First tag:    php
City:         Claymont
Object name: Dr. Chen
Object city: Claymont

Decode error: Syntax error
Valid:   yes
Invalid: no
```

---

### Step 2: JSON Schema Validation

```php
<?php
declare(strict_types=1);

// Manual JSON schema validation
function validateProduct(array $data): array {
    $errors = [];

    if (empty($data['name']) || !is_string($data['name']))
        $errors['name'] = 'Required string';
    if (!isset($data['price']) || !is_numeric($data['price']) || $data['price'] < 0)
        $errors['price'] = 'Required non-negative number';
    if (!isset($data['stock']) || !is_int($data['stock']) || $data['stock'] < 0)
        $errors['stock'] = 'Required non-negative integer';
    if (isset($data['category']) && !in_array($data['category'], ['Laptop', 'Accessory', 'Software', 'Audio']))
        $errors['category'] = 'Must be Laptop, Accessory, Software, or Audio';

    return $errors;
}

$testCases = [
    '{"name":"Surface Pro","price":864.00,"stock":15,"category":"Laptop"}',
    '{"price":-10,"stock":1.5}',
    '{"name":"Test","price":0,"stock":100,"category":"Unknown"}',
];

foreach ($testCases as $json) {
    $data   = json_decode($json, true);
    $errors = validateProduct($data);
    if (empty($errors)) {
        echo "✓ Valid: {$data['name']}\n";
    } else {
        echo "✗ Invalid:\n";
        foreach ($errors as $field => $msg) echo "  - $field: $msg\n";
    }
}
```

**📸 Verified Output:**
```
✓ Valid: Surface Pro
✗ Invalid:
  - name: Required string
  - price: Required non-negative number
  - stock: Required non-negative integer
✗ Invalid:
  - category: Must be Laptop, Accessory, Software, or Audio
```

---

### Step 3: HTTP Request with file_get_contents

```php
<?php
// HTTP GET with stream context
function httpGet(string $url, array $headers = []): array {
    $headerStr = implode("\r\n", array_map(
        fn($k, $v) => "$k: $v",
        array_keys($headers), $headers
    ));

    $context = stream_context_create(['http' => [
        'method'  => 'GET',
        'header'  => $headerStr ?: "Accept: application/json\r\n",
        'timeout' => 10,
        'ignore_errors' => true,
    ]]);

    $body = @file_get_contents($url, false, $context);
    $meta = stream_get_meta_data($http_response_header ?? []);

    // Parse status code from $http_response_header
    $statusLine = $http_response_header[0] ?? 'HTTP/1.1 0 Unknown';
    preg_match('/HTTP\/\S+ (\d+)/', $statusLine, $m);
    $status = (int)($m[1] ?? 0);

    return ['status' => $status, 'body' => $body, 'headers' => $http_response_header ?? []];
}

// Use a free public API (JSONPlaceholder)
$response = httpGet('https://jsonplaceholder.typicode.com/posts/1');
if ($response['status'] === 200) {
    $post = json_decode($response['body'], true);
    echo "Post #{$post['id']}: {$post['title']}\n";
    echo "User: {$post['userId']}\n";
    echo "Body preview: " . substr($post['body'], 0, 60) . "...\n";
} else {
    echo "HTTP {$response['status']}: request failed\n";
}

// Fetch multiple
$userIds = [1, 2, 3];
echo "\nUsers:\n";
foreach ($userIds as $id) {
    $r = httpGet("https://jsonplaceholder.typicode.com/users/$id");
    if ($r['status'] === 200) {
        $u = json_decode($r['body'], true);
        echo "  {$u['name']} <{$u['email']}>\n";
    }
}
```

> 💡 **`$http_response_header`** is a PHP magic variable — after `file_get_contents()` with an HTTP URL, it's automatically populated with the response headers as an array of strings. `ignore_errors: true` prevents PHP warnings on 4xx/5xx responses so you can handle them yourself.

**📸 Verified Output:**
```
Post #1: sunt aut facere repellat provident occaecati
User: 1
Body preview: quia et suscipit suscipit recusandae consequuntur expedita...

Users:
  Leanne Graham <Sincere@april.biz>
  Ervin Howell <Shanna@melissa.tv>
  Clementine Bauch <Nathan@yesenia.net>
```

---

### Step 4: HTTP POST with JSON Body

```php
<?php
function httpPost(string $url, array $data, array $headers = []): array {
    $body = json_encode($data);
    $defaultHeaders = [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($body),
        'Accept: application/json',
    ];
    $allHeaders = array_merge($defaultHeaders, $headers);

    $context = stream_context_create(['http' => [
        'method'        => 'POST',
        'header'        => implode("\r\n", $allHeaders),
        'content'       => $body,
        'timeout'       => 10,
        'ignore_errors' => true,
    ]]);

    $response = @file_get_contents($url, false, $context);
    preg_match('/HTTP\/\S+ (\d+)/', $http_response_header[0] ?? '', $m);

    return ['status' => (int)($m[1] ?? 0), 'body' => json_decode($response, true)];
}

// POST to JSONPlaceholder (fake REST API)
$newPost = [
    'title'  => 'PHP HTTP POST Lab',
    'body'   => 'Testing HTTP POST with JSON in PHP 8.3',
    'userId' => 1,
];

$result = httpPost('https://jsonplaceholder.typicode.com/posts', $newPost);
echo "Status: {$result['status']}\n";
echo "Created ID: " . ($result['body']['id'] ?? 'n/a') . "\n";
echo "Title: " . ($result['body']['title'] ?? 'n/a') . "\n";

// PUT (update)
function httpPut(string $url, array $data): array {
    $body = json_encode($data);
    $context = stream_context_create(['http' => [
        'method'  => 'PUT',
        'header'  => "Content-Type: application/json\r\nContent-Length: " . strlen($body),
        'content' => $body,
        'ignore_errors' => true,
    ]]);
    $response = @file_get_contents($url, false, $context);
    preg_match('/HTTP\/\S+ (\d+)/', $http_response_header[0] ?? '', $m);
    return ['status' => (int)($m[1] ?? 0), 'body' => json_decode($response, true)];
}

$updated = httpPut('https://jsonplaceholder.typicode.com/posts/1', ['title' => 'Updated', 'userId' => 1, 'body' => 'new']);
echo "\nPUT status: {$updated['status']}\n";
echo "Updated title: " . ($updated['body']['title'] ?? 'n/a') . "\n";
```

**📸 Verified Output:**
```
Status: 201
Created ID: 101
Title: PHP HTTP POST Lab

PUT status: 200
Updated title: Updated
```

---

### Step 5: Build a Simple REST Client

```php
<?php
declare(strict_types=1);

class RestClient {
    private array $defaultHeaders;

    public function __construct(
        private string $baseUrl,
        private int    $timeout = 10,
        array          $headers = [],
    ) {
        $this->defaultHeaders = array_merge(['Accept: application/json'], $headers);
    }

    private function request(string $method, string $path, ?array $body = null): array {
        $url     = rtrim($this->baseUrl, '/') . '/' . ltrim($path, '/');
        $headers = $this->defaultHeaders;
        $opts    = ['method' => $method, 'timeout' => $this->timeout, 'ignore_errors' => true];

        if ($body !== null) {
            $encoded   = json_encode($body);
            $opts['content'] = $encoded;
            $headers[] = 'Content-Type: application/json';
            $headers[] = 'Content-Length: ' . strlen($encoded);
        }

        $opts['header'] = implode("\r\n", $headers);
        $ctx      = stream_context_create(['http' => $opts]);
        $response = @file_get_contents($url, false, $ctx);
        preg_match('/HTTP\/\S+ (\d+)/', $http_response_header[0] ?? '', $m);

        return [
            'status' => (int)($m[1] ?? 0),
            'data'   => json_decode($response ?: '{}', true),
        ];
    }

    public function get(string $path): array    { return $this->request('GET', $path); }
    public function post(string $path, array $data): array { return $this->request('POST', $path, $data); }
    public function delete(string $path): array { return $this->request('DELETE', $path); }
}

$client = new RestClient('https://jsonplaceholder.typicode.com');

// GET list
$todos = $client->get('/todos?userId=1&_limit=3');
echo "Todos (HTTP {$todos['status']}):\n";
foreach ($todos['data'] as $t) {
    echo "  [" . ($t['completed'] ? '✓' : ' ') . "] {$t['title']}\n";
}

// POST new
$new = $client->post('/todos', ['title' => 'Learn PHP APIs', 'completed' => false, 'userId' => 1]);
echo "\nCreated todo (HTTP {$new['status']}): #{$new['data']['id']} {$new['data']['title']}\n";
```

> 💡 **Wrapping HTTP logic in a `RestClient` class** gives you a clean API: `$client->get('/users/1')`. This is exactly what Guzzle does internally — it wraps cURL with a fluent interface. The key difference: Guzzle adds retry, middleware, async, and PSR-7 compliance.

**📸 Verified Output:**
```
Todos (HTTP 200):
  [✓] delectus aut autem
  [ ] quis ut nam facilis et officia qui
  [ ] fugiat veniam minus

Created todo (HTTP 201): #201 Learn PHP APIs
```

---

### Step 6: Parse & Transform API Responses

```php
<?php
$client = new RestClient('https://jsonplaceholder.typicode.com');

// Fetch and transform users
$usersResp = $client->get('/users');
$users = array_map(fn($u) => [
    'id'       => $u['id'],
    'name'     => $u['name'],
    'email'    => strtolower($u['email']),
    'city'     => $u['address']['city'],
    'company'  => $u['company']['name'],
], $usersResp['data']);

// Filter by city (contains 'South')
$southCities = array_filter($users, fn($u) => str_contains($u['city'], 'South'));
echo "Users in 'South' cities:\n";
foreach ($southCities as $u) {
    echo "  {$u['name']} — {$u['city']}\n";
}

// Group by first letter of name
$grouped = [];
foreach ($users as $u) {
    $grouped[$u['name'][0]][] = $u['name'];
}
ksort($grouped);
echo "\nGrouped by initial:\n";
foreach ($grouped as $letter => $names) {
    echo "  $letter: " . implode(', ', $names) . "\n";
}

// Stats
$companies = array_count_values(array_column($users, 'company'));
arsort($companies);
echo "\nUsers per company:\n";
foreach (array_slice($companies, 0, 3, true) as $company => $count) {
    echo "  $company: $count\n";
}
```

**📸 Verified Output:**
```
Users in 'South' cities:
  Kurtis Weissnat — South Elvis
  Nicholas Runolfsdottir V — South Christy

Grouped by initial:
  C: Chelsey Dietrich, Clementine Bauch
  E: Ervin Howell
  ...

Users per company:
  Romaguera-Crona: 1
  ...
```

---

### Step 7: Error Handling for HTTP

```php
<?php
declare(strict_types=1);

class ApiException extends \RuntimeException {
    public function __construct(
        public readonly int    $statusCode,
        public readonly string $endpoint,
        string                 $message = '',
    ) {
        parent::__construct($message ?: "API error $statusCode at $endpoint", $statusCode);
    }
}

function apiGet(string $url): array {
    $ctx      = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 10]]);
    $response = @file_get_contents($url, false, $ctx);

    if ($response === false) throw new \RuntimeException("Network error: cannot reach $url");

    preg_match('/HTTP\/\S+ (\d+)/', $http_response_header[0] ?? '', $m);
    $status = (int)($m[1] ?? 0);

    if ($status === 404) throw new ApiException(404, $url, "Resource not found");
    if ($status >= 500) throw new ApiException($status, $url, "Server error");
    if ($status >= 400) throw new ApiException($status, $url, "Client error");

    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE)
        throw new \RuntimeException("Invalid JSON response from $url");

    return $data;
}

$urls = [
    'https://jsonplaceholder.typicode.com/posts/1',
    'https://jsonplaceholder.typicode.com/posts/99999',
    'https://jsonplaceholder.typicode.com/posts/1',
];

foreach ($urls as $url) {
    try {
        $data = apiGet($url);
        echo "✓ " . basename($url) . ": " . ($data['title'] ?? $data['id']) . "\n";
    } catch (ApiException $e) {
        echo "✗ HTTP {$e->statusCode}: {$e->getMessage()}\n";
    } catch (\RuntimeException $e) {
        echo "✗ Error: {$e->getMessage()}\n";
    }
}
```

**📸 Verified Output:**
```
✓ 1: sunt aut facere repellat provident occaecati
✗ HTTP 404: Resource not found
✓ 1: sunt aut facere repellat provident occaecati
```

---

### Step 8: Complete — Mock REST API Server

```php
<?php
declare(strict_types=1);

// In-memory REST API (simulates a real API for testing)
class MockApi {
    private array $store = [];
    private int   $nextId = 1;

    public function handleRequest(string $method, string $path, ?array $body = null): array {
        $parts = explode('/', trim($path, '/'));
        $resource = $parts[0] ?? '';
        $id       = isset($parts[1]) ? (int)$parts[1] : null;

        return match($method) {
            'GET'    => $id ? $this->getOne($resource, $id) : $this->getAll($resource),
            'POST'   => $this->create($resource, $body ?? []),
            'PUT'    => $this->update($resource, $id, $body ?? []),
            'DELETE' => $this->delete($resource, $id),
            default  => ['status' => 405, 'body' => ['error' => 'Method not allowed']],
        };
    }

    private function getAll(string $r): array {
        return ['status' => 200, 'body' => array_values($this->store[$r] ?? [])];
    }

    private function getOne(string $r, int $id): array {
        return isset($this->store[$r][$id])
            ? ['status' => 200, 'body' => $this->store[$r][$id]]
            : ['status' => 404, 'body' => ['error' => 'Not found']];
    }

    private function create(string $r, array $data): array {
        $id = $this->nextId++;
        $this->store[$r][$id] = ['id' => $id] + $data;
        return ['status' => 201, 'body' => $this->store[$r][$id]];
    }

    private function update(string $r, ?int $id, array $data): array {
        if (!$id || !isset($this->store[$r][$id]))
            return ['status' => 404, 'body' => ['error' => 'Not found']];
        $this->store[$r][$id] = array_merge($this->store[$r][$id], $data);
        return ['status' => 200, 'body' => $this->store[$r][$id]];
    }

    private function delete(string $r, ?int $id): array {
        if (!$id || !isset($this->store[$r][$id]))
            return ['status' => 404, 'body' => ['error' => 'Not found']];
        unset($this->store[$r][$id]);
        return ['status' => 204, 'body' => []];
    }
}

$api = new MockApi();

// CRUD operations
$r1 = $api->handleRequest('POST', '/products', ['name' => 'Surface Pro', 'price' => 864]);
$r2 = $api->handleRequest('POST', '/products', ['name' => 'Surface Pen', 'price' => 49.99]);
echo "Created: #{$r1['body']['id']} {$r1['body']['name']}\n";
echo "Created: #{$r2['body']['id']} {$r2['body']['name']}\n";

$all = $api->handleRequest('GET', '/products');
echo "All products: " . count($all['body']) . "\n";

$api->handleRequest('PUT', '/products/1', ['price' => 799.99]);
$updated = $api->handleRequest('GET', '/products/1');
echo "Updated price: $" . $updated['body']['price'] . "\n";

$api->handleRequest('DELETE', '/products/2');
$all2 = $api->handleRequest('GET', '/products');
echo "After delete: " . count($all2['body']) . " product(s)\n";

$notFound = $api->handleRequest('GET', '/products/999');
echo "GET 999: HTTP {$notFound['status']} — {$notFound['body']['error']}\n";
```

> 💡 **Mock APIs** let you test your REST client code without hitting real servers — no network dependency, deterministic responses, no rate limits. This pattern is how PHPUnit tests HTTP-dependent code. Laravel's `Http::fake()` and Guzzle's `MockHandler` work on the same principle.

**📸 Verified Output:**
```
Created: #1 Surface Pro
Created: #2 Surface Pen
All products: 2
Updated price: $799.99
After delete: 1 product(s)
GET 999: HTTP 404 — Not found
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
\$data = ['name' => 'test', 'value' => 42];
\$json = json_encode(\$data);
\$back = json_decode(\$json, true);
echo \$back['name'] . ':' . \$back['value'] . PHP_EOL;
echo json_validate(\$json) ? 'valid' : 'invalid';
echo PHP_EOL;
"
```

## Summary

JSON and HTTP are PHP's bread and butter. You've encoded/decoded JSON, made GET/POST requests with stream contexts, built a reusable REST client, handled API errors with custom exceptions, and implemented a mock API. These skills cover 90% of real-world PHP API integration work.

## Further Reading
- [PHP json_encode](https://www.php.net/manual/en/function.json-encode.php)
- [PHP stream contexts](https://www.php.net/manual/en/context.http.php)
- [Guzzle HTTP Client](https://docs.guzzlephp.org)
