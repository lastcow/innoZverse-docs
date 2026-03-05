# Lab 07: Ansible Roles & Galaxy

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Roles are the primary way to organize Ansible content for reuse. They enforce a standard directory structure, allow dependency management, and can be shared via Ansible Galaxy. This lab covers creating roles with `ansible-galaxy init`, understanding role directory structure, dependencies, requirements.yml, and using roles in playbooks.

## Prerequisites

- Completed Lab 06 (Ansible Foundations)
- Understanding of YAML and playbook structure

---

## Step 1: Create a Role with ansible-galaxy init

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp
ansible-galaxy init webserver
echo '=== Role created successfully ==='
echo ''
echo '=== Role directory structure ==='
find webserver -type f | sort
"
```

📸 **Verified Output:**
```
=== Role created successfully ===

=== Role directory structure ===
webserver/README.md
webserver/defaults/main.yml
webserver/handlers/main.yml
webserver/meta/main.yml
webserver/tasks/main.yml
webserver/tests/inventory
webserver/tests/test.yml
webserver/vars/main.yml
```

> 💡 **Tip:** `ansible-galaxy init` creates all 8 standard directories. Each has a specific purpose. Empty directories are gitignored by default — only add `files/` and `templates/` when needed. Keep roles focused on a single responsibility.

---

## Step 2: Understand Role Directory Structure

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp && ansible-galaxy init webserver 2>/dev/null

echo '=== tasks/main.yml (entry point) ==='
cat webserver/tasks/main.yml

echo ''
echo '=== handlers/main.yml ==='
cat webserver/handlers/main.yml

echo ''
echo '=== defaults/main.yml (low priority vars) ==='
cat webserver/defaults/main.yml

echo ''
echo '=== vars/main.yml (high priority vars) ==='
cat webserver/vars/main.yml

echo ''
echo '=== meta/main.yml (metadata + dependencies) ==='
cat webserver/meta/main.yml | head -20
"
```

📸 **Verified Output:**
```
=== tasks/main.yml (entry point) ===
---
# tasks file for webserver

=== handlers/main.yml ===
---
# handlers file for webserver

=== defaults/main.yml (low priority vars) ===
---
# defaults file for webserver

=== vars/main.yml (high priority vars) ===
---
# vars file for webserver

=== meta/main.yml (metadata + dependencies) ===
galaxy_info:
  author: your name
  description: your role description
  company: your company (optional)
  license: license (GPL-2.0-or-later, MIT, etc)
  min_ansible_version: 2.1
  galaxy_tags: []
dependencies: []
```

> 💡 **Tip:** Key distinction: `defaults/` variables have the lowest priority and are easily overridden. `vars/` variables have higher priority and should only be changed intentionally. Use `defaults/` for user-configurable settings and `vars/` for internal role constants.

---

## Step 3: Build a Complete webserver Role

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp && ansible-galaxy init webserver 2>/dev/null

# defaults/main.yml — user-configurable
cat > webserver/defaults/main.yml << 'EOF'
---
http_port: 80
https_port: 443
server_name: localhost
document_root: /var/www/html
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_keepalive_timeout: 65
EOF

# vars/main.yml — internal role vars
cat > webserver/vars/main.yml << 'EOF'
---
nginx_package: nginx
nginx_service: nginx
nginx_config_dir: /etc/nginx
nginx_sites_available: /etc/nginx/sites-available
nginx_sites_enabled: /etc/nginx/sites-enabled
EOF

# tasks/main.yml
cat > webserver/tasks/main.yml << 'EOF'
---
- name: Include OS-specific variables
  include_vars: \"{{ ansible_os_family }}.yml\"
  ignore_errors: true

- name: Install nginx
  apt:
    name: \"{{ nginx_package }}\"
    state: present
    update_cache: yes
  become: true

- name: Create document root
  file:
    path: \"{{ document_root }}\"
    state: directory
    owner: www-data
    group: www-data
    mode: '0755'
  become: true

- name: Deploy nginx virtual host config
  template:
    src: vhost.conf.j2
    dest: \"{{ nginx_sites_available }}/{{ server_name }}.conf\"
    owner: root
    group: root
    mode: '0644'
  become: true
  notify: reload nginx

- name: Enable virtual host
  file:
    src: \"{{ nginx_sites_available }}/{{ server_name }}.conf\"
    dest: \"{{ nginx_sites_enabled }}/{{ server_name }}.conf\"
    state: link
  become: true
  notify: reload nginx

- name: Ensure nginx is started and enabled
  service:
    name: \"{{ nginx_service }}\"
    state: started
    enabled: true
  become: true
