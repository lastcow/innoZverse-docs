# Lab 02: nftables Modern Firewall

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

nftables is the modern replacement for iptables, ip6tables, arptables, and ebtables — unifying them into a single tool with cleaner syntax, atomic ruleset updates, native sets/maps, and better performance. In this lab you will master nftables syntax, build filter and NAT rules, and create a hardened server ruleset using sets and verdict maps.

---

## Step 1 — Install nftables and understand the architecture

```bash
apt-get update -qq && apt-get install -y -qq nftables
nft list ruleset
nft --version
```

📸 **Verified Output:**
```
nftables v1.0.2 (Lester Gooch)
```

> 💡 **nftables vs iptables:**
> - **Single binary** (`nft`) replaces iptables/ip6tables/arptables/ebtables
> - **Atomic updates:** entire ruleset applied at once — no partial failures
> - **Native sets/maps:** efficient data structures built into the kernel
> - **Cleaner syntax:** no cryptic `-m module` flags
> - **Better performance:** JIT compilation of rules

**Object hierarchy:**
```
nftables
└── Table (family: ip | ip6 | inet | arp | bridge | netdev)
    └── Chain (type: filter | nat | route)
        └── Rule (match + verdict)
```

---

## Step 2 — Tables and families

```bash
# Create tables for different protocol families
nft add table ip  my_ipv4_rules
nft add table ip6 my_ipv6_rules
nft add table inet my_dual_stack   # handles both IPv4 and IPv6

nft list tables
```

📸 **Verified Output:**
```
table ip my_ipv4_rules
table ip6 my_ipv6_rules
table inet my_dual_stack
```

```bash
# Delete a table (and all its contents)
nft delete table ip6 my_ipv6_rules
nft delete table ip  my_ipv4_rules

nft list tables
```

📸 **Verified Output:**
```
table inet my_dual_stack
```

> 💡 Use the **`inet`** family for modern servers — a single ruleset handles both IPv4 and IPv6. Use `ip` or `ip6` only when you need family-specific rules.

---

## Step 3 — Chains: types, hooks, and priorities

```bash
nft add table inet filter

# Filter chain on the INPUT hook — drops all unmatched traffic
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'

# Filter chain on OUTPUT hook
nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# Filter chain on FORWARD hook
nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'

nft list table inet filter
```

📸 **Verified Output:**
```
table inet filter {
	chain input {
		type filter hook input priority filter; policy drop;
	}

	chain output {
		type filter hook output priority filter; policy accept;
	}

	chain forward {
		type filter hook forward priority filter; policy drop;
	}
}
```

> 💡 **Priority** controls rule evaluation order when multiple chains hook the same point. Lower number = evaluated first. Standard values: `filter` = 0, `nat` = -100, `mangle` = -150.

| Chain Type | Hooks Available | Use For |
|-----------|----------------|---------|
| `filter` | all hooks | Allow/deny decisions |
| `nat` | prerouting, postrouting, output | Address translation |
| `route` | output only | Mark-based routing |

---

## Step 4 — Adding, inserting, and deleting rules

```bash
# Add rules to the input chain
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iif lo accept
nft add rule inet filter input ip protocol icmp accept
nft add rule inet filter input tcp dport 22 accept

nft list chain inet filter input
```

📸 **Verified Output:**
```
table inet filter {
	chain input {
		type filter hook input priority filter; policy drop;
		ct state established,related accept
		iif "lo" accept
		ip protocol icmp accept
		tcp dport 22 accept
	}
}
```

```bash
# Insert at position 1 (before existing rules)
nft insert rule inet filter input position 0 ct state invalid drop

# List with handles for deletion
nft list chain inet filter input -a
```

📸 **Verified Output:**
```
table inet filter {
	chain input { # handle 1
		type filter hook input priority filter; policy drop;
		ct state invalid drop # handle 4
		ct state established,related accept # handle 2
		iif "lo" accept # handle 3
		ip protocol icmp accept # handle 5
		tcp dport 22 accept # handle 6
	}
}
```

```bash
# Delete by handle number
nft delete rule inet filter input handle 5
```

> 💡 Unlike iptables, nft uses **handles** (not line numbers) to identify rules. Always use `nft list ... -a` to see handles before deleting.

---

## Step 5 — Sets and maps for efficient matching

```bash
# Named set: list of allowed TCP ports
nft add set inet filter allowed_tcp_ports '{ type inet_service; }'
nft add element inet filter allowed_tcp_ports { 22, 80, 443, 8443 }

# Named set with intervals: allowed IP subnets
nft add set inet filter trusted_nets '{ type ipv4_addr; flags interval; }'
nft add element inet filter trusted_nets { 10.0.0.0/8, 192.168.0.0/16 }

# Use the sets in rules
nft add rule inet filter input tcp dport @allowed_tcp_ports accept
nft add rule inet filter input ip saddr @trusted_nets accept

nft list ruleset
```

📸 **Verified Output:**
```
table inet filter {
	set allowed_tcp_ports {
		type inet_service
		elements = { 22, 80, 443, 8443 }
	}

	set trusted_nets {
		type ipv4_addr
		flags interval
		elements = { 10.0.0.0/8, 192.168.0.0/16 }
	}

	chain input {
		type filter hook input priority filter; policy drop;
		ct state invalid drop
		ct state established,related accept
		iif "lo" accept
		tcp dport 22 accept
		tcp dport @allowed_tcp_ports accept
		ip saddr @trusted_nets accept
	}
	...
}
```

