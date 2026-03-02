# Cyber Security

![Cyber Security Hero](assets/hero-banner.svg)

> **Think like an attacker. Defend like an architect.**
> From packet analysis to red team operations — every concept is taught hands-on, with real tools in real environments.

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
      <td>Networking, cryptography, attack vectors, password security, social engineering. Build your mental model of how systems are broken — and protected.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚔️ Practitioner</strong></td>
      <td>OWASP Top 10 deep dives, web app penetration testing with Docker labs, Burp Suite, API security, session attacks. All 10 OWASP categories covered.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🔴 Advanced</strong></td>
      <td>Network pentesting, Active Directory attacks, privilege escalation, malware analysis, digital forensics, threat hunting, red team operations.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
    <tr>
      <td><strong>🏛️ Architect</strong></td>
      <td>Security architecture, zero trust design, SOC 2 / ISO 27001 / GDPR compliance, DevSecOps pipelines, enterprise risk management.</td>
      <td><a href="architect/">architect/</a></td>
    </tr>
  </tbody>
</table>

---

## 📋 Curriculum Overview

{% tabs %}
{% tab title="🌱 Foundations" %}
**Build your security foundation — understand before you attack**

| Labs | Topics |
|------|--------|
| 1–4  | OSI Model, TCP/IP fundamentals, DNS, cryptography basics |
| 5–8  | Hashing & integrity, PKI, SSL/TLS, common attack vectors |
| 9–12 | Linux security, network recon with nmap, password security, social engineering |
| 13–16 | Malware types, firewalls & IDS, VPN & tunneling, web security basics |
| 17–20 | Wireless security, incident classification, security tools, CTF intro |

**Tools:** nmap, openssl, hashcat concept, python3, curl
{% endtab %}

{% tab title="⚔️ Practitioner" %}
**Attack and defend real web applications with Docker labs**

| Labs | Topics |
|------|--------|
| 1–10  | OWASP A01–A10: every Top 10 vulnerability with live exploitation |
| 4     | Full web app pentest: SQLi, XSS, IDOR, Path Traversal, RCE, SSRF |
| 11–14 | Burp Suite, API security, authentication bypass techniques |
| 15–17 | File upload vulns, XXE injection, SSRF in cloud environments |
| 18–20 | Business logic flaws, session management, pentest report writing |

**Tools:** Docker, Burp Suite, curl, python3, OWASP ZAP
{% endtab %}

{% tab title="🔴 Advanced" %}
**Hands-on offensive security at the professional level**

| Labs | Topics |
|------|--------|
| 1–5  | Network pentesting, Active Directory attacks, Linux & Windows privesc |
| 6–8  | Lateral movement, persistence, C2 frameworks |
| 9–11 | Exfiltration, malware analysis, reverse engineering basics |
| 12–14 | Buffer overflow, disk forensics, memory forensics |
| 15–20 | SIEM, threat hunting, red/purple team, cloud security, containers |

**Tools:** Metasploit, mimikatz, volatility, wireshark, custom exploits
{% endtab %}

{% tab title="🏛️ Architect" %}
**Design and govern enterprise security at scale**

| Labs | Topics |
|------|--------|
| 1–5  | Security architecture, zero trust, IAM design, SIEM deployment |
| 6–10 | Threat modeling, risk assessment, security policy, SOC 2, ISO 27001 |
| 11–15 | GDPR, DevSecOps pipelines, Kubernetes security, secrets management, PKI |
| 16–20 | DDoS mitigation, bug bounty programs, security metrics, supply chain, capstone |

**Tools:** Terraform, Vault, OPA, Falco, STRIDE methodology
{% endtab %}
{% endtabs %}

---

## ⚡ Lab Format

Every lab follows a consistent, professional format:

{% hint style="success" %}
**Each lab includes:**
- 🎯 **Objective** — what you'll achieve and why it matters
- 📚 **Background** — the theory behind the attack or defense
- 🔬 **Step-by-step instructions** — real commands, real tools
- 📸 **Verified output** — actual terminal output captured from live runs
- 🛡️ **Mitigations** — how to fix or defend against each vulnerability
- 🚨 **Common mistakes** — what trips people up and how to avoid it
{% endhint %}

---

## 🏆 Certifications Aligned

| Certification | Relevant Levels |
|---|---|
| **CompTIA Security+** | Foundations + Practitioner |
| **CEH — Certified Ethical Hacker** | Practitioner + Advanced |
| **OSCP (OffSec)** | Advanced + Architect |
| **CISSP** | Architect |
| **AWS Security Specialty** | Advanced → Architect |
| **OWASP WSTG** | Practitioner (full coverage) |

---

## ⚠️ Legal & Ethical Notice

{% hint style="danger" %}
**All techniques in this curriculum are for authorized use only.**

- Only attack systems you own or have **explicit written permission** to test
- All Docker labs in this course use isolated localhost environments
- Never apply offensive techniques to production systems or third-party targets
- Unauthorized computer access is a criminal offense in most jurisdictions
{% endhint %}

---

## 🚀 Start Here

{% hint style="info" %}
**New to cybersecurity?** Begin with [Lab 1: OSI Model Deep Dive](foundations/labs/lab-01-osi-model-deep-dive.md) — no prior experience required.

**Have web dev experience?** Jump to [Lab 4: Web Application Security Testing](practitioner/labs/lab-04-web-application-security.md) — build and hack a Docker app in 90 minutes.

**Coming from IT/sysadmin?** Start at [Lab 9: Linux Security Basics](foundations/labs/lab-09-linux-security-basics.md).
{% endhint %}
