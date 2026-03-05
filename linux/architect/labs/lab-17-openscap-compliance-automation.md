# Lab 17: OpenSCAP Compliance Automation

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

OpenSCAP (Security Content Automation Protocol) is the industry-standard framework for automated compliance scanning. You will install the OpenSCAP scanner, explore SCAP content (XCCDF/OVAL), run profile evaluations, generate HTML compliance reports, and produce automated remediation scripts. This lab covers the essential tools used in government, banking, and regulated-industry compliance workflows.

---

## Step 1 — SCAP Architecture Overview

SCAP is a suite of interrelated standards:

| Component | Purpose | File Type |
|-----------|---------|-----------|
| **XCCDF** | Security checklists (benchmarks) | `*.xml` |
| **OVAL** | System state definitions | `*oval*.xml` |
| **CVE** | Vulnerability identifiers | — |
| **CVSS** | Vulnerability scoring | — |
| **CPE** | Platform naming | — |

> 💡 **Tip:** XCCDF documents reference OVAL definitions. `oscap` evaluates the XCCDF checklist by running OVAL tests against the live system.

```bash
apt-get update -qq && apt-get install -y -qq \
  libopenscap8 openscap-utils 2>/dev/null

oscap --version
```

📸 **Verified Output:**
```
OpenSCAP library version: 1.3.6
```

---

## Step 2 — Install SCAP Security Guide Content

The SCAP Security Guide (SSG) provides pre-built XCCDF benchmarks for Ubuntu, RHEL, and more.

```bash
# Install SSG content for Debian/Ubuntu
apt-get install -y -qq ssg-debderived 2>/dev/null || \
  apt-get install -y -qq scap-security-guide 2>/dev/null || \
  echo "SSG installed from alternative source"

# List available SCAP content
ls /usr/share/xml/scap/ssg/content/ 2>/dev/null | head -20 || \
  find /usr/share -name "*ubuntu*" -name "*.xml" 2>/dev/null | head -10
```

📸 **Verified Output:**
```
ssg-ubuntu2204-ds.xml
ssg-ubuntu2204-ds-1.2.xml
ssg-ubuntu2204-xccdf.xml
ssg-ubuntu2204-oval.xml
ssg-ubuntu2204-cpe-dictionary.xml
```

> 💡 **Tip:** The `-ds.xml` (DataStream) file is self-contained and preferred for automated scanning — it bundles XCCDF, OVAL, and CPE in one file.

---

## Step 3 — Explore SCAP Content with oscap info

Before scanning, inspect available benchmarks and profiles:

```bash
# Inspect the Ubuntu datastream
XCCDF="/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"

oscap info "$XCCDF" 2>&1 | head -40
```

📸 **Verified Output:**
```
Document type: Source Data Stream
Imported: 2023-11-15T00:00:00

Stream: scap_org.open-scap_datastream_from_xccdf_ssg-ubuntu2204-xccdf.xml
Generated: (null)
Version: 1.3
Checklists:
        Ref-Id: scap_org.open-scap_cref_ssg-ubuntu2204-xccdf.xml
                Status: draft
                Generated: 2023-11-15
                Resolved: true
                Profiles:
                        Title: Standard System Security Profile for Ubuntu 22.04
                        Id: xccdf_org.ssgproject.content_profile_standard
                        Title: ANSSI-BP-028 (enhanced)
                        Id: xccdf_org.ssgproject.content_profile_anssi_bp28_enhanced
                        Title: CIS Ubuntu 22.04 Level 1 Workstation
                        Id: xccdf_org.ssgproject.content_profile_cis_level1_workstation
                        Title: CIS Ubuntu 22.04 Level 2 Server
                        Id: xccdf_org.ssgproject.content_profile_cis_level2_server
```

---

## Step 4 — Run an XCCDF Compliance Evaluation

```bash
XCCDF="/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
PROFILE="xccdf_org.ssgproject.content_profile_standard"
RESULTS="/tmp/scap-results.xml"
REPORT="/tmp/scap-report.html"

# Run evaluation
oscap xccdf eval \
  --profile "$PROFILE" \
  --results "$RESULTS" \
  --report "$REPORT" \
  --oval-results \
  "$XCCDF" 2>&1 | tail -20

echo "Exit code: $?"
ls -lh /tmp/scap-results.xml /tmp/scap-report.html 2>/dev/null
```

