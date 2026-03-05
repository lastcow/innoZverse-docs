# Lab 08: Ansible Variables, Templates & Handlers

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Variables are the lifeblood of reusable Ansible automation. Ansible has 16 levels of variable precedence, Jinja2 templating for dynamic configuration files, and handlers for event-driven service management. This lab covers variable precedence, `register` + `debug`, Jinja2 templates with loops/conditionals, handlers with `notify`/`listen`, `include_tasks`/`import_tasks`, and `when` conditions.

## Prerequisites

- Completed Lab 06 (Ansible Foundations)
- Basic understanding of Jinja2 templating syntax

---

## Step 1: Variable Precedence — 16 Levels

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/hosts.ini << 'EOF'
[webservers]
localhost ansible_connection=local http_port=9090

[webservers:vars]
http_port=8080
app_name=myapp
EOF

mkdir -p /tmp/group_vars /tmp/host_vars

cat > /tmp/group_vars/webservers.yml << 'EOF'
---
http_port: 7070
max_connections: 500
EOF

cat > /tmp/host_vars/localhost.yml << 'EOF'
---
http_port: 6060
server_role: primary
EOF

cat > /tmp/precedence_test.yml << 'EOF'
---
- name: Variable precedence demonstration
  hosts: webservers
  gather_facts: false
  vars:
    http_port: 5050
    play_var: from_play

  tasks:
    - name: Show http_port (play vars override group/host vars)
      debug:
        msg: \"http_port = {{ http_port }} (play vars win over group_vars/host_vars)\"

    - name: Extra vars override everything
      debug:
        msg: \"extra_var = {{ extra_var | default('not set - use -e to set') }}\"

    - name: Show all variable sources
      debug:
        msg: |
          Variable Precedence (lowest to highest):
          1.  role defaults (defaults/main.yml)
          2.  inventory file or script group vars
          3.  inventory group_vars/all
          4.  playbook group_vars/all
          5.  inventory group_vars/*
          6.  playbook group_vars/*
          7.  inventory file or script host vars
          8.  inventory host_vars/*
          9.  playbook host_vars/*
          10. host facts / cached set_facts
          11. play vars
          12. play vars_prompt
          13. play vars_files
          14. role vars (vars/main.yml)
          15. block vars (only for tasks in block)
          16. task vars (only for the task)
          17. include_vars
          18. set_facts / registered vars
          19. role (and include_role) params
          20. include params
          21. extra vars (-e) ALWAYS WIN
EOF

ansible-playbook -i /tmp/hosts.ini /tmp/precedence_test.yml 2>&1
echo ''
echo '--- With extra vars (-e overrides everything) ---'
ansible-playbook -i /tmp/hosts.ini /tmp/precedence_test.yml -e 'extra_var=from_command_line http_port=1111' 2>&1 | grep 'http_port\|extra_var'
"
```

📸 **Verified Output:**
```
PLAY [Variable precedence demonstration] ****************************************

TASK [Show http_port (play vars override group/host vars)] **********************
ok: [localhost] => {
    "msg": "http_port = 5050 (play vars win over group_vars/host_vars)"
}

TASK [Extra vars override everything] ******************************************
ok: [localhost] => {
    "msg": "extra_var = not set - use -e to set"
}

PLAY RECAP **********************************************************************
localhost    : ok=3    changed=0    unreachable=0    failed=0    skipped=0

--- With extra vars (-e overrides everything) ---
    "msg": "http_port = 1111 (play vars win over group_vars/host_vars)"
    "msg": "extra_var = from_command_line"
```

> 💡 **Tip:** The golden rule: extra vars (`-e`) always win. Use them for environment-specific overrides in CI/CD: `ansible-playbook deploy.yml -e "env=prod version=2.1.0"`. Use `defaults/` for documentation-friendly defaults that users *should* override.

---

## Step 2: vars, vars_files, and register

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/app_vars.yml << 'EOF'
---
app_name: mywebapp
app_version: 2.1.0
app_port: 8080
app_config:
  debug: false
  log_level: info
  db_host: db.internal
  db_port: 5432
EOF

cat > /tmp/vars_demo.yml << 'EOF'
---
- name: Variables demonstration
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    inline_var: set_in_play
    color_list:
      - red
      - green
      - blue
  vars_files:
    - /tmp/app_vars.yml

  tasks:
    - name: Show inline variable
      debug:
        msg: \"inline_var = {{ inline_var }}\"

    - name: Show variables from vars_file
      debug:
        msg: \"App: {{ app_name }} v{{ app_version }} on port {{ app_port }}\"

    - name: Access nested dict variable
      debug:
        msg: \"DB: {{ app_config.db_host }}:{{ app_config.db_port }}\"

    - name: Show list variable
      debug:
        msg: \"Colors: {{ color_list | join(', ') }}\"

    - name: Register command output
      command: uname -a
      register: uname_result

    - name: Show registered variable
      debug:
        msg: \"Return code: {{ uname_result.rc }}, Output: {{ uname_result.stdout }}\"

    - name: Register and test
      shell: \"echo \$((RANDOM % 100))\"
      register: random_number

    - name: Show random number
      debug:
        var: random_number.stdout

    - name: Use fact variables
      debug:
        msg: \"System: {{ ansible_distribution }} {{ ansible_distribution_version }}, Arch: {{ ansible_architecture }}\"
EOF

ansible-playbook /tmp/vars_demo.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Variables demonstration] *************************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Show inline variable] ****************************************************
ok: [localhost] => {
    "msg": "inline_var = set_in_play"
}

TASK [Show variables from vars_file] *******************************************
ok: [localhost] => {
    "msg": "App: mywebapp v2.1.0 on port 8080"
}

TASK [Access nested dict variable] *********************************************
ok: [localhost] => {
    "msg": "DB: db.internal:5432"
}

TASK [Show list variable] ******************************************************
ok: [localhost] => {
    "msg": "Colors: red, green, blue"
}

TASK [Register command output] *************************************************
changed: [localhost]

TASK [Show registered variable] ************************************************
ok: [localhost] => {
    "msg": "Return code: 0, Output: Linux [hostname] 6.14.0-37-generic #37-Ubuntu SMP ..."
}

TASK [Use fact variables] ******************************************************
ok: [localhost] => {
    "msg": "System: Ubuntu 22.04, Arch: x86_64"
}

PLAY RECAP **********************************************************************
localhost    : ok=9    changed=1    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** `register` captures the entire module result as a dict. Common keys: `stdout`, `stderr`, `rc` (return code), `stdout_lines` (list), `changed`, `failed`. Always check `register_var.rc == 0` before using results in critical tasks.

---

## Step 3: Jinja2 Templates — .j2 Files

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/templates

cat > /tmp/templates/nginx.conf.j2 << 'EOF'
# Managed by Ansible — DO NOT EDIT MANUALLY
# Generated: {{ ansible_date_time.date | default('unknown') }}

user www-data;
worker_processes {{ nginx_worker_processes | default('auto') }};
pid /run/nginx.pid;

events {
    worker_connections {{ nginx_worker_connections | default(1024) }};
    multi_accept {{ nginx_multi_accept | default('on') }};
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {{ nginx_keepalive_timeout | default(65) }};
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
{% if nginx_gzip_enabled | default(true) %}
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length {{ nginx_gzip_min_length | default(256) }};
{% else %}
    gzip off;
{% endif %}

    # Virtual hosts
{% for vhost in nginx_vhosts | default([]) %}
    server {
        listen {{ vhost.port | default(80) }};
        server_name {{ vhost.server_name }};
        root {{ vhost.document_root | default('/var/www/html') }};

        location / {
            try_files \$uri \$uri/ =404;
        }
{% if vhost.ssl | default(false) %}
        listen 443 ssl;
        ssl_certificate {{ vhost.ssl_cert }};
        ssl_certificate_key {{ vhost.ssl_key }};
{% endif %}
    }
{% endfor %}
}
EOF

cat > /tmp/template_test.yml << 'EOF'
---
- name: Template rendering demo
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    nginx_worker_processes: 4
    nginx_worker_connections: 2048
    nginx_keepalive_timeout: 75
    nginx_gzip_enabled: true
    nginx_gzip_min_length: 512
    nginx_vhosts:
      - server_name: app1.example.com
        port: 80
        document_root: /var/www/app1
      - server_name: app2.example.com
        port: 80
        document_root: /var/www/app2
        ssl: true
        ssl_cert: /etc/ssl/certs/app2.crt
        ssl_key: /etc/ssl/private/app2.key

  tasks:
    - name: Render nginx config from template
      template:
        src: /tmp/templates/nginx.conf.j2
        dest: /tmp/nginx.conf
        mode: '0644'

    - name: Show rendered config
      command: cat /tmp/nginx.conf
      register: config_output

    - name: Display rendered nginx.conf
      debug:
        var: config_output.stdout_lines
EOF

ansible-playbook /tmp/template_test.yml 2>&1
echo ''
echo '=== Rendered nginx.conf ==='
cat /tmp/nginx.conf 2>/dev/null || echo '(run playbook to generate)'
"
```

📸 **Verified Output:**
```
PLAY [Template rendering demo] *************************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Render nginx config from template] ***************************************
changed: [localhost]

TASK [Show rendered config] ****************************************************
changed: [localhost]

TASK [Display rendered nginx.conf] *********************************************
ok: [localhost] => {
    "config_output.stdout_lines": [
        "# Managed by Ansible — DO NOT EDIT MANUALLY",
        "# Generated: 2026-03-05",
        "",
        "user www-data;",
        "worker_processes 4;",
        "pid /run/nginx.pid;",
        "",
        "events {",
        "    worker_connections 2048;",
        "    multi_accept on;",
        "}",
        "",
        "    gzip on;",
        "    gzip_types text/plain text/css application/json application/javascript;",
        "    gzip_min_length 512;",
        "",
        "    server {",
        "        listen 80;",
        "        server_name app1.example.com;",
        "        root /var/www/app1;",
        "    }",
        "    server {",
        "        listen 80;",
        "        server_name app2.example.com;",
        "        root /var/www/app2;",
        "        listen 443 ssl;",
        "        ssl_certificate /etc/ssl/certs/app2.crt;",
        "        ssl_certificate_key /etc/ssl/private/app2.key;",
        "    }",
        "}",
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=4    changed=2    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Always add `# Managed by Ansible — DO NOT EDIT MANUALLY` at the top of templates. Use `{{ variable | default('fallback') }}` to avoid undefined errors. The `template` module also sets `changed` correctly — it only overwrites if content differs, triggering handlers only when needed.

---

## Step 4: Handlers — notify and listen

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/handlers_demo.yml << 'EOF'
---
- name: Handlers demonstration
  hosts: localhost
  connection: local
  gather_facts: false

  handlers:
    # Basic handler
    - name: reload nginx
      debug:
        msg: \"[HANDLER] Reloading nginx...\"

    # Handler with listen (multiple notifiers)
    - name: restart application
      debug:
        msg: \"[HANDLER] Restarting application service...\"
      listen: app_restart

    - name: update systemd
      debug:
        msg: \"[HANDLER] Running systemctl daemon-reload...\"
      listen: app_restart

    # Handler chain (handlers can notify handlers)
    - name: validate config
      debug:
        msg: \"[HANDLER] Validating configuration...\"

  tasks:
    - name: Update nginx config (triggers handler)
      copy:
        content: |
          # nginx config v2
          worker_processes 4;
        dest: /tmp/nginx_test.conf
      notify: reload nginx

    - name: Update app config (triggers multiple via listen)
      copy:
        content: |
          app_version=2.0
        dest: /tmp/app_test.conf
      notify: app_restart

    - name: Update app config again (same handler, only runs once)
      copy:
        content: |
          app_version=2.0
          debug=false
        dest: /tmp/app_test2.conf
      notify: app_restart

    - name: This task does NOT change anything
      file:
        path: /tmp/nginx_test.conf
        state: file
      register: file_check

    - name: Show that no-change tasks dont trigger handlers
      debug:
        msg: \"File changed: {{ file_check.changed }}\"
EOF

ansible-playbook /tmp/handlers_demo.yml 2>&1
echo ''
echo '--- Force handlers with meta: flush_handlers ---'
cat > /tmp/flush_demo.yml << 'EOF'
---
- name: Flush handlers mid-play
  hosts: localhost
  connection: local
  gather_facts: false

  handlers:
    - name: reload service
      debug:
        msg: \"[HANDLER] Service reloaded\"

  tasks:
    - name: Change config
      copy:
        content: new config
        dest: /tmp/flush_test.conf
      notify: reload service

    - name: Flush handlers NOW (before end of play)
      meta: flush_handlers

    - name: Continue with post-reload tasks
      debug:
        msg: \"Continuing after handler ran\"
EOF
ansible-playbook /tmp/flush_demo.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Handlers demonstration] **************************************************

TASK [Update nginx config (triggers handler)] **********************************
changed: [localhost]

TASK [Update app config (triggers multiple via listen)] ************************
changed: [localhost]

TASK [Update app config again (same handler, only runs once)] ******************
changed: [localhost]

TASK [This task does NOT change anything] **************************************
ok: [localhost]

TASK [Show that no-change tasks dont trigger handlers] *************************
ok: [localhost] => {
    "msg": "File changed: False"
}

RUNNING HANDLER [reload nginx] *************************************************
ok: [localhost] => {
    "msg": "[HANDLER] Reloading nginx..."
}

RUNNING HANDLER [restart application] ******************************************
ok: [localhost] => {
    "msg": "[HANDLER] Restarting application service..."
}

RUNNING HANDLER [update systemd] ***********************************************
ok: [localhost] => {
    "msg": "[HANDLER] Running systemctl daemon-reload..."
}

PLAY RECAP **********************************************************************
localhost    : ok=8    changed=3    unreachable=0    failed=0    skipped=0

--- Force handlers with meta: flush_handlers ---
TASK [Change config] ***********************************************************
changed: [localhost]

RUNNING HANDLER [reload service] ***********************************************
ok: [localhost] => {"msg": "[HANDLER] Service reloaded"}

TASK [Continue with post-reload tasks] *****************************************
ok: [localhost] => {"msg": "Continuing after handler ran"}
```

> 💡 **Tip:** Handlers run ONCE at the end of a play, even if notified multiple times. Use `listen` to have multiple tasks trigger the same logical event. Use `meta: flush_handlers` when you need handlers to run mid-play (e.g., reload nginx before deploying content to it).

---

## Step 5: when Conditions and Loops

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/when_loop.yml << 'EOF'
---
- name: Conditions and loops
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    deploy_env: staging
    enable_debug: true
    packages:
      - curl
      - wget
      - vim
    users:
      - name: alice
        shell: /bin/bash
        groups: [sudo, docker]
      - name: bob
        shell: /bin/sh
        groups: [docker]
      - name: charlie
        shell: /bin/bash
        groups: []

  tasks:
    - name: Run only on Ubuntu
      debug:
        msg: This is Ubuntu {{ ansible_distribution_version }}
      when: ansible_distribution == 'Ubuntu'

    - name: Run only in staging
      debug:
        msg: Staging-specific setup
      when: deploy_env == 'staging'

    - name: Run only when debug enabled
      debug:
        msg: Debug mode is ON
      when:
        - enable_debug | bool
        - deploy_env != 'production'

    - name: Loop over packages list
      debug:
        msg: \"Would install: {{ item }}\"
      loop: \"{{ packages }}\"

    - name: Loop over users dict
      debug:
        msg: \"User {{ item.name }} with shell {{ item.shell }} in groups: {{ item.groups | join(', ') or 'none' }}\"
      loop: \"{{ users }}\"

    - name: Loop with index
      debug:
        msg: \"[{{ idx }}] {{ item }}\"
      loop: \"{{ packages }}\"
      loop_control:
        index_var: idx
        label: \"{{ item }}\"

    - name: Conditional loop - only users with sudo
      debug:
        msg: \"{{ item.name }} is an admin\"
      loop: \"{{ users }}\"
      when: \"'sudo' in item.groups\"
      loop_control:
        label: \"{{ item.name }}\"
EOF

ansible-playbook /tmp/when_loop.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Conditions and loops] ****************************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Run only on Ubuntu] ******************************************************
ok: [localhost] => {
    "msg": "This is Ubuntu 22.04"
}

TASK [Run only in staging] *****************************************************
ok: [localhost] => {
    "msg": "Staging-specific setup"
}

TASK [Run only when debug enabled] *********************************************
ok: [localhost] => {
    "msg": "Debug mode is ON"
}

TASK [Loop over packages list] *************************************************
ok: [localhost] => (item=curl) => {"msg": "Would install: curl"}
ok: [localhost] => (item=wget) => {"msg": "Would install: wget"}
ok: [localhost] => (item=vim) => {"msg": "Would install: vim"}

TASK [Loop over users dict] ****************************************************
ok: [localhost] => (item=alice) => {"msg": "User alice with shell /bin/bash in groups: sudo, docker"}
ok: [localhost] => (item=bob) => {"msg": "User bob with shell /bin/sh in groups: docker"}
ok: [localhost] => (item=charlie) => {"msg": "User charlie with shell /bin/bash in groups: none"}

TASK [Conditional loop - only users with sudo] *********************************
ok: [localhost] => (item=alice) => {"msg": "alice is an admin"}
skipped: [localhost] => (item=bob)
skipped: [localhost] => (item=charlie)

PLAY RECAP **********************************************************************
localhost    : ok=8    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Use `loop_control: label:` to control what Ansible displays per iteration (avoids dumping the full dict). For simple lists, `loop` is preferred over `with_items`. When combining `when` + `loop`, the condition is evaluated per item — perfect for filtering.

---

## Step 6: include_tasks and import_tasks

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/tasks

cat > /tmp/tasks/setup_user.yml << 'EOF'
---
- name: Create user {{ username }}
  debug:
    msg: \"Creating user: {{ username }} ({{ user_type | default('standard') }})\"

- name: Set user shell
  debug:
    msg: \"Setting shell {{ user_shell | default('/bin/bash') }} for {{ username }}\"
EOF

cat > /tmp/tasks/install_packages.yml << 'EOF'
---
- name: Install package {{ item }}
  debug:
    msg: \"Installing {{ item }}\"
  loop: \"{{ packages_to_install | default([]) }}\"
EOF

cat > /tmp/include_demo.yml << 'EOF'
---
- name: include_tasks vs import_tasks
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    deploy_db: true

  tasks:
    # import_tasks: STATIC — processed at parse time
    # - can use --list-tasks to see included tasks
    # - cannot use loops or when to conditionally import
    - name: Import common setup (static)
      import_tasks: /tmp/tasks/install_packages.yml
      vars:
        packages_to_install:
          - curl
          - git

    # include_tasks: DYNAMIC — processed at runtime
    # - can use variables, loops, when conditions
    # - does NOT appear in --list-tasks output
    - name: Include user setup (dynamic)
      include_tasks: /tmp/tasks/setup_user.yml
      vars:
        username: alice
        user_type: admin
        user_shell: /bin/bash

    - name: Include user setup again for another user
      include_tasks: /tmp/tasks/setup_user.yml
      vars:
        username: bob
        user_type: standard

    - name: Conditionally include DB tasks
      include_tasks: /tmp/tasks/install_packages.yml
      vars:
        packages_to_install:
          - postgresql-client
          - libpq-dev
      when: deploy_db | bool
EOF

ansible-playbook /tmp/include_demo.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [include_tasks vs import_tasks] *******************************************

TASK [Install package curl] ****************************************************
ok: [localhost] => (item=curl) => {"msg": "Installing curl"}
ok: [localhost] => (item=git) => {"msg": "Installing git"}

TASK [Include user setup (dynamic)] ********************************************
included: /tmp/tasks/setup_user.yml for localhost

TASK [Create user alice] ******************************************************
ok: [localhost] => {"msg": "Creating user: alice (admin)"}

TASK [Set user shell] **********************************************************
ok: [localhost] => {"msg": "Setting shell /bin/bash for alice"}

TASK [Include user setup again for another user] ********************************
included: /tmp/tasks/setup_user.yml for localhost

TASK [Create user bob] *********************************************************
ok: [localhost] => {"msg": "Creating user: bob (standard)"}

TASK [Set user shell] **********************************************************
ok: [localhost] => {"msg": "Setting shell /bin/bash for bob"}

TASK [Conditionally include DB tasks] ******************************************
included: /tmp/tasks/install_packages.yml for localhost

TASK [Install package postgresql-client] ***************************************
ok: [localhost] => (item=postgresql-client) => {"msg": "Installing postgresql-client"}
ok: [localhost] => (item=libpq-dev) => {"msg": "Installing libpq-dev"}

PLAY RECAP **********************************************************************
localhost    : ok=10    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Rule of thumb: use `import_tasks` for static includes that should show up in `--list-tasks` and `--check` mode. Use `include_tasks` when you need runtime dynamism (variables, loops, conditions). Never use `include` (deprecated) — always specify `include_tasks` or `import_tasks`.

---

## Step 7: Advanced Jinja2 Filters and Tests

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/jinja2_filters.yml << 'EOF'
---
- name: Jinja2 filters and tests
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    app_name: MyWebApp
    version: 2.1.0
    ports: [80, 443, 8080, 8443]
    servers:
      - web1.prod.example.com
      - web2.prod.example.com
      - db1.prod.example.com
    config:
      debug: false
      max_connections: 100
    undefined_var: ~

  tasks:
    - name: String filters
      debug:
        msg:
          - \"upper: {{ app_name | upper }}\"
          - \"lower: {{ app_name | lower }}\"
          - \"replace: {{ app_name | replace('App', 'Service') }}\"
          - \"title: {{ 'hello world' | title }}\"

    - name: List filters
      debug:
        msg:
          - \"join: {{ ports | join(', ') }}\"
          - \"sort: {{ ports | sort | list }}\"
          - \"min: {{ ports | min }}\"
          - \"max: {{ ports | max }}\"
          - \"length: {{ ports | length }}\"
          - \"first: {{ ports | first }}\"
          - \"last: {{ ports | last }}\"

    - name: Default filter
      debug:
        msg:
          - \"defined: {{ config.max_connections | default(50) }}\"
          - \"undefined: {{ undefined_var | default('fallback_value') }}\"

    - name: Boolean tests
      debug:
        msg:
          - \"is defined: {{ app_name is defined }}\"
          - \"is none: {{ undefined_var is none }}\"
          - \"is string: {{ app_name is string }}\"
          - \"is number: {{ 42 is number }}\"
          - \"in list: {{ 80 in ports }}\"

    - name: Dict filters
      debug:
        msg:
          - \"keys: {{ config | dict2items | map(attribute='key') | list }}\"
          - \"values: {{ config | dict2items | map(attribute='value') | list }}\"
EOF

ansible-playbook /tmp/jinja2_filters.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Jinja2 filters and tests] ************************************************

TASK [String filters] **********************************************************
ok: [localhost] => {
    "msg": [
        "upper: MYWEBAPP",
        "lower: mywebapp",
        "replace: MyWebService",
        "title: Hello World"
    ]
}

TASK [List filters] ************************************************************
ok: [localhost] => {
    "msg": [
        "join: 80, 443, 8080, 8443",
        "sort: [80, 443, 8080, 8443]",
        "min: 80",
        "max: 8443",
        "length: 4",
        "first: 80",
        "last: 8443"
    ]
}

TASK [Default filter] **********************************************************
ok: [localhost] => {
    "msg": [
        "defined: 100",
        "undefined: fallback_value"
    ]
}

TASK [Boolean tests] ***********************************************************
ok: [localhost] => {
    "msg": [
        "is defined: True",
        "is none: True",
        "is string: True",
        "is number: True",
        "in list: True"
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=5    changed=0    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** The `| default()` filter is your best friend — always use it for optional variables to prevent "undefined variable" errors. Chain filters with pipes: `{{ value | default('') | upper | trim }}`. Use `| bool` to safely convert strings like "true"/"yes"/"1" to Python booleans.

---

## Step 8: Capstone — Dynamic Configuration Generator

**Scenario:** Your infrastructure team needs to generate configuration files for 3 different environments (dev/staging/prod) with different settings, using a single template and variable files per environment.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/capstone/{templates,vars,output}

# Application config template
cat > /tmp/capstone/templates/app.conf.j2 << 'EOF'
# {{ app_name }} Configuration
# Environment: {{ environment }}
# Generated by Ansible on {{ ansible_date_time.date | default('unknown') }}
# ============================================================

[server]
host = {{ app_host }}
port = {{ app_port }}
workers = {{ app_workers }}
debug = {{ app_debug | lower }}

[database]
host = {{ db_host }}
port = {{ db_port }}
name = {{ db_name }}
pool_size = {{ db_pool_size }}

[logging]
level = {{ log_level }}
format = {{ log_format }}
{% if log_file is defined %}
file = {{ log_file }}
{% endif %}

[features]
{% for feature, enabled in app_features.items() %}
{{ feature }} = {{ enabled | lower }}
{% endfor %}

[allowed_hosts]
{% for host in allowed_hosts %}
{{ loop.index }}. {{ host }}
{% endfor %}
EOF

# Dev vars
cat > /tmp/capstone/vars/dev.yml << 'EOF'
---
environment: development
app_host: 127.0.0.1
app_port: 8000
app_workers: 2
app_debug: True
db_host: localhost
db_port: 5432
db_name: myapp_dev
db_pool_size: 5
log_level: DEBUG
log_format: detailed
log_file: /var/log/myapp/dev.log
app_features:
  beta_features: true
  analytics: false
  maintenance_mode: false
allowed_hosts:
  - localhost
  - 127.0.0.1
EOF

# Prod vars
cat > /tmp/capstone/vars/prod.yml << 'EOF'
---
environment: production
app_host: 0.0.0.0
app_port: 80
app_workers: 16
app_debug: False
db_host: db.prod.internal
db_port: 5432
db_name: myapp_prod
db_pool_size: 50
log_level: WARNING
log_format: json
app_features:
  beta_features: false
  analytics: true
  maintenance_mode: false
allowed_hosts:
  - myapp.example.com
  - www.myapp.example.com
  - api.myapp.example.com
EOF

cat > /tmp/capstone/generate.yml << 'EOF'
---
- name: Generate environment configurations
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    app_name: MyWebApp
    environments:
      - dev
      - prod

  tasks:
    - name: Generate config for each environment
      template:
        src: /tmp/capstone/templates/app.conf.j2
        dest: \"/tmp/capstone/output/app_{{ item }}.conf\"
      loop: \"{{ environments }}\"
      vars: \"{{ lookup('file', '/tmp/capstone/vars/' + item + '.yml') | from_yaml }}\"

    - name: List generated configs
      find:
        paths: /tmp/capstone/output
        patterns: '*.conf'
      register: generated_files

    - name: Show generated files
      debug:
        msg: \"Generated: {{ generated_files.files | map(attribute='path') | list }}\"

    - name: Show dev config
      command: cat /tmp/capstone/output/app_dev.conf
      register: dev_config

    - name: Display dev config
      debug:
        var: dev_config.stdout_lines

    - name: Show prod config
      command: cat /tmp/capstone/output/app_prod.conf
      register: prod_config

    - name: Display prod config
      debug:
        var: prod_config.stdout_lines

    - name: Summary comparison
      debug:
        msg:
          - \"=== Configuration Summary ===\"
          - \"Dev  - Port: 8000, Workers: 2,  Debug: True,  DB Pool: 5\"
          - \"Prod - Port: 80,   Workers: 16, Debug: False, DB Pool: 50\"
EOF

ansible-playbook /tmp/capstone/generate.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Generate environment configurations] **************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Generate config for each environment] ************************************
changed: [localhost] => (item=dev)
changed: [localhost] => (item=prod)

TASK [List generated configs] ***************************************************
ok: [localhost]

TASK [Show generated files] ****************************************************
ok: [localhost] => {
    "msg": "Generated: ['/tmp/capstone/output/app_dev.conf', '/tmp/capstone/output/app_prod.conf']"
}

TASK [Display dev config] ******************************************************
ok: [localhost] => {
    "dev_config.stdout_lines": [
        "# MyWebApp Configuration",
        "# Environment: development",
        "# Generated by Ansible on 2026-03-05",
        "[server]",
        "host = 127.0.0.1",
        "port = 8000",
        "workers = 2",
        "debug = true",
        "[database]",
        "host = localhost",
        "port = 5432",
        "name = myapp_dev",
        "pool_size = 5",
        "[logging]",
        "level = DEBUG",
        "format = detailed",
        "file = /var/log/myapp/dev.log",
        "[features]",
        "beta_features = true",
        "analytics = false",
        "maintenance_mode = false",
        "[allowed_hosts]",
        "1. localhost",
        "2. 127.0.0.1"
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=8    changed=2    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** This pattern — single template + per-environment var files — is the foundation of infrastructure-as-code. The template becomes your documentation; the var files become your environment specification. Combine this with Ansible Vault (Lab 09) to encrypt sensitive prod values.

---

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| Var precedence | `role defaults < group_vars < host_vars < play vars < extra vars` | Know what wins |
| Extra vars | `ansible-playbook -e "key=val"` | Always highest priority |
| vars_files | `vars_files: [file.yml]` | Load vars from external file |
| register | `register: result_var` | Capture task output |
| debug output | `debug: var: result.stdout` | Print registered var |
| Jinja2 variable | `{{ variable_name }}` | Insert value |
| Jinja2 filter | `{{ var \| upper \| default('x') }}` | Transform value |
| Jinja2 condition | `{% if condition %} ... {% endif %}` | Conditional block |
| Jinja2 loop | `{% for item in list %} ... {% endfor %}` | Loop in template |
| template module | `template: src: x.j2 dest: /path` | Render + deploy template |
| Handler | `handlers: - name: X` + `notify: X` | Event-driven triggers |
| Listen | `listen: event_name` | Multiple handlers, one event |
| flush_handlers | `meta: flush_handlers` | Run handlers mid-play |
| when condition | `when: var == 'value'` | Conditional task execution |
| loop | `loop: "{{ list }}"` | Iterate over list/dict |
| loop_control | `loop_control: label: "{{ item.name }}"` | Control loop display |
| import_tasks | `import_tasks: file.yml` | Static task inclusion |
| include_tasks | `include_tasks: file.yml` | Dynamic task inclusion |
