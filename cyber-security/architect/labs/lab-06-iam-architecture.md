# Lab 06: IAM Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design enterprise IAM architecture with SAML 2.0 and OAuth 2.0/OIDC
- Build and validate JWTs with HMAC-SHA256
- Implement RBAC engine
- Understand PAM and JIT access patterns

---

## Step 1: Enterprise IAM Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  IDENTITY FABRIC                         │
│                                                         │
│  HR System ──→ Identity Store (AD/LDAP) ←── SCIM sync  │
│                        │                               │
│              ┌─────────▼──────────┐                    │
│              │   Identity Provider │  (Okta, Azure AD)  │
│              │   - Authentication  │                    │
│              │   - MFA             │                    │
│              │   - Token issuance  │                    │
│              └─────────┬──────────┘                    │
│                        │                               │
│          ┌─────────────┼─────────────┐                 │
│          ▼             ▼             ▼                  │
│      SAML 2.0       OAuth2/OIDC    Kerberos             │
│      (Enterprise    (Modern apps,  (Windows/AD)         │
│       SSO)          APIs, mobile)                       │
└─────────────────────────────────────────────────────────┘
         │
    ┌────▼───────────────────────────────────┐
    │ Applications & Resources               │
    │  Web Apps │ APIs │ Cloud │ On-prem     │
    └────────────────────────────────────────┘
```

---

## Step 2: SAML 2.0 Flow

**Service Provider (SP) initiated SSO:**
```
1. User → SP (app) — access request
2. SP → redirect to IdP with AuthnRequest
3. User → IdP — authenticate (password + MFA)
4. IdP → SP — SAMLResponse (signed XML assertion)
5. SP validates signature → extracts attributes
6. SP grants access based on SAML attributes (role, groups)
```

**SAML assertion attributes for RBAC:**
```xml
<saml:AttributeStatement>
  <saml:Attribute Name="groups">
    <saml:AttributeValue>finance-analysts</saml:AttributeValue>
    <saml:AttributeValue>read-only-users</saml:AttributeValue>
  </saml:Attribute>
  <saml:Attribute Name="email">
    <saml:AttributeValue>alice@corp.com</saml:AttributeValue>
  </saml:Attribute>
</saml:AttributeStatement>
```

---

## Step 3: OAuth 2.0 / OIDC Flows

**OAuth 2.0 grant types:**

| Grant Type | Use Case | Security |
|-----------|---------|---------|
| Authorization Code + PKCE | Web/mobile apps | ✅ Recommended |
| Client Credentials | Service-to-service | ✅ Machine identity |
| Device Code | CLI tools, TV apps | ✅ Headless devices |
| Implicit | (deprecated) | ❌ Do not use |
| ROPC | Legacy only | ⚠️ Avoid if possible |

**OIDC ID Token (JWT) claims:**
```json
{
  "iss": "https://idp.corp.com",
  "sub": "user123",
  "aud": "my-app-client-id",
  "exp": 1712000000,
  "iat": 1711996400,
  "email": "alice@corp.com",
  "groups": ["finance", "read-only"],
  "amr": ["mfa", "pwd"]
}
```

---

## Step 4: JWT Builder + RBAC Engine

```python
import hmac, hashlib, base64, json, time

def b64url(data):
    if isinstance(data, str): data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def build_jwt(payload, secret):
    header = b64url(json.dumps({'alg':'HS256','typ':'JWT'}))
    body   = b64url(json.dumps(payload))
    sig_input = f'{header}.{body}'.encode()
    sig = hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
    return f'{header}.{body}.{b64url(sig)}'

def validate_jwt(token, secret):
    parts = token.split('.')
    if len(parts) != 3: return False, 'Invalid structure'
    sig_input = f'{parts[0]}.{parts[1]}'.encode()
    expected = hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
    actual = base64.urlsafe_b64decode(parts[2] + '==')
    if not hmac.compare_digest(expected, actual): return False, 'Invalid signature'
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
    if payload.get('exp', 9e9) < time.time(): return False, 'Token expired'
    return True, payload

SECRET = 'innozverse-secret-key'
payload = {'sub': 'user123', 'role': 'admin', 'iat': int(time.time()), 'exp': int(time.time())+3600}
token = build_jwt(payload, SECRET)
print('=== JWT Builder/Validator ===')
print(f'Token : {token[:60]}...')
valid, result = validate_jwt(token, SECRET)
print(f'Valid : {valid}')
print(f'Sub   : {result["sub"]}  Role: {result["role"]}')

print()
print('=== RBAC Engine ===')
roles = {'admin': ['read','write','delete','admin'], 'analyst': ['read','write'], 'viewer': ['read']}
def check_perm(role, action):
    return action in roles.get(role, [])

tests = [('admin','delete'), ('analyst','delete'), ('viewer','read'), ('analyst','read')]
for role, action in tests:
    status = 'ALLOW' if check_perm(role, action) else 'DENY'
    print(f'  role={role:<10} action={action:<8} -> {status}')
