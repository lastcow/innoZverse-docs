# Lab 13: TLS & Cryptography

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Master Go's cryptography stack: self-signed certificates with `x509`, mTLS server/client, AES-256-GCM encryption, SHA-256 hashing, bcrypt password hashing, and ECDSA key generation.

---

## Step 1: ECDSA Key Generation

```go
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
)

func generateECDSAKey() (*ecdsa.PrivateKey, error) {
	// P-256 (secp256r1) — NIST curve, widely supported
	return ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
}

func savePrivateKey(key *ecdsa.PrivateKey, path string) error {
	keyDER, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return pem.Encode(f, &pem.Block{Type: "EC PRIVATE KEY", Bytes: keyDER})
}

func main() {
	key, err := generateECDSAKey()
	if err != nil {
		panic(err)
	}
	fmt.Printf("ECDSA key: curve=%s\n", key.Curve.Params().Name)
	fmt.Printf("Public key X: %x\n", key.X.Bytes()[:8]) // first 8 bytes
}
```

---

## Step 2: Self-Signed Certificate

```go
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"os"
	"time"
)

func createSelfSignedCert(key *ecdsa.PrivateKey, cn string, ips []net.IP, dnsNames []string) ([]byte, error) {
	template := &x509.Certificate{
		SerialNumber: big.NewInt(time.Now().UnixNano()),
		Subject: pkix.Name{
			CommonName:   cn,
			Organization: []string{"innoZverse Lab"},
			Country:      []string{"US"},
		},
		NotBefore:   time.Now().Add(-10 * time.Minute),
		NotAfter:    time.Now().Add(24 * time.Hour),
		KeyUsage:    x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth, x509.ExtKeyUsageClientAuth},
		IPAddresses: ips,
		DNSNames:    dnsNames,
		IsCA:        true, // self-signed CA
		BasicConstraintsValid: true,
	}
	// Self-signed: template == parent, key == signer
	return x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
}

func saveCert(certDER []byte, path string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return pem.Encode(f, &pem.Block{Type: "CERTIFICATE", Bytes: certDER})
}

func main() {
	key, _ := generateECDSAKey()
	certDER, err := createSelfSignedCert(key, "localhost",
		[]net.IP{net.ParseIP("127.0.0.1")},
		[]string{"localhost"})
	if err != nil {
		panic(err)
	}
	cert, _ := x509.ParseCertificate(certDER)
	pemBlock := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})
	fmt.Printf("Subject: %s\n", cert.Subject.CommonName)
	fmt.Printf("Valid until: %s\n", cert.NotAfter.Format("2006-01-02"))
	fmt.Printf("PEM: %d bytes\n", len(pemBlock))
}
```

---

## Step 3: mTLS Server and Client

```go
// mtls_server.go
package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
)

func newMTLSServer(certFile, keyFile, caFile string) (*http.Server, error) {
	// Load CA cert to verify clients
	caCertPEM := loadFile(caFile)
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caCertPEM) {
		return nil, fmt.Errorf("failed to parse CA cert")
	}

	tlsCfg := &tls.Config{
		ClientCAs:  caPool,
		ClientAuth: tls.RequireAndVerifyClientCert, // mTLS: require client cert
		MinVersion: tls.VersionTLS13,
		CurvePreferences: []tls.CurveID{tls.X25519, tls.CurveP256},
		CipherSuites: []uint16{
			tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
		},
	}

	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, err
	}
	tlsCfg.Certificates = []tls.Certificate{cert}

	mux := http.NewServeMux()
	mux.HandleFunc("/secure", func(w http.ResponseWriter, r *http.Request) {
		cn := r.TLS.PeerCertificates[0].Subject.CommonName
		fmt.Fprintf(w, "Hello, %s! mTLS connection verified.\n", cn)
	})

	return &http.Server{
		Addr:      ":8443",
		Handler:   mux,
		TLSConfig: tlsCfg,
	}, nil
}
```

```go
// mtls_client.go
package main

import (
	"crypto/tls"
	"crypto/x509"
	"net/http"
)

func newMTLSClient(certFile, keyFile, caFile string) (*http.Client, error) {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, err
	}

	caCertPEM := loadFile(caFile)
	caPool := x509.NewCertPool()
	caPool.AppendCertsFromPEM(caCertPEM)

	tlsCfg := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caPool,
		MinVersion:   tls.VersionTLS13,
	}

	return &http.Client{
		Transport: &http.Transport{TLSClientConfig: tlsCfg},
	}, nil
}
```

---

## Step 4: AES-256-GCM Encryption

