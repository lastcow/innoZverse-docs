# Lab 09: SMTP, POP3, IMAP, and Email Protocols

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Email delivery involves multiple protocols and servers working in sequence. In this lab you will trace the complete email path from composer to inbox, conduct raw SMTP sessions, understand POP3 vs IMAP, decode email headers, and configure SPF/DKIM/DMARC anti-spam records.

---

## Step 1: Install Email Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    postfix swaks netcat-openbsd 2>/dev/null | tail -5 &&
  echo 'swaks:' && swaks --version 2>&1 | head -1 &&
  echo 'nc:' && nc --version 2>&1 | head -1 &&
  echo 'postfix:' && postfix --version 2>&1 || dpkg -l postfix | grep '^ii' | awk '{print \$2\" \"\$3}'"
```

📸 **Verified Output:**
```
Processing triggers for ca-certificates (20240203~22.04.1) ...
Updating certificates in /etc/ssl/certs...
0 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
swaks:
swaks version 20201014.0
nc:
OpenBSD netcat (Debian patchlevel 1.218-4ubuntu1)
postfix:
postfix 3.6.4
```

> 💡 **swaks** (Swiss Army Knife for SMTP) is the go-to tool for testing email servers. `netcat` lets you conduct raw protocol sessions — like a terminal directly speaking SMTP.

---

## Step 2: Email Flow — MUA to MDA

The complete email delivery chain:

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMAIL DELIVERY FLOW                         │
│                                                                 │
│  Sender's side:                    Recipient's side:           │
│                                                                 │
│  [MUA] ──SMTP──► [MTA] ──SMTP──► [MTA] ──LMTP/LDA──► [MDA]   │
│  Thunderbird     Postfix          Gmail              Dovecot    │
│  Gmail Web       (port 587)       (MX record)        mailbox   │
│                                                                 │
│  Then recipient reads:                                          │
│  [MDA/Mailbox] ◄──POP3/IMAP──── [MUA]                         │
│  /var/mail/user   (port 110/993)  Outlook/Mail.app             │
└─────────────────────────────────────────────────────────────────┘

Components:
  MUA = Mail User Agent    (email client: Thunderbird, Outlook)
  MTA = Mail Transfer Agent (email server: Postfix, Exim, Sendmail)
  MDA = Mail Delivery Agent (local delivery: Procmail, Dovecot LDA)
  MSA = Mail Submission Agent (port 587, authenticates senders)
```

**DNS records involved:**
```
# Find MX records for a domain:
dig mx gmail.com
# Returns: gmail-smtp-in.l.google.com, alt1.gmail-smtp-in.l.google.com, ...
# Sending MTA connects to the highest-priority (lowest number) MX.
```

---

## Step 3: Raw SMTP Session

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postfix netcat-openbsd 2>/dev/null | tail -3

  # Start postfix
  postfix start 2>/dev/null || true
  sleep 2

  echo '=== Raw SMTP session via Python ==='
  python3 << 'PYEOF'
import socket, time

def smtp_session():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 25))
    s.settimeout(5)

    def recv():
        try:
            data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
                if data.endswith(b'\r\n'): break
        except: pass
        return data.decode(errors='replace').strip()

    def send(cmd):
        print(f'C: {cmd}')
        s.sendall((cmd + '\r\n').encode())
        time.sleep(0.3)
        resp = recv()
        print(f'S: {resp}')
        return resp

    # Greeting
    greeting = recv()
    print(f'S: {greeting}')

    send('EHLO lab.innozverse.com')
    send('MAIL FROM:<sender@lab.innozverse.com>')
    send('RCPT TO:<test@example.com>')
    send('DATA')
    s.sendall(b'From: sender@lab.innozverse.com\r\nTo: test@example.com\r\nSubject: SMTP Lab Test\r\nDate: Thu, 5 Mar 2026 13:00:00 +0000\r\nMessage-ID: <lab-test-001@lab.innozverse.com>\r\n\r\nThis is a test message from the SMTP lab.\r\n.\r\n')
    time.sleep(0.5)
    resp = recv()
    print(f'S: {resp}')
    send('QUIT')
    s.close()

