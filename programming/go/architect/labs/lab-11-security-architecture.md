# Lab 11: Security Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Go security architecture: `golang.org/x/crypto` (chacha20poly1305/argon2/ed25519/x25519), secure random, PASETO-style tokens (HMAC-SHA512), mTLS, security headers middleware, and token bucket rate limiting.

---

## Step 1: Symmetric Encryption — XChaCha20-Poly1305

```go
package crypto

import (
	"crypto/rand"
	"errors"
	"golang.org/x/crypto/chacha20poly1305"
)

// XChaCha20-Poly1305: authenticated encryption (AEAD)
// 256-bit key, 192-bit nonce (XChaCha = extended nonce, safe for random generation)
// Authenticates both ciphertext + associated data (prevents tampering)

func Encrypt(key []byte, plaintext []byte) ([]byte, error) {
	if len(key) != chacha20poly1305.KeySize { // 32 bytes
		return nil, errors.New("key must be 32 bytes")
	}

	aead, err := chacha20poly1305.NewX(key)
	if err != nil {
		return nil, err
	}

	// Random 192-bit nonce — XChaCha extended nonce is safe to generate randomly
	nonce := make([]byte, aead.NonceSize()) // 24 bytes
	if _, err = rand.Read(nonce); err != nil {
		return nil, err
	}

	// Seal: encrypt + authenticate
	// Output: nonce || ciphertext+tag
	ciphertext := aead.Seal(nonce, nonce, plaintext, nil)
	return ciphertext, nil
}

func Decrypt(key []byte, ciphertext []byte) ([]byte, error) {
	aead, err := chacha20poly1305.NewX(key)
	if err != nil {
		return nil, err
	}

	nonceSize := aead.NonceSize()
	if len(ciphertext) < nonceSize+aead.Overhead() {
		return nil, errors.New("ciphertext too short")
	}

	nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
	return aead.Open(nil, nonce, ciphertext, nil)
}
```

---

## Step 2: Password Hashing — Argon2id

```go
package auth

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"fmt"
	"golang.org/x/crypto/argon2"
)

type Argon2Params struct {
	Memory      uint32  // KB of memory to use
	Iterations  uint32  // Number of passes over memory
	Parallelism uint8   // Number of threads
	SaltLength  uint32
	KeyLength   uint32
}

// OWASP recommended: memory=64MB, iterations=3, parallelism=4
var DefaultArgon2Params = Argon2Params{
	Memory: 64 * 1024, Iterations: 3, Parallelism: 4,
	SaltLength: 16, KeyLength: 32,
}

func HashPassword(password string, p Argon2Params) (string, error) {
	salt := make([]byte, p.SaltLength)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}

	hash := argon2.IDKey([]byte(password), salt,
		p.Iterations, p.Memory, p.Parallelism, p.KeyLength)

	return fmt.Sprintf("$argon2id$v=%d$m=%d,t=%d,p=%d$%s$%s",
		argon2.Version, p.Memory, p.Iterations, p.Parallelism,
		base64.RawStdEncoding.EncodeToString(salt),
		base64.RawStdEncoding.EncodeToString(hash)), nil
}

func VerifyPassword(password, encodedHash string) (bool, error) {
	p, salt, hash, err := decodeHash(encodedHash)
	if err != nil {
		return false, err
	}

	otherHash := argon2.IDKey([]byte(password), salt,
		p.Iterations, p.Memory, p.Parallelism, uint32(len(hash)))

	// Constant-time comparison to prevent timing attacks
	return subtle.ConstantTimeCompare(hash, otherHash) == 1, nil
}
```

---

## Step 3: Asymmetric Keys — Ed25519 + X25519

