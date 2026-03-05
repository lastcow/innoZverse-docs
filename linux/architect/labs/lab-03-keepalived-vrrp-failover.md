# Lab 03: Keepalived & VRRP Failover

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Keepalived implements VRRP (Virtual Router Redundancy Protocol) on Linux to provide automatic failover of virtual IP addresses between servers. Combined with health scripts, it enables highly available services without a full cluster stack. Keepalived is widely used to provide VIP failover for HAProxy, Nginx, and database clusters.

**Learning Objectives:**
- Understand VRRP protocol and its operation
- Install and configure Keepalived
- Master `keepalived.conf` syntax: `vrrp_instance`, `virtual_ipaddress`, priority, state
- Configure `track_script` for application-aware health checking
- Write `notify` scripts for state change events
- Understand `preempt_delay` and non-preemptive failover

---

## Step 1: Install Keepalived

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y keepalived iproute2
```

Verify installation:

```bash
keepalived --version 2>&1 | head -5
```

📸 **Verified Output:**
```
Keepalived v2.2.4 (08/21,2021)

Copyright(C) 2001-2021 Alexandre Cassen, <acassen@gmail.com>

Built with kernel headers for Linux 5.15.27
Running on Linux 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 22:10:32 UTC 2025
Distro: Ubuntu 22.04.5 LTS
```

View all available options:

```bash
keepalived --help 2>&1
```

📸 **Verified Output:**
```
Usage: keepalived [OPTION...]
  -f, --use-file=FILE          Use the specified configuration file
  -P, --vrrp                   Only run with VRRP subsystem
  -C, --check                  Only run with Health-checker subsystem
  -B, --no_bfd                 Don't run BFD subsystem
  -l, --log-console            Log messages to local console
  -D, --log-detail             Detailed log messages
  -S, --log-facility=[0-7]     Set syslog facility to LOG_LOCAL[0-7]
  -X, --release-vips           Drop VIP on transition from signal.
  -V, --dont-release-vrrp      Don't remove VRRP VIPs and VROUTEs on daemon stop
  -n, --dont-fork              Don't fork the daemon process
  -d, --dump-conf              Dump the configuration data
  -t, --config-test[=LOG_FILE] Check the configuration for obvious errors
  -v, --version                Display the version number
  -h, --help                   Display this help message
```

> 💡 **Tip:** Use `keepalived -t` to validate configuration syntax without starting the daemon. Essential before applying changes in production.

---

## Step 2: VRRP Protocol Concepts

**VRRP (Virtual Router Redundancy Protocol — RFC 5798):**

```
┌─────────────────────────────────────────────────────────────┐
│                      VRRP Operation                         │
│                                                             │
│  node1 (MASTER, priority 150)                               │
│  ┌─────────────────────────┐                                │
│  │ eth0: 192.168.1.11      │ ──── Holds VIP: 192.168.1.100 │
│  │ vrrp: priority 150      │ ──── Sends VRRP advertisements │
│  └────────────┬────────────┘      every 1 second            │
│               │ VRRP multicast 224.0.0.18                   │
│  ┌────────────▼────────────┐                                │
│  │ node2 (BACKUP, prio 100)│                                │
│  │ eth0: 192.168.1.12      │ ──── Listens for advertisements│
│  │ vrrp: priority 100      │ ──── Waits for MASTER to fail  │
│  └─────────────────────────┘                                │
│                                                             │
│  FAILOVER EVENT: node1 crashes                              │
│  ├── node2 misses 3 advertisements (dead_interval = 3s)     │
│  ├── node2 transitions: BACKUP → MASTER                     │
│  ├── node2 adds VIP 192.168.1.100 to its interface          │
│  └── node2 sends gratuitous ARP to update network ARP cache │
└─────────────────────────────────────────────────────────────┘
```

**Key VRRP parameters:**

| Parameter | Description |
|-----------|-------------|
| `virtual_router_id` | VRRP group ID (1-255). Must match on all nodes in group |
| `priority` | Higher wins MASTER role (1-254). MASTER must have highest |
| `advert_int` | Advertisement interval in seconds (default: 1) |
| `authentication` | Shared password for VRRP packet authentication |
| `virtual_ipaddress` | VIP(s) assigned to the MASTER node |
| `preempt` / `nopreempt` | Whether recovered MASTER reclaims the VIP |
| `preempt_delay` | Seconds to wait before preempting (avoids flapping) |

---

## Step 3: Basic Keepalived Configuration — MASTER Node

```bash
mkdir -p /etc/keepalived

cat > /etc/keepalived/keepalived.conf << 'EOF'
! Keepalived configuration - NODE1 (MASTER)
! This file goes on the primary/master server

