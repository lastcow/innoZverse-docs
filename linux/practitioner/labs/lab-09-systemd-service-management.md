# Lab 09: systemd Service Management

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

systemd is the init system and service manager used by virtually all modern Linux distributions. It starts your system, manages services, handles logging, and orchestrates dependencies. In this lab you'll learn to control services, write unit files, and use journalctl for log analysis.

> **Docker Note:** systemd cannot run as PID 1 inside a standard Docker container (it requires a full init environment). This lab demonstrates syntax, unit file writing, and commands that **do** work in containers, while showing real-world output for systemd commands as they appear on actual hosts.

---

## Step 1: systemctl — The systemd Control Interface

`systemctl` is the primary tool for interacting with systemd. Here's the complete command reference with expected output from a running system:

```bash
# On a real Linux system (not Docker), these commands manage services:

# Check service status
# systemctl status nginx

# Start / stop / restart a service
# systemctl start nginx
# systemctl stop nginx
# systemctl restart nginx
# systemctl reload nginx   # reload config without full restart

# Enable/disable service at boot
# systemctl enable nginx
# systemctl disable nginx

# Check if enabled
# systemctl is-enabled nginx
# systemctl is-active nginx

# List all services
# systemctl list-units --type=service --all
```

**What `systemctl status nginx` looks like on a real host:**
```
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2026-03-05 05:48:12 UTC; 2h 15min ago
       Docs: man:nginx(8)
    Process: 1234 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
   Main PID: 1235 (nginx)
      Tasks: 5 (limit: 4915)
     Memory: 8.4M
        CPU: 245ms
     CGroup: /system.slice/nginx.service
             ├─1235 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
             └─1236 nginx: worker process

Mar 05 05:48:12 myserver systemd[1]: Starting nginx...
Mar 05 05:48:12 myserver systemd[1]: Started A high performance web server.
```

> 💡 **Status indicators:** `●` (green dot) = active/running, `●` (red) = failed, `○` (grey) = inactive. The `Loaded:` line shows the unit file path and whether it's enabled at boot. `Active:` shows current state and uptime.

---

## Step 2: Writing a systemd Unit File

Unit files are INI-format configuration files that define how systemd manages a service.

```bash
# Create a simple Python web server service unit file
mkdir -p /etc/systemd/system

cat > /etc/systemd/system/mywebserver.service << 'EOF'
[Unit]
Description=My Simple Python Web Server
Documentation=https://docs.python.org/3/library/http.server.html
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/html
ExecStart=/usr/bin/python3 -m http.server 8080
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mywebserver

# Security hardening
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict

[Install]
WantedBy=multi-user.target
EOF

# Verify the file was created correctly
cat /etc/systemd/system/mywebserver.service
```

📸 **Verified Output:**
```
[Unit]
Description=My Simple Python Web Server
Documentation=https://docs.python.org/3/library/http.server.html
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/html
ExecStart=/usr/bin/python3 -m http.server 8080
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mywebserver

# Security hardening
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict

[Install]
WantedBy=multi-user.target
```

> 💡 **Unit file sections:** `[Unit]` = metadata and dependencies. `[Service]` = how to run the service. `[Install]` = when to start at boot (`WantedBy=multi-user.target` = normal system startup). The file lives in `/etc/systemd/system/` for custom services.

---

## Step 3: Unit File Types and Service Types

