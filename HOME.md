---
description: >-
  480+ verified, hands-on labs across Linux, Cybersecurity, Networking,
  Database, Programming, and AI — built for engineers who learn by doing.
cover: .gitbook/assets/home-hero.svg
coverY: 0
layout:
  cover:
    visible: true
    size: hero
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: true
  outline:
    visible: false
  pagination:
    visible: false
---

# innoZverse Documentation

> **The practitioner's knowledge base.** Every command verified. Every lab tested. No fluff.

---

## Choose Your Learning Path

<table data-view="cards">
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th data-hidden data-card-cover data-type="files"></th>
      <th data-hidden data-card-target data-type="content-ref"></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🐧 Linux</strong></td>
      <td>Master the command line from first boot to kernel internals. 80 verified labs across 4 levels.</td>
      <td></td>
      <td><a href="linux/README.md">linux/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🔐 Cybersecurity</strong></td>
      <td>Real pentest labs with two-container Kali → victim architecture. OWASP Top 10 and beyond. 60 labs.</td>
      <td></td>
      <td><a href="cyber-security/README.md">cyber-security/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🌐 Networking</strong></td>
      <td>Protocols, routing, firewalls, and packet analysis from OSI Layer 1 to BGP. 80 labs.</td>
      <td></td>
      <td><a href="networking/README.md">networking/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🗄️ Database</strong></td>
      <td>SQL, NoSQL, query optimisation, replication, and data engineering pipelines. 80 labs.</td>
      <td></td>
      <td><a href="database/README.md">database/README.md</a></td>
    </tr>
    <tr>
      <td><strong>💻 Programming</strong></td>
      <td>Python, JavaScript, Java, Go, PHP, TypeScript, HTML/CSS — foundations through advanced. 105+ labs.</td>
      <td></td>
      <td><a href="programming/README.md">programming/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🤖 AI & Machine Learning</strong></td>
      <td>From AI history to enterprise security platforms. 60 verified labs with Docker-tested code.</td>
      <td></td>
      <td><a href="artificial-intelligent-ai/README.md">artificial-intelligent-ai/README.md</a></td>
    </tr>
  </tbody>
</table>

---

## How Labs Are Structured

Every lab in innoZverse follows the same format so you always know what to expect.

{% tabs %}
{% tab title="🎯 Objective" %}
Each lab starts with a clear, one-paragraph objective:

- **What** you will build or demonstrate
- **Why** it matters in the real world
- **Time estimate** and **difficulty level**
- **Docker image** or environment required

No ambiguity. You know exactly what you're getting into before writing a single command.
{% endtab %}

{% tab title="🔬 Verified Steps" %}
Every step has been executed and the output captured:

```
**📸 Verified Output:**
```text
root@lab:~# nmap -sV 172.20.0.2
Starting Nmap 7.94 ...
PORT     STATE SERVICE VERSION
80/tcp   open  http    Werkzeug/3.0.1 Python/3.11.9
443/tcp  open  ssl/http Werkzeug/3.0.1
```
```

If the command doesn't produce that output, something is wrong — and you can debug from a known baseline.
{% endtab %}

{% tab title="💡 Callouts" %}
Throughout each lab you'll find:

> 💡 **Tips** — better ways to do what you just did

{% hint style="info" %}
**Info** — background context and "why this works"
{% endhint %}

{% hint style="warning" %}
**Warning** — common mistakes and gotchas
{% endhint %}

{% hint style="danger" %}
**Danger** — security implications or destructive commands
{% endhint %}
{% endtab %}

{% tab title="🏁 Capstone" %}
Step 8 of every lab is a **capstone challenge** that combines everything from steps 1–7 into a realistic scenario:

- Security labs: full attack → detect → remediate chain
- AI labs: end-to-end pipeline from raw data to production endpoint
- Programming labs: working application with tests
- Database labs: production schema with indexing and query optimisation

The capstone is where the learning sticks.
{% endtab %}
{% endtabs %}

---

## Quick Start

{% hint style="success" %}
**No environment setup required for most labs.** Pull the Docker image and start immediately.
{% endhint %}

```bash
# Pick your domain and pull the image
docker pull zchencow/innozverse-ai:latest        # AI/ML labs
docker pull zchencow/innozverse-cybersec:latest  # Cybersecurity labs
docker pull zchencow/innozverse-kali:latest      # Pentest attacker

# Start an interactive session
docker run -it --rm zchencow/innozverse-ai:latest bash
```

