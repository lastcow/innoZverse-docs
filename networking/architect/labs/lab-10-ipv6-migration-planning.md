# Lab 10: IPv6 Migration Planning

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

IPv4 exhaustion is complete — ARIN, RIPE, and APNIC have no more /8s to allocate. IPv6 adoption is accelerating with major carriers, cloud providers, and content networks. This lab covers migration strategies, addressing plans, and security considerations.

---

## Objectives
- Compare migration strategies (dual-stack, tunneling, translation)
- Design enterprise IPv6 addressing plan
- Configure DHCPv6 vs SLAAC
- Implement IPv6 security controls
- Build an IPv6 address planning tool

---

## Step 1: Migration Strategies

**Option 1: Dual Stack (Recommended)**
```
Every device has both IPv4 and IPv6 addresses.
Applications prefer IPv6 (Happy Eyeballs RFC 6555).
No translation overhead.
Gradual migration as IPv4 is slowly retired.

Pros: No translation, native performance, simple troubleshooting
Cons: Requires dual-stack on all devices, routers, firewalls
```

**Option 2: Tunneling**
```
6in4:    IPv6 packet encapsulated in IPv4 (Protocol 41)
6to4:    Automatic tunneling via anycast 192.88.99.1 (deprecated)
Teredo:  IPv6 via UDP for NAT traversal (Windows)
ISATAP:  Intra-site automatic tunnel (corporate)

Pros: Works over IPv4 infrastructure
Cons: MTU issues (1480 vs 1500), extra overhead, troubleshooting complexity
```

**Option 3: NAT64/DNS64 (IPv6-only clients → IPv4 servers)**
```
IPv6-only client → DNS64 synthesizes AAAA from A record
                 → Client sends to NAT64 prefix (64:ff9b::/96)
                 → NAT64 gateway translates IPv6→IPv4

Example:
  Client: AAAA query for www.example.com (IPv4-only: 93.184.216.34)
  DNS64: Returns 64:ff9b::5db8:d822 (synthesized AAAA)
  NAT64: Forwards as IPv4 to 93.184.216.34

Pros: IPv6-only networks can reach IPv4 internet
Cons: Translation overhead, ALG complexity, no IPv4 address needed
```

> 💡 **Best practice for enterprises:** Deploy dual-stack for all internal infrastructure. Use NAT64/DNS64 for IoT devices or greenfield IPv6-only segments. Avoid tunneling in production — MTU issues cause subtle failures.

---

## Step 2: IPv6 Address Types

```
Global Unicast (GUA):      2000::/3   → Public internet, routable globally
                           2001:db8::/32 → Documentation only (like 192.0.2.0/24)
                           
Unique Local (ULA):        fc00::/7   → Private (like RFC 1918)
                           fd00::/8   → Locally generated (fd + 40-bit random)

Link Local:                fe80::/10  → Per-interface, auto-configured, not routable

Multicast:                 ff00::/8   → One-to-many
  All nodes:               ff02::1
  All routers:             ff02::2
  OSPF routers:            ff02::5
  DHCPv6 servers/relays:   ff02::1:2

Loopback:                  ::1/128    → Equivalent to 127.0.0.1
Unspecified:               ::/128     → Equivalent to 0.0.0.0
```

**ULA vs GUA:**
- **ULA (fd00::/8):** Use for internal addressing. Won't accidentally route to internet. Stable even if provider changes.
- **GUA:** Use for internet-facing services. Provider-assigned (/48 per site minimum) or PI space.

---

## Step 3: Enterprise IPv6 Addressing Plan

**Allocation hierarchy:**
```
ISP allocation:     2001:db8::/32   (example, typically /32 from ISP)
                    or /48 per site from ARIN/RIPE PI space

Per site:           /48  → 65,536 /64 subnets per site
Per VLAN/subnet:    /64  → Required for SLAAC (stateless autoconfiguration)

Example for 6-site enterprise:
Site 0 (HQ):      2001:db8:0::/48
Site 1 (DC1):     2001:db8:1::/48
Site 2 (DC2):     2001:db8:2::/48
Site 3 (NYC):     2001:db8:3::/48
Site 4 (LON):     2001:db8:4::/48
Site 5 (SGP):     2001:db8:5::/48

Per-site VLAN assignment (using 4th hextet as VLAN ID):
HQ Management:    2001:db8:0:0a0a::/64   (VLAN 0x0A0A = 2570)
HQ Users:         2001:db8:0:0014::/64   (VLAN 20)
HQ Voice:         2001:db8:0:0064::/64   (VLAN 100)
HQ Servers:       2001:db8:0:00c8::/64   (VLAN 200)
```

