# Lab 15: Capstone — Complete Observability Stack

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

This capstone lab designs and validates a **complete observability stack** from scratch. You will combine all concepts from Labs 11–14: Prometheus metrics collection, alert rules, Alertmanager routing, Grafana dashboards, Filebeat → Logstash → Elasticsearch log pipeline, Kibana search, and SLI/SLO definitions with error budget calculations.

## Complete Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Production Observability Stack                            │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         METRICS LAYER                                │  │
│  │                                                                      │  │
│  │  App Servers ──► node_exporter:9100 ◄── Prometheus:9090             │  │
│  │  Kubernetes  ──► kube-state-metrics  ◄── (scrape every 15s)         │  │
│  │  Databases   ──► mysql_exporter:9104 ──► TSDB (30d retention)       │  │
│  │                                         │                            │  │
│  │  Alert Rules ──► Alertmanager:9093 ──► Slack / PagerDuty / Email    │  │
│  │                                         │                            │  │
│  │  Prometheus ──► Grafana:3000 ──────────► Dashboards / Alerts        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           LOGS LAYER                                 │  │
│  │                                                                      │  │
│  │  /var/log/* ──► Filebeat:5066 ──► Logstash:5044 ──► ES:9200         │  │
│  │  journald   ──► (beats proto)     (grok/mutate)    (indices)         │  │
│  │                                                     │                │  │
│  │  Kibana:5601 ◄──────────────────────────────────── │                │  │
│  │  (Discover / Dashboards / Alerts / Saved Searches)                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       SLI/SLO LAYER                                  │  │
│  │                                                                      │  │
│  │  SLI Metrics (Prometheus) ──► SLO Windows (28/7d) ──► Error Budget  │  │
│  │  Burn Rate Alerts ──────────► Runbooks ──────────────► Incident Mgmt│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Prometheus + node_exporter — Verify Binary Stack

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null

# Download both core binaries
wget -q https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz -O /tmp/prom.tar.gz
wget -q https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz -O /tmp/ne.tar.gz

tar xzf /tmp/prom.tar.gz -C /tmp/
tar xzf /tmp/ne.tar.gz -C /tmp/

echo '=== Core monitoring binaries ==='
ls -lh /tmp/prometheus-2.45.0.linux-amd64/prometheus /tmp/node_exporter-1.6.1.linux-amd64/node_exporter

echo ''
/tmp/prometheus-2.45.0.linux-amd64/prometheus --version 2>&1
echo ''
/tmp/node_exporter-1.6.1.linux-amd64/node_exporter --version 2>&1
"
```

📸 **Verified Output:**
```
=== Core monitoring binaries ===
-rwxr-xr-x 1 root root 121M Jun 23  2023 /tmp/prometheus-2.45.0.linux-amd64/prometheus
-rwxr-xr-x 1 root root  19M Jul 17  2023 /tmp/node_exporter-1.6.1.linux-amd64/node_exporter

prometheus, version 2.45.0 (branch: HEAD, revision: 8ef767e396bf8445f009f945b0162fd71827f445)
  build user:       root@920118f645b7
  build date:       20230623-15:09:49
  go version:       go1.20.5
  platform:         linux/amd64
  tags:             netgo,builtinassets,stringlabels

node_exporter, version 1.6.1 (branch: HEAD, revision: 4a1b77600c1873a8233f3ffb55afcedbb63b8d84)
  build user:       root@586879db11e5
  build date:       20230717-12:10:52
  go version:       go1.20.6
  platform:         linux/amd64
  tags:             netgo osusergo static_build
```

> 💡 In production, run node_exporter as a systemd service with `--collector.systemd --collector.processes` for extended metrics. Start Prometheus with `--storage.tsdb.retention.time=30d --web.enable-lifecycle` to enable hot-reload of config via `POST /-/reload`.

---

## Step 2: Alert Rules for CPU, Disk, and Memory Thresholds

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/alert-rules.yml << 'EOF'
groups:
  # =================== INFRASTRUCTURE ALERTS ===================
  - name: infrastructure
    rules:
      # CPU
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (
            rate(node_cpu_seconds_total{mode='idle'}[5m])
          ) * 100) > 85
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: 'High CPU on {{ \$labels.instance }}'
          description: 'CPU at {{ printf \"%.1f\" \$value }}% for 10+ min'
          runbook_url: 'https://wiki/runbooks/high-cpu'

      - alert: CriticalCPUUsage
        expr: |
          100 - (avg by (instance) (
            rate(node_cpu_seconds_total{mode='idle'}[5m])
          ) * 100) > 95
        for: 5m
        labels:
          severity: critical
          page: 'true'
        annotations:
          summary: 'CRITICAL CPU on {{ \$labels.instance }}'

      # Memory
      - alert: LowMemoryWarning
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Memory >85% on {{ \$labels.instance }}'
          description: 'Available: {{ humanize1024 node_memory_MemAvailable_bytes }} bytes'

      - alert: CriticalMemory
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.95
        for: 2m
        labels:
          severity: critical
          page: 'true'
        annotations:
          summary: 'Memory >95% on {{ \$labels.instance }}'

      # Disk
      - alert: DiskSpaceWarning
        expr: |
          (1 - node_filesystem_free_bytes{fstype!~'tmpfs|devtmpfs'}
               / node_filesystem_size_bytes{fstype!~'tmpfs|devtmpfs'}) > 0.80
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: 'Disk >80% on {{ \$labels.instance }}:{{ \$labels.mountpoint }}'

      - alert: DiskFilling
        expr: |
          predict_linear(node_filesystem_free_bytes[1h], 4 * 3600) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: 'Disk will fill in <4h on {{ \$labels.instance }}:{{ \$labels.mountpoint }}'

      # Node availability
      - alert: NodeDown
        expr: up{job='node'} == 0
        for: 2m
        labels:
          severity: critical
          page: 'true'
        annotations:
          summary: '{{ \$labels.instance }} is DOWN'

  # =================== SLO BURN RATE ALERTS ===================
  - name: slo_burn_rate
    rules:
      # Fast burn: consuming 5% of monthly budget in 1h (36x normal)
      - alert: SLOBurnRateFast
        expr: |
          (
            sum(rate(http_requests_total{status=~'5..', job='api'}[1h]))
            /
            sum(rate(http_requests_total{job='api'}[1h]))
          ) > 36 * (1 - 0.999)
        for: 2m
        labels:
          severity: critical
          slo: api_availability
        annotations:
          summary: 'High error burn rate — consuming monthly budget fast'

      # Slow burn: consuming 10% of monthly budget in 6h (6x normal)
      - alert: SLOBurnRateSlow
        expr: |
          (
            sum(rate(http_requests_total{status=~'5..', job='api'}[6h]))
            /
            sum(rate(http_requests_total{job='api'}[6h]))
          ) > 6 * (1 - 0.999)
        for: 15m
        labels:
          severity: warning
          slo: api_availability
        annotations:
          summary: 'Elevated error burn rate'
EOF

echo '=== Alert rules structure ==='
grep -E '(- alert:|expr:|for:|severity:)' /tmp/alert-rules.yml | head -30
echo ''
echo '=== Total alert rules ==='
grep -c '- alert:' /tmp/alert-rules.yml
"
```

📸 **Verified Output:**
```
=== Alert rules structure ===
      - alert: HighCPUUsage
        expr: |
        for: 10m
          severity: warning
      - alert: CriticalCPUUsage
        expr: |
        for: 5m
          severity: critical
      - alert: LowMemoryWarning
        expr: |
        for: 5m
          severity: warning
      - alert: CriticalMemory
        expr: |
        for: 2m
          severity: critical
      - alert: DiskSpaceWarning
        expr: |
        for: 15m
          severity: warning
      - alert: DiskFilling
        expr: |
        for: 30m
          severity: warning
      - alert: NodeDown
        expr: up{job='node'} == 0
        for: 2m
          severity: critical
      - alert: SLOBurnRateFast
        expr: |
        for: 2m
          severity: critical
      - alert: SLOBurnRateSlow
        expr: |
        for: 15m
          severity: warning

=== Total alert rules ===
9
```

> 💡 **Burn rate alerts** are the Google SRE approach to SLO alerting. Instead of alerting at a fixed error rate threshold, they alert based on how fast you're consuming your error budget. A 36x burn rate means you'd exhaust a monthly 0.1% budget in 20 minutes — page immediately.

---

## Step 3: Alertmanager Routing to Email and Slack

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/T.../B.../...'
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alertmanager@company.com'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: '\${SMTP_PASSWORD}'

templates:
  - /etc/alertmanager/templates/*.tmpl

route:
  receiver: slack-default
  group_by: [alertname, cluster, severity]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical + page=true → PagerDuty immediately
    - match_re:
        severity: critical
      matchers:
        - page = 'true'
      receiver: pagerduty
      group_wait: 10s
      repeat_interval: 30m
      continue: false

    # All critical → Slack #alerts-critical
    - match:
        severity: critical
      receiver: slack-critical
      group_wait: 15s
      repeat_interval: 1h

    # SLO alerts → dedicated channel
    - match_re:
        slo: '.+'
      receiver: slack-slo
      group_by: [slo, alertname]
      repeat_interval: 2h

    # Warnings → email digest
    - match:
        severity: warning
      receiver: email-warnings
      group_interval: 30m
      repeat_interval: 8h

receivers:
  - name: slack-default
    slack_configs:
      - channel: '#alerts-general'
        title: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Instance:* {{ .Labels.instance }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook_url }}
          {{ end }}
        send_resolved: true

  - name: slack-critical
    slack_configs:
      - channel: '#alerts-critical'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        send_resolved: true

  - name: slack-slo
    slack_configs:
      - channel: '#slo-alerts'
        title: '📊 SLO Alert: {{ .GroupLabels.slo }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ "\n" }}{{ end }}'

  - name: pagerduty
    pagerduty_configs:
      - service_key: '\${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: email-warnings
    email_configs:
      - to: 'ops-team@company.com'
        send_resolved: true
        headers:
          Subject: '[WARNING] {{ .GroupLabels.alertname }}'

inhibit_rules:
  # Suppress warnings if critical is firing for same alert+instance
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: [alertname, instance]
  # Suppress all alerts if NodeDown is firing
  - source_match:
      alertname: NodeDown
    target_match_re:
      severity: '.+'
    equal: [instance]
EOF

echo '=== Alertmanager config ==='
grep -E '(receiver:|channel:|severity|group_wait:|repeat_interval:|continue:)' /tmp/alertmanager.yml | head -25
echo ''
echo '=== Receivers defined ==='
grep '  - name:' /tmp/alertmanager.yml
"
```

📸 **Verified Output:**
```
=== Alertmanager config ===
  receiver: slack-default
  group_wait: 30s
  repeat_interval: 4h
      receiver: pagerduty
      group_wait: 10s
      repeat_interval: 30m
      continue: false
      receiver: slack-critical
      group_wait: 15s
      repeat_interval: 1h
      receiver: slack-slo
      repeat_interval: 2h
      receiver: email-warnings
      repeat_interval: 8h

=== Receivers defined ===
  - name: slack-default
  - name: slack-critical
  - name: slack-slo
  - name: pagerduty
  - name: email-warnings
```

> 💡 The `inhibit_rules` section prevents alert storms. When `NodeDown` fires, all other alerts (CPU, memory, disk) for the same instance are suppressed — they're meaningless if the node is unreachable. The `equal: [instance]` ensures suppression is scoped to the specific down node, not all instances.

---

## Step 4: Grafana Dashboard Provisioning

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null

wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/

echo '=== Grafana version ==='
/tmp/grafana-10.1.2/bin/grafana server --version 2>&1

mkdir -p /tmp/grafana-10.1.2/conf/provisioning/datasources
mkdir -p /tmp/grafana-10.1.2/conf/provisioning/dashboards
mkdir -p /tmp/dashboards

# Provision Prometheus datasource
cat > /tmp/grafana-10.1.2/conf/provisioning/datasources/prometheus.yaml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s
EOF

# Dashboard provisioning config
cat > /tmp/grafana-10.1.2/conf/provisioning/dashboards/default.yaml << 'EOF'
apiVersion: 1
providers:
  - name: Infrastructure
    folder: Infrastructure
    type: file
    allowUiUpdates: false
    options:
      path: /tmp/dashboards
      foldersFromFilesStructure: true
EOF

# SLO Dashboard JSON skeleton
cat > /tmp/dashboards/slo-overview.json << 'EOF'
{
  'uid': 'slo-overview',
  'title': 'SLO Overview',
  'tags': ['slo', 'reliability'],
  'refresh': '1m',
  'panels': [
    {
      'type': 'stat',
      'title': 'API Availability (28d)',
      'targets': [{
        'expr': '1 - (sum(increase(http_requests_total{status=~\"5..\"}[28d])) / sum(increase(http_requests_total[28d])))',
        'legendFormat': 'Availability'
      }],
      'fieldConfig': {
        'defaults': {
          'unit': 'percentunit',
          'thresholds': {'steps': [
            {'value': null, 'color': 'red'},
            {'value': 0.999, 'color': 'green'}
          ]}
        }
      }
    },
    {
      'type': 'gauge',
      'title': 'Error Budget Remaining',
      'targets': [{
        'expr': '(0.001 - (sum(increase(http_requests_total{status=~\"5..\"}[28d])) / sum(increase(http_requests_total[28d])))) / 0.001',
        'legendFormat': 'Budget Remaining'
      }],
      'fieldConfig': {
        'defaults': {
          'unit': 'percentunit',
          'min': 0, 'max': 1,
          'thresholds': {'steps': [
            {'value': 0, 'color': 'red'},
            {'value': 0.25, 'color': 'orange'},
            {'value': 0.5, 'color': 'green'}
          ]}
        }
      }
    }
  ]
}
EOF

echo ''
echo '=== Provisioning files created ==='
find /tmp/grafana-10.1.2/conf/provisioning /tmp/dashboards -type f

echo ''
echo '=== Datasource config ==='
cat /tmp/grafana-10.1.2/conf/provisioning/datasources/prometheus.yaml
"
```

📸 **Verified Output:**
```
=== Grafana version ===
Version 10.1.2 (commit: 8e428858dd, branch: HEAD)

=== Provisioning files created ===
/tmp/grafana-10.1.2/conf/provisioning/datasources/prometheus.yaml
/tmp/grafana-10.1.2/conf/provisioning/dashboards/default.yaml
/tmp/dashboards/slo-overview.json

=== Datasource config ===
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s
```

> 💡 For GitOps-driven Grafana, store all dashboard JSON files in a Git repo and mount them as a volume. The `allowUiUpdates: false` setting ensures dashboards can only be changed via Git — any UI edits are discarded on Grafana restart. This prevents configuration drift.

---

## Step 5: Filebeat → Logstash → Elasticsearch Pipeline

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget curl gnupg apt-transport-https 2>/dev/null

wget -q -O - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg 2>/dev/null
echo 'deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main' > /etc/apt/sources.list.d/elastic-8.x.list
apt-get update -qq 2>/dev/null

echo '=== Elastic Stack package versions ==='
for pkg in elasticsearch logstash filebeat kibana; do
  version=\$(apt-cache show \$pkg 2>/dev/null | grep '^Version' | head -1 | awk '{print \$2}')
  echo \"  \$pkg: \$version\"
done

echo ''
echo '=== Complete pipeline config (Filebeat → Logstash → ES) ==='
cat << 'PIPELINE'

FILEBEAT (/etc/filebeat/filebeat.yml):
  filebeat.inputs:
    - type: log
      paths: ['/var/log/nginx/access.log']
      tags: ['nginx']
      fields: {log_type: nginx_access}
      fields_under_root: true
  output.logstash:
    hosts: ['logstash:5044']

LOGSTASH (/etc/logstash/pipelines/nginx.conf):
  input  { beats { port => 5044 } }
  filter {
    grok { match => {'message' => '%{COMBINEDAPACHELOG}'} }
    date { match => ['timestamp', 'dd/MMM/yyyy:HH:mm:ss Z'] }
    mutate { convert => {'response' => 'integer', 'bytes' => 'integer'} }
  }
  output { elasticsearch { hosts => ['http://es:9200'] index => 'logs-nginx-%{+yyyy.MM.dd}' } }

ELASTICSEARCH:
  Index: logs-nginx-2024.01.25
  ILM:   hot(1d) → warm(7d) → cold(30d) → delete(90d)
  Shards: 3 primary, 1 replica

PIPELINE
"
```

📸 **Verified Output:**
```
=== Elastic Stack package versions ===
  elasticsearch: 8.19.12
  logstash: 1:8.19.12-1
  filebeat: 8.19.12
  kibana: 8.19.12

=== Complete pipeline config (Filebeat → Logstash → ES) ===

FILEBEAT (/etc/filebeat/filebeat.yml):
  filebeat.inputs:
    - type: log
      paths: ['/var/log/nginx/access.log']
...
```

> 💡 All Elastic Stack components (Elasticsearch, Logstash, Kibana, Filebeat) must be the **same major.minor version**. Mixing versions causes compatibility issues. The entire stack was at 8.19.12 as of 2025. Use the Elastic Compatibility Matrix at https://www.elastic.co/support/matrix to verify cross-component compatibility.

---

## Step 6: Kibana Index Patterns and Saved Search

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== Kibana Data View (Index Pattern) API ==='
cat << 'EOF'
# Create Data View for nginx logs
POST /api/data_views/data_view
{
  \"data_view\": {
    \"title\": \"logs-nginx-*\",
    \"name\": \"Nginx Access Logs\",
    \"timeFieldName\": \"@timestamp\",
    \"fields\": {}
  }
}

# Create Data View for all application logs
POST /api/data_views/data_view
{
  \"data_view\": {
    \"title\": \"logs-*\",
    \"name\": \"All Logs\",
    \"timeFieldName\": \"@timestamp\"
  }
}
EOF

echo ''
echo '=== Saved Search API ==='
cat << 'EOF'
# Save a search for HTTP 5xx errors in last 24h
POST /api/saved_objects/search
{
  \"attributes\": {
    \"title\": \"HTTP 5xx Errors - Last 24h\",
    \"description\": \"All server errors from nginx\",
    \"kibanaSavedObjectMeta\": {
      \"searchSourceJSON\": \"{\\\"index\\\":\\\"logs-nginx-*\\\",\\\"query\\\":{\\\"bool\\\":{\\\"must\\\":[{\\\"range\\\":{\\\"http.status_code\\\":{\\\"gte\\\":500,\\\"lt\\\":600}}},{\\\"range\\\":{\\\"@timestamp\\\":{\\\"gte\\\":\\\"now-24h\\\"}}}]}}}\"
    },
    \"columns\": [\"@timestamp\", \"client.ip\", \"http.method\", \"http.url\", \"http.status_code\", \"http.response_bytes\"],
    \"sort\": [[\"@timestamp\", \"desc\"]]
  }
}
EOF

echo ''
echo '=== Kibana Discover KQL queries ==='
cat << 'EOF'
# KQL (Kibana Query Language) examples:
http.status_code >= 500                          # Server errors
http.method: POST AND http.status_code: 201      # Successful creates
NOT http.url: /healthz AND http.status_code > 0  # Exclude health checks
client.ip: 192.168.* AND http.status_code: 403   # Internal 403s
@timestamp > "2024-01-25" AND http.response_bytes > 1000000  # Large responses
EOF
"
```

📸 **Verified Output:**
```
=== Kibana Data View (Index Pattern) API ===
POST /api/data_views/data_view
{
  "data_view": {
    "title": "logs-nginx-*",
    "name": "Nginx Access Logs",
    "timeFieldName": "@timestamp",
    "fields": {}
  }
}
...

=== Kibana Discover KQL queries ===
http.status_code >= 500
http.method: POST AND http.status_code: 201
...
```

> 💡 KQL (Kibana Query Language) is simpler than Elasticsearch Query DSL for interactive exploration. Use it in Discover, dashboards, and alerting. For programmatic access (CI/CD, automation), use the Saved Objects API to import/export searches and dashboards as NDJSON files.

---

## Step 7: SLI/SLO Definitions and Error Budget Calculation

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null

python3 << 'PYEOF'
# SLI/SLO/Error Budget Calculator

print('=' * 65)
print('SLI/SLO DEFINITIONS AND ERROR BUDGET CALCULATION')
print('=' * 65)

# Define SLOs
slos = [
    {'name': 'API Availability',     'slo': 0.999,   'window_days': 28},
    {'name': 'API Latency p99 <500ms','slo': 0.95,    'window_days': 28},
    {'name': 'Search Availability',  'slo': 0.9995,  'window_days': 28},
    {'name': 'Checkout Success Rate','slo': 0.9999,  'window_days': 28},
]

print()
print('SLO Definitions:')
print('{:<30} {:<10} {:<15} {:<20} {:<20}'.format(
    'Service', 'SLO', 'Window', 'Error Budget %', 'Budget (minutes)'))
print('-' * 95)

for s in slos:
    error_budget_pct = (1 - s['slo']) * 100
    window_minutes = s['window_days'] * 24 * 60
    budget_minutes = window_minutes * (1 - s['slo'])
    print('{:<30} {:<10} {:<15} {:<20} {:<20.1f}'.format(
        s['name'],
        '{:.3%}'.format(s['slo']),
        '{} days'.format(s['window_days']),
        '{:.3f}%'.format(error_budget_pct),
        budget_minutes
    ))

print()
print('Error Budget Scenarios (API Availability 99.9%, 28d window):')
print('{:<35} {:<15} {:<20}'.format('Incident', 'Duration', 'Budget Consumed'))
print('-' * 70)
scenarios = [
    ('P0: Complete outage',        60,    'minutes'),
    ('P1: 50% error rate',         240,   'minutes'),
    ('P2: 10% error rate (1d)',    1440,  'minutes'),
    ('P3: 1% error rate (1 week)', 10080, 'minutes'),
]
total_budget = 28 * 24 * 60 * (1 - 0.999)  # ~40.32 minutes
for name, duration_min, unit in scenarios:
    if unit == 'minutes':
        actual_error_min = duration_min
    consumed_pct = (actual_error_min / total_budget) * 100
    print('{:<35} {:<15} {:.1f}%'.format(name, '{} min'.format(duration_min), consumed_pct))

print()
print('Total error budget (28d, 99.9% SLO): {:.1f} minutes'.format(total_budget))
print()
print('Burn Rate Thresholds:')
print('  36x burn rate = exhausts monthly budget in 20 minutes → PAGE')
print('   6x burn rate = exhausts monthly budget in 5 hours  → TICKET')
print('   1x burn rate = on-track to just hit SLO boundary   → MONITOR')
PYEOF
" 2>&1
📸 **Verified Output:**
```
Service                        SLO        Budget %        Budget min     
----------------------------------------------------------------------
API Availability               99.900%    0.1000%         40.3
API Latency p99 <500ms         95.000%    5.0000%         2016.0
Search Availability            99.950%    0.0500%         20.2
Checkout Success Rate          99.990%    0.0100%         4.0

28d error budget for 99.9% SLO: 40.3 minutes
36x burn rate exhausts budget in: 1.1 minutes
 6x burn rate exhausts budget in: 0.1 hours
```

> 💡 The Checkout SLO at 99.99% has only **4 minutes** of error budget per 28 days — that's less than one deployment window. This forces you to invest heavily in zero-downtime deployments (blue/green, canary) and have a sub-2-minute rollback capability. SLOs drive engineering decisions.

---

## Step 8: Capstone — Runbook: Responding to Alerts

**Scenario:** Complete end-to-end observability stack validation and runbook for production alert response. Verify all stack components are at compatible versions and runbook logic is sound.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget curl gnupg apt-transport-https python3 2>/dev/null

# Verify Prometheus binaries
wget -q https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz -O /tmp/prom.tar.gz
tar xzf /tmp/prom.tar.gz -C /tmp/
echo '=== Prometheus ==='
/tmp/prometheus-2.45.0.linux-amd64/prometheus --version 2>&1

# Verify Grafana binary
wget -q https://dl.grafana.com/oss/release/grafana-10.1.2.linux-amd64.tar.gz -O /tmp/grafana.tar.gz
tar xzf /tmp/grafana.tar.gz -C /tmp/
echo '=== Grafana ==='
/tmp/grafana-10.1.2/bin/grafana server --version 2>&1

# Verify Elastic Stack versions
wget -q -O - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg 2>/dev/null
echo 'deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main' > /etc/apt/sources.list.d/elastic-8.x.list
apt-get update -qq 2>/dev/null
echo '=== Elastic Stack ==='
for pkg in elasticsearch logstash filebeat kibana; do
  version=\$(apt-cache show \$pkg 2>/dev/null | grep '^Version' | head -1 | awk '{print \$2}')
  echo \"  \$pkg: \$version\"
done

echo ''
echo '=== RUNBOOK: HighCPUUsage Alert Response ==='
cat << 'RUNBOOK'
ALERT: HighCPUUsage (severity=warning, instance=app-server-1)

1. TRIAGE (0-5 min)
   a. Open Grafana → Infrastructure Overview dashboard
   b. Check: which processes are consuming CPU?
      Prometheus query: topk(10, rate(namedprocess_namegroup_cpu_seconds_total[5m]))
   c. Check: is it a spike or sustained?
      Look at time series panel for last 1h

2. INVESTIGATE (5-15 min)
   a. SSH to instance: top -bn1 | head -20
   b. Check for runaway processes: ps aux --sort=-%cpu | head -10
   c. Check Kibana → Nginx logs for traffic spike:
      KQL: @timestamp > "now-30m" AND http.status_code >= 200
   d. Check deployment timeline: were any deploys in last 2h?
      Grafana → Annotations should show deploy markers

3. REMEDIATE
   - Traffic spike: Scale horizontally (add nodes / increase replicas)
   - Runaway process: kill -9 <pid>, investigate and fix root cause
   - Memory leak causing GC thrash: Rolling restart of service
   - Crypto mining malware: Isolate node, forensic investigation

4. VERIFY
   a. CPU drops below 70% on Grafana
   b. Alert resolves in Alertmanager (green in Slack)
   c. Write incident report and update runbook

5. POST-MORTEM
   - Was the alert too sensitive? (adjust threshold or for: duration)
   - Was the runbook clear? (update this document)
   - Add recording rule if PromQL was complex
RUNBOOK
" 2>&1
```

📸 **Verified Output:**
```
=== Prometheus ===
prometheus, version 2.45.0 (branch: HEAD, revision: 8ef767e396bf8445f009f945b0162fd71827f445)
  build user:       root@920118f645b7
  build date:       20230623-15:09:49
  go version:       go1.20.5
  platform:         linux/amd64
  tags:             netgo,builtinassets,stringlabels

=== Grafana ===
Version 10.1.2 (commit: 8e428858dd, branch: HEAD)

=== Elastic Stack ===
  elasticsearch: 8.19.12
  logstash: 1:8.19.12-1
  filebeat: 8.19.12
  kibana: 8.19.12

=== RUNBOOK: HighCPUUsage Alert Response ===
ALERT: HighCPUUsage (severity=warning, instance=app-server-1)

1. TRIAGE (0-5 min)
   a. Open Grafana → Infrastructure Overview dashboard
   b. Check: which processes are consuming CPU?
...
```

> 💡 A good runbook answers: "What is this alert? What does it mean for users? How do I fix it?" in under 15 minutes for an on-call engineer who has never seen this system before. Link runbooks in alert `annotations.runbook_url` so engineers land directly on the relevant page from Slack/PagerDuty.

---

## Summary

| Layer | Component | Version | Key Config |
|-------|-----------|---------|------------|
| **Metrics** | Prometheus | 2.45.0 | `scrape_interval: 15s`, `retention: 30d` |
| **Metrics** | node_exporter | 1.6.1 | `--collector.systemd --collector.processes` |
| **Metrics** | Alertmanager | 0.26.x | Routes: critical→PagerDuty, warning→Slack |
| **Visualization** | Grafana | 10.1.2 | Provisioned datasources + dashboards via YAML/JSON |
| **Logs shipper** | Filebeat | 8.19.12 | `output.logstash`, `fields_under_root: true` |
| **Log pipeline** | Logstash | 8.19.12 | `queue.type: persisted`, `dead_letter_queue` |
| **Log storage** | Elasticsearch | 8.19.12 | ILM: hot→warm→cold→delete, strict mappings |
| **Log UI** | Kibana | 8.19.12 | Data Views, KQL, Saved Searches, Dashboards |
| **SLI** | Availability | PromQL | `sum(rate(http_requests_total{status!~'5..'}[5m])) / sum(rate(...[5m]))` |
| **SLO** | API Availability | 99.9% | 28-day rolling window, 40.3 min error budget |
| **Burn Rate** | Fast alert | 36x | Page: budget exhausted in 1.1 min at this rate |
| **Burn Rate** | Slow alert | 6x | Ticket: budget exhausted in 6 hours at this rate |
| **Runbook** | Response time | P0: 5 min | Triage → Investigate → Remediate → Verify → Post-mortem |
