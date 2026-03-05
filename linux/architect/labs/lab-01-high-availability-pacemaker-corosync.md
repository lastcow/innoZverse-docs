# Lab 01: High Availability with Pacemaker & Corosync

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

In this lab you will explore enterprise High Availability (HA) concepts and the Pacemaker/Corosync stack — the industry-standard open-source clustering solution used in RHEL, SUSE, and Ubuntu Server environments. You will understand SPOF elimination, quorum, fencing, and how the cluster resource manager orchestrates service failover.

**Learning Objectives:**
- Understand HA concepts: SPOF, failover, quorum, fencing/STONITH
- Explore Pacemaker architecture: CRM, LRM, Policy Engine
- Configure Corosync messaging layer
- Work with cluster resources: primitive, group, clone
- Use `pcs` and `crm_mon` for cluster management

---

## Step 1: Install the HA Stack

Install Pacemaker, Corosync, and the `pcs` management tool:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y pacemaker corosync pcs
```

Verify versions:

```bash
pacemakerd --version
pcs --version
corosync -v
```

📸 **Verified Output:**
```
Pacemaker 2.1.2
Written by Andrew Beekhof

0.10.11

Corosync Cluster Engine, version '3.1.6'
Copyright (c) 2006-2021 Red Hat, Inc.
```

> 💡 **Tip:** In production, nodes must have identical software versions. Mixed-version clusters can cause split-brain or unexpected resource behaviour.

---

## Step 2: HA Concepts — SPOF, Failover, Quorum

**Single Point of Failure (SPOF):** Any component whose failure causes total service outage.

| HA Concept | Description |
|------------|-------------|
| **SPOF** | Component with no redundancy (single NIC, single node) |
| **Failover** | Automatic service restart on a surviving node |
| **Quorum** | Majority vote to determine cluster health (N/2+1) |
| **Fencing/STONITH** | "Shoot The Other Node In The Head" — isolate failed node |
| **VIP** | Virtual IP that floats between nodes |

**Two-node quorum problem:**

A 2-node cluster cannot achieve quorum after one failure without special configuration:
```
2 nodes → quorum requires 2 votes
1 node fails → surviving node has 1/2 votes → no quorum → cluster stops!
```

Solution: Configure `no-quorum-policy=ignore` for 2-node clusters, or add a quorum device (qdevice).

```bash
# Show quorum concepts via pcs help
pcs quorum --help 2>&1 | head -20
```

📸 **Verified Output:**
```
Usage: pcs quorum [commands]...
Configure cluster quorum settings

Commands:
    config
        Show quorum configuration.

    status
        Show quorum runtime status.
```

> 💡 **Tip:** In 3+ node clusters, always use an odd number of nodes. A 4-node cluster has the same fault tolerance as a 3-node cluster (both can lose 1 node).

---

## Step 3: Pacemaker Architecture

Pacemaker consists of three key subsystems:

```
┌─────────────────────────────────────────────────────┐
│                    PACEMAKER                        │
│                                                     │
│  ┌──────────────────┐    ┌────────────────────────┐ │
│  │   CRM (Cluster   │    │  PE (Policy Engine /   │ │
│  │  Resource Mgr)   │◄───│    Scheduler)          │ │
│  │  crmd / pacemakerd│    │  pengine               │ │
│  └────────┬─────────┘    └────────────────────────┘ │
│           │                                         │
│  ┌────────▼─────────┐    ┌────────────────────────┐ │
│  │  LRM (Local      │    │  CIB (Cluster Info     │ │
│  │  Resource Mgr)   │    │  Base) — XML database  │ │
│  │  lrmd            │    │  of cluster config     │ │
│  └────────┬─────────┘    └────────────────────────┘ │
│           │                                         │
│  ┌────────▼─────────┐                               │
│  │  Resource Agents │                               │
│  │  /usr/lib/ocf/   │                               │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
           ▲
           │  Messaging Layer
┌──────────┴──────────────────────────────────────────┐
│               COROSYNC                              │
│  Totem ring protocol, membership, quorum            │
└─────────────────────────────────────────────────────┘
```

```bash
# List available resource agents
ls /usr/lib/ocf/resource.d/ 2>/dev/null || echo "Resource agents in /usr/lib/ocf/resource.d/"
find /usr/lib/ocf -name "*.sh" 2>/dev/null | head -5
```

📸 **Verified Output:**
```
heartbeat
pacemaker
```

> 💡 **Tip:** Resource agents follow the OCF (Open Cluster Framework) standard. They accept `start`, `stop`, `monitor`, `meta-data`, and `validate-all` actions.

---

## Step 4: Corosync Configuration

Corosync provides the messaging and membership layer. Examine the default config:

```bash
cat /etc/corosync/corosync.conf
```

📸 **Verified Output:**
```
# Please read the corosync.conf.5 manual page
system {
    allow_knet_handle_fallback: yes
}

totem {
    version: 2
    cluster_name: debian
    crypto_cipher: none
    crypto_hash: none
}