```go
package crypto

import (
	"crypto/ed25519"
	"crypto/rand"
	"golang.org/x/crypto/curve25519"
)

// Ed25519: fast, secure digital signatures
func GenerateEd25519Keys() (ed25519.PublicKey, ed25519.PrivateKey, error) {
	return ed25519.GenerateKey(rand.Reader)
}

func SignEd25519(privateKey ed25519.PrivateKey, message []byte) []byte {
	return ed25519.Sign(privateKey, message)
}

func VerifyEd25519(publicKey ed25519.PublicKey, message, signature []byte) bool {
	return ed25519.Verify(publicKey, message, signature)
}

// X25519: Elliptic-Curve Diffie-Hellman key exchange
// Use for: establishing shared secrets for session encryption
func X25519KeyExchange() (shared []byte, err error) {
	// Alice generates ephemeral keypair
	alicePriv := make([]byte, 32)
	rand.Read(alicePriv)
	alicePub, _ := curve25519.X25519(alicePriv, curve25519.Basepoint)

	// Bob generates ephemeral keypair
	bobPriv := make([]byte, 32)
	rand.Read(bobPriv)
	bobPub, _ := curve25519.X25519(bobPriv, curve25519.Basepoint)

	// Exchange public keys (over the wire)

	// Compute shared secret (identical on both sides)
	aliceShared, _ := curve25519.X25519(alicePriv, bobPub)
	bobShared,   _ := curve25519.X25519(bobPriv, alicePub)

	// aliceShared == bobShared (DH property)
	// Then: derive session key with HKDF from shared secret
	_ = bobShared
	return aliceShared, nil
}
```

---

## Step 4: PASETO-Style Tokens (HMAC-SHA512)

```go
package token

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha512"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strings"
	"time"
)

type Claims struct {
	Subject   string    `json:"sub"`
	IssuedAt  time.Time `json:"iat"`
	ExpiresAt time.Time `json:"exp"`
	Issuer    string    `json:"iss"`
	Data      map[string]interface{} `json:"data,omitempty"`
}

type TokenMaker struct {
	secretKey []byte // 32+ bytes
}

func (m *TokenMaker) Create(claims Claims) (string, error) {
	// Add random nonce (prevents token reuse)
	nonce := make([]byte, 32)
	rand.Read(nonce)

	payload, _ := json.Marshal(claims)
	encoded := base64.URLEncoding.EncodeToString(payload)
	nonceEncoded := base64.URLEncoding.EncodeToString(nonce)
	data := encoded + "." + nonceEncoded

	// HMAC-SHA512 signature
	mac := hmac.New(sha512.New, m.secretKey)
	mac.Write([]byte(data))
	sig := base64.URLEncoding.EncodeToString(mac.Sum(nil))

	return data + "." + sig, nil
}

func (m *TokenMaker) Verify(token string) (*Claims, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return nil, errors.New("invalid token format")
	}

	data := parts[0] + "." + parts[1]
	mac := hmac.New(sha512.New, m.secretKey)
	mac.Write([]byte(data))
	expectedSig := base64.URLEncoding.EncodeToString(mac.Sum(nil))

	// Constant-time comparison
	if !hmac.Equal([]byte(expectedSig), []byte(parts[2])) {
		return nil, errors.New("invalid signature")
	}

	payload, _ := base64.URLEncoding.DecodeString(parts[0])
	var claims Claims
	if err := json.Unmarshal(payload, &claims); err != nil {
		return nil, err
	}

	if time.Now().After(claims.ExpiresAt) {
		return nil, errors.New("token expired")
	}

	return &claims, nil
}
```

---

## Step 5: Security Headers Middleware

```go
package middleware

import "net/http"

func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := w.Header()
		// Prevent MIME sniffing
		h.Set("X-Content-Type-Options", "nosniff")
		// Prevent clickjacking
		h.Set("X-Frame-Options", "DENY")
		// Force HTTPS
		h.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
		// CSP (customize per app)
		h.Set("Content-Security-Policy",
			"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"+
				"img-src 'self' data: https:; frame-ancestors 'none'")
		// XSS protection (legacy browsers)
		h.Set("X-XSS-Protection", "1; mode=block")
		// Referrer policy
		h.Set("Referrer-Policy", "strict-origin-when-cross-origin")
		// Permissions policy
		h.Set("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

		next.ServeHTTP(w, r)
	})
}
```

---

## Step 6: Token Bucket Rate Limiting

```go
package ratelimit

import (
	"net/http"
	"sync"
	"time"
)

type TokenBucket struct {
	capacity  float64
	tokens    float64
	refillRate float64 // tokens per second
	lastRefill time.Time
	mu        sync.Mutex
}

func NewTokenBucket(capacity float64, refillRate float64) *TokenBucket {
	return &TokenBucket{
		capacity:   capacity,
		tokens:     capacity,
		refillRate: refillRate,
		lastRefill: time.Now(),
	}
}

func (b *TokenBucket) Allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(b.lastRefill).Seconds()
	b.tokens = min(b.capacity, b.tokens+elapsed*b.refillRate)
	b.lastRefill = now

	if b.tokens >= 1.0 {
		b.tokens--
		return true
	}
	return false
}

// Per-IP rate limiter
type RateLimiter struct {
	buckets  map[string]*TokenBucket
	mu       sync.Mutex
	capacity float64
	rate     float64
}

func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := r.RemoteAddr
		bucket := rl.getBucket(ip)
		if !bucket.Allow() {
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}
		next.ServeHTTP(w, r)
	})
}
```

