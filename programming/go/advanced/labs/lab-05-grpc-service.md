# Lab 05: gRPC Service

**Time:** 45 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm golang:1.22-alpine sh`

## Overview

Build a production-grade gRPC service with Protocol Buffers, unary and server-streaming RPCs, interceptors, metadata, and proper error handling with status codes.

---

## Step 1: Install Tools

```bash
# Install protoc (Protocol Buffer compiler)
docker run -it --rm golang:1.22-alpine sh -c "
apk add --no-cache protobuf protobuf-dev curl
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
export PATH=\$PATH:\$(go env GOPATH)/bin
protoc --version
echo 'Tools installed'
"
```

> 💡 **On macOS:** `brew install protobuf` then `go install` the plugins.

---

## Step 2: Define the Protobuf Schema

```protobuf
// product.proto
syntax = "proto3";

package product;
option go_package = "./pb";

// Unary RPC: Get a single product
message GetProductRequest {
  string id = 1;
}

message Product {
  string id     = 1;
  string name   = 2;
  double price  = 3;
  int32  stock  = 4;
}

// Server-streaming RPC: List products
message ListProductsRequest {
  string category = 1;
  int32  limit    = 2;
}

service ProductService {
  rpc GetProduct(GetProductRequest) returns (Product);
  rpc ListProducts(ListProductsRequest) returns (stream Product);
}
```

Compile:
```bash
mkdir -p pb
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       product.proto
```

---

## Step 3: Implement the gRPC Server

```go
// server/main.go
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	pb "github.com/yourorg/grpclab/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

type productServer struct {
	pb.UnimplementedProductServiceServer
	products map[string]*pb.Product
}

func newProductServer() *productServer {
	return &productServer{
		products: map[string]*pb.Product{
			"1": {Id: "1", Name: "Go Book", Price: 39.99, Stock: 100},
			"2": {Id: "2", Name: "Rust Book", Price: 44.99, Stock: 50},
			"3": {Id: "3", Name: "K8s Guide", Price: 59.99, Stock: 25},
		},
	}
}

// Unary RPC
func (s *productServer) GetProduct(ctx context.Context, req *pb.GetProductRequest) (*pb.Product, error) {
	// Read metadata
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if auth := md.Get("authorization"); len(auth) > 0 {
			log.Printf("Auth: %s", auth[0])
		}
	}

	p, ok := s.products[req.Id]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "product %q not found", req.Id)
	}
	return p, nil
}

// Server-streaming RPC
func (s *productServer) ListProducts(req *pb.ListProductsRequest, stream pb.ProductService_ListProductsServer) error {
	limit := int(req.Limit)
	if limit <= 0 {
		limit = 10
	}
	count := 0
	for _, p := range s.products {
		if count >= limit {
			break
		}
		if err := stream.Send(p); err != nil {
			return err
		}
		time.Sleep(50 * time.Millisecond) // simulate work
		count++
	}
	return nil
}

// Logging interceptor
func loggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	start := time.Now()
	resp, err := handler(ctx, req)
	log.Printf("RPC %s duration=%v err=%v", info.FullMethod, time.Since(start), err)
	return resp, err
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	srv := grpc.NewServer(
		grpc.UnaryInterceptor(loggingInterceptor),
	)
	pb.RegisterProductServiceServer(srv, newProductServer())

	fmt.Println("gRPC server listening on :50051")
	if err := srv.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
```

---

## Step 4: Implement the gRPC Client

```go
// client/main.go
package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"time"

	pb "github.com/yourorg/grpclab/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