**Why always /64 for subnets?**
1. SLAAC requires /64 (EUI-64 generates 64-bit interface ID)
2. Neighbor Discovery Protocol (NDP) assumptions
3. Consistent with RFC 4291 and 4862

---

## Step 4: DHCPv6 vs SLAAC

**SLAAC (Stateless Address Autoconfiguration):**
```
1. Router sends RA (Router Advertisement) with prefix (e.g., 2001:db8:1::/64)
2. Host generates interface ID:
   - EUI-64: derived from MAC address (privacy concern)
   - RFC 7217: stable random IID (privacy-safe, stable per network)
   - RFC 4941: temporary random IID (changes periodically)
3. Host forms address: prefix + IID
4. Host performs DAD (Duplicate Address Detection)
5. No server needed — fully distributed
```

**DHCPv6:**
```
Stateful:  Server assigns specific address + DNS + options (like DHCPv4)
Stateless: Server provides only DNS/options, SLAAC provides address

DHCPv6 server (ISC Kea):
subnet6 2001:db8:1::/64 {
  range6 2001:db8:1::1000 2001:db8:1::ffff;
  option dhcp6.name-servers 2001:db8::53;
  option dhcp6.domain-search "company.internal";
}
```

**RA flags control behavior:**
- `M flag (Managed)=1`: Use DHCPv6 for address (stateful)
- `O flag (Other)=1`: Use DHCPv6 for options only (stateless)
- `M=0, O=0`: Pure SLAAC, no DHCPv6

---

## Step 5: IPv6 Security Considerations

**Attack vectors unique to IPv6:**

**1. Rogue Router Advertisement (RA):**
- Attacker sends fake RA → hijacks default gateway
- Mitigation: **RA Guard** on switches (only allow RA from trusted ports)
```
! Cisco: RA Guard
ipv6 nd raguard policy BLOCK-RA
  device-role host
interface FastEthernet0/1
  ipv6 nd raguard attach-policy BLOCK-RA
```

**2. DAD (Duplicate Address Detection) DoS:**
- Attacker replies to every DAD probe → no host can configure
- Mitigation: **DAD snooping**, Secure ND (SEND) - RFC 3971

**3. Extension header abuse:**
- IPv6 extension headers can be used to bypass security
- Mitigation: Drop packets with unknown/excessive extension headers

**4. ICMPv6 filtering:**
- DON'T block all ICMPv6! NDP requires it.
- Essential ICMPv6 types to allow: 135 (NS), 136 (NA), 133 (RS), 134 (RA), 1 (unreachable), 2 (too big)

**5. Amplification via multicast:**
- Use `ipv6 multicast-routing` only where needed

---

## Step 6: IPv6 Transition Checklist

**Infrastructure readiness:**
- [ ] Routers: IPv6 routing (OSPF v3 or IS-IS + IPv6)
- [ ] Firewalls: IPv6 ruleset (separate from v4 rules)
- [ ] DNS: AAAA records, IPv6 recursive resolvers
- [ ] NTP: IPv6 time servers
- [ ] SNMP/monitoring: IPv6 management plane
- [ ] Load balancers: IPv6 VIPs
- [ ] Logs: Syslog infrastructure handles IPv6 source addresses

**Application readiness:**
- [ ] Bind to `::` (all interfaces) not `0.0.0.0`
- [ ] Parse IPv6 addresses (brackets in URLs: `http://[::1]/`)
- [ ] Database: IPv6-friendly column types (128-bit, not INT)
- [ ] Session tokens: Don't include IP (IPv6 privacy extensions change IPs)

---

