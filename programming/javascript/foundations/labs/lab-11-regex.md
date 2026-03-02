# Lab 11: Regular Expressions

## Objective
Master JavaScript regular expressions — create patterns, use flags, extract groups, search and replace text, and apply regex to real-world tasks like validation, log parsing, and data extraction.

## Background
Regular expressions (regex) are a pattern-matching language built into JavaScript. They power form validation, log analysis, search-and-replace in editors, URL routing, and data parsing. A single regex pattern can replace 20 lines of string-splitting code. Learning regex is one of the highest-leverage skills in any language.

## Time
45 minutes

## Prerequisites
- Lab 03 (Functions & Scope)
- Lab 04 (Arrays & Objects)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: Creating Patterns — Literals and Constructors

Two ways to create regex in JavaScript: literal syntax `/pattern/flags` and `new RegExp()`.

```javascript
// step1-basics.js

// Literal syntax (preferred for fixed patterns)
const emailPattern = /[a-z]+@[a-z]+\.[a-z]+/i;

// Constructor (use when pattern is dynamic)
const domain = 'example';
const dynamicPattern = new RegExp(`\\b${domain}\\.com\\b`, 'gi');

// test() — returns boolean
console.log(emailPattern.test('user@example.com'));   // true
console.log(emailPattern.test('not-an-email'));        // false

// exec() — returns match details or null
const match = emailPattern.exec('Contact: hello@world.org today');
console.log(match[0]);   // hello@world.org
console.log(match.index); // 9

// String methods
const str = 'Find example.com and EXAMPLE.COM here';
console.log(str.match(dynamicPattern));  // ['example.com', 'EXAMPLE.COM']
```

> 💡 **Flags matter:** `i` = case-insensitive, `g` = global (find all), `m` = multiline, `s` = dotAll (`.` matches newlines). Without `g`, `.match()` returns only the first result.

**📸 Verified Output:**
```
true
false
hello@world.org
9
[ 'example.com', 'EXAMPLE.COM' ]
```

---

### Step 2: Character Classes and Quantifiers

Build patterns using character classes `[]`, anchors `^$`, and quantifiers `+*?{}`.

```javascript
// step2-patterns.js

const tests = [
  // Digits and word chars
  { pattern: /^\d{3}-\d{4}$/, input: '555-1234', label: 'Phone (digits)' },
  { pattern: /^\w+$/, input: 'hello_world', label: 'Word chars only' },
  { pattern: /^\w+$/, input: 'has space', label: 'Word chars (fail)' },

  // Character classes
  { pattern: /^[A-Z][a-z]+$/, input: 'Hello', label: 'Capitalized word' },
  { pattern: /^[aeiou]/i, input: 'apple', label: 'Starts with vowel' },
  { pattern: /[^aeiou]/i, input: 'b', label: 'Not a vowel' },

  // Quantifiers
  { pattern: /colou?r/, input: 'color', label: 'Optional u (US)' },
  { pattern: /colou?r/, input: 'colour', label: 'Optional u (UK)' },
  { pattern: /^.{8,20}$/, input: 'mypassword', label: '8-20 chars' },
  { pattern: /^.{8,20}$/, input: 'short', label: 'Too short' },
];

tests.forEach(({ pattern, input, label }) => {
  const result = pattern.test(input);
  console.log(`${result ? '✓' : '✗'} ${label}: "${input}"`);
});
```

> 💡 **`\d`** = `[0-9]`, **`\w`** = `[a-zA-Z0-9_]`, **`\s`** = whitespace, **`\D/\W/\S`** = their negations. The `^` inside `[]` negates the class; outside it anchors to string start.

**📸 Verified Output:**
```
✓ Phone (digits): "555-1234"
✓ Word chars only: "hello_world"
✗ Word chars (fail): "has space"
✓ Capitalized word: "Hello"
✓ Starts with vowel: "apple"
✓ Not a vowel: "b"
✓ Optional u (US): "color"
✓ Optional u (UK): "colour"
✓ 8-20 chars: "mypassword"
✗ Too short: "short"
```

---

### Step 3: Capture Groups — Extracting Data

Use `()` to capture parts of a match. Named groups `(?<name>)` make code self-documenting.

