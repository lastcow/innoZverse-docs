# Lab 05: Custom Stream Wrappers

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

PHP's stream API is extensible—you can register custom protocols (`myproto://`) that work transparently with `file_get_contents()`, `fopen()`, `fwrite()`, and all stream functions. This lab builds a memory-backed stream, then a SQLite-backed `db://` stream wrapper.

---

## Step 1: Stream Wrapper Interface

A stream wrapper must implement these methods:

```
stream_open($path, $mode, $options, &$opened_path)  → bool
stream_read($count)                                  → string
stream_write($data)                                  → int
stream_eof()                                         → bool
stream_stat()                                        → array
stream_seek($offset, $whence)                        → bool
stream_tell()                                        → int
stream_flush()                                       → bool
stream_close()                                       → void
url_stat($path, $flags)                              → array
unlink($path)                                        → bool
mkdir($path, $mode, $options)                        → bool
rmdir($path, $options)                               → bool
dir_opendir($path, $options)                         → bool
dir_readdir()                                        → string|false
dir_closedir()                                       → bool
rename($path_from, $path_to)                         → bool
```

> 💡 You only need to implement the methods your use case requires. `stream_open`, `stream_read`, `stream_eof`, and `stream_stat` are the minimum for read-only streams.

---

## Step 2: In-Memory Stream Wrapper

```php
<?php
class MemoryStreamWrapper {
    /** @var array<string, string> shared storage across instances */
    private static array $storage = [];
    private string $path = '';
    private int $position = 0;
    private string $mode = 'r';
    
    // Required: PHP will set this property
    public mixed $context = null;
    
    public function stream_open(string $path, string $mode, int $options, ?string &$opened_path): bool {
        $this->path     = $path;
        $this->mode     = $mode;
        $this->position = 0;
        
        if (!isset(self::$storage[$path])) {
            self::$storage[$path] = '';
        }
        
        // Truncate on 'w' mode
        if (str_contains($mode, 'w')) {
            self::$storage[$path] = '';
        }
        
        $opened_path = $path;
        return true;
    }
    
    public function stream_read(int $count): string|false {
        $data = substr(self::$storage[$this->path], $this->position, $count);
        $this->position += strlen($data);
        return $data;
    }
    
    public function stream_write(string $data): int {
        $len = strlen($data);
        $content = self::$storage[$this->path];
        
        // Handle seek position
        $before = substr($content, 0, $this->position);
        $after  = substr($content, $this->position + $len);
        self::$storage[$this->path] = $before . $data . $after;
        $this->position += $len;
        
        return $len;
    }
    
    public function stream_eof(): bool {
        return $this->position >= strlen(self::$storage[$this->path]);
    }
    
    public function stream_tell(): int {
        return $this->position;
    }
    
    public function stream_seek(int $offset, int $whence = SEEK_SET): bool {
        $size = strlen(self::$storage[$this->path]);
        $this->position = match ($whence) {
            SEEK_SET => $offset,
            SEEK_CUR => $this->position + $offset,
            SEEK_END => $size + $offset,
            default  => $this->position,
        };
        $this->position = max(0, min($this->position, $size));
        return true;
    }
    
    public function stream_flush(): bool { return true; }
    public function stream_close(): void { }
    
    public function stream_stat(): array {
        $size = strlen(self::$storage[$this->path] ?? '');
        return [
            'size'  => $size,
            'mtime' => time(),
            'mode'  => 0100644,
        ];
    }
    
    public function url_stat(string $path, int $flags): array|false {
        if (!isset(self::$storage[$path])) return false;
        return $this->stream_stat();
    }
    
    public function unlink(string $path): bool {
        if (isset(self::$storage[$path])) {
            unset(self::$storage[$path]);
            return true;
        }
        return false;
    }
    
    public static function listKeys(): array {
        return array_keys(self::$storage);
    }
}

// Register the wrapper
stream_wrapper_register('mem', MemoryStreamWrapper::class)
    or die("Failed to register mem:// wrapper");

// Test it
file_put_contents('mem://config/database', 'host=localhost;port=5432;db=myapp');
file_put_contents('mem://config/redis',    'host=redis;port=6379;db=0');

echo file_get_contents('mem://config/database') . "\n";
echo file_get_contents('mem://config/redis') . "\n";

// Append mode
$fh = fopen('mem://log/app', 'a');
fwrite($fh, "[2024-01-01] INFO: App started\n");
fwrite($fh, "[2024-01-01] INFO: Listening on :8080\n");
fclose($fh);

echo "\n=== App Log ===\n";
echo file_get_contents('mem://log/app');

// Seek
$fh = fopen('mem://config/database', 'r');
fseek($fh, 5);
echo "\nFrom offset 5: " . fread($fh, 9) . "\n"; // "localhost"
fclose($fh);

echo "\nStored keys: " . implode(', ', MemoryStreamWrapper::listKeys()) . "\n";
```

