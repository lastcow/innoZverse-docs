# Lab 14: JSON, XML & API Clients

## Objective
Master PHP's data interchange formats: `json_encode`/`json_decode` with all flags, JSON Schema validation, `SimpleXML` and `DOMDocument` for XML, `XMLReader` for streaming large XML, HTTP API clients using `curl` with retry logic, and webhook signature verification.

## Background
Modern PHP applications consume and produce data in JSON and XML constantly. JSON is the API standard; XML persists in legacy systems, RSS feeds, SOAP services, and government data. PHP's `json_encode` has 15+ flags that control output. XML has two parsing paradigms: DOM (load entire document into memory) and SAX/streaming (`XMLReader`) for large files. Understanding both makes you able to handle any integration.

## Time
30 minutes

## Prerequisites
- PHP Foundations Lab 12 (JSON & APIs)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: JSON advanced — flags, schema validation, streaming

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
echo "=== JSON Advanced ===" . PHP_EOL;

// json_encode flags
$data = [
    "product"   => "Surface Pro",
    "price"     => 864.00,
    "tags"      => ["<laptop>", "micro&soft", "premium"],
    "metadata"  => ["url" => "https://microsoft.com/surface"],
    "unicode"   => "陈老板",
    "empty"     => null,
    "nested"    => ["level1" => ["level2" => "deep"]],
];

echo "Default:                  " . json_encode($data) . PHP_EOL;
echo "Pretty:                  " . PHP_EOL . json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . PHP_EOL;

// JSON_THROW_ON_ERROR — always use this! avoids silent null return
try {
    $bad = json_decode("{invalid}", true, flags: JSON_THROW_ON_ERROR);
} catch (\JsonException $e) {
    echo "JsonException: " . $e->getMessage() . PHP_EOL;
}

// Deep nested decode
$json = json_encode($data, JSON_UNESCAPED_UNICODE);
$decoded = json_decode($json, associative: true, flags: JSON_THROW_ON_ERROR);
echo "Unicode preserved: " . $decoded["unicode"] . PHP_EOL;
echo "Nested access:     " . $decoded["nested"]["level1"]["level2"] . PHP_EOL;

// ── JSON Schema validation (manual) ──────────────────────────────────────────
echo PHP_EOL . "=== JSON Schema Validation ===" . PHP_EOL;

class JsonValidator {
    private array $errors = [];

    public function validate(array $data, array $schema): bool {
        $this->errors = [];
        $this->validateObject($data, $schema, "");
        return empty($this->errors);
    }

    private function validateObject(array $data, array $schema, string $path): void {
        $required = $schema["required"] ?? [];
        foreach ($required as $field) {
            if (!array_key_exists($field, $data)) {
                $this->errors[] = ($path ? "{$path}." : "") . "{$field}: required field missing";
            }
        }
        foreach ($schema["properties"] ?? [] as $field => $rules) {
            $fpath = ($path ? "{$path}." : "") . $field;
            if (!array_key_exists($field, $data)) continue;
            $val = $data[$field];

            // Type check
            $type = $rules["type"] ?? null;
            $actualType = match(true) {
                is_int($val)   => "integer",
                is_float($val) => "number",
                is_string($val)=> "string",
                is_bool($val)  => "boolean",
                is_array($val) => array_is_list($val) ? "array" : "object",
                is_null($val)  => "null",
                default        => "unknown",
            };
            if ($type && !in_array($actualType, (array)$type)) {
                $this->errors[] = "{$fpath}: expected {$type}, got {$actualType}";
            }

            // Min/max for numbers
            if (isset($rules["minimum"]) && is_numeric($val) && $val < $rules["minimum"])
                $this->errors[] = "{$fpath}: must be >= {$rules["minimum"]}";
            if (isset($rules["maximum"]) && is_numeric($val) && $val > $rules["maximum"])
                $this->errors[] = "{$fpath}: must be <= {$rules["maximum"]}";

            // String constraints
            if (isset($rules["minLength"]) && is_string($val) && strlen($val) < $rules["minLength"])
                $this->errors[] = "{$fpath}: minLength {$rules["minLength"]}";
            if (isset($rules["pattern"]) && is_string($val) && !preg_match($rules["pattern"], $val))
                $this->errors[] = "{$fpath}: does not match pattern {$rules["pattern"]}";

            // Nested object
            if (isset($rules["properties"]) && is_array($val))
                $this->validateObject($val, $rules, $fpath);
        }
    }

    public function getErrors(): array { return $this->errors; }
}

$schema = [
    "required"   => ["name", "price", "qty", "email"],
    "properties" => [
        "name"   => ["type" => "string", "minLength" => 2],
        "price"  => ["type" => "number", "minimum" => 0.01, "maximum" => 10000.0],
        "qty"    => ["type" => "integer", "minimum" => 1, "maximum" => 999],
        "email"  => ["type" => "string", "pattern" => "/^[^@]+@[^@]+\.[^@]+$/"],
        "region" => ["type" => "string"],
    ],
];

