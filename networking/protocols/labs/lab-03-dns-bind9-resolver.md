# Lab 03: DNS BIND9 Resolver Configuration

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

BIND9 (Berkeley Internet Name Domain) is the world's most widely deployed DNS server. In this lab you'll install BIND9, understand its configuration structure, create forward and reverse zones, validate configuration with `named-checkconf` and `named-checkzone`, explore zone transfers, configure recursion and forwarders, and use `rndc` for runtime management.

---

## Step 1: Install BIND9 and Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq &&
apt-get install -y bind9 bind9utils 2>&1 | tail -5 &&
named -V 2>&1 | head -3
"
```

📸 **Verified Output:**
```
Setting up bind9 (1:9.18.39-0ubuntu0.22.04.2) ...
Adding group 'bind' (GID 101) ...
Adding system user 'bind' (UID 101) ...
wrote key file "/etc/bind/rndc.key"
BIND 9.18.39-0ubuntu0.22.04.2-Ubuntu (Extended Support Version) <id:>
running on Linux x86_64 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC
built by make with '--build=x86_64-linux-gnu' ...
```

> 💡 **Tip:** BIND9 runs as the `bind` user by default (uid 101) — a security best practice to limit the blast radius if the daemon is compromised. The `rndc.key` is auto-generated for the control channel between `rndc` and `named`.

---

## Step 2: Understand named.conf Structure

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 -qq 2>/dev/null

echo '=== Default named.conf ==='
cat /etc/bind/named.conf
echo ''
echo '=== named.conf.options (main config) ==='
cat /etc/bind/named.conf.options
echo ''
echo '=== named.conf.local (custom zones) ==='
cat /etc/bind/named.conf.local
echo ''
echo '=== named.conf.default-zones (built-in zones) ==='
cat /etc/bind/named.conf.default-zones
"
```

📸 **Verified Output:**
```
=== Default named.conf ===
// This is the primary configuration file for the BIND DNS server named.
//
// Please read /usr/share/doc/bind9/README.Debian for information on the
// structure of BIND configuration files in Debian, *including
// Debian/Ubuntu bind9 packages*.
include "/etc/bind/named.conf.options";
include "/etc/bind/named.conf.local";
include "/etc/bind/named.conf.default-zones";

=== named.conf.options (main config) ===
options {
        directory "/var/cache/bind";
        dnssec-validation auto;
        listen-on-v6 { any; };
};
```

**named.conf anatomy:**

```
named.conf
├── named.conf.options   ← Global server settings
├── named.conf.local     ← Your custom zones (forward/reverse)
└── named.conf.default-zones ← localhost, 127.in-addr.arpa, etc.
```

**Key configuration blocks:**

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
// ============ FULL named.conf.options REFERENCE ============

options {
    // Working directory for zone files and cache
    directory \"/var/cache/bind\";

    // Listen on specific interfaces (default: all)
    listen-on { 127.0.0.1; 10.0.0.1; };
    listen-on-v6 { ::1; };

    // Limit recursive queries to trusted clients
    allow-recursion { 127.0.0.0/8; 10.0.0.0/8; 192.168.0.0/16; };

    // Allow zone transfers only to secondary servers
    allow-transfer { 10.0.0.2; };

    // Forward unresolvable queries to upstream
    forwarders { 8.8.8.8; 8.8.4.4; };
    forward only;   // 'only' = always forward; 'first' = try local first

    // DNSSEC validation
    dnssec-validation auto;

    // Response Rate Limiting (anti-amplification)
    rate-limit {
        responses-per-second 10;
        window 5;
    };

    // Disable version disclosure
    version \"not disclosed\";
};

// ============ ACL (Access Control List) ============
acl \"trusted\" {
    127.0.0.0/8;
    10.0.0.0/8;
    192.168.0.0/16;
};

// ============ ZONE TYPES ============
// master   - primary authoritative server
// slave    - secondary (gets data via zone transfer)
// forward  - forwards all queries to forwarders
// hint     - root hints (bootstraps root server discovery)
// stub     - like slave but only fetches NS records

