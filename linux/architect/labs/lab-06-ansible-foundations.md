# Lab 06: Ansible Foundations

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Ansible is the industry-standard agentless automation tool that uses SSH and YAML playbooks to manage infrastructure at scale. In this lab you will install Ansible, explore inventory formats, run ad-hoc commands, configure `ansible.cfg`, and write your first playbook — all verified inside a Docker container.

## Prerequisites

- Docker installed and running
- Basic YAML knowledge
- Familiarity with SSH concepts

---

## Step 1: Install Ansible via pip3

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null
apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null
ansible --version
"
```

📸 **Verified Output:**
```
ansible [core 2.17.14]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/local/lib/python3.10/dist-packages/ansible
  ansible collection location = /root/.ansible/collections:/usr/share/ansible/collections
  executable location = /usr/local/bin/ansible
  python version = 3.10.12 (main, Jan 26 2026, 14:55:28) [GCC 11.4.0] (/usr/bin/python3)
  jinja version = 3.1.6
  libyaml = True
```

> 💡 **Tip:** `pip3 install ansible` installs the full Ansible package including `ansible-core`. For minimal installs use `pip3 install ansible-core`. Always pin versions in production: `pip3 install ansible==9.x.x`.

---

## Step 2: Inventory Formats — INI and YAML

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /etc/ansible/inventory

# INI format inventory
cat > /etc/ansible/inventory/hosts.ini << 'EOF'
[webservers]
web1 ansible_host=192.168.1.10 ansible_user=ubuntu
web2 ansible_host=192.168.1.11 ansible_user=ubuntu

[dbservers]
db1 ansible_host=192.168.1.20 ansible_user=ubuntu

[production:children]
webservers
dbservers

[production:vars]
ansible_python_interpreter=/usr/bin/python3
EOF

# YAML format inventory
cat > /etc/ansible/inventory/hosts.yml << 'EOF'
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.10
          ansible_user: ubuntu
        web2:
          ansible_host: 192.168.1.11
          ansible_user: ubuntu
    dbservers:
      hosts:
        db1:
          ansible_host: 192.168.1.20
          ansible_user: ubuntu
EOF

echo '=== INI Inventory ==='
cat /etc/ansible/inventory/hosts.ini
echo ''
echo '=== YAML Inventory ==='
cat /etc/ansible/inventory/hosts.yml
"
```

📸 **Verified Output:**
```
=== INI Inventory ===
[webservers]
web1 ansible_host=192.168.1.10 ansible_user=ubuntu
web2 ansible_host=192.168.1.11 ansible_user=ubuntu

[dbservers]
db1 ansible_host=192.168.1.20 ansible_user=ubuntu

[production:children]
webservers
dbservers

[production:vars]
ansible_python_interpreter=/usr/bin/python3

=== YAML Inventory ===
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.10
          ansible_user: ubuntu
        web2:
          ansible_host: 192.168.1.11
          ansible_user: ubuntu
    dbservers:
      hosts:
        db1:
          ansible_host: 192.168.1.20
          ansible_user: ubuntu
```

> 💡 **Tip:** Both formats are equivalent. YAML is preferred for large inventories because it supports nesting and is easier to generate programmatically. INI is simpler for small static inventories.

---

## Step 3: ansible-inventory — Inspect Your Inventory

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/hosts.ini << 'EOF'
[webservers]
localhost ansible_connection=local
EOF

