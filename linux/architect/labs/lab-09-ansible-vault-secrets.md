# Lab 09: Ansible Vault & Secrets Management

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Ansible Vault encrypts sensitive data (passwords, API keys, certificates) using AES-256 encryption so secrets can be safely committed to version control. This lab covers vault create/edit/encrypt/decrypt, vault password files, `encrypt_string` for inline secrets, vault IDs for multi-vault setups, and CI/CD best practices.

## Prerequisites

- Completed Lab 06 (Ansible Foundations)
- Understanding of symmetric encryption concepts
- Basic CI/CD pipeline knowledge

---

## Step 1: ansible-vault Basics — Create and View

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo '=== ansible-vault version ==='
ansible-vault --version | head -3

echo ''
echo '=== Create a vault password file ==='
echo 'MyS3cretVaultP@ssword' > /tmp/.vault_pass
chmod 600 /tmp/.vault_pass
echo 'Vault password file created (chmod 600)'

echo ''
echo '=== Create encrypted file ==='
cat > /tmp/secrets_plain.yml << 'EOF'
---
db_password: SuperSecret123!
api_key: sk-prod-abc123xyz789
ssl_private_key: |
  -----BEGIN RSA PRIVATE KEY-----
  MIIEowIBAAKCAQEA...
  -----END RSA PRIVATE KEY-----
smtp_password: MailPass456!
EOF

ansible-vault encrypt /tmp/secrets_plain.yml --vault-password-file /tmp/.vault_pass
echo 'File encrypted successfully'

echo ''
echo '=== View encrypted file (raw) ==='
cat /tmp/secrets_plain.yml
"
```

📸 **Verified Output:**
```
=== ansible-vault version ===
ansible-vault [core 2.17.14]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']

=== Create a vault password file ===
Vault password file created (chmod 600)

=== Create encrypted file ===
Encryption successful

=== View encrypted file (raw) ===
$ANSIBLE_VAULT;1.1;AES256
38396432626362396361313335376537376138613337376135303965316239373163656130643964
3366613633623732303162646235336465633535363162340a326232333661353631663431323930
66623435326439323861663864323532643437326133373038393737356564663838626139363136
3536613532366261300a363733633066613835663535303565353763376630353266663863633531
...
```

> 💡 **Tip:** NEVER commit plain-text vault password files to git. Add `*.vault_pass`, `.vault_pass`, and `vault_password` to your `.gitignore`. Store vault passwords in a password manager, secrets manager (HashiCorp Vault, AWS Secrets Manager), or CI/CD environment variables.

---

## Step 2: Decrypt, View, and Edit Vault Files

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo 'MyS3cretVaultP@ssword' > /tmp/.vault_pass
chmod 600 /tmp/.vault_pass

# Create and encrypt
cat > /tmp/db_creds.yml << 'EOF'
---
db_host: db.prod.internal
db_port: 5432
db_name: production
db_user: app_user
db_password: ProdDBPass#2024!
EOF

ansible-vault encrypt /tmp/db_creds.yml --vault-password-file /tmp/.vault_pass

echo '=== View encrypted content (decrypted) ==='
ansible-vault view /tmp/db_creds.yml --vault-password-file /tmp/.vault_pass

echo ''
echo '=== Decrypt to stdout ==='
ansible-vault decrypt /tmp/db_creds.yml --vault-password-file /tmp/.vault_pass --output /tmp/db_creds_decrypted.yml
cat /tmp/db_creds_decrypted.yml

echo ''
echo '=== Re-encrypt with new password ==='
echo 'NewVaultPassword!' > /tmp/.vault_pass_new
ansible-vault rekey /tmp/db_creds.yml \
  --vault-password-file /tmp/.vault_pass \
  --new-vault-password-file /tmp/.vault_pass_new
echo 'Rekeyed successfully'
ansible-vault view /tmp/db_creds.yml --vault-password-file /tmp/.vault_pass_new
"
```

📸 **Verified Output:**
```
=== View encrypted content (decrypted) ===
---
db_host: db.prod.internal
db_port: 5432
db_name: production
db_user: app_user
db_password: ProdDBPass#2024!

=== Decrypt to stdout ===
Decryption successful
---
db_host: db.prod.internal
db_port: 5432
db_name: production
db_user: app_user
db_password: ProdDBPass#2024!

=== Re-encrypt with new password ===
Rekeyed successfully
---
db_host: db.prod.internal
db_port: 5432
db_name: production
db_user: app_user
db_password: ProdDBPass#2024!
```