---

## Step 7: Secrets Management Pattern

```go
package secrets

import (
	"os"
	"sync"
)

// Secret[T]: wraps sensitive values, redacts in JSON/fmt
type Secret[T any] struct {
	value T
}

func NewSecret[T any](v T) Secret[T] { return Secret[T]{value: v} }
func (s Secret[T]) Reveal() T        { return s.value }

// Prevent accidental logging
func (s Secret[T]) String() string       { return "[REDACTED]" }
func (s Secret[T]) MarshalJSON() ([]byte, error) { return []byte(`"[REDACTED]"`), nil }
func (s Secret[T]) GoString() string     { return "[REDACTED]" }

// Load from environment (never hardcode)
type Config struct {
	DatabaseURL Secret[string]
	APIKey      Secret[string]
	JWTSecret   Secret[[]byte]
}

func LoadConfig() (*Config, error) {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}
	return &Config{
		DatabaseURL: NewSecret(dbURL),
		APIKey:      NewSecret(os.Getenv("API_KEY")),
	}, nil
}
```

---

## Step 8: Capstone — Encryption + Ed25519

```bash
docker run --rm golang:1.22-alpine sh -c "
apk add --no-cache git 2>/dev/null | tail -1
cd /tmp && go mod init lab && go get golang.org/x/crypto@v0.21.0 && go mod tidy -e 2>/dev/null | tail -3

cat > main.go << 'GOEOF'
package main

import (
  \"crypto/ed25519\"
  \"crypto/rand\"
  \"fmt\"
  \"golang.org/x/crypto/chacha20poly1305\"
)

func main() {
  fmt.Println(\"=== XChaCha20-Poly1305 ===\")
  key := make([]byte, 32)
  rand.Read(key)
  plaintext := []byte(\"Hello, encrypted world!\")
  aead, _ := chacha20poly1305.NewX(key)
  nonce := make([]byte, aead.NonceSize())
  rand.Read(nonce)
  ciphertext := aead.Seal(nonce, nonce, plaintext, nil)
  fmt.Printf(\"Plaintext:  %s\\n\", plaintext)
  fmt.Printf(\"Encrypted:  %d bytes\\n\", len(ciphertext))
  decrypted, err := aead.Open(nil, ciphertext[:aead.NonceSize()], ciphertext[aead.NonceSize():], nil)
  fmt.Printf(\"Decrypted:  %s (err=%v)\\n\", decrypted, err)
  fmt.Println()
  fmt.Println(\"=== Ed25519 ===\")
  pub, priv, _ := ed25519.GenerateKey(rand.Reader)
  msg := []byte(\"signed message\")
  sig := ed25519.Sign(priv, msg)
  fmt.Printf(\"Valid:      %v\\n\", ed25519.Verify(pub, msg, sig))
  tampered := append([]byte{}, msg...)
  tampered[0] ^= 0xFF
  fmt.Printf(\"Tampered:   %v\\n\", ed25519.Verify(pub, tampered, sig))
}
GOEOF
go run main.go"
```

📸 **Verified Output:**
```
=== XChaCha20-Poly1305 ===
Plaintext:  Hello, encrypted world!
Encrypted:  63 bytes
Decrypted:  Hello, encrypted world! (err=<nil>)

=== Ed25519 ===
Valid:      true
Tampered:   false
```

---

## Summary

| Algorithm | Use Case | Security Level |
|-----------|---------|---------------|
| XChaCha20-Poly1305 | Symmetric AEAD encryption | 256-bit |
| Argon2id | Password hashing | OWASP recommended |
| Ed25519 | Digital signatures | 128-bit equivalent |
| X25519 | Key exchange (ECDH) | 128-bit equivalent |
| HMAC-SHA512 | Token authentication | 256-bit effective |
| Token bucket | Rate limiting | DoS protection |
| Security headers | HTTP hardening | OWASP Top 10 |
| Secret[T] | Prevent accidental leaks | Type-safe redaction |
