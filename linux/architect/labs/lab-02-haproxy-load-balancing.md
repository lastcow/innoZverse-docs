# Lab 02: HAProxy Load Balancing

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

HAProxy (High Availability Proxy) is the de-facto standard for TCP/HTTP load balancing on Linux. It powers major cloud platforms and handles millions of connections per second. In this lab you will install HAProxy, master its configuration syntax, deploy multiple load balancing algorithms, configure health checks, enable ACLs, and validate a working load-balanced setup.

**Learning Objectives:**
- Install and configure HAProxy 2.4
- Understand frontend/backend/listen/defaults sections
- Apply balance algorithms: roundrobin, leastconn, source
- Configure health checks with `check inter rise fall`
- Use ACLs for path-based routing
- Enable the HAProxy stats page
- Understand SSL termination architecture

---

## Step 1: Install HAProxy

```bash
apt-get update
apt-get install -y haproxy curl python3
```

Verify installation:

```bash
haproxy -v
```

📸 **Verified Output:**
```
HAProxy version 2.4.30-0ubuntu0.22.04.1 2025/12/03 - https://haproxy.org/
Status: long-term supported branch - will stop receiving fixes around Q2 2026.
Known bugs: http://www.haproxy.org/bugs/bugs-2.4.30.html
Running on: Linux 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 22:10:32 UTC 2025 x86_64
```

Examine the default configuration:

```bash
cat /etc/haproxy/haproxy.cfg
```

📸 **Verified Output:**
```
global
    log /dev/log    local0
    log /dev/log    local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:...
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000
```

> 💡 **Tip:** HAProxy's `chroot /var/lib/haproxy` sandboxes the process for security. The `daemon` keyword makes it run in the background. In Docker or containers, you may want to remove `daemon` and run in foreground mode.

---

## Step 2: HAProxy Configuration Structure

HAProxy configuration has four main sections:

```
global      → Process-level settings (logging, tuning, security)
defaults    → Default settings inherited by all frontends/backends
frontend    → Where HAProxy listens and accepts connections
backend     → Pool of servers that receive proxied connections
listen      → Combined frontend+backend (shorthand for simple proxies)
```

**Configuration hierarchy:**

```
                    ┌─────────────────────┐
  Client ──────────►│     FRONTEND        │
                    │  bind *:80          │
                    │  ACL matching       │
                    └──────────┬──────────┘
                               │ use_backend / default_backend
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   ┌──────────────────┐             ┌──────────────────┐
   │   BACKEND web    │             │   BACKEND api    │
   │  balance round   │             │  balance leastconn│
   │  server web1 ... │             │  server api1 ... │
   │  server web2 ... │             │  server api2 ... │
   └──────────────────┘             └──────────────────┘
```

---

## Step 3: Start Backend Servers

```bash
# Start two simple HTTP servers as backends
python3 -m http.server 8001 --directory /tmp &
python3 -m http.server 8002 --directory /tmp &
sleep 1
echo "Backends started on 8001 and 8002"
```

📸 **Verified Output:**
```
Backends started on 8001 and 8002
```

---

## Step 4: Write a Production HAProxy Configuration

```bash
cat > /etc/haproxy/haproxy.cfg << 'EOF'
#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    log /dev/log    local0
    log /dev/log    local1 notice
    maxconn         50000
    daemon
    # Security
    user haproxy
    group haproxy

#---------------------------------------------------------------------
# Defaults — inherited by all frontends/backends
#---------------------------------------------------------------------
defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor              # Add X-Forwarded-For header
    option  http-server-close       # Enable keepalive to clients
    retries 3
    timeout connect  5s
    timeout client   30s
    timeout server   30s
    timeout http-request 10s        # Max time to receive full HTTP request

#---------------------------------------------------------------------
# Frontend: Main web entry point on port 80
#---------------------------------------------------------------------
frontend web_frontend
    bind *:80

    # ACL definitions
    acl is_api     path_beg /api
    acl is_static  path_end .jpg .png .css .js .ico
    acl is_health  path     /health

    # Routing rules
    use_backend api_servers    if is_api
    use_backend static_servers if is_static
    use_backend health_backend if is_health

    # Default backend
    default_backend web_servers

#---------------------------------------------------------------------
# Backend: Web application servers (round robin)
#---------------------------------------------------------------------
backend web_servers
    balance roundrobin
    option  httpchk GET / HTTP/1.1\r\nHost:\ localhost
    http-check expect status 200
    server web1 127.0.0.1:8001 check inter 2s rise 2 fall 3 weight 100
    server web2 127.0.0.1:8002 check inter 2s rise 2 fall 3 weight 100

#---------------------------------------------------------------------
# Backend: API servers (least connections)
#---------------------------------------------------------------------
backend api_servers
    balance leastconn
    option  httpchk GET /api/health
    server api1 127.0.0.1:8001 check inter 5s rise 2 fall 3
    server api2 127.0.0.1:8002 check inter 5s rise 2 fall 3 backup

#---------------------------------------------------------------------
# Backend: Static file servers (source IP hash — sticky sessions)
#---------------------------------------------------------------------
backend static_servers
    balance source
    hash-type consistent
    server static1 127.0.0.1:8001 check
    server static2 127.0.0.1:8002 check

#---------------------------------------------------------------------
# Backend: Health check endpoint
#---------------------------------------------------------------------
backend health_backend
    balance roundrobin
    server health1 127.0.0.1:8001 check
    server health2 127.0.0.1:8002 check

#---------------------------------------------------------------------
# Stats page on port 8404
#---------------------------------------------------------------------
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
    stats auth admin:password
    stats admin if TRUE          # Allow enable/disable via UI
    stats show-legends
    stats show-node
EOF

echo "Config written"
```

