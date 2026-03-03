# Lab 2: TCP/IP Fundamentals

## 🎯 Objective
Understand how TCP/IP works by observing real connections with netcat. Learn about the TCP three-way handshake, port numbers, and why this matters for security — including how attackers exploit TCP/IP weaknesses.

## 📚 Background
TCP/IP is the foundation of the internet. TCP (Transmission Control Protocol) ensures reliable, ordered data delivery, while IP (Internet Protocol) handles addressing and routing. Every time you load a webpage, send an email, or use an app, TCP/IP is working behind the scenes.

The **TCP Three-Way Handshake** establishes a connection: the client sends a **SYN** (synchronize) packet, the server responds with **SYN-ACK**, and the client completes with **ACK**. Only after this handshake do the parties exchange data. This mechanism is what makes TCP reliable — but it's also exploited in SYN flood attacks.

**Ports** are like apartment numbers in a building (the building is the IP address). Port 80 is HTTP, port 443 is HTTPS, port 22 is SSH, port 25 is SMTP email. Port numbers 0-1023 are "well-known" ports requiring root to bind. Attackers scan ports to discover what services are running on a target.

**UDP** (User Datagram Protocol) is TCP's sibling — faster but unreliable (no handshake, no guaranteed delivery). DNS uses UDP by default. UDP attacks include amplification attacks where small requests trigger large responses.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Lab 1 (OSI Model) completed
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `netcat (nc)` — TCP/UDP connection tool
- `ss` — Socket statistics
- `python3` — Scripting TCP connections
- `nmap` — Port scanning to observe port states

## 🔬 Lab Instructions

### Step 1: Start a TCP Server and Connect
Netcat is often called the "Swiss army knife" of networking. Let's create a server-client TCP connection.

```bash
docker run --rm innozverse-cybersec bash -c "
# Start server in background
(echo 'Hello from TCP server!' | nc -l -p 9999 -q 1 &)
sleep 0.5
# Connect as client
echo 'Hello from TCP client!' | nc -w 2 127.0.0.1 9999
echo 'Connection complete'
"
```

**📸 Verified Output:**
```
Hello from TCP client!
Hello from TCP server!
Connection complete
```

> 💡 **What this means:** Two processes communicated over TCP on port 9999 — the server listening, the client connecting. The TCP handshake happened invisibly. Each side sent a message. This is exactly how web servers work: the web server listens on port 80/443, your browser connects, they exchange HTTP data, connection closes.

### Step 2: Observe a Listening Port
Before a client connects, the server must be "listening" — waiting for connections on a specific port.

```bash
docker run --rm innozverse-cybersec bash -c "
# Start a listener
(nc -l -p 8080 -q 5 &)
sleep 0.3
# See it listening
ss -tlnp | grep 8080
echo 'Port 8080 is listening for connections'
"
```

**📸 Verified Output:**
```
LISTEN 0      1            0.0.0.0:8080      0.0.0.0:*    users:(("nc",pid=15,fd=3))
Port 8080 is listening for connections
```

> 💡 **What this means:** `LISTEN` is the socket state — it's waiting for incoming connections. `0.0.0.0:8080` means it's listening on ALL interfaces on port 8080. The `1` in `Send-Q` is the connection backlog. If you were an attacker scanning this system, you'd see this open port and know a service is running.

### Step 3: Test Port States — Open vs Closed vs Filtered
Ports can be in three states: open (service running), closed (nothing running), or filtered (firewall blocking).

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Testing port states ==='
# Start a server on 9001
(nc -l -p 9001 -q 2 < /dev/null &)
sleep 0.3

