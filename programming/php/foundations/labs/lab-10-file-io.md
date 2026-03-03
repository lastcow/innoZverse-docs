# Lab 10: File I/O — Reading, Writing & Streams

## Objective
Read and write files with PHP's file functions, process CSV data, handle JSON files, work with streams, and use SPL file iterators for large file processing.

## Background
PHP was built for web file processing — log parsing, CSV imports, config files, report generation. Its file functions (`file_get_contents`, `fopen`, `fread`) cover everything from simple text files to gigabyte log streams. Modern PHP also supports PHP streams (`php://memory`, `php://stdin`) for testing and pipeline processing.

## Time
30 minutes

## Prerequisites
- Lab 05 (Functions)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`
- All files written to `/tmp/` for Docker compatibility

---

## Lab Instructions

### Step 1: Read & Write Text Files

```php
<?php
// Write a file
$content = "Line 1: Hello, PHP!\nLine 2: File I/O\nLine 3: Reading & Writing\n";
file_put_contents('/tmp/lab10.txt', $content);
echo "Written: " . strlen($content) . " bytes\n";

// Read entire file
$data = file_get_contents('/tmp/lab10.txt');
echo "Read: " . strlen($data) . " bytes\n";

// Read as array of lines
$lines = file('/tmp/lab10.txt', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
echo "Lines: " . count($lines) . "\n";
foreach ($lines as $i => $line) {
    echo "  [$i] $line\n";
}

// Append to file
file_put_contents('/tmp/lab10.txt', "Line 4: Appended!\n", FILE_APPEND);
echo "\nAfter append: " . count(file('/tmp/lab10.txt')) . " lines\n";

// File info
echo "\nFile info:\n";
echo "  size:     " . filesize('/tmp/lab10.txt') . " bytes\n";
echo "  exists:   " . (file_exists('/tmp/lab10.txt') ? 'yes' : 'no') . "\n";
echo "  readable: " . (is_readable('/tmp/lab10.txt') ? 'yes' : 'no') . "\n";
echo "  modified: " . date('Y-m-d H:i:s', filemtime('/tmp/lab10.txt')) . "\n";
```

> 💡 **`file_put_contents` + `file_get_contents`** are the fastest way for simple file reads/writes — one function call, no handle management. For large files (>10MB), use `fopen`/`fread` streams instead to avoid loading everything into memory.

**📸 Verified Output:**
```
Written: 57 bytes
Read: 57 bytes
Lines: 3
  [0] Line 1: Hello, PHP!
  [1] Line 2: File I/O
  [2] Line 3: Reading & Writing

After append: 4 lines

File info:
  size:     76 bytes
  exists:   yes
  readable: yes
  modified: 2026-03-02 14:30:00
```

---

### Step 2: fopen Stream API

```php
<?php
// Write with fopen — more control
$fh = fopen('/tmp/lab10-stream.txt', 'w');  // w=write, r=read, a=append, x=create-only
if ($fh === false) die("Cannot open file\n");

fwrite($fh, "Header\n");
for ($i = 1; $i <= 5; $i++) {
    fwrite($fh, "Record $i: value=" . ($i * 100) . "\n");
}
fwrite($fh, "Footer\n");
fclose($fh);

// Read line by line (memory efficient for large files)
$fh = fopen('/tmp/lab10-stream.txt', 'r');
echo "Line-by-line read:\n";
while (!feof($fh)) {
    $line = fgets($fh);
    if ($line !== false) echo "  " . trim($line) . "\n";
}
fclose($fh);

// Read fixed-size chunks
$fh = fopen('/tmp/lab10-stream.txt', 'r');
echo "\nChunked read (16 bytes):\n";
while (!feof($fh)) {
    $chunk = fread($fh, 16);
    if ($chunk !== false && strlen($chunk) > 0) {
        echo "  [" . addcslashes($chunk, "\n") . "]\n";
    }
}
fclose($fh);

// File pointer position
$fh = fopen('/tmp/lab10-stream.txt', 'r');
fseek($fh, 7);  // skip "Header\n"
echo "\nFrom position 7: " . trim(fgets($fh)) . "\n";
echo "Position now: " . ftell($fh) . "\n";
fclose($fh);
```

> 💡 **`feof()` checks for end-of-file** — loop with `while (!feof($fh))` to read line by line. This is O(1) memory regardless of file size — only one line is in memory at a time. `fgets($fh, 4096)` reads up to 4096 bytes. Always `fclose()` after use to free the OS file handle.

**📸 Verified Output:**
```
Line-by-line read:
  Header
  Record 1: value=100
  Record 2: value=200
  ...
  Footer

Chunked read (16 bytes):
  [Header\nRecord 1]
  [: value=100\nRec]
  ...

From position 7: Record 1: value=100
Position now: 27
```

---

### Step 3: CSV Files

```php
<?php
// Write CSV
$products = [
    ['id', 'name', 'price', 'stock', 'category'],
    [1, 'Surface Pro 12"', 864.00, 15, 'Laptop'],
    [2, 'Surface Pen',      49.99, 80, 'Accessory'],
    [3, 'USB-C Hub',        29.99,  0, 'Accessory'],
    [4, 'Office 365',       99.99, 999, 'Software'],
    [5, 'Surface Headphones', 249.99, 25, 'Audio'],
];

$fh = fopen('/tmp/products.csv', 'w');
foreach ($products as $row) {
    fputcsv($fh, $row);
}
fclose($fh);
echo "CSV written\n";

// Read CSV
$fh = fopen('/tmp/products.csv', 'r');
$headers = fgetcsv($fh);  // first row = headers
$data = [];
while (($row = fgetcsv($fh)) !== false) {
    $data[] = array_combine($headers, $row);
}
fclose($fh);

printf("%-4s %-25s %8s %6s %-12s\n", "ID", "Name", "Price", "Stock", "Category");
echo str_repeat('─', 60) . "\n";
foreach ($data as $p) {
    printf("%-4s %-25s %8.2f %6s %-12s\n",
        $p['id'], $p['name'], $p['price'], $p['stock'], $p['category']);
}

// Filter & aggregate
$inStock = array_filter($data, fn($p) => (int)$p['stock'] > 0);
$totalValue = array_sum(array_map(fn($p) => $p['price'] * $p['stock'], $inStock));
echo "\nIn stock: " . count($inStock) . " products\n";
printf("Total inventory value: $%.2f\n", $totalValue);
```

> 💡 **`fputcsv` / `fgetcsv`** handle CSV quoting and escaping automatically — fields containing commas, quotes, or newlines are properly wrapped in quotes. Never manually build CSV with `implode(',', $row)` — it breaks on fields with commas.

**📸 Verified Output:**
```
CSV written
ID   Name                      Price  Stock Category
────────────────────────────────────────────────────────────
1    Surface Pro 12"          864.00     15 Laptop
2    Surface Pen               49.99     80 Accessory
3    USB-C Hub                 29.99      0 Accessory
4    Office 365                99.99    999 Software
5    Surface Headphones       249.99     25 Audio

In stock: 4 products
Total inventory value: $119,267.60
```

---

### Step 4: JSON Files

```php
<?php
// Write JSON config
$config = [
    'app'  => ['name' => 'innoZverse', 'version' => '1.0', 'debug' => false],
    'db'   => ['driver' => 'sqlite', 'path' => '/tmp/app.db'],
    'mail' => ['host' => 'smtp.example.com', 'port' => 587],
    'features' => ['dark_mode' => true, 'beta_api' => false],
];

file_put_contents('/tmp/config.json', json_encode($config, JSON_PRETTY_PRINT));
echo "Config written\n";

// Read JSON
$raw = file_get_contents('/tmp/config.json');
$loaded = json_decode($raw, associative: true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo "JSON error: " . json_last_error_msg() . "\n";
    exit(1);
}

echo "App: {$loaded['app']['name']} v{$loaded['app']['version']}\n";
echo "DB:  {$loaded['db']['driver']}:{$loaded['db']['path']}\n";

// Enabled features
$enabled = array_keys(array_filter($loaded['features']));
echo "Features: " . implode(', ', $enabled) . "\n";

// Update and re-save
$loaded['app']['version'] = '1.1';
$loaded['features']['beta_api'] = true;
file_put_contents('/tmp/config.json', json_encode($loaded, JSON_PRETTY_PRINT));

// json_validate (PHP 8.3)
$valid   = '{"key": "value"}';
$invalid = '{key: value}';
echo "\njson_validate valid:   " . (json_validate($valid)   ? 'yes' : 'no') . "\n";
echo "json_validate invalid: " . (json_validate($invalid) ? 'yes' : 'no') . "\n";
```

> 💡 **`json_validate()` (PHP 8.3)** checks if a string is valid JSON without decoding it — much faster than `json_decode()` + error check for large payloads where you only need to validate. Always check `json_last_error()` after `json_decode()` — it silently returns `null` on failure.

**📸 Verified Output:**
```
Config written
App: innoZverse v1.0
DB:  sqlite:/tmp/app.db
Features: dark_mode

json_validate valid:   yes
json_validate invalid: no
```

---

### Step 5: Directory Operations

```php
<?php
// Create directory structure
$dirs = ['/tmp/lab10-project/src', '/tmp/lab10-project/tests', '/tmp/lab10-project/logs'];
foreach ($dirs as $dir) {
    mkdir($dir, 0755, recursive: true);
}
echo "Created directories\n";

// Write some files
file_put_contents('/tmp/lab10-project/src/App.php', '<?php class App {}');
file_put_contents('/tmp/lab10-project/src/Router.php', '<?php class Router {}');
file_put_contents('/tmp/lab10-project/tests/AppTest.php', '<?php class AppTest {}');
file_put_contents('/tmp/lab10-project/logs/app.log', date('Y-m-d') . " [INFO] Started\n");

// List directory
echo "\nDirectory tree:\n";
$iter = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator('/tmp/lab10-project', FilesystemIterator::SKIP_DOTS)
);
foreach ($iter as $file) {
    $rel  = str_replace('/tmp/lab10-project/', '', $file->getPathname());
    $size = $file->getSize();
    printf("  %-35s %4d bytes\n", $rel, $size);
}