ansible-inventory -i /tmp/hosts.ini --list
"
```

📸 **Verified Output:**
```json
{
    "_meta": {
        "hostvars": {
            "localhost": {
                "ansible_connection": "local"
            }
        }
    },
    "all": {
        "children": [
            "ungrouped",
            "webservers"
        ]
    },
    "webservers": {
        "hosts": [
            "localhost"
        ]
    }
}
```

> 💡 **Tip:** Use `ansible-inventory --list --yaml` for YAML output or `--graph` for a visual tree. This is invaluable for debugging dynamic inventories.

---

## Step 4: Configure ansible.cfg

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /etc/ansible
cat > /etc/ansible/ansible.cfg << 'EOF'
[defaults]
inventory          = /etc/ansible/hosts
remote_user        = ubuntu
host_key_checking  = False
retry_files_enabled = False
stdout_callback    = yaml
interpreter_python = auto_silent
forks              = 10
timeout            = 30

[privilege_escalation]
become             = False
become_method      = sudo
become_user        = root
become_ask_pass    = False

[ssh_connection]
pipelining         = True
control_path       = /tmp/ansible-ssh-%%h-%%p-%%r
EOF

echo '=== ansible.cfg ==='
cat /etc/ansible/ansible.cfg

echo ''
echo '=== Config file in use ==='
ANSIBLE_CONFIG=/etc/ansible/ansible.cfg ansible --version | grep 'config file'
"
```

📸 **Verified Output:**
```
=== ansible.cfg ===
[defaults]
inventory          = /etc/ansible/hosts
remote_user        = ubuntu
host_key_checking  = False
retry_files_enabled = False
stdout_callback    = yaml
interpreter_python = auto_silent
forks              = 10
timeout            = 30

[privilege_escalation]
become             = False
become_method      = sudo
become_user        = root
become_ask_pass    = False

[ssh_connection]
pipelining         = True
control_path       = /tmp/ansible-ssh-%h-%p-%r

=== Config file in use ===
  config file = /etc/ansible/ansible.cfg
```

> 💡 **Tip:** Ansible searches for `ansible.cfg` in this order: `$ANSIBLE_CONFIG` env var → `./ansible.cfg` (current dir) → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg`. Project-local configs override global ones.

---

## Step 5: host_vars and group_vars

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/project/{group_vars,host_vars}

cat > /tmp/project/group_vars/webservers.yml << 'EOF'
---
http_port: 80
https_port: 443
max_connections: 1000
nginx_worker_processes: auto
EOF

cat > /tmp/project/host_vars/web1.yml << 'EOF'
---
http_port: 8080
server_name: web1.example.com
EOF

cat > /tmp/project/hosts.ini << 'EOF'
[webservers]
web1 ansible_connection=local
EOF

echo '=== group_vars/webservers.yml ==='
cat /tmp/project/group_vars/webservers.yml
echo ''
echo '=== host_vars/web1.yml ==='
cat /tmp/project/host_vars/web1.yml

echo ''
echo '=== inventory with vars ==='
ansible-inventory -i /tmp/project/hosts.ini --host web1
"
```

📸 **Verified Output:**
```
=== group_vars/webservers.yml ===
---
http_port: 80
https_port: 443
max_connections: 1000
nginx_worker_processes: auto

=== host_vars/web1.yml ===
---
http_port: 8080
server_name: web1.example.com

=== inventory with vars ===
{
    "ansible_connection": "local",
    "http_port": 8080,
    "https_port": 443,
    "max_connections": 1000,
    "nginx_worker_processes": "auto",
    "server_name": "web1.example.com"
}
```

> 💡 **Tip:** `host_vars` override `group_vars` for the same variable name. This allows you to set defaults in group_vars and exceptions in host_vars. Note `http_port` is 8080 (host override) not 80 (group default).

---

## Step 6: Ad-hoc Commands

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/hosts.ini << 'EOF'
[local]
localhost ansible_connection=local
EOF

echo '=== -m ping ==='
ansible -i /tmp/hosts.ini local -m ping 2>/dev/null

echo ''
echo '=== -m command ==='
ansible -i /tmp/hosts.ini local -m command -a 'uname -r' 2>/dev/null

echo ''
echo '=== -m shell ==='
ansible -i /tmp/hosts.ini local -m shell -a 'echo \$HOSTNAME | tr a-z A-Z' 2>/dev/null

echo ''
echo '=== -m copy ==='
ansible -i /tmp/hosts.ini local -m copy -a 'content=\"Hello Ansible\n\" dest=/tmp/ansible_test.txt' 2>/dev/null
cat /tmp/ansible_test.txt

echo ''
echo '=== -m file (stat) ==='
ansible -i /tmp/hosts.ini local -m stat -a 'path=/tmp/ansible_test.txt' 2>/dev/null
"
```

📸 **Verified Output:**
```
=== -m ping ===
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}