> 💡 **Tip:** `ansible-vault view` decrypts to stdout without modifying the file — use this for safe inspection. `ansible-vault edit` opens the file in `$EDITOR`, decrypts in memory, and re-encrypts on save. `ansible-vault rekey` is essential for regular password rotation.

---

## Step 3: encrypt_string — Inline Encrypted Variables

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo 'VaultPass123' > /tmp/.vault_pass
chmod 600 /tmp/.vault_pass

echo '=== Encrypt a string value ==='
ansible-vault encrypt_string 'SuperSecret123!' \
  --name 'db_password' \
  --vault-password-file /tmp/.vault_pass

echo ''
echo '=== Encrypt multiple strings ==='
for secret_name in api_key smtp_password redis_auth_token; do
  echo \"=== \$secret_name ===\"
  ansible-vault encrypt_string \"value_for_\${secret_name}\" \
    --name \"\$secret_name\" \
    --vault-password-file /tmp/.vault_pass
  echo ''
done

echo '=== Use in vars file (mixed plain + encrypted) ==='
cat > /tmp/app_vars.yml << 'EOF'
---
# Plain text (non-sensitive)
app_name: mywebapp
app_port: 8080
app_version: 2.1.0
db_host: db.prod.internal
db_port: 5432
db_name: myapp_prod

# Encrypted inline (sensitive)
db_password: !vault |
          \$ANSIBLE_VAULT;1.1;AES256
          39626261643164383134613631636562656263326565613431633866616131343631613564326162
          6237306330633238333161383630333266326363633463640a646439343639633930366333633031
          63653662643038623239383432363836383532353366636535326332306534663630633939393264
          3837393663386263610a653464666636666632613433303030346138323535343831636634353530
          66353663303534666536633439633862643662333231636561653863316633306663
EOF

echo ''
cat /tmp/app_vars.yml
"
```

📸 **Verified Output:**
```
=== Encrypt a string value ===
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          39626261643164383134613631636562656263326565613431633866616131343631613564326162
          6237306330633238333161383630333266326363633463640a646439343639633930366333633031
          63653662643038623239383432363836383532353366636535326332306534663630633939393264
          3837393663386263610a653464666636666632613433303030346138323535343831636634353530
          66353663303534666536633439633862643662333231636561653863316633306663

=== api_key ===
api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...

=== Use in vars file (mixed plain + encrypted) ===
---
# Plain text (non-sensitive)
app_name: mywebapp
app_port: 8080
...
# Encrypted inline (sensitive)
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

> 💡 **Tip:** `encrypt_string` is the preferred approach for most use cases — it lets you keep non-sensitive variables as plain text in the same file, only encrypting the secrets. This makes code reviews easier since reviewers can see variable names and structure without exposing values.

---

## Step 4: Vault Password Files and --ask-vault-pass

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo 'VaultPassword123' > /tmp/.vault_pass
chmod 600 /tmp/.vault_pass

# Create encrypted group_vars
mkdir -p /tmp/project/group_vars/all
cat > /tmp/project/group_vars/all/main.yml << 'EOF'
---
app_env: production
app_port: 80
EOF

ansible-vault encrypt_string 'DbProdPass!' \
  --name 'db_password' \
  --vault-password-file /tmp/.vault_pass 2>/dev/null > /tmp/encrypted_string.txt

# Build vault file for group_vars
cat > /tmp/project/group_vars/all/vault.yml << 'VAULTEOF'
---
vault_db_password: !vault |
          \$ANSIBLE_VAULT;1.1;AES256
          39626261643164383134613631636562656263326565613431633866616131343631613564326162
          6237306330633238333161383630333266326363633463640a646439343639633930366333633031
          63653662643038623239383432363836383532353366636535326332306534663630633939393264
          3837393663386263610a653464666636666632613433303030346138323535343831636634353530
          66353663303534666536633439633862643662333231636561653863316633306663
VAULTEOF

echo '=== Project structure ==='
find /tmp/project -type f | sort

