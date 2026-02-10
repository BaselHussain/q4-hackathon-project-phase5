# Monitoring and Logging Quick Start Guide

This guide helps you quickly set up monitoring and logging for the Todo App.

## Overview

The Todo App includes comprehensive monitoring and logging capabilities:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **Loki**: Log aggregation and querying
- **Promtail**: Log collection from Kubernetes pods
- **Alertmanager**: Alert routing and notifications

## Quick Start (Minikube)

### Prerequisites

- Minikube installed and running
- kubectl configured
- Helm 3 installed
- At least 8GB RAM allocated to Minikube

### 1. Start Minikube with Monitoring and Logging

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192 --driver=docker

# Run setup script with monitoring and logging
./scripts/setup-minikube.sh --with-monitoring --with-logging
```

This will:
- Install Dapr runtime
- Deploy Prometheus + Grafana (monitoring namespace)
- Deploy Loki + Promtail (logging namespace)
- Configure all necessary components

### 2. Deploy Application Services

```bash
# Build and deploy services
./scripts/deploy-local.sh
```

### 3. Access Monitoring Dashboards

**Grafana** (Metrics Visualization):
```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Open in browser
open http://localhost:3000

# Login credentials
Username: admin
Password: admin  # Or retrieve with:
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

**Prometheus** (Metrics Query):
```bash
# Port-forward Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# Open in browser
open http://localhost:9090
```

**Loki** (Log Query):
```bash
# Port-forward Loki
kubectl port-forward -n logging svc/loki-gateway 3100:80

# Query logs via API
curl "http://localhost:3100/loki/api/v1/query?query={namespace=\"default\"}"
```

### 4. Explore Pre-Built Dashboards

In Grafana, navigate to **Dashboards** and explore:

1. **Service Overview**: HTTP metrics, error rates, response times
2. **Event Processing**: Kafka and Dapr pub/sub metrics
3. **WebSocket Metrics**: Active connections, message delivery
4. **Application Logs**: Centralized log viewer with Loki

### 5. Query Logs

In Grafana:
1. Go to **Explore** (compass icon)
2. Select **Loki** data source
3. Try these queries:

```logql
# All logs from backend service
{namespace="default", service="backend"}

# Error logs only
{namespace="default", level="ERROR"}

# Logs with specific text
{namespace="default"} |= "WebSocket"

# Logs from last 5 minutes
{namespace="default"} [5m]
```

### 6. Verify Everything Works

```bash
# Run E2E tests
./scripts/test-e2e-minikube.sh
```

This will verify:
- All services are running
- Metrics are being collected
- Logs are being aggregated
- Dashboards are accessible

---

## Production Deployment (OKE)

For production deployment to Oracle Kubernetes Engine, follow the comprehensive guide:

📖 **[OKE Deployment Guide](docs/deployment/oke-deployment.md)**

Key differences from Minikube:
- Persistent storage with OCI Block Volumes
- High availability (3+ replicas)
- Loki uses OCI Object Storage backend
- TLS/HTTPS with ingress
- 30-day log retention

---

## Multi-Cloud Deployment

The Todo App supports deployment to multiple cloud providers:

- **Oracle OKE**: [OKE Deployment Guide](docs/deployment/oke-deployment.md)
- **Azure AKS**: [AKS Deployment Guide](docs/deployment/aks-deployment.md)
- **Google GKE**: [GKE Deployment Guide](docs/deployment/gke-deployment.md)

Each guide includes:
- Step-by-step CLI commands
- Cloud-specific configurations
- Monitoring and logging setup
- Troubleshooting tips

---

## Key Metrics to Monitor

### Application Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total HTTP requests | - |
| `http_request_duration_seconds` | Request latency | p95 > 500ms |
| `tasks_created_total` | Tasks created | - |
| `websocket_connections_active` | Active WebSocket connections | - |
| `database_query_duration_seconds` | Database query latency | p95 > 100ms |

### Dapr Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `dapr_runtime_health` | Dapr sidecar health | == 0 |
| `dapr_component_pubsub_egress_count` | Events published | Failure rate > 5% |
| `dapr_component_state_operation_count` | State operations | Failure rate > 5% |

