# Cryptography Basics

## Symmetric vs Asymmetric

| Type | Keys | Speed | Use Case |
|------|------|-------|----------|
| Symmetric | 1 shared key | Fast | Bulk data encryption |
| Asymmetric | Public + Private pair | Slow | Key exchange, signatures |

**Symmetric algorithms:** AES-256, ChaCha20
**Asymmetric algorithms:** RSA, ECC, Ed25519

## Hashing

Hash functions convert data into a fixed-size digest. One-way — cannot be reversed.

```bash
echo "hello" | sha256sum
# 5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03

echo "hello" | md5sum
# b1946ac92492d2347c6235b4d2611184  (weak — don't use for security)
```

**Common hash functions:**
- **MD5** — Broken, don't use for security
- **SHA-1** — Deprecated
- **SHA-256** — Current standard
- **bcrypt/Argon2** — For password storage

## TLS/HTTPS

```bash
# Check SSL certificate
openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -text

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Check certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

## SSH Keys

```bash
# Generate Ed25519 key (modern, recommended)
ssh-keygen -t ed25519 -C "your@email.com"

# Generate RSA key (wider compatibility)
ssh-keygen -t rsa -b 4096 -C "your@email.com"

# View public key fingerprint
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```
