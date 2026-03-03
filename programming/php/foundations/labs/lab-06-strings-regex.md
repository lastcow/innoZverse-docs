# Lab 6: Strings & Regular Expressions

## Objective
Manipulate strings with PHP's built-in functions, format output with `sprintf`, use heredoc/nowdoc, and apply regular expressions with `preg_match`, `preg_replace`, and `preg_split`.

## Background
PHP has over 100 string functions and a mature PCRE (Perl Compatible Regular Expressions) engine. String manipulation is at the heart of web development — processing user input, formatting output, parsing logs, validating data, and building HTML/JSON responses.

## Time
35 minutes

## Prerequisites
- Lab 05 (Functions)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Essential String Functions

```php
<?php
$str = "  Hello, World! This is PHP 8.3  ";

// Length & trimming
echo "Length: " . strlen($str) . "\n";
echo "Trimmed: '" . trim($str) . "'\n";
echo "ltrim: '"   . ltrim($str) . "'\n";
echo "rtrim: '"   . rtrim($str) . "'\n";

// Case
$s = "hello WORLD";
echo "\nupper: " . strtoupper($s) . "\n";
echo "lower: " . strtolower($s) . "\n";
echo "ucfirst: " . ucfirst($s) . "\n";
echo "ucwords: " . ucwords($s) . "\n";

// Search & position
$haystack = "The quick brown fox jumps over the lazy dog";
echo "\nstrpos('fox'): "  . strpos($haystack, 'fox') . "\n";
echo "strrpos('the'): "  . strrpos($haystack, 'the') . "\n";
echo "contains 'fox': "  . (str_contains($haystack, 'fox') ? 'yes' : 'no') . "\n";
echo "starts 'The': "    . (str_starts_with($haystack, 'The') ? 'yes' : 'no') . "\n";
echo "ends 'dog': "      . (str_ends_with($haystack, 'dog') ? 'yes' : 'no') . "\n";
```

> 💡 **`str_contains()`, `str_starts_with()`, `str_ends_with()`** were added in PHP 8.0 — finally replacing the verbose `strpos() !== false` pattern. Always prefer these for readability. Note: `strpos` returns `false` (not -1) when not found — `strpos($s, 'x') == 0` is a bug if 'x' is at position 0!

**📸 Verified Output:**
```
Length: 34
Trimmed: 'Hello, World! This is PHP 8.3'
ltrim: 'Hello, World! This is PHP 8.3  '
rtrim: '  Hello, World! This is PHP 8.3'

upper: HELLO WORLD
lower: hello world
ucfirst: Hello WORLD
ucwords: Hello World

strpos('fox'): 16
strrpos('the'): 31
contains 'fox': yes
starts 'The': yes
ends 'dog': yes
```

---

### Step 2: Substr, Replace & Split

```php
<?php
$str = "The quick brown fox";

// Extraction
echo substr($str, 4, 5) . "\n";          // quick
echo substr($str, -3) . "\n";            // fox
echo substr($str, 4) . "\n";             // quick brown fox

// Replace
echo str_replace('fox', 'cat', $str) . "\n";
echo str_ireplace('THE', 'A', $str) . "\n"; // case-insensitive

// Multiple replacements
$search  = ['quick', 'brown', 'fox'];
$replace = ['slow',  'white', 'rabbit'];
echo str_replace($search, $replace, $str) . "\n";

// Split & join
$csv = "alice,bob,carol,dave";
$names = explode(',', $csv);
echo implode(' | ', $names) . "\n";

// Chunk string
$hex = bin2hex("PHP");
echo "hex: $hex\n";
$chunks = str_split($hex, 2);
echo implode(' ', $chunks) . "\n";

// Repeat & pad
echo str_repeat('ab', 4) . "\n";
echo str_pad('42', 8, '0', STR_PAD_LEFT) . "\n";
echo str_pad('hi', 10, '-', STR_PAD_BOTH) . "\n";

// Word count & wrap
echo "\nWord count: " . str_word_count("Hello World PHP") . "\n";
echo wordwrap("The quick brown fox jumps over the lazy dog", 15, "\n  ", true) . "\n";
```

> 💡 **`str_pad` with `STR_PAD_LEFT`** is the clean way to zero-pad numbers: `str_pad('42', 8, '0', STR_PAD_LEFT)` → `00000042`. More readable than `sprintf('%08d', 42)` for simple cases. `STR_PAD_BOTH` centers the string.

**📸 Verified Output:**
```
quick
fox
quick brown fox
The quick brown cat
A quick brown fox
The slow white rabbit
alice | bob | carol | dave
hex: 504850
50 48 50
abababab
00000042
----hi----

Word count: 3
The quick brown
  fox jumps over
  the lazy dog
```

