# Quickstart: Monitoring, Logging, and Multi-Cloud Deployment

**Feature**: 009-monitoring-multicloud
**Date**: 2026-02-10
**Audience**: Developers and DevOps engineers

## Overview

This quickstart guide helps you set up monitoring (Prometheus + Grafana) and logging (Loki + Promtail) for the Todo App microservices, and deploy to multiple cloud providers (OKE, AKS, GKE).

## Prerequisites

- Completed Spec 8 (Kafka + Dapr Event-Driven Architecture)
- Minikube running with all services deployed
- Helm 3.x installed
- kubectl configured for your cluster

## Part 1: Local Monitoring & Logging (Minikube)

### Step 1: Deploy kube-prometheus-stack

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kube-prometheus-stack -n monitoring --timeout=300s
```

**What this does**:
- Deploys Prometheus for metrics collection
- Deploys Grafana for visualization
- Deploys Alertmanager (for future alerting)
- Creates ServiceMonitors for auto-discovery

### Step 2: Configure Dapr Metrics Scraping

```bash
# Create ServiceMonitor for Dapr sidecars
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dapr-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      dapr.io/enabled: "true"
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
EOF
```

**What this does**:
- Configures Prometheus to scrape Dapr sidecar metrics
- Collects metrics from all services with Dapr enabled

### Step 3: Deploy Loki + Promtail

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Loki stack
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=10Gi \
  --set promtail.enabled=true \
  --set grafana.enabled=false

# Wait for Loki to be ready
kubectl wait --for=condition=ready pod -l app=loki -n monitoring --timeout=300s
```

**What this does**:
- Deploys Loki for log aggregation
- Deploys Promtail to collect logs from all pods
- Configures 10Gi persistent storage for logs

### Step 4: Configure Loki as Grafana Data Source

```bash
# Get Grafana admin password
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

**Access Grafana**:
1. Open browser: http://localhost:3000
2. Login: username=`admin`, password=`<from above command>`
3. Add Loki data source:
   - Go to Configuration → Data Sources → Add data source
   - Select "Loki"
   - URL: `http://loki:3100`
   - Click "Save & Test"

### Step 5: Import Dashboards

```bash
# Import service overview dashboard
kubectl create configmap grafana-dashboard-service-overview \
  --from-file=specs/009-monitoring-multicloud/contracts/dashboards/service-overview.json \
  -n monitoring

# Label for auto-discovery
kubectl label configmap grafana-dashboard-service-overview \
  grafana_dashboard=1 \
  -n monitoring
```

**What this does**:
- Imports pre-configured dashboard for service metrics
- Grafana automatically discovers and loads the dashboard

### Step 6: Add Structured Logging to Services

Update each service to use structlog:

```python
# backend/main.py (example)
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info("task_created", user_id="user_123", task_id="task_456", duration_ms=45.2)
```

### Step 7: Verify Monitoring & Logging

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# Open: http://localhost:9090/targets

# Check Grafana dashboards
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Open: http://localhost:3000

# Query logs in Grafana
# Go to Explore → Select Loki → Query: {service="backend"}
```

**Expected Results**:
- Prometheus shows all service targets as "UP"
- Grafana displays metrics in service overview dashboard
- Loki returns logs from all services

---

## Part 2: Cloud Deployment (OKE/AKS/GKE)

### Option A: Oracle OKE (Primary - Always Free Tier)

```bash
# 1. Create OKE cluster (via OCI Console or CLI)
oci ce cluster create \
  --compartment-id <compartment-ocid> \
  --name todo-app-cluster \
  --kubernetes-version v1.28.2 \
  --node-shape VM.Standard.E2.1.Micro \
  --node-count 2

# 2. Get kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id <cluster-ocid> \
  --file ~/.kube/config-oke

# 3. Deploy services with OKE-specific values
helm install backend ./helm/backend -f ./helm/values-oke.yaml
helm install recurring-task ./helm/recurring-task -f ./helm/values-oke.yaml
# ... (repeat for all services)

# 4. Deploy monitoring stack
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f ./helm/monitoring/values-oke.yaml

# 5. Deploy logging stack
helm install loki grafana/loki-stack \
  --namespace monitoring \
  -f ./helm/logging/values-oke.yaml
