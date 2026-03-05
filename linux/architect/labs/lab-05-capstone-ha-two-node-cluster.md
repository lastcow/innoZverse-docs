# Lab 05: Capstone — HA Two-Node Cluster Blueprint

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

This capstone lab brings together everything from Labs 01–04 into a complete, production-ready two-node High Availability cluster blueprint. You will design and document the full configuration: Corosync messaging, Pacemaker cluster properties, Virtual IP resource, HAProxy as a cluster resource, health check scripts, failover testing procedures, monitoring, and generate a complete operational runbook.

**Learning Objectives:**
- Integrate Corosync + Pacemaker + HAProxy + Keepalived concepts
- Write production-grade cluster configurations
- Design comprehensive health check scripts
- Create failover testing procedures
- Set up monitoring with crm_mon
- Generate an operational runbook document

---

## Step 1: Install the Complete HA Stack

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    pacemaker corosync pcs \
    haproxy keepalived \
    python3 curl iproute2 \
    2>/dev/null

echo "=== Installed versions ==="
echo -n "Pacemaker: "; pacemakerd --version 2>&1 | head -1
echo -n "Corosync: "; corosync -v 2>&1 | head -1
echo -n "HAProxy: "; haproxy -v 2>&1 | head -1
echo -n "Keepalived: "; keepalived --version 2>&1 | head -1
pcs --version
```

📸 **Verified Output:**
```
=== Installed versions ===
Pacemaker: Pacemaker 2.1.2
Corosync: Corosync Cluster Engine, version '3.1.6'
HAProxy: HAProxy version 2.4.30-0ubuntu0.22.04.1 2025/12/03
Keepalived: Keepalived v2.2.4 (08/21,2021)
0.10.11
```

> 💡 **Tip:** In production, always verify package versions match between nodes before forming a cluster. Mixed Pacemaker versions can cause CIB schema compatibility issues.

---

## Step 2: Corosync Configuration

The foundation of any Pacemaker cluster is the Corosync messaging layer. Here is the production configuration:

```bash
mkdir -p /etc/corosync

cat > /etc/corosync/corosync.conf << 'EOF'
# ============================================================
# Corosync Cluster Configuration
# Cluster: prod-ha-cluster
# Nodes: node1.prod.example.com (10.0.1.11)
#         node2.prod.example.com (10.0.1.12)
# ============================================================

system {
    # Required for containerized/unprivileged environments
    allow_knet_handle_fallback: yes
}

totem {
    version:            2
    cluster_name:       prod-ha-cluster
    transport:          knet            # Modern transport (replaces udpu)

    # Encryption (require corosync-keygen to generate /etc/corosync/authkey)
    crypto_cipher:      aes256
    crypto_hash:        sha256

    # Heartbeat timing
    token:              3000            # Token timeout (ms) — node declared dead
    token_retransmits_before_loss_const: 10
    join:               60             # Join timeout (ms)
    consensus:          3600           # Consensus timeout (ms)
    max_messages:       20             # Max messages per token rotation

    # Redundant ring (second network for cluster heartbeat)
    link_mode:          passive        # Active: use all links; Passive: failover
}

logging {
    fileline:           off
    to_stderr:          no
    to_logfile:         yes
    logfile:            /var/log/corosync/corosync.log
    to_syslog:          yes
    timestamp:          on
    debug:              off
    logger_subsys {
        subsys:         QUORUM
        debug:          off
    }
}

quorum {
    provider:               corosync_votequorum
    two_node:               1              # Enable two-node cluster mode
    # Optional: Add quorum device for tie-breaking
    # device { model: net; net { host: qdevice.prod.example.com; } }
}

nodelist {
    node {
        name:           node1
        nodeid:         1
        ring0_addr:     10.0.1.11      # Primary cluster network
        ring1_addr:     192.168.100.11 # Secondary cluster network (redundancy)
    }
    node {
        name:           node2
        nodeid:         2
        ring0_addr:     10.0.1.12
        ring1_addr:     192.168.100.12
    }
}
EOF