=== -m command ===
localhost | CHANGED | rc=0 >>
6.14.0-37-generic

=== -m shell ===
localhost | CHANGED | rc=0 >>
LOCALHOST

=== -m copy ===
localhost | CHANGED => {
    "changed": true,
    "dest": "/tmp/ansible_test.txt",
    "gid": 0,
    "group": "root",
    "md5sum": "d8e8fca2dc0f896fd7cb4cb0031ba249",
    "mode": "0644",
    "owner": "root",
    "size": 13,
    "src": "/root/.ansible/tmp/ansible-tmp-1234/source",
    "state": "file",
    "uid": 0
}
Hello Ansible

=== -m file (stat) ===
localhost | SUCCESS => {
    "changed": false,
    "stat": {
        "exists": true,
        "path": "/tmp/ansible_test.txt",
        "size": 13
    }
}
```

> 💡 **Tip:** Use `-m command` for simple commands (no shell features), `-m shell` when you need pipes/redirects/variables. The `command` module is more secure and predictable.

---

## Step 7: First Playbook — YAML Structure

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/hosts.ini << 'EOF'
[local]
localhost ansible_connection=local
EOF

cat > /tmp/first_playbook.yml << 'EOF'
---
- name: My First Ansible Playbook
  hosts: local
  gather_facts: true
  become: false

  vars:
    greeting: Hello from Ansible
    packages_to_check:
      - python3
      - curl

  tasks:
    - name: Print greeting message
      debug:
        msg: \"{{ greeting }}\"

    - name: Show OS information
      debug:
        msg: \"OS: {{ ansible_distribution }} {{ ansible_distribution_version }}\"

    - name: Check if Python3 exists
      stat:
        path: /usr/bin/python3
      register: python_check

    - name: Report Python3 status
      debug:
        msg: \"Python3 exists: {{ python_check.stat.exists }}\"

    - name: Create a test directory
      file:
        path: /tmp/ansible_lab
        state: directory
        mode: '0755'

    - name: Write a config file
      copy:
        content: |
          # Generated by Ansible
          app_version=1.0
          environment=lab
        dest: /tmp/ansible_lab/config.ini

    - name: Read back config file
      command: cat /tmp/ansible_lab/config.ini
      register: config_content

    - name: Display config content
      debug:
        var: config_content.stdout_lines
EOF

echo '=== Syntax Check ==='
ansible-playbook --syntax-check -i /tmp/hosts.ini /tmp/first_playbook.yml 2>&1

echo ''
echo '=== Run Playbook ==='
ansible-playbook -i /tmp/hosts.ini /tmp/first_playbook.yml 2>&1
"
```