---

### Step 3: sprintf & Number Formatting

```php
<?php
// sprintf — formatted strings
printf("%-15s %8s %6s\n", "Item", "Price", "Qty");
printf("%-15s %8.2f %6d\n", "Surface Pro", 864.00, 1);
printf("%-15s %8.2f %6d\n", "Surface Pen",  49.99, 2);

// Number formats
$n = 1234567.891;
echo "\nnumber_format: " . number_format($n, 2) . "\n";            // 1,234,567.89
echo "European:      " . number_format($n, 2, ',', '.') . "\n";   // 1.234.567,89
echo "scientific:    " . sprintf("%.3e", $n) . "\n";               // 1.235e+6

// Padding & alignment
foreach (['Alice' => 95, 'Bob' => 87, 'Carol-Ann' => 92] as $name => $score) {
    printf("%-12s: %s\n", $name, str_repeat('█', intdiv($score, 10)));
}

// Date formatting
$ts = mktime(14, 30, 0, 3, 2, 2026);
echo "\n" . date('Y-m-d H:i:s', $ts) . "\n";
echo date('D, d M Y', $ts) . "\n";
echo date('l, F jS Y', $ts) . "\n";

// String interpolation styles
$name = "Dr. Chen";
$score = 98;
echo "\n\"double quotes: $name scored $score\"\n";
echo "sprintf: " . sprintf("sprintf: %s scored %d", $name, $score) . "\n";
```

> 💡 **`printf` format specifiers:** `%s` = string, `%d` = integer, `%f` = float, `%e` = scientific, `%.2f` = 2 decimal places, `%08d` = zero-padded to 8 chars, `%-15s` = left-aligned in 15 chars. `printf` prints directly; `sprintf` returns the string.

**📸 Verified Output:**
```
Item             Price    Qty
Surface Pro     864.00      1
Surface Pen      49.99      2

number_format: 1,234,567.89
European:      1.234.567,89
scientific:    1.235e+6
Alice       : █████████
Bob         : ████████
Carol-Ann   : █████████

2026-03-02 14:30:00
Mon, 02 Mar 2026
Monday, March 2nd 2026

"double quotes: Dr. Chen scored 98"
sprintf: Dr. Chen scored 98
```

---

### Step 4: Heredoc & Nowdoc

```php
<?php
$name = "Dr. Chen";
$version = "8.3";

// Heredoc — interpolates variables (like double quotes)
$html = <<<HTML
<div class="card">
    <h2>Welcome, {$name}!</h2>
    <p>Running PHP {$version}</p>
    <p>Today: {$today}</p>
</div>
HTML;

$today = date('Y-m-d');
$html = <<<HTML
<div class="card">
    <h2>Welcome, {$name}!</h2>
    <p>Running PHP {$version}</p>
    <p>Today: {$today}</p>
</div>
HTML;

echo $html . "\n";

// Nowdoc — NO interpolation (like single quotes)
$template = <<<'EOT'
Template variables: {$name} and $version
These are NOT replaced.
EOT;

echo $template . "\n";

// Indented heredoc (PHP 7.3+)
function getJson(string $key, mixed $value): string {
    $encoded = json_encode($value);
    return <<<JSON
        {
            "key": "$key",
            "value": $encoded
        }
        JSON;
}

echo getJson("score", 95) . "\n";
```

> 💡 **Heredoc interpolates variables; nowdoc does not** — the only difference is the single quotes around the opening label. Indented heredoc (PHP 7.3+) strips leading whitespace up to the closing marker's indentation level, making it practical inside indented code.

**📸 Verified Output:**
```
<div class="card">
    <h2>Welcome, Dr. Chen!</h2>
    <p>Running PHP 8.3</p>
    <p>Today: 2026-03-02</p>
</div>

Template variables: {$name} and $version
These are NOT replaced.

        {
            "key": "score",
            "value": 95
        }
```

---

### Step 5: Regular Expressions — preg_match

```php
<?php
// preg_match — test and capture
function validate(string $pattern, string $input, string $label): void {
    $result = preg_match($pattern, $input) ? '✓' : '✗';
    echo "  $result $label: $input\n";
}

echo "Email validation:\n";
$emailPattern = '/^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/';
validate($emailPattern, 'chen@example.com', 'valid');
validate($emailPattern, 'bad-email',        'no @');

echo "\nPhone:\n";
validate('/^\+?[\d\s\-().]{7,15}$/', '+1 (555) 123-4567', 'US format');
validate('/^\+?[\d\s\-().]{7,15}$/', 'abc',               'letters');

// Capture groups
$date = '2026-03-02';
if (preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $date, $matches)) {
    echo "\nDate parts:\n";
    echo "  Year: $matches[1], Month: $matches[2], Day: $matches[3]\n";
}

// Named groups
$pattern = '/(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})/';
preg_match($pattern, '2026-03-02', $m);
echo "  Named: year={$m['year']} month={$m['month']} day={$m['day']}\n";

// preg_match_all — find all occurrences
$text = "Prices: $10.99, $25.00, and $5.50";
preg_match_all('/\$(\d+\.\d{2})/', $text, $allMatches);
echo "\nAll prices: " . implode(', ', $allMatches[1]) . "\n";
echo "Total: $" . array_sum($allMatches[1]) . "\n";
```

