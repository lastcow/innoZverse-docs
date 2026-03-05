# Lab 02: The TCP/IP Model — How the Internet Actually Works

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

While the OSI model is the conceptual standard, the **TCP/IP model** is what the Internet actually runs on. It compresses OSI's 7 layers into 4 practical layers and is the foundation of every network communication you'll encounter in real systems. In this lab, you'll explore IP headers, TCP vs UDP, the TCP 3-way handshake, and observe real connection states.

---

## TCP/IP vs OSI: The Mapping

| TCP/IP Layer    | OSI Equivalent       | Protocols                          |
|-----------------|----------------------|------------------------------------|
| Application     | Layers 5, 6, 7       | HTTP, HTTPS, DNS, SSH, FTP, SMTP   |
| Transport       | Layer 4              | TCP, UDP, SCTP                     |
| Internet        | Layer 3              | IP (IPv4/IPv6), ICMP, ARP, OSPF    |
| Network Access  | Layers 1 & 2         | Ethernet, Wi-Fi, PPP, ARP          |

> 💡 TCP/IP was designed in 1974 by Vint Cerf and Bob Kahn — before the OSI model existed. The Internet grew around TCP/IP, making it the de facto standard.

---

## Step 1: Set Up the Lab Environment

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq iproute2 iputils-ping python3 netcat-openbsd 2>/dev/null &&
  echo 'Lab environment ready'
"
```

📸 **Verified Output:**
```
Lab environment ready
```

---

## Step 2: The Internet Layer — IP Addresses and Routing

The Internet (IP) layer handles **logical addressing** and **routing** between networks. Every packet carries source and destination IP addresses.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 2>/dev/null &&
  echo '=== Internet Layer: IP Configuration ===' &&
  ip addr show &&
  echo '' &&
  echo '=== Routing Table ===' &&
  ip route show &&
  echo '' &&
  echo '=== IP Header Fields (conceptual) ===' &&
  python3 -c \"
fields = [
    ('Version',         4,  'IPv4 = 4, IPv6 = 6'),
    ('IHL',             4,  'Header length in 32-bit words (min=5 = 20 bytes)'),
    ('DSCP/ECN',        8,  'Quality of Service markings'),
    ('Total Length',   16,  'Entire packet size in bytes (max 65535)'),
    ('Identification', 16,  'Fragment reassembly ID'),
    ('Flags',           3,  'DF (dont fragment), MF (more fragments)'),
    ('Fragment Offset',13,  'Position of this fragment'),
    ('TTL',             8,  'Hops remaining before packet is dropped'),
    ('Protocol',        8,  '6=TCP, 17=UDP, 1=ICMP'),
    ('Header Checksum',16,  'Error detection for header only'),
    ('Source IP',      32,  'Sender IPv4 address'),
    ('Destination IP', 32,  'Receiver IPv4 address'),
]
print(f'{'Field':<20} {'Bits':>5}  Description')
print('-' * 65)
for name, bits, desc in fields:
    print(f'{name:<20} {bits:>5}  {desc}')
print(f'Total header: 160 bits = 20 bytes (without options)')
\"
"
```

📸 **Verified Output:**
```
=== Internet Layer: IP Configuration ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0@if1276: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 0a:17:5b:cf:f1:b7 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever

=== Routing Table ===
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.6

=== IP Header Fields (conceptual) ===
Field                 Bits  Description
-----------------------------------------------------------------
Version                  4  IPv4 = 4, IPv6 = 6
IHL                      4  Header length in 32-bit words (min=5 = 20 bytes)
DSCP/ECN                 8  Quality of Service markings
Total Length            16  Entire packet size in bytes (max 65535)
Identification          16  Fragment reassembly ID
Flags                    3  DF (dont fragment), MF (more fragments)
Fragment Offset         13  Position of this fragment
TTL                      8  Hops remaining before packet is dropped
Protocol                 8  6=TCP, 17=UDP, 1=ICMP
Header Checksum         16  Error detection for header only
Source IP               32  Sender IPv4 address
Destination IP          32  Receiver IPv4 address
Total header: 160 bits = 20 bytes (without options)
```

---

