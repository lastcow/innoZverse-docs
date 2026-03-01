# Lab 6: SSH Tunneling

## 🎯 Objective
Understand SSH local, remote, and dynamic port forwarding to securely access services through encrypted tunnels.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Advanced Lab 3: SSH Key Generation
- Advanced Lab 4: SSH Configuration

## 🔬 Lab Instructions

### Step 1: Understand SSH Tunneling Concepts

SSH tunneling forwards network traffic through an encrypted SSH connection. Three types:

```bash
cat > /tmp/tunnel-types.txt << 'EOF'
SSH TUNNEL TYPES:

1. LOCAL PORT FORWARDING (-L)
   Access a remote service as if it's local
   
   ssh -L local_port:target_host:target_port user@ssh_server
   
   Example: Access a remote database
   ssh -L 5433:db.internal:5432 user@bastion.example.com
   
   Then connect to: localhost:5433
   (traffic goes: you -> bastion -> db.internal:5432)

2. REMOTE PORT FORWARDING (-R)
   Expose a local service to a remote server
   
   ssh -R remote_port:localhost:local_port user@ssh_server
   
   Example: Let remote server access your local webserver
   ssh -R 8080:localhost:3000 user@server.example.com
   
   Then access: server.example.com:8080
   (traffic goes: server:8080 -> you -> localhost:3000)

3. DYNAMIC PORT FORWARDING (-D)
   Create a SOCKS proxy through SSH
   
   ssh -D local_port user@ssh_server
   
   Example: Browse through a remote server
   ssh -D 1080 user@server.example.com
   
   Configure browser SOCKS proxy: localhost:1080
   (all traffic goes through server.example.com)
EOF

cat /tmp/tunnel-types.txt
```

### Step 2: Local Port Forwarding Examples

```bash
cat > /tmp/local-forward-examples.txt << 'EOF'
LOCAL FORWARDING USE CASES:

# 1. Database access through bastion
ssh -L 5433:db.internal:5432 -N -f user@bastion
# Connect: psql -h localhost -p 5433 -U dbuser mydb

# 2. Web interface on internal server
ssh -L 8080:internal-web:80 -N -f user@jump-host
# Open: http://localhost:8080

# 3. Redis access
ssh -L 6380:cache.internal:6379 -N -f user@bastion
# Connect: redis-cli -p 6380

FLAGS:
  -N  Don't execute remote command (forwarding only)
  -f  Go to background after authentication
  -L  Local port forwarding
  -g  Allow others on local network to use the tunnel

PERSISTENT TUNNEL in ~/.ssh/config:
  Host db-tunnel
      HostName bastion.example.com
      User zchen
      LocalForward 5433 db.internal:5432
      ServerAliveInterval 60
      ExitOnForwardFailure yes
EOF

cat /tmp/local-forward-examples.txt
```

### Step 3: Remote Port Forwarding Examples

```bash
cat > /tmp/remote-forward-examples.txt << 'EOF'
REMOTE FORWARDING USE CASES:

# 1. Expose local development server
ssh -R 8080:localhost:3000 user@server.example.com
# External users can access: server.example.com:8080

# 2. Reverse SSH (let server connect back to you)
# On your machine:
ssh -R 2222:localhost:22 user@server
# From server: ssh -p 2222 localhost

# 3. Share local file server
ssh -R 8000:localhost:8000 user@server
# Others can download from server:8000

SECURITY NOTE:
  On the remote server, GatewayPorts must be set
  in /etc/ssh/sshd_config to allow external access:
    GatewayPorts yes
  
  Without this, remote port is only accessible on
  the server's localhost (127.0.0.1)
EOF

cat /tmp/remote-forward-examples.txt
```

### Step 4: Dynamic Forwarding (SOCKS Proxy)