echo "Corosync config written"
cat /etc/corosync/corosync.conf
```

📸 **Verified Output:**
```
Corosync config written
# ============================================================
# Corosync Cluster Configuration
# Cluster: prod-ha-cluster
...
```

> 💡 **Tip:** Always use `ring1_addr` for a second cluster heartbeat network. If ring0 fails, Corosync fails over to ring1, preventing a false node failure declaration. Use a dedicated VLAN for cluster heartbeat traffic.

---

## Step 3: Pacemaker Cluster Properties

```bash
# Show current pcs cluster property options
pcs property --help 2>&1 | head -25
```

📸 **Verified Output:**
```
Usage: pcs property [commands]...
Configure pacemaker properties

Commands:
    [config [<property>]... | --all | --defaults]
        Show values of cib properties, all properties, or only properties
        with default values.

    describe [--all] [<property>]
        Show description of the property. If --all is specified, all
        properties are shown.

    set [--force] [--node <nodename>] <property>=<value>...
        Set specific pacemaker properties.
```

**Cluster property configuration (syntax for running cluster):**

```bash
cat << 'PROPS'
# ============================================================
# Pacemaker Cluster Properties — Two-Node Production Settings
# Run these after: pcs cluster start --all
# ============================================================

# Quorum policy for 2-node cluster
pcs property set no-quorum-policy=ignore

# Enable STONITH (required for data integrity)
pcs property set stonith-enabled=true

# Resource defaults
pcs property set default-resource-stickiness=100  # Prefer current node
pcs property set migration-threshold=3             # Fail 3x before moving

# Timing (conservative settings)
pcs property set cluster-delay=60s
pcs property set pe-input-series-max=4000          # Audit log size

# Enable maintenance mode during planned downtime
# pcs property set maintenance-mode=true
# ... do your maintenance ...
# pcs property set maintenance-mode=false

# Resource operation defaults
pcs resource defaults update resource-stickiness=100
pcs resource defaults update failure-timeout=3min

# Operation defaults
pcs resource op defaults update timeout=60s
PROPS

echo "=== Writing cluster properties to CIB XML ==="
# Create a CIB snippet showing the properties
cat > /tmp/cluster-properties.xml << 'EOF'
<cib crm_feature_set="3.6.5">
  <configuration>
    <crm_config>
      <cluster_property_set id="cib-bootstrap-options">
        <nvpair id="no-quorum-policy" name="no-quorum-policy" value="ignore"/>
        <nvpair id="stonith-enabled" name="stonith-enabled" value="true"/>
        <nvpair id="default-resource-stickiness" name="default-resource-stickiness" value="100"/>
        <nvpair id="migration-threshold" name="migration-threshold" value="3"/>
        <nvpair id="cluster-delay" name="cluster-delay" value="60s"/>
      </cluster_property_set>
    </crm_config>
  </configuration>
</cib>
EOF

cat /tmp/cluster-properties.xml
echo "CIB properties XML written"
```

📸 **Verified Output:**
```
=== Writing cluster properties to CIB XML ===
<cib crm_feature_set="3.6.5">
  <configuration>
    <crm_config>
      <cluster_property_set id="cib-bootstrap-options">
        <nvpair id="no-quorum-policy" name="no-quorum-policy" value="ignore"/>
        <nvpair id="stonith-enabled" name="stonith-enabled" value="true"/>
...
CIB properties XML written
```

> 💡 **Tip:** `no-quorum-policy=ignore` is safe for 2-node clusters because with only 2 nodes, quorum can never be achieved after one fails. Use `no-quorum-policy=stop` for 3+ node clusters.

---

## Step 4: Virtual IP Resource Configuration

```bash
cat > /tmp/cluster-resources.sh << 'EOF'
#!/bin/bash
# ============================================================
# Pacemaker Resource Definitions — HA Two-Node Cluster
# Run after cluster is operational
# ============================================================

# --- STONITH Resources ---

# Fence node2 using IPMI
pcs stonith create fence-node1 fence_ipmilan \
    ip="10.0.0.11" username="admin" password="ipmisecret" \
    lanplus="1" pcmk_host_list="node1" \
    op monitor interval=60s timeout=30s

# Fence node1 using IPMI
pcs stonith create fence-node2 fence_ipmilan \
    ip="10.0.0.12" username="admin" password="ipmisecret" \
    lanplus="1" pcmk_host_list="node2" \
    op monitor interval=60s timeout=30s

