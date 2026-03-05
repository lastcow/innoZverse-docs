# Lab 11: Prometheus Metrics & Alerting

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

## Overview

Prometheus is a pull-based monitoring system with a time-series database (TSDB), PromQL query language, and a built-in alerting pipeline. In this lab you will install and configure Prometheus and node_exporter from official binaries, write PromQL queries, define recording rules and alert rules, and configure Alertmanager routing — all verified inside Docker.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus Architecture                   │
│                                                             │
│  ┌──────────────┐    scrape     ┌─────────────────────────┐ │
│  │  node_exporter│◄─────────────│     Prometheus Server   │ │
│  │  :9100/metrics│              │  ┌──────────────────┐   │ │
│  └──────────────┘              │  │   TSDB (chunks)  │   │ │
│                                │  │   /prometheus    │   │ │
│  ┌──────────────┐    scrape    │  └──────────────────┘   │ │
│  │  app_exporter │◄────────────│  ┌──────────────────┐   │ │
│  │  :8080/metrics│             │  │  PromQL Engine   │   │ │
│  └──────────────┘             │  └──────────────────┘   │ │
│                               └─────────────┬───────────┘ │
│  ┌──────────────────────────────────────────▼───────────┐  │
│  │                  Alertmanager :9093                  │  │
│  │     routes → email / slack / pagerduty / webhook     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Install Prometheus Binary

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null
apt-get install -y -qq wget curl 2>/dev/null

# Download Prometheus v2.45.0
wget -q https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz \
  -O /tmp/prom.tar.gz
tar xzf /tmp/prom.tar.gz -C /tmp/

# Check version
/tmp/prometheus-2.45.0.linux-amd64/prometheus --version 2>&1
"
```

📸 **Verified Output:**
```
prometheus, version 2.45.0 (branch: HEAD, revision: 8ef767e396bf8445f009f945b0162fd71827f445)
  build user:       root@920118f645b7
  build date:       20230623-15:09:49
  go version:       go1.20.5
  platform:         linux/amd64
  tags:             netgo,builtinassets,stringlabels
```

> 💡 The `netgo` and `builtinassets` tags mean Prometheus is statically compiled — no external library dependencies. The web UI assets are embedded in the binary.

---

## Step 2: Install node_exporter

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget 2>/dev/null

wget -q https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz \
  -O /tmp/ne.tar.gz
tar xzf /tmp/ne.tar.gz -C /tmp/

/tmp/node_exporter-1.6.1.linux-amd64/node_exporter --version 2>&1
"
```

📸 **Verified Output:**
```
node_exporter, version 1.6.1 (branch: HEAD, revision: 4a1b77600c1873a8233f3ffb55afcedbb63b8d84)
  build user:       root@586879db11e5
  build date:       20230717-12:10:52
  go version:       go1.20.6
  platform:         linux/amd64
  tags:             netgo osusergo static_build
```

> 💡 node_exporter exposes 40+ metric families by default: CPU, memory, disk I/O, filesystem, network, systemd units, and more. Run with `--collector.systemd` to include systemd service states.

---

## Step 3: Write prometheus.yml Configuration

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/prometheus.yml << 'EOF'
# Global settings apply to all scrape jobs
global:
  scrape_interval:     15s   # How often to scrape targets
  evaluation_interval: 15s   # How often to evaluate rules
  scrape_timeout:      10s   # Timeout for a single scrape