### Kubernetes Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `kube_pod_status_phase` | Pod status | Not Running |
| `container_memory_working_set_bytes` | Memory usage | > 80% of limit |
| `container_cpu_usage_seconds_total` | CPU usage | > 80% of limit |

---

## Common Log Queries

### Find Errors

```logql
{namespace="default", level="ERROR"}
```

### Find Logs for Specific User

```logql
{namespace="default"} | json | user_id="123"
```

### Find Slow Requests

```logql
{namespace="default", service="backend"} |= "duration" | json | duration > 1000
```

### Find WebSocket Connection Issues

```logql
{namespace="default", service="sync-service"} |= "WebSocket" |= "failed"
```

### Find Database Errors

```logql
{namespace="default"} |= "database" |= "error"
```

---

## Alerting

Alerts are pre-configured for critical issues:

- **High Error Rate**: > 5% of requests failing
- **Service Down**: Service not responding
- **High Memory Usage**: > 80% of limit
- **Pod Restarting**: > 3 restarts in 10 minutes
- **Database Errors**: > 5% of queries failing

### Configure Alert Notifications

Edit `helm/monitoring/templates/alertmanager-config.yaml`:

```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - channel: '#alerts-critical'
        api_url: 'YOUR_SLACK_WEBHOOK_URL'
    email_configs:
      - to: 'oncall@example.com'
```

Then redeploy:
```bash
helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values helm/monitoring/values.yaml
```

---

## Troubleshooting

### Metrics Not Appearing

1. **Check /metrics endpoint**:
   ```bash
   kubectl port-forward <pod-name> 8000:8000
   curl http://localhost:8000/metrics
   ```

2. **Check Prometheus targets**:
   - Open Prometheus UI
   - Go to Status > Targets
   - Verify service is "UP"

3. **Check ServiceMonitor**:
   ```bash
   kubectl get servicemonitor -n monitoring
   kubectl describe servicemonitor <name> -n monitoring
   ```

### Logs Not Appearing

1. **Check Promtail is running**:
   ```bash
   kubectl get pods -n logging -l app.kubernetes.io/name=promtail
   ```

2. **Check Promtail logs**:
   ```bash
   kubectl logs -n logging -l app.kubernetes.io/name=promtail
   ```

3. **Verify pod has annotation**:
   ```bash
   kubectl get pod <pod-name> -o yaml | grep prometheus.io/scrape
   ```

### Grafana Dashboard Not Loading

1. **Check Grafana pod**:
   ```bash
   kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana
   kubectl logs -n monitoring -l app.kubernetes.io/name=grafana
   ```

2. **Verify data sources**:
   - In Grafana, go to Configuration > Data Sources
   - Test Prometheus and Loki connections

3. **Re-import dashboards**:
   ```bash
   kubectl delete configmap -n monitoring grafana-dashboard-*
   kubectl apply -f helm/monitoring/templates/dashboards/
   ```

---

## Performance Tuning

### Prometheus

- **Retention**: Default 30 days, adjust in `values.yaml`
- **Storage**: Increase PVC size if running out of space
- **Scrape Interval**: Default 15s, increase for lower overhead

### Loki

- **Retention**: Default 7 days (Minikube), 30 days (production)
- **Ingestion Rate**: Adjust `ingestion_rate_mb` if hitting limits
- **Query Timeout**: Increase for complex queries

### Promtail

- **Resource Limits**: Increase if pods are being OOMKilled
- **Batch Size**: Adjust for better throughput

---

## Additional Resources

- **Production Readiness**: [Production Readiness Checklist](docs/production-readiness-checklist.md)
- **Operational Runbooks**: [Runbooks](docs/runbooks.md)
- **SLI/SLO Definitions**: [SLI/SLO Definitions](docs/sli-slo-definitions.md)
- **Incident Response**: [Incident Response Template](docs/incident-response-template.md)
- **Disaster Recovery**: [Disaster Recovery Plan](docs/disaster-recovery-plan.md)

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review [Operational Runbooks](docs/runbooks.md)
- Open an issue on GitHub
