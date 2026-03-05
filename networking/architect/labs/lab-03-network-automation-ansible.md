# Lab 03: Network Automation with Ansible

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Network automation eliminates manual, error-prone CLI changes and enables network-as-code principles. This lab covers the Ansible ecosystem for multi-vendor network automation, from simple playbooks to Nornir-based frameworks.

---

## Objectives
- Understand Ansible network collection architecture
- Compare connection types: network_cli, netconf, httpapi
- Use Netmiko for SSH-based automation
- Use NAPALM for multi-vendor abstraction
- Apply NETCONF/YANG for structured configuration
- Implement network-as-code principles

---

## Step 1: Ansible Network Architecture

Ansible for network uses **collections** that contain modules, plugins, and roles for specific vendors.

**Key collections:**
| Collection | Vendor | Connection |
|-----------|--------|-----------|
| `ansible.netcommon` | Any | Base network utilities |
| `cisco.ios` | Cisco IOS/IOS-XE | network_cli |
| `cisco.nxos` | Cisco NX-OS | network_cli / httpapi |
| `arista.eos` | Arista EOS | network_cli / httpapi |
| `junipernetworks.junos` | Juniper JunOS | netconf |
| `cisco.iosxr` | Cisco IOS-XR | network_cli / netconf |
| `ansible.netcommon` | Generic | netconf / restconf |

**Install collections:**
```bash
ansible-galaxy collection install cisco.ios arista.eos junipernetworks.junos
```

---

## Step 2: Connection Types

**network_cli** — SSH-based, parses CLI output
```yaml
vars:
  ansible_connection: ansible.netcommon.network_cli
  ansible_network_os: cisco.ios.ios
  ansible_user: admin
  ansible_password: "{{ vault_password }}"
  ansible_become: yes
  ansible_become_method: enable
```

**netconf** — XML-based, structured, preferred for Juniper/modern IOS-XE
```yaml
vars:
  ansible_connection: ansible.netcommon.netconf
  ansible_network_os: junipernetworks.junos.junos
  ansible_port: 830
```

**httpapi** — REST API-based, fast, modern (NX-OS, EOS)
```yaml
vars:
  ansible_connection: ansible.netcommon.httpapi
  ansible_network_os: arista.eos.eos
  ansible_httpapi_use_ssl: true
  ansible_httpapi_validate_certs: false
```

> 💡 **Best practice:** Use netconf/httpapi over network_cli whenever the device supports it. CLI screen-scraping is fragile; structured protocols are reliable.

---

## Step 3: Writing Network Playbooks

**Inventory file (`inventory.yml`):**
```yaml
all:
  children:
    cisco_routers:
      hosts:
        router-1:
          ansible_host: 192.168.1.1
        router-2:
          ansible_host: 192.168.1.2
      vars:
        ansible_connection: ansible.netcommon.network_cli
        ansible_network_os: cisco.ios.ios
    arista_switches:
      hosts:
        switch-1:
          ansible_host: 192.168.2.1
      vars:
        ansible_connection: ansible.netcommon.httpapi
        ansible_network_os: arista.eos.eos
```

**Configure VLAN playbook:**
```yaml
---
- name: Configure VLANs on Cisco IOS
  hosts: cisco_routers
  gather_facts: no
  tasks:
    - name: Create production VLANs
      cisco.ios.ios_vlans:
        config:
          - vlan_id: 10
            name: management
            state: active
          - vlan_id: 20
            name: users
            state: active
        state: merged

    - name: Configure interface description
      cisco.ios.ios_interfaces:
        config:
          - name: GigabitEthernet0/1
            description: "Uplink to Distribution"
            enabled: true
        state: merged

    - name: Save running config
      cisco.ios.ios_command:
        commands: write memory
```

**Idempotency test:**
```bash
ansible-playbook -i inventory.yml configure_vlans.yml --check --diff
```

---

## Step 4: Netmiko — SSH Automation

Netmiko simplifies SSH connections to 60+ network device types.

```python
from netmiko import ConnectHandler

device = {
    'device_type': 'cisco_ios',
    'host': '192.168.1.1',
    'username': 'admin',
    'password': 'secret',
    'secret': 'enable_secret',
}

with ConnectHandler(**device) as conn:
    conn.enable()
    
    # Send commands
    output = conn.send_command('show ip route')
    print(output)
    
    # Send config commands
    config_cmds = [
        'interface GigabitEthernet0/1',
        'description Uplink to Core',
        'ip address 10.0.1.1 255.255.255.252',
    ]
    conn.send_config_set(config_cmds)
    
    # Use TextFSM for structured output
    routes = conn.send_command('show ip route', use_textfsm=True)
    for route in routes:
        print(f"Network: {route['network']} via {route['nexthop']}")
```

**Multi-vendor example:**
```python
vendors = [
    {'device_type': 'cisco_ios',    'host': '10.0.1.1'},
    {'device_type': 'arista_eos',   'host': '10.0.1.2'},
    {'device_type': 'juniper_junos','host': '10.0.1.3'},
]
for v in vendors:
    v.update({'username': 'admin', 'password': 'secret'})
    with ConnectHandler(**v) as conn:
        print(conn.send_command('show version'))
```

---

## Step 5: NAPALM — Multi-Vendor Abstraction

NAPALM provides a unified API across Cisco IOS, NX-OS, EOS, Junos, and more.

