# TCP/IP Protocol Suite

## TCP — Transmission Control Protocol

TCP provides **reliable, ordered, connection-based** delivery.

### Three-Way Handshake
```
Client          Server
  │──── SYN ────→│    "I want to connect"
  │←── SYN-ACK ──│    "OK, I'm ready"
  │──── ACK ────→│    "Great, connected!"
  │    [DATA]    │
  │──── FIN ────→│    "I'm done"
  │←── FIN-ACK ──│    "Acknowledged"
```

### TCP vs UDP

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Yes | No |
| Reliability | Guaranteed | Best-effort |
| Ordering | Yes | No |
| Speed | Slower | Faster |
| Header size | 20 bytes | 8 bytes |
| Use cases | HTTP, SSH, FTP | DNS, VoIP, Gaming, Streaming |

## Key Ports

```bash
# Check what's listening on your system
ss -tlnp         # TCP listening ports
ss -ulnp         # UDP listening ports

# Common ports to know:
20, 21  FTP
22      SSH
23      Telnet (insecure — avoid)
25      SMTP
53      DNS
67, 68  DHCP
80      HTTP
110     POP3
143     IMAP
443     HTTPS
3306    MySQL
5432    PostgreSQL
6379    Redis
27017   MongoDB
```

## Socket Programming (Python)

```python
import socket

# TCP Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 8080))
server.listen(5)
conn, addr = server.accept()
data = conn.recv(1024)
conn.send(b"Hello!")
conn.close()

# TCP Client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.1.100', 8080))
client.send(b"Hello Server!")
response = client.recv(1024)
client.close()
```
