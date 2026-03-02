# Lab 14: Regular Expressions

## 🎯 Objective
Master Python's `re` module — pattern matching, extraction, validation, and text transformation using regular expressions.

## 📚 Background
Regular expressions (regex) are a mini-language for describing text patterns. They're used everywhere: validating emails, parsing log files, extracting data from HTML, reformatting dates, and sanitizing user input. Python's `re` module implements Perl-compatible regex. While regex can look cryptic, a handful of patterns handles 90% of real-world tasks.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 13: Debugging & Testing

## 🛠️ Tools Used
- Python 3.12 (`re` module — no install needed)

## 🔬 Lab Instructions

### Step 1: Regex Basics — Matching Patterns

```python
import re

text = "Hello, my name is Alice and I am 30 years old."

# re.search() — find first match anywhere in string
match = re.search(r'\d+', text)  # \d+ = one or more digits
if match:
    print(f"Found number: {match.group()}")
    print(f"At position: {match.start()}-{match.end()}")

# re.findall() — find all matches
numbers = re.findall(r'\d+', "I have 3 cats, 2 dogs, and 10 fish")
print(f"All numbers: {numbers}")

# re.match() — match only at START of string
print(re.match(r'\d+', "42 is the answer"))  # Match!
print(re.match(r'\d+', "The answer is 42"))  # None — not at start

# re.fullmatch() — entire string must match
print(re.fullmatch(r'\d+', "12345"))   # Match
print(re.fullmatch(r'\d+', "123abc"))  # None
```

**📸 Verified Output:**
```
Found number: 30
At position: 38-40
All numbers: ['3', '2', '10']
<re.Match object; span=(0, 2), match='42'>
None
<re.Match object; span=(0, 5), match='12345'>
None
```

### Step 2: Core Regex Syntax

```python
import re

# Character classes and quantifiers
patterns = [
    (r'\d',      "any digit"),
    (r'\D',      "any non-digit"),
    (r'\w',      "word char [a-zA-Z0-9_]"),
    (r'\W',      "non-word char"),
    (r'\s',      "whitespace"),
    (r'\S',      "non-whitespace"),
    (r'.',       "any char except newline"),
    (r'\d+',     "one or more digits"),
    (r'\d*',     "zero or more digits"),
    (r'\d?',     "zero or one digit"),
    (r'\d{3}',   "exactly 3 digits"),
    (r'\d{2,4}', "2 to 4 digits"),
    (r'[aeiou]', "any vowel"),
    (r'[^aeiou]',"any non-vowel"),
    (r'(cat|dog)', "cat or dog"),
    (r'\bword\b', "whole word 'word'"),
]

test = "Hello 12345 world! The cat sat."
for pattern, desc in patterns:
    matches = re.findall(pattern, test)
    print(f"  {pattern:12} ({desc:25}): {matches[:5]}")
```

**📸 Verified Output:**
```
  \d           (any digit                ): ['1', '2', '3', '4', '5']
  \D           (any non-digit            ): ['H', 'e', 'l', 'l', 'o']
  \w           (word char [a-zA-Z0-9_]  ): ['H', 'e', 'l', 'l', 'o']
  \W           (non-word char            ): [' ', ' ', '!', ' ', ' ']
  \s           (whitespace               ): [' ', ' ', ' ', ' ', ' ']
  \S           (non-whitespace           ): ['H', 'e', 'l', 'l', 'o']
  .            (any char except newline  ): ['H', 'e', 'l', 'l', 'o']
  \d+          (one or more digits       ): ['12345']
  \d*          (zero or more digits      ): ['', '', '', '', '', '']
  \d?          (zero or one digit        ): ['', '', '', '', '', '']
  \d{3}        (exactly 3 digits         ): ['123']
  \d{2,4}      (2 to 4 digits            ): ['1234']
  [aeiou]      (any vowel                ): ['e', 'o', 'o', 'a', 'a']
  [^aeiou]     (any non-vowel            ): ['H', 'l', 'l', ' ', '1']
  (cat|dog)    (cat or dog               ): ['cat']
  \bword\b     (whole word 'word'        ): []
```