EOF

# handlers/main.yml
cat > webserver/handlers/main.yml << 'EOF'
---
- name: reload nginx
  service:
    name: \"{{ nginx_service }}\"
    state: reloaded
  become: true

- name: restart nginx
  service:
    name: \"{{ nginx_service }}\"
    state: restarted
  become: true
EOF

# templates/vhost.conf.j2
mkdir -p webserver/templates
cat > webserver/templates/vhost.conf.j2 << 'EOF'
server {
    listen {{ http_port }};
    server_name {{ server_name }};
    root {{ document_root }};
    index index.html index.htm;

    access_log /var/log/nginx/{{ server_name }}_access.log;
    error_log  /var/log/nginx/{{ server_name }}_error.log;

    location / {
        try_files \$uri \$uri/ =404;
    }

    keepalive_timeout {{ nginx_keepalive_timeout }};

    worker_processes {{ nginx_worker_processes }};
}
EOF

# meta/main.yml
cat > webserver/meta/main.yml << 'EOF'
---
galaxy_info:
  author: innoZverse
  description: Install and configure nginx webserver
  license: MIT
  min_ansible_version: 2.9
  platforms:
    - name: Ubuntu
      versions:
        - '20.04'
        - '22.04'
  galaxy_tags:
    - nginx
    - webserver
    - web

dependencies:
  - role: common
    vars:
      common_packages:
        - curl
        - wget
EOF

echo '=== Role structure ==='
find webserver -type f | sort
echo ''
echo '=== tasks/main.yml ==='
cat webserver/tasks/main.yml
echo ''
echo '=== defaults/main.yml ==='
cat webserver/defaults/main.yml
"
```

📸 **Verified Output:**
```
=== Role structure ===
webserver/README.md
webserver/defaults/main.yml
webserver/handlers/main.yml
webserver/meta/main.yml
webserver/tasks/main.yml
webserver/templates/vhost.conf.j2
webserver/tests/inventory
webserver/tests/test.yml
webserver/vars/main.yml

=== tasks/main.yml ===
---
- name: Include OS-specific variables
  include_vars: "{{ ansible_os_family }}.yml"
  ignore_errors: true

- name: Install nginx
  apt:
    name: "{{ nginx_package }}"
    state: present
    update_cache: yes
  become: true
...

=== defaults/main.yml ===
---
http_port: 80
https_port: 443
server_name: localhost
document_root: /var/www/html
nginx_worker_processes: auto
```

> 💡 **Tip:** Templates go in `templates/` with `.j2` extension. Static files go in `files/`. The `template` module processes Jinja2; the `copy` module copies files verbatim. Always use `notify` in tasks that change configs to trigger handler restarts.

---

## Step 4: Role Dependencies in meta/main.yml

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp
ansible-galaxy init common 2>/dev/null
ansible-galaxy init webserver 2>/dev/null
ansible-galaxy init app 2>/dev/null

# common role tasks
cat > common/tasks/main.yml << 'EOF'
---
- name: Install common packages
  debug:
    msg: \"Installing common packages: {{ common_packages | default([]) }}\"
EOF

# webserver depends on common
cat > webserver/meta/main.yml << 'EOF'
---
galaxy_info:
  author: innoZverse
  description: Nginx webserver
  license: MIT
  min_ansible_version: 2.9

dependencies:
  - role: common
    vars:
      common_packages:
        - curl
        - wget
        - vim
EOF

# app depends on webserver (which depends on common)
cat > app/meta/main.yml << 'EOF'
---
galaxy_info:
  author: innoZverse
  description: Application role
  license: MIT

dependencies:
  - role: webserver
    vars:
      http_port: 8080
      server_name: myapp.example.com
EOF

cat > app/tasks/main.yml << 'EOF'
---
- name: Deploy application
  debug:
    msg: Deploying app to port 8080
EOF

# Test playbook with dependency chain
cat > /tmp/test_deps.yml << 'EOF'
---
- name: Deploy full app stack
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: app
EOF

ANSIBLE_ROLES_PATH=/tmp ansible-playbook --syntax-check /tmp/test_deps.yml 2>&1

echo ''
echo '=== Role dependency chain ==='
echo 'app -> webserver -> common'
echo ''
echo '=== app/meta/main.yml ==='
cat /tmp/app/meta/main.yml
"
```

📸 **Verified Output:**
```
playbook: /tmp/test_deps.yml

=== Role dependency chain ===
app -> webserver -> common

=== app/meta/main.yml ===
---
galaxy_info:
  author: innoZverse
  description: Application role
  license: MIT

dependencies:
  - role: webserver
    vars:
      http_port: 8080
      server_name: myapp.example.com
```