# Constraint: nodes should not fence themselves
pcs constraint location fence-node1 avoids node1
pcs constraint location fence-node2 avoids node2

# --- Virtual IP Resource ---

pcs resource create ClusterVIP ocf:heartbeat:IPaddr2 \
    ip="10.0.1.100" \
    cidr_netmask="24" \
    nic="eth0" \
    op monitor interval=10s timeout=20s \
    op start  timeout=30s \
    op stop   timeout=30s

# --- HAProxy Resource ---

pcs resource create HAProxy systemd:haproxy \
    op monitor interval=15s timeout=30s \
    op start  timeout=60s \
    op stop   timeout=30s

# --- Resource Grouping ---
# VIP and HAProxy start/stop together, VIP always first
pcs resource group add WebGroup ClusterVIP HAProxy

# --- Location Constraints ---
# Prefer node1 but allow failover to node2
pcs constraint location WebGroup prefers node1=100
pcs constraint location WebGroup prefers node2=50

# --- Optional: Clone resource for all nodes ---
# (e.g., a monitoring agent running on all nodes)
pcs resource create NodeExporter systemd:prometheus-node-exporter \
    op monitor interval=30s
pcs resource clone NodeExporter
EOF

chmod +x /tmp/cluster-resources.sh
cat /tmp/cluster-resources.sh
echo "Resource configuration script ready"
```

📸 **Verified Output:**
```
#!/bin/bash
# ============================================================
# Pacemaker Resource Definitions — HA Two-Node Cluster
...
Resource configuration script ready
```

---

## Step 5: HAProxy Configuration as Cluster Resource

```bash
cat > /etc/haproxy/haproxy.cfg << 'EOF'
#============================================================
# HAProxy Configuration — HA Cluster Managed Service
# This config is identical on both nodes (shared via Ansible/Git)
# HAProxy is managed by Pacemaker — do NOT set to start on boot
#============================================================

global
    log /dev/log    local0
    log /dev/log    local1 notice
    maxconn         50000
    daemon
    user haproxy
    group haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor
    option  http-server-close
    retries 3
    timeout connect  5s
    timeout client   30s
    timeout server   30s
    timeout http-request 10s

#------------------------------------------------------------
# Health check endpoint (used by Keepalived/Pacemaker)
#------------------------------------------------------------
frontend health_check
    bind 127.0.0.1:8888
    default_backend health_backend

backend health_backend
    balance roundrobin
    server local 127.0.0.1:8889 check

#------------------------------------------------------------
# Main web frontend
#------------------------------------------------------------
frontend web
    bind 10.0.1.100:80     # Bind to VIP — only works when this node is MASTER
    bind 10.0.1.100:443 ssl crt /etc/ssl/haproxy/cert.pem

    # Security headers
    http-response set-header Strict-Transport-Security "max-age=63072000"

    # ACL routing
    acl is_api  path_beg /api/
    acl is_ws   hdr(Upgrade) -i websocket

    use_backend api_pool if is_api
    use_backend ws_pool  if is_ws
    default_backend web_pool

backend web_pool
    balance roundrobin
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    http-check expect status 200
    server app1 10.0.2.10:8080 check inter 3s rise 2 fall 3 weight 100
    server app2 10.0.2.11:8080 check inter 3s rise 2 fall 3 weight 100
    server app3 10.0.2.12:8080 check inter 3s rise 2 fall 3 weight 100

backend api_pool
    balance leastconn
    option httpchk GET /api/health
    server api1 10.0.2.20:8080 check inter 5s rise 2 fall 3
    server api2 10.0.2.21:8080 check inter 5s rise 2 fall 3

backend ws_pool
    balance source
    timeout tunnel 3600s
    server ws1 10.0.2.30:8080 check inter 5s
    server ws2 10.0.2.31:8080 check inter 5s

#------------------------------------------------------------
# Stats page (accessible from management network only)
#------------------------------------------------------------
listen stats
    bind 0.0.0.0:8404
    stats enable
    stats uri /haproxy-stats
    stats refresh 10s
    stats auth ops:monitoring123
    stats show-legends
    stats show-node
EOF