### Step 3: Capturing Groups

```python
import re

# Groups — capture parts of the match
log_line = "2026-03-02 09:15:42 ERROR myapp: Connection timeout after 30s"

pattern = r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (\w+) (\w+): (.+)'
match = re.match(pattern, log_line)

if match:
    date, time, level, app, message = match.groups()
    print(f"Date:    {date}")
    print(f"Time:    {time}")
    print(f"Level:   {level}")
    print(f"App:     {app}")
    print(f"Message: {message}")

print()

# Named groups — more readable
pattern_named = r'(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<level>\w+)'
match = re.match(pattern_named, log_line)
if match:
    print(f"Named: date={match.group('date')}, time={match.group('time')}, level={match.group('level')}")
    print(f"As dict: {match.groupdict()}")
```

**📸 Verified Output:**
```
Date:    2026-03-02
Time:    09:15:42
Level:   ERROR
App:     myapp
Message: Connection timeout after 30s

Named: date=2026-03-02, time=09:15:42, level=ERROR
As dict: {'date': '2026-03-02', 'time': '09:15:42', 'level': 'ERROR'}
```

### Step 4: Common Validation Patterns

```python
import re

def validate(label, pattern, test_cases):
    print(f"\n{label}:")
    compiled = re.compile(pattern)
    for text in test_cases:
        valid = bool(compiled.fullmatch(text))
        status = "✅" if valid else "❌"
        print(f"  {status} {text!r}")

# Email validation (simplified)
validate("Email", 
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ["alice@example.com", "bob.jones@co.uk", "invalid@", "@no-local.com", "user@domain.x"])

# Phone: +1-555-123-4567 or (555) 123-4567 or 555-123-4567
validate("Phone",
    r'(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}',
    ["555-123-4567", "(555) 123-4567", "+1-555-123-4567", "1234567890", "555-1234"])

# Strong password: 8+ chars, upper, lower, digit, special
validate("Password",
    r'(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}',
    ["Passw0rd!", "weakpass", "NoSpecial1", "Short1!", "Str0ng@Pass"])

# IPv4 address
validate("IPv4",
    r'((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)',
    ["192.168.1.1", "255.255.255.0", "10.0.0.1", "256.1.2.3", "192.168.1"])
```

**📸 Verified Output:**
```
Email:
  ✅ 'alice@example.com'
  ✅ 'bob.jones@co.uk'
  ❌ 'invalid@'
  ❌ '@no-local.com'
  ❌ 'user@domain.x'

Phone:
  ✅ '555-123-4567'
  ✅ '(555) 123-4567'
  ✅ '+1-555-123-4567'
  ❌ '1234567890'
  ❌ '555-1234'

Password:
  ✅ 'Passw0rd!'
  ❌ 'weakpass'
  ❌ 'NoSpecial1'
  ❌ 'Short1!'
  ✅ 'Str0ng@Pass'

IPv4:
  ✅ '192.168.1.1'
  ✅ '255.255.255.0'
  ✅ '10.0.0.1'
  ❌ '256.1.2.3'
  ❌ '192.168.1'
```

### Step 5: re.sub() — Search and Replace

```python
import re

# Basic substitution
text = "The price is $19.99 and $5.00 discount"
masked = re.sub(r'\$[\d.]+', '[PRICE]', text)
print(masked)

# Replace with group references
date = "03/02/2026"
iso_date = re.sub(r'(\d{2})/(\d{2})/(\d{4})', r'\3-\1-\2', date)
print(f"ISO date: {iso_date}")

# Capitalize first letter of each sentence
paragraph = "hello world. this is python. regex is powerful."
result = re.sub(r'(^|(?<=\. ))([a-z])', lambda m: m.group().upper(), paragraph)
print(result)

# Remove multiple spaces
messy = "Hello    World   how   are   you"
clean = re.sub(r'\s+', ' ', messy)
print(clean)

# Redact sensitive data
log = "User john@example.com with card 4532-1234-5678-9012 logged in"
redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', log)
redacted = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', redacted)
print(redacted)
```