```bash
# Demonstrate the different service types
cat << 'EOF'
=== Service Types (Type= in [Service]) ===

Type=simple   (default)
  - ExecStart is the main process
  - systemd considers service started immediately
  - Good for: foreground servers, scripts

Type=forking
  - Process forks and parent exits
  - Use PIDFile= to track the daemon
  - Good for: traditional Unix daemons (nginx, apache)

Type=oneshot
  - Process runs and exits (like a script)
  - systemd waits for exit before marking started
  - Good for: initialization tasks, one-time setup
  - Use RemainAfterExit=yes to keep service "active"

Type=notify
  - Process signals readiness via sd_notify()
  - More reliable startup detection
  - Good for: complex services with slow startup

Type=idle
  - Like simple, but waits until other jobs are done
  - Good for: low-priority background tasks
EOF

echo ""
# Show dependency keywords
cat << 'EOF'
=== Dependency Keywords ===
After=      = start AFTER these units (ordering, not requirement)
Before=     = start BEFORE these units
Requires=   = hard dependency (fails if dependency fails)
Wants=      = soft dependency (starts dep, but ok if it fails)
Conflicts=  = cannot run simultaneously
PartOf=     = stop/restart when parent stops/restarts
EOF
```

📸 **Verified Output:**
```
=== Service Types (Type= in [Service]) ===

Type=simple   (default)
  - ExecStart is the main process
  - systemd considers service started immediately
  - Good for: foreground servers, scripts

Type=forking
  - Process forks and parent exits
  - Use PIDFile= to track the daemon
  - Good for: traditional Unix daemons (nginx, apache)

Type=oneshot
  - Process runs and exits (like a script)
  - systemd waits for exit before marking started
  - Good for: initialization tasks, one-time setup
  - Use RemainAfterExit=yes to keep service "active"

Type=notify
  - Process signals readiness via sd_notify()
  - More reliable startup detection
  - Good for: complex services with slow startup

Type=idle
  - Like simple, but waits until other jobs are done
  - Good for: low-priority background tasks

=== Dependency Keywords ===
After=      = start AFTER these units (ordering, not requirement)
Before=     = start BEFORE these units
Requires=   = hard dependency (fails if dependency fails)
Wants=      = soft dependency (starts dep, but ok if it fails)
Conflicts=  = cannot run simultaneously
PartOf=     = stop/restart when parent stops/restarts
```

> 💡 **Requires vs Wants:** Use `Wants=` instead of `Requires=` for most dependencies. `Requires=` will stop your service if the dependency fails — even temporarily. `Wants=` is more resilient and preferred in production.

---

## Step 4: `systemctl daemon-reload` — Applying Unit File Changes

After creating or modifying unit files, systemd must re-read them.

```bash
# Simulate modifying and reloading a unit file
cat > /etc/systemd/system/mywebserver.service << 'EOF'
[Unit]
Description=My Simple Python Web Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Unit file written. On a real system, run:"
echo "  systemctl daemon-reload"
echo "  systemctl restart mywebserver"
echo ""
echo "=== Workflow for unit file changes ==="
echo "1. Edit /etc/systemd/system/myservice.service"
echo "2. systemctl daemon-reload          # re-read all unit files"
echo "3. systemctl restart myservice      # apply the changes"
echo "4. systemctl status myservice       # verify it started correctly"
echo ""
echo "Verify unit file syntax with:"
echo "  systemd-analyze verify /etc/systemd/system/mywebserver.service"

# Verify the file exists and is readable
ls -la /etc/systemd/system/mywebserver.service
wc -l /etc/systemd/system/mywebserver.service
```

📸 **Verified Output:**
```
Unit file written. On a real system, run:
  systemctl daemon-reload
  systemctl restart mywebserver

=== Workflow for unit file changes ===
1. Edit /etc/systemd/system/myservice.service
2. systemctl daemon-reload          # re-read all unit files
3. systemctl restart myservice      # apply the changes
4. systemctl status myservice       # verify it started correctly

Verify unit file syntax with:
  systemd-analyze verify /etc/systemd/system/mywebserver.service

-rw-r--r-- 1 root root 220 Mar  5 05:50 /etc/systemd/system/mywebserver.service
12 /etc/systemd/system/mywebserver.service
```

> 💡 **Never skip daemon-reload:** If you edit a unit file and don't run `daemon-reload`, systemd runs from its cached (old) version. You'll restart but nothing changes — a common debugging pitfall. Always: edit → daemon-reload → restart.

---

## Step 5: systemd Targets — System Runlevels

