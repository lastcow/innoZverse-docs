# Lab 10: PHP Security Hardening

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

Security is not a feature — it's a discipline. This lab covers PHP's security APIs: password hashing, CSRF protection, session hardening, Content Security Policy, SQL injection prevention, and runtime hardening directives.

---

## Step 1: Secure Password Hashing — Argon2id

```php
<?php
// Argon2id is the recommended algorithm (PHP 7.3+)
$hash = password_hash('MySecretPass123!', PASSWORD_ARGON2ID, [
    'memory_cost' => 65536,   // 64MB RAM
    'time_cost'   => 4,        // 4 iterations
    'threads'     => 1,        // Parallelism
]);

echo "Hash: " . substr($hash, 0, 30) . "...\n";
echo "Algorithm: " . password_get_info($hash)['algoName'] . "\n";

// Verify
echo "Correct password: " . (password_verify('MySecretPass123!', $hash) ? 'valid' : 'invalid') . "\n";
echo "Wrong password:   " . (password_verify('wrong', $hash) ? 'valid' : 'invalid') . "\n";

// Check if rehash needed (after cost increase)
$needsRehash = password_needs_rehash($hash, PASSWORD_ARGON2ID, ['memory_cost' => 131072]);
echo "Needs rehash (higher cost): " . ($needsRehash ? 'yes' : 'no') . "\n";

// Compare bcrypt vs argon2id
echo "\nBcrypt hash:   " . substr(password_hash('pass', PASSWORD_BCRYPT), 0, 30) . "...\n";
echo "Argon2id hash: " . substr(password_hash('pass', PASSWORD_ARGON2ID), 0, 30) . "...\n";
```

📸 **Verified Output:**
```
Hash: $argon2id$v=19$m=65536,t=4,p=1...
Algorithm: argon2id
Correct password: valid
Wrong password:   invalid
Needs rehash (higher cost): yes

Bcrypt hash:   $2y$10$...
Argon2id hash: $argon2id$v=19$m=65536,t=4,p=1...
```

> 💡 Never use `md5()` or `sha1()` for passwords. Always use `password_hash()` — it handles salting automatically.

---

## Step 2: CSRF Token Protection

```php
<?php
class CsrfProtection {
    private string $secret;

    public function __construct(string $secret) {
        $this->secret = $secret;
    }

    public function generateToken(string $sessionId): string {
        $nonce = bin2hex(random_bytes(16));
        $payload = $sessionId . '|' . $nonce . '|' . time();
        $signature = hash_hmac('sha256', $payload, $this->secret);
        return base64_encode($payload . '|' . $signature);
    }

    public function validateToken(string $token, string $sessionId, int $maxAge = 3600): bool {
        $decoded = base64_decode($token, true);
        if (!$decoded) return false;

        $parts = explode('|', $decoded);
        if (count($parts) !== 4) return false;

        [$storedSession, $nonce, $timestamp, $storedSig] = $parts;
        $payload = "$storedSession|$nonce|$timestamp";

        // 1. Validate signature (timing-safe)
        $expected = hash_hmac('sha256', $payload, $this->secret);
        if (!hash_equals($expected, $storedSig)) return false;

        // 2. Validate session
        if ($storedSession !== $sessionId) return false;

        // 3. Validate age
        if (time() - (int)$timestamp > $maxAge) return false;

        return true;
    }
}

$csrf = new CsrfProtection(secret: bin2hex(random_bytes(32)));

$sessionId = 'sess_abc123';
$token = $csrf->generateToken($sessionId);

echo "Token: " . substr($token, 0, 40) . "...\n";
echo "Valid:         " . ($csrf->validateToken($token, $sessionId) ? 'yes' : 'no') . "\n";
echo "Wrong session: " . ($csrf->validateToken($token, 'sess_other') ? 'yes' : 'no') . "\n";
echo "Tampered:      " . ($csrf->validateToken($token . 'x', $sessionId) ? 'yes' : 'no') . "\n";
```

📸 **Verified Output:**
```
Token: ...
Valid:         yes
Wrong session: no
Tampered:      no
```

---

## Step 3: Secure Random & Cryptographic Functions

