# GitHub Actions

GitHub Actions automates workflows directly in your GitHub repository.

## Key Concepts

- **Workflow** — Automated process defined in YAML
- **Event** — Trigger (push, PR, schedule, manual)
- **Job** — Group of steps running on one runner
- **Step** — Individual task within a job
- **Action** — Reusable unit of work

## Common Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 9 * * 1'      # Every Monday 9 AM
  workflow_dispatch:          # Manual trigger
  release:
    types: [published]
```

## Useful Actions

```yaml
steps:
  - uses: actions/checkout@v4                    # Checkout code
  - uses: actions/setup-python@v4               # Setup Python
  - uses: actions/setup-node@v4                 # Setup Node.js
  - uses: actions/cache@v3                      # Cache dependencies
  - uses: actions/upload-artifact@v3            # Upload build artifacts
  - uses: docker/build-push-action@v5           # Build & push Docker
  - uses: aws-actions/configure-aws-credentials@v4  # AWS auth
```

## Matrix Strategy (Test Multiple Versions)

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pytest
```
