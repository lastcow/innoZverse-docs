# Linux

![Linux Hero](assets/hero-banner.svg)

> **In a world of GUIs, the command line is your superpower.**
> From your first `ls` to managing production clusters — every concept is taught hands-on, with real commands and verified output.

---

![Level Overview](assets/levels-diagram.svg)

---

## 🗺️ Choose Your Level

<table data-view="cards">
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th data-hidden data-card-target data-type="content-ref"></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>Terminal navigation, filesystem, permissions, text editing, users and packages. No prior experience needed — start from zero.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚙️ Practitioner</strong></td>
      <td>Shell scripting, process management, networking tools, SSH, cron automation, log management. Become a confident Linux user.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🔒 Advanced</strong></td>
      <td>Kernel tuning, security hardening, SELinux/AppArmor, LVM, storage, containers, namespaces, cgroups, systemd mastery.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
    <tr>
      <td><strong>🏛️ Architect</strong></td>
      <td>High availability, Ansible automation, Prometheus/Grafana/ELK observability, enterprise hardening and compliance at scale.</td>
      <td><a href="architect/">architect/</a></td>
    </tr>
  </tbody>
</table>

---

## 📋 Curriculum Overview

{% tabs %}
{% tab title="🌱 Foundations" %}
**Master the Linux filesystem and command line from scratch**

| Labs | Topics |
|------|--------|
| 1–5  | Intro to terminal, filesystem navigation, file operations, viewing files |
| 6–10 | Permissions (chmod/chown), special bits, text editors (vim & nano) |
| 11–15 | Users & groups, environment variables, shell config (.bashrc, .profile) |
| 16–20 | Package management (apt/yum), archiving (tar/zip), process basics (ps, kill) |

**Tools:** bash, vim, nano, apt, tar, grep, find
{% endtab %}

{% tab title="⚙️ Practitioner" %}
**Automate tasks and administer systems confidently**

| Labs | Topics |
|------|--------|
| 1–5  | Shell scripting: variables, conditionals, loops, functions, arguments |
| 6–10 | Process management, signals, background jobs, cron & at scheduling |
| 11–15 | Networking: ip, ss, curl, wget, netstat, firewall with ufw/iptables |
| 16–20 | SSH key auth, log management (journalctl), system monitoring, performance |

**Tools:** bash scripts, cron, ssh, iptables, ufw, systemctl, journalctl
{% endtab %}

{% tab title="🔒 Advanced" %}
**Tune, harden, and manage complex Linux systems**

| Labs | Topics |
|------|--------|
| 1–5  | Kernel parameters (sysctl), performance profiling (perf, strace, lsof) |
| 6–10 | Security hardening, SELinux/AppArmor policies, auditd, fail2ban |
| 11–15 | LVM, RAID, filesystem tuning (ext4/xfs/btrfs), disk encryption (LUKS) |
| 16–20 | Linux containers, namespaces, cgroups, Docker internals, systemd units |

**Tools:** sysctl, perf, strace, auditd, lvm, cryptsetup, nsenter, systemd
{% endtab %}

{% tab title="🏛️ Architect" %}
**Design and operate enterprise Linux infrastructure**

| Labs | Topics |
|------|--------|
| 1–5  | High availability with Pacemaker/Corosync, load balancing, clustering |
| 6–10 | Infrastructure as Code: Ansible playbooks, roles, inventory, vault |
| 11–15 | Observability: Prometheus metrics, Grafana dashboards, ELK log pipeline |
| 16–20 | Enterprise hardening, CIS benchmarks, compliance automation, large-scale ops |

**Tools:** Ansible, Prometheus, Grafana, Elasticsearch, Pacemaker, HAProxy
{% endtab %}
{% endtabs %}

---

## ⚡ Lab Format

Every lab is production-quality with verified output — not just theory:

{% hint style="success" %}
**Each lab includes:**
- 🎯 **Objective** — clear goal and real-world relevance
- 📚 **Background** — the WHY, not just the HOW
- 🔬 **Step-by-step instructions** — real commands on Ubuntu 22.04
- 📸 **Verified output** — actual terminal results captured from live runs
- 💡 **Explanations** — what each flag and output means
- 🚨 **Common mistakes** — what to watch out for
{% endhint %}

---

## 🏆 Certifications Aligned

| Certification | Relevant Levels |
|---|---|
| **CompTIA Linux+** | Foundations + Practitioner |
| **LPIC-1** | Foundations + Practitioner |
| **LPIC-2** | Advanced |
| **RHCSA (Red Hat)** | Practitioner + Advanced |
| **RHCE (Red Hat)** | Advanced + Architect |
| **Linux Foundation LFCS** | Foundations + Practitioner |
| **CKA (Kubernetes Admin)** | Advanced + Architect |

---

## 🚀 Start Here

{% hint style="info" %}
**Never used Linux before?** Begin at [Lab 1: Introduction to the Terminal](foundations/labs/lab-01-intro-to-terminal.md) — every command is explained from first principles.

**Coming from Windows/Mac?** Start at [Lab 2: Navigating the Filesystem](foundations/labs/lab-02-filesystem-navigation.md) to understand how Linux organizes files differently.

**Already comfortable in the terminal?** Jump to [Lab 1: Shell Scripting Fundamentals](practitioner/labs/lab-01-shell-scripting.md) to level up your automation skills.
{% endhint %}

{% hint style="warning" %}
**Environment:** All labs are tested on **Ubuntu 22.04 LTS**. Use WSL2 on Windows, a VM, or any Ubuntu-based cloud instance. Commands may vary slightly on RHEL/CentOS.
{% endhint %}