func main() {
	conn, err := grpc.Dial("localhost:50051",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		log.Fatalf("dial: %v", err)
	}
	defer conn.Close()

	client := pb.NewProductServiceClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Add metadata (auth token)
	md := metadata.Pairs("authorization", "Bearer token123")
	ctx = metadata.NewOutgoingContext(ctx, md)

	// Unary call
	fmt.Println("=== GetProduct ===")
	p, err := client.GetProduct(ctx, &pb.GetProductRequest{Id: "1"})
	if err != nil {
		st, _ := status.FromError(err)
		fmt.Printf("Error code=%s msg=%s\n", st.Code(), st.Message())
	} else {
		fmt.Printf("Product: id=%s name=%s price=%.2f stock=%d\n",
			p.Id, p.Name, p.Price, p.Stock)
	}

	// Not found error
	_, err = client.GetProduct(ctx, &pb.GetProductRequest{Id: "999"})
	if st, ok := status.FromError(err); ok {
		fmt.Printf("Expected error: code=%s\n", st.Code())
		if st.Code() == codes.NotFound {
			fmt.Println("Handled NotFound gracefully")
		}
	}

	// Streaming call
	fmt.Println("\n=== ListProducts ===")
	stream, err := client.ListProducts(ctx, &pb.ListProductsRequest{Limit: 5})
	if err != nil {
		log.Fatalf("ListProducts: %v", err)
	}
	for {
		p, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("stream recv: %v", err)
		}
		fmt.Printf("  Streamed: %s ($%.2f)\n", p.Name, p.Price)
	}
}
```

---

## Step 5: gRPC Interceptors

```go
// interceptors.go

// Unary server interceptor: authentication
func authInterceptor(secret string) grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
		md, ok := metadata.FromIncomingContext(ctx)
		if !ok {
			return nil, status.Error(codes.Unauthenticated, "missing metadata")
		}
		auth := md.Get("authorization")
		if len(auth) == 0 || auth[0] != "Bearer "+secret {
			return nil, status.Error(codes.Unauthenticated, "invalid token")
		}
		return handler(ctx, req)
	}
}

// Chain multiple interceptors
func chainInterceptors(interceptors ...grpc.UnaryServerInterceptor) grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
		chain := handler
		for i := len(interceptors) - 1; i >= 0; i-- {
			i := i
			prev := chain
			chain = func(ctx context.Context, req interface{}) (interface{}, error) {
				return interceptors[i](ctx, req, info, prev)
			}
		}
		return chain(ctx, req)
	}
}
```

> 💡 **In production**, use `google.golang.org/grpc/middleware` or `go.uber.org/zap` + grpc interceptors for structured logging, tracing, and metrics.

---

## Step 6: Status Codes & Error Handling

```go
package main

import (
	"fmt"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func validateProductID(id string) error {
	if id == "" {
		return status.Error(codes.InvalidArgument, "product ID cannot be empty")
	}
	if len(id) > 50 {
		return status.Error(codes.InvalidArgument, "product ID too long (max 50 chars)")
	}
	return nil
}

func getProduct(id string) (*Product, error) {
	if err := validateProductID(id); err != nil {
		return nil, err
	}
	// not found
	return nil, status.Errorf(codes.NotFound, "product %q not found", id)
}

func handleError(err error) {
	if err == nil {
		return
	}
	st, ok := status.FromError(err)
	if !ok {
		fmt.Printf("Non-gRPC error: %v\n", err)
		return
	}
	switch st.Code() {
	case codes.NotFound:
		fmt.Printf("Not found: %s\n", st.Message())
	case codes.InvalidArgument:
		fmt.Printf("Bad request: %s\n", st.Message())
	case codes.Unauthenticated:
		fmt.Printf("Auth error: %s\n", st.Message())
	case codes.Unavailable:
		fmt.Printf("Service unavailable: %s (retry)\n", st.Message())
	default:
		fmt.Printf("Error %s: %s\n", st.Code(), st.Message())
	}
}
```

---

## Step 7: Full Working Example (Single File, No Proto)

```go
// grpc_demo.go — demonstrates gRPC concepts without protoc
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
)

// Manual service descriptor (normally generated by protoc)
const serviceDesc = `
syntax = "proto3";
service GreetService {
  rpc SayHello (HelloRequest) returns (HelloReply);
}
message HelloRequest { string name = 1; }
message HelloReply   { string message = 1; }
`