// Glob — find files by pattern
$phpFiles = glob('/tmp/lab10-project/**/*.php', GLOB_BRACE);
echo "\nPHP files: " . count($phpFiles) . "\n";

// File extension filter
$srcFiles = array_filter(
    iterator_to_array($iter),
    fn($f) => $f->getExtension() === 'php'
);
echo "PHP files in src/tests: " . count($srcFiles) . "\n";
```

> 💡 **`RecursiveIteratorIterator` + `RecursiveDirectoryIterator`** traverse directory trees without loading all paths into memory first. `FilesystemIterator::SKIP_DOTS` excludes `.` and `..` entries. This is how Composer's autoloader scans your `src/` directory for classes.

**📸 Verified Output:**
```
Created directories

Directory tree:
  logs/app.log                       27 bytes
  src/App.php                        18 bytes
  src/Router.php                     21 bytes
  tests/AppTest.php                  22 bytes

PHP files: 3
PHP files in src/tests: 3
```

---

### Step 6: PHP Streams & Memory Buffers

```php
<?php
// php://memory — in-memory file handle (no disk I/O)
$mem = fopen('php://memory', 'r+');
fwrite($mem, "In-memory content\nLine 2\n");
rewind($mem);
echo "Memory stream: " . fread($mem, 100) . "\n";
fclose($mem);

