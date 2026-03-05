# Lab 13: LDAP Directory Services

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

LDAP (Lightweight Directory Access Protocol) is the standard protocol for storing and querying hierarchical identity data — users, groups, organizational units, and attributes. It powers Active Directory, OpenLDAP, and enterprise authentication everywhere. Understanding LDAP is essential for Linux PAM authentication, application SSO, and identity management.

In this lab you'll install OpenLDAP (slapd), explore the Directory Information Tree (DIT), add entries using LDIF format, and search the directory.

---

## Background

### LDAP Architecture

```
                    LDAP Client
                    (ldapsearch, app)
                         │
                    TCP Port 389 (LDAP)
                    TCP Port 636 (LDAPS)
                         │
                    ┌────┴─────┐
                    │  slapd   │ ← OpenLDAP daemon
                    │ (server) │
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              │  Directory (DIT)    │
              │                     │
              │  dc=example,dc=com  │ ← Suffix / Base DN
              │   ├── ou=people     │
              │   │    ├── cn=alice │
              │   │    └── cn=bob   │
              │   └── ou=groups     │
              │        └── cn=admins│
              └─────────────────────┘
```

### Distinguished Names (DN)

Every LDAP entry has a globally unique **Distinguished Name (DN)**:

```
cn=alice,ou=people,dc=example,dc=com
│         │         │         │
│         │         └── dc = domain component
│         └── ou = organizational unit
└── cn = common name (Relative DN = RDN)
```

| Attribute | Full Name | Typical Use |
|-----------|-----------|-------------|
| **dc** | domainComponent | DNS domain parts (dc=example,dc=com) |
| **cn** | commonName | Person's name, group name |
| **ou** | organizationalUnit | Department, category |
| **sn** | surname | Last name |
| **uid** | userid | Unix username |
| **mail** | — | Email address |
| **o** | organization | Company name |

### LDAP Operations

| Operation | Description |
|-----------|-------------|
| **Bind** | Authenticate (anonymous or with DN+password) |
| **Search** | Query entries matching a filter |
| **Add** | Create a new entry |
| **Modify** | Change attributes of an entry |
| **Delete** | Remove an entry |
| **Compare** | Test if attribute has a specific value |
| **ModifyDN** | Rename or move an entry |
| **Unbind** | Close the connection |

### LDIF Format

LDAP Data Interchange Format (LDIF) is the text format for entries:

```ldif
dn: cn=alice,ou=people,dc=example,dc=com
objectClass: top
objectClass: inetOrgPerson
cn: alice
sn: Smith
mail: alice@example.com
userPassword: {SSHA}hashedpassword
telephoneNumber: +1-555-0100
```

Rules:
- Each entry separated by a **blank line**
- `dn:` must be first
- `objectClass:` defines which attributes are allowed/required
- Lines starting with `#` are comments

---

## Step 1: Install OpenLDAP

```bash
docker run -it --rm ubuntu:22.04 bash
```

Inside the container:

```bash
DEBIAN_FRONTEND=noninteractive apt-get update && \
DEBIAN_FRONTEND=noninteractive apt-get install -y slapd ldap-utils
```

Check the version:
```bash
slapd -V
```

📸 **Verified Output:**
```
@(#) $OpenLDAP: slapd 2.5.20+dfsg-0ubuntu0.22.04.1 (Sep 24 2025 13:40:37) $
	Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
```

> 💡 `slapd` is the **LDAP daemon**. `ldap-utils` provides client tools: `ldapsearch`, `ldapadd`, `ldapmodify`, `ldapdelete`, `ldappasswd`.

---

## Step 2: Test the Default Configuration

```bash
# Test config syntax
slaptest

# List config files
ls /etc/ldap/
```

📸 **Verified Output:**
```
config file testing succeeded

ldap.conf
sasl2
schema
slapd.d
```

The directory `/etc/ldap/slapd.d/` contains the **cn=config** database — OpenLDAP's runtime configuration stored as LDAP entries themselves (you can modify config via LDAP operations):

```bash
# View the cn=config tree
ls /etc/ldap/slapd.d/cn\=config/
```

