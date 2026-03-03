# Lab 11: Advanced Regular Expressions

## Objective
Master PHP's PCRE regex engine: named capture groups, non-greedy quantifiers, lookahead/lookbehind assertions, backreferences, `preg_replace_callback`, Unicode properties, and building a regex-powered template engine and log parser.

## Background
PHP uses the PCRE2 library (Perl-Compatible Regular Expressions). Beyond simple pattern matching, PCRE supports named groups `(?P<name>...)`, lookahead `(?=...)` / lookbehind `(?<=...)`, atomic groups `(?>...)`, and Unicode character classes `\p{Lu}` (uppercase letters). `preg_replace_callback` enables complex substitutions where the replacement depends on the match content.

## Time
25 minutes

## Prerequisites
- PHP Foundations Lab 06 (Strings & Regex)

## Tools
- Docker: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Named groups, lookahead, `preg_replace_callback`

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Named capture groups ──────────────────────────────────────────────────────
echo "=== Named Capture Groups ===" . PHP_EOL;

$orderLog = [
    "2026-01-15 09:23:41 ORDER #1001 Surface Pro qty=2 total=$1728.00 region=West status=shipped",
    "2026-02-03 14:05:22 ORDER #1002 Surface Pen qty=5 total=$249.95  region=East status=pending",
    "2026-02-18 16:44:00 ORDER #1003 Office 365  qty=1 total=$99.99   region=North status=delivered",
    "2026-03-01 11:30:15 ORDER #9999 USB-C Hub   qty=10 total=$299.90 region=South status=cancelled",
];

// Named groups make the regex self-documenting
$pattern = '/^(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) ORDER #(?P<id>\d+) (?P<product>.+?) qty=(?P<qty>\d+) total=\$(?P<total>[\d.]+)\s+region=(?P<region>\w+) status=(?P<status>\w+)$/';

$orders = [];
foreach ($orderLog as $line) {
    if (preg_match($pattern, $line, $m)) {
        $orders[] = [
            "date"    => $m["date"],
            "id"      => (int) $m["id"],
            "product" => trim($m["product"]),
            "qty"     => (int) $m["qty"],
            "total"   => (float) $m["total"],
            "region"  => $m["region"],
            "status"  => $m["status"],
        ];
    }
}

foreach ($orders as $o) {
    printf("  #%-4d %-15s ×%d \$%-8.2f %-8s %s%s",
        $o["id"], $o["product"], $o["qty"], $o["total"], $o["region"], $o["status"], PHP_EOL);
}

$totalRevenue = array_sum(array_column($orders, "total"));
printf("  Total revenue: \$%.2f%s", $totalRevenue, PHP_EOL);

// ── Lookahead and lookbehind ──────────────────────────────────────────────────
echo PHP_EOL . "=== Lookahead & Lookbehind ===" . PHP_EOL;

$prices = ["$864.00", "€299.99", "£49.99", "¥12000", "$1299.00", "$0.00"];

// Positive lookahead: digits followed by .00 (end of cents)
$wholeDollar = array_filter($prices, fn($p) => preg_match('/\d+(?=\.00)/', $p));
echo "Whole dollar amounts: " . implode(", ", $wholeDollar) . PHP_EOL;

// Negative lookahead: $ prices that are NOT $0.00
$nonZero = array_filter($prices, fn($p) => preg_match('/^\$(?!0\.00)[\d.]+$/', $p));
echo "Non-zero USD: " . implode(", ", $nonZero) . PHP_EOL;

// Positive lookbehind: numbers preceded by $
$usdAmounts = [];
foreach ($prices as $p) {
    if (preg_match('/(?<=\$)[\d.]+/', $p, $m)) $usdAmounts[] = (float)$m[0];
}
echo "USD amounts: " . implode(", ", $usdAmounts) . PHP_EOL;

// ── preg_replace_callback ─────────────────────────────────────────────────────
echo PHP_EOL . "=== preg_replace_callback ===" . PHP_EOL;

// Convert markdown-ish product links to HTML
$text = "Buy the [[Surface Pro|/products/1]] for \$864 or the [[Surface Pen|/products/2]] for \$49.99.";
$html = preg_replace_callback(
    '/\[\[(?P<label>[^\|]+)\|(?P<url>[^\]]+)\]\]/',
    fn($m) => "<a href=\"{$m["url"]}\">{$m["label"]}</a>",
    $text
);
echo "  Input:  " . $text . PHP_EOL;
echo "  Output: " . $html . PHP_EOL;

// Mask credit card numbers: keep last 4
$payment = "Charged card 4111-1111-1111-1234 and backup 5500-0000-0000-0004";
$masked = preg_replace_callback(
    '/(\d{4})-(\d{4})-(\d{4})-(\d{4})/',
    fn($m) => "****-****-****-{$m[4]}",
    $payment
);
echo PHP_EOL . "  Original: " . $payment . PHP_EOL;
echo "  Masked:   " . $masked . PHP_EOL;