📸 **Verified Output:**
```
host=localhost;port=5432;db=myapp
host=redis;port=6379;db=0

=== App Log ===
[2024-01-01] INFO: App started
[2024-01-01] INFO: Listening on :8080

From offset 5: localhost

Stored keys: mem://config/database, mem://config/redis, mem://log/app
```

---

## Step 3: Stream Context

```php
<?php
// stream_context_create passes options to the wrapper
class HttpMockWrapper {
    public mixed $context = null;
    private array $data = [];
    private int $pos = 0;
    
    public function stream_open(string $path, string $mode, int $options, ?string &$opened): bool {
        $opts = stream_context_get_options($this->context ?? stream_context_get_default());
        $method  = $opts['http']['method'] ?? 'GET';
        $headers = $opts['http']['header'] ?? '';
        $body    = $opts['http']['content'] ?? '';
        
        // Simulate a response
        $responseBody = json_encode([
            'url'    => $path,
            'method' => $method,
            'body'   => $body,
            'echo'   => 'mock response',
        ]);
        
        $this->data = str_split($responseBody, 1024);
        $this->pos  = 0;
        return true;
    }
    
    public function stream_read(int $count): string {
        return array_shift($this->data) ?? '';
    }
    
    public function stream_eof(): bool { return empty($this->data); }
    public function stream_stat(): array { return []; }
    public function url_stat(string $p, int $f): array { return []; }
}

stream_wrapper_register('mock', HttpMockWrapper::class);

$ctx = stream_context_create([
    'http' => [
        'method'  => 'POST',
        'header'  => "Content-Type: application/json\r\nAuthorization: Bearer token123",
        'content' => json_encode(['action' => 'create', 'name' => 'test']),
    ]
]);

$response = file_get_contents('mock://api.example.com/resource', false, $ctx);
$data = json_decode($response, true);
echo "Mock response:\n";
echo "  URL:    {$data['url']}\n";
echo "  Method: {$data['method']}\n";
echo "  Body:   {$data['body']}\n";
```

---

## Step 4: SQLite-Backed db:// Stream Wrapper

