# Lab 12: UDP and ICMP

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Not everything needs TCP's reliability. UDP and ICMP serve different purposes: UDP is the lean, fast transport for time-sensitive applications; ICMP is the network's diagnostic heartbeat. In this lab you will dissect both protocols, write UDP sockets in Python, explore ICMP internals, and use `ping` and `traceroute` to watch TTL expiry in action.

---

## UDP Datagram Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          Data ...                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**UDP Header = 8 bytes total** (compare to TCP's 20–60 bytes).

| Field | Size | Purpose |
|-------|------|---------|
| Source Port | 16 bits | Sender's port (optional, 0 if unused) |
| Destination Port | 16 bits | Target service port (DNS=53, NTP=123, DHCP=67/68) |
| Length | 16 bits | Header + data in bytes (min 8) |
| Checksum | 16 bits | Error detection (optional in IPv4, mandatory in IPv6) |

---

## ICMP Message Types

| Type | Code | Meaning |
|------|------|---------|
| 0 | 0 | Echo Reply (ping response) |
| 3 | 0–15 | Destination Unreachable (port unreach, net unreach, etc.) |
| 5 | 0–3 | Redirect |
| 8 | 0 | Echo Request (ping) |
| 11 | 0 | Time Exceeded — TTL expired (traceroute basis) |
| 11 | 1 | Time Exceeded — Fragment reassembly timeout |

---

## Step 1: Launch the Container and Install Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && \
apt-get install -y -qq python3 iproute2 iputils-ping traceroute 2>/dev/null && \
echo 'Tools ready' && \
ping -V && \
python3 --version
"
```

📸 **Verified Output:**
```
Tools ready
ping from iputils 20211215
Python 3.10.12
```

> 💡 **Tip:** ICMP runs at Layer 3 (Network), not Layer 4. It has no port numbers — it uses Type and Code fields instead.

---

## Step 2: UDP Datagram Anatomy in Python

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
python3 -c \"
import struct

# Build a raw UDP header manually
src_port   = 54321
dst_port   = 53      # DNS
data       = b'Hello UDP!'
length     = 8 + len(data)  # header + data
checksum   = 0              # simplified (0 = unused)

header = struct.pack('!HHHH', src_port, dst_port, length, checksum)
datagram = header + data

print('=== UDP Datagram Structure ===')
print(f'Source Port:      {src_port}')
print(f'Destination Port: {dst_port} (DNS)')
print(f'Length:           {length} bytes (8 header + {len(data)} data)')
print(f'Checksum:         0x{checksum:04X}')
print(f'Data:             {data!r}')
print()
print(f'Raw header bytes: {header.hex(\" \")}')
print(f'Total datagram:   {len(datagram)} bytes')
print()
print('Key insight: UDP header is ONLY 8 bytes (vs TCP 20+ bytes)')
print('No seq/ack, no flow control, no retransmission = faster!')
\"
"
```

📸 **Verified Output:**
```
=== UDP Datagram Structure ===
Source Port:      54321
Destination Port: 53 (DNS)
Length:           18 bytes (8 header + 10 data)
Checksum:         0x0000

Raw header bytes: d4 31 00 35 00 12 00 00
Total datagram:   18 bytes

Key insight: UDP header is ONLY 8 bytes (vs TCP 20+ bytes)
No seq/ack, no flow control, no retransmission = faster!
```

---

## Step 3: UDP Server and Client in Python

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 iproute2 2>/dev/null
python3 -c \"
import socket, threading, time

PORT = 5555

def udp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', PORT))
    s.settimeout(3)
    try:
        for _ in range(3):
            data, addr = s.recvfrom(1024)
            print(f'[Server] From {addr}: {data.decode()}')
            s.sendto(b'ACK: ' + data, addr)
    except socket.timeout:
        pass
    s.close()

t = threading.Thread(target=udp_server, daemon=True)
t.start()
time.sleep(0.1)

# UDP client — fire-and-forget style
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.settimeout(2)
for msg in [b'Ping!', b'DNS query sim', b'NTP sync sim']:
    c.sendto(msg, ('127.0.0.1', PORT))
    resp, _ = c.recvfrom(1024)
    print(f'[Client] Sent: {msg.decode()!r:15s} Got: {resp.decode()!r}')