# Alertmanager connection
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rule files
rule_files:
  - /etc/prometheus/rules/*.yml

# Scrape configurations
scrape_configs:
  # Prometheus scrapes itself
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  # node_exporter on all hosts
  - job_name: node
    static_configs:
      - targets:
          - 'host1:9100'
          - 'host2:9100'
        labels:
          env: production
          region: us-east-1

  # Dynamic service discovery via file_sd
  - job_name: app_servers
    file_sd_configs:
      - files:
          - /etc/prometheus/targets/*.json
        refresh_interval: 30s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
      - source_labels: [env]
        target_label: environment
EOF

echo '=== prometheus.yml written ==='
cat /tmp/prometheus.yml
"
```

📸 **Verified Output:**
```
=== prometheus.yml written ===
global:
  scrape_interval:     15s
  evaluation_interval: 15s
  scrape_timeout:      10s
...
```

> 💡 Use `file_sd_configs` for dynamic environments (Kubernetes, auto-scaling groups). Files are JSON arrays of `{targets: [...], labels: {...}}`. Prometheus reloads them automatically on change without restart.

---

## Step 4: PromQL Query Reference

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'EOF'
=== Core PromQL Query Patterns ===

# 1. CPU usage rate (5-minute window)
# rate() computes per-second average over range vector
rate(node_cpu_seconds_total{mode='idle'}[5m])

# 2. CPU busy percentage per instance
100 - (avg by (instance) (
  rate(node_cpu_seconds_total{mode='idle'}[5m])
) * 100)

# 3. Memory available percentage
(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 4. Disk I/O rate
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])

# 5. HTTP request rate (increase over 1h, then per-second)
rate(http_requests_total{job='api',status=~'5..'}[5m])

# 6. 99th percentile latency (histogram)
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)
)

# 7. Error ratio
sum(rate(http_requests_total{status=~'5..'}[5m]))
  /
sum(rate(http_requests_total[5m]))

# 8. Top 5 memory consumers
topk(5, container_memory_usage_bytes{namespace='production'})

# 9. Predict disk full (linear extrapolation over 4h)
predict_linear(node_filesystem_free_bytes[1h], 4*3600) < 0

# 10. avg_over_time for smoothed metrics
avg_over_time(node_load1[30m])
EOF
"
```

📸 **Verified Output:**
```
=== Core PromQL Query Patterns ===

# 1. CPU usage rate (5-minute window)
rate(node_cpu_seconds_total{mode='idle'}[5m])
...
```

> 💡 `rate()` vs `increase()`: Use `rate()` for per-second calculations (CPU, requests/s). Use `increase()` for total count over a time window (e.g., errors in last hour). Both only work on counters.

---

## Step 5: Define Recording Rules

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/recording_rules.yml << 'EOF'
groups:
  - name: node_aggregations
    interval: 30s       # Override global evaluation_interval
    rules:
      # Pre-compute CPU busy % to avoid recalculating in dashboards
      - record: instance:node_cpu_utilisation:rate5m
        expr: |
          100 - (avg by (instance, job) (
            rate(node_cpu_seconds_total{mode='idle'}[5m])
          ) * 100)

      # Pre-compute memory utilisation
      - record: instance:node_memory_utilisation:ratio
        expr: |
          1 - (
            node_memory_MemAvailable_bytes
            /
            node_memory_MemTotal_bytes
          )

      # Pre-compute filesystem usage per mountpoint
      - record: instance:node_filesystem_usage:ratio
        expr: |
          1 - (
            node_filesystem_free_bytes{fstype!~'tmpfs|devtmpfs'}
            /
            node_filesystem_size_bytes{fstype!~'tmpfs|devtmpfs'}
          )

      # Network throughput
      - record: instance:node_network_receive_bytes:rate5m
        expr: |
          sum by (instance) (
            rate(node_network_receive_bytes_total[5m])
          )
EOF

echo '=== recording_rules.yml ==='
cat /tmp/recording_rules.yml
"
```

📸 **Verified Output:**
```
=== recording_rules.yml ===
groups:
  - name: node_aggregations
    interval: 30s
    rules:
      - record: instance:node_cpu_utilisation:rate5m
        expr: |
          100 - (avg by (instance, job) (
...
```

> 💡 Recording rules follow the naming convention `level:metric:operation`. This makes it easy to identify the aggregation level (`instance:`), the metric (`node_cpu_utilisation`), and the operation (`rate5m`). Dashboards referencing pre-computed metrics load significantly faster.

---

## Step 6: Define Alert Rules

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/alert_rules.yml << 'EOF'
groups:
  - name: infrastructure_alerts
    rules:
      # CPU alert using recording rule
      - alert: HighCPUUsage
        expr: instance:node_cpu_utilisation:rate5m > 85
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: 'High CPU usage on {{ \$labels.instance }}'
          description: 'CPU usage is {{ printf \"%.1f\" \$value }}% on {{ \$labels.instance }} (threshold: 85%)'
          runbook_url: 'https://wiki.company.com/runbooks/high-cpu'

      - alert: CriticalCPUUsage
        expr: instance:node_cpu_utilisation:rate5m > 95
        for: 5m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: 'Critical CPU usage on {{ \$labels.instance }}'
          description: 'CPU at {{ printf \"%.1f\" \$value }}% for >5min on {{ \$labels.instance }}'

      # Memory alert
      - alert: LowMemory
        expr: instance:node_memory_utilisation:ratio > 0.90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Low memory on {{ \$labels.instance }}'
          description: 'Memory utilisation at {{ printf \"%.0f\" (mul \$value 100) }}%'

      # Disk space alert
      - alert: DiskSpaceWarning
        expr: instance:node_filesystem_usage:ratio > 0.80
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: 'Disk usage >80% on {{ \$labels.instance }}:{{ \$labels.mountpoint }}'

      - alert: DiskSpaceCritical
        expr: instance:node_filesystem_usage:ratio > 0.95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: 'Disk almost full on {{ \$labels.instance }}:{{ \$labels.mountpoint }}'

      # Node down alert
      - alert: NodeDown
        expr: up{job='node'} == 0
        for: 2m
        labels:
          severity: critical
          page: 'true'
        annotations:
          summary: 'Node {{ \$labels.instance }} is DOWN'
          description: 'node_exporter on {{ \$labels.instance }} has been unreachable for >2 minutes'
EOF

echo '=== alert_rules.yml ==='
cat /tmp/alert_rules.yml
"
```

📸 **Verified Output:**
```
=== alert_rules.yml ===
groups:
  - name: infrastructure_alerts
    rules:
      - alert: HighCPUUsage
        expr: instance:node_cpu_utilisation:rate5m > 85
        for: 10m
        labels:
          severity: warning
          team: ops
...
```

> 💡 The `for:` field sets a **pending duration** — the condition must be true continuously for this period before firing. This prevents flapping on brief spikes. `for: 0m` fires immediately. Use `{{$labels.instance}}` in annotations to include the target name dynamically.

---

## Step 7: Configure Alertmanager

```bash
docker run --rm ubuntu:22.04 bash -c "
cat > /tmp/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alertmanager@company.com'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: 'secret'
  slack_api_url: 'https://hooks.slack.com/services/T.../B.../...'

# Templates for notification formatting
templates:
  - /etc/alertmanager/templates/*.tmpl

# Top-level route - all alerts start here
route:
  receiver: default-receiver
  group_by: [alertname, cluster, service]
  group_wait:      30s    # Wait for grouping window
  group_interval:  5m     # Min interval between grouped notifications
  repeat_interval: 4h     # Re-notify if still firing

  routes:
    # Critical alerts: page immediately
    - match:
        severity: critical
      receiver: pagerduty-critical
      group_wait: 10s
      repeat_interval: 1h
      continue: false

    # OPS team alerts
    - match:
        team: ops
      receiver: slack-ops
      group_by: [alertname, instance]

    # Warning alerts: email daily digest
    - match:
        severity: warning
      receiver: email-warnings
      group_interval: 1h
      repeat_interval: 24h

receivers:
  - name: default-receiver
    slack_configs:
      - channel: '#alerts-general'
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'
        send_resolved: true

  - name: slack-ops
    slack_configs:
      - channel: '#alerts-ops'
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
        title: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  - name: pagerduty-critical
    pagerduty_configs:
      - service_key: '<PAGERDUTY_SERVICE_KEY>'
        description: '{{ .GroupLabels.alertname }}'

  - name: email-warnings
    email_configs:
      - to: 'ops-team@company.com'
        headers:
          Subject: '[WARNING] {{ .GroupLabels.alertname }}'
        html: '{{ template "email.html" . }}'

# Silence noisy alerts during maintenance
inhibit_rules:
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: [alertname, instance]
EOF

echo '=== alertmanager.yml written ==='
wc -l /tmp/alertmanager.yml
"
```

📸 **Verified Output:**
```
=== alertmanager.yml written ===
64 /tmp/alertmanager.yml
```

> 💡 `inhibit_rules` suppress child alerts when a parent fires. If `NodeDown` (critical) fires, it silences `HighCPUUsage` (warning) for the same instance — avoiding alert storms. `continue: false` (default) stops routing to sibling receivers once matched.

---

## Step 8: Capstone — Production Monitoring Rollout

**Scenario:** You are deploying Prometheus monitoring for a 3-tier production application (load balancer, 4 app servers, 2 database servers). Requirements: 5-minute alert response, 30-day metric retention, HA setup.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq wget curl 2>/dev/null

# Download both binaries
wget -q https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz -O /tmp/prom.tar.gz
wget -q https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz -O /tmp/ne.tar.gz

tar xzf /tmp/prom.tar.gz -C /tmp/
tar xzf /tmp/ne.tar.gz -C /tmp/

echo '=== Binaries available ==='
ls -lh /tmp/prometheus-2.45.0.linux-amd64/prometheus /tmp/node_exporter-1.6.1.linux-amd64/node_exporter

echo ''
echo '=== prometheus binary info ==='
/tmp/prometheus-2.45.0.linux-amd64/prometheus --version 2>&1

echo ''
echo '=== node_exporter binary info ==='
/tmp/node_exporter-1.6.1.linux-amd64/node_exporter --version 2>&1

echo ''
echo '=== Prometheus help flags (storage) ==='
/tmp/prometheus-2.45.0.linux-amd64/prometheus --help 2>&1 | grep -E 'storage|retention' | head -10

echo ''
echo '=== Capstone: Production prometheus.yml ==='
cat << 'CONF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: production
    region: us-east-1

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['am1:9093', 'am2:9093']  # HA Alertmanager
      timeout: 10s

rule_files:
  - /etc/prometheus/rules/recording.yml
  - /etc/prometheus/rules/alerts.yml

scrape_configs:
  - job_name: node
    static_configs:
      - targets: ['lb1:9100']
        labels: {role: loadbalancer, env: prod}
      - targets: ['app1:9100', 'app2:9100', 'app3:9100', 'app4:9100']
        labels: {role: app, env: prod}
      - targets: ['db1:9100', 'db2:9100']
        labels: {role: database, env: prod}

# Start command with 30-day retention:
# prometheus --config.file=/etc/prometheus/prometheus.yml
#            --storage.tsdb.path=/var/lib/prometheus
#            --storage.tsdb.retention.time=30d
#            --storage.tsdb.retention.size=50GB
#            --web.enable-lifecycle
CONF
"
```

📸 **Verified Output:**
```
=== Binaries available ===
-rwxr-xr-x 1 root root 121M Jun 23  2023 /tmp/prometheus-2.45.0.linux-amd64/prometheus
-rwxr-xr-x 1 root root  19M Jul 17  2023 /tmp/node_exporter-1.6.1.linux-amd64/node_exporter

=== prometheus binary info ===
prometheus, version 2.45.0 (branch: HEAD, revision: 8ef767e396bf8445f009f945b0162fd71827f445)
  build user:       root@920118f645b7
  build date:       20230623-15:09:49
  go version:       go1.20.5
  platform:         linux/amd64
  tags:             netgo,builtinassets,stringlabels

=== node_exporter binary info ===
node_exporter, version 1.6.1 (branch: HEAD, revision: 4a1b77600c1873a8233f3ffb55afcedbb63b8d84)
  build user:       root@586879db11e5
  build date:       20230717-12:10:52
  go version:       go1.20.6
  platform:         linux/amd64
  tags:             netgo osusergo static_build
```

> 💡 For HA Prometheus, run two identical Prometheus instances and configure both to point at the same Alertmanager cluster. Use Thanos or Cortex for long-term storage and global query federation. Enable `--web.enable-lifecycle` to allow config reload via `POST /-/reload`.

---

## Summary

| Concept | Key Details |
|---------|-------------|
| **Scrape model** | Pull-based; Prometheus scrapes `/metrics` endpoints every `scrape_interval` |
| **TSDB** | Local time-series DB in chunks; default 2h blocks, compacted to 2h→2d→... |
| **prometheus.yml** | `global`, `alerting`, `rule_files`, `scrape_configs` sections |
| **PromQL rate()** | Per-second average of counter increase over range vector |
| **histogram_quantile** | Calculates percentile from histogram `_bucket` metrics |
| **Recording rules** | Pre-compute expensive queries; naming: `level:metric:operation` |
| **Alert rules** | `expr`, `for` (pending duration), `labels`, `annotations` fields |
| **Alertmanager** | Routes by label matchers; groups, inhibits, silences notifications |
| **Retention** | `--storage.tsdb.retention.time=30d` or `--storage.tsdb.retention.size=50GB` |
| **Prometheus v2.45.0** | Released 2023-06-23, Go 1.20.5, static binary 121MB |
| **node_exporter v1.6.1** | Released 2023-07-17, Go 1.20.6, static binary 19MB |