```

📸 **Verified Output:**
```
=== JWT Builder/Validator ===
Token : eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzdWIiOiAidXNlcjE...
Valid : True
Sub   : user123  Role: admin

=== RBAC Engine ===
  role=admin      action=delete   -> ALLOW
  role=analyst    action=delete   -> DENY
  role=viewer     action=read     -> ALLOW
  role=analyst    action=read     -> ALLOW
```

---

## Step 5: Access Control Models Comparison

**RBAC (Role-Based Access Control):**
- Assign users to roles; roles have permissions
- Simple to administer; good for stable job functions
- Example: `admin`, `analyst`, `viewer` roles

**ABAC (Attribute-Based Access Control):**
- Policy: `IF user.dept == 'finance' AND resource.classification == 'confidential' AND time.hour IN [9,17] THEN allow`
- Flexible, fine-grained; complex to manage at scale
- XACML standard; used in government/military

**ReBAC (Relationship-Based Access Control):**
- Access based on relationships between objects
- Example: Google Drive — owner → shares with → user
- Zanzibar (Google) model; used by Airbnb, Slack, GitHub

| Model | Best For | Complexity | Flexibility |
|-------|---------|-----------|------------|
| RBAC | Enterprise apps, clear job roles | Low | Medium |
| ABAC | Cloud, fine-grained, context-aware | High | High |
| ReBAC | Collaborative apps, hierarchical data | Medium | High |

---

## Step 6: SCIM Provisioning

**SCIM 2.0 (System for Cross-domain Identity Management):**
- RESTful API for user/group provisioning between IdP and apps
- Automates: create user, update attributes, deactivate (joiner/mover/leaver)

**SCIM endpoints:**
```
GET    /Users?filter=userName eq "alice"
POST   /Users                    # Create user
PUT    /Users/{id}               # Update (replace)
PATCH  /Users/{id}               # Update (partial)
DELETE /Users/{id}               # Deactivate
GET    /Groups                   # List groups
```

> 💡 **Leaver process automation with SCIM**: HR triggers deactivation in IdP → SCIM propagates to all connected apps within minutes, ensuring consistent offboarding across 50+ SaaS platforms.

---

## Step 7: PAM and JIT Access

**Privileged Access Management (PAM):**

| Feature | Description | Example Tool |
|---------|-----------|-------------|
| Credential vault | Store/rotate privileged passwords | CyberArk, HashiCorp Vault |
| Session recording | Record admin sessions for audit | BeyondTrust, Delinea |
| Just-in-Time (JIT) | Time-limited privilege elevation | PIM (Azure AD), CyberArk |
| Approval workflow | Multi-party approval for critical systems | ServiceNow + PAM |
| Break-glass | Emergency access for DR scenarios | Documented, monitored |

**JIT access pattern:**
```
Engineer requests: "sudo access to prod-db-01 for 2 hours"
  → Approval from manager (Slack/Teams)
  → PAM creates time-limited SSH certificate
  → Session recorded in PAM
  → After 2h: access revoked automatically
  → Audit log available for compliance
```

---

## Step 8: Capstone — Enterprise IAM Design

**Scenario:** Global enterprise, 10,000 employees, 200+ applications

```
IAM Architecture:

Identity Provider:
  - Okta (primary IdP)
  - Azure AD (Windows integration, M365)
  - Federation: Okta ↔ Azure AD via OIDC

Authentication:
  - MFA mandatory for all (Okta Verify push)
  - Passwordless (FIDO2) for privileged users
  - Phishing-resistant MFA for finance/HR systems

SSO Coverage:
  - SAML 2.0: 150 enterprise applications
  - OIDC: 50 modern web/mobile apps
  - SCIM provisioning: 80 SaaS apps automated

Access Control:
  - RBAC: 45 job-function roles defined
  - ABAC enrichment: data classification attributes
  - Context-aware: block access from high-risk countries

Privileged Access:
  - CyberArk for server credentials
  - Azure PIM for admin roles (JIT, 4h max)
  - Break-glass accounts: 2 per region, monitored 24/7

Lifecycle:
  - Joiner: Workday HR triggers Okta SCIM provisioning
  - Mover: Manager approves role change in Okta
  - Leaver: HR offboard → Okta deactivate → SCIM to all apps (< 1 hour)

Audit & Compliance:
  - Quarterly access reviews via Okta Access Governance
  - Separation of duties (SOD) enforcement for finance roles
  - GDPR: data minimisation in LDAP attributes
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| SAML 2.0 | XML-based SSO; SP-initiated flow; attributes carry role info |
| OAuth 2.0 | Delegated authorisation; Authorization Code + PKCE preferred |
| OIDC | Identity layer on OAuth 2.0; ID Token is a JWT |
| JWT | Header.Payload.Signature; verify signature + expiry |
| RBAC | Roles → permissions; simple but coarse-grained |
| ABAC | Policy-based; attributes from user/resource/environment |
| SCIM | Automated user provisioning/deprovisioning via REST API |
| PAM | Vault credentials, record sessions, JIT privilege elevation |