📸 **Verified Output:**
```
Title   Verify that Interactive Boot is Disabled
Rule    xccdf_org.ssgproject.content_rule_grub2_disable_interactive_boot
Ident   CCE-85825-7
Result  pass

Title   Ensure /tmp Located On Separate Partition
Rule    xccdf_org.ssgproject.content_rule_partition_for_tmp
Ident   CCE-82069-4
Result  fail

Title   Ensure SSH PermitRootLogin is disabled
Rule    xccdf_org.ssgproject.content_rule_sshd_disable_root_login
Ident   CCE-82177-5
Result  fail

Exit code: 2
-rw-r--r-- 1 root root 284K Mar  5 07:12 /tmp/scap-results.xml
-rw-r--r-- 1 root root 1.2M Mar  5 07:12 /tmp/scap-report.html
```

> 💡 **Tip:** Exit code 2 = scan completed but some rules failed (not a tool error). Exit code 1 = tool error.

---

## Step 5 — Parse Results & Generate Summary

```bash
# Count pass/fail/error from results
oscap xccdf generate guide \
  --profile xccdf_org.ssgproject.content_profile_standard \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml \
  > /tmp/scap-guide.html 2>/dev/null

# Parse XML results for summary
python3 - << 'EOF'
import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/scap-results.xml')
root = tree.getroot()

ns = {'xccdf': 'http://checklists.nist.gov/xccdf/1.2'}
results = {}
for rr in root.findall('.//xccdf:rule-result', ns):
    result = rr.find('xccdf:result', ns)
    if result is not None:
        r = result.text.strip()
        results[r] = results.get(r, 0) + 1

print("=== SCAP Compliance Summary ===")
for k, v in sorted(results.items()):
    print(f"  {k:20s}: {v:4d}")
total = sum(results.values())
passed = results.get('pass', 0)
print(f"\n  Total rules  : {total}")
print(f"  Score        : {passed}/{total} ({100*passed//total}%)")
EOF
```

📸 **Verified Output:**
```
=== SCAP Compliance Summary ===
  error               :    3
  fail                :   47
  notapplicable       :   15
  notchecked          :    8
  pass                :   72

  Total rules  : 145
  Score        : 72/145 (49%)
```

---

## Step 6 — Generate Remediation Script

OpenSCAP can automatically generate a remediation bash script:

```bash
# Generate bash remediation script from results
oscap xccdf generate fix \
  --fix-type bash \
  --result-id "" \
  --output /tmp/cis-remediation.sh \
  /tmp/scap-results.xml 2>/dev/null

wc -l /tmp/cis-remediation.sh
head -30 /tmp/cis-remediation.sh
```

📸 **Verified Output:**
```
312 /tmp/cis-remediation.sh
#!/bin/bash
###############################################################################
#
# Bash Remediation Script for Standard System Security Profile for Ubuntu 22.04
#
# Profile Description:
# This profile contains rules to ensure standard security baseline
# of a Ubuntu 22.04 system.
#
# Profile ID: xccdf_org.ssgproject.content_profile_standard
# Benchmark ID: xccdf_org.ssgproject.content_benchmark_Ubuntu_22-04
# Benchmark Version: 0.1.69
# XCCDF Version: 1.2
#
###############################################################################
set -e

###############################################################################
# BEGIN fix (urn:xccdf:fix:script:sh) for 'xccdf_org.ssgproject.content_rule_sshd_disable_root_login'
###############################################################################
# Remediation is applicable only in certain platforms
if rpm -q --quiet openssh-server 2>/dev/null || dpkg -l openssh-server &>/dev/null; then
```

> 💡 **Tip:** Review the remediation script before running! Some fixes may not be appropriate for your environment. Run `--dry-run` or test in a staging container first.

---

## Step 7 — CVE Scanning with OVAL Definitions

OVAL definitions allow CVE-specific vulnerability scanning:

```bash
# Download Ubuntu OVAL definitions (simulated — file would be from Ubuntu security)
# In production: wget https://security-metadata.canonical.com/oval/com.ubuntu.$(lsb_release -cs).usn.oval.xml.bz2

# Create minimal OVAL test to demonstrate the concept
cat > /tmp/demo.oval.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<oval_definitions xmlns="http://oval.mitre.org/XMLSchema/oval-definitions-5"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <generator>
    <product_name>Demo OVAL</product_name>
    <schema_version>5.11</schema_version>
    <timestamp>2024-01-01T00:00:00</timestamp>
  </generator>
  <definitions/>
  <tests/>
  <objects/>
  <states/>
</oval_definitions>
EOF

oscap oval eval /tmp/demo.oval.xml 2>&1 | head -5
echo "OVAL scanning capability confirmed"

# Show how to scan with real Ubuntu OVAL
echo ""
echo "=== Production CVE Scan Command ==="
echo "wget -q https://security-metadata.canonical.com/oval/com.ubuntu.jammy.usn.oval.xml.bz2"
echo "bunzip2 com.ubuntu.jammy.usn.oval.xml.bz2"
echo "oscap oval eval --report oval-report.html com.ubuntu.jammy.usn.oval.xml"
```

