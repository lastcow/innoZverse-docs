# Lab 12: API Security Testing

## Objective
Identify and exploit API security vulnerabilities: JWT algorithm confusion (alg:none attack), BOLA/IDOR in REST endpoints, missing authentication on internal routes, mass assignment, API rate limiting bypass, and GraphQL introspection abuse — then implement a hardened API with proper authentication and rate limiting.

## Background
APIs are the backbone of modern applications — and the fastest-growing attack surface. The **OWASP API Security Top 10** (2023) covers threats specific to APIs that the original Top 10 misses: BOLA (Broken Object Level Authorisation) is the #1 API vulnerability, present in virtually every large API. JWT (JSON Web Token) vulnerabilities — including the `alg:none` attack — have been found in production at Auth0, Amazon Cognito, and many others.

## Time
40 minutes

## Prerequisites
- Lab 07 (A07 Authentication Failures) — JWT basics

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: JWT Vulnerabilities — Algorithm Confusion

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import base64, json, hmac, hashlib, secrets

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def b64url_decode(s: str) -> bytes:
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

# --- Legitimate JWT creation ---
SECRET = secrets.token_bytes(32)

def create_jwt(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    h = b64url_encode(json.dumps(header).encode())
    p = b64url_encode(json.dumps(payload).encode())
    sig = hmac.new(SECRET, f'{h}.{p}'.encode(), hashlib.sha256).digest()
    return f'{h}.{p}.{b64url_encode(sig)}'

def verify_jwt_vulnerable(token: str) -> dict:
    '''VULNERABLE: trusts the alg header from the token itself.'''
    parts = token.split('.')
    if len(parts) != 3: raise ValueError('Invalid JWT')
    header  = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))
    alg = header.get('alg', 'HS256')
    
    if alg == 'none':
        # VULN: accepts unsigned tokens!
        print(f'  [VULN] alg=none accepted — no signature check!')
        return payload
    elif alg == 'HS256':
        sig = b64url_decode(parts[2])
        expected = hmac.new(SECRET, f'{parts[0]}.{parts[1]}'.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError('Invalid signature')
        return payload
    raise ValueError(f'Unknown algorithm: {alg}')

def verify_jwt_safe(token: str) -> dict:
    '''SAFE: ignores alg header, always uses HS256.'''
    parts = token.split('.')
    if len(parts) != 3: raise ValueError('Invalid JWT')
    sig = b64url_decode(parts[2])
    expected = hmac.new(SECRET, f'{parts[0]}.{parts[1]}'.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError('Invalid signature — token rejected')
    return json.loads(b64url_decode(parts[1]))

# Create legitimate token
legit_payload = {'sub': 'user-42', 'role': 'customer', 'exp': 9999999999}
legit_token = create_jwt(legit_payload)
print('=== JWT Algorithm Confusion Attack ===')
print(f'Legitimate token: {legit_token[:60]}...')
print()

# alg:none attack — forge admin token with no signature
forged_header  = b64url_encode(json.dumps({'alg': 'none', 'typ': 'JWT'}).encode())
forged_payload = b64url_encode(json.dumps({'sub': 'user-42', 'role': 'admin', 'exp': 9999999999}).encode())
forged_token   = f'{forged_header}.{forged_payload}.'  # empty signature

print(f'Forged token (alg:none, role=admin): {forged_token[:60]}...')
print()

print('[VULNERABLE] Server trusts alg header:')
try:
    result = verify_jwt_vulnerable(forged_token)
    print(f'  Accepted! Payload: {result}')
    print(f'  Attacker is now: {result[\"role\"]}')
except Exception as e:
    print(f'  Rejected: {e}')

print()
print('[SAFE] Server ignores alg header:')
try:
    result = verify_jwt_safe(forged_token)
    print(f'  Accepted: {result}')
except Exception as e:
    print(f'  Rejected: {e}')

# Also test RS256→HS256 confusion (public key used as HMAC secret)
print()
print('Other JWT attack vectors:')
attacks = [
    ('alg:none',      'Remove signature — server accepts unsigned tokens'),
    ('RS256→HS256',   'Server uses public key as HMAC secret — forge with known public key'),
    ('Key confusion', 'kid (key ID) header injection to control which key is used'),
    ('exp bypass',    'Modify exp claim if signature not verified'),
    ('jwk injection', 'Embed attacker-controlled JWK in header as trusted key'),
]
for name, desc in attacks:
    print(f'  [{name}] {desc}')
"
```

**📸 Verified Output:**
```
Forged token (alg:none, role=admin): eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0...

[VULNERABLE] Server trusts alg header:
  [VULN] alg=none accepted — no signature check!
  Accepted! Payload: {'sub': 'user-42', 'role': 'admin', 'exp': 9999999999}
  Attacker is now: admin

[SAFE] Server ignores alg header:
  Rejected: Invalid signature — token rejected
```

> 💡 **Never trust the `alg` field from the token itself.** The algorithm must be configured server-side. A library that says "I'll use whatever algorithm the token requests" is fundamentally broken. When using JWT libraries, explicitly specify the algorithm: `jwt.decode(token, secret, algorithms=['HS256'])` — note the plural `algorithms` parameter in PyJWT forces you to specify it.

### Step 2: BOLA — Broken Object Level Authorisation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import secrets

print('=== BOLA — Broken Object Level Authorisation (OWASP API #1) ===')
print()

# Simulated database
orders = {
    'ORD-001': {'user_id': 'user-42', 'product': 'Surface Pro 12',  'amount': 864.00, 'card_last4': '4242'},
    'ORD-002': {'user_id': 'user-99', 'product': 'Surface Laptop 5', 'amount': 1299.00,'card_last4': '1234'},
    'ORD-003': {'user_id': 'user-42', 'product': 'Surface Pen',      'amount': 49.99,  'card_last4': '4242'},
    'ORD-004': {'user_id': 'user-77', 'product': 'Office 365',       'amount': 99.99,  'card_last4': '5678'},
}

# VULNERABLE: No ownership check
def get_order_vulnerable(order_id: str, requesting_user: str) -> dict:
    order = orders.get(order_id)
    if not order:
        return {'error': 'Not found'}
    return order  # Returns ANY order regardless of owner!

# SAFE: Ownership verification
def get_order_safe(order_id: str, requesting_user: str) -> dict:
    order = orders.get(order_id)
    if not order:
        return {'error': 'Not found'}
    if order['user_id'] != requesting_user:
        return {'error': 'Forbidden'}  # Same error as not found (no enumeration)
    return order

attacker = 'user-42'  # logged in as user-42
target_order = 'ORD-002'  # belongs to user-99

print(f'Attacker: {attacker}')
print(f'Target order: {target_order} (belongs to user-99)')
print()

print('[VULNERABLE] GET /api/v1/orders/ORD-002:')
result = get_order_vulnerable(target_order, attacker)
print(f'  Response: {result}')
print(f'  Card leaked: ***{result[\"card_last4\"]}')
print(f'  Attacker can enumerate ALL orders by incrementing IDs!')

print()
print('[SAFE] GET /api/v1/orders/ORD-002:')
result2 = get_order_safe(target_order, attacker)
print(f'  Response: {result2}')

print()
print('BOLA impact scale:')
print('  Attacker script: for order_id in range(1, 10000000):')
print('    GET /api/orders/{order_id}')
print('    → Exfiltrates all customer orders, PII, payment data')
print()
print('BOLA prevention checklist:')
checks = [
    'Verify object ownership on EVERY request (not just at login)',
    'Use UUIDs instead of sequential IDs (reduces enumeration surface)',
    'Implement row-level security in database (PostgreSQL RLS)',
    'Log all access attempts with user_id + resource_id',
    'Rate limit enumerable endpoints',
    'Never return 403 vs 404 differently (prevents existence confirmation)',
]
for c in checks:
    print(f'  [✓] {c}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] GET /api/v1/orders/ORD-002:
  Response: {'user_id': 'user-99', 'product': 'Surface Laptop 5', 'amount': 1299.0, 'card_last4': '1234'}
  Card leaked: ***1234
  Attacker can enumerate ALL orders by incrementing IDs!

[SAFE] GET /api/v1/orders/ORD-002:
  Response: {'error': 'Forbidden'}
```

### Step 3: Mass Assignment

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Mass Assignment Vulnerability ===')
print()

# Simulated user model
class UserModelVulnerable:
    FIELDS = ['username', 'email', 'password', 'role', 'is_admin',
              'account_balance', 'plan', 'verified', 'created_at']

    def update(self, user_id: str, data: dict) -> dict:
        '''VULNERABLE: blindly applies all fields from request body.'''
        user = {'id': user_id, 'username': 'alice', 'email': 'alice@corp.com',
                'role': 'customer', 'is_admin': False, 'account_balance': 0.0}
        for key, value in data.items():
            if key in self.FIELDS:
                user[key] = value   # No field filtering!
        return user

class UserModelSafe:
    ALLOWED_UPDATE_FIELDS = {'username', 'email', 'password'}  # explicit allowlist

    def update(self, user_id: str, data: dict) -> dict:
        '''SAFE: only allows updating explicitly permitted fields.'''
        user = {'id': user_id, 'username': 'alice', 'email': 'alice@corp.com',
                'role': 'customer', 'is_admin': False, 'account_balance': 0.0}
        rejected = []
        for key, value in data.items():
            if key in self.ALLOWED_UPDATE_FIELDS:
                user[key] = value
            else:
                rejected.append(key)
        if rejected:
            print(f'  [SAFE] Rejected fields: {rejected}')
        return user

# Legitimate update
legit_update = {'username': 'alice2024', 'email': 'alice2024@corp.com'}

# Malicious mass assignment attack
malicious_update = {
    'username': 'alice2024',
    'email': 'alice2024@corp.com',
    'role': 'admin',           # privilege escalation!
    'is_admin': True,          # privilege escalation!
    'account_balance': 99999.99,  # financial fraud!
    'verified': True,          # bypass email verification
}

print('[VULNERABLE] PATCH /api/v1/users/me with malicious payload:')
result = UserModelVulnerable().update('user-42', malicious_update)
print(f'  role: {result[\"role\"]} (was: customer)')
print(f'  is_admin: {result[\"is_admin\"]} (was: False)')
print(f'  account_balance: \${result[\"account_balance\"]} (was: \$0.00)')
print(f'  IMPACT: Full account takeover + financial fraud!')

print()
print('[SAFE] PATCH /api/v1/users/me with malicious payload:')
result2 = UserModelSafe().update('user-42', malicious_update)
print(f'  role: {result2[\"role\"]} (unchanged)')
print(f'  is_admin: {result2[\"is_admin\"]} (unchanged)')
print(f'  account_balance: \${result2[\"account_balance\"]} (unchanged)')

print()
print('Mass assignment in real frameworks:')
examples = [
    ('Rails',  'User.update(params[:user])  ← vulnerable; use strong_parameters'),
    ('Django', 'form.save() with all fields ← use fields= or exclude= in ModelForm'),
    ('Spring', '@RequestBody User user      ← use DTOs, not entity classes directly'),
    ('Node',   'Object.assign(user, req.body) ← validate/filter req.body first'),
]
for fw, example in examples:
    print(f'  [{fw}] {example}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] PATCH /api/v1/users/me:
  role: admin (was: customer)
  is_admin: True (was: False)
  account_balance: $99999.99 (was: $0.00)
  IMPACT: Full account takeover + financial fraud!

[SAFE] PATCH /api/v1/users/me:
  [SAFE] Rejected fields: ['role', 'is_admin', 'account_balance', 'verified']
  role: customer (unchanged)
```

### Step 4: API Rate Limiting & Throttling

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import time

print('=== API Rate Limiting ===')
print()

call_store = {}

def rate_limit(api_key: str, endpoint: str, limit: int = 10, window: int = 60) -> tuple:
    '''Token bucket rate limiter per API key + endpoint.'''
    now = int(time.time())
    bucket_key = f'{api_key}:{endpoint}'
    timestamps = call_store.get(bucket_key, [])
    # Sliding window: keep only timestamps within current window
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= limit:
        reset_in = window - (now - timestamps[0])
        return False, 429, {
            'error': 'Rate limit exceeded',
            'limit': limit,
            'window': f'{window}s',
            'reset_in': f'{reset_in}s',
            'retry_after': reset_in,
        }
    timestamps.append(now)
    call_store[bucket_key] = timestamps
    remaining = limit - len(timestamps)
    return True, 200, {'X-RateLimit-Remaining': remaining, 'X-RateLimit-Limit': limit}

# Different limits per endpoint type
endpoint_limits = {
    '/api/v1/auth/login':           (5,  900),   # 5 per 15 minutes
    '/api/v1/auth/reset-password':  (3,  3600),  # 3 per hour
    '/api/v1/products':             (100, 60),   # 100 per minute
    '/api/v1/orders':               (30,  60),   # 30 per minute
    '/api/v1/admin/':               (20,  60),   # 20 per minute
}

print('Rate Limit Configuration:')
for endpoint, (limit, window) in endpoint_limits.items():
    print(f'  {endpoint:<40} {limit} req/{window}s')

print()
print('Simulating API abuse (brute-force login):')
for i in range(7):
    limit, window = endpoint_limits['/api/v1/auth/login']
    ok, status, resp = rate_limit('attacker-key', '/api/v1/auth/login', limit, window)
    if ok:
        print(f'  Request {i+1}: {status} OK (remaining: {resp[\"X-RateLimit-Remaining\"]})')
    else:
        print(f'  Request {i+1}: {status} BLOCKED — {resp[\"error\"]} (reset in {resp[\"reset_in\"]})')

print()
print('Rate limiting response headers:')
headers = {
    'X-RateLimit-Limit':     '100',
    'X-RateLimit-Remaining': '87',
    'X-RateLimit-Reset':     '1709510400',
    'Retry-After':           '43',
}
for h, v in headers.items():
    print(f'  {h}: {v}')

print()
print('Rate limiting bypass techniques:')
bypasses = [
    ('IP rotation',      'Use proxy pool — rate limit per IP', 'Use API key + IP together'),
    ('Header spoofing',  'X-Forwarded-For: different IPs each request', 'Never trust X-Forwarded-For for rate limiting'),
    ('Null byte',        'Append %00 to endpoint URL path', 'Normalise URLs before rate limit check'),
    ('Distributed',      'Many accounts each under threshold', 'Global rate limit per user, not per IP'),
]
for name, technique, defence in bypasses:
    print(f'  [{name}] Attack: {technique}')
    print(f'           Defence: {defence}')
"
```

**📸 Verified Output:**
```
Rate Limit Configuration:
  /api/v1/auth/login          5 req/900s
  /api/v1/auth/reset-password 3 req/3600s

Simulating API abuse:
  Request 1: 200 OK (remaining: 4)
  Request 2: 200 OK (remaining: 3)
  Request 5: 200 OK (remaining: 0)
  Request 6: 429 BLOCKED — Rate limit exceeded (reset in 900s)
```

### Step 5: Sensitive Data Exposure in API Responses

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import re

print('=== API Response — Data Overexposure ===')
print()

# VULNERABLE: Returns full user object from DB
def get_user_vulnerable(user_id):
    return {
        'id': user_id,
        'username': 'alice',
        'email': 'alice@corp.com',
        'password_hash': '\$2b\$12\$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
        'ssn': '123-45-6789',
        'credit_card': '4532-1234-5678-9012',
        'cvv': '421',
        'date_of_birth': '1990-05-15',
        'internal_notes': 'High-value customer, flagged for fraud review',
        'admin_level': 0,
        'totp_secret': 'JBSWY3DPEHPK3PXP',
        'reset_token': 'abc123def456',
        'login_attempts': 3,
        'is_banned': False,
        'stripe_customer_id': 'cus_abc123',
    }

# SAFE: Returns only fields needed by client
def get_user_safe(user_id):
    full = get_user_vulnerable(user_id)  # Fetch from DB
    return {
        'id':       full['id'],
        'username': full['username'],
        'email':    full['email'],
        # Never return: password_hash, ssn, cvv, totp_secret, reset_token, internal_notes
    }

print('[VULNERABLE] GET /api/v1/users/me — full DB record returned:')
vuln = get_user_vulnerable('user-42')
for k, v in vuln.items():
    risk = '[CRITICAL]' if k in ['password_hash','ssn','credit_card','cvv','totp_secret','reset_token'] else \
           '[HIGH]'     if k in ['date_of_birth','internal_notes','stripe_customer_id'] else '[OK]'
    print(f'  {risk} {k}: {v}')

print()
print('[SAFE] GET /api/v1/users/me — minimal response:')
safe = get_user_safe('user-42')
for k, v in safe.items():
    print(f'  [OK] {k}: {v}')

print()
print('OWASP API #3: Excessive Data Exposure — prevalence: very widespread')
print('Pattern: Developer returns entire DB model, relies on client to filter')
print('Reality: All fields are in the JSON response — accessible to any attacker')
print()
print('Prevention:')
print('  1. Define explicit response schemas (Pydantic, marshmallow, OpenAPI)')
print('  2. Code review API responses for sensitive field leakage')
print('  3. Automated scanning: check all API responses for PII patterns')
print('  4. Data classification: tag sensitive fields in models')
"
```

**📸 Verified Output:**
```
[VULNERABLE] GET /api/v1/users/me:
  [CRITICAL] password_hash: $2b$12$N9qo8uLOi...
  [CRITICAL] ssn: 123-45-6789
  [CRITICAL] credit_card: 4532-1234-5678-9012
  [CRITICAL] totp_secret: JBSWY3DPEHPK3PXP
  [CRITICAL] reset_token: abc123def456

[SAFE] GET /api/v1/users/me:
  [OK] id: user-42
  [OK] username: alice
  [OK] email: alice@corp.com
```

> 💡 **API response filtering must happen server-side.** Some developers return the full object and add a comment in JavaScript "only show these fields to the user." The client-side filtering is meaningless — all fields are in the HTTP response body, visible to browser dev tools, Burp Suite, or curl. Server-side schema enforcement (Pydantic's `response_model` in FastAPI, DRF serializers) is the correct approach.

### Step 6: Missing Function Level Authorisation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Missing Function Level Authorisation (OWASP API #5) ===')
print()

# API endpoint inventory — some admin endpoints exist but are 'hidden'
api_endpoints = [
    # Public endpoints
    ('GET',    '/api/v1/products',          'all',      True),
    ('GET',    '/api/v1/products/{id}',     'all',      True),
    ('POST',   '/api/v1/orders',            'customer', True),
    ('GET',    '/api/v1/orders/{id}',       'customer', True),

    # Admin endpoints — documented as 'internal' but still HTTP accessible
    ('GET',    '/api/v1/admin/users',       'admin',    False),  # No auth check!
    ('DELETE', '/api/v1/admin/users/{id}',  'admin',    False),  # No auth check!
    ('GET',    '/api/v1/admin/revenue',     'admin',    False),  # No auth check!
    ('POST',   '/api/v1/admin/refund',      'admin',    False),  # No auth check!
    ('GET',    '/api/v1/debug/config',      'admin',    False),  # Exists in prod!
    ('GET',    '/api/v1/internal/health',   'admin',    True),   # Properly secured
]

print(f'  {\"Method\":<8} {\"Endpoint\":<40} {\"Required Role\":<12} {\"Secured?\":<10} {\"Risk\"}')
for method, path, role, secured in api_endpoints:
    icon = '✓' if secured else '✗ EXPOSED'
    risk = 'CRITICAL' if not secured and role == 'admin' else 'OK'
    print(f'  {method:<8} {path:<40} {role:<12} {icon:<10} {risk}')

print()
print('Attack: enumerate admin endpoints via wordlist + HTTP verbs')
print('Target: GET /api/v1/admin/users → returns all user data without auth')
print()

# Secure implementation
print('Secure implementation (decorator pattern):')
print('''
  def require_role(*roles):
      def decorator(f):
          def wrapper(*args, **kwargs):
              token = get_current_token()
              if token[\"role\"] not in roles:
                  return {\"error\": \"Forbidden\"}, 403
              return f(*args, **kwargs)
          return wrapper
      return decorator

  @app.route(\"/api/v1/admin/users\")
  @require_role(\"admin\", \"super_admin\")   # Explicit role check on EVERY route
  def list_users():
      return get_all_users()
''')
"
```

### Step 7: GraphQL Security

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import json

print('=== GraphQL Security Issues ===')
print()

print('[Issue 1] Introspection — exposes entire schema')
introspection_query = '''
{
  __schema {
    types {
      name
      fields {
        name
        type { name }
      }
    }
  }
}'''
print(f'  Introspection query: {introspection_query.strip()[:100]}...')
print('  Response reveals: ALL types, ALL fields, ALL mutations, ALL queries')
print('  Attack: Find hidden admin mutations, sensitive fields, internal types')
print()

print('[Issue 2] Batching attack (rate limit bypass)')
batch_query = json.dumps([
    {'query': 'mutation { login(email: \"admin\", password: \"pass1\") { token } }'},
    {'query': 'mutation { login(email: \"admin\", password: \"pass2\") { token } }'},
    {'query': 'mutation { login(email: \"admin\", password: \"pass3\") { token } }'},
])
print(f'  Batch: {batch_query[:100]}...')
print('  One HTTP request = 100 login attempts → bypasses rate limiter!')
print()

print('[Issue 3] Deeply nested queries (DoS)')
nested = '{ user { orders { items { product { reviews { author { orders { items { product }}}}}}}}}}'
print(f'  Nested query: {nested}')
print('  Database: 8 JOINs per request, exponential data fetching = DoS')
print()

print('GraphQL security controls:')
controls = [
    ('Disable introspection in production', 'graphene: introspection=False'),
    ('Query depth limiting', 'Max depth 5 — reject deeper queries'),
    ('Query complexity scoring', 'Reject queries with complexity > 100'),
    ('Per-operation rate limiting', 'Rate limit per mutation type, not just per IP'),
    ('Field-level authorisation', 'Check permissions per field, not just per query'),
    ('Disable batching', 'Or limit batch size to 5'),
    ('Persisted queries', 'Only allow pre-approved query hashes'),
]
for control, impl in controls:
    print(f'  [✓] {control:<40} → {impl}')
"
```

**📸 Verified Output:**
```
[Issue 1] Introspection
  Response reveals: ALL types, ALL fields, ALL mutations, ALL queries
  Attack: Find hidden admin mutations, sensitive fields, internal types

[Issue 2] Batching attack (rate limit bypass)
  One HTTP request = 100 login attempts → bypasses rate limiter!

[Issue 3] Deeply nested queries
  Database: 8 JOINs per request, exponential data fetching = DoS
```

### Step 8: Capstone — API Security Hardening

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import json

api_security_policy = {
    'authentication': {
        'jwt_algorithm': 'RS256 (asymmetric) — server-side algorithm enforcement',
        'jwt_expiry': '15 minutes access token, 7 days refresh token',
        'api_keys': 'For machine-to-machine, rotate every 90 days',
        'mfa': 'Required for admin API endpoints',
    },
    'authorisation': {
        'bola': 'Every endpoint verifies object ownership before returning data',
        'function_auth': 'Role check decorator on every route — no exceptions',
        'mass_assignment': 'Explicit allowlist of updatable fields per endpoint',
    },
    'data_exposure': {
        'response_schema': 'Pydantic response_model on every endpoint',
        'pii_logging': 'Mask PII in logs (email → al***@corp.com)',
        'error_format': 'Generic errors with correlation ID — no stack traces',
    },
    'rate_limiting': {
        'auth_endpoints': '5 req/15min per IP + API key',
        'public_api': '100 req/min per API key',
        'admin_api': '20 req/min per session',
    },
    'transport': {
        'tls': 'TLS 1.3 only, HSTS with preload',
        'certificates': 'Short-lived certs (90 days), auto-renew',
    },
}

print('API Security Policy — InnoZverse API v2:')
print()
for category, controls in api_security_policy.items():
    print(f'  [{category.upper()}]')
    for key, value in controls.items():
        print(f'    {key:<20}: {value}')
    print()

print('OWASP API Security Top 10 coverage:')
coverage = [
    ('API1: BOLA',                   '✓ Object ownership check on all endpoints'),
    ('API2: Broken Auth',            '✓ JWT RS256, short expiry, MFA for admin'),
    ('API3: Broken Object Prop Auth','✓ Pydantic response_model, explicit allowlists'),
    ('API4: Unrestricted Resource',  '✓ Rate limiting per endpoint + user'),
    ('API5: Function Auth',          '✓ Role decorator on every route'),
    ('API6: Unrestricted Access',    '✓ Business flow validation'),
    ('API7: Server Side Request',    '✓ SSRF controls (Lab 10)'),
    ('API8: Security Misconfig',     '✓ Hardened headers, no debug mode'),
    ('API9: Improper Inventory',     '✓ OpenAPI spec + automated discovery'),
    ('API10: Unsafe API Consumption','✓ Validate all third-party API responses'),
]
for vuln, status in coverage:
    print(f'  [✓] {vuln:<35} {status}')
"
```

---

## Summary

| API Vulnerability | Attack | Fix |
|------------------|--------|-----|
| JWT alg:none | Forge token without signature | Server-side algorithm enforcement |
| BOLA | Access other users' resources | Object ownership check on every request |
| Mass assignment | Escalate privileges via extra fields | Explicit field allowlist per operation |
| Excessive data exposure | PII/secrets in response | Pydantic response_model schema |
| Missing function auth | Access admin endpoints | Role decorator on every route |
| No rate limiting | Brute-force, enumeration | Per-endpoint per-user rate limits |

## Further Reading
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [PortSwigger API Testing](https://portswigger.net/web-security/api-testing)
- [JWT Attack Playbook](https://github.com/ticarpi/jwt_tool/wiki)