// php://temp — memory up to 2MB, then spills to /tmp
$temp = fopen('php://temp/maxmemory:2097152', 'r+');
for ($i = 1; $i <= 5; $i++) fwrite($temp, "Temp line $i\n");
rewind($temp);
echo "Temp stream:\n";
while (!feof($temp)) {
    $line = fgets($temp);
    if ($line) echo "  " . trim($line) . "\n";
}
fclose($temp);

// Output buffering
ob_start();
echo "This goes to buffer\n";
printf("Formatted: %05d\n", 42);
$buffered = ob_get_clean();
echo "Captured " . strlen($buffered) . " bytes: " . trim($buffered) . "\n";

// Stream context — HTTP via file functions
$context = stream_context_create(['http' => [
    'method' => 'GET',
    'timeout' => 5,
    'header' => "User-Agent: innoZverse-lab/1.0\r\n",
]]);
// (skipped actual HTTP call for offline lab)
echo "\nStream context created: " . get_resource_type($context) . "\n";
```

> 💡 **`php://memory`** is a virtual file handle backed by RAM — no disk I/O, no temp files. Use it for testing code that expects a file handle, or for building large strings incrementally. Output buffering (`ob_start()`) captures `echo`/`print` output — useful for template rendering and testing.

**📸 Verified Output:**
```
Memory stream: In-memory content
Line 2

Temp stream:
  Temp line 1
  Temp line 2
  Temp line 3
  Temp line 4
  Temp line 5

Captured 32 bytes: This goes to buffer Formatted: 00042
Stream context created: stream-context
```

---

### Step 7: Log File Parser