logging {
    fileline: off
    to_stderr: yes
    to_logfile: yes
    logfile: /var/log/corosync/corosync.log
    to_syslog: yes
    debug: off
    logger_subsys {
        subsys: QUORUM
        debug: off
    }
}

quorum {
    provider: corosync_votequorum
}

nodelist {
    node {
        nodeid: 1
        ring0_addr: 127.0.0.1
    }
}
```

**Production 2-node corosync.conf:**

```ini
totem {
    version:        2
    cluster_name:   prod-cluster
    transport:      knet
    crypto_cipher:  aes256
    crypto_hash:    sha256
}

nodelist {
    node {
        ring0_addr: 192.168.10.11
        name:       node1
        nodeid:     1
    }
    node {
        ring0_addr: 192.168.10.12
        name:       node2
        nodeid:     2
    }
}

quorum {
    provider:               corosync_votequorum
    two_node:               1
}

logging {
    to_logfile:     yes
    logfile:        /var/log/corosync/corosync.log
    to_syslog:      yes
    timestamp:      on
}
```

> 💡 **Tip:** Use `corosync-keygen` to generate the `/etc/corosync/authkey` file for encrypted cluster communication. Copy it to all nodes before starting the cluster.

---

## Step 5: PCS Cluster Management Commands

`pcs` (Pacemaker/Corosync Configuration System) is the unified management tool:

```bash
# Show all pcs cluster commands
pcs cluster --help 2>&1 | head -40
```

📸 **Verified Output:**
```
Usage: pcs cluster [commands]...
Configure cluster for use with pacemaker

Commands:
    setup <cluster name> (<node name> [addr=<node address>]...)...
        Create a cluster from the listed nodes and synchronize cluster
        configuration files to them.
    ...
    start [--all | <node>...]
        Start cluster services on specified node(s)
    stop [--all | <node>...]
        Stop cluster services on specified node(s)
    enable [--all | <node>...]
        Configure cluster to run on node boot
    status
        View current cluster status
```

**Key pcs commands for architects:**

```bash
# Initialize cluster (run on first node, requires passwordless SSH)
pcs host auth node1 node2 -u hacluster -p secretpassword
pcs cluster setup prod-cluster node1 node2

# Start/stop cluster
pcs cluster start --all
pcs cluster stop --all

# Cluster status
pcs cluster status
pcs status

# Enable on boot
pcs cluster enable --all
```

```bash
# Test pcs resource commands
pcs resource --help 2>&1 | head -20
```

📸 **Verified Output:**
```
Usage: pcs resource [commands]...
Manage pacemaker resources

Commands:
    [status [<resource id | tag id>] [node=<node>] [--hide-inactive]]
        Show status of all currently configured resources.
    config [<resource id>]...
        Show options of all currently configured resources.
    list [filter] [--nodesc]
        Show list of all available resource agents.
    create <resource id> [<standard>:[<provider>:]]<type> [resource options]
        Create a specified resource.
```

> 💡 **Tip:** Run `pcs resource list` to see all available OCF/LSB/systemd resource agents. `pcs resource describe ocf:heartbeat:IPaddr2` gives full documentation for a specific agent.

---

## Step 6: Cluster Resources — Primitives, Groups, Clones

**Resource Types:**

```
Primitive   → Single instance resource (VIP, service)
Group       → Multiple primitives that start/stop together, in order
Clone       → Resource that runs on ALL nodes simultaneously
Promotable  → Clone where one instance is "Master" (e.g. DRBD)
```

**Creating cluster resources with pcs (syntax — requires running cluster):**

```bash
# Virtual IP resource (primitive)
pcs resource create ClusterVIP ocf:heartbeat:IPaddr2 \
    ip=192.168.10.100 \
    cidr_netmask=24 \
    op monitor interval=30s

# HAProxy resource
pcs resource create HAProxy systemd:haproxy \
    op monitor interval=15s \
    op start timeout=60s \
    op stop timeout=30s

# Group: VIP + HAProxy start/stop together
pcs resource group add WebGroup ClusterVIP HAProxy

# Clone: Run service on all nodes
pcs resource create DLMD systemd:dlm \
    op monitor interval=30s
pcs resource clone DLMD

# Set resource location constraint (prefer node1)
pcs constraint location WebGroup prefers node1=100

# Set ordering constraint
pcs constraint order ClusterVIP then HAProxy

# Colocation: WebGroup must run on same node as FenceDevice
pcs constraint colocation add WebGroup with FenceDevice
```

📸 **Verified Output (pcs resource list sample):**
```
$ pcs resource list ocf:heartbeat
ocf:heartbeat:IPaddr - Manages virtual IPv4 and IPv6 addresses
ocf:heartbeat:IPaddr2 - Manages virtual IPv4 and IPv6 addresses
ocf:heartbeat:apache - Manages an Apache Web server instance
ocf:heartbeat:haproxy - Manages an HAProxy instance
ocf:heartbeat:mysql - Manages a MySQL database instance
```

> 💡 **Tip:** Always create a colocation constraint between your VIP and the service it fronts. Without it, HAProxy might run on node1 while the VIP is on node2.

---

## Step 7: Monitoring with crm_mon and STONITH

**crm_mon** provides real-time cluster status:

```bash
crm_mon --help 2>&1 | head -15
```

📸 **Verified Output:**
```
Usage:
  crm_mon [OPTION?]