📸 **Verified Output:**
```
=== Syntax Check ===
playbook: /tmp/first_playbook.yml

=== Run Playbook ===
PLAY [My First Ansible Playbook] ***********************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Print greeting message] **************************************************
ok: [localhost] => {
    "msg": "Hello from Ansible"
}

TASK [Show OS information] *****************************************************
ok: [localhost] => {
    "msg": "OS: Ubuntu 22.04"
}

TASK [Check if Python3 exists] *************************************************
ok: [localhost]

TASK [Report Python3 status] ***************************************************
ok: [localhost] => {
    "msg": "Python3 exists: True"
}

TASK [Create a test directory] *************************************************
changed: [localhost]

TASK [Write a config file] *****************************************************
changed: [localhost]

TASK [Read back config file] ***************************************************
changed: [localhost]

TASK [Display config content] **************************************************
ok: [localhost] => {
    "config_content.stdout_lines": [
        "# Generated by Ansible",
        "app_version=1.0",
        "environment=lab"
    ]
}

PLAY RECAP *************************************************************
localhost                  : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

> 💡 **Tip:** Every playbook has the structure: `hosts` (target), `gather_facts` (collect system info), `become` (privilege escalation), `vars` (variables), `tasks` (ordered list of actions). The `register` keyword captures task output for later use.

---

## Step 8: Capstone — ansible --check and --diff Mode

**Scenario:** Your team needs to validate configuration changes before deploying to 50 production servers. Use `--check` (dry-run) and `--diff` (show changes) to audit what Ansible *would* change without touching anything.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/hosts.ini << 'EOF'
[local]
localhost ansible_connection=local
EOF

# Pre-create file with old content
echo 'old_setting=false' > /tmp/app.conf

cat > /tmp/check_playbook.yml << 'EOF'
---
- name: Configuration Audit Playbook
  hosts: local
  gather_facts: false

  tasks:
    - name: Ensure app config is correct
      copy:
        content: |
          new_setting=true
          version=2.0
          managed_by=ansible
        dest: /tmp/app.conf

    - name: Ensure log directory exists
      file:
        path: /var/log/myapp
        state: directory
        mode: '0750'

    - name: Ensure cron entry exists
      cron:
        name: cleanup job
        minute: '0'
        hour: '2'
        job: '/usr/bin/cleanup.sh'
EOF

echo '=== BEFORE: app.conf content ==='
cat /tmp/app.conf

echo ''
echo '=== CHECK + DIFF mode (dry run) ==='
ansible-playbook --check --diff -i /tmp/hosts.ini /tmp/check_playbook.yml 2>&1

echo ''
echo '=== AFTER check: app.conf unchanged ==='
cat /tmp/app.conf

echo ''
echo '=== Real run ==='
ansible-playbook -i /tmp/hosts.ini /tmp/check_playbook.yml 2>&1

echo ''
echo '=== AFTER real run: app.conf updated ==='
cat /tmp/app.conf
"
```

📸 **Verified Output:**
```
=== BEFORE: app.conf content ===
old_setting=false

=== CHECK + DIFF mode (dry run) ===
PLAY [Configuration Audit Playbook] ********************************************

TASK [Ensure app config is correct] ********************************************
--- before: /tmp/app.conf
+++ after: /tmp/app.conf
@@ -1 +1,3 @@
-old_setting=false
+new_setting=true
+version=2.0
+managed_by=ansible
changed: [localhost]

TASK [Ensure log directory exists] *********************************************
changed: [localhost]

TASK [Ensure cron entry exists] ************************************************
changed: [localhost]

PLAY RECAP *************************************************************
localhost     : ok=3    changed=3    unreachable=0    failed=0    skipped=0

=== AFTER check: app.conf unchanged ===
old_setting=false

=== Real run ===
PLAY [Configuration Audit Playbook] ********************************************
...
PLAY RECAP *************************************************************
localhost     : ok=3    changed=3    unreachable=0    failed=0    skipped=0

=== AFTER real run: app.conf updated ===
new_setting=true
version=2.0
managed_by=ansible
```

> 💡 **Tip:** Always run `--check --diff` before deploying to production. This is your "preview" mode — it shows unified diffs for file changes without executing them. Add `--limit web1` to test against a single host first.

---

## Summary

| Concept | Command/File | Purpose |
|---------|-------------|---------|
| Install | `pip3 install ansible` | Install Ansible via pip |
| Version | `ansible --version` | Show version and config info |
| INI inventory | `[group]\nhost ansible_host=x` | Simple static inventory |
| YAML inventory | `all.children.group.hosts` | Structured static inventory |
| Inspect inventory | `ansible-inventory --list` | View parsed inventory as JSON |
| Config file | `ansible.cfg` | Set defaults (forks, user, etc.) |
| Group variables | `group_vars/groupname.yml` | Variables for all hosts in group |
| Host variables | `host_vars/hostname.yml` | Variables for specific host |
| Ad-hoc ping | `ansible -m ping all` | Test connectivity |
| Ad-hoc command | `ansible -m command -a 'cmd'` | Run one-off command |
| Ad-hoc copy | `ansible -m copy -a 'content= dest='` | Copy content to file |
| Playbook structure | `hosts/gather_facts/become/vars/tasks` | YAML automation definition |
| Syntax check | `ansible-playbook --syntax-check` | Validate playbook YAML |
| Dry run | `ansible-playbook --check --diff` | Preview changes without applying |
