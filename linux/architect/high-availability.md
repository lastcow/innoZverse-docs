# High Availability & Clustering

## HA Architecture Principles

High availability systems target **99.9%+ uptime** through redundancy and failover.

```
                    [Load Balancer]
                    /             \
             [Node 1]           [Node 2]
          (Active)           (Standby/Active)
               \                /
            [Shared Storage / Replication]
```

## Keepalived — Virtual IP Failover

```bash
# /etc/keepalived/keepalived.conf (Master)
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 200
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass secretpassword
    }
    virtual_ipaddress {
        192.168.1.100/24    # Floating VIP
    }
    notify_master "/scripts/on-master.sh"
    notify_backup "/scripts/on-backup.sh"
}

# Backup node: state BACKUP, priority 100
```

## Linux Cluster with Pacemaker/Corosync

```bash
sudo apt install pacemaker corosync

# Configure cluster
pcs cluster auth node1 node2
pcs cluster setup --name mycluster node1 node2
pcs cluster start --all
pcs cluster enable --all

# Resources
pcs resource create virtual_ip ocf:heartbeat:IPaddr2 \
    ip=192.168.1.100 cidr_netmask=24 op monitor interval=30s

pcs resource create nginx systemd:nginx op monitor interval=30s

pcs constraint colocation add nginx with virtual_ip INFINITY
pcs constraint order virtual_ip then nginx
```

## Kernel Tuning for Production

```bash
# /etc/sysctl.conf

# Network performance
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# File descriptors
fs.file-max = 2097152

# Virtual memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Apply
sudo sysctl -p
```

## systemd Service Hardening

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=appuser
ExecStart=/usr/bin/myapp
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/myapp
CapabilityBoundingSet=
SystemCallFilter=@system-service

[Install]
WantedBy=multi-user.target
```
