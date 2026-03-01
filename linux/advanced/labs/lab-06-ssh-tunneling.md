# Lab 6: SSH Tunneling

## 🎯 Objective
Create local port forwards, remote port forwards, and dynamic SOCKS proxies using SSH tunneling for secure access to restricted services.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- SSH key-based authentication configured (Lab 3)
- Basic understanding of TCP ports

## 🔬 Lab Instructions

### Step 1: Understand SSH Tunneling Concepts
```bash
# Three types of SSH tunnels:
#
# LOCAL (-L): Forward local port → remote service
#   ssh -L local_port:target_host:target_port user@ssh_host
#   Use case: Access a remote database from your local machine
#
# REMOTE (-R): Forward remote port → local service
#   ssh -R remote_port:local_host:local_port user@ssh_host
#   Use case: Expose your local dev server through a public host
#
# DYNAMIC (-D): SOCKS proxy for all traffic
#   ssh -D local_port user@ssh_host
#   Use case: Route browser traffic through a remote host

echo "Tunneling concepts reviewed"
```

### Step 2: Local Port Forward — Access Remote Service Locally
```bash
# Scenario: Remote database on port 5432, not exposed externally
# Forward localhost:15432 -> remote_host:5432 through ssh_host

# Command format:
# ssh -L 15432:db-internal:5432 ubuntu@ssh-gateway

# General example (no live remote needed for concept):
echo "Local forward example:"
echo "  ssh -L 8080:localhost:80 user@remote"
echo "  Then: curl http://localhost:8080"
echo "  Routes: your_machine:8080 -> remote:80"

# Test with local service
# Start a simple server
python3 -m http.server 9090 &
HTTP_PID=$!
sleep 1

# Connect via tunnel to localhost (self-referential demo)
curl -s http://localhost:9090 | head -5 || true
kill $HTTP_PID 2>/dev/null || true
```

### Step 3: Create a Local Tunnel (Self-Test)
```bash
# If SSH server is running locally, create a real tunnel
if systemctl is-active --quiet ssh 2>/dev/null || systemctl is-active --quiet sshd 2>/dev/null; then
    # Start a simple HTTP server on port 8181
    python3 -m http.server 8181 &
    HTTP_PID=$!
    sleep 1

    # Tunnel: local 8282 -> localhost:8181 through SSH
    ssh -f -N -L 8282:localhost:8181 \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        localhost
    sleep 1

    echo "Tunnel established. Testing..."
    curl -s http://localhost:8282 | head -3 || true

    # Cleanup
    kill $HTTP_PID 2>/dev/null || true
    pkill -f "ssh.*8282" 2>/dev/null || true
else
    echo "SSH server not running locally — test with a real remote host"
fi
```

### Step 4: Running Tunnels in Background
```bash
# -f: fork to background after authentication
# -N: don't execute remote command (tunnel only)
# -C: compress data through tunnel

# Background tunnel:
# ssh -fN -L 15432:db.internal:5432 ubuntu@bastion.example.com

# Kill background tunnels later:
# pkill -f "ssh.*15432"
# or find the PID:
# pgrep -a ssh | grep 15432

echo "Background tunnel flags: -f (fork) -N (no command) -C (compress)"
```

### Step 5: Remote Port Forward — Expose Local to Remote
```bash
# Scenario: You have a local web server on port 3000
# You want people to access it via public_server:8080

# Command:
# ssh -R 8080:localhost:3000 ubuntu@public-server.example.com

# Then on public-server, port 8080 forwards back to your local :3000
# (requires GatewayPorts yes in sshd_config for external access)

echo "Remote forward example:"
echo "  ssh -R 8080:localhost:3000 user@public-host"
echo "  Anyone on public-host can: curl http://localhost:8080"
echo "  Which proxies to: your_machine:3000"
```

### Step 6: Dynamic SOCKS Proxy
```bash
# Creates a SOCKS5 proxy on local port 1080
# All traffic through it routes via the remote SSH host

# Command:
# ssh -D 1080 -fN ubuntu@remote.example.com

# Use with:
# curl --socks5 localhost:1080 http://whatismyip.com
# Configure browser SOCKS proxy: localhost:1080

echo "Dynamic SOCKS example:"
echo "  ssh -D 1080 -fN user@remote"
echo "  curl --socks5 localhost:1080 http://ifconfig.me"
echo "  Shows remote host's IP address"
```

### Step 7: Persistent Tunnel with AutoSSH
```bash
sudo apt install -y autossh 2>/dev/null || true

# autossh monitors and restarts tunnels that die
# autossh -M 0 -f -N -L 15432:db:5432 ubuntu@bastion
# -M 0: disable monitoring port (use ServerAlive instead)

# Add to ~/.ssh/config:
cat >> ~/.ssh/config << 'EOF'

Host db-tunnel
    HostName bastion.example.com
    User ubuntu
    LocalForward 15432 db.internal:5432
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
EOF

# Then: autossh -M 0 -f -N db-tunnel
echo "autossh config added to ~/.ssh/config"
```

### Step 8: Tunnel Security Considerations
```bash
cat << 'EOF'
=== SSH Tunnel Security Notes ===

1. Authentication: Tunnels inherit SSH auth — use key-based auth
2. Firewall: Local tunnel binds to 127.0.0.1 by default (safe)
3. Remote forward binding: Use GatewayPorts carefully
4. Known hosts: Always verify SSH host keys
5. Audit: Check for unauthorized tunnels with:
   ss -tlnp | grep ssh
   ps aux | grep "ssh.*-[LRD]"

6. Restrict tunnels server-side in sshd_config:
   AllowTcpForwarding local   # only local forwards
   PermitTunnel no            # disable tun/tap tunnels
EOF
```

### Step 9: X11 Forwarding (GUI Apps over SSH)
```bash
# Run graphical applications on remote, display locally
# Requires X11 server on client (XQuartz on macOS, Xming on Windows)

# Connect with X11 forward:
# ssh -X ubuntu@remote "xeyes"   # or -Y for trusted forwarding

# Check if X11 forwarding is enabled on server:
grep -i x11 /etc/ssh/sshd_config || echo "Check /etc/ssh/sshd_config for X11Forwarding"
# X11Forwarding yes   (should be present)
```

### Step 10: List Active SSH Tunnels
```bash
cat > ~/list_tunnels.sh << 'EOF'
#!/bin/bash
echo "=== Active SSH Tunnels ==="
echo ""
echo "SSH processes with tunnel flags (-L -R -D):"
ps aux | grep -E 'ssh.*([ ]-[LRD])' | grep -v grep \
  | awk '{for(i=11;i<=NF;i++) printf $i " "; print ""}' \
  | sed 's/^ //' || echo "  None found"

echo ""
echo "Locally bound ports (non-system):"
ss -tlnp | awk 'NR>1 && $4 ~ /^127/ {print "  " $4}'
EOF
chmod +x ~/list_tunnels.sh
~/list_tunnels.sh
```

## ✅ Verification
```bash
# Verify SSH config has tunnel entry
grep -A5 'db-tunnel' ~/.ssh/config 2>/dev/null || echo "Config entry not found"

# Check no unwanted tunnels
ss -tlnp | grep -v ':22 ' | grep ssh || echo "No other SSH listening ports"
```

## 📝 Summary
- `-L local:host:remote` forwards a local port to a remote service through SSH
- `-R remote:host:local` exposes a local service through a remote host's port
- `-D port` creates a SOCKS5 proxy routing all traffic through the remote host
- `-fN` runs the tunnel in background without executing a command
- `autossh` monitors and restarts failed tunnels automatically