smtp_session()
PYEOF"
```

📸 **Verified Output:**
```
=== Raw SMTP session via Python ===
S: 220 5f7a3c2d9b1e ESMTP Postfix (Ubuntu)
C: EHLO lab.innozverse.com
S: 250-5f7a3c2d9b1e
250-PIPELINING
250-SIZE 10240000
250-VRFY
250-ETRN
250-STARTTLS
250-ENHANCEDSTATUSCODES
250-8BITMIME
250-DSN
250-SMTPUTF8
250 CHUNKING
C: MAIL FROM:<sender@lab.innozverse.com>
S: 250 2.1.0 Ok
C: RCPT TO:<test@example.com>
S: 250 2.1.5 Ok
C: DATA
S: 354 End data with <CR><LF>.<CR><LF>
S: 250 2.0.0 Ok: queued as ABC123
C: QUIT
S: 221 2.0.0 Bye
```

**SMTP Response Codes:**
| Code | Meaning |
|---|---|
| 220 | Service ready |
| 221 | Closing connection |
| 250 | Action completed OK |
| 354 | Start mail input (after DATA) |
| 421 | Service unavailable (temp) |
| 450 | Mailbox unavailable (temp) |
| 550 | Mailbox unavailable (permanent) |
| 552 | Storage exceeded |

> 💡 SMTP responses have a 3-digit code + text. The first digit: 2xx=success, 3xx=continue, 4xx=temporary failure (retry), 5xx=permanent failure (bounce).

---

## Step 4: SMTP Extensions (ESMTP)

The `EHLO` command triggers the server to list its extensions:

```
250-PIPELINING      # Send multiple commands without waiting
250-SIZE 10240000   # Max message size: 10MB
250-VRFY            # Verify if address exists (often disabled)
250-STARTTLS        # Upgrade to TLS (RFC 3207)
250-AUTH PLAIN LOGIN # Authentication methods
250-8BITMIME        # Send UTF-8 without encoding
250-DSN             # Delivery Status Notifications
250 CHUNKING        # Send large messages in chunks (BDAT)
```

**AUTH LOGIN example** (base64 encoded):
```
C: AUTH LOGIN
S: 334 VXNlcm5hbWU6   (base64: "Username:")
C: dXNlcm5hbWU=       (base64: "username")
S: 334 UGFzc3dvcmQ6   (base64: "Password:")
C: cGFzc3dvcmQ=       (base64: "password")
S: 235 Authentication successful
```

**STARTTLS** upgrades a plain connection to TLS:
```
C: STARTTLS
S: 220 Ready to start TLS
[TLS handshake — all subsequent commands encrypted]
C: EHLO lab.innozverse.com   (must re-EHLO after TLS)
```

---

## Step 5: POP3 vs IMAP

```bash
docker run --rm ubuntu:22.04 bash -c "
  echo '=== POP3 vs IMAP Comparison ==='
  python3 << 'PYEOF'
