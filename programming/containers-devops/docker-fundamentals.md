# Docker Fundamentals

## Core Concepts

- **Image** — Read-only template (like a class)
- **Container** — Running instance of an image (like an object)
- **Dockerfile** — Instructions to build an image
- **Registry** — Repository for images (Docker Hub, ECR, GCR)
- **Volume** — Persistent data storage
- **Network** — Communication between containers

## Essential Commands

```bash
# Images
docker pull nginx:latest            # Download image
docker images                       # List local images
docker build -t myapp:1.0 .        # Build from Dockerfile
docker tag myapp:1.0 registry/myapp:1.0
docker push registry/myapp:1.0     # Push to registry
docker rmi myapp:1.0               # Remove image

# Containers
docker run -d -p 8080:80 --name web nginx   # Run detached
docker run -it ubuntu bash                  # Interactive shell
docker ps                                   # Running containers
docker ps -a                               # All containers
docker logs -f web                         # Follow logs
docker exec -it web bash                   # Shell into container
docker stop web                            # Stop gracefully
docker rm web                              # Remove container

# Cleanup
docker system prune -a                     # Remove all unused resources
```

## Dockerfile Best Practices

```dockerfile
# Use specific version tags (not :latest)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Document exposed port
EXPOSE 8000

# Use exec form (not shell form)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb

volumes:
  postgres_data:
```

```bash
docker-compose up -d            # Start all services
docker-compose down             # Stop and remove containers
docker-compose logs -f web      # Follow web service logs
docker-compose exec web bash    # Shell into web container
docker-compose ps               # Status of services
```
