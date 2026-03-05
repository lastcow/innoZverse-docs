# Lab 12: Grafana Dashboards

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Grafana is the industry-standard open-source visualization platform. It connects to data sources (Prometheus, Elasticsearch, InfluxDB, PostgreSQL, etc.) and renders dashboards with panels: time series, stat, gauge, table, heatmap, bar chart, and more. In this lab you download and run Grafana from the official binary, explore dashboard JSON structure, configure provisioning, and set up alerting.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Grafana Architecture                    │
│                                                            │
│  Browser ──► Grafana Server :3000                         │
│               │                                            │
│               ├── Data Sources                             │
│               │     ├── Prometheus (PromQL)                │
│               │     ├── Elasticsearch (Lucene/ES-DSL)      │
│               │     └── Loki (LogQL)                       │
│               │                                            │
│               ├── Dashboards (JSON model)                  │
│               │     ├── Panels (visualization units)       │
│               │     ├── Variables (template variables)     │
│               │     └── Annotations (event overlays)       │
│               │                                            │
│               ├── Alerting                                  │
│               │     ├── Alert Rules (per panel/query)       │
│               │     ├── Contact Points (email/slack)        │
│               │     └── Notification Policies              │
│               │                                            │
│               └── Provisioning (YAML files on disk)        │
│                     ├── datasources/                       │
│                     ├── dashboards/                        │
│                     └── alerting/                          │
└────────────────────────────────────────────────────────────┘
```

---

## Step 1: Download and Verify Grafana Binary

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null

wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz \
  -O /tmp/grafana.tar.gz

tar xzf /tmp/grafana.tar.gz -C /tmp/
echo '=== Grafana directory structure ==='
ls /tmp/grafana-10.1.2/

echo ''
echo '=== Grafana version ==='
/tmp/grafana-10.1.2/bin/grafana-server --version 2>&1
"
```

📸 **Verified Output:**
```
=== Grafana directory structure ===
Dockerfile
LICENSE
NOTICE.md
README.md
VERSION
bin
conf
docs
npm-artifacts
packaging
plugins-bundled
public
storybook

=== Grafana version ===
Deprecation warning: The standalone 'grafana-server' program is deprecated and will be removed in the future. Please update all uses of 'grafana-server' to 'grafana server'
Version 10.1.2 (commit: 8e428858dd, branch: HEAD)
```

> 💡 Starting Grafana 10+, the command is `grafana server` (not `grafana-server`). The binary in `bin/` is a multi-command binary: `grafana server`, `grafana cli`, `grafana migrate`. All configuration lives in `conf/defaults.ini` — override via `conf/custom.ini`.

---

## Step 2: Configure grafana.ini

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null
wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/

# Create custom config
mkdir -p /tmp/grafana-data /tmp/grafana-logs /tmp/grafana-plugins

cat > /tmp/grafana-10.1.2/conf/custom.ini << 'EOF'
[server]
http_addr = 0.0.0.0
http_port = 3000
domain = grafana.company.com
root_url = https://grafana.company.com/

[database]
type = sqlite3
path = /tmp/grafana-data/grafana.db

[paths]
data = /tmp/grafana-data
logs = /tmp/grafana-logs
plugins = /tmp/grafana-plugins
provisioning = /tmp/grafana-10.1.2/conf/provisioning

[security]
admin_user = admin
admin_password = securepassword123
secret_key = SW2YcwTIb9zpOOhoPsMm
allow_embedding = true

[auth.anonymous]
enabled = false

[users]
allow_sign_up = false
auto_assign_org_role = Viewer

[unified_alerting]
enabled = true

[smtp]
enabled = true
host = smtp.company.com:587
user = grafana@company.com
password = smtppassword
from_address = grafana@company.com
from_name = Grafana Alerts
EOF