```bash
cat > /tmp/dynamic-forward-examples.txt << 'EOF'
DYNAMIC FORWARDING (SOCKS PROXY):

Create a SOCKS5 proxy tunnel:
  ssh -D 1080 -N -f user@server.example.com

Configure applications to use SOCKS5 proxy:
  Host: localhost
  Port: 1080
  Type: SOCKS5

Use with curl:
  curl --socks5 localhost:1080 https://internal-site.com

Use with applications that support SOCKS:
  - Firefox: Settings > Network > Manual proxy > SOCKS5
  - Chrome: --proxy-server="socks5://localhost:1080"
  - Git: git config --global http.proxy socks5://localhost:1080

Use in ~/.ssh/config:
  Host socks-proxy
      HostName server.example.com
      User zchen
      DynamicForward 1080
      ServerAliveInterval 30
EOF

cat /tmp/dynamic-forward-examples.txt
```

### Step 5: Test Local Tunnel to Localhost

```bash
# We can demonstrate tunneling concepts by connecting to local services
# Check what's listening locally
ss -tlnp | grep "127.0.0.1\|0.0.0.0" | head -10
```

```bash
# Show the SSH client configuration for a tunnel
ssh -G -L 8080:localhost:80 localhost 2>/dev/null | grep -E "^(localforward|hostname)" | head -5 || echo "SSH config shown above"
```

### Step 6: SSH Config for Tunnels

```bash
cat > /tmp/tunnel-ssh-config.txt << 'EOF'
# ~/.ssh/config entries for common tunnels

# Database tunnel through bastion
Host db-prod-tunnel
    HostName bastion.example.com
    User zchen
    LocalForward 15432 postgres.internal:5432
    LocalForward 16379 redis.internal:6379
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
    
# Usage:
# ssh -N db-prod-tunnel &
# psql -h localhost -p 15432 mydb
# redis-cli -p 16379

# Kubernetes dashboard tunnel
Host k8s-tunnel
    HostName k8s-master.internal
    User k8sadmin
    LocalForward 8001 127.0.0.1:8001
    ProxyJump bastion
EOF

cat /tmp/tunnel-ssh-config.txt
```

### Step 7: Persistent Tunnels with autossh

```bash
cat > /tmp/autossh-reference.txt << 'EOF'
AUTOSSH - Persistent Tunnels:

autossh automatically restarts SSH tunnels if they die.

Install: apt install autossh (requires sudo)

Usage:
  autossh -M 0 -N -L 5433:db.internal:5432 user@bastion

Or as a systemd user service:
  ~/.config/systemd/user/db-tunnel.service:

  [Unit]
  Description=Database SSH Tunnel
  
  [Service]
  ExecStart=/usr/bin/autossh -M 0 -N \
            -L 5433:db.internal:5432 \
            -o ServerAliveInterval=30 \
            user@bastion
  Restart=always
  
  [Install]
  WantedBy=default.target

  Enable: systemctl --user enable db-tunnel
  Start:  systemctl --user start db-tunnel
EOF

cat /tmp/autossh-reference.txt
```

## ✅ Verification

```bash
echo "=== Tunnel concept verification ==="
echo "Local forward syntax: ssh -L local_port:remote_host:remote_port user@ssh_server"
echo "Remote forward syntax: ssh -R remote_port:local_host:local_port user@ssh_server"
echo "Dynamic forward syntax: ssh -D local_port user@ssh_server"

echo ""
echo "=== Current listening ports (potential tunnel targets) ==="
ss -tlnp | head -10

rm /tmp/tunnel-types.txt /tmp/local-forward-examples.txt /tmp/remote-forward-examples.txt /tmp/dynamic-forward-examples.txt /tmp/tunnel-ssh-config.txt /tmp/autossh-reference.txt 2>/dev/null
echo "Advanced Lab 6 complete"
```

## 📝 Summary
- Local forwarding (`-L`): access a remote service as if it were local
- Remote forwarding (`-R`): expose a local service to a remote server
- Dynamic forwarding (`-D`): create a SOCKS proxy for all traffic
- `-N` prevents command execution (forwarding only); `-f` backgrounds the tunnel
- Define tunnels in `~/.ssh/config` with `LocalForward` and `RemoteForward`
- `autossh` or systemd user services keep tunnels alive automatically
