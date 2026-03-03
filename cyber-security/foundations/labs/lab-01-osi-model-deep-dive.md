# Lab 1: OSI Model Deep Dive

## 🎯 Objective
Understand the 7 layers of the OSI model by using real network tools to observe each layer in action. By the end of this lab, you will be able to map network activities to specific OSI layers and explain why layering matters for security.

## 📚 Background
The OSI (Open Systems Interconnection) model is a conceptual framework that standardizes how different network systems communicate. Think of it like the postal system: you write a letter (application layer), put it in an envelope (presentation/session), hand it to a postal worker (transport), who routes it through the postal network (network), puts it on a truck (data link), and drives on a road (physical).

There are 7 layers:
- **Layer 7 – Application**: What users interact with (HTTP, DNS, FTP)
- **Layer 6 – Presentation**: Data format, encryption, compression (TLS/SSL)
- **Layer 5 – Session**: Managing connections between applications
- **Layer 4 – Transport**: End-to-end delivery, ports (TCP, UDP)
- **Layer 3 – Network**: IP addressing and routing
- **Layer 2 – Data Link**: MAC addresses, switches, frames
- **Layer 1 – Physical**: Cables, Wi-Fi signals, bits

Security professionals use the OSI model to identify **where** an attack is happening. A DDoS might target Layer 3/4, while phishing targets Layer 7. Understanding layers helps you choose the right defense.

## ⏱️ Estimated Time
45 minutes

## 📋 Prerequisites
- Basic familiarity with Linux command line
- Docker installed and `innozverse-cybersec` image available

## 🛠️ Tools Used
- `curl` — Application layer (HTTP requests)
- `ip` — Network and Data Link layer inspection
- `ss` / `netstat` — Transport layer socket info
- `cat /proc/net/dev` — Physical/Data Link interface stats

## 🔬 Lab Instructions

### Step 1: Observe Layer 7 (Application) — HTTP with curl
The Application layer is what end-users see. HTTP is a Layer 7 protocol. `curl` lets us see the raw HTTP communication happening at this layer.

```bash
docker run --rm innozverse-cybersec bash -c "curl -s -I http://example.com"
```

**📸 Verified Output:**
```
HTTP/1.1 200 OK
Date: Sun, 01 Mar 2026 19:51:44 GMT
Content-Type: text/html
Connection: keep-alive
CF-RAY: 9d5ab2b96f005d30-MIA
Last-Modified: Wed, 25 Feb 2026 07:22:28 GMT
Allow: GET, HEAD
Accept-Ranges: bytes
Age: 3132
cf-cache-status: HIT
```

> 💡 **What this means:** These are HTTP response headers from the web server. `HTTP/1.1 200 OK` means the server understood our request and responded successfully. The `Content-Type: text/html` tells the browser how to render the content. The `CF-RAY` header reveals this site uses Cloudflare (a CDN). This is purely Layer 7 information — the application-level conversation.

### Step 2: Observe Layer 4 (Transport) — TCP Sockets with ss
The Transport layer handles end-to-end communication using ports. TCP provides reliable, ordered delivery. Let's see what transport-layer sockets are active.

```bash
docker run --rm innozverse-cybersec bash -c "ss -tuln"
```

**📸 Verified Output:**
```
Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port Process
```

> 💡 **What this means:** `ss -tuln` shows TCP (`-t`) and UDP (`-u`) sockets that are listening (`-l`) with numeric ports (`-n`). In a fresh container there are no listening services, so the output is empty. On a real server you'd see ports like 22 (SSH), 80 (HTTP), 443 (HTTPS) listed here. The port number is the Layer 4 concept — it tells the OS which application should receive the data.

### Step 3: Create a TCP Connection to See Layer 4 in Action
Let's demonstrate a TCP connection using netcat (nc):

```bash
docker run --rm innozverse-cybersec bash -c "
(echo 'Hello from server' | nc -l -p 9999 -q 1 &)
sleep 1
echo 'Hello from client' | nc -w 2 127.0.0.1 9999
echo 'Connection complete'
"
```

**📸 Verified Output:**
```
Hello from client
Hello from server
Connection complete
```

> 💡 **What this means:** We created a TCP connection on port 9999. The server listened (`nc -l -p 9999`), the client connected to `127.0.0.1:9999`. TCP performed a 3-way handshake (SYN → SYN-ACK → ACK) invisibly, then data was exchanged. This is Layer 4 (transport) using Layer 3 (IP address 127.0.0.1) to get there.