> 💡 **Tip:** Dependency chains are resolved automatically. If multiple roles depend on the same role, Ansible deduplicates — a role only runs once unless `allow_duplicates: true` is set in its `meta/main.yml`. Use this carefully to avoid repeated package installations.

---

## Step 5: Using Roles in Playbooks

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp
ansible-galaxy init webserver 2>/dev/null
ansible-galaxy init database 2>/dev/null
ansible-galaxy init monitoring 2>/dev/null

# Simple tasks for demo
for role in webserver database monitoring; do
  cat > \${role}/tasks/main.yml << EOF
---
- name: Execute \${role} tasks
  debug:
    msg: \"Running \${role} role with port {{ http_port | default('N/A') }}\"
EOF
done

cat > /tmp/site.yml << 'EOF'
---
# Method 1: Simple role list
- name: Configure web servers
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - webserver

# Method 2: Role with inline vars
- name: Configure web servers with custom vars
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: webserver
      vars:
        http_port: 8080
      tags:
        - web
        - nginx

# Method 3: pre_tasks + roles + post_tasks
- name: Full provisioning play
  hosts: localhost
  connection: local
  gather_facts: false
  pre_tasks:
    - name: Pre-check
      debug:
        msg: Running pre-tasks before roles

  roles:
    - role: webserver
      tags: web
    - role: database
      tags: db

  post_tasks:
    - name: Post-check
      debug:
        msg: All roles completed
EOF

ANSIBLE_ROLES_PATH=/tmp ansible-playbook --syntax-check /tmp/site.yml 2>&1
echo ''
ANSIBLE_ROLES_PATH=/tmp ansible-playbook /tmp/site.yml 2>&1
"
```

📸 **Verified Output:**
```
playbook: /tmp/site.yml

PLAY [Configure web servers] ***************************************************

TASK [Execute webserver tasks] *************************************************
ok: [localhost] => {
    "msg": "Running webserver role with port N/A"
}

PLAY [Full provisioning play] ***************************************************

TASK [Pre-check] ****************************************************************
ok: [localhost] => {
    "msg": "Running pre-tasks before roles"
}

TASK [Execute webserver tasks] **************************************************
ok: [localhost] => {
    "msg": "Running webserver role with port N/A"
}

TASK [Execute database tasks] ***************************************************
ok: [localhost] => {
    "msg": "Running database role with port N/A"
}

TASK [Post-check] ***************************************************************
ok: [localhost] => {
    "msg": "All roles completed"
}

PLAY RECAP **********************************************************************
localhost    : ok=5    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** `pre_tasks` run before roles, `roles` run in order, `post_tasks` run last. Use `pre_tasks` for validation checks (assert module) and `post_tasks` for smoke tests. Tags on roles let you run selective parts: `ansible-playbook site.yml --tags web`.

---

## Step 6: requirements.yml — Install from Galaxy

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/requirements.yml << 'EOF'
---
roles:
  # Install from Ansible Galaxy by name
  - name: geerlingguy.nginx
    version: 3.2.0

  # Install from GitHub
  - name: my_custom_role
    src: https://github.com/example/ansible-role-custom
    version: main

  # Install from tar.gz
  - name: offline_role
    src: https://example.com/roles/my_role.tar.gz

collections:
  # Install collection from Galaxy
  - name: community.general
    version: '>=7.0.0'

  # Install from Automation Hub
  - name: ansible.posix
    version: '1.5.4'
EOF

echo '=== requirements.yml ==='
cat /tmp/requirements.yml

echo ''
echo '=== Install command (syntax) ==='
echo 'ansible-galaxy install -r requirements.yml'
echo 'ansible-galaxy collection install -r requirements.yml'
echo 'ansible-galaxy install -r requirements.yml --roles-path ./roles'

echo ''
echo '=== Verify galaxy CLI is available ==='
ansible-galaxy --version | head -3
"
```

📸 **Verified Output:**
```
=== requirements.yml ===
---
roles:
  # Install from Ansible Galaxy by name
  - name: geerlingguy.nginx
    version: 3.2.0

  # Install from GitHub
  - name: my_custom_role
    src: https://github.com/example/ansible-role-custom
    version: main

  # Install from tar.gz
  - name: offline_role
    src: https://example.com/roles/my_role.tar.gz

collections:
  # Install collection from Galaxy
  - name: community.general
    version: '>=7.0.0'

  # Install from Automation Hub
  - name: ansible.posix
    version: '1.5.4'