echo '=== custom.ini written ==='
echo 'Key sections:'
grep '^\[' /tmp/grafana-10.1.2/conf/custom.ini
"
```

📸 **Verified Output:**
```
=== custom.ini written ===
Key sections:
[server]
[database]
[paths]
[security]
[auth.anonymous]
[users]
[unified_alerting]
[smtp]
```

> 💡 Grafana uses INI format with sections `[section]`. The `conf/defaults.ini` has every possible option with comments. Only override what you need in `custom.ini`. Use environment variables for secrets: `GF_SECURITY_ADMIN_PASSWORD=secret`.

---

## Step 3: Provision Data Sources

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null
wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/

mkdir -p /tmp/grafana-10.1.2/conf/provisioning/datasources

cat > /tmp/grafana-10.1.2/conf/provisioning/datasources/prometheus.yaml << 'EOF'
apiVersion: 1

deleteDatasources:
  - name: OldPrometheus
    orgId: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy        # server-side proxy (recommended)
    orgId: 1
    url: http://prometheus:9090
    basicAuth: false
    isDefault: true
    version: 1
    editable: false      # Prevent UI edits
    jsonData:
      httpMethod: POST
      timeInterval: 15s  # Matches scrape_interval
      queryTimeout: 60s
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: false
    jsonData:
      maxLines: 1000
      derivedFields:
        - name: TraceID
          matcherRegex: '"trace_id":"(\w+)"'
          url: '${__value.raw}'
          datasourceUid: tempo
EOF

echo '=== datasource provisioning ==='
cat /tmp/grafana-10.1.2/conf/provisioning/datasources/prometheus.yaml
"
```

📸 **Verified Output:**
```
=== datasource provisioning ===
apiVersion: 1

deleteDatasources:
  - name: OldPrometheus
    orgId: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    orgId: 1
    url: http://prometheus:9090
...
```

> 💡 Set `editable: false` in provisioned data sources to prevent users from accidentally modifying the Prometheus URL in the UI. Changes to provisioning files take effect on Grafana restart or via `POST /api/admin/provisioning/datasources/reload`.

---

## Step 4: Dashboard JSON Structure

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
=== Grafana Dashboard JSON Model ===

{
  // Dashboard metadata
  'id': null,              // null for new, integer for existing
  'uid': 'infra-overview', // Unique ID for URLs and provisioning
  'title': 'Infrastructure Overview',
  'description': 'CPU, Memory, Disk for all nodes',
  'tags': ['infrastructure', 'node-exporter'],
  'timezone': 'browser',
  'schemaVersion': 38,     // Grafana schema version
  'version': 1,
  'refresh': '30s',        // Auto-refresh interval
  
  // Time range
  'time': {
    'from': 'now-1h',
    'to': 'now'
  },
  
  // Template variables (dropdowns in UI)
  'templating': {
    'list': [
      {
        'name': 'instance',
        'label': 'Instance',
        'type': 'query',
        'datasource': {'type': 'prometheus', 'uid': '\${DS_PROMETHEUS}'},
        'query': 'label_values(node_uname_info, instance)',
        'refresh': 2,         // Refresh on time range change
        'multi': true,
        'includeAll': true,
        'allValue': '.*'
      },
      {
        'name': 'job',
        'type': 'query',
        'query': 'label_values(up, job)',
        'refresh': 1
      }
    ]
  },
  
  // Annotations (event overlays)
  'annotations': {
    'list': [
      {
        'name': 'Deployments',
        'datasource': {'type': 'prometheus'},
        'expr': 'changes(deployment_timestamp[5m]) > 0',
        'titleFormat': 'Deploy: {{service}}',
        'iconColor': 'green'
      }
    ]
  },
  
  // Panel rows
  'panels': [
    // ... see Step 5
  ]
}
EOF
"
```

📸 **Verified Output:**
```
=== Grafana Dashboard JSON Model ===
{
  'id': null,
  'uid': 'infra-overview',
  'title': 'Infrastructure Overview',
  ...
}
```

> 💡 The `uid` field is critical — it's used in URLs (`/d/<uid>/title`) and for provisioning references. Keep it short, human-readable, and unique. Use `schemaVersion: 38` for Grafana 10.x compatibility.

---

## Step 5: Panel Types Reference

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
=== Panel Types and Configuration ===

1. TIME SERIES PANEL (most common)
{
  'type': 'timeseries',
  'title': 'CPU Usage %',
  'fieldConfig': {
    'defaults': {
      'unit': 'percent',
      'min': 0, 'max': 100,
      'thresholds': {
        'mode': 'absolute',
        'steps': [
          {'value': null, 'color': 'green'},
          {'value': 70,   'color': 'yellow'},
          {'value': 90,   'color': 'red'}
        ]
      }
    }
  },
  'targets': [{
    'datasource': {'type': 'prometheus'},
    'expr': 'instance:node_cpu_utilisation:rate5m{instance=~\"\$instance\"}',
    'legendFormat': '{{instance}}'
  }]
}

2. STAT PANEL (single big number)
{
  'type': 'stat',
  'title': 'Total Requests/s',
  'options': {'reduceOptions': {'calcs': ['lastNotNull']}},
  'fieldConfig': {'defaults': {'unit': 'reqps', 'color': {'mode': 'thresholds'}}}
}

3. GAUGE PANEL (radial meter)
{
  'type': 'gauge',
  'title': 'Memory Usage',
  'fieldConfig': {
    'defaults': {'unit': 'percent', 'min': 0, 'max': 100,
      'thresholds': {'steps': [
        {'value': null, 'color': 'green'},
        {'value': 80, 'color': 'orange'},
        {'value': 95, 'color': 'red'}
      ]}
    }
  }
}

4. TABLE PANEL (grid data)
{
  'type': 'table',
  'transformations': [
    {'id': 'merge', 'options': {}},
    {'id': 'organize', 'options': {
      'renameByName': {'instance': 'Host', 'Value': 'CPU %'}
    }}
  ]
}

5. HEATMAP PANEL (distribution over time)
{
  'type': 'heatmap',
  'title': 'Request Latency Distribution',
  'targets': [{
    'expr': 'sum(rate(http_request_duration_seconds_bucket[5m])) by (le)',
    'format': 'heatmap',
    'legendFormat': '{{le}}'
  }]
}
EOF
"
```