```php
<?php
class DbStreamWrapper {
    private static ?PDO $pdo = null;
    private string $key = '';
    private string $buffer = '';
    private int $pos = 0;
    public mixed $context = null;
    
    private static function db(): PDO {
        if (!self::$pdo) {
            self::$pdo = new PDO('sqlite:/tmp/stream_store.db');
            self::$pdo->exec('CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER DEFAULT (strftime(\'%s\',\'now\'))
            )');
        }
        return self::$pdo;
    }
    
    public function stream_open(string $path, string $mode, int $options, ?string &$opened): bool {
        // db://bucket/key → key = "bucket/key"
        $this->key = ltrim(parse_url($path, PHP_URL_HOST) . parse_url($path, PHP_URL_PATH), '/');
        $this->pos = 0;
        
        if (str_contains($mode, 'w')) {
            $this->buffer = '';
            self::db()->prepare('INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)')->execute([$this->key, '']);
        } else {
            $stmt = self::db()->prepare('SELECT value FROM kv WHERE key = ?');
            $stmt->execute([$this->key]);
            $this->buffer = $stmt->fetchColumn() ?: '';
        }
        return true;
    }
    
    public function stream_read(int $count): string {
        $chunk = substr($this->buffer, $this->pos, $count);
        $this->pos += strlen($chunk);
        return $chunk;
    }
    
    public function stream_write(string $data): int {
        $this->buffer .= $data;
        self::db()->prepare('INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)')->execute([$this->key, $this->buffer]);
        return strlen($data);
    }
    
    public function stream_eof(): bool { return $this->pos >= strlen($this->buffer); }
    public function stream_tell(): int { return $this->pos; }
    public function stream_flush(): bool { return true; }
    public function stream_close(): void {}
    
    public function stream_seek(int $offset, int $whence = SEEK_SET): bool {
        $size = strlen($this->buffer);
        $this->pos = match ($whence) {
            SEEK_SET => $offset,
            SEEK_CUR => $this->pos + $offset,
            SEEK_END => $size + $offset,
            default  => $this->pos,
        };
        return true;
    }
    
    public function stream_stat(): array {
        return ['size' => strlen($this->buffer), 'mtime' => time(), 'mode' => 0100644];
    }
    
    public function url_stat(string $path, int $flags): array|false {
        $key = ltrim(parse_url($path, PHP_URL_HOST) . parse_url($path, PHP_URL_PATH), '/');
        $stmt = self::db()->prepare('SELECT length(value) FROM kv WHERE key = ?');
        $stmt->execute([$key]);
        $size = $stmt->fetchColumn();
        if ($size === false) return false;
        return ['size' => (int)$size, 'mtime' => time(), 'mode' => 0100644];
    }
    
    public function unlink(string $path): bool {
        $key = ltrim(parse_url($path, PHP_URL_HOST) . parse_url($path, PHP_URL_PATH), '/');
        self::db()->prepare('DELETE FROM kv WHERE key = ?')->execute([$key]);
        return true;
    }
}

stream_wrapper_register('db', DbStreamWrapper::class);

// Store config values
file_put_contents('db://config/app.json', json_encode([
    'debug' => false,
    'db_host' => 'localhost',
    'workers' => 4,
]));

file_put_contents('db://cache/user:1001', serialize([
    'id' => 1001, 'name' => 'Alice', 'role' => 'admin'
]));

// Read them back
$config = json_decode(file_get_contents('db://config/app.json'), true);
echo "Config: db_host={$config['db_host']}, workers={$config['workers']}\n";

$user = unserialize(file_get_contents('db://cache/user:1001'));
echo "User: id={$user['id']}, name={$user['name']}, role={$user['role']}\n";

// file_exists via url_stat
echo "config/app.json exists: " . (file_exists('db://config/app.json') ? 'yes' : 'no') . "\n";
echo "config/missing exists:  " . (file_exists('db://config/missing') ? 'yes' : 'no') . "\n";

// Append log entries
$fh = fopen('db://logs/audit', 'a');
fwrite($fh, date('Y-m-d H:i:s') . " user:1001 login\n");
fwrite($fh, date('Y-m-d H:i:s') . " user:1001 viewed /dashboard\n");
fclose($fh);

echo "\nAudit log:\n" . file_get_contents('db://logs/audit');
```

📸 **Verified Output:**
```
Config: db_host=localhost, workers=4
User: id=1001, name=Alice, role=admin
config/app.json exists: yes
config/missing exists:  no

Audit log:
2024-01-15 10:30:00 user:1001 login
2024-01-15 10:30:00 user:1001 viewed /dashboard
```

---

## Step 5: Stream Filters

```php
<?php
// Chaining stream filters with custom wrappers
// PHP has built-in filters: string.toupper, string.tolower, string.rot13,
// convert.base64-encode, convert.base64-decode, zlib.deflate, zlib.inflate

// Write JSON, apply base64 filter on read
file_put_contents('/tmp/test_stream.json', json_encode(['key' => 'value', 'num' => 42]));

// Read with base64 encoding filter
$fh = fopen('/tmp/test_stream.json', 'r');
stream_filter_append($fh, 'convert.base64-encode');
$encoded = stream_get_contents($fh);
fclose($fh);

echo "Base64 encoded: {$encoded}\n";
echo "Decoded: " . base64_decode($encoded) . "\n";

// ROT13 filter
$fh = fopen('php://memory', 'r+');
fwrite($fh, 'Hello, Secret World!');
rewind($fh);
stream_filter_append($fh, 'string.rot13');
echo "ROT13: " . stream_get_contents($fh) . "\n";
fclose($fh);

// Compression filter
$data = str_repeat('AAABBBCCC', 1000);
$fh = fopen('php://memory', 'r+');
$filter = stream_filter_append($fh, 'zlib.deflate', STREAM_FILTER_WRITE);
fwrite($fh, $data);
stream_filter_remove($filter);
$compressed = stream_get_contents($fh, -1, 0);
fclose($fh);

echo "Original: " . strlen($data) . " bytes\n";
echo "Compressed: " . strlen($compressed) . " bytes\n";
echo "Ratio: " . round(strlen($compressed) / strlen($data) * 100, 1) . "%\n";
```

