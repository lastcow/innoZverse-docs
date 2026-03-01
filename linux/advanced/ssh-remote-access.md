# SSH & Remote Access

SSH (Secure Shell) lets you securely connect to and manage remote Linux systems.

## Basic SSH

```bash
ssh user@192.168.1.100              # Connect by IP
ssh user@hostname.com               # Connect by hostname
ssh -p 2222 user@server.com         # Custom port
ssh -i ~/.ssh/mykey.pem user@server # Use specific key
```

## SSH Key Authentication

```bash
# Generate key pair
ssh-keygen -t ed25519 -C "your@email.com"
# Creates: ~/.ssh/id_ed25519 (private) and ~/.ssh/id_ed25519.pub (public)

# Copy public key to server
ssh-copy-id user@server.com
# or manually:
cat ~/.ssh/id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

## SSH Config File

```bash
# ~/.ssh/config
Host myserver
    HostName 192.168.1.100
    User alice
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host prod
    HostName prod.example.com
    User deploy
    Port 10025
    IdentityFile ~/.ssh/prod_key
```

```bash
# Now just:
ssh myserver
ssh prod
```

## SSH Tunneling

```bash
# Local port forwarding (access remote service locally)
ssh -L 8080:localhost:80 user@server
# Now: http://localhost:8080 → server's port 80

# Remote port forwarding (expose local service remotely)
ssh -R 8080:localhost:3000 user@server

# SOCKS proxy
ssh -D 1080 user@server
```

## Securing SSH (sshd_config)

```bash
# /etc/ssh/sshd_config
PermitRootLogin no              # Disable root login
PasswordAuthentication no       # Keys only
Port 10025                      # Change default port
AllowUsers alice bob            # Whitelist users

# Apply changes
sudo systemctl restart sshd
```