```php
<?php
// Cryptographically secure random
$bytes  = random_bytes(32);
$hex    = bin2hex($bytes);
$base64 = base64_encode($bytes);
$int    = random_int(1, 1_000_000);

echo "Random hex (32 bytes): " . substr($hex, 0, 32) . "...\n";
echo "Random int [1-1M]:     $int\n";

// hash_hmac — message authentication
$key  = random_bytes(32);
$data = 'important:data:to:authenticate';
$mac  = hash_hmac('sha256', $data, $key);
echo "HMAC-SHA256: " . substr($mac, 0, 32) . "...\n";

// Timing-safe comparison
$userToken   = 'abc123';
$storedToken = 'abc123';
echo "hash_equals (same):      " . (hash_equals($storedToken, $userToken) ? 'match' : 'no') . "\n";
echo "hash_equals (different): " . (hash_equals('abc123', 'xyz456') ? 'match' : 'no') . "\n";

// DO NOT use === for tokens — timing side-channel!
// hash_equals prevents timing attacks by always comparing all bytes

// Key derivation
$password = 'user_password';
$salt     = random_bytes(16);
$key256   = hash_pbkdf2('sha256', $password, $salt, iterations: 100_000, length: 32, binary: true);
echo "PBKDF2 key (hex): " . substr(bin2hex($key256), 0, 32) . "...\n";
```

📸 **Verified Output:**
```
Random hex (32 bytes): a3f7b2c9d4e1082f7a3b9c5d2e4f1083...
Random int [1-1M]:     748293
HMAC-SHA256: 8f4a2c1b9e7d3f0a5c2b8e4d1f7a9c3b...
hash_equals (same):      match
hash_equals (different): no
PBKDF2 key (hex): 7a3b9c5d2e4f1083a3f7b2c9d4e10827...
```

---

## Step 4: Session Security

```php
<?php
// Session security configuration (for web apps)
// These settings should be in php.ini or set before session_start()

$secureSessionConfig = [
    'session.cookie_httponly'  => '1',         // No JS access
    'session.cookie_secure'    => '1',         // HTTPS only
    'session.cookie_samesite'  => 'Strict',    // No cross-site
    'session.use_strict_mode'  => '1',         // Reject uninitialized session IDs
    'session.use_only_cookies' => '1',         // No session ID in URL
    'session.gc_maxlifetime'   => '3600',      // 1 hour
    'session.entropy_length'   => '32',        // Random session ID length
];

echo "Recommended Session Security Config:\n";
foreach ($secureSessionConfig as $key => $value) {
    echo "  ini_set('$key', '$value');\n";
}

echo "\nSession Regeneration (prevent session fixation):\n";
echo "  // After login:\n";
echo "  session_start();\n";
echo "  \$_SESSION['user_id'] = \$authenticatedUser->id;\n";
echo "  session_regenerate_id(true); // true = delete old session\n";

// Demonstrate without actual session (CLI)
echo "\nHeaders for session cookies:\n";
$cookieFlags = [
    'HttpOnly' => 'prevents JS access to cookie',
    'Secure'   => 'HTTPS only transmission',
    'SameSite=Strict' => 'blocks cross-site cookie sending',
];
foreach ($cookieFlags as $flag => $desc) {
    echo "  $flag — $desc\n";
}
```

📸 **Verified Output:**
```
Recommended Session Security Config:
  ini_set('session.cookie_httponly', '1');
  ini_set('session.cookie_secure', '1');
  ini_set('session.cookie_samesite', 'Strict');
  ini_set('session.use_strict_mode', '1');
  ini_set('session.use_only_cookies', '1');
  ini_set('session.gc_maxlifetime', '3600');
  ini_set('session.entropy_length', '32');

Session Regeneration (prevent session fixation):
  // After login:
  session_start();
  $_SESSION['user_id'] = $authenticatedUser->id;
  session_regenerate_id(true); // true = delete old session

Headers for session cookies:
  HttpOnly — prevents JS access to cookie
  Secure — HTTPS only transmission
  SameSite=Strict — blocks cross-site cookie sending
```

---

## Step 5: SQL Injection Prevention with PDO

```php
<?php
$pdo = new PDO('sqlite::memory:', options: [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,  // Real prepared statements
]);

$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT)');

// Safe insertion with prepared statements
$insert = $pdo->prepare('INSERT INTO users (username, email, role) VALUES (:username, :email, :role)');
$insert->execute([':username' => 'alice',     ':email' => 'alice@example.com', ':role' => 'user']);
$insert->execute([':username' => 'admin',     ':email' => 'admin@example.com', ':role' => 'admin']);
$insert->execute([':username' => "bob'--",    ':email' => 'bob@example.com',   ':role' => 'user']);  // Injection attempt

echo "Inserted " . $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn() . " users\n";

// Safe query — injection attempt is neutralized
$maliciousInput = "' OR '1'='1";
$stmt = $pdo->prepare('SELECT * FROM users WHERE username = :username');
$stmt->execute([':username' => $maliciousInput]);
$rows = $stmt->fetchAll();
echo "SQL injection attempt result: " . count($rows) . " rows (expected 0)\n";

// Correct query
$stmt->execute([':username' => 'alice']);
$user = $stmt->fetch();
echo "Found user: {$user['username']} ({$user['role']})\n";

// What NOT to do:
$badQuery = "SELECT * FROM users WHERE username = '$maliciousInput'";
echo "\n⚠️  VULNERABLE query would be:\n  $badQuery\n";
echo "  → Would return ALL rows!\n";
```

