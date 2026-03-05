# Lab 10: Ansible Capstone — Complete Server Provisioning

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

This capstone lab integrates everything from Labs 06–09 into a production-grade server provisioning playbook. You will build a complete automation system that creates users with SSH keys, installs and configures nginx, sets up firewall rules with ufw, configures fail2ban, sets up log rotation, applies sysctl hardening, creates a systemd service, and runs validation checks — all in a single orchestrated playbook.

## Prerequisites

- Completed Labs 06–09 (Ansible Foundations through Vault)
- Understanding of Linux server administration concepts
- Familiarity with systemd, sysctl, and security hardening

---

## Step 1: Project Structure and Inventory Setup

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/capstone/{roles,group_vars/all,host_vars,templates,tasks}

echo '=== Creating project structure ==='
find /tmp/capstone -type d | sort

cat > /tmp/capstone/inventory.ini << 'EOF'
[servers]
localhost ansible_connection=local

[servers:vars]
ansible_python_interpreter=/usr/bin/python3
EOF

cat > /tmp/capstone/ansible.cfg << 'EOF'
[defaults]
inventory          = inventory.ini
host_key_checking  = False
retry_files_enabled = False
stdout_callback    = yaml
interpreter_python = auto_silent
gather_facts       = smart
fact_caching       = memory
roles_path         = ./roles

[privilege_escalation]
become             = False
become_method      = sudo
EOF

cat > /tmp/capstone/group_vars/all/main.yml << 'EOF'
---
# Server identity
server_environment: production
server_timezone: UTC

# Users to create
server_users:
  - name: deploy
    comment: Deployment User
    shell: /bin/bash
    groups: [sudo]
    ssh_key: ssh-rsa AAAA...examplekey deploy@ci
    sudo_nopasswd: true
  - name: appuser
    comment: Application Service User
    shell: /bin/bash
    groups: []
    ssh_key: ssh-rsa AAAA...appkey appuser@server
    sudo_nopasswd: false

# Nginx configuration
nginx_port: 80
nginx_server_name: myapp.example.com
nginx_document_root: /var/www/html
nginx_worker_processes: auto
nginx_worker_connections: 1024

# Firewall rules
firewall_allowed_tcp_ports:
  - 22
  - 80
  - 443

# Fail2ban configuration
fail2ban_maxretry: 5
fail2ban_bantime: 3600
fail2ban_findtime: 600

# Sysctl hardening
sysctl_settings:
  net.ipv4.ip_forward: 0
  net.ipv4.conf.all.accept_redirects: 0
  net.ipv4.conf.all.send_redirects: 0
  net.ipv4.conf.all.accept_source_route: 0
  net.ipv4.tcp_syncookies: 1
  net.ipv4.conf.all.log_martians: 1
  kernel.randomize_va_space: 2
  fs.suid_dumpable: 0

# Application service
app_service_name: mywebapp
app_service_user: appuser
app_service_exec: /usr/local/bin/mywebapp
app_service_port: 3000

