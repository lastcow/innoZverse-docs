# Ansible Automation

Ansible automates configuration management, application deployment, and task execution across many servers simultaneously.

## Key Concepts

- **Inventory** — List of hosts to manage
- **Playbook** — YAML file with automation tasks
- **Role** — Reusable collection of tasks
- **Module** — Built-in functionality (apt, copy, service, etc.)

## Inventory

```ini
# inventory.ini
[webservers]
web1.example.com
web2.example.com ansible_user=ubuntu

[databases]
db1.example.com ansible_port=2222

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

## Basic Playbook

```yaml
# setup-webserver.yml
---
- name: Configure web servers
  hosts: webservers
  become: yes           # sudo

  vars:
    app_user: www-data
    app_dir: /var/www/myapp

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install Nginx
      apt:
        name: nginx
        state: present

    - name: Start and enable Nginx
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Copy config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: Restart Nginx

  handlers:
    - name: Restart Nginx
      service:
        name: nginx
        state: restarted
```

## Running Playbooks

```bash
ansible-playbook -i inventory.ini setup-webserver.yml
ansible-playbook -i inventory.ini setup-webserver.yml --check   # Dry run
ansible-playbook -i inventory.ini setup-webserver.yml -v        # Verbose
ansible all -i inventory.ini -m ping                            # Test connectivity
```
