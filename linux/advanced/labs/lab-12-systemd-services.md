# Lab 12: systemd Services

## 🎯 Objective
Manage services with `systemctl`, create a custom systemd service unit file, enable it at boot, and understand service dependencies.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access with sudo privileges
- Basic shell scripting knowledge

## 🔬 Lab Instructions

### Step 1: Basic systemctl Commands
```bash
# Check service status
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # status ssh
# ● ssh.service - OpenBSD Secure Shell server
#    Active: active (running) since ...
#    Main PID: 1234 (sshd)

# List all active services
systemctl list-units 2>/dev/null || echo "systemd not running (use on real host)" --type=service --state=active | head -20

# List failed services
systemctl --failed
```

### Step 2: Start, Stop, Restart Services
```bash
# Stop a service (be careful with critical services)
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # stop cron
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # status cron | grep Active
# Active: inactive (dead)

# Start it
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # start cron
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # status cron | grep Active
# Active: active (running)

# Restart (stop then start)
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # restart cron

# Reload (apply config changes without full restart)
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # reload ssh 2>/dev/null || systemctl 2>/dev/null || echo "(systemctl not available in container)"  # reload ssh || true
```

### Step 3: Enable and Disable Services at Boot
```bash
# Enable (start automatically at boot)
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # enable cron
# Created symlink /etc/systemd/system/multi-user.target.wants/cron.service

# Disable (don't start at boot)
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # disable bluetooth 2>/dev/null || true
# Removed /etc/systemd/system/bluetooth.target.wants/bluetooth.service

# Enable and start immediately
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # enable --now cron

# Check if enabled
systemctl is-enabled cron
# enabled
```

### Step 4: Understand Service Unit File Structure
```bash
# View an existing service file
cat /lib/systemd/system/cron.service
# [Unit]
# Description=Regular background program processing daemon
# Documentation=man:cron(8)
# After=remote-fs.target nss-user-lookup.target
#
# [Service]
# EnvironmentFile=-/etc/default/cron
# ExecStart=/usr/sbin/cron -f $EXTRA_OPTS
# IgnoreSIGPIPE=false
# KillMode=process
# Restart=on-failure
#
# [Install]
# WantedBy=multi-user.target
```

### Step 5: Create a Custom Script to Daemonize
```bash
# Create a simple service script
sudo mkdir -p /usr/local/bin
sudo tee /usr/local/bin/myapp.sh << 'EOF'
#!/bin/bash
LOG="/var/log/myapp.log"
echo "myapp started at $(date)" >> "$LOG"

while true; do
    echo "myapp heartbeat: $(date)" >> "$LOG"
    sleep 30
done
EOF
sudo chmod +x /usr/local/bin/myapp.sh
```

### Step 6: Create the systemd Unit File
```bash
sudo tee /etc/systemd/system/myapp.service << 'EOF'
[Unit]
Description=My Custom Application Service
Documentation=https://example.com/myapp
After=network.target
Wants=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/myapp.sh
Restart=on-failure
RestartSec=5s
StandardOutput=append:/var/log/myapp.log
StandardError=append:/var/log/myapp.log
TimeoutStopSec=30

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF
```

### Step 7: Enable and Start the Service
```bash
# Reload systemd to recognize the new unit
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # daemon-reload

# Enable and start
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # enable myapp.service
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # start myapp.service

# Check status
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # status myapp.service
# ● myapp.service - My Custom Application Service
#    Loaded: loaded (/etc/systemd/system/myapp.service; enabled)
#    Active: active (running) since ...
#    Main PID: 56789 (/usr/local/bin/myapp.sh)

sleep 5
cat /var/log/myapp.log
# myapp started at Sun Mar  1 06:01:00 UTC 2026
# myapp heartbeat: Sun Mar  1 06:01:00 UTC 2026
```

### Step 8: Service Types and Restart Policies
```bash
# [Service] Type= options:
cat << 'EOF'
Type=simple    - default, ExecStart is the main process
Type=forking   - process forks to background (traditional daemons)
Type=oneshot   - process runs once then exits
Type=notify    - process sends sd_notify() when ready
Type=idle      - like simple but waits for other jobs to complete

Restart= options:
Restart=always       - always restart (even on success)
Restart=on-failure   - restart only on non-zero exit/signal
Restart=on-abnormal  - restart on signal, timeout, or watchdog
Restart=no           - never restart (default)
EOF
```

### Step 9: Environment Variables in Services
```bash
sudo tee /etc/systemd/system/myapp-env.service << 'EOF'
[Unit]
Description=My App with Environment
After=network.target

[Service]
Type=simple
User=nobody
# Inline environment
Environment=APP_ENV=production
Environment=LOG_LEVEL=info
# From a file
EnvironmentFile=-/etc/myapp/env.conf
ExecStart=/bin/sh -c 'echo "ENV=$APP_ENV LEVEL=$LOG_LEVEL at $(date)" >> /tmp/myapp_env.log; sleep 60'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl 2>/dev/null || echo "(systemctl not available in container)"  # daemon-reload
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # start myapp-env.service
sleep 2
cat /tmp/myapp_env.log
# ENV=production LEVEL=info at Sun Mar  1 06:01:00 UTC 2026
```

### Step 10: Clean Up and Service Dependencies
```bash
# Stop and disable our test services
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # stop myapp.service myapp-env.service
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # disable myapp.service myapp-env.service

# Remove unit files
sudo rm -f /etc/systemd/system/myapp.service
sudo rm -f /etc/systemd/system/myapp-env.service
sudo rm -f /usr/local/bin/myapp.sh
sudo rm -f /var/log/myapp.log /tmp/myapp_env.log
systemctl 2>/dev/null || echo "(systemctl not available in container)"  # daemon-reload

# Show service dependency tree
systemctl list-dependencies ssh | head -15
# ssh.service
# ● ├─ system.slice
# ● └─ sysinit.target
```

## ✅ Verification
```bash
systemctl is-active ssh
# active

systemctl is-enabled cron
# enabled

systemctl list-units 2>/dev/null || echo "systemd not running (use on real host)" --type=service --state=failed
# (should be empty if all services healthy)
```

## 📝 Summary
- `systemctl start/stop/restart/reload SERVICE` manages service state
- `systemctl enable/disable SERVICE` controls boot-time startup
- Unit files in `/etc/systemd/system/` override system defaults
- `[Unit]` section: description, dependencies; `[Service]`: execution; `[Install]`: targets
- `After=` and `Wants=` define ordering and soft dependencies
- `Restart=on-failure` with `RestartSec=` provides automatic recovery
- Always run `systemctl daemon-reload` after modifying unit files