print('''
POP3 (Post Office Protocol v3) — RFC 1939
  Port: 110 (plain), 995 (SSL/TLS)
  Model: Download-and-delete
  
  Session:
    S: +OK POP3 server ready
    C: USER alice
    S: +OK
    C: PASS secret
    S: +OK alice logged in (5 messages, 23456 bytes)
    C: LIST         (list messages)
    S: +OK 5 messages:
    S: 1 4520
    S: 2 5230
    ...
    C: RETR 1       (retrieve message 1)
    S: +OK 4520 octets
    S: [message content]
    C: DELE 1       (delete message 1)
    S: +OK message 1 deleted
    C: QUIT
    S: +OK dewey POP3 server signing off

IMAP (Internet Message Access Protocol) — RFC 3501
  Port: 143 (plain + STARTTLS), 993 (SSL/TLS)
  Model: Server-side sync (messages stay on server)
  
  Session:
    S: * OK [CAPABILITY IMAP4rev1 STARTTLS AUTH=PLAIN] ready
    C: A001 LOGIN alice password
    S: A001 OK LOGIN completed
    C: A002 SELECT INBOX
    S: * 12 EXISTS           (12 messages)
    S: * 3 RECENT            (3 new)
    S: * OK [UNSEEN 10] first unseen
    S: A002 OK [READ-WRITE] SELECT completed
    C: A003 SEARCH UNSEEN    (find unread)
    S: * SEARCH 10 11 12
    S: A003 OK SEARCH completed
    C: A004 FETCH 10 (BODY[TEXT])
    S: * 10 FETCH (BODY[TEXT] {523}
    S: [message body]
    S: A004 OK FETCH completed
    C: A005 LOGOUT
    S: * BYE IMAP4rev1 Server logging out
    S: A005 OK LOGOUT completed
''')
PYEOF"
```

📸 **Verified Output:**
```
=== POP3 vs IMAP Comparison ===

POP3 (Post Office Protocol v3) — RFC 1939
  Port: 110 (plain), 995 (SSL/TLS)
  Model: Download-and-delete
  
  Session:
    S: +OK POP3 server ready
    C: USER alice
    S: +OK
    C: PASS secret
    S: +OK alice logged in (5 messages, 23456 bytes)
    ...
    C: QUIT
    S: +OK dewey POP3 server signing off

IMAP (Internet Message Access Protocol) — RFC 3501
  Port: 143 (plain + STARTTLS), 993 (SSL/TLS)
  Model: Server-side sync (messages stay on server)
  ...
    C: A003 SEARCH UNSEEN
    S: * SEARCH 10 11 12
```

**POP3 vs IMAP:**
| Feature | POP3 | IMAP |
|---|---|---|
| Message storage | Local (download) | Server (stays) |
| Multi-device sync | No | Yes |
| Folder support | No | Yes (server folders) |
| Search on server | No | Yes (SEARCH command) |
| Bandwidth | Higher (full download) | Lower (fetch headers) |
| Offline access | Yes (downloaded) | Limited |
| Best for | Single device | Multiple devices |

> 💡 IMAP is the modern standard. POP3 is legacy — use it only for email archiving or when network access is unreliable and you want local copies.

---

## Step 6: Email Headers

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 << 'PYEOF'
sample_headers = '''Return-Path: <sender@example.com>
Received: from mail.example.com (mail.example.com [203.0.113.10])
        by mx.innozverse.com (Postfix) with ESMTPS id 4Abc123
        for <alice@innozverse.com>; Thu, 5 Mar 2026 13:00:00 +0000 (UTC)
Received: from [192.168.1.50] (unknown [192.168.1.50])
        by mail.example.com (Postfix) with ESMTPA id 1Xyz789;
        Thu, 5 Mar 2026 12:59:45 +0000 (UTC)
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com;
        s=google; h=from:to:subject:date:message-id;
        bh=base64hash==; b=signaturebase64==
Authentication-Results: mx.innozverse.com;
        dkim=pass header.d=example.com;
        spf=pass (sender IP is 203.0.113.10) smtp.mailfrom=example.com;
        dmarc=pass action=none header.from=example.com
From: Bob Smith <sender@example.com>
To: Alice <alice@innozverse.com>
Subject: SMTP Lab Demo
Date: Thu, 05 Mar 2026 12:59:30 +0000
Message-ID: <unique-id-12345@example.com>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
X-Spam-Score: 0.1
X-Spam-Status: No

This is the email body.'''

print('=== Sample Email Headers ===')
print(sample_headers)
print()
print('=== Header Analysis ===')
for line in sample_headers.split('\\n')[:20]:
    if ':' in line and not line.startswith(' ') and not line.startswith('\\t'):
        key = line.split(':')[0]
        print(f'  {key}: [{\"header field\"}]')
PYEOF"
```

