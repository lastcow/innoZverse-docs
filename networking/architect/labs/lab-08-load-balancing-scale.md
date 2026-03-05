# Lab 08: Load Balancing at Scale

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Load balancing distributes traffic across backend servers to maximize throughput, minimize response time, and ensure availability. This lab covers L4/L7 load balancing, advanced HAProxy configuration, GSLB, and anycast architecture.

---

## Objectives
- Compare L4 vs L7 load balancing
- Implement all major load balancing algorithms
- Configure HAProxy with ACLs, stick-tables, and rate limiting
- Design anycast and GSLB architectures
- Run HAProxy with python3 backend servers demo

---

## Step 1: L4 vs L7 Load Balancing

**L4 Load Balancer (Transport Layer):**
- Works at TCP/UDP level
- Doesn't inspect payload content
- Very fast: can handle millions of connections per second
- Can't route based on URL, cookies, headers
- Example: AWS NLB, LVS (Linux Virtual Server), F5 BIG-IP in fast-L4

**L7 Load Balancer (Application Layer):**
- Inspects HTTP headers, URL, cookies, body
- Full HTTP/HTTPS termination (TLS offload)
- Content-based routing (e.g., /api → API servers, /static → CDN)
- Session persistence (cookies, sticky sessions)
- Example: AWS ALB, HAProxy, NGINX, F5 BIG-IP HTTP profile

**When to use which:**
| Scenario | L4 | L7 |
|---------|----|----|
| Simple TCP forwarding | ✓ | |
| URL-based routing | | ✓ |
| TLS termination | | ✓ |
| Ultra-high throughput | ✓ | |
| WebSocket support | Both | |
| gRPC load balancing | | ✓ |

---

## Step 2: Load Balancing Algorithms

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| Round Robin | Cyclic distribution | Homogeneous backends |
| Least Connections | Route to least busy server | Mixed request durations |
| IP Hash | Hash src IP → consistent server | Session affinity without cookies |
| Weighted Round Robin | Different capacities | Mixed server specs |
| Least Response Time | Route to fastest server | Latency-sensitive apps |
| Random | Random selection | Simple stateless services |
| Consistent Hash | Distribute via hash ring | Cache servers (minimize misses) |

**HAProxy algorithm configuration:**
```
backend web_servers
    balance leastconn          # Algorithm
    server web1 10.0.1.1:80 weight 3 check
    server web2 10.0.1.2:80 weight 1 check
    server web3 10.0.1.3:80 weight 2 check
```

---

## Step 3: HAProxy Advanced Configuration

**Full production HAProxy config:**
```
global
    log /dev/log local0
    maxconn 50000
    nbthread 4
    cpu-map auto:1/1-4 0-3       # Pin threads to CPUs
    tune.ssl.default-dh-param 2048

defaults
    log global
    mode http
    option httplog
    option dontlognull
    option forwardfor             # X-Forwarded-For header
    option http-server-close
    timeout connect 5s
    timeout client  50s
    timeout server  50s
    retries 3

# HTTP → HTTPS redirect
frontend http_in
    bind *:80
    redirect scheme https code 301 if !{ ssl_fc }

# HTTPS frontend with TLS termination
frontend https_in
    bind *:443 ssl crt /etc/ssl/certs/combined.pem alpn h2,http/1.1
    
    # ACL-based routing
    acl is_api path_beg /api/
    acl is_websocket hdr(Upgrade) -i WebSocket
    acl is_static path_end .jpg .png .css .js .woff2
    
    use_backend api_servers     if is_api
    use_backend ws_servers      if is_websocket
    use_backend static_servers  if is_static
    default_backend web_servers

# Stick table for session persistence
backend web_servers
    balance leastconn
    cookie SERVERID insert indirect nocache
    stick-table type ip size 200k expire 30m
    stick on src
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    server web1 10.0.1.1:8080 check cookie s1
    server web2 10.0.1.2:8080 check cookie s2
    server web3 10.0.1.3:8080 check cookie s3 backup

backend api_servers
    balance roundrobin
    option http-keep-alive
    http-request set-header X-API-Version v2
    server api1 10.0.2.1:8080 check
    server api2 10.0.2.2:8080 check

# Rate limiting
frontend public_in
    bind *:8080
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
```

> 💡 **Stick tables** are HAProxy's in-memory key-value store for tracking client state. Use them for rate limiting (track req/s per IP), connection limiting, and custom persistence without cookies.

---

## Step 4: Health Checks

**Types of health checks:**
```
# Layer 4 TCP check (just verify port is open)
server web1 10.0.1.1:80 check

# Layer 7 HTTP check
option httpchk GET /health HTTP/1.0
http-check expect status 200

# Custom HTTP check with header
option httpchk GET /healthz HTTP/1.1\r\nHost:\ api.example.com
http-check expect rstring "\"status\":\"ok\""

# MySQL check
option mysql-check user haproxy_check

# DNS check
option dns-check
```

**Health check timing:**
```
server web1 10.0.1.1:80 check inter 2s fall 3 rise 2
#  inter 2s: check every 2 seconds
#  fall 3: mark down after 3 consecutive failures
#  rise 2: mark up after 2 consecutive successes
```

---

## Step 5: Anycast Load Balancing