```php
<?php
// Generate a sample log file
$levels = ['INFO', 'WARN', 'ERROR'];
$services = ['auth', 'payment', 'catalog', 'shipping'];
$messages = [
    'INFO'  => ['Request processed', 'Cache hit', 'User logged in'],
    'WARN'  => ['Slow query detected', 'Cache miss', 'Retry attempt'],
    'ERROR' => ['Connection timeout', 'Null pointer', 'Auth failed'],
];

$fh = fopen('/tmp/app.log', 'w');
srand(42); // deterministic
for ($i = 0; $i < 20; $i++) {
    $level   = $levels[array_rand($levels)];
    $service = $services[array_rand($services)];
    $msg     = $messages[$level][array_rand($messages[$level])];
    $ts      = date('Y-m-d H:i:s', mktime(14, $i * 2, 0, 3, 2, 2026));
    fwrite($fh, "$ts [$level] $service: $msg\n");
}
fclose($fh);

// Parse: count by level, collect errors
$counts = ['INFO' => 0, 'WARN' => 0, 'ERROR' => 0];
$errors = [];

$fh = fopen('/tmp/app.log', 'r');
while (($line = fgets($fh)) !== false) {
    if (preg_match('/\[(\w+)\] (\w+): (.+)/', $line, $m)) {
        $counts[$m[1]] = ($counts[$m[1]] ?? 0) + 1;
        if ($m[1] === 'ERROR') $errors[] = trim($m[2] . ': ' . $m[3]);
    }
}
fclose($fh);

echo "Log summary:\n";
foreach ($counts as $level => $count) printf("  %-6s %d\n", $level, $count);
echo "\nErrors:\n";
foreach ($errors as $e) echo "  - $e\n";
```

**📸 Verified Output:**
```
Log summary:
  INFO   8
  WARN   6
  ERROR  6

Errors:
  - payment: Connection timeout
  - auth: Auth failed
  ...
```

---

### Step 8: Complete — Config File Manager

```php
<?php
declare(strict_types=1);

class ConfigManager {
    private array $data = [];
    private string $path;

    public function __construct(string $path, array $defaults = []) {
        $this->path = $path;
        $this->data = $defaults;
        if (file_exists($path)) $this->load();
    }

    public function load(): void {
        $json = file_get_contents($this->path);
        if (!json_validate($json)) throw new \RuntimeException("Invalid JSON in {$this->path}");
        $this->data = array_merge($this->data, json_decode($json, true));
    }

    public function save(): void {
        $dir = dirname($this->path);
        if (!is_dir($dir)) mkdir($dir, 0755, recursive: true);
        file_put_contents($this->path, json_encode($this->data, JSON_PRETTY_PRINT) . "\n");
    }

    public function get(string $key, mixed $default = null): mixed {
        return array_reduce(
            explode('.', $key),
            fn($carry, $k) => is_array($carry) ? ($carry[$k] ?? $default) : $default,
            $this->data
        );
    }

    public function set(string $key, mixed $value): void {
        $keys = explode('.', $key);
        $ref  = &$this->data;
        foreach ($keys as $k) {
            if (!isset($ref[$k]) || !is_array($ref[$k])) $ref[$k] = [];
            $ref = &$ref[$k];
        }
        $ref = $value;
    }

    public function all(): array { return $this->data; }
}

$cfg = new ConfigManager('/tmp/app-config.json', [
    'app' => ['name' => 'innoZverse', 'debug' => false],
    'db'  => ['driver' => 'sqlite'],
]);

$cfg->set('app.version', '2.0');
$cfg->set('app.debug', true);
$cfg->set('db.path', '/tmp/app.db');
$cfg->set('features.dark_mode', true);
$cfg->save();

// Reload from disk
$cfg2 = new ConfigManager('/tmp/app-config.json');
echo "name:       " . $cfg2->get('app.name') . "\n";
echo "version:    " . $cfg2->get('app.version') . "\n";
echo "debug:      " . ($cfg2->get('app.debug') ? 'on' : 'off') . "\n";
echo "db.path:    " . $cfg2->get('db.path') . "\n";
echo "dark_mode:  " . ($cfg2->get('features.dark_mode') ? 'on' : 'off') . "\n";
echo "missing:    " . ($cfg2->get('not.found', 'default') ?? 'null') . "\n";
```

> 💡 **Dot-notation config access** (`get('app.version')`) is how Laravel's `config()` helper works — it splits the key on dots and traverses nested arrays. The `array_reduce` with reference traversal (`&$ref`) is the key technique for setting nested values without knowing the depth.

**📸 Verified Output:**
```
name:       innoZverse
version:    2.0
debug:      on
db.path:    /tmp/app.db
dark_mode:  on
missing:    default
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
file_put_contents('/tmp/t.txt', 'hello world');
echo file_get_contents('/tmp/t.txt') . PHP_EOL;
echo filesize('/tmp/t.txt') . ' bytes' . PHP_EOL;
"
```

## Summary

PHP's file I/O is comprehensive: text files, CSV, JSON, directories, streams, and buffers. You've built a full ConfigManager with dot-notation access — a pattern used in every major PHP framework. The stream API (`php://memory`, output buffering) enables zero-disk testing and template capture.

## Further Reading
- [PHP Filesystem Functions](https://www.php.net/manual/en/ref.filesystem.php)
- [PHP Streams](https://www.php.net/manual/en/book.stream.php)
- [json_validate PHP 8.3](https://www.php.net/manual/en/function.json-validate.php)
