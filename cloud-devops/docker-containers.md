# Docker & Containers

Containers package your application with all its dependencies, ensuring it runs consistently everywhere.

## Core Concepts

- **Image** — Blueprint for a container (read-only)
- **Container** — Running instance of an image
- **Dockerfile** — Instructions to build an image
- **Registry** — Store for images (Docker Hub, ECR)

## Essential Commands

```bash
# Images
docker pull nginx               # Download image
docker images                   # List local images
docker build -t myapp:1.0 .    # Build from Dockerfile
docker push myapp:1.0           # Push to registry

# Containers
docker run -d -p 80:80 nginx    # Run detached, map ports
docker ps                       # List running containers
docker ps -a                    # All containers
docker logs container_id        # View logs
docker exec -it container_id bash  # Shell into container
docker stop container_id        # Stop container
docker rm container_id          # Remove container
```

## Sample Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
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
      - DATABASE_URL=postgres://db/myapp
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
docker-compose up -d    # Start all services
docker-compose down     # Stop and remove
docker-compose logs     # View all logs
```