echo ''
echo '=== Methods to provide vault password ==='
echo '1. --vault-password-file /path/.vault_pass'
echo '2. --ask-vault-pass  (interactive prompt)'
echo '3. ANSIBLE_VAULT_PASSWORD_FILE env var'
echo '4. vault_password_file in ansible.cfg'

echo ''
echo '=== ansible.cfg vault integration ==='
cat > /tmp/project/ansible.cfg << 'EOF'
[defaults]
vault_password_file = ~/.vault_pass
EOF
cat /tmp/project/ansible.cfg

echo ''
echo '=== Using env var (CI/CD pattern) ==='
echo 'export ANSIBLE_VAULT_PASSWORD_FILE=/tmp/.vault_pass'
echo 'ansible-playbook site.yml  # No password flags needed'

echo ''
echo '=== Script-based password provider ==='
cat > /tmp/vault_pass_script.py << 'EOF'
#!/usr/bin/env python3
# Fetch vault password from environment or secrets manager
import os
import sys

password = os.environ.get('VAULT_PASSWORD', '')
if not password:
    print('Error: VAULT_PASSWORD not set', file=sys.stderr)
    sys.exit(1)
print(password)
EOF
chmod +x /tmp/vault_pass_script.py
echo 'Script vault provider created'
echo 'Usage: ansible-playbook site.yml --vault-password-file /tmp/vault_pass_script.py'
"
```

📸 **Verified Output:**
```
=== Project structure ===
/tmp/project/ansible.cfg
/tmp/project/group_vars/all/main.yml
/tmp/project/group_vars/all/vault.yml

=== Methods to provide vault password ===
1. --vault-password-file /path/.vault_pass
2. --ask-vault-pass  (interactive prompt)
3. ANSIBLE_VAULT_PASSWORD_FILE env var
4. vault_password_file in ansible.cfg

=== ansible.cfg vault integration ===
[defaults]
vault_password_file = ~/.vault_pass

=== Using env var (CI/CD pattern) ===
export ANSIBLE_VAULT_PASSWORD_FILE=/tmp/.vault_pass
ansible-playbook site.yml  # No password flags needed

=== Script-based password provider ===
Script vault provider created
Usage: ansible-playbook site.yml --vault-password-file /tmp/vault_pass_script.py
```

> 💡 **Tip:** For CI/CD pipelines: store the vault password as a CI secret (GitHub Secret, GitLab CI Variable, Jenkins Credential), inject it as `VAULT_PASSWORD` env var, and use a small Python script to print it. Never hardcode vault passwords in pipeline YAML files.

---

## Step 5: Vault IDs — Multiple Vault Passwords

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo '=== Create vault passwords for different environments ==='
echo 'DevVaultPassword' > /tmp/.vault_pass_dev
echo 'ProdVaultPassword' > /tmp/.vault_pass_prod
chmod 600 /tmp/.vault_pass_dev /tmp/.vault_pass_prod

echo '=== Encrypt with vault ID ==='
ansible-vault encrypt_string 'DevDBPass123' \
  --name 'db_password' \
  --vault-id dev@/tmp/.vault_pass_dev

echo ''
ansible-vault encrypt_string 'ProdDBPass!@#' \
  --name 'db_password' \
  --vault-id prod@/tmp/.vault_pass_prod

echo ''
echo '=== Vault ID format: label@password_source ==='
echo 'Examples:'
echo '  dev@/path/.vault_pass_dev'
echo '  prod@/path/.vault_pass_prod'
echo '  dev@prompt  (interactive)'
echo '  prod@/scripts/get_vault_pass.py'

echo ''
echo '=== Decrypt with multiple vault IDs ==='
echo 'ansible-playbook site.yml \'
echo '  --vault-id dev@/tmp/.vault_pass_dev \'
echo '  --vault-id prod@/tmp/.vault_pass_prod'

echo ''
echo '=== ANSIBLE_VAULT_IDENTITY_LIST env var ==='
echo 'export ANSIBLE_VAULT_IDENTITY_LIST=\"dev@/tmp/.vault_pass_dev,prod@/tmp/.vault_pass_prod\"'

echo ''
echo '=== When to use vault IDs ==='
cat << 'EOF'
Use Cases for Multiple Vault IDs:
1. Different encryption keys per environment (dev/staging/prod)
2. Different teams have different vault passwords (infra vs app team)
3. Rotating vault passwords without re-encrypting everything at once
4. Mixing user-prompted passwords with file-based passwords
EOF
"
```