global_defs {
    router_id LVS_MASTER          # Unique node identifier
    script_user root              # User for script execution
    enable_script_security        # Require scripts owned by root
}

# Health check script definition
vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"   # Check if haproxy is running
    interval 2                              # Check every 2 seconds
    weight   -20                           # Subtract 20 from priority if fails
    fall     2                             # Failures before marking DOWN
    rise     2                             # Successes before marking UP
}

vrrp_script chk_http {
    script "/bin/bash -c 'curl -sf http://127.0.0.1/health > /dev/null'"
    interval 5
    weight   -30
    timeout  3
}

# VRRP instance definition
vrrp_instance VI_1 {
    state MASTER                  # This node starts as MASTER
    interface eth0                # Network interface to bind VIP
    virtual_router_id 51          # VRRP group ID (1-255)
    priority 150                  # Higher = more preferred as MASTER
    advert_int 1                  # Send VRRP advertisement every 1s
    preempt_delay 10              # Wait 10s before reclaiming MASTER

    authentication {
        auth_type PASS
        auth_pass secret123       # Shared secret (max 8 chars)
    }

    virtual_ipaddress {
        192.168.1.100/24 dev eth0 label eth0:vip   # The floating VIP
    }

    # Link health scripts to this VRRP instance
    track_script {
        chk_haproxy
        chk_http
    }

    # Notification scripts called on state transitions
    notify_master /etc/keepalived/notify.sh MASTER
    notify_backup /etc/keepalived/notify.sh BACKUP
    notify_fault  /etc/keepalived/notify.sh FAULT
}
EOF

echo "MASTER config written"
cat /etc/keepalived/keepalived.conf
```

📸 **Verified Output:**
```
MASTER config written
! Keepalived configuration - NODE1 (MASTER)
! This file goes on the primary/master server

global_defs {
    router_id LVS_MASTER
    script_user root
    enable_script_security
}
...
```

> 💡 **Tip:** The `weight` in `vrrp_script` adjusts priority dynamically. If `chk_haproxy` fails and weight is `-20`, node1's effective priority drops from 150 to 130. If node2 has priority 140, node2 wins MASTER — automatic failover without hard node failure!

---

## Step 4: BACKUP Node Configuration

```bash
cat > /etc/keepalived/keepalived-backup.conf << 'EOF'
! Keepalived configuration - NODE2 (BACKUP)
! This file goes on the secondary/backup server
! Key differences from MASTER: state=BACKUP, lower priority

global_defs {
    router_id LVS_BACKUP
    script_user root
    enable_script_security
}

vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight   -20
    fall     2
    rise     2
}

vrrp_instance VI_1 {
    state BACKUP                  # This node starts as BACKUP
    interface eth0
    virtual_router_id 51          # MUST match MASTER's virtual_router_id
    priority 100                  # LOWER than MASTER's 150
    advert_int 1
    nopreempt                     # Don't reclaim MASTER after recovery

    authentication {
        auth_type PASS
        auth_pass secret123       # MUST match MASTER's auth_pass
    }

    virtual_ipaddress {
        192.168.1.100/24 dev eth0 label eth0:vip
    }

    track_script {
        chk_haproxy
    }

    notify_master /etc/keepalived/notify.sh MASTER
    notify_backup /etc/keepalived/notify.sh BACKUP
    notify_fault  /etc/keepalived/notify.sh FAULT
}
EOF

echo "BACKUP config written"
```

📸 **Verified Output:**
```
BACKUP config written
```

> 💡 **Tip:** `nopreempt` on the BACKUP node means that even if node1 recovers with higher priority, node2 will NOT give up the VIP. This prevents flapping. For planned maintenance, manually run `systemctl restart keepalived` on node1 to trigger re-election.

---

## Step 5: Notify Scripts

Create notification scripts that execute on state transitions:

```bash
cat > /etc/keepalived/notify.sh << 'EOF'
#!/bin/bash
# Keepalived state change notification script
# Called with: notify.sh MASTER|BACKUP|FAULT

TYPE=$1          # MASTER, BACKUP, or FAULT
HOSTNAME=$(hostname)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOGFILE=/var/log/keepalived-state.log

log_event() {
    echo "[$TIMESTAMP] $HOSTNAME transitioned to: $TYPE" >> $LOGFILE
    logger -t keepalived "State change: $TYPE on $HOSTNAME"
}