EOF
echo 'Config reference printed'
"
```

---

## Step 3: Create a Forward Zone

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils -qq 2>/dev/null

# Create zone file
mkdir -p /etc/bind/zones
cat > /etc/bind/zones/db.lab.local << 'ZONE'
; Forward zone file for lab.local
\$ORIGIN lab.local.
\$TTL 3600

@   IN  SOA ns1.lab.local. admin.lab.local. (
        2024030501  ; Serial
        3600        ; Refresh
        900         ; Retry
        604800      ; Expire
        300         ; Negative cache TTL
    )

; Nameservers
@       IN  NS  ns1.lab.local.
@       IN  NS  ns2.lab.local.

; A records for nameservers
ns1     IN  A   10.0.0.1
ns2     IN  A   10.0.0.2

; Hosts
@       IN  A   10.0.0.10
www     IN  A   10.0.0.10
mail    IN  A   10.0.0.20
db      IN  A   10.0.0.30
app1    IN  A   10.0.0.40
app2    IN  A   10.0.0.41

; CNAME alias
intranet  IN  CNAME  www.lab.local.

; MX record
@       IN  MX  10  mail.lab.local.

; TXT for SPF
@       IN  TXT  \"v=spf1 mx ~all\"
ZONE

echo 'Zone file created:'
cat /etc/bind/zones/db.lab.local
"
```

📸 **Verified Output:**
```
Zone file created:
; Forward zone file for lab.local
$ORIGIN lab.local.
$TTL 3600

@   IN  SOA ns1.lab.local. admin.lab.local. (
        2024030501  ; Serial
...
@       IN  MX  10  mail.lab.local.
@       IN  TXT  "v=spf1 mx ~all"
```

> 💡 **Tip:** The SOA admin email `admin.lab.local.` represents `admin@lab.local` — the first dot that isn't escaped becomes `@`. Use `admin\.user.lab.local.` if your email has a dot in the username (e.g., `admin.user@lab.local`).

---

## Step 4: Create a Reverse Zone

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils -qq 2>/dev/null

mkdir -p /etc/bind/zones

cat > /etc/bind/zones/db.10.0.0 << 'ZONE'
; Reverse zone file for 10.0.0.0/24
\$ORIGIN 0.0.10.in-addr.arpa.
\$TTL 3600

@   IN  SOA ns1.lab.local. admin.lab.local. (
        2024030501  ; Serial
        3600        ; Refresh
        900         ; Retry
        604800      ; Expire
        300         ; Negative cache TTL
    )

; Nameservers
@   IN  NS  ns1.lab.local.
@   IN  NS  ns2.lab.local.

; PTR records (only last octet as name)
1   IN  PTR  ns1.lab.local.
2   IN  PTR  ns2.lab.local.
10  IN  PTR  lab.local.
10  IN  PTR  www.lab.local.
20  IN  PTR  mail.lab.local.
30  IN  PTR  db.lab.local.
40  IN  PTR  app1.lab.local.
41  IN  PTR  app2.lab.local.
ZONE

echo 'Reverse zone file created:'
cat /etc/bind/zones/db.10.0.0
"
```

📸 **Verified Output:**
```
Reverse zone file created:
; Reverse zone file for 10.0.0.0/24
$ORIGIN 0.0.10.in-addr.arpa.
$TTL 3600
...
1   IN  PTR  ns1.lab.local.
20  IN  PTR  mail.lab.local.
```

---

## Step 5: Validate Configuration with named-checkconf and named-checkzone

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils -qq 2>/dev/null
mkdir -p /etc/bind/zones

# Create zone files (abbreviated)
cat > /etc/bind/zones/db.lab.local << 'EOF'
\$ORIGIN lab.local.
\$TTL 3600
@   IN SOA ns1.lab.local. admin.lab.local. (2024030501 3600 900 604800 300)
@   IN NS  ns1.lab.local.
ns1 IN A   10.0.0.1
@   IN A   10.0.0.10
www IN A   10.0.0.10
EOF

cat > /etc/bind/zones/db.10.0.0 << 'EOF'
\$ORIGIN 0.0.10.in-addr.arpa.
\$TTL 3600
@   IN SOA ns1.lab.local. admin.lab.local. (2024030501 3600 900 604800 300)
@   IN NS  ns1.lab.local.
1   IN PTR ns1.lab.local.
10  IN PTR www.lab.local.
EOF

# Add zones to named.conf.local
cat >> /etc/bind/named.conf.local << 'CONF'
zone \"lab.local\" {
    type master;
    file \"/etc/bind/zones/db.lab.local\";
    allow-transfer { none; };
};

zone \"0.0.10.in-addr.arpa\" {
    type master;
    file \"/etc/bind/zones/db.10.0.0\";
    allow-transfer { none; };
};
CONF

echo '=== Validate named.conf ==='
named-checkconf /etc/bind/named.conf && echo 'named.conf: OK'

echo ''
echo '=== Validate forward zone ==='
named-checkzone lab.local /etc/bind/zones/db.lab.local

echo ''
echo '=== Validate reverse zone ==='
named-checkzone 0.0.10.in-addr.arpa /etc/bind/zones/db.10.0.0
"
```