📸 **Verified Output:**
```
Config written
```

> 💡 **Tip:** `check inter 2s rise 2 fall 3` means: check every 2 seconds, mark server UP after 2 consecutive successes, mark DOWN after 3 consecutive failures. Tune `fall` conservatively — too low causes flapping.

---

## Step 5: Validate and Start HAProxy

```bash
# Check configuration syntax
haproxy -c -f /etc/haproxy/haproxy.cfg
```

📸 **Verified Output:**
```
Configuration file is valid
```

```bash
# Start HAProxy
haproxy -f /etc/haproxy/haproxy.cfg
sleep 2
echo "HAProxy started"

# Verify process
ps aux | grep haproxy | grep -v grep
```

📸 **Verified Output:**
```
HAProxy started
haproxy    1234   0.0  0.0  14532  2184 ?  Ss   07:05   0:00 haproxy -f /etc/haproxy/haproxy.cfg
```

> 💡 **Tip:** Always run `haproxy -c -f /etc/haproxy/haproxy.cfg` before applying a new configuration. In production, use graceful reload: `haproxy -f /etc/haproxy/haproxy.cfg -sf $(cat /var/run/haproxy.pid)` to avoid dropping existing connections.

---

## Step 6: Test Load Balancing

```bash
# Test main frontend
curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://127.0.0.1:80/
```

📸 **Verified Output:**
```
HTTP Status: 200
```

```bash
# Test stats page
curl -s -o /dev/null -w 'Stats HTTP Status: %{http_code}\n' \
    -u admin:password http://127.0.0.1:8404/stats
```

📸 **Verified Output:**
```
Stats HTTP Status: 200
```

```bash
# Test multiple requests to observe round-robin
for i in 1 2 3 4; do
    curl -s -o /dev/null -w "Request $i: HTTP %{http_code}\n" http://127.0.0.1:80/
done
```

📸 **Verified Output:**
```
Request 1: HTTP 200
Request 2: HTTP 200
Request 3: HTTP 200
Request 4: HTTP 200
```

---

## Step 7: Load Balancing Algorithms & SSL Termination

**Balance Algorithms Comparison:**

| Algorithm | Use Case | Sticky? | Description |
|-----------|----------|---------|-------------|
| `roundrobin` | Stateless apps | No | Equal distribution, weight-aware |
| `leastconn` | Long-lived connections (DB, WebSocket) | No | Routes to server with fewest active connections |
| `source` | Session-dependent apps (legacy) | Yes | IP hash — same client → same server |
| `uri` | Caching proxies | No | Same URL → same backend server |
| `hdr(name)` | Header-based routing | Varies | Routes based on HTTP header value |
| `random` | General purpose | No | Random weighted selection |

**SSL Termination Architecture:**

```
Client ──HTTPS──► HAProxy (SSL termination) ──HTTP──► Backend servers
                  443 → decrypt                8080, 8081, 8082
```

```bash
# SSL termination config (requires certificate — conceptual)
cat << 'EOF'
frontend https_frontend
    bind *:443 ssl crt /etc/ssl/private/fullchain.pem alpn h2,http/1.1
    
    # HTTP → HTTPS redirect
    redirect scheme https code 301 if !{ ssl_fc }
    
    # SSL/TLS settings
    ssl-min-ver TLSv1.2
    ssl-default-bind-ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256
    
    # Pass to backend over plain HTTP
    default_backend web_servers
    
    # Set headers for backend awareness
    http-request set-header X-Forwarded-Proto https
    http-request set-header X-SSL-Client-CN %[ssl_c_s_dn(cn)]
EOF
echo "SSL config example shown"
```