All images are hosted on Docker Hub under `zchencow/innozverse-*` and require no account or license.

---

## Lab Catalogue

| Domain | Foundations | Practitioner | Advanced | Architect | Total |
|--------|:-----------:|:------------:|:--------:|:---------:|:-----:|
| 🐧 Linux | 20 | 20 | 20 | 20 | **80** |
| 🔐 Cybersecurity | 20 | 20 | 20 | — | **60** |
| 🌐 Networking | 20 | 20 | 20 | 20 | **80** |
| 🗄️ Database | 20 | 20 | 20 | 20 | **80** |
| 💻 Programming | 15×7 | 15×7 | — | — | **105+** |
| 🤖 AI & ML | 20 | 20 | 20 | — | **60** |
| **Total** | | | | | **465+** |

---

## The Four Levels

{% tabs %}
{% tab title="🌱 Foundations" %}
**Who it's for:** Beginners and career-switchers

**What you'll learn:**
- Core concepts explained from first principles
- Industry terminology with real-world analogies
- Hands-on labs with guided walkthroughs
- No prior experience required

**Example labs:**
- Linux: File permissions, users, and the shell
- AI: How LLMs actually work (no jargon)
- Cybersecurity: Setting up your first Kali environment
{% endtab %}

{% tab title="⚔️ Practitioner" %}
**Who it's for:** Engineers with 1–3 years of experience

**What you'll learn:**
- Industry-standard tools and workflows
- Real-world scenarios and troubleshooting
- Production patterns and best practices
- OWASP Top 10, MITRE ATT&CK, CVE analysis

**Example labs:**
- Cybersecurity: SQL injection in a live Flask app
- AI: Deploy an ML model as a FastAPI endpoint
- Linux: Kernel tuning for high-throughput workloads
{% endtab %}

{% tab title="🔴 Advanced" %}
**Who it's for:** Senior engineers and specialists

**What you'll learn:**
- Deep internals and low-level mechanics
- Complex architectures and system design
- Research-level techniques with practical application
- Building tools, not just using them

**Example labs:**
- AI: Federated learning with differential privacy
- Cybersecurity: Lateral movement detection with GNNs
- Linux: Custom eBPF programs for observability
{% endtab %}

{% tab title="🏛️ Architect" %}
**Who it's for:** Tech leads, architects, and senior ICs

**What you'll learn:**
- System design at scale (millions of events/day)
- Trade-off analysis and decision frameworks
- Cross-domain integration (security + AI + networking)
- Production operations and reliability engineering

**Example labs:**
- Database: Designing a multi-region, active-active cluster
- Linux: Building a zero-trust infrastructure
{% endtab %}
{% endtabs %}

---

## Built for Real Engineers

{% hint style="info" %}
**Verification-first design**: Every command in every lab has been executed on Ubuntu 22.04 inside Docker. The output you see is the output you get.
{% endhint %}

- **No vendor lock-in** — open-source tools and freely available Docker images
- **No subscriptions** — all content is free and open on GitHub
- **No stale tutorials** — labs are tested against current tool versions
- **No hand-waving** — if a concept is hard, we explain it until it's not

---

## Certification Alignment

Labs map to industry certifications across all domains:

| Domain | Certifications |
|--------|---------------|
| Linux | LPIC-1/2, RHCSA, CompTIA Linux+ |
| Cybersecurity | OSCP, CEH, CompTIA Security+, eJPT |
| Networking | CCNA, CompTIA Network+, JNCIA |
| Database | Oracle OCA, MongoDB Associate, PostgreSQL Certified |
| AI/ML | AWS ML Specialty, Google Professional ML Engineer, Azure AI Engineer |
| Programming | AWS Developer, GCP ACE, Azure AZ-204 |

---

## GitHub & Contributing

All lab content is open source.

[![GitHub](https://img.shields.io/badge/GitHub-lastcow%2FinnoZverse--docs-blue?logo=github)](https://github.com/lastcow/innoZverse-docs)

Found a bug? Command doesn't work? Open an issue or submit a PR — verified corrections are merged within 48 hours.

---

*innoZverse — Learn by doing. Verify everything.*