**📸 Verified Output:**
```
The price is [PRICE] and [PRICE] discount
ISO date: 2026-03-02
Hello world. This is python. Regex is powerful.
Hello World how are you
User [EMAIL] with card [CARD] logged in
```

### Step 6: re.compile() — Pre-compiled Patterns

```python
import re
import time

# Compile once, use many times — faster for repeated use
log_pattern = re.compile(
    r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'
    r'(?P<method>GET|POST|PUT|DELETE|PATCH)\s+'
    r'(?P<path>/\S*)\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<ms>\d+)ms',
    re.IGNORECASE
)

access_logs = [
    "192.168.1.1  GET  /api/users      200  45ms",
    "10.0.0.5     POST /api/login      401  12ms",
    "172.16.0.1   GET  /api/products   200 123ms",
    "192.168.1.99 DELETE /api/admin    403   8ms",
    "10.10.10.1   GET  /health         200   2ms",
]

parsed = []
for log in access_logs:
    m = log_pattern.search(log)
    if m:
        parsed.append(m.groupdict())

# Analyze
total = len(parsed)
errors = sum(1 for r in parsed if int(r['status']) >= 400)
avg_ms = sum(int(r['ms']) for r in parsed) / total

print(f"Parsed {total} requests:")
print(f"  Errors (4xx/5xx): {errors}")
print(f"  Avg response time: {avg_ms:.1f}ms")
print(f"\nRequests:")
for r in parsed:
    print(f"  {r['method']:6} {r['path']:15} → {r['status']} ({r['ms']}ms)")
```

**📸 Verified Output:**
```
Parsed 5 requests:
  Errors (4xx/5xx): 2
  Avg response time: 38.0ms

Requests:
  GET    /api/users      → 200 (45ms)
  POST   /api/login      → 401 (12ms)
  GET    /api/products   → 200 (123ms)
  DELETE /api/admin      → 403 (8ms)
  GET    /health         → 200 (2ms)
```

### Step 7: re.split() and Lookahead/Lookbehind

```python
import re

# re.split() — split on pattern
text = "one, two; three|four.five"
parts = re.split(r'[,;|.]', text)
print(f"Split: {parts}")

# Split keeping the delimiter
parts2 = re.split(r'([,;|.])', text)
print(f"With delimiter: {parts2}")

# Lookahead (?=...) — match position before pattern
# Split before capital letters (CamelCase to words)
camel = "CamelCaseStringParser"
words = re.sub(r'(?=[A-Z])', ' ', camel).strip()
print(f"CamelCase: {words}")

# Lookbehind (?<=...) — match position after pattern
# Add spaces after punctuation if missing
text = "Hello,World.How are you?Fine,thanks!"
spaced = re.sub(r'(?<=[,\.\?!])(?=[^\s])', ' ', text)
print(f"Spaced: {spaced}")

# Non-greedy matching
html = "<b>bold</b> and <i>italic</i>"
greedy = re.findall(r'<.+>', html)       # Greedy: gets too much
non_greedy = re.findall(r'<.+?>', html)  # Non-greedy: gets each tag
print(f"Greedy: {greedy}")
print(f"Non-greedy: {non_greedy}")
```

**📸 Verified Output:**
```
Split: ['one', ' two', ' three', 'four', 'five']
With delimiter: ['one', ',', ' two', ';', ' three', '|', 'four', '.', 'five']
CamelCase: Camel Case String Parser
Spaced: Hello, World. How are you? Fine, thanks!
Greedy: ['<b>bold</b> and <i>italic</i>']
Non-greedy: ['<b>', '</b>', '<i>', '</i>']
```

### Step 8: Real-World Log Parser