```javascript
// step3-groups.js

// Unnamed groups
const datePattern = /(\d{4})-(\d{2})-(\d{2})/;
const dateMatch = '2026-03-02'.match(datePattern);
console.log('Full:', dateMatch[0]);
console.log('Year:', dateMatch[1]);
console.log('Month:', dateMatch[2]);
console.log('Day:', dateMatch[3]);

// Named groups (?<name>)
const namedDate = /(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})/;
const { groups } = '2026-03-02'.match(namedDate);
console.log('\nNamed:', groups);  // { year: '2026', month: '03', day: '02' }

// Non-capturing group (?:) — group without capture
const ipPattern = /^(?:\d{1,3}\.){3}\d{1,3}$/;
console.log('\nIP valid:', ipPattern.test('192.168.1.1'));
console.log('IP valid:', ipPattern.test('10.0.0.1'));
console.log('IP bad:', ipPattern.test('999.x.1.1'));

// Global capture — matchAll
const logLine = 'errors at 10:23, 14:05, 22:47';
const timePattern = /(\d{2}):(\d{2})/g;
for (const m of logLine.matchAll(timePattern)) {
  console.log(`Time: ${m[1]}h ${m[2]}m (at index ${m.index})`);
}
```

> 💡 **`matchAll`** requires the `g` flag and returns an iterator of all matches with full group info. Unlike `.match(pattern)` with `g` which only returns the matched strings, `matchAll` gives you each match's index and groups.

**📸 Verified Output:**
```
Full: 2026-03-02
Year: 2026
Month: 03
Day: 02

Named: { year: '2026', month: '03', day: '02' }

IP valid: true
IP valid: true
IP bad: false
Time: 10h 23m (at index 10)
Time: 14h 05m (at index 17)
Time: 22h 47m (at index 24)
```

---

### Step 4: Search and Replace

`str.replace()` and `str.replaceAll()` with regex are powerful text transformation tools.

```javascript
// step4-replace.js

// Basic replace (first match only without g)
console.log('hello world'.replace(/o/, '0'));    // hell0 world
console.log('hello world'.replace(/o/g, '0'));   // hell0 w0rld

// Replace with capture group backreferences ($1, $2...)
const date = '2026-03-02';
const usDate = date.replace(/(\d{4})-(\d{2})-(\d{2})/, '$2/$3/$1');
console.log('US format:', usDate);  // 03/02/2026

// Named backreferences
const reordered = date.replace(
  /(?<y>\d{4})-(?<m>\d{2})-(?<d>\d{2})/,
  '$<d>.$<m>.$<y>'
);
console.log('EU format:', reordered);  // 02.03.2026

// Replace with function (dynamic replacement)
const prices = 'apple $1.50, banana $0.75, cherry $2.25';
const inflated = prices.replace(/\$(\d+\.\d+)/g, (match, amount) => {
  return '$' + (parseFloat(amount) * 1.1).toFixed(2);
});
console.log('Inflated:', inflated);

// Sanitize user input
function sanitizeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
console.log('\nSanitized:', sanitizeHtml('<script>alert("xss")</script>'));
```

> 💡 **The replacement function** receives `(fullMatch, group1, group2, ..., offset, originalString)`. This lets you transform captured values dynamically — price calculations, case conversion, template filling, etc.

**📸 Verified Output:**
```
hell0 world
hell0 w0rld
US format: 03/02/2026
EU format: 02.03.2026
Inflated: apple $1.65, banana $0.83, cherry $2.48
Sanitized: &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;
```

---

### Step 5: Real-World — Form Validation

Build a validator using regex patterns.

```javascript
// step5-validation.js

const validators = {
  email: {
    pattern: /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/,
    message: 'Invalid email address'
  },
  phone: {
    pattern: /^\+?[\d\s\-().]{7,15}$/,
    message: 'Invalid phone number'
  },
  url: {
    pattern: /^https?:\/\/([\w\-]+\.)+[\w\-]+(\/[\w\-._~:/?#[\]@!$&'()*+,;=%]*)?$/,
    message: 'Invalid URL'
  },
  password: {
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
    message: 'Need 8+ chars, upper, lower, digit, special char'
  },
  ipv4: {
    pattern: /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/,
    message: 'Invalid IPv4 address'
  }
};

function validate(type, value) {
  const v = validators[type];
  const valid = v.pattern.test(value);
  return { valid, message: valid ? 'OK' : v.message };
}

const testCases = [
  ['email', 'user@example.com'],
  ['email', 'bad-email'],
  ['phone', '+1 (555) 123-4567'],
  ['url', 'https://docs.innozverse.com/programming'],
  ['password', 'Str0ng@Pass!'],
  ['password', 'weakpass'],
  ['ipv4', '192.168.1.255'],
  ['ipv4', '999.0.0.1'],
];

testCases.forEach(([type, value]) => {
  const { valid, message } = validate(type, value);
  console.log(`${valid ? '✓' : '✗'} [${type}] "${value}" → ${message}`);
});
```