📸 **Verified Output:**
```
=== Validate named.conf ===
named.conf: OK

=== Validate forward zone ===
zone lab.local/IN: loaded serial 2024030501
OK

=== Validate reverse zone ===
zone 0.0.10.in-addr.arpa/IN: loaded serial 2024030501
OK
```

> 💡 **Tip:** Always run `named-checkconf` and `named-checkzone` before reloading `named`. A syntax error in a zone file will cause `named` to refuse to load that zone — and depending on config, may prevent the whole server from starting.

---

## Step 6: rndc — Runtime Control

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils -qq 2>/dev/null

echo '=== rndc help (command list) ==='
rndc --help 2>&1 | head -30
"
```

📸 **Verified Output:**
```
=== rndc help (command list) ===
rndc: invalid argument --
Usage: rndc [-b address] [-c config] [-s server] [-p port]
	[-k key-file ] [-y key] [-r] [-V] [-4 | -6] command

command is one of the following:

  addzone zone [class [view]] { zone-options }
		Add zone to given view. Requires allow-new-zones option.
  delzone [-clean] zone [class [view]]
		Removes zone from given view.
  dnssec -checkds [-key id [-alg alg]] [-when time] (published|withdrawn) zone [class [view]]
  ...
```

**rndc command reference:**

```bash
# Reload all zones (re-read changed zone files)
rndc reload

# Reload a specific zone only
rndc reload lab.local

# Flush the resolver cache
rndc flush

# Check server status
rndc status

# Stop the server gracefully
rndc stop

# Force re-sign DNSSEC zones
rndc sign lab.local

# Add a zone at runtime (requires allow-new-zones yes)
rndc addzone example.com '{ type master; file "/etc/bind/zones/db.example.com"; };'

# Dump cache to file
rndc dumpdb -cache
```

---

## Step 7: Zone Transfer (AXFR) and Authoritative vs Recursive

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils dnsutils -qq 2>/dev/null
mkdir -p /etc/bind/zones

# Create minimal zone
cat > /etc/bind/zones/db.lab.local << 'EOF'
\$ORIGIN lab.local.
\$TTL 300
@   IN SOA ns1.lab.local. admin.lab.local. (2024030501 3600 900 604800 300)
@   IN NS  ns1.lab.local.
ns1 IN A   127.0.0.1
www IN A   10.0.0.10
mail IN A  10.0.0.20
db   IN A  10.0.0.30
EOF

cat >> /etc/bind/named.conf.local << 'CONF'
zone \"lab.local\" {
    type master;
    file \"/etc/bind/zones/db.lab.local\";
    allow-transfer { any; };   // allow AXFR for demo
};
CONF

# Start named
named -u bind -f 2>/dev/null &
NAMED_PID=\$!
sleep 2

echo '=== Query our authoritative server ==='
dig @127.0.0.1 www.lab.local A +short 2>&1

echo ''
echo '=== Zone Transfer (AXFR) - dumps entire zone ==='
dig @127.0.0.1 lab.local AXFR 2>&1

kill \$NAMED_PID 2>/dev/null || true
"
```

📸 **Verified Output:**
```
=== Query our authoritative server ===
10.0.0.10

=== Zone Transfer (AXFR) - dumps entire zone ===

; <<>> DiG 9.18.39 <<>> @127.0.0.1 lab.local AXFR
; (1 server found)
;; global options: +cmd
lab.local.		300	IN	SOA	ns1.lab.local. admin.lab.local. 2024030501 3600 900 604800 300
lab.local.		300	IN	NS	ns1.lab.local.
db.lab.local.		300	IN	A	10.0.0.30
mail.lab.local.		300	IN	A	10.0.0.20
ns1.lab.local.		300	IN	A	127.0.0.1
www.lab.local.		300	IN	A	10.0.0.10
lab.local.		300	IN	SOA	ns1.lab.local. admin.lab.local. 2024030501 3600 900 604800 300
;; Query time: 1 msec
;; SERVER: 127.0.0.1#53(127.0.0.1) (TCP)
```

**Authoritative vs Recursive:**

| Feature | Authoritative | Recursive |
|---------|--------------|-----------|
| Role | Answers for owned zones | Resolves queries on behalf of clients |
| Data source | Zone files | External nameservers |
| Recursion | Disabled | Enabled |
| Cache | No (or minimal) | Yes |
| Use case | Hosting your domains | Internal resolver for office/clients |
| Example | ns1.google.com | 8.8.8.8 |