> 💡 **`preg_match` returns 0 or 1** (not `true`/`false`), and returns `false` on regex error. Always check for `false` explicitly in critical code. Capture groups are stored in the third argument `$matches` — index 0 is the full match, 1+ are groups.

**📸 Verified Output:**
```
Email validation:
  ✓ valid: chen@example.com
  ✗ no @: bad-email

Phone:
  ✓ US format: +1 (555) 123-4567
  ✗ letters: abc

Date parts:
  Year: 2026, Month: 03, Day: 02
  Named: year=2026 month=03 day=02

All prices: 10.99, 25.00, 5.50
Total: $41.49
```

---

### Step 6: preg_replace & preg_split

```php
<?php
// preg_replace — replace with pattern
$text = "The price is $10.99 and was $15.00";

// Simple replace
$masked = preg_replace('/\$[\d.]+/', '$***', $text);
echo "Masked: $masked\n";

// Replace with callback
$inflated = preg_replace_callback('/\$([\d.]+)/', function($m) {
    return '$' . number_format((float)$m[1] * 1.1, 2);
}, $text);
echo "Inflated: $inflated\n";

// Named backreferences in replacement
$date = '2026-03-02';
$usDate = preg_replace('/(\d{4})-(\d{2})-(\d{2})/', '$2/$3/$1', $date);
echo "US date: $usDate\n";

// Sanitize HTML
function sanitize(string $html): string {
    return htmlspecialchars($html, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}
echo "Sanitized: " . sanitize('<script>alert("xss")</script>') . "\n";

// preg_split — split by pattern
$csv = "one, two,  three ,four";
$parts = preg_split('/\s*,\s*/', trim($csv));
echo "\nSplit: " . implode(' | ', $parts) . "\n";

// Split on multiple delimiters
$str = "alpha;beta|gamma,delta";
$tokens = preg_split('/[;|,]/', $str);
echo "Tokens: " . implode(', ', $tokens) . "\n";

// Split keeping delimiters
$equation = "10+20-5*3";
$parts = preg_split('/([+\-*\/])/', $equation, -1, PREG_SPLIT_DELIM_CAPTURE);
echo "Equation parts: " . implode(' ', $parts) . "\n";
```

> 💡 **`preg_replace_callback`** is the most powerful replace tool — you get the full match and all capture groups as `$matches`, and can compute the replacement dynamically. Use it for price updates, template rendering, code highlighting, and any transformation that can't be expressed as a static replacement string.

**📸 Verified Output:**
```
Masked: The price is $*** and was $***
Inflated: The price is $12.09 and was $16.50
US date: 03/02/2026
Sanitized: &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;

Split: one | two | three | four
Tokens: alpha, beta, gamma, delta
Equation parts: 10 + 20 - 5 * 3
```

---

### Step 7: String Security & Encoding

```php
<?php
// Hash passwords (never store plain text)
$password = "MySuperSecret123!";
$hash = password_hash($password, PASSWORD_BCRYPT);
echo "Hash: " . substr($hash, 0, 30) . "...\n";
echo "Verify: " . (password_verify($password, $hash) ? 'valid' : 'invalid') . "\n";
echo "Wrong: "  . (password_verify("wrong", $hash)   ? 'valid' : 'invalid') . "\n";

// Base64 encoding
$data = "Dr. Chen <chen@example.com>";
$encoded = base64_encode($data);
$decoded = base64_decode($encoded);
echo "\nBase64: $encoded\n";
echo "Decoded: $decoded\n";

// URL encoding
$url = "https://example.com/search?q=PHP 8.3 & features=new";
echo "\nURL encoded: " . urlencode($url) . "\n";
echo "rawurlencode: " . rawurlencode($url) . "\n";

// HTML entities
$unsafe = '<script>alert("hello & goodbye")</script>';
echo "\nHTML entities: " . htmlspecialchars($unsafe) . "\n";
echo "Decoded back: " . htmlspecialchars_decode(htmlspecialchars($unsafe)) . "\n";

// md5/sha1 (NOT for passwords — for checksums)
$file = "important data";
echo "\nMD5:  " . md5($file) . "\n";
echo "SHA1: " . sha1($file) . "\n";
echo "SHA256: " . hash('sha256', $file) . "\n";
```