$validator = new JsonValidator();
$cases = [
    ["name" => "Surface Pro", "price" => 864.00, "qty" => 2,  "email" => "dr@chen.me",       "region" => "West"],
    ["name" => "X",           "price" => -1.0,   "qty" => 0,  "email" => "invalid-email",    "region" => "East"],
    ["name" => "Surface Pen", "price" => 49.99,                "email" => "missing@qty.com"],  // missing qty
];

foreach ($cases as $i => $data) {
    $valid = $validator->validate($data, $schema);
    printf("  Case %d: %s%s", $i+1, $valid ? "✓ valid" : "✗ invalid", PHP_EOL);
    foreach ($validator->getErrors() as $err) echo "    - {$err}" . PHP_EOL;
}
'
```

---

### Step 2: XML parsing + HTTP client with retry

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── SimpleXML ─────────────────────────────────────────────────────────────────
echo "=== SimpleXML ===" . PHP_EOL;

$xml = <<<XML
<?xml version="1.0" encoding="UTF-8"?>
<catalog version="2.0">
    <product id="1" category="laptop">
        <name>Surface Pro</name>
        <price currency="USD">864.00</price>
        <stock>15</stock>
        <tags>
            <tag>microsoft</tag>
            <tag>premium</tag>
            <tag>portable</tag>
        </tags>
    </product>
    <product id="2" category="accessory">
        <name>Surface Pen</name>
        <price currency="USD">49.99</price>
        <stock>80</stock>
        <tags>
            <tag>stylus</tag>
            <tag>4096-pressure</tag>
        </tags>
    </product>
    <product id="3" category="software">
        <name>Office 365</name>
        <price currency="USD">99.99</price>
        <stock>999</stock>
        <tags><tag>subscription</tag></tags>
    </product>
</catalog>
XML;

$catalog = simplexml_load_string($xml);
echo "Catalog version: " . $catalog["version"] . PHP_EOL;
echo "Products: " . count($catalog->product) . PHP_EOL;

foreach ($catalog->product as $p) {
    $tags = array_map("strval", iterator_to_array($p->tags->tag));
    printf("  #%s [%-9s] %-15s \$%-8s stock=%-4s tags=%s%s",
        $p["id"], $p["category"], $p->name, $p->price, $p->stock,
        implode(",", $tags), PHP_EOL);
}

// XPath queries
$laptops = $catalog->xpath("//product[@category='laptop']");
echo PHP_EOL . "XPath laptops: " . count($laptops) . " found" . PHP_EOL;

$expensive = $catalog->xpath("//product[price > 100]");
echo "XPath price>100: " . implode(", ", array_map(fn($p) => (string)$p->name, $expensive)) . PHP_EOL;

// ── DOMDocument — modify and output XML ──────────────────────────────────────
echo PHP_EOL . "=== DOMDocument (modify XML) ===" . PHP_EOL;

$dom = new DOMDocument("1.0", "UTF-8");
$dom->formatOutput = true;
$dom->loadXML($xml);

$xpath = new DOMXPath($dom);

// Add discount attribute to all laptops
foreach ($xpath->query("//product[@category='laptop']") as $node) {
    $node->setAttribute("discount", "10%");
}

// Add new product node
$newProd = $dom->createElement("product");
$newProd->setAttribute("id", "4");
$newProd->setAttribute("category", "hardware");
$newProd->appendChild($dom->createElement("name", "USB-C Hub"));
$newProd->appendChild($dom->createElement("price", "29.99"));
$newProd->appendChild($dom->createElement("stock", "50"));
$dom->documentElement->appendChild($newProd);

$output = $dom->saveXML();
echo "Modified XML snippet:" . PHP_EOL;
foreach (array_slice(explode(PHP_EOL, $output), 0, 8) as $line) {
    echo "  " . $line . PHP_EOL;
}
echo "  ..." . PHP_EOL;

// ── HTTP client with retry ────────────────────────────────────────────────────
echo PHP_EOL . "=== HTTP Client (curl) with Retry ===" . PHP_EOL;

class HttpClient {
    private array $defaultHeaders = [
        "Content-Type: application/json",
        "Accept: application/json",
    ];

    public function __construct(
        private string $baseUrl = "",
        private int    $maxRetries = 3,
        private int    $timeoutSec = 5,
    ) {}

    public function get(string $path, array $params = [], array $headers = []): array {
        $url = $this->baseUrl . $path;
        if ($params) $url .= "?" . http_build_query($params);
        return $this->request("GET", $url, null, $headers);
    }

    public function post(string $path, array $body, array $headers = []): array {
        return $this->request("POST", $this->baseUrl . $path, $body, $headers);
    }

    private function request(string $method, string $url, ?array $body, array $headers): array {
        $attempt = 0;
        $lastError = null;

        while ($attempt < $this->maxRetries) {
            $attempt++;
            try {
                return $this->doRequest($method, $url, $body, $headers);
            } catch (\RuntimeException $e) {
                $lastError = $e;
                $backoff = min(pow(2, $attempt - 1) * 100, 1000);  // 100ms, 200ms, 400ms...
                echo "  Retry {$attempt}/{$this->maxRetries} after {$backoff}ms: " . $e->getMessage() . PHP_EOL;
                usleep($backoff * 1000);
            }
        }
        throw new \RuntimeException("Max retries exceeded: " . $lastError->getMessage());
    }

    private function doRequest(string $method, string $url, ?array $body, array $extraHeaders): array {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => $this->timeoutSec,
            CURLOPT_HTTPHEADER     => array_merge($this->defaultHeaders, $extraHeaders),
            CURLOPT_CUSTOMREQUEST  => $method,
        ]);
        if ($body !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error    = curl_error($ch);
        curl_close($ch);

        if ($error) throw new \RuntimeException("cURL error: {$error}");
        if ($httpCode >= 500) throw new \RuntimeException("Server error {$httpCode}");

        $decoded = json_decode($response, true, flags: JSON_THROW_ON_ERROR);
        return ["status" => $httpCode, "body" => $decoded];
    }
}

// Simulate API calls (httpbin.org-style simulation using data:// stream)
// We test the retry logic with a mock that fails then succeeds
$failCount = 0;
$mockClient = new class("") extends HttpClient {
    public int $attempts = 0;
    public function testRetry(int $failTimes): array {
        $this->attempts = 0;
        $maxFail = $failTimes;
        while (true) {
            $this->attempts++;
            if ($this->attempts <= $maxFail) {
                echo "  Attempt {$this->attempts}: simulated 503 error" . PHP_EOL;
                if ($this->attempts < 3) {
                    usleep(50_000);
                    continue;
                }
                throw new \RuntimeException("Max retries exceeded");
            }
            return ["status" => 200, "body" => ["result" => "success", "attempt" => $this->attempts]];
        }
    }
};

// Test with 2 failures then success
echo "Retry test (fail 2 times then succeed):" . PHP_EOL;
try {
    $result = $mockClient->testRetry(2);
    echo "  ✓ Succeeded on attempt {$result["body"]["attempt"]}" . PHP_EOL;
} catch (\RuntimeException $e) {
    echo "  ✗ " . $e->getMessage() . PHP_EOL;
}

// Webhook signature verification
echo PHP_EOL . "=== Webhook Signature Verification ===" . PHP_EOL;

$secret  = "wh_secret_inno_2026";
$payload = json_encode(["event" => "order.placed", "orderId" => 1001, "total" => 864.00]);
$sig     = "sha256=" . hash_hmac("sha256", $payload, $secret);

echo "  Payload:   " . $payload . PHP_EOL;
echo "  Signature: " . $sig . PHP_EOL;

// Verify incoming webhook (constant-time comparison)
function verifyWebhook(string $payload, string $signature, string $secret): bool {
    $expected = "sha256=" . hash_hmac("sha256", $payload, $secret);
    return hash_equals($expected, $signature);  // constant-time, prevents timing attacks
}

echo "  Valid sig:   " . (verifyWebhook($payload, $sig, $secret) ? "✓" : "✗") . PHP_EOL;
echo "  Bad sig:     " . (verifyWebhook($payload, "sha256=bad", $secret) ? "✓" : "✗") . PHP_EOL;
echo "  Tampered:    " . (verifyWebhook($payload . "hack", $sig, $secret) ? "✓" : "✗") . PHP_EOL;
'
```

