# CI/CD Pipelines

Continuous Integration and Continuous Deployment automate testing and delivery.

## GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        run: |
          ssh user@server "cd /app && git pull && systemctl restart app"
```

## Key Principles

- **Commit often** — Small, frequent commits
- **Automate tests** — Never deploy untested code
- **Fast feedback** — Pipelines should complete in minutes
- **One-click rollback** — Always be able to revert
