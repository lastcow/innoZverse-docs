# Kubernetes Basics

Kubernetes (k8s) orchestrates containers at scale — handling deployment, scaling, and healing automatically.

## Core Concepts

- **Pod** — Smallest unit; one or more containers
- **Deployment** — Manages replicas of pods
- **Service** — Exposes pods as a network service
- **Namespace** — Virtual cluster for isolation
- **ConfigMap** — Configuration data
- **Secret** — Sensitive configuration

## kubectl Commands

```bash
# Context & cluster
kubectl config get-contexts
kubectl config use-context my-cluster

# Pods
kubectl get pods
kubectl get pods -n kube-system         # Specific namespace
kubectl describe pod my-pod
kubectl logs my-pod -f                  # Follow logs
kubectl exec -it my-pod -- bash         # Shell into pod

# Deployments
kubectl get deployments
kubectl scale deployment myapp --replicas=5
kubectl rollout status deployment/myapp
kubectl rollout undo deployment/myapp   # Rollback

# Services
kubectl get services
kubectl port-forward service/myapp 8080:80
```

## Sample Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```