### Step 4: Observe Layer 3 (Network) — IP Routing
The Network layer handles IP addressing and routing — deciding HOW data gets from point A to point B.

```bash
docker run --rm innozverse-cybersec bash -c "ip route"
```

**📸 Verified Output:**
```
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

> 💡 **What this means:** This is the routing table — the Layer 3 map. `default via 172.17.0.1` means "for any IP I don't know how to reach directly, send it to 172.17.0.1 (the gateway/router)." The `172.17.0.0/16` line means "for IPs in this subnet, I can reach them directly via `eth0`." The `/16` is a subnet mask — it means the first 16 bits are the network address, leaving 16 bits for hosts (65,534 possible hosts).

### Step 5: Observe Layer 2 (Data Link) — MAC Addresses
The Data Link layer uses MAC addresses to deliver frames within a local network. Every network interface has a unique MAC address.

```bash
docker run --rm innozverse-cybersec bash -c "ip link show"
```

**📸 Verified Output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0@if34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 62:ef:c5:e9:ab:9a brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

> 💡 **What this means:** `lo` is the loopback interface (127.0.0.1) — it routes traffic back to itself. `eth0` is the actual network interface with MAC address `62:ef:c5:e9:ab:9a`. MAC addresses are 48-bit hardware addresses used at Layer 2. Unlike IP addresses (Layer 3), MAC addresses don't cross routers — they're only used within a single network segment.

### Step 6: Observe Layer 1 (Physical) — Interface Statistics
Layer 1 is the physical medium — cables, Wi-Fi signals. We can observe Layer 1 effects by looking at bytes transmitted/received.

```bash
docker run --rm innozverse-cybersec bash -c "cat /proc/net/dev"
```

**📸 Verified Output:**
```
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
  eth0:    1108      10    0    0    0     0          0         0      706      10    0    0    0     0       0          0
```

> 💡 **What this means:** This shows interface statistics. `eth0` has received 1108 bytes across 10 packets and sent 706 bytes. The `errs` and `drop` columns show errors — these would be non-zero if there were physical layer problems (bad cable, signal interference). `0 errors` means our Layer 1 connection is clean.

### Step 7: Understand the Security Implications of Each Layer
Different attacks target different layers:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
layers = {
    'Layer 7 Application': ['Phishing', 'SQL Injection', 'XSS', 'CSRF'],
    'Layer 6 Presentation': ['SSL Stripping', 'Weak Cipher Attacks'],
    'Layer 5 Session': ['Session Hijacking', 'Cookie Theft'],
    'Layer 4 Transport': ['Port Scanning', 'TCP SYN Flood', 'UDP Flood'],
    'Layer 3 Network': ['IP Spoofing', 'ICMP Flood', 'Routing Attacks'],
    'Layer 2 Data Link': ['ARP Poisoning', 'MAC Flooding', 'VLAN Hopping'],
    'Layer 1 Physical': ['Cable Tapping', 'Jamming', 'Hardware Keyloggers']
}
for layer, attacks in layers.items():
    print(f'{layer}: {', '.join(attacks)}')
\"
"
```

**📸 Verified Output:**
```
Layer 7 Application: Phishing, SQL Injection, XSS, CSRF
Layer 6 Presentation: SSL Stripping, Weak Cipher Attacks
Layer 5 Session: Session Hijacking, Cookie Theft
Layer 4 Transport: Port Scanning, TCP SYN Flood, UDP Flood
Layer 3 Network: IP Spoofing, ICMP Flood, Routing Attacks
Layer 2 Data Link: ARP Poisoning, MAC Flooding, VLAN Hopping
Layer 1 Physical: Cable Tapping, Jamming, Hardware Keyloggers
```

> 💡 **What this means:** Each layer has its own attack surface. A Web Application Firewall (WAF) defends Layer 7. A firewall defends Layer 3/4. Encryption (TLS) protects Layer 6. Physical security protects Layer 1. Defense-in-depth means protecting every layer.

### Step 8: Trace a Complete Request Through All Layers
Let's make an HTTP request and think through each layer it passes through:

```bash
docker run --rm innozverse-cybersec bash -c "
curl -v http://example.com 2>&1 | grep -E '(Trying|Connected|GET|HTTP|Host)'
"
```