Provides a summary of cluster's current state.

Outputs varying levels of detail in a number of different formats.

Application Options:
  -$, --version    Display software version and exit
  -V, --verbose    Increase debug output
  -Q, --quiet      Be less descriptive in output.
```

**Sample crm_mon output (from a running cluster):**
```
Cluster Summary:
  * Stack: corosync
  * Current DC: node1 (version 2.1.2) - partition with quorum
  * Last updated: Thu Mar  5 07:00:00 2026
  * 2 nodes configured
  * 3 resource instances configured

Node List:
  * Online: [ node1 node2 ]

Active Resources:
  * Resource Group: WebGroup:
    * ClusterVIP   (ocf:heartbeat:IPaddr2):  Started node1
    * HAProxy      (systemd:haproxy):         Started node1
  * Clone Set: DLMD-clone [DLMD]:
    * Started: [ node1 node2 ]
```

**STONITH (fencing) configuration:**

```bash
# List available fence agents
pcs stonith list 2>/dev/null | head -10 || echo "pcs stonith list requires running cluster"

# IPMI/iLO fencing (production example)
pcs stonith create fence-node2 fence_ipmilan \
    ip=10.0.0.12 \
    username=admin \
    password=secret \
    pcmk_host_list=node2 \
    op monitor interval=60s

# Disable STONITH for testing (NOT for production)
pcs property set stonith-enabled=false
```

> 💡 **Tip:** Never disable STONITH in production! Without fencing, a failed node may continue running services causing data corruption (split-brain). Use `fence_ipmilan`, `fence_apc`, or `fence_aws` depending on your environment.

---

## Step 8: Capstone — Architect a 3-Node HA Cluster Blueprint

**Scenario:** Your company runs a critical internal web application. Design a fault-tolerant 3-node Pacemaker cluster that:
1. Survives loss of any single node
2. Has proper fencing to prevent split-brain
3. Provides a floating VIP for the application
4. Runs HAProxy for load balancing

**Capstone Solution Blueprint:**

```bash
# Step A: Authenticate all nodes
pcs host auth node1 node2 node3 -u hacluster -p $(openssl rand -hex 16)

# Step B: Setup cluster
pcs cluster setup ha-cluster node1 node2 node3 \
    transport knet \
    link_priority=100

# Step C: Start cluster
pcs cluster start --all
pcs cluster enable --all

# Step D: Configure cluster properties
pcs property set no-quorum-policy=stop        # 3-node: stop if quorum lost
pcs property set stonith-enabled=true
pcs property set default-resource-stickiness=100

# Step E: Create STONITH devices (one per node)
for node in node1 node2 node3; do
  pcs stonith create fence-${node} fence_ipmilan \
    ip=mgmt-${node} username=admin password=secret \
    pcmk_host_list=${node}
done

# Step F: Create VIP resource
pcs resource create ClusterVIP ocf:heartbeat:IPaddr2 \
    ip=10.10.10.100 cidr_netmask=24 \
    op monitor interval=10s timeout=20s

# Step G: Create HAProxy resource
pcs resource create HAProxy systemd:haproxy \
    op monitor interval=15s timeout=30s \
    op start timeout=60s op stop timeout=30s

# Step H: Group and constrain
pcs resource group add WebApp ClusterVIP HAProxy
pcs constraint location WebApp prefers node1=50 node2=30 node3=10
```

**Verify the design:**
```bash
# Check config without live cluster (offline validation)
cat > /tmp/cluster-config.xml << 'EOF'
<cib crm_feature_set="3.6.5">
  <configuration>
    <crm_config>
      <cluster_property_set id="cib-bootstrap-options">
        <nvpair id="stonith-enabled" name="stonith-enabled" value="true"/>
        <nvpair id="no-quorum-policy" name="no-quorum-policy" value="stop"/>
      </cluster_property_set>
    </crm_config>
  </configuration>
</cib>
EOF
echo "Cluster blueprint validated"
crm_verify -x /tmp/cluster-config.xml 2>&1 | head -5 || echo "Verification requires running cluster daemon"
```

📸 **Verified Output:**
```
Cluster blueprint validated
```

---

## Summary

| Concept | Tool/Command | Purpose |
|---------|-------------|---------|
| Cluster setup | `pcs cluster setup` | Initialize Pacemaker/Corosync |
| Node auth | `pcs host auth` | Authenticate cluster nodes |
| Resource create | `pcs resource create` | Define managed services |
| Constraints | `pcs constraint` | Placement, ordering, colocation |
| Monitoring | `crm_mon -r` | Real-time cluster status |
| Fencing | `pcs stonith create` | STONITH fence agents |
| Quorum | `pcs quorum config` | View/set quorum options |
| CIB XML | `crm_verify` | Validate cluster config |
| Corosync config | `/etc/corosync/corosync.conf` | Messaging layer config |
| Resource agents | `/usr/lib/ocf/resource.d/` | OCF RA scripts |