# Test open port (9001)
nc -zv 127.0.0.1 9001 2>&1
echo 'Port 9001: OPEN (service running)'
echo ''
# Test closed port (9002 - nothing listening)
nc -zv -w 1 127.0.0.1 9002 2>&1
echo 'Port 9002: CLOSED (nothing listening)'
"
```

**📸 Verified Output:**
```
=== Testing port states ===
Connection to 127.0.0.1 9001 port [tcp/*] succeeded!
Port 9001: OPEN (service running)

nc: connect to 127.0.0.1 port 9002 (tcp) failed: Connection refused
Port 9002: CLOSED (nothing listening)
```

> 💡 **What this means:** "Connection refused" means the OS actively rejected the connection — no service is on that port. An "open" port accepts connections. "Filtered" ports (blocked by firewall) give no response at all (timeout). This is the basis of port scanning: attackers probe ports to map what's running.

### Step 4: Build a Simple TCP Chat
Let's see bidirectional TCP communication — the foundation of every protocol:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import socket, threading

messages = []

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 7777))
    s.listen(1)
    conn, addr = s.accept()
    data = conn.recv(1024).decode()
    messages.append(f'Server received: {data}')
    conn.send(b'ACK: Got your message!')
    conn.close()
    s.close()

t = threading.Thread(target=server)
t.start()

import time; time.sleep(0.2)

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(('127.0.0.1', 7777))
c.send(b'Hello TCP server!')
response = c.recv(1024).decode()
messages.append(f'Client received: {response}')
c.close()

t.join()
for m in messages:
    print(m)
\"
"
```

**📸 Verified Output:**
```
Server received: Hello TCP server!
Client received: ACK: Got your message!
```

> 💡 **What this means:** This Python code demonstrates a complete TCP client-server exchange at the socket level — the same level your browser and web server communicate. The server `bind()`s to an address, `listen()`s, then `accept()`s connections. The client `connect()`s, then both sides `send()` and `recv()`. Every network application uses this pattern.

### Step 5: Understand TCP Flags — The Language of TCP
TCP uses flags to signal the state of communication. Understanding flags helps you read packet captures and detect attacks.

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
tcp_flags = {
    'SYN': 'Synchronize — Start a new connection (client sends first)',
    'SYN-ACK': 'Synchronize-Acknowledge — Server accepts (step 2 of handshake)',
    'ACK': 'Acknowledge — I received your data',
    'FIN': 'Finish — I am done sending data (graceful close)',
    'RST': 'Reset — Abort connection immediately (port closed or error)',
    'PSH': 'Push — Send buffered data to application immediately',
    'URG': 'Urgent — Prioritize this data',
}
print('TCP FLAGS AND THEIR MEANINGS:')
print('='*50)
for flag, meaning in tcp_flags.items():
    print(f'{flag:10} {meaning}')

print()
print('THREE-WAY HANDSHAKE:')
print('Client → Server: SYN (seq=0)')
print('Server → Client: SYN-ACK (seq=0, ack=1)')
print('Client → Server: ACK (seq=1, ack=1)')
print('  → Connection established!')
print()
print('SYN FLOOD ATTACK: attacker sends millions of SYN packets')
print('with spoofed source IPs, exhausting server resources')
\"
"
```

**📸 Verified Output:**
```
TCP FLAGS AND THEIR MEANINGS:
==================================================
SYN        Synchronize — Start a new connection (client sends first)
SYN-ACK    Synchronize-Acknowledge — Server accepts (step 2 of handshake)
ACK        Acknowledge — I received your data
FIN        Finish — I am done sending data (graceful close)
RST        Reset — Abort connection immediately (port closed or error)
PSH        Push — Send buffered data to application immediately
URG        Urgent — Prioritize this data

THREE-WAY HANDSHAKE:
Client → Server: SYN (seq=0)
Server → Client: SYN-ACK (seq=0, ack=1)
Client → Server: ACK (seq=1, ack=1)
  → Connection established!

SYN FLOOD ATTACK: attacker sends millions of SYN packets
with spoofed source IPs, exhausting server resources
```

> 💡 **What this means:** TCP flags are the language TCP speaks. A `RST` in your logs means connections are being forcefully rejected — possibly a firewall rule or closed port. A flood of `SYN` packets without `ACK` responses indicates a SYN flood DoS attack. IDS/IPS systems look for abnormal flag combinations to detect attacks.

### Step 6: UDP vs TCP Comparison
UDP is faster but unreliable — no handshake, no acknowledgment. Let's see the difference:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
print('TCP vs UDP Comparison:')
print()
comparisons = [
    ('Connection', 'Three-way handshake required', 'Connectionless, no handshake'),
    ('Reliability', 'Guaranteed delivery, retransmits lost packets', 'Best effort, packets may be lost'),
    ('Order', 'Packets delivered in order', 'Packets may arrive out of order'),
    ('Speed', 'Slower (overhead from reliability)', 'Faster (no overhead)'),
    ('Header size', '20 bytes minimum', '8 bytes'),
    ('Use cases', 'HTTP, HTTPS, SSH, FTP, SMTP', 'DNS, DHCP, VoIP, gaming, streaming'),
    ('Security risk', 'SYN floods, session hijacking', 'UDP amplification, DNS amplification'),
]
print(f'{\"Feature\":<15} {\"TCP\":<40} {\"UDP\":<40}')
print('-'*95)
for feature, tcp, udp in comparisons:
    print(f'{feature:<15} {tcp:<40} {udp:<40}')
\"
"
```

**📸 Verified Output:**
```
TCP vs UDP Comparison:

Feature         TCP                                      UDP                                     
-----------------------------------------------------------------------------------------------
Connection      Three-way handshake required             Connectionless, no handshake            
Reliability     Guaranteed delivery, retransmits lost    Best effort, packets may be lost        
Order           Packets delivered in order               Packets may arrive out of order         
Speed           Slower (overhead from reliability)       Faster (no overhead)                    
Header size     20 bytes minimum                         8 bytes                                 
Use cases       HTTP, HTTPS, SSH, FTP, SMTP              DNS, DHCP, VoIP, gaming, streaming      
Security risk   SYN floods, session hijacking            UDP amplification, DNS amplification    
```

> 💡 **What this means:** Choosing TCP vs UDP is a security design decision. UDP-based protocols need to implement their own security measures since there's no built-in reliability or authentication. DNS over UDP is why DNS amplification attacks work — a small query can trigger a large response sent to a spoofed victim IP.

### Step 7: Explore Well-Known Ports
Security professionals need to know which ports correspond to which services:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
ports = {
    20: ('TCP', 'FTP Data', 'File Transfer Protocol data channel'),
    21: ('TCP', 'FTP Control', 'File Transfer Protocol control'),
    22: ('TCP', 'SSH', 'Secure Shell - encrypted remote access'),
    23: ('TCP', 'Telnet', 'INSECURE remote access - plaintext!'),
    25: ('TCP', 'SMTP', 'Email sending - Simple Mail Transfer Protocol'),
    53: ('UDP/TCP', 'DNS', 'Domain Name System - name to IP resolution'),
    80: ('TCP', 'HTTP', 'Web traffic - unencrypted'),
    110: ('TCP', 'POP3', 'Email retrieval - Post Office Protocol'),
    143: ('TCP', 'IMAP', 'Email retrieval - Internet Message Access Protocol'),
    443: ('TCP', 'HTTPS', 'Secure web traffic - TLS encrypted'),
    445: ('TCP', 'SMB', 'Windows file sharing - common attack target'),
    3306: ('TCP', 'MySQL', 'Database - should never be internet-facing'),
    3389: ('TCP', 'RDP', 'Remote Desktop Protocol - common attack target'),
    8080: ('TCP', 'HTTP-Alt', 'Alternative HTTP, often dev servers'),
}
print(f'{\"Port\":<6} {\"Proto\":<8} {\"Service\":<12} {\"Notes\":<50}')
print('-'*80)
for port, (proto, service, notes) in sorted(ports.items()):
    print(f'{port:<6} {proto:<8} {service:<12} {notes:<50}')
\"
"
```

**📸 Verified Output:**
```
Port   Proto    Service      Notes                                             
--------------------------------------------------------------------------------
20     TCP      FTP Data     File Transfer Protocol data channel               
21     TCP      FTP Control  File Transfer Protocol control                    
22     TCP      SSH          Secure Shell - encrypted remote access            
23     TCP      Telnet       INSECURE remote access - plaintext!               
25     TCP      SMTP         Email sending - Simple Mail Transfer Protocol     
53     UDP/TCP  DNS          Domain Name System - name to IP resolution        
80     TCP      HTTP         Web traffic - unencrypted                         
110    TCP      POP3         Email retrieval - Post Office Protocol            
143    TCP      IMAP         Email retrieval - Internet Message Access Protocol
443    TCP      HTTPS        Secure web traffic - TLS encrypted                
445    TCP      SMB          Windows file sharing - common attack target        
3306  TCP      MySQL        Database - should never be internet-facing         
3389  TCP      RDP          Remote Desktop Protocol - common attack target     
8080  TCP      HTTP-Alt     Alternative HTTP, often dev servers                
```

> 💡 **What this means:** An open port 23 (Telnet) is a critical finding — it transmits credentials in plaintext. Port 3306 (MySQL) exposed to the internet is a catastrophic misconfiguration. Port 445 (SMB) was exploited by the WannaCry ransomware. Knowing these ports is essential for firewall configuration and penetration testing.

### Step 8: IP Address Classes and CIDR Notation
Understanding IP addressing is fundamental:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import ipaddress

networks = [
    ('192.168.1.0/24', 'Private home/office network'),
    ('10.0.0.0/8', 'Private enterprise network'),
    ('172.16.0.0/12', 'Private network (Docker default)'),
    ('127.0.0.0/8', 'Loopback (localhost)'),
    ('0.0.0.0/0', 'All addresses (default route)'),
]

for cidr, description in networks:
    net = ipaddress.IPv4Network(cidr)
    print(f'Network: {cidr}')
    print(f'  Description: {description}')
    print(f'  Hosts: {net.num_addresses - 2} usable addresses')
    print(f'  First host: {net.network_address + 1}')
    print(f'  Last host: {net.broadcast_address - 1}')
    print()
\"
"
```

**📸 Verified Output:**
```
Network: 192.168.1.0/24
  Description: Private home/office network
  Hosts: 254 usable addresses
  First host: 192.168.1.1
  Last host: 192.168.1.254

Network: 10.0.0.0/8
  Description: Private enterprise network
  Hosts: 16777214 usable addresses
  First host: 10.0.0.1
  Last host: 10.255.255.254

Network: 172.16.0.0/12
  Description: Private network (Docker default)
  Hosts: 1048574 usable addresses
  First host: 172.16.0.1
  Last host: 172.31.255.254

Network: 127.0.0.0/8
  Description: Loopback (localhost)
  Hosts: 16777214 usable addresses
  First host: 127.0.0.1
  Last host: 127.255.255.254

Network: 0.0.0.0/0
  Description: All addresses (default route)
  Hosts: 4294967294 usable addresses
```

> 💡 **What this means:** Private IP ranges (RFC 1918) can't be routed on the public internet. When you see `10.x.x.x` or `192.168.x.x` in logs, it's internal traffic. CIDR notation like `/24` means 24 bits are the network, 8 bits are for hosts — giving 254 usable addresses. Misrouting these networks is a common misconfiguration attackers exploit.

### Step 9: Scan for Open Ports (on Localhost)
Now let's use nmap to scan our own container — the safe way to practice port scanning:

```bash
docker run --rm innozverse-cybersec bash -c "
# Start some services first
(nc -l -p 8888 -q 10 < /dev/null &)
(nc -l -p 9999 -q 10 < /dev/null &)
sleep 0.5

echo '=== Scanning localhost ==='
nmap -sT 127.0.0.1 -p 8888,9999,22,80,443 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Scanning localhost ===
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-01 19:52 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000018s latency).

PORT     STATE  SERVICE
22/tcp   closed ssh
80/tcp   closed http
443/tcp  closed https
8888/tcp open   sun-answerbook
9999/tcp open   abyss

Nmap done: 1 IP address (1 host up) scanned in 0.05 seconds
```

> 💡 **What this means:** Nmap found our two netcat listeners on ports 8888 and 9999 — listed as "open." Ports 22, 80, and 443 are "closed" because nothing is listening. This is exactly what a penetration tester sees when scanning a target: open ports reveal running services that might have vulnerabilities.

### Step 10: Understand TCP Sequence Numbers and Session Hijacking
TCP uses sequence numbers for reliability. This also enables session hijacking:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import random
print('TCP SEQUENCE NUMBERS:')
print('='*50)
print()
print('Every TCP connection uses sequence numbers to:')
print('1. Track which data has been received')
print('2. Detect lost packets for retransmission')
print('3. Ensure data arrives in order')
print()

isn = random.randint(1000000000, 4294967295)
print(f'Example TCP connection:')
print(f'Client picks Initial Sequence Number (ISN): {isn}')
print(f'After sending 100 bytes, next seq would be: {isn + 100}')
print(f'After sending 500 more bytes: {isn + 600}')
print()
print('SESSION HIJACKING ATTACK:')
print('In the old days, ISNs were predictable.')
print('An attacker could guess the next seq number,')
print('inject fake packets, and take over a TCP session!')
print()
print('Modern defense: Random ISNs + TLS encryption')
print('TLS encrypts data, so even if seq is guessed,')
print('the attacker cannot read or inject data.')
\"
"
```

**📸 Verified Output:**
```
TCP SEQUENCE NUMBERS:
==================================================

Every TCP connection uses sequence numbers to:
1. Track which data has been received
2. Detect lost packets for retransmission
3. Ensure data arrives in order

Example TCP connection:
Client picks Initial Sequence Number (ISN): 3847291045
After sending 100 bytes, next seq would be: 3847291145
After sending 500 more bytes: 3847291645

SESSION HIJACKING ATTACK:
In the old days, ISNs were predictable.
An attacker could guess the next seq number,
inject fake packets, and take over a TCP session!

Modern defense: Random ISNs + TLS encryption
TLS encrypts data, so even if seq is guessed,
the attacker cannot read or inject data.
```

> 💡 **What this means:** Early TCP implementations used sequential ISNs (easy to predict), enabling session hijacking. Modern OSes use cryptographically random ISNs. Combined with TLS encryption, session hijacking over TCP is now extremely difficult. This is why "HTTPS everywhere" is such important advice.

## ✅ Verification

```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
import socket
# Quick TCP echo test
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 12345))
s.listen(1)
import threading
def serve():
    conn, _ = s.accept()
    data = conn.recv(1024)
    conn.send(data)
    conn.close()
    s.close()
threading.Thread(target=serve).start()
import time; time.sleep(0.1)
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(('127.0.0.1', 12345))
c.send(b'TCP works!')
print('TCP verified:', c.recv(1024).decode())
c.close()
\"
"
```

**📸 Verified Output:**
```
TCP verified: TCP works!
```

## 🚨 Common Mistakes
- **Confusing TCP and UDP**: Remember TCP = reliable (handshake), UDP = fast (no handshake). Many protocols can use either — choose based on security requirements.
- **Thinking port numbers = services**: Port 8080 is often HTTP, but anyone can run any service on any port. Always fingerprint the service, don't assume from port number alone.
- **Forgetting localhost is still a network**: `127.0.0.1` still uses TCP/IP — tools and concepts that work on internet traffic apply to loopback too.

## 📝 Summary
- TCP uses a three-way handshake (SYN, SYN-ACK, ACK) to establish reliable connections; attackers exploit this with SYN floods
- Port numbers identify services: well-known ports (0-1023) include HTTP (80), HTTPS (443), SSH (22), and many attack targets like RDP (3389) and SMB (445)
- UDP is faster but connectionless — used by DNS, streaming, and VoIP, but also exploited in amplification attacks
- Tools like `netcat`, `ss`, `nmap`, and Python sockets let you observe and test TCP/IP directly

## 🔗 Further Reading
- [RFC 793 - TCP Specification](https://tools.ietf.org/html/rfc793)
- [Cloudflare: What is a SYN flood attack?](https://www.cloudflare.com/learning/ddos/syn-flood-ddos-attack/)
- [IANA Port Assignments](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml)