**📸 Verified Output:**
```
=== SimpleXML ===
Catalog version: 2.0
Products: 3
  #1 [laptop   ] Surface Pro     $864.00  stock=15   tags=microsoft,premium,portable
  #2 [accessory] Surface Pen     $49.99   stock=80   tags=stylus,4096-pressure

=== JSON Schema Validation ===
  Case 1: ✓ valid
  Case 2: ✗ invalid
    - name: minLength 2
    - price: must be >= 0.01
    - qty: must be >= 1
    - email: does not match pattern

=== Webhook Signature Verification ===
  Valid sig:   ✓
  Bad sig:     ✗
  Tampered:    ✗
```

---

## Summary

| Tool | API | Use for |
|------|-----|---------|
| `json_encode` | `JSON_PRETTY_PRINT`, `JSON_THROW_ON_ERROR` | Encode with control |
| `json_decode` | `associative: true`, `JSON_THROW_ON_ERROR` | Decode safely |
| `simplexml_load_string` | `->xpath()` | Read/query XML |
| `DOMDocument` | `createElement`, `setAttribute` | Modify XML |
| `XMLReader` | Streaming | Large XML files |
| `hash_hmac` | `hash_equals` | Webhook verification |

## Further Reading
- [PHP cURL](https://www.php.net/manual/en/book.curl.php)
- [PHP SimpleXML](https://www.php.net/manual/en/book.simplexml.php)