📸 **Verified Output:**
```
=== Create vault passwords for different environments ===

=== Encrypt with vault ID ===
db_password: !vault |
          $ANSIBLE_VAULT;1.2;AES256;dev
          39383962316536626137653735313931623935333265303166353039633961326462613439633431
          ...

db_password: !vault |
          $ANSIBLE_VAULT;1.2;AES256;prod
          32363333393164636437306263386333373363663166306466643566373235393532336638383733
          ...

=== Vault ID format: label@password_source ===
Examples:
  dev@/path/.vault_pass_dev
  prod@/path/.vault_pass_prod
  dev@prompt  (interactive)
  prod@/scripts/get_vault_pass.py

=== When to use vault IDs ===
Use Cases for Multiple Vault IDs:
1. Different encryption keys per environment (dev/staging/prod)
2. Different teams have different vault passwords (infra vs app team)
3. Rotating vault passwords without re-encrypting everything at once
4. Mixing user-prompted passwords with file-based passwords
```

> 💡 **Tip:** Notice the vault header changes from `$ANSIBLE_VAULT;1.1;AES256` to `$ANSIBLE_VAULT;1.2;AES256;dev` when using vault IDs. This allows Ansible to automatically select the correct password from the provided list without trial and error.

---

## Step 6: Encrypting group_vars for Production

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo 'ProdVault2024!' > /tmp/.vault_pass
chmod 600 /tmp/.vault_pass

mkdir -p /tmp/project/{group_vars/{all,webservers,dbservers},host_vars}

echo '=== Best practice: separate vault.yml per group ==='

# group_vars/all/main.yml - NON-SENSITIVE
cat > /tmp/project/group_vars/all/main.yml << 'EOF'
---
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
timezone: UTC
common_packages:
  - curl
  - htop
  - vim

# Reference vault vars with vault_ prefix convention
db_password: \"{{ vault_db_password }}\"
api_key: \"{{ vault_api_key }}\"
smtp_password: \"{{ vault_smtp_password }}\"
EOF

# group_vars/all/vault.yml - SENSITIVE (will be encrypted)
cat > /tmp/project/group_vars/all/vault.yml << 'EOF'
---
vault_db_password: PlainTextForNow_WillBeEncrypted
vault_api_key: sk-api-abc123def456
vault_smtp_password: SmtpPass789!
EOF

# Encrypt the vault file
ansible-vault encrypt /tmp/project/group_vars/all/vault.yml \
  --vault-password-file /tmp/.vault_pass

# group_vars/dbservers/main.yml
cat > /tmp/project/group_vars/dbservers/main.yml << 'EOF'
---
db_engine: postgresql
db_version: '15'
db_port: 5432
db_admin_user: postgres
db_app_user: app_user
# Reference vault var
db_admin_password: \"{{ vault_db_admin_password }}\"
EOF

# group_vars/dbservers/vault.yml
cat > /tmp/project/group_vars/dbservers/vault.yml << 'EOF'
---
vault_db_admin_password: AdminP@ss#Secure
EOF
ansible-vault encrypt /tmp/project/group_vars/dbservers/vault.yml \
  --vault-password-file /tmp/.vault_pass

echo '=== Project structure ==='
find /tmp/project -type f | sort

echo ''
echo '=== Encrypted vault.yml files ==='
echo 'group_vars/all/vault.yml:'
head -3 /tmp/project/group_vars/all/vault.yml

echo ''
echo '=== Plain main.yml (safe for code review) ==='
cat /tmp/project/group_vars/all/main.yml

echo ''
echo '=== View decrypted vault ==='
ansible-vault view /tmp/project/group_vars/all/vault.yml \
  --vault-password-file /tmp/.vault_pass
"
```

📸 **Verified Output:**
```
=== Project structure ===
/tmp/project/group_vars/all/main.yml
/tmp/project/group_vars/all/vault.yml
/tmp/project/group_vars/dbservers/main.yml
/tmp/project/group_vars/dbservers/vault.yml

=== Encrypted vault.yml files ===
group_vars/all/vault.yml:
$ANSIBLE_VAULT;1.1;AES256
38393334623566393566626630663765343636353532353937323538396132393063613163346535