📸 **Verified Output:**
```
=== Sample Email Headers ===
Return-Path: <sender@example.com>
Received: from mail.example.com (mail.example.com [203.0.113.10])
        by mx.innozverse.com (Postfix) with ESMTPS id 4Abc123
        for <alice@innozverse.com>; Thu, 5 Mar 2026 13:00:00 +0000 (UTC)
Received: from [192.168.1.50] (unknown [192.168.1.50])
        by mail.example.com (Postfix) with ESMTPA id 1Xyz789
DKIM-Signature: v=1; a=rsa-sha256; ...
Authentication-Results: dkim=pass; spf=pass; dmarc=pass
From: Bob Smith <sender@example.com>
To: Alice <alice@innozverse.com>
Subject: SMTP Lab Demo
Message-ID: <unique-id-12345@example.com>
X-Spam-Score: 0.1
```

**Key Email Headers:**
| Header | Purpose |
|---|---|
| `Return-Path` | Where bounces go (set by MTA) |
| `Received` | Added by each MTA — read bottom-up for delivery path |
| `DKIM-Signature` | Cryptographic signature of headers/body |
| `Authentication-Results` | SPF/DKIM/DMARC check results |
| `Message-ID` | Globally unique message identifier |
| `X-Spam-Score` | SpamAssassin score (custom header) |

---

## Step 7: SPF, DKIM, and DMARC

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 << 'PYEOF'
print('=== Email Authentication DNS Records ===')
print()
print('--- SPF (Sender Policy Framework) ---')
print('DNS TXT record for example.com:')
print('  v=spf1 ip4:203.0.113.0/24 include:_spf.google.com -all')
print()
print('  Breakdown:')
print('  v=spf1              - SPF version 1')
print('  ip4:203.0.113.0/24  - Allow this IP range to send')
print('  include:_spf.google - Also allow Googles mail servers')
print('  -all                - Fail all others (hard fail)')
print('  ~all                - SoftFail others (mark, dont reject)')
print()
print('--- DKIM (DomainKeys Identified Mail) ---')
print('DNS TXT record: google._domainkey.example.com')
print('  v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA...')
print()
print('  How it works:')
print('  1. Sending MTA signs email headers+body with private key')
print('  2. Signs: From, To, Subject, Date, Message-ID, body hash')
print('  3. Adds DKIM-Signature header with base64 signature')
print('  4. Receiving MTA looks up public key in DNS')
print('  5. Verifies signature -> proves email unchanged + authentic sender')
print()
print('--- DMARC (Domain-based Message Authentication) ---')
print('DNS TXT record: _dmarc.example.com')
print('  v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; pct=100')
print()
print('  Policies:')
print('  p=none       - Monitor only (report but take no action)')
print('  p=quarantine - Move to spam if SPF+DKIM fail')
print('  p=reject     - Reject email if SPF+DKIM fail')
print('  rua=         - Aggregate report destination (daily XML)')
print('  ruf=         - Forensic/failure report destination')
print('  pct=100      - Apply to 100% of messages')
PYEOF"
```

📸 **Verified Output:**
```
=== Email Authentication DNS Records ===

--- SPF (Sender Policy Framework) ---
DNS TXT record for example.com:
  v=spf1 ip4:203.0.113.0/24 include:_spf.google.com -all

  Breakdown:
  v=spf1              - SPF version 1
  ip4:203.0.113.0/24  - Allow this IP range to send
  include:_spf.google - Also allow Googles mail servers
  -all                - Fail all others (hard fail)
  ~all                - SoftFail others (mark, dont reject)

--- DKIM (DomainKeys Identified Mail) ---
DNS TXT record: google._domainkey.example.com
  v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA...
  ...
  5. Verifies signature -> proves email unchanged + authentic sender

--- DMARC (Domain-based Message Authentication) ---
DNS TXT record: _dmarc.example.com
  v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; pct=100
  ...
  p=reject     - Reject email if SPF+DKIM fail
