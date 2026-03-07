# Lab 05: Service Mesh Patterns

**Time:** 60 minutes | **Level:** Architect | **Docker:** `golang:1.22-alpine`

## Overview

Service mesh patterns in Go: mTLS with `crypto/tls`, service discovery via DNS-SD, load balancing strategies (round-robin/consistent hash), gRPC health v1, and Envoy xDS API concepts.

---

## Step 1: mTLS — Mutual TLS Authentication

```go
package mtls

import (
	"crypto/tls"
	"crypto/x509"
	"os"
)

// Server: requires client certificate
func ServerTLSConfig(certFile, keyFile, caFile string) (*tls.Config, error) {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, err
	}

	caCert, err := os.ReadFile(caFile)
	if err != nil {
		return nil, err
	}
	caPool := x509.NewCertPool()
	caPool.AppendCertsFromPEM(caCert)

	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		ClientAuth:   tls.RequireAndVerifyClientCert,
		ClientCAs:    caPool,
		MinVersion:   tls.VersionTLS13,
		CipherSuites: []uint16{
			tls.TLS_AES_256_GCM_SHA384,
			tls.TLS_CHACHA20_POLY1305_SHA256,
		},
	}, nil
}

// Client: presents certificate to server
func ClientTLSConfig(certFile, keyFile, caFile string) (*tls.Config, error) {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, err
	}

	caCert, err := os.ReadFile(caFile)
	if err != nil {
		return nil, err
	}
	caPool := x509.NewCertPool()
	caPool.AppendCertsFromPEM(caCert)

	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caPool,
		MinVersion:   tls.VersionTLS13,
	}, nil
}
```

---

## Step 2: Certificate Generation (Self-Signed for Development)

```go
package certs

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"time"
)

type CertBundle struct {
	CertPEM []byte
	KeyPEM  []byte
	Cert    *x509.Certificate
	Key     *ecdsa.PrivateKey
}

func GenerateCA() (*CertBundle, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, err
	}

	template := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"My Service Mesh"},
			CommonName:   "Root CA",
		},
		NotBefore:             time.Now(),
		NotAfter:              time.Now().Add(365 * 24 * time.Hour),
		IsCA:                  true,
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign,
		BasicConstraintsValid: true,
	}

	certDER, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return nil, err
	}

	cert, _ := x509.ParseCertificate(certDER)
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})
	keyBytes, _ := x509.MarshalECPrivateKey(key)
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyBytes})

	return &CertBundle{CertPEM: certPEM, KeyPEM: keyPEM, Cert: cert, Key: key}, nil
}

func GenerateServiceCert(serviceName string, ca *CertBundle) (*CertBundle, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, err
	}

	template := &x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject: pkix.Name{
			Organization: []string{"My Service Mesh"},
			CommonName:   serviceName,
		},
		DNSNames:  []string{serviceName, serviceName + ".svc.cluster.local"},
		NotBefore: time.Now(),
		NotAfter:  time.Now().Add(24 * time.Hour), // Short-lived certs
		KeyUsage:  x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{
			x509.ExtKeyUsageServerAuth,
			x509.ExtKeyUsageClientAuth,
		},
	}

	certDER, err := x509.CreateCertificate(rand.Reader, template, ca.Cert, &key.PublicKey, ca.Key)
	if err != nil {
		return nil, err
	}

	cert, _ := x509.ParseCertificate(certDER)
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})
	keyBytes, _ := x509.MarshalECPrivateKey(key)
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyBytes})

	return &CertBundle{CertPEM: certPEM, KeyPEM: keyPEM, Cert: cert, Key: key}, nil
}
```

---

## Step 3: Service Discovery — DNS-SD

```go
package discovery

import (
	"fmt"
	"net"
)

// DNS-SD: SRV records for service discovery
// _service._proto.name → host, port, priority, weight

type ServiceEndpoint struct {
	Host     string
	Port     int
	Priority int
	Weight   int
}

func DiscoverService(service, proto, domain string) ([]ServiceEndpoint, error) {
	// Query: _my-service._tcp.svc.cluster.local
	name := fmt.Sprintf("_%s._%s.%s", service, proto, domain)

	_, addrs, err := net.LookupSRV(service, proto, domain)
	if err != nil {
		return nil, fmt.Errorf("DNS-SD lookup %s: %w", name, err)
	}

	endpoints := make([]ServiceEndpoint, 0, len(addrs))
	for _, addr := range addrs {
		endpoints = append(endpoints, ServiceEndpoint{
			Host:     addr.Target,
			Port:     int(addr.Port),
			Priority: int(addr.Priority),
			Weight:   int(addr.Weight),
		})
	}
	return endpoints, nil
}
```