# Validate the configuration
haproxy -c -f /etc/haproxy/haproxy.cfg 2>&1 | grep -E "valid|error|warning|ALERT" | head -5
echo "HAProxy cluster config written and validated"
```

📸 **Verified Output:**
```
[WARNING]  (1) : config : missing timeouts for the 'health_backend' backend.
Configuration file is valid
HAProxy cluster config written and validated
```

> 💡 **Tip:** When HAProxy is managed by Pacemaker, disable the systemd auto-start: `systemctl disable haproxy`. Pacemaker will start/stop it based on cluster state. If both Pacemaker and systemd try to manage haproxy, you'll get conflicts.

---

## Step 6: Health Check Scripts

```bash
cat > /usr/local/bin/cluster-health-check.sh << 'EOF'
#!/bin/bash
# ============================================================
# Cluster Health Check Script
# Used by: Keepalived track_script, Pacemaker monitor
# Exit: 0 = healthy, 1 = unhealthy
# ============================================================

LOGFILE=/var/log/cluster-health.log
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
EXIT_CODE=0

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOGFILE"
}

# --- Check 1: HAProxy process ---
check_haproxy_process() {
    if pgrep -x haproxy > /dev/null 2>&1; then
        log "OK: haproxy process running (PID: $(pgrep -x haproxy | head -1))"
        return 0
    else
        log "FAIL: haproxy process not found"
        return 1
    fi
}

# --- Check 2: HAProxy socket responsiveness ---
check_haproxy_socket() {
    local sock=/run/haproxy/admin.sock
    if [[ -S "$sock" ]]; then
        local info
        info=$(echo "show info" | socat stdio "$sock" 2>/dev/null | grep "Uptime_sec" | awk '{print $2}')
        if [[ -n "$info" ]]; then
            log "OK: HAProxy socket responding (uptime: ${info}s)"
            return 0
        fi
    fi
    log "WARN: HAProxy socket not responding"
    return 0  # Warning only, not fatal
}

# --- Check 3: Backend servers health ---
check_backends() {
    local sock=/run/haproxy/admin.sock
    if [[ -S "$sock" ]]; then
        local up_count
        up_count=$(echo "show stat" | socat stdio "$sock" 2>/dev/null \
            | awk -F',' 'NR>1 && $18=="UP" {count++} END {print count+0}')
        if [[ "$up_count" -gt 0 ]]; then
            log "OK: $up_count backend servers are UP"
            return 0
        else
            log "FAIL: No backend servers are UP"
            return 1
        fi
    fi
    return 0
}

# --- Check 4: Network connectivity to backends ---
check_network() {
    local backends=("10.0.2.10" "10.0.2.11")
    local reachable=0
    for host in "${backends[@]}"; do
        if ping -c 1 -W 2 "$host" > /dev/null 2>&1; then
            ((reachable++))
        fi
    done
    if [[ "$reachable" -gt 0 ]]; then
        log "OK: $reachable/${#backends[@]} backends reachable"
        return 0
    else
        log "FAIL: No backends reachable"
        return 1
    fi
}

# --- Check 5: VIP presence ---
check_vip() {
    local vip="10.0.1.100"
    if ip addr show | grep -q "$vip"; then
        log "OK: VIP $vip is bound to this node"
    else
        log "INFO: VIP $vip not on this node (may be on peer)"
    fi
    return 0
}

# Run all checks
check_haproxy_process || EXIT_CODE=1
check_haproxy_socket
check_backends        || EXIT_CODE=1
check_network
check_vip

if [[ $EXIT_CODE -eq 0 ]]; then
    log "RESULT: All critical checks PASSED"
else
    log "RESULT: One or more critical checks FAILED"
fi

exit $EXIT_CODE
EOF

chmod 755 /usr/local/bin/cluster-health-check.sh
echo "Health check script created:"
ls -la /usr/local/bin/cluster-health-check.sh
```

📸 **Verified Output:**
```
Health check script created:
-rwxr-xr-x 1 root root 2473 Mar  5 07:10 /usr/local/bin/cluster-health-check.sh
```

---

## Step 7: Failover Testing Procedure

```bash
cat > /tmp/failover-test-procedure.md << 'EOF'
# Cluster Failover Test Procedure