```python
from napalm import get_network_driver

# Connect to Arista EOS
driver = get_network_driver('eos')
device = driver('192.168.1.1', 'admin', 'secret')
device.open()

# Get structured facts
facts = device.get_facts()
print(f"Vendor: {facts['vendor']}, OS: {facts['os_version']}")

# Get BGP neighbors
bgp = device.get_bgp_neighbors()
for peer, data in bgp['global']['peers'].items():
    print(f"Peer: {peer}, State: {data['description']}")

# Load and commit config
device.load_merge_candidate(filename='new_config.cfg')
diff = device.compare_config()
print(f"Config diff:\n{diff}")
device.commit_config()  # or device.discard_config()

device.close()
```

**NAPALM compliance reports:**
```python
# Check if device matches compliance report
report = device.compliance_report('compliance_template.yaml')
print(report['complies'])  # True/False
```

---

## Step 6: YANG / NETCONF / RESTCONF

Modern devices expose structured APIs for configuration management.

**YANG model hierarchy:**
```
module ietf-interfaces {
  container interfaces {
    list interface {
      key "name";
      leaf name { type string; }
      leaf description { type string; }
      container ipv4 {
        list address {
          key "ip";
          leaf ip { type ipv4-address; }
          leaf prefix-length { type uint8; range "0..32"; }
        }
      }
    }
  }
}
```

**NETCONF via Python (ncclient):**
```python
from ncclient import manager

with manager.connect(
    host='192.168.1.1', port=830,
    username='admin', password='secret',
    hostkey_verify=False
) as m:
    # Get running config
    config = m.get_config(source='running')
    print(config.xml)
    
    # Edit config using YANG
    edit_config = """
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>GigabitEthernet1</name>
          <description>Automated by NETCONF</description>
        </interface>
      </interfaces>
    </config>"""
    m.edit_config(target='running', config=edit_config)
```

**RESTCONF (HTTP-based):**
```bash
# GET interface config
curl -X GET \
  "https://router/restconf/data/ietf-interfaces:interfaces" \
  -H "Accept: application/yang-data+json" \
  -u admin:secret | python3 -m json.tool
```

---

## Step 7: Verification

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 python3-pip &&
pip3 install netmiko napalm 2>/dev/null | grep 'Successfully installed' | head -1
python3 -c 'import netmiko; print(\"netmiko\", netmiko.__version__)'
python3 -c 'import napalm; print(\"napalm\", napalm.__version__)'
"
```

📸 **Verified Output:**
```
Successfully installed netmiko-4.6.0 napalm-5.1.0 ...
netmiko 4.6.0
napalm 5.1.0
```

**Test playbook targeting localhost:**
```bash
cat > /tmp/test_playbook.yml << 'EOF'
---
- name: Network Automation Test
  hosts: localhost
  gather_facts: yes
  tasks:
    - name: Show Python version
      command: python3 --version
      register: pyver
    - name: Print result
      debug:
        msg: "Python: {{ pyver.stdout }} | Netmiko ready for SSH automation"
EOF
ansible-playbook /tmp/test_playbook.yml
```

```
PLAY [Network Automation Test] *************************************
TASK [Show Python version] *****************************************
changed: [localhost]
TASK [Print result] ************************************************
ok: [localhost] => {
    "msg": "Python: Python 3.10.12 | Netmiko ready for SSH automation"
}
PLAY RECAP *********************************************************
localhost: ok=2  changed=1  unreachable=0  failed=0
```

---

## Step 8: Capstone — Network-as-Code Pipeline

**Scenario:** Design a complete network-as-code pipeline for a 100-device network.

**Pipeline design:**

```
Git Repository
  └── network-configs/
      ├── inventory/
      │   ├── production.yml
      │   └── staging.yml
      ├── group_vars/
      │   ├── all.yml          (common vars)
      │   ├── cisco_ios.yml    (IOS-specific)
      │   └── arista_eos.yml   (EOS-specific)
      ├── host_vars/
      │   └── router-1.yml     (device-specific)
      ├── playbooks/
      │   ├── configure_vlans.yml
      │   ├── configure_routing.yml
      │   └── backup_configs.yml
      └── templates/
          ├── ios_base.j2
          └── eos_base.j2

CI/CD Pipeline:
  1. Developer commits config change to Git
  2. CI: ansible-playbook --check --diff (dry run)
  3. Peer review (pull request)
  4. CD: Deploy to staging environment
  5. Automated testing (ping tests, route verification)
  6. Promote to production
  7. Rollback on failure (git revert + replay)
```

**Key principles:**
- **Idempotency:** Running the playbook twice produces the same result
- **Version control:** Every change is a git commit with author + message
- **Dry-run first:** Always use `--check` before applying to production
- **Vault for secrets:** `ansible-vault encrypt group_vars/all/vault.yml`
- **Tags for scope:** `ansible-playbook site.yml --tags vlans,routing`

---

## Summary

| Tool | Use Case |
|------|----------|
| Ansible + cisco.ios | Multi-device IOS config automation |
| Ansible + netconf | Structured YANG-based config |
| Netmiko | SSH automation, TextFSM parsing |
| NAPALM | Multi-vendor abstraction, compliance reports |
| NETCONF/ncclient | Direct YANG config via XML |
| RESTCONF | REST API for network devices |
| Git + CI/CD | Network-as-code pipeline |

**Next:** [Lab 04: BGP Enterprise Design →](lab-04-bgp-enterprise-design.md)