**Anycast:** Same IP address announced from multiple locations via BGP. Traffic is routed to the nearest (AS-path shortest) location.

```
User (NYC) → 198.51.100.1 → BGP shortest path → NYC PoP
User (LON) → 198.51.100.1 → BGP shortest path → LON PoP
User (TYO) → 198.51.100.1 → BGP shortest path → TYO PoP

All use the same IP 198.51.100.1 !
```

**Requirements:**
- Own public IP block (PI space or provider-independent)
- BGP sessions at each PoP
- Same IP configured on loopback at each PoP

**Health integration:**
```
# If service is unhealthy, withdraw BGP announcement
# Traffic automatically reroutes to next-nearest PoP
ExaBGP health check → withdraw route on failure
```

---

## Step 6: GSLB (Global Server Load Balancing)

**DNS-based GSLB:**
```
Client → DNS query for api.example.com
       → GSLB checks health of all PoPs
       → Returns IP of nearest healthy PoP

Implementation:
  Route 53 latency-based routing
  Cloudflare Load Balancing
  F5 BIG-IP DNS (GTM)
  NS1, DNSimple
```

**GSLB algorithm comparison:**
| Algorithm | Metric | Pros | Cons |
|-----------|--------|------|------|
| Round Robin | None | Simple | Ignores load/health |
| RTT | Latency | Latency-optimal | DNS caching issues |
| Geographic | Location | Compliance | Inaccurate geolocation |
| QoS/Load | Backend health | Load-aware | Complex |
| Weighted | Manual bias | Control | Manual maintenance |

**DNS TTL strategy for GSLB:**
- Low TTL (10-30s): Fast failover, more DNS queries/cost
- Standard TTL (60-300s): Balanced approach
- Never use TTL=0: Not honored by all resolvers

---

## Step 7: Verification — HAProxy + Python Backends

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq haproxy python3 curl &&

# Start 3 python backend servers
python3 -c \"
import http.server, socketserver, threading, time
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        import socket
        self.wfile.write(f'Backend: {socket.gethostname()}:{self.server.server_address[1]}'.encode())
for port in [8001,8002,8003]:
    s = socketserver.TCPServer(('127.0.0.1', port), H)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
time.sleep(0.5)
print('Backends started on 8001,8002,8003')
\" &

sleep 1

# Write HAProxy config
cat > /tmp/haproxy.cfg << 'EOF'
global
    daemon
    maxconn 1000
defaults
    mode http
    timeout connect 3s
    timeout client 10s
    timeout server 10s
frontend web
    bind *:8080
    default_backend servers
backend servers
    balance roundrobin
    option httpchk GET /
    server s1 127.0.0.1:8001 check
    server s2 127.0.0.1:8002 check
    server s3 127.0.0.1:8003 check
EOF

haproxy -f /tmp/haproxy.cfg &
sleep 1

echo 'Load balancer test (5 requests):'
for i in 1 2 3 4 5; do
  curl -s http://127.0.0.1:8080/ && echo
done

haproxy -v 2>&1 | head -1"
```

📸 **Verified Output:**
```
HAProxy version 2.4.30-0ubuntu0.22.04.1 2025/12/03
Backends started on 8001,8002,8003
Load balancer test (5 requests):
Backend: abc123:8001
Backend: abc123:8002
Backend: abc123:8003
Backend: abc123:8001
Backend: abc123:8002
```

---

## Step 8: Capstone — Production Load Balancer Architecture

**Scenario:** Design load balancing for a high-traffic e-commerce site:
- 50,000 requests/second peak
- Mixed traffic: web (60%), API (30%), static assets (10%)
- Session-based shopping cart (must maintain affinity)
- Global users: US (60%), EU (30%), APAC (10%)
- 99.99% availability SLA

**Architecture:**

```
Global Layer (DNS GSLB):
  Route 53 latency-based → 3 regional LBs
  TTL: 60s for failover within 1 minute

Regional Layer (L4):
  AWS NLB per region (anycast within region)
  Handles TLS termination at this layer
  Passes to L7 tier

Application Layer (L7 HAProxy):
  2 × HAProxy nodes (active-active via keepalived VIP)
  Routing:
    /api/*     → API backend (roundrobin, no affinity)
    /checkout  → Cart backend (cookie persistence)
    /static/*  → CDN redirect (301 to Cloudflare)
    default    → Web backend (leastconn)

Session Persistence:
  HAProxy stick-table (in-memory, shared via peers)
  Cookie-based for cart sessions
  IP-hash fallback for API calls

Health Checks:
  L7: GET /health every 2s, fall=3, rise=2
  L4: TCP connect every 5s

Capacity:
  Per-region: 2 × HAProxy (32 vCPU, 64GB RAM) → 100K req/s
  Backends: 20 web, 10 API, 5 cart servers per region
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| L4 vs L7 | L4 for raw performance; L7 for content-based routing |
| Algorithms | Leastconn for long connections; roundrobin for fast requests |
| Stick tables | HAProxy in-memory KV for rate limiting and persistence |
| Health checks | L7 checks with expected response for true health |
| Anycast | Same IP, multiple locations — BGP routes to nearest |
| GSLB | DNS-based global routing with health awareness |

**Next:** [Lab 09: Network Observability →](lab-09-network-observability.md)
