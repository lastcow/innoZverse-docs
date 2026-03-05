# Lab 13: Containerizing Node.js

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Best practices for Docker with Node.js: multi-stage builds, `.dockerignore`, non-root user, layer caching, health checks, graceful shutdown, and Docker Compose.

---

## Step 1: Basic Dockerfile (and Why It's Bad)

```dockerfile
# BAD: Don't do this
FROM node:20
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD ["node", "server.js"]

# Problems:
# 1. Uses full node image (1GB+) instead of alpine (~150MB)
# 2. COPY . . before npm install breaks layer caching
# 3. Runs as root — security risk
# 4. Dev dependencies included in production
# 5. No health check
# 6. No graceful shutdown handling
```

---

## Step 2: Production Dockerfile

```dockerfile
# GOOD: Multi-stage production Dockerfile
# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests FIRST (layer caching!)
COPY package*.json ./

# Install all dependencies (including dev for build)
RUN npm ci

# Copy source code
COPY . .

# Build step (TypeScript compile, bundling, etc.)
RUN npm run build --if-present

# Prune dev dependencies
RUN npm prune --production

# ─────────────────────────────────────
# Stage 2: Production
FROM node:20-alpine AS production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user/group
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodeuser -u 1001 -G nodejs

WORKDIR /app

# Copy only what we need from builder
COPY --from=builder --chown=nodeuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodeuser:nodejs /app/dist ./dist
COPY --from=builder --chown=nodeuser:nodejs /app/package.json ./

# Switch to non-root user
USER nodeuser

# Expose port (documentation only)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Use dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

---

## Step 3: .dockerignore

```
# .dockerignore — exclude from build context
node_modules
npm-debug.log*
.npm
.git
.gitignore
.env
.env.*
*.log
*.md
coverage/
.nyc_output
.vscode
.idea
dist/
build/
.turbo
*.test.js
*.spec.js
__tests__
docs/
.github
Dockerfile*
docker-compose*
.dockerignore
```

> 💡 A good `.dockerignore` can reduce build context by 90%+ and prevent secrets from entering the build.

---

## Step 4: Health Check Script

```javascript
// healthcheck.js
const http = require('node:http');

const options = {
  host: 'localhost',
  port: process.env.PORT || 3000,
  path: '/health',
  timeout: 5000,
};

const request = http.request(options, (res) => {
  if (res.statusCode === 200) {
    process.exit(0); // Healthy
  } else {
    console.error(`Health check failed: HTTP ${res.statusCode}`);
    process.exit(1); // Unhealthy
  }
});

request.on('error', (err) => {
  console.error('Health check error:', err.message);
  process.exit(1);
});

request.on('timeout', () => {
  request.destroy();
  console.error('Health check timeout');
  process.exit(1);
});

request.end();
```

---

## Step 5: Graceful Shutdown in Containerized Apps

```javascript
// server.js — production-ready server
const http = require('node:http');
const app = require('./app');

const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

// Track active connections
const connections = new Set();
server.on('connection', (conn) => {
  connections.add(conn);
  conn.on('close', () => connections.delete(conn));
});

server.listen(PORT, () => {
  console.log(JSON.stringify({
    level: 'info',
    msg: `Server listening`,
    port: PORT,
    pid: process.pid,
    env: process.env.NODE_ENV
  }));
});

// Graceful shutdown
let isShuttingDown = false;

async function shutdown(signal) {
  if (isShuttingDown) return;
  isShuttingDown = true;

  console.log(JSON.stringify({ level: 'info', msg: `Shutdown: ${signal}` }));

  // Stop accepting new connections
  server.close(async (err) => {
    if (err) console.error('Server close error:', err);

    // Close existing connections
    for (const conn of connections) conn.destroy();

    // Cleanup resources (DB, Redis, etc.)
    try {
      await Promise.all([
        db?.destroy(),
        redis?.quit()
      ]);
      console.log(JSON.stringify({ level: 'info', msg: 'Cleanup complete' }));
      process.exit(0);
    } catch (e) {
      console.error('Cleanup error:', e.message);
      process.exit(1);
    }
  });

  // Force shutdown after timeout
  setTimeout(() => {
    console.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM')); // Docker stop
process.on('SIGINT', () => shutdown('SIGINT'));   // Ctrl+C
```

---

## Step 6: Docker Compose for Full Stack

```yaml
# docker-compose.yml
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: my-api:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass redispassword
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - api
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

---

## Step 7: Layer Caching Optimization

```dockerfile
# Optimal layer ordering for cache efficiency

FROM node:20-alpine AS base
RUN apk add --no-cache dumb-init

# Layer 1: package manifests (rarely changes)
COPY package*.json ./
# Layer 2: install (cached if package.json unchanged)
RUN npm ci --only=production

# Layer 3: app source (changes frequently)
COPY src/ ./src/
COPY public/ ./public/

# For monorepos:
FROM node:20-alpine AS builder
WORKDIR /app

# Copy all workspace package manifests first
COPY package*.json ./
COPY packages/utils/package*.json ./packages/utils/
COPY packages/api/package*.json ./packages/api/
# Now install (cached until any package.json changes)
RUN npm ci

# Then copy source
COPY packages/ ./packages/
RUN npm run build
```

---

## Step 8: Capstone — Build & Run Demo

```bash
docker run --rm node:20-alpine sh -c "
# Simulate multi-stage build output verification
cat > /tmp/server.js << 'EOF'
const http = require('http');
const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({ status: 'ok', pid: process.pid }));
  } else {
    res.writeHead(404); res.end('Not found');
  }
});

let connections = new Set();
server.on('connection', conn => { connections.add(conn); conn.on('close', () => connections.delete(conn)); });

server.listen(9999, () => {
  console.log('Server started on :9999');
  
  // Test health check
  http.get('http://localhost:9999/health', (res) => {
    let data = '';
    res.on('data', d => data += d);
    res.on('end', () => {
      console.log('Health check:', res.statusCode, JSON.parse(data).status);
      
      // Simulate graceful shutdown
      server.close(() => {
        console.log('Server closed gracefully');
        process.exit(0);
      });
      connections.forEach(c => c.destroy());
    });
  });
});

process.on('SIGTERM', () => { console.log('SIGTERM received'); server.close(); });
EOF
node /tmp/server.js
"
```

📸 **Verified Output:**
```
Server started on :9999
Health check: 200 ok
Server closed gracefully
```

---

## Summary

| Best Practice | Implementation | Benefit |
|---------------|---------------|---------|
| Alpine base image | `FROM node:20-alpine` | ~150MB vs ~1GB |
| Multi-stage build | `FROM ... AS builder` | Smaller prod image |
| Layer caching | COPY package*.json first | Faster rebuilds |
| Non-root user | `adduser` + `USER nodeuser` | Security |
| `.dockerignore` | Exclude node_modules etc | Smaller context |
| Health check | `HEALTHCHECK` instruction | Container orchestration |
| Graceful shutdown | SIGTERM handler | Zero-downtime deploys |
| `dumb-init` | PID 1 replacement | Proper signal forwarding |
| Resource limits | `deploy.resources.limits` | Prevent OOM in compose |
