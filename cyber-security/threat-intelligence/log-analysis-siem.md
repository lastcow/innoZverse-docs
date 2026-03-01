# Log Analysis & SIEM

## Key Log Sources

| Log | Location | What It Captures |
|-----|----------|-----------------|
| Auth | `/var/log/auth.log` | SSH, sudo, login attempts |
| Syslog | `/var/log/syslog` | General system events |
| Web server | `/var/log/nginx/access.log` | HTTP requests |
| Firewall | `/var/log/ufw.log` | Blocked connections |
| Application | Varies | App-specific events |

## Common Log Analysis

```bash
# Failed SSH logins
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head -10

# Successful logins
grep "Accepted" /var/log/auth.log | tail -20

# 404 errors in Nginx
grep " 404 " /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -20

# Top IPs in web logs
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# All sudo usage
grep "sudo" /var/log/auth.log | grep "COMMAND"
```

## ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# logstash pipeline example
input {
  file { path => "/var/log/nginx/access.log" }
}
filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
}
output {
  elasticsearch { hosts => ["localhost:9200"] }
}
```

## Splunk Quick Reference

```
# Search failed logins
source="/var/log/auth.log" "Failed password"
| stats count by src_ip
| sort -count

# Alert on brute force
| tstats count where source="/var/log/auth.log" "Failed password"
| where count > 10
```