```

**OKE-Specific Configuration**:
- Storage class: `oci-bv` (OCI Block Volume)
- Ingress: OCI Load Balancer
- Kafka: Oracle Streaming Service (Kafka-compatible)

### Option B: Azure AKS (Fallback - $200 Credits)

```bash
# 1. Create AKS cluster
az aks create \
  --resource-group todo-app-rg \
  --name todo-app-cluster \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys

# 2. Get kubeconfig
az aks get-credentials \
  --resource-group todo-app-rg \
  --name todo-app-cluster

# 3. Deploy services with AKS-specific values
helm install backend ./helm/backend -f ./helm/values-aks.yaml
# ... (repeat for all services)

# 4. Deploy monitoring & logging
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f ./helm/monitoring/values-aks.yaml

helm install loki grafana/loki-stack \
  --namespace monitoring \
  -f ./helm/logging/values-aks.yaml
```

**AKS-Specific Configuration**:
- Storage class: `azure-disk`
- Ingress: Azure Load Balancer
- Kafka: Azure Event Hubs (Kafka-compatible) or self-hosted Redpanda

### Option C: Google GKE (Fallback - $300 Credits)

```bash
# 1. Create GKE cluster
gcloud container clusters create todo-app-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type e2-small \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 3

# 2. Get kubeconfig
gcloud container clusters get-credentials todo-app-cluster \
  --zone us-central1-a

# 3. Deploy services with GKE-specific values
helm install backend ./helm/backend -f ./helm/values-gke.yaml
# ... (repeat for all services)

# 4. Deploy monitoring & logging
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f ./helm/monitoring/values-gke.yaml

helm install loki grafana/loki-stack \
  --namespace monitoring \
  -f ./helm/logging/values-gke.yaml
```

**GKE-Specific Configuration**:
- Storage class: `standard-rwo`
- Ingress: GCP Load Balancer
- Kafka: Self-hosted Redpanda (Google Pub/Sub not Kafka-compatible)

---

## Part 3: End-to-End Testing

### Run E2E Tests Locally

```bash
# Install test dependencies
pip install pytest requests websockets

# Run E2E tests
cd backend
pytest tests/e2e/test_event_flows.py -v

# Expected output:
# tests/e2e/test_event_flows.py::test_task_creation_flow PASSED
# tests/e2e/test_event_flows.py::test_recurring_task_flow PASSED
# tests/e2e/test_event_flows.py::test_reminder_flow PASSED
# tests/e2e/test_event_flows.py::test_websocket_sync_flow PASSED
# tests/e2e/test_event_flows.py::test_audit_log_flow PASSED
```

### Run E2E Tests in CI/CD

E2E tests run automatically in GitHub Actions on every PR:

```yaml
# .github/workflows/test.yml
- name: Run E2E Tests
  run: |
    pytest backend/tests/e2e/ -v --junit-xml=test-results.xml
```

---

## Part 4: Production Readiness Checklist

Before deploying to production, verify:

- [ ] All services have resource limits defined
- [ ] HPA configured for backend and sync services
- [ ] Pod Disruption Budgets (PDB) configured
- [ ] Network policies configured
- [ ] Secrets stored in Kubernetes Secrets (not ConfigMaps)
- [ ] Database backups configured
- [ ] Monitoring dashboards accessible
- [ ] Log retention configured (30 days for prod)
- [ ] E2E tests passing
- [ ] Health check endpoints working

---

## Troubleshooting

### Prometheus not scraping Dapr metrics

```bash
# Check ServiceMonitor
kubectl get servicemonitor -n monitoring

# Check Prometheus targets
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# Open: http://localhost:9090/targets
```

### Loki not receiving logs

```bash
# Check Promtail pods
kubectl get pods -n monitoring -l app=promtail

# Check Promtail logs
kubectl logs -n monitoring -l app=promtail --tail=50
```

### Grafana dashboard not loading

```bash
# Check Grafana pod
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Check Grafana logs
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana --tail=50
```

---

## Next Steps

1. Review metrics in Grafana dashboards
2. Set up alerting rules (future work)
3. Configure log retention policies
4. Optimize resource limits based on monitoring data
5. Document runbooks for common issues

## References

- Full deployment guides: `docs/deployment/`
- Helm chart documentation: `helm/*/README.md`
- Metrics specification: `specs/009-monitoring-multicloud/contracts/metrics-specification.md`
- Log format: `specs/009-monitoring-multicloud/contracts/log-format.json`
