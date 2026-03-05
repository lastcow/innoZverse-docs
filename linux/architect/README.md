# 🏛️ Linux Architect

**20 labs · Ubuntu 22.04 · Docker-verified**

Design and operate enterprise Linux infrastructure. Prerequisites: Linux Advanced.

---

## Labs

| # | Lab | Topics |
|---|-----|--------|
| 01 | [High Availability & Pacemaker/Corosync](labs/lab-01-high-availability-pacemaker-corosync.md) | HA concepts, CRM, quorum, fencing |
| 02 | [HAProxy — Load Balancing](labs/lab-02-haproxy-load-balancing.md) | frontends, backends, health checks, ACLs |
| 03 | [Keepalived — VRRP Failover](labs/lab-03-keepalived-vrrp-failover.md) | VRRP, virtual IPs, MASTER/BACKUP |
| 04 | [Linux Clustering & Shared Storage](labs/lab-04-linux-clustering-shared-storage.md) | GFS2, DRBD, DLM, fencing devices |
| 05 | [Capstone — HA Two-Node Cluster](labs/lab-05-capstone-ha-two-node-cluster.md) | full Pacemaker + HAProxy cluster runbook |
| 06 | [Ansible Foundations](labs/lab-06-ansible-foundations.md) | inventory, ad-hoc, first playbook |
| 07 | [Ansible Roles & Galaxy](labs/lab-07-ansible-roles-galaxy.md) | role structure, dependencies, galaxy |
| 08 | [Ansible Variables, Templates & Handlers](labs/lab-08-ansible-variables-templates-handlers.md) | Jinja2, handlers, register, when |
| 09 | [Ansible Vault — Secrets Management](labs/lab-09-ansible-vault-secrets.md) | vault create/encrypt, vault IDs, CI/CD |
| 10 | [Ansible Capstone — Server Provisioning](labs/lab-10-ansible-capstone-server-provisioning.md) | full 6-play provisioning playbook |
| 11 | [Prometheus — Metrics & Alerting](labs/lab-11-prometheus-metrics-alerting.md) | PromQL, alertmanager, recording rules |
| 12 | [Grafana — Dashboards](labs/lab-12-grafana-dashboards.md) | data sources, panels, provisioning |
| 13 | [Elasticsearch & Kibana — Log Indexing](labs/lab-13-elasticsearch-kibana-log-indexing.md) | indices, query DSL, ILM |
| 14 | [Logstash & Filebeat — Log Pipeline](labs/lab-14-logstash-filebeat-pipeline.md) | grok, mutate, filebeat modules |
| 15 | [Capstone — Full Observability Stack](labs/lab-15-capstone-observability-stack.md) | Prometheus + ELK + SLO/error budget |
| 16 | [CIS Benchmark Hardening](labs/lab-16-cis-benchmark-hardening.md) | Lynis audit, Level 1/2, scoring |
| 17 | [OpenSCAP Compliance Automation](labs/lab-17-openscap-compliance-automation.md) | XCCDF, OVAL, HTML reports, remediation |
| 18 | [Enterprise Audit & Reporting](labs/lab-18-enterprise-audit-reporting.md) | auditd rules, AIDE integrity, reports |
| 19 | [Large-Scale Patch Management](labs/lab-19-large-scale-patch-management.md) | unattended-upgrades, canary deployment |
| 20 | [Capstone — Enterprise Hardened HA Server](labs/lab-20-capstone-enterprise-hardened-ha-server.md) | all 4 levels combined, JSON scoring |

---

**Start here →** [Lab 01: High Availability & Pacemaker/Corosync](labs/lab-01-high-availability-pacemaker-corosync.md)