## Pre-Test Checklist
- [ ] Cluster is fully operational: `crm_mon -r` shows all resources Started
- [ ] Both nodes are online: `pcs cluster status` shows 2 nodes
- [ ] Backups are current
- [ ] Change window is approved
- [ ] Operations team is notified
- [ ] Monitoring alerts are acknowledged (not silenced)

## Test 1: Planned Resource Failover (Safest)

```bash
# Move resource to other node (graceful)
pcs resource move WebGroup node2

# Verify resources moved
crm_mon -r -1

# Move back
pcs resource move WebGroup node1
pcs resource clear WebGroup    # Remove move constraint
```

## Test 2: Node Standby (Graceful Failover)

```bash
# Put node1 in standby (resources will migrate to node2)
pcs node standby node1

# Verify failover
watch -n 2 'pcs status'

# Expected: All resources show "Started node2"

# Bring node1 back
pcs node unstandby node1

# Verify node1 rejoins
pcs status
```

## Test 3: Service Kill (Application Failure Simulation)

```bash
# Kill HAProxy on active node
ssh node1 "pkill -9 haproxy"

# Monitor recovery (Pacemaker should restart within monitor interval)
watch -n 1 'crm_mon -r -1'

# Expected: HAProxy restarts on node1 (or moves to node2 after migration-threshold)
# Recovery time: 15-45 seconds
```

## Test 4: Hard Node Failure (Physical Simulation)

```bash
# WARNING: This requires STONITH to be properly configured!
# Stop corosync to simulate network partition
ssh node1 "systemctl stop corosync"

# On node2, observe:
#   1. node1 declared UNCLEAN
#   2. STONITH fires (fence_ipmilan powers off node1)
#   3. Resources start on node2
watch -n 2 'crm_mon -r -1'

# Recovery:
ssh node1 "systemctl start corosync pacemaker"
```

## Test 5: VIP Failover Validation

```bash
# From an external client, continuously ping the VIP
ping 10.0.1.100 -i 0.5

# Trigger failover (see Test 2)
# Observe: ping may show 1-3 dropped packets during VIP migration
# Expected: VIP responds within 5-10 seconds on new node
```

## Test 6: HAProxy Backend Failover

```bash
# Simulate one backend going down
ssh app1 "systemctl stop myapp"

# HAProxy health check will detect failure within fall*inter = 3*3s = 9s
# Traffic redistributes to remaining backends

# Verify via HAProxy stats:
echo "show stat" | socat stdio /run/haproxy/admin.sock | awk -F',' 'NR>1 {print $1,$2,$18}'
```

## Expected Failover Times

| Failure Type | Detection Time | Recovery Time | Total Outage |
|-------------|---------------|---------------|-------------|
| Process killed | 15s (monitor) | 30s | 45s |
| Node standby | Immediate | 30-60s | 30-60s |
| Node hard crash | 3-10s (token) | 45-90s | 60-120s |
| Backend failure | 6-9s (HAProxy check) | Instant (other backends) | 0s (no VIP change) |

## Post-Failover Checks

```bash
# 1. Cluster status
pcs status

# 2. Resource locations
crm_mon -r -1

# 3. HAProxy backend health
echo "show stat" | socat stdio /run/haproxy/admin.sock | grep -E "BACKEND|UP|DOWN"

# 4. Application response
curl -sf http://10.0.1.100/health && echo "App OK"

# 5. Logs review
journalctl -u pacemaker --since "1 hour ago"
tail -100 /var/log/corosync/corosync.log
```
EOF

cat /tmp/failover-test-procedure.md | head -50
echo "..."
echo "Failover test procedure written ($(wc -l < /tmp/failover-test-procedure.md) lines)"
```

📸 **Verified Output:**
```
# Cluster Failover Test Procedure

## Pre-Test Checklist
- [ ] Cluster is fully operational: `crm_mon -r` shows all resources Started
...
Failover test procedure written (97 lines)
```

> 💡 **Tip:** Always test failover in staging before production. Test ALL failure scenarios: process kill, node standby, hard failure (STONITH), and network partition. Each has different timing and behaviour. Document your measured failover times — they will differ from theoretical values.

---

## Step 8: Monitoring with crm_mon + Full Runbook

```bash
# crm_mon options
crm_mon --help 2>&1 | head -20
```

📸 **Verified Output:**
```
Usage:
  crm_mon [OPTION?]

