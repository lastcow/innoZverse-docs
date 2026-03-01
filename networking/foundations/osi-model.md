# OSI Model

The OSI (Open Systems Interconnection) model is a conceptual framework for understanding how data travels across a network.

## The 7 Layers

| Layer | Name | Function | Examples |
|-------|------|----------|---------|
| 7 | **Application** | User-facing services | HTTP, FTP, SMTP, DNS |
| 6 | **Presentation** | Data formatting, encryption | SSL/TLS, JPEG, JSON |
| 5 | **Session** | Manage connections | NetBIOS, RPC |
| 4 | **Transport** | Reliable data delivery | TCP, UDP |
| 3 | **Network** | Routing between networks | IP, ICMP, OSPF |
| 2 | **Data Link** | Node-to-node delivery | Ethernet, Wi-Fi (802.11) |
| 1 | **Physical** | Raw bit transmission | Cables, fiber, radio |

## Memory Aid

> **"All People Seem To Need Data Processing"** (Layer 7 → 1)  
> **"Please Do Not Throw Sausage Pizza Away"** (Layer 1 → 7)

## Data Encapsulation

As data travels down the layers, each layer adds its own header:

```
Application data
→ [TCP header][Application data]           (Segment)
→ [IP header][TCP header][Data]            (Packet)
→ [Ethernet header][IP][TCP][Data][FCS]    (Frame)
→ 01010101...                              (Bits)
```

## TCP/IP Model vs OSI

The TCP/IP model (used in practice) maps to OSI:

| TCP/IP | OSI Equivalent |
|--------|---------------|
| Application | Layers 5, 6, 7 |
| Transport | Layer 4 |
| Internet | Layer 3 |
| Network Access | Layers 1, 2 |