---

## Step 6: Directory Listing Support

```php
<?php
// Add directory listing to the memory wrapper
class MemDirWrapper extends MemoryStreamWrapper {
    private array $keys = [];
    private int $dirPos = 0;
    private string $dirPath = '';
    
    public function dir_opendir(string $path, int $options): bool {
        $this->dirPath = rtrim($path, '/') . '/';
        $this->keys    = [];
        $this->dirPos  = 0;
        
        foreach (MemoryStreamWrapper::listKeys() as $key) {
            if (str_starts_with($key, $this->dirPath)) {
                $relative = substr($key, strlen($this->dirPath));
                if (!str_contains($relative, '/')) {
                    $this->keys[] = $relative;
                }
            }
        }
        return true;
    }
    
    public function dir_readdir(): string|false {
        return $this->keys[$this->dirPos++] ?? false;
    }
    
    public function dir_closedir(): bool { return true; }
}
```

---

## Step 7: Error Handling & Options

```php
<?php
// Proper error handling in stream wrappers
class SafeMemWrapper {
    private static array $store = [];
    private string $path = '';
    private string $buffer = '';
    private int $pos = 0;
    public mixed $context = null;
    
    public function stream_open(string $path, string $mode, int $options, ?string &$opened): bool {
        $this->path = $path;
        $this->pos  = 0;
        
        $readModes  = ['r', 'rb'];
        $writeModes = ['w', 'wb', 'a', 'ab'];
        $createModes = ['w', 'wb', 'a', 'ab', 'x', 'xb'];
        
        if (in_array($mode, $readModes) && !isset(self::$store[$path])) {
            if ($options & STREAM_REPORT_ERRORS) {
                trigger_error("safe://: No such file: {$path}", E_USER_WARNING);
            }
            return false;
        }
        
        if (in_array($mode, $createModes) && isset(self::$store[$path]) && str_starts_with($mode, 'x')) {
            if ($options & STREAM_REPORT_ERRORS) {
                trigger_error("safe://: File already exists: {$path}", E_USER_WARNING);
            }
            return false;
        }
        
        self::$store[$path] ??= '';
        if (str_starts_with($mode, 'w')) self::$store[$path] = '';
        if (str_starts_with($mode, 'a')) $this->pos = strlen(self::$store[$path]);
        
        $this->buffer = self::$store[$path];
        return true;
    }
    
    public function stream_read(int $count): string {
        $chunk = substr(self::$store[$this->path], $this->pos, $count);
        $this->pos += strlen($chunk);
        return $chunk;
    }
    public function stream_write(string $data): int {
        self::$store[$this->path] .= $data;
        $this->pos += strlen($data);
        return strlen($data);
    }
    public function stream_eof(): bool  { return $this->pos >= strlen(self::$store[$this->path]); }
    public function stream_stat(): array { return ['size' => strlen(self::$store[$this->path] ?? ''), 'mode' => 0100644]; }
    public function url_stat(string $p, int $f): array|false { return isset(self::$store[$p]) ? $this->stream_stat() : false; }
}

stream_wrapper_register('safe', SafeMemWrapper::class);

// Writing and reading
file_put_contents('safe://data/config', 'database_url=mysql://localhost/mydb');
echo file_get_contents('safe://data/config') . "\n";

// Missing file triggers warning (suppressed with @)
$result = @file_get_contents('safe://data/missing');
echo "Missing file returns: " . var_export($result, true) . "\n";

echo "exists: " . (file_exists('safe://data/config') ? 'yes' : 'no') . "\n";
```

📸 **Verified Output:**
```
database_url=mysql://localhost/mydb
Missing file returns: false
exists: yes
```

---

## Step 8: Capstone — Encrypted Config Stream Wrapper