c.close()
t.join(timeout=4)

print()
print('UDP characteristics demonstrated:')
print('  - No connection setup (no SYN/ACK)')
print('  - Each sendto() is an independent datagram')
print('  - Server must handle lost packets at application layer')
\"
"
```

📸 **Verified Output:**
```
[Server] From ('127.0.0.1', 47821): Ping!
[Client] Sent: 'Ping!'          Got: 'ACK: Ping!'
[Server] From ('127.0.0.1', 47821): DNS query sim
[Client] Sent: 'DNS query sim'  Got: 'ACK: DNS query sim'
[Server] From ('127.0.0.1', 47821): NTP sync sim
[Client] Sent: 'NTP sync sim'   Got: 'ACK: NTP sync sim'

UDP characteristics demonstrated:
  - No connection setup (no SYN/ACK)
  - Each sendto() is an independent datagram
  - Server must handle lost packets at application layer
```

> 💡 **Tip:** Real DNS uses UDP for queries ≤512 bytes, falling back to TCP for larger responses (zone transfers, DNSSEC). This is why DNS port 53 must be open for both TCP and UDP.

---

## Step 4: ICMP Echo Request (Ping Internals)

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 iputils-ping 2>/dev/null
python3 -c \"
import struct, socket, time

# Build ICMP Echo Request manually
ICMP_ECHO_REQUEST = 8
code = 0
identifier = 0xBEEF & 0xFFFF
sequence = 1

# Timestamp as payload (like real ping)
payload = struct.pack('d', time.time()) + b'PingPayload12345'

# Header with checksum=0 first
header = struct.pack('!BBHH', ICMP_ECHO_REQUEST, code, 0, identifier)
header += struct.pack('!H', sequence)

# Compute checksum
def checksum(data):
    if len(data) % 2:
        data += b'\\x00'
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) + data[i+1]
    s = (s >> 16) + (s & 0xFFFF)
    s += (s >> 16)
    return ~s & 0xFFFF

full = header + payload
csum = checksum(full)
header = struct.pack('!BBHH', ICMP_ECHO_REQUEST, code, csum, identifier)
header += struct.pack('!H', sequence)
packet = header + payload

print('=== ICMP Echo Request Structure ===')
print(f'Type:       {ICMP_ECHO_REQUEST} (Echo Request)')
print(f'Code:       {code}')
print(f'Checksum:   0x{csum:04X}')
print(f'Identifier: 0x{identifier:04X}')
print(f'Sequence:   {sequence}')
print(f'Payload:    {len(payload)} bytes (timestamp + padding)')
print(f'Total ICMP: {len(packet)} bytes')
print()
print('ICMP Reply (type=0) returns same identifier/sequence')
print('RTT = time(reply received) - timestamp in payload')
\"
"
```

📸 **Verified Output:**
```
=== ICMP Echo Request Structure ===
Type:       8 (Echo Request)
Code:       0
Checksum:   0xD5A3
Identifier: 0xBEEF
Sequence:   1
Payload:    24 bytes (timestamp + padding)
Total ICMP: 32 bytes

ICMP Reply (type=0) returns same identifier/sequence
RTT = time(reply received) - timestamp in payload
```

---

## Step 5: Live Ping — ICMP in Action

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iputils-ping 2>/dev/null

echo '=== ping -c 3 127.0.0.1 (standard) ==='
ping -c 3 127.0.0.1

echo ''
echo '=== ping -c 2 -s 1400 127.0.0.1 (large packets) ==='
ping -c 2 -s 1400 127.0.0.1

echo ''
echo '=== ping -c 2 -i 0.2 127.0.0.1 (fast interval) ==='
ping -c 2 -i 0.2 127.0.0.1
"
```

📸 **Verified Output:**
```
=== ping -c 3 127.0.0.1 (standard) ===
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.040 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.048 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.043 ms

--- 127.0.0.1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2033ms
rtt min/avg/max/mdev = 0.040/0.043/0.048/0.003 ms

=== ping -c 2 -s 1400 127.0.0.1 (large packets) ===
PING 127.0.0.1 (127.0.0.1) 1400(1428) bytes of data.
1408 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.077 ms
1408 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.065 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1013ms
rtt min/avg/max/mdev = 0.065/0.071/0.077/0.006 ms