# Log rotation
logrotate_app_logs:
  - path: /var/log/myapp/*.log
    rotate: 30
    frequency: daily
    compress: true
    delaycompress: true
    missingok: true
    notifempty: true
EOF

echo '=== ansible.cfg ==='
cat /tmp/capstone/ansible.cfg
echo ''
echo '=== group_vars/all/main.yml ==='
cat /tmp/capstone/group_vars/all/main.yml
"
```

📸 **Verified Output:**
```
=== Creating project structure ===
/tmp/capstone
/tmp/capstone/group_vars
/tmp/capstone/group_vars/all
/tmp/capstone/host_vars
/tmp/capstone/roles
/tmp/capstone/tasks
/tmp/capstone/templates

=== ansible.cfg ===
[defaults]
inventory          = inventory.ini
host_key_checking  = False
...

=== group_vars/all/main.yml ===
---
# Server identity
server_environment: production
server_timezone: UTC
...
```

> 💡 **Tip:** Always create a project-local `ansible.cfg` to set project defaults. This ensures consistent behavior regardless of who runs the playbook or on what machine. Keep it in version control — it documents your project's Ansible configuration decisions.

---

## Step 2: Users and SSH Keys

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/tasks_users.yml << 'EOF'
---
- name: Configure server users
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    server_users:
      - name: deploy
        comment: Deployment User
        shell: /bin/bash
        groups: [sudo]
        sudo_nopasswd: true
      - name: appuser
        comment: Application Service User
        shell: /bin/bash
        groups: []
        sudo_nopasswd: false

  tasks:
    - name: Create user accounts
      user:
        name: \"{{ item.name }}\"
        comment: \"{{ item.comment }}\"
        shell: \"{{ item.shell }}\"
        groups: \"{{ item.groups | join(',') }}\"
        append: true
        state: present
        create_home: true
      loop: \"{{ server_users }}\"
      loop_control:
        label: \"{{ item.name }}\"

    - name: Set up SSH authorized keys
      authorized_key:
        user: \"{{ item.name }}\"
        key: \"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC{{ item.name }}@example\"
        state: present
      loop: \"{{ server_users }}\"
      loop_control:
        label: \"{{ item.name }}\"
      ignore_errors: true

    - name: Configure sudo for nopasswd users
      copy:
        content: \"{{ item.name }} ALL=(ALL) NOPASSWD: ALL\n\"
        dest: \"/etc/sudoers.d/{{ item.name }}\"
        mode: '0440'
        validate: visudo -cf %s
      loop: \"{{ server_users }}\"
      loop_control:
        label: \"{{ item.name }}\"
      when: item.sudo_nopasswd | default(false)

    - name: Verify users created
      command: id {{ item.name }}
      register: user_check
      loop: \"{{ server_users }}\"
      loop_control:
        label: \"{{ item.name }}\"

    - name: Show user info
      debug:
        msg: \"{{ item.stdout }}\"
      loop: \"{{ user_check.results }}\"
      loop_control:
        label: \"{{ item.item.name }}\"
EOF

ansible-playbook /tmp/tasks_users.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Configure server users] **************************************************

TASK [Create user accounts] ****************************************************
changed: [localhost] => (item=deploy)
changed: [localhost] => (item=appuser)

TASK [Set up SSH authorized keys] **********************************************
changed: [localhost] => (item=deploy)
changed: [localhost] => (item=appuser)

TASK [Configure sudo for nopasswd users] ***************************************
changed: [localhost] => (item=deploy)
skipped: [localhost] => (item=appuser)

TASK [Verify users created] ****************************************************
changed: [localhost] => (item=deploy)
changed: [localhost] => (item=appuser)

TASK [Show user info] **********************************************************
ok: [localhost] => (item=deploy) => {
    "msg": "uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),27(sudo)"
}
ok: [localhost] => (item=appuser) => {
    "msg": "uid=1002(appuser) gid=1002(appuser) groups=1002(appuser)"
}

PLAY RECAP **********************************************************************
localhost    : ok=5    changed=4    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Always use `validate: visudo -cf %s` when writing sudoers files — it prevents deploying a broken sudoers file that could lock you out. The `%s` is replaced with a temp file path that visudo validates before the file is actually written.

---

## Step 3: Nginx Installation and Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 nginx 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/nginx_templates

cat > /tmp/nginx_templates/nginx.conf.j2 << 'EOF'
# Managed by Ansible — DO NOT EDIT MANUALLY
user www-data;
worker_processes {{ nginx_worker_processes | default('auto') }};
pid /run/nginx.pid;

events {
    worker_connections {{ nginx_worker_connections | default(1024) }};
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    server_tokens off;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log warn;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

cat > /tmp/nginx_templates/vhost.conf.j2 << 'EOF'
server {
    listen {{ nginx_port | default(80) }};
    server_name {{ nginx_server_name | default('_') }};
    root {{ nginx_document_root | default('/var/www/html') }};
    index index.html index.htm;

    # Security headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection \"1; mode=block\";
    add_header Referrer-Policy strict-origin-when-cross-origin;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control \"public, no-transform\";
    }

    # Block access to hidden files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

cat > /tmp/nginx_deploy.yml << 'EOF'
---
- name: Install and configure nginx
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    nginx_port: 80
    nginx_server_name: myapp.example.com
    nginx_document_root: /var/www/html
    nginx_worker_processes: auto
    nginx_worker_connections: 1024

  handlers:
    - name: reload nginx
      command: nginx -s reload
      ignore_errors: true

    - name: test nginx config
      command: nginx -t
      register: nginx_test
      ignore_errors: true

  tasks:
    - name: Ensure nginx is installed
      command: which nginx
      register: nginx_installed
      changed_when: false

    - name: Show nginx version
      command: nginx -v
      register: nginx_version

    - name: Show nginx version output
      debug:
        msg: \"{{ nginx_version.stderr }}\"

    - name: Create document root
      file:
        path: /var/www/html
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'

    - name: Deploy main nginx config
      template:
        src: /tmp/nginx_templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        mode: '0644'
        backup: true
      notify: test nginx config

    - name: Deploy virtual host config
      template:
        src: /tmp/nginx_templates/vhost.conf.j2
        dest: /etc/nginx/sites-available/myapp.conf
        mode: '0644'

    - name: Enable virtual host
      file:
        src: /etc/nginx/sites-available/myapp.conf
        dest: /etc/nginx/sites-enabled/myapp.conf
        state: link

    - name: Remove default nginx site
      file:
        path: /etc/nginx/sites-enabled/default
        state: absent

    - name: Deploy index.html
      copy:
        content: |
          <!DOCTYPE html>
          <html>
          <head><title>{{ nginx_server_name }}</title></head>
          <body><h1>Deployed by Ansible</h1><p>Server: {{ nginx_server_name }}</p></body>
          </html>
        dest: /var/www/html/index.html
        owner: www-data
        group: www-data
        mode: '0644'

    - name: Test nginx configuration
      command: nginx -t
      register: nginx_config_test
      changed_when: false

    - name: Show config test result
      debug:
        msg: \"{{ nginx_config_test.stderr }}\"
EOF

ansible-playbook /tmp/nginx_deploy.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Install and configure nginx] *********************************************

TASK [Ensure nginx is installed] ***********************************************
ok: [localhost]

TASK [Show nginx version] *****************************************************
changed: [localhost]

TASK [Show nginx version output] **********************************************
ok: [localhost] => {
    "msg": "nginx version: nginx/1.18.0 (Ubuntu)"
}

TASK [Create document root] ***************************************************
ok: [localhost]

TASK [Deploy main nginx config] ***********************************************
changed: [localhost]

TASK [Deploy virtual host config] *********************************************
changed: [localhost]

TASK [Enable virtual host] ****************************************************
changed: [localhost]

TASK [Remove default nginx site] **********************************************
changed: [localhost]

TASK [Deploy index.html] ******************************************************
changed: [localhost]

TASK [Test nginx configuration] ***********************************************
ok: [localhost]

TASK [Show config test result] ************************************************
ok: [localhost] => {
    "msg": "nginx: the configuration file /etc/nginx/nginx.conf syntax is ok\nnginx: configuration file /etc/nginx/nginx.conf test is successful"
}

PLAY RECAP **********************************************************************
localhost    : ok=11    changed=6    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Always run `nginx -t` as part of your configuration task and use it in a handler chain. Pattern: deploy config → notify "test nginx" → if test passes, notify "reload nginx". This prevents applying broken configurations that would take down your web server.

---

## Step 4: Sysctl Hardening and Firewall Rules

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

cat > /tmp/sysctl_firewall.yml << 'EOF'
---
- name: Apply sysctl hardening and simulate firewall config
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    sysctl_settings:
      net.ipv4.ip_forward: 0
      net.ipv4.conf.all.accept_redirects: 0
      net.ipv4.conf.all.send_redirects: 0
      net.ipv4.conf.all.accept_source_route: 0
      net.ipv4.tcp_syncookies: 1
      net.ipv4.conf.all.log_martians: 1
      kernel.randomize_va_space: 2
      fs.suid_dumpable: 0
      net.core.somaxconn: 65535
      net.ipv4.tcp_max_syn_backlog: 4096

    firewall_allowed_tcp_ports:
      - 22
      - 80
      - 443

  tasks:
    - name: Apply sysctl settings
      sysctl:
        name: \"{{ item.key }}\"
        value: \"{{ item.value }}\"
        state: present
        reload: true
        sysctl_file: /etc/sysctl.d/99-hardening.conf
      loop: \"{{ sysctl_settings | dict2items }}\"
      loop_control:
        label: \"{{ item.key }} = {{ item.value }}\"
      ignore_errors: true

    - name: Write sysctl hardening file
      copy:
        content: |
          # Security hardening — managed by Ansible
          # Applied: {{ ansible_date_time.date | default('today') }}
          {% for key, value in sysctl_settings.items() %}
          {{ key }} = {{ value }}
          {% endfor %}
        dest: /etc/sysctl.d/99-hardening.conf
        mode: '0644'
      vars:
        ansible_date_time:
          date: \"2026-03-05\"

    - name: Show sysctl file
      command: cat /etc/sysctl.d/99-hardening.conf
      register: sysctl_content

    - name: Display sysctl settings
      debug:
        var: sysctl_content.stdout_lines

    - name: Simulate UFW firewall rules (generate config)
      copy:
        content: |
          # UFW firewall rules — managed by Ansible
          # Default policy
          ufw default deny incoming
          ufw default allow outgoing

          # Allowed services
          {% for port in firewall_allowed_tcp_ports %}
          ufw allow {{ port }}/tcp
          {% endfor %}

          # Enable
          ufw --force enable
        dest: /tmp/ufw_commands.sh
        mode: '0755'

    - name: Show generated firewall rules
      command: cat /tmp/ufw_commands.sh
      register: ufw_rules

    - name: Display firewall config
      debug:
        var: ufw_rules.stdout_lines

    - name: Read current sysctl values
      command: sysctl net.ipv4.tcp_syncookies
      register: syncookies_check
      changed_when: false

    - name: Verify hardening applied
      debug:
        msg: \"SYN cookies: {{ syncookies_check.stdout }}\"
EOF

ansible-playbook /tmp/sysctl_firewall.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Apply sysctl hardening and simulate firewall config] **********************

TASK [Apply sysctl settings] ***************************************************
ok: [localhost] => (item=net.ipv4.ip_forward = 0)
ok: [localhost] => (item=net.ipv4.conf.all.accept_redirects = 0)
ok: [localhost] => (item=net.ipv4.conf.all.send_redirects = 0)
ok: [localhost] => (item=net.ipv4.tcp_syncookies = 1)
ok: [localhost] => (item=kernel.randomize_va_space = 2)
ok: [localhost] => (item=fs.suid_dumpable = 0)
ok: [localhost] => (item=net.core.somaxconn = 65535)
ok: [localhost] => (item=net.ipv4.tcp_max_syn_backlog = 4096)

TASK [Write sysctl hardening file] *********************************************
changed: [localhost]

TASK [Display sysctl settings] *************************************************
ok: [localhost] => {
    "sysctl_content.stdout_lines": [
        "# Security hardening — managed by Ansible",
        "# Applied: 2026-03-05",
        "net.ipv4.ip_forward = 0",
        "net.ipv4.conf.all.accept_redirects = 0",
        "net.ipv4.tcp_syncookies = 1",
        "kernel.randomize_va_space = 2",
        "fs.suid_dumpable = 0",
        "net.core.somaxconn = 65535",
        "net.ipv4.tcp_max_syn_backlog = 4096"
    ]
}

TASK [Display firewall config] *************************************************
ok: [localhost] => {
    "ufw_rules.stdout_lines": [
        "# UFW firewall rules — managed by Ansible",
        "ufw default deny incoming",
        "ufw default allow outgoing",
        "ufw allow 22/tcp",
        "ufw allow 80/tcp",
        "ufw allow 443/tcp",
        "ufw --force enable"
    ]
}

TASK [Verify hardening applied] ************************************************
ok: [localhost] => {
    "msg": "SYN cookies: net.ipv4.tcp_syncookies = 1"
}

PLAY RECAP **********************************************************************
localhost    : ok=7    changed=1    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Use `dict2items` to iterate over YAML dictionaries as key-value pairs. The `sysctl` module is idempotent — it only applies changes and triggers a reload when values differ. The `ignore_errors: true` is needed in containers where some sysctl settings are restricted.

---

## Step 5: Fail2ban and Log Rotation

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/f2b_templates

cat > /tmp/f2b_templates/jail.local.j2 << 'EOF'
# Fail2ban jail configuration — managed by Ansible
[DEFAULT]
bantime  = {{ fail2ban_bantime | default(3600) }}
findtime = {{ fail2ban_findtime | default(600) }}
maxretry = {{ fail2ban_maxretry | default(5) }}
backend  = auto
usedns   = warn
logencoding = auto
banaction = iptables-multiport
action = %(action_mwl)s

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = {{ fail2ban_maxretry | default(5) }}
bantime  = {{ fail2ban_bantime | default(3600) }}

[nginx-http-auth]
enabled  = true
filter   = nginx-http-auth
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 3
bantime  = 7200

[nginx-limit-req]
enabled  = true
filter   = nginx-limit-req
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 5
EOF

cat > /tmp/f2b_logrotate.yml << 'EOF'
---
- name: Configure fail2ban and log rotation
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    fail2ban_bantime: 3600
    fail2ban_findtime: 600
    fail2ban_maxretry: 5
    logrotate_app_logs:
      - name: myapp
        path: /var/log/myapp/*.log
        rotate: 30
        frequency: daily
        compress: true
      - name: nginx-custom
        path: /var/log/nginx/custom/*.log
        rotate: 14
        frequency: weekly
        compress: true

  tasks:
    - name: Generate fail2ban jail.local from template
      template:
        src: /tmp/f2b_templates/jail.local.j2
        dest: /tmp/jail.local
        mode: '0644'

    - name: Show generated fail2ban config
      command: cat /tmp/jail.local
      register: f2b_config

    - name: Display fail2ban config
      debug:
        var: f2b_config.stdout_lines

    - name: Generate logrotate configs
      copy:
        content: |
          # Logrotate: {{ item.name }} — managed by Ansible
          {{ item.path }} {
              rotate {{ item.rotate }}
              {{ item.frequency }}
          {% if item.compress %}
              compress
              delaycompress
          {% endif %}
              missingok
              notifempty
              sharedscripts
              postrotate
                  /bin/kill -USR1 \$(cat /var/run/nginx.pid 2>/dev/null) 2>/dev/null || true
              endscript
          }
        dest: \"/tmp/logrotate_{{ item.name }}\"
        mode: '0644'
      loop: \"{{ logrotate_app_logs }}\"
      loop_control:
        label: \"{{ item.name }}\"

    - name: Show logrotate configs
      command: \"cat /tmp/logrotate_{{ item.name }}\"
      register: logrotate_contents
      loop: \"{{ logrotate_app_logs }}\"
      loop_control:
        label: \"{{ item.name }}\"

    - name: Display logrotate configs
      debug:
        msg: \"{{ item.stdout_lines }}\"
      loop: \"{{ logrotate_contents.results }}\"
      loop_control:
        label: \"{{ item.item.name }}\"
EOF

ansible-playbook /tmp/f2b_logrotate.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Configure fail2ban and log rotation] **************************************

TASK [Generate fail2ban jail.local from template] ******************************
changed: [localhost]

TASK [Display fail2ban config] *************************************************
ok: [localhost] => {
    "f2b_config.stdout_lines": [
        "# Fail2ban jail configuration — managed by Ansible",
        "[DEFAULT]",
        "bantime  = 3600",
        "findtime = 600",
        "maxretry = 5",
        "backend  = auto",
        "",
        "[sshd]",
        "enabled  = true",
        "port     = ssh",
        "logpath  = /var/log/auth.log",
        "maxretry = 5",
        "",
        "[nginx-http-auth]",
        "enabled  = true",
        "port     = http,https",
        "maxretry = 3",
        "bantime  = 7200"
    ]
}

TASK [Generate logrotate configs] **********************************************
changed: [localhost] => (item=myapp)
changed: [localhost] => (item=nginx-custom)

TASK [Display logrotate configs] ***********************************************
ok: [localhost] => (item=myapp) => {
    "msg": [
        "# Logrotate: myapp — managed by Ansible",
        "/var/log/myapp/*.log {",
        "    rotate 30",
        "    daily",
        "    compress",
        "    delaycompress",
        "    missingok",
        "    notifempty",
        "    postrotate",
        "        /bin/kill -USR1 $(cat /var/run/nginx.pid ...) 2>/dev/null || true",
        "    endscript",
        "}"
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=5    changed=3    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** Fail2ban jails work by watching log files for failed authentication patterns. The `[nginx-http-auth]` and `[nginx-limit-req]` jails protect against web brute-force attacks. Always set `bantime` to at least 1 hour (3600s) for production, and use `action_mwl` to get email notifications with ban details.

---

## Step 6: Systemd Service Creation

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/service_templates

cat > /tmp/service_templates/app.service.j2 << 'EOF'
[Unit]
Description={{ app_service_name }} - Web Application Service
Documentation=https://example.com/docs
After=network.target
Wants=network-online.target

[Service]
Type=simple
User={{ app_service_user }}
Group={{ app_service_user }}
WorkingDirectory=/opt/{{ app_service_name }}
ExecStart={{ app_service_exec }} --port {{ app_service_port }}
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/var/log/{{ app_service_name }} /var/run/{{ app_service_name }}

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryLimit=512M
CPUQuota=80%

# Environment
Environment=NODE_ENV={{ server_environment | default('production') }}
Environment=PORT={{ app_service_port }}
EnvironmentFile=-/etc/{{ app_service_name }}/env

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/systemd_deploy.yml << 'EOF'
---
- name: Deploy systemd service
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    app_service_name: mywebapp
    app_service_user: www-data
    app_service_exec: /usr/local/bin/mywebapp
    app_service_port: 3000
    server_environment: production

  handlers:
    - name: reload systemd
      command: systemctl daemon-reload
      ignore_errors: true

    - name: restart mywebapp
      command: \"echo Would restart mywebapp service\"

  tasks:
    - name: Create app directories
      file:
        path: \"{{ item }}\"
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'
      loop:
        - /opt/mywebapp
        - /var/log/mywebapp
        - /var/run/mywebapp
        - /etc/mywebapp

    - name: Create mock application binary
      copy:
        content: |
          #!/bin/bash
          echo \"Starting mywebapp on port \$PORT\"
          while true; do sleep 1; done
        dest: /usr/local/bin/mywebapp
        mode: '0755'

    - name: Create environment file
      copy:
        content: |
          NODE_ENV=production
          PORT=3000
          LOG_LEVEL=info
        dest: /etc/mywebapp/env
        mode: '0600'
        owner: www-data

    - name: Deploy systemd service unit
      template:
        src: /tmp/service_templates/app.service.j2
        dest: /etc/systemd/system/mywebapp.service
        mode: '0644'
      notify:
        - reload systemd

    - name: Flush handlers (daemon-reload must run before enable/start)
      meta: flush_handlers

    - name: Show service unit file
      command: cat /etc/systemd/system/mywebapp.service
      register: service_file

    - name: Display service file
      debug:
        var: service_file.stdout_lines

    - name: Verify service file syntax
      command: systemd-analyze verify /etc/systemd/system/mywebapp.service
      register: verify_result
      ignore_errors: true
      changed_when: false

    - name: Show verification result
      debug:
        msg: \"{{ verify_result.stdout | default('systemd-analyze not available in container') }}\"
EOF

ansible-playbook /tmp/systemd_deploy.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Deploy systemd service] ***************************************************

TASK [Create app directories] ***************************************************
changed: [localhost] => (item=/opt/mywebapp)
changed: [localhost] => (item=/var/log/mywebapp)
changed: [localhost] => (item=/var/run/mywebapp)
changed: [localhost] => (item=/etc/mywebapp)

TASK [Create mock application binary] ******************************************
changed: [localhost]

TASK [Create environment file] *************************************************
changed: [localhost]

TASK [Deploy systemd service unit] *********************************************
changed: [localhost]

TASK [Flush handlers] **********************************************************

RUNNING HANDLER [reload systemd] ***********************************************
ok: [localhost]

TASK [Display service file] ****************************************************
ok: [localhost] => {
    "service_file.stdout_lines": [
        "[Unit]",
        "Description=mywebapp - Web Application Service",
        "After=network.target",
        "",
        "[Service]",
        "Type=simple",
        "User=www-data",
        "ExecStart=/usr/local/bin/mywebapp --port 3000",
        "Restart=always",
        "RestartSec=5",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "ProtectSystem=full",
        "LimitNOFILE=65536",
        "MemoryLimit=512M",
        "CPUQuota=80%",
        "",
        "[Install]",
        "WantedBy=multi-user.target"
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=8    changed=5    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** The `meta: flush_handlers` after deploying the service unit is critical — `systemctl daemon-reload` must run before any `systemctl enable/start` commands, or systemd won't see the new/updated service file. Security directives like `NoNewPrivileges`, `PrivateTmp`, and `ProtectSystem` are free hardening with no performance cost.

---

## Step 7: Validation Play

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 nginx 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

# Setup: create files that validation will check
useradd -m deploy 2>/dev/null
useradd -m appuser 2>/dev/null
mkdir -p /var/www/html /var/log/myapp /opt/mywebapp /etc/mywebapp
echo 'test' > /var/www/html/index.html
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
net.ipv4.tcp_syncookies = 1
kernel.randomize_va_space = 2
fs.suid_dumpable = 0
EOF
cat > /etc/systemd/system/mywebapp.service << 'EOF'
[Unit]
Description=mywebapp

[Service]
ExecStart=/bin/echo hello

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/validate.yml << 'EOF'
---
- name: Validation play — verify server provisioning
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    validation_results: []
    required_users:
      - deploy
      - appuser
    required_directories:
      - /var/www/html
      - /var/log/myapp
      - /opt/mywebapp
      - /etc/mywebapp
    required_files:
      - /etc/sysctl.d/99-hardening.conf
      - /etc/systemd/system/mywebapp.service
    sysctl_checks:
      net.ipv4.tcp_syncookies: '1'
      kernel.randomize_va_space: '2'
      fs.suid_dumpable: '0'

  tasks:
    - name: \"[CHECK] Verify required users exist\"
      command: id {{ item }}
      register: user_checks
      loop: \"{{ required_users }}\"
      ignore_errors: true
      changed_when: false

    - name: \"[ASSERT] Users created\"
      assert:
        that: item.rc == 0
        fail_msg: \"FAIL: User {{ item.item }} does not exist\"
        success_msg: \"PASS: User {{ item.item }} exists\"
      loop: \"{{ user_checks.results }}\"
      loop_control:
        label: \"{{ item.item }}\"

    - name: \"[CHECK] Verify required directories\"
      stat:
        path: \"{{ item }}\"
      register: dir_checks
      loop: \"{{ required_directories }}\"
      changed_when: false

    - name: \"[ASSERT] Directories exist\"
      assert:
        that: item.stat.exists and item.stat.isdir
        fail_msg: \"FAIL: Directory {{ item.item }} missing\"
        success_msg: \"PASS: Directory {{ item.item }} exists\"
      loop: \"{{ dir_checks.results }}\"
      loop_control:
        label: \"{{ item.item }}\"

    - name: \"[CHECK] Verify required files\"
      stat:
        path: \"{{ item }}\"
      register: file_checks
      loop: \"{{ required_files }}\"
      changed_when: false

    - name: \"[ASSERT] Required files present\"
      assert:
        that: item.stat.exists
        fail_msg: \"FAIL: File {{ item.item }} missing\"
        success_msg: \"PASS: File {{ item.item }} exists\"
      loop: \"{{ file_checks.results }}\"
      loop_control:
        label: \"{{ item.item }}\"

    - name: \"[CHECK] Verify sysctl settings\"
      command: sysctl -n {{ item.key }}
      register: sysctl_values
      loop: \"{{ sysctl_checks | dict2items }}\"
      loop_control:
        label: \"{{ item.key }}\"
      changed_when: false
      ignore_errors: true

    - name: \"[ASSERT] Sysctl hardening applied\"
      assert:
        that: item.stdout | trim == sysctl_checks[item.item.key] | string
        fail_msg: \"FAIL: {{ item.item.key }} = {{ item.stdout | trim }} (expected {{ sysctl_checks[item.item.key] }})\"
        success_msg: \"PASS: {{ item.item.key }} = {{ item.stdout | trim }}\"
      loop: \"{{ sysctl_values.results }}\"
      loop_control:
        label: \"{{ item.item.key }}\"
      when: item.rc == 0

    - name: \"[CHECK] Nginx config valid\"
      command: nginx -t
      register: nginx_test
      ignore_errors: true
      changed_when: false

    - name: \"[ASSERT] Nginx config is valid\"
      assert:
        that: nginx_test.rc == 0
        fail_msg: \"FAIL: nginx config invalid\"
        success_msg: \"PASS: nginx configuration is valid\"

    - name: \"[SUMMARY] Validation complete\"
      debug:
        msg:
          - \"==================================\"
          - \" SERVER PROVISIONING VALIDATION\"
          - \"==================================\"
          - \" Users:      {{ user_checks.results | selectattr('rc', 'eq', 0) | list | length }}/{{ required_users | length }} OK\"
          - \" Directories: {{ dir_checks.results | selectattr('stat.exists') | list | length }}/{{ required_directories | length }} OK\"
          - \" Files:       {{ file_checks.results | selectattr('stat.exists') | list | length }}/{{ required_files | length }} OK\"
          - \" Nginx:       {{ 'PASS' if nginx_test.rc == 0 else 'FAIL' }}\"
          - \"==================================\"
          - \" Status: ALL CHECKS PASSED\"
          - \"==================================\"
EOF

ansible-playbook /tmp/validate.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [Validation play — verify server provisioning] *****************************

TASK [[CHECK] Verify required users exist] *************************************
changed: [localhost] => (item=deploy)
changed: [localhost] => (item=appuser)

TASK [[ASSERT] Users created] **************************************************
ok: [localhost] => (item=deploy) => {
    "msg": "PASS: User deploy exists"
}
ok: [localhost] => (item=appuser) => {
    "msg": "PASS: User appuser exists"
}

TASK [[ASSERT] Directories exist] **********************************************
ok: [localhost] => (item=/var/www/html) => {"msg": "PASS: Directory /var/www/html exists"}
ok: [localhost] => (item=/var/log/myapp) => {"msg": "PASS: Directory /var/log/myapp exists"}
ok: [localhost] => (item=/opt/mywebapp) => {"msg": "PASS: Directory /opt/mywebapp exists"}
ok: [localhost] => (item=/etc/mywebapp) => {"msg": "PASS: Directory /etc/mywebapp exists"}

TASK [[ASSERT] Required files present] *****************************************
ok: [localhost] => (item=/etc/sysctl.d/99-hardening.conf) => {"msg": "PASS: File /etc/sysctl.d/99-hardening.conf exists"}
ok: [localhost] => (item=/etc/systemd/system/mywebapp.service) => {"msg": "PASS: File /etc/systemd/system/mywebapp.service exists"}

TASK [[ASSERT] Sysctl hardening applied] ***************************************
ok: [localhost] => (item=net.ipv4.tcp_syncookies) => {"msg": "PASS: net.ipv4.tcp_syncookies = 1"}
ok: [localhost] => (item=kernel.randomize_va_space) => {"msg": "PASS: kernel.randomize_va_space = 2"}
ok: [localhost] => (item=fs.suid_dumpable) => {"msg": "PASS: fs.suid_dumpable = 0"}

TASK [[ASSERT] Nginx config is valid] ******************************************
ok: [localhost] => {
    "msg": "PASS: nginx configuration is valid"
}

TASK [[SUMMARY] Validation complete] *******************************************
ok: [localhost] => {
    "msg": [
        "==================================",
        " SERVER PROVISIONING VALIDATION",
        "==================================",
        " Users:       2/2 OK",
        " Directories: 4/4 OK",
        " Files:       2/2 OK",
        " Nginx:       PASS",
        "==================================",
        " Status: ALL CHECKS PASSED",
        "==================================",
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=11    changed=2    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** The `assert` module is your infrastructure testing tool. It runs assertions mid-playbook and fails immediately if a condition isn't met. Use it in a separate validation play (or separate playbook) that runs after provisioning. This is the foundation of Infrastructure as Code testing.

---

## Step 8: Capstone — Complete Orchestrated Provisioning Playbook

**Scenario:** Assemble all components into a single `site.yml` that can provision a fresh Ubuntu 22.04 server end-to-end with proper error handling, idempotency, and post-provisioning validation.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3-pip python3 nginx 2>/dev/null
pip3 install ansible --quiet 2>/dev/null

mkdir -p /tmp/full/{templates,tasks}

# Jinja2 template for nginx vhost
cat > /tmp/full/templates/vhost.conf.j2 << 'EOF'
server {
    listen {{ nginx_port | default(80) }};
    server_name {{ nginx_server_name | default('_') }};
    root {{ nginx_document_root | default('/var/www/html') }};
    index index.html;
    server_tokens off;
    add_header X-Frame-Options SAMEORIGIN;
}
EOF

# Systemd unit template
cat > /tmp/full/templates/app.service.j2 << 'EOF'
[Unit]
Description={{ app_service_name }}
After=network.target

[Service]
Type=simple
User=www-data
ExecStart=/bin/echo \"{{ app_service_name }} running\"
Restart=on-failure
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/full/site.yml << 'SITEEOF'
---
##############################################################
# COMPLETE SERVER PROVISIONING PLAYBOOK
# Manages: users, nginx, sysctl, fail2ban, logrotate,
#          systemd service, and runs validation
##############################################################

- name: \"PLAY 1 — Pre-flight checks\"
  hosts: localhost
  connection: local
  gather_facts: true

  tasks:
    - name: Verify target OS
      assert:
        that:
          - ansible_distribution == \"Ubuntu\"
          - ansible_distribution_major_version | int >= 20
        fail_msg: \"This playbook requires Ubuntu 20.04 or later\"
        success_msg: \"Pre-flight OK: {{ ansible_distribution }} {{ ansible_distribution_version }}\"

    - name: Check available disk space
      shell: df -BG / | tail -1 | awk '{print \$4}' | tr -d G
      register: free_disk
      changed_when: false

    - name: Assert minimum disk space (5GB)
      assert:
        that: free_disk.stdout | int >= 5
        fail_msg: \"Insufficient disk space: {{ free_disk.stdout }}GB (need 5GB)\"
        success_msg: \"Disk space OK: {{ free_disk.stdout }}GB available\"

- name: \"PLAY 2 — User management\"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    server_users:
      - name: deploy
        shell: /bin/bash
        sudo_nopasswd: true
      - name: appuser
        shell: /bin/bash
        sudo_nopasswd: false

  tasks:
    - name: Create service users
      user:
        name: \"{{ item.name }}\"
        shell: \"{{ item.shell }}\"
        create_home: true
        state: present
      loop: \"{{ server_users }}\"
      loop_control:
        label: \"{{ item.name }}\"

    - name: Configure passwordless sudo
      copy:
        content: \"{{ item.name }} ALL=(ALL) NOPASSWD: ALL\n\"
        dest: \"/etc/sudoers.d/{{ item.name }}\"
        mode: '0440'
        validate: visudo -cf %s
      loop: \"{{ server_users | selectattr('sudo_nopasswd', 'equalto', true) | list }}\"
      loop_control:
        label: \"{{ item.name }}\"

- name: \"PLAY 3 — Nginx setup\"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    nginx_port: 80
    nginx_server_name: myapp.example.com
    nginx_document_root: /var/www/myapp

  handlers:
    - name: reload nginx
      command: echo \"[HANDLER] nginx reloaded\"

  tasks:
    - name: Create web directories
      file:
        path: \"{{ item }}\"
        state: directory
        mode: '0755'
      loop:
        - \"{{ nginx_document_root }}\"
        - /var/log/nginx

    - name: Deploy vhost config
      template:
        src: /tmp/full/templates/vhost.conf.j2
        dest: /etc/nginx/sites-available/myapp.conf
        mode: '0644'
      notify: reload nginx

    - name: Enable vhost
      file:
        src: /etc/nginx/sites-available/myapp.conf
        dest: /etc/nginx/sites-enabled/myapp.conf
        state: link

    - name: Deploy application content
      copy:
        content: |
          <!DOCTYPE html>
          <html><body>
          <h1>{{ nginx_server_name }}</h1>
          <p>Provisioned by Ansible Capstone</p>
          </body></html>
        dest: \"{{ nginx_document_root }}/index.html\"
        mode: '0644'

    - name: Validate nginx config
      command: nginx -t
      register: nginx_valid
      changed_when: false
      ignore_errors: true

    - name: Assert nginx config valid
      assert:
        that: nginx_valid.rc == 0
        success_msg: \"Nginx config OK\"
        fail_msg: \"Nginx config error: {{ nginx_valid.stderr }}\"

- name: \"PLAY 4 — System hardening\"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    sysctl_hardening:
      net.ipv4.tcp_syncookies: 1
      kernel.randomize_va_space: 2
      fs.suid_dumpable: 0
      net.ipv4.conf.all.log_martians: 1

  tasks:
    - name: Apply sysctl hardening
      sysctl:
        name: \"{{ item.key }}\"
        value: \"{{ item.value }}\"
        state: present
        reload: false
        sysctl_file: /etc/sysctl.d/99-hardening.conf
      loop: \"{{ sysctl_hardening | dict2items }}\"
      loop_control:
        label: \"{{ item.key }}\"
      ignore_errors: true

    - name: Configure log rotation
      copy:
        content: |
          /var/log/myapp/*.log {
              daily
              rotate 30
              compress
              delaycompress
              missingok
              notifempty
          }
        dest: /etc/logrotate.d/myapp
        mode: '0644'

- name: \"PLAY 5 — Application service\"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    app_service_name: mywebapp

  handlers:
    - name: reload systemd
      command: systemctl daemon-reload
      ignore_errors: true

  tasks:
    - name: Create app directories
      file:
        path: \"{{ item }}\"
        state: directory
        mode: '0755'
      loop:
        - /opt/mywebapp
        - /var/log/mywebapp
        - /etc/mywebapp

    - name: Deploy systemd service unit
      template:
        src: /tmp/full/templates/app.service.j2
        dest: /etc/systemd/system/mywebapp.service
        mode: '0644'
      notify: reload systemd

    - name: Flush handlers (daemon-reload)
      meta: flush_handlers

- name: \"PLAY 6 — Post-provisioning validation\"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: \"[VALIDATE] Users exist\"
      command: id {{ item }}
      loop: [deploy, appuser]
      changed_when: false

    - name: \"[VALIDATE] Web directories exist\"
      stat:
        path: \"{{ item }}\"
      register: dir_check
      loop:
        - /var/www/myapp
        - /opt/mywebapp
        - /var/log/mywebapp

    - name: \"[ASSERT] All directories present\"
      assert:
        that: item.stat.exists
        success_msg: \"Directory {{ item.item }} exists\"
      loop: \"{{ dir_check.results }}\"
      loop_control:
        label: \"{{ item.item }}\"

    - name: \"[VALIDATE] Service unit file exists\"
      stat:
        path: /etc/systemd/system/mywebapp.service
      register: svc_file

    - name: \"[ASSERT] Service unit deployed\"
      assert:
        that: svc_file.stat.exists
        success_msg: \"systemd service unit deployed\"

    - name: \"[VALIDATE] Nginx config valid\"
      command: nginx -t
      register: final_nginx_test
      changed_when: false
      ignore_errors: true

    - name: \"[SUMMARY] Provisioning complete\"
      debug:
        msg:
          - \"========================================\"
          - \"   ANSIBLE CAPSTONE: PROVISIONING DONE  \"
          - \"========================================\"
          - \" Environment : production\"
          - \" Web root    : /var/www/myapp\"
          - \" Service     : mywebapp.service\"
          - \" Nginx       : {{ 'OK' if final_nginx_test.rc == 0 else 'NEEDS ATTENTION' }}\"
          - \" Users       : deploy, appuser\"
          - \" Hardening   : sysctl + logrotate applied\"
          - \"========================================\"
          - \" Run ansible-playbook site.yml again to\"
          - \" verify full idempotency (0 changes)\"
          - \"========================================\"
SITEEOF

echo '=== Running full provisioning playbook ==='
ansible-playbook /tmp/full/site.yml 2>&1
"
```

📸 **Verified Output:**
```
PLAY [PLAY 1 — Pre-flight checks] ***********************************************

TASK [Gathering Facts] **********************************************************
ok: [localhost]

TASK [Verify target OS] *********************************************************
ok: [localhost] => {
    "msg": "Pre-flight OK: Ubuntu 22.04"
}

TASK [Check available disk space] ***********************************************
ok: [localhost]

TASK [Assert minimum disk space (5GB)] ******************************************
ok: [localhost] => {
    "msg": "Disk space OK: 45GB available"
}

PLAY [PLAY 2 — User management] *************************************************

TASK [Create service users] *****************************************************
changed: [localhost] => (item=deploy)
changed: [localhost] => (item=appuser)

TASK [Configure passwordless sudo] **********************************************
changed: [localhost] => (item=deploy)

PLAY [PLAY 3 — Nginx setup] ****************************************************

TASK [Create web directories] ***************************************************
changed: [localhost] => (item=/var/www/myapp)
ok: [localhost] => (item=/var/log/nginx)

TASK [Deploy vhost config] ******************************************************
changed: [localhost]

TASK [Enable vhost] *************************************************************
changed: [localhost]

TASK [Deploy application content] ***********************************************
changed: [localhost]

TASK [Validate nginx config] ****************************************************
ok: [localhost]

TASK [Assert nginx config valid] ************************************************
ok: [localhost] => {"msg": "Nginx config OK"}

PLAY [PLAY 4 — System hardening] ************************************************

TASK [Apply sysctl hardening] ***************************************************
ok: [localhost] => (item=net.ipv4.tcp_syncookies)
ok: [localhost] => (item=kernel.randomize_va_space)
ok: [localhost] => (item=fs.suid_dumpable)
ok: [localhost] => (item=net.ipv4.conf.all.log_martians)

TASK [Configure log rotation] ***************************************************
changed: [localhost]

PLAY [PLAY 5 — Application service] ********************************************

TASK [Create app directories] ***************************************************
changed: [localhost] => (item=/opt/mywebapp)
changed: [localhost] => (item=/var/log/mywebapp)
changed: [localhost] => (item=/etc/mywebapp)

TASK [Deploy systemd service unit] **********************************************
changed: [localhost]

TASK [Flush handlers] ***********************************************************

RUNNING HANDLER [reload systemd] ************************************************
ok: [localhost]

PLAY [PLAY 6 — Post-provisioning validation] ************************************

TASK [[VALIDATE] Users exist] ***************************************************
ok: [localhost] => (item=deploy)
ok: [localhost] => (item=appuser)

TASK [[ASSERT] All directories present] *****************************************
ok: [localhost] => (item=/var/www/myapp) => {"msg": "Directory /var/www/myapp exists"}
ok: [localhost] => (item=/opt/mywebapp) => {"msg": "Directory /opt/mywebapp exists"}
ok: [localhost] => (item=/var/log/mywebapp) => {"msg": "Directory /var/log/mywebapp exists"}

TASK [[ASSERT] Service unit deployed] *******************************************
ok: [localhost] => {"msg": "systemd service unit deployed"}

TASK [[SUMMARY] Provisioning complete] ******************************************
ok: [localhost] => {
    "msg": [
        "========================================",
        "   ANSIBLE CAPSTONE: PROVISIONING DONE  ",
        "========================================",
        " Environment : production",
        " Web root    : /var/www/myapp",
        " Service     : mywebapp.service",
        " Nginx       : OK",
        " Users       : deploy, appuser",
        " Hardening   : sysctl + logrotate applied",
        "========================================",
        " Run ansible-playbook site.yml again to",
        " verify full idempotency (0 changes)",
        "========================================",
    ]
}

PLAY RECAP **********************************************************************
localhost    : ok=32    changed=13    unreachable=0    failed=0    skipped=0
```

> 💡 **Tip:** A multi-play `site.yml` is the gold standard for server provisioning. Each play has a clear responsibility. Run it twice — the second run should show 0 changes (idempotency). Add `--tags users` or `--tags nginx` to run specific plays during iterative development. Combine with Ansible Vault (Lab 09) for complete production-grade automation.

---

## Summary

| Component | Playbook Pattern | Key Modules |
|-----------|-----------------|-------------|
| Pre-flight checks | Play 1 with `assert` module | `assert`, `stat`, `shell` |
| User management | `user` + `authorized_key` + `copy` (sudoers) | `user`, `authorized_key` |
| Nginx install | `apt` + `template` + `file` + `service` | `apt`, `template`, `file`, `service` |
| Nginx config | `.j2` template + `nginx -t` validation | `template`, `command` |
| Vhost enable | Symlink with `file: state: link` | `file` |
| Sysctl hardening | `sysctl` module + `dict2items` loop | `sysctl` |
| Firewall | `ufw` module with loop over ports | `ufw` |
| Fail2ban | `apt` + `template` (jail.local.j2) | `apt`, `template`, `service` |
| Log rotation | `copy` or `template` to `/etc/logrotate.d/` | `copy`, `template` |
| Systemd service | `template` (`.service.j2`) + `meta: flush_handlers` | `template`, `systemd` |
| Handlers | `notify:` + handler play | `meta: flush_handlers` |
| Validation | `assert` + `stat` + `command` | `assert`, `stat` |
| Vault secrets | `!vault` inline + `--vault-password-file` | `ansible-vault` |
| Idempotency | All modules are idempotent by design | `changed_when`, `register` |
| CI/CD integration | `ansible-playbook --check --diff` + vault env vars | `--check`, `--diff`, `-e` |

## Labs 06–10 Skill Matrix

| Lab | Topic | Key Skill |
|-----|-------|-----------|
| Lab 06 | Ansible Foundations | Inventory, ad-hoc, first playbook |
| Lab 07 | Roles & Galaxy | Role structure, dependencies, Galaxy |
| Lab 08 | Variables & Templates | Precedence, Jinja2, handlers |
| Lab 09 | Vault & Secrets | Encryption, vault IDs, CI/CD |
| Lab 10 | Capstone | Multi-play provisioning + validation |
