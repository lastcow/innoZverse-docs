---
description: 465+ verified, hands-on labs across Linux, Cybersecurity, Networking, Database, Programming, and AI — built for engineers who learn by doing.
cover: .gitbook/assets/home-hero.svg
coverY: 0
layout:
  cover:
    visible: true
    size: hero
  title:
    visible: false
  description:
    visible: false
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
---

# innoZverse Docs

<div align="center">

## The practitioner's knowledge base

**465+ verified labs. Every command tested. No fluff.**\
Pick a domain below and start learning.

</div>

---

## Learning Domains

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
      <td>From first boot to kernel internals. Shell scripting, system administration, performance tuning, and eBPF. 80 verified labs across 4 levels.</td>
      <td><a href=".gitbook/assets/card-linux.svg">card-linux.svg</a></td>
      <td><a href="linux/README.md">linux/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🔐 Cybersecurity</strong></td>
      <td>Real pentest labs with live Kali → victim containers. OWASP Top 10, advanced exploitation, threat hunting, and digital forensics. 60 labs.</td>
      <td><a href=".gitbook/assets/card-cybersecurity.svg">card-cybersecurity.svg</a></td>
      <td><a href="cyber-security/README.md">cyber-security/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🌐 Networking</strong></td>
      <td>OSI model through BGP routing. Packet analysis, firewalls, VPNs, SDN, and network automation. 80 labs from CCNA to architect level.</td>
      <td><a href=".gitbook/assets/card-networking.svg">card-networking.svg</a></td>
      <td><a href="networking/README.md">networking/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🗄️ Database</strong></td>
      <td>SQL mastery, NoSQL, query optimisation, replication, sharding, and data pipelines. PostgreSQL, MySQL, MongoDB, Redis. 80 labs.</td>
      <td><a href=".gitbook/assets/card-database.svg">card-database.svg</a></td>
      <td><a href="database/README.md">database/README.md</a></td>
    </tr>
    <tr>
      <td><strong>💻 Programming</strong></td>
      <td>Python, JavaScript, Java, Go, PHP, TypeScript, HTML/CSS — foundations to advanced. 105+ Docker-verified labs across 7 languages.</td>
      <td><a href=".gitbook/assets/card-programming.svg">card-programming.svg</a></td>
      <td><a href="programming/README.md">programming/README.md</a></td>
    </tr>
    <tr>
      <td><strong>🤖 AI & Machine Learning</strong></td>
      <td>AI history to enterprise security platforms. GNNs, federated learning, LLM security, RL agents, and MLOps. 60 Docker-tested labs.</td>
      <td><a href=".gitbook/assets/card-ai.svg">card-ai.svg</a></td>
      <td><a href="artificial-intelligent-ai/README.md">artificial-intelligent-ai/README.md</a></td>
    </tr>
  </tbody>
</table>

---

## Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
Pull any image and start immediately — no account or licence required.

```bash
# AI & ML labs
docker pull zchencow/innozverse-ai:latest
docker run -it --rm zchencow/innozverse-ai:latest bash

# Cybersecurity labs (victim server)
docker pull zchencow/innozverse-cybersec:latest

# Pentest attacker (Kali Linux)
docker pull zchencow/innozverse-kali:latest
```
{% endtab %}

{% tab title="🐧 Linux / macOS" %}
Most labs run on any Ubuntu 22.04 or macOS system with Python 3.10+.

```bash
# Clone the lab content
git clone https://github.com/lastcow/innoZverse-docs.git
cd innoZverse-docs

# Follow the lab README for environment setup
# Most labs specify: docker run ... or python3 -c "..."
```
{% endtab %}

{% tab title="☁️ Cloud (No local setup)" %}
Run labs in your browser using GitHub Codespaces:

1. Open [github.com/lastcow/innoZverse-docs](https://github.com/lastcow/innoZverse-docs)
2. Click **Code → Codespaces → Create codespace**
3. Docker is pre-installed — pull any `zchencow/innozverse-*` image

Free tier: 60 hours/month.
{% endtab %}
{% endtabs %}

---

## Four Levels, One Path

<table data-view="cards">
  <thead>
    <tr>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>Core concepts from first principles. Guided walkthroughs. No prior experience required. Perfect for career-switchers and students.</td>
    </tr>
    <tr>
      <td><strong>⚔️ Practitioner</strong></td>
      <td>Industry-standard tools and production patterns. Real-world scenarios. Maps to OSCP, CCNA, AWS certifications. 1–3 years experience recommended.</td>
    </tr>
    <tr>
      <td><strong>🔴 Advanced</strong></td>
      <td>Deep internals, complex architectures, research-level techniques. Build tools, not just use them. Senior engineers and specialists.</td>
    </tr>
    <tr>
      <td><strong>🏛️ Architect</strong></td>
      <td>System design at scale. Trade-off frameworks. Cross-domain integration. For tech leads designing production infrastructure.</td>
    </tr>
  </tbody>
</table>

---

## What Makes These Labs Different

{% hint style="success" %}
**Every command is verified.** The output shown in each lab is real output from a real execution. If yours differs, something is genuinely wrong — and that's a useful debugging exercise.
{% endhint %}

{% hint style="info" %}
**No setup hell.** Labs use pre-built Docker images. One `docker pull` and you're running code, not installing dependencies.
{% endhint %}

{% hint style="info" %}
**Security-themed throughout.** Even non-security labs (Python, databases, AI) use cybersecurity datasets and scenarios — network intrusion detection, malware classification, SIEM log analysis.
{% endhint %}

---

## Lab Count by Domain

| Domain | Foundations | Practitioner | Advanced | Architect | Total |
|--------|:-----------:|:------------:|:--------:|:---------:|:-----:|
| 🐧 Linux | 20 | 20 | 20 | 20 | **80** |
| 🔐 Cybersecurity | 20 | 20 | 20 | — | **60** |
| 🌐 Networking | 20 | 20 | 20 | 20 | **80** |
| 🗄️ Database | 20 | 20 | 20 | 20 | **80** |
| 💻 Programming | 105+ | — | — | — | **105+** |
| 🤖 AI & ML | 20 | 20 | 20 | — | **60** |
| **Total** | | | | | **465+** |

---

## Open Source

All content is free and open on GitHub. Found a bug or a broken command? Open an issue — verified fixes are merged within 48 hours.

[**github.com/lastcow/innoZverse-docs →**](https://github.com/lastcow/innoZverse-docs)

---

<div align="center">

*innoZverse — Learn by doing. Verify everything.*

</div>