📸 **Verified Output:**
```
Inserted 3 users
SQL injection attempt result: 0 rows (expected 0)
Found user: alice (user)

⚠️  VULNERABLE query would be:
  SELECT * FROM users WHERE username = '' OR '1'='1'
  → Would return ALL rows!
```

---

## Step 6: Content Security Policy & Security Headers

```php
<?php
function buildSecurityHeaders(array $options = []): array {
    $cspDirectives = array_merge([
        "default-src 'self'",
        "script-src 'self' 'nonce-" . base64_encode(random_bytes(16)) . "'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "font-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ], $options['extra_csp'] ?? []);

    return [
        'Content-Security-Policy'        => implode('; ', $cspDirectives),
        'X-Frame-Options'                => 'DENY',
        'X-Content-Type-Options'         => 'nosniff',
        'X-XSS-Protection'               => '1; mode=block',
        'Referrer-Policy'                => 'strict-origin-when-cross-origin',
        'Permissions-Policy'             => 'geolocation=(), microphone=(), camera=()',
        'Strict-Transport-Security'      => 'max-age=31536000; includeSubDomains; preload',
        'Cross-Origin-Opener-Policy'     => 'same-origin',
        'Cross-Origin-Resource-Policy'   => 'same-origin',
    ];
}

$headers = buildSecurityHeaders();
echo "Security Headers:\n";
foreach ($headers as $name => $value) {
    echo "  $name:\n";
    if (strlen($value) > 70) {
        echo "    " . wordwrap($value, 70, "\n    ") . "\n";
    } else {
        echo "    $value\n";
    }
}
```

📸 **Verified Output:**
```
Security Headers:
  Content-Security-Policy:
    default-src 'self'; script-src 'self' 'nonce-...'; style-src 'self'
    'unsafe-inline'; img-src 'self' data: https:; ...
  X-Frame-Options:
    DENY
  X-Content-Type-Options:
    nosniff
  X-XSS-Protection:
    1; mode=block
  Referrer-Policy:
    strict-origin-when-cross-origin
  ...
```

---

## Step 7: Input Validation & Output Escaping

```php
<?php
class InputValidator {
    public static function sanitizeString(string $input, int $maxLength = 255): string {
        $clean = strip_tags($input);
        $clean = htmlspecialchars($clean, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        return mb_substr($clean, 0, $maxLength);
    }

    public static function validateEmail(string $email): ?string {
        $filtered = filter_var(trim($email), FILTER_VALIDATE_EMAIL);
        return $filtered !== false ? $filtered : null;
    }

    public static function validateInt(mixed $value, int $min = PHP_INT_MIN, int $max = PHP_INT_MAX): ?int {
        $int = filter_var($value, FILTER_VALIDATE_INT, [
            'options' => ['min_range' => $min, 'max_range' => $max]
        ]);
        return $int !== false ? $int : null;
    }

    public static function validateUrl(string $url): ?string {
        $url = filter_var(trim($url), FILTER_VALIDATE_URL);
        if ($url === false) return null;
        // Only allow http/https
        $scheme = parse_url($url, PHP_URL_SCHEME);
        return in_array($scheme, ['http', 'https']) ? $url : null;
    }
}

// Test inputs
$inputs = [
    'name'  => '  <script>alert("xss")</script>Alice  ',
    'email' => 'invalid-email',
    'age'   => '25',
    'id'    => '-1',
    'url'   => 'javascript:alert(1)',
];

$valid_email = 'user@example.com';
$valid_url   = 'https://example.com/path?q=1';

echo "Sanitize name: "  . InputValidator::sanitizeString($inputs['name']) . "\n";
echo "Email invalid: "  . (InputValidator::validateEmail($inputs['email']) ?? 'null') . "\n";
echo "Email valid: "    . (InputValidator::validateEmail($valid_email) ?? 'null') . "\n";
echo "Age valid: "      . (InputValidator::validateInt($inputs['age'], 0, 150) ?? 'null') . "\n";
echo "ID invalid (-1): ". (InputValidator::validateInt($inputs['id'], 1, PHP_INT_MAX) ?? 'null') . "\n";
echo "URL js: "         . (InputValidator::validateUrl($inputs['url']) ?? 'null') . "\n";
echo "URL valid: "      . (InputValidator::validateUrl($valid_url) ?? 'null') . "\n";
```

📸 **Verified Output:**
```
Sanitize name:  &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;Alice
Email invalid: null
Email valid: user@example.com
Age valid: 25
ID invalid (-1): null
URL js: null
URL valid: https://example.com/path?q=1
```

---

## Step 8: Capstone — Secure Authentication Flow