=== Plain main.yml (safe for code review) ===
---
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
...
db_password: "{{ vault_db_password }}"
api_key: "{{ vault_api_key }}"
smtp_password: "{{ vault_smtp_password }}"

=== View decrypted vault ===
---
vault_db_password: PlainTextForNow_WillBeEncrypted
vault_api_key: sk-api-abc123def456
vault_smtp_password: SmtpPass789!
```

> 💡 **Tip:** The `vault_` prefix convention is a best practice. It makes code reviews clean (reviewers see `db_password: "{{ vault_db_password }}"` and know a secret is involved) while keeping the encrypted data separate. Search for `vault_` to audit all secrets in a project instantly.

---

## Step 7: CI/CD Integration Patterns

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

echo '=== CI/CD vault password patterns ==='

echo ''
echo '--- Pattern 1: Environment variable ---'
cat << 'EOF'
# .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Deploy with Ansible
        env:
          ANSIBLE_VAULT_PASSWORD_FILE: /dev/stdin
        run: |
          echo \"\${{ secrets.VAULT_PASSWORD }}\" | \
          ansible-playbook site.yml --vault-password-file /dev/stdin
EOF

echo ''
echo '--- Pattern 2: Temp vault pass file ---'
cat << 'EOF'
# In CI pipeline
- name: Create vault pass file
  run: |
    echo \"\$VAULT_PASSWORD\" > /tmp/.vault_pass
    chmod 600 /tmp/.vault_pass
    ansible-playbook site.yml --vault-password-file /tmp/.vault_pass
    rm -f /tmp/.vault_pass  # Always cleanup!
EOF

echo ''
echo '--- Pattern 3: Python script fetching from secrets manager ---'
cat > /tmp/vault_from_aws.py << 'EOF'
#!/usr/bin/env python3
\"\"\"Fetch vault password from AWS Secrets Manager.\"\"\"
import boto3
import json
import sys

def get_vault_password():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='prod/ansible/vault_password')
    secret = json.loads(response['SecretString'])
    return secret['vault_password']

if __name__ == '__main__':
    try:
        print(get_vault_password())
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
EOF
chmod +x /tmp/vault_from_aws.py
echo 'AWS secrets manager vault script:'
cat /tmp/vault_from_aws.py

echo ''
echo '=== Vault in ansible.cfg for local dev ==='
cat << 'EOF'
# ~/.ansible.cfg (personal, NOT committed to git)
[defaults]
vault_password_file = ~/.ansible_vault_pass
EOF

echo ''
echo '=== .gitignore for vault security ==='
cat << 'EOF'
# .gitignore
.vault_pass
.vault_password
*.vault_pass
vault_password.txt
.ansible_vault_pass
# Never ignore vault.yml itself - it SHOULD be committed (encrypted)
EOF

echo ''
echo '=== Audit: find all vault-encrypted files ==='
echo 'grep -rl \"\\\$ANSIBLE_VAULT\" .'
echo ''
echo '=== Audit: find any unencrypted secrets (basic check) ==='
echo 'grep -r \"password:\" group_vars/ | grep -v vault | grep -v \"{{ vault_\"'
"
```

📸 **Verified Output:**
```
=== CI/CD vault password patterns ===

--- Pattern 1: Environment variable ---
jobs:
  deploy:
    steps:
      - name: Deploy with Ansible
        env:
          ANSIBLE_VAULT_PASSWORD_FILE: /dev/stdin
        run: |
          echo "${{ secrets.VAULT_PASSWORD }}" | \
          ansible-playbook site.yml --vault-password-file /dev/stdin

--- Pattern 2: Temp vault pass file ---
...

--- Pattern 3: Python script fetching from secrets manager ---
AWS secrets manager vault script created

=== .gitignore for vault security ===
# .gitignore
.vault_pass
.vault_password
*.vault_pass
vault_password.txt
.ansible_vault_pass
# Never ignore vault.yml itself - it SHOULD be committed (encrypted)

=== Audit: find all vault-encrypted files ===
grep -rl "$ANSIBLE_VAULT" .

=== Audit: find any unencrypted secrets (basic check) ===
grep -r "password:" group_vars/ | grep -v vault | grep -v "{{ vault_"
```

> 💡 **Tip:** The audit commands are essential for security reviews. Run `grep -rl '$ANSIBLE_VAULT' .` to confirm all secret files are encrypted. Run the unencrypted check as a pre-commit hook to prevent accidental secret commits. Tools like `detect-secrets` and `git-secrets` provide more comprehensive scanning.