## Step 7: Verification — IPv6 Address Planning Tool

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 iproute2 &&
python3 - << 'EOF'
import ipaddress
gua = ipaddress.IPv6Network('2001:db8::/32')
print(f'GUA prefix (example): {gua}')
sites = ['hq', 'dc1', 'dc2', 'branch-nyc', 'branch-lon', 'branch-sgp']
site_prefix = list(gua.subnets(new_prefix=48))
print(f\"{'Site':<15} {'/48 Prefix':<35} {'Subnets Available'}\")
print('-'*65)
for i, site in enumerate(sites):
    net = site_prefix[i]
    vlans = list(net.subnets(new_prefix=64))
    print(f'{site:<15} {str(net):<35} {len(vlans):,} /64 subnets')
print()
print('SLAAC: hosts auto-configure using EUI-64 or random IID')
print('DHCPv6: centralized address management + DNS options')
print()

# Show ULA generation
import random, hashlib
company_id = random.randint(0, 2**40)
ula_prefix = f'fd{company_id:010x}'[:10]
print(f'Generated ULA prefix: fd{company_id:010x}::/48')
print('(Unique per-network random allocation per RFC 4193)')
EOF
ip -6 addr show lo 2>/dev/null"
```

📸 **Verified Output:**
```
GUA prefix (example): 2001:db8::/32

Site            /48 Prefix                          Subnets Available
-----------------------------------------------------------------
hq              2001:db8::/48                       65,536 /64 subnets
dc1             2001:db8:1::/48                     65,536 /64 subnets
dc2             2001:db8:2::/48                     65,536 /64 subnets
branch-nyc      2001:db8:3::/48                     65,536 /64 subnets
branch-lon      2001:db8:4::/48                     65,536 /64 subnets
branch-sgp      2001:db8:5::/48                     65,536 /64 subnets

SLAAC: hosts auto-configure using EUI-64 or random IID
DHCPv6: centralized address management + DNS options

Generated ULA prefix: fda3f9c12d48::/48

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN
    inet6 ::1/128 scope host
```

---

## Step 8: Capstone — Enterprise IPv6 Migration Plan

**Scenario:** 5,000-user enterprise, currently IPv4-only, mandate to complete IPv6 in 18 months.

**Phase 1 (Months 1-3): Foundation**
```
- Obtain IPv6 block: Request /32 from ISP or /48 PI from ARIN
- Design addressing plan (as above)
- Enable IPv6 on core/distribution switches (OSPFv3)
- Configure RA Guard on all access switches
- Enable IPv6 on DNS servers (AAAA for internal services)
- Update firewall: add IPv6 policy (default deny, allow established)
```

**Phase 2 (Months 4-9): Dual-Stack Infrastructure**
```
- Enable dual-stack on all server VLANs
- Add AAAA records for all internal services
- Configure DHCPv6 or SLAAC per segment
- Update monitoring: add IPv6 to all SNMP/NetFlow collection
- Enable IPv6 on WAN circuits (ISP eBGP dual-stack)
```

**Phase 3 (Months 10-15): Applications & Endpoints**
```
- Roll out dual-stack to user VLANs (floor by floor)
- Test applications with IPv6-only clients (catch IPv4 assumptions)
- Update load balancers: add IPv6 VIPs
- Update Ansible inventory: add IPv6 management addresses
```

**Phase 4 (Months 16-18): Validation & Retirement**
```
- IPv6-only test segment: verify all apps work without IPv4
- Traffic analysis: measure IPv6 usage % per application
- Document IPv4 dependencies (ERP, legacy systems)
- Plan IPv4 retirement date for each system
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| Dual stack | Recommended migration path; both protocols simultaneously |
| /64 per subnet | Required for SLAAC; don't subnet smaller |
| /48 per site | Standard allocation; 65K /64 subnets |
| SLAAC | Host self-configures from RA prefix; no server needed |
| DHCPv6 | Central control + DNS options; use for managed environments |
| RA Guard | Block rogue RA attacks at access switch ports |
| ICMPv6 | Never block all ICMPv6; NDP depends on it |

**Next:** [Lab 11: DNS at Scale →](lab-11-dns-at-scale.md)