=== ping -c 2 -i 0.2 127.0.0.1 (fast interval) ===
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.038 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.044 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 206ms
rtt min/avg/max/mdev = 0.038/0.041/0.044/0.003 ms
```

> 💡 **Tip:** `ping -s 56` sends 56 bytes of data + 8 ICMP header = 64 bytes payload, which is the default. The IP header adds another 20 bytes, so 84 bytes total on wire. That's why you see `56(84) bytes`.

---

## Step 6: Traceroute — TTL Expiry Mechanism

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 iputils-ping traceroute 2>/dev/null
python3 -c \"
print('=== Traceroute TTL Mechanism ===')
print()
print('How traceroute works:')
print('  1. Send packet with TTL=1 → Router 1 decrements to 0, sends ICMP Time Exceeded (type=11)')
print('  2. Send packet with TTL=2 → Router 2 decrements to 0, sends ICMP Time Exceeded')
print('  3. Continue until destination reached (sends ICMP Port Unreachable, type=3)')
print()
hops = [
    (1,  '172.17.0.1',   '0.312 ms'),
    (2,  '10.0.0.1',     '1.234 ms'),
    (3,  '192.168.1.1',  '2.891 ms'),
    (4,  '203.0.113.1',  '12.44 ms'),
    (5,  '93.184.216.34','15.22 ms'),
]
print('Simulated traceroute output:')
for ttl, ip, rtt in hops:
    print(f'  {ttl:2d}  {ip:<18} {rtt}')
print()
print('ICMP Type 11 (Time Exceeded) = TTL expired in transit')
print('ICMP Type 3  (Dest Unreach)  = Destination reached or blocked')
\"
echo ''
echo 'Live traceroute to loopback:'
traceroute -n -m 3 127.0.0.1 2>/dev/null || echo '(traceroute to localhost shows 1 hop)'
"
```

📸 **Verified Output:**
```
=== Traceroute TTL Mechanism ===

How traceroute works:
  1. Send packet with TTL=1 → Router 1 decrements to 0, sends ICMP Time Exceeded (type=11)
  2. Send packet with TTL=2 → Router 2 decrements to 0, sends ICMP Time Exceeded
  3. Continue until destination reached (sends ICMP Port Unreachable, type=3)

Simulated traceroute output:
   1  172.17.0.1         0.312 ms
   2  10.0.0.1           1.234 ms
   3  192.168.1.1        2.891 ms
   4  203.0.113.1        12.44 ms
   5  93.184.216.34      15.22 ms

ICMP Type 11 (Time Exceeded) = TTL expired in transit
ICMP Type 3  (Dest Unreach)  = Destination reached or blocked

Live traceroute to loopback:
traceroute to 127.0.0.1 (127.0.0.1), 3 hops max, 60 byte packets
 1  127.0.0.1  0.017 ms  0.009 ms  0.005 ms
```

---

## Step 7: UDP vs TCP Trade-offs

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 iproute2 2>/dev/null
python3 -c \"
import socket

print('=== UDP Socket Properties ===')
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('127.0.0.1', 5556))
print(f'Socket type: SOCK_DGRAM (UDP)')
print(f'Bound to:    127.0.0.1:5556')
print(f'No listen() needed, no accept() needed')
print()
s.close()

print('=== UDP vs TCP Comparison ===')
comparison = [
    ('Header size',      '8 bytes',            '20-60 bytes'),
    ('Connection',       'Connectionless',      'Connection-oriented (3WH)'),
    ('Reliability',      'None (best effort)',  'Guaranteed delivery'),
    ('Ordering',         'Not guaranteed',      'In-order delivery'),
    ('Flow control',     'None',                'Sliding window'),
    ('Congestion ctrl',  'None',                'Slow start, AIMD'),
    ('Use cases',        'DNS, NTP, DHCP,',     'HTTP, SSH, FTP,'),
    ('',                 'streaming, gaming',   'email, file transfer'),
    ('Latency',          'Low (no handshake)',  'Higher (setup overhead)'),
    ('Broadcast/Mcast',  'Supported',           'Unicast only'),
]
print(f'{\"Feature\":<20} {\"UDP\":<30} {\"TCP\":<30}')
print('-' * 80)
for row in comparison:
    print(f'{row[0]:<20} {row[1]:<30} {row[2]:<30}')