```
cn=module{0}.ldif
cn=schema.ldif
olcDatabase={-1}frontend.ldif
olcDatabase={0}config.ldif
olcDatabase={1}mdb.ldif
```

---

## Step 3: Start slapd and Search the Directory

```bash
# Start slapd (runs as root in container)
slapd -u root -h 'ldap://localhost' &
sleep 2

# Anonymous search of the base entry
ldapsearch -x -H ldap://localhost -b 'dc=nodomain'
```

📸 **Verified Output:**
```
# extended LDIF
#
# LDAPv3
# base <dc=nodomain> with scope subtree
# filter: (objectclass=*)
# requesting: ALL
#

# nodomain
dn: dc=nodomain
objectClass: top
objectClass: dcObject
objectClass: organization
o: nodomain
dc: nodomain

# search result
search: 2
result: 0 Success

# numResponses: 2
# numEntries: 1
```

> 💡 The `-x` flag means **simple authentication** (username+password, not SASL). For anonymous bind, omit `-D` and `-w`. The default base DN `dc=nodomain` was set during package installation.

---

## Step 4: Reconfigure with a Proper Domain

```bash
# Set debconf answers for reconfiguration
echo 'slapd slapd/root_password password admin123' | debconf-set-selections
echo 'slapd slapd/root_password_again password admin123' | debconf-set-selections
echo 'slapd slapd/domain string example.com' | debconf-set-selections
echo 'slapd slapd/organization string Example Corp' | debconf-set-selections

# Reconfigure slapd
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure slapd

# Restart with new config
kill $(pgrep slapd) 2>/dev/null; sleep 1
slapd -u root -h 'ldap://localhost' &
sleep 2

# Search new base
ldapsearch -x -H ldap://localhost -b 'dc=example,dc=com' -s base
```

📸 **Verified Output:**
```
# extended LDIF
#
# LDAPv3
# base <dc=example,dc=com> with scope baseObject
# filter: (objectclass=*)
# requesting: ALL
#

# example.com
dn: dc=example,dc=com
objectClass: top
objectClass: dcObject
objectClass: organization
o: Example Corp
dc: example

# search result
search: 2
result: 0 Success
```

Search scope options:
- `-s base` — Only the base entry itself
- `-s one` — Direct children of the base
- `-s sub` — Entire subtree (default)

---

## Step 5: Add Directory Entries with LDIF

```bash
# Create an LDIF file with organizational units and users
cat > /tmp/directory.ldif << 'EOF'
# Organizational Unit: people
dn: ou=people,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: people
description: User accounts

# Organizational Unit: groups
dn: ou=groups,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: groups
description: Unix/application groups

# User: Alice Smith
dn: cn=alice,ou=people,dc=example,dc=com
objectClass: top
objectClass: inetOrgPerson
cn: alice
sn: Smith
mail: alice@example.com
telephoneNumber: +1-555-0100

# User: Bob Jones
dn: cn=bob,ou=people,dc=example,dc=com
objectClass: top
objectClass: inetOrgPerson
cn: bob
sn: Jones
mail: bob@example.com
telephoneNumber: +1-555-0200
EOF

# Add entries (requires admin bind)
# Note: password is set in /etc/ldap/slapd.d — use slapadd for direct import
slapadd -l /tmp/directory.ldif 2>&1 || echo "slapadd requires slapd stopped"

# Alternative: restart slapd and use LDIF import
kill $(pgrep slapd) 2>/dev/null; sleep 1
slapadd -l /tmp/directory.ldif
slapd -u root -h 'ldap://localhost' &
sleep 2

# Search for all people
ldapsearch -x -H ldap://localhost -b 'ou=people,dc=example,dc=com'
```

📸 **Verified Output:**
```
# extended LDIF
#
# LDAPv3
# base <ou=people,dc=example,dc=com> with scope subtree
# filter: (objectclass=*)
# requesting: ALL
#

# people, example.com
dn: ou=people,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: people
description: User accounts

# alice, people, example.com
dn: cn=alice,ou=people,dc=example,dc=com
objectClass: top
objectClass: inetOrgPerson
cn: alice
sn: Smith
mail: alice@example.com
telephoneNumber: +1-555-0100

# bob, people, example.com
dn: cn=bob,ou=people,dc=example,dc=com
objectClass: top
objectClass: inetOrgPerson
cn: bob
sn: Jones
mail: bob@example.com
telephoneNumber: +1-555-0200

# search result
search: 2
result: 0 Success

# numResponses: 4
# numEntries: 3
```

