# Platform Engineering

Platform Engineering builds Internal Developer Platforms (IDPs) to enable self-service for development teams.

## Golden Path — Developer Experience

```
Developer pushes code → CI runs tests → Build Docker image
→ Push to registry → ArgoCD detects → Deploy to K8s
→ Prometheus monitors → Alert if degraded
→ Rollback automatically if health checks fail
```

## GitOps with ArgoCD

```yaml
# argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/k8s-manifests
    targetRevision: HEAD
    path: apps/myapp/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Observability Stack

```yaml
# Prometheus + Grafana + Loki + Tempo (full observability)

# Metrics (Prometheus)
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

# SLO Definition
groups:
  - name: slo
    rules:
      - record: slo:availability:ratio
        expr: |
          sum(rate(http_requests_total{code!~"5.."}[5m]))
          / sum(rate(http_requests_total[5m]))
      - alert: SLOBreach
        expr: slo:availability:ratio < 0.999  # 99.9% SLO
```

## Cost Optimization Strategies

```bash
# Identify unused resources
aws ec2 describe-instances --query \
  "Reservations[].Instances[?State.Name=='stopped'].{ID:InstanceId,Type:InstanceType}"

# Right-sizing recommendations
aws compute-optimizer get-ec2-instance-recommendations

# Spot instance savings (up to 90% cheaper)
eksctl create nodegroup \
  --cluster prod \
  --name spot-workers \
  --spot \
  --instance-types m6i.xlarge,m6a.xlarge,m5.xlarge \
  --nodes-min 0 --nodes-max 50
```