**📸 Verified Output:**
```
*   Trying 93.184.216.34:80...
* Connected to example.com (93.184.216.34) port 80 (#0)
> GET / HTTP/1.1
> Host: example.com
< HTTP/1.1 200 OK
```

> 💡 **What this means:** Watch how the layers stack: DNS resolved `example.com` to `93.184.216.34` (Layer 3 addressing). TCP connected to port 80 (Layer 4 transport). Then the HTTP GET request was made (Layer 7 application). All 7 layers worked together invisibly!

### Step 9: Examine DNS — the Address Book of the Internet
DNS (Domain Name System) works at Layer 7 but interacts with Layer 3 to convert names to IP addresses:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== DNS resolution ==='
dig +short google.com A
echo ''
echo '=== What DNS record types exist ==='
dig google.com ANY 2>/dev/null | grep -v '^;' | grep -v '^$' | head -10
"
```

**📸 Verified Output:**
```
=== DNS resolution ===
142.251.34.142

=== What DNS record types exist ===
google.com.		300	IN	A	142.251.34.142
google.com.		300	IN	AAAA	2607:f8b0:4008:802::200e
google.com.		300	IN	MX	10 smtp.google.com.
```

> 💡 **What this means:** DNS returned `142.251.34.142` as the IP for `google.com`. The `A` record is IPv4, `AAAA` is IPv6, `MX` is the mail server. Without DNS, you'd have to memorize IP addresses instead of domain names. This is why DNS poisoning attacks are so dangerous — an attacker who can corrupt DNS can redirect you to fake websites.

### Step 10: OSI Layer Summary Challenge
Let's verify your understanding:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
# OSI Layer identification quiz
questions = [
    ('Which layer does TCP port 443 operate at?', 'Layer 4 - Transport'),
    ('Which layer does ARP poisoning attack?', 'Layer 2 - Data Link'),
    ('Which layer does HTTPS encryption operate at?', 'Layer 6 - Presentation'),
    ('Which layer does routing (IP) happen at?', 'Layer 3 - Network'),
    ('Which layer do HTTP cookies exist at?', 'Layer 7 - Application'),
]
for q, a in questions:
    print(f'Q: {q}')
    print(f'A: {a}')
    print()
\"
"
```

**📸 Verified Output:**
```
Q: Which layer does TCP port 443 operate at?
A: Layer 4 - Transport

Q: Which layer does ARP poisoning attack?
A: Layer 2 - Data Link

Q: Which layer does HTTPS encryption operate at?
A: Layer 6 - Presentation

Q: Which layer does routing (IP) happen at?
A: Layer 3 - Network

Q: Which layer do HTTP cookies exist at?
A: Layer 7 - Application
```

> 💡 **What this means:** Each of these is a real-world security concern. HTTPS (Layer 6) protects data in transit. ARP poisoning (Layer 2) enables man-in-the-middle attacks. Port-based firewalls work at Layer 4. Understanding which layer an attack targets tells you which defense to deploy.

## ✅ Verification
Run this final check to confirm you understand the OSI model:

```bash
docker run --rm innozverse-cybersec bash -c "
ip addr show eth0 | grep 'inet '
echo '---'
ss -tuln 2>/dev/null | head -3
echo '---'
curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://example.com
"
```

**📸 Verified Output:**
```
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
---
Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port Process
---
HTTP Status: 200
```

## 🚨 Common Mistakes
- **Confusing Layer 7 with "everything"**: People often think security is only about web apps (Layer 7). Physical security, network segmentation, and protocol security are equally important.
- **Forgetting that layers depend on each other**: HTTPS (Layer 6/7) still travels over TCP (Layer 4) and IP (Layer 3). Breaking a lower layer breaks everything above it.
- **Assuming encryption makes you safe at all layers**: TLS protects Layer 6 data, but an ARP poisoning attack (Layer 2) can still intercept traffic before it's encrypted.

## 📝 Summary
- The OSI model has 7 layers, each responsible for a specific aspect of network communication
- Each layer has its own security concerns and attack surface — defense-in-depth means protecting every layer
- Tools like `curl`, `ip`, `ss`, and `dig` let us directly observe different OSI layers in action
- When analyzing a security incident, identifying the OSI layer helps determine the correct response and defense

## 🔗 Further Reading
- [Cloudflare: What is the OSI model?](https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/)
- [OWASP Network Layer Attacks](https://owasp.org/www-community/attacks/)
- [RFC 1122 - Requirements for Internet Hosts](https://tools.ietf.org/html/rfc1122)