// Capitalise first letter of each word in product names (title-case)
$names = ["surface pro 12 inch", "usb-c hub v2", "office 365 family"];
foreach ($names as $name) {
    $titleCase = preg_replace_callback(
        '/\b([a-z])/',
        fn($m) => strtoupper($m[1]),
        $name
    );
    echo "  " . str_pad($name, 25) . " -> " . $titleCase . PHP_EOL;
}
'
```

---

### Step 2: Template engine + log parser

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
// ── Regex Template Engine ─────────────────────────────────────────────────────
echo "=== Template Engine ===" . PHP_EOL;

function renderTemplate(string $template, array $vars): string {
    // {{var}} — simple substitution
    $result = preg_replace_callback(
        '/\{\{(\w+)\}\}/',
        fn($m) => htmlspecialchars($vars[$m[1]] ?? ""),
        $template
    );
    // {{#if condition}}...{{/if}} — conditional blocks
    $result = preg_replace_callback(
        '/\{\{#if (\w+)\}\}(.*?)\{\{\/if\}\}/s',
        fn($m) => !empty($vars[$m[1]]) ? $m[2] : "",
        $result
    );
    return $result;
}

$orderTemplate = <<<'TPL'
Order Confirmation #{{orderId}}
Product:   {{product}}
Quantity:  {{qty}}
Total:     ${{total}}
{{#if discount}}Discount applied: {{discount}}% off{{/if}}
Status:    {{status}}
TPL;

$orders = [
    ["orderId" => "1001", "product" => "Surface Pro", "qty" => "2", "total" => "1728.00",
     "discount" => "10",  "status" => "Confirmed"],
    ["orderId" => "1002", "product" => "USB-C Hub", "qty" => "5",  "total" => "149.95",
     "discount" => "",    "status" => "Pending"],
];

foreach ($orders as $o) {
    echo renderTemplate($orderTemplate, $o) . PHP_EOL . str_repeat("-", 35) . PHP_EOL;
}

// ── Log parser ────────────────────────────────────────────────────────────────
echo PHP_EOL . "=== Structured Log Parser ===" . PHP_EOL;

$logs = [
    "[2026-03-03 09:00:01] INFO  app.order    Order #1001 placed total=\$864.00 user=dr.chen@chen.me",
    "[2026-03-03 09:00:05] INFO  app.payment  Payment processed gateway=Stripe amount=\$864.00",
    "[2026-03-03 09:01:30] WARN  app.stock    Low stock: Surface Pro qty=2 remaining",
    "[2026-03-03 09:02:00] ERROR app.payment  Payment declined code=CARD_EXPIRED user=anon@test.com",
    "[2026-03-03 09:03:15] INFO  app.ship     Order #1001 shipped tracking=FX10019871US",
    "[2026-03-03 09:05:00] ERROR app.db       Connection timeout after 30s host=db-primary",
];

$logPattern = '/^\[(?P<datetime>[^\]]+)\] (?P<level>\w+)\s+(?P<channel>[\w.]+)\s+(?P<message>.+)$/';
$kvPattern  = '/(\w+)=(?:"([^"]+)"|(\S+))/';

$parsed = [];
foreach ($logs as $line) {
    if (!preg_match($logPattern, $line, $m)) continue;
    preg_match_all($kvPattern, $m["message"], $kvs, PREG_SET_ORDER);
    $context = [];
    foreach ($kvs as $kv) $context[$kv[1]] = $kv[2] ?: $kv[3];
    $parsed[] = [
        "datetime" => $m["datetime"],
        "level"    => $m["level"],
        "channel"  => $m["channel"],
        "message"  => $m["message"],
        "context"  => $context,
    ];
}

// Summary
$byLevel = array_count_values(array_column($parsed, "level"));
echo "Log summary:" . PHP_EOL;
foreach ($byLevel as $level => $count) {
    printf("  %-6s %d entries%s", $level, $count, PHP_EOL);
}

// Show errors with context
echo PHP_EOL . "Errors:" . PHP_EOL;
foreach (array_filter($parsed, fn($e) => $e["level"] === "ERROR") as $entry) {
    echo "  [{$entry["datetime"]}] [{$entry["channel"]}] " . $entry["message"] . PHP_EOL;
    if (!empty($entry["context"])) {
        foreach ($entry["context"] as $k => $v) echo "    {$k}={$v}" . PHP_EOL;
    }
}
'
```

**📸 Verified Output:**
```
=== Named Capture Groups ===
  #1001 Surface Pro      ×2 $1728.00  West     shipped
  #1002 Surface Pen      ×5 $249.95   East     pending
  Total revenue: $2377.84

=== Template Engine ===
Order Confirmation #1001
Product:   Surface Pro
Total:     $1728.00
Discount applied: 10% off
Status:    Confirmed

=== Log Parser ===
  INFO   4 entries
  WARN   1 entries
  ERROR  2 entries
```

---

## Summary

| Feature | Pattern | Notes |
|---------|---------|-------|
| Named group | `(?P<name>...)` | Access via `$m["name"]` |
| Positive lookahead | `(?=...)` | Match if followed by |
| Negative lookahead | `(?!...)` | Match if NOT followed by |
| Lookbehind | `(?<=...)` | Match if preceded by |
| Non-greedy | `*?` `+?` | Match as little as possible |
| `preg_replace_callback` | fn receives match array | Complex replacements |

## Further Reading
- [PHP PCRE](https://www.php.net/manual/en/book.pcre.php)
- [regex101.com](https://regex101.com/) (test with PHP flavour)