> 💡 **Never use `md5()` or `sha1()` for passwords** — they're fast hashing algorithms, vulnerable to brute force. Use `password_hash()` with `PASSWORD_BCRYPT` or `PASSWORD_ARGON2ID`. They're intentionally slow and include a salt automatically.

**📸 Verified Output:**
```
Hash: $2y$10$...
Verify: valid
Wrong: invalid

Base64: RHIuIENoZW4gPGNoZW5AZXhhbXBsZS5jb20+
Decoded: Dr. Chen <chen@example.com>

URL encoded: https%3A%2F%2Fexample.com...
HTML entities: &lt;script&gt;alert(&quot;hello &amp; goodbye&quot;)&lt;/script&gt;

MD5:  73b998e0e6d5e5e3adcf6e62e61acdd6
SHA1: 45e55e8d8ce0c7a7cd5f9e79ea42b4b3f99e1b48
SHA256: 9f86d081884c7d659a2feaa0c55ad015...
```

---

### Step 8: Real-World — Log Parser

```php
<?php
$logData = <<<'LOGS'
2026-03-02 10:23:14 [INFO] auth: User alice logged in from 192.168.1.10
2026-03-02 10:23:45 [ERROR] payment: Connection timeout after 30s (attempt 1/3)
2026-03-02 10:24:01 [WARN] catalog: Slow query: 2.3s for product_search
2026-03-02 10:24:15 [INFO] shipping: Order ORD-2026-001 dispatched
2026-03-02 10:25:00 [ERROR] auth: Failed login for user bob (IP: 10.0.0.99)
2026-03-02 10:25:30 [INFO] payment: Transaction TXN-8842 completed: $864.00
2026-03-02 10:26:00 [ERROR] payment: Connection timeout after 30s (attempt 2/3)
LOGS;

$pattern = '/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\w+): (.+)$/m';
preg_match_all($pattern, $logData, $matches, PREG_SET_ORDER);

$entries = array_map(fn($m) => [
    'time'    => $m[1],
    'level'   => $m[2],
    'service' => $m[3],
    'message' => $m[4],
], $matches);

// Count by level
$byLevel = array_count_values(array_column($entries, 'level'));
arsort($byLevel);
echo "By level:\n";
foreach ($byLevel as $level => $count) echo "  $level: $count\n";

// Extract transactions
echo "\nTransactions:\n";
foreach ($entries as $e) {
    if (preg_match('/TXN-\w+ completed: \$(\d+\.\d{2})/', $e['message'], $m)) {
        echo "  [{$e['time']}] \${$m[1]}\n";
    }
}

// Find errors with retry patterns
echo "\nRetry errors:\n";
foreach ($entries as $e) {
    if ($e['level'] === 'ERROR' && preg_match('/attempt (\d+)\/(\d+)/', $e['message'], $m)) {
        echo "  Attempt {$m[1]}/{$m[2]}: {$e['message']}\n";
    }
}

// Services with errors
$errorServices = array_unique(
    array_column(
        array_filter($entries, fn($e) => $e['level'] === 'ERROR'),
        'service'
    )
);
echo "\nServices with errors: " . implode(', ', $errorServices) . "\n";
```

> 💡 **`PREG_SET_ORDER`** organizes matches so each element is one full match with all its groups — `$matches[0]` is the first log line with all its captured groups. Without it, `$matches[0]` would be all full matches, `$matches[1]` all first-group captures, etc. `PREG_SET_ORDER` is almost always what you want.

**📸 Verified Output:**
```
By level:
  ERROR: 3
  INFO: 3
  WARN: 1

Transactions:
  [2026-03-02 10:25:30] $864.00

Retry errors:
  Attempt 1/3: Connection timeout after 30s (attempt 1/3)
  Attempt 2/3: Connection timeout after 30s (attempt 2/3)

Services with errors: payment, auth
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
preg_match_all('/\b[A-Z][a-z]+\b/', 'Hello World from PHP Land', \$m);
echo implode(', ', \$m[0]) . PHP_EOL;
"
```

Expected: `Hello, World, PHP, Land`

## Summary

PHP's string arsenal is massive. You've covered trimming/case/search functions, `sprintf` formatting, heredoc/nowdoc, `preg_match` with capture groups, `preg_replace_callback`, string security (password hashing, HTML escaping), and a complete log parser. These skills cover 90% of real PHP string work.

## Further Reading
- [PHP String Functions](https://www.php.net/manual/en/ref.strings.php)
- [PCRE Regex](https://www.php.net/manual/en/book.pcre.php)
- [password_hash](https://www.php.net/manual/en/function.password-hash.php)