---

## Step 4: Load Balancing Strategies

```go
package lb

import (
	"hash/fnv"
	"sync/atomic"
)

type Backend struct {
	Host        string
	Port        int
	ActiveConns int64
}

// Round-robin load balancer
type RoundRobin struct {
	backends []*Backend
	counter  atomic.Uint64
}

func (rr *RoundRobin) Next() *Backend {
	if len(rr.backends) == 0 {
		return nil
	}
	idx := rr.counter.Add(1) - 1
	return rr.backends[idx%uint64(len(rr.backends))]
}

// Least connections
type LeastConn struct {
	backends []*Backend
}

func (lc *LeastConn) Next() *Backend {
	if len(lc.backends) == 0 {
		return nil
	}
	best := lc.backends[0]
	for _, b := range lc.backends[1:] {
		if atomic.LoadInt64(&b.ActiveConns) < atomic.LoadInt64(&best.ActiveConns) {
			best = b
		}
	}
	return best
}

// Consistent hash
type ConsistentHash struct {
	backends []*Backend
}

func (ch *ConsistentHash) Next(key string) *Backend {
	if len(ch.backends) == 0 {
		return nil
	}
	h := fnv.New32a()
	h.Write([]byte(key))
	idx := int(h.Sum32()) % len(ch.backends)
	return ch.backends[idx]
}
```

---

## Step 5: gRPC Health Check Protocol

```go
package health

import (
	"context"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc"
)

// gRPC health check server (standard proto)
func RegisterHealthServer(s *grpc.Server) *health.Server {
	hs := health.NewServer()

	// Set initial status
	hs.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	hs.SetServingStatus("my.service.v1.UserService",
		grpc_health_v1.HealthCheckResponse_SERVING)

	grpc_health_v1.RegisterHealthServer(s, hs)
	return hs
}

// Update status when dependencies change
func UpdateHealth(hs *health.Server, db Database) {
	if err := db.Ping(context.Background()); err != nil {
		hs.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
	} else {
		hs.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	}
}

// Client-side health check
// grpc_health_v1.NewHealthClient(conn).Check(ctx,
//   &grpc_health_v1.HealthCheckRequest{Service: "my.service.v1.UserService"})
```

---

## Step 6: HTTP Health Endpoint

```go
package health

import (
	"encoding/json"
	"net/http"
	"time"
)

type HealthStatus struct {
	Status    string            `json:"status"`  // "healthy", "degraded", "unhealthy"
	Checks    map[string]string `json:"checks"`
	Timestamp time.Time         `json:"timestamp"`
	Version   string            `json:"version"`
}

func HealthHandler(deps Dependencies) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		status := HealthStatus{
			Status:    "healthy",
			Checks:    make(map[string]string),
			Timestamp: time.Now(),
			Version:   Version,
		}

		if err := deps.DB.Ping(r.Context()); err != nil {
			status.Checks["database"] = "unhealthy: " + err.Error()
			status.Status = "unhealthy"
		} else {
			status.Checks["database"] = "healthy"
		}

		if err := deps.Cache.Ping(r.Context()); err != nil {
			status.Checks["cache"] = "degraded: " + err.Error()
			if status.Status == "healthy" {
				status.Status = "degraded"
			}
		} else {
			status.Checks["cache"] = "healthy"
		}

		code := http.StatusOK
		if status.Status == "unhealthy" {
			code = http.StatusServiceUnavailable
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(code)
		json.NewEncoder(w).Encode(status)
	}
}
```

---

## Step 7: Envoy xDS — Concept