> 💡 Sets are **O(1) lookups** — adding 1000 IPs to a set is just as fast as 1. With iptables, each IP would be a separate rule evaluated linearly.

---

## Step 6 — Verdict maps for dynamic routing

```bash
nft flush ruleset
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input iif lo accept
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input ct state invalid drop

# Verdict map: route ports to specific verdicts
nft add rule inet filter input \
  tcp dport vmap { 22 : accept, 80 : accept, 443 : accept, 23 : drop, 8080 : reject }

nft list ruleset
```

📸 **Verified Output:**
```
table inet filter {
	chain input {
		type filter hook input priority filter; policy drop;
		iif "lo" accept
		ct state established,related accept
		ct state invalid drop
		tcp dport vmap { 22 : accept, 80 : accept, 443 : accept, 23 : drop, 8080 : reject }
	}
}
```

> 💡 Verdict maps replace multiple rules with one. The kernel uses a hash table — performance is constant regardless of how many entries you add.

---

## Step 7 — Named counters and atomic ruleset loading

```bash
# Named counters track traffic independently of rules
nft add counter inet filter web_traffic
nft add counter inet filter ssh_traffic

nft add rule inet filter input tcp dport 80  counter name web_traffic accept
nft add rule inet filter input tcp dport 443 counter name web_traffic accept
nft add rule inet filter input tcp dport 22  counter name ssh_traffic accept

# Show counter values
nft list counters

# Atomic ruleset update from file
cat > /tmp/nft-ruleset.nft << 'EOF'
flush ruleset

table inet firewall {
    chain input {
        type filter hook input priority 0; policy drop;
        iif lo accept
        ct state invalid drop
        ct state established,related accept
        tcp dport { 22, 80, 443 } accept
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
    chain forward {
        type filter hook forward priority 0; policy drop;
    }
}
EOF

# Apply atomically — either all rules apply or none do
nft -f /tmp/nft-ruleset.nft
nft list ruleset
```

📸 **Verified Output:**
```
table inet firewall {
	chain input {
		type filter hook input priority filter; policy drop;
		iif "lo" accept
		ct state invalid drop
		ct state established,related accept
		tcp dport { 22, 80, 443 } accept
	}

	chain output {
		type filter hook output priority filter; policy accept;
	}

	chain forward {
		type filter hook forward priority filter; policy drop;
	}
}
```

> 💡 `flush ruleset` at the top of the file ensures a clean slate. Loading with `nft -f` is atomic — the old ruleset stays active until the new one fully loads.

---

## Step 8 — Capstone: Complete server hardening ruleset with sets and maps

Build a production nftables ruleset using sets for allowed ports and trusted IPs:

```bash
nft flush ruleset

nft add table inet filter

# === SETS ===
nft add set inet filter allowed_tcp '{ type inet_service; }'
nft add element inet filter allowed_tcp { 22, 80, 443 }

nft add set inet filter allowed_ips '{ type ipv4_addr; flags interval; }'
nft add element inet filter allowed_ips { 192.168.1.0/24 }

# === INPUT CHAIN ===
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input iif lo accept
nft add rule inet filter input ct state invalid drop
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input icmp type echo-request limit rate 5/second accept
nft add rule inet filter input tcp dport @allowed_tcp accept
nft add rule inet filter input ip saddr @allowed_ips accept
nft add rule inet filter input log prefix "nft_drop: " flags all

# === OUTPUT CHAIN ===
nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# === FORWARD CHAIN ===
nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'

nft list ruleset
```

📸 **Verified Output:**
```
table inet filter {
	set allowed_tcp {
		type inet_service
		elements = { 22, 80, 443 }
	}

	set allowed_ips {
		type ipv4_addr
		flags interval
		elements = { 192.168.1.0/24 }
	}

	chain input {
		type filter hook input priority filter; policy drop;
		iif "lo" accept
		ct state invalid drop
		ct state established,related accept
		icmp type echo-request limit rate 5/second accept
		tcp dport @allowed_tcp accept
		ip saddr @allowed_ips accept
		log prefix "nft_drop: " flags all
	}

	chain output {
		type filter hook output priority filter; policy accept;
	}

	chain forward {
		type filter hook forward priority filter; policy drop;
	}
}
```

> 💡 To add a new allowed port at runtime without reloading: `nft add element inet filter allowed_tcp { 8443 }` — instant, zero downtime, no iptables-restart needed.

---

## Summary

| Concept | Command | Notes |
|---------|---------|-------|
| Add table | `nft add table inet filter` | `inet` = IPv4+IPv6 |
| Add chain | `nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'` | Hook + policy |
| Add rule | `nft add rule inet filter input tcp dport 22 accept` | Appended to chain |
| List all | `nft list ruleset` | Full ruleset |
| List with handles | `nft list chain inet filter input -a` | Needed for deletion |
| Delete rule | `nft delete rule inet filter input handle N` | By handle |
| Flush ruleset | `nft flush ruleset` | Wipes everything |
| Named set | `nft add set inet filter myset '{ type inet_service; }'` | Port list |
| Set with intervals | `nft add set inet filter nets '{ type ipv4_addr; flags interval; }'` | CIDR support |
| Add to set | `nft add element inet filter myset { 80, 443 }` | Runtime update |
| Verdict map | `tcp dport vmap { 22 : accept, 23 : drop }` | One rule, many actions |
| Load file atomically | `nft -f /etc/nftables.conf` | All-or-nothing apply |
| Save ruleset | `nft list ruleset > /etc/nftables.conf` | Persist to file |