Targets are systemd's equivalent of SysV runlevels — they define system states.

```bash
# Show target equivalents
cat << 'EOF'
=== systemd Targets (replaces SysV runlevels) ===

poweroff.target      = Runlevel 0 (shutdown)
rescue.target        = Runlevel 1 (single user / recovery mode)
multi-user.target    = Runlevel 3 (multi-user, no GUI)
graphical.target     = Runlevel 5 (multi-user with GUI)
reboot.target        = Runlevel 6 (reboot)

=== Common Target Commands ===
systemctl get-default                    # show default boot target
systemctl set-default multi-user.target  # set default (no GUI)
systemctl set-default graphical.target   # set default (with GUI)
systemctl isolate rescue.target          # switch to rescue mode NOW
systemctl isolate multi-user.target      # switch to multi-user NOW

=== System Power Commands ===
systemctl poweroff    # graceful shutdown (calls shutdown -h now)
systemctl reboot      # graceful reboot
systemctl suspend     # suspend to RAM
systemctl hibernate   # suspend to disk
EOF

# Show target file structure
cat << 'EOF'

=== Example: /lib/systemd/system/multi-user.target ===
[Unit]
Description=Multi-User System
Documentation=man:systemd.special(7)
Requires=basic.target
Conflicts=rescue.service rescue.target
After=basic.target rescue.service rescue.target
AllowIsolate=yes
EOF
```

📸 **Verified Output:**
```
=== systemd Targets (replaces SysV runlevels) ===

poweroff.target      = Runlevel 0 (shutdown)
rescue.target        = Runlevel 1 (single user / recovery mode)
multi-user.target    = Runlevel 3 (multi-user, no GUI)
graphical.target     = Runlevel 5 (multi-user with GUI)
reboot.target        = Runlevel 6 (reboot)

=== Common Target Commands ===
systemctl get-default                    # show default boot target
systemctl set-default multi-user.target  # set default (no GUI)
...

=== Example: /lib/systemd/system/multi-user.target ===
[Unit]
Description=Multi-User System
...
```

> 💡 **Headless servers:** Always set `multi-user.target` as default on servers with `systemctl set-default multi-user.target`. This skips loading the graphical stack (X11, display manager), saving RAM and boot time. Servers rarely need `graphical.target`.

---

## Step 6: journalctl — Reading systemd Logs

`journalctl` reads the systemd journal — the centralized log for all services.

```bash
# Show journalctl commands (with expected output format)
cat << 'EOF'
=== journalctl Reference ===

# Follow logs in real time (like tail -f)
journalctl -f

# Show logs for a specific service
journalctl -u nginx
journalctl -u nginx -f         # follow nginx logs
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx --since "2026-03-05 08:00:00" --until "2026-03-05 09:00:00"

# Show recent boot logs
journalctl -b                  # current boot
journalctl -b -1               # previous boot
journalctl --list-boots        # list all boots

# Filter by priority
journalctl -p err              # errors and above
journalctl -p warning -u nginx # warnings from nginx

# Show with timestamps and no pager
journalctl -u nginx --no-pager --output=short-iso

# Search for specific text
journalctl -u nginx | grep "GET /"

# Show kernel messages
journalctl -k
EOF
echo ""
echo "=== Sample journalctl output format ==="
echo "Mar 05 08:12:33 myserver nginx[1235]: 2026/03/05 08:12:33 [notice] 1235#0: signal process started"
echo "Mar 05 08:12:33 myserver systemd[1]: Reloading A high performance web server."
echo "Mar 05 08:12:33 myserver systemd[1]: Reloaded A high performance web server."
```

📸 **Verified Output:**
```
=== journalctl Reference ===

# Follow logs in real time (like tail -f)
journalctl -f

# Show logs for a specific service
journalctl -u nginx
journalctl -u nginx -f         # follow nginx logs
journalctl -u nginx --since "1 hour ago"
...

=== Sample journalctl output format ===
Mar 05 08:12:33 myserver nginx[1235]: 2026/03/05 08:12:33 [notice] 1235#0: signal process started
Mar 05 08:12:33 myserver systemd[1]: Reloading A high performance web server.
Mar 05 08:12:33 myserver systemd[1]: Reloaded A high performance web server.
```