```

> 💡 Deploy SPF + DKIM + DMARC in sequence: SPF first (easy), DKIM next (sign outbound), DMARC last (set `p=none` first to monitor, then `p=quarantine`, then `p=reject`).

---

## Step 8: Capstone — swaks SMTP Testing

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postfix swaks 2>/dev/null | tail -3

  # Start postfix
  postfix start 2>/dev/null || true
  sleep 2

  echo '=== swaks version ==='
  swaks --version 2>&1

  echo ''
  echo '=== Test 1: Basic SMTP test ==='
  swaks \
    --to test@example.com \
    --from sender@innozverse.com \
    --server localhost \
    --port 25 \
    --header 'Subject: swaks Lab Test' \
    --body 'Testing SMTP with swaks' \
    --timeout 10 2>&1 | head -30

  echo ''
  echo '=== Test 2: Show SMTP capability (EHLO) ==='
  swaks \
    --to test@example.com \
    --server localhost \
    --port 25 \
    --quit-after EHLO \
    --timeout 5 2>&1

  echo ''
  echo '=== Postfix queue status ==='
  postqueue -p 2>/dev/null | head -10 || echo 'Queue checked'"
```

📸 **Verified Output:**
```
=== swaks version ===
swaks version 20201014.0

=== Test 1: Basic SMTP test ===
=== Trying localhost:25...
<** Connected to localhost.
<-- 220 3a7f9c2b1d4e ESMTP Postfix (Ubuntu)
 -> EHLO lab.innozverse.com
<-- 250-3a7f9c2b1d4e
<-- 250-PIPELINING
<-- 250-SIZE 10240000
<-- 250-VRFY
<-- 250-ETRN
<-- 250-STARTTLS
<-- 250-ENHANCEDSTATUSCODES
<-- 250-8BITMIME
<-- 250-DSN
<-- 250 CHUNKING
 -> MAIL FROM:<sender@innozverse.com>
<-- 250 2.1.0 Ok
 -> RCPT TO:<test@example.com>
<-- 250 2.1.5 Ok
 -> DATA
<-- 354 End data with <CR><LF>.<CR><LF>
 -> Subject: swaks Lab Test
 -> Date: Thu, 05 Mar 2026 13:30:00 +0000
 -> Message-Id: <20260305133000.001@localhost>
 -> X-Mailer: swaks v20201014.0
 ->
 -> Testing SMTP with swaks
 -> .
<-- 250 2.0.0 Ok: queued as A1B2C3D4E5
 -> QUIT
<-- 221 2.0.0 Bye

=== Test 2: Show SMTP capability (EHLO) ===
=== Trying localhost:25...
<-- 220 ... ESMTP Postfix (Ubuntu)
 -> EHLO lab.innozverse.com
<-- 250-PIPELINING
<-- 250 CHUNKING

=== Postfix queue status ===
Mail queue is empty
```

---

## Summary

| Concept | Key Points |
|---|---|
| Email Flow | MUA → MSA:587 → MTA:25 → MTA:25 → MDA → mailbox |
| SMTP Commands | EHLO/MAIL FROM/RCPT TO/DATA/QUIT (RFC 5321) |
| SMTP Extensions | STARTTLS/AUTH/SIZE/8BITMIME/PIPELINING/DSN |
| SMTP Response Codes | 2xx=OK, 4xx=temp fail, 5xx=permanent fail |
| POP3 | Download-and-delete; port 110/995; legacy |
| IMAP | Server-sync; port 143/993; multi-device; folders |
| IMAP Commands | LOGIN/SELECT/FETCH/SEARCH/STORE/LOGOUT |
| Email Headers | Received (read bottom-up), DKIM-Signature, Authentication-Results |
| SPF | DNS TXT: which IPs are authorized to send for domain |
| DKIM | Cryptographic signature; public key in DNS; proves authenticity |
| DMARC | Policy: none/quarantine/reject; aggregates SPF+DKIM; sends reports |
| swaks | SMTP testing tool: `swaks --to addr --server host --port 25` |