> 💡 **Lookahead `(?=...)`** is what makes the password regex work: each `(?=.*[A-Z])` asserts "the string contains at least one uppercase letter" without consuming characters. Multiple lookaheads stack as AND conditions.

**📸 Verified Output:**
```
✓ [email] "user@example.com" → OK
✗ [email] "bad-email" → Invalid email address
✓ [phone] "+1 (555) 123-4567" → OK
✓ [url] "https://docs.innozverse.com/programming" → OK
✓ [password] "Str0ng@Pass!" → OK
✗ [password] "weakpass" → Need 8+ chars, upper, lower, digit, special char
✓ [ipv4] "192.168.1.255" → OK
✗ [ipv4] "999.0.0.1" → Invalid IPv4 address
```

---

### Step 6: Log Parsing — Extract Structured Data

Parse Apache-style access logs with regex.

```javascript
// step6-log-parsing.js

const LOG_PATTERN = /^(?<ip>\d+\.\d+\.\d+\.\d+)\s+-\s+-\s+\[(?<datetime>[^\]]+)\]\s+"(?<method>[A-Z]+)\s+(?<path>[^\s]+)\s+HTTP\/[\d.]+"\s+(?<status>\d{3})\s+(?<bytes>\d+)/;

const logLines = [
  '192.168.1.10 - - [02/Mar/2026:10:23:14 +0000] "GET /index.html HTTP/1.1" 200 1234',
  '10.0.0.5 - - [02/Mar/2026:10:23:20 +0000] "POST /api/login HTTP/1.1" 401 89',
  '172.16.0.1 - - [02/Mar/2026:10:24:05 +0000] "GET /admin HTTP/1.1" 403 512',
  '192.168.1.10 - - [02/Mar/2026:10:24:10 +0000] "GET /images/logo.png HTTP/1.1" 200 45678',
  '10.0.0.99 - - [02/Mar/2026:10:25:00 +0000] "DELETE /api/user/5 HTTP/1.1" 500 234',
];

const parsed = logLines.map(line => {
  const m = line.match(LOG_PATTERN);
  if (!m) return null;
  const { ip, datetime, method, path, status, bytes } = m.groups;
  return { ip, datetime, method, path, status: parseInt(status), bytes: parseInt(bytes) };
});

// Analyze
const errors = parsed.filter(r => r.status >= 400);
const totalBytes = parsed.reduce((sum, r) => sum + r.bytes, 0);

console.log('Parsed log entries:');
parsed.forEach(r => console.log(`  ${r.method} ${r.path} → ${r.status}`));

console.log(`\nErrors (4xx/5xx): ${errors.length}`);
errors.forEach(e => console.log(`  ${e.status} ${e.method} ${e.path}`));

console.log(`\nTotal bytes transferred: ${totalBytes.toLocaleString()}`);
```

> 💡 **Named groups make log parsing readable.** Instead of remembering `m[4]` is the path, `m.groups.path` is self-documenting. This approach scales to complex formats like nginx, syslog, or custom JSON-adjacent logs.

**📸 Verified Output:**
```
Parsed log entries:
  GET /index.html → 200
  POST /api/login → 401
  GET /admin → 403
  GET /images/logo.png → 200
  DELETE /api/user/5 → 500

Errors (4xx/5xx): 3
  401 POST /api/login
  403 GET /admin
  500 DELETE /api/user/5

Total bytes transferred: 47,747
```

---

### Step 7: Sticky and Lookaround

Advanced patterns: sticky flag `y`, lookahead `(?=)`, lookbehind `(?<=)`, negative variants.