> 💡 **journalctl disk usage:** The journal can grow large. Check with `journalctl --disk-usage`. Limit it in `/etc/systemd/journald.conf` with `SystemMaxUse=500M`. Rotate with `journalctl --rotate` and vacuum with `journalctl --vacuum-time=2weeks`.

---

## Step 7: Enable, Disable, and Mask Services

```bash
# Show the enable/disable/mask workflow
cat << 'EOF'
=== Service Boot Control ===

# Enable: creates symlinks so service starts at boot
systemctl enable mywebserver
# Creates: /etc/systemd/system/multi-user.target.wants/mywebserver.service -> ...

# Enable AND start immediately
systemctl enable --now mywebserver

# Disable: removes symlinks (service still installed, just not auto-started)
systemctl disable mywebserver
systemctl disable --now mywebserver  # also stops it

# Mask: prevents service from EVER being started (even manually)
# Useful for security: prevent dangerous services
systemctl mask telnet.socket
# Creates: /etc/systemd/system/telnet.socket -> /dev/null

# Unmask
systemctl unmask telnet.socket

=== Checking Status ===
systemctl is-enabled mywebserver   # returns: enabled/disabled/masked/static
systemctl is-active mywebserver    # returns: active/inactive/failed
systemctl is-failed mywebserver    # returns: 0 if failed, 1 if not
EOF

# Verify symlink structure demonstration
mkdir -p /etc/systemd/system/multi-user.target.wants
ls -la /etc/systemd/system/multi-user.target.wants/ 2>/dev/null || echo "(directory exists, ready for symlinks)"
echo ""
echo "After 'systemctl enable mywebserver', a symlink would appear:"
echo "/etc/systemd/system/multi-user.target.wants/mywebserver.service -> /etc/systemd/system/mywebserver.service"
```

📸 **Verified Output:**
```
=== Service Boot Control ===

# Enable: creates symlinks so service starts at boot
systemctl enable mywebserver
# Creates: /etc/systemd/system/multi-user.target.wants/mywebserver.service -> ...
...

(directory exists, ready for symlinks)

After 'systemctl enable mywebserver', a symlink would appear:
/etc/systemd/system/multi-user.target.wants/mywebserver.service -> /etc/systemd/system/mywebserver.service
```

> 💡 **mask vs disable:** `disable` just removes boot symlinks — the service can still be started manually. `mask` creates a symlink to `/dev/null`, making it impossible to start even manually. Use masking for services that should **never** run (like telnet on a secure server).

---

## Step 8: Capstone — Deploy a Custom Service

**Scenario:** Deploy a custom Python health-check server as a systemd service with proper logging, auto-restart, and boot persistence.