> 💡 **slapadd** directly imports LDIF into the MDB database files — faster than ldapadd but requires slapd to be stopped. Use `ldapadd` for online adds while slapd is running.

---

## Step 6: LDAP Search Filters

```bash
# Search filter syntax: (attribute=value)
# Compound: (&(filter1)(filter2)) = AND, (|(filter1)(filter2)) = OR

# Find all inetOrgPerson entries
ldapsearch -x -H ldap://localhost \
  -b 'dc=example,dc=com' \
  '(objectClass=inetOrgPerson)' cn mail

# Find user by email domain
ldapsearch -x -H ldap://localhost \
  -b 'dc=example,dc=com' \
  '(mail=*@example.com)' cn sn

# Find specific user
ldapsearch -x -H ldap://localhost \
  -b 'dc=example,dc=com' \
  '(cn=alice)' cn mail telephoneNumber

# AND filter: inetOrgPerson with surname starting with S
ldapsearch -x -H ldap://localhost \
  -b 'dc=example,dc=com' \
  '(&(objectClass=inetOrgPerson)(sn=S*))' dn cn sn
```

📸 **Verified Output:**
```
# extended LDIF
#
# LDAPv3
# base <dc=example,dc=com> with scope subtree
# filter: (cn=alice)
# requesting: cn mail telephoneNumber
#

# alice, people, example.com
dn: cn=alice,ou=people,dc=example,dc=com
cn: alice
mail: alice@example.com
telephoneNumber: +1-555-0100

# search result
search: 2
result: 0 Success

# numResponses: 2
# numEntries: 1
```

> 💡 LDAP filter special characters must be escaped: `*` = wildcard, `(` `)` `\` `NULL` must be escaped as `\2a`, `\28`, `\29`, `\5c`, `\00`.

---

## Step 7: Modify and Delete Entries

```bash
# Modify entry — change telephone number
cat > /tmp/modify.ldif << 'EOF'
dn: cn=alice,ou=people,dc=example,dc=com
changetype: modify
replace: telephoneNumber
telephoneNumber: +1-555-9999
-
add: description
description: Senior Engineer
EOF

ldapmodify -x -H ldap://localhost \
  -D 'cn=admin,dc=example,dc=com' -w admin123 \
  -f /tmp/modify.ldif

# Verify modification
ldapsearch -x -H ldap://localhost \
  -b 'cn=alice,ou=people,dc=example,dc=com' \
  -s base telephoneNumber description

# View LDAP schema (objectClasses and attributes)
ldapsearch -x -H ldap://localhost \
  -b 'cn=schema,cn=config' \
  -s base '(objectClass=*)' objectClasses 2>/dev/null | head -30 || \
  echo "Schema stored in /etc/ldap/schema/"

ls /etc/ldap/schema/
```

📸 **Verified Output:**
```
/etc/ldap/schema/:
collective.schema  corba.schema  core.schema  cosine.schema
duaconf.schema  dyngroup.schema  inetorgperson.schema
java.schema  misc.schema  nis.schema  openldap.schema
ppolicy.schema
```

> 💡 Schema files define **objectClasses** (which attributes an entry can/must have) and **attributeTypes** (data type, syntax, matching rules). The `inetOrgPerson` schema is the most common for user entries.

---

## Step 8: Capstone — LDAP Security and TLS Overview

```bash
# Demonstrate LDAP security concepts
cat << 'EOF'
=== LDAP Security Model ===

1. ANONYMOUS BIND
   ldapsearch -x -H ldap://server -b 'dc=example,dc=com'
   ↳ No credentials — read-only access if ACLs allow

2. SIMPLE BIND (DN + Password)
   ldapsearch -x -H ldap://server -D 'cn=admin,dc=...' -w password
   ↳ Cleartext over plain LDAP — INSECURE

