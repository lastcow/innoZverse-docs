# Lab 10: DevSecOps Pipeline

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Design a complete DevSecOps pipeline with security gates
- Run SAST with Bandit on vulnerable Python code
- Understand DAST, SCA/SBOM, secret scanning, IaC scanning
- Define security gates and break-build policies

---

## Step 1: DevSecOps Pipeline Architecture

```
Developer → Git Push
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                  CI/CD PIPELINE                          │
│                                                         │
│  PRE-COMMIT        BUILD            TEST                │
│  ┌───────────┐  ┌──────────┐   ┌──────────────────┐   │
│  │Secret scan│  │SAST      │   │DAST (ZAP)        │   │
│  │(git-secrets│  │(Bandit,  │   │SCA/SBOM          │   │
│  │detect-sec)│  │Semgrep)  │   │Container scan    │   │
│  └───────────┘  └──────────┘   │IaC scan (checkov)│   │
│                                └──────────────────┘   │
│                                                         │
│  SECURITY GATES                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ No CRITICAL CVEs │ No HIGH SAST │ No secrets    │   │
│  │ IaC compliant    │ SBOM attached │ DAST passing  │   │
│  └─────────────────────────────────────────────────┘   │
│              │                                          │
│              ▼                                          │
│         Deploy to                                       │
│    Staging → Production                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Step 2: SAST with Bandit

**Vulnerable Python code:**

```python
# vulnerable_app.py
import subprocess, pickle, hashlib

password = "hardcoded_secret_123"
token = "ghp_abc123secret"

def run_cmd(user_input):
    cmd = "ls " + user_input          # Command injection
    subprocess.call(cmd, shell=True)

def load_data(data):
    return pickle.loads(data)         # Insecure deserialization

def weak_hash(data):
    return hashlib.md5(data.encode()).hexdigest()  # Weak crypto
```

**Run Bandit:**
```bash
# In docker container
pip install bandit -q
cat > /tmp/vuln.py << 'EOF'
import subprocess, pickle, hashlib
password = "hardcoded_secret_123"
def run_cmd(user_input):
    cmd = "ls " + user_input
    subprocess.call(cmd, shell=True)
def load_data(data): return pickle.loads(data)
def weak_hash(data): return hashlib.md5(data.encode()).hexdigest()
EOF

bandit --severity-level medium /tmp/vuln.py
```

📸 **Verified Output (medium+ severity):**
```
Run started:2026-03-05 16:11:40.610267+00:00

Test results:
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
   Severity: High   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   Location: /tmp/vuln.py:6:4
5    cmd = "ls " + user_input
6    subprocess.call(cmd, shell=True)

--------------------------------------------------
>> Issue: [B301:blacklist] Pickle and modules that wrap it can be unsafe when used to
   deserialize untrusted data, possible security issue.
   Severity: Medium   Confidence: High
   CWE: CWE-502 (...)
```

---

## Step 3: Secret Scanning

**Tools:**
- `detect-secrets` — pre-commit hook; entropy + pattern-based
- `trufflehog` — git history scanning; finds secrets in commits
- `gitleaks` — SAST for secrets in source code
- GitHub Advanced Security — native secret scanning + push protection

**Pre-commit config:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

**Common secret patterns detected:**
```
AWS Access Key:    AKIA[0-9A-Z]{16}
GitHub Token:      ghp_[a-zA-Z0-9]{36}
Slack Token:       xox[baprs]-[0-9a-zA-Z]{10,48}
Private Key:       -----BEGIN RSA PRIVATE KEY-----
Google API:        AIza[0-9A-Za-z\\-_]{35}
```

> 💡 **If a secret is committed to git**, assume it's compromised — git history is permanent. Rotate immediately, then remove from history with `git-filter-repo` or BFG Repo Cleaner.

---

## Step 4: SCA and SBOM

**Software Composition Analysis (SCA):**
- Identifies open-source components and their CVEs
- Tools: Snyk, OWASP Dependency-Check, Grype, Trivy (filesystem mode)

**SBOM (Software Bill of Materials):**
- Machine-readable inventory of all components
- Formats: SPDX, CycloneDX
- Required by: US Executive Order 14028, PCI DSS 4.0, NIST SSDF

```bash
# Generate SBOM with Syft
syft nginx:latest -o cyclonedx-json > sbom.json

# Scan SBOM for CVEs with Grype
grype sbom:sbom.json
```

**SBOM structure (CycloneDX):**
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "components": [
    {
      "name": "flask",
      "version": "2.0.1",
      "purl": "pkg:pypi/flask@2.0.1",
      "licenses": [{"expression": "BSD-3-Clause"}],
      "vulnerabilities": []
    }
  ]
}
```