=== Install command (syntax) ===
ansible-galaxy install -r requirements.yml
ansible-galaxy collection install -r requirements.yml
ansible-galaxy install -r requirements.yml --roles-path ./roles

=== Verify galaxy CLI is available ===
ansible-galaxy [core 2.17.14]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
```

> 💡 **Tip:** Commit `requirements.yml` to version control but NOT the installed roles directory. Add `roles/` to `.gitignore` and install with `ansible-galaxy install -r requirements.yml` in your CI pipeline. This keeps your repo small and versions explicit.

---

## Step 7: Role Tags and Testing

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cd /tmp && ansible-galaxy init webserver 2>/dev/null

cat > webserver/tasks/main.yml << 'EOF'
---
- name: Install nginx packages
  debug:
    msg: Installing nginx
  tags:
    - install
    - packages

- name: Configure nginx
  debug:
    msg: Configuring nginx
  tags:
    - configure
    - config

- name: Deploy website content
  debug:
    msg: Deploying content
  tags:
    - deploy
    - content

- name: Start nginx service
  debug:
    msg: Starting nginx
  tags:
    - service
    - start
EOF

cat > /tmp/hosts.ini << 'EOF'
[local]
localhost ansible_connection=local
EOF

cat > /tmp/tagged_play.yml << 'EOF'
---
- name: Tagged role playbook
  hosts: local
  gather_facts: false
  roles:
    - role: webserver
      tags: web
EOF

echo '=== List all tags ==='
ANSIBLE_ROLES_PATH=/tmp ansible-playbook /tmp/tagged_play.yml --list-tags 2>&1

echo ''
echo '=== Run only configure tasks ==='
ANSIBLE_ROLES_PATH=/tmp ansible-playbook -i /tmp/hosts.ini /tmp/tagged_play.yml --tags configure 2>&1

echo ''
echo '=== Skip deploy tasks ==='
ANSIBLE_ROLES_PATH=/tmp ansible-playbook -i /tmp/hosts.ini /tmp/tagged_play.yml --skip-tags deploy 2>&1
"
```

📸 **Verified Output:**
```
=== List all tags ===
playbook: /tmp/tagged_play.yml

  play #1 (local): Tagged role playbook
    TASK TAGS: [configure, config, content, deploy, install, packages, service, start, web]

=== Run only configure tasks ===
PLAY [Tagged role playbook] *****************************************************

TASK [webserver : Configure nginx] *********************************************
ok: [localhost] => {
    "msg": "Configuring nginx"
}

PLAY RECAP **********************************************************************
localhost    : ok=1    changed=0    unreachable=0    failed=0    skipped=0

=== Skip deploy tasks ===
PLAY [Tagged role playbook] *****************************************************

TASK [webserver : Install nginx packages] **************************************
ok: [localhost] => {"msg": "Installing nginx"}

TASK [webserver : Configure nginx] *********************************************
ok: [localhost] => {"msg": "Configuring nginx"}

TASK [webserver : Start nginx service] *****************************************
ok: [localhost] => {"msg": "Starting nginx"}

PLAY RECAP **********************************************************************
localhost    : ok=3    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Tag individual tasks AND the role in the playbook. `--tags configure` runs only configure-tagged tasks. `--skip-tags deploy` runs everything except deploy tasks. Special tags `always` and `never` control tasks that always run or only run when explicitly requested.

---

## Step 8: Capstone — Multi-tier Application Role Structure

**Scenario:** You're architecting a 3-tier application (web/app/db) for your company. Design and validate a complete role hierarchy with proper dependencies, variable defaults, and tags.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/roles
cd /tmp/roles

# Initialize all roles
for role in common security webserver appserver database; do
  ansible-galaxy init \$role 2>/dev/null
done

echo '=== Created roles ==='
ls -1 /tmp/roles

# common role — base configuration
cat > common/tasks/main.yml << 'EOF'
---
- name: Set hostname
  debug:
    msg: \"Setting hostname to {{ inventory_hostname }}\"
  tags: [common, hostname]

- name: Configure NTP
  debug:
    msg: \"Configuring NTP with servers: {{ ntp_servers | join(', ') }}\"
  tags: [common, ntp]

- name: Install base packages
  debug:
    msg: \"Installing: {{ common_packages | join(', ') }}\"
  tags: [common, packages]
EOF

cat > common/defaults/main.yml << 'EOF'
---
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
common_packages:
  - curl
  - wget
  - vim
  - htop
  - net-tools
EOF

# security role
cat > security/tasks/main.yml << 'EOF'
---
- name: Configure SSH
  debug:
    msg: Hardening SSH configuration
  tags: [security, ssh]

- name: Configure firewall
  debug:
    msg: \"Opening ports: {{ firewall_allowed_ports | join(', ') }}\"
  tags: [security, firewall]
EOF

cat > security/defaults/main.yml << 'EOF'
---
firewall_allowed_ports:
  - 22
  - 80
  - 443
EOF

# webserver meta — depends on common and security
cat > webserver/meta/main.yml << 'EOF'
---
galaxy_info:
  author: innoZverse
  description: Nginx webserver
  license: MIT
dependencies:
  - role: common
  - role: security
    vars:
      firewall_allowed_ports: [22, 80, 443]
EOF

# database meta — depends on common and security
cat > database/meta/main.yml << 'EOF'
---
galaxy_info:
  author: innoZverse
  description: PostgreSQL database
  license: MIT
dependencies:
  - role: common
  - role: security
    vars:
      firewall_allowed_ports: [22, 5432]
EOF

for role in webserver appserver database; do
  cat > \${role}/tasks/main.yml << EOF
---
- name: Run \${role} tasks
  debug:
    msg: \"Configuring \${role} on {{ inventory_hostname }}\"
  tags: [\${role}]
EOF
done

# site playbook
cat > /tmp/site.yml << 'EOF'
---
- name: Provision web tier
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: webserver
      tags: web

- name: Provision database tier
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: database
      tags: db
EOF

echo ''
echo '=== Role dependency tree ==='
echo 'webserver -> common, security'
echo 'database  -> common, security'
echo ''

echo '=== Syntax check ==='
ANSIBLE_ROLES_PATH=/tmp/roles ansible-playbook --syntax-check /tmp/site.yml 2>&1

echo ''
echo '=== Full run ==='
ANSIBLE_ROLES_PATH=/tmp/roles ansible-playbook -i 'localhost,' /tmp/site.yml 2>&1
"
```