```php
<?php
/**
 * Encrypted config stream wrapper: enc://
 * - Stores encrypted values in SQLite
 * - Transparent encrypt on write, decrypt on read
 * - Uses libsodium XSalsa20-Poly1305
 */
class EncryptedConfigWrapper {
    private static ?PDO $pdo = null;
    private static string $key = '';
    private string $path = '';
    private string $buffer = '';
    private int $pos = 0;
    public mixed $context = null;
    
    public static function init(string $masterKey): void {
        // Derive encryption key from master key
        self::$key = hash('sha256', $masterKey, true);
        self::db()->exec('CREATE TABLE IF NOT EXISTS enc_config (
            path TEXT PRIMARY KEY,
            ciphertext TEXT NOT NULL,
            nonce TEXT NOT NULL
        )');
    }
    
    private static function db(): PDO {
        return self::$pdo ??= new PDO('sqlite::memory:');
    }
    
    private static function encrypt(string $plaintext): array {
        $nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $ct    = sodium_crypto_secretbox($plaintext, $nonce, self::$key);
        return ['ct' => base64_encode($ct), 'nonce' => base64_encode($nonce)];
    }
    
    private static function decrypt(string $ct64, string $nonce64): string {
        $ct    = base64_decode($ct64);
        $nonce = base64_decode($nonce64);
        return sodium_crypto_secretbox_open($ct, $nonce, self::$key);
    }
    
    public function stream_open(string $path, string $mode, int $options, ?string &$opened): bool {
        $this->path = $path;
        $this->pos  = 0;
        
        if (str_starts_with($mode, 'r')) {
            $stmt = self::db()->prepare('SELECT ciphertext, nonce FROM enc_config WHERE path = ?');
            $stmt->execute([$path]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            $this->buffer = $row ? self::decrypt($row['ciphertext'], $row['nonce']) : '';
        } else {
            $this->buffer = '';
        }
        return true;
    }
    
    public function stream_write(string $data): int {
        $this->buffer .= $data;
        $enc = self::encrypt($this->buffer);
        self::db()->prepare('INSERT OR REPLACE INTO enc_config VALUES (?, ?, ?)')
            ->execute([$this->path, $enc['ct'], $enc['nonce']]);
        return strlen($data);
    }
    
    public function stream_read(int $count): string {
        $chunk = substr($this->buffer, $this->pos, $count);
        $this->pos += strlen($chunk);
        return $chunk;
    }
    
    public function stream_eof(): bool { return $this->pos >= strlen($this->buffer); }
    public function stream_stat(): array { return ['size' => strlen($this->buffer), 'mode' => 0100600]; }
    public function url_stat(string $p, int $f): array|false { return []; }
}

EncryptedConfigWrapper::init('my-super-secret-master-key-2024');
stream_wrapper_register('enc', EncryptedConfigWrapper::class);

// Store sensitive config
file_put_contents('enc://secrets/db_password', 'p@ssw0rd!#$%');
file_put_contents('enc://secrets/api_key',     'sk-1234567890abcdef');
file_put_contents('enc://secrets/jwt_secret',  'jwt-hmac-secret-xyz');

// Read back transparently
$dbPass  = file_get_contents('enc://secrets/db_password');
$apiKey  = file_get_contents('enc://secrets/api_key');
$jwtSec  = file_get_contents('enc://secrets/jwt_secret');

echo "=== Encrypted Config Stream ===\n";
echo "DB Password: {$dbPass}\n";
echo "API Key:     {$apiKey}\n";
echo "JWT Secret:  {$jwtSec}\n";
echo "\nAll values stored encrypted in SQLite.\n";
echo "Reading decrypts transparently.\n";
```

📸 **Verified Output:**
```
=== Encrypted Config Stream ===
DB Password: p@ssw0rd!#$%
API Key:     sk-1234567890abcdef
JWT Secret:  jwt-hmac-secret-xyz

All values stored encrypted in SQLite.
Reading decrypts transparently.
```

---

## Summary

| Feature | Function | Use Case |
|---------|----------|----------|
| Register wrapper | `stream_wrapper_register('proto', Class::class)` | Add custom `proto://` protocol |
| Check wrappers | `stream_get_wrappers()` | List all registered protocols |
| File functions | `file_get_contents/file_put_contents/fopen` | Work transparently with custom streams |
| Stream context | `stream_context_create(['proto' => [...]])` | Pass options to wrapper |
| Get context options | `stream_context_get_options($context)` | Read wrapper options |
| Built-in filters | `stream_filter_append($fh, 'zlib.deflate')` | Compress/encode on the fly |
| Remove wrapper | `stream_wrapper_unregister('proto')` | Clean up or replace |
| Restore built-in | `stream_wrapper_restore('file')` | Restore overridden wrappers |
| Stat support | `url_stat()` | Enables `file_exists()`, `filesize()` |
| Directory support | `dir_opendir/dir_readdir` | Enables `opendir()`, `scandir()` |