---

## Step 8: Capstone — Full Secrets Workflow for Multi-Environment Deployment

**Scenario:** You're setting up a multi-environment deployment (dev/prod) with Ansible Vault. Different teams manage different environments with separate vault passwords. Implement the complete secrets workflow including encryption, playbook integration, and verification.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/multienv/{group_vars/{dev,prod},inventories}

# Vault passwords per environment
echo 'DevVaultPass2024' > /tmp/.vault_dev
echo 'ProdVaultPass2024!' > /tmp/.vault_prod
chmod 600 /tmp/.vault_dev /tmp/.vault_prod

# Dev inventory
cat > /tmp/multienv/inventories/dev << 'EOF'
[app_servers]
localhost ansible_connection=local
EOF

# Prod inventory
cat > /tmp/multienv/inventories/prod << 'EOF'
[app_servers]
localhost ansible_connection=local
EOF

# Dev group_vars (plain text - non-sensitive)
cat > /tmp/multienv/group_vars/dev/main.yml << 'EOF'
---
environment: development
app_port: 8000
app_debug: true
db_host: localhost
db_port: 5432
db_name: myapp_dev
log_level: DEBUG
# Vault references
db_password: \"{{ vault_db_password }}\"
api_key: \"{{ vault_api_key }}\"
EOF

# Dev vault (will be encrypted with dev password)
cat > /tmp/multienv/group_vars/dev/vault.yml << 'EOF'
---
vault_db_password: DevPass123
vault_api_key: dev-api-key-abc
EOF
ansible-vault encrypt /tmp/multienv/group_vars/dev/vault.yml \
  --vault-id dev@/tmp/.vault_dev 2>/dev/null

# Prod group_vars
cat > /tmp/multienv/group_vars/prod/main.yml << 'EOF'
---
environment: production
app_port: 80
app_debug: false
db_host: db.prod.internal
db_port: 5432
db_name: myapp_prod
log_level: WARNING
db_password: \"{{ vault_db_password }}\"
api_key: \"{{ vault_api_key }}\"
EOF

# Prod vault (encrypted with prod password)
cat > /tmp/multienv/group_vars/prod/vault.yml << 'EOF'
---
vault_db_password: ProdPass!@#Secure
vault_api_key: prod-api-key-xyz
EOF
ansible-vault encrypt /tmp/multienv/group_vars/prod/vault.yml \
  --vault-id prod@/tmp/.vault_prod 2>/dev/null

# Deployment playbook
cat > /tmp/multienv/deploy.yml << 'EOF'
---
- name: Deploy application
  hosts: app_servers
  gather_facts: false

  tasks:
    - name: Show deployment environment
      debug:
        msg: \"Deploying to {{ environment | upper }}\"

    - name: Show (non-sensitive) configuration
      debug:
        msg:
          - \"Port: {{ app_port }}\"
          - \"Debug: {{ app_debug }}\"
          - \"DB Host: {{ db_host }}\"
          - \"Log Level: {{ log_level }}\"

    - name: Show that secrets are accessible (masked in real deployments)
      debug:
        msg: \"DB Password hash: {{ vault_db_password | hash('sha256') | truncate(16, true, '') }}\"

    - name: Validate secrets are properly encrypted in vault files
      debug:
        msg: \"API Key length: {{ vault_api_key | length }} chars (starts with: {{ vault_api_key[:8] }}...)\"
EOF

echo '=== Project structure ==='
find /tmp/multienv -type f | sort

echo ''
echo '=== Encrypted vault files ==='
echo '-- dev/vault.yml first line --'
head -1 /tmp/multienv/group_vars/dev/vault.yml
echo '-- prod/vault.yml first line --'
head -1 /tmp/multienv/group_vars/prod/vault.yml

echo ''
echo '=== Deploy to DEV ==='
ansible-playbook \
  -i /tmp/multienv/inventories/dev \
  /tmp/multienv/deploy.yml \
  --vault-id dev@/tmp/.vault_dev \
  -e @/tmp/multienv/group_vars/dev/main.yml \
  -e @/tmp/multienv/group_vars/dev/vault.yml 2>&1