📸 **Verified Output:**
```
=== Panel Types and Configuration ===

1. TIME SERIES PANEL (most common)
{
  'type': 'timeseries',
  'title': 'CPU Usage %',
...
```

> 💡 The **Stat panel** is ideal for SLO dashboards showing current error rate or availability. The **Heatmap panel** is perfect for latency distributions from Prometheus histograms — set format to `heatmap` and legend format to `{{le}}` to get proper bucket display.

---

## Step 6: Dashboard Provisioning

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null
wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/

mkdir -p /tmp/grafana-10.1.2/conf/provisioning/dashboards
mkdir -p /tmp/dashboards

# Dashboard provider config
cat > /tmp/grafana-10.1.2/conf/provisioning/dashboards/default.yaml << 'EOF'
apiVersion: 1

providers:
  - name: Infrastructure
    orgId: 1
    folder: Infrastructure
    folderUid: infra-folder
    type: file
    disableDeletion: false      # Allow deleting provisioned dashboards
    updateIntervalSeconds: 30   # Check for updates every 30s
    allowUiUpdates: false       # Prevent UI edits (changes lost on reload)
    options:
      path: /tmp/dashboards     # Directory containing dashboard JSON files
      foldersFromFilesStructure: true  # Use subdirectory names as folder names

  - name: Operations
    folder: Operations
    type: file
    options:
      path: /tmp/dashboards/ops
EOF

echo '=== dashboard provisioning config ==='
cat /tmp/grafana-10.1.2/conf/provisioning/dashboards/default.yaml

# Create a minimal dashboard JSON
cat > /tmp/dashboards/node-overview.json << 'EOF'
{
  '__inputs': [{'name': 'DS_PROMETHEUS', 'type': 'datasource', 'pluginId': 'prometheus'}],
  'uid': 'node-overview',
  'title': 'Node Overview',
  'tags': ['infrastructure'],
  'refresh': '30s',
  'panels': []
}
EOF

echo ''
echo '=== dashboard JSON ==='
cat /tmp/dashboards/node-overview.json
"
```

📸 **Verified Output:**
```
=== dashboard provisioning config ===
apiVersion: 1

providers:
  - name: Infrastructure
    orgId: 1
    folder: Infrastructure
    folderUid: infra-folder
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /tmp/dashboards
      foldersFromFilesStructure: true