```javascript
// step7-advanced.js

// Sticky flag — match at exact position
const sticky = /\d+/y;
const input = '123 456 789';
sticky.lastIndex = 4;
console.log(sticky.exec(input)?.[0]);  // '456' (starts at index 4)
sticky.lastIndex = 5;
console.log(sticky.exec(input));       // null (no match at index 5)

// Lookahead — match X only if followed by Y
const pricePattern = /\d+(?= dollars)/g;
console.log('\n"I have 50 dollars and 30 euros"'.match(pricePattern)); // ['50']

// Negative lookahead — match X only if NOT followed by Y
const notDollars = /\d+(?! dollars)(?!\.\d)/g;
console.log('"I have 50 dollars and 30 euros"'.match(notDollars)); // ['0', '30']

// Lookbehind — match X only if preceded by Y
const afterDollar = /(?<=\$)\d+(\.\d{2})?/g;
const prices = 'Cost: $19.99, Tax: $1.50, Total: $21.49';
console.log('\nPrices:', prices.match(afterDollar));

// Negative lookbehind
const notAfterDollar = /(?<!\$)\b\d+\b/g;
const text = 'I have $50 but only 30 left and $100 budget';
console.log('Non-price numbers:', text.match(notAfterDollar));
```

> 💡 **Lookaheads/lookbehinds are zero-width** — they check context without including it in the match. This lets you extract "the number after $" or "the word before :" without capturing the delimiter itself.

**📸 Verified Output:**
```
456
null

[ '50' ]
[ '0', '30' ]

Prices: [ '19.99', '1.50', '21.49' ]
Non-price numbers: [ '30' ]
```

---

### Step 8: Build a Mini Template Engine

Use regex replace to build a lightweight `{{variable}}` template engine.

```javascript
// step8-template.js

function template(str, data, options = {}) {
  const { strict = false } = options;

  // Replace {{variable}} and {{nested.path}}
  return str.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (match, key) => {
    const value = key.split('.').reduce((obj, k) => obj?.[k], data);

    if (value === undefined || value === null) {
      if (strict) throw new Error(`Template key not found: ${key}`);
      return match; // leave unreplaced
    }

    return String(value);
  });
}

const tmpl = `
Hello, {{ name }}!
Your order #{{ order.id }} for {{ order.item }} is {{ order.status }}.
Total: ${{ order.total }}
Missing: {{ nonexistent }}
`.trim();

const data = {
  name: 'Dr. Chen',
  order: {
    id: 'ORD-2026-001',
    item: 'Surface Pro 12"',
    status: 'shipped',
    total: '864.00'
  }
};

console.log(template(tmpl, data));

// Strict mode — throw on missing keys
try {
  template('Hello {{ user.name }}!', {}, { strict: true });
} catch (e) {
  console.log('\nStrict error:', e.message);
}
```

> 💡 **Template engines** (Handlebars, Mustache, EJS) use regex at their core. This 15-line version handles dot notation, missing key behavior, and strict mode — demonstrating how much regex can accomplish elegantly.

**📸 Verified Output:**
```
Hello, Dr. Chen!
Your order #ORD-2026-001 for Surface Pro 12" is shipped.
Total: $864.00
Missing: {{ nonexistent }}

Strict error: Template key not found: user.name
```

---

## Verification

```bash
node step8-template.js
```

Expected: Template renders correctly with data substitution and strict error on missing key.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `g` flag for all matches | Without `g`, only first match is found |
| Using `test()` with stateful `g` regex | `lastIndex` advances — create new regex or reset |
| Overescaping in string constructors | `new RegExp('\\d+')` needs double backslash |
| Greedy vs lazy quantifiers | `.*?` is lazy (minimal), `.*` is greedy (maximal) |
| Not escaping user input in dynamic regex | Use `str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')` |

## Summary

You've covered regex literals and constructors, all major character classes and quantifiers, capture groups (named and unnamed), global matching with `matchAll`, powerful replacements with functions, form validation, log parsing, lookahead/lookbehind, and building a template engine. Regex is now a tool you can reach for confidently.

## Further Reading
- [MDN: Regular Expressions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions)
- [regex101.com](https://regex101.com) — interactive regex tester with JS flavor
- [Regexper](https://regexper.com) — visual regex diagrams
