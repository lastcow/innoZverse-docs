# Common Attack Vectors

## Social Engineering

**Phishing** — Fraudulent emails that mimic trusted sources
**Spear phishing** — Targeted phishing against specific individuals
**Vishing** — Voice/phone phishing
**Pretexting** — Creating false scenarios to extract information

**Red flags to spot:**
- Urgency or pressure
- Suspicious sender domains (micros0ft.com)
- Requests for credentials
- Unexpected attachments

## Injection Attacks

### SQL Injection
```sql
-- Vulnerable query
SELECT * FROM users WHERE username = '$input';

-- Malicious input: ' OR '1'='1
SELECT * FROM users WHERE username = '' OR '1'='1';
-- Returns ALL users!

-- Prevention: use parameterized queries
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

### Command Injection
```bash
# Vulnerable code (Python)
os.system(f"ping {user_input}")

# Malicious input: 8.8.8.8; cat /etc/passwd
os.system("ping 8.8.8.8; cat /etc/passwd")

# Prevention: never pass user input to shell commands
```

## Man-in-the-Middle (MITM)

Attacker intercepts communication between two parties.

**Prevention:**
- Always use HTTPS
- Verify SSL certificates
- Use VPN on public Wi-Fi
- HSTS headers on web servers

## Password Attacks

```bash
# Brute force SSH (for authorized testing only)
hydra -l admin -P wordlist.txt ssh://192.168.1.100

# Common tools: hashcat, John the Ripper
hashcat -m 0 hashes.txt wordlist.txt    # MD5 crack
```

**Defense:**
- Strong, unique passwords
- Multi-factor authentication
- Account lockout policies
- Password managers
