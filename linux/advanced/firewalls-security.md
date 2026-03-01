# Firewalls & Security

## UFW (Uncomplicated Firewall)

```bash
sudo ufw status                     # Check status
sudo ufw enable                     # Enable firewall
sudo ufw disable                    # Disable firewall

# Allow/deny rules
sudo ufw allow 22                   # Allow SSH
sudo ufw allow 80/tcp               # Allow HTTP
sudo ufw allow 443/tcp              # Allow HTTPS
sudo ufw deny 3306                  # Deny MySQL from outside
sudo ufw allow from 192.168.1.0/24  # Allow local network

sudo ufw delete allow 80            # Remove a rule
sudo ufw reset                      # Reset all rules
```

## iptables (Advanced)

```bash
iptables -L -n -v                   # List all rules
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -j DROP           # Drop everything else
iptables-save > /etc/iptables.rules # Save rules
```

## Fail2ban — Brute Force Protection

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban --now

# Check status
sudo fail2ban-client status
sudo fail2ban-client status sshd

# Unban an IP
sudo fail2ban-client set sshd unbanip 192.168.1.50
```

## Security Hardening Checklist

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Check for world-writable files
find / -type f -perm -o+w 2>/dev/null

# Check listening services
ss -tlnp

# Check for SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Check user accounts
awk -F: '$3 == 0' /etc/passwd       # Find root-privileged accounts
last                                 # Recent logins
grep "Failed password" /var/log/auth.log | tail -20
```