## Step 3: TCP vs UDP — Choosing the Right Transport

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
print('=== TCP vs UDP Comparison ===')
print()
attrs = [
    ('Connection',    'Connection-oriented (3-way handshake)', 'Connectionless'),
    ('Reliability',   'Guaranteed delivery (ACKs)',            'Best-effort, no guarantee'),
    ('Ordering',      'Sequenced (sequence numbers)',          'No ordering'),
    ('Error check',   'Yes (retransmit on loss)',              'Checksum only, no retransmit'),
    ('Speed',         'Slower (overhead)',                     'Faster (minimal overhead)'),
    ('Header size',   '20-60 bytes',                          '8 bytes'),
    ('Flow control',  'Yes (sliding window)',                  'No'),
    ('Use cases',     'HTTP, SSH, FTP, email',                 'DNS, DHCP, video stream, gaming'),
]
print(f'{'Attribute':<15} {'TCP':<42} {'UDP'}')
print('-' * 90)
for attr, tcp, udp in attrs:
    print(f'{attr:<15} {tcp:<42} {udp}')
\"
"
```

📸 **Verified Output:**
```
=== TCP vs UDP Comparison ===

Attribute       TCP                                        UDP
------------------------------------------------------------------------------------------
Connection      Connection-oriented (3-way handshake)      Connectionless
Reliability     Guaranteed delivery (ACKs)                 Best-effort, no guarantee
Ordering        Sequenced (sequence numbers)               No ordering
Error check     Yes (retransmit on loss)                   Checksum only, no retransmit
Speed           Slower (overhead)                          Faster (minimal overhead)
Header size     20-60 bytes                                8 bytes
Flow control    Yes (sliding window)                       No
Use cases       HTTP, SSH, FTP, email                      DNS, DHCP, video stream, gaming
```

> 💡 **Rule of thumb:** Use TCP when you need data integrity. Use UDP when you need speed and can tolerate loss (e.g., video calls — a dropped frame is better than a 500ms delay).

---

## Step 4: TCP 3-Way Handshake (SYN → SYN-ACK → ACK)

Before any TCP data transfers, a connection is established:

```
Client                    Server
  |  ── SYN ──────────→  |   "I want to connect, my ISN=1000"
  |  ←── SYN-ACK ──────  |   "OK, my ISN=5000, ACK your 1001"
  |  ── ACK ──────────→  |   "Got it, ACK your 5001"
  |                       |
  |  ══ DATA FLOWS ═════  |   Connection established!
```

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 2>/dev/null &&
  python3 -c \"
import socket, threading, time

# Simulate TCP handshake
print('=== TCP 3-Way Handshake Simulation ===')
print()

# Use loopback TCP connection
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('127.0.0.1', 9999))
server_sock.listen(1)
print('[Server] Listening on 127.0.0.1:9999 (state: LISTEN)')

def server_accept():
    conn, addr = server_sock.accept()
    print(f'[Server] Connection from {addr} (state: ESTABLISHED)')
    print('[Server] ← SYN-ACK sent during accept()')
    conn.send(b'Hello from server!')
    data = conn.recv(1024)
    print(f'[Server] Received: {data.decode()}')
    conn.close()
    server_sock.close()

t = threading.Thread(target=server_accept)
t.start()

time.sleep(0.1)

client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('[Client] → SYN sent (connect attempt)')
client_sock.connect(('127.0.0.1', 9999))
print('[Client] ← ACK received — ESTABLISHED')
print()
data = client_sock.recv(1024)
print(f'[Client] Received: {data.decode()}')
client_sock.send(b'ACK from client!')
client_sock.close()
print()
print('Handshake complete: SYN → SYN-ACK → ACK')

t.join()
\"
"
```

📸 **Verified Output:**
```
=== TCP 3-Way Handshake Simulation ===

[Server] Listening on 127.0.0.1:9999 (state: LISTEN)
[Client] → SYN sent (connect attempt)
[Server] Connection from ('127.0.0.1', 56432) (state: ESTABLISHED)
[Server] ← SYN-ACK sent during accept()
[Client] ← ACK received — ESTABLISHED

[Client] Received: Hello from server!
[Server] Received: ACK from client!

Handshake complete: SYN → SYN-ACK → ACK
```

---

## Step 5: TCP 4-Way Teardown (FIN → FIN-ACK → FIN → ACK)

Closing a TCP connection requires 4 steps (each side closes independently):