---

## Step 5: DAST — Dynamic Application Security Testing

**OWASP ZAP (Zed Attack Proxy) modes:**

| Mode | Description | Use Case |
|------|-----------|---------|
| Baseline scan | Spider + passive scan only | CI/CD quick check |
| Full scan | Spider + active scan | Staging environment |
| API scan | OpenAPI/Swagger spec scan | REST APIs |
| Ajax Spider | SPA support | React/Angular apps |

**ZAP baseline CI example:**
```bash
docker run --rm owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.myapp.com \
  -r zap-report.html \
  -x zap-report.xml \
  --fail_action WARN \
  -l MEDIUM
```

**Key DAST findings:**
- SQL injection (CWE-89)
- XSS (CWE-79)
- CSRF (CWE-352)
- Insecure headers (X-Frame-Options, CSP, HSTS)
- Sensitive data in URLs (query parameters)

---

## Step 6: IaC Security Scanning with Checkov

**Infrastructure as Code scanning:**
```bash
# Install and run checkov
pip install checkov
checkov -d ./terraform --framework terraform

# Or for Kubernetes
checkov -d ./kubernetes --framework kubernetes
```

**Example findings:**
```
Check: CKV_AWS_2: "Ensure the S3 bucket has access control list (ACL) disabled"
FAILED for resource: aws_s3_bucket.data
File: main.tf:15-22

Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
FAILED for resource: aws_s3_bucket.data
```

**Terraform secure example:**
```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-secure-bucket"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

---

## Step 7: Security Gates

**Security gate policies:**

| Gate | Fail Condition | Action |
|------|--------------|--------|
| SAST | Any HIGH/CRITICAL finding | Block merge |
| Secret scan | Any secret detected | Block merge + alert |
| SCA | CRITICAL CVE in direct deps | Block merge |
| Container scan | CRITICAL CVE in base image | Block deploy |
| IaC scan | Any CRITICAL checkov finding | Block deploy |
| DAST | HIGH finding in staging | Block prod deploy |
| SBOM | Missing or unsigned | Block deploy |

**GitHub Actions pipeline:**
```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Secret scan
        run: gitleaks detect --source . --exit-code 1
      
      - name: SAST (Bandit)
        run: bandit -r . --severity-level high --exit-zero-on-error
      
      - name: SCA (Grype)
        run: |
          grype . --fail-on critical
      
      - name: IaC scan (Checkov)
        run: checkov -d . --framework terraform --hard-fail-on HIGH
      
      - name: Container scan
        run: trivy image myapp:${{ github.sha }} --exit-code 1 --severity CRITICAL
```

---

## Step 8: Capstone — DevSecOps Maturity Model

**Scenario:** Scale DevSecOps across 20 development teams

```
Maturity Level 1 - Foundation (0-3 months):
  - Git hooks: detect-secrets pre-commit
  - Basic SAST: Bandit/Semgrep in PR checks
  - Dependency check: Dependabot automated PRs
  - Security champion: 1 per team
  Target: 100% teams with secret scanning

Maturity Level 2 - Integrated (3-9 months):
  - Full SAST pipeline with break-build on HIGH
  - Container scanning in CI/CD
  - IaC scanning (Checkov) for all Terraform
  - SBOM generation for all releases
  - Developer security training (OWASP Top 10)
  Target: < 30 day avg time to fix HIGH vulns

Maturity Level 3 - Advanced (9-18 months):
  - DAST in staging for all web apps
  - Threat modelling for new features
  - Security gates: CVSS < 7 to deploy
  - Signed images (Sigstore/Cosign)
  - Dynamic secrets (Vault) in all apps
  Target: < 7 day avg time to fix CRITICAL vulns

Metrics dashboard:
  - Mean time to fix (MTTF) by severity
  - Vulnerability density (CVEs per 1000 lines of code)
  - % pipelines with security gates
  - Secret leak incidents per quarter
  - % dependencies up-to-date (< 6 months old)
```

---

## Summary

| Tool | Stage | Purpose |
|------|-------|---------|
| detect-secrets / gitleaks | Pre-commit | Secret detection |
| Bandit / Semgrep | SAST | Code security flaws |
| OWASP Dependency-Check | SCA | OSS CVEs |
| Syft + Grype | SBOM | Component inventory + CVEs |
| OWASP ZAP | DAST | Runtime vulnerability testing |
| Checkov / tfsec | IaC | Infrastructure misconfigurations |
| Trivy | Container | Image CVE scanning |
| Security gates | Pipeline | Break-build on policy violation |
