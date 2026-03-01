# System Administration

Core skills for managing Linux systems in production environments.

## Process Management

```bash
ps aux              # List all running processes
top                 # Interactive process viewer
htop                # Enhanced process viewer (install separately)
kill 1234           # Kill process by PID
killall nginx       # Kill all processes named nginx
pkill -f "python"   # Kill by pattern
```

## Service Management (systemd)

```bash
systemctl status nginx      # Check service status
systemctl start nginx       # Start service
systemctl stop nginx        # Stop service
systemctl restart nginx     # Restart service
systemctl enable nginx      # Start on boot
systemctl disable nginx     # Disable on boot
journalctl -u nginx         # View service logs
```

## Disk Management

```bash
df -h               # Disk space usage
du -sh /var/log/    # Directory size
lsblk               # List block devices
mount /dev/sdb1 /mnt/disk   # Mount device
umount /mnt/disk    # Unmount device
```

## User Management

```bash
useradd -m alice            # Create user with home dir
passwd alice                # Set password
usermod -aG sudo alice      # Add to sudo group
userdel -r alice            # Delete user and home dir
id alice                    # Show user info
```

## Package Management

```bash
# Ubuntu/Debian
apt update && apt upgrade -y
apt install nginx
apt remove nginx

# CentOS/RHEL
yum update
yum install nginx
dnf install nginx   # Modern RHEL
```

## Networking

```bash
ip addr show        # Show IP addresses
ip route show       # Show routing table
ss -tlnp            # Show listening ports
curl ifconfig.me    # Get public IP
ping google.com     # Test connectivity
```