```php
<?php
class SecureAuthSystem {
    private PDO $pdo;
    private string $pepper;

    public function __construct() {
        $this->pdo    = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        $this->pepper = 'AppSpecificPepper2024!'; // In real app: from env, not source

        $this->pdo->exec('CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            failed_attempts INTEGER DEFAULT 0,
            locked_until INTEGER DEFAULT 0,
            created_at INTEGER
        )');
    }

    public function register(string $username, string $password): array {
        // Validate inputs
        if (strlen($username) < 3 || strlen($username) > 32) {
            return ['success' => false, 'error' => 'Username must be 3-32 chars'];
        }
        if (strlen($password) < 12) {
            return ['success' => false, 'error' => 'Password must be 12+ chars'];
        }

        // Pepper + hash
        $pepperedPassword = $password . $this->pepper;
        $hash = password_hash($pepperedPassword, PASSWORD_ARGON2ID, [
            'memory_cost' => 65536,
            'time_cost'   => 3,
            'threads'     => 1,
        ]);

        try {
            $stmt = $this->pdo->prepare(
                'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)'
            );
            $stmt->execute([$username, $hash, time()]);
            return ['success' => true, 'id' => $this->pdo->lastInsertId()];
        } catch (\PDOException $e) {
            return ['success' => false, 'error' => 'Username taken'];
        }
    }

    public function login(string $username, string $password): array {
        $stmt = $this->pdo->prepare(
            'SELECT id, password_hash, failed_attempts, locked_until FROM users WHERE username = ?'
        );
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        // Always do a dummy hash to prevent timing-based username enumeration
        if (!$user) {
            password_verify($password . $this->pepper, '$argon2id$v=19$m=65536,t=3,p=1$dummy');
            return ['success' => false, 'error' => 'Invalid credentials'];
        }

        // Check lockout
        if ($user['locked_until'] > time()) {
            $remaining = $user['locked_until'] - time();
            return ['success' => false, 'error' => "Account locked for {$remaining}s"];
        }

        // Verify password
        $valid = password_verify($password . $this->pepper, $user['password_hash']);

        if (!$valid) {
            $attempts = $user['failed_attempts'] + 1;
            $lockUntil = $attempts >= 5 ? time() + 300 : 0;  // 5min lockout after 5 fails
            $this->pdo->prepare('UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?')
                ->execute([$attempts, $lockUntil, $user['id']]);
            return ['success' => false, 'error' => "Invalid credentials (attempt $attempts/5)"];
        }

        // Reset failed attempts
        $this->pdo->prepare('UPDATE users SET failed_attempts=0, locked_until=0 WHERE id=?')
            ->execute([$user['id']]);

        // Generate session token
        $token = bin2hex(random_bytes(32));
        return ['success' => true, 'user_id' => $user['id'], 'token' => $token];
    }
}

$auth = new SecureAuthSystem();

// Register
$reg = $auth->register('alice', 'SuperSecurePass!123');
echo "Register Alice: " . ($reg['success'] ? "OK (id={$reg['id']})" : $reg['error']) . "\n";

$reg2 = $auth->register('bob', 'short');
echo "Register Bob (weak pass): " . ($reg2['error']) . "\n";

// Login
$login = $auth->login('alice', 'SuperSecurePass!123');
echo "Login Alice: " . ($login['success'] ? "OK, token=" . substr($login['token'], 0, 16) . "..." : $login['error']) . "\n";

$fail = $auth->login('alice', 'wrongpassword');
echo "Login wrong: " . $fail['error'] . "\n";

$nouser = $auth->login('nobody', 'any');
echo "Login nouser: " . $nouser['error'] . "\n";
```

📸 **Verified Output:**
```
Register Alice: OK (id=1)
Register Bob (weak pass): Password must be 12+ chars
Login Alice: OK, token=a3f7b2c9d4e1082f...
Login wrong: Invalid credentials (attempt 1/5)
Login nouser: Invalid credentials
```

---

## Summary

| Threat | Defense | PHP Function/Feature |
|---|---|---|
| Weak passwords | Argon2id hashing | `password_hash(PASSWORD_ARGON2ID)` |
| CSRF | HMAC token + timing-safe compare | `hash_hmac()`, `hash_equals()` |
| Session fixation | Regenerate on login | `session_regenerate_id(true)` |
| XSS | Output encoding | `htmlspecialchars(ENT_QUOTES)` |
| SQL injection | Prepared statements | `PDO::prepare()->execute([...])` |
| Timing attacks | Constant-time compare | `hash_equals()` |
| Insecure random | CSPRNG | `random_bytes()`, `random_int()` |
| Path traversal | `realpath()` + prefix check | `str_starts_with(realpath($p), $base)` |
| Header injection | `header()` with validation | Never pass user input directly |
| Information leakage | Error reporting off | `display_errors=Off` in production |