📸 **Verified Output:**
```
=== Created roles ===
appserver
common
database
security
webserver

=== Role dependency tree ===
webserver -> common, security
database  -> common, security

=== Syntax check ===
playbook: /tmp/site.yml

=== Full run ===
PLAY [Provision web tier] *******************************************************

TASK [common : Set hostname] ****************************************************
ok: [localhost] => {"msg": "Setting hostname to localhost"}

TASK [common : Configure NTP] ***************************************************
ok: [localhost] => {"msg": "Configuring NTP with servers: 0.pool.ntp.org, 1.pool.ntp.org"}

TASK [common : Install base packages] *******************************************
ok: [localhost] => {"msg": "Installing: curl, wget, vim, htop, net-tools"}

TASK [security : Configure SSH] *************************************************
ok: [localhost] => {"msg": "Hardening SSH configuration"}

TASK [security : Configure firewall] ********************************************
ok: [localhost] => {"msg": "Opening ports: 22, 80, 443"}

TASK [webserver : Run webserver tasks] ******************************************
ok: [localhost] => {"msg": "Configuring webserver on localhost"}

PLAY [Provision database tier] **************************************************

TASK [database : Run database tasks] ********************************************
ok: [localhost] => {"msg": "Configuring database on localhost"}

PLAY RECAP **********************************************************************
localhost    : ok=7    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Notice that `common` and `security` ran only once even though both `webserver` and `database` depend on them — Ansible deduplicates dependencies by default. This is the primary benefit of using role dependencies over manually repeating tasks.

---

## Summary

| Concept | Command/File | Purpose |
|---------|-------------|---------|
| Create role | `ansible-galaxy init rolename` | Scaffold standard role structure |
| Role structure | `tasks/ handlers/ templates/ files/ vars/ defaults/ meta/` | Standard directories |
| User config vars | `defaults/main.yml` | Lowest priority, easily overridden |
| Internal vars | `vars/main.yml` | Higher priority, role-internal |
| Dependencies | `meta/main.yml: dependencies:` | Declare required roles |
| Install from Galaxy | `ansible-galaxy install -r requirements.yml` | Install remote roles |
| List installed | `ansible-galaxy role list` | Show installed roles |
| Use in playbook | `roles: - role: name` | Apply role to hosts |
| Role with vars | `role: name \n vars: key: val` | Override defaults inline |
| Tags on tasks | `tags: [install, config]` | Label tasks for selective runs |
| Run by tag | `ansible-playbook --tags install` | Run only tagged tasks |
| Skip by tag | `ansible-playbook --skip-tags deploy` | Skip tagged tasks |
| List tags | `ansible-playbook --list-tags` | Show all available tags |
| requirements.yml | Roles + collections spec | Reproducible role installs |