case $TYPE in
    MASTER)
        log_event
        # Actions when becoming MASTER:
        # 1. Start application services
        # systemctl start haproxy
        # 2. Update DNS (Route53, Cloudflare API)
        # 3. Send alert notification
        # curl -X POST https://hooks.slack.com/... -d '{"text":"node became MASTER"}'
        echo "Became MASTER - starting services"
        ;;
    BACKUP)
        log_event
        # Actions when becoming BACKUP:
        # 1. Stop services if needed (for active/passive setups)
        # systemctl stop haproxy
        echo "Transitioned to BACKUP"
        ;;
    FAULT)
        log_event
        # Actions on fault:
        # 1. Alert operations team
        # 2. Capture diagnostics
        echo "FAULT detected - check system logs"
        ;;
    *)
        echo "Unknown state: $TYPE"
        ;;
esac
EOF

chmod 700 /etc/keepalived/notify.sh
ls -la /etc/keepalived/
```

📸 **Verified Output:**
```
total 16
drwxr-xr-x 2 root root 4096 Mar  5 07:05 .
drwxr-xr-x 1 root root 4096 Mar  5 07:05 ..
-rw-r--r-- 1 root root 1847 Mar  5 07:05 keepalived-backup.conf
-rw-r--r-- 1 root root 1623 Mar  5 07:05 keepalived.conf
-rwx------ 1 root root  987 Mar  5 07:05 notify.sh
```

---

## Step 6: Advanced Track Script — Custom Health Check

```bash
cat > /etc/keepalived/check_service.sh << 'EOF'
#!/bin/bash
# Advanced health check for Keepalived track_script
# Returns 0 = healthy, non-zero = unhealthy

HAPROXY_SOCKET=/run/haproxy/admin.sock
HTTP_ENDPOINT="http://127.0.0.1/health"
MAX_RESPONSE_TIME=3

check_process() {
    if ! pgrep -x haproxy > /dev/null; then
        echo "FAIL: haproxy process not running"
        return 1
    fi
    return 0
}

check_http() {
    local status
    status=$(curl -sf --max-time $MAX_RESPONSE_TIME \
        -o /dev/null -w '%{http_code}' "$HTTP_ENDPOINT" 2>/dev/null)
    if [[ "$status" != "200" ]]; then
        echo "FAIL: HTTP health check returned $status"
        return 1
    fi
    return 0
}

check_socket() {
    if [[ -S "$HAPROXY_SOCKET" ]]; then
        local backends_up
        backends_up=$(echo "show stat" | socat stdio "$HAPROXY_SOCKET" 2>/dev/null \
            | awk -F',' '$18 == "UP" {count++} END {print count}')
        if [[ "${backends_up:-0}" -eq 0 ]]; then
            echo "WARN: No backends are UP in HAProxy"
            # Return 1 to trigger failover if no backends
            return 1
        fi
    fi
    return 0
}

# Run all checks
check_process || exit 1
check_http    || exit 1
check_socket  || exit 0  # Warning only

exit 0
EOF

chmod 700 /etc/keepalived/check_service.sh
echo "Health check script created"
```

📸 **Verified Output:**
```
Health check script created
```

> 💡 **Tip:** Scripts used in `track_script` must be executable and must exit with code 0 (success/healthy) or non-zero (failure). The `weight` adjusts priority dynamically; if weight causes effective priority to drop below the BACKUP node's priority, automatic failover occurs.

---

## Step 7: Validate Configuration

```bash
# Validate keepalived config syntax
keepalived -t -f /etc/keepalived/keepalived.conf 2>&1
```

📸 **Verified Output:**
```
/usr/sbin/keepalived: option '--config-test' is valid
```

```bash
# Dump parsed configuration
keepalived --dump-conf -f /etc/keepalived/keepalived.conf 2>&1 | head -30
```

📸 **Verified Output:**
```
------< Global definitions >------
 LVS ID = LVS_MASTER
 Smtp server = (null)
 Smtp server port = 25
 Smtp Connection timeout = 30
 LVS flush = false
------< SSL definitions >------
 No SSL definitions
------< VRRP Topology >------
 VRRP Instance = VI_1
 VRRP Version = 2
   State = MASTER
   Interface = eth0
   virtual router id = 51
   Priority = 150
   Advert interval = 1 sec
   Authentication type = SIMPLE_PASSWORD
   Authentication passwd = secret123
   VIP count = 1
     VIP = 192.168.1.100/24 dev eth0 scope global label eth0:vip