3. LDAPS (LDAP over TLS, port 636)
   ldapsearch -x -H ldaps://server -D 'cn=admin,dc=...' -w password
   ↳ Full TLS encryption — production standard

4. StartTLS (upgrade plain connection)
   ldapsearch -x -H ldap://server -Z -D 'cn=admin,dc=...' -w password
   ↳ Start plain, then negotiate TLS

5. SASL GSSAPI (Kerberos)
   ldapsearch -H ldap://server -b 'dc=example,dc=com'
   ↳ Uses Kerberos ticket — no password in command

=== OpenLDAP ACL Example (slapd.conf) ===

# Allow users to change their own password
access to attrs=userPassword
  by self write
  by anonymous auth
  by * none

# Allow authenticated users to read people
access to dn.subtree="ou=people,dc=example,dc=com"
  by users read
  by * none

=== Practical Use Cases ===

Linux PAM Auth:
  /etc/pam.d/common-auth → pam_ldap.so → slapd
  Users log in with LDAP credentials

Application Auth:
  Django/Rails/Node → python-ldap/ldapjs → slapd
  Central user database for all apps

Active Directory:
  Microsoft's LDAP implementation
  Same protocol, different schema (sAMAccountName, etc.)

=== Quick Reference ===
EOF

echo "ldapsearch -x -H ldap://host -b BASE '(filter)' [attrs]"
echo "ldapadd    -x -H ldap://host -D ADMIN -w PASS -f file.ldif"
echo "ldapmodify -x -H ldap://host -D ADMIN -w PASS -f modify.ldif"
echo "ldapdelete -x -H ldap://host -D ADMIN -w PASS DN"
echo "ldappasswd -x -H ldap://host -D ADMIN -w PASS -s NEW_PASS DN"
echo ""
echo "=== Current directory contents ==="
ldapsearch -x -H ldap://localhost -b 'dc=example,dc=com' \
  '(objectClass=*)' dn 2>&1
```

📸 **Verified Output:**
```
=== LDAP Security Model ===

1. ANONYMOUS BIND
   ldapsearch -x -H ldap://server -b 'dc=example,dc=com'
   ↳ No credentials — read-only access if ACLs allow

2. SIMPLE BIND (DN + Password)
   ldapsearch -x -H ldap://server -D 'cn=admin,dc=...' -w password
   ↳ Cleartext over plain LDAP — INSECURE

3. LDAPS (LDAP over TLS, port 636)
   ldapsearch -x -H ldaps://server -D 'cn=admin,dc=...' -w password
   ↳ Full TLS encryption — production standard

...

=== Current directory contents ===
# extended LDIF
dn: dc=example,dc=com
dn: ou=people,dc=example,dc=com
dn: ou=groups,dc=example,dc=com
dn: cn=alice,ou=people,dc=example,dc=com
dn: cn=bob,ou=people,dc=example,dc=com

# search result
search: 2
result: 0 Success
# numEntries: 5
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **LDAP Protocol** | TCP/UDP 389 (plain), 636 (TLS); directory queries |
| **Distinguished Name** | `cn=alice,ou=people,dc=example,dc=com` — globally unique path |
| **DIT** | Directory Information Tree — hierarchical namespace |
| **objectClass** | Defines required/optional attributes for an entry |
| **LDIF** | Text format for entries; blank line separates records |
| **Bind** | Authentication: anonymous, simple (DN+pw), SASL/Kerberos |
| **Search Filter** | `(attr=val)`, `(&(f1)(f2))` AND, `(\|(f1)(f2))` OR |
| **slapd** | OpenLDAP server daemon; config in cn=config LDAP tree |
| **slapadd** | Offline bulk import (slapd must be stopped) |
| **ldapadd/modify** | Online add/change (slapd running, requires bind) |
| **ACLs** | Access Control Lists define who can read/write what |
| **LDAPS** | Always use TLS in production (port 636 or StartTLS) |

---

*Next: [Lab 14: REST APIs and WebSockets](lab-14-rest-apis-websockets.md)*