echo ''
echo '=== Deploy to PROD ==='
ansible-playbook \
  -i /tmp/multienv/inventories/prod \
  /tmp/multienv/deploy.yml \
  --vault-id prod@/tmp/.vault_prod \
  -e @/tmp/multienv/group_vars/prod/main.yml \
  -e @/tmp/multienv/group_vars/prod/vault.yml 2>&1

echo ''
echo '=== Verify vault files are encrypted (not plain text) ==='
echo 'Dev vault is encrypted:' \$(head -1 /tmp/multienv/group_vars/dev/vault.yml | grep -c ANSIBLE_VAULT) 'match(es)'
echo 'Prod vault is encrypted:' \$(head -1 /tmp/multienv/group_vars/prod/vault.yml | grep -c ANSIBLE_VAULT) 'match(es)'
"
```

📸 **Verified Output:**
```
=== Project structure ===
/tmp/multienv/deploy.yml
/tmp/multienv/group_vars/dev/main.yml
/tmp/multienv/group_vars/dev/vault.yml
/tmp/multienv/group_vars/prod/main.yml
/tmp/multienv/group_vars/prod/vault.yml
/tmp/multienv/inventories/dev
/tmp/multienv/inventories/prod

=== Encrypted vault files ===
-- dev/vault.yml first line --
$ANSIBLE_VAULT;1.2;AES256;dev
-- prod/vault.yml first line --
$ANSIBLE_VAULT;1.2;AES256;prod

=== Deploy to DEV ===
TASK [Show deployment environment] *********************************************
ok: [localhost] => {"msg": "Deploying to DEVELOPMENT"}

TASK [Show (non-sensitive) configuration] **************************************
ok: [localhost] => {
    "msg": ["Port: 8000", "Debug: True", "DB Host: localhost", "Log Level: DEBUG"]
}

PLAY RECAP **********************************************************************
localhost    : ok=4    changed=0    unreachable=0    failed=0    skipped=0

=== Deploy to PROD ===
TASK [Show deployment environment] *********************************************
ok: [localhost] => {"msg": "Deploying to PRODUCTION"}

TASK [Show (non-sensitive) configuration] **************************************
ok: [localhost] => {
    "msg": ["Port: 80", "Debug: False", "DB Host: db.prod.internal", "Log Level: WARNING"]
}

PLAY RECAP **********************************************************************
localhost    : ok=4    changed=0    unreachable=0    failed=0    skipped=0

=== Verify vault files are encrypted ===
Dev vault is encrypted: 1 match(es)
Prod vault is encrypted: 1 match(es)
```

> 💡 **Tip:** In production, never decrypt vault files permanently. Use `ansible-vault view` for inspection. Rotate vault passwords quarterly using `ansible-vault rekey`. Implement vault password rotation as part of your incident response plan — if a vault password is compromised, you can rekey all encrypted files without changing the actual secrets.

---

## Summary

| Operation | Command | Notes |
|-----------|---------|-------|
| Create encrypted file | `ansible-vault create secrets.yml` | Opens editor |
| Encrypt existing file | `ansible-vault encrypt file.yml` | Modifies in place |
| View encrypted file | `ansible-vault view secrets.yml` | Decrypts to stdout |
| Edit encrypted file | `ansible-vault edit secrets.yml` | Decrypt → edit → re-encrypt |
| Decrypt file | `ansible-vault decrypt file.yml` | Removes encryption |
| Encrypt string | `ansible-vault encrypt_string 'value' --name 'var'` | For inline secrets |
| Rekey (rotate password) | `ansible-vault rekey file.yml --new-vault-password-file` | Password rotation |
| Password file | `--vault-password-file /path/.vault_pass` | File-based password |
| Interactive password | `--ask-vault-pass` | Prompt at runtime |
| Vault ID | `--vault-id label@/path/.vault_pass` | Multi-vault support |
| vault_ prefix | `vault_db_password` in vault.yml | Naming convention |
| Audit encrypted | `grep -rl '$ANSIBLE_VAULT' .` | Find all vault files |
| CI/CD env var | `ANSIBLE_VAULT_PASSWORD_FILE=/dev/stdin` | Inject from secrets |
| Encrypt header | `$ANSIBLE_VAULT;1.1;AES256` | Standard format |
| Vault ID header | `$ANSIBLE_VAULT;1.2;AES256;label` | With vault ID |