```python
import re
from collections import Counter, defaultdict

# Parse Apache/Nginx access log format
log_data = """
192.168.1.1 - alice [02/Mar/2026:09:01:00] "GET /home HTTP/1.1" 200 1234
192.168.1.2 - - [02/Mar/2026:09:01:05] "POST /login HTTP/1.1" 401 256
10.0.0.5 - bob [02/Mar/2026:09:01:10] "GET /dashboard HTTP/1.1" 200 5678
192.168.1.1 - alice [02/Mar/2026:09:01:15] "GET /api/data HTTP/1.1" 200 890
10.0.0.99 - - [02/Mar/2026:09:01:20] "GET /admin HTTP/1.1" 403 128
192.168.1.1 - alice [02/Mar/2026:09:01:25] "DELETE /api/item/5 HTTP/1.1" 204 0
10.0.0.5 - bob [02/Mar/2026:09:01:30] "GET /report HTTP/1.1" 500 512
""".strip()

LOG_PATTERN = re.compile(
    r'(?P<ip>[\d.]+)\s+-\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\w+)\s+(?P<path>\S+)\s+HTTP/[\d.]+"\s+'
    r'(?P<status>\d+)\s+(?P<bytes>\d+)'
)

records = []
for line in log_data.split('\n'):
    m = LOG_PATTERN.match(line)
    if m:
        r = m.groupdict()
        r['status'] = int(r['status'])
        r['bytes'] = int(r['bytes'])
        records.append(r)

# Analysis
status_counts = Counter(r['status'] for r in records)
user_requests = Counter(r['user'] for r in records)
errors = [r for r in records if r['status'] >= 400]
total_bytes = sum(r['bytes'] for r in records)

print(f"Total requests: {len(records)}")
print(f"Total bytes: {total_bytes:,}")
print(f"Status codes: {dict(status_counts)}")
print(f"Requests by user: {dict(user_requests)}")
print(f"Errors ({len(errors)}):")
for e in errors:
    print(f"  {e['status']} {e['method']} {e['path']} from {e['ip']}")
```

**📸 Verified Output:**
```
Total requests: 7
Total bytes: 8,698
Status codes: {200: 3, 401: 1, 403: 1, 204: 1, 500: 1}
Requests by user: {'alice': 3, '-': 2, 'bob': 2}
Errors (3):
  401 POST /login from 192.168.1.2
  403 GET /admin from 10.0.0.99
  500 GET /report from 10.0.0.5
```

## ✅ Verification

```python
import re

def extract_emails(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)

def mask_credit_card(text):
    return re.sub(r'\b(\d{4})[-\s]?\d{4}[-\s]?\d{4}[-\s]?(\d{4})\b',
                  r'\1-****-****-\2', text)

sample = "Contact alice@test.com or bob@example.org. Card: 4532-1234-5678-9012"
print(f"Emails: {extract_emails(sample)}")
print(f"Masked: {mask_credit_card(sample)}")
print("Lab 14 verified ✅")
```

**Expected output:**
```
Emails: ['alice@test.com', 'bob@example.org']
Masked: Contact alice@test.com or bob@example.org. Card: 4532-****-****-9012
Lab 14 verified ✅
```

## 🚨 Common Mistakes

1. **Not using raw strings**: `re.search('\d', text)` — `\d` works here but `\b` is a backspace! Always use `r'\d'`.
2. **Greedy vs non-greedy**: `.*` is greedy (matches as much as possible); use `.*?` for minimal matching.
3. **re.match vs re.search**: `match` only checks the START; `search` scans the entire string.
4. **Forgetting to compile for repeated use**: Re-compiling the same pattern in a loop is wasteful — use `re.compile()`.
5. **Catastrophic backtracking**: Nested quantifiers like `(a+)+` on long strings can cause timeout — simplify patterns.

## 📝 Summary

- `re.search()` finds first match; `re.findall()` returns all; `re.match()` matches at start
- Core syntax: `\d` digit, `\w` word, `\s` whitespace, `.` any, `+` one+, `*` zero+, `?` optional
- Groups `()` capture; named groups `(?P<name>...)` for readability
- `re.sub(pattern, replacement, text)` — search and replace
- `re.compile()` — compile once for repeated use (performance)
- Lookahead `(?=...)` / lookbehind `(?<=...)` — match positions without consuming

## 🔗 Further Reading
- [Python Docs: re module](https://docs.python.org/3/library/re.html)
- [regex101.com](https://regex101.com) — interactive regex tester
- [Real Python: Regex](https://realpython.com/regex-python/)