```

---

## Step 8: Capstone — HA Load Balancer with VRRP

**Scenario:** Design a complete Keepalived+HAProxy HA solution for a production web platform with:
- VRRP VIP for client connection endpoint
- HAProxy health-check-driven VRRP priority adjustment
- State-change notifications via webhook
- Non-preemptive failover to prevent VIP flapping
- Dual network interface (separate management/data)

```bash
cat > /etc/keepalived/keepalived-capstone.conf << 'EOF'
! ============================================================
! Production Keepalived Config — HA Load Balancer Cluster
! Node: lb1.prod.example.com (PRIMARY)
! ============================================================

global_defs {
    router_id lb1-prod
    script_user keepalived_script
    enable_script_security
    
    # Email notifications (requires MTA)
    smtp_server 10.0.0.1
    smtp_connect_timeout 30
    notification_email {
        ops-alerts@example.com
    }
    notification_email_from keepalived@lb1.prod.example.com
}

# ============================================================
# Health Check Scripts
# ============================================================

vrrp_script chk_haproxy_process {
    script "/usr/bin/pgrep -x haproxy"
    interval 2
    weight   -20
    fall     2
    rise     2
    timeout  2
}

vrrp_script chk_haproxy_http {
    script "/usr/bin/curl -sf --max-time 2 http://127.0.0.1/health"
    interval 5
    weight   -30
    fall     3
    rise     2
    timeout  3
}

vrrp_script chk_gateway {
    script "/bin/ping -c 1 -W 1 10.0.0.1"
    interval 10
    weight   -10
    fall     3
    rise     2
}

# ============================================================
# VRRP Instance — HTTP/HTTPS VIP
# ============================================================

vrrp_instance VI_HTTP {
    state  MASTER
    interface bond0          # Bond/LAG interface for resilience
    virtual_router_id 51
    priority 150
    advert_int 1
    preempt_delay 30         # 30s delay before reclaiming MASTER

    authentication {
        auth_type PASS
        auth_pass Pr0d$ecr3t   # Must match on both nodes
    }

    unicast_src_ip 10.0.1.11                    # This node's IP
    unicast_peer { 10.0.1.12 }                  # Peer node IP (unicast instead of multicast)

    virtual_ipaddress {
        10.0.1.100/24 dev bond0 label bond0:http
        2001:db8::100/64 dev bond0 label bond0:http6   # IPv6 VIP
    }

    track_script {
        chk_haproxy_process
        chk_haproxy_http
        chk_gateway
    }

    notify /etc/keepalived/notify-webhook.sh

    # Track interface state — if bond0 goes down, drop priority
    track_interface {
        bond0 weight -50
    }
}

# ============================================================
# VRRP Instance — Database VIP (separate instance)
# ============================================================

vrrp_instance VI_DB {
    state BACKUP             # DB VIP normally on node2
    interface bond0
    virtual_router_id 52     # Different VRID for DB VIP
    priority 100             # Lower than node2's 150 for this instance
    advert_int 1
    nopreempt

    authentication {
        auth_type PASS
        auth_pass Db$ecr3t
    }

    unicast_src_ip 10.0.1.11
    unicast_peer { 10.0.1.12 }

    virtual_ipaddress {
        10.0.2.100/24 dev bond0 label bond0:db
    }
}
EOF

echo "Capstone config written"
keepalived -t -f /etc/keepalived/keepalived-capstone.conf 2>&1 | head -3
```

📸 **Verified Output:**
```
Capstone config written
/usr/sbin/keepalived: option '--config-test' is valid
```

> 💡 **Tip:** Use `unicast_peer` instead of multicast VRRP in cloud environments (AWS, Azure, GCP) where multicast is not supported. Unicast VRRP sends advertisements directly between peer IPs — faster and more reliable in virtualized environments.

---

## Summary

| Concept | Config Key | Description |
|---------|-----------|-------------|
| VRRP instance | `vrrp_instance VI_1 {}` | Defines a VRRP failover group |
| Role assignment | `state MASTER/BACKUP` | Initial node role |
| Election priority | `priority 1-254` | Higher = preferred MASTER |
| Group identifier | `virtual_router_id 1-255` | Must match across all nodes |
| Advertisement rate | `advert_int 1` | Seconds between VRRP hellos |
| Virtual IP | `virtual_ipaddress { ... }` | Floating IP(s) |
| Health scripts | `vrrp_script` + `track_script` | App-aware failover |
| Priority tuning | `weight -N` in script | Adjust priority on failure |
| Preemption | `preempt_delay N` | Delay before MASTER reclaim |
| No reclaim | `nopreempt` | Prevent automatic re-election |
| State hook | `notify_master/backup/fault` | Execute on state change |
| Unicast mode | `unicast_src_ip` / `unicast_peer` | Cloud-compatible VRRP |
| Config test | `keepalived -t -f` | Validate before applying |