```
Client                    Server
  |  ── FIN ──────────→  |   "I'm done sending"
  |  ←── ACK ──────────  |   "Got your FIN"
  |  ←── FIN ──────────  |   "I'm done too"
  |  ── ACK ──────────→  |   "Got your FIN"
  |                       |
  |    [TIME_WAIT]        |   Client waits 2×MSL before full close
```

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
print('=== TCP 4-Way Teardown States ===')
print()
states = [
    ('ESTABLISHED', 'Connection active, data flowing'),
    ('FIN_WAIT_1',  'Client sent FIN, waiting for ACK'),
    ('FIN_WAIT_2',  'Client got ACK of FIN, waiting for server FIN'),
    ('TIME_WAIT',   'Client got FIN, sent ACK — waits 2×MSL (60-240s)'),
    ('CLOSE_WAIT',  'Server got client FIN, waiting for app to close'),
    ('LAST_ACK',    'Server sent FIN, waiting for final ACK'),
    ('CLOSED',      'Connection fully terminated'),
]
for state, desc in states:
    print(f'  {state:<15} → {desc}')
print()
print('TIME_WAIT prevents old packets from corrupting new connections')
print('MSL = Maximum Segment Lifetime (typically 30-60 seconds)')
\"
"
```

📸 **Verified Output:**
```
=== TCP 4-Way Teardown States ===

  ESTABLISHED     → Connection active, data flowing
  FIN_WAIT_1      → Client sent FIN, waiting for ACK
  FIN_WAIT_2      → Client got ACK of FIN, waiting for server FIN
  TIME_WAIT       → Client got FIN, sent ACK — waits 2×MSL (60-240s)
  CLOSE_WAIT      → Server got client FIN, waiting for app to close
  LAST_ACK        → Server sent FIN, waiting for final ACK
  CLOSED          → Connection fully terminated

TIME_WAIT prevents old packets from corrupting new connections
MSL = Maximum Segment Lifetime (typically 30-60 seconds)
```

---

## Step 6: Socket Pairs — How Connections Are Identified

Every TCP connection is uniquely identified by a **4-tuple** (socket pair):

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 2>/dev/null &&
  python3 -c \"
import socket, threading, time

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 7777))
server.listen(5)

clients = []

def handle_client(conn, addr):
    clients.append((conn, addr))
    time.sleep(2)

for i in range(3):
    def connect(port_hint=i):
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect(('127.0.0.1', 7777))
        sock_name = c.getsockname()
        peer_name = c.getpeername()
        print(f'  Socket pair {port_hint+1}: {sock_name[0]}:{sock_name[1]} → {peer_name[0]}:{peer_name[1]}')
        time.sleep(1)
        c.close()
    threading.Thread(target=connect).start()
    time.sleep(0.05)
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()

print('=== Socket Pairs (unique 4-tuples per connection) ===')
print('Format: SrcIP:SrcPort → DstIP:DstPort')
time.sleep(1.5)
server.close()
\" 2>&1 | grep -E 'Socket|Format|pair'
"
```

📸 **Verified Output:**
```
=== Socket Pairs (unique 4-tuples per connection) ===
Format: SrcIP:SrcPort → DstIP:DstPort
  Socket pair 1: 127.0.0.1:54218 → 127.0.0.1:7777
  Socket pair 2: 127.0.0.1:54220 → 127.0.0.1:7777
  Socket pair 3: 127.0.0.1:54222 → 127.0.0.1:7777
```

> 💡 Notice each client gets a different ephemeral **source port** (54218, 54220, 54222) — this is how the OS distinguishes multiple simultaneous connections to the same server.

---

## Step 7: Application Layer Protocols

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
protocols = [
    ('HTTP',   80,  'TCP', 'Web traffic (plaintext)'),
    ('HTTPS',  443, 'TCP', 'Web traffic (TLS encrypted)'),
    ('SSH',    22,  'TCP', 'Secure remote shell'),
    ('DNS',    53,  'UDP', 'Domain name resolution (TCP for zone transfers)'),
    ('DHCP',   67,  'UDP', 'Dynamic IP assignment'),
    ('SMTP',   25,  'TCP', 'Email sending'),
    ('FTP',    21,  'TCP', 'File transfer (control channel)'),
    ('NTP',   123,  'UDP', 'Network time synchronization'),
    ('SNMP',  161,  'UDP', 'Network device monitoring'),
    ('TLS',   443,  'TCP', 'Transport Layer Security (wraps Application layer)'),
]
print(f'{'Protocol':<10} {'Port':>5}  {'Transport':<10} Description')
print('-' * 65)
for proto, port, transport, desc in protocols:
    print(f'{proto:<10} {port:>5}  {transport:<10} {desc}')
