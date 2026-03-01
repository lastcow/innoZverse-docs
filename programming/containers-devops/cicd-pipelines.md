# CI/CD Pipelines

CI/CD automates testing, building, and deploying software.

- **CI (Continuous Integration)** — Automatically test every commit
- **CD (Continuous Delivery)** — Always have deployable code
- **CD (Continuous Deployment)** — Automatically deploy to production

## GitHub Actions

```yaml
# .github/workflows/main.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest --cov=. --cov-report=xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push myapp:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          ssh -i ${{ secrets.SSH_KEY }} deploy@prod.example.com \
            "docker pull myapp:${{ github.sha }} && docker-compose up -d"
```