func main() {
	fmt.Println("gRPC concepts demonstrated above")
	fmt.Println("Full working example requires protoc-generated code")
	fmt.Println("See steps 2-4 for complete server+client implementation")

	// Demonstrate status codes
	err1 := status.Errorf(codes.NotFound, "user %q not found", "alice")
	err2 := status.Error(codes.InvalidArgument, "name cannot be empty")

	for _, err := range []error{err1, err2} {
		st, _ := status.FromError(err)
		fmt.Printf("Code: %-20s Message: %s\n", st.Code(), st.Message())
	}
}
```

---

## Step 8: Capstone — Run gRPC Server + Client

```bash
# Full setup in Docker
docker run --rm golang:1.22-alpine sh -c "
apk add --no-cache protobuf >/dev/null 2>&1
mkdir -p /tmp/grpclab/pb /tmp/grpclab/server /tmp/grpclab/client

# go.mod
cd /tmp/grpclab && cat > go.mod << 'EOF'
module grpclab
go 1.22
EOF
go get google.golang.org/grpc@v1.62.0
go get google.golang.org/protobuf@v1.33.0
go mod tidy

# Since protoc isn't available without generated code, demonstrate via echo
echo 'gRPC setup complete'
echo 'To run: protoc --go_out=. --go-grpc_out=. *.proto'
echo 'Then: go run server/main.go &; go run client/main.go'
"
```

For a runnable demo without protoc:
```bash
docker run --rm golang:1.22-alpine sh -c "
mkdir -p /tmp/grpcdemo
cd /tmp/grpcdemo
cat > go.mod << 'EOF'
module grpcdemo
go 1.22
EOF
go get google.golang.org/grpc@v1.62.0 2>/dev/null
cat > main.go << 'GOEOF'
package main

import (
	\"fmt\"
	\"google.golang.org/grpc/codes\"
	\"google.golang.org/grpc/status\"
)

func main() {
	// Demonstrate status code handling
	errors := []error{
		status.Error(codes.NotFound, \"product not found\"),
		status.Error(codes.InvalidArgument, \"invalid product ID\"),
		status.Error(codes.Unavailable, \"service temporarily unavailable\"),
		status.Error(codes.PermissionDenied, \"access denied\"),
	}
	for _, err := range errors {
		st, _ := status.FromError(err)
		fmt.Printf(\"Code: %-20s Message: %s\n\", st.Code(), st.Message())
	}
	fmt.Println(\"\\ngRPC status codes:\")
	fmt.Println(\"  codes.OK              = 0\")
	fmt.Println(\"  codes.NotFound        = 5\")
	fmt.Println(\"  codes.InvalidArgument = 3\")
	fmt.Println(\"  codes.Unauthenticated = 16\")
	fmt.Println(\"  codes.PermissionDenied= 7\")
	fmt.Println(\"  codes.Unavailable     = 14\")
}
GOEOF
go run main.go 2>&1" 2>&1 | tail -20
```

📸 **Verified Output:**
```
Code: NotFound             Message: product not found
Code: InvalidArgument      Message: invalid product ID
Code: Unavailable          Message: service temporarily unavailable
Code: PermissionDenied     Message: access denied

gRPC status codes:
  codes.OK              = 0
  codes.NotFound        = 5
  codes.InvalidArgument = 3
  codes.Unauthenticated = 16
  codes.PermissionDenied= 7
  codes.Unavailable     = 14
```

---

## Summary

| Concept | API | Notes |
|---------|-----|-------|
| Unary RPC | `func(ctx, req) (resp, error)` | Request-response |
| Server streaming | `func(req, stream) error` | Server sends multiple messages |
| Client streaming | `func(stream) error` | Client sends multiple messages |
| Bidirectional | `func(stream) error` | Full duplex |
| Interceptor | `grpc.UnaryServerInterceptor` | Auth, logging, metrics |
| Metadata | `metadata.FromIncomingContext` | HTTP headers equivalent |
| Status codes | `status.Errorf(codes.NotFound, ...)` | Structured errors |

**Key Takeaways:**
- protobuf schema is the single source of truth — generate, don't handwrite
- Always embed `Unimplemented*Server` for forward compatibility
- Use interceptors for cross-cutting concerns (auth, tracing, logging)
- Status codes map to HTTP status codes — use them semantically
- `io.EOF` on stream.Recv() is normal end-of-stream, not an error