```go
// Envoy xDS API: dynamic configuration protocol
// Types:
//   LDS (Listener Discovery Service): port bindings
//   RDS (Route Discovery Service):    HTTP routing rules
//   CDS (Cluster Discovery Service):  upstream service definitions
//   EDS (Endpoint Discovery Service): individual backend IPs

// Go control plane: use envoy-control-plane library
// import (
//   "github.com/envoyproxy/go-control-plane/pkg/cache/v3"
//   "github.com/envoyproxy/go-control-plane/pkg/server/v3"
// )

// Snapshot: atomic update to all xDS resources
// snapshot := cachev3.NewSnapshot("v1",
//   map[resource.Type][]types.Resource{
//     resource.ClusterType:  {makeCluster("user-service")},
//     resource.EndpointType: {makeEndpoints("user-service", []string{"10.0.0.1:8080", "10.0.0.2:8080"})},
//   })
// cache.SetSnapshot(ctx, nodeID, snapshot)
```

---

## Step 8: Capstone — mTLS Certificate Generation

```bash
docker run --rm golang:1.22-alpine sh -c "cat > /tmp/main.go << 'GOEOF'
package main

import (
  \"crypto/rand\"
  \"crypto/rsa\"
  \"crypto/tls\"
  \"crypto/x509\"
  \"crypto/x509/pkix\"
  \"encoding/pem\"
  \"fmt\"
  \"math/big\"
  \"time\"
)

func genCert(isCA bool, parent *x509.Certificate, pk *rsa.PrivateKey) (*x509.Certificate, *rsa.PrivateKey, []byte, []byte) {
  key, _ := rsa.GenerateKey(rand.Reader, 2048)
  t := &x509.Certificate{SerialNumber: big.NewInt(time.Now().UnixNano()),
    Subject: pkix.Name{Organization: []string{\"Test\"}, CommonName: \"test\"},
    NotBefore: time.Now(), NotAfter: time.Now().Add(time.Hour),
    KeyUsage: x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign, IsCA: isCA, BasicConstraintsValid: true}
  if parent == nil { parent = t; pk = key }
  der, _ := x509.CreateCertificate(rand.Reader, t, parent, &key.PublicKey, pk)
  cert, _ := x509.ParseCertificate(der)
  return cert, key, pem.EncodeToMemory(&pem.Block{Type:\"CERTIFICATE\",Bytes:der}), pem.EncodeToMemory(&pem.Block{Type:\"RSA PRIVATE KEY\",Bytes:x509.MarshalPKCS1PrivateKey(key)})
}

func main() {
  caCert, caKey, caCertPEM, _ := genCert(true, nil, nil)
  fmt.Printf(\"CA Certificate generated: %s\\n\", caCert.Subject.CommonName)
  fmt.Printf(\"CA PEM length: %d bytes\\n\", len(caCertPEM))
  _, _, sCertPEM, sKeyPEM := genCert(false, caCert, caKey)
  fmt.Printf(\"Server Certificate: signed by CA\\n\")
  caPool := x509.NewCertPool(); caPool.AppendCertsFromPEM(caCertPEM)
  tlsCert, _ := tls.X509KeyPair(sCertPEM, sKeyPEM)
  cfg := &tls.Config{Certificates:[]tls.Certificate{tlsCert}, ClientAuth:tls.RequireAndVerifyClientCert, ClientCAs:caPool, MinVersion:tls.VersionTLS13}
  _ = cfg
  fmt.Printf(\"mTLS Config: ClientAuth=RequireAndVerifyClientCert\\n\")
  fmt.Printf(\"mTLS Config: MinVersion=TLS 1.3\\n\")
  fmt.Printf(\"mTLS ready: server will reject clients without valid cert\\n\")
}
GOEOF
cd /tmp && go run main.go"
```

📸 **Verified Output:**
```
CA Certificate generated: test
CA PEM length: 1115 bytes
Server Certificate: signed by CA
mTLS Config: ClientAuth=RequireAndVerifyClientCert
mTLS Config: MinVersion=TLS 1.3
mTLS ready: server will reject clients without valid cert
```

---

## Summary

| Pattern | Implementation | Notes |
|---------|---------------|-------|
| mTLS | `crypto/tls.RequireAndVerifyClientCert` | Both sides present cert |
| Short-lived certs | 24h cert TTL | Rotation via SPIFFE/SPIRE |
| DNS-SD | `net.LookupSRV` | Kubernetes-native |
| Round-robin | `atomic.Uint64` counter | Lock-free |
| Least conn | Min `ActiveConns` scan | For long connections |
| Consistent hash | FNV hash % backends | Session affinity |
| Health check | gRPC health v1 | Standard protocol |
| Envoy xDS | Go control plane | Dynamic config push |