> 💡 **Tip:** **Never run a combined authoritative+recursive server** in production. Authoritative servers should have `recursion no;` to prevent cache poisoning and amplification attacks. Use separate instances or separate views for each role.

---

## Step 8: Capstone — Full BIND9 Setup with Logging

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y bind9 bind9utils dnsutils -qq 2>/dev/null
mkdir -p /etc/bind/zones /var/log/named

# === Forward zone ===
cat > /etc/bind/zones/db.innoZverse.lab << 'EOF'
\$ORIGIN innoZverse.lab.
\$TTL 300
@    IN SOA  ns1.innoZverse.lab. ops.innoZverse.lab. (
             2024030501 3600 900 604800 300)
@    IN NS   ns1.innoZverse.lab.
ns1  IN A    127.0.0.1
www  IN A    10.10.0.100
api  IN A    10.10.0.101
gw   IN A    10.10.0.1
vpn  IN CNAME gw.innoZverse.lab.
@    IN MX   10 mail.innoZverse.lab.
mail IN A    10.10.0.200
@    IN TXT  \"v=spf1 mx ~all\"
EOF

# === named.conf.local ===
cat > /etc/bind/named.conf.local << 'CONF'
logging {
    channel default_log {
        file \"/var/log/named/named.log\" versions 3 size 5m;
        severity dynamic;
        print-category yes;
        print-severity yes;
        print-time yes;
    };
    category default { default_log; };
    category queries { default_log; };
};

zone \"innoZverse.lab\" {
    type master;
    file \"/etc/bind/zones/db.innoZverse.lab\";
    allow-transfer { none; };
};
CONF

# === Validate ===
echo '=== Configuration validation ==='
named-checkconf /etc/bind/named.conf && echo 'named.conf: VALID'
named-checkzone innoZverse.lab /etc/bind/zones/db.innoZverse.lab

# === Start and query ===
chown -R bind:bind /var/log/named 2>/dev/null || true
named -u bind -f 2>/dev/null &
NAMED_PID=\$!
sleep 2

echo ''
echo '=== Live queries to our BIND9 server ==='
for NAME in www api mail gw vpn; do
    RESULT=\$(dig @127.0.0.1 \${NAME}.innoZverse.lab +short 2>&1)
    echo \"  \${NAME}.innoZverse.lab → \${RESULT}\"
done

echo ''
echo '=== MX and TXT ==='
dig @127.0.0.1 innoZverse.lab MX +short
dig @127.0.0.1 innoZverse.lab TXT +short

kill \$NAMED_PID 2>/dev/null || true
echo ''
echo 'BIND9 server stopped. Lab complete.'
"
```

📸 **Verified Output:**
```
=== Configuration validation ===
named.conf: VALID
zone innoZverse.lab/IN: loaded serial 2024030501
OK

=== Live queries to our BIND9 server ===
  www.innoZverse.lab → 10.10.0.100
  api.innoZverse.lab → 10.10.0.101
  mail.innoZverse.lab → 10.10.0.200
  gw.innoZverse.lab → 10.10.0.1
  vpn.innoZverse.lab → 10.10.0.1

=== MX and TXT ===
10 mail.innoZverse.lab.
"v=spf1 mx ~all"

BIND9 server stopped. Lab complete.
```

---

## Summary

| Tool / Concept | Command / Detail |
|----------------|-----------------|
| Install BIND9 | `apt-get install bind9 bind9utils` |
| Main config | `/etc/bind/named.conf` |
| Custom zones | `/etc/bind/named.conf.local` |
| Zone file location | `/etc/bind/zones/` (custom) or `/var/cache/bind/` |
| Validate global config | `named-checkconf /etc/bind/named.conf` |
| Validate zone file | `named-checkzone lab.local /etc/bind/zones/db.lab.local` |
| Check server version | `named -V` |
| Reload all zones | `rndc reload` |
| Reload one zone | `rndc reload lab.local` |
| Flush cache | `rndc flush` |
| Server status | `rndc status` |
| Zone transfer | `dig @server zone AXFR` |
| Restrict recursion | `allow-recursion { trusted; };` |
| Set forwarders | `forwarders { 8.8.8.8; };` |
| SOA serial format | `YYYYMMDDnn` — increment on every change |
| Authoritative | `recursion no;` — answers only owned zones |
| Recursive | `recursion yes;` — resolves for clients |