Provides a summary of cluster's current state.

Outputs varying levels of detail in a number of different formats.

Application Options:
  -$, --version     Display software version and exit
  -V, --verbose     Increase debug output
  -Q, --quiet       Be less descriptive in output.
```

```bash
# Generate the complete operational runbook
cat > /tmp/ha-cluster-runbook.md << 'RUNBOOK'
# HA Cluster Operational Runbook
# Cluster: prod-ha-cluster
# Version: 1.0 | Date: 2026-03-05
# Maintainer: Operations Team <ops@example.com>

---

## 1. Cluster Overview

| Item | Value |
|------|-------|
| Cluster Name | prod-ha-cluster |
| Software | Pacemaker 2.1.2 + Corosync 3.1.6 |
| Nodes | node1 (10.0.1.11) + node2 (10.0.1.12) |
| VIP | 10.0.1.100 |
| Load Balancer | HAProxy 2.4.x |
| Fencing | fence_ipmilan (IPMI) |
| Monitoring | crm_mon + Prometheus Node Exporter |

---

## 2. Daily Health Checks

```bash
# Run from either node as root
pcs status                          # Overall cluster status
crm_mon -r -1                       # Resource status (one-shot)
corosync-cfgtool -s                  # Ring status
pcs stonith status                  # Fencing status

# Expected: all nodes Online, all resources Started
```

---

## 3. Common Operations

### 3.1 Planned Maintenance (Node1)

```bash
# 1. Move resources to node2
pcs node standby node1

# 2. Verify failover complete
crm_mon -r -1 | grep -E "Started|Stopped"

# 3. Perform maintenance on node1

# 4. Return node1 to service
pcs node unstandby node1

# 5. Rebalance if desired
pcs resource move WebGroup node1
pcs resource clear WebGroup
```

### 3.2 HAProxy Config Update (Zero-Downtime)

```bash
# 1. Edit config on BOTH nodes (use Ansible/Git)
vim /etc/haproxy/haproxy.cfg

# 2. Validate
haproxy -c -f /etc/haproxy/haproxy.cfg

# 3. Reload via Pacemaker (graceful)
pcs resource restart HAProxy

# OR direct graceful reload (while managed by Pacemaker):
haproxy -f /etc/haproxy/haproxy.cfg -sf $(pidof haproxy)
```

### 3.3 Add New Backend Server

```bash
# 1. Edit /etc/haproxy/haproxy.cfg on both nodes:
# In backend web_pool, add:
#   server app4 10.0.2.13:8080 check inter 3s rise 2 fall 3 weight 100

# 2. Validate + reload
haproxy -c -f /etc/haproxy/haproxy.cfg
pcs resource restart HAProxy
```

### 3.4 Emergency — Force Resource to Specific Node

```bash
# Move WebGroup to node2 immediately
pcs resource move WebGroup node2 --wait

# After emergency resolved, remove constraint
pcs resource clear WebGroup
```

---

## 4. Monitoring Commands

```bash
# Real-time cluster monitor (interactive, refreshes every 1s)
crm_mon -r -i 1

# One-shot status with resource details
crm_mon -r -1

# Show failed operations
crm_mon -r -1 | grep -A5 "Failed"

# Clear failed operation count
pcs resource cleanup <resource-id>

# HAProxy statistics
echo "show stat" | socat stdio /run/haproxy/admin.sock | \
    awk -F',' 'NR>1 && $2!="FRONTEND" {printf "%-20s %-10s %-10s\n", $1,$2,$18}'

# Corosync ring status
corosync-cfgtool -s

# Check logs
journalctl -u corosync -u pacemaker -f    # Follow cluster logs
tail -f /var/log/corosync/corosync.log
tail -f /var/log/pacemaker/pacemaker.log
```

---

## 5. Troubleshooting

### 5.1 Resources Not Starting

```bash
pcs status                           # See error messages
crm_mon -r -1                        # Detailed resource status
pcs resource cleanup <resource>       # Clear failure count
pcs resource debug-start <resource>   # Debug start operation

# Check agent logs:
journalctl -u pacemaker | grep "ERROR\|FAIL"
```