```go
package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
)

func generateAES256Key() ([]byte, error) {
	key := make([]byte, 32) // 256 bits
	_, err := io.ReadFull(rand.Reader, key)
	return key, err
}

func encrypt(plaintext, key []byte) (ciphertext, nonce []byte, err error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, nil, err
	}

	nonce = make([]byte, gcm.NonceSize()) // 12 bytes for AES-GCM
	if _, err = io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, nil, err
	}

	// Seal appends ciphertext+tag to nil
	ciphertext = gcm.Seal(nil, nonce, plaintext, nil)
	return ciphertext, nonce, nil
}

func decrypt(ciphertext, nonce, key []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	return gcm.Open(nil, nonce, ciphertext, nil)
}

func main() {
	key, _ := generateAES256Key()
	plaintext := []byte("Top secret message: 42 is the answer")

	ciphertext, nonce, _ := encrypt(plaintext, key)
	fmt.Printf("Key:        %s\n", hex.EncodeToString(key[:8])+"...")
	fmt.Printf("Nonce:      %s\n", hex.EncodeToString(nonce))
	fmt.Printf("Ciphertext: %s...\n", hex.EncodeToString(ciphertext)[:20])

	decrypted, _ := decrypt(ciphertext, nonce, key)
	fmt.Printf("Decrypted:  %s\n", decrypted)

	// Tamper detection: modify ciphertext
	ciphertext[0] ^= 0xFF
	_, err := decrypt(ciphertext, nonce, key)
	fmt.Printf("Tampered:   err=%v\n", err)
}
```

---

## Step 5: SHA-256 and HMAC

```go
package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

func hashSHA256(data []byte) string {
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}

func hmacSHA256(data, secret []byte) string {
	h := hmac.New(sha256.New, secret)
	h.Write(data)
	return hex.EncodeToString(h.Sum(nil))
}

func verifyHMAC(data, secret []byte, expected string) bool {
	actual := hmacSHA256(data, secret)
	return hmac.Equal([]byte(actual), []byte(expected)) // constant-time compare
}

func main() {
	data := []byte("important document")

	// SHA-256
	hash := hashSHA256(data)
	fmt.Printf("SHA-256: %s\n", hash)

	// Same data → same hash (deterministic)
	fmt.Printf("Same:    %v\n", hash == hashSHA256(data))

	// HMAC: authenticated hash (requires secret key)
	secret := make([]byte, 32)
	rand.Read(secret)
	mac := hmacSHA256(data, secret)
	fmt.Printf("HMAC:    %s...\n", mac[:20])
	fmt.Printf("Verify:  %v\n", verifyHMAC(data, secret, mac))
	fmt.Printf("Tamper:  %v\n", verifyHMAC([]byte("tampered"), secret, mac))
}
```

---

## Step 6: bcrypt Password Hashing

```go
package main

import (
	"fmt"
	"golang.org/x/crypto/bcrypt"
)

func hashPassword(password string) (string, error) {
	// Cost 12 is recommended for most applications (~300ms on modern hardware)
	hash, err := bcrypt.GenerateFromPassword([]byte(password), 12)
	return string(hash), err
}

func checkPassword(hash, password string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

func main() {
	password := "super_secret_password_123"

	hash, err := hashPassword(password)
	if err != nil {
		panic(err)
	}
	fmt.Printf("bcrypt hash: %s\n", hash[:30]+"...")
	fmt.Printf("Hash length: %d chars\n", len(hash))
	fmt.Printf("Verify correct: %v\n", checkPassword(hash, password))
	fmt.Printf("Verify wrong:   %v\n", checkPassword(hash, "wrong_password"))

	// Same password → different hash each time (bcrypt uses random salt)
	hash2, _ := hashPassword(password)
	fmt.Printf("Different hashes: %v\n", hash != hash2)
	fmt.Printf("But both verify:  %v\n", checkPassword(hash2, password))
}
```

---

## Step 7: Complete Crypto Demo

```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/crypto_lab
cat > /tmp/crypto_lab/main.go << 'GOEOF'
package main

import (
	\"crypto/aes\"
	\"crypto/cipher\"
	\"crypto/ecdsa\"
	\"crypto/elliptic\"
	\"crypto/rand\"
	\"crypto/sha256\"
	\"crypto/x509\"
	\"crypto/x509/pkix\"
	\"encoding/hex\"
	\"encoding/pem\"
	\"fmt\"
	\"io\"
	\"math/big\"
	\"time\"
)

func main() {
	// 1. ECDSA key
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	fmt.Printf(\"ECDSA key: curve=%s\\n\", key.Curve.Params().Name)

	// 2. Self-signed cert
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: \"localhost\"},
		NotBefore: time.Now(), NotAfter: time.Now().Add(24*time.Hour),
		KeyUsage: x509.KeyUsageDigitalSignature, DNSNames: []string{\"localhost\"},
	}
	certDER, _ := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	cert, _ := x509.ParseCertificate(certDER)
	pemBlock := pem.EncodeToMemory(&pem.Block{Type: \"CERTIFICATE\", Bytes: certDER})
	fmt.Printf(\"Cert subject: %s, valid until: %s\\n\", cert.Subject.CommonName, cert.NotAfter.Format(\"2006-01-02\"))
	fmt.Printf(\"Cert PEM: %d bytes\\n\", len(pemBlock))

	// 3. AES-256-GCM
	aesKey := make([]byte, 32); io.ReadFull(rand.Reader, aesKey)
	block, _ := aes.NewCipher(aesKey)
	gcm, _ := cipher.NewGCM(block)
	nonce := make([]byte, gcm.NonceSize()); io.ReadFull(rand.Reader, nonce)
	msg := []byte(\"Hello, encrypted world!\")
	ciphertext := gcm.Seal(nil, nonce, msg, nil)
	fmt.Printf(\"Original:  %s\\n\", msg)
	fmt.Printf(\"Encrypted: %s...\\n\", hex.EncodeToString(ciphertext)[:20])
	decrypted, _ := gcm.Open(nil, nonce, ciphertext, nil)
	fmt.Printf(\"Decrypted: %s\\n\", decrypted)

	// 4. SHA-256
	h := sha256.Sum256([]byte(\"innoZverse\"))
	fmt.Printf(\"SHA-256: %s\\n\", hex.EncodeToString(h[:]))
}
GOEOF
cd /tmp/crypto_lab && go run main.go"
```