\"
echo ''
echo 'Active UDP sockets:'
ss -unp
"
```

📸 **Verified Output:**
```
=== UDP Socket Properties ===
Socket type: SOCK_DGRAM (UDP)
Bound to:    127.0.0.1:5556
No listen() needed, no accept() needed

=== UDP vs TCP Comparison ===
Feature              UDP                            TCP
--------------------------------------------------------------------------------
Header size          8 bytes                        20-60 bytes
Connection           Connectionless                 Connection-oriented (3WH)
Reliability          None (best effort)             Guaranteed delivery
Ordering             Not guaranteed                 In-order delivery
Flow control         None                           Sliding window
Congestion ctrl      None                           Slow start, AIMD
Use cases            DNS, NTP, DHCP,                HTTP, SSH, FTP,
                     streaming, gaming              email, file transfer
Latency              Low (no handshake)             Higher (setup overhead)
Broadcast/Mcast      Supported                      Unicast only

Active UDP sockets:
Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
```

---

## Step 8: Capstone — Simulated DNS over UDP

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 iproute2 2>/dev/null
python3 -c \"
import socket, threading, time, struct

DNS_PORT = 5353

# Minimal DNS response simulator
def dns_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', DNS_PORT))
    s.settimeout(3)
    db = {
        'example.com':  '93.184.216.34',
        'google.com':   '142.250.80.46',
        'unknown.xyz':  None,
    }
    try:
        for _ in range(3):
            data, addr = s.recvfrom(512)  # DNS max UDP = 512 bytes
            query = data.decode(errors='replace').strip()
            ip = db.get(query)
            if ip:
                resp = f'ANSWER: {query} → {ip} (A record, TTL=300)'.encode()
            else:
                resp = f'NXDOMAIN: {query} not found'.encode()
            s.sendto(resp, addr)
    except socket.timeout:
        pass
    s.close()

t = threading.Thread(target=dns_server, daemon=True)
t.start()
time.sleep(0.1)

domains = ['example.com', 'google.com', 'unknown.xyz']
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.settimeout(2)

print('=== Simulated DNS over UDP ===')
print(f'{\"Query\":<20} {\"Response\"}')
print('-' * 60)
for domain in domains:
    c.sendto(domain.encode(), ('127.0.0.1', DNS_PORT))
    resp, _ = c.recvfrom(512)
    print(f'{domain:<20} {resp.decode()}')
c.close()
t.join(timeout=4)

print()
print('Key UDP properties demonstrated:')
print('  - Each query is an independent datagram (no connection)')
print('  - Request/response fits in single UDP packet')
print('  - 512-byte limit is real DNS/UDP constraint (RFC 1035)')
print('  - Port 5353 = mDNS (multicast DNS), real DNS = 53')
\"
"
```

📸 **Verified Output:**
```
=== Simulated DNS over UDP ===
Query                Response
------------------------------------------------------------
example.com          ANSWER: example.com → 93.184.216.34 (A record, TTL=300)
google.com           ANSWER: google.com → 142.250.80.46 (A record, TTL=300)
unknown.xyz          NXDOMAIN: unknown.xyz not found

Key UDP properties demonstrated:
  - Each query is an independent datagram (no connection)
  - Request/response fits in single UDP packet
  - 512-byte limit is real DNS/UDP constraint (RFC 1035)
  - Port 5353 = mDNS (multicast DNS), real DNS = 53
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **UDP Header** | 8 bytes: src port, dst port, length, checksum — that's it |
| **UDP Use Cases** | DNS (latency matters), NTP (timing), DHCP (broadcast), streaming, gaming |
| **No Connection** | sendto()/recvfrom() — no handshake, no state, no retransmission |
| **ICMP Type 8/0** | Echo Request / Echo Reply — the ping mechanism |
| **ICMP Type 3** | Destination Unreachable — firewall blocks, wrong port |
| **ICMP Type 11** | Time Exceeded — TTL hit zero; used by traceroute |
| **Traceroute** | Sends packets with TTL=1,2,3... collecting ICMP type-11 replies from each router |
| **ping -c N** | Send N ICMP echo requests |
| **ping -s SIZE** | Set payload size (default 56 bytes) |
| **`ss -unp`** | List active UDP sockets |