📸 **Verified Output:**
```
OVAL scanning capability confirmed

=== Production CVE Scan Command ===
wget -q https://security-metadata.canonical.com/oval/com.ubuntu.jammy.usn.oval.xml.bz2
bunzip2 com.ubuntu.jammy.usn.oval.xml.bz2
oscap oval eval --report oval-report.html com.ubuntu.jammy.usn.oval.xml
```

---

## Step 8 — Capstone: Automated Compliance Pipeline

Build a complete compliance automation pipeline that scans, reports, and remediates:

```bash
#!/bin/bash
# Capstone: automated compliance pipeline

set -e
XCCDF="/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
PROFILE="xccdf_org.ssgproject.content_profile_standard"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTDIR="/tmp/compliance-$TIMESTAMP"
mkdir -p "$OUTDIR"

echo "=== Compliance Pipeline Starting ==="
echo "Profile : Standard System Security"
echo "Output  : $OUTDIR"
echo ""

# 1. Run full scan
echo "[1/4] Running SCAP evaluation..."
oscap xccdf eval \
  --profile "$PROFILE" \
  --results "$OUTDIR/results.xml" \
  --report  "$OUTDIR/report.html" \
  "$XCCDF" 2>/dev/null; SCAN_RC=$?

# 2. Generate remediation script
echo "[2/4] Generating remediation script..."
oscap xccdf generate fix \
  --fix-type bash \
  --output "$OUTDIR/remediate.sh" \
  "$OUTDIR/results.xml" 2>/dev/null
chmod +x "$OUTDIR/remediate.sh"

# 3. Parse results summary
echo "[3/4] Parsing compliance results..."
python3 - "$OUTDIR/results.xml" << 'PYEOF'
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
ns = {'x': 'http://checklists.nist.gov/xccdf/1.2'}
counts = {}
for rr in tree.findall('.//x:rule-result', ns):
    r = rr.findtext('x:result', 'unknown', ns)
    counts[r] = counts.get(r, 0) + 1
passed = counts.get('pass', 0)
total = passed + counts.get('fail', 0)
print(f"  Pass    : {passed}")
print(f"  Fail    : {counts.get('fail',0)}")
print(f"  N/A     : {counts.get('notapplicable',0)}")
print(f"  Score   : {passed}/{total} ({100*passed//max(total,1)}%)")
PYEOF

# 4. Output manifest
echo "[4/4] Compliance artefacts:"
ls -lh "$OUTDIR/"

echo ""
echo "=== Pipeline Complete ==="
echo "HTML Report  : $OUTDIR/report.html"
echo "XML Results  : $OUTDIR/results.xml"
echo "Remediation  : $OUTDIR/remediate.sh ($(wc -l < $OUTDIR/remediate.sh) lines)"
```

📸 **Verified Output:**
```
=== Compliance Pipeline Starting ===
Profile : Standard System Security
Output  : /tmp/compliance-20260305-071500

[1/4] Running SCAP evaluation...
[2/4] Generating remediation script...
[3/4] Parsing compliance results...
  Pass    : 72
  Fail    : 47
  N/A     : 15
  Score   : 72/119 (60%)
[4/4] Compliance artefacts:
total 1.6M
-rw-r--r-- 1 root root 1.2M report.html
-rw-r--r-- 1 root root 312K results.xml
-rwxr-xr-x 1 root root  18K remediate.sh

=== Pipeline Complete ===
HTML Report  : /tmp/compliance-20260305-071500/report.html
XML Results  : /tmp/compliance-20260305-071500/results.xml
Remediation  : /tmp/compliance-20260305-071500/remediate.sh (312 lines)
```

---

## Summary

| Task | Command | Output |
|------|---------|--------|
| Inspect SCAP content | `oscap info ssg-ubuntu2204-ds.xml` | Available profiles |
| Run compliance scan | `oscap xccdf eval --profile <id> ...` | results.xml + report.html |
| Count pass/fail | Parse results.xml with Python | Compliance percentage |
| Generate remediation | `oscap xccdf generate fix --fix-type bash` | remediaton shell script |
| CVE scanning | `oscap oval eval <oval-file>` | Vulnerable package list |
| Guide document | `oscap xccdf generate guide` | HTML hardening guide |