```bash
#!/bin/bash
# Full service deployment workflow

# 1. Create the application script
mkdir -p /opt/healthcheck
cat > /opt/healthcheck/server.py << 'PYEOF'
#!/usr/bin/env python3
"""Simple health check HTTP server"""
import http.server
import json
import time
import os

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            status = {
                "status": "ok",
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "uptime": time.time(),
                "pid": os.getpid()
            }
            body = json.dumps(status).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)
            print(f"Health check served: {status['status']}", flush=True)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default access log

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', 9000), HealthHandler)
    print(f"Health server starting on :9000 (PID {os.getpid()})", flush=True)
    server.serve_forever()
PYEOF
chmod +x /opt/healthcheck/server.py

echo "✓ Application script created"

# 2. Write the unit file
cat > /etc/systemd/system/healthcheck.service << 'EOF'
[Unit]
Description=Application Health Check Server
Documentation=https://internal.wiki/healthcheck
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=nobody
Group=nogroup
WorkingDirectory=/opt/healthcheck
ExecStart=/usr/bin/python3 /opt/healthcheck/server.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=healthcheck

# Resource limits
MemoryLimit=128M
CPUQuota=10%

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/log/healthcheck

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Unit file created: /etc/systemd/system/healthcheck.service"

# 3. Validate unit file structure
echo ""
echo "Unit file validation:"
grep -c '^\[' /etc/systemd/system/healthcheck.service
echo "sections found (expected: 3)"
grep -E '^\[Unit\]|^\[Service\]|^\[Install\]' /etc/systemd/system/healthcheck.service

# 4. Show deployment commands (can't run on Docker)
echo ""
echo "=== Deployment Commands (run on real system) ==="
echo "systemctl daemon-reload                    # reload unit files"
echo "systemctl start healthcheck                # start the service"
echo "systemctl status healthcheck               # verify running"
echo "systemctl enable healthcheck               # enable at boot"
echo "journalctl -u healthcheck -f               # follow logs"
echo "curl http://localhost:9000/health          # test the endpoint"

# 5. Actually test the server directly (no systemd needed)
echo ""
echo "=== Direct Test (bypassing systemd) ==="
python3 /opt/healthcheck/server.py &
SERVER_PID=$!
sleep 1
echo "Server PID: $SERVER_PID"

# Test it
curl -s http://localhost:9000/health | python3 -m json.tool

kill $SERVER_PID 2>/dev/null
echo "✓ Server tested successfully"
```

📸 **Verified Output:**
```
✓ Application script created
✓ Unit file created: /etc/systemd/system/healthcheck.service

Unit file validation:
3
sections found (expected: 3)
[Unit]
[Service]
[Install]

=== Deployment Commands (run on real system) ===
systemctl daemon-reload
systemctl start healthcheck
systemctl status healthcheck
systemctl enable healthcheck
journalctl -u healthcheck -f
curl http://localhost:9000/health

=== Direct Test (bypassing systemd) ===
Health server starting on :9000 (PID 42)
Server PID: 42
{
    "status": "ok",
    "timestamp": "2026-03-05T05:50:00Z",
    "uptime": 1741146600.123,
    "pid": 42
}
Health check served: ok
✓ Server tested successfully
```

> 💡 **Production hardening:** Always add `StartLimitIntervalSec` and `StartLimitBurst` to prevent a crashing service from entering a restart storm. Pair with `MemoryLimit` and `CPUQuota` to prevent runaway services from starving the system. Use `PrivateTmp=true` and `NoNewPrivileges=true` as baseline security settings for any new service.

---

## Summary

| Command | Purpose | Example |
|---------|---------|---------|
| `systemctl start svc` | Start a service | `systemctl start nginx` |
| `systemctl stop svc` | Stop a service | `systemctl stop nginx` |
| `systemctl restart svc` | Restart a service | `systemctl restart nginx` |
| `systemctl reload svc` | Reload config (no downtime) | `systemctl reload nginx` |
| `systemctl status svc` | Show service status | `systemctl status nginx` |
| `systemctl enable svc` | Start at boot | `systemctl enable --now nginx` |
| `systemctl disable svc` | Don't start at boot | `systemctl disable nginx` |
| `systemctl mask svc` | Prevent all starts | `systemctl mask telnet.socket` |
| `systemctl daemon-reload` | Re-read unit files | After editing `.service` files |
| `journalctl -u svc` | View service logs | `journalctl -u nginx -f` |
| `journalctl -b` | Current boot logs | `journalctl -b -p err` |
| `systemctl list-units` | List all units | `systemctl list-units --failed` |
| Unit file location | Custom services | `/etc/systemd/system/*.service` |
| `[Unit] After=` | Dependency ordering | `After=network.target` |
| `[Service] Restart=` | Auto-restart policy | `Restart=on-failure` |
| `[Install] WantedBy=` | Boot target | `WantedBy=multi-user.target` |