📸 **Verified Output:**
```
ECDSA key: curve=P-256
Cert subject: localhost, valid until: 2026-03-07
Cert PEM: 579 bytes
Original:  Hello, encrypted world!
Encrypted: 9758d207e73d65e000cf...
Decrypted: Hello, encrypted world!
SHA-256: e9d4c841b1fe725cbfde247de55fb80e5fa67bd3e6f4d3f6ce3745fdc6552f76
```

---

## Step 8: Capstone — mTLS Demo (In-Process)

```go
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"io"
	"math/big"
	"net"
	"net/http"
	"time"
)

func genCert(ca *x509.Certificate, caKey *ecdsa.PrivateKey, cn string) (tls.Certificate, *x509.Certificate) {
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(time.Now().UnixNano()),
		Subject:      pkix.Name{CommonName: cn},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth, x509.ExtKeyUsageClientAuth},
		IPAddresses:  []net.IP{net.ParseIP("127.0.0.1")},
		DNSNames:     []string{"localhost"},
	}
	parent := ca
	if parent == nil {
		tmpl.IsCA = true; tmpl.BasicConstraintsValid = true
		tmpl.KeyUsage |= x509.KeyUsageCertSign
		parent = tmpl; caKey = key
	}
	certDER, _ := x509.CreateCertificate(rand.Reader, tmpl, parent, &key.PublicKey, caKey)
	cert, _ := x509.ParseCertificate(certDER)
	keyDER, _ := x509.MarshalECPrivateKey(key)
	tlsCert, _ := tls.X509KeyPair(
		pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER}),
		pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyDER}),
	)
	return tlsCert, cert
}

func main() {
	// Generate CA + server + client certs
	caTLSCert, caCert := genCert(nil, nil, "My CA")
	_ = caTLSCert
	serverTLSCert, _ := genCert(caCert, caTLSCert.PrivateKey.(*ecdsa.PrivateKey), "server")
	clientTLSCert, _ := genCert(caCert, caTLSCert.PrivateKey.(*ecdsa.PrivateKey), "client")

	caPool := x509.NewCertPool()
	caPool.AddCert(caCert)

	// mTLS server
	srv := &http.Server{
		Addr: "127.0.0.1:18444",
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{serverTLSCert},
			ClientCAs:    caPool,
			ClientAuth:   tls.RequireAndVerifyClientCert,
			MinVersion:   tls.VersionTLS13,
		},
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			cn := r.TLS.PeerCertificates[0].Subject.CommonName
			fmt.Fprintf(w, "Hello, %s! mTLS verified.", cn)
		}),
	}
	ln, _ := tls.Listen("tcp", "127.0.0.1:18444", srv.TLSConfig)
	go srv.Serve(ln)
	time.Sleep(50 * time.Millisecond)

	// mTLS client
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				Certificates: []tls.Certificate{clientTLSCert},
				RootCAs:      caPool,
				MinVersion:   tls.VersionTLS13,
			},
		},
	}
	resp, err := client.Get("https://127.0.0.1:18444/")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
	fmt.Println("mTLS handshake successful!")
}
```

---

## Summary

| Algorithm | Package | Use Case |
|-----------|---------|----------|
| ECDSA P-256 | `crypto/ecdsa` | Key generation, signing |
| Self-signed cert | `crypto/x509` | Development TLS |
| mTLS | `crypto/tls` | Service-to-service auth |
| AES-256-GCM | `crypto/aes` + `crypto/cipher` | Symmetric encryption |
| SHA-256 | `crypto/sha256` | Integrity hashing |
| HMAC-SHA256 | `crypto/hmac` | Authenticated hashing |
| bcrypt | `golang.org/x/crypto/bcrypt` | Password storage |

**Key Takeaways:**
- AES-GCM provides both encryption AND authentication (AEAD)
- Never reuse a nonce with the same key — generate fresh random nonce each time
- `hmac.Equal` uses constant-time comparison to prevent timing attacks
- mTLS authenticates both server AND client with certificates
- bcrypt cost 12 is a good default — increase over time as hardware gets faster
- Never store plaintext passwords — always use bcrypt/argon2/scrypt