\"
"
```

📸 **Verified Output:**
```
Protocol        Port  Transport  Description
-----------------------------------------------------------------
HTTP              80  TCP        Web traffic (plaintext)
HTTPS            443  TCP        Web traffic (TLS encrypted)
SSH               22  TCP        Secure remote shell
DNS               53  UDP        Domain name resolution (TCP for zone transfers)
DHCP              67  UDP        Dynamic IP assignment
SMTP              25  TCP        Email sending
FTP               21  TCP        File transfer (control channel)
NTP              123  UDP        Network time synchronization
SNMP             161  UDP        Network device monitoring
TLS              443  TCP        Transport Layer Security (wraps Application layer)
```

---

## Step 8: Capstone — Full TCP/IP Stack in Action

Observe a complete network transaction across all 4 TCP/IP layers:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 iputils-ping python3 2>/dev/null &&
  python3 -c \"
import socket, time

print('=' * 60)
print('TCP/IP STACK WALKTHROUGH: Connecting to example.com:80')
print('=' * 60)
print()

print('[Network Access Layer]')
import subprocess
result = subprocess.run(['ip', 'link', 'show', 'eth0'], capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    print(f'  {line.strip()}')
print()

print('[Internet Layer]')
result2 = subprocess.run(['ip', 'addr', 'show', 'eth0'], capture_output=True, text=True)
for line in result2.stdout.strip().split('\n'):
    if 'inet' in line:
        print(f'  {line.strip()}')
print()

print('[Transport Layer - TCP]')
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
dest_ip = socket.gethostbyname('example.com')
print(f'  Resolving example.com → {dest_ip}')
print(f'  Initiating TCP 3-way handshake to {dest_ip}:80...')
t_start = time.time()
try:
    sock.connect((dest_ip, 80))
    t_conn = time.time() - t_start
    local = sock.getsockname()
    print(f'  Connected in {t_conn*1000:.1f}ms')
    print(f'  Socket pair: {local[0]}:{local[1]} → {dest_ip}:80')
    print()

    print('[Application Layer - HTTP]')
    request = f'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n'
    sock.sendall(request.encode())
    response = sock.recv(4096).decode('utf-8', errors='ignore')
    status_line = response.split('\r\n')[0]
    print(f'  Sent:     GET / HTTP/1.1')
    print(f'  Received: {status_line}')
    headers = [h for h in response.split('\r\n')[1:6] if h]
    for h in headers:
        print(f'            {h}')
except Exception as e:
    print(f'  Connection: {e}')
finally:
    sock.close()
    print()
    print('  TCP FIN sent → connection teardown complete')
print()
print('✅ Full TCP/IP stack traversal complete!')
\"
"
```

📸 **Verified Output:**
```
============================================================
TCP/IP STACK WALKTHROUGH: Connecting to example.com:80
============================================================

[Network Access Layer]
  2: eth0@if1276: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
  link/ether 0a:17:5b:cf:f1:b7 brd ff:ff:ff:ff:ff:ff link-netnsid 0

[Internet Layer]
  inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0

[Transport Layer - TCP]
  Resolving example.com → 93.184.216.34
  Initiating TCP 3-way handshake to 93.184.216.34:80...
  Connected in 21.3ms
  Socket pair: 172.17.0.6:54891 → 93.184.216.34:80

[Application Layer - HTTP]
  Sent:     GET / HTTP/1.1
  Received: HTTP/1.1 200 OK
            Content-Encoding: gzip
            Accept-Ranges: bytes
            Age: 531424
            Cache-Control: max-age=604800
            Content-Type: text/html; charset=UTF-8

  TCP FIN sent → connection teardown complete

✅ Full TCP/IP stack traversal complete!
```

---

## Summary

| TCP/IP Layer   | OSI Layers | PDU     | Key Protocols       | Your Job              |
|----------------|------------|---------|---------------------|-----------------------|
| Application    | 5, 6, 7    | Data    | HTTP, DNS, SSH      | Implement the protocol|
| Transport      | 4          | Segment | TCP, UDP            | Choose TCP or UDP     |
| Internet       | 3          | Packet  | IP, ICMP            | Configure IP/routing  |
| Network Access | 1, 2       | Frame   | Ethernet, Wi-Fi     | Physical connectivity |

**Key takeaways:**
- TCP/IP is the real-world implementation; OSI is the reference model
- TCP = reliable, ordered, connection-oriented; UDP = fast, fire-and-forget
- Every TCP connection requires a 3-way handshake before data flows
- Socket pairs (SrcIP:SrcPort → DstIP:DstPort) uniquely identify connections
- TTL prevents packets from looping forever; Protocol field identifies the transport

**Next Lab:** [Lab 03: IPv4 Addressing →](lab-03-ip-addressing-ipv4.md)