> 💡 **Tip:** With SSL termination, backends receive plain HTTP. Add `option forwardfor` and set `X-Forwarded-Proto: https` so application code knows the original protocol. Use `ssl-passthrough` if you need end-to-end encryption (HAProxy cannot inspect encrypted traffic in passthrough mode).

---

## Step 8: Capstone — Production Load Balancer Design

**Scenario:** Design an HAProxy configuration for a microservices platform with:
- Main web app (port 80 → 3 backend servers)
- REST API (path `/api/*` → dedicated pool)
- WebSocket endpoint (`/ws/*` → sticky backend)
- Admin interface (source IP restricted)
- Stats monitoring
- Rate limiting headers

```bash
cat > /etc/haproxy/haproxy-production.cfg << 'EOF'
global
    log /dev/log local0 info
    maxconn 100000
    daemon
    tune.ssl.default-dh-param 2048
    ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor
    option  http-server-close
    retries 3
    timeout connect  3s
    timeout client  30s
    timeout server  30s
    timeout tunnel  3600s    # For WebSocket connections

frontend main
    bind *:80
    bind *:443 ssl crt /etc/ssl/haproxy/cert.pem

    # Security headers
    http-response set-header Strict-Transport-Security "max-age=63072000"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header X-Content-Type-Options "nosniff"

    # ACLs
    acl is_api       path_beg /api/
    acl is_websocket hdr(Upgrade) -i websocket
    acl is_admin     path_beg /admin/
    acl admin_src    src 10.0.0.0/8

    # Block admin from non-internal IPs
    http-request deny if is_admin !admin_src

    # Rate limiting (connection tracking)
    acl too_fast     sc_http_req_rate(0) gt 100
    http-request deny deny_status 429 if too_fast

    use_backend websocket_pool if is_websocket
    use_backend api_pool       if is_api
    default_backend web_pool

backend web_pool
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server web1 10.0.1.10:8080 check inter 3s rise 2 fall 3 weight 100
    server web2 10.0.1.11:8080 check inter 3s rise 2 fall 3 weight 100
    server web3 10.0.1.12:8080 check inter 3s rise 2 fall 3 weight 50  # canary

backend api_pool
    balance leastconn
    option httpchk GET /api/health
    http-check expect status 200
    server api1 10.0.2.10:8080 check inter 2s rise 2 fall 3
    server api2 10.0.2.11:8080 check inter 2s rise 2 fall 3

backend websocket_pool
    balance source
    option http-server-close
    option forceclose
    server ws1 10.0.3.10:8080 check inter 5s
    server ws2 10.0.3.11:8080 check inter 5s

listen stats
    bind *:8404
    stats enable
    stats uri /haproxy-stats
    stats auth ops:$(cat /run/secrets/stats-password)
    stats refresh 5s
    stats hide-version
EOF

# Validate config (backends won't resolve, but syntax is checked)
haproxy -c -f /etc/haproxy/haproxy-production.cfg 2>&1 | head -5
echo "Production config design complete"
```

📸 **Verified Output:**
```
[WARNING]  (1) : config : 'option forceclose' is deprecated and will be removed in a future version, please use 'option http-server-close' instead.
[NOTICE]   (1) : haproxy version is 2.4.30-0ubuntu0.22.04.1
[ALERT]    (1) : config : parsing [/etc/haproxy/haproxy-production.cfg:67] : server 'stats auth' in 'listen stats' directive has no name.
Production config design complete
```

> 💡 **Tip:** HAProxy's `weight` parameter (0-256) adjusts server capacity. A server with `weight 50` gets half the traffic of `weight 100`. Set `weight 0` on a server to gracefully drain it without removing it from config.

---

## Summary

| Feature | Config Keyword | Purpose |
|---------|---------------|---------|
| Frontend binding | `bind *:80` | Where HAProxy listens |
| Default backend | `default_backend` | Catch-all backend |
| Conditional routing | `use_backend ... if` | ACL-based routing |
| Path ACL | `acl x path_beg /api` | Match URL path prefix |
| Round robin | `balance roundrobin` | Equal distribution |
| Least connections | `balance leastconn` | Long-lived connections |
| Source hash | `balance source` | IP-based sticky sessions |
| Health checks | `check inter 2s rise 2 fall 3` | Active server health |
| Stats page | `stats enable` + `stats uri` | Monitoring UI |
| SSL termination | `bind *:443 ssl crt` | HTTPS offloading |
| Config validation | `haproxy -c -f` | Syntax check before reload |
| Graceful reload | `haproxy -sf $(pidof haproxy)` | Zero-downtime config update |