### 5.2 Node Not Joining Cluster

```bash
# On the missing node:
systemctl status corosync pacemaker
journalctl -u corosync | tail -50
corosync-cfgtool -s

# Common causes:
# - Firewall blocking ports 5403-5405 (Corosync)
# - /etc/corosync/authkey mismatch (regenerate and copy)
# - Time skew > 2s (sync NTP: chronyc makestep)
```

### 5.3 STONITH Failure

```bash
# Test fencing manually
fence_ipmilan -a 10.0.0.12 -l admin -p secret --lanplus -o status

# If STONITH failing, temporarily disable for diagnostics (NEVER in production!):
pcs property set stonith-enabled=false   # Diagnostic only!

# Re-enable immediately after:
pcs property set stonith-enabled=true
```

### 5.4 Split-Brain Recovery

```bash
# If cluster is partitioned, one side will be fenced
# After recovery, re-integrate the fenced node:

# 1. On the previously fenced node (powered off by STONITH):
systemctl start corosync
systemctl start pacemaker

# 2. Cluster will re-accept the node
pcs status

# 3. If node stays UNCLEAN:
pcs stonith ack <node>    # Acknowledge fence completion manually
```

---

## 6. Emergency Contacts

| Role | Contact | Phone |
|------|---------|-------|
| Primary On-Call | ops-primary@example.com | +1-555-0100 |
| Backup On-Call | ops-backup@example.com | +1-555-0101 |
| Vendor Support | RedHat/SUSE Support | Contract # |

---

## 7. Runbook Sign-off

| Date | Engineer | Change | Tested |
|------|---------|--------|--------|
| 2026-03-05 | Infrastructure Team | Initial version | Yes |

RUNBOOK

echo "Runbook generated:"
wc -l /tmp/ha-cluster-runbook.md
echo ""
echo "=== Runbook Preview (first 30 lines) ==="
head -30 /tmp/ha-cluster-runbook.md
```

📸 **Verified Output:**
```
Runbook generated:
155 /tmp/ha-cluster-runbook.md

=== Runbook Preview (first 30 lines) ===
# HA Cluster Operational Runbook
# Cluster: prod-ha-cluster
# Version: 1.0 | Date: 2026-03-05
# Maintainer: Operations Team <ops@example.com>

---

## 1. Cluster Overview

| Item | Value |
|------|-------|
| Cluster Name | prod-ha-cluster |
| Software | Pacemaker 2.1.2 + Corosync 3.1.6 |
| Nodes | node1 (10.0.1.11) + node2 (10.0.1.12) |
| VIP | 10.0.1.100 |
| Load Balancer | HAProxy 2.4.x |
| Fencing | fence_ipmilan (IPMI) |
| Monitoring | crm_mon + Prometheus Node Exporter |

---

## 2. Daily Health Checks
...
```

> 💡 **Tip:** Store your runbook in Git alongside your cluster configuration. Every config change should update the runbook. Practice failover procedures quarterly — untested runbooks are worth nothing during a real outage at 3 AM.

---

## Summary

| Component | Technology | Config File | Key Command |
|-----------|-----------|-------------|-------------|
| Messaging Layer | Corosync 3.1.6 | `/etc/corosync/corosync.conf` | `corosync-cfgtool -s` |
| Cluster Manager | Pacemaker 2.1.2 | CIB (XML database) | `pcs status` |
| Cluster CLI | pcs 0.10.11 | N/A | `pcs resource`, `pcs node` |
| Load Balancer | HAProxy 2.4.x | `/etc/haproxy/haproxy.cfg` | `haproxy -c -f` |
| VIP Failover | IPaddr2 OCF RA | pcs resource definition | `pcs resource create ClusterVIP` |
| Fencing | fence_ipmilan | pcs stonith definition | `pcs stonith create` |
| Health Check | Custom bash | `/usr/local/bin/cluster-health-check.sh` | `./cluster-health-check.sh` |
| Real-time Monitor | crm_mon | N/A | `crm_mon -r -i 1` |
| Failover Test | pcs node standby | N/A | `pcs node standby node1` |
| Runbook | Markdown doc | `/opt/runbooks/ha-cluster.md` | Review quarterly |