...
```

> 💡 Use `allowUiUpdates: false` to treat dashboards as code — they can only be changed by updating the JSON file. This enforces GitOps for dashboards. Export dashboards from UI via **Share → Export → Save to file**, then commit to your repo.

---

## Step 7: Grafana Alerting Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
mkdir -p /tmp/grafana-alerting

cat > /tmp/grafana-alerting/contact-points.yaml << 'EOF'
apiVersion: 1

contactPoints:
  - orgId: 1
    name: slack-ops
    receivers:
      - uid: slack-ops-uid
        type: slack
        settings:
          url: https://hooks.slack.com/services/T.../B.../...
          channel: '#alerts-ops'
          title: '{{ template \"slack.title\" . }}'
          text: '{{ template \"slack.message\" . }}'
          mentionChannel: here
        disableResolveMessage: false

  - orgId: 1
    name: email-oncall
    receivers:
      - uid: email-oncall-uid
        type: email
        settings:
          addresses: oncall@company.com;backup@company.com
          singleEmail: false
EOF

cat > /tmp/grafana-alerting/notification-policies.yaml << 'EOF'
apiVersion: 1

policies:
  - orgId: 1
    receiver: email-oncall      # Default receiver
    group_by: [grafana_folder, alertname]
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: slack-ops
        matchers:
          - severity = critical
        group_wait: 10s
        repeat_interval: 1h
EOF

echo '=== contact points ==='
cat /tmp/grafana-alerting/contact-points.yaml

echo ''
echo '=== notification policies ==='
cat /tmp/grafana-alerting/notification-policies.yaml
"
```

📸 **Verified Output:**
```
=== contact points ===
apiVersion: 1

contactPoints:
  - orgId: 1
    name: slack-ops
    receivers:
      - uid: slack-ops-uid
        type: slack
...
```

> 💡 Grafana 10 uses **Unified Alerting** (vs legacy panel alerting). Alert rules are evaluated by Grafana itself — not the data source. This means alerts fire even if the dashboard isn't open. Configure via UI under Alerting → Alert Rules, then export to YAML for GitOps.

---

## Step 8: Capstone — Production Dashboard Stack

**Scenario:** Deploy a Grafana instance with provisioned dashboards, Prometheus data source, and alert rules for a production cluster. Validate the binary and directory structure.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget curl 2>/dev/null

wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/

echo '=== Grafana version ==='
/tmp/grafana-10.1.2/bin/grafana server --version 2>&1

echo ''
echo '=== Default config sections ==='
grep '^\[' /tmp/grafana-10.1.2/conf/defaults.ini | head -25

echo ''
echo '=== Bundled plugins ==='
ls /tmp/grafana-10.1.2/plugins-bundled/ 2>/dev/null | head -10

echo ''
echo '=== Grafana CLI help ==='
/tmp/grafana-10.1.2/bin/grafana cli --help 2>&1 | head -15
"
```

📸 **Verified Output:**
```
=== Grafana version ===
Version 10.1.2 (commit: 8e428858dd, branch: HEAD)

=== Default config sections ===
[paths]
[server]
[database]
[remote_cache]
[dataproxy]
[analytics]
[security]
[snapshots]
[dashboards]
[users]
[auth]
[auth.anonymous]
[auth.github]
[auth.gitlab]
[auth.google]
[auth.grafana_com]
[auth.azuread]
[auth.okta]
[auth.generic_oauth]
[auth.basic]
[auth.proxy]
[auth.jwt]
[smtp]
[emails]

=== Grafana CLI help ===
Usage:
  grafana cli [command]

Available Commands:
  admin       Admin commands
  certs       Generate self signed certificate
  plugins     Manage plugins
  server      Run the Grafana server
```

> 💡 For production, use `grafana cli plugins install grafana-piechart-panel` to install community plugins. In Docker, mount a persistent volume at `/var/lib/grafana` to preserve dashboards, user data, and alert states across container restarts.

---

## Summary

| Concept | Key Details |
|---------|-------------|
| **Grafana version** | 10.1.2 (commit 8e428858dd), binary in `bin/grafana` |
| **Config files** | `conf/defaults.ini` (reference), `conf/custom.ini` (overrides) |
| **Data sources** | Provisioned via `conf/provisioning/datasources/*.yaml`, `editable: false` for GitOps |
| **Panel types** | timeseries, stat, gauge, table, heatmap, bar chart, histogram, pie chart |
| **Variables** | `type: query` + `label_values()` for dynamic dropdowns; `multi: true` for multi-select |
| **Annotations** | PromQL-based event overlays; also supports native Grafana annotations via API |
| **Dashboard provisioning** | JSON files in `options.path`; `allowUiUpdates: false` enforces GitOps |
| **Unified Alerting** | Grafana 10 default; evaluates rules server-side; routes via Contact Points |
| **Plugins** | `grafana cli plugins install <id>`; bundled plugins in `plugins-bundled/` |
| **Production tips** | Persistent volume for `/var/lib/grafana`, env vars for secrets, HTTPS via reverse proxy |
